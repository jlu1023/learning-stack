# Setup

About 15 minutes. You need [Obsidian](https://obsidian.md), [Claude Code](https://code.claude.com) and Python 3.10 or later. Windows, macOS and Linux all work; the commands below show both shells where they differ.

## 1. Make your vault

Copy `vault-template/` to wherever you want your vault, and give it a name. For example:

```bash
git clone https://github.com/<owner>/obsidian-learning-loop.git
cp -r obsidian-learning-loop/vault-template ~/Study      # Windows: xcopy /E /I obsidian-learning-loop\vault-template %USERPROFILE%\Study
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

## 4. Install the plugin in Claude Code

Open a terminal in your vault folder and start Claude Code:

```bash
cd ~/Study
claude
```

Then add this repository as a plugin marketplace and install the plugin:

```
/plugin marketplace add <owner>/obsidian-learning-loop
/plugin install learn@obsidian-learning-loop
```

Restart Claude Code if it asks. The skills appear as `/learn:teach`, `/learn:quiz`, `/learn:primer`, `/learn:roadmap`, `/learn:ingest`, `/learn:lecture`, `/learn:query` and `/learn:lint`.

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

## Optional: diagram checks

With [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) installed, `/learn:roadmap` and `check-primer` render every diagram before writing, and refuse to write one that would not display. Without it they still work and report the diagrams as unchecked.

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
