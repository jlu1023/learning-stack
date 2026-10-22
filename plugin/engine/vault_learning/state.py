"""Learner state: mastery transitions, review ladder, due and next queries.

Fields (note frontmatter, or the progress store for human_authored notes):
  mastery          unseen | learning | secure | mastered   (missing = unseen)
  mastery_since    ISO date the current mastery level was reached
  last_quizzed     ISO date of the last lock-in or review attempt
  review           ISO date of the next review (the schema's existing field)
  review_interval  days, current rung of the 1, 3, 7, 21, 60 ladder

`updated:` is never bumped by a learner-state write: it means the content changed.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, asdict

from .vault import Vault, set_frontmatter_fields

LEVELS = ["unseen", "learning", "secure", "mastered"]
LADDER = [1, 3, 7, 21, 60]
SECURE_AFTER_DAYS = 3
MASTERED_AFTER_DAYS = 21
FIELDS = ["mastery", "mastery_since", "last_quizzed", "review", "review_interval"]
LEARNING_DIR = "Courses/_learning"
PROGRESS_REL = f"{LEARNING_DIR}/progress.md"
ERROR_LOG_REL = f"{LEARNING_DIR}/Error Log.md"


def _date(x) -> dt.date | None:
    if x is None or x == "":
        return None
    if isinstance(x, dt.datetime):
        return x.date()
    if isinstance(x, dt.date):
        return x
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(x))
    return dt.date.fromisoformat(m.group(1)) if m else None


@dataclass
class State:
    mastery: str = "unseen"
    mastery_since: dt.date | None = None
    last_quizzed: dt.date | None = None
    review: dt.date | None = None
    review_interval: int | None = None

    @classmethod
    def from_mapping(cls, d: dict) -> "State":
        m = str(d.get("mastery") or "unseen").strip().lower()
        if m not in LEVELS:
            m = "unseen"
        ri = d.get("review_interval")
        try:
            ri = int(ri) if ri not in (None, "") else None
        except (TypeError, ValueError):
            ri = None
        return cls(m, _date(d.get("mastery_since")), _date(d.get("last_quizzed")),
                   _date(d.get("review")), ri)

    def to_fields(self) -> dict:
        return {
            "mastery": self.mastery,
            "mastery_since": self.mastery_since.isoformat() if self.mastery_since else "",
            "last_quizzed": self.last_quizzed.isoformat() if self.last_quizzed else "",
            "review": self.review.isoformat() if self.review else "",
            "review_interval": self.review_interval if self.review_interval else "",
        }

    def to_json(self) -> dict:
        d = asdict(self)
        return {k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in d.items()}


def apply_result(s: State, passed: bool, today: dt.date) -> State:
    """Pure transition function; the method skill, 'Spacing and interleaving'."""
    lvl = LEVELS.index(s.mastery)
    n = State(**asdict(s))
    n.last_quizzed = today
    if passed:
        if s.mastery == "unseen":
            n.mastery, n.mastery_since, n.review_interval = "learning", today, LADDER[0]
        else:
            since = s.mastery_since or today
            if s.mastery == "learning" and (today - since).days >= SECURE_AFTER_DAYS:
                n.mastery, n.mastery_since = "secure", today
            elif s.mastery == "secure" and (today - since).days >= MASTERED_AFTER_DAYS:
                n.mastery, n.mastery_since = "mastered", today
            cur = s.review_interval or LADDER[0]
            higher = [x for x in LADDER if x > cur]
            n.review_interval = higher[0] if higher else LADDER[-1]
    else:
        if lvl > 0:
            n.mastery, n.mastery_since = LEVELS[lvl - 1], today
        n.review_interval = LADDER[0]
    n.review = today + dt.timedelta(days=n.review_interval)
    return n


# ---------- progress store (human_authored notes) ----------
PROGRESS_HEADER = ("| Note | Path | mastery | mastery_since | last_quizzed | review | review_interval |\n"
                   "|---|---|---|---|---|---|---|\n")


def read_progress(v: Vault) -> dict[str, State]:
    if not v.exists(PROGRESS_REL):
        return {}
    out = {}
    for line in v.read_text(PROGRESS_REL).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7 or cells[0] in ("Note", "---") or set(cells[0]) <= {"-"}:
            continue
        out[cells[1]] = State.from_mapping(dict(zip(FIELDS, cells[2:])))
    return out


def write_progress_row(v: Vault, rel: str, s: State) -> None:
    text = v.read_text(PROGRESS_REL)
    f = s.to_fields()
    name = rel.rsplit("/", 1)[-1][:-3]
    row = f"| {name} | {rel} | " + " | ".join(str(f[k]) for k in FIELDS) + " |"
    lines = text.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and cells[1] == rel:
            lines[i] = row
            break
    else:
        # append after the last table row
        last = max((i for i, l in enumerate(lines) if l.startswith("|")), default=len(lines) - 1)
        lines.insert(last + 1, row)
    v.write_text(PROGRESS_REL, "\n".join(lines) + "\n")


def read_state(v: Vault, rel: str, progress: dict[str, State] | None = None) -> State:
    note = v.note(rel)
    if note.human_authored:
        progress = read_progress(v) if progress is None else progress
        return progress.get(rel, State())
    return State.from_mapping(note.fm)


def write_state(v: Vault, rel: str, s: State) -> str:
    """Returns where the state went: 'frontmatter' or 'progress'."""
    note = v.note(rel)
    if note.human_authored:
        write_progress_row(v, rel, s)
        return "progress"
    text = v.read_text(rel)
    # empty values are not written: a missing field reads the same as an empty one
    fields = {k: val for k, val in s.to_fields().items() if val != ""}
    new = set_frontmatter_fields(text, fields)
    v.write_text(rel, new)
    return "frontmatter"


# ---------- error log ----------
ENTRY_RE = re.compile(r"^\s*-\s.*\[date::\s*(\d{4}-\d{2}-\d{2})\]")
FIELD_RE = re.compile(r"\[(\w+)::\s*([^\]]*)\]")


def read_error_log(v: Vault) -> list[dict]:
    if not v.exists(ERROR_LOG_REL):
        return []
    out = []
    for line in v.read_text(ERROR_LOG_REL).splitlines():
        if ENTRY_RE.match(line):
            d = {k: val.strip() for k, val in FIELD_RE.findall(line)}
            out.append(d)
    return out
