import numpy as np


def multi_level_decision(synced_samples):
    """
    多级判决：将同步后的频率样本映射到4个符号
    """
    if len(synced_samples) == 0:
        return np.array([], dtype=int)

    # 自适应计算判决门限
    # 先对样本进行排序，找到四个聚类中心
    sorted_samples = np.sort(synced_samples)
    n = len(sorted_samples)

    # 简单估计四个电平（假设均匀分布）
    level_indices = [int(n * i / 4) for i in range(4)]
    estimated_levels = sorted_samples[level_indices]

    # 计算判决门限（相邻电平的中点）
    thresholds = (estimated_levels[:-1] + estimated_levels[1:]) / 2

    symbols = np.zeros_like(synced_samples, dtype=int)

    # 判决逻辑
    for i, sample in enumerate(synced_samples):
        if sample < thresholds[0]:
            symbols[i] = 0
        elif sample < thresholds[1]:
            symbols[i] = 1
        elif sample < thresholds[2]:
            symbols[i] = 2
        else:
            symbols[i] = 3

    return symbols, estimated_levels
