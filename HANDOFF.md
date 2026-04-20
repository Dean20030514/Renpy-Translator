# 交接笔记（第 37 轮结束 → 第 38 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 37 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**385 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 511 断言点）。第 37 轮打包 HANDOFF round 36→37 预规划的 **M 级防御加固包**（M1-M5）：**M1** `TranslationDB.load()` 去掉 `version < SCHEMA_VERSION` gate 让 partial v2 文件缺 `language` 字段的 entry 也 backfill（防 None 与 zh bucket 漂移）+ **M2** 4 处用户面 JSON loader 加 50 MB size cap（用户同意从 HANDOFF 原列 3 处扩到 4 处，含 `_apply_v2_edits`）防 OOM + **M3** `main.py` 多语言外循环 try/finally restore `args.target_lang` / `lang_config` + **M4** `_apply_v2_edits` 加 `Path.cwd().resolve()` path whitelist 防钓鱼 edits.json 劫持写系统文件 + **M5** 空串 cell = SKIP 语义文档化 + side-by-side label 加 tooltip。5 fix commit + 1 docs commit，每 bisect-safe；+7 regression 测试（M1 + M2×4 + M4 + M5；M3 因 mock 成本 > 收益 skip test）。默认路径 byte-identical；唯一的"操作体验变化"是 M4 后 v2_path 必须 CWD-rooted（production 场景本来就是）。

---

## 第 20 ~ 37 轮成果索引

详细记录见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md)。摘要：

| 轮 | 主题 | 测试数 |
|----|------|-------|
| 20 | CRITICAL：悬空 import × 3 + pickle RCE × 3 + ZIP Slip + 治理文档 | 266 → 268 |
| 21 | HIGH：HTTP 连接池 + ProgressTracker 双锁 + API Key subprocess env + 11 条 mock 测试 + P1 审查回刷 | 268 → 280 |
| 22 | 响应体 32 MB 硬上限 + T-C-3/T-H-2 集成测试基础 | 280 → 286 |
| 23 | direct.py 拆分 4 模块（1301 → 584） | 286 |
| 24 | tl_mode + tl_parser 拆分 7 模块（2034 → 1099） | 286 |
| 25 | 7 项 HIGH/MEDIUM 收敛 | 286 → 288 |
| 26 | 综合包（A+B+C）：TranslationDB 三件套 / RPA 大小预检查 / RPYC 白名单同步 / stages+gate 可见化 / screen.py 拆分 / quality_report 加锁 / patcher 反向索引 / RateLimiter 批量清理 / os.path → pathlib | 288 → 293 |
| 27 | 分层收尾：A-H-2 + A-H-5 | 293 |
| 28 | A-H-3 Minimal 路由统一 + S-H-4 Dual-mode 插件沙箱 + main.py `os` bug | 293 → 301 |
| 29 | Priority B 持续优化：test_all.py 拆分 + patch_font_now 路径修复 + 文档刷新 | 301 |
| 30 | 冷启动审计后的 4 项加固 + 文档深度刷新 | 301 → 302 |
| 31 | 从竞品 renpy_hook_template 学习：UI 白名单 / 占位符漂移修正 / strip_tags L5 fallback + inject_hook.rpy 模板 + `--emit-runtime-hook` opt-in CLI | 302 → 307 |
| 32 | round 31 续做全包（UI whitelist 可配置化 + 字体自动打包 + v2 多语言 schema）+ Commit 1 prep（font path helper + 2 处遗留 bug 修复） | 307 → 326 |
| 33 | round 32 延续三小项全包（v2 merge 工具 + `--font-config` runtime 透传 + editor v2 支持）+ Commit 4 prep（`test_translation_state.py` 拆出 `test_runtime_hook.py`）| 326 → 346 |
| 34 | round 33 延续三小项全包（TranslationDB language 字段 + editor 同页多语言 + override 分派表）+ Commit 1 prep `entry_language_filter` + Commit 3 prep 抽离 `_translation_editor_html.py` | 346 → 363 |
| 35 | round 34 延续三小项全包（同次多语言外循环 + editor side-by-side + `config_overrides`）+ Commit 1 prep ProgressTracker language namespace | 363 → 376 |
| 36 | 深度审计驱动的 2 个 edge-case bug 修复（H1 跨语言 bare-key 污染 + H2 inf/nan 过滤）；纯 fix 无新功能 | 376 → 378 |
| 37 | M 级防御加固包（M1 backfill 补漏 / M2 4 处 50 MB size cap / M3 main 循环 restore / M4 v2_path CWD 白名单 / M5 空串 cell 语义文档化 + tooltip）| 378 → 385 |

---

## 运行时注入模式全能力（截至 round 37）

**何时用**：当静态 `.rpy` 改写不可行时（游戏发布方不允许分发修改后的源文件 / 想保留原始游戏完整性 / 需要给用户"一个补丁包"而非"一个修改版游戏"）。

**启用方式**（所有 opt-in）：
```bash
# 基础：生成 translations.json + zz_tl_inject_hook.rpy
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --emit-runtime-hook

# 扩展：UI 白名单 + v2 多语言 + 字体打包 + gui 字号/布局 override
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --emit-runtime-hook \
    --ui-button-whitelist custom_ui.txt extra_ui.json \
    --runtime-hook-schema v2 \
    --target-lang zh \
    --font-file /path/to/CustomFont.ttf \
    --font-config /path/to/font_config.json    # round 33 新：含 gui_overrides

# 多语言合并（round 33 新工具）：分别运行 zh / zh-tw / ja，再 merge
python tools/merge_translations_v2.py zh.json zh-tw.json ja.json \
    -o merged_translations.json --default-lang zh

# 使用时把生成的文件拖到游戏 game/ 目录，然后设置环境变量启动：
RENPY_TL_INJECT=1 ./game.exe
# v2 schema 下还可以指定运行时语言：
RENPY_TL_INJECT=1 RENPY_TL_INJECT_LANG=zh-tw ./game.exe

# 交互式 review v2 文件（round 33 新：editor v2 支持）：
# round 37 M4: CWD 必须是 v2 envelope 所在目录或祖先。
python -m tools.translation_editor --export --db merged_translations.json \
    --v2-lang zh -o review_zh.html    # 编辑 zh bucket
python -m tools.translation_editor --export --db merged_translations.json \
    --v2-lang ja -o review_ja.html    # 再编辑 ja bucket
python -m tools.translation_editor --import-json translation_edits.json
```

**生成的文件清单**：
- `translations.json` — flat v1 或嵌套 v2 envelope
- `zz_tl_inject_hook.rpy` — 主 hook 脚本（init python early）
- `zz_tl_inject_gui.rpy` — 可选，gui override aux 脚本（init 999），round 33 新增
- `ui_button_whitelist.json` — 可选，sidecar，round 32 新增
- `fonts/tl_inject.ttf` — 可选，字体 bundle，round 32 新增

**不启用 `--emit-runtime-hook` 时**：完全与 round 30 之前一样，静态改写流程一字不差。所有 round 32-37 新增 flag 全部 opt-in，default 零行为变化。

---

## 推荐的第 38+ 轮工作项

HANDOFF round 36→37 预规划的 M 级防御加固包（M1-M5）已于 round 37 闭环。
Priority A + B 持续清零 9 轮；项目仍处于 steady-state。**r38 主要候选**：
`tests/test_translation_editor.py` 拆分（r37 越软限 47 行）/ 其他 JSON loader
size cap 扩展（r37 只做 4 处）/ pre-existing 4 大文件拆分 / r35 绿色小项。

### 🟡 即刻小项（r37 直接抛出的债）

**(1) 拆 `tests/test_translation_editor.py`**：r37 加 M4 + M5 两个 test +
3 处 `tempfile.TemporaryDirectory(dir=str(Path.cwd()))` 调整后文件 847 行
（751 → 847，+96 行），越 800 软限 47 行。建议参 r33 Commit 4 prep 模式
拆出新 `test_translation_editor_v2.py`（把 v2 相关的 8 个测试移过去 —
test_extract_from_v2_envelope / test_import_to_v2_envelope /
test_v2_envelope_preserves_non_edited_languages / test_extract_from_v2_
exposes_full_languages_dict / test_v2_html_includes_language_switch_
dropdown / test_export_edits_multi_language_produces_per_lang_records /
test_apply_v2_edits_rejects_path_outside_cwd / test_side_by_side_label_
has_empty_string_hint_tooltip）。~400 行移出，主文件回到 ~450。纯结构
refactor，零行为变化，~1h 含测试验证。

**(2) 其他 JSON loader size cap 扩展**：r37 M2 只覆盖 4 处；另外
`core/config.py:105` / `core/glossary.py:119,139,211,231`（4 处）/
`pipeline/stages.py:212,378`（2 处）/ `pipeline/gate.py:116` /
`engines/rpgmaker_engine.py:85,396`（2 处）/ `engines/generic_pipeline.
py:151` / `core/translation_utils.py:138` / `translators/_screen_patch.
py:311` / `tools/analyze_writeback_failures.py:36` / `tools/review_
generator.py:35` / `tools/rpyc_decompiler.py:437` / `tools/translation_
editor.py:111,289` 共约 16 处仍无 size cap。大部分是内部 progress / DB /
report 读取，OOM 风险较低（文件由我们自己产）；但 `core/config.py` /
`core/glossary.py` / `translation_editor.py:289` 读用户供的 path，风险
偏高。~50 行扩展 + 3-4 个测试。建议与"拆 test_translation_editor.py"
合为 r38 轻量一轮。

### 🟢 延续 round 35 方向（r35-36-37 连续挂起的绿色小项）

r35 HANDOFF 挂起的 3 项，r36 被 H1/H2 审计优先级让行，r37 被 M 级防御
让行，现在仍可做：

**(1) tl-mode / retranslate 的 per-language prompt**：当前两个模式的
system prompt（`core/prompts.py::TLMODE_SYSTEM_PROMPT` +
`RETRANSLATE_SYSTEM_PROMPT`）硬编码中文输出 `"zh"` 字段。r35 加的
multi-lang guard 拒 `--tl-mode --target-lang ja`；下一步是真实支持两
个模板改用 `{target_language}` / `{field}` 占位符 + `tl_mode.py:92` /
`retranslator.py:284` 读 response 用 `target_lang` 字段 fallback `zh`。
~3-4h 含非中文 target 的端到端测试。

**(2) `config_overrides` 值类型扩 bool**：r35 `_sanitise_overrides`
仍只认 int/float；`config.autosave = True` / `config.developer = False`
这类常见 bool config 被 warning + drop。扩展时要 per-category 控制
（不是所有 category 都适合 bool —— `gui.text_size = True` 还是 drop）。
~1-2h。

**(3) editor side-by-side N>3 移动端适配**：r35 CSS `.col-trans-multi
{ width: 13% }` 写死；6 语言时每列 < 100px 在 mobile viewport 拥挤。加
`@media (max-width: 800px)` 自动回 dropdown 模式或 horizontal-scroll。
~1-2h 纯 CSS + 小 JS。

### 🟠 延续未做的深度重构

**A-H-3 Medium / Deep**：当前 A-H-3 只做 Minimal（入口统一）。Medium
（adapter 层，让 Ren'Py 走 generic_pipeline 6 阶段）或 Deep（完全退役
DialogueEntry）。需真实 API + 真实游戏验证。

**S-H-4 Breaking**：强制所有插件走 subprocess，retire importlib 路径。
目前 dual-mode 已经稳定。

### 🟡 新功能 / 扩展（Priority C）

- RPG Maker Plugin Commands / JS 硬编码支持
- 加密 RPA / RGSS 归档
- CSV/JSONL engine 完善

### 🔴 监控项（暂不修）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 理论链式攻击
- HTTP 响应体 64 KB 精度偏差

### ⚫ 外部基础设施 / Pre-existing 技术债

- **Pre-existing > 800 行源文件拆分**（r31-37 未触碰）：`tools/rpyc_
  decompiler.py` 974 / `core/api_client.py` 965 / `tests/test_engines.py`
  962 / `gui.py` 815。建议独立一轮参 r17 / r29 / r32 / r33 的拆分
  precedent。
- CI Windows runner
- docs/constants.md / docs/quality_chain.md / docs/roadmap.md 深度复查
  （连续 8 轮被提及未做）

---

## 架构健康度总览（第 37 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ⚠️ 源码侧清零；**r37 加测试后 `tests/test_translation_editor.py` 847 行越软限 47 行** → r38 拆分；pre-existing 4 个文件未动（`rpyc_decompiler.py` 974 / `api_client.py` 965 / `tests/test_engines.py` 962 / `gui.py` 815）| round 37 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + 接受 line=0；round 34 升 schema v2 加 `language` 字段；**round 37 M1 修 v2 partial backfill 漏洞** | round 37 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 | round 20/26 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in + 10 KB stderr 上限 | round 28/30 |
| 运行时注入 | ✅ `--emit-runtime-hook` 全套 r31-36 + **r37 `_apply_v2_edits` 加 50 MB size cap（M2 4/4 处）+ CWD path whitelist（M4）+ 空串 cell 语义文档化（M5）** | round 37 |
| 多语言数据模型 | ✅ `TranslationDB._index` 4-tuple + `ProgressTracker` language namespace（r35/r36）+ **r37 M1 `load()` 覆盖 partial v2 backfill** | round 37 |
| 多语言翻译调度 | ✅ `main.py::_parse_target_langs` 解析 `--target-lang zh,ja,zh-tw` → 外层 `engine.run` 循环 + **r37 M3 try/finally restore `args.target_lang` 防 post-loop 残留** | round 37 |
| 字体路径解析 | ✅ 全部走 `core.font_patch.default_resources_fonts_dir()` canonical helper；**r37 M2 `load_font_config` 加 50 MB cap** | round 37 |
| 生成代码注入防护 | ✅ `_OVERRIDE_CATEGORIES` 分派表 + 正则白名单 + int/float 白名单（round 33-35）+ r36 H2 inf/nan 过滤 | round 36 |
| **内存 OOM 防护**（新维度） | ✅ **r37 M2 4 处用户面 JSON loader 50 MB size cap**：`core/font_patch.load_font_config` / `core/translation_db.load` / `tools/merge_translations_v2._load_v2_envelope` / `tools/translation_editor._apply_v2_edits`。还有 ~16 处内部 / 低风险 loader 未覆盖（r38 候选） | round 37 |
| **路径信任边界**（新维度） | ✅ **r37 M4 `_apply_v2_edits` 加 CWD 路径白名单**（拒 `/etc/passwd` 等系统路径；预先存在的 v2-apply 测试已改 `tempfile(dir=str(Path.cwd()))` 配合）| round 37 |
| 潜伏 bug | ✅ 清零（round 28/29/30/32 / r36 H1/H2 / **r37 M1 partial v2 backfill 漏洞**）| round 37 |
| 测试覆盖 | ✅ **385 自动化** + tl_parser 75 + screen 51 = **511 断言点**；17 测试套件 | round 37 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 37 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 35/36/37 轮详细 + 第 1-34 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（统一 `engine.run()` 分派 + **r37 M3 外循环 args restore**）/ `one_click_pipeline.py` / `gui.py` / `start_launcher.py` |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py` |
| 运行时注入 | `core/runtime_hook_emitter.py`（r31 基础 + r32 UI sidecar / 字体 bundle / v2 schema + r33 gui_overrides aux rpy + r36 H2 isfinite 过滤）+ `resources/hooks/inject_hook.rpy`（r31 基础 + r32 sidecar reader + v2 reader + env var 语言选择）+ `resources/hooks/extract_hook.rpy`（已有） |
| v2 工具链 | `tools/merge_translations_v2.py`（r33 multi-lang 合并 + **r37 M2 50 MB size cap**）+ `tools/translation_editor.py`（r33 `--v2-lang` bucket 编辑 + r34 dropdown + **r37 M2 `_apply_v2_edits` 50 MB cap + M4 CWD path whitelist + M5 空串 cell 语义 docstring**） |
| 字体补丁 | `core/font_patch.py::default_resources_fonts_dir`（r32 canonical 出口）+ `resolve_font` + `apply_font_patch` + `load_font_config`（**r37 M2 `_MAX_FONT_CONFIG_SIZE` 50 MB cap**） |
| UI 白名单 | `file_processor/checker.py::COMMON_UI_BUTTONS`（baseline）+ `_ui_button_extensions` + `load_ui_button_whitelist`（r32） |
| 插件沙箱 | `core/api_client._SubprocessPluginClient`（S-H-4）+ `custom_engines/example_echo.py::_plugin_serve` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py`（checker 含 r27 下沉 + r31/r32 新增） |
| 测试 | `tests/test_all.py`（meta，6 模块）+ 独立套件（test_engines / smoke_test / test_rpa_unpacker / test_rpyc_decompiler / test_lint_fixer / test_tl_dedup / test_batch1 / test_custom_engine / test_direct_pipeline / test_tl_pipeline / test_translation_editor / test_merge_translations_v2 / test_runtime_hook_filter / test_translation_db_language / test_multilang_run） |
| Round 34/35 关键增量 | `core/translation_db.py` schema v2 + `language` 字段 + 4-tuple 索引（r34）/ `core/translation_utils.py::ProgressTracker` language namespace + r36 H1 `_LEGACY_BARE_LANG` 守卫 / `main.py::_parse_target_langs` + 外循环（r35）/ `tools/_translation_editor_html.py` side-by-side + dropdown（r34-35）/ `core/runtime_hook_emitter.py::_OVERRIDE_CATEGORIES` + r36 H2 isfinite |
| **Round 37 关键增量** | `core/translation_db.py::load()` M1 去 version gate + `_MAX_DB_FILE_SIZE` M2 50 MB cap / `core/font_patch.py::_MAX_FONT_CONFIG_SIZE` M2 / `tools/merge_translations_v2.py::_MAX_V2_ENVELOPE_SIZE` M2 / `tools/translation_editor.py::_MAX_V2_APPLY_SIZE` M2 + M4 `_apply_v2_edits` trust_root + CWD whitelist + M5 empty-cell skip docstring / `main.py` M3 外循环 try/finally restore / `tools/_translation_editor_html.py` M5 side-by-side label title tooltip / **测试**（tests/test_translation_db_language.py +2 / test_merge_translations_v2.py +1 / test_runtime_hook_filter.py +2 / test_translation_editor.py +2 + 3 处 tempdir dir=cwd 调整）|

---

## 🔍 Round 31-37 审计状态

用户在 r35 末要求"深度检查第 31-35 轮"的专项审查成果：**r36 修 H1+H2；
r37 修 M1-M5**。

### ✅ 已修（round 36-37 commit 记录）

**r36**：H1 `ProgressTracker` 跨语言 bare-key 污染 + H2 `_sanitise_overrides`
拒 inf/nan（详见 r36 HANDOFF 或 `git log --grep="round-36"`）。

**r37**：M 级防御加固包（commits `5d8e53a` M1 / `e848598` M2 / `34f1e0c`
M3 / `50ecb68` M4 / `0932a04` M5 / `<docs>` sync）:

- **M1 — `TranslationDB.load()` 覆盖 partial v2 backfill**：r34 的
  forced backfill 只在 `version < SCHEMA_VERSION` 分支触发；手编 v2 DB
  缺 language 字段的 entry 永远留在 None bucket。r37 去 version gate，
  任意 `default_language` 非空时遍历 entries 回填；`any_backfilled`
  flag 防 already-complete v2 文件被误标 dirty。+1 test。
- **M2 — 4 处 JSON loader 50 MB size cap**：用户同意扩展到 4 处
  （HANDOFF 原列 3 处 + `_apply_v2_edits`）。每处加 module-level 常量
  `_MAX_*_SIZE = 50 * 1024 * 1024` + 读前 `path.stat().st_size` 检查，
  oversize → 每个 site 的自然 no-op（`{}` / empty state / `MergeError` /
  skip edits）。+4 tests 全用 51 MB sparse file 触发 size gate。
- **M3 — `main.py` 外循环 args restore**：loop 前 `_saved_target_lang`
  / `_saved_lang_config = args.*`；try/finally 包 for 循环，finally
  restore。+0 test（mock `main()` 成本 > 收益，per "最小改动"）。
- **M4 — `_apply_v2_edits` CWD path whitelist**：函数顶部算
  `trust_root = Path.cwd().resolve()`；for-loop 遍历 edit 时 `Path(v2_
  path).resolve().relative_to(trust_root)` 失败 → warning + skip。+1
  test；3 个 pre-existing v2-apply 测试改 `tempfile(dir=str(Path.cwd()))`。
- **M5 — 空串 cell SKIP 语义文档化 + tooltip**：`_apply_v2_edits`
  docstring +1 段 + `_translation_editor_html.py` side-by-side label
  加 `title` tooltip。+1 test（HTML_TEMPLATE 常量断言）。

### 🟡 未修（r38+ 候选）

- `tests/test_translation_editor.py` 847 行越 800 软限（r37 加测试后）
  — 建议 r38 拆分参 r33 precedent
- 其他 JSON loader size cap 扩展（M2 未覆盖的 ~16 处，大部分内部低风险）
- r35 原候选绿色小项：tl-mode per-lang prompt / config_overrides bool /
  editor mobile
- Pre-existing 4 个源文件 > 800 行（`tools/rpyc_decompiler.py` /
  `core/api_client.py` / `tests/test_engines.py` / `gui.py`）
- A-H-3 Medium/Deep / S-H-4 Breaking / RPG Maker plugin commands / CI /
  docs 复查

### ❌ 审计 Agent 历史误判（防再误）

r36 HANDOFF 的"经核实不准确的指控"列表保留作历史参考：Agent 2 的测试数
虚报 / orphan 测试误判；Agent 3 的 `_apply_v2_edits` path traversal 过
度升级（LOW-MEDIUM，r37 M4 落地修复）/ regex DoS 夸大 / XSS in banner
innerHTML 误判。

---

## 📋 Round 38 建议执行顺序

**短平快小项（合为一轮"收尾包"建议）**：
1. 拆 `tests/test_translation_editor.py`（v2 相关测试 → 新 `test_
   translation_editor_v2.py`），主文件回到 < 800 行 — ~1h
2. M2 size cap 扩展到 `core/config.py` / `core/glossary.py` /
   `translation_editor.py:289` 等用户面 loader — ~2h
3. r35 的 `config_overrides` 值类型扩 bool — ~1h
4. r35 的 editor side-by-side mobile 自适应 — ~1h

合计 ~5h，一轮可清。

**中项（独立一轮）**：
5. tl-mode / retranslate per-language prompt — ~3-4h 含端到端

**大项（独立一轮）**：
6. 拆分 4 个 pre-existing > 800 行源文件（`rpyc_decompiler.py` /
   `api_client.py` / `test_engines.py` / `gui.py`）

---

## ✅ 整体质量评估（r37 末）

- **r35 挂起 M 级加固**：✅ 清零（M1-M5 全修 + 7 regression 测试）
- **向后兼容**：✅ 所有 default path byte-identical；唯一观察到的行为
  变化点是 M4 对非 CWD-rooted 的 v2_path 改判为 skip（production 场景
  下 v2 文件本来就在 `<project>/output/`）
- **测试覆盖**：✅ +7 regression 测试直接反映审计 reproducer；1 个新维度
  "内存 OOM 防护" 进架构健康度表
- **新功能 correctness**：N/A（r37 纯 fix + 防御性加固）
- **文档同步**：✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG 均现行
- **已知负债**：⚠️ `tests/test_translation_editor.py` 847 行越 800 软限
  47 行（r37 加测试产生），明文标注在 r38 候选第一项

**R31-37 七轮累积**：2 个 H-level bug + 5 个 M-level 加固清零；5 绿色
小项闭环；多语言完整栈（DB schema v2 + ProgressTracker language
namespace + main.py 外循环 + editor side-by-side + runtime hook 泛化
分派表 + 内存/路径信任加固）。主流程稳定；r38 候选主要是收尾债
（test_translation_editor.py 拆 + 剩余 size cap 扩 + r35 绿色小项）+
pre-existing 大文件拆分。

---

**本文件由第 37 轮末尾生成，作为第 38 轮起点。**
**下次对话：直接读 `HANDOFF.md` 这一 section，决定 round 38 打"收尾包"
（拆 test_editor + 其他 size cap + r35 绿色小项）/ tl-mode per-lang prompt
独立一轮 / 拆 pre-existing 大文件独立一轮。**
