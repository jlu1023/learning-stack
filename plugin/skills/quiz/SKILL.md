---
name: quiz
description: Pure retrieval session, no teaching - due reviews and Error Log redos, weighted to older and previously failed notes, with topic labels hidden. Use when the learner asks to be quizzed or to review what is due.
argument-hint: "[course | mixed] [n]"
disable-model-invocation: true
---

Run a retrieval session for `$ARGUMENTS` (default: `mixed 8`).

1. **Load the rules.** Load the `method` skill (Primers, Week ahead, Quiz design, Spacing and interleaving, Logging, Tone) and read `Courses/_learning/Learner Profile.md` and `Courses/_learning/Teaching Style.md` (for course overrides and question format). `VL` means the engine command in the method skill.

2. **Week ahead.** If this is the first `teach` or `quiz` run of a new week, give the week-ahead overview first (method, Week ahead).

3. **Draw the items.** Run `VL due <course|mixed>`. It returns due nodes, already ordered by overdue days plus logged errors, and due Error Log redos.
   - Take `n` items (default 8). Include every due redo first, then the due nodes in order, which weights them towards older and previously failed nodes.
   - For `mixed`, interleave courses: never two items from the same module in a row when avoidable.
   - If fewer than `n` are due, say how many and run only those. Do not pad with unseen material; that is what `teach` is for.

4. **Ask, one item at a time,** with **no course, module or topic labels**: not in the question, options or preamble.
   - Build each question from the node's note: recall with every hypothesis, application to a new case, a hypothesis-dropping question, or a near-miss twin.
   - A redo reworks the logged mistake with fresh numbers, and it is labelled "(generated)" in the log.
   - Multiple choice goes through `AskUserQuestion`. Proofs and precise statements are free response. Apply any course override in Teaching Style (for example, statements and methods only for a methods course).
   - For multi-step problems, the learner restates the problem from the stem first.
   - Ask confidence from 1 to 5, then give the verdict, then name the node. Flag overconfidence.
   - No teaching: on a wrong answer, point at the first broken line, give the correct statement in one or two lines, and move on. Offer `teach` for that node at the end, and name its unit's primer if it has one (`VL graph <COURSE>` gives the node's `unit`, `VL unit <COURSE> <unit>` its `primer`), rather than re-explaining.

5. **Record.**
   - Run `VL record "<node>" --result pass|fail` after each item.
   - Append each mistake to `Courses/_learning/Error Log.md` in the method's format.
   - When a redo is answered correctly, append ` [redone:: YYYY-MM-DD]` to its Error Log line.

6. **Close.**
   - Write `Courses/_learning/sessions/YYYY-MM-DD <course|mixed> quiz.md` (`type: session`, the method's format, no plan diagram).
   - Run `VL roadmap all` (or the one course) to refresh the colours.
   - Append a `quiz | <course|mixed>` entry to `_meta/log.md`.
   - Report in chat: the score, overconfident misses, notes that dropped a level, and what is due next.
