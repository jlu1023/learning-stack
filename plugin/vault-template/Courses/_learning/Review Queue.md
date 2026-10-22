---
title: "Review Queue"
type: reference
created: 2026-01-01
updated: 2026-01-01
---

# Review Queue

Live views of learner state (needs the Dataview plugin). A course note with no `mastery` field is unseen. Learner state for `human_authored: true` notes lives in `progress.md`, which these queries do not read. The same due list, with Error Log redos, comes from the engine's `due mixed`.

## Due for review

```dataview
TABLE WITHOUT ID
  file.link AS "Node",
  mastery AS "Mastery",
  review AS "Due",
  last_quizzed AS "Last quizzed",
  review_interval AS "Interval (days)"
FROM "Courses"
WHERE mastery AND review AND review <= date(today)
SORT course ASC, review ASC
```

## Stuck in learning for over 14 days

```dataview
TABLE WITHOUT ID
  file.link AS "Node",
  course AS "Course",
  mastery_since AS "Learning since",
  last_quizzed AS "Last quizzed"
FROM "Courses"
WHERE mastery = "learning" AND mastery_since AND mastery_since <= date(today) - dur(14 days)
SORT mastery_since ASC
```

## Last 10 Error Log entries

```dataview
TABLE WITHOUT ID
  L.date AS "Date",
  L.course AS "Course",
  L.node AS "Node",
  L.category AS "Category",
  L.redo AS "Redo",
  L.redone AS "Redone"
FROM "Courses/_learning"
WHERE file.name = "Error Log"
FLATTEN file.lists AS L
WHERE L.date
SORT L.date DESC
LIMIT 10
```

## Nodes by mastery state

Counts teachable notes (definitions, theorems, lemmas, methods, concepts, intuition notes and axioms); proofs, examples and MOCs are not nodes.

```dataview
TABLE WITHOUT ID
  key AS "Course and state",
  length(rows) AS "Nodes"
FROM "Courses" AND -"Courses/_learning"
WHERE course AND type AND type != "moc" AND type != "proof" AND type != "example" AND type != "question"
GROUP BY course + ": " + default(mastery, "unseen")
SORT key ASC
```
