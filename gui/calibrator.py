"""
calibrator.py — Visual ROI calibration tool.
Allows users to drag rectangles on their screen to configure ROIs.
"""

import tkinter as tk
from tkinter import messagebox
import mss
import numpy as np
import cv2
import json
import os
from gui.theme import *


class CalibratorWindow(tk.Toplevel):
    def __init__(self, parent, config: dict, on_save=None):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self.title("📐 toolFisch Calibrator")
        self.geometry("500x320")
        self.configure(bg=BG_SURFACE)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._selected_roi = tk.StringVar(value="bar_zone")
        self._build_ui()

    def _build_ui(self):
        # Header
        tk.Label(
            self, text="📐 VISUAL CALIBRATOR", bg=BG_SURFACE, fg=ACCENT_CYAN,
            font=FONT_TITLE
        ).pack(pady=PAD)

        # Dropdown selection
        frame_sel = tk.Frame(self, bg=BG_SURFACE)
        frame_sel.pack(fill="x", padx=PAD*2, pady=PAD_SM)

        tk.Label(
            frame_sel, text="Select zone to calibrate:", bg=BG_SURFACE,
            fg=TEXT_SECONDARY, font=FONT_UI_SM
        ).pack(anchor="w")

        rois = [
            ("Bar Zone (Minigame)",     "bar_zone"),
            ("Shake Zone (Bubbles)",    "shake_zone"),
            ("Progress Zone (Bottom)",  "progress_zone"),
        ]
        
        for text, value in rois:
            rb = tk.Radiobutton(
                frame_sel, text=text, variable=self._selected_roi, value=value,
                bg=BG_SURFACE, fg=TEXT_PRIMARY, selectcolor=BG_BASE,
                activebackground=BG_SURFACE, activeforeground=ACCENT_CYAN,
                font=FONT_UI_SM, cursor="hand2"
            )
            rb.pack(anchor="w", pady=2)

        # Instructions
        inst_text = (
            "How to calibrate:\n"
            "1. Click 'START CALIBRATION' below.\n"
            "2. Drag a box over the selected zone on your screen.\n"
            "3. Press ESC to cancel, or ENTER/Double-click to save."
        )
        tk.Label(
            self, text=inst_text, bg=BG_ELEVATED, fg=TEXT_SECONDARY,
            font=FONT_LABEL, justify="left", padx=PAD, pady=PAD_SM,
            relief="flat", bd=0
        ).pack(fill="x", padx=PAD*2, pady=PAD)

        # Action Buttons
        btn_frame = tk.Frame(self, bg=BG_SURFACE)
        btn_frame.pack(fill="x", side="bottom", pady=PAD)

        tk.Button(
            btn_frame, text="START CALIBRATION", bg=ACCENT_PRIMARY, fg=TEXT_PRIMARY,
            font=(FONT_UI[0], 11, "bold"), bd=0, cursor="hand2",
            activebackground=ACCENT_GLOW, activeforeground=TEXT_PRIMARY,
            padx=16, pady=8, command=self._start_capture
        ).pack(side="left", padx=PAD*2)

        tk.Button(
            btn_frame, text="CLOSE", bg=BG_BORDER, fg=TEXT_SECONDARY,
            font=FONT_UI_SM, bd=0, cursor="hand2",
            activebackground=BG_SURFACE, activeforeground=TEXT_PRIMARY,
            padx=16, pady=8, command=self.destroy
        ).pack(side="right", padx=PAD*2)

    def _start_capture(self):
        roi_key = self._selected_roi.get()
        self.withdraw()  # Hide calibrator window
        self.master.withdraw()  # Hide main window briefly to clear screen

        # Small delay to let windows hide
        self.after(300, lambda: self._do_overlay(roi_key))

    def _do_overlay(self, roi_key):
        # Capture entire screen
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = np.array(sct.grab(monitor))[:, :, :3]  # BGR

        # Restore main windows
        self.master.deiconify()
        self.deiconify()

        # Open Overlay Window
        OverlayWindow(self, screenshot, roi_key, self._save_roi)

    def _save_roi(self, roi_key, coords):
        self.config["roi"][roi_key] = coords
        # Save to file
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

        messagebox.showinfo(
            "📐 Saved", f"Successfully updated {roi_key} coordinates to:\n{coords}"
        )
        if self.on_save:
            self.on_save()


class OverlayWindow(tk.Toplevel):
    def __init__(self, parent, screenshot, roi_key, callback):
        super().__init__(parent)
        self.screenshot = screenshot
        self.roi_key = roi_key
        self.callback = callback

        # Configure fullscreen borderless overlay
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.config(cursor="cross")

        # Convert screenshot to photoimage
        h, w, _ = screenshot.shape
        self._img_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        
        # Use PIL if installed, else fallback
        try:
            from PIL import Image, ImageTk
            pil_img = Image.fromarray(self._img_rgb)
            self.photo = ImageTk.PhotoImage(image=pil_img)
        except ImportError:
            # Fallback to direct Tk photoimage (slow but works without PIL)
            self.photo = tk.PhotoImage(width=w, height=h)
            # direct pixel writing is too slow, better warn/raise or install PIL
            # PIL is already installed by our command status? Yes, PIL is a sub-dependency of CustomTkinter
            from PIL import Image, ImageTk
            pil_img = Image.fromarray(self._img_rgb)
            self.photo = ImageTk.PhotoImage(image=pil_img)

        self.canvas = tk.Canvas(self, cursor="cross", bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")

        # Overlay color box
        self.rect_id = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._confirm())

        # Title Label Overlay
        title_text = f"DRAG BOX TO SELECT: {self.roi_key.upper()}  |  Press ENTER to confirm  |  ESC to cancel"
        tk.Label(
            self.canvas, text=title_text, bg="#7c3aed", fg="#ffffff",
            font=("Segoe UI", 12, "bold"), padx=20, pady=8
        ).place(relx=0.5, y=40, anchor="n")

    def _on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#06b6d4", width=3
        )

    def _on_drag(self, event):
        self.end_x = event.x
        self.end_y = event.y
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, self.end_x, self.end_y)

    def _on_release(self, event):
        self.end_x = event.x
        self.end_y = event.y

    def _confirm(self):
        if self.start_x is not None and self.end_x is not None:
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)
            
            # Require minimum box size
            if (x2 - x1) > 10 and (y2 - y1) > 10:
                self.callback(self.roi_key, [x1, y1, x2, y2])
                self.destroy()
                return
        messagebox.showwarning("Warning", "Please drag a valid area first!")
