---
id: mon-ll1c
status: in_progress
deps: []
links: []
created: 2026-08-25T19:38:08Z
type: task
priority: 1
assignee: shinyobjectz
parent: mon-gh8j
tags: [canvas, scan, api]
---
# The graph endpoint: the whole ontology as nodes and edges, in one deterministic read

One function that returns the vocabulary AND the code it governs as a node/edge document. This is the contract the canvas renders, and it is worth having on its own — `monty canvas graph` piped to jq answers questions today that need three commands and a squint.

## Design

Deterministic, model-free, assembled from the database plus the scan — the same discipline as sync. An instrument, so what cannot be measured is absent rather than invented.

NODES: word (kind, owner, code, pos, definition, test, declaration count, wrong-resolution count), ruling (overload | collision | rename | exception — a node, not an edge, because each carries a why and a date), surface (kind, owner, version), candidate (a recurring declared name with no word, from scan --candidates), doctrine, token.

EDGES: contains (owner and dotted code), routes (from_term to to_word, carrying its REGISTER and scope — the label is the register, because that is the thing no vendor models), bears (word to surface), seams (surface to surface, with direction), governs (doctrine to the words it names), asks (candidate to the nearest existing word, from onto similar).

The candidate-to-word edge is the one that needs care: it comes from the semantic audit and is a SUGGESTION, so it must be marked as such in the payload and drawn differently. An instrument that hands back a guess dressed as a fact is worse than one that says nothing.

Shape: {nodes: [...], edges: [...], stats: {...}, fingerprint: sha256}. The fingerprint is the same instrument hash sync uses, so a canvas can tell it is looking at stale data.

## Acceptance Criteria

`monty canvas graph` prints valid JSON for montology (26 words) and qubie (99 words, 5,237 declarations) in under two seconds, every edge type present, candidates marked as suggestions, and the fingerprint matching what `monty sync` computes. Tests pin the shape.

