"""The zoo's registry: which models exist, how they run, what they may claim.

A starter selection biased to marketing work: multilingual text for captions
and briefs, an image-text pair for creative, audio for sound trends. Grow it
by decision — every entry is a download users pay for in disk and time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class EmbeddingModel:
    id: str                                   # zoo id, e.g. "text-bge-m3"
    repo: str                                 # HuggingFace repo
    backend: Literal["onnx", "gguf"]
    dims: int
    modality: Literal["text", "image-text", "audio"]
    role: Literal["retrieval", "text-query-only"]
    note: str


MODELS: tuple[EmbeddingModel, ...] = (
    EmbeddingModel(
        "text-bge-m3", "BAAI/bge-m3", "onnx", 1024, "text", "retrieval",
        "The workhorse: multilingual, long-context, dense retrieval for captions, briefs, SERPs.",
    ),
    EmbeddingModel(
        "text-minilm", "sentence-transformers/all-MiniLM-L6-v2", "onnx", 384, "text", "retrieval",
        "The small fast one: dedup, clustering, anything where 384 dims is plenty.",
    ),
    EmbeddingModel(
        "visual-siglip2", "google/siglip2-base-patch16-224", "onnx", 768, "image-text",
        "text-query-only",
        "Find creative by describing it. TEXT-QUERY ONLY: it may answer a typed query; "
        "it may NOT assert two images are alike — measured, not guessed.",
    ),
    EmbeddingModel(
        "audio-clap", "laion/clap-htsat-fused", "onnx", 512, "audio", "retrieval",
        "Sound and music similarity — trend-tracking for audio-led platforms.",
    ),
)


def get(model_id: str) -> EmbeddingModel | None:
    return next((m for m in MODELS if m.id == model_id), None)
