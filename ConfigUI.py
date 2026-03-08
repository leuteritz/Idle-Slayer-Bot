import tkinter as tk
from tkinter import ttk
import threading
import queue
import sys
from dataclasses import fields

from Config import BotConfig, ChestHuntConfig, BonusStageConfig, TargetConfig
from ui.LogBox import LogBox, QueueStream
from ui.QuickTab import QuickTab
from ui.ConfigTab import ConfigTab
from ui.TargetTab import TargetTab


class ConfigUI:
    def __init__(self, bot_config: BotConfig,
                 chest_config: ChestHuntConfig,
                 bonus_config: BonusStageConfig,
                 target_configs: list):

        self.bot_config     = bot_config
        self.chest_config   = chest_config
        self.bonus_config   = bonus_config
        self.target_configs = list(target_configs)

        self._log_queue   = queue.Queue()
        self._crash_queue = queue.Queue()
        self._stop_event  = threading.Event()
        self._pause_event = threading.Event()
        self._running     = False
        self._paused      = False
        self._entries     = {}   # geteilt zwischen QuickTab + ConfigTab

        self.root = tk.Tk()
        self.root.title("Idle Slayer Bot")
        self.root.resizable(True, True)
        self.root.minsize(600, 700)
        self.root.configure(bg="#1e1e2e")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._poll_log()

    # ──────────────────────────────────────────
    #  STYLE
    # ──────────────────────────────────────────

    def _apply_style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TNotebook",       background="#1e1e2e", borderwidth=0)
        s.configure("TNotebook.Tab",   background="#313244", foreground="#cdd6f4",
                                       padding=[14, 6], font=("Consolas", 10))
        s.map("TNotebook.Tab",         background=[("selected", "#89b4fa")],
                                       foreground=[("selected", "#1e1e2e")])
        s.configure("TFrame",          background="#1e1e2e")
        s.configure("TLabel",          background="#1e1e2e", foreground="#cdd6f4",
                                       font=("Consolas", 10))
        s.configure("TEntry",          fieldbackground="#313244", foreground="#cdd6f4",
                                       insertcolor="#cdd6f4", font=("Consolas", 10))
        s.configure("TCheckbutton",    background="#1e1e2e", foreground="#cdd6f4",
                                       font=("Consolas", 10))
        s.map("TCheckbutton",          background=[("active", "#1e1e2e")])
        s.configure("TScrollbar",      background="#313244", troughcolor="#1e1e2e",
                                       arrowcolor="#cdd6f4")
        s.configure("Sep.TFrame",      background="#313244")

    # ──────────────────────────────────────────
    #  UI AUFBAU
    # ──────────────────────────────────────────

    def _build_ui(self):
        self._apply_style()

        # Header
        hdr = tk.Frame(self.root, bg="#181825")
        hdr.pack(fill="x")
        tk.Label(hdr, text="  ⚔  Idle Slayer Bot",
                 bg="#181825", fg="#89b4fa",
                 font=("Consolas", 13, "bold"), pady=10, anchor="w"
                 ).pack(side="left")
        self._status_lbl = tk.Label(hdr, text="● Gestoppt",
                                    bg="#181825", fg="#f38ba8",
                                    font=("Consolas", 10), padx=12)
        self._status_lbl.pack(side="right")

        # Notebook + Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=(8, 2))

        configs = {"bot": self.bot_config,
                   "chest": self.chest_config,
                   "bonus": self.bonus_config}

        tab_quick = ttk.Frame(notebook)
        notebook.add(tab_quick, text="🚀  Übersicht")
        QuickTab(tab_quick, configs, self._entries)

        for label, section, cfg in [
            ("🤖  Bot",         "bot",   self.bot_config),
            ("📦  Chest Hunt",  "chest", self.chest_config),
            ("⭐  Bonus Stage", "bonus", self.bonus_config),
        ]:
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=label)
            ConfigTab(tab, section, cfg, self._entries)

        tab_target = ttk.Frame(notebook)
        notebook.add(tab_target, text="🎯  Targets")
        self._target_tab = TargetTab(tab_target, self.target_configs)

        # Trennlinie + Log
        ttk.Frame(self.root, style="Sep.TFrame", height=2).pack(
            fill="x", padx=10, pady=(6, 0))
        self._log_box = LogBox(self.root)

        # Trennlinie + Buttons
        ttk.Frame(self.root, style="Sep.TFrame", height=2).pack(
            fill="x", padx=10, pady=(4, 0))
        self._build_buttons()

    def _build_buttons(self):
        self._btn_frame = tk.Frame(self.root, bg="#181825", pady=8)
        self._btn_frame.pack(fill="x", padx=10)

        self._btn_start  = self._btn("▶  Starten",  "#a6e3a1", self._on_start)
        self._btn_pause  = self._btn("⏸  Pause",    "#fab387", self._on_pause)
        self._btn_resume = self._btn("▶  Weiter",   "#89b4fa", self._on_resume)
        self._btn_stop   = self._btn("⏹  Beenden",  "#f38ba8", self._on_close)

        self._btn_start.pack(side="right", padx=4)
        self._btn_stop.pack( side="right", padx=4)
        self._btn_pause.pack_forget()
        self._btn_resume.pack_forget()

    def _btn(self, text, color, cmd):
        return tk.Button(
            self._btn_frame, text=text, command=cmd,
            bg=color, fg="#1e1e2e",
            font=("Consolas", 10, "bold"),
            relief="flat", padx=16, pady=6,
            cursor="hand2", activebackground=color, bd=0
        )

    # ──────────────────────────────────────────
    #  CONFIG ANWENDEN
    # ──────────────────────────────────────────

    def _write_fields(self, section: str, config_obj):
        for f in fields(config_obj):
            var = self._entries.get((section, f.name))
            if var is None:
                continue
            current = getattr(config_obj, f.name)
            raw     = var.get()
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
                self._log_box.log(f"⚠ Ungültiger Wert für {f.name}: {raw} ({e})")

    def _apply_configs_inplace(self):
        self._write_fields("bot",   self.bot_config)
        self._write_fields("chest", self.chest_config)
        self._write_fields("bonus", self.bonus_config)
        self.target_configs = self._target_tab.get_targets()
        self._log_box.log("✅ Konfiguration übernommen.")

    # ──────────────────────────────────────────
    #  LOG POLLING
    # ──────────────────────────────────────────

    def _poll_log(self):
        try:
            while True:
                self._log_box.log(self._log_queue.get_nowait())
        except queue.Empty:
            pass
        # Crash-Queue prüfen (FailSafe o.ä.)
        try:
            while True:
                kind, msg = self._crash_queue.get_nowait()
                self._on_bot_crashed(kind, msg)
        except queue.Empty:
            pass
        # Thread unerwartet beendet?
        if self._running and hasattr(self, "_bot_thread") and not self._bot_thread.is_alive():
            self._on_bot_crashed("THREAD_DEAD", "Bot-Thread unerwartet beendet.")
        self.root.after(100, self._poll_log)

    def _set_status(self, text: str, color: str):
        self._status_lbl.configure(text=text, fg=color)

    def _on_bot_crashed(self, kind: str, msg: str):
        """Wird aufgerufen, wenn der Bot-Thread abstürzt (FailSafe, Exception, etc.)."""
        if not self._running:
            return
        self._running = False
        if kind == "FAILSAFE":
            self._log_box.log("❌ PyAutoGUI FailSafe ausgelöst – Maus in Bildschirmecke! "
                              "Bot gestoppt. Option 'disable_failsafe' aktivieren, um zu umgehen.")
        else:
            self._log_box.log(f"❌ Bot abgestürzt: {msg}")
        self._set_status("● Abgestürzt", "#f38ba8")
        self._btn_pause.pack_forget()
        self._btn_resume.pack_forget()
        self._btn_start.pack(side="right", padx=4)

    # ──────────────────────────────────────────
    #  BUTTON AKTIONEN
    # ──────────────────────────────────────────

    def _on_start(self):
        self._apply_configs_inplace()
        sys.stdout = QueueStream(self._log_queue)

        self._stop_event.clear()
        self._pause_event.clear()
        self._running = True

        from Bot import IdleSlayerBot
        bot = IdleSlayerBot(self.bot_config, self.target_configs,
                            self.chest_config, self.bonus_config)

        self._bot_thread = threading.Thread(
            target=bot.run,
            kwargs={"stop_event": self._stop_event, "pause_event": self._pause_event,
                    "crash_queue": self._crash_queue},
            daemon=True
        )
        self._bot_thread.start()

        self._btn_start.pack_forget()
        self._btn_pause.pack(side="right", padx=4)
        self._set_status("● Läuft", "#a6e3a1")
        self._log_box.log("Bot gestartet.")

    def _on_pause(self):
        if not self._paused:
            self._pause_event.set()
            self._paused = True
            self._log_box.log("⏸ Bot pausiert – Werte können jetzt angepasst werden.")
            self._btn_pause.pack_forget()
            self._btn_resume.pack(side="right", padx=4)
            self._set_status("● Pausiert", "#fab387")

    def _on_resume(self):
        if self._paused:
            self._apply_configs_inplace()
            self._pause_event.clear()
            self._paused = False
            self._log_box.log("▶ Bot fortgesetzt mit neuer Konfiguration.")
            self._btn_resume.pack_forget()
            self._btn_pause.pack(side="right", padx=4)
            self._set_status("● Läuft", "#a6e3a1")

    def _on_close(self):
        if self._running:
            self._stop_event.set()
            self._log_box.log("⏹ Bot wird beendet...")
            self.root.after(600, self.root.destroy)
        else:
            self.root.destroy()

    def show(self):
        self.root.mainloop()
