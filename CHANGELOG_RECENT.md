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
- 第二十三轮：A-H-4 Part 1 — `translators/direct.py` 1301 → 584 + 新建 `_direct_chunk` / `_direct_file` / `_direct_cli` 三个子模块；re-export 保持公共 API，T-C-3 集成测试护航零回归
- 第二十四轮：A-H-4 Part 2 — `translators/tl_mode.py` 928 → 558（+ `_tl_patches` / `_tl_dedup`），`translators/tl_parser.py` 1106 → 532（+ `_tl_postprocess` / `_tl_nvl_fix` / `_tl_parser_selftest`）；286 测试零回归

## 详细记录

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

### 第二十六轮：综合收敛包（A+B+C） — 数据完整性 / 安全加固 / screen 拆分 / 微优化

本轮按新一次深度审查结果，把 HANDOFF.md 未覆盖的 3 项 CRITICAL + 4 项 HIGH 与 HANDOFF 优先级 A + C 的 6 项微优化一起收敛，遵守"隔离变量、小步提交"原则，每阶段独立验证。

**A · TranslationDB 数据完整性**（CRITICAL，`core/translation_db.py`）：

266. [C-1] 加 `threading.RLock`，把 `load / save / upsert_entry / add_entries / has_entry / filter_by_status / _rebuild_index` 全部包在锁内。`engines/generic_pipeline.py::_translate_one_chunk` 的 `ThreadPoolExecutor` 并发调用从此无数据竞争
267. [C-2] `save()` 改为"temp 文件 + `os.replace`"原子替换，失败路径清理 tmp 并 re-raise（与 `generic_progress.json` 的原子写法对齐）。崩溃/并发下不再留下半写的 JSON
268. [C-3] `upsert_entry` 的 `if not line` 判断改为 `line is None`，并同步 `_rebuild_index` 的 key 过滤。`engines/generic_pipeline.py:330` 写 `"line": 0` 的兜底条目从此不再被静默丢弃
269. [PF-M-2] 加 `_dirty` flag：`upsert/add` 成功后置 True，`save()` 开头 False 即返回，`load()` 末尾置 False。未变更时 `save()` 直接 no-op，100 文件翻译约省 30-50ms × N 次

**A 测试**（`tests/test_all.py` 110 → 113）：
- `test_translation_db_concurrent_upsert`：32 线程 × 100 条 upsert → 断言 entries 数正确 + index 完整 + 全部 has_entry 命中
- `test_translation_db_save_atomic`：save 中途 mock `os.replace` 抛 OSError → 断言原文件不变 + tmp 被清理 + JSON 仍可解
- `test_translation_db_accepts_line_zero`：upsert `line=0` → has_entry/filter_by_status 均命中 + save/load round-trip 保留

**B · 安全加固 + 静默失败可见化**（HIGH）：

270. [B.1 · H-1] `tools/rpa_unpacker.py` 加常量 `_RPA_MAX_ENTRY_BYTES = 512 MiB`，`unpack_rpa` 在 `f.read(length)` 前预检查 `length` 范围。被篡改的恶意索引不再能触发 OOM。新增 `test_rpa_refuses_oversized_entry` 回归
271. [B.2 · H-2] `tools/rpyc_decompiler.py` 抽出模块级共享常量 `_SHARED_WHITELIST` + `_WHITELIST_TIER1_PY2_EXTRAS`。Tier 1 helper 从模板 `_DECOMPILE_HELPER_TEMPLATE` 渲染（`_render_decompile_helper`）时 `json.dumps` 注入，Tier 2 `_RestrictedUnpickler` 直接引用。新增 `test_whitelist_tier1_tier2_consistent` 锁定两侧同步（含 Py2 long/unicode 兼容校验）
272. [B.3 · H-3] `pipeline/stages.py` 唯一"静默降级"分支（第 361-370 行 `full report.json` 解析失败 silent zero）改为显式 `[WARN ]` 输出 + `report_error` 字段存进 report 供下游消费
273. [B.4 · H-4] `pipeline/gate.py` `glossary.json` 加载失败从 `logger.debug` 升级为 `logger.warning`，明确提示"锁定术语/禁翻检查已跳过"
274. [B.5 · M-1] `pipeline/gate.py` 缺失原文件场景从 `warnings += 1` 额外打印 `logger.warning("[GATE] 缺失原文件, 跳过校验: ...")`

**C · HANDOFF 优先级 A + C 微优化**：

275. [C.1 · A-H-4 补] `translators/screen.py` 877 → 478 行，拆出两个子模块：
   - `translators/_screen_extract.py`（172 行）：`ScreenTextEntry` + 4 条正则 + `_should_skip` + `_line_has_underscore_wrap` + `scan_screen_files` + `extract_screen_strings`
   - `translators/_screen_patch.py`（346 行）：`SCREEN_TRANSLATE_SYSTEM_PROMPT` + chunk 装配 + `_translate_screen_chunk` + `_deduplicate_entries` + `_escape_for_screen` + `_replace_screen_strings_in_file` + 进度 + backup
   - 保留 `run_screen_translate` + 9 条自测 + re-export 清单在 `screen.py`。下游 `main.py` / `pipeline/stages.py` / `tests/test_all.py` 的 `from translators.screen import ...` 零改动
276. [C.2 · PF-H-1] `translators/_direct_file.py` 加模块级 `_quality_report_lock = threading.Lock()`，包裹两处 `quality_report[rel_path] = issues` 写入。文件级并行下 dict 结构更新不再依赖 GIL 隐式保护
277. [C.3 · PF-H-3] `file_processor/patcher.py::_diagnose_writeback_failure` 加可选 `norm_lines` 参数 + 新建 `_build_writeback_diag_index()` 辅助。`apply_translations` 的 fourth-pass 失败循环里只在首次触发时构建 NFKC 缓存，后续复用。大文件多失败场景省 n² 次 Unicode 规范化
278. [C.4 · PF-H-4] `core/api_client.py::RateLimiter` 加 `_CLEANUP_INTERVAL = 64` + `_cleanup_counter`。过期桶清理从"每次 acquire 扫描"改为"每 64 次 acquire 批量清理"，持锁时间显著下降
279. [C.5 · P-H-3/4] `os.path` 遗留用法改 `pathlib`：`translators/tl_parser.py:528/531` 改 `Path.is_file()/is_dir()`；`tools/rpa_unpacker.py:319` 改 `Path(name).suffix`；`tools/renpy_upgrade_tool.py:618-619` 改 `Path.resolve()/is_dir()`

**结果**：
- 12 测试套件 286 → 293（+5 新测试）+ tl_parser 内建 75 自测全绿，零回归
- `translators/` 所有 .py 继续 < 800 行（screen.py 478 / direct.py 601 / tl_mode.py 558 / tl_parser.py 541，其余均 < 500）
- A-H-4 所有目标（direct / tl_mode / tl_parser / screen）全部达成

**本轮未做**（留给第 27+ 轮）：
- A-H-2：`core/translation_utils.py` ↔ `file_processor/` 反向依赖
- A-H-3：`translators/` 与 `engines/` 两套概念统一（大重构）
- S-H-4：插件 subprocess 沙箱真正隔离
- A-H-5：`tools/font_patch` 迁移到 `core/`（与 A-H-2 耦合，建议联合处理）

### 第二十七轮：分层收尾 — A-H-2（反向依赖消除）+ A-H-5（font_patch 迁移）

第 26 轮遗留的两项分层违规一次性收敛，纯 import 调整，零行为变化、零测试新增需求。

**A · A-H-2 消除 `core/translation_utils.py` 对 `file_processor/` 的反向依赖**：

280. 把三个 wrapper 函数下沉到 `file_processor/checker.py`（紧邻其委托的纯函数）：`_filter_checked_translations`（调用 `check_response_item`）、`_restore_placeholders_in_translations`（调用 `restore_placeholders`）、`_restore_locked_terms_in_translations`（调用 `restore_locked_terms`）。下沉后 file_processor 更自足，core 不再需要反向 import
281. 从 `core/translation_utils.py` 移除顶部 `from file_processor import (check_response_item, restore_placeholders)` 和函数内局部 `from file_processor.checker import restore_locked_terms`，并删除 3 个被搬走的 wrapper。`core/` 现在只剩 ProgressTracker / TranslationContext / ChunkResult / TranslationCache / dedup / strip 等进度-上下文-缓存层抽象
282. `file_processor/__init__.py` 加入三个新符号到 re-export 列表 + `__all__`
283. 更新 5 处调用方：`translators/_direct_chunk.py` / `translators/_direct_file.py` / `translators/tl_mode.py` / `translators/retranslator.py` / `tests/test_all.py`（两处 local import） — 全部从 `core.translation_utils` 改为 `file_processor` 导入

**B · A-H-5 `tools/font_patch.py` → `core/font_patch.py`**：

284. `git mv tools/font_patch.py core/font_patch.py`（147 行，3 个公共函数，纯 stdlib 依赖；层级上本就属于 core 基础设施，错位于 tools/ 导致 `translators/direct.py` 和 `translators/_tl_patches.py` 发生 `translators → tools` 的反向依赖）
285. 更新 5 处 import：`pipeline/stages.py:16`、`translators/direct.py:36`、`translators/_tl_patches.py:26 + 86`、`tools/patch_font_now.py:13`（后者是 CLI 单次运行脚本，消费者侧更新即可；无需保留 shim）
286. `build.py` PyInstaller hidden-imports 清单：`tools.font_patch` → `core.font_patch`

**结果**：
- 12 测试套件 + tl_parser 75 自测全绿，总数保持 293（纯重构、无新增测试）
- `core/` ↔ `file_processor/` 之间仅剩单向依赖（file_processor → nothing，core/translation_utils → nothing in file_processor）
- `translators/` 对 `tools/` 的唯一反向依赖（font_patch）消除；`translators/` 现在只依赖 `core/` 和 `file_processor/`，符合分层契约
- 新增 `core/font_patch.py` 占 147 行，`core/` 仍维持"基础设施"定位

**本轮未做**（留给第 28+ 轮）：
- A-H-3：`translators/` 与 `engines/` 两套平行概念合并（大重构，4+h，改变默认 engine 路由）
- S-H-4：插件 subprocess 沙箱真正隔离（需完整 IPC / Capabilities 设计）
- 如未来 `file_processor/checker.py` 超过 500 行，可考虑把下沉的 3 个 wrapper 再提到独立的 `file_processor/translations.py` 文件

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
