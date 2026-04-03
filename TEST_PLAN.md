# 测试方案

本文档定义项目的完整测试体系：已有测试的覆盖范围、待补充的测试用例、测试数据与执行方法。

---

## 一、测试体系总览

### 现有测试文件

| 文件 | 类型 | 覆盖范围 | 用例数 | 需 API |
|------|------|----------|--------|--------|
| `tests/test_all.py` | 单元+集成测试 | core.api_client / file_processor / core.glossary / core.prompts / main / core.translation_utils / translators.retranslator / translators.renpy_text_utils / core.translation_db / core.config / core.lang_config / tools.review_generator / translators.direct / translators.tl_parser nvl ID 修正 / translators.screen / **locked_terms 预替换** | 94 | 否 |
| `tests/test_engines.py` | 引擎抽象层测试 | engines.EngineProfile / engines.TranslatableUnit / engines.EngineDetector / engines.RenPyEngine / engines.EngineBase / engines.CSVEngine / engines.generic_pipeline / checker 参数化 / core.prompts addon / engines.RPGMakerMVEngine / core.glossary RPG Maker | 62 | 否 |
| `tests/smoke_test.py` | 冒烟测试 | validate_translation 所有 Warning/Error Code + strings 统计 | 13 | 否 |
| `tests/test_rpa_unpacker.py` | RPA 解包测试 | RPA-3.0/2.0 解包、XOR key 变体、prefix bytes、版本检测、损坏文件、目录批量解包 | 14 | 否 |
| `tests/test_rpyc_decompiler.py` | rpyc 反编译测试 | RPYC2 二进制格式、RestrictedUnpickler、Say/Menu/TranslateString 文本提取、Unicode、平台检测 | 17 | 否 |
| `tests/test_lint_fixer.py` | lint 修复测试 | 7 种 lint 错误模式解析、old/new 对修复、translate 块修复、连续空行清理、降级检测 | 15 | 否 |
| `tests/test_tl_dedup.py` | tl-mode 去重测试 | 去重基础/阈值/speaker 隔离/StringEntry/apply 复用/无翻译降级 | 10 | 否 |
| `translators/tl_parser.py` (内建) | 自测试 | 状态机解析 / fill_translation / extract_quoted_text / postprocess / _sanitize_translation 边界 | 75 | 否 |
| `tests/test_single.py` | 端到端测试 | 单文件完整翻译流程（API→回写→校验） | 1 | **是** |

> **自动化测试总计**：94 + 62 + 13 + 14 + 17 + 15 + 10 = **225** 个用例（不含 translators/tl_parser 内建 75 断言 + translators/screen 内建 51 断言）。

> **注**：`gui.py`（Tkinter GUI）和 `build.py`（PyInstaller 打包）为手动测试，不纳入自动化测试体系。验证方式：`python gui.py` 弹出窗口 + `python build.py` 产出 .exe。

### 测试数据文件

| 文件 | 用途 |
|------|------|
| `tests/sample_triggers.rpy` | 触发各 Warning/Error 的原文（与 trans 文件逐行配对） |
| `tests/sample_triggers_trans.rpy` | 故意构造的问题译文 |
| `tests/glossary_test.json` | 含 locked_terms / no_translate 的术语表 |
| `tests/sample_strings.rpy` | translate strings 块样本（6 条 old/new） |
| `tests/fixtures/strings_only/` | strings 统计隔离子目录（防其他 .rpy 污染） |
| `tests/tl_priority_mini/` | tl 优先模式最小目录结构 |
| `tests/artifacts/` | 实际项目 untranslated JSON（projz / tyrant） |

---

## 二、已覆盖的测试用例

### tests/test_all.py（94 个单元测试）

| # | 函数 | 覆盖模块 | 测试内容 |
|---|------|----------|----------|
| 1 | `test_api_config` | core.api_client | 5 个提供商的 endpoint / model 默认值 |
| 2 | `test_usage_stats` | core.api_client | token 累计、费用估算、summary 格式 |
| 3 | `test_rate_limiter` | core.api_client | RateLimiter acquire 不报错 |
| 4 | `test_estimate_tokens` | file_processor | 英文/中文 token 估算 > 0 |
| 5 | `test_find_block_boundaries` | file_processor | label/screen/init 块边界检测 |
| 6 | `test_safety_check` | file_processor | 变量丢失/多出、标签不匹配、换行符、{#id}、%(name)s、长度比例 |
| 7 | `test_apply_translations` | file_processor | 基本行级回写 |
| 8 | `test_apply_cascade` | file_processor | 多条翻译指向同一行时不重复替换 |
| 9 | `test_validate_translation` | file_processor | 无问题文件通过 + 变量丢失检出 |
| 10 | `test_glossary` | core.glossary | to_prompt_text / update_from_translations 过滤（短句/同值/数字/标点） |
| 11 | `test_prompts` | core.prompts | system_prompt 含风格/术语/规范 + user_prompt 含文件名/chunk 信息 |
| 12 | `test_json_parse` | core.api_client | 6 级 JSON 解析：直接/markdown/尾逗号/空数组/垃圾/逐对象/转义引号/字段顺序 |
| 13 | `test_force_split` | file_processor | 超大块强制拆分，总行数不丢 |
| 14 | `test_triple_quote_replacement` | file_processor | 三引号字符串替换 |
| 15 | `test_underscore_func_replacement` | file_processor | `_()` 包裹字符串替换 |
| 16 | `test_validate_menu_identifier` | file_processor | `{#identifier}` 保留/丢失检测 |
| 17 | `test_glossary_dedup` | core.glossary | terms 中已有的不重复进 memory |
| 18 | `test_image_block_boundary` | file_processor | image 声明作为块边界 |
| 19 | `test_glossary_thread_safety` | core.glossary | 4 线程 × 50 条并发写入 |
| 20 | `test_progress_cleanup` | core.translation_utils.ProgressTracker | mark_file_done 后 results 被清理 |
| 21 | `test_pricing_lookup` | core.api_client | 精确/前缀/兜底定价 + 推理模型检测 |
| 22 | `test_protect_restore_roundtrip` | file_processor | protect→translate→restore 往返正确 |
| 23 | `test_protect_dedup` | file_processor | 相同占位符去重（mapping 长度 1） |
| 24 | `test_protect_empty_and_no_placeholders` | file_processor | 空文本/无占位符原样返回 |
| 25 | `test_protect_mixed_types` | file_processor | 混合 [var]+{tag}+%(fmt)s 三种类型 |
| 26 | `test_protect_menu_id` | file_processor | {#id} 菜单标识符保护 |
| 27 | `test_check_response_item_normal` | file_processor | 正常条目通过 |
| 28 | `test_check_response_item_empty_zh` | file_processor | 译文为空被拦截 |
| 29 | `test_check_response_item_empty_original` | file_processor | 原文为空被拦截 |
| 30 | `test_check_response_item_var_missing` | file_processor | 占位符缺失被拦截 |
| 31 | `test_check_response_item_var_preserved` | file_processor | 占位符保留时通过 |
| 32 | `test_check_response_item_line_offset` | file_processor | line_offset 正确叠加 |
| 33 | `test_check_response_chunk_match` | file_processor | 条数一致无警告 |
| 34 | `test_check_response_chunk_mismatch` | file_processor | 条数不一致有警告 |
| 35 | `test_check_response_chunk_empty` | file_processor | 空 chunk 无警告 |
| 36 | `test_check_response_chunk_skip_chinese` | file_processor | 已含中文行跳过 |
| 37 | `test_dialogue_density` | translators.retranslator | 密度自适应路由（低/高/空 3 用例） |
| 38 | `test_skip_files` | file_processor | SKIP_FILES_FOR_TRANSLATION 跳过名单完整性 |
| 39 | `test_find_untranslated_lines` | translators.retranslator | 漏翻检测二次过滤（auto/idle/hover/image 排除） |
| 40 | `test_translation_db_roundtrip` | core.translation_db | save/load 往返 + upsert 去重 |
| 41 | `test_is_untranslated_dialogue` | translators.renpy_text_utils | 漏翻检测辅助函数（中文/英文/短文本） |
| 42 | `test_restore_placeholders_in_translations` | core.translation_utils | 公共辅助函数占位符还原 |
| 43 | `test_progress_resume` | core.translation_utils.ProgressTracker | 写入后重载数据一致 |
| 44 | `test_progress_normalize` | core.translation_utils.ProgressTracker | 损坏/缺key的JSON不崩溃 |
| 45 | `test_filter_checked_translations` | core.translation_utils | checker过滤：正常/空译文/占位符缺失 |
| 46 | `test_deduplicate_translations` | core.translation_utils | 去重：有重复/无重复/空列表 |
| 47 | `test_match_string_entry_fallback` | core.translation_utils | 四层fallback：精确/strip/去令牌/转义 |
| 48 | `test_api_empty_choices` | core.api_client | 推理模型检测（reasoning/o系列） |
| 49 | `test_positive_int_validation` | main | CLI参数校验：正值/零/负值 |
| 50 | `test_reasoning_model_timeout` | core.api_client | 推理模型auto timeout≥300s |
| 51 | `test_glossary_hyphenated_names` | core.glossary | 连字符人名提取（Mary-Jane） |
| 52 | `test_glossary_memory_confidence` | core.glossary | 翻译记忆信心度过滤（count>=2才输出） |
| 53 | `test_protect_control_tags` | file_processor | 控制标签{w}/{p}/{nw}/{fast}/{cps=N}被保护 |
| 54 | `test_replace_string_prefix_strip` | file_processor.patcher | WF-08 修复：AI 返回含行前缀的 original 剥离 |
| 55 | `test_replace_string_escaped_quotes` | file_processor.patcher | WF-04 修复：含转义引号字符串匹配 |
| 56 | `test_config_load_and_defaults` | core.config | 无配置文件时使用 DEFAULTS |
| 57 | `test_config_cli_override` | core.config | CLI 参数覆盖配置文件和默认值 |
| 58 | `test_config_file_load` | core.config | 配置文件正常加载并合并 |
| 59 | `test_progress_bar_render` | core.translation_utils.ProgressBar | 渲染不崩溃 + 计数/费用正确 |
| 60 | `test_review_generator_html` | tools.review_generator | HTML 生成 + 内容验证 |
| 61 | `test_lang_config_detect` | core.lang_config | 中日韩文字检测函数准确性 |
| 62 | `test_lang_config_lookup` | core.lang_config | get_language_config 查找与回退 |
| 63 | `test_resolve_translation_field` | core.lang_config | 兼容别名读取（zh/chinese/cn/translation） |
| 64 | `test_prompt_zh_unchanged` | core.prompts | 中文 prompt 零变更回归（基线对比） |
| 65 | `test_prompt_ja_generic` | core.prompts | 日语通用英文模板内容验证 |
| 66 | `test_validator_lang_config` | file_processor.validator | W442 使用 lang_config 参数化检测 |
| 67 | `test_should_retry_truncation` | translators.direct | 截断检测：returned < expected*0.5 触发 needs_split + 边界（returned=0、expected=0） |
| 68 | `test_should_retry_normal` | translators.direct | 正常返回不重试 + 丢弃率过高重试不拆分 |
| 69 | `test_split_chunk_basic` | translators.direct | chunk 二分后行数守恒 + line_offset 正确 |
| 70 | `test_split_chunk_at_empty_line` | translators.direct | 优先在空行处拆分验证 |
| 71 | `test_config_validation` | core.config | Config.validate() 类型检查/范围校验/未知键告警（4 子场景） |
| 72 | `test_fix_nvl_ids_basic` | translators.tl_parser | 含 nvl clear 的翻译块：say-only ID 被替换为 nvl+say ID |
| 73 | `test_fix_nvl_ids_no_nvl` | translators.tl_parser | 不含 nvl clear 的块不受影响 |
| 74 | `test_fix_nvl_ids_already_correct` | translators.tl_parser | 已正确的 nvl+say ID 不会被重复修改（幂等性） |
| 75 | `test_fix_nvl_ids_real_hashes` | translators.tl_parser | 用 begin.rpy 真实数据验证哈希计算（2 个已知 case） |
| 76 | `test_screen_should_skip` | translators.screen | 12 种跳过/不跳过场景（空串/纯变量/已中文/文件路径/正常文本） |
| 77 | `test_screen_extract_basic` | translators.screen | text/textbutton/tt.Action 三种模式提取 + 纯变量跳过 + 类型正确性 |
| 78 | `test_screen_extract_skips_underscore` | translators.screen | `_()` 包裹行被跳过（已由 tl translate strings 覆盖） |
| 79 | `test_screen_extract_skips_outside_screen` | translators.screen | screen 定义外的 text 不提取（in_screen 上下文检测） |
| 80 | `test_screen_dedup` | translators.screen | 相同文本去重 + 保留所有出现位置 |
| 81 | `test_screen_replace_text` | translators.screen | text 行替换保留缩进 |
| 82 | `test_screen_replace_textbutton_preserves_action` | translators.screen | textbutton 只替换显示文本，action/style 参数不动 |
| 83 | `test_screen_replace_tt_action` | translators.screen | tt.Action 替换括号内字符串，focus_mask 等参数不动 |
| 84 | `test_screen_replace_with_tags_and_vars` | translators.screen | 含 `{color}` 和 `[var]` 的复合文本正确替换 |
| 85 | `test_screen_backup_no_overwrite` | translators.screen | .bak 仅在不存在时创建，二次调用不覆盖 |
| 86 | `test_screen_chunks` | translators.screen | 分块行数守恒（100 条/40 per chunk → 3 chunks） |
| 87 | `test_screen_replace_notify` | translators.screen | Notify("...") 替换正确 + action 参数不动 |
| 88 | `test_locked_terms_protect_basic` | file_processor.checker | locked_terms 保护 + 中文译名还原往返正确 |
| 89 | `test_locked_terms_word_boundary` | file_processor.checker | \b 词边界防止部分匹配（GameOver vs Game） |
| 90 | `test_locked_terms_longer_first` | file_processor.checker | 长术语优先匹配（New York > New） |
| 91 | `test_locked_terms_empty` | file_processor.checker | 空字典 / 空值术语不处理 |
| 92 | `test_locked_terms_no_match` | file_processor.checker | 文本中不含术语时原样返回 |
| 93 | `test_locked_terms_multiple_occurrences` | file_processor.checker | 同一术语多次出现全部替换 + 还原 |
| 94 | `test_locked_terms_special_chars` | file_processor.checker | 含 regex 特殊字符的术语（C++ / Mr.Smith） |

### tests/test_rpa_unpacker.py（14 个 RPA 解包测试）

| # | 函数 | 测试内容 |
|---|------|----------|
| 1 | `test_rpa3_list` | RPA-3.0 文件列表提取 |
| 2 | `test_rpa3_extract` | RPA-3.0 文件内容提取 + 完整性校验 |
| 3 | `test_rpa3_extract_scripts_only` | 扩展名过滤（仅 .rpy/.rpyc） |
| 4 | `test_rpa3_no_overwrite` | force=False 跳过已存在文件 |
| 5 | `test_rpa3_force_overwrite` | force=True 覆盖已存在文件 |
| 6 | `test_rpa2_extract` | RPA-2.0 解包（无 XOR key） |
| 7 | `test_rpa3_different_keys` | 5 种 XOR key 变体（0/1/0xFFFFFFFF/0x12345678/0xCAFEBABE） |
| 8 | `test_rpa3_prefix_bytes` | index 条目含 prefix bytes 时正确拼接 |
| 9 | `test_unsupported_version` | RPA-4.0 等不支持版本的清晰错误信息 |
| 10 | `test_invalid_file` | 非 RPA 文件的版本检测 |
| 11 | `test_corrupted_index` | 损坏 zlib 数据的错误检测 |
| 12 | `test_unpack_all_rpa_in_dir` | 目录批量解包多个 .rpa 文件 |
| 13 | `test_nested_directory_structure` | 嵌套目录结构还原（tl/english/script.rpy） |
| 14 | `test_empty_archive` | 空档案不报错 |

### tests/test_rpyc_decompiler.py（17 个 rpyc 反编译测试）

| # | 函数 | 测试内容 |
|---|------|----------|
| 1 | `test_read_rpyc2_slot1` | RPYC2 slot 1 数据读取 |
| 2 | `test_read_rpyc2_missing_slot` | 不存在的 slot 返回 None |
| 3 | `test_read_legacy_rpyc` | Legacy（pre-RPYC2）格式读取 |
| 4 | `test_read_legacy_rpyc_slot2` | Legacy 格式只有 slot 1 |
| 5 | `test_read_corrupted_rpyc` | 损坏 zlib 数据返回 None |
| 6 | `test_restricted_unpickler` | renpy.ast 类替换为 DummyClass |
| 7 | `test_extract_say_statements` | Say 语句文本 + speaker 提取 |
| 8 | `test_extract_menu_items` | Menu 选项文本提取 |
| 9 | `test_extract_translate_strings` | TranslateString old/new/language 提取 |
| 10 | `test_extract_mixed_content` | Say + Menu + TranslateString 混合 |
| 11 | `test_extract_empty_rpyc` | 无可翻译内容返回空列表 |
| 12 | `test_extract_unicode_content` | CJK/日文 Unicode 文本正确提取 |
| 13 | `test_extract_strings_standalone` | 目录批量提取模式 |
| 14 | `test_extract_strings_standalone_json_output` | JSON 文件输出 |
| 15 | `test_find_renpy_python_not_found` | 空目录返回 None |
| 16 | `test_find_renpy_python_with_lib` | 模拟 lib/ 目录结构找到 Python |
| 17 | `test_detect_renpy_version` | py3 路径检测为 Ren'Py 8.x |

### tests/test_lint_fixer.py（15 个 lint 修复测试）

| # | 函数 | 测试内容 |
|---|------|----------|
| 1 | `test_remove_consecutive_empty_lines` | 连续空行折叠 |
| 2 | `test_remove_consecutive_no_change` | 无连续空行不变 |
| 3 | `test_parse_lint_termination_error` | "not terminated" 错误解析 |
| 4 | `test_parse_lint_end_of_line` | "end of line expected" 错误解析 |
| 5 | `test_parse_lint_empty_block` | "expects a non-empty block" 错误解析 |
| 6 | `test_parse_lint_unknown_statement` | "unknown statement" 错误解析 |
| 7 | `test_parse_lint_duplicate_translation` | 重复翻译异常解析 |
| 8 | `test_parse_lint_multiple_errors` | 多错误混合解析（4 种） |
| 9 | `test_parse_lint_no_errors` | 无错误输出返回空列表 |
| 10 | `test_fix_old_new_pair` | old/new 翻译对修复 |
| 11 | `test_fix_unknown_statement` | 无效语句删除 |
| 12 | `test_fix_translate_block` | translate 块头修复 |
| 13 | `test_fix_preserves_other_content` | 修复不影响无关内容 |
| 14 | `test_lint_not_available_empty_dir` | 空目录无 lib/ 返回不可用 |
| 15 | `test_lint_not_available_no_game_dir` | 无 game/ 返回不可用 |

### tests/test_tl_dedup.py（10 个跨文件去重测试）

| # | 函数 | 测试内容 |
|---|------|----------|
| 1 | `test_dedup_basic` | 长句去重 + 短句保留 |
| 2 | `test_dedup_different_speakers` | 不同 speaker 同文本不去重 |
| 3 | `test_dedup_string_entries` | StringEntry 去重 |
| 4 | `test_dedup_no_duplicates` | 全部唯一不去重 |
| 5 | `test_dedup_threshold` | 默认阈值 40 字符 |
| 6 | `test_dedup_custom_threshold` | 自定义阈值 |
| 7 | `test_dedup_mixed_types` | DialogueEntry + StringEntry 混合 |
| 8 | `test_apply_dedup_basic` | 翻译结果复用到重复条目 |
| 9 | `test_apply_dedup_no_translation` | 首条未翻译时不复用 |
| 10 | `test_apply_dedup_string_entry` | StringEntry 用 old text 做 key 复用 |

### tests/smoke_test.py（13 个冒烟测试）

| # | 函数 | 测试内容 |
|---|------|----------|
| 1 | `test_w430_len_ratio_suspect_triggered` | W430 长度比例过短触发 |
| 2 | `test_w440_model_speaking_triggered` | W440 模型自述触发 |
| 3 | `test_w441_punct_mix_triggered` | W441 标点混用触发 |
| 4 | `test_w442_suspect_english_output_triggered` | W442 中文占比极低触发 |
| 5 | `test_w251_placeholder_order_triggered` | W251 占位符顺序不同触发 |
| 6 | `test_e411_glossary_lock_miss_triggered` | E411 锁定术语未命中触发 |
| 7 | `test_e420_no_translate_changed_triggered` | E420 禁翻片段被改触发 |
| 8 | `test_e420_case_insensitive_when_kept` | E420 大小写不敏感保留时不触发 |
| 9 | `test_extract_placeholder_sequence_nested_order` | 嵌套占位符提取顺序正确 |
| 10 | `test_collect_strings_stats_summary` | strings 统计 6 条/已翻 3/未翻 3 |
| 11 | `test_w430_boundary_below_lower` | W430 边界：比例 < 0.3 触发 |
| 12 | `test_w430_boundary_at_upper` | W430 边界：比例 > 2.5 触发 |
| 13 | `test_w251_order_vs_set_same_order_no_w251` | W251 顺序相同时不触发 |

### translators/tl_parser.py 内建自测（75 个断言）

通过 `python -m translators.tl_parser` 直接运行 `_run_self_tests()`，覆盖：
- 状态机解析（IDLE / DIALOGUE / STRINGS / SKIP 状态切换）
- DialogueEntry / StringEntry 字段提取
- `extract_quoted_text` 各种引号场景
- `fill_translation` 行级回填（保留缩进/character 前缀/只替换第一个 `""`）
- `_sanitize_translation` 元数据清理 / 引号剥离 / 转义
- `postprocess_tl_file` nvl clear 移除 / 空块补 pass
- UTF-8 BOM 处理
- 源注释行（`# game/script.rpy:95`）解析

### translators/screen.py 内建自测（42 个断言）

通过 `python -m translators.screen` 直接运行 `_run_self_tests()`，覆盖：
- `_should_skip` 12 种场景（空串/纯变量/中文/文件路径/正常文本）
- `_line_has_underscore_wrap` 3 种场景
- `extract_screen_strings` 完整提取（text/textbutton/tt.Action + 跳过 `_()` + 跳过 screen 外）
- `_deduplicate_entries` 去重 + 位置保留
- `_replace_screen_strings_in_file` 三种模式替换（text/textbutton/tt.Action + action 参数不动 + 多 tt.Action 同行）
- `_create_backup` 备份逻辑（创建 + 不覆盖已有）
- `_build_screen_chunks` 分块行数守恒
- `Notify("...")` 提取 + 替换（第四种文本模式）
- `_should_skip` 含 Ren'Py 闭合标签的文本不被误判为文件路径

---

## 三、触发条件与测试输入详解

本节描述 `tests/sample_triggers.rpy` + `tests/sample_triggers_trans.rpy` 的逐行设计。
两文件行数严格一致，逐行配对作为 `validate_translation(orig, trans)` 的输入。

| 行号 | 原文要点 | 译文要点 | 触发 Code |
|------|----------|----------|-----------|
| 5 | 长句（> 20 字） | `"好。"`（2 字，< 5 字不触发 W430；smoke_test 用内联构造触发） | W430 辅助 |
| 7 | 普通对话 | 含 `"作为一个ai语言模型"` | W440 |
| 9 | 短问句 | `"真的吗？??"` | W441 |
| 11 | 长句（≥ 15 字） | 原封不动英文（中文占比 0%） | W442 |
| 13 | 含 `[var_a]` 和 `[var_b]` | 顺序调换为 `[var_b]...[var_a]` | W251 |
| 15 | 含 `MyGame`（locked_terms） | 不含「我的游戏」 | E411 |
| 17 | 含 `DONT_TRANSLATE_ME`（no_translate） | 未保留该串 | E420 |
| 19 | 含 `v1.0`（no_translate） | 保留 `V1.0`（大小写不同） | E420 不触发（正确行为） |

### glossary_test.json 结构

```json
{
  "characters": {},
  "terms": {"Save": "保存", "Load": "读取", "Settings": "设置", "MyGame": "我的游戏", "PROJECT_X": "项目X"},
  "memory": {},
  "locked_terms": ["MyGame", "PROJECT_X"],
  "no_translate": ["DONT_TRANSLATE_ME", "v1.0"]
}
```

---

## 四、边界值测试

### W430：长度比例（len_ratio_lower=0.3, len_ratio_upper=2.5）

前提：原文 ≥ 20 字且译文 ≥ 5 字时才检查。

| 用例 | 原文字数 | 译文字数 | 比例 | 期望 |
|------|----------|----------|------|------|
| 低于下限 | 26 | 5 | 0.19 | **触发** W430 |
| 等于下限 | 20 | 6 | 0.30 | 不触发 |
| 正常 | 20 | 15 | 0.75 | 不触发 |
| 等于上限 | 20 | 50 | 2.50 | 不触发 |
| 高于上限 | 20 | 51 | 2.55 | **触发** W430 |

已实现：smoke_test `test_w430_boundary_below_lower` + `test_w430_boundary_at_upper`。

### W442：中文占比（< 10% 触发）

前提：原文 ≥ 15 字且译文 ≥ 10 字。

| 用例 | 译文总字数 | 中文字数 | 占比 | 期望 |
|------|------------|----------|------|------|
| 低于 10% | 20 | 1 | 5% | **触发** W442 |
| 等于 10% | 20 | 2 | 10% | 不触发（`< 0.10`） |
| 高于 10% | 20 | 3 | 15% | 不触发 |

### E411：锁定术语

| 用例 | 原文 | 译文 | 期望 |
|------|------|------|------|
| 未用规定译名 | 含 `MyGame` | 不含「我的游戏」 | **E411** |
| 使用规定译名 | 含 `MyGame` | 含「我的游戏」 | 无 E411 |
| 原文不含该词 | 不含 `MyGame` | 任意 | 无 E411 |

### E420：禁翻片段（大小写不敏感）

| 用例 | no_translate | 原文 | 译文 | 期望 |
|------|-------------|------|------|------|
| 缺失 | `DONT_TRANSLATE_ME` | 含该串 | 无该串 | **E420** |
| 原样保留 | `DONT_TRANSLATE_ME` | 含该串 | 含该串 | 无 E420 |
| 小写保留 | `DONT_TRANSLATE_ME` | 含该串 | 含 `dont_translate_me` | 无 E420 |

已实现：smoke_test `test_e420_case_insensitive_when_kept`。

### W251：占位符顺序 vs 集合

| 用例 | 原文序列 | 译文序列 | 集合同 | 顺序同 | 期望 |
|------|----------|----------|--------|--------|------|
| 顺序不同 | [a],[b] | [b],[a] | 是 | 否 | **W251** |
| 顺序相同 | [a],[b] | [a],[b] | 是 | 是 | 无 W251 |
| 集合不同（缺） | [a],[b] | [a] | 否 | — | E210（不触发 W251） |
| 集合不同（多） | [a] | [a],[b] | 否 | — | W211（不触发 W251） |

已实现：smoke_test `test_w251_order_vs_set_same_order_no_w251`。

---

## 五、待补充测试用例（TODO）

### 高优先级：核心函数单元测试

以下函数尚无独立测试用例，是 .cursor_prompt 中标记的高优先级 TODO。

#### T1. protect_placeholders / restore_placeholders — **已实现**

> 已在 test_all.py #22-36 中实现（#22-26 覆盖 protect/restore）。

#### T2. check_response_item — **已实现**

> 已在 test_all.py #22-36 中实现（#27-32 覆盖 check_response_item）。

#### T3. check_response_chunk — **已实现**

> 已在 test_all.py #22-36 中实现（#33-36 覆盖 check_response_chunk）。

#### T4. _sanitize_translation（translators/tl_parser.py） — **已实现**

> 已在 translators/tl_parser.py 内建自测 #11-#12 中实现（19 个断言）

| 用例 | 输入 | 期望输出 |
|------|------|----------|
| 无引号 | `你好世界` | `你好世界` |
| ASCII 双引号包裹 | `"你好世界"` | `你好世界` |
| 弯引号包裹 | `\u201c你好世界\u201d` | `你好世界` |
| 全角引号包裹 | `\uff02你好世界\uff02` | `你好世界` |
| 双层引号 | `""你好世界""` | `你好世界` |
| 元数据 `[ID: xxx]` | `[ID: abc123] 你好世界` | `你好世界` |
| 内嵌 ASCII 引号 | `他说"你好"` | `他说\\"你好\\"` |
| 单侧残存 | `你好世界"` | `你好世界` |

#### T5. fill_translation（translators/tl_parser.py） — **已实现**

> 已在 translators/tl_parser.py 内建自测 #11-#12 中实现（19 个断言）

| 用例 | 场景 | 期望 |
|------|------|------|
| 正常回填 | 行含 `""` | `""` → `"译文"` |
| 已有翻译 | 行不含 `""` | 跳过，打印 WARNING |
| 行号越界 | tl_line > 文件行数 | 跳过，打印 WARNING |
| 多个 `""` | 行含两处 `""` | 只替换第一个 |
| 含缩进 | 4 空格缩进 | 缩进保留 |
| character 前缀 | `    mc ""` | 替换后 `    mc "译文"` |

---

### 中优先级：集成级测试

#### T6. 密度自适应路由

| 用例 | 文件内容 | 期望 |
|------|----------|------|
| 低密度（< 20%） | 10 行代码 + 1 行对话 | 走 `_translate_file_targeted`，打印 `[DENSITY]` |
| 高密度（≥ 20%） | 2 行代码 + 8 行对话 | 走 `split_file` → chunk 翻译 |
| 阈值边界 | 密度恰好 = 0.20 | 走整文件翻译（`>=` 不走定向） |

验证方法：构造文件，检查控制台是否输出 `[DENSITY]` 或 `[CHUNK]`。

#### T7. SKIP_FILES_FOR_TRANSLATION

| 用例 | 文件名 | 期望 |
|------|--------|------|
| define.rpy | 跳过 | 打印 `[SKIP-CFG]`，`count_untranslated_dialogues_in_file` 返回 `(0, 0)` |
| variables.rpy | 跳过 | 同上 |
| screens.rpy | 跳过 | 同上 |
| options.rpy | 跳过 | 同上 |
| earlyoptions.rpy | 跳过 | 同上 |
| script.rpy | 不跳过 | 正常翻译 |

已部分覆盖：可通过 `count_untranslated_dialogues_in_file` 直接测试。

#### T8. find_untranslated_lines 二次过滤

| 输入行 | 应检出 | 原因 |
|--------|--------|------|
| `auto "path_%s.png"` | 否 | auto 定义行 |
| `idle "icon_hover.png"` | 否 | idle 属性行 |
| `hover "btn_hover.png"` | 否 | hover 属性行 |
| `image bg = "backgrounds/bg.png"` | 否 | image 路径 |
| `text "Name" xalign 0.5` | 否 | screen 属性行（取决于具体过滤逻辑） |
| `pov "Hello world, this is a long test line for detection."` | **是** | 纯英文对话 |

#### T9. tl 优先模式

使用 `tests/tl_priority_mini/` 目录：

```bash
# 启用 --tl-priority：仅 tl/zh/script.rpy 被选
python -m translators.retranslator --game-dir "tests/tl_priority_mini/game" --provider xai --dry-run --tl-priority

# 不启用：script.rpy 和 tl/zh/script.rpy 均被选
python -m translators.retranslator --game-dir "tests/tl_priority_mini/game" --provider xai --dry-run
```

#### T10. strings 统计

使用 `tests/fixtures/strings_only/`（含 6 条 old/new，3 已翻译/3 未翻译）：

```python
result = collect_strings_stats(Path("tests/fixtures/strings_only"))
assert result["summary"]["total_strings_entries"] == 6
assert result["summary"]["total_strings_translated"] == 3
assert result["summary"]["untranslated_ratio"] == 0.5
```

已实现：smoke_test `test_collect_strings_stats_summary`。

---

### 待补充：需 API 的端到端测试

| 编号 | 测试 | 状态 | 说明 |
|------|------|------|------|
| T11 | 单文件翻译端到端 | ⚠ 需 API | `tests/test_single.py`，验证 API→回写→校验完整链路 |
| T12 | tl-mode 端到端 | ⚠ 需 API | 5-10 个空槽位，验证回填+引号剥离+备份+进度 |
| T13 | retranslate 端到端 | ⚠ 需 API | 验证残留英文检出+补翻+已有翻译不破坏 |
| T14 | 一键流水线端到端 | ⚠ 需 API | 极小目录，验证 Stage 1-4 + 闸门 + 报告 |

> T11-T14 需 API key，建议作为 CI 中的可选步骤（手动触发）。

---

## 六、测试执行方法

### 无 API 测试（推荐日常使用）

```bash
# 全部 225 个自动化用例（< 5 秒）
python tests/test_all.py             # 94 个单元+集成测试
python tests/test_engines.py         # 62 个引擎抽象层测试
python tests/smoke_test.py           # 13 个校验规则冒烟测试
python tests/test_rpa_unpacker.py    # 14 个 RPA 解包测试
python tests/test_rpyc_decompiler.py # 17 个 rpyc 反编译测试
python tests/test_lint_fixer.py      # 15 个 lint 修复测试
python tests/test_tl_dedup.py        # 10 个 tl 去重测试
python -m translators.tl_parser --test  # 75 个解析器断言（内建）
```

全部通过预期输出：
```
ALL 94 TESTS PASSED          (tests/test_all.py)
ALL 62 ENGINE TESTS PASSED   (tests/test_engines.py)
All tests passed              (tests/smoke_test.py)
All 75 assertions passed.     (translators/tl_parser.py)
```

### 需 API 测试

```bash
# 单文件端到端（需 xAI API key）
python tests/test_single.py YOUR_API_KEY

# tl-mode 端到端
python -m translators.retranslator --game-dir "tests/tl_priority_mini/game" --provider xai --api-key YOUR_KEY --tl-mode --tl-lang zh

# 一键流水线（需真实游戏目录）
python -m translators.renpy_text_utils --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY --pilot-count 3 --clean-output
```

### 推荐执行顺序

1. **快速验证**：`python tests/test_all.py && python tests/smoke_test.py && python -m translators.tl_parser --test`（< 5 秒，无 API）
2. **边界验证**：smoke_test 中的 boundary 测试已覆盖 W430/W251 边界
3. **密度/跳过**：构造低密度文件 + define.rpy 验证 `[DENSITY]` / `[SKIP-CFG]` 日志
4. **tl 优先**：`--dry-run` 模式验证文件选择（无需 API）
5. **端到端**：有 API key 时运行 `tests/test_single.py`

---

## 七、测试覆盖率差距分析

### 已良好覆盖

| 模块 | 覆盖函数 | 测试数 |
|------|----------|--------|
| file_processor.validate_translation | 全部 12 个 E/W Code | 13（smoke_test） |
| file_processor._check_translation_safety | 变量/标签/换行/ID/格式/长度 | 10（test_all） |
| file_processor.protect_placeholders / restore_placeholders | 往返/去重/空文本/混合类型/{#id} | 5（test_all #22-26） |
| file_processor.check_response_item | 正常/空译文/空原文/占位符缺失保留/line_offset | 6（test_all #27-32） |
| file_processor.check_response_chunk | 条数匹配/不匹配/空chunk/跳过中文 | 4（test_all #33-36） |
| core.api_client | APIConfig / UsageStats / RateLimiter / JSON 解析 / 定价 | 5（test_all） |
| core.glossary | prompt_text / 过滤 / 去重 / 线程安全 | 4（test_all） |
| translators.tl_parser | 状态机 / 回填 / 清理 / 后处理 / _sanitize_translation 边界 / fill_translation 边界 | 75（内建） |
| translators.retranslator.calculate_dialogue_density | 低密度/高密度/空文件 | 1（test_all #37） |
| translators.retranslator.find_untranslated_lines | auto/idle/hover/image 排除 + 长英文检出 | 1（test_all #39） |
| core.translation_utils._restore_placeholders_in_translations | 占位符还原辅助函数 | 1（test_all #42） |
| core.translation_db.TranslationDB | save/load 往返 + upsert 去重 | 1（test_all #40） |
| translators.renpy_text_utils._is_untranslated_dialogue | 中文/英文/短文本判定 | 1（test_all #41） |
| file_processor.SKIP_FILES_FOR_TRANSLATION | 跳过名单完整性 | 1（test_all #38） |
| core.translation_utils.ProgressTracker resume/normalize | 写入重载 + 损坏容错 | 2（test_all #43-44） |
| core.translation_utils._filter_checked_translations | checker 过滤分流 | 1（test_all #45） |
| core.translation_utils._deduplicate_translations | 翻译去重 | 1（test_all #46） |
| core.translation_utils._match_string_entry_fallback | 四层 fallback 匹配 | 1（test_all #47） |
| core.api_client.is_reasoning_model | 推理模型检测 | 1（test_all #48） |
| main CLI 参数校验 | _positive_int/_positive_float/_ratio_float | 1（test_all #49） |
| core.api_client.APIConfig 推理 timeout | auto timeout ≥ 300s | 1（test_all #50） |
| core.glossary.extract_terms 连字符人名 | Mary-Jane 提取 | 1（test_all #51） |
| core.glossary._memory_count 信心度 | count=1 不输出 / count=2 输出 | 1（test_all #52） |
| file_processor.protect_placeholders 控制标签 | {w}/{p}/{nw}/{fast}/{cps=N}/{done} 保护+还原 | 1（test_all #53） |
| core.config.Config.validate | 类型/范围/未知键校验 | 1（test_all #71，4 子场景） |
| file_processor.validator E250/W460/W470 | 控制标签损坏 / 过度翻译 / 连续标点 | 集成于 validate_translation |
| core.translation_utils.TranslationCache | get/put/confidence/stats/thread_safety | 集成测试验证 |
| core.glossary.get_consistent_translation / _evict_low_frequency | 术语一致性 / 内存淘汰 | 集成测试验证 |

### 当前覆盖状态

| 模块/函数 | 状态 | 测试位置 |
|----------|------|---------|
| `protect_placeholders` / `restore_placeholders` | ✅ 已覆盖 | test_all #22-26 |
| `check_response_item` / `check_response_chunk` | ✅ 已覆盖 | test_all #27-36 |
| `_sanitize_translation` / `fill_translation` 边界 | ✅ 已覆盖 | tl_parser 内建（19 断言） |
| `calculate_dialogue_density` / `find_untranslated_lines` | ✅ 已覆盖 | test_all #37-39 |
| `TranslationDB` / `SKIP_FILES_FOR_TRANSLATION` | ✅ 已覆盖 | test_all #38-40 |
| RPA 解包 / rpyc 反编译 / lint 修复 / tl 去重 | ✅ 已覆盖 | 独立测试文件 |
| 端到端 tl-mode | ❌ 待补充 | T12：需 API |
| 端到端 retranslate | ❌ 待补充 | T13：需 API |
| 一键流水线端到端 | ❌ 待补充 | T14：需 API |
| GUI / build 流程 | ⚠ 仅手动 | `python gui.py` / `python build.py` |

### 下一步

T11-T14 端到端测试需 API key，建议作为 CI 可选步骤（手动触发）。GUI 和 build 流程继续保持手动验证。
