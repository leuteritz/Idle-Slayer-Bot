import time
import pyautogui
import win32gui
import ctypes


class GameWindow:
    def __init__(self, title: str):
        self.hwnd = win32gui.FindWindow(None, title)
        if self.hwnd == 0:
            raise RuntimeError(f"Fenster '{title}' nicht gefunden!")
        self._previous_hwnd = None
        print(f"Spielfenster gefunden: HWND={self.hwnd}")

    def send_key(self, key: str, hold_time: float = 0.05):
        self._focus()
        pyautogui.keyDown(key)
        time.sleep(hold_time)
        pyautogui.keyUp(key)
        self._unfocus()

    def rapid_key(self, key: str):
        """Schneller Tastendruck ohne Fokus-Wechsel. Fenster muss bereits fokussiert sein."""
        pyautogui.press(key, _pause=False)

    def rapid_hold(self, key: str, hold_time: float):
        """Taste gedrückt halten ohne Fokus-Wechsel. Fenster muss bereits fokussiert sein."""
        pyautogui.keyDown(key)
        time.sleep(hold_time)
        pyautogui.keyUp(key)

    def click(self, abs_x: int, abs_y: int):
        self._focus()
        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
        pyautogui.click()
        self._unfocus()

    def force_click(self, abs_x: int, abs_y: int):
        self._force_focus()
        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
        time.sleep(0.1)
        pyautogui.click()
        time.sleep(0.1)
        self._unfocus()

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int,
             duration: float = 0.4):
        self._force_focus()
        pyautogui.moveTo(start_x, start_y, duration=0.1)
        time.sleep(0.15)
        pyautogui.mouseDown()
        time.sleep(0.05)
        pyautogui.moveTo(end_x, start_y, duration=duration)
        time.sleep(0.05)
        pyautogui.mouseUp()
        time.sleep(0.1)
        self._unfocus()

    def _focus(self):
        self._previous_hwnd = win32gui.GetForegroundWindow()
        ctypes.windll.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)

    def _force_focus(self):
        self._previous_hwnd = win32gui.GetForegroundWindow()
        fg_thread = ctypes.windll.user32.GetWindowThreadProcessId(
            win32gui.GetForegroundWindow(), None)
        tgt_thread = ctypes.windll.user32.GetWindowThreadProcessId(
            self.hwnd, None)
        ctypes.windll.user32.AttachThreadInput(fg_thread, tgt_thread, True)
        ctypes.windll.user32.SetForegroundWindow(self.hwnd)
        ctypes.windll.user32.BringWindowToTop(self.hwnd)
        ctypes.windll.user32.AttachThreadInput(fg_thread, tgt_thread, False)
        time.sleep(0.2)

    def _unfocus(self):
        time.sleep(0.05)
        if self._previous_hwnd and self._previous_hwnd != self.hwnd:
            ctypes.windll.user32.SetForegroundWindow(self._previous_hwnd)
