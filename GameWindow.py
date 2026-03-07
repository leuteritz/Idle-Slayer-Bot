import time
import pyautogui
import win32gui
import ctypes


class GameWindow:
    def __init__(self, title: str):
        self.hwnd = win32gui.FindWindow(None, title)
        if self.hwnd == 0:
            raise RuntimeError(f"Fenster '{title}' nicht gefunden!")
        print(f"Spielfenster gefunden: HWND={self.hwnd}")

    def send_key(self, key: str, hold_time: float = 0.05):
        self._focus()
        pyautogui.keyDown(key)
        time.sleep(hold_time)
        pyautogui.keyUp(key)
        self._unfocus()

    def click(self, abs_x: int, abs_y: int):
        self._focus()
        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
        pyautogui.click()
        self._unfocus()

    def _focus(self):
        self._previous_hwnd = win32gui.GetForegroundWindow()
        ctypes.windll.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)

    def _unfocus(self):
        time.sleep(0.05)
        if self._previous_hwnd and self._previous_hwnd != self.hwnd:
            ctypes.windll.user32.SetForegroundWindow(self._previous_hwnd)
