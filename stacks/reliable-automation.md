# 🟡 Reliable Automation Stack

> 无人值守运行的官方组合:状态、调度、错误压缩、断点恢复四位一体。

## 组合

```text
STATE
+
Cron
+
Error Compact
+
Checkpoint
```

## 对应公约

| Pattern | 公约 |
|:---|:---|
| 状态管理 | `conventions/state-file-pattern.md` |
| Cron 设计 | `conventions/cron-job-pattern.md` |
| 错误压缩 | `conventions/error-compact-pattern.md` |
| 检查点 | `conventions/checkpoint-pattern.md` |

## 什么时候用

- cron 定时任务,没人盯着跑
- 任务中途失败代价高(重复执行、脏数据)
- 对应成熟度 L2(辅助执行)

## 关键设计

```text
Pre-flight   读 STATE → 幂等查重
Execute      每步写 STATE(检查点)
Post-flight  结果汇总 → Monitor 记录 → 失败进 recovery
```

## 什么时候升级

- 失败代价高到「错了不能发出去」→ 叠加 🔵 Quality Stack
- 需要跨运行积累经验 → 叠加 🟣 Memory Stack

## 落地方式

直接复制 `starter-kits/cron-production/`。
