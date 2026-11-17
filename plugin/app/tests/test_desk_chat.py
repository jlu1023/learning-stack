"""The tutor: the command line it builds, the stream parser, and a whole chat
turn through the HTTP stream against a stand-in `claude` (never the real one)."""
import json
import threading
import time
from pathlib import Path

import pytest

from conftest import FAKE_CLAUDE, HEADER, finish, start
from studydesk import server as desk_server
from studydesk.server import SYSTEM_NOTE, parse_line, tool_summary


# ---------------------------------------------------------------- parser
def test_stream_parser():
    line = json.dumps
    assert parse_line(line({"type": "system", "subtype": "init", "session_id": "s1"}), False) == [{"t": "session", "id": "s1"}]
    delta = {"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "hi $x$"}}}
    assert parse_line(line(delta), False) == [{"t": "text", "d": "hi $x$"}]
    start_text = {"type": "stream_event", "event": {"type": "content_block_start", "content_block": {"type": "text"}}}
    assert parse_line(line(start_text), False) == [{"t": "phase", "p": "writing"}]
    assert parse_line(line(start_text), True) == [{"t": "phase", "p": "writing"}, {"t": "text", "d": "\n\n"}]
    think = {"type": "stream_event", "event": {"type": "content_block_start", "content_block": {"type": "thinking"}}}
    assert parse_line(line(think), False) == [{"t": "phase", "p": "thinking"}]
    assert parse_line(line({"type": "system", "subtype": "thinking_tokens", "estimated_tokens": 313}), False) == [{"t": "thinking", "tokens": 313}]
    tool = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {
        "command": 'cd x && py -3 "plugin/engine/vl.py" record "Open Ball" --result pass'}}]}}
    assert parse_line(line(tool), True) == [{"t": "tool", "summary": 'engine: record "Open Ball" --result pass'}]
    rate = {"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {"five_hour": {"utilization": 0.5}}}}
    assert parse_line(line(rate), True) == [{"t": "rate", "info": rate["rate_limit_info"]}]
    result = {"type": "result", "subtype": "success", "total_cost_usd": 0.5,
              "usage": {"output_tokens": 200, "iterations": [{"input_tokens": 2, "cache_read_input_tokens": 38000}]}}
    assert parse_line(line(result), True) == [{"t": "done", "output_tokens": 200, "context_tokens": 38002, "cost_usd": 0.5}]
    failed = {"type": "result", "subtype": "error_during_execution", "is_error": True}
    assert parse_line(line(failed), True)[0]["error"] == "error_during_execution"
    for junk in ("not json", "[1, 2]", '"text"', "{}", line({"type": "stream_event"}), line({"type": "assistant"})):
        assert parse_line(junk, False) == []


def test_tool_summaries_are_short_and_name_the_file_only():
    assert tool_summary("Read", {"file_path": "some\\long\\path\\Alpha.md"}) == "Read: Alpha.md"
    assert tool_summary("Grep", {"pattern": "limit"}) == "Grep: limit"
    assert tool_summary("PowerShell", {"command": "py -3 vl.py due mixed"}) == "engine: due mixed"
    assert tool_summary("Bash", {"command": "ls\n-la"}) == "ls -la"
    assert tool_summary("Other", {}) == "Other" and len(tool_summary("Bash", {"command": "x" * 500})) == 160


# ---------------------------------------------------------------- command line
def test_tutor_command_resumes_and_blocks_askuserquestion(running, client):
    client.get_json("/api/config")
    tutor = running.desk.tutor
    cmd = tutor.command("XX201")
    assert cmd[:2] == running.desk.claude_argv() and "-p" in cmd
    for flag in ("--input-format", "--output-format"):
        assert cmd[cmd.index(flag) + 1] == "stream-json"
    assert "--verbose" in cmd and "--include-partial-messages" in cmd
    assert "--resume" not in cmd and cmd[cmd.index("--disallowedTools") + 1] == "AskUserQuestion"
    assert cmd[cmd.index("--add-dir") + 1] == str(running.desk.uploads)
    note = cmd[cmd.index("--append-system-prompt") + 1]
    assert "XX201 compartment" in note and "unless the user asks otherwise" in note
    assert "compartment" not in tutor.command("General")[tutor.command("General").index("--append-system-prompt") + 1]
    tutor.sessions["XX201"] = "abc"
    assert tutor.command("XX201")[-2:] == ["--resume", "abc"]


def test_the_system_note_is_generic_and_keeps_its_instructions():
    for needed in ("$...$", "$$...$$", "LaTeX", "[[Note Name]]", "clickable", "AskUserQuestion does not exist here",
                   "plain text", "wait for the user's typed reply", "the method skill"):
        assert needed in SYSTEM_NOTE, needed
    # safe to pass through a Windows command shim: no quote or percent characters, one line
    assert not set('"%\r\n') & set(SYSTEM_NOTE)


def test_model_and_effort_are_allow_listed(running, client):
    tutor = running.desk.tutor
    cmd = tutor.command("General", "haiku", "low")
    assert cmd[cmd.index("--model") + 1] == "haiku" and cmd[cmd.index("--effort") + 1] == "low"
    cmd = tutor.command("General", "--dangerously-skip-permissions", "; rm")
    assert "--model" not in cmd and "--effort" not in cmd and "; rm" not in cmd
    assert "--dangerously-skip-permissions" not in cmd


def test_permission_mode_defaults_to_auto_and_is_checked(running, vault, tmp_path):
    cmd = running.desk.tutor.command("General")
    assert cmd[cmd.index("--permission-mode") + 1] == "auto"
    r = start(vault, tmp_path / "data2", permission_mode="acceptEdits", model="sonnet")
    try:
        r.desk.claude_argv = lambda: ["claude"]
        cmd = r.desk.tutor.command("General")
        assert cmd[cmd.index("--permission-mode") + 1] == "acceptEdits" and cmd[cmd.index("--model") + 1] == "sonnet"
    finally:
        finish(r)
    for bad in ("bypassPermissions", "anything", ""):
        with pytest.raises(ValueError):
            desk_server.Desk(vault, tmp_path / "data3", permission_mode=bad)
    with pytest.raises(ValueError):
        desk_server.Desk(vault, tmp_path / "data3", model="--dangerously-skip-permissions x")


def test_a_missing_claude_command_is_said_plainly(vault, tmp_path, monkeypatch):
    monkeypatch.delenv("STUDY_DESK_CLAUDE", raising=False)
    monkeypatch.setattr(desk_server.shutil, "which", lambda name: None)
    r = start(vault, tmp_path / "data")
    try:
        events = r.client.chat("General", "hello")
        assert events[-1]["t"] == "error" and "not on PATH" in events[-1]["msg"]
        assert not r.desk.tutor.busy
    finally:
        finish(r)


# ---------------------------------------------------------------- a whole turn
def text_of(events) -> str:
    return "".join(e["d"] for e in events if e["t"] == "text")


def field(events, name: str) -> str:
    return text_of(events).split(f"{name}=", 1)[1].split(" ", 1)[0]


def test_chat_streams_a_reply_from_the_tutor(running, client, vault, tmp_path):
    client.get_json("/api/config")
    events = client.chat("XX201", "hello there")
    kinds = [e["t"] for e in events]
    assert kinds == ["phase", "thinking", "phase", "text", "tool", "rate", "done"]
    assert "session" not in kinds                      # the session id stays on the server
    assert [e["p"] for e in events if e["t"] == "phase"] == ["thinking", "writing"]
    assert "echo=hello there $x^2$" in text_of(events) and field(events, "resumed") == "no"
    assert Path(text_of(events).split("cwd=", 1)[1].split(" echo=", 1)[0]) == vault.resolve()   # runs in the study folder
    assert events[4]["summary"] == 'engine: record "Alpha" --result pass'
    done = events[-1]
    assert done["output_tokens"] == 20 and done["context_tokens"] == 302 and done["totals"]["turns"] == 1

    # the limits are kept for the status line, and survive a restart
    usage = client.get_json("/api/usage")
    assert usage["rate"]["unifiedWindows"]["five_hour"]["utilization"] == 0.25
    assert usage["totals"]["XX201"]["output_tokens"] == 20
    assert json.loads((tmp_path / "data" / "usage.json").read_text(encoding="utf-8")) == usage["rate"]
    assert desk_server.Tutor(running.desk).rate == usage["rate"]


def test_one_process_per_tab_stays_open_and_resumes_after_a_stop(running, client):
    client.get_json("/api/config")
    first = client.chat("XX201", "one")
    second = client.chat("XX201", "two")
    assert field(first, "pid") == field(second, "pid")          # the same long-lived process
    assert second[-1]["totals"]["turns"] == 2
    other = client.chat("General", "three")
    assert field(other, "pid") != field(first, "pid")            # each tab has its own
    assert set(running.desk.tutor.procs) == {"XX201", "General"}

    status, _, body = client.post("/api/chat/XX201/stop", headers=HEADER)
    assert status == 200 and json.loads(body) == {"stopped": True}
    assert json.loads(client.post("/api/chat/XX201/stop", headers=HEADER)[2]) == {"stopped": False}
    third = client.chat("XX201", "four")
    assert field(third, "pid") != field(first, "pid")
    assert field(third, "resumed") == f"fake-{field(first, 'pid')}"   # a new process, the same conversation

    assert client.post("/api/chat/XX201/reset", headers=HEADER)[0] == 200
    fresh = client.chat("XX201", "five")
    assert field(fresh, "resumed") == "no" and fresh[-1]["totals"]["turns"] == 1


def test_a_changed_model_replaces_the_process_and_keeps_the_conversation(running, client):
    client.get_json("/api/config")
    first = client.chat("General", "one")
    second = client.chat("General", "two", model="haiku", effort="low")
    assert field(second, "pid") != field(first, "pid") and field(second, "resumed") == f"fake-{field(first, 'pid')}"


def test_idle_processes_are_closed_when_another_tab_is_used(running, client):
    client.get_json("/api/config")
    client.chat("XX201", "one")
    proc = running.desk.tutor.procs["XX201"]["proc"]
    running.desk.tutor.procs["XX201"]["used"] -= desk_server.IDLE_SECONDS + 1
    client.chat("General", "two")
    assert "XX201" not in running.desk.tutor.procs and proc.poll() is not None
    assert running.desk.tutor.sessions["XX201"]                   # it can still resume


def test_stopping_mid_reply_ends_the_stream_and_the_process(running, client):
    client.get_json("/api/config")
    got = {}
    worker = threading.Thread(target=lambda: got.update(events=client.chat("XX201", "slow please")))
    worker.start()
    end = time.time() + 30
    while "XX201" not in running.desk.tutor.procs and time.time() < end:
        time.sleep(0.05)
    proc = running.desk.tutor.procs["XX201"]["proc"]

    busy = client.chat("XX201", "again")                          # one turn at a time per tab
    assert busy == [{"t": "error", "msg": "This tab is still answering. Press Esc to stop it first."}]

    assert json.loads(client.post("/api/chat/XX201/stop", headers=HEADER)[2]) == {"stopped": True}
    worker.join(timeout=30)
    assert not worker.is_alive()
    assert got["events"][-1] == {"t": "error", "msg": "Stopped before finishing."}
    assert proc.poll() is not None and not running.desk.tutor.busy


def test_attached_photos_are_named_to_the_tutor(running, client):
    client.get_json("/api/config")
    _, _, body = client.post("/api/upload", body=b"\x89PNG", headers={**HEADER, "Content-Type": "image/png"})
    path = json.loads(body)["path"]
    events = client.chat("General", "see this", images=[path])
    assert f"read this image file: {path}" in text_of(events)


def test_closing_the_desk_stops_every_tutor_process(running, client):
    client.get_json("/api/config")
    client.chat("XX201", "one")
    client.chat("General", "two")
    procs = [live["proc"] for live in running.desk.tutor.procs.values()]
    running.desk.close()
    assert len(procs) == 2 and all(p.poll() is not None for p in procs)


def test_the_stand_in_is_what_the_tests_run(running):
    assert running.desk.claude_argv()[1] == str(FAKE_CLAUDE)
