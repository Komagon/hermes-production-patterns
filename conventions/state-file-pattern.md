---
name: state-file-pattern
description: "STATE.md 跨运行状态管理 — Read Before Run, Write After Every Step"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, state, idempotency]
    category: conventions
    related_skills: [error-compact-pattern, maker-checker]
---

# STATE.md — 跨运行状态管理

> **对应 12-Factor Agents Factor 5: Unify execution state and business state**  
> **对应 Loop Engineering Step 10: STATE.md**

## 核心原则

Agent 会话是无状态的。每次运行都需要知道：
- 上次跑到哪了？
- 哪些事已经做过了？
- 有什么踩坑经验？

STATE.md 就是干这个的。

## 文件约定

```
reports/{job-name}/STATE.md
```

## 模板

```markdown
# STATE: {job-name}

## Current Run
- Last run: 2026-06-29T10:00:00+08:00
- Status: idle | running | paused | failed
- Current batch: {batch_id or iteration}

## Progress
| Metric | Value |
|--------|-------|
| Total items processed | 0 |
| Successes | 0 |
| Failures | 0 |
| Skipped (duplicates) | 0 |

## Lessons Learned
- {date}: {lesson learned from this run}

## Idempotency Keys
- {date}: {checkpoint_key} (✅ done)
```

## 四条规则

1. **Read before run** — 每次运行先读取 STATE.md，知道从哪继续
2. **Write during run** — 每步执行后更新进度计数
3. **Write on completion** — 完成后更新 status 为 idle，记录最终统计
4. **Write on failure** — 失败时设置 status 为 failed，记录错误原因

## Idempotency 检查

在每次执行有副作用的操作前，先检查 Idempotency Keys：

```python
def should_skip(checkpoint_key: str, state: dict) -> bool:
    return checkpoint_key in state.get("idempotency_keys", [])
```

## Lessons Learned 的使用

Lessons Learned 是跨运行积累的「踩坑知识库」。每次运行中新遇到的问题和解决方案都追加到该节。这样即使隔了一周再跑，Agent 也不会掉进同一个坑。
