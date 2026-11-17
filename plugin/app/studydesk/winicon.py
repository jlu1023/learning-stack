"""Give the Study Desk window a sharp icon (Windows only; a no-op elsewhere).

Chrome and Edge build an app window's icon by scaling the page's 16-pixel
favicon up, which looks pixelated on the taskbar. Windows lets any process
replace a window's icon, so the server (which outlives the page) loads the
real .ico at full size and sets it. Icon handles die with the process that
made them, which is why this lives in the server and not in the launcher.

Nothing Windows-only is imported until `apply` runs on Windows.
"""
from __future__ import annotations

import sys
from pathlib import Path

ICON = Path(__file__).resolve().parent.parent / "static" / "icon.ico"
WM_SETICON, ICON_SMALL, ICON_BIG = 0x0080, 0, 1
IMAGE_ICON, LR_LOADFROMFILE = 1, 0x0010
_handles: dict[int, int] = {}   # size -> HICON, kept for the life of the server


def apply(title: str = "Study Desk") -> int:
    """Set the icon on every Chrome or Edge app window with this exact title.
    Returns how many windows were changed (always 0 off Windows)."""
    if sys.platform != "win32":
        return 0
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                                  ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

    def icon(size: int) -> int:
        if size not in _handles:
            _handles[size] = user32.LoadImageW(None, str(ICON), IMAGE_ICON, size, size, LR_LOADFROMFILE)
        return _handles[size]

    big, small = icon(256), icon(48)
    if not big or not small:
        return 0
    found: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if cls.value.startswith("Chrome_WidgetWin"):
                text = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, text, 256)
                if text.value == title:
                    found.append(hwnd)
        return True

    user32.EnumWindows(each, 0)
    for hwnd in found:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, big)
        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small)
    return len(found)
