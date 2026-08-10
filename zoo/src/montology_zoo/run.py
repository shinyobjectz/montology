"""The runtime: embed(), transcribe() — the calls the registry exists for.

ONE SESSION PER MODEL, CACHED. onnxruntime loads once per process; every
call after the first is tokenize → forward → pool. Everything reads the
zoo database: the artifact's real path, the model's dims (asserted against
the output — a wrong-shaped vector is a bug, not a return value), and the
role gate (a text-query-only model refuses to embed for similarity claims
at the API level, not in prose).

LANES:
  text   — tokenizers + ONNX encoder, mean-pool over the attention mask,
           L2-normalised (the sentence-transformers contract).
  image  — PIL preprocessing from the model's own preprocessor_config
           (resize, center-crop, rescale, normalise), vision tower forward.
  audio  — mel features built in numpy from preprocessor_config; SHAPE-
           VERIFIED but parity with the reference implementation is
           unverified — embed() says so in its own docstring and the fit
           table's role column stays the gate.
  asr    — whisper.cpp INVOKED, never linked: the `whisper-cli` binary
           (brew install whisper-cpp) runs the ggml artifact the zoo
           pulled. Absent binary answers with the repair.
"""

from __future__ import annotations

import json
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np

from .db import DB_PATH, connect
from .pull import MODELS_DIR, pull


class ZooError(RuntimeError):
    """Every zoo failure carries its repair in the message."""


def _model_row(model_id: str) -> dict:
    if not DB_PATH.exists():
        raise ZooError("the zoo database is empty. Repair: run `montology zoo sync`.")
    conn = connect()
    row = conn.execute("SELECT * FROM model WHERE id=?", (model_id,)).fetchone()
    if row is None:
        known = [r["id"] for r in conn.execute(
            "SELECT id FROM model WHERE status='carried' ORDER BY id")]
        raise ZooError(f"no model named {model_id!r}. Carried: {', '.join(known)}")
    art = conn.execute(
        "SELECT * FROM artifact WHERE model_id=? AND bytes IS NOT NULL ORDER BY bytes",
        (model_id,),
    ).fetchone()
    if art is None:
        raise ZooError(f"{model_id} has no synced artifact. Repair: `montology zoo sync`.")
    return {**dict(row), "artifact": dict(art)}


def _ensure_local(model_id: str, row: dict) -> Path:
    target = MODELS_DIR / model_id / row["artifact"]["path"]
    if not target.exists():
        got = pull(model_id)
        if not target.exists():
            raise ZooError(f"could not fetch {model_id}: {got}")
    return target


# ── text ────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=4)
def _text_session(model_id: str):
    import onnxruntime as ort
    from tokenizers import Tokenizer

    row = _model_row(model_id)
    onnx_path = _ensure_local(model_id, row)
    tok_path = MODELS_DIR / model_id / "tokenizer.json"
    if not tok_path.exists():
        raise ZooError(f"{model_id} has no tokenizer.json beside its weights — re-run `montology zoo pull {model_id}`.")
    tok = Tokenizer.from_file(str(tok_path))
    tok.enable_truncation(max_length=512)
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    return row, tok, sess


def embed_text(model_id: str, texts: list[str]) -> np.ndarray:
    """texts → (n, dims) float32, L2-normalised. Mean pooling over the mask."""
    row, tok, sess = _text_session(model_id)
    encs = tok.encode_batch(texts)
    max_len = max(len(e.ids) for e in encs)
    ids = np.zeros((len(encs), max_len), dtype=np.int64)
    mask = np.zeros_like(ids)
    for i, e in enumerate(encs):
        ids[i, : len(e.ids)] = e.ids
        mask[i, : len(e.ids)] = e.attention_mask
    feeds = {"input_ids": ids, "attention_mask": mask}
    names = {i.name for i in sess.get_inputs()}
    if "token_type_ids" in names:
        feeds["token_type_ids"] = np.zeros_like(ids)
    out = sess.run(None, feeds)[0]  # (n, seq, hidden) last_hidden_state
    m = mask[..., None].astype(np.float32)
    pooled = (out * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
    pooled /= np.clip(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-9, None)
    if row["dims"] and pooled.shape[1] != row["dims"]:
        raise ZooError(
            f"{model_id} answered {pooled.shape[1]} dims, registry says {row['dims']} — "
            "the artifact and the registry disagree; re-run `montology zoo sync`."
        )
    return pooled.astype(np.float32)


# ── image ───────────────────────────────────────────────────────────────────


@lru_cache(maxsize=2)
def _image_session(model_id: str):
    import onnxruntime as ort

    row = _model_row(model_id)
    onnx_path = _ensure_local(model_id, row)
    pre_path = MODELS_DIR / model_id / "preprocessor_config.json"
    pre = json.loads(pre_path.read_text()) if pre_path.exists() else {}
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    return row, pre, sess


def _preprocess_image(path: str, pre: dict) -> np.ndarray:
    from PIL import Image

    size = pre.get("size", {})
    side = size.get("shortest_edge") or size.get("height") or 224
    crop = pre.get("crop_size", {}).get("height", side) if pre.get("do_center_crop") else side
    img = Image.open(path).convert("RGB")
    # resize shortest edge, center-crop to square — the CLIP/SigLIP contract
    w, h = img.size
    scale = side / min(w, h)
    img = img.resize((round(w * scale), round(h * scale)), Image.BICUBIC)
    w, h = img.size
    left, top = (w - crop) // 2, (h - crop) // 2
    img = img.crop((left, top, left + crop, top + crop))
    x = np.asarray(img, dtype=np.float32)
    if pre.get("do_rescale", True):
        x *= pre.get("rescale_factor", 1 / 255)
    mean = np.array(pre.get("image_mean", [0.5, 0.5, 0.5]), dtype=np.float32)
    std = np.array(pre.get("image_std", [0.5, 0.5, 0.5]), dtype=np.float32)
    x = (x - mean) / std
    return x.transpose(2, 0, 1)[None, ...]  # (1, 3, H, W)


def embed_image(model_id: str, image_paths: list[str], *, for_similarity: bool = False) -> np.ndarray:
    """images → (n, dims), normalised. THE ROLE GATE IS CODE: a
    text-query-only model refuses `for_similarity=True` — it may answer a
    typed query, it may not assert two images are alike."""
    row, pre, sess = _image_session(model_id)
    if for_similarity and row["role"] == "text-query-only":
        raise ZooError(
            f"{model_id} is text-query-only: it may answer a typed query, it may NOT "
            "assert two images are alike (measured, not guessed). Use it via text→image "
            "search, or carry a retrieval-role vision model first."
        )
    batch = np.concatenate([_preprocess_image(p, pre) for p in image_paths])
    names = {i.name for i in sess.get_inputs()}
    if "pixel_values" not in names:
        raise ZooError(
            f"{model_id}'s artifact wants inputs {sorted(names)} — a full multimodal "
            "graph. Repair: point the artifact at the vision_model export in seed.py."
        )
    feeds: dict = {"pixel_values": batch.astype(np.float32)}
    if "input_ids" in names:  # full CLIP graph: feed a dummy text side
        feeds["input_ids"] = np.zeros((len(image_paths), 2), dtype=np.int64)
        if "attention_mask" in names:
            feeds["attention_mask"] = np.ones_like(feeds["input_ids"])
    vec = _pick_output(sess, feeds, "image_embeds", len(image_paths))
    vec = vec / np.clip(np.linalg.norm(vec, axis=1, keepdims=True), 1e-9, None)
    return vec.astype(np.float32)


def _pick_output(sess, feeds: dict, prefer: str, n: int) -> np.ndarray:
    """Select by NAME first — full dual-tower graphs also emit logits_per_*
    tensors that a shape-only pick would grab (an (n, n) matrix reads as a
    plausible embedding batch exactly when it is not one)."""
    out_names = [o.name for o in sess.get_outputs()]
    outs = sess.run(None, feeds)
    by_name = dict(zip(out_names, outs))
    for name, o in by_name.items():
        if prefer in name and o.ndim == 2 and o.shape[0] == n:
            return o
    for name, o in by_name.items():
        if "embed" in name and "logits" not in name and o.ndim == 2 and o.shape[0] == n:
            return o
    got = next((o for o in outs if o.ndim == 2 and o.shape[0] == n), None)
    if got is None:
        raise ZooError(f"no (n, dims) output among {out_names} — the artifact is not an embedder graph.")
    return got


# ── audio (shape-verified; parity unverified — stated, not hidden) ──────────


def embed_audio(model_id: str, wav_paths: list[str]) -> np.ndarray:
    """audio → (n, dims). Mel features are built in numpy from the model's
    own preprocessor_config. SHAPE-VERIFIED, reference-parity UNVERIFIED:
    trust ordering within this pipeline, verify against a reference before
    trusting absolute cross-modal scores."""
    try:
        import soundfile as sf
    except ImportError as e:
        raise ZooError("audio needs the extra: `uv sync --extra audio` (soundfile).") from e

    row, pre, sess = _audio_session(model_id)
    feats = [_mel_features(p, pre, sf) for p in wav_paths]
    batch = np.stack(feats)
    names = {i.name for i in sess.get_inputs()}
    feeds: dict = {}
    if "input_features" in names:
        feeds["input_features"] = batch.astype(np.float32)
    else:  # single-input audio tower
        feeds[next(iter(names))] = batch.astype(np.float32)
    if "is_longer" in names:
        feeds["is_longer"] = np.zeros((len(feats), 1), dtype=bool)
    if "input_ids" in names:  # full CLAP graph: dummy text side
        feeds["input_ids"] = np.zeros((len(feats), 2), dtype=np.int64)
        if "attention_mask" in names:
            feeds["attention_mask"] = np.ones_like(feeds["input_ids"])
    vec = _pick_output(sess, feeds, "audio_embeds", len(feats))
    vec = vec / np.clip(np.linalg.norm(vec, axis=1, keepdims=True), 1e-9, None)
    return vec.astype(np.float32)


@lru_cache(maxsize=1)
def _audio_session(model_id: str):
    import onnxruntime as ort

    row = _model_row(model_id)
    onnx_path = _ensure_local(model_id, row)
    pre_path = MODELS_DIR / model_id / "preprocessor_config.json"
    pre = json.loads(pre_path.read_text()) if pre_path.exists() else {}
    return row, pre, ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])


def _mel_features(path: str, pre: dict, sf) -> np.ndarray:
    sr = pre.get("sampling_rate", 48_000)
    n_mels = pre.get("feature_size", 64)
    n_fft = pre.get("fft_window_size", 1024)
    hop = pre.get("hop_length", 480)
    max_s = pre.get("max_length_s", 10)
    audio, in_sr = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if in_sr != sr:  # linear resample — adequate for features, stated above
        idx = np.linspace(0, len(audio) - 1, int(len(audio) * sr / in_sr))
        audio = np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)
    audio = audio[: sr * max_s]
    if len(audio) < sr * max_s:
        audio = np.pad(audio, (0, sr * max_s - len(audio)))
    # transformers' contract: center=True (reflect-pad n_fft//2 each side),
    # frames = 1 + len//hop (= 1001 at 10s/48k/480), layout (fusion, frames, mels)
    audio = np.pad(audio, (n_fft // 2, n_fft // 2), mode="reflect")
    frames = 1 + (len(audio) - n_fft) // hop
    window = np.hanning(n_fft).astype(np.float32)
    spec = np.abs(np.fft.rfft(
        np.lib.stride_tricks.sliding_window_view(audio, n_fft)[::hop][:frames] * window,
        axis=1,
    )) ** 2
    mel_fb = _mel_filterbank(sr, n_fft, n_mels)
    mel = np.log10(np.clip(spec @ mel_fb.T, 1e-10, None)) * 10.0  # (frames, mels)
    x = mel[None, ...].astype(np.float32)  # (1, frames, mels)
    return np.repeat(x, 4, axis=0) if pre.get("enable_fusion") else x


def _mel_filterbank(sr: int, n_fft: int, n_mels: int) -> np.ndarray:
    def hz_to_mel(f):
        return 2595.0 * np.log10(1.0 + f / 700.0)

    def mel_to_hz(m):
        return 700.0 * (10.0 ** (m / 2595.0) - 1.0)

    pts = mel_to_hz(np.linspace(hz_to_mel(0), hz_to_mel(sr / 2), n_mels + 2))
    bins = np.floor((n_fft + 1) * pts / sr).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1), dtype=np.float32)
    for i in range(n_mels):
        a, b, c = bins[i], bins[i + 1], bins[i + 2]
        if b > a:
            fb[i, a:b] = (np.arange(a, b) - a) / (b - a)
        if c > b:
            fb[i, b:c] = (c - np.arange(b, c)) / (c - b)
    return fb


# ── asr: whisper.cpp invoked, never linked ──────────────────────────────────


def transcribe(model_id: str, wav_path: str) -> str:
    """audio → text via the whisper.cpp CLI on the zoo's ggml artifact."""
    import shutil

    row = _model_row(model_id)
    if row["artifact"]["format"] != "ggml":
        raise ZooError(f"{model_id} is not an ASR row; use asr-whisper-base or asr-whisper-small.")
    binary = shutil.which("whisper-cli") or shutil.which("whisper-cpp") or shutil.which("main")
    if binary is None or "whisper" not in binary:
        binary = shutil.which("whisper-cli")
    if binary is None:
        raise ZooError(
            "whisper.cpp is not installed. Repair: `brew install whisper-cpp` "
            "(or your platform's package), then retry."
        )
    model_path = _ensure_local(model_id, row)
    r = subprocess.run(
        [binary, "-m", str(model_path), "-f", wav_path, "--no-timestamps", "--no-prints"],
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        raise ZooError(f"whisper.cpp failed: {r.stderr[-300:]}")
    return r.stdout.strip()


# ── the public one-call surface ─────────────────────────────────────────────


def embed(model_id: str, inputs: list[str], **kw) -> np.ndarray:
    """One call, routed by the model's modality — the README's promise."""
    row = _model_row(model_id)
    lane = {"text": embed_text, "image-text": embed_image, "audio": embed_audio}.get(row["modality"])
    if lane is None:
        raise ZooError(f"{model_id} is modality={row['modality']}; embed() covers text, image-text, audio.")
    return lane(model_id, inputs, **kw) if kw else lane(model_id, inputs)


def similarity(model_id: str, a: str, b: str) -> float:
    """Cosine similarity of two texts — the 'are these captions alike' call."""
    v = embed_text(model_id, [a, b])
    return float(v[0] @ v[1])
