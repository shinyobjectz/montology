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

**57 public ontologies and taxonomies across 14 domains**,
each checked for whether it is real, whether it is maintained, and whether
**you may ship against it**. Browse with `monty onto sources [group]` or the
`ontology_sources` MCP tool.

Two of them are more than an address: `monty onto sources ingest prov-o`
and `monty onto sources ingest schemaorg` load those vocabularies into
`.monty/ontology.db` as **adopted** words — 80 PROV-O terms, 2,322
Schema.org classes and properties — so that `monty onto check Activity`
answers "that is PROV-O's word, not yours" rather than "free". The payload
is cached under `.monty/cache/`, so every run after the first is offline;
your own words are never overwritten; and the licence travels with every
answer, which for Schema.org's CC BY-SA 3.0 is the difference between a
vocabulary you may read and one you may ship.

Your vocabulary rarely starts from nothing. Where an industry has already
agreed on a word, joining that standard beats minting a synonym — and where
it hasn't, montology's own gate is what keeps yours honest.

**How these were chosen.** There are thousands of ontologies —
[BioPortal](https://bioportal.bioontology.org/) alone lists 1,283 — but they
are overwhelmingly life-sciences, because genomics forced that field to agree
on words and no comparable pressure existed elsewhere. So this is a curated
shortlist, not a dump: entries had to be actively maintained, used by people
other than their authors, and carry a licence permitting commercial use. Most
of the rigorous ones follow the
[OBO Foundry principles](https://obofoundry.org/principles/fp-000-summary.html)
— open licence, versioning, textual definitions, stable identifiers, a named
authority — which is the closest thing this field has to a quality bar, and
close to what montology enforces on your own vocabulary.

**The second tier, for when the shortlist has no answer.** "What should I
join?" and "does one already exist for this?" are different questions, and
answering the second from a 56-row list answers it wrong. So
`monty onto sources --search <query>` searches the shortlist *and* a
harvested index: the 177 active OBO Foundry ontologies that declare a
licence, lifted verbatim from
[its registry](https://obofoundry.org/registry/ontologies.jsonld) and
cached under `.monty/cache/` so it works offline. The two tiers print under
separate headings and mean different things — tier 1 was read here and
carries a verdict; tier 2 is what its publisher says about itself, with
nobody's judgement attached. `--refresh` re-fetches and reports the
arithmetic: what came in, what stayed, and which filter dropped the rest
(unmaintained, no declared licence, or already in the shortlist).

**Three licence findings worth knowing before you reach for anything:**

- **The IAB taxonomies declare CC BY 3.0 in a README and ship no `LICENSE`
  file**, so GitHub and every automated scan report them as unlicensed.
  They are usable; attribution is required.
- **`google-product` grants nothing.** A bare `.txt` with no licence and no
  terms page — published so you can build a feed, which is not permission to
  ship it inside a product. Use `shopify-product` instead. It is the only 🚫
  on this page, and it is here as a warning.
- **`schemaorg`, `edam` and `owasp-llm` are share-alike** — the licences that
  can reach back into a vocabulary you build on top of them.

### `core` — any business, any industry

| ontology | licence | commercial | source |
|---|---|---|---|
| **BFO — Basic Formal Ontology** | CC BY 4.0 | ✅ yes — attribution | [`bfo`](https://obofoundry.org/ontology/bfo.html) |
| **DCMI Metadata Terms (Dublin Core)** | CC BY 4.0 | ✅ yes — attribution | [`dublin-core`](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) |
| **NAICS (North American Industry Classification System)** | US federal work — public domain (17 U.S.C. §105) | 🟢 public domain | [`naics`](https://www.census.gov/naics/) |
| **PROV-O — the Provenance Ontology (W3C)** | W3C Software and Document Licence | ✅ yes | [`prov-o`](https://www.w3.org/TR/prov-o/) |
| **QUDT — Quantities, Units, Dimensions and Types** | CC BY 4.0 | ✅ yes — attribution | [`qudt`](https://github.com/qudt/qudt-public-repo) |
| **RO — the Relation Ontology** | CC0 1.0 | 🟢 public domain | [`ro`](https://obofoundry.org/ontology/ro.html) |
| **Schema.org vocabulary (types + properties)** | CC BY-SA 3.0 | ⚠️ yes — share-alike | [`schemaorg`](https://schema.org/version/latest/schemaorg-current-https.jsonld) |
| **SIC codes** | US federal work — public domain (17 U.S.C. §105) | 🟢 public domain | [`sic`](https://www.sec.gov/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list) |
| **SKOS — Simple Knowledge Organization System (W3C)** | W3C Software and Document Licence | ✅ yes | [`skos`](https://www.w3.org/TR/skos-reference/) |

- **bfo** — The upper ontology (ISO/IEC 21838-2) most serious domain ontologies sit on: continuant vs occurrent, the distinctions you otherwise argue about from scratch. Reach for it when your ontology needs a spine.
- **dublin-core** — The 25-year-old lingua franca for describing ANY resource — title, creator, date, subject, rights. If your system has records, it already half-speaks this.
- **naics** — What industry is this? Firmographics for B2B, and the answer every registry and filing expects. Take it from the Census: the convenience repackagings declare no licence, and the authority is public domain.
- **prov-o** — Who made this, from what, and when. Every audit, lineage and reproducibility story reinvents this badly; it is already standard.
- **qudt** — Units and what they measure, done properly. Any system carrying a number with a unit has this problem, and almost all of them solve it with a string column.
- **ro** — Standard relations — part_of, derives_from, participates_in — so your edges mean what everyone else's edges mean. The counterpart to BFO's nouns, and montology's own `onto relate` is the same idea.
- **schemaorg** — The universal web vocabulary every industry structures data in — 2,454 classes and properties, and what SEO structured-data work speaks. If you join one thing on this page, join this.
- **sic** — NAICS's predecessor, still what many registries and filings use. From the SEC for the same reason NAICS comes from the Census.
- **skos** — Not a vocabulary but the standard SHAPE of one: concepts, broader/narrower, preferred and alternate labels. Half the taxonomies on this page are published in it, and it is what to publish yours in.

### health & life sciences

| ontology | licence | commercial | source |
|---|---|---|---|
| **ChEBI — Chemical Entities of Biological Interest** | CC BY 4.0 | ✅ yes — attribution | [`chebi`](https://obofoundry.org/ontology/chebi.html) |
| **Human Disease Ontology** | CC0 1.0 | 🟢 public domain | [`doid`](https://obofoundry.org/ontology/doid.html) |
| **Gene Ontology** | CC BY 4.0 | ✅ yes — attribution | [`go`](https://obofoundry.org/ontology/go.html) |
| **Mondo Disease Ontology** | CC BY 4.0 | ✅ yes — attribution | [`mondo`](https://obofoundry.org/ontology/mondo.html) |
| **NCI Thesaurus (OBO edition)** | CC BY 4.0 | ✅ yes — attribution | [`ncit`](https://obofoundry.org/ontology/ncit.html) |
| **Uberon multi-species anatomy ontology** | CC BY 3.0 | ✅ yes — attribution | [`uberon`](https://obofoundry.org/ontology/uberon.html) |

- **chebi** — Molecules and their roles, from EMBL-EBI. What to join if anything in your system is a compound, a drug or an ingredient.
- **doid** — The long-standing disease vocabulary Mondo builds on; CC0, so the one to take when attribution is inconvenient.
- **go** — The most-used ontology in science, full stop: molecular function, biological process, cellular component. The proof that a maintained vocabulary compounds in value.
- **mondo** — One disease vocabulary merging OMIM, Orphanet, DOID and NCIt — built precisely because those disagreed. The reference for naming a disease.
- **ncit** — The US National Cancer Institute's reference terminology — broad clinical and biomedical coverage, far past oncology.
- **uberon** — Anatomy across species, cross-referenced to the species-specific ones. The anatomical vocabulary with the widest reach.

### finance

| ontology | licence | commercial | source |
|---|---|---|---|
| **FIBO — Financial Industry Business Ontology** | MIT | ✅ yes | [`fibo`](https://github.com/edmcouncil/fibo) |

- **fibo** — The EDM Council's model of financial instruments, entities, contracts and market roles — the serious answer to what a 'counterparty' or a 'derivative' IS. MIT-licensed, which is unusual for finance and the reason this replaced the proprietary ICB that used to sit here.

### retail & e-commerce

| ontology | licence | commercial | source |
|---|---|---|---|
| **Google Product Taxonomy** | none — a bare .txt on www.google.com, no licence, no terms page, and developers.google.com's CC BY 4.0 site policy does not reach it | 🚫 unlicensed | [`google-product`](https://www.google.com/basepages/producttype/taxonomy.en-US.txt) |
| **Shopify Product Taxonomy** | MIT | ✅ yes | [`shopify-product`](https://github.com/Shopify/product-taxonomy) |

- **google-product** — 5k+ categories every Shopping feed must speak. Listed because you will need it and because the licence is a trap: published FOR building feeds, which is not permission to ship it inside your own product. Reach for shopify-product when you need one you may redistribute.
- **shopify-product** — 10k+ categories with attributes — richer than Google's tree, and the one in this pair you may actually redistribute.

### advertising & media

| ontology | licence | commercial | source |
|---|---|---|---|
| **Google NLP Content Categories** | CC BY 4.0 (Google Cloud docs) | ✅ yes — attribution | [`google-nlp-categories`](https://cloud.google.com/natural-language/docs/categories) |
| **Google Topics API Taxonomy** | W3C Software and Document Licence | ✅ yes | [`google-topics`](https://github.com/patcg-individual-drafts/topics) |
| **IAB Ad Product Taxonomy 2.0** | CC BY 3.0 (as above) | ✅ yes — attribution | [`iab-adproduct`](https://github.com/InteractiveAdvertisingBureau/Taxonomies) |
| **IAB Audience Taxonomy 1.1** | CC BY 3.0 (as above) | ✅ yes — attribution | [`iab-audience`](https://github.com/InteractiveAdvertisingBureau/Taxonomies) |
| **IAB Content Taxonomy 3.1** | CC BY 3.0 (stated in the repo README, no LICENSE file — so every automated scan calls it unlicensed) | ✅ yes — attribution | [`iab-content`](https://github.com/InteractiveAdvertisingBureau/Taxonomies) |
| **OpenOOH Venue Taxonomy** | Apache-2.0 | ✅ yes | [`openooh-venue`](https://github.com/openooh/venue-taxonomy) |
| **IABTechLab/iab-mapper (2.x → 3.0 mappings)** *(evaluate)* | BSD-2-Clause | ✅ yes | [`iab-mapper`](https://github.com/IABTechLab/iab-mapper) |
| **IPTC Media Topics** *(evaluate)* | CC BY 4.0 — IPTC states it for all NewsCodes | ✅ yes — attribution | [`iptc-media-topics`](https://iptc.org/standards/media-topics/) |

- **google-nlp-categories** — ~620 labels Google's classifier emits — useful as a mapping TARGET, not a house vocabulary.
- **google-topics** — ~470 ad-relevant topics; small, curated, and what Chrome's interest signals emit.
- **iab-adproduct** — Names the thing being sold; completes the IAB triple.
- **iab-audience** — The segmentation counterpart to iab-content; audience descriptions marketers already use.
- **iab-content** — THE contextual-targeting and brand-safety vocabulary; what OpenRTB speaks.
- **openooh-venue** — Digital-out-of-home venue types; niche channel, real standard.
- **iab-mapper** — Mappings, not a taxonomy — the open question is whether you have 2.x codes in the wild. Pertinent the day you meet one.
- **iptc-media-topics** — 1,200 terms, 13 languages, a real standard — the open question is RDF/SKOS parsing, which is its own project. Decide when PR or content work needs it.

### agriculture & food

| ontology | licence | commercial | source |
|---|---|---|---|
| **AGRO — the Agronomy Ontology** | CC BY 4.0 | ✅ yes — attribution | [`agro`](https://obofoundry.org/ontology/agro.html) |
| **FoodOn — the Food Ontology** | CC BY 4.0 | ✅ yes — attribution | [`foodon`](https://obofoundry.org/ontology/foodon.html) |

- **agro** — Agronomic practices, traits and inputs; joins FoodOn upstream of the plate.
- **foodon** — Food products, sources and processing — for menus, supply chains, nutrition and recall traceability alike.

### environment & climate

| ontology | licence | commercial | source |
|---|---|---|---|
| **ENVO — the Environment Ontology** | CC0 1.0 | 🟢 public domain | [`envo`](https://obofoundry.org/ontology/envo.html) |

- **envo** — Biomes, environmental materials and features — the vocabulary for where something is, in ESG, climate and sustainability reporting.

### software & infrastructure

| ontology | licence | commercial | source |
|---|---|---|---|
| **AsyncAPI Specification** | Apache-2.0 | ✅ yes | [`asyncapi`](https://www.asyncapi.com/docs/reference/specification/latest) |
| **CDEvents (Continuous Delivery Foundation)** | Apache-2.0 | ✅ yes | [`cdevents`](https://cdevents.dev/) |
| **Conventional Commits** | MIT | ✅ yes | [`conventional-commits`](https://www.conventionalcommits.org/) |
| **OWASP CycloneDX** | Apache-2.0 | ✅ yes | [`cyclonedx`](https://cyclonedx.org/specification/overview/) |
| **JSON Schema** | BSD-style (JSON Schema Specification Authors) | ✅ yes | [`json-schema`](https://json-schema.org/specification) |
| **OpenAPI Specification** | Apache-2.0 | ✅ yes | [`openapi`](https://spec.openapis.org/oas/latest.html) |
| **OpenTelemetry Semantic Conventions** | Apache-2.0 | ✅ yes | [`otel-semconv`](https://opentelemetry.io/docs/specs/semconv/) |
| **purl — Package URL specification** | MIT | ✅ yes | [`purl`](https://github.com/package-url/purl-spec) |
| **Semantic Versioning** | CC BY 3.0 | ✅ yes — attribution | [`semver`](https://semver.org/) |
| **SPDX — specification and licence list** | Community Specification Licence 1.0; pre-existing portions CC BY 3.0 | ✅ yes — attribution | [`spdx`](https://spdx.org/licenses/) |
| **SWO — the Software Ontology** | CC BY 4.0 | ✅ yes — attribution | [`swo`](https://obofoundry.org/ontology/swo.html) |
| **DOAP — Description of a Project** *(evaluate)* | Apache-2.0 | ✅ yes | [`doap`](https://github.com/ewilderj/doap) |
| **OASIS TOSCA (Topology and Orchestration Specification)** *(evaluate)* | Apache-2.0 | ✅ yes | [`tosca`](https://github.com/oasis-open/tosca-community-contributions) |

- **asyncapi** — OpenAPI's counterpart for event-driven systems: channels, messages, operations, bindings. The names for the half of a distributed system that is not request/response.
- **cdevents** — A common vocabulary for what happens in a pipeline — build queued, artifact published, service deployed — so tools from different vendors describe the same event the same way.
- **conventional-commits** — A tiny, near-universal taxonomy of CHANGE: feat, fix, refactor, chore, and what each implies for a version. The smallest useful vocabulary on this page and probably the most widely adopted.
- **cyclonedx** — Bill of materials for software, services, hardware and ML models — what a component IS, what it depends on and where it came from.
- **json-schema** — How to say what a document must look like — the shape language OpenAPI, AsyncAPI and Croissant all build on.
- **openapi** — The vocabulary of an HTTP API — operation, path, parameter, schema, response, security scheme. Whatever your service calls these things internally, this is what its consumers call them.
- **otel-semconv** — The one to reach for. Names services, hosts, containers, cloud providers, HTTP, RPC, databases, messaging and their attributes — the vocabulary your telemetry already emits, which makes it the vocabulary your infrastructure already speaks whether you wrote it down or not.
- **purl** — One identity for a package across every ecosystem: pkg:npm/foo@1.2.3. The join key the whole supply chain agreed on, and the answer to 'is this the same dependency' across tools.
- **semver** — What MAJOR, MINOR and PATCH mean — a three-term vocabulary that ends the argument about whether a change is breaking.
- **spdx** — The canonical identifiers for software licences (`Apache-2.0`, `CC-BY-4.0`) plus the SBOM spec around them. Every licence string in montology's own registry is an SPDX id.
- **swo** — What a piece of software IS — its licence, version, inputs, outputs and the task it performs. OBO-reviewed, which almost nothing else in this group is.
- **doap** — The RDF vocabulary for describing a software project — repository, release, maintainer, language. A finished, stable spec rather than an abandoned one, but the open question is whether you need RDF at all when purl and SPDX cover identity and licensing already.
- **tosca** — A vendor-neutral vocabulary for cloud application topology — nodes, relationships, capabilities, requirements. The open question is adoption: it is a real OASIS standard that most teams have replaced with their orchestrator's own nouns.

### security

| ontology | licence | commercial | source |
|---|---|---|---|
| **CVE — Common Vulnerabilities and Exposures** | CC0 1.0 | 🟢 public domain | [`cve`](https://www.cve.org/) |
| **CWE — Common Weakness Enumeration** | MITRE royalty-free licence (research, development AND commercial; reproduce the copyright designation) | ✅ yes — attribution | [`cwe`](https://cwe.mitre.org/) |
| **MITRE D3FEND — defensive countermeasures** | MIT | ✅ yes | [`d3fend`](https://d3fend.mitre.org/) |
| **MITRE ATT&CK** | MITRE royalty-free licence (research, development AND commercial; reproduce the copyright designation) | ✅ yes — attribution | [`mitre-attack`](https://attack.mitre.org/) |

- **cve** — The identifier for a specific vulnerability instance — the WHICH to CWE's what-class-of-bug. CC0, so nothing constrains reuse.
- **cwe** — The classification of software weakness TYPES — what class of bug this is, as opposed to CVE's which instance. What every scanner reports in.
- **d3fend** — The counterpart to ATT&CK: what you DO about a technique, as a real ontology with typed relations back to the attacks it addresses.
- **mitre-attack** — Adversary tactics and techniques — the vocabulary every detection, threat-intel and red-team report already speaks. MITRE grants a royalty-free commercial licence explicitly.

### AI, ML & data science

| ontology | licence | commercial | source |
|---|---|---|---|
| **Croissant — ML dataset metadata (MLCommons)** | Apache-2.0 | ✅ yes | [`croissant`](https://github.com/mlcommons/croissant) |
| **EDAM — data, operations, formats and identifiers** | CC BY-SA 4.0 | ⚠️ yes — share-alike | [`edam`](https://edamontology.org/) |
| **MITRE ATLAS — adversarial threats to AI systems** | Apache-2.0 | ✅ yes | [`mitre-atlas`](https://atlas.mitre.org/) |
| **OWASP Top 10 for LLM Applications** | CC BY-SA 4.0 | ⚠️ yes — share-alike | [`owasp-llm`](https://genai.owasp.org/llm-top-10/) |
| **STATO — the Statistical Methods Ontology** | CC BY 3.0 | ✅ yes — attribution | [`stato`](https://obofoundry.org/ontology/stato.html) |

- **croissant** — Describes an ML dataset: its records, fields, splits, provenance and licence. Built on Schema.org, adopted by Hugging Face, Kaggle and OpenML — the closest thing to a standard a dataset has.
- **edam** — What an analysis DOES and what it consumes and produces: operations, data types, formats, identifiers. Grew up in bioinformatics and the operation/format halves are domain-neutral.
- **mitre-atlas** — ATT&CK's shape applied to machine learning: prompt injection, model evasion, data poisoning, model theft, named and structured. The nearest thing to a settled vocabulary for how AI systems get attacked.
- **owasp-llm** — The risk vocabulary LLM application teams actually cite — prompt injection, insecure output handling, excessive agency. A ranked list rather than an ontology, and it is what people mean by these terms.
- **stato** — Names statistical tests, distributions, model parameters and what a result means — so 'significant' and 'confidence interval' stop being whatever the last analyst meant by them.

### geography

| ontology | licence | commercial | source |
|---|---|---|---|
| **GeoNames ontology + gazetteer** | CC BY 4.0 | ✅ yes — attribution | [`geonames`](https://www.geonames.org/ontology/documentation.html) |

- **geonames** — 11M+ place names with a feature-type vocabulary (country, city, admin division, landmark). The open answer to 'what kind of place is this'.

### trade & occupations

| ontology | licence | commercial | source |
|---|---|---|---|
| **Harvard Growth Lab classifications (ISIC/HS/SITC/O*NET)** *(evaluate)* | BSD-3-Clause | ✅ yes | [`cid-classifications`](https://github.com/cid-harvard/classifications) |

- **cid-classifications** — Many systems in one cleaned repo — incl. O*NET occupations for workforce mapping. The open question is which one you need: it is heavy, and taking all of it is taking four vocabularies you did not ask for.

### research & information

| ontology | licence | commercial | source |
|---|---|---|---|
| **DCAT — Data Catalog Vocabulary (W3C)** | W3C Software and Document Licence | ✅ yes | [`dcat`](https://www.w3.org/TR/vocab-dcat-3/) |
| **IAO — Information Artifact Ontology** | CC BY 4.0 | ✅ yes — attribution | [`iao`](https://obofoundry.org/ontology/iao.html) |

- **dcat** — How to describe a dataset and a catalogue of them — what every government open-data portal publishes in, and what a data catalogue should not reinvent.
- **iao** — Documents, datasets, identifiers, measurements — what an information thing IS, as opposed to what it is about. The distinction most data models blur.

### general knowledge

| ontology | licence | commercial | source |
|---|---|---|---|
| **wikidata-taxonomy (extraction CLI)** *(evaluate)* | MIT (the tool; Wikidata's own data is CC0) | ✅ yes | [`wikidata-taxonomy`](https://github.com/nichtich/wikidata-taxonomy) |

- **wikidata-taxonomy** — A tool, not a dataset — it mints a niche taxonomy out of Wikidata on demand. The open question is whether the niche you need is actually in there; Wikidata's coverage is wide and its depth is uneven.
An entry marked *(evaluate)* is promising with a question still open;
the note says which. Declined candidates are not listed — a registry that is
one-third things nobody should use reads as a search result, not a
recommendation. Those declines and their reasons live in the git history of
`.monty/onto/src/montology_ontology/sources.py`.

**The state of agent-architecture vocabulary, stated precisely.** There is no
formal *ontology* for agents, tools, memory and planning — FIPA's agent
standards are two decades dormant and nothing replaced them. But there IS an
operationalized, actively maintained vocabulary: **OpenTelemetry's GenAI
semantic conventions** (`otel-genai`) normatively define `gen_ai.agent.*`,
`gen_ai.tool.*`, `gen_ai.memory.*`, `gen_ai.conversation.*` and named
operations — `create_agent`, `invoke_agent`, `execute_tool`. Agents, tools,
memory and conversations, Apache-2.0, shipping commits daily.

What it is not is an ontology: telemetry attributes have no subsumption, no
metaproperties, and nothing a gate can enforce. So the gap is narrower and
more specific than "nothing exists" — it is the ontological layer over a
vocabulary the industry has already adopted. That is what
[`mon-uxs5`](.tickets/mon-uxs5.md) plans: LOT methodology with NeOn's
reuse-first scenarios, governed by the rule that already decides what
montology will model — **an edge nothing can check is a diagram**.

*Every licence here was checked against its source on 2026-09-01 and is recorded AS PUBLISHED. This is a starting point for your own diligence, not legal advice — terms change, and an unstated licence is never a permissive one.*

The registry is a **catalogue, not an ingest** in this era: it tells you what
exists, whether it is real, and whether you may use it. Wiring a source into
`.monty/ontology.db` is per-source work.
## Contributors

```sh
git clone https://github.com/shinyobjectz/montology && cd montology
uv sync && just              # the action surface
just check                   # the gate (montology lints itself, strictly:
                             # its own toml sets collisions = "enforce")
```

Changes go in [`CHANGELOG.md`](CHANGELOG.md) under `Unreleased`.
