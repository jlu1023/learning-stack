import { render, enhance } from '/md.js';

const $ = sel => document.querySelector(sel);
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const api = (path, opts = {}) => fetch(path, { ...opts, headers: { 'X-Study-Desk': '1', ...(opts.headers || {}) } });
const LEVELS = ['mastered', 'secure', 'learning'];
const tabUrl = id => '/api/chat/' + encodeURIComponent(id);

// ------------------------------------------------------------ theme
const PRESETS = {
  Article: { scheme: 'light', bg: '#f6f6f4', surface: '#ffffff', text: '#1b1a17', muted: '#66635c', border: '#dad6cc' },
  Paper: { scheme: 'light', bg: '#f6f3ec', surface: '#fffdf8', text: '#24211c', muted: '#7a7468', border: '#e2dccf' },
  Slate: { scheme: 'light', bg: '#eef1f4', surface: '#ffffff', text: '#1c2430', muted: '#66717f', border: '#d8dee6' },
  Sepia: { scheme: 'light', bg: '#efe4cf', surface: '#f7efde', text: '#3b2f20', muted: '#806f58', border: '#d9c9a8' },
  Ink: { scheme: 'dark', bg: '#15171b', surface: '#1d2026', text: '#e6e3dc', muted: '#8e8a80', border: '#2c3038' },
  Chalk: { scheme: 'dark', bg: '#1e2a26', surface: '#24332e', text: '#e8efe9', muted: '#8fa39a', border: '#33463f' },
};
const FONTS = {
  'Computer Modern (LaTeX)': 'KaTeX_Main, "Latin Modern Roman", "Times New Roman", serif',
  'Sitka (reading serif)': '"Sitka Text", Georgia, serif',
  Georgia: 'Georgia, serif',
  Cambria: 'Cambria, Georgia, serif',
  Constantia: 'Constantia, Georgia, serif',
  'Segoe UI (sans)': '"Segoe UI", system-ui, sans-serif',
  Calibri: 'Calibri, "Segoe UI", sans-serif',
  Verdana: 'Verdana, sans-serif',
};
const DEFAULTS = { preset: 'Article', colors: {}, font: 'Computer Modern (LaTeX)', size: 18.5, math: 1, width: 700, accents: {}, paper: true, model: '', effort: '' };
let settings = structuredClone(DEFAULTS);
let saveTimer;

function applyTheme() {
  const root = document.documentElement.style;
  const base = { ...PRESETS[settings.preset] || PRESETS.Paper, ...settings.colors };
  for (const k of ['scheme', 'bg', 'surface', 'text', 'muted', 'border']) root.setProperty('--' + k, base[k]);
  root.setProperty('--font', FONTS[settings.font] || FONTS.Georgia);
  root.setProperty('--size', settings.size + 'px');
  root.setProperty('--math', settings.math);
  root.setProperty('--width', settings.width + 'px');
  root.setProperty('--accent', accentOf(state.current));
  const hex = accentOf(state.current).replace('#', '');
  const lum = [0, 2, 4].map(i => parseInt(hex.slice(i, i + 2), 16)).reduce((sum, v, i) => sum + v * [0.299, 0.587, 0.114][i], 0);
  root.setProperty('--on-accent', lum > 165 ? '#1a1a1a' : '#ffffff');
  document.body.classList.toggle('paper', !!settings.paper);
  document.querySelectorAll('[data-tab]').forEach(n => n.style.setProperty('--tab-accent', accentOf(n.dataset.tab)));
}
function saveSettings() {
  applyTheme();
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => api('/api/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(settings) }), 400);
}
function accentOf(id) {
  const tab = state.tabs.find(t => t.id === id);
  return tab ? settings.accents[id] || tab.accent : '#d97757';  // Home and the app itself are orange
}

function buildSettings() {
  const body = $('#settings-body');
  body.innerHTML = '';
  const base = () => ({ ...PRESETS[settings.preset], ...settings.colors });
  const group = title => { const g = el('div', 'set-group', `<h4>${title}</h4>`); body.append(g); return g; };

  const g1 = group('Theme');
  const presets = el('div', 'presets');
  for (const [name, p] of Object.entries(PRESETS)) {
    const b = el('button', 'preset' + (settings.preset === name ? ' on' : ''), `<span>${name}</span>`);
    b.style.cssText = `background:${p.bg};color:${p.text};border-color:${p.border}`;
    b.onclick = () => { settings.preset = name; settings.colors = {}; saveSettings(); buildSettings(); };
    presets.append(b);
  }
  g1.append(presets);
  const paperRow = el('label', 'set-row', '<span>Academic paper layout (typeset page, theorem-style boxes)</span>');
  const paperBox = el('input'); paperBox.type = 'checkbox'; paperBox.checked = !!settings.paper;
  paperBox.onchange = () => { settings.paper = paperBox.checked; saveSettings(); };
  paperRow.append(paperBox); g1.append(paperRow);

  const g2 = group('Colours');
  for (const [key, label] of [['bg', 'Background'], ['surface', 'Panels and cards'], ['text', 'Text'], ['muted', 'Secondary text'], ['border', 'Lines']]) {
    const row = el('label', 'set-row', `<span>${label}</span>`);
    const input = el('input'); input.type = 'color'; input.value = base()[key];
    input.oninput = () => { settings.colors[key] = input.value; saveSettings(); };
    row.append(input); g2.append(row);
  }

  const g3 = group('Course colours');
  for (const tab of state.tabs) {
    const row = el('label', 'set-row', `<span>${esc(tab.label)}</span>`);
    const input = el('input'); input.type = 'color'; input.value = accentOf(tab.id);
    input.oninput = () => { settings.accents[tab.id] = input.value; saveSettings(); };
    row.append(input); g3.append(row);
  }

  const g4 = group('Text and maths');
  const fontRow = el('label', 'set-row', '<span>Reading font</span>');
  const select = el('select');
  for (const name of Object.keys(FONTS)) { const o = el('option', '', name); o.selected = settings.font === name; select.append(o); }
  select.onchange = () => { settings.font = select.value; saveSettings(); };
  fontRow.append(select); g4.append(fontRow);
  for (const [key, label, min, max, step, unit] of [['size', 'Text size', 13, 24, 0.5, 'px'], ['math', 'Maths size', 0.9, 1.4, 0.02, '×'], ['width', 'Column width', 560, 1200, 20, 'px']]) {
    const row = el('label', 'set-row', `<span>${label}</span>`);
    const input = el('input'); input.type = 'range'; Object.assign(input, { min, max, step, value: settings[key] });
    const out = el('output', '', settings[key] + unit);
    input.oninput = () => { settings[key] = +input.value; out.textContent = input.value + unit; saveSettings(); };
    row.append(input, out); g4.append(row);
  }

  const g5 = group('Preview');
  const sample = el('div', 'prose', render('Let $f$ be continuous on $[a,b]$. Then\n\n$$\\int_a^b f(x)\\,dx = \\lim_{n\\to\\infty} \\sum_{i=1}^{n} f(x_i^*)\\,\\Delta x.$$\n\n> [!note] Definition\n> A set $U$ is **open** if every $x \\in U$ has $B_\\varepsilon(x) \\subseteq U$.'));
  g5.append(sample); enhance(sample, { diagrams: false });

  const reset = el('button', '', 'Reset to defaults');
  reset.style.marginTop = '22px';
  reset.onclick = () => { settings = structuredClone(DEFAULTS); saveSettings(); buildSettings(); };
  body.append(reset);
}

// ------------------------------------------------------------ state
const state = { tabs: [], config: {}, ready: false, current: 'home', chats: {}, overview: { courses: {}, errors: {} }, usage: { rate: {}, totals: {} }, pane: 'note' };
const chat = id => state.chats[id] ||= { log: el('div', 'log'), busy: false, queue: [], notes: [], active: null, scroll: {}, attachments: [], meta: '', draft: '', abort: null };
const tabOf = id => state.tabs.find(t => t.id === id);

// ------------------------------------------------------------ rail + home
function barHtml(levels = {}, total = 0) {
  if (!total) return '<div class="bar"></div>';
  return '<div class="bar">' + LEVELS.map(l => `<i class="${l}" style="width:${100 * (levels[l] || 0) / total}%" title="${levels[l] || 0} ${l}"></i>`).join('') + '</div>';
}
const startedOf = c => (c.levels ? c.nodes - (c.levels.unseen || 0) : 0);

function renderRail() {
  const box = $('#tabs');
  box.innerHTML = '';
  const add = (id, label, badge) => {
    const b = el('button', 'tab' + (state.current === id ? ' on' : ''), `<span class="dot"></span><span class="label">${esc(label)}</span>`);
    b.dataset.tab = id;
    if (state.chats[id]?.busy) b.append(el('span', 'live'));
    else if (badge) b.append(el('span', 'badge', badge));
    b.onclick = () => show(id);
    box.append(b);
  };
  add('home', 'Home', state.overview.due_total ? `${state.overview.due_total} due` : '');
  box.append(el('div', 'tab-sep'));
  state.tabs.forEach((t, i) => {
    if (!t.course && i) box.append(el('div', 'tab-sep'));
    const due = t.course && state.overview.courses[t.course]?.due;
    add(t.id, t.label, due ? String(due) : '');
  });
  applyTheme();
}

function renderHome() {
  const home = $('#home');
  const o = state.overview;
  const date = new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const page = el('div', 'home-page');
  const courseTabs = state.tabs.filter(t => t.course);
  const summary = !state.ready ? 'Reading your notes…'
    : o.due_total != null ? `${o.due_total} review${o.due_total === 1 ? ' is' : 's are'} due across all courses.`
    : o.loading || !o.built ? 'Reading your notes…' : 'The engine did not report what is due.';
  page.innerHTML = `<h1>Study Desk</h1><div class="sub">${date}</div>
    <p class="abstract"><b>Summary.</b> ${summary}${o.loading && o.due_total != null ? ' Refreshing…' : ''}</p>`;
  const folderError = state.config.error || o.errors.folder;
  if (folderError) page.append(el('p', 'notice', 'The engine could not read this folder: ' + esc(folderError)));
  if (state.ready && !courseTabs.length && !folderError) {
    page.append(el('p', 'notice', `No courses were found in <code>${esc(state.config.folder || '')}</code>. In Claude Code, run <code>/learn:setup</code> in that folder (or <code>/learn:ingest</code> to add a course), then reload this page. The General tab works meanwhile.`));
  }
  if (courseTabs.length) {
    // The Due and Redos columns need the engine's `due`; they are hidden if it gave none.
    const hasDue = o.due_total != null || !o.built;
    const cols = 5 + (hasDue ? 2 : 0);
    const table = el('table', 'modules');
    table.innerHTML = `<thead><tr><th>Course</th><th class="wide">Progress</th><th class="num">Started</th>${hasDue ? '<th class="num">Due</th><th class="num">Redos</th>' : ''}<th class="num">Secure</th><th class="num">Mastered</th></tr></thead>`;
    const body = el('tbody');
    const num = v => v == null ? '' : v;
    for (const t of courseTabs) {
      const c = o.courses[t.course];
      const row = el('tr');
      row.dataset.tab = t.id; row.tabIndex = 0;
      row.innerHTML = `<td class="name"><span class="dot"></span>${esc(t.label)}</td>` + (c
        ? `<td class="wide">${barHtml(c.levels, c.nodes)}</td><td class="num">${startedOf(c)}/${c.nodes}</td>${hasDue ? `<td class="num">${num(c.due)}</td><td class="num">${num(c.redos)}</td>` : ''}<td class="num">${c.levels.secure || 0}</td><td class="num">${c.levels.mastered || 0}</td>`
        : `<td colspan="${cols}" class="muted">${o.errors[t.course] ? esc(o.errors[t.course]) : 'Loading…'}</td>`);
      row.onclick = () => show(t.id);
      row.onkeydown = e => { if (e.key === 'Enter') show(t.id); };
      body.append(row);
    }
    table.append(body); page.append(table);
    page.append(el('div', 'legend', `<span style="--c:var(--learning)">learning</span><span style="--c:var(--secure)">secure</span><span style="--c:var(--mastered)">mastered</span><span style="--c:var(--unseen)">unseen</span>`));
  }
  const s = o.stats;   // shown only when the engine reports retention figures
  if (s && s.attempts) {
    const r = s.reviews && s.reviews.n ? `Spaced reviews passed: ${Math.round(100 * s.reviews.rate)}% (${s.reviews.passed} of ${s.reviews.n}).` : 'No spaced reviews are logged yet, so there is no retention figure.';
    page.append(el('p', 'notice', `${s.attempts} attempts in the log. ${r}`));
  }
  home.replaceChildren(page);
  applyTheme();
}

// The courses may change while the app is open (a new course is ingested): pick up the new tabs.
async function syncTabs() {
  const codes = state.overview.course_codes;
  if (!codes || state.syncing) return;
  const have = state.tabs.filter(t => t.course).map(t => t.course);
  if (state.ready && codes.length === have.length && codes.every((c, i) => c === have[i])) return;
  state.syncing = true;
  try {
    const cfg = await (await api('/api/config')).json();
    state.config = cfg; state.tabs = cfg.tabs; state.ready = cfg.ready;
    if (state.current !== 'home' && !tabOf(state.current)) show('home');
  } catch (e) { /* keep the tabs we have */ }
  state.syncing = false;
}

async function loadOverview(refresh = false) {
  try {
    state.overview = await (await api('/api/overview' + (refresh ? '?refresh=1' : ''))).json();
  } catch (e) { return; }
  await syncTabs();
  renderRail();
  if (state.current === 'home') renderHome(); else { renderHead(); renderSidePanes(); }
  if (state.overview.loading) setTimeout(loadOverview, 2500);
}

// ------------------------------------------------------------ desk
function show(id) {
  if (state.current !== 'home') { const old = chat(state.current); old.draft = $('#input').value; old.scroll[old.active ?? 'tutor'] = $('#desk').scrollTop; }
  state.current = id;
  history.replaceState(null, '', id === 'home' ? '#' : '#' + encodeURIComponent(id));
  $('#home').hidden = id !== 'home';
  $('#desk').hidden = id === 'home';
  if (id === 'home') { $('#side').hidden = true; renderHome(); if (state.stale) { state.stale = false; loadOverview(true); } }
  else {
    const c = chat(id);
    $('#chat-inner').replaceChildren(c.log);
    if (!c.log.children.length) c.log.append(emptyState(tabOf(id)));
    $('#input').value = c.draft; autosize();
    renderHead(); renderAttachments(); renderBusy(); renderSidePanes();
    activate(c.active != null && c.notes[c.active] ? c.active : null, false);
  }
  renderRail();
}

function emptyState(tab) {
  return el('div', 'empty', `${esc(tab.label)}<small>${tab.course ? `Type /learn:teach ${esc(tab.course)} next, /learn:quiz ${esc(tab.course)}, or just ask.` : esc(tab.title || 'Type anything.')}</small>`);
}

function renderHead() {}

function renderBusy() {
  const c = chat(state.current);
  $('#turn-meta').textContent = c.meta || (c.busy ? '' : hintFor(tabOf(state.current)));
  $('#composer').classList.toggle('busy', c.busy);
  if (state.current !== 'home') renderStrip();
}
const hintFor = tab => tab ? (tab.course ? `/learn:teach ${tab.course} next · /learn:quiz ${tab.course} · /clear · About for more` : '/learn:quiz mixed · /learn:primer week · /clear · About for more') : '';

function autosize() { const t = $('#input'); t.style.height = 'auto'; t.style.height = Math.min(t.scrollHeight + 2, innerHeight * 0.4) + 'px'; }

// ------------------------------------------------------------ attachments
async function attach(files) {
  const c = chat(state.current);
  for (const file of files) {
    if (!/^image\/(png|jpeg|webp|gif)$/.test(file.type)) continue;
    const res = await api('/api/upload', { method: 'POST', headers: { 'Content-Type': file.type }, body: file });
    if (!res.ok) { c.meta = 'Could not attach that image.'; renderBusy(); continue; }
    c.attachments.push({ path: (await res.json()).path, url: URL.createObjectURL(file) });
  }
  renderAttachments();
}
function renderAttachments() {
  const c = chat(state.current), box = $('#attachments');
  box.innerHTML = '';
  c.attachments.forEach((a, i) => {
    const d = el('div', 'att', `<img src="${a.url}" alt="attached working">`);
    const x = el('button', '', '✕'); x.onclick = () => { c.attachments.splice(i, 1); renderAttachments(); };
    d.append(x); box.append(d);
  });
}

// ------------------------------------------------------------ chat
const fmt = n => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'k' : String(n);

// Prompt history per tab, like the terminal's up arrow. Kept in this browser
// (localStorage), so it survives F5 and a server restart; the conversation does not.
const HIST_MAX = 10, histKey = id => 'studydesk.history.' + id;
function loadHist(id) {
  try { const h = JSON.parse(localStorage.getItem(histKey(id)) || '[]'); return Array.isArray(h) ? h : []; } catch { return []; }
}
function remember(id, text) {
  const h = loadHist(id).filter(t => t !== text); h.push(text);
  try { localStorage.setItem(histKey(id), JSON.stringify(h.slice(-HIST_MAX))); } catch { /* history is a convenience */ }
  chat(id).histAt = null;
}
function recall(dir) {   // -1 older, +1 newer; true when the key was used
  const id = state.current, box = $('#input');
  if (id === 'home') return false;
  const c = chat(id), h = loadHist(id);
  if (!h.length) return false;
  if (c.histAt == null) { if (dir > 0) return false; c.histDraft = box.value; c.histAt = h.length; }
  const at = c.histAt + dir;
  if (at < 0) return true;
  if (at >= h.length) { c.histAt = null; box.value = c.histDraft || ''; }
  else { c.histAt = at; box.value = h[at]; }
  autosize(); box.setSelectionRange(box.value.length, box.value.length);
  return true;
}

async function send(text, queued) {
  const id = queued ? queued.id : state.current, c = chat(id);
  text = (text ?? $('#input').value).trim();
  if (!text && !c.attachments.length) return;
  if (!queued && text) remember(id, text);
  if (c.busy) {   // queue it, as the terminal does: it is sent when the current reply ends
    if (text.startsWith('/')) return;
    const item = { text, images: c.attachments.splice(0), row: el('div', 'msg user queued') };
    const b = el('div', 'bubble'); b.textContent = text; item.row.append(b);
    c.queue.push(item); c.log.append(item.row);
    $('#input').value = ''; autosize(); renderAttachments();
    $('#desk').scrollTop = $('#desk').scrollHeight;
    return;
  }
  if (localCommand(text, c)) { $('#input').value = ''; autosize(); return; }
  if (text === '/clear' || text === '/new') {
    await api(tabUrl(id) + '/reset', { method: 'POST' });
    c.log.replaceChildren(emptyState(tabOf(id))); c.meta = ''; c.attachments = [];
    $('#input').value = ''; autosize(); renderAttachments(); renderBusy();
    return;
  }
  if (!text) text = 'Here is my working.';
  const images = queued ? queued.images : c.attachments.splice(0);
  if (text === $('#input').value.trim()) { $('#input').value = ''; autosize(); }
  renderAttachments();
  c.log.querySelector('.empty')?.remove();

  const user = el('div', 'msg user');
  const bubble = el('div', 'bubble'); bubble.textContent = text;
  for (const a of images) { const img = el('img'); img.src = a.url; bubble.append(img); }
  user.append(bubble); c.log.append(user);

  const msg = el('div', 'msg assistant');
  const activity = el('details', 'activity'); activity.hidden = true; activity.append(el('summary', '', 'Working…'));
  const prose = el('div', 'prose cursor');
  msg.append(activity, prose); c.log.append(msg);
  const scroller = $('#desk');
  const follow = () => { if (state.current === id && c.active == null) scroller.scrollTop = scroller.scrollHeight; };
  follow();

  c.busy = true; c.meta = '✻ Thinking… 0s · esc to interrupt'; c.abort = new AbortController();
  renderBusy(); renderRail();
  let buffer = '', pending = false, tools = 0;
  // Timing, as the terminal shows it: live elapsed time, then "Thought for Ns".
  const started = Date.now();
  let phase = 'thinking', phaseAt = started, thoughtMs = 0, thinkTokens = 0;
  const secs = ms => { const t = Math.round(ms / 1000); return t >= 60 ? `${Math.floor(t / 60)}m ${t % 60}s` : `${t}s`; };
  const thought = el('div', 'thought'); thought.hidden = true; msg.prepend(thought);
  const setPhase = next => {
    if (phase === 'thinking') thoughtMs += Date.now() - phaseAt;
    phase = next; phaseAt = Date.now();
    if (next !== 'thinking' && thoughtMs >= 1000) { thought.hidden = false; thought.textContent = `✻ Thought for ${secs(thoughtMs)}`; }
  };
  const tick = () => {
    const label = { thinking: 'Thinking…', writing: 'Writing…', working: 'Working…' }[phase];
    const thinking = phase === 'thinking' && thinkTokens ? ` · ${fmt(thinkTokens)} thinking tokens` : '';
    c.meta = `✻ ${label} ${secs(Date.now() - started)}${thinking} · esc to interrupt`;
    if (state.current === id) renderBusy();
  };
  const timer = setInterval(tick, 1000);
  const paint = () => {
    pending = false;
    const near = scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 140;
    prose.innerHTML = render(buffer);
    enhance(prose, { diagrams: false });
    if (near) follow();
  };
  const handle = ev => {
    if (ev.t === 'phase') { setPhase(ev.p); tick(); }
    else if (ev.t === 'thinking') { thinkTokens = ev.tokens; }
    else if (ev.t === 'text') { buffer += ev.d; if (!pending) { pending = true; setTimeout(paint, 70); } }
    else if (ev.t === 'tool') {
      tools++; activity.hidden = false; activity.open = true;
      activity.querySelector('summary').textContent = `${ev.summary}  (${tools} step${tools > 1 ? 's' : ''})`;
      const line = el('div'); line.textContent = ev.summary; activity.append(line);
    }
    else if (ev.t === 'rate') { state.usage.rate = ev.info; renderUsage(); }
    else if (ev.t === 'done') {
      setPhase('done');
      c.meta = `✻ ${secs(Date.now() - started)}${thoughtMs >= 1000 ? ` · thought ${secs(thoughtMs)}` : ''} · reply ${fmt(ev.output_tokens)} tokens · context ${fmt(ev.context_tokens)}`;
      if (ev.error && !buffer) fail(ev.error);
    }
    else if (ev.t === 'error') fail(ev.msg);
  };
  const fail = text => { msg.classList.add('error'); buffer += (buffer ? '\n\n' : '') + text; c.meta = ''; };

  try {
    const res = await api(tabUrl(id), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, images: images.map(a => a.path), model: settings.model || '', effort: settings.effort || '' }), signal: c.abort.signal });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
    const reader = res.body.getReader(), dec = new TextDecoder();
    let carry = '';
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      carry += dec.decode(value, { stream: true });
      let cut;
      while ((cut = carry.indexOf('\n\n')) >= 0) {
        const line = carry.slice(0, cut); carry = carry.slice(cut + 2);
        if (line.startsWith('data: ')) handle(JSON.parse(line.slice(6)));
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') fail(e instanceof TypeError ? 'The Study Desk server is not running. Start it again (/learn:app in Claude Code, or the desktop shortcut), then reload this page.' : String(e.message || e));
  }
  clearInterval(timer);
  activity.open = false;
  if (phase !== 'done') setPhase('done');
  if (c.stopped) { c.meta = `Stopped after ${secs(Date.now() - started)}.`; c.stopped = false; }
  c.busy = false; c.abort = null;
  prose.classList.remove('cursor');
  prose.innerHTML = render(buffer || '*(no reply)*');
  await enhance(prose);
  if (state.current === id) { renderBusy(); follow(); }
  renderRail();
  state.stale = true;  // refreshed when Home is next opened: engine calls are slow and would compete with the tutor
  const next = c.queue.shift();
  if (next) { next.row.remove(); send(next.text, { id, images: next.images }); }
}

async function stop() {
  const id = state.current, c = chat(id);
  await api(tabUrl(id) + '/stop', { method: 'POST' });
  // Stopping hands control back: queued messages return to the prompt instead of being sent.
  if (c.queue.length) {
    $('#input').value = [...c.queue.map(q => q.text), $('#input').value].filter(Boolean).join(String.fromCharCode(10));
    c.queue.forEach(q => q.row.remove()); c.queue = []; autosize();
  }
  c.stopped = true; c.abort?.abort();
}

// ------------------------------------------------------------ side panel
// ---- tabs: the tutor first, then every opened note, grouped under the course ----
async function openNote(name, { side = false } = {}) {
  if (side) return openNoteSide(name);
  const id = state.current, c = chat(id), tab = tabOf(id);
  const q = new URLSearchParams({ name }); if (tab?.course) q.set('course', tab.course);
  const res = await api('/api/note?' + q);
  if (!res.ok) { localNote(c, `No note called "${name}" in your notes.`); return; }
  const note = await res.json();
  let i = c.notes.findIndex(n => n.path === note.path);
  if (i < 0) { c.notes.push(note); i = c.notes.length - 1; } else c.notes[i] = note;   // reopen = refresh from disk
  if (state.current === id) activate(i);
}
function activate(i, save = true) {
  const c = chat(state.current);
  if (save) c.scroll[c.active ?? 'tutor'] = $('#desk').scrollTop;
  c.active = i;
  const note = i == null ? null : c.notes[i];
  $('#chat').hidden = !!note; $('#composer').hidden = !!note; $('#noteview').hidden = !note;
  if (note) {
    const box = $('#noteview-inner');
    box.innerHTML = `<div class="path">${esc(note.path)}</div>`;
    const prose = el('div', 'prose', render(note.markdown, { note: true }));
    if (prose.firstElementChild?.tagName !== 'H1') box.append(el('h1', 'note-title', esc(note.name)));
    box.append(prose); enhance(prose);
  }
  renderStrip();
  $('#desk').scrollTop = c.scroll[i ?? 'tutor'] ?? (note ? 0 : $('#desk').scrollHeight);
  if (!note) $('#input').focus();
}
function closeNote(i) {
  const c = chat(state.current);
  c.notes.splice(i, 1); c.scroll = { tutor: c.scroll.tutor };
  const next = c.active == null ? null : c.active === i ? (c.notes.length ? Math.min(i, c.notes.length - 1) : null) : c.active > i ? c.active - 1 : c.active;
  c.active = null; activate(next, false);
}
function renderStrip() {
  const tab = tabOf(state.current), c = chat(state.current), strip = $('#tabstrip');
  strip.hidden = !c.notes.length;
  if (!c.notes.length) return;
  strip.replaceChildren(el('span', 'group', esc(tab.label)));
  const add = (label, i) => {
    const b = el('button', 'ptab' + (c.active === i ? ' on' : ''), `<span>${esc(label)}</span>`);
    b.onclick = () => activate(i);
    if (i != null) {
      const x = el('i', '', '×'); x.title = 'Close tab';
      x.onclick = e => { e.stopPropagation(); closeNote(i); };
      b.append(x);
      b.onauxclick = e => { if (e.button === 1) { e.preventDefault(); closeNote(i); } };
    }
    strip.append(b);
  };
  add(c.busy ? 'Tutor …' : 'Tutor', null);
  c.notes.forEach((n, i) => add(n.name, i));
}
async function openNoteSide(name) {
  const tab = tabOf(state.current);
  $('#side').hidden = false; setPane('note');
  const pane = $('#pane-note');
  pane.innerHTML = '<p class="muted">Loading…</p>';
  const q = new URLSearchParams({ name }); if (tab?.course) q.set('course', tab.course);
  const res = await api('/api/note?' + q);
  if (!res.ok) { pane.innerHTML = `<p class="muted">No note called “${esc(name)}” in your notes.</p>`; return; }
  const note = await res.json();
  pane.innerHTML = `<h1 class="note-title">${esc(note.name)}</h1><div class="path">${esc(note.path)}</div>`;
  const prose = el('div', 'prose', render(note.markdown, { note: true }));
  if (prose.firstElementChild?.tagName === 'H1') pane.querySelector('.note-title').remove();
  pane.append(prose); pane.scrollTop = 0;
  enhance(prose);
}
function setPane(name) {
  state.pane = name;
  for (const b of document.querySelectorAll('.side-tabs button')) b.classList.toggle('on', b.dataset.pane === name);
  for (const p of ['note', 'units', 'due']) $('#pane-' + p).hidden = p !== name;
}
function renderSidePanes() {
  const tab = tabOf(state.current);
  const c = tab?.course && state.overview.courses[tab.course];
  const units = $('#pane-units'), due = $('#pane-due');
  units.innerHTML = ''; due.innerHTML = '';
  if (!c) {
    const text = tab?.course ? (state.overview.errors[tab.course] || 'Loading…') : 'This tab has no course.';
    units.innerHTML = due.innerHTML = `<p class="muted">${esc(text)}</p>`; return;
  }
  if (!c.units) units.innerHTML = '<p class="muted">The engine did not report units for this course.</p>';
  for (const u of c.units || []) {
    const done = u.nodes - (u.levels.unseen || 0);
    const row = el('div', 'unit', `<div class="unit-top"><b>${esc(u.name)}</b><span>${done}/${u.nodes}${u.started ? '' : ' · not started'}</span></div><div class="title">${esc(u.title)}</div>${barHtml(u.levels, u.nodes)}`);
    if (u.primer) { const a = el('a', '', 'Overview'); a.style.cssText = 'display:inline-block;margin-top:7px'; a.onclick = () => openNote(u.primer); row.append(a); }
    units.append(row);
  }
  if (c.due == null) { due.innerHTML = '<p class="muted">The engine did not report what is due.</p>'; return; }
  if (!c.due_items.length) { due.innerHTML = '<p class="muted">Nothing due in this course.</p>'; return; }
  due.append(el('div', 'warn', `${c.due} due, most overdue first. Opening a note shows the answer: quiz first.`));
  for (const d of c.due_items) {
    const row = el('div', 'due-item', `${esc(d.name)}<span>${d.overdue_days ? d.overdue_days + 'd overdue' : 'today'}</span>`);
    row.onclick = () => openNote(d.name);
    due.append(row);
  }
}

// ------------------------------------------------------------ usage
function renderUsage() {
  const w = state.usage.rate?.unifiedWindows, box = $('#usage'), line = $('#status-usage');
  if (!w) { box.innerHTML = '<div>Limits show after the first reply</div>'; line.textContent = ''; return; }
  box.innerHTML = '';
  const parts = [];
  for (const [key, label, short] of [['five_hour', '5-hour limit', '5h'], ['seven_day', 'Weekly limit', 'week']]) {
    if (!w[key]) continue;
    const pct = Math.round(100 * w[key].utilization);
    const reset = new Date(w[key].resetsAt * 1000).toLocaleString(undefined, { weekday: 'short', hour: '2-digit', minute: '2-digit' });
    const d = el('div', '', `<div class="meter-row"><span>${label}</span><span>${pct}%</span></div><div class="meter${pct >= 80 ? ' hot' : ''}"><i style="width:${Math.min(pct, 100)}%"></i></div>`);
    d.title = `Resets ${reset}`;
    box.append(d);
    parts.push(`${short} ${pct}%`);
    w[key].resetText = reset;
  }
  line.textContent = parts.join(' · ');
}

const MODELS = ['default', 'fable', 'opus', 'sonnet', 'haiku'];
const EFFORTS = ['default', 'low', 'medium', 'high', 'xhigh', 'max'];
function buildStatus() {
  for (const [id, list, key] of [['#sel-model', MODELS, 'model'], ['#sel-effort', EFFORTS, 'effort']]) {
    const sel = $(id);
    sel.replaceChildren(...list.map(v => { const o = el('option', '', v); o.value = v === 'default' ? '' : v; return o; }));
    sel.value = settings[key] || '';
    sel.onchange = () => { settings[key] = sel.value; saveSettings(); $('#input').focus(); };
  }
}
function localNote(c, text) {
  c.log.querySelector('.empty')?.remove();
  c.log.append(el('div', 'msg note', esc(text)));
  $('#desk').scrollTop = $('#desk').scrollHeight;
}
// Commands the app answers itself, as the terminal does. Returns true when handled.
function localCommand(text, c) {
  const [cmd, arg = ''] = text.split(/\s+/);
  if (cmd === '/model' || cmd === '/effort') {
    const key = cmd.slice(1), list = key === 'model' ? MODELS : EFFORTS;
    if (!list.includes(arg)) localNote(c, `${cmd}: choose one of ${list.join(', ')}. Now: ${settings[key] || 'default'}.`);
    else { settings[key] = arg === 'default' ? '' : arg; saveSettings(); buildStatus(); localNote(c, `${key} set to ${arg} for the next message.`); }
    return true;
  }
  if (cmd === '/usage') {
    const w = state.usage.rate?.unifiedWindows;
    if (!w) localNote(c, 'No limits reported yet: they arrive with the first reply.');
    else localNote(c, [['five_hour', '5-hour limit'], ['seven_day', 'Weekly limit']].filter(([k]) => w[k]).map(([k, label]) => `${label}: ${Math.round(100 * w[k].utilization)}% used, resets ${w[k].resetText}`).join('\n'));
    return true;
  }
  return false;
}

// ------------------------------------------------------------ wiring
$('#input').addEventListener('input', autosize);
$('#input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); return; }
  // Up on the first line and Down on the last line walk this tab's past prompts, as in the terminal.
  if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey && !e.isComposing) {
    const box = e.target, v = box.value;
    if (box.selectionStart !== box.selectionEnd) return;
    const edge = e.key === 'ArrowUp' ? v.lastIndexOf('\n', box.selectionStart - 1) === -1 : v.indexOf('\n', box.selectionEnd) === -1;
    if (edge && recall(e.key === 'ArrowUp' ? -1 : 1)) e.preventDefault();
  }
});
$('#input').addEventListener('paste', e => { const f = [...e.clipboardData.files]; if (f.length) { e.preventDefault(); attach(f); } });
$('#file').onchange = e => { attach([...e.target.files]); e.target.value = ''; };
addEventListener('dragover', e => { if (state.current !== 'home') { e.preventDefault(); document.body.classList.add('dragging'); } });
addEventListener('dragleave', () => document.body.classList.remove('dragging'));
addEventListener('drop', e => { document.body.classList.remove('dragging'); if (state.current !== 'home') { e.preventDefault(); attach([...e.dataTransfer.files]); } });
document.addEventListener('click', e => {
  if (state.current === 'home') return;
  const a = e.target.closest('a.wl');
  if (a) { e.preventDefault(); openNote(a.dataset.note, { side: e.shiftKey }); return; }
  const link = e.target.closest('.prose a[href]');
  const href = link?.getAttribute('href') || '';
  if (/^[a-z][a-z0-9+.-]*:/i.test(href) || !/\.md(#.*)?$/i.test(href)) return;
  e.preventDefault();
  let target = href.replace(/#.*$/, '').replace(/^(\.{1,2}\/)+/, '');
  try { target = decodeURIComponent(target); } catch (err) { /* keep it as written */ }
  openNote(target, { side: e.shiftKey });
});
document.querySelectorAll('.side-tabs button').forEach(b => b.onclick = () => setPane(b.dataset.pane));
$('#side-close').onclick = () => { $('#side').hidden = true; };
$('#btn-settings').onclick = () => { buildSettings(); $('#settings').hidden = false; };
$('#settings-close').onclick = () => { $('#settings').hidden = true; };
$('#settings').addEventListener('click', e => { if (e.target.id === 'settings') $('#settings').hidden = true; });
$('#btn-full').onclick = () => document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
addEventListener('keydown', e => {
  if (e.key === 'F11') { e.preventDefault(); $('#btn-full').click(); return; }  // page fullscreen, so Esc leaves it
  if (e.key === 'Escape') {
    if (!$('#settings').hidden || !$('#about').hidden) { $('#settings').hidden = true; $('#about').hidden = true; }
    else if (state.current !== 'home' && chat(state.current).busy) stop();
    else $('#side').hidden = true;
  }
  if (e.altKey && !e.ctrlKey && state.current !== 'home') {   // tab keys (Ctrl+W and Ctrl+Tab belong to the window)
    const c = chat(state.current), order = [null, ...c.notes.keys()], at = order.indexOf(c.active);
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); activate(order[(at + (e.key === 'ArrowRight' ? 1 : order.length - 1)) % order.length]); }
    else if (e.key.toLowerCase() === 'w' && c.active != null) { e.preventDefault(); closeNote(c.active); }
  }
  if (e.ctrlKey && !e.shiftKey && !e.altKey) {
    if (e.key === '0') { e.preventDefault(); show('home'); }
    else if (/^[1-9]$/.test(e.key) && state.tabs[+e.key - 1]) { e.preventDefault(); show(state.tabs[+e.key - 1].id); }
    else if (e.key === 'b') { e.preventDefault(); setRail(!settings.railHidden); }
    else if (e.key === '.' && state.current !== 'home') { e.preventDefault(); $('#side').hidden = !$('#side').hidden; }
  }
});

function setRail(hidden) {
  settings.railHidden = hidden;
  document.body.classList.toggle('no-rail', hidden);
  $('#rail-show').hidden = !hidden;
  saveSettings();
}
$('#rail-hide').onclick = () => setRail(true);
$('#rail-show').onclick = () => setRail(false);
$('#btn-about').onclick = () => { $('#about').hidden = false; };
$('#about-close').onclick = () => { $('#about').hidden = true; };
$('#about').addEventListener('click', e => { if (e.target.id === 'about') $('#about').hidden = true; });

(async function init() {
  const [cfg, saved, usage] = await Promise.all([api('/api/config'), api('/api/settings'), api('/api/usage')].map(p => p.then(r => r.json())));
  state.config = cfg; state.tabs = cfg.tabs; state.ready = cfg.ready;
  $('#about-folder').textContent = cfg.library ? `${cfg.library} (your notes, read-only) with its review cards in ${cfg.root}` : cfg.root;
  $('#about-port').textContent = cfg.port;
  $('#about-mode').textContent = cfg.permission_mode;
  $('#about-data').textContent = cfg.data;
  settings = { ...structuredClone(DEFAULTS), ...saved, colors: { ...saved.colors }, accents: { ...saved.accents } };
  state.usage = usage;
  renderRail(); renderHome(); renderUsage(); buildStatus(); applyTheme();
  if (settings.railHidden) { document.body.classList.add('no-rail'); $('#rail-show').hidden = false; }
  const [hashTab, hashNote] = location.hash.slice(1).split('/').map(decodeURIComponent);
  if (tabOf(hashTab)) { show(hashTab); if (hashNote) openNote(hashNote); }
  if (location.search === '?demo' && state.current !== 'home') {  // style check without spending a turn
    const c = chat(state.current); c.log.innerHTML = '';
    const u = el('div', 'msg user'); const b = el('div', 'bubble'); b.textContent = 'B, because every point of the ball has room around it.'; u.append(b);
    const a = el('div', 'msg assistant'); const p = el('div', 'prose', render('## 1 Open sets\n\nRight. Let $(X,d)$ be a metric space; recall the open ball $B_r(x)=\\{y\\in X : d(x,y)<r\\}$, see [[Open Ball]].\n\n> [!note] Definition 1.2\n> A set $U\\subseteq X$ is **open** if for every $x\\in U$ there is $\\varepsilon>0$ with $B_\\varepsilon(x)\\subseteq U$.\n\n> [!note] Theorem 1.3\n> Every open ball is open. Moreover, for $y\\in B_r(x)$,\n> $$B_{r-d(x,y)}(y)\\subseteq B_r(x).$$\n\n| Set | Open in $\\mathbb{R}$? |\n|---|---|\n| $(0,1)$ | yes |\n| $[0,1)$ | no |\n\n**Question.** Which step of the proof uses the triangle inequality?\n\nA. Choosing $\\varepsilon$\n\nB. Showing $d(x,z)<r$\n\nConfidence 1 to 5?'));
    a.append(p); c.log.append(u, a); enhance(p);
  }
  loadOverview();
  // Windows only: an app window resets its icon when the page loads, so ask for the sharp one afterwards.
  for (const delay of [800, 3000]) setTimeout(() => api('/api/window-icon', { method: 'POST' }).catch(() => {}), delay);
})();
