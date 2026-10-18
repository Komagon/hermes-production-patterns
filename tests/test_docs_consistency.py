"""check_docs_consistency.py — the numbers in the docs match the repo."""

def test_counts_and_frontmatter_agree(run_script):
    code, out = run_script("check_docs_consistency.py")
    assert "[FAIL] conventions" not in out
    assert "[FAIL] anti-patterns" not in out
    assert "[FAIL] starter kits" not in out
    assert "[FAIL] test prompts" not in out
    assert "frontmatter complete" in out
    assert "version" in out
    # The only allowed failure is an untagged release (local checkouts often
    # have no tags); CI fetches tags and enforces this too.
    for line in out.splitlines():
        if "[FAIL]" in line:
            assert "tag" in line, line


def test_version_matches_changelog(run_script):
    code, out = run_script("check_docs_consistency.py")
    assert "matches CHANGELOG" in out
