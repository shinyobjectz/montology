"""The lanes, live — integration: needs pulled weights (CI skips, laptops run)."""
import numpy as np
import pytest

from montology_zoo.pull import models_dir

pytestmark = pytest.mark.integration
needs = lambda mid, f: pytest.mark.skipif(not (models_dir() / mid / f).exists(),
                                          reason=f"{mid} not pulled")


@needs("text-minilm", "onnx/model.onnx")
def test_text_lane_discriminates():
    from montology_zoo import embed_text, similarity

    v = embed_text("text-minilm", ["a", "b"])
    assert v.shape == (2, 384)
    assert np.allclose((v ** 2).sum(1), 1.0, atol=1e-4)
    close = similarity("text-minilm", "our ceramic pan hits 500F fast",
                       "the pan reaches five hundred degrees quickly")
    far = similarity("text-minilm", "our ceramic pan hits 500F fast",
                     "our new lipstick ships in three shades")
    assert close > far + 0.2


@needs("visual-clip", "onnx/model_quantized.onnx")
def test_role_gate_is_code():
    from montology_zoo import ZooError, embed_image

    with pytest.raises(ZooError, match="text-query-only"):
        embed_image("visual-clip", ["/tmp/red.png"], for_similarity=True)
