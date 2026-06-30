# Daily News Digest Example

## Goal

Run a daily digest loop that collects candidate links, filters duplicates, drafts a concise summary, and publishes only after verification.

## Maturity Level

Start at **L1** for one to two weeks. The loop reads sources and writes a report, but a human decides whether anything is published. Promote to **L2** only after the report format and duplicate checks are stable.

## Files

```text
reports/daily-news-digest/
├── STATE.md
├── candidates.json
└── digest.md
```

## Loop

1. Read `reports/daily-news-digest/STATE.md`.
2. Fetch source feeds with deterministic code.
3. Build an idempotency key from `{source}:{url}:{published_date}`.
4. Skip candidates already listed in `STATE.md`.
5. Ask the Maker agent to draft the digest from the remaining candidates.
6. Ask the Checker agent to score the draft for factuality, usefulness, source coverage, mobile readability, and repetition.
7. Publish or hold based on the maturity level and Checker result.
8. Update `STATE.md` with counts, skipped items, and lessons learned.

## Gates

| Gate | Pass Condition |
|:---|:---|
| Duplicate check | No repeated idempotency keys |
| Source coverage | Every item has a source URL and date |
| Checker score | At least 40 out of 50 |
| Hard stop | Authentication, corrupted config, or empty source set |

## Failure Handling

Use the compact error pattern before adding failures to context:

```text
[STEP_FAILED] fetch_feeds@2026-06-30T10:00:00+08:00
  Error: Timeout - source feed did not respond in 10s
  Hint: retry with exponential backoff
  Recoverable: YES
  Impact: one source skipped, digest can continue
```
