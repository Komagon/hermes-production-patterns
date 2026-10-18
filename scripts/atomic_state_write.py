#!/usr/bin/env python3
"""Atomic STATE.md writer with file locking.

Usage:
    python scripts/atomic_state_write.py <path> '{"status": "idle", ...}'

Supports Unix (fcntl) and Windows (msvcrt).
Raises RuntimeError if lock cannot be acquired within timeout.
"""

import json, os, sys, time, tempfile

# Windows pipes and redirects default to the locale code page (cp1252 on an
# en-US machine), so any non-ASCII output raises UnicodeEncodeError. Real
# consoles already go through WriteConsoleW, so forcing UTF-8 here only
# normalises pipes, redirects and CI logs.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

STATE_FILE = os.environ.get("STATE_FILE", "reports/STATE.md")

def acquire_lock(path: str, timeout: float = 5.0):
    """Acquire exclusive file lock. Raises on timeout."""
    lock_path = path + ".lock"
    # The lock file is created before the state file, so its directory has to
    # exist first — otherwise `os.open` raises FileNotFoundError on every retry
    # and the caller sees a bogus "could not acquire lock" after the timeout.
    os.makedirs(os.path.dirname(lock_path) or ".", exist_ok=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        fd = None
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
            # Close the descriptor we just opened: a retry loop that leaks one
            # fd per attempt exhausts the process limit on a long contention.
            if fd is not None:
                os.close(fd)
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
    """Read and parse STATE.md into a dict. Returns empty dict if file missing.

    A section becomes a dict when it holds at least one `- **key**: value`
    line, otherwise a list of its bullets. The previous implementation seeded
    every section as a list and then assigned into it with a string key, so
    `read_state` crashed on exactly the files `format_state` produces.
    """
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    sections = {}
    current = None
    for line in text.split("\n"):
        if line.startswith("## "):
            current = line.strip("# ").strip()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)

    state = {}
    for name, lines in sections.items():
        pairs, items = {}, []
        for line in lines:
            s = line.strip()
            if s.startswith("- **"):
                key, sep, value = s[len("- **"):].partition("**:")
                if sep:
                    pairs[key.strip()] = value.strip()
                    continue
            if s.startswith(("- ", "* ")):
                items.append(s[2:].strip())
        state[name] = pairs if pairs else items
    return state


def format_state(state: dict, title: str = "STATE") -> str:
    """Format a dict back into STATE.md format."""
    lines = [f"# STATE: {title}", ""]
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


def existing_title(path: str) -> str:
    """Reuse the project name already in the file instead of a canned one."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            first = f.readline().strip()
    except OSError:
        return "STATE"
    if first.startswith("# STATE:"):
        return first[len("# STATE:"):].strip() or "STATE"
    return "STATE"


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
            content = format_state(new_state, existing_title(path))
            atomic_write(path, content)
            print(f"Written: {path}")
        finally:
            release_lock(fd)
    else:
        # Read mode
        state = read_state(path)
        print(json.dumps(state, ensure_ascii=False, indent=2))
