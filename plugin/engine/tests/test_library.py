"""Library mode: a read-only folder of the learner's own notes, with cards and
state kept in a separate state folder."""
import hashlib
import os
from pathlib import Path

import pytest

from vault_learning import config
from vault_learning.cli import due_items, main, record_json
from vault_learning.convert import file_hash
from vault_learning.graph import CourseGraph
from vault_learning.library import connect, integrity_flag, scan
from vault_learning.vault import Vault, resolve_root

from .conftest import write


def _library(root: Path) -> Path:
    """Any structure: nested folders, Markdown, a PDF, a problem sheet."""
    lib = root / "My Notes"
    write(lib, "Term 1/Probability/week 1 - axioms.md", "# Axioms\n\nP(Omega) = 1 and countable additivity.\n")
    write(lib, "Term 1/Probability/week 2 conditional.md", "# Conditional probability\n\nP(A|B) = P(A and B)/P(B).\n")
    write(lib, "Term 1/Problem Sheet 1.md", "# Sheet 1\n\n1. Show that P(empty set) = 0. [3 marks]\n")
    write(lib, "random/ideas.txt", "Answer all questions. Time allowed: 2 hours.\n")
    (lib / "Term 1" / "Probability" / "slides.pdf").write_bytes(
        (Path(__file__).parent / "fixtures" / "sample-lecture.pdf").read_bytes())
    return lib


def _digest(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file() and "_learn" not in p.parts}


def _card(state: Path, lib: Path, name: str, source: str, answer: str = "A short answer.", **extra) -> None:
    h = file_hash(lib / source)
    fields = "".join(f"{k}: {v}\n" for k, v in extra.items())
    write(state, f"Courses/NOTES/1 Probability/{name}.md",
          f"---\ntype: card\ncourse: NOTES\nsource: \"{source}\"\nsource_hash: {h}\n{fields}---\n"
          f"# {name}\n\n## Prompt\nState it.\n\n## Answer\n{answer}\n")
    write(state, "Courses/NOTES/NOTES Syllabus.md", "---\ntype: moc\ncourse: NOTES\n---\n# NOTES\n")


def test_connect_creates_state_inside_library_and_never_touches_notes(tmp_path):
    lib = _library(tmp_path)
    before = _digest(lib)
    out = connect(lib, lib / "_learn")
    assert out["inside_library"] and "vault-learning.yaml" in out["created"]
    assert (lib / "_learn" / "Courses" / "_learning" / "Error Log.md").exists()
    assert _digest(lib) == before
    assert connect(lib, lib / "_learn")["created"] == []            # idempotent


def test_root_resolution_finds_learn_folder_pointer_and_state_dir(tmp_path, monkeypatch):
    lib = _library(tmp_path)
    connect(lib, lib / "_learn")
    monkeypatch.delenv("LEARN_STATE_DIR", raising=False)
    monkeypatch.delenv("VAULT_ROOT", raising=False)
    monkeypatch.chdir(lib)
    assert resolve_root() == Path("_learn").resolve() or resolve_root().name == "_learn"
    outside = tmp_path / "state elsewhere"
    connect(lib, outside)
    assert resolve_root(state_dir=str(outside)) == outside
    monkeypatch.setenv("LEARN_STATE_DIR", str(outside))
    assert resolve_root() == outside
    monkeypatch.delenv("LEARN_STATE_DIR")
    other = tmp_path / "synced"
    write(other, "vault-learning.yaml", "state_dir: ../state elsewhere\n")
    monkeypatch.chdir(other)
    assert resolve_root() == outside.resolve()


def test_state_dir_outside_library_stores_absolute_library(tmp_path):
    lib = _library(tmp_path)
    out = connect(lib, tmp_path / "study state")
    assert not out["inside_library"]
    Vault(tmp_path / "study state")
    assert config.SETTINGS["library"] == lib.resolve()


def test_write_guard_refuses_paths_outside_the_state_folder(tmp_path):
    lib = _library(tmp_path)
    connect(lib, lib / "_learn")
    v = Vault(lib / "_learn")
    with pytest.raises(PermissionError):
        v.write_text("../Term 1/Problem Sheet 1.md", "overwritten")
    assert "Sheet 1" in (lib / "Term 1" / "Problem Sheet 1.md").read_text(encoding="utf-8")


def test_scan_reports_new_changed_current_orphans_and_integrity(tmp_path):
    lib = _library(tmp_path)
    state = lib / "_learn"
    connect(lib, state)
    _card(state, lib, "Axioms of Probability", "Term 1/Probability/week 1 - axioms.md")
    _card(state, lib, "Conditional Probability", "Term 1/Probability/week 2 conditional.md")
    _card(state, lib, "Sheet 1 Question 1", "Term 1/Problem Sheet 1.md", answer="Attempt it first.",
          cite_only="true")
    _card(state, lib, "Leaked Solution", "Term 1/Problem Sheet 1.md", answer="Since P(A) = P(A) + P(empty)...")
    write(state, "Courses/NOTES/1 Probability/Gone.md",
          "---\ntype: card\ncourse: NOTES\nsource: \"deleted.md\"\n---\n# Gone\n")
    (lib / "Term 1" / "Probability" / "week 2 conditional.md").write_text("# Changed\n", encoding="utf-8")
    out = scan(Vault(state))
    by = {f["file"]: f for f in out["files"]}
    assert by["Term 1/Probability/week 1 - axioms.md"]["status"] == "current"
    assert by["Term 1/Probability/week 2 conditional.md"]["status"] == "changed"
    assert by["Term 1/Probability/slides.pdf"]["status"] == "new"
    assert not any("_learn" in f for f in by)                       # the state folder is not library content
    flagged = {f["file"] for f in out["integrity_flags"]}
    assert {"Term 1/Problem Sheet 1.md", "random/ideas.txt"} <= flagged
    assert [x["card"].rsplit("/", 1)[-1] for x in out["integrity_violations"]] == ["Leaked Solution.md"]
    assert out["orphan_cards"][0]["source"] == "deleted.md"
    assert by["Term 1/Probability/slides.pdf"]["href_from_state"] == "../Term%201/Probability/slides.pdf"


def test_integrity_flag_by_name_and_by_text(tmp_path):
    p = tmp_path / "notes.md"
    p.write_text("Lecture notes on limits.\n", encoding="utf-8")
    assert integrity_flag(p, "Lecture 3.md") is None
    assert "file name" in integrity_flag(p, "2024 Past Paper.pdf")
    p.write_text("Candidates should answer all questions. [20 marks]\n", encoding="utf-8")
    assert "opening text" in integrity_flag(p, "misc.md")


def test_cards_are_nodes_with_the_same_review_ladder(tmp_path):
    import datetime as dt
    lib = _library(tmp_path)
    state = lib / "_learn"
    connect(lib, state)
    _card(state, lib, "Axioms of Probability", "Term 1/Probability/week 1 - axioms.md")
    v = Vault(state)
    assert [Path(n).stem for n in CourseGraph(v, "NOTES").nodes] == ["Axioms of Probability"]
    d0 = dt.date(2025, 1, 6)
    assert record_json(v, "Axioms of Probability", "pass", d0)["after"]["review_interval"] == 1
    assert due_items(Vault(state), "mixed", d0 + dt.timedelta(days=1), 0)["due"][0]["name"] == "Axioms of Probability"
    assert record_json(Vault(state), "Axioms of Probability", "pass", d0 + dt.timedelta(days=1))["after"]["review_interval"] == 3


def test_cli_connect_and_scan(tmp_path, capsys, monkeypatch):
    lib = _library(tmp_path)
    monkeypatch.chdir(lib)
    monkeypatch.delenv("VAULT_ROOT", raising=False)
    monkeypatch.delenv("LEARN_STATE_DIR", raising=False)
    assert main(["connect", "."]) == 0
    assert main(["library-scan"]) == 0
    assert '"new": 5' in capsys.readouterr().out
