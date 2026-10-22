---
title: "Error Log"
type: reference
created: 2026-01-01
updated: 2026-01-01
---

# Error Log

One line per mistake, appended by `/learn:teach` and `/learn:quiz` in this format (the engine's `due` command and the Review Queue read it):

`- [date:: YYYY-MM-DD] [course:: CODE] [node:: Note Name] [category:: ...] [redo:: YYYY-MM-DD] What they did: ... First wrong line: "..." Cue they should have noticed: ...`

- **Categories:** logic, missing hypothesis, algebra, imported method or number, misread question, note error, overconfidence.
- **Redo date:** 3 to 7 days after the mistake. `/learn:quiz` includes every due redo, and appends `[redone:: YYYY-MM-DD]` when it is answered correctly.
- **Format rules:** node names are plain text, not links. Maths is LaTeX.

## Entries
