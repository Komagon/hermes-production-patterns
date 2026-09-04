---
name: human-escalation
description: "人工介入升级 — 高风险/低置信度/连续失败时升级到人工兜底"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, escalation, human-in-the-loop]
    category: conventions
    related_skills: [maker-checker, state-file-pattern, error-compact-pattern]
hpp_category: reliability
hpp_en: "Escalate to human when risk exceeds agent confidence."
hpp_maturity: L1
hpp_complexity: medium
hpp_reliability: high
hpp_capability: delegate
maturity: experimental
---

# Human Escalation — 人工介入升级

当 Agent 超出自身能力边界时，自动升级到人工兜底，而不是盲目重试或静默失败。

## 升级触发条件

三种硬触发，满足任一即进入 escalation 流程：

### 1. 高风险操作（High-Risk Operations）

| 操作类型 | 示例 | 升级阈值 |
|---------|------|---------|
| 不可逆删除 | `rm -rf`、删除数据库记录、清空 bucket | 必须升级 |
| 公开发布 | 发布文章、推送代码到 production、发送邮件 | 必须升级 |
| 资金支出 | API 付费调用、转账、购买订阅 | 金额 > 0 即升级 |
| 权限变更 | 修改 IAM policy、更新 SSH key、变更 DNS | 必须升级 |

实现方式：在 tool registry 中为每个 tool 打标 `risk_level`，Agent 在调用前检查。

```python
HIGH_RISK_TOOLS = {
    "delete_file": "irreversible",
    "publish_article": "public",
    "api_payment": "financial",
    "git_push_production": "deployment",
}

def should_escalate(tool_name: str, args: dict) -> bool:
    risk = HIGH_RISK_TOOLS.get(tool_name)
    if risk:
        return True
    # 检查参数中的金额
    if args.get("amount", 0) > 0:
        return True
    return False
```

### 2. 低置信度判断（Low Confidence）

当 Agent 对自身输出的质量评估低于阈值时触发：

- **内容质量**：AI 自评分数 < 0.6（如文章可读性、代码 review 分）
- **分类歧义**：分类置信度落在 0.4–0.6 的"灰色地带"
- **多义解读**：用户请求存在 ≥ 2 种合理解读且 Agent 无法确定

```
置信度评估示例（文章发布场景）:
├── AI 检测器分数: 0.72 (通过)
├── 可读性评分:   0.58 (低于阈值 0.6)
├── 事实核查:     0.45 (低置信度)
└── 综合判断:     ESCALATE → "文章事实核查置信度低，需人工确认"
```

### 3. 连续失败（Consecutive Failures）

同一任务链连续失败 N 次后停止重试并升级：

| 失败次数 | 行为 |
|---------|------|
| 1–2 次 | 自动重试，换策略 |
| 3 次 | 升级到人工，附带失败日志 |
| 同一错误模式 ≥ 5 次 | 升级并建议跳过该任务 |

配置化实现：

```yaml
# .hermes/config.yaml
escalation:
  max_retries_before_escalate: 3
  same_error_pattern_threshold: 5
  retry_strategies: [exponential_backoff, alternative_tool, rephrase_query]
```

## 升级通道设计

从简到繁，按部署复杂度递增：

### Level 1: Webhook（最简实现）

一个 HTTP POST 就够，适合任何团队：

```python
import httpx, json
from datetime import datetime

async def escalate_via_webhook(
    webhook_url: str,
    task_id: str,
    reason: str,
    context: dict,
    suggested_action: str = "approve_or_reject",
):
    payload = {
        "task_id": task_id,
        "reason": reason,
        "context": context,
        "suggested_action": suggested_action,
        "timestamp": datetime.utcnow().isoformat(),
        "callback_url": f"https://your-agent.example.com/escalation/{task_id}/respond",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
    return {"status": "escalated", "task_id": task_id}
```

Webhook 接收方可以是 Slack Incoming Webhook、飞书机器人、或自建 dashboard。

### Level 2: 邮件（Email）

适合低频高风险操作，人工有充足时间响应：

```python
import smtplib
from email.mime.text import MIMEText

def escalate_via_email(
    to: str,
    subject: str,
    task_id: str,
    reason: str,
    context: dict,
):
    body = f"""
    [Hermes Agent 升级通知]

    任务 ID: {task_id}
    升级原因: {reason}

    上下文:
    {json.dumps(context, indent=2, ensure_ascii=False)}

    请回复:
      APPROVE {task_id}  — 批准执行
      REJECT  {task_id}  — 拒绝并中止
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "agent@your-domain.com"
    msg["To"] = to

    with smtplib.SMTP("smtp.your-domain.com") as s:
        s.send_message(msg)
```

### Level 3: 企业 IM（企业微信/钉钉/Slack）

生产环境首选，支持卡片交互：

```python
# 企业微信 webhook 示例
async def escalate_via_wecom(webhook_url: str, task_id: str, reason: str, context: dict):
    card = {
        "msgtype": "interactive",
        "interactive": {
            "card": {
                "header": {"title": {"tag": "plain_text", "content": "⚠️ Agent 升级请求"}},
                "elements": [
                    {"tag": "div", "text": {"tag": "plain_text", "content": f"任务: {task_id}\n原因: {reason}"}},
                    {
                        "tag": "action",
                        "actions": [
                            {"tag": "button", "text": {"tag": "plain_text", "content": "✅ 批准"}, "type": "primary", "value": {"action": "approve", "task_id": task_id}},
                            {"tag": "button", "text": {"tag": "plain_text", "content": "❌ 拒绝"}, "type": "danger", "value": {"action": "reject", "task_id": task_id}},
                        ],
                    },
                ],
            }
        },
    }
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=card)
```

### 通道选择决策树

```
需要升级?
├── 频率 < 1次/天 → 邮件 (足够)
├── 需要即时响应 → 企业 IM 卡片
├── 需要集成到现有系统 → Webhook + 自建 dashboard
└── 兜底 → 写入本地 STATE.md + 等待下次 session 检查
```

## 升级后状态机

```
                          ┌─────────────────────────────────┐
                          │                                 │
                          ▼                                 │
┌───────┐  触发条件   ┌────────────┐   超时未响应    ┌──────┴─────┐
│RUNNING│───────────→│ ESCALATED  │───────────────→│  TIMEOUT   │
│       │            │            │                 │ (自动拒绝) │
└───────┘            │ waiting_   │                 └────────────┘
    ▲                │ human      │                        │
    │                └─────┬──────┘                        │
    │                      │                               │
    │          ┌───────────┴───────────┐                   │
    │          │                       │                   │
    │          ▼                       ▼                   │
    │   ┌────────────┐         ┌────────────┐             │
    │   │ CONFIRMED  │         │  REJECTED  │←────────────┘
    │   │ (人工批准)  │         │ (人工拒绝)  │
    │   └─────┬──────┘         └─────┬──────┘
    │         │                      │
    │         ▼                      ▼
    │   ┌────────────┐         ┌────────────┐
    │   │  RESUMED   │         │  ABORTED   │
    └───│ (恢复执行)  │         │ (中止任务)  │
        └────────────┘         └────────────┘
```

### 状态定义

| 状态 | 含义 | Agent 行为 |
|------|------|-----------|
| `RUNNING` | 正常执行 | 按计划推进 |
| `ESCALATED` | 等待人工响应 | 暂停，定期检查回调 |
| `CONFIRMED` | 人工批准 | 从暂停点恢复执行 |
| `REJECTED` | 人工拒绝 | 清理已做工作，记录原因 |
| `TIMEOUT` | 超时未响应 | 按配置：自动拒绝 or 再次升级 |
| `RESUMED` | 恢复执行 | 继续后续步骤 |
| `ABORTED` | 最终中止 | 写入 STATE.md，等待下次 session |

### 超时与重试策略

```yaml
escalation:
  timeout_minutes: 30          # 默认等待 30 分钟
  on_timeout: reject           # reject | re_escalate | park
  re_escalate_channel: email   # 二次升级换通道
  max_escalations: 2           # 最多升级 2 次，之后 park
```

### 回调接口

Agent 需要暴露一个 HTTP endpoint 接收人工响应：

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/escalation/{task_id}/respond")
async def handle_escalation_response(task_id: str, action: str, comment: str = ""):
    """
    action: "approve" | "reject"
    """
    # 更新 STATE.md 中的任务状态
    await update_task_state(task_id, status=action, human_comment=comment)
    # 如果是 approve，触发任务恢复
    if action == "approve":
        await resume_task(task_id)
    return {"status": "ok"}
```

## 与 maker-checker 的边界区分

| 维度 | Human Escalation | Maker-Checker |
|------|-----------------|---------------|
| **参与者** | Agent → **Human** | Agent → **Agent** |
| **触发方式** | 条件触发（风险/置信度/失败） | 流程内置（每步都走） |
| **响应时间** | 秒级到小时级 | 毫秒级 |
| **适用场景** | 低频高风险兜底 | 高频常规校验 |
| **可跳过性** | 正常流程不触发 | 不可跳过 |
| **典型例子** | 发布文章前确认 | 代码生成后 review |

**简单原则**：

- **Maker-Checker**：两个 Agent 之间的质量校验，是流水线的一部分
- **Human Escalation**：Agent 撞到能力边界了，需要人类兜底

两者可以组合：Maker-Checker 流水线中的 Checker 判定"不确定"时，触发 Human Escalation。

## 真实场景示例

### 场景 1：自动发布文章

```
Agent 生成文章 → AI 检测器评分 0.45 (低) → 触发升级
├── 升级原因: "AI 检测分数 0.45 低于阈值 0.6"
├── 通道: 企业微信卡片
├── 人工操作: 查看文章 → 点击"批准"
└── Agent 恢复: 发布文章到博客
```

### 场景 2：数据库清理

```
Agent 执行清理任务 → 发现需要 DROP TABLE → 触发升级
├── 升级原因: "高风险操作: DROP TABLE users_backup"
├── 通道: 邮件 + 企业微信 (双通道)
├── 人工操作: 回复 "REJECT - 只清理 30 天前的数据"
└── Agent 调整: 改用 DELETE WHERE created_at < 30天前
```

### 场景 3：连续 API 失败

```
Agent 调用外部 API → 失败 1 → 重试 → 失败 2 → 换策略 → 失败 3 → 触发升级
├── 升级原因: "连续 3 次失败: ConnectionTimeout"
├── 上下文: 包含完整错误日志和已尝试的策略
├── 人工操作: 确认是上游服务故障 → 点击"拒绝"
└── Agent 中止: 记录到 STATE.md，等待下次 session
```

## 实现检查清单

- [ ] 为所有 tool 定义 `risk_level` 标签
- [ ] 实现置信度评估函数
- [ ] 配置失败计数器和阈值
- [ ] 部署至少一个升级通道（推荐 webhook 起步）
- [ ] 实现 `/escalation/{task_id}/respond` 回调接口
- [ ] 在 STATE.md 中增加 escalation 状态追踪
- [ ] 设置超时策略和兜底行为
- [ ] 测试完整流程：触发 → 升级 → 响应 → 恢复/中止
