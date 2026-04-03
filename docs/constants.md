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
