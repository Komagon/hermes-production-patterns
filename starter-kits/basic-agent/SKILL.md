---
name: {my-skill}
description: 一句话描述这个技能做什么
version: 1.0.0
triggers:
  - "触发这个技能的用户话术"
tools:
  - terminal
  - read_file
  - write_file
mutating: true
---

# {My Skill}

> 简明扼要的技能说明

## 核心逻辑

### 1. 输入处理
{描述需要什么输入,从哪里获取}

### 2. 执行
{具体执行步骤,按序编号;确定性步骤标注 script 交给脚本}

### 3. 验证
{如何验证输出质量,输出是否满足输入要求}

## 状态契约(STATE.md)

- 读取:每次运行先读 STATE.md 的 Progress/Last run
- 写入:每完成一步写回进度与结果摘要

## 陷阱

- 用 LLM 心算确定性计算 → 写脚本
- 跑完不写 STATE.md → 断点丢失
