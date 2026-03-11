import tkinter as tk
from tkinter import ttk

from ui.theme import (BASE, MANTLE, SURF0, TEXT, DIM, BLUE, GREEN,
                      FONT_UI, FONT_BOLD, FONT_SMALL, ScrollableFrame, lighten)


class QuickTab:
    def __init__(self, parent, configs: dict, entries: dict, sp_var=None, scan_fn=None):
        sf = ScrollableFrame(parent)
        inner = sf.inner
        inner.columnconfigure(0, weight=1)

        row = 0

        # ── Current SP Card ──────────────────────────────────
        if sp_var is not None:
            sp_card = tk.Frame(inner, bg=MANTLE, padx=16, pady=14)
            sp_card.grid(row=row, column=0, sticky="ew", padx=20, pady=(20, 2))
            sp_card.bind("<MouseWheel>", sf.scroll_handler)

            tk.Label(sp_card, text="Current SP", bg=MANTLE, fg=TEXT,
                     font=FONT_UI, anchor="w").pack(anchor="w")
            tk.Label(sp_card, text="Aktuelle Slayer Points für den SP-Scanner",
                     bg=MANTLE, fg=DIM, font=FONT_SMALL, anchor="w").pack(anchor="w")

            input_row = tk.Frame(sp_card, bg=MANTLE)
            input_row.pack(fill="x", pady=(10, 0))
            input_row.bind("<MouseWheel>", sf.scroll_handler)
            ttk.Entry(input_row, textvariable=sp_var, width=20).pack(side="left")
            if scan_fn is not None:
                _g = GREEN
                btn = tk.Button(input_row, text="Scan starten", command=scan_fn,
                                bg=_g, fg=BASE, font=FONT_BOLD, relief="flat",
                                padx=14, pady=5, cursor="hand2",
                                activebackground=lighten(_g), activeforeground=BASE, bd=0)
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=lighten(_g)))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=_g))
                btn.pack(side="right")

            tk.Label(sp_card, text="z.B. 14.2 M, 500 K, 1.2 B, 3.5 T",
                     bg=MANTLE, fg=DIM, font=FONT_SMALL, anchor="w").pack(
                anchor="w", pady=(4, 0))
            row += 1

        # ── W-Taste Modus Card ───────────────────────────────
        mode_card = tk.Frame(inner, bg=MANTLE, padx=16, pady=12)
        mode_card.grid(row=row, column=0, sticky="ew", padx=20,
                       pady=(20 if sp_var is None else 12, 2))
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

        for val, label in [(1, "CPS-Spam"), (2, "Lang+Kurz")]:
            tk.Radiobutton(btn_frame, text=label, variable=mode_var,
                           value=val, bg=MANTLE, fg=TEXT, selectcolor=SURF0,
                           activebackground=MANTLE, activeforeground=BLUE,
                           font=FONT_UI, indicatoron=False,
                           padx=12, pady=5, relief="flat", bd=0,
                           highlightthickness=0).pack(side="left", padx=2)

        # ── Bottom spacer ────────────────────────────────────
        tk.Frame(inner, bg=BASE, height=16).grid(row=row, column=0)
