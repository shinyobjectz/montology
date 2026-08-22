"""The closing page: the whole ontology as one glossary, with the intake
answers it grew from as the appendix.

Rendered FROM the database, the same trade the words skill makes: every
word with its code, kind, part of speech, definition and test; every
ruling (say Y not X); the doctrine. Nothing here is authored — a word
that is not in `.monty/ontology.db` is not on the page, which is the
gate: the intake ends with `monty onto add`, not with prose.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from montology_core import WorkspaceError

from .spec import intake_dir, workspace_name


def _answer_files():
    folder = intake_dir()
    return sorted(folder.glob("*.answers.json")) if folder.exists() else []


def merged_answers() -> dict:
    """Every answered phase: {phase: {title, answered_at, answers, labels}}."""
    out: dict = {}
    for f in _answer_files():
        rec = json.loads(f.read_text())
        out[rec["phase"]] = {"title": rec["title"], "answered_at": rec["answered_at"],
                             "answers": rec["answers"],
                             "labels": {q["id"]: q["label"] for q in rec["questions"]}}
    return out


def status() -> list[str]:
    """Phases open and answered; whether the glossary has been rendered."""
    try:
        folder = intake_dir()
    except WorkspaceError as e:
        return [str(e)]
    if not folder.exists():
        return ["no intake yet — start one: monty intake ask <phase.json> "
                "(the intake skill carries phases/1-domain.json)"]
    specs = {p.stem for p in folder.glob("*.json") if not p.name.endswith(".answers.json")}
    answered = {p.name.removesuffix(".answers.json") for p in folder.glob("*.answers.json")}
    lines = [f"{'answered' if ph in answered else 'open    '}  {ph}" for ph in sorted(specs | answered)]
    g = folder / "glossary.html"
    lines.append(f"glossary  rendered {datetime.fromtimestamp(g.stat().st_mtime).date()} — {g}"
                 if g.exists() else "glossary  not rendered yet: monty intake glossary --open")
    return lines


def glossary() -> str:
    """Render .monty/answers/glossary.html from the ontology; refuse an empty one."""
    from montology_ontology.db import doctrines, overloads, words

    try:
        folder = intake_dir()
        name = workspace_name()
    except WorkspaceError as e:
        return str(e)
    rows = words()
    if not rows:
        return ("REFUSED — the ontology is empty, and a glossary shows words, it does not "
                "invent them. Author the words the intake surfaced first: "
                "monty onto add <name> \"<one-sentence definition>\" --test \"<what-is-it>\" --pos noun|verb|value")
    folder.mkdir(parents=True, exist_ok=True)
    phases = merged_answers()
    out = folder / "glossary.html"
    out.write_text(_render(name, rows, overloads(), doctrines(), phases))
    return f"glossary  {out} ({len(rows)} words, {len(phases)} phases answered)"


def _render(name: str, rows: list[dict], rulings: list[dict], doctrine: list[dict], phases: dict) -> str:
    e = html.escape
    by_name = sorted(rows, key=lambda r: r["name"].lower())
    cards = "".join(
        f"<section class='w' id='w-{e(r['name'])}'><h3>{e(r['name'])}"
        f"<span class='kind'>{e(r['kind'])}{(' · ' + e(r['pos'])) if r.get('pos') else ''}"
        f"{(' · inside ' + e(r['owner'])) if r.get('owner') else ''}</span>"
        f"{('<code>' + e(r['code']) + '</code>') if r.get('code') else ''}</h3>"
        f"<p class='def'>{e(r['definition'])}</p>"
        + (f"<p class='test'><b>test:</b> {e(r['test'])}</p>" if r.get("test") else "")
        + "</section>"
        for r in by_name)
    index = " ".join(f"<a href='#w-{e(r['name'])}'>{e(r['name'])}</a>" for r in by_name)
    ruled = "".join(
        f"<li><s>{e(o['dont_say'])}</s> → <b>{e(o['say'])}</b>{(' — ' + e(o['why'])) if o.get('why') else ''}</li>"
        for o in rulings)
    docs = "".join(f"<details><summary>{e(d['title'])}</summary><p>{e(d['body'])}</p></details>" for d in doctrine)
    answers = ""
    for ph, rec in phases.items():
        items = "".join(
            f"<dt>{e(rec['labels'].get(k, k))}</dt><dd>{e(', '.join(map(str, v)) if isinstance(v, list) else str(v))}</dd>"
            for k, v in rec["answers"].items())
        answers += (f"<details><summary>{e(rec['title'])} <span class='kind'>{e(ph)} · "
                    f"{e(rec['answered_at'][:10])}</span></summary><dl>{items}</dl></details>")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(name)} — glossary</title>
<style>
:root{{--bg:#fafaf8;--fg:#16161a;--muted:#6b6b74;--line:#e4e3df;--accent:#2f5bea;--card:#fff;
--font:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Helvetica,Arial,sans-serif;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111114;--fg:#f2f2f4;--muted:#9a9aa6;--line:#2a2a31;--accent:#7b95ff;--card:#18181d}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font-family:var(--font);line-height:1.5;-webkit-font-smoothing:antialiased}}
main{{max-width:820px;margin:0 auto;padding:56px clamp(20px,6vw,72px) 96px}}
.eyebrow{{color:var(--accent);font-weight:600;font-size:13px;letter-spacing:.04em;text-transform:uppercase}}
h1{{font-size:clamp(30px,4.5vw,46px);letter-spacing:-.02em;margin:6px 0 12px;line-height:1.1}}
.summary{{font-size:18px;color:var(--muted);max-width:62ch;margin:0 0 36px}}
.index{{display:flex;flex-wrap:wrap;gap:6px 14px;padding:16px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin-bottom:28px;font-size:14px}}
.index a{{color:var(--accent);text-decoration:none}}.index a:hover{{text-decoration:underline}}
.w{{padding:22px 0;border-bottom:1px solid var(--line)}}
.w h3{{margin:0 0 6px;font-size:22px;letter-spacing:-.01em;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}}
.w h3 code{{font:13px var(--mono);color:var(--muted);margin-left:auto}}
.kind{{font-size:12px;font-weight:500;color:var(--muted);letter-spacing:.02em}}
.def{{margin:0 0 6px;font-size:17px}}.test{{margin:0;color:var(--muted);font-size:14px}}
h2{{font-size:14px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:48px 0 12px}}
ul.ruled{{padding-left:18px}}ul.ruled li{{margin:6px 0}}
details{{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:12px 16px;margin-bottom:10px}}
summary{{cursor:pointer;font-weight:600}}details p{{color:var(--muted);margin:10px 0 0}}
dl{{margin:10px 0 0}}dt{{color:var(--muted);font-size:13px;margin-top:10px}}dd{{margin:2px 0 0}}
footer{{margin-top:48px;color:var(--muted);font-size:13px}}
</style></head><body><main>
<div class="eyebrow">{e(name)} · glossary</div>
<h1>The words this workspace runs on</h1>
<p class="summary">Every term below means exactly one thing here. When code, a brief or a conversation uses one of these words, this is what it means — and <code>monty onto check</code> answers for it.</p>
<div class="index">{index}</div>
{cards}
{('<h2>Rulings — say this, not that</h2><ul class="ruled">' + ruled + '</ul>') if ruled else ''}
{('<h2>Doctrine</h2>' + docs) if docs else ''}
<h2>Where they came from — the intake</h2>
{answers or '<p class="summary">No answered phases on disk.</p>'}
<footer>{len(rows)} words · rendered {stamp} from .monty/ontology.db. Definitions are authored there (<code>monty onto add</code>), never here.</footer>
</main></body></html>
"""
