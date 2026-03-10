import time
import cv2
import numpy as np
import mss
import threading
import pyautogui

from bot.game_window import GameWindow
from bot.minigames.chest_hunt import ChestHunt
from bot.minigames.bonus_stage import BonusStage
from bot.config import BotConfig, ChestHuntConfig, BonusStageConfig


class IdleSlayerBot:
    def __init__(self, bot_config: BotConfig,
                 chest_config: ChestHuntConfig,
                 bonus_config: BonusStageConfig,
                 key_data: dict = None):

        self.cfg = bot_config
        if bot_config.disable_failsafe:
            pyautogui.FAILSAFE = False
        self.window      = GameWindow(bot_config.game_title)
        self.last_d_key  = 0
        self.last_r_key  = 0
        self.last_w_key  = 0
        self._w_count    = 0
        self._w_log_time = 0
        self._key_data   = key_data if key_data is not None else {}

        # Monitor-Offset einmal zentral auflösen
        with mss.mss() as sct:
            mon = sct.monitors[bot_config.monitor_index]
            monitor_info = (mon["left"], mon["top"], bot_config.monitor_index)

        self.chest_hunt  = ChestHunt(chest_config, self.window, monitor_info) \
                           if chest_config.enabled else None

        self.bonus_stage = BonusStage(bonus_config, self.window, monitor_info) \
                           if bonus_config.enabled else None

        self._print_startup()

    def _print_startup(self):
        mode_name = "CPS-Spam" if self.cfg.w_mode == 1 else "Lang + Kurz"
        print(f"W-Modus: {self.cfg.w_mode} ({mode_name})")
        if self.cfg.w_mode == 1:
            print(f"  CPS: {self.cfg.w_key_cps}")
        else:
            print(f"  Lang: {self.cfg.w_hold_time}s, danach {self.cfg.w_short_count}× kurz")
        print(f"D-Taste: alle {self.cfg.d_key_interval}s")
        print(f"R-Taste: alle {self.cfg.r_key_interval}s")
        print(f"Chest Hunt:  {'aktiviert' if self.chest_hunt  else 'deaktiviert'}")
        print(f"Bonus Stage: {'aktiviert' if self.bonus_stage else 'deaktiviert'}")
        print("Läuft... Drücke Ctrl+C oder klicke Beenden zum Stoppen.\n")

    def _handle_d_key(self, now: float):
        if now - self.last_d_key >= self.cfg.d_key_interval:
            print("D gedrückt (Timer)")
            self.window.send_key('d')
            self.last_d_key = now
            self._key_data["d"] = self._key_data.get("d", 0) + 1

    def _handle_r_key(self, now: float):
        if now - self.last_r_key >= self.cfg.r_key_interval:
            print("R gedrückt (Timer)")
            self.window.send_key('r')
            self.last_r_key = now
            self._key_data["r"] = self._key_data.get("r", 0) + 1

    # ── Modus 1: CPS-Spam ────────────────────────────────────

    def _handle_w_mode1(self, now: float):
        interval = 1.0 / max(1.0, self.cfg.w_key_cps)
        if now - self.last_w_key >= interval:
            self.window.rapid_key('w')
            self.last_w_key = now
            self._w_count += 1
            self._key_data["w"] = self._key_data.get("w", 0) + 1

        if now - self._w_log_time >= 1.0:
            if self._w_count > 0:
                print(f"W × {self._w_count}")
                self._w_count = 0
            self._w_log_time = now

    # ── Modus 2: 1× Lang + N× Kurz ──────────────────────────

    def _handle_w_mode2(self):
        self.window._focus()

        # 1× lang drücken
        self.window.rapid_hold('w', self.cfg.w_hold_time)
        print(f"W gehalten ({self.cfg.w_hold_time}s)")

        # N× kurz drücken, sofort hintereinander
        for i in range(self.cfg.w_short_count):
            self.window.rapid_key('w')
        print(f"W × {self.cfg.w_short_count} (kurz)")

        self._key_data["w"] = self._key_data.get("w", 0) + 1 + self.cfg.w_short_count
        self.window._unfocus()

    # ── Main Loop ────────────────────────────────────────────

    def run(self, stop_event: threading.Event = None,
                  pause_event: threading.Event = None,
                  crash_queue = None):
        self.window._focus()

        with mss.mss() as sct:
            monitor = sct.monitors[self.cfg.monitor_index]
            last_scan = 0
            scan_interval = 0.2

            try:
                while True:
                    if stop_event and stop_event.is_set():
                        print("Bot gestoppt.")
                        break

                    if pause_event and pause_event.is_set():
                        time.sleep(0.2)
                        continue

                    now = time.time()

                    # Minigame-Erkennung alle 200ms
                    if now - last_scan >= scan_interval:
                        screenshot = sct.grab(monitor)
                        frame      = np.array(screenshot)
                        gray       = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                        if self.bonus_stage and self.bonus_stage.run(gray):
                            self.last_d_key = time.time()
                            last_scan = now
                            continue

                        if self.chest_hunt and self.chest_hunt.run(gray, pause_event=pause_event, stop_event=stop_event):
                            self.last_d_key = time.time()
                            last_scan = now
                            continue

                        last_scan = now

                    self._handle_d_key(now)
                    self._handle_r_key(now)

                    if self.cfg.w_mode == 1:
                        self._handle_w_mode1(now)
                    else:
                        self._handle_w_mode2()

            except pyautogui.FailSafeException as e:
                msg = "PyAutoGUI FailSafe ausgelöst – Maus in Bildschirmecke. Bot gestoppt."
                print(msg)
                if crash_queue is not None:
                    crash_queue.put(("FAILSAFE", str(e)))
            except KeyboardInterrupt:
                print("Skript beendet.")
