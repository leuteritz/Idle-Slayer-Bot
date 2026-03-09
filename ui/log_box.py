import io
import queue
import time
import tkinter as tk
from tkinter import scrolledtext, ttk

from ui.theme import (BASE, MANTLE, CRUST, SURF0, TEXT, DIM,
                      BLUE, GREEN, ORANGE, RED,
                      FONT_UI, FONT_BOLD, FONT_MONO, lighten)


class QueueStream(io.TextIOBase):
    def __init__(self, log_queue: queue.Queue):
        self._queue = log_queue

    def write(self, text: str):
        if text and text.strip():
            self._queue.put(text)
        return len(text)

    def flush(self):
        pass


class LogBox:
    def __init__(self, parent):
        outer = tk.Frame(parent, bg=BASE)
        outer.pack(fill="both", expand=True, padx=0, pady=0)

        # Header bar
        hdr = tk.Frame(outer, bg=MANTLE, padx=16, pady=7)
        hdr.pack(fill="x")

        tk.Label(hdr, text="📋  Log", bg=MANTLE, fg=BLUE,
                 font=FONT_BOLD).pack(side="left")

        clr_btn = tk.Button(
            hdr, text="Leeren",
            command=self._clear,
            bg=SURF0, fg=TEXT,
            font=("Segoe UI", 8), relief="flat",
            padx=10, pady=3, cursor="hand2",
            activebackground=lighten(SURF0), activeforeground=TEXT, bd=0)
        clr_btn.pack(side="right")
        clr_btn.bind("<Enter>", lambda e: clr_btn.config(bg=lighten(SURF0)))
        clr_btn.bind("<Leave>", lambda e: clr_btn.config(bg=SURF0))

        # Log text
        self._box = scrolledtext.ScrolledText(
            outer, height=9,
            bg=CRUST, fg=TEXT,
            font=FONT_MONO,
            state="disabled", relief="flat", bd=0,
            insertbackground=TEXT,
            selectbackground=SURF0, selectforeground=TEXT,
            padx=14, pady=8,
        )
        self._box.pack(fill="both", expand=True)

        self._box.tag_config("info",  foreground=TEXT)
        self._box.tag_config("good",  foreground=GREEN)
        self._box.tag_config("warn",  foreground=ORANGE)
        self._box.tag_config("error", foreground=RED)
        self._box.tag_config("jump",  foreground=BLUE)
        self._box.tag_config("ts",    foreground=DIM)

    def log(self, text: str):
        self._box.configure(state="normal")
        tl  = text.lower()
        tag = "info"
        if any(k in tl for k in ["gestartet", "abgeschlossen", "swipe", "bereit", "läuft", "✅"]):
            tag = "good"
        elif any(k in tl for k in ["panic", "close", "mimik", "verlassen", "pause", "⏸", "⚠"]):
            tag = "warn"
        elif any(k in tl for k in ["error", "fehler", "nicht gefunden", "❌"]):
            tag = "error"
        elif any(k in tl for k in ["sprung", "springe", "jump", "d gedrückt"]):
            tag = "jump"

        ts = time.strftime("%H:%M:%S")
        self._box.insert("end", f"[{ts}] ", "ts")
        self._box.insert("end", f"{text}\n", tag)
        self._box.see("end")
        self._box.configure(state="disabled")

    def _clear(self):
        self._box.configure(state="normal")
        self._box.delete("1.0", "end")
        self._box.configure(state="disabled")
