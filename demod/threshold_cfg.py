# 红方
import numpy as np
import time
from scipy import signal

# 配置参数
FS = 2e6             # 2MSPS 采样率
CENTER_FREQ = 433.2e6 # 红方中心频率
THRESHOLD = -45      # 能量检测阈值 (dB)

# 算子池配置：基于 433.2MHz 中心点的偏移
OPERATOR_POOL = {
    "Level1": {"offset": -1.0e6, "baud": 500e3, "active": False},
    "Level2": {"offset": -0.6e6, "baud": 285e3, "active": False},
    "Level3": {"offset": 0.0,    "baud": 200e3, "active": False}
}