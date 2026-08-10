"""Semantic hearing for the ontology: does the vocabulary MEAN what its
structure claims?

The string laws enforce "one word, one meaning". This module hears the
dual — "one meaning, one word" — which no string check can: two words
defined into the same idea, a candidate that is secretly an existing
word, a local word that duplicates an inherited org word under a
different name, an owner grouping that does not match where the meanings
actually cluster.

THE ENGINE IS DELIBERATELY TINY. POTION (model2vec static embeddings,
~30 MB, numpy-only) — no torch, no onnxruntime, no tokenizer session,
millisecond inference. Definitions are one-liners; static embeddings
rank one-liners well, and a context layer must stay light. The extra:

    uvx --from "montology[semantics] @ git+…" monty onto audit

EVERY FINDING IS ADVISORY, PERMANENTLY. A cosine score is an
instrument's hint; only a human ruling (rename, merge, re-own) makes it
vocabulary. Semantics propose — the laws stay deterministic.
"""

from __future__ import annotations

from typing import Callable

_MODEL_ID = "minishlab/potion-base-8M"

_NO_MODEL = (
    "semantic analysis needs the [semantics] extra (POTION static embeddings, "
    "~30 MB, numpy-only). Repair: reinstall with the extra — "
    'uvx --from "montology[semantics] @ git+https://github.com/socialite-ml/'
    'montology#subdirectory=.monty/cli" monty …'
)

# tests pin this to a deterministic fake; None = load POTION lazily
EMBEDDER: Callable | None = None


def _embed(texts: list[str]):
    """(n, dims) L2-normalized, or a string carrying the repair."""
    global EMBEDDER
    if EMBEDDER is not None:
        return EMBEDDER(texts)
    try:
        from model2vec import StaticModel
    except ImportError:
        return _NO_MODEL
    import os

    import numpy as np

    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

    model = StaticModel.from_pretrained(_MODEL_ID)

    def run(batch: list[str]):
        v = model.encode(batch)
        norms = np.linalg.norm(v, axis=1, keepdims=True)
        return v / np.clip(norms, 1e-9, None)

    EMBEDDER = run
    return run(texts)


def _rows():
    from .db import connect, db_path

    if not db_path().exists():
        return []
    conn = connect(readonly=True)
    try:
        return [dict(r) for r in conn.execute(
            "SELECT name, kind, owner, definition, origin FROM word ORDER BY name")]
    except Exception:  # noqa: BLE001 — a pre-origin db reads fine, just unattributed
        return [dict(r) | {"origin": None} for r in conn.execute(
            "SELECT name, kind, owner, definition FROM word ORDER BY name")]


def similar(query: str, top: int = 8) -> str:
    """The words nearest a name or a definition — run BEFORE authoring:
    the meaning may already have a word."""
    rows = _rows()
    if not rows:
        return "the ontology is empty — nothing to compare against yet."
    vecs = _embed([f"{w['name']}: {w['definition']}" for w in rows] + [query])
    if isinstance(vecs, str):
        return vecs
    scores = vecs[:-1] @ vecs[-1]
    ranked = sorted(zip(scores, rows), key=lambda p: -p[0])[:top]
    return "\n".join(f"{s:6.2f}  {w['name']:<22} {w['definition'][:70]}"
                     for s, w in ranked)


# calibrated live: montology's own 14 DISTINCT words top out at 0.49
# pairwise, while a genuinely duplicated meaning scored 0.74 — 0.70 sits
# in the measured gap with buffer on both sides
def audit(dup_threshold: float = 0.70, candidates: list[dict] | None = None) -> str:
    """The semantic audit, all advisory: meanings that collide, candidates
    that already exist, org/local doubles, misfiled owners."""
    rows = _rows()
    if not rows:
        return "the ontology is empty — nothing to cluster yet."
    texts = [f"{w['name']}: {w['definition']}" for w in rows]
    vecs = _embed(texts)
    if isinstance(vecs, str):
        return vecs
    sims = vecs @ vecs.T
    report: list[str] = []

    # one meaning, one word — the dual the string laws cannot hear
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if sims[i, j] >= dup_threshold:
                a, b = rows[i], rows[j]
                both_local = a["origin"] is None and b["origin"] is None
                flavor = ("two words, one meaning?" if both_local else
                          "local word doubles an inherited one?")
                report.append(
                    f"note semantics: {a['name']!r} ~ {b['name']!r} "
                    f"({sims[i, j]:.2f}) — {flavor} Merge, or sharpen one "
                    f"definition until they part.")

    # misfiled owners: a word whose nearest meanings live in another family.
    # Needs POPULATION — under ~10 words every neighbor is a stranger and
    # the signal is noise (measured on a 5-word fixture).
    owners = [w["owner"] or w["name"] for w in rows]
    for i, w in enumerate(rows):
        if len(rows) < 10 or not w["owner"]:
            continue
        order = sims[i].argsort()[::-1]
        neighbors = [owners[j] for j in order[1:4]]
        if neighbors and all(n != w["owner"] for n in neighbors):
            report.append(
                f"note semantics: {w['name']!r} is owned by {w['owner']!r} but "
                f"its meaning clusters with {max(set(neighbors), key=neighbors.count)!r} "
                f"— misfiled, or the definition understates its home.")

    # candidates that are secretly existing words
    for c in candidates or []:
        cv = _embed([c["name"]])
        if isinstance(cv, str):
            break
        scores = vecs @ cv[0]
        best = int(scores.argmax())
        if scores[best] >= dup_threshold:
            report.append(
                f"note semantics: candidate {c['name']!r} ({c['count']}×) is "
                f"semantically {rows[best]['name']!r} ({scores[best]:.2f}) — "
                f"map it to the existing word instead of minting a new one.")

    verdict = (f"semantics: {len(rows)} meanings compared, "
               f"{len(report)} finding(s) — all advisory; only a ruling makes them vocabulary")
    return "\n".join(report + [verdict])
