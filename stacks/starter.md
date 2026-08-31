# 🟢 Starter Stack

> 最小官方组合:能跑、有记忆、控制流不乱。所有旅程的起点。

## 组合

```text
SKILL Definition
+
STATE File
+
Control Flow Separation
```

## 对应公约

| Pattern | 公约 |
|:---|:---|
| Skill 定义 | `conventions/control-flow-separation.md`(Skill 契约部分) |
| 状态管理 | `conventions/state-file-pattern.md` |
| 控制流分离 | `conventions/control-flow-separation.md` |

## 什么时候用

- 新项目起步,还没有失败模式数据
- 单任务、人工触发频率高的场景
- 对应成熟度 L1(只报告,不自主)

## 什么时候升级

出现以下任一信号,升级到 🟡 Reliable Automation Stack:

- 任务开始无人值守运行(cron)
- 第一次出现静默失败
- 单次任务时长超过 10 分钟

## 落地方式

直接复制 `starter-kits/basic-agent/`,它就是这个 Stack 的代码骨架。
