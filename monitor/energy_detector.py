import numpy as np
from collections import deque

class Energy_Detector:
    def __init__(
        self,
        fs,
        fft_size = 4096,
        history_len = 1,
        hit_threshold = 1,
    ):
        self.fs = fs
        self.fft_size = fft_size

        # ---------- 频点定义 ----------
        self.freq_table = {
            "L1": 432.2e6,
            "L2": 432.6e6,
        }
        self.broadcast_freq = 433.2e6

        # ---------- 判决参数 ----------
        self.bandwidth = 0.05e6
        self.snr_l1 = 4        # dB 12
        self.snr_l2 = 7      # dB 18
        self.l3_margin = 6    # dB 15

        self.min_abs_power = -70  # dB，极低信号直接忽略（调高以避免单点噪声误判）

        # ---------- 历史一致性 ----------
        self.history_len = history_len
        self.hit_threshold = hit_threshold
        self.hit_history = {
            "L1": deque([0] * history_len, maxlen=history_len),
            "L2": deque([0] * history_len, maxlen=history_len),
        }

        self.window = np.hanning(self.fft_size)

    # FFT + 功率谱
    def compute_psd(self, iq):
        iq = iq[:self.fft_size] * self.window
        spec = np.fft.fftshift(np.fft.fft(iq))
        power = np.abs(spec) ** 2
        power_db = 10 * np.log10(power + 1e-12)
        freqs = np.fft.fftshift(np.fft.fftfreq(self.fft_size, 1 / self.fs))
        return freqs, power_db

    # 频带平均功率
    def band_power(self, freqs, power_db, f_offset, bandwidth):
        half_bw = bandwidth / 2
        mask = np.abs(freqs - f_offset) <= half_bw
        if not np.any(mask):
            return -120.0
        return np.mean(power_db[mask])

    # 主检测函数
    def detect(self, iq, center_freq, debug=False):
        freqs, power_db = self.compute_psd(iq)
        # 使用中位数作为噪声底，抗离群点更好
        noise_floor = np.median(power_db)
        spec_std = np.std(power_db)
        
        # ---------- L3：宽带压制（最高优先级），增加对广播频点能量的校验 ----------
        mean_power = np.mean(power_db)
        bc_power = self.band_power(freqs, power_db, self.broadcast_freq - center_freq, self.bandwidth)
        above_margin_frac = np.mean(power_db > (noise_floor + self.l3_margin / 2))
        
        # if debug:
            # print("[DEBUG] mean_power", mean_power, "noise_floor", noise_floor, "spec_std", spec_std, "bc_power", bc_power, "above_frac", above_margin_frac)
        
        # 更保守的 L3 判定：广播点必须显著，且至少满足一项更严格的全谱条件
        if (bc_power - noise_floor > self.l3_margin) and (
            (mean_power - noise_floor > self.l3_margin) or (spec_std < 6) or (above_margin_frac > 0.05)
        ):
             if debug:
                 print("[DEBUG] L3 triggered: mean_power", mean_power, "noise_floor", noise_floor, "spec_std", spec_std)
             return "L3"

        # ---------- L1 / L2 ----------
        current_p = {"L1": -120.0, "L2": -120.0}
        current_snr = {"L1": -999.0, "L2": -999.0}

        for level in ["L1", "L2"]:
            f_offset = self.freq_table[level] - center_freq
            half_bw = self.bandwidth / 2
            mask = np.abs(freqs - f_offset) <= half_bw

            if not np.any(mask):
                # 频点不在当前 FFT 范围内，记录未命中并跳过
                self.hit_history[level].append(0)
                continue

            # 使用频带平均能量作为判决依据（比单点峰值更稳健），并保留峰值用于 debug
            p_band = np.mean(power_db[mask])  # 或者使用 self.band_power
            p_peak = np.max(power_db[mask])
            snr = p_band - noise_floor

            current_p[level] = p_band
            current_snr[level] = snr

            # 绝对功率过滤 + 对应级别的 SNR 阈值判断
            if p_band > self.min_abs_power and ((level == "L1" and snr > self.snr_l1) or (level == "L2" and snr > self.snr_l2)):
                self.hit_history[level].append(1)
            else:
                self.hit_history[level].append(0)

        # ---------- 多帧一致性与并列判定 ----------
        candidates = [lvl for lvl in ["L1", "L2"] if sum(self.hit_history[lvl]) >= self.hit_threshold]

        if debug:
            print("[DEBUG] current_p:", current_p, "current_snr:", current_snr, "history_sums:", {lvl: sum(self.hit_history[lvl]) for lvl in ['L1','L2']}, "cands:", candidates)

        if not candidates:
            return "NONE"

        # 若有多个候选，选择当前帧 snr 最大的
        best = max(candidates, key=lambda x: current_snr.get(x, -999))
        return best
