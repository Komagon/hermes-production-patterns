# STATE: daily-news-digest

## Schema
- **Version**: 1
- **Lock**: fcntl.flock (Unix) / msvcrt.locking (Windows)

## Current Run
- **Last run**: 2026-06-29T08:30:00+08:00
- **Status**: idle
- **Current batch**: 2026-06-29

## Progress
| Metric | Value |
|--------|-------|
| Sources fetched | 12 |
| Articles summarized | 8 |
| Failures (timeouts) | 1 |
| Skipped (duplicates) | 3 |

## Lessons Learned
- 2026-06-28: Source-X rate-limits at 10 req/min; space requests 5s apart
- 2026-06-29: Source-Y returns 504 under load; retry after 30s with exponential backoff

## Idempotency Keys
- 2026-06-29: article: uuid-a1b2c3
- 2026-06-29: article: uuid-d4e5f6
- 2026-06-29: batch: 2026-W26
