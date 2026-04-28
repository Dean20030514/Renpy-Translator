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

### Round 49 升级：TOCTOU defense via `core.file_safety.check_fstat_size`

R47-R49 累积扩展：path-based stat() 仅是 fast path；attacker 在 stat→open
之间扩文件可绕过 path-stat cap。R47 Step 2 D3 在 `csv_engine._extract_csv`
inline 加了 `os.fstat(f.fileno())` 二次校验（TOCTOU MITIGATED inline），
R48 Step 2 抽取为共享 helper `core/file_safety.py::check_fstat_size(file_obj,
max_size) -> tuple[bool, int]`（93 行 stdlib-only，fail-open on OSError /
ValueError），R49 C4-C5 把 helper 推广到全部 user-facing JSON loader。
**整个 user-facing JSON ingestion surface 现 26 sites / 12 modules 全
TOCTOU MITIGATED**（attack window 缩到 microsecond 级 fstat-on-fd）：

| 节点 | sites cumulative | 状态 |
|------|------------------|------|
| r46 audit | 0 | 4 ACCEPTABLE（csv 仅 path-based stat） |
| r47 Step 2 D3 | 1 (csv `_extract_csv` inline) | TOCTOU MITIGATED inline |
| r48 Step 2 | 3 (csv 3 readers via helper) | csv 全 MITIGATED |
| **r49 C4** | **15** (+12 core sites: font_patch / translation_db / config / glossary 4 / gate / rpgmaker 2 / gui_dialogs / checker) | core 全 MITIGATED |
| **r49 C5** | **26** (+11 tools+internal sites: merge_v2 / translation_editor 3 / review_generator / analyze_writeback / generic_pipeline / translation_utils / _screen_patch / stages 2) | **整个 user-facing JSON 全 MITIGATED** |

升级 pattern（与 csv_engine byte-equivalent — 上方 user-facing / internal
表中所有 r37-r44 的 path-based stat 仍然作为 fast path 保留，加 `with open
+ check_fstat_size + read` 内层 TOCTOU 二次校验）：

```python
fsize = path.stat().st_size           # path-based fast path (existing)
if fsize > _MAX_X_SIZE: warn + skip   # rejects huge files before open
with open(path, encoding=...) as f:
    ok, fsize2 = check_fstat_size(f, _MAX_X_SIZE)  # TOCTOU defense
    if not ok: warn TOCTOU + skip/return/continue/raise
    data = json.loads(f.read())
```

`core/glossary.py::_json_file_too_large(path)` helper **不动**（保留 r38
path-based fast path）；4 callers 各自 inline 加 fstat check 而非升级
helper signature。理由 (i) 与 csv_engine pattern byte-equivalent (ii) 保
留 path stat fast path 拒 100GB 文件不需 open (iii) caller 侧 fallback
行为差异（continue / return）难抽象。

**测试集中策略**：23 expansion regression 集中到 `tests/test_file_safety.py`
(12 C4) + `tests/test_file_safety_c5.py` (11 C5)，所有 mock 统一打
`core.file_safety.os.fstat`（防 r48 Step 3 mock target stale CRITICAL 重
演 — 单 grep `mock.patch.*os.fstat` 即可 audit 全部一致性）。其中 4
lightweight test (gate / gui_dialogs / stages × 2) 因 e2e fixture 太重，
用 import + constant + active_src filter（过滤 `#` 注释行）source-grep。

**Round 50 1b 扩展 success-path coverage（closes r49 audit Coverage MEDIUM 1）**：
8 个 expansion sites 加 ≤ cap 接受路径 regression（cap-exact mock）；
helper-level cap-1/cap-exact/cap+1 三件套 + site-level cap-exact 共
覆盖每 site 的 boundary 接受 vs 拒绝两条路径。

**Round 50 1f informational note — symlink TOCTOU defense-in-depth 候选**
（closes r49 audit Security LOW 2）：当前 r49 fstat helper 把
TOCTOU race window 收紧到 microsecond 级 fd-based fstat，但 POSIX
``open(link)`` 在 t0 解析 → relink → fstat 在 t2 sees inode_B 的
**path-swap symlink TOCTOU** 在理论上仍可触发（fd 已绑 inode_B 但
logged path 名仍是 link）。**当前 codebase 无 exploit vector** —— 用
户面 path 来自 ``Path.rglob()`` / ``Path(game_dir)`` 而非 user-supplied
symlink；CLI 参数全是 directory / file 路径无 symlink 入口。Future
hardening 候选：参考 r45 `build.py` 加 ``d.is_symlink()`` 检查模式
（commit `bd9d6e1`）— 任何接受外部 path CLI 参数的入口点可加
``Path.is_symlink()`` reject 防 path-swap。**不属于 r50+ 必做欠账**
（informational watchlist）。

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
