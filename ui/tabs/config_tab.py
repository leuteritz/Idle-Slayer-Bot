import tkinter as tk
from tkinter import ttk
from dataclasses import fields

from ui.theme import BASE, MANTLE, TEXT, FONT_UI, ScrollableFrame

# Human-readable labels per field name
_LABELS = {
    # BotConfig
    "game_title":              "Spieltitel",
    "disable_failsafe":        "FailSafe deaktivieren",
    "monitor_index":           "Monitor-Index",
    "d_key_interval":          "D-Taste Intervall (s)",
    "r_key_interval":          "R-Taste Intervall (s)",
    "w_mode":                  "W-Modus (1 oder 2)",
    "w_key_cps":               "W-Taste CPS",
    "w_hold_time":             "W lang halten (s)",
    "w_short_count":           "W kurz Anzahl",
    # ChestHuntConfig
    "enabled":                 "Aktiviert",
    "template":                "Template-Datei",
    "wait_per_chest":          "Wartezeit / Kiste (s)",
    "confidence":              "Confidence",
    "rows":                    "Raster-Zeilen",
    "cols":                    "Raster-Spalten",
    "panic_button_template":   "Schließen-Button Template",
    "panic_button_confidence": "Schließen-Button Confidence",
    # BonusStageConfig
    "template_swipe_left":     "Swipe Links Template",
    "template_swipe_right":    "Swipe Rechts Template",
    "swipe_start_offset":      "Swipe Start-Offset (px)",
    "swipe_distance":          "Swipe-Distanz (px)",
    "swipe_duration":          "Swipe-Dauer (s)",
    "close_button_template":   "Schließen-Button Template",
    "close_button_confidence": "Schließen-Button Confidence",
    "jump_hold_time":          "Sprung halten (s)",
    "jump_interval":           "Sprung-Intervall (s)",
}


class ConfigTab:
    def __init__(self, parent, section: str, config_obj, entries: dict):
        sf = ScrollableFrame(parent)
        inner = sf.inner

        tk.Frame(inner, bg=BASE, height=14).pack()

        for i, f in enumerate(fields(config_obj)):
            val   = getattr(config_obj, f.name)
            label = _LABELS.get(f.name, f.name.replace("_", " ").title())

            card = tk.Frame(inner, bg=MANTLE, padx=16, pady=12)
            card.pack(fill="x", padx=20, pady=2)

            tk.Label(card, text=label, bg=MANTLE, fg=TEXT,
                     font=FONT_UI, anchor="w", width=28,
                     justify="left").pack(side="left")

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

            card.bind("<MouseWheel>", sf.scroll_handler)

        tk.Frame(inner, bg=BASE, height=16).pack()
