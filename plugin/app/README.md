# Study Desk

An optional local app for the learn plugin: a page in your browser with one tab per course, maths typeset with KaTeX, a progress table built from the engine, and the tutor running as headless Claude Code in your study folder. Start it with `/learn:app`, or from the study folder:

```
python3 <plugin>/app/serve.py            (Windows: py -3 <plugin>\app\serve.py)
```

## What it is (and is not)

- A shell. The teaching rules stay in the plugin's skills and the scheduling stays in the engine (`engine/vl.py`), which the app only asks for JSON. It reimplements neither.
- The server never writes into your notes. Learner state changes only when the tutor runs the engine's `record`, exactly as in the terminal.
- Conversations live in memory only. Each tab keeps its own Claude Code session while the server runs; `/clear` or a server restart starts clean.
- Standard library only (Python 3.10 or later). The page's libraries are in `static/vendor`, so nothing is fetched from the network.
- It uses Claude Code as you have it installed and signed in (`claude -p`); the app holds no key and makes no network connections of its own.

## The permission mode

The tutor is started with `--permission-mode auto`: **Claude Code reads and edits files and runs commands in the study folder without stopping to ask you**, because a web page cannot show its permission prompts. To choose a stricter mode:

- a flag: `serve.py --permission-mode acceptEdits` (also `manual`, `dontAsk`, `plan`);
- or the environment variable `STUDY_DESK_PERMISSION_MODE`;
- or `"permission_mode"` in `config.json` in the data folder.

In the stricter modes anything Claude Code would normally ask about is refused, so allow the engine command in the folder's Claude Code settings first (SETUP.md, Permission prompts). `bypassPermissions` is never accepted. `AskUserQuestion` is switched off in the app: questions arrive as text and you type the answer.

## Layout

```
serve.py                 the launcher: start, find a running server, open the browser, --stop
studydesk/server.py      the server: overview (engine JSON, cached), notes, chat stream, settings, uploads
studydesk/winicon.py     Windows only: a sharp taskbar icon for the app window
static/                  index.html, app.js, md.js (Markdown, KaTeX, wikilinks, callouts), app.css, icons
static/vendor/           KaTeX with its fonts, marked, DOMPurify, Mermaid, and their licences
windows/                 launch.vbs (no console window), make_shortcut.ps1, stop.ps1
tests/                   run with the engine's tests (from engine/: python -m pytest)
```

## Options

| Flag | Environment | `config.json` | Default |
|---|---|---|---|
| `--folder PATH` | `STUDY_DESK_FOLDER` | | the current folder |
| `--port N` | `STUDY_DESK_PORT` | `"port"` | 8030 |
| `--permission-mode MODE` | `STUDY_DESK_PERMISSION_MODE` | `"permission_mode"` | `auto` |
| `--model NAME` | | `"model"` | Claude Code's own default |
| `--data PATH` | `STUDY_DESK_DATA` | | the per-user data folder |
| | `STUDY_DESK_CLAUDE` | | `claude` on PATH |

Also `--background` (start detached and return), `--window browser|app|none` (`app` opens Chrome, Edge or Chromium as its own window, with a browser profile of its own in the data folder), `--no-browser` and `--stop`. A second launch on the same port only opens the browser.

The folder is found exactly as the skills find it: the engine runs from it, so a vault, a plain-editor vault and a connected notes folder (`_learn/`, `state_dir:`, `LEARN_STATE_DIR`) all work. Tabs are the engine's courses plus General; tab colours come from a built-in palette and can be changed under Style.

## Your data

Style settings (`settings.json`), photos of working (`uploads/`, kept a week), the last known usage limits (`usage.json`), the optional `config.json` and the server log are kept in:

- Windows: `%LOCALAPPDATA%\StudyDesk`
- macOS: `~/Library/Application Support/StudyDesk`
- Linux: `$XDG_DATA_HOME/study-desk`, or `~/.local/share/study-desk`

Nothing is written into the plugin or the notes folder.

## Only this computer

The server listens on 127.0.0.1 only. Every request must name it as the Host (which blocks DNS rebinding), a present Origin must be its own, and every write needs the `X-Study-Desk` header, so no other web page can drive the tutor. Static files are served only from `static/`.

## Windows extras

- `windows\make_shortcut.ps1 -Folder <study folder>` makes a "Study Desk" desktop shortcut. It runs `windows\launch.vbs`, which starts the server with no console window and opens the app in its own maximised window. Make the shortcut again after a plugin update, since the plugin's folder can move.
- `windows\stop.ps1` stops the server (the same as `serve.py --stop`).
- The app window gets a sharp taskbar icon (`studydesk/winicon.py`).

## Keys

Enter sends, Shift+Enter new line, Ctrl+0 Home, Ctrl+1 to 9 tabs, Alt+Left and Alt+Right note tabs, Alt+W close a note tab, Ctrl+B sidebar, Ctrl+. side panel, F11 fullscreen, Esc stops a reply or closes a panel.

Study Desk is an independent, open-source project. It is not made, endorsed or supported by Anthropic.
