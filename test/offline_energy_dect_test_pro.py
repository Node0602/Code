import sys
import os
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor import energy_detector_7
from signal_gen import generate_signal

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False 

FS = 2e6
CENTER_FREQ = 433e6
DURATION = 0.05  # 稍微加长一点时间，让 FFT 更稳定

def run_debug_test():
    cases = [
        ("无干扰", None),
        ("一级干扰", "L1"),
        ("二级干扰", "L2"),
        ("三级干扰", "L3")
    ]
    
    fig, axes = plt.subplots(2,2, figsize=(15, 10))
    axes = axes.flatten()
    
    print("===== 离线检测可视化调试 =====")
    
    for i, (name, jam) in enumerate(cases):
        ax = axes[i]
        
        # 1. 生成信号
        iq = generate_signal(
            fs=FS,
            duration=DURATION,
            center_freq=CENTER_FREQ,
            broadcast=True,
            jam_level=jam
        )
        
        # 2. 执行检测 (为了获取中间变量，我们手动重复部分逻辑或打印)
        # 获取 PSD 数据用于绘图
        monitor = energy_detector_7.Energy_Detector(fs=FS)
        freqs, psd = monitor.compute_psd(iq)
        # 将频率转为相对于中心频率的绝对频率，单位 MHz
        abs_freqs = (freqs + CENTER_FREQ) / 1e6
        
        # 计算噪声底（与检测器一致，使用中位数）
        noise_floor = np.median(psd)
        
        # 检测结果（启用 debug 输出）
        result = monitor.detect(iq, CENTER_FREQ, debug=True)
        
        # 3. 绘图
        ax.plot(abs_freqs, psd, color='blue', 
                alpha=0.7, label='PSD')
        ax.axhline(y=noise_floor, color='gray', 
                   linestyle='--', label=f'噪声底({noise_floor:.1f}dB)')
        
        # 标注 L1, L2, L3 的监测区域
        colors = {'L1': 'green', 'L2': 'orange', 'L3': 'red'}
        
        for level, f_target in monitor.freq_table.items():
            f_mhz = f_target / 1e6
            # 画出垂直线表示监测频点
            ax.axvline(x=f_mhz, color=colors.get(level), linestyle=':', alpha=0.8)
            
            # 计算该点当前的能量
            f_offset = f_target - CENTER_FREQ
            p_jam = monitor.band_power(freqs, psd, f_offset, 0.05e6)
            snr = p_jam - noise_floor
            
            # 在图上标注 SNR 文本
            ax.text(f_mhz, p_jam + 2, f"{level}\nSNR:{snr:.1f}", 
                    color=colors.get(level), fontsize=9, ha='center', weight='bold')

        # 4. 广播源特殊处理 (L3 判定依据)
        f_bc_mhz = monitor.broadcast_freq / 1e6
        p_bc = monitor.band_power(freqs, psd, monitor.broadcast_freq - CENTER_FREQ, 0.05e6)
        ax.scatter([f_bc_mhz], [p_bc], color='red', marker='x', zorder=5, label='广播参考点')

        # 完善坐标轴
        ax.set_title(f"场景: {name} | 检测结果: {result}", fontsize=14)
        ax.set_xlabel("频率 (MHz)")
        ax.set_ylabel("功率谱密度 (dB)")
        ax.set_ylim([noise_floor - 10, noise_floor + 50]) # 动态调整纵坐标范围
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize='small')

        print(f"[{name}] 期望: {jam or 'NONE'} | 检测: {result} | 广播功率: {p_bc:.1f}")

    plt.tight_layout()
    plt.suptitle(f"干扰检测算法调试图 (中心频率: {CENTER_FREQ/1e6}MHz)", fontsize=16, y=1.02)
    plt.show()

if __name__ == "__main__":
    run_debug_test()