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
  * the DESIGN SYSTEM as measured (tokens vs rogues, escapes);
  * CONTRADICTIONS: meanings that collide, near-duplicate colors, ghost
    classes — everything the repo says twice or says wrong.

Deterministic except the optional definition drafts. The terminal IS the
report — an instrument prints findings, it does not decorate them.
"""

from __future__ import annotations

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
    return lines


def explain(root: Path | None = None, draft: bool = True) -> list[str]:
    root = root or workspace_root()
    return render_terminal(build(root, draft=draft))
