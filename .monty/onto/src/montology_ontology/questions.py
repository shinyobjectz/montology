"""Competency questions: the requirements a vocabulary is answerable to.

The practice both vendors underplay. An ontology is correct if it answers the
questions it was built to answer — so the questions are kept, and re-run, and a
word that answers none of them has to explain itself.

Coverage runs BOTH WAYS, and the second direction is the one nobody ships:

  a question no word answers — the vocabulary has a hole where somebody said
  there was a need. Everyone checks this.

  a word no question motivates — vocabulary nobody asked for. This is how a
  glossary grows into something nobody reads, and it is invisible to every
  tool that only asks whether the model covers the requirements.

The second is only meaningful once questions exist. With none recorded, every
word is unmotivated, which is a fact about the questions rather than about the
words — so it is reported that way instead of as a hundred findings.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

from .db import connect


def _id(text: str) -> str:
    """A question's identity is its TEXT, normalised. Asking the same thing
    twice — a second intake round, a re-run — must not make two questions."""
    flat = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    flat = " ".join(flat.split())
    return hashlib.sha256(flat.encode()).hexdigest()[:12]


def _has(conn) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='question'").fetchone())


def ask(text: str, *, asked_in: str = "", answered_by: list[str] | None = None) -> str:
    """Record a question the vocabulary must be able to answer."""
    text = text.strip()
    if len(text.split()) < 3:
        return ("REFUSED — a competency question is a QUESTION: something the "
                "vocabulary must be able to answer, in words. 'orders' is a topic.")
    conn = connect()
    qid = _id(text)
    existing = conn.execute("SELECT text FROM question WHERE id=?", (qid,)).fetchone()
    conn.execute("INSERT OR IGNORE INTO question (id, text, asked_in, asked_at) "
                 "VALUES (?,?,?,?)",
                 (qid, text, asked_in or None,
                  datetime.now(UTC).isoformat(timespec="seconds")))
    note = ""
    for word in answered_by or []:
        note += "\n  " + answer(qid, word, conn=conn)
    conn.commit()
    return (f"asked  {qid}  {text}" if not existing
            else f"already asked  {qid}  {existing[0]}") + note


def answer(qid: str, word: str, *, conn=None) -> str:
    """Say that a word is part of how this question gets answered."""
    c = conn or connect()
    if not c.execute("SELECT 1 FROM question WHERE id=?", (qid,)).fetchone():
        return f"REFUSED — no question {qid!r}. `monty onto questions` lists them."
    if not c.execute("SELECT 1 FROM word WHERE lower(name)=?", (word.lower(),)).fetchone():
        return (f"REFUSED — {word!r} is not a word. A question is answered by "
                f"the vocabulary, so add it first (`monty onto add`).")
    c.execute("INSERT OR REPLACE INTO answers (question_id, word_name) VALUES (?,?)",
              (qid, word))
    if conn is None:
        c.commit()
    return f"answers  {qid} ← {word}"


def questions() -> list[dict]:
    conn = connect(readonly=True)
    if not _has(conn):
        return []
    rows = [dict(r) for r in conn.execute("SELECT * FROM question ORDER BY asked_at")]
    for r in rows:
        r["answered_by"] = [x[0] for x in conn.execute(
            "SELECT word_name FROM answers WHERE question_id=? ORDER BY word_name", (r["id"],))]
    return rows


def coverage() -> dict:
    """Both directions, and honest about what it cannot say."""
    from .db import words

    qs = questions()
    vocab = [w["name"] for w in words()]
    if not qs:
        return {"questions": 0, "words": len(vocab), "unanswered": [],
                "unmotivated": [],
                "note": ("no competency questions recorded, so nothing can be "
                         "said about whether this vocabulary answers anything. "
                         "`monty onto ask \"…\"` — or run the intake.")}
    answered = {w.lower() for q in qs for w in q["answered_by"]}
    return {
        "questions": len(qs), "words": len(vocab),
        "unanswered": [q for q in qs if not q["answered_by"]],
        "unmotivated": sorted(w for w in vocab if w.lower() not in answered),
        "note": "",
    }


# Words that name a THING rather than describe one — what an intake answer is
# mined for. Deliberately crude: this proposes, a person commits, and a
# generous proposal that gets edited beats a clever one that gets trusted.
_STOP = {"the", "a", "an", "and", "or", "of", "to", "for", "with", "that", "this",
         "our", "we", "it", "is", "are", "in", "on", "by", "as", "they", "them"}


def harvest(answers: dict) -> list[dict]:
    """Draft competency questions from what the intake was told.

    Proposes, never writes — the same rule `gen` follows. An intake answer names
    the things the system is about; the question that follows is whether the
    vocabulary can name them, and only a person can say whether that was the
    question they meant.
    """
    drafts: list[dict] = []
    seen: set[str] = set()

    def add(text: str, why: str) -> None:
        if _id(text) not in seen:
            seen.add(_id(text))
            drafts.append({"text": text, "from": why, "id": _id(text)})

    for key in ("central_things", "users", "argued_word"):
        raw = str(answers.get(key, "") or "")
        for chunk in re.split(r"[,\n;/]| and ", raw):
            term = chunk.strip().strip(".").lower()
            if not term or len(term) < 3 or term in _STOP or len(term.split()) > 3:
                continue
            add(f"What do we call {term}, and does it mean one thing?", key)

    banned = str(answers.get("banned_words", "") or "").strip()
    if banned:
        add("For every word we decided not to use, does the ledger say what to "
            "say instead?", "banned_words")
    return drafts
