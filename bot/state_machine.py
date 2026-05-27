"""bot/state_machine.py — Main FSM (Finite State Machine)

Bug fixes:
  1. Single-thread guard: start() bị ignore nếu thread đang chạy
  2. Clean stop: khi running=False, các state handler thoát sạch (không ERROR_RECOVERY)
  3. _do_casting check running trước cast để tránh click vô ích khi đã stop
  4. ERROR_RECOVERY cũng check running trước khi sleep
"""
import time
import random
import threading
import pydirectinput
from enum import Enum, auto
from loguru import logger

from .screen_capture import ScreenCapture
from .detector import Detector
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
        self.config         = config
        self.capture        = ScreenCapture(config)
        self.detector       = Detector(config)
        self.ctrl           = Controller()
        self.anti           = AntiDetect(config)
        self.state          = State.IDLE
        self.running        = False
        self.on_stat_update = on_stat_update
        self._fish_profile  = "rare"
        self._on_state_cb   = None
        self._on_caught_cb  = None
        self._on_failed_cb  = None
        self._thread: threading.Thread | None = None   # ← BUG FIX: track thread
        self.stats = {"caught": 0, "failed": 0, "casts": 0}

    # ── Public control ────────────────────────────────────────────────────────

    def start(self):
        # BUG FIX 1: Ngăn tạo nhiều thread song song
        if self.running:
            logger.warning("Bot already running — ignoring duplicate start()")
            return
        if self._thread and self._thread.is_alive():
            logger.warning("Previous thread still alive — waiting 1s...")
            self._thread.join(timeout=1.0)

        self.running = True
        self.state   = State.IDLE
        self.anti.start_afk_guard()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="FishBotLoop"
        )
        self._thread.start()
        logger.info(f"Bot loop started | thread={self._thread.name}")

    def stop(self):
        if not self.running:
            logger.debug("stop() called but bot was not running")
            return
        self.running = False
        self.ctrl.release_all()
        self.anti.stop()
        logger.info("Bot loop stopping... (current state will finish cleanly)")

    def set_fish_profile(self, profile: str):
        self._fish_profile = profile
        logger.info(f"Fish profile → {profile.upper()}")

    def set_callbacks(self, on_state=None, on_caught=None, on_failed=None):
        self._on_state_cb  = on_state
        self._on_caught_cb = on_caught
        self._on_failed_cb = on_failed

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _loop(self):
        logger.debug("FSM loop entered")
        self._transition(State.CASTING)

        while self.running:
            try:
                match self.state:
                    case State.CASTING:        self._do_casting()
                    case State.WAITING_BITE:   self._do_waiting_bite()
                    case State.SHAKING:        self._do_shaking()
                    case State.REELING:        self._do_reeling()
                    case State.CAUGHT:         self._do_caught()
                    case State.ERROR_RECOVERY: self._do_error_recovery()
                    case _:
                        time.sleep(0.05)
            except Exception as e:
                logger.exception(f"Unhandled exception in {self.state.name}: {e}")
                if self.running:
                    self._transition(State.ERROR_RECOVERY)

        # Thoát sạch
        self.ctrl.release_all()
        self._transition_silent(State.IDLE)
        logger.info("FSM loop exited cleanly")

    # ── State handlers ────────────────────────────────────────────────────────

    def _do_casting(self):
        if not self.running:
            return

        logger.info(f"Casting... (cast #{self.stats['casts'] + 1})")
        self.stats["casts"] += 1
        
        # Hold mouse to charge cast bar, then release
        self.ctrl.mouse_down()
        time.sleep(random.uniform(1.0, 1.6))
        self.ctrl.mouse_up()
        
        self.anti.cast_delay()
        self.anti.on_cast()

        if self.running:
            self._transition(State.WAITING_BITE)

    def _do_waiting_bite(self):
        logger.debug("Waiting for bite (max 30s)...")
        deadline = time.monotonic() + 30

        while self.running and time.monotonic() < deadline:
            # 1. Check for SHAKE bubbles
            shake_frame = self.capture.grab("shake_zone")
            shakes = self.detector.find_shakes(shake_frame)
            if shakes:
                logger.warning(f"SHAKE detected! {len(shakes)} bubble(s)")
                self._transition(State.SHAKING)
                return

            # 2. Check if mini-game bar is already on screen (skip SHAKE)
            bar_frame = self.capture.grab("bar_zone")
            _, bar_left, bar_w = self.detector.get_bar_positions(bar_frame, self.config)
            if bar_left is not None and bar_w is not None and bar_w > 0:
                logger.warning("Mini-game bar detected — transitioning straight to REELING")
                self._transition(State.REELING)
                return

            time.sleep(0.05)   # ~20 checks/s

        # BUG FIX 2: Phân biệt "bị stop" vs "timeout thật"
        if not self.running:
            logger.debug("Waiting_bite: bot stopped — exiting cleanly")
            return

        # Timeout thật (30s không thấy cá) → recast
        logger.debug("No bite in 30s — recasting")
        self._transition(State.ERROR_RECOVERY)

    def _do_shaking(self):
        roi      = self.config["roi"]["shake_zone"]
        deadline = time.monotonic() + 10

        while self.running and time.monotonic() < deadline:
            frame  = self.capture.grab("shake_zone")
            shakes = self.detector.find_shakes(frame)
            if not shakes:
                logger.debug("No more SHAKE — entering REELING")
                self._transition(State.REELING)
                return
            for cx, cy in sorted(shakes, key=lambda p: p[0]):
                if not self.running:
                    return   # Clean stop mid-shaking
                sx, sy = roi[0] + cx, roi[1] + cy
                logger.debug(f"Clicking SHAKE at ({sx}, {sy})")
                self.ctrl.click(sx, sy)
                self.anti.shake_click_delay()

        if not self.running:
            return
        self._transition(State.ERROR_RECOVERY)

    def _do_reeling(self):
        if not self.running:
            return
        from .reeling import ReelingController
        reeler = ReelingController(
            capture    = self.capture,
            detector   = self.detector,
            controller = self.ctrl,
            config     = self.config,
            profile    = self._fish_profile,
        )
        caught = reeler.run(timeout=60.0)
        if not self.running:
            return
        self._transition(State.CAUGHT if caught else State.ERROR_RECOVERY)

    def _do_caught(self):
        self.ctrl.release_all()
        self.stats["caught"] += 1
        logger.success(f"Fish caught! Total: {self.stats['caught']}")
        if self._on_caught_cb:
            self._on_caught_cb(self._fish_profile)
        if self.on_stat_update:
            self.on_stat_update(self.stats)
        self.anti.post_catch_delay()
        if self.running:
            self._transition(State.CASTING)

    def _do_error_recovery(self):
        if not self.running:
            return
        logger.warning("Error recovery — brief pause before recast")
        self.ctrl.release_all()
        self.stats["failed"] += 1
        if self._on_failed_cb:
            self._on_failed_cb()

        # BUG FIX 4: Interruptible sleep (check running mỗi 0.1s)
        for _ in range(int(random.uniform(15, 30))):   # 1.5–3s total
            if not self.running:
                return
            pydirectinput.press("d") if random.random() > 0.5 else None
            time.sleep(0.1)

        if self.running:
            self._transition(State.CASTING)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _transition(self, new_state: State):
        old = self.state.name
        self.state = new_state
        logger.debug(f"State: {old} → {new_state.name}")
        if self._on_state_cb:
            self._on_state_cb(new_state.name)

    def _transition_silent(self, new_state: State):
        """Chuyển state không log (dùng khi thoát loop)."""
        self.state = new_state
        if self._on_state_cb:
            self._on_state_cb(new_state.name)
