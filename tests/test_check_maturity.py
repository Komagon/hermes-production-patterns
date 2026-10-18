"""check_maturity.py — the gate must not pass itself.

Regression: four flags were `store_true` with `default=True` and two criteria
were hardcoded True, so 6 of 8 checks passed with no evidence at all.
"""

import json

from conftest import GOOD_STATE


def test_defaults_pass_nothing(run_script):
    code, out = run_script("check_maturity.py", "--current=L1")
    assert code == 1
    assert "Passed: 0/8" in out


def test_full_attestation_passes(run_script):
    code, out = run_script(
        "check_maturity.py", "--current=L1",
        "--runs_per_week", "3", "--days", "20", "--human_reviews", "6",
        "--state_exists", "--idempotency_exists", "--has_checker",
        "--has_budget", "--zero_denylist",
    )
    assert code == 0, out
    assert "Passed: 8/8" in out


def test_project_derivation_finds_state(run_script, make_project):
    proj = make_project({"STATE.md": GOOD_STATE}, name="derived")
    code, out = run_script("check_maturity.py", "--current=L1", "--project", proj, "--output", "json")
    assert code == 1
    payload = json.loads(out[out.index("{"):])
    assert payload["inputs"]["state_exists"] is True
    assert payload["inputs"]["idempotency_exists"] is True
    assert payload["facts"]["observed_days"] == 0


def test_runs_log_drives_observed_days(run_script, tmp_path):
    proj = tmp_path / "logged"
    (proj / "monitor").mkdir(parents=True)
    (proj / "monitor" / "runs.log").write_text(
        "# job log\n"
        "2026-01-01T09:00:00+08:00 | ok | 001 | 10 | first\n"
        "2026-01-20T09:00:00+08:00 | ok | 002 | 12 | later\n",
        encoding="utf-8",
    )
    code, out = run_script("check_maturity.py", "--current=L1", "--project", proj, "--output", "json")
    payload = json.loads(out[out.index("{"):])
    assert payload["facts"]["observed_days"] == 20
    assert payload["inputs"]["days"] == 20


def test_l3_is_manual_not_pass(run_script):
    code, out = run_script("check_maturity.py", "--current=L3")
    assert code == 0
    assert "人工评审" in out
    # The gate must not print a PASS verdict for L3 — it may *mention* the word
    # in prose ("这不是 PASS"), but it must never render the PASS badge.
    assert "✅ PASS" not in out


def test_missing_project_is_an_error(run_script, tmp_path):
    code, out = run_script("check_maturity.py", "--project", tmp_path / "nope")
    assert code == 2
