"""`init`: a new vault from the template bundled with the plugin."""
from vault_learning.cli import main
from vault_learning.graph import roadmap_courses
from vault_learning.scaffold import TEMPLATE, init_vault
from vault_learning.vault import Vault


def test_template_ships_inside_the_plugin():
    assert TEMPLATE.name == "vault-template" and TEMPLATE.parent.name == "plugin"
    assert (TEMPLATE / "CLAUDE.md").is_file() and (TEMPLATE / "vault-learning.yaml").is_file()


def test_init_makes_a_working_vault(tmp_path):
    out = init_vault(tmp_path / "Study")
    assert out["created"] > 30 and out["kept_existing"] == []
    v = Vault(tmp_path / "Study")
    assert roadmap_courses(v) == ["COURSE101"]
    assert (tmp_path / "Study" / ".obsidian" / "templates.json").is_file()


def test_init_plain_without_example(tmp_path):
    out = init_vault(tmp_path / "S", frontend="plain", example=False)
    assert out["frontend"] == "plain"
    cfg = (tmp_path / "S" / "vault-learning.yaml").read_text(encoding="utf-8")
    assert "frontend: plain" in cfg and "reference_courses: []" in cfg
    assert not (tmp_path / "S" / ".obsidian").exists()
    assert not (tmp_path / "S" / "Courses" / "COURSE101").exists()
    assert (tmp_path / "S" / "Courses" / "_learning" / "Error Log.md").is_file()
    assert roadmap_courses(Vault(tmp_path / "S")) == []


def test_init_never_overwrites(tmp_path):
    (tmp_path / "Courses" / "_learning").mkdir(parents=True)
    mine = tmp_path / "Courses" / "_learning" / "Error Log.md"
    mine.write_text("my log\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("my rules\n", encoding="utf-8")
    out = init_vault(tmp_path)
    assert {"CLAUDE.md", "Courses/_learning/Error Log.md"} <= set(out["kept_existing"])
    assert mine.read_text(encoding="utf-8") == "my log\n"
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "my rules\n"


def test_cli_init(tmp_path, capsys):
    assert main(["init", str(tmp_path / "V"), "--frontend", "plain"]) == 0
    assert '"frontend": "plain"' in capsys.readouterr().out
