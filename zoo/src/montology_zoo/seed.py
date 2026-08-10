"""The curated shelf: every model the zoo has ruled on, and where weights live.

CURATED, NOT SCRAPED — and the ruling is a column. ``carried`` rows have
verified artifact pointers and appear in ``zoo fit``; ``skip`` rows were
considered and declined, with the reason, so nothing gets re-litigated each
time a model list makes the rounds. (The evaluate tier was retired
2026-08-10 — a shelf tracks decisions, not hypotheticals; a candidate worth
carrying arrives as a carried row with verified artifacts.)

Artifact POINTERS live here; artifact SIZES and architecture facts do not —
``zoo sync`` fetches those from the HuggingFace API so every byte count in
the database is a measurement with a timestamp.

Selection bias, stated: multilingual text first (captions and briefs are
not English-only), rerankers because retrieval without reranking wastes the
good embedder, marketing-shaped classifiers (sentiment, zero-shot, NER),
image/audio pairs for creative, ASR for calls and podcast ads, and a tiny
GGUF generative shelf — optional, served by Ollama/llama.cpp/whisper.cpp,
never compiled into the default install.
"""

from __future__ import annotations

from .db import connect

# (id, repo, task, modality, dims, license, role, status, note)
MODELS = [
    # ── text embedders, carried ─────────────────────────────────────────────
    ("text-bge-m3", "BAAI/bge-m3", "embed", "text", 1024, "mit", "retrieval", "carried",
     "The multilingual workhorse: captions, briefs, SERPs; long context."),
    ("text-embeddinggemma", "onnx-community/embeddinggemma-300m-ONNX", "embed", "text",
     768, "gemma", "retrieval", "carried",
     "Google's 300M multilingual embedder, Matryoshka dims to 128 — the best "
     "small-first pick. Repo is the ONNX build; canonical google repo is gated."),
    ("text-qwen3-0.6b", "Qwen/Qwen3-Embedding-0.6B", "embed", "text", 1024,
     "apache-2.0", "retrieval", "carried",
     "Strong MTEB at 0.6B with 32k context — the long-document tier."),
    ("text-nomic-v2-moe", "nomic-ai/nomic-embed-text-v2-moe", "embed", "text", 768,
     "apache-2.0", "retrieval", "carried",
     "MoE: 475M total, 305M active — multilingual quality per FLOP."),
    ("text-bge-small", "BAAI/bge-small-en-v1.5", "embed", "text", 384, "mit",
     "retrieval", "carried",
     "English-only and light — when bge-m3 is more model than the task."),
    ("text-minilm", "sentence-transformers/all-MiniLM-L6-v2", "embed", "text", 384,
     "apache-2.0", "retrieval", "carried",
     "The tiny fast one: dedup, clustering, near-duplicate detection."),
    ("text-nomic-v1.5", "nomic-ai/nomic-embed-text-v1.5", "embed", "text", 768,
     "apache-2.0", "retrieval", "carried",
     "Long-context English with Matryoshka dims; strong mid-size choice."),

    # ── text embedders, ruled on ────────────────────────────────────────────
    ("text-bge-large", "BAAI/bge-large-en-v1.5", "embed", "text", 1024, "mit",
     "retrieval", "skip",
     "Covered: bge-m3 (multilingual, stronger) and nomic-v1.5 (same size class)."),
    ("text-e5-large", "intfloat/e5-large-v2", "embed", "text", 1024, "mit",
     "retrieval", "skip",
     "Covered by the carried English embedders; no capability the shelf lacks."),
    ("text-gte-large", "Alibaba-NLP/gte-large-en-v1.5", "embed", "text", 1024,
     "apache-2.0", "retrieval", "skip",
     "Long context is nomic-v1.5's job on this shelf; redundant."),
    ("text-jina-v2-base", "jinaai/jina-embeddings-v2-base-en", "embed", "text", 768,
     "apache-2.0", "retrieval", "skip",
     "Compact English is minilm/bge-small territory; redundant."),

    # ── rerankers ───────────────────────────────────────────────────────────
    ("rerank-bge-m3", "BAAI/bge-reranker-v2-m3", "rerank", "text", None,
     "apache-2.0", "scoring", "carried",
     "Multilingual cross-encoder; rerank the top-50 before showing a top-10."),
    ("rerank-minilm", "cross-encoder/ms-marco-MiniLM-L6-v2", "rerank", "text", None,
     "apache-2.0", "scoring", "carried",
     "The light reranker for English when speed beats nuance."),

    # ── classifiers ─────────────────────────────────────────────────────────
    ("classify-sentiment", "cardiffnlp/twitter-roberta-base-sentiment-latest",
     "classify", "text", None, "cc-by-4.0", "scoring", "carried",
     "Social-tuned sentiment — trained on tweets, which is what comments look like."),
    ("classify-zeroshot", "facebook/bart-large-mnli", "classify", "text", None, "mit",
     "scoring", "carried",
     "Zero-shot labels: any category list becomes a classifier, no training."),
    ("classify-ner", "dslim/bert-base-NER", "classify", "text", None, "mit",
     "scoring", "carried",
     "Entities in mentions — who and what a post talks about, for brand monitoring."),
    ("classify-topic-cardiff", "cardiffnlp/tweet-topic-latest-multi", "classify",
     "text", None, "mit", "scoring", "skip",
     "The social topic classifier everyone reaches for — but the repo ships "
     "PyTorch only, no ONNX. The topic lane is covered without it: fixed labels "
     "via carried classify-zeroshot, DISCOVERED topics via BERTopic/KeyBERT over "
     "the carried embedders (montology-zoo[topics]). Flip this ruling if an "
     "ONNX export lands."),
    ("classify-emotion-cardiff", "cardiffnlp/twitter-roberta-base-emotion-multilabel-latest",
     "classify", "text", None, "mit", "scoring", "skip",
     "Same PyTorch-only blocker as its topic sibling; sentiment (carried) plus "
     "zero-shot emotion labels cover the need meanwhile."),
    ("classify-distilbert-sst2", "distilbert/distilbert-base-uncased-finetuned-sst-2-english",
     "classify", "text", None, "apache-2.0", "scoring", "skip",
     "Covered: twitter-roberta is social-tuned, which is what marketing text is."),

    # ── creative: image ─────────────────────────────────────────────────────
    ("visual-siglip2", "google/siglip2-base-patch16-224", "embed-image", "image-text",
     768, "apache-2.0", "text-query-only", "carried",
     "Find creative by describing it. TEXT-QUERY ONLY: it may answer a typed "
     "query; it may NOT assert two images are alike — measured, not guessed."),
    ("visual-siglip2-so400m", "google/siglip2-so400m-patch14-384", "embed-image",
     "image-text", 1152, "apache-2.0", "text-query-only", "carried",
     "The production tier (PaliGemma's backbone) when base misses; same role gate."),
    ("visual-clip", "openai/clip-vit-base-patch32", "embed-image", "image-text", 512,
     "mit", "text-query-only", "carried",
     "The compatibility baseline every image-text eval speaks."),
    ("visual-clip-l14", "openai/clip-vit-large-patch14", "embed-image", "image-text",
     768, "mit", "text-query-only", "skip",
     "Between carried CLIP-B/32 and SigLIP2 there is no seat left for it."),
    ("classify-mobilenet", "google/mobilenet_v3_small", "classify", "image-text", None,
     "apache-2.0", "scoring", "skip",
     "ImageNet classes answer no marketing question without a fine-tune; "
     "zero-shot needs go to SigLIP2."),

    # ── creative: audio ─────────────────────────────────────────────────────
    ("audio-clap", "laion/larger_clap_general", "embed-audio", "audio", 512,
     "apache-2.0", "retrieval", "carried",
     "Sound and music similarity (LAION's general CLAP) — trend-tracking for "
     "audio-led platforms."),
    ("audio-vggish", "google/vggish", "embed-audio", "audio", 128, "apache-2.0",
     "retrieval", "skip",
     "CLAP covers audio embedding with text queries on top; VGGish adds nothing "
     "but age."),

    # ── ASR (calls, podcasts, video voiceovers) ─────────────────────────────
    ("asr-whisper-base", "openai/whisper-base", "asr", "audio", None, "apache-2.0",
     "transcribe", "carried",
     "Multilingual transcription for cheap; via whisper.cpp, never compiled here."),
    ("asr-whisper-small", "openai/whisper-small", "asr", "audio", None, "apache-2.0",
     "transcribe", "carried",
     "The accuracy step up that still runs on every laptop CPU."),
    ("asr-canary-qwen", "nvidia/canary-qwen-2.5b", "asr", "audio", None, "cc-by-4.0",
     "transcribe", "skip",
     "Best English WER but 2.5B — over the ceiling this zoo promised laptops."),
    ("asr-whisper-turbo", "openai/whisper-large-v3-turbo", "asr", "audio", None,
     "apache-2.0", "transcribe", "skip",
     "809M is fine but whisper-small carries the laptop tier; turbo is the "
     "documented upgrade path, not a second carried row."),

    # ── tabular (CRM, campaign tables) ──────────────────────────────────────

    # ── generative: the API-only ones, ruled on ─────────────────────────────
    ("gen-muse-image", "meta/muse-image", "generate", "image-text", None,
     "proprietary", "drafting", "skip",
     "Meta Muse Image/Spark are API-only — no open weights, so not zoo "
     "inventory. They belong in a tools package if creative generation lands."),

    # ── tiny generative (the optional GGUF shelf) ───────────────────────────
    ("gen-qwen2.5-0.5b", "Qwen/Qwen2.5-0.5B-Instruct", "generate", "text-gen", None,
     "apache-2.0", "drafting", "carried",
     "Offline extraction and normalisation on any laptop; served via Ollama/llama.cpp."),
    ("gen-smollm2-360m", "HuggingFaceTB/SmolLM2-360M-Instruct", "generate", "text-gen",
     None, "apache-2.0", "drafting", "carried",
     "Smaller still — structured extraction where 360M suffices."),
    ("gen-gemma3-270m", "unsloth/gemma-3-270m-it", "generate", "text-gen", None,
     "gemma", "drafting", "carried",
     "The smallest useful instruct model; fine-tunable on-device later. Repo is the "
     "ungated mirror of google/gemma-3-270m-it, whose gate blocks anonymous config reads."),
]

# (model_id, format, quant, repo, path) — carried models only.
# Pointers `zoo sync` verifies against the HF API; a wrong pointer fails sync
# loudly instead of shipping a dead download.
ARTIFACTS = [
    ("text-bge-m3", "onnx", "fp16", "Xenova/bge-m3", "onnx/model_fp16.onnx"),
    ("text-bge-m3", "gguf", "q8_0", "gpustack/bge-m3-GGUF", "bge-m3-Q8_0.gguf"),
    ("text-embeddinggemma", "onnx", "q8", "onnx-community/embeddinggemma-300m-ONNX",
     "onnx/model_quantized.onnx"),
    ("text-qwen3-0.6b", "gguf", "q8_0", "Qwen/Qwen3-Embedding-0.6B-GGUF",
     "Qwen3-Embedding-0.6B-Q8_0.gguf"),
    ("text-qwen3-0.6b", "onnx", "q8", "onnx-community/Qwen3-Embedding-0.6B-ONNX",
     "onnx/model_quantized.onnx"),
    ("text-nomic-v2-moe", "gguf", "q8_0", "nomic-ai/nomic-embed-text-v2-moe-GGUF",
     "nomic-embed-text-v2-moe.Q8_0.gguf"),
    ("text-bge-small", "onnx", "q8", "Xenova/bge-small-en-v1.5", "onnx/model_quantized.onnx"),
    ("text-minilm", "onnx", "fp32", "sentence-transformers/all-MiniLM-L6-v2", "onnx/model.onnx"),
    ("text-nomic-v1.5", "onnx", "fp32", "nomic-ai/nomic-embed-text-v1.5", "onnx/model.onnx"),
    ("text-nomic-v1.5", "gguf", "q8_0", "nomic-ai/nomic-embed-text-v1.5-GGUF",
     "nomic-embed-text-v1.5.Q8_0.gguf"),
    ("rerank-bge-m3", "onnx", "int8", "onnx-community/bge-reranker-v2-m3-ONNX",
     "onnx/model_int8.onnx"),
    ("rerank-minilm", "onnx", "fp32", "Xenova/ms-marco-MiniLM-L-6-v2", "onnx/model.onnx"),
    ("classify-sentiment", "onnx", "q8", "Xenova/twitter-roberta-base-sentiment-latest",
     "onnx/model_quantized.onnx"),
    ("classify-zeroshot", "onnx", "q8", "Xenova/bart-large-mnli", "onnx/model_quantized.onnx"),
    ("classify-ner", "onnx", "q8", "Xenova/bert-base-NER", "onnx/model_quantized.onnx"),
    ("visual-siglip2", "onnx", "fp32", "onnx-community/siglip2-base-patch16-224-ONNX",
     "onnx/model.onnx"),
    ("visual-siglip2-so400m", "onnx", "int8",
     "onnx-community/siglip2-so400m-patch14-384-ONNX", "onnx/model_int8.onnx"),
    ("visual-clip", "onnx", "q8", "Xenova/clip-vit-base-patch32", "onnx/model_quantized.onnx"),
    ("audio-clap", "onnx", "q8", "Xenova/larger_clap_general", "onnx/model_quantized.onnx"),
    ("asr-whisper-base", "ggml", "f16", "ggerganov/whisper.cpp", "ggml-base.bin"),
    ("asr-whisper-small", "ggml", "f16", "ggerganov/whisper.cpp", "ggml-small.bin"),
    ("gen-qwen2.5-0.5b", "gguf", "q4_k_m", "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
     "qwen2.5-0.5b-instruct-q4_k_m.gguf"),
    ("gen-smollm2-360m", "gguf", "q8_0", "HuggingFaceTB/SmolLM2-360M-Instruct-GGUF",
     "smollm2-360m-instruct-q8_0.gguf"),
    ("gen-gemma3-270m", "gguf", "q8_0", "ggml-org/gemma-3-270m-it-GGUF",
     "gemma-3-270m-it-Q8_0.gguf"),
]


def seed() -> str:
    conn = connect()
    for row in MODELS:
        conn.execute("INSERT OR REPLACE INTO model VALUES (?,?,?,?,?,?,?,?,?)", row)
    for m, fmt, quant, repo, path in ARTIFACTS:
        # keep measured bytes across re-seeds: INSERT OR IGNORE + pointer update
        conn.execute(
            "INSERT OR IGNORE INTO artifact VALUES (?,?,?,?,?,NULL,NULL)",
            (m, fmt, quant, repo, path),
        )
        conn.execute(
            "UPDATE artifact SET repo=?, path=? WHERE model_id=? AND format=? AND quant=?",
            (repo, path, m, fmt, quant),
        )
    conn.commit()
    carried = sum(1 for m in MODELS if m[7] == "carried")
    ev = sum(1 for m in MODELS if m[7] == "evaluate")
    sk = sum(1 for m in MODELS if m[7] == "skip")
    return f"seeded {len(MODELS)} models ({carried} carried, {ev} evaluate, {sk} skip), {len(ARTIFACTS)} artifacts"
