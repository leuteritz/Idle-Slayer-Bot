import tkinter as tk
from tkinter import ttk

from ui.theme import (BASE, MANTLE, SURF0, TEXT, DIM, BLUE, ORANGE, SEPARATOR,
                      FONT_UI, FONT_BOLD, FONT_SMALL, FONT_HDR_SMALL, ScrollableFrame)

# Felder die NACH dem Modus-Selector kommen
QUICK_FIELDS = [
    ("bot",   "disable_failsafe",  "FailSafe deaktivieren",  "Maus in Ecke löst sonst Stop aus"),
    ("bot",   "d_key_interval",    "D-Taste Intervall (s)",  "Alle X Sekunden wird D gedrückt"),
    ("bot",   "r_key_interval",    "R-Taste Intervall (s)",  "Alle X Sekunden wird R gedrückt"),
    ("chest", "confidence",        "Kisten-Confidence",      "Mindestwert für Kisten-Erkennung"),
    ("chest", "wait_per_chest",    "Wartezeit / Kiste (s)",  "Pause nach jedem Kisten-Klick"),
    ("bonus", "jump_interval",     "Bonus: Sprung alle (s)", "Sprungintervall im Bonus Stage"),
    ("bonus", "confidence",        "Bonus-Confidence",       "Mindestwert für Bonus Stage Erkennung"),
]

_SECTION_LABELS = {
    "bot":   ("🤖", "Bot"),
    "chest": ("📦", "Chest Hunt"),
    "bonus": ("⭐", "Bonus Stage"),
}

# Modus-spezifische Felder
_MODE1_FIELDS = [
    ("bot", "w_key_cps",     "W-Taste CPS",           "Clicks pro Sekunde für W-Taste"),
]
_MODE2_FIELDS = [
    ("bot", "w_hold_time",   "W lang halten (s)",     "Wie lange W gedrückt gehalten wird"),
    ("bot", "w_short_count", "W kurz Anzahl",         "Wie oft W danach kurz gedrückt wird"),
]


class QuickTab:
    def __init__(self, parent, configs: dict, entries: dict):
        sf = ScrollableFrame(parent)
        inner = sf.inner
        self._inner = inner
        self._sf = sf
        self._entries = entries
        self._configs = configs

        row = 0
        inner.columnconfigure(0, weight=1)

        # ── Bot Header ───────────────────────────────────────
        hdr_frame = tk.Frame(inner, bg=BASE)
        hdr_frame.grid(row=row, column=0, columnspan=2,
                       sticky="w", padx=20, pady=(20, 8))
        tk.Label(hdr_frame, text="🤖  Bot",
                 bg=BASE, fg=TEXT, font=FONT_HDR_SMALL).pack(side="left")
        row += 1

        # ── Modus-Auswahl ────────────────────────────────────
        mode_card = tk.Frame(inner, bg=MANTLE, padx=16, pady=12)
        mode_card.grid(row=row, column=0, columnspan=2,
                       sticky="ew", padx=20, pady=2)
        mode_card.bind("<MouseWheel>", sf.scroll_handler)
        row += 1

        label_col = tk.Frame(mode_card, bg=MANTLE)
        label_col.pack(side="left", fill="x", expand=True)
        tk.Label(label_col, text="W-Taste Modus", bg=MANTLE, fg=TEXT,
                 font=FONT_UI, anchor="w").pack(anchor="w")
        tk.Label(label_col, text="Spielmodus für die W-Taste", bg=MANTLE, fg=DIM,
                 font=FONT_SMALL, anchor="w").pack(anchor="w")

        bot_cfg = configs["bot"]
        if ("bot", "w_mode") not in entries:
            mode_var = tk.IntVar(value=bot_cfg.w_mode)
            entries[("bot", "w_mode")] = mode_var
        else:
            mode_var = entries[("bot", "w_mode")]

        btn_frame = tk.Frame(mode_card, bg=MANTLE)
        btn_frame.pack(side="right", padx=(8, 0))

        self._mode_var = mode_var
        self._mode_btns = []

        for val, label in [(1, "CPS-Spam"), (2, "Lang+Kurz")]:
            b = tk.Radiobutton(btn_frame, text=label, variable=mode_var,
                               value=val, command=self._on_mode_change,
                               bg=MANTLE, fg=TEXT, selectcolor=SURF0,
                               activebackground=MANTLE, activeforeground=BLUE,
                               font=FONT_UI, indicatoron=False,
                               padx=12, pady=5, relief="flat", bd=0,
                               highlightthickness=0)
            b.pack(side="left", padx=2)
            self._mode_btns.append(b)

        # ── Modus-spezifische Felder (werden dynamisch ein-/ausgeblendet)
        self._mode_frame = tk.Frame(inner, bg=BASE)
        self._mode_frame.grid(row=row, column=0, columnspan=2,
                              sticky="ew", padx=0, pady=0)
        row += 1
        self._mode_row = row - 1
        self._build_mode_fields()

        # ── Rest: normale Felder ─────────────────────────────
        last_section = "bot"

        for section, field_name, label, desc in QUICK_FIELDS:
            cfg_obj = configs[section]
            val     = getattr(cfg_obj, field_name)

            if section != last_section:
                # Section separator
                tk.Frame(inner, bg=SEPARATOR, height=1).grid(
                    row=row, column=0, columnspan=2,
                    sticky="ew", padx=20, pady=(12, 16))
                row += 1

                icon, name = _SECTION_LABELS[section]
                hdr_frame = tk.Frame(inner, bg=BASE)
                hdr_frame.grid(row=row, column=0, columnspan=2,
                               sticky="w", padx=20, pady=(0, 8))
                tk.Label(hdr_frame, text=f"{icon}  {name}",
                         bg=BASE, fg=TEXT, font=FONT_HDR_SMALL).pack(side="left")
                row += 1
                last_section = section

            if (section, field_name) not in entries:
                var = tk.BooleanVar(value=val) if isinstance(val, bool) \
                      else tk.StringVar(value=str(val))
                entries[(section, field_name)] = var
            else:
                var = entries[(section, field_name)]

            card = tk.Frame(inner, bg=MANTLE, padx=16, pady=10)
            card.grid(row=row, column=0, columnspan=2,
                      sticky="ew", padx=20, pady=2)

            lc = tk.Frame(card, bg=MANTLE)
            lc.pack(side="left", fill="x", expand=True)
            tk.Label(lc, text=label, bg=MANTLE, fg=TEXT,
                     font=FONT_UI, anchor="w").pack(anchor="w")
            tk.Label(lc, text=desc, bg=MANTLE, fg=DIM,
                     font=FONT_SMALL, anchor="w").pack(anchor="w")

            if isinstance(val, bool):
                ttk.Checkbutton(card, variable=var).pack(side="right", padx=(8, 0))
            else:
                ttk.Entry(card, textvariable=var, width=10).pack(side="right", padx=(8, 0))

            card.bind("<MouseWheel>", sf.scroll_handler)
            lc.bind("<MouseWheel>", sf.scroll_handler)
            row += 1

        tk.Frame(inner, bg=BASE, height=16).grid(row=row, column=0, columnspan=2)

    def _build_mode_fields(self):
        for w in self._mode_frame.winfo_children():
            w.destroy()

        mode = self._mode_var.get()
        fields = _MODE1_FIELDS if mode == 1 else _MODE2_FIELDS
        bot_cfg = self._configs["bot"]

        for section, field_name, label, desc in fields:
            val = getattr(bot_cfg, field_name)

            if (section, field_name) not in self._entries:
                var = tk.StringVar(value=str(val))
                self._entries[(section, field_name)] = var
            else:
                var = self._entries[(section, field_name)]

            card = tk.Frame(self._mode_frame, bg=MANTLE, padx=16, pady=10)
            card.pack(fill="x", padx=20, pady=2)

            lc = tk.Frame(card, bg=MANTLE)
            lc.pack(side="left", fill="x", expand=True)
            tk.Label(lc, text=label, bg=MANTLE, fg=TEXT,
                     font=FONT_UI, anchor="w").pack(anchor="w")
            tk.Label(lc, text=desc, bg=MANTLE, fg=DIM,
                     font=FONT_SMALL, anchor="w").pack(anchor="w")

            ttk.Entry(card, textvariable=var, width=10).pack(side="right", padx=(8, 0))

            card.bind("<MouseWheel>", self._sf.scroll_handler)
            lc.bind("<MouseWheel>", self._sf.scroll_handler)

    def _on_mode_change(self):
        self._build_mode_fields()
