---
id: mon-gskj
status: in_progress
deps: []
links: []
created: 2026-08-25T19:38:08Z
type: task
priority: 1
assignee: shinyobjectz
parent: mon-gh8j
tags: [canvas, ui, build]
---
# canvas/: the Svelte Flow app, and the generated-not-authored discipline for its bundle

A vite + svelte + @xyflow/svelte app in canvas/, whose BUILT OUTPUT is committed into the Python package so `monty canvas` works from a uvx install with no Node on the machine. The engine must stay pure Python at runtime; the toolchain is a build-time concern only.

## Design

The intake package is the precedent and it should be followed almost literally: a stdlib ThreadingHTTPServer bound to localhost on an ephemeral port, a self-contained page, the browser opened for you, state on disk as the contract. What differs is that intake renders its page from Python and this one serves a built asset.

The bundle is GENERATED MATERIAL and gets the same treatment as the words skill: a provenance header naming the source hash, and a lint law that fails the build when the committed bundle does not match what canvas/ would produce. Hand-editing a minified bundle is exactly the kind of drift this repo exists to catch, and a generated artefact with no gate on it is how the last vocabulary drifted.

Vendors are not vocabulary: svelte, vite and xyflow belong in package.json and in method prose, never in a word or a definition. The existing no-vendor law already covers the second half.

Open question to settle while building: whether the bundle is committed to git (simple, works from a git pin, costs diff noise) or built in CI and attached to a release (clean, but montology installs FROM A GIT REF today, so a release artefact is not reachable). Leaning committed, for the same reason the engine pin is a git URL.

## Acceptance Criteria

`monty canvas` on a machine with no Node installed opens a page that renders. `just check` fails when canvas/ has moved and the bundle has not been rebuilt, with the rebuild command in the error. The npm/ launcher story is unchanged.

