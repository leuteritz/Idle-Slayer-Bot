import json
import tkinter as tk
from tkinter import filedialog, messagebox
from dataclasses import fields

from bot.config import export_config, import_config

AUTO_SAVE_PATH = "config.json"


class ConfigIO:
    def __init__(self, bot_config, chest_config, bonus_config, entries: dict, log_fn=None):
        self._bot_config = bot_config
        self._chest_config = chest_config
        self._bonus_config = bonus_config
        self._entries = entries
        self.log_fn = log_fn or (lambda msg: None)

    def write_fields(self, section: str, config_obj):
        for f in fields(config_obj):
            var = self._entries.get((section, f.name))
            if var is None:
                continue
            current = getattr(config_obj, f.name)
            raw = var.get()
            try:
                if isinstance(current, bool):
                    new_val = bool(var.get())
                elif isinstance(current, int):
                    new_val = int(raw)
                elif isinstance(current, float):
                    new_val = float(raw)
                else:
                    new_val = raw
                setattr(config_obj, f.name, new_val)
            except (ValueError, TypeError) as e:
                self.log_fn(f"⚠ Ungültiger Wert für {f.name}: {raw} ({e})")

    def apply_configs(self):
        self.write_fields("bot",   self._bot_config)
        self.write_fields("chest", self._chest_config)
        self.write_fields("bonus", self._bonus_config)
        self.log_fn("✅ Konfiguration übernommen.")

    def refresh_entries(self):
        """Sync all UI entry variables from the current config objects."""
        section_map = {"bot": self._bot_config, "chest": self._chest_config, "bonus": self._bonus_config}
        for (section, field_name), var in self._entries.items():
            cfg = section_map.get(section)
            if cfg is None:
                continue
            val = getattr(cfg, field_name, None)
            if val is None:
                continue
            if isinstance(var, tk.BooleanVar):
                var.set(bool(val))
            else:
                var.set(str(val))

    def export_config(self):
        self.apply_configs()
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON-Datei", "*.json"), ("Alle Dateien", "*.*")],
            title="Konfiguration exportieren",
            initialfile="idle_slayer_config.json",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(export_config(self._bot_config, self._chest_config, self._bonus_config))
            self.log_fn(f"✅ Konfiguration exportiert: {path}")
        except OSError as e:
            messagebox.showerror("Export fehlgeschlagen", str(e))

    def import_config(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON-Datei", "*.json"), ("Alle Dateien", "*.*")],
            title="Konfiguration importieren",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            import_config(data, self._bot_config, self._chest_config, self._bonus_config)
            self.refresh_entries()
            self.log_fn(f"✅ Konfiguration importiert: {path}")
        except (OSError, json.JSONDecodeError, KeyError) as e:
            messagebox.showerror("Import fehlgeschlagen", str(e))

    def load_auto_save(self):
        """Load config.json if it exists and update config objects before the UI is built."""
        try:
            with open(AUTO_SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            import_config(data, self._bot_config, self._chest_config, self._bonus_config)
        except (FileNotFoundError, OSError, json.JSONDecodeError, KeyError):
            pass

    def save_auto_save(self):
        """Write current UI values to config objects and persist to config.json."""
        self.write_fields("bot",   self._bot_config)
        self.write_fields("chest", self._chest_config)
        self.write_fields("bonus", self._bonus_config)
        try:
            with open(AUTO_SAVE_PATH, "w", encoding="utf-8") as f:
                f.write(export_config(self._bot_config, self._chest_config, self._bonus_config))
        except OSError:
            pass
