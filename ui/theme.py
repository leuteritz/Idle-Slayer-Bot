# ── Catppuccin Mocha ──────────────────────────────────────────
BASE   = "#1e1e2e"
MANTLE = "#181825"
CRUST  = "#11111b"
SURF0  = "#313244"
SURF1  = "#45475a"
TEXT   = "#cdd6f4"
DIM    = "#6c7086"
BLUE   = "#89b4fa"
GREEN  = "#a6e3a1"
ORANGE = "#fab387"
RED    = "#f38ba8"
YELLOW = "#f9e2af"
MAUVE  = "#cba6f7"

# ── Fonts ─────────────────────────────────────────────────────
FONT_UI    = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_HDR       = ("Segoe UI", 13, "bold")
FONT_HDR_SMALL = ("Segoe UI", 9, "bold")
FONT_SMALL = ("Segoe UI", 8)
FONT_MONO  = ("Consolas", 9)
FONT_LABEL = ("Segoe UI", 8)
FONT_MED   = ("Segoe UI", 13, "bold")
FONT_BIG   = ("Segoe UI", 22, "bold")


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
