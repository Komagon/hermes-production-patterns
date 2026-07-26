---
name: maker-checker-article-pipeline
description: "文章生成流水线示例 — Maker 写稿→Checker 五维验证→Gate 发布，带成熟度分级"
version: 1.1.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, example, article, maker-checker, pipeline, opik]
    category: examples
    related_skills: [maker-checker, state-file-pattern, error-compact-pattern, maturity-staging-l1-l2-l3, opik-eval]
---

# Maker/Checker Article Pipeline

> 完整的文章生成流水线示例：Maker 写稿 → Checker 验证 → Gate 发布
> 支持手动 Checker 和 Opik 自动化 Checker 两种模式

## 工作流

```
1. Maker 角色接收 Topic
2. Maker 调研+撰写初稿
3. Checker 角色独立验证（选模式 A 或 B）
   A. 手动 Checker：不同 Agent 五维评分
   B. Opik Judge：LLM-as-a-Judge 自动化评分
4. Gate 判断：
   - 手动 PASS ≥ 40/50  → 发布
   - Opik PASS ≥ 0.7   → 发布
   - FAIL → 反馈给 Maker 修改（最多 3 轮）
5. 3 轮仍 FAIL → 上报人类
```

## Checker 模式选择

| 模式 | 执行方式 | 评分 | 成熟度 | 适用 |
|:---|:---|:---|:---:|:---|
| **A. 手动 Checker** | 独立 Agent（不同模型） | 五维 1-10 分 | L1→L2 | 高价值内容、首次上线 |
| **B. Opik Judge** | LLM-as-a-Judge 自动评分 | 归一化 0-1 | L2→L3 | 批量任务、日常运行 |

### 模式 A：手动 Checker（默认）

Maker 写稿后，启动一个独立的 Agent 实例加载 `maker-checker` skill 做验证：

```
角色: Checker
模型: 与 Maker 不同的模型
任务: 对文章做五维验证
```

| 维度 | 含义 | 1-10 分 |
|:---|:---|:---:|
| 🎣 钩子强度 | 开头能不能让人点进来？ | /10 |
| 📊 数据支撑 | 数字、对比表、具体案例到位吗？ | /10 |
| 🧹 AI味检测 | 有没有 AI 套话？ | /10 |
| 📱 手机适配 | 段落长度、排版舒适吗？ | /10 |
| 🎯 互动钩子 | 结尾有没有让人想评论？ | /10 |
| **总分** | | **/50** |

### 模式 B：Opik Judge 自动化 Checker

使用 Opik LLM-as-a-Judge 替代人工 Agent 做初筛：

```python
from judge import evaluate_answer

result = evaluate_answer(
    question="评估文章质量",
    answer=article_text,
    criteria=["hook_strength", "data_support", "ai_tone", "mobile_friendly", "engagement"]
)

if result.score >= 0.7:
    # PASS → 直接发布（或人工抽检终审）
    publish(article_text)
else:
    # FAIL → 返回具体反馈给 Maker 修改
    feedback_to_maker(result.feedback)
```

## 成熟度分级

| 等级 | Checker 方式 | Gate | 说明 |
|:---:|:---|:---|---|
| L1 🟢 | 人工 Review | 人工 | 第 1-2 周，建立基线 |
| L2 🟡 | 手动 Agent Checker | 人工批准 | 第 3-4 周，Agent 辅助 |
| L3 🔴 | Opik Judge 自动化 + 人工抽检 | 自动 | L1+L2 零失败后 |

## 隔离要求

- Maker 和 Checker 必须使用**不同 Agent 实例**运行
- 手动 Checker 优先使用不同模型（Maker: 强推理, Checker: 够用即可）
- 无法双模型时：Clear 上下文后独立加载 Checker Skill
- Opik Judge 模式无需独立 Agent，但需配置 Judge 模型
