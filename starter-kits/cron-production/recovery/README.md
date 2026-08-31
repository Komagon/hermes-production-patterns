# Recovery

断点恢复 + 错误压缩。中断后从这里回到任务。

## 断点恢复规则
- 读 STATE.md 的 last_checkpoint / Idempotency Keys
- 从最后完成单元继续,已完成的幂等跳过
- 禁止从头重跑

## 错误压缩规则(error_compact.py)
- 原始错误 → 压缩为:错误分类 / 关键堆栈 / 影响范围 / 恢复建议
- 压缩后的摘要才允许进上下文/STATE.md
- 禁止 2000 行原始日志全文灌入
