import tkinter as tk
from tkinter import ttk

# (section, field_name, lesbares Label, Beschreibung)
QUICK_FIELDS = [
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
    "bot":   "🤖  Bot",
    "chest": "📦  Chest Hunt",
    "bonus": "⭐  Bonus Stage",
}


class QuickTab:
    """Schnelleinstellungen – nur die wichtigsten Felder, übersichtlich beschriftet."""

    def __init__(self, parent, configs: dict, entries: dict):
        """
        configs: {"bot": BotConfig, "chest": ChestHuntConfig, "bonus": BonusStageConfig}
        entries: gemeinsames Variablen-Dict (wird mit ConfigTab geteilt)
        """
        canvas    = tk.Canvas(parent, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner     = tk.Frame(canvas, bg="#1e1e2e")

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left",  fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        last_section = None
        row          = 0

        for section, field_name, label, desc in QUICK_FIELDS:
            cfg_obj = configs[section]
            val     = getattr(cfg_obj, field_name)

            # Abschnitt-Header
            if section != last_section:
                if last_section is not None:
                    tk.Frame(inner, bg="#313244", height=1).grid(
                        row=row, column=0, columnspan=2,
                        sticky="ew", padx=12, pady=(4, 8))
                    row += 1
                tk.Label(inner, text=_SECTION_LABELS[section],
                         bg="#1e1e2e", fg="#89b4fa",
                         font=("Consolas", 10, "bold")
                         ).grid(row=row, column=0, columnspan=2,
                                sticky="w", padx=12, pady=(10, 4))
                row += 1
                last_section = section

            # Var anlegen oder wiederverwenden
            if (section, field_name) not in entries:
                var = tk.BooleanVar(value=val) if isinstance(val, bool) \
                      else tk.StringVar(value=str(val))
                entries[(section, field_name)] = var
            else:
                var = entries[(section, field_name)]

            # Label mit grauer Beschreibung
            lbl_frame = tk.Frame(inner, bg="#1e1e2e")
            lbl_frame.grid(row=row, column=0, sticky="w", padx=(16, 6), pady=2)
            tk.Label(lbl_frame, text=label, bg="#1e1e2e", fg="#cdd6f4",
                     font=("Consolas", 10), anchor="w", width=26).pack(anchor="w")
            tk.Label(lbl_frame, text=desc,  bg="#1e1e2e", fg="#6c7086",
                     font=("Consolas", 8),  anchor="w").pack(anchor="w")

            # Input
            if isinstance(val, bool):
                ttk.Checkbutton(inner, variable=var).grid(
                    row=row, column=1, padx=6, pady=2, sticky="w")
            else:
                ttk.Entry(inner, textvariable=var, width=10).grid(
                    row=row, column=1, padx=6, pady=2, sticky="w")

            row += 1
