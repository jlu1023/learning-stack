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

## Software used, not included

The engine needs nothing beyond Python's standard library. These optional tools are installed separately and keep their own licences:

- PyYAML (MIT): used for frontmatter when installed; otherwise a built-in reader is used.
- mermaid-cli (MIT): diagram checks and roadmap images.
- Obsidian and its community plugins (Dataview, LaTeX Suite, Linter, Update Time on Edit, Granola Meetings Simple Sync), and Granola.
- For the test suite only: pytest (MIT), and NetworkX (BSD-3-Clause) and PyYAML, which the parity tests compare the built-in code against.

`plugin/engine/vault_learning/digraph.py` follows NetworkX's function names and orderings, so the engine behaves as it did when it used NetworkX; it is written separately and includes no NetworkX code.

The sample PDF in `docs/examples/` is synthetic, written for this repository.
