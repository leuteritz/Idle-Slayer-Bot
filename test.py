import pymem
import struct
import ctypes
import ctypes.wintypes
import time
import os

pm = pymem.Pymem("Idle Slayer.exe")

class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress",       ctypes.c_ulonglong),
        ("AllocationBase",    ctypes.c_ulonglong),
        ("AllocationProtect", ctypes.wintypes.DWORD),
        ("RegionSize",        ctypes.c_size_t),
        ("State",             ctypes.wintypes.DWORD),
        ("Protect",           ctypes.wintypes.DWORD),
        ("Type",              ctypes.wintypes.DWORD),
    ]

SP_MIN = 13_000_000
SP_MAX = 14_000_000

def scan_heap_range(val_min, val_max):
    k32   = ctypes.windll.kernel32
    mbi   = MBI()
    addr  = 0
    hits  = {}
    while k32.VirtualQueryEx(pm.process_handle, ctypes.c_ulonglong(addr),
                              ctypes.byref(mbi), ctypes.sizeof(mbi)):
        is_heap = (
            mbi.State   == 0x1000  and
            mbi.Type    == 0x20000 and
            mbi.Protect not in (0x01, 0x100, 0)
        )
        if is_heap and mbi.RegionSize > 0:
            try:
                data = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                for i in range(0, len(data) - 8, 8):
                    val = struct.unpack_from('<d', data, i)[0]
                    if val_min <= val <= val_max:
                        hits[mbi.BaseAddress + i] = val
            except Exception:
                pass
        addr = mbi.BaseAddress + mbi.RegionSize
        if addr == 0:
            break
    return hits

# ── Scan 1 ───────────────────────────────────────────────────────────────────
print("Scan 1...")
hits1 = scan_heap_range(SP_MIN, SP_MAX)
print(f"  → {len(hits1)} Treffer")

print("⏳ Warte 20 Sekunden...")
time.sleep(20)

# ── Scan 2 ───────────────────────────────────────────────────────────────────
scan2_min = min(hits1.values()) * 0.99
scan2_max = max(hits1.values()) * 1.10
print("Scan 2...")
hits2 = scan_heap_range(scan2_min, scan2_max)
print(f"  → {len(hits2)} Treffer")

# ── Kandidaten filtern ────────────────────────────────────────────────────────
candidates = []
for addr in hits1:
    if addr not in hits2:
        continue
    v1, v2 = hits1[addr], hits2[addr]
    diff = v2 - v1
    if diff <= 0:
        continue
    pct = diff / v1 * 100
    if 0.0001 < pct < 5.0:
        candidates.append((addr, v1, v2, pct))

candidates.sort(key=lambda x: x[3])
print(f"\n{len(candidates)} Kandidaten gefunden. Starte Live-Anzeige...\n")
time.sleep(1)

if not candidates:
    print("Keine Kandidaten – Bereich anpassen!")
    exit()

# ── Live-Loop ─────────────────────────────────────────────────────────────────
# Anzahl Zeilen die wir überschreiben werden
N = len(candidates)
# Cursor-Up ANSI Code
UP   = f"\033[{N + 2}A"   # +2 für Header + Trennlinie
CLR  = "\033[K"            # Zeile löschen

# Header einmalig drucken
header  = f"  {'Adresse':<20}  {'Wert vorher':>14}  {'Wert aktuell':>14}  {'Diff':>10}  {'%':>8}"
trenner = "-" * len(header)
print(header)
print(trenner)
for addr, v1, v2, pct in candidates:
    print(f"  0x{addr:016X}  {v1:>14,.2f}  {v2:>14,.2f}  {v2-v1:>10,.2f}  {pct:>7.4f}%")

try:
    while True:
        time.sleep(1)

        # Cursor zurück an Anfang der Tabelle
        print(UP, end="")

        # Header neu schreiben
        ts = time.strftime("%H:%M:%S")
        print(f"{CLR}  {'Adresse':<20}  {'Wert vorher':>14}  {'Wert aktuell':>14}  {'Diff':>10}  {'%':>8}  [{ts}]")
        print(f"{CLR}{trenner}")

        # Jede Kandidaten-Zeile aktualisieren
        updated = []
        for addr, v1_orig, v_prev, pct_orig in candidates:
            try:
                v_now = pm.read_double(addr)
            except Exception:
                v_now = v_prev

            diff = v_now - v1_orig
            pct  = diff / v1_orig * 100 if v1_orig > 0 else 0

            # Wert gestiegen → grün, gleich → normal
            if v_now > v_prev:
                color = "\033[92m"   # grün
            elif v_now < v_prev:
                color = "\033[91m"   # rot
            else:
                color = ""
            reset = "\033[0m" if color else ""

            print(f"{CLR}  0x{addr:016X}  {v1_orig:>14,.2f}  {color}{v_now:>14,.2f}{reset}  {diff:>10,.2f}  {pct:>7.4f}%")
            updated.append((addr, v1_orig, v_now, pct_orig))

        candidates = updated

except KeyboardInterrupt:
    print("\n\nBeendet.")
