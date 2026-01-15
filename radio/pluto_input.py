# pluto 实时 IQ
import numpy as np
import adi
import time
import logging

import numpy as np
import adi
import time

class PlutoReceiver:
    def __init__(self, ip="ip:192.168.2.1", fs=2e6, fc=433.5e6, gain=None):
        """
        PlutoSDR 接收抽象层
        :param ip: Pluto 的 IP 地址
        :param fs: 采样率 (默认 2MHz)
        :param fc: 中心频率 (需覆盖 432.2MHz - 434.92MHz)
        :param gain: 接收增益 (None 表示开启 AGC)
        """
        self.ip = ip
        self.fs = int(fs)
        self.fc = int(fc)
        self.sdr = None
        
        try:
            self.sdr = adi.Pluto(self.ip)
            self._config_sdr(gain)
            logging.info(f"PlutoSDR connected at {self.ip}")
        except Exception as e:
            logging.error(f"Failed to connect to PlutoSDR: {e}")
            raise

    def _config_sdr(self, gain):
        # 基础射频参数设置
        self.sdr.sample_rate = self.fs
        self.sdr.rx_lo = self.fc
        
        # 接收 Buffer 大小 (建议为 2^N，影响实时性与 FFT 分辨率)
        self.sdr.rx_buffer_size = 1024 * 16 
        
        # 增益控制
        if gain is None:
            self.sdr.gain_control_mode_chan0 = "slow_attack" # 自动增益
        else:
            self.sdr.gain_control_mode_chan0 = "manual"
            self.sdr.rx_hardwaregain_chan0 = gain

    def capture_stream(self):
        """实时产生数据块，绝不在此打印原始数据"""
        try:
            while True:
                iq = self.sdr.rx()
                yield iq
        except Exception as e:
            print(f"[Rx Error] {e}")

    def update_fc(self, new_fc):
        """动态调整中心频率 (如果干扰漂移出了当前采样带宽)"""
        self.fc = int(new_fc)
        self.sdr.rx_lo = self.fc
        logging.info(f"LO frequency updated to {self.fc/1e6} MHz")

    def close(self):
        if self.sdr:
            self.sdr = None # 释放资源

'''
# radio/pluto_input.py
import adi
import numpy as np

class PlutoInput:
    def __init__(self,
                 uri="ip:192.168.2.1",
                 fs=2e6,
                 fc=433.2e6,
                 gain=10):

        self.sdr = adi.Pluto(uri)
        self.sdr.sample_rate = int(fs)
        self.sdr.rx_lo = int(fc)
        self.sdr.rx_rf_bandwidth = int(fs)

        self.sdr.rx_gain_control_mode = "manual"
        self.sdr.rx_hardwaregain_chan0 = gain

    def read(self):
        return self.sdr.rx()

'''