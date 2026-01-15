# 作图工具
import sys
import numpy as np
import pyqtgraph as pg
# pyqtgraph 的这个导入方式会自动识别并使用 PySide6
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt

def plot_spectrum(iq_data, fs, title="Power Spectral Density"):
    plt.figure(figsize=(10, 4))
    plt.psd(iq_data, NFFT=1024, Fs=fs/1e6, Fc=0) 
    plt.title(title)
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Relative Power (dB)')
    plt.grid(True)
    plt.show()

def plot_eye_diagram(demod_signal, sps, num_symbols=50):
    plt.figure(figsize=(8, 5))
    for i in range(num_symbols):
        if (i+1)*sps < len(demod_signal):
            segment = demod_signal[i*sps : (i+1)*sps]
            plt.plot(segment, color='blue', alpha=0.1)
    plt.axhline(y=0, color='r', linestyle='--')
    plt.title("4-FSK Eye Diagram")
    plt.show()

def plot_threshold_hist(demod_signal):
    plt.figure()
    plt.hist(demod_signal, bins=200, density=True)
    plt.title("Frequency Deviation Distribution")
    plt.show()

class SDRWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 初始化界面
        self.setWindowTitle("Zynq7020+AD9363 信号实时监控")
        self.main_widget = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.main_widget)
        
        # 添加 PSD 窗口
        self.p1 = self.main_widget.addPlot(title="实时频谱 (PSD)")
        self.curve = self.p1.plot(pen='y')
        self.p1.setYRange(-100, -20)
        
        self.main_widget.nextRow() # 换行
        
        # 添加 IQ 平面窗口
        self.p2 = self.main_widget.addPlot(title="IQ 平面 (星座图)")
        self.scatter = pg.ScatterPlotItem(size=3, pen=None, brush=pg.mkBrush(0, 255, 0, 150))
        self.p2.addItem(self.scatter)
        self.p2.setAspectLocked(lock=True, ratio=1) # 锁定比例，让圆看起来是圆的
        
        # 模拟数据更新定时器
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_live_plot)
        self.timer.start(50) # 20Hz 刷新率

    def update_live_plot(self):
        # 注意：实际运行时请将此处替换为 sdr.rx() 获取的数据
        # 这里仅作 PySide6 渲染演示，生成模拟的 IQ 数据
        try:
            # 模拟 1024 个采样点
            raw_data = np.random.normal(size=1024) + 1j * np.random.normal(size=1024)
            
            # 1. 更新频谱
            fft_data = np.abs(np.fft.fftshift(np.fft.fft(raw_data)))
            psd = 10 * np.log10(fft_data + 1e-12)
            self.curve.setData(psd)
            
            # 2. 更新 IQ 平面 (为了性能只显示部分点)
            self.scatter.setData(raw_data.real[:300], raw_data.imag[:300])
            
        except Exception as e:
            print(f"数据更新错误: {e}")
