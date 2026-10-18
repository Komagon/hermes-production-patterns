"""check_test_suite.py — schema validation of test-prompts.json.

The point of these tests is the *honesty* of the report: it must say
"schema validation only" and must not pretend to have run anything.
"""

import json
import shutil

import pytest


def _sandbox(tmp_path, root, entries):
    """Copy the script next to a fake test-prompts.json so ROOT resolves here."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy(root / "scripts" / "check_test_suite.py", scripts / "check_test_suite.py")
    (tmp_path / "test-prompts.json").write_text(
        json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    return scripts / "check_test_suite.py"


def _entry(i):
    return {
        "id": f"pattern-{i}",
        "prompt": "p",
        "expected": "e",
        "assertions": ["a"],
        "forbidden": ["b"],
    }


def test_valid_suite_passes(run_script, root, tmp_path):
    script = _sandbox(tmp_path, root, [_entry(1), _entry(2)])
    code, out = run_script(script, cwd=tmp_path)
    assert code == 0, out
    assert "SCHEMA-VALID: 2/2" in out


def test_missing_field_fails(run_script, root, tmp_path):
    bad = _entry(1)
    bad.pop("forbidden")
    script = _sandbox(tmp_path, root, [bad])
    code, out = run_script(script, cwd=tmp_path)
    assert code == 1
    assert "missing 'forbidden'" in out


def test_duplicate_id_fails(run_script, root, tmp_path):
    script = _sandbox(tmp_path, root, [_entry(1), _entry(1)])
    code, out = run_script(script, cwd=tmp_path)
    assert code == 1
    assert "Duplicate ID" in out


def test_empty_assertions_fails(run_script, root, tmp_path):
    bad = _entry(1)
    bad["assertions"] = []
    script = _sandbox(tmp_path, root, [bad])
    code, out = run_script(script, cwd=tmp_path)
    assert code == 1
    assert "'assertions' is empty" in out


def test_report_states_its_scope(run_script, root, tmp_path):
    script = _sandbox(tmp_path, root, [_entry(1)])
    run_script(script, cwd=tmp_path)
    report = (tmp_path / "TEST_REPORT.md").read_text(encoding="utf-8")
    assert "schema validation only" in report
    assert "not executed" in report
    # The old report claimed behavioural pass rates it never measured.
    assert "Pass rate" not in report


def test_shipped_suite_is_valid(run_script):
    code, out = run_script("check_test_suite.py")
    assert code == 0, out
