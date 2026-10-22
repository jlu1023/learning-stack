"""Library mode: the learner's own folder of notes, read-only.

A connected library is any folder, in any structure (Markdown, PDFs, Word,
slides, photos of handwritten notes). The engine never writes to it: the
state folder (`_learn/` inside the library by default, or anywhere given by
--state-dir) holds the settings, the cards and the learner state, and
`Vault.write_text` refuses any path outside it.

Cards are `type: card` notes in the state folder, one per idea, with:

    source: "Week 3/Lecture 3.pdf"     # path relative to the library root
    source_anchor: "page 4"            # or "#Heading", optional
    source_hash: 1a2b3c4d5e6f7a8b      # the file's hash when the card was written
    cite_only: true                    # optional: an exercise card with no answer

`scan` compares the library with the cards: new files, changed files (stale
cards), removed files (orphan cards), and files that look like problem
sheets, exercise sets or past papers, whose cards may cite them but must
never hold their solutions.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from urllib.parse import quote

from . import config
from .vault import SKIP_DIRS, Vault

# Claude Code reads these itself (PDFs and images page by page, as images)
READABLE = {".md", ".markdown", ".txt", ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif",
            ".html", ".htm"}
# listed so the scan can ask for them as PDF (Save as PDF in the app that made them)
EXPORT_FIRST = {".docx", ".doc", ".pptx", ".ppt", ".odt", ".odp", ".key", ".pages"}


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

EXERCISE_NAME_RE = re.compile(
    r"(problem[\s_-]*(set|sheet)s?|exercises?|work[\s_-]*sheets?|home[\s_-]*work|\bhw[\s_-]*\d|"
    r"assignments?|course[\s_-]*work|tutorial[\s_-]*sheets?|\bps[\s_-]*\d|past[\s_-]*papers?|"
    r"\bexam(ination)?s?\b|\bmocks?\b|sample[\s_-]*papers?|mark[\s_-]*schemes?|solutions?|answers?)", re.I)
EXERCISE_TEXT_RE = re.compile(
    r"(answer (all|any|\w+) (of the )?(\w+ )?questions|time allowed|candidates (should|must|may)|"
    r"total (of )?\d+ marks|\[\d+ marks?\]|\(\d+ marks?\)|problem (set|sheet) \d|"
    r"exercise sheet|mark scheme|solutions to)", re.I)
ANSWER_RE = re.compile(r"^##\s+Answer\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)


def _first_text(path: Path, limit: int = 4000) -> str:
    ext = path.suffix.lower()
    try:
        if ext in (".md", ".markdown", ".txt"):
            return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:  # noqa: BLE001 - a best-effort hint, never a failure
        return ""
    return ""


def integrity_flag(path: Path, rel: str) -> str | None:
    """Why this file looks like exercises, a problem sheet or a past paper, or None."""
    m = EXERCISE_NAME_RE.search(rel)
    if m:
        return f"file name ('{m.group(0)}')"
    t = EXERCISE_TEXT_RE.search(_first_text(path))
    if t:
        return f"opening text ('{t.group(0)}')"
    return None


def state_href(v: Vault, lib_rel: str) -> str:
    """A Markdown link target from the state folder's root to a library file."""
    target = Path(os.path.relpath(config.SETTINGS["library"] / lib_rel, v.root.resolve()))
    return quote(target.as_posix())


def scan(v: Vault) -> dict:
    lib: Path | None = config.SETTINGS["library"]
    if lib is None:
        return {"error": "not in library mode: vault-learning.yaml has no `library:` setting "
                         "(run /learn:connect first)"}
    if not lib.is_dir():
        return {"error": f"library folder not found: {lib}"}
    state = v.root.resolve()
    files = {}
    for dirpath, dirnames, filenames in os.walk(lib):
        d = Path(dirpath)
        dirnames[:] = sorted(n for n in dirnames if not n.startswith(".") and n not in SKIP_DIRS
                             and (d / n).resolve() != state)
        for fn in sorted(filenames):
            p = d / fn
            ext = p.suffix.lower()
            if ext not in READABLE | EXPORT_FIRST or fn.startswith("."):
                continue
            rel = p.relative_to(lib).as_posix()
            files[rel] = {"file": rel, "kind": ext[1:], "hash": file_hash(p),
                          "integrity": integrity_flag(p, rel), "href_from_state": state_href(v, rel),
                          **({"needs": "save as PDF"} if ext in EXPORT_FIRST else {})}
    cards: dict[str, list[dict]] = {}
    orphans, violations = [], []
    for rel, note in v.notes.items():
        if note.type != "card":
            continue
        src = str(note.fm.get("source") or "").replace("\\", "/")
        info = {"card": rel, "hash": str(note.fm.get("source_hash") or "")}
        if src not in files:
            orphans.append({"card": rel, "source": src})
            continue
        cards.setdefault(src, []).append(info)
        if files[src]["integrity"]:
            ans = ANSWER_RE.search(note.body)
            if ans and re.search(r"\w", re.sub(r"(?i)attempt it first\.?", "", ans.group(1))):
                violations.append({"card": rel, "source": src,
                                   "problem": "card from an exercise or exam source holds an answer"})
    out_files = []
    for rel, f in files.items():
        cs = cards.get(rel, [])
        stale = [c["card"] for c in cs if c["hash"] != f["hash"]]
        status = "new" if not cs else ("changed" if stale else "current")
        out_files.append({**f, "status": status, "cards": len(cs), "stale_cards": stale})
    return {
        "library": str(lib), "state": str(state),
        "files": out_files,
        "counts": {s: sum(1 for f in out_files if f["status"] == s) for s in ("new", "changed", "current")},
        "integrity_flags": [{"file": f["file"], "reason": f["integrity"]} for f in out_files if f["integrity"]],
        "save_as_pdf": [f["file"] for f in out_files if f.get("needs")],
        "integrity_violations": violations,
        "orphan_cards": orphans,
    }


# ---------- connect: create a state folder for a library ----------
STATE_FILES = {
    "CLAUDE.md": """# Learning state for a connected library

This folder belongs to the learn plugin. It holds cards, learner state and logs for the
notes in the library folder named in `vault-learning.yaml`. **The library is read-only:**
never edit, move or rename its files; the engine refuses to write outside this folder.

- Cards: `Courses/<CODE>/<N> <Unit>/<Card>.md`, `type: card`, one idea each, with `source:`
  (path relative to the library), `source_anchor:` and `source_hash:` (from `library-scan`).
- Learner state on cards is written only by the engine's `record` command.
- Exercise sets, problem sheets and past papers (flagged by `library-scan`) are cited,
  never solved: their cards set `cite_only: true` and hold no answer.
- Links: {link_rule}
""",
    "Courses/_learning/Learner Profile.md": """---
title: "Learner Profile"
type: reference
human_authored: false
---

# Learner Profile

Read by `/learn:teach` and `/learn:quiz`. Add who you are, your exams and your known
error patterns; `/learn:teach` appends dated observations under Observations.

## Observations
""",
    "Courses/_learning/Teaching Style.md": """---
title: "Teaching Style"
type: reference
human_authored: true
---

# Teaching Style

Your own preferences for how you are taught. Empty means the method's defaults apply
(definition first, examples, consequences, then theorems; three spaced passes; at most
three ideas per session). The plugin's `vault-template/Courses/_learning/Teaching Style.md`
has a full version with per-course examples to copy from.
""",
    "Courses/_learning/Error Log.md": """---
title: "Error Log"
type: reference
---

# Error Log

One line per mistake, appended by `/learn:teach` and `/learn:quiz`:
`- [date:: YYYY-MM-DD] [course:: CODE] [node:: Card Name] [category:: ...] [redo:: YYYY-MM-DD] What they did: ...`

## Entries
""",
    "Courses/_learning/progress.md": """---
title: "progress"
type: reference
---

# Progress store for human-authored notes

| Note | Path | mastery | mastery_since | last_quizzed | review | review_interval | fail_streak |
|---|---|---|---|---|---|---|---|
""",
    "Courses/_learning/sessions/.gitkeep": "",
    "_meta/log.md": "# Operation log\n",
}


def connect(library: Path, state: Path, frontend: str = "plain") -> dict:
    """Create (or complete) a state folder for `library`. Never touches the library
    itself, except creating `state` when it is the default `_learn/` inside it."""
    library, state = Path(library).resolve(), Path(state).resolve()
    if not library.is_dir():
        return {"error": f"library folder not found: {library}"}
    if frontend not in config.FRONTENDS:
        return {"error": f"frontend must be one of {', '.join(config.FRONTENDS)}"}
    inside = state.is_relative_to(library)
    if inside and state.parent != library:
        return {"error": "a state folder inside the library must sit directly in it (the default _learn/)"}
    lib_ref = ".." if inside else library.as_posix()
    created = []
    cfg = state / config.CONFIG_NAME
    if not cfg.exists():
        state.mkdir(parents=True, exist_ok=True)
        cfg.write_text(f"# learn plugin: settings for a connected library\nlibrary: \"{lib_ref}\"\n"
                       f"frontend: {frontend}\nreference_courses: []\nunit_labels: {{}}\n", encoding="utf-8")
        created.append(config.CONFIG_NAME)
    rule = ("relative Markdown links, `[Name](Name.md)`; any editor works" if frontend == "plain"
            else "wikilinks, `[[Name]]`, for Obsidian")
    for rel, text in STATE_FILES.items():
        p = state / rel
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text.replace("{link_rule}", rule), encoding="utf-8")
            created.append(rel)
    return {"library": str(library), "state": str(state), "inside_library": inside,
            "created": created,
            "next": ("open Claude Code in the library folder" if inside else
                     f"open Claude Code in {state}, or set LEARN_STATE_DIR={state}, or pass --state-dir")}
