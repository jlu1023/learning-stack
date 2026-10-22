"""Teaching units (a lecture, a week or a module) and their primers.

A course's unit is the part of it a lecture primer covers. It is found in this order:

1. the notes' `lecture:` field, when the course's notes carry one (a course that
   follows a textbook out of order, lecture by lecture);
2. else a `## Lecture map` table in the course MOC with a `Sections` column, which
   assigns sections of the notes to lectures (a course taught from numbered notes).
   A note goes to the lecture of the longest listed section its own `section:` starts
   with, so "3.1" can sit in one lecture and "3.1.1" in the next, and a bare "5"
   catches a chapter's intro notes;
3. else the module folder, numbered by its prefix (one folder per lecture, week or
   module). `unit_labels` in the vault's settings names the unit for each course.

A primer is a `type: moc` note with `primer: true`, `course:` and `unit:` (the
number) in frontmatter, saved in the unit's module folder. Being a moc, it is never
a graph node. A unit is started once any of its nodes has a lock-in or review
attempt (`last_quizzed`), so a failed first attempt counts as started.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from .config import UNIT_LABELS
from .graph import CourseGraph, canonical_code, module_number, section_key
from .state import read_progress, read_state
from .vault import Vault, owner_label

LECTURE_MAP_RE = re.compile(r"^##\s+Lecture map\s*$", re.M | re.I)
LEAD_INT_RE = re.compile(r"^\s*(\d+)")
SECTION_TOKEN_RE = re.compile(r"(?<![\d.])\d+(?:\.\d+)*")


@dataclass
class Unit:
    number: int
    label: str
    title: str
    nodes: list[str] = field(default_factory=list)     # graph node rels, suggested order

    @property
    def name(self) -> str:
        return f"{self.label} {self.number}"


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def lecture_map(text: str) -> list[dict[str, str]]:
    """Rows of the first table under '## Lecture map', keyed by lower-case header."""
    m = LECTURE_MAP_RE.search(text)
    if not m:
        return []
    rows, header = [], None
    for line in text[m.end():].splitlines():
        s = line.strip()
        if not s:
            if header:
                break
            continue
        if s.startswith("#"):
            break
        if not s.startswith("|"):
            if header:
                break
            continue
        cells = _cells(s)
        if header is None:
            header = [c.lower() for c in cells]
        elif all(set(c) <= set("-: ") for c in cells):
            continue
        else:
            rows.append(dict(zip(header, cells)))
    return rows


class CourseUnits:
    def __init__(self, vault: Vault, code: str, cg: CourseGraph | None = None):
        self.v = vault
        self.code = canonical_code(code)
        self.cg = cg or CourseGraph(vault, self.code)
        self.unit_of: dict[str, int] = {}
        self.units: dict[int, Unit] = {}
        self.unassigned: list[str] = []
        self.basis = ""
        self._build()

    def _build(self) -> None:
        cg, v = self.cg, self.v
        order = cg.suggested_order()
        rows = lecture_map(v.note(cg.course_moc).body) if v.exists(cg.course_moc) else []
        first_col = next(iter(rows[0]), "") if rows else ""
        titles: dict[int, str] = {}
        for r in rows:
            m = LEAD_INT_RE.match(r.get(first_col, ""))
            if m and r.get("topics"):
                titles[int(m.group(1))] = r["topics"]

        has_field = any(isinstance(v.note(n).fm.get("lecture"), int) for n in order)
        if has_field:
            self.basis, label = "lecture field", "Lecture"
            for n in order:
                lec = v.note(n).fm.get("lecture")
                if isinstance(lec, int):
                    self.unit_of[n] = lec
        elif rows and "sections" in rows[0]:
            self.basis, label = "lecture map sections", "Lecture"
            sec_to: dict[tuple, int] = {}
            for r in rows:
                m = LEAD_INT_RE.match(r.get(first_col, ""))
                if not m:
                    continue
                for tok in SECTION_TOKEN_RE.findall(r["sections"]):
                    sec_to[section_key(tok)] = int(m.group(1))
            for n in order:
                sk = section_key(v.note(n).fm.get("section"))
                hit = next((sk[:i] for i in range(len(sk), 0, -1) if sk[:i] in sec_to), None)
                if hit is not None:
                    self.unit_of[n] = sec_to[hit]
        else:
            self.basis, label = "module folder", UNIT_LABELS.get(self.code.upper(), "Module")
            for n in order:
                num = module_number(cg.module_of[n])
                if num < 10**6:
                    self.unit_of[n] = num
            for mod in cg.modules:
                num = module_number(mod.folder)
                if num < 10**6:
                    titles[num] = re.sub(r"^\d+\s+", "", mod.folder)

        for n in order:
            if n not in self.unit_of:
                self.unassigned.append(n)
                continue
            k = self.unit_of[n]
            if k not in self.units:
                self.units[k] = Unit(k, label, titles.get(k, f"{label} {k}"))
            self.units[k].nodes.append(n)
        self.units = dict(sorted(self.units.items()))

    # ---------- primers ----------
    def primers(self) -> dict[int, list[str]]:
        out: dict[int, list[str]] = defaultdict(list)
        for rel, note in self.v.notes.items():
            if not rel.startswith(self.cg.prefix) or note.fm.get("primer") is not True:
                continue
            if canonical_code(str(note.fm.get("course", ""))) != self.code:
                continue
            u = note.fm.get("unit")
            if isinstance(u, int):
                out[u].append(rel)
        return out

    # ---------- output ----------
    def _brief(self, k: int | None, primers, progress) -> dict | None:
        if k is None or k not in self.units:
            return None
        u = self.units[k]
        states = [read_state(self.v, n, progress) for n in u.nodes]
        hits = primers.get(k, [])
        return {"unit": k, "name": u.name, "title": u.title, "nodes": len(u.nodes),
                "started": any(s.last_quizzed for s in states),
                "primer": hits[0][:-3] if len(hits) == 1 else None,
                **({"primer_conflict": [h[:-3] for h in hits]} if len(hits) > 1 else {})}

    def summary(self) -> dict:
        primers, progress = self.primers(), read_progress(self.v)
        return {"course": self.code, "basis": self.basis,
                "units": [self._brief(k, primers, progress) for k in self.units],
                "unassigned": [self.cg.name(n) for n in self.unassigned],
                "orphan_primers": [p[:-3] for k, ps in primers.items()
                                   if k not in self.units for p in ps]}

    def detail(self, k: int) -> dict:
        if k not in self.units:
            return {"course": self.code, "error": f"no unit {k}", "units": list(self.units)}
        primers, progress = self.primers(), read_progress(self.v)
        cg, u = self.cg, self.units[k]
        keys = list(self.units)
        i = keys.index(k)
        members = set(u.nodes)
        ext: dict[str, set[str]] = defaultdict(set)
        for n in u.nodes:
            for e in cg.ext.get(n, ()):
                ext[owner_label(e)].add(e[:-3].rsplit("/", 1)[-1])
        out_links: dict[str, set[str]] = defaultdict(set)
        for owner, rels in cg.used_outside().items():
            for rel, inside in rels.items():
                if inside & members:
                    out_links[owner].add(rel[:-3].rsplit("/", 1)[-1])
        nodes = []
        for n in u.nodes:
            note, s = self.v.note(n), read_state(self.v, n, progress)
            nodes.append({"name": note.name, "type": note.type, "module": cg.module_of[n],
                          "section": note.fm.get("section"),
                          "mastery": s.mastery, "last_quizzed": s.to_json()["last_quizzed"]})
        return {
            **self._brief(k, primers, progress),
            "course": self.code, "basis": self.basis,
            "modules": sorted({cg.module_of[n] for n in u.nodes}, key=module_number),
            "previous": self._brief(keys[i - 1] if i > 0 else None, primers, progress),
            "following": self._brief(keys[i + 1] if i + 1 < len(keys) else None, primers, progress),
            "node_list": nodes,
            "external_prereqs": {o: sorted(s) for o, s in sorted(ext.items())},
            "used_outside": {o: sorted(s) for o, s in sorted(out_links.items())},
        }
