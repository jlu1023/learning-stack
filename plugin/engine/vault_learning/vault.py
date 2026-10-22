"""Read-side model of the vault: files, frontmatter, link resolution.

Links may be wikilinks (`[[Note]]`, `[[Path/Note|alias]]`) or Markdown links
(`[text](Note.md)`, `[text](../Other%20Folder/Note.md#Heading)`); a relative
Markdown link resolves from the folder of the note that holds it.

Nothing here writes to the vault except `write_text` (atomic, and refused
outside the vault root, so a connected library is never touched) and
`set_frontmatter_fields`, which edits single `key: value` lines inside an
existing frontmatter block and leaves every other byte of the file alone.
"""
from __future__ import annotations

import os
import posixpath
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

from . import miniyaml as yaml     # PyYAML when installed, else a built-in reader

from . import config

STATE_SUBDIR = "_learn"


def default_vault() -> Path:
    """$VAULT_ROOT when set, else the current directory."""
    return Path(os.environ.get("VAULT_ROOT") or Path.cwd())


def resolve_root(vault: str | None = None, state_dir: str | None = None) -> Path:
    """The folder the engine reads and writes (the vault, or a library's state folder).

    In order: --state-dir, then --vault, then $LEARN_STATE_DIR, then $VAULT_ROOT,
    then a `state_dir:` pointer in ./vault-learning.yaml (relative to this folder
    or absolute), then ./_learn/ when it holds a vault-learning.yaml (library
    mode), then the current folder.
    """
    for p in (state_dir, vault, os.environ.get("LEARN_STATE_DIR"), os.environ.get("VAULT_ROOT")):
        if p:
            return Path(p).expanduser()
    here = Path.cwd()
    cfg = here / config.CONFIG_NAME
    if cfg.is_file():
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict) and data.get("state_dir"):
            return (here / str(data["state_dir"])).expanduser().resolve()
    if (here / STATE_SUBDIR / config.CONFIG_NAME).is_file():
        return here / STATE_SUBDIR
    return here


SKIP_DIRS = {".obsidian", ".smart-env", ".git", ".trash", "node_modules", ".claude"}
FM_RE = re.compile(r"\A---\r?\n(.*?\r?\n)?---[ \t]*(\r?\n|\Z)", re.S)
LINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")
MDLINK_RE = re.compile(r"^\[[^\]\n]*\]\(<?([^)>\n]+?)>?\)$")
MDLINK_ANY_RE = re.compile(r"(?<![!\[])\[[^\]\n]*\]\(<?([^)>\s][^)>\n]*?)>?\)")


@dataclass
class Note:
    rel: str                      # vault-relative posix path, with .md
    fm: dict = field(default_factory=dict)
    fm_error: str | None = None
    body: str = ""

    @property
    def name(self) -> str:
        return Path(self.rel).stem

    @property
    def parts(self) -> list[str]:
        return self.rel.split("/")

    @property
    def type(self) -> str | None:
        t = self.fm.get("type")
        return str(t) if t is not None else None

    @property
    def human_authored(self) -> bool:
        return self.fm.get("human_authored") is True


def parse_frontmatter(text: str) -> tuple[dict, str | None, str]:
    """Return (frontmatter, error, body). Uses a YAML parser, never regex fields."""
    m = FM_RE.match(text)
    if not m:
        return {}, "no-frontmatter", text
    raw = m.group(1) or ""
    body = text[m.end():]
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        where = f" line {mark.line + 1}" if mark else ""
        return {}, f"YAML error{where}: {getattr(e, 'problem', e)}", body
    if not isinstance(data, dict):
        return {}, "frontmatter is not a mapping", body
    return data, None, body


def link_target(raw) -> str:
    """'[[Path/Name|alias]]', '[[Name#heading]]' or '[text](Path/Name.md#h)'
    -> 'Path/Name' / 'Name'. A Markdown link keeps any '../' (see resolve_from)."""
    s = str(raw).strip()
    m = re.fullmatch(r"\[\[(.+?)\]\]", s)
    if m:
        s = m.group(1).split("|", 1)[0]
    else:
        md = MDLINK_RE.match(s)
        if md:
            s = unquote(md.group(1))
    s = s.split("#", 1)[0].strip()
    if s.lower().endswith(".md"):
        s = s[:-3]
    s = s.replace("\\", "/")
    return s[2:] if s.startswith("./") else s


def is_markdown_link(raw) -> bool:
    return bool(MDLINK_RE.match(str(raw).strip()))


def make_link(src_rel: str, dst_rel: str, text: str | None = None) -> str:
    """A link from note `src_rel` to `dst_rel` in the configured style: a
    wikilink for Obsidian, a relative Markdown link for any other editor."""
    name = posixpath.basename(dst_rel)[:-3] if dst_rel.endswith(".md") else posixpath.basename(dst_rel)
    if not config.plain():
        return f"[[{name}]]" if not text or text == name else f"[[{name}|{text}]]"
    rel = posixpath.relpath(dst_rel, posixpath.dirname(src_rel) or ".")
    return f"[{text or name}]({rel.replace(' ', '%20')})"


def as_link_list(value) -> list[str]:
    """Normalise a depends_on / used_in value to a list of raw link strings.

    Unquoted `[[X]]` in YAML parses as a nested list [['X']]; recover it.
    """
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    out = []
    for x in items:
        while isinstance(x, list) and len(x) == 1:
            x = x[0]
        if isinstance(x, list):
            continue
        if x is None:
            continue
        s = str(x).strip()
        out.append(s if s.startswith("[[") or is_markdown_link(s) else f"[[{s}]]")
    return out


class Vault:
    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root else default_vault()
        config.load(self.root)
        self.notes: dict[str, Note] = {}
        self.by_stem: dict[str, list[str]] = defaultdict(list)
        self._by_rel_lower: dict[str, str] = {}
        self._scan()

    def _scan(self) -> None:
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if not fn.lower().endswith(".md"):
                    continue
                p = Path(dirpath) / fn
                rel = p.relative_to(self.root).as_posix()
                self.by_stem[p.stem.lower()].append(rel)
                self._by_rel_lower[rel[:-3].lower()] = rel
                text = p.read_text(encoding="utf-8", errors="replace")
                fm, err, body = parse_frontmatter(text)
                self.notes[rel] = Note(rel, fm, err, body)

    def note(self, rel: str) -> Note:
        """Course notes are pre-parsed; anything else is parsed on demand."""
        if rel not in self.notes:
            text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
            fm, err, body = parse_frontmatter(text)
            self.notes[rel] = Note(rel, fm, err, body)
        return self.notes[rel]

    def resolve(self, target: str) -> list[str]:
        """All files a link target could mean. Path-qualified links resolve by
        path suffix, bare links by filename. Never guesses between candidates."""
        t = link_target(target)
        if not t:
            return []
        if "/" in t:
            tl = t.lower()
            return sorted(r for k, r in self._by_rel_lower.items()
                          if k == tl or k.endswith("/" + tl))
        return sorted(self.by_stem.get(t.lower(), []))

    def resolve_from(self, src_rel: str, target: str) -> list[str]:
        """As resolve, but a relative Markdown link ('../x/Note.md') resolves from
        the folder of `src_rel` first, as any Markdown viewer would."""
        if is_markdown_link(target):
            t = link_target(target)
            joined = posixpath.normpath(posixpath.join(posixpath.dirname(src_rel), t)).lower()
            if joined in self._by_rel_lower:
                return [self._by_rel_lower[joined]]
            if t.startswith("../"):
                return []
        return self.resolve(target)

    def is_unique_name(self, name: str) -> bool:
        return len(self.by_stem.get(name.lower(), [])) == 1

    def exists(self, rel: str) -> bool:
        return (self.root / rel).is_file()

    def read_text(self, rel: str) -> str:
        # bytes then decode: Path.read_text would translate CRLF to LF, and every
        # rewrite would then silently change a note's line endings
        return (self.root / rel).read_bytes().decode("utf-8")

    def write_text(self, rel: str, text: str) -> None:
        path = self.root / rel
        if not path.resolve().is_relative_to(self.root.resolve()):
            # the guard that keeps a connected library read-only
            raise PermissionError(f"refusing to write outside {self.root}: {rel}")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)


def owner_label(rel: str) -> str:
    """Short label for where a note lives: course code, or top-level folder."""
    parts = rel.split("/")
    if parts[0] == "Courses" and len(parts) > 2:
        return parts[1]
    for code, spec in config.EXTRA_COURSES.items():
        if rel.startswith(spec.root):
            return code
    return parts[0]


def _yaml_scalar(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if re.fullmatch(r"[A-Za-z0-9_.:-]+", s):
        return s
    return '"' + s.replace('"', '\\"') + '"'


def set_frontmatter_fields(text: str, fields: dict) -> str:
    """Set scalar fields in an existing frontmatter block, line-surgically.

    Existing `key: ...` lines are replaced in place; new keys are appended just
    before the closing `---`. Multi-line values for these keys are not
    supported (the learner-state fields are all scalars). Nothing else changes.
    """
    m = FM_RE.match(text)
    if not m:
        raise ValueError("note has no frontmatter block")
    block = m.group(1) or ""
    block_start = text.index("\n") + 1          # just after the opening '---' line
    closing = m.end(1) if m.group(1) is not None else block_start   # start of the closing '---'
    # keep every line's own ending: some notes mix CRLF delimiters with LF fields
    lines = block.splitlines(keepends=True)
    ending = lambda l: l[len(l.rstrip("\r\n")):]  # noqa: E731
    default_nl = ending(lines[-1]) if lines else ("\r\n" if "\r\n" in text[: m.end()] else "\n")
    done = set()
    for i, line in enumerate(lines):
        km = re.match(r"^([A-Za-z_][\w-]*):", line)
        if km and km.group(1) in fields:
            key = km.group(1)
            # refuse to clobber a block value that continues on the next lines
            if i + 1 < len(lines) and re.match(r"^(\s+|- )", lines[i + 1]) and line.rstrip().endswith(":"):
                raise ValueError(f"field {key!r} has a block value; refusing to edit")
            lines[i] = f"{key}: {_yaml_scalar(fields[key])}" + (ending(line) or default_nl)
            done.add(key)
    for key, val in fields.items():
        if key not in done:
            lines.append(f"{key}: {_yaml_scalar(val)}{default_nl}")
    # everything before the block (the opening '---' and its ending) and from
    # the closing '---' onwards is kept byte for byte
    return text[:block_start] + "".join(lines) + text[closing:]
