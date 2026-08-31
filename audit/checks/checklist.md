# 审计检查单 Audit Checklist

> 每项 = 行为契约 + 证据要求。证据栏写「找什么才算数」。
> CLI 按本检查单逐项核对;人工审计同样适用。

## A. 可靠性 Reliability(25 分)

| # | 检查项 | 证据要求 | 分值 |
|:--|:---|:---|:---:|
| A1 | 幂等键存在且被使用 | STATE/代码中有幂等键生成与查重逻辑 | 8 |
| A2 | 重复触发不产生重复数据 | 重跑记录/幂等测试通过 | 7 |
| A3 | 静默失败防护 | 失败路径有记录/告警,存在「有触发无产出」检测 | 10 |

## B. 可观测性 Observability(20 分)

| # | 检查项 | 证据要求 | 分值 |
|:--|:---|:---|:---:|
| B1 | 运行记录留存 | monitor/runs.log 或等价的成败记录 | 8 |
| B2 | 失败可见 | 失败样例能被找到(日志/告警记录) | 7 |
| B3 | 关键指标可查 | 至少 3 个指标有定义与采集方式 | 5 |

## C. 可恢复性 Recoverability(20 分)

| # | 检查项 | 证据要求 | 分值 |
|:--|:---|:---|:---:|
| C1 | 状态先读后写 | STATE.md 有非空历史记录 | 6 |
| C2 | 检查点/断点续跑 | 中断后恢复的记录或测试 | 8 |
| C3 | 回滚预案 | 部署快照机制或回滚文档存在 | 6 |

## D. 质量控制 Quality(20 分)

| # | 检查项 | 证据要求 | 分值 |
|:--|:---|:---|:---:|
| D1 | 输出 schema 契约 | schemas/*.schema.json 存在且被引用 | 6 |
| D2 | 独立验证 | Checker 与 Maker 分离的证据(独立 prompt/会话) | 8 |
| D3 | 红线清单 | red-flags 类文件存在且非空 | 6 |

## E. 进化能力 Evolution(15 分)

| # | 检查项 | 证据要求 | 分值 |
|:--|:---|:---|:---:|
| E1 | 反测集存在 | regression.json / test-prompts.json 非空 | 6 |
| E2 | 基线与指标 | BASELINE/METRICS 类文件有实际数据 | 5 |
| E3 | 改动过闸记录 | 闸门判定/升级记录留痕 | 4 |

---

## 判定等级

| 总分 | 等级 | 建议 |
|:---:|:---|:---|
| ≥ 85 | Production Ready | 可长期无人值守运行 |
| 60–84 | Needs Hardening | 按缺失项 hpp add 补齐 |
| < 60 | Prototype | 只在有人监督下运行 |

## Maker/Checker 专项证据(Pattern Evidence 示例)

```text
✓ Maker exists         — maker prompt/角色存在
✓ Checker exists       — checker prompt/角色存在
✓ Separate execution   — 独立会话/子代理证据
✓ Output schema exists — schemas/ 非空且被 checker 引用
✓ Failure path exists  — FAIL 反馈模板 + 重试上限
✓ Evidence recorded    — 判定记录留痕
```
