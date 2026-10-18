"""Non-UTF-8 stdout must not crash the tooling.

On Windows, a pipe or redirect defaults to the locale code page — cp1252 on an
en-US machine — and `print()` of any Chinese character then raises
UnicodeEncodeError. The GitHub Windows runner is exactly such a machine, which
is how this was found: the whole suite passed on a zh-CN laptop and failed in
CI. Every entry point now pins stdout/stderr to UTF-8.
"""

import os
import subprocess
import sys

import pytest

CRASH = "UnicodeEncodeError"


def _run(interpreter_script, args, env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(interpreter_script), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


@pytest.fixture
def c1252():
    return {"PYTHONIOENCODING": "cp1252"}


def test_hpp_audit_survives_cp1252(root, tmp_path, c1252):
    proj = tmp_path / "p"
    proj.mkdir()
    (proj / "monitor.md").write_text("监控与告警说明" * 10, encoding="utf-8")
    code, out = _run(root / "cli" / "hpp.py", ["audit", proj, "-v"], c1252)
    assert CRASH not in out, out
    assert code == 0, out


def test_check_maturity_survives_cp1252(root, c1252):
    code, out = _run(root / "scripts" / "check_maturity.py", ["--current=L3"], c1252)
    assert CRASH not in out, out
    assert "人工评审" in out
    assert code == 0


def test_build_docs_check_nav_survives_cp1252(root, c1252):
    """--check-nav prints a Chinese summary; the build must have run first."""
    subprocess.run([sys.executable, str(root / "scripts" / "build_docs.py")],
                   capture_output=True, check=True)
    code, out = _run(root / "scripts" / "build_docs.py", ["--check-nav"], c1252)
    assert CRASH not in out, out
    assert code == 0, out


def test_doctor_survives_cp1252(root, tmp_path, c1252):
    code, out = _run(root / "scripts" / "doctor.py",
                     ["--auto", "--output", tmp_path / "D.md"], c1252)
    assert CRASH not in out, out
    assert code == 0, out


def test_check_test_suite_survives_cp1252(root, c1252):
    code, out = _run(root / "scripts" / "check_test_suite.py", [], c1252)
    assert CRASH not in out, out
    assert code == 0, out


def test_validate_state_survives_cp1252(root, c1252):
    code, out = _run(root / "scripts" / "validate_state.py",
                     [root / "templates" / "STATE.md.template"], c1252)
    assert CRASH not in out, out
    assert code == 0, out


def test_audit_field_survives_cp1252(root, tmp_path, c1252):
    """The grade is Chinese in a zh-CN report, and the action captures it."""
    report = tmp_path / "report.json"
    report.write_text('{"score": 60, "grade": "需要加固"}', encoding="utf-8")
    code, out = _run(root / "scripts" / "audit_field.py", [report, "grade"], c1252)
    assert CRASH not in out, out
    assert "需要加固" in out
    assert code == 0, out
