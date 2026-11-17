# Vendored libraries

Study Desk loads these from this folder, so the page needs no network. Each file is the unmodified one published in the named npm package.

| Files | Package and version | Licence | Text |
|---|---|---|---|
| `katex.min.js`, `katex.min.css` | katex 0.19.1 (`dist/`) | MIT | `licenses/katex-LICENSE.txt` |
| `fonts/KaTeX_*` | katex 0.19.1 (`dist/fonts/`) | SIL Open Font License 1.1, as each font file states | `licenses/katex-fonts-OFL.txt` |
| `marked.umd.js` | marked 18.2.1 (`lib/`) | MIT | `licenses/marked-LICENSE.md` |
| `purify.min.js` | dompurify 3.4.18 (`dist/`) | Apache-2.0 or MPL-2.0 (used here under Apache-2.0) | `licenses/dompurify-LICENSE.txt` |
| `mermaid.min.js` | mermaid 12.3.0 (`dist/`) | MIT | `licenses/mermaid-LICENSE.txt` |

`mermaid.min.js` is Mermaid's published bundle and so also contains Mermaid's own dependencies (D3, Cytoscape.js, dagre, lodash, Chevrotain, DOMPurify and others), each under its own licence as listed in the mermaid package.

To update a library, replace its file with the one from the new package version, update this table and the licence text, and update THIRD-PARTY.md at the top of the repository.
