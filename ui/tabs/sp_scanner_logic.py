import threading
import time

from bot.memory_reader import format_sp


def _fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class SpScannerLogic:
    """Memory-Scan + Live-Update Worker for SP tracking (no UI code)."""

    def __init__(self, game_title, sp_data, log_fn, schedule):
        self._game_title = game_title
        self._sp_data = sp_data
        self._log_fn = log_fn or (lambda msg: None)
        self._schedule = schedule  # parent.after(ms, fn)

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

        # Callbacks – set by the UI tab after construction
        self.on_status = None       # fn(text)
        self.on_cards_init = None   # fn(current_sp_str)
        self.on_cards_update = None # fn(current, farmed, time, rate_min, rate_hour)
        self.on_cards_reset = None  # fn()

    @staticmethod
    def parse_sp(text: str) -> float:
        _SUFFIXES = {"k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12}
        s = text.strip().replace(",", "").replace("_", "").replace(" ", "")
        if s and s[-1].lower() in _SUFFIXES:
            return float(s[:-1]) * _SUFFIXES[s[-1].lower()]
        return float(s)

    def start_scan(self, sp_text: str):
        if self._scanning:
            return

        try:
            sp_value = self.parse_sp(sp_text)
        except ValueError:
            if self.on_status:
                self.on_status("Invalid input – enter your current SP (e.g. 25.1 M, 500 K, 1.2 B).")
            return

        if sp_value <= 0:
            if self.on_status:
                self.on_status("SP value must be greater than 0.")
            return

        tolerance = max(100.0, sp_value * 0.01)
        sp_min = sp_value - tolerance
        sp_max = sp_value + tolerance

        self._scanning = True
        self._stop_flag.clear()

        self._candidates = []
        self._session_start_time = None
        self._session_start_sp = None
        self._sp_1min_ago = None
        self._sp_1min_time = None
        self._sp_data["session_start"] = None
        if self.on_cards_reset:
            self.on_cards_reset()

        self._scan_thread = threading.Thread(
            target=self._scan_worker, args=(sp_min, sp_max), daemon=True)
        self._scan_thread.start()

    def _scan_worker(self, sp_min: float, sp_max: float):
        try:
            self._run_scan(sp_min, sp_max)
        except Exception as e:
            self._schedule(0, lambda: self.on_status(f"Fehler: {e}") if self.on_status else None)
        finally:
            self._schedule(0, self._scan_finished)

    def _scan_finished(self):
        self._scanning = False

    def _run_scan(self, sp_min: float, sp_max: float):
        import win32gui
        from bot.memory_reader import GameMemory

        self._schedule(0, lambda: self.on_status("Suche Spielfenster...") if self.on_status else None)
        hwnd = win32gui.FindWindow(None, self._game_title)
        if not hwnd:
            msg = f"[SP] Fenster '{self._game_title}' nicht gefunden!"
            self._log_fn(msg)
            self._schedule(0, lambda: self.on_status(msg) if self.on_status else None)
            return

        self._log_fn(f"[SP] Suche Adresse für SP-Bereich {format_sp(sp_min)} – {format_sp(sp_max)}...")
        self._memory = GameMemory(hwnd)

        if self._stop_flag.is_set():
            return

        # Scan 1
        self._schedule(0, lambda: self.on_status("Scan 1 läuft...") if self.on_status else None)
        hits1 = self._memory.scan_range(sp_min, sp_max)
        n1 = len(hits1)
        self._schedule(0, lambda: self.on_status(f"Scan 1: {n1} Treffer. Warte 10 s...") if self.on_status else None)

        if self._stop_flag.is_set():
            return

        for _ in range(100):
            if self._stop_flag.is_set():
                return
            time.sleep(0.1)

        if not hits1:
            self._schedule(0, lambda: self.on_status("Keine Treffer in Scan 1.") if self.on_status else None)
            return

        # Scan 2
        scan2_min = min(hits1.values()) * 0.995
        scan2_max = max(hits1.values()) * 1.05
        self._schedule(0, lambda: self.on_status("Scan 2 läuft...") if self.on_status else None)
        hits2 = self._memory.scan_range(scan2_min, scan2_max)
        n2 = len(hits2)
        self._schedule(0, lambda: self.on_status(f"Scan 2: {n2} Treffer. Filtere...") if self.on_status else None)

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
            self._schedule(0, lambda: self.on_status(msg) if self.on_status else None)
            return

        best = candidates[0]
        nc = len(candidates)
        self._log_fn(f"[SP] Adresse gefunden: 0x{best[0]:016X} "
                     f"({nc} Kandidat(en), verwende ersten)")

        # Initialisiere Session
        now = time.time()
        self._session_start_time = now
        self._session_start_sp = best[2]
        self._sp_1min_ago = best[2]
        self._sp_1min_time = now

        self._candidates = [(best[0], best[2], best[2])]
        self._sp_data["value"] = best[2]
        self._sp_data["session_start"] = best[2]

        def init_cards():
            if self.on_cards_init:
                self.on_cards_init(format_sp(best[2]))
            if self.on_status:
                self.on_status("")

        self._schedule(0, init_cards)

        self._live_updating = True
        self._live_update_loop()

    # ── Live update ──────────────────────────────────────────

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

        farmed = max(0.0, v_now - self._session_start_sp) if self._session_start_sp else 0.0
        elapsed = now - self._session_start_time if self._session_start_time else 0.0

        if self._sp_1min_time and self._sp_1min_ago is not None:
            window = now - self._sp_1min_time
            if window >= 60:
                rate_per_min = (v_now - self._sp_1min_ago) / (window / 60)
                self._sp_1min_ago = v_now
                self._sp_1min_time = now
            elif elapsed > 0:
                rate_per_min = farmed / (elapsed / 60) if elapsed >= 1 else 0.0
            else:
                rate_per_min = 0.0
        else:
            rate_per_min = 0.0

        rate_per_hour = rate_per_min * 60

        if self.on_cards_update:
            self.on_cards_update(
                format_sp(v_now),
                format_sp(farmed) if farmed >= 1 else "0",
                _fmt_duration(elapsed),
                format_sp(rate_per_min) if rate_per_min >= 1 else "0",
                format_sp(rate_per_hour) if rate_per_hour >= 1 else "0",
            )

        self._schedule(1000, self._live_update_loop)

    def reset_session(self, current_sp):
        """Reset session tracking data (called from tab's reset_stats)."""
        now = time.time()
        self._session_start_time = now
        self._session_start_sp = current_sp
        self._sp_data["session_start"] = current_sp
        self._sp_1min_ago = current_sp
        self._sp_1min_time = now

    def stop(self):
        """Cleanup when UI closes."""
        self._stop_flag.set()
        self._live_updating = False
        self._sp_data["value"] = None
        self._sp_data["session_start"] = None
        if self._memory:
            self._memory.close()
            self._memory = None
