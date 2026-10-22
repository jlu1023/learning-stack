"""Courses that live outside Courses/<CODE>/ (`extra_courses` in vault-learning.yaml)."""
import datetime as dt

import pytest

from vault_learning import config
from vault_learning.cli import EngineError, _find_note, due_items
from vault_learning.graph import CourseGraph, canonical_code, roadmap_courses
from vault_learning.units import CourseUnits
from vault_learning.vault import Vault, owner_label

from .conftest import write

TODAY = dt.date(2025, 10, 10)


@pytest.fixture
def reading(vault):
    """Adds the Reading course under Library/Reading/: one module '1 Logic' with a
    module MOC and three notes, an excluded Methods/ folder, and a root-level note."""
    write(vault, "vault-learning.yaml", """
        reference_courses: [PRE100, PRE101]
        extra_courses:
          Reading:
            root: "Library/Reading/"
            exclude: ["Methods"]
            mixed_cap: 1
        unit_labels:
          Reading: Chapter
        """)
    write(vault, "Library/Reading/Reading Syllabus.md", """
        ---
        type: moc
        course: Reading
        ---
        # Reading
        """)
    write(vault, "Library/Reading/1 Logic/1 Logic.md", """
        ---
        type: moc
        course: Reading
        ---
        # Logic
        """)
    write(vault, "Library/Reading/1 Logic/Premise.md", """
        ---
        type: definition
        course: Reading
        depends_on: ["[[Alpha]]"]
        mastery: learning
        mastery_since: 2025-10-02
        last_quizzed: 2025-10-02
        review: 2025-10-03
        review_interval: 1
        ---
        # Premise
        """)
    write(vault, "Library/Reading/1 Logic/Argument.md", """
        ---
        type: definition
        course: Reading
        depends_on: ["[[Premise]]", "[[Outline Method]]"]
        mastery: learning
        mastery_since: 2025-10-02
        last_quizzed: 2025-10-02
        review: 2025-10-04
        review_interval: 1
        ---
        # Argument
        """)
    write(vault, "Library/Reading/1 Logic/Fallacy.md", """
        ---
        type: definition
        course: Reading
        depends_on: ["[[Argument]]"]
        ---
        # Fallacy
        """)
    write(vault, "Library/Reading/Methods/Outline Method.md", """
        ---
        type: method
        ---
        # Outline Method
        """)
    write(vault, "Library/Reading/Loose Note.md", """
        ---
        type: concept
        course: Reading
        ---
        # Loose Note
        """)
    return vault


def test_canonical_code_is_case_insensitive_for_registered_courses(reading):
    Vault(reading)
    assert canonical_code("READING") == "Reading"
    assert canonical_code("reading") == "Reading"
    assert canonical_code("course101") == "COURSE101"


def test_roadmap_courses_includes_registered_course_with_moc(reading):
    assert roadmap_courses(Vault(reading)) == ["XX201", "Reading"]


def test_registered_course_absent_without_settings(vault):
    assert "Reading" not in roadmap_courses(Vault(vault))
    assert config.EXTRA_COURSES == {}


def test_registered_course_graph_paths_modules_and_exclusions(reading):
    cg = CourseGraph(Vault(reading), "READING")
    assert cg.code == "Reading"
    assert cg.course_moc == "Library/Reading/Reading Syllabus.md"
    assert cg.roadmap_rel == "Library/Reading/Reading Roadmap.md"
    assert [m.folder for m in cg.modules] == ["1 Logic"]
    names = sorted(cg.name(n) for n in cg.nodes)
    assert names == ["Argument", "Fallacy", "Premise"]       # not Methods/, not the root note
    assert cg.G.has_edge("Library/Reading/1 Logic/Premise.md", "Library/Reading/1 Logic/Argument.md")
    # a note in an excluded folder counts as an external prerequisite
    ext = cg.ext["Library/Reading/1 Logic/Argument.md"]
    assert ext == {"Library/Reading/Methods/Outline Method.md"}
    # a prerequisite in another course is external too
    assert cg.ext["Library/Reading/1 Logic/Premise.md"] == {"Courses/XX201/1 Basics/Alpha.md"}
    assert owner_label("Library/Reading/1 Logic/Premise.md") == "Reading"


def test_find_note_accepts_registered_course_notes_only(reading):
    v = Vault(reading)
    assert _find_note(v, "Argument") == "Library/Reading/1 Logic/Argument.md"
    with pytest.raises(EngineError):
        _find_note(v, "Outline Method")                      # excluded folder: not a course note


def test_due_mixed_caps_registered_course_but_single_course_does_not(reading):
    v = Vault(reading)
    mixed = due_items(v, "mixed", TODAY, 0)
    assert [i["name"] for i in mixed["due"] if i["course"] == "Reading"] == ["Premise"]   # most overdue kept
    alone = due_items(v, "reading", TODAY, 0)
    assert sorted(i["name"] for i in alone["due"]) == ["Argument", "Premise"]
    assert all(i["course"] == "Reading" for i in alone["due"])


def test_unit_labels_come_from_settings(reading):
    assert CourseUnits(Vault(reading), "Reading").units[1].label == "Chapter"


def test_bad_unit_label_is_refused(vault):
    write(vault, "vault-learning.yaml", "unit_labels:\n  XX201: Session\n")
    with pytest.raises(ValueError):
        Vault(vault)
