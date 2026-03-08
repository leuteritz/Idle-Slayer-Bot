import cv2
import numpy as np
import time
import mss
import os
import threading

from bot.template_matcher import TemplateMatcher
from bot.config import ChestHuntConfig

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS_DIR    = os.path.join(_PROJECT_ROOT, "assets", "minigames")


class ChestHunt(TemplateMatcher):
    def __init__(self, config: ChestHuntConfig, game_window, monitor_index: int = 2):
        self.config      = config
        self.game_window = game_window
        self._active     = False

        self.template       = self._load_template(config.template,              ASSETS_DIR)
        self.panic_template = self._load_template(config.panic_button_template, ASSETS_DIR)

        with mss.mss() as sct:
            monitor = sct.monitors[monitor_index]
            self._offset_x    = monitor["left"]
            self._offset_y    = monitor["top"]
            self._monitor_idx = monitor_index

        print(f"ChestHunt bereit | Conf: {config.confidence} | Panic-Conf: {config.panic_button_confidence}")

    def _grab_gray(self, sct) -> np.ndarray:
        monitor    = sct.monitors[self._monitor_idx]
        screenshot = sct.grab(monitor)
        frame      = np.array(screenshot)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

    def _click_on_monitor(self, x: int, y: int):
        self.game_window.click(self._offset_x + x, self._offset_y + y)

    def _handle_panic(self, sct) -> bool:
        gray  = self._grab_gray(sct)
        match = self._find_one(gray, self.panic_template, self.config.panic_button_confidence)
        if match:
            cx, cy, conf, tw, th = match
            print(f"  [!] Panic-Button bei ({cx}, {cy}) | Conf: {conf:.2f} – Drücke Knopf!")
            self._click_on_monitor(cx, cy)
            time.sleep(1.0)
            self._active = False
            return True
        return False

    def run(self, gray_frame: np.ndarray,
            pause_event: threading.Event = None,
            stop_event: threading.Event = None) -> bool:
        chests   = self._find_all(gray_frame, self.template, self.config.confidence)
        expected = self.config.rows * self.config.cols

        if len(chests) < expected // 2:
            if self._active:
                print("[ChestHunt] Minigame verlassen – zurück zum normalen Spiel.\n")
                self._active = False
                return True
            return False

        if not self._active:
            print(f"[ChestHunt] Gestartet! {len(chests)}/{expected} Kisten – öffne alle...")
            self._active = True

        chests_sorted = sorted(chests, key=lambda c: (c[1], c[0]))

        with mss.mss() as sct:
            for i, (cx, cy) in enumerate(chests_sorted):
                if stop_event and stop_event.is_set():
                    return True
                while pause_event and pause_event.is_set():
                    time.sleep(0.2)

                if self._handle_panic(sct):
                    print("  Mimik zugeschlagen – verlassen.\n")
                    return True

                print(f"  Kiste {i+1}/{len(chests_sorted)} bei ({cx}, {cy}) – klicke...")
                self._click_on_monitor(cx, cy)

                waited = 0.0
                while waited < self.config.wait_per_chest:
                    if stop_event and stop_event.is_set():
                        return True
                    while pause_event and pause_event.is_set():
                        time.sleep(0.2)
                    time.sleep(0.5)
                    waited += 0.5
                    if self._handle_panic(sct):
                        print("  Mimik zugeschlagen – verlassen.\n")
                        return True

        print("[ChestHunt] Abgeschlossen!\n")
        self._active = False
        return True
