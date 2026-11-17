"""Start Study Desk: `python <plugin>/app/serve.py` from the folder you study in.

  serve.py                      start the server for the current folder and open the browser
  serve.py --folder PATH        study a different folder (a vault, or a connected notes folder)
  serve.py --background         start the server detached, open the browser, and return
  serve.py --stop               stop the running server (and its tutor processes)

If Study Desk is already running on the port, a second launch only opens the
browser. Options: --port N (default 8030, or $STUDY_DESK_PORT), --permission-mode
MODE (default auto, or $STUDY_DESK_PERMISSION_MODE), --model NAME, --data PATH
(or $STUDY_DESK_DATA), --window browser|app|none. A `config.json` in the data
folder may set "port", "permission_mode" and "model"; flags and environment
variables win over it.

Standard library only: Python 3.10 or later, nothing to install.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from studydesk.server import (DEFAULT_PERMISSION_MODE, DEFAULT_PORT, PERMISSION_MODES,  # noqa: E402
                              Desk, DeskServer, default_data_dir)

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # never through a proxy


def url_for(port: int) -> str:
    return f"http://127.0.0.1:{port}"


def health(port: int, timeout: float = 2.0) -> dict | None:
    """The running Study Desk's health reply, or None if it is not ours or not up."""
    try:
        with _OPENER.open(url_for(port) + "/api/health", timeout=timeout) as res:
            data = json.loads(res.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None
    return data if isinstance(data, dict) and data.get("app") == "study-desk" else None


def stop(port: int) -> bool:
    req = urllib.request.Request(url_for(port) + "/api/shutdown", data=b"", method="POST",
                                 headers={"X-Study-Desk": "1"})
    try:
        with _OPENER.open(req, timeout=5):
            return True
    except (OSError, urllib.error.URLError):
        return False


def read_config(data: Path) -> dict:
    """The optional, hand-edited `config.json` in the data folder."""
    try:
        cfg = json.loads((data / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return cfg if isinstance(cfg, dict) else {}


def resolve_options(args, env=None) -> dict:
    """Flags first, then environment variables, then config.json, then defaults."""
    env = os.environ if env is None else env
    data = Path(args.data).expanduser() if args.data else default_data_dir(env)
    cfg = read_config(data)
    port = args.port or env.get("STUDY_DESK_PORT") or cfg.get("port") or DEFAULT_PORT
    try:
        port = int(port)
    except (TypeError, ValueError):
        raise ValueError(f"the port must be a number, not '{port}'") from None
    if not 1 <= port <= 65535:
        raise ValueError(f"the port must be between 1 and 65535, not {port}")
    mode = args.permission_mode or env.get("STUDY_DESK_PERMISSION_MODE") or cfg.get("permission_mode") \
        or DEFAULT_PERMISSION_MODE
    if mode not in PERMISSION_MODES:
        raise ValueError(f"the permission mode must be one of {', '.join(PERMISSION_MODES)}, not '{mode}'")
    folder = Path(args.folder or env.get("STUDY_DESK_FOLDER") or Path.cwd()).expanduser().resolve()
    return {"folder": folder, "data": data, "port": port, "permission_mode": mode,
            "model": str(args.model or cfg.get("model") or ""),
            "explicit_folder": bool(args.folder or env.get("STUDY_DESK_FOLDER"))}


def find_app_browser(env=None, platform: str | None = None) -> str | None:
    """A Chrome, Edge or Chromium that can open a page as its own window."""
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        tails = (("Google", "Chrome", "Application", "chrome.exe"), ("Microsoft", "Edge", "Application", "msedge.exe"))
        bases = [env.get(k) for k in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")]
        candidates = [str(Path(b, *t)) for t in tails for b in bases if b]
    elif platform == "darwin":
        candidates = [f"/Applications/{n}.app/Contents/MacOS/{n}"
                      for n in ("Google Chrome", "Microsoft Edge", "Chromium")]
    else:
        candidates = [shutil.which(n) for n in ("google-chrome", "google-chrome-stable", "chromium",
                                                "chromium-browser", "microsoft-edge")]
    return next((c for c in candidates if c and Path(c).is_file()), None)


def open_window(url: str, mode: str, data: Path) -> None:
    """`browser`: a tab in the default browser. `app`: its own maximised window
    (Chrome, Edge or Chromium), else the default browser. `none`: nothing."""
    if mode == "none":
        return
    exe = find_app_browser() if mode == "app" else None
    if exe:
        # Its own profile folder makes the browser start a separate process, which
        # is what lets --start-maximized apply while your normal browser is open.
        profile = data / "browser"
        try:
            subprocess.Popen([exe, f"--app={url}", f"--user-data-dir={profile}", "--start-maximized",
                              "--no-first-run", "--no-default-browser-check"], **_detached())
            return
        except OSError:
            pass
    webbrowser.open(url)


def _detached() -> dict:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
                "stdin": subprocess.DEVNULL}
    return {"start_new_session": True, "stdin": subprocess.DEVNULL}


def start_background(opts: dict) -> bool:
    """Start the server as its own process, logging to the data folder, and
    wait until it answers."""
    opts["data"].mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(Path(__file__).resolve()), "--folder", str(opts["folder"]),
           "--data", str(opts["data"]), "--port", str(opts["port"]),
           "--permission-mode", opts["permission_mode"], "--window", "none"]
    if opts["model"]:
        cmd += ["--model", opts["model"]]
    with open(opts["data"] / "server.log", "ab") as log:
        subprocess.Popen(cmd, cwd=str(opts["folder"]), stdout=log, stderr=log, **_detached())
    for _ in range(60):
        time.sleep(0.25)
        if health(opts["port"], timeout=1):
            return True
    return False


def fail(message: str, dialog: bool = False, code: int = 1) -> int:
    print(message, file=sys.stderr)
    if dialog and sys.platform == "win32":      # launched with no console: say it in a box
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Study Desk", 0x10)
    return code


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="serve.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", default=None, help="the folder you study in (default: the current folder)")
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--permission-mode", default=None, help=f"one of {', '.join(PERMISSION_MODES)}")
    ap.add_argument("--model", default=None, help="the tutor's default model (default: Claude Code's own)")
    ap.add_argument("--data", default=None, help="where settings, uploads and logs are kept")
    ap.add_argument("--window", choices=["browser", "app", "none"], default="browser")
    ap.add_argument("--no-browser", action="store_const", const="none", dest="window")
    ap.add_argument("--background", action="store_true", help="start detached and return")
    ap.add_argument("--stop", action="store_true", help="stop the running server")
    ap.add_argument("--dialog", action="store_true", help="Windows: also show errors in a message box")
    args = ap.parse_args(argv)
    try:
        opts = resolve_options(args)
    except ValueError as e:
        return fail(str(e), args.dialog, 2)
    port, url = opts["port"], url_for(opts["port"])

    if args.stop:
        if not health(port):
            print(f"Study Desk is not running on port {port}.")
            return 0
        if not stop(port):
            return fail(f"Study Desk on port {port} did not stop.", args.dialog)
        print("Study Desk stopped.")
        return 0

    running = health(port)
    if running:
        theirs = Path(str(running.get("folder", "")))
        if opts["explicit_folder"] and theirs != opts["folder"]:
            return fail(f"Study Desk is already running for {theirs}. Stop it first "
                        f"(serve.py --stop), then start it for {opts['folder']}.", args.dialog, 3)
        print(f"Study Desk is already running at {url} for {theirs}.")
        open_window(url, args.window, opts["data"])
        return 0

    if args.background:
        if not start_background(opts):
            return fail(f"Study Desk could not start. See {opts['data'] / 'server.log'}", args.dialog)
        print(f"Study Desk is running at {url} for {opts['folder']}. Stop it with: serve.py --stop")
        open_window(url, args.window, opts["data"])
        return 0

    try:
        desk = Desk(opts["folder"], opts["data"], port, opts["permission_mode"], opts["model"])
        server = DeskServer(desk)
    except (OSError, ValueError) as e:
        return fail(f"Study Desk could not start on port {port}: {e}", args.dialog)
    print(f"Study Desk at {url} for {desk.folder} (permission mode: {desk.permission_mode}). "
          "Press Ctrl+C to stop.", flush=True)
    desk.overview.get()     # start reading the folder straight away
    if args.window != "none":
        threading.Timer(0.3, open_window, (url, args.window, opts["data"])).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        desk.close()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
