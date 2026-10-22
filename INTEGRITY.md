# Academic integrity

This plugin is built so that **the AI tests and you learn**. It is a tutor and a revision tool, not a way to have work done for you. These rules are built into its skills; please keep to them when you adapt it.

## Follow your institution's rules first

Universities and schools set their own rules on AI tools, recording lectures and sharing course material, and they differ between institutions and between courses. Read yours. Where they are stricter than anything here, they win. If you are unsure whether a use is allowed, ask your lecturer or department before relying on it.

## What the plugin does and does not do

- **It tests, it does not answer.** Teaching works by hints: a pointing question, then the name of the tool to use, then the first step only. A full solution comes only when you type `SOLUTION PLEASE`, and that counts as a fail on the note.
- **Problem sheets and coursework are cited, not solved.** Notes cite an exercise by number and say "attempt it first". The skills never write the solution to an exercise the source leaves to you, and never do assessed work. Anything you hand in must be your own, under your institution's rules.
- **Past papers are for format only.** You may read past papers to build a course's Exam Profile: the structure, the kinds of question and how answers are marked. The profile never quotes, paraphrases or solves a past question, and the skills never use past papers or their solutions as teaching material. Keep them for your own timed practice.
- **The same holds for your own connected notes.** In library mode (`/learn:connect`), files that look like problem sheets, exercise sets or past papers are flagged in the scan. Their review cards may only cite a question ("attempt question 3 first"), never hold its solution, and the scan reports any card that does. If a file is wrongly flagged (for example lecture notes titled "Solutions of differential equations"), you can say so and it is treated as notes.
- **Notes are in your own words.** `/learn:ingest` writes notes from your slides and textbooks in its own words, with a `section:` pointing at the source. It does not copy slides, textbook pages or problem sheets into the vault.
- **Sources stay private.** Slides, PDFs and transcripts live in `Sources/`, which `.gitignore` excludes. Do not publish your vault's `Sources/` folder or anyone else's course material.
- **Transcripts need permission.** Only transcribe lectures where your institution and lecturer allow it. See `optional/granola/PRIVACY.md`.
- **The AI can be wrong.** The skills teach from your notes, check computations in Python, and say "beyond the notes" when they go further. Check anything that matters against your course materials, and report errors in your notes so they get fixed.

## If you publish your own vault

Your course notes are your own work, but they may still contain material your institution does not allow you to share (for example, unpublished problem sheets or slides). Check before making a vault public, and never publish `Sources/`, your Error Log or your session files without thinking about what they contain.
