# Pattern 兼容性矩阵 — Compatibility Matrix

> 每个 Pattern 对 Hermes 能力版本的要求与成熟度状态。CLI 与审计工具引用本文件作为判定依据。
> 数据文件:`compatibility/hermes-versions.yaml`(机器可读);本页是人读版。

## 矩阵总览

| Pattern | Hermes 要求 | 状态 | 依赖的原生能力 |
|:---|:---|:---|:---|
| State File | 任意版本 | Stable | 文件读写 |
| Control Flow Separation | 任意版本 | Stable | 脚本执行 |
| Error Compact | 任意版本 | Stable | 上下文管理 |
| Checkpoint | 任意版本 | Stable | 文件读写 |
| Maker/Checker | ≥ v0.20 | Stable | delegate 子代理(独立实例)+ schema 契约 |
| Cron Job | ≥ v0.20 | Stable | 原生 cron + Monitor(哈希抑制) |
| Monitor(原生) | ≥ v0.20 | Stable | cron monitor 字段 |
| Skill Evolution | ≥ v0.15 | Stable | skills 目录热加载 |
| Secret Management | 任意版本 | Stable | .env |
| Memory OS | 版本相关 | Experimental | 文件系统即可运行;向量/图谱层视后端而定 |
| Evolution Gate | ≥ supported baseline | Stable | 依赖 Regression 数据,不依赖特定原生能力 |
| Data-Driven Optimization | 任意版本 | Stable | 运行日志留存 |
| Self-Update | ≥ v0.20 | Stable | git autostash 行为 |

## 状态定义

| 状态 | 含义 |
|:---|:---|
| Stable | 在真实 7x24 环境验证过,可生产使用 |
| Experimental | 可用,但接口/行为可能变化,需自行评估 |
| Deprecated | 不建议新项目采用(保留仅为存量迁移) |

## 使用规则

- 选 Stack/Kit 前先核对矩阵;Cron/Maker-Checker 类模式在旧版 Hermes 上需手动替代方案(外部 crontab + 双会话)
- `Experimental` 模式进生产前,先在非关键任务试运行一个完整周期
- Hermes 版本升级后,重跑 `audit/` 检查单确认兼容性仍然成立
