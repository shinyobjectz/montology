#!/usr/bin/env sh
# The firewall, as a plugin ships it.
#
# `monty init` writes this hook into a repo's own settings; a PLUGIN install
# has no init to run, so the same firewall has to arrive with the plugin and
# be invisible in every repo that is not a montology workspace. Two rules
# follow from that, and both are load-bearing:
#
#   * bail in pure shell, before any interpreter starts. A hook on the write
#     path runs on every edit in every repo the user opens; paying a Python
#     import to discover "not a workspace" would tax people who never asked
#     for montology, and a slow hook is a hook that gets deleted.
#   * fail OPEN, always. No engine, no workspace, a broken payload — exit 0.
#     Breaking someone's editor is a worse failure than missing one collision.
#
# Deny is exit 2 with the repair on stderr; the harness feeds that straight
# back to the model, which corrects and retries.

# The workspace marker, found the way git finds .git. Hooks run with the
# project directory as cwd, which is the right place to start walking.
dir=$(pwd)
while :; do
    [ -d "$dir/.monty" ] && break
    [ "$dir" = "/" ] || [ -z "$dir" ] && exit 0
    dir=$(dirname "$dir")
done

# A workspace pins its own engine in montology.toml — the one written by the
# `monty init` that made it. Reading it here beats a second hard-coded copy
# of the spec that would drift away from the first one silently.
if command -v monty >/dev/null 2>&1; then
    exec monty guard
fi
command -v uvx >/dev/null 2>&1 || exit 0

spec=$(sed -n 's/^engine[[:space:]]*=[[:space:]]*"\(.*\)"[[:space:]]*$/\1/p' \
    "$dir/.monty/montology.toml" 2>/dev/null | head -1)
[ -n "$spec" ] || spec="git+https://github.com/shinyobjectz/montology@main#subdirectory=.monty/cli"

exec uvx --from "$spec" monty guard
