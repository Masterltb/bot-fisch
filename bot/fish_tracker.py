"""
fish_tracker.py — Edge-Aware Predictive Controller

Cơ chế game:
  - Thanh TRẮNG ngang (Bar)  : player điều khiển bằng hold/release chuột
  - Thanh DỌC XÁM (Fish)     : di chuyển ngẫu nhiên, nhanh/chậm theo độ hiếm cá
  - Mục tiêu                 : giữ Fish NẰM TRONG Bar ở mọi thời điểm

Điều khiển Bar:
  - HOLD   chuột → Bar dịch sang TRÁI
  - RELEASE chuột → Bar dịch sang PHẢI
  (Tức là: Bar chạy về phía ngược hướng với Fish khi Fish lệch)

Logic ưu tiên (theo thứ tự):
  1. EMERGENCY: Fish sắp ra khỏi edge → phản ứng tức thì
  2. PREDICTIVE: Dựa vào velocity của Fish dự đoán sẽ ra edge không
  3. CENTER: Duy trì Fish gần center Bar để có buffer tối đa
"""

from collections import deque
from enum import Enum, auto
from dataclasses import dataclass


class Action(Enum):
    HOLD    = auto()   # Giữ chuột → Bar chạy PHẢI
    RELEASE = auto()   # Thả chuột → Bar chạy TRÁI
    KEEP    = auto()   # Giữ nguyên trạng thái hiện tại


@dataclass
class BarState:
    fish_x: int          # Tọa độ X tâm thanh cá (tuyệt đối trong ROI)
    bar_left: int        # Tọa độ X cạnh trái thanh Bar
    bar_right: int       # Tọa độ X cạnh phải thanh Bar
    bar_width: int       # Chiều rộng thanh Bar

    @property
    def bar_center(self) -> float:
        return (self.bar_left + self.bar_right) / 2.0

    @property
    def fish_offset(self) -> float:
        """Vị trí Fish tương đối so với center Bar. Âm = trái, dương = phải."""
        return self.fish_x - self.bar_center

    @property
    def fish_in_bar(self) -> bool:
        return self.bar_left <= self.fish_x <= self.bar_right

    @property
    def margin_left(self) -> int:
        """Khoảng cách từ Fish đến cạnh trái Bar."""
        return self.fish_x - self.bar_left

    @property
    def margin_right(self) -> int:
        """Khoảng cách từ Fish đến cạnh phải Bar."""
        return self.bar_right - self.fish_x


class FishTracker:
    """
    Edge-Aware Predictive Controller cho mini-game giữ cá.

    Các tham số tuning theo fish profile:
      emergency_margin : Ngưỡng pixel cạnh edge → trigger EMERGENCY response
      predict_frames   : Số frame look-ahead cho velocity prediction
      center_tolerance : Vùng chết quanh center → KEEP (tránh jitter)
    """

    def __init__(
        self,
        emergency_margin: int = 10,
        predict_frames: int = 3,
        center_tolerance: float = 0.20,  # 20% chiều rộng Bar
        history_size: int = 8,
    ):
        self.emergency_margin  = emergency_margin
        self.predict_frames    = predict_frames
        self.center_tolerance  = center_tolerance
        self._history: deque[int] = deque(maxlen=history_size)
        self._last_action = Action.RELEASE

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def update(self, state: BarState) -> Action:
        """
        Nhận BarState hiện tại, trả về Action cần thực hiện.
        Gọi liên tục trong reeling loop (mỗi frame).
        """
        self._history.append(state.fish_x)

        # 1. EMERGENCY — Fish đã ra ngoài hoặc sắp chạm edge
        action = self._emergency_check(state)
        if action is not None:
            self._last_action = action
            return action

        # 2. PREDICTIVE — Dự đoán vị trí tương lai
        action = self._predictive_check(state)
        if action is not None:
            self._last_action = action
            return action

        # 3. CENTER — Căn chỉnh Fish về gần center
        action = self._center_check(state)
        self._last_action = action
        return action

    def reset(self):
        self._history.clear()
        self._last_action = Action.RELEASE

    # ──────────────────────────────────────────────
    # Internal logic
    # ──────────────────────────────────────────────

    def _emergency_check(self, state: BarState) -> Action | None:
        """
        Mức ưu tiên cao nhất.
        Kích hoạt khi Fish ra ngoài Bar HOẶC còn < emergency_margin pixels.
        """
        # Fish đã ra ngoài bên TRÁI → cần Bar chạy TRÁI → RELEASE
        if state.fish_x < state.bar_left:
            return Action.RELEASE

        # Fish đã ra ngoài bên PHẢI → cần Bar chạy PHẢI → HOLD
        if state.fish_x > state.bar_right:
            return Action.HOLD

        # Fish sắp chạm cạnh TRÁI (margin nhỏ) → RELEASE để cứu
        if state.margin_left <= self.emergency_margin:
            return Action.RELEASE

        # Fish sắp chạm cạnh PHẢI (margin nhỏ) → HOLD để cứu
        if state.margin_right <= self.emergency_margin:
            return Action.HOLD

        return None  # Không có emergency

    def _predictive_check(self, state: BarState) -> Action | None:
        """
        Mức ưu tiên trung bình.
        Dùng velocity để dự đoán Fish sẽ chạm edge trong N frames không.
        """
        velocity = self._get_velocity()
        if velocity == 0 or len(self._history) < 2:
            return None

        # Dự đoán vị trí Fish sau predict_frames
        predicted_x = state.fish_x + velocity * self.predict_frames

        # Nếu Fish sẽ ĐI RA TRÁI → RELEASE sớm
        if predicted_x < state.bar_left + self.emergency_margin:
            return Action.RELEASE

        # Nếu Fish sẽ ĐI RA PHẢI → HOLD sớm
        if predicted_x > state.bar_right - self.emergency_margin:
            return Action.HOLD

        return None

    def _center_check(self, state: BarState) -> Action:
        """
        Mức ưu tiên thấp nhất.
        Căn Fish về center Bar để maximize buffer margin.
        """
        tol = state.bar_width * self.center_tolerance
        offset = state.fish_offset  # âm=trái, dương=phải

        # Fish lệch PHẢI → Bar cần đuổi sang PHẢI → HOLD
        if offset > tol:
            return Action.HOLD

        # Fish lệch TRÁI → Bar cần đuổi sang TRÁI → RELEASE
        if offset < -tol:
            return Action.RELEASE

        # Fish trong vùng trung tâm → giữ nguyên
        return Action.KEEP

    def _get_velocity(self) -> float:
        """Tính velocity trung bình từ lịch sử (px/frame)."""
        if len(self._history) < 3:
            return 0.0
        # Dùng weighted average: frame gần nhất có trọng số cao hơn
        hist = list(self._history)
        deltas = [hist[i+1] - hist[i] for i in range(len(hist)-1)]
        weights = list(range(1, len(deltas) + 1))
        weighted = sum(d * w for d, w in zip(deltas, weights))
        return weighted / sum(weights)

    def _get_acceleration(self) -> float:
        """Tính acceleration để detect đổi chiều đột ngột."""
        if len(self._history) < 4:
            return 0.0
        hist = list(self._history)
        d1 = hist[-1] - hist[-2]
        d2 = hist[-2] - hist[-3]
        return d1 - d2
