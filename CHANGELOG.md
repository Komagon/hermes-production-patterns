# Changelog

## v1.2.0 (2026-07-29)

### ✨ v1.2.0 新增

- **数据驱动技能优化公约** — `conventions/data-driven-optimization.md` 新增将真实运营数据嵌入技能文件的方法论。包含正向约束（什么有效）、负向约束（什么无效）、战术约束（执行规则）三层结构，以及自动化反馈循环设计。
- **公众号文章流水线示例** — `examples/wechat-article-pipeline.md` 新增完整的公众号写作+AI检测+去AI味+配图生成+数据优化闭环示例。内置8维度AI味评分引擎(`scripts/ai_detect.py`)、Obsidian模板(`references/article-template.md`)，以及账号运营前4周的真实数据反馈验证。

### 📝 v1.2.0 改进

- **pattern-composition 决策树** — 新增 data-driven-optimization 节点的关联引用。

### 🧹 v1.2.0 清理

- 无破坏性变更。所有 v1.1.0 文件向后兼容。

---

## v1.1.0 (2026-07-26)

### ✨ 新增

- **Opik 自动化 Checker 模式** — `maker-checker` 公约新增 Opik LLM-as-a-Judge 作为自动化 Checker 选项，与手动 Checker 并列。支持五维评分映射到 Opik 指标（AnswerRelevance, ContextRelevance, Hallucination 等），阈值 ≥ 0.7。配套参考文档 `references/opik-as-checker.md`。
- **Graph 工作流集成** — `pattern-composition` 决策树新增 Graph 工作流分支，速查表和关系图新增 `checkpoint-pattern` + `graph-executor` 节点。`control-flow-separation` 新增 Graph 节点内 Code vs LLM 路由决策指南（R1→R5 逐节点）。
- **状态管理关联资产** — `state-file-pattern` 新增关联文件引用（`scripts/validate_state.py`, `scripts/atomic_state_write.py`, `conventions/state-schema.json`, `templates/STATE.md.template`）。

### 📝 改进

- **maker-checker-article-pipeline 示例** — 重写为双模式架构（手动 Checker / Opik Judge），成熟度分级更新为 L1→L2→L3 三档。
- **state-file-pattern 模板** — 内嵌模板改为引用 `templates/STATE.md.template`，减少文档冗余。
- **related_skills 更新** — 各 skill 跨引用关系补全，新增 `opik-eval`、`checkpoint-pattern`、`graph-executor` 关联。

### 🧹 清理

- 无破坏性变更。所有 v1.0.0 文件向后兼容。
