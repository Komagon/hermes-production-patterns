---
name: multi-agent-isolation
description: "多 Agent 协作隔离 — 命名空间/文件锁/令牌桶防止资源竞争"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, multi-agent, isolation, concurrency]
    category: conventions
    related_skills: [state-file-pattern, cron-job-pattern, maker-checker]
hpp_category: reliability
hpp_en: "Namespace isolation and resource locks for parallel agents."
hpp_maturity: L1
hpp_complexity: high
hpp_reliability: medium
hpp_capability: delegate
maturity: experimental
hpp_when_to_use: ["多个 Agent 并行写同一目录", "共享 API 限流额度", "Cron 任务同时触发"]
hpp_when_not_to_use: ["单 Agent 顺序执行", "无共享资源的独立任务"]
---

# 多 Agent 协作隔离

> **对应 12-Factor Agents Factor 3: Own your own state**  
> **适用场景: 多 Agent 并行运行时的资源竞争防护**

## 核心原则

并行 Agent 的第一风险不是逻辑错误，而是**静默数据损坏** —— 两个 Agent 同时写一个文件，最后谁覆盖了谁，日志里看不出来。

## 资源竞争场景

### 1. 文件写入竞争

多个 Cron 任务或 Agent 同时写 `reports/`、`STATE.md` 或共享配置文件:

```text
Agent-A  ──write──>  reports/weekly.md  ──┐
                                          ├── 文件内容不确定（取决于谁最后写）
Agent-B  ──write──>  reports/weekly.md  ──┘
```

**症状**: 报告内容混杂、STATE.md 字段被回退、JSON 格式损坏。

### 2. API 限流竞争

多个 Agent 共享同一个 API Key，各自独立计数，集体触发 rate limit:

```text
Agent-A  ──10 req/s──┐
Agent-B  ──10 req/s──┼──>  API (limit: 15 req/s)  ──>  429
Agent-C  ──10 req/s──┘
```

**症状**: 批量 429 错误、指数退避导致任务超时、部分请求静默丢失。

### 3. 共享数据库/缓存竞争

多个 Agent 同时读-改-写同一个 Redis key 或 JSON 文件:

```text
Agent-A  read(amount=100)  ──>  write(amount=90)
Agent-B  read(amount=100)  ──>  write(amount=80)   # A 的修改被覆盖
```

**症状**: 经典 read-modify-write race condition。

## 隔离策略

### 策略一: 命名空间隔离

每个 Agent 拥有独立的工作目录，彻底消除写入冲突:

```text
shared-data/
├── agent-market-watcher/
│   ├── STATE.md          # 独立状态
│   └── reports/
│       └── weekly.md
├── agent-price-tracker/
│   ├── STATE.md
│   └── reports/
│       └── weekly.md
└── agent-news-curator/
    ├── STATE.md
    └── reports/
        └── weekly.md
```

**规则**: Agent 名称即目录名，`mkdir -p` 即授权，无需显式锁定。

### 策略二: 文件锁 (Lock File Pattern)

当必须写入共享资源时，用 `.lock` 文件做互斥:

```python
import fcntl
import time
import json
from pathlib import Path

class FileLock:
    """基于 fcntl 的文件锁，支持超时。"""

    def __init__(self, path: str, timeout: float = 30.0):
        self.lock_path = Path(f"{path}.lock")
        self.timeout = timeout

    def __enter__(self):
        start = time.monotonic()
        while True:
            try:
                self.fd = open(self.lock_path, "w")
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.fd.write(json.dumps({
                    "pid": __import__("os").getpid(),
                    "acquired": time.time()
                }))
                self.fd.flush()
                return self
            except (IOError, OSError):
                if time.monotonic() - start > self.timeout:
                    raise TimeoutError(
                        f"Lock timeout after {self.timeout}s: {self.lock_path}"
                    )
                time.sleep(0.1)

    def __exit__(self, *exc):
        try:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
            self.fd.close()
            self.lock_path.unlink(missing_ok=True)
        except Exception:
            pass

# 使用示例
with FileLock("/shared-data/reports/weekly.md"):
    data = Path("/shared-data/reports/weekly.md").read_text()
    # ... 修改 data ...
    Path("/shared-data/reports/weekly.md").write_text(data)
```

**超时原则**: 默认 30 秒，超时即报错而非无限等待 —— 避免死锁静默卡死。

### 策略三: 令牌桶限流 (Token Bucket)

共享 API 限流池，各 Agent 公平分配额度:

```python
import time
import threading

class TokenBucket:
    """共享令牌桶，多 Agent 公平限流。"""

    def __init__(self, rate: float, capacity: int):
        """
        rate: 每秒补充的令牌数
        capacity: 令牌桶最大容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self, tokens: int = 1, timeout: float = 30.0) -> bool:
        """尝试获取 tokens 个令牌，返回是否成功。"""
        deadline = time.monotonic() + timeout
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(
                    self.capacity, self.tokens + elapsed * self.rate
                )
                self.last_refill = now
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
            if time.monotonic() > deadline:
                return False
            time.sleep(0.05)

# 使用示例: 3 个 Agent 共享 15 req/s 配额
shared_bucket = TokenBucket(rate=15, capacity=30)

def agent_task(agent_name: str):
    for url in urls:
        if shared_bucket.acquire(timeout=10):
            response = call_api(url)
        else:
            raise RuntimeError(f"{agent_name}: rate limit exhausted")
```

## 目录结构示例

多 Agent 并行报告的推荐目录布局:

```text
hermes-production-patterns/
├── conventions/
│   ├── state-file-pattern.md      # 每个 Agent 自己的 STATE.md
│   ├── cron-job-pattern.md        # Cron 任务尊重共享限流
│   └── multi-agent-isolation.md   # 本文件
├── shared-data/
│   ├── rate-limit.json            # 共享限流配置
│   └── global-locks/              # 集中锁文件目录
│       └── .gitkeep
├── agents/
│   ├── market-watcher/
│   │   ├── STATE.md               # 独立状态文件
│   │   └── reports/
│   │       ├── 2026-W36.md
│   │       └── 2026-W37.md
│   ├── price-tracker/
│   │   ├── STATE.md
│   │   └── reports/
│   │       └── 2026-W37.md
│   └── news-curator/
│       ├── STATE.md
│       └── reports/
│           └── 2026-W37.md
└── merged/                        # 合并后的最终产出（只读）
    └── weekly/
        └── 2026-W37.md
```

## 与其他模式的集成

| 模式 | 集成点 |
|------|--------|
| **state-file-pattern** | 每个 Agent 在自己的命名空间下维护独立的 `STATE.md`，不共享 |
| **cron-job-pattern** | Cron 任务启动时获取令牌桶配额，失败则推迟到下一个窗口 |
| **maker-checker** | Maker 和 Checker 使用相同命名空间，Checker 通过锁文件读取 Maker 的产出 |
| **checkpoint-pattern** | Checkpoint 写入 Agent 自己的目录，恢复时只扫描自身命名空间 |

## 反模式

| 反模式 | 正确做法 |
|--------|----------|
| 所有 Agent 共享一个 `reports/` 目录 | 每个 Agent 一个子目录 |
| 各自独立计数 API 调用次数 | 共享 TokenBucket，集中限流 |
| 锁文件用 `sleep()` 轮询（无超时） | 设定超时，超时报错 |
| 锁文件不清理，残留 `.lock` | `__exit__` 中 `unlink`，异常也不留残渣 |
| 合并步骤和生产步骤用同一 Agent | 生产写自身目录，合并用独立 Agent 只读扫描 |

## 度量

- **锁等待时间** (p50/p99): 超过 5s 说明竞争严重，应扩大命名空间
- **令牌桶拒绝率**: 超过 10% 说明总配额不足或 Agent 数需要限流
- **文件损坏率**: 检查 JSON/YAML parse error 是否下降
