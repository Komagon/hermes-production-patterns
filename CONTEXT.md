# Hermes Production Patterns - 项目上下文

> 初次建立于：2026-07-05
> 基于 domain-glossary 技能

## 一句话描述

把 Hermes Agent 从「聊天玩具」变成「7×24 小时自主工作的生产系统」所需的工程模式、公约和模板集。

## 核心领域概念

| 术语 | 定义 | 别名 | 代码中的体现 |
|:--|:--|:--|:--|
| **Maker** | 生成内容/执行任务的 Agent 角色 | 执行者 | `examples/daily-news-digest/SKILL.md` |
| **Checker** | 验证 Maker 输出质量的独立 Agent 角色 | 验证者 | `conventions/maker-checker.md` |
| **Scheduler** | 定时触发、读取状态、决定运行节奏的组件 | 调度器 | `ARCHITECTURE.md` 组件图 |
| **State Store** | 持久化运行状态、进度、幂等键的存储 | 状态存储 | `STATE.md`, `conventions/state-file-pattern.md` |
| **Notifier** | 输出结果分发：报告/告警/存档 | 通知器 | `ARCHITECTURE.md` 组件图 |
| **Harness Engineering** | Agent 可靠执行的方法论体系 | — | `README.md` 设计原则 1 |
| **Loop Engineering** | 设计自主循环而非手写每一条 Prompt 的方法论 | — | `patterns/loop-engineering-14-steps.md` |
| **12-Factor Agents** | Agent 系统的 12 条工程原则 | — | `patterns/12-factor-agents-for-hermes.md` |
| **Maturity Staging** | L1(仅报告) → L2(辅助) → L3(自动) 三级成熟度 | 成熟度分级 | `patterns/maturity-staging-l1-l2-l3.md` |
| **Control Flow Separation** | 确定性代码控制流 vs LLM 控制流的分离原则 | 控制流分离 | `conventions/control-flow-separation.md` |
| **Error Compression** | 将错误信息压缩为单行/单分类的工程模式 | 错误压缩 | `conventions/error-compact-pattern.md` |
| **Skill Evolution** | 技能从简单到复杂的演进方法论 | 技能进化 | `conventions/skill-evolution.md` |
| **Idempotency** | 通过 STATE.md 中的幂等键防止重复处理 | 幂等性 | `ARCHITECTURE.md` 数据流 Step 2 |
| **Maker/Checker Loop** | MAKER→CHECKER→PASS/FAIL→重试(最多3轮)的验证循环 | 双角色循环 | `conventions/maker-checker.md` |

## 架构决策记录

### ADR-001：Maker 和 Checker 必须独立 Agent 会话
- **背景**：同一上下文中自我验证会导致 checker 为 maker 的错误找理由
- **方案**：Maker 和 Checker 使用不同的 Agent 实例（可不同模型），通过 STATE.md 传数据
- **后果**：+1 次 API 调用，但质量提升显著；建议 Maker 用强推理模型，Checker 用够用就行

### ADR-002：STATE.md 使用文件锁保证原子写入
- **背景**：多个 Cron 任务可能同时写 STATE.md，导致状态损坏
- **方案**：`scripts/atomic_state_write.py` 用文件锁 + 临时文件 + rename 策略
- **后果**：写性能降低但安全——STATE.md 损坏的后果远大于写入延迟

### ADR-003：成熟度分级 L1→L2→L3
- **背景**：新 Cron 任务直接跑 L3 自动模式风险太高
- **方案**：L1 只报告不执行 → L2 人类辅助决策 → L3 自动执行
- **后果**：任务上线慢但稳，至少运行 3 次无修正需求才升级

## 项目约定

- **命名规范**：Markdown 文件名用 kebab-case（`maker-checker.md`）
- **语言**：中文为主（README 中英文双版），英文术语首次出现需中文释义
- **目录结构**：
  - `conventions/` = 可执行的工程模式（核心产出）
  - `templates/` = 可填空的模板
  - `patterns/` = 设计方法论（不可直接执行，是上下文）
  - `examples/` = 完整实战示例
  - `scripts/` = 工具脚本（确定性代码，不用 LLM）
  - `.github/workflows/` = CI/CD
- **CI 流程**：lint → link-check → smoke-test 三层
- **版本发布**：npm 包（`@komagon/hermes-production-patterns`），见 `package.json`
