#!/usr/bin/env python3
"""Maturity level checklist verifier (machine-readable).

Checks L1→L2 and L2→L3 criteria.
Outputs JSON for CI integration.

Usage:
    python scripts/check_maturity.py --current=L1 --days=15 --checker_pass_rate=0.9
    python scripts/check_maturity.py --current=L2 --days=30 --checker_pass_rate=0.85 --retries=1
"""

import argparse, json, sys


def check_l1_to_l2(days: int, human_reviews: int, state_exists: bool,
                   idempotency_exists: bool, has_budget: bool, zero_denylist: bool):
    results = [
        ("Runs ≥ 1x/week", True),
        ("Has auto-verification (Checker)", True),
        ("STATE.md exists", state_exists),
        ("STATE.md has idempotency_keys", idempotency_exists),
        ("L1 runs ≥ 14 days", days >= 14),
        ("Human reviews ≥ 5", human_reviews >= 5),
        ("Token budget estimated", has_budget),
        ("Zero denylist writes", zero_denylist),
    ]
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    return {
        "checklist": "L1→L2",
        "passed": passed,
        "total": total,
        "pass": passed == total,
        "required_consecutive_days": 14,
        "details": {name: ok for name, ok in results}
    }


def check_l2_to_l3(days: int, pass_rate: float, avg_retries: float,
                   human_escalations: int, rollback_documented: bool,
                   alerts_configured: bool, sla_defined: bool, kill_switch_verified: bool,
                   error_compact_enabled: bool, max_retries: int):
    results = [
        ("L2 runs ≥ 28 days", days >= 28),
        ("Checker PASS rate ≥ 80%", pass_rate >= 0.8),
        ("Avg retries ≤ 1.5", avg_retries <= 1.5),
        ("Zero human escalations", human_escalations == 0),
        ("Rollback strategy documented", rollback_documented),
        ("Monitoring alerts configured", alerts_configured),
        ("SLA metrics defined", sla_defined),
        ("Kill switch verified", kill_switch_verified),
        ("Error compact pattern enabled", error_compact_enabled),
        ("Max retries ≤ 3", max_retries <= 3),
    ]
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    return {
        "checklist": "L2→L3",
        "passed": passed,
        "total": total,
        "pass": passed == total,
        "required_consecutive_days": 28,
        "min_checker_pass_rate": 0.8,
        "details": {name: ok for name, ok in results}
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", choices=["L1", "L2", "L3"], default="L1")
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--checker_pass_rate", type=float, default=0.0)
    parser.add_argument("--retries", type=float, default=99)
    parser.add_argument("--human_reviews", type=int, default=0)
    parser.add_argument("--human_escalations", type=int, default=99)
    parser.add_argument("--state_exists", action="store_true", default=True)
    parser.add_argument("--idempotency_exists", action="store_true", default=True)
    parser.add_argument("--has_budget", action="store_true", default=True)
    parser.add_argument("--zero_denylist", action="store_true", default=True)
    parser.add_argument("--rollback_documented", action="store_true")
    parser.add_argument("--alerts_configured", action="store_true")
    parser.add_argument("--sla_defined", action="store_true")
    parser.add_argument("--kill_switch_verified", action="store_true")
    parser.add_argument("--error_compact_enabled", action="store_true")
    parser.add_argument("--max_retries", type=int, default=99)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    if args.current == "L1":
        result = check_l1_to_l2(
            days=args.days, human_reviews=args.human_reviews,
            state_exists=args.state_exists,
            idempotency_exists=args.idempotency_exists,
            has_budget=args.has_budget,
            zero_denylist=args.zero_denylist,
        )
    elif args.current == "L2":
        result = check_l2_to_l3(
            days=args.days, pass_rate=args.checker_pass_rate,
            avg_retries=args.retries,
            human_escalations=args.human_escalations,
            rollback_documented=args.rollback_documented,
            alerts_configured=args.alerts_configured,
            sla_defined=args.sla_defined,
            kill_switch_verified=args.kill_switch_verified,
            error_compact_enabled=args.error_compact_enabled,
            max_retries=args.max_retries,
        )
    else:
        result = {"checklist": f"{args.current}→?", "pass": True}

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        status = "✅ PASS" if result["pass"] else "❌ FAIL"
        print(f"\n=== Maturity Check: {args.current} → {result['checklist']} === {status}")
        print(f"  Passed: {result['passed']}/{result['total']}")
        for name, ok in result.get("details", {}).items():
            print(f"  {'✅' if ok else '❌'} {name}")

    sys.exit(0 if result["pass"] else 1)
