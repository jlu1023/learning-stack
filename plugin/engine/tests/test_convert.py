"""Source conversion (vault_learning.convert) and the `convert` command."""
import json
import shutil
from pathlib import Path

import pytest

from vault_learning import convert as cv
from vault_learning.cli import convert_json
from vault_learning.vault import Vault

SAMPLE = Path(__file__).parent / "fixtures" / "sample-lecture.pdf"


def test_render_reason_spots_scans_and_maths():
    assert "scan" in cv.render_reason("   ")
    assert "mathematics" in cv.render_reason("Then P(A) = Σ P(A | Bᵢ) P(Bᵢ) for all i ∈ I and B ⊆ Ω " * 2)
    assert cv.render_reason("A plain paragraph of prose with no symbols at all, long enough to count.") is None


def test_pdf_with_pypdfium2_reads_text_and_renders_the_scan(tmp_path):
    pytest.importorskip("pypdfium2")
    pytest.importorskip("PIL")
    m = cv.convert(SAMPLE, tmp_path / "out")
    assert m["backend"] == "pypdfium2" and len(m["pages"]) == 2
    text = Path(m["text_file"]).read_text(encoding="utf-8")
    assert "Bayes" in text and "<!-- page 2 -->" in text
    p1, p2 = m["pages"]
    assert p1["chars"] > 100 and p2["chars"] == 0
    assert p2["image"] == "page-002.png" and "scan" in p2["why"]
    assert (tmp_path / "out" / "page-002.png").stat().st_size > 1000
    assert json.loads((tmp_path / "out" / "manifest.json").read_text(encoding="utf-8"))["hash"] == m["hash"]


def test_render_none_writes_no_images(tmp_path):
    pytest.importorskip("pypdfium2")
    m = cv.convert(SAMPLE, tmp_path / "out", render="none")
    assert m["images"] == [] and not list((tmp_path / "out").glob("*.png"))


def test_pdf_falls_back_to_poppler(tmp_path, monkeypatch):
    if not shutil.which("pdftotext"):
        pytest.skip("poppler's pdftotext not installed")
    monkeypatch.setattr(cv, "_pdf", cv._pdf_poppler)
    m = cv.convert(SAMPLE, tmp_path / "out")
    assert m["backend"].startswith("poppler") and len(m["pages"]) == 2
    assert "Conditional" in Path(m["text_file"]).read_text(encoding="utf-8")


def test_missing_pdf_tools_give_install_instructions(tmp_path, monkeypatch):
    monkeypatch.setattr(cv, "_which", lambda *n: None)
    with pytest.raises(cv.MissingTool) as e:
        cv._pdf_poppler(SAMPLE, tmp_path, "auto", 150)
    assert "pip install pypdfium2" in str(e.value) and "poppler" in str(e.value)


def test_missing_pandoc_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(cv, "_which", lambda *n: None)
    (tmp_path / "notes.docx").write_bytes(b"PK")
    with pytest.raises(cv.MissingTool) as e:
        cv.convert(tmp_path / "notes.docx", tmp_path / "out")
    assert e.value.tool == "pandoc" and "pandoc.org" in e.value.install


def test_docx_with_pandoc(tmp_path):
    if not shutil.which("pandoc"):
        pytest.skip("pandoc not installed")
    import subprocess
    md = tmp_path / "in.md"
    md.write_text("# Week 1\n\nA **definition** with $x^2 \\leq 1$.\n\n| Law | Mean |\n|---|---|\n"
                  "| Uniform(0, 1) | 1/2 |\n", encoding="utf-8")
    try:                                   # an image, when Pillow is there to draw one
        from PIL import Image
        Image.new("RGB", (8, 8), "white").save(tmp_path / "fig.png")
        md.write_text(md.read_text(encoding="utf-8") + "\n![fig](fig.png)\n", encoding="utf-8")
    except ImportError:
        pass
    subprocess.run(["pandoc", "in.md", "-o", "w.docx"], check=True, cwd=tmp_path)   # Word equations (OMML)
    m = cv.convert(tmp_path / "w.docx", tmp_path / "out")
    text = Path(m["text_file"]).read_text(encoding="utf-8")
    assert "definition" in text and "x^{2} \\leq 1" in text            # the equation comes back as LaTeX
    assert "| Uniform(0, 1) | 1/2 |" in text.replace("  ", " ")         # a pipe table, not a padded one
    for rel in m["media"]:                                              # images linked relatively, files kept
        assert rel.startswith("media/") and (tmp_path / "out" / rel).exists() and f"]({rel})" in text


def test_pptx_slide_text_and_notes(tmp_path):
    pptx = pytest.importorskip("pptx")
    prs = pptx.Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = "Independence"
    s.placeholders[1].text = "A and B are independent if P(A and B) = P(A) P(B)"
    s.notes_slide.notes_text_frame.text = "Stress: independence is not disjointness."
    prs.save(tmp_path / "deck.pptx")
    m = cv.convert(tmp_path / "deck.pptx", tmp_path / "out", render="none")
    text = Path(m["text_file"]).read_text(encoding="utf-8")
    assert "## Slide 1" in text and "Independence" in text and "Speaker notes: Stress" in text


def test_images_and_markdown_need_no_conversion(tmp_path):
    (tmp_path / "page.jpg").write_bytes(b"\xff\xd8\xff")
    (tmp_path / "n.md").write_text("# Note\n", encoding="utf-8")
    img = cv.convert(tmp_path / "page.jpg", tmp_path / "o1")
    assert img["images"] == [str(tmp_path / "page.jpg")] and "[?: ...]" in img["note"]
    assert cv.convert(tmp_path / "n.md", tmp_path / "o2")["text_file"] == str(tmp_path / "n.md")
    with pytest.raises(ValueError):
        (tmp_path / "x.xyz").write_text("?")
        cv.convert(tmp_path / "x.xyz", tmp_path / "o3")


def test_convert_command_keeps_output_inside_the_vault(vault, tmp_path):
    v = Vault(vault)
    assert "must be inside" in convert_json(v, str(SAMPLE), str(tmp_path.parent / "elsewhere"))["error"]
    pytest.importorskip("pypdfium2")
    m = convert_json(v, str(SAMPLE), None, render="none")
    assert Path(m["out"]).resolve().is_relative_to(vault.resolve() / ".converted")
