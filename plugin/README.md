# learn: a Socratic tutor for your notes

A Claude Code plugin that teaches you from your own notes, in an Obsidian vault or in any folder of PDFs, slides, Word files, Markdown or photos of handwritten pages. `/learn:teach` probes what you know, plans at most three ideas, teaches one at a time and locks each in with a quiz; `/learn:quiz` runs spaced, interleaved reviews of what is due; `/learn:primer` gives a five-minute overview of a lecture; `/learn:roadmap` draws dependency maps; `/learn:ingest` turns documents into notes; `/learn:connect` builds review cards over a folder of notes without changing it; `/learn:lecture`, `/learn:query` and `/learn:lint` complete the set.

It needs Python with PyYAML and networkx for the engine in `engine/` (plus the optional converters in `engine/requirements-ingest.txt` for PDFs and slides). Setup, the learning method and the integrity rules are in the repository's SETUP.md, LEARNING-METHOD.md and INTEGRITY.md. MIT licence.

Install:

```
/plugin marketplace add jlu1023/learning-stack
/plugin install learn@learning-stack
```
