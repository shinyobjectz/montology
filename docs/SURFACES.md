# Surfaces and seams

> Design, 2026-08-12; **built the same day** — the sequencing at the bottom
> records what shipped. Adds the half of the measurement montology does not
> have: not what the code declares, but what it stands on — and which of
> those things are actually connected to anything.

## The gap

`scan` measures one direction. `surface.py` says it plainly: *"Declarations,
measured: every named thing the codebase declares."* Every instrument built
on it — `lint`, `candidates`, `drift`, `vitals`, `explain` — reads that one
list.

So montology can tell you that a class collides with a word, and cannot tell
you that the word describes a library nobody imports any more. A vocabulary
kept honest against declarations still drifts freely against dependencies,
and that drift is invisible to the gate. The failure looks like this: a
manifest declares a package, a comment explains why that package is central,
the package has no call sites, and every instrument reports a tended repo.

Nothing in the current model can catch it, because nothing in the current
model knows the package exists.

## The model

**A surface is what a thing exposes** — its named, callable, importable
face. Our code has one. Every dependency has one. Whose it is, is an
attribute of the record, not a different concept, and that is the whole
reason this stays small: there is no separate vocabulary for "things we
build" and "things we buy."

**Surfaces meet at seams.** A seam is one point of contact: an import that
resolves, a call that lands, a config key that is read, a binding that is
declared and used. Direction — we call them, they call us — is an attribute
of the seam, which is where inputs, outputs and ports live without needing
words of their own.

**A surface with no seam is a phantom.** Declared, never met. That is the
finding the gate exists to produce, and it is the exact mirror of the
`candidate` montology already has: a candidate is a declaration with no
word, a phantom is a surface with no seam.

The consequence worth stating: **the seam is the evidence.** There is no
separate notion of proof-of-use, because a seam is what proof-of-use is. If
something is genuinely used there is a seam; if there is no seam, it is a
phantom. This is what keeps the vocabulary at three words.

## The words

Authored in `seed.py` (`just seed`) like every other montology word — these
are the repo's own vocabulary, not a target repo's.

```python
("surface", "core", None, "surf",
 "what a thing exposes: its named, callable, importable face — ours and a "
 "dependency's alike, whose it is being an attribute and not a second word",
 "what something offers"),
("seam", "core", "surface", "surf.seam",
 "one point where two surfaces meet — an import that resolves, a call that "
 "lands, a config key read; direction is an attribute, so inputs and outputs "
 "need no words of their own",
 "where two things touch"),
("phantom", "core", "surface", "surf.phantom",
 "a surface with no seam: declared, never met — the mirror of a candidate, "
 "which is a declaration with no word",
 "what nothing touches"),
```

`surface`, `seam` and `phantom` were each checked FREE against this repo's
ontology on 2026-08-12.

## What deliberately has no word

Recorded so it is not re-litigated from zero.

**evidence** — the seam is the evidence. A separate word would name the same
fact twice.

**the owner of a surface** (service, supplier, library, vendor, package,
reliance) — which thing a surface came from is a fact on the record, not a
concept in the vocabulary. Naming it forces a choice between words that each
cover only part of the range: a hosted service is not a library, a library is
not a vendor, and no single plain word covers all of them without stretching.
The record carries an owner string; the ontology does not carry a word for it.

**a word for the whole collection** (estate, stack, inventory) — the
collection is every surface. A word for "all the surfaces" earns nothing that
`surface` does not already say.

**a word for what we build** (part, component, piece) — unnecessary once
surface applies to our own code too. Nothing gets renamed; `surface.py`
simply stops being ours-only, which finally makes its name accurate.

**port** — BLOCKED. This repo's own `mcp_server.py` takes `--port 8848`. In a
repo that serves over a network port, port cannot mean one thing.

**a new verb** — montology's commands are already its nouns (`drift`,
`vitals`, `scan`). `monty surface` follows the pattern; `trace`, `survey` and
`audit` were considered and add nothing.

## The one existing edit

`scan` is currently:

> the tree-sitter sweep of a codebase: every declaration measured, checked
> against the vocabulary

It widens to cover dependency surfaces and the seams between them. Its test
(*"what the code claims"*) still holds — a manifest is a claim like any
other, and the point of this feature is that a claim is not a fact.

No word is renamed and no code is renamed.

## The probe seam

Montology must not become a dependency analyzer per ecosystem. It owns the
schema, the join to the vocabulary, and the report; each language and system
contributes a **probe** that emits the same rows.

A probe answers two questions and nothing else:

    surfaces(root) -> [{owner, kind, name, exposes[], declared_at}]
    seams(root)    -> [{from_surface, to_surface, kind, direction, at}]

`kind` on a surface distinguishes what montology cannot infer — a package, a
hosted service, an HTTP API, a model. `exposes` is the named face: the
symbols, endpoints or settings other surfaces can meet.

Three consequences of this shape:

- **Manifest-less things are first class.** A hosted service has no lockfile
  and still has a surface and seams; a probe that reads a deploy config or an
  SDK client emits the same rows a package probe does. This is the half of
  the requirement a dependency graph would miss entirely.
- **A language with no probe is skipped and SAID to be skipped.** This is
  already `surface.py`'s rule for grammars and it carries over unchanged —
  silence would read as "covered" when it was not.
- **Our own code is just the probe that already exists.** `declarations()`
  becomes the first-party surface probe; nothing about it changes except that
  its output is now one surface among several.

## What counts as a seam

The decision that shapes everything downstream.

**Static seams gate.** An import that resolves to a symbol in the target
surface, a call site, a config key read at a known path — these are
deterministic, they are the same on every machine, and they can fail `lint`
the way a collision does.

**Observed seams enrich, and never gate.** Traces, telemetry, request logs.
They are true but partial: they only cover paths that happened to run, so
absence of an observed seam proves nothing. An observed seam may raise a
static seam's confidence, and may annotate a phantom as "not seen either" —
it may never, on its own, promote a phantom or fail a build.

Stated as the invariant: **a phantom is a claim about static evidence.** If
that is wrong, the probe is wrong, and the repair is to teach the probe — not
to widen what counts as proof until nothing is ever a phantom.

### What teaching the probe actually looked like

The first run against `socialite` produced 26 phantoms, of which 13 were
false. Every one was a real dependency whose seam was not a JavaScript
`import` — which is the invariant doing its job: the probe was wrong, so the
probe was taught. Four kinds of seam now, and the schema already had the
column for them:

- **import** — the resolving import, in JS/TS *and in CSS*. `@import
  "tw-animate-css"` is a seam by any honest reading; it is not JavaScript.
- **call** — a tool a `scripts` entry invokes. `oxlint` is run, never
  imported.
- **config** — a tool a manifest configures. `[tool.ruff]` in the manifest
  that declares ruff is the same evidence an import would be.
- **config**, for typings — `@types/foo` is met when `foo` is met. A typings
  package is consumed by the compiler and never imported; its subject being
  used IS the evidence it is used. When the subject is unused, both are
  phantoms — the cascade is two findings, not one hiding the other.

The rule that kept this from becoming vendor knowledge: a package's command
is often not its name (`typescript` runs as `tsc`), and that mapping is
**declared by the package itself**, in its own installed `bin`. So we read it
there rather than carrying an alias table that would rot. Absent
`node_modules`, the rule is skipped and its packages stay phantoms — silence
would be worse.

What survived: 13 phantoms, each verified genuinely unimported. That is the
number the feature exists to produce.

## Data

Two tables beside the existing ones, in the same `.monty/ontology.db`:

    surface(id, owner, kind, name, exposes, declared_at, probe, first_seen)
    seam(from_id, to_id, kind, direction, at, probe, first_seen)

The join to the vocabulary is a third, and it is the one that answers the
question this feature exists for:

    bearing(word_name, surface_id, note)

`bearing` is a table, not a word — it is the edge between two things that
already have words, and naming an edge earns nothing.

It gives both directions the design was asked for:

- a word's surfaces — what actually implements this term
- a surface's words — which of our terms this thing bears on

And the consolidation case falls out: several surfaces bearing on one word is
exactly "we collapsed these into our own term," readable without a fourth
concept.

## The command

    monty surface                what this repo stands on: surfaces, seams,
                                 phantoms — one table
    monty surface --record       run the probes and write what they find
    monty surface <word>         this word's surfaces (what implements it)
    monty surface --on <id>      this surface's seams and the words it bears
    monty surface --phantoms     only what nothing touches
    monty surface <word> --bear <id> [--note …]
                                 record that a surface bears a word

`lint` gains one finding class: a phantom that a word bears on. That is the
case where the vocabulary makes a claim the code no longer supports, and it
is the one worth failing a build over. A phantom nothing bears on is
reported, not fatal — an unused dependency is untidy, not a lie.

`vitals` gains one line: phantoms over surfaces, which is the pulse of
whether the repo is carrying dead weight.

## Sequencing — all six done

1. ✅ **The three words**, seeded in `seed.py`; `scan`'s definition widened.
2. ✅ **The schema and the join** — `surface`, `seam`, `bearing`, and
   `monty surface` reading them.
3. ✅ **One probe end to end** — Python: `pyproject.toml` for the claim,
   `ast` for the imports that resolve.
4. ✅ **The first-party probe.** Rather than re-emitting `declarations()`,
   each manifest's own package IS the first-party surface. Better than
   designed: it makes the seams BETWEEN our own packages fall out, so the
   internal dependency graph comes free with the external one.
5. ✅ **The lint finding**, and a `vitals` line.
6. ✅ **A second ecosystem** — Node: `package.json`, and tree-sitter for
   the imports. The row shape survived; nothing in the schema moved.

Measured against the private `socialite` tree (Python + TypeScript, 87
surfaces, 508 seams) as well as against this repo. `just check` passes here
with 0 phantoms.

**One correction the build forced.** `lint` measures fresh rather than
reading the table. A gate that trusted the last sweep would pass on a
dependency deleted an hour ago — the exact drift montology exists to catch,
reintroduced at the least excusable place. So `measure()` runs the probes and
writes nothing, `record()` persists, and the gate calls the former. The table
is a cache; only the bearings joined to it are authored.

## Open

- **Version.** A surface changes between releases; a seam to a symbol that no
  longer exists is a distinct finding from a phantom. Deliberately out of
  scope for v1 — but the `surface` table should carry a version column from
  the start so the data is there when it is time.
- **Transitive surfaces.** Whether a dependency's own dependencies get
  surfaces, or whether montology stops at the first ring. Stopping is the
  better default: the question this answers is "what do WE stand on," and a
  full transitive graph buries that under noise.
- **Ecosystems with no probe yet.** Elixir (`mix.exs`), Go, Rust. Each is one
  class implementing two methods; the row shape has now survived two
  ecosystems unchanged, so the cost is per-ecosystem parsing and nothing
  structural. `socialite`'s `nexus/` is Elixir and is currently unmeasured —
  and, per the rule, SAID to be unmeasured rather than silently counted clean.
- **Bearings are hand-authored.** `monty surface WORD --bear ID` is the only
  way a word gets tied to a surface. That is deliberate for now — the join is
  a claim, and claims should be made on purpose — but it means the gate is
  only as good as the bearings recorded. Mining suggested bearings from
  candidates is the obvious next instrument.
