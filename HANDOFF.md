# 交接笔记（第 36 轮结束 → 第 37 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 36 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**378 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 504 断言点）。第 36 轮修复 HANDOFF round 35 深度审计定位的 2 个已复现 edge-case bug：**H1** `ProgressTracker` 跨语言 bare-key 污染（非 zh 的 language-aware tracker 不再读/写 bare bucket；新增 class 常量 `_LEGACY_BARE_LANG = "zh"` 标注 pre-r35 implicit owner + `mark_file_done` 镜像守卫防非 zh 清 bare 数据）+ **H2** `_sanitise_overrides` 加 `math.isfinite` 过滤拒收 `float('inf')/'-inf'/'nan'`（防 `repr(inf)='inf'` 写入 `init python:` block 导致 Ren'Py 启动 NameError；攻击面：不可信 `font_config.json` 通过 `json.loads` 接受 `Infinity`/`NaN` 偷渡）。两处修复独立 commit + 2 新 regression 测试（`test_progress_tracker_language_switch_does_not_leak_across_langs` 在 `test_translation_state.py`，`test_sanitise_overrides_rejects_non_finite_floats` 在 `test_runtime_hook_filter.py`）。无新功能，默认路径 byte-identical round-35，非 zh language-aware 调用是**唯一行为改变点**（之前错误继承 zh bare 数据，现在正确隔离）。

---

## 第 20 ~ 36 轮成果索引

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

---

## 运行时注入模式全能力（截至 round 36）

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

**不启用 `--emit-runtime-hook` 时**：完全与 round 30 之前一样，静态改写流程一字不差。所有 round 32-36 新增 flag 全部 opt-in，default 零行为变化。

---

## 推荐的第 37+ 轮工作项

HANDOFF round 35 深度审计定位的 H1 + H2 已于 round 36 修复。Priority A + B 清零持续 8 轮；项目仍处于 steady-state。审计报的 **M1-M5 防御性加固** + **pre-existing 4 个 > 800 行文件拆分** + r35 / r36 未做的 **绿色小项**三条战线仍开。

### 🟡 Medium 风险 — 审计挂起的防御性加固（建议 r37 打包一轮"防御包"）

| # | 位置 | 问题 | 触发条件 | 工作量 |
|---|------|------|---------|--------|
| M1 | `core/translation_db.py::load()` | v2 schema + 部分 entries 缺 language 字段时 backfill 被跳过 | 只在手工编辑 DB JSON 时出现（hypothetical）| 扩 backfill 条件，~3 行 + 1 测试 |
| M2 | `core/font_patch.py:91` / `core/translation_db.py:132` / `tools/merge_translations_v2.py:64` | 3 处 JSON loader 无文件大小上限 | 用户自供巨大 JSON 导致 OOM | 加 50MB cap，~5 行 × 3 处 |
| M3 | `main.py:342-353` 外循环 | 循环末尾 `args.target_lang` 停在最后语言（不是第一个）| 无实际 reader，但未来扩展易踩 | 用局部变量替代 args 修改，~3 行 |
| M4 | `tools/translation_editor.py::_apply_v2_edits:431` | `v2_path` 字段无路径白名单 | 用户从不可信源拿 edits.json | 加 path-prefix 校验，~10 行 |
| M5 | `tools/_translation_editor_html.py` + `_apply_v2_edits` | side-by-side 编辑为空串的语义歧义（JS 跳过 vs Python 跳过的一致性） | 用户主动清空某语言 cell | 文档化 + 小 UI 提示，~5 行 |

合计 ~36 行改动 + 2 新测试。一轮打包推荐。

### 🟢 延续 round 35 方向（绿色小项）

r35 HANDOFF 挂起的 3 项（被 r36 的审计驱动优先级让行，未做）：

**(1) tl-mode / retranslate 的 per-language prompt**：当前两个模式的 system prompt（`core/prompts.py::TLMODE_SYSTEM_PROMPT` + `RETRANSLATE_SYSTEM_PROMPT`）硬编码"翻译为简体中文 + `zh` 字段"。r35 加了 multi-lang guard 让 `--tl-mode --target-lang ja` 报错；下一步是真实支持：两个模板改用 `{target_language}` / `{field}` 占位符（参考 direct-mode 已有的 lang_config 处理方式）+ `tl_mode.py:92` / `retranslator.py:284` 读 response 用 `target_lang` 字段 fallback `zh`。~3-4h 含非中文 target 的端到端测试。

**(2) `config_overrides` 值类型扩 bool**：r35 `_sanitise_overrides` 仍只认 int/float；`config.autosave = True` / `config.developer = False` 这类常见 bool config 被 warning + drop。扩展时要 per-category 控制（不是所有 category 都适合 bool —— `gui.text_size = True` 还是 drop）。~1-2h。

**(3) editor side-by-side N>3 移动端适配**：r35 CSS `.col-trans-multi { width: 13% }` 写死；6 语言时每列 < 100px 在 mobile viewport 拥挤。加 `@media (max-width: 800px)` 自动回 dropdown 模式或 horizontal-scroll。~1-2h 纯 CSS + 小 JS。

### 🟠 延续未做的深度重构

**A-H-3 Medium / Deep**：当前 A-H-3 只做 Minimal（入口统一）。Medium（adapter 层，让 Ren'Py 走 generic_pipeline 6 阶段）或 Deep（完全退役 DialogueEntry）。需真实 API + 真实游戏验证。

**S-H-4 Breaking**：强制所有插件走 subprocess，retire importlib 路径。目前 dual-mode 已经稳定。

### 🟡 新功能 / 扩展（Priority C）

- RPG Maker Plugin Commands / JS 硬编码支持
- 加密 RPA / RGSS 归档
- CSV/JSONL engine 完善

### 🔴 监控项（暂不修）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 理论链式攻击
- HTTP 响应体 64 KB 精度偏差

### ⚫ 外部基础设施 / Pre-existing 技术债

- **Pre-existing > 800 行文件拆分**（r31-36 未触碰）：`tools/rpyc_decompiler.py` 974 / `core/api_client.py` 965 / `tests/test_engines.py` 962 / `gui.py` 815。建议独立一轮参 r17 / r29 / r32 的拆分 precedent（约定 800 是软上限，但这 4 个文件历史形成未清）。
- CI Windows runner
- docs/constants.md / docs/quality_chain.md / docs/roadmap.md 深度复查（连续 7 轮被提及未做）

---

## 架构健康度总览（第 36 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ⚠️ 源码侧清零（最大 `core/runtime_hook_emitter.py` 661；`translation_utils.py` 547；`translation_editor.py` 555；`direct.py` 604；`checker.py` 约 615；`inject_hook.rpy` 约 345；`tests/test_translation_state.py` 799 / `test_runtime_hook.py` 794 / `test_translation_editor.py` 751 均 < 800）；**但 pre-existing 4 个大文件未动**（`rpyc_decompiler.py` 974 / `api_client.py` 965 / `tests/test_engines.py` 962 / `gui.py` 815）| round 36 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + 接受 line=0；round 34 升 schema v2 加 `language` 字段保持向后兼容（v1 文件无 default_language 时行为 byte-identical） | round 34 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 | round 20/26 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in + 10 KB stderr 上限 | round 28/30 |
| 运行时注入 | ✅ `--emit-runtime-hook` 基础（r31）+ UI whitelist sidecar / 字体 bundle / v2 多语言 schema（r32）+ gui_overrides 透传 / v2 merge 工具 / editor v2 编辑（r33）+ editor 同页多语言 / `entry_language_filter` 防 bucket 污染 / override 分派表（r34）+ `config_overrides` 注册 / side-by-side UI（r35）+ **H2 inf/nan 过滤守护 `_sanitise_overrides`（r36）** | round 36 |
| 多语言数据模型 | ✅ `TranslationDB._index` 4-tuple + `ProgressTracker` language namespace（round 35 `"<lang>:<rel_path>"` key + **round 36 H1 非 zh language-aware tracker 禁止 bare fallback + mark_file_done 镜像守卫**）；`upsert` / `has_entry` / `filter_by_status` / `mark_chunk_done` 均 language-aware；v1→v2 `load()` 强制回填 | round 36 |
| 多语言翻译调度 | ✅ `main.py::_parse_target_langs` 解析 `--target-lang zh,ja,zh-tw` → 外层 `engine.run` 循环；`--tl-mode` / `--retranslate` + 多语言 guard 报错（两个 prompt 中文专用） | round 35 |
| 字体路径解析 | ✅ 全部走 `core.font_patch.default_resources_fonts_dir()` canonical helper，2 处遗留 bug 已修 | round 32 |
| 生成代码注入防护 | ✅ `zz_tl_inject_gui.rpy` 生成走 `_OVERRIDE_CATEGORIES` 分派表 + `_SAFE_GUI_KEY` / `_SAFE_CONFIG_KEY` 正则 + `int`/`float` 白名单（拒 bool/str/list/dict/None）；round 35 新增 `config_overrides` 注册，style_overrides 仍刻意排除；**round 36 加 `math.isfinite` 过滤拒 inf/-inf/nan** | round 36 |
| 潜伏 bug | ✅ 清零（round 28/29/30/32 陆续扫清 + **round 36 修清 r35 引入的 2 个 edge case：H1 跨语言 bare-key 污染 + H2 inf/nan runtime hook 注入**）| round 36 |
| 测试覆盖 | ✅ **378 自动化** + tl_parser 75 + screen 51 = **504 断言点**；17 测试套件 | round 36 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 36 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 34/35/36 轮详细 + 第 1-33 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（统一 `engine.run()` 分派）/ `one_click_pipeline.py` / `gui.py` / `start_launcher.py` |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py` |
| 运行时注入 | `core/runtime_hook_emitter.py`（r31 基础 + r32 UI sidecar / 字体 bundle / v2 schema + r33 gui_overrides aux rpy + **r36 H2 isfinite 过滤**）+ `resources/hooks/inject_hook.rpy`（r31 基础 + r32 sidecar reader + v2 reader + env var 语言选择）+ `resources/hooks/extract_hook.rpy`（已有） |
| v2 工具链（round 33） | `tools/merge_translations_v2.py`（multi-lang 合并）+ `tools/translation_editor.py`（`--v2-lang` bucket 编辑） |
| 字体补丁 | `core/font_patch.py::default_resources_fonts_dir`（r32 canonical 出口）+ `resolve_font` + `apply_font_patch` + `load_font_config`（r13，r33 跨模式复用） |
| UI 白名单 | `file_processor/checker.py::COMMON_UI_BUTTONS`（baseline）+ `_ui_button_extensions` + `load_ui_button_whitelist`（r32） |
| 插件沙箱 | `core/api_client._SubprocessPluginClient`（S-H-4）+ `custom_engines/example_echo.py::_plugin_serve` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py`（checker 含 round 27 下沉 + round 31 / 32 新增） |
| 测试 | `tests/test_all.py`（meta，6 模块）+ 6 个拆分（test_api_client / test_file_processor / test_translators / test_glossary_prompts_config / test_translation_state / test_runtime_hook r33）+ 11 个独立套件（test_engines / smoke_test / test_rpa_unpacker / test_rpyc_decompiler / test_lint_fixer / test_tl_dedup / test_batch1 / test_custom_engine / test_direct_pipeline / test_tl_pipeline / test_translation_editor / test_merge_translations_v2 r33 / **test_runtime_hook_filter** r34 新 + **r36 扩 H2 safety test** / **test_translation_db_language** r34 新 / test_multilang_run r35 新） |
| Round 34 关键增量 | `core/translation_db.py` schema v2 + `language` 字段 + `default_language` 构造 kwarg / `engines/generic_pipeline.py` resume index 3-tuple + language-aware / `tools/_translation_editor_html.py` HTML/JS 模板（368 行）/ `tools/translation_editor.py::switchV2Language` 同页切换 JS / `core/runtime_hook_emitter.py::_OVERRIDE_CATEGORIES` 分派表 |
| Round 35 关键增量 | `core/translation_utils.py::ProgressTracker` `language` kwarg + `_key()` namespace / `main.py::_parse_target_langs` + `--target-lang zh,ja` 外循环 + tl/retranslate guard / `tools/_translation_editor_html.py` `toggleSideBySide` + `_bindSideBySideCellEvents` + `.col-trans-multi` CSS / `core/runtime_hook_emitter.py::_SAFE_CONFIG_KEY` + `config_overrides` 注册 / `tests/test_multilang_run.py` 新独立 suite |
| **Round 36 关键增量** | `core/translation_utils.py::ProgressTracker._LEGACY_BARE_LANG` 常量 + 4 方法 gate（`is_file_done` / `is_chunk_done` / `get_file_translations` / `mark_file_done` 的 bare-key 访问语义：非 zh language-aware tracker 完全不读/不写 bare bucket）/ `core/runtime_hook_emitter.py::_sanitise_overrides` 加 `math.isfinite` 过滤 + 顶部 `import math` / `tests/test_translation_state.py::test_progress_tracker_language_switch_does_not_leak_across_langs`（H1 regression）/ `tests/test_runtime_hook_filter.py::test_sanitise_overrides_rejects_non_finite_floats`（H2 regression，文件 docstring 扩展为"Runtime-hook emitter micro-tests — safety / filter overflow suite"） |

---

## 🔍 Round 31-36 审计状态

用户在 r35 末要求"深度检查第 31-35 轮"后进行的专项审查原有 H1/H2 + M1-M5 + pre-existing 大文件 3 类发现。round 36 按用户拍板"仅修 H1 + H2"的最小改动方向推进，如下：

### ✅ 已修（round 36 commit 记录）

**H1 ProgressTracker 跨语言 bare-key 污染 — 已修**（commit `fix(round-36): H1 ProgressTracker cross-language bare-key pollution`）

审计复现：`pt_ja = ProgressTracker(p, language='ja')` 开 pre-r35 bare-key progress 文件，`is_chunk_done('a.rpy', x)` 误返回 True（穿透 namespaced miss 命中 zh bare key）。修复后返回 False，regression 测试 `test_progress_tracker_language_switch_does_not_leak_across_langs`（`tests/test_translation_state.py`）通过。

核心思路：非 zh language-aware tracker 完全不读/不写 bare bucket（bare 隐式属于 zh，由新 class 常量 `_LEGACY_BARE_LANG = "zh"` 显式标注）。`is_file_done` / `is_chunk_done` / `get_file_translations` / `mark_file_done` 共 4 处加 language 守卫；`mark_file_done` 的 bare cleanup 也加镜像守卫，防 ja tracker 完成后摧毁 hypothetical zh resume 数据。

保留 r35 的 `test_progress_tracker_legacy_bare_keys_resume_under_language` 测试不变 — zh 仍能 resume pre-r35 bare 数据。

**H2 `_sanitise_overrides` 拒 inf/nan — 已修**（commit `fix(round-36): H2 _sanitise_overrides rejects non-finite floats`）

审计复现：`json.loads('{"gui_overrides": {"gui.text_size": Infinity}}')` 生成 `float('inf')`，过 `isinstance(raw_val, (int, float))` 闸门后 `repr(inf)='inf'` 写入 `zz_tl_inject_gui.rpy` 的 `init python:` block → Ren'Py 启动 `NameError: name 'inf' is not defined`。修复后 inf / -inf / nan 在 safety check 阶段被 skip + warning，regression 测试 `test_sanitise_overrides_rejects_non_finite_floats`（`tests/test_runtime_hook_filter.py`）通过。

核心思路：`core/runtime_hook_emitter.py` 顶部加 `import math`；`_sanitise_overrides` 现有闸门后加 `if isinstance(raw_val, float) and not math.isfinite(raw_val): continue`。过滤自动覆盖所有注册的 category（`gui_overrides` + `config_overrides`），因共享 helper 入口。

---

### 🟡 未修（r37 防御性加固候选）

| # | 位置 | 问题 | 工作量 |
|---|------|------|--------|
| M1 | `core/translation_db.py::load()` | v2 schema + 部分 entries 缺 language 字段时 backfill 跳过 | ~3 行 + 1 测试 |
| M2 | 3 处 JSON loader（font_patch / translation_db / merge_v2）| 无文件大小上限 | 3 × ~5 行 |
| M3 | `main.py:342-353` 外循环 | `args.target_lang` 残留最后语言 | ~3 行 |
| M4 | `_apply_v2_edits:431` | `v2_path` 无路径白名单 | ~10 行 |
| M5 | side-by-side 空串语义 | JS / Python 一致性文档化 + UI hint | ~5 行 |

建议 r37 打包为一轮"防御加固"。

### ⚫ Pre-existing 遗留（不是 r31-36 引入，本次审计发现；r36 不动）

| 文件 | 当前行数 | 最近一次被 r31-36 修改 |
|------|---------|---------------------|
| `tools/rpyc_decompiler.py` | 974 | 无 |
| `core/api_client.py` | 965 | 无 |
| `tests/test_engines.py` | 962 | 无 |
| `gui.py` | 815 | 无 |

建议 r38+ 独立一轮技术债清理（参 r17 / r29 / r32 的拆分 precedent）。

### ❌ 审计 Agent 报告中经核实**不准确**的指控（历史记录）

防止下次对话重新做同样的 bad diagnosis。

| Agent | 原 Claim | 核实结果 |
|-------|---------|---------|
| Agent 2 | "CLAUDE.md 声称 307 实际 362，虚报 55" | **误读**。CLAUDE.md 准确写 378（r36 末）。 |
| Agent 2 | "smoke_test 不存在，虚计 13 条" | **错**。文件在 `tests/smoke_test.py`（9252 字节，13 tests）。 |
| Agent 2 | "22 / 212 orphan 测试（无 `run_all`）" | **误判**。Standalone suites 用 inline runner 是**设计模式**（test_engines / test_batch1 等 10 套件都这样），不进 test_all.py meta-runner 是**有意**的。 |
| Agent 3 | "CRITICAL path traversal in `_apply_v2_edits`" | **过度升级**。威胁模型需 attacker 控制 edits.json；正常流程操作员自导自入同一 JSON。实际 LOW-MEDIUM（M4 候选）。 |
| Agent 3 | "CRITICAL regex DoS via `_SAFE_GUI_KEY`" | **夸大**。Python `re` 非 NFA，polynomial 非 exponential。200-char length cap 即缓解。MEDIUM 顶。 |
| Agent 3 | "XSS in banner innerHTML" | **误判**。所有 `innerHTML` 赋值都走 `esc()` helper（用 `textContent` 转 `innerHTML` 的正确 pattern），实际安全。 |

---

## 📋 Round 37 建议执行顺序

**防御包（M 级合轮，审计挂起）**：
1. **M2 JSON size cap × 3 处** — ~15 行，OOM 防护最广谱
2. **M3 `main.py` 外循环 args 残留** — ~3 行，无实际 reader 但语义正确
3. **M4 `_apply_v2_edits` path 白名单** — ~10 行，降低信任边界风险
4. **M1 v2 partial backfill** — ~3 行 + 1 测试
5. **M5 side-by-side 空串文档化** — ~5 行 docs/UI hint

合计 ~36 行 + 2 新测试；一轮可完成。

**大项（建议独立一轮 r38+）**：
6. 拆分 4 个 pre-existing > 800 行文件（`rpyc_decompiler.py` / `api_client.py` / `test_engines.py` / `gui.py`）— 参 r17 / r29 / r32

**r35 绿色小项（低优先 r37+ 并行考虑）**：
- 🟢 tl-mode / retranslate per-language prompt（让 `--tl-mode ja` 真实工作）
- 🟢 `config_overrides` 值类型扩 bool
- 🟢 editor side-by-side mobile 自适应

---

## ✅ 整体质量评估（r36 末）

- **r35 edge-case bugs**：✅ 清零（H1 + H2 已修 + 2 regression 测试）
- **向后兼容**：✅ 所有 default path byte-identical（无 language 用法 / `language="zh"` 用法均守 r35 语义；非 zh language-aware 调用是**唯一行为改变点** — 之前错误继承 zh bare 数据，现在正确隔离）
- **测试覆盖**：✅ 新增 2 测试有实质断言（直接反映审计 reproducer + 镜像守卫保护）
- **新功能 correctness**：N/A（r36 纯 fix，无新功能）
- **文档同步**：✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG 均现行

**R31-36 六轮累积**：2 个 H-level bug 清零；5 绿色小项闭环（r31 模板 + r32 UI/字体/schema + r33 merge 工具/透传/editor + r34 DB 字段/同页/分派表 + r35 外循环/side-by-side/config 注册）；多语言完整栈（DB schema v2 + ProgressTracker language namespace + main.py 外循环 + editor side-by-side + runtime hook 泛化分派表）。主流程稳定；审计挂起的防御性加固（M1-M5）和 pre-existing 大文件拆分是 r37+ 候选。

---

**本文件由第 36 轮末尾生成，作为第 37 轮起点。**
**下次对话：直接读 `HANDOFF.md` 这一 section，决定 round 37 打 M 级防御包 / 走 r35 绿色小项 / 清理 pre-existing 大文件。**
