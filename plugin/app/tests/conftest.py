"""Fixtures for the Study Desk tests: a throwaway study folder and data folder,
a server on a free port, and a stand-in for the `claude` command. Nothing here
touches a real notes folder, a real data folder or the real Claude Code CLI."""
import http.client
import json
import sys
import textwrap
import threading
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from studydesk import server as desk_server  # noqa: E402

FAKE_CLAUDE = TESTS / "fake_claude.py"
STUB_ENGINE = TESTS / "stub_engine.py"
HEADER = {"X-Study-Desk": "1"}


def write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
    return p


def make_vault(root: Path) -> Path:
    """Courses XX201 (two notes, one module) and YY202 (one note), a reference
    course, a hidden folder and a duplicate note name across the two courses."""
    write(root, "vault-learning.yaml", "reference_courses: [PRE100]\n")
    for code, title in (("XX201", "Basics"), ("YY202", "Spaces")):
        write(root, f"Courses/{code}/{code} Syllabus.md", f"""
            ---
            title: "{code} Syllabus"
            type: moc
            course: {code}
            ---
            # {code}

            ## Chapters
            - [[1 {title}]]
            """)
        write(root, f"Courses/{code}/1 {title}/1 {title}.md", f"""
            ---
            title: "{title}"
            type: moc
            course: {code}
            ---
            # {title}

            ## Definitions
            - [[Limit]]
            """)
    write(root, "Courses/XX201/1 Basics/Limit.md", """
        ---
        title: Limit
        type: definition
        course: XX201
        ---
        # Limit

        The value $x^2$ approaches. ![[sketch.png]]
        """)
    write(root, "Courses/XX201/1 Basics/Alpha.md", """
        ---
        type: definition
        course: XX201
        depends_on: ["[[Limit]]"]
        ---
        # Alpha
        """)
    write(root, "Courses/YY202/1 Spaces/Limit.md", "---\ntype: definition\ncourse: YY202\n---\nmetric limit\n")
    write(root, "Courses/PRE100/1 Sets/Set.md", "---\ntype: definition\ncourse: PRE100\n---\n# Set\n")
    write(root, "Courses/PRE100/PRE100 Syllabus.md", "---\ntype: moc\ncourse: PRE100\n---\n# PRE100\n")
    (root / "Courses/_learning").mkdir(parents=True)
    (root / "Courses/XX201/1 Basics/sketch.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    write(root, ".obsidian/Hidden.md", "no\n")
    return root


class Client:
    """A tiny HTTP client that sends exactly the headers it is given."""

    def __init__(self, port: int) -> None:
        self.port = port
        self.host = f"127.0.0.1:{port}"

    def request(self, method: str, path: str, body=None, headers=None, json_body=None, timeout: float = 60):
        headers = dict(headers or {})
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        try:
            conn.putrequest(method, path, skip_host=True)
            conn.putheader("Host", headers.pop("Host", self.host))
            if body is not None or method in ("POST", "PUT"):
                headers.setdefault("Content-Length", str(len(body or b"")))
            for k, v in headers.items():
                conn.putheader(k, v)
            conn.endheaders(body if body else None)
            res = conn.getresponse()
            return res.status, dict(res.getheaders()), res.read()
        finally:
            conn.close()

    def get(self, path: str, **kw):
        return self.request("GET", path, **kw)

    def get_json(self, path: str):
        status, _, body = self.get(path)
        assert status == 200, (status, body)
        return json.loads(body)

    def post(self, path: str, **kw):
        return self.request("POST", path, **kw)

    def put(self, path: str, **kw):
        return self.request("PUT", path, **kw)

    def chat(self, tab: str, text: str, **extra) -> list:
        """Send one message and return the reply's events, read to the end."""
        status, headers, body = self.post(f"/api/chat/{tab}", json_body={"text": text, **extra}, headers=HEADER)
        assert status == 200, (status, body)
        assert headers["Content-Type"].startswith("text/event-stream")
        return [json.loads(block[6:]) for block in body.decode("utf-8").split("\n\n") if block.startswith("data: ")]


class Running:
    def __init__(self, desk, server, client) -> None:
        self.desk, self.server, self.client = desk, server, client


def start(folder: Path, data: Path, **options) -> Running:
    desk = desk_server.Desk(folder, data, port=0, **options)
    server = desk_server.DeskServer(desk, port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return Running(desk, server, Client(desk.port))


def finish(running: Running) -> None:
    running.desk.close()
    running.server.shutdown()
    running.server.server_close()


@pytest.fixture()
def vault(tmp_path) -> Path:
    (tmp_path / "secret.md").write_text("outside", encoding="utf-8")
    return make_vault(tmp_path / "study")


@pytest.fixture()
def running(vault, tmp_path, monkeypatch):
    """The app against a throwaway study folder and data folder, with a
    stand-in for the `claude` command."""
    for name in ("VAULT_ROOT", "LEARN_STATE_DIR", "STUDY_DESK_CLAUDE", "STUDY_DESK_DATA"):
        monkeypatch.delenv(name, raising=False)
    r = start(vault, tmp_path / "data")
    monkeypatch.setattr(r.desk, "claude_argv", lambda: [sys.executable, str(FAKE_CLAUDE)])
    yield r
    finish(r)


@pytest.fixture()
def client(running) -> Client:
    return running.client
