#!/usr/bin/env python3
"""Actually run the regression prompts — and say so only when it happened.

`check_test_suite.py` validates that test-prompts.json is well-formed. This
script executes the prompts and judges the answers. The distinction matters:
a green schema check says "the suite is well-formed", never "the patterns
still work".

Judging is binary and fail-closed, per `conventions/skill-evolution.md`
→「硬门禁判定纪律」:

    PASS          every `assertions` string appears, no `forbidden` string does
    FAIL          a `forbidden` string appeared, an `assertions` string did not,
                  the backend errored, or it returned nothing — "could not
                  confirm" is a failure, not a shrug
    INCONCLUSIVE  only when the entry carries an explicit N/A sentinel
                  (`"na": "deprecated: skill removed"`). Never inferred.

Matching is case-insensitive, whitespace-collapsed, NFKC-normalised substring
containment. It is deliberately dumb: a judge you cannot re-derive by hand is
not evidence.

Backends (no third-party dependencies):

    --backend command    run any agent CLI: --command "my-agent --prompt {prompt}"
                         (no shell: {prompt} is substituted inside one argv
                         element; without the placeholder the prompt goes to stdin)
    --backend openai     POST to an OpenAI-compatible /chat/completions
    --backend anthropic  POST to the Anthropic /v1/messages API
    --backend replay     read previously recorded outputs from --recordings

Usage:
    # dry run: list what would execute
    python scripts/run_regression.py --dry-run

    # bring your own agent
    python scripts/run_regression.py --backend command \
        --command "hermes run --prompt {prompt}" --record tests/recordings

    # a hosted model, with the repo's own conventions as the system prompt
    python scripts/run_regression.py --backend anthropic \
        --model claude-sonnet-4-5 --system-file AGENTS.md

    # re-judge yesterday's recordings without spending tokens
    python scripts/run_regression.py --backend replay --recordings tests/recordings

Exit codes:
    0  no FAIL (N/A entries with an explicit sentinel are reported separately)
    1  at least one FAIL — including "the backend gave us nothing"
    2  setup problem (no API key, unknown backend, missing suite)
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
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

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "test-prompts.json"

PASS, FAIL, INCONCLUSIVE = "PASS", "FAIL", "INCONCLUSIVE"


# ---------------------------------------------------------------------------
# Judging
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Case-fold, NFKC-normalise and collapse whitespace.

    The point is to remove differences that carry no meaning (full-width vs
    half-width punctuation, extra newlines) while keeping every difference
    that does.
    """
    text = unicodedata.normalize("NFKC", text or "")
    return " ".join(text.casefold().split())


def judge(entry: dict, output: str) -> dict:
    """Return a verdict dict for one entry against one backend output.

    Fail-closed: anything that is not positive evidence of compliance is a
    FAIL. The only escape hatch is a sentinel the author wrote down *before*
    the run, so it cannot be used after the fact to explain away a bad answer.
    """
    assertions = [a for a in entry.get("assertions") or [] if str(a).strip()]
    forbidden = [f for f in entry.get("forbidden") or [] if str(f).strip()]

    sentinel = str(entry.get("na") or "").strip()
    if sentinel:
        return {
            "verdict": INCONCLUSIVE,
            "reason": f"N/A sentinel: {sentinel}",
            "missing_assertions": [],
            "forbidden_hits": [],
        }
    if not assertions:
        return {
            "verdict": FAIL,
            "reason": "entry has no assertions — the suite cannot verify anything",
            "missing_assertions": [],
            "forbidden_hits": [],
        }
    if not output or not output.strip():
        return {
            "verdict": FAIL,
            "reason": "backend returned no output (fail-closed: unverified is not passed)",
            "missing_assertions": assertions,
            "forbidden_hits": [],
        }

    haystack = normalize(output)
    missing = [a for a in assertions if normalize(a) not in haystack]
    hits = [f for f in forbidden if normalize(f) in haystack]

    if hits:
        return {
            "verdict": FAIL,
            "reason": "forbidden behaviour present: " + ", ".join(hits),
            "missing_assertions": missing,
            "forbidden_hits": hits,
        }
    if missing:
        return {
            "verdict": FAIL,
            "reason": "missing assertion(s): " + ", ".join(missing),
            "missing_assertions": missing,
            "forbidden_hits": [],
        }
    return {
        "verdict": PASS,
        "reason": "all assertions present, no forbidden behaviour",
        "missing_assertions": [],
        "forbidden_hits": [],
    }


# ---------------------------------------------------------------------------
# Backends — each returns (output_text, error_text_or_None)
# ---------------------------------------------------------------------------

def _split_command(cmd: str) -> list[str]:
    """Split a command line into argv without eating Windows path separators.

    `shlex.split` in POSIX mode treats backslash as an escape character, which
    turns `C:\\Python311\\python.exe` into `C:Python311python.exe`. On Windows
    we therefore split in non-POSIX mode and peel one layer of quotes off each
    token; on POSIX the normal split is correct.
    """
    if os.name != "nt":
        return shlex.split(cmd)
    parts = shlex.split(cmd, posix=False)
    cleaned = []
    for part in parts:
        if len(part) >= 2 and part[0] == part[-1] and part[0] in "\"'":
            part = part[1:-1]
        cleaned.append(part)
    return cleaned


def backend_command(prompt: str, args) -> tuple[str, str | None]:
    """Delegate to an arbitrary agent CLI.

    The prompt is never interpolated into a shell string: the command is split
    into argv and `{prompt}` is replaced *inside* a single argument, so quotes,
    backslashes and newlines in a prompt cannot change the command. If the
    command has no `{prompt}` placeholder the prompt is written to stdin.
    """
    if not args.command:
        return "", "--command is required for --backend command"
    try:
        argv = _split_command(args.command)
    except ValueError as e:
        return "", f"cannot parse --command: {e}"
    if not argv:
        return "", "--command is empty"

    uses_placeholder = any("{prompt}" in a for a in argv)
    if uses_placeholder:
        argv = [a.replace("{prompt}", prompt) for a in argv]

    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=args.timeout,
            input=None if uses_placeholder else prompt,
        )
    except FileNotFoundError:
        return "", f"command not found: {argv[0]}"
    except subprocess.TimeoutExpired:
        return "", f"command timed out after {args.timeout}s"
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return out, f"command exited {proc.returncode}"
    return out, None


def _post_json(url: str, payload: dict, headers: dict, timeout: int) -> tuple[dict, str | None]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        return {}, f"HTTP {e.code}: {detail}"
    except urllib.error.URLError as e:
        return {}, f"network error: {e.reason}"
    except (TimeoutError, json.JSONDecodeError) as e:
        return {}, f"{type(e).__name__}: {e}"


def backend_openai(prompt: str, args) -> tuple[str, str | None]:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return "", "OPENAI_API_KEY is not set"
    messages = []
    if args.system_text:
        messages.append({"role": "system", "content": args.system_text})
    messages.append({"role": "user", "content": prompt})
    data, err = _post_json(
        args.base_url.rstrip("/") + "/chat/completions",
        {"model": args.model, "messages": messages},
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        args.timeout,
    )
    if err:
        return "", err
    try:
        return data["choices"][0]["message"]["content"] or "", None
    except (KeyError, IndexError, TypeError):
        return "", f"unexpected response shape: {json.dumps(data)[:300]}"


def backend_anthropic(prompt: str, args) -> tuple[str, str | None]:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return "", "ANTHROPIC_API_KEY is not set"
    payload = {
        "model": args.model,
        "max_tokens": args.max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if args.system_text:
        payload["system"] = args.system_text
    data, err = _post_json(
        args.base_url.rstrip("/") + "/v1/messages",
        payload,
        {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        args.timeout,
    )
    if err:
        return "", err
    try:
        blocks = data["content"]
        return "".join(b.get("text", "") for b in blocks if isinstance(b, dict)), None
    except (KeyError, TypeError):
        return "", f"unexpected response shape: {json.dumps(data)[:300]}"


def backend_replay(prompt: str, args, entry_id: str = "") -> tuple[str, str | None]:
    """Re-judge a recorded run. Never invents an answer for a missing recording."""
    if not args.recordings:
        return "", "--recordings is required for --backend replay"
    base = Path(args.recordings).expanduser()
    for name in (f"{entry_id}.txt", f"{entry_id}.json"):
        p = base / name
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as e:
                return "", f"recording is not valid JSON: {e}"
            return str(payload.get("output", "")), None
        return text, None
    return "", f"no recording for '{entry_id}' in {base}"


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def write_report(path: Path, results: list[dict], args, started: str) -> None:
    counts = {v: sum(1 for r in results if r["verdict"] == v)
              for v in (PASS, FAIL, INCONCLUSIVE)}
    total = len(results)

    lines = [
        "# Behavioral Regression Report",
        "",
        f"**Generated**: {started}",
        f"**Backend**: `{args.backend}`"
        + (f" / `{args.model}`" if args.backend in ("openai", "anthropic") else ""),
        f"**Suite**: `test-prompts.json` ({total} entries)",
        "",
    ]
    if args.system_file:
        lines.append(f"**System prompt**: `{args.system_file}`")
    lines += [
        "",
        "> **Scope: prompts were executed.** Each entry was sent to the backend and",
        "> judged by string containment — `assertions` must appear, `forbidden` must",
        "> not. Judging is **fail-closed**: a backend that errors or returns nothing",
        "> is a FAIL, because \"we could not check\" is not \"it passed\".",
        "> INCONCLUSIVE appears only for entries that declare an explicit N/A",
        "> sentinel (`\"na\"`), and those are excluded from the verified count.",
        "> What this does **not** prove: that the answer is *correct*, only that it",
        "> contains the required evidence and none of the banned behaviour.",
        "",
        "## Summary",
        "",
        "| Verdict | Count |",
        "|:---|---:|",
        f"| ✅ PASS | {counts[PASS]} |",
        f"| ❌ FAIL | {counts[FAIL]} |",
        f"| ⚠️ N/A (sentinel) | {counts[INCONCLUSIVE]} |",
        f"| **Total** | **{total}** |",
        "",
        f"Verified: **{counts[PASS]}/{total - counts[INCONCLUSIVE]}** entries actually passed.",
        "",
        "## Entries",
        "",
        "| # | ID | Verdict | Note |",
        "|---|:---|:---|:---|",
    ]
    for i, r in enumerate(results, 1):
        note = r["reason"].replace("|", "\\|")
        lines.append(f"| {i} | `{r['id']}` | {r['verdict']} | {note} |")

    failing = [r for r in results if r["verdict"] == FAIL]
    if failing:
        lines += ["", "## Failures", ""]
        for r in failing:
            lines.append(f"### `{r['id']}`")
            lines.append("")
            if r["missing_assertions"]:
                lines.append("- missing: " + ", ".join(f"`{a}`" for a in r["missing_assertions"]))
            if r["forbidden_hits"]:
                lines.append("- forbidden present: " + ", ".join(f"`{f}`" for f in r["forbidden_hits"]))
            lines.append("")
            excerpt = r["output"].strip().replace("\r", "")
            if len(excerpt) > 800:
                excerpt = excerpt[:800] + "\n… (truncated)"
            lines += ["```text", excerpt or "(empty)", "```", ""]

    inconclusive = [r for r in results if r["verdict"] == INCONCLUSIVE]
    if inconclusive:
        lines += ["", "## N/A entries (explicit sentinel)", ""]
        for r in inconclusive:
            lines.append(f"- `{r['id']}` — {r['reason']}")

    lines += [
        "",
        "---",
        "",
        "> Generated by `scripts/run_regression.py`. "
        "Schema-only validation is `scripts/check_test_suite.py`.",
    ]

    # Collapse runs of blank lines: the report is markdown that people read and
    # that markdownlint scans, so it has to be as clean as hand-written docs.
    text = []
    for line in lines:
        if line == "" and text and text[-1] == "":
            continue
        text.append(line)
    path.write_text("\n".join(text) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Execute and judge the regression prompts.")
    p.add_argument("--suite", default=str(SUITE))
    p.add_argument("--backend", choices=["command", "openai", "anthropic", "replay"],
                   default="replay")
    p.add_argument("--command", help="agent CLI; {prompt} is substituted")
    p.add_argument("--model", default="")
    p.add_argument("--base-url", default="")
    p.add_argument("--system-file", default="", help="file whose text becomes the system prompt")
    p.add_argument("--recordings", default="", help="directory of recorded outputs (replay/record)")
    p.add_argument("--record", default="", help="save each backend output here for later replay")
    p.add_argument("--only", default="", help="substring filter on entry id")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--max-tokens", type=int, default=2000)
    p.add_argument("--report", default=str(ROOT / "BEHAVIOR_REPORT.md"))
    p.add_argument("--json", default="", help="also write a machine-readable result file")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    suite_path = Path(args.suite).expanduser()
    if not suite_path.is_file():
        print(f"suite not found: {suite_path}", file=sys.stderr)
        return 2
    entries = json.loads(suite_path.read_text(encoding="utf-8"))

    if args.only:
        entries = [e for e in entries if args.only in e.get("id", "")]
    if args.limit:
        entries = entries[: args.limit]
    if not entries:
        print("no entries selected", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"[dry-run] backend={args.backend} entries={len(entries)}")
        for e in entries:
            print(f"  {e['id']}")
        return 0

    if args.backend in ("openai", "anthropic") and not args.model:
        print(f"--model is required for --backend {args.backend}", file=sys.stderr)
        return 2
    if args.backend == "openai" and not args.base_url:
        args.base_url = "https://api.openai.com/v1"
    if args.backend == "anthropic" and not args.base_url:
        args.base_url = "https://api.anthropic.com"

    args.system_text = ""
    if args.system_file:
        sf = Path(args.system_file).expanduser()
        if not sf.is_file():
            print(f"system file not found: {sf}", file=sys.stderr)
            return 2
        args.system_text = sf.read_text(encoding="utf-8", errors="replace")

    if args.record:
        Path(args.record).expanduser().mkdir(parents=True, exist_ok=True)

    started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"=== behavioral regression: {len(entries)} prompt(s), backend={args.backend} ===")

    results = []
    for i, entry in enumerate(entries, 1):
        eid = entry.get("id", f"entry-{i}")
        print(f"[{i}/{len(entries)}] {eid} ... ", end="", flush=True)

        output, err = "", None
        if str(entry.get("na") or "").strip():
            # Declared N/A before the run: do not spend a call on it.
            verdict = judge(entry, "")
        elif args.backend == "command":
            output, err = backend_command(entry["prompt"], args)
            verdict = judge(entry, output)
        elif args.backend == "openai":
            output, err = backend_openai(entry["prompt"], args)
            verdict = judge(entry, output)
        elif args.backend == "anthropic":
            output, err = backend_anthropic(entry["prompt"], args)
            verdict = judge(entry, output)
        else:
            output, err = backend_replay(entry["prompt"], args, entry_id=eid)
            verdict = judge(entry, output)

        if not str(entry.get("na") or "").strip() and err:
            # Fail-closed: a backend we could not reach tells us nothing about
            # the pattern, and "we learned nothing" must not look like a pass.
            verdict = {
                "verdict": FAIL,
                "reason": f"backend error (fail-closed): {err}",
                "missing_assertions": entry.get("assertions") or [],
                "forbidden_hits": [],
            }
        if args.record and output:
            (Path(args.record).expanduser() / f"{eid}.txt").write_text(output, encoding="utf-8")

        results.append({
            "id": eid,
            "verdict": verdict["verdict"],
            "reason": verdict["reason"],
            "missing_assertions": verdict["missing_assertions"],
            "forbidden_hits": verdict["forbidden_hits"],
            "output": output,
        })
        print(verdict["verdict"])

    counts = {v: sum(1 for r in results if r["verdict"] == v)
              for v in (PASS, FAIL, INCONCLUSIVE)}

    report_path = Path(args.report).expanduser()
    write_report(report_path, results, args, started)

    if args.json:
        json_path = Path(args.json).expanduser()
        json_path.write_text(json.dumps({
            "generated": started,
            "backend": args.backend,
            "model": args.model,
            "total": len(results),
            "counts": counts,
            "results": [{k: v for k, v in r.items() if k != "output"} for r in results],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print()
    print(f"  PASS          {counts[PASS]}/{len(results)}")
    print(f"  FAIL          {counts[FAIL]}/{len(results)}")
    print(f"  INCONCLUSIVE  {counts[INCONCLUSIVE]}/{len(results)}")
    print(f"  Report        {report_path}")

    for label, verdict in (("FAILED", FAIL), ("N/A (sentinel)", INCONCLUSIVE)):
        hits = [r for r in results if r["verdict"] == verdict]
        if hits:
            print(f"\n  {label}:")
            for r in hits:
                print(f"    {r['id']}: {r['reason']}")

    if counts[PASS] == 0 and counts[INCONCLUSIVE] == len(results):
        print("\n  ⚠️  Nothing was verified: every entry is N/A by sentinel.")

    if counts[FAIL]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
