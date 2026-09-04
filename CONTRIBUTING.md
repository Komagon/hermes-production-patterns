# 贡献指南

欢迎贡献！以下是参与本项目的方式和规范。

## 如何贡献

### 🐛 报告问题
- 提交 [Issue](https://github.com/Komagon/hermes-production-patterns/issues) 前请先搜索是否已有类似问题
- 标题用一句话清晰描述问题
- 正文包含：复现步骤、预期行为、实际行为、环境信息

### 💡 建议新模式

我们接受三种成熟度级别的模式提案：

| 级别 | 要求 | 标签 |
|:---|:---|:---:|
| **🟢 battle-tested** | 生产环境验证 ≥30 天，有真实运行数据 | `battle-tested` |
| **🟡 beta** | 有初步验证数据（<30 天或小规模），有具体场景 | `beta` |
| **🔵 experimental** | 有理论依据或单次验证，尚未长期运行 | `experimental` |

**提案流程**：
1. 使用 [Pattern Proposal](https://github.com/Komagon/hermes-production-patterns/issues/new?template=pattern-proposal.md) Issue 模板
2. 说明该模式解决什么问题
3. 提供至少一个真实场景的案例
4. 附上对照：用之前 vs 用之后
5. 标注你认为的成熟度级别（我们可能根据实际情况调整）

> 即使是 `experimental` 级别的模式也有价值——它为社区提供了讨论和验证的起点。进入仓库后，通过实际使用积累数据，可以逐步升级为 `beta` → `battle-tested`。

### 🔧 提交 PR
1. Fork 本仓库
2. 从 `main` 创建新分支：`feat/your-feature-name`
3. 提交修改
4. 确保 PR 描述关联相关 Issue

## 质量标准

每条模式必须满足：
- ✅ 有明确的「核心原则」段落
- ✅ 有 Before/After 对比（适用时）
- ✅ 语言中英皆可
- ✅ frontmatter 包含 `maturity` 字段（`battle-tested` / `beta` / `experimental`）

**battle-tested 额外要求**：
- ✅ 在生产环境中验证过（不接受纯理论设计）
- ✅ 附带至少一条实测数据或运行日志片段

## 回归测试

新增行为契约模式时，需要在 `test-prompts.json` 中添加对应的回归测试用例：

```json
{
  "id": "your-pattern-name-scenario",
  "prompt": "一个会触发该模式的用户提问",
  "expected": "Agent 应该怎么做",
  "assertions": ["必须出现的关键词1", "关键词2"],
  "forbidden": ["禁止出现的行为1", "行为2"]
}
```

运行 `python scripts/run_regression.py` 验证格式正确。

## 行为准则

- 尊重他人，建设性反馈
- 不接受 AI 生成的 PR 不做人工审查
