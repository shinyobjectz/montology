"""The generation backend, resolved once, with its repair attached.

Resolution order:
  1. MONTOLOGY_MODEL_URL (+ MONTOLOGY_MODEL, MONTOLOGY_MODEL_KEY) — any
     OpenAI-compatible endpoint (a vLLM box, a gateway, the zoo's shelf
     served by whatever the user runs).
  2. Local Ollama at the default port — Mellea's own default lane; the
     default model is Mellea's default (Granite), and the zoo's carried
     GGUF shelf works the same way.

No shared session state: a fresh session per generation run, SimpleContext
— the socialite rule (a module-level session corrupts under concurrency)
carried over before it can bite.
"""

from __future__ import annotations

import os
import urllib.request

NO_BACKEND = (
    "No model backend is reachable for generation. Repair, either one:\n"
    "  - install Ollama (ollama.com), run `ollama pull granite4.1:3b`, retry; or\n"
    "  - set MONTOLOGY_MODEL_URL to any OpenAI-compatible endpoint "
    "(and MONTOLOGY_MODEL / MONTOLOGY_MODEL_KEY as needed).\n"
    "Deterministic commands (gen lint) never need a model."
)

OLLAMA_URL = "http://localhost:11434"


def gen_session():
    """A fresh MelleaSession, or a string carrying the repair."""
    from mellea import MelleaSession
    from mellea.stdlib.context import SimpleContext

    url = os.environ.get("MONTOLOGY_MODEL_URL", "").rstrip("/")
    if url:
        from mellea.backends.openai import OpenAIBackend

        return MelleaSession(
            OpenAIBackend(
                model_id=os.environ.get("MONTOLOGY_MODEL", "default"),
                base_url=url,
                api_key=os.environ.get("MONTOLOGY_MODEL_KEY", "EMPTY"),
            ),
            ctx=SimpleContext(),
        )

    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
    except Exception:  # noqa: BLE001 — unreachable backend answers with the repair
        return NO_BACKEND

    from mellea import start_session

    return start_session("ollama", model_id=os.environ.get("MONTOLOGY_MODEL", "granite4.1:3b"))
