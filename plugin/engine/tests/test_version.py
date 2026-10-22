"""The plugin manifest and the engine agree on the version."""
import json
from pathlib import Path

import vault_learning
from vault_learning.cli import main


def test_manifest_and_engine_versions_match():
    manifest = json.loads((Path(__file__).resolve().parents[2] / ".claude-plugin" / "plugin.json")
                          .read_text(encoding="utf-8"))
    assert manifest["version"] == vault_learning.__version__


def test_version_flag(capsys):
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0
    assert vault_learning.__version__ in capsys.readouterr().out
