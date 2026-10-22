"""`init`: make a new vault from the template that ships with the plugin.

Copies `<plugin>/vault-template/` into a folder, never overwriting a file that
is already there, so it is safe to run in a folder that has notes in it. With
`frontend="plain"` the settings file is set for editors other than Obsidian
and the Obsidian-only `.obsidian/` folder is left out.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from . import config

TEMPLATE = Path(__file__).resolve().parents[2] / "vault-template"
EXAMPLE_DIRS = ("Courses/COURSE101", "Courses/PRE100")


def init_vault(target: Path, frontend: str = "obsidian", example: bool = True) -> dict:
    target = Path(target)
    if frontend not in config.FRONTENDS:
        return {"error": f"frontend must be one of {', '.join(config.FRONTENDS)}"}
    if not TEMPLATE.is_dir():
        return {"error": f"vault template not found at {TEMPLATE}"}
    created, kept = [], []
    for src in sorted(TEMPLATE.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(TEMPLATE).as_posix()
        if frontend == "plain" and rel.startswith(".obsidian/"):
            continue
        if not example and rel.startswith(tuple(d + "/" for d in EXAMPLE_DIRS)):
            continue
        dst = target / rel
        if dst.exists():
            kept.append(rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        created.append(rel)
    cfg = target / config.CONFIG_NAME
    if frontend == "plain" and config.CONFIG_NAME in created:
        text = cfg.read_text(encoding="utf-8")
        cfg.write_text(text.replace("frontend: obsidian", "frontend: plain"), encoding="utf-8")
    if not example and config.CONFIG_NAME in created:
        text = cfg.read_text(encoding="utf-8")
        cfg.write_text(text.replace("reference_courses: [PRE100]", "reference_courses: []"), encoding="utf-8")
    return {"vault": str(target.resolve()), "frontend": frontend, "example_course": example,
            "created": len(created), "kept_existing": kept}
