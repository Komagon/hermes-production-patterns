"""hpp validate — frontmatter, syntax, and inline secret detection."""

from conftest import GOOD_SKILL

# A realistic key: prefix + 45 chars. Never used anywhere, generated for tests.
FAKE_KEY = "sk-" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2W3x4"


def test_valid_project_passes(run_cli, make_project):
    proj = make_project({"SKILL.md": GOOD_SKILL})
    code, out = run_cli("validate", proj)
    assert code == 0, out
    assert "validate PASS" in out


def test_missing_version_fails(run_cli, make_project):
    proj = make_project({"SKILL.md": "---\nname: x\ndescription: y\n---\n"})
    code, out = run_cli("validate", proj)
    assert code == 1
    assert "missing: version" in out


def test_secret_in_assignment_is_detected(run_cli, make_project):
    """The old anchored regex missed this: the key never owns a whole line."""
    proj = make_project({
        "SKILL.md": GOOD_SKILL,
        "config.py": f'OPENAI_API_KEY = "{FAKE_KEY}"\n',
    })
    code, out = run_cli("validate", proj)
    assert code == 1, out
    assert "secret detected" in out
    assert "config.py:1" in out
    # The full key must never be echoed back.
    assert FAKE_KEY not in out


def test_secret_in_markdown_is_detected(run_cli, make_project):
    proj = make_project({
        "SKILL.md": GOOD_SKILL,
        "notes.md": f"临时密钥 {FAKE_KEY} 别外传\n",
    })
    code, out = run_cli("validate", proj)
    assert code == 1
    assert "notes.md:1" in out


def test_placeholder_is_not_flagged(run_cli, make_project):
    proj = make_project({
        "SKILL.md": GOOD_SKILL,
        "config.yaml.example": 'api_key: "sk-your-key-here-xxxxxxxxxxxxxxxxxxxxxxxx"\n',
    })
    code, out = run_cli("validate", proj)
    assert code == 0, out


def test_commented_secret_is_ignored(run_cli, make_project):
    proj = make_project({
        "SKILL.md": GOOD_SKILL,
        "notes.md": f"# 旧密钥（已作废）：{FAKE_KEY}\n",
    })
    code, out = run_cli("validate", proj)
    assert code == 0, out


def test_env_read_is_not_a_literal_secret(run_cli, make_project):
    proj = make_project({
        "SKILL.md": GOOD_SKILL,
        "app.py": 'import os\nKEY = os.environ["OPENAI_API_KEY"]\n',
    })
    code, out = run_cli("validate", proj)
    assert code == 0, out


def test_invalid_json_fails(run_cli, make_project):
    proj = make_project({"SKILL.md": GOOD_SKILL, "broken.json": "{ not json"})
    code, out = run_cli("validate", proj)
    assert code == 1
    assert "invalid JSON" in out
