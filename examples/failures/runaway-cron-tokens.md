# 失败案例: Cron Job 一夜烧光 Token

## 场景描述

团队配置了一个每小时执行的 cron job，用于监控 GitHub Issues 并自动分类标签。

任务本身合理，但配置中犯了一个致命错误：没有设置 `max_iterations` 上限，
也没有 token 用量的 circuit breaker。

周六凌晨 2:00，GitHub API 返回了一个异常响应（rate limit 临时解除后的反弹），
导致 agent 每次调用都收到一个巨大的 JSON payload（~50KB）。

agent 没有 early-exit 逻辑，每次迭代都完整解析这个 payload 并尝试分类所有 issues。
由于 rate limit 不断触发，agent 自动重试，形成了一个 正反馈循环：

```
解析大 payload → 消耗大量 token → 触发 rate limit → 重试 → 再次解析大 payload
```

到周日早上 9:00 用户发现问题时，已经消耗了 **$47.23** 的 API token，
产生了 **2,341 次** LLM 调用，其中 90% 是无效重试。

## 根因分析

缺失的模式：

1. **Circuit Breaker**: 没有连续失败次数上限，重试无限进行
2. **Token Budget**: 没有单次执行的 token 预算硬限制
3. **Heartbeat 监控**: cron job 没有向外部报告运行状态
4. **Graceful Degradation**: 遇到异常 payload 没有 early-exit

## 事故日志（脱敏）

```
[2026-08-16 02:00:01] cron:job started, job=github-issue-classifier, iteration=1
[2026-08-16 02:00:03] llm:call model=claude-sonnet tokens_in=12847 tokens_out=342
[2026-08-16 02:00:04] github:rate_limit_remaining=0 retry_after=60
[2026-08-16 02:01:05] cron:retry attempt=2 reason=rate_limit
[2026-08-16 02:01:07] llm:call model=claude-sonnet tokens_in=12847 tokens_out=341
[2026-08-16 02:01:08] github:rate_limit_remaining=0 retry_after=60
...
[2026-08-16 08:00:01] cron:heartbeat iteration=142 status=retrying
[2026-08-16 08:00:03] llm:call model=claude-sonnet tokens_in=12847 tokens_out=0
[2026-08-16 08:00:03] llm:error context_length_exceeded
[2026-08-16 08:00:04] cron:retry attempt=143 reason=context_length
...
[2026-08-17 09:12:00] user:discovered anomaly, token_usage_24h=$47.23
[2026-08-17 09:12:01] cron:force_stopped by=user
```

关键指标：
- 总迭代次数: 2,341
- 有效迭代: ~240（前 4 小时的正常运行）
- 无效重试: ~2,100
- Token 消耗: ~18M input tokens, ~800K output tokens
- 总费用: $47.23

## 解决方案

### 1. 配置 Circuit Breaker（防无限重试）

```yaml
# ~/.hermes/cron/github-issue-classifier.yaml
cron:
  schedule: "0 * * * *"
  max_iterations: 50          # 单次执行最多 50 轮
  max_consecutive_failures: 3 # 连续 3 次失败则停止
  on_failure: stop            # 而不是 retry
```

### 2. 设置 Token Budget（硬预算限制）

```yaml
# ~/.hermes/config.yaml
token_budget:
  per_task: 50000             # 单任务 50K tokens 上限
  per_hour: 200000            # 每小时 200K tokens
  alert_threshold: 0.8        # 80% 用量时告警
  hard_limit_action: stop     # 超限直接停止
```

### 3. 启用 Heartbeat 监控

```yaml
cron:
  heartbeat:
    enabled: true
    interval: 300             # 每 5 分钟汇报一次
    include: [token_usage, iteration_count, last_error]
    on_silence: alert         # 超过 15 分钟无心跳则告警
```

### 4. 加入 Early-Exit 条件

```python
# 在 cron job 的处理逻辑中
if payload_size > MAX_PAYLOAD_SIZE:
    logger.warning(f"Payload too large ({payload_size}), skipping")
    return  # 而不是继续解析

if consecutive_failures >= 3:
    logger.error("Circuit breaker triggered")
    raise CircuitBreakerOpen()
```

## 关联模式

- [cron-job-pattern](../../conventions/cron-job-pattern.md) — Circuit breaker、max_iterations、heartbeat
- [anti-patterns](../../conventions/anti-patterns.md) — "无限重试"反模式
- [error-compact-pattern](../../conventions/error-compact-pattern.md) — 错误压缩防止 token 浪费
- [secret-management](../../conventions/secret-management.md) — API key 的用量监控
