---
name: memory-os-pattern
description: "Memory OS — 五层记忆架构、向量/图谱/RRF 检索、写侧纪律与每日复盘"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, memory, vector, graph, rrf, retrieval]
    category: conventions
    related_skills: [state-file-pattern, evidence-memory, self-update-pattern, data-driven-optimization]
hpp_category: memory
hpp_en: "Five-layer memory architecture with vector/graph retrieval."
hpp_maturity: L3
hpp_complexity: high
hpp_reliability: medium
hpp_capability: memory
hpp_when_to_use: ["Long-lived personal agents", "Agents needing cross-session facts"]
hpp_when_not_to_use: ["Stateless request/response bots"]
---

# Memory OS（认知记忆系统）

> **STATE.md 是任务状态，Memory OS 是认知记忆。** 任务状态回答「这事干到哪了」，认知记忆回答「我积累了哪些可复用的知识与经验」。7x24 自主运行的 Agent 两者都要，缺一不可。

## 问题

- 上下文窗口会满、会话会断——知识只存在于上下文里，等于没有记忆
- `memory` 工具能存事实，但容量有限、无序，检索只能靠关键词
- 写进 vault 的知识没有证据校验，沉淀越多噪声越多
- 知识只进不出，没有「哪些经验真正有用」的反哺循环

## 五层记忆架构

```
┌─────────────────────────────────────────────────┐
│ Context Memory   会话上下文（当前任务）            │
│ Working Memory   工作记忆（任务中间态 = STATE.md） │
│ Long Memory      长期记忆（事实，memory 工具）     │
│ Experience Memory 经验记忆（历史会话 = session_search）│
│ Evidence Memory  证据记忆（可校验的知识库，带来源） │
└─────────────────────────────────────────────────┘
```

| 层 | 存什么 | 载体 | 生命周期 |
|:---|:---|:---|:---|
| Context | 当前对话、临时推理 | 会话上下文 | 会话结束即消失 |
| Working | 任务进度、幂等键、断点 | `STATE.md` | 任务完成归档 |
| Long | 用户偏好、环境事实、约定 | `memory` 工具（user/memory 双库） | 长期，人工维护 |
| Experience | 历史任务怎么做的、踩过什么坑 | `session_search`（FTS5 全量会话检索） | 永久，可检索 |
| Evidence | 校验过的知识（带 claim/evidence/source/confidence） | vault + 向量库 + 图谱 | 永久，需复核 |

**关键区分：RAG ≠ Memory。** RAG 是从外部语料检索答案；Memory OS 是 Agent 自身的认知沉淀。检索能力只是 Memory OS 的「读侧」，写侧纪律（什么值得沉淀、怎么校验）才是核心。

## 读侧：三层检索 + RRF 融合

单一检索方式都有盲区，Memory OS 用三种索引 + 加权融合（RRF）：

| 索引 | 工具/模型 | 擅长 | 盲区 |
|:---|:---|:---|:---|
| 向量检索 | LanceDB + embedding 模型（如 gemma:300m） | 语义相似、模糊表述 | 精确术语、专名 |
| 知识图谱 | 三元组（实体-关系-实体） | 关系推理、实体关联 | 语义泛化 |
| 关键词 | FTS5（如 `session_search`） | 精确词、代码、英文术语 | 同义改写 |

**RRF（Reciprocal Rank Fusion）**：把多路检索结果的排名融合为单一排序——不同索引的盲区互补，比单路检索显著更稳：

```text
score(d) = Σ 1 / (k + rank_i(d))      # k 通常取 60
```

> **实战**：Hermes 本地 Knowledge MCP（he-knowledge）即按此架构实现——LanceDB 向量 + 图谱三元组 + Router(RRF)，`ask` / `search` 两个入口对上层透明。

## 写侧：沉淀纪律（G4 Data Gate）

### 写入政策（Recall Policy）
- **何时写入 Long Memory**：当信息具有跨会话复用价值，且不依赖即时上下文时写入 Long Memory；否则保留在 Working Memory（STATE.md）直到任务结束。
- **对账查重**：写入前在 Long Memory 通过 `session_search` 检查是否已有相似条目；若已有冲突，先更新旧条目而非新增。
- **证据校验**：必须附带来源 URL、时间戳或可验证的实验数据；缺失来源的条目只能标记为 `hypothesis`，不进入 Long Memory。
- **格式与索引**：遵循 SKILL.md 中定义的 JSON schema（`type`, `content`, `source`, `timestamp`），写入后立即运行 `index_vault.py` 更新向量索引并跑 `kg_extract.py` 同步图谱。
- **审计记录**：每次写入写入动作记录在 `audit.log`，包括操作者（agent id）、时间、条目摘要、是否通过闸门。

### Recall Policy Queries
已在 `retrieval_recall_queries.json` 中定义了五个常用查询，用于在经验记忆层快速定位相关策略和实例。

进 Memory OS 的知识必须过闸门，否则沉淀=堆噪声：

| 闸门 | 检查 | 不过怎么办 |
|:---|:---|:---|
| 值得写吗 | 可复用性：还会用到吗？还是只对当前任务有意义？ | 只对当前任务有意义 → 留在会话 |
| 对账查重 | 库/记忆里已有类似条目？新旧冲突吗？ | 先更新旧条目，不新建重复 |
| 证据校验 | 结论有来源吗？可靠吗？（A 档证据：langextract + 验证模型复核） | 无来源 → 标记为假设，不沉淀为事实 |
| 格式规范 | 符合库的 schema / 模板吗？ | 按模板重写 |
| 索引同步 | 写入后向量索引 / 图谱索引更新了吗？ | 跑索引脚本（index_vault / kg_extract） |

## 复盘循环：每日回顾（Daily Review）

Memory OS 不是被动存储，需要主动复盘把「经验」沉淀为「资产」：

```text
每日会话结束
    ↓
回顾当日会话（session_search / 归档）
    ↓
提炼可复用经验 → 写入 vault 知识库
    ↓
对账查重（写前对账，6 动作）
    ↓
更新向量索引 + 图谱索引
    ↓
写「明日备忘」到 STATE.md
```

> **实战**：DailyReview cron（22:30）每日自动执行——回顾当日会话 → 写入 `areas/DailyReview/YYYY-MM-DD.md` → `index_vault.py` 向量索引（增量秒级）→ `kg_extract.py` 图谱索引（三元组/实体/文档计数）→ 明日备忘写入 STATE.md。运行 20+ 天零失败，图谱累计数万三元组。

## 记忆考核：Memory Exam（读侧的回归测试）

写侧有 G4 闸门，读侧也要有考卷。**`conventions/memory-exam.json` 是 31 题的 Hermes 记忆 mini 考核卷**，考纲提炼自 FP-AMB（MIT），语料换成本库真实记忆体系（memory 双库 / session_search / vault / skills）：

| 类别 | 考什么 | 失败信号 |
|:---|:---|:---|
| CAT1 单跳召回 | 凭据位置、项目路径等原子事实 | memory 条目缺失/检索不到 |
| CAT2 跨会话多跳 | 串联扒项目→借鉴→落地两跳以上 | session_search 覆盖不足 |
| CAT3 时间推理 | 日期差值、用户记错日期的纠正 | 条目没带时间戳 |
| CAT4 事实覆盖 | 旧规矩被新约定覆盖后是否还用旧的 | 新旧条目并存未清理 |
| CAT5 程序性规则 | 流程环节、前置检查动作 | 规则只说过一次没沉淀 |
| CAT6 对抗抗性 | 「你上次明明说…」型假引用、假前提 | 迎合用户转述而非以记忆为准 |
| CAT7 说话人归属 | 用户拍板 vs agent 决定不混淆 | agent 决定升格成用户约定 |
| CAT8 无中生有拒答 | 没存过的事说「没存过」，不编 | 顺嘴假装记得 |
| CAT9 来源裁决 | memory/vault/现场冲突时谁优先 | 静默选边不给理由 |
| CAT10 记忆驱动行为 | 记忆改变工具调用方式（deferred 流程、venv、全路径） | 记住了但行为不变 |

**判分三档**（继承 FP-AMB grading_mode）：exact=必须命中具体事实词；judgment=是非/拒答即答案；list=多子项全中 1.0、部分中 0.5。
**归因二分**（FP-AMB 最有价值的设计）：得 0 分先判是 RETRIEVAL_FAILURE（事实根本没被检索到→修写侧覆盖）还是 GENERATION_FAILURE（检索到了但没照做→修技能规则表述）。禁止用「答错」一个标签混过两种病。
**及格线**：≥25/31 且 CAT6/CAT8 各 ≥2/3——对抗抗性与拒答是信任底线，比召回错误更伤。

**何时跑**：① 大改 memory 内容或整理 vault 后；② 换主模型/改 fallback 链后（对照 self-update-pattern 失败基线）；③ 每月复盘时抽 CAT6/CAT8 各 1 题做哨兵。开新会话贴 prompt，对照 assertions/forbidden 判分。

## 与既有模式的关系

| 模式 | 关系 |
|:---|:---|
| `state-file-pattern` | Working Memory 的具体实现，其余四层的底座 |
| `self-update-pattern` | 更新后测试基线也是 Experience Memory 的一种 |
| `data-driven-optimization` | 复盘循环产出的数据 → 驱动技能迭代 |
| `skill-evolution` | 经验沉淀到一定程度 → G5 闸门决定是否固化为技能 |

## 落地清单

- [ ] 三层检索都有吗？（向量 / 图谱 / 关键词，至少两路再上 RRF）
- [ ] 写侧闸门过了一遍吗？（值得写 → 对账查重 → 证据校验）
- [ ] 写入后索引同步了吗？
- [ ] 有定期复盘循环吗？（日 / 周，把会话变成可复用资产）
- [ ] 证据层有校验机制吗？（AI 生成结论必须有来源 + 置信度，禁绝对化）
- [ ] 读过 Memory Exam 的归因二分吗？（检索失败修写侧，生成失败修规则，别混）

## References

- `conventions/memory-exam.json` – 31 题记忆考核卷（FP-AMB 考纲），判分细则见「记忆考核」节。
- `conventions/recall_schema.json` – 记忆条目 JSON schema（type/content/source/timestamp）。
- `conventions/retrieval_recall_queries.json` – 5 条经验记忆层召回基准查询（配套 test-prompts.json 的记忆反测条目）。

| ❌ 错误做法 | 后果 |
|:---|:---|
| 只加向量检索，没有写侧纪律 | 库里全是未经校验的噪声，检索越准伤害越大 |
| 有知识库没有复盘循环 | 知识只进不出，经验永远停留在会话里 |
| 把 RAG 当 Memory OS | 外部语料 ≠ 自身认知，答得再准也不积累 |
| 写入后不更新索引 | 库里查不到刚写的东西，用户以为没写 |
| 证据层缺失 | AI 生成的错误结论被当作事实反复引用 |
