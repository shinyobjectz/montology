#!/usr/bin/env npx tsx
/**
 * Suno Music Generator via browser-use API
 *
 * Generates AI background music using the Suno skill through browser-use.
 * Supports automatic artist/song style conversion to avoid trademark issues.
 *
 * Usage:
 *   npx tsx tools/suno-direct.ts --prompt "..." --tags "..." --output file.mp3
 *   npx tsx tools/suno-direct.ts --prompt "In the style of Tom Misch" -i -o background.mp3
 *
 * Environment variables (in .env.local):
 *   BROWSER_USE_API_KEY - Your browser-use API key
 *   SUNO_API_KEY - Your Suno authorization token (from browser DevTools)
 */

import * as fs from "fs";
import * as https from "https";
import * as path from "path";
import { execSync } from "child_process";

// ============================================
// ARTIST STYLE MAPPINGS (removes trademarks)
// ============================================

const ARTIST_STYLES: Record<string, string> = {
  "tom misch": "groovy electric guitar, jazzy neo-soul funk, laid-back pocket groove, warm analog production, sophisticated jazz chords",
  "lana del rey": "dreamy cinematic pop, melancholic vocals, vintage Americana, orchestral arrangements, nostalgic atmosphere",
  "daft punk": "French house, vocoder vocals, disco funk, robotic themes, groovy basslines, retro-futuristic",
  "hans zimmer": "epic cinematic scores, powerful orchestration, electronic elements, dramatic builds, emotional themes",
  "billie eilish": "dark whisper-pop, minimalist beats, atmospheric production, ASMR-like vocals, brooding mood",
  "the weeknd": "dark R&B, 80s synth-pop revival, falsetto vocals, nocturnal atmosphere, retro production",
  "tame impala": "psychedelic pop, swirling synths, dreamy vocals, retro production, hypnotic grooves",
  "coldplay": "atmospheric rock, piano-driven melodies, uplifting crescendos, emotional lyrics, ambient textures",
  "ed sheeran": "acoustic folk-pop, heartfelt lyrics, loop pedal layering, intimate singer-songwriter style",
  "bruno mars": "retro funk-pop, smooth R&B, 70s soul influence, upbeat grooves, polished production",
  "queen": "operatic rock, multi-layered harmonies, theatrical arrangements, guitar-driven anthems",
  "pink floyd": "progressive rock, atmospheric soundscapes, philosophical themes, long instrumental passages",
  "kendrick lamar": "conscious hip-hop, complex wordplay, jazz influences, storytelling, innovative production",
  "frank ocean": "alternative R&B, introspective lyrics, experimental production, emotional depth, atmospheric",
  "radiohead": "experimental rock, electronic elements, complex arrangements, melancholic atmosphere",
  "bon iver": "indie folk, falsetto vocals, atmospheric production, introspective lyrics, ethereal soundscapes",
  "ludovico einaudi": "minimalist piano, emotional simplicity, meditative quality, cinematic atmosphere",
};

// ============================================
// CONFIGURATION
// ============================================

interface Config {
  browserUseApiKey: string;
  sunoToken: string;
}

function loadConfig(envPath?: string): Config {
  // Try multiple env file locations
  const envPaths = [
    envPath,
    path.join(process.cwd(), ".env.local"),
    path.join(process.cwd(), ".env"),
  ].filter(Boolean) as string[];

  let envVars: Record<string, string> = {};

  for (const p of envPaths) {
    if (fs.existsSync(p)) {
      const content = fs.readFileSync(p, "utf-8");
      content.split("\n").forEach((line) => {
        const match = line.match(/^([^=]+)=(.*)$/);
        if (match) {
          const key = match[1].trim();
          let value = match[2].trim();
          // Remove quotes if present
          if ((value.startsWith('"') && value.endsWith('"')) ||
              (value.startsWith("'") && value.endsWith("'"))) {
            value = value.slice(1, -1);
          }
          envVars[key] = value;
        }
      });
      break;
    }
  }

  // Also check process.env
  const browserUseApiKey = envVars.BROWSER_USE_API_KEY || process.env.BROWSER_USE_API_KEY || "";
  const sunoToken = envVars.SUNO_API_KEY || envVars.SUNO_AUTH_TOKEN ||
                    process.env.SUNO_API_KEY || process.env.SUNO_AUTH_TOKEN || "";

  return { browserUseApiKey, sunoToken };
}

// ============================================
// ARTIST STYLE CONVERSION
// ============================================

function convertArtistReferences(prompt: string, tags: string): { prompt: string; tags: string; converted: boolean } {
  let converted = false;
  let newPrompt = prompt;
  let newTags = tags;

  const promptLower = prompt.toLowerCase();
  const tagsLower = tags.toLowerCase();

  for (const [artist, style] of Object.entries(ARTIST_STYLES)) {
    if (promptLower.includes(artist)) {
      console.log(`   🎭 Detected artist: "${artist}"`);
      console.log(`   🔄 Converting to: ${style.substring(0, 50)}...`);

      const regex = new RegExp(artist, "gi");
      newPrompt = newPrompt.replace(regex, `[${style}]`);

      // Add first 3 style descriptors to tags
      const styleTags = style.split(", ").slice(0, 3).join(", ");
      newTags = `${newTags}, ${styleTags}`;
      converted = true;
    }

    if (tagsLower.includes(artist)) {
      const regex = new RegExp(artist, "gi");
      const styleTags = style.split(", ").slice(0, 4).join(", ");
      newTags = newTags.replace(regex, styleTags);
      converted = true;
    }
  }

  // Clean up double commas
  newTags = newTags.replace(/,\s*,/g, ",").replace(/\s+/g, " ").trim();

  return { prompt: newPrompt, tags: newTags, converted };
}

// ============================================
// AUDIO POST-PROCESSING
// ============================================

function applyFadeOut(inputPath: string, outputPath: string, fadeDuration: number = 1): void {
  // Get audio duration using ffprobe
  try {
    const durationOutput = execSync(
      `ffprobe -v error -show_entries format=duration -of csv=p=0 "${inputPath}"`,
      { encoding: "utf-8" }
    ).trim();
    const duration = parseFloat(durationOutput);

    if (isNaN(duration)) {
      console.log("   ⚠️ Could not determine audio duration, skipping fade out");
      return;
    }

    const fadeStart = Math.max(0, duration - fadeDuration);

    console.log(`   🎚️ Applying ${fadeDuration}s smooth fade out (starting at ${fadeStart.toFixed(1)}s)...`);

    // Use exponential curve (exp) for smoother, more natural sounding fade
    // Also apply a gentle volume reduction in the last portion for extra smoothness
    execSync(
      `ffmpeg -i "${inputPath}" -af "afade=t=out:st=${fadeStart}:d=${fadeDuration}:curve=exp" -y "${outputPath}"`,
      { stdio: "pipe" }
    );

    // Replace original with faded version
    fs.unlinkSync(inputPath);
    fs.renameSync(outputPath, inputPath);

    console.log(`   ✅ Smooth fade out applied`);
  } catch (error) {
    console.log(`   ⚠️ Could not apply fade out: ${(error as Error).message}`);
  }
}

// ============================================
// FILE DOWNLOAD
// ============================================

async function downloadFile(url: string, outputPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    // Ensure directory exists
    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const file = fs.createWriteStream(outputPath);

    const request = (urlStr: string) => {
      https.get(urlStr, (response) => {
        // Handle redirects
        if (response.statusCode === 301 || response.statusCode === 302) {
          const redirectUrl = response.headers.location;
          if (redirectUrl) {
            request(redirectUrl);
            return;
          }
        }

        if (response.statusCode !== 200) {
          reject(new Error(`HTTP ${response.statusCode}`));
          return;
        }

        response.pipe(file);
        file.on("finish", () => {
          file.close();
          resolve();
        });
      }).on("error", (err) => {
        fs.unlink(outputPath, () => {});
        reject(err);
      });
    };

    request(url);
  });
}

// ============================================
// SUNO GENERATION
// ============================================

interface SunoClip {
  id: string;
  title: string;
  status: string;
  audio_url: string;
  video_url: string;
  image_url: string;
  duration: number | null;
  tags: string;
}

interface SunoResult {
  success: boolean;
  result?: {
    success: boolean;
    data?: {
      clips: SunoClip[];
      generation_id: string;
      count: number;
      message: string;
    };
    error?: {
      code: string;
      message: string;
    };
  };
  error?: string;
}

async function generateMusic(
  config: Config,
  prompt: string,
  tags: string,
  instrumental: boolean,
  title?: string
): Promise<SunoResult> {
  const requestBody = {
    parameters: {
      authorization_token: config.sunoToken.startsWith("Bearer ")
        ? config.sunoToken
        : `Bearer ${config.sunoToken}`,
      prompt,
      tags,
      make_instrumental: instrumental,
      ...(title && { title }),
    },
  };

  const response = await fetch(
    "https://api.browser-use.com/api/v2/skills/b3bafbfe-b785-41e6-a604-1f2c2102bffc/execute",
    {
      method: "POST",
      headers: {
        "X-Browser-Use-API-Key": config.browserUseApiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    }
  );

  const result = await response.json() as SunoResult;
  return result;
}

// ============================================
// CLI
// ============================================

function printUsage() {
  console.log(`
Suno Music Generator

Usage:
  npx tsx tools/suno-direct.ts [options]

Options:
  -p, --prompt <text>     Music description (required)
  -t, --tags <tags>       Style tags (comma-separated)
  -i, --instrumental      Generate without vocals (default: true)
  -o, --output <path>     Output file path
  --title <title>         Song title
  --fade <seconds>        Smooth fade out at end (default: 1, uses exp curve, 0 to disable)
  --env <path>            Path to .env file
  -h, --help              Show this help

Examples:
  npx tsx tools/suno-direct.ts -p "Ambient cinematic" -t "ambient, professional" -o bg.mp3
  npx tsx tools/suno-direct.ts -p "In the style of Tom Misch" -i -o groovy.mp3 --fade 2
`);
}

function parseArgs(args: string[]): Record<string, string | boolean | number> {
  const result: Record<string, string | boolean | number> = {
    instrumental: true,
    fade: 1, // Default 1 second smooth fade out (exponential curve)
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const next = args[i + 1];

    switch (arg) {
      case "-p":
      case "--prompt":
        result.prompt = next;
        i++;
        break;
      case "-t":
      case "--tags":
        result.tags = next;
        i++;
        break;
      case "-o":
      case "--output":
        result.output = next;
        i++;
        break;
      case "--title":
        result.title = next;
        i++;
        break;
      case "--env":
        result.env = next;
        i++;
        break;
      case "--fade":
        result.fade = parseFloat(next) || 0;
        i++;
        break;
      case "-i":
      case "--instrumental":
        result.instrumental = true;
        break;
      case "--no-instrumental":
        result.instrumental = false;
        break;
      case "-h":
      case "--help":
        result.help = true;
        break;
      default:
        // Positional args fallback
        if (!result.prompt && !arg.startsWith("-")) {
          result.prompt = arg;
        } else if (!result.tags && !arg.startsWith("-")) {
          result.tags = arg;
        } else if (!result.output && !arg.startsWith("-")) {
          result.output = arg;
        }
    }
  }

  return result;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    printUsage();
    process.exit(0);
  }

  if (!args.prompt) {
    console.error("❌ Error: --prompt is required");
    printUsage();
    process.exit(1);
  }

  // Load config
  const config = loadConfig(args.env as string | undefined);

  if (!config.browserUseApiKey) {
    console.error("❌ BROWSER_USE_API_KEY not found in environment");
    console.error("   Add it to .env.local: BROWSER_USE_API_KEY=your_key");
    process.exit(1);
  }

  if (!config.sunoToken) {
    console.error("❌ SUNO_API_KEY not found in environment");
    console.error("   Add it to .env.local: SUNO_API_KEY=your_token");
    console.error("");
    console.error("   To get your token:");
    console.error("   1. Go to suno.com and log in");
    console.error("   2. Open DevTools (F12) → Network tab");
    console.error("   3. Find a request to studio-api.suno.ai");
    console.error("   4. Copy the 'authorization' header value");
    process.exit(1);
  }

  let prompt = args.prompt as string;
  let tags = (args.tags as string) || "ambient, professional, instrumental";
  const instrumental = args.instrumental as boolean;
  const output = (args.output as string) || "suno-output.mp3";
  const title = args.title as string | undefined;
  const fadeDuration = args.fade as number;

  // Convert artist references
  console.log("\n🔍 Checking for artist references...");
  const conversion = convertArtistReferences(prompt, tags);
  if (conversion.converted) {
    prompt = conversion.prompt;
    tags = conversion.tags;
    console.log(`   ✅ Converted to style description`);
  } else {
    console.log("   No artist references detected");
  }

  console.log("\n🎵 Generating music...");
  console.log(`   Prompt: ${prompt.substring(0, 60)}${prompt.length > 60 ? "..." : ""}`);
  console.log(`   Tags: ${tags}`);
  console.log(`   Instrumental: ${instrumental}`);
  console.log();

  try {
    const result = await generateMusic(config, prompt, tags, instrumental, title);

    if (!result.success || !result.result?.success) {
      const errorMsg = result.result?.error?.message || result.error || "Unknown error";
      console.error(`❌ Generation failed: ${errorMsg}`);
      process.exit(1);
    }

    const clips = result.result.data?.clips || [];
    if (clips.length === 0) {
      console.error("❌ No clips generated");
      process.exit(1);
    }

    // Get unique clips (API sometimes returns duplicates)
    const uniqueClips = clips.filter(
      (clip, index, self) => index === self.findIndex((c) => c.id === clip.id)
    );

    console.log(`   ✅ Generated ${uniqueClips.length} clip(s)`);

    // Download the first clip
    const clip = uniqueClips[0];
    if (clip.audio_url) {
      console.log(`\n📥 Downloading audio...`);
      await downloadFile(clip.audio_url, output);
      let stats = fs.statSync(output);
      let sizeKB = (stats.size / 1024).toFixed(1);
      console.log(`   ✅ Saved: ${output} (${sizeKB} KB)`);

      // Apply fade out if requested
      if (fadeDuration > 0) {
        const tempOutput = output.replace(/(\.[^.]+)$/, "-faded$1");
        applyFadeOut(output, tempOutput, fadeDuration);
        stats = fs.statSync(output);
        sizeKB = (stats.size / 1024).toFixed(1);
      }

      // Save metadata
      const infoPath = output.replace(/\.[^.]+$/, "-info.json");
      const info = {
        prompt,
        tags,
        instrumental,
        clip_id: clip.id,
        audio_url: clip.audio_url,
        generation_id: result.result.data?.generation_id,
        generated_at: new Date().toISOString(),
      };
      fs.writeFileSync(infoPath, JSON.stringify(info, null, 2));
      console.log(`   📄 Metadata: ${infoPath}`);
    }

    console.log("\n✅ Done!");
  } catch (error) {
    console.error(`\n❌ Error: ${(error as Error).message}`);
    process.exit(1);
  }
}

main();
