---
name: skill-evolution
description: "技能进化管理 — 如何从 v1 升级到 v2，不破坏现有工作流"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, skill, evolution, lifecycle]
    category: conventions
    related_skills: [maker-checker, state-file-pattern, maturity-staging]
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
