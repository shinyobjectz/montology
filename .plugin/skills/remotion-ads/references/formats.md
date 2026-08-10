---
title: Instagram Display Formats
description: Display formats, dimensions, and safe zones for Instagram Reels
section: formats
priority: high
tags: [dimensions, safe-zones, formats, instagram, reels]
---

# Instagram Display Formats

Instagram shows Reels in multiple formats. Design for all three to ensure visibility.

---

## Format Overview

| Format | Aspect Ratio | Dimensions | Where Shown |
|--------|--------------|------------|-------------|
| **Full-screen Reels** | 9:16 | 1080×1920 | Reels tab, Stories |
| **Feed Preview** | 4:5 | 1080×1350 | Main feed (MOST COMMON) |
| **Profile Grid** | 1:1 | 1080×1080 | Profile page grid |

---

## 1. Full-screen Reels Tab (9:16)

The native Reels viewing experience.

```
Canvas: 1080×1920px (full resolution)
UI overlay: Bottom ~10-15% (y > 1630-1725px)
Shows: Complete video content
```

### What's Visible
- Full video frame
- UI elements overlay bottom portion
- Username, like/comment/share buttons visible

### Safe Zones
```
Top: 0-285px (username, system UI)
Bottom: 1520-1920px (buttons, captions, audio)
Sides: 80px left, 120px right
```

---

## 2. Feed Preview (4:5) - MOST COMMON

How most users first see your Reel in their feed.

```
Shows: 1080×1350px (centered)
Crops: ~285px from top AND bottom of 9:16 canvas
Users must tap to see full video
```

### Visual Representation

```
Original 9:16 (1080×1920)        Feed 4:5 Preview (1080×1350)
┌─────────────────────────┐
│     CROPPED (285px)     │
│.........................│      ┌─────────────────────────┐
│                         │      │                         │
│                         │      │                         │
│    VISIBLE IN FEED      │  →   │    VISIBLE IN FEED      │
│       PREVIEW           │      │       PREVIEW           │
│                         │      │                         │
│                         │      │                         │
│.........................│      └─────────────────────────┘
│     CROPPED (285px)     │
└─────────────────────────┘
```

### Critical Implication
**Key content must be within y = 285px to y = 1635px** to be visible in the feed preview.

---

## 3. Profile Grid (1:1)

Thumbnail shown on profile page.

```
Shows: Central 1080×1080 square
Crops: ~420px from top AND bottom
Used for: Profile grid thumbnails
```

### Visual Representation

```
Original 9:16 (1080×1920)        Grid 1:1 Preview (1080×1080)
┌─────────────────────────┐
│     CROPPED (420px)     │
│.........................│      ┌─────────────────────────┐
│                         │      │                         │
│   VISIBLE IN GRID       │  →   │   VISIBLE IN GRID       │
│      THUMBNAIL          │      │      THUMBNAIL          │
│                         │      │                         │
│.........................│      └─────────────────────────┘
│     CROPPED (420px)     │
└─────────────────────────┘
```

### Critical Implication
**Brand logos and key visuals must be within y = 420px to y = 1500px** to be visible in grid thumbnails.

---

## Multi-Format Safe Design

### Remotion Constants

```tsx
export const INSTAGRAM_FORMATS = {
  // Full-screen Reels (9:16)
  reels: {
    width: 1080,
    height: 1920,
    aspectRatio: "9:16",
  },

  // Feed Preview (4:5) - crops top and bottom
  feedPreview: {
    width: 1080,
    height: 1350,
    cropTop: 285,
    cropBottom: 285,  // 1920 - 285 - 1350 = 285
  },

  // Grid Preview (1:1) - crops more
  gridPreview: {
    width: 1080,
    height: 1080,
    cropTop: 420,
    cropBottom: 420,  // 1920 - 420 - 1080 = 420
  },

  // Content visible in ALL formats
  universalSafe: {
    minY: 420,   // Below 1:1 top crop
    maxY: 1500,  // Above 1:1 bottom crop
    minX: 80,
    maxX: 1000,
    width: 920,
    height: 1080,
  },

  // Branding zone (visible in grid thumbnail)
  brandingZone: {
    x: 0,
    y: 420,
    width: 1080,
    height: 1080,  // Center 1:1 square
  },
};
```

### Zone Visualization

```
┌─────────────────────────────────────┐ 0px
│                                     │
│        ⚠️ TOP CROP ZONE            │ } 285px (4:5 crop)
│        (not in feed preview)        │
├─────────────────────────────────────┤ 285px
│                                     │
│   ⚠️ EXTRA TOP CROP (GRID ONLY)    │ } 135px more (1:1 crop)
│                                     │
├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤ 420px
│                                     │
│                                     │
│    ✅ UNIVERSAL SAFE ZONE          │
│       (visible in ALL formats)      │
│                                     │
│    Place: Logo, key messages,       │
│    faces, important visuals         │
│                                     │
│                                     │
├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤ 1500px
│                                     │
│   ⚠️ EXTRA BOTTOM CROP (GRID ONLY) │ } 135px more (1:1 crop)
│                                     │
├─────────────────────────────────────┤ 1635px
│                                     │
│       ⚠️ BOTTOM CROP ZONE          │ } 285px (4:5 crop)
│       (not in feed preview)         │
│                                     │
└─────────────────────────────────────┘ 1920px
```

---

## Format-Specific Components

### Universal Safe Area Component

```tsx
/**
 * Content placed here is visible in ALL Instagram formats:
 * - Full-screen Reels (9:16)
 * - Feed preview (4:5)
 * - Profile grid (1:1)
 */
export const UniversalSafeArea: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{
    position: "absolute",
    top: 420,      // Below 1:1 top crop
    bottom: 420,   // Above 1:1 bottom crop
    left: 80,      // Side margin
    right: 120,    // Right margin (action buttons)
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
  }}>
    {children}
  </div>
);
```

### Feed Preview Safe Area Component

```tsx
/**
 * Content placed here is visible in:
 * - Full-screen Reels (9:16)
 * - Feed preview (4:5)
 * NOT visible in profile grid (1:1)
 */
export const FeedSafeArea: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{
    position: "absolute",
    top: 285,      // Below 4:5 top crop
    bottom: 285,   // Above 4:5 bottom crop
    left: 80,
    right: 120,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
  }}>
    {children}
  </div>
);
```

---

## Debug Overlay for Format Testing

```tsx
export const FormatDebugOverlay: React.FC = () => (
  <>
    {/* 4:5 Feed crop lines */}
    <div style={{
      position: "absolute",
      top: 285, left: 0, right: 0,
      height: 2,
      backgroundColor: "rgba(255,165,0,0.8)",
    }} />
    <div style={{
      position: "absolute",
      top: 285, left: 10,
      color: "orange",
      fontSize: 18,
      fontWeight: "bold",
    }}>
      4:5 FEED CROP (285px)
    </div>
    <div style={{
      position: "absolute",
      bottom: 285, left: 0, right: 0,
      height: 2,
      backgroundColor: "rgba(255,165,0,0.8)",
    }} />

    {/* 1:1 Grid crop lines */}
    <div style={{
      position: "absolute",
      top: 420, left: 0, right: 0,
      height: 2,
      backgroundColor: "rgba(0,255,0,0.8)",
    }} />
    <div style={{
      position: "absolute",
      top: 420, left: 10,
      color: "lime",
      fontSize: 18,
      fontWeight: "bold",
    }}>
      1:1 GRID CROP (420px)
    </div>
    <div style={{
      position: "absolute",
      bottom: 420, left: 0, right: 0,
      height: 2,
      backgroundColor: "rgba(0,255,0,0.8)",
    }} />

    {/* Center marker */}
    <div style={{
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
      width: 20,
      height: 20,
      borderRadius: "50%",
      backgroundColor: "rgba(255,0,0,0.8)",
    }} />
  </>
);
```

---

## Cover/Thumbnail Design

### Dimensions

```
Design at: 1080×1920 (matches Reel)
Grid display: Center 1080×1080 will be shown
Alternative spec: 420×654px (1:1.55 ratio)
```

### Cover Best Practices

1. **Center key elements** within middle 1080×1080 square
2. **Ensure titles/faces/logos** visible in 1:1 crop
3. **Design for both** 9:16 (Reels tab) and 1:1 (grid) views
4. **Test thumbnail** in both formats before posting
5. **Use high contrast** text that's readable at small sizes

### Cover Zone Component

```tsx
/**
 * Wrapper for content that should be visible
 * in profile grid thumbnails
 */
export const CoverSafeZone: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{
    position: "absolute",
    top: 420,
    left: 0,
    right: 0,
    height: 1080,  // 1:1 square
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "0 80px",
  }}>
    {children}
  </div>
);
```

---

## Content Placement Strategy

### By Content Type

| Content | Zone | Y Range | Why |
|---------|------|---------|-----|
| Logo | Universal | 420-1500px | Visible in grid thumbnail |
| Main headline | Universal | 420-1500px | Visible everywhere |
| Hook text | Feed | 300-600px | Grabs attention, ok if cropped in grid |
| Problem list | Feed | 500-1200px | Main content area |
| Solution | Universal | 700-1200px | Key message visible everywhere |
| CTA | Universal | 600-1000px | Must be visible everywhere |
| Captions | Feed | 1300-1600px | Above bottom UI, below grid crop |

### Scene-by-Scene Recommendations

| Scene | Primary Zone | Reason |
|-------|--------------|--------|
| Hook (Scene 1) | Universal | First impression in grid thumbnail |
| Problem (Scene 2) | Feed | Can use more vertical space |
| Solution (Scene 3) | Universal | Key message must be visible |
| CTA (Scene 4) | Universal | Logo/CTA must be in grid thumbnail |

---

## Export & Testing

### Preview Crops in Remotion Studio

```tsx
// Add to your composition for testing
const showCropGuides = true; // Set to false for production

{showCropGuides && <FormatDebugOverlay />}
```

### Manual Testing Checklist

- [ ] Open in Remotion Studio at 1080×1920
- [ ] Check content at y = 285-1635 (4:5 preview)
- [ ] Check content at y = 420-1500 (1:1 grid)
- [ ] Logo visible in center 1080×1080 square
- [ ] Key text readable in all formats
- [ ] Upload test to Instagram and verify in:
  - Feed preview
  - Full-screen Reels
  - Profile grid

---

## Quick Reference

### Safe Y Coordinates

| Zone | Min Y | Max Y | Height |
|------|-------|-------|--------|
| Full Reels | 0 | 1920 | 1920px |
| Feed Preview | 285 | 1635 | 1350px |
| Grid Thumbnail | 420 | 1500 | 1080px |
| Universal Safe | 420 | 1500 | 1080px |

### Critical Numbers to Remember

```
285px - Feed preview starts/ends here
420px - Grid thumbnail starts/ends here
540px - Center of feed preview (285 + 675)
960px - True center of canvas (1920/2)
1080px - Grid thumbnail height
1350px - Feed preview height
```
