# Recipe: Content Pipeline — 内容生产发布流水线

## Problem

内容生产(文章/帖子/报告)需要初稿→修改→审查→排版→发布多道工序。全靠一个 Agent 一次生成,质量不稳;靠人盯,产能上不去。失败代价是「发出去的东西代表你」。

## Architecture

```text
选题库(STATE.md 驱动)
   ↓
Maker:按提纲生成初稿
   ↓
Checker 独立审查(schema + 红线:事实/风格/禁词)
   ↓ PASS              ↓ FAIL
排版(确定性脚本)    压缩反馈 → Maker 修订(≤2 次)
   ↓                       ↓ 超限
定时发布              人工介入
   ↓
STATE 更新:发布记录 + 复盘数据
```

## Patterns Used

| Pattern | 公约 |
|:---|:---|
| Maker/Checker | `conventions/maker-checker.md` |
| 状态管理 | `conventions/state-file-pattern.md` |
| Cron(定时发布) | `conventions/cron-job-pattern.md` |
| 数据驱动优化 | `conventions/data-driven-optimization.md`(复盘) |

对应 Starter Kit:`starter-kits/maker-checker/` + `starter-kits/cron-production/`。

## Installation

```bash
cp -r starter-kits/maker-checker ~/content-pipeline
cd ~/content-pipeline
# 再按需把 cron-production 的 monitor/recovery 复制进来
```

## Configuration

1. 选题库:STATE.md 维护「待写/初稿/待审/已发布」状态与发布计划
2. `schemas/output.schema.json`:定义文章字段(标题/正文/配图/标签)
3. `checker/red-flags.md`:写入领域红线(未经核实的数据、禁用表述、长度越界)
4. 排版脚本:确定性工序,不进 LLM

## Run

```text
每次会话:读 STATE → 取「待写」选题 → Maker → Checker → 排版 → 更新 STATE
发布:独立 cron 按发布计划执行,与生产解耦
```

## Failure Modes

| 失败 | 症状 | 防护 |
|:---|:---|:---|
| 自我验证 | 质量忽高忽低 | Maker/Checker 强制双实例 |
| 事实错误 | 发布后被打脸 | 红线:无来源数据一票否决 |
| 风格漂移 | 越写越像 AI | 反测集含风格负例,改动 prompt 必跑 |
| 断更 | 计划在但没人执行 | STATE 驱动 + Monitor 断档告警 |

## Recovery

- 修订超限:文章退回「待写」并附失败摘要,人工决定重写或放弃
- 发布失败:重试 + 告警;文章状态保持「已排版」,不重复生产
- 选题枯竭:Monitor 检测待写队列为空,触发选题补充任务

## Metrics

- 一次通过率:Checker 首轮 PASS 占比(反映 Maker 稳定性)
- 平均修订轮次:超 1.5 轮说明 prompt 或提纲有问题
- 发布履约率:计划发布数 / 实际发布数
- 复盘数据:发布后表现回流 STATE,驱动选题与风格迭代
