"""
theme.py — Gen-Z Dark Theme Color System cho toolFisch
Palette: Deep space dark + neon violet/cyan/green accents
"""

# ── Background layers ──────────────────────────────────────
BG_BASE      = "#0a0a0f"   # Đen sâu - nền chính
BG_SURFACE   = "#12121a"   # Surface cards
BG_ELEVATED  = "#1a1a28"   # Elevated panels
BG_BORDER    = "#2a2a3f"   # Borders, dividers

# ── Accent colors (Gen-Z neon palette) ────────────────────
ACCENT_PRIMARY   = "#7c3aed"   # Violet chính
ACCENT_GLOW      = "#a855f7"   # Violet sáng (hover/active)
ACCENT_CYAN      = "#06b6d4"   # Cyan (secondary)
ACCENT_GREEN     = "#10b981"   # Emerald (success)
ACCENT_AMBER     = "#f59e0b"   # Amber (warning)
ACCENT_RED       = "#ef4444"   # Red (error/stop)
ACCENT_PINK      = "#ec4899"   # Pink (rare fish)

# ── Text ──────────────────────────────────────────────────
TEXT_PRIMARY   = "#f1f5f9"   # Trắng sữa
TEXT_SECONDARY = "#94a3b8"   # Xám nhạt
TEXT_MUTED     = "#475569"   # Xám tối
TEXT_ACCENT    = "#a855f7"   # Violet text

# ── Log level colors ──────────────────────────────────────
LOG_DEBUG    = "#475569"   # Muted gray
LOG_INFO     = "#60a5fa"   # Blue
LOG_SUCCESS  = "#10b981"   # Green
LOG_WARNING  = "#f59e0b"   # Amber
LOG_ERROR    = "#ef4444"   # Red
LOG_FISH     = "#a855f7"   # Violet (fish caught events)
LOG_TIME     = "#94a3b8"   # Secondary for timestamps

# ── Fish tier colors ──────────────────────────────────────
TIER_COMMON    = "#94a3b8"
TIER_UNCOMMON  = "#10b981"
TIER_RARE      = "#60a5fa"
TIER_LEGENDARY = "#f59e0b"
TIER_MYTHIC    = "#ec4899"

# ── State indicator colors ────────────────────────────────
STATE_IDLE     = "#475569"
STATE_RUNNING  = "#10b981"
STATE_CATCHING = "#a855f7"
STATE_ERROR    = "#ef4444"

# ── Font config ───────────────────────────────────────────
FONT_MONO  = ("Cascadia Code", 11)
FONT_MONO_SM = ("Cascadia Code", 10)
FONT_UI    = ("Segoe UI", 11)
FONT_UI_SM = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_STAT  = ("Segoe UI", 22, "bold")
FONT_STAT_SM = ("Segoe UI", 14, "bold")

# ── Size constants ────────────────────────────────────────
RADIUS      = 10
RADIUS_SM   = 6
PAD         = 12
PAD_SM      = 6
LOG_MAX_LINES = 500
