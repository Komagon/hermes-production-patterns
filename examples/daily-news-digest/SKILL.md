---
name: daily-news-digest
description: 每天定时抓取指定 RSS 源，用 LLM 生成中文新闻摘要，保存到 Obsidian
version: 1.0.0
triggers:
  - "run daily digest"
  - "fetch today's news"
  - "生成今日摘要"
tools:
  - terminal
  - read_file
  - write_file
  - web_extract
mutating: true
---

# Daily News Digest

> 按 STATE.md 规范管理跨运行状态，按控制流分离原则区分抓取和总结步骤。

## 前置条件

- 已设置 `reports/daily-news-digest/STATE.md`
- RSS 源列表在脚本中配置

## 工作流

### Step 1: 读取状态

读取 `STATE.md`，检查 idempotency keys 避免重复处理。

### Step 2: 确定性路线 — 抓取 RSS（零 LLM 成本）

```python
# ✅ DETERMINISTIC — known, predictable, zero LLM cost
import feedparser
for source in RSS_SOURCES:
    articles = feedparser.parse(source)
    # 只处理新增的文章
    new = [a for a in articles if a.id not in state["idempotency_keys"]]
```

### Step 3: 概率性路线 — LLM 摘要

```python
# ❌ STOCHASTIC — LLM reasons, output is probabilistic
for article in new[:5]:  # 每日限 5 篇
    summary = await llm.complete(f"用三点总结这篇中文新闻：{article.text}")
```

### Step 4: 更新状态

```python
state["progress"]["articles_summarized"] += len(summaries)
state["idempotency_keys"].extend([a.id for a in new])
# 写入 STATE.md
```

## 验证

- Checker 验证每篇摘要质量（五维评分 ≥ 40/50）
- FAIL 的摘要标记重试，上限 3 次

## 输出格式

```markdown
# 新闻摘要 {YYYY-MM-DD}

## 📰 {article.title}
- 来源：{source}
- 要点 1
- 要点 2
- 要点 3
```
