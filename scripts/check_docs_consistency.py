#!/usr/bin/env python3
"""Check that the numbers the docs claim match the repository.

A repo whose selling point is "no drift" should not drift on its own counts.
Every claim below is a number that has silently gone stale at least once.

Usage:
    python scripts/check_docs_consistency.py
"""

import json
import re
import subprocess
import sys
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

failures = []
notes = []


def ok(msg):
    print(f"  [PASS] {msg}")


def fail(msg):
    print(f"  [FAIL] {msg}")
    failures.append(msg)


def skip(msg):
    print(f"  [SKIP] {msg}")
    notes.append(msg)


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def claims(pattern, text):
    """All integers captured by a pattern, ignoring version-like prefixes."""
    return {int(m) for m in re.findall(pattern, text)}


def check_count(label, expected, patterns):
    """Every number claimed next to `label` must equal `expected`."""
    seen = set()
    for doc, pattern in patterns:
        text = read(doc)
        found = claims(pattern, text)
        if not found:
            skip(f"{label}: no match for /{pattern}/ in {doc}")
            continue
        seen |= found
        for n in sorted(found):
            if n != expected:
                fail(f"{label}: {doc} claims {n}, actual {expected}")
    if seen and seen == {expected}:
        ok(f"{label} = {expected} ({', '.join(d for d, _ in patterns)})")


print("=== docs consistency ===")

conv = sorted(p for p in (ROOT / "conventions").glob("*.md"))
check_count("conventions", len(conv), [
    # Both the prose ("全部 21 个公约") and the repo tree use this phrasing now;
    # the tree used to say "20 个 pattern" and drifted for months because no
    # pattern looked at it.
    ("README.md", r"(\d+)\s*个公约"),
    ("README.en.md", r"(?<![\d.])(\d+)\s+conventions"),
    ("README.en.md", r"(?<![\d.])(\d+)\s+patterns\b"),
])

anti = len(re.findall(r"^## \d+\.", read("conventions/anti-patterns.md"), re.M))
check_count("anti-patterns", anti, [
    ("README.md", r"(\d+)\s*条常见错误实践"),
    ("README.en.md", r"(?<![\d.])(\d+)\s+common error practices"),
])

kits = sorted(p for p in (ROOT / "starter-kits").iterdir() if p.is_dir())
check_count("starter kits", len(kits), [
    ("README.md", r"(\d+)\s*个\s*Starter Kits"),
    ("README.en.md", r"(?<![\d.])(\d+)\s+Starter Kits"),
])

prompts = json.loads(read("test-prompts.json"))
check_count("test prompts", len(prompts), [
    ("README.md", r"(\d+)\s*条回归反测提示词"),
    ("README.en.md", r"(?<![\d.])(\d+)\s+regression test prompts"),
])

# Version must agree across package.json, CHANGELOG and git tags.
pkg_version = json.loads(read("package.json"))["version"]
m = re.search(r"^## v(\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M)
if not m:
    fail("CHANGELOG.md: no '## vX.Y.Z' heading found")
else:
    changelog_version = m.group(1)
    if changelog_version == pkg_version:
        ok(f"version {pkg_version} matches CHANGELOG")
    else:
        fail(f"version mismatch: package.json {pkg_version} vs CHANGELOG {changelog_version}")

    try:
        tags = subprocess.run(["git", "tag", "--list"], cwd=ROOT,
                              capture_output=True, text=True, timeout=10).stdout.split()
    except (OSError, subprocess.SubprocessError):
        tags = []
    if not tags:
        skip("git tags unavailable (shallow clone or no git) — tag check skipped")
    elif f"v{pkg_version}" in tags:
        ok(f"tag v{pkg_version} exists")
    else:
        fail(f"missing tag v{pkg_version} (latest release is not tagged)")

# Every convention must carry the frontmatter fields the linter requires.
missing = []
for p in conv:
    text = p.read_text(encoding="utf-8")
    fm = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not fm:
        missing.append(f"{p.name}: no frontmatter")
        continue
    for key in ("name", "description", "version", "maturity"):
        if not re.search(rf"^{key}\s*:", fm.group(1), re.M):
            missing.append(f"{p.name}: missing {key}")
if missing:
    for m_ in missing:
        fail(f"frontmatter: {m_}")
else:
    ok(f"frontmatter complete for {len(conv)} conventions")

# Files the project promises to ship. A missing one is a broken promise, not a
# missing file: SECURITY.md is referenced from the repo's own threat model, and
# dependabot.yml silently does nothing when absent.
REQUIRED_FILES = [
    "SECURITY.md",
    ".github/dependabot.yml",
    ".gitattributes",
    "pytest.ini",
    "tests/requirements-dev.txt",
    "scripts/run_regression.py",
    "scripts/gate_summary.py",
    ".github/actions/readiness-gate/action.yml",
]
absent = [f for f in REQUIRED_FILES if not (ROOT / f).exists()]
if absent:
    for f in absent:
        fail(f"required file missing: {f}")
else:
    ok(f"all {len(REQUIRED_FILES)} required files present")

print()
if failures:
    print(f"docs consistency FAIL ({len(failures)} problem(s))")
    sys.exit(1)
print(f"docs consistency PASS ({len(notes)} skipped)")
sys.exit(0)