# Setup

About five minutes. You need two things:

- [Claude Code](https://code.claude.com)
- Python 3.10 or later. Most Macs and Linux machines already have it (check with `python3 --version`). On Windows, install it from [python.org](https://www.python.org/downloads/) and tick "Add python.exe to PATH".

That is all: the plugin's engine uses only Python's standard library, and Claude Code reads your PDFs and photos itself. [Obsidian](https://obsidian.md) is recommended but not required.

## 1. Install the plugin

Start Claude Code in the folder you want to study in (an empty folder for a new vault, or your existing notes folder):

```bash
cd ~/Study
claude
```

Then:

```
/plugin marketplace add jlu1023/learning-stack
/plugin install learn@learning-stack
```

Restart Claude Code if it asks.

**Windows: "Filename too long".** Adding the marketplace clones this repository, and Windows limits paths to 260 characters by default. From a normal user folder the longest path stays well under that, but if your Claude config folder is unusually deep, run `git config --global core.longpaths true` and add the marketplace again.

## 2. Run the set-up

```
/learn:setup
```

It checks Python, asks whether to start a new vault or use the notes already in the folder, and whether you use Obsidian, then does the rest:

- **A new vault** is copied in from the template that ships with the plugin (it never overwrites a file that is already there), with an optional example course, `COURSE101`, so you can see every piece working.
- **Your existing notes** are connected read-only: see [Using your own notes](#using-your-own-notes).

The skills are `/learn:setup`, `/learn:teach`, `/learn:quiz`, `/learn:primer`, `/learn:roadmap`, `/learn:ingest`, `/learn:connect`, `/learn:lecture`, `/learn:query` and `/learn:lint`.

## 3. If you use Obsidian

1. **Open folder as vault**, choose the folder, and allow community plugins when asked.
2. Settings, then **Community plugins**, then **Browse**, and install **Dataview** (the live tables in `Courses/_learning/Review Queue.md`). Everything else is optional:

   | Plugin | Why |
   |---|---|
   | **LaTeX Suite** | Faster LaTeX typing |
   | **Update Time on Edit** | Keeps `updated:` current when you edit by hand (set it to the `updated` key and `YYYY-MM-DD`) |
   | **Linter** | The vault ships no Linter settings. If you turn rules on, leave YAML key sorting and timestamp rules off, since they would rewrite the frontmatter the engine reads |

The Templates core plugin is already pointed at `Templates/`.

## 4. Try the example course

```
/learn:roadmap COURSE101
/learn:primer COURSE101 1
/learn:teach COURSE101
```

`/learn:roadmap` draws `Courses/COURSE101/COURSE101 Roadmap.md`. `/learn:teach` runs the probe, plan, teach and lock-in loop on its notes and records your results; a day later `/learn:quiz` has something to review. To see `/learn:ingest` at work, run it on the synthetic handout in this repository, [docs/examples/sample-lecture.pdf](docs/examples/sample-lecture.pdf) (one typed page, one handwritten page).

## 5. Add your first course

1. Fill in `Courses/_learning/Learner Profile.md`, and edit `Courses/_learning/Teaching Style.md` or keep its defaults.
2. Put the course's slides or notes in `Sources/courses/<CODE>/` (this folder is never committed).
3. Run `/learn:ingest Sources/courses/<CODE>/<file>`. It plans the notes, asks you to confirm, writes them with their `depends_on` links, creates the course page if needed, and regenerates the roadmap.
4. Optionally fill in `Courses/_learning/Timetable.md` (for the week-ahead overview) and a `<CODE> Exam Profile` from its template.
5. Earlier courses whose notes later ones build on go under `reference_courses` in `vault-learning.yaml`.

When you are ready, delete `Courses/COURSE101/` and `Courses/PRE100/`.

## Reading your files

Claude Code reads these itself, with nothing to install:

| File | How |
|---|---|
| Markdown, text, saved web pages | Read directly |
| PDF (typed, scanned or maths-heavy) | Read page by page, as text and as an image, so formulas and handwriting are read from the page itself |
| Photos of handwritten notes | Read as images; anything illegible is marked `[?: ...]` and you are asked |
| Web pages | Fetched |
| Word, PowerPoint, Keynote, Pages | Save as PDF from the app that made them (File, Save as or Export, PDF), then use the PDF |

## Using it without Obsidian

Everything works in a plain folder with any editor (VS Code, Typora, Zed, a text editor) or on GitHub. Choose "Another editor" in `/learn:setup`, or set `frontend: plain` in `vault-learning.yaml` and run `/learn:roadmap all`.

| | Obsidian | Plain |
|---|---|---|
| Links the skills write | `[[Note]]` | `[Note](../1%20Module/Note.md)`: ordinary relative Markdown links that any editor and GitHub follow |
| Roadmap diagrams | Drawn by Obsidian | Mermaid blocks, which GitHub, Typora and many editors draw. With mermaid-cli installed (optional, below) each is also saved as an SVG image beside its note |
| Review Queue | Live Dataview tables | Static tables (due, redos, stuck, recent errors, counts) that `/learn:roadmap all` regenerates after every session |
| Generated-block markers | `%% roadmap:start %%` | `<!-- roadmap:start -->`, hidden in any Markdown viewer |

The engine reads both link styles everywhere, so a vault can switch modes; rerun `/learn:roadmap all` after switching. The note templates in `Templates/` use Obsidian's `{{title}}` placeholders: in another editor, let `/learn:ingest` write notes, or copy a template and fill it in.

## Using your own notes

If you already keep notes in a folder, in any structure (Markdown, PDFs, photos of handwritten pages, with or without Obsidian), choose "Use the notes already in this folder" in `/learn:setup`, or run `/learn:connect` there.

- **Your files are never changed.** The plugin writes only to `_learn/` inside the folder: its settings, review cards, learner state and logs. The engine refuses to write anywhere else. Delete `_learn/` and the folder is exactly as it was.
- **Cards.** For each file you choose, `/learn:connect` writes one card per idea worth recalling (a prompt, a short answer in its own words, and a link back to the page or heading in your file). Cards follow the same 1, 3, 7, 21, 60-day ladder, so `/learn:quiz`, `/learn:teach` and `/learn:roadmap` work on them. `/learn:teach` teaches from your own file, not from the card.
- **Word and slides.** The scan lists them under "save as PDF": save a PDF beside each and run `/learn:connect` again.
- **Problem sheets and past papers.** Files that look like exercise sets, problem sheets or past papers are flagged. Their cards only cite a question ("attempt question 3 first") and never hold a solution; the scan reports any card that does.
- **Adding or changing notes.** Run `/learn:connect` again: it finds new files, files you changed since their cards were written (and updates those cards), and cards whose file was removed.

**A read-only, shared or synced folder.** Keep the state somewhere else:

```
/learn:connect --state-dir "~/Study State/My Notes"
```

Then open Claude Code in the state folder for later sessions (its `vault-learning.yaml` points back at your notes), or set the environment variable `LEARN_STATE_DIR` to it. If the notes folder may hold one small file, a `vault-learning.yaml` there with `state_dir: <path>` lets you keep opening Claude Code in the notes folder itself.

## Permission prompts

Claude Code asks before each engine command. Choose "Yes, and don't ask again", let `/learn:setup` add the rule, or put this in the folder's `.claude/settings.json`:

```json
{ "permissions": { "allow": [
  "Bash(python3 *vl.py*)", "Bash(python *vl.py*)", "Bash(py *vl.py*)",
  "PowerShell(python3 *vl.py*)", "PowerShell(python *vl.py*)", "PowerShell(py *vl.py*)"
] } }
```

The patterns end in `*vl.py*` rather than a full path so they also match Windows paths written with backslashes; the PowerShell forms cover Windows sessions that run commands through PowerShell.

## Optional extras

Neither is needed; `/learn:setup` (or the engine's `doctor` command) says which you have.

| Extra | Adds | Install |
|---|---|---|
| [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) | Checks every diagram renders before writing it; in plain mode also saves roadmaps as SVG images | `npm install -g @mermaid-js/mermaid-cli` (needs Node.js; uses an installed Chrome or Edge, or set `CHROME_PATH`) |
| PyYAML | Reads every kind of YAML frontmatter; without it a few rare forms (lists of mappings, anchors) are reported as unreadable | `python3 -m pip install PyYAML` |

For lecture transcripts, see [optional/granola/README.md](optional/granola/README.md), and read its PRIVACY.md first.

## Running the engine by hand

The skills call the engine for you, but it is an ordinary command-line tool. From the vault folder, with the plugin's folder (shown by `/plugin`) in place of `<plugin>`:

```bash
python3 <plugin>/engine/vl.py doctor
python3 <plugin>/engine/vl.py due mixed
python3 <plugin>/engine/vl.py --date 2026-02-01 record "Probability Measure" --result pass
```

Every command prints JSON; `--help` lists them. To run the tests, from `plugin/engine/` in a clone of this repository: `python3 -m pip install -r requirements-dev.txt`, then `python3 -m pytest`.
