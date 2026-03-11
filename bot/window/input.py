import time
import pyautogui

from bot.window.manager import WindowManager


class InputController:
    def __init__(self, manager: WindowManager):
        self._manager = manager

    @property
    def hwnd(self):
        return self._manager.hwnd

    def focus(self):
        self._manager.focus()

    def unfocus(self):
        self._manager.unfocus()

    def send_key(self, key: str, hold_time: float = 0.05):
        self._manager.focus()
        pyautogui.keyDown(key)
        time.sleep(hold_time)
        pyautogui.keyUp(key)
        self._manager.unfocus()

    def rapid_key(self, key: str):
        """Schneller Tastendruck ohne Fokus-Wechsel. Fenster muss bereits fokussiert sein."""
        pyautogui.press(key, _pause=False)

    def rapid_hold(self, key: str, hold_time: float):
        """Taste gedrückt halten ohne Fokus-Wechsel. Fenster muss bereits fokussiert sein."""
        pyautogui.keyDown(key)
        time.sleep(hold_time)
        pyautogui.keyUp(key)

    def click(self, abs_x: int, abs_y: int):
        self._manager.focus()
        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
        pyautogui.click()
        self._manager.unfocus()

    def force_click(self, abs_x: int, abs_y: int):
        self._manager.force_focus()
        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
        time.sleep(0.1)
        pyautogui.click()
        time.sleep(0.1)
        self._manager.unfocus()

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int,
             duration: float = 0.4):
        self._manager.force_focus()
        pyautogui.moveTo(start_x, start_y, duration=0.1)
        time.sleep(0.15)
        pyautogui.mouseDown()
        time.sleep(0.05)
        pyautogui.moveTo(end_x, start_y, duration=duration)
        time.sleep(0.05)
        pyautogui.mouseUp()
        time.sleep(0.1)
        self._manager.unfocus()
