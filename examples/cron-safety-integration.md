# Cron Safety Integration Example

## Goal

Wrap a scheduled Hermes task with maturity staging, state tracking, idempotency, compact errors, and hard stops.

## Recommended Layout

```text
reports/my-cron-job/
├── STATE.md
├── run.log
└── output/
```

## Before the Cron Runs

1. Confirm the task has passed the 4-condition test.
2. Start at L1 and define the promotion criteria before automation begins.
3. Create `STATE.md` from `templates/STATE.md.template`.
4. Define idempotency keys for every side effect.
5. Define the hard stops that force downgrade to L1.

## Runtime Flow

```text
cron trigger
  -> read STATE.md
  -> check maturity level
  -> check idempotency keys
  -> run deterministic collection steps
  -> call LLM only for judgment or synthesis
  -> run Maker/Checker gate when output quality matters
  -> write STATE.md after each side effect
  -> compact and classify errors
```

## Promotion Rules

| From | To | Requirement |
|:---|:---|:---|
| L1 | L2 | Reports are useful for at least one week |
| L2 | L3 | Human approvals are boring and consistently safe |
| L3 | L1 | Any hard stop, unsafe write, or repeated quality failure |

## Example Hard Stops

- Output path is outside the approved report directory.
- The source returns malformed data for more than half of items.
- The Checker score falls below the pass threshold twice in a row.
- `STATE.md` cannot be read or written.

## Compact Error Example

```text
[STEP_FAILED] write_state@2026-06-30T10:00:00+08:00
  Error: PermissionDenied - STATE.md could not be updated
  Hint: stop the loop and fix filesystem permissions
  Recoverable: NO
  Impact: idempotency cannot be guaranteed
```
