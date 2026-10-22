---
name: teach
description: Socratic teaching session on one course - primer for a new lecture, probe, plan, teach one node at a time, and lock in each with a quiz. Use when the learner asks to be taught a course, module or note from their vault.
argument-hint: <course> [module | note name | next | deepen | resume]
disable-model-invocation: true
---

Run a teaching session for `$ARGUMENTS`.

1. **Load the rules.** Load the `method` skill and follow it for everything below. Then read `Courses/_learning/Learner Profile.md` and `Courses/_learning/Teaching Style.md`; Teaching Style overrides the method's teaching and probing defaults, as the method says. `VL` means the engine command in the method skill.

2. **Load the graph.** Parse the course code from `$ARGUMENTS` and run `VL graph <COURSE>`. If the course has no roadmap, run `VL roadmap <COURSE>` first. Resolve the target:
   - `next` (or nothing): first look for **pass 2 candidates**: nodes in this course at `learning` whose `mastery_since` is at least 3 days ago (from the learner-state fields in `VL graph`). If any exist, plan up to 3 of them, oldest first. Otherwise run `VL next <COURSE>`.
   - `deepen`: plan the course's `learning` nodes for pass 2 now, even if fewer than 3 days have passed (for a homework deadline).
   - a module name: that module's nodes, in suggested order.
   - a note name: that node.
   - `resume` (with or without a course): find the most recent session file in `Courses/_learning/sessions/` with `status: open` (for that course if one is given). Read its plan, its per-node log, its `stopped_at` node and rung, and its last exchanges, plus any Error Log entries from that session. Recap in at most three lines (where they stopped, what passed, what failed), then skip the warm-up and the probe for nodes that session already confirmed, and continue from the recorded node and rung. Keep writing to the same session file. If no open session exists, say so and fall back to `next`.

3. **Week ahead, then warm-up.** If this is the first `teach` or `quiz` run of a new week, give the week-ahead overview first (method, Week ahead). Then the warm-up: run `VL due mixed --limit 6` and ask 2 or 3 retrieval questions from the due items and redos, mixed across courses, with **no course or topic labels shown**. Use the confidence-then-verdict flow, then `VL record "<node>" --result pass|fail` for each. If nothing is due, say so in one line and skip.

4. **Primer for a new unit.** Take the first node the target resolves to and its `unit` from `VL graph <COURSE>`, then run `VL unit <COURSE> <unit>`. If `started` is false, give the unit's primer per the method (Primers): show the saved primer, or write it first if there is none and run `VL check-primer <COURSE>` until it passes; give the short chat version; run its prerequisite check. Skip this step for `resume`, `deepen` and pass 2 candidates, and when `started` is true. When later in the session a planned node opens another unstarted unit, give that unit's primer before teaching the node.

5. **Probe.** Use `AskUserQuestion` to find the edge of what they know (after a primer, start from where its prerequisite check left off):
   - Start wide on the target module or node.
   - Then binary-search down the `prereqs` chain (and `external_prereqs` for earlier courses): if they know a node, assume its prerequisites; if not, probe them.
   - Include "I don't know" as an option on every probe question.
   - A right answer with no reason counts as **edge**, not known: follow up with "why" before crediting it.
   - Probing records nothing. It only shapes the plan.

6. **Plan.** Build the session's prerequisite graph for the gaps: **at most 3 nodes per session**, prerequisites first, so a session fits one sitting of 30 to 45 minutes. If the gap needs more, plan the first 3 and list the rest as next steps for `resume`.
   - Create the session file `Courses/_learning/sessions/YYYY-MM-DD <COURSE> <topic>.md` (format in the method) holding the plan as a small Mermaid diagram, with frontmatter `status: open` and `stopped_at` set to the first node, rung 0. Use plain labels and no `internal-link` class, so the session file adds nothing to the graph.
   - Show the ordered list in chat as plain text.

7. **Teach and lock in,** one node at a time, per the method and the passes and ladder in Teaching Style:
   - **Choose the pass from the node's learner state:** `unseen` is pass 1; `learning` is pass 2; `secure` or `mastered` is pass 3. If the learner says `pass 1` or `deepen`, use that instead. If a recall question in pass 2 or 3 fails, record the fail and switch that node to pass 1 for the rest of the session. Record the pass in the session file alongside `stopped_at`.
   - Use only that pass's rungs. For any problem that needs working, ask the learner to work on paper and type only the final answer or the line they are unsure of; if they paste a photo, read it and point to the first broken line.
   - Read the node's note and its proof and example notes first. For a card (library mode), read its source file at `source_anchor` (`VL convert` it if it is not text) and teach from that; never edit the source.
   - Teach concrete before symbolic, make them generate, use the hint ladder, point at the first broken line, enforce the restatement, and ask one hypothesis question per theorem.
   - Run the lock-in quiz: 3 questions, confidence first, then the pass rule.
   - On a pass, run `VL record "<node>" --result pass` and advance.
   - On a fail, run `VL record "<node>" --result fail`, then stay, re-teach smaller, or insert the missing prerequisite first. Never advance after a fail.
   - Append each node's log to the session file as you go, so an abrupt end loses nothing. After every turn, keep the frontmatter `stopped_at` current: the node and the ladder rung reached (for example `stopped_at: "Boole's Inequality, rung 3"`).

8. **Close** on `stop`, or when the plan is done:
   - Append every mistake to `Courses/_learning/Error Log.md` in the method's format.
   - Finish the session file: frontmatter `nodes` and `results`, plus next steps. Set `status: complete` if the plan was finished, or keep `status: open` with `stopped_at` filled in if it was not, so `resume` can pick it up.
   - Append dated observations to the Learner Profile (unless it is `human_authored: true`).
   - Run `VL roadmap <COURSE>` to refresh the mastery colours, and report any validation failure.
   - Append `teach | <COURSE> <topic>` to `_meta/log.md`, with nodes passed and failed, and errors logged.
   - Summarise in chat: what passed, what failed, what is due next (`VL due mixed`), and the suggested next target (`VL next <COURSE>`). When a node failed, name its unit's primer (from `VL unit`) as the place to see how it fits.
