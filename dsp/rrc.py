import numpy as np
from commpy.filters import rrcosfilter
from scipy.signal import fftconvolve

"""注意commpy库在pip中叫scikit-commpy 安装时请使用pip install scikit-commpy"""


def rrc_filter(iq, rs, fs, alpha, numtaps):
    """对iq信号进行根升余弦滤波

    Args:
        rs,fs,aplha,numtaps四个参数参考官网规则手册中参数
        iq: 复数IQ数据数组
        rs: 符号率 (符号每秒) 即规则手册中SymbolRate
        fs: 输入信号采样率 (Hz) 即规则手册中SampleRate
        alpha: 滤波器滚降系数
        numtaps: 滤波器抽头数量

    Returns:
        滤波后的IQ信号
    """
    ts = 1 / rs  # 符号周期
    _, taps = rrcosfilter(numtaps, alpha, ts, fs)
    filtered_iq = fftconvolve(iq, taps, mode="same")
    return filtered_iq
