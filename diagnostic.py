"""
diagnostic.py — Diagnostic utility to verify ROI coordinates and HSV thresholds.
Saves raw crops and color masks to the 'logs/' folder for debugging.
"""

import os
import json
import cv2
import numpy as np
from loguru import logger
from bot.screen_capture import ScreenCapture
from bot.detector import Detector


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        logger.error("config.json not found! Run main.py first to generate default config.")
        return {}
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def main():
    os.makedirs("logs", exist_ok=True)
    config = load_config()
    if not config:
        return

    logger.info("Starting diagnostic capture in 3 seconds...")
    logger.info("--> Please open Roblox, make sure the fishing mini-game (Reeling) is active on screen! <--")
    import time
    for i in range(3, 0, -1):
        logger.info(f"{i}...")
        time.sleep(1.0)

    # 1. Grab frames
    try:
        cap = ScreenCapture(config)
        shake_frame = cap.grab("shake_zone")
        bar_frame   = cap.grab("bar_zone")
        prog_frame  = cap.grab("progress_zone")
        logger.success("Screen capture successful!")
    except Exception as e:
        logger.error(f"Failed to capture screen: {e}")
        return

    # Save raw crops
    cv2.imwrite("logs/diag_shake_raw.png", shake_frame)
    cv2.imwrite("logs/diag_bar_raw.png", bar_frame)
    cv2.imwrite("logs/diag_progress_raw.png", prog_frame)
    logger.info("Saved raw crops to logs/ folder (diag_shake_raw.png, diag_bar_raw.png, diag_progress_raw.png)")

    # 2. Process HSV masks
    hsv = cv2.cvtColor(bar_frame, cv2.COLOR_BGR2HSV)
    
    # Fish bar (gray vertical)
    fish_lo = np.array(config["colors"]["fish_hsv_lower"], dtype=np.uint8)
    fish_hi = np.array(config["colors"]["fish_hsv_upper"], dtype=np.uint8)
    fish_mask = cv2.inRange(hsv, fish_lo, fish_hi)
    
    # Player bar (white horizontal)
    bar_lo = np.array(config["colors"]["bar_hsv_lower"], dtype=np.uint8)
    bar_hi = np.array(config["colors"]["bar_hsv_upper"], dtype=np.uint8)
    bar_mask = cv2.inRange(hsv, bar_lo, bar_hi)

    # Save masks
    cv2.imwrite("logs/diag_fish_mask.png", fish_mask)
    cv2.imwrite("logs/diag_bar_mask.png", bar_mask)
    logger.info("Saved filtered masks to logs/ folder (diag_fish_mask.png, diag_bar_mask.png)")

    # Analyze detection results
    det = Detector(config)
    fish_x, bar_left, bar_w = det.get_bar_positions(bar_frame, config)

    # Check progress bar stats
    prog_gray = cv2.cvtColor(prog_frame, cv2.COLOR_BGR2GRAY)
    white_ratio = float(np.sum(prog_gray > 200)) / prog_gray.size

    logger.info("=== DIAGNOSTIC REPORT ===")
    logger.info(f"Resolution: {config['resolution']}")
    logger.info(f"Bar Zone ROI: {config['roi']['bar_zone']}")
    logger.info(f"Fish Mask white pixels: {np.sum(fish_mask > 0)} / {fish_mask.size}")
    logger.info(f"Player Bar Mask white pixels: {np.sum(bar_mask > 0)} / {bar_mask.size}")
    logger.info(f"Detected Fish Center X: {fish_x}")
    logger.info(f"Detected Player Bar Left X: {bar_left}, Width: {bar_w}")
    logger.info(f"Progress Zone white ratio: {white_ratio:.2f} (Target to finish: {config['thresholds'].get('progress_complete', 0.90)})")
    
    if fish_x is None:
        logger.warning("[!] FISH (gray bar) was NOT detected. Check if color range is correct or if ROI contains the bar.")
    if bar_left is None:
        logger.warning("[!] PLAYER BAR (white bar) was NOT detected. Check if color range is correct or if ROI contains the bar.")
    if fish_x is not None and bar_left is not None:
        logger.success("[+] BOTH BARS DETECTED SUCCESSFULY! Your configuration is correct.")

    logger.info("Diagnostic complete. Please check the 'logs/' directory for images.")


if __name__ == "__main__":
    main()
