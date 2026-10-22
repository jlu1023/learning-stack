"""Command line: python -m vault_learning <command> ...

  roadmap [COURSE|all] [--dry-run] [--no-validate]   generate roadmaps into the vault
  graph COURSE                                       course graph as JSON (for /teach)
  next COURSE                                        next node to teach (JSON)
  due [COURSE|mixed] [--limit N]                     due reviews and Error Log redos (JSON)
  show NOTE                                          learner state of one note (JSON)
  record NOTE --result pass|fail                     apply a lock-in or review result
  index [--dry-run]                                  regenerate _meta/Vault Index.md (also run by `roadmap all`)
  unit COURSE [all|next|N]                           teaching units (lecture, week, module) and their primers (JSON)
  check-primer [COURSE|all] [--no-validate]          lint lecture primers (exit 1 if any fail)
  where                                              the folder in use, its library and front end (JSON)
  doctor                                             Python, optional extras and what each adds (JSON)
  init [FOLDER] [--frontend plain] [--no-example]    a new vault from the plugin's template (never overwrites)
  connect LIBRARY [--frontend plain|obsidian]        library mode: create the state folder (LIBRARY/_learn, or --state-dir)
  library-scan                                       library mode: new, changed and flagged files (JSON)
  review-queue [--dry-run]                           plain mode: rewrite the static Review Queue

Global options, before the command: --vault PATH or --state-dir PATH (the folder
the engine reads and writes; see vault.resolve_root for the defaults), and
--date YYYY-MM-DD (default: today).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from .graph import CourseGraph, canonical_code, course_moc_rel, course_spec, in_any_course, roadmap_courses
from .index import write_index
from .primer_check import check_all
from .units import CourseUnits
from .render import OBSIDIAN_MARKERS, PLAIN_MARKERS, Renderer
from .state import (LEVELS, apply_result, read_error_log, read_progress,
                    read_state, write_state)
from . import config, miniyaml
from .library import connect as connect_library, scan as library_scan
from .review_queue import REVIEW_QUEUE_REL, review_queue_text
from .vault import Vault, parse_frontmatter, resolve_root, set_frontmatter_fields


# ---------- marker writing ----------
def replace_block(text: str, block: str) -> tuple[str, str]:
    """Insert or replace the roadmap marker block. Returns (new_text, action).

    First run: insert before the first H2 after the frontmatter (or at the end).
    Later runs: replace exactly the marked span; bytes outside it are untouched.
    """
    # an existing block keeps its place whichever marker style it uses
    start, end = next(((s, e) for s, e in (OBSIDIAN_MARKERS, PLAIN_MARKERS) if s in text or e in text),
                      OBSIDIAN_MARKERS)
    ns, ne = text.count(start), text.count(end)
    nl = "\r\n" if "\r\n" in text else "\n"
    blk = block.replace("\n", nl)
    if ns == 1 and ne == 1:
        a, b = text.index(start), text.index(end) + len(end)
        if a > b:
            raise ValueError("roadmap markers out of order")
        if text[a:b] == blk:
            return text, "unchanged"
        return text[:a] + blk + text[b:], "replaced"
    if ns or ne:
        raise ValueError(f"malformed roadmap markers ({ns} start, {ne} end)")
    _, _, body = parse_frontmatter(text)
    body_start = len(text) - len(body)
    lines = text[body_start:].split(nl)
    offset = body_start
    for line in lines:
        if line.startswith("## "):
            return text[:offset] + blk + nl + nl + text[offset:], "inserted"
        offset += len(line) + len(nl)
    sep = "" if text.endswith(nl) else nl
    return text + sep + nl + blk + nl, "inserted"


def bump_updated(text: str, today: dt.date) -> str:
    return set_frontmatter_fields(text, {"updated": today.isoformat()})


def cmd_roadmap(args, v: Vault, today: dt.date) -> int:
    report, code = roadmap_report(v, args.course, today, args.dry_run, args.no_validate)
    print(json.dumps(report, indent=1, default=str))
    return code


def roadmap_report(v: Vault, course: str | None, today: dt.date, dry_run: bool = False,
                   no_validate: bool = False) -> tuple[dict, int]:
    """Build, validate and (unless dry_run) write roadmaps. Returns (report, exit code)."""
    from .validate import ValidatorUnavailable, validate
    courses = roadmap_courses(v) if course in (None, "all") else [canonical_code(course)]
    report = {"date": today.isoformat(), "courses": {}, "validation": None, "skipped": [], "errors": []}
    plans = []   # (rel, new_text, action)
    all_diagrams = []
    exports = []  # (svg rel, diagram): plain mode only
    for code in courses:
        if not v.exists(course_moc_rel(code)):
            report["errors"].append(f"{code}: no course MOC '{course_moc_rel(code)}'")
            continue
        cg = CourseGraph(v, code)
        r = Renderer(cg)
        created = None
        if v.exists(cg.roadmap_rel):
            created = v.note(cg.roadmap_rel).fm.get("created")
            created = str(created) if created else None
        text, diags = r.roadmap_note(today, created)
        all_diagrams += diags
        if v.exists(cg.roadmap_rel):
            old = v.read_text(cg.roadmap_rel)
            same = _strip_updated(old) == _strip_updated(text)
            plans.append((cg.roadmap_rel, old if same else text, "unchanged" if same else "rewritten"))
        else:
            plans.append((cg.roadmap_rel, text, "created"))
        for m in cg.modules:
            if not m.moc_rel:
                report["skipped"].append(f"{code} {m.folder}: no module MOC")
                continue
            block, diags = r.module_block(m.folder)
            all_diagrams += diags
            plans.append(_moc_plan(v, m.moc_rel, block, today, report))
        plans.append(_moc_plan(v, cg.course_moc, r.course_moc_block(), today, report))
        report["courses"][code] = {"stats": cg.stats(), "spine": [cg.name(n) for n, _ in cg.spine()],
                                   "mastery": dict(r.mastery_counts())}
        exports += r.exports
    plans = [p for p in plans if p]
    if no_validate:
        report["validation"] = {"method": "skipped (--no-validate)", "diagrams": len(all_diagrams)}
    else:
        try:
            fails = validate(all_diagrams)
            report["validation"] = {"method": "mermaid-cli render (mmdc)",
                                    "diagrams": len(all_diagrams), "failures": fails}
        except ValidatorUnavailable as e:
            # optional dependency: write anyway, and say the diagrams were not checked
            fails = []
            report["validation"] = {"method": f"skipped (validator unavailable: {e})",
                                    "diagrams": len(all_diagrams)}
        if fails:
            report["errors"].append("validation failed; nothing written")
            return report, 1
    plans += _image_plans(v, exports, report)
    if config.plain() and course in (None, "all"):
        plans.append(_file_plan(v, REVIEW_QUEUE_REL, review_queue_text(v, today)))
    written = []
    for rel, text, action in plans:
        if action in ("unchanged",):
            continue
        if not dry_run:
            v.write_text(rel, text)
        written.append(f"{action}: {rel}")
    report["written" if not dry_run else "would_write"] = written
    if course in (None, "all"):
        report["index"] = write_index(v, today, dry_run=dry_run)
    return report, 0


def _strip_updated(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.startswith("updated:"))


def _file_plan(v: Vault, rel: str, text: str) -> tuple[str, str, str]:
    if not v.exists(rel):
        return (rel, text, "created")
    old = v.read_text(rel)
    return (rel, old, "unchanged") if _strip_updated(old) == _strip_updated(text) else (rel, text, "rewritten")


def _image_plans(v: Vault, exports: list[tuple[str, str]], report: dict) -> list[tuple[str, str, str]]:
    """Plain mode with mermaid-cli installed: each diagram as an SVG beside its note.
    (Without mermaid-cli the notes keep plain Mermaid blocks and nothing is exported.)"""
    from .validate import ValidatorUnavailable, render_svgs
    if not exports:
        return []
    try:
        svgs = render_svgs(exports)
    except ValidatorUnavailable as e:
        report["errors"].append(f"roadmap images were not drawn: {e}")
        return []
    missing = [rel for rel, _ in exports if rel not in svgs]
    if missing:
        report["errors"].append(f"{len(missing)} roadmap images did not render: {', '.join(missing)}")
    return [_file_plan(v, rel, svgs[rel]) for rel, _ in exports if rel in svgs]


def _moc_plan(v: Vault, rel: str, block: str, today: dt.date, report: dict):
    note = v.note(rel)
    if note.human_authored:
        report["skipped"].append(f"{rel}: human_authored, not edited")
        return None
    text = v.read_text(rel)
    try:
        new, action = replace_block(text, block)
    except ValueError as e:
        report["skipped"].append(f"{rel}: {e}")
        return None
    if action == "unchanged":
        return (rel, text, "unchanged")
    return (rel, bump_updated(new, today), f"markers {action}")


# ---------- errors ----------
class EngineError(Exception):
    """An expected failure: main prints {"error": ..., **extra} as JSON and exits 2."""

    def __init__(self, error: str, **extra):
        super().__init__(error)
        self.payload = {"error": error, **extra}


def _course(v: Vault, code: str) -> str:
    """The course code, or an EngineError naming the courses that exist."""
    known = roadmap_courses(v)
    if code not in known:
        raise EngineError(f"no course '{code}' (a course needs Courses/{code}/{code} Syllabus.md)",
                          courses=known)
    return code


# ---------- state commands ----------
def _find_note(v: Vault, name: str) -> str:
    hits = v.resolve(name)
    hits = [h for h in hits if in_any_course(h)]
    if len(hits) != 1:
        raise EngineError(f"'{name}' matches {len(hits)} course notes", matches=hits)
    return hits[0]


def graph_json(v: Vault, code: str) -> dict:
    cg = CourseGraph(v, _course(v, code))
    progress = read_progress(v)
    order = cg.suggested_order()
    pos = {n: i for i, n in enumerate(order)}
    units = CourseUnits(v, code, cg)
    nodes = []
    for n in order:
        note = v.note(n)
        nodes.append({
            "name": note.name, "path": n, "type": note.type, "module": cg.module_of[n],
            "section": note.fm.get("section"), "lecture": note.fm.get("lecture"),
            "unit": units.unit_of.get(n), "order": pos[n],
            "prereqs": [cg.name(p) for p in sorted(cg.G.predecessors(n), key=pos.get)],
            "external_prereqs": [p[:-3] for p in sorted(cg.ext.get(n, ()))],
            "dependents": [cg.name(p) for p in sorted(cg.G.successors(n), key=pos.get)],
            "proofs": [cg.name(p) for p in cg.proofs_for.get(n, [])],
            "examples": sorted(cg.name(e) for e, a in cg.example_anchor.items() if n in a),
            "human_authored": note.human_authored,
            "state": read_state(v, n, progress).to_json(),
        })
    return {"course": code, "nodes": nodes}


def next_node(v: Vault, code: str) -> dict:
    g = graph_json(v, code)
    by = {n["name"]: n for n in g["nodes"]}
    ok = lambda n: LEVELS.index(n["state"]["mastery"]) >= 1
    elig = [n for n in g["nodes"] if n["state"]["mastery"] == "unseen"
            and all(ok(by[p]) for p in n["prereqs"])]
    if not elig:
        blocked = [n for n in g["nodes"] if n["state"]["mastery"] == "unseen"]
        return {"course": code, "next": None,
                "reason": "no unseen node has all its prerequisites at learning or better" if blocked
                          else "every node is at learning or better"}
    lectures = [n["lecture"] for n in elig if isinstance(n["lecture"], int)]
    if lectures:
        top = max(lectures)
        pick = next(n for n in elig if n["lecture"] == top)
        rule = f"latest lecture ({top}), then suggested order"
    else:
        pick, rule = elig[0], "suggested order"
    return {"course": code, "next": pick, "rule": rule, "eligible_count": len(elig)}


def unit_json(v: Vault, code: str, which: str) -> dict:
    cu = CourseUnits(v, _course(v, code))
    if which == "all":
        return cu.summary()
    if which == "next":
        nxt = next_node(v, code)["next"]
        if nxt is None or nxt.get("unit") is None:
            return {"course": cu.code, "next": None,
                    "reason": "no next node" if nxt is None else f"'{nxt['name']}' has no unit"}
        return {"next_node": nxt["name"], **cu.detail(nxt["unit"])}
    if not which.isdigit():
        raise EngineError(f"unit must be all, next or a number, not '{which}'")
    return cu.detail(int(which))


def due_items(v: Vault, which: str | None, today: dt.date, limit: int) -> dict:
    mixed = which in (None, "mixed", "all")
    courses = roadmap_courses(v) if mixed else [_course(v, canonical_code(which))]
    progress = read_progress(v)
    errors = read_error_log(v)
    err_count = {}
    for e in errors:
        err_count[e.get("node", "")] = err_count.get(e.get("node", ""), 0) + 1
    items = []
    for code in courses:
        cg = CourseGraph(v, code)
        for n in cg.nodes:
            s = read_state(v, n, progress)
            if s.mastery == "unseen" and not s.last_quizzed:
                continue
            if s.review and s.review <= today:
                name = cg.name(n)
                items.append({"course": code, "name": name, "path": n, "state": s.to_json(),
                              "overdue_days": (today - s.review).days,
                              "errors_logged": err_count.get(name, 0)})
    items.sort(key=lambda x: (-(x["overdue_days"] + 3 * x["errors_logged"]), x["state"]["last_quizzed"] or ""))
    capped = 0
    if mixed:
        # a registered course's mixed_cap keeps its most urgent items only
        kept, seen = [], {}
        for it in items:
            cap = course_spec(it["course"]).mixed_cap
            seen[it["course"]] = seen.get(it["course"], 0) + 1
            if cap and seen[it["course"]] > cap:
                capped += 1
                continue
            kept.append(it)
        items = kept
    redos, problems = [], []
    for e in errors:
        if not e.get("redo") or e.get("redone"):
            continue
        try:
            when = dt.date.fromisoformat(e["redo"][:10])
        except ValueError:          # a hand-typed line: report it, keep going
            problems.append(f"{e.get('node', '?')}: redo date '{e['redo']}' is not YYYY-MM-DD")
            continue
        if when <= today and (mixed or e.get("course", "").upper() == which.upper()):
            redos.append(e)
    out = {"date": today.isoformat(), "due": items[:limit] if limit else items,
           "due_total": len(items), "capped": capped, "redos": redos}
    if problems:
        out["error_log_problems"] = problems
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="vault_learning", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=None)
    ap.add_argument("--state-dir", default=None, help="library mode: where cards and state live")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD, default today")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("roadmap"); p.add_argument("course", nargs="?", default="all")
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--no-validate", action="store_true")
    p = sub.add_parser("graph"); p.add_argument("course")
    p = sub.add_parser("next"); p.add_argument("course")
    p = sub.add_parser("due"); p.add_argument("course", nargs="?", default="mixed")
    p.add_argument("--limit", type=int, default=0)
    p = sub.add_parser("show"); p.add_argument("note")
    p = sub.add_parser("record"); p.add_argument("note")
    p.add_argument("--result", choices=["pass", "fail"], required=True)
    p = sub.add_parser("index"); p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("unit"); p.add_argument("course"); p.add_argument("which", nargs="?", default="all")
    p = sub.add_parser("check-primer"); p.add_argument("course", nargs="?", default="all")
    p.add_argument("--no-validate", action="store_true")
    sub.add_parser("where")
    sub.add_parser("doctor")
    p = sub.add_parser("init"); p.add_argument("folder", nargs="?", default=".")
    p.add_argument("--frontend", choices=list(config.FRONTENDS), default="obsidian")
    p.add_argument("--no-example", action="store_true")
    sub.add_parser("library-scan")
    p = sub.add_parser("connect"); p.add_argument("library")
    p.add_argument("--frontend", choices=list(config.FRONTENDS), default="plain")
    p = sub.add_parser("review-queue"); p.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        return _run(args)
    except EngineError as e:
        out = e.payload
    except miniyaml.YAMLError as e:
        out = {"error": f"could not read YAML: {e}"}
    except (PermissionError, ValueError, OSError, UnicodeDecodeError) as e:
        out = {"error": f"{type(e).__name__}: {e}"}
    print(json.dumps(out, indent=1, default=str))
    return 2


def _run(args) -> int:
    if args.cmd == "init":          # creates the vault, so before one is opened
        from .scaffold import init_vault
        out = init_vault(Path(args.folder), args.frontend, example=not args.no_example)
        print(json.dumps(out, indent=1, default=str))
        return 2 if "error" in out else 0
    if args.cmd == "doctor":        # works even where no vault exists yet
        print(json.dumps(doctor_json(), indent=1, default=str))
        return 0
    if args.cmd == "connect":       # the state folder may not exist yet
        state = Path(args.state_dir) if args.state_dir else Path(args.library) / "_learn"
        out = connect_library(Path(args.library), state, args.frontend)
        print(json.dumps(out, indent=1, default=str))
        return 2 if "error" in out else 0
    v = Vault(resolve_root(args.vault, args.state_dir))
    try:
        today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        raise EngineError(f"--date must be YYYY-MM-DD, not '{args.date}'") from None

    if args.cmd == "roadmap":
        return cmd_roadmap(args, v, today)
    if args.cmd == "check-primer":
        out = check_all(v, args.course, validate_diagrams=not args.no_validate)
        print(json.dumps(out, indent=1, default=str))
        return 1 if out["failing"] else 0
    if args.cmd == "where":
        out = {"root": str(v.root.resolve()), "frontend": config.SETTINGS["frontend"],
               "library": str(config.SETTINGS["library"]) if config.SETTINGS["library"] else None,
               "settings_file": v.exists(config.CONFIG_NAME)}
    elif args.cmd == "library-scan":
        out = library_scan(v)
    elif args.cmd == "review-queue":
        rel, text, action = _file_plan(v, REVIEW_QUEUE_REL, review_queue_text(v, today))
        if action != "unchanged" and not args.dry_run:
            v.write_text(rel, text)
        out = {"review_queue": rel, "action": action, "dry_run": args.dry_run}
    elif args.cmd == "index":
        out = write_index(v, today, dry_run=args.dry_run)
    elif args.cmd == "graph":
        out = graph_json(v, canonical_code(args.course))
    elif args.cmd == "next":
        out = next_node(v, _course(v, canonical_code(args.course)))
    elif args.cmd == "unit":
        out = unit_json(v, canonical_code(args.course), args.which)
    elif args.cmd == "due":
        out = due_items(v, args.course, today, args.limit)
    elif args.cmd == "show":
        out = show_json(v, args.note)
    elif args.cmd == "record":
        out = record_json(v, args.note, args.result, today)
    print(json.dumps(out, indent=1, default=str))
    return 0


def doctor_json() -> dict:
    """What the engine has, and what each optional extra would add. Never fails."""
    from . import validate
    problem = None
    try:
        root = resolve_root()
    except (miniyaml.YAMLError, OSError) as e:
        root, problem = Path.cwd(), f"{config.CONFIG_NAME} here could not be read: {e}"
    ok = sys.version_info >= (3, 10)
    cfg = Path(root) / config.CONFIG_NAME
    try:
        settings = (miniyaml.safe_load(cfg.read_text(encoding="utf-8")) or {}) if cfg.is_file() else {}
    except miniyaml.YAMLError:
        settings = {}
    kind = ("library state" if isinstance(settings, dict) and settings.get("library") else
            "vault" if (Path(root) / "Courses").is_dir() else
            "neither: run /learn:setup to make a vault here or connect your notes")
    return {
        "python": {"version": sys.version.split()[0], "ok": ok,
                   **({} if ok else {"fix": "install Python 3.10 or later from https://www.python.org"})},
        "required_packages": "none: the engine uses the standard library only",
        "folder": {"path": str(root), "settings_file": cfg.is_file(), "looks_like": kind,
                   **({"problem": problem} if problem else {})},
        "optional": [
            {"name": "PyYAML", "present": miniyaml._pyyaml is not None,
             "adds": "reads every kind of YAML frontmatter; without it a few rare forms "
                     "(lists of mappings, anchors) are reported as unreadable",
             "install": "python3 -m pip install PyYAML"},
            {"name": "mermaid-cli", "present": validate.available(),
             "adds": "checks every diagram renders before writing it; in plain mode also saves "
                     "roadmaps as SVG images for editors that do not draw Mermaid",
             "install": "npm install -g @mermaid-js/mermaid-cli (needs Node.js)"},
        ],
    }


def show_json(v: Vault, name: str) -> dict:
    rel = _find_note(v, name)
    return {"note": rel, "state": read_state(v, rel).to_json(), "human_authored": v.note(rel).human_authored}


def record_json(v: Vault, name: str, result: str, today: dt.date) -> dict:
    rel = _find_note(v, name)
    before = read_state(v, rel)
    after = apply_result(before, result == "pass", today)
    where = write_state(v, rel, after)
    return {"note": rel, "result": result, "before": before.to_json(),
            "after": after.to_json(), "written_to": where}
