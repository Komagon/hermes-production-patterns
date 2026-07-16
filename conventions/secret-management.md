---
name: secret-management
description: "密钥管理 — API Key、Token、密码的存放和轮换规范"
version: 1.0.0
author: Komagon / Hermes Production Patterns
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, pattern, convention, secret, security, env]
    category: conventions
    related_skills: [control-flow-separation, error-compact-pattern]
---

# 密钥管理

> **对应 12-Factor Agents 的隐含原则：Secrets 不与代码共存**

## 核心原则

**密钥不进 Git、不进上下文、不落日志。**

## 密钥存放层级

| 层级 | 位置 | 适用 | 风险 |
|:----|:-----|:----|:----:|
| L1 | `.env` 文件（`~/.hermes/.env`）| 个人开发机 | 低（.env 在 gitignore 中）|
| L2 | 系统环境变量 | 服务器部署 | 中（进程可读）|
| L3 | 密钥管理服务（Bitwarden/AWS Secrets） | 生产环境多机部署 | 低（审计+轮换）|

## Hermes 中的实践

### 基本做法

```bash
# ~/.hermes/.env
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx
TUSHARE_TOKEN=xxx
```

Hermes 自动加载 `.env` 到环境变量，Skill 中通过 `os.getenv()` 读取。

### 禁止的做法

```python
# ❌ 密钥硬编码在 SKILL.md 中
api_key = "sk-xxx"

# ❌ 密钥硬编码在代码中
HEADERS = {"Authorization": "Bearer sk-xxx"}

# ❌ 密钥通过 Prompt 传给 LLM
prompt = f"使用密钥 {api_key} 调用 API"

# ❌ 密钥写入日志
logger.info(f"API Key: {api_key}")
```

## 密钥轮换

| 类型 | 轮换频率 | 做法 |
|:----|:--------|:-----|
| 个人 API Key | 每 90 天 | 更换 `.env` 文件 |
| 生产环境 Key | 每 30 天 | 通过密钥管理服务自动轮换 |
| 泄露后 | 立即 | 立即吊销+更换 |

## 演练清单

```markdown
[ ] 所有密钥是否在 `.env` 中，不在代码里？
[ ] `.env` 是否在 `.gitignore` 中？
[ ] 是否有密钥被写入日志的历史？
[ ] 是否有密钥通过 Prompt 传给 LLM？
[ ] 是否有密钥出现在错误消息中？
[ ] 上次轮换密钥是什么时候？
```

## 与 Hermes 的配合

Hermes 的 `security.redact_secrets` 功能默认开启，会在工具输出中自动扫描并脱敏 API Key 样式的字符串。**不要关闭它。**

```bash
hermes config set security.redact_secrets true  # 保持开启
```