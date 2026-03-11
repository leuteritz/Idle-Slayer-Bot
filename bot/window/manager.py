import time
import ctypes
import win32gui


class WindowManager:
    def __init__(self, title: str):
        self.hwnd = win32gui.FindWindow(None, title)
        if self.hwnd == 0:
            raise RuntimeError(f"Fenster '{title}' nicht gefunden!")
        self._previous_hwnd = None
        print(f"Spielfenster gefunden: HWND={self.hwnd}")

    def focus(self):
        self._previous_hwnd = win32gui.GetForegroundWindow()
        ctypes.windll.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)

    def force_focus(self):
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

    def unfocus(self):
        time.sleep(0.05)
        if self._previous_hwnd and self._previous_hwnd != self.hwnd:
            ctypes.windll.user32.SetForegroundWindow(self._previous_hwnd)
