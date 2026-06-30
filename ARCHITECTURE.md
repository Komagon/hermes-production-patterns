# Architecture

> 整体运行时架构：组件角色、数据流、部署要点、可观测性指标。

---

## 一、组件图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Scheduler (Cron)                         │
│  读取 STATE.md → 判断是否该运行 → 触发 Maker → 等待 → 循环     │
└──────────┬──────────────────────────────────────────────────────┘
           │ trigger
           ▼
┌──────────────────────┐     ┌──────────────────────┐
│      Maker           │     │      Checker          │
│ (生成内容/执行任务)  │────▶│ (验证输出质量)        │
│                      │     │                      │
│ 工具: terminal,      │     │ 评分: 五维验证        │
│       web_extract,   │     │ 标准: ≥ 40/50 PASS   │
│       read/write     │     │ 上限: 3 轮重试       │
└──────────────────────┘     └──────────┬───────────┘
                                        │ PASS / FAIL
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                         State Store                             │
│  STATE.md — 每次读写原子写入 + 文件锁                           │
│  字段: progress / lessons_learned / idempotency_keys            │
│  Schema: JSON / YAML                                            │
└─────────────────────────────────────────────────────────────────┘
                                        │ output
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Notifier                                │
│  成功 → 报告 | 失败 → 告警 | 重试 → 进度更新                   │
│  渠道: 飞书 / Telegram / 邮件 / GitHub Issue                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、角色定义

| 角色 | 职责 | 运行时 | 模型要求 |
|:---|:---|:---|:---|
| **Scheduler** | 定时触发、读取 STATE.md、决定是否需要运行 | 独立进程（Cron / 消息队列） | ❌ 不需 LLM |
| **Maker** | 执行具体任务：抓取、分析、生成 | Agent 会话 | ✅ LLM（推荐强推理模型） |
| **Checker** | 验证 Maker 输出质量，返回评分 | 独立 Agent 会话（与 Maker 隔离） | ✅ LLM（可与 Maker 不同） |
| **State Store** | 持久化运行状态、进度、idempotency keys | 文件系统 / 数据库 | ❌ 不需 LLM |
| **Notifier** | 输出结果分发：报告/告警/存档 | Webhook / API 调用 | ❌ 不需 LLM |

---

## 三、数据流

### 正常流程

```
1. Scheduler 读取 STATE.md
2. 检查 idempotency keys → 跳过已处理项
3. 触发 Maker 执行
4. Maker 产出 → 写入临时文件
5. 触发 Checker 验证
6. Checker PASS → 写入最终输出 + 更新 STATE.md
7. Checker FAIL → Maker 根据反馈重试（最多 3 轮）
8. 3 轮仍 FAIL → Notifier 告警给人类
```

### 错误流程

```
超时 → 记录 STATE.md → 下次运行自动重试
认证失败 → 记录 STATE.md → Notifier 告警（不重试）
数据异常 → 跳过该项 → 在 STATE.md 标记
致命错误 → 记录 → 降级 L1 → Notifier 紧急告警
```

---

## 四、网络与权限要点

| 维度 | 建议 |
|:---|:---|
| **网络隔离** | Maker/Checker 可使用不同网络出口（避免 IP 关联封禁） |
| **API 密钥** | 只通过环境变量注入，不写入 STATE.md 或 SKILL.md |
| **文件权限** | STATE.md 目录只对运行 agent 的 OS 用户可读写 |
| **日志** | 不记录 API Key、Token、个人信息到 stdout |
| **MCP 最小权限** | 每个 MCP 连接只授予其功能所需的最小 scope |

---

## 五、模型隔离建议

| 场景 | Maker | Checker | 原因 |
|:---|:---|:---|:---|
| 默认 | Claude Opus 4.8 | DeepSeek V4 Flash | Maker 要强推理，Checker 够用就行 |
| 成本优先 | DeepSeek V4 Flash | 同一模型 | 同一模型但分两次独立调用 |
| 高精度 | GPT-5.5 | Claude Opus 4.8 | Checker 比 Maker 更强，防漏网 |
| 开源部署 | Qwen3 / GLM-5 | 不同实例 | 池隔离，不互相影响 |

**规则：** Maker 和 Checker 必须使用**不同的 Agent 会话**运行，不能在同一上下文中自我验证。

---

## 六、可观测性指标

### 推荐 metrics（按 State store 或日志系统记录）

| Metric | Type | 含义 | 告警阈值 |
|:---|:---|:---|:---|
| `run_count` | Counter | 总运行次数 | — |
| `run_success` | Counter | 成功完成次数 | — |
| `run_fail` | Counter | 失败次数 | > 3 次/天 |
| `retry_count` | Counter | 重试次数（Maker→Checker 循环） | > 3/轮 |
| `checker_pass_rate` | Gauge | Checker 通过率 | < 50% |
| `maker_latency` | Histogram | Maker 执行耗时 | > 5 min |
| `state_write_corrupt` | Counter | STATE.md 损坏次数 | > 0 |
| `human_escalation` | Counter | 升级到人类干预的次数 | > 1 次/周 |

### 日志格式建议

```json
{
  "timestamp": "2026-06-29T10:00:00Z",
  "job": "daily-news-digest",
  "maker": "claude-opus-4.8",
  "checker": "deepseek-v4-flash",
  "duration_ms": 45200,
  "state": "success",
  "items_processed": 8,
  "items_skipped": 3,
  "failures": 1,
  "retries": 0
}
```

---

## 七、部署矩阵

| 部署方式 | Scheduler | Maker/Checker | State Store | 推荐场景 |
|:---|:---|:---|:---|:---|
| **单机 Hermes** | 内置 Cron | 同一进程 | 文件系统 | 个人/小团队 |
| **云端 Hermes** | Cron + Webhook | Gateway 托管 | 远程文件 / DB | 多 Agent 协作 |
| **容器化** | 独立容器 | 独立容器（可扩缩） | 挂载卷 + 锁 | 生产环境 |
| **K8s** | CronJob | Deployment | PVC + ConfigMap | 企业级部署 |
