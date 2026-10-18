"""Every workflow and action definition must at least be valid YAML.

Broken YAML in `.github/` fails silently: the workflow simply never runs, and
nothing on the default branch says so. That is how a repo can be "CI green"
while a workflow has not executed for weeks.
"""

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW_DIR = ".github/workflows"
ACTION_DIR = ".github/actions"


def _load(path):
    # `on:` is a YAML 1.1 boolean, so PyYAML turns the key into True.
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflows(root):
    return sorted((root / WORKFLOW_DIR).glob("*.yml")) + \
        sorted((root / WORKFLOW_DIR).glob("*.yaml"))


def test_every_workflow_parses(root):
    files = _workflows(root)
    assert files, "no workflows found"
    for path in files:
        data = _load(path)
        assert isinstance(data, dict), f"{path.name}: not a mapping"
        assert "jobs" in data, f"{path.name}: no jobs"
        assert data["jobs"], f"{path.name}: empty jobs"
        triggers = data.get("on", data.get(True))
        assert triggers, f"{path.name}: no trigger"


def test_every_job_declares_a_runner_or_reuses_a_workflow(root):
    for path in _workflows(root):
        data = _load(path)
        for name, job in data["jobs"].items():
            assert "runs-on" in job or "uses" in job, \
                f"{path.name}: job '{name}' has neither runs-on nor uses"


def test_every_action_parses(root):
    actions = sorted((root / ACTION_DIR).glob("*/action.yml"))
    assert actions, "no composite actions found"
    for path in actions:
        data = _load(path)
        assert data["name"], f"{path}: no name"
        assert data["description"], f"{path}: no description"
        assert data["runs"]["using"] in ("composite", "node20", "node16", "docker"), \
            f"{path}: unsupported runner {data['runs']['using']}"
        if data["runs"]["using"] == "composite":
            assert data["runs"]["steps"], f"{path}: composite action with no steps"
            for step in data["runs"]["steps"]:
                assert "shell" in step, f"{path}: composite step without shell"


def test_dependabot_config_is_valid(root):
    path = root / ".github" / "dependabot.yml"
    assert path.is_file(), "dependabot.yml is missing"
    data = _load(path)
    assert data["version"] == 2
    updates = data["updates"]
    assert updates
    ecosystems = {u["package-ecosystem"] for u in updates}
    assert {"github-actions", "pip"} <= ecosystems
    for u in updates:
        assert u["schedule"]["interval"] in ("daily", "weekly", "monthly")
        # A dependabot directory that does not exist silently does nothing.
        target = root / u["directory"].lstrip("/")
        assert target.is_dir(), f"dependabot directory does not exist: {u['directory']}"


def test_security_policy_exists(root):
    text = (root / "SECURITY.md").read_text(encoding="utf-8")
    assert "Report a vulnerability" in text or "报告漏洞" in text
    assert "security/advisories/new" in text
