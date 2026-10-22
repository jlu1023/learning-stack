---
name: setup
description: First-time set-up for the learn plugin - checks Python, then either makes a new study vault in the current folder (with an optional example course) or connects an existing folder of notes. Use when someone has just installed the plugin or asks how to start.
disable-model-invocation: true
---

Set the learner up in the current folder. Keep it short: a few questions, then do it.

1. **Check Python.** Run `VL doctor` (`VL` is the engine command in the `method` skill: `python3` on macOS and Linux, `py -3` on Windows, with the others as fallbacks). If none of them runs, or the version is below 3.10, stop and say: "The plugin needs Python 3.10 or later, which is free: install it from https://www.python.org/downloads/ (on Windows, tick 'Add python.exe to PATH'), then run /learn:setup again." Nothing else needs installing.

2. **Ask two questions** through `AskUserQuestion`:
   - **Notes:** "Start a new study vault here" (the folder is empty, or new to studying) or "Use the notes already in this folder" (connect them, read-only) or "Use notes in another folder".
   - **Editor:** "Obsidian" (recommended: links, tables and diagrams render as you read) or "Another editor (VS Code, Typora, a text editor)".

3. **A new vault:**
   - Ask whether to include the small example course (COURSE101, Introductory Probability), which shows every feature and can be deleted later. Default yes.
   - Run `VL init . --frontend <obsidian|plain>` (add `--no-example` if they said no). It never overwrites a file already in the folder; mention any it kept.
   - Then tell them, in at most six lines:
     - Obsidian: open this folder with **Open folder as vault**, allow community plugins, and install **Dataview** (for the review tables). Other editors need nothing.
     - To try it: `/learn:primer COURSE101 1`, then `/learn:teach COURSE101`.
     - To add a course: put its slides or notes (PDFs are fine) in `Sources/courses/<CODE>/` and run `/learn:ingest` on a file.
   - Offer to stop the permission prompt the engine triggers: with their agreement, create `.claude/settings.json` in the vault (or add to it) with
     `{"permissions": {"allow": ["Bash(python3 *vl.py*)", "Bash(python *vl.py*)", "Bash(py *vl.py*)", "PowerShell(python3 *vl.py*)", "PowerShell(python *vl.py*)", "PowerShell(py *vl.py*)"]}}`
     (the patterns end in `*vl.py*` so they match Windows paths with backslashes too).

4. **Existing notes** (this folder or another): read `${CLAUDE_PLUGIN_ROOT}/skills/connect/SKILL.md` and carry out its steps for that folder (the `connect` skill only starts when the learner types it, so follow the file rather than invoking it). For a read-only, shared or synced folder, ask whether to keep the state elsewhere with `--state-dir`. Use their editor answer as the frontend, so connect does not ask again. Never write anything into their notes folder except the `_learn/` state folder.

5. **Optional extras.** Only if `VL doctor` shows them missing and only in one line each, mention what they add: mermaid-cli (diagram checks, roadmap images for editors without Mermaid) and PyYAML (rare YAML forms). Say plainly that neither is needed.
