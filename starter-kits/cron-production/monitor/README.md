# Monitor

记录任务成败与告警,失败必须可观测。

- `runs.log` — 每轮运行记录(id/date/status/duration)
- `alerts.log` — 失败告警与升级记录
- 接入告警渠道:Telegram / 本地通知 / 状态页

规则:
- 成功/失败都要落 run 记录(不是只记失败)
- 失败必须产生可检索痕迹(alert + compact error)
- 连续失败 N 次 → 升级人工(停止自动重试)
