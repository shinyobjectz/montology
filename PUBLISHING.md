# Publishing — what remains needs the account owner

The engine and the front door are ready; two registry steps require the
`zaiusai` accounts (2FA), and no automation can do them.

## npm (`montology`, bin `monty`)

The package at `npm/` is complete and the name is free. Your account
requires a second factor for publish, so the token in `~/.npmrc`
authenticates but cannot publish. Either:

    cd npm && npm publish --access public
    # complete the browser step npm prints, once

…or mint an **Automation**-type granular token at npmjs.com (bypasses
2FA), replace the line in `~/.npmrc`, and re-run the publish.

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
