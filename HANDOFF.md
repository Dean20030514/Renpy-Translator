# 交接笔记（第 31 轮结束 → 第 32 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 31 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**307 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**。第 31 轮从闭源竞品（"刺客边风"v1.5.2）的 737 行 Ren'Py 运行时 hook 中提炼 3 项可移植技巧整合进 checker/fallback 层，并新增 `--emit-runtime-hook` opt-in 开关 + `resources/hooks/inject_hook.rpy` 模板，形成与现有 extract_hook 的闭环。所有改动 default off，不影响现有行为。

---

## 第 20 ~ 31 轮成果索引

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

---

## 本轮新增的运行时注入模式（round 31 Tier B + C）

**何时用**：当静态 `.rpy` 改写不可行时（游戏发布方不允许分发修改后的源文件 / 想保留原始游戏完整性 / 需要给用户"一个补丁包"而非"一个修改版游戏"）。

**启用方式**：
```bash
# 除了静态输出外，同时生成 translations.json + zz_tl_inject_hook.rpy
python main.py --game-dir /path/to/game --provider xai --api-key KEY \
    --emit-runtime-hook

# 使用时把这两个文件拖到游戏的 game/ 目录，然后设置环境变量启动：
RENPY_TL_INJECT=1 ./game.exe
```

**不启用时**：完全与 round 30 之前一样，静态改写流程一字不差。

---

## 推荐的第 32+ 轮工作项

HANDOFF Priority A + B 清空已维持 3 轮。项目维持 steady-state，新功能轴出现。

### 🟢 延续 round 31 方向（小项）

**(1) `COMMON_UI_BUTTONS` 可配置化**：当前硬编码 30 个通用 UI 词。真实游戏可能有自定义 UI（中文游戏的"存档"/"读档"/"选项"等），应允许通过 glossary 或新 `--ui-button-whitelist` flag 扩展。~1-2h。

**(2) `inject_hook.rpy` 字体自动打包**：目前字体替换只在 `game/fonts/tl_inject.ttf` 存在时触发。可在 `emit_runtime_hook` 里顺便拷贝字体文件（配合 `--font-file` / resources/fonts 查找逻辑）。~1h。

**(3) `translations.json` 支持多语言 schema**：当前 flat `{en: zh}`，可扩展为 `{en: {zh, zh-tw, ja}}` 支持同一游戏多语言切换。涉及 hook + emitter + TranslationDB，~3-4h。

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

---

## 架构健康度总览（第 31 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ✅ 零（源码最大 direct.py 601；hooks 最大 inject_hook.rpy 270）| round 31 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + 接受 line=0 | round 26 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 | round 20/26 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in + 10 KB stderr 上限 | round 28/30 |
| 运行时注入 | ✅ `--emit-runtime-hook` opt-in + extract/inject 闭环 | round 31 |
| 潜伏 bug | ✅ 清零（round 28/29/30 陆续扫清）| round 30 |
| 测试覆盖 | ✅ 307 自动化 + tl_parser 75 + screen 51 = 433 断言点 | round 31 |
| 文档同步 | ✅ CLAUDE / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 31 |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 29/30/31 轮详细 + 第 1-28 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（统一 `engine.run()` 分派）/ `one_click_pipeline.py` / `gui.py` / `start_launcher.py` |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py` |
| 运行时注入 | `core/runtime_hook_emitter.py`（round 31）+ `resources/hooks/inject_hook.rpy`（round 31）+ `resources/hooks/extract_hook.rpy`（已有） |
| 插件沙箱 | `core/api_client._SubprocessPluginClient`（S-H-4）+ `custom_engines/example_echo.py::_plugin_serve` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py`（checker 含 round 27 下沉 + round 31 新增） |
| 测试 | `tests/test_all.py`（meta）+ 5 个拆分 + 其他 8 个独立套件 |

---

**本文件由第 31 轮末尾自动生成，作为第 32 轮起点。**
