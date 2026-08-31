# STATE: {job-name}

## Current Run
- **Last run**: {ISO timestamp}
- **Status**: idle
- **Current batch**: {batch_id}

## Idempotency Keys

| Key | Date | Status |
|:---|:---|:---|
| {job}-{date}-001 | {date} | done |

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
