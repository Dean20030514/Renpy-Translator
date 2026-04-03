> 仅在修改或新增校验规则时加载此文档。

# Warning / Error Code 索引

**处理原则**：E 级错误 → 丢弃翻译保留原文；W 级警告 → 保留翻译但记录日志。

| Code | 级别 | 含义 | 处理 |
|------|------|------|------|
| E210_VAR_MISSING | error | 译文缺少原文中的 `[var]` 变量 | 丢弃翻译 |
| W211_VAR_EXTRA | warning | 译文含原文没有的 `[var]` 变量 | 保留但告警 |
| E220_TEXT_TAG_MISMATCH | error | `{tag}` 配对不一致 | 丢弃翻译 |
| E230_MENU_ID_MISMATCH | error | `{#id}` 菜单标识符不一致 | 丢弃翻译 |
| E240_FMT_PLACEHOLDER_MISMATCH | error | `%(name)s` 格式化占位符不一致 | 丢弃翻译 |
| W251_PLACEHOLDER_ORDER | warning | 占位符顺序与原文不一致（集合相同） | 仅告警，仍 apply |
| W410_GLOSSARY_MISS | warning | 术语表未命中 | 告警 |
| E411_GLOSSARY_LOCK_MISS | error | 锁定术语未使用规定译名 | 标记错误 |
| E420_NO_TRANSLATE_CHANGED | error | 禁翻片段被修改 | 标记错误 |
| W430_LEN_RATIO_SUSPECT | warning | 译文长度比例异常 | 告警 |
| W440_MODEL_SPEAKING | warning | 模型自我描述/多余解释 | 告警 |
| W441_PUNCT_MIX | warning | 中英标点连续混用 | 告警 |
| W442_SUSPECT_ENGLISH_OUTPUT | warning | 中文占比极低，疑似未翻译 | 告警 |
| E250_CONTROL_TAG_DAMAGED | error | Ren'Py 控制标签在译文中缺失 | 标记错误 |
| W460_POSSIBLE_OVERTRANSLATION | warning | Ren'Py 关键字可能被过度翻译 | 告警 |
| W470_CONSECUTIVE_PUNCTUATION | warning | 连续中文标点（。。、！！） | 告警 |
