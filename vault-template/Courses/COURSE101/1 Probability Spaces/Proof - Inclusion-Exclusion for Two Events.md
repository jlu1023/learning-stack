---
title: "Proof - Inclusion-Exclusion for Two Events"
type: proof
course: COURSE101
module: "Probability Spaces"
section: "1.2"
created: 2026-01-01
updated: 2026-01-01
status: growing
depends_on: ["[[Probability Measure]]", "[[Set Operations]]"]
---

# Proof - Inclusion-Exclusion for Two Events

**Theorem:** [[Inclusion-Exclusion for Two Events]]
**Strategy:** direct, by splitting into disjoint pieces

## Setup
- $P$ is a probability measure and $A, B \in \mathcal{F}$. Show $P(A \cup B) = P(A) + P(B) - P(A \cap B)$.
- Finite additivity: for disjoint $C, D$, take $A_1 = C$, $A_2 = D$ and $A_i = \emptyset$ for $i \geq 3$ in axiom 3. Since $P(\emptyset) = 0$ (apply axiom 3 to $\emptyset, \emptyset, \dots$), $P(C \cup D) = P(C) + P(D)$.

## Steps
1. $A \cup B = A \cup (B \setminus A)$, and $A$, $B \setminus A$ are disjoint, so $P(A \cup B) = P(A) + P(B \setminus A)$.
2. $B = (A \cap B) \cup (B \setminus A)$, again disjoint, so $P(B) = P(A \cap B) + P(B \setminus A)$.
3. Subtract step 2 from step 1: $P(A \cup B) - P(B) = P(A) - P(A \cap B)$, which rearranges to the result.

## Where each step relies on
- Steps 1 and 2: [[Set Operations]] for the disjoint splits, and finite additivity from [[Probability Measure]].
- Step 3: the probabilities are finite real numbers, so subtraction is allowed.
