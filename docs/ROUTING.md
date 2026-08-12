# Routing, and the health of a vocabulary

> Built 2026-08-12, alongside [SURFACES.md](SURFACES.md). Where surfaces
> measure what the code stands on, this measures what the vocabulary itself
> is doing: which terms are dead, which are stubs, and which the ledger has
> already told you to stop saying.

## The gap

Montology tracked edges, and enforced one and a half of the three that
matter:

| edge | answers | before |
|---|---|---|
| word → code symbol | does anything implement this term? | enforced |
| word → dependency | what does this term actually run on? | `bearing` (SURFACES.md) |
| **word → word** | **what replaced this? where?** | **prose only** |

The third lived in the `overload` table as a sentence — `"context (for
staged data)" → "stage"` — and no machine could read the parenthetical that
made it enforceable.

## Why the parenthetical is the whole feature

Measured across `socialite`, the rulings counted naively are useless:
`context` appears 5,045 times, `output` 5,726. Nothing survives that.

But the rulings were never tree-wide claims. They read:

    workspace (for the tenant boundary)  → org
    workspace (for the tenant surface)   → Studio
    org (on the App surface)             → Studio
    Dossier (anywhere a person reads it) → Artifact

`workspace` is a **correct** word — `har.workspace`, the agent's uv/git
workspace — that is wrong in two *other* registers. These look like
contradictions only because the scope is not data. Lift it into a column and
the noise collapses:

| ruling | tree-wide | in its register |
|---|---|---|
| `Dossier` → `Artifact` (surface) | 68 | **8 files in `ui/`** |
| `artifact` → `Dossier` (code) | 62 | **7 files in `nexus/`** |

Eight files is an afternoon. Sixty-eight is a reason to stop reading.

Stated as the law this feature obeys: **a finding that cannot be scoped
cannot gate.** An unscopable route is advisory forever and says so, with the
command that would scope it. That is not a limitation to fix later; it is
what keeps the gate worth reading.

## The register

A register is a place in the repo, declared once:

```toml
# .monty/montology.toml
[registers]
surface = ["ui/*"]
code    = ["harness/*", "nexus/*", "serve/*"]
prose   = ["docs/*"]
```

`code` and `prose` can fall back to a file's kind. **`surface` never can** —
it is a claim about which part of a product a person looks at, which only the
repo knows. An undeclared `surface` therefore matches *nothing*, rather than
guessing and producing confident nonsense.

## The table

    route(from_term, to_word, register, scope, ruled_on, why, origin)

`scope` is a path glob overriding the register. A route with neither cannot
be enforced anywhere.

Two rules the build forced:

- **`all` and a named register are mutually exclusive for one pair.** `all`
  already covers `code`, so keeping both doubles every finding and makes
  scoping a route look like adding a second ruling. **Scoping is a move.**
- **A route may point at a word that does not exist.** `Artifact` was retired
  in code on 2026-08-09 and reinstated as the surface word on 2026-08-11. A
  ledger that refused that could not describe the decision. It is recorded,
  and reported as an orphan until resolved.

## Migration is a parse, not a rewrite

`monty onto route --drafts` reads the existing `overload` and `renamed`
tables and proposes routes, lifting each parenthetical into a register. On
socialite it produced 20 drafts, correctly inferring `surface` for the three
rulings that name it and leaving the rest at `all` — **which is the honest
answer.** Where the parenthetical does not name a register, the draft says so
rather than guessing; those are exactly the ones a human must scope.

    monty onto route --drafts       what your rulings already imply
    monty onto route --adopt-all    take them, then scope the 'all' ones
    monty onto route 'artifact' --to 'Dossier' --in code

## The three instruments

    monty onto stale     deprecated terms still in use, IN THEIR REGISTER
    monty onto health    every word: carried / unnamed / thin / prose-only / dead
    monty onto routes    chains, orphans, and rulings that contradict

### stale

Advisory by default; `--strict` exits 1. Deliberately **not** in `monty
lint` — the sweep is only as trustworthy as the routes are scoped, and a
repo that has just adopted its drafts has not scoped them yet.

### health

Three independent signals — a symbol carries it, the code mentions it, prose
mentions it — and the verdict names which are missing. Matching is the whole
difficulty, and getting it wrong makes the instrument lie:

- **Compare the last dotted segment.** Elixir declares `Nexus.Events.Event`;
  matching whole names reported 65 live socialite words as unimplemented.
- **Normalize spelling.** `doc_id`, `docId` and `DocId` are one name.
- **A phrase is not a symbol.** `progressive disclosure` will never be a
  class, so conceptual kinds are never judged as though it could be.

Measured on socialite: of 96 words, **2 dead** (`agent ergonomics`,
`abstracted tools and CLI`), **1 prose-only** (`subspace` / `mad.space`,
written about three times and never built), **1 thin** (`SCDP`). The
vocabulary is in far better shape than the raw counts suggested.

`dead` is reported and never flips `vitals` to untended — montology's own
sequencing seeds the vocabulary *before* the code that implements it, so a
freshly added word is dead by construction. Counting that as a failure would
punish the workflow this tool prescribes.

### routes

Pure-table findings, so no false positive is possible — these DO gate:

- **orphan** — points at a word that does not exist.
- **contradiction** — the same term sent to two words *in the same register*.
  That is disagreement, not scope.
- **cycle** — two hops whose registers **overlap**. `all` overlaps
  everything, which is what makes an unscoped ruling so blunt.

The overlap rule is what lets the Artifact case be right. Unscoped,
`artifact → Dossier` and `Dossier → Artifact` is a FAIL: the ledger forbids
the word it sends you to. Scope the first to `code` and the same pair reads:

    note route artifact → Dossier → Artifact — a bridge, not a cycle:
    code says one word, surface says the other, and the registers do not
    overlap. This is one boundary in two registers.

## Elixir

The fourth probe (see SURFACES.md). `mix.exs` for the claim; `(alias)` nodes
for the seams. The one thing worth stealing: a built dep names **one .beam
file per module**, so `_build/*/lib/<dep>/ebin/` IS the module list — exact,
and free. `:ecto_sql` provides `Ecto.Adapters.SQL`, which no camelizing of
`ecto_sql` reaches; guessing there invents a phantom out of a naming
convention. Absent `_build`, the probe falls back to camelizing and finds
fewer seams rather than inventing them.

Seam matching takes the **longest** matching prefix: `Phoenix.LiveView.Socket`
belongs to whoever owns `Phoenix.LiveView`, not to whoever owns `Phoenix`.

On socialite: 22 Elixir surfaces, 5 phantoms — `broadway`, `postgrex`,
`file_system`, `sweet_xml`, `flame` — all verified genuinely unreferenced.
`flame` appears twice in `nexus/lib/nexus/harness/fly.ex`, both times inside
a comment explaining *why it is not used*. A comment is not a seam.

## Open

- **`stale` gates nothing yet.** By design, until a repo's routes are scoped.
  The promotion path is `--strict` in CI once `unscopable` reaches zero.
- **A route's `from_term` is matched textually.** `context` in a register
  will match React's `context` too. The register narrows it; only a symbol
  resolver would settle it, and that is a much larger instrument.
- **No `--fix`.** `monty migrate` already rewrites a rename across the tree;
  pointing it at a scoped route is the obvious next step and was not built.
