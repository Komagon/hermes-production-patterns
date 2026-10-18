"""build_docs.py — the site generator.

`docs/` is gitignored, so a build is a pure function of the repository. If it
stops producing the pages the site navigation promises, the published site
breaks even though every markdown file is still fine. These are contract tests
on the output, not on the layout.
"""

import subprocess
import sys

import pytest


@pytest.fixture(scope="module")
def built(root):
    """Build once for the whole module; every assertion reads the same output."""
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "build_docs.py")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def test_build_succeeds(built):
    code, out = built
    assert code == 0, out
    assert "docs/ generated" in out


def test_core_pages_exist(built, root):
    assert built[0] == 0, built[1]
    docs = root / "docs"
    for rel in ("index.md", "patterns-library.md", "architecture-page.md",
                "quickstart.md", "cli.md", "readme.md", "readme-en.md",
                "starter-kits.md", "templates.md", "router.md",
                "CHANGELOG.md", "CONTRIBUTING.md"):
        assert (docs / rel).is_file(), f"missing generated page: {rel}"


def test_every_convention_gets_a_page(built, root):
    assert built[0] == 0, built[1]
    conventions = sorted((root / "conventions").glob("*.md"))
    assert conventions, "no conventions found"
    missing = [p.name for p in conventions if not (root / "docs" / "conventions" / p.name).is_file()]
    assert missing == []


def test_nav_check_passes_after_build(built, root):
    assert built[0] == 0, built[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "build_docs.py"), "--check-nav"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")
