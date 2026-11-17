"""Study Desk server: a local window onto the learn plugin.

Standard library only, like the engine. It is a shell: the teaching rules stay
in the plugin's skills and the scheduling stays in the engine (`vl.py`), which
this server only ever asks for JSON. It never writes into the notes folder.
Learner state changes only when the tutor (headless Claude Code, started in
the study folder) runs the engine's `record`, exactly as in the terminal.

Everything the server keeps (style settings, photos of working, the last known
usage limits, its log) lives in a per-user data folder, never in the plugin or
the notes.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

APP_DIR = Path(__file__).resolve().parent.parent
STATIC = APP_DIR / "static"
ENGINE = APP_DIR.parent / "engine" / "vl.py"

DEFAULT_PORT = 8030
MODELS = {"opus", "sonnet", "haiku", "fable"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
# `bypassPermissions` is left out on purpose: the app never offers it.
PERMISSION_MODES = ("auto", "acceptEdits", "manual", "default", "dontAsk", "plan")
DEFAULT_PERMISSION_MODE = "auto"
IDLE_SECONDS = 20 * 60
OVERVIEW_SECONDS = 600
MAX_UPLOAD = 20 * 1024 * 1024
MAX_JSON = 1024 * 1024
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Tab colours, in order; each can be changed in the app's Style panel.
PALETTE = ("#e03131", "#1971c2", "#2f9e44", "#f08c00", "#7048e8", "#0c8599", "#c2255c", "#5c940d")
GENERAL_ACCENT = "#868e96"


class HttpError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


class EngineError(RuntimeError):
    pass


# ---------------------------------------------------------------- folders
def default_data_dir(env=None, platform: str | None = None, home: Path | None = None) -> Path:
    """Where settings, uploads, usage and logs go: $STUDY_DESK_DATA, else the
    platform's per-user data folder. Never the plugin, never the notes."""
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else Path(home)
    if env.get("STUDY_DESK_DATA"):
        return Path(env["STUDY_DESK_DATA"]).expanduser()
    if platform == "win32":
        base = env.get("LOCALAPPDATA")
        return (Path(base) if base else home / "AppData" / "Local") / "StudyDesk"
    if platform == "darwin":
        return home / "Library" / "Application Support" / "StudyDesk"
    base = env.get("XDG_DATA_HOME")
    return (Path(base) if base else home / ".local" / "share") / "study-desk"


def build_tabs(courses) -> list[dict]:
    """One tab per course, in the engine's order, then a General tab."""
    tabs = []
    for i, code in enumerate(dict.fromkeys(str(c) for c in courses)):
        tabs.append({"id": code, "course": code, "label": code, "title": "",
                     "accent": PALETTE[i % len(PALETTE)]})
    general = "General" if all(t["id"] != "General" for t in tabs) else "General tab"
    tabs.append({"id": general, "course": None, "label": "General",
                 "title": "Mixed quiz, the week ahead, or anything else", "accent": GENERAL_ACCENT})
    return tabs


# ---------------------------------------------------------------- static files
MIME = {
    ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8", ".json": "application/json", ".svg": "image/svg+xml",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
    ".webp": "image/webp", ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2",
    ".ttf": "font/ttf", ".md": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8",
}


def resolve_static(url_path: str, root: Path = STATIC) -> Path | None:
    """The file under `root` that a URL path names, or None.

    Refuses anything that is not a plain relative path: `..`, hidden names,
    backslashes, drive letters, NUL, and (after resolving links) any file that
    ends up outside `root`.
    """
    path = unquote(url_path)
    if path in ("", "/"):
        path = "/index.html"
    if not path.startswith("/") or "\\" in path or "\x00" in path or ":" in path:
        return None
    parts = path.split("/")[1:]
    if any(p in ("", ".", "..") or p.startswith(".") for p in parts):
        return None
    base = root.resolve()
    try:
        target = base.joinpath(*parts).resolve()
    except (OSError, ValueError):
        return None
    if base not in target.parents or not target.is_file():
        return None
    return target


# ---------------------------------------------------------------- stream parsing
def tool_summary(name: str, inp: dict) -> str:
    if name in ("Bash", "PowerShell"):
        cmd = str(inp.get("command", ""))
        m = re.search(r"vl\.py[\"']?\s+(.*)", cmd, re.S)
        return ("engine: " + m.group(1) if m else cmd).replace("\n", " ")[:160]
    for key in ("file_path", "pattern", "path", "query", "url", "skill"):
        if inp.get(key):
            value = str(inp[key]).replace("\\", "/")
            if key == "file_path":
                value = value.rsplit("/", 1)[-1]
            return f"{name}: {value}"[:160]
    return name


def parse_line(line: str, wrote_text: bool) -> list[dict]:
    """Turn one line of `claude -p --output-format stream-json` into UI events."""
    try:
        d = json.loads(line)
    except ValueError:
        return []
    if not isinstance(d, dict):
        return []
    kind = d.get("type")
    if kind == "system" and d.get("subtype") == "init" and d.get("session_id"):
        return [{"t": "session", "id": d["session_id"]}]
    if kind == "stream_event":
        ev = d.get("event") or {}
        if ev.get("type") == "content_block_start":
            block = (ev.get("content_block") or {}).get("type")
            phase = {"thinking": "thinking", "text": "writing", "tool_use": "working"}.get(block)
            out = [{"t": "phase", "p": phase}] if phase else []
            if block == "text" and wrote_text:
                out.append({"t": "text", "d": "\n\n"})
            return out
        delta = ev.get("delta") or {}
        if ev.get("type") == "content_block_delta" and delta.get("type") == "text_delta":
            return [{"t": "text", "d": delta.get("text", "")}]
        return []
    if kind == "assistant":
        out = []
        for block in (d.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                out.append({"t": "tool", "summary": tool_summary(block.get("name", ""), block.get("input") or {})})
        return out
    if kind == "system" and d.get("subtype") == "thinking_tokens":
        return [{"t": "thinking", "tokens": d.get("estimated_tokens", 0)}]
    if kind == "rate_limit_event":
        return [{"t": "rate", "info": d.get("rate_limit_info") or {}}]
    if kind == "result":
        usage = d.get("usage") or {}
        last = (usage.get("iterations") or [usage])[-1]
        context = sum(last.get(k, 0) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        event = {"t": "done", "output_tokens": usage.get("output_tokens", 0),
                 "context_tokens": context, "cost_usd": d.get("total_cost_usd", 0.0)}
        if d.get("is_error") or d.get("subtype") != "success":
            event["error"] = str(d.get("result") or d.get("subtype"))
        return [event]
    return []


def kill_tree(proc: subprocess.Popen) -> None:
    """Stop a process and everything it started."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, creationflags=NO_WINDOW)
    else:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(proc.pid, sig)     # the tutor is started in its own session
            except (ProcessLookupError, PermissionError):
                break
            try:
                proc.wait(timeout=3)
                break
            except subprocess.TimeoutExpired:
                continue
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


# ---------------------------------------------------------------- tutor
SYSTEM_NOTE = (
    "You are running inside Study Desk, a local study app, not a terminal. "
    "Your replies are rendered as Markdown with KaTeX, so write ALL maths as LaTeX: $...$ inline and "
    "$$...$$ on its own lines for display (this replaces the method skill's rule that chat maths is Unicode, "
    "which exists only because a terminal cannot render LaTeX). Mermaid code blocks render as diagrams. "
    "A [[Note Name]] wikilink, or a Markdown link to a note file, is clickable and opens that note beside "
    "the chat, so link the node you are teaching or testing when its name is not itself the answer. "
    "AskUserQuestion does not exist here: ask every question as plain text (multiple-choice options on "
    "their own lines as A, B, C, D), ask for confidence in the same message, then stop and wait for the "
    "user's typed reply. Emphasis is sparse and always means the same thing: bold only the term being "
    "defined in a definition and the hypotheses of a theorem (so the conditions stand apart from the "
    "conclusion); no other bold, no colour, no highlighting, and no emphasis at all inside a question, "
    "where it would give the answer away. Everything else (the method skill, Teaching Style, recording "
    "through the engine) applies unchanged."
)


class Tutor:
    """One long-lived headless Claude Code process per tab."""

    def __init__(self, desk: "Desk") -> None:
        self.desk = desk
        self.sessions: dict[str, str] = {}      # tab -> Claude session id (memory only)
        self.procs: dict[str, dict] = {}         # tab -> live process record
        self.busy: set[str] = set()
        self.totals: dict[str, dict] = {}
        self.lock = threading.Lock()
        self.rate: dict = {}
        try:  # the last known limits survive a restart, so the meter is never blank
            self.rate = json.loads(desk.usage_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass

    def command(self, tab: str, model: str = "", effort: str = "") -> list[str]:
        note = SYSTEM_NOTE
        course = self.desk.tab(tab).get("course")
        if course:
            course = re.sub(r'["%\r\n]', "", course)
            note += f" This tab is the {course} compartment: stay on {course} unless the user asks otherwise."
        cmd = [*self.desk.claude_argv(), "-p", "--input-format", "stream-json", "--output-format", "stream-json",
               "--verbose", "--include-partial-messages",
               "--permission-mode", self.desk.permission_mode,
               "--append-system-prompt", note, "--add-dir", str(self.desk.uploads),
               "--disallowedTools", "AskUserQuestion"]
        model = model if model in MODELS else self.desk.model
        if model:
            cmd += ["--model", model]
        if effort in EFFORTS:
            cmd += ["--effort", effort]
        if tab in self.sessions:
            cmd += ["--resume", self.sessions[tab]]
        return cmd

    def stop(self, tab: str) -> bool:
        """Kill the tab's Claude process. Its session id is kept, so the next
        message starts a new process that resumes the same conversation."""
        live = self.procs.pop(tab, None)
        if live is None or live["proc"].poll() is not None:
            return False
        kill_tree(live["proc"])
        return True

    def stop_all(self) -> None:
        for tab in list(self.procs):
            self.stop(tab)

    def reset(self, tab: str) -> None:
        self.stop(tab)
        self.sessions.pop(tab, None)
        self.totals.pop(tab, None)

    def process(self, tab: str, model: str, effort: str) -> dict:
        """The tab's long-lived Claude process, started on first use.

        One process per tab stays open between messages (as the terminal
        does), which saves the start-up and conversation reload on every turn.
        It is replaced when the model or effort changes, and idle ones are
        closed after 20 minutes; either way the conversation resumes.
        """
        now = time.time()
        for other, live in list(self.procs.items()):
            if other != tab and other not in self.busy and now - live["used"] > IDLE_SECONDS:
                self.stop(other)
        live = self.procs.get(tab)
        if live and (live["proc"].poll() is not None or live["key"] != (model, effort)):
            self.stop(tab)
            live = None
        if live is None:
            extra = {"creationflags": NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
            proc = subprocess.Popen(
                self.command(tab, model, effort), cwd=str(self.desk.folder), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="replace", **extra,
            )
            tail: list[str] = []

            def drain() -> None:
                for line in proc.stderr:
                    tail.append(line)
                    del tail[:-20]

            threading.Thread(target=drain, daemon=True).start()
            live = self.procs[tab] = {"proc": proc, "key": (model, effort), "stderr": tail, "used": now}
        live["used"] = now
        return live

    def stream(self, tab: str, text: str, model: str = "", effort: str = ""):
        """Send one message and yield the reply as Server-Sent Events."""
        def sse(obj: dict) -> str:
            return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"

        with self.lock:
            taken = tab in self.busy
            self.busy.add(tab)
        if taken:
            yield sse({"t": "error", "msg": "This tab is still answering. Press Esc to stop it first."})
            return
        wrote_text = False
        finished = False
        live = None
        try:
            live = self.process(tab, model if model in MODELS else "", effort if effort in EFFORTS else "")
            proc = live["proc"]
            message = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}
            proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            proc.stdin.flush()
            for line in iter(proc.stdout.readline, ""):
                for event in parse_line(line, wrote_text):
                    if event["t"] == "text":
                        wrote_text = True
                    elif event["t"] == "session":
                        self.sessions[tab] = event["id"]
                        continue
                    elif event["t"] == "rate":
                        self.rate = event["info"]
                        try:
                            self.desk.usage_file.write_text(json.dumps(self.rate), encoding="utf-8")
                        except OSError:
                            pass
                    elif event["t"] == "done":
                        finished = True
                        tot = self.totals.setdefault(tab, {"turns": 0, "output_tokens": 0, "cost_usd": 0.0})
                        tot["turns"] += 1
                        tot["output_tokens"] += event.get("output_tokens", 0) or 0
                        tot["cost_usd"] += event.get("cost_usd", 0.0) or 0.0
                        tot["context_tokens"] = event.get("context_tokens", 0)
                        event["totals"] = tot
                    yield sse(event)
                if finished:
                    break   # the turn is over; the process stays open for the next message
        except Exception as exc:
            yield sse({"t": "error", "msg": str(exc)})
            finished = True
        finally:
            self.busy.discard(tab)
            if live is not None:
                live["used"] = time.time()
            if not finished:   # browser went away, Esc, or the process died mid-turn
                self.stop(tab)
            self.desk.overview.built = 0.0  # a turn may have recorded results
        if not finished:
            tail = "".join(live["stderr"]).strip()[-500:] if live else ""
            yield sse({"t": "error", "msg": tail or "Stopped before finishing."})


# ---------------------------------------------------------------- overview
class Overview:
    """Cached dashboard data. Engine calls can take seconds each on a large
    folder, so they run in a small pool and the last good answer is served
    meanwhile."""

    def __init__(self, desk: "Desk") -> None:
        self.desk = desk
        self.data: dict | None = None
        self.built = 0.0
        self.building = False
        self.lock = threading.Lock()
        self.stats_supported: bool | None = None   # unknown until the engine is asked once

    def summarise_course(self, code: str) -> dict:
        """Per-unit progress for one course, from `graph` and `unit all`."""
        graph = self.desk.run_engine("graph", code)
        try:
            units = self.desk.run_engine("unit", code, "all").get("units") or []
        except Exception:   # the units panel is optional: the table still shows
            units = None
        by_unit: dict = {}
        levels: dict = {}
        for node in graph.get("nodes") or []:
            if node.get("type") in ("proof", "example") or "proof_state" in node:
                continue
            level = (node.get("state") or {}).get("mastery") or "unseen"
            levels[level] = levels.get(level, 0) + 1
            slot = by_unit.setdefault(node.get("unit"), {})
            slot[level] = slot.get(level, 0) + 1
        out_units = None
        if units is not None:
            out_units = []
            for u in units:
                if not isinstance(u, dict):
                    continue
                counts = by_unit.get(u.get("unit"), {})
                out_units.append({
                    "unit": u.get("unit"), "name": u.get("name") or f"Unit {u.get('unit')}",
                    "title": u.get("title") or "", "started": bool(u.get("started", False)),
                    "primer": u.get("primer"), "nodes": sum(counts.values()), "levels": counts,
                })
        return {"course": code, "levels": levels, "nodes": sum(levels.values()), "units": out_units}

    def stats(self) -> dict | None:
        """Retention figures, if this engine has a `stats` command. The public
        engine has none yet, so the page simply shows no retention line."""
        if self.stats_supported is False:
            return None
        try:
            out = self.desk.run_engine("stats", "mixed")
        except Exception:
            self.stats_supported = False
            return None
        self.stats_supported = True
        return {k: out.get(k) for k in ("attempts", "reviews")}

    def build(self) -> None:
        try:
            errors: dict = {}
            layout = self.desk.refresh_layout()
            if layout.get("error"):
                errors["folder"] = layout["error"]
            courses_list = layout["courses"]
            with ThreadPoolExecutor(max_workers=3) as pool:
                due_f = pool.submit(self.desk.run_engine, "due", "mixed")
                stats_f = pool.submit(self.stats)
                course_f = {c: pool.submit(self.summarise_course, c) for c in courses_list}
            courses: dict = {}
            for code, fut in course_f.items():
                try:
                    courses[code] = fut.result()
                except Exception as exc:  # one broken course must not blank the page
                    errors[code] = str(exc)
            due = None
            try:
                due = due_f.result()
            except Exception as exc:     # no `due`: the Due and Redos columns are hidden
                errors["due"] = str(exc)
            items = (due or {}).get("due") or []
            redos = (due or {}).get("redos")
            for code in courses:
                if due is None:
                    courses[code].update(due=None, due_items=[], redos=None)
                    continue
                mine = [d for d in items if d.get("course") == code]
                courses[code]["due"] = len(mine)
                courses[code]["due_items"] = [
                    {"name": d.get("name"), "overdue_days": d.get("overdue_days", 0),
                     "mastery": (d.get("state") or {}).get("mastery")}
                    for d in sorted(mine, key=lambda d: -(d.get("overdue_days") or 0))[:40]
                ]
                courses[code]["redos"] = None if redos is None else sum(
                    1 for r in redos if str(r.get("course", "")).upper() == code.upper())
            self.data = {
                "date": (due or {}).get("date", ""), "courses": courses, "errors": errors,
                "course_codes": courses_list,
                "due_total": None if due is None else due.get("due_total", len(items)),
                "stats": stats_f.result(), "built": time.time(),
            }
            self.built = time.time()
        finally:
            self.building = False

    def get(self, force: bool = False) -> dict:
        with self.lock:
            stale = force or self.data is None or time.time() - self.built > OVERVIEW_SECONDS
            if stale and not self.building:
                self.building = True
                threading.Thread(target=self.build, daemon=True).start()
        return {"loading": self.building, **(self.data or {"courses": {}, "errors": {}})}


# ---------------------------------------------------------------- notes
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")
SKIP_DIRS = ("_archive", "node_modules")


class NoteIndex:
    def __init__(self, desk: "Desk") -> None:
        self.desk = desk
        self.names: dict[str, list[Path]] = {}
        self.assets: dict[str, Path] = {}
        self.built = 0.0
        self.roots: tuple = ()

    def ensure(self) -> None:
        roots = tuple(self.desk.roots())
        if time.time() - self.built < 300 and self.names and roots == self.roots:
            return
        names: dict[str, list[Path]] = {}
        assets: dict[str, Path] = {}
        # a state folder inside the notes folder is walked once, as part of it
        tops = [r for r in roots if not any(o != r and o in r.parents for o in roots)]
        for top in tops:
            for dirpath, dirnames, filenames in os.walk(top):
                dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
                for fn in sorted(filenames):
                    p = Path(dirpath) / fn
                    low = fn.lower()
                    if low.endswith(".md"):
                        names.setdefault(low[:-3], []).append(p)
                    elif low.endswith(IMAGE_EXT):
                        assets.setdefault(low, p)
        self.names, self.assets, self.built, self.roots = names, assets, time.time(), roots


# ---------------------------------------------------------------- the desk
class Desk:
    """One running app: a study folder, a data folder and the tutor."""

    def __init__(self, folder, data, port: int = DEFAULT_PORT, permission_mode: str = DEFAULT_PERMISSION_MODE,
                 model: str = "", engine: Path = ENGINE, python: str | None = None) -> None:
        self.folder = Path(folder).expanduser().resolve()
        if not self.folder.is_dir():
            raise ValueError(f"not a folder: {self.folder}")
        if permission_mode not in PERMISSION_MODES:
            raise ValueError(f"permission mode must be one of {', '.join(PERMISSION_MODES)}, not '{permission_mode}'")
        if model and not re.fullmatch(r"[A-Za-z0-9._\[\]-]+", model):
            raise ValueError(f"not a model name: '{model}'")
        self.data = Path(data).expanduser()
        self.uploads = self.data / "uploads"
        self.uploads.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.data / "settings.json"
        self.usage_file = self.data / "usage.json"
        self.port = port
        self.permission_mode = permission_mode
        self.model = model
        self.engine = Path(engine)
        self.python = python or sys.executable
        self._layout: dict = {"root": self.folder, "library": None, "frontend": None, "courses": [],
                              "tabs": build_tabs([]), "error": None}
        self.layout_ready = threading.Event()
        self.layout_lock = threading.Lock()
        self.overview = Overview(self)
        self.notes = NoteIndex(self)
        self.tutor = Tutor(self)

    # ---- the engine
    def run_engine(self, *args: str, timeout: int = 120) -> dict:
        """Run the plugin's own engine from the study folder, as the skills do,
        so it finds the vault or the library's state folder the same way."""
        proc = subprocess.run(
            [self.python, str(self.engine), *args], cwd=str(self.folder), stdin=subprocess.DEVNULL,
            capture_output=True, encoding="utf-8", errors="replace", timeout=timeout, creationflags=NO_WINDOW,
        )
        try:
            out = json.loads(proc.stdout)
        except ValueError:
            out = None
        if proc.returncode != 0:
            if isinstance(out, dict) and out.get("error"):
                raise EngineError(str(out["error"]))
            raise EngineError((proc.stderr or proc.stdout or "the engine failed").strip()[-400:])
        if not isinstance(out, dict):
            raise EngineError("the engine printed no JSON")
        return out

    def claude_argv(self) -> list[str]:
        exe = os.environ.get("STUDY_DESK_CLAUDE") or shutil.which("claude")
        if not exe:
            raise RuntimeError("The `claude` command is not on PATH. Install Claude Code, or set "
                               "STUDY_DESK_CLAUDE to its full path, then start Study Desk again.")
        return [exe]

    # ---- the folder's layout: where the notes are and which courses exist
    def refresh_layout(self) -> dict:
        """Ask the engine which folder it uses here and which courses it sees.
        Works for a vault, a plain-editor vault and a connected library alike."""
        with self.layout_lock:
            layout = dict(self._layout)
            try:
                where = self.run_engine("where")
                layout["root"] = Path(where["root"]).resolve()
                layout["library"] = Path(where["library"]).resolve() if where.get("library") else None
                layout["frontend"] = where.get("frontend")
                layout["courses"] = [str(c) for c in where.get("courses") or []]
                layout["error"] = None
            except Exception as exc:
                layout["error"] = str(exc)
            layout["tabs"] = build_tabs(layout["courses"])
            self._layout = layout
            self.layout_ready.set()
            return layout

    def layout(self, wait: float = 0) -> dict:
        if wait and not self.layout_ready.is_set():
            self.overview.get()                 # starts the first build, which reads the layout
            self.layout_ready.wait(timeout=wait)
        return self._layout

    def tabs(self) -> list[dict]:
        return self._layout["tabs"]

    def tab(self, tab_id: str) -> dict:
        for t in self.tabs():
            if t["id"] == tab_id:
                return t
        raise HttpError(404, "no such tab")

    def roots(self) -> list[Path]:
        """Folders notes may be read from: the engine's folder, and the
        learner's own notes when it is a connected library."""
        lay = self._layout
        return [r for r in dict.fromkeys([lay["root"], lay["library"]]) if r is not None]

    # ---- notes
    def inside(self, p: Path) -> Path:
        p = Path(p).resolve()
        if not any(root == p or root in p.parents for root in self.roots()):
            raise HttpError(403, "outside the notes folder")
        return p

    def relative(self, p: Path) -> str:
        for root in self.roots():
            try:
                return p.resolve().relative_to(root).as_posix()
            except ValueError:
                continue
        return p.name

    def resolve_note(self, target: str, course: str | None = None) -> Path | None:
        target = target.split("#")[0].split("|")[0].strip().replace("\\", "/")
        if target.lower().endswith(".md"):
            target = target[:-3]
        if not target:
            return None
        if "/" in target:
            for root in self.roots():
                p = root / (target + ".md")
                try:
                    if self.inside(p).is_file() and not any(part.startswith(".") for part in Path(target).parts):
                        return p
                except (HttpError, OSError, ValueError):
                    continue
        self.notes.ensure()
        hits = self.notes.names.get(target.rsplit("/", 1)[-1].lower(), [])
        if not hits:
            return None
        if course:  # prefer the tab's own course when a name is duplicated
            for h in hits:
                if f"/{course.lower()}/" in h.as_posix().lower():
                    return h
        return hits[0]

    def note(self, name: str, course: str | None = None) -> dict:
        p = self.resolve_note(name, course)
        if p is None:
            raise HttpError(404, f"no note called {name}")
        self.inside(p)
        return {"name": p.stem, "path": self.relative(p),
                "markdown": p.read_text(encoding="utf-8", errors="replace")}

    def asset(self, name: str) -> Path:
        self.notes.ensure()
        p = self.notes.assets.get(name.replace("\\", "/").rsplit("/", 1)[-1].lower())
        if p is None:
            raise HttpError(404, "no such image")
        return self.inside(p)

    # ---- settings and uploads
    def get_settings(self) -> dict:
        if self.settings_file.is_file():
            try:
                data = json.loads(self.settings_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except (OSError, ValueError):
                pass
        return {}

    def put_settings(self, body) -> None:
        if not isinstance(body, dict):
            raise HttpError(400, "settings must be an object")
        tmp = self.settings_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(body, indent=1), encoding="utf-8")
        os.replace(tmp, self.settings_file)

    UPLOAD_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}

    def save_upload(self, ext: str, body: bytes) -> Path:
        for old in self.uploads.iterdir():  # working photos are throwaway: keep a week
            try:
                if time.time() - old.stat().st_mtime > 7 * 86400:
                    old.unlink()
            except OSError:
                pass
        stamp = f"{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() // 1000 % 1000000:06d}"
        path = self.uploads / f"working-{stamp}{ext}"
        path.write_bytes(body)
        return path

    def chat_text(self, body) -> str:
        """The message for the tutor, with any attached photos named as files."""
        if not isinstance(body, dict):
            raise HttpError(400, "the message must be an object")
        text = str(body.get("text", "")).strip()
        if not text:
            raise HttpError(400, "empty message")
        images = body.get("images") or []
        if not isinstance(images, list):
            raise HttpError(400, "unknown image")
        uploads = self.uploads.resolve()
        for path in images:
            try:
                p = Path(str(path)).resolve()
            except (OSError, ValueError):
                raise HttpError(400, "unknown image") from None
            if uploads not in p.parents or not p.is_file():
                raise HttpError(400, "unknown image")
            text += f"\n\n[Photo of my working, read this image file: {p}]"
        return text

    def close(self) -> None:
        self.tutor.stop_all()


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "StudyDesk"
    sys_version = ""
    timeout = 120

    @property
    def desk(self) -> Desk:
        return self.server.desk

    def log_message(self, fmt, *args):   # quiet: one line per error only
        if args and str(args[1] if len(args) > 1 else "").startswith("5"):
            sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))

    # ---- replies
    def send_json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")   # no other site may embed it
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, untrusted: bool = False) -> None:
        stat = path.stat()
        etag = f'"{stat.st_mtime_ns:x}-{stat.st_size:x}"'
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(path.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(stat.st_size))
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")   # no other site may embed it
        if untrusted:   # an image from the notes: never let it run as a page
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; sandbox")
        self.end_headers()
        with open(path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def read_body(self, limit: int) -> bytes:
        self.body_read = True
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            raise HttpError(411, "Content-Length is required") from None
        if length < 0:
            raise HttpError(400, "bad Content-Length")
        if length > limit:
            self.body_read = False
            raise HttpError(413, "image over 20 MB" if limit == MAX_UPLOAD else "request too large")
        return self.rfile.read(length)

    def linger(self) -> None:
        """After refusing a request whose body was never read, let the client
        finish sending before the socket closes. Closing with unread data
        resets the connection, and the client would lose the reply."""
        try:
            self.wfile.flush()
            self.connection.shutdown(socket.SHUT_WR)
            self.connection.settimeout(0.5)
            end, left = time.time() + 2, MAX_UPLOAD + MAX_JSON
            while left > 0 and time.time() < end:
                got = self.connection.recv(65536)
                if not got:
                    break
                left -= len(got)
        except OSError:
            pass

    def read_json(self):
        try:
            return json.loads(self.read_body(MAX_JSON).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise HttpError(400, "the request body is not JSON") from None

    # ---- the local-only guard
    def guard(self, path: str) -> dict | None:
        """Refuse anything a web page on another origin could send.

        The chat endpoint runs Claude Code in the study folder, so a
        cross-site request must never reach it: the Host must be ours (blocks
        DNS rebinding), a present Origin must be ours, and every write needs a
        custom header (which a cross-site form or no-cors fetch cannot set).
        """
        allowed = self.server.allowed_hosts
        if self.headers.get("Host", "") not in allowed:
            return {"error": "bad host"}
        if path.startswith("/api/"):
            origin = self.headers.get("Origin")
            if origin and origin not in {"http://" + h for h in allowed}:
                return {"error": "bad origin"}
            if self.command != "GET" and self.headers.get("X-Study-Desk") != "1":
                return {"error": "missing header"}
        return None

    def handle_request(self) -> None:
        url = urlsplit(self.path)
        path = url.path
        self.body_read = False
        try:
            self.dispatch(url, path)
        finally:
            if not self.body_read and self.headers.get("Content-Length", "0").strip() not in ("", "0"):
                self.linger()

    def dispatch(self, url, path: str) -> None:
        try:
            refused = self.guard(path)
            if refused:
                self.send_json(refused, 403)
                return
            query = {k: v[-1] for k, v in parse_qs(url.query).items()}
            if path.startswith("/api/"):
                self.api(path, query)
            elif self.command == "GET":
                target = resolve_static(path)
                if target is None:
                    raise HttpError(404, "not found")
                self.send_file(target)
            else:
                raise HttpError(405, "method not allowed")
        except HttpError as e:
            self.send_json({"detail": e.detail}, e.status)
        except (BrokenPipeError, ConnectionError):
            pass
        except Exception as e:  # never a traceback page
            try:
                self.send_json({"detail": f"{type(e).__name__}: {e}"}, 500)
            except OSError:
                pass

    do_GET = do_POST = do_PUT = handle_request

    # ---- routes
    def api(self, path: str, query: dict) -> None:
        desk, method = self.desk, self.command
        parts = [unquote(p) for p in path.split("/")[2:]]
        route = (method, parts[0] if parts else "")
        if route == ("GET", "health") and len(parts) == 1:
            self.send_json({"ok": True, "app": "study-desk", "folder": str(desk.folder)})
        elif route == ("GET", "config") and len(parts) == 1:
            lay = desk.layout(wait=90)
            self.send_json({
                "tabs": lay["tabs"], "folder": str(desk.folder), "root": str(lay["root"]),
                "library": str(lay["library"]) if lay["library"] else None, "frontend": lay["frontend"],
                "error": lay["error"], "ready": desk.layout_ready.is_set(), "port": desk.port,
                "permission_mode": desk.permission_mode, "data": str(desk.data),
            })
        elif route == ("GET", "overview") and len(parts) == 1:
            self.send_json(desk.overview.get(force=query.get("refresh") not in (None, "", "0")))
        elif route == ("GET", "note") and len(parts) == 1:
            if not query.get("name"):
                raise HttpError(400, "name is required")
            self.send_json(desk.note(query["name"], query.get("course") or None))
        elif route == ("GET", "asset") and len(parts) == 1:
            self.send_file(desk.asset(query.get("name", "")), untrusted=True)
        elif route == ("GET", "settings") and len(parts) == 1:
            self.send_json(desk.get_settings())
        elif route == ("PUT", "settings") and len(parts) == 1:
            desk.put_settings(self.read_json())
            self.send_json({"ok": True})
        elif route == ("GET", "usage") and len(parts) == 1:
            self.send_json({"rate": desk.tutor.rate, "totals": desk.tutor.totals})
        elif route == ("POST", "upload") and len(parts) == 1:
            ext = desk.UPLOAD_EXT.get(self.headers.get("Content-Type", "").split(";")[0].strip().lower())
            if ext is None:
                raise HttpError(415, "PNG, JPEG, WebP or GIF only")
            self.send_json({"path": str(desk.save_upload(ext, self.read_body(MAX_UPLOAD)))})
        elif route == ("POST", "window-icon") and len(parts) == 1:
            # Called by the page after it loads: swap the scaled-up favicon for the real icon.
            changed = 0
            if sys.platform == "win32":
                from . import winicon
                changed = winicon.apply()
            self.send_json({"windows": changed})
        elif route == ("POST", "shutdown") and len(parts) == 1:
            self.send_json({"ok": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        elif route == ("POST", "chat") and len(parts) in (2, 3):
            tab = desk.tab(parts[1])["id"]
            if len(parts) == 2:
                self.chat(tab)
            elif parts[2] == "stop":
                self.send_json({"stopped": desk.tutor.stop(tab)})
            elif parts[2] == "reset":
                desk.tutor.reset(tab)
                self.send_json({"ok": True})
            else:
                raise HttpError(404, "not found")
        else:
            raise HttpError(404, "not found")

    def chat(self, tab: str) -> None:
        """Stream the tutor's reply as Server-Sent Events, flushed line by line."""
        body = self.read_json()
        text = self.desk.chat_text(body)
        events = self.desk.tutor.stream(tab, text, str(body.get("model", "")), str(body.get("effort", "")))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            for chunk in events:
                self.wfile.write(chunk.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionError, OSError):
            pass            # the browser went away
        finally:
            events.close()  # runs the stream's clean-up, which stops an unfinished turn


class DeskServer(ThreadingHTTPServer):
    daemon_threads = True
    # On Windows SO_REUSEADDR would let a second server share the port.
    allow_reuse_address = os.name != "nt"

    def __init__(self, desk: Desk, port: int | None = None) -> None:
        super().__init__(("127.0.0.1", desk.port if port is None else port), Handler)
        self.desk = desk
        desk.port = self.server_address[1]
        self.allowed_hosts = {f"127.0.0.1:{desk.port}", f"localhost:{desk.port}"}

    def handle_error(self, request, client_address):   # a dropped connection is not news
        if not isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            super().handle_error(request, client_address)
