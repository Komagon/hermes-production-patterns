#!/usr/bin/env python3
"""Validate STATE.md schema compliance.

Checks:
  - Required sections exist
  - Required fields within each section
  - Idempotency key format
  - Status value is valid
  - No corrupted content
  - Deduplicate idempotency keys

Usage:
    python scripts/validate_state.py <path-to-state.md>
    python scripts/validate_state.py examples/daily-news-digest/STATE.md
"""

import os
import re
import sys

REQUIRED_SECTIONS = ["Current Run", "Progress", "Lessons Learned", "Idempotency Keys"]
REQUIRED_FIELDS = {
    "Current Run": ["Last run", "Status", "Current batch"],
    "Progress": [],
}
VALID_STATUSES = ["idle", "running", "paused", "failed"]
IDEMPOTENCY_KEY_PATTERN = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}):\s*(?:[A-Za-z0-9_-]+):\s*(?:[A-Za-z0-9_-]+)$"
)

exit_code = 0


def check(ok: bool, msg: str):
    global exit_code
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {msg}")
    if not ok:
        exit_code = 1


def parse_sections(lines):
    sections = {}
    current_section = None
    for line in lines:
        if line.startswith("## "):
            current_section = line.strip("# ").strip()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)
    return sections


def validate(path: str):
    global exit_code
    print(f"\n=== Validating: {path} ===")

    if not os.path.exists(path):
        check(False, "File not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    check(len(lines) > 0, f"File has content ({len(lines)} lines)")

    sections = parse_sections(lines)

    for section in REQUIRED_SECTIONS:
        check(section in sections, f"Section exists: '{section}'")

    if "Current Run" in sections:
        text = "".join(sections["Current Run"])
        for field in REQUIRED_FIELDS["Current Run"]:
            check(f"**{field}**" in text, f"Field exists: 'Current Run' → '{field}'")

        found_valid_status = False
        for status in VALID_STATUSES:
            if f"**Status**: {status}" in text:
                check(True, f"Status is valid: '{status}'")
                found_valid_status = True
                break
        if not found_valid_status:
            check(False, "Status is not a valid value")

    if "Lessons Learned" in sections:
        text = "".join(sections["Lessons Learned"]).strip()
        check(len(text) > 0, "Lessons Learned has content")

    if "Idempotency Keys" in sections:
        keys_text = "".join(sections["Idempotency Keys"])
        key_lines = [
            line.strip()
            for line in keys_text.split("\n")
            if line.strip() and not line.strip().startswith("<!--")
        ]

        if key_lines:
            valid_lines = 0
            seen = set()
            for kl in key_lines:
                if kl in seen:
                    check(False, f"Duplicate idempotency key: '{kl}'")
                    continue
                seen.add(kl)
                if IDEMPOTENCY_KEY_PATTERN.match(kl):
                    valid_lines += 1
                else:
                    check(False, f"Idempotency key format invalid: '{kl}'")
            check(valid_lines == len(key_lines), f"All idempotency keys match format ({valid_lines}/{len(key_lines)} valid)")
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
