---
title: Animation Guide
description: Spring configurations, transitions, and animation components
section: video-creation
priority: medium
tags: [animation, spring, transitions, motion, effects]
---

# Animation Guide for Instagram Ads

Animation patterns, spring configurations, and effects for Remotion Instagram videos.

---

## Spring Configurations

### Presets

```tsx
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

// Smooth - Professional, no bounce
const SPRING_SMOOTH = { damping: 200 };

// Gentle - Soft, subtle movement
const SPRING_GENTLE = { damping: 20, stiffness: 80 };

// Quick - Snappy, responsive
const SPRING_QUICK = { damping: 15, stiffness: 100 };

// Bouncy - Playful, attention-grabbing
const SPRING_BOUNCY = { damping: 8, stiffness: 200 };

// Elastic - Very bouncy, fun
const SPRING_ELASTIC = { damping: 5, stiffness: 150, mass: 0.5 };

// Heavy - Slow, weighty feel
const SPRING_HEAVY = { damping: 30, stiffness: 50, mass: 2 };
```

### When to Use Each

| Preset | Use For |
|--------|---------|
| `SPRING_SMOOTH` | Professional content, text reveals, subtle movements |
| `SPRING_GENTLE` | Icons appearing, soft transitions |
| `SPRING_QUICK` | Button presses, quick UI feedback |
| `SPRING_BOUNCY` | Attention-grabbing elements, playful content |
| `SPRING_ELASTIC` | Logos, fun branding, casual content |
| `SPRING_HEAVY` | Large elements, dramatic reveals |

---

## Basic Animation Components

### Fade In

```tsx
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

interface FadeInProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
}

export const FadeIn: React.FC<FadeInProps> = ({
  children,
  delay = 0,
  duration = 15,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const opacity = interpolate(
    frame - delayFrames,
    [0, duration],
    [0, 1],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  return (
    <div style={{ opacity }}>
      {children}
    </div>
  );
};
```

### Fade In with Slide Up

```tsx
import { spring, useCurrentFrame, useVideoConfig, interpolate } from "remotion";

interface FadeInUpProps {
  children: React.ReactNode;
  delay?: number;
  distance?: number;
  springConfig?: object;
}

export const FadeInUp: React.FC<FadeInUpProps> = ({
  children,
  delay = 0,
  distance = 30,
  springConfig = { damping: 200 },
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const progress = spring({
    frame: frame - delayFrames,
    fps,
    config: springConfig,
  });

  const translateY = interpolate(progress, [0, 1], [distance, 0]);
  const opacity = interpolate(progress, [0, 1], [0, 1]);

  return (
    <div style={{
      opacity,
      transform: `translateY(${translateY}px)`,
    }}>
      {children}
    </div>
  );
};
```

### Scale Pop

```tsx
interface ScalePopProps {
  children: React.ReactNode;
  delay?: number;
  springConfig?: object;
}

export const ScalePop: React.FC<ScalePopProps> = ({
  children,
  delay = 0,
  springConfig = { damping: 8, stiffness: 200 },
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const scale = spring({
    frame: frame - delayFrames,
    fps,
    config: springConfig,
  });

  const opacity = interpolate(frame - delayFrames, [0, 5], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  return (
    <div style={{
      opacity,
      transform: `scale(${scale})`,
    }}>
      {children}
    </div>
  );
};
```

### Slide In from Side

```tsx
interface SlideInProps {
  children: React.ReactNode;
  direction?: "left" | "right";
  delay?: number;
  distance?: number;
}

export const SlideIn: React.FC<SlideInProps> = ({
  children,
  direction = "left",
  delay = 0,
  distance = 100,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const progress = spring({
    frame: frame - delayFrames,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  const startX = direction === "left" ? -distance : distance;
  const translateX = interpolate(progress, [0, 1], [startX, 0]);
  const opacity = interpolate(progress, [0, 1], [0, 1]);

  return (
    <div style={{
      opacity,
      transform: `translateX(${translateX}px)`,
    }}>
      {children}
    </div>
  );
};
```

---

## Text Animations

### Staggered Text Reveal

```tsx
interface StaggeredTextProps {
  items: string[];
  delayBetween?: number;  // Seconds between each item
  startDelay?: number;     // Initial delay in seconds
  renderItem: (item: string, index: number) => React.ReactNode;
}

export const StaggeredText: React.FC<StaggeredTextProps> = ({
  items,
  delayBetween = 0.15,
  startDelay = 0,
  renderItem,
}) => {
  return (
    <>
      {items.map((item, index) => (
        <FadeInUp
          key={index}
          delay={startDelay + index * delayBetween}
        >
          {renderItem(item, index)}
        </FadeInUp>
      ))}
    </>
  );
};

// Usage
<StaggeredText
  items={["First point", "Second point", "Third point"]}
  delayBetween={0.2}
  renderItem={(item) => (
    <div style={{ fontSize: 48, marginBottom: 16 }}>
      • {item}
    </div>
  )}
/>
```

### Character-by-Character Reveal

```tsx
interface TypewriterProps {
  text: string;
  delay?: number;
  speed?: number;  // Characters per second
  style?: React.CSSProperties;
}

export const Typewriter: React.FC<TypewriterProps> = ({
  text,
  delay = 0,
  speed = 20,
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const framesPerChar = fps / speed;
  const charsToShow = Math.floor((frame - delayFrames) / framesPerChar);
  const visibleText = text.slice(0, Math.max(0, charsToShow));

  return (
    <span style={style}>
      {visibleText}
      <span style={{ opacity: frame % 15 < 8 ? 1 : 0 }}>|</span>
    </span>
  );
};
```

### Word Highlight

```tsx
interface HighlightWordProps {
  text: string;
  highlightWord: string;
  highlightColor?: string;
  style?: React.CSSProperties;
}

export const HighlightWord: React.FC<HighlightWordProps> = ({
  text,
  highlightWord,
  highlightColor = "#FFD700",
  style = {},
}) => {
  const parts = text.split(new RegExp(`(${highlightWord})`, "gi"));

  return (
    <span style={style}>
      {parts.map((part, i) =>
        part.toLowerCase() === highlightWord.toLowerCase() ? (
          <span key={i} style={{ color: highlightColor, fontWeight: 700 }}>
            {part}
          </span>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
};
```

---

## Icon Animations

### Animated Icon with Entrance

```tsx
import { Img, staticFile } from "remotion";

interface AnimatedIconProps {
  src: string;
  size: number;
  delay?: number;
  animation?: "pop" | "fade" | "slide";
}

export const AnimatedIcon: React.FC<AnimatedIconProps> = ({
  src,
  size,
  delay = 0,
  animation = "pop",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);

  let scale = 1;
  let opacity = 1;
  let translateY = 0;

  if (animation === "pop") {
    scale = spring({
      frame: frame - delayFrames,
      fps,
      config: { damping: 8, stiffness: 200 },
    });
    opacity = interpolate(frame - delayFrames, [0, 5], [0, 1], {
      extrapolateRight: "clamp",
    });
  } else if (animation === "fade") {
    const progress = spring({
      frame: frame - delayFrames,
      fps,
      config: { damping: 200 },
    });
    opacity = progress;
  } else if (animation === "slide") {
    const progress = spring({
      frame: frame - delayFrames,
      fps,
      config: { damping: 15, stiffness: 100 },
    });
    translateY = interpolate(progress, [0, 1], [30, 0]);
    opacity = progress;
  }

  return (
    <Img
      src={staticFile(src)}
      style={{
        width: size,
        height: size,
        objectFit: "contain",
        transform: `scale(${scale}) translateY(${translateY}px)`,
        opacity,
      }}
    />
  );
};
```

### Pulsing Icon

```tsx
interface PulsingIconProps {
  src: string;
  size: number;
  pulseScale?: number;
  pulseDuration?: number;  // In frames
}

export const PulsingIcon: React.FC<PulsingIconProps> = ({
  src,
  size,
  pulseScale = 1.1,
  pulseDuration = 30,
}) => {
  const frame = useCurrentFrame();

  const pulse = Math.sin((frame / pulseDuration) * Math.PI * 2);
  const scale = 1 + (pulse * 0.5 + 0.5) * (pulseScale - 1);

  return (
    <Img
      src={staticFile(src)}
      style={{
        width: size,
        height: size,
        objectFit: "contain",
        transform: `scale(${scale})`,
      }}
    />
  );
};
```

---

## Scene Transitions

### Crossfade

```tsx
import { interpolate, Sequence } from "remotion";

interface CrossfadeProps {
  children: [React.ReactNode, React.ReactNode];
  transitionDuration?: number;  // Frames
  transitionStart: number;       // Frame to start transition
}

export const Crossfade: React.FC<CrossfadeProps> = ({
  children,
  transitionDuration = 15,
  transitionStart,
}) => {
  const frame = useCurrentFrame();

  const opacity1 = interpolate(
    frame,
    [transitionStart, transitionStart + transitionDuration],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const opacity2 = interpolate(
    frame,
    [transitionStart, transitionStart + transitionDuration],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <>
      <div style={{ position: "absolute", inset: 0, opacity: opacity1 }}>
        {children[0]}
      </div>
      <div style={{ position: "absolute", inset: 0, opacity: opacity2 }}>
        {children[1]}
      </div>
    </>
  );
};
```

### Wipe Transition

```tsx
interface WipeProps {
  direction?: "left" | "right" | "up" | "down";
  progress: number;  // 0-1
  children: React.ReactNode;
}

export const Wipe: React.FC<WipeProps> = ({
  direction = "left",
  progress,
  children,
}) => {
  let clipPath: string;

  switch (direction) {
    case "left":
      clipPath = `inset(0 ${(1 - progress) * 100}% 0 0)`;
      break;
    case "right":
      clipPath = `inset(0 0 0 ${(1 - progress) * 100}%)`;
      break;
    case "up":
      clipPath = `inset(0 0 ${(1 - progress) * 100}% 0)`;
      break;
    case "down":
      clipPath = `inset(${(1 - progress) * 100}% 0 0 0)`;
      break;
  }

  return (
    <div style={{ clipPath }}>
      {children}
    </div>
  );
};
```

---

## Background Animations

### Gradient Shift

```tsx
interface GradientShiftProps {
  color1: string;
  color2: string;
  angle?: number;
  shiftAmount?: number;
}

export const GradientShift: React.FC<GradientShiftProps> = ({
  color1,
  color2,
  angle = 160,
  shiftAmount = 20,
}) => {
  const frame = useCurrentFrame();
  const shift = Math.sin(frame / 60) * shiftAmount;

  return (
    <div style={{
      position: "absolute",
      inset: 0,
      background: `linear-gradient(${angle + shift}deg, ${color1} 0%, ${color2} 100%)`,
    }} />
  );
};
```

### Grainy Overlay

```tsx
interface GrainyOverlayProps {
  opacity?: number;
  animated?: boolean;
}

export const GrainyOverlay: React.FC<GrainyOverlayProps> = ({
  opacity = 0.05,
  animated = false,
}) => {
  const frame = useCurrentFrame();
  const seed = animated ? frame % 10 : 0;

  const noiseFilter = `
    <svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">
      <filter id="noise${seed}" x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" seed="${seed}" stitchTiles="stitch"/>
        <feColorMatrix type="saturate" values="0"/>
      </filter>
      <rect width="100%" height="100%" filter="url(#noise${seed})" opacity="1"/>
    </svg>
  `;

  return (
    <div style={{
      position: "absolute",
      inset: 0,
      backgroundImage: `url("data:image/svg+xml,${encodeURIComponent(noiseFilter)}")`,
      backgroundRepeat: "repeat",
      opacity,
      mixBlendMode: "overlay",
      pointerEvents: "none",
    }} />
  );
};
```

---

## Timing Helpers

### Delay Calculator

```tsx
/**
 * Calculate frame delays from seconds
 */
export const useDelayFrames = (delaySeconds: number): number => {
  const { fps } = useVideoConfig();
  return Math.round(delaySeconds * fps);
};

// Usage
const delay = useDelayFrames(0.5); // 15 frames at 30fps
```

### Stagger Calculator

```tsx
/**
 * Generate delays for staggered animations
 */
export const getStaggerDelays = (
  count: number,
  interval: number,
  startDelay: number = 0
): number[] => {
  return Array.from({ length: count }, (_, i) => startDelay + i * interval);
};

// Usage
const delays = getStaggerDelays(5, 0.15, 0.3);
// [0.3, 0.45, 0.6, 0.75, 0.9]
```

### Scene Timing

```tsx
/**
 * Calculate if current frame is within a scene
 */
export const useIsInScene = (
  sceneStart: number,
  sceneDuration: number
): boolean => {
  const frame = useCurrentFrame();
  return frame >= sceneStart && frame < sceneStart + sceneDuration;
};

/**
 * Get progress within current scene (0-1)
 */
export const useSceneProgress = (
  sceneStart: number,
  sceneDuration: number
): number => {
  const frame = useCurrentFrame();
  return Math.max(0, Math.min(1, (frame - sceneStart) / sceneDuration));
};
```

---

## Performance Tips

1. **Avoid re-renders**: Use `useMemo` for expensive calculations
2. **Limit spring calculations**: Don't create new springs every frame
3. **Use CSS transforms**: `transform` is GPU-accelerated, `left/top` is not
4. **Batch similar animations**: Group elements with same timing
5. **Avoid blur on text**: `filter: blur()` is expensive

### Example: Optimized Animation

```tsx
const OptimizedAnimation: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Memoize spring config
  const springConfig = useMemo(() => ({ damping: 200 }), []);

  // Calculate spring once per frame
  const progress = spring({
    frame,
    fps,
    config: springConfig,
  });

  // Derive all values from single progress
  const style = useMemo(() => ({
    opacity: progress,
    transform: `translateY(${(1 - progress) * 30}px) scale(${0.8 + progress * 0.2})`,
  }), [progress]);

  return <div style={style}>Content</div>;
};
```
