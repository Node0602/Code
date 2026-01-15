import numpy as np
import adi
import time
from commpy.filters import rrcosfilter
from scipy.signal import fftconvolve
 
# 4-RRC-FSK 波形发生器

class RRCFSKSource:
    def __init__(self, rs, alpha, num_taps, fs=2e6):
        self.rs = rs                  # Symbol rate
        self.alpha = alpha
        self.num_taps = num_taps
        self.fs = fs
        self.delta_f = rs             # 规则：最大频偏 = Rs

    def generate(self, duration):
        num_samples = int(self.fs * duration)
        num_symbols = int(self.rs * duration)

        # 4-FSK 符号
        symbols = np.random.choice([-3, -1, 1, 3], num_symbols) / 3.0

        # 上采样
        sps = int(self.fs / self.rs)
        up = np.zeros(num_samples)
        up[::sps] = symbols[:len(up[::sps])]

        # RRC 滤波
        _, rrc = rrcosfilter(self.num_taps, self.alpha, 1/self.rs, self.fs)
        rrc /= np.sum(rrc)

        freq_ctrl = fftconvolve(up, rrc, mode="same")

        # FSK 相位积分
        phase = 2 * np.pi * self.delta_f * np.cumsum(freq_ctrl) / self.fs
        return np.exp(1j * phase)

# Pluto 自发自收

FS = 2e6
CENTER_FREQ = 433e6
DURATION = 0.5

def main():
    sdr = adi.Pluto("ip:192.168.2.1")
    sdr.sample_rate = int(FS)
    sdr.tx_lo = int(CENTER_FREQ)
    sdr.rx_lo = int(CENTER_FREQ)

    # 增益（稳定优先）
    sdr.tx_hardwaregain_chan0 = -20
    sdr.rx_hardwaregain_chan0 = 30
    sdr.gain_control_mode_chan0 = "manual"
    sdr.rx_buffer_size = 262144
    sdr.rx_enabled_channels = [0]

    # 4-RRC-FSK 参数（广播参数）
    src = RRCFSKSource(
        rs=250e3,
        alpha=0.25,
        num_taps=88,
        fs=FS
    )

    tx = src.generate(DURATION)

    # 正确幅度归一化 
    tx /= np.max(np.abs(tx))
    tx *= 0.7

    sdr.tx_cyclic_buffer = True
    sdr.tx(tx.astype(np.complex64))

    print("TX running... RX capturing...")
    time.sleep(0.5)

    rx = sdr.rx()
    rx.astype(np.complex64).tofile("captured_4rrcfsk.iq")

    sdr.tx_destroy_buffer()
    print("完成：captured_4rrcfsk.iq")

if __name__ == "__main__":
    main()
