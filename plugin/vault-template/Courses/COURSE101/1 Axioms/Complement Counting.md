---
title: "Complement Counting"
type: method
course: COURSE101
module: "Axioms"
section: "1.3"
lecture: 1
created: 2026-01-01
updated: 2026-01-01
status: growing
depends_on: ["[[Probability Measure]]"]
used_in: ["[[Example - At Least One Six]]"]
examinable: true
---

# Complement Counting

> [!method]
> Compute $P(A)$ as $1 - P(A^c)$ when the complement $A^c$ is easier to describe than $A$.

## When to use
- The event says "at least one", "not all" or "some": its complement is "none" or "all", usually a single case.
- Often confused with adding the cases of $A$ directly, which double-counts when the cases overlap (see [[Inclusion-Exclusion]]).

## Steps
1. Write $A^c$ in words and check that $A$ and $A^c$ together cover $\Omega$ with no overlap.
2. Compute $P(A^c)$.
3. $P(A) = 1 - P(A^c)$, because $A$ and $A^c$ are disjoint with union $\Omega$, so $P(A) + P(A^c) = P(\Omega) = 1$ by [[Probability Measure]].

## Worked example
- See [[Example - At Least One Six]].

## Common mistakes
- Taking the complement of "at least one" as "at least one fails" rather than "none".
- Multiplying probabilities for the complement without independence.

## Related
- [[Inclusion-Exclusion]]
