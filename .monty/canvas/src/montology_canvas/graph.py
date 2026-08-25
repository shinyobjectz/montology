"""The graph: the vocabulary and the code it governs, as nodes and edges.

An INSTRUMENT, under the rule the others follow — deterministic, model-free,
assembled from the database and the scan. What cannot be measured is absent
rather than invented, and anything inferred says so (`suggested`), because an
instrument that hands back a guess dressed as a fact is worse than one that
says nothing.

The node kinds are the things montology names: `word`, `ruling`, `surface`,
`candidate`, `doctrine`, `token` — plus `term`, a name the vocabulary speaks
ABOUT without owning. A term is where the dead names live: what a route routes
away from, what a rename retired, what an overload forbids. Rendering them is
the point rather than an accident — a vocabulary's history is the terms it
stopped using, and a graph that shows only live words cannot show a decision.

Every edge kind here already gates something (see the doctrine "An edge must be
enforceable"): `contains` gates the code namespace, `routes` gates a register,
`renamed` and `overloaded` gate a name, `bears` is checked against the scan.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

TREE_WIDE = "**"


def _word_nodes(vocab: list[dict]) -> list[dict]:
    return [{
        "id": f"word:{w['name']}",
        "kind": "word",
        "label": w["name"],
        "data": {
            "name": w["name"], "word_kind": w["kind"], "pos": w.get("pos"),
            "owner": w["owner"], "code": w["code"], "definition": w["definition"],
            "test": w["test"], "origin": w.get("origin"),
        },
    } for w in vocab]


def _code_edges(vocab: list[dict]) -> list[dict]:
    """Containment, from `owner`. The dotted code says the same thing and the
    lint already gates that its prefix resolves; owner is what a reader draws."""
    names = {w["name"] for w in vocab}
    return [{
        "id": f"contains:{w['owner']}:{w['name']}",
        "kind": "contains",
        "source": f"word:{w['owner']}",
        "target": f"word:{w['name']}",
        "label": "",
    } for w in vocab if w["owner"] and w["owner"] in names]


def _term_edges(routes: list[dict], renames: list[dict], overloads: list[dict],
                live: set[str]) -> tuple[list[dict], list[dict]]:
    """The three rulings that share one shape: a dead or wrong term pointing at
    the word to say instead. Different gates, same picture, so they are drawn
    the same way and told apart by the edge kind and its label."""
    terms: dict[str, dict] = {}
    edges: list[dict] = []

    def term(name: str, why: str) -> str:
        node_id = f"word:{name}" if name in live else f"term:{name}"
        if node_id.startswith("term:") and node_id not in terms:
            terms[node_id] = {"id": node_id, "kind": "term", "label": name,
                              "data": {"name": name, "why": why}}
        return node_id

    for r in routes:
        scope = r["scope"] or ""
        edges.append({
            "id": f"routes:{r['from_term']}:{r['to_word']}:{r['register']}",
            "kind": "routes",
            "source": term(r["from_term"], "routed away from"),
            "target": f"word:{r['to_word']}",
            "label": r["register"],
            "data": {"register": r["register"], "scope": scope,
                     "why": r.get("why"), "ruled_on": r.get("ruled_on"),
                     # A route with neither scope nor a register default cannot
                     # gate; the canvas must be able to draw that difference.
                     "gates": bool(scope) or r["register"] != "all"},
        })
    for r in renames:
        edges.append({
            "id": f"renamed:{r['was']}:{r['now']}",
            "kind": "renamed",
            "source": term(r["was"], "retired by a rename"),
            "target": f"word:{r['now']}",
            "label": "renamed",
            "data": {"why": r.get("why"), "renamed_on": r.get("renamed_on"),
                     "gates": True},   # the guard always blocks a retired name
        })
    for o in overloads:
        edges.append({
            "id": f"overloaded:{o['dont_say']}:{o['say']}",
            "kind": "overloaded",
            "source": term(o["dont_say"], "ruled against by an overload"),
            "target": f"word:{o['say']}",
            "label": "say instead",
            "data": {"why": o.get("why"), "gates": True},
        })
    return list(terms.values()), edges


def _ruling_nodes(collisions: list[dict], exceptions: list[dict],
                  live: set[str]) -> tuple[list[dict], list[dict]]:
    """Collisions and exceptions are NODES, not edge labels. Both carry a why
    and a place, and an edge label can hold neither — which is exactly how a
    decision decays into a line nobody can account for."""
    nodes, edges = [], []
    for c in collisions:
        nid = f"ruling:collision:{c['term']}"
        nodes.append({"id": nid, "kind": "ruling", "label": f"{c['term']} vs {c['theirs']}",
                      "data": {"ruling_kind": "collision", "term": c["term"],
                               "theirs": c["theirs"], "their_meaning": c["their_meaning"],
                               "ruling": c["ruling"], "decided": c.get("decided")}})
        if c["term"] in live:
            edges.append({"id": f"rules:{nid}", "kind": "rules", "source": nid,
                          "target": f"word:{c['term']}", "label": "ruled on"})
    for e in exceptions:
        nid = f"ruling:exception:{e['word']}:{e['scope']}"
        where = "tree-wide" if e["scope"] == TREE_WIDE else e["scope"]
        nodes.append({"id": nid, "kind": "ruling", "label": f"{e['word']} @ {where}",
                      "data": {"ruling_kind": "exception", "word": e["word"],
                               "scope": e["scope"], "judged": e.get("judged"),
                               "why": e["why"], "checked": e.get("checked")}})
        if e["word"] in live:
            edges.append({"id": f"rules:{nid}", "kind": "rules", "source": nid,
                          "target": f"word:{e['word']}", "label": "excepted"})
    return nodes, edges


def _code_facts(vocab: list[dict], decls: list[dict], granted: list[dict],
                enforced_kinds: set[str]) -> dict[str, dict]:
    """What the code does with each word's NAME.

    Montology's model is worth being precise about here, because the obvious
    reading is backwards: a declaration named after an enforced word is a
    COLLISION, not a resolution. Code answers to a word through a `bearing`
    (a surface that implements it), never by wearing its name. So a word node
    carries three counts, and they mean different things: `collides` (code
    wrongly wearing the name), `excepted` (code deliberately wearing it, with
    a recorded reason), and `bears` (what actually implements the term).
    """
    enforced = {w["name"].lower() for w in vocab if w["kind"] in enforced_kinds}
    facts = {w["name"]: {"collides": 0, "excepted": 0, "at": []} for w in vocab}
    by_low = {w["name"].lower(): w["name"] for w in vocab}
    for d in decls:
        low = d["name"].lower()
        if low not in enforced:
            continue
        name = by_low[low]
        hit = any(e["word"].lower() == low
                  and (e["scope"] == TREE_WIDE or fnmatch(d["file"], e["scope"]))
                  for e in granted)
        facts[name]["excepted" if hit else "collides"] += 1
        if not hit and len(facts[name]["at"]) < 10:
            facts[name]["at"].append(f"{d['file']}:{d['line']}")
    return facts


def graph(root: Path | None = None, *, with_scan: bool = True,
          candidate_top: int = 20) -> dict:
    """The whole ontology as one document: nodes, edges, stats, provenance.

    `with_scan=False` skips the tree-sitter sweep — the vocabulary alone, for
    when the caller wants the graph in milliseconds and does not need the code.
    """
    from montology_core import workspace_root
    from montology_ontology import (collisions, doctrines, exceptions, genera,
                                    overloads, renames, routes, tokens, words)

    root = root or workspace_root()
    vocab = words()
    live = {w["name"] for w in vocab}
    rulings_c, rulings_e = collisions(), exceptions()

    nodes = _word_nodes(vocab)
    edges = _code_edges(vocab)

    # subsumption: what a word IS, as against where it lives. Drawn separately
    # from containment for exactly that reason — see the genus doctrine.
    edges += [{"id": f"genus:{g['word_name']}:{g['genus_name']}", "kind": "genus",
               "source": f"word:{g['word_name']}", "target": f"word:{g['genus_name']}",
               "label": "is a kind of", "data": {"why": g.get("why"), "gates": True}}
              for g in genera()
              if g["word_name"] in live and g["genus_name"] in live]

    term_nodes, term_edges = _term_edges(routes(), renames(), overloads(), live)
    nodes += term_nodes
    edges += term_edges

    ruling_nodes, ruling_edges = _ruling_nodes(rulings_c, rulings_e, live)
    nodes += ruling_nodes
    edges += ruling_edges

    for d in doctrines():
        nodes.append({"id": f"doctrine:{d['title']}", "kind": "doctrine",
                      "label": d["title"], "data": {"body": d["body"], "ord": d["ord"]}})
    for t in tokens():
        nodes.append({"id": f"token:{t['name']}", "kind": "token", "label": t["name"],
                      "data": {"category": t["category"], "value": t["value"]}})

    # ── the code side ────────────────────────────────────────────────────────
    stats = {"words": len(vocab), "genus": len(genera()), "rulings": len(ruling_nodes),
             "terms": len(term_nodes), "doctrine": len(doctrines()),
             "tokens": len(tokens())}

    if with_scan:
        from montology_scan import candidates as scan_candidates
        from montology_scan import declarations
        from montology_scan.surf import bearings, seams, surfaces

        enforced_kinds = _enforced_kinds(root)
        surface = declarations(root)
        facts = _code_facts(vocab, surface["decls"], rulings_e, enforced_kinds)
        for n in nodes:
            if n["kind"] == "word":
                n["data"].update(facts.get(n["data"]["name"], {}))

        for s in surfaces(root):
            nodes.append({"id": f"surface:{s['id']}", "kind": "surface",
                          "label": s["owner"],
                          "data": {"surface_kind": s["kind"], "version": s.get("version"),
                                   "exposes": s["exposes"], "probe": s["probe"]}})
        for b in bearings(root):
            edges.append({"id": f"bears:{b['word_name']}:{b['surface_id']}",
                          "kind": "bears", "source": f"word:{b['word_name']}",
                          "target": f"surface:{b['surface_id']}", "label": "borne by",
                          "data": {"note": b.get("note")}})
        for s in seams(root):
            edges.append({"id": f"seam:{s['from_id']}:{s['to_id']}:{s['at']}",
                          "kind": "seam", "source": f"surface:{s['from_id']}",
                          "target": f"surface:{s['to_id']}", "label": s["kind"],
                          "data": {"direction": s["direction"], "at": s["at"]}})

        for c in scan_candidates(root, top=candidate_top):
            nodes.append({"id": f"candidate:{c['name']}", "kind": "candidate",
                          "label": c["name"],
                          "data": {"count": c["count"], "decl_kind": c["kind"],
                                   "suggested": True}})
        stats |= {"declarations": len(surface["decls"]), "files": surface["files"],
                  "surfaces": len(surfaces(root)), "seams": len(seams(root)),
                  "candidates": len(scan_candidates(root, top=candidate_top)),
                  "collides": sum(f["collides"] for f in facts.values()),
                  "excepted": sum(f["excepted"] for f in facts.values())}

    return {"workspace": root.name, "nodes": nodes, "edges": edges,
            "stats": stats, "fingerprint": _fingerprint(nodes, edges)}


def _enforced_kinds(root: Path) -> set[str]:
    """Read, not imported: the graph must not depend on the linter to know
    which kinds it gates on — the same reason the vocabulary does not."""
    import tomllib

    try:
        with (root / ".monty" / "montology.toml").open("rb") as fh:
            return set(tomllib.load(fh).get("scan", {}).get("enforced_kinds",
                                                            ["core", "inner"]))
    except (OSError, ValueError):
        return {"core", "inner"}


def _fingerprint(nodes: list[dict], edges: list[dict]) -> str:
    import hashlib
    import json

    blob = json.dumps({"n": nodes, "e": edges}, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]
