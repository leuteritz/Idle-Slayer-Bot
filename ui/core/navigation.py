import os
import tkinter as tk
from PIL import Image, ImageTk

from ui.theme import (BASE, MANTLE, SURF0, SURF1, TEXT, DIM, BLUE, GREEN, RED,
                      SEPARATOR, FONT_UI, FONT_HDR, FONT_SMALL, lighten)

NAV_ITEMS = [
    ("quick",   "🚀", "Übersicht"),
    ("bot",     "🤖", "Bot"),
    ("chest",   "📦", "Chest Hunt"),
    ("bonus",   "⭐", "Bonus Stage"),
]


class NavigationManager:
    """Sidebar + Header + Page-Switching + SP-Pill."""

    def __init__(self, root, sp_data):
        self._root = root
        self._sp_data = sp_data
        self._active_page = None
        self._prev_page = None
        self._nav_refs = {}
        self._pages = {}
        self._content = None

    @property
    def active_page(self):
        return self._active_page

    def build_header(self):
        hdr = tk.Frame(self._root, bg=MANTLE)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=SEPARATOR, height=1).pack(side="bottom", fill="x")

        inner = tk.Frame(hdr, bg=MANTLE, padx=24, pady=16)
        inner.pack(fill="x")

        # Icon laden und auf 32×32 skalieren
        try:
            _pil = Image.open("assets/icon.png").resize((32, 32), Image.LANCZOS)
            self._header_icon = ImageTk.PhotoImage(_pil)
            tk.Label(inner, image=self._header_icon,
                     bg=MANTLE).pack(side="left", padx=(0, 8))
        except Exception:
            pass

        tk.Label(inner, text="Idle Slayer Bot",
                 bg=MANTLE, fg=TEXT, font=FONT_HDR).pack(side="left")

        # Status pill
        badge = tk.Frame(inner, bg=SURF0, padx=14, pady=6)
        badge.pack(side="right")
        self._status_dot = tk.Label(badge, text="●", bg=SURF0, fg=RED,
                                    font=("SF Pro Display", 10))
        self._status_dot.pack(side="left")
        self._status_lbl = tk.Label(badge, text="  Gestoppt", bg=SURF0, fg=DIM,
                                    font=FONT_UI)
        self._status_lbl.pack(side="left")

        # SP pill – zweizeilig, klickbar → öffnet Scanner-Seite
        sp_badge = tk.Frame(inner, bg=SURF0, padx=14, pady=6, cursor="hand2")
        sp_badge.pack(side="right", padx=(0, 10))
        self._sp_badge = sp_badge

        # Linke Seite: SP-Texte
        sp_text = tk.Frame(sp_badge, bg=SURF0, cursor="hand2")
        sp_text.pack(side="left")
        self._sp_text_frame = sp_text

        self._sp_label = tk.Label(sp_text, text="SP: ---", bg=SURF0,
                                  fg=DIM, font=FONT_UI, cursor="hand2")
        self._sp_label.pack(anchor="w")
        self._sp_session_label = tk.Label(sp_text, text="", bg=SURF0,
                                          fg=DIM, font=FONT_SMALL, cursor="hand2")
        self._sp_session_label.pack(anchor="w")

        # Rechte Seite: Chevron als Navigationshinweis
        self._sp_chevron = tk.Label(sp_badge, text="\u203a", bg=SURF0, fg=DIM,
                                    font=("SF Pro Display", 16), cursor="hand2")
        self._sp_chevron.pack(side="right", padx=(8, 0))

        # Hover-Effekt
        def _sp_hover_enter(e):
            bg = lighten(SURF1, 10) if self._active_page == "scanner" else SURF1
            for w in (sp_badge, sp_text, self._sp_label,
                      self._sp_session_label, self._sp_chevron):
                w.config(bg=bg)
            self._sp_chevron.config(fg=TEXT)

        def _sp_hover_leave(e):
            bg = SURF1 if self._active_page == "scanner" else SURF0
            for w in (sp_badge, sp_text, self._sp_label,
                      self._sp_session_label, self._sp_chevron):
                w.config(bg=bg)
            self._sp_chevron.config(fg=TEXT if self._active_page == "scanner" else DIM)

        for w in (sp_badge, sp_text, self._sp_label,
                  self._sp_session_label, self._sp_chevron):
            w.bind("<Button-1>", lambda e: self.toggle_scanner_page())
            w.bind("<Enter>", _sp_hover_enter)
            w.bind("<Leave>", _sp_hover_leave)

    def build_body(self):
        """Build sidebar + content area. Returns the content frame for pages."""
        body = tk.Frame(self._root, bg=BASE)
        body.pack(fill="both", expand=True)

        # Sidebar — 220px
        sidebar = tk.Frame(body, bg=MANTLE, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Frame(sidebar, bg=MANTLE, height=12).pack()   # top padding

        # Sidebar right border
        tk.Frame(body, bg=SEPARATOR, width=1).pack(side="left", fill="y")

        # Content area
        self._content = tk.Frame(body, bg=BASE)
        self._content.pack(side="left", fill="both", expand=True)

        # Build nav items
        for key, icon, label in NAV_ITEMS:
            self._make_nav_item(sidebar, key, icon, label)

        tk.Label(sidebar, text="© Leuteritz", bg=MANTLE, fg="#8E8E93",
                 font=("SF Pro Display", 12)).pack(side="bottom", pady=(0, 10))

        return self._content

    def _make_nav_item(self, parent, page_name: str, icon: str, label: str):
        frame = tk.Frame(parent, bg=MANTLE, cursor="hand2")
        frame.pack(fill="x", padx=10, pady=1)

        inner = tk.Frame(frame, bg=MANTLE, padx=14, pady=10)
        inner.pack(fill="x")

        icon_lbl = tk.Label(inner, text=icon, bg=MANTLE, fg=DIM,
                            font=FONT_UI, width=2, anchor="center")
        icon_lbl.pack(side="left")

        lbl = tk.Label(inner, text=label, bg=MANTLE, fg=DIM,
                       font=FONT_UI, anchor="w")
        lbl.pack(side="left", padx=(6, 0), fill="x")

        self._nav_refs[page_name] = (frame, inner, lbl, icon_lbl)

        def on_enter(e):
            if self._active_page != page_name:
                for w in (frame, inner): w.config(bg=SURF0)
                lbl.config(bg=SURF0, fg=TEXT)
                icon_lbl.config(bg=SURF0, fg=TEXT)

        def on_leave(e):
            if self._active_page != page_name:
                for w in (frame, inner): w.config(bg=MANTLE)
                lbl.config(bg=MANTLE, fg=DIM)
                icon_lbl.config(bg=MANTLE, fg=DIM)

        def on_click(e):
            self.show_page(page_name)

        for w in (frame, inner, lbl, icon_lbl):
            w.bind("<Enter>",    on_enter)
            w.bind("<Leave>",    on_leave)
            w.bind("<Button-1>", on_click)

    def register_page(self, name: str, frame):
        self._pages[name] = frame

    def show_page(self, page_name: str):
        # Deactivate old nav highlight
        if self._active_page and self._active_page in self._nav_refs:
            frame, inner, lbl, icon_lbl = self._nav_refs[self._active_page]
            for w in (frame, inner): w.config(bg=MANTLE)
            lbl.config(bg=MANTLE, fg=DIM)
            icon_lbl.config(bg=MANTLE, fg=DIM)
        # Hide old page
        if self._active_page and self._active_page in self._pages:
            self._pages[self._active_page].pack_forget()

        self._active_page = page_name

        # Activate new nav highlight (only if page has a sidebar entry)
        if page_name in self._nav_refs:
            frame, inner, lbl, icon_lbl = self._nav_refs[page_name]
            for w in (frame, inner): w.config(bg=SURF0)
            lbl.config(bg=SURF0, fg=BLUE)
            icon_lbl.config(bg=SURF0, fg=BLUE)

        if page_name in self._pages:
            self._pages[page_name].pack(fill="both", expand=True)

        self._update_sp_pill_highlight()

    def toggle_scanner_page(self):
        if self._active_page == "scanner":
            self.show_page(self._prev_page or "quick")
        else:
            self._prev_page = self._active_page
            self.show_page("scanner")

    def _update_sp_pill_highlight(self):
        """Highlight SP pill when scanner page is active."""
        bg = SURF1 if self._active_page == "scanner" else SURF0
        for w in (self._sp_badge, self._sp_text_frame,
                  self._sp_label, self._sp_session_label, self._sp_chevron):
            w.config(bg=bg)
        self._sp_chevron.config(fg=TEXT if self._active_page == "scanner" else DIM)

    def set_status(self, text: str, dot_color: str):
        self._status_dot.configure(fg=dot_color)
        self._status_lbl.configure(text=f"  {text}")

    def update_sp_pill(self):
        """Update SP pill display from shared sp_data dict."""
        sp = self._sp_data.get("value")
        sp_start = self._sp_data.get("session_start")
        if sp is not None:
            from bot.memory.format import format_sp
            self._sp_label.configure(text=f"SP: {format_sp(sp)}", fg=GREEN)
            if sp_start is not None and sp_start > 0:
                farmed = max(0.0, sp - sp_start)
                pct = farmed / sp_start * 100
                self._sp_session_label.configure(
                    text=f"+{format_sp(farmed)}  +{pct:.1f}%", fg=GREEN)
            else:
                self._sp_session_label.configure(text="", fg=DIM)
        else:
            self._sp_label.configure(text="SP: ---", fg=DIM)
            self._sp_session_label.configure(text="", fg=DIM)
