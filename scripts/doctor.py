#!/usr/bin/env python3
"""hpp doctor — Pattern recommendation engine.

Asks a few questions about your agent setup and recommends which
patterns to use based on the pattern-composition decision tree.

Usage:
    python scripts/doctor.py
    python scripts/doctor.py --auto  # non-interactive (for CI)
"""

import sys
import os
import json

# --- Pattern Recommendation Rules ---

QUESTIONS = [
    {
        "id": "task_type",
        "question": "你的 Agent 主要做什么？",
        "question_en": "What does your agent primarily do?",
        "choices": [
            {"label": "定时任务（新闻/数据抓取）", "value": "cron", "en": "Scheduled tasks"},
            {"label": "内容生产（文章/报告）", "value": "content", "en": "Content production"},
            {"label": "代码/工程任务", "value": "coding", "en": "Coding/engineering tasks"},
            {"label": "研究/分析", "value": "research", "en": "Research/analysis"},
            {"label": "综合/多种任务", "value": "mixed", "en": "Mixed/general"},
        ],
    },
    {
        "id": "autonomy",
        "question": "Agent 的自主程度？",
        "question_en": "How autonomous should the agent be?",
        "choices": [
            {"label": "全程人工监督", "value": "supervised", "en": "Fully supervised"},
            {"label": "半自主（关键决策人工确认）", "value": "semi", "en": "Semi-autonomous"},
            {"label": "全自主（7x24 无人值守）", "value": "full", "en": "Fully autonomous 7x24"},
        ],
    },
    {
        "id": "risk_level",
        "question": "任务涉及的风险等级？",
        "question_en": "What risk level do your tasks involve?",
        "choices": [
            {"label": "低（只读/内部使用）", "value": "low", "en": "Low (read-only/internal)"},
            {"label": "中（有副作用但可回滚）", "value": "medium", "en": "Medium (reversible side effects)"},
            {"label": "高（涉及发布/资金/删除）", "value": "high", "en": "High (publish/delete/money)"},
        ],
    },
    {
        "id": "multi_agent",
        "question": "是否需要多个 Agent 协作？",
        "question_en": "Do you need multiple agents collaborating?",
        "choices": [
            {"label": "单 Agent", "value": "single", "en": "Single agent"},
            {"label": "多 Agent（同一任务内协作）", "value": "multi_same", "en": "Multi-agent, same task"},
            {"label": "多 Agent（独立并行任务）", "value": "multi_parallel", "en": "Multi-agent, parallel independent"},
        ],
    },
    {
        "id": "state_complexity",
        "question": "任务状态复杂度？",
        "question_en": "How complex is your task state?",
        "choices": [
            {"label": "简单（几行配置就够了）", "value": "simple", "en": "Simple"},
            {"label": "中等（需要跟踪进度和历史）", "value": "medium", "en": "Medium (progress tracking)"},
            {"label": "复杂（多步骤、检查点、回滚）", "value": "complex", "en": "Complex (checkpoints, rollback)"},
        ],
    },
]

# Pattern recommendation rules
PATTERN_RULES = {
    # Always recommended
    "state-file-pattern": {
        "condition": lambda a: True,
        "reason": "任何跨会话任务都需要 STATE.md 管理状态",
        "priority": "must",
    },
    "error-compact-pattern": {
        "condition": lambda a: True,
        "reason": "错误压缩是生产环境基础能力",
        "priority": "must",
    },

    # Cron-specific
    "cron-job-pattern": {
        "condition": lambda a: a.get("task_type") == "cron" or a.get("autonomy") == "full",
        "reason": "定时/自主任务需要幂等和防静默失败",
        "priority": "must",
    },
    "checkpoint-pattern": {
        "condition": lambda a: a.get("state_complexity") == "complex" or a.get("autonomy") == "full",
        "reason": "复杂/长任务需要检查点恢复",
        "priority": "should",
    },

    # Quality
    "maker-checker": {
        "condition": lambda a: a.get("risk_level") in ("medium", "high") or a.get("autonomy") == "full",
        "reason": "有风险或全自主任务需要独立验证",
        "priority": "must",
    },

    # Safety
    "human-escalation": {
        "condition": lambda a: a.get("risk_level") == "high" and a.get("autonomy") == "semi",
        "reason": "高风险+半自主需要人工兜底升级通道",
        "priority": "should",
    },
    "budget-guardrail": {
        "condition": lambda a: a.get("autonomy") == "full" or a.get("task_type") == "cron",
        "reason": "全自主/定时任务需要预算护栏防止 token 失控",
        "priority": "should",
    },
    "secret-management": {
        "condition": lambda a: a.get("risk_level") in ("medium", "high"),
        "reason": "有风险任务需要规范密钥管理",
        "priority": "should",
    },

    # Multi-agent
    "multi-agent-isolation": {
        "condition": lambda a: "multi" in a.get("multi_agent", ""),
        "reason": "多 Agent 协作需要资源隔离",
        "priority": "must",
    },

    # Advanced
    "control-flow-separation": {
        "condition": lambda a: a.get("task_type") in ("coding", "research", "mixed"),
        "reason": "复杂任务需要区分确定性代码和 LLM 决策",
        "priority": "should",
    },
    "data-driven-optimization": {
        "condition": lambda a: a.get("task_type") in ("content", "research"),
        "reason": "内容/研究任务需要数据驱动迭代",
        "priority": "nice",
    },
    "memory-os-pattern": {
        "condition": lambda a: a.get("autonomy") == "full" and a.get("state_complexity") == "complex",
        "reason": "全自主+复杂状态需要五层记忆架构",
        "priority": "nice",
    },
    "evolution-gate": {
        "condition": lambda a: a.get("autonomy") == "full",
        "reason": "全自主任务需要进化闸门控制技能变更",
        "priority": "nice",
    },
    "skill-evolution": {
        "condition": lambda a: a.get("autonomy") in ("semi", "full"),
        "reason": "半自主/全自主需要技能版本化管理",
        "priority": "should",
    },
    "observability-trace": {
        "condition": lambda a: a.get("autonomy") == "full" and a.get("risk_level") in ("medium", "high"),
        "reason": "全自主+有风险需要决策链路追溯",
        "priority": "nice",
    },
    "data-retention-privacy": {
        "condition": lambda a: a.get("risk_level") in ("medium", "high"),
        "reason": "有风险任务需要数据保留和隐私规范",
        "priority": "nice",
    },
    "self-update-pattern": {
        "condition": lambda a: a.get("autonomy") == "full",
        "reason": "全自主任务需要安全自更新流程",
        "priority": "should",
    },
    "anti-patterns": {
        "condition": lambda a: True,
        "reason": "反面模式参考，避免常见错误",
        "priority": "reference",
    },
    "pattern-composition": {
        "condition": lambda a: True,
        "reason": "模式组合决策树，帮你选择和组合模式",
        "priority": "reference",
    },
}


def ask_questions():
    """Interactive question flow."""
    answers = {}
    for q in QUESTIONS:
        print(f"\n{q['question']}")
        for i, choice in enumerate(q["choices"], 1):
            print(f"  {i}. {choice['label']}")
        while True:
            try:
                raw = input(f"  选择 [1-{len(q['choices'])}]: ").strip()
                idx = int(raw) - 1
                if 0 <= idx < len(q["choices"]):
                    answers[q["id"]] = q["choices"][idx]["value"]
                    break
            except (ValueError, EOFError):
                pass
            print(f"  请输入 1-{len(q['choices'])}")
    return answers


def auto_answers():
    """Non-interactive defaults for CI."""
    return {
        "task_type": "mixed",
        "autonomy": "semi",
        "risk_level": "medium",
        "multi_agent": "single",
        "state_complexity": "medium",
    }


def recommend(answers):
    """Generate pattern recommendations based on answers."""
    must = []
    should = []
    nice = []
    reference = []

    for pattern, rule in PATTERN_RULES.items():
        if rule["condition"](answers):
            entry = {"pattern": pattern, "reason": rule["reason"]}
            if rule["priority"] == "must":
                must.append(entry)
            elif rule["priority"] == "should":
                should.append(entry)
            elif rule["priority"] == "nice":
                nice.append(entry)
            else:
                reference.append(entry)

    return must, should, nice, reference


def format_report(answers, must, should, nice, reference):
    """Format recommendation report as markdown."""
    lines = [
        "# hpp doctor 推荐报告",
        "",
        "## 你的配置",
        "",
    ]

    for q in QUESTIONS:
        val = answers.get(q["id"], "?")
        label = next((c["label"] for c in q["choices"] if c["value"] == val), val)
        lines.append(f"- {q['question']} **{label}**")

    lines.append("")
    lines.append("---")
    lines.append("")

    def section(title, emoji, items):
        if not items:
            return
        lines.append(f"## {emoji} {title}（{len(items)} 个）")
        lines.append("")
        for item in items:
            lines.append(f"- **{item['pattern']}** — {item['reason']}")
            lines.append(f"  → `conventions/{item['pattern']}.md`")
        lines.append("")

    section("必装模式", "🔴", must)
    section("推荐模式", "🟡", should)
    section("可选模式", "🟢", nice)
    section("参考文档", "📖", reference)

    total = len(must) + len(should) + len(nice)
    lines.append("---")
    lines.append("")
    lines.append(f"**总计**: {total} 个推荐模式（必装 {len(must)} + 推荐 {len(should)} + 可选 {len(nice)}）")
    lines.append("")
    lines.append("## 安装命令")
    lines.append("")
    lines.append("```bash")
    patterns = [item["pattern"] for item in must + should]
    lines.append(f"# 安装必装+推荐模式（共 {len(patterns)} 个）")
    lines.append("git clone https://github.com/Komagon/hermes-production-patterns.git")
    lines.append("cd hermes-production-patterns")
    for p in patterns:
        lines.append(f"cp conventions/{p}.md ~/.hermes/skills/hermes-production-patterns/")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main():
    auto_mode = "--auto" in sys.argv

    print("=" * 50)
    print("  hpp doctor — Pattern Recommendation Engine")
    print("=" * 50)

    if auto_mode:
        answers = auto_answers()
        print("\n[auto mode: using defaults]")
    else:
        answers = ask_questions()

    must, should, nice, reference = recommend(answers)
    report = format_report(answers, must, should, nice, reference)

    # Output to stdout
    print("\n" + report)

    # Also save to file
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DOCTOR_REPORT.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📄 Report saved to: {output_path}")


if __name__ == "__main__":
    main()
