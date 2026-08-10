---
title: Voiceover Integration
description: ElevenLabs integration, scene JSON format, and timing synchronization
section: audio
priority: medium
tags: [voiceover, audio, elevenlabs, timing, sync, tts]
---

# Voiceover Integration for Instagram Ads

Complete guide for generating and integrating professional voiceovers into Remotion Instagram videos.

## Prerequisites

- ElevenLabs API key in `.env.local`

```bash
ELEVENLABS_API_KEY=your_api_key_here
```

---

## Model Selection

| Model | Languages | Best For |
|-------|-----------|----------|
| `eleven_v3` | 74 | Highest quality, emotional range, newest model |
| `eleven_multilingual_v2` | 29 | High quality, stable, good default for most use cases |
| `eleven_flash_v2_5` | 32 | ~75ms latency, real-time/preview use |
| `eleven_flash_v2` | 1 (English) | ~75ms latency, English-only fast preview |
| `eleven_turbo_v2_5` | 32 | Low latency with balanced quality |

> ⚠️ **`eleven_v3` warning — no request stitching, unstable timing.**
> v3 generates each scene independently, so timing drift between expected and
> actual scene durations can be significant (observed -2s+ on multi-second scenes).
> Pacing also varies more between runs. **Prefer `eleven_multilingual_v2` when
> you need predictable scene durations** (i.e., almost always for video work).
> Use `eleven_v3` only for one-shot single-scene generation where emotional
> nuance matters more than timing precision.

Use `--model` to select:

```bash
# Use the newest highest-quality model
node tools/generate.js \
  --scenes scenes.json \
  --model eleven_v3 \
  --output-dir public/audio/

# Use flash model for quick previews
node tools/generate.js \
  --scenes scenes.json \
  --model eleven_flash_v2_5 \
  --output-dir public/audio/
```

**Default**: `eleven_multilingual_v2`. Consider `eleven_v3` for final renders when emotional range matters (e.g., dramatic hooks, empathetic CTAs).

---

## Language Support

For multilingual ads, specify the language with ISO 639-1 codes to enforce correct pronunciation:

| Language | Code | Example Use |
|----------|------|-------------|
| English | `en` | Default |
| German | `de` | DACH market ads |
| French | `fr` | Francophone markets |
| Spanish | `es` | LATAM / Spain |
| Dutch | `nl` | Benelux market ads |

The model auto-detects language from text, but explicit codes help with mixed-language scripts or ambiguous text.

---

## Voice Settings

Fine-tune voice behavior with these parameters when using the API directly.

### Speed

The `speed` parameter controls the speaking rate as a multiplier:

| Value | Effect |
|-------|--------|
| `0.7` | 30% slower than normal |
| `1.0` | Normal speed (default) |
| `1.2` | 20% faster than normal |

Range: 0.7-1.2. Example:

```bash
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/YOUR_VOICE_ID" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is spoken at a slower, more deliberate pace.",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
      "stability": 0.7,
      "similarity_boost": 0.5,
      "style": 0.0,
      "speed": 0.85
    }
  }'
```

### Voice Settings Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `stability` | 0.0-1.0 | 0.5 | Higher = more consistent, lower = more expressive variation |
| `similarity_boost` | 0.0-1.0 | 0.75 | How closely to match the original voice. Higher = closer match |
| `style` | 0.0-1.0 | 0.0 | Style exaggeration. Higher = more dramatic. Adds latency |
| `speed` | 0.7-1.2 | 1.0 | Speaking rate multiplier |
| `use_speaker_boost` | boolean | true | Post-processing to enhance clarity and presence. Recommended for most use cases. Disable for raw audio post-processing |

### Voice Settings Presets by Use Case

| Use Case | Stability | Similarity | Style | Notes |
|----------|-----------|------------|-------|-------|
| Audiobooks/Narration | 0.7 | 0.5 | 0.0 | Consistent tone |
| Conversational/Chatbots | 0.4 | 0.75 | 0.3 | More expressive |
| News/Professional | 0.8 | 0.6 | 0.0 | Very consistent |
| Character/Drama | 0.3 | 0.8 | 0.5 | Highly expressive |

### Language Code Enforcement

Force a specific language for pronunciation, even if the text could be ambiguous:

```bash
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/YOUR_VOICE_ID" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Der Kaufvertrag wurde am Montag unterschrieben.",
    "model_id": "eleven_multilingual_v2",
    "language_code": "de"
  }'
```

This is especially important for mixed-language scripts or when the model might misdetect the language from short text segments.

---

## Pronunciation Dictionaries

Custom pronunciation dictionaries ensure brand names and technical terms are spoken correctly.

### Creating a Dictionary

1. Copy `dictionaries/template.pls` to `dictionaries/your-brand.pls`
2. Add lexeme entries for words needing custom pronunciation
3. Use `--dictionary your-brand` when generating

### Dictionary Format (PLS)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lexicon version="1.0"
      xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
      alphabet="ipa" xml:lang="de-DE">

  <!-- Brand name with phonetic pronunciation -->
  <lexeme>
    <grapheme>RF MedKonzept</grapheme>
    <alias>err eff Med Konzept</alias>
  </lexeme>

  <!-- Abbreviation spelled out -->
  <lexeme>
    <grapheme>bAV</grapheme>
    <alias>be ah fau</alias>
  </lexeme>

</lexicon>
```

### Using Dictionaries

```bash
# Use a specific dictionary
node tools/generate.js \
  --scenes scenes.json \
  --dictionary medkonzept \
  --output-dir public/audio/

# Disable dictionary (use default pronunciation)
node tools/generate.js \
  --scenes scenes.json \
  --no-dictionary \
  --output-dir public/audio/

# List available dictionaries
node tools/generate.js --list-dictionaries
```

### How It Works

1. **API Mode**: Dictionary is uploaded to ElevenLabs and applied during generation
2. **Fallback Mode**: If API permissions fail, text is preprocessed with replacements

The tool automatically caches dictionary IDs to avoid re-uploading

---

## Quick Start

```bash
# Generate voiceover from scenes JSON
node tools/generate.js \
  --scenes remotion/instagram-ads/scenes/ad-example-scenes.json \
  --with-timestamps \
  --output-dir public/audio/instagram-ads/ad-example/

# With pronunciation dictionary
node tools/generate.js \
  --scenes remotion/instagram-ads/scenes/ad-example-scenes.json \
  --dictionary medkonzept \
  --with-timestamps \
  --output-dir public/audio/instagram-ads/ad-example/
```

---

## Scene JSON Format

Create a scenes file for each ad at `remotion/instagram-ads/scenes/ad-{name}-scenes.json`:

```json
{
  "name": "ad-example",
  "voice": "YourVoiceName",
  "character": "narrator",
  "scenes": [
    {
      "id": "scene1",
      "text": "Hook text that grabs attention immediately.",
      "duration": 3.5,
      "character": "dramatic"
    },
    {
      "id": "scene2",
      "text": "Problem description. Multiple issues listed here.",
      "duration": 4.5,
      "character": "narrator"
    },
    {
      "id": "scene3",
      "text": "Solution presentation with key benefit.",
      "duration": 4.0,
      "character": "expert"
    },
    {
      "id": "scene4",
      "text": "Call to action. Your Brand Name.",
      "duration": 3.0,
      "character": "calm"
    }
  ]
}
```

### Character Presets

| Character | Description | Best For |
|-----------|-------------|----------|
| `literal` | Reads text exactly as written | Screen text, quotes |
| `narrator` | Professional storyteller, smooth | Explainers, general content |
| `salesperson` | Enthusiastic, persuasive | Marketing, ads |
| `expert` | Authoritative, confident | Professional content |
| `conversational` | Casual, friendly | Social media |
| `dramatic` | Intense, emotional | Hooks, problem statements |
| `calm` | Soothing, reassuring | Trust-building, CTAs |

---

## Output Files

After generation, the output directory contains:

```
public/audio/instagram-ads/ad-example/
├── ad-example-scene1.mp3      # Individual scene audio
├── ad-example-scene2.mp3
├── ad-example-scene3.mp3
├── ad-example-scene4.mp3
├── ad-example-combined.mp3    # All scenes stitched together
├── ad-example-info.json       # Metadata with actual durations
└── ad-example-captions.json   # Word-level timestamps (if --with-timestamps)
```

### info.json Structure

```json
{
  "name": "ad-example",
  "voice": "YourVoiceName",
  "totalDuration": 15.2,
  "scenes": [
    {
      "id": "scene1",
      "duration": 3.5,
      "actualDuration": 3.42,
      "text": "Hook text...",
      "file": "ad-example-scene1.mp3"
    }
  ]
}
```

**Important:** Use `actualDuration` from info.json in your Remotion composition for precise sync.

---

## Integration with Remotion

### Per-Scene Audio with TransitionSeries (Recommended)

When using `TransitionSeries` (fade/slide transitions between scenes), the combined audio file will drift out of sync because transitions overlap scenes visually. **Use per-scene audio files instead**, positioned with `Sequence` at the calculated start frame of each scene:

```tsx
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";

const FPS = 30;
const TRANSITION_FRAMES = Math.round(FPS * 0.6); // 18 frames
const PADDING = 5;

// Use actualDuration values from info.json
const SCENE1_FRAMES = Math.ceil(3.42 * FPS) + PADDING;
const SCENE2_FRAMES = Math.ceil(4.35 * FPS) + PADDING;
const SCENE3_FRAMES = Math.ceil(4.12 * FPS) + PADDING;
const SCENE4_FRAMES = Math.ceil(3.31 * FPS) + PADDING;

// Calculate when each scene starts in TransitionSeries
// Each scene starts (previous scene duration - transition overlap) after the last
const SCENE1_START = 0;
const SCENE2_START = SCENE1_FRAMES - TRANSITION_FRAMES;
const SCENE3_START = SCENE2_START + SCENE2_FRAMES - TRANSITION_FRAMES;
const SCENE4_START = SCENE3_START + SCENE3_FRAMES - TRANSITION_FRAMES;

export const TOTAL_FRAMES =
  SCENE1_FRAMES + SCENE2_FRAMES + SCENE3_FRAMES + SCENE4_FRAMES -
  3 * TRANSITION_FRAMES;

export const AdExample: React.FC = () => {
  return (
    <AbsoluteFill>
      {/* Visual: TransitionSeries for scene crossfades */}
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={SCENE1_FRAMES}>
          <Scene1Hook />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />
        <TransitionSeries.Sequence durationInFrames={SCENE2_FRAMES}>
          <Scene2Problem />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />
        <TransitionSeries.Sequence durationInFrames={SCENE3_FRAMES}>
          <Scene3Solution />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />
        <TransitionSeries.Sequence durationInFrames={SCENE4_FRAMES}>
          <Scene4CTA />
        </TransitionSeries.Sequence>
      </TransitionSeries>

      {/* Audio: per-scene voiceover, positioned to match visual starts */}
      <Sequence from={SCENE1_START}>
        <Audio src={staticFile("audio/ad-example/ad-example-scene1.mp3")} volume={1.0} />
      </Sequence>
      <Sequence from={SCENE2_START}>
        <Audio src={staticFile("audio/ad-example/ad-example-scene2.mp3")} volume={1.0} />
      </Sequence>
      <Sequence from={SCENE3_START}>
        <Audio src={staticFile("audio/ad-example/ad-example-scene3.mp3")} volume={1.0} />
      </Sequence>
      <Sequence from={SCENE4_START}>
        <Audio src={staticFile("audio/ad-example/ad-example-scene4.mp3")} volume={1.0} />
      </Sequence>

      {/* Audio: background music (low volume under voiceover) */}
      <Audio src={staticFile("audio/ad-example/background.mp3")} volume={0.15} />
    </AbsoluteFill>
  );
};
```

> **Why not the combined audio file?** With `TransitionSeries`, scenes overlap during transitions. The combined file plays all scenes back-to-back, so it drifts out of sync with the visuals — up to ~1s per transition. Per-scene audio stays locked to each visual scene.

### Combined Audio with Series (Simple, No Transitions)

If you use `Series` (no transition overlap), the combined audio file works fine:

```tsx
import { Audio, Series, staticFile, useVideoConfig } from "remotion";

const SCENE_DURATIONS = {
  scene1: 3.42,  // actualDuration from info.json
  scene2: 4.35,
  scene3: 4.12,
  scene4: 3.31,
};

export const AdSimple: React.FC = () => {
  const { fps } = useVideoConfig();
  const paddingFrames = 5;
  const scene1Frames = Math.round(SCENE_DURATIONS.scene1 * fps) + paddingFrames;
  const scene2Frames = Math.round(SCENE_DURATIONS.scene2 * fps) + paddingFrames;
  const scene3Frames = Math.round(SCENE_DURATIONS.scene3 * fps) + paddingFrames;
  const totalTargetFrames = Math.round(15 * fps);
  const scene4Frames = totalTargetFrames - scene1Frames - scene2Frames - scene3Frames;

  return (
    <AbsoluteFill>
      <Audio src={staticFile("audio/ad-example/ad-example-combined.mp3")} />
      <Series>
        <Series.Sequence durationInFrames={scene1Frames}>
          <Scene1Hook />
        </Series.Sequence>
        <Series.Sequence durationInFrames={scene2Frames}>
          <Scene2Problem />
        </Series.Sequence>
        <Series.Sequence durationInFrames={scene3Frames}>
          <Scene3Solution />
        </Series.Sequence>
        <Series.Sequence durationInFrames={scene4Frames}>
          <Scene4CTA />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
```

---

## Word-Level Timestamps (Captions)

> ⚠️ **`--with-timestamps` is not currently implemented in the bundled `generate.js`.**
> The flag is accepted but produces no `captions.json`. To get word-level
> timestamps from ElevenLabs, call the API directly with the
> `text_to_speech/with-timestamps` endpoint, or transcribe per-scene MP3s
> through Gemini audio understanding (see `gemini-tts.md` Step 4 — that
> approach works on any source MP3, not just Gemini-generated ones).

Generate with `--with-timestamps` for animated captions:

```bash
node tools/generate.js \
  --scenes scenes.json \
  --with-timestamps \
  --output-dir public/audio/instagram-ads/ad-example/
```

### captions.json Structure

```json
{
  "remotion": {
    "captions": [
      {
        "text": "Hook ",
        "startMs": 0,
        "endMs": 280,
        "timestampMs": 0,
        "sceneId": "scene1"
      },
      {
        "text": "text ",
        "startMs": 280,
        "endMs": 520,
        "timestampMs": 280,
        "sceneId": "scene1"
      }
    ]
  }
}
```

See [captions.md](captions.md) for complete caption integration guide.

---

## Regenerating Individual Scenes

If a scene needs adjustments:

```bash
# Regenerate scene2 with new text
node tools/generate.js \
  --scenes remotion/instagram-ads/scenes/ad-example-scenes.json \
  --scene scene2 \
  --new-text "Updated text for scene 2" \
  --output-dir public/audio/instagram-ads/ad-example/

# Regenerate with different character
node tools/generate.js \
  --scenes remotion/instagram-ads/scenes/ad-example-scenes.json \
  --scene scene3 \
  --character dramatic \
  --output-dir public/audio/instagram-ads/ad-example/
```

The tool automatically:
- Uses request stitching from previous scenes for consistent prosody
- Updates info.json with new metadata
- Updates scenes.json if `--new-text` is provided

---

## Text Replacement (Phonetic vs Display)

For brand names or words that need different pronunciation vs display:

```tsx
// In your composition
const TEXT_REPLACEMENTS: Record<string, string> = {
  // Example: TTS says "Acmee" but display should show "ACME"
  // "Acmee": "ACME",
  // "Fonetic": "Phonetic",
  // Add your brand-specific replacements
};

const getDisplayText = (text: string): string => {
  const trimmed = text.trim();
  const replaced = TEXT_REPLACEMENTS[trimmed] || trimmed;
  return replaced.toUpperCase();  // Optional: ALL CAPS for captions
};
```

Use phonetic spelling in scenes.json for correct pronunciation, then display the correct spelling in captions using the replacement map.

---

## Timing Validation

Validate generated audio matches expected durations:

```bash
node tools/generate.js --validate public/audio/instagram-ads/ad-example/
```

Output:
```
🔍 Validating ad-example (4 scenes)

✅ scene1: 3.42s (expected: 3.5s)
   👍 8 words @ 2.3 words/sec
⚠️ scene2: 4.85s (expected: 4.5s)
   ⚠️ Audio 0.35s longer than expected
❌ scene3: 3.00s (expected: 4.0s)
   ❌ Audio 1.00s shorter than expected
✅ scene4: 3.31s (expected: 3.0s)

📊 Total duration: 14.58s (expected: 15.00s)
```

---

## Best Practices

### Text Normalization

ElevenLabs can automatically normalize numbers, dates, and abbreviations for natural speech. When using the API directly, enable with `apply_text_normalization: "on"`:

- `"500"` is read as "five hundred" / "fünfhundert"
- `"24/7"` is read as "twenty-four seven"
- `"Dr."` is read as "Doctor"

This reduces the need to manually spell out numbers in scene scripts. However, for brand-critical pronunciation, still prefer explicit spelling or pronunciation dictionaries.

### Script Writing

1. **Keep scenes short**: 3-5 seconds each for Instagram
2. **Use punctuation**: Periods = pauses, commas = brief breaks
3. **Write numbers out**: "fünfhundert" not "500" (or enable text normalization)
4. **Spell out abbreviations**: "24 Stunden" not "24h"
5. **Front-load key messages**: Users may scroll away

### Voice Selection

**Finding the right voice**: Use `node tools/generate.js --list-voices` to browse all available voices. You can specify a voice by **name** (fuzzy matched) or **voice ID** (the 20-24 character alphanumeric string).

| Content Type | Recommended Voice Style |
|--------------|------------------------|
| Legal/professional | Expert, calm |
| Marketing/sales | Salesperson, narrator |
| Educational | Narrator, expert |
| Social/casual | Conversational |
| Emotional hook | Dramatic |

#### Brand Personality → Voice Guide

| Brand Personality | Voice Qualities | Example ElevenLabs Tags |
|-------------------|----------------|------------------------|
| Premium/luxury | Deep, smooth, unhurried | male, deep, mature |
| Friendly/approachable | Warm, medium pitch, natural | female/male, young, friendly |
| Bold/disruptive | Confident, energetic, punchy | male, strong, assertive |
| Trustworthy/institutional | Steady, authoritative, clear | male, mature, professional |
| Playful/youthful | Light, upbeat, casual | female, young, cheerful |
| Minimal/editorial | Understated, calm, measured | male/female, calm, neutral |

**Tip**: When a voice name isn't found, the tool tries prefix and substring matching (e.g., "Rachel" matches "Rachel - Conversational"). You can also use the voice ID directly from the ElevenLabs dashboard (e.g., `"pFZP5JQG7iQjIQuC4Bku"`).

### Duration Estimation

ElevenLabs actual output durations often differ from the `duration` hint in your scene JSON. Use word count to estimate realistic durations:

| Speaking Rate | Words/Second | Style | Example |
|---------------|-------------|-------|---------|
| Slow/dramatic | 2.0-2.5 wps | Hooks, emotional | "When was the last time you told someone they matter?" (11 words → ~4.5s) |
| Normal/narrative | 2.5-3.0 wps | Narration, explanation | General prose |
| Fast/conversational | 3.0-3.5 wps | Lists, casual | Quick feature lists |

**Rule of thumb**: Count the words in your scene text and divide by 2.5 for a conservative estimate. The actual audio will typically be within ±20% of this.

**Always use `actualDuration` from `info.json`** for your Remotion composition frame calculations — never rely on the estimated `duration` from the scene JSON.

### Timing Tips

1. Target 15 seconds total for Instagram Reels
2. Hook scene: 2-4 seconds (grab attention fast)
3. Problem scene: 3-5 seconds (establish pain point)
4. Solution scene: 3-5 seconds (present answer)
5. CTA scene: 2-4 seconds (clear next step)

---

## Output Format Options

Default output is MP3 (44.1kHz, 128kbps). Alternative formats available via the API:

| Format | Sample Rate | Bitrate | Use Case |
|--------|-------------|---------|----------|
| `mp3_22050_32` | 22,050 Hz | 32 kbps | Low quality, smallest file size |
| `mp3_44100_64` | 44,100 Hz | 64 kbps | Moderate quality, smaller file |
| `mp3_44100_128` | 44,100 Hz | 128 kbps | **Default.** Good for most use cases |
| `mp3_44100_192` | 44,100 Hz | 192 kbps | High quality MP3 |
| `pcm_16000` | 16,000 Hz | Raw | Speech-grade raw audio for post-processing |
| `pcm_24000` | 24,000 Hz | Raw | Higher quality raw audio |
| `pcm_44100` | 44,100 Hz | Raw | CD-quality raw audio |
| `pcm_48000` | 48,000 Hz | Raw | Studio-quality raw audio |
| `ulaw_8000` | 8,000 Hz | u-law | Telephony (North America) |
| `alaw_8000` | 8,000 Hz | A-law | Telephony (Europe) |
| `opus_48000_128` | 48,000 Hz | 128 kbps | Good quality Opus, efficient streaming |

For Remotion video production, `mp3_44100_128` (default) is recommended. Use `pcm_44100` when you need uncompressed audio for post-processing or mixing.

## Cost Monitoring

ElevenLabs charges per character. Track usage via the `x-character-count` response header. A typical 15-second ad with 4 scenes uses ~200-400 characters.

---

## Workflow Summary

```bash
# 1. Create scenes JSON
vim remotion/instagram-ads/scenes/ad-new-scenes.json

# 2. Generate voiceover with timestamps (and optional dictionary)
node tools/generate.js \
  --scenes remotion/instagram-ads/scenes/ad-new-scenes.json \
  --with-timestamps \
  --character narrator \
  --dictionary your-brand \
  --output-dir public/audio/instagram-ads/ad-new/

# 3. Check actual durations in info.json
cat public/audio/instagram-ads/ad-new/ad-new-info.json

# 4. Update composition with actual durations
# 5. Preview in Remotion Studio
npx remotion studio

# 6. If scene needs adjustment, regenerate just that scene
node tools/generate.js \
  --scenes remotion/instagram-ads/scenes/ad-new-scenes.json \
  --scene scene2 \
  --new-text "Adjusted text" \
  --output-dir public/audio/instagram-ads/ad-new/

# 7. Render final video
npx remotion render AdNew out/ad-new.mp4 --codec=h264 --crf=18
```

---

## Direct API Usage with JS SDK

> **JS SDK Warning:** Always use `@elevenlabs/elevenlabs-js`, not the deprecated `elevenlabs` package.

When using the ElevenLabs JS SDK directly (instead of the `tools/generate.js` wrapper):

```javascript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createWriteStream } from "fs";

const client = new ElevenLabsClient();

const audio = await client.textToSpeech.convert("YOUR_VOICE_ID", {
  text: "Your voiceover text here.",
  model_id: "eleven_multilingual_v2",
  language_code: "de",
  voice_settings: {
    stability: 0.7,
    similarity_boost: 0.5,
    style: 0.0,
    speed: 1.0,
    use_speaker_boost: true,
  },
  output_format: "mp3_44100_128",
});

audio.pipe(createWriteStream("output.mp3"));
```

---

## Speech-to-Text (Transcription)

ElevenLabs also offers transcription via the Scribe v2 model, useful for:

- Transcribing existing video/audio content to repurpose as ad scripts
- Generating captions from pre-recorded audio without the generate.js pipeline
- Speaker diarization for multi-speaker content

```bash
curl -X POST "https://api.elevenlabs.io/v1/speech-to-text" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -F "file=@audio.mp3" \
  -F "model_id=scribe_v2" \
  -F "timestamps_granularity=word" \
  -F "diarize=true"
```

Key features: 90+ languages, word-level timestamps, speaker diarization, keyterm prompting (up to 100 custom terms for domain-specific accuracy).

---

## Related Rules

- [sound-effects.md](sound-effects.md) - Generate transition and ambient SFX
- [music.md](music.md) - Background music generation
- [captions.md](captions.md) - Animated captions synced to word timestamps
