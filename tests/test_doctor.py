"""doctor.py — the recommendation engine.

These tests pin the decision tree, because a recommendation engine that quietly
stops recommending the safety patterns is worse than no engine at all: the user
believes they were advised.
"""

import subprocess
import sys

import pytest


@pytest.fixture
def doctor(root):
    return root / "scripts" / "doctor.py"


def _run(script, *args):
    proc = subprocess.run(
        [sys.executable, str(script), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


@pytest.fixture
def asw(root):
    sys.path.insert(0, str(root / "scripts"))
    try:
        import doctor as mod
    finally:
        sys.path.pop(0)
    return mod


def test_auto_mode_writes_report(doctor, tmp_path):
    out_file = tmp_path / "DOCTOR.md"
    code, out = _run(doctor, "--auto", "--output", out_file)
    assert code == 0, out
    assert out_file.is_file()
    assert "hpp doctor 推荐报告" in out_file.read_text(encoding="utf-8")


def test_output_requires_a_path(doctor):
    code, out = _run(doctor, "--auto", "--output")
    assert code == 2
    assert "--output needs a path" in out


def test_universal_patterns_always_recommended(asw):
    must, _, _, reference = asw.recommend({})
    names = {m["pattern"] for m in must}
    assert "state-file-pattern" in names
    assert "error-compact-pattern" in names
    assert {r["pattern"] for r in reference} == {"anti-patterns", "pattern-composition"}


def test_full_autonomy_escalates_to_safety_stack(asw):
    answers = {"task_type": "cron", "autonomy": "full", "risk_level": "high",
               "multi_agent": "multi_same", "state_complexity": "complex"}
    must, should, nice, _ = asw.recommend(answers)
    must_names = {m["pattern"] for m in must}
    should_names = {s["pattern"] for s in should}

    assert {"cron-job-pattern", "maker-checker", "multi-agent-isolation"} <= must_names
    assert {"checkpoint-pattern", "budget-guardrail", "self-update-pattern"} <= should_names
    assert {"memory-os-pattern", "evolution-gate"} <= {n["pattern"] for n in nice}


def test_high_risk_semi_autonomous_needs_human_escalation(asw):
    _, should, _, _ = asw.recommend({"risk_level": "high", "autonomy": "semi"})
    assert "human-escalation" in {s["pattern"] for s in should}


def test_low_risk_supervised_stays_lean(asw):
    answers = {"task_type": "content", "autonomy": "supervised",
               "risk_level": "low", "multi_agent": "single", "state_complexity": "simple"}
    must, should, _, _ = asw.recommend(answers)
    names = {m["pattern"] for m in must} | {s["pattern"] for s in should}
    assert "maker-checker" not in names
    assert "cron-job-pattern" not in names
    assert "secret-management" not in names


def test_every_question_value_is_reachable(asw):
    """Every choice in QUESTIONS must survive format_report without KeyError."""
    answers = {q["id"]: q["choices"][0]["value"] for q in asw.QUESTIONS}
    must, should, nice, ref = asw.recommend(answers)
    report = asw.format_report(answers, must, should, nice, ref)
    assert "安装命令" in report
    for q in asw.QUESTIONS:
        assert q["question"] in report
