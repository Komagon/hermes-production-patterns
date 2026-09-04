#!/usr/bin/env python3
"""Minimal demo: STATE.md + Cron lifecycle.

Simulates a cron task that reads/writes STATE.md, demonstrating:
- Read Before Run
- Write After Every Step
- Idempotency (skip completed batches)
- Error compression
- Silent failure prevention

Usage:
    python demo_cron.py [state_file]

Default state file: ./reports/STATE.md
"""

import os
import sys
import random
import re
from datetime import datetime, timezone

# Default state file path
DEFAULT_STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "STATE.md")

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

# --- Simulated data sources ---
SIMULATED_SOURCES = ["news-feed-A", "news-feed-B", "blog-rss", "github-trending", "arxiv-cs"]


def read_state(path: str) -> dict:
    """Read current STATE.md and parse key fields."""
    if not os.path.exists(path):
        return {"status": "new", "last_run": None, "completed_batches": [], "idempotency_keys": []}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
    last_run_match = re.search(r"\*\*Last run\*\*:\s*(.+)", content)
    batch_match = re.search(r"\*\*Current batch\*\*:\s*(.+)", content)

    # Parse idempotency keys
    keys = []
    in_keys = False
    for line in content.split("\n"):
        if "Idempotency Keys" in line:
            in_keys = True
            continue
        if in_keys and line.startswith("- "):
            keys.append(line[2:].strip())
        elif in_keys and line.startswith("## ") and "Idempotency" not in line:
            in_keys = False

    return {
        "status": status_match.group(1) if status_match else "unknown",
        "last_run": last_run_match.group(1).strip() if last_run_match else None,
        "current_batch": batch_match.group(1).strip() if batch_match else None,
        "idempotency_keys": keys,
    }


def is_already_done(state: dict, batch: str) -> bool:
    """Check if today's batch is already in idempotency keys (idempotent skip)."""
    return any(batch in key for key in state.get("idempotency_keys", []))


def simulate_task() -> dict:
    """Simulate fetching from multiple sources. Returns results dict."""
    results = {"fetched": 0, "summarized": 0, "failed": 0, "skipped": 0, "errors": []}

    for source in SIMULATED_SOURCES:
        # 80% chance success, 15% timeout, 5% rate-limit
        roll = random.random()
        if roll < 0.80:
            articles = random.randint(1, 5)
            results["fetched"] += articles
            results["summarized"] += articles
            print(f"  ✅ {source}: fetched {articles} articles")
        elif roll < 0.95:
            results["failed"] += 1
            error_msg = f"{source}: timeout after 30s"
            results["errors"].append(error_msg)
            print(f"  ❌ {error_msg}")
        else:
            results["skipped"] += 1
            print(f"  ⏭️  {source}: rate-limited, skipped")

    return results


def compress_error(errors: list[str]) -> str:
    """Compress errors into structured summary (error-compact-pattern)."""
    if not errors:
        return "None"
    return " | ".join(
        f"[STEP_FAILED] {e.split(':')[0].strip()}: {e.split(':')[1].strip() if ':' in e else e}"
        for e in errors
    )


def write_state(path: str, state: dict, results: dict, batch: str):
    """Write updated STATE.md (Write After Every Step)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    status = "idle" if results["failed"] == 0 else "paused"
    error_summary = compress_error(results.get("errors", []))

    content = f"""# STATE: demo-cron

## Schema
- **Version**: 1

## Current Run
- **Last run**: {NOW}
- **Status**: {status}
- **Current batch**: {batch}

## Progress

| Metric | Value |
|--------|-------|
| Sources fetched | {results['fetched']} |
| Articles summarized | {results['summarized']} |
| Failures | {results['failed']} |
| Skipped (rate-limited) | {results['skipped']} |

## Lessons Learned
- {NOW}: Demo run — {results['summarized']} articles, {results['failed']} failures
{f"- {NOW}: Errors: {error_summary}" if results['errors'] else ""}

## Idempotency Keys
- {batch}: batch:{batch}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n  📄 STATE.md updated: {path}")


def main():
    state_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STATE

    print(f"{'='*50}")
    print(f"  Minimal Cron Demo — STATE.md Lifecycle")
    print(f"  Batch: {TODAY}")
    print(f"  State: {state_path}")
    print(f"{'='*50}")

    # Step 1: Read Before Run
    print("\n📖 Step 1: Read STATE.md (Read Before Run)")
    state = read_state(state_path)
    print(f"  Previous status: {state['status']}")
    print(f"  Previous batch: {state.get('current_batch', 'none')}")

    # Step 2: Idempotency check
    if is_already_done(state, TODAY):
        print(f"\n⏭️  Step 2: Batch {TODAY} already completed (idempotent skip)")
        print("  Nothing to do. Exiting.")
        return

    print(f"\n⚙️  Step 3: Execute task (batch {TODAY})")
    results = simulate_task()

    # Step 4: Write After Every Step
    print(f"\n📝 Step 4: Write STATE.md (Write After Every Step)")
    write_state(state_path, state, results, TODAY)

    # Summary
    print(f"\n{'='*50}")
    print(f"  DONE: {results['summarized']} summarized, {results['failed']} failed")
    print(f"  Run again to see idempotent skip in action!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
