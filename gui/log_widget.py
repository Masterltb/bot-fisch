"""
log_widget.py — Colored real-time log panel
Hỗ trợ color-coded levels: DEBUG / INFO / SUCCESS / WARNING / ERROR / FISH
"""

import tkinter as tk
import queue
import threading
from datetime import datetime
from gui.theme import *


class LogEntry:
    __slots__ = ("level", "message", "timestamp")

    def __init__(self, level: str, message: str):
        self.level     = level
        self.message   = message
        self.timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]


class LogWidget(tk.Frame):
    """
    ScrolledText với color tags cho từng log level.
    Thread-safe: ghi log từ bất kỳ thread nào.
    """

    LEVEL_CONFIG = {
        "DEBUG":   {"fg": LOG_DEBUG,   "prefix": "  DBG"},
        "INFO":    {"fg": LOG_INFO,    "prefix": " INFO"},
        "SUCCESS": {"fg": LOG_SUCCESS, "prefix": "   OK"},
        "WARNING": {"fg": LOG_WARNING, "prefix": " WARN"},
        "ERROR":   {"fg": LOG_ERROR,   "prefix": "  ERR"},
        "FISH":    {"fg": LOG_FISH,    "prefix": " FISH"},
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_SURFACE, **kwargs)
        self._queue: queue.Queue[LogEntry] = queue.Queue()
        self._line_count = 0
        self._build()
        self._poll()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # Header bar
        header = tk.Frame(self, bg=BG_ELEVATED, height=32)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="● LIVE LOG", bg=BG_ELEVATED,
            fg=ACCENT_GREEN, font=FONT_UI_SM
        ).pack(side="left", padx=PAD)

        # Clear button
        tk.Button(
            header, text="CLEAR", bg=BG_ELEVATED, fg=TEXT_MUTED,
            font=FONT_UI_SM, bd=0, cursor="hand2",
            activebackground=BG_ELEVATED, activeforeground=TEXT_PRIMARY,
            command=self.clear
        ).pack(side="right", padx=PAD)

        # Auto-scroll toggle
        self._auto_scroll = tk.BooleanVar(value=True)
        tk.Checkbutton(
            header, text="Auto-scroll", variable=self._auto_scroll,
            bg=BG_ELEVATED, fg=TEXT_SECONDARY, font=FONT_UI_SM,
            selectcolor=BG_SURFACE, activebackground=BG_ELEVATED,
            activeforeground=TEXT_PRIMARY, bd=0
        ).pack(side="right", padx=4)

        # Log level filter
        self._show_debug = tk.BooleanVar(value=True)
        tk.Checkbutton(
            header, text="DEBUG", variable=self._show_debug,
            bg=BG_ELEVATED, fg=LOG_DEBUG, font=FONT_UI_SM,
            selectcolor=BG_SURFACE, activebackground=BG_ELEVATED,
            activeforeground=LOG_DEBUG, bd=0
        ).pack(side="right", padx=4)

        # Text widget with scrollbar
        text_frame = tk.Frame(self, bg=BG_SURFACE)
        text_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_frame, bg=BG_ELEVATED, troughcolor=BG_BASE,
                                  activebackground=ACCENT_PRIMARY, width=10)
        scrollbar.pack(side="right", fill="y")

        self._text = tk.Text(
            text_frame,
            bg=BG_BASE,
            fg=TEXT_PRIMARY,
            font=FONT_MONO_SM,
            bd=0,
            padx=PAD,
            pady=PAD_SM,
            wrap="word",
            state="disabled",
            yscrollcommand=scrollbar.set,
            selectbackground=ACCENT_PRIMARY,
            insertbackground=ACCENT_PRIMARY,
            relief="flat",
        )
        self._text.pack(fill="both", expand=True)
        scrollbar.config(command=self._text.yview)

        # Configure color tags
        self._text.tag_configure("timestamp", foreground=LOG_TIME, font=FONT_MONO_SM)
        self._text.tag_configure("separator", foreground=TEXT_MUTED, font=FONT_MONO_SM)

        for level, cfg in self.LEVEL_CONFIG.items():
            self._text.tag_configure(
                f"level_{level}", foreground=cfg["fg"],
                font=(FONT_MONO_SM[0], FONT_MONO_SM[1], "bold")
            )
            self._text.tag_configure(f"msg_{level}", foreground=cfg["fg"])

    # ── Public API ────────────────────────────────────────────────────────────

    def log(self, level: str, message: str):
        """Thread-safe log. Gọi từ bất kỳ thread nào."""
        self._queue.put(LogEntry(level.upper(), message))

    def debug(self, msg: str):   self.log("DEBUG", msg)
    def info(self, msg: str):    self.log("INFO", msg)
    def success(self, msg: str): self.log("SUCCESS", msg)
    def warning(self, msg: str): self.log("WARNING", msg)
    def error(self, msg: str):   self.log("ERROR", msg)
    def fish(self, msg: str):    self.log("FISH", msg)

    def clear(self):
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        self._text.config(state="disabled")
        self._line_count = 0

    # ── Internal ──────────────────────────────────────────────────────────────

    def _poll(self):
        """Drain queue và render vào text widget (chạy trên main thread)."""
        try:
            while True:
                entry = self._queue.get_nowait()
                if entry.level == "DEBUG" and not self._show_debug.get():
                    continue
                self._append(entry)
        except queue.Empty:
            pass
        self.after(50, self._poll)   # poll 20×/s — đủ mượt, không tốn CPU

    def _append(self, entry: LogEntry):
        cfg = self.LEVEL_CONFIG.get(entry.level, self.LEVEL_CONFIG["INFO"])
        self._text.config(state="normal")

        # Auto-trim nếu quá nhiều dòng
        if self._line_count >= LOG_MAX_LINES:
            self._text.delete("1.0", "51.0")   # Xóa 50 dòng cũ nhất
            self._line_count -= 50

        # Format: [HH:MM:SS.mmm]  LEVEL  message
        self._text.insert("end", f"[{entry.timestamp}]", "timestamp")
        self._text.insert("end", f" {cfg['prefix']} ", f"level_{entry.level}")
        self._text.insert("end", " │ ", "separator")
        self._text.insert("end", f"{entry.message}\n", f"msg_{entry.level}")

        self._line_count += 1
        self._text.config(state="disabled")

        if self._auto_scroll.get():
            self._text.see("end")
