# 交接笔记（第 40 轮结束 → 第 41 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 40 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**396 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 522 断言点）。第 40 轮按 HANDOFF r39→r40 主推方向拆 pre-existing 4 大文件中风险低的 **3 个**（`gui.py` 因 PyInstaller 打包耦合 + UI 手动测试需求挂 r41）：**Commit 1（prep）**拆 `tests/test_engines.py` 962→694 + 新 `test_engines_rpgmaker.py` 315（15 rpgmaker 测试 byte-identical 迁移）+ **Commit 2** 拆 `tools/rpyc_decompiler.py` 974→725（3-module 布局避循环 import：新 `tools/_rpyc_shared.py` 47 leaf 常量 + `tools/_rpyc_tier2.py` 274 safe-unpickle 链，主 re-export Tier 2 + shared 常量让测试 + `renpy_lint_fixer` 原 import 无感）+ **Commit 3** 拆 `core/api_client.py` 965→642（新 `core/api_plugin.py` 378 — `_load_custom_engine` + `_SubprocessPluginClient` sandbox，re-export 保 `test_custom_engine` 20 测试无感）+ **Commit 4** docs 同步。4 commits，每 bisect-safe；**纯结构 refactor，零行为变化，零新测试**（396 保持）。所有本轮拆分都是 byte-identical extraction + re-export 保向后兼容 — 老调用 site 完全无感。

---

## 第 20 ~ 40 轮成果索引

详细记录见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md)。摘要：

| 轮 | 主题 | 测试数 |
|----|------|-------|
| 20-24 | CRITICAL 修复 / HIGH 收敛 / 大文件拆（direct / tl_mode / tl_parser） | 266 → 286 |
| 25-30 | HIGH/MEDIUM 7 项 / 综合包 A+B+C / 分层 / A-H-3 Minimal / test_all 拆 / 冷启动加固 | 286 → 302 |
| 31-32 | 竞品 hook_template 3 技巧 / UI whitelist / 字体打包 / v2 schema | 302 → 326 |
| 33-35 | v2 merge / editor v2 / DB language 字段 / 多语言外循环 / side-by-side | 326 → 376 |
| 36 | 深度审计 H1 + H2 edge-case bug 修复 | 376 → 378 |
| 37 | M 级防御加固包 M1-M5 | 378 → 385 |
| 38 | "收尾包"：拆 test_editor + M2 扩 4 处 + config bool + mobile @media | 385 → 391 |
| 39 | "收尾包 Part 2"：拆 test_state + tl-mode per-lang prompt + M2 phase-2 | 391 → 396 |
| 40 | pre-existing 大文件拆 3/4（test_engines / rpyc_decompiler / api_client；gui.py 挂 r41） | 396 保持（纯 refactor） |

---

## 运行时注入模式全能力（截至 round 40）

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

# 交互式 review（r33-r38 全套，r38 mobile 自适应，r37 M4 CWD 白名单）
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

**不启用 `--emit-runtime-hook` 时**：完全与 round 30 之前一样，静态改写流程一字不差。所有 round 32-40 新增 flag 全部 opt-in，default 零行为变化。

---

## 推荐的第 41+ 轮工作项

HANDOFF round 39→40 主推的"pre-existing 4 大文件拆分"r40 完成 3/4；
`gui.py` 815 因 PyInstaller 打包耦合 + UI 手动测试需求，独立挂 r41。
Priority A + B 持续清零 12 轮；项目仍处于 steady-state。

### 🟠 主推方向 — 拆 `gui.py` 815 行（r40 剩余）

r40 把风险低的 3 个拆完，`gui.py` 需要单独处理。单一大 `class App`
(lines 55-808) 内部是 UI 布局 + 事件处理 + pipeline 启动混合，边界
需要先设计再拆：

**候选拆法**：
- `gui_dialogs.py` — 文件选择 / 消息弹框等辅助 dialog 类
- `gui_handlers.py` — 按钮 / 菜单的 event handler（后半大多是 `def on_XXX(self)` 类）
- `gui_pipeline.py` — subprocess 启动 main.py 的业务逻辑（前台跑 CLI，刷新进度条）
- `gui.py` 保留 `class App` 骨架 + `main()` — 预期 < 400 行

**前置检查**：
- `build.py` 入口显式指向 `gui.py`；PyInstaller 需要确保新模块也被
  include（通常会自动 discover，但 hidden-imports 若需要手动声明
  要提前测）
- 手动 smoke test：拆完打开 GUI，点几个主要按钮（选文件夹 / 开始翻译
  / 查看设置）确认不破坏
- 拆分 commit 前先 `python build.py` 跑一次 dry-run 建包确认能打包

估 ~4-5h 独立一轮（比 r40 的前 3 个难度略高）。

### 🟡 备选短平快（~2-3h 一轮）

1. 剩余 ~7 处内部 / 低风险 JSON loader size cap 补齐（`engines/
   generic_pipeline.py:151` / `core/translation_utils.py:138` /
   `translators/_screen_patch.py:311` / `tools/rpyc_decompiler.py:
   437` / `engines/rpgmaker_engine.py:85,396` / `pipeline/stages.py:
   212,378` / `gui.py:718`）
2. 非中文目标语言端到端验证（r39 per-language prompt 落地，需真实
   API + 真实游戏跑 ja / ko / zh-tw 的实际翻译）

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

### ⚫ 外部基础设施

- CI Windows runner
- docs/constants.md / docs/quality_chain.md / docs/roadmap.md 深度复查
  （连续 11 轮被提及未做）

---

## 架构健康度总览（第 40 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ⚠️ 源码 3/4 清零（r40 拆 `test_engines` / `rpyc_decompiler` / `api_client`），**剩 `gui.py` 815** — r41 候选（PyInstaller 耦合 + UI 手动测试）；测试全 < 800 | round 40 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + line=0 + r37 M1 partial v2 backfill | round 37 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 + **r40 `tools/_rpyc_shared._SHARED_WHITELIST` 独立 leaf 模块，Tier 1 / Tier 2 共享不可能 drift** | round 40 |
| 插件沙箱 | ✅ Dual-mode + **r40 `core/api_plugin.py` 独立模块**（`_load_custom_engine` importlib + `_SubprocessPluginClient` JSONL subprocess sandbox） | round 40 |
| 运行时注入 | ✅ 全套 r31-39 能力 | round 39 |
| 多语言数据模型 | ✅ 4-tuple 索引 + ProgressTracker language namespace + r37 M1 backfill | round 37 |
| 多语言翻译调度 | ✅ `_parse_target_langs` 外循环 + r37 M3 restore + r39 去 multi-lang guard | round 39 |
| 多语言 prompt 支持 | ✅ direct / tl-mode / retranslate 三条管线全部按 `lang_config.code` 分路 + `resolve_translation_field` | round 39 |
| 字体路径解析 | ✅ `default_resources_fonts_dir()` canonical + r37 M2 size cap | round 37 |
| 生成代码注入防护 | ✅ `_OVERRIDE_CATEGORIES` + r38 per-category bool + r36 H2 isfinite | round 38 |
| 内存 OOM 防护 | ✅ 11/~16 user-facing JSON loader 加 50 MB cap（r37 × 4 + r38 × 4 + r39 × 3） | round 39 |
| 路径信任边界 | ✅ r37 M4 `_apply_v2_edits` CWD 白名单 | round 37 |
| 潜伏 bug | ✅ 清零（r36 H1/H2 + r37 M1） | round 37 |
| **模块分层** | ✅ **r40 tier 分离：`_rpyc_shared`（leaf 常量）↓ `_rpyc_tier2`（safe-unpickle）/ `rpyc_decompiler`（Tier 1 + public API + CLI）；`api_plugin`（plugin loader + sandbox）↑ `api_client`（provider dispatch + APIClient 核心）。Re-export 保向后兼容。** | round 40 |
| 测试覆盖 | ✅ **396 自动化**（r40 纯 refactor 保持）+ tl_parser 75 + screen 51 = **522 断言点**；**20 测试套件** | round 40 |
| UI 自适应 | ✅ r38 side-by-side `@media (max-width: 800px)` | round 38 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 40 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 38/39/40 轮详细 + 第 1-37 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（r28 统一 `engine.run()` + r37 M3 外循环 args restore + r39 去 r35 multi-lang guard） |
| 核心 | `core/{api_client,api_plugin,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py`（**r40 新增 api_plugin.py**） |
| 运行时注入 | `core/runtime_hook_emitter.py` + `resources/hooks/inject_hook.rpy` + `resources/hooks/extract_hook.rpy` |
| v2 工具链 | `tools/merge_translations_v2.py` + `tools/translation_editor.py` |
| Prompt 层（多语言） | `core/prompts.py`（r39 双模板分路）+ `core/lang_config.py` |
| 字体补丁 | `core/font_patch.py`（r32 canonical + r37 M2 50 MB cap） |
| UI 白名单 | `file_processor/checker.py` + r32 新增 |
| **插件沙箱（r40 独立模块）** | **`core/api_plugin.py`**（`_load_custom_engine` + `_SubprocessPluginClient`，r40 从 `api_client.py` 抽出；`api_client` re-export 保老 import site 无感）+ `custom_engines/example_echo.py` 示例 |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py`（r39 tl_mode + retranslator 多语言就绪） |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py`（r39 gate.py glossary 50 MB cap） |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py` |
| **rpyc 反编译（r40 三模块布局）** | **`tools/rpyc_decompiler.py` 725**（Tier 1 game-python decompile + 平台/版本检测 + 公共 API + CLI + re-export from `_rpyc_tier2`）+ **`tools/_rpyc_tier2.py` 274**（`_DummyClass` + `_RestrictedUnpickler` + `_read_rpyc_data` + `_safe_unpickle` + `_extract_text_from_node` + `extract_strings_from_rpyc`）+ **`tools/_rpyc_shared.py` 47**（`RPYC2_HEADER` / `_SHARED_WHITELIST` / `_WHITELIST_TIER1_PY2_EXTRAS` leaf 常量） |
| 测试 | `tests/test_all.py`（meta，6 模块）+ 独立套件 **17** 个（`test_engines` + **`test_engines_rpgmaker` r40 新** + `smoke_test` / `test_rpa_unpacker` / `test_rpyc_decompiler` / `test_lint_fixer` / `test_tl_dedup` / `test_batch1` / `test_custom_engine` / `test_direct_pipeline` / `test_tl_pipeline` / `test_translation_editor` / `test_translation_editor_v2` / `test_merge_translations_v2` / `test_runtime_hook_filter` / `test_translation_db_language` / `test_multilang_run` / `test_override_categories`） |
| **Round 40 关键增量** | **`tools/_rpyc_shared.py` 新 47** + **`tools/_rpyc_tier2.py` 新 274** + **`core/api_plugin.py` 新 378** + **`tests/test_engines_rpgmaker.py` 新 315** / `tools/rpyc_decompiler.py` 974→725 / `core/api_client.py` 965→642 / `tests/test_engines.py` 962→694 |

---

## 🔍 Round 31-40 审计 / 加固 / 拆分状态

### ✅ 已修 / 已拆（commit 记录）

| 轮 | Fix | Commit |
|----|-----|--------|
| r36 | H1 跨语言 bare-key 污染 + H2 inf/nan 过滤 | `39bb791` / `8ec89d2` |
| r37 | M1-M5 加固包 | `5d8e53a` / `e848598` / `34f1e0c` / `50ecb68` / `0932a04` |
| r38 | test split + M2 ext × 4 + config bool + mobile @media | `daa7c1b` / `64cc154` / `ea19589` / `e492148` |
| r39 | test_state split + tl/retranslate per-lang prompt + M2 phase-2 × 3 | `7fc6c1b` / `35132f3` / `58fd6ab` |
| r40 | test_engines split / rpyc_decompiler Tier 2 + shared split / api_client plugin split | `dfa95e4` / `8588f57` / `b47c415` |

### 🟡 未修（r41+ 候选）

- **`gui.py` 815 行拆分**（r40 剩余，PyInstaller + UI 手动测试需独立一轮）
- 剩余 ~7 处内部 / 低风险 JSON loader size cap
- 非中文目标语言端到端验证（需真实 API）
- A-H-3 Medium/Deep / S-H-4 Breaking
- RPG Maker plugin commands / 加密 RPA / CI / docs 复查

---

## 📋 Round 41 建议执行顺序

**主推方向（建议独立一轮）**：拆 `gui.py` 815 行 — 单一大 `class App`
拆为 dialogs / handlers / pipeline-runner 三个子模块，保留 `class App`
骨架；前置 build.py smoke test 确认 PyInstaller 打包不破。~4-5h。

**备选短平快（~2-3h 一轮）**：
1. 剩余 ~7 处内部 JSON loader size cap 补齐（收尾 r37-39 M2 工作）
2. 非中文目标语言端到端 smoke test（验证 r39 per-lang prompt 真实
   API 工作）

**大项（独立一轮）**：A-H-3 Medium/Deep / S-H-4 Breaking（需真实 API +
游戏验证）

---

## ✅ 整体质量评估（r40 末）

- **Pre-existing 大文件负债**：✅ 3/4 清零（`test_engines` / `rpyc_
  decompiler` / `api_client`）；`gui.py` 815 flagged 为 r41 主方向
- **模块分层**：✅ r40 引入三层新布局：
  - `_rpyc_shared`（leaf 常量）← `_rpyc_tier2`（safe-unpickle）+ `rpyc_
    decompiler`（Tier 1 + public + CLI）
  - `api_plugin`（plugin loader + sandbox）← `api_client`（provider
    dispatch + APIClient 核心）
- **向后兼容**：✅ 所有 r40 拆分用 re-export 保老 import site 无感 —
  `test_rpyc_decompiler.py`（18 测试 import 6 个 Tier 2 符号 + shared
  常量 by 老名）+ `test_custom_engine.py`（20 测试 import 2 个 plugin
  符号）+ `tools/renpy_lint_fixer.py`（import `_find_renpy_python`）
  完全不用改
- **测试覆盖**：✅ **396 保持**（r40 纯 refactor）；20 测试套件 → 21（r40
  新 `test_engines_rpgmaker`）
- **文档同步**：✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG 均现行

**R31-40 十轮累积**：2 个 H-level bug + 8 个 M-level 加固 + 2 个"收尾
包" + 3 个 pre-existing 大文件拆分全清零；r35 原挂 3 个绿色小项全部
清零；多语言完整栈 + 内存/路径信任 + UI 自适应全部闭环；r40 引入模块
分层基础设施（shared 常量 leaf + plugin 抽象）。主流程稳定；r41 候选
主要是 `gui.py` 拆 + 剩余 JSON cap + 非 zh 端到端验证。

---

**本文件由第 40 轮末尾生成，作为第 41 轮起点。**
**下次对话：直接读 `HANDOFF.md` 这一 section，决定 round 41 拆 `gui.py` 独立一轮（含 build.py smoke test）/ 剩余 JSON cap 短平快 / 非 zh 端到端验证 / 其他方向。**
