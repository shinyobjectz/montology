---
title: Sound Effects Generation
description: Generate AI sound effects with ElevenLabs for transitions, ambience, and emphasis in video content
section: audio
priority: medium
tags: [sound-effects, audio, elevenlabs, sfx, transitions, ambience]
---

# Sound Effects Generation

Generate AI-powered sound effects from text descriptions using ElevenLabs. Perfect for adding whooshes, impacts, ambient layers, and transition sounds to Instagram Reels and video ads.

## Prerequisites

- ElevenLabs API key in `.env.local` (same key as voiceover)

```bash
ELEVENLABS_API_KEY=your_api_key_here
```

---

## API Reference

### Endpoint

```
POST https://api.elevenlabs.io/v1/sound-generation
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | **required** | Sound effect description |
| `duration_seconds` | number \| null | null (auto) | Length 0.5-30s. null = auto-detect from prompt |
| `prompt_influence` | number \| null | 0.3 | How closely to follow the prompt (0-1). Higher = stricter |
| `loop` | boolean | false | Seamless looping for ambient backgrounds |
| `model_id` | string | `eleven_text_to_sound_v2` | Model to use for sound generation |
| `output_format` | string | `mp3_44100_128` | Audio output format (see Output Formats section) |

### Output Formats

Specify via the `output_format` query parameter or request body field. The 21 supported formats:

| Format | Sample Rate | Bitrate | Notes |
|--------|-------------|---------|-------|
| `mp3_22050_32` | 22,050 Hz | 32 kbps | Low quality, smallest file |
| `mp3_24000_48` | 24,000 Hz | 48 kbps | |
| `mp3_44100_32` | 44,100 Hz | 32 kbps | |
| `mp3_44100_64` | 44,100 Hz | 64 kbps | |
| `mp3_44100_96` | 44,100 Hz | 96 kbps | |
| `mp3_44100_128` | 44,100 Hz | 128 kbps | **Default.** Good balance of quality and size |
| `mp3_44100_192` | 44,100 Hz | 192 kbps | High quality MP3 |
| `pcm_8000` | 8,000 Hz | Raw | Telephony-grade raw audio |
| `pcm_16000` | 16,000 Hz | Raw | Speech-grade raw audio |
| `pcm_22050` | 22,050 Hz | Raw | |
| `pcm_24000` | 24,000 Hz | Raw | |
| `pcm_32000` | 32,000 Hz | Raw | |
| `pcm_44100` | 44,100 Hz | Raw | CD-quality raw audio |
| `pcm_48000` | 48,000 Hz | Raw | Studio-quality raw audio |
| `ulaw_8000` | 8,000 Hz | u-law | Telephony (North America) |
| `alaw_8000` | 8,000 Hz | A-law | Telephony (Europe) |
| `opus_48000_32` | 48,000 Hz | 32 kbps | Low bitrate Opus |
| `opus_48000_64` | 48,000 Hz | 64 kbps | |
| `opus_48000_96` | 48,000 Hz | 96 kbps | |
| `opus_48000_128` | 48,000 Hz | 128 kbps | Good quality Opus |
| `opus_48000_192` | 48,000 Hz | 192 kbps | High quality Opus |

For video production, `mp3_44100_128` (default) or `mp3_44100_192` are recommended. Use `pcm_44100` or `pcm_48000` when you need uncompressed audio for post-processing.

---

## Quick Start

### Generate with cURL

```bash
# Simple sound effect
curl -X POST "https://api.elevenlabs.io/v1/sound-generation" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Quick dramatic whoosh transition"}' \
  --output public/audio/sfx/whoosh.mp3

# With custom duration and high prompt adherence
curl -X POST "https://api.elevenlabs.io/v1/sound-generation" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Soft ambient office background noise with keyboard typing",
    "duration_seconds": 10,
    "prompt_influence": 0.7,
    "loop": true
  }' \
  --output public/audio/sfx/office-ambience.mp3
```

### Generate with Node.js

> **JS SDK Warning:** Always use `@elevenlabs/elevenlabs-js`. Do not use `npm install elevenlabs` (that is an outdated v1.x package).

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createWriteStream } from "fs";

const client = new ElevenLabsClient();

const audio = await client.textToSoundEffects.convert({
  text: "Quick dramatic whoosh transition",
  duration_seconds: 1.5,
  prompt_influence: 0.5,
});

audio.pipe(createWriteStream("public/audio/sfx/whoosh.mp3"));
```

### Generate with Python

```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs()
audio = client.text_to_sound_effects.convert(
    text="Quick dramatic whoosh transition",
    duration_seconds=1.5,
    prompt_influence=0.5,
)

with open("public/audio/sfx/whoosh.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

---

## Sound Effects for Video Ads

### Recommended SFX by Scene Type

| Scene Type | Sound Effect | Prompt Example | Duration |
|------------|-------------|----------------|----------|
| Hook / Intro | Whoosh, impact | `"Quick dramatic whoosh transition with bass impact"` | 0.5-1.5s |
| Problem reveal | Tension riser | `"Suspenseful tension building riser, dark"` | 2-3s |
| Stat / number | Pop / ding | `"Clean notification pop, modern UI sound"` | 0.5-1s |
| Solution reveal | Positive chime | `"Bright uplifting chime, achievement unlock"` | 1-2s |
| Scene transition | Swoosh | `"Smooth soft swoosh transition, left to right"` | 0.5-1s |
| CTA | Click / tap | `"Satisfying button click, digital interface"` | 0.5s |
| Background loop | Ambient | `"Calm professional office ambience, subtle"` | 5-15s |

> **API constraint:** `duration_seconds` must be between **0.5** and **30** seconds. The API will return a 422 error for values outside this range. Use `null` to let the model auto-detect duration from the prompt.

### Batch Generation Script

Generate a full set of SFX for an ad in one go:

```bash
#!/bin/bash
# generate-sfx.sh - Generate sound effects for a video ad
OUTPUT_DIR="public/audio/sfx"
mkdir -p "$OUTPUT_DIR"

generate_sfx() {
  local name="$1"
  local prompt="$2"
  local duration="$3"
  local influence="${4:-0.3}"

  echo "Generating: $name"
  curl -s -X POST "https://api.elevenlabs.io/v1/sound-generation" \
    -H "xi-api-key: $ELEVENLABS_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$prompt\", \"duration_seconds\": $duration, \"prompt_influence\": $influence}" \
    --output "$OUTPUT_DIR/$name.mp3"
  echo "  -> $OUTPUT_DIR/$name.mp3"
}

# Common ad SFX kit
generate_sfx "whoosh-in"    "Quick dramatic whoosh sweep, cinematic"           1.0  0.5
generate_sfx "whoosh-out"   "Soft whoosh sweep outward, gentle"                0.8  0.5
generate_sfx "impact"       "Deep bass impact hit, dramatic, cinematic"        1.0  0.6
generate_sfx "pop"          "Clean bright pop, modern notification"            0.5  0.5
generate_sfx "chime"        "Uplifting bright chime, success, achievement"     1.5  0.5
generate_sfx "riser"        "Tension building riser, suspenseful, dramatic"    3.0  0.5
generate_sfx "click"        "Satisfying digital button click"                  0.5  0.5
generate_sfx "transition"   "Smooth cinematic scene transition swoosh"         1.0  0.5

echo "Done! Generated SFX in $OUTPUT_DIR"
```

---

## Integration with Remotion

### Adding SFX to Scene Transitions

```tsx
import { Audio, Sequence, staticFile, useVideoConfig } from "remotion";

export const AdWithSFX: React.FC<{
  scene1Frames: number;
  scene2Frames: number;
}> = ({ scene1Frames, scene2Frames }) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      {/* Whoosh at scene transition */}
      <Sequence from={scene1Frames - Math.round(0.3 * fps)}>
        <Audio
          src={staticFile("audio/sfx/whoosh-in.mp3")}
          volume={0.6}
        />
      </Sequence>

      {/* Impact when key stat appears */}
      <Sequence from={scene1Frames + Math.round(1 * fps)}>
        <Audio
          src={staticFile("audio/sfx/impact.mp3")}
          volume={0.4}
        />
      </Sequence>

      {/* Pop for each bullet point */}
      <Sequence from={scene2Frames + Math.round(0.5 * fps)}>
        <Audio
          src={staticFile("audio/sfx/pop.mp3")}
          volume={0.3}
        />
      </Sequence>
    </AbsoluteFill>
  );
};
```

### SFX Volume Guidelines

| Layer | Volume | Notes |
|-------|--------|-------|
| Voiceover | 1.0 | Always loudest |
| Sound effects | 0.3-0.6 | Accent, not overpower |
| Background music | 0.10-0.20 | Subtle bed during voiceover |

Keep SFX subtle. They should enhance transitions and key moments without competing with the voiceover.

---

## Prompt Writing Tips

1. **Be specific**: `"Heavy rain on a tin roof"` beats `"rain sound"`
2. **Combine elements**: `"Thunder rumbling with light rain and distant wind"`
3. **Specify mood**: `"Cheerful bright notification ding"` vs `"Dark ominous notification tone"`
4. **Include context**: `"Cinematic whoosh for video transition"` helps guide style
5. **Use `prompt_influence`**: Set 0.5-0.8 for precise sounds, 0.1-0.3 for creative variation

### Looping Sounds

For ambient backgrounds that need to loop seamlessly:

```bash
curl -X POST "https://api.elevenlabs.io/v1/sound-generation" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Calm coffee shop ambience, soft chatter, espresso machine",
    "duration_seconds": 15,
    "loop": true
  }' \
  --output public/audio/sfx/cafe-loop.mp3
```

Use looped audio in Remotion with the `loop` prop:

```tsx
<Audio
  src={staticFile("audio/sfx/cafe-loop.mp3")}
  volume={0.15}
  loop
/>
```

---

## File Organization

```
public/audio/sfx/
├── whoosh-in.mp3         # Scene intro transitions
├── whoosh-out.mp3        # Scene outro transitions
├── impact.mp3            # Dramatic emphasis
├── pop.mp3               # Bullet points, stats
├── chime.mp3             # Positive reveals, success
├── riser.mp3             # Tension building
├── click.mp3             # CTA, button press
├── transition.mp3        # Generic scene change
└── ambience/
    ├── office-loop.mp3   # Office background
    └── cafe-loop.mp3     # Cafe background
```

---

## Error Handling

| Code | Meaning | Fix |
|------|---------|-----|
| 401 | Invalid API key | Check `ELEVENLABS_API_KEY` in `.env.local` |
| 422 | Invalid parameters | Check `duration_seconds` is 0.5-30, `prompt_influence` is 0-1 |
| 429 | Rate limited | Wait and retry, or upgrade plan |

---

## Best Practices

1. **Less is more** - Use 2-3 SFX per 15-second ad, not every second
2. **Time SFX to visuals** - Sync whooshes with slide-ins, pops with text reveals
3. **Pre-generate a kit** - Build a reusable set of SFX for consistent branding
4. **Layer carefully** - Never stack more than one SFX at the same time
5. **Test with voiceover** - Always preview SFX alongside the voice track
6. **Use looping for ambience** - Set `loop: true` for background textures

## Related Rules

- [voiceover.md](voiceover.md) - ElevenLabs voiceover generation
- [music.md](music.md) - Background music generation
- [captions.md](captions.md) - Animated captions synced to audio
