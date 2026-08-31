# Recipes — 完整工程方案

> Starter Kit 是骨架,Recipe 是完整方案:真实场景、完整架构、失败模式与恢复路径。
> 每个 Recipe 九节齐全:Problem / Architecture / Patterns Used / Installation / Configuration / Run / Failure Modes / Recovery / Metrics。

## Recipe 索引

| Recipe | 场景 | 核心组合 |
|:---|:---|:---|
| [daily-news-agent](daily-news-agent.md) | 每日定时信息聚合与推送 | Cron + State + Error Compact |
| [content-pipeline](content-pipeline.md) | 内容生产发布流水线 | Maker/Checker + State + Cron |
| [research-pipeline](research-pipeline.md) | 研究调研流水线 | Evidence + Verifier + State |
| [autonomous-monitor](autonomous-monitor.md) | 无人值守监控告警 | Cron + Monitor + State |
| [coding-agent-pipeline](coding-agent-pipeline.md) | 编码任务流水线 | Maker/Checker + TDD 纪律 |
| [knowledge-agent](knowledge-agent.md) | 知识库问答与沉淀 | Memory OS + Retrieval |
| [multi-agent-workflow](multi-agent-workflow.md) | 多角色协同工作流 | 分工契约 + 状态总线 |

## 使用原则

- Recipe 是参考架构,不是黑盒:先读 Architecture 确认与你的场景匹配
- 每个 Recipe 都标注了对应 Starter Kit——先用 kit 起步,再按 Recipe 补齐工程细节
- Failure Modes 与 Recovery 是 Recipe 的价值所在,不要跳过
