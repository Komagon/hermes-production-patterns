"""gate_summary.py — audit JSON to markdown.

The action pipes this straight into $GITHUB_STEP_SUMMARY, so a crash here
silently costs the reviewer the whole report.
"""

import json
import subprocess
import sys


def _audit(checks, score=None, grade=None):
    total = sum(c["points"] for c in checks if c["hit"])
    return {
        "project": "/tmp/demo",
        "score": total if score is None else score,
        "grade": grade or ("Production Ready" if total >= 85 else "Prototype"),
        "checks": checks,
        "missing": [c["id"] for c in checks if not c["hit"]],
    }


CHECKS = [
    {"id": "A1", "group": "Reliability", "points": 8, "hit": True,
     "evidence": "file:STATE.md", "desc": "幂等键存在"},
    {"id": "A3", "group": "Reliability", "points": 10, "hit": False,
     "evidence": "", "desc": "静默失败防护"},
    {"id": "D1", "group": "Quality", "points": 6, "hit": True,
     "evidence": "content:schema.json", "desc": "输出 schema 契约"},
]


def _run(root, tmp_path, payload=None, raw=None):
    # Write the input outside the repo: a test must not leave artifacts in the
    # working tree (this one used to drop _gate_summary_input.json at the root).
    path = tmp_path / "audit.json"
    path.write_text(raw if raw is not None else json.dumps(payload), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "gate_summary.py"), "--json", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def test_renders_score_and_dimensions(root, tmp_path):
    code, out = _run(root, tmp_path, _audit(CHECKS))
    assert code == 0, out
    assert "Production Readiness" in out
    assert "Reliability" in out and "Quality" in out
    # 8 of 18 points in Reliability, 6 of 6 in Quality.
    assert "8/18" in out
    assert "6/6" in out


def test_lists_missing_evidence(root, tmp_path):
    code, out = _run(root, tmp_path, _audit(CHECKS))
    assert code == 0
    assert "Missing evidence" in out
    assert "`A3`" in out
    assert "静默失败防护" in out


def test_shows_where_evidence_came_from(root, tmp_path):
    code, out = _run(root, tmp_path, _audit(CHECKS))
    assert "file:STATE.md" in out
    assert "content:schema.json" in out


def test_states_what_the_score_does_not_measure(root, tmp_path):
    code, out = _run(root, tmp_path, _audit(CHECKS))
    assert "does not measure runtime behaviour" in out


def test_empty_checklist_does_not_crash(root, tmp_path):
    code, out = _run(root, tmp_path, _audit([], score=0, grade="Prototype"))
    assert code == 0, out
    assert "0/100" in out


def test_invalid_json_exits_2(root, tmp_path):
    code, out = _run(root, tmp_path, raw="{not json")
    assert code == 2
    assert "cannot read audit JSON" in out
