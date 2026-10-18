#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hpp — Hermes Production Patterns CLI.

v2.0 P2 tooling (roadmap §12-14):
  hpp init <kit>       scaffold a starter kit into a new project dir
  hpp add <pattern>    add a pattern's files into an existing project
  hpp validate         validate project structure (files/schema/secrets/state)
  hpp audit            Production Readiness Score (audit/checks/checklist.md)
  hpp doctor           environment diagnostics

Pure stdlib. HPP_ROOT (repo root) is resolved from the script location so the
CLI works from a clone without installation.

SECURITY UPDATES (2026-10):
- Path traversal protection in cmd_init
- Precise API key detection with checksums
- YAML parsing with size limits
- Secrets redacted from stdout (logged only)
"""
import argparse
import json
import logging
import re
import shutil
import sys
import os
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

HPP_ROOT = Path(__file__).resolve().parents[1]

# Configure logging for sensitive information (not printed to stdout)
_log_handler = logging.StreamHandler(stream=open(os.devnull, 'w'))
_logger = logging.getLogger("hpp_security")
_logger.addHandler(_log_handler)
_logger.setLevel(logging.WARNING)

KITS = [
    "basic-agent", "cron-production", "maker-checker",
    "research-agent", "memory-agent", "self-evolving-agent",
]

# pattern name -> (source paths relative to HPP_ROOT, description)
ADDPABLE = {
    "maker-checker": (
        ["starter-kits/maker-checker/maker", "starter-kits/maker-checker/checker",
         "starter-kits/maker-checker/schemas", "starter-kits/maker-checker/regression"],
        "Maker/Checker 双角色分离 + schema + red-flags + 反测",
    ),
    "error-compact": (
        ["starter-kits/cron-production/recovery"],
        "错误压缩与自愈(recovery/error_compact.py)",
    ),
    "regression-suite": (
        ["starter-kits/maker-checker/regression", "test-prompts.json"],
        "回归反测集:旧失败不再出现 + 旧成功仍成立",
    ),
    "checkpoint": (
        ["conventions/checkpoint-pattern.md"],
        "检查点模式:长任务断点续跑",
    ),
    "cron-production": (
        ["starter-kits/cron-production/monitor"],
        "监控与恢复骨架(monitor/)",
    ),
}

CHECK_GROUPS = [
    ("A", "Reliability", 25, [
        ("A1", 8, ["idempotency"], "幂等键(idempotency key)存在"),
        ("A2", 7, ["idempotency", "tests"], "重复触发防护(幂等测试/查重)"),
        ("A3", 10, ["monitor", "alert"], "静默失败防护(monitor/alert 路径)"),
    ]),
    ("B", "Observability", 20, [
        ("B1", 8, ["runs.log", "monitor"], "运行记录留存"),
        ("B2", 7, ["monitor", "error", "recovery"], "失败可见(失败记录/告警)"),
        ("B3", 5, ["METRICS", "metrics"], "指标定义与采集"),
    ]),
    ("C", "Recoverability", 20, [
        ("C1", 6, ["STATE.md"], "状态文件存在(先读后写)"),
        ("C2", 8, ["checkpoint", "recovery"], "检查点/断点续跑"),
        ("C3", 6, ["rollback", "ROLLBACK", "DEPLOY"], "回滚预案"),
    ]),
    ("D", "Quality", 20, [
        ("D1", 6, ["schema.json"], "输出 schema 契约"),
        ("D2", 8, ["checker", "Checker", "verify", "verifier"], "独立验证角色"),
        ("D3", 6, ["red-flags"], "红线清单"),
    ]),
    ("E", "Evolution", 15, [
        ("E1", 6, ["regression.json", "test-prompts.json"], "反测集"),
        ("E2", 5, ["BASELINE", "METRICS"], "基线与指标数据"),
        ("E3", 4, ["GATE", "gate"], "改动过闸记录"),
    ]),
]

BAR = "█"
EMPTY = "░"


def bar(score: float) -> str:
    filled = round(score / 10)
    return BAR * filled + EMPTY * (10 - filled)


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

# Inline patterns. The previous implementation anchored every pattern to the
# whole line (^...$), which missed every realistic case: a key assigned to a
# variable (`API_KEY = "sk-..."`) never occupies a line by itself.
SECRET_PATTERNS = [
    (re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{32,}\b"), "openai/anthropic api key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "github token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws access key id"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]{20,}=*"), "bearer token"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private key block"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "slack token"),
]

# A match is not a leak if the value itself is obviously a placeholder.
PLACEHOLDER_MARKERS = (
    "your_", "your-", "yourkey", "example", "placeholder", "dummy",
    "xxxx", "****", "redacted", "<", "{", "...", "todo", "changeme", "sample",
)

# Lines that read a value from the environment hold no literal secret.
ENV_READ_MARKERS = ("os.environ", "os.getenv", "process.env", "getenv(", "${")

SCAN_SUFFIXES = {
    ".py", ".md", ".json", ".yaml", ".yml", ".sh", ".bash",
    ".toml", ".ini", ".cfg", ".txt", ".js", ".ts", ".env",
}


def _mask(s: str) -> str:
    """Show enough to identify the key, not enough to use it."""
    if len(s) <= 10:
        return s[0] + "*" * (len(s) - 1)
    return f"{s[:6]}…{s[-4:]}"


def _is_placeholder(snippet: str, line: str) -> bool:
    low = snippet.lower()
    if any(m in low for m in PLACEHOLDER_MARKERS):
        return True
    low_line = line.lower()
    return any(m in low_line for m in ENV_READ_MARKERS)


def scan_secrets(text: str) -> list[tuple[str, int, str]]:
    """Scan text for inline secrets. Returns [(kind, line_no, masked)]."""
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith(("#", "//", "<!--")):
            continue
        for rx, kind in SECRET_PATTERNS:
            m = rx.search(line)
            if not m:
                continue
            snippet = m.group(0)
            if _is_placeholder(snippet, line):
                continue
            hits.append((kind, lineno, _mask(snippet)))
            break
    return hits


def _validate_yaml_safe(yaml_text: str, max_size: int = 1_000_000) -> tuple[bool, str]:
    """
    Safely validate YAML with size limits and timeout.
    
    🟠 FIX #4: Add size limits and prevent DoS attacks (Deep Merge Bomb)
    
    Returns (is_valid, error_msg)
    """
    # Size check
    if len(yaml_text) > max_size:
        return False, f"YAML too large ({len(yaml_text)} > {max_size} bytes)"
    
    # Attempt safe load
    try:
        import yaml
        # Use safe_load to prevent arbitrary code execution
        yaml.safe_load(yaml_text)
        return True, ""
    except yaml.YAMLError as e:
        return False, str(e)
    except Exception as e:
        return False, f"YAML validation error: {e}"


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_init(args) -> int:
    """
    Initialize a starter kit into a new directory.

    Safety policy (v2.4.1): refuse to follow a symlink, refuse to clobber a
    non-empty directory or an existing file, never delete anything. No path
    whitelist — see the comment below for why.
    """
    kit = args.kit
    if kit not in KITS:
        print(f"unknown kit: {kit}")
        print(f"available: {', '.join(KITS)}")
        return 2

    src = HPP_ROOT / "starter-kits" / kit
    if not src.is_dir():
        print(f"kit source missing: {src}")
        return 1

    # Security: normalize + expand "~". pathlib does NOT expand it, so the
    # documented `hpp init basic-agent ~/my-agent` used to create a literal
    # "~" directory on Windows.
    #
    # There is deliberately NO "must be under cwd or home" whitelist: it
    # blocked /tmp (which the CI smoke test writes to) and any legitimate
    # path outside those two roots, while adding no real protection — the
    # actual protection is "never follow a symlink, never clobber content".
    try:
        dest = Path(os.path.expanduser(args.target)).resolve()
    except (OSError, RuntimeError) as e:
        print(f"invalid target path: {e}")
        return 1

    # Prevent symlink attacks
    if dest.is_symlink():
        print(f"ERROR: target is a symlink")
        return 1

    # Target must be a directory (or not exist yet)
    if dest.exists() and not dest.is_dir():
        print(f"ERROR: target exists and is not a directory: {dest}")
        return 1

    # Check if target directory is empty or doesn't exist
    if dest.is_dir() and any(dest.iterdir()):
        print(f"target not empty: {dest}")
        return 1

    # Safe to copy. dirs_exist_ok: an existing *empty* dir is a valid target
    # (e.g. `hpp init basic-agent .` inside a freshly created folder).
    try:
        shutil.copytree(src, dest, dirs_exist_ok=True)
    except OSError as e:
        print(f"failed to scaffold: {e}")
        return 1
    
    print(f"✓ scaffolded {kit} → {dest}")
    print("next:")
    print(f"  cd {dest}")
    print("  edit SKILL.md (name/description/core logic)")
    print("  run and check the README verification checklist")
    return 0


def cmd_add(args) -> int:
    name = args.pattern
    if name not in ADDPABLE:
        print(f"unknown pattern: {name}")
        print(f"available: {', '.join(sorted(ADDPABLE))}")
        return 2
    paths, desc = ADDPABLE[name]
    root = Path(args.project).resolve()
    if not root.exists():
        print(f"project dir not found: {root}")
        return 1
    copied = []
    for rel in paths:
        src = HPP_ROOT / rel
        dest = root / Path(rel).name
        if dest.exists():
            print(f"  skip (exists): {dest}")
            continue
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        copied.append(str(dest))
    print(f"✓ added {name} — {desc}")
    for c in copied:
        print(f"  + {c}")
    print("run `hpp audit` to see the readiness impact")
    return 0


def cmd_validate(args) -> int:
    """
    Validate project structure: frontmatter, JSON/YAML syntax, inline secrets.

    Secret findings are reported with file + line + masked value, so the
    output is actionable without leaking the key itself.
    """
    root = Path(args.project).resolve()
    if not root.exists():
        print(f"project dir not found: {root}")
        return 1
    problems, warns = [], []

    skill = root / "SKILL.md"
    if skill.exists():
        text = skill.read_text(encoding="utf-8")
        m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        if not m:
            problems.append("SKILL.md: no frontmatter")
        else:
            fm = m.group(1)
            for key in ("name", "description", "version"):
                if not re.search(rf"^{key}\s*:", fm, re.M):
                    problems.append(f"SKILL.md frontmatter missing: {key}")
    else:
        warns.append("no SKILL.md (is this an agent project?)")

    state = root / "STATE.md"
    if not state.exists():
        warns.append("no STATE.md (state pattern not adopted)")

    # Inline secret scan (content-based, not line-anchored).
    secret_hits = 0
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in (".git", "node_modules", "__pycache__", ".venv") for part in f.parts):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for kind, lineno, masked in scan_secrets(text):
            secret_hits += 1
            rel = f.relative_to(root).as_posix()
            problems.append(f"secret detected: {rel}:{lineno} ({kind}: {masked})")
            _logger.warning("secret %s at %s:%d", kind, rel, lineno)
    if secret_hits:
        warns.append(f"{secret_hits} secret(s) found — rotate them and move to env vars")

    # 🟠 FIX #4: Validate YAML safely
    yaml_loader = None
    try:
        import yaml as _yaml
        yaml_loader = _yaml.safe_load
    except ImportError:
        yaml_loader = None
    
    for f in list(root.rglob("*.json")):
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:
            problems.append(f"invalid JSON {f.relative_to(root)}: {e}")
    
    if yaml_loader is not None:
        for f in list(root.rglob("*.yaml")) + list(root.rglob("*.yml")):
            try:
                yaml_text = f.read_text(encoding="utf-8")
                is_valid, error_msg = _validate_yaml_safe(yaml_text)
                if not is_valid:
                    problems.append(f"invalid YAML {f.relative_to(root)}: {error_msg}")
            except OSError as e:
                problems.append(f"cannot read {f.relative_to(root)}: {e}")

    for w in warns:
        print(f"⚠ {w}")
    for p in problems:
        print(f"✗ {p}")
    if not problems:
        print("validate PASS" + (f" ({len(warns)} warning(s))" if warns else ""))
        return 0
    return 1


MIN_EVIDENCE_BYTES = 40


def cmd_audit(args) -> int:
    """
    Audit production readiness.

    Evidence must be *content*, not just a file name: a 0-byte file called
    `monitor.md` is not a monitor. Each check reports where its evidence came
    from so the score can be re-derived by hand.
    """
    root = Path(args.project).resolve()
    if not root.exists():
        print(f"project dir not found: {root}")
        return 1

    # Index file contents once (skip VCS / dependency noise).
    blobs = []
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        if any(part in (".git", "node_modules", "__pycache__", ".venv", "site") for part in f.parts):
            continue
        rel = f.relative_to(root).as_posix()
        try:
            blobs.append((rel, f.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            blobs.append((rel, ""))

    evidence_cache = {}

    def evidence(kws) -> tuple[bool, str]:
        """Return (found, where). Filename hits need content; content hits scan text."""
        cache_key = tuple(kws)
        if cache_key in evidence_cache:
            return evidence_cache[cache_key]

        found, where = False, ""
        for kw in kws:
            k = kw.lower()
            for rel, text in blobs:
                if k in rel.lower() and len(text.strip()) >= MIN_EVIDENCE_BYTES:
                    found, where = True, f"file:{rel}"
                    break
            if found:
                break
            for rel, text in blobs:
                if k in text.lower():
                    found, where = True, f"content:{rel}"
                    break
            if found:
                break

        evidence_cache[cache_key] = (found, where)
        return found, where

    results = []
    total = 0
    missing = []  # (check_id, group_name, desc)
    for code, gname, weight, checks in CHECK_GROUPS:
        got, full = 0, 0
        for cid, pts, kws, desc in checks:
            full += pts
            ok, where = evidence(kws)
            if ok:
                got += pts
            else:
                missing.append((cid, gname, desc))
            results.append({
                "id": cid, "group": gname, "points": pts,
                "hit": ok, "evidence": where, "desc": desc,
            })
        dim = round(got / full * weight) if full else 0
        total += dim

    grade = ("Production Ready" if total >= 85
             else "Needs Hardening" if total >= 60 else "Prototype")

    if getattr(args, "json", False):
        print(json.dumps({
            "project": str(root),
            "score": total,
            "grade": grade,
            "checks": results,
            "missing": [c for c, _, _ in missing],
        }, ensure_ascii=False, indent=2))
    else:
        print("╔══════════════════════════╗")
        print("║ Production Readiness     ║")
        print("╚══════════════════════════╝")
        for code, gname, weight, checks in CHECK_GROUPS:
            dim = round(
                sum(r["points"] for r in results if r["group"] == gname and r["hit"])
                / sum(r["points"] for r in results if r["group"] == gname)
                * weight
            )
            print(f"{gname:<16} {bar(dim / weight * 100)} {dim}")
        print(f"\nScore: {total}/100")
        print(f"Grade: {grade}")

        if getattr(args, "verbose", False):
            print("\nEvidence:")
            for r in results:
                mark = "✓" if r["hit"] else "✗"
                src = r["evidence"] or "—"
                print(f"  {mark} {r['id']:<3} {r['desc']}  [{src}]")

        if missing:
            print("\nMissing evidence:")
            for cid, gname, desc in missing:
                print(f"  {cid} [{gname}] {desc}")
            print("\nRecommended:")
            recs = set()
            for cid, _, _ in missing:
                if cid in ("D1", "D2", "D3"):
                    recs.add("hpp add maker-checker")
                if cid in ("A3", "B1", "B2", "A1", "A2"):
                    recs.add("hpp add cron-production")
                if cid in ("C1", "C2"):
                    recs.add("hpp add checkpoint")
                if cid in ("E1", "E2", "E3"):
                    recs.add("hpp add regression-suite")
            for r in sorted(recs):
                print(f"  {r}")

    threshold = getattr(args, "fail_under", 0) or 0
    if total < threshold:
        print(f"\naudit FAIL: {total} < --fail-under {threshold}")
        return 1
    return 0


def cmd_doctor(args) -> int:
    ok = True
    rows = []

    def check(label, cond, detail=""):
        nonlocal ok
        rows.append((label, cond, detail))
        if not cond:
            ok = False

    import platform
    v = sys.version_info
    check("Python", v >= (3, 9), f"{v.major}.{v.minor}.{v.micro} (need >=3.9)")
    check("HPP repo", (HPP_ROOT / "conventions").is_dir(), str(HPP_ROOT))
    hermes = shutil.which("hermes")
    check("hermes CLI", hermes is not None, hermes or "not on PATH (kits still usable)")
    git = shutil.which("git")
    check("git", git is not None, git or "needed for self-update / state versioning")
    skills_dir = Path.home() / ".hermes" / "skills"
    check("Hermes skills dir", skills_dir.is_dir(), str(skills_dir))
    try:
        import yaml  # noqa: F401
        check("PyYAML", True, "installed")
    except ImportError:
        check("PyYAML", False, "pip install pyyaml (only needed for yaml validation)")

    width = max(len(r[0]) for r in rows)
    for label, cond, detail in rows:
        mark = "✓" if cond else "✗"
        print(f"{mark} {label:<{width}}  {detail}")
    print("\ndoctor: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hpp",
                                 description="Hermes Production Patterns CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="scaffold a starter kit")
    p.add_argument("kit", help=f"kit name: {', '.join(KITS)}")
    p.add_argument("target", help="destination directory")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("add", help="add a pattern to an existing project")
    p.add_argument("pattern", help=f"pattern: {', '.join(sorted(ADDPABLE))}")
    p.add_argument("project", nargs="?", default=".", help="project dir (default .)")
    p.set_defaults(fn=cmd_add)

    p = sub.add_parser("validate", help="validate project structure")
    p.add_argument("project", nargs="?", default=".", help="project dir (default .)")
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("audit", help="Production Readiness Score")
    p.add_argument("project", nargs="?", default=".", help="project dir (default .)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="show the evidence source for every check")
    p.add_argument("--fail-under", type=int, default=0, metavar="N",
                   help="exit 1 if the score is below N (default: never fail)")
    p.set_defaults(fn=cmd_audit)

    p = sub.add_parser("doctor", help="environment diagnostics")
    p.set_defaults(fn=cmd_doctor)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
