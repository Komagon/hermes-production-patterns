# 示例：Cron + Safety 集成

> 演示 cron-scheduler + task-safety 的完整配合

## 新任务创建流程

```bash
# 1. 创建 Cron 任务（默认 L1）
cronjob action=create \
  name="weekly-report" \
  schedule="0 9 * * 1" \
  prompt="生成上周工作总结" \
  maturity=L1

# 2. 先跑 Preflight Checklist
#    [ ] Denylist 合规
#    [ ] 范围约束
#    [ ] Kill switch
#    [ ] Token 预算
#    [ ] Idempotency

# 3. 手动审查第一次输出
#    确认格式正确、数据准确、无意外副作用

# 4. 稳定后升级到 L2
cronjob action=update job_id=<id> maturity=L2

# 5. L2 稳定 2 周后升级到 L3
cronjob action=update job_id=<id> maturity=L3
```

## STATE.md + Safety 状态

```markdown
# STATE: weekly-report

## Current Run
- Status: running (L2)
- Batch: 2026-W26

## Safety
- Maturity: L2
- Last preflight: 2026-06-01 (PASS)
- Denylist hits: 0
- Human approvals pending: 1

## Idempotency
- 2026-W25: weekly-report-W25 (✅ issued)
- 2026-W26: (in progress)
```

## 降级触发条件

| 事件 | 动作 |
|:---|:---|
| 输出格式错误 | 自动重试 1 次 → 仍错则降 L1 |
| 触碰 Denylist | 立即降 L1 + 通知人类 |
| 连续 2 次失败 | 降 L1 + 暂停任务 |
| Token 超预算 2x | 降 L1 + 报告用量 |
