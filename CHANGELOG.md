# Changelog

## 1.3.0

- Unit tests: once every node in a unit is learned, `/learn:teach` offers a short test (one question per node, an integrative problem, a teach-back); `test [N]` runs one on demand and `<module> final` tests a whole module.
- A teach-back question guards the step to `mastered`.
- Slips are pointed out once and never logged or re-taught; only conceptual errors get Error Log redos.
- One push-back per node on a right answer, on substance only; reasoning the learner did not give is never credited.
- Misses are sorted (slip, blank, wrong tool, misconception) after asking for the learner's thinking; only wrong tools and misconceptions are logged, and they are retested with fresh wording before the session closes.
- The probe starts from recorded state and from the top of what the target needs; a right answer at low confidence counts as edge.
- `/learn:quiz` picks the question type from the node's level and adjusts difficulty as it goes; generated problems are solved and checked for shortcuts before they are posed.
- Several of these ideas were adapted, in new wording, from Eero Alvar's LearnHarness prompts.
- A plain progress line per unit at the close (`5/13 learning, 2/13 secure`), and `harder` / `easier` shortcuts.

## 1.2.2

- Ready for the plugin directory: `/learn:setup` no longer offers to write Claude Code's permission settings (it explains how to allow the engine instead), and the plugin README says exactly what the plugin runs, writes, reads and sends.

## 1.2.1

- Every expected failure (an unknown course, an ambiguous note name, a bad `--date`, a broken `vault-learning.yaml`, a refused write) is a JSON error with exit code 2, never a traceback.
- A malformed redo date in the Error Log is reported instead of stopping `due`; a missing `progress.md` is created when first needed; `doctor` copes with a broken settings file.
- `/learn:setup` now carries out the connect steps itself (the `connect` skill only starts when typed), and `/learn:ingest` points library users to `/learn:connect`.
- `--version`, a plugin icon, tests on Windows, macOS and Linux with Python 3.10 and 3.13.

## 1.2

- Nothing to install but Python 3.10 or later: the engine uses the standard library only (a built-in graph module, and a built-in frontmatter reader when PyYAML is absent).
- Converters removed: Claude Code reads PDFs and images itself; Word and PowerPoint are saved as PDF.
- `/learn:setup` makes a vault from the template that now ships inside the plugin, or connects existing notes; new engine commands `init` and `doctor`.
- Plain mode keeps Mermaid blocks and exports SVG images only when mermaid-cli is installed.
- An impossible date in a note's frontmatter no longer stops the roadmap.
- Permission rules that match on Windows (backslash paths, PowerShell).

## 1.1

- Use it without Obsidian (`frontend: plain`): Markdown links, HTML-comment markers, static review tables.
- Bring your own notes: `/learn:connect` builds review cards over a read-only folder of notes, with problem sheets and past papers cited, never solved.
- Gentler demotion: one fail keeps the level; a second fail in a row drops it. Lenient marking for slips; learn first when behind.

## 1.0

- First release: the `learn` plugin for Claude Code (teach, quiz, primer, roadmap, ingest, lecture, query, lint) with an Obsidian vault template and an optional Granola lecture-transcript module.
