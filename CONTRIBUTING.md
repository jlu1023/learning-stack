# Contributing

Issues and pull requests are welcome. A few house rules keep the plugin easy to install and safe to share.

## The engine

- **Standard library only.** The engine in `plugin/engine/` must run on a plain Python 3.10 or later with no packages. Optional tools (PyYAML, mermaid-cli) may be used when present, never required.
- **Tests.** From `plugin/engine/`: `python -m pip install -r requirements-dev.txt`, then `python -m pytest`. Add a test with every fix. The parity tests compare the built-in graph and YAML code with networkx and PyYAML; keep them passing.
- **Never write outside the vault or state folder.** `Vault.write_text` refuses it; do not work around it. A connected library is read-only.
- **Errors are JSON.** An expected failure raises `EngineError` (or one of the errors `main` catches) so the skills get `{"error": ...}` on stdout, never a traceback.

## The skills and docs

- Skills live in `plugin/skills/<name>/SKILL.md`; the teaching rules are in `method`. If a rule changes, change it there and keep the other skills pointing at it.
- British English, day-month-year dates in prose, ISO dates in frontmatter. No em dashes anywhere (use a colon, comma or full stop).
- No personal data, course codes, institution names or copyrighted course material in examples or tests. Example content is synthetic.
- Integrity rules (INTEGRITY.md) are not optional: hints before answers, exercises cited not solved, past papers for format only.
