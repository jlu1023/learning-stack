---
name: query
description: Answer a question from the vault's own notes, citing each claim with a wikilink, and say plainly where the vault has nothing. Use when the learner asks what their notes say about something.
argument-hint: <question>
---

Answer `$ARGUMENTS` from the vault.

1. **Get the lay of the land** from `_meta/Vault Index.md` if it exists (`VL index` regenerates it).
2. **Search the vault** for relevant notes, including synonyms and related concepts. For maths, search both the definition and the results that use it.
3. **Read the relevant notes in full.** For maths and proofs, the whole note often matters.
4. **Answer directly.** Cite every non-trivial claim with `[[Note]]`. Quote definitions and theorem statements from the notes; show derivations step by step, linking each step to the note it relies on. If notes give different angles, present them.
5. **Gaps:** if the vault does not have enough, say so. Do not fill the gap from general knowledge unless asked; if you add anything, mark it "beyond the notes". Offer to stub a note for what is missing.
6. **Contradictions:** if two notes conflict, quote both and offer to flag them with `#contradicts`.
7. **Offer to file** the answer as a `type: concept` note linking its sources. If saved, log `query | <question>` in `_meta/log.md`.
