"""scripts/audit_field.py — the seam that replaced an inline `python -c`.

The readiness-gate action used to read the score with
`python -c 'json.load(open(sys.argv[1]))["score"]'`. That `open()` had no
encoding, so on a cp1252 Windows runner the UTF-8 report raised
UnicodeDecodeError and the action reported no score at all. These tests pin the
replacement: explicit UTF-8, a real exit code on bad input, and no traceback.
"""

import json

import pytest


@pytest.fixture
def script(root):
    return root / "scripts" / "audit_field.py"


def _run(run_script, tmp_path, payload, fields):
    report = tmp_path / "report.json"
    report.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return run_script("audit_field.py", report, *fields)


def test_prints_the_requested_fields_in_order(run_script, tmp_path):
    code, out = _run(run_script, tmp_path, {"score": 100, "grade": "Production Ready"},
                     ["score", "grade"])
    assert code == 0
    assert out.splitlines() == ["100", "Production Ready"]


def test_reads_utf8_reports_containing_non_ascii(run_script, tmp_path):
    """The exact shape that broke on a cp1252 runner."""
    payload = {"score": 60, "grade": "需要加固", "checks": [{"name": "监控"}]}
    code, out = _run(run_script, tmp_path, payload, ["grade"])
    assert code == 0
    assert "需要加固" in out


def test_missing_field_prints_empty_and_still_succeeds(run_script, tmp_path):
    code, out = _run(run_script, tmp_path, {"score": 60}, ["grade"])
    assert code == 0
    assert out.strip() == ""


def test_missing_report_exits_2_without_a_traceback(run_script, tmp_path):
    code, out = run_script("audit_field.py", tmp_path / "nope.json", "score")
    assert code == 2
    assert "report not found" in out
    assert "Traceback" not in out


def test_non_json_report_exits_2(run_script, tmp_path):
    report = tmp_path / "broken.json"
    report.write_text("{not json", encoding="utf-8")
    code, out = run_script("audit_field.py", report, "score")
    assert code == 2
    assert "not valid UTF-8 JSON" in out
    assert "Traceback" not in out


def test_usage_without_fields_exits_2(run_script, tmp_path):
    code, out = run_script("audit_field.py", tmp_path / "x.json")
    assert code == 2
    assert "usage:" in out
