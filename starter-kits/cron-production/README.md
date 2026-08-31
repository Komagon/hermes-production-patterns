# Cron Production Agent Starter Kit

> 定时自主运行的 Agent:可靠触发 + 状态 + 断点 + 错误压缩 + 监控。
> 适合:每日/每周定时任务,失败必须可发现、可恢复。

## Patterns Used

| Pattern | 文件 | 作用 |
|:---|:---|:---|
| Cron Job | `cron-config.example` | 幂等、防重复、防静默失败的调度 |
| State File | `STATE.md` | 跨运行进度与幂等键 |
| Checkpoint | `recovery/` | 中断后从断点恢复 |
| Error Compact | `recovery/error_compact.py` | 失败不污染上下文 |
| Monitor | `monitor/` | 失败可观测,不静默 |

## 安装

```bash
cp -r starter-kits/cron-production ~/my-cron-agent
cd ~/my-cron-agent
# 1. 编辑 cron-config.example 里的 schedule / prompt / skills
# 2. 复制为真实调度配置(Hermes cron 或系统 crontab)
# 3. 按 STATE.md 模板初始化状态
```

## 三段式设计(Pre-flight / Execute / Post-flight)

```
Pre-flight  读 STATE → 幂等键查重 → 确认本批未处理
Execute     按 SKILL 执行 → 每步写回 STATE(检查点)
Post-flight 汇总结果 → Monitor 记录成败 → 失败进入 recovery
```

## 验证

- [ ] 手动重跑不产生重复数据(幂等键生效)
- [ ] 中途 kill 后从断点恢复,不重头跑
- [ ] 失败时 Monitor 有记录/告警,不静默
- [ ] 错误以压缩摘要进上下文,非全文
