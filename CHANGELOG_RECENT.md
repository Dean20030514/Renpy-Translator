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

## 详细记录

### 第三十七轮：M 级防御加固包（M1+M2+M3+M4+M5）

r35 深度审计挂起的 5 项 Medium-level 防御加固，HANDOFF round 36→37
建议打包一轮。本轮按用户拍板的"M 级防御包"方向全做，纯 fix + 防御
加固、不加新功能。用户额外同意把 M2 范围从 HANDOFF 原列的 3 处扩到 4
处（含 `tools/translation_editor.py::_apply_v2_edits:445`，理由：该
函数读操作员控制的 v2_path，与 M4 路径白名单互补）。6 commits，每
commit bisect-safe。

**Commit 1：Fix M1 `TranslationDB.load()` backfill 覆盖 partial v2 文件**

`core/translation_db.py::load()` r34 的强制回填只在 `version <
SCHEMA_VERSION` 分支触发（即 v1 文件迁移 v2 时）。手编 v2 DB 或第
三方工具产出的 v2 文件若仍有部分 entry 缺 `language` 字段，永远
留在 None bucket；后续 `upsert_entry` 按 default_language 自动填新
entry → None bucket 与 zh bucket 并存，duplicate-bucket 漂移。

411. `core/translation_db.py::load()` 去掉 `version < SCHEMA_VERSION`
gate：只要 `default_language` 非空且有 entry 缺 `language` 字段就
backfill。新增 `any_backfilled` 局部 flag 精准控制 `_dirty` 只在
实际有回填时标记（避免 already-complete v2 文件被误标 dirty）
412. `tests/test_translation_db_language.py` +1 `test_load_backfills_
v2_entries_missing_language`（~40 行）：handcraft v2 DB 混合 "有
language" + "缺 language" 条目，断言两者最终都标 zh；control 组
`default_language=None` 保持原样不回填。`run_all()` 注册 meta→11

**Commit 2：Fix M2 JSON loader 50 MB size cap（4 处站点）**

4 处用户面向的 JSON 读取路径先全读 file → `json.loads`，对 attacker
crafted 或误供巨型文件会 OOM 进程。每处加 module-level 50 MB 常量
 + 读前 `path.stat().st_size` 检查：

413. `core/font_patch.py::load_font_config` 加 `_MAX_FONT_CONFIG_SIZE
= 50 * 1024 * 1024`；oversize → warning + return `{}`
414. `core/translation_db.py::TranslationDB._MAX_DB_FILE_SIZE = 50MB`；
oversize → warning + entries/index/dirty 全清 + 保 on-disk 不覆盖
（镜像现有 "corrupt file" 分支语义，让 operator 能人工恢复）
415. `tools/merge_translations_v2.py::_MAX_V2_ENVELOPE_SIZE = 50MB`；
oversize → raise `MergeError` → CLI 传播 exit=1
416. `tools/translation_editor.py::_MAX_V2_APPLY_SIZE = 50MB`（M4 白
名单后第二层防御：即使 CWD-rooted 路径过大也拒）；oversize → warning
+ skip 该 path 下所有 edits
417. `tests/test_runtime_hook_filter.py` +2（font_patch + _apply_v2_
edits，scope 扩到 "safety / filter overflow"，文件头 docstring 同步）
418. `tests/test_translation_db_language.py` +1（db load）；
`tests/test_merge_translations_v2.py` +1（merge cli + library 双断
言）。共 4 新测试，全用 51 MB sparse file（`f.seek(51<<20-1); f.write
(b'\\0')`）—— OS-dep 磁盘分配，但 stat() 报全尺寸，size gate 触发
在 read 前，测试在 NTFS / ext4 均能工作

**Commit 3：Fix M3 `main.py` 外循环末尾 args 状态恢复**

r35 的 multi-lang 外循环（`main.py:342`）每 iteration 改 `args.target_
lang` + `args.lang_config`，循环结束残留最后一个 language。当前无 post-
loop reader，但未来加 reporting / integration test 会踩。

419. `main.py:342-353` 外循环前 `_saved_target_lang / _saved_lang_config
= args.*`；try/finally 包 for 循环，finally 内 restore。~12 行。
保留循环体完全不变。无新测试：`main()` 带 mocked engine 的 plumbing
成本 > 6 行 save/restore 的可读性收益，per "最小改动" skip

**Commit 4：Fix M4 `_apply_v2_edits::v2_path` CWD 路径白名单**

`tools/translation_editor.py::_apply_v2_edits` 读 edit dict 的
`v2_path` 后直接 open + write。不可信 edits.json（钓鱼下载 / 其他
workspace 的旧文件）能把 v2_path 指向 `/etc/passwd` 或
`C:\Windows\System32\...`，只要目标碰巧 parse 成 v2 envelope 就被覆
盖。威胁模型 LOW-MEDIUM（r36 审计核实）但加一层防御足够便宜。

420. `_apply_v2_edits` 函数顶部算 `trust_root = Path.cwd().resolve()`；
for-loop 遍历 edit 时 `Path(v2_path).resolve().relative_to(trust_root)`
失败（`ValueError`）→ warning + skip 该 edit。非 raise 因单个 bad edit
不应 abort 整批 import。docstring 同步加两条 skip 原因（M2 size / M4
whitelist）
421. `tests/test_translation_editor.py` +1 `test_apply_v2_edits_
rejects_path_outside_cwd`（~35 行）：混合 batch（CWD-rooted + 系统
tempdir），断言 outside 被 skip + 文件字节不变 + CWD-rooted 合法
edit 仍 apply
422. 3 个 pre-existing v2-apply 测试 (`test_import_to_v2_envelope` /
`test_export_edits_multi_language_produces_per_lang_records` /
`test_v2_envelope_preserves_non_edited_languages`) 用 `tempfile.
TemporaryDirectory()` 默认 OS-tempdir（POSIX `/tmp` / Windows
`%LOCALAPPDATA%\\Temp`），M4 白名单会拒。改为 `tempfile.TemporaryDirectory
(dir=str(Path.cwd()))` 让它们 CWD-rooted。零测试语义改变，只是
选址调整

**Commit 5：Fix M5 空字符串 cell 语义文档化 + side-by-side UI tooltip**

side-by-side 编辑中 operator 清空某 cell → `exportEdits()` 产出
`new_translation: ""`；Python 侧 `_apply_v2_edits` 现有 `not new_trans.
strip()` guard silently skip。semantic 其实是 intentional（防止空白
删字导致意外 destructive），但未文档化，operator 看不出来。

423. `_apply_v2_edits` docstring +1 段：明确 empty-string = SKIP 非
DELETE；要删 bucket 请直接编辑 v2 JSON；side-by-side toolbar 有
tooltip 提示
424. `tools/_translation_editor_html.py` side-by-side label 加
`title="Empty cells are skipped on import (not treated as a delete).
To remove a translation bucket, edit the v2 JSON file directly."`。
1 行 attribute 追加
425. `tests/test_translation_editor.py` +1 `test_side_by_side_label_
has_empty_string_hint_tooltip`（~15 行）：直接 assert `HTML_TEMPLATE`
常量含 `title="Empty cells are skipped` + "edit the v2 JSON file
directly"。不需 tempdir / export roundtrip

**Commit 6：Docs sync**

426. 本文件（CHANGELOG_RECENT.md）：round 34 详细压缩进"演进摘要"
一行；35/36/37 保留详细
427. CLAUDE.md 项目身份段追加 r37 M1-M5 note + 测试数 378 → 385；
`.cursorrules` 同步（字节相同）
428. HANDOFF.md 重写为 37 → 38 交接；M1-M5 从"r37 候选"挪到"✅ r37
已修"；保留 pre-existing 4 大文件 + r35 绿色小项 + r37 其他 JSON
loader（未在 M2 四处内的）作 r38 候选；架构健康度表"防御加固"
状态更新

**结果**：
- 18 测试套件 + `tl_parser` 75 + `screen` 51 内建自测全绿；测试 **378 → 385**
  （+1 M1 + 4 M2 + 0 M3 + 1 M4 + 1 M5 = +7）
- 所有改动向后兼容：
  - M1：已完整填 language 的 v2 文件完全不受影响（`any_backfilled`
    flag 只在实际回填时标 dirty）
  - M2：合法大小文件（< 50 MB）完全不受影响
  - M3：`main()` 调用方无变化，外部 API byte-identical
  - M4：CWD-rooted 的 v2_path 完全不受影响（production 场景下 v2
    envelope 本来就在 `<project>/output/` 下运行）
  - M5：纯文档 + tooltip 追加，无行为改变（empty-string skip 语义
    从 r33 就在）
- 新增文件 0 个；修改文件 5 代码 + 2 测试 + 4 文档：
  - `core/translation_db.py` 305 → 332（+M1 +M2）
  - `core/font_patch.py` 161 → 185（+M2）
  - `tools/merge_translations_v2.py` 284 → 301（+M2）
  - `tools/translation_editor.py` 620 → 677（+M2 +M4 +M5 docstring）
  - `main.py` 358 → 370（+M3）
  - `tools/_translation_editor_html.py` label title（+~100 chars）
  - `tests/test_translation_db_language.py` 307 → 374
  - `tests/test_merge_translations_v2.py` 294 → 325
  - `tests/test_runtime_hook_filter.py` 146 → 211
  - `tests/test_translation_editor.py` 751 → 847（越 800 软限 47 行，
    r38 建议拆分 — 标注在 HANDOFF 未做列表）
  - CHANGELOG / CLAUDE / .cursorrules / HANDOFF
- 文件大小检查：`tests/test_translation_editor.py` 847 行已越 800 软
  限（r37 加 M4 + M5 测试 + 3 处 tempdir dir=cwd 调整共 96 行净增导致），
  建议 r38 拆分（参 r33 `test_runtime_hook.py` 拆分 precedent）。源码
  全部 < 800

**本轮未做**（留给第 38+ 轮）：
- `tests/test_translation_editor.py` 810 行越 800 软限，拆分（建议 r38）
- Pre-existing 4 个源文件 > 800 行（`tools/rpyc_decompiler.py` 974 /
  `core/api_client.py` 965 / `tests/test_engines.py` 962 / `gui.py` 815）
- 其他 JSON loader（M2 未覆盖的站点：`core/config.py:105` /
  `core/glossary.py:119,139,211,231` / `pipeline/stages.py:212,378` /
  `pipeline/gate.py:116` / `engines/rpgmaker_engine.py:85,396` / 等共
  ~10 处）的 size cap 扩展
- r35 原候选的 3 项绿色小项：tl-mode / retranslate per-lang prompt /
  `config_overrides` 值类型扩 bool / editor side-by-side mobile 自适应
- A-H-3 Medium / Deep / S-H-4 Breaking — 需真实 API + 游戏验证
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants / quality_chain / roadmap 复查
  （连续 8 轮欠账）

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

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
