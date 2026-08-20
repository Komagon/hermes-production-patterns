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

## 反模式

| ❌ 错误做法 | 后果 |
|:---|:---|
| 只加向量检索，没有写侧纪律 | 库里全是未经校验的噪声，检索越准伤害越大 |
| 有知识库没有复盘循环 | 知识只进不出，经验永远停留在会话里 |
| 把 RAG 当 Memory OS | 外部语料 ≠ 自身认知，答得再准也不积累 |
| 写入后不更新索引 | 库里查不到刚写的东西，用户以为没写 |
| 证据层缺失 | AI 生成的错误结论被当作事实反复引用 |
