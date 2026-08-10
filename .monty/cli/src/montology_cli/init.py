"""`monty init` — the onboarding: scaffold, install, and a first project.

The flow, decided deliberately:

  1. a two-second doctor pass (what is present, what is missing);
  2. interactive only: OFFER the official installer for a missing binary,
     one keystroke, never silently — the agent path never installs system
     software, it reports ``{missing, repair}`` and degrades;
  3. every install that can start STARTS, in the background — the gemma
     weights are coming down while the questions are being answered;
  4. four prompts, under a minute: workspace name, vendor keys now or
     later, which agent harnesses to wire (claude/cursor/codex, detected
     ones as the default), an optional first brand to crawl;
  5. one progress screen for whatever is still running;
  6. the finale: crawl + scaffold the brand, so init ends with a real
     project — which is also the end-to-end smoke test.

Non-interactive (``--yes``, or no TTY): no prompts ever, secrets from the
environment only, plain state lines instead of bars, ``--json`` for the
machine summary. Idempotent throughout: a re-run repairs what is missing
and no-ops the rest.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

import typer

from ._scaffold import materialize, wire_agents

OLLAMA_URL = "http://localhost:11434"
TINY_MODEL = "gemma3:270m"

REPAIRS = {
    "ollama": "brew install ollama && brew services start ollama  (ollama.com)",
    "node": "brew install node  (nodejs.org)",
    "ffmpeg": "brew install ffmpeg",
    "just": "brew install just  (the action surface: `just` shows what is live)",
}


# ── detection ────────────────────────────────────────────────────────────

def _ollama_serving() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2)
        return True
    except Exception:  # noqa: BLE001
        return False


def _gemma_present() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2) as r:
            tags = json.load(r)
        return any(m.get("name", "").startswith(TINY_MODEL) for m in tags.get("models", []))
    except Exception:  # noqa: BLE001
        return False


def _toolchain() -> dict[str, bool]:
    return {name: shutil.which(name) is not None
            for name in ("ollama", "node", "npm", "ffmpeg", "just", "git")}


AGENT_HARNESSES = ("claude", "cursor", "codex")


def _detect_agents() -> list[str]:
    """Which harnesses live on this machine — the prompt's default."""
    found = []
    if shutil.which("claude"):
        found.append("claude")
    if shutil.which("cursor") or Path("/Applications/Cursor.app").exists():
        found.append("cursor")
    if shutil.which("codex"):
        found.append("codex")
    return found


# ── background jobs ──────────────────────────────────────────────────────

class Job(threading.Thread):
    """One install, observable: state, a byte counter when the source
    streams one, and the outcome. The progress screen reads these."""

    def __init__(self, key: str, label: str):
        super().__init__(daemon=True)
        self.key, self.label = key, label
        self.state = "running"          # running | done | skipped | failed
        self.detail = ""
        self.total = self.completed = 0

    def finish(self, state: str, detail: str = "") -> None:
        self.state, self.detail = state, detail


class GemmaPull(Job):
    def run(self) -> None:
        if _gemma_present():
            return self.finish("done", "already present")
        if not _ollama_serving():
            return self.finish("skipped", "ollama not serving")
        try:
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/pull",
                data=json.dumps({"name": TINY_MODEL}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=1800) as r:
                for line in r:
                    part = json.loads(line)
                    if part.get("total"):
                        self.total = part["total"]
                        self.completed = part.get("completed", 0)
                    if part.get("error"):
                        return self.finish("failed", part["error"])
            self.finish("done", "pulled")
        except Exception as e:  # noqa: BLE001
            self.finish("failed", f"{type(e).__name__}: {e}")


class Subprocess(Job):
    def __init__(self, key: str, label: str, cmd: list[str], cwd: Path | None = None,
                 timeout: int = 1800):
        super().__init__(key, label)
        self.cmd, self.cwd, self.timeout = cmd, cwd, timeout

    def run(self) -> None:
        try:
            p = subprocess.run(self.cmd, cwd=self.cwd, capture_output=True,
                               text=True, timeout=self.timeout)
            if p.returncode == 0:
                self.finish("done")
            else:
                self.finish("failed", (p.stderr or p.stdout).strip()[-200:])
        except Exception as e:  # noqa: BLE001
            self.finish("failed", f"{type(e).__name__}: {e}")


# ── the flows ────────────────────────────────────────────────────────────

def _offer_installs(tools: dict[str, bool], interactive: bool, echo) -> dict[str, bool]:
    """Interactive: one [Y/n] per missing binary that matters, running the
    official installer on yes. Never in agent mode — doctrine holds."""
    brew = shutil.which("brew") is not None
    for name, why in (("ollama", "the 292 MB local model (one-line drafting) needs it"),
                      ("node", "the design render harness (banners, emails) needs it")):
        if tools.get(name) or not interactive or not brew:
            continue
        if typer.confirm(f"  {name} is missing — {why}. Install via brew now?", default=True):
            echo(f"  installing {name}…")
            subprocess.run(["brew", "install", name], check=False)
            if name == "ollama":
                subprocess.run(["brew", "services", "start", "ollama"], check=False)
            tools[name] = shutil.which(name) is not None
    if tools.get("ollama") and not _ollama_serving() and interactive:
        if typer.confirm("  ollama is installed but not serving — start it now?", default=True):
            subprocess.run(["brew", "services", "start", "ollama"], check=False)
    return tools


def _start_jobs(ws: Path, tools: dict[str, bool]) -> list[Job]:
    jobs: list[Job] = [GemmaPull("gemma", f"{TINY_MODEL} (292 MB, the atomic tier)")]
    jobs.append(Subprocess("chromium", "Chromium (crawling + rendering)",
                           [sys.executable, "-m", "playwright", "install", "chromium"]))
    if tools.get("npm"):
        jobs.append(Subprocess("design", "render harness deps (react, esbuild)",
                               ["npm", "install", "--no-fund", "--no-audit"],
                               cwd=ws / ".monty" / "design"))
    for j in jobs:
        j.start()
    return jobs


def _watch_plain(jobs: list[Job], echo) -> None:
    import time
    pending = list(jobs)
    while pending:
        for j in [j for j in pending if j.state != "running"]:
            echo(f"  {j.label}: {j.state}" + (f" ({j.detail})" if j.detail else ""))
            pending.remove(j)
        time.sleep(0.5)


def _watch_rich(jobs: list[Job]) -> None:
    from rich.progress import (BarColumn, DownloadColumn, Progress, SpinnerColumn,
                               TextColumn)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), DownloadColumn()) as progress:
        tasks = {j.key: progress.add_task(j.label, total=None) for j in jobs}
        import time
        while any(j.state == "running" for j in jobs):
            for j in jobs:
                kwargs: dict = {}
                if j.total:
                    kwargs = {"total": j.total, "completed": j.completed}
                if j.state != "running":
                    kwargs["completed"] = kwargs.get("total") or 1
                    kwargs.setdefault("total", 1)
                progress.update(tasks[j.key], **kwargs)
            time.sleep(0.2)
        for j in jobs:
            progress.update(tasks[j.key], total=j.total or 1, completed=j.total or 1)


def _masked_prompt(label: str) -> str:
    """A secret with feedback: echoes one bullet per keystroke instead of
    the unnerving nothing of hide_input. POSIX TTYs only; anywhere else
    falls back to the blank-hidden prompt."""
    if not sys.stdin.isatty():
        return typer.prompt(label, hide_input=True)
    try:
        import termios
        import tty
    except ImportError:
        return typer.prompt(label, hide_input=True)
    sys.stdout.write(f"{label}: ")
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old_attrs = termios.tcgetattr(fd)
    chars: list[str] = []
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch in ("\r", "\n"):
                break
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch in ("\x7f", "\x08"):
                if chars:
                    chars.pop()
                    sys.stdout.write("\b \b")
            elif ch.isprintable():
                chars.append(ch)
                sys.stdout.write("•")
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)
        sys.stdout.write("\n")
        sys.stdout.flush()
    return "".join(chars)


def _prompts(default_name: str, echo) -> tuple[str, dict[str, str], str]:
    """The onboarding questions. Under a minute, on purpose."""
    name = typer.prompt("Workspace name", default=default_name)

    keys: dict[str, str] = {}
    echo("\nVendor keys unlock live data (both optional — skills say what needs what).")
    if typer.confirm("  Add DataForSEO credentials now?", default=False):
        keys["DATAFORSEO_LOGIN"] = typer.prompt("    DATAFORSEO_LOGIN")
        keys["DATAFORSEO_PASSWORD"] = _masked_prompt("    DATAFORSEO_PASSWORD")
    if typer.confirm("  Add a ScrapeCreators key now?", default=False):
        keys["SCRAPECREATORS_API_KEY"] = _masked_prompt("    SCRAPECREATORS_API_KEY")

    detected = _detect_agents()
    default_agents = ",".join(detected) if detected else ",".join(AGENT_HARNESSES)
    raw = typer.prompt(
        f"\nWire this workspace for which agent harnesses? ({', '.join(AGENT_HARNESSES)})",
        default=default_agents,
    )
    agents = tuple(a.strip() for a in raw.split(",") if a.strip() in AGENT_HARNESSES)

    brand = typer.prompt(
        "\nFirst brand to crawl (a URL — builds your first project; Enter to skip)",
        default="", show_default=False,
    ).strip()
    return name, keys, brand, agents or tuple(AGENT_HARNESSES)


def _write_env(ws: Path, keys: dict[str, str]) -> bool:
    """Secrets land in .env (gitignored), merged over what is there."""
    keys = {k: v for k, v in keys.items() if v}
    if not keys:
        return False
    env_file = ws / ".env"
    existing: dict[str, str] = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    existing.update(keys)
    env_file.write_text("".join(f"{k}={v}\n" for k, v in existing.items()))
    env_file.chmod(0o600)
    return True


def _demo(ws: Path, url: str, echo) -> str | None:
    """The finale: audit → scaffold (captured registry) → logo → a real
    render. Init ends with React on disk AND pixels of it."""
    import json as _json

    from montology_crawl.audit import brand_audit
    from montology_crawl.brand import scaffold
    from montology_crawl.logos import logo_fetch
    from montology_crawl.render import render as brand_render

    slug = url.split("//")[-1].split("/")[0].removeprefix("www.").split(".")[0]
    echo(f"\n▸ crawling {url} (up to 4 pages) — this is the whole pipeline once…")
    audit = brand_audit(url if "://" in url else f"https://{url}")
    if not audit.strip().startswith("{"):
        echo(f"  crawl did not produce an audit: {audit[:200]}")
        return None
    echo(scaffold(slug, audit))
    echo("  " + logo_fetch(slug, slug).splitlines()[0])

    mf = ws / "brands" / slug / "manifest.json"
    comps = _json.loads(mf.read_text()).get("components", []) if mf.exists() else []
    if comps:
        ws_brand = ws / "brands" / slug
        pick = max(comps, key=lambda c: (ws_brand / c["file"]).stat().st_size
                   if (ws_brand / c["file"]).exists() else 0)
        echo(f"▸ rendering the richest captured component ({pick['name']})…")
        for line in brand_render(slug, pick["file"]).splitlines():
            echo(f"  {line}")
    echo(f"  the book: brands/{slug}/ — fill it fully with `monty brand index {slug}`")
    return f"brands/{slug}"


def init_command(path: str = ".", name: str = "", brand: str = "",
                 yes: bool = False, as_json: bool = False,
                 no_install: bool = False, agents: str = "") -> None:
    ws = Path(path).expanduser().resolve()
    interactive = sys.stdin.isatty() and sys.stdout.isatty() and not yes
    echo = (lambda *_: None) if as_json else typer.echo

    summary: dict = {"workspace": None, "created": [], "installed": {},
                     "missing": [], "demo": None, "ok": True}

    echo("▸ checking the toolchain…")
    tools = _toolchain()
    tools = _offer_installs(tools, interactive, echo)
    for t, present in tools.items():
        if not present and t in REPAIRS:
            summary["missing"].append({"bin": t, "repair": REPAIRS[t]})
    present = ", ".join(t for t, ok in tools.items() if ok) or "nothing"
    echo(f"  present: {present}")

    # scaffold before jobs — npm install needs design/ on disk
    ws_name = name or ws.name
    result = materialize(ws, ws_name)
    summary["created"] = result["made"]
    if tools.get("git") and not (ws / ".git").exists() \
            and not any((p / ".git").exists() for p in ws.parents):
        subprocess.run(["git", "init", "-q"], cwd=ws, check=False)
        summary["created"].append(".git")

    jobs: list[Job] = []
    if not no_install:
        echo("▸ starting downloads in the background…")
        jobs = _start_jobs(ws, tools)

    if interactive:
        ws_name2, keys, brand_answer, chosen = _prompts(ws_name, echo)
        if ws_name2 != ws_name:
            meta = ws / ".monty" / "workspace.toml"
            meta.write_text(meta.read_text().replace(f'name = "{ws_name}"',
                                                     f'name = "{ws_name2}"'))
            ws_name = ws_name2
        brand = brand or brand_answer
    else:
        keys = {k: os.environ[k] for k in
                ("DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD", "SCRAPECREATORS_API_KEY")
                if os.environ.get(k)}
        wanted = [a.strip() for a in agents.split(",") if a.strip()]
        chosen = tuple(a for a in wanted if a in AGENT_HARNESSES) \
            or tuple(_detect_agents()) or AGENT_HARNESSES
    wired = wire_agents(ws, ws_name, chosen)
    summary["created"].extend(wired["made"])
    summary["agents"] = list(chosen)
    for note in wired["notes"]:
        summary.setdefault("notes", []).append(note)
        echo(f"  {note}")
    if _write_env(ws, keys):
        summary["created"].append(".env")

    if jobs:
        echo("\n▸ finishing installs")
        (_watch_rich if interactive else _watch_plain)(jobs, *(() if interactive else (echo,)))
        for j in jobs:
            summary["installed"][j.key] = j.state + (f": {j.detail}" if j.detail else "")
            if j.state == "failed":
                echo(f"  {j.label} FAILED: {j.detail}")
    if not tools.get("ollama") or not _ollama_serving():
        summary.setdefault("degraded", []).append(
            "gen tiny tier (gemma) dormant until ollama serves")

    if brand:
        os.chdir(ws)  # the demo resolves everything through the workspace
        try:
            summary["demo"] = _demo(ws, brand, echo)
        except Exception as e:  # noqa: BLE001
            echo(f"  demo did not finish ({type(e).__name__}: {e}) — the workspace is fine; "
                 f"retry with: monty crawl audit {brand}")

    summary["workspace"] = str(ws)
    if as_json:
        typer.echo(json.dumps(summary, indent=2))
    else:
        echo("\n✔ workspace ready.")
        echo("  next: cd into it and run `just` (the action surface), or open your agent —")
        echo("  .mcp.json and .claude/skills are already wired for Claude Code.")
        if summary["missing"]:
            echo("  missing (each with its repair):")
            for m in summary["missing"]:
                echo(f"    {m['bin']}: {m['repair']}")
