# CURRENT_SITE_AUDIT — V1 现状审查 (2026-08-30)

> 任务书 STEP 1 产物。对象：[线上站点](https://komagon.github.io/hermes-production-patterns/)

## 技术栈

| 层 | 实现 | 状态 |
| --- | --- | --- |
| 生成器 | mkdocs 1.6.1 + mkdocs-material 9.7.7（社区版） | 稳定 |
| 内容源 | 仓库 markdown（conventions/patterns/examples/templates + 根文档） | SSOT，受保护 |
| docs 层 | scripts/build_docs.py 构建期生成（38→40 页） | 幂等，gitignore |
| 部署 | .github/workflows/deploy-docs.yml → GitHub Pages | CI 绿 |
| 质量闸门 | markdownlint + link-check + `mkdocs build --strict` + check-nav | 全绿 |

## 当前页面清单（V1，40 页）

- index.md（README 直转，文档式首页）
- 决策入口：router.md（场景→公约表）、skill-graph.md（公约互链 SVG）
- 总览：ARCHITECTURE / CONTEXT / CHANGELOG
- 方法论 Patterns ×4；工程公约 Conventions ×15（含自动 Skill Contract 卡）；
  实战案例 Examples ×4+子页；模板；CONTRIBUTING；EN README

## 当前组件（Material 主题内）

- 导航：三栏（左 nav sections / 正文 / 右 ToC），明暗双 palette，indigo 主色
- 交互：内置 lunr 搜索（⌘K/`/` 聚焦已支持）、代码复制、toc.follow、卡片折叠（??? admonition）
- 生成期组件：契约卡、路由表、环形图谱（构建期内联 SVG，节点已可点击）

## 内容系统

- 每公约 frontmatter：name/description/version/category/tags/related_skills
- 描述格式 `标题 — 一句话问题陈述`，是路由表与图谱标签的派生源

## 对照 V2 任务书的问题（按 P0/P1 归类）

| # | 问题 | 任务书条目 |
| --- | --- | --- |
| 1 | 首页是 README 直转：10 秒内看不出"Production Engineering Pattern System"定位，无 Hero/CTA | §7 §40-P0 |
| 2 | 无 Why Agents Fail / Problem→Solution 模块，问题驱动叙事缺失 | §9 §10 P0 |
| 3 | Pattern Library 是目录列表，无 Featured/分类卡片层级 | §12 §13 P0 |
| 4 | 明暗双主题+indigo 配色，与要求的统一深色工程终端风（#080A0D）不符 | §14 §26 §29 P0 |
| 5 | Pattern 详情页顶部无 category/maturity/complexity/reliability 信息栏 | §15 §16 P0 |
| 6 | Architecture 页是纯文字文档，无 Normal/Error Flow 图 | §19 §20 P0 |
| 7 | 无 Production Maturity 时间线、Choose Your Path、案例 Case-Study 化 | §21 §22 §23 P1 |
| 8 | 搜索 placeholder 无 ⌘K 提示与语义词 | §24 P1 |
| 9 | 图谱节点 hover 无高亮/关联弱高亮 | §11 P1 |
| 10 | 无 per-page SEO title/description 定制 | §38 |

## 可复用资产（V2 不重造）

1. build_docs.py 生成管线与幂等约定 —— V2 首页/卡片/图谱仍由它派生，内容零硬编码（§36）
2. frontmatter 元数据 —— category/related/version 直接喂给 V2 卡片与图谱
3. 内联 SVG 方案 —— 无外部 CDN 依赖，满足国内可达 + §39 性能
4. check-nav 回归闸门、--strict、CI 链路 —— 原样保留，V2 在其上迭代
5. router.md/skill-graph.md 的数据抽取函数 —— parse_meta 可扩展

## V2 技术路线判定

任务书组件清单（§35）是 React 心智，但在 mkdocs 上以
「custom_dir partial 覆写 + extra_css 设计令牌 + 构建期 HTML/SVG 生成 + <5KB 原生 JS」
可达成同等 UI/UX，且保留 §37 内容保护与既有质量闸门。换 Next.js 重写 = 丢掉
SSOT/CI/40 页内容管线，违背任务书自身原则 6-8 条。故：Material 深度定制路线。
