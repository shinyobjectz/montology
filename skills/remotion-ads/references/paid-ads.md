---
title: Paid Ads Campaign Management
description: Campaign strategy, creative specs, and optimization for Instagram/Meta ads created with Remotion
section: distribution
priority: medium
tags: [paid-ads, meta, instagram, campaigns, targeting, optimization, budget]
---

# Paid Ads Campaign Management

Strategy and optimization guide for running Instagram/Meta ad campaigns with Remotion-generated video and carousel creatives.

---

## Campaign Strategy

### Before Launch

Gather this context:

1. **Goal**: Awareness, traffic, leads, or sales?
2. **Budget**: Daily or lifetime? How much?
3. **Audience**: Demographics, interests, behaviors
4. **Creative**: Which video/carousel assets are ready?
5. **Landing Page**: Where does the ad send people?
6. **Tracking**: UTM parameters, pixel, conversions set up?

### Budget Allocation

| Phase | Proven Campaigns | Testing | Duration |
|-------|-----------------|---------|----------|
| Testing | 70% | 30% | First 2 weeks |
| Scaling | 85% | 15% | Ongoing |

### Campaign Naming Convention

```
{Brand}_{Objective}_{Audience}_{Creative}_{Date}
```

Example: `BrandX_Leads_Homebuyers_AdFeuchtigkeit_2026-02`

---

## Creative Specs for Meta Ads

### Video Ads (Remotion Reels)

| Property | Value |
|----------|-------|
| Aspect Ratio | 9:16 (vertical) |
| Resolution | 1080×1920 |
| Duration | 15 seconds (recommended) |
| Format | MP4, H.264, AAC audio |
| Max File Size | 4GB |
| Captions | Always (85% watch without sound) |

### Carousel Ads (Remotion Carousels)

| Property | Value |
|----------|-------|
| Aspect Ratio | 4:5 or 1:1 |
| Resolution | 1080×1350 (4:5) or 1080×1080 (1:1) |
| Slides | 2-10 images |
| Format | PNG or JPEG |
| Max File Size | 30MB per image |

### Thumbnail / Cover Image

| Property | Value |
|----------|-------|
| Resolution | 1080×1920 |
| Format | JPEG or PNG |
| Content | Key frame from video, readable at small size |

---

## Video Ad Script for Paid Placement

### 15-Second Structure

```
0-3s:   HOOK — Stop the scroll. Question, bold statement, or visual shock.
3-8s:   PROBLEM — Relatable pain point. "You just bought a house and..."
8-13s:  SOLUTION — What you offer. Credibility signal.
13-15s: CTA — "Link in Bio" / "Send us a message" / "Book a free call"
```

### Creative Best Practices

1. **Hook in first 1-2 seconds** — Viewer decides to watch or scroll
2. **Captions always** — 85% of Instagram video is watched without sound
3. **One message per ad** — Don't try to say everything
4. **Show, don't tell** — Use illustrations and icons, not just text
5. **Mobile-first** — Test on phone screen, not desktop
6. **Match landing page** — Visual style and messaging must align

---

## Audience Targeting

### Core Audiences

| Audience Type | Targeting | Use For |
|---------------|-----------|---------|
| Interest-based | Interests + demographics | Cold traffic, awareness |
| Lookalike | Based on best customers (by LTV) | Scaling proven campaigns |
| Retargeting | Website visitors, engagers | High-intent conversions |
| Custom | Email list, app users | Upsells, re-engagement |

### Retargeting Segments

| Segment | Window | Message |
|---------|--------|---------|
| Hot (video viewers 75%+) | 1-7 days | Direct CTA, book now |
| Warm (page visitors) | 7-14 days | Social proof, testimonials |
| Cool (engagers) | 14-30 days | Educational content |
| Cold (broad retarget) | 30-90 days | Brand awareness refresh |

### Exclusions

Always exclude:
- Existing customers (unless upsell campaign)
- People who already converted
- Irrelevant demographics

---

## UTM Parameters

### Standard UTM Structure

```
?utm_source=instagram
&utm_medium=paid
&utm_campaign={campaign_name}
&utm_content={ad_name}
&utm_term={audience_name}
```

### Naming Conventions

| Parameter | Format | Example |
|-----------|--------|---------|
| `utm_source` | Platform | `instagram`, `facebook` |
| `utm_medium` | Channel type | `paid`, `organic` |
| `utm_campaign` | Campaign name | `feuchtigkeit-jan2026` |
| `utm_content` | Creative variant | `reel-v1`, `carousel-v2` |
| `utm_term` | Audience | `lookalike-buyers`, `retarget-7d` |

---

## Optimization

### Key Metrics by Objective

| Objective | Primary Metric | Target |
|-----------|---------------|--------|
| Awareness | CPM (cost per 1000 impressions) | < $8 |
| Traffic | CPC (cost per click) | < $1.50 |
| Leads | CPL (cost per lead) | Varies by industry |
| Sales | ROAS (return on ad spend) | > 3x |

### When CPA Is Too High

| Symptom | Possible Cause | Fix |
|---------|---------------|-----|
| High CPA | Poor landing page | Improve page speed, copy, CTA alignment |
| High CPA | Wrong audience | Tighten targeting, test new segments |
| High CPA | Weak creative | Test new hooks, different ad format |
| High CPM | Audience too small | Broaden targeting, add interests |
| Low CTR | Weak hook/creative | Test new creatives, different hooks |
| Low CTR | Wrong audience | Ad message doesn't match audience |

### Testing Framework

1. **Test one variable at a time**: Hook, audience, or CTA — not all three
2. **Minimum 1000 impressions** before judging
3. **Give algorithms 3-5 days** to optimize before changing
4. **Kill losers fast**: If CPA is 2x target after 1000+ impressions, pause
5. **Scale winners gradually**: Increase budget 20-30% every 3-5 days

---

## Campaign Checklist

### Before Launch
- [ ] Pixel/conversion tracking verified
- [ ] UTM parameters on all URLs
- [ ] Landing page matches ad creative and message
- [ ] Exclusions set (existing customers, converters)
- [ ] Budget and schedule configured
- [ ] Creative passes platform review (no policy violations)
- [ ] Captions on all video ads

### After Launch (Daily)
- [ ] Check spend vs budget
- [ ] Monitor CPM and CTR trends
- [ ] Respond to comments/DMs from ads
- [ ] Pause underperforming creatives (>2x target CPA)

### Weekly Review
- [ ] Top 3 performing ads (why did they work?)
- [ ] Bottom 3 ads (what can you learn?)
- [ ] Audience performance comparison
- [ ] Creative fatigue check (declining CTR over time)
- [ ] Budget reallocation to winners

---

## Related Rules

- [copywriting/ad-copywriting.md](copywriting/ad-copywriting.md) - Script and copy frameworks
- [social-content.md](social-content.md) - Organic social strategy
- [formats.md](formats.md) - Instagram dimension specs
