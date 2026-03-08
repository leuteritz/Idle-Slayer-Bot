import time
import cv2
import numpy as np
import mss
import threading
import pyautogui

from bot.game_window import GameWindow
from bot.target import Target
from bot.minigames.chest_hunt import ChestHunt
from bot.minigames.bonus_stage import BonusStage
from bot.config import BotConfig, ChestHuntConfig, BonusStageConfig, TargetConfig


class IdleSlayerBot:
    def __init__(self, bot_config: BotConfig,
                 target_configs: list,
                 chest_config: ChestHuntConfig,
                 bonus_config: BonusStageConfig):

        self.cfg        = bot_config
        if bot_config.disable_failsafe:
            pyautogui.FAILSAFE = False
        self.window     = GameWindow(bot_config.game_title)
        self.last_d_key = 0
        self.last_r_key = 0

        self.targets = sorted(
            [Target(t.filename, t.priority, bot_config.confidence_threshold)
             for t in target_configs],
            key=lambda t: t.priority
        )

        self.chest_hunt  = ChestHunt(chest_config, self.window, bot_config.monitor_index) \
                           if chest_config.enabled else None

        self.bonus_stage = BonusStage(bonus_config, self.window, bot_config.monitor_index) \
                           if bonus_config.enabled else None

        self._print_startup()

    def _print_startup(self):
        print(f"{len(self.targets)} Template(s) geladen (nach Priorität):")
        for t in self.targets:
            print(f"  [{t.priority}] {t.name} | Confidence: {t.confidence}")
        print(f"Jump-Taste: '{self.cfg.jump_key}' | Hold: {self.cfg.space_key_interval}s")
        print(f"Check-Intervall: {self.cfg.check_interval}s")
        print(f"Chest Hunt:  {'aktiviert' if self.chest_hunt  else 'deaktiviert'}")
        print(f"Bonus Stage: {'aktiviert' if self.bonus_stage else 'deaktiviert'}")
        print("Läuft... Drücke Ctrl+C oder klicke Beenden zum Stoppen.\n")

    def _handle_d_key(self, now: float):
        if now - self.last_d_key >= self.cfg.d_key_interval:
            print("D gedrückt (Timer)")
            self.window.send_key('d')
            self.last_d_key = now

    def _handle_r_key(self, now: float):
        if now - self.last_r_key >= self.cfg.r_key_interval:
            print("R gedrückt (Timer)")
            self.window.send_key('r')
            self.last_r_key = now

    def _handle_detection(self, gray_frame: np.ndarray):
        for target in self.targets:
            match = target.find(gray_frame)
            if match:
                cx, cy, conf = match
                print(f"[Prio {target.priority}] [{target.name}] bei ({cx}, {cy}) | Conf: {conf:.2f} – Springe!")
                self.window.send_key(self.cfg.jump_key, hold_time=self.cfg.space_key_interval)
                time.sleep(self.cfg.space_key_pause)
                self.window.send_key(self.cfg.jump_key, hold_time=self.cfg.space_key_interval_fast)
                break

    def run(self, stop_event: threading.Event = None,
                  pause_event: threading.Event = None,
                  crash_queue = None):
        with mss.mss() as sct:
            monitor = sct.monitors[self.cfg.monitor_index]
            try:
                while True:
                    # ── Stop prüfen ──
                    if stop_event and stop_event.is_set():
                        print("Bot gestoppt.")
                        break

                    # ── Pause prüfen ──
                    if pause_event and pause_event.is_set():
                        time.sleep(0.2)
                        continue

                    now        = time.time()
                    screenshot = sct.grab(monitor)
                    frame      = np.array(screenshot)
                    gray       = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                    if self.bonus_stage and self.bonus_stage.run(gray):
                        self.last_d_key = time.time()
                        continue

                    if self.chest_hunt and self.chest_hunt.run(gray, pause_event=pause_event, stop_event=stop_event):
                        self.last_d_key = time.time()
                        continue

                    self._handle_d_key(now)
                    self._handle_r_key(now)
                    self._handle_detection(gray)
                    time.sleep(self.cfg.check_interval)

            except pyautogui.FailSafeException as e:
                msg = f"PyAutoGUI FailSafe ausgelöst – Maus in Bildschirmecke. Bot gestoppt."
                print(msg)
                if crash_queue is not None:
                    crash_queue.put(("FAILSAFE", str(e)))
            except KeyboardInterrupt:
                print("Skript beendet.")
