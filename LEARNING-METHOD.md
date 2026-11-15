# The learning method

How the plugin teaches, and why. The full rules Claude follows are in `plugin/skills/method/SKILL.md`; this page explains the reasoning.

## The loop

The loop is **Eero Alvar's**, from his video [How I Use AI to Learn Things](https://youtu.be/kzcI5F4tGiU) (14 August 2026), as implemented in the MIT-licensed [Alvarmethod](https://github.com/vasanthsreeram/Alvarmethod) skills (see THIRD-PARTY.md):

1. **Probe** for the edge of what you know. Each prerequisite chain of the target is bracketed between a floor (what you reliably get right) and a ceiling (what you miss): the probe opens near the top, jumps up after a confident, reasoned answer and narrows in after a miss, and ends with one `Edge:` line per chain.
2. **Plan** a small prerequisite graph for the gaps, at most three notes per session.
3. **Teach one node,** one idea per turn, then hand the turn back.
4. **Lock in** with three quick recall questions: the statement, plus two of what breaks without a hypothesis, when to use it, and the proof's key idea. Advance only on a pass; on a fail, re-teach smaller or teach the missing prerequisite first.

Learning and recall are kept apart. A lock-in or a review only checks that you remember; worked problems come in later passes and unit tests, and writing proofs has its own track (below).

Inside each step the tutor asks you to **predict** the next move before it is taught, then resolves your prediction, then **checks** the idea on a new case. Each step starts from something you already hold as plainly true and is motivated by a problem the current picture cannot handle, and each result is said once as a **chain**: which premises, by which move, give the conclusion.

The tutor also keeps a quiet **Learner Model** (`Courses/_learning/Learner Model.md`): one dated line per node, in your own words, on how you hold it and where it was shaky. It reads that line before probing, teaching or reviewing the node, so a review months later does not start cold.

This plugin adds a vault underneath it: every node is one of your own notes, the prerequisite graph comes from the notes' `depends_on` links, and your progress is stored in the notes themselves, so the next session starts where the last one stopped.

## Why each piece is there

| Practice | What the plugin does | Evidence |
|---|---|---|
| **Retrieval practice** | Every node ends in a quiz; `/learn:quiz` is pure recall. | Testing yourself beats rereading for long-term retention (Roediger and Karpicke, 2006). |
| **Generation** | You state the definition, predict the result or attempt the step before anything is revealed. | Producing an answer yourself is remembered better than reading it (Slamecka and Graf, 1978). |
| **Spacing** | Reviews come back on a widening ladder of 1, 3, 7, 21 and 60 days. | Spreading study over time beats massing it (Cepeda and others, 2006). |
| **Successive relearning** | Each topic is learned in three spaced passes: foundations, depth, use. | A few spaced rounds of retrieval give most of the durable gain (Rawson and Dunlosky, 2011). |
| **Interleaving** | Warm-ups and `/learn:quiz mixed` mix courses and hide topic labels. | Mixing problem types makes you choose the method, which blocked practice never asks for (Rohrer and Taylor, 2007). |
| **Definitions first** | You decide examples from the definition alone before trusting intuition. | Students' mental image of a concept can drift from its definition (Tall and Vinner, 1981). |
| **Self-explanation** | "Why" follow-ups; a right answer with no reason counts as the edge, not as known. | Explaining each step to yourself improves understanding (Chi and others, 1989). |
| **Hints, not answers** | A three-rung hint ladder; the full solution only on `SOLUTION PLEASE`. | In a field experiment, students given an answer-giving AI tutor did worse on later unaided exams, while a tutor that gave hints did not harm them (Bastani and others, 2025). |
| **Faded scaffolding** | A new kind of problem or proof starts with every step named, then you name the steps, then you work alone; proofs fade over four stages on their own spaced track. | Fading worked-example steps one at a time, as the learner takes them over, eases the move from studying examples to solving alone (Renkl and Atkinson, 2003). |
| **Prediction first** | Each teaching step opens with your prediction of the next move, even one you cannot finish. | An unsuccessful attempt to retrieve an answer, followed by the answer, improves later recall compared with simply studying it (Kornell, Hays and Bjork, 2009). |
| **Varied cues** | Reviews dress each question in a different cue class (new notation, a new setting, the conclusion given and the premises asked, the near-miss twin, a step in a bigger problem), never the same one twice running. | Recall depends on how closely the cue matches how the idea was learned (Tulving and Thomson, 1973), so an idea practised only in the lecture's wording tends to come to mind only in that wording. |
| **Diagnostic distractors** | Every wrong option in a multiple-choice question is the answer a specific wrong picture gives, so a miss says which picture you hold. | Concept inventories built from common wrong answers reveal which misconception a student holds (Hestenes, Wells and Swackhamer, 1992). |
| **Calibration** | Confidence 1 to 5 before every verdict; confident misses are flagged. | Knowing what you do not know is what makes study time go to the right places (Dunlosky and others, 2013, review). |

## The spacing ladder

Each note carries a `mastery` level and a `review` date, written only by the engine:

- `unseen` becomes `learning` on your first lock-in pass.
- `learning` becomes `secure` on a pass at least 3 days later.
- `secure` becomes `mastered` on a pass at least 21 days after that.
- Each pass moves the next review one rung up: 1, 3, 7, 21, then 60 days.
- Any fail resets the interval to 1 day. One fail keeps the level, so a bad day costs only an early review; a second fail in a row drops one level.

The rungs are a practical schedule, not an optimum: the best gap depends on how long you need to remember something (Cepeda and others, 2008, found it grows with the retention interval). If you want a different ladder, change `LADDER` in `plugin/engine/vault_learning/state.py`.

## The proof track

Recalling a theorem and being able to prove it are different skills, so proofs are never asked for in lock-ins or reviews (only their key idea in one line). Each proof note has its own track, offered after a unit's test (`/learn:teach <course> proofs`), with four stages that hand over more each time:

1. **Step by step:** the tutor gives each move and you carry it out.
2. **Name the chain, then write:** you name the moves in order, then write the proof.
3. **From the key line:** you are given the one key line and write the rest.
4. **Solo,** on paper.

A pass moves you up a stage and brings the proof back in 3 days; a solo pass brings it back in 21 days, then 60. A fail moves you down a stage and brings it back in 2 days. A Proof Log records where each attempt broke.

## Matching the exam

Courses differ: a proof course rewards exact statements and justified steps, a methods course rewards choosing and carrying out the right method, an applied course rewards numbers and interpretation. Each course can have:

- an **Exam Profile** (`Templates/Exam Profile.md`), recording how the course is examined and marked, read from past papers for **style only**: never their questions;
- a **course override** in your Teaching Style, which changes the teaching ladder and the marking for that course.

Profiles never decide which topics to skip: examiners often set unfamiliar questions, so every syllabus topic is taught in full.

## References

- Bastani, H., Bastani, O., Sungu, A., Ge, H., Kabakci, O. and Mariman, R. (2025). Generative AI without guardrails can harm learning: evidence from high school mathematics. *Proceedings of the National Academy of Sciences*, 122(26).
- Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T. and Rohrer, D. (2006). Distributed practice in verbal recall tasks: a review and quantitative synthesis. *Psychological Bulletin*.
- Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T. and Pashler, H. (2008). Spacing effects in learning: a temporal ridgeline of optimal retention. *Psychological Science*.
- Chi, M. T. H., Bassok, M., Lewis, M. W., Reimann, P. and Glaser, R. (1989). Self-explanations: how students study and use examples in learning to solve problems. *Cognitive Science*.
- Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J. and Willingham, D. T. (2013). Improving students' learning with effective learning techniques. *Psychological Science in the Public Interest*.
- Rawson, K. A. and Dunlosky, J. (2011). Optimizing schedules of retrieval practice for durable and efficient learning: how much is enough? *Journal of Experimental Psychology: General*.
- Hestenes, D., Wells, M. and Swackhamer, G. (1992). Force Concept Inventory. *The Physics Teacher*, 30(3).
- Kornell, N., Hays, M. J. and Bjork, R. A. (2009). Unsuccessful retrieval attempts enhance subsequent learning. *Journal of Experimental Psychology: Learning, Memory, and Cognition*, 35(4).
- Renkl, A. and Atkinson, R. K. (2003). Structuring the transition from example study to problem solving in cognitive skill acquisition: a cognitive load perspective. *Educational Psychologist*.
- Roediger, H. L. and Karpicke, J. D. (2006). Test-enhanced learning: taking memory tests improves long-term retention. *Psychological Science*.
- Rohrer, D. and Taylor, K. (2007). The shuffling of mathematics problems improves learning. *Instructional Science*.
- Slamecka, N. J. and Graf, P. (1978). The generation effect: delineation of a phenomenon. *Journal of Experimental Psychology: Human Learning and Memory*.
- Tall, D. and Vinner, S. (1981). Concept image and concept definition in mathematics with particular reference to limits and continuity. *Educational Studies in Mathematics*.
- Tulving, E. and Thomson, D. M. (1973). Encoding specificity and retrieval processes in episodic memory. *Psychological Review*, 80(5).
