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
