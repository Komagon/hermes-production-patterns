# Recipe: Coding Agent Pipeline — 编码任务流水线

## Problem

编码 Agent 最常见的失败链:生成代码 → 自己说「测试通过」→ 实际没跑或跑的是空测试。代码是要执行的,验证必须独立且可执行,否则产出的不是代码,是看起来像代码的文本。

## Architecture

```text
任务单(issue/需求,STATE.md 驱动)
   ↓
Maker:理解需求 → 写代码 + 写测试
   ↓
Runner(确定性):真实执行测试/构建/lint,产出原始结果
   ↓
Checker(独立实例):审查代码与测试质量 + 复核 Runner 结果
   ↓ PASS
提交(小步提交,可回滚)
   ↓ FAIL
失败压缩摘要 → Maker 修订(≤2 次)→ 超限人工
```

## Patterns Used

| Pattern | 公约 |
|:---|:---|
| Maker/Checker | `conventions/maker-checker.md` |
| 控制流分离 | `conventions/control-flow-separation.md`(执行/构建走脚本) |
| 状态管理 | `conventions/state-file-pattern.md`(任务单进度) |
| 错误压缩 | `conventions/error-compact-pattern.md`(测试失败摘要) |
| 检查点 | `conventions/checkpoint-pattern.md`(长任务分段提交) |

对应 Starter Kit:`starter-kits/maker-checker/`。

## Installation

```bash
cp -r starter-kits/maker-checker ~/coding-pipeline
cd ~/coding-pipeline
# schemas/output.schema.json 换成代码任务契约(diff/测试清单/验证结果)
```

## Configuration

1. 任务单格式:需求 + 验收标准(可执行的验收,不写「代码质量好」)
2. 测试纪律:Maker 必须同时交付测试;测试先于实现(TDD 可选但推荐)
3. Runner:统一入口脚本跑 `build + test + lint`,输出结构化结果
4. 提交纪律:小步提交,每步可独立回滚

## Run

```text
每个任务单一个分支;STATE 记录「进行中/待审/已合并」
Runner 永远由流水线触发,不由 Maker 自己宣称
```

## Failure Modes

| 失败 | 症状 | 防护 |
|:---|:---|:---|
| 虚假验证 | 「测试通过」但没跑 | Runner 强制执行,Checker 复核结构化结果 |
| 空测试 | 测试存在但无断言 | 红线:无断言测试 = FAIL |
| 范围蔓延 | 顺手改无关代码 | 契约:diff 超出任务单范围 = FAIL |
| 上下文爆炸 | 长报错刷屏 | 失败摘要压缩进上下文,全文落盘 |

## Recovery

- 测试失败:压缩摘要(文件:行号 + 断言差异)回给 Maker,不贴全文
- 修订超限:分支保留 + 摘要归档,人工接管
- 环境损坏:Runner 环境可重建(容器/脚本化 setup),不修坏环境
- 中断恢复:已提交的小步不重做,从 STATE 记录处继续

## Metrics

- 一次通过率:Checker 首轮 PASS 占比
- 测试有效性:反测「空测试/假通过」用例的拦截率(应为 100%)
- 修订轮次均值:超 1.5 轮 → 任务拆分粒度问题
- 回滚率:合并后 revert 占比(质量后验指标)
