#!/usr/bin/env node

/**
 * URL-to-Scenes Generator
 *
 * Fetches a web page and extracts structured data into a scene JSON
 * ready for voiceover generation and Remotion rendering.
 *
 * Usage:
 *   node url-to-scenes.js --url https://example.com/page --format reels
 *   node url-to-scenes.js --url https://example.com/page --format longform --output scenes.json
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');

// ============================================
// ARGUMENT PARSING
// ============================================

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    url: null,
    format: 'reels',
    output: null,
    voice: null,
    dictionary: null,
    language: null,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const next = args[i + 1];

    switch (arg) {
      case '--url': case '-u':
        options.url = next; i++; break;
      case '--format': case '-f':
        options.format = next; i++; break;
      case '--output': case '-o':
        options.output = next; i++; break;
      case '--voice': case '-v':
        options.voice = next; i++; break;
      case '--dictionary': case '-d':
        options.dictionary = next; i++; break;
      case '--language': case '-l':
        options.language = next; i++; break;
      case '--help': case '-h':
        printHelp(); process.exit(0);
    }
  }

  if (!options.url) {
    console.error('Error: --url is required');
    printHelp();
    process.exit(1);
  }

  if (!['reels', 'longform'].includes(options.format)) {
    console.error(`Error: --format must be "reels" or "longform", got "${options.format}"`);
    process.exit(1);
  }

  return options;
}

function printHelp() {
  console.log(`
URL-to-Scenes Generator

Fetches a web page and extracts structured data into a scene JSON
ready for voiceover generation and Remotion rendering.

Usage:
  node url-to-scenes.js --url https://example.com/page [options]

Options:
  --url, -u        URL to extract content from (required)
  --format, -f     Output format: "reels" (4 scenes) or "longform" (6 scenes)
                   Default: "reels"
  --output, -o     Output file path for scenes JSON
                   Default: stdout
  --voice, -v      Voice name to set in output
  --dictionary, -d Dictionary name to set in output
  --language, -l   Content language (e.g., "de", "en")
                   Default: auto-detect from page
  --help, -h       Show this help
  `);
}

// ============================================
// HTML FETCHING
// ============================================

function fetchUrl(url, redirectCount = 0) {
  if (redirectCount > 5) {
    return Promise.reject(new Error('Too many redirects'));
  }

  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const client = parsed.protocol === 'https:' ? https : http;

    client.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; url-to-scenes/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'de,en;q=0.9',
      },
    }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        const redirectUrl = new URL(res.headers.location, url).toString();
        resolve(fetchUrl(redirectUrl, redirectCount + 1));
        return;
      }

      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode} fetching ${url}`));
        return;
      }

      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
      res.on('error', reject);
    }).on('error', reject);
  });
}

// ============================================
// HTML PARSING (regex-based, no dependencies)
// ============================================

function stripTags(html) {
  return html.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ').trim();
}

function extractMeta(html, name) {
  const match = html.match(new RegExp(`<meta[^>]+name=["']${name}["'][^>]+content=["']([^"']+)["']`, 'i'))
    || html.match(new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+name=["']${name}["']`, 'i'));
  return match ? match[1].trim() : null;
}

function extractOgMeta(html, property) {
  const match = html.match(new RegExp(`<meta[^>]+property=["']${property}["'][^>]+content=["']([^"']+)["']`, 'i'))
    || html.match(new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+property=["']${property}["']`, 'i'));
  return match ? match[1].trim() : null;
}

function extractTitle(html) {
  const h1Match = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return {
    h1: h1Match ? stripTags(h1Match[1]) : null,
    title: titleMatch ? stripTags(titleMatch[1]) : null,
  };
}

function extractHeadings(html) {
  const headings = [];
  const regex = /<(h[2-3])[^>]*>([\s\S]*?)<\/\1>/gi;
  let match;
  while ((match = regex.exec(html)) !== null) {
    const level = match[1].toUpperCase();
    const text = stripTags(match[2]);
    if (text && text.length > 2) {
      headings.push({ level, text });
    }
  }
  return headings;
}

function extractFAQs(html) {
  const faqs = [];

  // Try FAQ schema (JSON-LD)
  const schemaRegex = /<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let schemaMatch;
  while ((schemaMatch = schemaRegex.exec(html)) !== null) {
    try {
      const data = JSON.parse(schemaMatch[1]);
      if (data['@type'] === 'FAQPage' && data.mainEntity) {
        for (const item of data.mainEntity) {
          if (item['@type'] === 'Question') {
            faqs.push({
              question: item.name,
              answer: stripTags(item.acceptedAnswer?.text || ''),
            });
          }
        }
      }
    } catch { /* ignore parse errors */ }
  }

  // Try accordion/details elements
  if (faqs.length === 0) {
    const detailsRegex = /<details[^>]*>[\s\S]*?<summary[^>]*>([\s\S]*?)<\/summary>([\s\S]*?)<\/details>/gi;
    let detailsMatch;
    while ((detailsMatch = detailsRegex.exec(html)) !== null) {
      faqs.push({
        question: stripTags(detailsMatch[1]),
        answer: stripTags(detailsMatch[2]).substring(0, 200),
      });
    }
  }

  return faqs;
}

function extractCTAs(html) {
  const ctas = [];
  // Buttons
  const buttonRegex = /<button[^>]*>([\s\S]*?)<\/button>/gi;
  let match;
  while ((match = buttonRegex.exec(html)) !== null) {
    const text = stripTags(match[1]);
    if (text && text.length > 2 && text.length < 60) ctas.push(text);
  }
  // Links with action verbs
  const linkRegex = /<a[^>]*>([\s\S]*?)<\/a>/gi;
  const actionWords = /kontakt|beratung|anfrage|termin|jetzt|kostenlos|anrufen|schreiben|contact|get started|book|schedule|call|free/i;
  while ((match = linkRegex.exec(html)) !== null) {
    const text = stripTags(match[1]);
    if (text && actionWords.test(text) && text.length < 60) ctas.push(text);
  }
  return [...new Set(ctas)].slice(0, 5);
}

function extractKeyTerms(html) {
  const terms = new Set();

  // Bold/strong text
  const boldRegex = /<(?:strong|b)[^>]*>([\s\S]*?)<\/(?:strong|b)>/gi;
  let match;
  while ((match = boldRegex.exec(html)) !== null) {
    const text = stripTags(match[1]);
    if (text && text.length > 2 && text.length < 40 && !text.includes('<')) {
      terms.add(text);
    }
  }

  return [...terms].slice(0, 15);
}

function extractLists(html) {
  const lists = [];
  const olRegex = /<ol[^>]*>([\s\S]*?)<\/ol>/gi;
  let match;
  while ((match = olRegex.exec(html)) !== null) {
    const items = [];
    const liRegex = /<li[^>]*>([\s\S]*?)<\/li>/gi;
    let liMatch;
    while ((liMatch = liRegex.exec(match[1])) !== null) {
      items.push(stripTags(liMatch[1]).substring(0, 100));
    }
    if (items.length >= 2) lists.push(items);
  }
  return lists;
}

function extractInternalLinks(html, baseUrl) {
  const links = [];
  const parsed = new URL(baseUrl);
  const linkRegex = /<a[^>]+href=["']([^"']+)["'][^>]*>/gi;
  let match;
  while ((match = linkRegex.exec(html)) !== null) {
    const href = match[1];
    if (href.startsWith('/') && !href.startsWith('//')) {
      links.push(href);
    } else if (href.startsWith(parsed.origin)) {
      links.push(href.replace(parsed.origin, ''));
    }
  }
  return [...new Set(links)].filter(l => l !== '/' && l.length > 1).slice(0, 10);
}

function extractStatistics(html) {
  const stats = [];
  // Numbers in headings
  const headingRegex = /<h[1-4][^>]*>([\s\S]*?)<\/h[1-4]>/gi;
  let match;
  while ((match = headingRegex.exec(html)) !== null) {
    const text = stripTags(match[1]);
    if (/\d+/.test(text)) stats.push(text);
  }
  // Numbers in bold
  const boldRegex = /<(?:strong|b)[^>]*>([\s\S]*?)<\/(?:strong|b)>/gi;
  while ((match = boldRegex.exec(html)) !== null) {
    const text = stripTags(match[1]);
    if (/\d+\s*(?:%|Jahre|Monate|Tage|€|EUR|\$|Wochen)/.test(text)) stats.push(text);
  }
  return [...new Set(stats)].slice(0, 5);
}

function detectLanguage(html) {
  const langMatch = html.match(/<html[^>]+lang=["']([^"']+)["']/i);
  if (langMatch) return langMatch[1].split('-')[0];
  // Heuristic: check for German keywords
  if (/Immobilien|Kaufvertrag|Gewährleistung|Rechtsanwalt/i.test(html)) return 'de';
  return 'en';
}

function extractExistingVideos(html) {
  const videos = [];
  const videoRegex = /<video[^>]+src=["']([^"']+)["']/gi;
  let match;
  while ((match = videoRegex.exec(html)) !== null) {
    videos.push(match[1]);
  }
  const sourceRegex = /<source[^>]+src=["']([^"']+\.mp4[^"']*)["']/gi;
  while ((match = sourceRegex.exec(html)) !== null) {
    videos.push(match[1]);
  }
  return [...new Set(videos)];
}

// ============================================
// SCENE GENERATION
// ============================================

function pickHighlightWords(text, keyTerms, maxWords = 3) {
  const words = [];
  const textLower = text.toLowerCase();
  for (const term of keyTerms) {
    if (textLower.includes(term.toLowerCase()) && words.length < maxWords) {
      words.push(term);
    }
  }
  // Add numbers if found
  const numberMatch = text.match(/\d+\s*(?:%|Jahre|Monate|€|EUR|\$|Wochen|Tage)/);
  if (numberMatch && words.length < maxWords) {
    words.push(numberMatch[0]);
  }
  return words;
}

function generateReelsScenes(extracted) {
  const { h1, description, headings, faqs, keyTerms, ctas } = extracted;

  const hookSource = h1 || extracted.title || 'Page title';
  const problemHeadings = headings.filter(h => h.level === 'H2').slice(0, 3);
  const faqQuestions = faqs.slice(0, 2);

  return [
    {
      id: 'scene1',
      text: `TODO: Rewrite as emotional hook from: ${hookSource}`,
      duration: 3.5,
      character: 'dramatic',
      highlightWords: pickHighlightWords(hookSource, keyTerms),
      _source: `H1: ${hookSource}`,
    },
    {
      id: 'scene2',
      text: `TODO: Rewrite as pain points from: ${problemHeadings.map(h => h.text).join(', ') || faqQuestions.map(f => f.question).join(', ') || 'Problem section'}`,
      duration: 4.5,
      character: 'narrator',
      highlightWords: pickHighlightWords(
        problemHeadings.map(h => h.text).join(' '),
        keyTerms
      ),
      _source: problemHeadings.length > 0
        ? `H2s: ${problemHeadings.map(h => h.text).join(' | ')}`
        : `FAQs: ${faqQuestions.map(f => f.question).join(' | ')}`,
    },
    {
      id: 'scene3',
      text: `TODO: Rewrite as solution from: ${description || headings.find(h => /lösung|recht|anspruch|solution/i.test(h.text))?.text || 'Solution section'}`,
      duration: 4.0,
      character: 'expert',
      highlightWords: pickHighlightWords(description || '', keyTerms),
      _source: `Meta: ${description || 'No description found'}`,
    },
    {
      id: 'scene4',
      text: `TODO: Write CTA. Available CTAs: ${ctas.join(', ') || 'None found'}`,
      duration: 3.0,
      character: 'calm',
      highlightWords: [],
      _source: `CTAs: ${ctas.join(', ') || 'None'}`,
    },
  ];
}

function generateLongformScenes(extracted) {
  const { h1, description, headings, faqs, keyTerms, ctas, statistics, lists } = extracted;

  const hookSource = h1 || extracted.title || 'Page title';
  const problemHeadings = headings.filter(h => h.level === 'H2').slice(0, 3);
  const contextHeadings = headings.filter(h => h.level === 'H2').slice(3, 6);
  const solutionHeadings = headings.filter(h =>
    /lösung|recht|anspruch|option|solution|hilfe|schutz/i.test(h.text)
  );

  return [
    {
      id: 'scene1',
      name: 'hook',
      text: `TODO: Emotional opening from: ${hookSource}`,
      duration: 7,
      character: 'dramatic',
      highlightWords: pickHighlightWords(hookSource, keyTerms),
      _source: `H1: ${hookSource}`,
    },
    {
      id: 'scene2',
      name: 'problem',
      text: `TODO: Detail the issue from: ${problemHeadings.map(h => h.text).join(', ') || 'Problem sections'}`,
      duration: 12,
      character: 'narrator',
      highlightWords: pickHighlightWords(
        problemHeadings.map(h => h.text).join(' '),
        keyTerms
      ),
      _source: `H2s: ${problemHeadings.map(h => h.text).join(' | ')}`,
    },
    {
      id: 'scene3',
      name: 'context',
      text: `TODO: Background/statistics from: ${statistics.join(', ') || contextHeadings.map(h => h.text).join(', ') || 'Context sections'}`,
      duration: 18,
      character: 'expert',
      highlightWords: pickHighlightWords(
        statistics.join(' ') + ' ' + contextHeadings.map(h => h.text).join(' '),
        keyTerms
      ),
      _source: `Stats: ${statistics.join(' | ') || 'None'} | H2s: ${contextHeadings.map(h => h.text).join(' | ')}`,
    },
    {
      id: 'scene4',
      name: 'solution',
      text: `TODO: Rights and options from: ${solutionHeadings.map(h => h.text).join(', ') || description || 'Solution sections'}`,
      duration: 18,
      character: 'expert',
      highlightWords: pickHighlightWords(
        solutionHeadings.map(h => h.text).join(' ') + ' ' + (description || ''),
        keyTerms
      ),
      _source: `Solution H2s: ${solutionHeadings.map(h => h.text).join(' | ') || 'None found'}`,
    },
    {
      id: 'scene5',
      name: 'process',
      text: `TODO: Step-by-step from: ${lists.length > 0 ? lists[0].join(', ') : faqs.map(f => f.question).join(', ') || 'Process sections'}`,
      duration: 12,
      character: 'narrator',
      highlightWords: pickHighlightWords(
        (lists[0] || []).join(' '),
        keyTerms
      ),
      _source: `Lists: ${lists.length > 0 ? lists[0].slice(0, 3).join(' | ') : 'None'} | FAQs: ${faqs.slice(0, 2).map(f => f.question).join(' | ')}`,
    },
    {
      id: 'scene6',
      name: 'cta',
      text: `TODO: Contact CTA. Available: ${ctas.join(', ') || 'None found'}`,
      duration: 6,
      character: 'calm',
      highlightWords: [],
      _source: `CTAs: ${ctas.join(', ') || 'None'}`,
    },
  ];
}

// ============================================
// MAIN
// ============================================

async function main() {
  const options = parseArgs();

  console.error(`Fetching ${options.url}...`);
  const html = await fetchUrl(options.url);
  console.error(`Fetched ${(html.length / 1024).toFixed(0)} KB`);

  // Extract all data
  const titles = extractTitle(html);
  const description = extractMeta(html, 'description') || extractOgMeta(html, 'og:description');
  const headings = extractHeadings(html);
  const faqs = extractFAQs(html);
  const keyTerms = extractKeyTerms(html);
  const ctas = extractCTAs(html);
  const internalLinks = extractInternalLinks(html, options.url);
  const existingVideos = extractExistingVideos(html);
  const statistics = extractStatistics(html);
  const lists = extractLists(html);
  const language = options.language || detectLanguage(html);

  console.error(`Extracted: ${headings.length} headings, ${faqs.length} FAQs, ${keyTerms.length} key terms, ${ctas.length} CTAs`);

  const extracted = {
    ...titles,
    description,
    headings,
    faqs,
    keyTerms,
    ctas,
    internalLinks,
    existingVideos,
    statistics,
    lists,
  };

  // Generate scenes
  const scenes = options.format === 'longform'
    ? generateLongformScenes(extracted)
    : generateReelsScenes(extracted);

  // Build slug from URL
  const urlPath = new URL(options.url).pathname.replace(/^\/|\/$/g, '');
  const slug = urlPath.split('/').pop() || 'page';
  const prefix = options.format === 'longform' ? 'lf' : 'ad';
  const name = `${prefix}-${slug}`;

  // Build output JSON
  const output = {
    name,
    sourceUrl: options.url,
    format: options.format,
    voice: options.voice || 'TODO',
    character: 'narrator',
    dictionary: options.dictionary || 'TODO',
    language,
    scenes,
    extracted: {
      title: titles.title,
      h1: titles.h1,
      description,
      headings: headings.map(h => `${h.level}: ${h.text}`),
      faqs,
      keyTerms: [...keyTerms],
      ctas,
      internalLinks,
      existingVideos,
      statistics,
      lists: lists.map(l => l.slice(0, 5)),
    },
  };

  const json = JSON.stringify(output, null, 2);

  if (options.output) {
    const fs = require('fs');
    const path = require('path');
    const dir = path.dirname(options.output);
    if (dir && !require('fs').existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(options.output, json);
    console.error(`Wrote ${options.output}`);
  } else {
    console.log(json);
  }
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
