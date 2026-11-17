---
name: app
description: Study Desk, the plugin's optional local app - a browser page with a tab per course, typeset maths, a progress table and the tutor running as Claude Code in the study folder. Starts it, stops it, or (on Windows) makes a desktop shortcut. Use when the learner asks for the app, a window, a dashboard or rendered maths.
argument-hint: "[stop | shortcut] [--port N] [--permission-mode MODE]"
disable-model-invocation: true
---

Open Study Desk for the current folder: `$ARGUMENTS`.

Study Desk is a local web page for this plugin, served from the learner's own machine. It adds no teaching rules: each tab's tutor is Claude Code itself, started in this folder, following the same skills and the same engine. `APP` below means, from the study folder:

```
python3 "${CLAUDE_PLUGIN_ROOT}/app/serve.py" <options>
```

On Windows use `py -3`; if a form fails, try `python3`, `python`, `py -3` and keep the one that works (the same rule as the engine command in the `method` skill). It needs Python 3.10 or later and nothing else.

1. **Check the folder.** Run the engine's `where` (the `method` skill's `VL where`). If `courses` is empty, say that the app will open with only a General tab until `/learn:setup` (or `/learn:ingest`) has made a course here, and ask whether to carry on.

2. **Say what will happen, once, before the first start:**
   - It opens a page at `http://127.0.0.1:8030` that only this computer can reach.
   - **The tutor in the app runs Claude Code in this folder in permission mode `auto`: it reads and edits files and runs commands here without stopping to ask**, because the page cannot show permission prompts. To use a stricter mode, start it with `--permission-mode acceptEdits` (or `manual`, `dontAsk`, `plan`); then anything Claude Code would ask about is refused, so the engine command must be allowed first (SETUP.md, Permission prompts).
   - Style settings, photos of working and a log are kept in the per-user data folder, never in the notes.

3. **Start it.** Run `APP --background` plus any options from `$ARGUMENTS` (`--port N`, `--permission-mode MODE`, `--model NAME`). It starts the server detached, opens the default browser and returns; if Study Desk is already running it only opens the browser. If it reports that it is running for a different folder, ask before stopping that one (`APP --stop`) and starting again here. If the detached start fails in this environment, run `APP` without `--background` as a background command instead, and read its first line.

4. **Tell the learner,** in at most five lines: the address, that each course has its own tab and conversation, that the plugin's commands work there as typed (`/learn:teach <course> next`, `/learn:quiz mixed`), that the About panel in the app explains the rest, and that `/learn:app stop` stops it.

5. **`stop`:** run `APP --stop` and report its answer.

6. **`shortcut` (Windows only),** or once after the first successful start on Windows: ask, through `AskUserQuestion`, whether they would like a "Study Desk" shortcut on the desktop that opens the app in its own window for this folder. Only on a yes, run:

   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/app/windows/make_shortcut.ps1" -Folder "<this folder>"
   ```

   Say where the shortcut is, and that it must be made again if the plugin is updated (its folder can move). On macOS and Linux there is no shortcut script: suggest a bookmark for the address, with `APP --background --no-browser` to start the server.

Never change Claude Code's settings or permission files, and never start the app with a permission mode the learner did not ask for. If the page says `claude` is not on PATH, the fix is to install Claude Code or set `STUDY_DESK_CLAUDE` to its full path, then start the app again.
