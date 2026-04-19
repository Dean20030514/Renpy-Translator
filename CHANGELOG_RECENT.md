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
- 第三十轮：冷启动审计后的 4 项 robustness 加固 — `_SubprocessPluginClient` stderr 10 KB 上限 + Popen 异常 atexit 兜底 + http_pool `except Exception` 收窄 + `retranslator.quality_report` 死代码清理；README/engine_guide 刷新；测试 301→302
- 第三十一轮：从竞品 renpy_hook_template 提炼 3 项技巧 — checker UI 白名单 / 占位符漂移修正 / strip_tags L5 fallback + inject_hook.rpy 模板（270 行）+ `--emit-runtime-hook` opt-in CLI（core/runtime_hook_emitter.py + 4 管线 tail 统一调用）；测试 302→307

## 详细记录

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

### 第三十三轮：round 32 延续三小项 — v2 merge 工具 + `--font-config` 透传 + editor v2 适配（+ 顺手拆分 test_translation_state）

HANDOFF round 32 挂起的三项"🟢 自然延续 round 32 方向（小项）"本轮按用户
指定一次全做。实施过程中在 Commit 3 末尾发现 `tests/test_translation_state.py`
已累积到 1256 行（远超 CLAUDE.md 800 行软上限，与 round 29 拆分 `test_all.py`
同性质），用户批准顺手拆分成 Commit 4 prep，故本轮共 **5 commits**，每个
bisect-safe。

**Commit 1 · Subtask 1：v2 translations.json merge 工具**

346. 新增 `tools/merge_translations_v2.py`（~260 行，零依赖纯 stdlib）：
   - `main(argv=None) -> int` + `sys.exit(main())` wrapper（仿
     `tools/rpa_unpacker.py` / `rpyc_decompiler.py` 模板）
   - Library API `merge_v2_translations(paths, *, default_lang, strict) -> dict`
     返回一个新的 v2 envelope；对每个输入严格校验 `_schema_version == 2`
     （v1 flat JSON 直接报错 exit=1），遍历 `translations` 累积
     `{original: {lang: translation}}`
   - 冲突规则：同 `(original, lang)` 对第一次出现胜出，warning 打印；
     `--strict` 时改为立即 MergeError + exit=1
   - 输出 `default_lang` 优先级：`--default-lang` flag > 第一个输入的
     `default_lang` > `"zh"` 硬 fallback
   - 原子写（temp + `os.replace`），与
     `core/runtime_hook_emitter._write_json_atomic` 一致的崩溃安全保证
347. 新增 `tests/test_merge_translations_v2.py`（~290 行，12 tests）
   独立测试套件不进 meta-runner，模仿 `test_rpa_unpacker.py` 风格：
   - Library 9 条：2 lang 合并 / first-wins / envelope 保留 / v1 拒收 /
     malformed JSON / 缺文件 / default_lang 显式覆盖 / strict 模式 /
     fallback "zh"
   - CLI 3 条：happy path / 缺文件 rc=1 / strict 冲突 rc=1

**Commit 2 · Subtask 2：`--font-config` 透传到 runtime hook（生成 zz_tl_inject_gui.rpy）**

关键设计决策：**生成独立 `.rpy` 文件**而非走 sidecar JSON + hook 代码
解析。理由：Ren'Py 惯用 `init 999 python:` 高优先级 block 覆盖 gui.rpy
的 `define gui.xxx = N` 默认值；把覆盖值作为 Python 字面量内嵌到生成
的 .rpy 里最简单安全，无需运行时 JSON 解析。

348. `core/runtime_hook_emitter.py` 新增私有 `_SAFE_GUI_KEY` 正则
`^gui\.[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*$`：禁止任何
能逃逸 "attribute assignment" 形状的 key（空白、操作符、分号注入等）。
349. 新增 `_sanitise_gui_overrides(overrides)` 过滤器：key 必须匹配
`_SAFE_GUI_KEY`；value 必须是 `int` / `float`（不是 `bool` — 即使 Python
把 `True` 当 `int(1)` 我们也拒收，因为没有 `gui.*` 需要布尔）。每个
过滤事件打 warning。
350. 新增 `_emit_gui_overrides_rpy(output_game_dir, overrides, *, filename=
"zz_tl_inject_gui.rpy")` 生成目标 .rpy，shape：
```
init 999 python:
    import os
    if os.environ.get("RENPY_TL_INJECT") == "1":
        gui.text_size = 22
        gui.name_text_size = 24
```
`init 999` 保证在游戏 gui.rpy 的 `define` 之后执行覆盖；env var guard
让文件与游戏一起分发安全。原子写 temp + os.replace。空/全被过滤 →
不生成文件（保 round 32 字节兼容）
351. `emit_runtime_hook` 新增 `font_config: Mapping | None = None` kwarg；
`emit_if_requested` 读 `args.font_config` path，调
`core.font_patch.load_font_config`（与 static `--patch-font` 共享），把
dict 透传给 emitter
352. 测试 +5（round 33 先放在 `test_translation_state.py`，Commit 4 prep
再 move 到新 `test_runtime_hook.py`）：
   - `test_emit_gui_overrides_rpy_when_font_config_has_overrides`（有序键、
     env 守卫、int+float 字面量）
   - `test_emit_gui_overrides_rpy_skips_when_empty`（5 种 no-op 形状）
   - `test_emit_gui_overrides_rpy_rejects_unsafe_keys`（6 种注入变体全挡）
   - `test_emit_gui_overrides_rpy_rejects_unsafe_values`（str/list/dict/
     bool/None 全拒）
   - `test_emit_if_requested_resolves_font_config`（e2e path → aux rpy）

**Commit 3 · Subtask 3：translation_editor 读写 v2 envelope**

353. `tools/translation_editor.py::_extract_from_db` auto-detect v2：JSON 顶层
`_schema_version == 2` → 路由到新增 `_extract_from_v2_envelope(data,
db_path, *, lang=None)`。v1 `translation_db.json` 路径逐字节不变。
354. `_extract_from_v2_envelope` 为每个 original 生成 row，`translation`
取自 `bucket[lang]`（`lang` 默认 envelope 的 `default_lang`）。额外
带入 `v2_path` / `v2_lang` / `v2_default_lang` / `v2_langs_seen` 路由
字段，让 save-back 无需 CLI flag
355. HTML 模板新增 `#v2-banner` 元素（默认隐藏）+ JS `initV2Banner()`：
v2 row 存在时自动显示 "v2 envelope mode — editing &lt;lang&gt; bucket of
&lt;file&gt; | Other buckets: ..."。`exportEdits()` 为 v2 edit 附加
`v2_path` + `v2_lang` 字段。`export_html` 保留 v2 路由 key 到 metadata
JSON
356. `import_edits` 路由 `source == "v2"` edits 到新增 `_apply_v2_edits(v2_
edits, *, create_backup)`：按 `v2_path` 分组，加载每个 v2 envelope，
更新 `translations[original][lang]` 就地，原子写（temp + os.replace）+
可选 `.bak`。非 v2 edits 继续走原有 regex-on-rpy 路径
357. `main` CLI 新增 `--v2-lang LANG`（可选，默认 envelope 的 `default_lang`）
358. 测试 +3（`tests/test_translation_editor.py`，13 → 16）：
   - `test_extract_from_v2_envelope`（auto-detect、default lang、显式 lang
     override、orphan bucket → 空、v1 仍走原路径）
   - `test_import_to_v2_envelope`（两条 edit 不同 lang 写进同一文件，
     `.bak` 保存 pre-edit envelope）
   - `test_v2_envelope_preserves_non_edited_languages`（编辑 zh 不动 ja/ko
     buckets；envelope 顶层 metadata 保持）

**Commit 4 prep · 拆分 tests/test_translation_state.py**

359. Round 29 拆分 `test_all.py` 后，round 31–33 持续往
`test_translation_state.py` 注入 runtime_hook 相关测试（+1 r31，+13 r32，
+5 r33 Commit 2），文件膨胀到 **1256 行**，与 round 29 拆分前的 2539 行
同性质（都是 57%+ 超 800 行软上限）。用户批准把顺手修并入本轮作 Commit
4 prep。零行为变化，纯结构 refactor。
360. 新增 `tests/test_runtime_hook.py`（791 行），21 runtime-hook 测试
byte-identical 拷贝（round 31 Tier C × 2 + round 32 Commit 1 × 1 +
Subtask A × 2 + Subtask B × 4 + Subtask C × 7 + round 33 Subtask 2 × 5）
361. `tests/test_translation_state.py` 瘦身回 504 行，只留 13 条 ProgressTracker
/ TranslationDB / dedup / progress-bar / review-html 测试
362. `tests/test_all.py` meta-runner 从 5 模块扩为 6：新增
`test_runtime_hook.run_all()` 调用；docstring 同步更新成"six focused
modules"。模块级聚合数还是 **142**（19+41+24+24+13+21），分布更合理

**Commit 5 · Docs 同步**

363. 本文件（CHANGELOG_RECENT.md）：round 30 详细压缩进"演进摘要"一行；
31/32/33 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
364. CLAUDE.md 项目身份段追加 round 33 新能力（merge 工具 / font-config
runtime 透传 / editor v2 编辑）+ 测试数 326 → 346；`.cursorrules` 同步
365. HANDOFF.md 重写为 33 → 34 交接（测试 346、15 测试套件、round 32
延续三小项全部 ✅）

**结果**：
- 15 测试套件 + `tl_parser` 75 + `screen` 51 内建自测全绿；测试 **326 → 346**
  （+12 Commit 1 / +5 Commit 2 / +3 Commit 3 / +0 Commit 4 prep 纯拆分）
- 所有新功能 default off：`tools/merge_translations_v2.py` 是新独立工具，
  仅在用户显式运行时触发；`--font-config` runtime 透传仅当
  `--emit-runtime-hook` 同时开启时生效；`--v2-lang` 仅当 editor 读 v2
  文件时生效。既有 tl-mode / direct-mode / retranslate / screen / 静态
  `--patch-font` 行为 byte-identical
- 新增文件 3 个：
  - `tools/merge_translations_v2.py`（~260 行）
  - `tests/test_merge_translations_v2.py`（~290 行，独立套件）
  - `tests/test_runtime_hook.py`（791 行，从 translation_state 拆出来的 21 测试）
- 修改文件 6 个：`core/runtime_hook_emitter.py` (+~140) / `tools/translation_
  editor.py` (+~230) / `tests/test_translation_editor.py` (+~240) /
  `tests/test_translation_state.py` (从 1256 回到 504) / `tests/test_all.py`
  (+~5) / `CHANGELOG_RECENT.md` + `CLAUDE.md` + `.cursorrules` + `HANDOFF.md`
- **所有源文件仍 < 800 行**（最接近 test_runtime_hook.py 791 / tools/
  translation_editor.py 749 / translators/direct.py 601）

**本轮未做**（留给第 34+ 轮）：
- `TranslationDB.entries` 加 `language` 字段（当前 v2 仍在 emit 层手工
  指定 lang bucket；源头数据结构未扩，后续多语言翻译 first-class 支持
  需要 DB schema 升级 + 数据迁移）
- A-H-3 Medium/Deep（让 Ren'Py 走 generic_pipeline 6 阶段 / 完全退役
  DialogueEntry）
- S-H-4 Breaking（强制所有插件走 subprocess，retire importlib 路径）
- RPG Maker Plugin Commands(356) / 加密 RPA / RGSS 归档 / JS 硬编码
- Editor HTML 多语言**同页**编辑（当前每 `--v2-lang` 跑一次，多轮切换
  仍可行但非"单页"体验）
- CI Windows runner + docs/constants.md / quality_chain.md / roadmap.md
  深度复查（连续 4 轮被记到未做列表）

### 第三十四轮：round 33 延续三小项 — TranslationDB language 字段 + editor 同页多语言 + override 分派表

HANDOFF round 33 挂起的三项"🟢 自然延续 round 33 方向（小项）"本轮按用户
指定一次全做。Plan agent 审查时发现 5 大风险（2 CRITICAL + 3 HIGH），用户
批准的 5-commit 修订方案全部吸收风险缓解。每个 commit bisect-safe。

**Commit 1 · Prep（de-risk）：`build_translations_map` `entry_language_filter`**

366. `core/runtime_hook_emitter.py::_iter_translation_pairs` + `build_translations_map`
+ `emit_runtime_hook` 新增 `entry_language_filter: str | None = None` 参数。
filter=None 时零行为变化（round 33 byte-identical）。filter 非 None 时只
保留 `entry.get("language") == filter` 或 `language` 字段缺失（None bucket，
对应 v1 legacy 条目）的 entries，丢弃其他 language 字符串
367. `emit_if_requested` 在 v2 schema 路径下计算 `entry_lang_filter =
args.target_lang` 并透传；v1 路径保持 None（flat schema 无 language 维度）
368. 新独立文件 `tests/test_runtime_hook_filter.py`（90 行，不进 meta-runner）：
   - `test_build_translations_map_filters_by_language`（zh/ja filter + 混合
     buckets + v2 envelope 输出验证）
   - `test_build_translations_map_filter_none_means_no_filter`（round-33
     回归 guard + legacy no-language 形态仍工作）
   避开 `tests/test_runtime_hook.py` 791 行的 800 软上限

**Commit 2 · Subtask 1（最大）：`TranslationDB` schema v2 + `language` 字段**

369. `core/translation_db.py` 194 → 305 行：
   - `SCHEMA_VERSION = 2`（从 1 bump）
   - 构造器新增 `default_language: Optional[str] = None` kwarg
   - `_index` key 从 3-tuple `(file, line, original)` 改为 4-tuple
     `(file, line, original, language_or_None)`；None 是独立 bucket（非通配）
   - `upsert_entry` 自动回填：`default_language` 非空且 entry 无 `language`
     → shallow-copy + 盖章；caller 显式 language 始终胜出
   - `has_entry(file, line, original, language=None)` + `filter_by_status(
     ..., language=None)` 新增 language kwarg；None 精确匹配（非 wildcard），
     3-参 旧调用 shape 向后兼容
   - `save()` 始终写 `version=2`；`load()` 检测 v1 数据 + caller 非空
     `default_language` → **强制回填**所有无 `language` 字段的 entry；
     `_dirty=True` 让下次 save 持久化回填结果；防"(file,line,orig,None)
     与 (file,line,orig,zh) 双份"DB 膨胀
   - 新 `_entry_language(entry)` 静态 helper 规范化 language 字段
370. 所有生产调用者透传 `default_language=args.target_lang`（8 处）：
`pipeline/stages.py` 4 处（retranslate_db / pilot_db / project_db merge 目标
/ sub_db merge 源）+ `translators/direct.py:139` + `translators/tl_mode.py:180`
+ `translators/retranslator.py:375` + `engines/generic_pipeline.py:239`
371. `engines/generic_pipeline.py:260-265` resume index 从 `(file, original)`
2-tuple 改为 `(file, original, language)` 3-tuple；查询 `target_lang` 优先
→ fallback None bucket（兼容 pre-r34 DB）→ miss = 重新翻译。防止 zh 运行
误 resume ja 翻译
372. 新独立测试文件 `tests/test_translation_db_language.py`（307 行，10 tests，
不进 meta-runner）：
   - upsert 显式 language / autofill from default / 同 key 不同 language
     分 bucket 存 / None vs 字符串 language 区分 / filter_by_status
     language kwarg / save+load v2 roundtrip / load v1 无 default 保 None /
     load v1 有 default 回填（**关键 duplicate-prevention 检查**）/
     default_language=None 等价 round 33 / save version bump 2
   每一条都带 tempfile + 原子行为断言

**Commit 3 · Subtask 2：editor 同页多语言切换 + HTML template 抽取**

373. `tools/translation_editor.py::_extract_from_v2_envelope` 给每条 entry
加 `languages: {lang: trans}` 完整 bucket dict；HTML 用这个作切语言的
baseline。`export_html` safe_entries 白名单加入 `languages` key 以随
metadata JSON 传到浏览器
374. **Prep 抽取**（强制执行：改动后 translation_editor.py 达 893 行超 800
限制）：新增 `tools/_translation_editor_html.py`（368 行），把
`_HTML_TEMPLATE = r"""..."""` 常量整体移入作 `HTML_TEMPLATE` 导出；原
文件 `from tools._translation_editor_html import HTML_TEMPLATE as
_HTML_TEMPLATE`，其余字节不变。主文件回到 549 行
375. HTML toolbar 新增 `<label id="v2-lang-switch-label" style="display:none">`
包 `<select id="v2-lang-switch">`；JS 检测 v2 source 后枚举 `v2_langs_seen`
填充 options + 显示 label。非 v2 flow（tl/db source）label 保持隐藏零干扰
376. 新 JS 状态：`_currentV2Lang`（当前编辑语言）+ `_edits[idx][lang]`
（per-row per-lang 待提交 edit 存储）。input 事件除了更新 DOM 也写入
`_edits[i][_currentV2Lang]`，保证切语言不丢失已输入但未导出的 edits
377. 新 JS 函数：
   - `initV2UI()` 替换 round 33 的 `initV2Banner` — 不仅显示 banner 还
     populate dropdown 并 bind change handler
   - `_getRowBaseline(idx, lang)` / `_applyRowFromEdits(tr, idx, lang)`
     辅助：从 `META[idx].languages` 取 baseline；按 pending edit or
     baseline 重绘 col-trans 单元格；更新 dirty/empty/stats flags
   - `switchV2Language(newLang)` 切换：(a) flush 当前 DOM 的 in-flight
     edit 到 `_edits[idx][oldLang]`；(b) 遍历 v2 rows 用新 lang 重绘；
     (c) 更新 banner 的 `<code id="v2-banner-lang">` 文字
378. `exportEdits()` 改 per-(idx, lang) 迭代 `_edits`（v2 路径）+ 保留
per-row DOM-read（非 v2 路径）。一个 original 同时编辑 3 语言 → 导出
3 条独立 record，每条带对应 `v2_lang`；`_apply_v2_edits` 早已 per-lang
处理所以后端侧无需改动
379. `--v2-lang LANG` CLI 语义从"排它性单语言"改为"**初始默认语言**"，
向后兼容（现有 `--v2-lang zh` 调用仍产出合法 HTML，只是多了个 dropdown）
380. `tests/test_translation_editor.py` +3（16 → 19）：
   - `test_extract_from_v2_exposes_full_languages_dict`（每 entry 的
     `languages` 完整 bucket）
   - `test_v2_html_includes_language_switch_dropdown`（扫 HTML 找
     dropdown 元素 + `switchV2Language` / `_edits` / `_currentV2Lang`
     标记 + metadata JSON 的 `languages` 字段）
   - `test_export_edits_multi_language_produces_per_lang_records`（同
     original 多语言 edits 写回各自 bucket 不互扰）

**Commit 4 · Subtask 3：font-config 泛化分派表（只注册 gui）**

381. `core/runtime_hook_emitter.py` 新模块级 `_OVERRIDE_CATEGORIES:
dict[str, re.Pattern]` 分派表；**今天只注册** `"gui_overrides":
_SAFE_GUI_KEY`。docstring 明确解释为何不注册 `style_overrides`（与
`inject_hook.rpy:34-37` 项目级设计选择冲突："不走 style 对象
monkey-patch"）
382. `_sanitise_gui_overrides` → 泛化为 `_sanitise_overrides(overrides,
key_regex, category_name)`，category_name 只作 warning 标签。旧名保留
为 thin back-compat wrapper 调新版
383. `_emit_gui_overrides_rpy` → 泛化为 `_emit_overrides_rpy(output_game_
dir, font_config)` 遍历 `_OVERRIDE_CATEGORIES` 累加安全 key/value 到一
个合并字典 → 单一 `init 999 python:` 块写入 `zz_tl_inject_gui.rpy`。
旧名保留为 thin wrapper 把 single overrides dict 包成 font_config shape
384. `emit_runtime_hook` 的 font_config 分支改调 `_emit_overrides_rpy`
（非未来再修一次）。文件名 `zz_tl_inject_gui.rpy` 保持 round 33 兼容
385. `tests/test_translation_state.py` +2（13 → 15）：
   - `test_sanitise_overrides_unknown_category_ignored`（font_config 带
     `nvl_overrides` / `config_overrides` 未注册 sub-dict 被静默丢弃）
   - `test_override_categories_table_is_extensible`（identity check:
     `_OVERRIDE_CATEGORIES["gui_overrides"] is _SAFE_GUI_KEY`；正负样例
     守护 regex 不被回归放宽）

**Commit 5 · Docs 同步**

386. 本文件（CHANGELOG_RECENT.md）：round 31 详细压缩进"演进摘要"一行；
32/33/34 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
387. CLAUDE.md 项目身份段追加 round 34 新能力（DB language 字段、editor
同页多语言、override 分派表）+ 测试数 346 → 363；`.cursorrules` 同步
388. HANDOFF.md 重写为 34 → 35 交接（测试 363、16 测试套件、round 33
延续三项全部 ✅）

**结果**：
- 16 测试套件 + `tl_parser` 75 + `screen` 51 全绿；测试 **346 → 363**
  （+2 C1 / +10 C2 / +3 C3 / +2 C4，合计 +17）
- 所有新能力向后兼容：`TranslationDB(path)` 旧 2-参构造 = round-33 byte-
  identical；`has_entry(file, line, orig)` 3-参 = round-33 byte-identical；
  v1 DB 文件 + 无 default_language caller = 不做回填保 None bucket；
  editor `--v2-lang` CLI 仍产出合法 HTML
- 新增文件 3 个：
  - `tests/test_runtime_hook_filter.py`（90 行 Commit 1 独立 suite）
  - `tests/test_translation_db_language.py`（307 行 Commit 2 独立 suite）
  - `tools/_translation_editor_html.py`（368 行 Commit 3 prep 抽取）
- 修改文件 10 个：核心 DB / 4 pipeline+translator 调用者 / generic_pipeline
  resume index / runtime_hook_emitter 多次扩展 / translation_editor 多语言
  UI / test_translation_state 加 2 test / test_translation_editor 加 3
  test / test_runtime_hook 注释指针 / 本 CHANGELOG / CLAUDE / HANDOFF
- **所有源文件仍 < 800 行**（最大 translation_editor.py 555 / runtime_hook_
  emitter.py 634 / test_translation_state.py 571 / test_runtime_hook.py 794）
- `has_entry(..., language=...)` / `filter_by_status(..., language=...)`
  / `TranslationDB(path, default_language=...)` / `build_translations_map(
  ..., entry_language_filter=...)` 均为新扩展点，default 保 round-33 语义

**本轮未做**（留给第 35+ 轮）：
- 同次翻译运行产出多语言（需把 `translators/direct.py` / `tl_mode.py`
  的内循环改为按语言迭代；DB schema 已 ready）
- editor 多语言**同行**并列显示（3 列各一语言）— 目前 dropdown 切换是
  单列显示；多列需要 HTML 表格 schema 扩展
- `_OVERRIDE_CATEGORIES` 新注册 category（需要 Ren'Py init-timing 分析）
- A-H-3 Medium/Deep / S-H-4 Breaking（需真实 API + 游戏验证）
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants/quality_chain/roadmap 复查（连续 5
  轮欠账）

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
