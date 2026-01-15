# signal_gen.py
import numpy as np

def generate_signal(
    fs,
    duration,
    center_freq,
    broadcast=True,
    jam_level=None
):
    """
    jam_level: None / "L1" / "L2" / "L3"
    """

    t = np.arange(0, duration, 1 / fs)
    sig = np.zeros_like(t, dtype=np.complex64)

    # 广播源
    if broadcast:
        f_bc = 433.2e6 - center_freq
        sig += 0.01 * np.exp(1j * 2 * np.pi * f_bc * t)

    # 干扰源
    jam_params = {
        "L1": (432.2e6, 1.0),
        "L2": (432.6e6, 3.0),
        "L3": (433.2e6, 0.5),
    }

    if jam_level:
        f_abs, amp = jam_params[jam_level]
        f_offset = f_abs - center_freq
        sig += amp * np.exp(1j * 2 * np.pi * f_offset * t)

    # 噪声
    noise = 0.001 * (
        np.random.randn(len(t)) +
        1j * np.random.randn(len(t))
    )

    return sig + noise
