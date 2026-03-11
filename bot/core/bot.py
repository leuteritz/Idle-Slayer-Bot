import time
import cv2
import numpy as np
import mss
import threading
import pyautogui

from bot.window.manager import WindowManager
from bot.window.input import InputController
from bot.core.key_handler import KeyHandler
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

        manager     = WindowManager(bot_config.game_title)
        self.window = InputController(manager)
        self._key_data    = key_data if key_data is not None else {}
        self._key_handler = KeyHandler(bot_config, self.window)

        # Monitor-Offset einmal zentral auflösen
        with mss.mss() as sct:
            mon = sct.monitors[bot_config.monitor_index]
            monitor_info = (mon["left"], mon["top"], bot_config.monitor_index)

        self.chest_hunt  = ChestHunt(chest_config, self.window, monitor_info,
                                     key_data=self._key_data) \
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

    def run(self, stop_event: threading.Event = None,
                  pause_event: threading.Event = None,
                  crash_queue=None):
        self.window.focus()

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
                            self._key_handler.last_d_key = time.time()
                            last_scan = now
                            continue

                        if self.chest_hunt and self.chest_hunt.run(gray, pause_event=pause_event, stop_event=stop_event):
                            self._key_handler.last_d_key = time.time()
                            last_scan = now
                            continue

                        last_scan = now

                    self._key_handler.handle_d(now, self._key_data)
                    self._key_handler.handle_r(now, self._key_data)

                    if self.cfg.w_mode == 1:
                        self._key_handler.handle_w_mode1(now, self._key_data)
                    else:
                        self._key_handler.handle_w_mode2(self._key_data)

            except pyautogui.FailSafeException as e:
                msg = "PyAutoGUI FailSafe ausgelöst – Maus in Bildschirmecke. Bot gestoppt."
                print(msg)
                if crash_queue is not None:
                    crash_queue.put(("FAILSAFE", str(e)))
            except KeyboardInterrupt:
                print("Skript beendet.")
