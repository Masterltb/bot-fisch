"""
reeling.py — Reeling Loop tối ưu cho mini-game giữ cá

Tích hợp FishTracker (Edge-Aware Predictive Controller) với vòng lặp
capture-detect-act tốc độ cao.

Luồng xử lý mỗi frame:
  1. Capture ROI bar_zone (mss, cực nhanh)
  2. Detect vị trí Fish (xám dọc) và Bar (trắng ngang)
  3. Tính Action từ FishTracker
  4. Thực thi mouse hold/release qua Controller
  5. Check progress bar đã đầy chưa → CAUGHT
  6. Sleep để đạt target FPS
"""

import time
from loguru import logger

from .fish_tracker import FishTracker, BarState, Action
from .screen_capture import ScreenCapture
from .detector import Detector
from .controller import Controller


# ── Fish profile presets ──────────────────────────────────────────────────────
# Tuning guide:
#   emergency_margin : nhỏ hơn = phản ứng edge sớm hơn (dùng cho cá hiếm)
#   predict_frames   : lớn hơn = look-ahead xa hơn (tốt cho cá có pattern)
#   center_tolerance : nhỏ hơn = giữ Fish gần center hơn (buffer nhiều hơn)
#   loop_fps         : cao hơn = phản ứng nhanh hơn (cần CPU tốt)

FISH_PROFILES: dict[str, dict] = {
    "common": {
        "loop_fps":         30,
        "emergency_margin": 15,
        "predict_frames":   2,
        "center_tolerance": 0.25,   # 25% bar width = vùng chết rộng
        "history_size":     6,
    },
    "uncommon": {
        "loop_fps":         40,
        "emergency_margin": 12,
        "predict_frames":   3,
        "center_tolerance": 0.20,
        "history_size":     7,
    },
    "rare": {
        "loop_fps":         50,
        "emergency_margin": 10,
        "predict_frames":   3,
        "center_tolerance": 0.18,
        "history_size":     8,
    },
    "legendary": {
        "loop_fps":         60,
        "emergency_margin": 7,
        "predict_frames":   4,
        "center_tolerance": 0.15,
        "history_size":     8,
    },
    "mythic": {
        "loop_fps":         60,
        "emergency_margin": 5,
        "predict_frames":   4,
        "center_tolerance": 0.10,   # 10% bar width = gần như luôn căn center
        "history_size":     10,
    },
}


class ReelingController:
    """
    Điều khiển giai đoạn REELING (mini-game giữ cá).

    Cơ chế điều khiển Bar:
      HOLD   chuột → Bar dịch sang TRÁI
      RELEASE chuột → Bar dịch sang PHẢI
    Mục tiêu: thanh dọc XÁM (Fish) luôn nằm trong thanh ngang TRẮNG (Bar).
    """

    def __init__(
        self,
        capture: ScreenCapture,
        detector: Detector,
        controller: Controller,
        config: dict,
        profile: str = "rare",
    ):
        self.capture    = capture
        self.detector   = detector
        self.ctrl       = controller
        self.config     = config
        self.profile_name = profile
        self._tracker   = self._build_tracker(profile)

    def set_profile(self, profile: str):
        """Đổi fish profile khi đang chạy (gọi từ GUI)."""
        if profile not in FISH_PROFILES:
            raise ValueError(f"Unknown profile: {profile}")
        self.profile_name = profile
        self._tracker = self._build_tracker(profile)

    # ─────────────────────────────────────────────────────────────────────────
    # Main reeling loop — gọi từ StateMachine khi vào REELING state
    # ─────────────────────────────────────────────────────────────────────────

    def run(self, timeout: float = 60.0) -> bool:
        """
        Chạy vòng lặp reeling đến khi:
          - Progress bar đầy → return True  (CAUGHT)
          - Timeout          → return False (FAILED)

        Args:
            timeout: Giới hạn thời gian (giây). Cá thường < 15s, hiếm < 30s.

        Returns:
            True nếu bắt được cá, False nếu timeout/thất bại.
        """
        profile  = FISH_PROFILES[self.profile_name]
        fps      = profile["loop_fps"]
        period   = 1.0 / fps
        deadline = time.monotonic() + timeout

        self._tracker.reset()
        self.ctrl.release_all()       # Bắt đầu ở trạng thái release

        logger.info(f"Reeling started | profile={self.profile_name} | fps={fps}")
        consecutive_no_detect = 0
        MAX_NO_DETECT = 10           # Frames liên tiếp không detect → error

        while time.monotonic() < deadline:
            t0 = time.perf_counter()

            # ── 1. Capture bar zone ──────────────────────────────────────────
            bar_frame  = self.capture.grab("bar_zone")
            prog_frame = self.capture.grab("progress_zone")

            # ── 2. Detect positions ──────────────────────────────────────────
            fish_x, bar_left, bar_w = self.detector.get_bar_positions(
                bar_frame, self.config
            )

            if fish_x is None or bar_left is None or bar_w is None or bar_w == 0:
                consecutive_no_detect += 1
                if consecutive_no_detect >= MAX_NO_DETECT:
                    logger.warning("Cannot detect bar/fish for 10 frames — aborting reel")
                    break
                # Giữ nguyên action cũ, tiếp tục
                self._enforce_sleep(t0, period)
                continue

            consecutive_no_detect = 0

            # ── 3. Build state & get action ──────────────────────────────────
            state = BarState(
                fish_x    = fish_x,
                bar_left  = bar_left,
                bar_right = bar_left + bar_w,
                bar_width = bar_w,
            )
            action = self._tracker.update(state)

            # ── 4. Execute action ────────────────────────────────────────────
            self._execute(action)

            # ── 5. Log debug ─────────────────────────────────────────────────
            if logger.level("DEBUG").no <= logger._core.min_level:
                margin_l = state.margin_left
                margin_r = state.margin_right
                in_bar   = "✓" if state.fish_in_bar else "✗"
                logger.debug(
                    f"{in_bar} fish={fish_x:4d} "
                    f"bar=[{bar_left}…{bar_left+bar_w}] "
                    f"ML={margin_l:3d} MR={margin_r:3d} "
                    f"action={action.name}"
                )

            # ── 6. Check progress complete ───────────────────────────────────
            if self._is_progress_full(prog_frame):
                self.ctrl.release_all()
                logger.success("Progress bar full → CAUGHT!")
                return True

            # ── 7. Sleep đúng period ─────────────────────────────────────────
            self._enforce_sleep(t0, period)

        # Timeout
        self.ctrl.release_all()
        logger.warning(f"Reeling timeout after {timeout}s → FAILED")
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _execute(self, action: Action):
        """Ánh xạ Action → lệnh chuột thực tế."""
        if action == Action.HOLD:
            self.ctrl.mouse_down()
        elif action == Action.RELEASE:
            self.ctrl.mouse_up()
        # Action.KEEP → không làm gì

    def _is_progress_full(self, frame) -> bool:
        """Kiểm tra thanh tiến trình đã đầy (>= threshold)."""
        import numpy as np, cv2
        gray        = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        white_ratio = float(np.sum(gray > 200)) / gray.size
        threshold   = self.config["thresholds"].get("progress_complete", 0.90)
        return white_ratio >= threshold

    def _build_tracker(self, profile: str) -> FishTracker:
        p = FISH_PROFILES[profile]
        return FishTracker(
            emergency_margin  = p["emergency_margin"],
            predict_frames    = p["predict_frames"],
            center_tolerance  = p["center_tolerance"],
            history_size      = p["history_size"],
        )

    @staticmethod
    def _enforce_sleep(t0: float, period: float):
        elapsed = time.perf_counter() - t0
        sleep   = period - elapsed
        if sleep > 0:
            time.sleep(sleep)
