#!/usr/bin/env python3
"""Maturity level checklist verifier (machine-readable).

Checks the L1→L2 and L2→L3 criteria. Every criterion is either derived from a
project artifact (`--project DIR`) or attested explicitly on the command line —
nothing is true by default. A gate whose inputs default to "yes" is not a gate.

Objective facts are derived from the project:

    STATE.md exists                 → state_exists
    STATE.md has idempotency keys   → idempotency_exists
    checker/ or verifier/ non-empty → has_checker
    config mentions a budget        → has_budget
    monitor/runs.log dates          → runs_per_week, observed_days

Judgement calls stay explicit and default to False:

    --zero_denylist     you assert no denylist write happened
    --human_reviews N   how many human reviews you actually did

Usage:
    python scripts/check_maturity.py --project ~/my-agent --current=L1
    python scripts/check_maturity.py --current=L2 --project . --checker_pass_rate=0.85
    python scripts/check_maturity.py --current=L1 --runs_per_week 3 --days 20 \
        --human_reviews 6 --state_exists --idempotency_exists --has_checker \
        --has_budget --zero_denylist
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows pipes and redirects default to the locale code page (cp1252 on an
# en-US machine), so any non-ASCII output raises UnicodeEncodeError. Real
# consoles already go through WriteConsoleW, so forcing UTF-8 here only
# normalises pipes, redirects and CI logs.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RUN_LOG_CANDIDATES = ("monitor/runs.log", "runs.log", "reports/runs.log")


def _parse_run_dates(project: Path) -> list[datetime]:
    """Collect dates from the first ISO8601 field of every non-comment line."""
    dates = []
    for rel in RUN_LOG_CANDIDATES:
        log = project / rel
        if not log.is_file():
            continue
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
            if not m:
                continue
            try:
                dates.append(datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                      tzinfo=timezone.utc))
            except ValueError:
                continue
        if dates:
            break
    return dates


def derive_facts(project: Path) -> dict:
    """Read objective facts from a project directory. Missing = False/0."""
    facts = {
        "state_exists": False,
        "idempotency_exists": False,
        "has_checker": False,
        "has_budget": False,
        "runs_per_week": 0,
        "observed_days": 0,
    }

    state = project / "STATE.md"
    if state.is_file():
        facts["state_exists"] = True
        text = state.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^##\s+Idempotency Keys\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
        if m:
            keys = [ln for ln in m.group(1).splitlines()
                    if ln.strip().startswith(("- ", "* "))]
            facts["idempotency_exists"] = len(keys) > 0

    for cand in ("checker", "verifier"):
        p = project / cand
        if p.is_dir() and any(p.iterdir()):
            facts["has_checker"] = True
            break
    for cand in ("checker/PROMPT.md", "CHECKER.md", "verifier/PROMPT.md"):
        p = project / cand
        if p.is_file() and p.stat().st_size > 0:
            facts["has_checker"] = True
            break

    for cand in ("config.yaml", "config.yml", ".env.example", "BUDGET.md"):
        p = project / cand
        if p.is_file() and "budget" in p.read_text(encoding="utf-8", errors="replace").lower():
            facts["has_budget"] = True
            break

    dates = _parse_run_dates(project)
    if dates:
        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)
        facts["runs_per_week"] = sum(1 for d in dates if d.date() >= week_ago)
        facts["observed_days"] = (max(dates).date() - min(dates).date()).days + 1

    return facts


def check_l1_to_l2(runs_per_week: int, has_checker: bool, state_exists: bool,
                   idempotency_exists: bool, days: int, human_reviews: int,
                   has_budget: bool, zero_denylist: bool):
    results = [
        ("Runs ≥ 1x/week", runs_per_week >= 1),
        ("Has auto-verification (Checker)", has_checker),
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
        "details": {name: ok for name, ok in results},
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
        "details": {name: ok for name, ok in results},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", choices=["L1", "L2", "L3"], default="L1")
    parser.add_argument("--project", help="derive objective facts from this project dir")
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--runs_per_week", type=int, default=0)
    parser.add_argument("--checker_pass_rate", type=float, default=0.0)
    parser.add_argument("--retries", type=float, default=99)
    parser.add_argument("--human_reviews", type=int, default=0)
    parser.add_argument("--human_escalations", type=int, default=99)
    # Everything below defaults to False on purpose: nothing is true by default.
    parser.add_argument("--state_exists", action="store_true", default=False)
    parser.add_argument("--idempotency_exists", action="store_true", default=False)
    parser.add_argument("--has_checker", action="store_true", default=False)
    parser.add_argument("--has_budget", action="store_true", default=False)
    parser.add_argument("--zero_denylist", action="store_true", default=False)
    parser.add_argument("--rollback_documented", action="store_true", default=False)
    parser.add_argument("--alerts_configured", action="store_true", default=False)
    parser.add_argument("--sla_defined", action="store_true", default=False)
    parser.add_argument("--kill_switch_verified", action="store_true", default=False)
    parser.add_argument("--error_compact_enabled", action="store_true", default=False)
    parser.add_argument("--max_retries", type=int, default=99)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    facts = {"state_exists": False, "idempotency_exists": False, "has_checker": False,
             "has_budget": False, "runs_per_week": 0, "observed_days": 0}
    if args.project:
        project = Path(args.project).expanduser()
        if not project.is_dir():
            print(f"project dir not found: {project}", file=sys.stderr)
            return 2
        facts = derive_facts(project)

    # CLI attestations can only turn things on, never off.
    state_exists = args.state_exists or facts["state_exists"]
    idempotency_exists = args.idempotency_exists or facts["idempotency_exists"]
    has_checker = args.has_checker or facts["has_checker"]
    has_budget = args.has_budget or facts["has_budget"]
    runs_per_week = args.runs_per_week or facts["runs_per_week"]
    days = args.days or facts["observed_days"]

    if args.current == "L1":
        result = check_l1_to_l2(
            runs_per_week=runs_per_week, has_checker=has_checker,
            state_exists=state_exists, idempotency_exists=idempotency_exists,
            days=days, human_reviews=args.human_reviews,
            has_budget=has_budget, zero_denylist=args.zero_denylist,
        )
    elif args.current == "L2":
        result = check_l2_to_l3(
            days=days, pass_rate=args.checker_pass_rate,
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
        # L3 has no mechanical checklist — say so instead of silently passing.
        result = {"checklist": "L3", "pass": None, "manual": True,
                  "note": "L3 无机械检查项，需人工评审"}

    if args.output == "json":
        payload = dict(result)
        payload["facts"] = facts
        payload["inputs"] = {
            "runs_per_week": runs_per_week, "days": days,
            "state_exists": state_exists, "idempotency_exists": idempotency_exists,
            "has_checker": has_checker, "has_budget": has_budget,
            "zero_denylist": args.zero_denylist,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif result.get("manual"):
        print(f"\n=== Maturity Check: {args.current} → 人工评审 ===")
        print(f"  {result['note']}")
        print("  这不是 PASS：L3 的门槛是运营指标，脚本无法替你判断。")
    else:
        status = "✅ PASS" if result["pass"] else "❌ FAIL"
        print(f"\n=== Maturity Check: {args.current} → {result['checklist']} === {status}")
        print(f"  Passed: {result['passed']}/{result['total']}")
        for name, ok in result.get("details", {}).items():
            print(f"  {'✅' if ok else '❌'} {name}")

    if result.get("manual"):
        return 0
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
