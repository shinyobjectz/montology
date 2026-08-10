"""zoo fit: does this model run on THIS machine?

THE MATH, IN ONE PLACE, WITH ITS SOURCES STATED. Two kinds of number feed
it — measured facts (artifact bytes, layer counts: fetched by `zoo sync`)
and estimate constants (activation and overhead factors: typed HERE, named,
and justified). The output marks itself accordingly: sizes print exact,
peak-RAM figures print with a tilde, because they are estimates built on
measurements.

Encoder peak (ONNX, CPU, batch 1, seq ≤ 512):
    peak ≈ weights_bytes × ACT_FACTOR + ONNX_RUNTIME_MB
    ACT_FACTOR covers activations + runtime workspace. Encoder activations
    at batch 1/seq 512 are tens of MB; 1.5× is deliberately generous so
    "fits" stays trustworthy. Long-context embedders (bge-m3 at 8k) can
    exceed it — noted per row, not hidden in the constant.

Generative peak (GGUF via llama.cpp/Ollama):
    peak ≈ gguf_bytes + kv_cache(ctx) + GGUF_OVERHEAD_MB
    kv_cache = 2 × n_layers × n_kv_heads × head_dim × 2 bytes(f16) × ctx
    The 2× is K and V; f16 cache is the llama.cpp default. Arch numbers
    come from config.json via sync — never typed.

Usable memory:
    usable = min(total × 0.75, total − 4 GB)
    Both bounds are honest about laptops: the OS and a browser hold several
    GB, and unified-memory Macs cap a working set near 75%. On an 8 GB Air
    that yields 4 GB, which matches observed reality, not the spec sheet.

Verdicts: fits (peak ≤ 80% of usable) · tight (≤ usable) · no.
"""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
from dataclasses import dataclass

from .db import DB_PATH, connect

# ── the estimate constants, named and owned ─────────────────────────────────
ACT_FACTOR = 1.5          # encoder activations + ORT workspace, batch 1 seq ≤ 512
ONNX_RUNTIME_MB = 300     # onnxruntime CPU: session + allocator baseline
GGUF_OVERHEAD_MB = 250    # llama.cpp compute buffer + tokenizer + mmap slack
ASR_OVERHEAD_MB = 500     # whisper.cpp: mel buffers + KV + beam state (its own
                          # docs put base/small total near model + ~0.5 GB)
KV_CTX_DEFAULT = 4096     # the context the generative estimate assumes
FITS_HEADROOM = 0.8       # "fits" leaves a fifth of usable memory free


@dataclass(frozen=True, slots=True)
class Machine:
    os: str
    arch: str
    total_ram: int
    usable_ram: int
    free_disk: int
    apple_silicon: bool


def machine() -> Machine:
    total = _total_ram()
    usable = min(int(total * 0.75), max(total - 4 * 1024**3, total // 4))
    return Machine(
        os=platform.system(),
        arch=platform.machine(),
        total_ram=total,
        usable_ram=usable,
        free_disk=shutil.disk_usage(os.path.expanduser("~")).free,
        apple_silicon=(platform.system() == "Darwin" and platform.machine() == "arm64"),
    )


def _total_ram() -> int:
    if hasattr(os, "sysconf") and os.sysconf_names.get("SC_PHYS_PAGES"):
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    if platform.system() == "Windows":  # pragma: no cover — stdlib-only fallback
        class MemStatus(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_uint64), ("ullAvailPhys", ctypes.c_uint64),
                        ("ullTotalPageFile", ctypes.c_uint64), ("ullAvailPageFile", ctypes.c_uint64),
                        ("ullTotalVirtual", ctypes.c_uint64), ("ullAvailVirtual", ctypes.c_uint64),
                        ("ullAvailExtendedVirtual", ctypes.c_uint64)]
        status = MemStatus()
        status.dwLength = ctypes.sizeof(MemStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        return int(status.ullTotalPhys)
    return 8 * 1024**3  # unknown platform: assume a small laptop, stay honest


def peak_bytes(task: str, artifact_bytes: int, arch_row) -> int | None:
    """The peak-RAM estimate for one artifact. None = arch facts missing."""
    if task == "asr":
        # whisper.cpp holds the model plus roughly constant working buffers;
        # context is audio-window-bounded, not user-bounded.
        return artifact_bytes + ASR_OVERHEAD_MB * 1024**2
    if task == "generate":
        if arch_row is None or not all(
            arch_row[k] for k in ("n_layers", "n_kv_heads", "head_dim")
        ):
            return None
        kv = 2 * arch_row["n_layers"] * arch_row["n_kv_heads"] * arch_row["head_dim"] \
            * 2 * KV_CTX_DEFAULT
        return artifact_bytes + kv + GGUF_OVERHEAD_MB * 1024**2
    return int(artifact_bytes * ACT_FACTOR) + ONNX_RUNTIME_MB * 1024**2


def report() -> list[str]:
    """The fit table for this machine, one line per model's best artifact."""
    if not DB_PATH.exists():
        return ["The zoo database is empty. Repair: run `montology zoo sync` first."]
    m = machine()
    conn = connect()
    lines = [
        f"this machine: {m.os} {m.arch}"
        + (" (Apple Silicon, unified memory)" if m.apple_silicon else "")
        + f", {m.total_ram / 1024**3:.0f} GB RAM"
        f" ({m.usable_ram / 1024**3:.0f} GB usable), {m.free_disk / 1024**3:.0f} GB disk free",
        "",
    ]
    for model in conn.execute(
        "SELECT * FROM model WHERE status='carried' ORDER BY task, id"
    ).fetchall():
        arts = conn.execute(
            "SELECT * FROM artifact WHERE model_id=? AND bytes IS NOT NULL "
            "ORDER BY bytes ASC",
            (model["id"],),
        ).fetchall()
        if not arts:
            lines.append(f"  ?      {model['id']:<20} not synced — run `montology zoo sync`")
            continue
        best = arts[0]
        arch_row = conn.execute(
            "SELECT * FROM arch WHERE model_id=?", (model["id"],)
        ).fetchone()
        peak = peak_bytes(model["task"], best["bytes"], arch_row)
        if peak is None:
            lines.append(
                f"  ?      {model['id']:<20} {best['bytes'] / 1e6:>6.0f} MB  "
                f"{model['task']:<12} arch facts missing — re-run `zoo sync`"
            )
            continue
        verdict = ("fits" if peak <= m.usable_ram * FITS_HEADROOM
                   else "tight" if peak <= m.usable_ram else "no")
        via = ""
        if best["format"] == "gguf" and model["task"] == "generate":
            via = " (via ollama/llama.cpp)"
        elif best["format"] == "ggml":
            via = " (via whisper.cpp)"
        lines.append(
            f"  {verdict:<6} {model['id']:<20} {best['bytes'] / 1e6:>6.0f} MB "
            f"{best['format']}/{best['quant']:<7} ~{peak / 1024**2:>5.0f} MB peak  "
            f"{model['task']}{via}"
        )
    lines.append("")
    lines.append(
        f"peak figures are estimates: measured weights × documented factors "
        f"(encoders ×{ACT_FACTOR} + {ONNX_RUNTIME_MB} MB; generative + KV@{KV_CTX_DEFAULT} "
        f"+ {GGUF_OVERHEAD_MB} MB; ASR + {ASR_OVERHEAD_MB} MB). Sizes are measured. "
        f"evaluate/skip rows are not shown — `montology zoo list` has the full rulings."
    )
    return lines
