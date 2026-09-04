---
name: data-retention-privacy
description: "数据保留与隐私 — STATE.md/日志中的敏感信息清单、保留期限、自动清理"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, privacy, data-retention, gdpr, pii]
    category: conventions
    related_skills: [secret-management, state-file-pattern, error-compact-pattern]
hpp_category: security
hpp_en: "PII redaction, retention periods, and auto-cleanup for agent state."
hpp_maturity: L1
hpp_complexity: medium
hpp_reliability: high
hpp_capability: memory
maturity: experimental
hpp_when_to_use: ["Agent 长期运行积累日志/STATE.md", "涉及用户数据的 pipeline", "合规审计要求的场景"]
hpp_when_not_to_use: ["纯离线一次性 demo", "无敏感数据的公开信息聚合"]
---

# 数据保留与隐私

> **对应 12-Factor Agents 的隐含原则：State is a liability, not an asset.**
> **与 secret-management.md 互补：secret-management 管密钥存放，本篇管数据生命周期。**

## 核心原则

**数据只在需要时保留，超过期限自动清理，写入前先脱敏。**

## 问题

STATE.md、运行日志、错误日志在长期运行中会不知不觉积累敏感信息：

- 用户原始输入中的 PII（邮箱、手机号、身份证号）
- 密钥碎片（调试时不小心写入的 API key 片段）
- 完整 API 响应体（含 token、用户 ID、内部 URL）
- 文件路径泄露（暴露用户名、目录结构）

这些数据一旦进入 Git 历史或共享日志，就很难彻底清除。

## 不该出现的内容清单

| 类别 | 示例 | 风险等级 |
|:-----|:-----|:--------:|
| PII — 邮箱 | `user@example.com` | 🔴 高 |
| PII — 手机号 | `13812345678`, `+1-555-0123` | 🔴 高 |
| PII — 身份证号 | `110101199001011234` | 🔴 高 |
| PII — 姓名+地址组合 | `张三，北京市朝阳区...` | 🟡 中 |
| 密钥碎片 | `sk-proj-abc...xyz` | 🔴 高 |
| 完整 API 响应体 | 含 `access_token`, `refresh_token` 的 JSON | 🔴 高 |
| 内部 URL | `https://internal.corp.local/api/...` | 🟡 中 |
| 文件路径（含用户名） | `/home/john/.hermes/.env` | 🟢 低 |

## 保留期限建议

| 数据类型 | 保留期限 | 清理方式 |
|:---------|:---------|:---------|
| 运行日志（`logs/`） | 30 天 | 按文件修改时间删除 |
| STATE.md 历史版本 | 90 天 | 只保留最近 N 个版本 |
| 错误日志（`error_logs/`） | 7 天 | 按文件修改时间删除 |
| 临时文件（`/tmp/hermes-*`） | 1 天 | cron 定时清理 |
| Git 中的敏感提交 | 0（立即清除） | `git filter-branch` 或 BFG |

> **原则：宁短勿长。** 不确定时选更短的保留期。

## 自动清理脚本模式

```python
#!/usr/bin/env python3
"""data_retention_cleanup.py — 按保留期限清理过期数据"""

import os
import time
import re
import glob
from pathlib import Path
from datetime import datetime, timedelta

# 保留期限配置（天）
RETENTION = {
    "logs": 30,
    "state_history": 90,
    "error_logs": 7,
    "tmp": 1,
}

def cleanup_by_age(directory: str, max_days: int, dry_run: bool = True) -> int:
    """删除超过 max_days 天的文件，返回删除数量"""
    if not os.path.isdir(directory):
        return 0
    cutoff = time.time() - (max_days * 86400)
    removed = 0
    for f in Path(directory).rglob("*"):
        if f.is_file() and f.stat().st_mtime < cutoff:
            if dry_run:
                print(f"[DRY] would remove: {f}")
            else:
                f.unlink()
                print(f"removed: {f}")
            removed += 1
    return removed

def scan_for_pii(filepath: str) -> list[dict]:
    """扫描文件中的 PII，返回匹配列表"""
    patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone_cn": r"(?<!\d)1[3-9]\d{9}(?!\d)",
        "phone_intl": r"\+\d{1,3}[-.\s]?\d{4,14}",
        "id_card_cn": r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)",
        "api_key_generic": r"(?:sk|key|token|secret)[_-][a-zA-Z0-9]{20,}",
        "bearer_token": r"Bearer\s+[a-zA-Z0-9._-]{20,}",
    }
    findings = []
    try:
        text = Path(filepath).read_text(errors="ignore")
    except Exception:
        return findings
    for ptype, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            findings.append({
                "type": ptype,
                "line_preview": match.group()[:8] + "***",
                "position": match.start(),
            })
    return findings

# 敏感信息正则模式列表（导出供其他脚本使用）
SENSITIVE_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone_cn": r"(?<!\d)1[3-9]\d{9}(?!\d)",
    "phone_intl": r"\+\d{1,3}[-.\s]?\d{4,14}",
    "id_card_cn": r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)",
    "api_key_generic": r"(?:sk|key|token|secret)[_-][a-zA-Z0-9]{20,}",
    "bearer_token": r"Bearer\s+[a-zA-Z0-9._-]{20,}",
    "ipv4_private": r"(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}",
    "jwt": r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}",
}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hermes data retention cleanup")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true", help="Actually delete files")
    parser.add_argument("--scan-pii", type=str, help="Scan a file/directory for PII")
    args = parser.parse_args()

    dry_run = not args.execute

    if args.scan_pii:
        target = Path(args.scan_pii)
        files = [target] if target.is_file() else target.rglob("*")
        for f in files:
            if f.is_file():
                findings = scan_for_pii(str(f))
                if findings:
                    print(f"\n⚠️  {f}:")
                    for f2 in findings:
                        print(f"  [{f2['type']}] {f2['line_preview']}")
        return

    hermes_dir = os.path.expanduser("~/.hermes")
    cleanup_targets = {
        os.path.join(hermes_dir, "logs"): RETENTION["logs"],
        os.path.join(hermes_dir, "error_logs"): RETENTION["error_logs"],
        "/tmp": RETENTION["tmp"],  # 仅清理 hermes-* 前缀
    }

    print(f"{'[DRY RUN] ' if dry_run else ''}Starting cleanup at {datetime.now()}")
    for directory, max_days in cleanup_targets.items():
        count = cleanup_by_age(directory, max_days, dry_run=dry_run)
        print(f"  {directory}: {count} files {'would be' if dry_run else ''} removed (>{max_days}d)")

if __name__ == "__main__":
    main()
```

### 定时运行

```bash
# crontab -e
# 每天凌晨 3 点清理过期数据
0 3 * * * ~/.hermes/scripts/data_retention_cleanup.py --execute >> ~/.hermes/logs/cleanup.log 2>&1
```

## 正则模式列表（敏感信息检测）

以下是可直接用于 `grep`、`ripgrep` 或 Python `re` 的模式：

| 名称 | 正则 | 说明 |
|:-----|:-----|:-----|
| 邮箱 | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | 通用邮箱格式 |
| 中国手机号 | `(?<!\d)1[3-9]\d{9}(?!\d)` | 11 位，1 开头 |
| 国际手机号 | `\+\d{1,3}[-.\s]?\d{4,14}` | 含国家码 |
| 中国身份证号 | `(?<!\d)[1-9]\d{5}(?:19\|20)\d{2}(?:0[1-9]\|1[0-2])(?:0[1-9]\|[12]\d\|3[01])\d{3}[\dXx](?!\d)` | 18 位 |
| API Key | `(?:sk\|key\|token\|secret)[_-][a-zA-Z0-9]{20,}` | 常见 key 前缀 |
| Bearer Token | `Bearer\s+[a-zA-Z0-9._-]{20,}` | HTTP Authorization |
| JWT | `eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}` | 三段式 JWT |
| 内网 IP | `(?:10\|172\.(?:1[6-9]\|2\d\|3[01])\|192\.168)\.\d{1,3}\.\d{1,3}` | RFC1918 地址 |

### 快速扫描命令

```bash
# 扫描 STATE.md 中的敏感信息
grep -Pn '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' reports/*/STATE.md

# 扫描日志中的 API key
grep -Prn '(?:sk|key|token|secret)[_-][a-zA-Z0-9]{20,}' ~/.hermes/logs/

# 使用 Python 脚本批量扫描
python data_retention_cleanup.py --scan-pii ~/.hermes/
```

## 脱敏写入策略

在写入 STATE.md 或日志前，对敏感字段做替换：

```python
import re

def redact(text: str) -> str:
    """写入前脱敏：替换敏感信息为占位符"""
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]", text)
    text = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "[REDACTED_PHONE]", text)
    text = re.sub(r"(?:sk|key|token|secret)[_-][a-zA-Z0-9]{20,}", "[REDACTED_KEY]", text)
    text = re.sub(r"Bearer\s+[a-zA-Z0-9._-]{20,}", "Bearer [REDACTED]", text)
    return text

# 写入 STATE.md 时使用
state_content = redact(raw_content)
Path("STATE.md").write_text(state_content)
```

## 和 secret-management.md 的分工

| 维度 | secret-management | data-retention-privacy（本篇） |
|:-----|:------------------|:-------------------------------|
| 管什么 | 密钥（API Key、Token、密码） | 数据（PII、日志、状态文件） |
| 核心问题 | 放在哪？怎么轮换？ | 保留多久？何时清理？怎么脱敏？ |
| 生命周期 | 创建 → 存储 → 轮换 → 销毁 | 生成 → 脱敏 → 保留 → 过期清理 |
| 关注点 | 不进 Git、不进上下文 | 不超期、不裸写、可审计 |

**简单记：secret-management 管「钥匙不丢」，data-retention-privacy 管「垃圾及时倒」。**

## 检查清单

- [ ] STATE.md 写入前经过 `redact()` 脱敏
- [ ] 日志不包含完整 API 响应体（只记 status code 和 request ID）
- [ ] 错误日志 7 天自动清理
- [ ] 运行日志 30 天自动清理
- [ ] 定期扫描 `~/.hermes/` 目录确认无 PII 残留
- [ ] Git 历史中无密钥或 PII（用 `git log -p | grep` 检查）
