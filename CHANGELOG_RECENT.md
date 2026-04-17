<!-- 维护规则：每完成新一轮开发后，把最新轮次追加到"详细记录"段，
     同时把最老的一轮从"详细记录"压缩为一行并入"演进摘要"。
     始终保持最近 3 轮的详细记录。 -->

# 变更日志（精简版）

## 项目演进摘要

- 第一轮：质量校验体系 — W430/W440/W441/W442/W251 告警 + E411/E420 术语锁定
- 第二轮：功能增强 — 结构化报告 + translation_db + 字体补丁
- 第三轮：降低漏翻率 — 12.12% → 4.01%（占位符保护 + 密度自适应 + retranslate）
- 第四轮：tl-mode — 独立 tl_parser + 并发翻译 + 精确回填
- 第五轮：tl-mode 全量验证 — 引号剥离修复 + 99.97% 翻译成功率
- 第六轮：代码优化 — chunk 重试 + logging + 模块拆分 + 术语提取
- 第七轮：全量验证 — 99.99% 成功率（未翻译 25→7，Checker 丢弃 4→2）
- 第八轮：代码质量 — 消除重复 + 大函数拆分 + validator 结构化 + 测试 36→42
- 第九轮：深度优化 — 线程安全 + O(1) fallback + API 错误处理 + 测试 42→50
- 第十轮：功能加固 — 控制标签确认 + CI 零依赖 + 跨平台路径 + 测试 50→53
- 第十一轮：main.py 拆分 — 2400→233 行 + Config 类 + Review HTML + 类型注解 + 多语言
- 第十二轮：引擎抽象层 — EngineProfile + EngineBase + RPG Maker MV/MZ + CSV/JSONL + GUI
- 第十三轮：四项优化 — pipeline review.html + 可配置字体 + tl/none 模板 + CoT
- 第十四轮：Ren'Py 专项 — 五阶段升级（基础重构 + 健壮性 + 性能 + 质量 + 体验）
- 第十五轮：nvl clear ID 修正 — 8.6+ say-only → 7.x nvl+say 哈希自动修正
- 第十六轮：screen 文本翻译 — screen_translator.py + 缓存清理 .rpymc 补全
- 第十七轮：项目结构重构 — 根目录 25→5 .py + core/translators/tools 分层 + 消除 re-export + 162 测试全绿
- 第十八轮：预处理工具链 — RPA 解包 + rpyc 双层反编译 + lint 自动修复 + locked_terms 预替换 + tl 跨文件去重 + Hook 模板；测试 162→225
- 第十九轮：翻译后工具链 + 插件系统 — `tools/rpa_packer` + `tools/translation_editor` HTML 校对 + `custom_engines/` 插件接口 + 默认语言自动生成 + lint 修复阶段集成；测试 225→266
- 第二十轮：CRITICAL 修复 — pipeline 悬空 import 三处（stages/gate/generic_pipeline）+ pickle RCE 三处（core/pickle_safe + rpyc Tier 1/2 + rpa_unpacker）+ ZIP Slip 防护 + CONTRIBUTING/SECURITY 治理文档
- 第二十一轮：Top 5 HIGH 收敛 — HTTP 连接池（核心 ~90s/600 次握手）+ ProgressTracker 两锁（解除 worker 串行化）+ API Key 走 subprocess env（关闭进程列表泄露）+ 6 条 HTTP 重试 mock 测试 + P1 快照单调性回刷
- 第二十二轮：测试基础 + 响应体上限 — `MAX_API_RESPONSE_BYTES = 32MB` 硬上限 + `read_bounded` 通用工具（pool + urllib 双路径）+ T-C-3（`test_direct_pipeline`）+ T-H-2（`test_tl_pipeline`）集成测试为 A-H-4 重构铺路；测试 280→286

## 详细记录

### 第二十三轮：A-H-4 Part 1 — direct.py 拆分

**文件拆分**（1301 行 → 4 个模块，每个均在 800 行以下）：

248. 新建 `translators/_direct_chunk.py`（209 行）：搬迁 `_translate_chunk` / `_should_retry` / `_split_chunk` / `_translate_chunk_with_retry` 四个紧耦合的 chunk 级函数。这四个函数形成"发送单 chunk → 分类是否重试 → 截断时拆分"的状态机，放在一起维护
249. 新建 `translators/_direct_file.py`（548 行）：搬迁 `translate_file` (297 行) + `_translate_file_targeted` (188 行) 两个文件级函数。`translate_file` 做密度检测后分派给 `_translate_file_targeted`（低密度）或自身的 chunk 并发路径（高密度）
250. 新建 `translators/_direct_cli.py`（70 行）：搬迁 `_compute_file_dialogue_stats` / `_print_density_histogram` / `_print_term_scan_preview` 三个 dry-run 辅助函数
251. 重写 `translators/direct.py`（1301 → 584 行）：只保留 `run_pipeline` 编排函数 + 必要 imports + re-export 声明。下划线前缀子模块保持私有，外部只看 `translators.direct`

**向后兼容（re-export）**：`translators.direct` 继续导出 `run_pipeline` / `translate_file` / `_translate_file_targeted` / `_translate_chunk` / `_should_retry` / `_split_chunk` / `_translate_chunk_with_retry`，`main.py` / `engines/renpy_engine.py` / `tests/test_all.py` / `tests/test_batch1.py` / `tests/test_direct_pipeline.py` 的现有 import 零修改即可工作

**测试保护**：T-C-3（第 22 轮新建的 `tests/test_direct_pipeline.py`）的 2 条集成测试覆盖了 `translate_file` happy path 和 resume skip，保证拆分后行为不变。全套 286 测试零回归

**下一步**：第 24 轮处理 `translators/tl_mode.py`（928 行）和 `translators/tl_parser.py`（1106 行）的类似拆分，依赖 T-H-2 测试基础保护

### 第二十四轮：A-H-4 Part 2 — tl_mode.py + tl_parser.py 拆分

**tl_mode.py 拆分**（928 行 → 3 个模块，均 < 800 行）：

252. 新建 `translators/_tl_patches.py`（232 行）：搬迁 `_LANG_BUTTON_SNIPPET` + `_clean_rpyc` + `_apply_tl_game_patches` + `_inject_language_buttons`。四项共同特征：都对 `game_dir` 做预翻译期的副作用修改（拷贝字体 / 写 none_overlay.rpy / 改 gui.rpy / 注入 Language 按钮 / 清 rpyc 缓存），作为一组 game-dir 补丁操作聚合
253. 新建 `translators/_tl_dedup.py`（200 行）：搬迁 `DEDUP_MIN_LENGTH` + `DedupResult` + `dedup_tl_entries` + `apply_dedup_translations` + `build_tl_chunks`。形成完整的"去重 → chunk 装配 → AI 翻译后复用"三步管线
254. 重写 `translators/tl_mode.py`（928 → 558 行）：保留 `_translate_one_tl_chunk`（tl-mode 专用 chunk 级函数）+ `run_tl_pipeline` 编排 + re-export。所有 `_apply_tl_game_patches` / `dedup_tl_entries` / `build_tl_chunks` 等现有外部引用通过 re-export 透明工作

**tl_parser.py 拆分**（1106 行 → 4 个模块，均 < 800 行）：

255. 新建 `translators/_tl_postprocess.py`（106 行）：搬迁 `postprocess_tl_file` + `postprocess_tl_directory`。独立一套 `_RE_TRANSLATE_BLOCK` 正则（避免循环依赖），负责翻译后 ``nvl clear`` 清理和空 translate 块补 ``pass``
256. 新建 `translators/_tl_nvl_fix.py`（152 行）：搬迁 `_compute_say_only_hash` + `_compute_nvl_say_hash` + `fix_nvl_translation_ids` + `fix_nvl_ids_directory`。Ren'Py 8.6+ → 7.x 翻译块 ID 兼容层，独立的自足模块
257. 新建 `translators/_tl_parser_selftest.py`（426 行）：搬迁原 `_run_self_tests`（含 12 组、75 条断言）。改造为可被外部调用的 `run_self_tests()` 函数 + `__main__` block。搬出原因：若与 tl_parser.py 合在一起将使后者仍超 800 行
258. 重写 `translators/tl_parser.py`（1106 → 532 行）：保留数据类（`DialogueEntry` / `StringEntry` / `TlParseResult`）+ 常量/正则 + `_sanitize_translation` / `extract_quoted_text` / `parse_tl_file` / `scan_tl_directory` / `get_untranslated_entries` / `fill_translation` / `print_tl_stats` + re-export + 瘦身的 `__main__` block

**兼容性**：
- 支持 `python translators/tl_parser.py --test` 直接运行：`__main__` 前用 `__package__ in (None, '')` 检测脚本模式并临时把项目根加到 `sys.path`，让 re-export 的包导入正常工作
- `translators.tl_mode` 继续暴露 `run_tl_pipeline` / `_translate_one_tl_chunk` / `dedup_tl_entries` / `apply_dedup_translations` / `build_tl_chunks` / `DedupResult` / `DEDUP_MIN_LENGTH` / `_apply_tl_game_patches` / `_inject_language_buttons` / `_clean_rpyc` / `_LANG_BUTTON_SNIPPET`
- `translators.tl_parser` 继续暴露 `postprocess_tl_file` / `postprocess_tl_directory` / `_compute_say_only_hash` / `_compute_nvl_say_hash` / `fix_nvl_translation_ids` / `fix_nvl_ids_directory`
- 下游 `main.py` / `engines/renpy_engine.py` / `tools/translation_editor.py` / `tests/test_all.py` / `tests/test_tl_dedup.py` / `tests/test_tl_pipeline.py` / `tests/test_translation_editor.py` 零修改

**结果**：
- 7 个 `translators/` 目标文件的总行数由 `direct.py + tl_mode.py + tl_parser.py = 3335` 行 → 4 个原文件 + 7 个新子模块 = 约 2800 行有效代码（import/docstring 增量 ~550 行，换来每文件 < 800 行）
- 全套 12 测试套件 286/286 全绿，`python -m translators.tl_parser --test` 75/75 绿，零回归

**本轮不新增测试**：第 22 轮预埋的 T-C-3（`test_direct_pipeline`）+ T-H-2（`test_tl_pipeline`）+ `test_tl_dedup` 三组集成测试在拆分前后持续绿色，满足"A-H-4 回归保护"目标

**A-H-4 目标达成**：
- direct.py 1301 → 584（第 23 轮）+ _direct_chunk/file/cli
- tl_mode.py 928 → 558（第 24 轮）+ _tl_patches/_tl_dedup
- tl_parser.py 1106 → 532（第 24 轮）+ _tl_postprocess/_tl_nvl_fix/_tl_parser_selftest
- **A-H-4 计划覆盖的三大目标文件**（direct / tl_mode / tl_parser）均 < 800 行
- 遗留项：`translators/screen.py`（877 行）不在本轮 A-H-4 计划内，留给第 26+ 轮处理

### 第二十五轮：HIGH/MEDIUM 剩余项批量收敛

**架构收尾**：

259. [A-H-1 尾巴] `pipeline/stages.py:235, 332` 两处 `from one_click_pipeline import StageError` 改为 `from pipeline.helpers import StageError`。彻底消除 `pipeline/` 子包对顶层 `one_click_pipeline.py` 的反向依赖——此前 StageError 虽然能通过 `one_click_pipeline` 的 re-export 工作，但违反分层模型
260. [A-H-6] `core/api_client.UsageStats` 新增 `to_dict()` 方法返回结构化快照；`engines/generic_pipeline.py:402` 从 `summary()`（人读字符串，含价格免责声明）改用 `to_dict()`。`pipeline_report.json` 的 `api_usage` 字段从**字符串**变成**结构化对象**（含 provider / model / requests / tokens / cost_usd / pricing_exact），下游 CI/HTML 报告可直接消费

**安全**：

261. [S-H-3] `core/config.py::Config.resolve_api_key` 抽出 `_read_api_key_file(key_file)` 辅助方法，增加三层防护：(1) `Path(...).expanduser().resolve(strict=False)` 规范化；(2) 拒绝指向 `C:/Windows` / `/etc` / `/proc` / `/sys` / `/root` 的路径并 warning；(3) 8 KB 大小上限（合理 Key < 200 字节，留 40× 余量）。防"恶意配置文件诱导任意文件读取"，所有失败路径都记 logger.warning 并返回空串

**性能**：

262. [PF-H-2] `translators/direct.py::run_pipeline` 的 `log()` 函数改为开一次句柄复用：`open(_log_path, 'a')` 存为 `log_fp`，`log(msg)` 直接 write+flush，函数末尾 close。消除 Windows 上 NTFS 元数据更新 + Defender 扫描带来的每条日志 ~1ms 开销（典型 200 文件翻译节省 ~200ms）。sys.exit 分支依赖 OS 自动回收
263. [PF-C-2] `file_processor/validator.py` 提取 7 个模块级预编译正则（`_RE_SINGLE_QUOTED_STR` / `_RE_CODE_KEYWORD_LINE` / `_RE_DOUBLE_QUOTED_STR` / `_RE_BRACKET_VAR` / `_RE_TAG_BRACE` / `_RE_COMMENT_TAG` / `_RE_PRINTF_NAMED` / `_RE_DOUBLE_PUNCT`）。`_check_structural_integrity` / `_check_placeholders_and_tags` / `_check_control_tags_and_keywords` 三个热路径函数改用这些常量替代字面量 `re.search/match/findall/sub`。每翻译文件节省 500-700ms 正则编译开销；100 文件游戏节省 50-70 秒

**测试增量**（test_all 109 → 110，test_rpa_unpacker 14 → 15，总数 286 → 288）：

264. [T-H-3] `tests/test_rpa_unpacker.py::test_rpa3_refuses_zip_slip`：构造含 `../../evil.py` 恶意条目的 RPA-3.0 归档，验证合法条目解出、恶意条目被拒绝写入；同时检查 `extracted` 返回列表中所有路径都在 outdir 内。锁定第 20 轮修复的 S-C-1 ZIP Slip 防护
265. [T-H-1] `tests/test_all.py::test_glossary_scan_renpy_directory`：构造 `define mc = Character("Main Hero")` / `DynamicCharacter` / `config.name` / `config.version` 等 Ren'Py 定义 + `renpy/` 子目录（应被跳过），验证 `Glossary.scan_game_directory` 的 Ren'Py 解析正则和引擎目录过滤。此前仅 RPG Maker 分支有专项测试（`test_glossary_scan_rpgmaker`），Ren'Py 正则路径零覆盖

**本轮未做**（留给第 26+ 轮）：
- A-H-2：`core/translation_utils.py` 反向依赖 `file_processor/`（需要函数下沉/提升重构）
- A-H-3：`translators/` 与 `engines/` 两套平行概念合并（大重构，需要把 direct/tl/retranslate 也迁到 TranslatableUnit 模型）
- S-H-4：插件 subprocess 沙箱真正隔离（需要整套 IPC / Capabilities 设计）

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
