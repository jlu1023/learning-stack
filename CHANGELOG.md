# Changelog

## 1.6.0

- Study Desk, an optional local app (`/learn:app`, or `python3 <plugin>/app/serve.py` from the study folder): a page in your browser with one tab per course plus a General tab, each with its own conversation; a home table of progress per course; maths typeset with KaTeX, Mermaid diagrams, wikilinks and Markdown links that open the note beside the chat; photos of working pasted or dropped in; a style editor; and a status line with the model, the effort and your Claude usage limits.
- It is a shell: the tutor in each tab is headless Claude Code started in the study folder, one long-lived process per tab, following the same skills and engine. The server never writes into the notes; its settings, uploads and log live in a per-user data folder.
- The tutor runs in permission mode `auto` by default, which acts without asking; `--permission-mode`, `STUDY_DESK_PERMISSION_MODE` or the app's `config.json` choose a stricter mode. `bypassPermissions` is never accepted.
- Standard library only, like the engine: the server is `http.server`, the chat is streamed as Server-Sent Events, and KaTeX (with its fonts), marked, DOMPurify and Mermaid are bundled, so the page loads nothing from the network (licences in THIRD-PARTY.md and `plugin/app/static/vendor/licenses/`).
- Local only: it listens on 127.0.0.1, checks the Host and Origin of every request and requires a custom header on every write, so another web page cannot reach the tutor.
- Works in a vault, a plain-editor vault and a connected notes folder: the folder is resolved by the engine, as for the skills. Windows extras: a desktop shortcut, a launcher with no console window, a stop script and a sharp taskbar icon.
- Engine: `where` also lists the folder's `courses` (the app's tabs come from it).
- Tests for the app run with the engine's, against a stand-in for the `claude` command.

## 1.5.0

- The probe brackets each prerequisite strand between a floor and a ceiling: it opens near the top of what the target needs, jumps up after a confident, reasoned answer, steps gently after a hesitant one and narrows in after a miss, with no filler questions. The session file gets one `Edge:` line per strand (floor, ceiling, misconception, where to build from).
- Teaching: each step is predict, teach, check (a prediction on its own turn, then the teaching resolves it, then one check on a new case); each node starts from firm ground with motivated steps; each result is said once as a chain (premises, move, conclusion); visuals are drawn into the session file only when asked for.
- Questions: every multiple-choice distractor names a specific wrong picture, and reviews vary their cue through six classes (`lecture`, `notation`, `setting`, `reverse`, `twin`, `combined`), never the same one twice running, moving along on a clean pass and back on a miss. The cue class is noted per question in the session file; the engine does not track it. Lock-ins may ask a theorem's chain instead of its proof's key idea.
- The Learner Model (`Courses/_learning/Learner Model.md`, new in the template and in connected libraries): one dated line per node per session, in the learner's own words, on how they hold it and where it was shaky. Written silently at the close of `teach` and `quiz`, read before probing, teaching or reviewing that node.
- Engine: `show` adds the note's two newest `held_as` lines and `due` adds each item's newest one, read from the Learner Model (never written by the engine).
- Textbook look-up: when a note is thin, read only the pages it cites, plus at most a page either side; never search a whole book.
- These ideas come from Eero Alvar's LearnHarness, rewritten in new words (THIRD-PARTY.md). LEARNING-METHOD.md gains the evidence for prediction, varied cues and diagnostic distractors.

## 1.4.0

- Learning and recall are separate. A lock-in is now three quick recall questions: the statement with every hypothesis, plus two of what breaks without a hypothesis, when to use it (or a near-miss twin), and the proof's key idea. No proofs and no new problems in lock-ins or reviews; problems come in later passes and unit tests.
- The proof track: each proof has its own level, scaffold stage and review dates. `/learn:teach <course> proofs [unit]` (or `proofs` alone, across courses) runs it after a unit test: due proofs first, then new ones, at most three a session, through four fading stages (step by step, name the chain then write, from the key line, solo). A pass moves up a stage and returns in 3 days (21, then 60, once solo); a fail moves down and returns in 2. A new Proof Log records where each attempt broke.
- Engine: `record <proof> --result pass|fail --stage N` (required for proof notes, refused for others, both as JSON errors); a new `proofs [COURSE|mixed] [--limit N]` command; `due` and `next` never draw proofs; `show` and `graph` add `proof_state`. Human-authored proofs keep their state in `proof-progress.md`. Both Review Queues gain a Proofs due view.
- Library mode: a card named `Proof - <Card>` is on the proof track, its state in the card like any card's.
- Scaffold first, then fade: any new kind of multi-step problem starts with each step named, then the learner names the steps, then works alone.
- The method skill is consolidated (about a quarter shorter) with no other rule changes; the template's Teaching Style follows the new lock-in and proof track.

## 1.3.0

- Unit tests: once every node in a unit is learned, `/learn:teach` offers a short test (one question per node, an integrative problem, a teach-back); `test [N]` runs one on demand and `<module> final` tests a whole module.
- A teach-back question guards the step to `mastered`.
- Slips are pointed out once and never logged or re-taught; only conceptual errors get Error Log redos.
- One push-back per node on a right answer, on substance only; reasoning the learner did not give is never credited.
- Misses are sorted (slip, blank, wrong tool, misconception) after asking for the learner's thinking; only wrong tools and misconceptions are logged, and they are retested with fresh wording before the session closes.
- The probe starts from recorded state and from the top of what the target needs; a right answer at low confidence counts as edge.
- `/learn:quiz` picks the question type from the node's level and adjusts difficulty as it goes; generated problems are solved and checked for shortcuts before they are posed.
- Confidence is asked in the same question call as the answer; the push-back only applies from `secure` up.
- Probes now record: a reasoned, confident right answer is a pass (an untaught node becomes `learning`), a miss on an already-learned node is a fail; misses on untaught nodes record nothing. The expanding edge of knowledge is the record.
- Several of these ideas were adapted, in new wording, from Eero Alvar's LearnHarness prompts.
- A plain progress line per unit at the close (`5/13 learning, 2/13 secure`), and `harder` / `easier` shortcuts.

## 1.2.2

- Ready for the plugin directory: `/learn:setup` no longer offers to write Claude Code's permission settings (it explains how to allow the engine instead), and the plugin README says exactly what the plugin runs, writes, reads and sends.

## 1.2.1

- Every expected failure (an unknown course, an ambiguous note name, a bad `--date`, a broken `vault-learning.yaml`, a refused write) is a JSON error with exit code 2, never a traceback.
- A malformed redo date in the Error Log is reported instead of stopping `due`; a missing `progress.md` is created when first needed; `doctor` copes with a broken settings file.
- `/learn:setup` now carries out the connect steps itself (the `connect` skill only starts when typed), and `/learn:ingest` points library users to `/learn:connect`.
- `--version`, a plugin icon, tests on Windows, macOS and Linux with Python 3.10 and 3.13.

## 1.2

- Nothing to install but Python 3.10 or later: the engine uses the standard library only (a built-in graph module, and a built-in frontmatter reader when PyYAML is absent).
- Converters removed: Claude Code reads PDFs and images itself; Word and PowerPoint are saved as PDF.
- `/learn:setup` makes a vault from the template that now ships inside the plugin, or connects existing notes; new engine commands `init` and `doctor`.
- Plain mode keeps Mermaid blocks and exports SVG images only when mermaid-cli is installed.
- An impossible date in a note's frontmatter no longer stops the roadmap.
- Permission rules that match on Windows (backslash paths, PowerShell).

## 1.1

- Use it without Obsidian (`frontend: plain`): Markdown links, HTML-comment markers, static review tables.
- Bring your own notes: `/learn:connect` builds review cards over a read-only folder of notes, with problem sheets and past papers cited, never solved.
- Gentler demotion: one fail keeps the level; a second fail in a row drops it. Lenient marking for slips; learn first when behind.

## 1.0

- First release: the `learn` plugin for Claude Code (teach, quiz, primer, roadmap, ingest, lecture, query, lint) with an Obsidian vault template and an optional Granola lecture-transcript module.
