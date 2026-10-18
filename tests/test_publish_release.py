"""scripts/publish_release.py — release notes come from the CHANGELOG.

The bug this prevents is a boring one: tags get pushed, releases do not, and the
Releases page quietly stops matching the changelog (v2.4.1 … v2.5.3 shipped
with no release at all). Parsing is pure, so it is tested directly; the `gh`
calls are exercised in CI.
"""

import sys

import pytest


@pytest.fixture
def mod(root):
    sys.path.insert(0, str(root / "scripts"))
    try:
        import publish_release as m
    finally:
        sys.path.pop(0)
    return m


CHANGELOG = """# Changelog

Intro prose that belongs to no version.

## v2.5.3 (2026-10-18)

### 📌 A subtitle

Body of 2.5.3.

- a bullet

## v2.5.2 (2026-10-18)

### 🐛 Another subtitle

Body of 2.5.2.
"""


def test_sections_are_keyed_by_version(mod):
    sections = mod.parse_changelog(CHANGELOG)
    assert list(sections) == ["2.5.3", "2.5.2"]


def test_body_stops_at_the_next_version(mod):
    body = mod.parse_changelog(CHANGELOG)["2.5.3"]["body"]
    assert "Body of 2.5.3." in body
    assert "Body of 2.5.2." not in body
    assert "Intro prose" not in body


def test_subtitle_is_the_first_h3(mod):
    sections = mod.parse_changelog(CHANGELOG)
    assert sections["2.5.3"]["subtitle"] == "📌 A subtitle"
    assert sections["2.5.2"]["subtitle"] == "🐛 Another subtitle"


def test_version_without_subtitle_is_tolerated(mod):
    sections = mod.parse_changelog("## v1.0.0 (2026-01-01)\n\nplain body\n")
    assert sections["1.0.0"]["subtitle"] == ""
    assert sections["1.0.0"]["body"] == "plain body"


def test_version_key_orders_numerically_not_lexically(mod):
    tags = ["v2.10.0", "v2.9.0", "v2.9.10"]
    assert sorted(tags, key=mod.version_key) == ["v2.9.0", "v2.9.10", "v2.10.0"]


def test_non_semver_tag_is_rejected(mod):
    # v1.0.0.11 is a real tag in this repository's history.
    with pytest.raises(ValueError):
        mod.version_key("v1.0.0.11")


def test_dry_run_reports_without_calling_gh(mod, capsys):
    code = mod.main(["publish_release.py", "--tag", "v2.5.3", "--dry-run"])
    assert code == 0
    out = capsys.readouterr().out
    assert "would create release v2.5.3" in out


def test_missing_changelog_section_exits_2(mod, capsys):
    code = mod.main(["publish_release.py", "--tag", "v9.9.9", "--dry-run"])
    assert code == 2
    assert "no section for v9.9.9" in capsys.readouterr().err


def test_non_semver_tag_exits_2(mod, capsys):
    code = mod.main(["publish_release.py", "--tag", "latest", "--dry-run"])
    assert code == 2
    assert "not a semver tag" in capsys.readouterr().err


def test_all_missing_dry_run_covers_tagged_versions(mod, capsys, monkeypatch):
    # The test must not depend on the current state of the GitHub Releases page
    # *or* on the CI git fetch depth (shallow clones have no tags).
    monkeypatch.setattr(mod, "tagged_versions", lambda: ["v2.5.3", "v2.5.2"])
    monkeypatch.setattr(mod, "release_exists", lambda tag: False)
    code = mod.main(["publish_release.py", "--all-missing", "--dry-run"])
    assert code == 0
    out = capsys.readouterr().out
    assert "would create release v2.5.3" in out
    assert "would create release v2.5.2" in out
    assert "0 failed" in out


def test_tag_and_all_missing_together_is_a_usage_error(mod):
    with pytest.raises(SystemExit) as exc:
        mod.main(["publish_release.py", "--tag", "v2.5.3", "--all-missing"])
    assert exc.value.code == 2
