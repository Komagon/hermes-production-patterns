---
name: skill-evolution
description: "技能进化管理 — 如何从 v1 升级到 v2，不破坏现有工作流"
version: 1.3.1
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, skill, evolution, lifecycle]
    category: conventions
    related_skills: [maker-checker, state-file-pattern, maturity-staging]
migration: "v1.2.0 → v1.3.0:新增「回归反测集」章节(借鉴 dao-skill test-prompts.json);v1.3.0 → v1.3.1:澄清反测覆盖范围(14 个行为契约技能,capability-map 豁免)与运行范围(升级跑映射条目/发版跑全量/失败处置)"
---

# 技能进化管理

> **一个不进化的工作流，终将被废弃。一个进化但没有版本控制的工作流，终将崩坏。**

## 核心原则

**每条技能都有一个生命周期。** 从创建到稳定到废弃，必须有明确的阶段管理，不能靠「我记得以前不是这样跑的」。

## 技能生命周期

```text
草案（Draft） → 试用（Beta） → 稳定（Stable） → 废弃（Deprecated） → 移除（Removed）
```

| 阶段 | 谁可以用 | 谁来改 | 是否有版本号 |
|:---|:--------|:------|:----------:|
| **Draft** | 仅作者 | 任何人 | ❌ |
| **Beta** | 限定用户 | 作者+review | ✅ v0.x |
| **Stable** | 所有人 | 必须走 PR | ✅ v1.x+ |
| **Deprecated** | 不推荐新用户 | 仅修 bug | ✅ 标记 deprecated |
| **Removed** | — | — | — |

## 版本化约定

每个 SKILL.md 的 frontmatter 中必须有 `version` 字段：

```yaml
---
name: my-skill
version: 1.2.0
---
```

版本号规则（SemVer）：

| 变动类型 | 版本号变动 | 例子 |
|:--------|:---------|:-----|
| 修复 bug、措辞修正 | Patch | 1.0.0 → 1.0.1 |
| 新增功能、参数 | Minor | 1.0.0 → 1.1.0 |
| 破坏性变更（接口不兼容） | Major | 1.0.0 → 2.0.0 |

## 升级流程

### 从 Stable v1 → v2

```
1. 创建分支: git checkout -b feat/skill-v2
2. 修改 SKILL.md，version 改为 2.0.0
3. 在 frontmatter 中加 migration 字段：
   migration: "从 v1 升级到 v2：FIELD_X 改为 FIELD_Y"
4. 更新所有引用此技能的 convention 和 example
5. 创建测试用例验证 v2 行为
6. 提交 PR，标注为 major change
7. 合入后通知所有使用者
```

### 向后兼容

| 变更类型 | 必须兼容？| 做法 |
|:--------|:--------:|:-----|
| 新增字段 | ✅ 是 | 旧值保持默认行为 |
| 改字段名 | ❌ 否 | 加 migration 说明 |
| 删功能 | ❌ 否 | 先 deprecated 一个周期再删 |
| 修 bug | ✅ 是 | 不改接口 |

## 回归反测集(2026-08-27,借鉴 dao-skill)

**技能升级的验收标准不是「看起来对」，而是「旧失败不再出现、旧成功仍然成立」。** 反测集就是把这句口号变成可执行资产。

- **位置**:`hermes-production-patterns/test-prompts.json`(与 15 个技能平级),20 条回归提示词,每条含 `prompt / expected / assertions(应命中) / forbidden(禁止触犯)`。
- **覆盖范围**:14 个行为契约技能 1:1 全覆盖;`hermes-capability-map` 为参考映射表(无行为契约,不设陷阱式反测,其正确性由 CI 链接检查与人工审校保证)。
- **何时跑**:
  - 任何技能 major/minor 升级后 → 跑该技能相关反测条目(至少 1 条)
  - 用户反馈「不对 / 不好用 / 还是老样子」→ 先跑对应反测定位是技能缺陷还是 Agent 未遵守
  - evolution-gate G5 回归对比 → 反测条目即回归测试资产
- **怎么跑**:把条目的 `prompt` 喂给 Agent(或复盘历史会话),检查行为是否命中所有 `assertions`、未触任何 `forbidden`。结构检查(SKILL.md 格式/语法)不等于行为反测——dry-run 不能当已验证。
- **新增条目规则**:每修复一个「真实发生的失败模式」,就补一条能暴露旧失败的反测条目;同根同触发合并进现有条目,不无脑堆条目(防膨胀,呼应瘦身原则)。
- **铁律**:改完技能不跑反测 = 改完技能不验证 = 禁止宣称完成。
- **范围说明**:任何技能 major/minor 升级后只跑该技能映射的 1-2 条(按下方速查表 1:1 查表);全量 20 条只在发版 tag 前跑,或当被改技能是横切技能(`evolution-gate` / `pattern-composition`,它们影响其他技能的验证方式)时跑。条目失败时:先重跑一次排除偶发,再犯则按 Deploy-or-Rollback 回滚,修复该条目后才允许合并——这是 G5 数据闸的落地形态。

### 反测覆盖速查

| 技能 | 反测条目 id |
|:---|:---|
| evolution-gate | evolution-gate-required / evolution-gate-deploy-or-rollback |
| state-file-pattern | state-file-read-before-run / state-file-write-after-step |
| checkpoint-pattern | checkpoint-recovery / checkpoint-session-recovery-search |
| maker-checker | maker-checker-separation |
| self-update-pattern | self-update-backup-first / self-update-rollback-condition |
| secret-management | secret-management-env-only |
| error-compact-pattern | error-compact-before-context |
| control-flow-separation | control-flow-code-not-llm |
| cron-job-pattern | cron-idempotency-key / cron-no-silent-failure |
| data-driven-optimization | data-driven-optimization |
| skill-evolution | skill-evolution-backward-compat / skill-evolution-versioned-files |
| anti-patterns | anti-patterns-no-adhoc-prompt |
| pattern-composition | pattern-composition-selection |
| memory-os-pattern | memory-os-write-discipline |
| hermes-capability-map | (豁免:参考映射表,无行为契约;由 CI 链接检查保证) |

## 与 STATE.md 的配合

每次技能版本变更后，更新 STATE.md 中的 `skill_version` 字段：

```markdown
## Skill Version
- name: maker-checker
- version: 1.2.0
- updated: 2026-07-15
- migration: 新增「五维验证评分」可选参数
```

## 废弃流程

```
1. 在 SKILL.md frontmatter 加: status: deprecated
2. 在 README 中标注为 deprecated
3. 保留 30 天，期间只修 bug
4. 30 天后移除文件，在 CHANGELOG 中记录
```

## 落地工具：skill_manage（2026-08）

Hermes 原生 `skill_manage` 是技能进化的执行工具：

| 动作 | 对应生命周期阶段 |
|:----|:----------------|
| `patch`（old_string/new_string 精确替换） | Stable 小修（v1.0.x → v1.0.y）：加坑位、改措辞 |
| `edit`（整文件重写） | Major 升级（v1 → v2） |
| `delete` + `absorbed_into=<umbrella>` | Deprecated/Removed：声明内容并入哪个技能（无去向则传空串=纯废弃） |
| `write_file` / `remove_file` | 管理技能的 references / templates / scripts 子文件（版本化引用资产） |

**要点：** 技能升级用 `patch` 而不是整文件重写（保留 frontmatter 与历史上下文）；废弃技能必须带 `absorbed_into` 声明去向，让下游（引用该技能的 cron/文档）可追踪。

## 技能瘦身（Skill Slimming，2026-08 实践）

**进化不只有加法，还有减法。** 技能最常见的死亡方式是「臃肿」：框架越写越厚、章节越叠越多，触发条件埋在正文深处，真正有用的约束被淹没。瘦身是技能进化的第一优先动作。

### 什么时候必须瘦身

- description 超过 57 字符被截断（系统只显示前 57 字符 + `...`）——触发条件必须在 57 字符内说清
- 技能里有「大而全」的框架章节，但实际使用只用其中 20%
- 用户反复手动纠正的内容（如「只要保留 X，其余都删」）——这是最硬的数据信号
- 更新技能时发现旧内容没人再引用（检查 STATE.md usage_count / 会话记录）

### 瘦身三原则

1. **只留会用的** — 删掉所有「理论上应该」的框架，保留「实际每次都用」的核心
2. **触发条件前置** — description 前 57 字符内写清「何时用这个技能」，让加载决策零成本
3. **约束而非教程** — 技能里放硬约束（标题 ≤ 30 字、禁盘点型内容），不放通用方法论（方法论进 vault 知识库，不占技能上下文）

### 实战案例（2026-08-16）

头条写作技能瘦身：用户明确要求「只留标题 ≤ 30 字 + 账号定位 + 去 AI 味」，其余框架（文章结构、章节限定、模板）全部删除。瘦身后技能更小、加载更快、指令更聚焦——**技能的价值在于约束精准，不在于篇幅完整。**

### 反模式

| ❌ 错误做法 | 后果 |
|:---|:---|
| 技能越改越厚，章节只增不减 | 上下文预算被占满，核心约束被淹没 |
| description 写满 200 字符 | 系统截断后触发条件丢失，技能被错误加载 |
| 把通用方法论塞进技能 | 每次加载都重复读教程，浪费 token |
| 用户说「只留 X」还保留 Y | 违背用户意图，技能失去信任 |
