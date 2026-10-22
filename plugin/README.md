# learn: a Socratic tutor for your notes

A Claude Code plugin that teaches you from your own notes, in an Obsidian vault or in any folder of PDFs, Markdown or photos of handwritten pages. `/learn:setup` makes a vault or connects your notes; `/learn:teach` probes what you know, plans at most three ideas, teaches one at a time and locks each in with a quiz; `/learn:quiz` runs spaced, interleaved reviews of what is due; `/learn:primer` gives a five-minute overview of a lecture; `/learn:roadmap` draws dependency maps; `/learn:ingest` turns documents into notes; `/learn:connect` builds review cards over a folder of notes without changing it; `/learn:lecture`, `/learn:query` and `/learn:lint` complete the set.

It needs only Python 3.10 or later: the engine in `engine/` uses the standard library alone, and Claude Code reads PDFs and images itself. `/learn:setup` copies `vault-template/` for a new vault. Setup, the learning method and the integrity rules are in the repository's SETUP.md, LEARNING-METHOD.md and INTEGRITY.md. MIT licence.

Install:

```
/plugin marketplace add jlu1023/learning-stack
/plugin install learn@learning-stack
/learn:setup
```

## What it runs, writes, reads and sends

- **Runs:** one bundled program, the engine at `engine/vl.py` (readable Python source, standard library only), through Claude Code's shell: `python3`, `python` or `py -3` followed by that path and a command such as `due` or `record`. Claude Code asks your permission before each run unless you allow it. If you have installed mermaid-cli yourself, the engine also runs `mmdc` locally to check diagrams, which opens an installed Chrome or Edge in headless mode. There are no hooks, no MCP servers and no background processes.
- **Writes:** only inside the folder you are studying in, or, for a connected notes folder, inside its state folder (`_learn/`, or the one you name with `--state-dir`). That covers the notes and review cards the skills write when you ask them to, learner-state fields in those notes' frontmatter (`mastery`, `review` and similar), generated roadmaps, the Vault Index, the Review Queue, session files and logs. `/learn:setup` copies the vault template into an empty or existing folder and never overwrites a file. In a connected notes folder the engine refuses any write outside the state folder, so your own files are never changed.
- **Never:** changes Claude Code's settings or permissions, installs packages, or deletes your files.
- **Reads:** your notes and the files you point a skill at. As with any file Claude Code reads, their content goes to Claude as part of your conversation.
- **Fetches:** a web page only when you give `/learn:ingest` a URL, using Claude Code's own fetch tool.
- **Sends:** nothing to any other service. The engine makes no network connections and collects no telemetry.
