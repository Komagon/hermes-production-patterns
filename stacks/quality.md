# 🔵 Quality Stack

> 输出质量的官方组合:生成与验证分离,红线兜底,回归防劣化。

## 组合

```text
Maker
+
Checker
+
Red Flags
+
Regression
```

## 对应公约

| Pattern | 公约 |
|:---|:---|
| 双角色分离 | `conventions/maker-checker.md` |
| 反面模式 | `conventions/anti-patterns.md`(自我验证条目) |
| 回归反测 | `test-prompts.json` + `conventions/skill-evolution.md` |

## 什么时候用

- 产出会外发(发布、交付、存档)
- 失败的代价是声誉或下游损失,不是重跑一次
- Agent 输出质量不稳定,靠肉眼审查撑不住

## 关键设计

```text
Maker(独立实例)产出
   ↓
Checker(另一个实例)对照 schema + red-flags
   ↓
PASS → 交付     FAIL → 压缩反馈 → 有界重试
```

## 判定红线

- Checker 与 Maker 永远不是同一个会话
- 反馈是结构化摘要,不是全文粘贴
- 每次修改行为文件后跑 regression,双通过才部署

## 落地方式

直接复制 `starter-kits/maker-checker/`。
