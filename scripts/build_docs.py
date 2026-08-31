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

Website V2 additions (see vault: Hermes Production Patterns Website 任务书):
- index.md        : generated Landing (10 modules, §6) — README moved to
                    readme.md so nothing is deleted (§37)
- patterns-library.md : Explorer with category filter + keyword search (§25)
- architecture-page.md: Production Architecture with Normal/Error flow (§19-20)
- decision layout  : per-convention kicker + meta bar + when(Not) cards (§15-18)
- interactive graph: hover highlight data hooks on skill-graph SVG (§11)
Content rule (§36): all pattern-level data comes from frontmatter/body
parsing; only brand copy (hero, 6-problem frame) lives in template constants.
"""
import html as _html
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

# ---------------------------------------------------------------------------
# V2 品牌层常量（任务书 §9/§10/§21/§23 指定文案；允许硬编码的唯一内容）
# ---------------------------------------------------------------------------

# §9 Why Agents Fail: (no, title_en, stmt_en, 中文, 入口公约, 解法标签)
PROBLEMS = [
    ("01", "State Loss", "SESSION ENDS. THE AGENT FORGETS EVERYTHING.",
     "会话结束，Agent 忘记一切。", "state-file-pattern", "State File"),
    ("02", "Silent Failure", "THE AGENT FAILED. NOBODY KNOWS.",
     "任务失败了，没有人知道。", "maker-checker", "Maker / Checker"),
    ("03", "Cron Drift", "THE JOB RUNS. BUT NOT AS EXPECTED.",
     "任务在跑，但不是预期的样子。", "cron-job-pattern", "Cron Job"),
    ("04", "Context Explosion", "ERRORS KEEP ACCUMULATING. CONTEXT KEEPS GROWING.",
     "错误不断堆积，上下文持续膨胀。", "error-compact-pattern", "Error Compact"),
    ("05", "Self Validation", "THE AGENT VALIDATES ITSELF. THE VALIDATION IS NOT INDEPENDENT.",
     "自己给自己打分，验证并不独立。", "maker-checker", "Maker / Checker"),
    ("06", "Skill Regression", "NEW SKILL. OLD CAPABILITY BREAKS.",
     "新模式上线，旧能力回归了。", "evolution-gate", "Evolution Gate"),
]

# §10 Problem -> Pattern -> Result (6 条, 与 §9 六问题一一对应)
CHAINS = [
    ("STATE LOSS", "STATE FILE", "PERSISTENT AGENT", "state-file-pattern"),
    ("SILENT FAILURE", "MAKER / CHECKER", "INDEPENDENT VALIDATION", "maker-checker"),
    ("CRON RUNS WRONG", "CRON JOB", "RELIABLE AUTOMATION", "cron-job-pattern"),
    ("CONTEXT EXPLOSION", "ERROR COMPACT", "BOUNDED CONTEXT", "error-compact-pattern"),
    ("SELF VALIDATION", "MAKER / CHECKER", "INDEPENDENT GATE", "maker-checker"),
    ("SKILL REGRESSION", "EVOLUTION GATE", "VERIFIED EVOLUTION", "evolution-gate"),
]

# §21 成熟度阶梯
MATURITY_STEPS = ["PROMPT", "SKILL", "LOOP", "STATEFUL AGENT", "VERIFIED AGENT", "AUTONOMOUS AGENT"]
MATURITY_LEVELS = [
    ("L1", "Assistant", "人触发、人检查、人兜底。Prompt 与 Skill 即可起步。",
     [("State File", "state-file-pattern")]),
    ("L2", "Copilot", "定时自主运行，输出经独立验证，失败可恢复。",
     [("Cron Job", "cron-job-pattern"), ("Maker / Checker", "maker-checker"),
      ("Checkpoint", "checkpoint-pattern")]),
    ("L3", "Autonomous Agent", "长期进化：可观测、可回归、可安全自我更新。",
     [("Memory OS", "memory-os-pattern"), ("Evolution Gate", "evolution-gate"),
      ("Self Update", "self-update-pattern")]),
]

# §23 Choose Your Path
PATHS = [
    ("BEGINNER", "I'M NEW TO AGENT ENGINEERING",
     [("01 State", "state-file-pattern"), ("02 Cron", "cron-job-pattern"),
      ("03 Maker / Checker", "maker-checker")]),
    ("AUTOMATION BUILDER", "I'M BUILDING AUTOMATION",
     [("Cron", "cron-job-pattern"), ("State", "state-file-pattern"),
      ("Checkpoint", "checkpoint-pattern")]),
    ("PRODUCTION ENGINEER", "I'M BUILDING AUTONOMOUS AGENTS",
     [("Monitor", "cron-job-pattern"), ("Memory", "memory-os-pattern"),
      ("Checker", "maker-checker"), ("Evolution", "evolution-gate")]),
]

FEATURED = ["maker-checker", "state-file-pattern", "cron-job-pattern"]

CAT_LABEL = {
    "state": "STATE", "quality": "QUALITY", "automation": "AUTOMATION",
    "memory": "MEMORY", "reliability": "RELIABILITY", "evolution": "EVOLUTION",
    "security": "SECURITY", "guide": "GUIDE", "meta": "GUIDE",
}
CAT_ORDER = ["state", "quality", "automation", "memory", "reliability", "evolution", "security", "guide"]
METER = {"reliability": {"high": 5, "medium": 3, "low": 2},
         "complexity": {"low": 2, "medium": 3, "high": 4}}
REPO_URL = "https://github.com/Komagon/hermes-production-patterns"


def esc(s):
    return _html.escape(str(s), quote=True)


def parse_meta(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    fm = m.group(0) if m else ""

    def grab(key: str):
        mm = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
        return mm.group(1).strip().strip('"').strip("'") if mm else None

    def grab_list(key: str):
        mm = re.search(rf"^{key}:\s*\[([^\]]*)\]", fm, re.M)
        return [s.strip().strip('"').strip("'") for s in mm.group(1).split(",") if s.strip()] if mm else []

    rel = re.search(r"related_skills:\s*\[([^\]]*)\]", fm)
    return {
        "version": grab("version"),
        "description": grab("description"),
        "category": (re.search(r"category:\s*(\S+)", fm) or [None, None])[1]
        if re.search(r"category:\s*(\S+)", fm)
        else None,
        "related": [s.strip() for s in rel.group(1).split(",")] if rel else [],
        # --- V2 扩展键（全部可选，缺省安全, §36 元数据增强路径） ---
        "hpp_category": (grab("hpp_category") or "meta").lower(),
        "maturity": grab("hpp_maturity"),
        "complexity": grab("hpp_complexity"),
        "reliability": grab("hpp_reliability"),
        "capability": grab("hpp_capability"),
        "en": grab("hpp_en"),
        "when_use": grab_list("hpp_when_to_use"),
        "when_not": grab_list("hpp_when_not_to_use"),
    }


def collect_meta(sub: str) -> dict:
    out = {}
    for f in sorted((ROOT / sub).glob("*.md")):
        meta = parse_meta(f.read_text(encoding="utf-8"))
        meta["file"] = f.name
        out[f.stem] = meta
        DIR_OF.setdefault(f.stem, sub)
    return out


def title_of(stem: str, meta: dict) -> str:
    desc = meta.get("description") or stem
    return (re.split(r"\s*—\s*", desc, 1)[0].strip() or stem)


def signal_of(meta: dict, stem: str) -> str:
    desc = meta.get("description") or stem
    if "—" in desc:
        return desc.split("—", 1)[1].strip()
    if "-" in desc:
        return desc.split("-", 1)[1].strip()
    return desc


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


def dots(n: int, cls: str) -> str:
    n = max(0, min(5, n))
    return (
        f'<span class="hpp-pcard__meter {cls}">'
        + "".join(f'<i class="{"on" if i < n else ""}"></i>' for i in range(5))
        + "</span>"
    )


def decision_blocks(stem: str, meta: dict):
    """§15-§18: kicker(插到 H1 前) + meta bar + when/when-not(插到 H1 后)."""
    cat = meta.get("hpp_category") or "meta"
    label = CAT_LABEL.get(cat, cat.upper())
    kicker = (
        f'<p class="hpp-kicker cat-{cat}"><span class="hpp-kicker__dot"></span>'
        f"{esc(label)} PATTERN</p>\n\n"
    )
    rows = []
    for k, key in (("Maturity", "maturity"), ("Complexity", "complexity"),
                   ("Reliability", "reliability"), ("Hermes", "capability")):
        v = meta.get(key)
        if v:
            rows.append(f"<div><dt>{k}</dt><dd>{esc(v)}</dd></div>")
    if meta.get("version"):
        rows.append(f"<div><dt>Version</dt><dd>v{esc(meta['version'])}</dd></div>")
    bar = ('<dl class="hpp-meta-bar">' + "".join(rows) + "</dl>\n\n") if rows else ""
    wtu = ""
    if meta.get("when_use") or meta.get("when_not"):
        cols = []
        if meta.get("when_use"):
            cols.append('<div class="hpp-wtu__col hpp-wtu__col--yes"><h4>When to Use</h4><ul>'
                        + "".join(f"<li>{esc(i)}</li>" for i in meta["when_use"]) + "</ul></div>")
        if meta.get("when_not"):
            cols.append('<div class="hpp-wtu__col hpp-wtu__col--no"><h4>When NOT to Use</h4><ul>'
                        + "".join(f"<li>{esc(i)}</li>" for i in meta["when_not"]) + "</ul></div>")
        wtu = '<div class="hpp-wtu">' + "".join(cols) + "</div>\n\n"
    return kicker, bar + wtu


def inject_contract(sub: str, metas: dict) -> None:
    for stem, meta in metas.items():
        path = DOCS / sub / meta["file"]
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        block = contract_block(meta)
        kicker, decision = decision_blocks(stem, meta)
        if not block and not decision:
            continue
        m = re.search(r"^# .+$", text, re.M)
        if not m:
            continue
        pos = m.end()
        after = "\n" + decision + block if block else "\n" + decision
        text = text[:m.start()] + kicker + text[m.start():pos] + after + text[pos:]
        path.write_text(text, encoding="utf-8")


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
        "## Problem → Diagnosis(描述你的问题,拿推荐组合)",
        "",
        "> 用自己的话描述症状,按最像的一条进入。这是 Router 2.0:先问题,后模式。",
        "",
    ]
    # (症状关键词, 诊断, 推荐 Stack, 落地 kit 页锚点)
    DIAGNOSES = [
        ("Agent 重启后忘记任务进度 / 断片",
         "State Loss — 状态没有跨运行持久化",
         "🟢 Starter Stack(State + Control Flow)",
         "basic-agent"),
        ("Cron 任务跑着跑着跑偏 / 重复执行 / 静默失败",
         "Cron Drift + Silent Failure",
         "🟡 Reliable Automation Stack(Cron + State + Error Compact + Checkpoint)",
         "cron-production"),
        ("Agent 输出质量不稳定,全靠肉眼审查 / 自己验自己",
         "Self Validation — 验证不独立",
         "🔵 Quality Stack(Maker/Checker + Red Flags + Regression)",
         "maker-checker"),
        ("报告/结论没有出处,数据可能是编的",
         "Evidence Discipline 缺失",
         "🔵 Quality Stack + 证据条目(evidence.jsonl)",
         "research-agent"),
        ("上次踩过的坑这次又踩 / 会话之间没有积累",
         "Memory 缺失 — 经验没有沉淀",
         "🟣 Memory Stack(五层记忆 + 检索 + 复盘)",
         "memory-agent"),
        ("每次改 prompt 都像赌博,不知道会不会改坏",
         "无基线无回归 — 改动不可验证",
         "🔴 Evolution Stack(Metrics + Gate + Regression + Rollback)",
         "self-evolving-agent"),
        ("多个 Agent 协作互相等待 / 接缝出错",
         "契约与状态总线缺失",
         "🔵 Quality Stack + 文件租约 + 状态总线",
         "maker-checker"),
    ]
    for symptom, diag, stack, kit in DIAGNOSES:
        symptom = symptom.replace("|", "／")
        lines.append(f"| {symptom} | {diag} | {stack} | [starter-kit](starter-kits.md#kit-{kit}) |")
    lines += [
        "",
        "## 下一步",
        "",
        "- 10 分钟跑通第一个 Production Agent:[Quick Start](quickstart.md)",
        "- 官方推荐组合:[Production Stacks](stacks/starter.md)",
        "- 想看多公约如何组合：[模式组合指南](conventions/pattern-composition.md)",
        "- 想看真实工作流：[实战案例](examples/index.md)",
        "- 想看能力总览：[模式图谱](skill-graph.md)",
        "",
    ]
    (DOCS / "router.md").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# 图谱与架构图 (构建期内联 SVG, 无外部依赖)
# ---------------------------------------------------------------------------

def graph_svg(site_url: str, metas: dict) -> str:
    prefix = re.sub(r"https?://[^/]+", "", site_url).rstrip("/") or "."
    # 按分类分组环排: 同类/强关联节点相邻, 长边减少, 结构可读 (§11)
    def cat_key(stem):
        c = metas[stem].get("hpp_category") or "meta"
        return (CAT_ORDER.index(c) if c in CAT_ORDER else 99, stem)
    names = sorted(metas, key=cat_key)
    n = len(names)
    size = 980
    c = size / 2
    r = c - 190
    pos = {}
    for i, name in enumerate(names):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        pos[name] = (c + r * math.cos(ang), c + r * math.sin(ang))

    def label(stem: str) -> str:
        """按近似渲染宽度截断(中文≈15px/字,西文≈8px/字),预算 210px."""
        t = title_of(stem, metas[stem])
        def w(s):
            return sum(15 if ord(ch) > 0x2E7F else 8 for ch in s)
        if w(t) <= 210:
            return t
        acc = ""
        for ch in t:
            if w(acc + ch + "…") > 210:
                return acc.rstrip(" (（") + "…"
            acc += ch
        return acc

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
        # viewBox 四周留 240/180 安全边距: 环外侧标签不溢出画布
        f'<svg viewBox="-240 -180 {size + 480} {size + 360}" width="100%" style="max-width:{size + 480}px;height:auto" xmlns="http://www.w3.org/2000/svg" class="hpp-graph" data-edges="1" role="img" aria-label="工程公约关联图谱：{n} 个节点，{len(edges)} 条关联，按分类环排">',
    ]
    # 弦式曲边(向圆心微收)
    for a, b in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        qx = (x1 + x2) / 2 + (c - (x1 + x2) / 2) * 0.35
        qy = (y1 + y2) / 2 + (c - (y1 + y2) / 2) * 0.35
        parts.append(
            f'<path class="hpp-edge" data-from="{a}" data-to="{b}" d="M{x1:.0f} {y1:.0f} Q{qx:.0f} {qy:.0f} {x2:.0f} {y2:.0f}"/>'
        )
    # 中心品牌区: 底圆遮断穿心连线
    parts.append(
        f'<circle cx="{c}" cy="{c}" r="118" fill="var(--hpp-bg-secondary, #0d1117)" opacity="0.92"/>'
        f'<text x="{c}" y="{c - 10}" text-anchor="middle" font-size="15" letter-spacing="4" fill="#57606a">PATTERNS</text>'
        f'<text x="{c}" y="{c + 16}" text-anchor="middle" font-size="15" letter-spacing="4" fill="#57606a">WORK TOGETHER</text>'
    )
    for i, name in enumerate(names):
        x, y = pos[name]
        dx, dy = x - c, y - c
        ln = math.hypot(dx, dy) or 1
        # 标签双环错位: 奇偶节点放不同半径, 消除相邻水平碰撞
        off = 30 if i % 2 == 0 else 62
        lx = x + dx / ln * off
        ly = y + dy / ln * off + 5
        cosv = dx / ln
        anchor = "start" if cosv > 0.25 else ("end" if cosv < -0.25 else "middle")
        cat = metas[name].get("hpp_category") or "meta"
        href = f"{prefix}/conventions/{name}/"
        tip = esc(signal_of(metas[name], name))
        parts.append(
            f'<g class="hpp-node cat-{cat}" data-id="{name}" tabindex="0">'
            f'<a href="{href}"><circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="currentColor" fill-opacity="0.9" stroke="currentColor" stroke-opacity="0.35"/>'
            f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="{anchor}" font-size="15" fill="currentColor">{esc(label(name))}</text>'
            f'<title>{tip}</title></a></g>'
        )
    parts.append("</svg>")
    return "".join(parts)


def make_graph(site_url: str, metas: dict) -> None:
    n = len(metas)
    doc = [
        "# 模式图谱 Skill Graph",
        "",
        "> 借鉴 Skill OS 的 Skill Graph 思想：公约不是孤立的 Prompt，而是互相引用的能力模块。",
        "> 连线 = frontmatter `related_skills` 声明（自动提取，构建期生成，无外部依赖）；点击节点进入对应公约；悬停节点高亮其关联。",
        "",
        graph_svg(site_url, metas),
        "",
        f"共 {n} 个工程公约节点。图谱仅覆盖公约间互链；跨类型引用（案例等）见各页 Skill Contract 卡。",
        "",
    ]
    (DOCS / "skill-graph.md").write_text("\n".join(doc), encoding="utf-8")


ARCH_NODES = [  # (id, x, y, w, h, label, sub)
    ("scheduler", 150, 16, 180, 44, "SCHEDULER", "Cron Job Pattern"),
    ("maker", 150, 122, 180, 44, "MAKER", "生成 · Control Flow"),
    ("checker", 150, 228, 180, 44, "CHECKER", "独立验证 · Maker/Checker"),
    ("state", 150, 366, 180, 44, "STATE", "State File · Checkpoint"),
    ("notifier", 150, 472, 180, 44, "NOTIFIER", "Monitor · 交付"),
    ("retry", 388, 228, 148, 44, "RETRY", "Error Compact"),
    ("human", 388, 366, 148, 44, "HUMAN GATE", "人工升级"),
]
ARCH_EDGES = [  # (from, to, label, cls)
    ("scheduler", "maker", "", ""),
    ("maker", "checker", "", ""),
    ("checker", "state", "PASS", "hpp-e-pass"),
    ("state", "notifier", "", ""),
    ("checker", "retry", "FAIL", "hpp-e-fail"),
    ("retry", "maker", "修正重试", "hpp-e-fail"),
    ("retry", "human", "超限", "hpp-e-fail"),
]
NODE_POS = {k: (x, y, w, h) for k, x, y, w, h, _, _ in ARCH_NODES}


def arch_svg(flow: bool = True) -> str:
    parts = [
        '<svg viewBox="0 0 586 532" width="586" height="532" xmlns="http://www.w3.org/2000/svg" '
        'class="hpp-graph hpp-arch-svg" style="max-width:100%;height:auto" role="img" '
        'aria-label="生产架构：Scheduler 触发 Maker 生成，Checker 独立验证，PASS 写入 State 并通知，FAIL 压缩错误后重试，超限升级人工">',
        '<defs><marker id="hpp-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0 0L10 5L0 10z" fill="#33404d"/></marker>'
        '<marker id="hpp-arrow-err" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0 0L10 5L0 10z" fill="#ff6b6b"/></marker></defs>',
    ]
    for a, b, lab, cls in ARCH_EDGES:
        ax, ay, aw, ah = NODE_POS[a]
        bx, by, bw, bh = NODE_POS[b]
        if bx == ax:  # vertical
            x1, y1, x2, y2 = ax + aw / 2, ay + ah, bx + bw / 2, by
        elif b == "maker":  # retry -> maker 回边: 从 maker 右侧接入,不穿盒
            x1, y1 = ax + aw, ay + ah / 2      # retry 右缘
            x2, y2 = bx + bw, by + bh / 2      # maker 右缘
            mx = x1 + 28
            parts.append(
                f'<path class="hpp-a-edge {cls} hpp-flow" d="M{x1:.0f} {y1:.0f} H{mx:.0f} V{y2:.0f} H{x2 + 2:.0f}"/>'
            )
            parts.append(
                f'<text class="hpp-a-edge-label" x="{mx + 8:.0f}" y="{(y1 + y2) / 2:.0f}" text-anchor="start">{esc(lab or "修正重试")}</text>'
            )
            continue
        else:  # horizontal
            x1, y1 = ax + aw, ay + ah / 2
            x2, y2 = bx, by + bh / 2
        parts.append(f'<line class="hpp-a-edge {cls}{" hpp-flow" if flow and cls == "" else ""}" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"/>')
        if lab:
            lx = (x1 + x2) / 2
            ly = (y1 + y2) / 2 - 8 if y2 > y1 else (y1 + y2) / 2 + 4
            parts.append(f'<text class="hpp-a-edge-label" x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle">{esc(lab)}</text>')
    for _k, x, y, w, h, lab, sub in ARCH_NODES:
        parts.append(
            f'<g class="hpp-a-node"><a href="#">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
            f'<text x="{x + w / 2:.0f}" y="{y + 19:.0f}" text-anchor="middle" font-weight="700">{esc(lab)}</text>'
            f'<text class="hpp-a-sub" x="{x + w / 2:.0f}" y="{y + 35:.0f}" text-anchor="middle">{esc(sub)}</text>'
            f"</a></g>"
        )
    parts.append("</svg>")
    return "".join(parts)


def arch_svg_link(site_url: str) -> str:
    """架构图节点可点击跳转到对应公约 (§8 节点=Pattern 入口)."""
    prefix = re.sub(r"https?://[^/]+", "", site_url).rstrip("/") or "."
    href_of = {
        "scheduler": "cron-job-pattern", "maker": "maker-checker", "checker": "maker-checker",
        "state": "state-file-pattern", "notifier": "cron-job-pattern",
        "retry": "error-compact-pattern", "human": "anti-patterns",
    }
    svg = arch_svg()
    out = []
    i = 0
    for k, *_rest in ARCH_NODES:
        seg_start = svg.index('<g class="hpp-a-node">', i)
        seg_end = svg.index("</g>", seg_start) + 4
        seg = svg[seg_start:seg_end]
        stem = href_of[k]
        seg = seg.replace('href="#"', f'href="{prefix}/conventions/{stem}/"')
        out.append(svg[i:seg_start] + seg)
        i = seg_end
    out.append(svg[i:])
    return "".join(out)


# ---------------------------------------------------------------------------
# Pattern 卡片
# ---------------------------------------------------------------------------

def card_search_blob(stem: str, meta: dict) -> str:
    bits = [stem, title_of(stem, meta), signal_of(meta, stem), meta.get("en") or "",
            meta.get("capability") or "", meta.get("hpp_category") or ""]
    return " ".join(bits).lower()


def pattern_card(stem: str, meta: dict, base: str, featured: bool = False) -> str:
    cat = meta.get("hpp_category") or "meta"
    rel = METER["reliability"].get((meta.get("reliability") or "").lower(), 3)
    cmpx = METER["complexity"].get((meta.get("complexity") or "").lower(), 3)
    href = f"{base}/conventions/{stem}/"
    one = meta.get("en") or signal_of(meta, stem)
    cls = "hpp-card hpp-pcard hpp-reveal" + (" hpp-pcard--featured" if featured else "")
    cap = f'<span class="hpp-chip">HERMES · {esc(meta["capability"])}</span>' if meta.get("capability") else ""
    mat = f'<span class="hpp-chip">{esc(meta["maturity"])}</span>' if meta.get("maturity") else ""
    return (
        f'<div class="{cls}" style="--hpp-cat:var(--hpp-cat-{cat})" data-cat="{cat}" data-search="{esc(card_search_blob(stem, meta))}">'
        f'<p class="hpp-kicker cat-{cat}"><span class="hpp-kicker__dot"></span>{esc(CAT_LABEL.get(cat, cat.upper()))}</p>'
        f'<h3 class="hpp-card__title"><a href="{href}">{esc(title_of(stem, meta))}</a></h3>'
        f'<p class="hpp-card__body">{esc(one)}</p>'
        f'<p class="hpp-card__body" style="font-size:0.78rem">{esc(signal_of(meta, stem))}</p>'
        f"<div>{mat}{cap}</div>"
        f'<div class="hpp-pcard__dots"><span>RELIABILITY {dots(rel, "r")}</span><span>COMPLEXITY {dots(cmpx, "c")}</span></div>'
        f'<a class="hpp-card__link cat-{cat}" href="{href}">→ VIEW PATTERN</a>'
        "</div>"
    )


# ---------------------------------------------------------------------------
# 首页 Landing (§6 十模块)
# ---------------------------------------------------------------------------

def problem_cards(base: str, metas: dict) -> str:
    out = []
    for no, t_en, stmt, zh, stem, fix in PROBLEMS:
        cat = metas[stem].get("hpp_category") if stem in metas else "meta"
        out.append(
            f'<div class="hpp-card hpp-reveal" style="--hpp-cat:var(--hpp-cat-{cat})">'
            f'<span class="hpp-card__num">PROBLEM {no}</span>'
            f'<h3 class="hpp-card__title">{esc(t_en.upper())}</h3>'
            f'<p class="hpp-card__stmt">{esc(stmt)}</p>'
            f'<p class="hpp-card__body">{esc(zh)}</p>'
            f'<a class="hpp-fix cat-{cat}" href="{base}/conventions/{stem}/" '
            f'style="--hpp-cat:var(--hpp-cat-{cat})">→ {esc(fix.upper())}</a>'
            "</div>"
        )
    return "".join(out)


def chain_rows() -> str:
    out = []
    for p, pat, res, stem in CHAINS:
        out.append(
            f'<div class="hpp-chain__row hpp-reveal">'
            f'<span class="hpp-chain__problem">{esc(p)}</span>'
            f'<span class="hpp-chain__arrow">→</span>'
            f'<span class="hpp-chain__pattern">{esc(pat)}</span>'
            f'<span class="hpp-chain__arrow">→</span>'
            f'<span class="hpp-chain__result">{esc(res)}</span></div>'
        )
    return "".join(out)


def maturity_html(base: str) -> str:
    steps = "".join(
        f'<div class="hpp-maturity__step"><div class="hpp-maturity__dot"></div>'
        f'<div class="hpp-maturity__label">{esc(s)}</div></div>'
        for s in MATURITY_STEPS
    )
    lvl_cards = []
    for lv, name, desc, pats in MATURITY_LEVELS:
        chips = " ".join(
            f'<a class="hpp-chip" href="{base}/conventions/{s}/" style="text-decoration:none">{esc(t)}</a>'
            for t, s in pats
        )
        lvl_cards.append(
            f'<div class="hpp-card hpp-reveal" style="--hpp-cat:var(--hpp-accent-primary)">'
            f'<span class="hpp-card__num">{esc(lv)}</span>'
            f'<h3 class="hpp-card__title">{esc(name.upper())}</h3>'
            f'<p class="hpp-card__body">{esc(desc)}</p>'
            f'<p style="margin:0"><span class="hpp-kicker" style="margin:0 0 .4rem">REQUIRED PATTERNS</span><br>{chips}</p></div>'
        )
    return (
        f'<div class="hpp-maturity">{steps}</div>'
        f'<div class="hpp-grid hpp-grid--3">{"".join(lvl_cards)}</div>'
    )


def paths_html(base: str) -> str:
    out = []
    for tag, stmt, stack in PATHS:
        chips = []
        for i, (t, stem) in enumerate(stack):
            if i:
                chips.append('<span class="hpp-plus">+</span>')
            chips.append(f'<a class="hpp-chip" href="{base}/conventions/{stem}/" style="text-decoration:none">{esc(t)}</a>')
        out.append(
            f'<div class="hpp-card hpp-pcard hpp-reveal" style="--hpp-cat:var(--hpp-accent-secondary)">'
            f'<span class="hpp-card__num">{esc(tag)}</span>'
            f'<h3 class="hpp-card__title">{esc(stmt)}</h3>'
            f'<p class="hpp-card__body">推荐路线：</p>'
            f'<div class="hpp-path__stack">{"".join(chips)}</div></div>'
        )
    return "".join(out)


def blurb_of(text: str) -> str:
    """取正文首个真实段落(跳过标题/引用/代码围栏),按句读智能截断."""
    for block in re.split(r"\n\s*\n", text):
        s = block.strip()
        if not s or s[0] in "#>|`-" or s.startswith("```"):
            continue
        s = re.sub(r"`([^`]*)`", r"\1", s)          # 去行内代码标记
        s = re.sub(r"\*\*([^*]*)\*\*", r"\1", s)     # 去粗体
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        s = " ".join(s.split())
        if len(s) <= 118:
            return s
        cut = s[:118]
        for sep in ("。", "；", ".", ";", "，", ","):
            i = cut.rfind(sep)
            if i > 60:
                return cut[: i + 1]
        return cut.rsplit(" ", 1)[0] + "…"
    return ""


def example_cards(base: str, ex_metas: dict) -> str:
    out = []
    for stem in sorted(ex_metas):
        f = ROOT / "examples" / ex_metas[stem]["file"]
        text = FRONTMATTER_RE.sub("", f.read_text(encoding="utf-8"), count=1)
        h1 = re.search(r"^# (.+)$", text, re.M)
        title = (h1.group(1).strip() if h1 else stem).replace(" Example", "").upper()
        blurb = blurb_of(text) or signal_of(ex_metas[stem], stem)
        out.append(
            f'<div class="hpp-card hpp-pcard hpp-reveal" style="--hpp-cat:var(--hpp-cat-evolution)">'
            f'<span class="hpp-card__num">CASE STUDY</span>'
            f'<h3 class="hpp-card__title"><a href="{base}/examples/{stem}/">{esc(title)}</a></h3>'
            f'<p class="hpp-card__body">{esc(blurb)}</p>'
            f'<a class="hpp-card__link" href="{base}/examples/{stem}/">→ VIEW CASE STUDY</a></div>'
        )
    return "".join(out)


def make_home(base: str, conv_metas: dict, ex_metas: dict) -> None:
    feat = "".join(pattern_card(s, conv_metas[s], base, featured=True) for s in FEATURED if s in conv_metas)
    secondary = []
    for cat in CAT_ORDER:
        stems = [s for s, m in sorted(conv_metas.items())
                 if (m.get("hpp_category") or "meta") == cat and s not in FEATURED]
        if not stems:
            continue
        chips = " · ".join(
            f'<a href="{base}/conventions/{s}/" style="text-decoration:none">{esc(title_of(s, conv_metas[s]))}</a>'
            for s in stems
        )
        secondary.append(
            f'<div class="hpp-chain__row hpp-reveal" style="grid-template-columns:minmax(110px,auto) 1fr">'
            f'<span class="hpp-chain__pattern" style="text-align:left;color:var(--hpp-cat-{cat})">{esc(CAT_LABEL.get(cat, cat.upper()))}</span>'
            f'<span style="font-size:12.5px;letter-spacing:.02em">{chips}</span></div>'
        )
    term = (
        '<div class="hpp-terminal hpp-reveal"><div class="hpp-terminal__bar">'
        "<span></span><span></span><span></span><em>hermes — production-agent</em></div>"
        "<pre>"
        '<span class="hpp-t-cmd">$ hermes run production-agent</span>\n'
        "[Scheduler] triggered\n"
        "[Maker] executing\n"
        "[Checker] validating\n"
        '<span class="hpp-t-ok">✓ score: 46/50</span>\n'
        '<span class="hpp-t-info">[State] checkpoint saved</span>\n'
        '<span class="hpp-t-ok">✓ SUCCESS</span>'
        "</pre></div>"
    )
    page = f"""---
title: "Build Agents That Survive Production"
description: "一套用于构建可靠、自主、可恢复、可验证 AI Agent 的生产级工程模式体系。Production-grade engineering patterns for autonomous AI agents."
hide:
  - navigation
  - toc
---
<div class="hpp-landing">

<!-- 01 HERO -->
<section class="hpp-hero">
  <div>
    <p class="hpp-kicker cat-quality"><span class="hpp-kicker__dot"></span>AGENT PRODUCTION ENGINEERING</p>
    <h1 class="hpp-hero__title">BUILD AGENTS<br>THAT SURVIVE<br><span class="hpp-accent">PRODUCTION.</span></h1>
    <p class="hpp-hero__sub">Production-grade engineering patterns for autonomous AI agents.<br>
    让 AI Agent 从「能运行」，进化到<span class="hpp-em">「能够长期稳定运行」</span>。</p>
    <div class="hpp-ctas">
      <a class="hpp-btn hpp-btn--primary" href="{base}/quickstart/">10-Minute Quick Start</a>
      <a class="hpp-btn" href="{base}/patterns-library/">Explore Patterns</a>
      <a class="hpp-btn" href="{base}/cli/">hpp CLI</a>
      <a class="hpp-btn" href="{REPO_URL}">GitHub</a>
    </div>
  </div>
  <div class="hpp-hero__visual">
    <div class="hpp-graph-wrap">{arch_svg_link(read_site_url())}</div>
    {term}
  </div>
</section>

<!-- 02 WHY AGENTS FAIL -->
<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">DIAGNOSIS</p>
    <h2 class="hpp-sec__title">WHY AGENTS FAIL IN PRODUCTION</h2>
    <p class="hpp-sec__sub">Agent 在生产环境里的失败不是随机的，而是六类结构性问题。每一条都对应一个已被验证的工程解法。</p>
  </div>
  <div class="hpp-grid hpp-grid--3">{problem_cards(base, conv_metas)}</div>
</section>

<!-- 03 PATTERN SOLUTIONS -->
<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">PROBLEM → PATTERN → RESULT</p>
    <h2 class="hpp-sec__title">EACH PROBLEM HAS AN ENGINEERING ANSWER</h2>
    <p class="hpp-sec__sub">不是技巧清单，而是「问题 → 模式 → 结果」的因果链。</p>
  </div>
  <div class="hpp-chain">{chain_rows()}</div>
</section>

<!-- 04 PRODUCTION ARCHITECTURE -->
<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">THE SYSTEM</p>
    <h2 class="hpp-sec__title">ONE PRODUCTION-READY LOOP</h2>
    <p class="hpp-sec__sub">调度触发 → 生成 → 独立验证 → 持久化 → 通知；失败则压缩错误重试，超限升级人工。节点可点击进入对应 Pattern。</p>
  </div>
  <div class="hpp-grid hpp-grid--2" style="align-items:center">
    <div class="hpp-graph-wrap hpp-reveal">{arch_svg_link(read_site_url())}</div>
    <div>
      <p class="hpp-card__body" style="font-size:0.95rem">这条流水线本身就是 Pattern 的组合：<b style="color:var(--hpp-text-primary)">Cron Job</b> 负责可靠触发，<b style="color:var(--hpp-text-primary)">Maker / Checker</b> 负责输出质量，<b style="color:var(--hpp-text-primary)">State File + Checkpoint</b> 负责断电恢复，<b style="color:var(--hpp-text-primary)">Error Compact</b> 负责失败不污染上下文。完整拆解见 Architecture 页。</p>
      <div class="hpp-ctas" style="margin-top:1.2rem">
        <a class="hpp-btn" href="{base}/architecture-page/">OPEN ARCHITECTURE →</a>
      </div>
    </div>
  </div>
</section>

<!-- 05 PATTERN RELATIONSHIP -->
<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">PATTERNS WORK TOGETHER.</p>
    <h2 class="hpp-sec__title">A SYSTEM, NOT A TRICK LIST</h2>
    <p class="hpp-sec__sub">Production agents are built from systems of patterns, not isolated techniques. 悬停高亮关联，点击进入公约。</p>
  </div>
  <div class="hpp-graph-wrap hpp-reveal">{graph_svg(read_site_url(), conv_metas)}</div>
  <div class="hpp-ctas" style="margin-top:1.2rem">
    <a class="hpp-btn" href="{base}/skill-graph/">FULL GRAPH →</a>
  </div>
</section>

<!-- 06 PATTERN LIBRARY -->
<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">PATTERN LIBRARY</p>
    <h2 class="hpp-sec__title">FEATURED PATTERNS</h2>
    <p class="hpp-sec__sub">三个最核心的生产组件，建议按此顺序理解整个系统。</p>
  </div>
  <div class="hpp-grid hpp-grid--3">{feat}</div>
  <h3 class="hpp-sec__title" style="font-size:22px;margin:3rem 0 1.2rem">SECONDARY PATTERNS</h3>
  <div class="hpp-chain">{"".join(secondary)}</div>
  <div class="hpp-ctas" style="margin-top:1.6rem">
    <a class="hpp-btn hpp-btn--primary" href="{base}/patterns-library/">OPEN FULL LIBRARY →</a>
  </div>
</section>

<!-- 07 PRODUCTION MATURITY -->
<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">MATURITY MODEL</p>
    <h2 class="hpp-sec__title">FROM AGENT TO PRODUCTION SYSTEM</h2>
    <p class="hpp-sec__sub">从 Prompt 到自主系统的六级阶梯；每一级由对应 Pattern 托底。</p>
  </div>
  {maturity_html(base)}
</section>

<!-- 08 REAL EXAMPLES -->
<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">CASE STUDIES</p>
    <h2 class="hpp-sec__title">RUNNING IN PRODUCTION, NOT IN A DEMO</h2>
    <p class="hpp-sec__sub">四条 Pattern 在真实 7×24 工作流中的组合应用。</p>
  </div>
  <div class="hpp-grid hpp-grid--4">{example_cards(base, ex_metas)}</div>
</section>

<!-- 09 CHOOSE YOUR PATH -->
<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">ON-RAMP</p>
    <h2 class="hpp-sec__title">CHOOSE YOUR PATH</h2>
    <p class="hpp-sec__sub">按你的角色直接开始，30 秒找到第一个要读的 Pattern。</p>
  </div>
  <div class="hpp-grid hpp-grid--3">{paths_html(base)}</div>
</section>

<!-- 10 FINAL CTA -->
<section class="hpp-sec hpp-finale">
  <p class="hpp-kicker" style="text-align:center">START TODAY</p>
  <h2 class="hpp-sec__title">BUILD AGENTS THAT SURVIVE PRODUCTION.</h2>
  <p class="hpp-sec__sub" style="margin:0 auto 2rem">clone 仓库即可把全部 15 条公约装进你的 Hermes。</p>
  <div class="hpp-ctas">
    <a class="hpp-btn hpp-btn--primary" href="{base}/readme/">GET STARTED</a>
    <a class="hpp-btn" href="{REPO_URL}">STAR ON GITHUB ★</a>
  </div>
</section>

</div>
"""
    (DOCS / "index.md").write_text(page, encoding="utf-8")


def make_readme_page() -> None:
    """V1 首页内容(README)保留为独立页面——§37 不删除既有内容."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    logo = f"{read_site_url_prefix()}/logo.png"
    text = re.sub(r'src="(?!http)[^"]*assets/logo\.png"', f'src="{logo}"', text)
    text = re.sub(r'srcset="(?!http)[^"]*assets/logo\.png"', f'srcset="{logo}"', text)
    text = text.replace("(README.en.md)", "(readme-en.md)")
    text = text.replace('href="README.en.md"', 'href="readme-en.md"')
    fm = ('---\ntitle: "项目说明 README | Hermes Production Patterns"\n'
          "description: \"仓库总览：项目背景、三大设计原则、快速开始与核心概念速查。\"\n---\n")
    (DOCS / "readme.md").write_text(fm + text, encoding="utf-8")


def make_library(base: str, conv_metas: dict) -> None:
    cats = sorted({(m.get("hpp_category") or "meta") for m in conv_metas.values()})
    buttons = ['<button data-filter="all" class="is-active">ALL</button>']
    for c in cats:
        buttons.append(f'<button data-filter="{c}">{esc(CAT_LABEL.get(c, c.upper()))}</button>')
    cards = "".join(pattern_card(s, m, base) for s, m in sorted(
        conv_metas.items(), key=lambda kv: (CAT_ORDER.index(kv[1].get("hpp_category") or "meta")
                                            if (kv[1].get("hpp_category") or "meta") in CAT_ORDER else 99, kv[0])))
    body = f"""---
title: "Pattern Explorer | Hermes Production Patterns"
description: "按分类、难度与 Hermes 能力浏览全部生产级工程公约（Pattern）。Explore all production engineering patterns."
---
<div class="hpp-landing" data-hpp-explorer>

<section class="hpp-sec" style="padding-top:clamp(48px,7vw,96px)">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">EXPLORER</p>
    <h2 class="hpp-sec__title">EXPLORE PRODUCTION PATTERNS</h2>
    <p class="hpp-sec__sub">每条公约 = 一个解决特定生产问题的工程组件。按分类过滤，或直接搜关键词。</p>
  </div>
  <div class="hpp-filters">
    {''.join(buttons)}
    <input class="hpp-searchbox" type="search" placeholder="Search patterns, problems, capabilities..." aria-label="过滤 Pattern 卡片">
    <span class="hpp-kicker" style="align-self:center;margin:0"><b data-hpp-count>0</b> SHOWN</span>
  </div>
  <div class="hpp-grid hpp-grid--3">{cards}</div>
</section>

</div>
"""
    (DOCS / "patterns-library.md").write_text(body, encoding="utf-8")


def make_arch_page(base: str, conv_metas: dict) -> None:
    comps = [
        ("Scheduler", "可靠触发：幂等、防重复、防静默失败", "cron-job-pattern"),
        ("Maker", "生成/执行：控制流分离，确定性步骤交给代码", "control-flow-separation"),
        ("Checker", "独立验证：生成与验证不共享上下文", "maker-checker"),
        ("State", "跨运行状态：先读后跑，每步落盘", "state-file-pattern"),
        ("Checkpoint", "断点恢复：挂了从哪恢复", "checkpoint-pattern"),
        ("Error Compact", "失败压缩：错误不污染长期上下文", "error-compact-pattern"),
        ("Notifier", "交付与可观测：结果可达，异常可见", "cron-job-pattern"),
        ("Evolution Gate", "进化闸门：新模式上线前回归验证", "evolution-gate"),
    ]
    comp_rows = "".join(
        f'<tr><td style="font-family:var(--hpp-font-mono);letter-spacing:.05em">{c}</td>'
        f"<td>{d}</td>"
        f'<td><a href="{base}/conventions/{stem}/">{stem}</a></td></tr>'
        for c, d, stem in comps
    )
    comp_table = (
        '<table><thead><tr><th>组件</th><th>职责</th><th>对应公约</th></tr></thead>'
        f"<tbody>{comp_rows}</tbody></table>"
    )
    body = f"""---
title: "Production Architecture | Hermes Production Patterns"
description: "AI Agent 生产架构：Scheduler→Maker→Checker→State→Notifier 的正常运行流与错误处理流。"
---
<div class="hpp-landing">

<section class="hpp-sec" style="padding-top:clamp(48px,7vw,96px)">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">THE SECOND CORE PAGE</p>
    <h2 class="hpp-sec__title">PRODUCTION ARCHITECTURE</h2>
    <p class="hpp-sec__sub">一个可靠的 Agent 系统 = 一条可验证的主循环。节点点击进入对应 Pattern。</p>
  </div>
  <div class="hpp-graph-wrap hpp-reveal">{arch_svg_link(read_site_url())}</div>
</section>

<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">NORMAL FLOW</p>
    <h2 class="hpp-sec__title">EVERYTHING WORKS</h2>
  </div>
  <div class="hpp-chain">
    <div class="hpp-chain__row"><span class="hpp-chain__pattern">SCHEDULER</span><span class="hpp-chain__arrow">→</span><span class="hpp-chain__pattern">MAKER</span><span class="hpp-chain__arrow">→</span><span class="hpp-chain__result">CHECKER · PASS</span></div>
    <div class="hpp-chain__row"><span class="hpp-chain__pattern">STATE</span><span class="hpp-chain__arrow">→</span><span class="hpp-chain__pattern">CHECKPOINT</span><span class="hpp-chain__arrow">→</span><span class="hpp-chain__result">NOTIFIER</span></div>
  </div>
</section>

<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker" style="color:var(--hpp-error)">ERROR FLOW</p>
    <h2 class="hpp-sec__title">AND WHEN IT DOESN'T</h2>
    <p class="hpp-sec__sub">失败是设计的一部分：压缩错误 → 有界重试 → 超限升级人工，绝不静默吞掉。</p>
  </div>
  <div class="hpp-chain">
    <div class="hpp-chain__row"><span class="hpp-chain__problem">MAKER</span><span class="hpp-chain__arrow">→</span><span class="hpp-chain__problem">CHECKER · FAIL</span><span class="hpp-chain__arrow">→</span><span class="hpp-chain__pattern">FEEDBACK (ERROR COMPACT)</span></div>
    <div class="hpp-chain__row"><span class="hpp-chain__problem">RETRY</span><span class="hpp-chain__arrow">→</span><span class="hpp-chain__problem">RETRY LIMIT</span><span class="hpp-chain__arrow">→</span><span class="hpp-chain__result">HUMAN ESCALATION</span></div>
  </div>
</section>

<section class="hpp-sec">
  <div class="hpp-sec__head">
    <p class="hpp-kicker">COMPONENTS</p>
    <h2 class="hpp-sec__title">WHAT EACH BOX MEANS</h2>
  </div>
  {comp_table}
  <p class="hpp-sec__sub" style="margin-top:2rem">宏观文档（仓库结构、质量闸门）见 <a href="{base}/ARCHITECTURE/">架构总览 ARCHITECTURE</a>；模式如何叠加见 <a href="{base}/conventions/pattern-composition/">模式组合指南</a>。</p>
</section>

</div>
"""
    (DOCS / "architecture-page.md").write_text(body, encoding="utf-8")


def read_site_url() -> str:
    t = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    m = re.search(r"^site_url:\s*(\S+)", t, re.M)
    return m.group(1) if m else "/"


def read_site_url_prefix() -> str:
    return re.sub(r"https?://[^/]+", "", read_site_url()).rstrip("/")


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


def copy_v2_assets() -> None:
    (DOCS / "assets").mkdir(exist_ok=True)
    for name in ("hpp.css", "hpp.js"):
        shutil.copy2(ROOT / "assets" / name, DOCS / "assets" / name)


def make_starter_kits_page() -> None:
    """v2.0: starter-kits 目录 → 单页速览(每个 kit 一节,锚点 #kit-<name>)。"""
    parts = [
        "---",
        'title: "Starter Kits | Hermes Production Patterns"',
        'description: "六个可复制的起步套件:先跑通,再理解。cp -r 开跑。" ',
        "---",
        "",
        "# Starter Kits",
        "",
        "> Pattern 告诉你为什么,Starter Kit 给你可复制的骨架。选一个贴近场景的 kit,`cp -r` 开跑。",
        "",
    ]
    kits_root = ROOT / "starter-kits"
    for kit_dir in sorted(p for p in kits_root.iterdir() if p.is_dir()):
        readme = kit_dir / "README.md"
        if not readme.exists():
            continue
        text = FRONTMATTER_RE.sub("", readme.read_text(encoding="utf-8"), count=1)
        # relative links within the kit -> stay; cross-repo links -> repo pages
        text = text.replace("](starter-kits/", "](../starter-kits/")
        text = re.sub(r"\]\((conventions|patterns|examples|stacks|recipes|audit)/",
                      r"](../\1/", text)
        parts += [f"## <span id=\"kit-{kit_dir.name}\"></span>{kit_dir.name}", "", text, "", "---", ""]
    parts += [
        "## 用 `hpp init` 一键起步",
        "",
        "```bash",
        "cli/hpp init basic-agent ~/my-agent",
        "```",
        "",
        "详见 [hpp CLI](cli.md)。",
        "",
    ]
    (DOCS / "starter-kits.md").write_text("\n".join(parts), encoding="utf-8")


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
    copy_v2_assets()
    for sub in ("conventions", "patterns", "examples", "stacks", "recipes", "audit", "compatibility"):
        copy_tree(sub)
    for root_md in ("ARCHITECTURE.md", "CONTEXT.md", "CHANGELOG.md", "CONTRIBUTING.md"):
        shutil.copy2(ROOT / root_md, DOCS / root_md)
    # v2.0: quick start page (rewrite starter-kit links to the generated page)
    qs = (ROOT / "quickstart.md").read_text(encoding="utf-8")
    qs = re.sub(r"\]\(starter-kits/([a-z\-]+)/README\.md\)", r"](starter-kits.md#kit-\1)", qs)
    (DOCS / "quickstart.md").write_text(qs, encoding="utf-8")
    # v2.0: hpp CLI page (plain copy, h1 title carries)
    shutil.copy2(ROOT / "cli" / "README.md", DOCS / "cli.md")

    conv_metas = collect_meta("conventions")
    collect_meta("patterns")
    ex_metas = collect_meta("examples")
    inject_contract("conventions", conv_metas)
    make_router(conv_metas)
    make_graph(read_site_url(), conv_metas)

    write_section_indexes()
    make_templates_page()
    make_starter_kits_page()
    (DOCS / "readme-en.md").write_text(
        (ROOT / "README.en.md").read_text(encoding="utf-8").replace("(README.md)", "(readme.md)"),
        encoding="utf-8",
    )
    make_readme_page()
    site_url = read_site_url()
    base = re.sub(r"https?://[^/]+", "", site_url).rstrip("/")  # '/hermes-production-patterns'
    make_home(base, conv_metas, ex_metas)
    make_library(base, conv_metas)
    make_arch_page(base, conv_metas)
    n = sum(1 for _ in DOCS.rglob("*.md"))
    print(f"docs/ generated: {n} markdown pages (V2 landing + library + arch page)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
