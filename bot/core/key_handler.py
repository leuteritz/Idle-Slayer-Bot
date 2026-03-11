import time


class KeyHandler:
    def __init__(self, cfg, window):
        self.cfg         = cfg
        self.window      = window
        self.last_d_key  = 0
        self.last_r_key  = 0
        self.last_w_key  = 0
        self._w_count    = 0
        self._w_log_time = 0

    def handle_d(self, now: float, key_data: dict):
        if now - self.last_d_key >= self.cfg.d_key_interval:
            print("D gedrückt (Timer)")
            self.window.send_key('d')
            self.last_d_key = now
            key_data["d"] = key_data.get("d", 0) + 1

    def handle_r(self, now: float, key_data: dict):
        if now - self.last_r_key >= self.cfg.r_key_interval:
            print("R gedrückt (Timer)")
            self.window.send_key('r')
            self.last_r_key = now
            key_data["r"] = key_data.get("r", 0) + 1

    # ── Modus 1: CPS-Spam ────────────────────────────────────

    def handle_w_mode1(self, now: float, key_data: dict):
        interval = 1.0 / max(1.0, self.cfg.w_key_cps)
        if now - self.last_w_key >= interval:
            self.window.rapid_key('w')
            self.last_w_key = now
            self._w_count += 1
            key_data["w"] = key_data.get("w", 0) + 1

        if now - self._w_log_time >= 1.0:
            if self._w_count > 0:
                print(f"W × {self._w_count}")
                self._w_count = 0
            self._w_log_time = now

    # ── Modus 2: 1× Lang + N× Kurz ──────────────────────────

    def handle_w_mode2(self, key_data: dict):
        self.window.focus()

        # 1× lang drücken
        self.window.rapid_hold('w', self.cfg.w_hold_time)
        print(f"W gehalten ({self.cfg.w_hold_time}s)")

        # N× kurz drücken, sofort hintereinander
        for i in range(self.cfg.w_short_count):
            self.window.rapid_key('w')
        print(f"W × {self.cfg.w_short_count} (kurz)")

        key_data["w"] = key_data.get("w", 0) + 1 + self.cfg.w_short_count
        self.window.unfocus()
