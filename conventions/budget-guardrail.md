---
name: budget-guardrail
description: "成本护栏 — 三级预算响应(预警/降级/熔断)防止 token/API 调用失控"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, budget, cost, guardrail]
    category: conventions
    related_skills: [cron-job-pattern, state-file-pattern, error-compact-pattern]
hpp_category: reliability
hpp_en: "Three-tier budget guardrail: warn, degrade, circuit-break."
hpp_maturity: L1
hpp_complexity: medium
hpp_reliability: high
hpp_capability: cron
maturity: experimental
---

# 成本护栏 — 三级预算响应

> **对应 12-Factor Agents Factor 10: Resource Limits**
> **目标：防止 token/API 调用在无人值守时失控，把成本事故变成可预期的梯度响应**

## 问题场景

### 真实案例：Cron 任务夜间烧 token

某定时任务每天凌晨 3:00 跑新闻摘要，正常消耗约 8k token/次。某天上游网站改版导致解析失败，Agent 进入无限重试循环。8 小时后人工发现时，已消耗 **120 万 token**（约 $18），相当于 150 次正常运行的总和。

**根因**：没有预算上限、没有预警机制、没有自动熔断。Agent 会"忠诚地"执行到天荒地老。

**其他高风险场景**：
- API 调用频率失控（爬虫循环、重试风暴）
- 多 Cron 任务同时运行互相放大
- LLM Provider 按 token 计费，一个 runaway agent 吃掉月度预算
- 免费额度耗尽后自动切到付费 tier，账单飙升

## 三级响应机制

```text
监控循环：每次 LLM 调用 / API 调用后 → 计算累计消耗 → 对比阈值 → 触发对应级别
```

### L1: 预警（Warning）— 80% 阈值

**触发**：当期预算消耗 ≥ 80%

**动作**：
1. 写入 STATE.md `budget_status` 为 `warning`
2. 记录当前消耗详情（token 数、API 调用次数、来源任务）
3. Agent 继续运行，但上下文中注入预算警告
4. 可选：推送通知到 IM（Slack/Telegram/飞书）

```python
if budget_used >= budget_limit * 0.8:
    state["budget_status"] = "warning"
    state["budget_warning_at"] = now_iso()
    context.append(
        f"[BUDGET_WARNING] 已用 {budget_used}/{budget_limit} "
        f"({budget_used/budget_limit*100:.0f}%)。请控制后续消耗。"
    )
    notify_human(f"⚠️ 预算预警: {task_name} 已用 {pct}%")
```

### L2: 降级（Degradation）— 90% 阈值

**触发**：当期预算消耗 ≥ 90%

**动作**：
1. 写入 STATE.md `budget_status` 为 `degraded`
2. 自动切换到更小/更便宜的模型（如 `gpt-4o` → `gpt-4o-mini`）
3. 减少 Cron 任务频率（如每小时 → 每 4 小时）
4. 降低重试次数上限（如 3 次 → 1 次）
5. 裁剪上下文长度（减少 history/window 大小）

```python
if budget_used >= budget_limit * 0.9:
    state["budget_status"] = "degraded"
    state["degraded_at"] = now_iso()
    # 降级策略
    apply_degradation({
        "model": "gpt-4o-mini",           # 切小模型
        "retry_max": 1,                    # 减少重试
        "cron_frequency": "every 4h",      # 降频
        "context_window": 4096,            # 缩上下文
    })
```

### L3: 熔断（Circuit-Break）— 100% 阈值

**触发**：当期预算消耗 ≥ 100%

**动作**：
1. **立即停止**当前任务执行
2. 写入 STATE.md `budget_status` 为 `circuit_broken`
3. 记录熔断时间、最终消耗、触发任务
4. 暂停相关 Cron 任务（`cron set enabled=false`）
5. 推送紧急通知到人类

```python
if budget_used >= budget_limit:
    state["budget_status"] = "circuit_broken"
    state["circuit_broken_at"] = now_iso()
    state["final_consumption"] = budget_used
    write_state(state)
    pause_cron_tasks(related_tasks)
    notify_human(
        f"🔴 预算熔断: {task_name} 已达上限 "
        f"{budget_used}/{budget_limit}，任务已暂停"
    )
    raise BudgetExceeded(f"Budget limit {budget_limit} reached")
```

### 状态流转图

```text
normal ──80%──▶ warning ──90%──▶ degraded ──100%──▶ circuit_broken
  ▲                                                    │
  └──────────── 新预算周期重置 ◀─────────────────────────┘
```

每个预算周期（日/周/月）开始时重置状态：

```python
def reset_budget_if_new_period(state: dict, period: str) -> dict:
    if is_new_period(state.get("budget_period_start"), period):
        state["budget_status"] = "normal"
        state["budget_used"] = 0
        state["budget_period_start"] = now_iso()
    return state
```

## 阈值配置示例

```yaml
# config.yaml 或 .hermes/config.yaml 中的 budget 配置
budget:
  # 全局预算
  global:
    period: daily                    # daily | weekly | monthly
    limit: 500000                    # token 上限（或 API 调用次数）
    currency: token                  # token | usd | api_calls

  # 三级阈值（百分比）
  thresholds:
    warning: 0.80                    # 80% 触发预警
    degradation: 0.90                # 90% 触发降级
    circuit_break: 1.00              # 100% 触发熔断

  # 降级策略
  degradation:
    model_downgrade: gpt-4o-mini     # 降级时使用的模型
    retry_max: 1                     # 降级后最大重试次数
    frequency_divisor: 4             # Cron 频率除数（every 1h → every 4h）
    context_window_limit: 4096       # 降级后上下文窗口

  # 通知配置
  notify:
    warning: [telegram, log]         # 预警通知渠道
    degradation: [telegram, log]     # 降级通知渠道
    circuit_break: [telegram, email, log]  # 熔断通知渠道

  # 按任务覆盖
  overrides:
    news-digest:
      limit: 50000                   # 该任务独立限额
      period: daily
    market-scan:
      limit: 100000
      period: weekly
```

### 最小配置（快速接入）

```yaml
# 只配全局限额，阈值使用默认值
budget:
  global:
    period: daily
    limit: 200000
```

## 与 cron-job-pattern 的联动

### Pre-flight 中加入预算检查

在 cron-job-pattern 的三段式 Pre-flight 阶段，**第一步**就检查预算：

```markdown
### Pre-flight（加入预算检查后）

1. **读取 STATE.md，检查 budget_status**
   - 如果 budget_status == circuit_broken → 跳过本次运行，记录原因
   - 如果 budget_status == degraded → 应用降级策略后继续
   - 如果 budget_status == warning → 注入警告上下文后继续
   - 如果 budget_status == normal → 正常执行
2. 读取 STATE.md，检查上次运行状态
3. 检查 Idempotency Keys，跳过已处理的批次
4. 检查资源可用性（磁盘/网络/API Key）
```

### Post-flight 中更新预算消耗

```markdown
### Post-flight（加入预算更新后）

1. **累计本次运行 token 消耗，写入 STATE.md budget_used**
2. **对比阈值，更新 budget_status**
3. 更新 STATE.md（status → idle，记录统计）
4. 生成运行报告
5. 如果 budget_status 升级 → 推送通知
```

### 实现示例

```python
def preflight_budget_check(state: dict) -> str:
    """Pre-flight 预算检查，返回 'proceed' | 'degrade' | 'halt'"""
    status = state.get("budget_status", "normal")
    if status == "circuit_broken":
        log("[BUDGET] 预算已熔断，跳过本次运行")
        return "halt"
    elif status == "degraded":
        log("[BUDGET] 预算降级模式，使用轻量配置")
        return "degrade"
    elif status == "warning":
        log("[BUDGET] 预算预警，注意控制消耗")
    return "proceed"

def postflight_budget_update(state: dict, tokens_used: int) -> dict:
    """Post-flight 预算更新"""
    state["budget_used"] = state.get("budget_used", 0) + tokens_used
    limit = state.get("budget_limit", 500000)
    pct = state["budget_used"] / limit

    if pct >= 1.0:
        state["budget_status"] = "circuit_broken"
    elif pct >= 0.9:
        state["budget_status"] = "degraded"
    elif pct >= 0.8:
        state["budget_status"] = "warning"
    return state
```

## 与 state-file-pattern 的联动

### STATE.md 中标准化预算字段

预算状态应作为 STATE.md 的**一等字段**，与 `status`、`last_run` 同级：

```markdown
## STATE.md 预算字段

### Budget Control
- **budget_period**: daily
- **budget_limit**: 500000
- **budget_used**: 387420 (77.5%)
- **budget_status**: normal | warning | degraded | circuit_broken
- **budget_period_start**: 2026-09-04T00:00:00+08:00
- **budget_warning_at**: (warning 触发时间)
- **budget_degraded_at**: (degraded 触发时间)
- **budget_circuit_broken_at**: (circuit_broken 触发时间)
- **budget_breakdown**:
  - news-digest: 45200 tokens
  - market-scan: 128000 tokens
  - ad-hoc: 214220 tokens
```

### 与 state-schema.json 的关系

预算字段应同步更新到 `state-schema.json`：

```json
{
  "budget_status": {
    "type": "string",
    "enum": ["normal", "warning", "degraded", "circuit_broken"],
    "default": "normal"
  },
  "budget_used": {
    "type": "integer",
    "minimum": 0
  },
  "budget_limit": {
    "type": "integer",
    "minimum": 0
  }
}
```

## 与 error-compact-pattern 的联动

预算相关错误使用 error-compact-pattern 的分类桶：

| 错误场景 | 归类 | 处理 |
|:---|:---|:---|
| 单次 API 调用超预算 | 💥 致命 | 立即熔断 |
| Rate Limit 被限流 | 🔁 可重试 | 退避重试，但计入预算 |
| Provider 切换到付费 tier | 🔐 认证/配置 | 通知人类，不自动续 |
| Token 计数异常（负数/溢出） | 📐 结构 | 忽略该次，用上一次值 |

```
[BUDGET_EXCEEDED] news-digest@2026-09-04T03:47:00
  Error: BudgetExceeded - 消耗 501200/500000 tokens
  Hint: 已自动熔断，任务暂停。检查是否有重试风暴。
  Recoverable: NO（需新预算周期或人工重置）
  Impact: 当前任务及关联 Cron 暂停
```

## 实现清单

接入 budget-guardrail 需要以下步骤：

```
1. [ ] 在 config.yaml 中添加 budget 配置块
2. [ ] 在 STATE.md 模板中添加 Budget Control 字段
3. [ ] 在 state-schema.json 中添加预算字段 schema
4. [ ] 在 Cron Pre-flight 中集成 preflight_budget_check()
5. [ ] 在 Cron Post-flight 中集成 postflight_budget_update()
6. [ ] 配置通知渠道（Telegram/Email/Slack）
7. [ ] 为高消耗任务配置 overrides
8. [ ] 写一个 mock 测试：模拟消耗到 80%/90%/100% 验证三级响应
```

## 实测数据

> **TODO：以下为 placeholder，待真实运行数据回填**

### 测试环境

- Hermes 版本：x.x.x
- Provider：OpenAI (gpt-4o / gpt-4o-mini)
- 测试任务：模拟 news-digest Cron 任务
- 预算配置：daily 50,000 tokens

### 测试结果

| 场景 | 预期行为 | 实际行为 | 耗时 |
|:---|:---|:---|:---|
| 消耗到 80% | 触发 warning，写 STATE.md | _待测_ | _待测_ |
| 消耗到 90% | 切换 gpt-4o-mini，降频 | _待测_ | _待测_ |
| 消耗到 100% | 熔断，暂停 Cron，通知 | _待测_ | _待测_ |
| 新周期开始 | 状态重置为 normal | _待测_ | _待测_ |
| 预算为 0（禁用） | 跳过所有检查 | _待测_ | _待测_ |
| 多任务并发消耗 | 全局预算正确累计 | _待测_ | _待测_ |

### 成本对比

| 指标 | 无护栏（1周） | 有护栏（1周） |
|:---|:---:|:---:|
| 最大单次事故消耗 | ~$18 | ≤$0.10 |
| 日均 token 消耗 | 不可控 | ≤预算上限 |
| 人工干预次数 | 1-2 次/周 | 0 次（自动降级/熔断） |
| Cron 空跑浪费 | ~40k tokens | 0（熔断后不执行） |
