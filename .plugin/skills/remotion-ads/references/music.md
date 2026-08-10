---
title: Background Music Generation
description: Generate AI background music using Suno or ElevenLabs for Instagram Reels and video content
section: audio
priority: medium
tags: [music, audio, suno, elevenlabs, background, instrumental]
---

# Background Music Generation

Generate professional AI background music for Instagram Reels using **Suno** (via browser-use API) or **ElevenLabs** (native API).

| Provider | Strengths | Auth |
|----------|-----------|------|
| **Suno** | Artist style conversion, longer tracks, vocal support | Browser token (expires 24h) |
| **ElevenLabs** | Native API, composition plans, no browser token needed | Same API key as voiceover |

---

## ElevenLabs Music Generation

Generate music directly through the ElevenLabs API. No browser token required -- uses the same API key as voiceover and sound effects.

### API Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | - | Text description of the music to generate (use with prompt mode) |
| `music_length_ms` | number | - | Duration in milliseconds. Range: 3,000-600,000ms (3 seconds to 10 minutes) |
| `model_id` | string | `music_v1` | Model to use for music generation |
| `force_instrumental` | boolean | false | Guarantees no vocals in prompt mode. Use for background music under voiceover |
| `respect_sections_durations` | boolean | false | Enforces exact `duration_ms` values in composition plan sections |
| `composition_plan` | object | - | Structured composition plan (alternative to prompt mode) |

> **Duration range**: 3,000-600,000ms (3 seconds to 10 minutes).

### Quick Start

```bash
# Simple instrumental track
curl -X POST "https://api.elevenlabs.io/v1/music/compose" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A chill lo-fi hip hop beat with jazzy piano chords",
    "music_length_ms": 30000,
    "force_instrumental": true
  }' \
  --output public/audio/background.mp3
```

### With Python SDK

```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs()
audio = client.music.compose(
    prompt="Professional ambient music for a corporate video, subtle piano with soft strings",
    music_length_ms=30000,
)

with open("public/audio/background.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

### With JS SDK

> **JS SDK Warning:** Always use `@elevenlabs/elevenlabs-js`. Do not use `npm install elevenlabs` (that is an outdated v1.x package).

```javascript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
const client = new ElevenLabsClient();
const audio = await client.music.compose({
  prompt: "A chill lo-fi beat",
  musicLengthMs: 30000,
});
```

### Composition Plans (Advanced)

For granular control over musical structure, generate a plan first, modify it, then compose:

```python
# 1. Generate a composition plan
plan = client.music.composition_plan.create(
    prompt="Epic orchestral piece building to a climax, then resolving peacefully",
    music_length_ms=60000,
)

# 2. Inspect/modify the plan (sections, styles, instruments)
print(plan)

# 3. Compose from the plan
audio = client.music.compose(
    composition_plan=plan,
    music_length_ms=60000,
    respect_sections_durations=True,  # Enforce exact section durations
)
```

#### Composition Plan Response Structure

When you create a composition plan, the response includes:

```json
{
  "positiveGlobalStyles": ["cinematic", "orchestral", "epic"],
  "negativeGlobalStyles": ["electronic", "lo-fi"],
  "sections": [
    {
      "name": "Intro",
      "duration_ms": 15000,
      "localStyles": ["soft", "building"],
      "lines": []
    },
    {
      "name": "Climax",
      "duration_ms": 30000,
      "localStyles": ["powerful", "full orchestra"],
      "lines": []
    },
    {
      "name": "Resolution",
      "duration_ms": 15000,
      "localStyles": ["peaceful", "fading"],
      "lines": []
    }
  ]
}
```

- **positiveGlobalStyles**: Styles applied across the entire track
- **negativeGlobalStyles**: Styles to avoid
- **sections[].localStyles**: Styles specific to each section
- **sections[].duration_ms**: Duration for each section (enforced when `respect_sections_durations=true`)
- **sections[].lines**: Lyric lines (empty for instrumental)

### compose_detailed Method

The `compose_detailed` method returns both the audio and the composition plan metadata in a single call:

```python
result = client.music.compose_detailed(
    prompt="Professional ambient background music",
    music_length_ms=30000,
    force_instrumental=True,
)

# result contains: json (metadata), filename, audio (binary)
print(result.json)       # Composition plan and metadata
print(result.filename)   # Suggested filename
# result.audio contains the audio bytes
```

This is useful when you want to inspect the composition plan that was used, or when you need the metadata for downstream processing.

### Content Restrictions

ElevenLabs music generation cannot reference specific artists, bands, or copyrighted lyrics. If your prompt triggers a `bad_prompt` error, the API returns a `prompt_suggestion` alternative.

---

## Suno Music Generation

Generate music using Suno via browser-use API. Best for when you need artist style references or longer tracks.

**Key Features:**
- Automatic artist/song reference conversion (removes trademarks, preserves style)
- Automatic fade out for smooth Remotion integration
- TypeScript-based CLI tool

---

## Setup Instructions

### Step 1: Get Your API Keys

You need two API keys:

1. **Browser-Use API Key**: Get from [browser-use.com](https://browser-use.com)
2. **Suno Authorization Token**: Get from browser DevTools (see below)

### Step 2: Get Your Suno Authorization Token

1. Go to [suno.com](https://suno.com) and log in
2. Open Developer Tools:
   - **Chrome/Edge**: Press `F12` or `Ctrl+Shift+I` (`Cmd+Option+I` on Mac)
   - **Firefox**: Press `F12` or `Ctrl+Shift+I` (`Cmd+Option+I` on Mac)
3. Go to the **Network** tab
4. Make any action on the Suno website
5. Find a request to `studio-api.suno.ai`
6. Copy the `authorization` header value (without "Bearer ")

### Step 3: Add Tokens to Environment

Create or edit `.env.local` in your project root:

```bash
# .env.local
BROWSER_USE_API_KEY=bu_your_key_here
SUNO_API_KEY=eyJhbGciOiJSUzI1NiIsIn...
```

### Step 4: Verify Setup

```bash
npx tsx tools/suno-direct.ts -p "Test ambient music" -i -o test.mp3
```

### Token Expiration

Suno tokens expire after approximately **24 hours**. If you get authorization errors, repeat Step 2 to get a fresh token.

---

## Quick Start

```bash
# Generate instrumental background music with fade out
npx tsx tools/suno-direct.ts \
  -p "Ambient, cinematic background for professional video" \
  -t "ambient, cinematic, professional" \
  -i \
  -o public/audio/background.mp3

# Generate with artist style reference (auto-converted!)
npx tsx tools/suno-direct.ts \
  -p "In the style of Tom Misch, groovy and jazzy" \
  -i \
  -o public/audio/groovy-background.mp3
# → Automatically converts to: "groovy electric guitar, jazzy neo-soul funk..."

# Custom fade duration (5 seconds)
npx tsx tools/suno-direct.ts \
  -p "Dramatic cinematic music" \
  -t "cinematic, dramatic, orchestral" \
  -i \
  --fade 5 \
  -o public/audio/dramatic.mp3

# No fade out
npx tsx tools/suno-direct.ts \
  -p "Upbeat intro music" \
  --fade 0 \
  -o public/audio/intro.mp3
```

---

## Artist/Song Style Conversion

The tool **automatically detects and converts artist or song references** to style descriptions. This removes trademarked names while preserving the musical style.

### How It Works

When you mention an artist like "Lana Del Rey" or a song like "Bohemian Rhapsody", the tool:

1. Detects the reference in your prompt or tags
2. Converts it to a style description (e.g., "dreamy cinematic pop, melancholic vocals, vintage Americana")
3. Adds relevant style tags automatically
4. Shows you the conversion before generating

### Examples

| Your Input | Converted To |
|------------|--------------|
| "Like Hans Zimmer" | "epic cinematic scores, powerful orchestration, electronic elements, dramatic builds" |
| "In the style of Billie Eilish" | "dark whisper-pop, minimalist beats, atmospheric production, ASMR-like vocals" |
| "Daft Punk vibes" | "French house, vocoder vocals, disco funk, robotic themes, groovy basslines" |
| "Similar to Bohemian Rhapsody" | "operatic rock, multi-section structure, dramatic dynamics, harmonized vocals" |

### List All Known Artists

```bash
python3 tools/suno.py --list-styles
```

Shows all 50+ artists and 20+ songs with their style descriptions, organized by genre:
- Pop, Rock, Hip-Hop, R&B/Soul
- Electronic, Alternative, Country
- Jazz, Classical/Cinematic, Latin, Metal

### Skip Conversion

If you want to use artist names directly (not recommended):
```bash
python3 tools/suno.py --prompt "..." --no-convert
```

---

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--prompt`, `-p` | Lyrics or description of the music | Required |
| `--tags`, `-t` | Style/genre tags (comma-separated) | `ambient, professional` |
| `--title` | Song title | Auto-generated |
| `--instrumental`, `-i` | Generate without vocals | false |
| `--output`, `-o` | Output file path | `output.mp3` |
| `--output-dir` | Output directory for batch | `public/audio/` |
| `--count`, `-n` | Number of variations | 1 |
| `--wait-timeout` | Max wait for generation (seconds) | 300 |
| `--help`, `-h` | Show help | - |

---

## Recommended Tags by Content Type

### For Video Backgrounds (Most Common)
```
ambient, cinematic, professional, minimal, corporate, soft, elegant, background
```

### For Instagram Reels
```
upbeat, modern, energetic, trendy, social media, short form, catchy
```

### For Dramatic/Legal Content
```
dramatic, tension, suspense, cinematic, orchestral, building, serious
```

### For Professional/Corporate
```
trustworthy, professional, corporate, clean, minimal, subtle, business
```

### For Emotional Content
```
emotional, hopeful, inspiring, heartfelt, reassuring, warm
```

---

## Prompting Best Practices

### Structure Your Prompts

Include these elements for best results:

1. **Mood/Emotion**: "professional", "dramatic", "hopeful"
2. **Genre/Style**: "ambient", "cinematic", "electronic"
3. **Duration**: "30 seconds", "1 minute"
4. **Structure**: "starts subtle, builds in middle, fades at end"
5. **Special instructions**: "no vocals", "suitable for voiceover"

### Example Prompts

#### For Instagram Reel Background (Recommended)
```
Professional, trustworthy ambient music for a legal services video.
Subtle piano with soft strings. Starts quietly, builds slightly in middle,
gentle fade at end. 30 seconds. Instrumental only, suitable for voiceover on top.
```

#### For Dramatic Hook Scene
```
Dramatic tension building intro, 5 seconds of suspense,
then transitions to hopeful/reassuring tone. Cinematic feel.
Instrumental only. Total 15 seconds.
```

#### For CTA/Outro
```
Uplifting, positive outro music. Clean and professional.
Builds to confident finish. 10 seconds. No vocals.
```

---

## Integration with Remotion

### Basic Background Music

```tsx
import { Audio, staticFile } from "remotion";

export const AdWithMusic: React.FC = () => {
  return (
    <AbsoluteFill>
      {/* Background music - low volume */}
      <Audio
        src={staticFile("audio/instagram-ads/ad-example/background.mp3")}
        volume={0.25}
      />

      {/* Voiceover on top - full volume */}
      <Audio
        src={staticFile("audio/instagram-ads/ad-example/ad-example-combined.mp3")}
        volume={1.0}
      />

      {/* Visual content */}
      <VideoContent />
    </AbsoluteFill>
  );
};
```

### Volume Ducking During Voiceover

Lower background music when voiceover is speaking:

```tsx
import { Audio, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const AdWithDucking: React.FC<{
  voiceoverStart: number;  // Frame where voiceover begins
  voiceoverEnd: number;    // Frame where voiceover ends
}> = ({ voiceoverStart, voiceoverEnd }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade duration in frames
  const fadeFrames = Math.round(0.5 * fps);  // 0.5 second fade

  // Duck music volume during voiceover
  const musicVolume = interpolate(
    frame,
    [
      voiceoverStart - fadeFrames,  // Start fading down
      voiceoverStart,                // Fully ducked
      voiceoverEnd,                  // Still ducked
      voiceoverEnd + fadeFrames,     // Fade back up
    ],
    [0.35, 0.12, 0.12, 0.35],  // From 35% to 12% during voiceover
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <>
      <Audio
        src={staticFile("audio/instagram-ads/ad-example/background.mp3")}
        volume={musicVolume}
      />
      <Audio
        src={staticFile("audio/instagram-ads/ad-example/ad-example-combined.mp3")}
        volume={1.0}
      />
    </>
  );
};
```

### Scene-Based Volume Control

Different music volume for different scenes:

```tsx
import { Audio, Sequence, staticFile, useVideoConfig } from "remotion";

export const AdWithSceneMusic: React.FC = () => {
  const { fps } = useVideoConfig();

  // Scene frame calculations
  const scene1Frames = Math.round(3.5 * fps);
  const scene2Frames = Math.round(4.5 * fps);
  const scene3Frames = Math.round(4.0 * fps);
  const scene4Frames = Math.round(3.0 * fps);

  const scene2Start = scene1Frames;
  const scene3Start = scene2Start + scene2Frames;
  const scene4Start = scene3Start + scene3Frames;
  const totalFrames = scene4Start + scene4Frames;

  return (
    <AbsoluteFill>
      {/* Music louder during hook (no voiceover) */}
      <Sequence from={0} durationInFrames={scene1Frames}>
        <Audio
          src={staticFile("audio/instagram-ads/ad-example/background.mp3")}
          volume={0.4}
          startFrom={0}
        />
      </Sequence>

      {/* Music quieter during voiceover scenes */}
      <Sequence from={scene1Frames} durationInFrames={scene2Frames + scene3Frames}>
        <Audio
          src={staticFile("audio/instagram-ads/ad-example/background.mp3")}
          volume={0.15}
          startFrom={Math.round(scene1Frames / fps * 1000)}  // Continue from music position
        />
      </Sequence>

      {/* Music louder for CTA */}
      <Sequence from={scene4Start} durationInFrames={scene4Frames}>
        <Audio
          src={staticFile("audio/instagram-ads/ad-example/background.mp3")}
          volume={0.3}
          startFrom={Math.round(scene4Start / fps * 1000)}
        />
      </Sequence>

      {/* Voiceover */}
      <Audio src={staticFile("audio/instagram-ads/ad-example/ad-example-combined.mp3")} />
    </AbsoluteFill>
  );
};
```

---

## Workflow for Instagram Ads

### Complete Audio Workflow

```bash
# 1. Generate background music first
python3 tools/suno.py \
  --prompt "Professional, trustworthy ambient music. Starts subtle, builds slightly, fades at end. 20 seconds." \
  --tags "ambient, professional, corporate" \
  --instrumental \
  --output public/audio/instagram-ads/ad-new/background.mp3

# 2. Generate voiceover with timestamps
node tools/generate.js \
  --scenes remotion/instagram-ads/scenes/ad-new-scenes.json \
  --with-timestamps \
  --output-dir public/audio/instagram-ads/ad-new/

# 3. Preview in Remotion Studio
npx remotion studio

# 4. Adjust music if needed (too long, wrong mood, etc.)
python3 tools/suno.py \
  --prompt "Shorter version, 15 seconds, same professional ambient style" \
  --tags "ambient, professional" \
  --instrumental \
  --output public/audio/instagram-ads/ad-new/background.mp3

# 5. Render final video
npx remotion render AdNew out/ad-new.mp4 --codec=h264 --crf=18
```

---

## Music Length Guidelines

| Video Duration | Music Duration | Notes |
|----------------|----------------|-------|
| 15 seconds | 18-20 seconds | Extra for fade out |
| 30 seconds | 33-35 seconds | Extra for transitions |
| 60 seconds | 65-70 seconds | Buffer for editing |

**Tip**: Always generate music slightly longer than your video. You can trim or fade out in Remotion.

---

## Volume Guidelines

| Scenario | Music Volume | Voiceover Volume |
|----------|--------------|------------------|
| No voiceover | 0.35-0.50 | N/A |
| With voiceover | 0.10-0.20 | 1.0 |
| Dramatic moment | 0.30-0.40 | 0.8-1.0 |
| CTA (quiet music) | 0.15-0.25 | 1.0 |

---

## Output Format

Generated files are saved as MP3. For optimal Remotion compatibility:

```bash
# Convert to WAV (uncompressed, better quality)
ffmpeg -i background.mp3 -acodec pcm_s16le background.wav

# Convert to AAC for Instagram (if needed)
ffmpeg -i background.mp3 -c:a aac -b:a 192k background.m4a
```

---

## Cost & Credits

Suno uses a credit-based system:

| Plan | Credits/Month | Approx Songs |
|------|---------------|--------------|
| Free | ~50/day | ~10 |
| Pro | 2,500 | ~500 |
| Premier | 10,000 | ~2,000 |

Each generation uses ~5 credits for a single song (2 variations are generated by default).

---

## Troubleshooting

### "Authorization failed"
Your token has expired. Get a new one from Suno DevTools (see Prerequisites).

### "Rate limited"
Wait a few minutes or check your remaining credits at suno.com.

### "Generation timed out"
Increase `--wait-timeout` or try a simpler prompt.

### Music doesn't match video length
1. Specify exact duration in prompt: "30 seconds exactly"
2. Generate slightly longer and trim
3. Use Remotion's `startFrom` and `endAt` props

### Music too loud/quiet
Adjust `volume` prop in Remotion. Start with 0.2 for background music with voiceover.

### ElevenLabs: "bad_prompt" error
Your prompt references a specific artist or copyrighted content. The error response includes a `prompt_suggestion` field with an alternative prompt you can use directly. Example:

```json
{
  "detail": {
    "status": "bad_prompt",
    "message": "Prompt references copyrighted content",
    "prompt_suggestion": "A chill lo-fi beat with jazzy piano and vinyl crackle"
  }
}
```

### ElevenLabs: "bad_composition_plan" error
Your composition plan has structural issues (e.g., invalid durations, conflicting styles). The error response includes a `composition_plan_suggestion` field with a corrected plan you can use directly.

```json
{
  "detail": {
    "status": "bad_composition_plan",
    "message": "Section durations exceed total length",
    "composition_plan_suggestion": { "...corrected plan..." }
  }
}
```

---

## Best Practices

1. **Always use `--instrumental`** for video backgrounds to avoid competing with voiceover
2. **Specify duration** in the prompt for predictable length
3. **Generate 2-3 variations** and pick the best (`--count 3`)
4. **Match mood to content**: dramatic for problems, hopeful for solutions
5. **Keep background music subtle**: 15-25% volume during voiceover
6. **Add fade out** at the end of your video for professional finish
7. **Test on mobile** with headphones to ensure music isn't overpowering
8. **Use ElevenLabs for quick iterations** when you don't need artist-style references (no token expiry)
9. **Use composition plans** for complex multi-section music that needs structural control

## Related Rules

- [voiceover.md](voiceover.md) - ElevenLabs voiceover generation
- [sound-effects.md](sound-effects.md) - Generate transition and ambient SFX
- [captions.md](captions.md) - Animated captions synced to audio
