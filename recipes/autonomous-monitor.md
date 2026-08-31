# Recipe: Autonomous Monitor — 无人值守监控告警 Agent

## Problem

监控类任务(盯价格/盯更新/盯状态)要求「有变化才动作,没变化零成本」。裸 LLM 轮询既烧钱又容易漏报;脚本轮询不智能。正确架构是脚本探测 + LLM 判断 + 可靠告警。

## Architecture

```text
Cron(高频,如每 10 分钟)
   ↓
Probe(纯脚本):抓取目标状态 → 计算哈希
   ↓
哈希与上次相同? → 是:退出(零 LLM 成本)
   ↓ 否
Diff:与上次快照做确定性 diff
   ↓
Judge(LLM):diff 是否值得告警(只看 diff,不看全量)
   ↓ 值得
Alert:按渠道发出(含压缩的 diff 摘要)
   ↓
Post-flight:更新快照哈希 + STATE + Monitor 记录
```

## Patterns Used

| Pattern | 公约 |
|:---|:---|
| Cron 设计 | `conventions/cron-job-pattern.md`(Monitor 模式:变了才烧 token) |
| 状态管理 | `conventions/state-file-pattern.md`(快照哈希存 STATE) |
| 控制流分离 | `conventions/control-flow-separation.md`(探测走脚本) |
| 错误压缩 | `conventions/error-compact-pattern.md`(告警内容压缩) |

对应 Starter Kit:`starter-kits/cron-production/`(monitor/ 目录)。

## Installation

```bash
cp -r starter-kits/cron-production ~/monitor-agent
cd ~/monitor-agent
```

## Configuration

1. 探测目标:URL/文件/接口清单放独立配置
2. 哈希存储:STATE.md 存上次快照哈希与时间戳
3. 告警渠道:主渠道 + 备用渠道;主渠道失败走备用
4. 判定 prompt:只输出「告警/忽略 + 一句话理由」

## Run

```bash
# Probe 可独立手动执行验证
python probe.py --check
# 挂 cron 后通过 monitor/runs.log 观察触发/抑制比
```

## Failure Modes

| 失败 | 症状 | 防护 |
|:---|:---|:---|
| 探测失败 | 目标不可达 | 连续 N 次失败升级告警,与「无变化」区分 |
| 误报 | 微小变动触发告警 | Judge 只看确定性 diff;阈值化(变动 > x% 才进 LLM) |
| 漏报 | 变了但没报 | 哈希对全量内容计算,不做抽样 |
| 告警渠道故障 | 发不出去 | 主备渠道 + 发送失败重试 + 记录待补发队列 |

## Recovery

- 快照丢失:重建基线(全量探测一次)并记录异常
- 告警积压:待补发队列持久化在 STATE,恢复后按序补发
- 长时间无触发:周期性自检(Heartbeat)证明监控本身活着

## Metrics

- 触发/抑制比:LLM 实际被调用的比例(成本指标)
- 误报率:告警后被人工判定「不值得报」的占比
- 检出延迟:变化发生到告警发出的时间差
- 监控存活率:Heartbeat 缺失次数(应为 0)
