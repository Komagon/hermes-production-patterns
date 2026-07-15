---
name: maker-checker
description: "Maker/Checker 双角色分离 — 生成与验证不在同一个 Agent"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, maker-checker, quality]
    category: conventions
    related_skills: [state-file-pattern, control-flow-separation, error-compact-pattern]
---

# Maker/Checker 双角色分离

> **对应 12-Factor Agents Factor 7: Contact humans with tool calls**  
> **对应 Loop Engineering Skill 9: Sub-Agents**

## 核心原则

**写代码的 Agent 和验证的 Agent 不是同一个。**

这是 Agent 工程化中最关键也最容易被忽略的模式。一个 Agent 如果不经外部验证就接受自己的输出，等于学生自己批改自己的试卷。

## 工作流

```
┌─────────────┐     ┌──────────────┐
│   Maker     │────→│   Checker    │
│ (生成内容)  │     │ (验证内容)   │
└─────────────┘     └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Gate       │
                    │ PASS? FAIL?  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │ PASS       │ FAIL       │
              ▼            ▼            ▼
         ✅ 输出       🔄 反馈给      ❌ 终止
                        Maker 修改
```

## 五维验证评分

Checker 对 Maker 的输出从 5 个维度评分（各 1-10 分）：

| 维度 | 含义 |
|:---|:---|
| 🎣 钩子强度 | 开头能不能让人点进来？ |
| 📊 数据支撑 | 数字、对比表、具体案例到位吗？ |
| 🧹 AI味检测 | 有没有 AI 套话？ |
| 📱 手机适配 | 段落长度、排版舒适吗？ |
| 🎯 互动钩子 | 结尾有没有让人想评论？ |

总分 ≥ 40/50 为 PASS，否则反馈修改建议。

## 实现要点

1. **隔离性** — Maker 和 Checker 各自独立运行，不通气
2. **客观标准** — Checker 的评分维度必须事先定义，不能临时拍
3. **可量化** — 每个维度必须能打分数级判断
4. **可迭代** — FAIL 后 Maker 根据具体建议修改，最多 3 轮
5. **硬上限** — 3 轮仍 FAIL 则上报人类，不无限循环

## 陷阱

- ❌ Maker 和 Checker 用同一个模型（自我验证无效）
- ❌ 评分标准太模糊（"感觉还行"不算通过）
- ❌ 无限循环修改（必须设硬上限）
