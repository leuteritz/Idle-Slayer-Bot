import tkinter as tk
from tkinter import ttk
import threading
import time

BASE   = "#1e1e2e"
MANTLE = "#181825"
SURF0  = "#313244"
SURF1  = "#45475a"
TEXT   = "#cdd6f4"
DIM    = "#7f849c"
BLUE   = "#89b4fa"
GREEN  = "#a6e3a1"
RED    = "#f38ba8"
ORANGE = "#fab387"
YELLOW = "#f9e2af"
MAUVE  = "#cba6f7"

FONT_UI    = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_MONO  = ("Consolas", 9)
FONT_SMALL = ("Segoe UI", 8)
FONT_HDR   = ("Segoe UI", 9, "bold")
FONT_BIG   = ("Segoe UI", 22, "bold")
FONT_MED   = ("Segoe UI", 13, "bold")
FONT_LABEL = ("Segoe UI", 8)


def _fmt(value: float) -> str:
    """Format a number with K/M/B/T suffix."""
    if value >= 1e12:
        return f"{value / 1e12:.3f} T"
    if value >= 1e9:
        return f"{value / 1e9:.3f} B"
    if value >= 1e6:
        return f"{value / 1e6:.3f} M"
    if value >= 1e3:
        return f"{value / 1e3:.3f} K"
    return f"{value:,.2f}"


def _fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class _StatCard(tk.Frame):
    """A single statistic card with a label and a value."""
    def __init__(self, parent, label: str, color: str = TEXT, wide: bool = False):
        super().__init__(parent, bg=SURF0, padx=16, pady=12)
        tk.Label(self, text=label, bg=SURF0, fg=DIM, font=FONT_LABEL).pack(anchor="w")
        self._var = tk.StringVar(value="—")
        tk.Label(self, textvariable=self._var, bg=SURF0, fg=color,
                 font=FONT_MED if not wide else FONT_BIG).pack(anchor="w", pady=(2, 0))

    def set(self, text: str):
        self._var.set(text)


class SpScannerTab:
    def __init__(self, parent, game_title: str = "Idle Slayer", sp_data: dict = None,
                 log_fn=None):
        self._parent = parent
        self._game_title = game_title
        self._sp_data = sp_data if sp_data is not None else {}
        self._log_fn = log_fn or (lambda msg: None)
        self._memory = None
        self._candidates = []       # [(addr, v_session_start, v_current)]
        self._scan_thread = None
        self._scanning = False
        self._live_updating = False
        self._stop_flag = threading.Event()

        # Session tracking
        self._session_start_time: float | None = None
        self._session_start_sp:   float | None = None
        self._sp_1min_ago:        float | None = None   # SP-Wert vor ~60s für Rate
        self._sp_1min_time:       float | None = None

        self._build_ui(parent)

    # ------------------------------------------------------------------ UI --

    def _build_ui(self, parent):
        canvas    = tk.Canvas(parent, bg=BASE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self._inner = tk.Frame(canvas, bg=BASE)

        self._inner.bind("<Configure>",
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _scroll(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        canvas.bind("<MouseWheel>", _scroll)
        self._inner.bind("<MouseWheel>", _scroll)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self._inner, bg=BASE)
        hdr.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(hdr, text="Slayer Points Scanner",
                 bg=BASE, fg=BLUE, font=FONT_BOLD).pack(side="left")

        # ── Eingabe ─────────────────────────────────────────────────────────
        input_card = tk.Frame(self._inner, bg=SURF0, padx=14, pady=10)
        input_card.pack(fill="x", padx=16, pady=(4, 2))

        row1 = tk.Frame(input_card, bg=SURF0)
        row1.pack(fill="x", pady=2)

        tk.Label(row1, text="SP Min:", bg=SURF0, fg=TEXT, font=FONT_UI).pack(side="left")
        self._sp_min_var = tk.StringVar(value="0")
        ttk.Entry(row1, textvariable=self._sp_min_var, width=18).pack(side="left", padx=(8, 20))

        tk.Label(row1, text="SP Max:", bg=SURF0, fg=TEXT, font=FONT_UI).pack(side="left")
        self._sp_max_var = tk.StringVar(value="0")
        ttk.Entry(row1, textvariable=self._sp_max_var, width=18).pack(side="left", padx=(8, 0))

        tk.Label(input_card, text="Bereich eingeben (z. B. 17.8 M, 500 K, 1.2 B, 3 T)",
                 bg=SURF0, fg=DIM, font=FONT_SMALL, anchor="w").pack(anchor="w", pady=(4, 0))

        # ── Buttons ─────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self._inner, bg=BASE)
        btn_frame.pack(fill="x", padx=16, pady=(8, 4))

        self._btn_scan = tk.Button(
            btn_frame, text="Scan starten", command=self._on_scan,
            bg=GREEN, fg="#11111b", font=FONT_BOLD, relief="flat",
            padx=14, pady=6, cursor="hand2")
        self._btn_scan.pack(side="left", padx=(0, 8))

        self._btn_stop = tk.Button(
            btn_frame, text="Stop", command=self._on_stop,
            bg=RED, fg="#11111b", font=FONT_BOLD, relief="flat",
            padx=14, pady=6, cursor="hand2")

        # ── Status ──────────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="")
        tk.Label(self._inner, textvariable=self._status_var,
                 bg=BASE, fg=DIM, font=FONT_SMALL, anchor="w").pack(
            fill="x", padx=16, pady=(2, 4))

        # ── Trennlinie ──────────────────────────────────────────────────────
        tk.Frame(self._inner, bg=SURF0, height=1).pack(fill="x", padx=16, pady=(2, 12))

        # ── Statistik-Dashboard ─────────────────────────────────────────────
        stats = tk.Frame(self._inner, bg=BASE)
        stats.pack(fill="x", padx=16, pady=(0, 12))

        # Große SP-Karte (volle Breite)
        big_card = tk.Frame(stats, bg=SURF0, padx=20, pady=14)
        big_card.pack(fill="x", pady=(0, 8))
        tk.Label(big_card, text="AKTUELLE SLAYER POINTS",
                 bg=SURF0, fg=DIM, font=FONT_LABEL).pack(anchor="w")
        self._card_current = tk.StringVar(value="—")
        tk.Label(big_card, textvariable=self._card_current,
                 bg=SURF0, fg=BLUE, font=FONT_BIG).pack(anchor="w", pady=(4, 0))

        # Zweite Reihe: Farmed + Session-Zeit
        row_a = tk.Frame(stats, bg=BASE)
        row_a.pack(fill="x", pady=(0, 8))
        row_a.columnconfigure(0, weight=1)
        row_a.columnconfigure(1, weight=1)

        self._card_farmed = self._make_card(row_a, "SESSION GEFARMT", GREEN, 0)
        self._card_time   = self._make_card(row_a, "SESSION DAUER",   YELLOW, 1)

        # Dritte Reihe: SP/min + SP/h
        row_b = tk.Frame(stats, bg=BASE)
        row_b.pack(fill="x", pady=(0, 8))
        row_b.columnconfigure(0, weight=1)
        row_b.columnconfigure(1, weight=1)

        self._card_per_min  = self._make_card(row_b, "SP / MINUTE",  ORANGE, 0)
        self._card_per_hour = self._make_card(row_b, "SP / STUNDE",  MAUVE,  1)

    def _make_card(self, parent, label: str, color: str, col: int):
        card = tk.Frame(parent, bg=SURF0, padx=16, pady=12)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, 8) if col == 0 else (0, 0))
        tk.Label(card, text=label, bg=SURF0, fg=DIM, font=FONT_LABEL).pack(anchor="w")
        var = tk.StringVar(value="—")
        tk.Label(card, textvariable=var, bg=SURF0, fg=color,
                 font=FONT_MED).pack(anchor="w", pady=(4, 0))
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
            sp_min = self._parse_sp(self._sp_min_var.get())
            sp_max = self._parse_sp(self._sp_max_var.get())
        except ValueError:
            self._set_status("Ungültige Eingabe – bitte Zahlen eingeben (z. B. 17.8 M, 500 K).")
            return

        if sp_min >= sp_max:
            self._set_status("SP Min muss kleiner als SP Max sein.")
            return

        self._scanning = True
        self._stop_flag.clear()
        self._btn_scan.pack_forget()
        self._btn_stop.pack(side="left", padx=(0, 8))

        self._candidates = []
        self._session_start_time = None
        self._session_start_sp   = None
        self._sp_1min_ago        = None
        self._sp_1min_time       = None
        self._reset_cards()

        self._scan_thread = threading.Thread(
            target=self._scan_worker, args=(sp_min, sp_max), daemon=True)
        self._scan_thread.start()

    def _on_stop(self):
        self._stop_flag.set()
        self._live_updating = False
        self._scanning = False
        self._sp_data["value"] = None
        self._btn_stop.pack_forget()
        self._btn_scan.pack(side="left", padx=(0, 8))
        self._set_status("Scan abgebrochen.")
        if self._memory:
            self._memory.close()
            self._memory = None

    def _reset_cards(self):
        self._card_current.set("—")
        self._card_farmed.set("—")
        self._card_time.set("—")
        self._card_per_min.set("—")
        self._card_per_hour.set("—")

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
        self._btn_stop.pack_forget()
        self._btn_scan.pack(side="left", padx=(0, 8))

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

        self._log_fn(f"[SP] Suche Adresse für SP-Bereich {_fmt(sp_min)} – {_fmt(sp_max)}...")
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

        def init_cards():
            self._card_current.set(_fmt(best[2]))
            self._card_farmed.set("0")
            self._card_time.set("00:00")
            self._card_per_min.set("0")
            self._card_per_hour.set("0")
            self._set_status(f"Adresse gefunden – Live-Tracking aktiv ({nc} Kandidat(en))")

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

        # Farmed since session start
        farmed = max(0.0, v_now - self._session_start_sp) if self._session_start_sp else 0.0

        # Session duration
        elapsed = now - self._session_start_time if self._session_start_time else 0.0

        # SP/min rate: use sliding 60s window
        if self._sp_1min_time and self._sp_1min_ago is not None:
            window = now - self._sp_1min_time
            if window >= 60:
                rate_per_min  = (v_now - self._sp_1min_ago) / (window / 60)
                # slide the window forward
                self._sp_1min_ago  = v_now
                self._sp_1min_time = now
            elif elapsed > 0:
                # Not enough time yet – use full session average
                rate_per_min = farmed / (elapsed / 60) if elapsed >= 1 else 0.0
            else:
                rate_per_min = 0.0
        else:
            rate_per_min = 0.0

        rate_per_hour = rate_per_min * 60

        self._card_current.set(_fmt(v_now))
        self._card_farmed.set(_fmt(farmed) if farmed >= 1 else "0")
        self._card_time.set(_fmt_duration(elapsed))
        self._card_per_min.set(_fmt(rate_per_min) if rate_per_min >= 1 else "0")
        self._card_per_hour.set(_fmt(rate_per_hour) if rate_per_hour >= 1 else "0")

        self._parent.after(1000, self._live_update_loop)

    def stop(self):
        """Cleanup when UI closes."""
        self._stop_flag.set()
        self._live_updating = False
        self._sp_data["value"] = None
        if self._memory:
            self._memory.close()
            self._memory = None
