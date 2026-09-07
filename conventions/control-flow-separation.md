---
name: control-flow-separation
description: "控制流分离 — 确定性代码 vs LLM 路由矩阵，能用代码的别用 LLM"
version: 1.2.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, control-flow, efficiency, graph]
    category: conventions
    related_skills: [error-compact-pattern, maker-checker, state-file-pattern, checkpoint-pattern]
migration: "v1.1.0 → v1.2.0:新增「工具侧效标注」章节(借鉴 Trace Engineering;READ_ONLY/MUTATING 静态分类,重放安全,mutating 走沙箱/需 approval)"
hpp_category: automation
hpp_en: "Deterministic steps belong in code, not in prompts."
hpp_maturity: L2
hpp_complexity: low
hpp_reliability: high
hpp_capability: terminal
maturity: beta
hpp_when_to_use: ["Loops with fixed logic", "Retry / counting / branching", "Cost-sensitive repeated runs"]
hpp_when_not_to_use: ["Genuinely open-ended exploration"]
---

# 控制流分离

> **对应 12-Factor Agents Factor 8: Own your control flow**

## 核心原则

**能用确定性代码表达的，绝不交给 LLM。**

Agent 的每一步要么是确定性代码（已知输入 → 已知输出），要么是概率性 LLM 调用（结果不确定）。两者必须分开管理。

## 对比

| | 确定性 (Code) | 概率性 (LLM) |
|:---|:---|:---|
| 成本 | ~0 tokens | 5k-50k+ tokens/步 |
| 可测试性 | 单元测试 | 评测框架 |
| 失败模式 | 崩溃 + 堆栈 | 静默跑偏（最危险） |
| 验证方式 | Exit code | Maker/Checker |

## 路由矩阵

```
Task Input
    │
    ├─ Deterministic Gate ── 这步有确定的、可重复的逻辑吗？
    │   ├─ YES → Code path（脚本、文件操作、API 调用、状态更新）
    │   └─ NO  → LLM path（推理、总结、分类、决策）
    │
    └─ Result → Append to context → Loop
```

### Graph 工作流的控制流

在 Graph（多节点）工作流中，控制流分离在每个节点内独立执行：

```
Graph Entry
    │
    ├─ Node R1 (Researcher)
    │   └─ Code path 优先 → 搜 API、读文件
    │   └─ LLM path → 仅做信息筛选和排序
    │
    ├─ Node R2 (Analyzer)
    │   └─ Code path → 数据聚合、统计
    │   └─ LLM path → 趋势分析、归因
    │
    ├─ Node R3 (Drafter)
    │   └─ LLM path 为主（生成内容）
    │
    ├─ Node R4 (Reviewer)
    │   └─ Code path → 格式检查、规则匹配
    │   └─ LLM path → 逻辑一致性、事实核查
    │
    └─ Node R5 (Decider)
        └─ Code path → 阈值判断、路由决策
```

核心规则：**Graph 执行器本身必须用代码编排**（DAG 调度器），
每个节点内部的 Code vs LLM 路由由 `control-flow-separation` 决定。

## 代码示例

```python
# ✅ 确定性 — 已知、可预测、零 LLM
def run_linter(file_path):
    result = subprocess.run(["eslint", file_path], capture_output=True)
    return {"status": "ok" if result.returncode == 0 else "fail"}

# ❌ 概率性 — LLM 推理，输出不确定
async def summarize_document(text):
    return await llm.complete(f"用三点总结：\n{text}")

# ✨ 混合 — 确定性框架 + 概率性核心
async def triage_issue(issue):
    severity = classify_by_keywords(issue)  # 确定性的初筛
    if severity == "UNCERTAIN":
        severity = await llm.classify(issue)  # LLM 处理边缘情况
    return severity
```

## 工具侧效标注（Tool Side-Effect Tagging，2026-09-07，借鉴 Trace Engineering）

**不知道工具能不能安全重放，就不知道失败能不能复现。** 侧效标注把每个工具静态分为 `READ_ONLY` 和 `MUTATING`，重放时 `READ_ONLY` 全量回放无副作用，`MUTATING` 走沙箱/需 approval，且执行前写 WAL（Write-Ahead Log）。这是「确定性重放」的安全前提，也是「规则写两遍」在工具层的落地。

### 分类标准

| 侧效 | 定义 | 重放行为 | approval |
|:--|:--|:--|:--|
| `READ_ONLY` | 纯查询，不改外部状态 | 全量回放，从 event ledger 取缓存 payload | 免审批 |
| `MUTATING` | 写文件/发消息/提交/发 PR/生成产物/执行代码 | replay 时走沙箱 dry-run；真实执行需 approval | 必审批 |

分类原则：**保守优先**——凡无法证明无副作用，一律标 `MUTATING`。工具行为明确只读时才标 `READ_ONLY`。

### 分类表（能力级，保守）

| 能力 | side_effect | 理由 |
|:--|:--|:--|
| web-search | READ_ONLY | 搜索/抓取，不改外部状态 |
| hithink-mcp | READ_ONLY | 查股价数据 |
| stock-data-mcp | READ_ONLY | 查股价数据 |
| hermes-cli | READ_ONLY | 查看状态/列表 |
| ollama | READ_ONLY | 推理，纯计算无副作用 |
| browser-export | READ_ONLY | 抓取并导出文本 |
| browser | MUTATING | 可填写表单/提交，保守标 MUTATING |
| git | MUTATING | push/commit 改远程 |
| github | MUTATING | PR/issue/release 写操作 |
| python | MUTATING | execute_code 任意副作用 |
| obsidian-vault | MUTATING | write_file 改 vault |
| image-gen | MUTATING | 生成图落盘 |
| tts | MUTATING | 生成 mp3 文件 |

### 注册表位置

`~/.hermes/routing/capability-registry.json` 每个能力条目带 `side_effect` 字段（机器可读，`capability_probe.py` 刷新时保留）。

### 强制规则

1. **工具注册时必须标注** `side_effect`，缺字段 = 默认 MUTATING（fail-closed）。
2. **MUTATING 工具在 replay 时** 走沙箱 dry-run，禁止无审批回放真实副作用。
3. **新增/修改工具分类时** 跑 `capability_probe.py`（保留 side_effect 字段，不重置）。
4. **approval 审批域已覆盖的 MUTATING 工具**，replay 时自动注入沙箱包装器，无需额外配置。

### 与「纯提示词约束」的关系

侧效标注是**机械层**——agent 不能说「我觉得这个工具是只读的」来绕过审批。分类写在 registry JSON 里，`capability_probe.py` 读到后强制，agent 的建议只在 GUIDANCE 层有效，MECHANICAL 层不听。这正是 anti-patterns #13「规则写两遍」的落地实例：规则写进提示词（告诉 agent 工具性质）+ 规则写进 registry（让审批绕不过）。

## 为什么重要

1. **调试** — 出问题知道检查代码还是检查 Prompt
2. **成本** — LLM 调用是最贵的环节，能用代码替代就替代
3. **可靠性** — 确定性代码可预期、可测试、可审计
4. **可读性** — 控制流清晰，不黑盒
