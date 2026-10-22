---
name: primer
description: Big-picture primer for one lecture, week or module of a course (show it, or write it from the vault notes if missing), or the week-ahead overview across all courses. Use when the learner wants an overview of a unit before studying it.
argument-hint: <course> <unit number | next> | week
---

Give a primer for `$ARGUMENTS`.

1. **Load the rules.** Load the `method` skill, sections Primers, Week ahead, Grounding and trust, and Tone. `VL` means the engine command in the method skill.

2. **`week`:** give the week-ahead overview exactly as the method (Week ahead) says: read `Courses/_learning/Timetable.md`, run `VL unit <COURSE> all` for each course, write `Courses/_learning/Week Ahead.md`, and show one screen in chat. Stop there.

3. **Otherwise, resolve the unit.** Parse the course code. The unit is a number (`primer COURSE101 2`), or `next` for the unit of the next node to teach (`VL unit <COURSE> next`). Words that name the unit are fine too (`lecture 2`, `week 3`, `module 1`): take the number. Run `VL unit <COURSE> <N>`.
   - If the course has no such unit because its notes are not in the vault yet, say so in one line. If the slides or notes for it exist, ask the learner where they are (or to put them in `Sources/courses/<COURSE>/`); never write a primer from anything else, and never guess the content.

4. **Show or write it.**
   - If `primer` is set, read that note and show the chat version (method, Primers). Offer the prerequisite check through `AskUserQuestion`; it records nothing.
   - If not, read the unit's nodes (`node_list`), their notes, the previous and following units' primers or MOCs, the course's Exam Profile if it has one, and the source pages for the slides or textbook. Write the primer note in the method's format, link it from its module MOC, run `VL check-primer <COURSE>` and fix every problem until it passes. Then show the chat version.
   - If a source the learner needs to supply is missing or unreadable (slides not in `Sources/`, a PDF with no text layer), say exactly what is missing and ask for it, rather than writing from less.

5. **Log.** If a primer was written or updated, append `primer | <COURSE> <unit name>` under today's heading in `_meta/log.md`.

Never use past exam papers, their solutions or reserved sample papers. Chat maths is plain text or Unicode; the note's maths is LaTeX.
