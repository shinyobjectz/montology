---
title: Reusable Components
description: Template components for building Instagram Reels and Carousels
section: video-creation
priority: medium
tags: [components, templates, react, layout, scenes]
---

# Reusable Components for Instagram Ads

Template components for building Instagram Reels and Carousels with Remotion.

---

## Layout Components

### Safe Content Area

```tsx
import { AbsoluteFill } from "remotion";

// TODO: Import your brand colors
const COLORS = {
  primary: "#YOUR_PRIMARY",
  background: "#YOUR_BACKGROUND",
};

interface SafeContentAreaProps {
  children: React.ReactNode;
  style?: React.CSSProperties;
}

/**
 * Wraps content within Instagram Reels safe zones
 * Avoids top UI (username) and bottom UI (buttons, captions)
 */
export const SafeContentArea: React.FC<SafeContentAreaProps> = ({
  children,
  style = {},
}) => (
  <div style={{
    position: "absolute",
    top: 285,      // Below top UI
    bottom: 400,   // Above bottom UI
    left: 80,      // Left margin
    right: 120,    // Right margin (action buttons)
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    ...style,
  }}>
    {children}
  </div>
);
```

### Title Zone

```tsx
/**
 * Upper-middle zone for headlines (y = 400-800px)
 */
export const TitleZone: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{
    position: "absolute",
    top: 400,
    left: 80,
    right: 120,
    height: 400,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
  }}>
    {children}
  </div>
);
```

### Subtitle Zone

```tsx
/**
 * Center zone for main content (y = 800-1400px)
 */
export const SubtitleZone: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{
    position: "absolute",
    top: 800,
    left: 80,
    right: 120,
    height: 600,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
  }}>
    {children}
  </div>
);
```

### Caption Zone

```tsx
/**
 * Lower zone for captions (y = 1300-1520px)
 * Above Instagram's bottom UI but below main content
 */
export const CaptionZone: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{
    position: "absolute",
    bottom: 420,  // Above bottom danger zone
    left: 60,
    right: 60,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  }}>
    {children}
  </div>
);
```

---

## Background Components

### Gradient Background

```tsx
interface GradientBackgroundProps {
  color1: string;
  color2: string;
  angle?: number;
}

export const GradientBackground: React.FC<GradientBackgroundProps> = ({
  color1,
  color2,
  angle = 160,
}) => (
  <AbsoluteFill style={{
    background: `linear-gradient(${angle}deg, ${color1} 0%, ${color2} 100%)`,
  }} />
);

// Usage
<GradientBackground color1={COLORS.primary} color2={COLORS.dark} angle={160} />
```

### Image Background

```tsx
import { Img, staticFile } from "remotion";

interface ImageBackgroundProps {
  src: string;
  opacity?: number;
}

export const ImageBackground: React.FC<ImageBackgroundProps> = ({
  src,
  opacity = 1,
}) => (
  <Img
    src={staticFile(src)}
    style={{
      position: "absolute",
      width: "100%",
      height: "100%",
      objectFit: "cover",
      opacity,
    }}
  />
);

// Usage
<ImageBackground src="images/instagram-ads/backgrounds/dots.png" />
```

### Grainy Overlay

```tsx
interface GrainyOverlayProps {
  opacity?: number;
}

/**
 * Adds subtle noise texture to backgrounds
 * Use opacity 0.03-0.05 for light BGs, 0.05-0.10 for dark BGs
 */
export const GrainyOverlay: React.FC<GrainyOverlayProps> = ({ opacity = 0.05 }) => {
  const noiseFilter = `
    <svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">
      <filter id="noise" x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" stitchTiles="stitch"/>
        <feColorMatrix type="saturate" values="0"/>
      </filter>
      <rect width="100%" height="100%" filter="url(#noise)" opacity="1"/>
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

## Typography Components

### Animated Headline

```tsx
import { spring, useCurrentFrame, useVideoConfig, interpolate } from "remotion";

interface AnimatedHeadlineProps {
  children: React.ReactNode;
  delay?: number;
  color?: string;
  fontSize?: number;
}

export const AnimatedHeadline: React.FC<AnimatedHeadlineProps> = ({
  children,
  delay = 0,
  color = "#ffffff",
  fontSize = 64,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const progress = spring({
    frame: frame - delayFrames,
    fps,
    config: { damping: 200 },
  });

  return (
    <h1 style={{
      fontSize,
      fontWeight: 700,
      color,
      textAlign: "center",
      lineHeight: 1.15,
      margin: 0,
      opacity: progress,
      transform: `translateY(${interpolate(progress, [0, 1], [30, 0])}px)`,
    }}>
      {children}
    </h1>
  );
};
```

### Highlighted Text

```tsx
interface HighlightedTextProps {
  children: React.ReactNode;
  highlight: string;
  highlightColor?: string;
  baseColor?: string;
  fontSize?: number;
}

/**
 * Renders text with a highlighted word/phrase
 */
export const HighlightedText: React.FC<HighlightedTextProps> = ({
  children,
  highlight,
  highlightColor = "#FFD700",
  baseColor = "#ffffff",
  fontSize = 64,
}) => {
  const text = String(children);
  const parts = text.split(new RegExp(`(${highlight})`, "gi"));

  return (
    <span style={{ fontSize, color: baseColor }}>
      {parts.map((part, i) =>
        part.toLowerCase() === highlight.toLowerCase() ? (
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

// Usage
<HighlightedText highlight="Mängel" highlightColor={COLORS.accent}>
  Versteckte Mängel entdeckt?
</HighlightedText>
```

### Subtitle Text

```tsx
interface SubtitleProps {
  children: React.ReactNode;
  delay?: number;
  color?: string;
  fontSize?: number;
}

export const Subtitle: React.FC<SubtitleProps> = ({
  children,
  delay = 0,
  color = "#cccccc",
  fontSize = 48,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const progress = spring({
    frame: frame - delayFrames,
    fps,
    config: { damping: 200 },
  });

  return (
    <p style={{
      fontSize,
      fontWeight: 500,
      color,
      textAlign: "center",
      lineHeight: 1.3,
      margin: 0,
      marginTop: 24,
      opacity: progress,
      transform: `translateY(${interpolate(progress, [0, 1], [20, 0])}px)`,
    }}>
      {children}
    </p>
  );
};
```

---

## List Components

### Animated Bullet List

```tsx
import { Img, staticFile } from "remotion";

interface BulletItem {
  icon?: string;
  text: string;
}

interface AnimatedBulletListProps {
  items: BulletItem[];
  startDelay?: number;
  staggerDelay?: number;
  iconSize?: number;
  fontSize?: number;
  color?: string;
}

export const AnimatedBulletList: React.FC<AnimatedBulletListProps> = ({
  items,
  startDelay = 0.2,
  staggerDelay = 0.15,
  iconSize = 60,
  fontSize = 44,
  color = "#ffffff",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      gap: 24,
      width: "100%",
    }}>
      {items.map((item, index) => {
        const itemDelay = startDelay + index * staggerDelay;
        const delayFrames = Math.round(itemDelay * fps);

        const progress = spring({
          frame: frame - delayFrames,
          fps,
          config: { damping: 15, stiffness: 100 },
        });

        const opacity = interpolate(progress, [0, 1], [0, 1]);
        const translateX = interpolate(progress, [0, 1], [-30, 0]);

        return (
          <div
            key={index}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 20,
              opacity,
              transform: `translateX(${translateX}px)`,
            }}
          >
            {item.icon ? (
              <Img
                src={staticFile(item.icon)}
                style={{
                  width: iconSize,
                  height: iconSize,
                  objectFit: "contain",
                }}
              />
            ) : (
              <span style={{ color, fontSize: 36, fontWeight: 700 }}>•</span>
            )}
            <span style={{
              fontSize,
              fontWeight: 500,
              color,
              lineHeight: 1.3,
            }}>
              {item.text}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// Usage
<AnimatedBulletList
  items={[
    { icon: "images/icons/warning.png", text: "Problem one" },
    { icon: "images/icons/warning.png", text: "Problem two" },
    { icon: "images/icons/warning.png", text: "Problem three" },
  ]}
  startDelay={0.3}
  staggerDelay={0.2}
/>
```

---

## Icon Components

### Animated Icon

```tsx
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
    opacity = spring({
      frame: frame - delayFrames,
      fps,
      config: { damping: 200 },
    });
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

---

## CTA Components

### CTA Button

```tsx
interface CTAButtonProps {
  text: string;
  delay?: number;
  backgroundColor?: string;
  textColor?: string;
  icon?: React.ReactNode;
}

export const CTAButton: React.FC<CTAButtonProps> = ({
  text,
  delay = 0,
  backgroundColor = "#ffffff",
  textColor = "#000000",
  icon,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const progress = spring({
    frame: frame - delayFrames,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 12,
      backgroundColor,
      padding: "24px 48px",
      borderRadius: 60,
      opacity: progress,
      transform: `scale(${interpolate(progress, [0, 1], [0.8, 1])})`,
    }}>
      <span style={{
        fontSize: 36,
        fontWeight: 600,
        color: textColor,
      }}>
        {text}
      </span>
      {icon}
    </div>
  );
};

// Usage
<CTAButton
  text="Link in Bio"
  backgroundColor={COLORS.primary}
  textColor={COLORS.background}
  icon={<ArrowIcon color={COLORS.background} size={32} />}
/>
```

### Arrow Icon

```tsx
interface ArrowIconProps {
  color?: string;
  size?: number;
}

export const ArrowIcon: React.FC<ArrowIconProps> = ({
  color = "#ffffff",
  size = 28,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M5 12h14M12 5l7 7-7 7" />
  </svg>
);
```

### Trust Badge

```tsx
interface TrustBadgeProps {
  rating: number;
  reviewCount: string;
  delay?: number;
}

export const TrustBadge: React.FC<TrustBadgeProps> = ({
  rating,
  reviewCount,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const progress = spring({
    frame: frame - delayFrames,
    fps,
    config: { damping: 200 },
  });

  // Render stars
  const stars = Array.from({ length: 5 }, (_, i) => {
    const filled = i < Math.floor(rating);
    const partial = i === Math.floor(rating) && rating % 1 > 0;

    return (
      <span
        key={i}
        style={{
          color: filled || partial ? "#f97316" : "#666666",
          fontSize: 32,
        }}
      >
        ★
      </span>
    );
  });

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 12,
      opacity: progress,
    }}>
      <div style={{ display: "flex" }}>{stars}</div>
      <span style={{ fontSize: 28, color: "#888888" }}>
        ({reviewCount})
      </span>
    </div>
  );
};
```

---

## Debug Components

### Safe Zone Debug Overlay

```tsx
/**
 * Shows safe zone boundaries during development
 * Set showDebug={false} for production renders
 */
export const SafeZoneDebugOverlay: React.FC = () => (
  <>
    {/* Top danger zone */}
    <div style={{
      position: "absolute",
      top: 0, left: 0, right: 0,
      height: 285,
      backgroundColor: "rgba(255,0,0,0.15)",
      borderBottom: "2px dashed #ff0000",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#ff0000",
      fontSize: 24,
    }}>
      TOP DANGER ZONE (0-285px)
    </div>

    {/* Bottom danger zone */}
    <div style={{
      position: "absolute",
      bottom: 0, left: 0, right: 0,
      height: 400,
      backgroundColor: "rgba(255,0,0,0.15)",
      borderTop: "2px dashed #ff0000",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#ff0000",
      fontSize: 24,
    }}>
      BOTTOM DANGER ZONE (1520-1920px)
    </div>

    {/* Side margins */}
    <div style={{
      position: "absolute",
      top: 285, bottom: 400,
      left: 0, width: 80,
      backgroundColor: "rgba(255,165,0,0.15)",
      borderRight: "2px dashed orange",
    }} />
    <div style={{
      position: "absolute",
      top: 285, bottom: 400,
      right: 0, width: 120,
      backgroundColor: "rgba(255,165,0,0.15)",
      borderLeft: "2px dashed orange",
    }} />

    {/* 1:1 grid crop lines */}
    <div style={{
      position: "absolute",
      top: 420, left: 0, right: 0,
      height: 2,
      backgroundColor: "rgba(0,255,0,0.5)",
    }} />
    <div style={{
      position: "absolute",
      bottom: 420, left: 0, right: 0,
      height: 2,
      backgroundColor: "rgba(0,255,0,0.5)",
    }} />
  </>
);
```

---

## Complete Scene Templates

### Scene 1: Hook Template

```tsx
export const HookSceneTemplate: React.FC<{
  icon: string;
  headline: React.ReactNode;
  subtitle: string;
  backgroundColor?: string;
}> = ({
  icon,
  headline,
  subtitle,
  backgroundColor,
}) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      <GradientBackground
        color1={backgroundColor || COLORS.primary}
        color2={COLORS.dark}
      />
      <GrainyOverlay opacity={0.08} />

      <SafeContentArea>
        <AnimatedIcon src={icon} size={180} animation="pop" />

        <div style={{ marginTop: 40, textAlign: "center" }}>
          <AnimatedHeadline delay={0.15}>
            {headline}
          </AnimatedHeadline>

          <Subtitle delay={0.35} color={COLORS.accent}>
            {subtitle}
          </Subtitle>
        </div>
      </SafeContentArea>
    </AbsoluteFill>
  );
};
```

### Scene 4: CTA Template

```tsx
export const CTASceneTemplate: React.FC<{
  logo: string;
  headline: string;
  ctaText: string;
  rating?: number;
  reviewCount?: string;
}> = ({
  logo,
  headline,
  ctaText,
  rating,
  reviewCount,
}) => {
  return (
    <AbsoluteFill>
      <GradientBackground
        color1={COLORS.background}
        color2={COLORS.backgroundDark}
      />
      <GrainyOverlay opacity={0.04} />

      <SafeContentArea style={{ gap: 32 }}>
        <AnimatedIcon src={logo} size={300} delay={0} animation="fade" />

        <AnimatedHeadline delay={0.2} color={COLORS.primary} fontSize={52}>
          {headline}
        </AnimatedHeadline>

        {rating && reviewCount && (
          <TrustBadge rating={rating} reviewCount={reviewCount} delay={0.4} />
        )}

        <CTAButton
          text={ctaText}
          delay={0.5}
          backgroundColor={COLORS.primary}
          textColor={COLORS.background}
          icon={<ArrowIcon color={COLORS.background} size={32} />}
        />
      </SafeContentArea>
    </AbsoluteFill>
  );
};
```

---

## Usage Example

```tsx
import { AbsoluteFill, Audio, Series, staticFile, useVideoConfig } from "remotion";

export const MyAd: React.FC = () => {
  const { fps } = useVideoConfig();

  // Durations from voiceover info.json
  const DURATIONS = { scene1: 3.5, scene2: 4.5, scene3: 4.0, scene4: 3.0 };

  const scene1Frames = Math.round(DURATIONS.scene1 * fps) + 5;
  const scene2Frames = Math.round(DURATIONS.scene2 * fps) + 5;
  const scene3Frames = Math.round(DURATIONS.scene3 * fps) + 5;
  const scene4Frames = Math.round(15 * fps) - scene1Frames - scene2Frames - scene3Frames;

  return (
    <AbsoluteFill>
      <Audio src={staticFile("audio/instagram-ads/my-ad/my-ad-combined.mp3")} />

      <Series>
        <Series.Sequence durationInFrames={scene1Frames}>
          <HookSceneTemplate
            icon="images/icons/hook.png"
            headline={<>Your <span style={{ color: COLORS.accent }}>Hook</span> Here</>}
            subtitle="Empathetic subtitle"
          />
        </Series.Sequence>

        {/* ... more scenes */}

        <Series.Sequence durationInFrames={scene4Frames}>
          <CTASceneTemplate
            logo="your-logo.png"
            headline="Your CTA Headline"
            ctaText="Link in Bio"
            rating={4.9}
            reviewCount="500+"
          />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
```
