---
name: compatibility-matrix
description: "兼容性矩阵 — Pattern × Hermes 版本 × 依赖能力"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
maturity: experimental
---

# 兼容性矩阵

> 每次 Hermes 发新版本，花 10 分钟更新这张表。

## Pattern × Hermes 版本

| Pattern | 最低版本 | 依赖能力 | 备注 |
|:---|:---:|:---|:---|
| state-file-pattern | v0.6+ | 文件读写 | 无特殊依赖 |
| error-compact-pattern | v0.6+ | 无 | 纯文本处理 |
| maker-checker | v0.6+ | delegate (子代理) | 需要 Hermes 子代理支持 |
| control-flow-separation | v0.6+ | 无 | 纯设计模式 |
| cron-job-pattern | v0.6+ | cronjob_manage | 需要 Hermes cron 调度器 |
| checkpoint-pattern | v0.6+ | 文件读写 + session | 会话恢复依赖 Hermes session 机制 |
| secret-management | v0.6+ | .env 支持 | 标准 dotenv |
| skill-evolution | v0.7+ | skill_manage | 需要 Hermes 技能管理工具 |
| anti-patterns | v0.6+ | 无 | 参考文档 |
| pattern-composition | v0.6+ | 无 | 参考文档 |
| data-driven-optimization | v0.7+ | session_search, memory | 需要会话搜索和记忆工具 |
| hermes-capability-map | v0.8+ | 无 | 能力映射参考表 |
| self-update-pattern | v0.7+ | terminal, git | 需要终端和 Git 操作 |
| memory-os-pattern | v0.8+ | memory, session_search | 需要记忆和会话搜索工具 |
| evolution-gate | v0.8+ | skill_manage, session_search | 需要技能管理和会话搜索 |
| budget-guardrail | v0.6+ | cronjob_manage | 新增，experimental |
| human-escalation | v0.6+ | delegate | 新增，experimental |
| multi-agent-isolation | v0.8+ | delegate, cronjob_manage | 新增，experimental |
| observability-trace | v0.6+ | 无 | 新增，experimental |
| data-retention-privacy | v0.6+ | 无 | 新增，experimental |

## 能力 × 版本对照

| Hermes 能力 | 引入版本 | 说明 |
|:---|:---:|:---|
| 文件读写 (read_file/write_file) | v0.6+ | 基础工具 |
| memory 工具 | v0.6+ | 持久化记忆 |
| cronjob_manage | v0.6+ | 定时任务调度 |
| delegate (子代理) | v0.7+ | 委托子代理执行 |
| skill_manage | v0.7+ | 技能管理 |
| session_search | v0.7+ | 会话历史搜索 |
| Monitor 原生监控 | v0.8+ | 哈希抑制，变了才烧 token |
| terminal | v0.6+ | Shell 命令执行 |

## 已知兼容性问题

| 问题 | 影响 Pattern | 解决方案 |
|:---|:---|:---|
| WSL 中 Obsidian CLI 需 cmd.exe | memory-os-pattern (索引更新) | 用 cmd.exe /c 调用 |
| Windows 文件锁语义不同 | multi-agent-isolation | 使用 msvcrt.locking |

---

> 更新方法：Hermes 发新版后，运行 `hermes --version` 确认版本号，检查 [CHANGELOG](https://github.com/NousResearch/hermes-agent/releases) 中新增能力，更新上表。
