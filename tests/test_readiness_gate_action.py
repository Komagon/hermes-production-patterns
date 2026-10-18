"""The readiness-gate action's shell logic, executed outside GitHub.

GitHub only runs a composite action inside a workflow, which makes it the one
piece of this repo that would otherwise ship untested. The step script is plain
bash driven by environment variables, so it can be run here with the two
`${{ ... }}` expressions substituted by hand.
"""

import os
import re
import shutil
import subprocess
import sys

import pytest

yaml = pytest.importorskip("yaml")

BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(BASH is None, reason="bash not available")


@pytest.fixture
def action_script(root):
    path = root / ".github" / "actions" / "readiness-gate" / "action.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    steps = data["runs"]["steps"]
    assert len(steps) == 1
    script = steps[0]["run"]
    # The only expression the shell sees; everything else is passed as env.
    return script.replace("${{ github.action_path }}", str(path.parent))


def _run_action(action_script, tmp_path, target, fail_under="85"):
    out_file = tmp_path / "github_output"
    summary = tmp_path / "summary.md"
    out_file.write_text("", encoding="utf-8")
    summary.write_text("", encoding="utf-8")
    env = dict(os.environ)
    env.update({
        "INPUT_PATH": str(target),
        "INPUT_FAIL_UNDER": str(fail_under),
        "INPUT_SUMMARY": "true",
        "PY": sys.executable,
        "GITHUB_OUTPUT": str(out_file),
        "GITHUB_STEP_SUMMARY": str(summary),
        "RUNNER_TEMP": str(tmp_path),
    })
    proc = subprocess.run([BASH, "-c", action_script], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env)
    return proc, out_file.read_text(encoding="utf-8"), summary.read_text(encoding="utf-8")


def test_hollow_project_fails_the_gate(action_script, tmp_path):
    proj = tmp_path / "hollow"
    proj.mkdir()
    for name in ("monitor.md", "STATE.md", "checker.md"):
        (proj / name).write_text("", encoding="utf-8")

    proc, outputs, summary = _run_action(action_script, tmp_path, proj)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "score=0" in outputs
    assert "grade=Prototype" in outputs
    assert "Production Readiness" in summary
    assert "below the required" in proc.stdout + proc.stderr


def test_real_evidence_passes_the_gate(action_script, tmp_path, root):
    """Pointing the action at this repository must clear a 60 threshold."""
    proc, outputs, summary = _run_action(action_script, tmp_path, root, fail_under="60")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    score = int(re.search(r"score=(\d+)", outputs).group(1))
    assert score >= 60
    assert "Missing evidence" not in summary


def test_missing_cli_is_reported_as_an_error(tmp_path):
    """A checkout that does not contain cli/hpp.py must fail loudly."""
    fake = tmp_path / ".github" / "actions" / "readiness-gate"
    fake.mkdir(parents=True)
    script = (
        'repo="$(cd "' + str(fake) + '/../../.." && pwd)"\n'
        'cli="$repo/cli/hpp.py"\n'
        'if [ ! -f "$cli" ]; then echo "::error::hpp CLI not found"; exit 2; fi\n'
    )
    proc = subprocess.run([BASH, "-c", script], capture_output=True, text=True)
    assert proc.returncode == 2
    assert "hpp CLI not found" in proc.stdout
