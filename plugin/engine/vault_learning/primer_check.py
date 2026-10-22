"""Lint lecture primers (read-only). The format is set in the plugin's
method skill (Primers); this checks what can be checked mechanically."""
from __future__ import annotations

import re

from .graph import CourseGraph, roadmap_courses
from .units import CourseUnits
from .vault import Vault, link_target

MAX_WORDS = 250
NAME_RE = re.compile(r"^(?P<code>\S+) (?P<label>Lecture|Week|Module|Chapter) (?P<n>\d+) Overview - .+$")
MERMAID_RE = re.compile(r"```mermaid\n(.*?)```", re.S)
WIKILINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")
INLINE_MATH_RE = re.compile(r"\$[^$\n]+\$")
REQUIRED = ["**The question:**", "## Where it sits", "## Key ideas", "## Why it matters",
            "## Before you start"]
FORBIDDEN_SOURCE_RE = re.compile(r"\b(exam|sample paper|solutions?)\b", re.I)


def _section(body: str, heading: str) -> str:
    m = re.search(rf"^{re.escape(heading)}\s*$", body, re.M)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def _numbered(text: str) -> int:
    return len(re.findall(r"^\d+\.\s", text, re.M))


def prose_words(body: str) -> int:
    """Words outside the diagram: a wikilink counts as its shown text, inline maths as one word."""
    t = MERMAID_RE.sub(" ", body)
    t = re.sub(r"^#.*$", " ", t, flags=re.M)                    # headings
    t = WIKILINK_RE.sub(lambda m: m.group(1).split("|")[-1].split("#")[0], t)
    t = INLINE_MATH_RE.sub(" M ", t)
    t = re.sub(r"[*_>`|]", " ", t)
    return len([w for w in t.split() if re.search(r"\w", w)])


def check_primer(v: Vault, rel: str, units: dict[str, CourseUnits]) -> list[str]:
    note = v.note(rel)
    fm, body, probs = note.fm, note.body, []
    code = str(fm.get("course", ""))
    m = NAME_RE.match(note.name)
    if not m:
        probs.append("file name is not '<CODE> <Lecture|Week|Module|Chapter> <N> Overview - <Title>'")
    if fm.get("type") != "moc":
        probs.append("type is not moc")
    if str(fm.get("title", "")) != note.name:
        probs.append("title does not match the file name")
    cu = units.get(code)
    if cu is None:
        probs.append(f"course '{code}' is not a roadmap course")
    elif not isinstance(fm.get("unit"), int) or fm["unit"] not in cu.units:
        probs.append(f"unit {fm.get('unit')!r} is not a unit of {code}")
    elif m:
        u = cu.units[fm["unit"]]
        if (m["code"], m["label"], int(m["n"])) != (code, u.label, u.number):
            probs.append(f"file name does not match the unit ({code} {u.name})")
    for h in REQUIRED:
        if h not in body:
            probs.append(f"missing '{h}'")
    ideas = _numbered(_section(body, "## Key ideas"))
    if not 3 <= ideas <= 5:
        probs.append(f"{ideas} key ideas (want 3 to 5)")
    qs = _numbered(_section(body, "## Before you start"))
    if not 2 <= qs <= 3:
        probs.append(f"{qs} prerequisite questions (want 2 or 3)")
    diagrams = MERMAID_RE.findall(body)
    if len(diagrams) != 1:
        probs.append(f"{len(diagrams)} Mermaid diagrams (want 1)")
    words = prose_words(body)
    if words > MAX_WORDS:
        probs.append(f"{words} words (limit {MAX_WORDS})")
    if "—" in v.read_text(rel):
        probs.append("contains an em dash")
    for raw in WIKILINK_RE.findall(body):
        hits = v.resolve(raw)
        if len(hits) != 1:
            probs.append(f"link [[{raw}]] resolves to {len(hits)} notes")
        if FORBIDDEN_SOURCE_RE.search(link_target(raw)) and "Exam Profile" not in raw:
            probs.append(f"links what looks like an exam paper: [[{raw}]]")
    for s in fm.get("sources") or []:
        if FORBIDDEN_SOURCE_RE.search(str(s)) and "Exam Profile" not in str(s):
            probs.append(f"source looks like an exam paper: {s}")
    folder = rel.rsplit("/", 1)[0]
    moc = f"{folder}/{folder.rsplit('/', 1)[-1]}.md"
    if not v.exists(moc) or f"[[{note.name}" not in v.read_text(moc):
        probs.append("not linked from its module MOC")
    return probs


def check_all(v: Vault, course: str | None = None, validate_diagrams: bool = True) -> dict:
    codes = [c for c in roadmap_courses(v) if course in (None, "all") or c.upper() == course.upper()]
    units = {c: CourseUnits(v, c, CourseGraph(v, c)) for c in codes}
    results, diagrams = [], []
    for c, cu in units.items():
        for k, rels in sorted(cu.primers().items()):
            if len(rels) > 1:
                results.append({"primer": rels[0][:-3], "problems": [f"unit {k} has {len(rels)} primers"]})
            for rel in rels:
                results.append({"primer": rel[:-3], "problems": check_primer(v, rel, units)})
                diagrams += [(rel[:-3], d) for d in MERMAID_RE.findall(v.note(rel).body)]
    if validate_diagrams and diagrams:
        from .validate import validate
        bad = dict(validate(diagrams))
        for r in results:
            if r["primer"] in bad:
                r["problems"].append(f"Mermaid does not render: {bad[r['primer']]}")
    missing = {c: [u.name for k, u in cu.units.items() if k not in cu.primers()] for c, cu in units.items()}
    return {"checked": len(results), "failing": sum(1 for r in results if r["problems"]),
            "results": results, "units_without_primer": missing}
