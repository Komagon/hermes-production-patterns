# Starter Kits — 起步套件

> Pattern 告诉你为什么,Starter Kit 给你可复制的骨架。选一个贴近你场景的 kit,`cp -r` 开跑。

## 选择路径

| 你要做什么 | 用哪个 Kit | 复杂度 |
|:---|:---|:---|
| 第一个 Agent,本地实验 | [basic-agent](basic-agent/README.md) | ★ |
| 定时自主运行,失败必须可恢复 | [cron-production](cron-production/README.md) | ★★ |
| 产出质量要求高,不能自己验自己 | [maker-checker](maker-checker/README.md) | ★★ |
| 结论必须有出处的研究任务 | [research-agent](research-agent/README.md) | ★★★ |
| 长期运行,需要积累经验 | [memory-agent](memory-agent/README.md) | ★★★ |
| 持续自我改进,可回滚 | [self-evolving-agent](self-evolving-agent/README.md) | ★★★★ |

## 使用原则

1. **Run First, Understand Later**:先复制跑通,再读对应公约理解设计意图
2. **一个 Kit 解决一类问题**:不要一开始就把 6 个 kit 叠在一起
3. **每个 kit 都有验证清单**:跑通后逐项打勾,打不全勾不算装好

## Kit 与公约的对应

每个 kit 的 Patterns Used 表都指向 `conventions/` 下的公约原文——骨架是快捷方式,公约是原理。
