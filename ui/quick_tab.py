import tkinter as tk
from tkinter import ttk

from ui.theme import (BASE, SURF0, TEXT, DIM, BLUE,
                      FONT_UI, FONT_BOLD, FONT_SMALL, ScrollableFrame)

# (section, field_name, label, description)
QUICK_FIELDS = [
    ("bot",   "disable_failsafe",        "FailSafe deaktivieren",  "Maus in Ecke löst sonst Stop aus"),
    ("bot",   "w_key_cps",              "W-Taste CPS",            "Clicks pro Sekunde für W-Taste"),
    ("bot",   "d_key_interval",          "D-Taste Intervall (s)",  "Alle X Sekunden wird D gedrückt"),
    ("bot",   "r_key_interval",          "R-Taste Intervall (s)",  "Alle X Sekunden wird R gedrückt"),
    ("chest", "confidence",              "Kisten-Confidence",      "Mindestwert für Kisten-Erkennung"),
    ("chest", "wait_per_chest",          "Wartezeit / Kiste (s)",  "Pause nach jedem Kisten-Klick"),
    ("bonus", "jump_interval",           "Bonus: Sprung alle (s)", "Sprungintervall im Bonus Stage"),
    ("bonus", "confidence",              "Bonus-Confidence",       "Mindestwert für Bonus Stage Erkennung"),
]

_SECTION_LABELS = {
    "bot":   ("🤖", "Bot"),
    "chest": ("📦", "Chest Hunt"),
    "bonus": ("⭐", "Bonus Stage"),
}


class QuickTab:
    def __init__(self, parent, configs: dict, entries: dict):
        sf = ScrollableFrame(parent)
        inner = sf.inner

        last_section = None
        row = 0

        for section, field_name, label, desc in QUICK_FIELDS:
            cfg_obj = configs[section]
            val     = getattr(cfg_obj, field_name)

            # Section header
            if section != last_section:
                if last_section is not None:
                    tk.Frame(inner, bg=SURF0, height=1).grid(
                        row=row, column=0, columnspan=2,
                        sticky="ew", padx=16, pady=(2, 10))
                    row += 1

                icon, name = _SECTION_LABELS[section]
                hdr_frame = tk.Frame(inner, bg=BASE)
                hdr_frame.grid(row=row, column=0, columnspan=2,
                               sticky="w", padx=16, pady=(14, 6))
                tk.Label(hdr_frame, text=f"{icon}  {name}",
                         bg=BASE, fg=BLUE, font=FONT_BOLD).pack(side="left")
                row += 1
                last_section = section

            # Reuse or create var
            if (section, field_name) not in entries:
                var = tk.BooleanVar(value=val) if isinstance(val, bool) \
                      else tk.StringVar(value=str(val))
                entries[(section, field_name)] = var
            else:
                var = entries[(section, field_name)]

            # Row card
            card = tk.Frame(inner, bg=SURF0, padx=14, pady=8)
            card.grid(row=row, column=0, columnspan=2,
                      sticky="ew", padx=16, pady=2)
            inner.columnconfigure(0, weight=1)

            label_col = tk.Frame(card, bg=SURF0)
            label_col.pack(side="left", fill="x", expand=True)

            tk.Label(label_col, text=label, bg=SURF0, fg=TEXT,
                     font=FONT_UI, anchor="w").pack(anchor="w")
            tk.Label(label_col, text=desc, bg=SURF0, fg=DIM,
                     font=FONT_SMALL, anchor="w").pack(anchor="w")

            if isinstance(val, bool):
                ttk.Checkbutton(card, variable=var).pack(side="right", padx=(8, 0))
            else:
                ttk.Entry(card, textvariable=var, width=10).pack(side="right", padx=(8, 0))

            card.bind("<MouseWheel>", sf.scroll_handler)
            label_col.bind("<MouseWheel>", sf.scroll_handler)

            row += 1

        # Bottom padding
        tk.Frame(inner, bg=BASE, height=12).grid(row=row, column=0, columnspan=2)
