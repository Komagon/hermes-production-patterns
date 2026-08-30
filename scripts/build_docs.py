# -*- coding: utf-8 -*-
"""Generate docs/ for mkdocs by copying repo markdown (idempotent).

Keeps directory shape identical to repo root (conventions/, patterns/,
examples/) so all relative links & asset paths keep working.

Skill OS inspired additions (see vault: Hermes Skill OS 升级优化路线图):
- router.md       : MASTER-ROUTING style decision entry, derived from
                    frontmatter descriptions of every convention
- skill-graph.md  : Skill Graph rendered as inline SVG from related_skills
- contract cards  : per-convention Skill Contract (version/category/related)
- --check-nav     : regression gate, every docs page must appear in nav
"""
import math
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)

SECTION_INDEXES = {
    "patterns": ("方法论 Patterns", "先读这里：项目的思想源流——12-Factor Agents、Loop Engineering、成熟度评估。"),
    "conventions": ("工程公约 Conventions", "可独立采用的工程公约，每条回答一个生产问题。新读者建议从 Maker/Checker 或 Cron 模式开始。"),
    "examples": ("实战案例 Examples", "多个公约在真实工作流中的组合应用。每个案例含完整技能目录，可直接 copy 改造。"),
}

# page stem -> docs dir (for cross-folder relative links)
DIR_OF = {}


def parse_meta(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    fm = m.group(0) if m else ""

    def grab(key: str):
        mm = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
        return mm.group(1).strip().strip('"').strip("'") if mm else None

    rel = re.search(r"related_skills:\s*\[([^\]]*)\]", fm)
    return {
        "version": grab("version"),
        "description": grab("description"),
        "category": (re.search(r"category:\s*(\S+)", fm) or [None, None])[1]
        if re.search(r"category:\s*(\S+)", fm)
        else None,
        "related": [s.strip() for s in rel.group(1).split(",")] if rel else [],
    }


def collect_meta(sub: str) -> dict:
    out = {}
    for f in sorted((ROOT / sub).glob("*.md")):
        meta = parse_meta(f.read_text(encoding="utf-8"))
        meta["file"] = f.name
        out[f.stem] = meta
        DIR_OF.setdefault(f.stem, sub)
    return out


def contract_block(meta: dict) -> str:
    bits = []
    if meta.get("version"):
        bits.append(f"版本 **v{meta['version']}**")
    if meta.get("category"):
        bits.append(f"分类 `{meta['category']}`")
    chips = []
    for r in meta.get("related", []):
        r = r.strip()
        if not r:
            continue
        d = DIR_OF.get(r)
        if not d:
            continue
        href = f"{r}.md" if d == "conventions" else f"../{d}/{r}.md"
        chips.append(f"[{r}]({href})")
    if chips:
        bits.append("相关 " + " · ".join(chips))
    if not bits:
        return ""
    return (
        '\n??? abstract "Skill Contract（本模式的模块声明）"\n'
        f"    {' ｜ '.join(bits)}\n"
    )


def inject_contract(sub: str, metas: dict) -> None:
    for stem, meta in metas.items():
        path = DOCS / sub / meta["file"]
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        block = contract_block(meta)
        if not block:
            continue
        m = re.search(r"^# .+$", text, re.M)
        if not m:
            continue
        pos = m.end()
        path.write_text(text[:pos] + "\n" + block + text[pos:], encoding="utf-8")


def make_router(metas: dict) -> None:
    lines = [
        "# 路由入口 Pattern Router",
        "",
        "> 借鉴 Skill OS 的 MASTER ROUTING 思想：先按场景信号定位入口公约，再沿相关模式扩展。",
        "> 本页由 `scripts/build_docs.py` 从各公约 frontmatter 自动生成，勿手工编辑。",
        "",
        "## 场景 → 公约",
        "",
        "| 你遇到的问题 | 入口公约 | 配套模式 |",
        "| --- | --- | --- |",
    ]
    for stem in sorted(metas):
        meta = metas[stem]
        desc = meta.get("description") or stem
        if "—" in desc:
            signal = desc.split("—", 1)[1].strip()
        elif "-" in desc:
            signal = desc.split("-", 1)[1].strip()
        else:
            signal = desc
        signal = signal.replace("|", "／")
        href_stem = f"conventions/{stem}.md"
        chips = []
        for r in meta.get("related", []):
            r = r.strip()
            d = DIR_OF.get(r)
            if r and d:
                href = f"conventions/{r}.md" if d == "conventions" else f"{d}/{r}.md"
                chips.append(f"[{r}]({href})")
        related = " · ".join(chips[:4]) if chips else "—"
        lines.append(f"| {signal} | [{stem}]({href_stem}) | {related} |")
    lines += [
        "",
        "## 下一步",
        "",
        "- 想看多公约如何组合：[模式组合指南](conventions/pattern-composition.md)",
        "- 想看真实工作流：[实战案例](examples/index.md)",
        "- 想看能力总览：[模式图谱](skill-graph.md)",
        "",
    ]
    (DOCS / "router.md").write_text("\n".join(lines), encoding="utf-8")


def make_graph(site_url: str, metas: dict) -> None:
    prefix = re.sub(r"https?://[^/]+", "", site_url).rstrip("/") or "."
    names = [s for s in sorted(metas)]
    n = len(names)
    size = 720
    c = size / 2
    r = c - 110
    pos = {}
    for i, name in enumerate(names):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        pos[name] = (c + r * math.cos(ang), c + r * math.sin(ang))

    def label(stem: str) -> str:
        desc = metas[stem].get("description") or stem
        # titles sit left of the full-width em dash; don't cut on hyphens
        # inside words like "Anti-Patterns"
        left = re.split(r"\s*—\s*", desc, 1)[0].strip()
        return left or stem

    edges = []
    seen = set()
    for stem, meta in metas.items():
        for rel in meta.get("related", []):
            rel = rel.strip()
            if rel in metas:
                key = frozenset((stem, rel))
                if key not in seen:
                    seen.add(key)
                    edges.append((stem, rel))

    parts = [
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto">',
    ]
    for a, b in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        parts.append(
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="currentColor" stroke-opacity="0.18" stroke-width="1.5"/>'
        )
    for name in names:
        x, y = pos[name]
        import html as _html
        href = f"{prefix}/conventions/{name}/"
        anchor = "start" if x < c - 40 else ("end" if x > c + 40 else "middle")
        parts.append(
            f'<a href="{href}"><circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="currentColor" fill-opacity="0.75"/>'
            f'<text x="{x:.0f}" y="{y + 18:.0f}" text-anchor="{anchor}" font-size="13" fill="currentColor">{_html.escape(label(name))}</text></a>'
        )
    parts.append("</svg>")

    doc = [
        "# 模式图谱 Skill Graph",
        "",
        "> 借鉴 Skill OS 的 Skill Graph 思想：公约不是孤立的 Prompt，而是互相引用的能力模块。",
        "> 连线 = frontmatter `related_skills` 声明（自动提取，构建期生成，无外部依赖）；点击节点进入对应公约。",
        "",
        "".join(parts),
        "",
        f"共 {n} 个工程公约节点、{len(edges)} 条关联。图谱仅覆盖公约间互链；跨类型引用（案例等）见各页 Skill Contract 卡。",
        "",
    ]
    (DOCS / "skill-graph.md").write_text("\n".join(doc), encoding="utf-8")


def read_site_url() -> str:
    t = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    m = re.search(r"^site_url:\s*(\S+)", t, re.M)
    return m.group(1) if m else "/"


def check_nav() -> int:
    yml = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    nav_part = yml[yml.index("\nnav:"):]
    # nav lines look like `- path.md` or `- 标题: path.md`; a .md path always
    # ends the line, so anchoring at EOL cleanly avoids matching titles.
    pages = set(re.findall(r"([A-Za-z0-9_\-./]+\.md)\s*$", nav_part, re.M))
    docs_pages = {str(p.relative_to(DOCS)) for p in DOCS.rglob("*.md")}
    missing = sorted(docs_pages - pages)
    unknown = sorted(pages - docs_pages)
    if missing:
        print("check-nav FAIL: 页面存在但未进 nav:", missing)
    if unknown:
        print("check-nav FAIL: nav 引用了不存在的页面:", unknown)
    if missing or unknown:
        return 1
    print(f"check-nav PASS: {len(docs_pages)} 个页面全部在 nav 中")
    return 0


def copy_tree(sub: str) -> None:
    src, dst = ROOT / sub, DOCS / sub
    dst.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.rglob("*.md")):
        rel = f.relative_to(src)
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        text = f.read_text(encoding="utf-8")
        # repo-internal dir links like ../../conventions/ -> index page
        text = re.sub(r"\]\((\.\./\.\./conventions)/\)", r"](../../conventions/index.md)", text)
        (dst / rel).write_text(text, encoding="utf-8")


def make_home() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    text = re.sub(r'src="(?!http)[^"]*assets/logo\.png"', 'src="logo.png"', text)
    text = re.sub(r'srcset="(?!http)[^"]*assets/logo\.png"', 'srcset="logo.png"', text)
    text = text.replace("(README.en.md)", "(readme-en.md)")
    (DOCS / "index.md").write_text(text, encoding="utf-8")


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
        parts += [f"## {f.name}", "", "```" + lang, f.read_text(encoding="utf-8").rstrip("\n"), "```", ""]
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
    if "--check-nav" in sys.argv:
        if not DOCS.exists():
            print("check-nav: docs/ 不存在，先运行 build_docs.py")
            return 1
        return check_nav()

    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    shutil.copy2(ROOT / "assets" / "logo.png", DOCS / "logo.png")
    for sub in ("conventions", "patterns", "examples"):
        copy_tree(sub)
    for root_md in ("ARCHITECTURE.md", "CONTEXT.md", "CHANGELOG.md", "CONTRIBUTING.md"):
        shutil.copy2(ROOT / root_md, DOCS / root_md)

    conv_metas = collect_meta("conventions")
    collect_meta("patterns")
    collect_meta("examples")
    inject_contract("conventions", conv_metas)
    make_router(conv_metas)
    make_graph(read_site_url(), conv_metas)

    write_section_indexes()
    make_templates_page()
    (DOCS / "readme-en.md").write_text(
        (ROOT / "README.en.md").read_text(encoding="utf-8").replace("(README.md)", "(index.md)"),
        encoding="utf-8",
    )
    make_home()
    n = sum(1 for _ in DOCS.rglob("*.md"))
    print(f"docs/ generated: {n} markdown pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
