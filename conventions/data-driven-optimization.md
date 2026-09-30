---
name: data-driven-optimization
description: "数据驱动技能优化 — 以真实运营数据驱动技能迭代,技能是活文档"
version: 1.1.0
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
migration: "v1.0.0 → v1.1.0:新增「标定闭环」章节(评测集→分离度检验→--fresh 重跑→policy.calibration 写回;弃权单列,有序档位用档位距离)"
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

## 标定闭环：用评测集校准阈值与 rubric（2026-09-30 新增）

> 上游文档：`conventions/decision-contract.md`。本节是它的**数据侧**落地：阈值和 rubric 都不是拍出来的，是用评测集标定出来的。

### 闭环五步

1. **先建集再看阈值** —— 每个判断一个 `datasets/<decision>.jsonl`，行格式 `{"state":..., "expected":..., "metadata":{...}}`。没有集就调阈值 = 猜。
2. **跑基线** —— 一次跑出 `accuracy`（精确）、`accuracy_answered`（排除弃权）、`abstained_rate`（弃权率）、`near_accuracy` + `mae_rank`（有序档位的差档距离）。
3. **做分离度检验** —— 比「真值上的置信度中位」vs「错值上的中位」。**分得开才动阈值；分不开就去改 rubric**。
4. **改完用 `--fresh` 重跑** —— 绕过 replay 重新问后端，避免拿旧记录自我背书；日常回归则不 `--fresh`，走 replay 保持可比。
5. **写回 policy 的 calibration 段** —— 记录 n / accuracy / 中位数 / 日期，让下一次改动有对照。

### 三条实测教训

- **置信度不区分对错时，阈值无效。** 实测某打分决策真值中位 0.92、错值中位 0.88，唯一错的那行置信度 1.0 —— 此时把阈值调高只是把好答案也拦下来。问题在 rubric/刻度，不在阈值。
- **有序档位别用精确匹配当唯一指标。** 「差一档」和「差三档」不是一回事：实测一个 4 档相关度决策精确 0.722、差一档内 0.944、平均档位距离 0.333。只报精确匹配会把「边界有争议」误读成「几乎不可用」。
- **弃权 ≠ 答错。** 判断拒答、交给人类是正确的失败模式。把它算成错误会得出反向结论：实测某「是否升级人类」决策被算成 0.583，排除弃权后其实是 1.000。指标里弃权必须单列。

### 反模式

| 反模式 | 后果 |
|:---|:---|
| 未建集先调阈值 | 调的是手感，不是数据 |
| 只看精确匹配 | 有序档位的真实水平被低估，误判为不可用 |
| 把弃权算成答错 | 越谨慎的系统得分越低，指标反向激励 |
| 用 `--fresh` 的旧结果做回归对比 | 概率后端抖动混进结论，无法判断是改好了还是抖好了 |
| 改完 rubric 不 bump 契约 version | 历史记录被复用，回归对比串台 |

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
