---
name: remotion-ads
description: Professional video ad creation with Remotion — Instagram Reels (9:16), explainers (16:9), carousels (4:5) — with voiceover, word-level captions, music, and ad copywriting frameworks. Use when the marketer wants video ads, animated social content, or a video built from a URL; pairs with the brand-crawl skill so ads use the brand's measured tokens and video-* components.
---

> Folded from the official skill: [Maartenlouis/remotion-ads]
> (https://github.com/Maartenlouis/remotion-ads), MIT, fetched 2026-08-10.
> scripts/ and references/ vendored verbatim (see references/brand-config-template.md).

# Remotion Ads

Create professional video ads and explainer videos with Remotion, ElevenLabs voiceover, and animated captions.

## Setup

1. Copy `references/brand-config-template.md` → `references/brand-config.md`
2. Fill in brand colors, fonts, voice, caption styling, and content rules
3. Create pronunciation dictionary from `assets/dictionaries/template.pls`

See [references/setup.md](references/setup.md) for dependencies and folder structure.

---

## Supported Formats

| Format | Aspect | Resolution | Duration | Scenes |
|--------|--------|-----------|----------|--------|
| Instagram Reels | 9:16 | 1080×1920 | 15-60s | 4 (Hook→Problem→Solution→CTA) |
| Instagram Reels (Ohneis) | 9:16 | 1080×1920 | 15-45s | Beat-driven (word-level) |
| Website Explainers | 16:9 | 1920×1080 | 60-160s | 6 (Hook→Problem→Context→Solution→Process→CTA) |
| Carousels | 4:5 | 1080×1350 | Static | 5-10 slides |

See [references/formats.md](references/formats.md) for safe zones and crop specs.
See [references/ohneis-style.md](references/ohneis-style.md) for beat-driven cinematic reel template.
See [references/website-videos.md](references/website-videos.md) for 16:9 long-form format.

---

## Workflow

### From scratch

```bash
# 1. Write scene JSON
# 2. Generate voiceover with word timestamps
node scripts/generate.js \
  --scenes scenes.json \
  --with-timestamps \
  --dictionary your-brand \
  --output-dir public/audio/ad-example/

# 3. Create Remotion composition using actualDuration from info.json
# 4. Render
npx remotion render AdExample out/ad-example.mp4 --codec=h264 --crf=18
```

### From a URL (page → video)

```bash
# 1. Extract page data into scene JSON
node scripts/url-to-scenes.js --url https://example.com/page --format reels --output scenes.json
# 2. Review/edit the generated scenes.json
# 3. Continue with voiceover + composition as above
```

See [references/url-to-video.md](references/url-to-video.md) for the full URL-to-video workflow.

---

## Safe Zones (Critical)

### Reels (1080×1920)

```
┌──────────────────────────┐ 0px
│     TOP DANGER (285px)   │
├──────────────────────────┤
│ ←80px  SAFE AREA  120px→ │
│      880×1235px          │
├──────────────────────────┤
│   BOTTOM DANGER (400px)  │
└──────────────────────────┘ 1920px
```

```tsx
const SAFE = { top: 285, bottom: 400, left: 80, right: 120 };
```

### Website Videos (1920×1080)

```tsx
const SAFE = { top: 60, bottom: 60, left: 80, right: 80 };
```

---

## Scene JSON Format

```json
{
  "name": "ad-example",
  "voice": "VoiceName",
  "character": "narrator",
  "dictionary": "your-brand",
  "scenes": [
    { "id": "scene1", "text": "Hook text.", "duration": 3.5, "character": "dramatic" },
    { "id": "scene2", "text": "Problem.", "duration": 4.5 },
    { "id": "scene3", "text": "Solution.", "duration": 4.0, "character": "expert" },
    { "id": "scene4", "text": "CTA.", "duration": 3.0, "character": "calm" }
  ]
}
```

### Voice Character Presets

| Character | Style | Stability | Similarity | Style Param |
|-----------|-------|-----------|------------|-------------|
| `dramatic` | Intense, emotional | 0.3 | 0.8 | 0.7 |
| `narrator` | Professional, smooth | 0.5 | 0.75 | 0.4 |
| `expert` | Authoritative | 0.6 | 0.85 | 0.3 |
| `calm` | Soothing, reassuring | 0.7 | 0.8 | 0.2 |
| `conversational` | Casual, friendly | 0.45 | 0.7 | 0.5 |

---

## Composition Template

```tsx
import { AbsoluteFill, Audio, Series, staticFile } from "remotion";

// Import from your brand-config.md values
const COLORS = { primary: "#000", accent: "#888", dark: "#111", background: "#fff" };

export const AdTemplate: React.FC = () => {
  const { fps } = useVideoConfig();
  // Use actualDuration from info.json, not estimated
  const DURATIONS = { scene1: 3.42, scene2: 4.35, scene3: 4.12, scene4: 3.31 };
  const pad = 5;

  return (
    <AbsoluteFill>
      <Audio src={staticFile("audio/ad-example/ad-example-combined.mp3")} />
      <Series>
        <Series.Sequence durationInFrames={Math.round(DURATIONS.scene1 * fps) + pad}>
          <Scene1Hook />
        </Series.Sequence>
        {/* ... remaining scenes */}
      </Series>
    </AbsoluteFill>
  );
};
```

See [references/components.md](references/components.md) for reusable scene components.
See [references/voiceover.md](references/voiceover.md) for TransitionSeries audio sync.

---

## Reference Files

Load these on demand based on the task:

### Core (read first)

| File | When to read |
|------|-------------|
| [setup.md](references/setup.md) | Project initialization |
| [brand-config-template.md](references/brand-config-template.md) | Configuring brand: colors, fonts, voice, captions, compliance |
| [formats.md](references/formats.md) | Dimension specs, safe zones, crop previews |

### Video Creation

| File | When to read |
|------|-------------|
| [ohneis-style.md](references/ohneis-style.md) | Beat-driven cinematic reel template: mixed-font typography, hard cuts, moody photos |
| [voiceover.md](references/voiceover.md) | ElevenLabs TTS, models, scene JSON, timing sync, dictionaries |
| [captions.md](references/captions.md) | Animated captions: TikTok-style, word-by-word, karaoke |
| [animations.md](references/animations.md) | Spring configs, transitions, animation components |
| [components.md](references/components.md) | Reusable scene template components |
| [html-in-canvas.md](references/html-in-canvas.md) | Render live DOM into a canvas with 2D filters or WebGL2 shaders (vintage, progressive blur, page-tour mockup) |
| [website-videos.md](references/website-videos.md) | 16:9 long-form format, 6-scene structure |
| [url-to-video.md](references/url-to-video.md) | Create videos from existing web pages |

### Audio

| File | When to read |
|------|-------------|
| [sound-effects.md](references/sound-effects.md) | ElevenLabs SFX generation |
| [music.md](references/music.md) | Background music via ElevenLabs or Suno |

### Assets & Static

| File | When to read |
|------|-------------|
| [local-assets.md](references/local-assets.md) | Background images, icons, illustrations |
| [carousels.md](references/carousels.md) | 4:5 carousel design and batch rendering |

### Copywriting

| File | When to read |
|------|-------------|
| [ad-copywriting.md](references/ad-copywriting.md) | Script frameworks, hook formulas, CTA patterns |
| [copy-frameworks.md](references/copy-frameworks.md) | Headline templates, section formulas |
| [natural-transitions.md](references/natural-transitions.md) | Human-sounding transitions, AI-tell avoidance |

### Distribution

| File | When to read |
|------|-------------|
| [paid-ads.md](references/paid-ads.md) | Meta campaign strategy, targeting, budgets |
| [social-content.md](references/social-content.md) | Content calendar, repurposing framework |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/generate.js` | ElevenLabs voiceover with dictionaries, request stitching (note: `--with-timestamps` flag is currently a no-op) |
| `scripts/gemini-tts.mjs` | Gemini TTS — single-request generate + silence split with text-proportion boundary picker |
| `scripts/suno-direct.ts` | Suno background music generation |
| `scripts/url-to-scenes.js` | Extract page content into scene JSON |

---

## Pre-Upload Checklist

### Reels
- [ ] 1080×1920, H.264, 30fps
- [ ] All text within safe zones
- [ ] No content in top 285px or bottom 400px
- [ ] Font sizes ≥ 48px
- [ ] Voiceover synced, captions timed
- [ ] ~15s total duration

### Website Videos
- [ ] 1920×1080, H.264, 30fps
- [ ] Font sizes ≥ 36px
- [ ] 60-160s duration
- [ ] 6-scene structure with appropriate voice characters

### Carousels
- [ ] 1080×1350, PNG
- [ ] 80px padding from edges
- [ ] 5-10 slides with swipe indicators

## House method (montology)

- **The brand config is MEASURED, not asked for.** Fill
  references/brand-config-template.md from the brand's library:
  `brands/<brand>/tokens.ts` has the counted palette and fonts;
  `manifest.json` has the logo and source URL. Never ask the marketer for
  hex codes the audit already measured.
- **Shop the component library first.** `video-title`, `video-lower-third`
  and `video-endcard` components in `brands/<brand>/components/` drop into
  Remotion compositions as ordinary React — tokens and all. Build missing
  ones there (then `monty brand register` + `brand lint`), so the ad
  and the landing page stay one design system.
- **Copy obeys marketing-science**: any claim with a number in the ad comes
  from a tool this session, and rates beat raws in on-screen stats.
