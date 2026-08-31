# Recipe: Research Pipeline — 研究调研流水线

## Problem

研究类任务(行业调研/竞品分析/事实核查)的核心风险是「编造」:LLM 会自信地产出无来源的结论。裸跑一个「帮我调研 X」的 prompt,产出基本不可用。需要证据纪律与独立验证。

## Architecture

```text
研究计划(子问题拆解,确定性清单)
   ↓
Researcher:逐子问题检索 → 每条事实落 evidence.jsonl(claim+source)
   ↓
Verifier(独立实例):逐条核对来源,打 VERIFIED/UNVERIFIED/CONTRADICTED
   ↓
Report:只基于 VERIFIED 条目撰写,结论逐条对应证据 ID
   ↓
终审:未证实条目单列,不混入结论
```

## Patterns Used

| Pattern | 公约 |
|:---|:---|
| 证据纪律 | `conventions/memory-os-pattern.md`(evidence 层) |
| Maker/Checker | `conventions/maker-checker.md`(Researcher/Verifier 分离) |
| 状态管理 | `conventions/state-file-pattern.md`(子问题进度) |
| 控制流分离 | `conventions/control-flow-separation.md`(计划是清单,不是自由发挥) |

对应 Starter Kit:`starter-kits/research-agent/`。

## Installation

```bash
cp -r starter-kits/research-agent ~/research-pipeline
cd ~/research-pipeline
```

## Configuration

1. `planner/PLAN.template.md`:先填研究问题与子问题清单再开工
2. 证据格式:JSONL 一行一条,字段 id/question/claim/source/verified
3. 来源优先级:一手 > 官方文档 > 权威媒体 > 二手转述;二手必须交叉验证

## Run

```text
长任务拆会话:每完成 N 个子问题写 STATE,下个会话续跑
Verifier 在独立会话运行,只看 evidence.jsonl
```

## Failure Modes

| 失败 | 症状 | 防护 |
|:---|:---|:---|
| 来源失效 | 链接 404/内容不符 | Verifier 逐条打开核对,失效即 UNVERIFIED |
| 语境偏差 | 摘录断章取义 | 核对时保留原文上下文比对 |
| 结论越界 | 结论超出证据范围 | 终审:每条结论必须映射证据 ID |
| 冲突数据 | 来源互相矛盾 | 标注冲突,给出取舍依据,不静默择一 |

## Recovery

- 中断恢复:STATE 记录子问题完成度,VERIFIED 条目不重复检索
- 证据不足:子问题标「未证实」,报告单列,不推测填充
- 计划失效:研究过程中发现子问题设计错误 → 更新 PLAN 并记录,不硬跑

## Metrics

- 证据存活率:VERIFIED / 总采集条目
- 结论可追溯率:能映射到证据 ID 的结论占比(目标 100%)
- 子问题完成度:STATE 中的完成清单
- 重检索率:因中断导致的重复检索次数(应趋近 0)
