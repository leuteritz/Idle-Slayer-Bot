import tkinter as tk
from tkinter import ttk
from Config import TargetConfig


class TargetTab:
    """Tab für die Verwaltung der Target-Templates."""

    def __init__(self, parent, target_configs: list):
        hdr = ttk.Frame(parent)
        hdr.pack(fill="x", padx=12, pady=(8, 2))
        ttk.Label(hdr, text="Dateiname",  width=30).grid(row=0, column=0, padx=4)
        ttk.Label(hdr, text="Priorität",  width=10).grid(row=0, column=1, padx=4)

        self._list_frame = ttk.Frame(parent)
        self._list_frame.pack(fill="both", expand=True, padx=12)

        self._rows: list = []
        for t in target_configs:
            self._add_row(t.filename, t.priority)

        tk.Button(parent, text="＋  Target hinzufügen",
                  command=lambda: self._add_row("", 1),
                  bg="#89b4fa", fg="#1e1e2e",
                  font=("Consolas", 10), relief="flat",
                  padx=10, pady=4, cursor="hand2"
                  ).pack(pady=6)

    def _add_row(self, filename: str, priority: int):
        idx      = len(self._rows)
        fn_var   = tk.StringVar(value=filename)
        prio_var = tk.StringVar(value=str(priority))

        ttk.Entry(self._list_frame, textvariable=fn_var,   width=28).grid(
            row=idx, column=0, padx=4, pady=2)
        ttk.Entry(self._list_frame, textvariable=prio_var, width=8).grid(
            row=idx, column=1, padx=4, pady=2)
        tk.Button(self._list_frame, text="✖",
                  command=lambda f=fn_var, p=prio_var: self._remove_row(f, p),
                  bg="#f38ba8", fg="#1e1e2e",
                  font=("Consolas", 9), relief="flat", padx=4, cursor="hand2"
                  ).grid(row=idx, column=2, padx=4)

        self._rows.append((fn_var, prio_var))

    def _remove_row(self, fn_var, prio_var):
        existing = [(f.get(), p.get()) for f, p in self._rows if f is not fn_var]
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._rows = []
        for fn, pr in existing:
            self._add_row(fn, pr)

    def get_targets(self) -> list:
        return [
            TargetConfig(filename=f.get().strip(), priority=int(p.get()))
            for f, p in self._rows
            if f.get().strip()
        ]
