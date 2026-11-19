"""Give the Study Desk window a sharp icon, and keep it (Windows only; a no-op elsewhere).

Chrome and Edge build an app window's icon by scaling the page's 16-pixel
favicon up, which looks pixelated on the taskbar. Windows lets any process
replace a window's icon, so the server (which outlives the page) loads the
real .ico at full size and sets it. Icon handles die with the process that
made them, which is why this lives in the server and not in the launcher.

The browser puts its own icon back from time to time, so `keep` runs a small
watcher thread that looks at the window every couple of seconds and sets the
icon again only when it has been replaced.

Nothing Windows-only is imported until `apply` runs on Windows.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ICON = Path(__file__).resolve().parent.parent / "static" / "icon.ico"
WM_SETICON, WM_GETICON, ICON_SMALL, ICON_BIG = 0x0080, 0x007F, 0, 1
IMAGE_ICON, LR_LOADFROMFILE = 1, 0x0010
SMTO_ABORTIFHUNG, TIMEOUT_MS = 0x0002, 200
_handles: dict[int, int] = {}   # size -> HICON, kept for the life of the server
_user32 = None
_watcher: threading.Thread | None = None


def _api():
    global _user32
    if _user32 is None:
        import ctypes
        from ctypes import wintypes

        u = ctypes.WinDLL("user32", use_last_error=True)
        u.LoadImageW.restype = wintypes.HANDLE
        u.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                                 ctypes.c_int, ctypes.c_int, wintypes.UINT]
        # SendMessageTimeout, not SendMessage: a hung browser window must not hang the server.
        u.SendMessageTimeoutW.restype = wintypes.LPARAM
        u.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
                                          wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
        _user32 = u
    return _user32


def _icon(size: int) -> int:
    if size not in _handles:
        _handles[size] = _api().LoadImageW(None, str(ICON), IMAGE_ICON, size, size, LR_LOADFROMFILE) or 0
    return _handles[size]


def _send(hwnd: int, msg: int, wparam: int, lparam: int) -> int | None:
    import ctypes

    out = ctypes.c_size_t(0)
    ok = _api().SendMessageTimeoutW(hwnd, msg, wparam, lparam, SMTO_ABORTIFHUNG, TIMEOUT_MS, ctypes.byref(out))
    return out.value if ok else None


def _windows(title: str) -> list[int]:
    import ctypes
    from ctypes import wintypes

    user32, found = _api(), []

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
    return found


def apply(title: str = "Study Desk", only_if_changed: bool = False) -> int:
    """Set the icon on every Chrome or Edge app window with this exact title.
    Returns how many windows were changed (always 0 off Windows)."""
    if sys.platform != "win32":
        return 0
    big, small = _icon(256), _icon(48)
    if not big or not small:
        return 0
    changed = 0
    for hwnd in _windows(title):
        if only_if_changed and _send(hwnd, WM_GETICON, ICON_BIG, 0) == big:
            continue
        _send(hwnd, WM_SETICON, ICON_BIG, big)
        _send(hwnd, WM_SETICON, ICON_SMALL, small)
        changed += 1
    return changed


def keep(title: str = "Study Desk", every: float = 2.0) -> bool:
    """Start (once) a daemon thread that puts the icon back whenever the browser
    replaces it. Returns whether a watcher is running (always False off Windows)."""
    global _watcher
    if sys.platform != "win32":
        return False
    if _watcher and _watcher.is_alive():
        return True

    def loop():
        while True:
            try:
                apply(title, only_if_changed=True)
            except Exception:
                pass   # cosmetic only: never let this take the server down
            time.sleep(every)

    _watcher = threading.Thread(target=loop, name="window-icon", daemon=True)
    _watcher.start()
    return True
