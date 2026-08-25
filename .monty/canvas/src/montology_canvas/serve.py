"""`monty canvas`: the graph, served on localhost.

The intake package is the precedent and this follows it — a stdlib HTTP server
bound to the loopback on an ephemeral port, the browser opened for you, nothing
leaving the machine. What differs is the lifetime: intake serves one form and
exits on the answer, while the canvas is a place you stay, so it runs until
interrupted.

The page is a BUILT asset committed into this package (see `stamp`), because
`monty canvas` has to work from a uvx install on a machine with no Node.
"""

from __future__ import annotations

import json
import mimetypes
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STATIC = Path(__file__).resolve().parent / "static"


def _handler(state: dict):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):  # the server's own chatter is not the point
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            # A canvas that can be framed or fetched cross-origin is a canvas
            # that can be read by a page you did not open. It is localhost, but
            # localhost is not a permission.
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, payload) -> None:
            self._send(code, json.dumps(payload).encode(), "application/json")

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path in ("/api/graph", "/api/graph/"):
                from .graph import graph
                from .intents import catalogue

                try:
                    payload = graph(with_scan=state["with_scan"])
                    # The token rides here and nowhere else. A cross-origin page
                    # can POST to loopback, but it cannot READ this response —
                    # no CORS headers are sent — so it never learns the token.
                    # That is the whole CSRF story, and it needs no cookie.
                    payload["token"] = state["token"]
                    payload["intents"] = catalogue()
                    self._json(200, payload)
                except Exception as e:  # noqa: BLE001 — the page must say why
                    self._json(500, {"error": f"{type(e).__name__}: {e}"})
                return
            if path in ("/api/check", "/api/check/"):
                from urllib.parse import parse_qs, urlparse

                from montology_ontology import check

                name = (parse_qs(urlparse(self.path).query).get("name") or [""])[0]
                if not name.strip():
                    self._json(200, {"name": name, "findings": []})
                    return
                self._json(200, {"name": name, "findings": check(name)})
                return
            self._static(path)

        def do_POST(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path not in ("/api/intent", "/api/intent/"):
                self._json(404, {"error": f"no {path!r}"})
                return
            if self.headers.get("X-Monty-Token") != state["token"]:
                self._json(403, {"error": "this request did not come from the canvas"})
                return
            if "json" not in (self.headers.get("Content-Type") or ""):
                self._json(415, {"error": "intents are JSON"})
                return
            try:
                size = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(size) or b"{}")
            except (ValueError, OSError) as e:
                self._json(400, {"error": f"unreadable intent: {e}"})
                return

            from .intents import apply

            # The engine's own answer, verbatim — including its refusal text.
            # Errors are data with the repair attached; re-wording one here
            # would be a second gate, and it would drift from the first.
            self._json(200, apply(str(body.get("intent", "")), body.get("fields") or {}))

        def _static(self, path: str) -> None:
            rel = "index.html" if path in ("/", "") else path.lstrip("/")
            target = (STATIC / rel).resolve()
            # the bundle is the only thing this server may hand out
            if not str(target).startswith(str(STATIC.resolve())) or not target.is_file():
                self._json(404, {"error": f"no {rel!r} in the bundle"})
                return
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self._send(200, target.read_bytes(), ctype)

    return Handler


def serve(*, open_browser: bool = True, port: int = 0, with_scan: bool = True,
          _ready=None) -> str:
    """Serve the canvas until interrupted. Returns the reason it stopped."""
    import webbrowser

    if not (STATIC / "index.html").exists():
        return ("the canvas bundle is not in this install. Repair: build it — "
                "`just canvas` in the montology repo, or reinstall a release "
                "that ships it.")

    httpd = ThreadingHTTPServer(
        ("127.0.0.1", port),
        _handler({"with_scan": with_scan, "token": secrets.token_urlsafe(24)}))
    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    if _ready:
        _ready(url)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return f"canvas closed ({url})"
    finally:
        httpd.server_close()
    return f"canvas closed ({url})"
