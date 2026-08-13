# Judging a collision

> Design, 2026-08-13; **built the same day** — the sequencing at the bottom
> records what shipped and what is still open. Where [SURFACES.md](SURFACES.md)
> added what the code stands on and [ROUTING.md](ROUTING.md) added where a
> ruling applies, this one is about the finding montology already produced and
> could not judge: a symbol sharing a word's name.

## The gap

Two things were wrong with the collision advisory, and they compounded.

**The escape hatch was a bare list of strings.**

```toml
[scan]
allow = ["ontology", "word", "code", "doctrine", "scan", "collision", …]
```

No reason, no scope, no validation. It lived outside `.monty/ontology.db`, so
it was not ledgered, not queryable, and did not travel with the vocabulary a
`monty onto pull` inherits. Everything else montology records — a rename, an
overload, an amendment, a route, a bearing — carries *why* and, where it
matters, *where*. This one carried a word and a shrug.

The cost is not theoretical. That list above is montology's own, and when the
seventeen entries were migrated into the database and measured against the
tree, **twelve of them silenced nothing at all**: the declarations are plural
(`words()`, `tokens()`, `collisions()`) or compound (`workspace_root`,
`_migrate`), so no collision was ever raised on them. Five were doing real
work. Nobody could have known which, because a bare string in a config file is
never read against anything. That is what "a reasoning-free allow-list is how
a gate stops being read" looks like when you actually count it.

**And the advisory could not tell four different situations apart.** The
repair said *"rename the function, or record the exception"* for every one of
them, which is wrong three times out of four. Shane's distinction, applied to
an eighteen-advisory list on `lazyriver`, reduced it to one genuine finding:

| | | |
|---|---|---|
| **a basic verb below the surface** | `Store.open`, `Keyring.open`, `Ledger.open` | fine — ordinary work at a layer nobody authors against, and English has one word for it |
| **a primary verb at the surface** | `Controller.open` | fine — it IS the operation, and should be literal |
| **a noun** | `Snapshot.answer/3` vs some other `answer` | the real defect *if it is a second thing* — a noun names a thing, and two things with one name is the failure a vocabulary exists to prevent |
| **a value type** | `Ledger.name` vs `Snapshot.name` | must be deliberately consistent: the same value wears the same name everywhere |

The test for the bottom two is one question: **could you pass one where the
other is expected?** If yes, one name is right and that is the point, not the
problem. If no, two things are wearing one noun.

## Part 1 — part of speech is a dimension of the WORD

`kind` (core | inner | adopted | custom) records **provenance** — whose word
it is, and therefore whether the gate enforces it. The judging rule needs
**part of speech** — what the word names. These answer different questions and
neither substitutes for the other, so montology could not express the rule at
all.

Three candidate homes, and why one wins:

- **On the word** (shipped, `word.pos`). Part of speech is a property of the
  meaning. Doctrine already says a word means one thing; a word that meant one
  thing would not be a verb here and a noun there. Recording it once means
  every exception, every advisory and every future instrument reads the same
  answer.
- **On the exception.** Rejected. It would be re-declared at each site, and
  two exceptions on one word could then disagree about what the word even is —
  which is precisely the "two things, one name" failure, reproduced inside the
  mechanism built to catch it.
- **Inferred from the definition** (a gerund reads as a verb, a noun phrase as
  a noun). Rejected as a source of truth: a guess in the column the gate turns
  on would be a guess with build-breaking consequences. It is a fine thing to
  *suggest* later — see the open questions.

So: a nullable `pos` column, `verb | noun | value`, authored with
`monty onto add --pos` and correctable with `monty onto amend --pos` (ledgered
like any other amendment). Nullable is deliberate — every database in
existence predates the column, and an upgrade that fails a build nobody
changed is not an upgrade. A word with no `pos` gets an advisory that says so
and asks for it, and cannot be excepted until it has one.

`value` is not a part of speech in the grammatical sense; it is a noun with a
stricter promise. It earns the third slot because that promise is the only one
montology can mechanically check.

## Part 2 — the verb: `monty onto except`

Checked against the existing register — `check, add, amend, rule, collide,
rename, route, pull, similar, audit, list` — the authoring commands are plain
imperative verbs, so the new one should be too. `allow` was rejected: it is
vague, it is already spoken for by `[surface] allow`, and it names the
outcome rather than the act. `ordinary` was rejected because it names *one of
the four cases*, not the mechanism — a primary verb at the surface is not
"ordinary", it is the word meaning itself.

`except` wins because the noun montology already uses in its own prose is
*exception*: "a named exception is A RECORDED DECISION" is a sentence the
surface gate was already written around. The word is now in the vocabulary
(`exception`, `onto.exception`).

```sh
monty onto except open --where "lib/**" --why "ordinary work below the surface"
monty onto except                 # every exception, with its reason
monty onto except open --where "lib/**" --drop
monty onto except --drafts        # what an old [scan] allow list would become
```

**The case is derived, never declared.** The caller supplies the word, the
scope and the reason; the word's `pos` decides which of the four rules
applies. Asking a human to type the case would let the claim disagree with the
vocabulary, and then there would be two answers to the same question.

`--why` is required and stored. A blank one is refused, in the same voice as
`monty onto rename`'s missing why: *a reasonless allow-list is how a gate
stops being read.*

## Part 3 — scope is a path glob, and nothing grander

Shane's case is not "`open` is always fine" but "`open` is fine *below the
surface*". A mechanism that cannot say that cannot record the decision.

What a scanner can actually enforce is a **path**. It already knows
`file:line` for every declaration; matching a glob against it is exact and
free. Module and layer were considered and rejected: a module is a per-language
concept the declaration query does not carry, and "layer" is a fact about a
repo's architecture that no scan can discover — encoding either would be
aspiration wearing the costume of enforcement. A repo that wants layers
expresses them as globs, which is what a layer is on disk anyway.

So: `--where "lib/**"`, matched with `fnmatch` against the declaration's path
relative to the workspace root. Omitting it is legal and records `**`, which
is *said out loud* on grant ("tree-wide") and shown that way in every listing —
the same treatment `route` gives an unscoped ruling, and for the same reason:
a ruling that cannot say where it applies cannot be enforced anywhere. The
advisory's suggested repair pre-fills the glob with the declaration's own
directory, so the easy path is a scoped one.

The scope binds the **firewall** as well as the gate (`monty guard` reads the
same rows). A pre-write hook that denies what CI allows teaches an agent to
stop reading either.

## Part 4 — recorded in the database

`.monty/ontology.db`, table `exception`: `word, scope, why, judged, checked,
granted_on, origin`, keyed on `(word, scope)`. It is ledgered, queryable,
rendered into the words skill, inherited by `monty onto pull`, and it appears
in `monty onto check <name>` — which is where somebody about to name a thing
is already looking.

Every exception is **shown on every lint run**, whether or not it fired, and
one that covers no declaration is reported as possibly stale with a `--drop`
repair. An exception nobody ever sees again is how a stale one survives for
years; this is the same discipline the surface gate applies to a recorded
phantom.

`[scan] allow` is still honoured — silently breaking a build nobody touched is
not an upgrade — and now reported on every run:

```
note: 3 exception(s) still live in montology.toml [scan] allow — unledgered,
reasonless, and unjudged (the four cases turn on a word's part of speech,
which a list of strings cannot carry). Repair: monty onto except --drafts
```

**Migration is a review, not a rewrite.** `monty onto except --drafts` lists
each legacy entry with the command to adopt it, flags the ones that are not
words at all and the ones with no part of speech yet, and refuses to invent a
`why` — the reason is the entire feature, and a generated one would be worse
than none. Montology's own migration ran this way and is in `seed.py`, twelve
dead entries lighter.

## Part 5 — the value-type guard

This is the part that had to be right, and the answer turned out to be
structural rather than clever.

**An exception and a divergence are two different findings.** An exception
says *a symbol may share this word's name*. A divergence says *this one name
holds two different values*. The first is a decision a human is entitled to
make; the second is a contradiction inside the vocabulary itself. So they are
separate laws, and **the exception mechanism has no power over the divergence
law at all** — not "it is refused", but "it is not connected to it". There is
no configuration in which granting an exception suppresses a divergence,
because the divergence check never consults the exception table.

That is the honest answer to *"could a blanket exception hide it?"*: no,
structurally, rather than by policy.

### What is actually detectable

Where a language declares its types, montology can compare them. `TYPE_QUERIES`
covers Elixir (`@type`/`@typep`/`@opaque`), TypeScript/TSX (`type` aliases and
`interface`), Go (`type_spec`) and Rust (`type`/`struct`). Each match pairs a
name with its right-hand side — paired *per match*, never by position in two
capture lists, or an interface with no body would shift every later pair and
invent divergences that are not there. The right-hand side is whitespace-
normalised and compared as text: two declarations that differ only in
formatting are the same, and nothing else is assumed equal.

On the case that produced this feature, that is exactly enough:

```
lib/lazy_river/cluster.ex:32   @type name :: term()
lib/lazy_river/ledger.ex:26    @type name :: term()
lib/lazy_river/snapshot.ex:22  @type name :: %{Ledger.ref() => non_neg_integer()}
```

`Ledger.open/2` takes the first. `Snapshot.name/1` returns the second. They are
not interchangeable, `name` is the word, and a blanket exception is precisely
what would have buried this.

### What it does

- **At grant time**, `monty onto except` measures the name first. For a
  `value`, a divergence is a **refusal** — the word claims interchangeability
  and the code already contradicts it, so there is nothing to except yet; the
  refusal prints both shapes with their sites and the interchangeability
  question. For a `noun`, the divergence is **printed as a warning and the
  exception is granted**: two declarations may be two renderings of one thing
  (a wire form and a struct), and only a human can say.
- **At every lint**, independently: a `value` word declared as two values
  **FAILS**; a `noun` word **warns**. Grant time alone would rot — an
  exception recorded honestly today must not shield a second `@type` added in
  six months. There is a test for exactly that scenario.
- The law fires **only on words with `pos` in {noun, value}**. Two modules
  declaring their own `option` type are two modules, not drift; without a word
  claiming the name means one thing, there is no claim to violate. This is
  what keeps the law from becoming the false-positive storm that would get it
  switched off.

### What is NOT detectable, stated plainly

- **Languages that do not declare named types.** Python's `name: str` is an
  annotation on a binding, not a declaration of a named type; inferring one
  would be guessing. Python, Ruby, Java, C and the rest are not covered, and
  the exception says so: `checked = 'unchecked'`, and the grant prints *"nothing
  declared this name as a type in a language montology can compare, so nothing
  verified that these two are the same thing. The reason above is the only
  evidence."* Silence would read as agreement; it is recorded as ignorance.
- **Function parameters and return positions.** `Ledger.open(name, opts)` binds
  a parameter called `name`; the scan sees declarations, not parameters, so
  that occurrence is invisible. It happened not to matter here — the `@type`
  declarations carried the same divergence — but it will matter in a repo that
  never names its types.
- **Structural equivalence.** `%{a: t()}` and a struct with the same shape read
  as two values. The tool is deliberately literal: it compares what the code
  says, and a name that means one thing said two ways is a finding worth a
  human glance anyway.
- **Semantic sameness.** Two `term()`s that are the same text but different
  concepts pass. Nothing short of a type system catches that, and montology
  will not pretend to.

## Part 6 — the repair text

The old line prescribed a rename for all four cases and pointed at a config
file. The new one names the case, asks the question that decides it, and
offers both directions with the scope pre-filled:

> **verb** — `'open'` is a verb. If this function does the work the word names
> — at the surface it IS the operation, below it English simply has one word
> for the job — keep it and record why: `monty onto except open --where
> "lib/lazy_river/**" --why "…"`. If it names some other action, rename it.

> **noun** — `'ledger'` is a noun, and a noun names a thing: two things with
> one name is the failure the vocabulary exists to prevent. If this struct
> denotes exactly what the word denotes, keep it and say so: … If it denotes a
> second thing, rename it — that one IS the defect.

> **value** — `'name'` is a value type: the same value wears the same name
> everywhere. Could you pass this function's value where the word's is
> expected? If yes, one name is right — record it: … If no, two things are
> wearing one noun and renaming is the only repair.

> **no pos yet** — `'open'` has no part of speech, so this collision cannot be
> judged. Say which it is (`monty onto amend open --pos verb|noun|value`), then
> rename the function or except it.

And the divergence line, which belongs to no case because no exception reaches
it:

> **FAIL** word `'name'` is a value and the code declares it as 2 different
> values — `cluster.ex:32 term()`; `snapshot.ex:22 %{Ledger.ref() =>
> non_neg_integer()}`. Could you pass one where the other is expected? If not,
> two things are wearing one noun. Repair: rename one of them, or amend the
> word if the definition is what is wrong. No exception silences this: an
> exception says a SYMBOL may share the name, never that the NAME may mean two
> values.

## Measured

The `lazyriver` tree, read as a case study (a scratch copy; nothing was written
to it):

| | before | after |
|---|---|---|
| collision advisories | 15 | 1 |
| exceptions recorded | 7 strings in a toml comment block | 6 rows, each with its reason and scope |
| genuine findings | — | **1 FAIL: `name` declared as two values** |

The survivor is exactly the one Shane predicted a blanket exception would
hide, and the attempt to except it is refused with both shapes named.

Montology's own repo: 17 reasonless allow entries → 6 reasoned exceptions, and
`just check` stays green.

## What shipped

1. `word.pos` (`verb | noun | value`), nullable, additive migration, amendable
   and ledgered; `--pos` on `onto add` / `onto amend` and both MCP tools.
2. `exception` table; `monty onto except` with `--where` / `--why` / `--drop` /
   `--drafts`; exceptions in `monty onto check`, in the lint output, and in the
   rendered words skill.
3. `TYPE_QUERIES` and `scan.type_declarations` — name paired with what it
   holds, for the four languages that declare it.
4. The `divergence` law, independent of exceptions: FAIL for a value type,
   warn for a noun, silent for anything the vocabulary makes no claim about.
5. The four-case repair text, and the guard reading the same rows as the gate
   so the firewall cannot contradict CI.
6. Montology's own migration, in `seed.py`, twelve dead entries lighter — plus
   the doctrine block that states the rule where the vocabulary lives.

## Open questions — Shane's, not the implementation's

1. **Should `pos` be required for new words?** Today it is optional, and a word
   without one gets an advisory that cannot be judged or excepted. Requiring it
   would make every collision judgeable and would break `monty onto add` for
   every existing script and the `gen` path. *Recommendation: leave optional
   for now, and revisit once a repo other than montology and lazyriver has
   authored with it.* The trade is completeness against an upgrade that
   refuses work it used to accept.

2. **Is `value` a third `pos`, or a flag on `noun`?** Shipped as a third value
   because the divergence law treats them differently (FAIL vs warn) and a
   flag would make that a two-field lookup. The counter-argument is that a
   value type IS a noun, and a vocabulary that says otherwise is teaching bad
   grammar. *Recommendation: keep three; the field is called `pos` and it is
   already documented as a judging dimension rather than a grammar lesson.*

3. **Should a noun divergence FAIL rather than warn?** Shane's rule says a
   colliding noun is the real defect, which argues for FAIL. The
   implementation warns, because two type declarations of one noun can be two
   renderings of one thing. *Recommendation: leave at warn until a second repo
   has been measured; promoting it later is a one-word change, demoting it
   after a build breaks is an argument.*

4. **Should an agent be able to grant an exception?** `monty onto except` is
   CLI-only; it is deliberately NOT an MCP tool, because the guard's own
   refusal already says *"the human records the exception"*, and an agent that
   can silence the gate that constrains it is not constrained. *Recommendation:
   keep it human-only.* An agent can read every exception (`ontology_check`,
   `ontology_lint`), which is what it needs to comply.

5. **Should `monty onto except` be able to amend the word's `pos` inline?**
   Today a missing `pos` is a refusal carrying the exact repair command, which
   costs one extra step. Doing both in one call is friendlier and makes a
   single command do two ledgered things. *Recommendation: keep the refusal;
   `add` and `amend` set the same precedent, and the second step is one line.*

6. **Should `pos` be suggested from the definition?** A definition beginning
   with a gerund ("naming the ledgers to read…") reads as a verb; a noun
   phrase reads as a noun. Cheap to offer as a *proposal* in `monty onto
   audit`, alongside the semantic duplicates it already reports. It must never
   be written without confirmation — the gate turns on this column.
