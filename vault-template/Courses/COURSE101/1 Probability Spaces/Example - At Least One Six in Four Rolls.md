---
title: "Example - At Least One Six in Four Rolls"
type: example
course: COURSE101
module: "Probability Spaces"
section: "1.3"
created: 2026-01-01
updated: 2026-01-01
status: growing
depends_on: ["[[Complement Counting]]"]
---

# Example - At Least One Six in Four Rolls

**Illustrates:** [[Complement Counting]]

## Problem
- A fair die is rolled four times, independently. Find the probability of at least one six.

## Solution
1. Complement: no six in any of the four rolls.
2. $P(\text{no six}) = \left(\tfrac{5}{6}\right)^4 = \tfrac{625}{1296}$, using independence of the rolls.
3. $P(\text{at least one six}) = 1 - \tfrac{625}{1296} = \tfrac{671}{1296} \approx 0.518$.

## What to notice
- Counting "exactly one, two, three or four sixes" directly works too but takes four cases; the complement is one case.
- Step 2 needs independence; step 3 needs only the axioms of a [[Probability Measure]].
