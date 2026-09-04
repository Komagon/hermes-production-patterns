# hpp doctor 推荐报告

## 你的配置

- 你的 Agent 主要做什么？ **综合/多种任务**
- Agent 的自主程度？ **半自主（关键决策人工确认）**
- 任务涉及的风险等级？ **中（有副作用但可回滚）**
- 是否需要多个 Agent 协作？ **单 Agent**
- 任务状态复杂度？ **中等（需要跟踪进度和历史）**

---

## 🔴 必装模式（3 个）

- **state-file-pattern** — 任何跨会话任务都需要 STATE.md 管理状态
  → `conventions/state-file-pattern.md`
- **error-compact-pattern** — 错误压缩是生产环境基础能力
  → `conventions/error-compact-pattern.md`
- **maker-checker** — 有风险或全自主任务需要独立验证
  → `conventions/maker-checker.md`

## 🟡 推荐模式（3 个）

- **secret-management** — 有风险任务需要规范密钥管理
  → `conventions/secret-management.md`
- **control-flow-separation** — 复杂任务需要区分确定性代码和 LLM 决策
  → `conventions/control-flow-separation.md`
- **skill-evolution** — 半自主/全自主需要技能版本化管理
  → `conventions/skill-evolution.md`

## 🟢 可选模式（1 个）

- **data-retention-privacy** — 有风险任务需要数据保留和隐私规范
  → `conventions/data-retention-privacy.md`

## 📖 参考文档（2 个）

- **anti-patterns** — 反面模式参考，避免常见错误
  → `conventions/anti-patterns.md`
- **pattern-composition** — 模式组合决策树，帮你选择和组合模式
  → `conventions/pattern-composition.md`

---

**总计**: 7 个推荐模式（必装 3 + 推荐 3 + 可选 1）

## 安装命令

```bash
# 安装必装+推荐模式（共 6 个）
git clone https://github.com/Komagon/hermes-production-patterns.git
cd hermes-production-patterns
cp conventions/state-file-pattern.md ~/.hermes/skills/hermes-production-patterns/
cp conventions/error-compact-pattern.md ~/.hermes/skills/hermes-production-patterns/
cp conventions/maker-checker.md ~/.hermes/skills/hermes-production-patterns/
cp conventions/secret-management.md ~/.hermes/skills/hermes-production-patterns/
cp conventions/control-flow-separation.md ~/.hermes/skills/hermes-production-patterns/
cp conventions/skill-evolution.md ~/.hermes/skills/hermes-production-patterns/
```
