---
name: checkpoint-pattern
description: "检查点模式 — 长任务中途挂了从哪恢复"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, checkpoint, recovery, resilience]
    category: conventions
    related_skills: [state-file-pattern, cron-job-pattern, error-compact-pattern]
---

# 检查点模式

> **对应 12-Factor Agents Factor 12: Stateless reducer**
> **对应 Loop Engineering Step 10: STATE.md**

## 核心原则

**长任务一定会挂。关键是挂了之后能捡起来，而不是重头来。**

## 什么时候需要检查点

| 任务特征 | 需要检查点？|
|:--------|:----------:|
| 执行时间 < 1 分钟 | ❌ 挂了重跑就行 |
| 执行时间 1-10 分钟 | ⚠️ 建议有 |
| 执行时间 > 10 分钟 | ✅ 必须有 |
| 有外部副作用（发消息/写文件）| ✅ 必须有 |
| 分批处理大量数据 | ✅ 必须有 |

## 检查点设计

### 每步检查点

```text
步骤 1 → [保存检查点] → 步骤 2 → [保存检查点] → 步骤 3 ...
```

每次关键操作完成后保存 STATE.md：

```markdown
## Checkpoints
| Step | Key | Status | Time |
|:----|:----|:------:|:-----|
| 1 | fetch_raw_data | ✅ done | 10:00:00 |
| 2 | parse_data | ✅ done | 10:01:30 |
| 3 | analyze | ⏳ running | 10:03:00 |
```

### 恢复流程

```
1. 读取 STATE.md
2. 找到最后一个 ✅ done 的检查点
3. 从下一步开始恢复执行
4. 跳过已完成的步骤
```

## 幂等性保障

每个有副作用的操作（发消息、写文件、调用 API）都必须有 Idempotency Key：

```python
def execute_with_idempotency(step_name: str, params: dict, state: dict) -> dict:
    key = f"{step_name}/{hash(params)}"
    if key in state.get("idempotency_keys", []):
        return {"skipped": True, "reason": "already executed"}
    
    result = actual_execution(params)
    
    state["idempotency_keys"].append(key)
    save_state(state)
    return result
```

## 超时处理

| 模式 | 做法 | 适用场景 |
|:----|:-----|:--------|
| 硬超时 | 超过 N 分钟强制终止 | API 调用、网络请求 |
| 软超时 | 超时后标记状态，下次恢复 | 数据分析、批处理 |
| 进度超时 | 长时间进度没更新→终止 | LLM 推理卡死 |

## 模板

```markdown
## 检查点配置
- 粒度: {每步/每 N 条/每 N 分钟}
- 存储: {STATE.md / 外部文件}
- 恢复策略: {自动恢复 / 需人工确认}
- 最大重试: {次数}
```