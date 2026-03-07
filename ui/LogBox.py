import io
import queue
import time
import tkinter as tk
from tkinter import scrolledtext


class QueueStream(io.TextIOBase):
    """Leitet print()-Aufrufe in eine Queue um."""
    def __init__(self, log_queue: queue.Queue):
        self._queue = log_queue

    def write(self, text: str):
        if text and text.strip():
            self._queue.put(text)
        return len(text)

    def flush(self):
        pass


class LogBox:
    """ScrolledText-Widget mit farbigem Log und Timestamp."""

    def __init__(self, parent):
        outer = tk.Frame(parent, bg="#1e1e2e")
        outer.pack(fill="both", expand=True, padx=10, pady=(4, 0))

        tk.Label(outer, text="📋  Log", bg="#1e1e2e", fg="#89b4fa",
                 font=("Consolas", 10, "bold"), anchor="w"
                 ).pack(fill="x")

        self._box = scrolledtext.ScrolledText(
            outer, height=10, width=78,
            bg="#11111b", fg="#cdd6f4",
            font=("Consolas", 9),
            state="disabled", relief="flat", bd=0,
            insertbackground="#cdd6f4"
        )
        self._box.pack(fill="both", expand=True)

        self._box.tag_config("info",  foreground="#cdd6f4")
        self._box.tag_config("good",  foreground="#a6e3a1")
        self._box.tag_config("warn",  foreground="#fab387")
        self._box.tag_config("error", foreground="#f38ba8")
        self._box.tag_config("jump",  foreground="#89b4fa")
        self._box.tag_config("ts",    foreground="#45475a")

    def log(self, text: str):
        self._box.configure(state="normal")
        tl  = text.lower()
        tag = "info"
        if any(k in tl for k in ["gestartet", "abgeschlossen", "swipe", "bereit", "läuft", "✅"]):
            tag = "good"
        elif any(k in tl for k in ["panic", "close", "mimik", "verlassen", "pause", "⏸", "⚠"]):
            tag = "warn"
        elif any(k in tl for k in ["error", "fehler", "nicht gefunden"]):
            tag = "error"
        elif any(k in tl for k in ["sprung", "springe", "jump", "d gedrückt"]):
            tag = "jump"

        ts = time.strftime("%H:%M:%S")
        self._box.insert("end", f"[{ts}] ", "ts")
        self._box.insert("end", f"{text}\n", tag)
        self._box.see("end")
        self._box.configure(state="disabled")
