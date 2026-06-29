# Hermes Production Patterns

> **Production-grade engineering patterns for Hermes Agent**  
> Built on Harness Engineering methodology + Loop Engineering + 12-Factor Agents

把 Hermes Agent 从「聊天玩具」变成「7×24 小时自主工作的生产系统」所需的全部工程模式、公约和模板。

---

## 📖 简介 · Introduction

### 中文

**Hermes Production Patterns** 是一套面向 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的生产级工程模式集。

如果你已经装好了 Hermes，但发现：
- 不知道怎么写一个「靠谱」的技能（Skill）？
- Cron 任务跑着跑着就跑偏了，没人发现？
- Agent 输出质量不稳定，全靠肉眼审查？
- 多个任务的状态全靠脑子记，一重启就断片？
- 错误一出来就把上下文炸了，Agent 直接失焦？

这个项目就是为你准备的。

它不是什么「最佳实践」大合集——每一条模式都在真实的 7×24 运行环境中验证过，踩过坑，打过补丁，最终沉淀为可复用的工程公约。

### English

**Hermes Production Patterns** is a collection of production-grade engineering patterns for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

You've installed Hermes. Now what? If you're struggling with:

- Writing reliable Skills that don't drift over time
- Cron jobs that silently produce garbage
- Agent output quality that requires constant human babysitting
- Task state that evaporates the moment the session ends
- Error traces that flood the context window and derail the agent

This project is for you.

These aren't armchair best practices — every pattern here has been battle-tested in real 7×24 production runs, broken, fixed, and hardened into reusable conventions.

---

## 为什么需要这个项目

Hermes Agent 本身是一个强大的 Agent 框架，但社区里最缺的不是「怎么装 Hermes」，而是：

- 怎么让 Cron 任务不跑偏、不重复、不静默失败？
- 怎么从「手写提示词」进化到「设计自动化的 Loop」？
- Maker/Checker 分离怎么做？
- 多个 Agent 任务的状态怎么管理？
- 错误来了怎么处理，不让 Agent 失焦？
- 什么时候用 LLM，什么时候用确定性代码？

**这个项目回答的就是这些问题。**

---

## 项目结构

```
hermes-production-patterns/
├── AGENTS.md                    ← Harness 入口（AI 读我）
├── README.md
├── LICENSE                      ← MIT
├── config.yaml.example          ← Hermes 配置模板
│
├── conventions/                 ← 工程公约（核心产出）
│   ├── maker-checker.md         — 生成/验证双角色分离
│   ├── state-file-pattern.md    — STATE.md 跨运行状态管理
│   ├── control-flow-separation.md — 确定性 vs LLM 控制流
│   └── error-compact-pattern.md — 错误压缩与分类处理
│
├── templates/                   ← 可复用的文件模板
│   ├── SKILL.md.template
│   ├── STATE.md.template
│   └── AGENTS.md.template
│
├── patterns/                    ← 设计模式与方法论
│   ├── loop-engineering-14-steps.md
│   ├── 12-factor-agents-for-hermes.md
│   └── maturity-staging-l1-l2-l3.md
│
└── examples/                    ← 完整实战示例
    ├── daily-news-digest.md
    ├── maker-checker-article-pipeline.md
    └── cron-safety-integration.md
```

---

## 三大设计原则

### 1. Harness Engineering — 仓库即真理之源

整个项目本身就是 Harness 的落地案例。`AGENTS.md` 是 AI 读你的切入点，每个 `conventions/` 文件是可执行的技能，模板是可实例化的原型。

### 2. Loop Engineering — 从提示词到系统设计

不是手写每一条 Prompt，而是设计一个**自主循环**：接任务 → 派给 Agent → 验证结果 → 记录状态 → 决策下一步。

### 3. 12-Factor Agents — 可靠性的十二条守则

每一条原则对应一个具体的工程决策：
- Factor 2 → 写 SKILL.md 不写临时 Prompt
- Factor 5 → 用 STATE.md 统一状态
- Factor 7 → Maker/Checker 双角色
- Factor 8 → 控制流分离（代码 vs LLM）
- Factor 9 → 错误压缩不炸锅

---

## 快速开始

### 1. 把模式装进你的 Hermes

```bash
# clone 项目
git clone https://github.com/YOUR_USERNAME/hermes-production-patterns.git
cd hermes-production-patterns

# 把 conventions 复制到 Hermes skill 目录
cp conventions/* ~/AppData/Local/hermes/skills/conventions/
```

### 2. 用模板创建你的第一个技能

```bash
cp templates/SKILL.md.template ~/AppData/Local/hermes/skills/my-skill/SKILL.md
# 编辑填充你的技能逻辑
```

### 3. 为你的 Cron 任务添加 STATE.md

```bash
cp templates/STATE.md.template reports/my-cron-job/STATE.md
```

### 4. 参考 config.yaml.example 配置你的 Hermes

```bash
cp config.yaml.example ~/AppData/Local/hermes/config.yaml
# 替换 YOUR_xxx_HERE 为你的真实 API Key
```

---

## 核心概念速查

| 概念 | 文件 | 一句话 |
|:---|:---|:---|
| Maker/Checker | `conventions/maker-checker.md` | 写代码的 Agent 和验证的 Agent 不是同一个 |
| STATE.md | `conventions/state-file-pattern.md` | 每次运行先读状态，每步执行后写状态 |
| 控制流分离 | `conventions/control-flow-separation.md` | 能用代码的别用 LLM |
| 错误压缩 | `conventions/error-compact-pattern.md` | 错误信息压成一行，不让 Agent 失焦 |
| Loop Engineering | `patterns/loop-engineering-14-steps.md` | 先判断值不值得做，再设计怎么做 |
| 成熟度分级 | `patterns/maturity-staging-l1-l2-l3.md` | L1 只报告 → L2 辅助 → L3 自动 |
| 12-Factor 对照 | `patterns/12-factor-agents-for-hermes.md` | 12 条工程原则的 Hermes 落地映射 |

---

## 引用与致谢

### 核心框架

| 项目 | 说明 |
|:---|:---|
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) — Nous Research | 本项目所基于的自进化 AI Agent 框架 |
| [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) — HumanLayer | 12 条工程原则的原始定义，本项目的理论基石之一 |
| [Loop Engineering](https://x.com/0xCodez/status/2064374643729773029) — @0xCodez (Lev Deviatkin, Anthropic) | 14 步 Loop 路线图的原始 X Article，6000+ likes |
| [Harness Engineering](https://github.com/garrytan/harness-engineering) — garrytan | Agent 可靠执行方法论课程，本项目架构设计的指导思想 |

### 延伸参考

| 资源 | 说明 |
|:---|:---|
| [Addy Osmani — Loop Engineering](https://addyosmani.com/blog/loop-engineering/) | Loop Engineering 的体系化文章，与 14 步路线图互补 |
| [AlphaSignal — 4-Condition Test](https://alphasignalai.substack.com/p/most-developers-do-not-need-agent) | 「大部分开发者还不该用 Agent Loop」—— 前置判断标准 |
| [Anthropic — Recursive Self-Improvement](https://www.anthropic.com/institute/recursive-self-improvement) | Agent 自我改进的边界研究 |
| [Geoffrey Huntley — Agentic Loop Failures](https://ghuntley.com/loop/) | 生产环境 Agent Loop 失败的案例研究 |
| [CB Insights — AI Agent Bible](https://www.cbinsights.com/research/report/ai-agents-bible/) | AI Agent 产业全景报告（69页） |
| [Google Cloud — AI Agent Trends 2026](https://cloud.google.com/resources/content/ai-agent-trends-2026) | 企业 Agent 部署趋势报告 |

### 本项目中的关联文档

| 文件 | 引用来源 |
|:---|:---|
| `conventions/maker-checker.md` | 12-Factor Agents Factor 7 + Loop Engineering Step 9 |
| `conventions/state-file-pattern.md` | 12-Factor Agents Factor 5 + Loop Engineering Step 10 |
| `conventions/control-flow-separation.md` | 12-Factor Agents Factor 8 |
| `conventions/error-compact-pattern.md` | 12-Factor Agents Factor 9 |
| `patterns/loop-engineering-14-steps.md` | @0xCodez Loop Engineering X Article |
| `patterns/12-factor-agents-for-hermes.md` | HumanLayer 12-Factor Agents |
| `patterns/maturity-staging-l1-l2-l3.md` | cron-scheduler + task-safety 实践经验 |

---

## 先决条件

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) v0.6+
- Obsidian（可选，用于知识管理）
- Git（用于版本化技能文件）

---

## 许可

MIT — 自由使用、修改、分发。

## 贡献

PR 和 Issues 都欢迎。核心原则：**每条模式必须在生产环境中验证过**，不接受纯理论设计。
