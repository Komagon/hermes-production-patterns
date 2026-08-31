# Recipe: Daily News Agent — 每日新闻摘要 Agent

## Problem

每天需要从多个来源聚合领域新闻、压缩成摘要并推送。人肉做重复且时点不稳;裸 cron 做,则大概率演进成「跑着跑着跑偏了/重复推送/静默失败没人发现」。

## Architecture

```text
Cron 触发(每日固定时间)
   ↓
Pre-flight:读 STATE.md → 幂等键 = 日期,当日已跑则退出
   ↓
Collect:多来源抓取(脚本确定性执行)
   ↓
Summarize:LLM 压缩成条目式摘要
   ↓
Checker:来源核对 + 格式 schema 校验(独立实例)
   ↓
Publish:推送(可重复,幂等键去重)
   ↓
Post-flight:写 STATE → Monitor 记录成败
```

## Patterns Used

| Pattern | 公约 |
|:---|:---|
| Cron 幂等 | `conventions/cron-job-pattern.md` |
| 状态管理 | `conventions/state-file-pattern.md` |
| 错误压缩 | `conventions/error-compact-pattern.md` |
| 质量验证 | `conventions/maker-checker.md` |

对应 Starter Kit:`starter-kits/cron-production/`。

## Installation

```bash
cp -r starter-kits/cron-production ~/daily-news
cd ~/daily-news
```

## Configuration

1. `SKILL.md`:任务定义为「抓取来源清单 → 摘要 → 推送」
2. 来源清单放独立文件(如 sources.txt),脚本读取——来源增减不改 prompt
3. `cron-config.example`:schedule 设每日目标时间;prompt 引用技能名
4. 幂等键约定:`news-YYYY-MM-DD`,Publish 前查重

## Run

```bash
# 手动首跑验证
hermes run --skill SKILL.md --state STATE.md
# 挂 cron 后,用 Monitor 日志确认每日执行
```

## Failure Modes

| 失败 | 症状 | 防护 |
|:---|:---|:---|
| 来源抓取失败 | 部分来源超时 | 单来源失败压缩记录,不中断整批;全失败才告警 |
| 摘要编造 | 摘要含来源没有的内容 | Checker 对照来源核对,编造即 FAIL |
| 重复推送 | 同日多次推送 | 幂等键 + Publish 前查重 |
| 静默失败 | cron 跑了但没产出 | Monitor:有触发无产出即告警 |

## Recovery

- 中断恢复:STATE.md 记录「已抓取来源/已生成摘要/已推送」三阶段,断点续跑
- 当日失败:次日自动补跑(幂等键按内容日期而非执行日期)
- 推送失败:重试 3 次后升级人工,摘要保留不丢弃

## Metrics

- 成功率:周期内成功推送天数占比
- 时效:实际推送时间与目标时间差
- 抓取完整率:成功来源数 / 配置来源数
- 编造拦截数:Checker 拦截的条目数(异常升高说明来源质量劣化)
