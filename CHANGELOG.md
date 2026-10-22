# Changelog

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
