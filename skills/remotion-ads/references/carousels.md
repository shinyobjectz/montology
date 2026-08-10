---
title: Instagram Carousel Specifications
description: Technical guide for creating Instagram carousels with Remotion
section: assets
priority: low
tags: [carousel, static, images, slides, instagram]
---

# Instagram Carousel Design Specifications

Technical guide for creating Instagram carousels with Remotion. Carousels are static image posts (up to 10 slides) that users swipe through.

## Core Dimensions

| Format | Dimensions | Aspect Ratio | Use Case |
|--------|------------|--------------|----------|
| **Portrait (Recommended)** | 1080×1350px | 4:5 | More screen real estate |
| Square | 1080×1080px | 1:1 | Classic format |
| Landscape | 1080×566px | 1.91:1 | Wide content |

**Recommended: 4:5 Portrait (1080×1350px)**

---

## Safe Zones

```
┌─────────────────────────────────────┐ 0px
│       TOP PADDING (80px)            │
├─────────────────────────────────────┤ 80px
│ ←80px                         80px→ │
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  │      SAFE CONTENT           │    │
│  │         AREA                │    │
│  │                             │    │
│  │    920×1190px centered      │    │
│  │                             │    │
│  └─────────────────────────────┘    │
│                                     │
├─────────────────────────────────────┤ 1270px
│     BOTTOM PADDING (80px)           │
└─────────────────────────────────────┘ 1350px
```

---

## Slide Types

### 1. Hook Slide (Slide 1)

Attention-grabbing first slide:

```tsx
import { AbsoluteFill, Img, staticFile } from "remotion";

// TODO: Import your design system
const COLORS = {
  primary: "#YOUR_PRIMARY",
  background: "#YOUR_BACKGROUND",
  // ...
};

const PADDING = 80;

export const CarouselSlide1: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COLORS.primary }}>
    <GrainyOverlay opacity={0.05} />

    <div style={{
      position: "absolute",
      top: PADDING,
      left: PADDING,
      right: PADDING,
      bottom: PADDING,
      display: "flex",
      flexDirection: "column",
    }}>
      {/* Badge/Category */}
      <span style={{
        fontSize: 36,
        fontWeight: 500,
        color: COLORS.background,
        textAlign: "center",
      }}>
        Category Tag
      </span>

      {/* Hero Icon/Illustration */}
      <div style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}>
        <Img
          src={staticFile("images/instagram-ads/illustrations/hero.png")}
          style={{ width: 420, height: 420, objectFit: "contain" }}
        />
      </div>

      {/* Headline */}
      <div style={{ textAlign: "center", marginBottom: 60 }}>
        <h1 style={{
          fontSize: 58,
          fontWeight: 600,
          color: COLORS.background,
          lineHeight: 1.15,
          margin: 0,
        }}>
          Your Hook<br />Headline Here?
        </h1>
        <p style={{
          fontSize: 48,
          fontWeight: 500,
          color: COLORS.background,
          marginTop: 16,
        }}>
          Supporting subtitle.
        </p>
      </div>

      {/* Swipe indicator */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: 26, color: COLORS.background }}>
          Swipe for more
        </span>
        <ArrowIcon color={COLORS.background} size={28} />
      </div>
    </div>
  </AbsoluteFill>
);
```

### 2. Content Slides (Slides 2-4)

Information slides with bullet points:

```tsx
export const CarouselSlide2: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COLORS.background }}>
    <GrainyOverlay opacity={0.04} />

    <div style={{
      position: "absolute",
      top: PADDING,
      left: PADDING,
      right: PADDING,
      bottom: PADDING,
      display: "flex",
      flexDirection: "column",
    }}>
      {/* Title */}
      <h2 style={{
        fontSize: 48,
        fontWeight: 600,
        color: COLORS.primary,
        textAlign: "center",
        margin: 0,
      }}>
        Slide Title Here
      </h2>

      {/* Illustration */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginTop: 40,
        marginBottom: 40,
      }}>
        <Img
          src={staticFile("images/instagram-ads/illustrations/content.png")}
          style={{ width: 380, height: 380, objectFit: "contain" }}
        />
      </div>

      {/* Bullet points */}
      <div style={{ display: "flex", flexDirection: "column", gap: 20, marginBottom: 40 }}>
        {[
          "First bullet point",
          "Second bullet point",
          "Third bullet point",
          "Fourth bullet point",
        ].map((item, i) => (
          <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
            <span style={{ color: COLORS.primary, fontSize: 36, fontWeight: 700 }}>•</span>
            <span style={{
              fontSize: 34,
              fontWeight: 600,
              color: COLORS.primary,
              lineHeight: 1.4,
            }}>
              {item}
            </span>
          </div>
        ))}
      </div>

      {/* Note (optional) */}
      <p style={{
        fontSize: 24,
        color: COLORS.primary,
        lineHeight: 1.5,
        marginTop: "auto",
        marginBottom: 20,
        fontFamily: "monospace",
      }}>
        Additional note or context here.
      </p>

      {/* Arrow indicator */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <ArrowIcon color={COLORS.primary} size={28} />
      </div>
    </div>
  </AbsoluteFill>
);
```

### 3. Paragraph Style Content

For text-heavy slides without bullets:

```tsx
export const CarouselParagraphSlide: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COLORS.secondary }}>
    <GrainyOverlay opacity={0.04} />

    <div style={{
      position: "absolute",
      top: PADDING,
      left: PADDING,
      right: PADDING,
      bottom: PADDING,
      display: "flex",
      flexDirection: "column",
    }}>
      <h2 style={{
        fontSize: 48,
        fontWeight: 600,
        color: COLORS.primary,
        textAlign: "center",
        margin: 0,
      }}>
        Slide Title
      </h2>

      {/* Centered paragraph content */}
      <div style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        textAlign: "center",
        gap: 30,
      }}>
        <p style={{
          fontSize: 36,
          fontWeight: 500,
          color: COLORS.background,
          lineHeight: 1.5,
          margin: 0,
        }}>
          Your paragraph text here. Use flowing sentences
          instead of bullet points for editorial content.
        </p>

        <Img
          src={staticFile("images/instagram-ads/illustrations/small-icon.png")}
          style={{ width: 280, height: 280, objectFit: "contain" }}
        />

        <p style={{
          fontSize: 34,
          fontWeight: 600,
          color: COLORS.primary,
          lineHeight: 1.4,
        }}>
          Key takeaway or<br />call to action.
        </p>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <ArrowIcon color={COLORS.background} size={28} />
      </div>
    </div>
  </AbsoluteFill>
);
```

### 4. CTA Slide (Last Slide)

```tsx
export const CarouselCTASlide: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COLORS.background }}>
    <GrainyOverlay opacity={0.04} />

    <div style={{
      position: "absolute",
      top: PADDING,
      left: PADDING,
      right: PADDING,
      bottom: PADDING,
      display: "flex",
      flexDirection: "column",
    }}>
      {/* Brand name */}
      <span style={{
        fontSize: 36,
        fontWeight: 600,
        color: COLORS.primary,
        textAlign: "center",
      }}>
        your.brand
      </span>

      {/* CTA Content */}
      <div style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 24,
      }}>
        {/* Logo */}
        <Img
          src={staticFile("your-logo.png")}
          style={{ height: 360, objectFit: "contain" }}
        />

        <h2 style={{
          fontSize: 52,
          fontWeight: 600,
          color: COLORS.primary,
          textAlign: "center",
          lineHeight: 1.2,
        }}>
          Your CTA Headline
        </h2>

        {/* CTA Button */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          backgroundColor: COLORS.primary,
          padding: "24px 48px",
          borderRadius: 60,
          marginTop: 10,
        }}>
          <span style={{
            fontSize: 36,
            fontWeight: 600,
            color: COLORS.background,
          }}>
            Link in Bio
          </span>
          <ArrowIcon color={COLORS.background} size={32} />
        </div>
      </div>

      {/* Tagline */}
      <p style={{
        fontSize: 26,
        color: COLORS.primary,
        textAlign: "center",
        fontFamily: "monospace",
      }}>
        Your brand tagline
      </p>
    </div>
  </AbsoluteFill>
);
```

---

## Arrow Icon Component

```tsx
const ArrowIcon: React.FC<{ color?: string; size?: number }> = ({
  color = "#ffffff",
  size = 28
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

---

## Grainy Overlay

```tsx
const GrainyOverlay: React.FC<{ opacity?: number }> = ({ opacity = 0.04 }) => {
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
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage: `url("data:image/svg+xml,${encodeURIComponent(noiseFilter)}")`,
        backgroundRepeat: "repeat",
        opacity,
        mixBlendMode: "overlay",
        pointerEvents: "none",
      }}
    />
  );
};
```

**Opacity guide:**
- Dark backgrounds: `0.05`
- Light backgrounds: `0.04`

---

## Typography Specs

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Badge/Category | 36px | 500 | 1.2 |
| Headline H1 | 58px | 600 | 1.15 |
| Headline H2 | 48-52px | 600 | 1.2 |
| Subheadline | 44-48px | 500 | 1.3 |
| Bullets | 30-34px | 500-600 | 1.4 |
| Note/Footer | 24-26px | 400 | 1.5 |
| CTA Button | 36px | 600 | 1.0 |

---

## Background Rotation

Alternate backgrounds across slides for visual variety:

| Slide | Background |
|-------|------------|
| Slide 1 | Primary color |
| Slide 2 | Light background |
| Slide 3 | Secondary color |
| Slide 4 | Primary color |
| Slide 5 (CTA) | Light background |

---

## Registering Compositions

In `remotion/Root.tsx`:

```tsx
import { Composition } from "remotion";
import {
  CarouselSlide1,
  CarouselSlide2,
  CarouselSlide3,
  CarouselSlide4,
  CarouselSlide5,
} from "./compositions/CarouselExample";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="CarouselExample-Slide1"
      component={CarouselSlide1}
      durationInFrames={1}
      fps={1}
      width={1080}
      height={1350}
    />
    <Composition
      id="CarouselExample-Slide2"
      component={CarouselSlide2}
      durationInFrames={1}
      fps={1}
      width={1080}
      height={1350}
    />
    {/* ... repeat for all slides */}
  </>
);
```

---

## Rendering Workflow

### Single Slide

```bash
mkdir -p public/images/instagram-carousels/example

npx remotion still remotion/index.ts "CarouselExample-Slide1" \
  "public/images/instagram-carousels/example/slide1.png" --overwrite
```

### Batch Render All Slides

```bash
mkdir -p public/images/instagram-carousels/example

for i in 1 2 3 4 5; do
  npx remotion still remotion/index.ts "CarouselExample-Slide$i" \
    "public/images/instagram-carousels/example/slide$i.png" --overwrite
done
```

### Parallel Rendering

```bash
mkdir -p public/images/instagram-carousels/example

npx remotion still remotion/index.ts "CarouselExample-Slide1" "public/images/instagram-carousels/example/slide1.png" --overwrite &
npx remotion still remotion/index.ts "CarouselExample-Slide2" "public/images/instagram-carousels/example/slide2.png" --overwrite &
npx remotion still remotion/index.ts "CarouselExample-Slide3" "public/images/instagram-carousels/example/slide3.png" --overwrite &
npx remotion still remotion/index.ts "CarouselExample-Slide4" "public/images/instagram-carousels/example/slide4.png" --overwrite &
npx remotion still remotion/index.ts "CarouselExample-Slide5" "public/images/instagram-carousels/example/slide5.png" --overwrite &
wait
```

---

## File Structure

```
remotion/
  compositions/
    CarouselExample.tsx    # All slides for one carousel
  Root.tsx                 # Register compositions

public/
  images/
    instagram-carousels/
      example/             # One folder per carousel
        slide1.png
        slide2.png
        slide3.png
        slide4.png
        slide5.png
    instagram-ads/
      illustrations/       # Shared icons/illustrations
  your-logo.png            # Brand logo
```

---

## Pre-Upload Checklist

- [ ] Resolution is 1080×1350 (4:5)
- [ ] All text within 80px padding
- [ ] First slide is attention-grabbing
- [ ] Icons have proper margins (40px+)
- [ ] Grainy overlay on all slides
- [ ] Swipe indicators on slides 1-4
- [ ] CTA with button on final slide
- [ ] Brand logo visible and large
- [ ] Consistent color rotation
- [ ] 5-10 slides total
