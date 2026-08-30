# -*- coding: utf-8 -*-
"""Generate docs/ for mkdocs by copying repo markdown (idempotent).

Keeps directory shape identical to repo root (conventions/, patterns/,
examples/, templates/) so all relative links & asset paths keep working.
Adds a docs/index.md derived from README.md (assets rebased, EN tab page).
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)


def copy_tree(sub: str) -> None:
    src, dst = ROOT / sub, DOCS / sub
    dst.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.rglob("*.md")):
        rel = f.relative_to(src)
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        text = f.read_text(encoding="utf-8")
        # repo-internal dir links like ../../conventions/ -> index page
        text = re.sub(r"\]\((\.\./\.\./conventions)/\)", r"](../../conventions/index.md)", text)
        (dst / rel).write_text(text, encoding="utf-8")  # links: pre-segmentation, raw


def make_home() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    # markdownlint may require blank line; README assets are root-relative
    text = re.sub(r'src="(?!http)[^"]*assets/logo\.png"', 'src="logo.png"', text)
    text = re.sub(r'srcset="(?!http)[^"]*assets/logo\.png"', 'srcset="logo.png"', text)
    text = text.replace("(README.en.md)", "(readme-en.md)")
    (DOCS / "index.md").write_text(text, encoding="utf-8")


SECTION_INDEXES = {
    "patterns": ("方法论 Patterns", "先读这里：项目的思想源流——12-Factor Agents、Loop Engineering、成熟度评估。"),
    "conventions": ("工程公约 Conventions", "可独立采用的工程公约，每条回答一个生产问题。新读者建议从 Maker/Checker 或 Cron 模式开始。"),
    "examples": ("实战案例 Examples", "多个公约在真实工作流中的组合应用。每个案例含完整技能目录，可直接 copy 改造。"),
}


def make_templates_page() -> None:
    """mkdocs excludes any dir named templates/ by default — inline them here."""
    parts = [
        "# 模板 Templates",
        "",
        "> SKILL.md / STATE.md / AGENTS.md 起手模板，直接复制到新项目使用。",
        "",
    ]
    for f in sorted((ROOT / "templates").iterdir()):
        lang = "yaml" if f.suffix in (".yml", ".yaml") else "markdown"
        parts += [
            f"## {f.name}",
            "",
            "```" + lang,
            f.read_text(encoding="utf-8").rstrip("\n"),
            "```",
            "",
        ]
    (DOCS / "templates.md").write_text("\n".join(parts), encoding="utf-8")


def write_section_indexes() -> None:
    for sub, (title, blurb) in SECTION_INDEXES.items():
        files = sorted((ROOT / sub).glob("*.md"))
        lines = [f"# {title}", "", f"> {blurb}", "", "## 清单", ""]
        for f in files:
            text = FRONTMATTER_RE.sub("", f.read_text(encoding="utf-8"), count=1)
            h1 = re.search(r"^# (.+)$", text, re.M)
            name = h1.group(1).strip() if h1 else f.stem
            lines.append(f"- [{name}]({f.name})")
        (DOCS / sub / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    shutil.copy2(ROOT / "assets" / "logo.png", DOCS / "logo.png")
    for sub in ("conventions", "patterns", "examples"):
        copy_tree(sub)
    make_templates_page()
    for root_md in ("ARCHITECTURE.md", "CONTEXT.md", "CHANGELOG.md", "CONTRIBUTING.md"):
        shutil.copy2(ROOT / root_md, DOCS / root_md)
    write_section_indexes()
    (DOCS / "readme-en.md").write_text(
        (ROOT / "README.en.md")
        .read_text(encoding="utf-8")
        .replace("(README.md)", "(index.md)"),
        encoding="utf-8",
    )
    make_home()
    n = sum(1 for _ in DOCS.rglob("*.md"))
    print(f"docs/ generated: {n} markdown pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
