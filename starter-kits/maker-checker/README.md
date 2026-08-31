# Maker/Checker Pipeline Starter Kit

> 生成与验证分离的双角色流水线:Maker 产出,Checker 独立验证,失败走压缩反馈与重试。
> 适合:内容生产 / 代码生成 / 研究报告 / 任何失败代价高的任务。

## Patterns Used

| Pattern | 文件 | 作用 |
|:---|:---|:---|
| Maker/Checker | `maker/PROMPT.md` + `checker/PROMPT.md` | 生成与验证必须是两个独立 Agent 实例 |
| Output Schema | `schemas/output.schema.json` | Checker 用 schema 判定,不凭感觉 |
| Red Flags | `checker/red-flags.md` | 硬性一票否决线,违反即 FAIL |
| Error Compact | `checker/feedback.template.md` | FAIL 反馈压缩成结构化摘要,不污染 Maker 上下文 |
| Regression | `regression/regression.json` | 每次改动跑反测集,旧失败不再出现 + 旧成功仍成立 |

## 目录结构

```text
maker-checker/
├── maker/PROMPT.md          # Maker 角色提示词
├── checker/PROMPT.md        # Checker 角色提示词(独立实例)
├── checker/red-flags.md     # 一票否决红线清单
├── checker/feedback.template.md  # FAIL 反馈模板(结构化)
├── schemas/output.schema.json    # 产出契约
├── regression/regression.json    # 反测集(新增条目规则见内注释)
└── README.md
```

## 安装

```bash
cp -r starter-kits/maker-checker ~/my-mc-pipeline
cd ~/my-mc-pipeline
# 1. 把 maker/PROMPT.md 里的任务描述换成你的真实任务
# 2. 按产出物字段调整 schemas/output.schema.json
# 3. 按业务红线补充 checker/red-flags.md
```

## 流程

```text
Maker(独立实例) 产出
        ↓
Checker(另一个独立实例) 对照 schema + red-flags 判定
        ↓
PASS → 交付 / Publish
FAIL → feedback.template.md 压缩反馈 → Maker 修订(有界重试)
超限 → 升级人工
```

## 使用

```text
# 会话 1(Maker):加载 maker/PROMPT.md,执行任务产出初稿
# 会话 2(Checker):加载 checker/PROMPT.md,只看产出物本身,独立判定
# Checker 不看 Maker 的推理过程,只验产出
```

## 验证

- [ ] Maker 与 Checker 在两个独立会话/实例中运行
- [ ] Checker 判定有 schema 依据,结论可复现
- [ ] FAIL 反馈是压缩摘要,不是全文粘贴
- [ ] 重试有上限,超限升级人工而非无限循环
- [ ] 改动 prompt 后跑 regression/regression.json,旧行为不回退
