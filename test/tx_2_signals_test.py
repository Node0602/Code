import numpy as np
import adi
import time
from commpy.filters import rrcosfilter
from scipy.signal import fftconvolve

# --- 用户手动配置区 ---
CURRENT_LEVEL = 3       # 在这里修改等级：1, 2, 或 3
RECORD_DURATION = 5     # 运行一次发射并录制的时长（秒）
OUTPUT_FILE = f"level_{CURRENT_LEVEL}_capture.iq" # 自动命名文件
# ----------------------

class WaveSource:
    def __init__(self, name, fc_offset, rs, alpha, num_taps, pwr_dbm, fs=2e6):
        self.name, self.fc_offset, self.rs = name, fc_offset, rs
        self.alpha, self.num_taps, self.pwr_dbm, self.fs = alpha, num_taps, pwr_dbm, fs
        self.delta_f = rs 

    def generate(self, duration_sec=0.5):
        num_samples = int(self.fs * duration_sec)
        num_symbols = int(self.rs * duration_sec)
        raw_symbols = np.random.choice([-3, -1, 1, 3], num_symbols)
        normalized_symbols = raw_symbols / 3.0
        sps = self.fs / self.rs
        upsampled = np.zeros(num_samples)
        for i in range(num_symbols):
            idx = int(i * sps)
            if idx < num_samples: upsampled[idx] = normalized_symbols[i]
        ts = 1 / self.rs
        _, taps = rrcosfilter(self.num_taps, self.alpha, ts, self.fs)
        taps /= np.sum(taps)
        freq_control = fftconvolve(upsampled, taps, mode="same")
        dt = 1 / self.fs
        phase = 2 * np.pi * self.delta_f * np.cumsum(freq_control) * dt
        baseband_fsk = np.exp(1j * phase)
        t = np.arange(num_samples) / self.fs
        shifted_signal = baseband_fsk * np.exp(1j * 2 * np.pi * self.fc_offset * t)
        return shifted_signal * 10**(self.pwr_dbm / 20)

def main():
    FS = 2e6
    CENTER_FREQ = 433e6
    sdr = None

    try:
        sdr = adi.Pluto("ip:192.168.2.1")
        sdr.sample_rate = int(FS)
        sdr.tx_lo = int(CENTER_FREQ)
        sdr.rx_lo = int(CENTER_FREQ)
        sdr.tx_hardwaregain_chan0 = -10 
        sdr.rx_hardwaregain_chan0 = 40
        sdr.rx_buffer_size = 1024 * 1024 # 约0.5秒的缓冲区

        # 定义波源
        broadcast = WaveSource("红方广播源", 433.2e6 - CENTER_FREQ, 250e3, 0.25, 88, -60, FS)
        jams = {
            1: WaveSource("一级干扰", 432.2e6 - CENTER_FREQ, 500e3, 0.25, 44, -10, FS),
            2: WaveSource("二级干扰", 432.6e6 - CENTER_FREQ, 285e3, 0.25, 77, 10, FS),
            3: WaveSource("三级干扰", 433.2e6 - CENTER_FREQ, 200e3, 0.25, 110, -10, FS)
        }

        print(f"--- 启动单级发射任务 ---")
        print(f"模式: {broadcast.name} + {jams[CURRENT_LEVEL].name}")

        # 1. 预生成波形并发射
        tx_sig = broadcast.generate(0.5) + jams[CURRENT_LEVEL].generate(0.5)
        tx_sig = (tx_sig / np.max(np.abs(tx_sig)) * 32767).astype(np.complex64)
        
        sdr.tx_cyclic_buffer = True
        sdr.tx(tx_sig)
        
        # 2. 持续接收并存储
        captured_data = []
        num_reads = int(RECORD_DURATION * FS / sdr.rx_buffer_size)
        
        print(f"正在录制 {RECORD_DURATION} 秒数据至 {OUTPUT_FILE}...")
        for i in range(num_reads):
            captured_data.append(sdr.rx())
            if i % 2 == 0: print(f"进度: {((i+1)/num_reads)*100:.0f}%")

        # 3. 保存
        final_signal = np.concatenate(captured_data).astype(np.complex64)
        final_signal.tofile(OUTPUT_FILE)
        print(f"\n任务完成！文件已保存。")

    except Exception as e:
        print(f"错误: {e}")
    finally:
        if sdr:
            sdr.tx_destroy_buffer()

if __name__ == "__main__":
    main()