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

## 为什么重要

1. **调试** — 出问题知道检查代码还是检查 Prompt
2. **成本** — LLM 调用是最贵的环节，能用代码替代就替代
3. **可靠性** — 确定性代码可预期、可测试、可审计
4. **可读性** — 控制流清晰，不黑盒
