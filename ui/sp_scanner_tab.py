import tkinter as tk
from tkinter import ttk
import threading
import time

BASE   = "#1e1e2e"
MANTLE = "#181825"
SURF0  = "#313244"
SURF1  = "#45475a"
TEXT   = "#cdd6f4"
DIM    = "#7f849c"
BLUE   = "#89b4fa"
GREEN  = "#a6e3a1"
RED    = "#f38ba8"
ORANGE = "#fab387"

FONT_UI    = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_MONO  = ("Consolas", 9)
FONT_SMALL = ("Segoe UI", 8)
FONT_HDR   = ("Segoe UI", 9, "bold")


class SpScannerTab:
    def __init__(self, parent, game_title: str = "Idle Slayer", sp_data: dict = None,
                 log_fn=None):
        self._parent = parent
        self._game_title = game_title
        self._sp_data = sp_data if sp_data is not None else {}
        self._log_fn = log_fn or (lambda msg: None)
        self._memory = None
        self._candidates = []       # [(addr, v_initial, v_current)]
        self._scan_thread = None
        self._scanning = False
        self._live_updating = False
        self._stop_flag = threading.Event()

        self._build_ui(parent)

    def _build_ui(self, parent):
        canvas    = tk.Canvas(parent, bg=BASE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self._inner = tk.Frame(canvas, bg=BASE)

        self._inner.bind("<Configure>",
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _scroll(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        canvas.bind("<MouseWheel>", _scroll)
        self._inner.bind("<MouseWheel>", _scroll)

        # Header
        hdr = tk.Frame(self._inner, bg=BASE)
        hdr.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(hdr, text="Slayer Points Scanner",
                 bg=BASE, fg=BLUE, font=FONT_BOLD).pack(side="left")

        # Input fields
        input_card = tk.Frame(self._inner, bg=SURF0, padx=14, pady=10)
        input_card.pack(fill="x", padx=16, pady=(4, 2))

        row1 = tk.Frame(input_card, bg=SURF0)
        row1.pack(fill="x", pady=2)

        tk.Label(row1, text="SP Min:", bg=SURF0, fg=TEXT, font=FONT_UI).pack(side="left")
        self._sp_min_var = tk.StringVar(value="0")
        ttk.Entry(row1, textvariable=self._sp_min_var, width=18).pack(side="left", padx=(8, 20))

        tk.Label(row1, text="SP Max:", bg=SURF0, fg=TEXT, font=FONT_UI).pack(side="left")
        self._sp_max_var = tk.StringVar(value="0")
        ttk.Entry(row1, textvariable=self._sp_max_var, width=18).pack(side="left", padx=(8, 0))

        # Description
        tk.Label(input_card, text="Bereich eingeben, in dem die aktuellen Slayer Points liegen",
                 bg=SURF0, fg=DIM, font=FONT_SMALL, anchor="w").pack(anchor="w", pady=(4, 0))

        # Buttons
        btn_frame = tk.Frame(self._inner, bg=BASE)
        btn_frame.pack(fill="x", padx=16, pady=(8, 4))

        self._btn_scan = tk.Button(
            btn_frame, text="Scan starten", command=self._on_scan,
            bg=GREEN, fg="#11111b", font=FONT_BOLD, relief="flat",
            padx=14, pady=6, cursor="hand2")
        self._btn_scan.pack(side="left", padx=(0, 8))

        self._btn_stop = tk.Button(
            btn_frame, text="Stop", command=self._on_stop,
            bg=RED, fg="#11111b", font=FONT_BOLD, relief="flat",
            padx=14, pady=6, cursor="hand2")

        # Status label
        self._status_var = tk.StringVar(value="")
        self._status_lbl = tk.Label(self._inner, textvariable=self._status_var,
                                    bg=BASE, fg=DIM, font=FONT_SMALL, anchor="w")
        self._status_lbl.pack(fill="x", padx=16, pady=(2, 6))

        # Separator
        tk.Frame(self._inner, bg=SURF0, height=1).pack(fill="x", padx=16, pady=(2, 8))

        # Results table
        table_frame = tk.Frame(self._inner, bg=BASE)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        columns = ("address", "initial", "current", "diff", "pct")
        self._tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                  height=10)
        self._tree.heading("address", text="Adresse")
        self._tree.heading("initial", text="Wert vorher")
        self._tree.heading("current", text="Wert aktuell")
        self._tree.heading("diff",    text="Diff")
        self._tree.heading("pct",     text="%")

        self._tree.column("address", width=160, anchor="w")
        self._tree.column("initial", width=120, anchor="e")
        self._tree.column("current", width=120, anchor="e")
        self._tree.column("diff",    width=100, anchor="e")
        self._tree.column("pct",     width=80,  anchor="e")

        # Style the treeview
        style = ttk.Style()
        style.configure("Treeview",
                        background=SURF0, foreground=TEXT,
                        fieldbackground=SURF0, font=FONT_MONO,
                        rowheight=24)
        style.configure("Treeview.Heading",
                        background=SURF1, foreground=TEXT,
                        font=FONT_HDR)
        style.map("Treeview", background=[("selected", BLUE)],
                  foreground=[("selected", "#11111b")])

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical",
                                    command=self._tree.yview)
        self._tree.configure(yscrollcommand=tree_scroll.set)
        self._tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

    def _set_status(self, text: str):
        self._status_var.set(text)

    def _on_scan(self):
        if self._scanning:
            return

        try:
            sp_min = float(self._sp_min_var.get().replace(",", "").replace("_", ""))
            sp_max = float(self._sp_max_var.get().replace(",", "").replace("_", ""))
        except ValueError:
            self._set_status("Ungültige Eingabe – bitte Zahlen eingeben.")
            return

        if sp_min >= sp_max:
            self._set_status("SP Min muss kleiner als SP Max sein.")
            return

        self._scanning = True
        self._stop_flag.clear()
        self._btn_scan.pack_forget()
        self._btn_stop.pack(side="left", padx=(0, 8))

        # Clear old results
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._candidates = []

        self._scan_thread = threading.Thread(
            target=self._scan_worker, args=(sp_min, sp_max), daemon=True)
        self._scan_thread.start()

    def _on_stop(self):
        self._stop_flag.set()
        self._live_updating = False
        self._scanning = False
        self._sp_data["value"] = None
        self._btn_stop.pack_forget()
        self._btn_scan.pack(side="left", padx=(0, 8))
        self._set_status("Scan abgebrochen.")
        if self._memory:
            self._memory.close()
            self._memory = None

    def _scan_worker(self, sp_min: float, sp_max: float):
        try:
            self._run_scan(sp_min, sp_max)
        except Exception as e:
            self._parent.after(0, lambda: self._set_status(f"Fehler: {e}"))
        finally:
            self._parent.after(0, self._scan_finished)

    def _scan_finished(self):
        self._scanning = False
        self._btn_stop.pack_forget()
        self._btn_scan.pack(side="left", padx=(0, 8))

    def _run_scan(self, sp_min: float, sp_max: float):
        import win32gui
        from bot.memory_reader import GameMemory

        # Find game window
        self._parent.after(0, lambda: self._set_status("Suche Spielfenster..."))
        hwnd = win32gui.FindWindow(None, self._game_title)
        if not hwnd:
            msg = f"[SP] Fenster '{self._game_title}' nicht gefunden!"
            self._log_fn(msg)
            self._parent.after(0, lambda: self._set_status(msg))
            return

        self._log_fn(f"[SP] Suche Adresse für SP-Bereich {sp_min:,.0f} – {sp_max:,.0f}...")
        self._memory = GameMemory(hwnd)

        if self._stop_flag.is_set():
            return

        # Scan 1
        self._parent.after(0, lambda: self._set_status("Scan 1 läuft..."))
        hits1 = self._memory.scan_range(sp_min, sp_max)
        n1 = len(hits1)
        self._parent.after(0, lambda: self._set_status(f"Scan 1: {n1} Treffer. Warte 10s..."))

        if self._stop_flag.is_set():
            return

        # Wait 10 seconds
        for _ in range(100):
            if self._stop_flag.is_set():
                return
            time.sleep(0.1)

        # Scan 2 with wider range
        if not hits1:
            self._parent.after(0, lambda: self._set_status("Keine Treffer in Scan 1."))
            return

        scan2_min = min(hits1.values()) * 0.995
        scan2_max = max(hits1.values()) * 1.05
        self._parent.after(0, lambda: self._set_status("Scan 2 läuft..."))
        hits2 = self._memory.scan_range(scan2_min, scan2_max)
        n2 = len(hits2)
        self._parent.after(0, lambda: self._set_status(f"Scan 2: {n2} Treffer. Filtere..."))

        if self._stop_flag.is_set():
            return

        # Filter candidates
        candidates = []
        for addr in hits1:
            if addr not in hits2:
                continue
            v1, v2 = hits1[addr], hits2[addr]
            diff = v2 - v1
            if diff <= 0:
                continue
            pct = diff / v1 * 100
            if 0.0001 < pct < 2.5:
                candidates.append((addr, v1, v2))

        candidates.sort(key=lambda x: (x[2] - x[1]) / x[1])

        if not candidates:
            msg = "[SP] Keine Adresse gefunden – Bereich anpassen!"
            self._log_fn(msg)
            self._parent.after(0, lambda: self._set_status(msg))
            return

        # Automatically pick the first candidate
        best = candidates[0]
        self._candidates = [best]
        nc = len(candidates)

        self._log_fn(f"[SP] Adresse gefunden: 0x{best[0]:016X} "
                     f"({nc} Kandidat(en), verwende ersten)")

        # Populate table (all candidates shown, first is used for header)
        def fill_table():
            for item in self._tree.get_children():
                self._tree.delete(item)
            for addr, v_init, v_cur in candidates:
                diff = v_cur - v_init
                pct = diff / v_init * 100 if v_init > 0 else 0
                self._tree.insert("", "end", iid=str(addr), values=(
                    f"0x{addr:016X}",
                    f"{v_init:,.2f}",
                    f"{v_cur:,.2f}",
                    f"{diff:,.2f}",
                    f"{pct:.4f}%",
                ))
            self._sp_data["value"] = best[2]
            self._set_status(
                f"{nc} Kandidat(en) – verwende 0x{best[0]:016X}")

        self._parent.after(0, fill_table)

        # Start live update loop
        self._live_updating = True
        self._live_update_loop()

    def _live_update_loop(self):
        if not self._live_updating or self._stop_flag.is_set():
            return
        if not self._memory or not self._candidates:
            return

        updated = []
        for addr, v_init, v_prev in self._candidates:
            try:
                v_now = self._memory.read_double(addr)
                if v_now is None:
                    v_now = v_prev
            except Exception:
                v_now = v_prev

            diff = v_now - v_init
            pct = diff / v_init * 100 if v_init > 0 else 0

            # Update tree item
            item_id = str(addr)
            if self._tree.exists(item_id):
                self._tree.item(item_id, values=(
                    f"0x{addr:016X}",
                    f"{v_init:,.2f}",
                    f"{v_now:,.2f}",
                    f"{diff:,.2f}",
                    f"{pct:.4f}%",
                ))

            updated.append((addr, v_init, v_now))

        self._candidates = updated

        # Erste Adresse in Header-Badge schreiben
        if updated:
            self._sp_data["value"] = updated[0][2]
        ts = time.strftime("%H:%M:%S")
        self._set_status(f"{len(updated)} Kandidaten – Letzte Aktualisierung: {ts}")

        # Schedule next update in 1 second
        self._parent.after(1000, self._live_update_loop)

    def stop(self):
        """Cleanup when UI closes."""
        self._stop_flag.set()
        self._live_updating = False
        self._sp_data["value"] = None
        if self._memory:
            self._memory.close()
            self._memory = None
