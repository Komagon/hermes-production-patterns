---
name: Pattern Proposal
about: 提议一个新的工程模式（必须附带生产验证证据）
title: '[Pattern] '
labels: enhancement
---

## 解决什么问题

<!-- 用一句话描述这个模式解决的生产痛点。 -->

## 生产验证证据

<!-- ⚠️ 不接受纯理论设计。至少提供以下一项： -->

- [ ] 附带脱敏后的 STATE.md 快照或运行日志片段
- [ ] 附带接入前后的量化对比数据（如失败率、人工介入次数）
- [ ] 附带真实使用者的反馈截图或链接

**证据内容：**

```
（粘贴日志/STATE.md 快照/数据表格）
```

## 设计思路

<!-- 模式的核心机制是什么？与现有 conventions/ 中的模式如何配合？ -->

## 与现有模式的关系

<!-- 勾选相关的现有模式，说明是扩展、替代还是互补。 -->

- [ ] `state-file-pattern` — 状态管理
- [ ] `maker-checker` — 双角色验证
- [ ] `cron-job-pattern` — 定时任务
- [ ] `error-compact-pattern` — 错误压缩
- [ ] `control-flow-separation` — 控制流分离
- [ ] `checkpoint-pattern` — 检查点恢复
- [ ] `skill-evolution` — 技能进化
- [ ] `evolution-gate` — 进化闸门
- [ ] 其他：___

## 改前 vs 改后

<!-- 用代码块对比展示"没有这个模式"和"有这个模式"的区别。 -->
