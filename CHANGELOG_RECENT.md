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
- 第二十七轮：分层收尾 — A-H-2（3 wrapper 下沉 `file_processor/checker.py`）+ A-H-5（`tools/font_patch.py` → `core/font_patch.py`）；测试 293 保持
- 第二十八轮：A-H-3 Minimal 路由统一 + S-H-4 Dual-mode 插件沙箱（`--sandbox-plugin` opt-in）+ `main.py` 潜伏 `os` bug 修复；测试 293→301

## 详细记录

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

### 第三十轮：冷启动质量审计后的 4 项加固 + 文档深度刷新

HANDOFF.md round 29 把 Priority A + B 都清零后，第 30 轮先做一次冷启动的
全面质量扫描（两个独立 Explore 代理交叉检查），然后按发现执行。扫描结果
"no material findings" — 没有新的高危 bug 可修；只剩若干 robustness 小项
和 docs 陈旧面。本轮一次收敛这 4 项小加固 + 2 项文档刷新。

**A · Robustness fixes（低风险防御性改动）**：

314. `core/api_client.py::_SubprocessPluginClient._call` 第 289 行 `stderr.read()` 改为 `stderr.read(10_000)`。pathological 插件在异常退出时可能把几 MB 错误日志写到 stderr；之前的无界 read 理论上可 OOM 宿主进程。新增 10 KB 硬上限 + 保留原 600 字符 tail slice 不变。新增回归测试 `test_sandbox_stderr_read_bounded`：插件写 3 KB 到 stderr 后 `sys.exit(7)`，断言宿主报出 `exit=7` 错误 + 消息长度 < 2000 字符。测试数 301→302
315. `core/api_client.py::_SubprocessPluginClient.__init__` 加 try/except 兜底：之前如果 `subprocess.Popen(...)` 成功但 `atexit.register` 之前（之间）抛异常（极端场景），会留下孤儿子进程。新版在 except `BaseException` 分支里 `proc.kill() + wait(2)` 清理，然后 re-raise。正常路径零性能影响
316. `core/http_pool.py::_get_or_create` + `_drop_connection` 的连接清理分支把 `except Exception` 收窄为 `except (OSError, http.client.HTTPException)`。原来过宽的 catch 会把 `AttributeError` / `TypeError` 之类的编程错误（例如重构后连接对象类型变了）悄悄吞掉，现在会让这类 bug 直接向上 bubble
317. `translators/retranslator.py` 清理死代码 `quality_report` 参数（位于 `retranslate_file` 签名 + 内部赋值 + `run_retranslate_pipeline` 调用 + `pipeline/stages.py::_run_retranslate_phase` 对应字典构造）。该参数被填充但从未被保存/返回，属于 round 23 前 direct.py 拆分时遗留的 dead plumbing。`translators/direct.py::run_pipeline` 的同名 `quality_report` 是真在用（保存为 `quality_report.json`），未受影响

**B · 文档深度刷新**：

318. `README.md` 特性一览追加 4 个 round 26-29 能力：`--sandbox-plugin` opt-in 插件沙箱、统一引擎入口 `engines.resolve_engine(...).run(args)`、`TranslationDB` 并发安全（RLock + 原子写）。保留原有所有描述，只增补不删除
319. `docs/engine_guide.md` 新增"自定义引擎插件（`--provider custom --custom-module NAME`）"整节：接口契约、两种运行模式对照表（legacy vs sandbox）、sandbox 模式 `_plugin_serve` 插件模板 + 完整 JSONL 协议细节、超时/stderr 截断/shutdown sentinel 行为、`custom_engines/example_echo.py` 参考指引。此前 engine_guide 只讲 EngineBase 抽象，完全没提 custom provider 轴
320. CHANGELOG / CLAUDE.md / .cursorrules / HANDOFF.md 按惯例同步

**结果**：
- 12 测试套件 + tl_parser 75 + screen 51 内建自测全绿；测试数 301 → 302（+1 stderr 边界）
- 零源代码文件超过 800 行；`translators/retranslator.py` 轻微瘦身（-7 行死代码）
- HANDOFF Priority A + B 保持清空；本轮新增 1 项监控类改进（stderr 边界防御），2 项文档深度刷新
- 冷启动 Explore 确认"no material findings"—项目已到达"多年可维护"的稳定点

**本轮未做**（留给第 31+ 轮）：
- CI Windows runner（仍是外部基础设施项）
- docs/constants.md / docs/quality_chain.md / docs/roadmap.md 深度复查（本轮只做 engine_guide；其他基本仍然准确）
- A-H-3 Medium / S-H-4 Breaking（需真实游戏 + 社区反馈，非 AI 独立可推进）
- Glossary 线程安全文档化（当前架构单线程，不是 bug，但可在 CLAUDE.md 原则里加一行明确）

### 第三十一轮：从竞品 renpy_hook_template_py3.rpy 提炼 3 项技巧 + 新增运行时注入模式

参照闭源竞品"【微信公众号：刺客边风】游戏汉化翻译_1.5.2"的 737 行 Ren'Py
运行时 hook 模板，把可移植的技巧选择性整合到本项目，并作为全新的 opt-in
路径新增"运行时注入模式"，让 tl-mode / direct-mode 静态改写之外多一条
"改游戏运行时行为"的补充路线。分 3 个 Tier 实施。

**Tier A · 静态 checker / fallback 增强**（零风险，每项独立带测试）：

321. [A-1] `file_processor/checker.py` 新增 `COMMON_UI_BUTTONS` frozenset +
`is_common_ui_button(text)` 辅助函数。清单来自竞品第 460-472 行
`_youling_is_sensitive_ui_text`，覆盖 30+ 常见 UI 按钮（yes/no/ok/cancel/
save/load/preferences 等）。大小写 + 空白规范化后查表。**不**自动丢弃条目，
只提供 helper 供 screen translator 等上层决策使用，保持对现有 behavior 零
影响。新增 `test_is_common_ui_button`
322. [A-2] `file_processor/checker.py` 新增 `fix_chinese_placeholder_drift(text)`
+ `_fix_chinese_placeholder_drift_in_translations(translations)` 两个函数。
处理 AI 常见"好心翻译占位符变量名"的错误：`[姓名]` / `[名字]` / `[名称]`
→ `[name]`、`（姓名）` / `(姓名)` → `[name]`、`{{姓名}}` / `{{名字}}` /
`{{名称}}` → `{{name}}`。**关键集成点**：`_filter_checked_translations`
在 `check_response_item` 之前原地规范化 zh，让 drift 导致的占位符不匹配
不再触发"丢弃"—— 所有下游管线（direct / tl / retranslate / screen）无需
修改即可享受这项修复。新增 `test_fix_chinese_placeholder_drift` +
`test_filter_checked_translations_fixes_placeholder_drift`
323. [A-3] `core/translation_utils.py::_build_fallback_dicts` 从返回 3 dict
扩展为 4 dict，新增 `ft_tagstripped` 层。`_match_string_entry_fallback`
签名增加可选 `ft_tagstripped=None` 参数（向后兼容），新增 L5 层：`{color=
#f00}Hello{/color}` → `Hello` 后做 whitespace 规范化再查表。竞品 `_strip_tags`
（第 279-294 行）是裸状态机；本项目用正则 `_RENPY_TAG_RE = re.compile(r"
\{/?[a-zA-Z#!][^}]*\}")` 利用 Python 编译缓存更简洁。`translators/tl_mode.py`
两处 `_build_fallback_dicts` 调用点同步改为 4-tuple unpack；`test_translation_state.py::
test_match_string_entry_fallback` 扩展为 5 层测试 + 向后兼容 call-shape 断言

**Tier B · `resources/hooks/inject_hook.rpy` 模板**（270 行，纯 Ren'Py 脚本）：

324. 从竞品 737 行提炼到 270 行的清洁实现，与现有 `extract_hook.rpy` 形成
"extract → translate → inject" 闭环。关键设计：
   - `RENPY_TL_INJECT=1` 环境变量门控（对应竞品 `YOULING_ACTIVE`）：不设时零行为变化，
     文件可安全与游戏一起分发
   - 从 `game/translations.json` 读取 flat `{英文: 中文}` 映射，UTF-8 + 两级容错
   - 三个 hook 点：`config.say_menu_text_filter`（首选，官方 API）+
     `config.replace_text`（全局兜底）+ `Character.__call__`（最后补丁，try/except 包裹）
   - UI 按钮白名单与 `file_processor.COMMON_UI_BUTTONS` 逐字节一致
   - 占位符漂移修正与 `fix_chinese_placeholder_drift` 逐字节一致
   - Ren'Py 7.x（Python 2）↔ 8.x（Python 3）curry/partial proxy 兼容层
   - 字体替换只走 `config.font_replacement_map` 官方 API（不学竞品的 style
     monkey-patch），仅当 `game/fonts/tl_inject.ttf` 存在时生效
   - MIT 授权，注明灵感来源（renpy-translator + 竞品模板的公开可观察技术）

**Tier C · `--emit-runtime-hook` opt-in CLI 开关 + emitter 模块**：

325. 新增 `core/runtime_hook_emitter.py`（~170 行）：
   - `build_translations_map(entries) -> dict[str, str]`：从 `TranslationDB.entries`
     过滤 `status == "ok"` 条目，去重时保留首次翻译并记 debug 日志
   - `emit_runtime_hook(output_game_dir, entries, *, hook_template_path=None,
     hook_filename="zz_tl_inject_hook.rpy")`：原子写入 `translations.json`
     (temp + `os.replace` 与 TranslationDB 保持一致风格) + `shutil.copy2`
     复制 hook 模板。默认文件名用 `zz_` 前缀让 Ren'Py 在 `init python early:`
     中最后加载，避免打乱其他 early init 顺序
   - `emit_if_requested(args, output_dir, translation_db)`：供管线 tail
     调用，读 `args.emit_runtime_hook`，失败时 logger.warning 不抛出
326. `main.py` 新增 `--emit-runtime-hook` flag（`action="store_true"`，默认 False）
327. 4 个管线 tail 统一调用 `emit_if_requested`：`translators/direct.py`、
`translators/tl_mode.py`、`translators/retranslator.py`、`engines/generic_pipeline.py`
—— 都在 `translation_db.save()` 之后。零行为变化（flag 默认关）
328. 新增 `test_runtime_hook_emit_builds_map_and_copies_template`
（验证 status 过滤 + 去重 + JSON 排序 + hook 模板 bytes-identical 复制）+
`test_runtime_hook_emit_if_requested_respects_flag`（验证 flag on/off/missing
三种状态）

**测试增量**（总数 302 → 307，+5 新测试）：
- `tests/test_file_processor.py` 33 → 36：+3 (UI 白名单 / 占位符漂移 / filter 集成)
- `tests/test_translation_state.py` 13 → 15：+2 (runtime hook emit 两条)
- `tests/test_translation_state.py::test_match_string_entry_fallback` 扩展 L5 assertion + 向后兼容 call-shape（同一条测试更丰富，不计入数量）

**结果**：
- 14 测试套件全绿，测试 302 → 307
- `resources/hooks/` 新增 `inject_hook.rpy`（270 行），补齐 extract/inject 闭环
- `core/runtime_hook_emitter.py` 新模块，~170 行，零依赖纯 stdlib
- `--emit-runtime-hook` flag 为所有 4 条 Ren'Py 翻译路径开箱启用，`--sandbox-plugin`
  之外的第二个 opt-in 开关
- 现有用户零感知：所有新功能 default off，既有 tl-mode / direct-mode 行为
  逐字节不变

**本轮未做**（留给第 32+ 轮）：
- 将 `COMMON_UI_BUTTONS` 暴露为 glossary-style 配置（当前硬编码，真实游戏
  可能需要定制化）
- `inject_hook.rpy` 的字体替换目前只在 `game/fonts/tl_inject.ttf` 存在时
  生效，可以考虑通过 `--font-file` flag 自动拷贝
- `translations.json` 仍是 flat map，未来可能扩展为 `{original: {zh, zh-tw, ja}}`
  嵌套结构支持多语言切换
- CI Windows runner + docs/ 其余文档复查

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
