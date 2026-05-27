"""bot/controller.py — Mouse control via PyDirectInput"""
import time
import random
import ctypes
import pydirectinput


class Controller:
    def __init__(self):
        self._holding = False

    def click(self, x: int, y: int):
        """Instant teleport click (no sliding mouse movement)."""
        pydirectinput.click(x, y)

    def mouse_down(self):
        if not self._holding:
            pydirectinput.mouseDown()
            self._holding = True

    def mouse_up(self):
        if self._holding:
            pydirectinput.mouseUp()
            self._holding = False

    def release_all(self):
        if self._holding:
            pydirectinput.mouseUp()
            self._holding = False

    def _get_pos(self) -> tuple[int, int]:
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    def _bezier_move(self, start: tuple, end: tuple, steps: int = 12):
        sx, sy = start
        ex, ey = end
        # Control point offset for natural curve
        cx = (sx + ex) / 2 + random.randint(-30, 30)
        cy = (sy + ey) / 2 + random.randint(-30, 30)
        for i in range(steps + 1):
            t = i / steps
            x = int((1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t ** 2 * ex)
            y = int((1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t ** 2 * ey)
            pydirectinput.moveTo(x, y)
            time.sleep(0.004)
