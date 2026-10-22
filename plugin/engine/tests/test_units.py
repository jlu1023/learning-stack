"""Teaching units (vault_learning.units) and the `unit` command."""
import datetime as dt

from vault_learning.cli import graph_json, unit_json
from vault_learning.graph import CourseGraph
from vault_learning.state import apply_result, read_state, write_state
from vault_learning.units import CourseUnits, lecture_map
from vault_learning.vault import Vault

from .conftest import write

TODAY = dt.date(2025, 10, 11)


def _folder_course(r):
    """ZZ300: two module folders, no lecture field, no lecture map, and a primer."""
    write(r, "Courses/ZZ300/ZZ300 Syllabus.md", "---\ntype: moc\ncourse: ZZ300\n---\n# ZZ300\n")
    write(r, "Courses/ZZ300/1 One/1 One.md", "---\ntype: moc\ncourse: ZZ300\n---\n# One\n")
    write(r, "Courses/ZZ300/1 One/Ant.md", """
        ---
        type: definition
        course: ZZ300
        section: "1.1"
        depends_on: ["[[Set]]"]
        ---
        # Ant
        """)
    write(r, "Courses/ZZ300/1 One/ZZ300 Lecture 1 Overview - One.md", """
        ---
        title: "ZZ300 Lecture 1 Overview - One"
        type: moc
        primer: true
        course: ZZ300
        unit: 1
        ---
        # Overview
        """)
    write(r, "Courses/ZZ300/2 Two/2 Two.md", "---\ntype: moc\ncourse: ZZ300\n---\n# Two\n")
    write(r, "Courses/ZZ300/2 Two/Bee.md", """
        ---
        type: theorem
        course: ZZ300
        section: "2.1"
        depends_on: ["[[Ant]]", "[[Alpha]]"]
        ---
        # Bee
        """)


def test_lecture_field_basis(vault):
    cu = CourseUnits(Vault(vault), "XX201")
    assert cu.basis == "lecture field"
    assert {k: [cu.cg.name(n) for n in u.nodes] for k, u in cu.units.items()} == {
        1: ["Alpha", "Beta"], 2: ["Lemma Zeta", "Gamma Theorem"], 3: ["Delta Method"]}
    assert cu.units[1].name == "Lecture 1"
    assert cu.unassigned == []


def test_folder_basis_with_primer(vault):
    _folder_course(vault)
    v = Vault(vault)
    cu = CourseUnits(v, "zz300")
    assert cu.basis == "module folder"
    assert cu.units[1].title == "One" and cu.units[1].label == "Module"
    s = cu.summary()
    assert [u["primer"] for u in s["units"]] == ["Courses/ZZ300/1 One/ZZ300 Lecture 1 Overview - One", None]
    # the primer is a moc, so it is never a graph node, nor counted as content
    cg = CourseGraph(v, "ZZ300")
    assert all("Overview" not in n for n in cg.nodes)
    assert cg.stats()["content_notes"] == 2
    d = cu.detail(2)
    assert d["previous"]["unit"] == 1 and d["following"] is None
    assert d["external_prereqs"] == {"XX201": ["Alpha"]}
    assert cu.detail(1)["used_outside"] == {}


def test_sections_basis_from_lecture_map(vault):
    write(vault, "Courses/YY202/YY202 Syllabus.md", """
        ---
        type: moc
        course: YY202
        ---
        # YY202

        ## Lecture map

        | Lecture | Topics | Sections | Slides |
        |---|---|---|---|
        | 1 | Opening | 1 (intro), 1.1, 1.2 | 1.0 to 1.20 |
        | 2 (Week 2) | Closing | 1.2.4, 2.1 | 2.0 to 2.9 |

        ## Chapters
        """)
    for name, sec in [("Pa", "1.1"), ("Pb", "1.2.3"), ("Pc", "2.1"), ("Pd", "3.1"), ("Pe", "1"), ("Pf", "1.2.4")]:
        write(vault, f"Courses/YY202/1 M/{name}.md",
              f'---\ntype: definition\ncourse: YY202\nsection: "{sec}"\ndepends_on: ["[[Set]]"]\n---\n# {name}\n')
    cu = CourseUnits(Vault(vault), "YY202")
    assert cu.basis == "lecture map sections"
    # longest listed prefix wins: 1.2.4 goes to lecture 2 although 1.2 is in lecture 1;
    # a bare "1" catches the chapter intro
    got = {k: sorted(cu.cg.name(n) for n in u.nodes) for k, u in cu.units.items()}
    assert got == {1: ["Pa", "Pb", "Pe"], 2: ["Pc", "Pf"]}
    assert cu.units[2].title == "Closing"
    assert [cu.cg.name(n) for n in cu.unassigned] == ["Pd"]


def test_lecture_map_parsing_stops_at_table_end():
    text = "## Lecture map\n\n| Week | Topics |\n|---|---|\n| 1 | A |\n| 2 | B |\n\nAfter.\n| 3 | C |\n"
    assert lecture_map(text) == [{"week": "1", "topics": "A"}, {"week": "2", "topics": "B"}]
    assert lecture_map("# No map here\n") == []


def test_started_counts_a_failed_first_attempt(vault):
    v = Vault(vault)
    assert unit_json(v, "XX201", "1")["started"] is False
    rel = "Courses/XX201/1 Basics/Beta.md"
    write_state(v, rel, apply_result(read_state(v, rel), False, TODAY))
    v = Vault(vault)
    assert read_state(v, rel).mastery == "unseen"
    assert unit_json(v, "XX201", "1")["started"] is True


def test_graph_carries_unit_and_unit_next(vault):
    v = Vault(vault)
    g = graph_json(v, "XX201")
    assert {n["name"]: n["unit"] for n in g["nodes"]}["Delta Method"] == 3
    nxt = unit_json(v, "XX201", "next")
    assert nxt["next_node"] == "Alpha" and nxt["unit"] == 1
    assert [n["name"] for n in nxt["node_list"]] == ["Alpha", "Beta"]
    assert unit_json(v, "XX201", "9")["error"] == "no unit 9"


GOOD_PRIMER = """
    ---
    title: "ZZ300 Module 2 Overview - Two"
    type: moc
    primer: true
    course: ZZ300
    unit: 2
    sources: ["[[Ant]]"]
    ---
    # ZZ300 Module 2 Overview - Two

    **The question:** why does $x$ matter?

    ## Where it sits
    After [[ZZ300 Lecture 1 Overview - One|Module 1]].

    ## Key ideas
    ```mermaid
    flowchart LR
      A[Ant] --> B[Bee]
    ```
    1. [[Ant]]
    2. [[Bee]]
    3. [[Alpha]]

    ## Why it matters
    It is examined.

    ## Before you start
    1. State [[Ant]].
    2. State [[Alpha]].
    """


def test_check_primer_passes_a_good_primer_and_flags_a_bad_one(vault):
    from vault_learning.primer_check import check_all, prose_words
    _folder_course(vault)
    write(vault, "Courses/ZZ300/2 Two/ZZ300 Module 2 Overview - Two.md", GOOD_PRIMER)
    write(vault, "Courses/ZZ300/2 Two/2 Two.md",
          "---\ntype: moc\ncourse: ZZ300\n---\n# Two\n\nOverview: [[ZZ300 Module 2 Overview - Two]]\n")
    out = check_all(Vault(vault), "ZZ300", validate_diagrams=False)
    probs = {r["primer"].rsplit("/", 1)[-1]: r["problems"] for r in out["results"]}
    assert probs["ZZ300 Module 2 Overview - Two"] == []
    # the fixture's unit-1 primer is a stub: wrong label in its name, no sections, no MOC link
    bad = probs["ZZ300 Lecture 1 Overview - One"]
    assert "file name does not match the unit (ZZ300 Module 1)" in bad
    assert "missing '## Key ideas'" in bad and "not linked from its module MOC" in bad
    assert out["failing"] == 1 and out["units_without_primer"]["ZZ300"] == []
    assert prose_words("A [[Ant|an ant]] and $x^2 + y$.\n```mermaid\nflowchart LR\n A-->B\n```\n") == 5


def test_check_primer_flags_dead_links_dashes_and_exam_sources(vault):
    from vault_learning.primer_check import check_all
    _folder_course(vault)
    text = GOOD_PRIMER.replace("[[Alpha]].", "[[Nowhere]] \u2014 see.").replace(
        'sources: ["[[Ant]]"]', 'sources: ["2025 exam solutions"]')
    write(vault, "Courses/ZZ300/2 Two/ZZ300 Module 2 Overview - Two.md", text)
    out = check_all(Vault(vault), "ZZ300", validate_diagrams=False)
    p = next(r["problems"] for r in out["results"] if r["primer"].endswith("Two"))
    assert "link [[Nowhere]] resolves to 0 notes" in p
    assert "contains an em dash" in p
    assert "source looks like an exam paper: 2025 exam solutions" in p
