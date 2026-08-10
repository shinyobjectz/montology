"""`monty explain` — the one-shot conceptual X-ray of a codebase.

Point it at any repo cold and it composes everything the instruments can
measure into one anatomy:

  * the DECLARED surface (languages, declarations, files);
  * the vocabulary it HAS (words) and the vocabulary it is ASKING FOR
    (candidates — with definitions drafted on the atomic tier when a
    backend is reachable, refused-over-wrong as always);
  * CONCEPT CLUSTERS — where meanings actually gather, semantically —
    versus the directory structure's claimed architecture: concepts that
    span many directories are cross-cutting; directories whose names
    scatter across many clusters are grab-bags;
  * the DESIGN SYSTEM as measured (palette with real chips, tokens vs
    rogues, escapes);
  * CONTRADICTIONS: meanings that collide, near-duplicate colors, ghost
    classes — everything the repo says twice or says wrong.

Deterministic except the optional definition drafts; renders a terminal
summary and a self-contained dark HTML report (.monty/explain.html).
"""

from __future__ import annotations

import html as html_mod
from collections import Counter, defaultdict
from pathlib import Path

from montology_core import workspace_root

from .lint import candidates as scan_candidates
from .styles import norm_color, style_surface
from .surface import declarations

CLUSTER_T = 0.35   # grouping RELATED meanings (duplicates fire at 0.70)


def _clusters(items: list[dict]) -> list[list[int]]:
    """Union-find over semantic similarity; [] when semantics is absent."""
    try:
        from montology_ontology import semantics
    except ImportError:
        return []
    texts = [f"{it['name']}: {it.get('definition') or ''}".strip(": ")
             for it in items]
    vecs = semantics._embed(texts)
    if isinstance(vecs, str) or len(items) < 2:
        return []
    sims = vecs @ vecs.T
    parent = list(range(len(items)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if sims[i, j] >= CLUSTER_T:
                parent[find(i)] = find(j)
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(items)):
        groups[find(i)].append(i)
    return sorted((g for g in groups.values() if len(g) >= 2), key=len, reverse=True)


def _draft_definitions(names: list[str], cap: int = 5) -> dict[str, str]:
    """Atomic-tier drafts for the top candidates — best-effort, law-checked,
    silently absent when no backend serves."""
    try:
        import logging

        logging.disable(logging.INFO)  # mellea narrates; the report should not
        from montology_gen import gen_word
        from montology_gen._session import tiny_session

        if tiny_session() is None:
            return {}
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for name in names[:cap]:
        got = gen_word(name, f"a recurring declared name in this codebase")
        if not got.startswith(("REFUSED", "the model", "No model")):
            out[name] = got.split("\n")[0].partition(":")[2].strip()
    return {k: v for k, v in out.items() if v}


def build(root: Path | None = None, draft: bool = True) -> dict:
    from montology_ontology import doctrines, tokens, words

    root = root or workspace_root()
    surface = declarations(root)
    cands = scan_candidates(root, top=20)
    styles = style_surface(root)
    vocab = words()
    toks = tokens()

    by_lang: Counter[str] = Counter(d["lang"] for d in surface["decls"])
    name_dirs: dict[str, set[str]] = defaultdict(set)
    for d in surface["decls"]:
        top = d["file"].split("/")[0] if "/" in d["file"] else "."
        name_dirs[d["name"].lower().lstrip("_")].add(top)

    items = ([{"name": w["name"], "definition": w["definition"], "kind": "word"}
              for w in vocab]
             + [{"name": c["name"], "definition": "", "kind": "candidate"}
                for c in cands])
    groups = _clusters(items)
    clusters = []
    for g in groups:
        members = [items[i] for i in g]
        dirs: set[str] = set()
        for m in members:
            dirs |= name_dirs.get(m["name"].lower(), set())
        clusters.append({"members": members, "dirs": sorted(dirs)})

    cross_cutting = [c for c in clusters if len(c["dirs"]) >= 3]
    dir_spread: Counter[str] = Counter()
    for c in clusters:
        for d in c["dirs"]:
            dir_spread[d] += 1
    grab_bags = [d for d, n in dir_spread.most_common(3) if n >= 3]

    contradictions: list[str] = []
    try:
        from montology_ontology import semantic_audit

        audit = semantic_audit(candidates=cands)
        contradictions += [line for line in audit.splitlines()
                           if line.startswith("note semantics:")]
    except Exception:  # noqa: BLE001
        pass
    token_values = {norm_color(t["value"]) for t in toks if t["category"] == "color"}
    rogues = [(c, n, styles["where"].get(c, "?"))
              for c, n in styles["colors"].most_common(12)
              if c not in token_values]

    drafted = _draft_definitions([c["name"] for c in cands]) if draft else {}

    return {"root": str(root), "name": root.name,
            "surface": {"files": surface["files"], "decls": len(surface["decls"]),
                        "by_lang": dict(by_lang), "errors": surface["errors"]},
            "vocab": vocab, "tokens": toks, "doctrine": doctrines(),
            "candidates": cands, "drafted": drafted,
            "clusters": clusters, "cross_cutting": cross_cutting,
            "grab_bags": grab_bags, "contradictions": contradictions,
            "styles": {"colors": styles["colors"].most_common(12),
                       "rogues": rogues,
                       "n_classes": len(styles["defined_classes"]),
                       "escapes": len(styles["arbitrary"])}}


def render_terminal(r: dict) -> list[str]:
    lines = [f"── {r['name']}: the conceptual X-ray ─────────────────────"]
    s = r["surface"]
    langs = ", ".join(f"{k} {v}" for k, v in
                      sorted(s["by_lang"].items(), key=lambda kv: -kv[1])[:5])
    lines.append(f"surface: {s['decls']} declarations in {s['files']} files ({langs})")
    lines.append(f"vocabulary: {len(r['vocab'])} word(s), {len(r['tokens'])} token(s)"
                 + (f", {len(r['candidates'])} candidate(s) unclaimed" if r["candidates"] else ""))
    for c in r["candidates"][:6]:
        drafted = r["drafted"].get(c["name"])
        lines.append(f"  {c['count']:>4}x  {c['name']}"
                     + (f" — draft: {drafted}" if drafted else ""))
    for c in r["clusters"][:5]:
        names = ", ".join(m["name"] for m in c["members"][:6])
        span = f" (spans {len(c['dirs'])} dirs)" if len(c["dirs"]) >= 2 else ""
        lines.append(f"cluster: {names}{span}")
    for c in r["cross_cutting"][:3]:
        lines.append("note: concept group [" + ", ".join(m["name"] for m in c["members"][:4])
                     + f"] cuts across {', '.join(c['dirs'][:5])} — "
                     "an architecture the directory tree does not show")
    for d in r["grab_bags"]:
        lines.append(f"note: {d}/ appears in many unrelated concept clusters — a grab-bag")
    for line in r["contradictions"][:6]:
        lines.append(line)
    if r["styles"]["rogues"]:
        top = ", ".join(f"{c} ×{n}" for c, n, _ in r["styles"]["rogues"][:5])
        lines.append(f"design: {len(r['styles']['rogues'])} unnamed color(s): {top}")
    lines.append(f"explained — full report: .monty/explain.html")
    return lines


def _chip(color: str, label: str) -> str:
    return (f'<span class="chip"><i style="background:{color}"></i>'
            f"{html_mod.escape(label)}</span>")


def render_html(r: dict) -> str:
    e = html_mod.escape
    parts = [f"""<!doctype html><meta charset="utf-8">
<title>{e(r['name'])} — montology X-ray</title>
<style>
 body{{background:#0d0d14;color:#cdd6f4;font:15px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;
      max-width:960px;margin:2rem auto;padding:0 1.2rem}}
 h1{{font-size:1.3rem}} h2{{font-size:1.02rem;color:#8aadf4;margin-top:2.2rem;
     border-bottom:1px solid #24273a;padding-bottom:.35rem}}
 .stat{{display:inline-block;background:#181825;border:1px solid #24273a;border-radius:8px;
       padding:.45rem .8rem;margin:.2rem .3rem .2rem 0}}
 .stat b{{color:#a6da95}}
 table{{border-collapse:collapse;width:100%}} td,th{{text-align:left;padding:.28rem .6rem;
       border-bottom:1px solid #1e1e2c;vertical-align:top}} th{{color:#8aadf4}}
 .chip{{display:inline-flex;align-items:center;gap:.45rem;background:#181825;
       border:1px solid #24273a;border-radius:999px;padding:.25rem .7rem;margin:.18rem}}
 .chip i{{width:1rem;height:1rem;border-radius:4px;display:inline-block;
         border:1px solid #363a4f}}
 .cluster{{background:#141420;border:1px solid #24273a;border-radius:10px;
          padding:.7rem 1rem;margin:.5rem 0}}
 .k-word{{color:#a6da95}} .k-candidate{{color:#eed49f}}
 .warn{{color:#eed49f}} .dim{{color:#6c7086}}
 .draft{{color:#94e2d5}}
</style>
<h1>{e(r['name'])} <span class="dim">— the conceptual X-ray</span></h1>
<div>
 <span class="stat"><b>{r['surface']['decls']}</b> declarations</span>
 <span class="stat"><b>{r['surface']['files']}</b> files</span>
 <span class="stat"><b>{len(r['vocab'])}</b> words</span>
 <span class="stat"><b>{len(r['tokens'])}</b> tokens</span>
 <span class="stat"><b>{len(r['candidates'])}</b> unclaimed concepts</span>
</div>"""]

    if r["styles"]["colors"]:
        parts.append("<h2>The palette, as measured</h2><div>")
        token_vals = {norm_color(t["value"]): t["name"] for t in r["tokens"]
                      if t["category"] == "color"}
        for c, n, *_ in [(c, n) for c, n in r["styles"]["colors"]]:
            name = token_vals.get(c)
            label = f"{name} · {c}" if name else f"{c} ×{n} (unnamed)"
            parts.append(_chip(c, label))
        parts.append("</div>")

    if r["vocab"]:
        parts.append("<h2>The vocabulary it has</h2><table>"
                     "<tr><th>word</th><th>code</th><th>is</th></tr>")
        for w in r["vocab"]:
            parts.append(f"<tr><td class=k-word>{e(w['name'])}</td>"
                         f"<td class=dim>{e(w['code'] or '—')}</td>"
                         f"<td>{e(w['definition'])}</td></tr>")
        parts.append("</table>")

    if r["candidates"]:
        parts.append("<h2>The vocabulary it is asking for</h2><table>"
                     "<tr><th>uses</th><th>name</th><th>drafted definition</th></tr>")
        for c in r["candidates"][:12]:
            d = r["drafted"].get(c["name"], "")
            parts.append(f"<tr><td>{c['count']}×</td><td class=k-candidate>{e(c['name'])}</td>"
                         f"<td class=draft>{e(d) if d else '<span class=dim>—</span>'}</td></tr>")
        parts.append("</table>")

    if r["clusters"]:
        parts.append("<h2>Where meanings actually gather</h2>")
        for c in r["clusters"][:8]:
            members = " ".join(
                f"<span class='k-{m['kind']}'>{e(m['name'])}</span>" for m in c["members"])
            dirs = (f"<div class=dim>spans: {e(', '.join(c['dirs']))}</div>"
                    if c["dirs"] else "")
            parts.append(f"<div class=cluster>{members}{dirs}</div>")

    tensions = []
    for c in r["cross_cutting"][:4]:
        tensions.append("concept group [" + ", ".join(e(m["name"]) for m in c["members"][:4])
                        + f"] cuts across <b>{e(', '.join(c['dirs'][:6]))}</b>")
    for d in r["grab_bags"]:
        tensions.append(f"<b>{e(d)}/</b> appears in many unrelated clusters — a grab-bag")
    if tensions:
        parts.append("<h2>The architecture the directory tree does not show</h2><ul>")
        parts += [f"<li class=warn>{t}</li>" for t in tensions]
        parts.append("</ul>")

    if r["contradictions"]:
        parts.append("<h2>Where it contradicts itself</h2><ul>")
        for line in r["contradictions"][:10]:
            parts.append(f"<li class=warn>{e(line.removeprefix('note semantics: '))}</li>")
        parts.append("</ul>")

    parts.append('<p class=dim>rendered by <b>monty explain</b> — montology, '
                 'the ontology layer. Prose is rendered, never authored.</p>')
    return "\n".join(parts)


def explain(root: Path | None = None, draft: bool = True) -> list[str]:
    root = root or workspace_root()
    report = build(root, draft=draft)
    out = root / ".monty" / "explain.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(render_html(report))
    return render_terminal(report)
