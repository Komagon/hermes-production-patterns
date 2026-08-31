# Research Agent Starter Kit

> 研究 → 证据 → 独立验证 → 报告的四段式研究 Agent。
> 适合:事实核查 / 行业调研 / 竞品分析 / 任何「结论必须有出处」的任务。

## Patterns Used

| Pattern | 文件 | 作用 |
|:---|:---|:---|
| Control Flow Separation | `planner/` | 确定性的研究计划走固定清单,LLM 只做判断与综合 |
| Evidence Discipline | `evidence/evidence.jsonl` | 每条具体事实都有来源条目,无来源不成文 |
| Maker/Checker | `verifier/` | 撰写者与验证者分离,验证者只对证据负责 |
| State File | `STATE.md` | 跨运行记住研究进度,长任务可断点续跑 |
| Regression | `regression/` | 报告质量反测,防「证据齐全但结论跑偏」 |

## 目录结构

```text
research-agent/
├── planner/PLAN.template.md  # 研究问题拆解模板
├── researcher/PROMPT.md      # 研究执行角色
├── verifier/PROMPT.md        # 独立验证角色(独立实例)
├── evidence/evidence.jsonl   # 证据条目(JSONL,一行一条)
├── STATE.md                  # 研究进度状态
├── regression/regression.json
└── README.md
```

## 核心流程

```text
Research(研究者检索与摘录)
   ↓ 每条事实落 evidence.jsonl(claim + source)
Verification(验证者逐条核对来源)
   ↓ 剔除未证实条目
Report(基于存活证据撰写,结论逐条对应证据)
```

## 安装

```bash
cp -r starter-kits/research-agent ~/my-research-agent
cd ~/my-research-agent
# 1. 在 planner/PLAN.template.md 填研究问题
# 2. 初始化 STATE.md
# 3. 按 SKILL.md(见 cron-production 或 basic-agent 的写法)封装为技能
```

## 验证

- [ ] 报告中每条具体事实都能在 evidence.jsonl 找到对应条目
- [ ] 未证实条目被剔除或明确标注「未证实」
- [ ] 中断后从 STATE.md 续跑,不重复已完成的检索
- [ ] 撰写者与验证者不在同一实例
