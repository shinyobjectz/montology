"""The phase spec and the form it becomes.

A phase is JSON the agent writes: a slug, a title, an intro, and an ordered
list of questions. `validate_spec` says exactly what is wrong and how to
fix it (the person answering never sees this — the agent does, and repairs).
`render_form` turns a valid spec into one self-contained HTML page: one
question per screen, keyboard-first, no external assets.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

# Tests pin INTAKE_DIR directly; when None it resolves from the workspace marker.
INTAKE_DIR: Path | None = None

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
TYPES = ("text", "long", "url", "email", "number", "choice", "multi", "scale", "yesno")
NEEDS_OPTIONS = ("choice", "multi")


def validate_spec(spec: dict) -> list[str]:
    """Problems with a phase spec, each stated with its repair; [] = valid."""
    out: list[str] = []
    if not isinstance(spec, dict):
        return ["the spec must be a JSON object: {phase, title, questions: [...]}"]
    phase = str(spec.get("phase", ""))
    if not SLUG_RE.match(phase):
        out.append(f"phase {phase!r} must be a slug like 'brand' or '2-market' (lowercase, digits, dashes)")
    if not str(spec.get("title", "")).strip():
        out.append("title is missing — the marketer needs to know what this round is about")
    qs = spec.get("questions")
    if not isinstance(qs, list) or not qs:
        return out + ["questions must be a non-empty list"]
    seen: set[str] = set()
    for i, q in enumerate(qs):
        where = f"questions[{i}]"
        if not isinstance(q, dict):
            out.append(f"{where} must be an object")
            continue
        qid = str(q.get("id", ""))
        if not ID_RE.match(qid):
            out.append(f"{where}.id {qid!r} must be snake_case (it becomes the answer key)")
        elif qid in seen:
            out.append(f"{where}.id {qid!r} is used twice — every answer key is unique")
        seen.add(qid)
        if not str(q.get("label", "")).strip():
            out.append(f"{where}.label is missing — that is the question itself")
        t = str(q.get("type", "text"))
        if t not in TYPES:
            out.append(f"{where}.type {t!r} is not one of {', '.join(TYPES)}")
        if t in NEEDS_OPTIONS:
            opts = q.get("options")
            if not isinstance(opts, list) or len(opts) < 2 or not all(isinstance(o, str) and o.strip() for o in opts):
                out.append(f"{where} is a {t} question and needs options: [\"a\", \"b\", ...] (2+ strings)")
        if t == "scale":
            lo, hi = q.get("min", 1), q.get("max", 5)
            if not (isinstance(lo, int) and isinstance(hi, int) and 1 <= hi - lo <= 10):
                out.append(f"{where} scale needs integer min/max with 2..11 steps (default 1..5)")
    return out


def load_spec(source: str) -> dict:
    """A spec from a JSON string, a path, or '-' for stdin."""
    if source == "-":
        import sys

        return json.loads(sys.stdin.read())
    p = Path(source)
    if p.exists():
        return json.loads(p.read_text())
    return json.loads(source)


def intake_dir() -> Path:
    """<workspace>/.monty/answers — beside the ontology the answers feed."""
    if INTAKE_DIR is not None:
        return INTAKE_DIR
    from montology_core import workspace_root

    return workspace_root() / ".monty" / "answers"


def workspace_name() -> str:
    if INTAKE_DIR is not None:
        return INTAKE_DIR.parents[1].name if len(INTAKE_DIR.parents) > 1 else "workspace"
    from montology_core import workspace_root

    return workspace_root().name


# ── the page ────────────────────────────────────────────────────────────────

def render_form(spec: dict, workspace: str, *, post_to: str = "/answers") -> str:
    """The typeform-style page for one phase. All CSS/JS inline; the spec is
    embedded as JSON and the page builds itself from it."""
    problems = validate_spec(spec)
    if problems:
        raise ValueError("; ".join(problems))
    payload = json.dumps({"project": workspace, "spec": spec, "post_to": post_to}) \
        .replace("</", "<\\/")
    title = html.escape(str(spec["title"]))
    return _PAGE.replace("__TITLE__", title).replace("__PAYLOAD__", payload)


_PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{
  --bg:#fafaf8; --fg:#16161a; --muted:#6b6b74; --line:#e4e3df; --accent:#2f5bea; --accent-ink:#fff;
  --card:#fff; --soft:#eef1fb; --ok:#1f8f5f; --err:#c23d3d; --radius:14px;
  --font:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#111114; --fg:#f2f2f4; --muted:#9a9aa6; --line:#2a2a31; --accent:#7b95ff; --accent-ink:#0d1230;
  --card:#18181d; --soft:#1d2238;
}}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font-family:var(--font);-webkit-font-smoothing:antialiased}
body{display:flex;flex-direction:column;min-height:100vh}
.bar{position:fixed;inset:0 0 auto 0;height:4px;background:var(--line)}
.bar i{display:block;height:100%;width:0;background:var(--accent);transition:width .35s cubic-bezier(.4,0,.2,1)}
header{padding:28px clamp(20px,6vw,72px) 0;display:flex;justify-content:space-between;align-items:center;font-size:13px;color:var(--muted)}
header b{color:var(--fg);font-weight:600}
main{flex:1;display:flex;align-items:center;padding:40px clamp(20px,6vw,72px)}
.screen{width:100%;max-width:760px;margin:0 auto;opacity:0;transform:translateY(18px);animation:in .38s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes in{to{opacity:1;transform:none}}
.num{color:var(--accent);font-size:14px;font-weight:600;letter-spacing:.02em;margin-bottom:12px}
h1{font-size:clamp(22px,3.2vw,34px);line-height:1.2;font-weight:600;margin:0 0 10px;letter-spacing:-.01em}
h1.intro{font-size:clamp(28px,4.2vw,44px)}
.help{color:var(--muted);font-size:16px;line-height:1.5;margin:0 0 28px;max-width:60ch}
input[type=text],input[type=url],input[type=email],input[type=number],textarea{
  width:100%;font:inherit;font-size:clamp(18px,2.2vw,24px);color:var(--fg);background:transparent;border:0;border-bottom:2px solid var(--line);padding:10px 0;outline:0;transition:border-color .2s}
input:focus,textarea:focus{border-color:var(--accent)}
textarea{resize:vertical;min-height:96px;line-height:1.45}
.opts{display:grid;gap:10px;max-width:520px}
.opt{display:flex;align-items:center;gap:14px;padding:13px 16px;border:1.5px solid var(--line);border-radius:var(--radius);background:var(--card);cursor:pointer;font-size:17px;transition:border-color .15s,background .15s,transform .1s;user-select:none}
.opt:hover{border-color:var(--accent)}
.opt.on{border-color:var(--accent);background:var(--soft)}
.opt:active{transform:scale(.99)}
.key{display:inline-grid;place-items:center;min-width:26px;height:26px;border:1.5px solid var(--line);border-radius:7px;font-size:12px;font-weight:600;color:var(--muted)}
.opt.on .key{border-color:var(--accent);color:var(--accent)}
.scale{display:flex;gap:8px;flex-wrap:wrap}
.scale .opt{justify-content:center;min-width:56px;padding:14px 0;font-weight:600}
.ends{display:flex;justify-content:space-between;max-width:520px;color:var(--muted);font-size:13px;margin-top:10px}
.row{display:flex;align-items:center;gap:14px;margin-top:30px}
button{font:inherit;font-size:16px;font-weight:600;border:0;border-radius:11px;padding:12px 22px;cursor:pointer;background:var(--accent);color:var(--accent-ink);transition:transform .1s,opacity .2s}
button:active{transform:scale(.98)}
button.ghost{background:transparent;color:var(--muted);padding:12px 8px}
button[disabled]{opacity:.45;cursor:not-allowed}
.hint{color:var(--muted);font-size:13px}
.hint kbd{font:inherit;font-weight:600;color:var(--fg)}
.err{color:var(--err);font-size:14px;margin-top:10px;min-height:18px}
.review{display:grid;gap:14px;margin:0 0 8px}
.review div{padding:14px 16px;border:1.5px solid var(--line);border-radius:var(--radius);background:var(--card);cursor:pointer}
.review div:hover{border-color:var(--accent)}
.review small{display:block;color:var(--muted);font-size:13px;margin-bottom:4px}
.done{text-align:center}
.done .tick{width:64px;height:64px;border-radius:50%;background:var(--ok);color:#fff;display:grid;place-items:center;margin:0 auto 20px;font-size:30px}
footer{padding:0 clamp(20px,6vw,72px) 24px;display:flex;gap:8px;justify-content:flex-end}
footer button{padding:8px 12px;background:var(--card);color:var(--fg);border:1.5px solid var(--line)}
pre{white-space:pre-wrap;word-break:break-word;font-size:13px;background:var(--card);border:1.5px solid var(--line);border-radius:var(--radius);padding:14px;text-align:left;max-height:40vh;overflow:auto}
</style>
</head>
<body>
<div class="bar"><i id="bar"></i></div>
<header><span><b id="hTitle"></b></span><span id="hStep"></span></header>
<main><div id="root"></div></main>
<footer><button id="prev" title="previous">↑</button><button id="next" title="next">↓</button></footer>
<script>
const DATA = __PAYLOAD__;
const SPEC = DATA.spec, Q = SPEC.questions, A = {};
let i = -1;  // -1 intro, 0..n-1 questions, n review, n+1 done
const root = document.getElementById('root');
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
document.getElementById('hTitle').textContent = SPEC.title;

function val(q){ return A[q.id]; }
function filled(q){
  const v = val(q);
  if (q.type === 'multi') return Array.isArray(v) && v.length > 0;
  return v !== undefined && v !== null && String(v).trim() !== '';
}
function progress(){
  const n = Q.length, done = Q.filter(filled).length;
  document.getElementById('bar').style.width = (i < 0 ? 0 : Math.min(100, Math.round(100 * (i >= n ? n : done) / n))) + '%';
  document.getElementById('hStep').textContent = i >= 0 && i < n ? `${i + 1} / ${n}` : (i >= n ? 'review' : '');
  document.getElementById('prev').disabled = i <= -1 || i > Q.length;
  document.getElementById('next').disabled = i >= Q.length;
}
function show(){
  progress();
  root.className = 'screen'; root.style.animation = 'none'; void root.offsetWidth; root.style.animation = '';
  if (i < 0) return intro();
  if (i === Q.length) return review();
  if (i > Q.length) return done();
  question(Q[i]);
}
function intro(){
  root.innerHTML = `<div class="num">${esc(DATA.project)} · ${Q.length} question${Q.length === 1 ? '' : 's'}</div>
    <h1 class="intro">${esc(SPEC.title)}</h1>
    <p class="help">${esc(SPEC.intro || 'A few questions so the work that follows is built on what you actually mean.')}</p>
    <div class="row"><button id="go">Start</button><span class="hint">press <kbd>Enter ↵</kbd></span></div>`;
  document.getElementById('go').onclick = () => go(1);
}
function question(q){
  const req = q.required !== false;
  let field = '';
  if (q.type === 'long') field = `<textarea id="f" placeholder="${esc(q.placeholder || 'Type your answer…')}">${esc(val(q) || '')}</textarea>`;
  else if (['text','url','email','number'].includes(q.type))
    field = `<input id="f" type="${q.type}" placeholder="${esc(q.placeholder || (q.type === 'url' ? 'https://' : 'Type your answer…'))}" value="${esc(val(q) ?? '')}">`;
  else if (q.type === 'choice' || q.type === 'multi'){
    const cur = q.type === 'multi' ? (val(q) || []) : [val(q)];
    field = `<div class="opts">` + q.options.map((o, k) =>
      `<div class="opt ${cur.includes(o) ? 'on' : ''}" data-o="${esc(o)}"><span class="key">${LETTERS[k]}</span><span>${esc(o)}</span></div>`).join('') + `</div>`;
  } else if (q.type === 'yesno'){
    field = `<div class="opts">` + ['Yes','No'].map((o, k) =>
      `<div class="opt ${val(q) === o ? 'on' : ''}" data-o="${o}"><span class="key">${'YN'[k]}</span><span>${o}</span></div>`).join('') + `</div>`;
  } else if (q.type === 'scale'){
    const lo = q.min ?? 1, hi = q.max ?? 5; let s = '';
    for (let v = lo; v <= hi; v++) s += `<div class="opt ${val(q) === v ? 'on' : ''}" data-o="${v}">${v}</div>`;
    field = `<div class="scale">${s}</div>` + (q.labels ? `<div class="ends"><span>${esc(q.labels[0] || '')}</span><span>${esc(q.labels[1] || '')}</span></div>` : '');
  }
  const hint = q.type === 'long' ? '<kbd>Shift ⇧ + Enter ↵</kbd> for a new line · <kbd>Enter ↵</kbd> to continue'
            : q.type === 'multi' ? 'pick any · <kbd>Enter ↵</kbd> to continue'
            : ['choice','yesno','scale'].includes(q.type) ? 'press a key or click' : 'press <kbd>Enter ↵</kbd>';
  root.innerHTML = `<div class="num">${i + 1} → ${req ? '' : '<span style="color:var(--muted)">optional</span>'}</div>
    <h1>${esc(q.label)}</h1>${q.help ? `<p class="help">${esc(q.help)}</p>` : ''}${field}
    <div class="err" id="err"></div>
    <div class="row"><button id="ok">${i === Q.length - 1 ? 'Review' : 'OK'}</button><span class="hint">${hint}</span></div>`;
  const f = document.getElementById('f');
  if (f){ f.focus(); f.oninput = () => { A[q.id] = q.type === 'number' ? (f.value === '' ? '' : Number(f.value)) : f.value; progress(); }; }
  root.querySelectorAll('.opt').forEach(el => el.onclick = () => pick(q, el.dataset.o));
  document.getElementById('ok').onclick = () => advance(q);
}
function pick(q, o){
  if (q.type === 'multi'){
    const cur = new Set(val(q) || []); cur.has(o) ? cur.delete(o) : cur.add(o);
    A[q.id] = q.options.filter(x => cur.has(x));
    root.querySelectorAll('.opt').forEach(el => el.classList.toggle('on', cur.has(el.dataset.o)));
    progress(); return;
  }
  A[q.id] = q.type === 'scale' ? Number(o) : o;
  root.querySelectorAll('.opt').forEach(el => el.classList.toggle('on', el.dataset.o === String(o)));
  setTimeout(() => advance(q), 180);
}
function advance(q){
  const err = document.getElementById('err');
  if (q.required !== false && !filled(q)){ err.textContent = 'This one matters — an answer is needed to continue.'; return; }
  if (q.type === 'url' && filled(q) && !/^https?:\/\/\S+\.\S+/.test(String(val(q)))){ err.textContent = 'A full address, starting with https://'; return; }
  if (q.type === 'email' && filled(q) && !/^\S+@\S+\.\S+$/.test(String(val(q)))){ err.textContent = 'That does not look like an email address.'; return; }
  go(1);
}
function go(d){ i = Math.max(-1, Math.min(Q.length, i + d)); show(); }
function review(){
  root.innerHTML = `<div class="num">review</div><h1>Everything in one place</h1>
    <p class="help">Click any answer to change it. Submit when it reads true.</p>
    <div class="review">` + Q.map((q, k) => {
      const v = val(q); const txt = Array.isArray(v) ? v.join(', ') : (v === undefined || v === '' ? '—' : String(v));
      return `<div data-k="${k}"><small>${esc(q.label)}</small>${esc(txt)}</div>`; }).join('') +
    `</div><div class="err" id="err"></div>
    <div class="row"><button id="submit">Submit answers</button><span class="hint"><kbd>⌘/Ctrl + Enter ↵</kbd></span></div>`;
  root.querySelectorAll('.review div').forEach(el => el.onclick = () => { i = Number(el.dataset.k); show(); });
  document.getElementById('submit').onclick = submit;
}
async function submit(){
  const missing = Q.filter(q => q.required !== false && !filled(q));
  if (missing.length){ i = Q.indexOf(missing[0]); show(); return; }
  const body = JSON.stringify({ project: DATA.project, phase: SPEC.phase, answers: A });
  const btn = document.getElementById('submit'); btn.disabled = true; btn.textContent = 'Sending…';
  if (location.protocol === 'file:'){ i = Q.length + 1; show(body); return; }
  try {
    const r = await fetch(DATA.post_to, { method: 'POST', headers: { 'content-type': 'application/json' }, body });
    if (!r.ok) throw new Error(await r.text());
    i = Q.length + 1; show();
  } catch (e) {
    btn.disabled = false; btn.textContent = 'Submit answers';
    document.getElementById('err').textContent = 'Could not reach the agent (' + e.message + '). Is `monty intake ask` still running?';
  }
}
function done(body){
  root.innerHTML = `<div class="done"><div class="tick">✓</div><h1>Thank you</h1>
    <p class="help" style="margin:0 auto 20px">${body ? 'This page was opened as a file, so nothing could be sent. Copy the answers below to the agent.' : 'Your answers are with the agent. You can close this tab — the next round will open when it is ready.'}</p>
    ${body ? `<pre>${esc(body)}</pre>` : ''}</div>`;
  document.getElementById('bar').style.width = '100%';
}
document.getElementById('prev').onclick = () => go(-1);
document.getElementById('next').onclick = () => i < 0 ? go(1) : advance(Q[i]);
document.addEventListener('keydown', e => {
  if (i > Q.length) return;
  const inField = e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT';
  if (e.key === 'Enter'){
    if ((e.metaKey || e.ctrlKey) && i === Q.length) return submit();
    if (i < 0) return go(1);
    if (i === Q.length) return;
    if (e.target.tagName === 'TEXTAREA' && e.shiftKey) return;
    e.preventDefault(); return advance(Q[i]);
  }
  if (inField) return;
  if (i < 0 || i >= Q.length) return;
  const q = Q[i], k = e.key.toUpperCase();
  if ((q.type === 'choice' || q.type === 'multi') && LETTERS.indexOf(k) > -1 && q.options[LETTERS.indexOf(k)]) pick(q, q.options[LETTERS.indexOf(k)]);
  else if (q.type === 'yesno' && (k === 'Y' || k === 'N')) pick(q, k === 'Y' ? 'Yes' : 'No');
  else if (q.type === 'scale' && /^[0-9]$/.test(k)){ const v = Number(k); if (v >= (q.min ?? 1) && v <= (q.max ?? 5)) pick(q, v); }
  else if (e.key === 'ArrowUp') go(-1);
});
show();
</script>
</body>
</html>
"""
