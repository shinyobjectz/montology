---
id: mon-qyb3
status: in_progress
deps: [mon-ll1c]
links: []
created: 2026-08-25T19:38:08Z
type: task
priority: 2
assignee: shinyobjectz
parent: mon-gh8j
tags: [review, scan, semantics]
---
# monty onto review: the anti-pattern catalogue, named, on machinery we already have

Palantir's most stealable asset is not their metamodel, it is their named anti-pattern list — because a shared NAME is what makes review possible. 'This is a God Object' ends an argument that 'this feels wrong' cannot. Half of their catalogue is already computable here; it is just not named or surfaced.

## Design

Port the catalogue onto existing instruments, and be honest where an instrument is a heuristic rather than a proof — each finding says which it is.

  - The Misnomer (vague or misleading names) — `onto similar` already computes semantic neighbours; a word whose nearest neighbour is itself vague is the signal.
  - System Silos (one entity split by source system) — `onto audit --threshold` already finds meanings that collide by cosine. This IS that check, given a name.
  - The Kitchen Sink (ETL artefacts as vocabulary) — the no-vendor law already covers part of it; extend to pipeline and timestamp shapes.
  - The God Object (one word answering for several things) — bearing count and declaration spread across unrelated packages; the divergence law is the strict half of this and already exists.
  - The Time Machine (a version or a date inside a name) — a new check, and a trivial one.
  - Department Silos — needs an owner concept montology does not have. Skip it and say so.
  - Action Sprawl / The Golden Hammer — not applicable without a kinetic layer. Skip, and say why, because a catalogue with silent omissions reads as a catalogue that found nothing.

Findings are advisory, never a build failure. The gate is for facts; an anti-pattern is a judgement, and a judgement that fails a build is a judgement people learn to route around.

Competency questions belong here eventually — the ontology is correct if it answers the questions it was built to answer — but they need the intake work first.

## Acceptance Criteria

`monty onto review` runs on qubie and montology and names findings with the anti-pattern they instantiate, the evidence, and a repair. Skipped checks are listed as skipped with the reason. Nothing it reports fails a build. The canvas surfaces the same findings on the nodes they concern.

