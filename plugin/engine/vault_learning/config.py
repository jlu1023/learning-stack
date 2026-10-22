"""Per-vault settings, read from `vault-learning.yaml` at the vault root.

Every key is optional; with no file the engine treats every `Courses/<CODE>/`
folder with a `<CODE> Syllabus.md` as a course and names its units "Module".

```yaml
# Courses whose notes are only ever prerequisites (for example last year's
# courses): never roadmapped, never quizzed, shown as external prerequisites.
reference_courses: [PRE100]

# Courses whose notes live outside Courses/. Each top-level folder under
# `root` (minus `exclude`) is a module; `mixed_cap` limits how many of the
# course's items one `due mixed` draw may hold (0 = no cap).
extra_courses:
  Reading:
    root: "Reading/"
    exclude: ["Inbox"]
    mixed_cap: 1

# What to call a folder-based unit, per course: Lecture, Week, Chapter or Module.
unit_labels:
  COURSE101: Lecture

# obsidian (default): wikilinks, Dataview, %% markers %%. plain: any editor -
# Markdown links, HTML-comment markers, roadmap images and static review tables.
frontend: obsidian

# Library mode: the folder of the learner's own notes, read-only, relative to
# this file's folder or absolute. Cards and state live in this folder instead.
library: ".."
```

`state_dir` is not read here: it is a pointer, read by `vault.resolve_root`.

The registries below are module-level so the graph helpers can stay plain
functions; `load` replaces their contents each time a Vault is opened.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_NAME = "vault-learning.yaml"
LABELS = ("Lecture", "Week", "Chapter", "Module")


@dataclass(frozen=True)
class CourseSpec:
    root: str                       # vault-relative course folder, with a trailing slash
    exclude: tuple[str, ...] = ()   # top-level folders under root that are not modules
    mixed_cap: int = 0              # most items per `due mixed` draw; 0 means no cap


FRONTENDS = ("obsidian", "plain")

REFERENCE_COURSES: set[str] = set()
EXTRA_COURSES: dict[str, CourseSpec] = {}
UNIT_LABELS: dict[str, str] = {}
SETTINGS: dict = {"frontend": "obsidian", "library": None}


def plain() -> bool:
    return SETTINGS["frontend"] == "plain"


def load(root: Path) -> dict:
    """Read the vault's settings into the registries. Returns the raw mapping."""
    p = Path(root) / CONFIG_NAME
    data = {}
    if p.is_file():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"{CONFIG_NAME} is not a mapping")
    REFERENCE_COURSES.clear()
    REFERENCE_COURSES.update(str(c).upper() for c in data.get("reference_courses") or [])
    EXTRA_COURSES.clear()
    for code, spec in (data.get("extra_courses") or {}).items():
        root_rel = str(spec["root"]).replace("\\", "/")
        if not root_rel.endswith("/"):
            root_rel += "/"
        EXTRA_COURSES[str(code)] = CourseSpec(root=root_rel,
                                              exclude=tuple(spec.get("exclude") or ()),
                                              mixed_cap=int(spec.get("mixed_cap") or 0))
    UNIT_LABELS.clear()
    for code, label in (data.get("unit_labels") or {}).items():
        if label not in LABELS:
            raise ValueError(f"{CONFIG_NAME}: unit label for {code} must be one of {', '.join(LABELS)}")
        UNIT_LABELS[str(code).upper()] = label
    frontend = str(data.get("frontend") or "obsidian").lower()
    if frontend not in FRONTENDS:
        raise ValueError(f"{CONFIG_NAME}: frontend must be one of {', '.join(FRONTENDS)}")
    SETTINGS["frontend"] = frontend
    lib = data.get("library")
    SETTINGS["library"] = (Path(root) / str(lib)).resolve() if lib else None
    return data
