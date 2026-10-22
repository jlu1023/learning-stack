---
title: "progress"
type: reference
created: 2026-01-01
updated: 2026-01-01
---

# Progress store for human-authored notes

Learner state for course notes marked `human_authored: true`, whose frontmatter is never touched. Written only by the engine's `record`, one row per note, with the same fields and rules as the frontmatter learner state. Do not edit rows by hand. The Path column is the vault-relative path.

| Note | Path | mastery | mastery_since | last_quizzed | review | review_interval | fail_streak |
|---|---|---|---|---|---|---|---|
