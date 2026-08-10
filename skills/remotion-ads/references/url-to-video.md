# URL-to-Video Workflow

Create video content from existing web pages. Provide a URL, extract structured data, and generate a pre-filled scene JSON ready for voiceover and rendering.

## Quick Start

```bash
# Generate scene JSON from a URL
node scripts/url-to-scenes.js \
  --url https://example.com/your-page \
  --format reels \
  --output remotion/scenes/ad-example-scenes.json

# Or for website explainer videos
node scripts/url-to-scenes.js \
  --url https://example.com/your-page \
  --format longform \
  --output remotion/scenes/lf-example-scenes.json
```

---

## What the Script Extracts

The `url-to-scenes.js` script fetches a page and extracts:

| Data | Source | Used For |
|------|--------|----------|
| Page title | `<title>`, `<h1>` | Hook headline |
| Meta description | `<meta name="description">` | Hook subtitle |
| Headings (H2, H3) | Content structure | Scene topics |
| FAQ questions | FAQ schema, accordion elements | Problem/Context scenes |
| Key terms | Bold text, repeated terms, domain keywords | Highlight words |
| CTA text | Buttons, links with action verbs | CTA scene |
| Internal links | `<a>` to related pages | Related topics |
| Existing videos | `<video>`, schema markup | Avoid duplicating |
| Lists/steps | `<ol>`, `<ul>`, numbered items | Process scene |
| Statistics | Numbers in headings/bold | Context scene |

---

## Output Format

The script generates a scene JSON with suggested content:

### Reels (4 scenes)

```json
{
  "name": "ad-example",
  "sourceUrl": "https://example.com/your-page",
  "voice": "TODO",
  "character": "narrator",
  "dictionary": "TODO",
  "scenes": [
    {
      "id": "scene1",
      "text": "Derived from H1 + meta description",
      "duration": 3.5,
      "character": "dramatic",
      "highlightWords": ["keyword1", "keyword2"],
      "_source": "H1: Original heading text"
    },
    {
      "id": "scene2",
      "text": "Derived from problem headings and FAQ questions",
      "duration": 4.5,
      "character": "narrator",
      "highlightWords": ["pain-point", "issue"],
      "_source": "H2: Problem section heading"
    },
    {
      "id": "scene3",
      "text": "Derived from solution section",
      "duration": 4.0,
      "character": "expert",
      "highlightWords": ["solution", "benefit"],
      "_source": "H2: Solution section heading"
    },
    {
      "id": "scene4",
      "text": "Derived from CTA buttons and contact section",
      "duration": 3.0,
      "character": "calm",
      "highlightWords": ["brand-name"],
      "_source": "CTA: Button text"
    }
  ],
  "extracted": {
    "title": "Original page title",
    "description": "Meta description",
    "headings": ["H2: ...", "H2: ...", "H3: ..."],
    "faqs": [
      { "question": "...", "answer": "..." }
    ],
    "keyTerms": ["term1", "term2", "term3"],
    "ctas": ["Button text 1", "Link text 2"],
    "relatedLinks": ["/related-page-1", "/related-page-2"],
    "existingVideos": []
  }
}
```

### Long-form (6 scenes)

Same format but with 6 scenes mapping to: hook, problem, context, solution, process, cta. The script distributes extracted headings and FAQ content across the additional context and process scenes.

---

## CLI Options

```
Usage: node scripts/url-to-scenes.js [options]

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
```

---

## Manual Workflow (Without Script)

When the script isn't available or needs supplementing:

### Step 1: Fetch and analyze the page

```bash
# Using WebFetch or curl
curl -s https://example.com/page | ...
```

Or use the WebFetch tool to extract content with a prompt like:
> "Extract all H1-H3 headings, FAQ questions/answers, CTA button text, bold/emphasized terms, and any numbered lists or step-by-step sections."

### Step 2: Map content to scenes

**Reels (4 scenes):**

| Scene | Content Source |
|-------|--------------|
| Hook | H1 + meta description → emotional question |
| Problem | First 2-3 H2s or FAQ questions → pain points |
| Solution | Solution/benefits section → key rights/options |
| CTA | CTA buttons → call to action with brand name |

**Long-form (6 scenes):**

| Scene | Content Source |
|-------|--------------|
| Hook | H1 + meta description → emotional opening |
| Problem | Problem H2s → detailed pain points |
| Context | Statistics, legal refs, timelines → background |
| Solution | Solution H2s → rights and options |
| Process | Step-by-step lists, how-to sections → actionable steps |
| CTA | CTA + trust signals → contact info |

### Step 3: Select highlight words

From the extracted key terms, pick 2-4 per scene:
- Domain-specific keywords (legal terms, technical terms)
- Emotional words (pain, risk, protect, secure)
- Numbers and deadlines
- Brand name in CTA

### Step 4: Suggest assets

Match extracted topics to existing icon catalog or generate new ones:
- Hook icon: Main topic illustration
- Problem icons: One per pain point
- Solution icon: Shield/protection/positive outcome
- CTA icon: Consultation/contact

### Step 5: Write scene JSON

Combine all extracted data into the scene JSON format. Set `_source` fields to track where each scene's content came from for review.

---

## Tips

- **Review the generated JSON** before generating voiceover — the script provides a starting point, not a final script
- **Adapt tone**: Page copy (written for reading) needs rewriting for spoken delivery — shorter sentences, more direct
- **Check compliance**: Run the generated text through your content compliance rules before TTS
- **Reuse icons**: Check if existing icon catalog covers the topic before generating new ones
- **Set word targets**: Reels ~15 words/scene, long-form ~25-50 words/scene
