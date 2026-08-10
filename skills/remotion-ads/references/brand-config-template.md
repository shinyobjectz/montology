# Brand Configuration Template

Copy this file to `brand-config.md` and fill in your brand values. This is the single source of truth for all visual, audio, and content decisions across video formats.

---

## 1. Colors

```tsx
const COLORS = {
  // Primary brand colors
  primary: "#000000",        // TODO: Main brand color
  primaryLight: "#333333",   // TODO: Lighter variant
  primaryDark: "#111111",    // TODO: Darker variant (dark scene backgrounds)
  darkest: "#0a0a0a",       // TODO: Darkest shade (hook/problem backgrounds)

  // Accent
  accent: "#888888",         // TODO: Highlight color (captions, keywords, badges)
  accentAlt: "#aaaaaa",     // TODO: Alternative accent (warm topics, alt highlights)

  // Neutrals
  background: "#ffffff",     // Light backgrounds, CTA scenes
  foreground: "#1a1a1a",     // Primary text color
  muted: "#888888",          // Secondary text

  // Special
  orange: "#f97316",         // Star ratings ONLY
};
```

### Gradient Presets

```tsx
const GRADIENTS = {
  hook:     [COLORS.darkest, "#midtone", COLORS.darkest],     // TODO: Scene 1
  problem:  [COLORS.darkest, "#midtone2", "#midtone3"],       // TODO: Scene 2
  solution: [COLORS.primary, "#midtone4", COLORS.primaryDark], // TODO: Scene 3+
};
```

### Color Rules

| Color | Use For | Never For |
|-------|---------|-----------|
| `accent` | Highlighted caption words, badges, checkmarks | Large backgrounds |
| `accentAlt` | Warm topic highlights, body text on dark | — |
| `darkest` | Scene 1-2 backgrounds | Light mode |
| `primary` | Scene 3+ backgrounds, positive tone | Text on light backgrounds |
| `orange` | Star ratings ONLY | Anything else |

---

## 2. Typography

```tsx
// TODO: Replace with your fonts
import { loadFont } from "@remotion/google-fonts/YourHeadingFont";
import { loadFont as loadBodyFont } from "@remotion/google-fonts/YourBodyFont";
```

### Font Sizes

| Element | Reels (9:16) | Website (16:9) | Weight |
|---------|-------------|----------------|--------|
| Hero headline | 64-80px | 72-80px | 700 |
| Section headline | 52-64px | 56-64px | 600-700 |
| Body text | 44-52px | 42-48px | 500 |
| Bullets | 40-48px | 40-44px | 500 |
| CTA button | 48-56px | — | 600 |
| **Minimum** | **48px** | **36px** | — |

---

## 3. Caption Styling

### Instagram Reels

```tsx
const CAPTION_REELS = {
  fontSize: 72,              // TODO: Adjust
  fontWeight: 700,
  position: { bottom: 450 }, // Above Instagram UI
  maxWidth: 900,
  lineHeight: 1.1,
  highlightColor: COLORS.accent,
  defaultColor: "#ffffff",
  // Scale animation curve (pop → hold → settle)
  scale: {
    keyframes: [0, 0.15, 0.5, 1],
    values:    [1.0, 1.15, 1.1, 1.0],
  },
  opacity: {
    keyframes: [0, 0.1, 0.9, 1],
    values:    [0.7, 1, 1, 0.9],
  },
  // Glow for highlighted words
  glowIntensity: 20,        // px blur for highlight glow
  textShadow: "0 4px 20px rgba(0,0,0,0.8), 0 2px 4px rgba(0,0,0,0.5)",
};
```

### Website Videos

```tsx
const CAPTION_WEBSITE = {
  fontSize: 48,              // TODO: Adjust
  fontWeight: 700,
  position: { bottom: 100 },
  maxWidth: 1600,
  lineHeight: 1.2,
  highlightColor: COLORS.accent,
  defaultColor: "#ffffff",
  // Subtler scale (less dramatic for educational content)
  scale: {
    keyframes: [0, 0.15, 0.5, 1],
    values:    [1.0, 1.1, 1.05, 1.0],
  },
  opacity: {
    keyframes: [0, 0.1, 0.9, 1],
    values:    [0.7, 1, 1, 0.9],
  },
  glowIntensity: 15,
  textShadow: "0 4px 20px rgba(0,0,0,0.8), 0 2px 4px rgba(0,0,0,0.5)",
};
```

### Highlight Word Strategy

Choose 2-4 words per scene to highlight:

1. **Domain keywords**: Core terms the viewer should remember
2. **Emotional triggers**: Words that create urgency or empathy
3. **Numbers/deadlines**: Quantifiable facts that stick
4. **Action words**: What the viewer should do
5. **Brand name**: Always highlight

---

## 4. Voice Configuration

```
Voice name/ID:    ___          # TODO: ElevenLabs voice name or ID
Default model:    eleven_multilingual_v2
Final render:     eleven_v3    # Use for production renders
Preview model:    eleven_flash_v2_5
Language:         ___          # TODO: e.g., "de" for German
```

### Scene-to-Character Mapping

**Reels (4 scenes):**

| Scene | Character | Why |
|-------|-----------|-----|
| Hook | `dramatic` | Emotional impact |
| Problem | `narrator` | Storytelling |
| Solution | `expert` or `narrator` | Authority |
| CTA | `calm` | Reassurance |

**Website Videos (6 scenes):**

| Scene | Character | Why |
|-------|-----------|-----|
| Hook | `dramatic` | Emotional opening |
| Problem | `narrator` | Detail the issue |
| Context | `expert` | Legal/technical authority |
| Solution | `expert` | Explain options |
| Process | `narrator` | Step-by-step clarity |
| CTA | `calm` | Trust and reassurance |

### Pronunciation Dictionary

```xml
<!-- assets/dictionaries/your-brand.pls -->
<lexeme>
  <grapheme>YourBrand</grapheme>
  <alias>Phonetic Spelling</alias>
</lexeme>
```

Captions show the written form; TTS receives the phonetic form.

### Speaking Pace

| Format | Target WPS | Style |
|--------|-----------|-------|
| Reels | ~3.5 wps | Fast, urgent |
| Website | ~2.8 wps | Moderate, educational |

### Timing Validation

- Leading silence: < 200ms
- Trailing silence: < 500ms
- Speaking rate: 2-4.5 wps (reject if outside range)

---

## 5. Backgrounds

### DriftingBackground (animated gradient)

```tsx
<DriftingBackground colors={GRADIENTS.hook} angle={180} grainOpacity={0.08} />
```

- Gradient angle drifts ±5° with sine wave
- Position shifts ±20px for subtle motion
- Grain overlay at 5-10% opacity

### Background by Scene

| Scene | Type | Colors |
|-------|------|--------|
| Hook | DriftingBackground | `GRADIENTS.hook` |
| Problem | DriftingBackground | `GRADIENTS.problem` |
| Solution | DriftingBackground | `GRADIENTS.solution` |
| CTA | Static image | `grainy-background.png` or brand bg |

---

## 6. Animation

### Spring Configs

```tsx
const SPRING = {
  smooth: { damping: 200 },              // Professional, no bounce
  snappy: { damping: 150, stiffness: 200 }, // Punchy entrances
  heavy:  { damping: 250, mass: 1.5 },   // Slow, weighty reveals
};
```

### Duration Presets (frames at 30fps)

| Name | Frames | Seconds |
|------|--------|---------|
| fast | 15 | 0.5s |
| normal | 30 | 1.0s |
| slow | 45 | 1.5s |

### Scene Padding

- Reels: 5 frames between scenes
- Website: 5 frames + 15-20 frame crossfade

---

## 7. Accent Elements

### PulseGlow

```tsx
<PulseGlow color={COLORS.accent} size={300} opacity={0.15} />
```

### Highlighted Text

```tsx
<span style={{ color: COLORS.accent }}>{keyword}</span>
```

### Info/Warning Boxes

```tsx
backgroundColor: COLORS.accent + "25"  // 15% opacity
border: `2px solid ${COLORS.accent}60`  // 37% opacity
```

Never use red/orange for info boxes — use brand accent colors.

---

## 8. Icons

### Style

Describe your icon style for AI generation:

```
TODO: e.g., "3D clay miniature model, soft matte ceramic finish,
beige/cream pedestal base, [brand color] accents, soft lighting,
clean white background"
```

### Sizes

| Context | Size |
|---------|------|
| Hero/Hook | 180-220px |
| Bullet list | 55-70px |
| Solution scene | 160-180px |
| CTA scene | 140px |

---

## 9. Logo

```tsx
const LOGO_PATH = "your-logo.png";  // TODO: In public/ folder
```

| Context | Size |
|---------|------|
| CTA prominent | 300-400px height |
| Corner badge | 80-120px |
| Inline | 48-64px |

---

## 10. Content Compliance

### Forbidden Terms

| Forbidden | Use Instead |
|-----------|-------------|
| TODO | TODO |

### Content Rules

- TODO: List industry-specific compliance rules
- TODO: List hedging language requirements
- TODO: List required disclaimers

---

## 11. Render Commands

### Reels

```bash
npx remotion render Ad{Topic} public/videos/ad-{topic}.mp4 --codec=h264 --crf=18
npx remotion still Ad{Topic} public/videos/ad-{topic}-thumb.png --frame=30
```

### Website Videos

```bash
npx remotion render LongForm{Topic} public/videos/lf-{topic}.mp4 --codec=h264 --crf=18
npx remotion still LongForm{Topic} public/videos/lf-{topic}-thumb.png --frame=30
```

---

## Checklist

Before creating any video, verify:

- [ ] Colors filled in (no `#000000` placeholders)
- [ ] Fonts configured
- [ ] Voice name/ID set
- [ ] Pronunciation dictionary created
- [ ] Caption highlight color matches accent
- [ ] Content compliance terms filled in
- [ ] Logo path set
- [ ] Icon style described
