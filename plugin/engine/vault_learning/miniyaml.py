"""YAML for note frontmatter and vault-learning.yaml, with no installs.

`safe_load` uses PyYAML when it is installed (set VL_NO_PYYAML=1 to force the
built-in reader, as the tests do). The built-in reader covers what Obsidian
frontmatter and the engine's settings use, and gives the same Python values
as PyYAML for it (tests/test_miniyaml.py compares the two):

- block mappings, nested by indentation, and block lists (`- item`);
- flow lists and mappings, `["[[A]]", b]` and `{root: "x/", mixed_cap: 1}`;
  an unquoted `[[A]]` reads as a nested list, as in PyYAML;
- plain, single-quoted and double-quoted scalars; null, true/false, integers,
  floats, ISO dates and date-times;
- `|` and `>` block text; comments.

Anything else (anchors, tags, multi-line plain scalars, lists of mappings)
raises YAMLError, which the engine reports as unreadable frontmatter.
"""
from __future__ import annotations

import datetime as dt
import os
import re

try:
    if os.environ.get("VL_NO_PYYAML"):
        raise ImportError
    import yaml as _pyyaml
except ImportError:
    _pyyaml = None


class YAMLError(Exception):
    def __init__(self, problem: str, line: int | None = None):
        super().__init__(problem)
        self.problem = problem
        self.problem_mark = type("Mark", (), {"line": line})() if line is not None else None


def safe_load(text: str):
    if _pyyaml is not None:
        try:
            return _pyyaml.safe_load(text)
        except _pyyaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            raise YAMLError(str(getattr(e, "problem", e)), mark.line if mark else None) from None
        except ValueError as e:       # PyYAML raises this for an impossible date such as 2026-13-40
            raise YAMLError(f"invalid value: {e}") from None
    try:
        return _Reader(text).document()
    except YAMLError:
        raise
    except (TypeError, ValueError, IndexError) as e:   # never crash the engine on an odd note
        raise YAMLError(f"unreadable YAML: {e}") from None


# ---------- scalars ----------
INT_RE = re.compile(r"[-+]?(0|[1-9][0-9_]*)$")
FLOAT_RE = re.compile(r"[-+]?(\d[\d_]*)?\.\d+([eE][-+]?\d+)?$|[-+]?\d[\d_]*[eE][-+]?\d+$")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})$")
DATETIME_RE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})[Tt ](\d{1,2}):(\d{2}):(\d{2})(\.\d+)?"
                         r"\s*(Z|[-+]\d{1,2}(?::?\d{2})?)?$")


def plain_scalar(s: str):
    s = s.strip()
    low = s.lower()
    if s in ("", "~") or low == "null":
        return None
    if low in ("true", "false"):
        return low == "true"
    if INT_RE.match(s):
        return int(s.replace("_", ""))
    if FLOAT_RE.match(s):
        return float(s.replace("_", ""))
    m = DATE_RE.match(s)
    if m:
        try:
            return dt.date(*map(int, m.groups()))
        except ValueError as e:
            raise YAMLError(f"invalid date {s!r}: {e}") from None
    m = DATETIME_RE.match(s)
    if m:
        y, mo, d, h, mi, se = map(int, m.groups()[:6])
        frac, tz = m.group(7), m.group(8)
        micro = int((frac[1:] + "000000")[:6]) if frac else 0
        tzinfo = None
        if tz == "Z":
            tzinfo = dt.timezone.utc
        elif tz:
            sign = -1 if tz[0] == "-" else 1
            hh, _, mm = tz[1:].partition(":")
            if not mm and len(hh) > 2:
                hh, mm = hh[:-2], hh[-2:]
            tzinfo = dt.timezone(sign * dt.timedelta(hours=int(hh), minutes=int(mm or 0)))
        return dt.datetime(y, mo, d, h, mi, se, micro, tzinfo=tzinfo)
    return s


def _double_quoted(body: str) -> str:
    esc = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/", "0": "\0", " ": " "}
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            out.append(esc.get(body[i + 1], "\\" + body[i + 1]))
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _strip_comment(line: str) -> str:
    """Drop a trailing ' # comment' outside quotes."""
    q = None
    for i, c in enumerate(line):
        if q:
            if c == q and not (q == '"' and line[i - 1] == "\\"):
                q = None
        elif c in "\"'" and (i == 0 or line[i - 1] in " [{,:"):
            q = c
        elif c == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


# ---------- flow collections ----------
class _Flow:
    def __init__(self, text: str, line: int):
        self.s, self.i, self.line = text, 0, line

    def err(self, what: str):
        raise YAMLError(what, self.line)

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] in " \t":
            self.i += 1

    def value(self, stops: str):
        self.ws()
        if self.i >= len(self.s):
            return None
        c = self.s[self.i]
        if c == "[":
            return self.seq()
        if c == "{":
            return self.map()
        if c in "\"'":
            return self.quoted()
        start = self.i
        while self.i < len(self.s) and self.s[self.i] not in stops:
            if self.s[self.i] == ":" and self.i + 1 < len(self.s) and self.s[self.i + 1] == " " and "}" in stops:
                break
            self.i += 1
        return plain_scalar(self.s[start:self.i])

    def quoted(self):
        q = self.s[self.i]
        self.i += 1
        out = []
        while self.i < len(self.s):
            c = self.s[self.i]
            if q == "'" and c == "'":
                if self.s[self.i + 1:self.i + 2] == "'":
                    out.append("'"); self.i += 2; continue
                self.i += 1
                return "".join(out)
            if q == '"' and c == "\\":
                out.append(self.s[self.i:self.i + 2]); self.i += 2; continue
            if q == '"' and c == '"':
                self.i += 1
                return _double_quoted("".join(out))
            out.append(c)
            self.i += 1
        self.err("unterminated quoted string")

    def seq(self):
        self.i += 1
        out = []
        while True:
            self.ws()
            if self.i >= len(self.s):
                self.err("unterminated flow list")
            if self.s[self.i] == "]":
                self.i += 1
                return out
            out.append(self.value(",]"))
            self.ws()
            if self.i < len(self.s) and self.s[self.i] == ",":
                self.i += 1

    def map(self):
        self.i += 1
        out = {}
        while True:
            self.ws()
            if self.i >= len(self.s):
                self.err("unterminated flow mapping")
            if self.s[self.i] == "}":
                self.i += 1
                return out
            k = self.value(":,}")
            if isinstance(k, (dict, list)):
                self.err("a mapping key must be a plain value (an Obsidian {{placeholder}}?)")
            self.ws()
            v = None
            if self.i < len(self.s) and self.s[self.i] == ":":
                self.i += 1
                v = self.value(",}")
            out[k] = v
            self.ws()
            if self.i < len(self.s) and self.s[self.i] == ",":
                self.i += 1


def _inline(text: str, line: int):
    """A value written on one line: flow collection, quoted or plain scalar."""
    t = text.strip()
    if not t:
        return None
    if t[0] in "[{\"'":
        f = _Flow(t, line)
        v = f.value("")
        f.ws()
        if f.i != len(t):
            raise YAMLError(f"unexpected text after value: {t[f.i:]!r}", line)
        return v
    if t[0] in "&*!|>%@`":
        raise YAMLError(f"unsupported YAML ({t[0]!r}); install PyYAML to read it", line)
    if ": " in t or t.endswith(":"):
        raise YAMLError("a mapping inside a plain value is not supported", line)
    return plain_scalar(t)


# ---------- block structure ----------
KEY_RE = re.compile(r"""^(?P<key>"(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s#'"][^:]*?)\s*:(?:\s+(?P<rest>.*))?$""")


class _Reader:
    def __init__(self, text: str):
        self.lines = []           # (line number, indent, content)
        for n, raw in enumerate(text.splitlines()):
            if raw.strip().startswith("#") or not raw.strip():
                self.lines.append((n, None, raw))
                continue
            self.lines.append((n, len(raw) - len(raw.lstrip(" ")), raw))
        self.i = 0

    def peek(self):
        while self.i < len(self.lines) and self.lines[self.i][1] is None:
            self.i += 1
        return self.lines[self.i] if self.i < len(self.lines) else None

    def document(self):
        first = self.peek()
        if first is None:
            return None
        if "\t" in first[2][:first[1] + 1]:
            raise YAMLError("tabs are not allowed for indentation", first[0])
        v = self.node(first[1])
        rest = self.peek()
        if rest is not None:
            raise YAMLError("unexpected indentation", rest[0])
        return v

    def node(self, indent: int):
        n, ind, raw = self.peek()
        body = _strip_comment(raw[ind:])
        if body.startswith("- ") or body == "-":
            return self.block_list(ind)
        if KEY_RE.match(body):
            return self.block_map(ind)
        self.i += 1
        return _inline(body, n)

    def block_map(self, indent: int) -> dict:
        out = {}
        while True:
            cur = self.peek()
            if cur is None or cur[1] < indent:
                return out
            n, ind, raw = cur
            if ind > indent:
                raise YAMLError("unexpected indentation", n)
            body = _strip_comment(raw[ind:])
            m = KEY_RE.match(body)
            if not m:
                raise YAMLError(f"expected 'key: value', got {body!r}", n)
            key = _inline(m.group("key"), n) if m.group("key")[0] in "\"'" else plain_scalar(m.group("key"))
            rest = (m.group("rest") or "").strip()
            self.i += 1
            if rest in ("|", ">", "|-", ">-", "|+", ">+"):
                out[key] = self.block_text(indent, rest)
            elif rest:
                out[key] = _inline(rest, n)
            else:
                nxt = self.peek()
                if nxt is not None and (nxt[1] > indent or (nxt[1] == indent and
                                                            _strip_comment(nxt[2][nxt[1]:]).startswith("-"))):
                    out[key] = self.node(nxt[1])
                else:
                    out[key] = None

    def block_list(self, indent: int) -> list:
        out = []
        while True:
            cur = self.peek()
            if cur is None or cur[1] < indent:
                return out
            n, ind, raw = cur
            body = _strip_comment(raw[ind:])
            if ind > indent or not (body.startswith("- ") or body == "-"):
                if ind == indent:
                    return out
                raise YAMLError("unexpected indentation", n)
            item = body[1:].strip()
            if KEY_RE.match(item) and not item.startswith(("[", "{", '"', "'")):
                raise YAMLError("lists of mappings are not supported; install PyYAML to read them", n)
            self.i += 1
            out.append(_inline(item, n))

    def block_text(self, indent: int, style: str) -> str:
        lines = []
        while self.i < len(self.lines):
            n, ind, raw = self.lines[self.i]
            if ind is not None and ind <= indent:
                break
            lines.append(raw)
            self.i += 1
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            return ""
        cut = min(len(l) - len(l.lstrip(" ")) for l in lines if l.strip())
        body = [l[cut:] if l.strip() else "" for l in lines]
        if style[0] == "|":
            text = "\n".join(body)
        else:                         # folded: lines join with spaces, a blank line is a newline
            paras, cur = [], []
            for l in body:
                if l:
                    cur.append(l)
                else:
                    paras.append(" ".join(cur)); cur = []
            paras.append(" ".join(cur))
            text = "\n".join(paras)
        return text if style.endswith("-") else text + "\n"
