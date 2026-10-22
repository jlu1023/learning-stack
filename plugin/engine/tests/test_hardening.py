"""Bad input gives a JSON error on stdout (exit 2), never a traceback, and the
engine recovers from the small mistakes notes and logs are likely to hold."""
import datetime as dt
import json

import pytest

from vault_learning import cli
from vault_learning.state import PROGRESS_REL
from vault_learning.vault import Vault

from .conftest import write


def _run(capsys, *argv) -> tuple[int, dict]:
    code = cli.main(list(argv))
    out = capsys.readouterr()
    assert "Traceback" not in out.err
    return code, json.loads(out.out)


def test_a_broken_settings_file_is_a_clear_error(vault, capsys):
    write(vault, "vault-learning.yaml", "reference_courses: [PRE100\n")
    code, out = _run(capsys, "--vault", str(vault), "due", "mixed")
    assert code == 2 and "vault-learning.yaml" in out["error"]


def test_an_unknown_course_is_named_with_the_known_ones(vault, capsys):
    for cmd in (["graph", "NOPE"], ["next", "nope"], ["unit", "NOPE"], ["due", "NOPE"]):
        code, out = _run(capsys, "--vault", str(vault), *cmd)
        assert code == 2 and "NOPE" in out["error"] and out["courses"] == ["XX201"], cmd


def test_note_lookups_fail_as_json_on_stdout(vault, capsys):
    code, out = _run(capsys, "--vault", str(vault), "show", "Nowhere Note")
    assert code == 2 and out["matches"] == []
    code, out = _run(capsys, "--vault", str(vault), "unit", "XX201", "seven")
    assert code == 2 and "unit must be" in out["error"]


def test_a_bad_date_option_is_a_clear_error(vault, capsys):
    code, out = _run(capsys, "--vault", str(vault), "--date", "22/10/2026", "due")
    assert code == 2 and "22/10/2026" in out["error"]


def test_malformed_error_log_dates_are_reported_not_fatal(vault, capsys):
    write(vault, "Courses/_learning/Error Log.md",
          "# Error Log\n\n"
          "- [date:: 2025-09-21] [course:: XX201] [node:: Alpha] [category:: logic] [redo:: soon] x\n"
          "- [date:: 2025-09-21] [course:: XX201] [node:: Beta] [category:: logic] [redo:: 2025-09-24] y\n")
    code, out = _run(capsys, "--vault", str(vault), "--date", "2025-10-01", "due", "mixed")
    assert code == 0 and [r["node"] for r in out["redos"]] == ["Beta"]
    assert out["error_log_problems"] == ["Alpha: redo date 'soon' is not YYYY-MM-DD"]


def test_record_creates_a_missing_progress_store(vault):
    write(vault, "Courses/XX201/1 Basics/Alpha.md",
          "---\ntype: definition\ncourse: XX201\nhuman_authored: true\n---\n# Alpha\n")
    v = Vault(vault)
    assert not (vault / PROGRESS_REL).exists()
    out = cli.record_json(v, "Alpha", "pass", dt.date(2025, 10, 1))
    assert out["written_to"] == "progress"
    text = (vault / PROGRESS_REL).read_text(encoding="utf-8")
    assert "| Alpha | Courses/XX201/1 Basics/Alpha.md | learning |" in text


def test_a_write_outside_the_vault_is_a_clear_error(vault, capsys, monkeypatch):
    def escape(self, rel, text):
        raise PermissionError("refusing to write outside the vault")
    monkeypatch.setattr(Vault, "write_text", escape)
    code, out = _run(capsys, "--vault", str(vault), "--date", "2025-10-01", "record", "Alpha", "--result", "pass")
    assert code == 2 and "refusing to write" in out["error"]


def test_doctor_survives_a_broken_pointer_file(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("VAULT_ROOT", raising=False)
    monkeypatch.delenv("LEARN_STATE_DIR", raising=False)
    write(tmp_path, "vault-learning.yaml", "state_dir: [unclosed\n")
    monkeypatch.chdir(tmp_path)
    code, out = _run(capsys, "doctor")
    assert code == 0 and "vault-learning.yaml" in out["folder"]["problem"]


@pytest.mark.parametrize("bad", [b"\xff\xfe not utf-8 \x81", b"---\ntype: definition\n---\n\x81\x82"])
def test_a_note_that_is_not_utf8_does_not_stop_the_scan(vault, bad):
    (vault / "Courses/XX201/1 Basics/Odd.md").write_bytes(bad)
    Vault(vault)                                       # scanning tolerates it
