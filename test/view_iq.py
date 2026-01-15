import numpy as np
import matplotlib.pyplot as plt

def analyze_captured_data(file_path, fs=2e6, is_npy=False):
    # 1. 加载数据
    if is_npy:
        data = np.load(file_path)
    else:
        # 读取 .iq 文件 (Complex64 格式)
        data = np.fromfile(file_path, dtype=np.complex64)

    print(f"成功加载信号，总采样点数: {len(data)}")
    print(f"信号总时长: {len(data)/fs:.2f} 秒")

    # 创建画布
    plt.figure(figsize=(12, 10))

    # --- 视图 1: 时域信号 (幅度) ---
    # 选取中间一小段观察波形
    plt.subplot(3, 1, 1)
    plt.plot(np.abs(data[:2000])) 
    plt.title("Time Domain (Amplitude - First 2000 samples)")
    plt.xlabel("Samples")
    plt.ylabel("Linear Amplitude")
    plt.grid(True)

    # --- 视图 2: 功率谱密度 (PSD) ---
    # 观察全局频率分布
    plt.subplot(3, 1, 2)
    plt.psd(data, NFFT=1024, Fs=fs/1e6, Fc=0)
    plt.title("Power Spectral Density (PSD)")
    plt.xlabel("Frequency Offset (MHz)")
    plt.ylabel("Relative Power (dB/Hz)")

    # --- 视图 3: 时序频谱图 (Spectrogram) ---
    plt.subplot(3, 1, 3)
    # NFFT 决定频率分辨率，noverlap 决定平滑度
    plt.specgram(data, NFFT=2048, Fs=fs/1e6, noverlap=1024, cmap='viridis')
    plt.title("Spectrogram (Signal Evolution Over Time)")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency Offset (MHz)")
    plt.colorbar(label='Intensity (dB)')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # 存的是 .npy，把 is_npy 设为 True
    file_path2 = r"D:\NGXY\Radar\level_2_capture.iq"
    analyze_captured_data(file_path2, fs=2e6, is_npy=False)