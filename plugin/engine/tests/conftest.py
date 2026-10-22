import textwrap
from pathlib import Path

import pytest


def write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
    return p


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    """A tiny vault: course XX201 with two modules, reference courses PRE100 and PRE101,
    a duplicate-named note, a proof with a 'Part' suffix, and an example."""
    r = tmp_path
    write(r, "vault-learning.yaml", "reference_courses: [PRE100, PRE101]\n")
    write(r, "Courses/XX201/XX201 Syllabus.md", """
        ---
        title: "XX201 Syllabus"
        type: moc
        course: XX201
        updated: 2025-09-02
        ---
        # XX201

        Intro paragraph.

        ## Chapters
        - [[1 Basics]]
        """)
    write(r, "Courses/XX201/1 Basics/1 Basics.md", """
        ---
        title: "Basics"
        type: moc
        course: XX201
        updated: 2025-09-02
        ---
        # Basics

        Intro.

        ## Definitions
        - [[Alpha]]
        - [[Beta]]

        ## Theorems
        - [[Gamma Theorem]]
        """)
    write(r, "Courses/XX201/1 Basics/Alpha.md", """
        ---
        type: definition
        course: XX201
        section: "1.1"
        lecture: 1
        depends_on: ["[[Set]]"]
        used_in: ["[[Beta]]", "[[Gamma Theorem]]"]
        ---
        # Alpha
        """)
    write(r, "Courses/XX201/1 Basics/Beta.md", """
        ---
        type: definition
        course: XX201
        section: "1.2"
        lecture: 1
        depends_on: ["[[Alpha|the alpha]]", "[[Courses/PRE101/8 Continuity/Extreme Value Theorem]]"]
        ---
        # Beta
        """)
    write(r, "Courses/XX201/1 Basics/Gamma Theorem.md", """
        ---
        type: theorem
        course: XX201
        section: "1.3"
        lecture: 2
        depends_on: ["[[Beta#Statement]]"]
        used_in: ["[[Delta Method]]"]
        ---
        # Gamma Theorem
        """)
    write(r, "Courses/XX201/1 Basics/Proof - Gamma Theorem (Part 1).md", """
        ---
        type: proof
        course: XX201
        depends_on: ["[[Alpha]]", "[[Lemma Zeta]]"]
        ---
        # Proof

        **Theorem:** [[Gamma Theorem]], part (1)
        """)
    write(r, "Courses/XX201/1 Basics/Lemma Zeta.md", """
        ---
        type: lemma
        course: XX201
        section: "1.2.5"
        lecture: 2
        depends_on: ["[[Alpha]]"]
        ---
        # Lemma Zeta
        """)
    write(r, "Courses/XX201/1 Basics/Example - Alpha in Action.md", """
        ---
        type: example
        course: XX201
        depends_on: ["[[Alpha]]", "[[Beta]]"]
        ---
        # Example
        """)
    write(r, "Courses/XX201/2 Methods/2 Methods.md", """
        ---
        title: "Methods"
        type: moc
        course: XX201
        updated: 2025-09-02
        ---
        # Methods

        ## Methods
        - [[Delta Method]]
        """)
    write(r, "Courses/XX201/2 Methods/Delta Method.md", """
        ---
        type: method
        course: XX201
        section: "2.1"
        lecture: 3
        depends_on: ["[[Gamma Theorem]]", "[[Nowhere Note]]", "[[Linear Transformation]]"]
        ---
        # Delta Method
        """)
    write(r, "Courses/PRE101/8 Continuity/Extreme Value Theorem.md", """
        ---
        type: theorem
        course: PRE101
        ---
        # EVT
        """)
    write(r, "Courses/PRE100/3 Opt/Extreme Value Theorem.md", """
        ---
        type: theorem
        course: PRE100
        ---
        # EVT
        """)
    write(r, "Courses/PRE101/2 Sets/Set.md", """
        ---
        type: definition
        course: PRE101
        ---
        # Set
        """)
    write(r, "Courses/PRE101/14 Vector Spaces/Linear Transformation.md", "---\ntype: definition\n---\n# LT\n")
    write(r, "Courses/PRE100/12 LT/Linear Transformation.md", "---\ntype: definition\n---\n# LT\n")
    (r / "Courses/_learning").mkdir(parents=True)
    return r
