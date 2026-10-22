---
name: ingest
description: Turn new material into atomic course notes in the vault - a PDF (including scans and maths-heavy pages), Markdown, a photo of handwritten notes, a web page or a file in Inbox/ (Word and PowerPoint as PDF) - with depends_on links, then regenerate the course roadmap.
argument-hint: <file path | url | pasted content | (empty for Inbox/)>
---

Process new material into the vault: `$ARGUMENTS`.

In library mode (`VL where` shows a `library`), the learner's files are not copied into notes: use the `connect` skill instead, which builds cards that point back to them.

1. **Read the rules.** Read the vault's `CLAUDE.md` (atomic notes, page types, frontmatter, LaTeX, links) and `vault-learning.yaml` (`frontend`: wikilinks for Obsidian, relative Markdown links for plain). Load the `method` skill's Grounding and trust section. `VL` means the engine command in the method skill.

2. **Get the text.**

   | Input | How |
   |---|---|
   | Markdown, text or saved web page | Read it. |
   | PDF | Read it with the Read tool, which shows every page's text and image (over 10 pages, read in ranges with `pages`, at most 20 a call). Take formulas from the page images, not from garbled text; scanned pages have only the image. |
   | Photo or scan of handwritten notes (.png, .jpg) | Read the image. Mark any word or symbol you cannot read as `[?: ...]` and ask the learner, never guess. |
   | Word, PowerPoint, Keynote or Pages file | Ask the learner to save it as PDF from the app that made it (File, Save as or Export, PDF), then read the PDF. |
   | URL | Fetch the page, save the readable text to `Sources/web/<title>.md` with its URL and today's date at the top, then work from that file. |
   | Pasted content | Use it directly. |
   | Nothing | List `Inbox/` and process each file in turn, asking before processing more than 3. |

   Never write notes from a file you could not read.

3. **Classify it.** Course material needs a course code, a module and a `section:` (the source's numbered item, or slide and page). Ask if any is unclear. Anything else is a source: one note in `Sources/` with the source template, plus concept notes for its key ideas.
   - **Problem sheets, exercise sets and past papers** are not turned into notes with answers. Exercises are cited ("attempt it first"); past papers may only inform an Exam Profile (style, never questions).

4. **Search the vault first** for notes on the same concepts (names and synonyms). Extend an existing note rather than creating a duplicate.

5. **Plan** when it is more than a couple of notes: the notes to create (type and path), the notes to extend, and the `depends_on` and `used_in` links. Show the plan and wait for confirmation.

6. **Write the notes.**
   - One concept per note, using the templates in `Templates/`: a chunk of a lecture is often a definition, a theorem, its proof and an example, as four linked notes.
   - Write in your own words. Never paste slides, textbook text or problem sheets wholesale; short quoted statements of definitions and theorems are fine, with `section:` saying where they come from.
   - Exercises the source leaves to the reader stay unsolved: the note cites the exercise and says "attempt it first".
   - Fill `depends_on` with every note the concept needs (the engine builds the roadmap from it) and `used_in` in the other direction, in the configured link style.
   - New notes carry no learner-state fields: they start as unseen.
   - Maths is LaTeX. Anything you could not read is `[?: ...]`. No em dashes.

7. **Regenerate the roadmap** for each course touched: `VL roadmap <COURSE>`. For a new course, create `Courses/<CODE>/<CODE> Syllabus.md` first. Never hand-edit between the roadmap markers.

8. **Log and report.** Append `ingest | <source>` to `_meta/log.md`. Report the notes created and extended, the roadmap's data gaps (broken links, cycles, `used_in` mismatches), every `[?: ...]` left for the learner, and any page you could only read as an image.
