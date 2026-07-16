---
name: cron-job-pattern
description: "Cron 任务设计模式 — 幂等、防重复、防静默失败"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, cron, idempotency]
    category: conventions
    related_skills: [state-file-pattern, maturity-staging, error-compact-pattern]
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