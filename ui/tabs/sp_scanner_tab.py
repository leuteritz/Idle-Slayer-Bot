import tkinter as tk
from tkinter import ttk

from ui.theme import (BASE, MANTLE, SURF0, TEXT, DIM, BLUE, GREEN, RED, ORANGE,
                      YELLOW, MAUVE, SEPARATOR,
                      FONT_UI, FONT_BOLD, FONT_SMALL, FONT_LABEL, FONT_MED, FONT_BIG,
                      lighten, ScrollableFrame)
from ui.tabs.sp_scanner_logic import SpScannerLogic


class SpScannerTab:
    def __init__(self, parent, game_title: str = "Idle Slayer", sp_data: dict = None,
                 log_fn=None, key_data: dict = None, sp_var=None):
        self._parent = parent
        self._sp_data = sp_data if sp_data is not None else {}
        self._key_data = key_data if key_data is not None else {}
        self._log_fn = log_fn or (lambda msg: None)
        self._sp_var = sp_var if sp_var is not None else tk.StringVar(value="")

        self._status_var = tk.StringVar(value="")

        self._build_ui(parent)

        # Create logic and wire callbacks
        self._logic = SpScannerLogic(game_title, sp_data, log_fn, parent.after)
        self._logic.on_status = lambda text: self._status_var.set(text)
        self._logic.on_cards_init = self._init_cards
        self._logic.on_cards_update = self._update_cards
        self._logic.on_cards_reset = self._reset_cards

    # ── UI ───────────────────────────────────────────────────

    def _build_ui(self, parent):
        sf = ScrollableFrame(parent)
        self._inner = sf.inner

        # Status-Label
        tk.Label(self._inner, textvariable=self._status_var,
                 bg=BASE, fg=DIM, font=FONT_SMALL, anchor="w").pack(
            fill="x", padx=24, pady=(0, 0))

        # Stats-Frame
        stats = tk.Frame(self._inner, bg=BASE)
        stats.pack(fill="x", padx=24, pady=(6, 16))

        # Große SP-Karte (volle Breite)
        big_card = tk.Frame(stats, bg=MANTLE, padx=24, pady=18)
        big_card.pack(fill="x", pady=(0, 10))
        tk.Label(big_card, text="AKTUELLE SLAYER POINTS",
                 bg=MANTLE, fg=DIM, font=FONT_LABEL).pack(anchor="w")
        self._card_current = tk.StringVar(value="—")
        tk.Label(big_card, textvariable=self._card_current,
                 bg=MANTLE, fg=BLUE, font=FONT_BIG).pack(anchor="w", pady=(6, 0))

        # Zweite Reihe: Farmed + Session-Zeit
        row_a = tk.Frame(stats, bg=BASE)
        row_a.pack(fill="x", pady=(0, 10))
        row_a.columnconfigure(0, weight=1)
        row_a.columnconfigure(1, weight=1)

        self._card_farmed = self._make_card(row_a, "SESSION GEFARMT", GREEN,  0)
        self._card_time   = self._make_card(row_a, "SESSION DAUER",   YELLOW, 1)

        # Dritte Reihe: SP/min + SP/h
        row_b = tk.Frame(stats, bg=BASE)
        row_b.pack(fill="x", pady=(0, 10))
        row_b.columnconfigure(0, weight=1)
        row_b.columnconfigure(1, weight=1)

        self._card_per_min  = self._make_card(row_b, "SP / MINUTE", ORANGE, 0)
        self._card_per_hour = self._make_card(row_b, "SP / STUNDE", MAUVE,  1)

        # Trennlinie
        tk.Frame(self._inner, bg=SEPARATOR, height=1).pack(fill="x", padx=24, pady=(4, 14))

        # Key-Counter-Dashboard
        key_hdr = tk.Frame(self._inner, bg=BASE)
        key_hdr.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(key_hdr, text="Session Tastenzähler",
                 bg=BASE, fg=TEXT, font=FONT_BOLD).pack(side="left")

        reset_btn = tk.Label(key_hdr, text="↺ Zurücksetzen", bg=SURF0, fg=DIM,
                             font=FONT_SMALL, padx=8, pady=2, cursor="hand2")
        reset_btn.pack(side="right")
        reset_btn.bind("<Button-1>", lambda e: self.reset_stats())
        reset_btn.bind("<Enter>", lambda e: reset_btn.config(bg=lighten(SURF0, 0.1), fg=TEXT))
        reset_btn.bind("<Leave>", lambda e: reset_btn.config(bg=SURF0, fg=DIM))

        key_stats = tk.Frame(self._inner, bg=BASE)
        key_stats.pack(fill="x", padx=24, pady=(0, 16))
        key_stats.columnconfigure(0, weight=1)
        key_stats.columnconfigure(1, weight=1)
        key_stats.columnconfigure(2, weight=1)

        self._card_d_key = self._make_key_card(key_stats, "D-TASTE", GREEN,  0)
        self._card_r_key = self._make_key_card(key_stats, "R-TASTE", ORANGE, 1)
        self._card_w_key = self._make_key_card(key_stats, "W-TASTE", BLUE,   2)

        # Trennlinie
        tk.Frame(self._inner, bg=SEPARATOR, height=1).pack(fill="x", padx=24, pady=(4, 14))

        # Chest Hunt Statistik
        ch_hdr = tk.Frame(self._inner, bg=BASE)
        ch_hdr.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(ch_hdr, text="Chest Hunt Statistik",
                 bg=BASE, fg=TEXT, font=FONT_BOLD).pack(side="left")

        ch_stats = tk.Frame(self._inner, bg=BASE)
        ch_stats.pack(fill="x", padx=24, pady=(0, 16))
        ch_stats.columnconfigure(0, weight=1)
        ch_stats.columnconfigure(1, weight=1)
        ch_stats.columnconfigure(2, weight=1)

        self._card_chest_hunts   = self._make_key_card(ch_stats, "CHEST HUNTS",     MAUVE,  0)
        self._card_chests_opened = self._make_key_card(ch_stats, "KISTEN GEÖFFNET", YELLOW, 1)
        self._card_mimics        = self._make_key_card(ch_stats, "MIMIKS",           RED,    2)

        self._parent.after(1000, self._key_poll_loop)

    def _make_key_card(self, parent, label: str, color: str, col: int):
        card = tk.Frame(parent, bg=MANTLE, padx=20, pady=14)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, 10) if col < 2 else (0, 0))
        tk.Label(card, text=label, bg=MANTLE, fg=DIM, font=FONT_LABEL).pack(anchor="w")
        var = tk.StringVar(value="0")
        tk.Label(card, textvariable=var, bg=MANTLE, fg=color,
                 font=FONT_MED).pack(anchor="w", pady=(6, 0))
        return var

    def _make_card(self, parent, label: str, color: str, col: int):
        card = tk.Frame(parent, bg=MANTLE, padx=20, pady=14)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, 10) if col == 0 else (0, 0))
        tk.Label(card, text=label, bg=MANTLE, fg=DIM, font=FONT_LABEL).pack(anchor="w")
        var = tk.StringVar(value="—")
        tk.Label(card, textvariable=var, bg=MANTLE, fg=color,
                 font=FONT_MED).pack(anchor="w", pady=(6, 0))
        return var

    # ── Card callbacks ───────────────────────────────────────

    def _init_cards(self, current_sp_str):
        self._card_current.set(current_sp_str)
        self._card_farmed.set("0")
        self._card_time.set("00:00")
        self._card_per_min.set("0")
        self._card_per_hour.set("0")

    def _update_cards(self, current, farmed, time_str, rate_min, rate_hour):
        self._card_current.set(current)
        self._card_farmed.set(farmed)
        self._card_time.set(time_str)
        self._card_per_min.set(rate_min)
        self._card_per_hour.set(rate_hour)

    def _reset_cards(self):
        self._card_current.set("—")
        self._card_farmed.set("—")
        self._card_time.set("—")
        self._card_per_min.set("—")
        self._card_per_hour.set("—")

    # ── Polling + Actions ────────────────────────────────────

    def _key_poll_loop(self):
        self._card_d_key.set(str(self._key_data.get("d", 0)))
        self._card_r_key.set(str(self._key_data.get("r", 0)))
        self._card_w_key.set(str(self._key_data.get("w", 0)))
        self._card_chest_hunts.set(str(self._key_data.get("chest_hunts", 0)))
        self._card_chests_opened.set(str(self._key_data.get("chests_opened", 0)))
        self._card_mimics.set(str(self._key_data.get("mimics", 0)))
        self._parent.after(1000, self._key_poll_loop)

    def _on_scan(self):
        self._logic.start_scan(self._sp_var.get())

    def reset_stats(self):
        """Reset all session statistics to zero."""
        # Reset key counters
        for k in ("d", "r", "w", "chest_hunts", "chests_opened", "mimics"):
            self._key_data[k] = 0

        # Delegate SP session reset to logic
        self._logic.reset_session(self._sp_data.get("value"))

        # Reset SP cards
        self._card_farmed.set("0")
        self._card_time.set("00:00")
        self._card_per_min.set("0")
        self._card_per_hour.set("0")

        self._log_fn("[Stats] Statistiken zurückgesetzt.")

    def stop(self):
        """Cleanup when UI closes."""
        self._logic.stop()
