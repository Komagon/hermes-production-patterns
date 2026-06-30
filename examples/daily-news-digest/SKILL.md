---
name: daily-news-digest
description: 定时抓取 RSS 源，用 LLM 生成中文新闻摘要，遵循 STATE.md 状态管理和 Maker/Checker 验证
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

> 实时演示 [conventions/](../conventions/) 中全部四条工程公约的完整集成：
> - **[state-file-pattern](../conventions/state-file-pattern.md)** — STATE.md 跨运行状态
> - **[control-flow-separation](../conventions/control-flow-separation.md)** — 抓取用代码 / 摘要用 LLM
> - **[maker-checker](../conventions/maker-checker.md)** — Checker 五维验证摘要质量
> - **[error-compact-pattern](../conventions/error-compact-pattern.md)** — 错误不炸上下文

## 工作流

### Step 1: 读取状态（确定性）✅

从 `STATE.md` 读取上次运行状态和 idempotency keys。

### Step 2: 抓取 RSS（确定性）✅

```python
# 零 LLM 成本。只处理上次运行后新增的文章。
import feedparser

for url in RSS_SOURCES:
    feed = feedparser.parse(url)
    new = [entry for entry in feed.entries
           if entry.id not in state.get("idempotency_keys", [])]
```

### Step 3: LLM 摘要（概率性）❌

```python
# 每日限 5 篇，控制 token 开销。
for article in new[:5]:
    summary = await llm.complete(
        f"按三点总结，每条不超过20字：\n标题：{article.title}\n{article.description}"
    )
```

### Step 4: Checker 验证（概率性）❌

独立 Agent 对摘要做五维评分，≥ 40/50 PASS。

### Step 5: 更新状态（确定性）✅

```python
state["progress"]["articles_summarized"] += len(passed)
state["idempotency_keys"].extend([a.id for a in processed])
atomic_write("STATE.md", state)  # 原子写入 + 文件锁
```

## 错误处理

```python
# 按 error-compact-pattern 压缩错误
try:
    feed = feedparser.parse(url)
except Exception as e:
    compact = f"[STEP_FAILED] fetch_rss@{now}\n  Error: {type(e).__name__} - {str(e)[:80]}\n  Recoverable: YES (retry with backoff)"
    context.append(compact)
```

## 输出格式

```markdown
# 新闻摘要 {YYYY-MM-DD}

## 📰 {article.title}
- {point 1}
- {point 2}
- {point 3}
```
