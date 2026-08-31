# 🟣 Memory Stack

> 跨会话积累能力的官方组合:分层记忆、证据支撑、按需召回、定期复盘。

## 组合

```text
Memory OS(五层)
+
Evidence
+
Retrieval
+
Daily Review
```

## 对应公约

| Pattern | 公约 |
|:---|:---|
| 五层记忆 | `conventions/memory-os-pattern.md` |
| 状态管理 | `conventions/state-file-pattern.md`(working 层基础) |
| 写侧纪律 | `conventions/memory-os-pattern.md`(§写侧) |

## 什么时候用

- Agent 需要记住跨会话的经验与知识
- 同类任务重复出现,希望越跑越好
- 出现过「上次踩过的坑这次又踩」

## 关键设计

```text
写入: 三问过滤(一周后有用?有证据?可召回?)
存放: context / working / long-term / experience / evidence 五层
召回: 预定义查询按层取,不整层倾倒
维护: 定期复盘 → 提炼 / 淘汰 / 校正
```

## 判定红线

- 长期层条目必须有 evidence 来源
- 摘要不当证据
- 无查询对应的条目不写入长期层

## 落地方式

直接复制 `starter-kits/memory-agent/`。
