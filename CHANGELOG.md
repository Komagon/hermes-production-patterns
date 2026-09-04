# Changelog

## v2.1.0 (2026-09-04)

### ✨ Pattern Expansion + Tooling Phase

#### Phase 1: 5 New Patterns (20 conventions total)
- **budget-guardrail.md** — 三级预算响应（预警/降级/熔断）防止 token/API 失控，与 cron-job-pattern/state-file-pattern 联动
- **human-escalation.md** — 高风险/低置信度/连续失败时升级到人工兜底，含状态机（running→escalated→confirm/reject）
- **multi-agent-isolation.md** — 命名空间隔离 + 文件锁 + 令牌桶，解决多 Agent 资源竞争
- **observability-trace.md** — 结构化决策追溯日志（决策/置信度/备选/证据），配套 trace-schema.json
- **data-retention-privacy.md** — 敏感信息检测（PII/密钥/API 响应）、保留期限、自动清理脚本

#### Phase 2: Pattern Linter (MVP)
- **scripts/lint.js** — 扫描 SKILL.md/STATE.md，三条规则：版本号缺失、STATE.md 缺失、敏感数据检测
- 支持 `--fix` 自动修复（补 frontmatter version/maturity 字段）
- `npx hpp-lint <path>` 或 `node scripts/lint.js <path>`
- 注册进 `package.json` bin + scripts

#### Phase 3: doctor CLI
- **scripts/doctor.py** — 交互式问答，5 个问题（任务类型/自主程度/风险等级/多 Agent/状态复杂度）
- 对照 pattern-composition 决策树自动推荐 pattern 列表（must/should/nice/reference）
- 输出 markdown 报告 + 安装命令，支持 `--auto` 非交互模式

#### Phase 4: Failure Case Library
- **examples/failures/** — 4 个真实失败案例复盘：
  - runaway-cron-tokens.md（Cron token 失控）
  - silent-data-corruption.md（数据静默损坏）
  - concurrent-state-conflict.md（多 Agent 状态冲突）
  - prompt-injection-escalation.md（注入导致越权）

#### Phase 5: Schema & Compatibility
- **conventions/pattern-schema.json** — Pattern frontmatter JSON Schema，linter 和文档共用同一份真理源
- **compatibility/matrix.md** — Pattern × Hermes 版本 × 依赖能力矩阵

#### Quality & Infrastructure
- test-prompts.json 从 25 条扩展到 30 条（覆盖 5 个新 pattern）
- pattern-composition.md 决策树新增「全自主 7x24 Agent」分支和 5 个新场景行
- README 核心概念表新增 5 个 pattern + 成熟度标注
- 回归测试 badge 更新为 30/30 Pass

## v2.0.0 (2026-08-31)

### 🚀 Productization Phase：从 Pattern Library 到 Production Engineering System

按 vault 路线图《Hermes_Production_Patterns_v2.0_产品化升级路线图》执行。核心战略转变：不再以增加 Pattern 数量为目标，而是 **MAKE PATTERNS USABLE**——先提升采用率，再扩展知识库。

- **Starter Kits（P0）** — `starter-kits/` 六个可复制骨架全部就位：basic-agent / cron-production / maker-checker / research-agent / memory-agent / self-evolving-agent。每个含 Patterns Used 表、安装、流程与验证清单；maker-checker 含 schema 契约 + red-flags + 压缩反馈模板 + 反测集；research-agent 含 evidence.jsonl 证据纪律 + 独立 Verifier；self-evolving-agent 含 Metrics/Baseline/Gate/Deploy/Rollback 全闭环。新增 `starter-kits/index.md` 选择路径表。
- **Production Stacks（P0）** — `stacks/` 五个官方组合：🟢 Starter / 🟡 Reliable Automation / 🔵 Quality / 🟣 Memory / 🔴 Evolution。每个含组合公式、对应公约、何时用、何时升级、落地方式；叠加原则对齐成熟度 L1-L3。
- **10-Minute Quick Start（P0）** — `quickstart.md`：六步从零到第一个 Production Agent（复制 kit → 定义技能 → 初始化状态 → 运行 → 独立验证 → 挂定时）。
- **Router 2.0（P0）** — docs Router 页新增 Problem→Diagnosis 表：7 类用户症状 → 诊断 → 推荐 Stack → 落地 kit 锚点。
- **Production Recipes（P1）** — `recipes/` 七个完整工程方案：daily-news-agent / content-pipeline / research-pipeline / autonomous-monitor / coding-agent-pipeline / knowledge-agent / multi-agent-workflow。每个九节齐全：Problem / Architecture / Patterns Used / Installation / Configuration / Run / Failure Modes / Recovery / Metrics。
- **Compatibility Matrix（P1）** — `compatibility/`：人读版 README + 机器可读 `hermes-versions.yaml`（13 个 pattern 的 min_hermes/status/requires）。
- **Production Audit（P1）** — `audit/`：审计规范（Pattern Evidence 哲学）+ 15 项行为检查单（五组 A-E）+ 五维加权 Readiness Score 模型（Reliability 25 / Observability 20 / Recoverability 20 / Quality 20 / Evolution 15）。
- **hpp CLI（P2）** — `cli/hpp.py`（纯 stdlib）：`hpp init` 六 kit 脚手架、`hpp add` 五 pattern 增量注入（幂等跳过）、`hpp validate` 结构/契约/密钥校验、`hpp audit` 五维打分条形图 + 缺失项 + 建议命令、`hpp doctor` 环境诊断。已在本地完成全命令实测。
- **网站重组** — mkdocs nav 改为 START HERE / BUILD / UNDERSTAND / VALIDATE / 项目说明 / 总览 / Examples / Templates / 参与贡献；build_docs.py 复制清单扩展至 stacks/recipes/audit/compatibility + 新增 starter-kits 生成页与 cli 页；首页 Hero CTA 改为 10-Minute Quick Start 优先。
- **清理** — 移除误生成的 `' /'` 目录与 stacks/ 空骨架。

## v1.06.00 (2026-08-30)

### ✨ 网站 V2:从文档站升级为 Agent Production Engineering 知识系统

按 V2 UI/UX 改版任务书执行(设计文档见 `.hermes/reports/website-v2/`):

- **首页 Landing 化**(§6-§8)— Hero「BUILD AGENTS THAT SURVIVE PRODUCTION.」+ 三 CTA + 可点击生产架构 SVG + 终端元素;Why Agents Fail 六问题卡;Problem→Pattern→Result 六链;成熟度时间线 L1-L3;Choose Your Path 三角色;案例 Case-Study 卡。构建期由 `build_docs.py` 从 frontmatter/正文派生,零硬编码内容(§36)。
- **统一深色工程终端风**(§14/§29)— 配色令牌 #080A0D/#78FFB7/#62D9FF 全套落地并桥接 Material 变量;取消浅色主题;分类 accent 走卡片左边框+kicker,禁高饱和整卡背景。
- **Pattern Explorer**(§25)— 新页 `/patterns-library/`:分类过滤 pills + 关键词搜索 + SHOWN 计数,4.2KB 无依赖 JS。
- **生产架构页**(§19-20)— 新页 `/architecture-page/`:Normal/Error 双流 + 组件职责表;retry→maker 回边正交布线。
- **Engineering Decision Layout**(§15-18)— 全部 15 个公约页注入分类 kicker、MATURITY/COMPLEXITY/RELIABILITY/HERMES/VERSION 信息栏、When(Not) ✓/✕ 双栏卡;数据源为新增 `hpp_*` frontmatter 键(可选,缺省安全,正文零改动)。
- **关系图谱升级**(§11)— 分类环排 + 弦式曲边 + 双环标签错位 + 中心品牌遮罩 + hover 高亮/关联弱高亮/键盘可达。
- **搜索**(§24)— ⌘K + placeholder「搜索 Patterns、问题、架构… (⌘K)」(zh locale 覆写)。
- **SEO**(§38)— `overrides/main.html` 补每页 OpenGraph/Twitter card;独立 title/description。
- **响应式**(§34)— 390px 实测零横向溢出;图在窄屏保持可读尺寸 + 横向滚动。
- **渐进增强红线** — 滚动淡入 1.5s 兜底强制可见,JS 失效不空洞;prefers-reduced-motion 全关。
- 旧首页(README)完整保留为 `/readme/`,零页面删除(§37);check-nav 43 页全挂 nav;markdownlint / strict build / 视觉五轮复检全 PASS。

## v1.05.01 (2026-08-30)

### ✨ 文档站吸收 Skill OS 理念:决策入口 + 模式图谱 + 契约卡 + nav 回归闸门

- **路由入口 Router**(`router.md`,构建自动生成)— 借鉴 Hermes Skill OS 路线图的 MASTER ROUTING 思想:从 15 个公约的 frontmatter `description` 提取「场景信号 → 入口公约 → 配套模式」决策表,新读者按问题找模式,不再靠翻目录。
- **模式图谱 Skill Graph**(`skill-graph.md`)— 从 `related_skills` 声明提取公约互链,构建期生成纯内联 SVG(零外部 CDN 依赖,规避 mermaid/unpkg 国内不可达问题),节点可点击进入对应公约。
- **Skill Contract 卡**— 每个公约页 H1 下自动注入折叠契约卡(版本/分类/相关模式),呼应路线图「Skill 从一段 Prompt 升级为可声明、可验证的能力模块」;数据源仍是 frontmatter,无新增维护负担。
- **check-nav 回归闸门**(`scripts/build_docs.py --check-nav`,已入 CI)— 呼应路线图 Regression 原则:任何 docs 页面未挂进 nav 或 nav 引用幽灵页面即构建失败,防止站点演化中的「孤儿页面」退化。
- 全部生成物仍由 `build_docs.py` 单点产出,`docs/`/`site/` 保持 gitignore;markdownlint 与 `mkdocs build --strict` 均零警告。

## v1.05.00 (2026-08-30)

### ✨ maker-checker v1.1.0 → v1.2.0:新增「红线优先」判决制(加功能,不需迁移)

- **实现要点第 6 条** — 借鉴 JIT-Agent(bingreeky/JIT, arXiv 2608.25593)评审团的 Architecture/Red-flag charter 思路:评分制之外允许预定义「命中即 FAIL」的 red flags,Checker 报告须写明检查了哪几条、是否命中;红线只从真实失败案例蒸馏,禁止凭想象堆砌。向后兼容:旧触发方式与五维评分流程不变。
- 评估过程:JIT 五专家 charter 对照自家体系做必要性/可行性评估(evolution-gate 的 G3/G4、routing_check、反测集已有对位物),仅 Architecture-Proportionality 一项是真缺口但落在 hermes-skill-os 侧;评审团/全套蒸馏方案因架构与任务不成比例被否。

## v1.04.01 (2026-08-29)

### 🔧 修正:全面体检发现的 6 处问题(修 bug 不改接口,按 skill-evolution 版本表升 patch)

- **frontmatter 缺失** — `conventions/data-driven-optimization.md` 补齐全套 YAML frontmatter(15 个 conventions 中唯一漏网,违反仓库自身模板约定)。
- **覆盖声明纠偏** — v1.04.00 的「覆盖全部 15 个模式」表述不准确:速查表实际覆盖 14 个行为契约技能,`hermes-capability-map` 是参考映射表、无行为契约可反测。README/skill-evolution 已改为「14 个行为契约模式 + capability-map 豁免」,速查表补注豁免行。
- **反测运行范围成文** — `skill-evolution` v1.3.0 → v1.3.1:把「升级跑映射条目、发版/tag 前跑全量、横切技能(evolution-gate/pattern-composition)变更跑全量、失败重跑一次再回滚」的口径写进章节(此前仅口头约定,本次源于社区问答沉淀)。
- **package.json 版本漂移** — 1.03.00 → 1.04.01(v1.04.00 发布时漏更)。
- **死链修复** — `examples/daily-news-digest/SKILL.md` 中 5 处 `../conventions/` 相对链接层级错误(应为 `../../conventions/`),本地链接检查器抓到、CI markdown-link-check 因 max-depth 配置未覆盖而漏报。
- **README.en.md 同步** — 补 v1.04.00/v1.04.01 发布说明与回归反测集介绍(中文版已有、英文版缺失)。

## v1.04.00 (2026-08-27)

### ✨ v1.04.00 新增:回归反测集(借鉴 dao-skill)

- **回归反测集** — `test-prompts.json`(仓库根,与 15 个技能平级):25 条回归提示词,每条含 `prompt / expected / assertions(应命中) / forbidden(禁止触犯)`,覆盖全部 15 个 production pattern 的核心行为契约(evolution-gate 走闸门、state-file Read Before Run、maker-checker 独立验证、secret-management 环境变量、cron 幂等防静默失败等)。反测集的定位 = 「技能升级的验收标准:旧失败不再出现、旧成功仍然成立」;结构检查 ≠ 行为反测,dry-run 不能当已验证(借鉴 dao-skill 的 E0-E4 证据分级思维)。
- **skill-evolution 升级 v1.3.0** — `conventions/skill-evolution.md`:新增「回归反测集」章节,定义何时跑(技能升级后 / 用户反馈"不对"时 / evolution-gate G5 回归对比)、怎么跑(prompt 喂 Agent → 检查 assertions 命中 + forbidden 未触)、新增条目规则(一个真实失败模式 → 一条反测,同根同触发合并防膨胀),并附 15 技能 → 25 条目反测覆盖速查表。
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
