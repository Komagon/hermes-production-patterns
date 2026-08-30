---
name: anti-patterns
description: "反面模式（Anti-Patterns）— 生产中常见的 Hermes Agent 错误实践及纠正方案"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, anti-pattern, pitfalls]
    category: conventions
    related_skills: [maker-checker, state-file-pattern, control-flow-separation, error-compact-pattern]
hpp_category: guide
hpp_en: "A catalogue of production anti-patterns and their fixes."
hpp_maturity: L1
hpp_complexity: low
hpp_reliability: medium
hpp_capability: docs
---

# 反面模式（Anti-Patterns）

> 每一个生产模式都有一个对应的反面模式。知道「不要做什么」和知道「做什么」同样重要。

## 目录

| # | 反面模式 | 违反的公约 | 纠正 |
|:---:|:---|:---:|:---|
| 1 | 自我验证 | maker-checker | Maker 和 Checker 用不同模型/实例 |
| 2 | 状态膨胀 | state-file-pattern | 旧 Idempotency Keys 定期清理 |
| 3 | 跳过 L1 直接上 L3 | maturity-staging | 严格执行渐进式发布协议 |
| 4 | 压缩过度 | error-compact-pattern | 保留关键堆栈上下文 |
| 5 | 手写临时 Prompt | 12-Factor Factor 2 | 始终写 SKILL.md |
| 6 | 无状态循环 | state-file-pattern | 每次运行先读 STATE.md |
| 7 | Maker/Checker 无标准 | maker-checker | 预定义五维评分维度 |
| 8 | 无限重试 | error-compact-pattern | 设硬上限，记录到 STATE.md |
| 9 | 摘要当证据 | memory-os-pattern | 精确断言必须下钻原 DAG/原文验证 |

---

## 1. 自我验证（Self-Validation）

**表现：** Maker 和 Checker 使用同一个模型、同一个上下文、同一个 Agent 实例。

**为什么有害：**
- Agent 不会推翻自己的输出——心理学上叫「证实偏差」（Confirmation Bias）
- 等于学生自己批改自己的试卷

**纠正：**
- Maker 和 Checker 必须**不同 Agent 实例**（通过 `delegate_task` 或独立进程）
- 优先使用不同模型（如 Maker 用 Sonnet，Checker 用 Haiku）
- 如果只能用同一模型：Clear 上下文后独立加载 Checker Skill

---

## 2. 状态膨胀（State Bloat）

**表现：** STATE.md 中的 `Idempotency Keys` 越积越多，从不清理，文件膨胀到无法阅读。

**为什么有害：**
- Agent 每次都要扫描几百个 key，浪费 token
- Lessons Learned 重复累积同一类问题

**纠正：**
```python
# 清理超过 30 天的旧 key
MAX_AGE_DAYS = 30
def prune_state(state: dict) -> dict:
    cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
    state["idempotency_keys"] = [
        k for k in state["idempotency_keys"]
        if parse_key_date(k) > cutoff
    ]
    return state
```

---

## 3. 跳过 L1 直接上 L3（Skip-to-Production）

**表现：** Cron 任务写好 Prompt 后直接设为自动执行，没有经过 L1（仅报告）和 L2（辅助批准）阶段。

**为什么有害：**
- 错误输出会自动发布，无人察觉
- Agent 的 5%「幻觉率」在 7x24 运行下意味着每天都有垃圾输出

**纠正：**
```
第 1-2 周: L1 — 仅写入 reports/，不推送
第 3-4 周: L2 — 草稿推送，人类批准
第 5 周+:  L3 — 自动，仅当 L1+L2 零失败
```

---

## 4. 压缩过度（Over-Compression）

**表现：** 错误压缩后丢失了关键的诊断信息（堆栈行号、变量值、HTTP 响应体）。

**为什么有害：**
- 无法定位问题根因
- Agent 自愈失败后人类也看不懂

**纠正：**
```
❌ 过度压缩：
  [STEP_FAILED] call_api@...  Error: 请求失败

✅ 适度压缩：
  [STEP_FAILED] call_api@2026-07-15T10:00:00
    Error: HTTP 500 - 上游服务返回服务器错误
    Hint: 检查 /var/log/upstream/error.log 第 42 行
    Recoverable: YES
    Impact: 此次调用失败，但不影响其他操作
```

---

## 5. 手写临时 Prompt（Ad-hoc Prompting）

**表现：** 每次在 Cron 任务 Prompt 里手写一堆上下文，而不是写成 SKILL.md。

**为什么有害：**
- 不可版本化、不可审查、不可复用
- 同一个任务跑两次可能表现不一致

**纠正：**
```bash
# ❌ 每次手写
hermes cron create "0 9 * * *" \
  --prompt "先检查磁盘，如果超过 80% 就告警..."

# ✅ 写成 SKILL.md
hermes cron create "0 9 * * *" \
  --skills state-file-pattern \
  --prompt "按 disk-monitor skill 执行磁盘检查"
```

---

## 6. 无状态循环（State-Less Loop）

**表现：** 每次运行从零开始，不知道上次跑了多少、哪些完成了、哪些失败了。

**为什么有害：**
- 重复处理已完成的条目（浪费 token 和时间）
- 失败后无恢复点，必须从头开始

**纠正：** 每条 Cron 任务必配 STATE.md，严格执行 Read → Execute → Write 循环。

---

## 7. Maker/Checker 无客观标准（Subjective Checking）

**表现：** Checker 的评分标准是「感觉还行」「看起来不错」，没有量化维度。

**为什么有害：**
- 无法审计、无法复现、无法迭代改进
- Checker 的「通过」和人类审查结果经常不一致

**纠正：** 始终使用五维评分体系（钩子/数据/AI味/适配/互动），各项 1-10 分，总分 ≥ 40/50 才 PASS。

---

## 8. 无限重试（Infinite Retry）

**表现：** Agent 遇到可恢复错误后无限重试，直到超时才失败。

**为什么有害：**
- 消耗大量 token（一次错误重试 20 次 = 浪费 ~100k tokens）
- 延迟后续步骤的执行

**纠正：**
```python
MAX_RETRIES = 3
retry_count = 0
while retry_count < MAX_RETRIES:
    try:
        return await execute()
    except RetryableError as e:
        retry_count += 1
        compact = compact_error(step_name, e)
        context.append(f"[RETRY {retry_count}/{MAX_RETRIES}] {compact}")
        await asyncio.sleep(BACKOFF[retry_count])  # 1, 3, 9 秒
raise PermanentError(f"重试 {MAX_RETRIES} 次均失败")
```

---

## 9. 摘要当证据（Summary-As-Evidence）

**表现：** Agent 把压缩后的摘要、复盘结论或反测输出当事实直接用——"摘要里写了 X"，不再下钻原 DAG / 原文 / 原始日志验证。长会话或跨压缩恢复时最危险：摘要天然丢细节，且摘要本身可能是模型单次生成的（有幻觉率）。

**为什么有害：**
- 一条被压缩的断言被当作"证据"二次引用，错误会沿摘要链扩散，比不记还糟
- 违反 memory-os-pattern 的证据校验闸门：摘要只是召回线索（Recall Cue），不是证据（Evidence）

**纠正：**
- 精确断言（路径、版本号、数据值、用户拍板）必须下钻验证：`lcm_recall` / `session_search` 取原文，或重跑命令/读原始文件
- 摘要里出现的具体事实，引用时标注"待验证"，验证后补来源
- 只有 `claim + evidence + source` 齐全才允许进入结论/记忆（对应 memory-os-pattern 的 G4 数据闸）
