# CHANGELOG v2

本文档记录本轮对「Renpy汉化（我的）」项目的全部改动。
按迭代轮次组织，每轮按类型（功能 / 增强 / 修复）分组。

---

## 改动总览

| 轮次 | 主题 | 核心成果 |
|------|------|----------|
| 第一轮 | 质量校验体系 | W430/W440/W441/W442/W251 告警 + E411/E420 术语锁定 |
| 第二轮 | 功能增强 | 结构化报告 + translation_db + 字体补丁 |
| 第三轮 | 降低漏翻率 | 12.12% → 4.01%（占位符保护 + 密度自适应 + retranslate） |
| 第四轮 | tl-mode | 独立 tl_parser 解析器 + 并发翻译 + 精确回填 |
| 第五轮 | tl-mode 全量验证 | 引号剥离修复 + 后处理 + 99.97% 翻译成功率 |
| 第六轮 | 代码优化与新功能 | chunk重试 + logging + 模块拆分 + 术语提取 + 退避优化 + show修复 + 全文扫描安全性 + 截断阈值提升 + tl_parser 测试扩充 |
| 第七轮 | 全量验证（第六轮改进） | 99.99% 成功率（未翻译 25→7，Checker 丢弃 4→2）；9 条遗漏全为边界 case |
| 第八轮 | 代码质量八阶段优化 | 消除重复 + 大函数拆分 + validator 结构化 + Magic Number 收敛 + except 精细化 + 测试 36→42 + LICENSE/pyproject.toml + CI 增强 |
| 第九轮 | 深度优化六阶段 | 线程安全修复 + 深层重复消除(`_filter_checked`/`_deduplicate`) + 性能O(1)fallback + API 404/401/推理timeout + 测试 42→50 + `has_entry`封装 |
| 第十轮 | 功能加固与生态完善 | 控制标签覆盖确认 + CI零依赖+dry-run + 跨平台路径 + Glossary连字符+信心度 + getpass安全输入 + README故障排查/调优/示例 + 测试 50→53 |
| 第十一轮 阶段一 | main.py 模块拆分 | main.py 2400→233 行，拆分为 direct_translator / retranslator / tl_translator / translation_utils 四个独立模块 + TranslationContext 闭包重构 |
| 第十一轮 阶段二+三 | 回写失败分析与修复 | diagnostic 记录 + analyze 工具 + 前缀剥离 + 转义引号正则 + 回写失败 609→28→~0 + 测试 53→55 |
| 第十一轮 阶段四 | config.json 配置文件 | Config 类（三层合并）+ resolve_api_key + renpy_translate.example.json + argparse default=None + 测试 55→58 |
| 第十一轮 阶段五 | Review HTML + 进度条 | ProgressBar（GBK/ASCII 自适应）+ review_generator.py（HTML 校对报告）+ direct_translator 集成 + 测试 58→60 |
| 第十一轮 阶段六 | 类型注解 | 全部公共 API 返回/参数注解 + py.typed PEP 561 + CI mypy informational |
| 第十一轮 阶段七 | 目标语言参数化 | LanguageConfig dataclass + 4 预置语言 + 文字检测 + resolve_translation_field + 测试 60→63 |
| 第十一轮 阶段八 | Prompt + Validator 多语言 | 中文/英文 prompt 分支 + W442 参数化 + 中文零变更验证 + 测试 63→66 |
| 第十二轮 | 阶段零四项优化 | chunk 截断自动拆分重试 + pipeline main() 拆分 + .rpyc 精确清理 + dry-run verbose 增强 + 测试 66→70 |
| 第十二轮 阶段一 | 引擎抽象层骨架 | EngineProfile + TranslatableUnit + EngineBase ABC + EngineDetector + RenPyEngine 薄包装 + `--engine` CLI + 引擎测试 25 个 |
| 第十二轮 阶段二 | CSV/JSONL + 通用流水线 | CSVEngine（CSV/TSV/JSONL/JSON 读写）+ generic_pipeline（6 阶段通用翻译）+ checker/prompts 参数化适配 + 引擎测试 25→47 |
| 第十二轮 阶段三 | RPG Maker MV/MZ | RPGMakerMVEngine（事件指令 401/405 合并 + 102 选项 + 8 种数据库 + System.json）+ glossary.scan_rpgmaker_database + 引擎测试 47→62 |
| 第十二轮 阶段四 | 文档 + 发布 | start_launcher.py 新增模式 8/9（RPG Maker / CSV）+ 全部文档更新 + 里程碑 M4 达成 |
| 第十二轮 结构整理 | 项目目录重构 | 根目录 .py 27→17：测试→tests/ + 工具→tools/ + 引擎抽象→engines/ 包合并 + import 路径更新 |
| 第十二轮 GUI | 图形界面 + 打包 | gui.py Tkinter GUI（3 Tab + 内嵌日志 + 命令预览 + 配置加载）+ build.py PyInstaller 打包（32MB 单文件 .exe） |
| 第十三轮 | 四项功能优化 | pipeline 集成 review.html + font_config.json 可配置 + tl/none 覆盖模板（不修改 gui.rpy）+ CoT 思维链翻译（`--cot`） |
| 第十四轮 | 全面优化（Ren'Py 专项） | 五阶段升级：基础重构 + 代码健壮性 + 性能优化 + 翻译质量 + 用户体验 |
| 第十五轮 | nvl clear 翻译 ID 修正 | `fix_nvl_translation_ids` 自动检测 8.6+ say-only 哈希并修正为 7.x nvl+say 哈希 + 管道集成 + 测试 71→75 |
| 第十六轮 | screen 文本翻译 + 缓存清理修复 | `screen_translator.py` screen 裸英文翻译（`--tl-screen`，含 text/textbutton/tt.Action/Notify 四模式）+ `_should_skip` 标签误杀修复 + 缓存清理 .rpymc 补全 + 流水线/启动器/打包集成 + 测试 75→87 |
| 第十七轮 | 项目结构深度重构 | 根目录 25→5 .py：core/(7模块) + translators/(6模块) + tools/(扩充3模块)，消除 re-export 兼容层 + 循环依赖，162 测试全绿 |
| 第十八轮 | 预处理工具链 + 翻译增强 | RPA 解包 + rpyc 反编译（双层策略）+ Ren'Py lint 集成 + 文件级并行翻译 + locked_terms 预替换 + 跨文件去重 + Hook 模板，测试 162→225 |
| 第十九轮 | 翻译后工具链 + 插件系统 | RPA 打包 + HTML 交互式校对 + 自定义翻译引擎 + 默认语言设置 + Lint 流水线集成 + JSON 解析失败拆分重试，测试 225→267 |
| 第二十轮 | CRITICAL 修复 + 治理文档 | pipeline 悬空 import 三处 + pickle RCE 三处（白名单）+ ZIP Slip 防护 + CONTRIBUTING/SECURITY，测试 266→280 |
| 第二十一轮 | Top 5 HIGH 收敛 | HTTP 连接池（~90s 节省）+ ProgressTracker 双锁解串行 + API Key 走 subprocess env + HTTP 重试 mock + P1 快照单调性，测试 280→286 |
| 第二十二轮 | 测试基础 + 响应体上限 | `MAX_API_RESPONSE_BYTES = 32MB` + `read_bounded` 共享工具 + T-C-3 direct_pipeline + T-H-2 tl_pipeline 集成测试，测试 286→286 |
| 第二十三轮 | A-H-4 Part 1 | `translators/direct.py` 1301→584 + 子模块 `_direct_chunk` / `_direct_file` / `_direct_cli`，286 测试零回归 |
| 第二十四轮 | A-H-4 Part 2 | `translators/tl_mode.py` 928→558 + `tl_parser.py` 1106→532 + 子模块拆分，286 测试零回归 |
| 第二十五轮 | 七项 HIGH/MEDIUM 收敛 | A-H-1 尾巴 + A-H-6 UsageStats.to_dict + S-H-3 api_key_file 校验 + PF-H-2 direct log 句柄 + PF-C-2 validator 正则预编译 + T-H-1/T-H-3 新测试，测试 286→288 |
| 第二十六轮 | 综合包 A+B+C | TranslationDB 三件套（RLock + 原子写 + line=0 + dirty flag）+ RPA 大小检查 + RPYC 白名单同步 + stages/gate 可见化 + screen.py 拆分 + quality_report 加锁 + patcher 反向索引 + RateLimiter 批量清理，测试 288→293 |
| 第二十七轮 | 分层收尾 | A-H-2 3 wrapper 下沉 `file_processor/checker.py` + A-H-5 `tools/font_patch.py` → `core/font_patch.py`，测试 293 保持 |
| 第二十八轮 | A-H-3 Minimal 路由 + S-H-4 Dual-mode 插件沙箱 | `main.py` 潜伏 `os` bug 修复 + `--sandbox-plugin` opt-in，测试 293→301 |
| 第二十九轮 | Priority B 持续优化 | `tests/test_all.py` 2539 拆为 5 聚焦 suite + 49 行 meta-runner（113 tests/1 命令）+ `tools/patch_font_now.py:27` bug 修复 + TEST_PLAN/dataflow_pipeline 刷新，测试 301 保持 |
| 第三十轮 | 冷启动审计 4 项 | `_SubprocessPluginClient` stderr 10 KB 上限 + Popen atexit 兜底 + http_pool except 收窄 + retranslator.quality_report 死代码清理，测试 301→302 |
| 第三十一轮 | 竞品 hook_template 3 技巧 | checker UI 白名单 / 占位符漂移修正 / strip_tags L5 fallback + inject_hook.rpy 模板 + `--emit-runtime-hook` CLI，测试 302→307 |
| 第三十二轮 | UI 白名单 + v2 schema + 字体打包 + gui/config override | sidecar JSON 可配置 + `--runtime-hook-schema v2` 嵌套多语言 + emit 时拷 `tl_inject.ttf` + `zz_tl_inject_gui.rpy` init 999 覆盖 + Commit 1 prep（`default_resources_fonts_dir` helper 修 2 处 `__file__.parent` bug），测试 307→326 |
| 第三十三轮 | v2 多语言工具链补齐 | `merge_translations_v2.py` 合并工具 + `--font-config` 透传 runtime hook + `translation_editor.py` v2 envelope 适配 + 拆 `test_translation_state.py` 运行时 hook 测试到新 `test_runtime_hook.py`，测试 326→346 |
| 第三十四轮 | TranslationDB schema v2 + 多语言 | `language` 字段 + 4-tuple 索引 + `has_entry`/`filter_by_status`/`upsert_entry` language-aware + editor HTML dropdown 多语言切换 + `_OVERRIDE_CATEGORIES` 泛化，测试 346→363 |
| 第三十五轮 | 多语言外循环 + side-by-side | `ProgressTracker` language namespace + `--target-lang zh,ja,zh-tw` 逗号分隔 + main.py 外层循环 + editor checkbox 切换 side-by-side 多列 + `_OVERRIDE_CATEGORIES` 注册 `config_overrides`，测试 363→376 |
| 第三十六轮 | 深度审计 H1+H2 | H1 跨语言 bare-key 污染 + H2 `_sanitise_overrides` isfinite 过滤，测试 376→378 |
| 第三十七轮 | M 级防御加固包 M1-M5 | M1 TranslationDB.load() partial v2 backfill + M2 4 处 JSON loader 50 MB cap + M3 main.py try/finally restore + M4 CWD path whitelist + M5 empty-cell SKIP 语义，测试 378→385 |
| 第三十八轮 | "收尾包"一轮清 | 拆 test_translation_editor.py 847→376 + 新 test_translation_editor_v2.py + M2 扩 4 处 + `config_overrides` 扩 bool + editor side-by-side mobile @media，测试 385→391 |
| 第三十九轮 | "收尾包 Part 2" | 拆 test_translation_state.py 850→681 + tl-mode/retranslate per-lang prompt（r35 挂起绿色小项）+ M2 phase-2 × 3，测试 391→396 |
| 第四十轮 | pre-existing 大文件拆 3/4 | `tests/test_engines.py` 962→694 + `tools/rpyc_decompiler.py` 974→725 + `core/api_client.py` 965→642；`gui.py` 815 挂 r41，纯 refactor 396 保持 |
| 第四十一轮 | gui.py 拆 4/4 mixin 收官 + 3 项审计尾巴 | `gui.py` 815→489 拆为 `gui_handlers.py`/`gui_pipeline.py`/`gui_dialogs.py`（MRO mixin 架构）+ M4 OSError warning log + r39 alias integration test + suite count 口径统一，测试 396→398 |
| 第四十二轮 | 内部 JSON loader cap 收尾 + checker per-language 化 | rpgm × 2 + 3 progress + 2 pipeline reports cap（原声称 18/18）+ `check_response_item` `lang_config` kwarg + 调用点透传 + 5 regression tests，测试 398→405 |
| 第四十三轮 | r36-r42 累计三维度专项审计 | 3 audit agent（correctness/tests/security）发现 3 test gap（zh-tw / mixed-lang / stat fallback）+ 1 defensive（plugin stdout 50 MB cap），0 CRITICAL/HIGH，测试 405→409 |
| 第四十四轮 | r43 审计 + 10 项综合清算 + 14 轮欠账 closed | 3 漏网 JSON cap（csv × 2 / gui_dialogs / ui_whitelist，真实 21/21）+ plugin cap rename `_CHARS` 澄清语义 + zh-tw generic fallback test + docs/constants/quality_chain/roadmap 三大刷新 + CI Windows matrix + PyInstaller build 33.9 MB exe 成功 + gui.py 3s smoke 成功，测试 409→413 |
| 第四十五轮 | 综合维护（测试拆分 / 审计 / docs / CI / hooks 等） | test_file_processor 830→560 拆 UI whitelist → test_ui_whitelist.py + .gitattributes LF policy + 扩 .gitignore + build.py --clean + pre-commit hook + docs/constants 扩 pricing+rate_limit+retry + 其他 docs 复查 + CI shell 一致性 + rpyc_decompiler:416 audit fix，测试 413+ |

> **注**：r20-r44 的详细轮次内容（功能/增强/修复分组、具体 commit、技术决策）见
> [CHANGELOG_RECENT.md](../CHANGELOG_RECENT.md) 近 3 轮详细段 + `git log`
> commit 历史。本 FULL 只保留总览表以控制文档规模。

---

## 第十九轮：翻译后工具链 + 插件系统

> **背景**：深度分析 renpy-translator-main（MIT, anonymousException）项目，识别出 6 项可借鉴功能。核心价值在于补齐「翻译后工作流」——打包分发、人工校对、引擎扩展。

### 新增工具

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 210 | **RPA 打包工具**：纯标准库实现 RPA-3.0 写入（随机 XOR key + zlib + pickle），支持自动收集 tl/字体/Hook + 打包后往返验证 | `tools/rpa_packer.py`（新增 ~280 行） | 翻译→分发最后一环 |
| 211 | **HTML 交互式校对工具**：导出翻译为可编辑 HTML（contenteditable + 搜索/过滤 + 修改跟踪），浏览器中编辑后导出 JSON，导入回写到 .rpy | `tools/translation_editor.py`（新增 ~420 行 Python + ~160 行 HTML/JS） | 人工校对工作流 |
| 212 | **自定义翻译引擎插件**：`custom_engines/` 目录放 Python 模块，双层接口（`translate_batch` 批量优先，`translate` 单句降级），安全限制（仅加载子目录、拒绝路径遍历） | `core/api_client.py`（+~140 行）+ `custom_engines/example_echo.py`（示例） | 引擎扩展性 |

### 流水线增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 213 | **默认语言设置**：打包前自动生成 `default_language.rpy`（`config.default_language = "chinese"`），已存在则跳过，通过 `lang_config` 映射语言代码→目录名 | `pipeline/stages.py` | 玩家首次启动即显示中文 |
| 214 | **Lint 修复流水线集成**：翻译后自动运行 `run_lint()` 修复语法错误，不可用时明确告知而非静默跳过，`--no-lint-repair` 可禁用 | `pipeline/stages.py` + `one_click_pipeline.py` | 翻译质量兜底 |
| 215 | **JSON 解析失败拆分重试**：`_should_retry` 新增判断——返回 0 条且期望 > 0 且无 API 错误时触发 chunk 拆分重试 | `translators/direct.py` | 鲁棒性提升 |

### CLI 变更

| 参数 | 说明 |
|------|------|
| `--provider custom` | 使用自定义翻译引擎（需配合 `--custom-module`） |
| `--custom-module NAME` | 自定义引擎模块名（位于 `custom_engines/` 目录） |
| `--no-lint-repair` | 跳过翻译后的 Lint 修复阶段 |

### 测试新增

| 文件 | 新增用例 | 覆盖 |
|------|---------|------|
| `tests/test_batch1.py` | 18 | RPA 打包（10：基本/往返/随机key/嵌套目录/空集/缺失文件/Unicode/验证/大文件/收集 + header 格式验证）+ 默认语言（5：zh/ja/ko/zh-tw/不覆盖）+ JSON 重试（1）+ Lint 集成（1） |
| `tests/test_translation_editor.py` | 13 | 导出（4：基本/多条/空/XSS 转义）+ 提取（2：tl/db）+ 导入（6：tl 替换/空槽/db 模式/备份不覆盖/缺失文件/空译文）+ 工具（1：转义） |
| `tests/test_custom_engine.py` | 11 | 加载（6：正常/扩展名/不存在/空名/路径遍历/无接口）+ 配置（2）+ 调用（3：批量 string/单句降级/批量 list） |

### 工程配置

| 文件 | 变更 |
|------|------|
| `build.py` | `hidden_imports` +2（`tools.rpa_packer`、`tools.translation_editor`） |
| `.github/workflows/test.yml` | `py_compile` +3 + test runs +3 |
| `main.py` | `--provider` choices +1（`custom`）+ `--custom-module` 参数 |
| `translators/*.py` | 4 处 `APIConfig()` 构造加 `custom_module=` 透传 |

### 技术指标

- 新增文件：3（`tools/rpa_packer.py` + `tools/translation_editor.py` + `custom_engines/example_echo.py`）+ 3 测试文件
- 修改文件：8（`core/api_client.py` + `pipeline/stages.py` + `one_click_pipeline.py` + `main.py` + `translators/direct.py` + `translators/tl_mode.py` + `translators/retranslator.py` + `translators/screen.py`）+ `build.py` + `test.yml`
- 测试数量：225 → **267**（18 + 13 + 11 = 42 新增用例）
- 零依赖原则：保持

---

## 第十八轮：预处理工具链 + 翻译增强

> **背景**：分析 renpy-translator-main（MIT, anonymousException 2024）项目，识别出 8 项可借鉴功能，按 P0~P3 优先级全部实施。新增 3 个独立预处理工具（`tools/`）、2 个 Ren'Py Hook 模板（`resources/hooks/`），并对翻译流水线做了 3 项增强（文件级并行、锁定术语预替换、跨文件去重）。

### 新增工具

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 205 | **RPA 解包工具**：纯标准库实现 RPA-3.0/2.0 档案解包（XOR 解混淆 + zlib + pickle），支持 `--list` / `--scripts-only` / `--force`，独立 CLI + API | `tools/rpa_unpacker.py`（新增 ~320 行） | 翻译全链路第一步：解包 → 反编译 → 翻译 |
| 206 | **rpyc 反编译工具**（双层策略）：Tier 1 调用游戏自带 Python + `renpy.util.get_code()` 生成完美 .rpy；Tier 2 用 `RestrictedUnpickler` 独立提取文本（无需 Ren'Py 运行时）。平台适配层覆盖 Win/Mac/Linux × Ren'Py 7.x/8.x。法律确认提示为阻塞式 `input()` | `tools/rpyc_decompiler.py`（新增 ~640 行） | 覆盖只发布 .rpyc 的游戏 |
| 207 | **Ren'Py lint 集成 + 自动修复**：调用游戏自带引擎执行 lint，解析 6 种语法错误 + 1 种重复翻译，自动删除/修复问题行。优雅降级：无完整运行时时静默回退到静态验证。超时默认 120s 可配置 | `tools/renpy_lint_fixer.py`（新增 ~340 行） | 静态验证的兜底补充 |
| 208 | **运行时提取 Hook**：注入游戏运行时，从 `renpy.game.script.translator.default_translates` 提取全部 say 语句导出 JSON | `resources/hooks/extract_hook.rpy`（新增 ~63 行） | 复杂脚本的终极兜底方案 |
| 209 | **语言切换 UI 注入**：monkey-patch `renpy.show_screen` 替换设置页，自动扫描 `tl/` 列出语言切换按钮 | `resources/hooks/language_switcher.rpy`（新增 ~63 行） | 玩家体验增强 |

### 翻译流水线增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 210 | **文件级并行翻译**（`--file-workers`）：在现有 chunk 并发之上新增文件级 ThreadPoolExecutor，默认 1（不改变现有行为），opt-in 启用。共用 `_results_lock` 保护共享状态 | `translators/direct.py` + `main.py` + `gui.py` + `one_click_pipeline.py` | 大型项目翻译提速 |
| 211 | **锁定术语预替换**：翻译前将 `locked_terms` 替换为 `__LOCKED_TERM_N__` 令牌（智能词边界：仅在首尾为 \w 时添加 `\b`），翻译后替换为中文译名。作为 prompt 注入的补充保险 | `file_processor/checker.py` + `translators/direct.py` + `core/translation_utils.py` | 术语准确率提升 |
| 212 | **跨文件翻译去重**（仅 tl-mode）：相同 `(speaker, text)` 且源文本 ≥40 字符的条目只翻译一次，结果复用到所有重复条目。短语气词/短句不去重（保留上下文翻译差异）。记录复用来源 `{source_file, source_line}` 便于调试 | `translators/tl_mode.py` | 节省 ~20% API 调用（实测 TheTyrant 42.7% 重复率） |

### 测试新增

| 文件 | 新增用例 | 覆盖 |
|------|---------|------|
| `tests/test_rpa_unpacker.py` | 14 | RPA-3.0/2.0 解包、XOR key 变体、prefix bytes、版本检测、损坏文件、目录解包 |
| `tests/test_rpyc_decompiler.py` | 17 | RPYC2 二进制格式、RestrictedUnpickler、Say/Menu/TranslateString 提取、Unicode、平台检测 |
| `tests/test_lint_fixer.py` | 15 | 7 种 lint 错误模式解析、old/new 对修复、translate 块修复、连续空行清理、降级检测 |
| `tests/test_tl_dedup.py` | 10 | 去重基础/阈值/speaker 隔离/StringEntry/apply 复用/无翻译降级 |
| `tests/test_all.py` 追加 | 7 | locked_terms 保护/还原/词边界/长匹配优先/特殊字符/多次出现/空输入 |

### 技术指标

- 新增文件：5（3 工具 + 2 Hook 模板）+ 4 测试文件
- 修改文件：8（direct.py / tl_mode.py / checker.py / translation_utils.py / main.py / gui.py / one_click_pipeline.py / __init__.py）
- 测试数量：162 → **225**（94 + 62 + 13 + 14 + 17 + 15 + 10 = 225 自动化用例，不含内建断言）
- 零依赖原则：保持
- 所有预处理工具遵循 fail-fast + 不阻断主流程原则

---

## 第十七轮：项目结构深度重构

> **背景**：经过 16 轮迭代，根目录积累了 ~25 个 .py 文件，`main.py` 和 `one_click_pipeline.py` 维护着大量 re-export 兼容层，`pipeline/helpers.py` 从 `one_click_pipeline.py` 反向导入常量形成循环依赖。需要按职责将模块分入包，消除兼容层，统一 import 路径。

### 结构变更

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 194 | 新建 `core/` 包（7 模块）：api_client / config / lang_config / glossary / prompts / translation_db / translation_utils 从根目录迁入 | `core/`（新增） | 共享基础设施独立包 |
| 195 | 新建 `translators/` 包（6 模块）：direct（合并 dryrun）/ tl_mode / retranslator / screen / tl_parser / renpy_text_utils 从根目录迁入 | `translators/`（新增） | 翻译引擎独立包 |
| 196 | `tools/` 包扩充（+3 模块）：font_patch / renpy_upgrade_tool / review_generator 从根目录迁入 | `tools/`（扩充） | 工具集中管理 |
| 197 | `direct_translator_dryrun.py` 合并入 `translators/direct.py`（3 个函数保持原名） | `translators/direct.py` | 消除 44 行独立文件 |
| 198 | 常量迁移：`RISK_KEYWORDS` / 评分常量 / `LEN_RATIO_*` / `StageError` 从 `one_click_pipeline.py` 移入 `pipeline/helpers.py` | `pipeline/helpers.py`、`one_click_pipeline.py` | 消除循环依赖 |
| 199 | 删除 `main.py` re-export 块（40 行）+ `one_click_pipeline.py` re-export 块（30 行） | `main.py`、`one_click_pipeline.py` | 消除兼容层 |
| 200 | `pipeline/__init__.py` 清空 re-export（无消费者） | `pipeline/__init__.py` | 清理无用代码 |
| 201 | 所有消费者（tests / tools / engines / pipeline）import 路径迁移到新包路径 | 20+ 文件 | 统一 import 路径 |
| 202 | `start_launcher.py` subprocess 路径改用 `Path(__file__).resolve().parent`（PyInstaller 兼容） | `start_launcher.py` | 打包后路径正确 |
| 203 | `build.py` hidden_imports 更新为新包路径（38 项） | `build.py` | PyInstaller 打包正确 |
| 204 | `.github/workflows/test.yml` 全部更新（py_compile 路径 + 自测命令 + 零依赖白名单） | `test.yml` | CI 覆盖完整 |

### 迁移策略

采用 **shim 渐进迁移**：每移动一批文件在原位置留 `sys.modules` 重定向 shim，确保每步测试全绿；全部消费者迁移完成后统一删除 shim。12 个 Git 检查点，任何一步失败可回退。

### 技术指标

- 根目录 .py 文件：25 → **5**（main / gui / start_launcher / one_click_pipeline / build）
- 新增包：`core/`（7 模块）、`translators/`（6 模块）、`tools/__init__.py`
- 删除文件：17 个根目录 .py（迁入包）+ `direct_translator_dryrun.py`（合并）
- 消除 re-export：main.py 40 行 + one_click_pipeline.py 30 行 + pipeline/__init__.py 30 行
- 消除循环依赖：`pipeline/helpers.py` ↔ `one_click_pipeline.py`
- 测试数量：162（87 + 62 + 13）全绿 + 内建自测 126 断言
- PyInstaller 打包：31.4 MB 成功
- 零依赖原则：保持

---

## 第十六轮：screen 文本翻译 + 缓存清理修复

> **背景**：Ren'Py 的 `Generate Translations` 只提取 Say 对话和 `_()` 包裹的字符串到 tl 框架。screen 定义中的裸 `text "..."`、`textbutton "..."`、`tt.Action("...")` 不会被提取，导致 tl-mode 翻译后仍有 ~5.3% 的 UI 文本（按钮、状态面板、Tooltip 提示等）显示英文。经验证 `translate <lang> screen xxx():` 语法不存在于 Ren'Py（`renpy/parser.py` 只支持 strings/python/style），唯一可行路径是直接修改源文件中的英文字符串。

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 182 | `screen_translator.py` 新增（~420 行）：`ScreenTextEntry` 数据类 + 三组正则（text/textbutton/tt.Action）+ `in_screen` 上下文检测（只在 `screen xxx():` 缩进范围内提取）+ `_should_skip` 跳过逻辑（纯变量/已中文/文件路径/单字符）+ `_line_has_underscore_wrap` 跳过 `_()` 包裹行 + 去重翻译 + 逐行正则替换 + `.bak` 备份 + 进度文件断点续传 + dry-run 支持 + 42 个内建断言 | `screen_translator.py`（新增） | tl-mode 补充，覆盖 screen 裸英文 |
| 183 | `--tl-screen` CLI 参数：可与 `--tl-mode` 联用（tl 翻译后自动补充 screen 文本），也可独立运行 | `main.py` | 新增 CLI 参数 |
| 184 | GUI 新增 `--tl-screen` 勾选框（高级设置 tab） | `gui.py` | GUI 增强 |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 185 | `_clean_rpyc` 的 `modified_files` 分支：增加 `.rpymc` 精确清理 + `.rpyb` 全量清理（此前只清理 `.rpyc`） | `tl_translator.py` | 缓存清理完整性 |
| 186 | `delete_rpyc_files` 扩展到三种后缀（`.rpyc` + `.rpymc` + `.rpyb`）（此前只清理 `.rpyc`） | `renpy_upgrade_tool.py` | 升级扫描后缓存清理完整性 |
| 187 | 资源复制排除列表增加 `.rpymc`（此前排除 `.rpy`/`.rpyc`/`.rpyb` 但漏掉 `.rpymc`） | `direct_translator.py` | 防止复制编译模块缓存 |

### 测试

| # | 描述 |
|---|------|
| 76 | `test_screen_should_skip`：12 种跳过/不跳过场景 |
| 77 | `test_screen_extract_basic`：text/textbutton/tt.Action 三种模式提取 + 类型正确性 |
| 78 | `test_screen_extract_skips_underscore`：`_()` 包裹行被跳过 |
| 79 | `test_screen_extract_skips_outside_screen`：screen 定义外的 text 不提取 |
| 80 | `test_screen_dedup`：相同文本去重 + 保留所有出现位置 |
| 81 | `test_screen_replace_text`：text 行替换保留缩进 |
| 82 | `test_screen_replace_textbutton_preserves_action`：textbutton 只替换显示文本，action/style 参数不动 |
| 83 | `test_screen_replace_tt_action`：tt.Action 替换括号内字符串 |
| 84 | `test_screen_replace_with_tags_and_vars`：含 `{color}` 和 `[var]` 的复合文本正确替换 |
| 85 | `test_screen_backup_no_overwrite`：.bak 仅在不存在时创建 |
| 86 | `test_screen_chunks`：分块行数守恒 |
| 87 | `test_screen_replace_notify`：Notify("...") 替换正确 + action 参数不动 |

### 修复（实战验证后）

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 188 | `_RE_NOTIFY` 正则新增：覆盖 `Notify("...")` 弹出通知模式（SAZMOD 大量使用） | `screen_translator.py` | 新增 735 条 Notify 文本覆盖 |
| 189 | `_should_skip` 文件路径检测误杀修复：先剥离 Ren'Py 标签再检测 `/` + `.` | `screen_translator.py` | 修复 405 条含标签文本未提取 |

### 流水线集成

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 190 | `_run_tl_mode_phase()` 末尾自动追加 screen 翻译 | `pipeline/stages.py` | 一键流水线 tl-mode 自动补充 |
| 191 | `parse_args()` 新增 `--tl-screen` 参数 | `one_click_pipeline.py` | 流水线 CLI 支持 |
| 192 | 模式 5/6 新增"翻译 screen 裸英文？"交互询问 | `start_launcher.py` | 启动器支持 |
| 193 | `hidden_imports` 新增 `"screen_translator"` | `build.py` | PyInstaller 打包覆盖 |

### 实战验证数据（The Tyrant, ~140 文件）

| 轮次 | 条数 | 种类 | 费用 |
|------|------|------|------|
| 第一轮（text/textbutton/tt.Action） | 3,818 | 1,428 | $0.034 |
| 第二轮（_should_skip 标签修复后） | 405 | 176 | $0.007 |
| 第三轮（Notify 新增后） | 886 | 433 | $0.011 |
| **合计** | **5,109** | **2,037** | **$0.052** |

---

## 第十五轮：nvl clear 翻译 ID 修正

> **背景**：Ren'Py 8.6+ 的 `Generate Translations` 默认启用 `config.tlid_only_considers_say = True`，计算翻译块 ID 时只哈希 Say 语句。但 Ren'Py 7.x 没有此配置，始终把 `nvl clear` 等 translatable 语句也纳入哈希。导致含 `nvl clear` 的翻译块 ID 不匹配，翻译静默失败——游戏显示英文原文而非中文。

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 178 | `fix_nvl_translation_ids(file_path)` 单文件修正：扫描 .tl 文件中含 `# nvl clear` 注释的 translate 块，验证当前 ID 是 say-only 哈希后替换为 nvl+say 哈希；幂等（已修正的不重复处理） | `tl_parser.py` | 修正 Ren'Py 7.x 翻译静默失败 |
| 179 | `fix_nvl_ids_directory(tl_dir, lang)` 批量目录修正，遍历 `tl/<lang>/**/*.rpy` | `tl_parser.py` | 一次修正全部文件 |
| 180 | 管道集成：`run_tl_pipeline` 两处 `postprocess_tl_directory` 调用后自动执行 `fix_nvl_ids_directory` | `tl_translator.py` | 翻译流程自动修正 |
| 181 | `_clean_rpyc` 增强：新增 .rpymc（编译模块）/ .rpyb（字节码缓存）清理；翻译后始终全量清理（不再仅清理已修改文件） | `tl_translator.py` | 避免残留缓存导致翻译不生效 |

### 测试

| # | 描述 |
|---|------|
| 72 | `test_fix_nvl_ids_basic`：say-only ID 被替换为 nvl+say ID |
| 73 | `test_fix_nvl_ids_no_nvl`：不含 nvl clear 的块不受影响 |
| 74 | `test_fix_nvl_ids_already_correct`：已正确的 ID 不重复修改（幂等性） |
| 75 | `test_fix_nvl_ids_real_hashes`：begin.rpy 真实数据回归（2 case） |

### 哈希算法

```python
# Ren'Py 7.x 翻译块 ID = md5(所有 translatable 语句)[:8]
md5 = hashlib.md5()
md5.update(b"nvl clear\r\n")          # nvl clear 的 get_code()
md5.update(say_code.encode("utf-8") + b"\r\n")  # Say 的 get_code()
digest = md5.hexdigest()[:8]           # → label_XXXXXXXX
```

---

## 第十四轮：全面优化（Ren'Py 专项）

> **目标**：专注 Ren'Py 翻译链路，从代码结构、健壮性、性能、翻译质量、用户体验五个维度全面提升。

### Phase 0: 基础重构

**功能**：
- 新建 `renpy_text_utils.py`：从 `one_click_pipeline.py` 提取 `_is_user_visible_string_line` 等 5 个公共函数，消除 `direct_translator` / `retranslator` 对 pipeline 的反向依赖
- 新建 `pipeline/` 包：将 `one_click_pipeline.py`（1472 行）拆分为 `pipeline/helpers.py` + `pipeline/gate.py` + `pipeline/stages.py`，原文件保留为薄 facade
- 新建 `direct_translator_dryrun.py`：提取 dry-run 分析逻辑（密度直方图、术语预览、文件统计）
- `glossary.py`: `import string` 移至模块顶部

### Phase 1: 代码健壮性

**修复**：
- 收窄 10+ 处裸 `except Exception`：静默异常改为 `(OSError, ValueError, UnicodeDecodeError)` + debug 日志；主循环改为具体异常类型；保留 API 调用层的宽泛 catch-all
- `config.py` 新增 `validate()` 方法：类型检查、范围校验、未知键告警（不拒绝，仅 warning）
- `gui.py._stop()` 改为优雅终止：先发送 `CTRL_C_EVENT`（让子进程保存进度），等待 5 秒后才 kill

### Phase 2: 性能优化

**功能**：
- `TranslationCache`：线程安全的会话级翻译缓存（original → zh），支持置信度跟踪和命中率统计
- token 估算改进：按字符类别分别估算（英文单词按词长、CJK 按 1.5x、标点按 1/3），取代简单的 ascii//4 + non_ascii//2
- 线程池背压：`Semaphore(workers * 2)` 限制并发提交数，避免大文件一次性提交所有 future
- 占位符处理缓存：`protect_placeholders()` 结果按 text hash 缓存，避免相同文本重复正则匹配
- 术语库内存上限：`memory` dict 设 10000 条上限，超出后按频次淘汰低频条目

### Phase 3: 翻译质量

**功能**：
- 跨 chunk 上下文传递（验证已有实现）：第 2 个 chunk 起附带前 5 行作为上文参考
- 术语一致性主动执行：`get_consistent_translation()` 返回高置信度已有翻译；高频 memory 条目（count≥3）在 prompt 中升级为"确定翻译（必须遵循）"
- 新增 3 条验证规则：
  - `E250_CONTROL_TAG_DAMAGED`：`{w}` / `{p}` / `{nw}` / `{fast}` / `{cps=N}` 控制标签损坏
  - `W460_POSSIBLE_OVERTRANSLATION`：Ren'Py 关键字（label/screen/define 等）被翻译成中文
  - `W470_CONSECUTIVE_PUNCTUATION`：连续中文标点（。。、！！）

### Phase 4: 用户体验

**功能**：
- GUI 进度条：`ttk.Progressbar` + 百分比标签，解析 CLI 输出的 `[N/M]` 格式更新
- 自适应日志轮询：有数据时 50ms、无数据时 200ms，每次最多处理 50 条
- 日志显示性能：超过 5000 行自动裁剪至 3000 行
- CLI 优雅终止：注册 SIGTERM 处理器，收到信号后设中断标志、保存进度

### 技术指标

- 代码行数：~12000 行核心代码
- 测试数量：71 + 62 + 13 = 146 测试
- 新增模块：`renpy_text_utils.py` / `direct_translator_dryrun.py` / `pipeline/` 包
- 零依赖原则：保持仅 Python 标准库
- 向后兼容：所有现有 CLI 参数、配置文件、import 路径不变

---

## 第一轮：质量校验体系

### 新增功能

| # | 描述 | 涉及文件 | Code | 影响 |
|---|------|----------|------|------|
| 1 | 译文长度比例异常告警：原文 ≥ 20 字且译文 ≥ 5 字时，比例超区间触发 warning | `file_processor.py` | W430 | 新增告警 |
| 2 | 术语锁定（`locked_terms`）与禁翻片段（`no_translate`）：glossary.json 新增字段，Prompt / 校验 / 闸门联动 | `glossary.py`, `prompts.py`, `file_processor.py`, `main.py`, `one_click_pipeline.py` | E411, E420 | 新增错误（仅当配置时生效） |
| 3 | 翻译风格规则检查：模型自述、标点混用、中文占比极低 | `file_processor.py` | W440, W441, W442 | 新增告警 |
| 4 | 占位符顺序校验：集合一致前提下比较顺序，不一致仅 warning，仍 apply | `file_processor.py` | W251 | 语义变更：无检测 → 仅告警 |
| 5 | tl 优先模式（`--tl-priority`）：启用时仅翻译 `tl/` 下的 .rpy | `main.py` | — | 默认不启用 |
| 6 | strings 统计视图（`collect_strings_stats`）：统计 translate strings 块翻译情况 | `one_click_pipeline.py` | — | 仅新增统计 |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 7 | `validate_translation` 支持可配置 `len_ratio_lower` / `len_ratio_upper` | `file_processor.py`, `one_click_pipeline.py` | 默认行为不变 |
| 8 | `MODEL_SPEAKING_PATTERNS` / `PLACEHOLDER_ORDER_PATTERNS` 提升为模块级常量 | `file_processor.py` | 可配置化 |
| 9 | `evaluate_gate` 传入 glossary 参数，保证闸门统计与 main 行为一致 | `one_click_pipeline.py` | 闸门统计更完整 |
| 10 | 闸门打印增加 W430 / W251 统计 | `one_click_pipeline.py` | 仅输出增强 |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 11 | `prompts.py` 花括号转义（`{标签}` → `{{标签}}`） | `prompts.py` | 防止 Python format 报错 |
| 12 | E420 错误消息引号转义修正 | `file_processor.py` | 仅展示修正 |

### 文档

| # | 描述 | 涉及文件 |
|---|------|----------|
| 13 | Prompt 补充锁定术语 / 禁翻片段 / 占位符顺序规范 | `prompts.py` |
| 14 | 代码注释：W251 语义变更（仅告警仍 apply） | `file_processor.py` |
| 15 | 代码注释：locked_terms 应少而精 | `glossary.py` |

---

## 第二轮：功能增强

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 16 | 结构化报告 `report_summary.md`（三级判定绿/黄/红，warning code 分布） | `one_click_pipeline.py` | 仅新增输出 |
| 17 | `TranslationDB` 增量翻译元数据存储（upsert 去重，按 status/file/stage 筛选） | `translation_db.py` | 新增模块 |
| 18 | 自动字体补丁（`--patch-font` + `font_patch.py`）：`resolve_font` + `apply_font_patch` 修改 gui.rpy | `font_patch.py`, `main.py`, `one_click_pipeline.py` | 默认不启用 |
| 19 | README 组合式工作流推荐（4 种模式） | `README.md` | 仅文档 |

---

## 第三轮：降低漏翻率（12.12% → 4.01%）

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 20 | 占位符保护 / 还原（`protect_placeholders` / `restore_placeholders`，令牌 `__RENPY_PH_N__`） | `file_processor.py` | 发送前保护，返回后还原 |
| 21 | `ResponseChecker`：`check_response_item`（占位符集合 + 非空）+ `check_response_chunk`（条数一致） | `file_processor.py` | 不通过则丢弃，保留原文 |
| 22 | Checker 丢弃逻辑：status = `"checker_dropped"` 写入 translation_db | `main.py`, `file_processor.py` | 归因可追溯 |
| 23 | 密度自适应翻译策略：`calculate_dialogue_density()` < 20% 的文件走 `_translate_file_targeted()` 定向翻译 | `main.py` | 行为变更：低密度文件不再整文件发送 |
| 24 | 配置文件跳过名单 `SKIP_FILES_FOR_TRANSLATION`：define / variables / screens / options / earlyoptions.rpy | `file_processor.py`, `main.py`, `one_click_pipeline.py` | 行为变更：跳过翻译和漏翻统计 |
| 25 | 补翻模式 `--retranslate`：`find_untranslated_lines` 检测残留英文 → `build_retranslate_chunks`（≤ 20 行 + ±3 上下文）→ 专用 prompt → 原地回写 | `main.py`, `prompts.py` | 新增 CLI 模式 |
| 26 | `find_untranslated_lines` 二次过滤：排除 auto / hover / idle / image 路径 / screen 属性行 | `main.py` | 减少假阳性 |
| 27 | 漏翻归因分析：per-chunk 指标（expected / returned / dropped）+ `attribute_untranslated`（AI 未返回 / Checker 丢弃 / 回写失败 / 未知） | `main.py`, `one_click_pipeline.py` | 仅新增统计 |
| 28 | Pipeline Stage 3 改为 retranslate 原地补翻（替代旧的增量翻译 + merge 覆盖） | `one_click_pipeline.py` | 架构变更 |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 29 | translate strings 专用回写路径（`_parse_strings_blocks` + `_apply_strings_translations`） | `main.py` | 提升 strings 块回写成功率 |
| 30 | original 对齐（`_align_original_with_file`，两层匹配：完全相等 + 前缀后缀 ≥ 0.8） | `main.py` | 提升行号对齐精度 |
| 31 | 原地补翻 `.bak` 自动备份（不覆盖已有备份） | `main.py` | 安全增强 |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 32 | `translate_file` 早退路径返回值不一致（`0, []` → `0, [], 0, []`） | `main.py` | 修复潜在解包错误 |
| 33 | `retranslate_file` 中 `ph_mapping` 类型错误（`list[tuple]` 当 `dict` 调用 `.items()`） | `main.py` | 修复含占位符行崩溃 |
| 34 | `retranslate_file` 中 AI 返回带角色名前缀导致匹配失败 | `main.py` | 补翻回写成功率从 ~0% 恢复正常 |
| 35 | Pipeline Stage 3 增量覆盖丢翻译的结构性缺陷（删除 `merge_incremental_results`） | `one_click_pipeline.py` | 架构修复 |

### 验证数据（The Tyrant, ~140 文件）

| 阶段 | 漏翻率 | 关键改动 |
|------|--------|----------|
| 基线 | 12.12% | 无 |
| + 占位符保护 + checker | 10.40% | 挽回校验拦住的条目 |
| + 密度自适应 + retranslate | **4.01%** | 低密度文件定向翻译 |

漏翻归因：AI 未返回 71.1% / 回写失败 28.1% / Checker 丢弃 0.8%

---

## 第四轮：tl-mode 翻译模式

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 36 | `tl_parser.py` 独立解析模块：状态机（IDLE / DIALOGUE / STRINGS / SKIP）、`DialogueEntry` / `StringEntry` / `TlParseResult` 数据类、UTF-8 BOM 处理、75 个内建测试 | `tl_parser.py` | 新增模块 |
| 37 | `--tl-mode` + `--tl-lang` CLI 参数：扫描 `tl/<lang>/` 空槽位，AI 翻译后精确回填 | `main.py` | 新增模式，与 `--retranslate` 互斥 |
| 38 | tl-mode 专用 Prompt：`TLMODE_SYSTEM_PROMPT` + `build_tl_system_prompt` + `build_tl_user_prompt` | `prompts.py` | 新增模板 |
| 39 | `run_tl_pipeline`：`build_tl_chunks`（每 chunk ≤ 30 条）→ ThreadPoolExecutor 并发翻译 → 串行回填 | `main.py` | 新增功能（`--workers` 控制线程数） |
| 40 | `fill_translation` 行级精确回填：`str.replace` 只替换第一个 `""` → `"译文"`，保留缩进 / character 前缀 | `tl_parser.py` | 新增函数 |
| 41 | StringEntry 四层 fallback 匹配：精确 → strip 空白 → 去占位符令牌 → 转义规范化（`\"` → `"`、`\n` → 换行） | `main.py` | 提升匹配率 |
| 42 | start_launcher.py 新增模式 5/6：tl-mode 从头 / 断点续跑，含 `--workers` 参数 | `start_launcher.py` | 新增菜单选项 |
| 43 | 独立进度文件 `tl_progress.json`：chunk 级断点续传 | `main.py` | 支持 `--resume` |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 44 | `run_tl_pipeline` id 字段占位符还原：`restore_placeholders` 覆盖 `id` / `original` / `zh` 三个字段 | `main.py` | 修复 StringEntry 匹配失败 |
| 45 | tl 优先回退 warning 增加路径提示 | `main.py` | 便于排查 |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 46 | start_launcher.py 重复"并发线程数"提示：tl-mode 和 direct-mode 各自独立询问 | `start_launcher.py` | UX 修复 |

### 小规模验证数据（3 文件 / 135 条）

- 匹配率：97.8%（132/135），Checker 丢弃 0 条
- 缩进/引号/character 前缀：100% 正确
- 占位符保留：13/13 个 `[var]` 全部保留
- 未匹配 3 条：含 `\n` 多行 UI 按钮文本（AI 未返回）
- id 占位符还原修复后：93.3% → 97.8%（挽回 6 条）
- 费用：$0.0034（5 请求，grok-4-1-fast-reasoning）

---

## 第五轮：tl-mode 全量验证 & 修复

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 47 | `fill_translation` 引号剥离保护：循环剥离外层引号（ASCII `""` / 弯引号 `""` / 全角 `＂＂`），防止 `""text""` 格式错误 | `tl_parser.py` | 修复 14% 的译文格式问题 |
| 48 | `_QUOTE_STRIP_PAIRS` 提升为模块级常量 | `tl_parser.py` | 性能优化 |
| 49 | `_sanitize_translation` 完善：元数据泄漏清理 + 循环引号剥离 + 单侧残存处理 + 内嵌引号转义 | `tl_parser.py` | 全面的译文清理 |
| 50 | `postprocess_tl_file` / `postprocess_tl_directory`：翻译后修复 Ren'Py 兼容性问题（移除 translate 块内 `nvl clear`、空块补 `pass`） | `tl_parser.py` | 新增后处理 |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 51 | `fill_translation` 双引号 bug：AI 返回带引号译文时回填产生 `""text""`，增加三对引号剥离 | `tl_parser.py` | 10,402/74,002 条受影响，修复后 0 格式错误 |

### 全量验证数据（The Tyrant, 107 文件, 10 线程）

| 指标 | 数值 |
|------|------|
| 总槽位 | 76,169（75,993 对话 + 176 字符串） |
| 待翻译 | 74,044（73,868 对话 + 176 字符串） |
| **翻译成功** | **74,019（99.97%）** |
| 未翻译 | 25 条（命名输入框 / 转义引号 / AI 未返回） |
| Checker 丢弃 | 4 条 |
| API 请求 | 2,541 次 |
| Token 用量 | 输入 4.09M / 输出 3.83M |
| 费用 | $2.73（grok-4-1-fast-reasoning） |
| 耗时 | 73.1 分钟 |
| 引号 bug 影响 | 10,402/74,002 条（14%），修复后 0 格式错误 |

---

## 第六轮：代码优化与新功能

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 34 | `_translate_chunk_with_retry`: chunk 翻译自动重试，API 错误或丢弃率 > 30% 时重试 1 次 | `main.py` | 降低 API 瞬时故障导致的漏翻 |
| 35 | `--verbose` / `--quiet` CLI 参数：控制日志级别（DEBUG/WARNING） | `main.py` | 新增 CLI 参数 |
| 36 | `setup_logging()`: 全局 logging 配置，支持文件输出 | `main.py` | 替代 print |
| 37 | `extract_terms_from_translations()`: 从翻译结果中自动提取高频专有名词（n-gram 共现分析）| `glossary.py` | 新增方法 |
| 38 | `auto_add_terms()`: 将提取的术语自动加入 glossary.terms | `glossary.py` | 新增方法 |
| 39 | Pipeline pilot 后自动术语提取：从 pilot 翻译结果提取人名/地名，供全量翻译使用 | `one_click_pipeline.py` | pipeline 增强 |
| 40 | Pipeline `--tl-mode` / `--tl-lang`：一键流水线支持 tl-mode（跳过试跑/补翻，直接 tl 翻译） | `one_click_pipeline.py`, `start_launcher.py` | 新增模式 |
| 41 | RENPY-020 规则：`show image:` 空 ATL 块修复（多行感知，仅删除无 ATL 块的冒号）| `renpy_upgrade_tool.py` | 新增升级规则 |
| 42 | chunk 上文上下文：split_file 的第 2+ chunk 附带前一 chunk 末尾 5 行 | `file_processor/splitter.py` | 提升跨块翻译连贯性 |
| 43 | `[MULTILINE]` 标记：tl-mode 中含 `\n` 的条目自动标记，提示 AI 保留换行 | `main.py`, `prompts.py` | 提升多行字符串翻译率 |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 44 | 429/5xx 退避优化：jitter 防雪崩 + 60s 上限 + Retry-After header 优先 | `api_client.py` | 多线程稳定性提升 |
| 45 | `file_processor.py` 拆分为 `file_processor/` 包（splitter/checker/patcher/validator + __init__.py re-export） | `file_processor/` | 可维护性，外部 import 不变 |
| 46 | 全模块 print → logging 迁移（main/file_processor/api_client/one_click_pipeline/glossary/font_patch） | 6 个文件 | 支持 --verbose/--quiet/--log-file |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 47 | validate_translation 中 `✓` Unicode 字符在 GBK 终端报错 → 改为 `OK` | `file_processor/validator.py` | 修复 Windows 终端编码错误 |
| 48 | StringEntry fallback 注释从"三层"修正为"四层"（精确→strip→去占位符→转义规范化） | `main.py` | 注释修正 |
| 49 | 全文扫描安全性：第四遍 `apply_translations` 跳过已被前面 pass 修改的行（`modified_lines` + `full_scan`），防止同一原文多次出现时误替换 | `file_processor/patcher.py` | 降低回写错误 |
| 50 | 截断匹配阈值从 0.5 提高到 0.7（阶段 3e），减少 AI 截断文本误匹配 | `file_processor/patcher.py` | 提升匹配精度 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 51 | tl_parser 内建自测新增 19 个断言（56→75）：`_sanitize_translation` 12 个边界 + `fill_translation` 7 个边界 | `tl_parser.py` | 测试覆盖 |

---

## 第七轮：全量验证（第六轮 15 项改进）

### 验证数据（The Tyrant, 105 文件, 10 线程）

| 指标 | 第五轮（基线） | 第七轮（本次） | 变化 |
|------|---------------|----------------|------|
| 总槽位 | 76,169 | 76,225 | +56 |
| 待翻译 | 74,044 | 74,098 | +54 |
| **翻译成功** | **74,019（99.97%）** | **74,091（99.99%）** | **+72 条, +0.024pp** |
| 未翻译 | 25 | **7** | **-18（-72%）** |
| Checker 丢弃 | 4 | **2** | **-2（-50%）** |
| Fallback 匹配 | — | 3 | 新增指标 |
| API 请求 | 2,541 | 2,572 | +31 |
| Input tokens | 4.09M | 4.23M | +3.4%（chunk 上下文 5 行导致） |
| Output tokens | 3.83M | 3.83M | 持平 |
| 费用 | $2.73 | $2.76 | +$0.03（+1.1%） |
| 耗时 | 73.1 min | 82.3 min | +9.2 min |

### translation_db 质量

- 74,004 条全部 status=ok，**0 error、0 warning**
- 325 条原文=译文（同值保留），全部合理：拟声词 315 + 人名/格式标签 10
- 中文占比 ≥ 30% 的条目占 92.7%（68,241/73,639），其余为短文本/拟声词/占位符混合

### 9 条未翻译条目逐条追查

#### 2 条空对话 — 原文为单个空格

| 文件 | 源码行 | 原文 | 根因 |
|------|--------|------|------|
| `v06.rpy:3451` | `v06.rpy:1311` | `" "`（空格） | 原文无实际内容，是剧情中的空白停顿 |
| `v06.rpy:3733` | `v06.rpy:1408` | `" "`（空格） | 同上 |

#### 7 条空字符串 — 命名输入框 / 游戏标题 / UI 按钮

| 文件 | 原文 | 根因 |
|------|------|------|
| `living_room.rpy:8821` | `My name is... (default = Irina)` | 命名输入框提示，含括号说明 |
| `living_room.rpy:8825` | `Her name is... (default = Miranda` | 同上，且原文**右括号缺失**（原文 bug） |
| `options.rpy:7` | `The Tyrant` | 游戏标题，通常不翻译 |
| `subway.rpy:2581` | `Her name is... (default = Susan)` | 命名输入框 |
| `stats.rpy:7` | `close` | UI 按钮文本，单词过短 |
| `fitness_studio.rpy:6661` | `My name is... (If left blank, her name will be Vivian.)` | 命名输入框，含长括号说明 |
| `subway.rpy:5125` | `Her name is... (If left blank, her name will be Susan.)` | 同上 |

#### 根因分类

| 根因 | 条数 | 说明 |
|------|------|------|
| 原文为空格（无需翻译） | 2 | `" "` 空白停顿 |
| 命名输入框提示语 | 4 | 含 `(default = xxx)` 括号说明，AI 视为系统文本 |
| 游戏标题 | 1 | `The Tyrant` — 通常保留原名 |
| UI 按钮 | 1 | `close` — 单词过短被忽略 |
| 原文有 bug（括号未闭合） | 1 | `(default = Miranda` — 缺右括号 |

**结论**：9 条遗漏全为边界 case，0 条正常对话漏翻。其中 3 条（2 空格 + 1 标题）本就不应翻译，实际有意义的遗漏仅 6 条（0.008%）。

### 改进效果确认

| 改进项 | 效果验证 |
|--------|----------|
| chunk 自动重试 | Checker 丢弃 4→2（-50%），API 瞬时故障恢复有效 |
| `[MULTILINE]` 标记 | 含 `\n` 多行条目未翻译从上次的 3 条降至 0（不计入本次 9 条中） |
| chunk 上下文 5 行 | Input tokens +3.4%，翻译连贯性改善（无法量化但成本可控） |
| 429/5xx 退避优化 | 10 线程 82 分钟无中断完成，多线程稳定性验证通过 |
| logging 系统 | `--verbose`/`--quiet` 正常工作，日志可读性提升 |
| file_processor 包拆分 | 外部 import 无变化，功能完全兼容 |
| 全文扫描安全性 | 0 条回写错误（translation_db 0 error） |
| 截断匹配阈值 0.7 | 0 条误匹配（上次有少量截断匹配错误） |
| tl_parser 75 项测试 | 全部通过，引号剥离/清理/后处理回归安全 |

---

## 已回滚

| 描述 | 原因 | 教训 |
|------|------|------|
| Prompt 强制覆盖指令（CRITICAL RULE） | 降低 AI 返回率 5 个百分点，增量覆盖导致丢翻译 | prompt 干预不如算法保障（占位符保护 + checker 过滤）可靠；强制指令可能干扰 AI 正常输出 |
| 增量翻译 + merge 覆盖架构 | 两次翻译覆盖范围不一致时丢数据，被 retranslate 模式替代 | 合并策略复杂度高且脆弱，不如"全量 + 补翻"两步走简单可靠 |

---

> 配置项速查表已移至 README §附录：配置项速查表

---

## Warning / Error Code 完整索引

### Error（结构性错误）

| Code | 含义 | 处理 |
|------|------|------|
| E100_LINE_COUNT_MISMATCH | 翻译后行数与原文不一致 | 标记错误 |
| E110_INDENT_CHANGED | 缩进被修改 | 标记错误 |
| E120_NON_STRING_MODIFIED | 非字符串行被修改 | 标记错误 |
| E130_DQUOTE_MISMATCH | 双引号结构不一致 | 标记错误 |
| E131_SQUOTE_MISMATCH | 单引号结构不一致 | 标记错误 |
| E140_CODE_STRUCT_CHANGED | 代码结构被修改 | 标记错误 |
| E210_VAR_MISSING | 译文缺少原文中的 `[var]` 变量 | 标记错误 |
| E220_TEXT_TAG_MISMATCH | `{tag}` 配对不一致 | 标记错误 |
| E230_MENU_ID_MISMATCH | `{#id}` 菜单标识符不一致 | 标记错误 |
| E240_FMT_PLACEHOLDER_MISMATCH | `%(name)s` 格式化占位符不一致 | 标记错误 |
| E411_GLOSSARY_LOCK_MISS | 锁定术语未使用规定译名 | 标记错误 |
| E420_NO_TRANSLATE_CHANGED | 禁翻片段被修改 | 标记错误 |

### Warning（质量告警）

| Code | 含义 | 处理 |
|------|------|------|
| W211_VAR_EXTRA | 译文含原文没有的 `[var]` 变量 | 仅告警 |
| W251_PLACEHOLDER_ORDER | 占位符顺序与原文不一致（集合相同） | 仅告警，仍 apply |
| W310_ESCAPED_NL_MISMATCH | 转义换行符 `\n` 数量不一致 | 仅告警 |
| W410_GLOSSARY_MISS | 术语表未命中 | 仅告警 |
| W420_SUSPECT_UNTRANSLATED | 疑似漏翻（原文 = 译文且符合英文特征） | 仅告警 |
| W430_LEN_RATIO_SUSPECT | 译文长度比例异常（过短或过长） | 仅告警 |
| W440_MODEL_SPEAKING | 译文含模型自我描述或多余解释 | 仅告警 |
| W441_PUNCT_MIX | 中英标点连续混用 | 仅告警 |
| W442_SUSPECT_ENGLISH_OUTPUT | 中文字符占比极低 | 仅告警 |

---

## 第八轮：代码质量八阶段优化

### 阶段一：错误处理加固（commit afb51e0）

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 52 | 8 处 `except Exception` 精细化为具体异常类型 | 多文件 | 更精确的错误处理 |
| 53 | `.tmp` 临时文件清理 | `main.py` | 进程安全性 |

### 阶段二：消除代码重复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 54 | 提取 `_restore_placeholders_in_translations()` 统一 4 处占位符还原逻辑 | `main.py` | 代码量 -20 行，维护点 4→1 |
| 55 | 提取 `_strip_char_prefix()` + `_CHAR_PREFIX_RE` 统一 2 处角色前缀清理 | `main.py` | 消除重复编译正则 |
| 56 | 提取 `_is_untranslated_dialogue()` + `_extract_dialogue_text()` 消除漏翻检测重复 | `one_click_pipeline.py` | 两个函数共享检测逻辑 |
| 57 | 删除 4 处冗余 `import re as _re`（模块级已有 `import re`） | `main.py` | 清理冗余 import |

### 阶段三：大函数拆分

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 58 | `one_click_pipeline.main()` 补翻阶段拆分为 `_run_retranslate_phase()` | `one_click_pipeline.py` | ~110 行独立函数 |
| 59 | `one_click_pipeline.main()` 最终报告拆分为 `_run_final_report()` | `one_click_pipeline.py` | ~120 行独立函数 |
| 60 | `run_tl_pipeline` 重试块使用 `_restore_placeholders_in_translations` 简化 | `main.py` | 消除 6 行重复代码 |

### 阶段四：validator 结构化拆分

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 61 | `validate_translation` 293 行拆为 4 个子检查函数 + 主入口调度 | `file_processor/validator.py` | 可读性大幅提升 |
|   | `_check_structural_integrity` — 缩进/非字符串行/引号结构/代码关键字 | | |
|   | `_check_placeholders_and_tags` — 变量/标签/菜单ID/格式化/顺序 | | |
|   | `_check_glossary_compliance` — 术语锁定/禁翻/漏翻疑似 | | |
|   | `_check_quality_heuristics` — 风格/长度比例/中文占比 | | |

### 阶段五：测试体系升级

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 62 | 新增 6 个集成测试（36→42）：密度自适应 / 跳过名单 / 漏翻检测 / TranslationDB 往返 / `_is_untranslated_dialogue` / `_restore_placeholders_in_translations` | `test_all.py` | 测试覆盖扩展 |
| 63 | CI 增加 `py_compile` 语法检查步骤（14 个 .py 文件） | `.github/workflows/test.yml` | CI 加固 |

### 阶段六：Magic Number 收敛

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 64 | `CHECKER_DROP_RATIO_THRESHOLD` / `MIN_DROPPED_FOR_WARNING` / `MIN_DIALOGUE_LENGTH` | `main.py` | 3 处硬编码→命名常量 |
| 65 | `MAX_FILE_RANK_SCORE` / `RISK_KEYWORD_SCORE` / `SAZMOD_BONUS_SCORE` / `MIN_UNTRANSLATED_TEXT_LENGTH` / `MIN_ENGLISH_CHARS_FOR_UNTRANSLATED` | `one_click_pipeline.py` | 5 处硬编码→命名常量 |
| 66 | `MIN_CHINESE_RATIO` | `file_processor/validator.py` | W442 阈值命名化 |

### 阶段七：项目工程化

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 67 | MIT LICENSE 文件 | `LICENSE`（新增） | 开源许可证 |
| 68 | `pyproject.toml`（name/version/requires-python/零依赖） | `pyproject.toml`（新增） | 项目元数据 |
| 69 | 4 处硬编码 Windows 路径改为环境变量可配置 | `test_single.py` / `verify_alignment.py` / `patch_font_now.py` / `revalidate.py` | 可移植性 |

### 阶段八：代码细节打磨

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 70 | 6 处 `except Exception:` 精细化为 `(KeyError, AttributeError, ValueError)` 等具体类型 | `api_client.py` / `glossary.py` / `translation_db.py` | 异常处理更精确 |
| 71 | `_SKIP_TOKENS` 常量提取（validator 中资源路径检测元组） | `file_processor/validator.py` | 可读性 |

---

## 第九轮：深度优化六阶段

### 阶段一：线程安全与健壮性加固

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 72 | 并发锁修复：`run_tl_pipeline` 的 `as_completed` 回调中 `n` → `n_completed` 局部变量，在锁内赋值锁外使用 | `main.py` | 消除潜在竞态 |
| 73 | CLI 参数校验：`_positive_int` / `_positive_float` / `_ratio_float` 三个校验函数，rpm/rps/timeout/max-chunk-tokens/max-response-tokens/min-dialogue-density 负值/零值防御 | `main.py` | 参数错误提前报错 |
| 74 | 词典文件提前校验：3 处 `load_dict` 前检查文件存在，不存在则 warning | `main.py` | 防静默忽略拼错路径 |
| 75 | ProgressTracker 规范化：`_load()` 捕获 JSON 损坏 + `setdefault` 确保必需 key | `main.py` | 防损坏文件 KeyError |

### 阶段二：深层代码重复消除

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 76 | `_filter_checked_translations()` 提取：checker 逐条过滤 + kept/dropped 分流（4 处→1 函数） | `main.py` | 消除 4 处重复 |
| 77 | `_deduplicate_translations()` 提取：`(line, original)` 去重（3 处→1 函数） | `main.py` | 消除 3 处重复 |

### 阶段三：性能优化

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 78 | `_build_fallback_dicts()` + `_match_string_entry_fallback()`：StringEntry 四层 fallback O(n*m)→O(1) 预建查找表 | `main.py` | 大项目性能提升 |
| 79 | ProgressTracker 批量写入：`SAVE_INTERVAL=10`，每 10 次 mark 才写磁盘 | `main.py` | 减少磁盘 I/O |

### 阶段四：API 兼容性加固

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 80 | 空 choices 响应显式 warning（不再静默返回空字符串） | `api_client.py` | 更好的错误诊断 |
| 81 | HTTP 404 → 立即报错"模型不存在"（不重试）；HTTP 401 → 立即报错"认证失败" | `api_client.py` | 避免无意义重试 |
| 82 | 推理模型自动 timeout 提升：`is_reasoning_model()` 检测到时 timeout 从 180s 提升到 300s | `api_client.py` | 推理模型稳定性 |

### 阶段五：测试深度覆盖

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 83 | 新增 8 个测试（42→50）：progress resume/normalize、`_filter_checked_translations`、`_deduplicate_translations`、`_match_string_entry_fallback`、推理模型检测、CLI 参数校验、推理模型 timeout | `test_all.py` | 测试覆盖扩展 |

### 阶段六：文档与代码卫生

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 84 | `TranslationDB.has_entry()` 公共方法替代 `_index` 直接访问 | `translation_db.py` `main.py` | 封装性 |
| 85 | 过期注释修正（"外部模板" → "术语表 + 项目名"） | `main.py` | 准确性 |

---

## 第十轮：功能加固与生态完善六阶段

### 阶段一：控制标签保护确认

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 86 | 确认现有 tag 正则 `\{/?[a-zA-Z]+=?[^}]*\}` 已覆盖 `{w}/{p}/{nw}/{fast}/{cps=N}/{done}` 等控制标签；新增测试 `test_protect_control_tags` 确认 | `test_all.py` | 测试覆盖 |

### 阶段二：启动器安全增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 87 | API Key 输入改用 `getpass.getpass()` 隐藏明文回显 | `start_launcher.py` | 安全性 |
| 88 | 命令预览中 API Key 显示为 `****` | `start_launcher.py` | 安全性 |

### 阶段三：CI 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 89 | 零第三方依赖自动检查：扫描全部 .py import，排除标准库和本地模块后报错 | `.github/workflows/test.yml` | CI 防护 |
| 90 | `--dry-run` 集成测试：用 `tests/tl_priority_mini` 目录验证完整 dry-run 流程不崩溃 | `.github/workflows/test.yml` | CI 防护 |

### 阶段四：Glossary 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 91 | 连字符人名正则：`[A-Z][a-z]+(?:-[A-Z][a-z]+)*` 匹配 `Mary-Jane` 等复合人名 | `glossary.py` | 术语提取准确率 |
| 92 | 翻译记忆信心度：`_memory_count` 追踪出现次数，`to_prompt_text` 只输出 count>=2 的记忆 | `glossary.py` | Prompt 质量 |

### 阶段五：文档完善

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 93 | README 新增"各提供商用法示例"：xAI/OpenAI/DeepSeek/Claude/Gemini 各一个完整命令行 | `README.md` | 用户体验 |
| 94 | README 新增"性能调优"表：各提供商推荐 workers/rpm/rps 配置 | `README.md` | 用户体验 |
| 95 | README 新增"故障排查"FAQ：API 超时/编码错误/进度损坏/漏翻率/词典不生效 5 项 | `README.md` | 用户体验 |

### 阶段六：跨平台兼容

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 96 | subprocess 调用 main.py 改用 `Path(__file__).parent / "main.py"` 绝对路径 | `one_click_pipeline.py` | Linux/Mac 兼容 |

---

## 第十一轮阶段一：main.py 模块拆分

### 结构变更

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 97 | 新建 `translation_utils.py`（263 行）：从 main.py 提取 ChunkResult / ProgressTracker / 所有公共辅助函数和常量 | `translation_utils.py`（新增）`main.py` | 公共基础设施独立 |
| 98 | 新建 `direct_translator.py`（943 行）：从 main.py 迁移 translate_file / _translate_file_targeted / run_pipeline | `direct_translator.py`（新增）`main.py` | direct-mode 引擎独立 |
| 99 | 新建 `retranslator.py`（487 行）：从 main.py 迁移 retranslate_file / find_untranslated_lines / build_retranslate_chunks / calculate_dialogue_density / run_retranslate_pipeline | `retranslator.py`（新增）`main.py` | 补翻引擎独立 |
| 100 | 新建 `tl_translator.py`（638 行）：从 main.py 迁移 run_tl_pipeline / build_tl_chunks / _apply_tl_game_patches / _inject_language_buttons / _clean_rpyc | `tl_translator.py`（新增）`main.py` | tl-mode 引擎独立 |
| 101 | main.py 瘦身为 233 行 CLI 入口 + 向后兼容 re-export（确保 `from main import ...` 不断裂） | `main.py` | 降幅 89% |
| 102 | CI 增加 4 个新模块的 py_compile 语法检查 | `.github/workflows/test.yml` | CI 覆盖 |
| 103 | 清理未使用 import（tl_translator.py 中 `apply_font_patch` 未使用已移除） | `tl_translator.py` | 代码卫生 |
| 104 | 新增 `TranslationContext` dataclass，替代嵌套函数的闭包变量捕获（`client` / `system_prompt` / `rel_path`） | `translation_utils.py` | 闭包重构 |
| 105 | `_translate_chunk` / `_should_retry` / `_translate_chunk_with_retry` 从 translate_file 内嵌套函数提升为模块级函数（接收 ctx 参数） | `direct_translator.py` | 闭包重构 |
| 106 | `_translate_one_tl_chunk` 从 run_tl_pipeline 内嵌套函数提升为模块级函数 | `tl_translator.py` | 闭包重构 |

---

## 第十一轮阶段二+三：回写失败分析与修复

### 阶段二：数据采集与分析

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 107 | `_diagnose_writeback_failure()` 诊断函数：分析每条回写失败的根因（WF-01~08 分类） | `file_processor/patcher.py` | 新增 ~80 行 |
| 108 | `apply_translations` 失败路径记录 `status="writeback_failed"` + diagnostic 字段到 translation_db | `direct_translator.py` | 数据采集 |
| 109 | `analyze_writeback_failures.py` 独立分析脚本（分类统计 + 典型样本 + JSON 报告） | 新增 | ~120 行 |

### 分析结果（The Tyrant, 140 文件, direct-mode）

| 指标 | 第三轮基线 | 第十一轮 |
|------|-----------|---------|
| 回写失败总数 | 609 | **28**（降 95%） |
| 主要失败类型 | 未分类 | WF-08（82%）：`_replace_string_in_line` 不支持含前缀的 original |

### 阶段三：基于数据的修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 110 | `_replace_string_in_line` 阶段 1b：剥离 AI 返回的行前缀（`text _("` / `textbutton "` / `text "`） | `file_processor/patcher.py` | 修复 WF-08 主因 |
| 111 | 阶段 3 正则升级：`"([^"]+)"` → `"((?:[^"\\]|\\.)+)"` 支持转义引号 | `file_processor/patcher.py` | 修复 WF-04 |
| 112 | 阶段 3f：用剥离后 original 在 quoted_parts 中 fallback 匹配 | `file_processor/patcher.py` | 兜底修复 |
| 113 | 新增 2 个测试：`test_replace_string_prefix_strip` + `test_replace_string_escaped_quotes` | `test_all.py` | 测试 53→55 |

---

## 第十一轮阶段四：config.json 配置文件支持

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 114 | `config.py` 新增（~140行）：Config 类 + DEFAULTS 字典 + 三层合并（CLI>配置文件>DEFAULTS）+ `resolve_api_key()`（api_key_env/api_key_file） | `config.py`（新增） | 配置管理 |
| 115 | `renpy_translate.example.json` 示例配置文件 | 新增 | 用户模板 |
| 116 | main.py argparse 18 个参数改 `default=None` + 新增 `--config` 参数 + Config 集成填充 args | `main.py` | CLI 行为变更（向后兼容） |
| 117 | `.gitignore` 新增 `renpy_translate.json` 排除 | `.gitignore` | 防误提交 |
| 118 | CI 新增 `config.py` + `analyze_writeback_failures.py` py_compile | `.github/workflows/test.yml` | CI 覆盖 |
| 119 | 新增 3 个测试（55→58）：config 默认值 / CLI 覆盖 / 配置文件加载 | `test_all.py` | 测试覆盖 |
| 120 | README 新增"配置文件（可选）"章节 | `README.md` | 用户文档 |

---

## 第十一轮阶段五：Review HTML + 进度增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 121 | `ProgressBar` 类加入 translation_utils.py（~60行）：Unicode/ASCII 自适应 + `_detect_unicode_support()` GBK 安全 | `translation_utils.py` | 进度显示 |
| 122 | `review_generator.py` 新增（~150行）：HTML 翻译校对报告（side-by-side + 深色主题 + 按文件折叠 + error/warning/fail 颜色高亮 + 统计摘要） | `review_generator.py`（新增） | 校对工具 |
| 123 | `direct_translator.py` run_pipeline 集成 ProgressBar（非 quiet/dry-run 模式） | `direct_translator.py` | 用户体验 |
| 124 | main.py re-export ProgressBar + CI 新增 review_generator.py py_compile | `main.py` `.github/workflows/test.yml` | 兼容+CI |
| 125 | 新增 2 个测试（58→60）：ProgressBar 渲染 + review HTML 生成 | `test_all.py` | 测试覆盖 |

---

## 第十一轮阶段六：类型注解

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 126 | 全部公共 API 补齐返回类型注解（ProgressTracker 6 个方法 + APIConfig.__post_init__） | `translation_utils.py` `api_client.py` | 类型安全 |
| 127 | `read_file(path)` → `read_file(path: object)` 参数注解 | `file_processor/splitter.py` | 参数注解 |
| 128 | `update_stats(value)` → `update_stats(value: object)` 参数注解 | `translation_utils.py` | 参数注解 |
| 129 | `py.typed` PEP 561 marker 文件 | `py.typed`（新增） | 类型包标记 |
| 130 | CI 新增 mypy 步骤（`continue-on-error: true`，informational） | `.github/workflows/test.yml` | CI 类型检查 |

---

## 第十一轮阶段七：目标语言参数化抽象层

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 131 | `lang_config.py` 新增（~130行）：LanguageConfig dataclass（code/name/native_name/detector/min_ratio/instruction/style_notes/glossary_field/field_aliases） | `lang_config.py`（新增） | 多语言基础设施 |
| 132 | 预置 4 种语言配置：zh（简体中文）/ zh-tw（繁体中文）/ ja（日语）/ ko（韩语） | `lang_config.py` | 开箱即用 |
| 133 | `detect_chinese/japanese/korean_ratio()` 文字检测函数 | `lang_config.py` | W442 参数化基础 |
| 134 | `get_language_config()` 查找 + 不存在回退 zh；`resolve_translation_field()` 兼容别名读取 | `lang_config.py` | 容错 + 兼容 |
| 135 | main.py 集成：`args.lang_config = get_language_config(args.target_lang)` | `main.py` | 全局挂载 |
| 136 | 中文 prompt 基线 `tests/zh_prompt_baseline.txt` + 零变更回归验证 | `tests/`（新增） | 安全网 |
| 137 | 新增 3 个测试（60→63）：语言检测 / 配置查找与回退 / 兼容字段读取 | `test_all.py` | 测试覆盖 |
| 138 | CI 新增 `lang_config.py` py_compile | `.github/workflows/test.yml` | CI |

---

## 第十一轮阶段八：Prompt + Validator 多语言适配

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 139 | `build_system_prompt` 新增 `lang_config` 参数：zh/zh-tw 走 `_build_chinese_system_prompt`（现有逻辑零变更），其他走 `_build_generic_system_prompt` | `prompts.py` | Prompt 多语言 |
| 140 | `_GENERIC_SYSTEM_PROMPT_TEMPLATE` 英文通用模板（含动态 `{field}` JSON 字段名 + 语言指令 + 风格注释） | `prompts.py` | ja/ko 支持 |
| 141 | `validate_translation` + `_check_quality_heuristics` 新增 `lang_config` 参数：W442 使用 `target_script_detector` + `min_target_ratio` 参数化 | `file_processor/validator.py` | W442 多语言 |
| 142 | 新增 3 个测试（63→66）：中文 prompt 零变更回归 / 日语通用模板内容验证 / validator lang_config 参数化 | `test_all.py` | 测试覆盖 |

---

## 第十二轮：阶段零四项优化

> 对应 EXPANSION_PLAN.md §1「当前 Ren'Py 工具优化」，在多引擎扩展之前落地四项低风险高价值改进。

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 143 | chunk 截断自动拆分重试：`_should_retry` 返回 `(should, needs_split)` 元组，`returned < expected * 0.5` 触发截断检测；`_split_chunk` 三级拆分（label/screen 边界 > 空行 > 二等分）；`_translate_chunk_with_retry` 拆分后分别翻译再合并，单层不递归 | `direct_translator.py` | 大 chunk 截断时翻译完整度提升 |
| 144 | tl-mode .rpyc 精确清理：`_clean_rpyc` 新增 `modified_files` 参数，只删除本次修改的 .rpy 对应的 .rpyc；`run_tl_pipeline` 收集 `modified_rpy_files` 集合 | `tl_translator.py` | 精确清理而非全目录 |
| 145 | `--no-clean-rpyc` CLI 参数：禁用 tl-mode 翻译后的 .rpyc 缓存清理 | `main.py` | 新增 CLI 参数 |
| 146 | dry-run verbose 增强：`--verbose` 时输出每文件对话行数/密度/策略/费用 + 密度分布直方图 + 术语扫描预览 | `direct_translator.py` | 仅 verbose 模式新增输出 |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 147 | `one_click_pipeline.py` main() 拆分：提取 `_run_pilot_phase` / `_run_full_translation_phase` / `_run_tl_mode_phase` 三个阶段函数，main() 从 ~280 行缩减到 ~113 行纯编排 | `one_click_pipeline.py` | 纯重构，零行为变更 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 148 | 新增 4 个测试（66→70）：`test_should_retry_truncation`（截断检测 + 边界 returned=0/expected=0）/ `test_should_retry_normal`（正常+丢弃率过高）/ `test_split_chunk_basic`（行数守恒+offset）/ `test_split_chunk_at_empty_line`（空行拆分优先） | `test_all.py` | 测试覆盖 |

---

## 第十二轮 阶段一：引擎抽象层骨架

> 对应 EXPANSION_PLAN.md §2「引擎抽象层设计」+ §9 阶段一里程碑 M1。

### 新增文件

| # | 描述 | 文件 | 行数 |
|---|------|------|------|
| 149 | `EngineProfile` 数据类（9 字段 + 占位符/skip 编译方法）+ `TranslatableUnit` 数据类（8 字段）+ `EngineBase` ABC（4 抽象 + 3 可选方法）+ 内置 Profile 常量（RENPY / RPGMAKER_MV / CSV）+ `ENGINE_PROFILES` 注册表 | `engine_base.py`（新增） | ~202 |
| 150 | `EngineType` 枚举（6 值）+ `detect_engine_type` 目录特征扫描（5 级优先：Ren'Py > MV > MZ > VXAce > Unknown）+ `create_engine` 延迟导入工厂 + `resolve_engine` CLI 路由 + 未识别时 top 10 扩展名诊断 | `engine_detector.py`（新增） | ~160 |
| 151 | `RenPyEngine` 薄包装：`detect()` 检查 .rpy/.rpa、`run()` 路由到三条管线（延迟导入 + try-except）、`extract_texts()`/`write_back()` 抛 NotImplementedError | `engines/renpy_engine.py`（新增） | ~74 |
| 152 | 引擎实现包声明 | `engines/__init__.py`（新增） | ~3 |

### 修改文件

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 153 | `--engine` CLI 参数（auto/renpy/rpgmaker/csv/jsonl）；路由：auto/renpy 走原路径零改动，其他走 `resolve_engine()` | `main.py` | 向后兼容，默认行为不变 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 154 | 新增 `test_engines.py`（25 个测试）：EngineProfile 编译 6 + TranslatableUnit 默认值 3 + 引擎检测 10 + RenPyEngine 5 + EngineBase dry_run 1 | `test_engines.py`（新增） | 引擎抽象层全覆盖 |

---

## 第十二轮 阶段二：CSV/JSONL + 通用翻译流水线

> 对应 EXPANSION_PLAN.md §4-§6 阶段二里程碑 M2。

### 新增文件

| # | 描述 | 文件 | 行数 |
|---|------|------|------|
| 155 | 通用翻译流水线（6 阶段：提取→初始化→分块→并发翻译→回写→报告）+ GenericChunk 数据类 + build_generic_chunks 按 file_path 分组拆块 + translation_db 断点恢复 + RPG Maker 术语扫描钩子 + 原子进度写入 | `generic_pipeline.py`（新增） | ~414 |
| 156 | CSVEngine（CSV/TSV/JSONL/JSON 读写）：列名别名自动匹配（original/source/text/en 等 6 组）+ UTF-8 BOM + 多行 CSV 值安全读取 + 目录批量扫描 + 按源格式分流回写 | `engines/csv_engine.py`（新增） | ~317 |

### 修改文件

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 157 | `protect_placeholders` 新增 `patterns` 参数；`check_response_item` 新增 `placeholder_re` 参数；`_extract_placeholder_sequence` 新增 `regex` 参数。全部默认 None 走 Ren'Py 模式 | `file_processor/checker.py` | 向后兼容 |
| 158 | `_ENGINE_PROMPT_ADDONS` 字典（rpgmaker/generic 两条 addon）+ `build_system_prompt` 新增 `engine_profile` 参数；None 时零变更 | `prompts.py` | 向后兼容 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 159 | 新增 22 个引擎测试（25→47）：CSV 提取 5 + JSONL 3 + 回写 2 + 目录扫描 1 + 分块 3 + 匹配 2 + patcher 参数化 2 + checker 参数化 2 + prompts addon 2 | `test_engines.py` | 引擎测试覆盖 |

---

## 第十二轮 阶段三：RPG Maker MV/MZ 引擎

> 对应 EXPANSION_PLAN.md §3 阶段三里程碑 M3。

### 新增文件

| # | 描述 | 文件 | 行数 |
|---|------|------|------|
| 160 | RPGMakerMVEngine：目录定位（MV www/data/ vs MZ data/）+ 事件指令提取（401/405 连续合并、102 选项遍历、402 When、320/324 改名）+ 8 种数据库文件提取（_DB_FIELDS 配置表）+ System.json 提取（简单字段 + 数组 + terms.*）+ JSON path 导航回写（_navigate_to_node + _patch_by_json_path）+ 对话块拆分回写（行数不匹配处理）+ 紧凑 JSON 输出 + 字体安装提示 | `engines/rpgmaker_engine.py`（新增） | ~636 |

### 修改文件

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 161 | `scan_rpgmaker_database(game_dir)` 新增：从 Actors.json 提取角色名（name/nickname）+ 从 System.json 提取系统术语（terms.basic/commands/params）；线程安全 | `glossary.py` | 新增方法，现有行为不变 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 162 | 新增 15 个 RPG Maker 测试（47→62）：检测 3 + 目录定位 1 + 事件指令 4（401 合并/102 选项/405 滚动/320 改名）+ 数据库 1 + System 1 + 回写 2 + JSON path 2 + glossary 1 | `test_engines.py` | 引擎测试覆盖 |

---

## 第十二轮 阶段四：文档 + 发布

> 对应 EXPANSION_PLAN.md §9 阶段四里程碑 M4。

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 163 | start_launcher.py 新增模式 8（RPG Maker MV/MZ 翻译）和模式 9（CSV/JSONL 通用格式翻译）；菜单标题改为「多引擎游戏汉化统一启动器」；分类显示（Ren'Py / 其他引擎 / 工具） | `start_launcher.py` | 新增菜单选项 |
| 164 | README/CHANGELOG/TEST_PLAN/.cursor_prompt/EXPANSION_PLAN 全部文档已在各阶段增量更新完成 | 多文件 | 文档齐全 |

---

## 第十二轮 结构整理：项目目录重构

| # | 描述 | 影响 |
|---|------|------|
| 165 | 测试文件移入 `tests/`：test_all.py / test_engines.py / test_single.py + sys.path 修正 | 根目录 -3 |
| 166 | 独立工具移入 `tools/`（新建）：verify_alignment / revalidate / patch_font_now / analyze_writeback_failures + sys.path 修正 | 根目录 -4 |
| 167 | 引擎抽象层合并到 `engines/` 包：engine_base / engine_detector / generic_pipeline 移入 + `engines/__init__.py` 新增 re-export（EngineProfile / TranslatableUnit / EngineBase / EngineType 等） | 根目录 -3 |
| 168 | 全量 import 路径更新：`from engine_base import` → `from engines.engine_base import`（main.py + 4 引擎 + 3 测试 + 3 工具共 11 个文件） | 零功能变更 |
| 169 | 清理所有 `__pycache__/` 目录 | 磁盘清理 |

**结果**：根目录 .py 文件 **27 → 17**，目录结构清晰分层。132 测试全绿。

---

## 第十二轮 GUI：图形界面 + PyInstaller 打包

| # | 描述 | 文件 | 行数 |
|---|------|------|------|
| 170 | Tkinter GUI 启动器：3 Tab 分页（基本设置 + 翻译设置动态引擎面板 + 高级设置）、引擎选择联动面板切换、API key 隐藏（Entry show="*" + 命令预览 ****）、命令预览实时更新、内嵌 ScrolledText 日志（queue.Queue 线程安全轮询）、subprocess 后台执行 + kill 停止、配置加载/保存（JSON）、工具菜单（Dry-run 摘要弹窗 + 升级扫描）、DPI 适配 | `gui.py`（新增） | ~753 |
| 171 | PyInstaller 打包脚本：29 个 hidden-import + 资源文件打包 → 单文件 .exe（32MB） | `build.py`（新增） | ~100 |
| 172 | .gitignore 新增 build/dist/*.spec 排除 | `.gitignore` | +4 行 |

---

## 第十三轮：四项功能优化

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 173 | `_run_final_report()` 中 TranslationDB merge 后自动调用 `generate_review_html()` 生成 `review.html` 校对报告 | `one_click_pipeline.py` | pipeline 产物新增 review.html |
| 174 | `load_font_config(config_path)` + `font_config.json` 支持 `gui_overrides`（字号/布局参数）；`apply_font_patch()` 新增 `font_config_path` 可选参数；`--font-config` CLI 参数 | `font_patch.py`, `main.py` | 字体补丁可配置化 |
| 175 | tl/none 覆盖模板：`_apply_tl_game_patches()` 不再直接修改 gui.rpy，改为生成 `tl/<lang>/none_overlay.rpy`（`translate None python:` 运行时覆盖字体）；支持 font_config.json gui_overrides | `tl_translator.py` | gui.rpy 不被修改，游戏更新安全 |
| 176 | CoT 思维链翻译模式：`--cot` CLI flag；`_COT_ADDON_ZH` / `_COT_ADDON_EN` 双语 addon（直译→校正→意译三步）；`build_system_prompt(cot=)` + `build_tl_system_prompt(cot=)` 参数化 | `prompts.py`, `main.py`, `direct_translator.py`, `tl_translator.py` | 可选质量增强（费用 +30-50%） |
| 177 | `font_config.example.json` 示例配置文件 | 新增 | 用户模板 |

---

## 第四十三轮：r36-r42 累计专项审计 + 3 个 test 补 + 1 个插件子进程 stdout 封顶 (round 47 archive push)

**审计结果概览**：

- **Correctness agent**：23 个审计点全 pass，0 CRITICAL / 0 HIGH（r36-r42
  改动 code-level 正确性 clean，包括 r42 JSON cap 7 处 fallback / r41
  mixin `self._project_root` init 顺序 / r42 checker deferred import 保
  r27 A-H-2 layering / TOCTOU windows / signature consistency 等）
- **Test coverage agent**：3 项 valid gap + 3 项 false-positive（被
  overly-detailed boundary testing / 已被现有 test 隐含覆盖的 path / 标
  准 try/finally 已足够的 isolation）
- **Security agent**：1 项 valid defensive improvement + 5 项
  theoretical-only / false-positive（post-parse size check 无法用
  `sys.getsizeof` 实现，monkey-patch 威胁已属 "attacker has RCE" 范畴，
  env var leakage on Windows 权限隔离足够，等等）

3 项 valid 发现合流到 r43：

**Commit 1：Test coverage 补齐（3 个 new test）**

491. `tests/test_multilang_run.py::test_check_response_item_zh_tw_rejects_
generic_zh_field` — 钉住 `LANGUAGE_CONFIGS["zh-tw"].field_aliases =
["zh-tw", "zh_tw", "traditional_chinese"]` **刻意不含 bare "zh"** 的设
计决策。否则 model 习惯性 emit `"zh"` 会悄悄落进 zh-tw bucket 而
Simplified / Traditional 的脚本家族混淆没人察觉。正向 case 也测：
"zh-tw" / "traditional_chinese" alias 被接受
492. `tests/test_multilang_run.py::test_check_response_item_mixed_
language_fields_picks_correct_alias` — 文档化 `resolve_translation_
field` 的 alias 优先级契约：item 同时含 `"ja"` + `"ko"` 时，ja config
读 ja 字段，ko config 读 ko 字段；ja-empty 但 ko-populated 在 ja
config 下被拒（ko 不在 ja 别名链）
493. `tests/test_translation_state.py::test_progress_tracker_handles_
stat_failure_gracefully` — 覆盖 r42 M2 phase-3 的"stat() OSError →
size=0 → 继续 read"两步降级路径。用 `mock.patch.object(Path, "stat",
_selective_raise)` 让目标 progress.json stat() 抛 OSError，验证
`read_text()` 仍成功时 data **不会被错误重置**。填补了 "stat fails
but read works" 的路径覆盖缺口（原先只测 "文件太大"）

测试 **405 → 408**（test_multilang_run 14→16 / test_translation_state
18→19 / meta-runner 149→150）

**Commit 2：插件子进程 response line 50 MB 封顶（defensive）**

r30 已为 `_SubprocessPluginClient` stderr 加 10 KB cap 防 crash 日志
OOM host。但 **stdout response 通道无 cap** —— 若 plugin 恶意（或故障）
emit unbounded 单行 JSON，`readline()` 无 size 会一直累积到 OOM，早
于任何 JSON decoder 介入。r43 audit surfaced 为 valid defensive
improvement。

494. `core/api_plugin.py` 新增 `_MAX_PLUGIN_RESPONSE_BYTES = 50 * 1024
* 1024` 模块常量（与 r37-r42 JSON loader cap 跨模块一致）。legitimate
batch response typically < 1 MB，50 MB 留足冗余
495. `_read_response_line` 的内部 `_reader()` 改为 `readline(
_MAX_PLUGIN_RESPONSE_BYTES)`。Python `readline(N)` 返回至多 N bytes
**或**到 `\n` 为止，谁先到谁先返回 — 若 plugin 在 N bytes 前没发
newline，被视为 malformed oversized 响应 raise RuntimeError（与既有
"plugin stuck" / "EOFError" 路径同风格 wrap）
496. `tests/test_custom_engine.py::test_sandbox_rejects_oversize_
response_line` — stub `_proc.stdout` + `mock.patch.object` 把 cap 缩到
1 KB 验证语义（避免实际 alloc 50 MB）。与 r30 的 `test_sandbox_
stderr_read_bounded` 成对，共同 bound plugin 的 stdin/stdout/stderr
三通道

测试 test_custom_engine 20→21（独立 suite）；total **408 → 409**

**Commit 3：Docs sync**

497. 本文件（CHANGELOG_RECENT.md）：round 40 详细压缩进"演进摘要"一行；
41/42/43 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
498. CLAUDE.md 项目身份段追加 r43 note + 测试数 405 → 409；`.cursorrules`
同步（字节相同）
499. HANDOFF.md 重写为 43 → 44 交接；r43 三项修从"r43 候选"挪到"✅ r43
已修"；保留 PyInstaller smoke test + GUI manual smoke test（三轮积压）
+ 非 zh 端到端验证 + A-H-3 / S-H-4 / CI / docs 复查作 r44 候选。
架构健康度表更新：**插件子进程三通道封顶完整**（stdin via
`_SHUTDOWN_REQUEST_ID` + stdout via r43 50 MB cap + stderr via r30
10 KB cap）

**结果**：

- **22 测试文件**（21 独立 suite + `test_all.py` meta；r43 无新 .py）
  + `tl_parser` 75 + `screen` 51 = **535 断言点**；测试 **405 → 409**
  （+4：zh-tw rejects +1 / mixed-lang +1 / stat fallback +1 / oversize
  response line +1）
- 所有改动向后兼容：
  - Test 补齐：纯新增 assertion，零现有 test 受影响
  - Plugin stdout cap：合法 response 行（< 50 MB）完全不受影响；只有
    malformed / 恶意 oversized 情况才触发 RuntimeError，走已有
    error-wrapping path
- **新增文件 0 个**
- **修改文件 1 代码 + 3 测试 + 4 文档**：
  - `core/api_plugin.py` +cap 常量 + `_read_response_line` size-bounded
    readline
  - `tests/test_multilang_run.py` +2 tests
  - `tests/test_translation_state.py` +1 test
  - `tests/test_custom_engine.py` +1 test
  - CHANGELOG / CLAUDE / `.cursorrules` / HANDOFF
- **文件大小检查**：所有源码 / 测试 < 800 保持

**审计连续性统计**（连续 3 次 3 维度 审计）：

| 审计轮 | CRITICAL | HIGH | MEDIUM (已修) | LOW | False Positive | OOS |
|-------|---------|------|------|-----|---------------|-----|
| r35 末（r31-35） | 0 | 0 | 2 (H1, H2 → r36) | 0 | 6 | — |
| r40 末（r36-40） | 0 | 0 | 2 (M4, r39 integ → r41) | 1 | 3 | 2 |
| r43（r36-42） | 0 | 0 | 3 (zh-tw / mixed-lang / stat) + 1 defensive (stdout cap) → r43 | 1 | 6 | 3 |

**趋势**：连续 3 次审计均无 CRITICAL/HIGH；每次找到的 MEDIUM/LOW 都在
对应的下一轮合流修复；False-positive 和 OOS 比例稳定在 ~30-40%（正常
量级，说明 agent 报告质量稳定）。

**本轮未做**（留给第 44+ 轮）：

- **PyInstaller 打包 smoke test**（r41/r42/r43 **三轮积压**）—
  HANDOFF 最高优先，需 `pip install pyinstaller`（用户 approve） +
  跑 `python build.py` + `dist/多引擎游戏汉化工具.exe` 启动 smoke；
  若 fail 回退加 `gui_handlers`/`gui_pipeline`/`gui_dialogs` 到
  `build.py::hidden_imports`
- **GUI 手动 smoke test 全面清单**（r41/r42/r43 **三轮积压**）— 需
  人工点击 Tab / 按钮 / 菜单 / 工具菜单 / 配置保存加载 验证 Tkinter
  callback 真实运行时正确 dispatch + mixin MRO 工作
- 非中文目标语言端到端验证（r39 prompt + r41 alias read + r42 checker
  三层锁死 code-level contract，需真实 API + 真实游戏跑 ja / ko / zh-tw）
- A-H-3 Medium / Deep / S-H-4 Breaking — 需真实 API + 游戏验证
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants / quality_chain / roadmap 复查
  （连续 14 轮欠账）

---

## 关键发现与经验

1. **对话密度是漏翻率最强相关因子**：< 10% 密度文件漏翻中位数 57.69%，≥ 40% 仅 4.54%
2. **Prompt 强化无效甚至有害**：CRITICAL RULE 降低 AI 返回率 5pp，引入翻译不一致性
3. **tl-mode 精度远高于 direct-mode**：行号精确定位 vs 文本匹配回写，可消除"回写失败"类漏翻
4. **AI 约 14% 概率返回带外层引号**：ASCII / 弯引号 / 全角，需循环剥离
5. **旧增量架构有结构性缺陷**：两次翻译覆盖范围不一致时丢数据，retranslate 模式解决
6. **占位符保护对 Checker 通过率有显著正面影响**：从基线到 +2pp
7. **tl-mode 剩余遗漏全为边界 case**：空格原文、命名输入框提示、游戏标题、原文 bug（括号未闭合），0 条正常对话漏翻
8. **chunk 自动重试对 Checker 丢弃有直接效果**：4→2（-50%），验证了重试策略的价值
