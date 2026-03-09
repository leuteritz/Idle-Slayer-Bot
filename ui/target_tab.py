import tkinter as tk
from tkinter import ttk
from bot.config import TargetConfig

from ui.theme import (BASE, MANTLE, SURF0, TEXT, DIM, BLUE, RED, CRUST,
                      FONT_UI, FONT_BOLD, FONT_HDR_SMALL, lighten, ScrollableFrame)


class TargetTab:
    def __init__(self, parent, target_configs: list):
        # Header row
        hdr = tk.Frame(parent, bg=MANTLE, padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=SURF0, height=1).pack(side="bottom", fill="x")

        tk.Label(hdr, text="Dateiname", bg=MANTLE, fg=DIM,
                 font=FONT_HDR_SMALL, width=28, anchor="w").pack(side="left")
        tk.Label(hdr, text="Priorität", bg=MANTLE, fg=DIM,
                 font=FONT_HDR_SMALL, width=10, anchor="w").pack(side="left")
        tk.Label(hdr, text="", bg=MANTLE, width=4).pack(side="left")

        # Add button — must be packed BEFORE canvas to claim bottom space
        btn_frame = tk.Frame(parent, bg=MANTLE, pady=10)
        btn_frame.pack(side="bottom", fill="x")
        tk.Frame(btn_frame, bg=SURF0, height=1).pack(side="top", fill="x")

        sf = ScrollableFrame(parent)
        self._list_frame = sf.inner

        add_btn = tk.Button(
            btn_frame, text="＋  Target hinzufügen",
            command=lambda: self._add_row("", 1),
            bg=BLUE, fg=CRUST,
            font=FONT_BOLD, relief="flat",
            padx=16, pady=7, cursor="hand2",
            activebackground=lighten(BLUE), activeforeground=CRUST, bd=0)
        add_btn.pack(pady=(8, 2))
        add_btn.bind("<Enter>", lambda e: add_btn.config(bg=lighten(BLUE)))
        add_btn.bind("<Leave>", lambda e: add_btn.config(bg=BLUE))

        self._rows: list = []
        for t in target_configs:
            self._add_row(t.filename, t.priority)

    def _add_row(self, filename: str, priority: int):
        idx      = len(self._rows)
        fn_var   = tk.StringVar(value=filename)
        prio_var = tk.StringVar(value=str(priority))

        row = tk.Frame(self._list_frame, bg=SURF0 if idx % 2 == 0 else BASE, padx=14, pady=8)
        row.pack(fill="x", padx=16, pady=2)

        fn_entry = ttk.Entry(row, textvariable=fn_var, width=28)
        fn_entry.pack(side="left", padx=(0, 8))

        pr_entry = ttk.Entry(row, textvariable=prio_var, width=8)
        pr_entry.pack(side="left", padx=(0, 8))

        del_btn = tk.Button(
            row, text="✖",
            command=lambda f=fn_var, p=prio_var: self._remove_row(f, p),
            bg=RED, fg=CRUST,
            font=("Segoe UI", 9, "bold"), relief="flat",
            padx=8, pady=4, cursor="hand2",
            activebackground=lighten(RED), activeforeground=CRUST, bd=0)
        del_btn.pack(side="left")
        del_btn.bind("<Enter>", lambda e: del_btn.config(bg=lighten(RED)))
        del_btn.bind("<Leave>", lambda e: del_btn.config(bg=RED))

        self._rows.append((fn_var, prio_var, row))

    def _remove_row(self, fn_var, prio_var):
        existing = [(f.get(), p.get()) for f, p, _ in self._rows if f is not fn_var]
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._rows = []
        for fn, pr in existing:
            self._add_row(fn, pr)

    def get_targets(self) -> list:
        return [
            TargetConfig(filename=f.get().strip(), priority=int(p.get()))
            for f, p, _ in self._rows
            if f.get().strip()
        ]
