---
title: Animated Captions
description: TikTok-style animated captions with word-level timing and highlighting
section: video-creation
priority: medium
tags: [captions, subtitles, animation, timing, tiktok]
---

# Instagram Reels Captions

Modern animated captions for Instagram Reels with word-level timing, highlighting, and icon integration.

## Prerequisites

```bash
npx remotion add @remotion/captions
```

## Generating Word Timestamps

Use the ElevenLabs skill (or any TTS with timestamps) to generate word-level timing:

```bash
# Scene-based generation with timestamps
node .claude/skills/elevenlabs/generate.js \
  --scenes remotion/instagram-ads/scenes/ad-example-scenes.json \
  --with-timestamps \
  --output-dir public/audio/instagram-ads/ad-example/

# Align existing audio (forced alignment)
node .claude/skills/elevenlabs/generate.js \
  --align public/audio/existing-voiceover.mp3 \
  --align-text "The transcript of your audio" \
  --output public/audio/existing-voiceover-captions.json
```

### Output Format

Creates a `*-captions.json` file:

```json
{
  "remotion": {
    "captions": [
      { "text": "Your ", "startMs": 0, "endMs": 250, "timestampMs": 0, "sceneId": "scene1" },
      { "text": "text ", "startMs": 250, "endMs": 500, "timestampMs": 250, "sceneId": "scene1" },
      { "text": "here", "startMs": 500, "endMs": 800, "timestampMs": 500, "sceneId": "scene1" }
    ]
  }
}
```

---

## Caption Styles

### 1. TikTok-Style Captions (Recommended)

Groups words into pages with active word highlighting:

```tsx
import { useMemo } from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";

type CaptionWord = {
  text: string;
  startMs: number;
  endMs: number;
  sceneId: string;
};

// Text replacements for phonetic spelling → display spelling
// Add your brand name or special words here
const TEXT_REPLACEMENTS: Record<string, string> = {
  // Example: TTS might mispronounce your brand name
  // "Fonetic": "Phonetic",  // How TTS says it → How it should display
  // "YourBrand": "YourBrand",
};

const getDisplayText = (text: string): string => {
  const trimmed = text.trim();
  const replaced = TEXT_REPLACEMENTS[trimmed] || trimmed;
  return replaced.toUpperCase();  // ALL CAPS for TikTok style
};

// Group words into pages
const createCaptionPages = (captions: CaptionWord[], combineMs: number = 1000) => {
  const pages: Array<{
    words: CaptionWord[];
    startMs: number;
    endMs: number;
  }> = [];

  let currentPage: CaptionWord[] = [];
  let pageStartMs = 0;

  for (const caption of captions) {
    if (currentPage.length === 0) {
      pageStartMs = caption.startMs;
      currentPage.push(caption);
    } else if (caption.startMs - pageStartMs < combineMs && currentPage.length < 6) {
      currentPage.push(caption);
    } else {
      pages.push({
        words: currentPage,
        startMs: pageStartMs,
        endMs: currentPage[currentPage.length - 1].endMs,
      });
      currentPage = [caption];
      pageStartMs = caption.startMs;
    }
  }

  if (currentPage.length > 0) {
    pages.push({
      words: currentPage,
      startMs: pageStartMs,
      endMs: currentPage[currentPage.length - 1].endMs,
    });
  }

  return pages;
};

interface TikTokCaptionsProps {
  captions: CaptionWord[];
  sceneId: string;
  sceneStartMs: number;
  highlightColor?: string;
  defaultColor?: string;
  fontSize?: number;
  fontFamily?: string;
}

export const TikTokCaptions: React.FC<TikTokCaptionsProps> = ({
  captions,
  sceneId,
  sceneStartMs,
  highlightColor = "#YOUR_ACCENT",  // TODO: Your accent color
  defaultColor = "#ffffff",
  fontSize = 52,
  fontFamily = "YOUR_FONT_FAMILY",  // TODO: Your brand font
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Filter captions for this scene
  const sceneCaptions = useMemo(() => {
    return captions.filter(c => c.sceneId === sceneId);
  }, [captions, sceneId]);

  // Create pages
  const pages = useMemo(() => createCaptionPages(sceneCaptions, 1000), [sceneCaptions]);

  // Current time relative to scene start
  const currentTimeMs = (frame / fps) * 1000 + sceneStartMs;

  // Find current page
  const currentPage = pages.find(p => p.startMs <= currentTimeMs && p.endMs >= currentTimeMs - 200);

  if (!currentPage) return null;

  // Page entrance animation
  const pageStartFrame = Math.round(((currentPage.startMs - sceneStartMs) / 1000) * fps);
  const pageProgress = spring({
    frame: frame - pageStartFrame,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  return (
    <div style={{
      position: "absolute",
      bottom: 420,  // Safe zone above Instagram UI
      left: 60,
      right: 60,
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      opacity: pageProgress,
      transform: `translateY(${interpolate(pageProgress, [0, 1], [30, 0])}px)`,
    }}>
      <div style={{ maxWidth: 900 }}>
        <div style={{
          fontFamily,
          fontSize,
          fontWeight: 400,
          textAlign: "center",
          lineHeight: 1.4,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "6px 16px",
        }}>
          {currentPage.words.map((word, i) => {
            const isActive = word.startMs <= currentTimeMs && word.endMs > currentTimeMs;
            const isPast = word.endMs <= currentTimeMs;
            const displayText = getDisplayText(word.text);

            // Word entrance animation
            const wordStartFrame = Math.round(((word.startMs - sceneStartMs) / 1000) * fps);
            const wordEntrance = spring({
              frame: frame - wordStartFrame,
              fps,
              config: { damping: 12, stiffness: 200, mass: 0.8 },
            });

            // Active word scale (subtle to avoid overlap)
            const scale = isActive ? 1.05 : 1;
            const opacity = interpolate(wordEntrance, [0, 1], [0.3, 1], { extrapolateRight: "clamp" });
            const translateY = interpolate(wordEntrance, [0, 1], [8, 0], { extrapolateRight: "clamp" });

            return (
              <span
                key={i}
                style={{
                  color: isActive ? highlightColor : (isPast ? "#cccccc" : defaultColor),
                  transform: `scale(${scale}) translateY(${translateY}px)`,
                  opacity,
                  textShadow: isActive
                    ? `0 2px 12px rgba(0,0,0,0.9), 0 0 30px ${highlightColor}40`
                    : "0 2px 8px rgba(0,0,0,0.8), 0 0 20px rgba(0,0,0,0.5)",
                  display: "inline-block",
                }}
              >
                {displayText}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
};
```

### 2. Word-by-Word (Single Word Display)

Shows one word at a time, centered:

```tsx
const WordByWordCaptions: React.FC<{ captions: CaptionWord[] }> = ({ captions }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeMs = (frame / fps) * 1000;

  const currentCaption = captions.find(
    (c) => c.startMs <= currentTimeMs && c.endMs > currentTimeMs
  );

  if (!currentCaption) return null;

  const wordDuration = currentCaption.endMs - currentCaption.startMs;
  const wordProgress = (currentTimeMs - currentCaption.startMs) / wordDuration;

  const scale = interpolate(
    wordProgress,
    [0, 0.15, 0.85, 1],
    [0.5, 1.1, 1.0, 0.95],
    { extrapolateRight: "clamp" }
  );

  const opacity = interpolate(
    wordProgress,
    [0, 0.1, 0.9, 1],
    [0, 1, 1, 0.8],
    { extrapolateRight: "clamp" }
  );

  return (
    <div style={{
      position: "absolute",
      inset: 0,
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
    }}>
      <div style={{
        fontSize: 120,
        fontWeight: 900,
        color: "#ffffff",
        textShadow: "0 4px 20px rgba(0,0,0,0.8)",
        transform: `scale(${scale})`,
        opacity,
        textAlign: "center",
        maxWidth: 900,
      }}>
        {currentCaption.text.trim().toUpperCase()}
      </div>
    </div>
  );
};
```

### 3. Karaoke-Style (Full Sentence, Highlighted Word)

```tsx
const KaraokeCaptions: React.FC<{
  captions: CaptionWord[];
  highlightColor?: string;
}> = ({
  captions,
  highlightColor = "#FFD700",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeMs = (frame / fps) * 1000;

  return (
    <div style={{
      position: "absolute",
      bottom: 450,
      left: 80,
      right: 80,
      textAlign: "center",
    }}>
      <div style={{
        fontSize: 64,
        fontWeight: 700,
        lineHeight: 1.3,
        textShadow: "0 4px 12px rgba(0,0,0,0.7)",
      }}>
        {captions.map((caption, index) => {
          const isActive = caption.startMs <= currentTimeMs && caption.endMs > currentTimeMs;
          const isPast = caption.endMs <= currentTimeMs;

          return (
            <span
              key={index}
              style={{
                color: isActive ? highlightColor : isPast ? "#ffffff" : "rgba(255,255,255,0.6)",
                fontWeight: isActive ? 900 : 700,
                transform: isActive ? "scale(1.1)" : "scale(1)",
                display: "inline",
              }}
            >
              {caption.text}
            </span>
          );
        })}
      </div>
    </div>
  );
};
```

---

## Animation Presets

### Pop Animation

```tsx
const PopAnimation: React.FC<{ children: React.ReactNode; delay?: number }> = ({
  children,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame: frame - delay,
    fps,
    config: { damping: 8, stiffness: 200 },
  });

  const opacity = interpolate(frame - delay, [0, 3], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div style={{ transform: `scale(${scale})`, opacity }}>
      {children}
    </div>
  );
};
```

### Slide Up Animation

```tsx
const SlideUpAnimation: React.FC<{ children: React.ReactNode; delay?: number }> = ({
  children,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - delay,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  const translateY = interpolate(progress, [0, 1], [50, 0]);
  const opacity = interpolate(progress, [0, 1], [0, 1]);

  return (
    <div style={{ transform: `translateY(${translateY}px)`, opacity }}>
      {children}
    </div>
  );
};
```

---

## Caption Positioning

### Safe Zone Placement

```tsx
const CAPTION_POSITIONS = {
  // Upper third - good for titles
  upper: { bottom: "auto", top: 400 },

  // Center - most visible
  center: { top: "50%", transform: "translateY(-50%)" },

  // Lower third - traditional position (above danger zone!)
  lower: { top: "auto", bottom: 450 },
};
```

### Responsive Font Sizing

```tsx
const getResponsiveFontSize = (wordLength: number): number => {
  if (wordLength <= 3) return 140;
  if (wordLength <= 6) return 120;
  if (wordLength <= 10) return 100;
  if (wordLength <= 15) return 80;
  return 64;
};
```

---

## Integration with Scenes

### Using Captions in Ad Composition

```tsx
import captionsData from "../../../public/audio/instagram-ads/ad-example/ad-example-captions.json";

const SCENE_START_MS = {
  scene1: 0,
  scene2: 3500,  // From info.json durations
  scene3: 8000,
  scene4: 12000,
};

export const Scene1: React.FC = () => {
  return (
    <AbsoluteFill>
      {/* Scene content */}

      {/* Captions */}
      <TikTokCaptions
        captions={captionsData.remotion.captions}
        sceneId="scene1"
        sceneStartMs={SCENE_START_MS.scene1}
        highlightColor={COLORS.accent}  // TODO: Your accent color
        fontSize={56}
      />
    </AbsoluteFill>
  );
};
```

---

## Performance Tips

1. **Memoize caption calculations**:
   ```tsx
   const memoizedPages = useMemo(
     () => createCaptionPages(captions, 1000),
     [captions]
   );
   ```

2. **Pre-load fonts**:
   ```tsx
   // TODO: Replace with your brand font
   import { loadFont } from "@remotion/google-fonts/YourFont";
   const { fontFamily } = loadFont();
   ```

3. **Keep text shadows simple**:
   ```tsx
   // Good
   textShadow: "0 4px 12px rgba(0,0,0,0.7)"

   // Avoid
   textShadow: "0 2px 4px rgba(0,0,0,0.3), 0 4px 8px rgba(0,0,0,0.2), ..."
   ```

---

## Workflow Summary

1. **Generate voiceover with timestamps**:
   ```bash
   node .claude/skills/elevenlabs/generate.js \
     --scenes remotion/instagram-ads/scenes/ad-example-scenes.json \
     --with-timestamps \
     --output-dir public/audio/instagram-ads/ad-example/
   ```

2. **Import captions in composition**:
   ```tsx
   import captionsData from "../../../public/audio/instagram-ads/ad-example/ad-example-captions.json";
   const captions = captionsData.remotion.captions;
   ```

3. **Choose caption style** (TikTok, word-by-word, karaoke)

4. **Configure colors to match your brand**

5. **Render**:
   ```bash
   npx remotion render AdExample out/reel.mp4 --codec=h264 --crf=18
   ```
