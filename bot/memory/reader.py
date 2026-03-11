import ctypes
from ctypes import wintypes
import struct

import numpy as np

kernel32 = ctypes.windll.kernel32

# ── Funktions-Signaturen für 64-Bit-Korrektheit ──
kernel32.OpenProcess.restype  = wintypes.HANDLE
kernel32.VirtualQueryEx.restype = ctypes.c_size_t
kernel32.ReadProcessMemory.restype = wintypes.BOOL

PROCESS_VM_READ           = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT                = 0x1000
PAGE_GUARD                = 0x100
_READABLE = frozenset((0x02, 0x04, 0x08, 0x20, 0x40, 0x80))


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress",       ctypes.c_void_p),
        ("AllocationBase",    ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize",        ctypes.c_size_t),
        ("State",             wintypes.DWORD),
        ("Protect",           wintypes.DWORD),
        ("Type",              wintypes.DWORD),
    ]


class MemoryReader:
    def __init__(self, hwnd: int):
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        self._handle = kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid.value)
        if not self._handle:
            raise RuntimeError(f"Kann Prozess {pid.value} nicht öffnen")
        self._pid = pid.value

    def close(self):
        if self._handle:
            kernel32.CloseHandle(self._handle)
            self._handle = None

    # ── Einzelwert lesen ─────────────────────────────────────

    def read_double(self, address: int):
        buf = ctypes.create_string_buffer(8)
        n   = ctypes.c_size_t()
        ok  = kernel32.ReadProcessMemory(
            self._handle, ctypes.c_void_p(address), buf, 8, ctypes.byref(n))
        if ok and n.value == 8:
            return struct.unpack_from('d', buf.raw)[0]
        return None

    # ── Vollständiger Scan ───────────────────────────────────

    def scan_double(self, value: float, tolerance: float = 100.0):
        return list(self.scan_range(value - tolerance, value + tolerance).keys())

    def scan_range(self, lo: float, hi: float):
        """Scanne den gesamten Prozessspeicher nach double-Werten in [lo, hi]."""
        results = {}
        mbi     = MEMORY_BASIC_INFORMATION()
        address = 0

        while True:
            ret = kernel32.VirtualQueryEx(
                self._handle, ctypes.c_void_p(address),
                ctypes.byref(mbi), ctypes.sizeof(mbi))
            if ret == 0:
                break

            base = mbi.BaseAddress or 0
            size = mbi.RegionSize

            if (mbi.State == MEM_COMMIT
                    and not (mbi.Protect & PAGE_GUARD)
                    and (mbi.Protect & 0xFF) in _READABLE
                    and size < 100_000_000):
                buf = ctypes.create_string_buffer(size)
                n   = ctypes.c_size_t()
                if kernel32.ReadProcessMemory(
                        self._handle, ctypes.c_void_p(base),
                        buf, size, ctypes.byref(n)):
                    read_size = n.value
                    trim      = read_size - (read_size % 8)
                    if trim >= 8:
                        arr  = np.frombuffer(buf.raw[:trim], dtype=np.float64)
                        mask = (arr >= lo) & (arr <= hi)
                        for idx in np.flatnonzero(mask):
                            addr = base + int(idx) * 8
                            results[addr] = float(arr[idx])

            next_addr = base + size
            if next_addr <= address:
                break
            address = next_addr
            if address > 0x7FFF_FFFF_FFFF:
                break

        return results

    # ── Rescan: nur Adressen behalten, deren Wert gestiegen ist

    def rescan_increased(self, candidates, prev_value: float,
                         max_growth_pct: float = 1.0):
        results = []
        ceiling = prev_value * (1 + max_growth_pct / 100)
        for addr in candidates:
            val = self.read_double(addr)
            if val is not None and prev_value < val <= ceiling:
                results.append(addr)
        return results
