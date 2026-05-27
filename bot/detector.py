"""
detector.py — Screen detection cho toolFisch

Phát hiện:
  1. SHAKE bubbles (template matching, multi-scale)
  2. Vị trí thanh Fish (xám dọc) và Bar (trắng ngang) trong ROI bar_zone
"""

import cv2
import numpy as np


class Detector:
    def __init__(self, config: dict):
        self.config    = config
        self._shake_tpl = self._load_shake_template()

    # ──────────────────────────────────────────────────────────────────────────
    # SHAKE detection
    # ──────────────────────────────────────────────────────────────────────────

    def find_shakes(self, frame: np.ndarray) -> list[tuple[int, int]]:
        """
        Tìm tất cả bong bóng SHAKE trong frame.
        Returns: list[(cx, cy)] tọa độ tâm trong hệ ROI.
        """
        if self._shake_tpl is None:
            return []

        threshold = self.config["thresholds"].get("shake_confidence", 0.78)
        gray      = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tpl_gray  = cv2.cvtColor(self._shake_tpl, cv2.COLOR_BGR2GRAY)
        results   = []

        for scale in [0.85, 1.0, 1.15]:
            h, w = tpl_gray.shape
            rh, rw = int(h * scale), int(w * scale)
            if rh < 5 or rw < 5:
                continue
            resized = cv2.resize(tpl_gray, (rw, rh))
            if resized.shape[0] > gray.shape[0] or resized.shape[1] > gray.shape[1]:
                continue

            res  = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
            locs = np.where(res >= threshold)
            for pt in zip(*locs[::-1]):
                score = float(res[pt[1], pt[0]])
                results.append((pt[0] + rw // 2, pt[1] + rh // 2, score))

        return self._nms(results, radius=40)

    # ──────────────────────────────────────────────────────────────────────────
    # Bar & Fish position detection
    # ──────────────────────────────────────────────────────────────────────────

    def get_bar_positions(
        self, frame: np.ndarray, config: dict
    ) -> tuple[int | None, int | None, int | None]:
        """
        Tìm vị trí thanh cá (xám dọc) và thanh Bar (trắng ngang).

        Returns:
            (fish_x, bar_left, bar_width)
            - fish_x   : tọa độ X tâm thanh cá trong hệ ROI
            - bar_left : tọa độ X cạnh TRÁI của thanh Bar
            - bar_width: chiều rộng thanh Bar (pixel)

        Trả về None nếu không tìm thấy.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # ── Thanh cá (xám dọc) ───────────────────────────────────────────────
        fish_lo = np.array(config["colors"]["fish_hsv_lower"], dtype=np.uint8)
        fish_hi = np.array(config["colors"]["fish_hsv_upper"], dtype=np.uint8)
        fish_mask = cv2.inRange(hsv, fish_lo, fish_hi)

        # Tăng cường: erode để loại noise nhỏ, dilate để fill gap
        kernel    = np.ones((3, 3), np.uint8)
        fish_mask = cv2.erode(fish_mask, kernel, iterations=1)
        fish_mask = cv2.dilate(fish_mask, kernel, iterations=2)

        fish_x = self._find_vertical_bar_center(fish_mask)

        # ── Thanh Bar player (trắng ngang) ───────────────────────────────────
        bar_lo = np.array(config["colors"]["bar_hsv_lower"], dtype=np.uint8)
        bar_hi = np.array(config["colors"]["bar_hsv_upper"], dtype=np.uint8)
        bar_mask = cv2.inRange(hsv, bar_lo, bar_hi)
        bar_mask  = cv2.dilate(bar_mask, kernel, iterations=2)

        bar_left, bar_width = self._find_horizontal_bar_extent(bar_mask)

        return fish_x, bar_left, bar_width

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _find_vertical_bar_center(self, mask: np.ndarray) -> int | None:
        """
        Tìm tọa độ X của thanh DỌC (Fish).
        Chiến thuật: project mask theo trục Y, tìm cluster pixel dense nhất.
        """
        col_sums = mask.sum(axis=0)          # shape: (width,)
        if col_sums.max() == 0:
            return None

        # Tìm contiguous cluster lớn nhất (thanh dọc)
        threshold  = col_sums.max() * 0.3
        active_cols = np.where(col_sums > threshold)[0]
        if len(active_cols) == 0:
            return None

        # Dùng weighted average để chính xác hơn mean
        weights = col_sums[active_cols]
        center  = int(np.average(active_cols, weights=weights))
        return center

    def _find_horizontal_bar_extent(
        self, mask: np.ndarray
    ) -> tuple[int | None, int | None]:
        """
        Tìm vị trí cạnh trái và chiều rộng thanh NGANG (Bar).
        Chiến thuật: project theo trục X, tìm range pixel liên tục lớn nhất.
        """
        row_sums = mask.sum(axis=1)           # shape: (height,)
        col_sums = mask.sum(axis=0)           # shape: (width,)

        if col_sums.max() == 0:
            return None, None

        threshold   = col_sums.max() * 0.2
        active_cols = np.where(col_sums > threshold)[0]
        if len(active_cols) == 0:
            return None, None

        # Tìm run liên tục dài nhất (loại bỏ noise rải rác)
        best_start, best_len = self._longest_run(active_cols)
        if best_len < 5:
            return None, None

        return int(best_start), int(best_len)

    @staticmethod
    def _longest_run(arr: np.ndarray) -> tuple[int, int]:
        """Tìm đoạn liên tục dài nhất trong mảng số nguyên có thể có gaps nhỏ."""
        if len(arr) == 0:
            return 0, 0
        best_start = int(arr[0])
        best_len   = 1
        cur_start  = int(arr[0])
        cur_len    = 1
        GAP_TOL    = 3  # cho phép gap tối đa 3 pixel

        for i in range(1, len(arr)):
            gap = arr[i] - arr[i - 1]
            if gap <= GAP_TOL:
                cur_len += gap
            else:
                if cur_len > best_len:
                    best_len  = cur_len
                    best_start = cur_start
                cur_start = int(arr[i])
                cur_len   = 1

        if cur_len > best_len:
            best_len  = cur_len
            best_start = cur_start

        return best_start, best_len

    def _nms(self, pts: list, radius: int = 40) -> list[tuple[int, int]]:
        """Non-maximum suppression để loại bỏ duplicate SHAKE detections."""
        if not pts:
            return []
        pts_sorted = sorted(pts, key=lambda p: -p[2])  # sort by score desc
        kept: list[tuple[int, int, float]] = []
        for p in pts_sorted:
            px, py, _ = p
            if all(
                abs(px - k[0]) > radius or abs(py - k[1]) > radius
                for k in kept
            ):
                kept.append(p)
        return [(x, y) for x, y, _ in kept]

    def _load_shake_template(self) -> np.ndarray | None:
        tpl = cv2.imread("templates/shake_template.png")
        if tpl is None:
            import warnings
            warnings.warn(
                "templates/shake_template.png not found. "
                "SHAKE detection will be disabled until template is provided."
            )
        return tpl
