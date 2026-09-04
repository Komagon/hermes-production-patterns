---
maturity: experimental
name: {job-name}
description: 定时任务执行技能:有状态、幂等、可断点恢复
version: 1.0.0
triggers:
  - "scheduled: {job-name}"
tools:
  - terminal
  - read_file
  - write_file
  - process
mutating: true
---

# {Job Name}

## 执行协议

### Pre-flight(幂等闸门)
1. 读 STATE.md,取 Idempotency Keys
2. 生成本轮 key `{job}-{YYYYMMDD}-{batch}`
3. 若 key 已存在 → 本轮已处理,直接退出

### Execute(带检查点)
1. 执行主逻辑,每处理 `CHECKPOINT_EVERY` 个单元写回 STATE.md
2. 中间产物落盘 `reports/{date}/`,不占上下文

### Post-flight
1. 汇总结果 → 写 STATE.md(进度 + 本轮 key)
2. Monitor 记录成功;失败 → error_compact 压缩 → recovery 重试

## 陷阱
- 无幂等键直接跑 → 重跑即重复
- 失败静默 → Monitor 必须记录
- 错误全文进上下文 → 先压缩
