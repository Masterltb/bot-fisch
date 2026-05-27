# 🎣 AGENT SKILL — toolFisch Fishing Bot
**Game**: Fisch (Roblox) | **Method**: External CV (Screen Recognition) | **Lang**: Python 3.11+

---

## SKILL OVERVIEW
Tự động hóa toàn bộ vòng lặp câu cá:
1. Quăng cần → 2. Click SHAKE bubbles → 3. **Edge-Aware Predictive Reeling** giữ Bar theo cá → 4. Loop lại

### Cơ chế điều khiển Bar (quan trọng)
```
HOLD chuột   → Thanh trắng (Bar) dịch sang TRÁI
RELEASE chuột → Thanh trắng (Bar) dịch sang PHẢI

Mục tiêu: Thanh DỌC XÁM (cá) phải luôn NẰM TRONG thanh NGANG TRẮNG (Bar)
```

### Logic ưu tiên (3 tầng)
```
[EMERGENCY]  → Fish gần/ngoài edge → phản ứng tức thì (< 1 frame)
[PREDICTIVE] → Velocity dự đoán Fish sẽ ra edge → phản ứng sớm  
[CENTER]     → Căn Fish về center Bar → tăng buffer margin
```

---

## DEPENDENCIES

```bash
pip install mss opencv-python pydirectinput customtkinter loguru numpy
```

**Lưu ý**: `pydirectinput` yêu cầu Windows + quyền Admin để gửi DirectX input.

---

## PROJECT STRUCTURE

```
e:\toolFisch\
├── main.py                      ← Entry point + loguru bridge
├── config.json                  ← Auto-created nếu không có
├── bot\
│   ├── __init__.py
│   ├── state_machine.py
│   ├── screen_capture.py
│   ├── detector.py
│   ├── controller.py
│   ├── fish_tracker.py          ← Edge-Aware Predictive Controller
│   ├── reeling.py               ← Reeling loop tốc độ cao
│   └── anti_detect.py
├── gui\
│   ├── __init__.py
│   ├── theme.py                 ← Gen-Z dark color system
│   ├── log_widget.py            ← Thread-safe colored log panel
│   └── app_window.py            ← Main window 1100×680
├── templates\
│   ├── shake_template.png       ← Cần chụp thủ công từ game
│   └── caught_template.png
└── logs\
    └── fisch.log                ← Auto-rotating, 10MB/file
```

---

## GUI — Dark Theme Windows Tool

### Layout tổng thể (1100×680)
```
┌──────────────────────────────────────────────────────────────┐
│  🎣 toolFisch   External CV Bot    F8 toggle · F9 calibrate  │
├──────────────────────────────────────────────────────────────┤
│ [CAUGHT: 0] [FAILED: 0] [SUCCESS%: —] [UPTIME] [CASTS]      │
├──────────────┬───────────────────────────────────────────────┤
│  ▶ START     │  LIVE DEBUG LOG                               │
│  ◉ IDLE      │  [10:23:45.123]  INFO  │ Bot started...       │
│              │  [10:23:45.456]  DBG   │ Profile: RARE        │
│  PROFILE:    │  [10:23:47.001]  WARN  │ SHAKE detected!      │
│  ○ Common    │  [10:23:47.050]  OK    │ Fish caught!         │
│  ● Rare      │  [10:23:47.051]  FISH  │ 🎣 Tier: LEGENDARY   │
│  ○ Legendary │                                               │
│              │  [■ INFO ■ OK ■ WARN ■ ERR ■ FISH ■ DBG]     │
│  FISH CNT:   │  □ Auto-scroll  □ DEBUG  [CLEAR]             │
│  ● Mythic: 0 │                                               │
│  ● Legend: 0 │                                               │
└──────────────┴───────────────────────────────────────────────┘
```

### Color Palette (Gen-Z Dark)
| Role | Hex | Dùng cho |
|---|---|---|
| `BG_BASE` | `#0a0a0f` | Nền chính |
| `BG_SURFACE` | `#12121a` | Cards, sidebar |
| `ACCENT_PRIMARY` | `#7c3aed` | Button START, badges |
| `ACCENT_GREEN` | `#10b981` | Caught, success |
| `ACCENT_RED` | `#ef4444` | Failed, STOP button |
| `ACCENT_CYAN` | `#06b6d4` | Success rate, INFO |
| `ACCENT_AMBER` | `#f59e0b` | Warning, casts |
| `TIER_MYTHIC` | `#ec4899` | Pink neon |
| `TIER_LEGENDARY` | `#f59e0b` | Gold |

### Log Levels (Color-coded)
```
[HH:MM:SS.mmm]  INFO  │ message    → Blue
[HH:MM:SS.mmm]    OK  │ message    → Green
[HH:MM:SS.mmm]  WARN  │ message    → Amber
[HH:MM:SS.mmm]   ERR  │ message    → Red
[HH:MM:SS.mmm]  FISH  │ message    → Violet
[HH:MM:SS.mmm]   DBG  │ message    → Gray (toggleable)
```

### Hotkeys
| Key | Action |
|---|---|
| `F8` | Toggle Start/Stop |
| `F9` | Open Calibrator |
| `Esc` | Emergency Stop |

---

## STATE MACHINE

```
IDLE → CASTING → WAITING_BITE → SHAKING → REELING → CAUGHT → (loop)
                                                 ↓
                                          ERROR_RECOVERY
```

| State | Điều kiện thoát | Timeout |
|---|---|---|
| CASTING | Delay 1.5–2.5s ngẫu nhiên | — |
| WAITING_BITE | SHAKE detected | 30s → ERROR_RECOVERY |
| SHAKING | Không còn SHAKE | 10s → ERROR_RECOVERY |
| REELING | Progress bar đầy | 60s → ERROR_RECOVERY |
| CAUGHT | Delay 1–2s | — |
| ERROR_RECOVERY | Sau reset + di chuyển | — |

---

## CORE MODULES

### 1. `config.json` — Cấu hình gốc

```json
{
  "resolution": [1920, 1080],
  "roi": {
    "shake_zone":    [0, 150, 1920, 500],
    "bar_zone":      [280, 460, 740, 545],
    "progress_zone": [380, 520, 640, 535]
  },
  "colors": {
    "fish_hsv_lower":   [0, 0, 110],
    "fish_hsv_upper":   [180, 40, 185],
    "bar_hsv_lower":    [0, 0, 215],
    "bar_hsv_upper":    [180, 25, 255]
  },
  "thresholds": {
    "shake_confidence": 0.78,
    "progress_complete": 0.90
  },
  "anti_detect": {
    "shake_click_delay_ms": [50, 150],
    "cast_delay_s":         [1.5, 2.5],
    "post_catch_delay_s":   [1.0, 2.5],
    "afk_interval_min":     [15, 25],
    "break_every_n_casts":  [10, 18],
    "break_duration_s":     [30, 90]
  },
  "fish_profiles": {
    "common":    {"loop_fps": 30, "emergency_margin": 15, "predict_frames": 2, "center_tolerance": 0.25},
    "uncommon":  {"loop_fps": 40, "emergency_margin": 12, "predict_frames": 3, "center_tolerance": 0.20},
    "rare":      {"loop_fps": 50, "emergency_margin": 10, "predict_frames": 3, "center_tolerance": 0.18},
    "legendary": {"loop_fps": 60, "emergency_margin": 7,  "predict_frames": 4, "center_tolerance": 0.15},
    "mythic":    {"loop_fps": 60, "emergency_margin": 5,  "predict_frames": 4, "center_tolerance": 0.10}
  },
  "hotkeys": {
    "toggle_bot": "f8",
    "open_calibrator": "f9"
  }
}
```

---

### 2. `bot/screen_capture.py`

```python
import mss
import numpy as np

class ScreenCapture:
    def __init__(self, config: dict):
        self.config = config
        import threading
        self._local = threading.local()

    @property
    def sct(self):
        if not hasattr(self._local, "sct"):
            self._local.sct = mss.mss()
        return self._local.sct

    def grab(self, roi_key: str) -> np.ndarray:
        x1, y1, x2, y2 = self.config["roi"][roi_key]
        monitor = {"left": x1, "top": y1, "width": x2-x1, "height": y2-y1}
        img = self.sct.grab(monitor)
        return np.array(img)[:, :, :3]  # BGR, drop alpha
```

---

### 3. `bot/detector.py`

```python
import cv2
import numpy as np

class Detector:
    def __init__(self, config: dict):
        self.shake_tpl = cv2.imread("templates/shake_template.png")
        self.threshold = config["thresholds"]["shake_confidence"]

    def find_shakes(self, frame: np.ndarray) -> list[tuple]:
        """Multi-scale template match. Trả về list (cx, cy) tâm bubble."""
        results = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tpl_gray = cv2.cvtColor(self.shake_tpl, cv2.COLOR_BGR2GRAY)

        for scale in [0.85, 1.0, 1.15]:
            h, w = tpl_gray.shape
            resized = cv2.resize(tpl_gray, (int(w*scale), int(h*scale)))
            if resized.shape[0] > gray.shape[0] or resized.shape[1] > gray.shape[1]:
                continue
            res = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
            locs = np.where(res >= self.threshold)
            rh, rw = resized.shape
            for pt in zip(*locs[::-1]):
                results.append((pt[0] + rw//2, pt[1] + rh//2, res[pt[1], pt[0]]))

        return self._nms(results)

    def _nms(self, pts: list, radius=40) -> list:
        """Non-max suppression: loại trùng lặp gần nhau."""
        if not pts:
            return []
        pts = sorted(pts, key=lambda p: -p[2])
        kept = []
        for p in pts:
            if all(abs(p[0]-k[0]) > radius or abs(p[1]-k[1]) > radius for k in kept):
                kept.append(p)
        return [(x, y) for x, y, _ in kept]

    def get_bar_positions(self, frame: np.ndarray, config: dict) -> tuple[int|None, int|None, int|None]:
        """
        Trả về (fish_x, bar_left_x, bar_width).
        fish_x: tâm X của thanh cá (xám dọc).
        bar_left_x, bar_width: vị trí thanh trắng player.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Tìm thanh cá (xám)
        lo = np.array(config["colors"]["fish_hsv_lower"])
        hi = np.array(config["colors"]["fish_hsv_upper"])
        fish_mask = cv2.inRange(hsv, lo, hi)
        fish_x = self._mask_center_x(fish_mask)

        # Tìm thanh Bar player (trắng)
        lo2 = np.array(config["colors"]["bar_hsv_lower"])
        hi2 = np.array(config["colors"]["bar_hsv_upper"])
        bar_mask = cv2.inRange(hsv, lo2, hi2)
        bar_left, bar_w = self._mask_extent_x(bar_mask)

        return fish_x, bar_left, bar_w

    def _mask_center_x(self, mask: np.ndarray) -> int | None:
        cols = np.where(mask.max(axis=0) > 0)[0]
        return int(cols.mean()) if len(cols) > 0 else None

    def _mask_extent_x(self, mask: np.ndarray) -> tuple[int|None, int|None]:
        cols = np.where(mask.max(axis=0) > 0)[0]
        if len(cols) == 0:
            return None, None
        return int(cols.min()), int(cols.max() - cols.min())
```

---

### 4. `bot/fish_tracker.py` — Edge-Aware Predictive Controller

> ⚠️ **Thay đổi lớn**: Logic mới không dùng PID. Thay vào đó dùng **3-tier priority system** ưu tiên giữ Fish trong biên Bar, rồi mới căn center.

```python
from collections import deque
from enum import Enum, auto
from dataclasses import dataclass

class Action(Enum):
    HOLD    = auto()   # Giữ chuột    → Bar dịch TRÁI
    RELEASE = auto()   # Thả chuột   → Bar dịch PHẢI
    KEEP    = auto()   # Giữ nguyên trạng thái

@dataclass
class BarState:
    fish_x: int
    bar_left: int
    bar_right: int
    bar_width: int

    @property
    def bar_center(self): return (self.bar_left + self.bar_right) / 2.0
    @property
    def fish_offset(self): return self.fish_x - self.bar_center
    @property
    def fish_in_bar(self): return self.bar_left <= self.fish_x <= self.bar_right
    @property
    def margin_left(self): return self.fish_x - self.bar_left
    @property
    def margin_right(self): return self.bar_right - self.fish_x

class FishTracker:
    def __init__(self, emergency_margin=10, predict_frames=3,
                 center_tolerance=0.18, history_size=8):
        self.emergency_margin = emergency_margin
        self.predict_frames   = predict_frames
        self.center_tolerance = center_tolerance
        self._history = deque(maxlen=history_size)

    def update(self, state: BarState) -> Action:
        self._history.append(state.fish_x)
        # Tier 1: EMERGENCY
        action = self._emergency_check(state)
        if action: return action
        # Tier 2: PREDICTIVE
        action = self._predictive_check(state)
        if action: return action
        # Tier 3: CENTER
        return self._center_check(state)

    def _emergency_check(self, s: BarState):
        if s.fish_x < s.bar_left:                         return Action.HOLD
        if s.fish_x > s.bar_right:                        return Action.RELEASE
        if s.margin_left  <= self.emergency_margin:       return Action.HOLD
        if s.margin_right <= self.emergency_margin:       return Action.RELEASE
        return None

    def _predictive_check(self, s: BarState):
        vel = self._velocity()
        if vel == 0: return None
        predicted = s.fish_x + vel * self.predict_frames
        if predicted < s.bar_left  + self.emergency_margin: return Action.HOLD
        if predicted > s.bar_right - self.emergency_margin: return Action.RELEASE
        return None

    def _center_check(self, s: BarState) -> Action:
        tol = s.bar_width * self.center_tolerance
        if s.fish_offset >  tol: return Action.RELEASE
        if s.fish_offset < -tol: return Action.HOLD
        return Action.KEEP

    def _velocity(self) -> float:
        if len(self._history) < 3: return 0.0
        h = list(self._history)
        deltas  = [h[i+1]-h[i] for i in range(len(h)-1)]
        weights = list(range(1, len(deltas)+1))
        return sum(d*w for d,w in zip(deltas,weights)) / sum(weights)
```

### 4b. `bot/reeling.py` — Reeling Loop tốc độ cao

```python
# Xem file e:\toolFisch\bot\reeling.py để biết full implementation
# Key: ReelingController.run(timeout=60) trả về True=caught, False=failed
# Tích hợp FishTracker + ScreenCapture + Detector trong 1 vòng lặp cao tần

from .reeling import ReelingController, FISH_PROFILES
```

---

### 5. `bot/controller.py`

```python
import pydirectinput
import time
import random
import math

class Controller:
    def __init__(self):
        self._holding = False

    # ── Mouse actions ──
    def click(self, x: int, y: int):
        self._bezier_move(self._get_pos(), (x, y))
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

    # ── Humanized movement ──
    def _get_pos(self):
        import ctypes
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    def _bezier_move(self, start, end, steps=15):
        sx, sy = start; ex, ey = end
        cx = (sx + ex) / 2 + random.randint(-40, 40)
        cy = (sy + ey) / 2 + random.randint(-40, 40)
        for i in range(steps + 1):
            t = i / steps
            x = int((1-t)**2 * sx + 2*(1-t)*t * cx + t**2 * ex)
            y = int((1-t)**2 * sy + 2*(1-t)*t * cy + t**2 * ey)
            pydirectinput.moveTo(x, y)
            time.sleep(0.004)
```

---

### 6. `bot/anti_detect.py`

```python
import pydirectinput, time, random, threading

class AntiDetect:
    def __init__(self, config: dict):
        self.cfg = config["anti_detect"]
        self._afk_timer = None
        self._cast_count = 0
        self._break_threshold = random.randint(*self.cfg["break_every_n_casts"])

    def shake_click_delay(self):
        lo, hi = self.cfg["shake_click_delay_ms"]
        time.sleep(random.uniform(lo/1000, hi/1000))

    def cast_delay(self):
        time.sleep(random.uniform(*self.cfg["cast_delay_s"]))

    def post_catch_delay(self):
        time.sleep(random.uniform(*self.cfg["post_catch_delay_s"]))

    def on_cast(self):
        """Gọi sau mỗi lần cast để kiểm tra break schedule."""
        self._cast_count += 1
        if self._cast_count >= self._break_threshold:
            dur = random.uniform(*self.cfg["break_duration_s"])
            time.sleep(dur)
            self._cast_count = 0
            self._break_threshold = random.randint(*self.cfg["break_every_n_casts"])

    def start_afk_guard(self):
        """Chạy anti-AFK routine theo interval ngẫu nhiên."""
        lo, hi = self.cfg["afk_interval_min"]
        interval = random.uniform(lo * 60, hi * 60)
        self._afk_timer = threading.Timer(interval, self._afk_action)
        self._afk_timer.daemon = True
        self._afk_timer.start()

    def _afk_action(self):
        actions = ['a', 'd', 'space']
        for _ in range(random.randint(2, 3)):
            pydirectinput.press(random.choice(actions))
            time.sleep(random.uniform(0.2, 0.6))
        self.start_afk_guard()   # reschedule

    def stop(self):
        if self._afk_timer:
            self._afk_timer.cancel()
```

---

### 7. `bot/state_machine.py` — FSM chính

```python
import time, threading
from enum import Enum, auto
from loguru import logger
import pydirectinput

from .screen_capture import ScreenCapture
from .detector import Detector
from .fish_tracker import FishTracker, Action
from .controller import Controller
from .anti_detect import AntiDetect

class State(Enum):
    IDLE           = auto()
    CASTING        = auto()
    WAITING_BITE   = auto()
    SHAKING        = auto()
    REELING        = auto()
    CAUGHT         = auto()
    ERROR_RECOVERY = auto()

class FishBot:
    def __init__(self, config: dict, on_stat_update=None):
        self.config = config
        self.capture   = ScreenCapture(config)
        self.detector  = Detector(config)
        self.ctrl      = Controller()
        self.anti      = AntiDetect(config)
        self.tracker   = None
        self.state     = State.IDLE
        self.running   = False
        self.stats     = {"caught": 0, "failed": 0, "session_start": None}
        self.on_stat_update = on_stat_update
        self._fish_profile = "rare"  # default, user chọn trong GUI

    # ─── Public control ───────────────────────────────────────
    def start(self):
        self.running = True
        self.stats["session_start"] = time.time()
        self.anti.start_afk_guard()
        threading.Thread(target=self._loop, daemon=True).start()
        logger.info("Bot started")

    def stop(self):
        self.running = False
        self.ctrl.release_all()
        self.anti.stop()
        logger.info("Bot stopped")

    def set_fish_profile(self, profile: str):
        self._fish_profile = profile

    # ─── Main loop ────────────────────────────────────────────
    def _loop(self):
        self._transition(State.CASTING)
        while self.running:
            try:
                if   self.state == State.CASTING:        self._do_casting()
                elif self.state == State.WAITING_BITE:   self._do_waiting_bite()
                elif self.state == State.SHAKING:        self._do_shaking()
                elif self.state == State.REELING:        self._do_reeling()
                elif self.state == State.CAUGHT:         self._do_caught()
                elif self.state == State.ERROR_RECOVERY: self._do_error_recovery()
            except Exception as e:
                logger.error(f"Exception in state {self.state}: {e}")
                self._transition(State.ERROR_RECOVERY)

    # ─── State handlers ───────────────────────────────────────
    def _do_casting(self):
        logger.debug("Casting...")
        pydirectinput.click()            # cast action
        self.anti.cast_delay()
        self.anti.on_cast()
        self._transition(State.WAITING_BITE)

    def _do_waiting_bite(self):
        deadline = time.time() + 30
        while self.running and time.time() < deadline:
            frame = self.capture.grab("shake_zone")
            shakes = self.detector.find_shakes(frame)
            if shakes:
                self._pending_shakes = shakes
                self._transition(State.SHAKING)
                return
            time.sleep(0.05)
        self._transition(State.ERROR_RECOVERY)

    def _do_shaking(self):
        deadline = time.time() + 10
        while self.running and time.time() < deadline:
            frame = self.capture.grab("shake_zone")
            shakes = self.detector.find_shakes(frame)
            if not shakes:
                self._transition(State.REELING)
                return
            # Offset về tọa độ màn hình
            roi = self.config["roi"]["shake_zone"]
            for (x, y) in shakes:
                self.ctrl.click(roi[0] + x, roi[1] + y)
                self.anti.shake_click_delay()
        self._transition(State.ERROR_RECOVERY)

    def _do_reeling(self):
        # Dùng ReelingController (Edge-Aware) thay vì PID cũ
        from .reeling import ReelingController
        reeler = ReelingController(
            capture=self.capture,
            detector=self.detector,
            controller=self.ctrl,
            config=self.config,
            profile=self._fish_profile,
        )
        caught = reeler.run(timeout=60.0)
        self._transition(State.CAUGHT if caught else State.ERROR_RECOVERY)

    def _do_caught(self):
        self.ctrl.release_all()
        self.stats["caught"] += 1
        logger.success(f"Fish caught! Total: {self.stats['caught']}")
        if self.on_stat_update:
            self.on_stat_update(self.stats)
        self.anti.post_catch_delay()
        self._transition(State.CASTING)

    def _do_error_recovery(self):
        logger.warning("Error recovery: resetting state")
        self.ctrl.release_all()
        self.stats["failed"] += 1
        pydirectinput.press('d')
        time.sleep(0.3)
        pydirectinput.press('a')
        time.sleep(2.5)
        self._transition(State.CASTING)

    # ─── Helpers ──────────────────────────────────────────────
    def _transition(self, new_state: State):
        logger.debug(f"{self.state.name} → {new_state.name}")
        self.state = new_state

    def _is_progress_full(self, frame) -> bool:
        import numpy as np, cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        white_ratio = np.sum(gray > 200) / gray.size
        return white_ratio >= self.config["thresholds"]["progress_complete"]
```

---

### 8. `main.py` — Entry Point

```python
import json, customtkinter as ctk
from bot.state_machine import FishBot

def load_config():
    with open("config.json") as f:
        return json.load(f)

def main():
    config = load_config()
    bot = FishBot(config)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("🎣 toolFisch")
    root.geometry("420x300")

    status_lbl = ctk.CTkLabel(root, text="Status: IDLE", font=("Arial", 14))
    status_lbl.pack(pady=10)

    caught_lbl = ctk.CTkLabel(root, text="Caught: 0 | Failed: 0")
    caught_lbl.pack()

    def on_stats(stats):
        caught_lbl.configure(text=f"Caught: {stats['caught']} | Failed: {stats['failed']}")

    bot.on_stat_update = on_stats

    def toggle():
        if bot.running:
            bot.stop()
            btn.configure(text="▶ Start (F8)")
            status_lbl.configure(text="Status: STOPPED")
        else:
            bot.start()
            btn.configure(text="⏹ Stop (F8)")
            status_lbl.configure(text="Status: RUNNING")

    btn = ctk.CTkButton(root, text="▶ Start (F8)", command=toggle, width=200)
    btn.pack(pady=20)

    # Fish profile selector
    profile_var = ctk.StringVar(value="rare")
    ctk.CTkLabel(root, text="Fish Profile:").pack()
    for p in ["common", "rare", "legendary", "mythic"]:
        ctk.CTkRadioButton(root, text=p.capitalize(),
                           variable=profile_var, value=p,
                           command=lambda: bot.set_fish_profile(profile_var.get())
                           ).pack(side="left", padx=10)

    # F8 hotkey
    root.bind("<F8>", lambda e: toggle())

    root.mainloop()

if __name__ == "__main__":
    main()
```

---

## CALIBRATION GUIDE

**Bước bắt buộc trước khi chạy bot:**

1. Chụp ảnh mẫu SHAKE từ game → lưu vào `templates/shake_template.png`
2. Xác định ROI (Region of Interest):
   - Mở game ở độ phân giải cố định (khuyến nghị: 1920×1080 Window Mode)
   - Dùng Windows Snipping Tool hoặc Paint để xác định tọa độ pixel
   - Cập nhật `config.json` > `roi` section
3. Tune màu sắc:
   - Chụp frame khi đang reeling
   - Dùng script nhỏ để in HSV range của thanh cá và thanh Bar
   - Cập nhật `config.json` > `colors` section

**Script lấy HSV color:**
```python
import cv2, mss, numpy as np
with mss.mss() as sct:
    img = np.array(sct.grab(sct.monitors[1]))[:,:,:3]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Click pixel cần lấy màu → in giá trị HSV
    h, w = hsv.shape[:2]
    print(f"Center pixel HSV: {hsv[h//2, w//2]}")
```

---

## PERFORMANCE CHECKLIST

- [ ] Game chạy Window Mode, resolution cố định
- [ ] `config.json` ROI đã calibrate đúng
- [ ] `templates/shake_template.png` đã chụp rõ nét
- [ ] HSV color range đã tune cho màn hình của bạn
- [ ] Chọn `fish_profile` phù hợp (rare/legendary/mythic)
- [ ] Chạy script với quyền Administrator
- [ ] Tắt V-Sync trong game nếu được (giảm latency)

---

## ANTI-DETECTION CHECKLIST

- [x] Bezier mouse movement (không teleport)
- [x] Random delay giữa các click SHAKE (50–150ms)
- [x] Session breaks sau mỗi 10–18 cast
- [x] Anti-AFK ngẫu nhiên mỗi 15–25 phút
- [x] Post-catch delay ngẫu nhiên 1–2.5s
- [x] Error recovery không loop vô hạn

---

## KNOWN LIMITATIONS

| Vấn đề | Nguyên nhân | Workaround |
|---|---|---|
| SHAKE không detect | Template không match scale | Tune `shake_confidence`, chụp lại template |
| Bar màu không nhận | HSV range sai theo màn hình | Re-tune `colors` trong config.json |
| Cá mythic vẫn miss | `emergency_margin` quá lớn | Giảm xuống 3–5, tăng `predict_frames` lên 5 |
| Bar jitter liên tục | `center_tolerance` quá nhỏ | Tăng lên 0.20–0.25 |
| Lag spike khiến state lỗi | Game/PC lag | ERROR_RECOVERY tự xử lý |

---

## REELING TUNING GUIDE

### Khi cá mythic di chuyển quá nhanh
```json
"mythic": {
  "loop_fps": 60,
  "emergency_margin": 3,   ← giảm: phản ứng edge sớm hơn
  "predict_frames": 5,     ← tăng: look-ahead xa hơn  
  "center_tolerance": 0.08 ← giảm: giữ Fish sát center
}
```

### Khi Bar bị jitter (hold/release liên tục)
```json
"center_tolerance": 0.25   ← tăng vùng chết center
"emergency_margin": 12     ← tăng: chỉ emergency khi thực sự nguy hiểm
```

### Thứ tự debug khi reeling không hoạt động
1. Kiểm tra `fish_x` có detect được không → xem log DEBUG
2. Kiểm tra `bar_left` và `bar_width` hợp lý không (bar_width > 50px?)
3. Tune HSV range trong config.json
4. Giảm `emergency_margin` nếu cá thoát mặc dù bot đang phản ứng
