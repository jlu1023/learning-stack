from vault_learning.graph import CourseGraph, roadmap_courses
from vault_learning.vault import Vault, as_link_list, link_target

from .conftest import write


def test_link_target_strips_alias_heading_and_md():
    assert link_target("[[Alpha|the alpha]]") == "Alpha"
    assert link_target("[[Beta#Statement]]") == "Beta"
    assert link_target("[[Courses/X/Y.md|y]]") == "Courses/X/Y"


def test_unquoted_yaml_wikilink_is_recovered():
    # depends_on: [[X]] (unquoted) parses as a nested list
    assert as_link_list([["X"]]) == ["[[X]]"]


def test_resolution_path_bare_ambiguous_missing(vault):
    v = Vault(vault)
    assert v.resolve("[[Courses/PRE101/8 Continuity/Extreme Value Theorem]]") == \
        ["Courses/PRE101/8 Continuity/Extreme Value Theorem.md"]
    assert len(v.resolve("Extreme Value Theorem")) == 2
    assert v.resolve("Nowhere Note") == []


def test_graph_edges_fold_proofs_and_report_gaps(vault):
    cg = CourseGraph(Vault(vault), "XX201")
    n = {cg.name(x): x for x in cg.nodes}
    assert "Proof - Gamma Theorem (Part 1)" not in n          # folded
    # the proof's Lemma Zeta dependency becomes a prerequisite of the theorem
    assert cg.G.has_edge(n["Lemma Zeta"], n["Gamma Theorem"])
    assert cg.G.has_edge(n["Alpha"], n["Beta"])               # alias stripped
    assert cg.G.has_edge(n["Gamma Theorem"], n["Delta Method"])
    # examples are not nodes but are anchored
    assert all("Example" not in k for k in n)
    ex = next(e for e in cg.examples)
    assert cg.example_anchor[ex] == {n["Alpha"], n["Beta"]}
    # gaps: missing and ambiguous reported, never guessed
    assert ("Delta Method", "depends_on", "Nowhere Note") in cg.gaps.missing
    amb = [a for a in cg.gaps.ambiguous if a[2] == "Linear Transformation"]
    assert amb and len(amb[0][3]) == 2
    # external prerequisites
    ext = cg.external_prereqs()
    assert set(ext) == {"PRE101"}
    assert cg.gaps.cycles == []


def test_used_in_consistency(vault):
    cg = CourseGraph(Vault(vault), "XX201")
    # Alpha lists Gamma Theorem in used_in, but Gamma's depends_on lacks Alpha
    assert ("Alpha", "Gamma Theorem") in cg.gaps.used_in_without_depends_on
    assert ("Alpha", "Beta") not in cg.gaps.used_in_without_depends_on


def test_suggested_order_is_topological_with_section_ties(vault):
    cg = CourseGraph(Vault(vault), "XX201")
    names = [cg.name(x) for x in cg.suggested_order()]
    assert names == ["Alpha", "Beta", "Lemma Zeta", "Gamma Theorem", "Delta Method"]


def test_cycle_reported_and_back_edge_chosen_without_editing(vault):
    p = vault / "Courses/XX201/1 Basics/Alpha.md"
    before = p.read_text(encoding="utf-8").replace('["[[Set]]"]', '["[[Set]]", "[[Gamma Theorem]]"]')
    p.write_text(before, encoding="utf-8")
    cg = CourseGraph(Vault(vault), "XX201")
    assert cg.gaps.cycles, "cycle should be reported"
    assert cg.back_edges
    assert p.read_text(encoding="utf-8") == before
    # ordering still works on the acyclic view
    assert len(cg.suggested_order()) == len(cg.nodes)


def test_roadmap_courses_excludes_reference_courses(vault):
    write(vault, "Courses/PRE101/PRE101 Syllabus.md", "---\ntype: moc\n---\n# x\n")
    assert roadmap_courses(Vault(vault)) == ["XX201"]
