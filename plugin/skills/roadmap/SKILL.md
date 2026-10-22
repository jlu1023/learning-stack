---
name: roadmap
description: Regenerate course roadmaps (Mermaid dependency maps, suggested order, data gaps) from the notes' depends_on fields, then report gaps and validation. Use after adding or editing course notes.
argument-hint: "[course | all]"
---

Regenerate roadmaps for `$ARGUMENTS` (default `all`: every `Courses/<CODE>/` with a `<CODE> Syllabus.md`, except the reference courses listed in `vault-learning.yaml`, which only ever appear as external prerequisites).

1. **Run the generator:** `VL roadmap <COURSE|all>` (`VL` is the engine command in the `method` skill).
   - It writes `Courses/<CODE>/<CODE> Roadmap.md`, a generated block between the roadmap markers in each module MOC, and one link line between the same markers in the course MOC. The markers are `%% roadmap:start %%` and `%% roadmap:end %%` for Obsidian, and `<!-- roadmap:start -->` and `<!-- roadmap:end -->` in plain mode (hidden in any Markdown viewer); either is recognised.
   - Nothing outside the markers changes, and `human_authored: true` MOCs are skipped.
   - **Plain mode** (`frontend: plain`) also writes each diagram as an SVG beside its note (`<CODE> Roadmap - Course map.svg`, `<Module> Roadmap.svg`) and embeds it as an image, with the Mermaid source below it. Without mermaid-cli it writes `.mmd` sources instead and reports how to install it. `all` also rewrites `Courses/_learning/Review Queue.md` as static tables, since Dataview needs Obsidian.
   - If mermaid-cli is installed, every diagram is validated before anything is written; on any failure, nothing is written and the exit code is 1. Without it, the report says the diagrams were not checked.
   - A rerun with no data changes writes nothing.

2. **Report in chat** from the JSON output. Mention notes by plain name, never as wikilinks.
   - Per course: nodes, in-course edges, edges to other courses, broken links, ambiguous links, cycles, `used_in` mismatches, and unreadable frontmatter.
   - Any MOCs skipped, and why.
   - The validation result (method, diagram count, failures).
   - Which files were written, including roadmap images and the Review Queue in plain mode, and any image error with its install line.

3. **Do not fix data gaps by editing notes.** Broken links, `used_in` mismatches and missing `depends_on` are listed in each Roadmap's Data gaps section for a separate cleanup pass. If validation fails, report the failing diagram and error, and do not hand-edit generated blocks.

4. **Log:** append a `roadmap | <COURSE|all>` entry to `_meta/log.md` only when run on its own. When `teach`, `quiz` or `ingest` calls it, their own log entry covers it.
