import numpy as np
import time
import mss

from bot.template_matcher import TemplateMatcher, MINIGAMES_DIR
from bot.config import BonusStageConfig


class BonusStage(TemplateMatcher):
    def __init__(self, config: BonusStageConfig, game_window,
                 monitor_info: tuple):
        self.config      = config
        self.game_window = game_window
        self._active     = False
        self._last_jump  = 0.0

        self.template_left  = self._load_template(config.template_swipe_left,   MINIGAMES_DIR)
        self.template_right = self._load_template(config.template_swipe_right,  MINIGAMES_DIR)
        self.close_template = self._load_template(config.close_button_template, MINIGAMES_DIR)

        self._offset_x, self._offset_y, self._monitor_idx = monitor_info

        print(f"BonusStage bereit | Conf: {config.confidence} | "
              f"Jump alle {config.jump_interval}s | Links+Rechts Swipe aktiv")

    def _swipe(self, cx: int, cy: int, tw: int, direction: str):
        half_w = tw // 2
        abs_y  = self._offset_y + cy

        if direction == "left":
            start_x = self._offset_x + cx + half_w
            end_x   = self._offset_x + cx - self.config.swipe_distance
        else:
            start_x = self._offset_x + cx - half_w
            end_x   = self._offset_x + cx + self.config.swipe_distance

        arrow = "←" if direction == "left" else "→"
        print(f"  Swipe {arrow} | Start: ({start_x}, {abs_y}) → Ende: ({end_x}, {abs_y})")

        self.game_window.drag(start_x, abs_y, end_x, abs_y,
                              duration=self.config.swipe_duration)

    def _check_close_button(self, sct) -> bool:
        gray  = self.grab_gray(sct, self._monitor_idx)
        match = self._find_one(gray, self.close_template, self.config.close_button_confidence)
        if match:
            cx, cy, conf, tw, th = match
            abs_x = self._offset_x + cx
            abs_y = self._offset_y + cy
            print(f"  [!] Close-Button erkannt bei ({cx}, {cy}) | Conf: {conf:.2f} – Klicke...")
            self.game_window.force_click(abs_x, abs_y)
            time.sleep(1.0)
            self._active    = False
            self._last_jump = 0.0
            return True
        return False

    def _handle_jump(self, now: float):
        if now - self._last_jump >= self.config.jump_interval:
            print(f"  [BonusStage] Sprung! (alle {self.config.jump_interval}s)")
            self.game_window.send_key(self.config.jump_key, hold_time=self.config.jump_hold_time)
            self._last_jump = now

    def _detect_swipe(self, gray_frame: np.ndarray):
        match_left  = self._find_one(gray_frame, self.template_left,  self.config.confidence)
        match_right = self._find_one(gray_frame, self.template_right, self.config.confidence)

        if match_left and match_right:
            if match_left[2] >= match_right[2]:
                cx, cy, conf, tw, th = match_left
                return cx, cy, conf, tw, "left"
            else:
                cx, cy, conf, tw, th = match_right
                return cx, cy, conf, tw, "right"
        if match_left:
            cx, cy, conf, tw, th = match_left
            return cx, cy, conf, tw, "left"
        if match_right:
            cx, cy, conf, tw, th = match_right
            return cx, cy, conf, tw, "right"
        return None

    def run(self, gray_frame: np.ndarray) -> bool:
        now = time.time()

        if self._active:
            with mss.mss() as sct:
                if self._check_close_button(sct):
                    print("[BonusStage] Geschlossen – warte auf nächsten Swipe-Button.\n")
                    return True
            self._handle_jump(now)
            return True

        match = self._detect_swipe(gray_frame)
        if not match:
            return False

        cx, cy, conf, tw, direction = match
        arrow = "←" if direction == "left" else "→"
        print(f"[BonusStage] Erkannt bei ({cx}, {cy}) | Conf: {conf:.2f} | Swipe {arrow}")
        self._active    = True
        self._last_jump = now
        self._swipe(cx, cy, tw, direction)
        print(f"[BonusStage] Swipe {arrow} abgeschlossen – Minispiel läuft.\n")
        time.sleep(1.0)
        return True
