"""bot/screen_capture.py"""
import mss
import numpy as np
import threading


class ScreenCapture:
    def __init__(self, config: dict):
        self.config = config
        self._local = threading.local()

    @property
    def sct(self):
        if not hasattr(self._local, "sct"):
            self._local.sct = mss.mss()
        return self._local.sct

    def grab(self, roi_key: str) -> np.ndarray:
        x1, y1, x2, y2 = self.config["roi"][roi_key]
        monitor = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
        img = self.sct.grab(monitor)
        return np.array(img)[:, :, :3]  # BGR, drop alpha

