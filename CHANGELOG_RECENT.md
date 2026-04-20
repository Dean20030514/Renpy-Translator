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
- 第三十四轮：round 33 延续三小项全包 — `TranslationDB` schema v2 + `language` 字段 + 4-tuple 索引（`has_entry` / `filter_by_status` / `upsert_entry` language-aware；v1→v2 `load()` 强制回填防 duplicate-bucket 膨胀）+ `tools/translation_editor.py` HTML dropdown 同页多语言切换（per-lang `_edits` 状态 + 切换时 flush 保 pending）+ `_translation_editor_html.py` 模板抽离（368 行）+ `_OVERRIDE_CATEGORIES` 泛化 override 分派表（仅注册 gui，为 r35 config 扩展留点）+ Commit 1 prep `build_translations_map::entry_language_filter` 防 v2 emit 跨 bucket 污染；测试 346→363
- 第三十五轮：round 34 延续三小项全包 — `ProgressTracker` 加 `language` kwarg + `_key()` namespace（`"<lang>:<rel_path>"` key，保 bare-key fallback 兼容 r34 progress.json resume）+ `main.py::_parse_target_langs` 解析 `--target-lang zh,ja,zh-tw` 逗号分隔多语言（外层 `engine.run` 循环 + `--tl-mode` / `--retranslate` 多语言 guard 因 prompt 中文专用）+ `tools/_translation_editor_html.py` `toggleSideBySide` / `_bindSideBySideCellEvents` + `.col-trans-multi` CSS 做 side-by-side 多列并列显示（dropdown 保留共存，flush-before-toggle 保 pending 不丢）+ `_OVERRIDE_CATEGORIES` 注册第二个 category `config_overrides`（扁平 `config.X = int|float` 仅，为 r38 bool 扩展留点）+ 新独立 suite `tests/test_multilang_run.py`；测试 363→376
- 第三十六轮：深度审计驱动的 2 个 edge-case bug 修复（纯 fix 无新功能）— H1 `ProgressTracker` 跨语言 bare-key 污染（非 zh language-aware tracker 不再读/写 bare bucket；新增 class 常量 `_LEGACY_BARE_LANG = "zh"` 标注 pre-r35 implicit owner + `mark_file_done` 镜像守卫防非 zh 清 bare 数据）+ H2 `_sanitise_overrides` 加 `math.isfinite` 过滤拒收 `float('inf')/'-inf'/'nan'`（防 `repr(inf)='inf'` 写入 `init python:` block 致 Ren'Py 启动 NameError）；2 regression 测试；测试 376→378
- 第三十七轮：HANDOFF round 36→37 预规划的 M 级防御加固包（M1-M5）— M1 `TranslationDB.load()` 去 `version < SCHEMA_VERSION` gate 让 partial v2 文件缺 `language` 字段的 entry 也 backfill + M2 4 处用户面 JSON loader 加 50 MB size cap（`font_patch.load_font_config` / `translation_db.load` / `merge_translations_v2._load_v2_envelope` / `translation_editor._apply_v2_edits`）+ M3 `main.py` 外层 multi-lang 循环 try/finally restore `args.target_lang` / `lang_config` + M4 `_apply_v2_edits` 加 `Path.cwd().resolve()` path whitelist 防钓鱼 edits.json + M5 空串 cell = SKIP 语义文档化 + side-by-side label 加 tooltip；5 fix + 1 docs commits，+7 regression 测试；测试 378→385

## 详细记录

### 第三十八轮："收尾包"一轮清（测试拆 + M2 扩 + config bool + mobile CSS）

HANDOFF round 37→38 推荐的"收尾包"方向：清理 r37 加测试导致的
`test_translation_editor.py` 越 800 软限 + 扩展 M2 到其余用户面 JSON
loader + 闭环 r35 挂起的两项绿色小项（`config_overrides` 扩 bool /
editor side-by-side mobile 自适应）。用户同意后一轮全做。5 commits，
每 bisect-safe。

**Commit 1（prep）：拆 `test_translation_editor.py` 成 v1 + v2 两份**

r37 加 M4 / M5 测试 + 3 处 tempdir dir=cwd 调整后文件 847 行，越 800
软限 47 行。按 r33 Commit 4 prep 的 `test_translation_state.py` 拆分
precedent，把 11 个 v2-related 测试（r33 S3 × 3 + r34 C3 × 3 + r35
C3 × 3 + r37 M4 × 1 + r37 M5 × 1）+ `_make_v2_envelope` helper 整体
byte-identical 迁到新文件。纯结构 refactor，零行为变化。

429. 新建 `tests/test_translation_editor_v2.py`（553 行，11 测试 +
helper + main runner）。文件头 docstring 解释拆分缘由 + 每个测试的
归属（r33 / r34 / r35 / r37）
430. `tests/test_translation_editor.py` 瘦身到 376 行（847 → 376，
剩 13 个 v1 / tl / db / escape / empty 测试 + utility test_escape_for_rpy）
431. 两文件都 `< 800` ✓；test 总数 24 保持（13 + 11）不变

**Commit 2：M2 扩展到 4 个用户面 JSON loader（r37 M2 之外的 4 处）**

r37 M2 覆盖了 4 处 user-facing JSON loader（font_patch / translation_db
/ merge_v2 / translation_editor::_apply_v2_edits）。r37 HANDOFF 识别
~16 处仍无 size cap；本轮按用户同意扩到 4 处「优先级最高」的
operator-supplied path：

432. `core/config.py::_load_config_file`（第 105 行 `json.loads`）：
新增模块级常量 `_MAX_CONFIG_FILE_SIZE = 50*1024*1024`；读前
`p.stat().st_size > cap` → warning + `continue`（search_paths loop
fall through to next / defaults）
433. `core/glossary.py` 4 个 JSON loader（Actors.json / System.json
/ `load_system_terms` / `load`）：新增 `_MAX_GLOSSARY_JSON_SIZE =
50*1024*1024` 常量 + 共享 helper `_json_file_too_large(path) -> bool`
（warning 副作用在 helper 内，caller 只 `return`/`continue`）。4 处
调用点各加 `and not _json_file_too_large(path)` / 显式 `if too_large:
return` 守卫
434. `tools/translation_editor.py`：r37 `_MAX_V2_APPLY_SIZE` 改名为更
generic 的 `_MAX_EDITOR_INPUT_SIZE`（保向后兼容 alias），两处新增：
   - `_extract_from_db`（第 119 行）读前 size-cap → warning + `return []`
     → `main()` 打印 "No entries found to export"
   - `import_edits`（第 297 行）读前 size-cap → warning + `return
     {applied:0, skipped:0, files_modified:0}`（CLI summary 仍 well-formed）
435. 测试 +4：
   - `tests/test_glossary_prompts_config.py` +2（`test_config_file_
     rejects_oversized` + `test_glossary_load_rejects_oversized`）—
     后者覆盖共享 helper，一测 4 sites
   - `tests/test_translation_editor.py` +2（`test_extract_from_db_
     rejects_oversized_file` + `test_import_edits_rejects_oversized_file`）
   所有测试用 51 MB sparse file（`f.seek(51<<20-1); f.write(b'\\0')`）

**Commit 3：`config_overrides` 值类型扩 bool（r35 挂起绿色小项）**

r35 C4 的 `_OVERRIDE_CATEGORIES` 分派表让 `gui_overrides` +
`config_overrides` 共享 int/float 白名单。但 Ren'Py 的 `config.*`
命名空间有一等公民级 bool switches（`config.autosave` /
`config.developer` / `config.rollback_enabled` 等），操作员填这些值
被 `_sanitise_overrides` 当 non-numeric warning-drop。r35 HANDOFF
挂起至今。

436. `core/runtime_hook_emitter.py` 新增 per-category bool policy map：
```python
_OVERRIDE_ALLOW_BOOL: "dict[str, bool]" = {
    "gui_overrides": False,
    "config_overrides": True,
}
```
437. `_sanitise_overrides` 新增 `allow_bool: bool = False` kwarg
（default False 保 r33-r37 byte-identical）。bool 检查显式排在 int/float
检查**之前**（因 `isinstance(True, int)` 为 True，不能让 bool 混
过 int 闸门）
438. `_emit_overrides_rpy` 的 category 分派循环里 `allow_bool =
_OVERRIDE_ALLOW_BOOL.get(cat_name, False)` 然后透传给
`_sanitise_overrides`。`repr(True)` / `repr(False)` = `"True"` /
`"False"`（合法 Ren'Py Python literal），emit 不需额外 escape
439. 更新 r35 测试 `test_config_overrides_emits_assignments`：断言
`config.autosave = True` + `config.developer = False` 两个 bool 都 land
（之前 r35 断言它们被 reject）。r33 测试 `test_emit_gui_overrides_rpy_
rejects_unsafe_values` 继续守护 gui 拒 bool 语义 — 未改
440. 新 regression 测试 `test_gui_overrides_still_rejects_bool`：同
font_config 混合 `gui.bad_flag=True`（gui 拒 bool）+
`config.autosave=True`（config 接受 bool），断言 per-category 策略
真正分流（gui bool 不 leak 成 emit，config bool 确实 emit）

**Commit 4：editor side-by-side mobile `@media` 自适应（r35 挂起绿色小项）**

r35 C3 的 side-by-side `.col-trans-multi` 固定 `width: 13%`，6 语言
时每列 < 75px 在 480px 手机 viewport 根本没法编辑。r35 HANDOFF 挂起。

441. `tools/_translation_editor_html.py` CSS 段末加
`@media (max-width: 800px)` block：
```css
@media (max-width: 800px) {
  table { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
  thead, tbody { display: table; width: 100%; }
  .col-trans-multi { min-width: 120px; width: auto; }
  .col-file { width: 120px; }  /* 桌面 180px 太占，窄屏收 */
}
```
桌面 (>= 800px) 行为不变。iOS Safari 加 `-webkit-overflow-scrolling:
touch` 补 momentum scrolling
442. `tests/test_translation_editor_v2.py` +1 `test_side_by_side_
mobile_media_query_present` — 断言 `HTML_TEMPLATE` 常量含
`@media (max-width: 800px)` + `min-width: 120px` + `overflow-x: auto`
+ iOS scroll 属性

**Commit 5：Docs sync**

443. 本文件（CHANGELOG_RECENT.md）：round 35 详细压缩进"演进摘要"
一行；36/37/38 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
444. CLAUDE.md 项目身份段追加 r38 note + 测试数 385 → 391；
`.cursorrules` 同步（字节相同）
445. HANDOFF.md 重写为 38 → 39 交接；M2 扩展 + C3 + C4 从"r38 候选"
挪到"✅ r38 已修"；保留 pre-existing 4 大文件拆分 + tl-mode per-lang
prompt + 其他 ~10 处 JSON loader size cap 扩展作 r39 候选

**结果**：
- 19 测试套件 + `tl_parser` 75 + `screen` 51 = **517 断言点**；测试
  **385 → 391**（+6：C2 × 4 + C3 × 1 + C4 × 1；prep 拆分 +0）
- 所有改动向后兼容：
  - 测试拆：零行为变化，只是两个文件替代一个
  - M2 扩展：合法 < 50 MB 文件完全不受影响
  - C3 bool：gui 行为不变（仍拒 bool）；config 是 opt-in widen（只有
    operator 显式填 bool 才受影响，之前会被 reject，现在接受）
  - C4 mobile：桌面 (>= 800px) byte-identical；窄屏是 UX 改进非改变
- 新增文件 1 个：`tests/test_translation_editor_v2.py`（553 行）
- 修改文件 6 代码 + 2 测试 + 4 文档：
  - `core/config.py` 132 → 144（+M2 site 1）
  - `core/glossary.py` ~300 → ~332（+M2 sites 2-5 + helper）
  - `core/runtime_hook_emitter.py` 661 → ~693（+C3 per-category bool）
  - `tools/translation_editor.py` 677 → ~716（+M2 sites 6-7 + docstring）
  - `tools/_translation_editor_html.py` 523 → ~540（+C4 @media block）
  - `tests/test_glossary_prompts_config.py` 525 → ~595（+2 M2 tests）
  - `tests/test_translation_editor.py` 847 → ~440（-471 拆走 + M2 +40）
  - `tests/test_translation_editor_v2.py` 0 → 574（新文件 +C4 test）
  - `tests/test_translation_state.py` 799 → ~850（+C3 gui regression
    — 注意新增 50 行后越 800 软限，作 r39 候选）
  - CHANGELOG / CLAUDE / .cursorrules / HANDOFF
- 文件大小检查：
  - `tests/test_translation_state.py` ~850（r38 C3 加 gui regression 后
    越 800）— r39 建议拆分
  - `tests/test_translation_editor.py` 440 ✓（r38 拆分成功）
  - 其他源码 / 测试 均 < 800

**本轮未做**（留给第 39+ 轮）：
- `tests/test_translation_state.py` 850 行越 800 软限（r38 C3 加 50 行
  gui regression 后），r39 候选拆分
- Pre-existing 4 个源文件 > 800 行（`rpyc_decompiler.py` / `api_client.py`
  / `tests/test_engines.py` / `gui.py`）— r17 / r29 / r32 / r33 / r38
  拆分 precedent
- 其他 ~10 处 JSON loader size cap 扩展（`engines/generic_pipeline.py:
  151` / `core/translation_utils.py:138` / `translators/_screen_patch.py:
  311` / `tools/analyze_writeback_failures.py:36` / `tools/review_
  generator.py:35` / `tools/rpyc_decompiler.py:437` / `engines/rpgmaker_
  engine.py:85,396` / `pipeline/stages.py:212,378` / `pipeline/gate.py:
  116` / `gui.py:718` 等）
- r35 最后一项绿色小项：tl-mode / retranslate per-language prompt —
  让 `--tl-mode ja` 真实工作
- A-H-3 Medium / Deep / S-H-4 Breaking — 需真实 API + 游戏验证
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants / quality_chain / roadmap 复查
  （连续 9 轮欠账）

### 第三十九轮："收尾包 Part 2"（test_state 拆 + tl-mode per-lang prompt + M2 phase-2）

HANDOFF round 38→39 推荐的"收尾包 Part 2"方向：清理 r38 C3 加测试导致
的 `test_translation_state.py` 越 800 软限 + 闭环 r35 最后一项挂了 4 轮
的绿色小项（tl-mode / retranslate per-language prompt）+ 继续扩展 M2 到
剩余用户面 JSON loader。用户同意后一轮全做。4 commits，每 bisect-safe。

**Commit 1（prep）：拆 `tests/test_translation_state.py` 越软限**

r38 C3 加 `test_gui_overrides_still_rejects_bool` 约 50 行后文件 850 行
（799 → 850，+51），越 800 软限 50 行。按 r33 / r38 拆分 precedent 把
r34/r35/r38 的 4 个 override-dispatch-table 相关测试 byte-identical 迁
到新文件。纯结构 refactor，零行为变化。

446. 新建 `tests/test_override_categories.py`（218 行，4 测试 + main
runner）。文件头 docstring 解释拆分缘由 + 每个测试的归属（r34 / r35 /
r38）
447. `tests/test_translation_state.py` 瘦身到 681 行（850 → 681），剩
17 个 ProgressTracker / TranslationDB / review-generator 测试
448. 两文件都 `< 800` ✓；test 总数 21 保持（17 + 4）不变。meta-runner
`test_all.py` 从 152 → 148（4 override 测试移出；新文件独立 suite
贡献 4）

**Commit 2：tl-mode + retranslate per-language prompt（r35 最后一项挂起）**

r35 multi-lang 外循环之后，tl-mode 和 retranslate 的 system prompt 仍
硬编码中文输出（`"zh"` 字段）。r35 加 guard 让 `--tl-mode --target-lang
ja` 报错。r35 HANDOFF 挂起至今，r36/r37/r38 被其他优先级让行。r39 真
实支持非 zh 目标：

449. `core/prompts.py` 新增两个 generic 英文模板：
  - `_GENERIC_TLMODE_SYSTEM_PROMPT`（带 `{target_language}` /
    `{native_name}` / `{translation_instruction}` / `{field}` /
    `{style_notes}` / `{glossary_block}` 占位符）
  - `_GENERIC_RETRANSLATE_SYSTEM_PROMPT`（同上 + `>>>` 标记语法保留）
450. `build_tl_system_prompt` + `build_retranslate_system_prompt` 加
`lang_config` kwarg：`None` / `zh` / `zh-tw` → 既有中文模板 byte-
identical r38；其他语言（`ja` / `ko` / 等）→ 新 generic 模板。CoT
addon 分支也按 lang_code（非 zh 用 `_COT_ADDON_EN`）
451. `core/translation_utils.py::TranslationContext` 加 optional
`lang_config` 字段（default `None` 保 direct_file / tl_mode 现有 2 个
callers 向后兼容）
452. `translators/tl_mode.py::run_tl_pipeline` 透传 `args.lang_config`
→ `build_tl_system_prompt` + `TranslationContext`；`_translate_chunk`
response reader 在 `ctx.lang_config` 非 None 时用
`core.lang_config.resolve_translation_field`（alias chain `"zh"` /
`"ja"` / `"jp"` / `"japanese"` 等）读译文字段，`None` path 保
`t.get("zh", "")` 硬编码
453. `translators/retranslator.py::retranslate_file` 加 `lang_config`
kwarg（default None）+ 透传给 `build_retranslate_system_prompt` + 响应
读取点用 `resolve_translation_field`；`run_retranslate_pipeline` 透传
`args.lang_config`
454. `main.py` 去掉 r35 的 multi-lang guard block（之前 `tl_mode` /
`retranslate` + `len(target_langs) > 1` 触发 exit=1）替换为解释块指向
r39 修复；`--target-lang` argparse help 更新说明
455. `tests/test_multilang_run.py` +2 regression：`test_tl_system_
prompt_per_language_branch`（zh → 中文模板 byte-identical；ja / ko →
generic 英文模板 + 正确 lang_config 字段替换）+ `test_retranslate_
system_prompt_per_language_branch`（同契约，`>>>` 标记语法跨路径保留）

**Commit 3：M2 phase-2 — 3 处 user-facing JSON loader**

r37 M2 覆盖 4 处；r38 M2 扩到 4 处；r39 再扩 3 处（r38 HANDOFF 识别的
~10 处用户面 loader 中 priority 最高的 3 处）。每处加 module-level
`_MAX_*_SIZE = 50 * 1024 * 1024` + 读前 `path.stat().st_size` 检查：

456. `tools/review_generator.py::generate_review_html`（operator 供
translation_db.json → HTML 报告）：oversize → warning + return 0 →
caller `main()` 层打印 "no entries"
457. `tools/analyze_writeback_failures.py::analyze`（operator 供
translation_db.json → failure 分析 dict）：oversize → warning + return
`{total: 0, by_type: {}, samples: {}}` → CLI summary well-formed
458. `pipeline/gate.py` glossary 加载块（读输出 tree 的 auto-detected
glossary.json）：oversize → raise `OSError` → 落到既有 try/except 的
malformed-glossary 降级分支（r26 H-4 契约：WARNING + locked-term /
no-translate 检查禁用，其他 gate 继续）
459. `tests/test_runtime_hook_filter.py` +3 regression 测试（文件 scope
已在 r36 / r37 扩成 "safety / filter overflow suite"，house 项目 size-
cap 测试天然）。全用 51 MB sparse file。Gate 测试直接断言常量 +
sparse-file size check（evaluate_gate 全流程 roundtrip 需要真实 translated
tree + DB，属集成测试范畴）

**Commit 4：Docs sync**

460. 本文件（CHANGELOG_RECENT.md）：round 36 详细压缩进"演进摘要"
一行；37/38/39 保留详细
461. CLAUDE.md 项目身份段追加 r39 note + 测试数 391 → 396；`.cursorrules`
同步（字节相同）
462. HANDOFF.md 重写为 39 → 40 交接；r39 四项修从"r39 候选"挪到"✅ r39
已修"；保留 pre-existing 4 大文件拆 + 剩余 ~7 处 JSON loader（内部 /
低风险）+ A-H-3 Medium/Deep 等作 r40 候选

**结果**：
- 19 测试套件 + `tl_parser` 75 + `screen` 51 = **522 断言点**；测试
  **391 → 396**（+5：C1 prep 拆分 +0 / C2 per-lang prompt +2 / C3
  M2 phase-2 +3）
- 所有改动向后兼容：
  - 测试拆：零行为变化，只是两个文件替代一个
  - per-lang prompt：`lang_config=None` / `zh` / `zh-tw` 保中文模板
    byte-identical；`None` default 在所有 caller 当 legacy 路径
    安全
  - M2 phase-2：合法 < 50 MB 文件完全不受影响
- 新增文件 1 个：`tests/test_override_categories.py`（218 行）
- 修改文件 6 代码 + 2 测试 + 4 文档：
  - `tests/test_translation_state.py` 850 → 681（移出 4 测试）
  - `core/prompts.py` 530 → ~695（+2 新 template + `build_*` 重构）
  - `core/translation_utils.py` 547 → 549（+TranslationContext
    `lang_config` 字段）
  - `translators/tl_mode.py` + `translators/retranslator.py` 透传
    lang_config
  - `main.py` 去 r35 guard + argparse help 更新
  - `tests/test_multilang_run.py` 89 → ~155（+2 r39 prompt 测试）
  - `tools/review_generator.py` / `tools/analyze_writeback_failures.py`
    / `pipeline/gate.py`（+M2 phase-2 caps）
  - `tests/test_runtime_hook_filter.py` 217 → ~295（+3 M2 phase-2 测试）
  - CHANGELOG / CLAUDE / .cursorrules / HANDOFF
- 文件大小检查：
  - `tests/test_translation_state.py` 681（r38 850 → 681，回到软限内）
  - 其他全部 < 800

**本轮未做**（留给第 40+ 轮）：
- Pre-existing 4 个源文件 > 800 行（`rpyc_decompiler.py` 974 /
  `api_client.py` 965 / `tests/test_engines.py` 962 / `gui.py` 815）—
  r17 / r29 / r32 / r33 / r38 / r39 拆分 precedent 已很充分
- 剩余 ~7 处内部 / 低风险 JSON loader size cap（`engines/generic_
  pipeline.py:151` / `core/translation_utils.py:138` / `translators/
  _screen_patch.py:311` / `tools/rpyc_decompiler.py:437` /
  `engines/rpgmaker_engine.py:85,396` / `pipeline/stages.py:212,378` /
  `gui.py:718`）
- A-H-3 Medium / Deep / S-H-4 Breaking — 需真实 API + 游戏验证
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants / quality_chain / roadmap 复查
  （连续 10 轮欠账）

### 第四十轮：pre-existing 大文件拆分（3/4，gui.py 挂 r41）

HANDOFF round 39→40 主推方向：拆分 4 个 pre-existing > 800 行源文件
（r31-39 均未触碰，最老可追溯到 r10 前）。`gui.py` (815 行) 因
PyInstaller 打包耦合 + 单 class 内部边界不清 + UI 代码手动测试要求，
风险显著高于其他三个——本轮优先做风险低的 3 个，`gui.py` 挂 r41
独立一轮专门做（含 `build.py` 打包回归）。4 commits，每 bisect-safe，
全部是纯结构 refactor（byte-identical extraction + re-export 保
向后兼容），零行为变化 / 零新测试。

**Commit 1（prep）：拆 `tests/test_engines.py` RPG Maker 块**

r10 前就形成的 962 行测试文件。RPG Maker MV/MZ 是自包含的 engine
slice（独立导入 `engines.rpgmaker_engine` + `core.glossary`，自带
2 个 tempdir 辅助函数 `_make_rpgm_mv_dir` / `_make_rpgm_mz_dir`）—
clean cut point。

463. 新建 `tests/test_engines_rpgmaker.py`（315 行，15 测试 + 2
helper + main runner）：`test_rpgm_detect_mv` / `_mz` / `_false` /
`_find_data_dir` / 4 event-command extraction 测试（401 merge / 102
choices / 405 scroll / 320 name change）/ `_extract_database` /
`_extract_system` / 2 writeback 测试 / `_patch_by_json_path` /
`_navigate_to_node` / `test_glossary_scan_rpgmaker`
464. `tests/test_engines.py` 瘦身到 694 行（962 → 694），剩 47 测试
（EngineProfile / TranslatableUnit / EngineDetector / RenPyEngine /
EngineBase / CSV Engine / generic_pipeline / patcher-checker / prompts
addon）
465. 两文件均 `< 800` ✓；test 总数 62 保持（47 + 15）；meta-runner
`test_all.py` 不受影响（test_engines 作独立 suite）

**Commit 2：拆 `tools/rpyc_decompiler.py` 974 → 725（-249）**

HANDOFF 建议"Tier1 + Tier2 两条反编译链可拆"。实际拆分采用 3-module
布局避免循环 import（主 re-exports from Tier 2 requires Tier 2 import
first but Tier 2 imports shared constants → shared must be a leaf）：

466. 新建 `tools/_rpyc_shared.py`（47 行）：`RPYC2_HEADER` /
`_AST_SLOT` 格式常量 + `_SHARED_WHITELIST` / `_WHITELIST_TIER1_PY2_
EXTRAS` pickle 白名单（r26 H-4 "no drift" 契约的源头数据）
467. 新建 `tools/_rpyc_tier2.py`（274 行）：`_DummyClass` stub +
`_RestrictedUnpickler` 白名单 unpickler + `_read_rpyc_data` slot
reader + `_safe_unpickle` + `_extract_text_from_node` AST walker +
`extract_strings_from_rpyc` 公共入口；从 `_rpyc_shared` 导入常量
（leaf-only，无循环）
468. `tools/rpyc_decompiler.py` 974 → 725 行：保留 Tier 1（game-python
helper template + `_render_decompile_helper` + `_run_decompile_with_
game_python`）/ Errors / 平台+版本检测 / 公共 API（`decompile_game`
/ `extract_strings_standalone`）/ CLI；末尾 re-export Tier 2 的 6
个符号 + `_rpyc_shared` 的 4 个常量让 `tests/test_rpyc_decompiler.py`
（18 测试 import 6 个 Tier 2 符号 + `_SHARED_WHITELIST` by 老名）+
`tools/renpy_lint_fixer.py`（import `_find_renpy_python`）完全不用
改
469. 零行为变化；18 rpyc 测试 + renpy_lint_fixer 依赖全保

**Commit 3：拆 `core/api_client.py` 965 → 642（-323）**

提取 custom plugin loader surface（`_load_custom_engine` legacy
importlib mode + `_SubprocessPluginClient` round-28 S-H-4 JSONL
subprocess sandbox）到新模块。剩下 APIClient 主类 + 5 provider
dispatch（xAI / OpenAI / DeepSeek / Claude / Gemini）+ APIConfig /
UsageStats / RateLimiter 继续留在主文件。

470. 新建 `core/api_plugin.py`（378 行）：`_CUSTOM_ENGINES_DIR`
常量 + `_load_custom_engine` 函数（签名 + 文件名 security check +
interface contract validation）+ `_SubprocessPluginClient` 完整类
（包括 r28 初始化 + r30 `atexit` 异常兜底 + stderr 10 KB 上限 +
`_SHUTDOWN_REQUEST_ID` + `close()` + `__del__` finaliser）
471. `core/api_client.py` 965 → 642 行：原 "Custom engine plugin
loader" section 替换为一行 import + 4-行 re-export block
（`_load_custom_engine`, `_SubprocessPluginClient`）让
`tests/test_custom_engine.py`（20 测试 import 2 符号 by 老名）
完全不用改
472. 零行为变化；20 custom-engine 测试全绿；APIClient.__init__
的 duck-typed plugin dispatch（`config.sandbox_plugin` 分支）
通过 re-export 名 lookup 保工作

**Commit 4：Docs sync**

473. 本文件（CHANGELOG_RECENT.md）：round 37 详细压缩进"演进摘要"
一行；38/39/40 保留详细
474. CLAUDE.md 项目身份段追加 r40 note + 测试数 396 保持（纯
refactor）；`.cursorrules` 同步
475. HANDOFF.md 重写为 40 → 41 交接；r40 三项拆分从"r40 候选"挪到
"✅ r40 已修"；保留 `gui.py` 815 行 + 其余 ~7 处内部 JSON loader +
A-H-3 Medium/Deep 等作 r41 候选；架构健康度表"大文件"维度更新为"全
源码 < 800 except gui.py 815（PyInstaller 打包耦合，r41 独立一轮）"

**结果**：
- 21 测试套件 + `tl_parser` 75 + `screen` 51 = **522 断言点**；测试
  **396 保持**（纯 refactor，byte-identical 拆分）
- 所有改动向后兼容：
  - rpyc_decompiler.py re-export Tier 2 符号 + shared 常量 → 老调用
    无感
  - api_client.py re-export `_load_custom_engine` +
    `_SubprocessPluginClient` → 老调用无感
  - test_engines.py 拆 rpgmaker → 新 suite 独立跑，总 test 数不变
- 新增文件 4 个：
  - `tools/_rpyc_shared.py`（47 行，leaf constants）
  - `tools/_rpyc_tier2.py`（274 行，safe-unpickle chain）
  - `core/api_plugin.py`（378 行，custom plugin loader + sandbox）
  - `tests/test_engines_rpgmaker.py`（315 行，15 rpgmaker 测试）
- 修改文件 3 代码 + 4 文档：
  - `tools/rpyc_decompiler.py` 974 → 725（-249）
  - `core/api_client.py` 965 → 642（-323）
  - `tests/test_engines.py` 962 → 694（-268）
  - CHANGELOG / CLAUDE / .cursorrules / HANDOFF
- 文件大小检查：源码 3/4 从 >800 降到 <800；`gui.py` 815 仍保持
  （r41 候选）。所有测试文件继续 < 800（r39 拆 test_translation_state
  的遗产）

**本轮未做**（留给第 41+ 轮）：
- **`gui.py` 815 行**（PyInstaller 打包耦合 + 单 `class App` 内部
  难以清晰分边界 + UI 代码自动化测试覆盖不到 → 建议 r41 独立一轮，
  配合 `build.py` 回归手动验证）
- 剩余 ~7 处内部 / 低风险 JSON loader size cap（`engines/generic_
  pipeline.py:151` / `core/translation_utils.py:138` / `translators/
  _screen_patch.py:311` / `tools/rpyc_decompiler.py:437` /
  `engines/rpgmaker_engine.py:85,396` / `pipeline/stages.py:212,378`
  / `gui.py:718`）
- 非中文目标语言的端到端验证（r39 per-language prompt 落地，需真实
  API + 真实游戏跑）
- A-H-3 Medium / Deep / S-H-4 Breaking — 需真实 API + 游戏验证
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants / quality_chain / roadmap 复查
  （连续 11 轮欠账）

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
