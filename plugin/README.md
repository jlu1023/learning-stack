# learn: a Socratic tutor for Obsidian course notes

A Claude Code plugin that teaches you from your own Obsidian vault. `/learn:teach` probes what you know, plans at most three notes, teaches one idea at a time and locks each in with a quiz; `/learn:quiz` runs spaced, interleaved reviews of what is due; `/learn:primer` gives a five-minute overview of a lecture; `/learn:roadmap` draws dependency maps from your notes' `depends_on` links; `/learn:ingest`, `/learn:lecture`, `/learn:query` and `/learn:lint` build and check the vault.

It expects a vault laid out like `vault-template/` in the repository, and Python with PyYAML and networkx for the engine in `engine/`. Setup, the learning method and the integrity rules are in the repository's SETUP.md, LEARNING-METHOD.md and INTEGRITY.md. MIT licence.

Install:

```
/plugin marketplace add <owner>/obsidian-learning-loop
/plugin install learn@obsidian-learning-loop
```
