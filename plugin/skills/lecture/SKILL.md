---
name: lecture
description: Add what a lecturer said aloud to a lecture's notes, from a lecture transcript (for example one synced from Granola) - explanations and examples not on the slides, and what the lecturer stressed. The slides stay the authority for formulas.
argument-hint: <course> <lecture number> [transcript note]
disable-model-invocation: true
---

Fold a lecture transcript into the notes for `$ARGUMENTS`.

Only use transcripts the learner was allowed to make: see PRIVACY.md in the repository's `optional/granola/`. Transcripts stay private, in `Sources/transcripts/` (excluded from git by the vault's `.gitignore`).

1. **Load the rules.** Load the `method` skill (Grounding and trust) and read the vault's `CLAUDE.md`. `VL` means the engine command in the method skill.

2. **Find the inputs.**
   - The transcript: the note named in `$ARGUMENTS`, else the newest note in `Sources/transcripts/` whose title or date matches the lecture. If more than one could match, ask.
   - The unit: `VL unit <COURSE> <N>` gives its notes (`node_list`) and primer. Read them all.
   - The slides or lecture notes for the same lecture, from the notes' `sources` or `Sources/courses/<COURSE>/`. If there are none, say so and ask before going on: without them nothing in the transcript can be checked.

3. **Read the transcript against the slides** and sort what you find:
   - **Said aloud only:** explanations, intuitions, worked examples, analogies and warnings that are not on the slides.
   - **Emphasis:** what the lecturer stressed, repeated or called important, common mistakes they named, and anything they said about how it is assessed.
   - **Admin:** deadlines, changes to the course, reading. Report these in chat only; they do not go into notes.
   - **Discrepancies:** anything the transcript says that conflicts with the slides.

4. **The slides are the authority for formulas and statements.** Speech-to-text garbles mathematics, so:
   - never take a formula, statement or number from the transcript when the slides give it;
   - where the transcript seems to contradict the slides, keep the slides' version and list the discrepancy for the learner to check;
   - where a formula is only spoken (not on any slide), write it only if it is unambiguous, mark it "from the lecture, not on the slides; check", and list it in the report.

5. **Plan, then write.** Show the plan (which notes gain what) and wait for confirmation. Then, in each affected note:
   - add a `## From the lecture` section (or extend it), in your own words: the explanation or example, then one line of emphasis where there is any (for example "Stressed: check the hypotheses before applying it");
   - add the transcript note to `sources`;
   - write a new atomic note only for a genuinely new concept, from the templates in `Templates/`, with `depends_on` filled;
   - never quote more than a sentence of the transcript, and never name or quote other people in the room (students' questions are paraphrased without names).
   - Maths is LaTeX. No em dashes. Do not touch learner-state fields.

6. **Refresh.** If notes were added or `depends_on` changed, run `VL roadmap <COURSE>`. If the unit has a primer and the lecture changes its key ideas, update the primer and run `VL check-primer <COURSE>`.

7. **Log and report.** Append `lecture | <COURSE> <lecture>` to `_meta/log.md`. Report the notes changed, the emphasis captured, the admin items, and every discrepancy and spoken-only formula to check.
