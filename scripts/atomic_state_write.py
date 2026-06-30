#!/usr/bin/env python3
"""Atomic STATE.md writer with file locking.

Usage:
    python scripts/atomic_state_write.py <path> '{"status": "idle", ...}'

Supports Unix (fcntl) and Windows (msvcrt).
Raises RuntimeError if lock cannot be acquired within timeout.
"""

import json, os, sys, time, tempfile

STATE_FILE = os.environ.get("STATE_FILE", "reports/STATE.md")

def acquire_lock(path: str, timeout: float = 5.0):
    """Acquire exclusive file lock. Raises on timeout."""
    lock_path = path + ".lock"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if sys.platform == "win32":
                import msvcrt
                fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return fd
            else:
                import fcntl
                fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fd
        except (BlockingIOError, IOError):
            time.sleep(0.1)
    raise RuntimeError(f"Could not acquire lock on {lock_path} within {timeout}s")


def release_lock(fd):
    """Release file lock and close fd."""
    if sys.platform == "win32":
        import msvcrt
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)


def atomic_write(path: str, content: str):
    """Atomically write content to path using tempfile + rename."""
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dir_name, prefix=".state_tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except:
        os.unlink(tmp)
        raise


def read_state(path: str) -> dict:
    """Read and parse STATE.md into a dict. Returns empty dict if file missing."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Basic parsing: extract key fields via section headers
    state = {}
    current_section = None
    for line in text.split("\n"):
        if line.startswith("## "):
            current_section = line.strip("# ").strip()
            state[current_section] = []
        elif current_section and line.strip().startswith("- **"):
            parts = line.strip().split("**:")
            if len(parts) == 2:
                key = parts[0].strip("- **")
                value = parts[1].strip()
                if current_section not in state:
                    state[current_section] = {}
                state[current_section][key] = value
    return state


def format_state(state: dict) -> str:
    """Format a dict back into STATE.md format."""
    lines = ["# STATE: daily-news-digest", ""]
    for section, data in state.items():
        lines.append(f"## {section}")
        lines.append("")
        if isinstance(data, dict):
            for k, v in data.items():
                lines.append(f"- **{k}**: {v}")
        elif isinstance(data, list):
            for item in data:
                lines.append(f"  - {item}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python atomic_state_write.py <path> [json_state]")
        print("  If json_state omitted, reads and prints current state.")
        sys.exit(1)

    path = sys.argv[1]

    if len(sys.argv) >= 3:
        # Write mode
        new_state = json.loads(sys.argv[2])
        fd = acquire_lock(path)
        try:
            content = format_state(new_state)
            atomic_write(path, content)
            print(f"Written: {path}")
        finally:
            release_lock(fd)
    else:
        # Read mode
        state = read_state(path)
        print(json.dumps(state, ensure_ascii=False, indent=2))
