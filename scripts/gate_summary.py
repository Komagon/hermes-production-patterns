#!/usr/bin/env python3
"""Render `hpp audit --json` as a markdown summary.

Exists so CI (and the readiness-gate action) can publish a reviewable table to
`$GITHUB_STEP_SUMMARY` without re-implementing the scoring in YAML.

Usage:
    python cli/hpp.py audit . --json > audit.json
    python scripts/gate_summary.py --json audit.json >> "$GITHUB_STEP_SUMMARY"

    # or pipe straight through
    python cli/hpp.py audit . --json | python scripts/gate_summary.py
"""

import argparse
import json
import sys

# Windows pipes and redirects default to the locale code page (cp1252 on an
# en-US machine), so any non-ASCII output raises UnicodeEncodeError. Real
# consoles already go through WriteConsoleW, so forcing UTF-8 here only
# normalises pipes, redirects and CI logs.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

BAR_FULL, BAR_EMPTY = "█", "░"


def bar(pct: float) -> str:
    filled = max(0, min(10, round(pct / 10)))
    return BAR_FULL * filled + BAR_EMPTY * (10 - filled)


def render(payload: dict) -> str:
    checks = payload.get("checks") or []
    groups = {}
    for c in checks:
        g = groups.setdefault(c["group"], {"hit": 0, "full": 0})
        g["full"] += c["points"]
        if c["hit"]:
            g["hit"] += c["points"]

    score = payload.get("score", 0)
    grade = payload.get("grade", "?")
    icon = "✅" if score >= 85 else ("⚠️" if score >= 60 else "❌")

    lines = [
        f"### {icon} Production Readiness: {score}/100 — {grade}",
        "",
        f"`{payload.get('project', '?')}`",
        "",
        "| Dimension | Score |",
        "|:---|:---|",
    ]
    for name, g in groups.items():
        got = round(g["hit"] / g["full"] * 100) if g["full"] else 0
        lines.append(f"| {name} | {bar(got)} {g['hit']}/{g['full']} |")

    missing = [c for c in checks if not c["hit"]]
    if missing:
        lines += ["", "**Missing evidence**", "", "| id | Dimension | What is missing |", "|:---|:---|:---|"]
        for c in missing:
            lines.append(f"| `{c['id']}` | {c['group']} | {c['desc']} |")

    hit = [c for c in checks if c["hit"]]
    if hit:
        lines += ["", "<details><summary>Evidence sources</summary>", ""]
        for c in hit:
            lines.append(f"- `{c['id']}` {c['desc']} → `{c['evidence']}`")
        lines += ["", "</details>"]

    lines += [
        "",
        "> The score measures whether the *evidence of a production practice* is",
        "> present in the tree (a monitor that logs, a checker that is separate, a",
        "> rollback plan). It does not measure runtime behaviour. See",
        "> `audit/scoring/readiness-score.md`.",
    ]
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Render hpp audit JSON as markdown.")
    p.add_argument("--json", default="-", help="path to audit JSON, or - for stdin")
    args = p.parse_args()

    try:
        raw = sys.stdin.read() if args.json == "-" else open(
            args.json, encoding="utf-8").read()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read audit JSON: {e}", file=sys.stderr)
        return 2

    print(render(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
