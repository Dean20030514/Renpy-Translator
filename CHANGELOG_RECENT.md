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
- 第二十九轮：Priority B 持续优化 — `tests/test_all.py` 2539 行拆为 5 个聚焦文件 + 49 行 meta-runner（113 tests/1 命令）+ `tools/patch_font_now.py:27` 路径 bug（`__file__.parent` 少一层）修复 + TEST_PLAN/dataflow_pipeline 文档刷新；测试 301 保持

## 详细记录

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

### 第三十二轮：round 31 续做全包 — UI 白名单可配置化 + 字体自动打包 + v2 多语言 schema（+ Commit 1 prep 字体路径 bug）

HANDOFF.md round 31 把三项"🟢 延续 round 31 小项"挂起；本轮按用户指定
一次全做。方案阶段 Plan agent 审查过程中意外发现 **CRITICAL** 级遗留
bug：`translators/direct.py:523` 和 `translators/_tl_patches.py:88` 的
`resources/fonts/` 路径 `__file__.parent` 少一层 parent（与 round 29
修的 `tools/patch_font_now.py` 同类型），源码运行时字体解析静默失败，
只有 PyInstaller 打包后才能工作。用户批准并入本轮作 Commit 1 prep，故
本轮共 5 commits，每个 bisect-safe（独立测试通过）。

**Commit 1 · Prep (refactor)：字体路径 helper + 2 处遗留 bug 修复**

329. `core/font_patch.py` 新增 `default_resources_fonts_dir() -> Path`：
canonical 抽取 `__file__.resolve().parent.parent / "resources" / "fonts"`
（从 `core/` 出发）。统一 4 个调用者：`pipeline/stages.py:517`（此前已
正确，迁移保一致）、`tools/patch_font_now.py:34`（round 29 修过，迁移）、
`translators/direct.py:523`（**bug 修复**）、`translators/_tl_patches.py:88`
（**同类 bug 修复**）。新增 `test_default_resources_fonts_dir_points_to_project_root`
守护：断言绝对路径 + 根目录结构 + 至少一个 `.ttf`

**Commit 2 · Subtask A：`--ui-button-whitelist` via sidecar JSON**

330. `file_processor/checker.py`：`COMMON_UI_BUTTONS` frozenset 保持不动
（现有 `isinstance(..., frozenset)` 测试依赖），新增 `_ui_button_extensions:
frozenset[str] = frozenset()` 模块级状态 + 4 个 public helper：
`add_ui_button_whitelist` / `load_ui_button_whitelist` /
`clear_ui_button_whitelist` / `get_ui_button_whitelist_extensions`。extensions
在每次 load/add/clear 时**重绑为新 frozenset**（不 mutate）→ Python GIL
下 attribute rebind 原子，worker 线程读取 `is_common_ui_button` 总能看到
一致 snapshot。契约：所有加载必须在 `engine.run(args)` 前完成
331. `load_ui_button_whitelist(paths)` 支持 `.txt`（UTF-8-sig、每行一 token、
`#` 注释 + 空行跳过）+ `.json`（顶层 list of str）。缺文件 / 解析失败 →
warning + 跳过，不阻断翻译运行
332. `main.py` 新增 `--ui-button-whitelist nargs="*"`（仿 `--dict` 风格）+
config fallback（`ui_button_whitelist` 键）；在 `engine.run(args)` 之前
`load_ui_button_whitelist(args.ui_button_whitelist)`。`core/config.py`
`_CONFIG_SCHEMA` 加 `"ui_button_whitelist": {"type": list}`
333. `core/runtime_hook_emitter.py`：`emit_runtime_hook` 新增
`ui_button_extensions` kwarg + 共享 `_write_json_atomic` helper。非空时
原子写 `output/game/ui_button_whitelist.json`，shape `{"extensions":
[sorted tokens]}`。`emit_if_requested` 调 `get_ui_button_whitelist_extensions`
拿快照透传
334. `resources/hooks/inject_hook.rpy` 新增 ~30 行 sidecar reader（与
`translations.json` 读取对齐的 two-level try/except），`_tl_is_ui_button`
改为检查 `_UI_BUTTONS` OR `_TL_UI_EXT`。缺 sidecar 时 hook 行为逐字节不变
335. 测试 +7：`test_file_processor.py` +5（txt/json/builtin_untouched/
clear_restores/rebinds_frozenset，每条开头 `clear_ui_button_whitelist()`
保 test 隔离）；`test_translation_state.py` +2（sidecar written when
non-empty / skipped when empty）

**Commit 3 · Subtask B：font auto-bundle in `emit_runtime_hook`**

336. `emit_runtime_hook` 新增 `font_path: Path | None = None` kwarg。非 None
且文件存在时：`mkdir output/game/fonts/ -p` + `shutil.copy2(src,
fonts/tl_inject.ttf)`。文件名固定 `tl_inject.ttf` 匹配 `inject_hook.rpy:244`
的 `_TL_FONT_REL`。**Cross-platform 同文件处理**：比较 `resolve()` 路径在
copy 前预判（Windows 同文件 copy 抛 `PermissionError [WinError 32]` 而非
POSIX 的 `SameFileError`），双保险 `SameFileError` 分支保留
337. `emit_if_requested` 用 Commit 1 的 `default_resources_fonts_dir()` +
`resolve_font(dir, args.font_file)` 解析字体路径传给 emitter。`resolve_font`
返回 None（无 flag 无内建字体）→ 静默跳过。返回签名不变（仍
`(json_path, hook_path, count)`），font 是 side-effect 只通过文件存在
断言验证
338. 测试 +4：`copies_font_when_path_given` / `skips_font_when_none`（None +
不存在的路径）/ `font_same_file_tolerated`（Windows WinError 32 回归守护）/
`emit_if_requested_resolves_font_from_args_font_file`

**Commit 4 · Subtask C：`translations.json` v2 nested multi-lang schema**

339. `build_translations_map` 新增 `target_lang="zh"` + `schema_version=1`
kwargs。v1 保持旧 flat shape byte-identical；v2 返回 `{"_schema_version":
2, "_format": "renpy-translate", "default_lang": target_lang,
"translations": {en: {target_lang: zh}}}` 信封。`schema_version ∉ {1,2}`
→ `ValueError`
340. `emit_runtime_hook` 新增 `schema_version` + `target_lang` 透传。
`entry_count` v2 case 数 `translations` 子项数（保持返回语义）。`main.py`
新增 `--runtime-hook-schema {v1,v2}` choices flag（默认 `"v1"`，与 emitter
默认对齐保 round 31 行为）。`emit_if_requested` 映射 `"v1"→1 / "v2"→2`，
未知值安全 fallback v1。`_CONFIG_SCHEMA` 加对应 schema 守护
341. `inject_hook.rpy` schema 检测 + v2 lookup 分支：
   - 头部注释更新：v1/v2 部署步骤 + 运行时环境变量表
   - 加载 `translations.json` 后检测 `_schema_version == 2` → `_TL_SCHEMA=2`、
     `_TL_TRANSLATIONS` 指向内层 `translations`、`_TL_DEFAULT_LANG` 从 JSON
   - `_tl_resolve_lang()` 优先级：`RENPY_TL_INJECT_LANG` env → `renpy.preferences.language`
     （`getattr` + try/except 兜底，`init python early:` 时 preferences 可能
     未构造；Ren'Py "None" 字符串也过滤）→ `_TL_DEFAULT_LANG`
   - `_tl_resolve_bucket(bucket)` 从 `{lang: str}` v2 bucket 按优先级选 lang，
     缺失时退 `default_lang` bucket，仍缺则返回 `None`（caller 回退英文原文）
   - `_tl_lookup` 按 `_TL_SCHEMA` 分支；v1 路径保持原有 API / 行为
342. 测试 +7：`build_translations_map` 4 条（`v1_unchanged` / `v2_structure` /
`v2_respects_target_lang` / `v2_empty_entries`）+ `emit_runtime_hook` 2 条
（`v2_schema_kwarg_produces_nested_json` / `emit_if_requested_respects_
runtime_hook_schema_flag`）+ 1 条结构 smoke：`inject_hook_contains_v2_
reader_markers` 正则扫 `_schema_version` / `RENPY_TL_INJECT_LANG` /
`_TL_TRANSLATIONS` / `_tl_resolve_lang` / `_tl_resolve_bucket` /
`default_lang` / `_format` + env var 在 preferences 之前的顺序（Ren'Py 语法
不可 `py_compile`，所以用 regex smoke 守护）

**Commit 5 · Docs 同步**

343. 本文件（CHANGELOG_RECENT.md）：第 29 轮详细压缩一行并入"演进摘要"；
30/31/32 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
344. CLAUDE.md 项目身份段追加 round 32 新能力；`.cursorrules` 同步；
HANDOFF.md 重写为 32 → 33 交接（测试 307→326、3 项"续做 round 31"
三项全部 ✅）

**结果**：
- 14 测试套件 + `tl_parser` 75 + `screen` 51 内建自测全绿；测试 **307 → 326**
  （+1 Commit 1 / +7 Commit 2 / +4 Commit 3 / +7 Commit 4，合计 +19）
- 所有新功能 default off：`--ui-button-whitelist` 默认空 /
  `--runtime-hook-schema` 默认 `v1` / 字体自动打包仅当 `--emit-runtime-hook`
  开启时生效。既有 tl-mode / direct-mode / retranslate / screen 行为
  byte-identical
- **2 个遗留字体路径 bug 顺手修复**（Commit 1 prep）—— 源码运行时也能
  正确解析 `resources/fonts/`，不再依赖 PyInstaller 打包
- 源文件增量：`core/font_patch.py` 148→163、`file_processor/checker.py` 515→~615、
  `core/runtime_hook_emitter.py` 196→~330、`main.py` 259→~275、
  `resources/hooks/inject_hook.rpy` 270→~345。**仍全部 < 800 行**
- 未引入任何第三方依赖

**本轮未做**（留给第 33+ 轮）：
- v2 schema 的多次翻译运行合并工具（把多次 `--target-lang` 的 v2 envelope
  合并成单一多语言文件 — 本轮只支持单 bucket 生成）
- `TranslationDB.entries` 加 `language` 字段（当前 v2 在 emit 层手工指定，
  未来扩多语言源）
- CI Windows runner（仍是外部基础设施项）
- docs/constants.md / docs/quality_chain.md / docs/roadmap.md 深度复查
- A-H-3 Medium/Deep / S-H-4 Breaking（需真实 API + 社区反馈）
- `inject_hook.rpy` 字体替换的 `--font-config` 信号传递（本轮只打包字体文件，
  未透传 font size 配置）

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
