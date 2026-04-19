# 交接笔记（第 32 轮结束 → 第 33 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 32 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**326 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 452 断言点）。第 32 轮一次性清掉 HANDOFF round 31 挂起的三项"延续小项"：`--ui-button-whitelist` 通过 sidecar JSON 把 UI 按钮扩展同步到 hook、`--emit-runtime-hook` 自动把字体打包为 `game/fonts/tl_inject.ttf`、`--runtime-hook-schema v2` 产出嵌套多语言 translations.json。同步顺手修了 2 个遗留的 `Path(__file__).parent` 少一层 parent bug（`translators/direct.py:523` + `translators/_tl_patches.py:88`，与 round 29 修的 `patch_font_now.py` 同类），抽出 `core.font_patch.default_resources_fonts_dir()` canonical helper 防止再次漂移。所有新 flag default off，既有 tl-mode / direct-mode / retranslate / screen 行为逐字节不变。

---

## 第 20 ~ 32 轮成果索引

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

---

## 运行时注入模式全能力（截至 round 32）

**何时用**：当静态 `.rpy` 改写不可行时（游戏发布方不允许分发修改后的源文件 / 想保留原始游戏完整性 / 需要给用户"一个补丁包"而非"一个修改版游戏"）。

**启用方式**（所有 opt-in）：
```bash
# 基础：生成 translations.json + zz_tl_inject_hook.rpy
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --emit-runtime-hook

# 扩展：UI 按钮白名单 + v2 多语言 schema + 字体自动打包
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --emit-runtime-hook \
    --ui-button-whitelist custom_ui.txt extra_ui.json \
    --runtime-hook-schema v2 \
    --target-lang zh \
    --font-file /path/to/CustomFont.ttf

# 使用时把生成的文件拖到游戏 game/ 目录，然后设置环境变量启动：
RENPY_TL_INJECT=1 ./game.exe
# v2 schema 下还可以指定运行时语言：
RENPY_TL_INJECT=1 RENPY_TL_INJECT_LANG=zh-tw ./game.exe
```

**生成的文件清单**：
- `translations.json` — flat v1 或嵌套 v2 envelope
- `zz_tl_inject_hook.rpy` — hook 脚本
- `ui_button_whitelist.json` — 可选，sidecar，round 32 新增
- `fonts/tl_inject.ttf` — 可选，字体 bundle，round 32 新增

**不启用 `--emit-runtime-hook` 时**：完全与 round 30 之前一样，静态改写流程一字不差。round 32 新增三个 flag 全部 opt-in，default 零行为变化。

---

## 推荐的第 33+ 轮工作项

HANDOFF round 31 挂起的三项绿色小项（🟢）已全部完成于 round 32。Priority A + B 清零持续 4 轮；项目仍处于 steady-state。

### 🟢 自然延续 round 32 方向（小项）

**(1) v2 schema 多语言 merge 工具**：当前 v2 单次运行只填一个 language bucket（由 `--target-lang` 决定）。实现一个独立 tool（例如 `tools/merge_translations_v2.py`）把多次运行的 v2 envelope 合并成 `{en: {zh, zh-tw, ja}}`，让用户一次部署支持多语言切换。~2-3h。

**(2) `--font-config` 透传到 runtime hook**：当前字体打包只拷贝 `.ttf` 文件，没有把 `font_config.json` 中的 `gui_overrides`（字号 / 布局参数）传给 hook。需 hook 端读 sidecar config，然后调 `config.font_replacement_map` 之外再设置 gui 参数。~1-2h。

**(3) `translation_editor` HTML 校对页适配 v2 schema**：当前 editor 读 flat `{en: zh}`。若 v2 普及需要 editor 支持多 language 切换编辑。~3-4h。

### 🟠 延续未做的深度重构

**A-H-3 Medium / Deep**：当前 A-H-3 只做 Minimal（入口统一）。Medium（adapter 层，让 Ren'Py 走 generic_pipeline 6 阶段）或 Deep（完全退役 DialogueEntry）。需真实 API + 真实游戏验证。

**S-H-4 Breaking**：强制所有插件走 subprocess，retire importlib 路径。目前 dual-mode 已经稳定。

**`TranslationDB.entries` 加 `language` 字段**：当前 DB 按项目单次运行只存一个翻译方向；v2 schema 是在 emit 层手工指定 language key 拼装出来的。若要真实支持多语言翻译（同游戏一次运行生成 zh+zh-tw+ja），DB schema 要扩展。~3-5h 含数据迁移。

### 🟡 新功能 / 扩展（Priority C）

- RPG Maker Plugin Commands / JS 硬编码支持
- 加密 RPA / RGSS 归档
- CSV/JSONL engine 完善

### 🔴 监控项（暂不修）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 理论链式攻击
- HTTP 响应体 64 KB 精度偏差

### ⚫ 外部基础设施（AI 独立推不动）

- CI Windows runner
- docs/constants.md / docs/quality_chain.md / docs/roadmap.md 深度复查（连续 3 轮被提及未做）

---

## 架构健康度总览（第 32 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ✅ 零（源码最大 direct.py 601；checker.py 约 615；inject_hook.rpy 约 345） | round 32 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + 接受 line=0 | round 26 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 | round 20/26 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in + 10 KB stderr 上限 | round 28/30 |
| 运行时注入 | ✅ `--emit-runtime-hook` 基础（round 31）+ UI whitelist sidecar / 字体 bundle / v2 多语言 schema（round 32） | round 32 |
| 字体路径解析 | ✅ 全部走 `core.font_patch.default_resources_fonts_dir()` canonical helper，2 处遗留 bug 已修 | round 32 |
| 潜伏 bug | ✅ 清零（round 28/29/30/32 陆续扫清）| round 32 |
| 测试覆盖 | ✅ **326 自动化** + tl_parser 75 + screen 51 = **452 断言点** | round 32 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 32 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 30/31/32 轮详细 + 第 1-29 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（统一 `engine.run()` 分派）/ `one_click_pipeline.py` / `gui.py` / `start_launcher.py` |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py` |
| 运行时注入 | `core/runtime_hook_emitter.py`（r31 基础 + r32 UI sidecar / 字体 bundle / v2 schema）+ `resources/hooks/inject_hook.rpy`（r31 基础 + r32 sidecar reader + v2 reader + env var 语言选择）+ `resources/hooks/extract_hook.rpy`（已有） |
| 字体补丁 | `core/font_patch.py::default_resources_fonts_dir`（r32 canonical 出口）+ `resolve_font` + `apply_font_patch` |
| UI 白名单 | `file_processor/checker.py::COMMON_UI_BUTTONS`（baseline）+ `_ui_button_extensions` + `load_ui_button_whitelist`（r32） |
| 插件沙箱 | `core/api_client._SubprocessPluginClient`（S-H-4）+ `custom_engines/example_echo.py::_plugin_serve` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py`（checker 含 round 27 下沉 + round 31 / 32 新增） |
| 测试 | `tests/test_all.py`（meta）+ 5 个拆分（test_api_client / test_file_processor / test_translators / test_glossary_prompts_config / test_translation_state）+ 其他 8 个独立套件 |

---

**本文件由第 32 轮末尾自动生成，作为第 33 轮起点。**
