# 交接笔记（第 39 轮结束 → 第 40 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 39 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**396 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 522 断言点）。第 39 轮打包 HANDOFF round 38→39 预规划的"收尾包 Part 2"方向：**Commit 1（prep）**拆 `tests/test_translation_state.py` 850→681 行 + 新建 `test_override_categories.py` 218 行（r34/r35/r38 的 4 个 override-dispatch 测试 byte-identical 迁移）+ **Commit 2**tl-mode / retranslate per-language prompt 真实支持（`core/prompts.py` 加 `_GENERIC_TLMODE_SYSTEM_PROMPT` + `_GENERIC_RETRANSLATE_SYSTEM_PROMPT` 英文模板，`build_tl_system_prompt` / `build_retranslate_system_prompt` 按 `lang_config.code` 分路：zh/zh-tw byte-identical r38、非 zh 用新 generic 模板；`TranslationContext` 加 `lang_config` 字段；`tl_mode._translate_chunk` + `retranslator.retranslate_file` 用 `resolve_translation_field` 按 alias chain 读响应；`main.py` 去掉 r35 multi-lang guard；`--tl-mode --target-lang ja` 终于端到端可用）+ **Commit 3 (M2 phase-2)** 3 处用户面 JSON loader 加 50 MB size cap（`tools/review_generator.py` / `tools/analyze_writeback_failures.py` / `pipeline/gate.py` glossary 加载）+ **Commit 4** docs 同步。4 commits，每 bisect-safe；+5 新 regression 测试（prep 拆分 +0 / per-lang prompt +2 / M2 phase-2 +3）。默认路径全部 byte-identical；唯一观察变化点是 `--tl-mode` / `--retranslate` + 非 zh 目标之前 exit=1 现在端到端工作。

---

## 第 20 ~ 39 轮成果索引

详细记录见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md)。摘要：

| 轮 | 主题 | 测试数 |
|----|------|-------|
| 20 | CRITICAL 修复 + pickle RCE + ZIP Slip | 266 → 268 |
| 21 | Top 5 HIGH 收敛 + 并发解锁 | 268 → 280 |
| 22 | 响应体 32 MB 上限 + 集成测试基础 | 280 → 286 |
| 23 | direct.py 拆 4 模块 | 286 |
| 24 | tl_mode + tl_parser 拆 7 模块 | 286 |
| 25 | 7 项 HIGH/MEDIUM 收敛 | 286 → 288 |
| 26 | 综合包（A+B+C） | 288 → 293 |
| 27 | 分层收尾 | 293 |
| 28 | A-H-3 Minimal + S-H-4 Dual-mode | 293 → 301 |
| 29 | test_all.py 拆分 + 路径 bug 修 | 301 |
| 30 | 冷启动审计 4 项 | 301 → 302 |
| 31 | 竞品 hook_template 3 技巧 + runtime hook CLI | 302 → 307 |
| 32 | UI whitelist / 字体打包 / v2 schema + 2 处 bug | 307 → 326 |
| 33 | v2 merge 工具 / font-config 透传 / editor v2 + 拆 test_runtime_hook | 326 → 346 |
| 34 | DB language 字段 + editor 同页多语言 + override 分派表 | 346 → 363 |
| 35 | 多语言外循环 + side-by-side + config_overrides 注册 | 363 → 376 |
| 36 | H1（跨语言 bare-key 污染）+ H2（inf/nan 过滤） | 376 → 378 |
| 37 | M 级防御加固包 M1-M5 | 378 → 385 |
| 38 | "收尾包"：拆 test_editor + M2 扩 4 处 + config bool + mobile `@media` | 385 → 391 |
| 39 | "收尾包 Part 2"：拆 test_state + tl-mode per-lang prompt + M2 phase-2 | 391 → 396 |

---

## 运行时注入模式全能力（截至 round 39）

**何时用**：当静态 `.rpy` 改写不可行时（游戏发布方不允许分发修改后的源文件 / 想保留原始游戏完整性 / 需要给用户"一个补丁包"而非"一个修改版游戏"）。

**启用方式**（所有 opt-in）：
```bash
# 基础：生成 translations.json + zz_tl_inject_hook.rpy
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --emit-runtime-hook

# 扩展：UI 白名单 + v2 多语言 + 字体打包 + gui/config override
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --emit-runtime-hook \
    --ui-button-whitelist custom_ui.txt extra_ui.json \
    --runtime-hook-schema v2 \
    --target-lang zh \
    --font-file /path/to/CustomFont.ttf \
    --font-config /path/to/font_config.json

# Round 39 新：tl-mode / retranslate 非中文目标
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --tl-mode --target-lang ja     # r39: 真实支持（之前 r35 exit=1）
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --retranslate --target-lang ko # r39: 真实支持

# Round 35 多语言外循环（direct-mode 已支持）
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --target-lang zh,ja,zh-tw --emit-runtime-hook --runtime-hook-schema v2

# v2 合并（r33）
python tools/merge_translations_v2.py zh.json ja.json -o merged.json

# 运行时加载（r31 基础 + r32 多语言选择）
RENPY_TL_INJECT=1 ./game.exe
RENPY_TL_INJECT=1 RENPY_TL_INJECT_LANG=zh-tw ./game.exe

# 交互式 review（r33-r38 全套功能，r38 mobile 自适应）
python -m tools.translation_editor --export --db merged.json \
    --v2-lang zh -o review_zh.html
python -m tools.translation_editor --import-json translation_edits.json
```

**生成的文件清单**：
- `translations.json` — flat v1 或嵌套 v2 envelope
- `zz_tl_inject_hook.rpy` — 主 hook 脚本（init python early）
- `zz_tl_inject_gui.rpy` — 可选，gui + config override aux 脚本（init 999），round 33 新增 + r38 接受 bool
- `ui_button_whitelist.json` — 可选，sidecar，round 32 新增
- `fonts/tl_inject.ttf` — 可选，字体 bundle，round 32 新增

**不启用 `--emit-runtime-hook` 时**：完全与 round 30 之前一样，静态改写流程一字不差。所有 round 32-39 新增 flag 全部 opt-in，default 零行为变化。

---

## 推荐的第 40+ 轮工作项

HANDOFF round 38→39 预规划的"收尾包 Part 2"已于 r39 闭环。Priority A + B
持续清零 11 轮；r35 原挂 3 项绿色小项全部清零（C3 r38 / C4 r38 / per-lang
prompt r39）；项目仍处于 steady-state。**r40 主要候选**：pre-existing 4
大文件拆分（r31-39 均未动，独立一轮参 r17 / r29 / r32 / r33 / r38 / r39
precedent）/ 剩余 ~7 处内部 / 低风险 JSON loader size cap 补齐（r40 可
轻量一轮）/ A-H-3 Medium/Deep 或 S-H-4 Breaking（需真实 API + 游戏验证）。

### ⚫ Pre-existing 4 大文件拆分（推荐 r40 主方向）

r31-39 **未触碰**的 4 个 > 800 行源文件（多数从 r10 前就形成），独立
一轮清理：

| 文件 | 行数 | 拆分建议 |
|------|------|---------|
| `tools/rpyc_decompiler.py` | 974 | Tier1 + Tier2 两条反编译链可拆 `_rpyc_tier1.py` + `_rpyc_tier2.py` |
| `core/api_client.py` | 965 | 5 provider 实现（xAI / OpenAI / DeepSeek / Claude / Gemini）+ subprocess plugin 可拆 `core/api_providers/*.py` |
| `tests/test_engines.py` | 962 | 按引擎拆（renpy / rpgmaker / csv）→ 3 个 test file |
| `gui.py` | 815 | UI 面板 + event handler + pipeline 启动可拆；风险：PyInstaller 打包需同步 |

合计 ~5-6h 一轮含测试回归。参 r33 / r38 / r39 测试拆分的成功模式。

### 🟡 剩余 JSON loader size cap（r40 可轻量一轮）

r37-r39 覆盖 11 处 user-facing loader。剩余 ~7 处内部 / 低风险：

| 文件 | 行 | 场景 |
|------|---|------|
| `engines/generic_pipeline.py:151` | progress.json read — 自产 |
| `core/translation_utils.py:138` | ProgressTracker load — 自产 |
| `translators/_screen_patch.py:311` | screen progress — 自产 |
| `tools/rpyc_decompiler.py:437` | rpyc result json — 自产 |
| `engines/rpgmaker_engine.py:85,396` | MV/MZ game files — user-supplied 游戏 |
| `pipeline/stages.py:212,378` | pipeline report — 自产 |
| `gui.py:718` | GUI 用户选的 path |

大部分是内部产物（OOM 风险低）；`rpgmaker_engine` + `gui.py` 仍是 user-
supplied 但 r39 HANDOFF 判断优先级低。~2h 一轮。

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
- **非中文目标语言的端到端验证**：r39 加了 per-language prompt，但尚未
  用真实 API + 真实游戏做 ja / ko / zh-tw 的实际翻译验证。建议 beta
  testers 跑一轮

### 🔴 监控项（暂不修）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 理论链式攻击
- HTTP 响应体 64 KB 精度偏差

### ⚫ 外部基础设施

- CI Windows runner
- docs/constants.md / docs/quality_chain.md / docs/roadmap.md 深度复查
  （连续 10 轮被提及未做）

---

## 架构健康度总览（第 39 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ⚠️ 源码全 < 800；测试全 < 800（r39 拆 `test_translation_state.py` 850→681）；pre-existing 4 个源文件未动（`rpyc_decompiler.py` 974 / `api_client.py` 965 / `tests/test_engines.py` 962 / `gui.py` 815）| round 39 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + line=0 + r37 M1 partial v2 backfill | round 37 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 | round 20/26 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in + 10 KB stderr 上限 | round 28/30 |
| 运行时注入 | ✅ 全套 r31-38 + **r39 tl-mode / retranslate per-language prompt 真实支持非 zh 目标** | round 39 |
| 多语言数据模型 | ✅ 4-tuple 索引 + ProgressTracker language namespace + r37 M1 backfill | round 37 |
| 多语言翻译调度 | ✅ `_parse_target_langs` 外循环 + r37 M3 try/finally restore + **r39 tl-mode / retranslate 也支持多语言（去 r35 guard）** | round 39 |
| **多语言 prompt 支持**（新维度） | ✅ **r39 direct / tl-mode / retranslate 三条管线全部按 `lang_config.code` 分路：zh/zh-tw 中文模板 + 其他语言 generic 英文模板 + `resolve_translation_field` 响应读取** | round 39 |
| 字体路径解析 | ✅ `default_resources_fonts_dir()` canonical + r37 M2 size cap | round 37 |
| 生成代码注入防护 | ✅ `_OVERRIDE_CATEGORIES` 分派 + r38 per-category bool policy + r36 H2 isfinite | round 38 |
| 内存 OOM 防护 | ✅ r37 M2 4 处 + r38 M2 4 处 + **r39 M2 phase-2 3 处 = 11 处 user-facing loader（/ ~16，剩 ~7 处内部 / 低风险 r40+ 候选）** | round 39 |
| 路径信任边界 | ✅ r37 M4 `_apply_v2_edits` CWD 白名单 | round 37 |
| 潜伏 bug | ✅ 清零（r36 H1/H2 + r37 M1） | round 37 |
| 测试覆盖 | ✅ **396 自动化** + tl_parser 75 + screen 51 = **522 断言点**；19 测试套件 | round 39 |
| UI 自适应 | ✅ r38 side-by-side `@media (max-width: 800px)` 桌面 / 手机双路径 | round 38 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 39 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 37/38/39 轮详细 + 第 1-36 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（r28 统一 `engine.run()` + r37 M3 外循环 args restore + **r39 去掉 r35 multi-lang guard**） |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py` |
| 运行时注入 | `core/runtime_hook_emitter.py` + `resources/hooks/inject_hook.rpy` + `resources/hooks/extract_hook.rpy` |
| v2 工具链 | `tools/merge_translations_v2.py` + `tools/translation_editor.py`（r37 M2/M4/M5 + r38 扩 + r38 mobile） |
| Prompt 层（多语言） | **`core/prompts.py`（r11 基础 + r39 `_GENERIC_TLMODE_SYSTEM_PROMPT` + `_GENERIC_RETRANSLATE_SYSTEM_PROMPT`，`build_tl_system_prompt` + `build_retranslate_system_prompt` 按 `lang_config.code` 分路）**+ `core/lang_config.py`（`LANGUAGE_CONFIGS` zh/zh-tw/ja/ko + `resolve_translation_field`） |
| 字体补丁 | `core/font_patch.py`（r32 canonical + r37 M2 50 MB cap） |
| UI 白名单 | `file_processor/checker.py` + r32 新增 |
| 插件沙箱 | `core/api_client._SubprocessPluginClient`（S-H-4） |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py`（**r39 tl_mode + retranslator 加 lang_config 透传 + `resolve_translation_field` 读响应**） |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py`（**r39 `gate.py` glossary 加载 50 MB cap**） |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py` |
| 测试 | `tests/test_all.py`（meta，6 模块）+ 独立套件 16 个（`test_engines` / `smoke_test` / `test_rpa_unpacker` / `test_rpyc_decompiler` / `test_lint_fixer` / `test_tl_dedup` / `test_batch1` / `test_custom_engine` / `test_direct_pipeline` / `test_tl_pipeline` / `test_translation_editor` / `test_translation_editor_v2` r38 / `test_merge_translations_v2` r33 / `test_runtime_hook_filter` r34 / `test_translation_db_language` r34 / `test_multilang_run` r35 / **`test_override_categories` r39 新**） |
| **Round 38 关键增量** | `tests/test_translation_editor_v2.py` r38 新 / `core/config.py` M2 ext / `core/glossary.py` M2 ext shared helper / `tools/translation_editor.py` M2 ext `_MAX_EDITOR_INPUT_SIZE` / `core/runtime_hook_emitter.py` C3 `_OVERRIDE_ALLOW_BOOL` + `_sanitise_overrides.allow_bool` / `_translation_editor_html.py` C4 `@media (max-width: 800px)` |
| **Round 39 关键增量** | **`tests/test_override_categories.py` 新 218 行**（r34/r35/r38 的 4 override dispatch 测试迁移）/ `core/prompts.py::_GENERIC_TLMODE_SYSTEM_PROMPT` + `_GENERIC_RETRANSLATE_SYSTEM_PROMPT` + `build_tl_system_prompt` / `build_retranslate_system_prompt` lang_config 分路 / `core/translation_utils.py::TranslationContext.lang_config` 字段 / `translators/tl_mode.py::_translate_chunk` `resolve_translation_field` + ctx.lang_config 透传 / `translators/retranslator.py::retranslate_file` lang_config kwarg + 响应别名读取 / `main.py` 去 r35 multi-lang guard + argparse help 更新 / `tools/review_generator.py` + `tools/analyze_writeback_failures.py` + `pipeline/gate.py` 各加 50 MB cap |

---

## 🔍 Round 31-39 审计 / 加固状态

### ✅ 已修（commit 记录）

| 轮 | Fix | Commit |
|----|-----|--------|
| r36 | H1 ProgressTracker 跨语言 bare-key 污染 | `39bb791` |
| r36 | H2 `_sanitise_overrides` 拒非有限 float | `8ec89d2` |
| r37 | M1-M5 加固包（backfill + 4 size cap + args restore + path whitelist + tooltip） | `5d8e53a` / `e848598` / `34f1e0c` / `50ecb68` / `0932a04` |
| r38 | test split + M2 ext × 4 + config_overrides bool + mobile @media | `daa7c1b` / `64cc154` / `ea19589` / `e492148` |
| r39 | test_state split + tl/retranslate per-lang prompt + M2 phase-2 × 3 | `7fc6c1b` / `35132f3` / `58fd6ab` |

### 🟡 未修（r40+ 候选）

- Pre-existing 4 大文件拆分（未触碰 9 轮）
- 剩余 ~7 处内部 / 低风险 JSON loader size cap
- A-H-3 Medium/Deep / S-H-4 Breaking
- 非中文目标语言的端到端验证（r39 加了 per-language prompt 但未跑真实 API）
- RPG Maker plugin commands / 加密 RPA / CI / docs 复查

---

## 📋 Round 40 建议执行顺序

**主方向（建议独立一轮）**：拆分 4 个 pre-existing > 800 行源文件（`rpyc_decompiler.py` / `api_client.py` / `tests/test_engines.py` / `gui.py`）。~5-6h 一轮。

**备选短平快（~2-3h 轻量一轮）**：
1. 剩余 ~7 处内部 / 低风险 JSON loader size cap 补齐
2. 非中文目标语言端到端验证（需真实 API）

**大项（独立一轮）**：A-H-3 Medium/Deep / S-H-4 Breaking（需真实 API + 游戏验证）

---

## ✅ 整体质量评估（r39 末）

- **r35 挂起绿色小项**：✅ 3/3 全部清零（C3 config bool r38 / C4 mobile r38 / **C2 tl-mode + retranslate per-lang prompt r39**）
- **测试文件大小负债**：✅ r37 的 `test_translation_editor.py` 已于 r38 拆分；r38 的 `test_translation_state.py` 已于 r39 拆分；当前所有测试文件全 < 800
- **向后兼容**：✅ 所有 default path byte-identical；唯一行为变化点是 `--tl-mode` / `--retranslate` + 非 zh 目标之前 exit=1 现在可用（新能力，非行为改变）
- **测试覆盖**：✅ +5 regression 测试（per-lang prompt +2 / M2 phase-2 +3）；新独立 suite `test_override_categories.py` 清晰分层
- **新功能 correctness**：✅ per-lang prompt 通过 lang_config.code 分路 + resolve_translation_field 的现有 r11 infrastructure；lang_config None default 在所有 2 个 TranslationContext caller 保 r38 byte-identical
- **文档同步**：✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG 均现行

**R31-39 九轮累积**：2 个 H-level bug + 8 个 M-level 加固 + 2 个"收尾包"
全清零；r35 原挂 3 个绿色小项全部清零；多语言完整栈端到端（direct-mode
r11 + tl-mode r39 + retranslate r39）+ 内存/路径信任 + UI 自适应全部闭环。
主流程稳定；r40 候选主要是 pre-existing 大文件拆分（已被 HANDOFF 提及
9 轮）。

---

**本文件由第 39 轮末尾生成，作为第 40 轮起点。**
**下次对话：直接读 `HANDOFF.md` 这一 section，决定 round 40 拆分 pre-existing 4 大文件独立一轮 / 剩余 JSON cap 短平快轻量一轮 / A-H-3 深度重构（需真实 API） / 其他方向。**
