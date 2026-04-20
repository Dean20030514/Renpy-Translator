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

## 详细记录

### 第四十一轮：gui.py 拆分（4/4）+ 3 项审计小尾巴合流

HANDOFF round 40→41 主推方向：r40 完成 3/4 pre-existing 大文件拆分
（`test_engines.py` / `rpyc_decompiler.py` / `api_client.py`），剩
`gui.py` 815 行因 PyInstaller 打包耦合 + 单 `class App` 边界不清 +
UI 手动测试需求独立挂到 r41。同时合流 r40 末专项审计识别的 3 项
MEDIUM/LOW 尾巴（用户已拍板）。7 commits，每 bisect-safe。

**Commit 1（prep）：抽 `gui_handlers.py`（3 方法 ~73 行，最小风险试水）**

3 个纯 UI event handler（无 subprocess / 无日志）。风险最低，先做
验证 mixin 模式 + Tkinter bound-method 在 MRO 查找下的行为。

476. 新建 `gui_handlers.py`（73 行）：`AppHandlersMixin` 含
`_on_engine_change` / `_on_renpy_mode_change` / `_on_provider_change`。
方法体 byte-identical 从 `class App` 剪切。`_PROVIDER_DEFAULTS`（7 行）
复制副本防 import cycle（gui.py load 时 import gui_handlers 时反向引用
gui 会半初始化）
477. `gui.py`：新增 `from gui_handlers import AppHandlersMixin`，改
`class App:` → `class App(AppHandlersMixin):`，删除 3 方法（line
246-276）。MRO 验证：`['App', 'AppHandlersMixin', 'object']`
478. `gui.py` 815 → 785（-30）。148 meta-runner tests 保持 pass

**Commit 2：抽 `gui_pipeline.py`（9 方法 + 3 常量 ~230 行）**

9 个方法围绕 subprocess 启动 + 日志队列 + 进度条 + 完成回调。
`_on_finished` 归 pipeline（非 handlers），因语义上是 subprocess
completion 直接 callback，被 `_poll_log` 调用，管理 pipeline-specific
state（`process` / `progress_bar` / `lbl_progress`）。

479. 新建 `gui_pipeline.py`（230 行）：`AppPipelineMixin` 含 `_start`
/ `_run_command` / `_parse_progress` / `_append_log` / `_on_finished`
/ `_stop` / `_clear_log` / `_run_dry_run` / `_poll_log`。常量
`_RE_PROGRESS` / `MAX_LOG_LINES` / `TRIM_TO` move 过来
480. `gui.py::App.__init__` 加 `self._project_root = PROJECT_ROOT`
（pipeline mixin 用 `self._project_root` 代替原 `PROJECT_ROOT` 引用 —
若 mixin 里直接 `Path(__file__).parent` 会指向 gui_pipeline.py 所在
目录，subprocess cwd 就错了；通过 self 把 canonical PROJECT_ROOT 带
进 mixin 是最干净的解耦）
481. 清理 `gui.py` unused imports：`os` / `re` / `threading` / `time`
（4 个顶层 import 被搬走后不再使用）
482. `gui.py` 785 → 601（-184）。148 tests pass。MRO:
`['App', 'AppHandlersMixin', 'AppPipelineMixin', 'object']`

**Commit 3：抽 `gui_dialogs.py`（5 方法 ~140 行）**

5 方法围绕 filedialog / messagebox / 配置 I/O / 工具菜单。跨 mixin
调用（`_run_upgrade_scan_on_game_dir` worker 里 `self._append_log`
/ `self._log_queue` / `self.btn_start`）通过 MRO 自动解析 —
`class App(AppHandlersMixin, AppPipelineMixin, AppDialogsMixin)` 让
dialog 方法能看到 pipeline state。

483. 新建 `gui_dialogs.py`（140 行）：`AppDialogsMixin` 含
`_run_upgrade_scan` / `_run_upgrade_scan_on_game_dir` / `_load_config`
/ `_save_config` / `_browse_dir`。`from tools.renpy_upgrade_tool
import run_scan` 保持为 worker 内 lazy import（原语义未变）
484. `gui.py`：新增 `from gui_dialogs import AppDialogsMixin`，扩继
承链为 `class App(AppHandlersMixin, AppPipelineMixin, AppDialogsMixin):`，
删除 5 方法
485. 清理 `gui.py` unused imports：`filedialog` / `json` / `messagebox`
486. `gui.py` 601 → 489（-112）。**源码 4/4 全部 < 800 达成**：
`gui.py` 489 / `gui_handlers.py` 73 / `gui_pipeline.py` 230 /
`gui_dialogs.py` 140。148 tests 继续 pass

**Commit 4：M4 OSError warning log（审计尾巴 1/3）**

r37 M4 引入的 `except OSError: trust_root = None` 让 CWD 白名单
静默失效（e.g. cwd 并发删除 / 权限问题 / fs 调用失败），operator
无任何 log 感知。attack surface 极小（操作员通常在项目根运行）但
silent bypass 无 log 是语义缺陷。

487. `tools/translation_editor.py:498-509` 加 `logger.warning(
"[V2-EDIT] Path.cwd().resolve() failed — CWD whitelist disabled, edits
outside the project tree will NOT be rejected")` 在 `except OSError:`
分支。零行为变化（仅加 log 不改 fallback 路径）
488. `tests/test_translation_editor_v2.py` +1 `test_apply_v2_edits_
warns_when_cwd_resolve_fails`：monkey-patch `pathlib.Path.cwd` 抛
OSError，用临时 `logging.Handler` 捕获 logger output 断言 warning
被 emit；try/finally 恢复 `Path.cwd` 防污染后续测试。测试 12 → 13

**Commit 5：r39 integration test（审计尾巴 2/3）**

r39 的 `test_tl_system_prompt_per_language_branch` 只验证 prompt
**生成**按 `lang_config` 分路；但响应读取点（`_translate_one_tl_chunk`
/ `retranslate_file` 里 `ctx.lang_config → resolve_translation_field`
alias chain）没有端到端断言。当前仅靠 "prompt-branch test + r11 alias
unit test" 间接拼接。

489. `tests/test_multilang_run.py` +1 `test_tl_chunk_reads_alias_
field_from_mocked_response`：mock APIClient.translate 返回同时带
`"zh"` 陷阱值 + `"ja"`/`"jp"` 真实 alias 的条目，调用
`_translate_one_tl_chunk` with `ctx.lang_config = get_language_config
("ja")`，断言 `kept_items` 从 ja/jp 取值而非 zh 陷阱值（若 r39 分派
回归到 legacy `t.get("zh","")` path，测试会捕获 "zh-honeypot-*"）
490. Test 同时对 file_processor.checker 的局限性（`check_response_
item` 只看 "zh" 字段）形成文档化约束 — 为未来 checker 的 per-language
扩展留下契约证据。测试 8 → 9

**Commit 6：Suite count doc drift 统一（审计尾巴 3/3）**

r40 末审计识别 HANDOFF 与 CHANGELOG 交替用 "19 / 20 / 21 测试套件"
文字，口径不一致。

491. 统一规则：**测试文件数 = 独立 suite 数 + 1**（`test_all.py`
meta-runner 聚合 6 个聚焦 suite 作内部使用）。按此 retroactively 校
准三轮 monotonic 递增：r38=19 / r39=20 / r40=21
492. 修正两处 drift：HANDOFF line 171 的 "20 测试套件"（r40 末健康度
表）→ "21 测试文件"；CHANGELOG r39 line 308 的 "19 测试套件"
→ "20 测试文件"。r38 / r40 原表述正确，未改
493. HANDOFF 末尾 summary section 加"统一口径"澄清注释

**Commit 7：Docs sync**

494. 本文件（CHANGELOG_RECENT.md）：round 38 详细压缩进"演进摘要"
一行；39/40/41 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
495. CLAUDE.md 项目身份段追加 r41 note + 测试数 396 → 398；
`.cursorrules` 同步（字节相同）
496. HANDOFF.md 重写为 41 → 42 交接；r41 gui.py 拆分 + 3 项审计
小尾巴从"r41 候选"挪到"✅ r41 已修"；架构健康度表"大文件"维度
更新为"**源码 4/4 清零**"；r42 候选：~7 处内部 JSON loader size cap
+ 非 zh 端到端验证 + A-H-3 Medium/Deep + S-H-4 Breaking + CI/docs 复查

**结果**：

- **22 测试文件**（21 独立 suite + `test_all.py` meta）+ `tl_parser`
  75 + `screen` 51 = **524 断言点**；测试 **396 → 398**（+2：M4
  OSError log regression + r39 response-side alias integration；拆分
  3 commits 纯 byte-identical 未改测试数）
- 所有改动向后兼容：
  - **mixin 继承模式**保 `self.X` 访问 / MRO 跨 mixin 自动解析 /
    Tkinter bound-method callback 正确工作（`command=self._start`
    在 `__init__` 时解析为 bound method，Python MRO 保证调用到
    `AppPipelineMixin._start`）
  - **PyInstaller 打包**不受影响：`build.py` 入口仍是 `gui.py`，
    同目录 `from gui_handlers import ...` / `from gui_pipeline
    import ...` / `from gui_dialogs import ...` 由 PyInstaller 静态
    分析自动 discover；`hidden_imports` 列表不用改
  - **_on_finished 归属 pipeline**：与 plan 初议"归 handlers"不同，
    最终按语义正确性（subprocess completion callback）归 pipeline；
    不影响任何外部 caller
- **新增文件 3 个**：
  - `gui_handlers.py`（73 行：3 方法 + `_PROVIDER_DEFAULTS` 副本 + docstring）
  - `gui_pipeline.py`（230 行：9 方法 + 3 常量 + docstring）
  - `gui_dialogs.py`（140 行：5 方法 + docstring）
- **修改文件 2 代码 + 2 测试 + 4 文档**：
  - `gui.py` **815 → 489**（-326，拆分 3 mixin + 删 4 unused import +
    `__init__` 加 `self._project_root`）
  - `tools/translation_editor.py` ~650 → ~660（+M4 OSError warning log）
  - `tests/test_translation_editor_v2.py` 574 → 633（+1 test ~57 行）
  - `tests/test_multilang_run.py` 155 → 230（+1 test ~75 行）
  - CHANGELOG / CLAUDE / `.cursorrules` / HANDOFF
- **文件大小检查**：源码 **4/4 全部 < 800**（r41 首次达成；r10 前
  `gui.py` 就是 800+ 级大文件，r41 拆完彻底清零）：
  - `gui.py` 489 ✓（r40 815）
  - `gui_handlers.py` 73 ✓
  - `gui_pipeline.py` 230 ✓
  - `gui_dialogs.py` 140 ✓
  - 所有其他源码 / 测试 均 < 800

**本轮未做**（留给第 42+ 轮）：

- **PyInstaller 打包端到端验证**：r41 拆分理论上 PyInstaller 自动
  discover 同目录 `.py`，但未在 r41 本地实跑 `python build.py`
  verify（PyInstaller 可能未安装）。若 follow-up 跑包失败，兜底方案：
  在 `build.py::hidden_imports` 追加 `"gui_handlers", "gui_pipeline",
  "gui_dialogs"` 三行即可
- **GUI 手动 smoke test 全面验证**：r41 每 commit 后仅做 import 测试
  + 148 meta tests；生产环境需人工点击 Tab / 按钮 / 菜单 / 配置保存
  加载 / Dry-run / 升级扫描 等全面验证，确认 Tkinter callback + mixin
  MRO 在真实运行时全部正确
- 剩余 ~7 处内部 / 低风险 JSON loader size cap（`engines/generic_
  pipeline.py:151` / `core/translation_utils.py:138` / `translators/
  _screen_patch.py:311` / `tools/rpyc_decompiler.py:437` / `engines/
  rpgmaker_engine.py:85,396` / `pipeline/stages.py:212,378` /
  `gui.py:718` — r41 拆分后 gui.py 里已无此 line，但 gui_dialogs 里
  可能对应）
- 非中文目标语言端到端验证（r39 per-language prompt 落地 + r41
  integration test 锁死 code-level contract，但需真实 API + 真实游戏
  跑 ja / ko / zh-tw）
- A-H-3 Medium / Deep / S-H-4 Breaking — 需真实 API + 游戏验证
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants / quality_chain / roadmap 复查
  （连续 12 轮欠账）

### 第四十二轮：内部 JSON loader cap 收尾 + checker per-language 化

HANDOFF round 41→42 调整方向：r42 主推的 PyInstaller smoke test 因本地未
装 PyInstaller 且不自行 `pip install`、GUI manual smoke 因 agent 环境无
人工点击能力，两项都挂起为 human follow-up；按 HANDOFF 备选短平快做
两项：**剩余 7 处内部 JSON loader 50 MB size cap 补齐**（r37-r39 M2 续作
phase-3）+ **`file_processor/checker.py::check_response_item` per-language
化**（解锁 r41 audit test 文档化的"checker 只认 zh"约束 + 与 r41
alias-chain integration test 端到端闭环）。5 commits，每 bisect-safe。

**Commit 1：RPG Maker JSON readers cap（user-facing，P1）**

`engines/rpgmaker_engine.py` 两处 JSON loader（`extract_texts` line 85
读每个 MapXXX / System / CommonEvents / Troops 数据，writeback 路径
line 396 读回写前原文）都是 operator 控制的 `game_dir` 入口。合法 RPG
Maker MV/MZ 数据文件在 KB-low-MB 范围；50 MB+ 几乎必然 malformed 或
adversarial。

477. `engines/rpgmaker_engine.py` 加 `_MAX_RPGM_JSON_SIZE = 50 * 1024 *
1024` 常量；两处 `json.loads` 前加 `path.stat().st_size > cap` 检查，
oversize → warning + continue（与既有 OSError / JSONDecodeError 分支同
fallback）
478. `tests/test_engines_rpgmaker.py` +1 regression `test_rpgm_extract_
rejects_oversized_json`，51 MB sparse file 触发 cap，断言 extract_texts
返回无此文件的 unit。15 → 16 tests

**Commit 2：3 处 internal progress loaders cap（P2）**

三处内部 progress 文件 loader 在 r41 末仍无 cap：

- `engines/generic_pipeline.py::_load_progress` line 151（generic
  pipeline progress）
- `core/translation_utils.py::ProgressTracker._load` line 145（主
  progress.json）
- `translators/_screen_patch.py::_load_progress` line 311（screen
  translator progress）

合法 progress 文件大小按 chunk 数线性扩展，typical 几 KB 到几百 KB；
50 MB+ 视为 corrupt / 非 progress 文件意外指到 --resume-file。

479. 三文件各加 `_MAX_PROGRESS_JSON_SIZE = 50 * 1024 * 1024` 模块常量
（各自独立，与 r37-r41 user-facing loader 一致的 per-module 模式）；
每处 loader 加 size gate，oversize → warning + 重置为空 progress（与既
有 JSONDecodeError 分支同 fallback）
480. `tests/test_translation_state.py` +1 `test_progress_tracker_
rejects_oversized_file`。meta-runner `test_all.py` 148 → 149

**Commit 3：pipeline/stages.py 2 处 internal report loaders cap（P3）**

`pipeline/stages.py` 读两个 stage-generated 报告 feeds final summary：

- `tl_mode_report.json` line 212
- `report.json` line 378

两处都已有 try/except 包围 normal-path fallback。

481. `pipeline/stages.py` 加 `_MAX_REPORT_JSON_SIZE = 50 * 1024 * 1024`
模块常量；两处加 size gate。`tl_mode_report` oversize → 复用既有
`{"error": ...}` 分支；`full report` oversize → raise ValueError 落到
既有广捕 `except (OSError, JSONDecodeError, KeyError, ValueError)` 降
级分支
482. 无新 test：两处 loader 在 run_pipeline / run_full 大流程内部调用，
难以 isolated unit-test（r39 `pipeline/gate.py` glossary cap 同样处
理）。Import smoke 验证

**Commit 4：`check_response_item` per-language 化 + 5 测试**

r41 audit test 文档化 checker 硬编码 `item.get("zh")` on line 298 导致
tl-mode 必须在 checker 之后 alias-chain re-resolve（r39 workaround）；
本轮把 per-language awareness 推进 checker 本身，r39 workaround 变成
整洁路径。

483. `file_processor/checker.py::check_response_item` 加 `lang_config:
"object | None" = None` kwarg（用 `object` forward-ref 避免 module load
时 import core 破坏 r27 A-H-2 layering）。Body 分路：`if lang_config is
not None:` deferred `from core.lang_config import resolve_translation_
field` + `zh = (resolve_translation_field(item, lang_config) or "").
strip()`；`else` 保 r41 `zh = item.get("zh", "").strip()` byte-identical
484. `file_processor/checker.py::_filter_checked_translations` 加同样
kwarg 透传给 `check_response_item`
485. `engines/generic_pipeline.py:356` 调用点传 `lang_config=lang_config`
（该变量在 line 204 已存在，来自 `get_language_config(target_lang)`）
486. `translators/tl_mode.py::_translate_one_tl_chunk` 调用点传
`lang_config=ctx.lang_config`。注意 checker 之后的 `zh = _resolve_field
(t, ctx.lang_config) or ""` post-checker resolve 保留 — 它与 checker 职
责不同（读取 vs 校验）
487. `tests/test_multilang_run.py` +5 regression 全覆盖 per-language
分路：（1）`test_check_response_item_lang_config_none_backward_compat`
无 lang_config 时仍用 "zh"；（2）ja lang_config 接受 `"ja"` / `"japanese"`
/ `"jp"` alias 链、拒绝 zh-only；（3）ko lang_config 接受 ko 别名链；
（4）fallback 到 generic `"translation"` / `"target"` / `"trans"` 字段；
（5）`_filter_checked_translations` 透传 lang_config 到 checker。9 →
14 tests

**Commit 5：Docs sync**

488. 本文件（CHANGELOG_RECENT.md）：round 39 详细压缩进"演进摘要"一行；
40/41/42 保留详细；维护规则继续"最近 3 轮详细 + 更老压缩"
489. CLAUDE.md 项目身份段追加 r42 note + 测试数 398 → 405；`.cursorrules`
同步（字节相同）
490. HANDOFF.md 重写为 42 → 43 交接；r42 两项从"r42 候选"挪到"✅ r42
已修"；保留 PyInstaller smoke test / GUI manual smoke test / 非 zh 端
到端验证 / A-H-3 / S-H-4 / CI / docs 作 r43 候选。Internal JSON loader
size cap 覆盖率：11 / 16 (r37-r39) → 18 / 18（r42 收尾）

**结果**：

- **22 测试文件**（21 独立 suite + `test_all.py` meta；r42 无新 .py）
  + `tl_parser` 75 + `screen` 51 = **531 断言点**；测试 **398 → 405**
  （+7：rpgm oversize +1 / progress tracker oversize +1 / pipeline/stages
   +0 / checker per-language +5）
- 所有改动向后兼容：
  - JSON cap：合法 < 50 MB 文件完全不受影响；oversize 走 warning + 既
    有 fallback 路径（reset / continue / raise → 集成 try/except）
  - `check_response_item` / `_filter_checked_translations` 新 kwarg 默
    认 `None`，保 r41 byte-identical 行为；非 None 时按 alias 链解析
  - 新 `core.lang_config` import 是 deferred（仅 `if lang_config is not
    None:` 分支触发），不破坏 r27 A-H-2 core → file_processor 单向层次
- **新增文件 0 个**；测试分布在现有 suite
- **修改文件 6 代码 + 3 测试 + 4 文档**：
  - `engines/rpgmaker_engine.py` +cap 常量 + 2 处 size gate
  - `engines/generic_pipeline.py` +cap 常量 + 1 处 size gate + 1 处
    checker lang_config pass-through
  - `core/translation_utils.py` +cap 常量 + 1 处 size gate
  - `translators/_screen_patch.py` +cap 常量 + 1 处 size gate
  - `pipeline/stages.py` +cap 常量 + 2 处 size gate
  - `file_processor/checker.py` +lang_config kwarg × 2（checker +
    filter）
  - `translators/tl_mode.py` 1 处 checker pass-through
  - `tests/test_engines_rpgmaker.py` +1 test
  - `tests/test_translation_state.py` +1 test
  - `tests/test_multilang_run.py` +5 tests
  - CHANGELOG / CLAUDE / `.cursorrules` / HANDOFF
- **文件大小检查**：所有源码 / 测试 < 800 保持（r42 加量都在百行内）
- **内部 JSON loader size cap 覆盖率**：r37-r41 覆盖 11 处 → r42 补齐
  到 18 处（所有已识别 user-facing + internal loader 全部 covered）

**本轮未做**（留给第 43+ 轮）：

- **PyInstaller 打包 smoke test**（r42 优先方向未能做 — pyinstaller 未
  装，不自行 pip install）：human follow-up，若打包失败回退加
  `"gui_handlers", "gui_pipeline", "gui_dialogs"` 到 `build.py::
  hidden_imports`
- **GUI 手动 smoke test 全面清单**（r41/r42 两轮积压）：需人工点击各
  Tab / 按钮 / 菜单验证 Tkinter callback + mixin MRO 在真实运行时正确
  dispatch
- 非中文目标语言端到端验证（r39 prompt + r41 alias + r42 checker 三层
  锁死 code-level contract，但需真实 API + 真实游戏跑 ja / ko / zh-tw
  实际翻译）
- A-H-3 Medium / Deep / S-H-4 Breaking — 需真实 API + 游戏验证
- RPG Maker Plugin Commands / 加密 RPA / RGSS
- CI Windows runner + docs/constants / quality_chain / roadmap 复查
  （连续 13 轮欠账）

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

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
