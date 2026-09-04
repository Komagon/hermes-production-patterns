---
name: observability-trace
description: "可观测性/决策追溯 — 结构化日志记录决策链路、置信度、备选方案"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, observability, trace, logging, decision]
    category: conventions
    related_skills: [error-compact-pattern, state-file-pattern, data-driven-optimization]
hpp_category: observability
hpp_en: "Structured decision traces: why, confidence, alternatives."
hpp_maturity: L1
hpp_complexity: medium
hpp_reliability: medium
hpp_capability: skills
maturity: experimental
---

# 可观测性/决策追溯

> **核心问题：Agent 正常运行时，决策链路是黑箱。出了问题只能看最终结果，不知道中间做了什么决策、为什么这么做、考虑过哪些替代方案。**

## 1. 问题

Agent 运行时最常见的调试困境：

- 用户问"为什么选了方案 A 而不是方案 B？"——没人知道
- Pipeline 跑完了但结果不对——中间哪步决策失误？无法追溯
- 多 Agent 协作时——谁在什么时间做了什么决定？链路断了

传统的 logging 只记录"发生了什么"（what），不记录"为什么"（why）。

## 2. 结构化日志 Schema

每条 trace 记录必须包含决策上下文，而不只是执行结果：

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| `timestamp` | ISO 8601 | 决策发生时间 |
| `agent_id` | string | 做出决策的 Agent 标识 |
| `step` | string | 当前执行步骤名 |
| `decision` | string | 实际做出的决策（一句话） |
| `confidence` | number (0-1) | 对该决策的置信度 |
| `alternatives` | string[] | 考虑过但未选中的备选方案 |
| `evidence` | object[] | 决策依据，每项含 `source` 和 `summary` |
| `outcome` | string | 结果：`success` / `failure` / `partial` |

完整 JSON Schema 见 [`trace-schema.json`](./trace-schema.json)。

## 3. 和 error-compact-pattern 的关系

两个模式互补，覆盖 Agent 运行的两个侧面：

| 模式 | 覆盖场景 | 记录什么 |
|:-----|:---------|:---------|
| **error-compact-pattern** | 出错时 | 错误类型、恢复提示、是否可重试 |
| **observability-trace** | 正常运行时 | 决策理由、置信度、备选方案、证据 |

简单说：error-compact 是"出了错怎么压缩"，observability-trace 是"没出错时怎么留痕"。

两者结合才能完整还原 Agent 的运行轨迹：

```
正常决策 → [TRACE] 记录决策链路
     ↓ 出错
错误处理 → [ERROR_COMPACT] 压缩错误信息
     ↓ 自愈成功
继续执行 → [TRACE] 记录恢复后的决策
```

## 4. Trace 示例

```json
{
  "timestamp": "2026-09-04T14:30:00+08:00",
  "agent_id": "research-agent-01",
  "step": "select_data_source",
  "decision": "使用 HuggingFace Hub 搜索模型，而非直接访问 arXiv",
  "confidence": 0.85,
  "alternatives": [
    "直接搜索 arXiv API（延迟较高，但覆盖更全）",
    "使用本地缓存的模型列表（可能过期）"
  ],
  "evidence": [
    {
      "source": "performance_benchmark",
      "summary": "HF Hub API 平均响应 200ms，arXiv API 平均 1.2s"
    },
    {
      "source": "task_requirements",
      "summary": "任务需要最新模型元数据，本地缓存不满足"
    }
  ],
  "outcome": "success"
}
```

## 5. 和 state-file-pattern 的联动

关键决策摘要应写入 STATE.md，形成跨运行的决策可追溯性：

```markdown
## Decision Log
| Time | Step | Decision | Confidence | Outcome |
|:-----|:-----|:---------|:----------:|:--------|
| 14:30 | select_data_source | HF Hub > arXiv | 0.85 | ✅ |
| 14:32 | choose_model | Qwen3-8B > Llama3-8B | 0.72 | ✅ |
```

**写入规则：**
- 只有 `confidence < 0.7` 或 `outcome == "failure"` 的决策**必须**写入 STATE.md
- 高置信度且成功的决策可选写入（减少噪声）
- 每次运行结束时，将本轮所有低置信度决策汇总到 Lessons Learned

## 6. 使用指南

### 何时记录 Trace

| 场景 | 是否记录 | 原因 |
|:-----|:-------:|:-----|
| 选择工具/数据源 | ✅ | 用户会问"为什么用这个" |
| 选择模型/参数 | ✅ | 影响输出质量 |
| 简单的顺序执行 | ❌ | 无决策点，记了也是噪声 |
| 错误恢复路径 | ✅ | 和 error-compact 互补 |
| 多 Agent 委托 | ✅ | 需要跨 Agent 链路追踪 |

### Trace 存储

- **运行时**：写入执行日志（stdout / log file）
- **持久化**：关键决策写入 STATE.md Decision Log
- **分析**：可用 `trace-schema.json` 校验日志格式合规性
