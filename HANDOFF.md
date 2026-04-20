# 交接笔记（第 38 轮结束 → 第 39 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 38 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**391 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 517 断言点）。第 38 轮打包 HANDOFF round 37→38 预规划的"收尾包"方向：**Commit 1（prep）**拆 `tests/test_translation_editor.py` 847→376 行 + 新建 `test_translation_editor_v2.py` 581 行（11 个 v2 / side-by-side / M4 / M5 测试 byte-identical 迁移，零行为变化）+ **Commit 2 (M2 扩)** 给另 4 处 user-facing JSON loader 加 50 MB size cap（`core/config.py::_load_config_file` / `core/glossary.py` 的 4 loader 共享 `_json_file_too_large` helper / `tools/translation_editor.py::_extract_from_db` + `import_edits`，`_MAX_V2_APPLY_SIZE` 重命名为更通用的 `_MAX_EDITOR_INPUT_SIZE`）+ **Commit 3 (C3)** `config_overrides` 扩 bool（新 `_OVERRIDE_ALLOW_BOOL` per-category map：gui 仍拒、config 接受；`_sanitise_overrides` 加 `allow_bool` kwarg，bool 检查先于 int/float 防 `isinstance(True,int)` 偷渡；更新 r35 测试 + 新 gui regression guard）+ **Commit 4 (C4)** editor side-by-side `@media (max-width: 800px)` mobile 自适应（table `overflow-x: auto`、`.col-trans-multi min-width: 120px`、iOS Safari momentum 滚动）+ **Commit 5** docs 同步。5 fix commits + 1 docs commit，每 bisect-safe；+6 新 regression 测试（prep 拆分 +0 / M2 扩 +4 / C3 +1 / C4 +1）。默认路径全部 byte-identical；唯一观察变化点是 C3 下 config bool 之前被 reject 现在被接受（opt-in widen）和 C4 下窄屏 UX 改进。

---

## 第 20 ~ 38 轮成果索引

详细记录见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md)。摘要：

| 轮 | 主题 | 测试数 |
|----|------|-------|
| 20 | CRITICAL：悬空 import × 3 + pickle RCE × 3 + ZIP Slip + 治理文档 | 266 → 268 |
| 21 | HIGH：HTTP 连接池 + ProgressTracker 双锁 + API Key subprocess env + 11 条 mock 测试 + P1 审查回刷 | 268 → 280 |
| 22 | 响应体 32 MB 硬上限 + T-C-3/T-H-2 集成测试基础 | 280 → 286 |
| 23 | direct.py 拆分 4 模块（1301 → 584） | 286 |
| 24 | tl_mode + tl_parser 拆分 7 模块（2034 → 1099） | 286 |
| 25 | 7 项 HIGH/MEDIUM 收敛 | 286 → 288 |
| 26 | 综合包（A+B+C） | 288 → 293 |
| 27 | 分层收尾：A-H-2 + A-H-5 | 293 |
| 28 | A-H-3 Minimal + S-H-4 Dual-mode 沙箱 | 293 → 301 |
| 29 | test_all.py 拆分 + 路径 bug 修复 | 301 |
| 30 | 冷启动审计 4 项加固 | 301 → 302 |
| 31 | 竞品 renpy_hook_template 3 技巧 + runtime hook CLI | 302 → 307 |
| 32 | UI whitelist / 字体打包 / v2 schema + 2 处 `__file__.parent` bug 修 | 307 → 326 |
| 33 | v2 merge 工具 / font-config 透传 / editor v2 + 拆 test_runtime_hook | 326 → 346 |
| 34 | DB language 字段 + editor 同页多语言 + override 分派表 | 346 → 363 |
| 35 | 多语言外循环 + side-by-side + config_overrides 注册 | 363 → 376 |
| 36 | 深度审计修 H1（跨语言 bare-key 污染）+ H2（inf/nan 过滤） | 376 → 378 |
| 37 | M 级防御加固包 M1-M5（backfill / size cap / args restore / path whitelist / 空串 tooltip） | 378 → 385 |
| 38 | "收尾包"：拆 test_editor + M2 扩 4 处 + config_overrides 扩 bool + mobile `@media` | 385 → 391 |

---

## 运行时注入模式全能力（截至 round 38）

**何时用**：当静态 `.rpy` 改写不可行时（游戏发布方不允许分发修改后的源文件 / 想保留原始游戏完整性 / 需要给用户"一个补丁包"而非"一个修改版游戏"）。

**启用方式**（所有 opt-in）：
```bash
# 基础：生成 translations.json + zz_tl_inject_hook.rpy
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --emit-runtime-hook

# 扩展：UI 白名单 + v2 多语言 + 字体打包 + gui 字号/布局 + config bool switches (r38)
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --emit-runtime-hook \
    --ui-button-whitelist custom_ui.txt extra_ui.json \
    --runtime-hook-schema v2 \
    --target-lang zh \
    --font-file /path/to/CustomFont.ttf \
    --font-config /path/to/font_config.json    # round 33-38: 含 gui_overrides + config_overrides (r38 接受 bool)

# font_config.json 示例（r38 新：config_overrides 接受 bool）
# {
#   "gui_overrides": {
#     "gui.text_size": 22,
#     "gui.name_text_size": 24
#   },
#   "config_overrides": {
#     "config.autosave": true,
#     "config.developer": false,
#     "config.rollback_enabled": true
#   }
# }

# 多语言合并（round 33）：分别运行 zh / zh-tw / ja，再 merge
python tools/merge_translations_v2.py zh.json zh-tw.json ja.json \
    -o merged_translations.json --default-lang zh

# 使用时把生成的文件拖到游戏 game/ 目录，然后设置环境变量启动：
RENPY_TL_INJECT=1 ./game.exe
RENPY_TL_INJECT=1 RENPY_TL_INJECT_LANG=zh-tw ./game.exe

# 交互式 review v2 文件（r33 editor v2 + r34 dropdown + r35 side-by-side + r37 M4 CWD +
# r38 mobile 自适应）：CWD 必须是 v2 envelope 所在目录或祖先（M4 白名单）。
python -m tools.translation_editor --export --db merged_translations.json \
    --v2-lang zh -o review_zh.html
python -m tools.translation_editor --import-json translation_edits.json
```

**生成的文件清单**：
- `translations.json` — flat v1 或嵌套 v2 envelope
- `zz_tl_inject_hook.rpy` — 主 hook 脚本（init python early）
- `zz_tl_inject_gui.rpy` — 可选，gui / config override aux 脚本（init 999），round 33 新增 + r38 接受 bool
- `ui_button_whitelist.json` — 可选，sidecar，round 32 新增
- `fonts/tl_inject.ttf` — 可选，字体 bundle，round 32 新增

**不启用 `--emit-runtime-hook` 时**：完全与 round 30 之前一样，静态改写流程一字不差。所有 round 32-38 新增 flag 全部 opt-in，default 零行为变化。

---

## 推荐的第 39+ 轮工作项

HANDOFF round 37→38 预规划的"收尾包"已于 r38 闭环。Priority A + B 持续
清零 10 轮；项目仍处于 steady-state。**r39 主要候选**：拆分 `tests/test_
translation_state.py`（r38 C3 加测试后 850 行越软限）/ 其他 JSON loader
size cap 继续扩展 / tl-mode per-language prompt（r35 最后一项挂起绿色
小项）/ pre-existing 4 大文件拆分（r31-38 未动）。

### 🟡 即刻小项（r38 直接抛出的债 + r35 挂了 3 轮的最后一项）

**(1) 拆 `tests/test_translation_state.py`**：r38 C3 加
`test_gui_overrides_still_rejects_bool` 约 50 行后文件 850 行（799 → 850，
+51），越 800 软限 50 行。和 r37 越软限的 `test_translation_editor.py`
一样，建议参 r33 / r38 的拆分 precedent 抽出一个新文件。候选拆法：把
r34/r35 的 override 相关测试（`test_sanitise_overrides_unknown_category_
ignored` / `test_override_categories_table_is_extensible` /
`test_config_overrides_emits_assignments` / `test_gui_overrides_still_
rejects_bool`）移到新 `tests/test_override_categories.py`。主文件回
到 ~700 行。~1h 纯结构 refactor。

**(2) tl-mode / retranslate per-language prompt**：r35 HANDOFF 挂起的
最后一项绿色小项 — `core/prompts.py::TLMODE_SYSTEM_PROMPT` +
`RETRANSLATE_SYSTEM_PROMPT` 仍硬编码中文输出 `"zh"` 字段。r35 加
multi-lang guard 让 `--tl-mode --target-lang ja` 报错；下一步是真实
支持：两个模板改用 `{target_language}` / `{field}` 占位符 +
`tl_mode.py:92` / `retranslator.py:284` 读 response 用 `target_lang`
字段 fallback `zh`。~3-4h 含非中文 target 的端到端测试。

**(3) 其他 JSON loader size cap 继续扩展**：r38 覆盖了 4 处用户面
loader，仍有 ~10 处内部 / 低风险 loader 未覆盖（见 r38 CHANGELOG 列
表：`engines/generic_pipeline.py:151` / `core/translation_utils.py:138`
/ `translators/_screen_patch.py:311` / `tools/analyze_writeback_
failures.py:36` / `tools/review_generator.py:35` / `tools/rpyc_
decompiler.py:437` / `engines/rpgmaker_engine.py:85,396` /
`pipeline/stages.py:212,378` / `pipeline/gate.py:116` / `gui.py:718`）。
大部分是内部产物或游戏文件，OOM 风险较低，按优先级分批做。

### 🟠 延续未做的深度重构

**A-H-3 Medium / Deep**：当前 A-H-3 只做 Minimal。Medium（adapter 层
让 Ren'Py 走 generic_pipeline 6 阶段）或 Deep（完全退役 DialogueEntry）。
需真实 API + 真实游戏验证。

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

- **Pre-existing > 800 行源文件拆分**（r31-38 未触碰）：`tools/rpyc_
  decompiler.py` 974 / `core/api_client.py` 965 / `tests/test_engines.py`
  962 / `gui.py` 815。建议独立一轮参 r17 / r29 / r32 / r33 / r38
  拆分 precedent。
- CI Windows runner
- docs/constants.md / docs/quality_chain.md / docs/roadmap.md 深度复查
  （连续 9 轮被提及未做）

---

## 架构健康度总览（第 38 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ⚠️ 源码全 < 800；**r38 C3 加测试后 `tests/test_translation_state.py` 850 行越软限 50 行** → r39 拆分；pre-existing 4 个文件未动（`rpyc_decompiler.py` 974 / `api_client.py` 965 / `tests/test_engines.py` 962 / `gui.py` 815） | round 38 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + 接受 line=0 + r37 M1 partial v2 backfill | round 37 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 | round 20/26 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in + 10 KB stderr 上限 | round 28/30 |
| 运行时注入 | ✅ 全套 r31-37 + **r38 `config_overrides` 接受 bool** + **side-by-side mobile `@media` 自适应** | round 38 |
| 多语言数据模型 | ✅ 4-tuple 索引 + ProgressTracker language namespace + r37 M1 覆盖 partial v2 backfill | round 37 |
| 多语言翻译调度 | ✅ `_parse_target_langs` 外循环 + r37 M3 try/finally restore | round 37 |
| 字体路径解析 | ✅ `default_resources_fonts_dir()` canonical + r37 M2 size cap | round 37 |
| 生成代码注入防护 | ✅ `_OVERRIDE_CATEGORIES` 分派表 + 正则白名单 + **r38 per-category value type（gui int/float / config int/float/bool）** + r36 H2 `isfinite` | round 38 |
| 内存 OOM 防护 | ✅ r37 M2 4 处 + **r38 M2 扩 4 处（8/16 用户面 loader；另 ~10 处内部 / 低风险 loader 是 r39+ 候选）** | round 38 |
| 路径信任边界 | ✅ r37 M4 `_apply_v2_edits` CWD 白名单 | round 37 |
| 潜伏 bug | ✅ 清零（r36 H1/H2 + r37 M1） | round 37 |
| 测试覆盖 | ✅ **391 自动化** + tl_parser 75 + screen 51 = **517 断言点**；18 测试套件 | round 38 |
| UI 自适应 | ✅ **r38 side-by-side `@media (max-width: 800px)` 桌面 / 手机双路径** | round 38 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 38 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 36/37/38 轮详细 + 第 1-35 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（r28 统一 `engine.run()` + r37 M3 外循环 args restore） |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py` |
| 运行时注入 | `core/runtime_hook_emitter.py`（r31 基础 + r32/r33 全套 + r34/r35 dispatch + r36 H2 isfinite + **r38 C3 per-category `_OVERRIDE_ALLOW_BOOL`**）+ `resources/hooks/inject_hook.rpy` + `resources/hooks/extract_hook.rpy` |
| v2 工具链 | `tools/merge_translations_v2.py` + `tools/translation_editor.py`（r33-37 + **r38 `_MAX_EDITOR_INPUT_SIZE` 覆盖所有 3 个 editor 输入路径**）+ `tools/_translation_editor_html.py`（**r38 C4 `@media` mobile adaptive CSS**） |
| 字体补丁 | `core/font_patch.py`（r32 canonical + r37 M2 50 MB cap）|
| UI 白名单 | `file_processor/checker.py` + r32 新增 |
| 插件沙箱 | `core/api_client._SubprocessPluginClient`（S-H-4） |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py` |
| 测试 | `tests/test_all.py`（meta，6 模块）+ 独立套件 15+1 个（`test_engines` / `smoke_test` / `test_rpa_unpacker` / `test_rpyc_decompiler` / `test_lint_fixer` / `test_tl_dedup` / `test_batch1` / `test_custom_engine` / `test_direct_pipeline` / `test_tl_pipeline` / `test_translation_editor` / `test_merge_translations_v2` / `test_runtime_hook_filter` / `test_translation_db_language` / `test_multilang_run` / **`test_translation_editor_v2` r38 新**） |
| **Round 37 关键增量** | `core/translation_db.py::load()` M1 去 version gate + r37 M2 50 MB cap / `core/font_patch.py` r37 M2 / `tools/merge_translations_v2.py` r37 M2 / `tools/translation_editor.py::_apply_v2_edits` M2 + M4 CWD whitelist + M5 docstring / `main.py` M3 外循环 restore / `_translation_editor_html.py` M5 label tooltip |
| **Round 38 关键增量** | **`tests/test_translation_editor_v2.py` 新 581 行**（r33-r37 v2 相关 11 测试迁移，r38 C4 mobile test）/ `core/config.py::_load_config_file` M2 ext / `core/glossary.py` 4 loader 共享 `_json_file_too_large` helper M2 ext / `tools/translation_editor.py::_extract_from_db` + `import_edits` M2 ext，`_MAX_V2_APPLY_SIZE` 重命名为 `_MAX_EDITOR_INPUT_SIZE` / `core/runtime_hook_emitter.py` C3 `_OVERRIDE_ALLOW_BOOL` + `_sanitise_overrides` `allow_bool` kwarg / `_translation_editor_html.py` C4 `@media (max-width: 800px)` 块 |

---

## 🔍 Round 31-38 审计 / 加固状态

### ✅ 已修

| 轮 | Fix | Commit |
|----|-----|--------|
| r36 | H1 ProgressTracker 跨语言 bare-key 污染 | `39bb791` |
| r36 | H2 `_sanitise_overrides` 拒非有限 float | `8ec89d2` |
| r37 | M1 `TranslationDB.load()` partial v2 backfill | `5d8e53a` |
| r37 | M2 × 4 sites 50 MB size cap（font_patch / translation_db / merge_v2 / _apply_v2_edits） | `e848598` |
| r37 | M3 `main.py` 外循环 args restore | `34f1e0c` |
| r37 | M4 `_apply_v2_edits` CWD path whitelist | `50ecb68` |
| r37 | M5 空串 cell = SKIP 文档化 + tooltip | `0932a04` |
| r38 | test split prep（test_translation_editor.py 越软限） | `daa7c1b` |
| r38 | M2 ext × 4 more sites（config / glossary × 4 / _extract_from_db / import_edits） | `64cc154` |
| r38 | C3 `config_overrides` 扩 bool（per-category） | `ea19589` |
| r38 | C4 editor side-by-side `@media` mobile 自适应 | `e492148` |

### 🟡 未修（r39+ 候选）

- `tests/test_translation_state.py` 850 行越 800 软限（r38 C3 +50 行
  gui regression 导致）— r39 拆分候选（参 r33 / r38 precedent）
- tl-mode / retranslate per-language prompt（r35 最后一项挂起绿色小项）
- 其他 ~10 处 JSON loader size cap 扩展（内部 / 低风险）
- Pre-existing 4 个源文件 > 800 行（`rpyc_decompiler.py` /
  `api_client.py` / `tests/test_engines.py` / `gui.py`）
- A-H-3 Medium/Deep / S-H-4 Breaking / RPG Maker plugin commands / CI /
  docs 复查

---

## 📋 Round 39 建议执行顺序

**短平快小项（合为一轮"收尾包 Part 2"建议）**：
1. 拆 `tests/test_translation_state.py`（override 相关 → 新 `test_
   override_categories.py`）— ~1h
2. tl-mode / retranslate per-language prompt — ~3-4h 含端到端
3. 剩余 JSON loader size cap 扩展（按优先级挑 3-5 处）— ~2h

合计 ~7h，一轮可清 r35 + r38 的剩余债。

**大项（独立一轮）**：
4. 拆分 4 个 pre-existing > 800 行源文件（`rpyc_decompiler.py` /
   `api_client.py` / `test_engines.py` / `gui.py`）

---

## ✅ 整体质量评估（r38 末）

- **r35 挂起绿色小项**：✅ 2/3 清零（C3 config bool + C4 mobile）；仍挂
  tl-mode per-lang prompt 一项
- **测试文件大小负债**：⚠️ r37 的 `test_translation_editor.py` 已于 r38
  拆分；r38 新产 `test_translation_state.py` 850 行越软限，r39 候选
- **向后兼容**：✅ 所有 default path byte-identical；唯一行为变化点是
  C3 下 `config.autosave=True` 这类 bool 之前被 reject 现在被接受（opt-in
  widen）；C4 桌面 (>= 800px) byte-identical，窄屏 UX 改进非改变
- **测试覆盖**：✅ +6 regression 测试（M2 扩 +4 + C3 +1 + C4 +1）；新
  独立 suite `test_translation_editor_v2.py` 清晰分层
- **新功能 correctness**：✅ config_overrides bool 通过共享 `_sanitise_
  overrides` + `_OVERRIDE_ALLOW_BOOL` per-category gate 实现；gui 拒
  bool 的既有测试继续守护
- **文档同步**：✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG 均现行

**R31-38 八轮累积**：2 个 H-level bug + 5 个 M-level 加固 + 1 个"收尾包"
全清零；r35 原挂 3 个绿色小项清 2 个（剩 tl-mode per-lang）；多语言完
整栈 + 内存/路径信任 + UI 自适应全部闭环。主流程稳定；r39 候选主要是
r35 最后一项 + 测试文件拆 + pre-existing 大文件。

---

**本文件由第 38 轮末尾生成，作为第 39 轮起点。**
**下次对话：直接读 `HANDOFF.md` 这一 section，决定 round 39 打"收尾包 Part 2"
（test_state 拆 + tl-mode per-lang prompt + JSON cap 续扩）/ 拆 pre-
existing 4 大文件独立一轮 / 其他方向。**
