---
name: data-driven-optimization
description: "数据驱动技能优化 — 以真实运营数据驱动技能迭代,技能是活文档"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, skill, optimization, analytics]
    category: conventions
    related_skills: [evolution-gate, anti-patterns, skill-evolution]
hpp_category: evolution
hpp_en: "Let real operational data drive skill iterations."
hpp_maturity: L3
hpp_complexity: medium
hpp_reliability: medium
hpp_capability: analytics
maturity: beta
hpp_when_to_use: ["Mature agents with usage logs"]
hpp_when_not_to_use: ["Pre-launch intuition phase"]
---

# Data-Driven Skill Optimization Convention

## Problem

Skills written in a vacuum drift from reality. The agent follows a well-structured procedure, but the output quality degrades over time because the skill has no feedback loop — it never learns what actually works.

## Solution

Embed real analytics data directly into the skill file, then use it to constrain every decision the agent makes. The skill becomes a living document that evolves with your account.

## How It Works

### 1. Collect Real Data

Before writing or updating a skill, pull actual performance metrics from your production environment:

```text
Article          Reads   Likes   Type
LoopEngineering  112     13      Framework
三层记忆架构       109     11      Framework
GraphEngineering 103     15      Framework
PromptEng         76     11      Methodology
工具生态            55      5      ❌ Tool list
```

### 2. Derive Hard Constraints

From the data, extract three types of constraints:

**Positive constraints** (things that work — must do):
- "XXEngineering" naming → 81 avg reads vs 57 non-series
- Framework articles → 108 avg reads

**Negative constraints** (things that don't work — must not do):
- Tool lists → 55 avg reads, never break 100
- Purely introductory content → 9 reads

**Tactical constraints** (execution rules):
- Publish every 2-3 days (matches algorithm boost window)
- Minimum 1 architecture diagram per article
- End with open question + next-preview teaser

### 3. Bake Constraints Into the Skill

The raw data and derived constraints are placed at the top of the skill file, before any procedural steps. Every time the agent loads the skill, it sees "this is what worked" before it sees "this is what to do."

### 4. The Loop

```text
┌──────────────────────────┐
│ Publish article          │
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│ Wait 48h (data window)   │
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│ Pull read/like/share #s  │
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│ Update constraints       │
│  → Add new findings      │
│  → Demote outdated ones  │
│  → Remove disproven ones │
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│ Next article is smarter  │
└──────────────────────────┘
```

## State File

Store optimization data in `STATE.md` under the skill directory:

```yaml
# STATE.md
last_updated: 2026-07-29
articles_published: 8
current_constraints:
  naming: "XXEngineering: subtitle"  # mandatory
  type: framework                      # no tool lists
  frequency: every 2-3 days
  min_diagrams: 1
performance_summary:
  engineering_series_avg: 81
  non_series_avg: 57
  best_topic: agent_framework_comparison
```

## When to Use

Use this convention whenever the skill produces content that will be consumed by real users or evaluated by a recommendation algorithm. The list includes:

- Social media/content publishing pipelines
- Email/newsletter drafting skills
- Code generation skills used in production
- Report/dashboard generation skills

## Anti-Patterns

- **Confirmation bias** — Don't remove a finding after one bad article. Require 3+ data points.
- **Overfitting** — Don't optimize for 13-follower patterns if your account grows 10x. Re-check constraints every 20 articles.
- **Static data** — Data ages. Add a `last_validated` field and refresh monthly.
