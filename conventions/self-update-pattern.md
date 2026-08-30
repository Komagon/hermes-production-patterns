---
name: self-update-pattern
description: "Hermes 自更新安全流程 — 更新前备份、更新后验证、失败归因、可回滚"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, self-update, upgrade, rollback, testing]
    category: conventions
    related_skills: [state-file-pattern, error-compact-pattern, checkpoint-pattern, anti-patterns]
hpp_category: evolution
hpp_en: "Safe agent self-update: backup, verify, roll back."
hpp_maturity: L3
hpp_complexity: high
hpp_reliability: medium
hpp_capability: skills
hpp_when_to_use: ["Agents that patch their own config/skills", "Versioned infrastructure changes"]
hpp_when_not_to_use: ["Frozen production systems"]
---

# Hermes 自更新安全流程（Self-Update Pattern）

> **更新不是安装动作，是变更管理。** Agent 框架每升一次级，本地补丁、配置、技能都可能被悄悄破坏——更新后不验证，等于把生产系统交给运气。

## 问题

`hermes update` 看似一条命令，实际是一个高风险变更：

- **本地补丁丢失**：v0.20.4 起 `autostash` 可能不自动恢复——更新后本地修改还躺在 `git stash list` 里，系统已经用「没有补丁」的代码在跑
- **上游测试失败误判**：上游 3 万+ 测试跑出上百个失败，如果不建立基线，无法区分「上游本来就失败」和「我的环境坏了」
- **dev 依赖缺失**：更新后测试直接跑不起来（缺 pytest-asyncio 等 extras），掩盖真实回归
- **配置漂移**：`.env` / `config.yaml` 被更新流程覆盖或绕过

## 核心原则

1. **更新前可回滚** — Hermes 源码是 git 仓库（`~/.hermes/hermes-agent`），改可回滚，这是安全网
2. **更新后必验证** — 不跑测试的更新等于没验证
3. **失败要归因** — 上游失败 ≠ 本地回归，分不清就无法决策继续还是回滚
4. **基线是资产** — 每次更新后的失败清单就是下次更新的对照基准

## 标准流程（7 步）

### 1. 更新前快照

```bash
cd ~/.hermes/hermes-agent
git status                    # 本地是否有未提交改动？
git stash list                # 已有 stash 清单（更新前记录，更新后对比）
hermes --version              # 记录当前版本
```

预期：`git status` 干净或明确知道有哪些改动；stash 清单为空或已知。

### 2. 执行更新

```bash
hermes update
```

### 3. 更新后立即检查 stash（v0.20.4+ 必做）

```bash
git stash list                # 与更新前对比
```

**坑**：v0.20.4 起 autostash 可能不自动恢复。如果 stash 列表里有新条目，手动恢复：

```bash
git stash apply               # 恢复改动
git status                    # 处理冲突
# modify/delete 冲突（上游删了文件但本地改过）：
git rm <冲突文件>             # 确认上游删除合理后
```

**不要** 在确认 stash 恢复前继续任何工作——你可能在无补丁的代码上跑生产任务。

### 4. 补装缺失依赖

```bash
# 不装 dev extras（官方 extras 可能缺包），缺什么手动装什么：
pip install pytest-asyncio     # 示例：上游测试缺这个
```

### 5. 跑测试并对照失败基线

```bash
cd ~/.hermes/hermes-agent
pytest -q 2>&1 | tail -20     # 全量测试
```

**失败归因三分类**：

| 类别 | 判断 | 处理 |
|:---|:---|:---|
| 基线内失败 | 上次更新后就在基线清单里 | 无视，记录数量一致即可 |
| 新增上游失败 | 不在基线里，但失败原因是上游代码/测试本身 | 归入新基线，向上游报告 |
| 本地回归 | 不在基线里，且失败与本地补丁/配置相关 | 回滚或修补丁 |

> **实战基线**（2026-08）：v0.20.3→v0.20.4 更新后全量跑 30524 个测试、106 个失败，逐一归因后确认**零本地回归**，106 全部为上游既有失败——据此建立「更新后测试失败基线」，下次更新直接对照。

### 6. 决策：继续 or 回滚

```bash
# 回滚（本地回归或更新明显破坏）：
cd ~/.hermes/hermes-agent
git log --oneline -5          # 找到更新前的 commit
git checkout <上一个commit>   # 或 git revert
hermes --version              # 验证回到旧版本
```

### 7. 记录到 STATE.md

```markdown
## Update Record
- updated: 2026-08-19
- from: v0.20.3
- to: v0.20.4
- stash_restored: true
- test_total: 30524
- test_failed: 106
- baseline_delta: 0        # 新增失败数（本地回归为 0 才安全）
- local_regression: 0
- decision: keep
```

## 更新后测试失败基线（Baseline）

**基线 = 资产**，不是「反正会失败就无所谓」：

- 首次更新：全量跑测试，逐条归因，把「上游失败」清单存档（如 `~/reports/hermes-update-baseline.md`）
- 后续每次更新：`基线内失败数` 必须持平（±合理波动），`新增失败数` 必须归因清楚
- 基线随上游修复而缩小——上游修了什么，下次基线就少什么

## 反模式

| ❌ 错误做法 | 后果 |
|:---|:---|
| 更新后不看 `git stash list` | 本地补丁静默丢失，生产行为悄悄变化 |
| 更新后不跑测试 | 回归直到生产任务出错才发现 |
| 上游失败全部当成「环境问题」 | 错过真正被更新破坏的本地依赖 |
| 更新后立刻跑生产 cron | 在未验证的系统上执行真实任务 |
| 把失败基线当免责条款 | 基线只覆盖「上次确认过的失败」，新失败必须归因 |

## 落地工具

| 工具 | 用途 |
|:---|:---|
| `hermes update` | 更新本体（注意 v0.20.4+ autostash 行为变化） |
| `git stash / stash apply` | 补丁暂存与恢复 |
| `pytest -q` | 全量测试 + 失败清单 |
| `git checkout <commit>` | 回滚 |
| `STATE.md` | 更新记录与基线对照（本模式的标准写法） |

## 触发时机

- 每次 `hermes update` 或升级 Hermes 版本
- 每次升级第三方依赖（MCP server、插件）
- 更新后出现「莫名行为变化」时——先查 stash 和基线，再查业务代码
