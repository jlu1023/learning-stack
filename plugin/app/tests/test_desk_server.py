"""The server's own behaviour: the local-only guard, notes, settings, uploads,
static files, tabs from the engine's courses, and the dashboard."""
import json
import re
import sys
import time
from pathlib import Path

import pytest

from conftest import APP, HEADER, STUB_ENGINE, finish, make_vault, start, write
from studydesk import server as desk_server
from studydesk.server import PALETTE, build_tabs, default_data_dir, resolve_static


def wait_for_overview(client, timeout: float = 60) -> dict:
    end = time.time() + timeout
    while time.time() < end:
        data = client.get_json("/api/overview")
        if not data["loading"] and "built" in data:
            return data
        time.sleep(0.1)
    raise AssertionError("the overview never finished building")


# ---------------------------------------------------------------- guard
def test_writes_need_the_header_and_our_origin(client):
    body = {"size": 18}
    assert client.put("/api/settings", json_body=body)[0] == 403
    assert client.put("/api/settings", json_body=body, headers={**HEADER, "Origin": "https://evil.example"})[0] == 403
    assert client.post("/api/chat/XX201", json_body={"text": "hi"}, headers={"Origin": "https://evil.example"})[0] == 403
    assert client.post("/api/shutdown")[0] == 403
    assert client.get("/api/health", headers={"Host": "evil.example"})[0] == 403
    assert client.get("/", headers={"Host": "evil.example"})[0] == 403
    ours = {**HEADER, "Origin": f"http://{client.host}"}
    assert client.put("/api/settings", json_body=body, headers=ours)[0] == 200
    assert client.get_json("/api/settings") == body
    assert client.put("/api/settings", json_body=body, headers={**HEADER, "Host": f"localhost:{client.port}"})[0] == 200


def test_health_names_the_app_and_its_folder(running, client, vault):
    assert client.get_json("/api/health") == {"ok": True, "app": "study-desk", "folder": str(vault.resolve())}


def test_other_methods_and_unknown_routes_are_refused(client):
    assert client.request("DELETE", "/api/settings", headers=HEADER)[0] == 501
    assert client.request("OPTIONS", "/api/chat/XX201", headers={"Origin": "https://evil.example"})[0] == 501
    assert client.get("/api/nothing")[0] == 404
    assert client.post("/app.js", headers=HEADER)[0] == 405


# ---------------------------------------------------------------- notes
def test_note_lookup_prefers_the_tabs_course(client):
    assert client.get_json("/api/config")["ready"]
    assert client.get_json("/api/note?name=Limit&course=YY202")["markdown"] == "---\ntype: definition\ncourse: YY202\n---\nmetric limit\n"
    note = client.get_json("/api/note?name=limit&course=XX201")
    assert "x^2" in note["markdown"] and note["path"] == "Courses/XX201/1 Basics/Limit.md"
    assert client.get_json("/api/note?name=Courses/YY202/1%20Spaces/Limit")["name"] == "Limit"


def test_note_lookup_stays_inside_the_notes_folder(client):
    client.get_json("/api/config")
    for name in ("../secret", "..%2Fsecret", "Hidden", ".obsidian/Hidden", "secret"):
        assert client.get(f"/api/note?name={name}")[0] == 404, name
    assert client.get("/api/note")[0] == 400


def test_images_in_the_notes_are_served_but_never_as_pages(client):
    client.get_json("/api/config")
    status, headers, body = client.get("/api/asset?name=sub/Sketch.PNG")
    assert status == 200 and headers["Content-Type"] == "image/png" and body.startswith(b"\x89PNG")
    assert "sandbox" in headers["Content-Security-Policy"]
    assert client.get("/api/asset?name=nothing.png")[0] == 404
    assert client.get("/api/asset?name=..%2F..%2Fsecret.md")[0] == 404


# ---------------------------------------------------------------- settings, uploads
def test_settings_must_be_a_json_object(client):
    assert client.put("/api/settings", body=b"not json", headers=HEADER)[0] == 400
    assert client.put("/api/settings", json_body=[1, 2], headers=HEADER)[0] == 400
    assert client.get_json("/api/settings") == {}


def test_upload_accepts_images_only(running, client):
    assert client.post("/api/upload", body=b"x", headers={**HEADER, "Content-Type": "text/html"})[0] == 415
    status, _, body = client.post("/api/upload", body=b"\x89PNG", headers={**HEADER, "Content-Type": "image/png"})
    path = Path(json.loads(body)["path"])
    assert status == 200 and path.parent == running.desk.uploads and path.read_bytes() == b"\x89PNG"
    too_big = {**HEADER, "Content-Type": "image/png", "Content-Length": str(desk_server.MAX_UPLOAD + 1)}
    assert client.post("/api/upload", body=b"x", headers=too_big)[0] == 413


def test_user_data_stays_in_the_data_folder(running, client, vault, tmp_path):
    before = sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*"))
    client.put("/api/settings", json_body={"size": 18}, headers=HEADER)
    client.post("/api/upload", body=b"\x89PNG", headers={**HEADER, "Content-Type": "image/png"})
    wait_for_overview(client)
    assert sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*")) == before
    assert (tmp_path / "data" / "settings.json").is_file()
    assert not list(APP.glob("settings.json")) and not list(APP.glob("uploads"))


def test_chat_rejects_images_outside_the_upload_folder(client, tmp_path):
    client.get_json("/api/config")
    r = client.post("/api/chat/XX201", json_body={"text": "x", "images": [str(tmp_path / "secret.md")]}, headers=HEADER)
    assert r[0] == 400
    assert client.post("/api/chat/XX201", json_body={"text": "  "}, headers=HEADER)[0] == 400
    assert client.post("/api/chat/NOPE", json_body={"text": "x"}, headers=HEADER)[0] == 404


def test_default_data_folder_is_per_user_on_each_platform():
    home = Path("home-folder")
    assert default_data_dir({"STUDY_DESK_DATA": "elsewhere"}, "linux", home) == Path("elsewhere")
    assert default_data_dir({"LOCALAPPDATA": "local-data"}, "win32", home) == Path("local-data") / "StudyDesk"
    assert default_data_dir({}, "win32", home) == home / "AppData" / "Local" / "StudyDesk"
    assert default_data_dir({}, "darwin", home) == home / "Library" / "Application Support" / "StudyDesk"
    assert default_data_dir({}, "linux", home) == home / ".local" / "share" / "study-desk"
    assert default_data_dir({"XDG_DATA_HOME": "xdg"}, "linux", home) == Path("xdg") / "study-desk"


# ---------------------------------------------------------------- static files
@pytest.mark.parametrize("path", [
    "/../serve.py", "/%2e%2e/serve.py", "/..%2fserve.py", "/..%5cserve.py", "/vendor/../../serve.py",
    "/vendor/..%2f..%2fserve.py", "//etc/passwd", "/C:/Windows/win.ini", "/.hidden", "/vendor/.hidden",
    "/vendor", "/vendor/", "/nothing.js", "/app.js%00.png", "\\app.js", "app.js", "/vendor\\katex.min.js",
])
def test_static_resolver_refuses_anything_but_a_file_under_static(path):
    assert resolve_static(path) is None


def test_static_resolver_finds_the_app_and_its_vendored_files():
    static = APP / "static"
    assert resolve_static("/") == (static / "index.html").resolve()
    assert resolve_static("/app.js") == (static / "app.js").resolve()
    assert resolve_static("/vendor/fonts/KaTeX_Main-Regular.woff2").is_file()
    assert resolve_static("/icon%2D32.png") == (static / "icon-32.png").resolve()


def test_static_resolver_refuses_a_link_that_leaves_the_folder(tmp_path):
    root = tmp_path / "static"
    root.mkdir()
    (root / "ok.txt").write_text("fine", encoding="utf-8")
    (tmp_path / "outside.txt").write_text("secret", encoding="utf-8")
    try:
        (root / "leak.txt").symlink_to(tmp_path / "outside.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are not available here")
    assert resolve_static("/ok.txt", root) == (root / "ok.txt").resolve()
    assert resolve_static("/leak.txt", root) is None


def test_static_files_are_served_with_their_types(client):
    status, headers, body = client.get("/")
    assert status == 200 and headers["Content-Type"].startswith("text/html") and b"<title>Study Desk</title>" in body
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin" and headers["X-Content-Type-Options"] == "nosniff"
    assert client.get("/app.js")[1]["Content-Type"].startswith("text/javascript")
    assert client.get("/vendor/katex.min.css")[1]["Content-Type"].startswith("text/css")
    status, headers, _ = client.get("/vendor/fonts/KaTeX_Main-Regular.woff2")
    assert status == 200 and headers["Content-Type"] == "font/woff2"
    assert client.get("/app.js", headers={"If-None-Match": client.get("/app.js")[1]["ETag"]})[0] == 304
    for path in ("/../serve.py", "/%2e%2e/serve.py", "/..%5cserve.py", "/studydesk/server.py"):
        assert client.get(path)[0] == 404, path


def test_the_page_names_the_plugins_real_commands_and_nothing_else():
    """Command hints must be skills that exist, with the plugin's prefix."""
    skills = {p.parent.name for p in (APP.parent / "skills").glob("*/SKILL.md")}
    pages = "".join((APP / "static" / n).read_text(encoding="utf-8") for n in ("index.html", "app.js"))
    used = set(re.findall(r"/learn:([a-z]+)", pages))
    assert used and used <= skills, used - skills
    assert {"teach", "quiz", "primer", "app"} <= used
    for bare in ("/teach ", "/quiz ", "/primer "):
        assert bare not in pages


# ---------------------------------------------------------------- tabs
def test_tabs_are_the_courses_then_general():
    tabs = build_tabs(["XX201", "YY202"])
    assert [t["id"] for t in tabs] == ["XX201", "YY202", "General"]
    assert [t["course"] for t in tabs] == ["XX201", "YY202", None]
    assert tabs[0]["accent"] == PALETTE[0] and tabs[1]["accent"] == PALETTE[1]
    assert build_tabs([])[0]["id"] == "General" and len(build_tabs([])) == 1


def test_tab_colours_cycle_and_a_course_called_general_keeps_its_tab():
    many = build_tabs([f"C{i}" for i in range(len(PALETTE) + 2)])
    assert many[len(PALETTE)]["accent"] == PALETTE[0] and len({t["id"] for t in many}) == len(many)
    tabs = build_tabs(["General", "XX201", "XX201"])
    assert [t["id"] for t in tabs] == ["General", "XX201", "General tab"]
    assert tabs[0]["course"] == "General" and tabs[-1]["course"] is None


def test_config_takes_its_tabs_from_the_engine(running, client, vault):
    cfg = client.get_json("/api/config")
    assert [t["id"] for t in cfg["tabs"]] == ["XX201", "YY202", "General"]      # PRE100 is a reference course
    assert cfg["ready"] and cfg["error"] is None and cfg["library"] is None
    assert Path(cfg["root"]) == vault.resolve() and cfg["permission_mode"] == "auto" and cfg["frontend"] == "obsidian"
    assert cfg["port"] == client.port


def test_plain_front_end_and_registered_courses_follow_the_settings_file(vault, tmp_path):
    write(vault, "vault-learning.yaml", """
        frontend: plain
        extra_courses:
          Reading:
            root: "Reading/"
        """)
    write(vault, "Reading/Reading Syllabus.md", "---\ntype: moc\n---\n# Reading\n")
    r = start(vault, tmp_path / "data")
    try:
        cfg = r.client.get_json("/api/config")
        assert cfg["frontend"] == "plain"
        assert [t["id"] for t in cfg["tabs"]] == ["PRE100", "XX201", "YY202", "Reading", "General"]
    finally:
        finish(r)


def test_a_connected_library_is_read_alongside_its_state_folder(tmp_path):
    library = tmp_path / "my notes"
    write(library, "week one/Handout.md", "# Handout\n\nA page of notes.\n")
    r = start(library, tmp_path / "data")
    try:
        r.desk.run_engine("connect", str(library), "--frontend", "plain")
        state = library / "_learn"
        write(state, "Courses/PROB/PROB Syllabus.md", "---\ntype: moc\ncourse: PROB\n---\n# PROB\n")
        write(state, "Courses/PROB/1 Week one/Bayes Rule.md", "---\ntype: card\ncourse: PROB\n---\n# Bayes Rule\n")
        cfg = r.client.get_json("/api/config")
        assert Path(cfg["root"]) == state.resolve() and Path(cfg["library"]) == library.resolve()
        assert [t["id"] for t in cfg["tabs"]] == ["PROB", "General"]
        assert r.client.get_json("/api/note?name=Bayes%20Rule")["path"] == "Courses/PROB/1 Week one/Bayes Rule.md"
        assert r.client.get_json("/api/note?name=Handout")["path"] == "week one/Handout.md"
    finally:
        finish(r)


def test_a_folder_that_is_not_set_up_still_opens_with_the_general_tab(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    r = start(empty, tmp_path / "data")
    try:
        cfg = r.client.get_json("/api/config")
        assert [t["id"] for t in cfg["tabs"]] == ["General"] and cfg["error"] is None
        data = wait_for_overview(r.client)
        assert data["courses"] == {} and data["due_total"] == 0
    finally:
        finish(r)


def test_a_broken_settings_file_is_reported_not_fatal(vault, tmp_path):
    write(vault, "vault-learning.yaml", "reference_courses: [PRE100\n")
    r = start(vault, tmp_path / "data")
    try:
        cfg = r.client.get_json("/api/config")
        assert [t["id"] for t in cfg["tabs"]] == ["General"] and "yaml" in cfg["error"].lower()
        assert "yaml" in wait_for_overview(r.client)["errors"]["folder"].lower()
    finally:
        finish(r)


# ---------------------------------------------------------------- overview
def test_overview_is_built_from_the_engine(running, client):
    running.desk.run_engine("--date", "2025-09-02", "record", "Alpha", "--result", "pass")
    data = wait_for_overview(client)
    xx = data["courses"]["XX201"]
    assert data["course_codes"] == ["XX201", "YY202"] and data["errors"] == {}
    assert xx["nodes"] == 2 and xx["levels"] == {"unseen": 1, "learning": 1}
    assert xx["due"] == 1 and xx["due_items"][0]["name"] == "Alpha" and xx["due_items"][0]["overdue_days"] > 0
    assert xx["redos"] == 0 and data["due_total"] == 1
    assert [u["name"] for u in xx["units"]] and xx["units"][0]["nodes"] == 2 and xx["units"][0]["started"] is True
    assert data["courses"]["YY202"]["due"] == 0
    assert data["stats"] is None       # the public engine has no `stats` command: the page shows no retention line


def test_overview_degrades_when_the_engine_lacks_commands(tmp_path):
    folder = tmp_path / "study"
    folder.mkdir()
    r = start(folder, tmp_path / "data", engine=STUB_ENGINE)
    try:
        assert [t["id"] for t in r.client.get_json("/api/config")["tabs"]] == ["ZZ303", "General"]
        data = wait_for_overview(r.client)
        zz = data["courses"]["ZZ303"]
        assert zz["nodes"] == 2 and zz["levels"] == {"secure": 1, "unseen": 1}     # the proof is not counted
        assert zz["units"] is None and zz["due"] is None and zz["redos"] is None
        assert data["due_total"] is None and data["stats"] is None and "due" in data["errors"]
        assert r.desk.overview.stats_supported is False
    finally:
        finish(r)


def test_one_broken_course_does_not_blank_the_page(running, client, monkeypatch):
    real = running.desk.run_engine

    def flaky(*args, **kw):
        if args[:2] == ("graph", "YY202"):
            raise desk_server.EngineError("no such course today")
        return real(*args, **kw)

    monkeypatch.setattr(running.desk, "run_engine", flaky)
    data = wait_for_overview(client)
    assert "XX201" in data["courses"] and data["errors"] == {"YY202": "no such course today"}


def test_engine_errors_arrive_as_their_message(running):
    with pytest.raises(desk_server.EngineError) as e:
        running.desk.run_engine("graph", "NOPE")
    assert "NOPE" in str(e.value) and "Traceback" not in str(e.value)


# ---------------------------------------------------------------- window icon
def test_window_icon_endpoint_is_a_no_op_off_windows(client, monkeypatch):
    from studydesk import winicon
    monkeypatch.setattr(winicon, "apply", lambda title="Study Desk": 0)   # never touch real windows in a test
    monkeypatch.setattr(winicon, "keep", lambda title="Study Desk": False)   # nor start the watcher
    status, _, body = client.post("/api/window-icon", headers=HEADER)
    assert status == 200 and json.loads(body) == {"windows": 0}
    assert client.post("/api/window-icon")[0] == 403


def test_winicon_imports_anywhere_and_does_nothing_off_windows(monkeypatch):
    from studydesk import winicon
    monkeypatch.setattr(sys, "platform", "linux")
    assert winicon.apply() == 0
    assert winicon.keep() is False and winicon._watcher is None
    assert winicon.ICON.is_file()
