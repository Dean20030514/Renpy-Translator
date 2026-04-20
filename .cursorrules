<!-- 修改后执行 cp CLAUDE.md .cursorrules -->
# 多引擎游戏汉化工具 — AI 全局上下文

## 项目身份

纯 Python（零第三方依赖，≥3.9）多引擎游戏汉化工具。~15,000 行核心代码，409 个自动化测试。支持 Ren'Py / RPG Maker MV/MZ / CSV/JSONL，五大 LLM（xAI/OpenAI/DeepSeek/Claude/Gemini）+ 自定义引擎插件（`--sandbox-plugin` 可选 subprocess 沙箱，stderr 读取有 10 KB 上限防 OOM）。Direct-mode 漏翻率 4.01%，tl-mode 翻译成功率 99.97%。HTTPS 调用默认启用持久连接池（节省 ~90s 握手/600 次调用）+ 响应体 32 MB 硬上限。`core/translation_db.py` 线程安全（RLock）+ 原子写入（temp + os.replace）；round 34 升级到 schema v2，`entries` 新增可选 `language` 字段 + 4-tuple 索引键，让"同次运行多语言"成为 first-class（向后兼容 v1 DB 文件：`load()` 在 caller 传 `default_language` 时做强制回填，防 duplicate-bucket 膨胀）。`main.py` 所有引擎统一走 `engines.resolve_engine(...).run(args)` 单一入口。`tests/test_all.py` 为 meta-runner，实际测试分布在 6 个聚焦文件（api / file_processor / translators / glossary-prompts-config / translation-state / runtime-hook），每个均 < 800 行；round 34 额外的 `test_runtime_hook_filter` / `test_translation_db_language` 作独立套件保留清晰分层。`--emit-runtime-hook` opt-in 可生成 `translations.json` + `resources/hooks/inject_hook.rpy`（与 extract_hook 闭环），支持不改游戏源文件的运行时注入模式；round 32 加入 `--ui-button-whitelist` 扩展 UI 按钮清单（通过 sidecar JSON 同步到 hook）、`--runtime-hook-schema v2` 输出嵌套多语言 translations.json（运行时按 `RENPY_TL_INJECT_LANG` / `renpy.preferences.language` 选择语言）、emit 时自动把 `--font-file`（或 `resources/fonts/` 内建字体）打包为 `game/fonts/tl_inject.ttf`。Round 33 补齐"v2 多语言工具链"：`tools/merge_translations_v2.py` 把多次运行产出的 v2 envelope 合并成单一多语言文件；`--font-config` 通过 `zz_tl_inject_gui.rpy`（`init 999` 覆盖 + 注入白名单正则安全守护）把 gui 字号/布局 override 从静态模式透传到 runtime hook；`tools/translation_editor.py` 自动识别 v2 envelope 并支持 `--v2-lang` 选择语言 bucket 编辑 + 写回。Round 34 把三条"纵深"补齐：TranslationDB 真正支持多语言共存 + `build_translations_map` 获 `entry_language_filter` 防 v2 emit 跨 bucket 污染；`tools/translation_editor.py` 用 HTML dropdown 做**同页**多语言切换（per-lang `_edits` 状态 + 切换时 flush 保 pending 不丢）+ `tools/_translation_editor_html.py` 模板抽离；`core/runtime_hook_emitter.py::_OVERRIDE_CATEGORIES` 泛化 override 分派表（今仅注册 gui，保留扩展点）。Round 35 让多语言真正端到端：`ProgressTracker` 加 language namespace key（`"<lang>:<rel_path>"` 形式 + bare key fallback 保 r34 resume）、`--target-lang zh,ja,zh-tw` 逗号分隔语法触发 main.py 外层语言循环（每 lang 跑一次，`--tl-mode` / `--retranslate` 组合下 guard 报错因 prompt 中文专用）、editor checkbox 切换 side-by-side 多列并列显示（dropdown 保留共存）、`_OVERRIDE_CATEGORIES` 注册第二个 category `config_overrides`（扁平 `config.X = int|float` 仅，保持 style_overrides 刻意排除）。Round 36 深度审计驱动的两个 edge-case bug 修复（纯 fix 无新功能）：H1 `ProgressTracker` 跨语言 bare-key 污染（非 zh 的 language-aware tracker 不再读/写 bare bucket，新增 class 常量 `_LEGACY_BARE_LANG = "zh"` 显式标注 pre-r35 implicit owner；`mark_file_done` 镜像守卫防 non-zh 清 bare 摧毁 hypothetical zh resume）+ H2 `_sanitise_overrides` 加 `math.isfinite` 过滤拒收 `float('inf')/'-inf'/'nan'`（防 `repr(inf)='inf'` 写入 `init python:` block 导致 Ren'Py 启动 NameError，攻击面：不可信 `font_config.json` 通过 `json.loads` 接受 `Infinity`/`NaN` 偷渡）。Round 37 M 级防御加固包：M1 `TranslationDB.load()` 去掉 `version < SCHEMA_VERSION` gate，让 partial v2 文件缺 `language` 字段的 entry 也 backfill（防 None/zh duplicate-bucket 漂移）+ M2 4 处用户面 JSON loader 加 50 MB size cap（`font_patch.load_font_config` / `translation_db.load` / `merge_translations_v2._load_v2_envelope` / `translation_editor._apply_v2_edits`）防 OOM + M3 `main.py` 外层 multi-lang 循环 try/finally restore `args.target_lang` / `lang_config` 防 post-loop reader 踩最后一个语言残留 + M4 `_apply_v2_edits` 加 `Path.cwd().resolve()` path whitelist 防钓鱼 edits.json 劫持写到系统文件 + M5 空串 cell = SKIP 非 DELETE 语义文档化 + side-by-side label 加 `title` tooltip。Round 38 "收尾包"：拆 `tests/test_translation_editor.py` 847→376 + 新 `test_translation_editor_v2.py` 581（v2/side-by-side/M4/M5 的 11 测试迁移，byte-identical）+ M2 扩到另 4 处 user-facing JSON loader（`core/config.py::_load_config_file` / `core/glossary.py` 的 4 loader 共享 `_json_file_too_large` helper / `tools/translation_editor.py::_extract_from_db` + `import_edits`）+ `config_overrides` 扩 bool（新 `_OVERRIDE_ALLOW_BOOL` per-category map；gui 仍拒 bool，config 接受 `config.autosave=True` 等第一类 Ren'Py bool switches；`_sanitise_overrides` 加 `allow_bool` kwarg，bool 检查先于 int/float 防 `isinstance(True,int)==True` 偷渡）+ editor side-by-side `@media (max-width: 800px)` mobile 自适应（table `overflow-x: auto`，`.col-trans-multi` `min-width: 120px`，iOS Safari momentum 滚动）。Round 39 "收尾包 Part 2"：拆 `tests/test_translation_state.py` 850→681 + 新 `test_override_categories.py` 218（r34/r35/r38 的 4 override-dispatch tests 迁移）+ **tl-mode / retranslate per-language prompt**（r35 挂 4 轮的最后一项绿色小项）— `core/prompts.py` 新 `_GENERIC_TLMODE_SYSTEM_PROMPT` + `_GENERIC_RETRANSLATE_SYSTEM_PROMPT` 英文模板带 `{target_language}/{native_name}/{translation_instruction}/{field}/{style_notes}` 占位符，`build_tl_system_prompt` / `build_retranslate_system_prompt` 加 `lang_config` kwarg 按 `lang_config.code` 分路（zh/zh-tw → byte-identical 中文模板；非 zh → 新 generic 英文模板），`TranslationContext` 加 `lang_config` 字段，`tl_mode._translate_chunk` 和 `retranslator.retranslate_file` 用 `resolve_translation_field` 按 alias chain 读响应，`main.py` 去掉 r35 的 `--tl-mode --target-lang ja` multi-lang guard — `--tl-mode` / `--retranslate` 现在端到端支持非 zh 目标 + M2 phase-2 续扩 3 处 user-facing JSON loader（`tools/review_generator.py` + `tools/analyze_writeback_failures.py` + `pipeline/gate.py` glossary 加载，共 4+4+3=11/~16 user-facing loader 覆盖率）。Round 40 pre-existing 大文件拆分（3/4）：`tests/test_engines.py` 962→694（新 `test_engines_rpgmaker.py` 315 + 15 rpgmaker 测试 byte-identical 迁移），`tools/rpyc_decompiler.py` 974→725（新 `tools/_rpyc_shared.py` 47 leaf 常量 + `tools/_rpyc_tier2.py` 274 safe-unpickle 链，re-export 保 test + `renpy_lint_fixer` import 无感），`core/api_client.py` 965→642（新 `core/api_plugin.py` 378 — `_load_custom_engine` + `_SubprocessPluginClient` sandbox，re-export 保 `test_custom_engine` 20 测试无感）；`gui.py` 815 挂 r41（PyInstaller 打包耦合 + UI 手动测试要求）；全部 byte-identical 纯 refactor，396 测试数保持不变。Round 43 做 r36-r42 累计**三维度专项审计**（correctness / test coverage / security）+ 合流 3 个 valid 发现：audit 结果 **0 CRITICAL / 0 HIGH**，3 个 MEDIUM-level valid gap / defensive improvement。1 项 code change + 3 项 test：`core/api_plugin.py::_SubprocessPluginClient._read_response_line` 新增 `_MAX_PLUGIN_RESPONSE_BYTES = 50 * 1024 * 1024` 模块常量 + `readline(N)` bounded read（plugin 响应超 50 MB 无 newline → raise RuntimeError 走既有 error-wrapping；成对 r30 stderr 10 KB cap 一起 bound plugin stdout/stderr 三通道，stdin 由 `_SHUTDOWN_REQUEST_ID` 控制）+ `tests/test_custom_engine.py` +1 regression（stub `_proc.stdout` + `mock.patch` cap 到 1 KB 避免实际 alloc 50 MB）；test coverage 补齐 3 个 gap：`test_check_response_item_zh_tw_rejects_generic_zh_field` 钉住 zh-tw aliases **刻意不含 bare "zh"** 的设计决策（防 Simplified / Traditional 脚本家族混淆）、`test_check_response_item_mixed_language_fields_picks_correct_alias` 文档化 `resolve_translation_field` 的 alias 优先级契约（item 同时含 "ja"+"ko" 时按 lang_config field_aliases 顺序取）、`test_progress_tracker_handles_stat_failure_gracefully` 覆盖 r42 M2 phase-3 的 "stat() OSError → size=0 → 继续 read" 两步降级路径；测试 405→409；PyInstaller smoke + GUI manual smoke 仍待外部资源（r41/r42/r43 三轮积压）。Round 42 继续两项 HANDOFF 短平快：**内部 JSON loader cap 收尾**（r37-r39 M2 续作 phase-3）— `engines/rpgmaker_engine.py` 两处（user-facing，P1）+ `engines/generic_pipeline.py` / `core/translation_utils.py::ProgressTracker._load` / `translators/_screen_patch.py` 三处 internal progress loader（P2）+ `pipeline/stages.py` 两处 internal report loader（P3）各加 50 MB `_MAX_*_SIZE` 常量 + `stat().st_size` size gate（oversize → warning + 复用既有 fallback 路径 reset/continue/raise），至此 ~18/18 user-facing + internal JSON loader 全部 covered；**`file_processor/checker.py::check_response_item` per-language 化**（解锁 r41 audit test 文档化的"checker 只认 zh"约束）— signature 加 `lang_config: "object | None" = None` kwarg，body `if lang_config is not None:` 分路用 deferred `from core.lang_config import resolve_translation_field` 按 alias chain 读字段，`None` 默认保 r41 byte-identical；`_filter_checked_translations` 同样加 kwarg + 透传；调用点 `engines/generic_pipeline.py::run_generic_pipeline` 与 `translators/tl_mode.py::_translate_one_tl_chunk` 传入 lang_config，r39 的 post-checker `resolve_translation_field` 保留（读取 vs 校验职责不同）；deferred import 保 r27 A-H-2 `file_processor` 不 import `core` 的 layering 规则；5 个 regression test（backward compat + ja/ko alias 链 + generic fallback + `_filter_checked_translations` forwarding），测试 398 → 405；PyInstaller smoke / GUI manual smoke 推迟（r42 环境无 pyinstaller 且不自 pip install，GUI 需人工点击）。Round 41 收官 pre-existing 大文件拆分（4/4，**源码全部 < 800 行首次达成**）+ 3 项审计小尾巴：`gui.py` 815→489 拆为 mixin 继承架构 — 新 `gui_handlers.py` 73（`AppHandlersMixin` 3 个 UI event handler）+ `gui_pipeline.py` 230（`AppPipelineMixin` 9 方法：subprocess 启动 / 日志队列 / 进度条 / `_on_finished` 完成回调 / `_stop` / `_run_dry_run` / `_poll_log`；`_RE_PROGRESS` / `MAX_LOG_LINES` / `TRIM_TO` 常量迁出）+ `gui_dialogs.py` 140（`AppDialogsMixin` 5 方法：配置 I/O + 升级扫描 dialog + filedialog/messagebox）；`class App(AppHandlersMixin, AppPipelineMixin, AppDialogsMixin)` 通过 Python MRO 让所有跨 mixin 的 `self.X` 访问自动解析（`_poll_log` → `_on_finished`、`_run_upgrade_scan_on_game_dir` → `_append_log` 等）；`App.__init__` 加 `self._project_root = PROJECT_ROOT` 代替 mixin 里 `Path(__file__).parent`（否则 `_run_command` 的 subprocess cwd 错）；Tkinter bound-method callback（`command=self._start` / lambda）通过 MRO 正确 dispatch；build.py 入口仍 `gui.py`，同目录 `.py` 被 PyInstaller 静态分析自动 discover，`hidden_imports` 不用改；3 项审计尾巴：M4 `_apply_v2_edits` 的 `except OSError: trust_root = None` 加 `logger.warning("[V2-EDIT] Path.cwd().resolve() failed — CWD whitelist disabled ...")` 防 silent bypass（+1 regression test `test_apply_v2_edits_warns_when_cwd_resolve_fails` 用 monkey-patch `pathlib.Path.cwd` + 临时 `logging.Handler` 捕获 emit）+ r39 tl-mode alias chain integration test `test_tl_chunk_reads_alias_field_from_mocked_response` 用 mock APIClient.translate 返回 "zh" 陷阱 + "ja"/"jp" 真实 alias 断言 `kept_items` 从 alias 取值（证明 `ctx.lang_config → resolve_translation_field` 真正被调用，而非 legacy `t.get("zh","")` 硬编码）+ HANDOFF / CHANGELOG 的 "N 测试套件" 表述统一为 "N 测试文件 = 独立 suite + 1 meta-runner"（retroactively monotonic r38=19 / r39=20 / r40=21）。`core/font_patch.py::default_resources_fonts_dir()` 抽取为所有 4 个字体路径调用者的 canonical 出口（round 32 修复 `translators/direct.py` / `_tl_patches.py` 两处遗留 `__file__.parent` 少一层 bug）。

## 开发原则

1. **宁可漏翻也不误翻** — 不确定的条目保留原文
2. **数据驱动** — 改动前收集数据，改动后验证数据，不拍脑袋定阈值
3. **隔离变量** — 每次只改一个东西，验证独立效果
4. **不破坏已有功能** — 新功能用开关控制（CLI 参数），默认行为不变
5. **安全优先** — checker 不通过就丢弃、回写前校验、原地操作前备份
6. **先读再写** — 涉及参考项目借鉴时，先完整阅读其源码和文档再给方案
7. **方案先行** — 给出改动方案和受影响函数列表，等用户确认后再写代码
8. **最小改动** — 不做不必要的重构、不加不需要的注释、不改不相关的代码
9. **零依赖** — 坚持纯标准库，不引入第三方包

## 模块调用关系 + 职责

```
gui.py (图形界面) ─── start_launcher.py (CLI 菜单) ─── tools/renpy_upgrade_tool.py (独立工具)
       │                      │
       └──────────────────────┘
                │ subprocess 调用
                ▼
main.py (CLI 入口) → engines.resolve_engine(args.engine or "auto").run(args)
  │
  ├── engines/ 多引擎抽象层（所有引擎统一入口，round 28 A-H-3 Minimal）
  │    ├── engines/engine_detector.py  (检测+路由)
  │    ├── engines/engine_base.py      (EngineProfile/TranslatableUnit/EngineBase)
  │    ├── engines/generic_pipeline.py (6 阶段通用流水线)
  │    ├── engines/renpy_engine.py     (Ren'Py 薄包装，内部路由 tl_mode/tl_screen/retranslate/direct)
  │    ├── engines/rpgmaker_engine.py  (RPG Maker MV/MZ)
  │    └── engines/csv_engine.py       (CSV/JSONL)
  │
  ├── translators/ Ren'Py 三条管线（由 RenPyEngine.run 内部调度）
  │    ├── translators/direct.py         (direct-mode 入口 + run_pipeline)
  │    │   ├── _direct_chunk.py        (chunk 级翻译/重试/拆分)
  │    │   ├── _direct_file.py         (file 级翻译 + targeted 低密度路径)
  │    │   └── _direct_cli.py          (dry-run 预览/统计)
  │    ├── translators/retranslator.py   (补翻)
  │    ├── translators/tl_mode.py        (tl-mode 入口 + run_tl_pipeline)
  │    │   ├── _tl_patches.py          (font / rpyc / language switch patches)
  │    │   └── _tl_dedup.py            (跨文件去重 + chunk 装配)
  │    ├── translators/screen.py         (screen 裸英文翻译入口 + re-export)
  │    │   ├── _screen_extract.py      (扫描 / 识别 / 跳过判断)
  │    │   └── _screen_patch.py        (翻译 / 替换 / 进度 / 备份)
  │    ├── translators/tl_parser.py      (tl 解析核心 + re-export)
  │    │   ├── _tl_postprocess.py      (nvl clear / 空块后处理)
  │    │   ├── _tl_nvl_fix.py          (Ren'Py 8.6 → 7.x 翻译 ID 修复)
  │    │   └── _tl_parser_selftest.py  (内置 75 条自测套件)
  │    └── translators/renpy_text_utils.py (文本分析)
  │
  └── core/ 共享基础设施
       ├── core/api_client.py（含自定义引擎加载）/ core/prompts.py / core/glossary.py
       ├── core/translation_db.py / core/translation_utils.py
       ├── core/config.py / core/lang_config.py / core/font_patch.py
       ├── core/http_pool.py（HTTPS 线程本地连接池） / core/pickle_safe.py（白名单反序列化）
       ├── file_processor/ (splitter/patcher/checker/validator)
       └── one_click_pipeline.py → pipeline/ (Ren'Py 四阶段流水线 + lint 修复 + 默认语言)

tools/   — review_generator / rpa_unpacker / rpa_packer / rpyc_decompiler
           renpy_lint_fixer / renpy_upgrade_tool / translation_editor
           verify_alignment / revalidate / patch_font_now / analyze_writeback
custom_engines/ — 用户自定义翻译引擎插件目录（example_echo.py 示例）
tests/   — test_all(meta) → api_client(19) + file_processor(36) + translators(24) + glossary_prompts_config(24) + translation_state(15) = 118
           + test_engines(62) + smoke(13) + rpa(16) + rpyc(18) + lint(15) + dedup(10) + batch1(18)
           + editor(13) + custom(20) + direct_pipeline(2) + tl_pipeline(2) = 307
```

**调用关系图中未标注职责的关键文件**：

| 文件 | 职责 |
|------|------|
| engines/renpy_engine.py | Ren'Py 薄包装，委托三条管线 |
| pipeline/helpers.py | 文件评分 / 试跑选择 / 扫描辅助 |
| pipeline/gate.py | 闸门评估 / 漏翻归因 / 报告生成 |
| pipeline/stages.py | 四阶段实现入口 |
| build.py | PyInstaller 打包为单文件 .exe |
| resources/hooks/ | Ren'Py Hook 模板（提取 + 语言切换） |

## 修改代码前的检查清单

- [ ] 列出要修改的文件和函数，等用户确认后再写代码
- [ ] 是否引入了第三方依赖？（禁止）
- [ ] 是否改变了默认行为？（需要 CLI 开关控制）
- [ ] 新增/修改的函数是否有类型注解？
- [ ] 是否有对应的测试用例？运行 `python tests/test_all.py` 确认零回归
- [ ] 原地修改文件前是否有 .bak 备份逻辑？
- [ ] checker 不通过的翻译是否被丢弃（而非强行使用）？
- [ ] 开发完成后是否更新了 CHANGELOG_RECENT.md？

## 已知限制

- GUI/build 仅手动测试，未纳入自动化
- 端到端测试需 API key，未进入 CI
- RPG Maker Plugin Commands(356) / JS 硬编码 / 加密归档暂不支持

## 按需加载文档索引

| 你在做什么 | 加载哪个文档 |
|-----------|-------------|
| 修改翻译模式（direct/tl/retranslate） | `docs/dataflow_translate.md` |
| 修改一键流水线或核心算法 | `docs/dataflow_pipeline.md` |
| 修改校验逻辑或 API 调用 | `docs/quality_chain.md` |
| 修改/新增校验规则（Error/Warning Code） | `docs/error_codes.md` |
| 调整阈值或常量 | `docs/constants.md` |
| 新增引擎支持 | `docs/engine_guide.md` |
| 讨论下一步做什么 | `docs/roadmap.md` |
| 了解历史决策 | `CHANGELOG_RECENT.md` |
| 修改测试体系 | `TEST_PLAN.md` |
