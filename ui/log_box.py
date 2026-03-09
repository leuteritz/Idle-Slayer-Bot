import io
import queue
import time
import tkinter as tk
from tkinter import scrolledtext, ttk

from ui.theme import (BASE, MANTLE, CRUST, SURF0, TEXT, DIM,
                      BLUE, GREEN, ORANGE, RED, SEPARATOR, TINT_DIM,
                      FONT_UI, FONT_BOLD, FONT_SMALL, FONT_MONO, lighten)

# Vivid log colors (slightly brighter than the HIG system colors for readability)
_LOG_GREEN  = "#32D74B"
_LOG_ORANGE = "#FFB340"
_LOG_RED    = "#FF6961"
_LOG_BLUE   = "#64D2FF"   # systemTeal-ish, pops against dark bg
_LOG_TS     = "#8E8E93"   # secondaryLabel — readable timestamp


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
        hdr = tk.Frame(outer, bg=MANTLE, padx=20, pady=8)
        hdr.pack(fill="x")

        tk.Label(hdr, text="📋  Log", bg=MANTLE, fg=BLUE,
                 font=FONT_BOLD).pack(side="left")

        clr_btn = tk.Button(
            hdr, text="Leeren",
            command=self._clear,
            bg=SURF0, fg=DIM,
            font=FONT_SMALL, relief="flat",
            padx=12, pady=4, cursor="hand2",
            activebackground=lighten(SURF0), activeforeground=TEXT, bd=0)
        clr_btn.pack(side="right")
        clr_btn.bind("<Enter>", lambda e: clr_btn.config(bg=lighten(SURF0), fg=TEXT))
        clr_btn.bind("<Leave>", lambda e: clr_btn.config(bg=SURF0, fg=DIM))

        # Log text — darker background for contrast
        self._box = scrolledtext.ScrolledText(
            outer, height=9,
            bg="#0A0A0A", fg="#E5E5EA",
            font=FONT_MONO,
            state="disabled", relief="flat", bd=0,
            insertbackground=TEXT,
            selectbackground=SURF0, selectforeground=TEXT,
            padx=16, pady=10,
        )
        self._box.pack(fill="both", expand=True)

        # Bright, vivid tag colors for maximum readability
        self._box.tag_config("info",  foreground="#E5E5EA")
        self._box.tag_config("good",  foreground=_LOG_GREEN)
        self._box.tag_config("warn",  foreground=_LOG_ORANGE)
        self._box.tag_config("error", foreground=_LOG_RED)
        self._box.tag_config("jump",  foreground=_LOG_BLUE)
        self._box.tag_config("ts",    foreground=_LOG_TS)

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
