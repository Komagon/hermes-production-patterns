# 12-Factor Agents — Hermes 落地映射

> **来源**: [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)  
> **关联**: conventions/ 全部四个文件

## 核心哲学

> *"生产环境中的大多数 AI Agent 不是完全自主的循环。它们是确定性代码为主、战略性点缀 LLM 步骤的软件。"*

## 12 条原则的 Hermes 落地

| # | 原则 | 本项目的对应 | Hermes 中的实现方式 |
|:---:|:---|:---|:---|
| 1 | NL → Tool Calls | Agent 原生能力 | Hermes 工具的 NL 描述直接映射 |
| 2 | Own your prompts | `templates/SKILL.md.template` | SKILL.md 是结构化、版本化的 Prompt |
| 3 | Own your context | Harness Engineering 课程 | Context Engineering 方法论 |
| 4 | Tools = structured outputs | `config.yaml.example` MCP 配置 | MCP 协议天然支持 |
| 5 | **Unify state** | `conventions/state-file-pattern.md` | STATE.md 跨运行管理 |
| 6 | Lifecycle APIs | `examples/` | Cron 创建/暂停/移除 |
| 7 | **Human-in-loop** | `conventions/maker-checker.md` | Maker/Checker 双角色 |
| 8 | **Control flow** | `conventions/control-flow-separation.md` | 确定性 vs LLM 路由 |
| 9 | **Compact errors** | `conventions/error-compact-pattern.md` | 错误压缩+分类桶 |
| 10 | Small focused | `templates/SKILL.md.template` | 每个 Skill 只干一件事 |
| 11 | Trigger anywhere | `examples/` | Cron + Webhook |
| 12 | Stateless reducer | STATE.md | 输入状态+事件→新状态 |
