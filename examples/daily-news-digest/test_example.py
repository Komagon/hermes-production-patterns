#!/usr/bin/env python3
"""Smoke test: validate SKILL.md and STATE.md structure."""

import os, sys, re, yaml

EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
exit_code = 0

def check(ok: bool, msg: str):
    global exit_code
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {msg}")
    if not ok:
        exit_code = 1

print("=== daily-news-digest example smoke test ===\n")

# 1. SKILL.md exists and has valid YAML frontmatter
skill_path = os.path.join(EXAMPLES_DIR, "SKILL.md")
check(os.path.exists(skill_path), "SKILL.md exists")

with open(skill_path) as f:
    content = f.read()

# Parse frontmatter
frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
check(frontmatter_match is not None, "SKILL.md has YAML frontmatter")

if frontmatter_match:
    fm = yaml.safe_load(frontmatter_match.group(1))
    check(isinstance(fm, dict), "Frontmatter is valid YAML")
    check("name" in fm, "Has 'name' field")
    check("description" in fm, "Has 'description' field")
    check("version" in fm, "Has 'version' field")
    check("triggers" in fm, "Has 'triggers' field")
    check("tools" in fm, "Has 'tools' field")

# 2. Check required sections in body
body = content[frontmatter_match.end():] if frontmatter_match else content
check("前置条件" in body, "Has prerequisites section")
check("### Step 1" in body, "Has Step 1")
check("### Step 2" in body, "Has Step 2")
check("### Step 3" in body, "Has Step 3")
check("### Step 4" in body, "Has Step 4")

# 3. STATE.md exists and has required fields
state_path = os.path.join(EXAMPLES_DIR, "STATE.md")
check(os.path.exists(state_path), "STATE.md exists")

with open(state_path) as f:
    state_content = f.read()

for field in ["Last run", "Status", "Current batch", "Progress", "Lessons Learned", "Idempotency Keys"]:
    check(field in state_content, f"STATE.md has '{field}'")

# 4. Verify convention compliance
check("✅ DETERMINISTIC" in body, "References control-flow-separation (deterministic)")
check("❌ STOCHASTIC" in body, "References control-flow-separation (stochastic)")
check("Idempotency Keys" in state_content, "Follows state-file-pattern convention")

print(f"\n=== Result: {'ALL PASS' if exit_code == 0 else 'FAILURES DETECTED'} ===")
sys.exit(exit_code)
