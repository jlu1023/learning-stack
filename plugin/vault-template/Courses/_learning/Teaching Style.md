---
title: Teaching Style
type: reference
created: 2026-01-01
updated: 2026-01-01
status: active
human_authored: true
---

# Teaching Style

**Your note.** It tells `/learn:teach` and `/learn:quiz` how you want to be taught. They read it every run and never edit it. Where it conflicts with the plugin's `method` skill, this note wins, except for the method's hard rules: teach from the vault notes, verify computations, and never give a full solution before you have attempted it.

**The aim:** a steadily expanding, recorded edge of knowledge. Learn first, then recall; writing proofs is practised on its own track.

Everything below is a working default. Rewrite it in your own words as you learn what works for you, and log each change under Refinements.

## How I learn best

- *Replace with your own.* For example: built up in order (definitions, then their first consequences, then theorems); by doing rather than reading; by applying the same idea in different settings.

## The ladder (for every node, in this order)

0. **Motivate.** What problem forced this definition or result into existence, and what goes wrong without it?
1. **Definition.** I state it exactly. For each condition: what it does, and what breaks without it. Then I negate it.
2. **Examples from the definition alone.** I generate examples, non-examples and edge cases, and decide each using only the definition. (Tall and Vinner: a student's mental picture of a concept can differ from its formal definition; this step closes the gap.)
3. **First consequences.** The immediate results, reasoned through from the definitions and axioms with hints only (for example, $P(\emptyset) = 0$ from the probability axioms). Writing them out as proofs is the proof track.
4. **Theorems.** First ask how I could have discovered the result. Then I predict the statement and say where each hypothesis is used, and learn the proof's key idea.
5. **Connect.** Link the node to the earlier nodes it builds on, and to other courses where the link is real.
6. **Application.** A problem that needs the idea, then the same idea in a different setting: what carries over, what fails, and why.
7. **Lock-in (recall only).** The statement word for word, then two quick recall questions: the role of a condition, when to use it, or for a theorem the proof's key idea in one line. No proofs and no new problems.

## Three passes per topic (successive relearning)

Each topic is learned in three spaced passes rather than all at once (Rawson and Dunlosky's successive relearning: about three spaced sessions of retrieval give most of the durable gain). `/learn:teach` picks the pass from the note's learner state.

| Pass | When the note is | Rungs |
|---|---|---|
| **1. Foundations** | `unseen` | 0, 1, 2, 3 and 7. Theorems get their statement, the role of each hypothesis and the proof's key idea |
| **2. Depth** | `learning`, at least 3 days after pass 1 | Recall the definitions from memory, then 4, 5, one light application on paper, 7 |
| **3. Use** | `secure` or `mastered` | Recall, then one light application in a new setting |

A failed recall in pass 2 or 3 drops the note back to pass 1. I can say `pass 1` to go back to the foundations, or `deepen` to move to pass 2 early.

**Working on paper:** for any problem that needs working, I solve it on paper and type only the final answer or the line I am unsure of. If I paste a photo of my working, point to the first broken line.

**Scaffold first, then fade:** a multi-step problem or proof of a kind I have not done before starts scaffolded (you name each step, I do it, one per turn). Next time I name the steps, then solve. Then I solve alone. Fade only after a clean attempt.

**Session length:** at most 3 nodes and 30 to 45 minutes.

## Probes

- Start at the definition (exact statement, the role of each condition), then examples, then a first consequence.
- A right answer without a reason counts as the edge, not as known. "I don't know" is always a valid answer.

## Proof track

Proofs are learned, not recalled: lock-ins and `/learn:quiz` never ask me to write one, only its key idea in one line.

- **Stages** (a fading scaffold): (1) you give the chain of moves step by step and I carry out each; (2) I name the chain, then write; (3) I write it from the theorem and one key line; (4) solo, on paper, typing only the line I am unsure of.
- **Spaced, not blocked:** each proof has its own level, stage and review date in the engine, and every attempt gets a line in `Proof Log.md` saying where it broke. After a unit test, `/learn:teach <course> proofs` takes due proofs first, mixed across units, then new proofs from tested units. At most 3 per session.
- **Recall in step:** once I have worked on a proof, its key idea joins its theorem's recall questions.
- A course override below may make the proof track a course's main practice, or keep its short derivations in recall.

## Pace and feedback

- Short turns and fast feedback: one rung per turn.
- Fewer, harder problems over many easy ones.

## Course overrides

Courses differ, so each course can have its own style here, overriding the default ladder for that course only. Draft each one from the course's Exam Profile (the kinds of question and skill the exam rewards, and how answers are marked) and add it once you have checked it.

**Style, not topics.** Past papers are not a guide to which topics will come up, since examiners often set unfamiliar questions. Overrides shape *how* a course is taught and marked, never *what* is skipped: every syllabus topic is taught in full.

The three examples below show the three common shapes. Rename the headings to your course codes, or delete them.

### Example: a proof-led course (for example, real analysis)

Mostly proof, with exact statements and unseen questions. **Keep the full default ladder, and make the proof track the main practice**, plus:

- **Statements:** lock-in checks every definition and named theorem word for word, with every condition and the quantifiers in order.
- **Plan before proving:** on the proof track, in one line, I name the definition I will unwind or the theorem I will cite, and check its hypotheses. Then I write the proof.
- **Decide, then prove:** passes 2 and 3 include fresh "is it true that...?" items built from the notes. I decide first, then prove it or give a counterexample.
- **New settings:** application uses a space not seen in the notes.

**Marking my work:** a statement passes only if it is exact (point to the missing condition). A proof passes if every step is justified; any valid route counts. Flag the first unjustified step and every cited theorem whose hypotheses I did not check. A verdict with no argument fails.

### Example: a methods-led course (for example, applied calculus)

Most marks are for choosing and carrying out a method. **Method notes use a method ladder in place of the default one:**

1. **When.** What signals this method, and which method it is most often confused with.
2. **Why it works.** One or two lines linking the method to the concept underneath it.
3. **Steps.** I give the steps in order, and the condition to check at each one.
4. **Traps.** Where it usually goes wrong: a rule used when its conditions fail, a lost sign or limit.
5. **Do it.** One short problem on paper. In pass 1 the method is named; in passes 2 and 3 it is not, so I choose it first.
6. **Lock-in (recall only).** Name the method from a problem's first line, and give the steps and why they work. Problems in new settings belong to passes 2 and 3.

**Recall and method, not proof:** state definitions and conditions accurately and say when a result applies; nothing on the proof track except the derivations the Exam Profile marks as bookwork, or when I ask.

**Marking my work:** every justification is a marked step. Check that I stated each rule's condition before using it, and that the arithmetic is exact. A right answer with a missing justification is partial: name the missing step.

### Example: an applied, numerical course (for example, introductory finance)

Models carried through to numbers, then explained. **Ladder:**

1. **Concept:** what the model says and what it assumes.
2. **Why it holds:** for every result on the main slides, I can say why it holds in a few sentences, with the key line of algebra.
3. **Apply:** one short numerical problem on paper. I type the set-up line and the final number.
4. **Interpret:** what the number means, and which way it moves when an input changes.
5. **Evaluate a statement:** a fresh true-or-false statement. Verdict first, then two or three sentences of reasoning, including why a plausible-sounding version fails.
6. **Theory against data:** what the evidence shows, where the lectures cover it.
7. **Lock-in.**

**Marking my work:** method credit separately from arithmetic; a bare true or false earns nothing; a missing interpretation loses its share. Report a mark out of a typical part (for example "2 of 3: verdict and mechanism right, the reason it fails is missing").

## Refinements

Add a dated line each time you change this note, with the reason.

- YYYY-MM-DD: first version.
