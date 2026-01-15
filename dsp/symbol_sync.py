import numpy as np


def pll_function(freq_deviations, fs, symbol_rate, alpha=0.1, detect_threshold=1e4):
    """
    峰值检测定时恢复环路
    基于频率差分的峰值检测来恢复符号定时
    Args:
        freq_deviations: 鉴频器输出的频率偏移序列
        fs: 采样率
        symbol_rate: 符号率
        alpha: 软更新系数 每次矫正的影响大小
        detect_threshold: 频率变化检测的阈值
    Rets:
        sync_symbols: 完成同步符号样本列表
    """
    sps = int(fs / symbol_rate)
    if sps != fs / symbol_rate:
        raise ValueError("采样率必须是符号率的整数倍")
    threshold = detect_threshold

    # 计算频率差分
    freq_diff = np.diff(freq_deviations)

    # 计算绝对值（关注幅度）
    abs_freq_diff = np.abs(freq_diff)

    # 初始化定时恢复状态
    mu = 0.0  # 小数间隔
    last_peak_time = 0
    last_lock_time = 0  # 记录上一次锁定时间
    symbol_counter = 0  # 符号计数器

    # 存储结果
    sync_symbols = []
    locked_index = []
    timing_errors = []

    def linear_interpolate(sig, pos):
        idx = int(np.floor(pos))
        t = pos - idx

        if idx < 0 or idx >= len(sig) - 1:
            return sig[min(max(idx, 0), len(sig) - 1)]

        # 线性插值
        y0 = sig[idx]
        y1 = sig[idx + 1]

        return y0 + t * (y1 - y0)

    # 主循环 - 遍历每个采样点
    for n in range(1, len(abs_freq_diff) - 1):
        # 检查是否是局部极大值（峰值）
        is_peak = (
            abs_freq_diff[n] > abs_freq_diff[n - 1]
            and abs_freq_diff[n] > abs_freq_diff[n + 1]
            and abs_freq_diff[n] > threshold
        )

        # 检查最小峰值间距
        if is_peak and (n - last_peak_time) > sps // 2:
            last_peak_time = n

            # 计算期望的符号边界位置
            # 假设峰值应该出现在符号边界（对于矩形频率响应）
            expected_boundary = last_lock_time + sps / 2

            # 计算定时误差
            error = n - expected_boundary

            # 更新环路滤波器
            mu += alpha * error

            # # 记录误差
            # timing_errors.append(error)
            # print(f"[{n}]UPDATE error={error}, mu={mu}")

        if n >= last_lock_time + sps + mu:
            # 符号边界到达，进行符号采样

            # 插值位置
            interp_pos = last_lock_time + sps + mu

            # 采样符号
            if interp_pos < len(freq_deviations):
                symbol_sample = linear_interpolate(freq_deviations, interp_pos)
                sync_symbols.append(symbol_sample)
                locked_index.append(int(round(interp_pos)))
                # print(
                #     f"[{n}]SYMBOL LOCKED symbol_counter={symbol_counter}, interp_pos={interp_pos}, sample={symbol_sample}, mu={mu}"
                # )

            symbol_counter += 1
            last_lock_time = interp_pos
            mu = 0.0  # 重置mu以准备下一个符号

    return sync_symbols
