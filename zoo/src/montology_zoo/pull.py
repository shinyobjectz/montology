"""Download a model's weights — the artifact the database points at.

The db row says which repo and file; `zoo sync` has already verified the
pointer resolves and measured its size. Weights land under zoo/models/<id>/
(gitignored) via huggingface_hub, which dedupes and resumes.
"""

from __future__ import annotations

from pathlib import Path

from .db import DB_PATH, connect

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"


def pull(model_id: str) -> str:
    if not DB_PATH.exists():
        return "The zoo database is empty. Repair: run `monty zoo sync` first."
    conn = connect()
    arts = conn.execute(
        "SELECT * FROM artifact WHERE model_id=? ORDER BY bytes ASC", (model_id,)
    ).fetchall()
    if not arts:
        known = [r["id"] for r in conn.execute("SELECT id FROM model ORDER BY id")]
        return f"no model named {model_id!r}. Registered: {', '.join(known)}"

    from huggingface_hub import hf_hub_download

    got: list[str] = []
    best = arts[0]
    target = MODELS_DIR / model_id
    # the artifact itself, plus the sidecar files ONNX needs to tokenize
    files = [best["path"]]
    if best["format"] == "onnx":
        files += ["tokenizer.json", "tokenizer_config.json", "config.json",
                  "special_tokens_map.json", "preprocessor_config.json", "vocab.txt"]
    for f in files:
        try:
            hf_hub_download(best["repo"], f, local_dir=str(target))
            got.append(f)
        except Exception:  # noqa: BLE001 — sidecars are model-dependent; the artifact is not
            if f == best["path"]:
                return (
                    f"{model_id}: could not fetch {best['repo']}/{f}. "
                    f"Run `monty zoo sync` — if sync reports MISS, the pointer needs fixing."
                )
    size = (best["bytes"] or 0) / 1e6
    return f"{model_id}: {best['format']}/{best['quant']} ({size:.0f} MB) + {len(got) - 1} sidecars → {target}"
