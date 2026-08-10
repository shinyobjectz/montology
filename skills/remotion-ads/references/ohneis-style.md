---
title: Ohneis Style Template
description: Beat-driven cinematic reel style inspired by @ohneis652 — mixed-font typography, hard cuts, moody photos alternating with text-only frames
section: video-creation
priority: high
tags: [ohneis, beat-driven, typography, cinematic, reels, style-template]
---

# Ohneis Style Template

A beat-driven composition style inspired by [Andries Ohneisser (@ohneis652)](https://instagram.com/ohneis652). Moody cinematic photos alternate with text-only frames using designed mixed-font typography and hard cuts.

**When to use**: Brand reels, product promos, editorial content, any short-form video (15-45s) where the voiceover drives the pacing and the typography IS the design.

---

## Core Principles

1. **Typography is the hero** — not the images. The text design carries the brand.
2. **Hard cuts only** — no transitions, no crossfades. Instant frame switches.
3. **Beat-driven** — every frame is mapped to a voiceover word timestamp. The audio dictates the rhythm.
4. **Restraint** — limited palette, minimal UI, let the images carry all the color.
5. **Alternation** — never 3+ of the same frame type in a row. Mix constantly.

---

## Architecture: The Beat Timeline

The entire composition is driven by a single `BEAT_TIMELINE` array. Each entry maps a voiceover timestamp to a frame type, caption, and visual source.

```tsx
interface CaptionWord {
  text: string;
  bold?: boolean; // true = serif bold italic
}

interface Beat {
  caption: CaptionWord[];
  type: "photo" | "text" | "video" | "collage" | "padded";
  imageSrc?: string;
  videoSrc?: string;
  collageSrcs?: CollageImage[];
  bg?: string;           // hex color for text frames
  startMs: number;
  endMs: number;
  showBrand?: boolean;   // show brand mark on text frames
  captionSize?: number;  // override auto-sizing
}
```

The main composition finds the current beat and renders:

```tsx
const frame = useCurrentFrame();
const { fps } = useVideoConfig();
const currentMs = (frame / fps) * 1000;

const beat = BEAT_TIMELINE.find(
  (b) => currentMs >= b.startMs && currentMs < b.endMs
);
```

This is the entire rendering logic. No `Series`, no `Sequence`, no scene components. One array, one lookup.

---

## Typography System

### Option A: Mixed-Font Inline (Original Ohneis)

Single-line sentences with two fonts inline on the same line.

| Element | Font | Weight | Style |
|---------|------|--------|-------|
| Regular words | Inter | 400 | normal |
| Bold/keyword | Instrument Serif | 700 | italic |

```tsx
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadInstrumentSerif } from "@remotion/google-fonts/InstrumentSerif";

const { fontFamily: sansFont } = loadInter();
const { fontFamily: serifFont } = loadInstrumentSerif();
```

**Rules:**
- Bold words are ~15% larger: `boldSize = size * 1.15`
- Bold words use primary text color, regular words use muted accent color
- Everything lowercase
- On photo/video frames: heavy text shadow for readability
- On text-only frames: no shadow

```tsx
// Caption data
caption: [
  { text: "you feed it " },
  { text: "context.", bold: true },
]

// Rendering
{beat.caption.map((word, i) => (
  <span
    key={i}
    style={{
      fontFamily: word.bold ? serifFont : sansFont,
      fontWeight: word.bold ? 700 : 400,
      fontStyle: word.bold ? "italic" : "normal",
      fontSize: word.bold ? size * 1.15 : size,
      color: word.bold ? TEXT_COLOR : ACCENT_COLOR,
    }}
  >
    {word.text}
  </span>
))}
```

### Option B: Two-Tier Typography (Adapted)

Small connector text above + large bold keyword below. Better for fast-paced content with short beats.

| Element | Size | Weight |
|---------|------|--------|
| Small text | ~28px | 400, regular |
| Big text | 68-96px | 800, extrabold |

```tsx
// Beat data
{ smallText: "you feed it", bigText: "context", ... }

// Auto-sizing
const bigSize = bigText.length > 11 ? 68 : bigText.length > 8 ? 78 : 96;

// Override for impact words
{ smallText: "", bigText: "legal", bigSize: 120 }
```

Both options: everything lowercase, tight letter-spacing (-3px on big text, -0.5px on small text).

---

## 5 Frame Types

| Type | Description | When to Use |
|------|-------------|-------------|
| **photo** | Cinematic image fills frame (or padded with blurred bg) | Emotional/dramatic beats |
| **text** | Solid color background | Connector words, pauses, emphasis |
| **padded** | Image with brand-color border (8% padding, 24px radius) | Key visual moments. The border IS the brand. |
| **video** | Animated clip, fullbleed or padded | 3-5 per reel max |
| **collage** | 3 images stacked vertically, text overlaid | Context/overview beats |

### Photo Frame

```tsx
const PhotoFrame: React.FC<{
  src: string;
  progress: number;
  zoomDir: number;
  zoomSpeed: "slow" | "normal" | "fast";
}> = ({ src, progress, zoomDir, zoomSpeed }) => {
  const range = ZOOM_RANGES[zoomSpeed];
  const from = zoomDir > 0 ? range.from : range.to;
  const to = zoomDir > 0 ? range.to : range.from;
  const scale = interpolate(progress, [0, 1], [from, to]);

  return (
    <AbsoluteFill>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
        }}
      />
    </AbsoluteFill>
  );
};
```

### Padded Frame (Brand Border)

The brand-color border around photos is the most distinctive visual element. Use frequently (4-5 per reel).

```tsx
const PaddedPhotoFrame: React.FC<{
  src: string;
  bgColor: string;
  progress: number;
  zoomDir: number;
  zoomSpeed: "slow" | "normal" | "fast";
}> = ({ src, bgColor, progress, zoomDir, zoomSpeed }) => {
  const padX = Math.round(1080 * 0.08); // 86px
  const padY = Math.round(1920 * 0.08); // 154px

  return (
    <AbsoluteFill style={{ backgroundColor: bgColor }}>
      <div style={{
        position: "absolute",
        top: padY, left: padX, right: padX, bottom: padY,
        borderRadius: 24,
        overflow: "hidden",
      }}>
        <Img src={staticFile(src)} style={{
          width: "100%", height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
        }} />
      </div>
    </AbsoluteFill>
  );
};
```

### Collage Frame

3 images stacked vertically with text on top via dark gradient.

**Critical rules (learned through 10+ iterations):**
1. **No rotation** — images stack straight
2. **No border-radius** — sharp rectangular edges
3. **Varying widths** — each image has different `widthPct` (e.g., 65%, 50%, 55%)
4. **Overlap** — negative margin between images
5. **Text ON TOP** — captions render above images with gradient backdrop
6. **Staggered entry** — each image slides in with delay

```tsx
// Gradient stripe behind text on collage frames
<div style={{
  position: "absolute",
  top: 0, left: 0, right: 0, height: 240,
  background: "linear-gradient(to bottom, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.6) 70%, transparent 100%)",
}} />
```

### Vignette (Photo/Video Frames Only)

```tsx
const Vignette: React.FC = () => (
  <AbsoluteFill style={{
    background: "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.5) 100%)",
    pointerEvents: "none",
  }} />
);
```

---

## Animation System

### Ken Burns Presets

```tsx
const ZOOM_RANGES = {
  slow: { from: 1.0, to: 1.03 },   // barely noticeable
  normal: { from: 1.02, to: 1.06 }, // standard
  fast: { from: 1.0, to: 1.10 },    // noticeable push-in
} as const;
```

Alternate `zoomDir`: `1` (zoom in) vs `-1` (zoom out).

### Caption Animation Variants

Each beat has an `animType` for visual variety:

| AnimType | Effect | Best For |
|----------|--------|----------|
| `scaleUp` | Scale 0.92 to 1.0 + fade | Default, smooth entry |
| `slideUp` | Slides up 80px + fade | Photo/video reveals |
| `slideDown` | Slides down 80px + fade | Emphasis changes |
| `slideLeft` | Slides in from right 120px | Fast transitions |
| `slideRight` | Slides in from left 120px | Fast transitions |
| `popIn` | Spring bounce (0.5 to 1.0) | Impact words |

**Rules:**
- Never use same animation type on consecutive beats
- `popIn` for high-impact single words
- `slideUp`/`slideDown` for photo/video reveals
- `scaleUp` for text frames with logo
- Small text staggers 2-3 frames after big text

```tsx
case "popIn": {
  const spr = spring({
    frame: localFrame, fps,
    config: { damping: 8, stiffness: 150, mass: 0.6 },
  });
  const scale = interpolate(spr, [0, 1], [0.5, 1.0]);
  containerStyle = {
    transform: `scale(${scale})`,
    opacity: interpolate(spr, [0, 0.3], [0, 1], { extrapolateRight: "clamp" }),
  };
  break;
}
```

### Entry Animation

All frame content: 4-frame (~130ms) fade + scale 0.92 to 1.0.

```tsx
const entryFrames = frame - beatStartFrame;
const entryProgress = interpolate(entryFrames, [0, 4], [0, 1], {
  extrapolateRight: "clamp",
});
```

### Rhythm Pattern

```
text(brand) → photo → text(brand) → text → photo → padded → text(brand) → video → text → padded → text(brand) → ...
```

---

## Audio: Multi-Track

### Critical: Use @remotion/media

```tsx
// CORRECT — properly mixes multiple audio tracks
import { Audio } from "@remotion/media";

// WRONG — does NOT reliably mix multiple tracks
import { Audio } from "remotion";
```

### Background Music Pattern

Use the full music file with `trimBefore` to set start offset. Do NOT pre-cut with ffmpeg.

```tsx
<Audio
  src={staticFile("audio/your-music.mp3")}
  volume={(f) => {
    const fadeStart = Math.round(durationSec * fps) - Math.round(1.5 * fps);
    const fadeEnd = Math.round(durationSec * fps);
    if (f >= fadeStart) {
      return interpolate(f, [fadeStart, fadeEnd], [MUSIC_VOLUME, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
    }
    return MUSIC_VOLUME;
  }}
  trimBefore={Math.round(startOffsetSec * fps)}
/>
```

### Voiceover Speed Correction

Some ElevenLabs voices produce audio slower than expected. Fix:

```tsx
// Speed up with ffmpeg
// ffmpeg -i original.mp3 -filter:a "atempo=1.2" -y sped-up.mp3

// Scale all timestamps in composition
const SPEED = 1.2;
const ms = (t: number) => Math.round(t / SPEED);

// Use in beat timeline
{ startMs: ms(2847), endMs: ms(4485), ... }
```

### ffmpeg Pre-Mix Fallback

If dual `<Audio>` tracks don't work, pre-mix:

```bash
ffmpeg -i voiceover.mp3 -i music.mp3 \
  -filter_complex "[1:a]volume=0.20[music];[0:a][music]amix=inputs=2:duration=longest:dropout_transition=3[out]" \
  -map "[out]" -y final-mix.mp3
```

---

## Image Sourcing

Images for the ohneis style should be dark, moody, cinematic — film grain, shallow DoF, warm tungsten/amber tones, silhouettes.

### Options

| Source | Cost | Quality | Notes |
|--------|------|---------|-------|
| **cosmos.so** | Free | Excellent | Curated photography. Best for consistent aesthetic. |
| **Grok Imagine** | Free (via Vercel AI Gateway) | Good | `xai/grok-imagine-image` model. Free until Feb 25, 2025. 9:16 portrait support. |
| **Gemini Flash Image** | ~$0.04/image | Good | `gemini-2.5-flash-image`. Use style reference image for consistency. |
| **Your own photos** | Free | Variable | Best for authenticity. Mix with AI-generated. |

### Generation Prompt Template (Grok/Gemini)

```
Cinematic urban street photography, portrait orientation 9:16 vertical.
Dramatic backlighting with warm amber tungsten color tones.
Deep rich shadows, silhouettes against light sources.
Shallow depth of field, creamy bokeh.
Subtle film grain texture, dark moody atmospheric.
Editorial fashion photography feel.
No text, no watermarks, no logos, no UI elements, no overlays.

Subject: [YOUR SCENE DESCRIPTION]
```

### Image Deduplication

Never show the same image twice. Track all usage:

```tsx
const IMG = {
  hero: "images/your-reel/hero.jpg",
  detail: "images/your-reel/detail.jpg",
  // ... each image used max once
} as const;
```

---

## Palette Guidance

The style works best with extremely limited palettes. Examples:

### Dark Minimal (4 shades)

```tsx
const BG = {
  charcoal: "#0a0a0a",
  dark: "#111111",
  darkGrey: "#1a1a1a",
  medGrey: "#2a2a2a",
} as const;

const TEXT_COLOR = "#e8e6e1";
const ACCENT_COLOR = "#c8c4bb";
```

### Brand-Colored (Dark + Accent)

```tsx
const BG = {
  charcoal: "#1a1a1a",
  brand: "#ff511c",      // your primary brand color
  brandDark: "#546d55",  // your secondary
  sand: "#f2eee2",       // light variant
} as const;
```

**Rule**: The images carry all the visual richness. The palette just provides structure.

---

## Complete Composition Template

```tsx
import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  AbsoluteFill,
  staticFile,
  Img,
  OffthreadVideo,
  interpolate,
  spring,
} from "remotion";
import { Audio } from "@remotion/media"; // CRITICAL: not from "remotion"
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadSerif } from "@remotion/google-fonts/InstrumentSerif";

const { fontFamily: sansFont } = loadInter();
const { fontFamily: serifFont } = loadSerif();

// ── Your Brand ──
const BG = { /* your palette */ } as const;
const TEXT_COLOR = "#e8e6e1";
const ACCENT_COLOR = "#c8c4bb";
const MUSIC_VOLUME = 0.28;

// ── Speed correction (if needed) ──
const SPEED = 1.0; // adjust if voiceover too slow
const ms = (t: number) => Math.round(t / SPEED);

// ── Beat Timeline ──
const BEAT_TIMELINE: Beat[] = [
  {
    caption: [{ text: "your hook " }, { text: "word.", bold: true }],
    type: "text",
    bg: "charcoal",
    startMs: ms(0),
    endMs: ms(1200),
    showBrand: true,
  },
  {
    caption: [{ text: "next " }, { text: "beat.", bold: true }],
    type: "photo",
    imageSrc: "images/your-reel/photo1.jpg",
    startMs: ms(1200),
    endMs: ms(2800),
  },
  // ... more beats, mapped to voiceover word timestamps
];

// ── Main Composition ──
export const YourReel: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentMs = (frame / fps) * 1000;

  const beat = BEAT_TIMELINE.find(
    (b) => currentMs >= b.startMs && currentMs < b.endMs
  );

  if (!beat) return <AbsoluteFill style={{ backgroundColor: "#000" }} />;

  const duration = beat.endMs - beat.startMs;
  const progress = (currentMs - beat.startMs) / duration;
  const beatStartFrame = Math.round((beat.startMs / 1000) * fps);
  const entryProgress = interpolate(frame - beatStartFrame, [0, 4], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Voiceover */}
      <Audio
        src={staticFile("audio/your-reel/voiceover.mp3")}
        volume={(f) => {
          const fadeStart = Math.round(totalDurationSec * fps) - 45;
          const fadeEnd = Math.round(totalDurationSec * fps);
          if (f >= fadeStart) {
            return interpolate(f, [fadeStart, fadeEnd], [1, 0], {
              extrapolateLeft: "clamp", extrapolateRight: "clamp",
            });
          }
          return 1;
        }}
      />

      {/* Background music */}
      <Audio
        src={staticFile("audio/your-reel/music.mp3")}
        volume={MUSIC_VOLUME}
        trimBefore={Math.round(musicStartSec * fps)}
      />

      {/* Frame layer */}
      {beat.type === "photo" && <PhotoFrame ... />}
      {beat.type === "text" && <TextOnlyFrame ... />}
      {beat.type === "video" && <VideoFrame ... />}
      {beat.type === "padded" && <PaddedPhotoFrame ... />}

      {/* Vignette on photo/video */}
      {(beat.type === "photo" || beat.type === "video") && <Vignette />}

      {/* Typography overlay */}
      <MixedFontCaption caption={beat.caption} ... />
    </AbsoluteFill>
  );
};

export const YOUR_REEL_CONFIG = {
  id: "YourReel",
  fps: 30,
  width: 1080,
  height: 1920,
  durationInFrames: Math.ceil(totalDurationSec * 30),
};
```

---

## Known Issues & Learnings

### What Works

1. **Static photos with hard cuts** — at 0.5-2s per beat, static images feel intentional and cinematic
2. **Mixed-font inline captions** — the serif/sans contrast is instantly recognizable
3. **Brand-colored padded borders** — most distinctive visual element, use often
4. **`@remotion/media` for Audio** — the only reliable way to mix voiceover + music
5. **Full music file + `trimBefore`** — simpler and more reliable than pre-cutting
6. **Animation variety** — alternating animation types prevents visual monotony

### What Doesn't Work

1. **AI video generation (Grok Imagine Video)** — produces skewed, low-res (480x848), character-inconsistent results. Static photos are better.
2. **Ken Burns on dark moody images** — too smooth, breaks the raw aesthetic. Use sparingly or skip.
3. **Two-tier text layout** for the original ohneis style — the inline mixed-font single line IS the style. Two-tier is an adaptation, not the original.
4. **Transitions between beats** — crossfades, wipes, etc. all break the rhythm. Hard cuts only.
5. **Busy palettes** — more than 4-5 background colors dilutes the impact
6. **AI-looking images** — Grok Aurora produces too-smooth results. Gemini with a style reference image or curated photography (cosmos.so) is better.
7. **Text in generated images** — AI always botches text. Use `no text, no watermarks` in prompts.

### Audio Gotchas

8. **`Audio` from `remotion` silently drops tracks** — always use `@remotion/media`
9. **Some ElevenLabs voices run slow with `eleven_v3`** — speed up with ffmpeg atempo, scale timestamps with `ms()` helper
10. **Voiceover trimming needs a short fade** — 0.5s fade at the very end, not aggressive fading during content
11. **Extend video 1-1.5s beyond voiceover** — gives music a graceful fade-out window

---

## Workflow Summary

```
1. Write voiceover script (scenes.json)
2. Generate voiceover with word timestamps (ElevenLabs)
3. Source images (cosmos.so / Gemini / Grok / own photos)
4. Map word timestamps → BEAT_TIMELINE array
5. Build composition (frame types + typography + audio)
6. Render: npx remotion render YourReel out/reel.mp4 --codec=h264 --crf=18
```
