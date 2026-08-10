---
title: Project Setup Guide
description: Initial project configuration, dependencies, and folder structure
section: setup
priority: high
tags: [setup, installation, dependencies, configuration]
---

# Project Setup Guide

Complete setup guide for using the remotion-ads skill in your project.

## Prerequisites

- Node.js 18+
- npm or pnpm
- Remotion installed in your project

## Step 1: Install Dependencies

```bash
# Core Remotion packages
npm install remotion @remotion/cli @remotion/bundler

# Google Fonts (for typography)
npm install @remotion/google-fonts

# Captions support
npx remotion add @remotion/captions

# Canvas for background generation (optional)
npm install canvas
```

## Step 2: Configure Brand Design System

1. Copy the template:
   ```bash
   cp .claude/skills/remotion-ads/rules/design-system-template.md \
      .claude/skills/remotion-ads/rules/design-system.md
   ```

2. Edit `design-system.md` with your brand values:
   - Colors (primary, secondary, background, etc.)
   - Fonts (heading, body)
   - Logo path
   - Icon paths

## Step 3: Create Asset Directory Structure

```bash
mkdir -p public/images/instagram-ads/{backgrounds,icons,illustrations,overlays}
mkdir -p public/audio/instagram-ads
```

## Step 4: Generate Background Patterns (Optional)

If your design uses patterned backgrounds (dots, gradients, grain), create a `scripts/generate-backgrounds.js` in your project. This script is **not included** in the skill — copy the code below and customize the colors:

```javascript
const { createCanvas } = require("canvas");
const fs = require("fs");
const path = require("path");

// ============================================
// CONFIGURE YOUR BRAND COLORS HERE
// ============================================
const COLORS = {
  primary: "#YOUR_PRIMARY_COLOR",           // Main brand color
  primaryLight: "rgba(R, G, B, 0.35)",      // Primary with opacity
  primaryMedium: "rgba(R, G, B, 0.50)",
  background: "#YOUR_BACKGROUND_COLOR",     // Light background
  backgroundDark: "#YOUR_DARK_BG",          // Darker variant
  white: "#ffffff",
};

// Dimensions (Instagram carousel = 4:5)
const WIDTH = 1080;
const HEIGHT = 1350;  // Change to 1920 for Reels

const OUTPUT_DIR = "public/images/instagram-ads/backgrounds";

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

function saveCanvas(canvas, filename) {
  const buffer = canvas.toBuffer("image/png");
  const filepath = path.join(OUTPUT_DIR, filename);
  fs.writeFileSync(filepath, buffer);
  console.log(`✓ Created ${filepath}`);
}

// Dot pattern
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

// Gradient background
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

// Solid primary color
function createSolidPrimary() {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = COLORS.primary;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  saveCanvas(canvas, "solid-primary.png");
}

// Grain texture
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

// Generate all backgrounds
console.log("Generating backgrounds...\\n");
createDotPattern();
createGradient();
createSolidPrimary();
createGrainTexture();
console.log("\\n✅ All backgrounds generated!");
```

Run: `node scripts/generate-backgrounds.js`

## Step 5: Create Asset Scanner (Optional)

If you want an auto-generated manifest of your image assets, create a `scripts/scan-instagram-assets.js` in your project. This script is **not included** in the skill — copy the code below:

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
    return { file, width, height, category };
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
console.log(`✓ Asset manifest written to ${OUTPUT_FILE}`);
console.log(`  Backgrounds: ${manifest.backgrounds.length}`);
console.log(`  Icons: ${manifest.icons.length}`);
console.log(`  Illustrations: ${manifest.illustrations.length}`);
console.log(`  Overlays: ${manifest.overlays.length}`);
```

Run: `node scripts/scan-instagram-assets.js`

## Step 6: Create Remotion Config

Create `remotion.config.ts`:

```typescript
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
```

## Step 7: Register Compositions

In `remotion/Root.tsx`:

```tsx
import { Composition } from "remotion";
import { AdExample } from "./compositions/AdExample";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Reels (9:16) */}
      <Composition
        id="AdExample"
        component={AdExample}
        durationInFrames={450}  // 15 seconds at 30fps
        fps={30}
        width={1080}
        height={1920}
      />

      {/* Carousels (4:5) - register each slide */}
      <Composition
        id="CarouselExample-Slide1"
        component={CarouselSlide1}
        durationInFrames={1}
        fps={1}
        width={1080}
        height={1350}
      />
      {/* ... more slides */}
    </>
  );
};
```

## Step 8: Environment Variables

Create `.env.local` in the **video app directory** (where `remotion.config.ts` lives):

```bash
# For voiceover generation (optional)
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# For AI icon generation (optional)
GEMINI_API_KEY=your_gemini_api_key
```

### Monorepo Tips

In a monorepo, the API key may already exist in another app (e.g., `apps/web/.env`). The `tools/generate.js` script reads the key from `process.env.ELEVENLABS_API_KEY`, so you have a few options:

1. **Copy the key** to a `.env.local` in your video app directory
2. **Symlink the file**: `ln -s ../web/.env .env.local`
3. **Pass it inline** when running the tool:
   ```bash
   ELEVENLABS_API_KEY=sk_... node tools/generate.js --scenes scenes.json --output-dir public/audio/
   ```
4. **Export it** in your shell session before running commands:
   ```bash
   export ELEVENLABS_API_KEY=sk_...
   ```

Check these common locations for existing keys:
- `apps/web/.env` or `apps/web/.env.local`
- `.env` at the monorepo root
- `apps/mobile/.env` or `apps/mobile/app.json` (for Expo projects)

## Verification Checklist

- [ ] Remotion dependencies installed
- [ ] Design system configured with brand colors/fonts
- [ ] Asset directories created
- [ ] Background patterns generated
- [ ] Asset manifest created
- [ ] Remotion config file created
- [ ] Compositions registered in Root.tsx
- [ ] Environment variables set (if using voiceover/AI features)

## Quick Test

```bash
# Start Remotion studio
npx remotion studio

# Render a test video
npx remotion render AdExample out/test.mp4 --codec=h264

# Render a carousel slide
npx remotion still CarouselExample-Slide1 out/slide1.png
```

## Troubleshooting

### "Canvas not found"
```bash
npm install canvas
```

### "Font not loading"
Ensure Google Fonts are imported correctly:
```tsx
import { loadFont } from "@remotion/google-fonts/YourFont";
const { fontFamily } = loadFont();
```

### "Asset not found"
Check paths use `staticFile()`:
```tsx
import { staticFile } from "remotion";
<Img src={staticFile("images/instagram-ads/icons/your-icon.png")} />
```
