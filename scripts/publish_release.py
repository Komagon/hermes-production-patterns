#!/usr/bin/env python3
"""Publish GitHub releases from the CHANGELOG.

Every release note in this repository already exists as a `## vX.Y.Z` section of
CHANGELOG.md. Retyping it into the GitHub UI is how the two drift apart: tags
v2.4.1 … v2.5.3 were pushed but never released, so the Releases page stopped at
v2.4.0 while the changelog kept going.

This script makes the changelog the only source of release notes, and `gh` the
only thing that talks to GitHub.

Usage:
    publish_release.py --tag v2.5.3      # publish one tag
    publish_release.py --all-missing     # publish every tagged version that has
                                         # no release yet and has a changelog
                                         # section (oldest first, so "latest"
                                         # ends up on the newest version)

Add --dry-run to print what would happen without touching GitHub.

Exit codes: 0 published (or nothing to do), 1 at least one publish failed,
2 a precondition failed (no gh, no changelog section, bad tag).
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows pipes and redirects default to the locale code page, so non-ASCII
# output would raise UnicodeEncodeError on an en-US machine.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"

SEMVER_TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
VERSION_HEADING = re.compile(r"^## v(\d+\.\d+\.\d+)\b(.*)$", re.MULTILINE)
SUBTITLE = re.compile(r"^###\s+(.+)$", re.MULTILINE)


def parse_changelog(text: str) -> dict[str, dict[str, str]]:
    """Map each `## vX.Y.Z` section to its body and its first `###` subtitle."""
    headings = list(VERSION_HEADING.finditer(text))
    sections: dict[str, dict[str, str]] = {}
    for index, match in enumerate(headings):
        version = match.group(1)
        start = match.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[start:end].strip()
        subtitle = SUBTITLE.search(body)
        sections[version] = {
            "body": body,
            "subtitle": subtitle.group(1).strip() if subtitle else "",
        }
    return sections


def version_key(tag: str) -> tuple[int, int, int]:
    match = SEMVER_TAG.match(tag)
    if not match:
        raise ValueError(f"not a semver tag: {tag}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _gh(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess:
    binary = shutil.which("gh")
    if binary is None:
        raise SystemExit("gh CLI not found — install it, or run this in GitHub Actions")
    return subprocess.run(
        [binary, *args],
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def release_exists(tag: str) -> bool | None:
    """True/False, or None when the answer cannot be known (no gh, dry run)."""
    if shutil.which("gh") is None:
        return None
    return _gh(["release", "view", tag], capture=True).returncode == 0


def publish(tag: str, body: str, subtitle: str, *, dry_run: bool) -> bool:
    title = f"{tag} — {subtitle}" if subtitle else tag
    if dry_run:
        print(f"[dry-run] would create release {tag} ({len(body)} chars of notes)")
        return True

    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".md", delete=False
    ) as notes:
        notes.write(body + "\n")
        notes_path = notes.name
    try:
        proc = _gh(
            [
                "release", "create", tag,
                "--title", title,
                "--notes-file", notes_path,
                "--verify-tag",
            ]
        )
    finally:
        Path(notes_path).unlink(missing_ok=True)

    if proc.returncode != 0:
        print(f"FAILED: {tag} — gh exited {proc.returncode}", file=sys.stderr)
        return False
    print(f"published {tag}")
    return True


def tagged_versions() -> list[str]:
    proc = subprocess.run(
        ["git", "tag", "--list", "v*"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    tags = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    return sorted((t for t in tags if SEMVER_TAG.match(t)), key=version_key)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", default="", help="publish this tag (e.g. v2.5.3)")
    parser.add_argument("--all-missing", action="store_true",
                        help="publish every tagged version that has no release yet")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv[1:])

    if bool(args.tag) == bool(args.all_missing):
        parser.error("pass exactly one of --tag or --all-missing")

    sections = parse_changelog(CHANGELOG.read_text(encoding="utf-8"))

    if args.tag:
        if not SEMVER_TAG.match(args.tag):
            print(f"not a semver tag: {args.tag}", file=sys.stderr)
            return 2
        version = args.tag[1:]
        if version not in sections:
            print(f"CHANGELOG.md has no section for {args.tag}", file=sys.stderr)
            return 2
        exists = release_exists(args.tag)
        if exists:
            print(f"{args.tag} already has a release — nothing to do")
            return 0
        if exists is None:
            print(f"{args.tag}: cannot check for an existing release (no gh); "
                  f"dry run assumes it is missing")
        section = sections[version]
        return 0 if publish(args.tag, section["body"], section["subtitle"],
                            dry_run=args.dry_run) else 1

    failures = 0
    published = 0
    if shutil.which("gh") is None:
        print("note: gh not found — every tagged version is assumed unreleased")
    for tag in tagged_versions():
        version = tag[1:]
        if version not in sections:
            print(f"skip {tag}: no CHANGELOG section")
            continue
        exists = release_exists(tag)
        if exists:
            print(f"skip {tag}: release exists")
            continue
        section = sections[version]
        if publish(tag, section["body"], section["subtitle"], dry_run=args.dry_run):
            published += 1
        else:
            failures += 1

    print(f"{published} published, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
