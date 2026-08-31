#!/usr/bin/env python3
"""Error Compact: 把原始错误压缩为结构化摘要(参考 error-compact-pattern)."""
import re, sys

def compact_error(step: str, raw: str, max_lines: int = 25) -> dict:
    lines = raw.splitlines()
    head = lines[:max_lines]
    # 常见错误分类桶(按需扩展)
    buckets = {
        "timeout": ["timeout", "timed out", "deadline"],
        "ratelimit": ["429", "rate limit", "too many requests"],
        "auth": ["401", "403", "unauthorized", "permission"],
        "network": ["connection", "refused", "resolve", "ssl"],
        "parse": ["json", "parse", "decode", "schema"],
    }
    cls = "unknown"
    for name, keys in buckets.items():
        if any(k in raw.lower() for k in keys):
            cls = name
            break
    return {
        "step": step,
        "error_class": cls,
        "summary": re.sub(r"\s+", " ", " ".join(head))[:300],
        "recoverable": cls in ("timeout", "ratelimit", "network"),
        "impact": "该步骤失败;可能影响后续流程",
    }

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    print(compact_error(step, sys.stdin.read()))
