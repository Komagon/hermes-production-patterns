# Hermes Production Patterns

## 项目概述

此仓库包含一套生产级的 Hermes Agent 工程模式、公约和模板。目标是帮助开发者从「手写提示词」进化到「设计自主运行的 Agent 系统」。

## 核心能力

| 能力 | 入口点 |
|:---|:---|
| Maker/Checker 分离 | `conventions/maker-checker.md` |
| 状态文件管理 | `conventions/state-file-pattern.md` |
| 控制流分离 | `conventions/control-flow-separation.md` |
| 错误压缩与自愈 | `conventions/error-compact-pattern.md` |
| 技能进化 | `conventions/skill-evolution.md` |
| 💡 反面模式 | `conventions/anti-patterns.md` |
| 🧩 模式组合指南 | `conventions/pattern-composition.md` |
| 📐 状态文件 Schema | `conventions/state-schema.json` |
| 模板 | `templates/` |
| 设计模式 | `patterns/` |
| 实战示例 | `examples/` |

## 你的角色

- **阅读 `conventions/` 理解工程模式** — 这些是可执行的技能文件
- **阅读 `patterns/` 理解方法论** — 这些是设计决策的上下文
- **使用 `templates/` 快速起步** — 填空即用

## 约束

- 不要修改 `conventions/` 文件的内容来绕过设计意图
- 所有 Cron 任务必须经过 L1→L2→L3 成熟度分级
- Maker 和 Checker 必须是独立的 Agent 实例
- 错误信息必须压缩后写入上下文
