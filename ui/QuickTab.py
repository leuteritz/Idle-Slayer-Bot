import tkinter as tk
from tkinter import ttk

BASE   = "#1e1e2e"
MANTLE = "#181825"
SURF0  = "#313244"
SURF1  = "#45475a"
TEXT   = "#cdd6f4"
DIM    = "#7f849c"
BLUE   = "#89b4fa"

FONT_UI   = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 8)
FONT_HDR  = ("Segoe UI", 9, "bold")

# (section, field_name, label, description)
QUICK_FIELDS = [
    ("bot",   "disable_failsafe",        "FailSafe deaktivieren",  "Maus in Ecke löst sonst Stop aus"),
    ("bot",   "d_key_interval",          "D-Taste Intervall (s)",  "Alle X Sekunden wird D gedrückt"),
    ("bot",   "cooldown",                "Sprung-Cooldown (s)",    "Mindestpause zwischen zwei Sprüngen"),
    ("bot",   "check_interval",          "Scan-Intervall (s)",     "Wie oft pro Sekunde gescannt wird"),
    ("bot",   "confidence_threshold",    "Erkennungs-Confidence",  "Mindestwert für Gegner-Erkennung (0–1)"),
    ("bot",   "space_key_interval",      "Sprung halten (s)",      "Wie lange Leertaste beim 1. Druck"),
    ("bot",   "space_key_interval_fast", "Sprung kurz (s)",        "Wie lange beim 2. schnellen Druck"),
    ("chest", "confidence",              "Chest Confidence",       "Mindestwert für Kisten-Erkennung"),
    ("chest", "wait_per_chest",          "Wartezeit / Kiste (s)",  "Pause nach jedem Kisten-Klick"),
    ("bonus", "jump_interval",           "Bonus: Sprung alle (s)", "Sprungintervall im Bonus Stage"),
    ("bonus", "confidence",              "Bonus Confidence",       "Mindestwert für Bonus Stage Erkennung"),
]

_SECTION_LABELS = {
    "bot":   ("🤖", "Bot"),
    "chest": ("📦", "Chest Hunt"),
    "bonus": ("⭐", "Bonus Stage"),
}


class QuickTab:
    def __init__(self, parent, configs: dict, entries: dict):
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

            card.bind("<MouseWheel>", _scroll)
            label_col.bind("<MouseWheel>", _scroll)

            row += 1

        # Bottom padding
        tk.Frame(inner, bg=BASE, height=12).grid(row=row, column=0, columnspan=2)
