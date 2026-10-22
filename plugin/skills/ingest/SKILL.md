---
name: ingest
description: Turn new material (lecture slides, notes, a textbook section, a web page or a file in Inbox/) into atomic course notes in the vault, with depends_on links, then regenerate the course roadmap.
argument-hint: <file path | url | pasted content | (empty for Inbox/)>
---

Process new material into the vault: `$ARGUMENTS`.

1. **Read the rules.** Read the vault's `CLAUDE.md` (atomic notes, page types, frontmatter, LaTeX, cross-linking). Load the `method` skill's Grounding and trust section.

2. **Identify the input.**
   - A file path: read it. Course material normally sits in `Sources/courses/<COURSE>/`.
   - A URL: fetch it.
   - Pasted content: use it directly.
   - Empty: list `Inbox/` and process each file in turn, asking before processing more than 3.

3. **Classify it.** Course material needs a course code, a module and a `section:` (the source's numbered item, or slide and page). Ask if any is unclear. Anything else is a source: one note in `Sources/` with the source template, plus concept notes for its key ideas.

4. **Search the vault first** for notes on the same concepts (names and synonyms). Extend an existing note rather than creating a duplicate.

5. **Plan** when it is more than a couple of notes: the notes to create (type and path), the notes to extend, and the `depends_on` and `used_in` links. Show the plan and wait for confirmation.

6. **Write the notes.**
   - One concept per note, using the templates in `Templates/`: a chunk of a lecture is often a definition, a theorem, its proof and an example, as four linked notes.
   - Write in your own words. Never paste slides, textbook text or problem sheets wholesale; short quoted statements of definitions and theorems are fine, with `section:` saying where they come from.
   - Exercises the source leaves to the reader stay unsolved: the note cites the exercise and says "attempt it first".
   - Fill `depends_on` with every note the concept needs (the engine builds the roadmap from it) and `used_in` in the other direction.
   - New notes carry no learner-state fields: they start as unseen.
   - Maths is LaTeX. No em dashes.

7. **Regenerate the roadmap** for each course touched: `VL roadmap <COURSE>` (`VL` is the engine command in the `method` skill). For a new course, create `Courses/<CODE>/<CODE> Syllabus.md` first. Never hand-edit between the `%% roadmap:start %%` and `%% roadmap:end %%` markers.

8. **Log and report.** Append `ingest | <source>` to `_meta/log.md`. Report the notes created and extended, the roadmap's data gaps (broken links, cycles, `used_in` mismatches), and anything that needs the learner's attention.
