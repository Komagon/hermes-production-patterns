# 10-Minute Quick Start — 从零到第一个 Production Agent

> 目标:10 分钟内,你有一个带状态、可验证、能定时运行的 Agent 骨架。
> 本教程是 Journey A(新用户)的主路径,全部使用仓库内文件,零外部依赖。

## 前置

- 已安装 [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- 已 clone 本仓库

```bash
git clone https://github.com/Komagon/hermes-production-patterns.git
cd hermes-production-patterns
```

---

## Step 1 — 复制 Starter Kit(1 分钟)

```bash
cp -r starter-kits/basic-agent ~/my-agent
cd ~/my-agent
```

你得到:SKILL.md + STATE.md + AGENTS.md + .env.example。

## Step 2 — 定义技能(3 分钟)

打开 SKILL.md,只改三处:

1. `name`:你的任务名
2. `description`:「什么触发 + 做什么 + 产出什么」一句话
3. 核心逻辑节:把示例任务换成你的真实任务

原则:确定性步骤(换算、聚合、格式化)写明用脚本,不要让 LLM 心算。

## Step 3 — 初始化状态(1 分钟)

STATE.md 已经是可用的空状态。每次运行:

```text
先读 STATE → 干活 → 每步写回 STATE
```

这就是重启不丢进度的全部秘密。

## Step 4 — 第一次运行(2 分钟)

```bash
hermes run --skill SKILL.md --state STATE.md
```

验证三件事:

- [ ] 技能被正常触发
- [ ] 跑两次,第二次读到上次的进度
- [ ] 输出符合 SKILL.md 里的产出要求

## Step 5 — 加上独立验证(2 分钟)

把 `starter-kits/maker-checker/checker/PROMPT.md` 复制过来,在**另一个会话**里用 Checker 角色验证你的产出:

```text
# 会话 2(独立实例)
加载 checker PROMPT → 对照产出判定 PASS/FAIL
```

这一步解决 Agent 生产环境最大的坑:自己验自己。

## Step 6 — 挂上定时(1 分钟)

参考 `starter-kits/cron-production/cron-config.example`,把你的技能配置成每日定时任务,并确认:

- [ ] 幂等键:同一周期重复触发不会重复执行
- [ ] 失败可见:失败会写入 monitor 记录,不静默

---

## 完成 — 你现在的架构

```text
Trigger(cron / 手动)
   ↓
Agent(SKILL.md 定义)
   ↓
STATE(跨运行进度)
   ↓
Checker(独立验证)
   ↓
Publish / Fail→Retry
```

这就是 🟢 Starter Stack + 🔵 Quality Stack 的雏形。

## 下一步

| 想加什么 | 去哪里 |
|:---|:---|
| 断点恢复、错误压缩 | [cron-production kit](starter-kits/cron-production/README.md) |
| 完整质量流水线 | [maker-checker kit](starter-kits/maker-checker/README.md) |
| 官方组合总览 | [Stacks](stacks/starter.md) |
| 真实工程方案 | [Recipes](recipes/index.md) |
| 检查你的 Agent 靠不靠谱 | [Production Audit](audit/audit.md) |
