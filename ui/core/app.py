import tkinter as tk
from tkinter import ttk
import threading
import queue
import ctypes
import os
from PIL import Image

from bot.config import BotConfig, ChestHuntConfig, BonusStageConfig
from ui.theme import (BASE, MANTLE, SURF0, SURF1, TEXT, DIM,
                      BLUE, GREEN, ORANGE, RED, SEPARATOR, TINT_DIM,
                      FONT_UI, FONT_BOLD, FONT_SMALL, lighten)
from ui.widgets.log_box import LogBox
from ui.tabs.quick_tab import QuickTab
from ui.tabs.config_tab import ConfigTab
from ui.tabs.sp_scanner_tab import SpScannerTab
from ui.core.config_io import ConfigIO
from ui.core.navigation import NavigationManager
from ui.core.bot_controller import BotController


class ConfigUI:
    def __init__(self, bot_config: BotConfig,
                 chest_config: ChestHuntConfig,
                 bonus_config: BonusStageConfig):

        self.bot_config   = bot_config
        self.chest_config = chest_config
        self.bonus_config = bonus_config

        self._log_queue   = queue.Queue()
        self._crash_queue = queue.Queue()
        self._stop_event  = threading.Event()
        self._pause_event = threading.Event()
        self._entries     = {}
        self._sp_data  = {"value": None, "session_start": None}
        self._key_data = {"d": 0, "r": 0, "w": 0,
                          "chest_hunts": 0, "chests_opened": 0, "mimics": 0}

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("leuteritz.idleslayerbot.1")
        self.root = tk.Tk()
        self.root.title("Idle Slayer Bot")
        self.root.resizable(True, True)
        self.root.minsize(800, 780)
        self.root.configure(bg=BASE)
        # Fenster-Icon (Taskleiste + Titelzeile)
        try:
            ico_path = os.path.join(os.environ.get("TEMP", "."), "idleslayerbot.ico")
            Image.open("assets/icon.png").save(ico_path, format="ICO")
            self.root.iconbitmap(ico_path)
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Config I/O (log_fn set after log box is built)
        self._config_io = ConfigIO(bot_config, chest_config, bonus_config, self._entries)
        self._config_io.load_auto_save()

        # Navigation
        self._nav = NavigationManager(self.root, self._sp_data)

        self._apply_style()
        self._build_ui()

        # Now that log_box exists, wire up ConfigIO logging
        self._config_io.log_fn = self._log_box.log

        # Bot controller
        self._bot_ctrl = BotController(
            bot_config, chest_config, bonus_config,
            self._stop_event, self._pause_event,
            self._log_queue, self._crash_queue, self._key_data,
            apply_fn=self._config_io.apply_configs,
            schedule_fn=lambda fn: self.root.after(0, fn),
            ui_callbacks={
                "set_status":   self._nav.set_status,
                "show_start":   self._show_start_btn,
                "show_pause":   self._show_pause_btn,
                "show_resume":  self._show_resume_btn,
                "log":          self._log_box.log,
            })

        self._poll_log()

    # ── TTK Style ─────────────────────────────────────────────

    def _apply_style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TFrame",       background=BASE)
        s.configure("TLabel",       background=BASE, foreground=TEXT, font=FONT_UI)
        s.configure("TEntry",       fieldbackground=SURF0, foreground=TEXT,
                                    insertcolor=TEXT, font=("SF Mono", 12), borderwidth=0)
        s.configure("TCheckbutton", background=BASE, foreground=TEXT, font=FONT_UI)
        s.map("TCheckbutton",       background=[("active", BASE)])
        s.configure("TScrollbar",   background=SURF1, troughcolor=MANTLE,
                                    arrowcolor=DIM, borderwidth=0)

    # ── Build UI ──────────────────────────────────────────────

    def _build_ui(self):
        self._nav.build_header()
        content = self._nav.build_body()

        self._sp_input_var = tk.StringVar(value="")

        # Quick tab
        p = tk.Frame(content, bg=BASE)
        QuickTab(p, {"bot": self.bot_config, "chest": self.chest_config,
                      "bonus": self.bonus_config},
                 self._entries, sp_var=self._sp_input_var,
                 scan_fn=lambda: self._sp_scanner_tab._on_scan())
        self._nav.register_page("quick", p)

        # Config tabs
        for key, cfg in [("bot",   self.bot_config),
                          ("chest", self.chest_config),
                          ("bonus", self.bonus_config)]:
            p = tk.Frame(content, bg=BASE)
            ConfigTab(p, key, cfg, self._entries)
            self._nav.register_page(key, p)

        # Scanner tab
        p = tk.Frame(content, bg=BASE)
        self._sp_scanner_tab = SpScannerTab(
            p, self.bot_config.game_title, self._sp_data,
            log_fn=self._log_queue.put, key_data=self._key_data,
            sp_var=self._sp_input_var)
        self._nav.register_page("scanner", p)

        self._nav.show_page("quick")
        self._build_log()
        self._build_buttons()

    def _build_log(self):
        tk.Frame(self.root, bg=SEPARATOR, height=1).pack(fill="x")
        self._log_box = LogBox(self.root)

    def _build_buttons(self):
        tk.Frame(self.root, bg=SEPARATOR, height=1).pack(fill="x")
        bar = tk.Frame(self.root, bg=MANTLE, pady=12, padx=20)
        bar.pack(fill="x")

        def make_btn(text, color, cmd):
            lighter = lighten(color)
            b = tk.Button(bar, text=text, command=cmd,
                          bg=color, fg=BASE,
                          font=FONT_BOLD, relief="flat",
                          padx=22, pady=8, cursor="hand2",
                          activebackground=lighter, activeforeground=BASE, bd=0)
            b.bind("<Enter>", lambda e: b.config(bg=lighter))
            b.bind("<Leave>", lambda e: b.config(bg=color))
            return b

        self._btn_start  = make_btn("▶  Starten", GREEN,  self._on_start)
        self._btn_pause  = make_btn("⏸  Pause",   ORANGE, self._on_pause)
        self._btn_resume = make_btn("▶  Weiter",  BLUE,   self._on_resume)
        self._btn_stop   = make_btn("⏹  Beenden", RED,    self._on_close)

        self._btn_stop.pack(side="right", padx=(6, 0))
        self._btn_start.pack(side="right", padx=6)
        self._btn_pause.pack_forget()
        self._btn_resume.pack_forget()

        tk.Label(bar, text="F9: Pause / Weiter", bg=MANTLE, fg=TINT_DIM,
                 font=FONT_SMALL).pack(side="left", padx=4)

        def make_small_btn(text, cmd):
            b = tk.Button(bar, text=text, command=cmd,
                          bg=SURF0, fg=DIM,
                          font=FONT_SMALL, relief="flat",
                          padx=12, pady=6, cursor="hand2",
                          activebackground=SURF1, activeforeground=TEXT, bd=0)
            b.bind("<Enter>", lambda e: b.config(bg=SURF1, fg=TEXT))
            b.bind("<Leave>", lambda e: b.config(bg=SURF0, fg=DIM))
            return b

        make_small_btn("↑ Export", self._config_io.export_config).pack(side="left", padx=(12, 2))
        make_small_btn("↓ Import", self._config_io.import_config).pack(side="left", padx=2)

    # ── Button swap helpers ───────────────────────────────────

    def _show_start_btn(self):
        self._btn_pause.pack_forget()
        self._btn_resume.pack_forget()
        self._btn_start.pack(side="right", padx=6)

    def _show_pause_btn(self):
        self._btn_start.pack_forget()
        self._btn_resume.pack_forget()
        self._btn_pause.pack(side="right", padx=6)

    def _show_resume_btn(self):
        self._btn_pause.pack_forget()
        self._btn_resume.pack(side="right", padx=6)

    # ── Button actions ────────────────────────────────────────

    def _on_start(self):
        self._bot_ctrl.start()

    def _on_pause(self):
        self._bot_ctrl.pause()

    def _on_resume(self):
        self._bot_ctrl.resume()

    # ── Log polling ───────────────────────────────────────────

    def _poll_log(self):
        try:
            while True:
                self._log_box.log(self._log_queue.get_nowait())
        except queue.Empty:
            pass
        try:
            while True:
                kind, msg = self._crash_queue.get_nowait()
                self._bot_ctrl.on_crashed(kind, msg)
        except queue.Empty:
            pass
        if (self._bot_ctrl.running
                and self._bot_ctrl.bot_thread
                and not self._bot_ctrl.bot_thread.is_alive()):
            self._bot_ctrl.on_crashed("THREAD_DEAD", "Bot-Thread unerwartet beendet.")
        self._nav.update_sp_pill()
        self.root.after(100, self._poll_log)

    # ── Close ─────────────────────────────────────────────────

    def _on_close(self):
        self._config_io.save_auto_save()
        self._bot_ctrl.stop_hotkey()
        self._sp_scanner_tab.stop()
        if self._bot_ctrl.running:
            self._bot_ctrl.request_stop()
            self.root.after(600, self.root.destroy)
        else:
            self.root.destroy()

    def show(self):
        self.root.mainloop()
