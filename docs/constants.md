> 仅在调整阈值或常量时加载此文档。

# 可配置常量速查

## 校验相关

| 常量 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `MODEL_SPEAKING_PATTERNS` | file_processor/checker.py | 7 条模式 | W440 模型自述检测关键词 |
| `PLACEHOLDER_ORDER_PATTERNS` | file_processor/checker.py | 4 组 (regex, name) | W251 占位符顺序提取 |
| `MIN_CHINESE_RATIO` | file_processor/validator.py | 0.05 | W442 中文占比阈值 |
| `LEN_RATIO_LOWER / UPPER` | pipeline/helpers.py | 0.15 / 2.5 | W430 长度异常阈值 |

## 翻译流程相关

| 常量 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `SKIP_FILES_FOR_TRANSLATION` | file_processor/checker.py | `{define, variables, screens, earlyoptions, options}.rpy` | 跳过翻译的配置文件 |
| `CHECKER_DROP_RATIO_THRESHOLD` | core/translation_utils.py | 0.3 | chunk 丢弃率重试阈值 |
| `MIN_DROPPED_FOR_WARNING` | core/translation_utils.py | 3 | 最小丢弃数触发警告 |
| `MIN_DIALOGUE_LENGTH` | core/translation_utils.py | 4 | 定向翻译最小对话长度 |
| `MAX_MEMORY_ENTRIES` | core/glossary.py | 10000 | 翻译记忆最大条目数 |
| `SAVE_INTERVAL` | core/translation_utils.py | 10 | 批量写入间隔（每 N 次 mark 写磁盘） |
| `_PH_TOKEN_RE` | core/translation_utils.py | `__RENPY_PH_\d+__` | 占位符令牌正则 |
| `_QUOTE_STRIP_PAIRS` | translators/tl_parser.py | ASCII "" / 弯引号 "" / 全角 ＂＂ | fill_translation 引号剥离对 |
| 截断匹配阈值 | file_processor/patcher.py:414 | 0.7 | AI 截断文本匹配阈值 |

## 流水线相关

| 常量 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `RISK_KEYWORDS` | pipeline/helpers.py | 14 个关键词 | 试跑文件风险评分 |
| `MAX_FILE_RANK_SCORE` | pipeline/helpers.py | 200 | 文件大小评分上限 |
| `RISK_KEYWORD_SCORE` | pipeline/helpers.py | 80 | 风险关键词加分 |
| `SAZMOD_BONUS_SCORE` | pipeline/helpers.py | 30 | SAZMOD 模组额外加分 |

## 文本分析相关

| 常量 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `MIN_UNTRANSLATED_TEXT_LENGTH` | translators/renpy_text_utils.py | 20 | 漏翻检测最小文本长度 |
| `MIN_ENGLISH_CHARS_FOR_UNTRANSLATED` | translators/renpy_text_utils.py | 12 | 漏翻检测最小英文字符数 |
| `_MODEL_PRICING` | core/api_client.py | ~20 个模型 | 精确定价表 |

## 内存 OOM 防护 — 50 MB 文件大小上限

Round 37-r44 累积添加的 `stat().st_size` gate，为所有用户面 + 内部
JSON/text loader 提供内存 OOM 防护。每个 loader 在 `json.loads`
(或 `read_text()`) 前检查文件大小，超限则 warning + fallback
（skip / return empty / raise to outer handler）。合法文件（< 50 MB）
行为完全不受影响；attacker-crafted 或 misconfigured 的超大文件
（如误指 `--config` 到一个 1 GB 数据库 dump）被 bounded。

**阈值选择 rationale**：
- 50 MB 远超任何 legitimate 场景（典型 `translation_db.json` 几百
  KB；游戏 RPG Maker `Map001.json` 低 MB；glossary 几十 KB）
- 50 MB 也是 `urllib` / HTTP 响应读取的合理内存上限（匹配
  `core/api_client.py::MAX_API_RESPONSE_BYTES = 32 MB` 的同量级）
- 每个 loader 各自定义独立的 `_MAX_*_SIZE` 常量而非共享 helper —
  保持 r27 A-H-2 layering 规则（`file_processor` 不 import `core`），
  同时每个 module 可独立调阈值

### User-facing loaders（operator-supplied path）

| 常量 | 位置 | 轮次 | 说明 |
|------|------|------|------|
| `_MAX_FONT_CONFIG_SIZE` | core/font_patch.py | r37 M2 | `load_font_config` |
| `_MAX_TRANSLATION_DB_SIZE` | core/translation_db.py | r37 M2 | `TranslationDB.load` (schema v2 envelope 入口) |
| `_MAX_V2_ENVELOPE_SIZE` | tools/merge_translations_v2.py | r37 M2 | `_load_v2_envelope` |
| `_MAX_V2_APPLY_SIZE` (→ `_MAX_EDITOR_INPUT_SIZE`) | tools/translation_editor.py | r37 M2 / r38 C2 rename | `_apply_v2_edits` + r38 扩 `_extract_from_db` + `import_edits` |
| `_MAX_CONFIG_FILE_SIZE` | core/config.py | r38 C2 | `_load_config_file` |
| `_MAX_GLOSSARY_JSON_SIZE` | core/glossary.py | r38 C2 | 4 JSON loader 共享 helper `_json_file_too_large` |
| `_MAX_REVIEW_DB_SIZE` | tools/review_generator.py | r39 M2 phase-2 | `generate_review_html` |
| `_MAX_ANALYZE_DB_SIZE` | tools/analyze_writeback_failures.py | r39 M2 phase-2 | `analyze` |
| `_MAX_GATE_GLOSSARY_SIZE` | pipeline/gate.py | r39 M2 phase-2 | gate glossary 加载（落 malformed-glossary 降级分支） |
| `_MAX_RPGM_JSON_SIZE` | engines/rpgmaker_engine.py | r42 M2 phase-3 | `extract_texts` + writeback（2 sites，user game_dir） |
| `_MAX_CSV_JSON_SIZE` | engines/csv_engine.py | r44 audit-tail | `_extract_jsonl` + `_extract_json_or_jsonl`（2 sites） |
| `_MAX_GUI_CONFIG_SIZE` | gui_dialogs.py | r44 audit-tail | `_load_config` dialog-picked JSON |
| `_MAX_UI_WHITELIST_SIZE` | file_processor/checker.py | r44 audit-tail | `load_ui_button_whitelist` (inline in function body) |

### Internal loaders（pipeline-generated / progress file）

| 常量 | 位置 | 轮次 | 说明 |
|------|------|------|------|
| `_MAX_PROGRESS_JSON_SIZE` | engines/generic_pipeline.py | r42 M2 phase-3 | `_load_progress` (generic_pipeline 进度) |
| `_MAX_PROGRESS_JSON_SIZE` | core/translation_utils.py | r42 M2 phase-3 | `ProgressTracker._load` |
| `_MAX_PROGRESS_JSON_SIZE` | translators/_screen_patch.py | r42 M2 phase-3 | `_load_progress` (screen 翻译进度) |
| `_MAX_REPORT_JSON_SIZE` | pipeline/stages.py | r42 M2 phase-3 | `tl_mode_report.json` + `report.json`（2 sites） |

## 其他内存 / 资源上限

| 常量 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `MAX_API_RESPONSE_BYTES` | core/api_client.py | 32 MB | r22 HTTPS 响应体上限（`read_bounded` 共享工具） |
| `_MAX_PLUGIN_RESPONSE_CHARS` | core/api_plugin.py | 50M chars | r43 / r44 plugin subprocess stdout per-line cap（**chars 不是 bytes** — Popen text mode；CJK 响应最坏字节 ~150 MB） |
| `_MAX_PLUGIN_RESPONSE_BYTES` (deprecated alias) | core/api_plugin.py | = `_MAX_PLUGIN_RESPONSE_CHARS` | r43 原 name，r44 保留作 backward-compat alias |
| plugin stderr `read(10_000)` | core/api_plugin.py | 10 KB chars | r30 crash-diag cap（取尾 600 字符显示） |
| `MAX_LOG_LINES` / `TRIM_TO` | gui_pipeline.py | 5000 / 3000 | r41 GUI 日志 Text widget 行数上限 / 裁剪目标 |

## API 调用默认参数（`core/api_client.py::APIConfig`）

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `rpm` | 0 | 每分钟请求数；0 = 不限（由用户通过 `--rpm` 覆盖） |
| `rps` | 0 | 每秒请求数；0 = 不限 |
| `timeout` | 180.0 秒 | 整文件翻译需要较长超时；推理模型（grok-reasoning / gpt-o3 / claude thinking）自动提升到 ≥ 300.0 秒 |
| `temperature` | 0.1 | 低温保证翻译一致性；某些推理模型不接受，需手工调 |
| `max_retries` | 5 | 429/5xx 自动重试次数上限 |
| `max_response_tokens` | 32768 | response 的最大 token 数（供 API 的 max_tokens 参数） |
| `sandbox_plugin` | False | r28 S-H-4 opt-in；True 时自定义引擎 plugin 走 JSONL subprocess sandbox |
| `use_connection_pool` | True | r21 HTTPS 连接池（节省典型 600 次调用 ~90 秒握手） |

## 速率限制 + 退避重试

| 常量 / 行为 | 位置 | 说明 |
|------|------|------|
| RPM / RPS 双重限制 | `core/api_client.py::RateLimiter` | 线程安全；`_second_counts` 批量清理策略（r21 PF-H-1：r21 → N 次获取清一次 vs 每次都清） |
| 429 / 5xx 自动重试 | `core/api_client.py::translate` | 指数退避 + jitter；优先 `Retry-After` 响应头；退避上限 60 秒 |
| 断路器 (circuit breaker) | — | 未实现；依赖 provider 侧限流 + 本地 `max_retries` |

## 模型定价表 `_MODEL_PRICING`

位置：`core/api_client.py:30`。精确匹配优先、按 model name 前缀 fallback、最终 `(input, output, False)` unknown 降级。涵盖 xAI (grok) / OpenAI (gpt-*) / DeepSeek (deepseek-chat) / Claude (claude-sonnet / haiku / opus) / Gemini (gemini-2.5-flash / pro)。reasoning models 的 thinking tokens 按 3-5× 计费。

## Chunk / Pipeline 默认参数

| 字段 / 常量 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `--workers` (chunk 级并发) | `main.py` argparse | 3 | 同一文件内 chunk 并发翻译数 |
| `--file-workers` (文件级并发) | `main.py` argparse | 1 | 同时翻译的文件数；r21 ProgressTracker 双锁解串行让其可 > 1 |
| `max_chunk_tokens` | `main.py` argparse | 4000 | chunk 切分上限；超过则 `_force_split` |
| `min_dialogue_density` | `main.py` argparse | 0.20 | 低于此密度的文件降级为 `targeted` 模式（r12） |
| `--pilot-count` (四阶段流水线) | `main.py` argparse | 20 | 试跑文件数 |
| `--gate-max-untranslated-ratio` | `main.py` argparse | 0.08 | 闸门最大漏翻比阈值 |
| `CHECKER_DROP_RATIO_THRESHOLD` | core/translation_utils.py | 0.3 | chunk 丢弃率超过此触发重试 |
| `MIN_DROPPED_FOR_WARNING` | core/translation_utils.py | 3 | 最小丢弃数触发警告（防小 chunk 丢 1 条就报警） |
| `SAVE_INTERVAL` | core/translation_utils.py | 10 | ProgressTracker 批量写入间隔（每 N 次 mark 写磁盘） |

## 语言配置（`core/lang_config.py::LANGUAGE_CONFIGS`）

| 语言 code | `field_aliases` | `min_target_ratio` | `native_name` |
|----------|----------------|------------------|---------------|
| `zh` | `["zh", "chinese", "cn"]` | 0.05 | 简体中文 |
| `zh-tw` | `["zh-tw", "zh_tw", "traditional_chinese"]` | 0.05 | 繁體中文（**刻意不含 bare "zh"**，防 Simplified vs Traditional 混淆 — r43/r44 tests pinned） |
| `ja` | `["ja", "japanese", "jp"]` | 0.05 | 日本語 |
| `ko` | `["ko", "korean", "kr"]` | 0.05 | 한국어 |

`resolve_translation_field(item, lang_config)` 按 `field_aliases` 顺序查找；都不匹配时 fallback 到 generic `["translation", "target", "trans"]`。r42 checker per-language 化后被 `check_response_item(lang_config=)` 和 `_filter_checked_translations(lang_config=)` 调用。
