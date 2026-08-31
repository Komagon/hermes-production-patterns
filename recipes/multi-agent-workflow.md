# Recipe: Multi-Agent Workflow — 多角色协同工作流

## Problem

多个 Agent 协作时,失败往往不在单个 Agent,而在「接缝」:角色边界模糊(谁都改同一文件)、状态不同步(A 用旧数据)、互相等待死锁、一个挂了全链路挂。多 Agent 的本质工程问题是契约与状态。

## Architecture

```text
编排器(确定性脚本/单一主 Agent,不是民主投票)
   ↓ 按契约分发
Role A(Maker)──产出+schema──→ 共享状态区
   ↓
Role B(Checker/加工)──判定/转换──→ 共享状态区
   ↓
Role C(执行/发布)
   ↓
状态总线(STATE.md per role + 全局 STATE)
```

## Patterns Used

| Pattern | 公约 |
|:---|:---|
| Maker/Checker | `conventions/maker-checker.md`(角色分离是特例) |
| 控制流分离 | `conventions/control-flow-separation.md`(编排用确定性代码) |
| 状态管理 | `conventions/state-file-pattern.md`(角色间通信靠状态不靠记忆) |
| 检查点 | `conventions/checkpoint-pattern.md`(链路断点恢复) |
| 反面模式 | `conventions/anti-patterns.md`(民主编排、无契约协作) |

对应 Starter Kit:`starter-kits/maker-checker/` 起步,按角色扩展。

## Installation

```bash
cp -r starter-kits/maker-checker ~/multi-agent
cd ~/multi-agent
# 每个新角色复制一份 maker/ 或 checker/ 结构,PROMPT 换角色契约
```

## Configuration

1. 角色契约:每个角色一页 PROMPT(职责/输入/输出/禁止),字段与 schema 对齐
2. 文件租约:一个文件同一时间只有一个角色可写,写完声明完成
3. 状态总线:全局 STATE + 每角色 STATE;交接即状态变更
4. 超时与心跳:每个角色有预期完成时限,超时触发干预而非无限等待

## Run

```text
编排器按 DAG 推进:每步「前置状态确认 → 分发 → 收产物 → 校验 → 记状态」
任何一步校验不过,不进入下游
```

## Failure Modes

| 失败 | 症状 | 防护 |
|:---|:---|:---|
| 接缝错配 | 下游拿到不合 schema 的产物 | 交接点 schema 校验,不过不收 |
| 文件冲突 | 两个角色改同一文件 | 文件租约 + 编排器裁决 |
| 状态不同步 | 基于过期数据决策 | 交接必须经状态总线,禁止口头/记忆传递 |
| 死锁 | 互相等待 | 心跳 + 超时干预;编排器单点推进 |
| 单点崩溃 | 一挂全挂 | 每步检查点,恢复从断点角色续跑 |

## Recovery

- 角色失败:该角色状态置「失败+原因」,编排器决定重试或降级
- 链路中断:各角色 STATE 完好,从断点续跑,已完成产物不重做
- 契约冲突:角色契约冲突时,编排器有最终裁决权(不民主投票)

## Metrics

- 交接一次通过率:下游首次校验通过占比(衡量上游质量)
- 角色超时率:各角色超时频次(定位瓶颈角色)
- 断点恢复成功率:中断后续跑不重做的比例
- 端到端时延:全链路完成时间,按阶段分解定位
