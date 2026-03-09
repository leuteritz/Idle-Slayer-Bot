# ── Apple HIG Dark Mode ──────────────────────────────────────
BASE   = "#000000"       # systemBackground (dark)
MANTLE = "#1C1C1E"       # secondarySystemBackground
CRUST  = "#1C1C1E"       # tertiarySystemBackground (cards)
SURF0  = "#2C2C2E"       # tertiarySystemBackground (inputs)
SURF1  = "#3A3A3C"       # quaternarySystemFill
TEXT   = "#FFFFFF"       # label
DIM    = "#8E8E93"       # secondaryLabel
BLUE   = "#0A84FF"       # systemBlue
GREEN  = "#30D158"       # systemGreen
ORANGE = "#FF9F0A"       # systemOrange
RED    = "#FF453A"       # systemRed
YELLOW = "#FFD60A"       # systemYellow
MAUVE  = "#BF5AF2"       # systemPurple

# Additional Apple HIG colors
SEPARATOR = "#38383A"    # separator (dark)
TINT_DIM  = "#636366"    # tertiaryLabel

# ── Fonts (SF Pro stack with fallbacks) ──────────────────────
_FONT_FAMILY    = "SF Pro Display"
_FONT_FALLBACK  = "Segoe UI"
_FONT_MONO_FAM  = "SF Mono"
_FONT_MONO_FB   = "Consolas"

FONT_UI        = (_FONT_FAMILY, 13)
FONT_BOLD      = (_FONT_FAMILY, 13, "bold")
FONT_HDR       = (_FONT_FAMILY, 20, "bold")          # Large Title
FONT_HDR_SMALL = (_FONT_FAMILY, 11, "bold")          # Subheadline
FONT_SMALL     = (_FONT_FAMILY, 11)                  # Caption 1
FONT_MONO      = (_FONT_MONO_FAM, 11)                # Monospaced
FONT_LABEL     = (_FONT_FAMILY, 9)                   # Caption 2
FONT_MED       = (_FONT_FAMILY, 15, "bold")          # Title 3
FONT_BIG       = (_FONT_FAMILY, 28, "bold")          # Large display


def lighten(hex_color: str, amount: int = 20) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{min(255, r+amount):02x}{min(255, g+amount):02x}{min(255, b+amount):02x}"


# ── Widgets ───────────────────────────────────────────────────
import tkinter as tk
from tkinter import ttk


class ScrollableFrame:
    """Canvas + Scrollbar + MouseWheel wrapper. Use .inner as parent for content."""

    def __init__(self, parent):
        canvas    = tk.Canvas(parent, bg=BASE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=BASE)

        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _scroll(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        canvas.bind("<MouseWheel>", _scroll)
        self.inner.bind("<MouseWheel>", _scroll)
        self.scroll_handler = _scroll
