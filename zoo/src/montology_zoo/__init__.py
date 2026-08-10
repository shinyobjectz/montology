"""montology-zoo: small models for marketing work, run on YOUR laptop.

THE DATABASE IS THE REGISTRY (zoo/data/zoo.db) — models and artifacts as
rows, sizes and architecture as MEASURED facts fetched by `zoo sync` from
the HuggingFace API, never typed by hand. `zoo fit` does the peak-RAM math
against this machine, with its estimate constants named and justified in
fit.py.

ROLE IS A PERMISSIONS TABLE, NOT METADATA. A model that cannot tell two
captions apart must not be allowed to claim two captions are alike —
`text-query-only` rows may answer a typed query and nothing more.

ONNX-first: encoders run through onnxruntime (prebuilt wheels, every OS).
The GGUF shelf (tiny generative) is served by an installed Ollama or
llama.cpp — montology never compiles C++ on a marketer's laptop.
"""

from .db import DB_PATH, connect
from .fit import machine, report as fit_report
from .pull import pull
from .seed import seed
from .sync import sync

__all__ = ["DB_PATH", "connect", "fit_report", "machine", "pull", "seed", "sync"]
