# Publishing — what remains needs the account owner

The engine and the front door are ready; two registry steps require the
`zaiusai` accounts (2FA), and no automation can do them.

## npm — DONE (2026-08-10)

`montology@0.2.0` is live: `npm install -g montology` works from the
public registry (verified with a clean global install). The token in
~/.npmrc has publish rights; future releases are `cd npm && npm version
<x.y.z> && npm publish`.

## skills.sh — DONE under the OLD name; the new name is catching up

skills.sh keys its repo page to the slug people INSTALL with, and the
first installs used `socialite-ml/montology`. So the live repo page is
https://skills.sh/socialite-ml/montology (GitHub 301-redirects the old
name, so every skill — montology, words, intake — renders there), while
https://skills.sh/shinyobjectz/montology 404s until installs under the
new slug are aggregated (one was recorded 2026-08-22; the leaderboard
refreshes in batches). Per-skill pages work under BOTH names today:
https://skills.sh/shinyobjectz/montology/intake etc. `npx skills add
shinyobjectz/montology --list` discovers every skill in the top-level
`skills/` mirror (the gate diffs it against `.plugin/skills/`).

## PyPI (uvx montology without git)

`.github/workflows/publish.yml` uses trusted publishing. On pypi.org,
add a *pending publisher* for each package (montology, montology-core,
montology-ontology, montology-scan, montology-gen): owner
`socialite-ml`, repo `montology`, workflow `publish.yml`, environment
`pypi`. Then:

    git tag v0.1.0 && git push --tags

## After the first release: flip the engine pin

Change `git+…@main#subdirectory=.monty/cli` → `montology==<version>` in:
`.monty/cli/src/montology_cli/_engine.py` (ENGINE_SPEC),
`npm/package.json` (montology.engine), `.plugin/mcp.json`. One commit,
tagged with the release.
