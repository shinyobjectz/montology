<p align="center"><img src="docs/banner.png" alt="montology — your codebase's vocabulary, enforced" width="100%"></p>

**Your codebase's vocabulary, enforced — and your agents can't drift it.**
Words and rulings live in a database; a tree-sitter scan checks every
named thing your code declares against them — classes, structs, functions,
types, modules, protocols — across twelve languages; a pre-write hook
corrects your coding agent before drift ever lands.

montology reads what your code *already declares* — every named thing in
Python, TypeScript, Go, Rust, Swift, Java, Ruby, Elixir, C and C++ (and,
where there is a UI, the Tailwind theme and the CSS) — and turns it into
an ontology with a gate: drift fails CI with the file, the line, and the
repair. It is a vocabulary layer for **all** of your code, not a styling
tool; a repo with no UI in it uses every part of this except the last.

```sh
# the CLI — works today, from nothing but `uv`
uvx --from "git+https://github.com/shinyobjectz/montology#subdirectory=.monty/cli" monty init

# the agent skill (Claude Code, Cursor, and friends)
npx skills add shinyobjectz/montology

# npm (the launcher)
npm install -g montology
```

![monty init + lint: theme adopted, drift receipted](docs/demo.gif)

[**Changelog**](CHANGELOG.md) · [Research notes](research/FINDINGS.md) ·
[Surfaces](docs/SURFACES.md)

## Sixty seconds to a drift report

```sh
cd your-repo
monty init            # .monty/, agent wiring, the pre-write guard hook
monty explain         # the X-ray: what this repo is, in one pass
monty scan --candidates   # the words your code is already asking for
monty lint            # the gate — every finding carries its repair
monty config          # what the gate enforces, and how to change it
monty intake ask …    # no words yet? the agent's `intake` skill asks the team
                      # in a form, round by round, and ends in a glossary
```

```
FAIL collision: struct 'Harness' at Sources/Runner.swift:14 is the word
     'harness' — "the thing that runs a scenario end to end". Rename it,
     or record the exception: monty onto except harness --where … --why …
FAIL divergence: type 'RowID' is declared as String (db/rows.ts:8) and as
     Int (api/rows.ts:12) — one noun, two things
warn retired: 'pointer' was RENAMED to 'cursor' (the word moved when the
     UI stopped owning it). Name it 'cursor' — the old name stays retired.
note design: rogue color #121212 ×2 (first at css/app.scss:37)
     — nearest token: ink #1b1b1f (Δ31)
```

Every finding names the file, the line and the repair. The first three
are about the CODE — a struct wearing a word that means something else, a
type declared as two different things, a name a ruling retired — and the
last is the same contract applied to a hex code, which is a word that
means one thing. If your repo has no UI you will never see that line.

Where there IS a UI, the same machinery goes further: `monty design
recipes` mines the class strings your markup repeats (`flex flex-wrap
gap-2 items-center` ×102 — on shadcn/ui's own repo) so they can become
*named* things.

## The firewall: your agent cannot write drift

![the guard denies the edit before it lands, with the tokens to use](docs/guard.gif)

Everything above is post-hoc. The guard runs **before the write**:
`monty init` installs a pre-write hook in every harness it wires
(merge-safe — `.claude/settings.json` and `.cursor/hooks.json`), and the
plugin ships its own, so a plugin install is guarded without an init. It
lints every proposed Write/Edit/NotebookEdit against the ontology in
milliseconds — a declaration named after a **retired** word
(renames are rulings; always blocks), a collision with an enforced word,
a rogue hex when tokens exist. Deny is exit 2 with the repair on stderr:
the harness feeds it straight back to the model, which corrects and
retries. The agent *physically cannot* introduce a second gray or resurrect
a renamed concept — it gets the token or the current word handed to it
mid-edit. The guard **fails open** (malformed payload, no workspace, any
internal error → allow silently) so it can never break an editor; humans
in vim never meet it. `monty doctor` says, per harness, whether it is
actually wired; `monty config guard.names block|warn|off` tunes it.

## `monty explain` — the one-shot conceptual X-ray

![point it at a repo it has never seen](docs/explain.gif)

Point montology at any repo cold: one command composes the declared
surface, the vocabulary it has, the vocabulary it is *asking for* (with
definitions drafted on the atomic tier when one serves — law-checked,
refused over wrong), **where meanings actually gather** (semantic
clusters vs the directory tree's claimed architecture: cross-cutting
concepts, grab-bag directories), the design system as measured, and
every place the repo contradicts itself — straight to the terminal,
because an instrument prints findings, it does not decorate them.

## The part that keeps you: words

A repo's concepts drift exactly like its colors. montology's vocabulary
is a **database, not a doc** — one word, one meaning, a one-line test,
an optional dotted code — rendered into a generated agent skill and
enforced against every declaration tree-sitter can parse (python,
ts/tsx, js, go, rust, swift, elixir, ruby, java, c, c++):

![candidates → check-first → advisory collisions](docs/words.gif)

```sh
monty onto check thread        # FREE / TAKEN / RULED — before naming ANYTHING
monty scan --candidates        # the words your codebase is asking for
monty onto add thread "a stateful user↔agent session" --code atl.thread --pos noun
monty onto amend thread --definition "…" --why "a later ruling narrowed it"
monty lint                     # collisions (advisory by default), code-tree
                               # integrity, stale prose — each with its repair
```

Not every symbol sharing a word's name is drift, and treating them alike
produces a list nobody reads. A word carries **what it names** — verb,
noun, or value type — and the judgment follows from it: `Store.open` is
English doing ordinary work below the surface, while a noun answering for
a second thing is the failure a vocabulary exists to prevent. A collision
you keep is a recorded decision, in the database with the rest of the
vocabulary:

```sh
monty onto except open --where "lib/**" --why "ordinary work below the surface"
monty onto except --drafts     # what an old [scan] allow list would become
```

What an exception can never do is silence a **divergence** — one
value-typed word declared as two different values (`@type name :: term()`
in one module, `@type name :: %{…}` in another). That is a separate law
with a separate line: an exception says a *symbol* may share the name, not
that the *name* may mean two things.

Rulings end arguments permanently: **overloads** ("say cell, not
sandbox"), **collisions** with frameworks (whose word it is, who moved),
and **renames** — the old name retires, old material stays readable, and
`monty migrate old new --apply` propagates the rename through the code
by *token* (tree-sitter positions, strings and comments untouched,
losslessly round-trippable — proven on eight real repos).

When a ruling narrows a word you already authored, **`monty onto amend`**
corrects the record in place: the name and its history stay, every field
that changes is ledgered with the text it replaced, and an unknown name or
a no-op is refused. Editing the database around the authoring path is the
same drift the gate exists to catch.

## Meaning over time

![monty vitals: one verdict per repo](docs/vitals.gif)

Three instruments make a repo's meaning a *tracked quantity*:

- **`monty vitals`** — the pulse: gate state, vocabulary state, design
  state, guard compliance → one verdict (**TENDED / DRIFTING /
  UNTENDED**) with every reason carrying its repair — plus whether the
  firewall is wired and the org upstream it inherits. `--json` is the
  dashboard shape; `--strict` exits 1 unless TENDED, so a repo can gate
  on its own tending. Track it per repo the way you track CI.
- **`monty drift`** — the telescope: the git history sampled into
  lexicon, palette and convergence curves (`--csv` for the research
  lane). First observation, excalidraw's full history: the palette
  fragmented ~10× in two years (4→11→27→42 distinct colors) while
  declarations merely doubled — and their one-off CSS-variable cleanup
  did not hold. Flask's concept lexicon, by contrast: 49 concepts in 15
  years, flat since 2019. **Convergence is a property of tending, not
  of software.**
- **`monty guard --stats`** — repair-following, measured: every hook
  denial followed by a clean edit within 30 minutes is a complied
  denial. The compliance dataset accumulates from ordinary use; every
  hooked workspace is a passive experiment in whether enforcement
  closes the literature's *text-action disconnect*.

The research notes — instruments, first measurements, prior art, open
protocols — live in [`research/FINDINGS.md`](research/FINDINGS.md), and
what has changed release to release is in [`CHANGELOG.md`](CHANGELOG.md).

## Semantic hearing

![similar → the string laws pass → the audit hears the duplicate](docs/semantics.gif)

The string laws enforce *one word, one meaning*. The `[semantics]` extra
hears the dual — *one meaning, one word* — with POTION static embeddings
(~30 MB, numpy-only; no torch, no runtime): `monty onto audit` flags two
words defined into the same idea, local words that duplicate inherited
org words under different names, candidates that are secretly existing
words, and owner groupings that don't match where meanings cluster.
Advisory permanently — a cosine score proposes, only a ruling decides.

## One ontology, every repo

The org's vocabulary is authored once — any montology workspace's
`.monty/ontology.db` *is* the artifact — and inherited everywhere:

![inherit the org ontology, renames cross the fleet](docs/org.gif)

```sh
monty init --from git@github.com:acme/ontology.git    # or a path, or a .db URL
monty onto pull                                       # refresh from the pin
```

Upstream rows refresh on every pull; local words always survive; a name
defined in both places is a loud conflict (local wins — reconcile
deliberately). When the org renames a word, every repo's next pull
prints the exact `monty migrate` command: that is how a rename crosses
the fleet.

## The two models it carries (and the ones it refuses)

montology is deliberately near-modelless — the deterministic laws do the
enforcing — but it carries exactly two, each chosen for a measured floor:

| model | size | lane | what it does | what it refuses |
|---|---|---|---|---|
| **POTION** (`potion-base-8M`, model2vec) | ~30 MB, numpy-only | `[semantics]` extra | static embeddings over definitions: `onto similar`, `onto audit` — duplicate meanings, org/local doubles, misfiled clusters. Millisecond inference, no torch, no runtime. | deciding anything. A cosine score proposes; only a ruling makes vocabulary. |
| **gemma3:270m** (via Ollama, optional) | 292 MB, user-installed | `monty gen <word>` | drafts ONE-LINE definitions under the word laws (refused over written wrong) when no host agent is present — the autonomous lane. | bodies and prose. The 270M capability floor is atomic one-liners; everything longer is the host agent's work or a served endpoint (`MONTOLOGY_MODEL_URL`). |

Nothing heavier ships, ever: no torch, no onnxruntime, no bundled
weights. The host agent (Claude, Cursor, Codex) is always the best
drafter available, and the gate never needs a model at all.

## For agents

`monty init` wires the repo for Claude Code, Cursor, and Codex
(merge-safe: sections are appended, JSON keys merged, global config never
touched) — MCP server, the instructions section, and the pre-write guard
hook in each harness's own dialect. `monty doctor` reports which of those
actually landed.

Two skills ship: **`montology`** routes the work (new repo → set up,
empty vocabulary → build one, working repo → the check-first contract),
and **`intake`** runs the guided walkthrough for a codebase whose words
were never written down. The generated **`words`** skill carries the whole
vocabulary — words, tokens, recipes, rulings, doctrine — tiering into
reference pages rather than truncating when it outgrows its budget.

The MCP server exposes `ontology_check`, `ontology_add`, `ontology_amend`,
`ontology_rule`, `ontology_similar`, `ontology_words`, `ontology_lint`,
`scan_surface`, `scan_candidates`, `structural_search`, `repo_explain`,
`repo_vitals` and `workspace_config`. Prose is rendered from the database,
never authored; a stale render fails the build.

## Under the hood

tree-sitter (via `tree-sitter-language-pack`) measures declarations and
CSS structurally; ast-grep (invoked, one static binary) powers
structural pattern search; SQLite holds the vocabulary. The stress
battery (`stress/run.py`, weekly in CI) proves four properties on eight
real repos — flask, excalidraw, gin, ripgrep, phoenix, sinatra,
spring-petclinic, redis: merge-safe idempotent init, zero-error parsing,
truthful collision reporting, and lossless migrate round-trips.

## The taxonomy library

Your vocabulary rarely starts from nothing. Where an industry has already
agreed on a word, joining that standard beats inventing a synonym — so
montology keeps a vetted registry of public taxonomies, browsable with
`monty onto sources [core|extra|evaluate|skip]` or the `ontology_sources`
MCP tool. Each entry carries two rulings: whether it is worth reaching for,
and **whether you may ship against it**.

All 27 licences were checked against the source, so there is no "unknown"
column to squint at. Four results are worth knowing before you reach for one:

- **The IAB taxonomies declare CC BY 3.0 in a README and ship no `LICENSE`
  file**, so GitHub — and every automated scan — reports three of the five
  `core` entries as unlicensed. They are usable; attribution is required.
- **`google-product` grants nothing.** A bare `.txt` with no licence and no
  terms page; `developers.google.com`'s CC BY 4.0 policy does not reach it.
  Published so you can build a feed — not permission to ship it in a product.
- **`schemaorg` is share-alike**, the one licence here that can reach back
  into a vocabulary you build on top of it.
- **NAICS and SIC point at the Census and the SEC**, not at convenience
  repackagings that declare no licence. The authority is a US federal work
  and therefore public domain.

### `core` — Reach for these first.

| taxonomy | domain | licence | commercial | source |
|---|---|---|---|---|
| **Google Product Taxonomy** | retail · e-commerce | none — a bare .txt on www.google.com, no licence, no terms page, and developers.google.com's CC BY 4.0 site policy does not reach it | 🚫 unlicensed | [`google-product`](https://www.google.com/basepages/producttype/taxonomy.en-US.txt) |
| **Google Topics API Taxonomy** | advertising · web platform | W3C Software and Document Licence | ✅ yes | [`google-topics`](https://github.com/patcg-individual-drafts/topics) |
| **IAB Ad Product Taxonomy 2.0** | advertising · inventory | CC BY 3.0 | ✅ yes — attribution | [`iab-adproduct`](https://github.com/InteractiveAdvertisingBureau/Taxonomies) |
| **IAB Audience Taxonomy 1.1** | advertising · audience | CC BY 3.0 | ✅ yes — attribution | [`iab-audience`](https://github.com/InteractiveAdvertisingBureau/Taxonomies) |
| **IAB Content Taxonomy 3.1** | advertising · media | CC BY 3.0 | ✅ yes — attribution | [`iab-content`](https://github.com/InteractiveAdvertisingBureau/Taxonomies) |

- **google-product** — 5k+ categories every Shopping feed must speak; e-commerce lives here. Published FOR building feeds; that is not a licence to redistribute it inside your own product, and Google grants none.
- **google-topics** — ~470 ad-relevant topics; small, curated, and what Chrome's interest signals emit.
- **iab-adproduct** — Names the thing being sold; completes the IAB triple.
- **iab-audience** — The segmentation counterpart to iab-content; audience descriptions marketers already use.
- **iab-content** — THE contextual-targeting and brand-safety vocabulary; what OpenRTB speaks.

### `extra` — Pertinent, but not everyone's need.

| taxonomy | domain | licence | commercial | source |
|---|---|---|---|---|
| **Google NLP Content Categories** | content classification | CC BY 4.0 (Google Cloud docs) | ✅ yes — attribution | [`google-nlp-categories`](https://cloud.google.com/natural-language/docs/categories) |
| **NAICS (North American Industry Classification System)** | cross-industry · government | US federal work — public domain (17 U.S.C. §105) | 🟢 public domain | [`naics`](https://www.census.gov/naics/) |
| **OpenOOH Venue Taxonomy** | advertising · out-of-home | Apache-2.0 | ✅ yes | [`openooh-venue`](https://github.com/openooh/venue-taxonomy) |
| **Schema.org vocabulary (types + properties)** | cross-industry · web | CC BY-SA 3.0 | ⚠️ yes — share-alike | [`schemaorg`](https://schema.org/version/latest/schemaorg-current-https.jsonld) |
| **Shopify Product Taxonomy** | retail · e-commerce | MIT | ✅ yes | [`shopify-product`](https://github.com/Shopify/product-taxonomy) |
| **SIC codes** | cross-industry · government | US federal work — public domain (17 U.S.C. §105) | 🟢 public domain | [`sic`](https://www.sec.gov/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list) |

- **google-nlp-categories** — ~620 labels Google's classifier emits — useful as a mapping TARGET, not a house vocabulary.
- **naics** — Industry classification — firmographics for B2B. Take it from the Census: the convenience repackaging at CompileInc/naics-codes declares no licence, and there is no reason to inherit that when the authority is public domain.
- **openooh-venue** — Digital-out-of-home venue types; niche channel, real standard.
- **schemaorg** — The universal web vocabulary every industry structures data in; 2,454 classes and properties, and what SEO structured-data work speaks.
- **shopify-product** — 10k+ categories with attributes — richer than Google's tree; heavy, so opt-in.
- **sic** — NAICS's predecessor, still what many registries file under. From the SEC for the same reason NAICS comes from the Census.

### `evaluate` — Known and promising — **not recommended yet**; the note says what question is open.

| taxonomy | domain | licence | commercial | source |
|---|---|---|---|---|
| **Harvard Growth Lab classifications (ISIC/HS/SITC/O*NET)** | trade · occupations | BSD-3-Clause | ✅ yes | [`cid-classifications`](https://github.com/cid-harvard/classifications) |
| **IABTechLab/iab-mapper (2.x → 3.0 mappings)** | advertising · migration | BSD-2-Clause | ✅ yes | [`iab-mapper`](https://github.com/IABTechLab/iab-mapper) |
| **Industry Classification Benchmark (FTSE/Dow Jones)** | finance | ICB is proprietary to FTSE Russell; the gist republishes it without a licence to do so | 🚫 proprietary | [`icb`](https://gist.github.com/mysticmind/bf3acd436bbaddca62ca1f3e01e890c9) |
| **IPTC Media Topics** | news · media | CC BY 4.0 — IPTC states it for all NewsCodes | ✅ yes — attribution | [`iptc-media-topics`](https://iptc.org/standards/media-topics/) |
| **wikidata-taxonomy (extraction CLI)** | general knowledge | MIT (the tool; Wikidata's own data is CC0) | ✅ yes | [`wikidata-taxonomy`](https://github.com/nichtich/wikidata-taxonomy) |

- **cid-classifications** — Many systems, one cleaned repo — incl. O*NET occupations for workforce mapping. Heavy; take one system when a concrete need names it.
- **iab-mapper** — Mappings, not a taxonomy — pertinent the day you meet 2.x codes in the wild.
- **icb** — The open GICS-alternative investors reference — but a personal gist is not an authority, and ICB itself is FTSE Russell's property. Find a durable, licensed source before touching it.
- **iptc-media-topics** — 1,200 terms, 13 languages, real standard — but RDF/SKOS parsing is its own project; decide when PR or content work needs it.
- **wikidata-taxonomy** — A tool, not a dataset — could mint niche taxonomies on demand; decide if a real need appears.

### `skip` — Considered and declined, with the reason, so nobody re-litigates it. Licensed anyway — "we declined it" and "we never looked" are different sentences, and a blank field cannot tell them apart.

| taxonomy | domain | licence | commercial | source |
|---|---|---|---|---|
| **IAB ↔ Google crosswalk (markomma)** | advertising · migration | n/a — the repository no longer exists | — source gone | [`adtech-crosswalk`](https://github.com/markomma/adtech-crosswalk) |
| **classifast (UNSPSC/NAICS/ISIC/ETIM classifier)** | classification tooling | MIT | ✅ yes | [`classifast`](https://github.com/DmitryMatv/classifast) |
| **DMOZ / Curlie web directory** | web directory | CC BY 3.0 Unported | ✅ yes — attribution | [`dmoz-curlie`](https://curlie.org/) |
| **Essential-AI web-content taxonomy** | ML data curation | none — the README's Licence section is an unfilled '[License information]' placeholder, so nothing is granted | 🚫 unlicensed | [`eai-taxonomy`](https://github.com/Essential-AI/eai-taxonomy) |
| **InstructLab knowledge taxonomy** | ML tuning | Apache-2.0 | ✅ yes | [`instructlab-taxonomy`](https://github.com/instructlab/taxonomy) |
| **iPullRank IAB-as-JSON** | advertising | MIT | ✅ yes | [`ipullrank-iab-json`](https://github.com/iPullRank-dev/iab-taxonomy) |
| **MISP threat-intel taxonomies** | security | CC0 1.0 (dual-licensed, CC0 or BSD) | 🟢 public domain | [`misp`](https://github.com/MISP/misp-taxonomies) |
| **NAICS-GH labeled-repos dataset** | ML data | CC BY 4.0 | ✅ yes — attribution | [`naics-gh`](https://huggingface.co/datasets/aquiro1994/naics-gh) |
| **ecosyste.ms OSS taxonomy** | open source | CC0-1.0 | 🟢 public domain | [`oss-taxonomy`](https://github.com/ecosyste-ms/oss-taxonomy) |
| **SIC/NAICS/GICS/Fama-French SAS crosswalk** | finance research | none — a gist carries no licence unless its author writes one, and this one does not | 🚫 unlicensed | [`sic-naics-finance-macros`](https://gist.github.com/mgao6767/4134ce36793b9e932a219ff07d7a3c7f) |
| **Tabiya occupations/skills taxonomy** | occupations · skills | MIT for the platform code; the taxonomy itself derives from the EU's ESCO and carries the Commission's reuse terms | ✅ yes — attribution | [`tabiya`](https://docs.tabiya.org/our-tech-stack/inclusive-livelihoods-taxonomy/open-taxonomy-platform) |

*All 27 licences were checked against the source on 2026-09-01 and are recorded AS PUBLISHED. This is a starting point for your own diligence, not legal advice — terms change, and an unstated licence is never a permissive one.*

The registry is a **catalogue, not an ingest** in this era: it tells you what
exists, whether it is real, and whether you may use it. Wiring a source into
`.monty/ontology.db` is per-source work, and the note on each entry says what
that would take.
## Contributors

```sh
git clone https://github.com/shinyobjectz/montology && cd montology
uv sync && just              # the action surface
just check                   # the gate (montology lints itself, strictly:
                             # its own toml sets collisions = "enforce")
```

Changes go in [`CHANGELOG.md`](CHANGELOG.md) under `Unreleased`.
