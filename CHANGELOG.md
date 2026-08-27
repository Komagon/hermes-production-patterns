# Changelog

## v1.04.00 (2026-08-27)

### ✨ v1.04.00 新增:回归反测集(借鉴 dao-skill)

- **回归反测集** — `test-prompts.json`(仓库根,与 15 个技能平级):20 条回归提示词,每条含 `prompt / expected / assertions(应命中) / forbidden(禁止触犯)`,覆盖全部 15 个 production pattern 的核心行为契约(evolution-gate 走闸门、state-file Read Before Run、maker-checker 独立验证、secret-management 环境变量、cron 幂等防静默失败等)。反测集的定位 = 「技能升级的验收标准:旧失败不再出现、旧成功仍然成立」;结构检查 ≠ 行为反测,dry-run 不能当已验证(借鉴 dao-skill 的 E0-E4 证据分级思维)。
- **skill-evolution 升级 v1.3.0** — `conventions/skill-evolution.md`:新增「回归反测集」章节,定义何时跑(技能升级后 / 用户反馈"不对"时 / evolution-gate G5 回归对比)、怎么跑(prompt 喂 Agent → 检查 assertions 命中 + forbidden 未触)、新增条目规则(一个真实失败模式 → 一条反测,同根同触发合并防膨胀),并附 15 技能 → 20 条目反测覆盖速查表。
- **AGENTS.md 能力表** — 增加回归反测集入口。

## v1.03.00 (2026-08-20)

### ✨ v1.03.00 新增（3 个实战模式，来自 7x24 生产环境近期优化）

- **自更新安全流程** — `conventions/self-update-pattern.md`：把 `hermes update` 从「安装动作」变成「变更管理」。含 v0.20.4+ autostash 可能不自动恢复的坑（更新后查 `git stash list` → 手动 `stash apply` → modify/delete 冲突 `git rm`）、更新后测试失败基线（30524 测试/106 失败全量归因 → 区分上游失败 vs 本地回归）、回滚路径（git checkout）、STATE.md 更新记录模板。
- **Memory OS** — `conventions/memory-os-pattern.md`：五层记忆架构（Context/Working/Long/Experience/Evidence）、读侧三层检索 + RRF 融合（LanceDB 向量 + 知识图谱 + FTS5）、写侧 G4 数据闸（对账查重、证据校验、索引同步）、每日复盘循环（DailyReview cron）。明确 RAG ≠ Memory。
- **进化闸门** — `conventions/evolution-gate.md`：G1-G5 五道闸门（输入/运行时/质量/数据/进化）、五维加权评估（准确性 30% / 证据 25% / 完整 20% / 可靠 15% / 成本 10%）、G5 分档（≥85 promote / 55-84 improve / <55 failures）、回归测试 Deploy or Rollback、技能可度量化（usage_count/success_rate/average_score/cost/confidence）、落地工具 loopctl（11 子命令）。

### 📝 v1.03.00 改进

- **skill-evolution 升级 v1.2.0** — 新增「技能瘦身（Skill Slimming）」章节：description 前 57 字符截断规则、瘦身三原则（只留会用的 / 触发条件前置 / 约束而非教程）、2026-08-16 实战案例（头条写作技能只留硬约束）。
- **hermes-capability-map 升级 v1.1.0** — 新增「七、知识检索与记忆」族（he-knowledge MCP / index_vault / kg_extract / session_search / memory 双库 / 证据校验）与「八、生命周期与进化」族（loopctl / golden dataset / hermes update / git stash / 测试基线）。
- **pattern-composition 升级** — 决策树新增「系统阶段」分支（起步→cron→知识→优化），速查表新增 3 行（系统升级 / 知识沉淀 / 持续优化）。
- **README / README.en / AGENTS.md / CONTEXT.md** — 结构树、核心概念速查、能力表、术语表同步新增 3 个模式。

### 🧹 v1.03.00 兼容性

- 无破坏性变更。所有既有文件向后兼容；新增 3 个独立 convention，2 个升级文件仅追加章节与 frontmatter version 变更。

---
## v1.02.00 (2026-08-08)

### ✨ v1.02.00 新增

- **Hermes 能力 × 模式映射** — `conventions/hermes-capability-map.md` 新增：把 2026-08 前后的 Hermes 工具能力（cronjob monitor 族、delegate_task、session_search、execute_code、skill_manage 等）对号入座到既有模式。原则：能力在变，模式不变。
- **cron-job-pattern 升级 v1.1.0** — 新增「Hermes 原生 Monitor 模式」：`monitor_script`/`monitor_url`（哈希抑制，变了才烧 token）、`no_agent=True` Watchdog（零 token 告警）、`context_from` 链式、`enabled_toolsets`、`attach_to_session`、`workdir`，附场景选择矩阵。
- **maker-checker 升级 v1.1.0** — 新增「委托 Checker」选项：`delegate_task` 独立子代理 + `output_schema` 契约校验 + `live transcripts` 审计，与 Opik Judge 并列，附选择建议。
- **state-file-pattern 升级 v1.1.0** — 新增恢复手段：`session_search`（FTS5 跨会话检索）与 `memory`（batch operations 原子更新）作为 STATE.md 的补充。
- **skill-evolution 升级 v1.1.0** — 新增落地工具：`skill_manage`（patch/edit/delete/absorbed_into/write_file）对应技能生命周期各阶段。
- **secret-management 升级 v1.1.0** — 新增按需加载工具：`tool_search`/`tool_call` 延迟加载，工具面越窄凭据暴露面越小。

### 📝 v1.02.00 改进

- README / README.en 项目结构树与核心概念速查同步新增 hermes-capability-map 与 Monitor 模式引用。

### 🧹 v1.02.00 兼容性

- 无破坏性变更。所有 v1.0.x / v1.1.0 文件向后兼容；四个升级文件仅追加章节与 frontmatter version 变更。

---
## v1.01.03 (2026-07-29)

### ✨ v1.01.03 新增

- **数据驱动技能优化公约** — `conventions/data-driven-optimization.md` 新增将真实运营数据嵌入技能文件的方法论。包含正向约束（什么有效）、负向约束（什么无效）、战术约束（执行规则）三层结构，以及自动化反馈循环设计。
- **公众号文章流水线示例** — `examples/wechat-article-pipeline.md` 新增完整的公众号写作+AI检测+去AI味+配图生成+数据优化闭环示例。内置8维度AI味评分引擎(`scripts/ai_detect.py`)、Obsidian模板(`references/article-template.md`)，以及账号运营前4周的真实数据反馈验证。

### 📝 v1.01.03 改进

- **pattern-composition 决策树** — 新增 data-driven-optimization 节点的关联引用。

### 🧹 v1.01.03 清理

- 无破坏性变更。所有 v1.1.0 文件向后兼容。
- 移除仓库根目录下的过期 ChatGPT 图片。

### 📝 v1.01.03 项目健康检查

- **README 项目结构树** — 新增 `data-driven-optimization.md`、`wechat-article-pipeline.md`、`maturity-checklist.md` 引用。中英文同步更新。
- **AGENTS.md** — 新增 data-driven-optimization 和 wechat-article-pipeline 入口。
- **CONTEXT.md** — 更新最后修改时间戳。
- **ARCHITECTURE.md** — Maker 组件新增 draw.io CLI、data-driven-optimization 数据源引用。
- **Smoke test** — 新增 `examples/wechat-article-pipeline/test_example.py`，覆盖 clean text 和 AI-tainted text 两种场景。
- **CHANGELOG.md 重复标题** — MD024 修复。

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
