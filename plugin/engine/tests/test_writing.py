import datetime as dt
import json
import shutil

import pytest

from vault_learning import cli
from vault_learning.render import END, START, Renderer, esc
from vault_learning.graph import CourseGraph
from vault_learning.vault import Vault, set_frontmatter_fields


def test_replace_block_inserts_before_first_h2_then_replaces_only_span():
    text = "---\ntitle: x\n---\n# T\n\nIntro.\n\n## Defs\n- a\n"
    new, act = cli.replace_block(text, f"{START}\nv1\n{END}")
    assert act == "inserted"
    assert new.index(START) < new.index("## Defs")
    again, act2 = cli.replace_block(new, f"{START}\nv1\n{END}")
    assert act2 == "unchanged" and again == new
    v2, act3 = cli.replace_block(new, f"{START}\nv2\n{END}")
    assert act3 == "replaced"
    a, b = v2.index(START), v2.index(END) + len(END)
    a0, b0 = new.index(START), new.index(END) + len(END)
    assert v2[:a] == new[:a0] and v2[b:] == new[b0:]


def test_replace_block_preserves_crlf_and_rejects_malformed():
    text = "---\r\ntitle: x\r\n---\r\n# T\r\n\r\n## Defs\r\n"
    new, _ = cli.replace_block(text, f"{START}\nx\n{END}")
    assert "\n" not in new.replace("\r\n", "")
    with pytest.raises(ValueError):
        cli.replace_block(text + START, f"{START}\nx\n{END}")


def test_set_frontmatter_fields_is_surgical():
    text = ("---\ntitle: \"A\"\nupdated: 2025-09-02\ndepends_on: [\"[[X]]\"]\nreview: 2025-01-02\n---\n"
            "# Body with review: 2019-01-02\n")
    new = set_frontmatter_fields(text, {"review": "2025-10-02", "mastery": "learning"})
    assert "review: 2025-10-02" in new and "mastery: learning" in new
    assert "updated: 2025-09-02" in new
    assert new.endswith("# Body with review: 2019-01-02\n")
    assert new.count("review:") == 2  # frontmatter one replaced, body untouched


def test_set_frontmatter_fields_keeps_each_line_ending():
    # real vault case: CRLF on the '---' delimiters and body, LF inside the block
    text = "---\r\ntags:\n  - example\nupdated: 2025-07-24T12:43\n---\r\n\r\n# Body\r\n"
    new = set_frontmatter_fields(text, {"updated": "2025-09-30T22:05", "mastery": "learning"})
    assert new == ("---\r\ntags:\n  - example\nupdated: 2025-09-30T22:05\nmastery: learning\n---\r\n\r\n# Body\r\n")
    # an all-CRLF note stays all-CRLF, including the appended key
    crlf = "---\r\ntitle: A\r\n---\r\nbody\r\n"
    assert set_frontmatter_fields(crlf, {"review": "2025-10-02"}) == "---\r\ntitle: A\r\nreview: 2025-10-02\r\n---\r\nbody\r\n"


def test_esc_quotes_and_hashes():
    assert esc('He said "x" #1') == "He said #quot;x#quot; #35;1"


def test_duplicate_named_external_is_not_clickable(vault):
    v = Vault(vault)
    r = Renderer(CourseGraph(v, "XX201"))
    lab, click = r.label("Courses/PRE101/8 Continuity/Extreme Value Theorem.md")
    assert lab == "Extreme Value Theorem (PRE101)" and click is False
    assert r.label("Courses/XX201/1 Basics/Alpha.md") == ("Alpha", True)


def test_roadmap_suggested_order_has_no_wikilinks(vault):
    v = Vault(vault)
    text, diagrams = Renderer(CourseGraph(v, "XX201")).roadmap_note(dt.date(2025, 9, 30), None)
    order = text.split("## Suggested order", 1)[1].split("## Connections", 1)[0]
    assert "[[" not in order
    assert "[[" not in text  # the whole Roadmap adds no graph edges
    assert "-file:Roadmap" in text
    assert "—" not in text  # no em dashes


def _run(vault, *argv, capsys):
    rc = cli.main(["--vault", str(vault), "--date", "2025-09-30", *argv])
    return rc, json.loads(capsys.readouterr().out)


def test_roadmap_end_to_end_idempotent_and_skips_human_authored(vault, capsys):
    moc = vault / "Courses/XX201/2 Methods/2 Methods.md"
    moc.write_text(moc.read_text(encoding="utf-8").replace("type: moc", "type: moc\nhuman_authored: true"),
                   encoding="utf-8")
    ha_before = moc.read_bytes()
    rc, out = _run(vault, "roadmap", "XX201", "--no-validate", capsys=capsys)
    assert rc == 0
    assert any("human_authored" in s for s in out["skipped"])
    assert moc.read_bytes() == ha_before
    assert (vault / "Courses/XX201/XX201 Roadmap.md").is_file()
    basics = (vault / "Courses/XX201/1 Basics/1 Basics.md").read_text(encoding="utf-8")
    assert START in basics and "updated: 2025-09-30" in basics
    syl = (vault / "Courses/XX201/XX201 Syllabus.md").read_text(encoding="utf-8")
    assert "[[XX201 Roadmap]]" in syl
    rc, out2 = _run(vault, "roadmap", "XX201", "--no-validate", capsys=capsys)
    assert out2["written"] == []


def test_record_writes_frontmatter_without_bumping_updated(vault, capsys):
    p = vault / "Courses/XX201/1 Basics/Alpha.md"
    p.write_text(p.read_text(encoding="utf-8").replace("type: definition", "type: definition\nupdated: 2025-09-02"),
                 encoding="utf-8")
    rc, out = _run(vault, "record", "Alpha", "--result", "pass", capsys=capsys)
    assert out["after"]["mastery"] == "learning" and out["written_to"] == "frontmatter"
    t = p.read_text(encoding="utf-8")
    assert "mastery: learning" in t and "review: 2025-10-01" in t and "updated: 2025-09-02" in t


def test_record_preserves_crlf_body(vault, capsys):
    p = vault / "Courses/XX201/1 Basics/Alpha.md"
    p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    _run(vault, "record", "Alpha", "--result", "pass", capsys=capsys)
    raw = p.read_bytes()
    assert b"mastery: learning\r\n" in raw
    assert raw.count(b"\n") == raw.count(b"\r\n")  # no bare LF introduced, none lost


def test_record_human_authored_goes_to_progress_store(vault, capsys):
    p = vault / "Courses/XX201/1 Basics/Beta.md"
    p.write_text(p.read_text(encoding="utf-8").replace("type: definition", "type: definition\nhuman_authored: true"),
                 encoding="utf-8")
    before = p.read_bytes()
    (vault / "Courses/_learning/progress.md").write_text(
        "---\ntype: reference\n---\n# Progress\n\n| Note | Path | mastery | mastery_since | last_quizzed | review | review_interval |\n"
        "|---|---|---|---|---|---|---|\n", encoding="utf-8")
    rc, out = _run(vault, "record", "Beta", "--result", "pass", capsys=capsys)
    assert out["written_to"] == "progress" and p.read_bytes() == before
    rc, show = _run(vault, "show", "Beta", capsys=capsys)
    assert show["state"]["mastery"] == "learning"


def test_next_prefers_latest_lecture_among_eligible(vault, capsys):
    rc, out = _run(vault, "next", "XX201", capsys=capsys)
    assert out["next"]["name"] == "Alpha"          # only Alpha has no in-course prerequisite
    for n in ("Alpha", "Beta"):
        _run(vault, "record", n, "--result", "pass", capsys=capsys)
    rc, out = _run(vault, "next", "XX201", capsys=capsys)
    assert out["next"]["name"] == "Lemma Zeta"      # lecture 2, eligible; Gamma needs Lemma Zeta


def test_due_lists_reviews_and_error_log_redos(vault, capsys):
    _run(vault, "record", "Alpha", "--result", "fail", capsys=capsys)
    (vault / "Courses/_learning/Error Log.md").write_text(
        "# Error Log\n\n- [date:: 2025-09-21] [course:: XX201] [node:: Alpha] [category:: algebra] [redo:: 2025-09-26] note\n"
        "- [date:: 2025-09-22] [course:: XX201] [node:: Beta] [category:: logic] [redo:: 2025-09-26] [redone:: 2025-09-27] x\n",
        encoding="utf-8")
    rc = cli.main(["--vault", str(vault), "--date", "2025-10-02", "due", "mixed"])
    out = json.loads(capsys.readouterr().out)
    assert [d["name"] for d in out["due"]] == ["Alpha"]
    assert [r["node"] for r in out["redos"]] == ["Alpha"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_validator_catches_a_broken_diagram():
    from vault_learning.validate import ValidatorUnavailable, validate
    try:
        fails = validate([("good", 'flowchart TD\n    n001["A"] --> n002("B")'),
                          ("bad", 'flowchart TD\n    n001["A] -->')])
    except ValidatorUnavailable as e:
        pytest.skip(str(e))
    assert [f[0] for f in fails] == ["bad"]


def test_index_counts_hubs_no_links_and_is_idempotent(vault, capsys):
    from vault_learning.cli import main
    from vault_learning.index import INDEX_REL
    assert main(["--vault", str(vault), "--date", "2025-09-30", "index"]) == 0
    text = (vault / INDEX_REL).read_text(encoding="utf-8")
    assert "generated: true" in text and "created: 2025-09-30" in text
    assert "- **Courses/**" in text
    assert "hub: XX201 Syllabus" in text          # '<name> Syllabus' rule
    assert "hub: Basics" not in text and "hub: 1 Basics" in text  # named after its folder
    body = text.split("\n---\n", 1)[1]
    assert "[[" not in body                        # plain names only: no graph edges
    before = (vault / INDEX_REL).read_bytes()
    capsys.readouterr()
    assert main(["--vault", str(vault), "--date", "2025-10-02", "index"]) == 0
    assert '"unchanged"' in capsys.readouterr().out
    assert (vault / INDEX_REL).read_bytes() == before   # only the date moved: nothing written
