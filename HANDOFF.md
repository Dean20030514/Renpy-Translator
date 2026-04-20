# 交接笔记（第 42 轮结束 → 第 43 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 42 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**405 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 531 断言点）。第 42 轮因 r41 末 HANDOFF 推荐的 PyInstaller smoke test 本地未装 pyinstaller 且不自行 `pip install`、GUI manual smoke 因 agent 环境无人工点击能力，两项都挂起为 r43 human follow-up；按备选短平快方向执行：**内部 JSON loader cap 收尾**（r37-r39 M2 续作 phase-3 补齐 7 处，达到 18/18 user-facing + internal loader 全覆盖）+ **`check_response_item` per-language 化**（解锁 r41 audit test 文档化的 "checker 只认 zh" 约束 + 与 r41 alias-chain integration test 端到端闭环）。5 commits，每 bisect-safe；+7 新 regression tests。所有改动向后兼容：JSON cap 合法 < 50 MB 文件不受影响；checker 新 `lang_config` kwarg 默认 `None` 保 r41 byte-identical。

---

## 第 20 ~ 42 轮成果索引

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
| 42 | 内部 JSON loader cap 收尾（18/18 全覆盖）+ checker per-language 化 | 398 → 405 |

---

## 运行时注入模式全能力（截至 round 42）

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

# Round 39 新：tl-mode / retranslate 非中文目标（r41 alias integration + r42 checker per-lang 已三层锁死）
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --tl-mode --target-lang ja
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --retranslate --target-lang ko

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

**生成的文件清单**（r32-r41 均 opt-in，default 零行为变化）：
- `translations.json` — flat v1 或嵌套 v2 envelope
- `zz_tl_inject_hook.rpy` — 主 hook 脚本（init python early）
- `zz_tl_inject_gui.rpy` — 可选，gui + config override aux 脚本（init 999）
- `ui_button_whitelist.json` — 可选，sidecar
- `fonts/tl_inject.ttf` — 可选，字体 bundle

---

## 推荐的第 43+ 轮工作项

r41 末 HANDOFF 推荐的 PyInstaller smoke test + GUI manual smoke test 两项 r42 未做（pyinstaller 未装 + agent 环境无 GUI 点击能力）— 这两项**仍是 r43 最高优先级**。r42 已把 HANDOFF 备选短平快（JSON cap 收尾 + checker per-lang）做完，项目真正处于 steady-state。

### 🟢 最高优先（r41 末承诺的 follow-up，r43 起步）

**PyInstaller 打包 smoke test + hidden-imports 兜底（~30 分钟）**

```bash
pip install pyinstaller           # ~100 MB 下载，需用户 approve
python build.py                   # 尝试打包
./dist/多引擎游戏汉化工具.exe     # 启动 smoke
```
若打包 fail 或启动 `ModuleNotFoundError`：
```python
# build.py::hidden_imports 追加
"gui_handlers", "gui_pipeline", "gui_dialogs",
```
3 行 fix + 一次验证。

**GUI 手动 smoke test 全面清单（需人工）**

- `python gui.py` 启动
- 切换"基本设置"引擎下拉 → 面板切换
- 切换提供商 → 模型自动更新
- 切换 Ren'Py 翻译模式 → tl 语言字段启用/禁用、pipeline 参数 show/hide
- 填虚拟 game_dir + API key → 点"开始翻译" 验证 warning
- 点"停止" / "清空日志"
- 工具菜单 Dry-run / 升级扫描
- 配置保存 / 加载

若任一 callback 不工作（MRO dispatch 错位），回退到单文件或重新调整 mixin 继承顺序。

### 🟡 备选短平快（~2-3h 一轮）

1. **非中文目标语言端到端验证**（需真实 API + 真实游戏） — r39 prompt + r41 alias + r42 checker 三层 code-level contract 已全部锁死，需生产验证 ja / ko / zh-tw 实际翻译质量
2. **Round 42 专项审计**（~3h） — 3 个 Explore agent 分 correctness / 测试覆盖 / 安全三维度评估 r42 JSON cap + checker per-lang 的收益、遗留、潜在 bug
3. **`core/translation_db.py::schema v3`** 或 **`file_processor/patcher.py` Ren'Py 8 tag alias 扩展** 等其他小项

### 🟠 延续未做的深度重构（需真实 API + 游戏验证）

**A-H-3 Medium / Deep**：当前 A-H-3 只做 Minimal。Medium（adapter 层让 Ren'Py 走 generic_pipeline 6 阶段）或 Deep（完全退役 DialogueEntry）。

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
  （连续 13 轮被提及未做）

---

## 架构健康度总览（第 42 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ✅ **源码 4/4 全部清零**（r41 `gui.py` 815→489）；测试全 < 800 | round 41 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + line=0 + r37 M1 partial v2 backfill | round 37 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 + r40 `tools/_rpyc_shared._SHARED_WHITELIST` 独立 leaf 模块 | round 40 |
| 插件沙箱 | ✅ Dual-mode + r40 `core/api_plugin.py` 独立模块 | round 40 |
| 运行时注入 | ✅ 全套 r31-39 能力 | round 39 |
| 多语言数据模型 | ✅ 4-tuple 索引 + ProgressTracker language namespace + r37 M1 backfill | round 37 |
| 多语言翻译调度 | ✅ `_parse_target_langs` 外循环 + r37 M3 restore + r39 去 multi-lang guard | round 39 |
| 多语言 prompt 支持 | ✅ direct / tl-mode / retranslate 三条管线全部按 `lang_config.code` 分路 + `resolve_translation_field`；r41 response-read integration 锁死 | round 41 |
| **多语言 checker 支持** | ✅ **r42 `check_response_item` + `_filter_checked_translations` 加 `lang_config` kwarg；alias chain via `resolve_translation_field`；r27 A-H-2 layering 保留（deferred import）** | round 42 |
| 字体路径解析 | ✅ `default_resources_fonts_dir()` canonical + r37 M2 size cap | round 37 |
| 生成代码注入防护 | ✅ `_OVERRIDE_CATEGORIES` + r38 per-category bool + r36 H2 isfinite | round 38 |
| **内存 OOM 防护** | ✅ **18/18 JSON loader 加 50 MB cap**（r37 × 4 + r38 × 4 + r39 × 3 user-facing + r41 保持 + r42 × 7：rpgm × 2 / progress × 3 / reports × 2）— **全覆盖** | round 42 |
| 路径信任边界 | ✅ r37 M4 `_apply_v2_edits` CWD 白名单 + r41 OSError log-on-failure | round 41 |
| 潜伏 bug | ✅ 清零（r36 H1/H2 + r37 M1） | round 37 |
| 模块分层 | ✅ r40 rpyc/plugin tier + r41 GUI mixin 分层；r42 checker 多语言化保 r27 A-H-2 core→file_processor 单向层次 | round 42 |
| 测试覆盖 | ✅ **405 自动化**（r42 +7：rpgm oversize +1 / progress oversize +1 / checker per-language +5）+ tl_parser 75 + screen 51 = **531 断言点**；**22 测试文件**（21 独立 suite + `test_all.py` meta-runner） | round 42 |
| UI 自适应 | ✅ r38 side-by-side `@media (max-width: 800px)` | round 38 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 42 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 40/41/42 轮详细 + 第 1-39 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py` |
| 核心 | `core/{api_client,api_plugin,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py`（r42 `translation_utils.py` +_MAX_PROGRESS_JSON_SIZE） |
| 运行时注入 | `core/runtime_hook_emitter.py` + `resources/hooks/inject_hook.rpy` + `resources/hooks/extract_hook.rpy` |
| v2 工具链 | `tools/merge_translations_v2.py` + `tools/translation_editor.py`（r41 `_apply_v2_edits` OSError log） |
| Prompt 层（多语言） | `core/prompts.py`（r39 双模板分路）+ `core/lang_config.py`（`resolve_translation_field` 被 r41 tl_mode + r42 checker 共用） |
| **checker（r42 多语言化）** | **`file_processor/checker.py::check_response_item`** + **`_filter_checked_translations`** 加 `lang_config: "object | None" = None` kwarg；deferred `from core.lang_config import resolve_translation_field` 保 r27 A-H-2 |
| 字体补丁 | `core/font_patch.py` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py`（r42 `_screen_patch.py` +_MAX_PROGRESS_JSON_SIZE） |
| **引擎抽象层（r42 cap）** | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py`（**r42 `rpgmaker_engine.py` +_MAX_RPGM_JSON_SIZE × 2 sites；`generic_pipeline.py` +_MAX_PROGRESS_JSON_SIZE + checker lang_config pass-through**） |
| **流水线（r42 cap）** | **`pipeline/{helpers,gate,stages}.py`（`stages.py` +_MAX_REPORT_JSON_SIZE × 2 sites）** |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py`（r42 `checker.py` per-language） |
| rpyc 反编译（r40 三模块布局） | `tools/rpyc_decompiler.py` 725 + `tools/_rpyc_tier2.py` 274 + `tools/_rpyc_shared.py` 47 |
| GUI（r41 mixin 分层） | `gui.py` 489 + `gui_handlers.py` 73 + `gui_pipeline.py` 230 + `gui_dialogs.py` 140 |
| 测试 | `tests/test_all.py`（meta，6 模块）+ 独立套件 **21** 个 |
| **Round 42 关键增量** | **6 代码**（`engines/rpgmaker_engine.py` +cap × 2 / `engines/generic_pipeline.py` +cap + checker pass-through / `core/translation_utils.py` +cap / `translators/_screen_patch.py` +cap / `pipeline/stages.py` +cap × 2 / `file_processor/checker.py` +lang_config kwarg × 2 + deferred import / `translators/tl_mode.py` checker pass-through）+ **3 测试**（test_engines_rpgmaker +1 / test_translation_state +1 / test_multilang_run +5） |

---

## 🔍 Round 31-42 审计 / 加固 / 拆分状态

### ✅ 已修 / 已拆（commit 记录）

| 轮 | Fix | Commit |
|----|-----|--------|
| r36 | H1 跨语言 bare-key 污染 + H2 inf/nan 过滤 | `39bb791` / `8ec89d2` |
| r37 | M1-M5 加固包 | `5d8e53a` / `e848598` / `34f1e0c` / `50ecb68` / `0932a04` |
| r38 | test split + M2 ext × 4 + config bool + mobile @media | `daa7c1b` / `64cc154` / `ea19589` / `e492148` |
| r39 | test_state split + tl/retranslate per-lang prompt + M2 phase-2 × 3 | `7fc6c1b` / `35132f3` / `58fd6ab` |
| r40 | test_engines split / rpyc_decompiler Tier 2 + shared split / api_client plugin split | `dfa95e4` / `8588f57` / `b47c415` |
| r41 | gui.py 3-way mixin split + M4 OSError log + r39 alias response integration test + suite count doc drift + docs sync | `019a1f7` / `086b250` / `94c1015` / `16e28fb` / `4165f57` / `09e63da` / `a38f6e1` |
| r42 | rpgm JSON cap / 3 progress loaders cap / 2 pipeline report loaders cap / checker per-language / docs sync | `9726113` / `13ac6e3` / `8ed99d9` / `d0404ff` / [pending Commit 5] |

### 🟡 未修（r43+ 候选）

- PyInstaller 打包 smoke test（r41/r42 两轮积压，需 pip install + 用户 approve）
- GUI 手动 smoke test 全面清单（r41/r42 两轮积压，需人工点击）
- 非中文目标语言端到端验证（r39 prompt + r41 alias + r42 checker 三层锁死 code-level，需真实 API）
- A-H-3 Medium/Deep / S-H-4 Breaking
- RPG Maker plugin commands / 加密 RPA / CI / docs 深度复查（13 轮欠账）

---

## 🔍 Round 42 审计情况

r42 本身是纯执行轮（做 r41 末 HANDOFF 推荐的 JSON cap + checker per-lang），未重新做全项审计。连续 3 次 3 维度审计（r35 末 / r40 末 / r41 末 skip）统计详见 r41 HANDOFF 末。建议 r43 起启动一次完整 r36-r42 审计总结。

---

## 📋 Round 43 建议执行顺序

**推荐优先**（r41/r42 两轮积压的 follow-up）：**PyInstaller 打包 smoke test + GUI manual smoke test**

这是 r41 拆分 `gui.py` 815→489 为 3 mixin 的生产验证，r42 也因环境无 pyinstaller 未做。两项都是 30 分钟级别工作，能解锁：
1. 确认 PyInstaller 能 auto-discover 同目录 `gui_handlers.py` / `gui_pipeline.py` / `gui_dialogs.py`（如不能，加 3 行 hidden_imports 到 `build.py`）
2. 确认 Tkinter bound-method + lambda callback 在 mixin MRO 下真实运行时正确 dispatch（r41/r42 仅 `import gui` smoke + 测试验证，未在真实运行时点击）

**r43 候选方向（若 smoke test 通过）**：

1. **非中文目标语言端到端验证**（需 API key + 真实游戏，~3-4h） — r39 prompt + r41 alias chain + r42 checker per-lang 三层锁死 code-level contract，需生产跑 ja / ko / zh-tw 的实际翻译质量
2. **Round 42 专项审计**（~3h，无需 API） — 3 个 Explore agent 分 correctness / 测试覆盖 / 安全三维度评估 r42 的 JSON cap + checker per-lang 的收益、遗留 bug、潜在风险
3. **CI Windows runner 搭建**（~4h） — 13 轮欠账的架构基础设施

**大项（独立一轮）**：A-H-3 Medium/Deep / S-H-4 Breaking（需真实 API + 游戏验证）

---

## ✅ 整体质量评估（r42 末）

- **JSON Loader OOM 防护**：✅ **18/18 全覆盖**（r37-r41 × 11 + r42 × 7）；所有已识别 user-facing + internal JSON loader 全部加 50 MB cap
- **多语言端到端**：✅ prompt 层（r39）→ alias response-read（r41）→ **checker validation（r42）** 三层全部按 `lang_config.field_aliases` 解析；r39 workaround path 变为整洁路径，checker 不再硬编码 `"zh"`
- **向后兼容**：✅ 所有 r42 改动 `lang_config=None` 默认保 r41 byte-identical；合法 < 50 MB 文件不受 JSON cap 影响
- **r27 A-H-2 layering**：✅ `file_processor/checker.py` 新增的 `core.lang_config` import 是 deferred（仅 `if lang_config is not None:` 分支触发），`file_processor` 仍不在 module load 时 import `core`
- **测试覆盖**：✅ 398 → 405（+7 r42 new tests；22 测试文件）
- **文档同步**：✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG 均现行

**R31-42 十二轮累积**：2 个 H-level bug + 8 个 M-level 加固 + 2 个"收尾包" + 4 个 pre-existing 大文件拆分全清零（r40 × 3 + r41 × 1）+ 1 个 GUI mixin 收官 + **r42 两项收尾**（JSON cap 18/18 + checker per-lang）；r35 原挂 3 个绿色小项全部清零；多语言完整栈（prompt + alias + checker）三层锁死；内存/路径信任 + UI 自适应全部闭环。主流程稳定；r43 候选主要是**验证层**（PyInstaller / GUI smoke，两轮积压）+ 非 zh 端到端 + 审计。

---

**本文件由第 42 轮末尾生成，作为第 43 轮起点。**

**下次对话接手指南**（按此顺序读）：
1. 本文件（`HANDOFF.md`）— 尤其 "📋 Round 43 建议执行顺序"
2. `CLAUDE.md` — 项目身份 + 9 大开发原则 + r41 GUI mixin 分层 + r42 JSON cap 全覆盖 + checker per-lang
3. `CHANGELOG_RECENT.md` — r40/r41/r42 详细记录

**r43 起点摘要**：
- 代码 / 测试 / 文档状态：r42 末（405 tests × 22 测试文件全绿）
- r43 建议方向：**PyInstaller + GUI manual smoke test 优先**（~30 分钟清零 r41/r42 两轮积压的 follow-up 验证）；清零后选非 zh 端到端 / r42 审计 / CI runner 之一
