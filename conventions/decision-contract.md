---
name: decision-contract
description: "决策契约 — 判断与执行分离：类型/候选/阈值/降级/收据/复现/离线评测"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, decision, routing, gate, eval, replay]
    category: conventions
    related_skills: [control-flow-separation, human-escalation, observability-trace, data-driven-optimization, evolution-gate, anti-patterns]
hpp_category: governance
hpp_en: "Separate the judgment from the permission from the action."
hpp_maturity: L2
hpp_complexity: medium
hpp_reliability: high
hpp_capability: terminal
maturity: beta
hpp_when_to_use: ["Routing and gating judgments", "Thresholds that need a fallback", "Auditable and reproducible decisions"]
hpp_when_not_to_use: ["Pure generation, writing or reasoning (that is the LLM's job, not a Decision)"]
---

# 决策契约（Decision Contract）

> **Decision ≠ Action。** 判断、授权、执行是三件事：Decision 出「选择 + 置信度」，Policy（代码）出「授权」，Action 才执行。
> **Confidence is evidence, not authorization.** 置信度只是证据，永远不能当授权用。

## Problem

Agent 的判断通常埋在这些地方，三种坏味道：

1. **判断写死在提示词里** —— 路由、阈值、要不要重试、算不算完成，都靠一句 prompt 描述。模型每次都重新发明一遍判断标准，行为和昨天不一致。
2. **无阈值直接执行** —— 判断出结果就直接动手，没有「置信度不足就降级/交人」这一步，静默跑偏是唯一结局。
3. **不可审计、不可复现** —— 事后无法回答「当时为什么这么判」，同一输入再跑一次得到不同结果，回归测试无从谈起。

## Solution

给每个重要判断一份契约，六个字段一个都不能少：

| 字段 | 作用 | 缺失的后果 |
|:---|:---|:---|
| `type` | choice / score / noul | 无法校验输出合法性 |
| `candidates` | 合法取值域（choice 必填） | 模型可能返回不存在的选项 |
| `policy` | 三段门阈值 + 动作 | 没有授权层，判断直接变执行 |
| `fallback` | 链上降级目标 | 后端一挂就整条断掉 |
| `receipt` | 每次决策留痕（含降级轨迹） | 不可审计 |
| `version` | 契约版本 | 改完无法复现历史决策 |

### 判断与执行的分离

```
LLM  = Think / Create / Reason
Jev  = Choose / Score / Judge      ← 只是决策的一个可选后端
Code = Enforce / Execute / Authorize
```

## 决策的三种类型

| type | 形态 | 例子 | 校验规则 |
|:---|:---|:---|:---|
| `choice` | 从候选集里选一个 | 意图→技能、工具→治理 | 值必须 ∈ 候选集 |
| `score` | 打分/分级 | 相关度、任务复杂度 | 数值 + **声明刻度** |
| `noul` | 是/否门 | 任务是否完成、要不要重试、要不要升人类 | 布尔 |

## 后端链：从最确定、最便宜的开始

```
rule → cache → local → jev → llm → human
```

1. **能规则就规则。** 确定性检查（DoD 是否全满足、schema 是否合法）优先于任何模型。模型只补充判断，不自称完成。
2. **硬边界由代码先裁剪候选集**，再让后端在合法候选里选。权限、白名单、隐私、金额、文件系统边界永远不到模型手里。
3. **失败与越界一律 fail-open 到下一个后端**，绝不把越界值当决策（返回值不在候选集、noul 不是布尔、score 不是数值 → 一律判无效继续降级）。
4. **末位是 human**：不确定就不猜，交人。

## 三段门与按 type 分阈值

| 段 | 默认线 | 动作 | 含义 |
|:---|:---|:---|:---|
| high | ≥ 0.90 | `auto` | 直接执行 |
| medium | ≥ 0.75 | `verify` | 执行 + 观察 |
| low | < 0.75 | `escalate` | 交人 |

**别用一条 0.9 通吃所有 type。** 实测：score 型（0-3 分）与 choice/noul 的置信度语义不同，共用一条线会把整片 score 决策打成 escalate。阈值要按 type 声明（`confidence_by_type` / `min_confidence_by_type`）。

**但阈值不能治质量问题。** 调阈值前先做分离度检验：真值上的置信度中位 vs 错值上的中位。

- 分得开（如 0.95 vs 0.62）→ 阈值有效，往上顶。
- 分不开（实测 score 型真值中位 0.92 vs 错值 0.88，甚至唯一错的那行 conf=1.0）→ **阈值无效**，问题在 rubric 或刻度，去改契约，别动阈值。

## Record & Replay：可复现不是「把温度调低」

概率后端天然抖动（实测同一输入三次：0.33 / 1.0 / 1.0，band 在 low 与 medium 间跳）。可复现靠记录与重放，不靠祈祷。

- **key** = `decision + version + policy + state + question`（比普通缓存更严：policy 或 version 变了就不复用旧决策）。
- **未接受、降级到 fallback 的结果也要记** —— 只记「成功」的话，同一输入每次都会重新走向不确定的 fallback。
- **命中即整条链短路**，输出带 `replayed: true` + 原 trace_id，latency ≈ 0。
- **改类型、改 rubric、改阈值必须 bump `version`**，否则旧记录会被当成同一条决策复用（这是一个真实踩过的坑：score → choice 改型后不 bump，结果直接串台）。
- 记录要有 TTL 和 GC，否则按 state 记录的文件会无限增长。

## 离线评测：没有 dataset 的阈值只是猜测

```
dataset 行: {"state": {...}, "expected": ..., "metadata": {...}}
```

- 默认走 replay（回归稳定、快、可比）；改 rubric 或标定阈值时用 `--fresh` 重新问后端。
- 指标要分清：`accuracy` / `accuracy_answered`（排除弃权）/ `abstained_rate` / `near_accuracy`（有序档位差一档内）/ `mae_rank`（平均档位距离）。
- **abstain（弃权、交给人类）不是答错。** 把弃权当失败计会得出反向结论：某决策实测 0.92 被算成 0.58，而它其实只是正确地拒绝了 5 次猜测。弃权要单列。
- **有序档位别用精确匹配当唯一指标。** 「差一档」和「差三档」不是一回事：实测某相关度决策精确 0.722，但差一档内 0.944、平均档位距离 0.333 —— 这才是有信息量的读数。
- 覆盖不足时先补集，不要用「跑了几个手测用例」当基线。

## 实测数据（8 个决策，2026-09-30）

| decision | type | n | accuracy | 备注 |
|:---|:---|---:|---:|:---|
| intent.route | choice | 26 | **1.00** | 本地确定性打分全中 |
| context.select | choice | 12 | **1.00** | 候选集动态取自既有资产 |
| tool.route | choice | 3 | **1.00** | |
| task.complete | noul | 13 | **1.00** | 规则 4 + 模型 9 |
| retry.should | noul | 12 | **1.00** | 修完置信度语义后 |
| human.escalate | noul | 12 | 0.917 | 唯一未命中是弃权（结果等价），排除弃权后 1.00 |
| task.complexity | score | 8 | 0.75 | 2 行差一档 |
| memory.relevance | choice | 18 | 0.722 | 差一档内 0.944，平均档位距离 0.333 |

**三个只靠 dataset 才暴露的坑**（都已修，值得当验收清单用）：

1. **候选集动态解析写错一个字段，准确率 0.31 → 1.00。** 从既有资产（路由规则表）取候选时，把字面字段名当成了候选值，真正的候选一个都没进集合。**候选集错了，后面的判断再准也没用** —— 动态候选集必须有「候选数 + 抽样目视」检查。
2. **score 的刻度由刻度档数决定，不由问题文本决定。** 契约写 0-3 但只声明了 3 档 → 后端最多只能给出 2.0，「满分」永远拿不到（实测直接命中的文档只拿 1.95）。**声明几个档，刻度就是几档**；拿到返回值后还要做一次刻度校正，原始分留在收据里备查。
3. **noul 的置信度不能用「离 0.5 的距离」。** 该后端返回的是 margin（`2|p-0.5|`），会把「p=0.8 的明确 yes」压成 0.6 → 大片决策白白降级到下游模型或人工。正确的置信度是「所选值的概率」`max(p, 1-p)`；margin 存进收据备查。改完某决策 0.917 → 1.000，另一个 0.583 → 0.917。

## Before / After

| | Before | After |
|:---|:---|:---|
| 判断在哪 | 提示词里的一句话 | 契约文件（type/candidates/policy/version） |
| 阈值 | 没有，或写死在代码里一句话 | 按 type 声明，数据标定 |
| 低置信怎么办 | 照样执行 | 三段门 → verify / escalate |
| 越界输出 | 当决策用 | 判无效，fail-open 降级 |
| 事后审计 | 翻聊天记录 | 收据（含完整降级轨迹 + state 哈希） |
| 同一输入两次 | 结果可能不同 | replay 命中，逐字一致 |
| 改完怎么验收 | 「看着对」 | 跑 dataset，看 accuracy/abstain/档位距离 |

## 与既有模式的关系

| 模式 | 关系 |
|:---|:---|
| `control-flow-separation` | 上游：哪一步用代码。决策契约是它的下一层：判断本身怎么被约束与授权 |
| `human-escalation` | 下游：三段门的 `escalate` 段就是升级通道的入口；弃权语义见该文 |
| `observability-trace` | 落地：每次决策出收据，含 backend 降级轨迹（attempts / fallback_used） |
| `data-driven-optimization` | 落地：dataset + 标定闭环，用数据决定阈值与 rubric |
| `evolution-gate` | 配合：契约是行为契约，升级走 G1-G5；回测即 dataset |
| `anti-patterns` #13 | 同类病：硬规则只靠提示词说 = 默认违规；契约是「规则写两遍」的决策层形态 |

## 实现检查清单

- [ ] 这个判断是 Decision 而不是 Generation？（纯生成/写作/推理不该套契约）
- [ ] 确定性代码能不能直接解决？（能就别上模型）
- [ ] type / candidates / policy / fallback / version 五件齐全？
- [ ] 硬边界（权限/白名单/隐私/金额）由代码裁剪候选集，未交给模型？
- [ ] 越界值与后端失败都走 fail-open，未当决策用？
- [ ] 阈值按 type 声明，且做过分离度检验（真值 vs 错值置信度）？
- [ ] dataset 覆盖 ≥ 12 行，含「规则可判」与「只有自然语言」两类？
- [ ] 弃权、有序档位距离单独计入指标，未被算成答错？
- [ ] replay key 含 version/policy，未接受的结果也记？
- [ ] 收据含降级轨迹，能回答「当时为什么这么判」？

## 红线

- ❌ 判断写死在提示词里（无契约、无阈值、无 fallback）
- ❌ 把置信度当授权用（高置信 ≠ 有权执行）
- ❌ 越界返回值当决策用（不在候选集 / 非布尔 / 非数值）
- ❌ 改了 rubric/类型/阈值不 bump version（历史决策串台）
- ❌ 只看精确匹配就宣布质量（有序档位要用档位距离）
- ❌ 把弃权算成答错（会把正确的「拒绝猜测」判成失败）
- ❌ 用阈值去治 rubric 的问题（分不开就说明阈值无效）
