"""Per-course dependency graph built from `depends_on`.

Edges point prerequisite -> dependent. Proofs are folded into the theorem they
prove: a proof's own `depends_on` becomes part of its theorem's prerequisites,
and anything that depends on a proof depends on its theorem instead. Examples
and Evidence notes are kept aside and only drawn in module diagrams.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import networkx as nx

from .config import EXTRA_COURSES, REFERENCE_COURSES, CourseSpec
from .vault import Note, Vault, as_link_list, link_target, owner_label

CORE_TYPES = {"definition", "theorem", "lemma", "method", "concept",
              "intuition", "axiom", "corollary", "proposition", "card"}
THEOREM_TYPES = {"theorem", "lemma", "corollary", "proposition"}
SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)")
THEOREM_LINE_RE = re.compile(r"^\*\*Theorem:\*\*\s*(\[\[[^\]]+\]\]|\[[^\]\n]*\]\([^)\n]+\))", re.M)
PART_RE = re.compile(r"\s*\((?:part|Part)\s*[^)]*\)\s*$")


def kind_of(note: Note) -> str:
    t = note.type
    if t == "moc":
        return "moc"
    if t == "proof" or note.name.startswith("Proof - "):
        return "proof"
    if t == "example" or note.name.startswith(("Example - ", "Evidence - ")):
        return "example"
    if t in CORE_TYPES:
        return "core"
    return "other"


def section_key(section) -> tuple:
    if section is None:
        return ()
    m = SECTION_RE.match(str(section))
    return tuple(int(x) for x in m.group(1).split(".")) if m else ()


# Courses that live outside Courses/<CODE>/ come from the vault's settings
# (config.EXTRA_COURSES). As for a Courses/ course, the course MOC is
# '<root><CODE> Syllabus.md', the roadmap '<root><CODE> Roadmap.md', and each
# top-level folder under root (minus `exclude`) is a module.


def canonical_code(code: str) -> str:
    """A registered course keeps its own spelling (any case matches); others are upper-cased."""
    for k in EXTRA_COURSES:
        if k.upper() == code.upper():
            return k
    return code.upper()


def course_spec(code: str) -> CourseSpec:
    code = canonical_code(code)
    return EXTRA_COURSES.get(code) or CourseSpec(root=f"Courses/{code}/")


def course_moc_rel(code: str) -> str:
    code = canonical_code(code)
    return f"{course_spec(code).root}{code} Syllabus.md"


def in_any_course(rel: str) -> bool:
    """True for a note inside some course: Courses/<CODE>/... or a registered root,
    outside that root's excluded folders."""
    if rel.startswith("Courses/"):
        return True
    for spec in EXTRA_COURSES.values():
        if rel.startswith(spec.root):
            return rel[len(spec.root):].split("/")[0] not in spec.exclude
    return False


def module_number(folder: str) -> int:
    m = re.match(r"^(\d+)\s", folder)
    return int(m.group(1)) if m else 10**6


@dataclass
class Module:
    folder: str
    moc_rel: str | None
    notes: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.folder


@dataclass
class Gaps:
    yaml_errors: list[tuple[str, str]] = field(default_factory=list)
    missing: list[tuple[str, str, str]] = field(default_factory=list)      # (note, field, target)
    ambiguous: list[tuple[str, str, str, list[str]]] = field(default_factory=list)
    no_depends_on: list[str] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)
    module_cycles: list[list[str]] = field(default_factory=list)
    proofs_external_theorem: list[tuple[str, str]] = field(default_factory=list)
    proofs_unattached: list[str] = field(default_factory=list)
    examples_unanchored: list[str] = field(default_factory=list)
    example_as_prereq: list[tuple[str, str]] = field(default_factory=list)
    used_in_without_depends_on: list[tuple[str, str]] = field(default_factory=list)
    depends_on_without_used_in: int = 0
    other_types: list[tuple[str, str]] = field(default_factory=list)


class CourseGraph:
    def __init__(self, vault: Vault, code: str):
        self.v = vault
        self.code = code = canonical_code(code)
        spec = course_spec(code)
        self.prefix = spec.root
        self.exclude = set(spec.exclude)
        self.depth = self.prefix.count("/") + 1     # slashes in a module note's path
        self.course_moc = f"{self.prefix}{code} Syllabus.md"
        self.roadmap_rel = f"{self.prefix}{code} Roadmap.md"
        self.gaps = Gaps()
        self.modules: list[Module] = []
        self.module_of: dict[str, str] = {}
        self.kind: dict[str, str] = {}
        self.proof_of: dict[str, str] = {}          # proof rel -> theorem rel (in course)
        self.proofs_for: dict[str, list[str]] = defaultdict(list)
        self.nodes: list[str] = []                  # core + unattached proofs
        self.examples: list[str] = []
        self.G = nx.DiGraph()                       # in-course, prerequisite -> dependent
        self.ext: dict[str, set[str]] = defaultdict(set)   # node -> external prereq rels
        self.example_anchor: dict[str, set[str]] = defaultdict(set)
        self.example_feeds: dict[str, set[str]] = defaultdict(set)  # example -> dependents
        self.back_edges: set[tuple[str, str]] = set()
        self._build()

    # ---------- helpers ----------
    def note(self, rel: str) -> Note:
        return self.v.note(rel)

    def name(self, rel: str) -> str:
        return rel.rsplit("/", 1)[-1][:-3]

    def in_course(self, rel: str) -> bool:
        return rel.startswith(self.prefix) and self._folder(rel) not in self.exclude

    def _folder(self, rel: str) -> str:
        return rel[len(self.prefix):].split("/")[0]

    def _module_note(self, rel: str) -> bool:
        return rel.startswith(self.prefix) and rel.count("/") >= self.depth \
            and self._folder(rel) not in self.exclude

    def _resolve_one(self, src: str, fld: str, raw: str) -> str | None:
        hits = self.v.resolve_from(src, raw)
        tgt = link_target(raw)
        if not hits:
            self.gaps.missing.append((self.name(src), fld, tgt))
            return None
        if len(hits) > 1:
            self.gaps.ambiguous.append((self.name(src), fld, tgt, hits))
            return None
        return hits[0]

    def fold(self, rel: str) -> str:
        return self.proof_of.get(rel, rel)

    # ---------- build ----------
    def _build(self) -> None:
        v = self.v
        folders = sorted({self._folder(r) for r in v.notes if self._module_note(r)},
                         key=lambda f: (module_number(f), f))
        for f in folders:
            moc = f"{self.prefix}{f}/{f}.md"
            self.modules.append(Module(f, moc if v.exists(moc) else None))
        mod_by_folder = {m.folder: m for m in self.modules}

        for rel, note in sorted(v.notes.items()):
            if not self._module_note(rel):
                continue
            folder = self._folder(rel)
            mod = mod_by_folder[folder]
            if rel == mod.moc_rel:
                continue
            if note.fm_error:
                self.gaps.yaml_errors.append((note.name, note.fm_error))
            k = kind_of(note)
            self.kind[rel] = k
            self.module_of[rel] = folder
            mod.notes.append(rel)
            if k == "other":
                self.gaps.other_types.append((note.name, str(note.type)))

        # attach proofs to theorems
        for rel, k in self.kind.items():
            if k != "proof":
                continue
            note = self.note(rel)
            cands = []
            m = THEOREM_LINE_RE.search(note.body)
            if m:
                cands.append(m.group(1))
            if note.name.startswith("Proof - "):
                bare = note.name[len("Proof - "):]
                cands += [bare, PART_RE.sub("", bare)]
            attached, external = None, None
            for c in cands:
                hits = v.resolve_from(rel, c)
                if len(hits) != 1:
                    continue
                h = hits[0]
                if self.in_course(h) and self.kind.get(h) == "core":
                    attached = h
                    break
                if not self.in_course(h) and external is None:
                    external = h
            if attached:
                self.proof_of[rel] = attached
                self.proofs_for[attached].append(rel)
            elif external:
                self.gaps.proofs_external_theorem.append((note.name, external[:-3]))
            else:
                self.gaps.proofs_unattached.append(note.name)

        self.nodes = [r for r, k in self.kind.items()
                      if k == "core" or (k == "proof" and r not in self.proof_of)]
        self.examples = [r for r, k in self.kind.items() if k == "example"]
        self.G.add_nodes_from(self.nodes)

        # edges from depends_on (node + its folded proofs)
        for rel, k in self.kind.items():
            note = self.note(rel)
            deps = as_link_list(note.fm.get("depends_on"))
            if not deps and k in ("core",):
                self.gaps.no_depends_on.append(note.name)
            target_node = self.fold(rel)
            for raw in deps:
                h = self._resolve_one(rel, "depends_on", raw)
                if h is None:
                    continue
                if self.in_course(h):
                    hk = self.kind.get(h)
                    if hk is None:          # course MOC, roadmap, etc.
                        continue
                    if hk == "example":
                        if k != "example":
                            self.gaps.example_as_prereq.append((note.name, self.name(h)))
                            self.example_feeds[h].add(target_node)
                        continue
                    src = self.fold(h)
                    if k == "example":
                        self.example_anchor[rel].add(src)
                        continue
                    if src != target_node:
                        self.G.add_edge(src, target_node)
                else:
                    if k == "example":
                        continue
                    self.ext[target_node].add(h)

        for rel in self.examples:
            if not self.example_anchor.get(rel) and not self.example_feeds.get(rel):
                self.gaps.examples_unanchored.append(self.name(rel))

        # used_in / depends_on consistency, both directions
        for rel, k in self.kind.items():
            note = self.note(rel)
            for raw in as_link_list(note.fm.get("used_in")):
                h = self._resolve_one(rel, "used_in", raw)
                if h is None or not self.v.exists(h):
                    continue
                other = self.note(h)
                back = {x for r2 in as_link_list(other.fm.get("depends_on"))
                        for x in self.v.resolve_from(h, r2)}
                if rel not in back:
                    self.gaps.used_in_without_depends_on.append((note.name, other.name))
            for raw in as_link_list(note.fm.get("depends_on")):
                hits = self.v.resolve_from(rel, raw)
                if len(hits) != 1 or not self.in_course(hits[0]) or hits[0] not in self.kind:
                    continue
                pre = self.note(hits[0])
                fwd = {x for r2 in as_link_list(pre.fm.get("used_in")) for x in self.v.resolve_from(hits[0], r2)}
                if rel not in fwd:
                    self.gaps.depends_on_without_used_in += 1

        # cycles: report, and pick back-edges for drawing only
        for comp in nx.strongly_connected_components(self.G):
            if len(comp) > 1:
                sub = self.G.subgraph(comp)
                for cyc in nx.simple_cycles(sub):
                    self.gaps.cycles.append([self.name(x) for x in cyc])
                order = sorted(comp, key=self.sort_key)
                pos = {n: i for i, n in enumerate(order)}
                for u, w in sub.edges():
                    if pos[u] >= pos[w]:
                        self.back_edges.add((u, w))
        mg = self.module_graph()
        for cyc in nx.simple_cycles(mg):
            if len(cyc) > 1:
                # start at the first module in syllabus order, so the report is stable
                i = min(range(len(cyc)), key=lambda j: (module_number(cyc[j]), cyc[j]))
                self.gaps.module_cycles.append(cyc[i:] + cyc[:i])

    # ---------- ordering ----------
    def _moc_index(self, rel: str) -> int:
        folder = self.module_of.get(rel)
        mod = next((m for m in self.modules if m.folder == folder), None)
        if not mod or not mod.moc_rel:
            return 10**6
        body = self.note(mod.moc_rel).body.lower()
        nm = self.name(rel).lower()
        idx = [i for i in (body.find(f"[[{nm}]]"), body.find(f"[[{nm}|")) if i >= 0]
        return min(idx) if idx else 10**6

    def sort_key(self, rel: str):
        note = self.note(rel)
        sk = section_key(note.fm.get("section"))
        return (sk if sk else (10**6,), self._moc_index(rel), self.name(rel).lower())

    def acyclic(self) -> nx.DiGraph:
        g = self.G.copy()
        g.remove_edges_from(self.back_edges)
        return g

    def module_order(self, folder: str) -> list[str]:
        g = self.acyclic()
        members = [n for n in self.nodes if self.module_of[n] == folder]
        sub = g.subgraph(members)
        return list(nx.lexicographical_topological_sort(sub, key=lambda r: self.sort_key(r)))

    def suggested_order(self) -> list[str]:
        out = []
        for m in self.modules:
            out += self.module_order(m.folder)
        return out

    # ---------- summaries ----------
    def module_graph(self) -> nx.DiGraph:
        mg = nx.DiGraph()
        mg.add_nodes_from(m.folder for m in self.modules)
        for u, w in self.G.edges():
            a, b = self.module_of[u], self.module_of[w]
            if a != b:
                c = mg.get_edge_data(a, b, {}).get("n", 0)
                mg.add_edge(a, b, n=c + 1)
        return mg

    def dependents_count(self) -> dict[str, int]:
        g = self.acyclic()
        return {n: len(nx.descendants(g, n)) for n in self.nodes}

    def spine(self, lo: int = 10, hi: int = 20, target: int = 15) -> list[tuple[str, int]]:
        counts = self.dependents_count()
        ranked = sorted(((n, c) for n, c in counts.items() if c > 0),
                        key=lambda x: (-x[1], self.sort_key(x[0])))
        k = min(max(lo, min(target, len(ranked))), hi, len(ranked))
        return ranked[:k]

    def external_prereqs(self) -> dict[str, dict[str, set[str]]]:
        """owner -> external rel -> dependent node rels."""
        out: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for node, exts in self.ext.items():
            for e in exts:
                out[owner_label(e)][e].add(node)
        return out

    def used_outside(self) -> dict[str, dict[str, set[str]]]:
        """owner -> outside rel -> course notes it builds on (from outside
        depends_on pointing in, and this course's used_in pointing out)."""
        out: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for rel, note in self.v.notes.items():
            if self.in_course(rel):
                continue
            for raw in as_link_list(note.fm.get("depends_on")):
                hits = self.v.resolve_from(rel, raw)
                if len(hits) == 1 and self.in_course(hits[0]) and hits[0] in self.kind:
                    out[owner_label(rel)][rel].add(self.fold(hits[0]))
        for rel, k in self.kind.items():
            for raw in as_link_list(self.note(rel).fm.get("used_in")):
                hits = self.v.resolve_from(rel, raw)
                if len(hits) == 1 and not self.in_course(hits[0]):
                    out[owner_label(hits[0])][hits[0]].add(self.fold(rel))
        return out

    def stats(self) -> dict:
        content = [r for r, k in self.kind.items() if k != "moc"]   # primers are not content
        with_dep = sum(1 for r in content if as_link_list(self.note(r).fm.get("depends_on")))
        ext_edges = Counter()
        for node, exts in self.ext.items():
            for e in exts:
                ext_edges[owner_label(e)] += 1
        return {
            "content_notes": len(content),
            "with_depends_on": with_dep,
            "nodes": len(self.nodes),
            "proofs_folded": len(self.proof_of),
            "examples": len(self.examples),
            "in_course_edges": self.G.number_of_edges(),
            "external_edges": dict(ext_edges),
            "missing": len(self.gaps.missing),
            "ambiguous": len(self.gaps.ambiguous),
            "cycles": len(self.gaps.cycles),
            "used_in_without_depends_on": len(self.gaps.used_in_without_depends_on),
            "depends_on_without_used_in": self.gaps.depends_on_without_used_in,
            "yaml_errors": len(self.gaps.yaml_errors),
        }


def roadmap_courses(vault: Vault) -> list[str]:
    """Every Courses/<CODE>/ with a '<CODE> Syllabus.md', minus the reference
    courses (they appear only as external prerequisites), then each registered
    course (EXTRA_COURSES) whose course MOC exists."""
    out = []
    base = vault.root / "Courses"
    for d in sorted(base.iterdir()) if base.is_dir() else []:
        if d.is_dir() and not d.name.startswith("_") and d.name.upper() not in REFERENCE_COURSES \
                and (d / f"{d.name} Syllabus.md").is_file():
            out.append(d.name)
    out += [code for code in EXTRA_COURSES if vault.exists(course_moc_rel(code))]
    return out
