"""Proof track: each proof note's own level, scaffold stage and review date.

A proof folds into its theorem for the graph, but writing a proof is practised
apart from recalling the theorem: lock-ins and reviews ask only for a proof's
key idea, and proofs get their own spaced track. So a proof note carries its
own state, in proof-prefixed fields:

  proof_level    unseen | learning | secure | mastered   (missing = unseen)
  proof_since    ISO date the current proof_level was reached
  proof_last     ISO date of the last attempt
  proof_review   ISO date the proof is next due
  proof_stage    the scaffold stage to attempt next, 1 to 4 (missing = 1):
                 1 step by step, 2 name the chain of moves then write,
                 3 from the key line, 4 solo
  proof_streak   consecutive fails (missing = 0)
  proof_solo     consecutive stage 4 passes (missing = 0)

Rules: a pass moves the next stage up one (capped at 4) and is due again in 3
days; a stage 4 pass is due in 21 days, or 60 from the second stage 4 pass in
a row. A fail moves the stage down one (floor 1) and is due in 2 days. Levels:
unseen to learning on the first pass, to secure on the first stage 4 pass, to
mastered on a stage 4 pass at least 21 days after secure. The level drops one
on the second fail in a row, never below learning once reached.

A proof is any note the graph classes as one (`type: proof`, or a name starting
`Proof - `), so in library mode a card named `Proof - <Card>` is on the track
too, its state in the card's frontmatter like any card's. State goes to the
note's frontmatter, or to `proof-progress.md` for a `human_authored: true` note.
`updated:` is never bumped.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, asdict

from .state import FAILS_TO_DROP, LEARNING_DIR, LEVELS, MASTERED_AFTER_DAYS, _date, read_progress, read_state
from .vault import Vault, set_frontmatter_fields

PROOF_FIELDS = ["proof_level", "proof_since", "proof_last", "proof_review",
                "proof_stage", "proof_streak", "proof_solo"]
PROOF_PROGRESS_REL = f"{LEARNING_DIR}/proof-progress.md"
SESSIONS_DIR = f"{LEARNING_DIR}/sessions"
STAGES = (1, 2, 3, 4)
PASS_DAYS = 3
SOLO_DAYS = (21, 60)
FAIL_DAYS = 2


def _int(x, default: int) -> int:
    try:
        return int(x) if x not in (None, "") else default
    except (TypeError, ValueError):
        return default


@dataclass
class ProofState:
    proof_level: str = "unseen"
    proof_since: dt.date | None = None
    proof_last: dt.date | None = None
    proof_review: dt.date | None = None
    proof_stage: int = 1
    proof_streak: int = 0
    proof_solo: int = 0

    @classmethod
    def from_mapping(cls, d: dict) -> "ProofState":
        lvl = str(d.get("proof_level") or "unseen").strip().lower()
        if lvl not in LEVELS:
            lvl = "unseen"
        stage = min(max(_int(d.get("proof_stage"), 1), 1), 4)
        return cls(lvl, _date(d.get("proof_since")), _date(d.get("proof_last")),
                   _date(d.get("proof_review")), stage,
                   max(_int(d.get("proof_streak"), 0), 0), max(_int(d.get("proof_solo"), 0), 0))

    def to_fields(self) -> dict:
        iso = lambda d: d.isoformat() if d else ""  # noqa: E731
        return {"proof_level": self.proof_level, "proof_since": iso(self.proof_since),
                "proof_last": iso(self.proof_last), "proof_review": iso(self.proof_review),
                "proof_stage": self.proof_stage, "proof_streak": self.proof_streak,
                "proof_solo": self.proof_solo}

    def to_json(self) -> dict:
        return {k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in asdict(self).items()}


def apply_proof_result(s: ProofState, passed: bool, stage: int, today: dt.date) -> ProofState:
    """Pure transition for one attempt at `stage` (1 to 4); the method skill, Proof track."""
    if stage not in STAGES:
        raise ValueError(f"stage must be 1 to 4, not {stage}")
    n = ProofState(**asdict(s))
    n.proof_last = today
    lvl = LEVELS.index(s.proof_level)
    if passed:
        n.proof_streak = 0
        n.proof_stage = min(stage + 1, 4)
        if s.proof_level == "unseen":
            n.proof_level, n.proof_since = "learning", today
        if stage == 4:
            n.proof_solo = s.proof_solo + 1
            days = SOLO_DAYS[0] if n.proof_solo == 1 else SOLO_DAYS[1]
            if n.proof_level == "learning":
                n.proof_level, n.proof_since = "secure", today
            elif (n.proof_level == "secure" and s.proof_since
                  and (today - s.proof_since).days >= MASTERED_AFTER_DAYS):
                n.proof_level, n.proof_since = "mastered", today
        else:
            n.proof_solo = 0
            days = PASS_DAYS
    else:
        n.proof_streak = s.proof_streak + 1
        n.proof_stage = max(stage - 1, 1)
        n.proof_solo = 0
        days = FAIL_DAYS
        if n.proof_streak >= FAILS_TO_DROP:
            if lvl > 1:     # never below learning once reached; unseen stays unseen
                n.proof_level, n.proof_since = LEVELS[lvl - 1], today
            n.proof_streak = 0
    n.proof_review = today + dt.timedelta(days=days)
    return n


# ---------- storage ----------
PROOF_PROGRESS_HEADER = ("---\ntitle: \"proof-progress\"\ntype: reference\n---\n\n"
                         "# Proof-track store for human-authored proofs\n\n"
                         "Written only by the engine's `record`; do not edit rows by hand.\n\n"
                         "| Note | Path | " + " | ".join(PROOF_FIELDS) + " |\n"
                         "|---|---|" + "---|" * len(PROOF_FIELDS) + "\n")


def _row_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def read_proof_progress(v: Vault) -> dict[str, ProofState]:
    if not v.exists(PROOF_PROGRESS_REL):
        return {}
    out = {}
    for line in v.read_text(PROOF_PROGRESS_REL).splitlines():
        cells = _row_cells(line)
        if len(cells) != 2 + len(PROOF_FIELDS) or cells[0] == "Note" or set(cells[0]) <= {"-"}:
            continue
        out[cells[1]] = ProofState.from_mapping(dict(zip(PROOF_FIELDS, cells[2:])))
    return out


def read_proof_state(v: Vault, rel: str, progress: dict | None = None) -> ProofState:
    note = v.note(rel)
    if note.human_authored:
        progress = read_proof_progress(v) if progress is None else progress
        return progress.get(rel, ProofState())
    return ProofState.from_mapping(note.fm)


def write_proof_state(v: Vault, rel: str, s: ProofState) -> str:
    """Returns where the state went: 'frontmatter' or 'proof-progress'."""
    note = v.note(rel)
    f = s.to_fields()
    if note.human_authored:
        text = v.read_text(PROOF_PROGRESS_REL) if v.exists(PROOF_PROGRESS_REL) else PROOF_PROGRESS_HEADER
        row = f"| {note.name} | {rel} | " + " | ".join(str(f[k]) for k in PROOF_FIELDS) + " |"
        lines = text.splitlines()
        for i, line in enumerate(lines):
            cells = _row_cells(line)
            if len(cells) == 2 + len(PROOF_FIELDS) and cells[1] == rel:
                lines[i] = row
                break
        else:
            last = max((i for i, l in enumerate(lines) if l.startswith("|")), default=len(lines) - 1)
            lines.insert(last + 1, row)
        v.write_text(PROOF_PROGRESS_REL, "\n".join(lines) + "\n")
        return "proof-progress"
    fields = {k: val for k, val in f.items() if val != ""}
    v.write_text(rel, set_frontmatter_fields(v.read_text(rel), fields))
    return "frontmatter"


# ---------- queries ----------
def tested_units(v: Vault, code: str) -> set[int]:
    """Units with a unit-test session file (`YYYY-MM-DD <CODE> Unit <N> test.md`)."""
    folder = v.root / SESSIONS_DIR
    if not folder.is_dir():
        return set()
    pat = re.compile(rf"^\d{{4}}-\d{{2}}-\d{{2}} {re.escape(code)} Unit (\d+) test\.md$", re.I)
    return {int(m.group(1)) for p in folder.iterdir() if (m := pat.match(p.name))}


def proofs_due(v: Vault, courses: list[str], today: dt.date, limit: int = 0) -> dict:
    """Due proofs (proof_review today or earlier), most overdue first, then new ones:
    never attempted, with their theorem at learning or better (a proof with no theorem
    note: every prerequisite at learning or better). New proofs from units that have
    had their unit test come first."""
    from .graph import CourseGraph
    from .units import CourseUnits

    progress, pprogress = read_progress(v), read_proof_progress(v)
    learned = lambda rel: LEVELS.index(read_state(v, rel, progress).mastery) >= 1  # noqa: E731
    due, new = [], []
    for code in courses:
        cg = CourseGraph(v, code)
        units = CourseUnits(v, code, cg)
        tested = tested_units(v, code)
        order = {n: i for i, n in enumerate(cg.suggested_order())}
        for rel, k in cg.kind.items():
            if k != "proof":
                continue
            ps = read_proof_state(v, rel, pprogress)
            theorem = cg.proof_of.get(rel)
            anchor = theorem or rel
            unit = units.unit_of.get(anchor)
            item = {"course": code, "name": cg.name(rel), "path": rel,
                    "theorem": cg.name(theorem) if theorem else None, "unit": unit,
                    "unit_tested": unit in tested, "state": ps.to_json()}
            if ps.proof_review:
                if ps.proof_review <= today:
                    item["overdue_days"] = (today - ps.proof_review).days
                    due.append(item)
                continue
            ready = learned(theorem) if theorem else (
                rel in cg.G and all(learned(p) for p in cg.G.predecessors(rel)))
            if ready:
                new.append((not item["unit_tested"], code, order.get(anchor, len(order)), item))
    due.sort(key=lambda x: (-x["overdue_days"], x["state"]["proof_last"] or ""))
    new = [t[-1] for t in sorted(new, key=lambda t: t[:3])]
    return {"date": today.isoformat(), "due": due[:limit] if limit else due, "due_total": len(due),
            "new": new[:limit] if limit else new, "new_total": len(new)}
