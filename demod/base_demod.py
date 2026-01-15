import numpy as np
from dsp.rrc import rrc_filter

class BroadcastFrontend:
    """
    - 在一级 / 二级干扰存在时
    - 提取干净的广播源基带
    """

    def __init__(self,
                 fs=2e6,
                 rs=250e3,
                 alpha=0.25,
                 num_taps=88):

        self.fs = fs
        self.rs = rs
        self.alpha = alpha
        self.num_taps = num_taps

    def process(self, iq):
        """
        输入：Pluto 基带 IQ（433.2 MHz 对齐）
        输出：广播源净化基带
        """

        # ① RRC 窄带滤波
        bb = rrc_filter(
            iq,
            fs=self.fs,
            rs=self.rs,
            alpha=self.alpha,
            num_taps=self.num_taps
        )

        # ② 软件 AGC
        power = np.mean(np.abs(bb)**2)
        if power > 1e-8:
            bb = bb / np.sqrt(power)

        return bb





'''
# demod/base_demod.py
import numpy as np
from dsp.rrc import rrc_filter

class BroadcastFrontend:
    """
    广播信道前端：
    - 假设 Pluto LO 已对准广播源
    - 只解决一、二级干扰
    """

    def __init__(self,
                 fs=2e6,
                 rs=250e3,
                 alpha=0.25,
                 num_taps=88):

        self.fs = fs
        self.rs = rs
        self.alpha = alpha
        self.num_taps = num_taps

    def process(self, iq):
        # ① RRC 窄带滤波（核心）
        bb = rrc_filter(
            iq,
            fs=self.fs,
            rs=self.rs,
            alpha=self.alpha,
            num_taps=self.num_taps
        )

        # ② 轻量 AGC（不破坏调制）
        power = np.mean(np.abs(bb)**2)
        if power > 1e-8:
            bb = bb / np.sqrt(power)

        return bb

'''