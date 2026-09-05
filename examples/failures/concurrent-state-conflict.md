# 失败案例: 并发写入 STATE.md — 两个 Agent 互相覆盖

## 场景描述

团队部署了两个并行的 Hermes Agent：

- **Agent-A**: 每小时运行，负责代码仓库巡检（检查 CI 状态、依赖更新）
- **Agent-B**: 每 2 小时运行，负责文档同步（更新 README、CHANGELOG）

两个 agent 共享同一个 `.hermes/STATE.md` 文件，用于记录各自的工作进度和上下文。

周五下午 14:00，两个 agent 几乎同时触发：

```
14:00:01  Agent-A 读取 STATE.md（获取上次巡检时间）
14:00:02  Agent-B 读取 STATE.md（获取文档版本号）
14:00:15  Agent-A 完成巡检，写入 STATE.md（更新 last_inspection 字段）
14:00:18  Agent-B 完成文档同步，写入 STATE.md（更新 docs_version 字段）
```

**问题**：Agent-B 的写入覆盖了 Agent-A 的更新。Agent-B 读取时 STATE.md 包含
`last_inspection: 2026-08-15T13:00:00`，写入时把它覆盖回了旧值。

更糟糕的是，Agent-A 下次运行时读到的是被覆盖的 STATE.md，认为自己从未执行过
14:00 的巡检，于是**重复执行了所有检查**，产生了重复的 PR 评论和 issue 标签。

这个 cycle 持续了整个周末，产生了：
- **47 条重复 PR 评论**
- **12 个重复 issue 标签**
- **3 个相互矛盾的文档版本**

## 根因分析

1. **无文件锁**: STATE.md 的读写没有原子性保证
2. **无 Path Leasing**: 两个 agent 不知道对方正在写同一个文件
3. **全量覆盖**: 写入时覆盖整个文件，而不是 merge 字段级变更
4. **无 Version 检测**: 写入前没有检查文件是否已被修改

## 事故日志（脱敏）

```
[2026-08-18 14:00:01] agent-a:read STATE.md size=1247 mtime=2026-08-18T13:00:00
[2026-08-18 14:00:02] agent-b:read STATE.md size=1247 mtime=2026-08-18T13:00:00
[2026-08-18 14:00:15] agent-a:write STATE.md fields=[last_inspection, ci_status]
[2026-08-18 14:00:15] agent-a:write success, mtime=2026-08-18T14:00:15
[2026-08-18 14:00:18] agent-b:write STATE.md fields=[docs_version, changelog_hash]
[2026-08-18 14:00:18] agent-b:write success, mtime=2026-08-18T14:00:18
                      ↑ 没有检测到 14:00:15 的变更，直接覆盖

# Agent-A 下次运行
[2026-08-18 15:00:01] agent-a:read STATE.md
[2026-08-18 15:00:01] agent-a:last_inspection=2026-08-18T13:00:00  ← 被覆盖回旧值!
[2026-08-18 15:00:01] agent-a:resuming from checkpoint, re-running inspection
[2026-08-18 15:00:12] agent-a:created PR comment on #127  ← 重复!
[2026-08-18 15:00:13] agent-a:created PR comment on #134  ← 重复!
```

## 解决方案

### 1. 启用 Path Leasing（文件租约）

```yaml
# ~/.hermes/config.yaml
path_leasing:
  enabled: true
  lease_dir: .hermes/leases/
  default_ttl: 300           # 租约有效期 5 分钟
  conflict_strategy: wait    # 遇到冲突时等待而不是覆盖
```

Agent 启动时：
```
agent-a: lease acquired for .hermes/STATE.md (ttl=300s)
agent-b: lease conflict for .hermes/STATE.md, waiting...
agent-a: lease released
agent-b: lease acquired for .hermes/STATE.md
```

### 2. 字段级 Merge 而非全量覆盖

```python
# 不要这样：
write_file("STATE.md", new_content)

# 而是这样：
def merge_state(file_path: str, updates: dict):
    current = read_yaml(file_path)
    # 检查 mtime 是否变化
    if current["_mtime"] != get_mtime(file_path):
        raise StaleWriteError("STATE.md changed since last read")
    current.update(updates)
    current["_mtime"] = now()
    write_yaml(file_path, current)
```

### 3. 加入乐观锁（mtime 检测）

```python
def safe_write_state(file_path: str, expected_mtime: float, new_content: str):
    current_mtime = os.path.getmtime(file_path)
    if current_mtime != expected_mtime:
        raise ConcurrentModificationError(
            f"STATE.md modified since read "
            f"(expected={expected_mtime}, actual={current_mtime})"
        )
    write_file(file_path, new_content)
```

### 4. 分离各 Agent 的状态文件

```yaml
# 每个 agent 使用独立的状态文件
agent_a:
  state_file: .hermes/state/agent-a.yml

agent_b:
  state_file: .hermes/state/agent-b.yml

# 共享状态通过专门的 merge 脚本
shared_state:
  source: .hermes/state/*.yml
  merged: .hermes/STATE.md
  merge_strategy: field_union    # 合并不同字段，冲突字段取最新
```

## 关联模式

- [state-file-pattern](../../conventions/state-file-pattern.md) — STATE.md 的正确读写方式
- [multi-agent-isolation](../../conventions/multi-agent-isolation.md) — 多 agent 命名空间隔离与文件锁机制
- [checkpoint-pattern](../../conventions/checkpoint-pattern.md) — checkpoint 的一致性保证
- [anti-patterns](../../conventions/anti-patterns.md) — "盲目覆盖"反模式
