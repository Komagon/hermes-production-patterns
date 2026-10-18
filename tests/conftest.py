"""Shared fixtures for the hpp / scripts test suite."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HPP = ROOT / "cli" / "hpp.py"
SCRIPTS = ROOT / "scripts"


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture
def run_cli():
    """Run `python cli/hpp.py ...` and return (exit_code, stdout)."""

    def _run(*args, cwd=None):
        proc = subprocess.run(
            [sys.executable, str(HPP), *[str(a) for a in args]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd) if cwd else None,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")

    return _run


@pytest.fixture
def run_script():
    """Run a script from scripts/ and return (exit_code, stdout)."""

    def _run(name, *args, cwd=None):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *[str(a) for a in args]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd) if cwd else None,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")

    return _run


@pytest.fixture
def make_project(tmp_path):
    """Create a throwaway project directory from a dict of relative path -> text."""

    def _make(files: dict, name: str = "proj") -> Path:
        proj = tmp_path / name
        proj.mkdir(parents=True, exist_ok=True)
        for rel, content in files.items():
            p = proj / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return proj

    return _make


GOOD_SKILL = """---
name: demo
description: a demo skill
version: 1.0.0
maturity: beta
---

# Demo
"""

GOOD_STATE = """# STATE: demo

## Current Run
- **Last run**: 2026-10-01T09:00:00+08:00
- **Status**: idle
- **Current batch**: b1

## Progress
- 1/1

## Lessons Learned
- first lesson

## Idempotency Keys
- 2026-10-01: fetch: a1b2c3
"""
