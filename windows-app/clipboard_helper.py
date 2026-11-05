"""Small, thread-safe Win32 clipboard helpers (Unicode text only)."""

import ctypes
import time
from ctypes import wintypes

# Private DLL instances so our prototypes never clash with other modules
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

_user32.OpenClipboard.argtypes = [wintypes.HWND]
_user32.OpenClipboard.restype = wintypes.BOOL
_user32.CloseClipboard.argtypes = []
_user32.CloseClipboard.restype = wintypes.BOOL
_user32.EmptyClipboard.argtypes = []
_user32.EmptyClipboard.restype = wintypes.BOOL
_user32.GetClipboardData.argtypes = [wintypes.UINT]
_user32.GetClipboardData.restype = wintypes.HANDLE
_user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
_user32.SetClipboardData.restype = wintypes.HANDLE
_user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
_user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
_user32.GetClipboardSequenceNumber.argtypes = []
_user32.GetClipboardSequenceNumber.restype = wintypes.DWORD

_kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
_kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
_kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalFree.restype = wintypes.HGLOBAL
_kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalLock.restype = ctypes.c_void_p
_kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalUnlock.restype = wintypes.BOOL


def sequence_number() -> int:
    """Changes every time any application modifies the clipboard."""
    return int(_user32.GetClipboardSequenceNumber())


def has_text() -> bool:
    return bool(_user32.IsClipboardFormatAvailable(CF_UNICODETEXT))


def _open(retries: int = 10) -> bool:
    for _ in range(retries):
        if _user32.OpenClipboard(None):
            return True
        time.sleep(0.02)
    return False


def get_clipboard() -> str:
    """Return the clipboard text, or '' if there is none."""
    if not _open():
        return ""
    try:
        h_mem = _user32.GetClipboardData(CF_UNICODETEXT)
        if not h_mem:
            return ""
        ptr = _kernel32.GlobalLock(h_mem)
        if not ptr:
            return ""
        try:
            return ctypes.wstring_at(ptr)
        finally:
            _kernel32.GlobalUnlock(h_mem)
    finally:
        _user32.CloseClipboard()


def set_clipboard(text: str) -> bool:
    if not _open():
        return False
    try:
        _user32.EmptyClipboard()
        data = (text + "\0").encode("utf-16-le")
        h_mem = _kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not h_mem:
            return False
        ptr = _kernel32.GlobalLock(h_mem)
        if not ptr:
            _kernel32.GlobalFree(h_mem)
            return False
        ctypes.memmove(ptr, data, len(data))
        _kernel32.GlobalUnlock(h_mem)
        if not _user32.SetClipboardData(CF_UNICODETEXT, h_mem):
            _kernel32.GlobalFree(h_mem)  # ownership was not transferred
            return False
        return True
    finally:
        _user32.CloseClipboard()
