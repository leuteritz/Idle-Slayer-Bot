import tkinter as tk
from tkinter import ttk
from bot.config import TargetConfig

BASE   = "#1e1e2e"
MANTLE = "#181825"
SURF0  = "#313244"
SURF1  = "#45475a"
TEXT   = "#cdd6f4"
DIM    = "#7f849c"
BLUE   = "#89b4fa"
RED    = "#f38ba8"
CRUST  = "#11111b"

FONT_UI   = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_HDR  = ("Segoe UI", 9, "bold")


def _lighten(hex_color: str, amount: int = 20) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{min(255, r+amount):02x}{min(255, g+amount):02x}{min(255, b+amount):02x}"


class TargetTab:
    def __init__(self, parent, target_configs: list):
        # Header row
        hdr = tk.Frame(parent, bg=MANTLE, padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=SURF0, height=1).pack(side="bottom", fill="x")

        tk.Label(hdr, text="Dateiname", bg=MANTLE, fg=DIM,
                 font=FONT_HDR, width=28, anchor="w").pack(side="left")
        tk.Label(hdr, text="Priorität", bg=MANTLE, fg=DIM,
                 font=FONT_HDR, width=10, anchor="w").pack(side="left")
        tk.Label(hdr, text="", bg=MANTLE, width=4).pack(side="left")

        # Scrollable list
        # Add button — must be packed BEFORE canvas to claim bottom space
        btn_frame = tk.Frame(parent, bg=MANTLE, pady=10)
        btn_frame.pack(side="bottom", fill="x")
        tk.Frame(btn_frame, bg=SURF0, height=1).pack(side="top", fill="x")

        canvas    = tk.Canvas(parent, bg=BASE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self._list_frame = tk.Frame(canvas, bg=BASE)

        self._list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _scroll(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        canvas.bind("<MouseWheel>", _scroll)
        self._list_frame.bind("<MouseWheel>", _scroll)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        add_btn = tk.Button(
            btn_frame, text="＋  Target hinzufügen",
            command=lambda: self._add_row("", 1),
            bg=BLUE, fg=CRUST,
            font=FONT_BOLD, relief="flat",
            padx=16, pady=7, cursor="hand2",
            activebackground=_lighten(BLUE), activeforeground=CRUST, bd=0)
        add_btn.pack(pady=(8, 2))
        add_btn.bind("<Enter>", lambda e: add_btn.config(bg=_lighten(BLUE)))
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
            activebackground=_lighten(RED), activeforeground=CRUST, bd=0)
        del_btn.pack(side="left")
        del_btn.bind("<Enter>", lambda e: del_btn.config(bg=_lighten(RED)))
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
