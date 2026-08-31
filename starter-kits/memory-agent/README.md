# Memory Agent Starter Kit

> 五层记忆 + 三层检索 + 写侧纪律的完整记忆体系骨架。
> 适合:长期运行的 Agent / 需要跨会话积累经验的任务 / 知识沉淀。

## Patterns Used

| Pattern | 文件 | 作用 |
|:---|:---|:---|
| Memory OS | `memory/` 五层目录 | context/working/long-term/experience/evidence 分层存放 |
| Retrieval | `retrieval/` | 写入有纪律,检索有查询,不做「全部塞上下文」 |
| Write Policy | `write-policy/WRITE-POLICY.md` | 什么该写、写到哪层、何时淘汰 |
| Daily Review | `write-policy/REVIEW.md` | 定期复盘:经验层提炼、过期清理 |

## 目录结构

```text
memory-agent/
├── memory/
│   ├── context/       # 当前会话上下文(易变,可丢弃)
│   ├── working/       # 当前任务工作集(任务结束归档或清理)
│   ├── long-term/     # 沉淀的知识(结构化笔记)
│   ├── experience/    # 失败与成功经验(含反例)
│   └── evidence/      # 每条长期记忆的来源证据
├── retrieval/
│   ├── QUERIES.md     # 预定义召回查询清单
│   └── recall_schema.json
├── write-policy/
│   ├── WRITE-POLICY.md
│   └── REVIEW.md
└── README.md
```

## 写侧纪律(核心)

```text
写入前问三个问题:
1. 这条信息一周后还有用吗?      没用 → context/working,不进 long-term
2. 它有来源证据吗?             没有 → 不写入长期层
3. 它能被一条查询召回吗?        不能 → 改写成可检索的形式再写
```

## 检索纪律

- 用 `retrieval/QUERIES.md` 的预定义查询按需召回,不整层倾倒进上下文
- 召回结果附带来源;来源失效的条目降权或清除
- 每层只召回与当前任务相关的条目(查询词 + 层级过滤)

## 安装

```bash
cp -r starter-kits/memory-agent ~/my-memory-agent
cd ~/my-memory-agent
# 1. 按业务改写 retrieval/QUERIES.md 的查询清单
# 2. 把 WRITE-POLICY.md 挂进你的 SKILL.md 写入流程
# 3. 每日/每周任务末尾挂 REVIEW.md 复盘
```

## 验证

- [ ] 写入 long-term 的每条记忆在 evidence/ 有对应条目
- [ ] 召回走查询而非全量倾倒,上下文不膨胀
- [ ] 复盘时淘汰过期条目,长期层不无限增长
- [ ] 经验层包含失败案例,不只记成功
