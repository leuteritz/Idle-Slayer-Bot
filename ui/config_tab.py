import tkinter as tk
from tkinter import ttk
from dataclasses import fields

BASE  = "#1e1e2e"
SURF0 = "#313244"
SURF1 = "#45475a"
TEXT  = "#cdd6f4"
DIM   = "#7f849c"

FONT_UI    = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 8)

# Human-readable labels per field name
_LABELS = {
    # BotConfig
    "game_title":              "Game Title",
    "disable_failsafe":        "Disable FailSafe",
    "monitor_index":           "Monitor Index",
    "d_key_interval":          "D Key Interval (s)",
    "space_key_interval":      "Jump Hold Time (s)",
    "space_key_interval_fast": "Jump Hold Fast (s)",
    "space_key_pause":         "Jump Pause (s)",
    "confidence_threshold":    "Detection Confidence",
    "jump_key":                "Jump Key",
    "cooldown":                "Jump Cooldown (s)",
    "check_interval":          "Scan Interval (s)",
    # ChestHuntConfig
    "enabled":                 "Enabled",
    "template":                "Template File",
    "wait_per_chest":          "Wait per Chest (s)",
    "confidence":              "Confidence",
    "rows":                    "Grid Rows",
    "cols":                    "Grid Cols",
    "panic_button_template":   "Close Button Template",
    "panic_button_confidence": "Close Button Confidence",
    # BonusStageConfig
    "template_swipe_left":     "Swipe Left Template",
    "template_swipe_right":    "Swipe Right Template",
    "swipe_start_offset":      "Swipe Start Offset (px)",
    "swipe_distance":          "Swipe Distance (px)",
    "swipe_duration":          "Swipe Duration (s)",
    "close_button_template":   "Close Button Template",
    "close_button_confidence": "Close Button Confidence",
    "jump_hold_time":          "Jump Hold Time (s)",
    "jump_interval":           "Jump Interval (s)",
}


class ConfigTab:
    def __init__(self, parent, section: str, config_obj, entries: dict):
        canvas    = tk.Canvas(parent, bg=BASE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner     = tk.Frame(canvas, bg=BASE)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _scroll(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        canvas.bind("<MouseWheel>", _scroll)
        inner.bind("<MouseWheel>", _scroll)

        tk.Frame(inner, bg=BASE, height=10).pack()

        for i, f in enumerate(fields(config_obj)):
            val   = getattr(config_obj, f.name)
            label = _LABELS.get(f.name, f.name.replace("_", " ").title())

            # Card row
            card = tk.Frame(inner, bg=SURF0, padx=14, pady=10)
            card.pack(fill="x", padx=16, pady=3)

            tk.Label(card, text=label, bg=SURF0, fg=TEXT,
                     font=FONT_UI, anchor="w", width=28,
                     justify="left").pack(side="left")

            # Reuse or create var
            if (section, f.name) not in entries:
                var = tk.BooleanVar(value=val) if isinstance(val, bool) \
                      else tk.StringVar(value=str(val))
                entries[(section, f.name)] = var
            else:
                var = entries[(section, f.name)]

            if isinstance(val, bool):
                ttk.Checkbutton(card, variable=var).pack(side="right")
            else:
                ttk.Entry(card, textvariable=var, width=22).pack(side="right")

            card.bind("<MouseWheel>", _scroll)

        tk.Frame(inner, bg=BASE, height=12).pack()
