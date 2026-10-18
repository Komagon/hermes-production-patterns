"""hpp init — path handling and safety policy.

Regression cover for the bug that kept main red for 18 days: a cwd/home
whitelist rejected /tmp, which is exactly where the CI smoke test scaffolds.
"""

import json


def test_init_new_dir(run_cli, tmp_path):
    dest = tmp_path / "agent"
    code, out = run_cli("init", "basic-agent", dest)
    assert code == 0, out
    assert (dest / "SKILL.md").is_file()
    assert (dest / "README.md").is_file()


def test_init_into_existing_empty_dir(run_cli, tmp_path):
    dest = tmp_path / "empty"
    dest.mkdir()
    code, out = run_cli("init", "basic-agent", dest)
    assert code == 0, out
    assert (dest / "SKILL.md").is_file()


def test_init_outside_cwd_is_allowed(run_cli, tmp_path):
    """No cwd/home whitelist: /tmp-style targets must work (CI relies on it)."""
    dest = tmp_path / "elsewhere" / "agent"
    code, out = run_cli("init", "basic-agent", dest, cwd=tmp_path)
    assert code == 0, out


def test_init_refuses_non_empty_dir(run_cli, tmp_path):
    dest = tmp_path / "busy"
    dest.mkdir()
    (dest / "keep.txt").write_text("do not touch", encoding="utf-8")
    code, out = run_cli("init", "basic-agent", dest)
    assert code == 1
    assert "not empty" in out
    assert (dest / "keep.txt").read_text(encoding="utf-8") == "do not touch"


def test_init_refuses_file_target(run_cli, tmp_path):
    dest = tmp_path / "afile"
    dest.write_text("x", encoding="utf-8")
    code, out = run_cli("init", "basic-agent", dest)
    assert code == 1
    assert "not a directory" in out


def test_init_unknown_kit(run_cli, tmp_path):
    code, out = run_cli("init", "no-such-kit", tmp_path / "x")
    assert code == 2
    assert "unknown kit" in out


def test_init_then_validate_then_audit(run_cli, tmp_path):
    """The exact CI smoke sequence, including --json output."""
    dest = tmp_path / "smoke"
    assert run_cli("init", "basic-agent", dest)[0] == 0
    assert run_cli("validate", dest)[0] == 0
    code, out = run_cli("audit", dest, "--json")
    assert code == 0
    payload = json.loads(out[out.index("{"):])
    assert payload["score"] >= 0
    assert payload["checks"]
