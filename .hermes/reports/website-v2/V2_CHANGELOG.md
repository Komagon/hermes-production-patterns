# V2 改版说明与变更记录 (2026-08-30)

> 任务书 STEP 10 产物。对应版本 v1.06.00。
> 技术路线（见 CURRENT_SITE_AUDIT.md 判定）：mkdocs-material 深度定制 —
> custom_dir partial 覆写 + extra_css 设计令牌 + 构建期 HTML/SVG 生成 + 4KB 原生 JS。
> 内容红线全部遵守：Markdown 仍为 SSOT（§36），零页面删除（§37），质量闸门全绿。

## 交付清单（对照任务书优先级）

### P0 — 全部完成

| 任务书 | 落地 |
| --- | --- |
| §6 首页信息架构 | `index.md` 重写为 10 模块 Landing（Hero→Why Agents Fail→Solutions→Architecture→Relationship→Library→Maturity→Examples→Paths→CTA），由 `build_docs.py: make_home()` 构建期生成 |
| §7 Hero | 「BUILD AGENTS THAT SURVIVE PRODUCTION.」分行大标题（clamp 44-96px，PRODUCTION. accent+glow）+ 中英副题 + 三 CTA（Explore Patterns / View Architecture / GitHub） |
| §8 Hero 核心视觉 | 生产架构 SVG（Scheduler→Maker→Checker→State→Notifier + FAIL 重试环 + Human Gate），节点可点击进入对应公约；数据流边线流动动画；另配 1 个终端元素（§32 限 1-2 处） |
| §9 Why Agents Fail | 6 问题卡（State Loss / Silent Failure / Cron Drift / Context Explosion / Self Validation / Skill Regression），各带英文陈述 + 中文 + → 解法入口 |
| §10 Problem→Solution | 6 条「问题→模式→结果」因果链，与 §9 六问题一一对应 |
| §12-13 Pattern Library | 首页 Featured 3 大卡（Maker/Checker、State File、Cron）+ Secondary 8 分类行；卡片含 CATEGORY/TITLE/描述/RELIABILITY ●●●●●/COMPLEXITY ●●○○○/HERMES chip/→ VIEW PATTERN |
| §14 分类视觉系统 | 统一深色（禁双主题切换出浅色），分类 accent 走「Dark Card + Accent Border + Accent Tag + Small Glow」，禁高饱和整卡背景 |
| §15-18 Pattern Detail | Engineering Decision Layout：分类 kicker（mono 12px uppercase）→ H1 → MATURITY/COMPLEXITY/RELIABILITY/HERMES/VERSION 信息栏 → When to Use ✓ / When NOT ✕ 双栏卡；数据来自 frontmatter 新 `hpp_*` 键（缺省安全） |
| §19-20 Architecture 页 | 新增 `/architecture-page/`：可点击架构大图 + NORMAL FLOW / ERROR FLOW（FAIL→Feedback→Retry→Limit→Human Escalation）+ 组件职责表 |
| §34 Responsive | 桌面/平板/移动三档断点实测通过（390px 无横向溢出）；两张图在窄屏保持可读尺寸 + 容器横向滚动（不缩到看不清） |

### P1 — 全部完成

| 任务书 | 落地 |
| --- | --- |
| §11 Pattern Relationship | 图谱升级为分类环排 + 弦式曲边 + 双环标签错位 + 中心品牌圆；hover/focus 节点高亮、关联弱高亮、其余暗化（键盘 tabindex 可达）；节点可点击、title 显示问题简介 |
| §21 Production Maturity | 首页六级时间线（PROMPT→…→AUTONOMOUS AGENT）+ L1 Assistant / L2 Copilot / L3 Autonomous 三卡（含 Required Patterns） |
| §23 Choose Your Path | Beginner / Automation Builder / Production Engineer 三卡，各带可点击模式栈 |
| §22 Examples Case-Study 化 | 首页 4 张 CASE STUDY 卡（从 examples/*.md H1+首段自动派生，句读智能截断） |
| §24 搜索体验 | ⌘K 原生支持确认 + zh locale 覆写 placeholder「搜索 Patterns、问题、架构… (⌘K)」；search.highlight 开启 |
| §25 Pattern Explorer | 新增 `/patterns-library/`：分类过滤 pills + 关键词搜索框 + SHOWN 计数（纯原生 JS，实测 15→quality:2→cron:1→记忆:1→security:1 全通过） |

### P2 — 部分完成

§25 的 search/category 过滤已上线（Selector 雏形）；capability matrix 与 AI 助手不在本版范围。

### §38-39 SEO / 性能 / 可访问性

- `overrides/main.html` 覆写 site_meta：每页 og:type/title/description/url/image + twitter:card + 独立 `<title>`/description（Material 原生不出 og，此为补齐）
- 零新增外部请求：无 webfont（系统栈 + CJK 回退链）、图全内联 SVG；自研 JS 4.2KB
- 图均带 role=img + aria-label + `<title>` tooltip
- Landing 10 模块内容 1.5s 兜底强制可见（渐进增强：动画只是锦上添花，JS 失效不空洞）

## 变更文件

| 文件 | 变更 |
| --- | --- |
| `scripts/build_docs.py` | V2 生成器：landing/library/arch 页、decision layout 注入、弦图、案例卡派生、hpp_* 元数据解析；README 保链为 `/readme/` |
| `assets/hpp.css` (新) | 设计系统令牌 + 全部组件样式 + 响应式 + reduced-motion 红线 |
| `assets/hpp.js` (新) | 图谱 hover / Explorer 过滤 / 滚动淡入(+兜底)，4.2KB 无依赖 |
| `overrides/partials/languages/zh.html` (新) | 搜索 placeholder 覆写 |
| `overrides/main.html` (新) | OG/SEO site_meta 覆写 |
| `conventions/*.md` ×15 | 仅追加 `hpp_*` frontmatter 键（正文零改动，旧消费者无感知） |
| `mkdocs.yml` | custom_dir / 统一深色 palette / font:false / extra_css+js / nav +4 条目 / search.highlight |
| `.gitignore` | docs/ site/ 生成物规则不变 |

## 验证记录（任务书 §42 增量验证）

每阶段跑：build_docs → check-nav(43 页) → `mkdocs build --strict`(0 错误) → markdownlint(源文件 0 issues)。
页面实测（Playwright 无头，1440px + 390px 双档，全页截图 + 视觉审查 5 轮）：

- 首页 10 模块完整、无空洞无重叠 — PASS
- 图谱标签完整无截断无重叠 — PASS
- 详情页 Decision Layout 五要素齐全 — PASS
- 架构页图/链/表 — PASS
- Explorer 过滤+搜索交互 — 实测通过
- 移动端全部页面无横向溢出 — PASS
- 内部链接爬取 0 坏链（修复 README.en.md 与 logo 相对路径两处后）

已知非阻断小项（留 V2.1）：readme 页 🇬🇧 emoji 在无 CJK-emoji 字体的终端环境显示豆腐块（站点 logo 正常，仅 README 源文件顶栏徽章行受影响）。

## 不变的东西（§37 内容保护）

- 40 个 V1 页面一删未删：README 首页 → `/readme/`，其余原地
- `docs/` 全部仍是 `build_docs.py` 派生，Markdown SSOT 不动摇
- CI 三闸门（lint / link-check / strict build + check-nav）原样生效
- router.md / skill-graph.md / 契约卡机制保留，仅在其上升级
