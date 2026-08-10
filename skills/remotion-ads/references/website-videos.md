# Website Explainer Videos (16:9)

Educational videos for website embedding. Longer duration, deeper content, authoritative tone.

## Specifications

| Property | Value |
|----------|-------|
| Resolution | 1920×1080 |
| Aspect ratio | 16:9 |
| FPS | 30 |
| Codec | H.264 + AAC |
| Duration | 60-160 seconds |
| Scenes | 6 |

## Safe Zones

```tsx
const SAFE = { top: 60, bottom: 60, left: 80, right: 80 };
// Usable area: 1760 × 960px
```

No Instagram UI overlays — safe zones are minimal padding.

---

## 6-Scene Structure

| Scene | Name | Duration | Character | Purpose |
|-------|------|----------|-----------|---------|
| 1 | Hook | 5-8s | `dramatic` | Emotional opening, problem statement |
| 2 | Problem | 10-15s | `narrator` | Deep dive into the issue |
| 3 | Context | 15-20s | `expert` | Legal/technical background, statistics |
| 4 | Solution | 15-20s | `expert` | Options and rights explained |
| 5 | Process | 10-15s | `narrator` | Step-by-step what to do |
| 6 | CTA | 5-8s | `calm` | Contact, trust signals, credentials |

### Scene JSON (6-scene format)

```json
{
  "name": "lf-example",
  "format": "longform",
  "voice": "VoiceName",
  "dictionary": "your-brand",
  "scenes": [
    { "id": "scene1", "name": "hook", "text": "...", "duration": 7, "character": "dramatic" },
    { "id": "scene2", "name": "problem", "text": "...", "duration": 12, "character": "narrator" },
    { "id": "scene3", "name": "context", "text": "...", "duration": 18, "character": "expert" },
    { "id": "scene4", "name": "solution", "text": "...", "duration": 18, "character": "expert" },
    { "id": "scene5", "name": "process", "text": "...", "duration": 12, "character": "narrator" },
    { "id": "scene6", "name": "cta", "text": "...", "duration": 6, "character": "calm" }
  ],
  "metadata": {
    "totalWords": 200,
    "speakingRate": 2.8,
    "topics": ["topic1", "topic2"]
  }
}
```

---

## Differences from Reels

| Aspect | Reels (9:16) | Website (16:9) |
|--------|-------------|----------------|
| Scenes | 4 | 6 |
| Duration | 15-20s | 60-160s |
| Tone | Urgent, emotional | Educational, authoritative |
| Font min | 48px | 36px |
| Caption size | 72px | 48px |
| Caption bottom | 450px | 100px |
| Caption scale | 1.0→1.15→1.1→1.0 | 1.0→1.1→1.05→1.0 |
| Spring damping | 150 (snappy) | 200 (smooth) |
| Speaking pace | ~3.5 wps | ~2.8 wps |
| Content depth | Emotional hooks | Legal citations, statistics |

---

## Background by Scene

| Scene | Gradient | Mood |
|-------|----------|------|
| Hook | `GRADIENTS.hook` | Dark, dramatic |
| Problem | `GRADIENTS.problem` | Darker, serious |
| Context | Mid-tone blend | Transitional |
| Solution | `GRADIENTS.solution` | Positive, brand color |
| Process | Light variant of solution | Actionable |
| CTA | `grainy-background.png` image | Trust, premium |

---

## Shared Components

Website videos use shared components from a base file (e.g., `LongFormBase.tsx`):

| Component | Purpose |
|-----------|---------|
| `LongFormSafeContent` | Safe area wrapper |
| `DriftingBackground` | Animated gradient + grain |
| `FloatingElement` | Spring entrance + sine float |
| `PulseGlow` | Breathing glow behind icons |
| `FadeInText` | Slide + fade entrance |
| `ScaleBounce` | Scale 0→1 spring entrance |
| `ClayIllustration` | Icon with contain fit |
| `LongFormCaption` | Word-by-word captions |
| `SectionHeading` | Heading with keyword highlight |
| `AnimatedBulletList` | Staggered bullet items |
| `StepIndicator` | Numbered step-by-step |

See [components.md](components.md) for implementation details.

---

## Composition Pattern

```tsx
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";

// Actual durations from info.json
const SCENE_DURATIONS = {
  scene1: 7.13, scene2: 13.19, scene3: 12.85,
  scene4: 10.48, scene5: 10.68, scene6: 3.94,
};

const FPS = 30;
const PAD = 5;

export const LongFormExample: React.FC = () => {
  const s1 = Math.ceil(SCENE_DURATIONS.scene1 * FPS) + PAD;
  const s2 = Math.ceil(SCENE_DURATIONS.scene2 * FPS) + PAD;
  // ... calculate all scene frames

  return (
    <AbsoluteFill>
      <Audio src={staticFile("audio/lf-example/lf-example-combined.mp3")} />
      <Sequence durationInFrames={s1}><Scene1Hook /></Sequence>
      <Sequence from={s1} durationInFrames={s2}><Scene2Problem /></Sequence>
      {/* ... remaining scenes */}
    </AbsoluteFill>
  );
};
```

---

## Content Depth

Website videos include more detail than Reels:

- Legal citations (e.g., "§ 437 BGB")
- Specific timeframes (e.g., "2 Jahre Gewährleistung")
- Statistical data and expert context
- Step-by-step process explanations
- Explain WHY not just WHAT

---

## Render

```bash
npx remotion render LongFormExample public/videos/lf-example.mp4 --codec=h264 --crf=18
npx remotion still LongFormExample public/videos/lf-example-thumb.png --frame=30
```
