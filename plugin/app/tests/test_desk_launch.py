"""The launcher: options, finding a running server, a second launch, stopping."""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import APP, make_vault

import serve


def args(**kw):
    base = dict(folder=None, port=None, permission_mode=None, model=None, data=None)
    return argparse.Namespace(**{**base, **kw})


def test_options_come_from_flags_then_environment_then_the_config_file(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    env = {"STUDY_DESK_DATA": str(data)}
    opts = serve.resolve_options(args(), env)
    assert opts["port"] == 8030 and opts["permission_mode"] == "auto" and opts["model"] == ""
    assert opts["data"] == data and opts["folder"] == Path.cwd().resolve() and not opts["explicit_folder"]

    (data / "config.json").write_text(json.dumps({"port": 8111, "permission_mode": "plan", "model": "sonnet"}), encoding="utf-8")
    opts = serve.resolve_options(args(), env)
    assert (opts["port"], opts["permission_mode"], opts["model"]) == (8111, "plan", "sonnet")

    env.update(STUDY_DESK_PORT="8222", STUDY_DESK_PERMISSION_MODE="acceptEdits", STUDY_DESK_FOLDER=str(tmp_path))
    opts = serve.resolve_options(args(), env)
    assert (opts["port"], opts["permission_mode"]) == (8222, "acceptEdits")
    assert opts["folder"] == tmp_path.resolve() and opts["explicit_folder"]

    opts = serve.resolve_options(args(port=8333, permission_mode="manual", model="opus", folder=str(data)), env)
    assert (opts["port"], opts["permission_mode"], opts["model"], opts["folder"]) == (8333, "manual", "opus", data.resolve())


def test_bad_options_are_refused(tmp_path):
    env = {"STUDY_DESK_DATA": str(tmp_path)}
    for bad in (dict(permission_mode="bypassPermissions"), dict(permission_mode="nonsense"), dict(port=70000)):
        with pytest.raises(ValueError):
            serve.resolve_options(args(**bad), env)
    with pytest.raises(ValueError):
        serve.resolve_options(args(), {**env, "STUDY_DESK_PORT": "eighty"})
    (tmp_path / "config.json").write_text("not json", encoding="utf-8")
    assert serve.resolve_options(args(), env)["port"] == 8030      # an unreadable config file is ignored


def test_health_finds_a_running_study_desk_and_nothing_else(running, client):
    assert serve.health(client.port)["app"] == "study-desk"
    running.server.shutdown()
    running.server.server_close()
    assert serve.health(client.port, timeout=0.5) is None


def test_a_second_launch_only_opens_the_browser(running, client, vault, tmp_path, monkeypatch, capsys):
    opened = []
    monkeypatch.setattr(serve, "open_window", lambda url, mode, data: opened.append((url, mode)))
    monkeypatch.setattr(serve, "start_background", lambda opts: pytest.fail("a second server was started"))
    base = ["--port", str(client.port), "--data", str(tmp_path / "data")]
    assert serve.main(base) == 0
    assert opened == [(f"http://127.0.0.1:{client.port}", "browser")]
    assert "already running" in capsys.readouterr().out
    assert serve.main(base + ["--background", "--folder", str(vault), "--no-browser"]) == 0
    assert opened[-1][1] == "none"

    # a different folder is not silently swapped in
    assert serve.main(base + ["--folder", str(tmp_path)]) == 3
    assert "already running for" in capsys.readouterr().err and len(opened) == 2


def test_stop_asks_the_server_to_shut_down(running, client, tmp_path, capsys):
    base = ["--port", str(client.port), "--data", str(tmp_path / "data"), "--stop"]
    assert serve.main(base) == 0 and "stopped" in capsys.readouterr().out
    end = time.time() + 10
    while serve.health(client.port, timeout=0.5) and time.time() < end:
        time.sleep(0.1)
    assert serve.health(client.port, timeout=0.5) is None
    assert serve.main(base) == 0 and "not running" in capsys.readouterr().out


def test_the_app_browser_is_optional(tmp_path, monkeypatch):
    assert serve.find_app_browser({}, "win32") is None
    exe = tmp_path / "Google" / "Chrome" / "Application" / "chrome.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    assert serve.find_app_browser({"ProgramFiles": str(tmp_path)}, "win32") == str(exe)
    calls = []
    monkeypatch.setattr(serve.webbrowser, "open", lambda url: calls.append(url))
    monkeypatch.setattr(serve, "find_app_browser", lambda: None)
    serve.open_window("http://127.0.0.1:1", "none", tmp_path)
    assert calls == []
    serve.open_window("http://127.0.0.1:1", "app", tmp_path)       # no app browser: the default browser
    serve.open_window("http://127.0.0.1:1", "browser", tmp_path)
    assert calls == ["http://127.0.0.1:1"] * 2


def test_serve_starts_in_the_background_and_stops(tmp_path):
    """The real launcher, as a user runs it: start detached, find it, stop it."""
    vault = make_vault(tmp_path / "study")
    data = tmp_path / "data"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    base = [sys.executable, str(APP / "serve.py"), "--port", str(port), "--data", str(data)]
    env = {k: v for k, v in os.environ.items() if not k.startswith("STUDY_DESK_")}
    run = lambda *extra: subprocess.run([*base, *extra], cwd=str(vault), env=env, capture_output=True,  # noqa: E731
                                        encoding="utf-8", errors="replace", timeout=90)
    try:
        started = run("--background", "--no-browser")
        assert started.returncode == 0, started.stderr + started.stdout
        assert f"http://127.0.0.1:{port}" in started.stdout
        assert Path(serve.health(port)["folder"]) == vault.resolve()        # the current folder is the default
        again = run("--no-browser")
        assert again.returncode == 0 and "already running" in again.stdout
        assert (data / "server.log").is_file() and (data / "uploads").is_dir()
    finally:
        stopped = run("--stop")
    assert stopped.returncode == 0 and "stopped" in stopped.stdout
    end = time.time() + 10
    while serve.health(port, timeout=0.5) and time.time() < end:
        time.sleep(0.1)
    assert serve.health(port, timeout=0.5) is None
