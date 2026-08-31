# Production Audit — 生产就绪审计

> 审计的不是「文件存在」,是 Pattern Evidence:每个 Pattern 的关键行为是否有证据支撑。
> 规范(本页)+ 检查单(`checks/checklist.md`)+ 评分模型(`scoring/readiness-score.md`)。
> `cli/hpp audit` 按本规范输出得分与建议。

## 审计哲学

传统检查:「有 STATE.md 吗?」
生产审计:「STATE 是否真的在每步执行后写回?断电重跑会怎样?」

每条检查项 = 行为契约 + 可观察证据,不看声明看证据。

## 五维评分模型

| 维度 | 权重 | 检查什么 |
|:---|:---:|:---|
| 可靠性 Reliability | 25 | 幂等、防重复、静默失败防护 |
| 可观测性 Observability | 20 | Monitor、运行记录、失败可见 |
| 可恢复性 Recoverability | 20 | 检查点、断点续跑、回滚预案 |
| 质量控制 Quality | 20 | 独立验证、schema、红线、回归 |
| 进化能力 Evolution | 15 | 指标、基线、反测集、闸门 |

## 审计流程

```text
1. 声明收集:SKILL/AGENTS frontmatter + 目录结构
2. 证据核对:逐检查项找证据(文件/日志/记录)
3. 五维打分:每维按检查单计分
4. 产出报告:总分 + 各维得分条 + 缺失项 + hpp add 建议
```

## 报告格式

```text
Production Readiness Score: 68/100

Reliability        █████████░ 90
Observability      ██████░░░░ 60
Recoverability     ████████░░ 80
Quality            █████████░ 90
Evolution          ████░░░░░░ 40

✓ Skill Contract    ✓ State Management
⚠ No Output Validation    ⚠ No Regression Tests
✗ No Failure Recovery

Recommended:
hpp add maker-checker
hpp add error-compact
hpp add regression-suite
```
