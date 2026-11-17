# Third-party notices

## Alvarmethod

Parts of the teaching rules in `plugin/skills/method/SKILL.md` are adapted from Alvarmethod (https://github.com/vasanthsreeram/Alvarmethod), an Agent Skills implementation of Eero Alvar's AI learning loop: the probe, plan, teach one node, lock-in quiz loop, the `one node only` and `use the quiz tool` shortcuts, and the rule against finishing the slide. Alvarmethod is used under the MIT licence below.

```
MIT License

Copyright (c) 2026 Vasanth Sreeram

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

The learning loop itself is Eero Alvar's, from his video "How I Use AI to Learn Things" (14 August 2026, https://youtu.be/kzcI5F4tGiU). No part of the video or its captions is included here.

## LearnHarness (ideas only)

Several teaching ideas in `plugin/skills/method/SKILL.md` and the `teach` and `quiz` skills come from Eero Alvar's LearnHarness (https://github.com/amosblomqvist/learnharness): the bracketing probe with a floor and a ceiling per prerequisite strand, predict-teach-check, starting from firm ground with motivated steps, teaching each result as a chain, distractors that each name a wrong picture, the cue classes for reviews, and the record of how the learner holds each node. Only the ideas are used, described here in new words; no text or code from LearnHarness is included in this repository.

## Libraries bundled with Study Desk

The optional app in `plugin/app/` ships these unmodified files in `plugin/app/static/vendor/`, so its page needs no network. Each licence is reproduced in full in `plugin/app/static/vendor/licenses/`.

| Library | Version | Files | Licence | Copyright |
|---|---|---|---|---|
| [KaTeX](https://github.com/KaTeX/KaTeX) | 0.19.1 | `katex.min.js`, `katex.min.css` | MIT | Copyright (c) 2013-2020 Khan Academy and other contributors |
| KaTeX fonts | 0.19.1 | `fonts/KaTeX_*` (`.woff2`, `.woff`, `.ttf`) | SIL Open Font License 1.1, as each font file states (the katex package as a whole is published under MIT) | Copyright (c) 2009-2010 Design Science, Inc.; Copyright (c) 2014-2018 Khan Academy; with Reserved Font Names `KaTeX_*` |
| [marked](https://github.com/markedjs/marked) | 18.2.1 | `marked.umd.js` | MIT | Copyright (c) 2018+, MarkedJS; Copyright (c) 2011-2018, Christopher Jeffrey. Its licence file also carries John Gruber's Markdown licence (BSD-style), reproduced with it |
| [DOMPurify](https://github.com/cure53/DOMPurify) | 3.4.18 | `purify.min.js` | Apache-2.0 or MPL-2.0, at the user's choice; used here under Apache-2.0 | (c) Cure53 and other contributors |
| [Mermaid](https://github.com/mermaid-js/mermaid) | 12.3.0 | `mermaid.min.js` | MIT | Copyright (c) 2014 - 2022 Knut Sveidqvist |

`mermaid.min.js` is Mermaid's published bundle, so it also contains Mermaid's own dependencies (D3, Cytoscape.js, dagre, lodash, Chevrotain, DOMPurify and others), each under its own licence as listed in the mermaid package.

The app's icon and its other files are part of this repository and under its MIT licence. The app starts Claude Code, which is installed separately and is not included; "Claude" and "Claude Code" are Anthropic's names, and this project is not affiliated with or endorsed by Anthropic.

## Software used, not included

The engine and the Study Desk server need nothing beyond Python's standard library. These optional tools are installed separately and keep their own licences:

- PyYAML (MIT): used for frontmatter when installed; otherwise a built-in reader is used.
- mermaid-cli (MIT): diagram checks and roadmap images.
- Obsidian and its community plugins (Dataview, LaTeX Suite, Linter, Update Time on Edit, Granola Meetings Simple Sync), and Granola.
- For the test suite only: pytest (MIT), and NetworkX (BSD-3-Clause) and PyYAML, which the parity tests compare the built-in code against.

`plugin/engine/vault_learning/digraph.py` follows NetworkX's function names and orderings, so the engine behaves as it did when it used NetworkX; it is written separately and includes no NetworkX code.

The sample PDF in `docs/examples/` is synthetic, written for this repository.
