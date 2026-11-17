// Markdown + KaTeX + Obsidian syntax (wikilinks, embeds, callouts, comments).
// Maths is lifted out before Markdown parsing so `_` and `\` inside it survive,
// then put back as rendered KaTeX after the HTML has been sanitised.

const TOKEN = new RegExp([
  '(```[\\s\\S]*?(?:```|$)|`[^`\\n]+`)',           // 1 code: left alone
  '(\\$\\$[\\s\\S]+?\\$\\$|\\\\\\[[\\s\\S]+?\\\\\\])', // 2 display maths
  '(\\\\\\([\\s\\S]+?\\\\\\))',                     // 3 inline \( \)
  '(\\$(?![\\s$])(?:\\\\.|[^$\\\\\\n])+?\\$(?!\\d))', // 4 inline $ $
  '(!\\[\\[[^\\]\\n]+\\]\\])',                      // 5 embed
  '(\\[\\[[^\\]\\n]+\\]\\])',                       // 6 wikilink
].join('|'), 'g');

const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function tex(src, display) {
  try {
    return katex.renderToString(src, { displayMode: display, throwOnError: false, strict: false });
  } catch (e) {
    return `<code class="tex-error">${esc(src)}</code>`;
  }
}

export function render(markdown, { note = false } = {}) {
  let src = markdown;
  if (note) src = src.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, '');
  src = src.replace(/%%[\s\S]*?%%/g, '');
  if (note) src = src.replace(/(^|[ \t])\^[\w-]+[ \t]*(?=\r?$)/gm, '');  // Obsidian block ids
  const maths = [];
  src = src.replace(TOKEN, (m, code, disp, par, inl, embed, link) => {
    if (code) return m;
    if (disp) {
      const body = disp.startsWith('$$') ? disp.slice(2, -2) : disp.slice(2, -2);
      maths.push(tex(body.trim(), true));
      return `@@M${maths.length - 1}@@`;  // no blank lines: they would split a callout
    }
    if (par) { maths.push(tex(par.slice(2, -2).trim(), false)); return `@@M${maths.length - 1}@@`; }
    if (inl) { maths.push(tex(inl.slice(1, -1), false)); return `@@M${maths.length - 1}@@`; }
    if (embed) {
      const target = embed.slice(3, -2).split('|')[0].trim();
      if (/\.(png|jpe?g|gif|svg|webp)$/i.test(target)) return `<img class="embed" src="/api/asset?name=${encodeURIComponent(target)}" alt="${esc(target)}">`;
      return `<a class="wl" data-note="${esc(target)}">${esc(target)}</a>`;
    }
    const inner = link.slice(2, -2);
    const [target, alias] = inner.split('|');
    const label = (alias || target.split('#')[0].split('/').pop() || target).trim();
    return `<a class="wl" data-note="${esc(target.trim())}">${esc(label)}</a>`;
  });
  let html = marked.parse(src, { gfm: true, breaks: false });
  html = DOMPurify.sanitize(html, { ADD_ATTR: ['data-note'] });
  html = html.replace(/@@M(\d+)@@/g, (_, i) => maths[+i] || '');
  return html;
}

// Post-processing that needs the DOM: callouts, mermaid, external links.
export async function enhance(root, { diagrams = true } = {}) {
  for (const bq of root.querySelectorAll('blockquote')) {
    const first = bq.querySelector('p');
    if (!first) continue;
    const m = first.innerHTML.match(/^\s*\[!(\w+)\][+-]?[ \t]*([^\n<]*)(?:<br>|\n)?/);
    if (!m) continue;
    first.innerHTML = first.innerHTML.slice(m[0].length);
    bq.classList.add('callout', 'callout-' + m[1].toLowerCase());
    const title = document.createElement('div');
    title.className = 'callout-title';
    title.innerHTML = m[2] || m[1][0].toUpperCase() + m[1].slice(1).toLowerCase();
    bq.prepend(title);
    if (/^(theorem|lemma|proposition|corollary)/i.test(title.textContent) || /^(theorem|lemma|proposition|corollary)$/i.test(m[1])) bq.classList.add('thm');
    if (!first.textContent.trim() && !first.children.length) first.remove();
  }
  for (const a of root.querySelectorAll('a[href]')) { a.target = '_blank'; a.rel = 'noopener'; }
  if (!diagrams) return;
  const blocks = root.querySelectorAll('pre > code.language-mermaid');
  if (!blocks.length) return;
  if (!window.mermaid) {
    await new Promise((ok, bad) => {
      const s = document.createElement('script');
      s.src = '/vendor/mermaid.min.js'; s.onload = ok; s.onerror = bad;
      document.head.append(s);
    });
  }
  const dark = getComputedStyle(document.documentElement).getPropertyValue('--scheme').trim() === 'dark';
  window.mermaid.initialize({ startOnLoad: false, theme: dark ? 'dark' : 'neutral', securityLevel: 'strict' });
  let n = 0;
  for (const code of blocks) {
    try {
      const { svg } = await window.mermaid.render(`mmd-${Date.now()}-${n++}`, code.textContent);
      const div = document.createElement('div');
      div.className = 'mermaid-out';
      div.innerHTML = svg;
      code.parentElement.replaceWith(div);
    } catch (e) { /* leave the source visible */ }
  }
}
