---
name: evolution-gate
description: "进化闸门 G1-G5 — 五维加权评估、经验价值判定、回归对比、Deploy or Rollback"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, evolution, evaluation, gate, regression, loopctl]
    category: conventions
    related_skills: [maker-checker, data-driven-optimization, skill-evolution, memory-os-pattern, state-file-pattern]
---

# 进化闸门（Evolution Gate）

> **进化不是「顺手改进」，是「有闸门、有评估、有回归」的工程流程。** 没有闸门的进化叫折腾——改坏了不知道，改好了也不知道为什么好。

## 问题

- 技能/流程改了，怎么知道是变好还是变差？全靠感觉
- 一个任务做完了，哪些经验值得沉淀为技能？哪些该扔进错误分类？没有判定标准
- 每次优化都怕破坏已有能力，但回归怎么测？凭运气
- 「改进」积累了一大堆，哪些真正有效？没有数据支撑

## G1-G5 五道闸门

```
任务进入 → G1 输入闸 → G2 运行时闸 → G3 质量闸 → G4 数据闸 → G5 进化闸 → 产出
```

| 闸门 | 位置 | 校验什么 | 不过怎么办 |
|:---|:---|:---|:---|
| **G1 输入闸** | 任务开始时 | 任务完整性、权限、参数 | 补齐/拒绝，不硬跑 |
| **G2 运行时闸** | 执行过程中 | 工具使用、文件操作、外部动作是否越界 | 拦截，降级为只读 |
| **G3 质量闸** | 产出时 | 准确性、完整性、证据 | 打回重做或标记降级 |
| **G4 数据闸** | 写记忆前 | 知识可验证、噪声过滤、图谱更新 | 只记有据可查的 |
| **G5 进化闸** | 任务收尾 | 这段经验值不值得沉淀/改进技能？ | 按分档处理（见下） |

## G5 进化闸：经验价值判定

任务/技能评估后产出**五维加权评分**（0-100）：

| 维度 | 权重 | 评什么 |
|:---|:---:|:---|
| 准确性 | 30% | 结论与事实是否一致 |
| 证据可靠性 | 25% | 依据是否可溯源、可复核 |
| 完整性 | 20% | 是否覆盖任务全部要求 |
| 可靠性 | 15% | 过程是否稳定、可复现 |
| 成本效率 | 10% | token / 时间消耗是否合理 |

### 分档规则（G5 判定）

| 分数 | 判定 | 动作 |
|:---|:---|:---|
| **≥ 85** | 高价值经验 | Promote → 沉淀为技能 / 更新技能并升版 |
| **55-84** | 有价值但有缺陷 | Improve → 修问题后重评估 |
| **< 55** | 失败案例 | 归入错误分类 / Failures，提炼教训 |

每次评估产出固定结构：

```text
Task          任务描述
Result        实际结果
Score         五维加权分（含各维明细）
Issues        问题清单
Root Cause    根因分析
Improvement   改进方案
```

> **实战**（Evolution OS v5.2）：评估记录落盘 `telemetry/evaluation.jsonl`（带 weights / root_cause / improvement_plan），改进方案落盘 `Improvements/{id}.md`，golden dataset 六类基准（coding/research/investment/writing/automation/reasoning）作为对比锚点。

## 回归测试：Deploy or Rollback

任何优化上线前必须跑回归——用「之前的任务」验证「新版本」没有破坏已有能力：

```text
Previous Tasks
    ↓
New Agent Version
    ↓
Compare Results（与基线对比）
    ↓
Deploy or Rollback
```

| 回归结果 | 判定 | 动作 |
|:---|:---|:---|
| 新版本 ≥ 基线 | ✅ 通过 | Deploy，更新基线 |
| 新版本 < 基线 | ❌ 回退 | Rollback，记录失败原因 |

**回归基线是资产**：每次 Deploy 后把结果存为基线，下次优化对比用。基线对比失败必须给根因，不许「先上线再说」。

## 技能的可度量化

技能不是「写完了就完了」，而是可度量的对象：

| 指标 | 含义 | 谁更新 |
|:---|:---|:---|
| `usage_count` | 被调用次数 | 每次使用后 |
| `success_rate` | 成功率 | 每次使用后 |
| `average_score` | 平均评估分 | G5 评估后 |
| `cost` | 平均成本 | 每次使用后 |
| `confidence` | 置信度 | G3 后 |
| `last_update` | 最后更新 | 每次更新 |

**规则**：高分技能 Promote（沉淀/升版）；低分技能 Review or Remove（降级/删除）。数据驱动的技能迭代闭环，见 `data-driven-optimization`。

## 落地工具：loopctl（Evolution OS）

| 子命令 | 对应闸门/环节 |
|:---|:---|
| `init` / `list` / `status` | G1 输入闸（任务台账） |
| `advance` / `update` / `close` | 生命周期推进 |
| `review` | G3 质量闸 + G5 进化闸（五维加权评估 + 分档判定） |
| `regression` | 回归对比（list/compare → Deploy or Rollback） |
| `heartbeat` / `heartbeat-q` | 运行时健康（G2 运行时闸） |
| `evidence` | G4 数据闸（证据登记） |

## 与既有模式的关系

| 模式 | 关系 |
|:---|:---|
| `maker-checker` | G3 质量闸的验证者实现；Check FAIL 即未过闸 |
| `data-driven-optimization` | G5 产出数据 → 技能约束迭代的数据源 |
| `skill-evolution` | G5 Promote/Improve 的落地载体（版本化） |
| `memory-os-pattern` | G4 数据闸的写侧纪律（什么值得进记忆） |
| `state-file-pattern` | 任务台账 + 基线存储的载体 |

## 反模式

| ❌ 错误做法 | 后果 |
|:---|:---|
| 改完不评估 | 不知道变好还是变差，进化=撞运气 |
| 评估只看总分不看分维度 | 总分还行但证据维度崩了，照样埋雷 |
| 回归不过还上线 | 老能力悄悄退化，用户先发现 |
| 只沉淀成功经验 | 失败教训同样值钱，全扔了等于白踩坑 |
| 技能指标从不回写 | 无法判断哪个技能该升该删 |
