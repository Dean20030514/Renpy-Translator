# 交接笔记（第 35 轮结束 → 第 36 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 35 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**376 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 502 断言点）。第 35 轮清掉 HANDOFF round 34 挂起的三项"🟢 自然延续 round 34 方向"小项：`ProgressTracker` 加 `language` kwarg（namespace key `"<lang>:<rel_path>"`，带 bare key fallback 保 r34 progress 文件 resume）、`main.py` 加 `_parse_target_langs(raw) -> list[str]` 支持 `--target-lang zh,ja,zh-tw` 逗号分隔语法 + 外层语言循环（每 lang 跑一次 `engine.run(args)`）+ `--tl-mode` / `--retranslate` 组合下 guard 报错因 prompt 中文专用、editor toolbar 加 `<input id="v2-side-by-side">` checkbox + `toggleSideBySide` / `_bindSideBySideCellEvents` JS 实现多列并列显示（dropdown 保留共存）、`_OVERRIDE_CATEGORIES` 注册第二个 category `config_overrides`（扁平 `config.X = int|float` 仅，style_overrides 按 r34 决定仍排除）。测试套件扩到 17 个（新增 `test_multilang_run`）。所有新能力向后兼容 — 旧 ProgressTracker 无 language 调用、单语言 `--target-lang zh`、单语言 v2 editor 导出、空 font_config 全部 byte-identical round 34。

---

## 第 20 ~ 35 轮成果索引

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

---

## 运行时注入模式全能力（截至 round 35）

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

**不启用 `--emit-runtime-hook` 时**：完全与 round 30 之前一样，静态改写流程一字不差。所有 round 32/33 新增 flag 全部 opt-in，default 零行为变化。

---

## 推荐的第 36+ 轮工作项

HANDOFF round 34 挂起的三项绿色小项（🟢）已全部完成于 round 35。Priority A + B 清零持续 7 轮；项目仍处于 steady-state。

### 🟢 自然延续 round 35 方向（小项）

**(1) tl-mode / retranslate 的 per-language prompt**：当前两个模式的 system prompt（`core/prompts.py::TLMODE_SYSTEM_PROMPT` + `RETRANSLATE_SYSTEM_PROMPT`）硬编码"翻译为简体中文 + `zh` 字段"。Round 35 加了 multi-lang guard 让 `--tl-mode --target-lang ja` 报错；下一步是真实支持：两个模板改用 `{target_language}` / `{field}` 占位符（参考 direct-mode 已有的 lang_config 处理方式）+ `tl_mode.py:92` / `retranslator.py:284` 读 response 用 `target_lang` 字段 fallback `zh`。~3-4h 含非中文 target 的端到端测试。

**(2) `config_overrides` 值类型扩 bool**：round 35 `_sanitise_overrides` 仍只认 int/float；`config.autosave = True` / `config.developer = False` 这类常见 bool config 被 warning + drop。扩展时要 per-category 控制（不是所有 category 都适合 bool —— `gui.text_size = True` 还是 drop）。~1-2h。

**(3) editor side-by-side N>3 移动端适配**：round 35 CSS `.col-trans-multi { width: 13% }` 写死；6 语言时每列 < 100px 在 mobile viewport 拥挤。加 `@media (max-width: 800px)` 自动回 dropdown 模式或 horizontal-scroll。~1-2h 纯 CSS + 小 JS。

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

### ⚫ 外部基础设施（AI 独立推不动）

- CI Windows runner
- docs/constants.md / docs/quality_chain.md / docs/roadmap.md 深度复查（连续 6 轮被提及未做）

---

## 架构健康度总览（第 35 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ✅ 零（源码最大 test_runtime_hook.py 794；runtime_hook_emitter.py 634；tools/translation_editor.py 555；translators/direct.py 604；checker.py 约 615；inject_hook.rpy 约 345） | round 34 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + 接受 line=0；round 34 升 schema v2 加 `language` 字段保持向后兼容（v1 文件无 default_language 时行为 byte-identical） | round 34 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 | round 20/26 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in + 10 KB stderr 上限 | round 28/30 |
| 运行时注入 | ✅ `--emit-runtime-hook` 基础（r31）+ UI whitelist sidecar / 字体 bundle / v2 多语言 schema（r32）+ gui_overrides 透传 / v2 merge 工具 / editor v2 编辑（r33）+ editor 同页多语言 / `entry_language_filter` 防 bucket 污染 / override 分派表（r34）| round 34 |
| 多语言数据模型 | ✅ `TranslationDB._index` 4-tuple + `ProgressTracker` language namespace（round 35 `"<lang>:<rel_path>"` key，保 bare-key fallback）；`upsert` / `has_entry` / `filter_by_status` / `mark_chunk_done` 均 language-aware；v1→v2 `load()` 强制回填 | round 35 |
| 多语言翻译调度 | ✅ `main.py::_parse_target_langs` 解析 `--target-lang zh,ja,zh-tw` → 外层 `engine.run` 循环；`--tl-mode` / `--retranslate` + 多语言 guard 报错（两个 prompt 中文专用） | round 35 |
| 字体路径解析 | ✅ 全部走 `core.font_patch.default_resources_fonts_dir()` canonical helper，2 处遗留 bug 已修 | round 32 |
| 生成代码注入防护 | ✅ `zz_tl_inject_gui.rpy` 生成走 `_OVERRIDE_CATEGORIES` 分派表 + `_SAFE_GUI_KEY` / `_SAFE_CONFIG_KEY` 正则 + `int`/`float` 白名单（拒 bool/str/list/dict/None）；round 35 新增 `config_overrides` 注册（扁平命名空间仅），style_overrides 仍刻意排除 | round 35 |
| 潜伏 bug | ✅ 清零（round 28/29/30/32 陆续扫清；round 35 确认 tl-mode / retranslate 的 "zh" 硬编码是设计非 bug） | round 35 |
| 测试覆盖 | ✅ **376 自动化** + tl_parser 75 + screen 51 = **502 断言点**；17 测试套件 | round 35 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 35 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 33/34/35 轮详细 + 第 1-32 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（统一 `engine.run()` 分派）/ `one_click_pipeline.py` / `gui.py` / `start_launcher.py` |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py` |
| 运行时注入 | `core/runtime_hook_emitter.py`（r31 基础 + r32 UI sidecar / 字体 bundle / v2 schema + r33 gui_overrides aux rpy）+ `resources/hooks/inject_hook.rpy`（r31 基础 + r32 sidecar reader + v2 reader + env var 语言选择）+ `resources/hooks/extract_hook.rpy`（已有） |
| v2 工具链（round 33） | `tools/merge_translations_v2.py`（multi-lang 合并）+ `tools/translation_editor.py`（`--v2-lang` bucket 编辑） |
| 字体补丁 | `core/font_patch.py::default_resources_fonts_dir`（r32 canonical 出口）+ `resolve_font` + `apply_font_patch` + `load_font_config`（r13，r33 跨模式复用） |
| UI 白名单 | `file_processor/checker.py::COMMON_UI_BUTTONS`（baseline）+ `_ui_button_extensions` + `load_ui_button_whitelist`（r32） |
| 插件沙箱 | `core/api_client._SubprocessPluginClient`（S-H-4）+ `custom_engines/example_echo.py::_plugin_serve` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py`（checker 含 round 27 下沉 + round 31 / 32 新增） |
| 测试 | `tests/test_all.py`（meta，6 模块）+ 6 个拆分（test_api_client / test_file_processor / test_translators / test_glossary_prompts_config / test_translation_state / test_runtime_hook r33）+ 11 个独立套件（test_engines / smoke_test / test_rpa_unpacker / test_rpyc_decompiler / test_lint_fixer / test_tl_dedup / test_batch1 / test_custom_engine / test_direct_pipeline / test_tl_pipeline / test_translation_editor / test_merge_translations_v2 r33 / **test_runtime_hook_filter** r34 新 / **test_translation_db_language** r34 新） |
| Round 34 关键增量 | `core/translation_db.py` schema v2 + `language` 字段 + `default_language` 构造 kwarg / `engines/generic_pipeline.py` resume index 3-tuple + language-aware / `tools/_translation_editor_html.py` HTML/JS 模板（368 行）/ `tools/translation_editor.py::switchV2Language` 同页切换 JS / `core/runtime_hook_emitter.py::_OVERRIDE_CATEGORIES` 分派表 |
| Round 35 关键增量 | `core/translation_utils.py::ProgressTracker` `language` kwarg + `_key()` namespace / `main.py::_parse_target_langs` + `--target-lang zh,ja` 外循环 + tl/retranslate guard / `tools/_translation_editor_html.py` `toggleSideBySide` + `_bindSideBySideCellEvents` + `.col-trans-multi` CSS / `core/runtime_hook_emitter.py::_SAFE_CONFIG_KEY` + `config_overrides` 注册 / `tests/test_multilang_run.py` 新独立 suite |

---

**本文件由第 35 轮末尾自动生成，作为第 36 轮起点。**
