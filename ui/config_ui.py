import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import sys
import ctypes
from ctypes import wintypes
from dataclasses import fields
import json
import win32con
from PIL import Image, ImageTk


_WM_HOTKEY  = 0x0312
_PAUSE_KEY  = win32con.VK_F9   # F9 = Pause/Weiter


class _HotkeyThread(threading.Thread):
    """Globaler Win32-Hotkey-Listener (läuft als Daemon-Thread)."""
    def __init__(self, callback):
        super().__init__(daemon=True)
        self._callback = callback
        self._tid      = None

    def run(self):
        self._tid = ctypes.windll.kernel32.GetCurrentThreadId()
        ctypes.windll.user32.RegisterHotKey(None, 1, win32con.MOD_NOREPEAT, _PAUSE_KEY)
        msg = wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == _WM_HOTKEY:
                self._callback()
        ctypes.windll.user32.UnregisterHotKey(None, 1)

    def stop(self):
        if self._tid:
            ctypes.windll.user32.PostThreadMessageW(self._tid, 0x0012, 0, 0)  # WM_QUIT

from bot.config import BotConfig, ChestHuntConfig, BonusStageConfig, export_config, import_config
from ui.log_box import LogBox, QueueStream
from ui.quick_tab import QuickTab
from ui.config_tab import ConfigTab
from ui.sp_scanner_tab import SpScannerTab
from ui.theme import (BASE, MANTLE, CRUST, SURF0, SURF1, TEXT, DIM,
                      BLUE, GREEN, ORANGE, RED, SEPARATOR, TINT_DIM,
                      FONT_UI, FONT_BOLD, FONT_HDR, FONT_SMALL, lighten)

AUTO_SAVE_PATH = "config.json"

NAV_ITEMS = [
    ("quick",   "🚀", "Übersicht"),
    ("bot",     "🤖", "Bot"),
    ("chest",   "📦", "Chest Hunt"),
    ("bonus",   "⭐", "Bonus Stage"),
    ("scanner", "📊", "SP Scanner"),
]


class ConfigUI:
    def __init__(self, bot_config: BotConfig,
                 chest_config: ChestHuntConfig,
                 bonus_config: BonusStageConfig):

        self.bot_config     = bot_config
        self.chest_config   = chest_config
        self.bonus_config   = bonus_config

        self._log_queue   = queue.Queue()
        self._crash_queue = queue.Queue()
        self._stop_event  = threading.Event()
        self._pause_event = threading.Event()
        self._running     = False
        self._paused      = False
        self._entries     = {}
        self._active_page = None
        self._nav_refs    = {}   # page_name -> (frame, inner, lbl)
        self._hotkey_thread: _HotkeyThread = None
        self._sp_data  = {"value": None}

        self.root = tk.Tk()
        self.root.title("Idle Slayer Bot")
        self.root.resizable(True, True)
        self.root.minsize(800, 780)
        self.root.configure(bg=BASE)
        # Fenster-Icon (Taskleiste + Titelzeile)
        try:
            self._win_icon = tk.PhotoImage(file="assets/icon.png")
            self.root.iconphoto(True, self._win_icon)
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._load_auto_save()
        self._apply_style()
        self._build_ui()
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
        self._build_header()
        self._build_body()
        self._build_log()
        self._build_buttons()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=MANTLE)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=SEPARATOR, height=1).pack(side="bottom", fill="x")

        inner = tk.Frame(hdr, bg=MANTLE, padx=24, pady=16)
        inner.pack(fill="x")

        # Icon laden und auf 32×32 skalieren
        try:
            _pil = Image.open("assets/icon.png").resize((32, 32), Image.LANCZOS)
            self._header_icon = ImageTk.PhotoImage(_pil)
            tk.Label(inner, image=self._header_icon,
                    bg=MANTLE).pack(side="left", padx=(0, 8))
        except Exception:
            pass

        tk.Label(inner, text="Idle Slayer Bot",
                bg=MANTLE, fg=TEXT, font=FONT_HDR).pack(side="left")

        # Status pill
        badge = tk.Frame(inner, bg=SURF0, padx=14, pady=6)
        badge.pack(side="right")
        self._status_dot = tk.Label(badge, text="●", bg=SURF0, fg=RED,
                                    font=("SF Pro Display", 10))
        self._status_dot.pack(side="left")
        self._status_lbl = tk.Label(badge, text="  Gestoppt", bg=SURF0, fg=DIM,
                                    font=FONT_UI)
        self._status_lbl.pack(side="left")

        # SP pill
        sp_badge = tk.Frame(inner, bg=SURF0, padx=14, pady=6)
        sp_badge.pack(side="right", padx=(0, 10))
        self._sp_label = tk.Label(sp_badge, text="SP: ---", bg=SURF0,
                                  fg=DIM, font=FONT_UI)
        self._sp_label.pack()

    def _build_body(self):
        body = tk.Frame(self.root, bg=BASE)
        body.pack(fill="both", expand=True)

        # Sidebar — 220px, Apple-style grouped nav
        sidebar = tk.Frame(body, bg=MANTLE, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Frame(sidebar, bg=MANTLE, height=12).pack()   # top padding

        # Sidebar right border
        tk.Frame(body, bg=SEPARATOR, width=1).pack(side="left", fill="y")

        # Content area
        self._content = tk.Frame(body, bg=BASE)
        self._content.pack(side="left", fill="both", expand=True)

        # Build nav + pages
        configs = {"bot":   self.bot_config,
                   "chest": self.chest_config,
                   "bonus": self.bonus_config}

        self._pages = {}

        for key, icon, label in NAV_ITEMS:
            self._make_nav_item(sidebar, key, icon, label)

        tk.Label(sidebar, text="© Leuteritz", bg=MANTLE, fg="#8E8E93",
                 font=("SF Pro Display", 12)).pack(side="bottom", pady=(0, 10))

        p = tk.Frame(self._content, bg=BASE)
        QuickTab(p, configs, self._entries)
        self._pages["quick"] = p

        for key, cfg in [("bot",   self.bot_config),
                          ("chest", self.chest_config),
                          ("bonus", self.bonus_config)]:
            p = tk.Frame(self._content, bg=BASE)
            ConfigTab(p, key, cfg, self._entries)
            self._pages[key] = p

        p = tk.Frame(self._content, bg=BASE)
        self._sp_scanner_tab = SpScannerTab(
            p, self.bot_config.game_title, self._sp_data,
            log_fn=self._log_queue.put)
        self._pages["scanner"] = p

        self._show_page("quick")

    def _make_nav_item(self, parent, page_name: str, icon: str, label: str):
        # Apple-style nav: pill-shaped highlight on active, no accent bar
        frame = tk.Frame(parent, bg=MANTLE, cursor="hand2")
        frame.pack(fill="x", padx=10, pady=1)

        inner = tk.Frame(frame, bg=MANTLE, padx=14, pady=10)
        inner.pack(fill="x")

        # Split icon and label into separate widgets with fixed icon width
        # so mismatched emoji sizes don't break alignment
        icon_lbl = tk.Label(inner, text=icon, bg=MANTLE, fg=DIM,
                            font=FONT_UI, width=2, anchor="center")
        icon_lbl.pack(side="left")

        lbl = tk.Label(inner, text=label, bg=MANTLE, fg=DIM,
                       font=FONT_UI, anchor="w")
        lbl.pack(side="left", padx=(6, 0), fill="x")

        self._nav_refs[page_name] = (frame, inner, lbl, icon_lbl)

        def on_enter(e):
            if self._active_page != page_name:
                for w in (frame, inner): w.config(bg=SURF0)
                lbl.config(bg=SURF0, fg=TEXT)
                icon_lbl.config(bg=SURF0, fg=TEXT)

        def on_leave(e):
            if self._active_page != page_name:
                for w in (frame, inner): w.config(bg=MANTLE)
                lbl.config(bg=MANTLE, fg=DIM)
                icon_lbl.config(bg=MANTLE, fg=DIM)

        def on_click(e):
            self._show_page(page_name)

        for w in (frame, inner, lbl, icon_lbl):
            w.bind("<Enter>",    on_enter)
            w.bind("<Leave>",    on_leave)
            w.bind("<Button-1>", on_click)

    def _show_page(self, page_name: str):
        if self._active_page and self._active_page in self._nav_refs:
            frame, inner, lbl, icon_lbl = self._nav_refs[self._active_page]
            for w in (frame, inner): w.config(bg=MANTLE)
            lbl.config(bg=MANTLE, fg=DIM)
            icon_lbl.config(bg=MANTLE, fg=DIM)
            if self._active_page in self._pages:
                self._pages[self._active_page].pack_forget()

        self._active_page = page_name
        frame, inner, lbl, icon_lbl = self._nav_refs[page_name]
        # Apple-style: subtle fill + blue text for active nav item
        for w in (frame, inner): w.config(bg=SURF0)
        lbl.config(bg=SURF0, fg=BLUE)
        icon_lbl.config(bg=SURF0, fg=BLUE)

        if page_name in self._pages:
            self._pages[page_name].pack(fill="both", expand=True)

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

        make_small_btn("↑ Export", self._export_config).pack(side="left", padx=(12, 2))
        make_small_btn("↓ Import", self._import_config).pack(side="left", padx=2)

    # ── Config apply ──────────────────────────────────────────

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
        self._log_box.log("✅ Konfiguration übernommen.")

    def _refresh_entries(self):
        """Sync all UI entry variables from the current config objects."""
        section_map = {"bot": self.bot_config, "chest": self.chest_config, "bonus": self.bonus_config}
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

    def _export_config(self):
        self._apply_configs_inplace()
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
                f.write(export_config(self.bot_config, self.chest_config, self.bonus_config))
            self._log_box.log(f"✅ Konfiguration exportiert: {path}")
        except OSError as e:
            messagebox.showerror("Export fehlgeschlagen", str(e))

    def _import_config(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON-Datei", "*.json"), ("Alle Dateien", "*.*")],
            title="Konfiguration importieren",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            import_config(data, self.bot_config, self.chest_config, self.bonus_config)
            self._refresh_entries()
            self._log_box.log(f"✅ Konfiguration importiert: {path}")
        except (OSError, json.JSONDecodeError, KeyError) as e:
            messagebox.showerror("Import fehlgeschlagen", str(e))

    def _load_auto_save(self):
        """Load config.json if it exists and update config objects before the UI is built."""
        try:
            with open(AUTO_SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            import_config(data, self.bot_config, self.chest_config, self.bonus_config)
        except FileNotFoundError:
            pass
        except (OSError, json.JSONDecodeError, KeyError):
            pass  # silently ignore a corrupted file

    def _save_auto_save(self):
        """Write current UI values to config objects and persist to config.json."""
        for section, cfg in [("bot",   self.bot_config),
                              ("chest", self.chest_config),
                              ("bonus", self.bonus_config)]:
            self._write_fields(section, cfg)
        try:
            with open(AUTO_SAVE_PATH, "w", encoding="utf-8") as f:
                f.write(export_config(self.bot_config, self.chest_config, self.bonus_config))
        except OSError:
            pass  # best-effort; don't block window close on I/O error

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
                self._on_bot_crashed(kind, msg)
        except queue.Empty:
            pass
        if self._running and hasattr(self, "_bot_thread") and not self._bot_thread.is_alive():
            self._on_bot_crashed("THREAD_DEAD", "Bot-Thread unerwartet beendet.")
        sp = self._sp_data.get("value")
        if sp is not None:
            from bot.memory_reader import format_sp
            self._sp_label.configure(text=f"SP: {format_sp(sp)}", fg=GREEN)
        self.root.after(100, self._poll_log)

    # ── Status ────────────────────────────────────────────────

    def _set_status(self, text: str, dot_color: str):
        self._status_dot.configure(fg=dot_color)
        self._status_lbl.configure(text=f"  {text}")

    def _on_bot_crashed(self, kind: str, msg: str):
        if not self._running:
            return
        self._running = False
        if kind == "FAILSAFE":
            self._log_box.log("❌ PyAutoGUI FailSafe ausgelöst – Maus in Bildschirmecke! "
                              "Bot gestoppt. Option 'disable_failsafe' aktivieren, um zu umgehen.")
        else:
            self._log_box.log(f"❌ Bot abgestürzt: {msg}")
        self._set_status("Abgestürzt", RED)
        self._btn_pause.pack_forget()
        self._btn_resume.pack_forget()
        self._btn_start.pack(side="right", padx=6)

    # ── Button actions ────────────────────────────────────────

    def _toggle_pause(self):
        """Wird vom globalen Hotkey (F9) aufgerufen – thread-safe via root.after."""
        if not self._running:
            return
        self.root.after(0, self._on_resume if self._paused else self._on_pause)

    def _on_start(self):
        self._apply_configs_inplace()
        sys.stdout = QueueStream(self._log_queue)

        self._stop_event.clear()
        self._pause_event.clear()
        self._running = True

        self._hotkey_thread = _HotkeyThread(self._toggle_pause)
        self._hotkey_thread.start()

        from bot.bot import IdleSlayerBot
        bot = IdleSlayerBot(self.bot_config,
                            self.chest_config, self.bonus_config)

        self._bot_thread = threading.Thread(
            target=bot.run,
            kwargs={"stop_event":  self._stop_event,
                    "pause_event": self._pause_event,
                    "crash_queue": self._crash_queue},
            daemon=True
        )
        self._bot_thread.start()

        self._btn_start.pack_forget()
        self._btn_pause.pack(side="right", padx=6)
        self._set_status("Läuft", GREEN)
        self._log_box.log("Bot gestartet.")

    def _on_pause(self):
        if not self._paused:
            self._pause_event.set()
            self._paused = True
            self._log_box.log("⏸ Bot pausiert – Werte können jetzt angepasst werden.")
            self._btn_pause.pack_forget()
            self._btn_resume.pack(side="right", padx=6)
            self._set_status("Pausiert", ORANGE)

    def _on_resume(self):
        if self._paused:
            self._apply_configs_inplace()
            self._pause_event.clear()
            self._paused = False
            self._log_box.log("▶ Bot fortgesetzt mit neuer Konfiguration.")
            self._btn_resume.pack_forget()
            self._btn_pause.pack(side="right", padx=6)
            self._set_status("Läuft", GREEN)

    def _on_close(self):
        self._save_auto_save()
        if self._hotkey_thread:
            self._hotkey_thread.stop()
        self._sp_scanner_tab.stop()
        if self._running:
            self._stop_event.set()
            self._log_box.log("⏹ Bot wird beendet...")
            self.root.after(600, self.root.destroy)
        else:
            self.root.destroy()

    def show(self):
        self.root.mainloop()
