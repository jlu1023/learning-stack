"""Launcher for the learning engine: `python <plugin>/engine/vl.py <command> ...`.

Equivalent to `python -m vault_learning` run from this folder, so the skills can
call the engine from the vault without installing it. The vault is --vault,
else $VAULT_ROOT, else the current directory.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vault_learning.cli import main  # noqa: E402

sys.exit(main())
