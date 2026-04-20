> 仅在修改校验逻辑或 API 调用逻辑时加载此文档。

# 翻译质量保障链 + API 集成

## 6.1 发送前保护

```
protect_placeholders()
  [name] → __RENPY_PH_0__
  {color=#f00} → __RENPY_PH_1__
  %(var)s → __RENPY_PH_2__
  → 按出现顺序全局去重，生成映射 list[(index, original)]
```

## 6.2 返回后校验（ResponseChecker）

```
check_response_item(item, placeholder_re=None, lang_config=None):
  ├─ 占位符集合一致性（原文 vs 译文）
  ├─ 原文非空 + 译文非空
  │   ├─ lang_config=None (r41 default): 硬编码读 item["zh"]
  │   └─ lang_config=<LanguageConfig>:  (r42 M2 phase-4 per-language)
  │        resolve_translation_field(item, lang_config) 按 alias
  │        链查 item[alias]；fallback 到 translation/target/trans 通用字段
  └─ 不通过 → status="checker_dropped"，保留原文

check_response_chunk():
  └─ 条数一致性（启发式 _count_translatable_lines_in_chunk）
```

**Round 42 M2 phase-4 per-language 化 (r42 d0404ff)**：
- 调用点 `engines/generic_pipeline.py::run_generic_pipeline` +
  `translators/tl_mode.py::_translate_one_tl_chunk` 传入 `lang_config`
- `_filter_checked_translations` 同样加 kwarg 透传
- `core.lang_config` import 在 checker 内是 **deferred**（只在 `if
  lang_config is not None:` 分支触发），保 r27 A-H-2 layering
  （`file_processor` 不在 module load 时 import `core`）

**Round 43-r44 检查器扩展**：
- r43 `test_check_response_item_zh_tw_rejects_generic_zh_field` 钉住
  zh-tw 的 `field_aliases = ["zh-tw", "zh_tw", "traditional_chinese"]`
  **刻意不含** bare "zh"（防 Simplified vs Traditional 脚本家族混淆）
- r44 `test_check_response_item_zh_tw_accepts_generic_translation_fallback`
  documents 另一半契约：若无任何 alias 匹配，fallback 到通用
  ``translation`` / ``target`` / ``trans`` 字段
- r44 `test_check_response_item_mixed_language_fields_picks_correct_alias`
  documents 多语言字段同时存在时的 first-match-wins 优先级契约

## 6.3 回写后校验（validate_translation，50+ 项）

| 类别 | 检查项 | Code |
|------|--------|------|
| 结构 | 行数一致性 | — |
| 结构 | 缩进保留 | — |
| 结构 | 关键字保留（label/screen/jump/call 等） | — |
| 变量 | `[var]` 缺失 | E210_VAR_MISSING |
| 变量 | `[var]` 多余 | W211_VAR_EXTRA |
| 标签 | `{tag}` 配对不一致 | E220_TEXT_TAG_MISMATCH |
| 菜单 | `{#id}` 标识符不一致 | E230_MENU_ID_MISMATCH |
| 格式化 | `%(name)s` 占位符不一致 | E240_FMT_PLACEHOLDER_MISMATCH |
| 顺序 | 占位符顺序偏差（仅 warning） | W251_PLACEHOLDER_ORDER |
| 术语 | 锁定术语未使用规定译名 | E411_GLOSSARY_LOCK_MISS |
| 术语 | 禁翻片段被修改 | E420_NO_TRANSLATE_CHANGED |
| 长度 | 译文长度比例异常（<0.15 或 >2.5） | W430_LEN_RATIO_SUSPECT |
| 风格 | 模型自我描述片段 | W440_MODEL_SPEAKING |
| 风格 | 中英标点连续混用 | W441_PUNCT_MIX |
| 风格 | 中文字符占比极低 | W442_SUSPECT_ENGLISH_OUTPUT |
| 控制标签 | Ren'Py 控制标签损坏 | E250_CONTROL_TAG_DAMAGED |
| 过度翻译 | Ren'Py 关键字被翻译 | W460_POSSIBLE_OVERTRANSLATION |
| 标点 | 连续中文标点 | W470_CONSECUTIVE_PUNCTUATION |

## 6.4 数据采集与归因

- **per-chunk 指标**：report.json → chunk_stats（expected / returned / dropped 三元组）
- **漏翻归因**：`attribute_untranslated()` → 四分类：AI 未返回（~71%）/ 回写失败（~28%）/ Checker 丢弃（~1%）/ 未知
- **translation_db** 记录每条翻译的完整元数据，支持增量归因查询

## 7.1 支持的提供商

xAI / OpenAI / DeepSeek / Claude / Gemini 五大提供商 + 自定义引擎插件（`--provider custom --custom-module`）。精确定价表在 `core/api_client.py` 的 `_MODEL_PRICING`。→ 详见 README §支持的API

## 7.2 JSON 解析容错链（6 级降级）

1. 直接 `json.loads()`
2. 从 Markdown 代码块提取 ` ```json...``` `
3. 搜索第一个 `[` 到最后一个 `]`
4. 修复尾部逗号
5. 正则逐项提取 JSON 对象
6. 字段顺序容错

## 7.3 速率控制

- `RateLimiter`：线程安全的 RPM + RPS 双重限制
- 指数退避重试：429/5xx 自动重试，jitter 随机抖动，优先 `Retry-After` 头，退避上限 60s
- `UsageStats`：线程安全的 token 用量 + 费用实时统计
- 推理模型检测：reasoning model 的 thinking tokens 按 3-5× 计费

## 7.4 资源边界与 OOM 防护

**Round 37-r44 累积 21+ 个 50 MB size caps** 为所有用户面 +
内部 JSON/text loader 提供 OOM 防护。合法文件（< 50 MB，典型 KB
到低 MB 范围）行为完全不变；adversarial / misconfigured 的超大文件
被 warning + fallback 处理。详细清单见 [constants.md](constants.md)
"内存 OOM 防护" section。

**插件子进程三通道防护**（`--sandbox-plugin` 模式）：
- **stdout**：`_MAX_PLUGIN_RESPONSE_CHARS = 50M chars` 单行上限
  （r43 + r44 char-vs-byte 澄清）— text-mode readline 按字符数
  bound，CJK 响应最坏字节 ~150 MB
- **stderr**：`stderr.read(10_000)` 10 KB 字符（r30）crash-diag 取尾 600 字符
- **stdin**：由 `_SHUTDOWN_REQUEST_ID = -1` 控制 lifecycle（不是
  attack-surface bound，而是 close timing 防 plugin hang）

**HTTP 响应体**：`MAX_API_RESPONSE_BYTES = 32 MB`（r22），`read_bounded`
共享工具统一 pool + urllib 双路径。

**Round 44 自审 21/21 全覆盖达成**（r37 × 4 + r38 × 4 + r39 × 3 +
r42 × 7 + r43 × 1 + r44 × 3 overlooked 补齐）。
