# WeChat Article Pipeline Example

## Goal

Use Hermes Agent to write, detect AI-taste, de-AI-fy, and publish WeChat Official Account articles. The skill is continuously optimized using real account analytics data — not guesswork.

## Maturity Level

**L2** (semi-autonomous). Agent drafts the full article and generates diagrams. Human reviews and publishes. The analytics feedback loop runs weekly to refine title strategy, content structure, and topic selection.

## Files

```text
examples/wechat-article-pipeline/
├── SKILL.md              # wechat-viral-article skill (main pipeline)
├── scripts/
│   ├── ai_detect.py      # 8-dimension AI-taste scoring engine
│   └── de_ai.py          # AI-taste removal + repair instructions
└── references/
    └── article-template.md  # Obsidian YAML frontmatter template
```

## How It Works

### The 9-Step Writing SOP

```text
Step 1: Topic selection   → 3 directions (source code / pitfalls / comparison)
Step 2: Research           → web search + official docs + GitHub issues
Step 3: Outline            → choose from 4 proven templates
Step 4: Draft              → 2000-4000 characters, inline image markers
Step 5: AI-taste detect    → scripts/ai_detect.py, target <20%
Step 6: De-AI-fy           → scripts/de_ai.py + 8-step manual method
Step 7: Generate diagrams  → draw.io CLI, brand color system
Step 8: Final check        → headline checklist + layout + image positions
Step 9: Save to Obsidian   → /今日头条/{title}.md with YAML frontmatter
```

### The Analytics Feedback Loop

The skill includes real account data from July 2026 (13 followers, 8 articles, 238 recommendation reads/week) that validates:

1. **「XXEngineering」naming convention** is the strongest IP asset — Engineering-series articles averaged **81 reads** vs **57 reads** for non-series articles
2. **Concept/framework articles outperform tool/list articles** — frameworks averaged 108 reads, tools averaged 55
3. **Recommendation algorithm favors high-completion + high-engagement content** — publish every 2-3 days during the boost window

These findings are baked into the skill's hard requirements checklist:
- Title format: `XXEngineering: subtitle` (mandatory)
- Content type: concept/framework/methodology only (no tool lists)
- Minimum 1 architecture diagram + 2 code screenshots
- Ending: interactive question + next-preview teaser
- AI concentration: <20%

## Loop

1. Read `STATE.md` to check the publishing schedule and next planned topic.
2. Consult the performance data of past articles to select the next topic with highest potential.
3. Agent writes the full draft following the 9-step SOP.
4. Run `scripts/ai_detect.py` on the draft. If concentration >20%, run `scripts/de_ai.py`.
5. Generate architecture diagrams via draw.io CLI (brand colors: #1a1a2e dark, #00d4ff blue).
6. Save final article to Obsidian vault + paste into WeChat backend.
7. Update `STATE.md` with publish date, actual reads after 48h, and lessons learned.

## What Makes This Different

Most article-writing pipelines just generate text. This pipeline:

- **Detects and removes AI-taste** programmatically (8-dimension rule engine + LLM-assisted rewrite)
- **Is data-driven** — the skill file itself contains real analytics from the account's first month, so every writing decision is informed by what actually worked
- **Bakes the IP** into the naming convention — the account's "XXEngineering" series identity is enforced at the title level
- **Generates professional diagrams** via draw.io with a consistent brand color system

## Dependencies

- Hermes Agent v0.6+
- draw.io desktop app
- Obsidian vault at `/Volumes/DISCa/Hermes Vault/Hermes Vault`
- Python 3.10+ (for ai_detect.py and de_ai.py)
