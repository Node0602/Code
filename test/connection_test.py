import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import adi  # PlutoSDR 接口

class PlutoMonitor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # --- 1. 配置 PlutoSDR 参数 ---
        try:
            self.sdr = adi.Pluto("ip:192.168.2.1") # 默认 Pluto IP
            self.sdr.sample_rate = int(2e6)        # Fs = 2 MSPS
            self.sdr.rx_lo = int(433.5e6)          # LO = 433.5 MHz
            self.sdr.rx_enabled_channels = [0]
            self.sdr.gain_control_mode_chan0 = 'manual'
            self.sdr.rx_hardwaregain_chan0 = 30    # 手动增益中值
            self.sdr.rx_buffer_size = 4096         # 每次读取的采样点数
        except Exception as e:
            print(f"SDR 连接失败: {e}")
            sys.exit()

        # --- 2. 初始化界面 ---
        self.setWindowTitle("PlutoSDR IQ 基线确认")
        self.main_widget = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.main_widget)

        # 窗口 1: PSD 功率谱密度
        self.p1 = self.main_widget.addPlot(title="实时功率谱密度 (PSD)")
        self.p1.setLabel('bottom', '频率', units='Hz')
        self.p1.setLabel('left', '幅度', units='dB')
        self.p1.setYRange(-100, -20)
        self.curve_psd = self.p1.plot(pen='y')

        self.main_widget.nextRow()

        # 窗口 2: IQ 平面 (星座图)
        self.p2 = self.main_widget.addPlot(title="IQ 平面 (星座图)")
        self.p2.setLabel('bottom', 'I (实部)')
        self.p2.setLabel('left', 'Q (虚部)')
        self.p2.setXRange(-2000, 2000)
        self.p2.setYRange(-2000, 2000)
        # 使用散点绘制 IQ 点
        self.scatter_iq = pg.ScatterPlotItem(size=3, pen=None, brush=pg.mkBrush(0, 255, 0, 150))
        self.p2.addItem(self.scatter_iq)

        # --- 3. 设置定时刷新 ---
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)  # 20 FPS

    def update(self):
        # 读取原始 IQ 数据
        data = self.sdr.rx()
        I = data.real
        Q = data.imag

        # --- 计算 PSD ---
        # 对 IQ 数据做 FFT 并取对数幅度
        N = len(data)
        win = np.hanning(N)
        xf = np.fft.fftshift(np.fft.fft(data * win))
        psd = 20 * np.log10(np.abs(xf) / N + 1e-12)
        
        # 生成频率轴
        freqs = np.linspace(-self.sdr.sample_rate/2, self.sdr.sample_rate/2, N)
        
        # 更新 PSD 曲线
        self.curve_psd.setData(freqs, psd)

        # --- 更新 IQ 平面 ---
        # 每次抽样显示 500 个点
        step = max(1, len(I) // 500)
        self.scatter_iq.setData(I[::step], Q[::step])

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PlutoMonitor()
    window.show()
    sys.exit(app.exec())