"""Mermaid and Markdown rendering. Vault output rules: British English, no em
dashes, no LaTeX in Mermaid labels, plain note names (never wikilinks) in the
report-style parts of the Roadmap, day month year in prose.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict

from . import config
from .graph import THEOREM_TYPES, CourseGraph, kind_of, section_key
from .state import State, read_progress, read_state
from .vault import make_link, owner_label

# Obsidian hides %% comments %%; any other viewer hides HTML comments. Both are recognised.
OBSIDIAN_MARKERS = ("%% roadmap:start %%", "%% roadmap:end %%")
PLAIN_MARKERS = ("<!-- roadmap:start -->", "<!-- roadmap:end -->")
START, END = OBSIDIAN_MARKERS


def markers() -> tuple[str, str]:
    return PLAIN_MARKERS if config.plain() else OBSIDIAN_MARKERS
MAX_NODES = 50

CLASSDEFS = """    classDef unseen fill:#e4e4e4,stroke:#7a7a7a,color:#1a1a1a
    classDef learning fill:#f6cf72,stroke:#a86a12,color:#1a1a1a
    classDef secure fill:#9ec5f0,stroke:#2b5f9e,color:#1a1a1a
    classDef mastered fill:#9ad3a2,stroke:#2f7a4a,color:#1a1a1a
    classDef ext stroke-dasharray:5 4,stroke-width:2px
    classDef ctx fill:#f0f0f0,stroke:#7a7a7a,stroke-dasharray:5 4,color:#444444
    classDef example fill:#ffffff,stroke:#7a7a7a,stroke-dasharray:2 3,color:#1a1a1a
    classDef module fill:#e9edf4,stroke:#4f5f7a,color:#1a1a1a
    classDef course fill:#f0f0f0,stroke:#7a7a7a,stroke-dasharray:5 4,color:#1a1a1a"""

LEGEND = ("Shapes: rectangle definition, rounded box theorem, hexagon method, "
          "stadium concept or intuition, double-sided box proof with no theorem note, "
          "slanted box example or evidence (dotted). Fills: grey unseen, amber learning, "
          "blue secure, green mastered. Dashed border: outside this module or course. "
          "Only nearest prerequisites are drawn: an arrow implied by a longer chain is left out. "
          "In Obsidian, click a node to open its note.")

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def prose_date(d: dt.date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def esc(label: str) -> str:
    return label.replace("#", "#35;").replace('"', "#quot;")


def shape(label: str, kind: str, typ: str | None) -> str:
    l = esc(label)
    if kind == "example":
        return f'[/"{l}"/]'
    if kind == "proof":
        return f'[["{l}"]]'
    if kind == "module":
        return f'["{l}"]'
    if typ in THEOREM_TYPES:
        return f'("{l}")'
    if typ == "method":
        return '{{"' + l + '"}}'
    if typ in ("concept", "intuition"):
        return f'(["{l}"])'
    return f'["{l}"]'


class Diagram:
    """Builds one flowchart with safe ids n001..., collecting classes."""

    def __init__(self, direction: str = "TD"):
        self.direction = direction
        self.ids: dict[str, str] = {}
        self.decls: list[str] = []
        self.edges: list[str] = []
        self.classes: dict[str, list[str]] = defaultdict(list)
        self.sub: dict[str, list[str]] = defaultdict(list)
        self.sub_titles: dict[str, str] = {}

    def node(self, key: str, label: str, kind: str, typ: str | None,
             classes: list[str], clickable: bool, subgraph: str | None = None) -> str:
        if key in self.ids:
            return self.ids[key]
        nid = f"n{len(self.ids) + 1:03d}"
        self.ids[key] = nid
        decl = f"    {nid}{shape(label, kind, typ)}"
        (self.sub[subgraph] if subgraph else self.decls).append(decl)
        for c in classes:
            self.classes[c].append(nid)
        if clickable and not config.plain():          # Obsidian makes these nodes open their note
            self.classes["internal-link"].append(nid)
        return nid

    def edge(self, a: str, b: str, style: str = "-->", label: str | None = None) -> None:
        lab = f'|"{esc(label)}"|' if label else ""
        self.edges.append(f"    {a} {style}{lab} {b}")

    def render(self) -> str:
        out = [f"flowchart {self.direction}"]
        out += self.decls
        for i, (sg, members) in enumerate(sorted(self.sub.items())):
            out.append(f'    subgraph s{i + 1}["{esc(self.sub_titles.get(sg, sg))}"]')
            out += ["  " + m for m in members]
            out.append("    end")
        out += self.edges
        out.append(CLASSDEFS)
        for c, ids in self.classes.items():
            for i in range(0, len(ids), 40):
                out.append(f"    class {','.join(ids[i:i + 40])} {c}")
        return "\n".join(out)


class Renderer:
    def __init__(self, cg: CourseGraph):
        self.cg = cg
        self.v = cg.v
        self.progress = read_progress(self.v)
        self._state: dict[str, State] = {}
        self.exports: list[tuple[str, str]] = []      # (vault-relative .svg path, diagram), plain mode

    def state(self, rel: str) -> State:
        if rel not in self._state:
            self._state[rel] = read_state(self.v, rel, self.progress)
        return self._state[rel]

    def label(self, rel: str, external: bool = False) -> tuple[str, bool]:
        """(label, clickable). Duplicate-named notes get a location suffix and
        are not clickable, because internal-link resolves by label."""
        name = rel.rsplit("/", 1)[-1][:-3]
        if self.v.is_unique_name(name):
            return name, True
        return f"{name} ({owner_label(rel)})", False

    def add_note(self, d: Diagram, rel: str, extra: list[str] | None = None,
                 subgraph: str | None = None) -> str:
        note = self.v.note(rel)
        k = self.cg.kind.get(rel) or kind_of(note)
        lab, click = self.label(rel)
        classes = list(extra or [])
        if k == "example":
            classes.append("example")
        else:
            classes.insert(0, self.state(rel).mastery)
        return d.node(rel, lab, k, note.type, classes, click, subgraph)

    # ---------- module diagram ----------
    def module_groups(self, folder: str) -> list[tuple[str | None, list[str]]]:
        order = self.cg.module_order(folder)
        size = self._module_size(order)
        if size <= MAX_NODES:
            return [(None, order)]
        groups: dict[tuple, list[str]] = defaultdict(list)
        for r in order:
            sk = section_key(self.v.note(r).fm.get("section"))
            groups[sk[:2] if sk else ()].append(r)
        if len(groups) > 1 and () not in groups:
            return [("Section " + ".".join(map(str, k)), groups[k]) for k in sorted(groups)]
        # no usable sections: split along suggested order into even chunks
        n = -(-size // MAX_NODES)
        per = -(-len(order) // n)
        return [(f"Part {i + 1} of {n}", order[i * per:(i + 1) * per]) for i in range(n)]

    def _module_size(self, members: list[str]) -> int:
        ms = set(members)
        ex = {e for e in self.cg.examples
              if (self.cg.example_anchor.get(e, set()) | self.cg.example_feeds.get(e, set())) & ms}
        ext = {x for m in members for x in self.cg.ext.get(m, ())}
        return len(ms) + len(ex) + len(ext)

    def module_diagram(self, folder: str, members: list[str]) -> str:
        """Draws the transitive reduction: an arrow implied by a longer chain is
        omitted, so each note shows only its nearest prerequisites. External
        prerequisites and examples take part in the reduction too."""
        import networkx as nx
        cg = self.cg
        d = Diagram("TD")
        ms = set(members)
        acyc = cg.acyclic()
        H = nx.DiGraph()
        H.add_nodes_from(members)
        role: dict[str, str] = {}
        for r in members:
            for p in acyc.predecessors(r):
                H.add_edge(p, r)
                if p not in ms:
                    role[p] = "ctx"
            for e in cg.ext.get(r, ()):
                H.add_edge(e, r)
                role[e] = "ext"
        dotted = set()
        for e in cg.examples:
            if cg.module_of.get(e) != folder:
                continue
            anchors = cg.example_anchor.get(e, set()) & ms
            feeds = cg.example_feeds.get(e, set()) & ms
            for a in anchors:
                H.add_edge(a, e); dotted.add((a, e))
            for f in feeds:
                H.add_edge(e, f); dotted.add((e, f))
            if anchors or feeds:
                role[e] = "example"
        if nx.is_directed_acyclic_graph(H):
            R = nx.transitive_reduction(H)
            gens = list(nx.topological_generations(H))
            # Obsidian scales a diagram to the pane width: a wide, shallow graph
            # reads better laid out left to right (tall and narrow).
            if max(len(g) for g in gens) > 1.5 * len(gens):
                d.direction = "LR"
        else:
            R = H
        for r in members:
            self.add_note(d, r)
        for n in sorted((x for x in H if role.get(x) == "ctx"), key=cg.sort_key):
            where = cg.module_of[n]
            d.sub_titles[f"ctx:{where}"] = f"From {where}"
            self.add_note(d, n, ["ctx"], subgraph=f"ctx:{where}")
        for n in sorted((x for x in H if role.get(x) == "ext"), key=lambda x: x.lower()):
            owner = owner_label(n)
            d.sub_titles[f"ext:{owner}"] = f"From {owner}"
            self.add_note(d, n, ["ext"], subgraph=f"ext:{owner}")
        for n in sorted((x for x in H if role.get(x) == "example"), key=cg.sort_key):
            self.add_note(d, n)
        order = {n: i for i, n in enumerate(d.ids)}
        for u, w in sorted(R.edges(), key=lambda e: (order[e[0]], order[e[1]])):
            d.edge(d.ids[u], d.ids[w], "-.->" if (u, w) in dotted else "-->")
        for u, w in sorted(cg.back_edges):
            if u in d.ids and w in d.ids and w in ms:
                d.edge(d.ids[u], d.ids[w], "-.->", "cycle")
        return d.render()

    # ---------- course and spine ----------
    def module_dependencies(self) -> list[tuple[str, str, int]]:
        cg = self.cg
        pos = {m.folder: i for i, m in enumerate(cg.modules)}
        return sorted(((a, b, data["n"]) for a, b, data in cg.module_graph().edges(data=True)),
                      key=lambda e: (pos[e[0]], pos[e[1]]))

    def course_diagram(self) -> str:
        """Modules only, transitive reduction of the module dependencies; the
        full list with counts is printed under the diagram."""
        import networkx as nx
        cg = self.cg
        d = Diagram("TD")
        mg = cg.module_graph()
        for m in cg.modules:
            click = m.moc_rel is not None and self.v.is_unique_name(m.folder)
            d.node(m.folder, m.folder, "module", None, ["module"], click)
        R = nx.transitive_reduction(mg) if nx.is_directed_acyclic_graph(mg) else mg
        mod_cycle_edges = {(c[i], c[(i + 1) % len(c)]) for c in cg.gaps.module_cycles for i in range(len(c))}
        pos = {m.folder: i for i, m in enumerate(cg.modules)}
        for a, b in sorted(R.edges(), key=lambda e: (pos[e[0]], pos[e[1]])):
            back = (a, b) in mod_cycle_edges and pos[a] > pos[b]
            d.edge(d.ids[a], d.ids[b], "-.->" if back else "-->", str(mg[a][b]["n"]))
        return d.render()

    def spine_diagram(self, spine: list[tuple[str, int]]) -> str:
        import networkx as nx
        cg = self.cg
        d = Diagram("TD")
        keep = [n for n, _ in spine]
        for n in keep:
            self.add_note(d, n)
        g = cg.acyclic()
        reach = nx.DiGraph()
        reach.add_nodes_from(keep)
        for a in keep:
            desc = nx.descendants(g, a)
            for b in keep:
                if b in desc:
                    reach.add_edge(a, b)
        red = nx.transitive_reduction(reach)
        for a, b in sorted(red.edges(), key=lambda e: (cg.sort_key(e[0]), cg.sort_key(e[1]))):
            d.edge(d.ids[a], d.ids[b])
        return d.render()

    # ---------- documents ----------
    def mastery_counts(self) -> Counter:
        return Counter(self.state(n).mastery for n in self.cg.nodes)

    def roadmap_note(self, today: dt.date, created: str | None) -> tuple[str, list[tuple[str, str]]]:
        cg, code = self.cg, self.cg.code
        diagrams: list[tuple[str, str]] = []
        spine = cg.spine()
        course_d = self.course_diagram()
        spine_d = self.spine_diagram(spine)
        diagrams += [(f"{code} course map", course_d), (f"{code} spine", spine_d)]
        mc = self.mastery_counts()
        n = len(cg.nodes)
        L = []
        L.append("---")
        L.append(f'title: "{code} Roadmap"')
        L.append("type: moc")
        L.append(f"course: {code}")
        L.append("generated: true")
        L.append(f"created: {created or today.isoformat()}")
        L.append(f"updated: {today.isoformat()}")
        L.append("---")
        L.append("")
        L.append(f"# {code} Roadmap")
        L.append("")
        L.append(f"Generated by `/learn:roadmap` from the `depends_on` fields of the {code} notes. Do not edit by hand: "
                 f"rerun `/learn:roadmap {code}` after every ingest, and after each `/learn:teach` or `/learn:quiz` session to refresh the colours. "
                 f"Course MOC: {code} Syllabus. Module diagrams sit in each module MOC between the roadmap markers.")
        L.append("")
        if not config.plain():
            L.append("To hide roadmaps in the graph view, add `-file:Roadmap` to the graph's search filter.")
            L.append("")
        L.append(f"Learner state: {n} nodes; " + ", ".join(f"{mc.get(k, 0)} {k}" for k in
                                                          ("unseen", "learning", "secure", "mastered")) + ".")
        L.append("")
        L.append("## Course map")
        L.append("")
        L.append("One box per module. An arrow from A to B means notes in B depend on notes in A, and the number "
                 "counts those dependencies. Arrows implied by a chain of other arrows are left out; every direct "
                 "dependency is listed below the diagram.")
        L.append("")
        L += self.diagram_md(cg.roadmap_rel, f"{cg.prefix}{code} Roadmap - Course map.svg", "Course map", course_d)
        deps = self.module_dependencies()
        if deps:
            L.append("Direct dependencies between modules (prerequisite module, dependent module, count):")
            L.append("")
            L += [f"- {a} to {b}: {n}" for a, b, n in deps]
            L.append("")
        ext = cg.external_prereqs()
        if ext:
            per = Counter()
            for owner, targets in ext.items():
                for e, dd in targets.items():
                    for x in dd:
                        per[(owner, cg.module_of[x])] += 1
            L.append("Prerequisites from earlier courses, by module (details under Connections to other courses):")
            L.append("")
            for owner in sorted(ext):
                parts = [f"{m.folder} ({per[(owner, m.folder)]})" for m in cg.modules if per[(owner, m.folder)]]
                L.append(f"- {owner}: " + ", ".join(parts))
            L.append("")
        L.append("## Spine")
        L.append("")
        L.append("The results with the most dependents inside the course: what the rest of it hangs on. "
                 "An arrow means the lower result builds on the upper one, directly or through others.")
        L.append("")
        L += self.diagram_md(cg.roadmap_rel, f"{cg.prefix}{code} Roadmap - Spine.svg", "Spine", spine_d)
        for i, (nd, c) in enumerate(spine, 1):
            L.append(f"{i}. {self.label(nd)[0]}: {c} dependent{'' if c == 1 else 's'}")
        L.append("")
        L.append(LEGEND)
        L.append("")
        L.append("## Suggested order")
        L.append("")
        L.append("A prerequisite-first order within each module, in the course's module order. "
                 "Plain names on purpose, so the roadmap adds no graph edges; open notes from the diagrams.")
        L.append("")
        for m in cg.modules:
            order = cg.module_order(m.folder)
            L.append(f"### {m.folder}")
            L.append("")
            if not order:
                L.append("No notes yet.")
                L.append("")
                continue
            for i, r in enumerate(order, 1):
                nm = self.label(r)[0]
                proofs = sorted(cg.proofs_for.get(r, []))
                extra = f" (proof: {'; '.join(p.rsplit('/', 1)[-1][:-3] for p in proofs)})" if proofs else ""
                st = self.state(r).mastery
                tag = "" if st == "unseen" else f" [{st}]"
                L.append(f"{i}. {nm}{extra}{tag}")
            L.append("")
        L += self.connections_section()
        L += self.gaps_section()
        return "\n".join(L).rstrip() + "\n", diagrams

    def connections_section(self) -> list[str]:
        cg = self.cg
        L = ["## Connections to other courses", ""]
        L.append("### Prerequisites from other courses")
        L.append("")
        ext = cg.external_prereqs()
        if not ext:
            L += ["None recorded.", ""]
        for owner in sorted(ext):
            L.append(f"**{owner}**")
            L.append("")
            for e in sorted(ext[owner], key=lambda r: r.rsplit('/', 1)[-1].lower()):
                deps = sorted(self.label(x)[0] for x in ext[owner][e])
                L.append(f"- {self.label(e)[0]}: used by {', '.join(deps)}")
            L.append("")
        L.append("### Where this course is used elsewhere")
        L.append("")
        out = cg.used_outside()
        if not out:
            L += ["Nothing outside the course links in yet.", ""]
        for owner in sorted(out):
            L.append(f"**{owner}**")
            L.append("")
            for e in sorted(out[owner], key=lambda r: r.rsplit('/', 1)[-1].lower()):
                srcs = sorted(self.label(x)[0] for x in out[owner][e])
                L.append(f"- {self.label(e)[0]}: builds on {', '.join(srcs)}")
            L.append("")
        return L

    def gaps_section(self) -> list[str]:
        cg, g = self.cg, self.cg.gaps
        s = cg.stats()
        L = ["## Data gaps", ""]
        L.append("How far to trust this map. The roadmap is only as good as the `depends_on` fields.")
        L.append("")
        ext = ", ".join(f"{k} {v}" for k, v in sorted(s["external_edges"].items())) or "none"
        L.append(f"- Content notes: {s['content_notes']}, of which {s['with_depends_on']} have `depends_on`.")
        L.append(f"- Diagram nodes: {s['nodes']} ({s['proofs_folded']} proofs folded into their theorems; "
                 f"{s['examples']} examples and evidence notes shown only in module diagrams).")
        L.append(f"- Prerequisite edges inside the course: {s['in_course_edges']}. Edges to other courses: {ext}.")
        L.append(f"- Broken links: {s['missing']}. Ambiguous links: {s['ambiguous']}. Cycles: {s['cycles']}.")
        L.append(f"- `used_in` entries with no matching `depends_on` on the target: {s['used_in_without_depends_on']} "
                 f"(listed below). `depends_on` entries with no matching `used_in` on the prerequisite: "
                 f"{s['depends_on_without_used_in']} (expected, since `used_in` is selective; not listed).")
        L.append("")

        def block(title: str, items: list[str]) -> None:
            if not items:
                return
            L.append(f"### {title}")
            L.append("")
            L.extend(f"- {x}" for x in items)
            L.append("")

        block("Unreadable frontmatter", [f"{a}: {b}" for a, b in g.yaml_errors])
        block("Notes with no prerequisites recorded", sorted(g.no_depends_on))
        block("Broken links", [f"{a} ({b}): {c}" for a, b, c in g.missing])
        block("Ambiguous links", [f"{a} ({b}): {c} could be {' or '.join(h[:-3] for h in hs)}"
                                  for a, b, c, hs in g.ambiguous])
        block("Cycles (drawn with a dashed back-edge; notes not edited)", [" then ".join(c) for c in g.cycles])
        block("Module-level cycles", [" then ".join(c) for c in g.module_cycles])
        block("Proofs whose theorem note is outside the course (drawn as their own node)",
              [f"{a}: theorem is {b}" for a, b in g.proofs_external_theorem])
        block("Proofs with no theorem note found (drawn as their own node)", g.proofs_unattached)
        block("Examples with no prerequisite in the course (not drawn)", sorted(g.examples_unanchored))
        block("Examples or evidence listed as a prerequisite (drawn dotted in the module diagram, not used for ordering)", [f"{a} depends on {b}" for a, b in g.example_as_prereq])
        block("Notes with a type outside the schema (not drawn)", [f"{a}: {b}" for a, b in g.other_types])
        if g.used_in_without_depends_on:
            L.append("### `used_in` without a matching `depends_on`")
            L.append("")
            L.append(f"> [!note]- {len(g.used_in_without_depends_on)} entries: A lists B in `used_in`, "
                     f"but B does not list A in `depends_on`")
            for a, b in sorted(g.used_in_without_depends_on, key=lambda x: (x[0].lower(), x[1].lower())):
                L.append(f"> - {a} lists {b}")
            L.append("")
        return L

    def module_block(self, folder: str) -> tuple[str, list[tuple[str, str]]]:
        code = self.cg.code
        groups = self.module_groups(folder)
        start, end = markers()
        L = [start, "## Roadmap", "",
             f"Generated by `/learn:roadmap` from `depends_on`; everything between the roadmap markers is "
             f"overwritten on each run. Suggested order and data gaps: {code} Roadmap.", ""]
        diagrams = []
        for title, members in groups:
            if not members:
                L += ["No notes yet.", ""]
                continue
            dg = self.module_diagram(folder, members)
            diagrams.append((f"{code} {folder}" + (f" {title}" if title else ""), dg))
            if title:
                L += [f"### {title}", ""]
            moc = f"{self.cg.prefix}{folder}/{folder}.md"
            svg = f"{self.cg.prefix}{folder}/{folder} Roadmap" + (f" - {title}" if title else "") + ".svg"
            L += self.diagram_md(moc, svg, f"{folder} roadmap", dg)
        L += [LEGEND, end]
        return "\n".join(L), diagrams

    def course_moc_block(self) -> str:
        code = self.cg.code
        start, end = markers()
        link = make_link(self.cg.course_moc, self.cg.roadmap_rel)
        return "\n".join([start, f"Roadmap: {link} (generated dependency map, suggested order and data gaps).", end])

    def diagram_md(self, note_rel: str, svg_rel: str, alt: str, diagram: str) -> list[str]:
        """A diagram as Markdown lines. Obsidian renders Mermaid itself; elsewhere the
        diagram is exported as an SVG beside the note, with its source kept below."""
        if not config.plain():
            return ["```mermaid", diagram, "```", ""]
        self.exports.append((svg_rel, diagram))
        img = make_link(note_rel, svg_rel, alt)
        return ["!" + img, "", "<details><summary>Diagram source (Mermaid)</summary>", "",
                "```mermaid", diagram, "```", "", "</details>", ""]
