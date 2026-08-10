"""Topic discovery: BERTopic over the zoo's own embedder.

LIBRARY-SHAPED BY RULING (the seed's skip rows say why): BERTopic brings
the clustering (UMAP + HDBSCAN + c-TF-IDF); the vectors come from
embed_text on a carried model, so "what are people talking about" runs on
the same embedder every other comparison uses. KeyBERT rides the same
vectors for per-document keyphrases.

Needs the extra: `uv sync --extra topics`.
"""

from __future__ import annotations

from .run import ZooError, embed_text


def discover_topics(texts: list[str], model_id: str = "text-minilm",
                    min_topic_size: int = 5) -> list[dict]:
    """texts → topics: [{topic, count, terms, examples}] — discovered, not
    assigned. Fixed-label assignment is classify-zeroshot's job; this finds
    the labels nobody wrote down."""
    try:
        from bertopic import BERTopic
    except ImportError as e:
        raise ZooError("topics needs the extra: `uv sync --extra topics` (bertopic).") from e
    if len(texts) < max(min_topic_size * 2, 10):
        raise ZooError(
            f"{len(texts)} texts is too few to discover topics from — "
            "gather at least ~20, or use classify-zeroshot with labels you name."
        )

    vectors = embed_text(model_id, texts)
    topic_model = BERTopic(min_topic_size=min_topic_size, calculate_probabilities=False,
                           verbose=False)
    assignments, _ = topic_model.fit_transform(texts, embeddings=vectors)

    out = []
    for row in topic_model.get_topic_info().to_dict("records"):
        tid = row["Topic"]
        if tid == -1:  # BERTopic's outlier bucket — reported, never hidden
            out.append({"topic": "(outliers)", "count": row["Count"], "terms": [],
                        "examples": []})
            continue
        terms = [t for t, _ in (topic_model.get_topic(tid) or [])[:6]]
        examples = [texts[i] for i, a in enumerate(assignments) if a == tid][:3]
        out.append({"topic": row.get("Name", str(tid)), "count": row["Count"],
                    "terms": terms, "examples": examples})
    return out


def keyphrases(texts: list[str], model_id: str = "text-minilm", top_n: int = 5) -> list[list[str]]:
    """Per-document keyphrases via KeyBERT on the zoo's embedder."""
    try:
        from keybert import KeyBERT
    except ImportError as e:
        raise ZooError("topics needs the extra: `uv sync --extra topics` (keybert).") from e

    class _Backend:  # KeyBERT wants an object with .embed()
        def embed(self, documents, verbose=False):
            return embed_text(model_id, list(documents))

    kb = KeyBERT(model=_Backend())
    got = kb.extract_keywords(texts, top_n=top_n)
    if texts and isinstance(got[0], tuple):  # single-doc shape
        got = [got]
    return [[k for k, _ in doc] for doc in got]
