#!/usr/bin/env node

/**
 * ElevenLabs Voiceover Generator with Request Stitching
 *
 * Features:
 * - Single text generation
 * - Scene-based generation with request stitching for consistent prosody
 * - Character/narrator modes for natural voiceovers
 * - Pronunciation dictionaries for brand names and terms
 * - Single scene regeneration for fine-tuning
 * - Automatic timing validation with ffprobe
 * - Silence detection
 * - Individual scene files + combined output
 *
 * Usage:
 *   node generate.js --text "Your text" --output output.mp3
 *   node generate.js --scenes scenes.json --output-dir public/audio/
 *   node generate.js --scenes scenes.json --scene scene2 --output-dir public/audio/
 *   node generate.js --validate public/audio/project/
 *   node generate.js --list-voices
 *   node generate.js --list-dictionaries
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { execSync } = require('child_process');

// Paths
const SKILL_DIR = path.dirname(__dirname); // Go up from scripts/ to skill root
const DICT_DIR = path.join(SKILL_DIR, 'assets', 'dictionaries');
const DICT_CACHE_FILE = path.join(SKILL_DIR, '.dictionary-cache.json');

// Default dictionary (set to null to disable, or specify your brand dictionary name)
const DEFAULT_DICTIONARY = null;

// Load environment variables from .env.local
function loadEnv() {
  const envPath = path.join(process.cwd(), '.env.local');
  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, 'utf-8');
    content.split('\n').forEach(line => {
      const [key, ...valueParts] = line.split('=');
      if (key && valueParts.length > 0) {
        process.env[key.trim()] = valueParts.join('=').trim();
      }
    });
  }
}

loadEnv();

const API_KEY = process.env.ELEVENLABS_API_KEY;

if (!API_KEY && !process.argv.includes('--validate') && !process.argv.includes('--help') && !process.argv.includes('-h') && !process.argv.includes('--list-dictionaries') && !process.argv.includes('--align')) {
  console.error('Error: ELEVENLABS_API_KEY not found in .env.local');
  process.exit(1);
}

// ============================================
// FORCED ALIGNMENT & TIMESTAMPS FUNCTIONS
// ============================================

/**
 * Generate speech with word-level timestamps using the /with-timestamps endpoint
 */
async function generateSpeechWithTimestamps(text, voiceId, options, previousRequestIds = [], dictionaryLocators = []) {
  const requestBody = {
    text: text,
    model_id: options.model,
    voice_settings: {
      stability: options.stability,
      similarity_boost: options.similarity,
      style: options.style,
      use_speaker_boost: true,
    },
    previous_request_ids: previousRequestIds,
  };

  if (dictionaryLocators.length > 0) {
    requestBody.pronunciation_dictionary_locators = dictionaryLocators;
  }

  const response = await makeRequest({
    hostname: 'api.elevenlabs.io',
    path: `/v1/text-to-speech/${voiceId}/with-timestamps`,
    method: 'POST',
    headers: {
      'xi-api-key': API_KEY,
      'Content-Type': 'application/json',
    },
  }, JSON.stringify(requestBody));

  if (response.status !== 200) {
    console.error('Error generating speech with timestamps:', response.data);
    throw new Error('Failed to generate speech with timestamps');
  }

  const data = response.data;

  // Convert base64 audio to buffer
  const audioBuffer = Buffer.from(data.audio_base64, 'base64');

  // Extract word-level timestamps from character alignment
  const words = extractWordsFromAlignment(text, data.alignment || data.normalized_alignment);

  return {
    audio: audioBuffer,
    requestId: response.requestId,
    characterCost: response.characterCost,
    alignment: data.alignment,
    normalizedAlignment: data.normalized_alignment,
    words: words,
  };
}

/**
 * Extract word-level timestamps from character alignment
 * Groups characters into words based on spaces/punctuation
 */
function extractWordsFromAlignment(text, alignment) {
  if (!alignment || !alignment.characters) {
    return [];
  }

  const words = [];
  let currentWord = '';
  let wordStartTime = null;
  let wordEndTime = null;
  let charIndex = 0;

  for (let i = 0; i < alignment.characters.length; i++) {
    const char = alignment.characters[i];
    const startTime = alignment.character_start_times_seconds[i];
    const endTime = alignment.character_end_times_seconds[i];

    // Handle word boundaries (space, punctuation at end)
    if (char === ' ' || char === '\n' || char === '\t') {
      if (currentWord.trim()) {
        words.push({
          text: currentWord.trim(),
          start: wordStartTime,
          end: wordEndTime,
          startMs: Math.round(wordStartTime * 1000),
          endMs: Math.round(wordEndTime * 1000),
        });
      }
      currentWord = '';
      wordStartTime = null;
      wordEndTime = null;
    } else {
      if (wordStartTime === null) {
        wordStartTime = startTime;
      }
      wordEndTime = endTime;
      currentWord += char;
    }
    charIndex++;
  }

  // Don't forget the last word
  if (currentWord.trim()) {
    words.push({
      text: currentWord.trim(),
      start: wordStartTime,
      end: wordEndTime,
      startMs: Math.round(wordStartTime * 1000),
      endMs: Math.round(wordEndTime * 1000),
    });
  }

  return words;
}

/**
 * Forced alignment: align existing audio to text
 * Returns word-level timestamps for the audio
 */
async function forceAlign(audioPath, text) {
  const audioBuffer = fs.readFileSync(audioPath);
  const fileName = path.basename(audioPath);

  // Create multipart form data
  const boundary = '----ElevenLabsBoundary' + Date.now();

  let body = '';
  body += `--${boundary}\r\n`;
  body += `Content-Disposition: form-data; name="text"\r\n\r\n`;
  body += `${text}\r\n`;
  body += `--${boundary}\r\n`;
  body += `Content-Disposition: form-data; name="file"; filename="${fileName}"\r\n`;
  body += `Content-Type: audio/mpeg\r\n\r\n`;

  const bodyStart = Buffer.from(body, 'utf-8');
  const bodyEnd = Buffer.from(`\r\n--${boundary}--\r\n`, 'utf-8');
  const fullBody = Buffer.concat([bodyStart, audioBuffer, bodyEnd]);

  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'api.elevenlabs.io',
      path: '/v1/forced-alignment',
      method: 'POST',
      headers: {
        'xi-api-key': API_KEY,
        'Content-Type': `multipart/form-data; boundary=${boundary}`,
        'Content-Length': fullBody.length,
      },
    }, (res) => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const data = Buffer.concat(chunks).toString();
        try {
          const json = JSON.parse(data);
          if (res.statusCode === 200 || res.statusCode === 201) {
            resolve(json);
          } else {
            reject(new Error(`Forced alignment failed: ${json.detail?.message || json.detail || data}`));
          }
        } catch {
          reject(new Error(`Forced alignment failed: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.write(fullBody);
    req.end();
  });
}

/**
 * Run forced alignment on existing audio and save word timestamps
 */
async function alignExistingAudio(audioPath, text, outputPath) {
  console.log(`\n🎯 Running forced alignment...`);
  console.log(`   Audio: ${audioPath}`);
  console.log(`   Text: "${text.substring(0, 60)}${text.length > 60 ? '...' : ''}"`);

  const alignment = await forceAlign(audioPath, text);

  const result = {
    audioFile: path.basename(audioPath),
    text: text,
    words: alignment.words || [],
    characters: alignment.characters || [],
    totalDuration: alignment.words?.length > 0
      ? alignment.words[alignment.words.length - 1].end
      : 0,
    loss: alignment.loss,
    alignedAt: new Date().toISOString(),
  };

  // Convert to Remotion-compatible format
  const remotionCaptions = {
    captions: result.words.map((word, index) => ({
      text: word.text + (index < result.words.length - 1 ? ' ' : ''),
      startMs: Math.round(word.start * 1000),
      endMs: Math.round(word.end * 1000),
      timestampMs: Math.round(word.start * 1000),
      confidence: 1 - (word.loss || 0),
    })),
  };

  // Save alignment data
  const alignmentPath = outputPath || audioPath.replace(/\.[^.]+$/, '-alignment.json');
  fs.writeFileSync(alignmentPath, JSON.stringify({ ...result, remotion: remotionCaptions }, null, 2));

  console.log(`\n✅ Alignment complete!`);
  console.log(`   Words: ${result.words.length}`);
  console.log(`   Duration: ${result.totalDuration?.toFixed(2)}s`);
  console.log(`   Confidence: ${((1 - (alignment.loss || 0)) * 100).toFixed(1)}%`);
  console.log(`   Output: ${alignmentPath}`);

  return result;
}

/**
 * Align all scenes in a project directory
 */
async function alignProjectScenes(projectDir, scenesFile) {
  const files = fs.readdirSync(projectDir);
  const infoFile = files.find(f => f.endsWith('-info.json'));

  if (!infoFile) {
    console.error(`No info file found in ${projectDir}`);
    process.exit(1);
  }

  const infoPath = path.join(projectDir, infoFile);
  const info = JSON.parse(fs.readFileSync(infoPath, 'utf-8'));

  console.log(`\n🎯 Aligning ${info.totalScenes} scenes from ${info.name}`);

  const alignments = [];

  for (const scene of info.scenes) {
    const audioPath = path.join(projectDir, scene.file);

    if (!fs.existsSync(audioPath)) {
      console.log(`⚠️  Skipping ${scene.id}: File not found`);
      continue;
    }

    console.log(`\n[${scene.id}] Aligning...`);

    try {
      const alignment = await forceAlign(audioPath, scene.text);

      const sceneAlignment = {
        id: scene.id,
        audioFile: scene.file,
        text: scene.text,
        words: alignment.words || [],
        loss: alignment.loss,
      };

      alignments.push(sceneAlignment);

      console.log(`   ✅ ${alignment.words?.length || 0} words, confidence: ${((1 - (alignment.loss || 0)) * 100).toFixed(1)}%`);

      // Small delay between API calls
      await new Promise(resolve => setTimeout(resolve, 200));
    } catch (error) {
      console.error(`   ❌ Error: ${error.message}`);
    }
  }

  // Save combined alignment file
  const outputPath = path.join(projectDir, `${info.name}-captions.json`);

  // Convert to Remotion-compatible format
  let cumulativeMs = 0;
  const allCaptions = [];

  for (const scene of alignments) {
    const sceneDelay = info.scenes.find(s => s.id === scene.id)?.delay || 0;
    const sceneDuration = info.scenes.find(s => s.id === scene.id)?.actualDuration || 0;

    for (const word of scene.words) {
      allCaptions.push({
        text: word.text + ' ',
        startMs: cumulativeMs + Math.round(word.start * 1000),
        endMs: cumulativeMs + Math.round(word.end * 1000),
        timestampMs: cumulativeMs + Math.round(word.start * 1000),
        sceneId: scene.id,
      });
    }

    cumulativeMs += Math.round((sceneDuration + sceneDelay) * 1000);
  }

  const output = {
    name: info.name,
    totalScenes: alignments.length,
    totalWords: allCaptions.length,
    scenes: alignments,
    remotion: {
      captions: allCaptions,
    },
    alignedAt: new Date().toISOString(),
  };

  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));

  console.log(`\n✅ All scenes aligned!`);
  console.log(`   Total words: ${allCaptions.length}`);
  console.log(`   Output: ${outputPath}`);

  return output;
}

// Timing thresholds for validation
const TIMING_CONFIG = {
  maxDurationDiffPercent: 15,
  maxLeadingSilenceMs: 200,
  maxTrailingSilenceMs: 500,
  minWordsPerSecond: 2.0,
  maxWordsPerSecond: 4.5,
  idealWordsPerSecond: 3.0,
};

// Character/narrator presets
const CHARACTER_PRESETS = {
  literal: {
    name: 'Literal',
    description: 'Reads text exactly as written',
    stability: 0.5,
    similarity: 0.75,
    style: 0.0,
  },
  narrator: {
    name: 'Narrator',
    description: 'Professional storyteller, smooth transitions, engaging',
    stability: 0.65,
    similarity: 0.8,
    style: 0.15,
  },
  salesperson: {
    name: 'Salesperson',
    description: 'Enthusiastic, persuasive, energetic delivery',
    stability: 0.4,
    similarity: 0.75,
    style: 0.35,
  },
  expert: {
    name: 'Expert',
    description: 'Authoritative, confident, knowledgeable tone',
    stability: 0.7,
    similarity: 0.85,
    style: 0.1,
  },
  conversational: {
    name: 'Conversational',
    description: 'Casual, friendly, like talking to a friend',
    stability: 0.45,
    similarity: 0.7,
    style: 0.25,
  },
  dramatic: {
    name: 'Dramatic',
    description: 'Intense, emotional, high impact delivery',
    stability: 0.35,
    similarity: 0.75,
    style: 0.5,
  },
  calm: {
    name: 'Calm',
    description: 'Soothing, reassuring, gentle delivery',
    stability: 0.8,
    similarity: 0.85,
    style: 0.05,
  },
};

// ============================================
// PRONUNCIATION DICTIONARY FUNCTIONS
// ============================================

/**
 * Load dictionary cache
 */
function loadDictionaryCache() {
  if (fs.existsSync(DICT_CACHE_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(DICT_CACHE_FILE, 'utf-8'));
    } catch {
      return {};
    }
  }
  return {};
}

/**
 * Parse PLS dictionary file and extract grapheme->alias mappings
 * Used as fallback when API dictionary permissions are missing
 */
function parsePLSDictionary(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const mappings = [];

  // Simple regex to extract grapheme and alias pairs
  const lexemeRegex = /<lexeme>[\s\S]*?<grapheme>([^<]+)<\/grapheme>[\s\S]*?<alias>([^<]+)<\/alias>[\s\S]*?<\/lexeme>/gi;

  let match;
  while ((match = lexemeRegex.exec(content)) !== null) {
    mappings.push({
      grapheme: match[1].trim(),
      alias: match[2].trim(),
    });
  }

  // Sort by grapheme length descending to avoid partial replacements
  mappings.sort((a, b) => b.grapheme.length - a.grapheme.length);

  return mappings;
}

/**
 * Apply pronunciation dictionary as text preprocessing fallback
 * Used when dictionary API permissions are missing
 */
function applyDictionaryFallback(text, dictName) {
  const dictPath = path.join(DICT_DIR, `${dictName}.pls`);
  if (!fs.existsSync(dictPath)) {
    return text;
  }

  const mappings = parsePLSDictionary(dictPath);
  let processedText = text;

  for (const { grapheme, alias } of mappings) {
    // Use case-insensitive replacement while preserving word boundaries where appropriate
    const regex = new RegExp(escapeRegex(grapheme), 'gi');
    processedText = processedText.replace(regex, alias);
  }

  return processedText;
}

/**
 * Escape special regex characters
 */
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Save dictionary cache
 */
function saveDictionaryCache(cache) {
  fs.writeFileSync(DICT_CACHE_FILE, JSON.stringify(cache, null, 2));
}

/**
 * Upload a pronunciation dictionary file to ElevenLabs
 */
async function uploadDictionary(filePath, name) {
  const fileContent = fs.readFileSync(filePath);
  const fileName = path.basename(filePath);

  // Create multipart form data boundary
  const boundary = '----ElevenLabsBoundary' + Date.now();

  // Build multipart body
  let body = '';
  body += `--${boundary}\r\n`;
  body += `Content-Disposition: form-data; name="name"\r\n\r\n`;
  body += `${name}\r\n`;
  body += `--${boundary}\r\n`;
  body += `Content-Disposition: form-data; name="file"; filename="${fileName}"\r\n`;
  body += `Content-Type: application/xml\r\n\r\n`;

  const bodyStart = Buffer.from(body, 'utf-8');
  const bodyEnd = Buffer.from(`\r\n--${boundary}--\r\n`, 'utf-8');
  const fullBody = Buffer.concat([bodyStart, fileContent, bodyEnd]);

  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'api.elevenlabs.io',
      path: '/v1/pronunciation-dictionaries/add-from-file',
      method: 'POST',
      headers: {
        'xi-api-key': API_KEY,
        'Content-Type': `multipart/form-data; boundary=${boundary}`,
        'Content-Length': fullBody.length,
      },
    }, (res) => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const data = Buffer.concat(chunks).toString();
        try {
          const json = JSON.parse(data);
          if (res.statusCode === 200 || res.statusCode === 201) {
            resolve(json);
          } else {
            reject(new Error(`Upload failed: ${json.detail?.message || json.detail || data}`));
          }
        } catch {
          reject(new Error(`Upload failed: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.write(fullBody);
    req.end();
  });
}

/**
 * List all pronunciation dictionaries
 */
async function listDictionaries() {
  const response = await makeRequest({
    hostname: 'api.elevenlabs.io',
    path: '/v1/pronunciation-dictionaries',
    method: 'GET',
    headers: { 'xi-api-key': API_KEY },
  });

  if (response.status !== 200) {
    throw new Error('Failed to list dictionaries');
  }

  return response.data.pronunciation_dictionaries || [];
}

/**
 * Get or create a dictionary, returns { id, versionId }
 */
async function getOrCreateDictionary(dictName) {
  // Check cache first
  const cache = loadDictionaryCache();
  if (cache[dictName]) {
    console.log(`   📖 Using cached dictionary: ${dictName}`);
    return cache[dictName];
  }

  // Check if dictionary file exists
  const dictPath = path.join(DICT_DIR, `${dictName}.pls`);
  if (!fs.existsSync(dictPath)) {
    throw new Error(`Dictionary file not found: ${dictPath}`);
  }

  // Check if already exists on ElevenLabs
  const existing = await listDictionaries();
  const found = existing.find(d => d.name === dictName);

  if (found) {
    const result = {
      id: found.id,
      versionId: found.latest_version_id,
    };
    cache[dictName] = result;
    saveDictionaryCache(cache);
    console.log(`   📖 Found existing dictionary: ${dictName}`);
    return result;
  }

  // Upload new dictionary
  console.log(`   📤 Uploading dictionary: ${dictName}`);
  const uploaded = await uploadDictionary(dictPath, dictName);

  const result = {
    id: uploaded.id,
    versionId: uploaded.version_id,
  };
  cache[dictName] = result;
  saveDictionaryCache(cache);

  return result;
}

/**
 * Display available dictionaries
 */
async function displayDictionaries() {
  console.log('\n📖 Pronunciation Dictionaries\n');

  // Local dictionaries
  console.log('Local dictionaries (in dictionaries/):');
  if (fs.existsSync(DICT_DIR)) {
    const files = fs.readdirSync(DICT_DIR).filter(f => f.endsWith('.pls'));
    if (files.length === 0) {
      console.log('  (none)');
    } else {
      files.forEach(f => {
        const name = f.replace('.pls', '');
        console.log(`  - ${name} (${f})`);
      });
    }
  } else {
    console.log('  (directory not found)');
  }

  // Remote dictionaries
  if (API_KEY) {
    console.log('\nRemote dictionaries (on ElevenLabs):');
    try {
      const remote = await listDictionaries();
      if (remote.length === 0) {
        console.log('  (none)');
      } else {
        remote.forEach(d => {
          console.log(`  - ${d.name} (id: ${d.id})`);
        });
      }
    } catch (e) {
      console.log(`  (error: ${e.message})`);
    }
  }

  // Cache
  console.log('\nCached dictionary IDs:');
  const cache = loadDictionaryCache();
  const keys = Object.keys(cache);
  if (keys.length === 0) {
    console.log('  (none)');
  } else {
    keys.forEach(k => {
      console.log(`  - ${k}: ${cache[k].id}`);
    });
  }

  console.log('\nUsage:');
  console.log('  --dictionary vosslegal     # Use local dictionary by name');
  console.log('  --no-dictionary            # Disable default dictionary');
}

// ============================================
// TIMING VALIDATION FUNCTIONS
// ============================================

function getAudioDuration(filePath) {
  try {
    const result = execSync(
      `ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${filePath}"`,
      { encoding: 'utf-8' }
    );
    return parseFloat(result.trim());
  } catch {
    console.warn(`   ⚠ Could not get duration for ${filePath} (ffprobe not available?)`);
    return null;
  }
}

function detectSilence(filePath) {
  try {
    const result = execSync(
      `ffmpeg -i "${filePath}" -af silencedetect=noise=-30dB:d=0.1 -f null - 2>&1`,
      { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }
    );

    const silenceStarts = [];
    const silenceEnds = [];

    const lines = result.split('\n');
    for (const line of lines) {
      const startMatch = line.match(/silence_start: ([\d.]+)/);
      const endMatch = line.match(/silence_end: ([\d.]+)/);
      if (startMatch) silenceStarts.push(parseFloat(startMatch[1]));
      if (endMatch) silenceEnds.push(parseFloat(endMatch[1]));
    }

    const duration = getAudioDuration(filePath);

    let leadingSilence = 0;
    if (silenceStarts.length > 0 && silenceStarts[0] < 0.05) {
      leadingSilence = silenceEnds[0] || 0;
    }

    let trailingSilence = 0;
    if (silenceEnds.length > 0 && duration) {
      const lastEnd = silenceEnds[silenceEnds.length - 1];
      const lastStart = silenceStarts[silenceStarts.length - 1];
      if (Math.abs(lastEnd - duration) < 0.1 || lastEnd > duration - 0.1) {
        trailingSilence = duration - lastStart;
      }
    }

    return { leadingSilence, trailingSilence };
  } catch {
    return { leadingSilence: 0, trailingSilence: 0 };
  }
}

function countWords(text) {
  return text.trim().split(/\s+/).filter(w => w.length > 0).length;
}

function validateTiming(filePath, text, expectedDuration = null) {
  const issues = [];
  const warnings = [];

  const actualDuration = getAudioDuration(filePath);
  if (!actualDuration) {
    return { actualDuration: null, issues: ['Could not determine audio duration'], warnings: [], silence: null, wordsPerSecond: null };
  }

  if (expectedDuration) {
    const diffPercent = Math.abs(actualDuration - expectedDuration) / expectedDuration * 100;
    if (diffPercent > TIMING_CONFIG.maxDurationDiffPercent) {
      const diff = actualDuration - expectedDuration;
      if (diff > 0) {
        issues.push(`Audio ${diff.toFixed(2)}s longer than expected (${actualDuration.toFixed(2)}s vs ${expectedDuration}s)`);
      } else {
        issues.push(`Audio ${Math.abs(diff).toFixed(2)}s shorter than expected (${actualDuration.toFixed(2)}s vs ${expectedDuration}s)`);
      }
    }
  }

  const silence = detectSilence(filePath);
  if (silence.leadingSilence > TIMING_CONFIG.maxLeadingSilenceMs / 1000) {
    warnings.push(`Leading silence: ${(silence.leadingSilence * 1000).toFixed(0)}ms (may start late)`);
  }
  if (silence.trailingSilence > TIMING_CONFIG.maxTrailingSilenceMs / 1000) {
    warnings.push(`Trailing silence: ${(silence.trailingSilence * 1000).toFixed(0)}ms`);
  }

  const wordCount = countWords(text);
  const speakingDuration = actualDuration - silence.leadingSilence - silence.trailingSilence;
  const wordsPerSecond = wordCount / speakingDuration;

  if (wordsPerSecond < TIMING_CONFIG.minWordsPerSecond) {
    warnings.push(`Speaking rate slow: ${wordsPerSecond.toFixed(1)} words/sec (target: ${TIMING_CONFIG.idealWordsPerSecond})`);
  } else if (wordsPerSecond > TIMING_CONFIG.maxWordsPerSecond) {
    warnings.push(`Speaking rate fast: ${wordsPerSecond.toFixed(1)} words/sec (target: ${TIMING_CONFIG.idealWordsPerSecond})`);
  }

  return {
    actualDuration,
    expectedDuration,
    issues,
    warnings,
    silence,
    wordsPerSecond,
    wordCount,
  };
}

async function validateProject(outputDir) {
  const files = fs.readdirSync(outputDir);
  const infoFile = files.find(f => f.endsWith('-info.json'));

  if (!infoFile) {
    console.error(`No info file found in ${outputDir}`);
    process.exit(1);
  }

  const infoPath = path.join(outputDir, infoFile);
  const info = JSON.parse(fs.readFileSync(infoPath, 'utf-8'));

  console.log(`\n🔍 Validating ${info.name} (${info.totalScenes} scenes)\n`);

  let hasIssues = false;
  let hasWarnings = false;
  const updatedScenes = [];

  for (const scene of info.scenes) {
    const filePath = path.join(outputDir, scene.file);

    if (!fs.existsSync(filePath)) {
      console.log(`❌ ${scene.id}: File not found - ${scene.file}`);
      hasIssues = true;
      updatedScenes.push(scene);
      continue;
    }

    const validation = validateTiming(filePath, scene.text, scene.duration);

    const updatedScene = {
      ...scene,
      actualDuration: validation.actualDuration,
      wordsPerSecond: validation.wordsPerSecond ? parseFloat(validation.wordsPerSecond.toFixed(2)) : null,
      leadingSilence: validation.silence?.leadingSilence ? parseFloat(validation.silence.leadingSilence.toFixed(3)) : 0,
      trailingSilence: validation.silence?.trailingSilence ? parseFloat(validation.silence.trailingSilence.toFixed(3)) : 0,
    };
    updatedScenes.push(updatedScene);

    const status = validation.issues.length > 0 ? '❌' : validation.warnings.length > 0 ? '⚠️' : '✅';
    console.log(`${status} ${scene.id}: ${validation.actualDuration?.toFixed(2)}s (expected: ${scene.duration || 'N/A'}s)`);

    if (validation.issues.length > 0) {
      hasIssues = true;
      validation.issues.forEach(i => console.log(`   ❌ ${i}`));
    }
    if (validation.warnings.length > 0) {
      hasWarnings = true;
      validation.warnings.forEach(w => console.log(`   ⚠️  ${w}`));
    }

    if (validation.wordsPerSecond) {
      const rateIcon = validation.wordsPerSecond < TIMING_CONFIG.minWordsPerSecond ? '🐢' :
                       validation.wordsPerSecond > TIMING_CONFIG.maxWordsPerSecond ? '🐇' : '👍';
      console.log(`   ${rateIcon} ${validation.wordCount} words @ ${validation.wordsPerSecond.toFixed(1)} words/sec`);
    }
  }

  info.scenes = updatedScenes;
  info.validatedAt = new Date().toISOString();
  fs.writeFileSync(infoPath, JSON.stringify(info, null, 2));

  console.log('\n' + '─'.repeat(50));
  const totalActual = updatedScenes.reduce((sum, s) => sum + (s.actualDuration || 0), 0);
  const totalExpected = updatedScenes.reduce((sum, s) => sum + (s.duration || 0), 0);
  console.log(`📊 Total duration: ${totalActual.toFixed(2)}s (expected: ${totalExpected.toFixed(2)}s)`);

  if (hasIssues) {
    console.log('\n❌ Issues found - consider regenerating affected scenes');
    console.log('   Example: node generate.js --scenes <file> --scene <id> --output-dir ' + outputDir);
  } else if (hasWarnings) {
    console.log('\n⚠️  Warnings found - review timing for best results');
  } else {
    console.log('\n✅ All scenes passed validation!');
  }

  console.log(`\n📝 Updated: ${infoFile} (with actual durations)`);

  return { hasIssues, hasWarnings };
}

// ============================================
// ARGUMENT PARSING
// ============================================

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    text: null,
    file: null,
    output: 'output.mp3',
    outputDir: null,
    voice: 'Vossi',
    model: 'eleven_multilingual_v2',
    stability: 0.5,
    similarity: 0.75,
    style: 0.0,
    speed: 1.0,
    listVoices: false,
    listCharacters: false,
    listDictionaries: false,
    scenes: null,
    scene: null,
    character: null,
    combined: true,
    newText: null,
    validate: null,
    skipValidation: false,
    dictionary: DEFAULT_DICTIONARY,  // Default to vosslegal dictionary
    noDictionary: false,
    withTimestamps: false,  // Generate with word-level timestamps
    align: null,            // Path to audio file for forced alignment
    alignText: null,        // Text for forced alignment
    alignProject: null,     // Align all scenes in a project directory
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];

    switch (arg) {
      case '--text':
      case '-t':
        options.text = nextArg;
        i++;
        break;
      case '--file':
      case '-f':
        options.file = nextArg;
        i++;
        break;
      case '--output':
      case '-o':
        options.output = nextArg;
        i++;
        break;
      case '--output-dir':
        options.outputDir = nextArg;
        i++;
        break;
      case '--voice':
      case '-v':
        options.voice = nextArg;
        i++;
        break;
      case '--model':
      case '-m':
        options.model = nextArg;
        i++;
        break;
      case '--stability':
        options.stability = parseFloat(nextArg);
        i++;
        break;
      case '--similarity':
        options.similarity = parseFloat(nextArg);
        i++;
        break;
      case '--style':
        options.style = parseFloat(nextArg);
        i++;
        break;
      case '--speed':
        options.speed = parseFloat(nextArg);
        i++;
        break;
      case '--list-voices':
        options.listVoices = true;
        break;
      case '--list-characters':
        options.listCharacters = true;
        break;
      case '--list-dictionaries':
        options.listDictionaries = true;
        break;
      case '--scenes':
        options.scenes = nextArg;
        i++;
        break;
      case '--scene':
        options.scene = nextArg;
        i++;
        break;
      case '--character':
      case '-c':
        options.character = nextArg;
        i++;
        break;
      case '--new-text':
        options.newText = nextArg;
        i++;
        break;
      case '--no-combined':
        options.combined = false;
        break;
      case '--validate':
        options.validate = nextArg;
        i++;
        break;
      case '--skip-validation':
        options.skipValidation = true;
        break;
      case '--dictionary':
      case '-d':
        options.dictionary = nextArg;
        i++;
        break;
      case '--no-dictionary':
        options.noDictionary = true;
        options.dictionary = null;
        break;
      case '--with-timestamps':
        options.withTimestamps = true;
        break;
      case '--align':
        options.align = nextArg;
        i++;
        break;
      case '--align-text':
        options.alignText = nextArg;
        i++;
        break;
      case '--align-project':
        options.alignProject = nextArg;
        i++;
        break;
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);
    }
  }

  if (options.character) {
    const preset = CHARACTER_PRESETS[options.character.toLowerCase()];
    if (preset) {
      options.stability = preset.stability;
      options.similarity = preset.similarity;
      options.style = preset.style;
    } else {
      console.error(`Unknown character: ${options.character}`);
      console.error(`Use --list-characters to see available options.`);
      process.exit(1);
    }
  }

  return options;
}

function printHelp() {
  console.log(`
ElevenLabs Voiceover Generator with Request Stitching, Timestamps & Pronunciation Dictionaries

Usage:
  node generate.js --text "Your text" --output output.mp3
  node generate.js --text "Your text" --with-timestamps --output output.mp3
  node generate.js --scenes scenes.json --output-dir public/audio/
  node generate.js --scenes scenes.json --scene scene2 --new-text "New text"
  node generate.js --validate public/audio/project/
  node generate.js --align audio.mp3 --align-text "Your transcript"
  node generate.js --align-project public/audio/project/
  node generate.js --list-voices
  node generate.js --list-characters
  node generate.js --list-dictionaries

Options:
  --text, -t          Text to convert to speech
  --file, -f          Read text from file
  --output, -o        Output file path (default: output.mp3)
  --output-dir        Output directory for scene files
  --voice, -v         Voice name or ID (default: Vossi)
  --model, -m         Model ID (default: eleven_multilingual_v2)
  --stability         Voice stability 0-1 (default: 0.5)
  --similarity        Similarity boost 0-1 (default: 0.75)
  --style             Style exaggeration 0-1 (default: 0.0)
  --character, -c     Character preset (narrator, salesperson, expert, etc.)
  --dictionary, -d    Pronunciation dictionary name (default: vosslegal)
  --no-dictionary     Disable pronunciation dictionary
  --scenes            JSON file with scenes for stitched generation
  --scene             Regenerate single scene by ID (use with --scenes)
  --new-text          New text for scene regeneration (optional)
  --no-combined       Don't create combined file (scenes mode only)
  --validate          Validate timing of generated audio in directory
  --skip-validation   Skip automatic validation after generation
  --with-timestamps   Generate with word-level timestamps (for captions)
  --align             Align existing audio file to text (forced alignment)
  --align-text        Text transcript for forced alignment
  --align-project     Align all scenes in a project directory
  --list-voices       List all available voices
  --list-characters   List all character presets
  --list-dictionaries List pronunciation dictionaries
  --help, -h          Show this help

Character Presets:
  literal        - Reads text exactly as written (default)
  narrator       - Professional storyteller, smooth, engaging
  salesperson    - Enthusiastic, persuasive, energetic
  expert         - Authoritative, confident, knowledgeable
  conversational - Casual, friendly, natural
  dramatic       - Intense, emotional, impactful
  calm           - Soothing, reassuring, gentle

Pronunciation Dictionaries:
  Use --dictionary to specify a custom pronunciation dictionary for
  brand names and technical terms.

  To create a custom dictionary, add a .pls file to:
    assets/dictionaries/

  Example .pls file:
    <?xml version="1.0" encoding="UTF-8"?>
    <lexicon version="1.0" xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
        alphabet="ipa" xml:lang="de">
      <lexeme>
        <grapheme>voss.legal</grapheme>
        <alias>Foss Legahl</alias>
      </lexeme>
    </lexicon>

Timestamps & Captions:
  Use --with-timestamps to generate audio with word-level timing data.
  This creates a JSON file with timestamps for each word, compatible
  with Remotion's @remotion/captions package for animated captions.

  Use --align to get timestamps for existing audio files (forced alignment).
  This is useful when you already have voiceovers and need timing data.

  Use --align-project to align all scenes in a project directory.
  This creates a combined captions file for the entire project.

Timing Validation:
  After generation, the tool automatically validates:
  - Actual vs expected duration (warns if >15% difference)
  - Leading silence (warns if >200ms - audio starts late)
  - Trailing silence (warns if >500ms)
  - Speaking rate (optimal: ~3 words/second for German)

Scene File Format (scenes.json):
{
  "name": "feuchtigkeit",
  "voice": "Vossi",
  "character": "narrator",
  "dictionary": "vosslegal",
  "scenes": [
    {
      "id": "scene1",
      "text": "Text for scene 1",
      "duration": 4,
      "character": "dramatic"
    }
  ]
}
  `);
}

function listCharacters() {
  console.log('\nAvailable Character Presets:\n');
  console.log('Name'.padEnd(15) + 'Stability'.padEnd(12) + 'Similarity'.padEnd(12) + 'Style'.padEnd(8) + 'Description');
  console.log('-'.repeat(90));

  for (const [key, preset] of Object.entries(CHARACTER_PRESETS)) {
    console.log(
      key.padEnd(15) +
      preset.stability.toFixed(2).padEnd(12) +
      preset.similarity.toFixed(2).padEnd(12) +
      preset.style.toFixed(2).padEnd(8) +
      preset.description
    );
  }

  console.log('\nUsage:');
  console.log('  --character narrator     # Use narrator style');
  console.log('  --character salesperson  # Use salesperson style');
}

// ============================================
// API FUNCTIONS
// ============================================

function makeRequest(options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const headers = res.headers;
        const requestId = headers['request-id'];
        const characterCost = headers['character-cost'];

        if (res.headers['content-type']?.includes('application/json')) {
          try {
            resolve({
              status: res.statusCode,
              data: JSON.parse(Buffer.concat(chunks).toString()),
              headers,
              requestId,
              characterCost
            });
          } catch {
            resolve({
              status: res.statusCode,
              data: Buffer.concat(chunks),
              headers,
              requestId,
              characterCost
            });
          }
        } else {
          resolve({
            status: res.statusCode,
            data: Buffer.concat(chunks),
            headers,
            requestId,
            characterCost
          });
        }
      });
    });

    req.on('error', reject);
    if (postData) req.write(postData);
    req.end();
  });
}

async function listVoices() {
  console.log('Fetching available voices...\n');

  const response = await makeRequest({
    hostname: 'api.elevenlabs.io',
    path: '/v1/voices',
    method: 'GET',
    headers: { 'xi-api-key': API_KEY },
  });

  if (response.status !== 200) {
    console.error('Error fetching voices:', response.data);
    return;
  }

  console.log('Available Voices:\n');
  console.log('Name'.padEnd(25) + 'ID'.padEnd(28) + 'Labels');
  console.log('-'.repeat(80));

  response.data.voices.forEach(voice => {
    const labels = voice.labels ? Object.values(voice.labels).join(', ') : '';
    console.log(
      voice.name.padEnd(40) +
      voice.voice_id.padEnd(28) +
      labels.substring(0, 40)
    );
  });

  console.log('\nTip: Use the full voice name or voice ID in your scenes JSON.');
  console.log('     Both exact and partial name matching are supported.');
  console.log('     Example: "Lily" matches "Lily - Velvety Actress"');
}

async function getVoiceId(voiceName) {
  // If it looks like a voice ID (20-24 alphanumeric chars), use directly
  if (/^[a-zA-Z0-9]{20,24}$/.test(voiceName)) {
    return voiceName;
  }

  const response = await makeRequest({
    hostname: 'api.elevenlabs.io',
    path: '/v1/voices',
    method: 'GET',
    headers: { 'xi-api-key': API_KEY },
  });

  if (response.status !== 200) {
    throw new Error('Failed to fetch voices');
  }

  const nameLower = voiceName.toLowerCase();

  // Try exact match first
  let voice = response.data.voices.find(
    v => v.name.toLowerCase() === nameLower
  );

  // Try prefix match (e.g. "Lily" matches "Lily - Velvety Actress")
  if (!voice) {
    voice = response.data.voices.find(
      v => v.name.toLowerCase().startsWith(nameLower)
    );
  }

  // Try contains match (e.g. "Velvety" matches "Lily - Velvety Actress")
  if (!voice) {
    voice = response.data.voices.find(
      v => v.name.toLowerCase().includes(nameLower)
    );
  }

  if (!voice) {
    throw new Error(`Voice "${voiceName}" not found. Use --list-voices to see available voices.\nTip: You can also use a voice ID directly (e.g. "pFZP5JQG7iQjIQuC4Bku").`);
  }

  console.log(`   Resolved voice: "${voice.name}" (${voice.voice_id})`);
  return voice.voice_id;
}

async function generateSpeechChunk(text, voiceId, options, previousRequestIds = [], dictionaryLocators = []) {
  const requestBody = {
    text: text,
    model_id: options.model,
    voice_settings: {
      stability: options.stability,
      similarity_boost: options.similarity,
      style: options.style,
      use_speaker_boost: true,
    },
    previous_request_ids: previousRequestIds,
  };

  // Add pronunciation dictionary if provided
  if (dictionaryLocators.length > 0) {
    requestBody.pronunciation_dictionary_locators = dictionaryLocators;
  }

  const response = await makeRequest({
    hostname: 'api.elevenlabs.io',
    path: `/v1/text-to-speech/${voiceId}`,
    method: 'POST',
    headers: {
      'xi-api-key': API_KEY,
      'Content-Type': 'application/json',
      'Accept': 'audio/mpeg',
    },
  }, JSON.stringify(requestBody));

  if (response.status !== 200) {
    console.error('Error generating speech:', response.data);
    throw new Error('Failed to generate speech');
  }

  return {
    audio: response.data,
    requestId: response.requestId,
    characterCost: response.characterCost,
  };
}

// ============================================
// GENERATION FUNCTIONS
// ============================================

async function generateSpeech(text, options) {
  console.log(`Generating voiceover${options.withTimestamps ? ' with timestamps' : ''}...`);
  console.log(`  Voice: ${options.voice}`);
  console.log(`  Model: ${options.model}`);
  if (options.character) console.log(`  Character: ${options.character}`);
  if (options.dictionary) console.log(`  Dictionary: ${options.dictionary}`);
  if (options.withTimestamps) console.log(`  Timestamps: enabled`);
  console.log(`  Text length: ${text.length} characters`);
  console.log(`  Output: ${options.output}`);
  console.log('');

  const voiceId = await getVoiceId(options.voice);

  // Get dictionary locators if specified
  let dictionaryLocators = [];
  let useFallback = false;
  const dictName = options.noDictionary ? null : (options.dictionary || DEFAULT_DICTIONARY);

  if (dictName) {
    try {
      const dict = await getOrCreateDictionary(dictName);
      dictionaryLocators = [{
        pronunciation_dictionary_id: dict.id,
        version_id: dict.versionId,
      }];
    } catch (e) {
      console.warn(`   ⚠ Could not load dictionary API: ${e.message}`);
      console.log(`   🔄 Using text preprocessing fallback for ${dictName}`);
      useFallback = true;
    }
  }

  // Apply text preprocessing fallback if API failed
  const processedText = useFallback && dictName ? applyDictionaryFallback(text, dictName) : text;

  let result;
  if (options.withTimestamps) {
    result = await generateSpeechWithTimestamps(processedText, voiceId, options, [], dictionaryLocators);
  } else {
    result = await generateSpeechChunk(processedText, voiceId, options, [], dictionaryLocators);
  }

  const outputDir = path.dirname(options.output);
  if (outputDir && !fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(options.output, result.audio);

  const stats = fs.statSync(options.output);
  console.log(`✓ Voiceover saved: ${options.output} (${(stats.size / 1024).toFixed(1)} KB)`);
  if (result.characterCost) console.log(`  Character cost: ${result.characterCost}`);

  // Save timestamps if generated
  if (options.withTimestamps && result.words) {
    const timestampsPath = options.output.replace(/\.[^.]+$/, '-captions.json');

    // Create Remotion-compatible captions format
    const remotionCaptions = result.words.map((word, index) => ({
      text: word.text + (index < result.words.length - 1 ? ' ' : ''),
      startMs: word.startMs,
      endMs: word.endMs,
      timestampMs: word.startMs,
    }));

    const timestampsData = {
      text: processedText,
      words: result.words,
      remotion: {
        captions: remotionCaptions,
      },
      generatedAt: new Date().toISOString(),
    };

    fs.writeFileSync(timestampsPath, JSON.stringify(timestampsData, null, 2));
    console.log(`✓ Timestamps saved: ${timestampsPath} (${result.words.length} words)`);
  }

  if (!options.skipValidation) {
    console.log('\n📊 Validating timing...');
    const validation = validateTiming(options.output, text);
    if (validation.actualDuration) {
      console.log(`   Duration: ${validation.actualDuration.toFixed(2)}s`);
      console.log(`   Speaking rate: ${validation.wordsPerSecond?.toFixed(1)} words/sec`);
      validation.warnings.forEach(w => console.log(`   ⚠️  ${w}`));
    }
  }

  return options.output;
}

async function regenerateSingleScene(scenesFile, sceneId, options) {
  const config = JSON.parse(fs.readFileSync(scenesFile, 'utf-8'));
  const voiceName = config.voice || options.voice;
  const projectName = config.name || 'voiceover';
  const outputDir = options.outputDir || path.dirname(options.output) || 'public/audio';
  const dictName = options.noDictionary ? null : (options.dictionary || config.dictionary || DEFAULT_DICTIONARY);

  const sceneIndex = config.scenes.findIndex(s => s.id === sceneId);
  if (sceneIndex === -1) {
    console.error(`Scene "${sceneId}" not found in ${scenesFile}`);
    console.error(`Available scenes: ${config.scenes.map(s => s.id).join(', ')}`);
    process.exit(1);
  }

  const scene = config.scenes[sceneIndex];
  const text = options.newText || scene.text;

  let characterSettings = { ...CHARACTER_PRESETS.literal };
  if (config.character && CHARACTER_PRESETS[config.character]) {
    characterSettings = { ...CHARACTER_PRESETS[config.character] };
  }
  if (scene.character && CHARACTER_PRESETS[scene.character]) {
    characterSettings = { ...CHARACTER_PRESETS[scene.character] };
  }
  if (options.character && CHARACTER_PRESETS[options.character]) {
    characterSettings = { ...CHARACTER_PRESETS[options.character] };
  }

  const infoFilePath = path.join(outputDir, `${projectName}-info.json`);
  let previousRequestIds = [];
  let infoData = null;

  if (fs.existsSync(infoFilePath)) {
    infoData = JSON.parse(fs.readFileSync(infoFilePath, 'utf-8'));
    const prevScenes = infoData.scenes.slice(Math.max(0, sceneIndex - 3), sceneIndex);
    previousRequestIds = prevScenes.map(s => s.requestId).filter(Boolean);
  }

  console.log(`\n🔄 Regenerating ${sceneId}`);
  console.log(`   Voice: ${voiceName}`);
  console.log(`   Character: ${options.character || scene.character || config.character || 'literal'}`);
  if (dictName) console.log(`   Dictionary: ${dictName}`);
  console.log(`   Text: "${text.substring(0, 60)}${text.length > 60 ? '...' : ''}"`);
  if (options.newText) console.log(`   (Using new text)`);
  console.log('');

  const voiceId = await getVoiceId(voiceName);

  // Get dictionary locators
  let dictionaryLocators = [];
  let useFallback = false;
  if (dictName) {
    try {
      const dict = await getOrCreateDictionary(dictName);
      dictionaryLocators = [{
        pronunciation_dictionary_id: dict.id,
        version_id: dict.versionId,
      }];
    } catch (e) {
      console.warn(`   ⚠ Could not load dictionary: ${e.message}`);
      console.log(`   🔄 Using text preprocessing fallback`);
      useFallback = true;
    }
  }

  // Apply text preprocessing fallback if API failed
  const processedText = useFallback && dictName ? applyDictionaryFallback(text, dictName) : text;

  const result = await generateSpeechChunk(processedText, voiceId, {
    ...options,
    stability: characterSettings.stability,
    similarity: characterSettings.similarity,
    style: characterSettings.style,
  }, previousRequestIds, dictionaryLocators);

  const sceneFilename = `${projectName}-${sceneId}.mp3`;
  const sceneFilePath = path.join(outputDir, sceneFilename);
  fs.writeFileSync(sceneFilePath, result.audio);

  const stats = fs.statSync(sceneFilePath);
  console.log(`✓ Regenerated: ${sceneFilename} (${(stats.size / 1024).toFixed(1)} KB)`);

  if (!options.skipValidation) {
    console.log('\n📊 Validating timing...');
    const validation = validateTiming(sceneFilePath, text, scene.duration);

    if (validation.actualDuration) {
      const status = validation.issues.length > 0 ? '❌' : validation.warnings.length > 0 ? '⚠️' : '✅';
      console.log(`${status} Actual: ${validation.actualDuration.toFixed(2)}s, Expected: ${scene.duration || 'N/A'}s`);
      console.log(`   Speaking rate: ${validation.wordsPerSecond?.toFixed(1)} words/sec (${validation.wordCount} words)`);

      if (validation.silence.leadingSilence > 0.05) {
        console.log(`   Leading silence: ${(validation.silence.leadingSilence * 1000).toFixed(0)}ms`);
      }

      validation.issues.forEach(i => console.log(`   ❌ ${i}`));
      validation.warnings.forEach(w => console.log(`   ⚠️  ${w}`));

      if (infoData) {
        infoData.scenes[sceneIndex] = {
          ...infoData.scenes[sceneIndex],
          text: text,
          size: stats.size,
          actualDuration: validation.actualDuration,
          wordsPerSecond: parseFloat(validation.wordsPerSecond.toFixed(2)),
          leadingSilence: parseFloat(validation.silence.leadingSilence.toFixed(3)),
          requestId: result.requestId,
          regeneratedAt: new Date().toISOString(),
          character: options.character || scene.character || config.character || 'literal',
        };
        infoData.updatedAt = new Date().toISOString();
        fs.writeFileSync(infoFilePath, JSON.stringify(infoData, null, 2));
        console.log(`✓ Updated: ${projectName}-info.json`);
      }
    }
  }

  if (options.newText) {
    config.scenes[sceneIndex].text = options.newText;
    fs.writeFileSync(scenesFile, JSON.stringify(config, null, 2));
    console.log(`✓ Updated: ${scenesFile}`);
  }

  console.log(`\n✅ Scene regeneration complete!`);

  return result;
}

async function generateScenes(scenesFile, options) {
  const config = JSON.parse(fs.readFileSync(scenesFile, 'utf-8'));
  const scenes = config.scenes;
  const voiceName = config.voice || options.voice;
  const projectName = config.name || 'voiceover';
  const globalCharacter = options.character || config.character || 'literal';
  const dictName = options.noDictionary ? null : (options.dictionary || config.dictionary || DEFAULT_DICTIONARY);
  const withTimestamps = options.withTimestamps;

  const outputDir = options.outputDir || path.dirname(options.output) || 'public/audio';

  console.log(`\n🎬 Generating ${scenes.length} scenes with Request Stitching`);
  console.log(`   Voice: ${voiceName}`);
  console.log(`   Model: ${options.model}`);
  console.log(`   Character: ${globalCharacter}`);
  if (dictName) console.log(`   Dictionary: ${dictName}`);
  if (withTimestamps) console.log(`   Timestamps: enabled`);
  console.log(`   Output: ${outputDir}/`);
  console.log('');

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const voiceId = await getVoiceId(voiceName);

  // Get dictionary locators
  let dictionaryLocators = [];
  let useFallback = false;
  if (dictName) {
    try {
      const dict = await getOrCreateDictionary(dictName);
      dictionaryLocators = [{
        pronunciation_dictionary_id: dict.id,
        version_id: dict.versionId,
      }];
    } catch (e) {
      console.warn(`   ⚠ Could not load dictionary: ${e.message}`);
      console.log(`   🔄 Using text preprocessing fallback for ${dictName}`);
      useFallback = true;
    }
  }

  const requestIds = [];
  const audioBuffers = [];
  const sceneInfo = [];
  let totalCharacters = 0;

  for (let i = 0; i < scenes.length; i++) {
    const scene = scenes[i];
    const sceneId = scene.id || `scene${i + 1}`;
    const rawText = scene.text;
    // Apply text preprocessing fallback if API failed
    const text = useFallback && dictName ? applyDictionaryFallback(rawText, dictName) : rawText;

    const sceneCharacter = scene.character || globalCharacter;
    const characterSettings = CHARACTER_PRESETS[sceneCharacter] || CHARACTER_PRESETS.literal;

    console.log(`[${i + 1}/${scenes.length}] ${sceneId} (${sceneCharacter})`);
    console.log(`   "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"`);

    try {
      let result;
      if (withTimestamps) {
        result = await generateSpeechWithTimestamps(text, voiceId, {
          ...options,
          stability: scene.stability || characterSettings.stability,
          similarity: scene.similarity || characterSettings.similarity,
          style: scene.style || characterSettings.style,
        }, requestIds.slice(-3), dictionaryLocators);
      } else {
        result = await generateSpeechChunk(text, voiceId, {
          ...options,
          stability: scene.stability || characterSettings.stability,
          similarity: scene.similarity || characterSettings.similarity,
          style: scene.style || characterSettings.style,
        }, requestIds.slice(-3), dictionaryLocators);
      }

      const sceneFilename = `${projectName}-${sceneId}.mp3`;
      const sceneFilePath = path.join(outputDir, sceneFilename);
      fs.writeFileSync(sceneFilePath, result.audio);

      const stats = fs.statSync(sceneFilePath);

      let validation = null;
      if (!options.skipValidation) {
        validation = validateTiming(sceneFilePath, text, scene.duration);
      }

      const actualDuration = validation?.actualDuration || null;
      const status = !validation ? '✓' :
                     validation.issues.length > 0 ? '⚠️' :
                     validation.warnings.length > 0 ? '⚠️' : '✓';

      console.log(`   ${status} ${sceneFilename} (${(stats.size / 1024).toFixed(1)} KB, ${actualDuration?.toFixed(2) || '?'}s)`);

      if (validation?.issues.length > 0) {
        validation.issues.forEach(i => console.log(`      ❌ ${i}`));
      }
      if (validation?.warnings.length > 0) {
        validation.warnings.forEach(w => console.log(`      ⚠️  ${w}`));
      }

      requestIds.push(result.requestId);
      audioBuffers.push(result.audio);

      const sceneData = {
        id: sceneId,
        file: sceneFilename,
        text: text,
        size: stats.size,
        duration: scene.duration || null,
        actualDuration: actualDuration,
        wordsPerSecond: validation?.wordsPerSecond ? parseFloat(validation.wordsPerSecond.toFixed(2)) : null,
        leadingSilence: validation?.silence?.leadingSilence ? parseFloat(validation.silence.leadingSilence.toFixed(3)) : 0,
        delay: scene.delay || 0,
        character: sceneCharacter,
        requestId: result.requestId,
      };

      // Add word timestamps if generated
      if (withTimestamps && result.words) {
        sceneData.words = result.words;
      }

      sceneInfo.push(sceneData);

      totalCharacters += text.length;

    } catch (error) {
      console.error(`   ✗ Error: ${error.message}`);
      throw error;
    }

    if (i < scenes.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }

  if (options.combined) {
    const combinedFilename = `${projectName}-combined.mp3`;
    const combinedFilePath = path.join(outputDir, combinedFilename);
    const combinedBuffer = Buffer.concat(audioBuffers);
    fs.writeFileSync(combinedFilePath, combinedBuffer);

    const combinedStats = fs.statSync(combinedFilePath);
    console.log(`\n✓ Combined: ${combinedFilename} (${(combinedStats.size / 1024).toFixed(1)} KB)`);
  }

  const infoFilePath = path.join(outputDir, `${projectName}-info.json`);
  const infoData = {
    name: projectName,
    voice: voiceName,
    model: options.model,
    character: globalCharacter,
    dictionary: dictName,
    totalScenes: scenes.length,
    totalCharacters: totalCharacters,
    withTimestamps: withTimestamps,
    generatedAt: new Date().toISOString(),
    scenes: sceneInfo,
  };
  fs.writeFileSync(infoFilePath, JSON.stringify(infoData, null, 2));

  // Save combined captions file if timestamps were generated
  if (withTimestamps) {
    let cumulativeMs = 0;
    const allCaptions = [];

    for (const scene of sceneInfo) {
      if (scene.words) {
        for (const word of scene.words) {
          allCaptions.push({
            text: word.text + ' ',
            startMs: cumulativeMs + word.startMs,
            endMs: cumulativeMs + word.endMs,
            timestampMs: cumulativeMs + word.startMs,
            sceneId: scene.id,
          });
        }
      }
      cumulativeMs += Math.round((scene.actualDuration || scene.duration || 0) * 1000) + Math.round((scene.delay || 0) * 1000);
    }

    const captionsFilePath = path.join(outputDir, `${projectName}-captions.json`);
    const captionsData = {
      name: projectName,
      totalWords: allCaptions.length,
      remotion: {
        captions: allCaptions,
      },
      generatedAt: new Date().toISOString(),
    };
    fs.writeFileSync(captionsFilePath, JSON.stringify(captionsData, null, 2));
    console.log(`\n✓ Captions: ${captionsFilePath} (${allCaptions.length} words)`);
  }

  console.log(`\n📋 Summary`);
  console.log(`   Scenes: ${scenes.length}`);
  console.log(`   Characters: ${totalCharacters}`);

  const totalActual = sceneInfo.reduce((sum, s) => sum + (s.actualDuration || 0), 0);
  const totalExpected = sceneInfo.reduce((sum, s) => sum + (s.duration || 0), 0);
  console.log(`   Total duration: ${totalActual.toFixed(2)}s (expected: ${totalExpected.toFixed(2)}s)`);

  const issues = sceneInfo.filter(s => s.actualDuration && s.duration && Math.abs(s.actualDuration - s.duration) / s.duration > 0.15);
  if (issues.length > 0) {
    console.log(`\n⚠️  ${issues.length} scene(s) with timing issues:`);
    issues.forEach(s => {
      const diff = s.actualDuration - s.duration;
      console.log(`   - ${s.id}: ${diff > 0 ? '+' : ''}${diff.toFixed(2)}s (actual: ${s.actualDuration.toFixed(2)}s, expected: ${s.duration}s)`);
    });
  }

  console.log(`\n✅ Scene generation complete!`);
  console.log(`\nTo regenerate a scene with timing issues:`);
  console.log(`   node generate.js --scenes ${scenesFile} --scene <scene-id> --output-dir ${outputDir}`);

  return sceneInfo;
}

// ============================================
// MAIN
// ============================================

async function main() {
  const options = parseArgs();

  try {
    if (options.listVoices) {
      await listVoices();
      return;
    }

    if (options.listCharacters) {
      listCharacters();
      return;
    }

    if (options.listDictionaries) {
      await displayDictionaries();
      return;
    }

    if (options.validate) {
      await validateProject(options.validate);
      return;
    }

    // Forced alignment for existing audio
    if (options.align) {
      if (!options.alignText && !options.text) {
        console.error('Error: --align-text or --text is required with --align');
        process.exit(1);
      }
      const text = options.alignText || options.text;
      await alignExistingAudio(options.align, text, options.output.replace('.mp3', '-alignment.json'));
      return;
    }

    // Align all scenes in a project directory
    if (options.alignProject) {
      await alignProjectScenes(options.alignProject, options.scenes);
      return;
    }

    if (options.scenes) {
      if (!fs.existsSync(options.scenes)) {
        console.error(`Error: Scenes file not found: ${options.scenes}`);
        process.exit(1);
      }

      if (options.scene) {
        await regenerateSingleScene(options.scenes, options.scene, options);
        return;
      }

      await generateScenes(options.scenes, options);
      return;
    }

    let text = options.text;

    if (options.file) {
      if (!fs.existsSync(options.file)) {
        console.error(`Error: File not found: ${options.file}`);
        process.exit(1);
      }
      text = fs.readFileSync(options.file, 'utf-8').trim();
    }

    if (!text) {
      console.error('Error: No text provided. Use --text, --file, or --scenes');
      printHelp();
      process.exit(1);
    }

    await generateSpeech(text, options);

  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

main();
