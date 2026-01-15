import numpy as np


def ddc(iq, fs, fc):
    """
    数字下变频

    Args:
    iq: 复数IQ数据数组
    fs: 输入信号采样率 (Hz)
    fc: 中心频率 (Hz)

    Returns:
    下变频后的基带信号
    """
    t = np.arrange(len(iq)) / fs
    lo = np.exp(-2j * np.pi * fc * t)
    baseband = iq * lo
    return baseband
