#!/usr/bin/env node
/**
 * Gemini TTS pipeline — full single-request generation + silence split.
 *
 * Replaces the previously-documented `gemini-tts-test.mjs` and
 * `gemini-tts-split.mjs` with one consolidated script.
 *
 * Usage:
 *   node scripts/gemini-tts.mjs --scenes scenes.json --output-dir public/audio/ad-name/
 *
 * Override per-run:
 *   --voice Vindemiatrix      (overrides scenes.voice)
 *   --speed 1.1               (atempo post-process; default 1.0; preserves pitch)
 *   --model gemini-3.1-flash-tts-preview
 *   --silence-d 0.35          (silencedetect duration threshold; default 0.35)
 *
 * scenes.json shape:
 * {
 *   "name": "ad-name",
 *   "voice": "Vindemiatrix",
 *   "model": "gemini-2.5-flash-preview-tts",
 *   "speed": 1.0,
 *   "directorNotes": {
 *     "audioProfile": "Female German narrator for a recruiting ad.",
 *     "scene": "Friendly invitation.",
 *     "style": "Warm, sincere, conversational. Energetic but not salesy.",
 *     "accent": "Hochdeutsch",
 *     "pacing": "Natural, brisk pace. Keep momentum."
 *   },
 *   "scenes": [
 *     { "id": "scene1", "text": "..." },
 *     { "id": "scene2", "text": "..." }
 *   ]
 * }
 *
 * Output:
 *   <out>/<name>-scene1.mp3 ... <name>-sceneN.mp3
 *   <out>/<name>-combined.mp3
 *   <out>/<name>-info.json   (includes actualDuration per scene + provenance)
 */

import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
import { GoogleGenAI } from "@google/genai";

// ---------- CLI ----------
const args = process.argv.slice(2);
function arg(name, fallback) {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : fallback;
}

const scenesPath = arg("scenes");
const outputDir = arg("output-dir");
const voiceOverride = arg("voice");
const speedOverride = arg("speed");
const modelOverride = arg("model");
const silenceD = parseFloat(arg("silence-d", "0.35"));

if (!scenesPath || !outputDir) {
  console.error(
    "Usage: node scripts/gemini-tts.mjs --scenes scenes.json --output-dir <dir>\n" +
      "       [--voice Vindemiatrix] [--speed 1.0] [--model gemini-2.5-flash-preview-tts] [--silence-d 0.35]"
  );
  process.exit(1);
}

// ---------- env ----------
const envPath = path.join(process.cwd(), ".env.local");
if (fs.existsSync(envPath)) {
  for (const line of fs.readFileSync(envPath, "utf-8").split("\n")) {
    const [k, ...v] = line.split("=");
    if (k && v.length) process.env[k.trim()] = v.join("=").trim();
  }
}
if (!process.env.GEMINI_API_KEY) {
  console.error("Error: GEMINI_API_KEY not set in environment or .env.local");
  process.exit(1);
}

// ---------- config ----------
const cfg = JSON.parse(fs.readFileSync(scenesPath, "utf-8"));
const NAME = cfg.name || "ad";
const VOICE = voiceOverride || cfg.voice || "Vindemiatrix";
const MODEL = modelOverride || cfg.model || "gemini-2.5-flash-preview-tts";
const SPEED = parseFloat(speedOverride ?? cfg.speed ?? 1.0);
const SCENES = cfg.scenes;
const NOTES = cfg.directorNotes || {};

if (!Array.isArray(SCENES) || SCENES.length === 0) {
  console.error("scenes.json: 'scenes' array missing or empty");
  process.exit(1);
}

fs.mkdirSync(outputDir, { recursive: true });

// ---------- build prompt ----------
const directorBlock = Object.entries(NOTES)
  .map(([k, v]) => `  ${capitalize(k)}: ${v}`)
  .join("\n");

const PROMPT = `${NOTES.audioProfile ? `Audio Profile: ${NOTES.audioProfile}\n` : ""}${
  NOTES.scene ? `Scene: ${NOTES.scene}\n` : ""
}Director's Notes:
${directorBlock || "  Style: Natural, professional."}

Script:
${SCENES.map((s) => s.text).join(" [long pause] ")}`;

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ---------- main ----------
console.log(`🎙  Gemini TTS`);
console.log(`   name:  ${NAME}`);
console.log(`   voice: ${VOICE}`);
console.log(`   model: ${MODEL}`);
console.log(`   speed: ${SPEED}x`);
console.log(`   scenes: ${SCENES.length}`);

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const response = await ai.models.generateContent({
  model: MODEL,
  contents: [{ parts: [{ text: PROMPT }] }],
  config: {
    responseModalities: ["AUDIO"],
    speechConfig: {
      voiceConfig: { prebuiltVoiceConfig: { voiceName: VOICE } },
    },
  },
});

const part = response.candidates?.[0]?.content?.parts?.find((p) => p.inlineData);
if (!part) {
  console.error("No audio data returned. Full response:", JSON.stringify(response, null, 2));
  process.exit(1);
}
const audioBuffer = Buffer.from(part.inlineData.data, "base64");

const pcmPath = path.join(outputDir, `${NAME}-full.pcm`);
const fullMp3 = path.join(outputDir, `${NAME}-combined.mp3`);
fs.writeFileSync(pcmPath, audioBuffer);
console.log(`✓ PCM: ${(audioBuffer.length / 1024).toFixed(1)} KB`);

// PCM 24kHz mono → MP3, with optional atempo speed-up (preserves pitch)
const speedFilter = SPEED !== 1.0 ? `-af atempo=${SPEED}` : "";
execSync(
  `ffmpeg -y -f s16le -ar 24000 -ac 1 -i "${pcmPath}" ${speedFilter} -ar 44100 -ab 128k "${fullMp3}"`,
  { stdio: "pipe" }
);
fs.unlinkSync(pcmPath);

const totalDur = parseFloat(
  execSync(`ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "${fullMp3}"`)
    .toString()
    .trim()
);
console.log(`✓ Combined: ${totalDur.toFixed(2)}s`);

// ---------- silence detect ----------
const silenceLog = execSync(
  `ffmpeg -i "${fullMp3}" -af silencedetect=noise=-30dB:d=${silenceD} -f null - 2>&1 || true`,
  { stdio: "pipe" }
).toString();

const starts = [];
const ends = [];
let m;
const startRe = /silence_start: ([\d.]+)/g;
const endRe = /silence_end: ([\d.]+) \| silence_duration: ([\d.]+)/g;
while ((m = startRe.exec(silenceLog))) starts.push(parseFloat(m[1]));
while ((m = endRe.exec(silenceLog))) ends.push({ end: parseFloat(m[1]), dur: parseFloat(m[2]) });

const silences = [];
for (let i = 0; i < Math.min(starts.length, ends.length); i++) {
  silences.push({ start: starts[i], end: ends[i].end, dur: ends[i].dur });
}

if (SCENES.length > 1 && silences.length === 0) {
  console.error(
    `No silences detected. Try lowering --silence-d (currently ${silenceD}). ` +
      "Gemini may have produced a continuous take."
  );
  process.exit(1);
}

// ---------- text-proportion-based boundary picker ----------
// For each expected boundary (cumulative char proportion × totalDur), pick the
// silence whose midpoint is closest to that target. Robust to in-scene pauses
// that exceed inter-scene pauses.
const charLens = SCENES.map((s) => s.text.length);
const totalChars = charLens.reduce((a, b) => a + b, 0);
const expected = [];
let acc = 0;
for (let i = 0; i < SCENES.length - 1; i++) {
  acc += charLens[i];
  expected.push((acc / totalChars) * totalDur);
}

const boundaries = expected.map((target) => {
  let best = silences[0];
  let bestD = Infinity;
  for (const s of silences) {
    const mid = (s.start + s.end) / 2;
    const d = Math.abs(mid - target);
    if (d < bestD) {
      bestD = d;
      best = s;
    }
  }
  return (best.start + best.end) / 2;
});

console.log(`  silences: ${silences.length}`);
console.log(`  expected: ${expected.map((e) => e.toFixed(2)).join(", ")}`);
console.log(`  picked:   ${boundaries.map((b) => b.toFixed(2)).join(", ")}`);

// ---------- cut per-scene ----------
const cuts = [0, ...boundaries, totalDur];
const sceneInfo = [];
for (let i = 0; i < SCENES.length; i++) {
  const start = cuts[i];
  const end = cuts[i + 1];
  const out = path.join(outputDir, `${NAME}-${SCENES[i].id}.mp3`);
  execSync(`ffmpeg -y -i "${fullMp3}" -ss ${start} -to ${end} -c copy "${out}"`, {
    stdio: "pipe",
  });
  const dur = parseFloat(
    execSync(`ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "${out}"`)
      .toString()
      .trim()
  );
  sceneInfo.push({
    id: SCENES[i].id,
    file: path.basename(out),
    text: SCENES[i].text,
    actualDuration: dur,
  });
  console.log(`  [${i + 1}/${SCENES.length}] ${SCENES[i].id}: ${dur.toFixed(2)}s`);
}

// Rebuild combined from per-scene cuts so combined length == sum(scene lengths)
const concatList = path.join(outputDir, "_concat.txt");
fs.writeFileSync(concatList, sceneInfo.map((s) => `file '${s.file}'`).join("\n"));
execSync(`ffmpeg -y -f concat -safe 0 -i "${concatList}" -c copy "${fullMp3}"`, {
  stdio: "pipe",
});
fs.unlinkSync(concatList);

// ---------- info.json ----------
const info = {
  name: NAME,
  provider: "gemini",
  voice: VOICE,
  model: MODEL,
  speed: SPEED,
  silenceD,
  generatedAt: new Date().toISOString(),
  totalDuration: sceneInfo.reduce((a, s) => a + s.actualDuration, 0),
  scenes: sceneInfo,
};
fs.writeFileSync(path.join(outputDir, `${NAME}-info.json`), JSON.stringify(info, null, 2));

console.log(`\n✅ Done. Total: ${info.totalDuration.toFixed(2)}s`);
console.log("\nScene durations for your composition:");
console.log(
  "const SCENE_DURATIONS = {\n" +
    sceneInfo.map((s) => `  ${s.id}: ${s.actualDuration.toFixed(2)},`).join("\n") +
    "\n};"
);
