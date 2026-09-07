---
name: skill-evolution
description: "技能进化管理 — 如何从 v1 升级到 v2，不破坏现有工作流"
version: 1.3.3
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, skill, evolution, lifecycle]
    category: conventions
    related_skills: [maker-checker, state-file-pattern, evolution-gate]
migration: "v1.2.0 → v1.3.0:新增「回归反测集」章节(借鉴 dao-skill test-prompts.json);v1.3.0 → v1.3.1:澄清反测覆盖范围(14 个行为契约技能,capability-map 豁免)与运行范围(升级跑映射条目/发版跑全量/失败处置);v1.3.1 → v1.3.2:反测集补硬门禁判定纪律(N/A 与验证失败分离/横切技能强制门禁/分数封顶,借鉴 iFixAi);v1.3.2 → v1.3.3:新增变更后自动验证强制 hook(改 skill 必跑 ①routing_check+capability_probe ②反向引用 grep ③反测,缺项不结项)"
hpp_category: evolution
hpp_en: "Evolve skills v1 to v2 without breaking current users."
hpp_maturity: L2
hpp_complexity: medium
hpp_reliability: medium
hpp_capability: skills
maturity: beta
hpp_when_to_use: ["Iterating production skills"]
hpp_when_not_to_use: ["Scratch skills with no dependents"]
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

- **位置**:`hermes-production-patterns/test-prompts.json`(与 19 个技能平级),30 条回归提示词,每条含 `prompt / expected / assertions(应命中) / forbidden(禁止触犯)`。
- **覆盖范围**:19 个行为契约技能 1:1 全覆盖;`hermes-capability-map` 为参考映射表(无行为契约,不设陷阱式反测,其正确性由 CI 链接检查与人工审校保证)。
- **何时跑**:
  - 任何技能 major/minor 升级后 → 跑该技能相关反测条目(至少 1 条)
  - 用户反馈「不对 / 不好用 / 还是老样子」→ 先跑对应反测定位是技能缺陷还是 Agent 未遵守
  - evolution-gate G5 回归对比 → 反测条目即回归测试资产
- **怎么跑**:把条目的 `prompt` 喂给 Agent(或复盘历史会话),检查行为是否命中所有 `assertions`、未触任何 `forbidden`。结构检查(SKILL.md 格式/语法)不等于行为反测——dry-run 不能当已验证。
- **新增条目规则**:每修复一个「真实发生的失败模式」,就补一条能暴露旧失败的反测条目;同根同触发合并进现有条目,不无脑堆条目(防膨胀,呼应瘦身原则)。
- **铁律**:改完技能不跑反测 = 改完技能不验证 = 禁止宣称完成。
- **范围说明**:任何技能 major/minor 升级后只跑该技能映射的 1-2 条(按下方速查表 1:1 查表);全量 30 条只在发版 tag 前跑,或当被改技能是横切技能(`evolution-gate` / `pattern-composition`,它们影响其他技能的验证方式)时跑。条目失败时:先重跑一次排除偶发,再犯则按 Deploy-or-Rollback 回滚,修复该条目后才允许合并——这是 G5 数据闸的落地形态。

### 硬门禁判定纪律(2026-09-07,借鉴 iFixAi)

**反测结果不是「加权平均的分数」,而是有三条不可违背的门禁。** 借鉴 iFixAi 的 mandatory-minimum + 评分封顶 + N/A sentinel 处理,给反测集补上打分纪律,否则「多条中了几条」的模糊结论会让真正致命的遗漏蒙混过关。

1. **N/A 与验证失败必须分离。** 条目判 INCONCLUSIVE(不适用)的唯一条件:能显式给出 sentinel——如该技能已 Deprecated/Removed(红线本体不再存在)、或条目针对的能力被我方显式声明不承接(example:capability-map 豁免)。除此之外一律不能「跳过/默认通过」;凡是「没法确认命中」(Agent 无响应、输出为空、断言无法定位)都判 FAIL(fail-closed),不能拿「不好说」当通过。区分记法:`N/A(记录 sentinel)` 可以背书,`unverifiable` 只能判死。
2. **横切技能的反测条目是强制门禁(mandatory)。** `evolution-gate` / `pattern-composition` 这两条类型(以及任何影响其他技能验证方式的条目)不得靠其余条目加权通过来抵偿——该条目必须唯一命中其全部断言、未触任一 forbidden,否则整体升级判定失败、分数封顶(参考 iFixAi:B01=1.0,任一 mandatory 不过 cap 0.60)。理由:工具本身校准错了,用这个工具量出来的其他一切绿色都不可信。
3. **分数封顶而非平均对消。** 反测结论只输出 `PASS(全命中+无 forbidden)` 或 `FAIL(任一断言漏 / 任一 forbidden触 / fail-closed)` 二值;不输出「6/8 通过,基本可以」——留有失败项就不是升级验收标准,必须回滚或修复。

落地形态:这三条直接替换旧版「检查所有 assertions 命中 + forbidden 未触」一句话——它没有说死 fail-closed 与 N/A 分离、也没有给横切条目强制权重。新增条目时按同根合并不变。

### 变更后自动验证强制 hook(2026-09-07)

**不是"改完记得跑",是"改完必跑,缺一项不结项"。** 把上面所有"铁律"固化为三条硬命令,任何 skill 的 patch/edit/升级后必须依次通过,全部 exit 0 才算完成交付——这是把验证从"自觉纪律"升级成"必然发生的 hook"。

```bash
# ① 确定性校验:路由/能力/技能库状态一致性
python3 ~/.hermes/scripts/routing_check.py        # 期望 RESULT: PASS (0 warnings)
python3 ~/.hermes/scripts/capability_probe.py     # 期望全 OK

# ② 反向引用检查:改了 X 技能,谁在用它(打散 inlined 引用)
grep -rl "<改了的技能名>" ~/.hermes/skills ~/.hermes/cron 2>/dev/null
#   结果非空 → 每个引用方都要审视:X 的触发/契约/输出变了会不会破坏它。
#   横切技能(evolution-gate/pattern-composition)反向引用非空时,跑全量反测而非 1-2 条。

# ③ 反测条目:按速查表 1:1 喂对应 prompt,核对 assertions 命中 + forbidden 未触(PASS/FAIL 二值)
```

触发时机(全部强制):skill_manage patch/edit/delete、多文件批量 patch、self-update 后。跑完把 ①的 PASS、② 引用了谁、③ 的 PASS/FAIL 写进交付说明——缺项说明不行了还没验。

前置条件:这三步只依赖 `~/.hermes/scripts/` 下既有脚本 + grep,零新依赖;`routing_check.py`/`capability_probe.py` 不存在则先按全网 ② 手动核对并记录"脚本未装"而非跳过。

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
| memory-os-pattern | memory-os-write-discipline / memory-recall-write-policy / memory-recall-evidence-gate / memory-recall-three-layer-retrieval / memory-recall-rrf-formula / memory-recall-daily-review |
| budget-guardrail | budget-guardrail-threshold |
| human-escalation | human-escalation-trigger |
| multi-agent-isolation | multi-agent-isolation-lock |
| observability-trace | observability-trace-decision |
| data-retention-privacy | data-retention-cleanup |
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
