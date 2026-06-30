#!/usr/bin/env python3
"""Smoke test: validates SKILL.md frontmatter and STATE.md schema compliance."""

import os, re, sys, yaml

EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
exit_code = 0

def check(ok, msg):
    global exit_code
    print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")
    if not ok: exit_code = 1

print(f"=== Testing: {os.path.basename(EXAMPLE_DIR)} ===\n")

# ── SKILL.md checks ──
skill = os.path.join(EXAMPLE_DIR, "SKILL.md")
check(os.path.exists(skill), "SKILL.md exists")
with open(skill) as f:
    body = f.read()

fm = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
check(fm is not None, "Has YAML frontmatter")
if fm:
    meta = yaml.safe_load(fm.group(1))
    check(isinstance(meta, dict), "Frontmatter is valid YAML")
    for field in ["name", "description", "version", "triggers", "tools"]:
        check(field in meta, f"Has '{field}'")

# Check convention cross-references
body_text = body[fm.end():] if fm else body
for ref in ["state-file-pattern", "control-flow-separation", "maker-checker", "error-compact-pattern"]:
    check(ref in body_text, f"References convention: {ref}")

# Check 5-step workflow
steps = sum(1 for s in body_text.split("### Step ") if s)
check(steps >= 4, f"Has workflow steps (found {steps})")

# ── STATE.md checks ──
state_path = os.path.join(EXAMPLE_DIR, "STATE.md")
check(os.path.exists(state_path), "STATE.md exists")
with open(state_path) as f:
    state = f.read()

for section in ["Schema", "Current Run", "Progress", "Lessons Learned", "Idempotency Keys"]:
    check(f"## {section}" in state, f"Has '{section}' section")

for field in ["Last run", "Status", "Current batch"]:
    check(f"**{field}**" in state, f"Has '{field}' field")

# Check idempotency key format
keys_section = state.split("## Idempotency Keys")[1].split("##")[0] if "## Idempotency Keys" in state else ""
pattern = re.compile(r"\d{4}-\d{2}-\d{2}:\s*\S+:\s*\S+")
valid = sum(1 for line in keys_section.split("\n") if pattern.search(line))
check(valid > 0, f"Idempotency keys match format ({valid} valid)")

print(f"\n=== Result: {'ALL PASS' if exit_code == 0 else 'FAILURES DETECTED'} ===")
sys.exit(exit_code)
