# hpp CLI — Hermes Production Patterns 工具链

> v2.0 P2 Deliverable:让 Pattern 从文档变成命令。

```bash
# 直接运行(仓库内)
cli/hpp --help

# 或加入 PATH
ln -s "$(pwd)/cli/hpp" ~/.local/bin/hpp
hpp --help
```

## 命令

### hpp init — 初始化 Starter Kit

```bash
hpp init cron-production ~/my-cron-agent
```

从 `starter-kits/<kit>/` 复制骨架到目标目录(目标必须为空)。

### hpp add — 给现有项目加 Pattern

```bash
hpp add maker-checker ~/my-agent
```

可选 pattern:

| pattern | 内容 |
|:---|:---|
| maker-checker | maker/checker 角色 + schema + red-flags + 反测 |
| error-compact | recovery/ 错误压缩与自愈 |
| regression-suite | regression/ 反测集 + test-prompts.json |
| checkpoint | checkpoint-pattern 公约 |
| cron-production | monitor/ 监控骨架 |

### hpp validate — 工程结构校验

```bash
hpp validate ~/my-agent
```

检查:SKILL frontmatter(name/description/version)、STATE.md 存在性、JSON/YAML 可解析、疑似真实密钥泄漏。

### hpp audit — Production Readiness Score

```bash
hpp audit ~/my-agent
```

```text
╔══════════════════════════╗
║ Production Readiness     ║
╚══════════════════════════╝
Reliability      ██████████ 25
Observability    ██████░░░░ 12
...

Score: 68/100
Grade: Needs Hardening

Missing evidence:
  A3 [Reliability] 静默失败防护(monitor/alert 路径)

Recommended:
  hpp add cron-production
```

评分模型:`audit/scoring/readiness-score.md`;检查单:`audit/checks/checklist.md`。

### hpp doctor — 环境诊断

```bash
hpp doctor
```

检查:Python 版本、HPP 仓库完整性、hermes/git 可用性、Hermes skills 目录、PyYAML。

## 设计约定

- 纯 stdlib,零依赖(PyYAML 可选,仅影响 validate 的 yaml 检查)
- 只读写用户指定的目标目录;`hpp add` 对已存在文件跳过不覆盖
- 审计证据来自文件名与文件内容的关键词匹配——保守判定,误报无害,漏报可见
