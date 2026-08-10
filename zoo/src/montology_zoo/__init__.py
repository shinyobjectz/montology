"""montology-zoo: local embeddings for marketing text and creative.

THE REGISTRY IS A PERMISSIONS TABLE, NOT METADATA. Each model declares its
role — what question it may answer. A model that cannot tell two captions
apart must not be allowed to claim two captions are alike. (A lesson
imported from production: role gates are invariants, not config.)

Weights are DOWNLOADED, never bundled: `montology zoo pull <id>` fetches
from HuggingFace onto the user's disk under zoo/models/.
"""

from .registry import MODELS, EmbeddingModel, get

__all__ = ["MODELS", "EmbeddingModel", "get"]
