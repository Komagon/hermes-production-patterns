---
name: cron-job-pattern
description: "Cron 任务设计模式 — 幂等、防重复、防静默失败（含 Hermes 原生 Monitor 模式）"
version: 1.1.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, cron, idempotency, monitor]
    category: conventions
    related_skills: [state-file-pattern, maturity-staging, error-compact-pattern, control-flow-separation]
hpp_category: automation
hpp_en: "Idempotent, dedup-safe, silent-failure-proof scheduling."
hpp_maturity: L2
hpp_complexity: medium
hpp_reliability: high
hpp_capability: cron
hpp_when_to_use: ["Recurring autonomous jobs", "Jobs that must never double-fire", "Jobs needing delivery guarantees"]
hpp_when_not_to_use: ["One-off tasks", "Jobs needing interactive input"]
---

# Cron 任务设计模式

> **对应 12-Factor Agents Factor 6: Lifecycle APIs**
> **对应 Loop Engineering Step 5: Automations**

## 核心原则

Cron 任务的核心风险不是「跑崩了」，而是**「跑偏了但没人发现」**。

## 三段式结构

每个 Cron 任务遵循三段式：

```text
Pre-flight（起飞前检查） → Execute（执行） → Post-flight（落地报告）
```

### Pre-flight

```
1. 读取 STATE.md，检查上次运行状态
2. 检查 Idempotency Keys，跳过已处理的批次
3. 检查资源可用性（磁盘/网络/API Key）
4. 如果任何检查失败 → 记录到 STATE.md → 跳过本次运行
```

### Execute

```
1. 锁定状态（STATE.md status → running）
2. 按步骤执行，每步更新进度
3. 使用确定性代码处理已知路径，LLM 只在决策点介入
4. 失败时按 error-compact-pattern 压缩后写入上下文
```

### Post-flight

```
1. 更新 STATE.md（status → idle，记录统计）
2. 生成运行报告（成功/失败/跳过）
3. 如果失败率超过阈值 → 通知人类
4. 如果连续失败 N 次 → 自动暂停 Cron
```

## 幂等性保障

| 场景 | 问题 | 解法 |
|:----|:-----|:-----|
| 任务重复触发 | 同一批数据跑了两遍 | Idempotency Keys |
| 部分成功 | 跑了 50%，下次从哪开始？ | STATE.md 进度记录 |
| 静默失败 | 报错了但没人看见 | 失败率阈值+告警 |
| 跑偏 | 输出了错误结果但没报错 | Maker/Checker 验证 |

### Idempotency Key 实现

```python
def generate_key(task_id: str, batch: str, date: str) -> str:
    return f"{task_id}/{batch}/{date}"

def should_skip(key: str, state: dict) -> bool:
    return key in state.get("idempotency_keys", [])
```

## 防静默失败

核心思路：**大声失败比沉默通过好一万倍。**

| 防护层 | 机制 | 触发条件 |
|:------|:-----|:--------|
| L1 | 日志记录 | 任何错误 |
| L2 | 失败率告警 | 单次运行失败率 > 20% |
| L3 | 自动暂停 | 连续 3 次运行失败 |
| L4 | 人类通知 | L3 触发后推送到 IM |

## Hermes 原生 Monitor 模式（2026-08）

> 上面的三段式是"agent 自查"；Hermes 现在提供**原生监控模式**，从运行时层面解决"跑偏没人发现"——不需要 agent 每 tick 自查，大部分 tick 根本不烧 token。

### monitor_script / monitor_url（变化检测）

```
每个 tick:
  1. 先运行 monitor 脚本（或抓取 URL），对输出做哈希
  2. 哈希与上次相同 → 跳过 agent 运行（0 token，静默 tick）
  3. 哈希变化 → 把 unified diff + 新输出注入 agent prompt，跑一轮 agent
  4. 首个 tick 总是跑 agent（建立基线）
```

- **适用**：监控网页变化、文件变化、价格/行情变化、外部 API 状态、CI 状态
- **与三段式的关系**：monitor 是 Pre-flight 的自动化升级（变化检测交给运行时），agent 只在变化时执行 Execute
- **脚本要求**：输出必须稳定（无时间戳/随机顺序），否则每 tick 都"看起来变了"

### no_agent=True（Watchdog 模式）

脚本即任务：stdout 非空 → 原样投递；stdout 空 → 静默（什么都不发）。适合纯告警/看门狗（磁盘水位、进程存活、API 配额、日志关键词），**零 token**。

### 链式与上下文（context_from / script / workdir）

| 能力 | 用法 | 场景 |
|:----|:-----|:-----|
| `context_from=[jobB]` | job A 最新输出注入 job B 的 prompt | 数据流水线（A 采集 → B 处理） |
| `script`（agent 模式） | 脚本 stdout 注入 prompt 当上下文 | 数据收集 |
| `enabled_toolsets` | 限制 job 工具集 | 降 token：只读监控 job 只给 web 工具 |
| `attach_to_session` | 用户可回复该 job 投递并续上下文 | 交互式任务 |
| `workdir` | 指定目录运行 + 注入 AGENTS.md/CLAUDE.md | 项目内 job |

### 选择矩阵

| 场景 | 推荐 |
|:-----|:-----|
| 网页/文件/行情变化检测 | `monitor_script` / `monitor_url` |
| 纯脚本告警/看门狗 | `no_agent=True` |
| 数据流水线（A→B） | `context_from` 链式 |
| 定期内容生成 | 三段式 + `enabled_toolsets` |
| 交互式/可追问任务 | `attach_to_session` |
| 项目内定时维护 | `workdir` + 三段式 |

## 与成熟度分级配合

| 级别 | Cron 行为 |
|:---:|:---------|
| L1 | 只跑报告，不写外部。失败只记日志不告警 |
| L2 | 跑报告+草稿，失败推送摘要到 IM |
| L3 | 全自动执行，失败自动暂停+通知 |

## 模板

```markdown
# Cron Job: {job-name}

## 调度
- 频率: {cron 表达式}
- 超时: {最大运行时间}
- 重试: {次数和策略}

## 步骤
1. {步骤 1: 描述}
2. {步骤 2: 描述}

## 失败处理
- 可重试: {错误类型}
- 不可重试: {错误类型}
- 人类通知: {通知方式}

## 状态文件
- 路径: reports/{job-name}/STATE.md
```
