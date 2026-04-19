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
- 第三十二轮：round 31 续做全包 — UI 白名单可配置化（sidecar JSON + `--ui-button-whitelist`）+ 字体自动打包（emit 时拷 `game/fonts/tl_inject.ttf`）+ `translations.json` v2 多语言 schema（`--runtime-hook-schema v2` + `RENPY_TL_INJECT_LANG` env 选运行时语言）+ Commit 1 prep（抽 `default_resources_fonts_dir` helper 修 `direct.py:523` / `_tl_patches.py:88` 两处 `__file__.parent` 少一层 bug）；测试 307→326
- 第三十三轮：round 32 延续三小项全包 — `tools/merge_translations_v2.py`（v2 多语言合并工具，独立 260 行纯 stdlib）+ `--font-config` 透传 runtime hook（生成 `zz_tl_inject_gui.rpy` `init 999` 覆盖 gui 字号/布局，`RENPY_TL_INJECT=1` env guard 安全）+ `tools/translation_editor.py` v2 envelope 适配（`--v2-lang` 选 bucket 编辑）+ Commit 4 prep 拆 `test_translation_state.py` 运行时 hook 测试到新 `test_runtime_hook.py`（791 行，21 测试）；测试 326→346

## 详细记录

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

### 第三十五轮：round 34 延续三小项 — 同次多语言输出 + editor side-by-side + 新 override category

HANDOFF round 34 挂起的三项"🟢 自然延续 round 34 方向（小项）"本轮按用户
指定一次全做。Subtask 1 比估时略深（11 处 `args.target_lang` 读取点 +
`tl_mode.py::t.get("zh")` 初看像 bug 实则设计是 prompt 中文专用 + ProgressTracker
无 language 感知）—— 改造面控制在 main.py 外层循环 + ProgressTracker
language namespace，不侵入各 pipeline 内部。共 5 commits，每个 bisect-safe。

**Commit 1 · Prep（de-risk）：ProgressTracker language namespace**

389. `core/translation_utils.py::ProgressTracker` 构造器新增 `language:
str | None = None` kwarg；内部 `_key(rel_path)` helper 返回
`"<lang>:<rel_path>"`（language 非空时）或 bare rel_path。`is_file_done` /
`is_chunk_done` 读路径先查 namespaced key 再 fallback bare key（保
round-34 progress.json resume 不失效）；`mark_chunk_done` / `mark_file_done`
写路径始终用 namespaced key，`mark_file_done` 同时清 bare 和 namespaced
两个 bucket 防跨语言污染
390. 所有生产 ProgressTracker 构造点透传 `language=args.target_lang`
(4 处)：`translators/direct.py:130` / `translators/tl_mode.py:174` /
`translators/retranslator.py:369` / `pipeline/stages.py:82`。tl-mode +
retranslate 实际是中文专用（prompt 硬编码 zh），但仍透传 arg 保对称
+ 为未来 per-language prompt 预留
391. 测试 +3（`tests/test_translation_state.py`，15 → 18）：
   - `test_progress_tracker_language_namespace_isolation`（同 file 两
     language 的 chunk 状态互不见）
   - `test_progress_tracker_legacy_no_language_backward_compat`（无
     language kwarg 时 byte-identical round-34 on-disk shape）
   - `test_progress_tracker_legacy_bare_keys_resume_under_language`
     （pre-r35 bare-key progress 文件 + language-aware tracker 仍能
     resume，关键 migration scenario）
392. **关键澄清**：`translators/tl_mode.py:92` 的 `t.get("zh", "")` 和
`translators/retranslator.py:284` 的同款读取**不是 latent bug**——
tl-mode 和 retranslate 的 system prompt（`core/prompts.py::TLMODE_SYSTEM_PROMPT`
+ `RETRANSLATE_SYSTEM_PROMPT`）硬编码中文输出 `"zh"` 字段，这是设计
（两个模式的 prompt 都是中文专用）。Commit 2 的外循环会在
`--tl-mode` / `--retranslate` + 多语言组合时显式报错

**Commit 2 · Subtask 1：`--target-lang zh,ja,zh-tw` 多语言外循环**

393. 新 `main._parse_target_langs(raw) -> list[str]`：按逗号分隔；
trim whitespace；空/None/纯逗号 fallback `["zh"]`；duplicates 保留
（让 CI 脚本 typo 可见）；BCP-47 hyphen（如 `zh-tw`）不受影响因 split
只分 `,`。`args.target_langs` 派生字段记这个 list；`args.target_lang`
保第一个（或唯一）元素，所有下游代码读单值不改
394. `main.py` 加 guard：`len(args.target_langs) > 1 + (tl-mode /
retranslate)` → exit 1 并打印 actionable 错误消息，防止把重复中文
翻译写进 ja/ko/zh-tw buckets
395. 外循环：包 `engine.run(args)` 在 `for lang in args.target_langs`
里；每次迭代改 `args.target_lang=lang` + 刷新 `args.lang_config`。
多语言模式下启动前 warning 提示 N 倍 API 成本
396. `--target-lang` argparse help 更新示例 + tl-mode/retranslate caveat
397. 新独立文件 `tests/test_multilang_run.py`（95 行，6 tests，不进
meta-runner）：parse_target_langs 单元测试 —— single lang / BCP-47
hyphen / comma-separated / whitespace trim / 空 fallback / duplicates 保留

**Commit 3 · Subtask 2：editor side-by-side 多列显示**

398. `tools/_translation_editor_html.py` toolbar 新增
`<label id="v2-side-by-side-label" style="display:none"><input type=
"checkbox" id="v2-side-by-side" onchange="toggleSideBySide(this.checked)">`。
`initV2UI()` 加 `if (langsSeen.length >= 2)` 判断，只有多语言 envelope
才 reveal label（单语言 v2 / v1 / tl-mode 导出零侧边栏干扰）
399. 新 CSS 类 `.col-trans-multi`（13% width，contenteditable +
dirty + empty-trans 变体）
400. 新 JS 状态 `_sideBySideOn: bool`；`_v2LangsForSideBySide()` helper
从 `META[0].v2_langs_seen` 读
401. `toggleSideBySide(on)`：
   - ON: flush 当前单列 DOM 的 in-flight edit 到 `_edits`（保 pending
     不丢）；remove 之前的 `.col-trans-multi` cells；hide 单列
     `.col-trans` th/td；inject 每语言一列 th + 每 row 每语言一 td
     （contenteditable，binding handler 直接写 `_edits[idx][lang]`，
     删除无效 edit 保证 exportEdits 不产 no-op record）；dropdown
     disabled（不 hide，让 operator 看切回单列时的 baseline lang）
   - OFF: show 回单列 `.col-trans`；remove injected cells；用
     `_applyRowFromEdits(tr, idx, _currentV2Lang)` 重渲单列
402. `_bindSideBySideCellEvents(td, tr, idx, lang)` 每 cell 独立 handler
监听 input/paste/keydown；row-level modified flag = 任何 cell dirty
403. 测试 +3（`tests/test_translation_editor.py`，19 → 22）：
   - `test_side_by_side_toggle_and_styles_present_in_html`（checkbox
     + toggleSideBySide + `_sideBySideOn` + col-trans-multi CSS 齐全）
   - `test_side_by_side_label_hidden_by_default`（label 初始 display:
     none + reveal 门槛 ≥2 langs）
   - `test_side_by_side_preserves_dropdown_coexistence`（dropdown 不被
     移除，flush-before-toggle 保 pending）

**Commit 4 · Subtask 3：注册 `config_overrides` category**

404. `core/runtime_hook_emitter.py` 新增 `_SAFE_CONFIG_KEY` 正则
`r"^config\.[A-Za-z_][A-Za-z_0-9]*$"`——比 gui 更严（**不允许 nested
`config.sub.X`**，因 Ren'Py 的 `config` 是扁平 module-like namespace）
405. `_OVERRIDE_CATEGORIES` 新增 `"config_overrides": _SAFE_CONFIG_KEY`
条目，实现 round 34 挂起的"多 category 分派表"第二项落地。docstring
明确 `style_overrides` 仍刻意排除（遵 `inject_hook.rpy:34-37` 设计选择）
406. 值类型政策不变——仍只 int/float（拒 bool/str/list/dict/None）。
`config.autosave = True` 这类 bool use-case 留给未来 round 扩展
407. 测试 +1 新 / +2 更新（`tests/test_translation_state.py`，15 → 19）：
   - `test_sanitise_overrides_unknown_category_ignored` UPDATED：现在
     既有 `gui_overrides` 也有 `config_overrides` 都 land；
     `nvl_overrides` / `style_overrides` / `foobar_overrides` 仍被丢弃
   - `test_override_categories_table_is_extensible` UPDATED：断言
     `{gui_overrides, config_overrides}` 两条 + 独立验证 config regex
     扁平命名空间规则（拒 `config.sub.nested`）
   - `test_config_overrides_emits_assignments` NEW：端到端验证混合
     safe int/float、unsafe bool、unsafe nested key 情况下只有安全对
     emit；gui + config 在同一 init 999 block 共存

**Commit 5 · Docs 同步**

408. 本文件（CHANGELOG_RECENT.md）：round 32 详细压缩进"演进摘要"一行；
33/34/35 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
409. CLAUDE.md 项目身份段追加 round 35 新能力（`ProgressTracker`
language namespace、`--target-lang` 逗号分隔多语言、editor side-by-side、
`config_overrides`）+ 测试数 363 → 376；`.cursorrules` 同步
410. HANDOFF.md 重写为 35 → 36 交接（测试 376、17 测试套件、round 34
延续三项全部 ✅）

**结果**：
- 17 测试套件 + `tl_parser` 75 + `screen` 51 全绿；测试 **363 → 376**
  （+3 C1 / +6 C2 / +3 C3 / +1 C4，合计 +13）
- 所有新能力向后兼容：
  - `ProgressTracker(path)` 旧 1-参构造 + 无 language kwarg = round-34
    byte-identical 输出；pre-r35 progress 文件在 language-aware 模式
    下仍 resume（fallback 读 bare key）
  - 单语言 `--target-lang zh` = round-34 路径不变（外循环 1 iteration）
  - editor single-language v2 / v1 / tl-mode 导出零 side-by-side chrome
  - `config_overrides` 是新字段，operator 需显式在 font_config.json 里
    填才生效
- 新增文件 1 个：`tests/test_multilang_run.py`（95 行独立 suite）
- 修改文件 7 个：`core/translation_utils.py`（ProgressTracker language
  namespace）/ `pipeline/stages.py` + 3 translators（ProgressTracker
  透传）/ `main.py`（+98 行外循环 + `_parse_target_langs`）/
  `tools/_translation_editor_html.py`（+155 行 side-by-side） /
  `core/runtime_hook_emitter.py`（+~16 行 config_overrides）
- 文件大小检查：最大 `tests/test_translation_editor.py` 751 /
  `main.py` 360 / `runtime_hook_emitter.py` 649 / `translation_utils.py` 507。
  全部 < 800

**本轮未做**（留给第 36+ 轮）：
- tl-mode / retranslate 的 per-language prompt（让 `--tl-mode` +
  `--target-lang ja` 真实工作，不再 guard 拒绝）—— 需重写两个 system
  prompt 模板
- config_overrides 值类型扩 bool（覆盖 `config.autosave=True` 等常见
  use-case）
- editor side-by-side N>3 时 mobile 自适应（media query 或自动回
  dropdown 模式）
- `_OVERRIDE_CATEGORIES` 第三 category（e.g. 专门的 `preferences_overrides`
  for `preferences.afm_time` 等，需审查 init 时序）
- A-H-3 Medium/Deep / S-H-4 Breaking（需真实 API + 游戏验证）
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants/quality_chain/roadmap 复查（连续
  6 轮欠账）

### 第三十六轮：深度审计驱动的 2 个 edge-case bug 修复（H1 + H2）

HANDOFF round 35 末尾的深度审计（3 个并行 Explore 代理从 correctness /
测试覆盖 / 安全三维度报告，手工核实后）定位了 2 个**已复现验证**的真实
bug。用户批准"仅修 H1 + H2"方向，本轮纯 fix 不加新功能，3 commits
每个 bisect-safe。不扩场景、不拉新需求，保 r31-35 五轮 steady-state
迭代的收敛节奏。

**Commit 1：Fix H1 ProgressTracker 跨语言 bare-key 污染**

`core/translation_utils.py::ProgressTracker` r35 加的 bare-key fallback
设计只考虑"单语言 r34→r35 升级保 resume"场景；没考虑"之前跑过 zh，
现在切 ja"。ja 的 `is_chunk_done` 会穿透 namespaced miss 命中 zh 遗留
的 bare key，导致 ja 对应 chunk 被跳过但 DB 里没有 ja bucket 数据 —
ja 输出永久空缺，用户察觉不到。审计复现脚本已手工跑通。

411. `ProgressTracker` 新 class 级常量 `_LEGACY_BARE_LANG: str = "zh"`
带 docstring 解释 pre-r35 convention（r35 前只支持 zh，bare keys 隐式
属于 zh；与 `core/config.py::DEFAULTS["target_lang"]` 和 `main._parse_
target_langs` 空 fallback 一致）。class docstring 同步加 r36 H1 设计
说明段。
412. 修改 4 个方法的 bare-key 访问逻辑（语义：非 zh language 的
language-aware tracker 完全不读/不写 bare bucket）：
   - `is_file_done`（第 198 行）：`self.language and self.language !=
     _LEGACY_BARE_LANG` 时 namespaced miss 后**直接返回 False**，不再
     穿透到 bare 查询
   - `is_chunk_done`（第 212 行）：同上模式
   - `get_file_translations`（第 245 行）：非 zh language 下只返回
     namespaced bucket，跳过 bare bucket 合并（防 zh bare 数据污染
     ja/ko 等的 resume 集合）
   - `mark_file_done`（第 264 行）：cleanup 阶段 bare bucket 的两处 pop
     操作加 `self.language is None or self.language == _LEGACY_BARE_
     LANG` 守卫 — 非 zh tracker 不清 bare 数据（镜像保护：避免 ja 完成
     后摧毁 hypothetical zh resume data）
413. `tests/test_translation_state.py` +1 `test_progress_tracker_language_
switch_does_not_leak_across_langs`（~50 行）：handcraft HANDOFF 审计的
精确 reproducer（pre-r35 bare-key progress.json + `language='ja'`
tracker），断言 is_file_done / is_chunk_done / get_file_translations
全 False；ja mark_chunk_done + mark_file_done 后 bare bucket 仍含
完整 zh 数据；zh 对照组开同样 pre-r35 文件仍能 resume（守 r35
`test_progress_tracker_legacy_bare_keys_resume_under_language` 语义）
414. `run_all()` 注册新测试 — meta-runner 148 → 149

**Commit 2：Fix H2 `_sanitise_overrides` 拒绝非有限 float**

`core/runtime_hook_emitter.py::_sanitise_overrides` 的值类型检查只排
`bool` / 非 `(int, float)`，**没排** `inf` / `-inf` / `nan`。Python 的
`json.loads` 默认接受 JSON `Infinity` / `NaN`（非 JSON 标准但 Python
扩展），不可信 `font_config.json` 能偷渡 inf/nan；过现有 isinstance 闸
门后 `repr(inf) == 'inf'` 写入 `zz_tl_inject_gui.rpy` 的 `init python:`
block → Ren'Py 启动 NameError，游戏挂。审计复现脚本已手工跑通。

415. `core/runtime_hook_emitter.py` 顶部 imports 段加 `import math`
（按 stdlib 字母序插入：json / logging / math / re / shutil）
416. `_sanitise_overrides`（第 224 行）在 bool/非数值闸门后、赋值到
`clean[]` 前插入：
```python
if isinstance(raw_val, float) and not math.isfinite(raw_val):
    logger.warning(
        "[TL-INJECT] skipping non-finite %s value for %s: %r",
        category_name, raw_key, raw_val,
    )
    continue
```
完全复用现有 warning log pattern。过滤自动覆盖所有注册的 category
（`gui_overrides` / `config_overrides`）因共享 helper 入口
417. `tests/test_runtime_hook_filter.py` +1 `test_sanitise_overrides_
rejects_non_finite_floats`（~47 行）：构造混合 safe int/float + 不安全
inf/-inf/nan 在 `gui_overrides` + `config_overrides` 下；emit 后断言
aux rpy 含 safe 值赋值，不含任何 `= inf` / `= -inf` / `= nan` 字样；
额外测 all-non-finite config 场景不生成 aux rpy（空 combined map →
`_emit_overrides_rpy` 返回 None）。文件头 docstring 同步更新
"Runtime-hook emitter micro-tests — safety / filter overflow suite"，
解释 H2 测试放此处而非 `test_translation_state.py`（r34/r35 override
convention）的原因：H1 补进后 test_translation_state.py 已 799 行，
再加 H2 会越 800 软限

**关键设计决定**：`_LEGACY_BARE_LANG = "zh"` 硬编码而非从 `core/config.py`
动态读。理由：(1) 减少 import 依赖链；(2) 如未来改 default 语言，
progress 数据语义被动变化是 surprising，显式更新常量 + docstring 强制
人工 review 更安全；(3) class 级常量最小 scope。

**Commit 3：Docs sync**

418. 本文件（CHANGELOG_RECENT.md）：round 33 详细压缩进"演进摘要"
一行；34/35/36 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
419. CLAUDE.md 项目身份段追加 r36 修复 note（"r36 修 H1 bare-key 跨语言
污染 + H2 inf/nan runtime hook 注入"）+ 测试数 376 → 378；`.cursorrules`
同步（`cp CLAUDE.md .cursorrules`，字节相同）
420. HANDOFF.md 重写为 36 → 37 交接：H1/H2 从"🔴 必修"挪到"✅ r36
已修"section；保留 M1-M5 / pre-existing 4 个大文件 / r35 原绿色小项
作 r37 候选；架构健康度表"潜伏 bug"清零日期更新到 round 36

**结果**：
- 17 测试套件 + `tl_parser` 75 + `screen` 51 内建自测全绿；测试 **376 → 378**
  （+1 H1 在 `test_translation_state.py` / +1 H2 在 `test_runtime_hook_
  filter.py`）
- 所有改动向后兼容：
  - `ProgressTracker(path)` 无 language kwarg 用法 byte-identical round-35
  - `ProgressTracker(path, language="zh")` 语义 byte-identical round-35
    （保 pre-r35 bare-key resume 测试 `test_progress_tracker_legacy_bare_
    keys_resume_under_language`）
  - 非 zh language-aware 调用是**唯一行为改变点** — 之前错误继承 zh
    bare 数据，现在正确隔离
  - `_sanitise_overrides` 仅在之前会 emit inf/nan（随后崩溃）的场景
    改为 skip；默认路径零行为变化
- 新增文件 0 个；修改文件 4 个（仅代码）+ 4 个（文档）：
  - `core/translation_utils.py` 508 → 547（+1 常量 + 4 方法 gate + 扩
    docstring）
  - `core/runtime_hook_emitter.py` 649 → 661（+`import math` + 5 行
    isfinite check + 说明 comment）
  - `tests/test_translation_state.py` 733 → 799（+H1 test + 扩 run_all）
  - `tests/test_runtime_hook_filter.py` 90 → 137（+H2 test + 扩 docstring
    + 扩 run_all）
  - CHANGELOG_RECENT.md / CLAUDE.md / .cursorrules / HANDOFF.md
- 文件大小检查：最大 `tests/test_translation_state.py` 799 / `test_runtime_
  hook.py` 794 / `tests/test_translation_editor.py` 751 / `core/runtime_
  hook_emitter.py` 661 — 全部 < 800 ✓

**本轮未做**（留给第 37+ 轮）：
- M1 `TranslationDB.load()` v2 schema + 部分 entries 缺 language 字段
  时 backfill 缺口（~3 行 + 1 测试）
- M2 3 处 JSON loader 无文件大小上限（`core/font_patch.py:91` /
  `core/translation_db.py:132` / `tools/merge_translations_v2.py:64`，
  ~15 行）
- M3 `main.py:342-353` 外循环末尾 `args.target_lang` 残留最后语言
  （~3 行，无实际 reader，但未来扩展易踩）
- M4 `tools/translation_editor.py::_apply_v2_edits:431` 的 `v2_path`
  路径白名单（~10 行）
- M5 side-by-side 编辑空串语义歧义文档化（JS / Python 一致性提示，
  ~5 行）
- Pre-existing 4 个 >800 行文件拆分（`tools/rpyc_decompiler.py` 974 /
  `core/api_client.py` 965 / `tests/test_engines.py` 962 / `gui.py`
  815）— 建议独立一轮参 r17 / r29 / r32 拆分 precedent
- r35 原 HANDOFF 候选的 3 项绿色小项：tl-mode / retranslate per-lang
  prompt（让 `--tl-mode ja` 真实工作）/ `config_overrides` 值类型扩
  bool / editor side-by-side mobile 自适应
- A-H-3 Medium / Deep（让 Ren'Py 走 generic_pipeline 6 阶段 / 完全退役
  DialogueEntry）/ S-H-4 Breaking（强制所有插件走 subprocess）— 需
  真实 API + 游戏验证
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants / quality_chain / roadmap 复查
  （连续 7 轮欠账）

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
