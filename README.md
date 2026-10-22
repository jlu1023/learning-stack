# Learning Stack

A **Claude Code plugin** that turns your notes into a Socratic tutor: in an Obsidian vault, or in any folder of PDFs, slides, Word files, Markdown or photos of handwritten pages. It gives you a primer before each lecture, teaches one idea at a time from your own material, makes you work every step, quizzes you to lock each idea in, and brings it back on a spaced schedule until you know it. An optional module adds what your lecturer said aloud, from Granola lecture transcripts.

It is for students (and anyone working through a technical course) who want to *learn* their notes, not just store them: mathematics, statistics, economics, finance and other subjects with definitions, results and methods.

![A module roadmap generated from the example course's depends_on links](docs/screenshots/module-roadmap.png)

*A module roadmap, generated from the notes' `depends_on` links. Colours show mastery (grey unseen, amber learning, blue secure, green mastered) and update after every session.*

## Three ways to use it

| You have | Use | What happens |
|---|---|---|
| Obsidian, or you want it | **The vault** (`vault-template/`) | `/learn:ingest` turns your slides and notes into small linked notes; everything renders in Obsidian (links, Dataview tables, diagrams). Recommended. |
| Any editor (VS Code, Typora, a text editor) | **The vault in plain mode** (`frontend: plain`) | The same, with ordinary Markdown links, roadmaps exported as images and static review tables. |
| Your own folder of notes, in any structure | **Library mode** (`/learn:connect`) | Your files are left exactly as they are. The plugin builds a separate deck of review cards in `_learn/` (or a folder you choose) that link back to your files, on the same spaced schedule. |

## What you get

| Skill | What it does |
|---|---|
| `/learn:teach <course>` | Warm-up reviews, a primer for a new lecture, a probe for what you already know, a plan of at most three ideas, then one idea at a time with a lock-in quiz. Advances only on a pass. |
| `/learn:quiz [course\|mixed]` | Pure retrieval over what is due, mixed across courses with topic labels hidden, plus redos of your logged mistakes. |
| `/learn:primer <course> <unit>` | A five-minute overview of a lecture or week: the question it answers, where it sits, its key ideas, and a prerequisite check. `/learn:primer week` gives the week ahead. |
| `/learn:roadmap [course]` | Dependency maps, a suggested order and a data-gaps report, built from your notes' `depends_on` links. |
| `/learn:ingest <file or url>` | Turns a PDF (including scans and maths-heavy pages), Word file, slide deck, web page, Markdown file or photo of handwritten notes into small linked notes, in your own words. |
| `/learn:connect [folder]` | Connects your own folder of notes without changing it, and builds review cards that point back to your files. Problem sheets and past papers are cited, never solved. |
| `/learn:lecture <course> <n>` | Optional: adds what the lecturer said aloud, from a transcript, to that lecture's notes. The slides stay the authority for formulas. |
| `/learn:query <question>` | Answers from your notes, with a link for every claim. |
| `/learn:lint` | A health check: broken links, theorems without proofs, failing primers, the review backlog. |

Behind the skills is a small Python engine that keeps the learner state (`unseen`, `learning`, `secure`, `mastered`), schedules reviews on a 1, 3, 7, 21, 60-day ladder, converts documents, and draws the roadmaps. It runs on your machine; Claude Code sends the notes it reads to Claude as usual.

## Quick start

1. `python -m pip install PyYAML networkx` (and, to read PDFs and slides, `python -m pip install -r plugin/engine/requirements-ingest.txt`).
2. In Claude Code:

   ```
   /plugin marketplace add <owner>/learning-stack
   /plugin install learn@learning-stack
   ```

3. Either copy `vault-template/` and open Claude Code there (try `/learn:teach COURSE101` on the example course), or open Claude Code in your own notes folder and run `/learn:connect`.

Full steps: **[SETUP.md](SETUP.md)**, including using it without Obsidian and with your own notes.

## Using it without Obsidian

Set `frontend: plain` in `vault-learning.yaml` (library mode asks you). Links become ordinary relative Markdown links that any editor and GitHub follow, `/learn:roadmap` writes each diagram as an SVG image beside its note, and the Review Queue becomes static tables that `/learn:roadmap` regenerates. Nothing else changes. See [SETUP.md](SETUP.md#using-it-without-obsidian).

## Using your own notes

Open Claude Code in your notes folder and run `/learn:connect`. It reads your Markdown, PDFs, Word files, slides and photos where they are, never edits them, and writes review cards to `_learn/` (or, with `--state-dir`, to a folder outside a read-only, shared or synced library). Rerun it after you add or change notes: it finds new and changed files. See [SETUP.md](SETUP.md#using-your-own-notes).

## How it teaches

The loop is Eero Alvar's (probe, plan, teach one node, lock-in quiz), built on retrieval practice, spacing, interleaving, generation and hints rather than answers. [LEARNING-METHOD.md](LEARNING-METHOD.md) explains each piece and its evidence. You tune it to yourself in `Courses/_learning/Teaching Style.md`, including a different style per course (proof-led, methods-led or applied), each matched to how that course is examined.

## Integrity

The AI tests; you learn. Hints before answers, problem sheets and past papers cited rather than solved (also in your own connected notes), past papers used for exam format only, and your institution's rules on AI come first. Read [INTEGRITY.md](INTEGRITY.md) before using it for a course.

## Repository layout

```
.claude-plugin/marketplace.json   the plugin marketplace (this repository)
plugin/                           the Claude Code plugin "learn"
  skills/                         method, teach, quiz, primer, roadmap, ingest, connect, lecture, query, lint
  engine/                         the Python engine (vl.py, vault_learning/, tests/)
vault-template/                   the empty vault to copy: CLAUDE.md, templates, learning files, example course
optional/granola/                 lecture transcripts: plugin setup, template, PRIVACY.md
SETUP.md  LEARNING-METHOD.md  INTEGRITY.md  THIRD-PARTY.md  LICENSE
```

## Credits

Built by James Lu. The learning loop is Eero Alvar's ([How I Use AI to Learn Things](https://youtu.be/kzcI5F4tGiU)); some of the teaching rules are adapted from [Alvarmethod](https://github.com/vasanthsreeram/Alvarmethod) under the MIT licence (see [THIRD-PARTY.md](THIRD-PARTY.md)).

MIT licence: see [LICENSE](LICENSE).
