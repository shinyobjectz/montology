---
name: montology
description: A repo's vocabulary as a database, enforced against the code by a tree-sitter scan — in every language it declares (Python, TypeScript/JS, Go, Rust, Swift, Java, Ruby, Elixir, C/C++, and more). Use BEFORE naming anything in code — a class, struct, function, type, module, table, column, endpoint, event, env var, CLI flag or plain concept; when two names collide or mean two things; when a rename must propagate through the tree; when building a vocabulary out of what a codebase already declares; when setting montology up in a repo for the first time; and for design tokens, which are one kind of word among many rather than the point. Triggers on montology / monty / ontology / vocabulary / naming / "what do we call this" / drift.
---

# Montology: the vocabulary is a database

One idea: a repo's words live in `.monty/ontology.db`, prose renders FROM
it, and a scan enforces it against the code. A vocabulary kept in prose
stays correct only as long as someone remembers it; this one has a gate.

**Scope — read this before anything else.** Montology is about EVERY named
thing in a codebase, in every language it parses: classes, structs,
protocols, functions, methods, types, modules, actors, traits, enums, and
the domain concepts behind them. Backend, infra, data models, CLIs and
games are as much its subject as any UI. Design tokens (colors, spacing,
radii) are in here because a hex code is a word that means one thing — one
KIND of word, at the end of a list, not the reason montology exists. If
you arrived here from a naming question about non-visual code, you are in
exactly the right place; ignore the design section entirely.

## Start here: which situation are you in?

| The repo… | Do this |
|---|---|
| has no `.monty/` yet | **[A] Set it up** — below. Do not start authoring words first. |
| has `.monty/` but few or no words | **[B] Build the vocabulary** — the `intake` skill. |
| has a vocabulary already | **[C] Work the contract** — check, author, lint. |
| is unfamiliar and you need orientation | `monty explain` — the one-shot X-ray, then come back. |

Run `monty doctor` if you are not sure which — it names what is missing
and the repair for each.

---

## [A] Setting montology up in a repo

`monty init` is seconds and merge-safe: it writes `.monty/` (an empty
database + `montology.toml`), and wires the agent harnesses it detects —
a marked section appended to `CLAUDE.md`/`AGENTS.md`, one key merged into
`.mcp.json` and `.cursor/mcp.json`, and the pre-write guard hook into
`.claude/settings.json` and `.cursor/hooks.json`. It never overwrites a
file it did not author.

**Ask before you run it.** These are decisions the repo's owners make,
not defaults you should pick for them:

1. **How strict?** Advisory (findings only) or enforced (fails the build
   and blocks agent writes). Start advisory on an existing codebase with
   no vocabulary yet — an enforced gate over an empty database has
   nothing to say, and an enforced gate over a freshly-mined one says too
   much at once.
2. **Where does the vocabulary come from?** Three answers, and they
   compose: mined from the code (`monty scan --candidates`), asked of the
   people who own it (the `intake` skill), or inherited from an org
   ontology (`monty init --from <git-url|path>`). Ask which exist.
3. **Which trees are in scope?** A monorepo usually wants `[scan]
   exclude` for generated code, vendored trees and fixtures — otherwise
   the first candidate list is dominated by code nobody writes.
4. **Is there an org ontology to inherit?** If another repo already ran
   montology, pull it rather than re-deciding the same words.

Then: `monty init`, `monty explain` (orient), and go to [B].

## [B] Building a vocabulary from a codebase

Two sources, and the good ontologies use both:

- **What the code asks for** — `monty scan --candidates 20` mines
  recurring declared names with no word. That is raw material for
  building an ontology FROM a codebase instead of imposing one on it.
  Define the load-bearing ones; skip the noise.
- **What the people mean** — the **`intake` skill**: phased questions
  served as a form to the people who own the code, answers back on disk,
  each round written from the last and from the scan. Use it whenever the
  meanings are not recoverable from the code alone, which is most of the
  time. It closes with `monty onto add`, never with prose.

## [C] The contract, in order

1. **Check before naming anything.** `monty onto check <name>` (or the
   `ontology_check` tool). FREE means yours; TAKEN shows the definition
   you would collide with; RULED shows what to say instead.
2. **Author deliberately.** `monty onto add <name> "<definition>"
   --test "<one-line what-is-it>" --code <dotted>` — refused with findings
   if taken. One word means one thing; a dotted code lives inside the word
   owning its prefix (`har.cell` needs `har`).
   **Correct it with `monty onto amend <name> --definition "<corrected>"
   --why "<what changed>"`** (also `--test --note --code --owner`) when a
   later ruling narrows a word or its test was written loosely: the name
   and its history stay, the text it replaced is ledgered and recoverable,
   and an unknown name or an amendment that changes nothing is refused.
   Never `UPDATE` the database by hand — that is the drift the gate exists
   to catch.
3. **The gate runs in CI.** `monty lint` fails on: a declaration named
   after a word that means something else (collision), one value-typed
   word declared as two different values (divergence), a code prefix that
   resolves to nothing, and generated prose gone stale behind the db.
   Every FAIL carries its repair. A collision is judged on what the word
   NAMES (`--pos verb|noun|value`): a verb doing ordinary work below the
   surface is not a second meaning, while a noun answering for a second
   thing is the defect. One you decide to keep is `monty onto except WORD
   --where "lib/**" --why "…"` — ledgered, scoped, and reasoned. It never
   silences a divergence: sharing a name is a decision, meaning two things
   is not.
4. **Never hand-edit the words skill.** It is GENERATED; `monty sync`
   re-renders it after any change (onto add/amend/rule do this themselves),
   and lint fails on any file that differs from what the database renders.
   Past its budget the render TIERS rather than truncating: the page keeps
   the words and the rulings, and hands the rest to `references/*.md`
   beside it — read one when you are working in its area. Nothing is ever
   lost to compaction; `monty onto check <name>` answers in full for any
   single word without reading a page at all.

## Settings: montology is tuned, not taken as given

Everything is in `.monty/montology.toml`. `monty config` reads and writes
it (`monty config` lists every key with its value, source and effect;
`monty config <key> <value>` sets one, refusing an unknown key or an
invalid value with the allowed set). Change a setting when the gate is
saying the wrong thing — do not work around it, and do not silence a
finding you have not read.

| key | values | what it does |
|---|---|---|
| `guard.names` | `block` · `warn` · `off` | the pre-write firewall on names. Retired words block regardless. |
| `guard.design` | `block` · `warn` · `off` | the firewall on rogue design values; only fires once tokens exist. |
| `scan.collisions` | `advisory` · `enforce` | whether a code/vocabulary collision FAILS or merely reports. |
| `scan.enforced_kinds` | list of `core` `inner` `adopted` `custom` | which word kinds a declaration may not be named after. |
| `scan.exclude` | globs | trees the scan must not read — generated code, vendored, fixtures. |
| `scan.include` | paths | extra roots to read, including hidden ones. |
| `design.enforce` | `true` · `false` | promote design findings from advisory to law. |

**The staged adoption that works:** everything advisory → mine and author
the load-bearing words → `scan.collisions = "enforce"` → tokens defined →
`design.enforce = true`. Turning it all on at once over an untended repo
produces a wall of findings nobody reads, which teaches the team the gate
is noise.

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
  `--json` is the dashboard shape; `--strict` exits 1 unless TENDED (CI).
- `monty drift [--csv]` — history curves: lexicon, palette, convergence.
  A palette growing super-linearly or a `new` column that never decays
  is untended meaning; cite the rows, never estimate.
- `monty guard --stats` — repair-following measured from the hook log.

## The firewall (the guard)

`monty init` installs a pre-write hook in every harness it wires: every
proposed Write/Edit is linted in milliseconds BEFORE the file lands.
Retired words always block; enforced collisions block; rogue colors block
with the nearest token as the repair. If your edit is denied, READ THE
REPAIR AND APPLY IT — use the named token/word and retry; do not work
around the hook. It fails open outside montology workspaces. `monty
guard` is the entry (JSON on stdin, exit 2 = deny).

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

## The taxonomy library: don't invent what an industry already agreed

`monty onto sources [core|extra|evaluate|skip]` (or `ontology_sources`)
lists the public taxonomies montology has vetted — IAB, Google Product
and Topics, Schema.org, Shopify, NAICS/SIC, Harvard's trade and
occupation classifications and more, across advertising, retail, finance,
news and government. Consult it BEFORE authoring a word in a domain that
already has a standard: joining one beats minting a synonym, and
`monty onto collide <term> <system> …` records whose word it is.

Each entry carries the licence AS PUBLISHED and a commercial verdict.
**Relay both with any recommendation** — three of the five `core` entries
are CC BY 3.0 and need attribution (their repo has no LICENSE file, so
every automated scan calls them unlicensed), `schemaorg` is share-alike,
and anything marked `verify` has terms montology could not establish.
Never present a `verify` or a `skip` as safe to ship against.

## Structural search

`monty grep '<pattern>' --lang <language>` runs ast-grep: patterns parse,
so `def $F($$$)` finds function shapes, not text that looks like them.
Use it to find every usage of a word-bearing symbol before renaming.

## What the scan reads

Declarations are read per language from a tree-sitter query map. Covered
today: Python, JavaScript, TypeScript, TSX, Go, Rust, Swift, Java, Ruby,
Elixir, C and C++. A language whose extension is recognised but whose
query map is unwritten (Kotlin, C#, PHP, Lua) is COUNTED AS SKIPPED and
said to be skipped — never silently reported as clean. `monty surface`
prints the skipped counts; if the language you care about is in that
list, say so rather than reporting a clean scan.

## Design values are vocabulary too

The last section, and deliberately so: this is one kind of word, not the
subject. A hex code is a word that means one thing. `monty design scan`
measures the style surface (CSS/SCSS structurally, className strings,
inline styles and `style={{…}}` objects, Tailwind arbitrary escapes);
`monty design candidates` lists the most-used unnamed values,
adoption-ready; `monty design token <name> <category> <value>` names one
(one name, one value — same contract as words). With tokens defined,
`monty lint` reports drift: rogue literals WITH their nearest token named
(`#06191b … nearest: brand-primary #061a1c (Δ2)`), near-duplicate colors
doing one job, classes used but defined nowhere, and every arbitrary
value that left the scale. Advisory until `design.enforce = true` —
promote the law once the tokens are real. A repo with no UI never needs
this section.

## Rules

- A word means one thing. If it cannot, pick a different word.
- Vendors are not vocabulary — tools you buy belong in code, never in a
  sentence about what the system means.
- At a framework's boundary, speak the framework's word; record the
  collision ruling (`monty onto rule`) so the choice is findable.
- Errors are data with the repair attached — relay repairs, do not
  improvise workarounds.
