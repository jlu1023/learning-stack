"""The Learner Model: dated "held as" lines, read back by `show` and `due`."""
import json

from vault_learning import cli
from vault_learning.state import read_learner_model
from vault_learning.vault import Vault

from .conftest import write

MODEL = "Courses/_learning/Learner Model.md"


def _run(vault, *argv, capsys, date="2025-09-30"):
    rc = cli.main(["--vault", str(vault), "--date", date, *argv])
    return rc, json.loads(capsys.readouterr().out)


def _model(vault):
    write(vault, MODEL, """
        ---
        title: "Learner Model"
        type: reference
        ---
        # Learner Model

        One line per node per session: `- [date:: YYYY-MM-DD] [course:: CODE] [node:: Note Name] Held as: ...`

        ## Entries
        - [date:: 2025-09-28] [course:: XX201] [node:: Alpha] Held as: a picture of boxes.
        - not a model line
        - [date:: 2025-09-29] [course:: XX201] Held as: no node, skipped.
        - [date:: 2025-09-30] [course:: XX201] [node:: Beta] Held as: the alpha, twice.
        - [date:: 2025-09-29] [course:: XX201] [node:: Alpha] Held as: the boxes shrink. Shaky: why they must be disjoint.
        - [date:: 2025-09-30] [course:: XX201] [node:: Alpha] Held as: nested boxes, each inside the last.
        """)


def test_lines_are_grouped_by_node_and_dated_oldest_first(vault):
    _model(vault)
    model = read_learner_model(Vault(vault))
    assert set(model) == {"Alpha", "Beta"}
    assert [x["date"] for x in model["Alpha"]] == ["2025-09-28", "2025-09-29", "2025-09-30"]
    assert model["Alpha"][1]["text"] == "Held as: the boxes shrink. Shaky: why they must be disjoint."


def test_a_missing_learner_model_is_empty_not_an_error(vault, capsys):
    assert read_learner_model(Vault(vault)) == {}
    rc, shown = _run(vault, "show", "Alpha", capsys=capsys)
    assert rc == 0 and shown["held_as"] == []


def test_show_gives_the_newest_two_lines(vault, capsys):
    _model(vault)
    rc, shown = _run(vault, "show", "Alpha", capsys=capsys)
    assert rc == 0
    assert [h["date"] for h in shown["held_as"]] == ["2025-09-29", "2025-09-30"]
    assert shown["held_as"][-1]["text"] == "Held as: nested boxes, each inside the last."


def test_due_gives_each_item_its_newest_line(vault, capsys):
    _model(vault)
    for n in ("Alpha", "Gamma Theorem"):
        _run(vault, "record", n, "--result", "pass", capsys=capsys)
    rc, due = _run(vault, "due", "XX201", capsys=capsys, date="2025-10-02")
    by_name = {i["name"]: i for i in due["due"]}
    assert by_name["Alpha"]["held_as"] == "Held as: nested boxes, each inside the last."
    assert by_name["Gamma Theorem"]["held_as"] is None


def test_reading_the_model_never_writes_it(vault, capsys):
    _model(vault)
    before = (vault / MODEL).read_bytes()
    _run(vault, "record", "Alpha", "--result", "pass", capsys=capsys)
    _run(vault, "show", "Alpha", capsys=capsys)
    _run(vault, "due", "mixed", capsys=capsys, date="2025-10-02")
    assert (vault / MODEL).read_bytes() == before


def test_new_vaults_and_connected_libraries_start_with_an_empty_learner_model(tmp_path):
    from vault_learning.library import connect
    from vault_learning.scaffold import init_vault
    init_vault(tmp_path / "V", example=False)
    lib = tmp_path / "L"
    lib.mkdir()
    connect(lib, lib / "_learn")
    for root in (tmp_path / "V", lib / "_learn"):
        assert (root / MODEL).is_file()
        assert read_learner_model(Vault(root)) == {}      # the format line is not an entry
