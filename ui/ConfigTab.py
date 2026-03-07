import tkinter as tk
from tkinter import ttk
from dataclasses import fields


class ConfigTab:
    """Generischer scrollbarer Tab für eine beliebige Dataclass-Config."""

    def __init__(self, parent, section: str, config_obj, entries: dict):
        canvas    = tk.Canvas(parent, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner     = ttk.Frame(canvas)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left",  fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, f in enumerate(fields(config_obj)):
            val = getattr(config_obj, f.name)

            ttk.Label(inner, text=f.name, width=32, anchor="w").grid(
                row=i, column=0, padx=(14, 6), pady=3, sticky="w")

            # Var wiederverwenden falls schon im Schnell-Tab angelegt
            if (section, f.name) not in entries:
                var = tk.BooleanVar(value=val) if isinstance(val, bool) \
                      else tk.StringVar(value=str(val))
                entries[(section, f.name)] = var
            else:
                var = entries[(section, f.name)]

            if isinstance(val, bool):
                ttk.Checkbutton(inner, variable=var).grid(
                    row=i, column=1, padx=6, pady=3, sticky="w")
            else:
                ttk.Entry(inner, textvariable=var, width=24).grid(
                    row=i, column=1, padx=6, pady=3)
