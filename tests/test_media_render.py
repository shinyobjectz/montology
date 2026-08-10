"""Conversion and rendering — offline halves; the node/ffmpeg runs are
integration (skipped where the binaries are absent)."""
import shutil

import pytest

from montology_media import convert_image, data_uri, resize_image, to_wav16
from montology_crawl import render as rmod


def test_image_roundtrip_and_resize(tmp_path):
    from PIL import Image

    src = tmp_path / "a.png"
    Image.new("RGB", (600, 400), (10, 20, 30)).save(src)
    got = convert_image(str(src), "webp")
    assert got.startswith("wrote") and (tmp_path / "a.webp").exists()
    got = resize_image(str(src), 300, 250)
    assert "(300x250)" in got and (tmp_path / "a-300x250.png").exists()
    assert convert_image(str(src), "tiff").startswith("unknown target")
    assert convert_image("/no/file.png", "webp") == "no such file: /no/file.png"


def test_data_uri_and_cap(tmp_path):
    f = tmp_path / "x.png"
    f.write_bytes(b"abc")
    assert data_uri(str(f)).startswith("data:image/png;base64,")
    big = tmp_path / "big.png"
    big.write_bytes(b"0" * 600 * 1024)
    assert "inline cap" in data_uri(str(big))


def test_ffmpeg_absent_carries_repair(tmp_path, monkeypatch):
    from montology_media import av

    monkeypatch.setattr(shutil, "which", lambda name: None)
    f = tmp_path / "a.mp3"
    f.write_bytes(b"x")
    assert "brew install ffmpeg" in av.to_wav16(str(f))
    assert to_wav16("/no/file.mp3") == "no such file: /no/file.mp3"


def test_render_harness_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(rmod, "BRANDS_DIR", tmp_path / "projects")
    monkeypatch.setattr(rmod, "DESIGN_DIR", tmp_path / "design")
    # the harness template: node-resolvable react, automatic JSX, props seam,
    # and THE BRAND BINDING — design imports @brand/*, bound per render
    assert "nodePaths" in rmod.RENDER_MJS
    assert '"@brand"' in rmod.RENDER_MJS
    assert 'jsx: "automatic"' in rmod.RENDER_MJS
    assert "renderToStaticMarkup" in rmod.RENDER_MJS
    assert {"react", "react-dom", "esbuild"} <= set(rmod.PACKAGE_JSON["dependencies"])
    # a render against a missing component carries the projects/ repair
    (tmp_path / "design" / "node_modules").mkdir(parents=True)
    (tmp_path / "projects" / "acme").mkdir(parents=True)
    assert "no such component: projects/acme" in rmod.render("acme", "nope.tsx")


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="no ffmpeg")
def test_wav16_live(tmp_path):
    import subprocess

    src = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                    str(src)], capture_output=True, check=True)
    got = to_wav16(str(src))
    assert got.startswith("wrote")
