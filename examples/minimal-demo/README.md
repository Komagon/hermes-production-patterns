# Minimal Demo: STATE.md + Cron

最简单的可运行示例：一个 Cron 脚本 + STATE.md，让你在 5 分钟内看到「状态文件自动更新」的 aha moment。

## 快速开始

```bash
# 1. 创建工作目录
mkdir -p ~/my-first-agent/reports
cd ~/my-first-agent

# 2. 复制 STATE.md 模板
cp /path/to/hermes-production-patterns/templates/STATE.md.template reports/STATE.md

# 3. 运行模拟脚本（不需要 Hermes，纯演示状态流转）
python /path/to/hermes-production-patterns/examples/minimal-demo/demo_cron.py
```

## 你会看到什么

脚本模拟一个 Cron 任务的完整生命周期：

1. **读取 STATE.md** — 显示当前状态
2. **执行模拟任务** — 随机成功/失败
3. **写回 STATE.md** — 更新进度、状态、幂等键
4. **再次运行** — 演示幂等（跳过已完成的批次）

每次运行后，打开 `reports/STATE.md`，你会看到状态文件在自动更新。

## 核心概念映射

| 你看到的 | 对应模式 |
|:---|:---|
| 脚本先读 STATE.md | [state-file-pattern](../../conventions/state-file-pattern.md) — Read Before Run |
| 每步写回 STATE.md | [state-file-pattern](../../conventions/state-file-pattern.md) — Write After Every Step |
| 成功/失败都有记录 | [cron-job-pattern](../../conventions/cron-job-pattern.md) — 防静默失败 |
| 已完成批次自动跳过 | [cron-job-pattern](../../conventions/cron-job-pattern.md) — 幂等 |
| 错误被压缩成一行 | [error-compact-pattern](../../conventions/error-compact-pattern.md) |

## 下一步

- 把 `demo_cron.py` 的 `simulate_task()` 换成你的实际任务逻辑
- 按 [quickstart.md](../../quickstart.md) 配置 Hermes Agent
- 按 [starter-kits/cron-production](../../starter-kits/cron-production/) 搭建生产级 Cron
