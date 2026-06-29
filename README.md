# Hermes Production Patterns

> **Production-grade engineering patterns for Hermes Agent**  
> Built on Harness Engineering methodology + Loop Engineering + 12-Factor Agents

把 Hermes Agent 从「聊天玩具」变成「7×24 小时自主工作的生产系统」所需的全部工程模式、公约和模板。

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

## 先决条件

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) v0.6+
- Obsidian（可选，用于知识管理）
- Git（用于版本化技能文件）

---

## 许可

MIT — 自由使用、修改、分发。

## 贡献

PR 和 Issues 都欢迎。核心原则：**每条模式必须在生产环境中验证过**，不接受纯理论设计。
