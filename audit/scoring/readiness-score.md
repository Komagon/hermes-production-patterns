# Production Readiness Score — 评分模型 v1.0

> 五维加权 100 分制。`cli/hpp audit` 与人工审计共用本模型,保证口径一致。

## 维度与权重

| 维度 | 权重 | 数据来源 |
|:---|:---:|:---|
| Reliability | 25 | audit/checks/checklist.md A 组 |
| Observability | 20 | B 组 |
| Recoverability | 20 | C 组 |
| Quality | 20 | D 组 |
| Evolution | 15 | E 组 |

## 计分规则

1. 每个检查项按 checklist 分值逐项判定:有证据 = 满分,部分证据 = 一半,无证据 = 0
2. 维度得分 = 组内得分 / 组内满分 × 维度权重
3. 总分 = 五维之和(取整)
4. 显示:总分 + 五维条形图(░█ 十格)

## 条形图渲染

```text
Reliability        █████████░ 90
```

- 十格:每格 = 10 分
- 得分换算成 0-100 显示(该维度的百分比)

## 建议生成规则

缺失项 → 推荐命令映射:

| 缺失 | 建议 |
|:---|:---|
| D1/D2/D3 | `hpp add maker-checker` |
| A3/B1/B2 | `hpp add cron-production`(monitor/recovery) |
| C1/C2 | `hpp add checkpoint` |
| E1/E2/E3 | `hpp add regression-suite` |
| A1/A2 | `hpp add cron-production` |

## 版本化

- 模型变更(权重/检查项)必须 bump 本文件版本号并更新 CHANGELOG
- 历史得分只在同版本模型内可比;跨版本比较需重跑审计
