---
name: pattern-composition
description: "模式组合指南 — 何时使用哪个 Convention，以及如何组合"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, guide, composition, decision-tree]
    category: conventions
    related_skills: [maker-checker, state-file-pattern, control-flow-separation, error-compact-pattern, skill-evolution]
---

# 模式组合指南

## 场景→模式映射决策树

```
你的 Cron 任务是什么类型？
    │
    ├─ 只读监控（检查磁盘、API 健康、证书过期）
    │   ├─ 只需要 state-file-pattern（防重复 + 进度追踪）
    │   └─ 错误多？→ + error-compact-pattern
    │
    ├─ 内容生成（写摘要、日报、周报）
    │   ├─ state-file-pattern（基础）
    │   ├─ + maker-checker（质量控制）
    │   └─ + error-compact-pattern（异常处理）
    │
    ├─ 数据流水线（抓取→清洗→转换→入库）
    │   ├─ control-flow-separation（决定哪些步用代码）
    │   ├─ state-file-pattern（进度追踪 + 断点续跑）
    │   ├─ + error-compact-pattern（各步骤错处理）
    │   └─ + skill-evolution（长周期优化）
    │
    └─ 复杂多 Agent 协作
        ├─ maker-checker（角色分离）
        ├─ control-flow-separation（协调者用代码控制流）
        ├─ state-file-pattern（全局状态）
        ├─ + error-compact-pattern（错误隔离）
        └─ + skill-evolution（持续优化）
```

## 快速速查表

| 场景 | 必须 | 强烈推荐 | 可选 |
|:---|:---|:---|:---|
| 🟢 健康检查监控 | state-file | error-compact | — |
| 📊 数据采集 | state-file | error-compact, control-flow | — |
| 📝 自动摘要/日报 | state-file, maker-checker | error-compact | skill-evolution |
| 🧪 CI 自动修复 | control-flow, state-file | maker-checker, error-compact | skill-evolution |
| 🤖 多 Agent 流水线 | maker-checker, state-file | control-flow, error-compact | skill-evolution |
| 🔧 系统运维自动化 | control-flow, error-compact | state-file | — |

## 模式间的关系图

```
                    ┌───────────────────┐
                    │  control-flow-sep  │← 决定每一步用 Code 还是 LLM
                    └────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  maker-check │  │ state-file  │  │error-compact│
    │  (LLM 输出)  │  │ (全局状态)   │  │ (异常处理)   │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           └────────────────┼────────────────┘
                            ▼
                   ┌────────────────┐
                   │ skill-evolution│← 长期迭代优化
                   │ (收敛后停止)   │
                   └────────────────┘
```

## 按成熟度分级（L1→L3）的推荐组合

| 级别 | 必须装的 convention | 行为 |
|:---:|:---|:---|
| L1 🟢 | state-file-pattern | 只读、仅报告、人类决策 |
| L2 🟡 | + maker-checker + error-compact | 草稿 + 人工批准、有错误处理 |
| L3 🔴 | + control-flow-separation + skill-evolution | 自动执行、自愈、持续优化 |

## 反组合（不要这样用）

| ❌ 错误组合 | 为什么不行 |
|:---|:---|
| maker-checker 但无 state-file | Checker FAIL 后无法记录状态，下次不知道哪些重试过 |
| skill-evolution 但无 maker-checker | 没有评分数据，无法判断技能变好还是变差 |
| control-flow-separation 但无 error-compact | 代码路径出错后堆栈炸上下文 |
| state-file 但无 error-compact | 错误发生后写入 STATE.md 失败，状态不完整 |
