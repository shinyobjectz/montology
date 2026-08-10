---
title: Local Assets Management
description: Organizing and using backgrounds, icons, and illustrations
section: assets
priority: low
tags: [assets, backgrounds, icons, illustrations, images]
---

# Local Assets for Instagram Ads

Guide for organizing and using backgrounds, icons, and illustrations in Remotion Instagram videos.

## Asset Directory Structure

```
public/
├── images/
│   └── instagram-ads/
│       ├── backgrounds/          # Full-screen backgrounds
│       │   ├── dots.png
│       │   ├── gradient.png
│       │   ├── solid-primary.png
│       │   └── grain.png
│       ├── icons/                # Small visual elements (64-256px)
│       │   ├── checkmark.svg
│       │   ├── warning.svg
│       │   └── arrow.svg
│       ├── illustrations/        # Medium-sized graphics (256-800px)
│       │   ├── ad-example/
│       │   │   └── final/        # Processed with transparent backgrounds
│       │   │       ├── hero.png
│       │   │       ├── problem1.png
│       │   │       └── solution.png
│       └── overlays/             # Transparent overlays
│           ├── vignette.png
│           └── noise.png
├── audio/
│   └── instagram-ads/
│       └── ad-example/           # Per-ad audio files
│           ├── ad-example-combined.mp3
│           ├── ad-example-info.json
│           └── ad-example-captions.json
└── your-logo.png
```

---

## Generating Backgrounds

### Background Generator Script

Create `scripts/generate-backgrounds.js`:

```javascript
const { createCanvas } = require("canvas");
const fs = require("fs");
const path = require("path");

// ============================================
// TODO: CONFIGURE YOUR BRAND COLORS
// ============================================
const COLORS = {
  primary: "#000000",                      // Your primary color
  primaryLight: "rgba(0, 0, 0, 0.35)",     // Primary with transparency
  primaryMedium: "rgba(0, 0, 0, 0.50)",
  background: "#ffffff",                    // Light background
  backgroundDark: "#f5f5f5",               // Darker variant
  white: "#ffffff",
};

// Dimensions
const WIDTH = 1080;
const HEIGHT = 1350;  // 4:5 for carousels, change to 1920 for reels

const OUTPUT_DIR = "public/images/instagram-ads/backgrounds";
// ============================================

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

function saveCanvas(canvas, filename) {
  const buffer = canvas.toBuffer("image/png");
  const filepath = path.join(OUTPUT_DIR, filename);
  fs.writeFileSync(filepath, buffer);
  console.log(`✓ Created ${filepath}`);
}

// 1. Dot pattern
function createDotPattern() {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = COLORS.background;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  const dotSize = 4;
  const spacing = 40;
  ctx.fillStyle = COLORS.primaryLight;

  for (let x = spacing / 2; x < WIDTH; x += spacing) {
    for (let y = spacing / 2; y < HEIGHT; y += spacing) {
      ctx.beginPath();
      ctx.arc(x, y, dotSize, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  saveCanvas(canvas, "dots.png");
}

// 2. Dense dots
function createDenseDots() {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = COLORS.background;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  const dotSize = 3;
  const spacing = 24;
  ctx.fillStyle = COLORS.primaryMedium;

  for (let x = spacing / 2; x < WIDTH; x += spacing) {
    for (let y = spacing / 2; y < HEIGHT; y += spacing) {
      ctx.beginPath();
      ctx.arc(x, y, dotSize, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  saveCanvas(canvas, "dots-dense.png");
}

// 3. Vertical gradient
function createGradient() {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  const gradient = ctx.createLinearGradient(0, 0, 0, HEIGHT);
  gradient.addColorStop(0, COLORS.background);
  gradient.addColorStop(1, COLORS.backgroundDark);

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  saveCanvas(canvas, "gradient.png");
}

// 4. Radial gradient
function createRadialGradient() {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  const gradient = ctx.createRadialGradient(
    WIDTH / 2, HEIGHT / 2, 0,
    WIDTH / 2, HEIGHT / 2, HEIGHT * 0.7
  );
  gradient.addColorStop(0, COLORS.background);
  gradient.addColorStop(1, COLORS.backgroundDark);

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  saveCanvas(canvas, "gradient-radial.png");
}

// 5. Solid primary
function createSolidPrimary() {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = COLORS.primary;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  saveCanvas(canvas, "solid-primary.png");
}

// 6. Primary with dots
function createPrimaryWithDots() {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = COLORS.primary;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  const dotSize = 3;
  const spacing = 20;
  ctx.fillStyle = "rgba(255, 255, 255, 0.15)";

  for (let x = spacing / 2; x < WIDTH; x += spacing) {
    for (let y = spacing / 2; y < HEIGHT; y += spacing) {
      ctx.beginPath();
      ctx.arc(x, y, dotSize, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  saveCanvas(canvas, "primary-dots.png");
}

// 7. Grain texture
function createGrainTexture() {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = COLORS.background;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  const imageData = ctx.getImageData(0, 0, WIDTH, HEIGHT);
  const data = imageData.data;

  for (let i = 0; i < data.length; i += 4) {
    const noise = (Math.random() - 0.5) * 20;
    data[i] = Math.min(255, Math.max(0, data[i] + noise));
    data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + noise));
    data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + noise));
  }

  ctx.putImageData(imageData, 0, 0);
  saveCanvas(canvas, "grain.png");
}

// 8. Diagonal lines
function createDiagonalLines() {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = COLORS.background;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  ctx.strokeStyle = COLORS.primaryLight;
  ctx.lineWidth = 2;

  const spacing = 30;
  for (let i = -HEIGHT; i < WIDTH + HEIGHT; i += spacing) {
    ctx.beginPath();
    ctx.moveTo(i, 0);
    ctx.lineTo(i + HEIGHT, HEIGHT);
    ctx.stroke();
  }

  saveCanvas(canvas, "lines-diagonal.png");
}

// Generate all
console.log("Generating backgrounds...\\n");
createDotPattern();
createDenseDots();
createGradient();
createRadialGradient();
createSolidPrimary();
createPrimaryWithDots();
createGrainTexture();
createDiagonalLines();
console.log("\\n✅ All backgrounds generated!");
```

Run: `node scripts/generate-backgrounds.js`

---

## Adding Decorative Borders

Use ImageMagick to add borders/frames:

```bash
# Add colored border as inner frame (keeps original dimensions)
magick -size 1080x1350 xc:"#YOUR_ACCENT_COLOR" \
  \( public/images/instagram-ads/backgrounds/dots.png -resize 1000x1270 \) \
  -gravity center -composite \
  public/images/instagram-ads/backgrounds/dots-framed.png

# Rounded corners version
magick -size 1080x1350 xc:"#YOUR_ACCENT_COLOR" \
  \( public/images/instagram-ads/backgrounds/dots.png -resize 1000x1270 \
     \( +clone -alpha extract -draw "fill black polygon 0,0 0,30 30,0 fill white circle 30,30 30,0" \
        \( +clone -flip \) -compose Multiply -composite \
        \( +clone -flop \) -compose Multiply -composite \
     \) -alpha off -compose CopyOpacity -composite \
  \) -gravity center -composite \
  public/images/instagram-ads/backgrounds/dots-rounded.png
```

---

## Generating AI Illustrations

### Using Gemini GFX (Optional)

If you have the Gemini GFX skill set up:

```bash
# Generate illustration with style reference
node .claude/skills/gemini-gfx/generate.js \
  --prompt "3D clay miniature model of [SUBJECT], soft matte ceramic finish" \
  --reference path/to/style-reference.png \
  --output public/images/instagram-ads/illustrations/ad-example/subject.png

# Process for transparent background (using u2net)
python3 .claude/skills/image-processor/process.py \
  public/images/instagram-ads/illustrations/ad-example/*.png \
  -d public/images/instagram-ads/illustrations/ad-example/final/
```

**Important:** Don't use `--transparent` flag for illustrations with internal white areas. Use u2net instead for intelligent background removal.

---

## Asset Manifest

Create `public/images/instagram-ads/assets.json`:

```json
{
  "backgrounds": [
    {
      "file": "dots.png",
      "width": 1080,
      "height": 1350,
      "brightness": "light",
      "tags": ["dots", "pattern", "light"]
    },
    {
      "file": "solid-primary.png",
      "width": 1080,
      "height": 1350,
      "brightness": "dark",
      "tags": ["solid", "brand", "dark"]
    }
  ],
  "illustrations": [
    {
      "file": "ad-example/final/hero.png",
      "width": 512,
      "height": 512,
      "hasTransparency": true,
      "tags": ["hero", "main"]
    }
  ]
}
```

### Asset Scanner Script

Create `scripts/scan-instagram-assets.js`:

```javascript
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ASSETS_DIR = 'public/images/instagram-ads';
const OUTPUT_FILE = path.join(ASSETS_DIR, 'assets.json');

function getImageDimensions(filePath) {
  try {
    const output = execSync(`sips -g pixelWidth -g pixelHeight "${filePath}" 2>/dev/null`, { encoding: 'utf8' });
    const width = parseInt(output.match(/pixelWidth: (\d+)/)?.[1] || 0);
    const height = parseInt(output.match(/pixelHeight: (\d+)/)?.[1] || 0);
    return { width, height };
  } catch {
    return { width: 0, height: 0 };
  }
}

function scanDirectory(dir, category) {
  const fullPath = path.join(ASSETS_DIR, dir);
  if (!fs.existsSync(fullPath)) {
    fs.mkdirSync(fullPath, { recursive: true });
    return [];
  }

  const files = fs.readdirSync(fullPath).filter(f =>
    /\.(png|jpg|jpeg|svg|webp)$/i.test(f)
  );

  return files.map(file => {
    const filePath = path.join(fullPath, file);
    const { width, height } = getImageDimensions(filePath);
    return {
      file,
      width,
      height,
      tags: file.replace(/[-_]/g, ' ').replace(/\.\w+$/, '').split(' '),
    };
  });
}

const manifest = {
  generatedAt: new Date().toISOString(),
  backgrounds: scanDirectory('backgrounds', 'backgrounds'),
  icons: scanDirectory('icons', 'icons'),
  illustrations: scanDirectory('illustrations', 'illustrations'),
  overlays: scanDirectory('overlays', 'overlays'),
};

fs.writeFileSync(OUTPUT_FILE, JSON.stringify(manifest, null, 2));
console.log(`✓ Manifest: ${OUTPUT_FILE}`);
console.log(`  Backgrounds: ${manifest.backgrounds.length}`);
console.log(`  Icons: ${manifest.icons.length}`);
console.log(`  Illustrations: ${manifest.illustrations.length}`);
```

Run: `node scripts/scan-instagram-assets.js`

---

## Using Assets in Remotion

### Background Usage

```tsx
import { AbsoluteFill, Img, staticFile } from "remotion";

export const SceneWithBackground: React.FC<{
  background?: string;
}> = ({ background = "backgrounds/dots.png" }) => (
  <AbsoluteFill>
    <Img
      src={staticFile(`images/instagram-ads/${background}`)}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
      }}
    />
    {/* Content goes here */}
  </AbsoluteFill>
);
```

### Animated Icon

```tsx
import { Img, staticFile, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface AnimatedIconProps {
  icon: string;
  size: number;
  delay?: number;
}

export const AnimatedIcon: React.FC<AnimatedIconProps> = ({
  icon,
  size,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame: frame - delay,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  const opacity = spring({
    frame: frame - delay,
    fps,
    config: { damping: 20, stiffness: 80 },
  });

  return (
    <Img
      src={staticFile(`images/instagram-ads/${icon}`)}
      style={{
        width: size,
        height: size,
        objectFit: "contain",
        transform: `scale(${scale})`,
        opacity,
      }}
    />
  );
};
```

### Icon Registry Pattern

```tsx
// Define all icons in one place
const ICONS = {
  hero: "illustrations/ad-example/final/hero.png",
  problem1: "illustrations/ad-example/final/problem1.png",
  problem2: "illustrations/ad-example/final/problem2.png",
  solution: "illustrations/ad-example/final/solution.png",
  cta: "illustrations/ad-example/final/cta.png",
};

// Icon component with registry
const Icon: React.FC<{ name: keyof typeof ICONS; size?: number }> = ({
  name,
  size = 80
}) => (
  <Img
    src={staticFile(`images/instagram-ads/${ICONS[name]}`)}
    style={{
      width: size,
      height: size,
      objectFit: "contain",
    }}
  />
);

// Usage
<Icon name="hero" size={180} />
```

---

## Icon Sizing Guidelines

| Context | Size | Notes |
|---------|------|-------|
| Hero/Hook (Scene 1) | 160-240px | Large, attention-grabbing |
| Problem list items | 55-75px | Inline with text |
| Feature highlight | 60-100px | Medium emphasis |
| Solution/CTA | 140-180px | Large, prominent |
| Decorative | 32-48px | Background accents |

---

## Asset Sizing Guidelines

| Asset Type | Recommended Size | Max File Size |
|------------|-----------------|---------------|
| Backgrounds | 1080×1920px or 1080×1350px | 500KB |
| Icons | 128×128px (SVG preferred) | 20KB |
| Illustrations | 512-800px width | 200KB |
| Overlays | 1080×1920px | 100KB |

---

## Best Practices

1. **Use SVG for icons** - Scales without quality loss
2. **Compress PNGs** with tools like `pngquant`
3. **Consistent naming** - Use kebab-case (e.g., `hero-icon.png`)
4. **Organize by ad** - One folder per ad campaign
5. **Keep total assets under 5MB** per video
6. **Use `staticFile()`** for all asset paths in Remotion
