"""lint.js — cross-platform parsing and non-destructive --fix.

Regressions guarded here:
  * CRLF checkouts used to report "No YAML frontmatter" for every file;
  * --fix then prepended a second frontmatter block, corrupting the file.
"""

import shutil
import subprocess
import sys

import pytest

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node not on PATH")


def _lint(root, target, *args):
    proc = subprocess.run(
        [NODE, str(root / "scripts" / "lint.js"), str(target), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


SKILL = "---\nname: demo\ndescription: demo\nversion: 1.0.0\nmaturity: beta\n---\n\n# body\n"


def test_crlf_file_is_parsed(root, tmp_path):
    proj = tmp_path / "crlf"
    proj.mkdir()
    (proj / "SKILL.md").write_bytes(SKILL.replace("\n", "\r\n").encode())
    code, out = _lint(root, proj)
    assert code == 0, out
    assert "No YAML frontmatter" not in out


def test_missing_maturity_is_fixed_with_backup(root, tmp_path):
    proj = tmp_path / "nomaturity"
    proj.mkdir()
    (proj / "SKILL.md").write_text(
        "---\nname: demo\ndescription: demo\nversion: 1.0.0\n---\n\n# body\n",
        encoding="utf-8")
    code, out = _lint(root, proj)
    assert code == 1
    assert "Missing maturity" in out

    code, out = _lint(root, proj, "--fix")
    assert code == 0, out
    assert "maturity:" in (proj / "SKILL.md").read_text(encoding="utf-8")
    backups = list((proj / ".hpp-backup").rglob("SKILL.md"))
    assert backups, "no backup was written"


def test_unparsable_frontmatter_is_never_rewritten(root, tmp_path):
    proj = tmp_path / "broken"
    proj.mkdir()
    original = "---\nname: broken\ndescription: no closing fence\n\n# body\n"
    (proj / "SKILL.md").write_text(original, encoding="utf-8")
    code, out = _lint(root, proj, "--fix")
    assert code == 1
    assert "refusing to auto-fix" in out
    assert (proj / "SKILL.md").read_text(encoding="utf-8") == original


def test_repository_lints_clean(root):
    code, out = _lint(root, root)
    assert code == 0, out
