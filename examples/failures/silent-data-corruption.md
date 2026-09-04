# 失败案例: 静默数据损坏 — 连续 3 天产出错误报告

## 场景描述

团队使用 Hermes Agent 每日生成 A 股市场复盘报告，流程如下：

1. Cron job 每天 18:00 触发
2. Agent 调用 stock-data MCP 获取当日行情
3. Agent 读取前一天的 STATE.md 获取上下文（持仓、关注列表）
4. Agent 生成复盘报告，写入 Obsidian vault

周一，stock-data MCP 的一个端点升级了 API 版本，返回格式从 `{data: {prices: [...]}}`
变成了 `{result: {market_data: [...]}}`。Agent 没有 schema 校验，继续用旧路径解析。

**结果**：Agent 拿到 `undefined`，但没有报错，而是基于 LLM 的"合理猜测"生成了报告。
报告看起来格式正确、语言流畅，但数据完全是 LLM 编造的。

- 周一的报告：编造了涨跌幅（"沪指上涨 1.2%"实际下跌 0.3%）
- 周二的报告：基于周一的编造数据继续推演，偏差更大
- 周三的报告：与实际行情已经完全脱节

直到周四用户手动对比了同花顺数据才发现问题。**3 天的报告全部作废**。

## 根因分析

1. **无 Schema 校验**: API 返回数据没有做结构化校验，`undefined` 被静默处理
2. **无 Checkpoint**: 每一步的中间结果没有保存，无法回溯是哪一步出错
3. **Maker 无 Checker**: 生成报告后没有独立的验证步骤
4. **无 Data Lineage**: 报告中没有标注数据来源和时间戳，无法追溯

## 事故日志（脱敏）

```
[2026-08-18 18:00:01] cron:job started, job=daily-market-recap
[2026-08-18 18:00:03] mcp:stock-data call=get_a_share_prices_snapshot
[2026-08-18 18:00:04] mcp:stock-data response status=200 size=12847
[2026-08-18 18:00:04] agent: parsing response path=data.prices  ← 旧路径
[2026-08-18 18:00:04] agent: result=undefined  ← 未捕获!
[2026-08-18 18:00:05] agent: reading STATE.md
[2026-08-18 18:00:05] agent: context loaded, yesterday_close=3245.67  ← 来自 STATE.md
[2026-08-18 18:00:06] llm:call generating report with context
[2026-08-18 18:00:12] llm:response generated, 2847 chars
[2026-08-18 18:00:13] obsidian:file written path=daily/2026-08-18-复盘.md
[2026-08-18 18:00:13] cron:job completed successfully  ← 标记成功!

# 周二继续错误链
[2026-08-19 18:00:01] cron:job started, job=daily-market-recap
[2026-08-19 18:00:05] agent: reading STATE.md  ← 周一写入的错误数据
[2026-08-19 18:00:05] agent: context loaded, yesterday_close=3289.45  ← 周一编造的值
[2026-08-19 18:00:06] llm:call generating report  ← 基于错误上下文继续推演
```

## 解决方案

### 1. 加入 Schema 校验（拦截无效数据）

```python
# 在数据获取后立即校验
from pydantic import BaseModel

class MarketData(BaseModel):
    prices: list[PriceEntry]
    timestamp: datetime

def validate_response(raw: dict) -> MarketData:
    try:
        return MarketData.parse_obj(raw.get("data") or raw.get("result", {}))
    except ValidationError as e:
        raise DataSchemaError(f"API response schema mismatch: {e}")
        # 不要静默降级，直接报错
```

### 2. 启用 Checkpoint（中间结果可回溯）

```yaml
# ~/.hermes/config.yaml
checkpoint:
  enabled: true
  save_intermediate: true    # 保存每一步的输入输出
  format: json
  path: .hermes/checkpoints/{task_id}/{step}.json
```

### 3. 加入 Checker 步骤（Maker-Checker 分离）

```yaml
# 工作流定义
workflow:
  - name: generate_report
    role: maker
    output: report_draft.md

  - name: verify_report
    role: checker
    input: report_draft.md
    checks:
      - type: data_freshness       # 数据不能超过 1 小时
      - type: cross_reference      # 与至少一个外部源对比
      - type: schema_validation    # 报告结构符合模板
    on_failure: reject_and_alert
```

### 4. Data Lineage 标注

```markdown
<!-- 每份报告底部自动追加 -->
---
**数据溯源**
- 数据源: stock-data MCP v2.3.1
- 获取时间: 2026-08-18T18:00:03+08:00
- 数据路径: result.market_data.prices
- 校验状态: ✅ schema_valid, ✅ cross_referenced
- Checkpoint: .hermes/checkpoints/daily-recap-20260818/
```

## 关联模式

- [maker-checker](../../conventions/maker-checker.md) — 生成与验证分离
- [checkpoint-pattern](../../conventions/checkpoint-pattern.md) — 中间结果保存与回溯
- [error-compact-pattern](../../conventions/error-compact-pattern.md) — 结构化错误处理
- [data-driven-optimization](../../conventions/data-driven-optimization.md) — 数据驱动的质量门
- [anti-patterns](../../conventions/anti-patterns.md) — "静默降级"反模式
