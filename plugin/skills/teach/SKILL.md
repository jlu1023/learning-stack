---
name: teach
description: Socratic teaching session on one course - primer for a new lecture, probe, plan, teach one node at a time, and lock in each with quick recall; unit tests, and the proof track for writing proofs. Use when the learner asks to be taught a course, module or note from their vault, or to practise proofs.
argument-hint: <course> [module | note name | next | deepen | resume | test [unit] | proofs [unit] | <module> final], or proofs alone
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
   - `test [N]` or `<module> final`: run the unit test (unit N, or the latest unit whose nodes are all at least `learning`) or the module final per the method (Unit tests and finals), after the warm-up, then close (step 8). Skip steps 4 to 7. After a unit test, offer that unit's proofs (the method's Proof track).
   - `proofs [N]` (with or without a course): the proof track per the method (Proof track) and Teaching Style. After the warm-up, run `VL proofs <COURSE|mixed>`: due proofs first, then new ones from tested units (from unit N only, if given), at most 3, each started at its `proof_stage`. After each attempt run `VL record "<proof>" --result pass|fail --stage N` and append a line to `Courses/_learning/Proof Log.md`. Then close (step 8). Skip steps 4 to 7.
   - Before planning `next` or a module, check the course's units (`VL unit <COURSE> all`, then `VL unit <COURSE> <N>` for started ones): if a unit is ready for its test and has none yet, offer it first (method).

3. **Week ahead, then warm-up.** If this is the first `teach` or `quiz` run of a new week, give the week-ahead overview first (method, Week ahead). Then the warm-up: run `VL due mixed --limit 6` and ask 2 or 3 retrieval questions from the due items and redos (only 2 while the learner has unstarted units whose lectures have happened: method, Learn first when behind), mixed across courses, with **no course or topic labels shown**. Dress each in a cue class other than the item's last cue (method, Varying the cue) and pitch it at its `held_as` line. Confidence comes with each answer, then the verdict, then `VL record "<node>" --result pass|fail` for each. If nothing is due, say so in one line and skip.

4. **Primer for a new unit.** Take the first node the target resolves to and its `unit` from `VL graph <COURSE>`, then run `VL unit <COURSE> <unit>`. If `started` is false, give the unit's primer per the method (Primers): show the saved primer, or write it first if there is none and run `VL check-primer <COURSE>` until it passes; give the short chat version; run its prerequisite check. Skip this step for `resume`, `deepen` and pass 2 candidates, and when `started` is true. When later in the session a planned node opens another unstarted unit, give that unit's primer before teaching the node.

5. **Probe.** Bracket every strand the target depends on per the method (Probing), through `AskUserQuestion`, one question at a time (after a primer, start from where its prerequisite check left off):
   - Strands are the target's `prereqs` chains (and `external_prereqs` for earlier courses). Nodes at `secure` or above count as known and are not probed; run `VL show` on each strand's top node for its `held_as` lines.
   - Enter near the top of each strand, jump up on a confident reasoned pass, step gently on a hesitant one, narrow in on a miss, until each strand has a floor and a ceiling.
   - "I don't know" on every question; a right answer with no reason, or at confidence 1 or 2, is **edge**, not known: ask "why" before crediting it.
   - Record the answers per the method (Probes record); the session file created in step 6 gets one `Edge:` line per strand. Then plan from the ceilings.

6. **Plan.** Build the session's prerequisite graph for the gaps: **at most 3 nodes per session**, prerequisites first, so a session fits one sitting of 30 to 45 minutes. If the gap needs more, plan the first 3 and list the rest as next steps for `resume`.
   - Create the session file `Courses/_learning/sessions/YYYY-MM-DD <COURSE> <topic>.md` (format in the method) holding the plan as a small Mermaid diagram, with frontmatter `status: open` and `stopped_at` set to the first node, rung 0. Use plain labels and no `internal-link` class, so the session file adds nothing to the graph.
   - Show the ordered list in chat as plain text.

7. **Teach and lock in,** one node at a time, per the method and the passes and ladder in Teaching Style:
   - **Choose the pass from the node's learner state:** `unseen` is pass 1; `learning` is pass 2; `secure` or `mastered` is pass 3. If the learner says `pass 1` or `deepen`, use that instead. If a recall question in pass 2 or 3 fails, record the fail and switch that node to pass 1 for the rest of the session. Record the pass in the session file alongside `stopped_at`.
   - Use only that pass's rungs. For any problem that needs working, ask the learner to work on paper and type only the final answer or the line they are unsure of; if they paste a photo, read it and point to the first broken line.
   - Read the node's note and its proof and example notes first (a proof's key idea is taught; writing the proof is for the proof track). For a card (library mode), read its source file at `source_anchor` (read as in the method's Reading sources) and teach from that; never edit the source.
   - Teach each step as predict, teach, check (method, Teaching): from firm ground, by motivated steps, concrete before symbolic, with the result said once as a chain. Use the hint ladder, point at the first broken line, enforce the restatement, and ask one hypothesis question per theorem. A new kind of multi-step problem starts scaffolded, then fades. Draw a visual into the session file only if the learner asks.
   - If the note is thin or a question goes beyond it, use the textbook look-up (method, Grounding): the cited pages only, plus a page either side.
   - Run the lock-in: 3 quick recall questions (no proofs, no worked problems), each with its cue class noted in the session file, confidence with each answer, then the pass rule (method, Lock-in).
   - On a pass, run `VL record "<node>" --result pass` and advance.
   - On a fail, stay: re-teach a smaller step, or insert the missing prerequisite first, then retry once. If the retry also fails, run `VL record "<node>" --result fail` and move on to the next node: it comes back tomorrow, and only a second fail in a row drops its level.
   - Append each node's log to the session file as you go, so an abrupt end loses nothing. After every turn, keep the frontmatter `stopped_at` current: the node and the ladder rung reached (for example `stopped_at: "Boole's Inequality, rung 3"`).

8. **Close** on `stop`, or when the plan is done:
   - Append every logged mistake to `Courses/_learning/Error Log.md`, and every proof attempt to `Courses/_learning/Proof Log.md`, in the method's formats.
   - Append a Learner Model line for each node whose answers showed how the learner holds it (method, Logging). Silent: do not mention it in chat.
   - Finish the session file: frontmatter `nodes` and `results`, plus next steps. Set `status: complete` if the plan was finished, or keep `status: open` with `stopped_at` filled in if it was not, so `resume` can pick it up.
   - Append dated observations to the Learner Profile (unless it is `human_authored: true`).
   - Run `VL roadmap <COURSE>` to refresh the mastery colours, and report any validation failure.
   - Append `teach | <COURSE> <topic>` to `_meta/log.md`, with nodes passed and failed, and errors logged.
   - Summarise in chat: the progress line for each unit touched with `Proofs due: n` (method, Logging), what passed, what failed, what is due next (`VL due mixed`), and the suggested next target (`VL next <COURSE>`). When a node failed, name its unit's primer (from `VL unit`) as the place to see how it fits.
