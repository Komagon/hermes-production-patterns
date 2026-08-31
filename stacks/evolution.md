# 🔴 Evolution Stack

> 持续进化的官方组合:数据驱动、闸门管控、回归护航、可进可退。

## 组合

```text
Metrics
+
Data-Driven Optimization
+
Evolution Gate
+
Regression
+
Deploy / Rollback
```

## 对应公约

| Pattern | 公约 |
|:---|:---|
| 指标与采集 | `conventions/data-driven-optimization.md` |
| 进化闸门 | `conventions/evolution-gate.md` |
| 回归反测 | `test-prompts.json` |
| 技能升级 | `conventions/skill-evolution.md` |
| 自更新 | `conventions/self-update-pattern.md`(部署/回滚参考) |

## 什么时候用

- Agent 已稳定运行,进入改进期
- 改动频繁,需要防止「越改越坏」
- 对应成熟度 L3(自主执行 + 自我改进)

## 关键设计

```text
采集 metrics → 对比 baseline → 单变量改动
   ↓
regression 反测全量
   ↓
G1-G5 闸门 → Deploy(带快照) → 观察
   ↓ 劣化
Rollback(保状态,回行为)
```

## 判定红线

- 无指标数据不改动
- 反测不过不部署
- 劣化即回滚,不在劣化版本上继续修

## 落地方式

直接复制 `starter-kits/self-evolving-agent/`。
