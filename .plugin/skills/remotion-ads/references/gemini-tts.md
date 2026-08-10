---
title: Gemini TTS Voice Generation
description: Google Gemini Flash TTS integration as alternative to ElevenLabs
section: audio
priority: medium
tags: [voiceover, audio, gemini, tts, google]
---

# Gemini TTS Voice Generation

Alternative TTS provider using Google's Gemini Flash TTS models. Supports director's notes for tone control, pause tags for pacing, and a post-processing pipeline for scene splitting + word-level captions.

> **No voice cloning.** Gemini TTS only ships with the 30 prebuilt voices listed below.
> If you need a custom/cloned voice, use ElevenLabs (Instant Voice Clone, ~1 min sample)
> or Google Cloud TTS Custom Voice (separate product, requires GCP setup).
>
> **Non-deterministic.** Same script + voice + model can vary 30–50% in total
> duration between runs. Use `--speed` to normalize, or re-run if a take is unusable.

## Prerequisites

```bash
GEMINI_API_KEY=your_api_key_here  # in .env.local
npm install @google/genai
```

---

## Model Selection

| Model | Quality | Best For |
|-------|---------|----------|
| `gemini-3.1-flash-tts-preview` | Highest, newest | Final renders, emotional range |
| `gemini-2.5-flash-preview-tts` | High | Good default |
| `gemini-2.5-pro-preview-tts` | Highest (slower) | Premium quality when speed doesn't matter |

---

## Available Voices (30)

| Voice | Personality |
|-------|------------|
| Zephyr | Bright |
| Puck | Upbeat |
| Charon | Informative |
| **Kore** | **Firm** (good for legal) |
| Fenrir | Excitable |
| Leda | Youthful |
| Orus | Firm |
| Aoede | Breezy |
| Callirrhoe | Informative |
| Autonoe | Bright |
| Enceladus | Breathy |
| Iapetus | Clear |
| Umbriel | Easy-going |
| Algieba | Smooth |
| Despina | Smooth |
| Erinome | Clear |
| Algenib | Gravelly |
| Rasalgethi | Informative |
| Laomedeia | Upbeat |
| Achernar | Soft |
| Alnilam | Firm |
| Schedar | Even |
| Gacrux | Mature |
| Pulcherrima | Forward |
| Achird | Friendly |
| Zubenelgenubi | Casual |
| Vindemiatrix | Gentle |
| Sadachbia | Lively |
| Sadaltager | Knowledgeable |
| Sulafat | Warm |

### Recommended Voices for Ad Content

| Use Case | Voice | Why |
|----------|-------|-----|
| Legal/professional | Kore, Alnilam, Orus | Firm, authoritative |
| Hook/dramatic | Fenrir, Puck | Excitable, attention-grabbing |
| Calm/reassuring CTA | Achernar, Vindemiatrix | Soft, gentle |
| Narrator/explainer | Charon, Schedar | Informative, even |
| Conversational | Achird, Zubenelgenubi | Friendly, casual |

---

## Critical: Single-Request Generation

**Always send the entire script in one API request.** Splitting scenes into separate requests produces inconsistent voice/tone between scenes because Gemini has no request stitching.

Use `[long pause]` tags between scenes to create silence gaps that can be detected and split in post-processing.

---

## Director's Notes + Prompt Structure

Structure your prompt with director's notes followed by the full script:

```
Audio Profile: Male German legal narrator for a short Instagram ad.
Scene: Professional legal consultation.
Director's Notes:
  Style: Confident, direct, trustworthy. Measured and clear, not dramatic.
  Accent: Standard German (Hochdeutsch).
  Pacing: Steady and deliberate. Let key legal terms land with weight.

Script:
Hat der Verkäufer Sie absichtlich getäuscht? [medium pause] Das ändert alles. [long pause] Gewährleistungsausschluss? [short pause] Bei Arglist unwirksam. [long pause] Kostenlose Erstberatung. [medium pause] Foss Liegal.
```

### Director's Notes Fields

| Field | Purpose | Example |
|-------|---------|---------|
| Audio Profile | Character identity | "Male German legal narrator" |
| Scene | Environmental context | "Professional consultation" |
| Style | Tone and delivery | "Confident, direct, not dramatic" |
| Accent | Regional pronunciation | "Hochdeutsch" |
| Pacing | Overall tempo | "Steady and deliberate" |

---

## Pause Tags

| Tag | Duration | Use For |
|-----|----------|---------|
| `[short pause]` | ~250ms | Between clauses, after commas |
| `[medium pause]` | ~500ms | Between sentences, emphasis |
| `[long pause]` | ~1000ms+ | **Between scenes** (used for split detection) |

**Important:** Use `[long pause]` between scenes — these become the split points in post-processing.

---

## Audio Style Tags

Embed inline to control delivery of specific words or phrases.

**Warning: Use sparingly.** Mixing multiple strong styles causes jarring tonal shifts. For ads, prefer director's notes for overall tone and let the voice carry naturally. Only use tags when a specific moment genuinely needs a different delivery.

### Available Tags

```
[whispers] [shouting] [excited] [sarcastic] [serious] [tired]
[sighs] [laughs] [crying] [very fast] [very slowly]
```

No limit to tags — the model interprets creative variations within brackets.

---

## Pronunciation Control

**No pronunciation dictionaries.** Use phonetic spelling in the script text, then replace for display in captions:

| Correct Spelling | Phonetic in Script | Why |
|-----------------|-------------------|-----|
| voss.legal | Foss Liegal | German "V" → "F" sound |
| Your brand | Phonetic spelling | Adjust as needed |

The text replacement happens in the post-processing pipeline (see below).

---

## Complete Pipeline: Generate → Split → Captions

### Overview

```
1. Generate    →  Single request with [long pause] between scenes
2. Convert     →  PCM to MP3 (ffmpeg)
3. Split       →  Silence detection finds [long pause] boundaries
4. Transcribe  →  Gemini audio understanding → word-level timestamps
5. Output      →  Per-scene MP3s + info.json + captions.json
```

### Step 1: Generate (single request)

```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const script = `Audio Profile: Male German legal narrator.
Director's Notes:
  Style: Confident, direct, trustworthy.
  Pacing: Steady and deliberate.

Script:
Scene 1 text here. [long pause] Scene 2 text here. [long pause] Scene 3 text here. [long pause] Scene 4 text here.`;

const response = await ai.models.generateContent({
  model: "gemini-3.1-flash-tts-preview",
  contents: [{ parts: [{ text: script }] }],
  config: {
    responseModalities: ["AUDIO"],
    speechConfig: {
      voiceConfig: {
        prebuiltVoiceConfig: { voiceName: "Alnilam" },
      },
    },
  },
});

const audioBuffer = Buffer.from(
  response.candidates[0].content.parts[0].inlineData.data,
  "base64"
);
fs.writeFileSync("output.pcm", audioBuffer);
```

### Step 2: Convert PCM to MP3

```bash
ffmpeg -y -f s16le -ar 24000 -ac 1 -i output.pcm -ar 44100 -ab 128k output.mp3
```

### Step 3: Split using silence detection

```bash
# Detect silences (≥0.35s at -30dB) — lower than the original 0.6s recommendation,
# because Gemini frequently emits inter-scene pauses around 0.4–0.6s, not 1.0s+.
ffmpeg -i output.mp3 -af silencedetect=noise=-30dB:d=0.35 -f null - 2>&1 | grep silence_
```

**Boundary picker — text-proportion-based (recommended).** The naive
"longest N-1 silences" heuristic fails when an in-scene sentence pause
exceeds an inter-scene `[long pause]`. Instead, compute each expected boundary
as the cumulative character proportion of total audio duration, then pick the
silence whose midpoint is closest to that target:

```javascript
// Compute expected boundaries from text proportions
const charLens = scenes.map((s) => s.text.length);
const totalChars = charLens.reduce((a, b) => a + b, 0);
const expected = [];
let acc = 0;
for (let i = 0; i < scenes.length - 1; i++) {
  acc += charLens[i];
  expected.push((acc / totalChars) * totalDuration);
}

// Pick silence closest to each expected boundary
const boundaries = expected.map((target) => {
  let best = silences[0], bestD = Infinity;
  for (const s of silences) {
    const mid = (s.start + s.end) / 2;
    const d = Math.abs(mid - target);
    if (d < bestD) { bestD = d; best = s; }
  }
  return (best.start + best.end) / 2;
});

// Cut per-scene
const cuts = [0, ...boundaries, totalDuration];
for (let i = 0; i < scenes.length; i++) {
  // ffmpeg -ss cuts[i] -to cuts[i+1] -c copy scene{i+1}.mp3
}
```

This is what the bundled `scripts/gemini-tts.mjs` does — robust to in-scene pauses.

### Optional: speed control via atempo (preserves pitch)

Gemini's natural pacing is **non-deterministic** between runs — the same script
can produce 17s on one take and 35s on the next. To get consistent output speed,
apply ffmpeg's `atempo` filter during PCM→MP3 conversion. `atempo` preserves
pitch and is free (post-process only).

```bash
# 1.1× speed-up applied during encode (preserves pitch)
ffmpeg -y -f s16le -ar 24000 -ac 1 -i output.pcm -af atempo=1.1 -ar 44100 -ab 128k output.mp3
```

Typical sweet spot: **1.0–1.15×**. Higher values sound rushed; lower values sound
sleepy if the take was already slow.

### Step 4: Transcribe for word-level timestamps

Use Gemini's audio understanding (not TTS) to transcribe each scene:

```javascript
const audioData = fs.readFileSync("scene1.mp3");
const base64Audio = audioData.toString("base64");

const response = await ai.models.generateContent({
  model: "gemini-2.5-flash",
  contents: [{
    parts: [
      { inlineData: { mimeType: "audio/mpeg", data: base64Audio } },
      { text: 'Transcribe this German audio with word-level timestamps. Return ONLY a JSON array where each element is {"text": "word", "startMs": number, "endMs": number}. No markdown, no explanation, just the JSON array.' },
    ],
  }],
});

// Returns: [{"text": "Hat", "startMs": 147, "endMs": 287}, ...]
```

### Step 5: Output

Produces the same file structure as the ElevenLabs pipeline:

```
output-dir/
├── ad-name-scene1.mp3          # Per-scene audio
├── ad-name-scene2.mp3
├── ad-name-scene3.mp3
├── ad-name-scene4.mp3
├── ad-name-combined.mp3        # Full audio
├── ad-name-info.json           # Scene durations
└── ad-name-captions.json       # Word-level timestamps (Remotion format)
```

**captions.json** uses the same Remotion-compatible format as ElevenLabs output:

```json
{
  "remotion": {
    "captions": [
      {
        "text": "Hat ",
        "startMs": 0,
        "endMs": 190,
        "timestampMs": 0,
        "sceneId": "scene1"
      }
    ]
  }
}
```

### Automated Script

A consolidated script is bundled with the skill — `scripts/gemini-tts.mjs`.
It performs all of Step 1–3 (generate → MP3 → silence-split with text-proportion
boundary picker → per-scene MP3s + info.json).

```bash
# Single command, no captions
node scripts/gemini-tts.mjs --scenes scenes.json --output-dir public/audio/ad-name/

# Override per-run
node scripts/gemini-tts.mjs \
  --scenes scenes.json \
  --output-dir public/audio/ad-name/ \
  --voice Vindemiatrix \
  --speed 1.1 \
  --model gemini-3.1-flash-tts-preview \
  --silence-d 0.35
```

The scenes JSON adds two Gemini-specific fields on top of the ElevenLabs format:

```json
{
  "name": "ad-name",
  "voice": "Vindemiatrix",
  "model": "gemini-2.5-flash-preview-tts",
  "speed": 1.0,
  "directorNotes": {
    "audioProfile": "Female German narrator for a recruiting ad.",
    "scene": "Friendly invitation.",
    "style": "Warm, sincere, conversational. Energetic but not salesy.",
    "accent": "Hochdeutsch",
    "pacing": "Natural, brisk pace. Keep momentum."
  },
  "scenes": [
    { "id": "scene1", "text": "..." },
    { "id": "scene2", "text": "..." }
  ]
}
```

**Word-level captions:** not yet implemented in this script. If you need them,
follow Step 4 separately on each per-scene MP3 (Gemini audio understanding).

### Legacy script names (deprecated)

Earlier versions of this doc referenced `gemini-tts-test.mjs` and
`gemini-tts-split.mjs`. Those have been consolidated into `gemini-tts.mjs`.

```bash
# (deprecated — kept for reference)
node scripts/gemini-tts-test.mjs

# Steps 2-5: Split + transcribe + output
node scripts/gemini-tts-split.mjs
```

---

## Multi-Speaker (up to 2)

```javascript
const response = await ai.models.generateContent({
  model: "gemini-3.1-flash-tts-preview",
  contents: [{
    parts: [{
      text: `Anwalt: Der Verkäufer hat den Mangel arglistig verschwiegen.
Mandant: Was bedeutet das für meinen Kaufvertrag?
Anwalt: Sie haben Anspruch auf Rücktritt vom Kaufvertrag.`,
    }],
  }],
  config: {
    responseModalities: ["AUDIO"],
    speechConfig: {
      multiSpeakerVoiceConfig: {
        speakerVoiceConfigs: [
          { speaker: "Anwalt", voiceConfig: { prebuiltVoiceConfig: { voiceName: "Kore" } } },
          { speaker: "Mandant", voiceConfig: { prebuiltVoiceConfig: { voiceName: "Puck" } } },
        ],
      },
    },
  },
});
```

---

## Language Support

85+ languages via BCP-47 codes. Language is auto-detected from text. For German legal content, no explicit language code needed.

---

## Comparison: ElevenLabs vs Gemini TTS

| Feature | ElevenLabs | Gemini TTS |
|---------|-----------|------------|
| Voice cloning | Yes (custom voices) | No (30 prebuilt) |
| Word-level timestamps | Native | Via post-processing (transcribe back) |
| Voice consistency | Request stitching | Single-request (send full script) |
| Pronunciation control | PLS dictionaries | Phonetic spelling in text |
| Style control | Voice settings params | Director's notes + inline tags |
| Multi-speaker | No (one voice/request) | Yes (up to 2) |
| Output format | MP3/PCM/WAV/Opus | PCM only (convert with ffmpeg) |
| Streaming | Yes | No |
| Languages | 29-74 | 85+ |
| Cost | Per-character | Per-request (Gemini pricing) |

### When to Use Which

**Use ElevenLabs when:**
- You need a specific custom/cloned voice
- You need native word timestamps without extra processing
- You need pronunciation dictionaries for many brand terms
- You need request stitching for very long content (>32k tokens)

**Use Gemini TTS when:**
- You want director's notes style control
- Multi-speaker dialogue
- Cost optimization
- The 30 built-in voices cover your needs
- You're already using Gemini API

---

## Limitations

1. **32k token context limit** per request (~128k characters of script)
2. **No streaming** — full audio returned in one response
3. **No pronunciation dictionaries** — phonetic spelling only
4. **PCM output only** — requires ffmpeg for MP3 conversion
5. **Max 2 speakers** per multi-speaker request
6. **Word timestamps require extra step** — transcribe audio back with Gemini audio understanding
7. **Transcription timestamps are approximate** — Gemini audio understanding is not a dedicated ASR; timestamps may drift ±100ms compared to ElevenLabs native timestamps

---

## Related

- [voiceover.md](voiceover.md) — ElevenLabs TTS (primary provider)
- [captions.md](captions.md) — Animated captions (word timestamps)
- [sound-effects.md](sound-effects.md) — SFX generation
