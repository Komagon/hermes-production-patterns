# Security Policy

这个仓库的核心公约之一是 [`conventions/secret-management.md`](conventions/secret-management.md)。
一份讲密钥管理的文档如果自己不写上报路径，那条公约就只对别人生效。

## 支持范围

| 版本 | 是否接受安全修复 |
|:---|:---|
| 最新 `v2.x` tag | ✅ |
| 更早的 `v2.x` | ⚠️ 只修严重问题，且需能升级到最新版 |
| `v1.x` | ❌ 请先升级 |

## 报告漏洞

**不要开 public issue。**

- 首选：GitHub 的 [Private vulnerability reporting](https://github.com/Komagon/hermes-production-patterns/security/advisories/new)（Security → Report a vulnerability）。
- 备选：如果该入口不可用，请开一个**不含细节**的 issue，只写「需要一个安全联系方式」，维护者会私信你。

报告里请包含：

1. 受影响的文件 / 脚本 / workflow，以及版本或 commit；
2. 复现步骤（能贴最小复现最好）；
3. 影响判断：是「工具本身有漏洞」还是「按文档做会写出漏洞」；
4. 如果你已经有修复思路，欢迎附上。

**响应时限**：48 小时内确认收到，7 天内给出初步判断（是否成立、影响面、修复计划）。
这是单人维护的项目，超时会主动告知，不会静默。

## 本项目的威胁模型

这个仓库发布的是**工具与文档**，不是运行时服务。因此威胁面集中在三处：

### 1. 工具会读你的仓库

`cli/hpp.py validate`、`scripts/lint.js`、`scripts/run_regression.py` 会读取本地文件，
`run_regression.py --backend openai|anthropic` 会把 `test-prompts.json` 里的 prompt 发给模型服务商。

- **不会**上传你的代码；只有 `--backend command|openai|anthropic` 时才会发起网络请求。
- `--backend replay` 完全离线。
- 发给模型的内容 = 该条 `prompt` 字段 + 可选的 `--system-file`（默认 `AGENTS.md`）。**如果你的 prompt 里带业务机密，请用 replay 或 command 后端。**

### 2. 工具会写你的文件

- `scripts/lint.js --fix` 会改文件，改前备份到 `.hpp-backup/<时间戳>/`；
  frontmatter 解析失败时**拒绝修复**而不是硬写。
- `scripts/atomic_state_write.py` 走临时文件 + 原子 rename，不会留下半个 STATE.md。
- `cli/hpp.py init` 不覆盖已有内容、不删除任何东西、不跟随 symlink。

### 3. 密钥检测是「尽力而为」，不是保证

`hpp validate` 内置 6 类常见密钥模式（OpenAI/Anthropic、GitHub、AWS、Bearer、私钥块、Slack），
带占位符与环境变量读取过滤，命中时脱敏输出。

它能抓到写死的 key，**抓不到**你自创格式的凭证、编码后的凭证、以及拼字符串拼出来的 key。
把它当 smoke detector，不是当防火墙——真正的防线是 [`secret-management.md`](conventions/secret-management.md) 里的「密钥只从环境读」。

## 凭证如何存放

本仓库**不需要任何凭证**就能跑完整测试套件（`python -m pytest`）。

需要凭证的只有 `.github/workflows/behavioral-regression.yml`，它读两个 repository secret：

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`

该 workflow 只在 `workflow_dispatch` 和每周定时触发；没有配置 secret 时**跳过并说明原因**，
不会伪装成通过。secret 不会被写入日志——脚本只打印是否存在，从不打印值。

## 依赖

- 运行时：`cli/` 与 `scripts/` 全部为 Python 标准库 / Node 标准库，**零运行时依赖**。
- 开发时：`tests/requirements-dev.txt`（pytest、pytest-cov、pyyaml）。
- 由 Dependabot 按周检查 GitHub Actions 与 dev 依赖，见 `.github/dependabot.yml`。
