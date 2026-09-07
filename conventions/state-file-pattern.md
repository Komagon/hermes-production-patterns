---
name: state-file-pattern
description: "STATE.md 跨运行状态管理 — Read Before Run, Write After Every Step"
version: 1.1.1
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, state, idempotency]
    category: conventions
    related_skills: [error-compact-pattern, maker-checker, checkpoint-pattern]
migration: "v1.1.0 → v1.1.1:新增「变更收据(Change Receipt)」章节(借鉴 LunarResearcher harness engineering;run 结束时收敛 state+evidence+unresolved risk 三件套,给人类审 + 给下次 session 起跑)"
hpp_category: state
hpp_en: "Cross-run memory: read before run, write after every step."
hpp_maturity: L2
hpp_complexity: low
hpp_reliability: high
hpp_capability: files
maturity: battle-tested
hpp_when_to_use: ["Any task that survives sessions", "Cron jobs with incremental progress", "Multi-step pipelines"]
hpp_when_not_to_use: ["Truly one-shot stateless queries"]
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

## 关联文件

| 文件 | 用途 |
|:---|:---|
| `scripts/validate_state.py` | 程序化校验 STATE.md 格式和必填字段 |
| `scripts/atomic_state_write.py` | 原子化写入 STATE.md，防并发冲突 |
| `conventions/state-schema.json` | STATE.md 的 JSON Schema |
| `templates/STATE.md.template` | 可直接复制的 STATE.md 模板 |

## 文件约定

```
reports/{job-name}/STATE.md
```

## 模板

参见 `templates/STATE.md.template`，或直接复制以下内嵌模板：

## 四条规则

1. **Read before run** — 每次运行先读取 STATE.md，知道从哪继续
2. **Write during run** — 每步执行后更新进度计数
3. **Write on completion** — 完成后更新 status 为 idle，记录最终统计
4. **Write on failure** — 失败时设置 status 为 failed，记录错误原因

## 变更收据（Change Receipt，2026-09-07，借鉴 LunarResearcher）

> run 结束时不要只留「agent 说了什么」，要留「系统能证明什么」。

规则 1-4 管「什么时候写」；变更收据管「结束时收敛成什么形状」。

一个 run 的可靠收尾不是对话总结，而是一张紧凑的变更收据 + 三件套：**state + evidence + unresolved risk**。这是给人类审的紧凑面，也是给下一次 session 的可靠起点。

**给人类**的收据（一次 run 结束时在 STATE.md 末尾写，控制在一屏内）：

```
## 变更收据
- 状态(Status): done / failed / partial
- 证明(Evidence): <这次系统能证明的结构化产出:文件路径/URL/ID/校验和;不是计划、是已落地物>
- 未决风险(Unresolved): <已知没解决/不可靠的地方,显式列出,不许留「应该都行」>
- 关键决策(Decisions): <改变方向的选择,不是中间推理>
- 成本/范围: <耗时、token量、触及的外部副作用>
```

铁律:收据里每一条都要是**可证明的**——evidence 必须是已存在的产物句柄(路径/URL/校验),unresolved 每一条都能答「哪里还没验证」。

**给下次 session** 的起点:下一次 Read before run 时,先读这份收据的 Evidence + Unresolved,而不是重读整段对话历史。这正好接上 SKILL.state 的「显式状态优于对话历史」——收据就是 run 级的那一层显式状态。

与四条规则的关系:规则 3(Write on completion)更新 status 与统计,是收据的骨架;收据把这些散落的项收敛成三件套的紧凑交接面,给人类审 + 给下次起跑。

## Idempotency 检查

在每次执行有副作用的操作前，先检查 Idempotency Keys：

```python
def should_skip(checkpoint_key: str, state: dict) -> bool:
    return checkpoint_key in state.get("idempotency_keys", [])
```

## Lessons Learned 的使用

Lessons Learned 是跨运行积累的「踩坑知识库」。每次运行中新遇到的问题和解决方案都追加到该节。这样即使隔了一周再跑，Agent 也不会掉进同一个坑。

## 恢复手段：session_search 与 memory（2026-08）

STATE.md 是跨运行状态的**主存储**；Hermes 的两个原生能力作为补充：

| 能力 | 用途 | 何时用 |
|:----|:-----|:------|
| `session_search`（FTS5） | 跨会话检索历史对话（discovery / scroll / read 三种形态） | STATE.md 没写全时，找回"上次到底怎么处理的"；会话级复盘 |
| `memory`（batch operations） | 原子批量增删改记忆（replace/remove 一次完成，超限时合并腾挪） | 记忆更新要原子性：删旧加新一次提交，避免中间态 |
