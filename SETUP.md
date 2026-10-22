# Setup

About 15 minutes. You need [Claude Code](https://code.claude.com) and Python 3.10 or later. [Obsidian](https://obsidian.md) is recommended but not required: see [Using it without Obsidian](#using-it-without-obsidian). To use a folder of notes you already have, skip to [Using your own notes](#using-your-own-notes). Windows, macOS and Linux all work.

## 1. Make your vault

Copy `vault-template/` to wherever you want your vault, and give it a name. For example:

```bash
git clone https://github.com/<owner>/learning-stack.git
cp -r learning-stack/vault-template ~/Study      # Windows: xcopy /E /I learning-stack\vault-template %USERPROFILE%\Study
```

Keep the vault outside the cloned repository, so updating the plugin never touches your notes.

## 2. Open it in Obsidian

1. Obsidian: **Open folder as vault** and choose the folder.
2. When asked, **trust the author and enable community plugins**.
3. Settings, then **Community plugins**, then **Browse**, and install:

   | Plugin | Why |
   |---|---|
   | **Dataview** | The live tables in `Courses/_learning/Review Queue.md` |
   | **LaTeX Suite** | Faster LaTeX typing (optional) |
   | **Update Time on Edit** | Keeps `updated:` current when you edit by hand (optional; set it to the `updated` key and `YYYY-MM-DD`) |
   | **Linter** | Optional. The vault ships no Linter settings: the defaults have every rule off, and the note format is enforced by `CLAUDE.md` and `check-primer` instead. If you turn rules on, leave YAML key sorting and timestamp rules off, since they would rewrite the frontmatter the engine reads |

4. Core plugins: **Templates** is already pointed at `Templates/`.

## 3. Install the engine's Python packages

The plugin's engine needs two packages, in the Python that `python` runs in your terminal:

```bash
python -m pip install PyYAML networkx
```

If you use a virtual environment, activate it before starting Claude Code, so `python` is that environment's.

**To read PDFs, slides and Word files** (for `/learn:ingest` and `/learn:connect`), add the optional converters. All are free:

```bash
python -m pip install -r <path-to-repo>/plugin/engine/requirements-ingest.txt    # pypdfium2, Pillow, python-pptx
```

| For | Install separately | Without it |
|---|---|---|
| Word (.docx) and saved web pages | [pandoc](https://pandoc.org/installing.html): `winget install --id JohnMacFarlane.Pandoc`, `brew install pandoc` or `sudo apt install pandoc` | Those files are refused with this install line |
| Slide images (.pptx) | LibreOffice: `winget install TheDocumentFoundation.LibreOffice`, `brew install --cask libreoffice` or `sudo apt install libreoffice-impress` | Slide text and speaker notes only |
| PDFs without pypdfium2 | poppler (`pdftotext`, `pdftoppm`): `brew install poppler` or `sudo apt install poppler-utils` | PDFs are refused with the install line |

Photos of handwritten notes and Markdown need nothing: Claude reads them directly.

## 4. Install the plugin in Claude Code

Open a terminal in your vault folder and start Claude Code:

```bash
cd ~/Study
claude
```

Then add this repository as a plugin marketplace and install the plugin:

```
/plugin marketplace add <owner>/learning-stack
/plugin install learn@learning-stack
```

Restart Claude Code if it asks. The skills appear as `/learn:teach`, `/learn:quiz`, `/learn:primer`, `/learn:roadmap`, `/learn:ingest`, `/learn:connect`, `/learn:lecture`, `/learn:query` and `/learn:lint`.

To avoid a permission prompt every time a skill runs the engine, allow it once when asked ("Yes, and don't ask again"), or add this to the vault's `.claude/settings.json`:

```json
{ "permissions": { "allow": ["Bash(python *engine/vl.py*)"] } }
```

## 5. Try the example course

The vault ships with a small synthetic course, `COURSE101` (Introductory Probability), so you can see every piece working before adding your own:

```
/learn:roadmap COURSE101
/learn:primer COURSE101 1
/learn:teach COURSE101
```

`/learn:roadmap` draws `Courses/COURSE101/COURSE101 Roadmap.md`. `/learn:teach` runs the probe, plan, teach and lock-in loop on its three notes and records your results; a day later `/learn:quiz` has something to review.

## 6. Add your first course

1. Make yourself known: fill in `Courses/_learning/Learner Profile.md` and edit `Courses/_learning/Teaching Style.md` (or keep its defaults).
2. Create `Courses/<CODE>/<CODE> Syllabus.md` from the **Course Syllabus** template.
3. Put the course's slides or notes in `Sources/courses/<CODE>/` (this folder is never committed).
4. Run `/learn:ingest Sources/courses/<CODE>/<file>`. It plans the notes, asks you to confirm, writes them with their `depends_on` links, and regenerates the roadmap.
5. Optionally fill in `Courses/_learning/Timetable.md` (for the week-ahead overview) and a `<CODE> Exam Profile` from its template.
6. If you have earlier courses whose notes later courses build on, list them under `reference_courses` in `vault-learning.yaml`.

When you are ready, delete `Courses/COURSE101/` and `Courses/PRE100/`.

## Using it without Obsidian

Everything works in a plain folder with any editor (VS Code, Typora, Zed, a text editor) or on GitHub.

1. Copy `vault-template/` as in step 1 and skip step 2. Delete its `.obsidian/` folder if you like.
2. In `vault-learning.yaml`, set `frontend: plain`.
3. Run `/learn:roadmap all` once.

What changes in plain mode:

| | Obsidian | Plain |
|---|---|---|
| Links the skills write | `[[Note]]` | `[Note](../1%20Module/Note.md)`: ordinary relative Markdown links that any editor and GitHub follow |
| Roadmap diagrams | Rendered by Obsidian | Exported as SVG images beside each note and embedded as images, with the Mermaid source kept below. Needs mermaid-cli (below); without it the skill writes `.mmd` files you can paste into mermaid.live, and says so |
| Review Queue | Live Dataview tables | Static tables (due, redos, stuck, recent errors, counts) that `/learn:roadmap all` regenerates after every session |
| Generated-block markers | `%% roadmap:start %%` | `<!-- roadmap:start -->`, hidden in any Markdown viewer |

The engine reads both link styles everywhere, so you can switch a vault between modes; rerun `/learn:roadmap all` after switching. The note templates in `Templates/` use Obsidian's `{{title}}` placeholders: in another editor, copy one and fill it in by hand, or let `/learn:ingest` write notes for you.

## Using your own notes

If you already keep notes in a folder, in any structure (Markdown, PDFs, Word, slides, photos of handwritten pages, with or without Obsidian), connect it instead of copying anything:

```bash
cd "~/My Notes"
claude
```

```
/learn:connect
```

- **Your files are never changed.** The plugin writes only to `_learn/` inside the folder: its settings, review cards, learner state and logs. The engine refuses to write anywhere else. Delete `_learn/` and the folder is exactly as it was.
- **Cards.** For each file you choose, `/learn:connect` writes one card per idea worth recalling (a prompt, a short answer in its own words, and a link back to the page or heading in your file). Cards follow the same 1, 3, 7, 21, 60-day ladder, so `/learn:quiz`, `/learn:teach` and `/learn:roadmap` work on them. `/learn:teach` teaches from your own file, not from the card.
- **Problem sheets and past papers.** Files that look like exercise sets, problem sheets or past papers are flagged in the scan. Their cards only cite a question ("attempt question 3 first") and never hold a solution; the scan reports any card that does.
- **Adding or changing notes.** Run `/learn:connect` again: it finds new files, files you changed since their cards were written (and updates those cards), and cards whose file was removed.

**A read-only, shared or synced folder.** Keep the state somewhere else with `--state-dir`:

```
/learn:connect --state-dir "~/Study State/My Notes"
```

Then open Claude Code in the state folder for later sessions (its `vault-learning.yaml` points back at your notes), or set the environment variable `LEARN_STATE_DIR` to it. If the notes folder may hold one small file, a `vault-learning.yaml` there with `state_dir: <path>` lets you keep opening Claude Code in the notes folder itself.

## Optional: diagram checks and roadmap images

With [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) installed, `/learn:roadmap` and `check-primer` render every diagram before writing, and refuse to write one that would not display; in plain mode it also draws the roadmap images. Without it they still work and report the diagrams as unchecked.

```bash
npm install -g @mermaid-js/mermaid-cli
```

It uses an installed Chrome or Edge where it finds one (set `CHROME_PATH` to point at another).

## Optional: Granola lecture transcripts

See [optional/granola/README.md](optional/granola/README.md), and read its PRIVACY.md first.

## Running the engine by hand

The skills call the engine for you, but it is an ordinary command-line tool. From the vault folder:

```bash
python <path-to-plugin>/engine/vl.py due mixed
python <path-to-plugin>/engine/vl.py --date 2026-02-01 record "Probability Measure" --result pass
```

Every command prints JSON; `python <path-to-plugin>/engine/vl.py --help` lists them. To run its tests, from `plugin/engine/` in a clone of this repository: `python -m pip install -r requirements.txt -r requirements-dev.txt`, then `python -m pytest`.
