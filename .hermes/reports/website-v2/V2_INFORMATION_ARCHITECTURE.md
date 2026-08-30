# V2 信息架构 (2026-08-30)

> 任务书 STEP 2 产物。约束：不删现有页面、不改内容目录结构、docs/ 仍全部由
> scripts/build_docs.py 派生（Markdown = SSOT，§36/§37）。

## 导航（mkdocs.yml nav，V2）

```text
首页 Home                 index.md            ← 重写为 Landing（10 模块）
决策入口
  ├ 路由入口 Router        router.md            （V1.5 已有，保留）
  └ 模式图谱 Skill Graph   skill-graph.md       （V1.5 已有，升级 hover 交互）
Pattern Library           patterns-library.md   ← 新增：分类卡片库（P0）
方法论 Patterns ×4                              （不变）
工程公约 Conventions ×15                        （内容不变，页面外壳升级）
实战案例 Examples ×4+子页                        （索引页 Case-Study 化）
生产架构 Architecture       architecture-page.md  ← 新增：图文 Normal/Error Flow
  （原 ARCHITECTURE.md 仍在「总览」组内，不删）
总览 / 模板 / 参与贡献                            （不变）
```

页面增量：+2（pattern library、architecture page），0 删除。

## 首页模块顺序（任务书 §6 的 10 段映射）

```text
01 Hero          BUILD AGENTS THAT SURVIVE PRODUCTION. + 三 CTA + 架构流程图(SVG)
02 Why Agents Fail   6 问题卡（State Loss/Silent Failure/Cron Drift/
                     Context Explosion/Self Validation/Skill Regression）
03 Pattern Solutions Problem→Pattern→Result 三段链
04 Production Architecture  Scheduler→Maker→Checker→State→Notifier 流图
05 Pattern Relationship     复用 skill-graph SVG 内嵌 + 链接到全图
06 Pattern Library          Featured 3 大卡 + 5 分类小卡 + 链到 /patterns-library
07 Production Maturity      PROMPT→…→AUTONOMOUS + L1/L2/L3
08 Real Examples            4 张 Case Study 卡
09 Choose Your Path         Beginner / Automation Builder / Production Engineer
10 Final CTA                Get Started(装仓库) + GitHub
```

## 内容层级与来源

| 首页区块 | 数据来源 | 派生方式 |
| --- | --- | --- |
| Pattern 卡片 | conventions/*.md frontmatter | build_docs.py parse_meta |
| 问题→解 | 手工映射表（6 条，任务书 §9 指定） | build_docs.py 常量 |
| 分类/配色 | CATEGORY_MAP 常量（6 类，§14） | 同上 |
| 成熟度 | patterns/maturity-* 的既有文字 | 摘要 + 链接，不复制正文 |
| 案例卡 | examples/*.md H1+首段 | parse |

硬编码禁令（§36）：首页所有 Pattern 级信息一律来自 frontmatter/正文解析；
Hero 文案、6 问题框架属于品牌层，是允许写在模板 partial 里的唯一静态文案。

## 详情页结构（Engineering Decision Layout, §15-§18）

- H1 上方：分类 kicker（MONOSPACE UPPERCASE + 分类色）
- H1 下：meta 信息栏 MATURITY/COMPLEXITY/RELIABILITY/HERMES（来自扩展 frontmatter 新字段，缺省值安全）
- 契约卡（V1.5 已有）并入信息栏体系
- 11 段标准结构不强行重排既有正文（保护 §37），用「陷阱≈Failure Modes/Anti-Patterns、
  何时用」在 meta 栏与锚点呈现；When to Use / NOT 用新 frontmatter 字段渲染成 ✓/✕ 卡

## 搜索（§24）

Material 原生支持 ⌘K/ctrl+k 与 placeholder 自定义（i18n 覆写）→ 只改配置+覆写 zh locale，占位文案
「搜索 Patterns、问题、架构… (⌘K)」。搜索结果天然按页面分组（lunr location 层级）。
