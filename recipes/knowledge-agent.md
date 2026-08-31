# Recipe: Knowledge Agent — 知识库问答与沉淀 Agent

## Problem

知识问答类 Agent 的通病:回答时把整个知识库塞进上下文(贵且慢),或者记忆只进不出(越积越杂,召回越来越不准)。需要「写有纪律、查有查询、定期维护」的完整闭环。

## Architecture

```text
写入路径:
  新知识产生(会话/任务/复盘)
     ↓
  写入三问过滤(一周后有用?有证据?可召回?)
     ↓
  按层入库(long-term / experience)+ evidence 来源
     ↓
  登记召回查询词

查询路径:
  用户提问
     ↓
  预定义查询按层召回(top-k,带来源)
     ↓
  生成回答(引用来源条目)
     ↓
  来源失效 → 标记 stale → 进复盘淘汰清单
```

## Patterns Used

| Pattern | 公约 |
|:---|:---|
| Memory OS | `conventions/memory-os-pattern.md`(五层+检索+写侧) |
| 状态管理 | `conventions/state-file-pattern.md` |
| 数据驱动 | `conventions/data-driven-optimization.md`(复盘改进) |

对应 Starter Kit:`starter-kits/memory-agent/`。

## Installation

```bash
cp -r starter-kits/memory-agent ~/knowledge-agent
cd ~/knowledge-agent
```

## Configuration

1. 五层目录初始化,`.gitkeep` 占位
2. `retrieval/QUERIES.md`:按业务定义 5-10 个预定义查询
3. 写侧策略挂进技能:任何长期写入先过三问
4. 复盘周期:每周一次(REVIEW.md 清单)

## Run

```text
问答:召回 → 引用条目 ID 回答 → 无证据时明说「知识库没有」
沉淀:任务结束触发写入流程,不随手倾倒
复盘:每周跑 REVIEW 清单,输出淘汰/提炼/校正三清单
```

## Failure Modes

| 失败 | 症状 | 防护 |
|:---|:---|:---|
| 记忆腐烂 | 旧知识失效仍被召回 | 复盘淘汰 + 召回时校验来源 |
| 无证知识 | 长期层混入无来源断言 | 写入三问 + evidence 必填 |
| 检索污染 | 召回一堆无关条目 | 限定层 + top-k + 查询词对齐 |
| 摘要当证据 | 链条断裂 | 红线:摘要不作为 evidence 引用 |

## Recovery

- 召回质量下降:检查最近写入批次的查询词登记,补齐后重测
- 误淘汰:复盘操作走 git(记忆文件可追溯可恢复)
- 知识库损坏:五层目录进 git,恢复最近提交

## Metrics

- 召回命中率:被采纳条目 / 召回条目(低于 30% 说明查询词需优化)
- 淘汰率:每次复盘淘汰条目占比(长期为 0 说明复盘没执行)
- 无证回答率:无证据支撑的回答占比(目标 0)
- 上下文成本:平均召回条目数(应稳定,不随库增长而增长)
