import time

from bot.memory.reader import MemoryReader
from bot.memory.format import format_sp


class SpScanner:
    def __init__(self, reader: MemoryReader):
        self._reader = reader

    def auto_find(self, initial_value: float, stop_event=None,
                  log_fn=print, max_rounds: int = 5, wait: float = 5.0):
        tol = max(100.0, initial_value * 0.002)
        log_fn(f"[ISP] Scanne nach Wert ~{format_sp(initial_value)} (±{tol:.0f})...")

        candidates = self._reader.scan_double(initial_value, tolerance=tol)
        log_fn(f"[ISP] {len(candidates)} Kandidaten gefunden")

        if not candidates:
            log_fn("[ISP] Keine Treffer – ISP-Tracking deaktiviert.")
            return None
        if len(candidates) == 1:
            log_fn(f"[ISP] Adresse gefunden: {candidates[0]:#x}")
            return candidates[0]

        prev = initial_value
        for i in range(max_rounds):
            if stop_event and stop_event.is_set():
                return None
            log_fn(f"[ISP] Warte {wait:.0f}s auf Wertänderung... "
                   f"(Runde {i + 1}/{max_rounds})")
            time.sleep(wait)
            if stop_event and stop_event.is_set():
                return None
            candidates = self._reader.rescan_increased(candidates, prev)
            log_fn(f"[ISP] {len(candidates)} Kandidaten übrig")
            if not candidates:
                log_fn("[ISP] Alle Kandidaten verloren – ISP-Tracking fehlgeschlagen.")
                return None
            if len(candidates) <= 3:
                log_fn(f"[ISP] Adresse gefunden: {candidates[0]:#x}")
                return candidates[0]
            val = self._reader.read_double(candidates[0])
            if val is not None:
                prev = val

        if candidates:
            log_fn(f"[ISP] Beste Adresse: {candidates[0]:#x} "
                   f"({len(candidates)} Kandidaten übrig)")
            return candidates[0]
        return None
