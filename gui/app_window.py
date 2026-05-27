"""
app_window.py — Main GUI Window cho toolFisch
Dark theme, Gen-Z neon palette, Windows native feel

Layout:
┌──────────────────────────────────────────────┐
│  🎣 toolFisch          [_][□][X]             │
├──────────┬───────────────────────────────────┤
│ CONTROLS │         STATS ROW                 │
│  [START] │  Caught │ Failed │ Rate │ Uptime  │
│  profile │                                   │
├──────────┼───────────────────────────────────┤
│ STATE    │         LIVE LOG                  │
│ indicator│  [HH:MM:SS]  LEVEL │ message...  │
│          │  ...                              │
│ FISH     │                                   │
│ counters │                                   │
└──────────┴───────────────────────────────────┘
"""

import tkinter as tk
import time
import threading
import json
import os
from gui.theme import *
from gui.log_widget import LogWidget
from gui.calibrator import CalibratorWindow


class StatCard(tk.Frame):
    """Mini card hiển thị 1 chỉ số."""
    def __init__(self, parent, label: str, value: str = "0", color=TEXT_PRIMARY):
        super().__init__(parent, bg=BG_ELEVATED, bd=0)
        self.config(highlightbackground=BG_BORDER, highlightthickness=1)

        tk.Label(self, text=label, bg=BG_ELEVATED, fg=TEXT_SECONDARY,
                 font=FONT_LABEL).pack(pady=(PAD_SM, 0), padx=PAD)
        self._val_lbl = tk.Label(self, text=value, bg=BG_ELEVATED,
                                  fg=color, font=FONT_STAT_SM)
        self._val_lbl.pack(pady=(0, PAD_SM), padx=PAD)

    def set(self, value: str, color: str = None):
        self._val_lbl.config(text=value)
        if color:
            self._val_lbl.config(fg=color)


class StateBadge(tk.Label):
    """Pill badge thể hiện current state."""
    STATE_MAP = {
        "IDLE":           (STATE_IDLE,    "◉  IDLE"),
        "CASTING":        (ACCENT_CYAN,   "⟳  CASTING"),
        "WAITING_BITE":   (ACCENT_AMBER,  "◌  WAITING BITE"),
        "SHAKING":        (ACCENT_PINK,   "⚡ SHAKING"),
        "REELING":        (ACCENT_GLOW,   "🎣 REELING"),
        "CAUGHT":         (ACCENT_GREEN,  "✓  CAUGHT"),
        "ERROR_RECOVERY": (ACCENT_RED,    "✗  RECOVERING"),
        "STOPPED":        (STATE_IDLE,    "◉  STOPPED"),
    }

    def __init__(self, parent):
        super().__init__(
            parent, text="◉  IDLE", bg=BG_SURFACE,
            fg=STATE_IDLE, font=(FONT_UI[0], 13, "bold"),
            padx=16, pady=8
        )

    def set_state(self, state: str):
        color, text = self.STATE_MAP.get(state, (TEXT_MUTED, state))
        self.config(fg=color, text=text)


class FishCounter(tk.Frame):
    """Hiển thị số cá theo từng tier."""
    TIERS = [
        ("Mythic",    TIER_MYTHIC),
        ("Legendary", TIER_LEGENDARY),
        ("Rare",      TIER_RARE),
        ("Uncommon",  TIER_UNCOMMON),
        ("Common",    TIER_COMMON),
    ]

    def __init__(self, parent):
        super().__init__(parent, bg=BG_SURFACE)
        self._labels: dict[str, tk.Label] = {}
        tk.Label(self, text="FISH COUNTER", bg=BG_SURFACE,
                 fg=TEXT_MUTED, font=FONT_LABEL).pack(anchor="w", padx=PAD)

        for tier, color in self.TIERS:
            row = tk.Frame(self, bg=BG_SURFACE)
            row.pack(fill="x", padx=PAD, pady=1)
            tk.Label(row, text=f"● {tier}", bg=BG_SURFACE, fg=color,
                     font=FONT_UI_SM, width=10, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="0", bg=BG_SURFACE, fg=color,
                           font=(FONT_UI[0], 10, "bold"), width=4, anchor="e")
            lbl.pack(side="right")
            self._labels[tier] = lbl

    def increment(self, tier: str):
        lbl = self._labels.get(tier.capitalize())
        if lbl:
            lbl.config(text=str(int(lbl.cget("text")) + 1))

    def reset(self):
        for lbl in self._labels.values():
            lbl.config(text="0")


class ProfileSelector(tk.Frame):
    """Radio buttons chọn fish profile."""
    PROFILES = [
        ("Common",    "common",    TIER_COMMON),
        ("Uncommon",  "uncommon",  TIER_UNCOMMON),
        ("Rare",      "rare",      TIER_RARE),
        ("Legendary", "legendary", TIER_LEGENDARY),
        ("Mythic",    "mythic",    TIER_MYTHIC),
    ]

    def __init__(self, parent, on_change=None):
        super().__init__(parent, bg=BG_SURFACE)
        self._var = tk.StringVar(value="rare")
        self._on_change = on_change
        tk.Label(self, text="FISH PROFILE", bg=BG_SURFACE,
                 fg=TEXT_MUTED, font=FONT_LABEL).pack(anchor="w", padx=PAD)

        for label, value, color in self.PROFILES:
            rb = tk.Radiobutton(
                self, text=label, variable=self._var, value=value,
                bg=BG_SURFACE, fg=color, selectcolor=BG_BASE,
                activebackground=BG_SURFACE, activeforeground=color,
                font=FONT_UI_SM, bd=0, cursor="hand2",
                command=self._emit
            )
            rb.pack(anchor="w", padx=PAD, pady=1)

    def get(self) -> str:
        return self._var.get()

    def _emit(self):
        if self._on_change:
            self._on_change(self._var.get())


class ToolFischApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._bot = None
        self._start_time: float | None = None
        self._running = False
        self._toggle_lock = False          # BUG FIX: debounce toggle
        self._last_toggle_time = 0.0       # BUG FIX: min interval 300ms

        self._setup_window()
        self._build_ui()
        self._bind_hotkeys()
        self._start_clock()

    # ─── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self):
        self.title("🎣 toolFisch")
        self.geometry("1100x680")
        self.minsize(900, 560)
        self.configure(bg=BG_BASE)
        self.resizable(True, True)

        # Custom titlebar feel (remove default for later, keep for now)
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        # Position: center screen
        self.update_idletasks()
        w, h = 1100, 680
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ─── Build UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Title bar ──────────────────────────────────────────────────────
        self._build_titlebar()

        # ── Stats row ──────────────────────────────────────────────────────
        self._build_stats_row()

        # ── Main body (left panel + log) ───────────────────────────────────
        body = tk.Frame(self, bg=BG_BASE)
        body.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        # Left sidebar
        self._build_sidebar(body)

        # Right log panel
        self._build_log_panel(body)

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=BG_SURFACE, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo + title
        tk.Label(
            bar, text="🎣  toolFisch",
            bg=BG_SURFACE, fg=TEXT_PRIMARY,
            font=(FONT_UI[0], 16, "bold")
        ).pack(side="left", padx=PAD + 4)

        # Subtitle
        tk.Label(
            bar, text="Fisch Auto Bot  ·  External CV",
            bg=BG_SURFACE, fg=TEXT_MUTED, font=FONT_UI_SM
        ).pack(side="left", padx=4)

        # Version badge
        badge = tk.Label(
            bar, text=" v1.0 ", bg=ACCENT_PRIMARY, fg=TEXT_PRIMARY,
            font=FONT_LABEL, padx=4, pady=1
        )
        badge.pack(side="right", padx=PAD + 4, pady=14)

        # Hotkey hint
        tk.Label(
            bar, text="F8 toggle  ·  F9 calibrate",
            bg=BG_SURFACE, fg=TEXT_MUTED, font=FONT_LABEL
        ).pack(side="right", padx=PAD)

        # Separator line
        sep = tk.Frame(self, bg=BG_BORDER, height=1)
        sep.pack(fill="x")

    def _build_stats_row(self):
        row = tk.Frame(self, bg=BG_BASE)
        row.pack(fill="x", padx=PAD, pady=(PAD, 0))

        self._stat_caught  = StatCard(row, "CAUGHT",   "0", ACCENT_GREEN)
        self._stat_failed  = StatCard(row, "FAILED",   "0", ACCENT_RED)
        self._stat_rate    = StatCard(row, "SUCCESS %", "—", ACCENT_CYAN)
        self._stat_uptime  = StatCard(row, "UPTIME",   "00:00:00", TEXT_SECONDARY)
        self._stat_session = StatCard(row, "SESSION CASTS", "0", ACCENT_AMBER)

        for card in (self._stat_caught, self._stat_failed,
                     self._stat_rate, self._stat_uptime, self._stat_session):
            card.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=BG_SURFACE, width=220)
        sidebar.pack(side="left", fill="y", padx=(0, PAD), pady=PAD)
        sidebar.pack_propagate(False)

        # ── START/STOP button ──────────────────────────────────────────────
        self._btn = tk.Button(
            sidebar,
            text="▶  START",
            bg=ACCENT_PRIMARY,
            fg=TEXT_PRIMARY,
            font=(FONT_UI[0], 14, "bold"),
            bd=0, cursor="hand2",
            activebackground=ACCENT_GLOW,
            activeforeground=TEXT_PRIMARY,
            padx=8, pady=12,
            command=self._toggle,
            relief="flat",
        )
        self._btn.pack(fill="x", padx=PAD, pady=(PAD, PAD_SM))

        # ── State badge ───────────────────────────────────────────────────
        self._state_badge = StateBadge(sidebar)
        self._state_badge.pack(padx=PAD, pady=PAD_SM)

        # Divider
        tk.Frame(sidebar, bg=BG_BORDER, height=1).pack(fill="x", padx=PAD, pady=PAD_SM)

        # ── Fish profile ──────────────────────────────────────────────────
        self._profile_sel = ProfileSelector(sidebar, on_change=self._on_profile_change)
        self._profile_sel.pack(fill="x", pady=PAD_SM)

        # Divider
        tk.Frame(sidebar, bg=BG_BORDER, height=1).pack(fill="x", padx=PAD, pady=PAD_SM)

        # ── Fish counter ──────────────────────────────────────────────────
        self._fish_counter = FishCounter(sidebar)
        self._fish_counter.pack(fill="x", pady=PAD_SM)

        # Divider
        tk.Frame(sidebar, bg=BG_BORDER, height=1).pack(fill="x", padx=PAD, pady=PAD_SM)

        # ── Quick actions ─────────────────────────────────────────────────
        tk.Label(sidebar, text="QUICK ACTIONS", bg=BG_SURFACE,
                 fg=TEXT_MUTED, font=FONT_LABEL).pack(anchor="w", padx=PAD)

        for label, cmd in [
            ("📐  Calibrate ROI", self._open_calibrator),
            ("🗑  Clear Log",     lambda: self._log.clear()),
            ("💾  Save Config",  self._save_config),
        ]:
            tk.Button(
                sidebar, text=label, bg=BG_ELEVATED, fg=TEXT_SECONDARY,
                font=FONT_UI_SM, bd=0, cursor="hand2", relief="flat",
                activebackground=BG_BORDER, activeforeground=TEXT_PRIMARY,
                pady=6, anchor="w", padx=PAD,
                command=cmd
            ).pack(fill="x", padx=PAD_SM, pady=1)

    def _build_log_panel(self, parent):
        right = tk.Frame(parent, bg=BG_BASE)
        right.pack(side="left", fill="both", expand=True, pady=PAD)

        # Panel header
        hdr = tk.Frame(right, bg=BG_SURFACE, height=36)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="LIVE DEBUG LOG", bg=BG_SURFACE,
                 fg=TEXT_ACCENT, font=(FONT_UI[0], 11, "bold")).pack(side="left", padx=PAD)
        tk.Label(hdr, text="Color-coded  ·  Thread-safe  ·  500 line buffer",
                 bg=BG_SURFACE, fg=TEXT_MUTED, font=FONT_LABEL).pack(side="left")

        # Log legend
        legend = tk.Frame(right, bg=BG_ELEVATED, height=26)
        legend.pack(fill="x")
        legend.pack_propagate(False)
        for lvl, color in [("INFO", LOG_INFO), ("OK", LOG_SUCCESS),
                           ("WARN", LOG_WARNING), ("ERR", LOG_ERROR),
                           ("FISH", LOG_FISH), ("DBG", LOG_DEBUG)]:
            tk.Label(legend, text=f"■ {lvl}", bg=BG_ELEVATED,
                     fg=color, font=FONT_LABEL).pack(side="left", padx=8)

        # Log widget
        self._log = LogWidget(right)
        self._log.pack(fill="both", expand=True)

        # Startup message
        self._log.info("toolFisch initialized — ready to fish 🎣")
        self._log.debug("Press F8 or click START to begin")
        self._log.debug(f"Config loaded from: {os.path.abspath('config.json')}")

    # ─── Actions ──────────────────────────────────────────────────────────────

    def _toggle(self):
        # BUG FIX: debounce — chặn double-fire từ F8 + button cùng lúc
        import time as _time
        now = _time.monotonic()
        if now - self._last_toggle_time < 0.3:
            return
        self._last_toggle_time = now

        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self._running = True
        self._start_time = time.monotonic()
        self._btn.config(text="⏹  STOP", bg=ACCENT_RED,
                          activebackground="#dc2626")
        self._state_badge.set_state("CASTING")
        self._log.info("Bot started — casting first line...")
        self._log.debug(f"Profile: {self._profile_sel.get().upper()}")

        # BUG FIX: Wire callbacks & start bot AFTER GUI is ready
        if self._bot:
            self._bot.set_callbacks(
                on_state   = self.on_state_change,
                on_caught  = self.on_fish_caught,
                on_failed  = self.on_fish_failed,
            )
            self._bot.set_fish_profile(self._profile_sel.get())
            self._bot.start()

    def _stop(self):
        self._running = False
        self._btn.config(text="▶  START", bg=ACCENT_PRIMARY,
                          activebackground=ACCENT_GLOW)
        self._state_badge.set_state("STOPPED")
        self._log.warning("Bot stopped by user")

        if self._bot:
            self._bot.stop()

    def _on_profile_change(self, profile: str):
        self._log.info(f"Fish profile changed → {profile.upper()}")
        if self._bot:
            self._bot.set_fish_profile(profile)

    def _open_calibrator(self):
        self._log.info("Opening visual calibrator...")
        # Get active config
        if self._bot:
            config = self._bot.config
        else:
            config_path = os.path.abspath('config.json')
            try:
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                config = {}

        if not config:
            self._log.error("Could not load config for calibration.")
            return

        def _on_save():
            self._log.success("ROI updated successfully!")
            # Reload config inside bot if running
            if self._bot:
                self._bot.config = config
                if hasattr(self._bot, 'capture') and self._bot.capture:
                    self._bot.capture.config = config
                # Reload reeling controller config if running
                if hasattr(self._bot, 'reeling') and self._bot.reeling:
                    self._bot.reeling.config = config

        CalibratorWindow(self, config, on_save=_on_save)


    def _save_config(self):
        self._log.success("Config saved")

    # ─── Callbacks from bot ───────────────────────────────────────────────────

    def on_state_change(self, state: str):
        """Gọi từ bot thread khi state thay đổi."""
        self.after(0, lambda: self._state_badge.set_state(state))
        self.after(0, lambda: self._log.debug(f"State → {state}"))

    def on_fish_caught(self, tier: str = "rare"):
        """Gọi từ bot thread khi bắt được cá."""
        def _update():
            caught = int(self._stat_caught._val_lbl.cget("text")) + 1
            failed = int(self._stat_failed._val_lbl.cget("text"))
            total  = caught + failed
            rate   = f"{caught/total*100:.1f}%" if total > 0 else "—"

            self._stat_caught.set(str(caught), ACCENT_GREEN)
            self._stat_rate.set(rate, ACCENT_CYAN)
            self._fish_counter.increment(tier)
            self._log.fish(f"🎣 Caught! Tier: {tier.upper()}  |  Total: {caught}")

        self.after(0, _update)

    def on_fish_failed(self):
        def _update():
            caught = int(self._stat_caught._val_lbl.cget("text"))
            failed = int(self._stat_failed._val_lbl.cget("text")) + 1
            total  = caught + failed
            rate   = f"{caught/total*100:.1f}%" if total > 0 else "—"
            self._stat_failed.set(str(failed), ACCENT_RED)
            self._stat_rate.set(rate, ACCENT_CYAN)
            self._log.error(f"Fish escaped — Failed: {failed}")
        self.after(0, _update)

    def on_log(self, level: str, message: str):
        """Direct log bridge từ bot thread."""
        self._log.log(level, message)

    # ─── Clock / uptime ───────────────────────────────────────────────────────

    def _start_clock(self):
        self._update_uptime()

    def _update_uptime(self):
        if self._running and self._start_time:
            elapsed = int(time.monotonic() - self._start_time)
            h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            self._stat_uptime.set(f"{h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self._update_uptime)

    # ─── Hotkeys ──────────────────────────────────────────────────────────────

    def _bind_hotkeys(self):
        self.bind("<F8>", lambda e: self._toggle())
        self.bind("<F9>", lambda e: self._open_calibrator())
        self.bind("<Escape>", lambda e: self._stop() if self._running else None)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self._running:
            self._stop()
        self.destroy()
