#!/usr/bin/env python3
"""Print one field of an `hpp audit --json` report.

The readiness-gate action needs the score and the grade out of the JSON report.
Doing that with an inline `python -c 'json.load(open(sys.argv[1]))'` in the
action's shell script is how v2.5.1 shipped a bug: `open()` without an encoding
uses the *locale* code page, and on an English Windows runner that is cp1252,
which cannot decode the UTF-8 report. The action then died with a
UnicodeDecodeError instead of reporting a score.

Reading the file here, with an explicit encoding, makes the failure impossible
and the behaviour testable.

Usage:
    audit_field.py <report.json> <field> [<field> ...]

Missing fields print an empty string, so a caller can tell "absent" from
"crashed" by the exit code.
"""

import json
import sys

# The grade is a human-readable string and may be non-ASCII. Windows pipes and
# redirects default to the locale code page (cp1252 on an en-US machine), so
# printing it would raise UnicodeEncodeError exactly where this script is used:
# inside `$(...)` in the readiness-gate action.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: audit_field.py <report.json> <field> [<field> ...]", file=sys.stderr)
        return 2

    path, fields = argv[1], argv[2:]
    try:
        with open(path, encoding="utf-8") as fh:
            report = json.load(fh)
    except FileNotFoundError:
        print(f"report not found: {path}", file=sys.stderr)
        return 2
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"report is not valid UTF-8 JSON: {path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(report, dict):
        print(f"report is not a JSON object: {path}", file=sys.stderr)
        return 2

    for name in fields:
        value = report.get(name, "")
        print(value if isinstance(value, str) else str(value))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
