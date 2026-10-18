# Changelog

## v2.5.4 (2026-10-18)

### 🏷️ 发布一直是手工的，于是它停了

`git tag` 一路推到 v2.5.3，Releases 页面却停在 v2.4.0——**有 6 个 tag 没有对应的 release**（v2.4.1、v2.4.2、v2.5.0、v2.5.1、v2.5.2、v2.5.3）。发版说明其实早就写在 `CHANGELOG.md` 里，缺的只是「把它复制到 GitHub 上」这一步；而手工步骤的典型失败方式就是**静默不做**。

- **`scripts/publish_release.py`（新）**：从 `CHANGELOG.md` 的 `## vX.Y.Z` 段取发布说明，交给 `gh release create`。`--tag` 发单个，`--all-missing` 补齐所有「有 tag、有 changelog 段、还没 release」的版本（按版本号升序发布，保证 latest 落在最新版），`--dry-run` 只打印。
  - 标题取该段第一个 `###` 副标题，拼成 `v2.5.4 — 🏷️ ...`。
  - 没有 changelog 段的 tag 跳过（历史上有 `v2.0.00` 这种没写说明的）；非 semver tag（如 `v1.0.0.11`）忽略。
  - **dry-run 不说谎**：没有 `gh` 时明确打印「无法确认是否已发布」，而不是假装每个都要发。
- **`.github/workflows/release.yml`（新）**：`push: tags: [v*]` 发布该 tag；`push: main`（仅当 CHANGELOG / 本脚本 / 本 workflow 变动）执行 `--all-missing` 补历史；另留 `workflow_dispatch` 手动补。`permissions: contents: write`。
- **补齐 6 个漏发的 release**：v2.4.1 / v2.4.2 / v2.5.0 / v2.5.1 / v2.5.2 / v2.5.3 现在都有页面，正文就是各自的 changelog 段。v2.5.1 那段里「这一版是必要的，但不充分——CI 仍红」照原样保留：历史不该被润色。
- **测试 11 例**：changelog 分段（边界、副标题缺失）、版本号按数值而非字典序排序、非 semver 拒绝、dry-run 不调 `gh`、缺段落退出 2。

## v2.5.3 (2026-10-18)

### 📌 可复用 workflow 钉住的 action 版本会漂，现在有门禁

`readiness-gate.yml` 里刻意把 action 引用写死成同一个 tag：这样 `@vX.Y.Z` 的行为端到端冻结，调用方不会因为默认分支前进而被动升级。但「同一个 tag」是手工维护的——v2.5.2 修了 action 的编码 bug，workflow 里还钉着 `@v2.5.0`，**调用方拿到的仍是坏的那一版**。

- **钉版本对齐到 `@v2.5.3`**（注释、示例、`uses:` 三处）。
- **新门禁 `test_reusable_workflow_pins_the_current_release`**：`readiness-gate.yml` 里对 action 的 `uses:` 必须以 `@v{package.json 的 version}` 结尾，否则红。发版忘了改，CI 会拦住，而不是等调用方踩坑。
- **README 同步**：两份 README 都新增「这个仓库怎么验证自己 / How this repository verifies itself」——把 9 条门禁、对应命令、各抓什么列成表，并写明两条原则（「跑不动」也是红；只写在文档里的约束等于默认违规）。脚本清单补 `run_regression.py` / `gate_summary.py` / `audit_field.py`，用例数 107 → 122，action 引用版本从 `@v2.5.0` 更新到 `@v2.5.3`。

## v2.5.2 (2026-10-18)

### 🐛 真正的红：`open()` 没写 `encoding`，在英文版 Windows 上读 UTF-8 会炸

v2.5.1 修的是「测试假装自己是 UTF-8」，修完 CI 还是红。拿到真实堆栈后才看清：

```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x8d in position 579
```

`readiness-gate` action 里用内联 `python -c 'json.load(open(sys.argv[1]))["score"]'` 读报告。`open()` 不写 `encoding` 就用**系统 ANSI 代码页**：GitHub 的 Windows 运行器是英文版，代码页 1252，而 `hpp audit --json` 输出的是 UTF-8，`0x8d` 在 cp1252 里是未定义字节——直接抛异常。于是 action 一个分数都没报出来，测试断言 `'score=0' in ''` 才失败。

这个 bug 在我本机永远复现不了：cp936（GBK）几乎能解任何字节序列，中文 Windows 上「UTF-8 文件用默认编码读」看起来一直是对的。**这是本仓库最想防的那类问题——不是逻辑错，是环境假设错。**

- **`scripts/audit_field.py`（新）**：把「从报告里取字段」从 YAML 里的内联 Python 挪成可导入、可测试的脚本，显式 `encoding="utf-8"`。action 改为调用它。
- **两处同族隐患一并修掉**：`cli/hpp.py` 的 `open(os.devnull, 'w')`、`check_docs_consistency.py` 里 `git tag` 的 `subprocess.run(text=True)` 都补上 `encoding`。
- **加机械门禁 `tests/test_file_encoding.py`（7 例）**：
  - AST 扫描 `cli/` 与 `scripts/` 下所有随仓库运行的 Python，**任何文本模式 `open()` / `read_text()` / `write_text()` 缺 `encoding=` 就红**；
  - 扫描 `.github/workflows/*.yml` 与 `.github/actions/**/action.yml` 的 `run:` 块，**禁止内联 `python -c`**——这类代码测不到，正是本次踩坑的地方。
  - 这条门禁本身就是本仓库的公约：只写在文档里的约束等于默认违规（反模式 #13）。
- **`scripts/audit_field.py` 的测试（6 例）**：字段顺序、含中文的报告、缺字段返回空串但退出 0、报告缺失/损坏时退出 2 且不打 `Traceback`。

## v2.5.1 (2026-10-18)

### 🩹 修 v2.5.0 在 Windows CI 上的红：判定的 UTF-8 契约没写下来

> 这一版是必要的，但不充分——CI 仍红，真因见 v2.5.2。

v2.5.0 推上去之后 `Unit Tests (windows-latest)` 红了，Ubuntu 绿。原因不在被测代码，在**测试自己没说清契约**：`run_regression.py` 一直按 UTF-8 解码后端 stdout，而测试里的假后端是 `python -c "print('独立检查')"`——在 ANSI 代码页 1252 的 Windows 运行器上，`print` 写中文直接 `UnicodeEncodeError`，子进程退出 1，判定按 fail-closed 记 `FAIL`，测试却断言它该 `PASS`。本机（代码页 936）能过，所以一直没暴露。

- **假后端改为显式输出 UTF-8 字节**：测试里新增 `_say()`，走 `sys.stdout.buffer.write(text.encode("utf-8"))`。`-X utf8` 不够——`PYTHONIOENCODING` 会覆盖它，这一点是本地用 `PYTHONIOENCODING=cp1252` 复现时才看清的。
- **顺手修掉一个「碰巧能跑」**：测试里的 `--command` 一直没给解释器路径加引号，`G:\workbuddy 1\...\python.exe` 能被正确执行纯属 Windows CreateProcess 会沿命令行找「存在的最长前缀」。路径换成 `C:\Program Files\...` 就会碎。现在统一加引号。
- **新增 1 条用例（共 108）**：后端吐出非 UTF-8 字节时，必须是「判定为未命中」，而不是让运行器抛 `Traceback`——`errors="replace"` 是契约的一部分，值得钉住。
- **CI 把这条路径钉死**：`unit-tests` 的 Windows 腿现在显式带 `PYTHONIOENCODING=cp1252` 跑（Linux 腿不变）。既然用户就在非 UTF-8 控制台里跑，测试就该在那个环境里跑，而不是在碰巧是 CJK 代码页的机器上绿。
- **契约写进文档**：`--command` 的帮助文本、`README.md` / `README.en.md` 都补了一句「后端 stdout 按 UTF-8 解码，非 ASCII 输出要显式 UTF-8」。

## v2.5.0 (2026-10-18)

### 🎯 第三阶段：从「模式集」到「可执行的验收标准」

前两阶段把门禁修到「跑不动就红」。这一阶段解决最后一件没说清的事：**谁都可以说自己的模式有效，只有跑过的人不算说。**

- **真跑反测 `scripts/run_regression.py`（新）**：不再只校验 JSON 字段，而是把 36 条 prompt **真的执行**并做二值判定——`assertions` 必须出现、`forbidden` 必须不出现。判定刻意做得很笨（大小写折叠 + NFKC + 空白归一后的子串包含），因为「你没法手工复算的判定不算证据」。
  - **fail-closed，而不是三态模糊**：后端报错、返回空、条目没有 assertions **一律判 `FAIL`**——这是 `conventions/skill-evolution.md`「硬门禁判定纪律」里早写下的规矩（「没法确认命中」不能拿「不好说」当通过）。初版把它判成 `INCONCLUSIVE` 并默认退出 0，等于自己又违反了一次自己的公约，已改回。`INCONCLUSIVE` 只留给条目**运行前**就写好的 N/A sentinel（`"na": "deprecated: ..."`），且不计入已验证数；全表都是 N/A 时会显式警告「什么都没验证」。
  - **不绑定模型**：`--backend command` 接任意 agent CLI（prompt 走 argv 单参数或 stdin，**不经过 shell**，prompt 里的 `;`、`$(...)`、反引号都不会被解释）；`--backend openai|anthropic` 直连 HTTP（纯标准库）；`--backend replay` 离线重判上次录下的答案。
  - `--record` 存答案、`--only`/`--limit` 选子集、`--system-file` 注入公约、`--json` 出机器可读结果，报告写 `BEHAVIOR_REPORT.md`（FAIL 附缺失 assertion 与原文摘录）。
- **`.github/workflows/behavioral-regression.yml`（新）**：只在 `workflow_dispatch` 与每周一跑——这是唯一花钱的 workflow。没配 secret 时 job **跳过并写明原因**，不伪装成通过。
- **Readiness 门禁可以装到别人的仓库里**：
  - `.github/actions/readiness-gate/action.yml`（composite action）：输入 `path` / `fail-under`，输出 `score` / `grade` / `report`，把五维明细写进 job summary，低于阈值让步骤失败。
  - `.github/workflows/readiness-gate.yml`（可复用 workflow）：`uses: Komagon/hermes-production-patterns/.github/workflows/readiness-gate.yml@v2.5.0`。
  - 新增 `scripts/gate_summary.py` 把 `audit --json` 渲染成 markdown，避免在 YAML 里重写打分逻辑。
  - `hpp audit --json --fail-under N` 现在把失败信息写到 **stderr**，stdout 保持纯 JSON（`| jq` 不用先剥一行人话）。
- **失败复盘提到首屏**：`README.md` / `README.en.md` 顶部原来堆着 6 段 changelog，现在换成 4 条真实事故的一句话摘要 + 链接。四篇复盘各加开篇「如果你只记一句话」，`examples/failures/README.md` 索引表新增该列。
- **`SECURITY.md`（新）**：写清威胁模型（工具会读什么、写什么、密钥检测的能力边界）、支持版本、48 小时确认 / 7 天初步判断的响应时限、凭证如何存放。一个讲密钥管理的项目，这是底线。
- **`.github/dependabot.yml`（新）**：github-actions / pip / npm 三生态每周聚合更新，按周一分组。
- **新增 4 个测试文件（共 107 用例）**：`run_regression.py` 的判定与诚实性（后端不可达、缺录制、shell 注入）、`gate_summary.py`、workflow/action/dependabot 的 YAML 合法性、**以及在 bash 里真跑一遍 composite action 的脚本**（action 是最容易「上线才发现坏了」的一块）。
- **文档一致性检查扩容**：新增「必需文件是否存在」与 `README.md` 里 `N 个 pattern` 的声明核对——这条声明此前写的是 20（实际 21），因为检查器压根没看它，漂了好几个月。

## v2.4.2 (2026-10-18)

### 🛡️ 第二阶段：把「靠自觉」的检查改成「跑不动就红」的检查

v2.4.1 修的是「说的和做的不一致」，这一版修的是「检查和被检查者其实是同一个人写的」——每个门禁都能被自己刷过，等于没有门禁。

- **`hpp audit` 改为按内容取证，不再是文件名匹配**：13 个 0 字节的 `monitor.md`/`STATE.md`/`checker.md` 曾经能刷到 86 分「Production Ready」。现在每项证据必须来自 ≥40 字符的真实正文（`file:` 命中要看文件有没有内容，`content:` 命中要扫正文），并且每条命中都记录证据出处，分数可以手工复算。新增 `--json`、`-v/--verbose`、`--fail-under N`：低于阈值退出码为 1。空壳工程现在得 0 分。
- **密钥扫描重写**：旧实现每条正则都用 `^...$` 整行锚定，而真实密钥从不独占一行（`API_KEY = "sk-..."` 永远匹配不到），所以扫描器 100% 漏报。现在改成非锚定模式（OpenAI/Anthropic、GitHub、AWS、Bearer、私钥块、Slack），带占位符与环境变量读取过滤，输出时脱敏（`sk-A1b…W3x4`）。`validate` 命中即退出 1。
- **`lint.js` 跨平台安全**：CRLF 文件在 Windows 上会被判成「无 frontmatter」，旧 `--fix` 于是再插一个 frontmatter 块，把文件写坏并把 `version: 1.0.0` 降级成 `0.1.0`。现在统一换行后再解析、保留原换行写回、解析失败拒绝自动修复、修改前备份到 `.hpp-backup/<时间戳>/`。同时跳过 `docs/`、`site/` 等生成目录（此前本地跑过 `build_docs.py` 就会把 lint 弄红）。
- **`check_maturity.py` 不再自证通过**：6 条判定项原本 `default=True`，所以不带任何参数也报 6/8 通过。现在全部默认 `False`，新增 `--project DIR` 从项目里推导客观事实（STATE.md、幂等键、checker/、预算、`monitor/runs.log` 的运行日期），L3 明确返回「需人工评审」而不是静默 PASS。
- **新增 `scripts/check_docs_consistency.py`**：核对文档里声称的公约数、anti-pattern 数、starter kit 数、提示词数、版本号（package.json ↔ CHANGELOG ↔ git tag）与 21 篇公约的 frontmatter 完整性。上线第一次运行就抓到「v2.4.1 从未打 tag」。
- **新增 `tests/`（pytest，72 个用例，覆盖率 84%）**：覆盖 `hpp` 的 5 个子命令与 8 个脚本的边界，含空壳工程、伪造证据、CRLF、重复幂等键、锁超时等回归点。测试直接以子进程驱动真实 CLI，所以 `.coveragerc` 用 `patch = subprocess` 让覆盖率跟进子进程。
- **CI 新增 `unit-tests`（Ubuntu + Windows 双矩阵）、`repo-lint`、`docs-consistency`**：Windows 矩阵不是摆设——本阶段修的 5 个 bug 里有 4 个只在 Windows 复现（路径分隔符、`fcntl`/`msvcrt` 分支、`docs\a.md` 与 `docs/a.md` 不相等）。
- **顺带修掉四个真实缺陷**（都由新测试暴露，不是理论问题）：
  - `atomic_state_write.py` 的 `read_state` 解析不了 `format_state` 自己写出的格式（章节被初始化成 list 又用字符串下标赋值，`TypeError`）——读写不闭环。
  - 同一脚本在父目录不存在时，锁文件创建失败被当成「锁竞争」，重试到超时后报 `Could not acquire lock`，与真实原因无关。
  - `build_docs.py --check-nav` 在 Windows 上把 `docs\a.md` 和 nav 里的 `docs/a.md` 相比，导致「全部页面既缺失又未知」；`check_test_suite.py` 遇到重复 id 时退出码仍是 0。
  - **所有入口脚本在非 UTF-8 代码页下打印中文会崩**：Windows 的管道/重定向默认用系统代码页（英文机器是 cp1252），`print("人工评审")` 直接抛 `UnicodeEncodeError`。这个 bug 在 zh-CN 笔记本上永远复现不出来，是 CI 的 Windows 矩阵第一次跑就抓到的——也正是加那个矩阵的理由。现在所有入口统一把 stdout/stderr 钉到 UTF-8（真实控制台本来就走 `WriteConsoleW`，所以只影响管道与重定向）。

## v2.4.1 (2026-10-18)

### 🔧 对齐修复：让「承诺」与「实现」一致（无新增模式）

本版不写新内容，只修 v2.4.0 之前遗留的「说的和做的不一致」。起因是一次外部代码审查——审计脚本可以被 13 个空文件刷到 86 分，而 `main` 的 CI 从 2026-09-30 起一直是红的。

- **`cli/hpp.py` `init` 不再用 cwd/home 路径白名单**：该白名单把 `/tmp` 挡死（CI 冒烟脚本正好写 `/tmp`），是 CI 连续两次失败的根因；同时它也不提供真实防护。改为「不跟随 symlink + 不覆盖已有内容 + 不删除任何东西」。顺带修三个同类问题：`~` 未展开（README 的 `~/my-agent` 在 Windows 上会建出字面量 `~` 目录）、已存在空目录无法初始化（`WinError 183`）、目标为文件时抛未捕获 `NotADirectoryError`。
- **`scripts/validate_state.py` 接受 Markdown 列表前缀**：v2.4.0 的「安全加固」把幂等键正则改成行首锚定，结果拒绝了仓库自带的示例（`- 2026-06-29: article: uuid-a1b2c3`）。这正是 `skill-evolution` 里「旧成功仍然成立」那条被自己违反的实例。同时 `Lessons Learned` 改为「章节必须存在、内容可为空」（新任务尚无经验可写）。
- **两个 starter kit 的 STATE.md 补齐缺失章节**（`basic-agent` 缺 `Idempotency Keys`，两者均缺 `Lessons Learned`），`cron-production` 的幂等键从表格改为与 `templates/STATE.md.template` 一致的列表格式——一个契约，不再各写各的。
- **`scripts/run_regression.py` → `scripts/check_test_suite.py`**：它从来不跑任何 prompt，只校验 JSON 字段齐全。改名后报告口径同步改为 `schema-valid`，并显式标注「未执行行为验证」。徽章从 `Regression 36/36 Pass` 改为 `Test suite 36 schema-valid`。顺带删掉 `Patterns covered` 这个指标——它用 `id.rsplit("-", 1)` 猜模式名，36 条算出 36 个「模式」，是假的。
- **CI 新增 `state-contract` job**：对 `templates/`、`examples/`、`starter-kits/` 下每个 STATE.md 逐一校验，README 里「CI 自动运行 STATE 校验」这句话从此为真（此前为假）。`regression-test` job 更名为 `test-suite-schema`。
- **新增 `.gitattributes`（`* text=auto eol=lf`）**：修 Windows 检出（autocrlf）后 `lint.js` 把全部 21 篇公约误判为「无 frontmatter」的根因，也让后续跨平台工具行为一致。
- **文档数字对齐**：21 个公约（原写 20）、anti-patterns 13 条（原写 8 种）；`package.json` 版本 `2.01.00`（非法 semver）→ `2.4.1`。

已知未修（下一阶段）：`hpp audit` 仍只按文件名匹配证据、密钥扫描仍整行锚定、`lint.js` 在 CRLF 下仍会误判并可能写坏文件、`check_maturity.py` 仍有 6 条恒真项。详见审查报告的 P0-2/P0-3/P1-6/P1-7。

## v2.4.0 (2026-09-30)

### ⚖️ 判断层落地：决策契约（Decision Contract）+ 复现 + 评测标定

此前的能力地图只覆盖**执行层**（cron/状态/错误）与**产出层**（浏览器/网关/多模态），本版首次覆盖**判断层**——「怎么判」不该埋在提示词里。

- **新增公约 `conventions/decision-contract.md` v1.0.0（maturity: beta）**：判断/授权/执行三分离（Decision 出选择+置信度，Policy 出授权，Action 才执行）；五种判断形态的契约六件套（type/candidates/policy/fallback/receipt/version）；后端链 `rule→cache→local→jev→llm→human`（能规则就规则、硬边界先由代码裁剪候选集、失败与越界一律 fail-open）；三段门与**按 type 分阈值**；**Record & Replay**（key 含 version/policy，未接受与降级结果也记，命中即短路复现）；离线评测（弃权单列、有序档位用档位距离）。
- **`data-driven-optimization` v1.0.0 → v1.1.0**：新增「标定闭环」——评测集 → 基线 → **分离度检验**（真值 vs 错值置信度中位）→ `--fresh` 重跑 → 写回 `policy.calibration`。附三条实测教训：置信度不区分对错时阈值无效；有序档位别用精确匹配当唯一指标；弃权 ≠ 答错。
- **`human-escalation` v1.0.0 → v1.1.0**：新增「弃权语义」——拒答不等于答错（实测某决策被算成 0.583，排除弃权后是 1.000）；弃权要能归因到「谁弃的」（收据里的降级轨迹）；弃权率当 SLO 看，不当错误率看。
- **`hermes-capability-map` v1.4.0 → v1.5.0**：新增三族——「十五、决策与路由」（决策插件 / 影子钩子 / 只做判断的后端 / 收据与降级轨迹 / replay / 评测）、「十六、外部工具目录（MCP 延迟加载）」、「十七、多代理任务编排（kanban 工具族：依赖门 / 按原因分流的阻塞 / 交审与打回 / 附件 / 心跳 / 判官续跑）」。
- **反测集 30 → 36 条（覆盖 19 → 20 个行为契约模式）**：新增 5 条决策契约反测（按类型分阈值 / 改型必须升版本 / 弃权不是答错 / 先查候选集再怀疑模型 / 打分刻度由档数决定）+ 1 条能力目录按需加载；`skill-evolution` 速查表同步。
- **验证案例 `examples/decision-os-baseline-2026-09.md`**：8 个判断的 labeled dataset 基线（含 4 个真实修复：候选集解析 0.31→1.00、打分刻度档位数坑、noul 置信度 margin 坑、弃权被算成答错），全部可 `--fresh` 复跑。按项目成熟度分级标为 🟡 beta（有初步验证数据，尚未 ≥30 天长期运行）。
- **兼容性矩阵**：新增 Decision Contract 行（任意版本可用，纪律即可落地；参考实现为扩展面决策 CLI + 可选插件，标 experimental）。

与既有资产关系：全部为增量章节与新增文件，未改动既有行为契约的既有小节；`control-flow-separation`（哪一步用代码）与本节（判断本身怎么被约束与授权）互补，`observability-trace`（收据）与 `data-driven-optimization`（标定闭环）为下游落地。

## v2.3.2 (2026-09-07)

### ✨ Trace Engineering 吸收:工具侧效标注 + capability-registry READ_ONLY/MUTATING 分类

marfinxx Trace Engineering(2026-09-05,13.4 万浏览)新方向吸收,核心洞察:多 agent 系统的失败根因是分布式可追溯性问题,不是提示词问题。可落地的点:

- **control-flow-separation v1.1.0 → v1.2.0**:新增「工具侧效标注(Tool Side-Effect Tagging)」章节。工具静态分为 `READ_ONLY`(纯查询,可安全全量重放)和 `MUTATING`(写文件/发消息/提交,重放走沙箱,真实执行需 approval,执行前写 WAL)。分类表覆盖 13 个能力;保守优先原则:凡无法证明无副作用一律标 MUTATING,缺字段=fail-closed。侧效标注是 anti-patterns #13「规则写两遍」在工具层的机械层落地:规则写进提示词(告诉 agent 工具性质)+ 规则写进 registry(让审批绕不过,agent 的建议只在 GUIDANCE 层有效)。
- **capability-registry.json 机器可读化**:`~/.hermes/routing/capability-registry.json` 全部 13 个能力增加 `side_effect` 字段(6 READ_ONLY / 7 MUTATING),`capability_probe.py` 刷新时保留。示例:web-search=READ_ONLY,git/python/tts=MUTATING。

与 v2.3.0/v2.3.1 关系:前两条(反测试集/状态管理/任务遴选/harness 规则写两遍)在 harness 层收口,本条进到 trace/观测层,是 harness 主题之后的新方向首波落地;真正可落地的只有侧效标注(确定性重放安全前提),其余(trace DAG/causal fault localization/token entropy 断路器/trace-to-memory 蒸馏)属于分布式框架基础设施,当前无接入点,记录为方向备忘不强行落地。

## v2.3.1 (2026-09-07)

### ✨ anti-patterns v1.0.0 → v1.2.0:三条补全 + 纯提示词约束(规则写两遍)

harness 工程主题收尾(借鉴 0xwhrrari 的 harness checklist / Anthropic/OpenAI/Codex 引用),补齐反模式目录到 13 条:

- **反模式 10-12 补全**(此前远端 conventions 落后于本地运行版):事后加载技能(Skill After Start)、过度确认(Premature Confirmation)、死马当活马医(Dead Horse Flogging)。
- **反模式 13「纯提示词约束」(Prompt-Only Enforcement)** — 硬规则只写进提示词/SKILL.md prose、靠 agent「读到并记住」遵守 = 默认违规。纠正 = **规则写两遍**(双编码):指引层(agent 能理解的自然语言,解释为什么)+ 机械层(agent 绕不过的确定性检查:pre_tool_call 拦截、approval 审批域、enabled_toolsets、secret-management 扫描、测试脚本)。判定口诀:硬规则必须给机械层,只靠提示词就是默认违规。测试时 mock 掉 agent 自觉,看机械层拦不拦。

与 v2.3.0 关系:这是「写两遍」共识的兑现,v2.3.0 那四条均在回测集/状态管理/任务遴选层落地,本条落进反面模式目录作为收敛收尾。

## v2.3.0 (2026-09-07)

### ✨ 三篇 X/GitHub 项目吸收:硬门禁判定 + 任务遴选 + 变更收据

按 v2.1.0「能力在变，模式不变」原则，把三次外部侦察提炼的工程纪律对号入座到既有模式，全部实机验证通过（改后跑 routing_check PASS + capability_probe OK + 反向引用核对 + 行为契约反测）。

- **skill-evolution v1.3.1 → v1.3.3**（借鉴 ifixai-ai/iFixAi 的 mandatory-minimum + N/A sentinel 处理）：
  - 「硬门禁判定纪律」— 反测结果三条不可违背门禁：N/A 与验证失败分离（仅能显式给 sentinel 才判 INCONCLUSIVE，其余 fail-closed）、横切技能条目强制门禁（evolution-gate/pattern-composition 不过则整体封顶）、分数封顶而非平均对消（PASS/FAIL 二值）。
  - 「变更后自动验证强制 hook」— 任何 skill 变更必跑 ① routing_check + capability_probe ② 反向引用 grep（横切技能引用非空 → 全量反测）③ 反测条目；缺项不结项。把验证从「自觉纪律」升级成「必然发生的 hook」。
- **cron-job-pattern v1.1.0 → v1.1.1**（借鉴 polydao 的 loop engineering）：
  - 新增「该不该自动化：频率×可逆性遴选」— 三条门槛（频率：每周重复 / 可验证：一分钟确认 / 可逆：错成本≈0），剧本反例：发消息/支付/发布/发邮件。三条都过才配谈三段式与幂等。
- **state-file-pattern v1.1.0 → v1.1.1**（借鉴 LunarResearcher 的 harness engineering）：
  - 新增「变更收据（Change Receipt）」— run 结束时收敛 state + evidence + unresolved risk 三件套，给人类审 + 给下次 session 起跑；evidence 必须是已落地产物句柄，接上 SKILL.state「显式状态优于对话历史」。

与既有资产关系：三处均为增量章节，未触碰既有行为契约；反测覆盖速查表已在 v1.04.00 的 test-prompts.json（30 条/19 模式）基础上。

## v2.2.0 (2026-09-05)

### ✨ Capability Sync: 四族新能力 + 真实验证案例

按 v2.1.0 的「能力在变，模式不变」原则，把 2026-09-05 前后系统里已实测可用的四族 Hermes 能力对号入座到既有模式。

- **hermes-capability-map 升级 v1.4.0** — 新增四个能力族章节：
  - 「十一、浏览器自动化」— browser_navigate/snapshot/click/type/scroll/vision/console/get_images + vision_analyze，落地调研兜底 / maker-checker UI 验证 / 前端审计
  - 「十二、消息网关」— `platforms.qqbot`（官方 QQ 机器人网关），落地 human-escalation 投递渠道 / secret-management / self-update
  - 「十三、多模态产出」— image_generate（qwen-image 文生图）+ text_to_speech，落地公众号/头条配图与内容分发
  - 「十四、能力验证（元能力）」— 新能力必须跑出可复现的真实输出作为证据锚点，反 hallucination
- **新增验证案例** `examples/capability-verification-2026-09.md` — 四族 9 项能力全部在真实环境实际调用跑通：
  - 浏览器：navigate 成功解析 example.com + console JS 求值 + vision 截图落盘（3/3）
  - 网关：config 授权 + `gateway run` 进程 PID 1058 常驻（2/2）
  - 多模态：qwen-image-3.0-pro 生成 1280×1280 落 `/mnt/g/hermes图片/` + edge TTS 生成 mp3（2/2）
  - 检索：hybrid_retrieve.py 三层（语义→混合→RRF）检索「如何防止上下文膨胀」得 16 hits、Top10 单调排序（16 hits）
- **补齐 examples/index.md** — mkdocs nav 引用了但文件缺失，本次补建。
- 维护规则新增：能力表新增族时，同步在 examples/ 补验证案例。

### 🧹 兼容性

- 无破坏性变更。hermes-capability-map v1.4.0 向后兼容 v1.3.0。

## v2.1.0 (2026-09-04)

### ✨ Pattern Expansion + Tooling Phase

#### Phase 1: 5 New Patterns (20 conventions total)
- **budget-guardrail.md** — 三级预算响应（预警/降级/熔断）防止 token/API 失控，与 cron-job-pattern/state-file-pattern 联动
- **human-escalation.md** — 高风险/低置信度/连续失败时升级到人工兜底，含状态机（running→escalated→confirm/reject）
- **multi-agent-isolation.md** — 命名空间隔离 + 文件锁 + 令牌桶，解决多 Agent 资源竞争
- **observability-trace.md** — 结构化决策追溯日志（决策/置信度/备选/证据），配套 trace-schema.json
- **data-retention-privacy.md** — 敏感信息检测（PII/密钥/API 响应）、保留期限、自动清理脚本

#### Phase 2: Pattern Linter (MVP)
- **scripts/lint.js** — 扫描 SKILL.md/STATE.md，三条规则：版本号缺失、STATE.md 缺失、敏感数据检测
- 支持 `--fix` 自动修复（补 frontmatter version/maturity 字段）
- `npx hpp-lint <path>` 或 `node scripts/lint.js <path>`
- 注册进 `package.json` bin + scripts

#### Phase 3: doctor CLI
- **scripts/doctor.py** — 交互式问答，5 个问题（任务类型/自主程度/风险等级/多 Agent/状态复杂度）
- 对照 pattern-composition 决策树自动推荐 pattern 列表（must/should/nice/reference）
- 输出 markdown 报告 + 安装命令，支持 `--auto` 非交互模式

#### Phase 4: Failure Case Library
- **examples/failures/** — 4 个真实失败案例复盘：
  - runaway-cron-tokens.md（Cron token 失控）
  - silent-data-corruption.md（数据静默损坏）
  - concurrent-state-conflict.md（多 Agent 状态冲突）
  - prompt-injection-escalation.md（注入导致越权）

#### Phase 5: Schema & Compatibility
- **conventions/pattern-schema.json** — Pattern frontmatter JSON Schema，linter 和文档共用同一份真理源
- **compatibility/matrix.md** — Pattern × Hermes 版本 × 依赖能力矩阵

#### Quality & Infrastructure
- test-prompts.json 从 25 条扩展到 30 条（覆盖 5 个新 pattern）
- pattern-composition.md 决策树新增「全自主 7x24 Agent」分支和 5 个新场景行
- README 核心概念表新增 5 个 pattern + 成熟度标注
- 回归测试 badge 更新为 30/30 Pass

## v2.0.0 (2026-08-31)

### 🚀 Productization Phase：从 Pattern Library 到 Production Engineering System

按 vault 路线图《Hermes_Production_Patterns_v2.0_产品化升级路线图》执行。核心战略转变：不再以增加 Pattern 数量为目标，而是 **MAKE PATTERNS USABLE**——先提升采用率，再扩展知识库。

- **Starter Kits（P0）** — `starter-kits/` 六个可复制骨架全部就位：basic-agent / cron-production / maker-checker / research-agent / memory-agent / self-evolving-agent。每个含 Patterns Used 表、安装、流程与验证清单；maker-checker 含 schema 契约 + red-flags + 压缩反馈模板 + 反测集；research-agent 含 evidence.jsonl 证据纪律 + 独立 Verifier；self-evolving-agent 含 Metrics/Baseline/Gate/Deploy/Rollback 全闭环。新增 `starter-kits/index.md` 选择路径表。
- **Production Stacks（P0）** — `stacks/` 五个官方组合：🟢 Starter / 🟡 Reliable Automation / 🔵 Quality / 🟣 Memory / 🔴 Evolution。每个含组合公式、对应公约、何时用、何时升级、落地方式；叠加原则对齐成熟度 L1-L3。
- **10-Minute Quick Start（P0）** — `quickstart.md`：六步从零到第一个 Production Agent（复制 kit → 定义技能 → 初始化状态 → 运行 → 独立验证 → 挂定时）。
- **Router 2.0（P0）** — docs Router 页新增 Problem→Diagnosis 表：7 类用户症状 → 诊断 → 推荐 Stack → 落地 kit 锚点。
- **Production Recipes（P1）** — `recipes/` 七个完整工程方案：daily-news-agent / content-pipeline / research-pipeline / autonomous-monitor / coding-agent-pipeline / knowledge-agent / multi-agent-workflow。每个九节齐全：Problem / Architecture / Patterns Used / Installation / Configuration / Run / Failure Modes / Recovery / Metrics。
- **Compatibility Matrix（P1）** — `compatibility/`：人读版 README + 机器可读 `hermes-versions.yaml`（13 个 pattern 的 min_hermes/status/requires）。
- **Production Audit（P1）** — `audit/`：审计规范（Pattern Evidence 哲学）+ 15 项行为检查单（五组 A-E）+ 五维加权 Readiness Score 模型（Reliability 25 / Observability 20 / Recoverability 20 / Quality 20 / Evolution 15）。
- **hpp CLI（P2）** — `cli/hpp.py`（纯 stdlib）：`hpp init` 六 kit 脚手架、`hpp add` 五 pattern 增量注入（幂等跳过）、`hpp validate` 结构/契约/密钥校验、`hpp audit` 五维打分条形图 + 缺失项 + 建议命令、`hpp doctor` 环境诊断。已在本地完成全命令实测。
- **网站重组** — mkdocs nav 改为 START HERE / BUILD / UNDERSTAND / VALIDATE / 项目说明 / 总览 / Examples / Templates / 参与贡献；build_docs.py 复制清单扩展至 stacks/recipes/audit/compatibility + 新增 starter-kits 生成页与 cli 页；首页 Hero CTA 改为 10-Minute Quick Start 优先。
- **清理** — 移除误生成的 `' /'` 目录与 stacks/ 空骨架。

## v1.06.00 (2026-08-30)

### ✨ 网站 V2:从文档站升级为 Agent Production Engineering 知识系统

按 V2 UI/UX 改版任务书执行(设计文档见 `.hermes/reports/website-v2/`):

- **首页 Landing 化**(§6-§8)— Hero「BUILD AGENTS THAT SURVIVE PRODUCTION.」+ 三 CTA + 可点击生产架构 SVG + 终端元素;Why Agents Fail 六问题卡;Problem→Pattern→Result 六链;成熟度时间线 L1-L3;Choose Your Path 三角色;案例 Case-Study 卡。构建期由 `build_docs.py` 从 frontmatter/正文派生,零硬编码内容(§36)。
- **统一深色工程终端风**(§14/§29)— 配色令牌 #080A0D/#78FFB7/#62D9FF 全套落地并桥接 Material 变量;取消浅色主题;分类 accent 走卡片左边框+kicker,禁高饱和整卡背景。
- **Pattern Explorer**(§25)— 新页 `/patterns-library/`:分类过滤 pills + 关键词搜索 + SHOWN 计数,4.2KB 无依赖 JS。
- **生产架构页**(§19-20)— 新页 `/architecture-page/`:Normal/Error 双流 + 组件职责表;retry→maker 回边正交布线。
- **Engineering Decision Layout**(§15-18)— 全部 15 个公约页注入分类 kicker、MATURITY/COMPLEXITY/RELIABILITY/HERMES/VERSION 信息栏、When(Not) ✓/✕ 双栏卡;数据源为新增 `hpp_*` frontmatter 键(可选,缺省安全,正文零改动)。
- **关系图谱升级**(§11)— 分类环排 + 弦式曲边 + 双环标签错位 + 中心品牌遮罩 + hover 高亮/关联弱高亮/键盘可达。
- **搜索**(§24)— ⌘K + placeholder「搜索 Patterns、问题、架构… (⌘K)」(zh locale 覆写)。
- **SEO**(§38)— `overrides/main.html` 补每页 OpenGraph/Twitter card;独立 title/description。
- **响应式**(§34)— 390px 实测零横向溢出;图在窄屏保持可读尺寸 + 横向滚动。
- **渐进增强红线** — 滚动淡入 1.5s 兜底强制可见,JS 失效不空洞;prefers-reduced-motion 全关。
- 旧首页(README)完整保留为 `/readme/`,零页面删除(§37);check-nav 43 页全挂 nav;markdownlint / strict build / 视觉五轮复检全 PASS。

## v1.05.01 (2026-08-30)

### ✨ 文档站吸收 Skill OS 理念:决策入口 + 模式图谱 + 契约卡 + nav 回归闸门

- **路由入口 Router**(`router.md`,构建自动生成)— 借鉴 Hermes Skill OS 路线图的 MASTER ROUTING 思想:从 15 个公约的 frontmatter `description` 提取「场景信号 → 入口公约 → 配套模式」决策表,新读者按问题找模式,不再靠翻目录。
- **模式图谱 Skill Graph**(`skill-graph.md`)— 从 `related_skills` 声明提取公约互链,构建期生成纯内联 SVG(零外部 CDN 依赖,规避 mermaid/unpkg 国内不可达问题),节点可点击进入对应公约。
- **Skill Contract 卡**— 每个公约页 H1 下自动注入折叠契约卡(版本/分类/相关模式),呼应路线图「Skill 从一段 Prompt 升级为可声明、可验证的能力模块」;数据源仍是 frontmatter,无新增维护负担。
- **check-nav 回归闸门**(`scripts/build_docs.py --check-nav`,已入 CI)— 呼应路线图 Regression 原则:任何 docs 页面未挂进 nav 或 nav 引用幽灵页面即构建失败,防止站点演化中的「孤儿页面」退化。
- 全部生成物仍由 `build_docs.py` 单点产出,`docs/`/`site/` 保持 gitignore;markdownlint 与 `mkdocs build --strict` 均零警告。

## v1.05.00 (2026-08-30)

### ✨ maker-checker v1.1.0 → v1.2.0:新增「红线优先」判决制(加功能,不需迁移)

- **实现要点第 6 条** — 借鉴 JIT-Agent(bingreeky/JIT, arXiv 2608.25593)评审团的 Architecture/Red-flag charter 思路:评分制之外允许预定义「命中即 FAIL」的 red flags,Checker 报告须写明检查了哪几条、是否命中;红线只从真实失败案例蒸馏,禁止凭想象堆砌。向后兼容:旧触发方式与五维评分流程不变。
- 评估过程:JIT 五专家 charter 对照自家体系做必要性/可行性评估(evolution-gate 的 G3/G4、routing_check、反测集已有对位物),仅 Architecture-Proportionality 一项是真缺口但落在 hermes-skill-os 侧;评审团/全套蒸馏方案因架构与任务不成比例被否。

## v1.04.01 (2026-08-29)

### 🔧 修正:全面体检发现的 6 处问题(修 bug 不改接口,按 skill-evolution 版本表升 patch)

- **frontmatter 缺失** — `conventions/data-driven-optimization.md` 补齐全套 YAML frontmatter(15 个 conventions 中唯一漏网,违反仓库自身模板约定)。
- **覆盖声明纠偏** — v1.04.00 的「覆盖全部 15 个模式」表述不准确:速查表实际覆盖 14 个行为契约技能,`hermes-capability-map` 是参考映射表、无行为契约可反测。README/skill-evolution 已改为「14 个行为契约模式 + capability-map 豁免」,速查表补注豁免行。
- **反测运行范围成文** — `skill-evolution` v1.3.0 → v1.3.1:把「升级跑映射条目、发版/tag 前跑全量、横切技能(evolution-gate/pattern-composition)变更跑全量、失败重跑一次再回滚」的口径写进章节(此前仅口头约定,本次源于社区问答沉淀)。
- **package.json 版本漂移** — 1.03.00 → 1.04.01(v1.04.00 发布时漏更)。
- **死链修复** — `examples/daily-news-digest/SKILL.md` 中 5 处 `../conventions/` 相对链接层级错误(应为 `../../conventions/`),本地链接检查器抓到、CI markdown-link-check 因 max-depth 配置未覆盖而漏报。
- **README.en.md 同步** — 补 v1.04.00/v1.04.01 发布说明与回归反测集介绍(中文版已有、英文版缺失)。

## v1.04.00 (2026-08-27)

### ✨ v1.04.00 新增:回归反测集(借鉴 dao-skill)

- **回归反测集** — `test-prompts.json`(仓库根,与 15 个技能平级):25 条回归提示词,每条含 `prompt / expected / assertions(应命中) / forbidden(禁止触犯)`,覆盖全部 15 个 production pattern 的核心行为契约(evolution-gate 走闸门、state-file Read Before Run、maker-checker 独立验证、secret-management 环境变量、cron 幂等防静默失败等)。反测集的定位 = 「技能升级的验收标准:旧失败不再出现、旧成功仍然成立」;结构检查 ≠ 行为反测,dry-run 不能当已验证(借鉴 dao-skill 的 E0-E4 证据分级思维)。
- **skill-evolution 升级 v1.3.0** — `conventions/skill-evolution.md`:新增「回归反测集」章节,定义何时跑(技能升级后 / 用户反馈"不对"时 / evolution-gate G5 回归对比)、怎么跑(prompt 喂 Agent → 检查 assertions 命中 + forbidden 未触)、新增条目规则(一个真实失败模式 → 一条反测,同根同触发合并防膨胀),并附 15 技能 → 25 条目反测覆盖速查表。
- **AGENTS.md 能力表** — 增加回归反测集入口。

## v1.03.00 (2026-08-20)

### ✨ v1.03.00 新增（3 个实战模式，来自 7x24 生产环境近期优化）

- **自更新安全流程** — `conventions/self-update-pattern.md`：把 `hermes update` 从「安装动作」变成「变更管理」。含 v0.20.4+ autostash 可能不自动恢复的坑（更新后查 `git stash list` → 手动 `stash apply` → modify/delete 冲突 `git rm`）、更新后测试失败基线（30524 测试/106 失败全量归因 → 区分上游失败 vs 本地回归）、回滚路径（git checkout）、STATE.md 更新记录模板。
- **Memory OS** — `conventions/memory-os-pattern.md`：五层记忆架构（Context/Working/Long/Experience/Evidence）、读侧三层检索 + RRF 融合（LanceDB 向量 + 知识图谱 + FTS5）、写侧 G4 数据闸（对账查重、证据校验、索引同步）、每日复盘循环（DailyReview cron）。明确 RAG ≠ Memory。
- **进化闸门** — `conventions/evolution-gate.md`：G1-G5 五道闸门（输入/运行时/质量/数据/进化）、五维加权评估（准确性 30% / 证据 25% / 完整 20% / 可靠 15% / 成本 10%）、G5 分档（≥85 promote / 55-84 improve / <55 failures）、回归测试 Deploy or Rollback、技能可度量化（usage_count/success_rate/average_score/cost/confidence）、落地工具 loopctl（11 子命令）。

### 📝 v1.03.00 改进

- **skill-evolution 升级 v1.2.0** — 新增「技能瘦身（Skill Slimming）」章节：description 前 57 字符截断规则、瘦身三原则（只留会用的 / 触发条件前置 / 约束而非教程）、2026-08-16 实战案例（头条写作技能只留硬约束）。
- **hermes-capability-map 升级 v1.1.0** — 新增「七、知识检索与记忆」族（he-knowledge MCP / index_vault / kg_extract / session_search / memory 双库 / 证据校验）与「八、生命周期与进化」族（loopctl / golden dataset / hermes update / git stash / 测试基线）。
- **pattern-composition 升级** — 决策树新增「系统阶段」分支（起步→cron→知识→优化），速查表新增 3 行（系统升级 / 知识沉淀 / 持续优化）。
- **README / README.en / AGENTS.md / CONTEXT.md** — 结构树、核心概念速查、能力表、术语表同步新增 3 个模式。

### 🧹 v1.03.00 兼容性

- 无破坏性变更。所有既有文件向后兼容；新增 3 个独立 convention，2 个升级文件仅追加章节与 frontmatter version 变更。

---
## v1.02.00 (2026-08-08)

### ✨ v1.02.00 新增

- **Hermes 能力 × 模式映射** — `conventions/hermes-capability-map.md` 新增：把 2026-08 前后的 Hermes 工具能力（cronjob monitor 族、delegate_task、session_search、execute_code、skill_manage 等）对号入座到既有模式。原则：能力在变，模式不变。
- **cron-job-pattern 升级 v1.1.0** — 新增「Hermes 原生 Monitor 模式」：`monitor_script`/`monitor_url`（哈希抑制，变了才烧 token）、`no_agent=True` Watchdog（零 token 告警）、`context_from` 链式、`enabled_toolsets`、`attach_to_session`、`workdir`，附场景选择矩阵。
- **maker-checker 升级 v1.1.0** — 新增「委托 Checker」选项：`delegate_task` 独立子代理 + `output_schema` 契约校验 + `live transcripts` 审计，与 Opik Judge 并列，附选择建议。
- **state-file-pattern 升级 v1.1.0** — 新增恢复手段：`session_search`（FTS5 跨会话检索）与 `memory`（batch operations 原子更新）作为 STATE.md 的补充。
- **skill-evolution 升级 v1.1.0** — 新增落地工具：`skill_manage`（patch/edit/delete/absorbed_into/write_file）对应技能生命周期各阶段。
- **secret-management 升级 v1.1.0** — 新增按需加载工具：`tool_search`/`tool_call` 延迟加载，工具面越窄凭据暴露面越小。

### 📝 v1.02.00 改进

- README / README.en 项目结构树与核心概念速查同步新增 hermes-capability-map 与 Monitor 模式引用。

### 🧹 v1.02.00 兼容性

- 无破坏性变更。所有 v1.0.x / v1.1.0 文件向后兼容；四个升级文件仅追加章节与 frontmatter version 变更。

---
## v1.01.03 (2026-07-29)

### ✨ v1.01.03 新增

- **数据驱动技能优化公约** — `conventions/data-driven-optimization.md` 新增将真实运营数据嵌入技能文件的方法论。包含正向约束（什么有效）、负向约束（什么无效）、战术约束（执行规则）三层结构，以及自动化反馈循环设计。
- **公众号文章流水线示例** — `examples/wechat-article-pipeline.md` 新增完整的公众号写作+AI检测+去AI味+配图生成+数据优化闭环示例。内置8维度AI味评分引擎(`scripts/ai_detect.py`)、Obsidian模板(`references/article-template.md`)，以及账号运营前4周的真实数据反馈验证。

### 📝 v1.01.03 改进

- **pattern-composition 决策树** — 新增 data-driven-optimization 节点的关联引用。

### 🧹 v1.01.03 清理

- 无破坏性变更。所有 v1.1.0 文件向后兼容。
- 移除仓库根目录下的过期 ChatGPT 图片。

### 📝 v1.01.03 项目健康检查

- **README 项目结构树** — 新增 `data-driven-optimization.md`、`wechat-article-pipeline.md`、`maturity-checklist.md` 引用。中英文同步更新。
- **AGENTS.md** — 新增 data-driven-optimization 和 wechat-article-pipeline 入口。
- **CONTEXT.md** — 更新最后修改时间戳。
- **ARCHITECTURE.md** — Maker 组件新增 draw.io CLI、data-driven-optimization 数据源引用。
- **Smoke test** — 新增 `examples/wechat-article-pipeline/test_example.py`，覆盖 clean text 和 AI-tainted text 两种场景。
- **CHANGELOG.md 重复标题** — MD024 修复。

---

## v1.1.0 (2026-07-26)

### ✨ 新增

- **Opik 自动化 Checker 模式** — `maker-checker` 公约新增 Opik LLM-as-a-Judge 作为自动化 Checker 选项，与手动 Checker 并列。支持五维评分映射到 Opik 指标（AnswerRelevance, ContextRelevance, Hallucination 等），阈值 ≥ 0.7。配套参考文档 `references/opik-as-checker.md`。
- **Graph 工作流集成** — `pattern-composition` 决策树新增 Graph 工作流分支，速查表和关系图新增 `checkpoint-pattern` + `graph-executor` 节点。`control-flow-separation` 新增 Graph 节点内 Code vs LLM 路由决策指南（R1→R5 逐节点）。
- **状态管理关联资产** — `state-file-pattern` 新增关联文件引用（`scripts/validate_state.py`, `scripts/atomic_state_write.py`, `conventions/state-schema.json`, `templates/STATE.md.template`）。

### 📝 改进

- **maker-checker-article-pipeline 示例** — 重写为双模式架构（手动 Checker / Opik Judge），成熟度分级更新为 L1→L2→L3 三档。
- **state-file-pattern 模板** — 内嵌模板改为引用 `templates/STATE.md.template`，减少文档冗余。
- **related_skills 更新** — 各 skill 跨引用关系补全，新增 `opik-eval`、`checkpoint-pattern`、`graph-executor` 关联。

### 🧹 清理

- 无破坏性变更。所有 v1.0.0 文件向后兼容。
