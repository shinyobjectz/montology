---
id: mon-uxs5
status: open
deps: []
links: []
created: 2026-09-01T18:58:28Z
type: epic
priority: 1
assignee: shinyobjectz
tags: [ontology, research, agents, software, taxonomy]
---
# The agent-architecture ontology: the layer over the vocabulary that exists

CORRECTED 2026-09-01, BEFORE ANY WORK STARTED. This epic was opened on the
claim that no agent vocabulary exists. That was wrong, and finding out how
wrong is the most useful thing that has happened to it.

**OpenTelemetry's GenAI semantic conventions** (`otel-genai`, Apache-2.0,
commits landing daily) normatively define `gen_ai.agent.{id,name,version,
description}`, `gen_ai.tool.{name,type,description,call.arguments,
call.result}`, `gen_ai.memory.{store.id,record.id,query.text}`,
`gen_ai.conversation.{id,compacted}`, and the operations `create_agent`,
`invoke_agent`, `execute_tool`, `chat`, `embeddings`. Agents, tools, memory,
conversations and operations — the exact four things this ticket was opened
to say had no names.

So the gap is REAL but much narrower, and it is a different KIND of gap.
What `otel-genai` gives is a flat namespace of telemetry attributes: no
subsumption, no metaproperties, no relations, and nothing a gate can
enforce. What it cannot answer is whether "orchestrator" is a kind of agent
or a role an agent plays; whether a session is a continuant or an occurrent;
which of two names for the same thing wins. Those are ontology questions,
and they are montology's actual lane.

**The work is therefore not to invent a vocabulary. It is to give an adopted
one the ontological layer and the gate it lacks** — which is a far more
defensible project than the one this ticket originally described, and much
harder to do badly, because the terms are no longer ours to choose.

We are unusually well placed to do it: we ship the gate that would enforce
it, we dogfood it on ourselves, and the users who would adopt it are the
ones already running agents against our guard.

The case AGAINST, which has to be answered before any of this ships:
authoring a domain ontology is exactly what `mon-by5n` decided montology
would not drift into. Read that ticket first. Its test is the one that
governs here.

## The constraint that governs everything below

From `mon-by5n`: **every edge montology has is enforceable, and an edge
nothing can check is a diagram — the artefact this repo exists to
replace.** An agent ontology full of `hasMemory` and `invokesTool`
assertions that no scan can verify would be precisely the thing we refused
to build for other domains, wearing a fashionable hat.

The discipline this forces is good: a term earns its place when a scan
can find it in code, or when a ruling about it changes what the gate does.
"Does tree-sitter see it?" is the acceptance test for every candidate
term, and it is the question that should kill most of them.

## Why we are qualified to judge our own work here

Montology already implements, without naming them as such, four of the
primitives that ontology engineering research says an ontology needs:

| research primitive | montology already has |
|---|---|
| competency questions (Grüninger & Fox) | `monty onto questions` — checked both ways |
| OntoClean metaproperties (Guarino & Welty) | `monty onto rigidity` — rigid vs anti-rigid |
| subsumption with inheritance | `monty onto genus` |
| textual definitions + a test (OBO principle 6) | every `onto add` requires both |
| anti-pattern catalogue | `monty onto review` |
| change governance | `monty onto proposals` |

That is most of a methodology already in the box. The plan below is
mostly a matter of pointing it at ourselves in the right order.

## Method: LOT, because it is the industrial one

Four methodologies are live in the literature — METHONTOLOGY (the classic),
NeOn (scenario-based, reuse-first), SAMOD (agile, test-driven) and LOT
(Linked Open Terms, industrial). **Use LOT as the spine and borrow NeOn's
reuse scenarios**, because LOT's four activities map cleanly onto commands
we already have, and NeOn's central insight — build an ontology NETWORK by
reusing existing resources rather than an ontology from scratch — is the
difference between a credible artefact and a vanity one.

LOT's loop, mapped:

1. **Requirements** → competency questions (`onto ask` / `onto questions`)
2. **Implementation** → `onto add` / `genus` / `relate` / `rigidity`
3. **Publication** → `monty sync`, and the db IS the distributable artefact
4. **Maintenance** → `onto amend`, `onto proposals`, `monty lint` in CI

Each phase below is a child ticket. None of them starts by writing terms.

## Phase 1 — requirements, before any term exists

Write the competency questions FIRST and record them with `monty onto ask`.
An ontology is complete when it answers its questions and not before; a
term that answers no question is vocabulary nobody asked for, which is a
finding `onto questions` already reports both ways.

Draft seeds, to be argued and cut:

- What tools may this agent call, and which of them can write?
- What did this agent do, in what order, and on whose behalf?
- Where did this claim in the output come from?
- What is remembered between runs, and what is scoped to one?
- When one agent hands off to another, what crosses the boundary?
- What is the difference between a retry, a fallback and an escalation?
- Which step failed, and was the failure the model's or the tool's?

Acceptance: 15–25 questions, each traceable to a real thing someone needed
to ask and could not. Reject any question invented to justify a term.

## Phase 2 — reuse before minting (NeOn scenario 2/3)

For every concept the questions demand, search the 57 sources BEFORE
authoring: `monty onto sources`, `monty onto check`, `monty onto similar`.
The honest expectation is that a real fraction is already covered:

- **otel-genai** — START HERE. It already names agents, tools, memory,
  conversations and the operations between them. A term it has is a term we
  must not re-mint under another spelling; the most likely failure of this
  whole epic is authoring `tool_invocation` next to its `execute_tool`.
- **PROV-O** — agent, activity, entity, `wasGeneratedBy`, `actedOnBehalfOf`.
  Provenance is most of what an agent TRACE is, and W3C standardised it in
  2013. Where otel-genai says what a field is called, PROV-O says what the
  relation between two of them IS — which is the half otel does not have.
- **BFO / RO** — continuant vs occurrent settles whether a "session" is a
  thing or a happening, which is the argument every agent codebase has.
- **otel-semconv** — spans, services, attributes: agent runs are traces,
  and the observability world already named the parts.
- **schema.org** `Action` — a modelled action with agent, object, result.
- **mitre-atlas / owasp-llm** — the failure and attack vocabulary; do not
  re-mint prompt injection.

Acceptance: a written REUSE MAP — every competency question mapped to an
existing term or explicitly marked as a gap, with the reason. A gap
claimed without a search of all 57 is not a gap.

## Phase 3 — mint only the residue, under the enforceability test

Whatever Phase 2 could not cover gets authored, and each term must pass:

1. **Does a scan see it?** Name a tree-sitter query, an ast-grep pattern,
   or a declaration kind that finds it in real code. If nothing finds it,
   it does not go in.
2. **`--pos`** — verb, noun or value, so a collision on it can be judged.
3. **`--test`** — the one-line what-is-it.
4. **Rigidity** — `onto rigidity` for anything that could be a role rather
   than a kind. "Orchestrator" is almost certainly anti-rigid; "tool call"
   almost certainly rigid. Getting this wrong is how a subsumption
   hierarchy goes bad, which is exactly what OntoClean exists to catch.
5. **Genus** — what kind of thing it is, so it inherits rulings.

Acceptance: every minted term has all five, and `monty onto review` is
clean. Expect the residue to be SMALL. If Phase 3 mints eighty terms,
Phase 2 was not done honestly.

## Phase 4 — validate against real code, not against taste

The ontology is a hypothesis until it survives contact with a codebase.
Run it against agent repos the way `stress/run.py` runs against the eight:
candidates mined, collisions reported, and the interesting number is
**what fraction of an agent codebase's recurring declarations the ontology
has a word for**. A vocabulary that covers 10% of what agent code declares
is not comprehensive whatever its author believes.

Acceptance: measured coverage on at least five real agent codebases, with
the misses listed. The misses are the next iteration's Phase 1.

## Phase 5 — software development, the same loop

Deliberately second, and only after the agent pass has proven the method.
The library is already strongest here (13 sources), so Phase 2's reuse map
will be dense and Phase 3's residue thin — which makes it the better test
of whether we can resist minting. Terms here must clear a higher bar
precisely because so much exists: OpenAPI, AsyncAPI, CDEvents, SPDX, purl,
CWE, semver and Conventional Commits between them already name most of
what a software project does.

## Publication, if it survives

If and only if Phases 1–4 produce something that measures well: publish it
the way the sources we respect are published — an open licence (CC BY 4.0
is the field norm and what most of our registry carries), stable
identifiers, versioning, textual definitions on every term, a named locus
of authority. That is the OBO Foundry principle set, and meeting it is
what would make this the 57th entry in our own library rather than another
vendor's vocabulary nobody adopted.

## Acceptance criteria

- [ ] `mon-by5n`'s enforceability test is answered IN WRITING for this
      domain before Phase 3 mints anything
- [ ] 15–25 competency questions recorded via `onto ask`
- [ ] a reuse map covering every question against all 57 sources,
      `otel-genai` and PROV-O first
- [ ] every minted term carries pos, test, rigidity, genus and a named
      scan that finds it
- [ ] coverage measured on ≥5 real agent codebases, misses listed
- [ ] `monty onto review` and `monty lint` clean
- [ ] a decision recorded on whether to publish, either way

## The honest risk

The likeliest outcome is not failure but DILUTION: that we author forty
plausible terms, none of which a scan can find, and end up with the
diagram `mon-by5n` refused. The correction above sharpens this — with
`otel-genai` in hand, a minted term now has to justify itself against an
adopted standard, not against an empty field. The mitigation is that Phase 3's first test is
mechanical, and the second is a measurement. If the coverage number comes
back low, the answer is to publish the reuse map and the questions and
NOT the ontology — which would still be a real contribution, because the
finding that agent architecture is mostly PROV-O plus telemetry is worth
knowing.
