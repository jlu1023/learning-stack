---
name: connect
description: Bring your own notes - connect an existing folder of notes in any structure (Markdown, PDFs, photos of handwritten notes; Word and slides saved as PDF) without changing it, and build a separate deck of review cards with the same spaced schedule, linking back to the learner's files. Also rescans a connected folder for new or changed files.
argument-hint: "[folder] [--state-dir <path>]"
disable-model-invocation: true
---

Connect `$ARGUMENTS` (default: the current folder) as a read-only library.

**The library is never changed.** Do not edit, move, rename or delete anything in it. Everything goes in the state folder: `_learn/` inside the library by default, or the `--state-dir` path when the library is read-only, shared or synced. The engine refuses writes outside the state folder; never work around that.

1. **Load the rules.** Load the `method` skill (Grounding and trust, Integrity). `VL` means the engine command in the method skill.

2. **Set up the state folder** (first run only):
   - Ask, through `AskUserQuestion`, whether they use Obsidian with this folder (frontend `obsidian`: wikilinks, Dataview) or another editor (frontend `plain`: Markdown links, static tables, roadmap images). Default `plain`.
   - If they gave `--state-dir`, run `VL --state-dir "<path>" connect "<folder>" --frontend <frontend>`; otherwise `VL connect "<folder>" --frontend <frontend>`.
   - With a state folder outside the library, every later `VL` command needs it: tell them to open Claude Code in the state folder (simplest), set `LEARN_STATE_DIR`, or, if the library may hold one small file, add `state_dir: <path>` to a `vault-learning.yaml` in the library. Pass `--state-dir` yourself for the rest of this run.

3. **Scan.** Run `VL library-scan`. It lists every supported file with its status (`new`, `changed`, `current`), its hash, `integrity_flags`, `integrity_violations` and `orphan_cards`.

4. **Plan with the learner.** Show a short summary, then ask:
   - **Courses:** how the files group into courses (often one per top-level folder) and a short code for each (for example `PROB`). Record each as `Courses/<CODE>/<CODE> Syllabus.md` in the state folder, naming the library folders it covers.
   - **Units:** each source file (or a few related ones) becomes a unit: a module folder `Courses/<CODE>/<N> <Unit title>/`, numbered in the order the material is taught (ask when the file names do not show it). Give each folder a module MOC named after it, `<N> <Unit title>.md` (`type: moc`, a one-line intro naming the source file, then a list of links to its cards), so `/learn:roadmap` draws the unit's diagram.
   - **Which files to do now.** Large libraries go a few files at a time; say how many cards each file is likely to give.
   - **Flagged files:** list every file in `integrity_flags` and its reason. These look like problem sheets, exercise sets or past papers. Their cards **cite** questions and never hold solutions (step 6). If the learner says a flag is wrong (for example lecture notes titled "Solutions of differential equations"), treat the file as notes.

5. **Read each file** with the Read tool, as in the method's Reading sources: Markdown and text directly; PDFs page by page (formulas from the page images; over 10 pages, in ranges of at most 20); photos of handwritten notes as images, marking any word you cannot read as `[?: ...]` and asking rather than guessing. Files in the scan's `save_as_pdf` list (Word, PowerPoint, Keynote, Pages) cannot be read directly: ask the learner to save each as a PDF next to the original (it is their folder, so they do this, not you), then rescan.

6. **Write cards.** One card per idea worth recalling (a definition, a result with its conditions, a method, a key example), in the unit's folder in the state folder, using the configured link style:

   ```
   ---
   title: "<Card name>"
   type: card
   course: <CODE>
   module: "<Unit title>"
   source: "<path relative to the library, from library-scan>"
   source_anchor: "page 4"            # or a heading, "#Bayes' theorem"
   source_hash: <hash from library-scan>
   depends_on: []                     # earlier cards it needs
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   ---

   # <Card name>

   **From:** <a link back to the source file: "../../../" plus its `href_from_state`>, <anchor>

   ## Prompt
   <a recall question: state it with every condition, or apply it to a small new case>

   ## Answer
   <a short answer in your own words; maths in LaTeX>
   ```

   - Fill `depends_on` with earlier cards the idea needs, so the roadmap and the teaching order work.
   - Never copy long passages: a few lines in your own words, pointing back to the source.
   - **Flagged sources (problem sheets, exercises, past papers):** a card may only cite a question, with `cite_only: true`, a prompt like "Attempt question 3 of <source> on paper", and an Answer section that says only "Attempt it first." Never write a solution, a hint that gives it away, or a worked answer. `library-scan` reports any card from a flagged source whose Answer holds more as an integrity violation; fix every one.
   - Cards carry no learner-state fields: they start as unseen.

7. **Finish.** Run `VL roadmap all`, then `VL library-scan` again and confirm the files you did are `current` and `integrity_violations` is empty. Append `connect | <library>: <n> cards from <m> files` to `_meta/log.md` in the state folder. Report the cards written per file, the flagged files and how they were handled, anything marked `[?: ...]`, and the next step (`/learn:quiz` from tomorrow, `/learn:teach <CODE>` now).

**Rescans** (running `connect` again on a connected folder): run `VL library-scan` and handle, with the learner's agreement:
- `new` files: as above.
- `changed` files: reread the file and update its stale cards in place (prompt, answer, `source_anchor`, new `source_hash`, bumped `updated`). Keep each card's file name and learner state. If an idea is gone from the source, ask before deleting its card.
- `orphan_cards` (their source was removed or renamed): ask whether to point them at the new path or delete them.
