"""The proof track: each proof has its own level, scaffold stage and review date,
apart from its theorem's learner state."""
import datetime as dt
import json

from vault_learning import cli
from vault_learning.library import connect
from vault_learning.proofs import PROOF_PROGRESS_REL, ProofState, apply_proof_result
from vault_learning.review_queue import review_queue_text
from vault_learning.vault import Vault

from .conftest import write
from .test_library import _card, _library

D = dt.date(2026, 3, 2)
PROOF = "Proof - Gamma Theorem (Part 1)"
PROOF_REL = f"Courses/XX201/1 Basics/{PROOF}.md"


def day(n):
    return D + dt.timedelta(days=n)


def _run(vault, capsys, *argv, date="2026-03-02") -> tuple[int, dict]:
    code = cli.main(["--vault", str(vault), "--date", date, *argv])
    out = capsys.readouterr()
    assert "Traceback" not in out.err
    return code, json.loads(out.out)


# ---------- transitions ----------
def test_pass_moves_the_stage_up_and_is_due_in_3_days():
    s = apply_proof_result(ProofState(), True, 1, D)
    assert (s.proof_level, s.proof_stage, s.proof_review, s.proof_since) == ("learning", 2, day(3), D)


def test_fail_moves_the_stage_down_due_in_2_days_and_unseen_stays_unseen():
    s = apply_proof_result(ProofState(proof_stage=3), False, 3, D)
    assert (s.proof_level, s.proof_stage, s.proof_review, s.proof_streak) == ("unseen", 2, day(2), 1)
    assert apply_proof_result(ProofState(), False, 1, D).proof_stage == 1          # floor


def test_solo_passes_space_out_21_then_60_and_reach_secure_then_mastered():
    s = apply_proof_result(ProofState(proof_level="learning", proof_since=D, proof_stage=4), True, 4, D)
    assert (s.proof_level, s.proof_review, s.proof_solo, s.proof_stage) == ("secure", day(21), 1, 4)
    s = apply_proof_result(s, True, 4, day(21))
    assert (s.proof_level, s.proof_review, s.proof_solo) == ("mastered", day(81), 2)


def test_mastered_needs_21_days_after_secure():
    s = apply_proof_result(ProofState(proof_level="secure", proof_since=D, proof_stage=4), True, 4, day(10))
    assert s.proof_level == "secure"


def test_a_stage_below_4_resets_the_solo_run():
    s = ProofState(proof_level="secure", proof_since=D, proof_stage=4, proof_solo=1)
    s = apply_proof_result(s, True, 3, day(5))
    assert s.proof_solo == 0 and s.proof_review == day(8)


def test_second_fail_in_a_row_drops_a_level_but_never_below_learning():
    s = apply_proof_result(ProofState(proof_level="secure", proof_since=D, proof_stage=4), False, 4, D)
    assert s.proof_level == "secure" and s.proof_streak == 1
    s = apply_proof_result(s, False, 3, day(2))
    assert s.proof_level == "learning" and s.proof_streak == 0
    s = apply_proof_result(apply_proof_result(s, False, 2, day(4)), False, 1, day(6))
    assert s.proof_level == "learning"


def test_parsing_is_lenient():
    s = ProofState.from_mapping({"proof_level": "Bogus", "proof_stage": "9", "proof_streak": "x"})
    assert (s.proof_level, s.proof_stage, s.proof_streak) == ("unseen", 4, 0)


# ---------- the command line ----------
def test_record_a_proof_needs_a_stage_and_writes_proof_fields_only(vault, capsys):
    code, out = _run(vault, capsys, "record", PROOF, "--result", "pass")
    assert code == 2 and "--stage" in out["error"]
    code, out = _run(vault, capsys, "record", PROOF, "--result", "pass", "--stage", "2")
    assert code == 0 and out["after"]["proof_stage"] == 3 and out["written_to"] == "frontmatter"
    text = (vault / PROOF_REL).read_text(encoding="utf-8")
    assert "proof_review: 2026-03-05" in text and "mastery:" not in text and "updated:" not in text
    code, show = _run(vault, capsys, "show", PROOF)
    assert show["proof_state"]["proof_level"] == "learning" and show["state"]["mastery"] == "unseen"


def test_a_stage_on_a_note_that_is_not_a_proof_is_refused(vault, capsys):
    code, out = _run(vault, capsys, "record", "Alpha", "--result", "pass", "--stage", "1")
    assert code == 2 and "proof" in out["error"]
    assert "mastery" not in (vault / "Courses/XX201/1 Basics/Alpha.md").read_text(encoding="utf-8")


def test_proofs_lists_new_once_the_theorem_is_learned_then_due(vault, capsys):
    code, out = _run(vault, capsys, "proofs", "XX201")
    assert code == 0 and out["new_total"] == 0 and out["due_total"] == 0        # theorem unseen
    _run(vault, capsys, "record", "Gamma Theorem", "--result", "pass")
    code, out = _run(vault, capsys, "proofs", "XX201")
    assert [x["name"] for x in out["new"]] == [PROOF] and out["new"][0]["theorem"] == "Gamma Theorem"
    assert out["new"][0]["unit"] == 2 and out["new"][0]["unit_tested"] is False
    _run(vault, capsys, "record", PROOF, "--result", "fail", "--stage", "1")
    code, out = _run(vault, capsys, "proofs", "mixed", date="2026-03-04")
    assert out["due_total"] == 1 and out["new_total"] == 0 and out["due"][0]["overdue_days"] == 0


def test_proofs_from_a_tested_unit_come_first(vault, capsys):
    write(vault, "Courses/XX201/2 Methods/Proof - Delta Method.md",
          "---\ntype: proof\ncourse: XX201\n---\n# Proof\n\n**Theorem:** [[Delta Method]]\n")
    for node in ("Alpha", "Beta", "Gamma Theorem", "Delta Method"):
        _run(vault, capsys, "record", node, "--result", "pass")
    code, out = _run(vault, capsys, "proofs", "XX201")
    assert [x["name"] for x in out["new"]] == [PROOF, "Proof - Delta Method"]
    write(vault, "Courses/_learning/sessions/2026-03-01 XX201 Unit 3 test.md", "---\ntype: session\n---\n")
    code, out = _run(vault, capsys, "proofs", "XX201")
    assert [x["name"] for x in out["new"]] == ["Proof - Delta Method", PROOF]
    assert out["new"][0]["unit_tested"] is True


def test_an_unknown_course_is_a_json_error(vault, capsys):
    code, out = _run(vault, capsys, "proofs", "NOPE")
    assert code == 2 and out["courses"] == ["XX201"]


def test_due_and_next_never_draw_proofs(vault, capsys):
    write(vault, "Courses/XX201/1 Basics/Proof - Orphan Result.md",
          "---\ntype: proof\ncourse: XX201\ndepends_on: [\"[[Alpha]]\"]\n---\n# Proof\n")
    _run(vault, capsys, "record", PROOF, "--result", "fail", "--stage", "1")
    code, out = _run(vault, capsys, "due", "XX201", date="2027-01-01")
    assert all(not x["name"].startswith("Proof - ") for x in out["due"])
    code, g = _run(vault, capsys, "graph", "XX201")
    orphan = next(n for n in g["nodes"] if n["name"] == "Proof - Orphan Result")
    assert orphan["proof_state"]["proof_stage"] == 1
    taught = []
    while True:
        code, nxt = _run(vault, capsys, "next", "XX201")
        if nxt["next"] is None:
            break
        taught.append(nxt["next"]["name"])
        _run(vault, capsys, "record", taught[-1], "--result", "pass")
    assert sorted(taught) == ["Alpha", "Beta", "Delta Method", "Gamma Theorem", "Lemma Zeta"]
    assert nxt["reason"] == "every node is at learning or better"
    # a proof with no theorem note is new once its prerequisites are learned
    code, out = _run(vault, capsys, "proofs", "XX201")
    assert "Proof - Orphan Result" in [x["name"] for x in out["new"]]


def test_a_human_authored_proof_goes_to_the_proof_progress_store(vault, capsys):
    p = vault / PROOF_REL
    p.write_text(p.read_text(encoding="utf-8").replace("type: proof", "type: proof\nhuman_authored: true"),
                 encoding="utf-8")
    before = p.read_bytes()
    code, out = _run(vault, capsys, "record", PROOF, "--result", "pass", "--stage", "4")
    assert out["written_to"] == "proof-progress" and p.read_bytes() == before
    assert (vault / PROOF_PROGRESS_REL).is_file()
    _run(vault, capsys, "record", PROOF, "--result", "pass", "--stage", "4", date="2026-03-23")
    code, show = _run(vault, capsys, "show", PROOF)
    assert show["proof_state"]["proof_stage"] == 4 and show["proof_state"]["proof_level"] == "mastered"
    rows = [l for l in (vault / PROOF_PROGRESS_REL).read_text(encoding="utf-8").splitlines() if PROOF_REL in l]
    assert len(rows) == 1


def test_the_static_review_queue_lists_due_proofs(vault, capsys):
    _run(vault, capsys, "record", PROOF, "--result", "pass", "--stage", "1")
    text = review_queue_text(Vault(vault), day(3))
    section = text.split("## Proofs due")[1].split("##")[0]
    assert "Gamma Theorem (Part 1)" in section and "| 2 |" in section


# ---------- library mode ----------
def test_a_proof_card_is_on_the_track_with_its_state_in_the_card(tmp_path, capsys):
    lib = _library(tmp_path)
    state = lib / "_learn"
    connect(lib, state)
    _card(state, lib, "Axioms of Probability", "Term 1/Probability/week 1 - axioms.md")
    _card(state, lib, "Proof - Axioms of Probability", "Term 1/Probability/week 1 - axioms.md")
    before = {p: p.read_bytes() for p in lib.rglob("*") if p.is_file() and "_learn" not in p.parts}
    _run(state, capsys, "record", "Axioms of Probability", "--result", "pass")
    code, out = _run(state, capsys, "proofs")
    assert [x["name"] for x in out["new"]] == ["Proof - Axioms of Probability"]
    code, out = _run(state, capsys, "record", "Proof - Axioms of Probability", "--result", "pass", "--stage", "1")
    assert code == 0 and out["written_to"] == "frontmatter"
    card = (state / "Courses/NOTES/1 Probability/Proof - Axioms of Probability.md").read_text(encoding="utf-8")
    assert "proof_stage: 2" in card
    assert {p: p.read_bytes() for p in before} == before          # the library is untouched
