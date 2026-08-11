"""The stress battery: montology against real repos, one per language family.

Run with:  uv run python stress/run.py [--keep] [workdir]

Per repo, four PROVABLE properties (plus recorded judgment calls):

  1. init is merge-safe and idempotent — a pre-existing CLAUDE.md and
     .mcp.json survive with exactly one montology section/key after TWO
     runs.
  2. scan parses at scale — declaration counts and wall time, unparsable
     files counted, unknown languages said out loud.
  3. the collision law fires truthfully — a word picked FROM THE REPO'S
     OWN SCAN is defined as core; lint must fail naming that file; an
     allow entry turns it green (the exception as a decision).
  4. migrate round-trips losslessly — rename X -> XZq --apply, back, and
     `git diff` must be EMPTY. Token-rewrites that cannot be undone are
     rewrites we should not be doing.

Candidates (top 5) are recorded for human judgment — whether mined names
are real vocabulary is not machine-checkable.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

MONTY_ROOT = Path(__file__).resolve().parents[1]

REPOS = [
    # (name, clone url, ref)
    ("flask", "https://github.com/pallets/flask", "3.1.0"),
    ("excalidraw", "https://github.com/excalidraw/excalidraw", "v0.18.0"),
    ("gin", "https://github.com/gin-gonic/gin", "v1.10.0"),
    ("ripgrep", "https://github.com/BurntSushi/ripgrep", "14.1.1"),
    ("phoenix", "https://github.com/phoenixframework/phoenix", "v1.7.19"),
    ("sinatra", "https://github.com/sinatra/sinatra", "v4.1.1"),
    ("spring-petclinic", "https://github.com/spring-projects/spring-petclinic", "main"),
    ("redis", "https://github.com/redis/redis", "7.4.2"),
]


def run(cmd: list[str], cwd: Path, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def monty(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return run(["uv", "run", "--project", str(MONTY_ROOT), "--no-sync", "monty", *args], cwd)


def prepare(workdir: Path, name: str, url: str, ref: str) -> Path | None:
    repo = workdir / name
    if repo.exists():  # cached clone: reset to honest state for re-runs
        run(["git", "checkout", "--", "."], repo)
        run(["git", "clean", "-qfdx"], repo)
    if not repo.exists():
        got = run(["git", "clone", "--depth", "1", "--branch", ref, url, str(repo)],
                  workdir, timeout=900)
        if got.returncode != 0:
            print(f"  clone failed: {got.stderr.strip()[-200:]}")
            return None
    # pre-existing agent files: the merge-safety fixture
    (repo / "CLAUDE.md").write_text("# Their instructions\n\nTheir rules.\n")
    (repo / ".mcp.json").write_text(json.dumps({"mcpServers": {"theirs": {"command": "x"}}}))
    run(["git", "add", "-A"], repo)
    run(["git", "-c", "user.email=s@s", "-c", "user.name=s", "commit", "-qm", "fixture"], repo)
    return repo


def stress_one(repo: Path) -> dict:
    row: dict = {"repo": repo.name}
    sys.path[:0] = [str(MONTY_ROOT / ".monty" / m / "src") for m in ("core", "onto", "scan", "gen")]
    from montology_scan import declarations  # noqa: E402

    # 1. init, twice — merge-safe, idempotent
    for _ in range(2):
        got = monty(["init", "--yes", "--json", "--agents", "claude"], repo)
        ok = got.returncode == 0 and json.loads(got.stdout.splitlines()[-0] and got.stdout)["ok"]
        if not ok:
            row["init"] = f"FAIL: {got.stderr.strip()[-160:]}"
            return row
    claude_md = (repo / "CLAUDE.md").read_text()
    mcp = json.loads((repo / ".mcp.json").read_text())
    row["init"] = ("ok" if claude_md.startswith("# Their instructions")
                   and claude_md.count("montology:begin") == 1
                   and set(mcp["mcpServers"]) == {"theirs", "montology"}
                   else "FAIL: merge broke")

    # 2. scan, timed (in-process — measures the engine, not uv startup)
    t0 = time.monotonic()
    surface = declarations(repo)
    dt = time.monotonic() - t0
    row["files"] = surface["files"]
    row["decls"] = len(surface["decls"])
    row["errors"] = surface["errors"]
    row["skipped"] = ", ".join(f"{k}:{v}" for k, v in surface["skipped_langs"].items()) or "—"
    row["scan_s"] = round(dt, 2)

    # 3. candidates — recorded for judgment
    got = monty(["scan", "--candidates", "5"], repo)
    row["candidates"] = "; ".join(
        line.split()[1] for line in got.stdout.splitlines() if line.strip() and "x " in line
    ) or got.stdout.strip()[:80]

    # 4. the collision drill: a class name from the repo's own scan
    classish = Counter(d["name"] for d in surface["decls"]
                       if d["kind"] in ("class", "struct", "interface", "type", "module")
                       and d["name"][:1].isupper() and d["name"].isalpha())
    if classish:
        victim = classish.most_common(1)[0][0]
        monty(["onto", "add", victim.lower(), "a word meaning something else entirely",
               "--kind", "core"], repo)
        toml0 = repo / ".monty" / "montology.toml"
        toml0.write_text(toml0.read_text().replace(
            'enforced_kinds = ["core", "inner"]',
            'enforced_kinds = ["core", "inner"]\ncollisions = "enforce"'))
        lint1 = monty(["lint"], repo)
        hit_file = next((d["file"] for d in surface["decls"] if d["name"] == victim), "")
        fired = lint1.returncode == 1 and victim in lint1.stdout and hit_file in lint1.stdout
        toml = repo / ".monty" / "montology.toml"
        toml.write_text(toml.read_text().replace("allow = []", f'allow = ["{victim.lower()}"]'))
        lint2 = monty(["lint"], repo)
        row["collision"] = (f"ok ({victim} → FAIL@{hit_file.split('/')[-1]} → allow → green)"
                            if fired and lint2.returncode == 0
                            else f"FAIL (fired={fired}, after_allow={lint2.returncode})")
    else:
        row["collision"] = "skipped (no class-like decls)"

    # 5. vitals: the verdict must compose on every real repo, and the JSON
    #    must honor the dashboard contract (state consistent with verdict)
    got = monty(["vitals", "--json"], repo)
    try:
        v = json.loads(got.stdout)
        consistent = v["state"] in ("tended", "drifting", "untended") \
            and v["verdict"].lower().startswith(v["state"]) \
            and (v["state"] == "tended") == (not v["reasons"])
        row["vitals"] = (v["state"] if consistent
                         else f"FAIL: inconsistent ({v['state']} vs {v['verdict'][:30]})")
    except Exception as e:  # noqa: BLE001
        row["vitals"] = f"FAIL: {type(e).__name__} {got.stderr.strip()[-80:]}"

    # 6. migrate round-trip: lossless or it does not ship
    once = [n for n, c in Counter(d["name"] for d in surface["decls"]).items()
            if c >= 1 and n[:1].isupper() and n.isalpha() and len(n) > 4]
    if once:
        victim = once[0]
        monty(["migrate", victim, victim + "Zq", "--apply"], repo)
        changed = run(["git", "diff", "--stat"], repo).stdout.strip()
        monty(["migrate", victim + "Zq", victim, "--apply"], repo)
        clean = run(["git", "diff", "--numstat", "--", ".", ":!CLAUDE.md", ":!.mcp.json"],
                    repo).stdout.strip() == ""
        row["migrate"] = ("ok (round-trip clean, "
                          f"{changed.splitlines()[-1].strip() if changed else 'no-op'})"
                          if clean else "FAIL: round-trip left a diff")
        run(["git", "checkout", "--", "."], repo)
    else:
        row["migrate"] = "skipped"
    return row


def main() -> None:
    keep = "--keep" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    workdir = Path(args[0]) if args else Path("/tmp/montology-stress")
    workdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, url, ref in REPOS:
        print(f"── {name} ({ref})")
        repo = prepare(workdir, name, url, ref)
        if repo is None:
            rows.append({"repo": name, "init": "clone failed"})
            continue
        try:
            row = stress_one(repo)
        except Exception as e:  # noqa: BLE001 — one repo's crash is a row, not an abort
            row = {"repo": name, "init": f"CRASH {type(e).__name__}: {e}"}
        rows.append(row)
        print("   " + json.dumps(row, default=str))
        if not keep:
            pass  # clones cached for re-runs; pass --keep is a no-op kept for symmetry

    cols = ["repo", "init", "files", "decls", "errors", "skipped", "scan_s",
            "collision", "vitals", "migrate", "candidates"]
    lines = ["# Stress battery — " + time.strftime("%Y-%m-%d"), "",
             "| " + " | ".join(cols) + " |",
             "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(c, "—")) for c in cols) + " |")
    report = "\n".join(lines) + "\n"
    (MONTY_ROOT / "stress" / "REPORT.md").write_text(report)
    print("\n" + report)
    bad = [r for r in rows if any("FAIL" in str(v) or "CRASH" in str(v) for v in r.values())]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
