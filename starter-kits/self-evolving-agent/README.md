# Self-Evolving Agent Starter Kit

> 度量 → 基线 → 回归 → 进化闸门 → 部署/回滚 的完整自进化闭环。
> 这是高级 Starter Kit:先跑通基础 kit,再上这个。

## Patterns Used

| Pattern | 文件 | 作用 |
|:---|:---|:---|
| Data-Driven Optimization | `metrics/` | 用真实运行数据驱动改进,不凭感觉调 prompt |
| Baseline | `baseline/BASELINE.md` | 当前版本的行为基线,改动的对照物 |
| Regression | `regression/` | 每次改动跑反测:旧失败不再现 + 旧成功仍成立 |
| Evolution Gate | `evolution-gate/GATE.md` | G1-G5 五闸门 + 五维加权,过闸才部署 |
| Deploy / Rollback | `deploy/` `rollback/` | 部署留快照,失败可回滚 |

## 目录结构

```text
self-evolving-agent/
├── metrics/METRICS.md        # 指标定义与采集方式
├── baseline/BASELINE.md      # 基线记录(版本、指标快照、已知失败)
├── regression/regression.json
├── evolution-gate/GATE.md    # 过闸判定表
├── deploy/DEPLOY.md          # 部署流程(含快照)
├── rollback/ROLLBACK.md      # 回滚流程(触发条件、步骤)
└── README.md
```

## 进化循环

```text
运行采集 metrics
   ↓
与 baseline 对比 → 发现问题或改进机会
   ↓
提出改动(prompt/schema/流程)
   ↓
跑 regression 反测集
   ↓
过 Evolution Gate(G1-G5)
   ↓
deploy(带快照) → 观察一个完整周期
   ↓ 指标劣化
rollback(按 ROLLBACK.md)
```

## 铁律

- 没有指标数据不做改动——「感觉更好」不是证据
- 改动必须一个变量一次,不混合多改动
- 每次部署前 baseline 更新为上次通过验证的版本
- 回滚不丢数据:回滚的是行为,不是状态

## 安装

```bash
cp -r starter-kits/self-evolving-agent ~/my-evolving-agent
cd ~/my-evolving-agent
# 1. 在 metrics/METRICS.md 定义 3-5 个真实可采集的指标
# 2. 跑一轮记录 baseline
# 3. 把 GATE.md 挂进技能升级流程
```

## 验证

- [ ] 每个指标都有明确采集方式,不是主观打分
- [ ] 反测集覆盖上一次真实失败案例
- [ ] 过闸记录留痕(版本、五维得分、结论)
- [ ] 在非关键任务上演练过一次完整回滚
