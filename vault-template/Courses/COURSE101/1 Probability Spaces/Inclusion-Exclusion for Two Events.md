---
title: "Inclusion-Exclusion for Two Events"
type: theorem
course: COURSE101
module: "Probability Spaces"
section: "1.2"
lecture: 1
created: 2026-01-01
updated: 2026-01-01
status: growing
depends_on: ["[[Probability Measure]]", "[[Set Operations]]"]
used_in: []
examinable: true
---

# Inclusion-Exclusion for Two Events

> [!theorem]
> For any probability measure $P$ and any events $A, B \in \mathcal{F}$,
> $$P(A \cup B) = P(A) + P(B) - P(A \cap B).$$

## Depends on
- [[Probability Measure]] (axiom 3, for two disjoint events)
- [[Set Operations]] (splitting a union into disjoint pieces)

## Proof
See [[Proof - Inclusion-Exclusion for Two Events]].

## Intuition
- Adding $P(A)$ and $P(B)$ counts the overlap $A \cap B$ twice, so subtract it once.

## Used in
- Bounds such as $P(A \cup B) \leq P(A) + P(B)$, which follows because $P(A \cap B) \geq 0$.

## Counter-examples / when it fails
- Dropping the correction term is right only when $P(A \cap B) = 0$, for example when $A$ and $B$ are disjoint. For a fair die with $A = \{1, 2\}$ and $B = \{2, 3\}$, $P(A) + P(B) = 4/6$ but $P(A \cup B) = 3/6$.
