"""The zoo's own database: models, artifacts, and measured facts.

SEPARATE FROM ontology.db on purpose — the ontology is vocabulary, this is
inventory. Three tables:

  * ``model`` — one row per curated model: what it is, what it may claim
    (role), and its license.
  * ``artifact`` — one row per (model, format, quant): WHERE the weights
    live and, after ``zoo sync``, how many bytes they actually are. Sizes
    are FETCHED from the HuggingFace API and recorded with a sync
    timestamp — never typed in by hand, because a typed size is a guess
    wearing a number's clothes.
  * ``arch`` — per-model architecture facts sync reads from config.json
    (layers, KV heads, head dim, hidden size, context). The KV-cache math
    needs these, and they too are fetched, not transcribed.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "zoo.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS model (
  id        TEXT PRIMARY KEY,      -- zoo id, e.g. 'text-bge-m3'
  repo      TEXT NOT NULL,         -- canonical HF repo (the model's identity)
  task      TEXT NOT NULL,         -- embed | rerank | classify | embed-image | embed-audio | generate
  modality  TEXT NOT NULL,         -- text | image-text | audio | text-gen
  dims      INTEGER,               -- embedding dims (NULL for non-embedders)
  license   TEXT,
  role      TEXT NOT NULL,         -- retrieval | text-query-only | scoring | drafting | transcribe
  status    TEXT NOT NULL,         -- carried | evaluate | skip  (the curation ruling)
  note      TEXT NOT NULL          -- for evaluate/skip, the note IS the ruling's why
);

CREATE TABLE IF NOT EXISTS artifact (
  model_id  TEXT NOT NULL REFERENCES model(id),
  format    TEXT NOT NULL,         -- onnx | gguf
  quant     TEXT NOT NULL,         -- fp32 | q8 | q4_k_m | ...
  repo      TEXT NOT NULL,         -- HF repo holding THIS artifact
  path      TEXT NOT NULL,         -- file (gguf) or file-with-dir (onnx) inside the repo
  bytes     INTEGER,               -- measured by `zoo sync`; NULL = not yet synced
  synced_at TEXT,                  -- ISO timestamp of the measurement
  PRIMARY KEY (model_id, format, quant)
);

CREATE TABLE IF NOT EXISTS arch (
  model_id      TEXT PRIMARY KEY REFERENCES model(id),
  params_m      INTEGER,           -- millions of parameters (from safetensors index / config)
  n_layers      INTEGER,
  n_kv_heads    INTEGER,
  head_dim      INTEGER,
  hidden        INTEGER,
  max_ctx       INTEGER,
  synced_at     TEXT
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(target)
    c.executescript(SCHEMA)
    c.row_factory = sqlite3.Row
    return c
