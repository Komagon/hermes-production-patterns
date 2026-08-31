# Production Stacks — 官方推荐组合

> Opinionated Defaults:官方明确告诉你「这种场景推荐这样组合」。
> 每个 Stack 是一组公约的组合套餐,配套一个可直接复制的 Starter Kit。

## 五个官方 Stack

| Stack | 组合 | 适用 | 落地 Kit |
|:---|:---|:---|:---|
| 🟢 [Starter](starter.md) | SKILL + STATE + Control Flow | 起步,单任务 | basic-agent |
| 🟡 [Reliable Automation](reliable-automation.md) | STATE + Cron + Error Compact + Checkpoint | 无人值守定时 | cron-production |
| 🔵 [Quality](quality.md) | Maker + Checker + Red Flags + Regression | 产出外发 | maker-checker |
| 🟣 [Memory](memory.md) | Memory OS + Evidence + Retrieval + Review | 跨会话积累 | memory-agent |
| 🔴 [Evolution](evolution.md) | Metrics + Gate + Regression + Deploy/Rollback | 持续改进 | self-evolving-agent |

## 叠加原则

- Stack 从下往上叠加:🟢 是基础,叠 🔵/🟣 前先有 🟢
- 不要一次叠全部——每叠一层,先跑稳一个周期
- 对应成熟度:🟢≈L1,🟡/🔵≈L2,🟣/🔴≈L3
