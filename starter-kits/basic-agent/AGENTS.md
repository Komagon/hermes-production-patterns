# {project-name}

## 项目概述

{一句话描述:这个 Agent 负责什么任务}

## 核心约定(Control Flow Separation)

- 确定性步骤(数据清洗、聚合、换算、格式化)→ 必须写脚本执行
- LLM 只负责需要判断的部分(语义理解、方案选择、文案生成)
- 每次运行先读 `STATE.md`,完成后写回

## 目录结构

```
{project-name}/
├── AGENTS.md          ← AI 读我(本文件)
├── SKILL.md           ← 任务技能定义
├── STATE.md           ← 跨运行状态
├── scripts/           ← 确定性逻辑脚本
└── reports/           ← 输出与中间结果
```
