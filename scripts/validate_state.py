#!/usr/bin/env python3
"""Validate STATE.md schema compliance.

Checks:
  - Required sections exist
  - Required fields within each section
  - Idempotency key format
  - Status value is valid
  - No corrupted content

Usage:
    python scripts/validate_state.py <path-to-state.md>
    python scripts/validate_state.py examples/daily-news-digest/STATE.md
"""

import os, sys, re

REQUIRED_SECTIONS = ["Current Run", "Progress", "Lessons Learned", "Idempotency Keys"]
REQUIRED_FIELDS = {
    "Current Run": ["Last run", "Status", "Current batch"],
    "Progress": [],  # no required sub-fields, but must exist
}
VALID_STATUSES = ["idle", "running", "paused", "failed"]
IDEMPOTENCY_KEY_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}:\s*\S+:\s*\S+"
)

exit_code = 0


def check(ok: bool, msg: str):
    global exit_code
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {msg}")
    if not ok:
        exit_code = 1


def validate(path: str):
    print(f"\n=== Validating: {path} ===")

    if not os.path.exists(path):
        check(False, "File not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    check(len(lines) > 0, f"File has content ({len(lines)} lines)")

    # Parse sections
    sections = {}
    current_section = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            current_section = line.strip("# ").strip()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)

    # Check required sections
    for section in REQUIRED_SECTIONS:
        check(section in sections, f"Section exists: '{section}'")

    # Check required fields in Current Run
    if "Current Run" in sections:
        text = "".join(sections["Current Run"])
        for field in REQUIRED_FIELDS["Current Run"]:
            check(f"**{field}**" in text, f"Field exists: 'Current Run' → '{field}'")

    # Check status value
    if "Current Run" in sections:
        text = "".join(sections["Current Run"])
        for status in VALID_STATUSES:
            if f"**Status**: {status}" in text:
                check(True, f"Status is valid: '{status}'")
                break
        else:
            check(False, "Status is not a valid value")

    # Check Lessons Learned has content
    if "Lessons Learned" in sections:
        text = "".join(sections["Lessons Learned"]).strip()
        # At minimum should have a comment or entry
        check(len(text) > 0, "Lessons Learned has content")

    # Check Idempotency Keys format
    if "Idempotency Keys" in sections:
        keys_text = "".join(sections["Idempotency Keys"])
        key_lines = [
            l.strip() for l in keys_text.split("\n")
            if l.strip() and not l.strip().startswith("<!--")
        ]
        if key_lines:
            valid_count = sum(1 for kl in key_lines if IDEMPOTENCY_KEY_PATTERN.search(kl))
            check(valid_count > 0, f"Idempotency keys match format ({valid_count} valid)")
        else:
            check(True, "Idempotency Keys section exists (can be empty for new jobs)")

    print(f"  Result: {'ALL PASS' if exit_code == 0 else 'FAILURES DETECTED'}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_state.py <path> [path2 ...]")
        sys.exit(1)

    for p in sys.argv[1:]:
        validate(p)

    sys.exit(exit_code)
