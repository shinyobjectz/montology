"""`ask`: serve one phase, block until it is answered, write the answers.

A stdlib HTTP server bound to localhost on an ephemeral port serves the
form and accepts exactly one POST. The call returns when that POST lands
(or the deadline passes) — so the PROCESS EXIT is the signal an agent
waits on. Run `monty intake ask …` in the background and the exit is the
notification; or watch for `<phase>.answers.json` to appear. Both work,
because the answers file is the contract, not the process.
"""

from __future__ import annotations

import json
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from montology_core import WorkspaceError

from .spec import intake_dir, load_spec, render_form, validate_spec, workspace_name


def ask(source: str, *, open_browser: bool = True, timeout: float = 0,
        port: int = 0, _ready=None) -> str:
    """Serve the phase in `source` (JSON text, path, or '-') for this workspace;
    block until submitted; write .monty/answers/<phase>.answers.json.

    Returns one line: 'answered  <path> (N answers)' or the failure with its
    repair. `_ready` is a callback given the URL once the server is up
    (tests use it; the CLI prints the URL)."""
    try:
        spec = load_spec(source)
    except (ValueError, OSError) as e:
        return f"could not read the phase spec: {e}. It is JSON: {{phase, title, intro, questions:[...]}}"
    problems = validate_spec(spec)
    if problems:
        return "REFUSED — the phase spec has problems:\n  " + "\n  ".join(problems)
    try:
        folder = intake_dir()
        project = workspace_name()
    except WorkspaceError as e:
        return str(e)
    folder.mkdir(parents=True, exist_ok=True)
    phase = spec["phase"]
    (folder / f"{phase}.json").write_text(json.dumps(spec, indent=2))
    page = render_form(spec, project).encode()

    got: dict = {}
    done = threading.Event()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *_):  # quiet — stdout is the agent's channel
            pass

        def _send(self, code: int, body: bytes, ctype: str = "text/html; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.split("?")[0] in ("/", "/index.html"):
                self._send(200, page)
            elif self.path == "/spec.json":
                self._send(200, json.dumps(spec).encode(), "application/json")
            else:
                self._send(404, b"not here")

        def do_POST(self):
            if self.path != "/answers":
                return self._send(404, b"not here")
            n = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
                answers = body["answers"]
                assert isinstance(answers, dict)
            except (ValueError, KeyError, AssertionError):
                return self._send(400, b"expected {answers: {...}}")
            got.update(answers)
            self._send(200, b'{"ok":true}', "application/json")
            done.set()

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    srv.daemon_threads = True
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    (folder / f"{phase}.html").write_text(page.decode())
    t = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True)
    t.start()
    if _ready:
        _ready(url)
    else:
        print(f"serving  {url}  ({phase}: {len(spec['questions'])} questions) — waiting for the submit", flush=True)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 — headless is fine; the URL was printed
            pass
    deadline = time.monotonic() + timeout if timeout else None
    try:
        while not done.is_set():
            if deadline and time.monotonic() > deadline:
                return (f"timed out after {timeout:.0f}s with no submit; the form is still at "
                        f"{folder / (phase + '.html')} — rerun `monty intake ask "
                        f"{folder / (phase + '.json')}` when they are ready")
            done.wait(0.25)
    finally:
        srv.shutdown()
        srv.server_close()
    record = {
        "workspace": project,
        "phase": phase,
        "title": spec["title"],
        "answered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "questions": [{"id": q["id"], "label": q["label"], "type": q.get("type", "text")}
                      for q in spec["questions"]],
        "answers": got,
    }
    out = folder / f"{phase}.answers.json"
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False))
    return f"answered  {out} ({len(got)} answers)"


def main() -> None:  # python -m montology_intake.serve <project> <spec>
    print(ask(sys.argv[1]))
