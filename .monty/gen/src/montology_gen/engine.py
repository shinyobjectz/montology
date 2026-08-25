"""The engine: three verbs, each honest about what it is.

  * ``gen_word`` — GENERATIVE: a one-line definition drafted on the atomic
    tier (or a served model), law-checked, refused if it cannot comply.
    Refused means NOT written; `monty onto add` is always the human lane.
  * ``sync`` — DETERMINISTIC: the words skill rendered from the database.
    No model, ever — prose is output here, the db is the source.
  * ``lint`` — the gate: the generated skill parses, fits its budgets, and
    matches the database it claims to render (the drift law); this
    package's own source carries no prompt-shaped strings.

Rendering is TIERED, because the resident page is context every agent pays
for on every turn. See `LADDER`: the ontology renders full while it fits,
and demotes in a fixed order once it does not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path

from montology_core import workspace_root
from montology_ontology import check as onto_check
from montology_ontology import record_run

from ._session import gen_session, tiny_session
from .instruments import fingerprint, parse_frontmatter, vocabulary
from .laws import (BODY_CAP, PAGE_CAP, STRUCTURAL, Law, body_cap,
                   provenance_current, word_laws)

SKILL_REL = Path(".claude") / "skills" / "words" / "SKILL.md"
REFS_REL = SKILL_REL.parent / "references"


def _check(text: str, laws: tuple[Law, ...]) -> list[str]:
    return [f"{law.name}: {why}" for law in laws if (why := law.check(text))]


def _model_of(session) -> str:
    try:
        return str(getattr(session.backend, "model_id", "unknown"))
    except Exception:  # noqa: BLE001
        return "unknown"


def gen_word(name: str, context: str = "") -> str:
    """Draft one definition. THE TINY TIER: a one-line definition is atomic
    work, exactly what a 270M model holds. Bodies never route here."""
    session = tiny_session() or gen_session()
    if isinstance(session, str):
        return session

    from .stubs import define_word

    existing = [w["name"] for w in vocabulary()["words"]]
    laws = word_laws(onto_check)
    try:
        line = define_word(session, name=name,
                           usage_context=context or f"this codebase's ontology; the word {name}",
                           existing_words=existing)
    except Exception as e:  # noqa: BLE001
        record_run("word", name, _model_of(session), "errored", [type(e).__name__])
        return (f"the model could not produce a definition ({type(e).__name__}). "
                "Repair: retry, or define it yourself with `monty onto add`.")
    failures = _check(str(line), laws)
    if failures:
        record_run("word", name, _model_of(session), "refused", failures)
        return "REFUSED — the definition could not satisfy its laws:\n  " + "\n  ".join(failures)
    record_run("word", name, _model_of(session), "accepted", [])
    return (f"{str(line).strip()}\n\n(accept it with: monty onto add "
            f"\"{name}\" \"<the definition above>\" — gen proposes, you commit)")


# ── disclosure: what the resident page keeps, and what it points at ─────────

GIST_CAP = 170          # a definition's first sentence, at a word boundary


# Where a definition's first clause ends. The minimum length is what keeps an
# abbreviation ("e.g. ", "i.e. ") from being read as the end of the sentence —
# a gist that is three characters long is not a gist.
CLAUSE_END = re.compile(r"\. |; | — ")
CLAUSE_MIN = 12


def gist(text: str, cap: int = GIST_CAP) -> str:
    """A definition's one-sentence form. Deterministic — the first clause, cut
    at a word boundary if that is still long. Never a model: a gist is a
    shorter rendering of an authored definition, never a new claim."""
    head = text.strip()
    for m in CLAUSE_END.finditer(head):
        if m.start() >= CLAUSE_MIN:
            head = head[:m.start()]
            break
    head = head.rstrip(" .;—")
    if len(head) <= cap:
        return head
    return head[:cap].rsplit(" ", 1)[0] + "…"


@dataclass(frozen=True, slots=True)
class Plan:
    """How much of the ontology a render keeps resident.

    Every field is a knob the LADDER turns, in order, until the body fits its
    disclosure budget. A small vocabulary never leaves the defaults: the page
    that fits is rendered whole.
    """
    renames: str = "resident"      # resident | referenced
    adopted: str = "full"          # full | gist
    collisions: str = "full"       # full | compact
    doctrine: str = "full"         # full | titles
    words: str = "full"            # full | gist
    split: bool = False            # words move to a page per area, the map stays


# Ordered by what each step costs the reader. Renames go first because they
# cost nothing: the guard blocks a retired name at write time and the error
# carries the repair, so the ledger was never what enforced them. Our own
# words shorten LAST — they are the reason the skill exists.
LADDER: tuple[tuple[str, str, str], ...] = (
    ("renames", "referenced",
     "the guard blocks a retired name at write time — the ledger enforces nothing here"),
    ("adopted", "gist",
     "adopted words carry their source's prose; one sentence resident, the full text a page away"),
    ("collisions", "compact",
     "the ruling stays resident, the argument moves"),
    ("doctrine", "titles",
     "a doctrine's title is its claim; the argument moves"),
    ("words", "gist",
     "our own definitions shorten to their first sentence"),
    ("split", True,
     "the words move to a page per area; the map of areas stays"),
)


def _area(w: dict) -> str:
    """Which reference page a word belongs on: the word that owns it, else
    its kind. Owner first because a namespace is how a reader navigates; kind
    is the fallback for a flat vocabulary, where 'adopted' IS the area."""
    return w["owner"] or w["kind"]


def _word_rows(words: list[dict]) -> list[str]:
    """The full table — dropping any column no word in this ontology fills.
    A column of em-dashes is markup that costs context and carries nothing."""
    has_code = any(w["code"] for w in words)
    has_test = any(w["test"] for w in words)
    head = ["word"] + (["code"] if has_code else []) + ["kind", "is"] + (["test"] if has_test else [])
    rows = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for w in words:
        owner = f" (inside **{w['owner']}**)" if w["owner"] else ""
        cells = [f"**{w['name']}**{owner}"]
        if has_code:
            cells.append(f"`{w['code']}`" if w["code"] else "—")
        cells.append(w["kind"] + (f" · {w['pos']}" if w.get("pos") else ""))
        cells.append(w["definition"])
        if has_test:
            cells.append(w["test"] or "—")
        rows.append("| " + " | ".join(cells) + " |")
    return rows


def _gist_rows(words: list[dict]) -> list[str]:
    """The compact form: name, where it lives, one sentence. The full text is
    always one `monty onto check <name>` away, so nothing is lost — only
    moved off the surface every agent loads."""
    out = []
    for w in words:
        owner = f" *(in {w['owner']})*" if w["owner"] else ""
        out.append(f"- **{w['name']}**{owner} — {gist(w['definition'])}")
    return out


def _render_words(words: list[dict], plan: Plan) -> tuple[list[str], dict[str, list[str]]]:
    """The resident words section, plus whatever it hands to reference pages."""
    pages: dict[str, list[str]] = {}
    if not words:
        return (["## No words yet",
                 "",
                 "This ontology is empty. Author the first word with",
                 "`monty onto add <name> \"<definition>\"` — check-first: a taken",
                 "name is refused with findings. `monty scan --candidates` lists",
                 "the recurring declared names the codebase is asking for.", ""], pages)

    if plan.split:
        lines = ["## The words", "",
                 f"{len(words)} words across {len({_area(w) for w in words})} areas. Each page below "
                 "carries its area in full — read the one you are working in, or ask the",
                 "database for any single word: `monty onto check <name>`.", "",
                 "| area | words | in full |", "|---|---|---|"]
        for area in sorted({_area(w) for w in words}):
            here = [w for w in words if _area(w) == area]
            names = ", ".join(w["name"] for w in here)
            page = f"words-{area}.md"
            lines.append(f"| **{area}** ({len(here)}) | {names} | `references/{page}` |")
            pages[page] = [f"# {area} — {len(here)} words", ""] + _word_rows(here) + [""]
        return lines + [""], pages

    ours = [w for w in words if w["kind"] != "adopted"]
    adopted = [w for w in words if w["kind"] == "adopted"]

    lines = ["## The words", ""]
    if plan.adopted == "gist" and adopted:
        shown = ours
        lines += (_word_rows(shown) if plan.words == "full" else _gist_rows(shown)) + [""]
        lines += [f"### Adopted — {len(adopted)} words taken from elsewhere", "",
                  "One sentence each; the full definitions and tests are in",
                  "`references/adopted.md`, and `monty onto check <name>` answers for any one.",
                  ""] + _gist_rows(adopted) + [""]
        pages["adopted.md"] = ([f"# Adopted words — {len(adopted)}", "",
                                "Taken from elsewhere and spoken here as-is.", ""]
                               + _word_rows(adopted) + [""])
    else:
        lines += (_word_rows(words) if plan.words == "full" else _gist_rows(words)) + [""]
    return lines, pages


def _render_collisions(rulings: list[dict], plan: Plan) -> tuple[list[str], dict[str, list[str]]]:
    if not rulings:
        return [], {}
    head = ["## Collisions, ruled on", "",
            "At a framework's boundary, speak the framework's word. Where "
            "names collide, the ruling below says which side moved — "
            "inherit the decision, not the argument.", ""]
    if plan.collisions == "full":
        for c in rulings:
            head += [f"**`{c['term']}`** ({c['theirs']}) — their meaning: "
                     f"{c['their_meaning']}", "",
                     f"{c['ruling']} *(decided {c['decided']})*", ""]
        return head, {}

    head += [f"The rulings in full, with what each framework's word means, are in "
             f"`references/collisions.md`.", "",
             "| term | theirs | the ruling |", "|---|---|---|"]
    for c in rulings:
        head.append(f"| `{c['term']}` | {c['theirs']} | {gist(c['ruling'])} |")
    page = [f"# Collisions, ruled on — {len(rulings)}", ""]
    for c in rulings:
        page += [f"**`{c['term']}`** ({c['theirs']}) — their meaning: {c['their_meaning']}", "",
                 f"{c['ruling']} *(decided {c['decided']})*", ""]
    return head + [""], {"collisions.md": page}


def _render_renames(renames: list[dict], plan: Plan) -> tuple[list[str], dict[str, list[str]]]:
    if not renames:
        return [], {}
    if plan.renames == "resident":
        lines = ["## Renamed — what older material means", "",
                 "| was | is | when | why |", "|---|---|---|---|"]
        for r in renames:
            lines.append(f"| {r['was']} | **{r['now']}** | {r['renamed_on']} | {r['why'] or ''} |")
        return lines + [""], {}

    page = [f"# Renamed — {len(renames)} retired names", "",
            "The ledger older material is read through.", "",
            "| was | is | when | why |", "|---|---|---|---|"]
    for r in renames:
        page.append(f"| {r['was']} | **{r['now']}** | {r['renamed_on']} | {r['why'] or ''} |")
    return (["## Renamed", "",
             f"{len(renames)} names have been retired. **The guard blocks every one of them "
             "at write time**, with the current word in the error — you do not need them in "
             "mind to be stopped. The ledger, for reading older material: "
             "`references/renamed.md`.", ""],
            {"renamed.md": page + [""]})


def _render_doctrine(doctrine: list[dict], plan: Plan) -> tuple[list[str], dict[str, list[str]]]:
    if not doctrine:
        return [], {}
    if plan.doctrine == "full":
        lines = []
        for d in doctrine:
            lines += [f"## {d['title']}", "", d["body"], ""]
        return lines, {}

    lines = ["## Doctrine — the decisions, in one line each", "",
             "The title is the decision; the argument for it is in `references/doctrine.md`.", ""]
    page = ["# Doctrine", ""]
    for d in doctrine:
        lines.append(f"- **{d['title']}** — {gist(d['body'])}")
        page += [f"## {d['title']}", "", d["body"], ""]
    return lines + [""], {"doctrine.md": page}


def _render(repo_name: str, vocab: dict, plan: Plan, cap: int) -> tuple[str, dict[str, str]]:
    """One rendering at one plan. Deterministic in (vocabulary, plan, cap)."""
    words, doctrine, rulings = vocab["words"], vocab["doctrine"], vocab["overloads"]
    pages: dict[str, list[str]] = {}

    def take(rendered):
        body, produced = rendered
        pages.update(produced)
        return body

    lines = [
        "---",
        "name: words",
        f"description: {repo_name}'s vocabulary — every defined word, its code and its "
        "test. GENERATED from .monty/ontology.db by `monty sync`; never hand-edit. "
        "Check `monty onto check <name>` BEFORE naming anything.",
        "---",
        "",
        "> **GENERATED FILE.** The database at `.monty/ontology.db` is the truth;",
        "> this renders from it. Hand edits are lost on the next sync — change the",
        "> database instead (`monty onto add`), which is also what `monty lint` verifies.",
        "",
        f"<!-- GENERATED by monty gen sync instruments=sha256:{fingerprint(vocab, cap)} -->",
        "",
    ]
    lines += take(_render_words(words, plan))

    if rulings:
        lines += ["## Overloaded — say the right one", "",
                  "| do not say | say | why |", "|---|---|---|"]
        for o in rulings:
            lines.append(f"| {o['dont_say']} | **{o['say']}** | {o['why'] or ''} |")
        lines.append("")

    if vocab["tokens"]:
        lines += ["## Design tokens", "",
                  "One name, one value — the style lint aligns the code to these.",
                  "", "| token | category | value |", "|---|---|---|"]
        for t in vocab["tokens"]:
            lines.append(f"| **{t['name']}** | {t['category']} | `{t['value']}` |")
        lines.append("")

    lines += take(_render_collisions(vocab["collisions"], plan))

    if vocab.get("exceptions"):
        lines += ["## Excepted — symbols that may share a word's name", "",
                  "A recorded decision, not a loophole: the reason and the place are "
                  "the whole point. An exception says a SYMBOL may share the name; it "
                  "never says the name may mean two things.", "",
                  "| word | where | as | why |", "|---|---|---|---|"]
        for e in vocab["exceptions"]:
            where = "tree-wide" if e["scope"] == "**" else f"`{e['scope']}`"
            lines.append(f"| **{e['word']}** | {where} | {e['judged'] or '—'} | {e['why']} |")
        lines.append("")

    lines += take(_render_renames(vocab["renames"], plan))
    lines += take(_render_doctrine(doctrine, plan))

    if pages:
        lines += ["## What is not on this page", "",
                  "These are NOT loaded with this skill. Read one when you are working in "
                  "its area — and the database answers for any single word without reading "
                  "anything: `monty onto check <name>`, `monty onto list`.", ""]
        for name in sorted(pages):
            lines.append(f"- `references/{name}`")
        lines.append("")

    lines += [
        "## Rules",
        "",
        "1. Before naming ANYTHING — a class, a concept, a tag: `monty onto check <name>`.",
        "2. A word means one thing. If it cannot, pick a different word.",
        "3. Vendors are not vocabulary — tools you buy belong in code, never in a",
        "   sentence about what the system means.",
        "4. A dotted code lives inside the word owning its prefix.",
        "5. A collision is judged on what the word NAMES. A verb doing ordinary work",
        "   below the surface is not a second meaning; a noun or a value type answering",
        "   for a second thing is the defect. Keep one deliberately with",
        "   `monty onto except WORD --where \"…\" --why \"…\"`.",
        "",
    ]
    stamp = f"<!-- GENERATED by monty gen sync instruments=sha256:{fingerprint(vocab, cap)} -->"
    rendered = {name: stamp + "\n\n" + "\n".join(body) for name, body in pages.items()}
    return "\n".join(lines), rendered


def render_pages(repo_name: str) -> tuple[str, dict[str, str], list[str]]:
    """The whole disclosure tree: the resident page, the reference pages, and
    what had to be demoted to make the resident one fit.

    The ladder is walked, not chosen: a vocabulary that fits renders whole, and
    one that does not gives up the cheapest thing first. Sync never truncates
    silently — every step taken is reported, and the page itself says what it
    is pointing at.
    """
    vocab = vocabulary()
    cap, _ = body_cap()
    plan, demoted = Plan(), []

    text, pages = _render(repo_name, vocab, plan, cap)
    for field, value, why in LADDER:
        _, body = parse_frontmatter(text)
        if len(body) <= cap:
            break
        plan = replace(plan, **{field: value})
        demoted.append(f"{field}: {why}")
        text, pages = _render(repo_name, vocab, plan, cap)
    return text, pages, demoted


def render_words_skill(repo_name: str) -> str:
    """The words skill, rendered from the database. Deterministic."""
    return render_pages(repo_name)[0]


def sync(write: bool = True) -> str:
    """Render the disclosure tree into the workspace. The only writer of it."""
    ws = workspace_root()
    text, pages, demoted = render_pages(ws.name)
    if not write:
        return text

    target = ws / SKILL_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)

    refs = ws / REFS_REL
    if pages:
        refs.mkdir(parents=True, exist_ok=True)
    for name, body in pages.items():
        (refs / name).write_text(body)
    # a page this render did not produce is a page the ontology no longer has
    if refs.exists():
        for stale in refs.glob("*.md"):
            if stale.name not in pages:
                stale.unlink()

    v = vocabulary()
    cap, _ = body_cap()
    _, body = parse_frontmatter(text)
    note = (f"synced {SKILL_REL} ({len(v['words'])} words"
            + (f", {len(v['tokens'])} tokens" if v["tokens"] else "")
            + f") — {len(body):,}/{cap:,} chars resident")
    if pages:
        note += f", {len(pages)} reference page{'s' if len(pages) > 1 else ''}"
    for step in demoted:
        note += f"\n  demoted {step}"
    return note


def lint() -> list[str]:
    """Deterministic, model-free, exit-code-shaped. In the check gate."""
    ws = workspace_root()
    report: list[str] = []
    failed = False

    target = ws / SKILL_REL
    expected, pages, demoted = render_pages(ws.name)
    cap, why = body_cap()

    if target.exists():
        text = target.read_text()
        current = fingerprint(vocabulary(), cap)
        laws = STRUCTURAL + (provenance_current(current),)
        for f in _check(text, laws):
            failed = True
            report.append(f"FAIL {SKILL_REL}: {f}")
        if text != expected:
            failed = True
            report.append(f"FAIL {SKILL_REL}: HAND-EDITED — the file differs from what the "
                          f"database renders. Prose is rendered, never authored. "
                          f"Repair: `monty sync` (your edit is lost; put it in the db instead)")
    else:
        report.append(f"note: {SKILL_REL} not rendered yet — `monty sync` writes it")

    # the reference pages: same truth, same gate — a tree of generated files is
    # more surface to hand-edit, not less
    refs = ws / REFS_REL
    on_disk = {p.name for p in refs.glob("*.md")} if refs.exists() else set()
    for name, body in pages.items():
        path = refs / name
        if not path.exists():
            failed = True
            report.append(f"FAIL {REFS_REL / name}: linked but missing — `monty sync`")
        elif path.read_text() != body:
            failed = True
            report.append(f"FAIL {REFS_REL / name}: HAND-EDITED or stale — `monty sync`")
        elif len(body) > PAGE_CAP:
            failed = True
            report.append(f"FAIL {REFS_REL / name}: page is {len(body)} chars; the page "
                          f"budget is {PAGE_CAP} — split the area")
    for orphan in sorted(on_disk - set(pages)):
        failed = True
        report.append(f"FAIL {REFS_REL / orphan}: linked from nothing — `monty sync` removes it")

    # the no-prompt ban, enforced where it could be broken
    for py in sorted(Path(__file__).resolve().parent.glob("*.py")):
        for bad in re.findall(r'"(You are[^"]{0,60}|Please [^"]{0,60})"', py.read_text()):
            failed = True
            report.append(f"FAIL {py.name}: prompt-shaped string {bad!r} — specs, not prompts")

    # Said every time. A budget raised once and then never mentioned is a budget
    # nobody weighs again, which is the same as not having one.
    if cap != BODY_CAP and why:
        report.append(f"note: disclosure budget raised to {cap} from {BODY_CAP} — {why}")
    # Said every time, for the same reason: what left the resident page left it
    # for a reason, and a reader who cannot see that it left cannot ask for it.
    for step in demoted:
        report.append(f"note: demoted {step}")

    report.append("gen lint: " + ("FAILED" if failed else "ok"))
    return report
