# 成熟度检查清单（Maturity Checklist）

> 从 L1 到 L3 的可量化验收标准。**不满足则不能升级。**

---

## L1 → L2 检查表

### 名称 (L1→L2)
`checklist-l1-to-l2`

### 条件（全部必须满足 - L1→L2）

| # | 检查项 | 验证方式 | 通过标准 |
|:---:|:---|:---|:---|
| 1 | 任务至少每周重复一次 | 日历/Schedule 记录 | ≥ 1 次/周 |
| 2 | 有自动验证机制 | 存在 Checker 或等效验证步骤 | 存在 > 0 行验证代码 |
| 3 | 有 STATE.md | 文件存在 | `reports/{job}/STATE.md` 存在 |
| 4 | STATE.md 含 idempotency_keys | 内容检查 | 字段存在 |
| 5 | L1 运行 ≥ 2 周无问题 | 运行日志 | ≥ 14 天连续运行 |
| 6 | L1 输出已由人类审查 ≥ 5 次 | 审查记录 | ≥ 5 次人工确认 |
| 7 | Token 预算已估算 | 文档记录 | `estimated_tokens_per_run` 已知 |
| 8 | 无 denylist 路径写入 | 日志审查 | 0 次 |

### 通过条件 (L1→L2)

```json
{
  "checklist": "L1→L2",
  "total_checks": 8,
  "required_pass": 8,
  "required_consecutive_days": 14,
  "max_failures_in_period": 0,
  "human_approval_required": true
}
```

---

## L2 → L3 检查表

### 名称 (L2→L3)
`checklist-l2-to-l3`

### 条件（全部必须满足 — L2→L3）

| # | 检查项 | 验证方式 | 通过标准 |
|:---:|:---|:---|:---|
| 1 | L2 运行 ≥ 4 周无问题 | 运行日志 | ≥ 28 天连续运行 |
| 2 | Checker PASS 率 ≥ 80% | 统计 | `pass_count / total ≥ 0.8` |
| 3 | 重试次数 ≤ 3 次/轮 | 统计 | 平均 retry ≤ 1.5 |
| 4 | 人类升级次数 = 0 | 日志 | 0 次 |
| 5 | 回滚策略已定义 | 文档存在 | 有回滚步骤 |
| 6 | 监控告警已配置 | 验证存在 | `fail_count` / `state_corrupt` 告警 |
| 7 | SLA 指标已定义 | 文档存在 | `max_latency` / `min_pass_rate` 已知 |
| 8 | Kill switch 已验证 | 手动测试 | `cronjob action=remove` 在 30s 内生效 |
| 9 | 错误压缩模式已启用 | 检查日志 | 错误信息按 `[STEP_FAILED]` 格式输出 |
| 10 | Max retries ≤ 3 | 配置检查 | `max_retries` 字段 ≤ 3 |

### 通过条件 (L2→L3)

```json
{
  "checklist": "L2→L3",
  "total_checks": 10,
  "required_pass": 10,
  "required_consecutive_days": 28,
  "max_failures_in_period": 2,
  "human_approval_required": true,
  "max_retries": 3,
  "min_checker_pass_rate": 0.8
}
```

---

## L3 持续运行检查表

### 名称 (L3 运行中)
`checklist-l3-running`

### 条件（每日检查）

| # | 检查项 | 通过标准 |
|:---:|:---|:---:|
| 1 | 单次运行 Token 消耗 ≤ 预算 2x | `actual ≤ budget × 2` |
| 2 | 连续失败次数 ≤ 2 | `consecutive_failures ≤ 2` |
| 3 | STATE.md 无损坏 | 可解析且 schema 完整 |
| 4 | 无 denylist 触碰 | 0 次 |
| 5 | Checker PASS 率 ≥ 70% | `pass_rate ≥ 0.7` |

### 自动降级触发

```json
{
  "auto_demote_to_l1": {
    "conditions": [
      "consecutive_failures ≥ 3",
      "state_corrupt == true",
      "denylist_hit ≥ 1",
      "checker_pass_rate < 0.5"
    ],
    "action": "cronjob action=update job_id=<id> maturity=L1",
    "notification": "发送告警给人类 + 记录到 STATE.md"
  }
}
```

---

## 可执行检查脚本

见 `scripts/check_maturity.py`，可以做为 CI 步骤或在升级前手动运行。
