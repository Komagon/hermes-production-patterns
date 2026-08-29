# Loop Engineering: 从 Prompter 到 Loop Designer 的 14 步

> **来源**: @0xCodez (Lev Deviatkin, Anthropic) X Article  
> **补充**: Addy Osmani Loop Engineering + AlphaSignal 4-Condition Test  
> **关联**: conventions/state-file-pattern.md, conventions/control-flow-separation.md

## 核心论点

杠杆已经从「会写提示词的人」转移到了「设计提示系统的人」。

## 14 步路线图

### Tier 1：先判断值不值得做（步骤 1-4）

**4-Condition Test** — 四个条件全部满足才值得搭 Loop：

| # | 条件 | 含义 |
|:---|:---|:---|
| 1 | Task Repeats | 至少每周重复一次 |
| 2 | Verification is Automated | 有自动测试/linter/类型检查 |
| 3 | Token Budget Flexibility | 能承受探索性重试 |
| 4 | Agent Has Senior Tools | 有日志、复现环境、运行环境 |

### Tier 2：五个积木（步骤 5-9）

| # | 积木 | 说明 | 本项目的对应 |
|:---|:---|:---|:---:|
| 5 | Automations | 定时/循环触发器 | examples/ |
| 6 | Worktrees | Git 并行隔离 | — |
| 7 | Skills | SKILL.md 结构化上下文 | templates/SKILL.md.template |
| 8 | Connectors | MCP 外部集成 | config.yaml.example |
| 9 | Sub-Agents | Maker/Checker 分离 | conventions/maker-checker.md |

### Tier 3：从小开始（步骤 10-14）

| # | 步骤 | 本项目的对应 |
|:---|:---|:---:|
| 10 | STATE.md | conventions/state-file-pattern.md |
| 11 | 手动跑通 → 写成 Skill | templates/ |
| 12 | 包进 Loop | examples/ |
| 13 | Gates | conventions/maker-checker.md |
| 14 | Hard Stops | conventions/error-compact-pattern.md |

## 关键洞察

**在任何 Loop 中，Verifier 是瓶颈，不是 Generator。** 一个弱 Verifier 的 Loop 不会「大声失败」——它会自信地生产垃圾，重复几百次。

## 参考

- 原始 X Article: <https://x.com/0xCodez/status/2064374643729773029>
- Addy Osmani Loop Engineering: <https://addyosmani.com/blog/loop-engineering/>
