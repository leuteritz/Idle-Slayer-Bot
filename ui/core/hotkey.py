import threading
import ctypes
from ctypes import wintypes
import win32con

_WM_HOTKEY = 0x0312
_PAUSE_KEY = win32con.VK_F9


class HotkeyThread(threading.Thread):
    """Globaler Win32-Hotkey-Listener (läuft als Daemon-Thread)."""

    def __init__(self, callback):
        super().__init__(daemon=True)
        self._callback = callback
        self._tid = None

    def run(self):
        self._tid = ctypes.windll.kernel32.GetCurrentThreadId()
        ctypes.windll.user32.RegisterHotKey(None, 1, win32con.MOD_NOREPEAT, _PAUSE_KEY)
        msg = wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == _WM_HOTKEY:
                self._callback()
        ctypes.windll.user32.UnregisterHotKey(None, 1)

    def stop(self):
        if self._tid:
            ctypes.windll.user32.PostThreadMessageW(self._tid, 0x0012, 0, 0)  # WM_QUIT
