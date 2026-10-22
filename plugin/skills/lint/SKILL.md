---
name: lint
description: Vault health check for a learning vault - orphans, duplicates, broken links, theorems without proofs, frontmatter drift, primer problems and review backlog. Report only, no fixes.
---

Walk the vault and produce a structured report. Change nothing.

1. **Orphans:** notes with no inbound and no outbound links.
2. **Duplicates:** near-duplicate note titles (case-insensitive, plurals, common variants).
3. **Broken wikilinks:** `[[X]]` where `X` does not exist.
4. **Contradictions:** notes that make contradictory claims about the same concept. Quote the excerpts.
5. **Theorems without proofs:** `type: theorem` notes with no linked `type: proof` note (unless `proof_pending: true` explains why).
6. **Proofs without theorems:** `type: proof` notes whose theorem link is broken.
7. **Definitions never used:** `type: definition` notes with no inbound `depends_on` or wikilink.
8. **Stale content:** notes with `updated:` more than 180 days ago and `status: seedling` or the `#stub` tag.
9. **Stale MOCs:** MOCs where at least 30% of linked notes no longer exist.
10. **Topic tags:** any hashtag in use that is not in the tag registry in `CLAUDE.md`.
11. **Frontmatter drift:** notes missing the required fields for their type (see `CLAUDE.md`), for example a theorem with no `depends_on`.
12. **Primers:** run `VL check-primer all` (`VL` is the engine command in the `method` skill) and list every failing primer and every unit without one.
13. **Review backlog:** from `VL due mixed`, the number of overdue notes and due redos.

Output, severity-ordered:

```
# Lint Report - <day month year>

## Severe (breaks navigation or correctness)
- Broken wikilinks: ...
- Contradictions: ...

## Important
- Theorems without proofs: ...
- Failing primers: ...
- Tags not in the registry: ...

## Cleanup
- Orphans: ...
- Stale stubs: ...
```

Name notes in plain text, not wikilinks. End by asking whether to stub the missing notes or fix any items now.
