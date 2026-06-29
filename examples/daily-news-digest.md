# 示例：每日 AI 新闻摘要 Cron 任务

> 演示 STATE.md + 控制流分离 + 错误压缩的完整集成

## 1. 创建状态文件

```markdown
# STATE: daily-ai-digest

## Current Run
- Last run: —
- Status: idle
- Current batch: 2026-06-29

## Progress
| Metric | Value |
|--------|-------|
| Sources fetched | 0 |
| Articles summarized | 0 |
| Failures | 0 |

## Lessons Learned
(empty)

## Idempotency Keys
(empty)
```

## 2. 控制流分离（伪代码）

```python
# 确定性路线：抓取 RSS
for source in RSS_SOURCES:
    try:
        articles = fetch_rss(source)         # ✅ 确定性
    except TimeoutError:
        log_compact_error(source, "timeout") # 🔁 可重试

# LLM 路线：写摘要
for article in articles:
    summary = await llm.summarize(article)   # ❌ 概率性
    # Checker 验证摘要质量
    if not checker.validate(summary):
        retry_count += 1
        if retry_count > 3:
            log_compact_error(article.id, "summary_failed")
            continue
```

## 3. 每次运行后的状态更新

```
# STATE: daily-ai-digest (运行后)
## Current Run
- Last run: 2026-06-29T08:30:00+08:00
- Status: idle

## Progress
| Metric | Value |
|--------|-------|
| Sources fetched | 12 |
| Articles summarized | 8 |
| Failures | 1 |

## Lessons Learned
- 2026-06-28: Source-X rate-limits at 10 req/min; space requests 5s apart

## Idempotency Keys
- 2026-06-29: digest-2026-06-29 (✅ done)
```
