"""Download a registered model's weights from HuggingFace.

Weights land under zoo/models/<id>/ (gitignored). ONNX exports are preferred
when the repo ships them; a repo without an ONNX export is reported with the
repair (export it, or pick a model that ships one) rather than silently
falling back to a 2GB PyTorch download.
"""

from __future__ import annotations

from pathlib import Path

from .registry import MODELS, get

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"


def pull(model_id: str) -> str:
    model = get(model_id)
    if model is None:
        known = ", ".join(m.id for m in MODELS)
        return f"no model named {model_id!r}. Registered: {known}"

    from huggingface_hub import snapshot_download

    patterns = {
        "onnx": ["*.onnx", "onnx/**", "tokenizer*", "*.json", "vocab*", "merges.txt"],
        "gguf": ["*.gguf", "*.json"],
    }[model.backend]

    target = MODELS_DIR / model.id
    path = snapshot_download(model.repo, allow_patterns=patterns, local_dir=str(target))
    got = list(Path(path).rglob(f"*.{model.backend.replace('gguf', 'gguf')}"))
    if model.backend == "onnx" and not list(Path(path).rglob("*.onnx")):
        return (
            f"{model.id}: {model.repo} ships no ONNX export. Repair: export one "
            f"(optimum-cli export onnx --model {model.repo} …) or register a repo that ships it."
        )
    return f"{model.id}: {len(got) or 'files'} fetched to {target}"
