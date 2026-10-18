"""Mechanical gates for the two encoding bugs that only show up on other machines.

Both of these were invisible on a Chinese Windows box and broke on the English
Windows runner:

  * `open(path)` / `Path.read_text()` without `encoding=` uses the *locale*
    code page. cp936 decodes almost any byte sequence, so a UTF-8 file reads
    "fine" locally; cp1252 cannot decode byte 0x8d and raises UnicodeDecodeError.
  * An inline `python -c '...open(sys.argv[1])...'` inside a workflow or action
    has the same problem, and is also the one piece of shipped logic that no
    test can import.

So both are checked statically. This is the same rule as anti-pattern #13: a
constraint that only exists in a document is a constraint that will be violated.
"""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Every Python file that ships and runs unattended.
SHIPPED = sorted(
    list((ROOT / "cli").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py"))
)

# `python -c` / `python3 -c` inside a shell step. Legitimate code belongs in
# scripts/, where it can be imported and tested.
INLINE_PYTHON = re.compile(r"\bpython3?\s+-c\b")


def _text_file_calls(tree: ast.AST):
    """Yield (lineno, call) for text-mode file opens that omit `encoding`."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
            # os.open() returns a file descriptor, not a text stream.
            if name == "open" and isinstance(func.value, ast.Name) and func.value.id == "os":
                continue
        else:
            continue

        if name == "open":
            mode = "r"
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if isinstance(mode, str) and "b" in mode:
                continue
        elif name not in {"read_text", "write_text"}:
            continue

        if not any(kw.arg == "encoding" for kw in node.keywords):
            yield node.lineno, name


def test_shipped_python_reads_files_with_an_explicit_encoding():
    offenders = []
    for path in SHIPPED:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for lineno, name in _text_file_calls(tree):
            rel = path.relative_to(ROOT).as_posix()
            offenders.append(f"{rel}:{lineno}: {name}() without encoding=")

    assert not offenders, (
        "text-mode file access must pin encoding= (the locale code page is not "
        "UTF-8 on an English Windows box):\n  " + "\n  ".join(offenders)
    )


def _shell_blocks(text: str):
    """Yield the `run:` / `script:` values of a workflow or action file."""
    import yaml

    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        return

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"run", "script"} and isinstance(value, str):
                    yield value
                else:
                    yield from walk(value)
        elif isinstance(node, list):
            for item in node:
                yield from walk(item)

    yield from walk(data)


@pytest.mark.parametrize(
    "path",
    sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    + sorted((ROOT / ".github" / "actions").rglob("*.yml")),
    ids=lambda p: p.name,
)
def test_no_inline_python_in_shell_steps(path):
    pytest.importorskip("yaml")
    for block in _shell_blocks(path.read_text(encoding="utf-8")):
        assert not INLINE_PYTHON.search(block), (
            f"{path.name}: inline `python -c` in a shell step — put it in "
            f"scripts/ so it can be imported and tested:\n{block.strip()[:400]}"
        )
