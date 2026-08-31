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
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HPP_ROOT = Path(__file__).resolve().parents[1]

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
# commands
# ---------------------------------------------------------------------------

def cmd_init(args) -> int:
    kit = args.kit
    if kit not in KITS:
        print(f"unknown kit: {kit}")
        print(f"available: {', '.join(KITS)}")
        return 2
    src = HPP_ROOT / "starter-kits" / kit
    dest = Path(args.target)
    if dest.exists() and any(dest.iterdir()):
        print(f"target not empty: {dest}")
        return 1
    shutil.copytree(src, dest)
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
    root = Path(args.project)
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
    root = Path(args.project)
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

    # secrets must not be committed-ish: .env present without .example is fine
    # locally but flag real-looking keys in tracked files
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in (".md", ".py", ".json", ".yaml", ".yml", ".example", ".txt"):
            try:
                t = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if re.search(r"(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,})", t):
                problems.append(f"possible real API key in: {f.relative_to(root)}")
                break

    # json/yaml files parse
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
                yaml_loader(f.read_text(encoding="utf-8"))
            except Exception as e:
                problems.append(f"invalid YAML {f.relative_to(root)}: {e}")

    for w in warns:
        print(f"⚠ {w}")
    for p in problems:
        print(f"✗ {p}")
    if not problems:
        print("validate PASS" + (f" ({len(warns)} warning(s))" if warns else ""))
        return 1 if False else 0
    return 1


def cmd_audit(args) -> int:
    root = Path(args.project)
    if not root.exists():
        print(f"project dir not found: {root}")
        return 1

    # pre-index all file *names* and file *contents* once
    names = []
    blobs = []
    for f in sorted(root.rglob("*")):
        if f.is_file():
            rel = str(f.relative_to(root))
            names.append(rel)
            try:
                blobs.append((rel, f.read_text(encoding="utf-8")))
            except (UnicodeDecodeError, OSError):
                blobs.append((rel, ""))

    def evidence(kws) -> bool:
        for kw in kws:
            if any(kw.lower() in n.lower() for n in names):
                return True
            # content-level evidence for well-known markers
            if kw in ("red-flags", "checker", "idempotency"):
                for _, t in blobs:
                    if kw.lower() in t.lower():
                        return True
        return False

    print("╔══════════════════════════╗")
    print("║ Production Readiness     ║")
    print("╚══════════════════════════╝")
    total = 0
    missing = []  # (check_id, group_name, weight_hint)
    for code, gname, weight, checks in CHECK_GROUPS:
        got, full = 0, 0
        for cid, pts, kws, desc in checks:
            full += pts
            if evidence(kws):
                got += pts
            else:
                missing.append((cid, gname, desc))
        dim = round(got / full * weight) if full else 0
        total += dim
        print(f"{gname:<16} {bar(dim / weight * 100)} {dim}")
    print(f"\nScore: {total}/100")
    grade = ("Production Ready" if total >= 85
             else "Needs Hardening" if total >= 60 else "Prototype")
    print(f"Grade: {grade}")
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
    p.set_defaults(fn=cmd_audit)

    p = sub.add_parser("doctor", help="environment diagnostics")
    p.set_defaults(fn=cmd_doctor)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
