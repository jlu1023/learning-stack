# Learning vault: schema for Claude Code

This vault holds course notes in small linked pieces, plus the learner's progress. The `learn` plugin's skills (`/learn:teach`, `/learn:quiz`, `/learn:primer`, `/learn:roadmap`, `/learn:ingest`, `/learn:lecture`, `/learn:query`, `/learn:lint`) work on it. This file sets how notes are written; the plugin's `method` skill sets how teaching works.

## Hard rules

- Work only inside this folder.
- **Learner state is written only by the engine** (`record`), never by hand. See Learner state below.
- Never rewrite a `human_authored: true` note without asking.
- Never put copyrighted material into notes wholesale: notes are in your own words, with `section:` pointing at the source. Exercises the source leaves to the reader stay unsolved (see INTEGRITY.md in the repository).
- Past exam papers are never teaching material. A course's Exam Profile may record how the course is examined (style), never what was asked.
- Do not touch `.obsidian/`. Do not run `git` here unless the owner asks.

## Folders

| What | Where |
|---|---|
| Course note | `Courses/<CODE>/<N> <Module>/<Note>.md` |
| Course MOC | `Courses/<CODE>/<CODE> Syllabus.md` |
| Module MOC | `Courses/<CODE>/<N> <Module>/<N> <Module>.md` (same name as the folder) |
| Generated roadmap | `Courses/<CODE>/<CODE> Roadmap.md` (never hand-edit) |
| Unit primer | `Courses/<CODE>/<N> <Module>/<CODE> <Unit> <N> Overview - <Title>.md` |
| Exam Profile | `Courses/<CODE>/<CODE> Exam Profile.md` |
| Learning files | `Courses/_learning/` (Learner Profile, Teaching Style, Error Log, Review Queue, Timetable, Week Ahead, progress, sessions/) |
| Raw material | `Sources/courses/<CODE>/` (slides, notes, PDFs), `Sources/transcripts/` (lecture transcripts): both excluded from git |
| Unsorted capture | `Inbox/` |
| Operation log, index | `_meta/log.md` (appended), `_meta/Vault Index.md` (generated) |
| Note templates | `Templates/` |
| Engine settings | `vault-learning.yaml` |

Module folders are number-prefixed in syllabus order (`1 Probability Spaces/`, `2 Conditional Probability/`). Note filenames are not prefixed: the concept name is the identity. Notes sit flat in their module folder.

## Atomic notes: one concept per note

- Each definition, theorem, lemma, proof, method and named result gets its own note. A proof is always a separate note from its theorem, named `Proof - <Theorem>` or `Proof of <Theorem>`, with a `**Theorem:** [[<Theorem>]]` line.
- A note on "Limits" covering the definition, the algebra of limits and the sandwich theorem is four to eight notes, not one.
- Word ceilings (past one is a split candidate, not a failure): definition 400, theorem or lemma 350, proof 500, method 400, other types 300. Set `indivisible: true` once a split has been considered and rejected.

## Note types

- `definition`, `theorem`, `lemma`, `corollary`, `proposition`, `axiom`, `method`, `concept`, `intuition`: the nodes the engine teaches and quizzes.
- `proof`: folded into its theorem in the roadmap.
- `example`: drawn beside the notes it illustrates; never a prerequisite.
- `question`: an active-recall question.
- `moc`: navigation (course and module MOCs, primers, roadmaps).
- `source`: captured raw material; its body is not edited.
- `reference`, `summary`, `session`, `report`: working files and generated output.

## Frontmatter

```yaml
---
title: "..."
type: definition
course: COURSE101
module: "Probability Spaces"          # matches the folder, without the number
section: "1.2"                        # the source's numbered item, or slide and page
lecture: 1                            # optional: the lecture that covers it
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: seedling | growing | mature
depends_on: ["[[Note A]]", "[[Note B]]"]   # every note this one needs
used_in: ["[[Note X]]"]                    # the reverse direction
sources: ["[[Source Note]]"]
examinable: true
proof_pending: true                   # optional, on a theorem whose proof is out of scope
human_authored: true                  # optional: never rewritten without asking
---
```

- Bump `updated:` on every content edit. Wikilinks in frontmatter lists are quoted strings.
- **`depends_on` is what the roadmap is built from.** List every definition and result the note uses. A link to another course's note becomes an external prerequisite.

### Learner state

```yaml
mastery: unseen | learning | secure | mastered   # missing = unseen
mastery_since: YYYY-MM-DD
last_quizzed: YYYY-MM-DD
review: YYYY-MM-DD
review_interval: 1 | 3 | 7 | 21 | 60
fail_streak: 0 | 1                               # consecutive fails; the second in a row drops a level
```

- Written only by the engine's `record` command (the `teach` and `quiz` skills call it), never by hand, and never in bulk.
- A learner-state write does not bump `updated:`, which keeps meaning "the content changed".
- For a `human_authored: true` note, learner state goes in `Courses/_learning/progress.md` and the note is never touched.
- New notes carry no learner-state fields.

## LaTeX

- All mathematics in notes is LaTeX: `$...$` inline, `$$...$$` on its own lines for display. No Unicode maths symbols inside mathematics (`$\forall \varepsilon > 0$`, not `∀ε>0`).
- Headings with mathematics wrap it: `# AM $\geq$ GM`.
- Use `\varepsilon`, `\varphi`, `\mathbb{R}` for number sets, `\mathcal{F}` for script letters, and `\mid` in set-builder notation: `$\{x \in \mathbb{R} \mid x > 0\}$`.
- Never put mathematics in code blocks.
- Chat replies are different: a terminal cannot render LaTeX, so maths in chat is plain text or Unicode.

## Dates

- Frontmatter, task markers and filenames that sort: ISO (`2026-01-30`).
- Prose: day month year (`30 January 2026`).

## Links

- **Style follows `frontend:` in `vault-learning.yaml`.** `obsidian`: wikilinks, `[[Note]]` and `[[Note|text]]`. `plain` (any other editor): relative Markdown links, `[Note](../2%20Module/Note.md)`, with spaces as `%20`; in frontmatter too: `depends_on: ["[Note](Note.md)"]`. The engine resolves both styles, so a vault can switch, but write new links in the configured one.
- Every concept, theorem and method note has 3 to 6 deliberate outbound wikilinks, at least one `depends_on` or `used_in` entry, and a place in its module MOC.
- Theorems link to their proof and to every definition in their statement; proofs link back to the theorem and to each result a step relies on; definitions list the theorems that use them under "Used in".
- **Reports never wikilink.** Logs, session files, the Error Log, roadmaps' suggested order, lint reports and the Vault Index name notes in plain text, so they add no false edges to the graph.

## Templates

Use the files in `Templates/` (Obsidian's core Templates plugin inserts them): Definition, Theorem, Proof, Method, Example, Intuition, Question, Module MOC, Course Syllabus, Primer.

## Tags

Only these hashtags are used; links and MOCs do the rest.

- `#stub`: needs expanding
- `#contradicts`: a conflict to resolve
- `#examinable` / `#non-examinable`
- `#ToProcess`: captured but not yet turned into notes

Never invent a new tag; add it here first.

## Roadmaps and primers

- `<CODE> Roadmap.md` (`generated: true`) holds the course map, the spine, a suggested order, links to other courses and the data gaps. Module MOCs carry a generated diagram between `%% roadmap:start %%` and `%% roadmap:end %%`; the course MOC carries one link line between the same markers. Never edit between the markers: the generator overwrites them and leaves everything else alone.
- Rerun `/learn:roadmap <COURSE>` after adding notes (`/learn:ingest` does it as its last step).
- A primer is a `type: moc` note with `primer: true`, `course:` and `unit:`, linked from its module MOC by an `Overview:` line outside the markers. Its format is in the `method` skill; `check-primer` lints it.
- Courses listed under `reference_courses` in `vault-learning.yaml` get no roadmap; their notes appear only as external prerequisites.

## Working style

- Search before creating a note; extend rather than duplicate.
- Edit rather than rewrite; keep the rest of the file.
- Mark anything uncertain inline: `[?: claim to check]`.
- Terse notes: bullets and short paragraphs, no filler. Callouts (`> [!definition]`, `> [!theorem]`) are welcome.
- No em dashes in notes: use a colon, comma or full stop.
- Append one line per operation to `_meta/log.md` under a day-month-year heading.
