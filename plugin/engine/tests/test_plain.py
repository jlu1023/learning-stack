"""Plain mode (no Obsidian) and Markdown links."""
import datetime as dt

import pytest

from vault_learning import config
from vault_learning.cli import replace_block, roadmap_report
from vault_learning.graph import CourseGraph
from vault_learning.primer_check import check_all
from vault_learning.review_queue import REVIEW_QUEUE_REL
from vault_learning.state import apply_result, read_state, write_state
from vault_learning.vault import Vault, link_target, make_link

from .conftest import write

TODAY = dt.date(2025, 10, 10)


def _plain(vault):
    write(vault, "vault-learning.yaml", "reference_courses: [PRE100, PRE101]\nfrontend: plain\n")
    return vault


def test_link_target_reads_markdown_links():
    assert link_target("[the alpha](Alpha.md)") == "Alpha"
    assert link_target("[x](../2%20Methods/Delta%20Method.md#Steps)") == "../2 Methods/Delta Method"
    assert link_target("[x](<./Beta.md>)") == "Beta"


def test_markdown_links_build_the_same_graph(vault):
    write(vault, "Courses/XX201/2 Methods/Epsilon.md", """
        ---
        type: definition
        course: XX201
        section: "2.2"
        depends_on: ["[Delta](Delta%20Method.md)", "[Gamma](../1%20Basics/Gamma%20Theorem.md)"]
        ---
        # Epsilon
        """)
    cg = CourseGraph(Vault(vault), "XX201")
    eps = "Courses/XX201/2 Methods/Epsilon.md"
    assert set(cg.G.predecessors(eps)) == {"Courses/XX201/2 Methods/Delta Method.md",
                                          "Courses/XX201/1 Basics/Gamma Theorem.md"}
    assert not [m for m in cg.gaps.missing if m[0] == "Epsilon"]


def test_broken_relative_markdown_link_is_a_gap(vault):
    write(vault, "Courses/XX201/2 Methods/Zed.md", """
        ---
        type: definition
        course: XX201
        depends_on: ["[gone](../Nowhere/Gamma%20Theorem.md)"]
        ---
        # Zed
        """)
    cg = CourseGraph(Vault(vault), "XX201")
    assert ("Zed", "depends_on", "../Nowhere/Gamma Theorem") in cg.gaps.missing


def test_make_link_follows_the_frontend(vault):
    Vault(vault)
    assert make_link("Courses/A/x.md", "Courses/B/Some Note.md") == "[[Some Note]]"
    Vault(_plain(vault))
    assert make_link("Courses/A/x.md", "Courses/B/Some Note.md") == "[Some Note](../B/Some%20Note.md)"


def test_plain_roadmap_without_mermaid_cli_keeps_mermaid_blocks_quietly(vault, monkeypatch):
    from vault_learning import validate
    monkeypatch.setattr(validate, "available", lambda: False)
    v = Vault(_plain(vault))
    report, code = roadmap_report(v, "all", TODAY, no_validate=True)
    assert code == 0 and report["errors"] == []
    moc = (vault / "Courses/XX201/1 Basics/1 Basics.md").read_text(encoding="utf-8")
    assert "<!-- roadmap:start -->" in moc and "%% roadmap" not in moc
    assert "internal-link" not in moc
    assert "```mermaid" in moc and ".svg" not in moc
    course = (vault / "Courses/XX201/XX201 Syllabus.md").read_text(encoding="utf-8")
    assert "Roadmap: [XX201 Roadmap](XX201%20Roadmap.md)" in course
    roadmap = (vault / "Courses/XX201/XX201 Roadmap.md").read_text(encoding="utf-8")
    assert "-file:Roadmap" not in roadmap
    assert not list((vault / "Courses").rglob("*.svg")) and not list((vault / "Courses").rglob("*.mmd"))
    assert (vault / REVIEW_QUEUE_REL).exists()


def test_plain_roadmap_with_mermaid_cli_exports_svg_images(vault):
    from vault_learning import validate
    if not validate.available():
        pytest.skip("mermaid-cli not installed")
    v = Vault(_plain(vault))
    report, code = roadmap_report(v, "all", TODAY, no_validate=True)
    assert code == 0 and report["errors"] == []
    moc = (vault / "Courses/XX201/1 Basics/1 Basics.md").read_text(encoding="utf-8")
    assert "![1 Basics roadmap](1%20Basics%20Roadmap.svg)" in moc and "```mermaid" in moc
    assert (vault / "Courses/XX201/1 Basics/1 Basics Roadmap.svg").read_text(encoding="utf-8").lstrip().startswith("<svg")
    roadmap = (vault / "Courses/XX201/XX201 Roadmap.md").read_text(encoding="utf-8")
    assert "XX201%20Roadmap%20-%20Course%20map.svg" in roadmap


def test_old_obsidian_markers_are_replaced_in_place():
    text = "---\ntitle: x\n---\n# X\n\n%% roadmap:start %%\nold\n%% roadmap:end %%\n\n## Rest\n"
    new, action = replace_block(text, "<!-- roadmap:start -->\nnew\n<!-- roadmap:end -->")
    assert action == "replaced" and "old" not in new and new.endswith("## Rest\n")


def test_static_review_queue_lists_due_items_and_errors(vault):
    v = Vault(_plain(vault))
    rel = "Courses/XX201/1 Basics/Alpha.md"
    write_state(v, rel, apply_result(read_state(v, rel), True, dt.date(2025, 10, 1)))
    write(vault, "Courses/_learning/Error Log.md",
          "# Error Log\n\n- [date:: 2025-10-02] [course:: XX201] [node:: Alpha] [category:: logic] [redo:: 2025-10-05] x\n")
    report, _ = roadmap_report(Vault(vault), "all", TODAY, no_validate=True)
    text = (vault / REVIEW_QUEUE_REL).read_text(encoding="utf-8")
    assert "generated: true" in text and "```dataview" not in text
    assert "[Alpha](../XX201/1%20Basics/Alpha.md)" in text
    assert "| 2025-10-02 | XX201 | Alpha | logic | 2025-10-05 |" in text
    assert "XX201: learning" in text


def test_obsidian_mode_leaves_dataview_review_queue_alone(vault):
    write(vault, REVIEW_QUEUE_REL, "# Review Queue\n\n```dataview\nTABLE x\n```\n")
    roadmap_report(Vault(vault), "all", TODAY, no_validate=True)
    assert "```dataview" in (vault / REVIEW_QUEUE_REL).read_text(encoding="utf-8")


def test_primer_check_accepts_markdown_links(vault):
    _plain(vault)
    write(vault, "Courses/XX201/1 Basics/1 Basics.md",
          "---\ntype: moc\ncourse: XX201\n---\n# Basics\n\nOverview: [o](XX201%20Lecture%201%20Overview%20-%20Basics.md)\n")
    write(vault, "Courses/XX201/1 Basics/XX201 Lecture 1 Overview - Basics.md", """
        ---
        title: "XX201 Lecture 1 Overview - Basics"
        type: moc
        primer: true
        course: XX201
        unit: 1
        ---
        # Overview

        **The question:** what are the basics?

        ## Where it sits
        - First.

        ## Key ideas

        ```mermaid
        flowchart LR
          A --> B
        ```

        1. One: [Alpha](Alpha.md)
        2. Two: [Beta](Beta.md)
        3. Three: [Gamma](Gamma%20Theorem.md)

        ## Why it matters
        - Style only.

        ## Before you start
        1. A question? [Set](../../PRE101/2%20Sets/Set.md)
        2. Another? [Broken](Nowhere.md)
        """)
    out = check_all(Vault(vault), "XX201", validate_diagrams=False)
    probs = next(r for r in out["results"] if "Lecture 1" in r["primer"])["problems"]
    assert probs == ["link [Broken](Nowhere.md) resolves to 0 notes"]
