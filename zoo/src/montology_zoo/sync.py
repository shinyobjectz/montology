"""zoo sync: turn artifact pointers into measured facts.

For every artifact row, ask the HuggingFace API for the file's real size;
for every model, read config.json for the architecture numbers the fit math
needs. A pointer that does not resolve is reported with its repair — it
means seed.py names a file the repo does not ship, and the row must be
fixed, not papered over.

Nothing here is typed by hand: bytes come from the tree API, layer counts
from config.json, and both carry a synced_at timestamp.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from .db import connect

API = "https://huggingface.co/api/models"


def sync() -> list[str]:
    conn = connect()
    now = datetime.now(UTC).isoformat()
    report: list[str] = []

    with httpx.Client(timeout=60, follow_redirects=True) as http:
        # ── artifact sizes, from the repo file tree ─────────────────────────
        trees: dict[str, dict[str, int]] = {}
        carried = conn.execute(
            "SELECT a.* FROM artifact a JOIN model m ON m.id = a.model_id "
            "WHERE m.status = 'carried'"
        ).fetchall()
        for a in carried:
            if a["repo"] not in trees:
                trees[a["repo"]] = _tree_sizes(http, a["repo"], report)
            sizes = trees[a["repo"]]
            got = sizes.get(a["path"])
            # ONNX external data: a graph-only .onnx with weights in a
            # sidecar. Counting only the graph would undercount peak RAM by
            # the entire model, so the sidecar's bytes join the artifact's.
            if got is not None:
                for sidecar in (a["path"] + "_data", a["path"] + ".data"):
                    got += sizes.get(sidecar, 0)
            if got is None:
                near = [p for p in sizes if p.endswith((".onnx", ".gguf"))][:6]
                report.append(
                    f"MISS {a['model_id']} {a['format']}/{a['quant']}: "
                    f"{a['repo']} has no file {a['path']!r}. Ships: {near}"
                )
                continue
            conn.execute(
                "UPDATE artifact SET bytes=?, synced_at=? "
                "WHERE model_id=? AND format=? AND quant=?",
                (got, now, a["model_id"], a["format"], a["quant"]),
            )
            report.append(f"ok   {a['model_id']} {a['format']}/{a['quant']}: {got / 1e6:.0f} MB")

        # ── architecture, from the canonical repo's config.json ─────────────
        for m in conn.execute(
            "SELECT id, repo, task FROM model WHERE status = 'carried'"
        ).fetchall():
            cfg = _config(http, m["repo"])
            if cfg is None:
                report.append(f"MISS {m['id']}: no readable config.json at {m['repo']}")
                continue
            conn.execute(
                "INSERT OR REPLACE INTO arch VALUES (?,?,?,?,?,?,?,?)",
                (m["id"], _params_m(trees, conn, m["id"]),
                 cfg.get("num_hidden_layers") or cfg.get("n_layer"),
                 cfg.get("num_key_value_heads") or cfg.get("num_attention_heads"),
                 _head_dim(cfg), cfg.get("hidden_size") or cfg.get("n_embd"),
                 cfg.get("max_position_embeddings") or cfg.get("n_ctx"), now),
            )

    conn.commit()
    return report


def _tree_sizes(http: httpx.Client, repo: str, report: list[str]) -> dict[str, int]:
    """Every file in a repo with its size, recursively (one call per dir level)."""
    sizes: dict[str, int] = {}

    def walk(path: str) -> None:
        url = f"{API}/{repo}/tree/main" + (f"/{path}" if path else "")
        r = http.get(url)
        if r.status_code != 200:
            report.append(f"MISS repo {repo}: API answered {r.status_code}")
            return
        for entry in r.json():
            if entry.get("type") == "directory":
                # only descend where artifacts live; a full walk of a big repo
                # is hundreds of calls for nothing
                if entry["path"].split("/")[-1] in ("onnx", "gguf"):
                    walk(entry["path"])
            else:
                sizes[entry["path"]] = int(entry.get("size", 0))

    walk("")
    return sizes


def _config(http: httpx.Client, repo: str) -> dict | None:
    r = http.get(f"https://huggingface.co/{repo}/raw/main/config.json")
    if r.status_code != 200:
        return None
    try:
        cfg = r.json()
    except ValueError:
        return None
    # multimodal configs nest the text tower; prefer it for the numbers we use
    return cfg.get("text_config", cfg)


def _head_dim(cfg: dict) -> int | None:
    if cfg.get("head_dim"):
        return cfg["head_dim"]
    hidden, heads = cfg.get("hidden_size"), cfg.get("num_attention_heads")
    return hidden // heads if hidden and heads else None


def _params_m(trees: dict, conn, model_id: str) -> int | None:
    """Parameter count estimated from the fp16/fp32 artifact size — a derived
    number, marked so by living next to measured bytes rather than replacing
    them. q8 ≈ 1 byte/param, fp16 ≈ 2, fp32 ≈ 4."""
    per_byte = {"fp32": 4.0, "fp16": 2.0, "q8": 1.0, "q8_0": 1.06, "q4_k_m": 0.56}
    row = conn.execute(
        "SELECT quant, bytes FROM artifact WHERE model_id=? AND bytes IS NOT NULL "
        "ORDER BY CASE quant WHEN 'fp32' THEN 0 WHEN 'fp16' THEN 1 ELSE 2 END LIMIT 1",
        (model_id,),
    ).fetchone()
    if row is None or row["quant"] not in per_byte:
        return None
    return int(row["bytes"] / per_byte[row["quant"]] / 1e6)
