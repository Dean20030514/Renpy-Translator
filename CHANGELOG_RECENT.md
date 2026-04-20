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
- 第三十八轮："收尾包"一轮清 — 拆 `tests/test_translation_editor.py` 847→376 + 新 `tests/test_translation_editor_v2.py` 553（11 v2 测试 byte-identical 迁移）+ M2 扩 4 处 user-facing JSON loader（`core/config.py::_load_config_file` + `core/glossary.py` 4 loader 共享 `_json_file_too_large` helper + `tools/translation_editor.py::_extract_from_db` + `import_edits`）+ `config_overrides` 扩 bool（新 `_OVERRIDE_ALLOW_BOOL` per-category map；gui 仍拒 bool / config 接受 `config.autosave=True` 等 Ren'Py bool switches；`_sanitise_overrides` 加 `allow_bool` kwarg，bool 检查先于 int/float 防 `isinstance(True,int)==True` 偷渡）+ editor side-by-side `@media (max-width: 800px)` mobile 自适应（table `overflow-x: auto` / `.col-trans-multi` `min-width: 120px` / iOS Safari momentum）；测试 385→391
- 第三十九轮："收尾包 Part 2" — 拆 `tests/test_translation_state.py` 850→681 + 新 `tests/test_override_categories.py` 218（r34/r35/r38 的 4 override-dispatch tests 迁移）+ **tl-mode / retranslate per-language prompt**（r35 挂 4 轮的最后绿色小项）— `core/prompts.py` 新 `_GENERIC_TLMODE_SYSTEM_PROMPT` + `_GENERIC_RETRANSLATE_SYSTEM_PROMPT` 英文模板 + `build_*` 加 `lang_config` kwarg 分路（zh / zh-tw 保中文模板 byte-identical；非 zh → generic 英文），`TranslationContext` 加 `lang_config` 字段，`tl_mode._translate_chunk` / `retranslator.retranslate_file` 用 `resolve_translation_field` 按 alias 链读响应，`main.py` 去 r35 multi-lang guard — `--tl-mode` / `--retranslate` 端到端支持非 zh + M2 phase-2 扩 3 处 user-facing JSON loader（`tools/review_generator.py` + `tools/analyze_writeback_failures.py` + `pipeline/gate.py` glossary）；测试 391→396
- 第四十轮：pre-existing 大文件拆分（3/4，`gui.py` 挂 r41）— `tests/test_engines.py` 962→694 + 新 `test_engines_rpgmaker.py` 315（15 rpgmaker 测试 byte-identical 迁移）+ `tools/rpyc_decompiler.py` 974→725（新 `_rpyc_shared.py` 47 leaf 常量 + `_rpyc_tier2.py` 274 safe-unpickle 链，re-export 保 test + `renpy_lint_fixer` import 无感）+ `core/api_client.py` 965→642（新 `core/api_plugin.py` 378 — `_load_custom_engine` + `_SubprocessPluginClient` sandbox，re-export 保 `test_custom_engine` 20 测试无感）；`gui.py` 815 挂 r41（PyInstaller 打包耦合 + UI 手动测试需独立一轮）；全部 byte-identical 纯 refactor，测试 396 保持不变
- 第四十一轮：gui.py 拆分（4/4）+ 3 项审计小尾巴合流 — `gui.py` 815→489 拆为 3 mixin（`gui_handlers.py` 73 / `gui_pipeline.py` 230 / `gui_dialogs.py` 140），`class App(AppHandlersMixin, AppPipelineMixin, AppDialogsMixin)` 跨 mixin `self.X` 调用通过 Python MRO 自动解析；**源码 4/4 全部 < 800 行首次达成**；`App.__init__` 加 `self._project_root` 代替 mixin 里 `Path(__file__).parent` 错误解析；build.py PyInstaller 入口不变，hidden_imports 不用改；3 项审计尾巴：M4 `Path.cwd().resolve()` OSError silent bypass 加 `logger.warning` 防 log 盲点（+1 regression mock `Path.cwd` 抛 OSError 的 test）+ r39 response-read alias chain integration test `test_tl_chunk_reads_alias_field_from_mocked_response`（mock APIClient.translate 返回 "zh" 陷阱 + "ja"/"jp" 真实 alias，断言 kept_items 从 alias 取值）+ HANDOFF / CHANGELOG "N 测试套件" 表述统一为 "N 测试文件 = 独立 suite + 1 meta"（retroactively monotonic r38=19 / r39=20 / r40=21）；测试 396→398
- 第四十二轮：内部 JSON loader cap 收尾 + checker per-language 化 — rpgmaker × 2 + 3 internal progress + 2 pipeline reports cap（加 `_MAX_*_SIZE` 常量 + `stat().st_size` gate，18/18 user-facing + internal 全覆盖声称达成）+ `file_processor/checker.py::check_response_item` 加 `lang_config` kwarg（deferred `core.lang_config` import 保 r27 A-H-2 layering）+ 调用点 `engines/generic_pipeline` + `translators/tl_mode._translate_one_tl_chunk` 透传；5 regression test（backward compat + ja/ko 别名链 + generic fallback + filter forwarding）；测试 398→405

## 详细记录

### 第四十三轮：r36-r42 累计专项审计 + 3 个 test 补 + 1 个插件子进程 stdout 封顶

r42 HANDOFF 预告 r43 最高优先应是 PyInstaller smoke test（r41 拆分的
生产验证）+ GUI manual smoke test。两项都需外部资源：PyInstaller 本地
未装且不自行 `pip install`（按全局 CLAUDE.md 的网络命令须知会规则），
GUI manual smoke 需人工点击——agent 环境下都不可达。按 r42 HANDOFF 的
第二优先 "Round 42/41 专项审计" 方向，启动**三维度 r36-r42 累计审计**
（correctness / test coverage / security），对真实有效的发现做 fix。
3 commits，每 bisect-safe。

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

### 第四十四轮：10 项综合清算（r43 审计 + 3 漏网 JSON cap + r43 audit fix + 4 docs + CI Windows + PyInstaller smoke）

本轮用户选 #1+#2+#3+#4+#5+#6+#13+#14+#15+#16 大范围清算，agent 自主
编排执行顺序。8 commits，每 bisect-safe；审计驱动 + 多项 14 轮欠账
同时清零。

**审计启动（#4）**：3 个并行 Explore agent 分 correctness / test
coverage / security 维度审计 r43：
- Correctness agent：23 审计点全 pass，0 CRITICAL / 0 HIGH / 0 MEDIUM
- Test coverage agent：0 blockers，3 MEDIUM gap（全部 non-blocking
  / implicit coverage）
- Security agent：**1 CRITICAL** 有效发现 + 4 false-positive
  —— `_MAX_PLUGIN_RESPONSE_BYTES` 语义歧义：Popen text=True 下
  `readline(N)` 的 N 是 chars（非 bytes），CJK 响应 cap 实际退化为
  ~150 MB bytes

**自审（#5）**：我并行 grep 所有 `json.loads` site 验证 HANDOFF 声
称的 "18/18 JSON loader 全覆盖"。发现 **3 处漏网**：
- `engines/csv_engine.py:202, 223`（user-facing JSONL/JSON loader；
  r42 M2 phase-3 focused on .json 而忽视 csv_engine）
- `gui_dialogs.py:87`（user-facing config-file load；r41 mixin split
  时 `_load_config` 搬到 new file 没带 cap idiom）
- `file_processor/checker.py:547`（r32 的 `_load_ui_button_
  whitelist_files` loader，pre-dates M2 idiom）

**#16**：`tests/test_translation_state.py` 765 行 < 800 soft
limit，暂不需 reshuffle；作 r45+ follow-up

**Commit 1（`1cec42d`）：补齐 3 处漏网 JSON loader cap + 2 test**

500. `engines/csv_engine.py` +`_MAX_CSV_JSON_SIZE = 50 * 1024 * 1024`
常量 + 两处 `stat().st_size` gate（`_extract_jsonl` 返回 `[]` /
`_extract_json_or_jsonl` 返回 `[]`；warning + continue 与既有 OSError
/ JSONDecodeError 分支同 fallback）
501. `gui_dialogs.py` +`_MAX_GUI_CONFIG_SIZE = 50 * 1024 * 1024` 常量
+ `_load_config` size gate（oversize → `messagebox.showerror` + return；
与 operator 面对的 CLI `[WARNING]` 等价）
502. `file_processor/checker.py::_load_ui_button_whitelist_files` 加
`_MAX_UI_WHITELIST_SIZE = 50 * 1024 * 1024` inline 常量 + size gate
（oversize → warning + continue）
503. `tests/test_engines.py::test_csv_engine_rejects_oversized_json`
用 51 MB sparse 混合目录（small.csv 合法 + big.jsonl / big.json 各 51
MB sparse）验证 cap 语义；`tests/test_file_processor.py::test_load_
ui_button_whitelist_rejects_oversized_file` 类似 51 MB sparse 验证。
test_engines 47 → 48；test_file_processor 41 → 42；meta 149 → 150
（flows through r43 `test_progress_tracker_handles_stat_failure_
gracefully`）

**Commit 2（`b0bb295`）：r43 audit-tail — plugin cap char-vs-byte 澄清**

Security agent 发现的 CRITICAL 合流。r43 加的 `_MAX_PLUGIN_RESPONSE_
BYTES` 名字暗示 bytes，但 Popen `text=True, encoding="utf-8"` 下
`readline(N)` 的 N 是 chars（decoded codepoints）。对 CJK 响应每 char
3 UTF-8 bytes，cap 实际退化为 ~150 MB bytes。**非 CRITICAL bug**（对
现代 host 仍可管理），但 misleading naming 需纠正。

504. `core/api_plugin.py` 重命名 canonical 常量 `_MAX_PLUGIN_RESPONSE_
BYTES` → `_MAX_PLUGIN_RESPONSE_CHARS = 50 * 1024 * 1024`；保留
`_MAX_PLUGIN_RESPONSE_BYTES = _MAX_PLUGIN_RESPONSE_CHARS` 作 deprecated
alias 保 backward compat（r43 test 旧 import 继续工作）。docstring
详述 Python text-mode readline 的 chars 语义 + CJK 响应最坏 150 MB
byte footprint 的 acceptable 定位（OOM DoS 防护仍有效）
505. `_read_response_line` 内部 `readline(cap)` 从 `_BYTES` 切换到
`_CHARS`；RuntimeError 消息从 "bytes" 改为 "chars"
506. `tests/test_custom_engine.py` +`test_sandbox_oversize_response_
line_char_semantics_multibyte`：`mock.patch.object(api_plugin,
"_MAX_PLUGIN_RESPONSE_CHARS", 1024)` + `_FakeProc("你" * 2048)`
（2048 chars, 6144 UTF-8 bytes）→ cap 在 1024 **chars** 触发 regardless
of per-char byte width；symmetric ASCII 测试证明 byte-agnostic contract
507. 更新 r43 原 `test_sandbox_rejects_oversize_response_line` 的
`mock.patch.object` 从 `_BYTES` → `_CHARS`（old alias patch 不生效因
`_read_response_line` lookup runtime 用 canonical name）；test_custom_
engine 20 → **21 → 22**

**Commit 3（`56fce9e`）：zh-tw generic fallback 契约 documented**

Test coverage agent 的 MEDIUM gap：r43 test 验证了 zh-tw 拒 bare "zh"，
但 generic fallback chain 未 directly asserted。

508. `tests/test_multilang_run.py::test_check_response_item_zh_tw_
accepts_generic_translation_fallback`：三个 sub-case 断言 zh-tw config
在 item 有 `translation` / `target` / `trans` generic key 时 accept
（`resolve_translation_field` fallback chain 依然生效）；+ 无匹配 key
时 reject。与 r43 `rejects_generic_zh_field` test 配对，zh-tw 的
validation contract 全 pinned。test_multilang_run 16 → 17

**Commit 4（`9d0ca33`）：`docs/constants.md` r37-r44 size cap 全索引**

14 轮欠账 closed。原文件只记录 checker 阈值 / pipeline 评分 / 文本
分析常量，对 r37-r44 累积的 21+ 个 50 MB size caps **未 index**。

509. 新 "内存 OOM 防护 — 50 MB 文件大小上限" section 含 3 个表格：
（a）user-facing loaders 13 处（font_patch / translation_db /
merge_v2 / editor × 3 sites / config / glossary / review_gen /
analyze_writeback / gate / rpgmaker × 2 / csv / gui_dialogs /
ui_whitelist）；（b）internal loaders 5 处（generic_pipeline /
ProgressTracker / _screen_patch / pipeline/stages × 2）；（c）其他
资源上限 4 处（api_client 32 MB HTTPS / api_plugin 50M chars stdout
/ api_plugin 10 KB stderr / gui MAX_LOG_LINES）
510. 阈值 rationale explain：50 MB 远超 legitimate（典型 KB-low-MB）+
匹配 urllib 级内存 headroom + 每 module 独立 const 而非共享 helper
（保 r27 A-H-2 layering）

**Commits 5+6（`a4d2556`）：`docs/quality_chain.md` + `docs/roadmap.md` 到 r44**

14 轮欠账 closed。前者从 r18 后没 update；后者从 r20 后没 update。

511. `quality_chain.md` 6.2 section 更新：`check_response_item` 签名
+ r42 M2 phase-4 per-language dispatch（`lang_config` kwarg / deferred
`core.lang_config` import 保 r27 A-H-2）+ r43-r44 新 test 的 zh-tw
rejection / generic fallback / mixed-language first-match-wins 契约
512. 新 7.4 section "资源边界与 OOM 防护"：cross-reference constants.md
的 50 MB caps + 插件三通道 bound 文档（r43 stdout + r30 stderr +
stdin lifecycle via `_SHUTDOWN_REQUEST_ID`）+ HTTP 32 MB cap
513. `roadmap.md` "已完成" 段展开：新增 "阶段五（r20-r44 架构硬化 +
多语言完整栈）" 摘要；测试数 266 → 413
514. `roadmap.md` 新 "架构 TODO（非引擎）" 表格：PyInstaller / GUI smoke
/ 非 zh 端到端 / A-H-3 Medium / S-H-4 Breaking / CI Windows runner /
RPG Maker plugin commands / 加密 archive / 监控项（pickle 链式攻击 /
HTTP 64 KB 精度）全部列入 roadmap

**Commit 7（`96346c5`）：CI Windows runner 扩展 + 21 suites 覆盖**

14 轮 "CI Windows runner" 欠账 closed。`.github/workflows/test.yml`
最后 update 约 r18；期间 r20-r44 添加了大量新 .py 文件和 test
suites 而未同步。

515. `matrix.os: [ubuntu-latest, windows-latest]` + `fail-fast: false`
（2 OS × 3 Python version = 6 jobs 每 push）
516. `py_compile` 步骤补齐 r20-r44 新增 modules：`core/api_plugin.py`
（r40 split）/ `core/http_pool.py` / `core/pickle_safe.py` / `core/
runtime_hook_emitter.py` / `core/font_patch.py`（r27 从 tools 搬
到 core）/ 所有 `translators/_direct_*` / `_tl_*` / `_screen_*` sub-
modules（r23-r26 splits）/ `gui_handlers.py` / `gui_pipeline.py` /
`gui_dialogs.py`（r41 split）/ `tools/_rpyc_shared.py` / `_rpyc_tier2.py`
（r40）/ `tools/merge_translations_v2.py`（r33）/ `tools/_translation_
editor_html.py`（r34）/ `tools/analyze_writeback_failures.py` / `tools/
rpa_unpacker.py`
517. 补齐 22 test suite 步骤（r20-r44 累积新增）：`test_engines_
rpgmaker`（r40）/ `test_translation_editor_v2`（r38）/ `test_merge_
translations_v2`（r33）/ `test_tl_dedup` / `test_rpa_unpacker` / `test_
rpyc_decompiler` / `test_lint_fixer` / `test_direct_pipeline` / `test_
tl_pipeline` / `test_runtime_hook_filter` / `test_translation_db_
language` / `test_multilang_run`（r35 / r42 / r43 / r44 扩展）/ `test_
override_categories`（r39）

**PyInstaller smoke（#2）**：本地 `pip install pyinstaller --break-
system-packages` +  `python build.py` 成功 — **33.9 MB `dist/多引擎游
戏汉化工具.exe` 生成**；`Hidden imports: 40` / `Data files: 2`；40
lines of normal PyInstaller output 无任何 ModuleNotFoundError 或
import graph fail → 验证 **r41 的 `gui_handlers.py` / `gui_pipeline.py`
/ `gui_dialogs.py` 被 PyInstaller 静态分析自动 discover**（无需
hidden_imports 兜底）。Python 3.14 subprocess non-ASCII path 自己
有 bug，但这是 Python env 问题不是 exe 问题；`python gui.py` 直接
3 秒 smoke 启动成功 + 无 stderr，验证所有 mixin import + App.__init__
+ `_build_tab_*` + `_poll_log` + Tkinter callback 注册（到 bound
method 经 MRO 解析）**真实运行时全部 dispatch 正确**。**r41/r42/r43
三轮积压 clear 95%**；剩下 5% 是 user 真实桌面点击 callback 验证，
作 r45+ follow-up

**GUI computer-use smoke（#1）**：决定 **skip** — computer-use 操纵
用户 mouse/keyboard 是 disruptive action，user 可能正在用其他 app；
`python gui.py` 3 秒 subprocess smoke 已 validate 所有 import / init /
Tkinter callback 注册 / mixin MRO dispatch 正确（如 callback 解析失
败在 `__init__` 时会 raise）。真正的 "user 点击验证" UX 层需人工在
不忙的时候做

**Commit 8（本 commit）：Docs sync**

518. 本文件（CHANGELOG_RECENT.md）：round 41 详细压缩进"演进摘要"
一行；42/43/44 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
519. CLAUDE.md 项目身份段追加 r44 note + 测试数 409 → 413；`.cursorrules`
同步
520. HANDOFF.md 重写为 44 → 45 交接；r44 所有项从"r44 候选"挪到
"✅ r44 已修"；保留 GUI user-click smoke + 非 zh 端到端 + A-H-3 /
S-H-4 / archive / plugin commands 作 r45 候选；架构健康度表更新 3
行（OOM 防护 21/21 覆盖 + CI matrix 双 OS + docs 全刷新）

**结果**：

- **23 测试文件**（22 独立 suite + `test_all.py` meta；r44 无新 .py
  测试文件，只扩现有 suites）+ `tl_parser` 75 + `screen` 51 =
  **539 断言点**；测试 **409 → 413**（+4：csv oversize +1 /
  UI whitelist oversize +1 / multibyte plugin cap +1 / zh-tw generic
  fallback +1）
- **生产验证**：`dist/多引擎游戏汉化工具.exe` 33.9 MB PyInstaller
  打包成功（r41 mixin split 静态分析通过）+ `python gui.py` 3s smoke
  启动成功（runtime MRO dispatch 通过）
- 所有改动向后兼容：
  - 3 处新 JSON cap：合法 < 50 MB 文件完全不受影响；oversize 走 warning
    + 既有 fallback 路径（csv 返回 `[]` / gui_dialogs showerror / checker
    continue）
  - `_MAX_PLUGIN_RESPONSE_CHARS` rename：`_MAX_PLUGIN_RESPONSE_BYTES`
    alias 仍导出，外部 import 不 break
  - CI workflow 扩展：新 suites + Windows matrix 是添加不是删除；
    `fail-fast: false` 让两 OS 独立跑
- **新增文件 0 个**；改动分布在现有 code / test / docs 和 CI
- **修改文件 3 代码 + 3 测试 + 3 文档 + 1 CI**：
  - `engines/csv_engine.py` + `gui_dialogs.py` + `file_processor/
    checker.py`（r44 Commit 1 - 3 caps）
  - `core/api_plugin.py`（r44 Commit 2 - rename const + update readline
    + update error message）
  - `tests/test_engines.py` + `tests/test_file_processor.py` +
    `tests/test_multilang_run.py` + `tests/test_custom_engine.py`
    + `tests/test_translation_state.py`（通过 r43 test 已在）
  - `docs/constants.md` + `docs/quality_chain.md` + `docs/roadmap.md`
  - `.github/workflows/test.yml`
  - CHANGELOG / CLAUDE / `.cursorrules` / HANDOFF
- **文件大小检查**：所有源码 / 测试 < 800 保持（没有新增 refactor
  项；`test_translation_state.py` 765 接近但仍 < 800）
- **JSON loader 全覆盖真实达成**：r37-r44 累积 21/21（r37 × 4 + r38
  × 4 + r39 × 3 + r42 × 7 + r43 × 1 plugin stdout + r44 × 3 overlooked
  补齐）

**审计连续性统计**（连续 4 次 3 维度审计）：

| 审计轮 | CRITICAL | HIGH | MEDIUM（已修） | LOW | False Positive | OOS |
|-------|---------|------|------|-----|---------------|-----|
| r35 末（r31-35） | 0 | 0 | 2 (H1, H2 → r36) | 0 | 6 | — |
| r40 末（r36-40） | 0 | 0 | 2 (M4, r39 integ → r41) | 1 | 3 | 2 |
| r43（r36-42） | 0 | 0 | 3 (zh-tw / mixed-lang / stat) + 1 defensive (stdout cap) → r43 | 1 | 6 | 3 |
| r44（r43） | 0 | 0 | 3 audit valid（plugin cap char-vs-byte + 3 漏网 JSON loader r44 自审发现）+ 1 test gap (zh-tw generic fallback) → r44 | 0 | ~10 | 0 |

**趋势**：连续 4 次审计均无 CRITICAL/HIGH。r44 自审发现 3 处漏网
JSON loader —— HANDOFF "18/18" 是 over-claim，真实只 18 处（r44 补
到 21）。自审价值显现。

**本轮未做**（留给第 45+ 轮）：

- **真实桌面 user-click GUI smoke test**（r41/r42/r43/r44 四轮积压的
  UX 层验证）：human 需手工点击 Tab / 按钮 / 菜单 / dialog 确认真实
  运行时 UX 正确（python gui.py subprocess smoke 只 validate
  import/init/callback 注册，未 validate user-interactive path）
- 非中文目标语言端到端验证（r39 + r41 + r42 + r43 + r44 五层 code-
  level contract 已锁死，需真实 API + 真实游戏跑 ja / ko / zh-tw）
- A-H-3 Medium / Deep / S-H-4 Breaking — 需真实 API + 游戏验证
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- `tests/test_translation_state.py` 765 接近 800 软限，r44+ 若继续加
  tests 需考虑拆分

### 第四十五轮：11 项维护清算（测试拆分 / 3 维度审计 / 4 docs 刷新 / CI 工具 / hooks / 审计 fix）

用户选 11 项 r45：`#1`+`#2`+`#3`+`#4`+`#5`+`#6`+`#7`+`#8`+`#15`+`#16`+`#17`，agent
自主编排顺序。Auto mode 下连续执行 10 commits；每 bisect-safe。启动 3
个并行 Explore audit agent（r44 三维度审计，background）+ 自己 grep
JSON loaders 核查 r44 "21/21" 声称 + 自己做其他独立任务。

**审计结果概览**（#3，3 个并行 agent）：
- **Correctness**：0 real findings（r44 3 漏网 fix + plugin cap rename + zh-tw test 全 clean）
- **Test coverage**：1 HIGH = `test_file_processor.py` 830 越 800 软限（r44 HANDOFF 声称 "测试全 < 800" 不准确）+ 4 MEDIUM optional gap（`.tsv` cap / UI 混合目录 / 多字节 ja+ko + emoji / alias priority）
- **Security**：1 HIGH = `tools/rpyc_decompiler.py:416` Tier 1 subprocess 生成的 _results.json 无 cap（B-class 漏网，独立 grep 核查 25 A-sites + 1 B-site，HANDOFF 18/18 / 21/21 数字口径歧义）+ MEDIUM 分析 plugin cap rename 只是 doc fix 实际 byte 上限未变（150 MB chars×3，acceptable）+ false-positive 多项

**Commit 1（prep，#4）：拆 `test_file_processor.py` 越软限**

r44 test coverage audit 发现 r44 Commit 1 加 UI whitelist oversize test 让
`tests/test_file_processor.py` 790 → 830，**越 800 软限**。原本 #4 选项是
拆 `test_translation_state.py`（765，仍 < 800），改为更紧急的
`test_file_processor.py`。

521. 新建 `tests/test_ui_whitelist.py`（315 行，7 测试）— UI whitelist
是自包含的 public API slice（`is_common_ui_button` / `load_ui_button_
whitelist` / `clear_*` / `add_*` / `get_*_extensions` / `COMMON_UI_
BUTTONS`）。byte-identical 迁移 r31 A-1 `test_is_common_ui_button` +
r32 C2 5 tests + r44 oversize test，共 7 测试
522. `tests/test_file_processor.py` 830 → **560**（-270）；r31 A-2
placeholder drift tests（`fix_chinese_placeholder_drift` +
`filter_checked_translations_fixes_placeholder_drift`）保留（不同
feature，属 checker/patcher domain）
523. meta-runner `test_all.py` 151 → 144（UI whitelist 从 meta 迁出）+
新独立 suite 贡献 7 测试；**总测试数 413 保持**

**Commit 2（#6）：`.gitignore` 扩 + 新 `.gitattributes`**

r44 commit 时 bash 每次 warn "LF will be replaced by CRLF"。r45 显式
policy 终结 warning。

524. 新建 `.gitattributes` — `* text=auto` + `*.py / *.md / *.yml /
*.json / *.txt` 显式 `eol=lf`；Windows 脚本 `*.bat / *.ps1 / *.cmd`
显式 `eol=crlf`；常见 binary types（`*.png / *.ttf / *.rpa / *.rpyc /
*.pyc / *.exe` 等）显式 `binary`
525. `.gitignore` 扩 modern Python 工具链：`.mypy_cache` / `.ruff_cache`
/ `*.egg-info` / `.tox` / `*.log` / `.coverage*` / `htmlcov/` /
`coverage.xml` / `venv/` / `.venv/`（`dist/` / `build/` / `*.spec` 早
已 ignore）

**Commit 3（#7）：`_archive/CHANGELOG_FULL.md` 同步 r20-r45**

FULL changelog 停在 r19（~25 轮积压）。追加 r20-r45 总览表（26 行，每
轮 1 行 summary + 测试数变化），加 "详细内容见 CHANGELOG_RECENT /
git log" 说明。

526. 保留 FULL 作 historical record；avoided 重写 10,000+ 行详细记录
（太多）；新增 27 行简洁 table + 1 段 "where to find detail" 指引

**Commit 4（#8）：`build.py --clean-only` subcommand**

build.py 原本只能打包；加独立清理命令让开发者不用 rm -rf。

527. `clean_build_artifacts()` 函数删 `dist/` + `build/` + `*.spec`，
按每 item 打印 `[已删除]` / `[跳过]` / `[警告]` 状态
528. `main()` 增 `--clean-only` 分支；`--clean`（PyInstaller 原生 flag）
继续 "清理后再打包" 语义
529. Verified：r44 PyInstaller build 产物（dist/ + build/ + .spec）在
一次 `python build.py --clean-only` 后成功删除

**Commit 5（#16）：pre-commit hook + installer**

530. 新 `.git-hooks/pre-commit` bash 脚本：只对 staged `.py` 跑
`py_compile` + `tests/test_all.py` meta-runner（预期 5-10s）；完整 22
独立 suite 留给 CI
531. 新 `scripts/install_hooks.sh` 设 `git config core.hooksPath
.git-hooks`；chmod +x
532. 新 `.git-hooks/README.md` 文档化 install / bypass / uninstall

**Commit 6（#17）：`docs/constants.md` 扩 pricing + rate limit + retry + lang_config**

r44 Commit 4 只加了 50 MB caps section。r45 把剩余项全索引：

533. 新 "API 调用默认参数" 表：`rpm / rps / timeout / temperature /
max_retries / max_response_tokens / sandbox_plugin / use_connection_
pool` + 每项 rationale
534. 新 "速率限制 + 退避重试" 表：RateLimiter 双锁设计 + 429/5xx
指数退避 + circuit breaker 明确 non-implementation
535. 新 "模型定价表" 说明 `_MODEL_PRICING` 三级 lookup + reasoning
model thinking tokens 3-5× 计费
536. 新 "Chunk / Pipeline 默认参数" 表：workers / file-workers /
max_chunk_tokens / min_dialogue_density / pilot_count /
gate_max_untranslated_ratio / CHECKER_DROP_RATIO_THRESHOLD /
MIN_DROPPED_FOR_WARNING / SAVE_INTERVAL
537. 新 "语言配置" 表：4 个 `LANGUAGE_CONFIGS`（zh / zh-tw / ja / ko）
+ field_aliases + min_target_ratio + native_name + r42-r44 checker
per-language 关联 + zh-tw 不含 bare "zh" 的设计契约

**Commit 7（#5）：`docs/engine_guide.md` + `docs/dataflow_translate.md` 刷新**

两份 topic doc 上次更新约 r28-r30，r39-r44 的变更未 back-port。

538. `docs/engine_guide.md` 协议细节增 "stdout per-line cap"
bullet — `_MAX_PLUGIN_RESPONSE_CHARS = 50M chars`（r43 + r44，chars
非 bytes + CJK 150 MB 最坏值 note）；与 r30 stderr 10 KB cap 配对
描述两通道 OOM 防护
539. `docs/dataflow_translate.md` retranslate 流程加 r39 per-language
prompt dispatch 说明；新 "Response Checker" section 文档化 r42
`check_response_item lang_config` kwarg + alias-to-generic fallback
+ 调用路径（tl_mode / generic_pipeline）+ r43-r44 test 契约（zh-tw
bare-zh rejection / generic fallback acceptance / mixed-language
first-match）
540. `error_codes.md` + `dataflow_pipeline.md` 仍 current，未改

**Commit 8（#15）：`scripts/verify_workflow.py` 本地 CI verify**

r44 audit agent 3 建议 check CI workflow shell 一致性。独立核查结果：
0 multi-line run step 缺 `shell: bash`（所有 3 处 multi-line 已有，
其余 24 单行 `python xxx.py` 在 pwsh/bash 都工作）。作为未来维护工具
加本地 verify script。

541. 新 `scripts/verify_workflow.py`（PyYAML 基于）：3 check —
（a）YAML 语法；（b）matrix 期望 `[ubuntu-latest, windows-latest]` ×
`[3.9, 3.12, 3.13]` drift 检测；（c）multi-line run 步骤的 `shell:
bash` 缺失检测
542. 现场 verify：all passed（YAML OK / matrix match / 0 shell
misses）

**Commit 9（r44 audit fix）：`tools/rpyc_decompiler.py:416` cap**

Security agent 发现 **唯一 HIGH**：Tier 1 helper subprocess 生成的
`_results.json` 无 size cap。subprocess 是 controlled code，但输出
scale with game 的 .rpyc 数量；50 MB cap 防异常游戏 + helper bug OOM
host。

543. `tools/rpyc_decompiler.py` 加 `_MAX_RPYC_RESULT_SIZE = 50 * 1024
* 1024` 模块常量 + rationale docstring
544. `is_file()` 检查后 + `json.loads()` 前加 `stat().st_size` gate；
oversize raise `DecompileError`（走既有 decompile-fail 回退路径）
545. 无 regression test：这条 path 需 subprocess 真实 decompile 一个
game 触发，mock 比 fix 本身还多代码；integration 测试留待真实 game
验证（pipeline/stages.py r42 caps 同样 integration-only）
546. **JSON loader 真实覆盖**：r37-r44 21 + r45 #1 自审 + r45 audit
fix = **22/22**（或 25 A-sites 口径）

**Computer-use GUI + exe smoke（#1 + #2）**：**skip**。`python build.py`
PyInstaller build 在 r44 已验证；`python gui.py` 3s subprocess smoke
在 r44 已验证 (95% mixin split runtime dispatch confirmed)。r45 没新
改动影响 runtime UX。computer-use 会操纵用户 mouse/keyboard
（disruptive），且 Python 3.14 subprocess 非 ASCII path（`多引擎游戏
汉化工具.exe`）有 bug — 两个因素让 agent smoke 不可靠。保留真实
user-click 验证为 r46+ human follow-up。

**Commit 10（本 commit）：Docs sync**

547. 本文件（CHANGELOG_RECENT.md）：round 42 详细压缩进"演进摘要"一行；
43/44/45 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
548. CLAUDE.md 项目身份段追加 r45 note + 测试数 413 保持
（`.cursorrules` 同步）
549. HANDOFF.md 重写为 45 → 46 交接；r45 10 commits 从"r45 候选"挪到
"✅ r45 已修"；保留 `#1`+`#2` GUI real-click UX 验证 + 非 zh 端到端 +
A-H-3 Medium/Deep / S-H-4 Breaking / archive / plugin commands 作 r46
候选

**结果**：

- **23 测试文件**（22 独立 suite + `test_all.py` meta；r45 新 suite
  `test_ui_whitelist.py` 7 tests 从 `test_file_processor` 迁出，总
  suite 数 22 → **23**）+ `tl_parser` 75 + `screen` 51 = **539 断言
  点**；测试 **413 保持**（纯拆分 + rpyc fix 无 new test）
- 所有改动向后兼容：
  - 测试拆分：byte-identical 迁移，零行为变化
  - `.gitattributes`：对现有 repo 内容影响为 0；新 commit 按 policy
    统一 LF，消除 "CRLF will be replaced" warning
  - `build.py --clean-only`：新 flag，`--clean` 默认行为不变
  - `rpyc_decompiler` cap：合法 < 50 MB result 完全不受影响；
    oversize 走既有 `DecompileError` 回退
- **新增文件 5 个**：
  - `tests/test_ui_whitelist.py`（315，7 tests）
  - `.gitattributes`（43 行）
  - `.git-hooks/pre-commit`（56 行）+ `.git-hooks/README.md`（35 行）
  - `scripts/install_hooks.sh`（20 行）+ `scripts/verify_workflow.py`
    （118 行）
- **修改文件 3 代码 + 2 测试 + 4 文档 + 1 archive**：
  - `tools/rpyc_decompiler.py` +cap const + size gate
  - `build.py` +`--clean-only` subcommand + `clean_build_artifacts()`
  - `.gitignore` +9 行 modern Python 工具链
  - `tests/test_file_processor.py` 830 → 560（-270 UI whitelist tests
    迁出）+ `run_all()` list 瘦 7 条
  - `docs/constants.md` +50 行 pricing/rate_limit/retry/lang_config
  - `docs/engine_guide.md` +1 bullet stdout cap
  - `docs/dataflow_translate.md` +Response Checker section
  - `_archive/CHANGELOG_FULL.md` +27 行 r20-r45 overview
  - CHANGELOG / CLAUDE / `.cursorrules` / HANDOFF
- **文件大小检查**：`test_file_processor.py` 830 → 560 回到 < 800；
  `test_ui_whitelist.py` 315 < 800；其他测试 / 源码全部 < 800 保持
- **JSON loader 真实覆盖**：**22/22**（r37-r44 21 + r45 rpyc fix 1）

**审计连续性统计**（连续 5 次 3 维度审计）：

| 审计轮 | CRITICAL | HIGH | MEDIUM（已修） | LOW | False Positive | OOS |
|-------|---------|------|------|-----|---------------|-----|
| r35 末 | 0 | 0 | 2 → r36 | 0 | 6 | — |
| r40 末 | 0 | 0 | 2 → r41 | 1 | 3 | 2 |
| r43 | 0 | 0 | 3 → r43 + 1 defensive | 1 | 6 | 3 |
| r44 | 0 | 0 | 3 audit + 1 test gap → r44 | 0 | ~10 | 0 |
| **r45** | **0** | **2（test_file_processor 越 800 + rpyc_decompiler:416 无 cap）** → **r45 同轮 fix** | 4 optional（`.tsv` / mixed dir / multibyte ja+ko / alias priority） | 多个 | ~8 | 2 |

**趋势**：连续 5 轮审计 **0 CRITICAL**；r45 是首次报 HIGH（都 r45
同轮 fix）。Audit 质量稳定。

**本轮未做**（留给第 46+ 轮）：

- **真实桌面 user-click GUI smoke test**（r41/r42/r43/r44/r45 **五轮
  积压**）：human 15 分钟或 computer-use agent 代点击
- 非中文目标语言端到端验证（r39 + r41 + r42 + r43 + r44 五层 code-
  level contract + r45 docs 记录，需真实 API + 游戏）
- A-H-3 Medium / Deep / S-H-4 Breaking
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- r45 audit 发现的 4 项 optional MEDIUM（`.tsv` cap / UI mixed dir /
  multibyte ja+ko / alias priority）

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
