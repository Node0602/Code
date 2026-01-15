import threading
import time

class DemodWorker(threading.Thread):
    def __init__(self, name, demod, iq_source):
        super().__init__(daemon=True)
        self.name = name
        self.demod = demod
        self.iq_source = iq_source
        self.running = False

    def run(self):
        self.running = True
        print(f"[{self.name}] started")

        while self.running:
            iq = self.iq_source.read()
            if iq is None:
                time.sleep(0.01)
                continue

            bits = self.demod.process(iq)
            if bits is not None:
                print(f"[{self.name}] decoded {len(bits)} bits")

    def stop(self):
        print(f"[{self.name}] stopped")
        self.running = False
