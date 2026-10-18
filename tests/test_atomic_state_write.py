"""atomic_state_write.py — the writer every cron pattern copies.

The failure this guards against is a half-written STATE.md: a crash between
`write()` and the rename leaves the previous state intact, never a truncated
one. Also guards the lock timeout, which must raise instead of silently
proceeding unlocked.
"""

import json
import subprocess
import sys

import pytest


def _run(script, *args, cwd=None):
    proc = subprocess.run(
        [sys.executable, str(script), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd) if cwd else None,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


@pytest.fixture
def script(root):
    return root / "scripts" / "atomic_state_write.py"


def test_write_then_read_roundtrip(script, tmp_path):
    state = tmp_path / "STATE.md"
    code, out = _run(script, state, json.dumps({"Progress": {"done": "3/10"}}))
    assert code == 0, out
    assert state.is_file()
    assert "**done**: 3/10" in state.read_text(encoding="utf-8")

    code, out = _run(script, state)
    assert code == 0, out
    payload = json.loads(out[out.index("{"):out.rindex("}") + 1])
    assert payload["Progress"]["done"] == "3/10"


def test_read_missing_file_is_empty_object(script, tmp_path):
    code, out = _run(script, tmp_path / "nope.md")
    assert code == 0, out
    assert "{}" in out


def test_missing_argument_exits_1(script):
    code, out = _run(script)
    assert code == 1
    assert "Usage" in out


def test_creates_parent_directory(script, tmp_path):
    state = tmp_path / "deep" / "nested" / "STATE.md"
    code, out = _run(script, state, json.dumps({"A": ["x"]}))
    assert code == 0, out
    assert state.is_file()


def test_no_temp_file_left_behind(script, tmp_path):
    state = tmp_path / "STATE.md"
    _run(script, state, json.dumps({"A": {"k": "v"}}))
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".state_tmp_")]
    assert leftovers == []


def test_lock_is_exclusive_and_times_out(script, tmp_path):
    sys.path.insert(0, str(script.parent))
    try:
        import atomic_state_write as asw
    finally:
        sys.path.pop(0)

    target = str(tmp_path / "STATE.md")
    fd = asw.acquire_lock(target)
    try:
        with pytest.raises(RuntimeError, match="Could not acquire lock"):
            asw.acquire_lock(target, timeout=0.3)
    finally:
        asw.release_lock(fd)


def test_parse_ignores_lines_without_sections(tmp_path, root):
    sys.path.insert(0, str(root / "scripts"))
    try:
        import atomic_state_write as asw
    finally:
        sys.path.pop(0)

    p = tmp_path / "STATE.md"
    p.write_text("# STATE\n\n- **stray**: ignored\n\n## S\n- **k**: v\n- plain bullet\n",
                 encoding="utf-8")
    state = asw.read_state(str(p))
    assert state == {"S": {"k": "v"}}
