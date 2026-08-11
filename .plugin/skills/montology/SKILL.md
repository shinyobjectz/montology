---
name: montology
description: Design-system and vocabulary drift for this repo — the Tailwind theme as enforced tokens, rogue values with nearest-token receipts, words as a database checked before naming anything, org ontologies inherited across repos, and token-precise renames. Use when naming things, when styles or concepts have drifted, when adopting a design system, or when propagating a rename.
---

# Montology: the vocabulary is a database

One idea: a repo's words live in `.monty/ontology.db`, prose renders FROM
it, and a scan enforces it against the code. A vocabulary kept in prose
stays correct only as long as someone remembers it; this one has a gate.

## The contract, in order

1. **Check before naming anything.** `monty onto check <name>` (or the
   `ontology_check` tool). FREE means yours; TAKEN shows the definition
   you would collide with; RULED shows what to say instead.
2. **Author deliberately.** `monty onto add <name> "<definition>"
   --test "<one-line what-is-it>" --code <dotted>` — refused with findings
   if taken. One word means one thing; a dotted code lives inside the word
   owning its prefix (`har.cell` needs `har`).
3. **Let the code ask for words.** `monty scan --candidates` mines
   recurring declared names with no word — that is the raw material for
   building an ontology FROM a codebase instead of imposing one on it.
   Define the load-bearing ones; skip the noise.
4. **The gate runs in CI.** `monty lint` fails on: a declaration named
   after a word that means something else (collision), a code prefix that
   resolves to nothing, and generated prose gone stale behind the db.
   Every FAIL carries its repair. An exception you decide to keep is
   recorded in `.monty/montology.toml` `[scan] allow` — a decision, not
   a silence.
5. **Never hand-edit the words skill.** It is GENERATED; `monty sync`
   re-renders it after any change (onto add/rule do this themselves).

## One ontology, every repo

`monty onto pull <git-url|path|.db-url>` inherits the ORG vocabulary
(pinned in montology.toml after the first pull; `monty init --from <src>`
does both at once). Upstream rows refresh on every pull; this repo's own
words always survive; conflicts are loud and local wins. When upstream
renames a word, the pull prints the exact `monty migrate` command — run
it on a clean tree.

## Meaning over time (vitals · drift · guard --stats)

- `monty vitals` — run FIRST when asked "how is this repo doing": one
  verdict (TENDED / DRIFTING / UNTENDED), each reason with its repair.
- `monty drift [--csv]` — history curves: lexicon, palette, convergence.
  A palette growing super-linearly or a `new` column that never decays
  is untended meaning; cite the rows, never estimate.
- `monty guard --stats` — repair-following measured from the hook log.

## The firewall (the guard)

`monty init` installs a PreToolUse hook: every proposed Write/Edit is
linted in milliseconds BEFORE the file lands. Retired words always
block; enforced collisions block; rogue colors block with the nearest
token as the repair. If your edit is denied, READ THE REPAIR AND APPLY
IT — use the named token/word and retry; do not work around the hook.
It fails open outside montology workspaces. `monty guard` is the entry
(JSON on stdin, exit 2 = deny).

## The X-ray

`monty explain` — the one-shot anatomy of any repo: surface, vocabulary
had and asked-for, semantic clusters vs directory structure, design
system, contradictions — straight to the terminal. Run it FIRST on an
unfamiliar codebase — it is the fastest orientation montology offers.

## Rulings: how arguments end

- **Overload** — `monty onto rule <dont-say> <say> "<why>"`: from now on,
  X is said as Y; `onto check X` answers with the ruling.
- **Collision** — `monty onto collide <term> <system> "<their meaning>"
  "<ruling>"`: at a framework's boundary, record whose word it is and
  which side moved, so the choice is inherited, never re-argued.
- **Rename** — `monty onto rename <was> <now> "<why>"`: the word row
  moves, the old name retires (blocked from re-use), the ledger keeps old
  material readable — and the sweep immediately shows where the CODE
  still says the old name.

## Migration: the code catches up

`monty migrate <was> <now>` sweeps every case variant (snake, Pascal,
UPPER) by TOKEN through the tree-sitter parse — every position a name
occupies, in every covered language, with strings and comments
structurally untouchable. `--apply` rewrites; do it on a clean git tree
and review the diff. Montology never edits code silently.

## Design values are vocabulary too

A hex code is a word that means one thing. `monty design scan` measures
the style surface (CSS/SCSS structurally, className strings, inline
styles and `style={{…}}` objects, Tailwind arbitrary escapes);
`monty design candidates` lists the most-used unnamed values,
adoption-ready; `monty design token <name> <category> <value>` names one
(one name, one value — same contract as words). With tokens defined,
`monty lint` reports drift: rogue literals WITH their nearest token named
(`#06191b … nearest: brand-primary #061a1c (Δ2)`), near-duplicate colors
doing one job, classes used but defined nowhere, and every arbitrary
value that left the scale. Advisory until `[design] enforce = true` in
montology.toml — promote the law once the tokens are real.

## Semantic hearing (the [semantics] extra)

String laws enforce one-word-one-meaning; the semantic audit hears the
DUAL — one meaning, one word — which no string check can. POTION static
embeddings (~30 MB, numpy-only) power it:

- `monty onto similar "<name or definition>"` — run BEFORE authoring:
  the meaning may already have a word.
- `monty onto audit` — advisory always: two words defined into one
  meaning, a local word doubling an inherited org word, candidates that
  are secretly existing words, owner groupings that do not match where
  meanings actually cluster. Threshold 0.70, calibrated live (distinct
  words score ≤0.49 pairwise; a real duplicate scored 0.74).
- A cosine score is an instrument's hint — only a ruling (merge, rename,
  re-own) makes it vocabulary.

## Structural search

`monty grep '<pattern>' --lang <language>` runs ast-grep: patterns parse,
so `def $F($$$)` finds function shapes, not text that looks like them.
Use it to find every usage of a word-bearing symbol before renaming.

## Rules

- A word means one thing. If it cannot, pick a different word.
- Vendors are not vocabulary — tools you buy belong in code, never in a
  sentence about what the system means.
- At a framework's boundary, speak the framework's word; record the
  collision ruling (`monty onto rule`) so the choice is findable.
- Errors are data with the repair attached — relay repairs, do not
  improvise workarounds.
