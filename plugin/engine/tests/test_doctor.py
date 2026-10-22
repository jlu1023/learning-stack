"""`doctor`: what the engine has and what each optional extra adds."""
from vault_learning.cli import doctor_json
from vault_learning.library import connect

from .conftest import write


def test_doctor_in_a_vault_a_library_and_an_empty_folder(vault, tmp_path, monkeypatch):
    monkeypatch.delenv("VAULT_ROOT", raising=False)
    monkeypatch.delenv("LEARN_STATE_DIR", raising=False)
    monkeypatch.chdir(vault)
    d = doctor_json()
    assert d["python"]["ok"] and d["folder"]["looks_like"] == "vault"
    assert {o["name"] for o in d["optional"]} == {"PyYAML", "mermaid-cli"}
    assert all(o["install"] and o["adds"] for o in d["optional"])
    lib = tmp_path / "notes"
    write(lib, "a.md", "# A\n")
    connect(lib, lib / "_learn")
    monkeypatch.chdir(lib)
    assert doctor_json()["folder"]["looks_like"] == "library state"
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(empty)
    assert doctor_json()["folder"]["looks_like"].startswith("neither")
