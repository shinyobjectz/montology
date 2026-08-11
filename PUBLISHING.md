# Publishing — what remains needs the account owner

The engine and the front door are ready; two registry steps require the
`zaiusai` accounts (2FA), and no automation can do them.

## npm — DONE (2026-08-10)

`montology@0.2.0` is live: `npm install -g montology` works from the
public registry (verified with a clean global install). The token in
~/.npmrc has publish rights; future releases are `cd npm && npm version
<x.y.z> && npm publish`.

## skills.sh — DONE (2026-08-10)

Auto-indexed: https://skills.sh/socialite-ml/montology (2 skills, the
`npx skills add socialite-ml/montology` command shown on-page). The
top-level `skills/` mirror is what the installer discovers; the gate
diffs it against `.plugin/skills/` so it cannot drift.

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
