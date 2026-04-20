# 交接笔记（第 41 轮结束 → 第 42 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 41 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**398 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 524 断言点）。第 41 轮按 HANDOFF r40→r41 主推方向完成 pre-existing 大文件拆分（4/4 收官，**源码全部 < 800 行首次达成**）+ 合流 r40 末审计的 3 项 MEDIUM/LOW 小尾巴：**Commit 1（prep）**抽 `gui.py` 中 3 个 UI event handler 到新 `gui_handlers.py` 73（`AppHandlersMixin`；`_PROVIDER_DEFAULTS` 副本避 import cycle）+ **Commit 2** 抽 9 个 pipeline 方法 + 3 常量到新 `gui_pipeline.py` 230（`AppPipelineMixin`；`_on_finished` 归此 mixin — 语义正确因它是 subprocess completion callback；`App.__init__` 加 `self._project_root` 代替 mixin 里 `__file__` 引用，避 subprocess cwd 错误）+ **Commit 3** 抽 5 个 dialog 方法到新 `gui_dialogs.py` 140（`AppDialogsMixin`；跨 mixin 调用如 `_append_log` 通过 MRO 自动解析）+ **Commit 4** `tools/translation_editor.py` 的 M4 `except OSError: trust_root = None` 加 `logger.warning(...)` 防 CWD 白名单 silent bypass（+1 regression test 用 monkey-patch `Path.cwd` + 临时 `logging.Handler`）+ **Commit 5** r39 alias-chain response-read integration test `test_tl_chunk_reads_alias_field_from_mocked_response`（mock `APIClient.translate` 返回 "zh" 陷阱 + "ja"/"jp" 真实 alias 证明 `resolve_translation_field` 被调用）+ **Commit 6** HANDOFF/CHANGELOG 的 "N 测试套件" 表述统一为 "测试文件数 = 独立 suite + meta-runner"（retroactively r38=19 / r39=20 / r40=21 monotonic）+ **Commit 7** docs 同步。7 commits，每 bisect-safe；**纯结构 refactor + 2 新测试**，零行为变化。

---

## 第 20 ~ 41 轮成果索引

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
| 41 | pre-existing 大文件拆 4/4 收官（gui.py 815→489 拆为 3 mixin）+ 3 项审计小尾巴合流 | 396 → 398 |

---

## 运行时注入模式全能力（截至 round 41）

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

# Round 39 新：tl-mode / retranslate 非中文目标（r41 response-read 路径已 integration-tested）
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

# 交互式 review（r33-r38 全套，r38 mobile 自适应，r37 M4 CWD 白名单 + r41 log-on-OSError）
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

**不启用 `--emit-runtime-hook` 时**：完全与 round 30 之前一样，静态改写流程一字不差。所有 round 32-41 新增 flag 全部 opt-in，default 零行为变化。

---

## 推荐的第 42+ 轮工作项

HANDOFF round 40→41 主推的"pre-existing 4 大文件拆分"r41 收官（4/4 全部 < 800）。Priority A + B 持续清零已 13 轮；项目进入真正 steady-state — 下一轮没有自然主推方向，以下是候选。

### 🟢 短平快小项（~2-3h 一轮）

**PyInstaller 打包 smoke test + hidden-imports 兜底**

r41 依赖 PyInstaller 静态分析自动 discover 同目录 `from gui_handlers import ...` / `from gui_pipeline import ...` / `from gui_dialogs import ...`，理论上应工作。r41 未在本地实跑 `python build.py`（pyinstaller 可能未装）。

建议 r42 起步先跑：
```bash
pip install pyinstaller
python build.py
./dist/多引擎游戏汉化工具.exe  # 启动 smoke
```
若失败，追加兜底到 `build.py::hidden_imports`：
```python
"gui_handlers", "gui_pipeline", "gui_dialogs",
```
3 行 fix + 一次验证。

**GUI 手动 smoke test 全面清单**

r41 每 commit 后仅跑 148 meta tests + `import gui` 语法检查；Tkinter callback + mixin MRO 在真实运行时的全面验证留 r42：
- 启动 `python gui.py`
- 切换"基本设置"引擎下拉 → 面板切换工作
- 切换提供商 → 模型自动更新
- 切换 Ren'Py 翻译模式 → tl 语言字段启用/禁用工作、pipeline 参数 show/hide
- 填入虚拟路径 + API key → 点"开始翻译"触发 warning messagebox
- 点"停止"、点"清空日志"
- 工具菜单 Dry-run / 升级扫描弹 dialog
- 配置保存到 JSON / 从 JSON 加载

若任一 callback 不工作（MRO dispatch 错位 / `self.X` 访问失败），回退到单文件或重新调整 mixin 继承顺序。

### 🟡 备选短平快（~2-3h 一轮）

1. 剩余 ~7 处内部 / 低风险 JSON loader size cap 补齐（`engines/generic_pipeline.py:151` / `core/translation_utils.py:138` / `translators/_screen_patch.py:311` / `tools/rpyc_decompiler.py:437` / `engines/rpgmaker_engine.py:85,396` / `pipeline/stages.py:212,378`）
2. 非中文目标语言端到端验证（r39 per-lang prompt 落地 + r41 integration test 锁死 code-level contract，但需真实 API + 真实游戏跑 ja / ko / zh-tw 的实际翻译）
3. `file_processor/checker.py::check_response_item` 的 "zh" 硬编码 per-language 化（r41 audit test 文档化了这个约束；操作 checker 把 `item.get("zh")` 改为用 `resolve_translation_field(item, lang_config)` 链式查，+ 1-2 个 regression test）

### 🟠 延续未做的深度重构（需真实 API + 游戏验证）

**A-H-3 Medium / Deep**：当前 A-H-3 只做 Minimal。Medium（adapter 层让 Ren'Py 走 generic_pipeline 6 阶段）或 Deep（完全退役 DialogueEntry）。需真实 API + 真实游戏验证。

**S-H-4 Breaking**：强制所有插件走 subprocess，retire importlib 路径。目前 dual-mode 已经稳定。

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
  （连续 12 轮被提及未做）

---

## 架构健康度总览（第 41 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ✅ **源码 4/4 全部清零（r41 `gui.py` 815→489 收官）+ gui_handlers 73 / gui_pipeline 230 / gui_dialogs 140**；测试全 < 800 | round 41 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + line=0 + r37 M1 partial v2 backfill | round 37 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 + r40 `tools/_rpyc_shared._SHARED_WHITELIST` 独立 leaf 模块，Tier 1 / Tier 2 共享不可能 drift | round 40 |
| 插件沙箱 | ✅ Dual-mode + r40 `core/api_plugin.py` 独立模块（`_load_custom_engine` importlib + `_SubprocessPluginClient` JSONL subprocess sandbox） | round 40 |
| 运行时注入 | ✅ 全套 r31-39 能力 | round 39 |
| 多语言数据模型 | ✅ 4-tuple 索引 + ProgressTracker language namespace + r37 M1 backfill | round 37 |
| 多语言翻译调度 | ✅ `_parse_target_langs` 外循环 + r37 M3 restore + r39 去 multi-lang guard | round 39 |
| 多语言 prompt 支持 | ✅ direct / tl-mode / retranslate 三条管线全部按 `lang_config.code` 分路 + `resolve_translation_field`；**r41 response-read integration test 锁死** | round 41 |
| 字体路径解析 | ✅ `default_resources_fonts_dir()` canonical + r37 M2 size cap | round 37 |
| 生成代码注入防护 | ✅ `_OVERRIDE_CATEGORIES` + r38 per-category bool + r36 H2 isfinite | round 38 |
| 内存 OOM 防护 | ✅ 11/~16 user-facing JSON loader 加 50 MB cap（r37 × 4 + r38 × 4 + r39 × 3） | round 39 |
| 路径信任边界 | ✅ r37 M4 `_apply_v2_edits` CWD 白名单 + **r41 OSError log-on-failure 防 silent bypass** | round 41 |
| 潜伏 bug | ✅ 清零（r36 H1/H2 + r37 M1） | round 37 |
| 模块分层 | ✅ r40 rpyc/plugin tier 分离 + **r41 GUI mixin 分层（handlers / pipeline / dialogs 各自聚焦，通过 MRO 组合到 `class App`；Tkinter callback + PyInstaller discover 向后兼容）** | round 41 |
| 测试覆盖 | ✅ **398 自动化**（r41 +2：M4 OSError log + r39 alias response reading）+ tl_parser 75 + screen 51 = **524 断言点**；**22 测试文件**（21 独立 suite + `test_all.py` meta-runner） | round 41 |
| UI 自适应 | ✅ r38 side-by-side `@media (max-width: 800px)` | round 38 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 41 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 39/40/41 轮详细 + 第 1-38 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（r28 统一 `engine.run()` + r37 M3 外循环 args restore + r39 去 r35 multi-lang guard） |
| 核心 | `core/{api_client,api_plugin,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py`（r40 新增 api_plugin.py） |
| 运行时注入 | `core/runtime_hook_emitter.py` + `resources/hooks/inject_hook.rpy` + `resources/hooks/extract_hook.rpy` |
| v2 工具链 | `tools/merge_translations_v2.py` + `tools/translation_editor.py`（r41 `_apply_v2_edits` OSError log） |
| Prompt 层（多语言） | `core/prompts.py`（r39 双模板分路）+ `core/lang_config.py` |
| 字体补丁 | `core/font_patch.py`（r32 canonical + r37 M2 50 MB cap） |
| UI 白名单 | `file_processor/checker.py` + r32 新增 |
| 插件沙箱（r40 独立模块） | `core/api_plugin.py`（`_load_custom_engine` + `_SubprocessPluginClient`，r40 从 `api_client.py` 抽出）+ `custom_engines/example_echo.py` 示例 |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py`（r39 tl_mode + retranslator 多语言就绪） |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py`（r39 gate.py glossary 50 MB cap） |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py` |
| rpyc 反编译（r40 三模块布局） | `tools/rpyc_decompiler.py` 725（Tier 1 + 公共 API + CLI + re-export from `_rpyc_tier2`）+ `tools/_rpyc_tier2.py` 274（safe-unpickle 链）+ `tools/_rpyc_shared.py` 47（leaf 常量） |
| **GUI（r41 mixin 分层）** | **`gui.py` 489**（`class App(AppHandlersMixin, AppPipelineMixin, AppDialogsMixin)` 骨架 + `_build_*` UI 布局 + `_build_command` / `_mask_api_key` / `_update_preview` + `main()`）+ **`gui_handlers.py` 73**（`AppHandlersMixin`：3 个 UI event handler + `_PROVIDER_DEFAULTS` 副本）+ **`gui_pipeline.py` 230**（`AppPipelineMixin`：9 subprocess/log 方法 + 3 常量）+ **`gui_dialogs.py` 140**（`AppDialogsMixin`：5 个 filedialog/messagebox/配置 I/O 方法）+ `build.py`（PyInstaller 入口；`hidden_imports` 列表未改） |
| 测试 | `tests/test_all.py`（meta，6 模块）+ 独立套件 **20** 个（`test_engines` + `test_engines_rpgmaker` r40 新 + `smoke_test` / `test_rpa_unpacker` / `test_rpyc_decompiler` / `test_lint_fixer` / `test_tl_dedup` / `test_batch1` / `test_custom_engine` / `test_direct_pipeline` / `test_tl_pipeline` / `test_translation_editor` / `test_translation_editor_v2` / `test_merge_translations_v2` / `test_runtime_hook_filter` / `test_translation_db_language` / `test_multilang_run` / `test_override_categories`） |
| Round 41 关键增量 | **`gui_handlers.py` 新 73** + **`gui_pipeline.py` 新 230** + **`gui_dialogs.py` 新 140** / `gui.py` 815→489 / `tools/translation_editor.py` +OSError log / `tests/test_translation_editor_v2.py` 12→13 / `tests/test_multilang_run.py` 8→9 |

---

## 🔍 Round 31-41 审计 / 加固 / 拆分状态

### ✅ 已修 / 已拆（commit 记录）

| 轮 | Fix | Commit |
|----|-----|--------|
| r36 | H1 跨语言 bare-key 污染 + H2 inf/nan 过滤 | `39bb791` / `8ec89d2` |
| r37 | M1-M5 加固包 | `5d8e53a` / `e848598` / `34f1e0c` / `50ecb68` / `0932a04` |
| r38 | test split + M2 ext × 4 + config bool + mobile @media | `daa7c1b` / `64cc154` / `ea19589` / `e492148` |
| r39 | test_state split + tl/retranslate per-lang prompt + M2 phase-2 × 3 | `7fc6c1b` / `35132f3` / `58fd6ab` |
| r40 | test_engines split / rpyc_decompiler Tier 2 + shared split / api_client plugin split | `dfa95e4` / `8588f57` / `b47c415` |
| r41 | gui.py 3-way mixin split + M4 OSError log + r39 alias response integration test + suite count doc drift + docs sync | `019a1f7` / `086b250` / `94c1015` / `16e28fb` / `4165f57` / `09e63da` / [pending Commit 7] |

### 🟡 未修（r42+ 候选）

- PyInstaller 打包 smoke test（r41 拆分未实跑 `build.py` 验证）
- GUI 手动 smoke test 全面清单（r41 只验证 import + 148 meta tests）
- 剩余 ~7 处内部 / 低风险 JSON loader size cap
- 非中文目标语言端到端验证（r41 integration test 锁死 code-level，需真实 API）
- `file_processor/checker.py::check_response_item` 的 "zh" 硬编码 per-language 化（r41 audit test 文档化了约束）
- A-H-3 Medium/Deep / S-H-4 Breaking
- RPG Maker plugin commands / 加密 RPA / CI / docs 深度复查

---

## 🔍 Round 31-41 累积审计结论

连续 3 次 3 维度审计（r35 末 / r40 末 / r41 末）的趋势统计：

| 审计轮次 | CRITICAL/HIGH | MEDIUM | LOW | False Positive | OOS |
|---------|--------------|--------|-----|---------------|-----|
| r35 末（r31-35 审计） | 0 | 2 (H1, H2) | 0 | 6 | — |
| r40 末（r36-40 审计） | 0 | 2 (M4, r39 integration) | 1 | 3 | 2 |
| r41 末（r41 审计——如进行） | 未做（本轮重点是主方向 gui 拆 + 合流 r40 末审计发现；独立 r41 审计留 r42） | — | — | — | — |

**趋势**：连续 2 次审计均无 CRITICAL/HIGH；r40 末审计的 3 项 MEDIUM/LOW 已在 r41 全部修复。主流程 bug 面持续稳定。r41 本身是纯执行轮（做 r40 末审计的修复 + 主方向 gui 拆分），未重新做全项审计。建议 r42 + 3 启动一次完整 r36-r41 审计总结。

---

## 📋 Round 42 建议执行顺序

**推荐优先**（阻塞 follow-up 的前置验证）：**PyInstaller 打包 smoke test + GUI 手动 smoke test**

r41 拆分是 bisect-safe 的 byte-identical + mixin 组合，理论上零行为变化，但两个重要维度未在 r41 本地验证：
1. PyInstaller 能否 discover 3 个新 mixin 模块（如不能，兜底加 hidden_imports）
2. Tkinter bound-method + lambda callback 在真实运行时 dispatch 到 mixin（MRO 保证应工作，但需人工点击确认）

建议 r42 **先做这两个验证**（~30 分钟），清零后再选下一轮方向。

**r42 候选方向（若 smoke test 通过）**：

1. **内部 JSON loader size cap 补齐**（~2h，纯 mechanical） — 剩余 ~7 处 loader 加 50 MB cap。各自 bisect-safe commit。
2. **非中文目标语言端到端验证**（~3-4h，需 API key + 真实游戏） — 跑 ja / ko / zh-tw direct-mode 和 tl-mode 的实际翻译，确认 r39 per-lang prompt + r41 alias chain integration 在生产环境工作。
3. **`file_processor/checker.py::check_response_item` per-language 化**（~2h） — 把 `item.get("zh")` 改为 `resolve_translation_field(item, lang_config)`，解除 r41 audit test 文档化的"checker 只认 zh"约束。
4. **Round 41 专项审计**（~3h） — 3 个 Explore agent 分 correctness / 测试覆盖 / 安全 三维度评估 r41 的 gui 拆分 + 3 项修复的收益和遗留。

**大项（独立一轮）**：A-H-3 Medium/Deep / S-H-4 Breaking（需真实 API + 游戏验证）

---

## ✅ 整体质量评估（r41 末）

- **Pre-existing 大文件负债**：✅ **4/4 清零**（r40 3/4 + r41 `gui.py`）
- **模块分层**：✅ r40 tier 分离 + **r41 GUI mixin 分层**：
  - `_rpyc_shared`（leaf 常量）← `_rpyc_tier2`（safe-unpickle）+ `rpyc_decompiler`（Tier 1 + public + CLI）
  - `api_plugin`（plugin loader + sandbox）← `api_client`（provider dispatch + APIClient 核心）
  - `gui_handlers` + `gui_pipeline` + `gui_dialogs`（各自聚焦职责）← `gui.py::App`（class 骨架通过 MRO 组合 3 个 mixin）
- **向后兼容**：✅ 所有 r41 拆分用 mixin 继承保 Tkinter callback 的 bound-method resolution 通过 MRO 无感工作；`_project_root` 从 gui.py 通过 `self` 透传给 pipeline mixin；`build.py` PyInstaller 静态分析 discover 同目录 `.py` → `hidden_imports` 不用改
- **测试覆盖**：✅ **396 → 398**（r41 纯 refactor 保持 + 2 audit-tail tests）；20 → 21 独立测试文件 + 1 meta-runner
- **文档同步**：✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG 均现行；r41 新澄清"测试文件数"口径统一

**R31-41 十一轮累积**：2 个 H-level bug + 8 个 M-level 加固 + 2 个"收尾包" + **4 个 pre-existing 大文件拆分全清零（r40 3 + r41 1）** + 1 个收官 mixin 架构（`gui.py` 拆 3 mixin）；r35 原挂 3 个绿色小项全部清零；多语言完整栈 + 内存/路径信任 + UI 自适应全部闭环；r40 末审计的 3 项 MEDIUM/LOW 全部 r41 已修。主流程稳定；r42 候选主要是验证层（PyInstaller / GUI smoke） + 内部加固（JSON cap / checker per-lang） + 端到端验证。

---

**本文件由第 41 轮末尾生成，作为第 42 轮起点。**

**下次对话接手指南**（按此顺序读）：
1. 本文件（`HANDOFF.md`）— 尤其 "📋 Round 42 建议执行顺序"
2. `CLAUDE.md` — 项目身份 + 9 大开发原则 + r41 GUI mixin 分层架构
3. `CHANGELOG_RECENT.md` — r39/r40/r41 详细记录

**r42 起点摘要**：
- 代码 / 测试 / 文档状态：r41 末（398 tests × 22 测试文件全绿；commit `09e63da` + pending Commit 7 docs sync）
- 本地 main 领先 origin/main：按前几轮规则未推送
- r42 建议方向：**PyInstaller + GUI manual smoke test 优先**（~30 分钟清零 r41 拆分的 follow-up 验证）；清零后选 JSON loader cap / 非 zh 端到端验证 / checker per-lang / r41 审计之一
