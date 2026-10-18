"""validate_state.py — the STATE.md contract."""

import pytest

from conftest import GOOD_STATE

SHIPPED = [
    "templates/STATE.md.template",
    "examples/daily-news-digest/STATE.md",
    "starter-kits/basic-agent/STATE.md",
    "starter-kits/cron-production/STATE.md",
]


@pytest.mark.parametrize("rel", SHIPPED)
def test_shipped_state_files_pass(run_script, root, rel):
    """Everything we ship must satisfy our own validator."""
    path = root / rel
    if not path.exists():
        pytest.skip(f"{rel} not present")
    code, out = run_script("validate_state.py", path)
    assert code == 0, out


def test_good_state_passes(run_script, make_project):
    proj = make_project({"STATE.md": GOOD_STATE})
    code, out = run_script("validate_state.py", proj / "STATE.md")
    assert code == 0, out


def test_bullet_prefixed_keys_are_accepted(run_script, make_project):
    """The v2.4.0 'hardening' rejected the documented `- YYYY-MM-DD: step: key` form."""
    proj = make_project({"STATE.md": GOOD_STATE})
    code, out = run_script("validate_state.py", proj / "STATE.md")
    assert "All idempotency keys match format (1/1 valid)" in out


def test_bad_status_fails(run_script, make_project):
    proj = make_project({"STATE.md": GOOD_STATE.replace("**Status**: idle", "**Status**: done")})
    code, out = run_script("validate_state.py", proj / "STATE.md")
    assert code == 1
    assert "Status is not a valid value" in out


def test_duplicate_keys_fail(run_script, make_project):
    dup = GOOD_STATE.replace(
        "- 2026-10-01: fetch: a1b2c3",
        "- 2026-10-01: fetch: a1b2c3\n- 2026-10-01: fetch: a1b2c3",
    )
    proj = make_project({"STATE.md": dup})
    code, out = run_script("validate_state.py", proj / "STATE.md")
    assert code == 1
    assert "Duplicate idempotency key" in out


def test_missing_section_fails(run_script, make_project):
    proj = make_project({"STATE.md": "# STATE\n\n## Current Run\n- **Status**: idle\n"})
    code, out = run_script("validate_state.py", proj / "STATE.md")
    assert code == 1
    assert "Section exists: 'Idempotency Keys'" in out


def test_empty_lessons_learned_is_allowed(run_script, make_project):
    """A freshly scaffolded job has no lessons yet — that is not a failure."""
    empty = GOOD_STATE.replace("## Lessons Learned\n- first lesson\n", "## Lessons Learned\n")
    proj = make_project({"STATE.md": empty})
    code, out = run_script("validate_state.py", proj / "STATE.md")
    assert code == 0, out
