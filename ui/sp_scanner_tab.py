import tkinter as tk
from tkinter import ttk
import threading
import time

from bot.memory_reader import format_sp
from ui.theme import (BASE, MANTLE, SURF0, TEXT, DIM, BLUE, GREEN, RED, ORANGE,
                      YELLOW, MAUVE, SEPARATOR,
                      FONT_UI, FONT_BOLD, FONT_SMALL, FONT_LABEL, FONT_MED, FONT_BIG,
                      lighten, ScrollableFrame)


def _fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class SpScannerTab:
    def __init__(self, parent, game_title: str = "Idle Slayer", sp_data: dict = None,
                 log_fn=None, key_data: dict = None, sp_var=None):
        self._parent = parent
        self._game_title = game_title
        self._sp_data = sp_data if sp_data is not None else {}
        self._key_data = key_data if key_data is not None else {}
        self._log_fn = log_fn or (lambda msg: None)
        self._sp_var = sp_var if sp_var is not None else tk.StringVar(value="")
        self._memory = None
        self._candidates = []
        self._scan_thread = None
        self._scanning = False
        self._live_updating = False
        self._stop_flag = threading.Event()

        # Session tracking
        self._session_start_time: float | None = None
        self._session_start_sp:   float | None = None
        self._sp_1min_ago:        float | None = None
        self._sp_1min_time:       float | None = None

        self._status_var = tk.StringVar(value="")

        self._build_ui(parent)

    # ------------------------------------------------------------------ UI --

    def _build_ui(self, parent):
        sf = ScrollableFrame(parent)
        self._inner = sf.inner

        # Status-Label
        tk.Label(self._inner, textvariable=self._status_var,
                 bg=BASE, fg=DIM, font=FONT_SMALL, anchor="w").pack(
            fill="x", padx=24, pady=(0, 0))

        # Stats-Frame
        stats = tk.Frame(self._inner, bg=BASE)
        stats.pack(fill="x", padx=24, pady=(6, 16))

        # Große SP-Karte (volle Breite)
        big_card = tk.Frame(stats, bg=MANTLE, padx=24, pady=18)
        big_card.pack(fill="x", pady=(0, 10))
        tk.Label(big_card, text="AKTUELLE SLAYER POINTS",
                 bg=MANTLE, fg=DIM, font=FONT_LABEL).pack(anchor="w")
        self._card_current = tk.StringVar(value="—")
        tk.Label(big_card, textvariable=self._card_current,
                 bg=MANTLE, fg=BLUE, font=FONT_BIG).pack(anchor="w", pady=(6, 0))

        # Zweite Reihe: Farmed + Session-Zeit
        row_a = tk.Frame(stats, bg=BASE)
        row_a.pack(fill="x", pady=(0, 10))
        row_a.columnconfigure(0, weight=1)
        row_a.columnconfigure(1, weight=1)

        self._card_farmed = self._make_card(row_a, "SESSION GEFARMT", GREEN,  0)
        self._card_time   = self._make_card(row_a, "SESSION DAUER",   YELLOW, 1)

        # Dritte Reihe: SP/min + SP/h
        row_b = tk.Frame(stats, bg=BASE)
        row_b.pack(fill="x", pady=(0, 10))
        row_b.columnconfigure(0, weight=1)
        row_b.columnconfigure(1, weight=1)

        self._card_per_min  = self._make_card(row_b, "SP / MINUTE", ORANGE, 0)
        self._card_per_hour = self._make_card(row_b, "SP / STUNDE", MAUVE,  1)

        # Trennlinie
        tk.Frame(self._inner, bg=SEPARATOR, height=1).pack(fill="x", padx=24, pady=(4, 14))

        # Key-Counter-Dashboard
        key_hdr = tk.Frame(self._inner, bg=BASE)
        key_hdr.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(key_hdr, text="Session Tastenzähler",
                 bg=BASE, fg=TEXT, font=FONT_BOLD).pack(side="left")

        reset_btn = tk.Label(key_hdr, text="↺ Zurücksetzen", bg=SURF0, fg=DIM,
                             font=FONT_SMALL, padx=8, pady=2, cursor="hand2")
        reset_btn.pack(side="right")
        reset_btn.bind("<Button-1>", lambda e: self.reset_stats())
        reset_btn.bind("<Enter>", lambda e: reset_btn.config(bg=lighten(SURF0, 0.1), fg=TEXT))
        reset_btn.bind("<Leave>", lambda e: reset_btn.config(bg=SURF0, fg=DIM))

        key_stats = tk.Frame(self._inner, bg=BASE)
        key_stats.pack(fill="x", padx=24, pady=(0, 16))
        key_stats.columnconfigure(0, weight=1)
        key_stats.columnconfigure(1, weight=1)
        key_stats.columnconfigure(2, weight=1)

        self._card_d_key = self._make_key_card(key_stats, "D-TASTE", GREEN,  0)
        self._card_r_key = self._make_key_card(key_stats, "R-TASTE", ORANGE, 1)
        self._card_w_key = self._make_key_card(key_stats, "W-TASTE", BLUE,   2)

        # Trennlinie
        tk.Frame(self._inner, bg=SEPARATOR, height=1).pack(fill="x", padx=24, pady=(4, 14))

        # Chest Hunt Statistik
        ch_hdr = tk.Frame(self._inner, bg=BASE)
        ch_hdr.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(ch_hdr, text="Chest Hunt Statistik",
                 bg=BASE, fg=TEXT, font=FONT_BOLD).pack(side="left")

        ch_stats = tk.Frame(self._inner, bg=BASE)
        ch_stats.pack(fill="x", padx=24, pady=(0, 16))
        ch_stats.columnconfigure(0, weight=1)
        ch_stats.columnconfigure(1, weight=1)
        ch_stats.columnconfigure(2, weight=1)

        self._card_chest_hunts  = self._make_key_card(ch_stats, "CHEST HUNTS",     MAUVE,  0)
        self._card_chests_opened = self._make_key_card(ch_stats, "KISTEN GEÖFFNET", YELLOW, 1)
        self._card_mimics       = self._make_key_card(ch_stats, "MIMIKS",           RED,    2)

        self._parent.after(1000, self._key_poll_loop)

    def _make_key_card(self, parent, label: str, color: str, col: int):
        card = tk.Frame(parent, bg=MANTLE, padx=20, pady=14)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, 10) if col < 2 else (0, 0))
        tk.Label(card, text=label, bg=MANTLE, fg=DIM, font=FONT_LABEL).pack(anchor="w")
        var = tk.StringVar(value="0")
        tk.Label(card, textvariable=var, bg=MANTLE, fg=color,
                 font=FONT_MED).pack(anchor="w", pady=(6, 0))
        return var

    def _make_card(self, parent, label: str, color: str, col: int):
        card = tk.Frame(parent, bg=MANTLE, padx=20, pady=14)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, 10) if col == 0 else (0, 0))
        tk.Label(card, text=label, bg=MANTLE, fg=DIM, font=FONT_LABEL).pack(anchor="w")
        var = tk.StringVar(value="—")
        tk.Label(card, textvariable=var, bg=MANTLE, fg=color,
                 font=FONT_MED).pack(anchor="w", pady=(6, 0))
        return var

    # ---------------------------------------------------------------- Parsing

    @staticmethod
    def _parse_sp(text: str) -> float:
        _SUFFIXES = {"k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12}
        s = text.strip().replace(",", "").replace("_", "").replace(" ", "")
        if s and s[-1].lower() in _SUFFIXES:
            return float(s[:-1]) * _SUFFIXES[s[-1].lower()]
        return float(s)

    # --------------------------------------------------------------- Actions

    def _set_status(self, text: str):
        self._status_var.set(text)

    def _on_scan(self):
        if self._scanning:
            return

        try:
            sp_value = self._parse_sp(self._sp_var.get())
        except ValueError:
            self._set_status("Invalid input – enter your current SP (e.g. 25.1 M, 500 K, 1.2 B).")
            return

        if sp_value <= 0:
            self._set_status("SP value must be greater than 0.")
            return

        tolerance = max(100.0, sp_value * 0.01)
        sp_min = sp_value - tolerance
        sp_max = sp_value + tolerance

        self._scanning = True
        self._stop_flag.clear()

        self._candidates = []
        self._session_start_time = None
        self._session_start_sp   = None
        self._sp_1min_ago        = None
        self._sp_1min_time       = None
        self._reset_cards()

        self._scan_thread = threading.Thread(
            target=self._scan_worker, args=(sp_min, sp_max), daemon=True)
        self._scan_thread.start()

    def _key_poll_loop(self):
        self._card_d_key.set(str(self._key_data.get("d", 0)))
        self._card_r_key.set(str(self._key_data.get("r", 0)))
        self._card_w_key.set(str(self._key_data.get("w", 0)))
        self._card_chest_hunts.set(str(self._key_data.get("chest_hunts", 0)))
        self._card_chests_opened.set(str(self._key_data.get("chests_opened", 0)))
        self._card_mimics.set(str(self._key_data.get("mimics", 0)))
        self._parent.after(1000, self._key_poll_loop)

    def _reset_cards(self):
        self._card_current.set("—")
        self._card_farmed.set("—")
        self._card_time.set("—")
        self._card_per_min.set("—")
        self._card_per_hour.set("—")
        self._sp_data["session_start"] = None

    # -------------------------------------------------------------- Scanning

    def _scan_worker(self, sp_min: float, sp_max: float):
        try:
            self._run_scan(sp_min, sp_max)
        except Exception as e:
            self._parent.after(0, lambda: self._set_status(f"Fehler: {e}"))
        finally:
            self._parent.after(0, self._scan_finished)

    def _scan_finished(self):
        self._scanning = False

    def _run_scan(self, sp_min: float, sp_max: float):
        import win32gui
        from bot.memory_reader import GameMemory

        self._parent.after(0, lambda: self._set_status("Suche Spielfenster..."))
        hwnd = win32gui.FindWindow(None, self._game_title)
        if not hwnd:
            msg = f"[SP] Fenster '{self._game_title}' nicht gefunden!"
            self._log_fn(msg)
            self._parent.after(0, lambda: self._set_status(msg))
            return

        self._log_fn(f"[SP] Suche Adresse für SP-Bereich {format_sp(sp_min)} – {format_sp(sp_max)}...")
        self._memory = GameMemory(hwnd)

        if self._stop_flag.is_set():
            return

        # Scan 1
        self._parent.after(0, lambda: self._set_status("Scan 1 läuft..."))
        hits1 = self._memory.scan_range(sp_min, sp_max)
        n1 = len(hits1)
        self._parent.after(0, lambda: self._set_status(f"Scan 1: {n1} Treffer. Warte 10 s..."))

        if self._stop_flag.is_set():
            return

        for _ in range(100):
            if self._stop_flag.is_set():
                return
            time.sleep(0.1)

        if not hits1:
            self._parent.after(0, lambda: self._set_status("Keine Treffer in Scan 1."))
            return

        # Scan 2
        scan2_min = min(hits1.values()) * 0.995
        scan2_max = max(hits1.values()) * 1.05
        self._parent.after(0, lambda: self._set_status("Scan 2 läuft..."))
        hits2 = self._memory.scan_range(scan2_min, scan2_max)
        n2 = len(hits2)
        self._parent.after(0, lambda: self._set_status(f"Scan 2: {n2} Treffer. Filtere..."))

        if self._stop_flag.is_set():
            return

        # Filter candidates
        candidates = []
        for addr in hits1:
            if addr not in hits2:
                continue
            v1, v2 = hits1[addr], hits2[addr]
            diff = v2 - v1
            if diff <= 0:
                continue
            pct = diff / v1 * 100
            if 0.0001 < pct < 2.5:
                candidates.append((addr, v1, v2))

        candidates.sort(key=lambda x: (x[2] - x[1]) / x[1])

        if not candidates:
            msg = "[SP] Keine Adresse gefunden – Bereich anpassen!"
            self._log_fn(msg)
            self._parent.after(0, lambda: self._set_status(msg))
            return

        best = candidates[0]
        nc   = len(candidates)
        self._log_fn(f"[SP] Adresse gefunden: 0x{best[0]:016X} "
                     f"({nc} Kandidat(en), verwende ersten)")

        # Initialisiere Session
        now = time.time()
        self._session_start_time = now
        self._session_start_sp   = best[2]
        self._sp_1min_ago        = best[2]
        self._sp_1min_time       = now

        self._candidates = [(best[0], best[2], best[2])]
        self._sp_data["value"] = best[2]
        self._sp_data["session_start"] = best[2]

        def init_cards():
            self._card_current.set(format_sp(best[2]))
            self._card_farmed.set("0")
            self._card_time.set("00:00")
            self._card_per_min.set("0")
            self._card_per_hour.set("0")
            self._set_status("")

        self._parent.after(0, init_cards)

        self._live_updating = True
        self._live_update_loop()

    # ---------------------------------------------------------- Live update

    def _live_update_loop(self):
        if not self._live_updating or self._stop_flag.is_set():
            return
        if not self._memory or not self._candidates:
            return

        now = time.time()
        updated = []
        for addr, v_start, v_prev in self._candidates:
            try:
                v_now = self._memory.read_double(addr)
                if v_now is None:
                    v_now = v_prev
            except Exception:
                v_now = v_prev
            updated.append((addr, v_start, v_now))

        self._candidates = updated
        if not updated:
            return

        v_now = updated[0][2]
        self._sp_data["value"] = v_now

        farmed  = max(0.0, v_now - self._session_start_sp) if self._session_start_sp else 0.0
        elapsed = now - self._session_start_time if self._session_start_time else 0.0

        if self._sp_1min_time and self._sp_1min_ago is not None:
            window = now - self._sp_1min_time
            if window >= 60:
                rate_per_min       = (v_now - self._sp_1min_ago) / (window / 60)
                self._sp_1min_ago  = v_now
                self._sp_1min_time = now
            elif elapsed > 0:
                rate_per_min = farmed / (elapsed / 60) if elapsed >= 1 else 0.0
            else:
                rate_per_min = 0.0
        else:
            rate_per_min = 0.0

        rate_per_hour = rate_per_min * 60

        self._card_current.set(format_sp(v_now))
        self._card_farmed.set(format_sp(farmed) if farmed >= 1 else "0")
        self._card_time.set(_fmt_duration(elapsed))
        self._card_per_min.set(format_sp(rate_per_min) if rate_per_min >= 1 else "0")
        self._card_per_hour.set(format_sp(rate_per_hour) if rate_per_hour >= 1 else "0")

        self._parent.after(1000, self._live_update_loop)

    def reset_stats(self):
        """Reset all session statistics to zero."""
        now = time.time()
        current_sp = self._sp_data.get("value")

        # Reset key counters
        for k in ("d", "r", "w", "chest_hunts", "chests_opened", "mimics"):
            self._key_data[k] = 0

        # Reset SP session tracking
        self._session_start_time = now
        self._session_start_sp = current_sp
        self._sp_data["session_start"] = current_sp
        self._sp_1min_ago = current_sp
        self._sp_1min_time = now

        # Reset SP cards
        self._card_farmed.set("0")
        self._card_time.set("00:00")
        self._card_per_min.set("0")
        self._card_per_hour.set("0")

        self._log_fn("[Stats] Statistiken zurückgesetzt.")

    def stop(self):
        """Cleanup when UI closes."""
        self._stop_flag.set()
        self._live_updating = False
        self._sp_data["value"] = None
        self._sp_data["session_start"] = None
        if self._memory:
            self._memory.close()
            self._memory = None
