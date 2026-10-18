"""hpp audit — evidence must be content, not file names.

The regression this guards: 13 zero-byte files named monitor.md / STATE.md /
checker.md used to score 86/100 "Production Ready".
"""

import json


def _json(out):
    return json.loads(out[out.index("{"):])


def test_empty_files_score_near_zero(run_cli, make_project):
    names = [
        "monitor.md", "alert.md", "STATE.md", "schema.json", "checker.md",
        "red-flags.md", "regression.json", "BASELINE.md", "GATE.md",
        "METRICS.md", "idempotency.txt", "runs.log",
    ]
    proj = make_project({n: "" for n in names}, name="hollow")
    code, out = run_cli("audit", proj, "--json")
    assert code == 0
    assert _json(out)["score"] < 30


def test_real_content_scores_higher_than_empty(run_cli, make_project):
    body = "This file documents an actual monitoring procedure with alerts.\n"
    hollow = make_project({n: "" for n in ("monitor.md", "STATE.md")}, name="hollow2")
    real = make_project({n: body for n in ("monitor.md", "STATE.md")}, name="real2")
    assert _json(run_cli("audit", hollow, "--json")[1])["score"] < \
           _json(run_cli("audit", real, "--json")[1])["score"]


def test_evidence_source_is_reported(run_cli, tmp_path):
    proj = tmp_path / "ev"
    proj.mkdir()
    # Realistic doc: enough substance to clear the minimum-evidence threshold,
    # and it names the artifact it describes (monitor/alert), which is what the
    # audit keywords look for.
    (proj / "monitor.md").write_text(
        "# 监控与告警\n\n"
        "本项目的 monitor 与 alert 流程如下：每次运行都会写入 monitor/runs.log，\n"
        "失败必须产生可检索的痕迹，并通过 alert 渠道升级人工处理。\n",
        encoding="utf-8")
    payload = _json(run_cli("audit", proj, "--json")[1])
    hits = [c for c in payload["checks"] if c["hit"]]
    assert hits, payload
    assert all(c["evidence"] for c in hits)
    assert any(c["evidence"].startswith(("file:", "content:")) for c in hits)


def test_fail_under_controls_exit_code(run_cli, make_project):
    proj = make_project({"x.md": ""}, name="gate")
    assert run_cli("audit", proj)[0] == 0
    assert run_cli("audit", proj, "--fail-under", "85")[0] == 1


def test_scaffolded_kit_is_not_instantly_production_ready(run_cli, tmp_path):
    dest = tmp_path / "kit"
    assert run_cli("init", "basic-agent", dest)[0] == 0
    score = _json(run_cli("audit", dest, "--json")[1])["score"]
    assert score < 85, "a fresh scaffold must not be graded Production Ready"
