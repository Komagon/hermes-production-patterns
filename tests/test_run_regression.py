"""run_regression.py — the behavioural judge.

Two separate claims are tested here:

  * the judge itself (PASS / FAIL / INCONCLUSIVE), because a judge you cannot
    re-derive by hand is not evidence;
  * the runner's honesty — an unreachable backend or a missing recording must
    never be reported as a pass.
"""

import json
import sys

import pytest


@pytest.fixture
def mod(root):
    sys.path.insert(0, str(root / "scripts"))
    try:
        import run_regression as m
    finally:
        sys.path.pop(0)
    return m


ENTRY = {
    "id": "demo-pattern",
    "prompt": "p",
    "expected": "e",
    "assertions": ["独立检查", "阈值"],
    "forbidden": ["自审通过"],
}


# ---------------------------------------------------------------------------
# judge()
# ---------------------------------------------------------------------------

def test_judge_passes_when_all_assertions_present(mod):
    v = mod.judge(ENTRY, "应该由独立检查完成，并设定阈值。")
    assert v["verdict"] == "PASS"
    assert v["missing_assertions"] == []


def test_judge_is_case_and_width_insensitive(mod):
    entry = dict(ENTRY, assertions=["Maker", "Checker"], forbidden=["self-approve"])
    v = mod.judge(entry, "  ＭＡＫＥＲ   and checker   did it, no SELF-APPROVE here? ")
    # 'self-approve' IS present, so this must FAIL — the point is that width
    # folding and case folding both worked, not that the verdict is PASS.
    assert v["forbidden_hits"] == ["self-approve"]
    assert v["missing_assertions"] == []
    assert v["verdict"] == "FAIL"


def test_judge_fails_on_forbidden_only(mod):
    v = mod.judge(ENTRY, "独立检查，设定阈值，然后自审通过。")
    assert v["verdict"] == "FAIL"
    assert v["forbidden_hits"] == ["自审通过"]
    assert "forbidden" in v["reason"]


def test_judge_reports_which_assertion_is_missing(mod):
    v = mod.judge(ENTRY, "只有独立检查，没有别的。")
    assert v["verdict"] == "FAIL"
    assert v["missing_assertions"] == ["阈值"]


def test_empty_output_fails_closed(mod):
    """conventions/skill-evolution.md: unverifiable is FAIL, never a shrug."""
    for text in ("", "   ", "\n\n"):
        v = mod.judge(ENTRY, text)
        assert v["verdict"] == "FAIL", repr(text)
        assert "fail-closed" in v["reason"]


def test_entry_without_assertions_fails(mod):
    v = mod.judge(dict(ENTRY, assertions=[]), "随便什么答案")
    assert v["verdict"] == "FAIL"
    assert "no assertions" in v["reason"]


def test_na_requires_an_explicit_sentinel(mod):
    v = mod.judge(dict(ENTRY, na="deprecated: skill removed"), "irrelevant")
    assert v["verdict"] == "INCONCLUSIVE"
    assert "deprecated" in v["reason"]


def test_blank_sentinel_is_not_an_escape_hatch(mod):
    v = mod.judge(dict(ENTRY, na="   "), "")
    assert v["verdict"] == "FAIL"


def test_forbidden_beats_missing_assertion(mod):
    v = mod.judge(ENTRY, "自审通过。")
    assert v["verdict"] == "FAIL"
    assert v["forbidden_hits"] and v["missing_assertions"]


# ---------------------------------------------------------------------------
# runner — replay backend
# ---------------------------------------------------------------------------

def _write_suite(tmp_path, entries):
    p = tmp_path / "suite.json"
    p.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    return p


def _run(root, *args):
    import subprocess
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "run_regression.py"), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def test_replay_pass_and_report_says_it_executed(root, tmp_path):
    suite = _write_suite(tmp_path, [ENTRY])
    rec = tmp_path / "rec"
    rec.mkdir()
    (rec / "demo-pattern.txt").write_text("由独立检查完成，阈值 80 分。", encoding="utf-8")
    report = tmp_path / "R.md"

    code, out = _run(root, "--suite", suite, "--backend", "replay",
                     "--recordings", rec, "--report", report)
    assert code == 0, out
    text = report.read_text(encoding="utf-8")
    assert "prompts were executed" in text
    assert "✅ PASS | 1" in text


def test_missing_recording_fails_the_run(root, tmp_path):
    """A recording that does not exist must not become a green row."""
    suite = _write_suite(tmp_path, [ENTRY])
    rec = tmp_path / "rec"
    rec.mkdir()
    report = tmp_path / "R.md"

    code, out = _run(root, "--suite", suite, "--backend", "replay",
                     "--recordings", rec, "--report", report)
    assert code == 1, out
    assert "no recording" in out
    text = report.read_text(encoding="utf-8")
    assert "❌ FAIL | 1" in text
    assert "✅ PASS | 0" in text


def test_na_entry_is_reported_separately_and_not_verified(root, tmp_path):
    suite = _write_suite(tmp_path, [dict(ENTRY, na="deprecated: removed")])
    report = tmp_path / "R.md"
    code, out = _run(root, "--suite", suite, "--backend", "replay",
                     "--recordings", tmp_path, "--report", report)
    assert code == 0, out
    text = report.read_text(encoding="utf-8")
    assert "⚠️ N/A (sentinel) | 1" in text
    assert "Nothing was verified" in out


def test_failing_entry_exits_1_and_reports_the_gap(root, tmp_path):
    suite = _write_suite(tmp_path, [ENTRY])
    rec = tmp_path / "rec"
    rec.mkdir()
    (rec / "demo-pattern.txt").write_text("我直接自审通过了。", encoding="utf-8")
    report = tmp_path / "R.md"
    code, out = _run(root, "--suite", suite, "--backend", "replay",
                     "--recordings", rec, "--report", report)
    assert code == 1, out
    text = report.read_text(encoding="utf-8")
    assert "## Failures" in text
    assert "自审通过" in text


def test_json_output_is_machine_readable(root, tmp_path):
    suite = _write_suite(tmp_path, [ENTRY])
    rec = tmp_path / "rec"
    rec.mkdir()
    (rec / "demo-pattern.txt").write_text("独立检查 + 阈值", encoding="utf-8")
    js = tmp_path / "r.json"
    code, out = _run(root, "--suite", suite, "--backend", "replay",
                     "--recordings", rec, "--report", tmp_path / "R.md", "--json", js)
    assert code == 0, out
    payload = json.loads(js.read_text(encoding="utf-8"))
    assert payload["counts"]["PASS"] == 1
    assert payload["backend"] == "replay"


# ---------------------------------------------------------------------------
# runner — command backend and guards
# ---------------------------------------------------------------------------

def test_command_backend_uses_argv_not_a_shell(root, tmp_path):
    """A prompt containing shell metacharacters must not be interpreted."""
    nasty = 'a; rm -rf / ; echo $(whoami) `id` "quoted"'
    entry = dict(ENTRY, id="nasty", prompt=nasty, assertions=["a; rm -rf /"], forbidden=[])
    suite = _write_suite(tmp_path, [entry])
    code, out = _run(root, "--suite", suite, "--backend", "command",
                     "--command", f'{sys.executable} -c "import sys;print(sys.argv[1])" "{{prompt}}"',
                     "--report", tmp_path / "R.md")
    assert code == 0, out
    assert "PASS" in out


def test_command_backend_reads_prompt_from_stdin_without_placeholder(root, tmp_path):
    entry = dict(ENTRY, id="stdin", assertions=["独立检查"])
    suite = _write_suite(tmp_path, [entry])
    code, out = _run(root, "--suite", suite, "--backend", "command",
                     "--command", f'{sys.executable} -c "import sys;print(\'独立检查\')"',
                     "--report", tmp_path / "R.md")
    assert code == 0, out


def test_dry_run_lists_entries_without_calling_anything(root, tmp_path):
    suite = _write_suite(tmp_path, [ENTRY])
    code, out = _run(root, "--suite", suite, "--backend", "replay", "--dry-run")
    assert code == 0
    assert "dry-run" in out
    assert "demo-pattern" in out


def test_openai_backend_without_model_exits_2(root, tmp_path):
    suite = _write_suite(tmp_path, [ENTRY])
    code, out = _run(root, "--suite", suite, "--backend", "openai")
    assert code == 2
    assert "--model is required" in out


def test_openai_backend_without_key_is_inconclusive(root, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    suite = _write_suite(tmp_path, [ENTRY])
    code, out = _run(root, "--suite", suite, "--backend", "openai",
                     "--model", "x", "--report", tmp_path / "R.md")
    assert code == 1, out
    assert "OPENAI_API_KEY is not set" in out


def test_only_filter_selects_a_subset(root, tmp_path):
    entries = [dict(ENTRY, id="keep-me"), dict(ENTRY, id="drop-me")]
    suite = _write_suite(tmp_path, entries)
    code, out = _run(root, "--suite", suite, "--backend", "replay",
                     "--only", "keep", "--dry-run")
    assert code == 0
    assert "keep-me" in out
    assert "drop-me" not in out


def test_record_then_replay_roundtrip(root, tmp_path):
    """--record writes what --backend replay later reads."""
    entry = dict(ENTRY, id="round", prompt="say it")
    suite = _write_suite(tmp_path, [entry])
    rec = tmp_path / "rec"

    code, out = _run(root, "--suite", suite, "--backend", "command",
                     "--command", f'{sys.executable} -c "print(\'独立检查 阈值\')"',
                     "--record", rec, "--report", tmp_path / "R1.md")
    assert code == 0, out
    assert (rec / "round.txt").is_file()

    code, out = _run(root, "--suite", suite, "--backend", "replay",
                     "--recordings", rec, "--report", tmp_path / "R2.md")
    assert code == 0, out
    assert "✅ PASS | 1" in (tmp_path / "R2.md").read_text(encoding="utf-8")
