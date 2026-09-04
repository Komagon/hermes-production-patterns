---
name: maker-checker
description: "Maker/Checker 双角色分离 — 生成与验证不在同一个 Agent"
version: 1.2.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, maker-checker, quality]
    category: conventions
    related_skills: [state-file-pattern, control-flow-separation, error-compact-pattern]
hpp_category: quality
hpp_en: "Separate generation from validation."
hpp_maturity: L2
hpp_complexity: medium
hpp_reliability: high
hpp_capability: delegate
maturity: battle-tested
hpp_when_to_use: ["Long-running Agent", "High-value task", "Autonomous workflow", "Output needs validation"]
hpp_when_not_to_use: ["Simple one-shot task", "Low-value operation", "Validation cost exceeds task value"]
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

## Checker 模式选择

Checker 有两种实现模式，按成熟度选择：

| 模式 | 方式 | 适用场景 | 成熟度 |
|:---|:---|:---|:---:|
| **手动 Checker** | 独立 Agent（不同模型）五维评分 | 高价值内容、首次上线 | L1→L2 |
| **自动化 Checker** | Opik LLM-as-a-Judge 评分 | 批量任务、日常运行 | L2→L3 |
| **委托 Checker** | `delegate_task` 独立子代理 + `output_schema` 验证 | 需要真隔离/可审计的日常任务 | L2→L3 |

### 自动化 Checker（Opik Judge）

使用 Opik 的 LLM-as-a-Judge 替代人工 Agent 做初步验证：

```python
from judge import evaluate_answer

result = evaluate_answer(
    question="评估这篇文章质量",
    answer=article_text,
    criteria=["hook_strength", "data_support", "ai_tone", "mobile_friendly", "engagement"]
)
# result.score: 0-1 归一化分数
# result.passed: True/False (threshold ≥ 0.7)
```

**优势：** 速度快、可重复、一致性高  
**局限：** 对需要深度推理的验证项（如事实核查）不如人工 Checker 可靠  
**推荐：** 自动化 Checker 做初筛 + 人工 Checker 抽检终审

### 委托 Checker（delegate_task，2026-08）

用 Hermes 原生 `delegate_task` 把 Checker 跑成**独立子代理**，与 Maker 完全隔离（独立上下文、独立终端会话）：

```
delegate_task(
  goal="以 Checker 身份验证以下文章质量…",
  context="五维评分标准 + Maker 输出全文",
  output_schema={...评分 JSON Schema...}
)
```

**关键能力：**
- `output_schema` — 子代理最终答案必须符合 JSON Schema，否则打回重试一次 → 评分契约硬校验
- 并行 batch — 最多 3 个 Checker 子代理并行（如三视角评审），各自独立上下文
- `live transcripts` — 子代理操作全量落盘，事后可审计（谁评的、查了什么、怎么打的分）

**选择建议：** Opik Judge 适合"快而稳"的批量初筛；delegate_task 适合"要真隔离 + 要审计轨迹 + 要 schema 强校验"的场景；两者可串联（Opik 初筛 → delegate 抽检）。

## 五维验证评分

Checker 对 Maker 的输出从 5 个维度评分（各 1-10 分，或 Opik 归一化 0-1）：

| 维度 | 含义 | 手动分 | Opik 指标 |
|:---|:---|:---:|:---:|
| 🎣 钩子强度 | 开头能不能让人点进来？ | 1-10 | AnswerRelevance |
| 📊 数据支撑 | 数字、对比表、具体案例到位吗？ | 1-10 | ContextRelevance |
| 🧹 AI味检测 | 有没有 AI 套话？ | 1-10 | Hallucination (逆) |
| 📱 手机适配 | 段落长度、排版舒适吗？ | 1-10 | Custom |
| 🎯 互动钩子 | 结尾有没有让人想评论？ | 1-10 | Custom |

总分 ≥ 40/50（手动）或 ≥ 0.7（Opik 归一化）为 PASS，否则反馈修改建议。

## 实现要点

1. **隔离性** — Maker 和 Checker 各自独立运行，不通气
2. **客观标准** — Checker 的评分维度必须事先定义，不能临时拍
3. **可量化** — 每个维度必须能打分数级判断
4. **可迭代** — FAIL 后 Maker 根据具体建议修改，最多 3 轮
5. **硬上限** — 3 轮仍 FAIL 则上报人类，不无限循环
6. **红线优先（判决制，2026-08-30 借鉴 JIT-Agent 评审 charter）** — 评分制（"6/10 感觉还行"）之外，允许在评分维度旁预定义若干「命中即 FAIL」的具体 red flags（如：终答路径不可达、循环只能靠步数上限兜底、模板渲染必崩写法）。Checker 报告须写明检查了哪几条红线、是否命中——红线是硬闸，分数是软评，任一命中直接 FAIL 不进修改轮次。红线只从真实失败案例蒸馏，禁止凭想象堆砌（防评分器变许愿池）。

## 陷阱

- ❌ Maker 和 Checker 用同一个模型（自我验证无效）
- ❌ 评分标准太模糊（"感觉还行"不算通过）
- ❌ 无限循环修改（必须设硬上限）

## 真实案例：公众号文章 Maker/Checker 流水线

> 以下数据来自 Hermes Agent 自动化公众号写作流水线，已脱敏。

### 接入前（单 Agent 写+自检）

```
问题：Agent 自己写文章、自己检查质量，"AI味"重的文章经常被放过。
典型失败：一篇文章用了 12 次"首先/其次/最后"、3 次"值得注意的是"，
Agent 自检评分 42/50 通过，实际发布后阅读完成率低于均值 30%。
根因：自我验证存在盲区，Agent 倾向于给自己的输出高分。
```

### 接入后（Maker 写 + 独立 Checker 验证）

```markdown
## 一次 FAIL → 修改 → PASS 的真实记录

Round 1:
  Maker 输出: 3200 字文章
  Checker 评分: 33/50 (FAIL)
  Red flags 命中: "AI味检测"维度 3/10（"值得注意的是"×2, "总而言之"×1）
  反馈: "删除开头三段背景铺垫，直接从数据切入"

Round 2:
  Maker 修改后: 2800 字
  Checker 评分: 43/50 (PASS)
  Red flags: 0 命中
```

### 量化结果

| 指标 | 单 Agent 自检 | Maker/Checker |
|:---|:---:|:---:|
| AI味检出率 | ~30%（漏检多） | ~90%（独立视角） |
| 首次通过率 | 85%（标准松） | 55%（标准严） |
| 发布后平均阅读完成率 | 基准 | +18% |
| 人工返工次数 | 2-3 次/周 | 0-1 次/周 |

**关键改进**：独立 Checker 的"五维评分 + 红线判决"机制，把 AI味文章从发布前拦住。3 轮硬上限防止了无限修改循环（实际运行中 85% 的文章在 2 轮内通过）。
