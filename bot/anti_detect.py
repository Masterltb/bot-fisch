"""bot/anti_detect.py — Anti-detection & Anti-AFK"""
import pydirectinput
import time
import random
import threading


class AntiDetect:
    def __init__(self, config: dict):
        self.cfg = config["anti_detect"]
        self._afk_timer: threading.Timer | None = None
        self._cast_count = 0
        self._break_threshold = random.randint(*self.cfg["break_every_n_casts"])

    def shake_click_delay(self):
        lo, hi = self.cfg["shake_click_delay_ms"]
        time.sleep(random.uniform(lo / 1000, hi / 1000))

    def cast_delay(self):
        time.sleep(random.uniform(*self.cfg["cast_delay_s"]))

    def post_catch_delay(self):
        time.sleep(random.uniform(*self.cfg["post_catch_delay_s"]))

    def on_cast(self):
        self._cast_count += 1
        if self._cast_count >= self._break_threshold:
            dur = random.uniform(*self.cfg["break_duration_s"])
            time.sleep(dur)
            self._cast_count = 0
            self._break_threshold = random.randint(*self.cfg["break_every_n_casts"])

    def start_afk_guard(self):
        lo, hi = self.cfg["afk_interval_min"]
        interval = random.uniform(lo * 60, hi * 60)
        self._afk_timer = threading.Timer(interval, self._afk_action)
        self._afk_timer.daemon = True
        self._afk_timer.start()

    def _afk_action(self):
        actions = ["a", "d", "space"]
        for _ in range(random.randint(2, 3)):
            pydirectinput.press(random.choice(actions))
            time.sleep(random.uniform(0.2, 0.6))
        self.start_afk_guard()  # reschedule

    def stop(self):
        if self._afk_timer:
            self._afk_timer.cancel()
