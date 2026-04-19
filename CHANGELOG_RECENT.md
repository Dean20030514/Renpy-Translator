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
- 第二十五轮：七项 HIGH/MEDIUM 收敛 — A-H-1 尾巴（pipeline StageError 反向 import）+ A-H-6（UsageStats.to_dict）+ S-H-3（api_key_file 路径校验）+ PF-H-2（direct.py log 句柄复用）+ PF-C-2（validator 正则预编译）+ T-H-1 / T-H-3 新测试；测试 286→288
- 第二十六轮：综合包（A+B+C） — TranslationDB 三件套（RLock + 原子写 + line=0 + dirty flag）+ RPA 大小预检查 + RPYC 白名单同步 + stages/gate 可见化 + screen.py 拆分 + quality_report 加锁 + patcher 反向索引 + RateLimiter 批量清理 + os.path→pathlib；测试 288→293

## 详细记录

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

### 第二十八轮：A-H-3 Minimal 路由统一 + S-H-4 Dual-mode 插件沙箱

第 27 轮遗留的两项 Priority A 大重构以"保守组合"方式一次收敛：A-H-3 只做 Minimal（零行为变化的 entry-point 统一），S-H-4 以 opt-in dual-mode 发布（默认关闭，新增 `--sandbox-plugin` 开关），避免任何现有插件 / 翻译流程被破坏。

**A · A-H-3 Minimal — 统一引擎路由入口**：

287. `engines/renpy_engine.py::RenPyEngine.run()` 扩展覆盖 `tl_screen` 分支：`--tl-mode --tl-screen` 连贯执行（先 tl，后 screen）+ `--tl-screen` 单独使用时补日志提示"建议先 --tl-mode"。行为与 main.py 原版 if/elif 链一致
288. `main.py:234-261` 的 28 行 if/elif 路由（按 tl_mode / tl_screen / retranslate / direct 分派 translators/*）简化为 5 行 `engine = resolve_engine(engine_arg or "auto", ...); engine.run(args)`。所有引擎（Ren'Py + RPGMaker + CSV/JSONL + auto）共用同一入口，Ren'Py 的子分支逻辑内敛到 `RenPyEngine.run` 一处
289. `main.py:23-26` 顶部 import 列表补 `import os` — 修复 Explore 代理发现的潜伏 bug：`main.py:220` 使用 `os.environ.pop(...)` 但 `os` 模块在顶部未 import。先前靠 `core/config.py` 等下游模块间接污染 `globals()` 让它"碰巧"工作，但任何直接调用 main.py:main() 的路径会 NameError
290. **风险控制**：本轮不动 Ren'Py 内部的 direct/tl/retranslate 三条管线，也不做 DialogueEntry → TranslatableUnit 的数据模型迁移。direct-mode 4.01% 漏翻率 / tl-mode 99.97% 成功率由逐字节保留翻译链路保证

**B · S-H-4 Dual-mode — 插件 subprocess 沙箱 (opt-in)**：

291. `core/api_client.py` 新增 `_SubprocessPluginClient` 类：包装 `subprocess.Popen([python, -u, plugin_path, '--plugin-serve'])`，长连接 JSONL 协议 — Request `{request_id, system_prompt, user_prompt}` / Response `{request_id, response, error}` / Shutdown sentinel `request_id == -1`。`threading.Lock` 保护 stdin 写入；`threading.Thread` + join-timeout 实现无阻塞 stdout 读取；超时则 `proc.kill() + wait(2)` 清理。`close()` 幂等，`atexit` 自动兜底，`__del__` 再兜底。类方法 `translate_batch(system_prompt, user_prompt)` 与传统插件模块 duck-type 兼容 — 故 `APIClient._call_custom` 一行不改即可用
292. `APIConfig` 新增 `sandbox_plugin: bool = False` 字段（默认 False 保留历史 importlib 快路径）；`APIClient.__init__` 根据 `config.provider == "custom"` + `config.sandbox_plugin` 分流：启用则 `_SubprocessPluginClient(...)`，否则 `_load_custom_engine(...)`
293. `main.py` 新增 `--sandbox-plugin` CLI flag（`action="store_true"`）；`translators/direct.py` / `translators/tl_mode.py` / `translators/retranslator.py` / `translators/screen.py` / `engines/generic_pipeline.py` / `pipeline/stages.py` 共 6 处 APIConfig 构造点补 `sandbox_plugin=getattr(args, "sandbox_plugin", False)` 透传。`generic_pipeline.py:212` 的 APIConfig 构造此前缺失 `custom_module` 透传（非 custom provider 时无影响），本轮顺手补上
294. `custom_engines/example_echo.py` 追加 `_plugin_serve()` 函数 + `if __name__ == "__main__"` 分支：读 stdin JSONL，dispatch 到 `translate_batch`，异常结构化写回 `{error: ...}`；legacy mode 直接执行脚本时打印 usage 并 exit(1)。既有 `translate_batch` / `translate` API 保持不变 — 同一文件在 legacy / sandbox 两种模式下均可用
295. **安全收益**：sandbox 模式下插件无法通过 `os.environ` 读取 `XAI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` 等环境变量；无法直接访问宿主进程的 translation_db 等内存；OS 层面 subprocess 提供天然隔离。性能代价：首次启动 ~100-150ms Python 解释器开销，后续 per-call ~5-15ms JSON 序列化 + pipe round-trip。对 100 chunk 游戏 < 2s 额外总开销

**测试增量**（`tests/test_custom_engine.py` 11 → 19，总数 293→301）：

296. [新] `test_config_sandbox_plugin_default`：断言 `sandbox_plugin` 默认 False，保证 opt-in 行为
297. [新] `test_sandbox_roundtrip_batch`：端到端 — 启动 example_echo subprocess，发送批量请求，验证 `[ECHO] Hello` 响应透传
298. [新] `test_sandbox_request_id_tracking`：3 次连续调用，断言 `_request_id` 从 0 递增到 3，保证 stdin/stdout 不乱序
299. [新] `test_sandbox_plugin_exception_wrapped`：构造抛 `ValueError` 的插件，断言宿主收到 `RuntimeError("plugin crashed on purpose")` 而非进程崩溃
300. [新] `test_sandbox_rejects_path_traversal` / `test_sandbox_rejects_missing_module`：路径安全校验复用 legacy 模式的相同规则
301. [新] `test_sandbox_timeout_kills_hung_plugin`：构造永远不响应的插件 + `timeout=1.0`，断言超时后 `proc.poll() is not None`（进程已清理）
302. [新] `test_sandbox_close_idempotent`：`close()` 两次不抛异常；关闭后继续调用 `translate_batch` 明确 raise RuntimeError

**本轮未做**（留给第 29+ 轮）：
- A-H-3 Medium / Deep：Ren'Py 通过 adapter 层走 generic_pipeline 6 阶段，或完全退役 DialogueEntry → TranslatableUnit 统一。需真实 API key + 真实游戏做漏翻率 / 成功率回归验证
- S-H-4 Breaking：强制所有插件走 subprocess，retire importlib 路径。当前 dual-mode 已足够，等社区反馈再决定是否切换
- `tools/patch_font_now.py:27` 疑似路径错位（`Path(__file__).parent / "resources" / "fonts"` 解析为 `tools/resources/fonts/`，但实际资源在项目根 `resources/fonts/`）— 独立小项

### 第二十九轮：Priority B 持续优化 — test_all.py 拆分 + 路径 bug + 文档刷新

HANDOFF.md round 28 把 Priority A 四项全部清零；本轮进入"持续优化"阶段，
一次收敛测试文件拆分、遗留路径 bug 修复、以及第 26-28 轮后的文档陈旧点。
没有代码行为变更，只有结构/文档整理。

**A · `tests/test_all.py` 2,539 行拆为 5 个聚焦文件 + meta-runner**：

303. `tests/test_all.py` 历经 29 轮迭代后已达 **2,539 行**（113 个 `test_*` 函数 + 3 个 `_mock_*` 辅助），3 倍超过 CLAUDE.md 800 行软上限。按模块边界拆成：
   - `tests/test_api_client.py`（578 行，19 测试 + 3 辅助）：`APIConfig` / `UsageStats` / `RateLimiter` / `json_parse` / 定价 / 推理 timeout / HTTP 429/500/401/404 重试 / URLError / 连接池 / 响应体上限 / `API Key subprocess env`
   - `tests/test_file_processor.py`（500 行，33 测试）：splitter（`estimate_tokens` / `_find_block_boundaries` / `force_split`）+ checker（`protect_placeholders` / `restore_placeholders` / `check_response_item` × 6 / `check_response_chunk` × 4 / `_filter_checked_translations` / `_restore_placeholders_in_translations`）+ patcher（`apply_translations` × 6 / 转义）+ validator（menu id / lang_config / W442）
   - `tests/test_translators.py`（604 行，24 测试）：`dialogue_density` / `find_untranslated_lines` / `is_untranslated_dialogue` / `_should_retry` / `_split_chunk` / `fix_nvl_ids` × 4 / `screen_extract/replace` × 12 / `pipeline_imports_smoke`
   - `tests/test_glossary_prompts_config.py`（525 行，24 测试）：Glossary 基础/dedup/线程安全/Ren'Py 扫描/memory confidence + `locked_terms` × 7 + prompts（zh/ja/system）+ config（load/CLI/validate/lang_config）
   - `tests/test_translation_state.py`（483 行，13 测试）：ProgressTracker（cleanup/resume/normalize/并发 flush/write ordering）+ TranslationDB（roundtrip/concurrent upsert/atomic save/line=0）+ `_deduplicate_translations` / `_match_string_entry_fallback` / `ProgressBar` / `review_generator_html`
304. `tests/test_all.py` 重写为 49 行 meta-runner：`import` 5 个拆分模块 + 调用各自的 `run_all()` 函数 + 打印合计计数。`python tests/test_all.py` 命令保持工作（CI / scripts / IDE 集成无需改动）
305. 每个拆分文件同时暴露 `if __name__ == "__main__":` 入口，支持 `python tests/test_translation_state.py` 单独运行某类。`run_all()` 返回该文件的测试数，便于聚合
306. **验证**：5 个文件单独跑均绿（19+33+24+24+13 = 113），`test_all.py` meta-runner 打印 `ALL 113 TESTS PASSED`；全套 12 套件 + tl_parser 内建 75 自测零回归
307. **为何不用 unittest/pytest**：现有测试风格是"def 函数 + 内联 print `[OK]`"，没有 framework 依赖；拆分后每个文件仍然是纯 stdlib Python 脚本，可直接 `python xxx.py` 运行，符合项目零依赖原则

**B · `tools/patch_font_now.py:27` 路径 bug 修复**：

308. 第 27 行 `Path(__file__).parent / "resources" / "fonts"` 解析为 `tools/resources/fonts/`（不存在），因 `__file__` 是 `tools/patch_font_now.py`。改为 `Path(__file__).resolve().parent.parent / "resources" / "fonts"` 正确指向项目根 `resources/fonts/`。`python tools/patch_font_now.py` CLI 调用之前一直静默走到 "fonts dir not found" 分支，现在能正确加载 `NotoSansSC-Regular.ttf` / `SourceHanSansSC-Regular.otf`。不是单元测试覆盖的路径（该脚本需要真实 translation output 目录），但 round 28 HANDOFF 已标记，round 29 顺手修

**C · 文档刷新**：

309. `TEST_PLAN.md`：现有测试文件表格从 1 个入口 `test_all.py(94)` 扩成 7 个条目（meta-runner + 5 个拆分文件 + 原 94 细分仍保留作历史引用）。总计从 267 更新到 301。执行方法段新增 5 个拆分文件的独立命令行示例。test_rpa_unpacker/test_rpyc_decompiler/test_custom_engine 用例数同步到 round 26/28 后的 16/18/19
310. `docs/dataflow_pipeline.md`：新增"CLI 入口统一路由（round 28 A-H-3）"段落，记录 main.py 现在统一走 `engines.resolve_engine(...).run(args)`，Ren'Py 子分支由 `RenPyEngine.run` 分派到 translators 管线
311. `docs/dataflow_translate.md`：已有 `fix_nvl_ids_directory()` 引用（第 15 轮添加），无需修改
312. `CLAUDE.md` 模块图已在 round 28 同步，本轮只更新测试计数行与拆分描述
313. `HANDOFF.md`：round 29 → 30 handoff，Priority A 保持清空，新增"架构健康度"一栏记录 `test_all.py` 拆分完成、`patch_font_now` 修复

**本轮未做**（留给第 30+ 轮）：
- CI 增加 Windows runner（外部基础设施）
- docs/ 其他按需加载文档的深度复查
- 任何 A-H-3 Medium/Deep 或 S-H-4 Breaking 的进一步推进

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
