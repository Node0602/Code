import numpy as np
from scipy import signal


def quadrature_discriminator(iq_signal, fs, lpf_numtaps=101, lpf_cutoff=None):
    """
    正交鉴频器 通过复数乘积法计算相位变化率
    Args:
        iq_signal: 输入信号
        fs: 采样率
        lpf_numtaps: 低通滤波器抽头数
        lpf_cutoff: 低通滤波器截止频率
    Rets:
        freq_deviations: 频率变化率序列
    """
    # 复数乘积法     # 只取角度 信号不在单位圆上也可以
    conj_product = iq_signal[1:] * np.conj(iq_signal[:-1])
    phase_diff = np.angle(conj_product)
    # 转换为频率偏移（归一化到符号率）
    freq_deviations = phase_diff * fs / (2 * np.pi)
    # 添加最后一个值保持长度
    freq_deviations = np.append(freq_deviations, freq_deviations[-1])

    # 低通滤波去除高频噪声
    if lpf_cutoff is None:
        lpf_cutoff = fs / 10  # 默认截止频率为采样率的十分之一
    taps = signal.firwin(lpf_numtaps, lpf_cutoff, fs=fs)
    freq_deviations = signal.fftconvolve(freq_deviations, taps, mode="same")

    return freq_deviations
