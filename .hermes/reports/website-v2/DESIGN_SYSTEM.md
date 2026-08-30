# V2 设计系统 (2026-08-30)

> 任务书 STEP 3 产物。全部令牌落地在 docs 构建时注入的 extra_css（partials 覆写）。

## Color（§29 原样采用）

```css
--hpp-bg-primary:    #080A0D;  /* 页面底 */
--hpp-bg-secondary:  #0D1117;  /* 次级面 */
--hpp-bg-card:       #11161D;  /* 卡片 */
--hpp-text-primary:  #F2F4F7;
--hpp-text-secondary:#8B949E;
--hpp-accent-primary:#78FFB7;  /* 主强调:CTA/高亮 */
--hpp-accent-secondary:#62D9FF;
--hpp-warning:       #FFB454;
--hpp-error:         #FF6B6B;
```

主题策略：palette 固定 slate（统一深色，任务书 §14），primary 调深色以匹配。

分类 Accent（§14，用于卡片左边框/kicker/标签/图谱节点）：

| 分类 | 色 | Token |
| --- | --- | --- |
| STATE | Blue #62D9FF | cat-state |
| QUALITY | Green #78FFB7 | cat-quality |
| AUTOMATION | Violet | cat-automation（任务书未列，补 #B78FFF）|
| MEMORY | Purple #C792EA | cat-memory |
| RELIABILITY | Cyan #4DD0E1 | cat-reliability |
| EVOLUTION | Orange #FFB454 | cat-evolution |
| SECURITY | Red #FF6B6B | cat-security |

卡片规则（§14 末）：深色卡 + accent 左边框 + accent kicker，禁止高饱和整卡背景。

## Typography（§30）

- Headline/body：系统 sans 栈优先 + Inter（本地无 Google 依赖，用 system-ui 回退；
  中文回退链必须显式带 CJK 字体，WSL 渲染纪律）
- Mono：JetBrains Mono，回退 ui-monospace
- Kicker/技术标签：mono 12px uppercase letter-spacing .12em
- Hero H1：clamp(44px, 8vw, 96px)，900 字重，逐行断排，PRODUCTION. 用 accent-primary

留白：区块间距 desktop 160 / tablet 96 / mobile 64（§31 区间中值）。

## 组件规格（§35 在 Material 内的等价物）

| 任务书组件 | 实现 |
| --- | --- |
| Hero / CTA | 覆写 home.html partial（仅首页模板） |
| PatternCard | build_docs.py 生成 HTML 卡片 + extra_css 网格 |
| PatternGraph / ArchitectureGraph | 构建期内联 SVG（无 CDN），hover 用 :has/.sel 类 + <6KB 原生 JS |
| ProblemSolutionCard / MaturityTimeline / PathCard / CaseStudyCard | 首页 partial 内静态生成，数据来自 parse_meta |
| Navbar/Footer/SearchDialog | Material 原生，palette + i18n 覆写定制 |

## 动效（§33）

允许：卡片 hover 位移+边框 glow、节点 hover 高亮+关联弱高亮、fade-in（IntersectionObserver，一次性）。
禁止：autoplay 循环、粒子、旋转。prefers-reduced-motion 全部禁用。

## 响应式（§34）

- <960px：卡片网格降列；图谱 SVG 容器横向滚动（不缩到看不清），<600px 降单列
- 首页 Hero 在移动端改上下堆叠

## 性能/SEO/可访问性（§38-39）

- 零新增外部请求（字体不引 webfont，emoji 用 twemoji 已是本地打包）
- meta  description：mkdocs 页 frontmatter `description` + Material meta 支持
- 图谱/架构图加 aria-label 与 <title>；对比度均 ≥ AA（accent 仅用于大文本/边框）
- 目标：JS <10KB 自研、静态生成、lazy-load 不适用（无图）

## 元数据扩展（§36 合规路径）

公约 frontmatter `metadata.hermes` 下新增可选键（旧文件不阻塞，缺省安全值）：
```yaml
maturity: L2 | complexity: medium | reliability: high
when_to_use: [...] | when_not_to_use: [...]
```
15 个公约先以「缺省 + 分类」上线，字段逐条补齐后图谱/卡片自动丰富。
