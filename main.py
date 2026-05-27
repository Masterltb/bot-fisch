"""
main.py — Entry point toolFisch
Kết nối GUI ↔ Bot, setup loguru bridge
"""

import json
import os
import sys
import threading
from loguru import logger

# ── Setup loguru trước khi import bot ──────────────────────
logger.remove()   # Xóa default handler

# File sink (persistent logs)
logger.add(
    "logs/fisch.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {message}",
    level="DEBUG",
    encoding="utf-8",
)

# ── Import GUI & Bot ────────────────────────────────────────
from gui.app_window import ToolFischApp


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        _create_default_config(config_path)
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def _create_default_config(path: str):
    """Tạo config.json mặc định nếu chưa có."""
    default = {
        "resolution": [1920, 1080],
        "roi": {
            "shake_zone":    [0, 150, 1920, 500],
            "bar_zone":      [280, 460, 740, 545],
            "progress_zone": [380, 520, 640, 535]
        },
        "colors": {
            "fish_hsv_lower": [0, 0, 100],
            "fish_hsv_upper": [180, 40, 190],
            "bar_hsv_lower":  [0, 0, 210],
            "bar_hsv_upper":  [180, 25, 255]
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
            "common":    {"loop_fps": 30, "emergency_margin": 15, "predict_frames": 2,  "center_tolerance": 0.25},
            "uncommon":  {"loop_fps": 40, "emergency_margin": 12, "predict_frames": 3,  "center_tolerance": 0.20},
            "rare":      {"loop_fps": 50, "emergency_margin": 10, "predict_frames": 3,  "center_tolerance": 0.18},
            "legendary": {"loop_fps": 60, "emergency_margin": 7,  "predict_frames": 4,  "center_tolerance": 0.15},
            "mythic":    {"loop_fps": 60, "emergency_margin": 5,  "predict_frames": 4,  "center_tolerance": 0.10}
        },
        "hotkeys": {
            "toggle_bot":      "f8",
            "open_calibrator": "f9"
        }
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(default, f, indent=2, ensure_ascii=False)
    logger.info(f"Default config created at: {path}")


def _setup_loguru_gui_bridge(app: ToolFischApp):
    """Pipe loguru → GUI log widget (real-time)."""
    LEVEL_MAP = {
        "DEBUG":   "DEBUG",
        "INFO":    "INFO",
        "SUCCESS": "SUCCESS",
        "WARNING": "WARNING",
        "ERROR":   "ERROR",
        "CRITICAL":"ERROR",
    }

    def gui_sink(message):
        record = message.record
        level  = LEVEL_MAP.get(record["level"].name, "INFO")
        text   = record["message"]
        # Route FISH events specially
        if "caught" in text.lower() or "🎣" in text:
            app.on_log("FISH", text)
        else:
            app.on_log(level, text)

    logger.add(gui_sink, level="DEBUG", colorize=False)


def main():
    os.makedirs("logs", exist_ok=True)
    config = load_config()

    app = ToolFischApp()
    _setup_loguru_gui_bridge(app)

    # ── Try to connect bot ──────────────────────────────────
    try:
        from bot.state_machine import FishBot

        def on_stat_update(stats: dict):
            # Được gọi sau mỗi lần caught/failed
            pass  # GUI tự cập nhật qua on_fish_caught / on_fish_failed

        bot = FishBot(config, on_stat_update=on_stat_update)
        app._bot = bot
        logger.success("Bot engine loaded successfully")

    except ImportError as e:
        logger.warning(f"Bot engine not found ({e}) — running in GUI-only mode")

    logger.info(f"Resolution: {config['resolution']}")
    logger.info(f"ROI bar_zone: {config['roi']['bar_zone']}")
    logger.debug("All systems ready — waiting for user input")

    app.mainloop()


if __name__ == "__main__":
    main()
