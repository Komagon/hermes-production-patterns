# 失败案例库 (Failure Case Studies)

> 每个案例都是从真实事故中抽象而来，用于教学和模式验证。

模式告诉你「应该怎么做」，失败案例告诉你「不做会怎样」。后者更难伪造，也更难忘记——所以每篇都开篇一句「如果你只记一句话」。

## 案例索引

| 案例 | 类型 | 影响 | 如果你只记一句话 | 涉及模式 |
|------|------|------|------|----------|
| [runaway-cron-tokens](runaway-cron-tokens.md) | 资源失控 | 一夜烧掉 $47 API token | 没有 `max_iterations` 和预算的 cron，等于把信用卡交给一个不会累的员工 | [cron-job-pattern](../../conventions/cron-job-pattern.md) |
| [silent-data-corruption](silent-data-corruption.md) | 数据损坏 | 连续 3 天产出错误报告 | 上游 schema 变了不会报错，只会安静地错 | [maker-checker](../../conventions/maker-checker.md), [checkpoint-pattern](../../conventions/checkpoint-pattern.md) |
| [concurrent-state-conflict](concurrent-state-conflict.md) | 状态冲突 | 两个 agent 互相覆盖 STATE.md | 先读后写 + 共享一个文件 = 必然互相覆盖 | [state-file-pattern](../../conventions/state-file-pattern.md), [multi-agent-isolation](../../conventions/multi-agent-isolation.md) |
| [prompt-injection-escalation](prompt-injection-escalation.md) | 安全漏洞 | 从网页注入执行了未授权命令 | 网页内容永远是数据，不是指令 | [secret-management](../../conventions/secret-management.md), [anti-patterns](../../conventions/anti-patterns.md) |

## 使用方式

每个案例遵循统一结构：

```
如果你只记一句话 → 场景描述 → 根因分析 → 事故日志 → 解决方案 → 关联模式
```

- **如果你只记一句话**: 开篇摘要，读完标题就能带走的那条规则
- **场景描述**: 发生了什么，面向非技术人员也能理解
- **根因分析**: 哪个 pattern 缺失导致了这个问题
- **事故日志**: 脱敏后的关键日志片段（时间戳、token 用量、错误信息）
- **解决方案**: 具体引用哪些 convention 文件来修复
- **关联模式**: 到 conventions/ 的链接

## 如何贡献新案例

1. 从真实事故中提取，脱敏处理
2. 确保能映射到至少一个 existing convention
3. 提交 PR，标题格式: `[failure] <案例名>`
