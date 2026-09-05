# 实战案例 Examples

本目录存放 Hermes Production Patterns 的真实落地案例。每个案例都遵循「先有真实运行，再有文档」——能复现的输出比描述更有说服力。

| 案例 | 覆盖能力 | 状态 |
|:----|:--------|:----:|
| [真实运行验证 2026-09](capability-verification-2026-09.md) | 浏览器自动化 / 消息网关 / 多模态产出 / 检索强化 | ✅ 4 族 9 项全通过 |
| [公众号文章流水线](wechat-article-pipeline.md) | 写作 / 去 AI 味 / 配图 / 排版 | battle-tested |
| [Maker/Checker 文章流水线](maker-checker-article-pipeline.md) | Maker/Checker 分离 + 手动/Opik 双通道 | battle-tested |
| [每日新闻摘要](daily-news-digest.md) | Cron + 去重 + 摘要 + 投递 | battle-tested |
| [Cron 安全集成](cron-safety-integration.md) | Cron 安全护栏 / 防重复 / 防静默失败 | battle-tested |
| [极简 Demo](minimal-demo/README.md) | cron 最小可运行骨架 | 参考 |
| [失败案例复盘](failures/README.md) | Token 失控 / 数据损坏 / 状态冲突 / 注入越权 | 反面教材 |

> 新增能力时：先在本文档登记入口，再到 [能力 × 模式映射](../conventions/hermes-capability-map.md) 对号入座，最后在 [能力验证](capability-verification-2026-09.md) 留存可复现的真实运行输出。
