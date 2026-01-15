import numpy as np
from collections import Counter
# 从旧代码文件中引用 Energy_Detector 类
from energy_detector import Energy_Detector

def analyze_iq_file(file_path, fs=2e6, lo_freq=433e6):
    """
    读取指定路径的 .iq 文件并输出干扰等级判定
    """
    print(f"[*] 开始分析文件: {file_path}")
    
    # 1. 加载 IQ 数据
    try:
        # 使用 complex64 对应发射端保存的格式
        data = np.fromfile(file_path, dtype=np.complex64)
    except FileNotFoundError:
        print(f"[!] 错误: 找不到文件 {file_path}")
        return

    # 2. 实例化检测器 (引用自旧代码)
    detector = Energy_Detector(fs=fs)
    
    # 3. 执行分段检测
    # 步长等于 FFT 长度，确保覆盖文件全长
    chunk_size = detector.fft_size
    results = []
    
    total_chunks = len(data) // chunk_size
    print(f"[*] 文件包含 {len(data)} 个采样点，分为 {total_chunks} 个片段进行处理...")

    for i in range(total_chunks):
        start = i * chunk_size
        end = start + chunk_size
        iq_chunk = data[start:end]
        
        # 调用引用过来的 detect 方法
        label = detector.detect(iq_chunk, center_freq=lo_freq)
        results.append(label)

    # 4. 汇总统计结果
    counts = Counter(results)
    
    print("\n" + "="*30)
    print(f" 统计报告: {file_path}")
    print("="*30)
    for level in ["NONE", "L1", "L2", "L3"]:
        c = counts.get(level, 0)
        print(f" 干扰等级 {level:4s} | 命中: {c:5d} 次 | 占比: {(c/total_chunks)*100:5.1f}%")
    
    # 5. 给出最终结论
    # 排除 NONE 以外出现次数最多的等级
    valid_results = [r for r in results if r != "NONE"]
    if valid_results:
        final_decision = Counter(valid_results).most_common(1)[0][0]
        print("-" * 30)
        print(f" >>> 最终判定结果: {final_decision} <<<")
    else:
        print("-" * 30)
        print(" >>> 最终判定结果: 无效干扰 (NONE) <<<")

if __name__ == "__main__":
    analyze_iq_file(r"D:\NGXY\Radar\level_3_capture.iq")