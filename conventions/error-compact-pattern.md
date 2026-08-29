---
name: error-compact-pattern
description: "错误压缩模式 — 将原始错误压缩为结构化摘要，防止 Agent 失焦"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, error, resilience]
    category: conventions
    related_skills: [state-file-pattern, control-flow-separation]
---

# 错误压缩模式

> **对应 12-Factor Agents Factor 9: Compact Errors into Context Window**

## 核心原则

原始错误信息又长又噪，直接塞进上下文会让 Agent 失焦。**压缩它。**

## 对比

❌ **原始错误（炸锅式）：**
```
Error: ModuleNotFoundError: No module named 'requests'
Traceback (most recent call last):
  File "/usr/lib/python3.11/runpy.py", line 196, in _run_module_as_main
    ...
ModuleNotFoundError: No module named 'requests'
```

✅ **压缩后（可消化式）：**
```
[STEP_FAILED] fetch_data@2026-06-29T10:00:00
  Error: ModuleNotFoundError - 'requests' 包未安装
  Hint: pip install requests
  Recoverable: YES
```

## 压缩模板

```
[STEP_FAILED] {tool_name}@{timestamp}
  Error: {error_type} - {brief_message}
  Hint: {recovery_hint}
  Recoverable: YES | NO | MAYBE
  Impact: {影响范围描述}
```

## 错误分类桶

| 桶 | 示例 | 动作 |
|:---|:---|:---|
| 🔁 **可重试** | Timeout, RateLimit, 503 | 指数退避重试，最多3次 |
| 🔐 **认证** | 401, 403, 密钥过期 | 记录错误，上报人类，不重试 |
| 📐 **结构** | 期望 JSON 返回了 HTML | 跳过该项，其余继续 |
| 💥 **致命** | 磁盘满，OOM，配置损坏 | 硬停止，降级到 L1，通知人类 |

## Agent Loop 集成

```python
try:
    result = await execute_step(next_step)
    context.append(result)
except Exception as e:
    compact = compact_error(next_step["tool"], e)
    context.append(compact)
    if compact["recoverable"] == "YES" and retry_count < 3:
        continue  # 重试
    elif compact["recoverable"] == "NO":
        context.append("[HALT] 不可恢复错误，停止循环")
        break
    else:  # MAYBE
        context.append(f"[RETRY {retry_count+1}/3] {compact}")
        continue
```

## 自愈机制（Self-Healing）

压缩错误后，Agent 不只是跳过它——还应该尝试**自愈**：

### 四步自愈循环

```
[STEP_FAILED] → 压缩 → 分类 → 自愈尝试 → 成功？→ 继续
                                         ↓ 失败
                                    记录到 STATE.md Lessons Learned
                                         ↓
                                    下次运行跳过该步骤
```

| 错误桶 | 自愈动作 | 成功判断 |
|:---|:---|:---|
| 🔁 可重试 | 指数退避重试（1s → 3s → 9s） | 后续步骤正常执行 |
| 🔐 认证 | 读取备用密钥池 / 上报人类 | 新 token 验证通过 |
| 📐 结构 | 改变解析策略（如 HTML→BeautifulSoup） | 解析成功 |
| 💥 致命 | 立即停止，写 STATE.md 状态为 failed | 人工介入 |

### 失败记录到 STATE.md

```markdown
## Lessons Learned
- 2026-07-15: fetch_feeds 频繁 Timeout，增加 retry_wait_base=3，下次跳过该源
```

### 自愈代码模板

```python
async def heal(compact: dict, state: dict) -> HealingResult:
    """尝试自愈，返回是否成功及措施描述"""
    bucket = classify_bucket(compact["error_type"])

    if bucket == "retryable":
        for attempt in backoff_sequence([1, 3, 9]):
            result = await retry_step()
            if result.success:
                return HealingResult(success=True, action=f"重试 {attempt}s 后成功")
        return HealingResult(success=False, action="重试 3 次均失败")

    elif bucket == "auth":
        if rotate_credentials(state):
            return HealingResult(success=True, action="切换备用密钥")
        return HealingResult(success=False, action="密钥池耗尽，需人工")

    elif bucket == "structural":
        alt_result = await parse_with_fallback()
        if alt_result:
            return HealingResult(success=True, action="切换解析策略")
        return HealingResult(success=False, action="所有解析策略均失败")

    else:  # fatal
        return HealingResult(success=False, action="致命错误，需人工介入")
```
