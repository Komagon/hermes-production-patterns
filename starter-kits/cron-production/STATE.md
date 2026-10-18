# STATE: {job-name}

## Current Run
- **Last run**: {ISO timestamp}
- **Status**: idle
- **Current batch**: {batch_id}

## Idempotency Keys
<!-- 格式：YYYY-MM-DD: step: key。每完成一步追加一行，重跑时先查这里防止重复 -->

## Progress

| Metric | Value |
|:---|:---|
| processed | 0 |
| total | 0 |
| last_checkpoint | {offset} |

## Recovery
- **Last failure**: {compact error summary}
- **Retry count**: 0
- **Next action**: —

## Lessons Learned
<!-- 每次跑完写一条：踩了什么坑、下次怎么避免。新任务可以为空 -->
