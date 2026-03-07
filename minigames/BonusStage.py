import cv2
import numpy as np
import time
import mss
import ctypes
import win32gui
import pyautogui
import os

from TemplateMatcher import TemplateMatcher
from Config import BonusStageConfig

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


class BonusStage(TemplateMatcher):
    def __init__(self, config: BonusStageConfig, game_window, monitor_index: int = 2):
        self.config      = config
        self.game_window = game_window
        self._active     = False
        self._last_jump  = 0.0

        self.template_left  = self._load_template(config.template_swipe_left,   ASSETS_DIR)
        self.template_right = self._load_template(config.template_swipe_right,  ASSETS_DIR)
        self.close_template = self._load_template(config.close_button_template, ASSETS_DIR)

        with mss.mss() as sct:
            monitor = sct.monitors[monitor_index]
            self._offset_x    = monitor["left"]
            self._offset_y    = monitor["top"]
            self._monitor_idx = monitor_index

        print(f"BonusStage bereit | Conf: {config.confidence} | "
              f"Jump alle {config.jump_interval}s | Links+Rechts Swipe aktiv")

    def _grab_gray(self, sct) -> np.ndarray:
        monitor    = sct.monitors[self._monitor_idx]
        screenshot = sct.grab(monitor)
        frame      = np.array(screenshot)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

    def _force_focus(self):
        hwnd       = self.game_window.hwnd
        fg_thread  = ctypes.windll.user32.GetWindowThreadProcessId(
            win32gui.GetForegroundWindow(), None)
        tgt_thread = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
        ctypes.windll.user32.AttachThreadInput(fg_thread, tgt_thread, True)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        ctypes.windll.user32.BringWindowToTop(hwnd)
        ctypes.windll.user32.AttachThreadInput(fg_thread, tgt_thread, False)
        time.sleep(0.2)

    def _click(self, abs_x: int, abs_y: int):
        previous = win32gui.GetForegroundWindow()
        self._force_focus()
        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
        time.sleep(0.1)
        pyautogui.click()
        time.sleep(0.1)
        if previous and previous != self.game_window.hwnd:
            ctypes.windll.user32.SetForegroundWindow(previous)

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

        previous = win32gui.GetForegroundWindow()
        self._force_focus()

        pyautogui.moveTo(start_x, abs_y, duration=0.1)
        time.sleep(0.15)
        pyautogui.mouseDown()
        time.sleep(0.05)
        pyautogui.moveTo(end_x, abs_y, duration=self.config.swipe_duration)
        time.sleep(0.05)
        pyautogui.mouseUp()
        time.sleep(0.1)

        if previous and previous != self.game_window.hwnd:
            ctypes.windll.user32.SetForegroundWindow(previous)

    def _check_close_button(self, sct) -> bool:
        gray  = self._grab_gray(sct)
        match = self._find_one(gray, self.close_template, self.config.close_button_confidence)
        if match:
            cx, cy, conf, tw, th = match
            abs_x = self._offset_x + cx
            abs_y = self._offset_y + cy
            print(f"  [!] Close-Button erkannt bei ({cx}, {cy}) | Conf: {conf:.2f} – Klicke...")
            self._click(abs_x, abs_y)
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
