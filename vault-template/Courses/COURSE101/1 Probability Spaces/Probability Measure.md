---
title: "Probability Measure"
type: definition
course: COURSE101
module: "Probability Spaces"
section: "1.1"
lecture: 1
created: 2026-01-01
updated: 2026-01-01
status: growing
depends_on: ["[[Set Operations]]"]
used_in: ["[[Inclusion-Exclusion for Two Events]]", "[[Proof - Inclusion-Exclusion for Two Events]]", "[[Complement Counting]]"]
examinable: true
---

# Probability Measure

> [!definition]
> Let $\Omega$ be a sample space and $\mathcal{F}$ a collection of its subsets (the events) that contains $\Omega$ and is closed under complements and countable unions. A **probability measure** is a function $P : \mathcal{F} \to \mathbb{R}$ such that
> 1. $P(A) \geq 0$ for every $A \in \mathcal{F}$;
> 2. $P(\Omega) = 1$;
> 3. for every sequence $A_1, A_2, \dots \in \mathcal{F}$ of pairwise disjoint events, $P\left(\bigcup_{i=1}^{\infty} A_i\right) = \sum_{i=1}^{\infty} P(A_i)$.

## In plain English
- A probability assigns each event a non-negative number, gives the whole sample space probability 1, and adds up over events that cannot happen together.

## Why it matters
- Every rule of probability (complements, inclusion-exclusion, continuity) is derived from these three axioms, so nothing has to be assumed case by case.

## Example
- A fair die: $\Omega = \{1, \dots, 6\}$, $\mathcal{F}$ all subsets, $P(A) = |A|/6$.
- A non-example: $m(A) = 1$ for every non-empty $A$ fails axiom 3, since $m(\{1\} \cup \{2\}) = 1 \neq m(\{1\}) + m(\{2\}) = 2$.

## Used in
- [[Inclusion-Exclusion for Two Events]]
- [[Complement Counting]]

## Related
- Built on: [[Set Operations]]
- See also: [[Example - At Least One Six in Four Rolls]]
