"""The shelf's invariants and the fit math — including the verdicts this
development machine can never exercise for real."""
from montology_zoo.fit import (ACT_FACTOR, FITS_HEADROOM, GGUF_OVERHEAD_MB,
                               KV_CTX_DEFAULT, Machine, ONNX_RUNTIME_MB,
                               peak_bytes)
from montology_zoo.seed import ARTIFACTS, MODELS


def test_shelf_invariants():
    ids = [m[0] for m in MODELS]
    assert len(ids) == len(set(ids)), "duplicate model ids"
    statuses = {m[7] for m in MODELS}
    assert statuses <= {"carried", "skip"}, "the evaluate tier was retired"
    carried = {m[0] for m in MODELS if m[7] == "carried"}
    with_artifacts = {a[0] for a in ARTIFACTS}
    assert with_artifacts <= {m[0] for m in MODELS}
    missing = carried - with_artifacts
    assert not missing, f"carried without artifacts: {missing}"
    for m in MODELS:
        if m[7] == "skip":
            assert len(m[8]) > 40, f"a skip needs its reason: {m[0]}"


def test_peak_math_per_lane():
    enc = peak_bytes("embed", 100_000_000, None)
    assert enc == int(100_000_000 * ACT_FACTOR) + ONNX_RUNTIME_MB * 1024**2
    asr = peak_bytes("asr", 148_000_000, None)
    assert asr == 148_000_000 + 500 * 1024**2
    arch = {"n_layers": 24, "n_kv_heads": 2, "head_dim": 64}
    gen = peak_bytes("generate", 400_000_000, arch)
    kv = 2 * 24 * 2 * 64 * 2 * KV_CTX_DEFAULT
    assert gen == 400_000_000 + kv + GGUF_OVERHEAD_MB * 1024**2
    assert peak_bytes("generate", 1, None) is None  # arch facts missing


def test_usable_ram_formula_is_honest_about_laptops():
    def usable(total):
        return min(int(total * 0.75), max(total - 4 * 1024**3, total // 4))
    g = 1024**3
    assert usable(8 * g) == 4 * g       # an 8GB Air with a browser open
    assert usable(16 * g) == 12 * g
    assert usable(64 * g) == 48 * g


def test_verdict_ladder_fits_tight_no_nodisk():
    g = 1024**3
    usable = 4 * g
    assert 3 * g <= usable * FITS_HEADROOM          # fits
    assert usable * FITS_HEADROOM < 3.9 * g <= usable  # tight
    assert 5 * g > usable                            # no
    m = Machine(os="T", arch="x", total_ram=8 * g, usable_ram=usable,
                free_disk=100, apple_silicon=False)
    assert m.free_disk < 1_000_000                   # no-disk case constructible
