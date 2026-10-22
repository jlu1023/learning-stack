"""The built-in YAML reader matches PyYAML on frontmatter (PyYAML is optional)."""
import datetime as dt
from pathlib import Path

import pytest

from vault_learning import miniyaml
from vault_learning.library import STATE_FILES
from vault_learning.vault import FM_RE, parse_frontmatter

ROOT = Path(__file__).resolve().parents[3]

SAMPLES = [
    'title: "A \\"quoted\\" title"\ntype: definition\n',
    "depends_on: [\"[[Alpha]]\", \"[[Beta|the beta]]\"]\nused_in: []\n",
    "depends_on: [[Alpha]]\n",                                    # unquoted wikilink: nested list
    "depends_on:\n  - \"[[Alpha]]\"\n  - Beta\n",
    "tags:\n- one\n- two\n",                                      # list at the key's indent
    "created: 2026-01-01\nupdated: 2026-01-01T10:30:00\n",
    "a: 2026-05-28T20:39:40Z\nb: 2026-05-27T11:50:00+01:00\nc: 2026-05-27 11:50:00.25 -05:30\n",
    "lecture: 3\nsection: \"1.2\"\nratio: 0.5\nflag: true\nnone: null\nempty:\nprimer: False\n",
    "title: 'It''s fine'\npath: C:/Users/x\nurl: https://example.org/a#b\n",
    "note: text # a comment\n# a whole-line comment\nk: v\n",
    "results: {passed: [A, B], failed: [], reviews: {passed: 1, failed: 0}}\n",
    "extra_courses:\n  Reading:\n    root: \"Reading/\"\n    exclude: [\"Inbox\"]\n    mixed_cap: 1\n",
    "summary: |\n  Line one\n  Line two\nafter: x\n",
    "folded: >\n  one\n  two\n\n  three\n",
    "aliases: [Bayes, \"Bayes' rule\"]\n",
    "stopped_at: \"Boole's Inequality, rung 3\"\n",
    "mastery: learning\nmastery_since: 2025-10-02\nreview_interval: 3\nfail_streak: 0\n",
]


def _frontmatters():
    for p in sorted((ROOT / "plugin" / "vault-template").rglob("*.md")):
        m = FM_RE.match(p.read_text(encoding="utf-8"))
        if m and m.group(1) and "{{" not in m.group(1):            # Obsidian template placeholders are not YAML
            yield p.name, m.group(1)
    for rel, text in STATE_FILES.items():
        m = FM_RE.match(text)
        if m and m.group(1):
            yield rel, m.group(1)
    yield "vault-learning.yaml", (ROOT / "plugin" / "vault-template" / "vault-learning.yaml").read_text(encoding="utf-8")


@pytest.mark.parametrize("text", SAMPLES)
def test_samples_match_pyyaml(text):
    yaml = pytest.importorskip("yaml")
    assert miniyaml._Reader(text).document() == yaml.safe_load(text)


def test_every_template_frontmatter_matches_pyyaml():
    yaml = pytest.importorskip("yaml")
    checked = 0
    for name, text in _frontmatters():
        assert miniyaml._Reader(text).document() == yaml.safe_load(text), name
        checked += 1
    assert checked > 20


def test_values_without_pyyaml():
    d = miniyaml._Reader(SAMPLES[5] + SAMPLES[7]).document()
    tz = miniyaml._Reader(SAMPLES[6]).document()
    assert tz["a"].tzinfo == dt.timezone.utc and tz["b"].utcoffset() == dt.timedelta(hours=1)
    assert d["created"] == dt.date(2026, 1, 1) and d["updated"] == dt.datetime(2026, 1, 1, 10, 30)
    assert d["section"] == "1.2" and d["lecture"] == 3
    assert d["flag"] is True and d["primer"] is False and d["none"] is None and d["empty"] is None
    assert miniyaml._Reader(SAMPLES[2]).document() == {"depends_on": [["Alpha"]]}


@pytest.mark.parametrize("bad", ["review: 2026-13-40\n", "created: {{date:YYYY-MM-DD}}\n", "a: &anchor x\n",
                                 "- a: 1\n  b: 2\n",
                                 "k: [unclosed\n", "k: v\n  bad: indent\n", "\tk: v\n"])
def test_unsupported_or_broken_yaml_raises_yamlerror(bad):
    with pytest.raises(miniyaml.YAMLError):
        miniyaml._Reader(bad).document()


def test_an_impossible_date_is_unreadable_frontmatter_not_a_crash():
    # with PyYAML this used to raise ValueError and stop the whole roadmap
    fm, err, _ = parse_frontmatter("---\nreview: 2026-13-40\n---\n# x\n")
    assert fm == {} and err and err.startswith("YAML error")
