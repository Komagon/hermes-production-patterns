---
name: skill-evolution
description: "Skill 自动进化 — 基于验证门控的迭代优化，让 SKILL.md 越用越好"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, evolution, optimization]
    category: conventions
    related_skills: [maker-checker, state-file-pattern]
---

# Skill Evolution — 技能的自动进化

> **受 [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) 启发**  
> 把 SKILL.md 当作可训练的参数，用验证门控的优化循环让它越来越好。

## 核心思想

模型权重不需要动，进化**技能文件本身**——通过分析失败案例，对 SKILL.md 做有针对性的增、删、改，再用验证门确保每一次修改都是净收益。

## 进化循环

```
现有 SKILL.md
      │
      ▼
┌─ Rollout ───────────────┐
│  用当前技能跑 N 轮任务   │
│  记录每轮的评分数据      │
└────────┬─────────────────┘
         ▼
┌─ Reflect ───────────────┐
│  分析失败样本的共同模式  │
│  「技能缺了什么导致失败」│
└────────┬─────────────────┘
         ▼
┌─ Aggregate ─────────────┐
│  汇聚多轮反思 →          │
│  生成候选修改方案        │
└────────┬─────────────────┘
         ▼
┌─ Select ────────────────┐
│  从候选中选出最 promising│
│  的一条修改              │
└────────┬─────────────────┘
         ▼
┌─ Update ────────────────┐
│  对 SKILL.md 做一次      │
│  ADD / DELETE / REPLACE │
└────────┬─────────────────┘
         ▼
┌─ Evaluate ──────────────┐
│  用 hold-out 验证集评分  │
│  分数提高？→ 保留修改    │
│  分数下降？→ 回滚        │
└────────┬─────────────────┘
         ▼
     迭代下一轮（或收敛停止）
```

## 三种基本编辑操作

| 操作 | 含义 | 适用场景 |
|:---|:---|:---|
| **ADD** | 在 SKILL.md 中增加一段缺失的指引 | Agent 反复在同一个环节犯错，技能没覆盖到 |
| **DELETE** | 删除一段误导性或不必要的文字 | 技能中的某条规则导致 Agent 走偏 |
| **REPLACE** | 替换一段内容为更精准的版本 | 现有指引表达模糊，需要精炼 |

**规则**：每次迭代只做**一个操作**，这样回滚是原子级的。

## 验证门（Validation Gate）

**任何修改必须通过验证门才能保留。**

```python
def should_accept(candidate_score: float, baseline_score: float) -> bool:
    return candidate_score > baseline_score   # 严格提升才保留
    # 或候选项分数 > 基线分数 + 容差
    # return candidate_score > baseline_score + 0.01
```

- 使用 **hold-out 验证集**（没在 Rollout 阶段用过的任务）
- 如果分数下降 → 自动回滚到修改前的版本
- 如果分数持平 → 默认不保留（避免无意义变更）

## 收敛条件

当连续 N 轮验证门都拒绝修改时，停止迭代：

| 参数 | 建议值 | 说明 |
|:---:|:---|:---|
| `max_epochs` | 10 | 最大迭代轮数 |
| `patience` | 3 | 连续拒绝多少次后提前停止 |
| `hold_out_ratio` | 0.2 | 验证集占总任务的比例 |

## 与现有 Maker/Checker 的关系

| | Maker/Checker | Skill Evolution |
|:---|:---|:---|
| **粒度** | 单次输出验证 | 技能文件级进化 |
| **频率** | 每次运行 | 每月/每季度 |
| **修改对象** | 任务输出 | SKILL.md 本身 |
| **验证** | 五维评分 ≥ 40 | Hold-out 集分数 > 基线 |

两者互补：**Maker/Checker 保证单次输出质量，Skill Evolution 保证技能本身越来越好。**

## Hermes 中的实现路径

```bash
# 1. 跑当前 SKILL.md 收集基线数据
#    （手工或通过 cron 收集 N 轮运行结果）

# 2. 分析失败模式
#    查看 Maker/Checker 评分中 < 40 的案例 → 找出共同点

# 3. 应用编辑操作
#    对 SKILL.md 做 ADD / DELETE / REPLACE

# 4. Hold-out 验证
#    用未在步骤 1 中使用的任务跑一轮 → 对比分数

# 5. 保留或回滚
#    分数提高 → 提交新版本 SKILL.md
#    分数下降 → git revert
```

## 参考

- [SkillOpt: Executive Strategy for Self-Evolving Agent Skills](https://github.com/microsoft/SkillOpt) — Microsoft, MIT License
- [arXiv:2605.23904](https://arxiv.org/abs/2605.23904) — SkillOpt 论文
