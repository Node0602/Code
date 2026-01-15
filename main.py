from radio.pluto_input import PlutoInput
from monitor.energy_detector import SpectrumMonitor
from demod.base_demod import BaseFSKDemod
from demod.demod_worker import DemodWorker

FS = 2e6
CENTER_FREQ = 433e6

pluto = PlutoInput(center_freq=CENTER_FREQ, fs=FS)
monitor = SpectrumMonitor(fs=FS)

workers = {}

def start_worker(level):
    if level in workers:
        return

    if level == "L1":
        demod = BaseFSKDemod(FS, -1.3e6, 500e3, sps=4)
    elif level == "L2":
        demod = BaseFSKDemod(FS, -0.9e6, 285e3, sps=7)
    elif level == "L3":
        demod = BaseFSKDemod(FS, 0, 200e3, sps=10)

    w = DemodWorker(level, demod, pluto)
    w.start()
    workers[level] = w

def stop_all_except(level):
    for k in list(workers.keys()):
        if k != level:
            workers[k].stop()
            del workers[k]

# 主循环
while True:
    iq = pluto.read()
    state = monitor.detect(iq, CENTER_FREQ)

    if state == "NONE":
        stop_all_except(None)
    else:
        start_worker(state)
        stop_all_except(state)
