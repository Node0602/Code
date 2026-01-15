import numpy as np
import adi
import time
from commpy.filters import rrcosfilter
from scipy.signal import fftconvolve

class WaveSource:
    def __init__(self, name, fc_offset, rs, alpha, num_taps, pwr_dbm, fs=2e6):
        self.name = name
        self.fc_offset = fc_offset  # Hz
        self.rs = rs                # Symbol Rate (Hz)
        self.alpha = alpha
        self.num_taps = num_taps
        self.pwr_dbm = pwr_dbm
        self.fs = fs
        # 最大频偏 Delta_f = Symbol Rate
        self.delta_f = rs 

    def generate(self, duration_sec=0.1):
        num_samples = int(self.fs * duration_sec)
        num_symbols = int(self.rs * duration_sec)
        
        # 1. 生成 4-FSK 符号映射
        # 为了让最大符号 3 对应 Delta_f，将符号归一化到 [-1, 1] 区间
        # 映射：-3 -> -1.0, -1 -> -0.33, 1 -> 0.33, 3 -> 1.0
        raw_symbols = np.random.choice([-3, -1, 1, 3], num_symbols)
        normalized_symbols = raw_symbols / 3.0
        
        # 2. 上采样
        sps = self.fs / self.rs
        upsampled = np.zeros(num_samples)
        for i in range(num_symbols):
            idx = int(i * sps)
            if idx < num_samples:
                upsampled[idx] = normalized_symbols[i]

        # 3. RRC 脉冲成形滤波 (作为频率演变曲线)
        ts = 1 / self.rs
        _, taps = rrcosfilter(self.num_taps, self.alpha, ts, self.fs)
        taps /= np.sum(taps) # 保持直流增益
        
        # 得到平滑后的频率控制信号 (范围约在 -1 到 1 之间)
        freq_control = fftconvolve(upsampled, taps, mode="same")
        
        # 4. FSK 积分调制
        # 瞬时频率 f(t) = Delta_f * freq_control
        # 相位 phi(t) = 2 * pi * sum( f(t) * dt )
        dt = 1 / self.fs
        phase = 2 * np.pi * self.delta_f * np.cumsum(freq_control) * dt
        baseband_fsk = np.exp(1j * phase)

        # 5. 频移至中心频点偏移处
        t = np.arange(num_samples) / self.fs
        shifted_signal = baseband_fsk * np.exp(1j * 2 * np.pi * self.fc_offset * t)
        
        # 6. 功率缩放
        # 参考：0dBm 对应幅值 1.0 (在归一化前)
        amplitude = 10**(self.pwr_dbm / 20)
        return shifted_signal * amplitude

# --- 硬件配置 ---
FS = 2e6
CENTER_FREQ = 433e6 # Pluto 硬件中心频率 (433MHz)
STAGE_DURATION = 5 # 每个等级录5秒，总计15秒
FILE_NAME = "captured_signals.iq"

def main():
    try:
        sdr = adi.Pluto("ip:192.168.2.1") 
        sdr.sample_rate = int(FS)
        sdr.tx_lo = int(CENTER_FREQ)
        sdr.rx_lo = int(CENTER_FREQ)
        
        sdr.tx_hardwaregain_chan0 = -10 # 发射增益
        sdr.rx_buffer_size = 1000000 # 每次读取 0.5 秒的数据 (FS/2)
        sdr.rx_enabled_channels = [0]
        sdr.gain_control_mode_chan0 = "manual"
        sdr.rx_hardwaregain_chan0 = 30  # 接收增益，根据实际环境调整

        # 初始化波源
        broadcast = WaveSource("广播源", 433.2e6 - CENTER_FREQ, 250e3, 0.25, 117, -60)
        jams = {
            1: WaveSource("一级干扰", 432.2e6 - CENTER_FREQ, 500e3, 0.25, 44, -10),
            2: WaveSource("二级干扰", 432.6e6 - CENTER_FREQ, 285e3, 0.25, 77, 10),
            3: WaveSource("三级干扰", 433.2e6 - CENTER_FREQ, 200e3, 0.25, 110, -10)
        }

        all_rx_data = []

        # 3. 循环发射与接收
        for level in [1]:
        # for level in [1, 2, 3]:
            # print(f"正在进行第 {level} 阶段：广播 + {jams[level].name}...")
            
            # 生成一段足够循环的发射信号
            tx_info = broadcast.generate(0.5)
            # tx_jam = jams[level].generate(0.5)
            # tx_sig = tx_info + tx_jam
            tx_sig = tx_info
            
            # 归一化并加载到发射缓冲区 (循环模式)
            tx_sig = (tx_sig / np.max(np.abs(tx_sig)) * 32767).astype(np.complex64)
            sdr.tx_cyclic_buffer = True
            sdr.tx(tx_sig)
            
            # 持续接收该阶段信号
            num_reads = int(STAGE_DURATION / 0.5)
            for _ in range(num_reads):
                rx_samples = sdr.rx()
                all_rx_data.append(rx_samples)
            
            sdr.tx_destroy_buffer() # 停止当前级别的发射，准备下一级

        # 4. 保存文件
        # 合并所有采集到的片段
        final_rx_signal = np.concatenate(all_rx_data).astype(np.complex64)
        final_rx_signal.tofile(FILE_NAME)
        
        print(f"\n录制完成！")
        print(f"文件名: {FILE_NAME}")
        print(f"采样点总数: {len(final_rx_signal)}")
        print(f"总时长: {len(final_rx_signal)/FS:.2f} 秒")

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        sdr.tx_destroy_buffer()

if __name__ == "__main__":
    main()