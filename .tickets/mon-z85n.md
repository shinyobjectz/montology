---
id: mon-z85n
status: open
deps: [mon-ll1c, mon-gskj]
links: []
created: 2026-08-25T19:38:08Z
type: task
priority: 1
assignee: shinyobjectz
parent: mon-gh8j
tags: [canvas, ui]
---
# Build mode: render the five edges montology already has, read-only

The first thing that ships, and deliberately read-only. It will teach us more about what the canvas needs than any further design will — and it is useful immediately, because nobody has ever SEEN qubie's 99 words as a graph.

## Design

Custom Svelte Flow node types, one per node kind, each with at least one Handle. Word nodes coloured by kind (core / inner / adopted / custom) with the declaration count on the node — a word with 200 declarations and a word with none should not look alike, because that difference is the whole point of the scan.

Ruling nodes are visually distinct from word nodes: they are decisions, not vocabulary. Route edges carry their REGISTER as the label. Candidate nodes are greyed and their suggested edges dashed, per the graph-endpoint rule about suggestions.

Layout: containment drives it — a word sits inside its owner. Dagre or elk for the initial pass; positions are not persisted in v1 (a saved layout is state that drifts from the database, and the database is the truth).

Built-in Background, MiniMap, Controls and Panel come with the library — use them rather than reinventing. The Panel carries the vitals: word count, declarations, unresolved candidates, the gate's verdict.

Filtering matters more than it sounds at qubie's size: by kind, by owner, by 'has code resolving to it', by 'appears in a ruling'. 99 word nodes with five edge types is already past what an unfiltered canvas can show honestly.

## Acceptance Criteria

qubie's ontology renders legibly: every word, every rename, every collision, every route with its register, and the candidates the scan is asking for. Clicking a word shows its definition, its test, and the files whose declarations resolve to it. Nothing writes.

