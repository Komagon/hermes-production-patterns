# Basic Agent Starter Kit

> 最小的可运行 Agent:一个 Skill + 一个状态文件 + 控制流纪律。
> 适合:新用户 / 单任务 Agent / 本地实验。

## Patterns Used

| Pattern | 文件 | 作用 |
|:---|:---|:---|
| Skill Definition | `SKILL.md` | 把任务封装成可复用、可版本化的技能 |
| Basic State | `STATE.md` | 跨运行记住进度,重启不丢 |
| Control Flow Separation | `AGENTS.md` 约定 | 确定性步骤交给脚本,LLM 只做判断 |

## 安装

```bash
cp -r starter-kits/basic-agent ~/my-agent
cd ~/my-agent
# 按需编辑 SKILL.md 的 name/description/核心逻辑
```

## 使用

```bash
hermes run --skill SKILL.md --state STATE.md
```

## 验证

- [ ] `hermes run` 能正常触发技能
- [ ] 跑两次,第二次能读到 STATE.md 里的上次进度
- [ ] 确定性计算(聚合/换算)走脚本而非 LLM 心算
