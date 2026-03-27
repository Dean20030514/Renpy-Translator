# CHANGELOG v2

本文档记录本轮对「Renpy汉化（我的）」项目的全部改动。
按迭代轮次组织，每轮按类型（功能 / 增强 / 修复）分组。

---

## 改动总览

| 轮次 | 主题 | 核心成果 |
|------|------|----------|
| 第一轮 | 质量校验体系 | W430/W440/W441/W442/W251 告警 + E411/E420 术语锁定 |
| 第二轮 | 功能增强 | 结构化报告 + translation_db + 字体补丁 |
| 第三轮 | 降低漏翻率 | 12.12% → 4.01%（占位符保护 + 密度自适应 + retranslate） |
| 第四轮 | tl-mode | 独立 tl_parser 解析器 + 并发翻译 + 精确回填 |
| 第五轮 | tl-mode 全量验证 | 引号剥离修复 + 后处理 + 99.97% 翻译成功率 |
| 第六轮 | 代码优化与新功能 | chunk重试 + logging + 模块拆分 + 术语提取 + 退避优化 + show修复 |

---

## 第一轮：质量校验体系

### 新增功能

| # | 描述 | 涉及文件 | Code | 影响 |
|---|------|----------|------|------|
| 1 | 译文长度比例异常告警：原文 ≥ 20 字且译文 ≥ 5 字时，比例超区间触发 warning | `file_processor.py` | W430 | 新增告警 |
| 2 | 术语锁定（`locked_terms`）与禁翻片段（`no_translate`）：glossary.json 新增字段，Prompt / 校验 / 闸门联动 | `glossary.py`, `prompts.py`, `file_processor.py`, `main.py`, `one_click_pipeline.py` | E411, E420 | 新增错误（仅当配置时生效） |
| 3 | 翻译风格规则检查：模型自述、标点混用、中文占比极低 | `file_processor.py` | W440, W441, W442 | 新增告警 |
| 4 | 占位符顺序校验：集合一致前提下比较顺序，不一致仅 warning，仍 apply | `file_processor.py` | W251 | 语义变更：无检测 → 仅告警 |
| 5 | tl 优先模式（`--tl-priority`）：启用时仅翻译 `tl/` 下的 .rpy | `main.py` | — | 默认不启用 |
| 6 | strings 统计视图（`collect_strings_stats`）：统计 translate strings 块翻译情况 | `one_click_pipeline.py` | — | 仅新增统计 |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 7 | `validate_translation` 支持可配置 `len_ratio_lower` / `len_ratio_upper` | `file_processor.py`, `one_click_pipeline.py` | 默认行为不变 |
| 8 | `MODEL_SPEAKING_PATTERNS` / `PLACEHOLDER_ORDER_PATTERNS` 提升为模块级常量 | `file_processor.py` | 可配置化 |
| 9 | `evaluate_gate` 传入 glossary 参数，保证闸门统计与 main 行为一致 | `one_click_pipeline.py` | 闸门统计更完整 |
| 10 | 闸门打印增加 W430 / W251 统计 | `one_click_pipeline.py` | 仅输出增强 |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 11 | `prompts.py` 花括号转义（`{标签}` → `{{标签}}`） | `prompts.py` | 防止 Python format 报错 |
| 12 | E420 错误消息引号转义修正 | `file_processor.py` | 仅展示修正 |

### 文档

| # | 描述 | 涉及文件 |
|---|------|----------|
| 13 | Prompt 补充锁定术语 / 禁翻片段 / 占位符顺序规范 | `prompts.py` |
| 14 | 代码注释：W251 语义变更（仅告警仍 apply） | `file_processor.py` |
| 15 | 代码注释：locked_terms 应少而精 | `glossary.py` |

---

## 第二轮：功能增强

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 16 | 结构化报告 `report_summary.md`（三级判定绿/黄/红，warning code 分布） | `one_click_pipeline.py` | 仅新增输出 |
| 17 | `TranslationDB` 增量翻译元数据存储（upsert 去重，按 status/file/stage 筛选） | `translation_db.py` | 新增模块 |
| 18 | 自动字体补丁（`--patch-font` + `font_patch.py`）：`resolve_font` + `apply_font_patch` 修改 gui.rpy | `font_patch.py`, `main.py`, `one_click_pipeline.py` | 默认不启用 |
| 19 | README 组合式工作流推荐（4 种模式） | `README.md` | 仅文档 |

---

## 第三轮：降低漏翻率（12.12% → 4.01%）

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 20 | 占位符保护 / 还原（`protect_placeholders` / `restore_placeholders`，令牌 `__RENPY_PH_N__`） | `file_processor.py` | 发送前保护，返回后还原 |
| 21 | `ResponseChecker`：`check_response_item`（占位符集合 + 非空）+ `check_response_chunk`（条数一致） | `file_processor.py` | 不通过则丢弃，保留原文 |
| 22 | Checker 丢弃逻辑：status = `"checker_dropped"` 写入 translation_db | `main.py`, `file_processor.py` | 归因可追溯 |
| 23 | 密度自适应翻译策略：`calculate_dialogue_density()` < 20% 的文件走 `_translate_file_targeted()` 定向翻译 | `main.py` | 行为变更：低密度文件不再整文件发送 |
| 24 | 配置文件跳过名单 `SKIP_FILES_FOR_TRANSLATION`：define / variables / screens / options / earlyoptions.rpy | `file_processor.py`, `main.py`, `one_click_pipeline.py` | 行为变更：跳过翻译和漏翻统计 |
| 25 | 补翻模式 `--retranslate`：`find_untranslated_lines` 检测残留英文 → `build_retranslate_chunks`（≤ 20 行 + ±3 上下文）→ 专用 prompt → 原地回写 | `main.py`, `prompts.py` | 新增 CLI 模式 |
| 26 | `find_untranslated_lines` 二次过滤：排除 auto / hover / idle / image 路径 / screen 属性行 | `main.py` | 减少假阳性 |
| 27 | 漏翻归因分析：per-chunk 指标（expected / returned / dropped）+ `attribute_untranslated`（AI 未返回 / Checker 丢弃 / 回写失败 / 未知） | `main.py`, `one_click_pipeline.py` | 仅新增统计 |
| 28 | Pipeline Stage 3 改为 retranslate 原地补翻（替代旧的增量翻译 + merge 覆盖） | `one_click_pipeline.py` | 架构变更 |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 29 | translate strings 专用回写路径（`_parse_strings_blocks` + `_apply_strings_translations`） | `main.py` | 提升 strings 块回写成功率 |
| 30 | original 对齐（`_align_original_with_file`，两层匹配：完全相等 + 前缀后缀 ≥ 0.8） | `main.py` | 提升行号对齐精度 |
| 31 | 原地补翻 `.bak` 自动备份（不覆盖已有备份） | `main.py` | 安全增强 |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 32 | `translate_file` 早退路径返回值不一致（`0, []` → `0, [], 0, []`） | `main.py` | 修复潜在解包错误 |
| 33 | `retranslate_file` 中 `ph_mapping` 类型错误（`list[tuple]` 当 `dict` 调用 `.items()`） | `main.py` | 修复含占位符行崩溃 |
| 34 | `retranslate_file` 中 AI 返回带角色名前缀导致匹配失败 | `main.py` | 补翻回写成功率从 ~0% 恢复正常 |
| 35 | Pipeline Stage 3 增量覆盖丢翻译的结构性缺陷（删除 `merge_incremental_results`） | `one_click_pipeline.py` | 架构修复 |

### 验证数据（The Tyrant, ~140 文件）

| 阶段 | 漏翻率 | 关键改动 |
|------|--------|----------|
| 基线 | 12.12% | 无 |
| + 占位符保护 + checker | 10.40% | 挽回校验拦住的条目 |
| + 密度自适应 + retranslate | **4.01%** | 低密度文件定向翻译 |

漏翻归因：AI 未返回 71.1% / 回写失败 28.1% / Checker 丢弃 0.8%

---

## 第四轮：tl-mode 翻译模式

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 36 | `tl_parser.py` 独立解析模块：状态机（IDLE / DIALOGUE / STRINGS / SKIP）、`DialogueEntry` / `StringEntry` / `TlParseResult` 数据类、UTF-8 BOM 处理、56 个内建测试 | `tl_parser.py` | 新增模块 |
| 37 | `--tl-mode` + `--tl-lang` CLI 参数：扫描 `tl/<lang>/` 空槽位，AI 翻译后精确回填 | `main.py` | 新增模式，与 `--retranslate` 互斥 |
| 38 | tl-mode 专用 Prompt：`TLMODE_SYSTEM_PROMPT` + `build_tl_system_prompt` + `build_tl_user_prompt` | `prompts.py` | 新增模板 |
| 39 | `run_tl_pipeline`：`build_tl_chunks`（每 chunk ≤ 30 条）→ ThreadPoolExecutor 并发翻译 → 串行回填 | `main.py` | 新增功能（`--workers` 控制线程数） |
| 40 | `fill_translation` 行级精确回填：`str.replace` 只替换第一个 `""` → `"译文"`，保留缩进 / character 前缀 | `tl_parser.py` | 新增函数 |
| 41 | StringEntry 四层 fallback 匹配：精确 → strip 空白 → 去占位符令牌 → 转义规范化（`\"` → `"`、`\n` → 换行） | `main.py` | 提升匹配率 |
| 42 | start_launcher.py 新增模式 5/6：tl-mode 从头 / 断点续跑，含 `--workers` 参数 | `start_launcher.py` | 新增菜单选项 |
| 43 | 独立进度文件 `tl_progress.json`：chunk 级断点续传 | `main.py` | 支持 `--resume` |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 44 | `run_tl_pipeline` id 字段占位符还原：`restore_placeholders` 覆盖 `id` / `original` / `zh` 三个字段 | `main.py` | 修复 StringEntry 匹配失败 |
| 45 | tl 优先回退 warning 增加路径提示 | `main.py` | 便于排查 |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 46 | start_launcher.py 重复"并发线程数"提示：tl-mode 和 direct-mode 各自独立询问 | `start_launcher.py` | UX 修复 |

### 小规模验证数据（3 文件 / 135 条）

- 匹配率：97.8%（132/135），Checker 丢弃 0 条
- 缩进/引号/character 前缀：100% 正确
- 占位符保留：13/13 个 `[var]` 全部保留
- 未匹配 3 条：含 `\n` 多行 UI 按钮文本（AI 未返回）
- id 占位符还原修复后：93.3% → 97.8%（挽回 6 条）
- 费用：$0.0034（5 请求，grok-4-1-fast-reasoning）

---

## 第五轮：tl-mode 全量验证 & 修复

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 47 | `fill_translation` 引号剥离保护：循环剥离外层引号（ASCII `""` / 弯引号 `""` / 全角 `＂＂`），防止 `""text""` 格式错误 | `tl_parser.py` | 修复 14% 的译文格式问题 |
| 48 | `_QUOTE_STRIP_PAIRS` 提升为模块级常量 | `tl_parser.py` | 性能优化 |
| 49 | `_sanitize_translation` 完善：元数据泄漏清理 + 循环引号剥离 + 单侧残存处理 + 内嵌引号转义 | `tl_parser.py` | 全面的译文清理 |
| 50 | `postprocess_tl_file` / `postprocess_tl_directory`：翻译后修复 Ren'Py 兼容性问题（移除 translate 块内 `nvl clear`、空块补 `pass`） | `tl_parser.py` | 新增后处理 |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 51 | `fill_translation` 双引号 bug：AI 返回带引号译文时回填产生 `""text""`，增加三对引号剥离 | `tl_parser.py` | 10,402/74,002 条受影响，修复后 0 格式错误 |

### 全量验证数据（The Tyrant, 107 文件, 10 线程）

| 指标 | 数值 |
|------|------|
| 总槽位 | 76,169（75,993 对话 + 176 字符串） |
| 待翻译 | 74,044（73,868 对话 + 176 字符串） |
| **翻译成功** | **74,019（99.97%）** |
| 未翻译 | 25 条（命名输入框 / 转义引号 / AI 未返回） |
| Checker 丢弃 | 4 条 |
| API 请求 | 2,541 次 |
| Token 用量 | 输入 4.09M / 输出 3.83M |
| 费用 | $2.73（grok-4-1-fast-reasoning） |
| 耗时 | 73.1 分钟 |
| 引号 bug 影响 | 10,402/74,002 条（14%），修复后 0 格式错误 |

---

## 第六轮：代码优化与新功能

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 34 | `_translate_chunk_with_retry`: chunk 翻译自动重试，API 错误或丢弃率 > 30% 时重试 1 次 | `main.py` | 降低 API 瞬时故障导致的漏翻 |
| 35 | `--verbose` / `--quiet` CLI 参数：控制日志级别（DEBUG/WARNING） | `main.py` | 新增 CLI 参数 |
| 36 | `setup_logging()`: 全局 logging 配置，支持文件输出 | `main.py` | 替代 print |
| 37 | `extract_terms_from_translations()`: 从翻译结果中自动提取高频专有名词（n-gram 共现分析）| `glossary.py` | 新增方法 |
| 38 | `auto_add_terms()`: 将提取的术语自动加入 glossary.terms | `glossary.py` | 新增方法 |
| 39 | Pipeline pilot 后自动术语提取：从 pilot 翻译结果提取人名/地名，供全量翻译使用 | `one_click_pipeline.py` | pipeline 增强 |
| 40 | Pipeline `--tl-mode` / `--tl-lang`：一键流水线支持 tl-mode（跳过试跑/补翻，直接 tl 翻译） | `one_click_pipeline.py`, `start_launcher.py` | 新增模式 |
| 41 | RENPY-020 规则：`show image:` 空 ATL 块修复（多行感知，仅删除无 ATL 块的冒号）| `renpy_upgrade_tool.py` | 新增升级规则 |
| 42 | chunk 上文上下文：split_file 的第 2+ chunk 附带前一 chunk 末尾 5 行 | `file_processor/splitter.py` | 提升跨块翻译连贯性 |
| 43 | `[MULTILINE]` 标记：tl-mode 中含 `\n` 的条目自动标记，提示 AI 保留换行 | `main.py`, `prompts.py` | 提升多行字符串翻译率 |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 44 | 429/5xx 退避优化：jitter 防雪崩 + 60s 上限 + Retry-After header 优先 | `api_client.py` | 多线程稳定性提升 |
| 45 | `file_processor.py` 拆分为 `file_processor/` 包（splitter/checker/patcher/validator + __init__.py re-export） | `file_processor/` | 可维护性，外部 import 不变 |
| 46 | 全模块 print → logging 迁移（main/file_processor/api_client/one_click_pipeline/glossary/font_patch） | 6 个文件 | 支持 --verbose/--quiet/--log-file |

### 修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 47 | validate_translation 中 `✓` Unicode 字符在 GBK 终端报错 → 改为 `OK` | `file_processor/validator.py` | 修复 Windows 终端编码错误 |
| 48 | StringEntry fallback 注释从"三层"修正为"四层"（精确→strip→去占位符→转义规范化） | `main.py` | 注释修正 |

---

## 已回滚

| 描述 | 原因 |
|------|------|
| Prompt 强制覆盖指令（CRITICAL RULE） | 降低 AI 返回率 5 个百分点，增量覆盖导致丢翻译 |
| 增量翻译 + merge 覆盖架构 | 两次翻译覆盖范围不一致时丢数据，被 retranslate 模式替代 |

---

## 配置项速查表

### CLI 参数（本轮新增）

| 参数 | 所在文件 | 默认值 | 说明 |
|------|----------|--------|------|
| `--tl-priority` | `main.py` | False | 仅翻译 `tl/` 下的 .rpy |
| `--retranslate` | `main.py` | False | 补翻模式：扫描残留英文行 |
| `--min-dialogue-density` | `main.py` | 0.20 | 低密度阈值（低于此值走定向翻译） |
| `--tl-mode` | `main.py` | False | tl 框架翻译模式 |
| `--tl-lang` | `main.py` | `chinese` | tl 语言子目录名 |
| `--patch-font` | `main.py` | False | 启用自动字体补丁 |
| `--font-file` | `main.py` | — | 指定字体文件路径 |
| `--verbose` | `main.py` | False | 日志级别设为 DEBUG |
| `--quiet` | `main.py` | False | 日志级别设为 WARNING |
| `--tl-mode`（pipeline） | `one_click_pipeline.py` | False | 一键流水线使用 tl-mode 翻译 |
| `--tl-lang`（pipeline） | `one_click_pipeline.py` | `chinese` | 一键流水线 tl 语言子目录名 |

### 模块级常量

| 常量 | 所在文件 | 默认值 | 说明 | 调整建议 |
|------|----------|--------|------|----------|
| `LEN_RATIO_LOWER` | `one_click_pipeline.py` | 0.15 | W430 译文长度比例下限 | 短句误报多可调低 |
| `LEN_RATIO_UPPER` | `one_click_pipeline.py` | 2.5 | W430 译文长度比例上限 | 译文偏长可调高 |
| `MODEL_SPEAKING_PATTERNS` | `file_processor.py` | 7 条模式 | W440 模型自述检测关键词 | 新套话可追加 |
| `PLACEHOLDER_ORDER_PATTERNS` | `file_processor.py` | 4 组 (regex, name) | W251 占位符顺序提取 | 新类型追加，具体 pattern 靠前 |
| `SKIP_FILES_FOR_TRANSLATION` | `file_processor.py` | 5 个文件名 | 跳过翻译的配置文件 | 按项目追加无对话文件 |
| `_QUOTE_STRIP_PAIRS` | `tl_parser.py` | 3 对引号 | fill_translation 引号剥离 | AI 返回新引号类型时追加 |

### 数据文件字段

| 字段 | 所在文件 | 默认值 | 说明 |
|------|----------|--------|------|
| `locked_terms` | `glossary.json` | `[]` | 锁定术语 key 列表，违反报 E411 |
| `no_translate` | `glossary.json` | `[]` | 禁翻片段列表，违反报 E420 |

---

## Warning / Error Code 完整索引

### Error（结构性错误）

| Code | 含义 | 处理 |
|------|------|------|
| E100_LINE_COUNT_MISMATCH | 翻译后行数与原文不一致 | 标记错误 |
| E110_INDENT_CHANGED | 缩进被修改 | 标记错误 |
| E120_NON_STRING_MODIFIED | 非字符串行被修改 | 标记错误 |
| E130_DQUOTE_MISMATCH | 双引号结构不一致 | 标记错误 |
| E131_SQUOTE_MISMATCH | 单引号结构不一致 | 标记错误 |
| E140_CODE_STRUCT_CHANGED | 代码结构被修改 | 标记错误 |
| E210_VAR_MISSING | 译文缺少原文中的 `[var]` 变量 | 标记错误 |
| E220_TEXT_TAG_MISMATCH | `{tag}` 配对不一致 | 标记错误 |
| E230_MENU_ID_MISMATCH | `{#id}` 菜单标识符不一致 | 标记错误 |
| E240_FMT_PLACEHOLDER_MISMATCH | `%(name)s` 格式化占位符不一致 | 标记错误 |
| E411_GLOSSARY_LOCK_MISS | 锁定术语未使用规定译名 | 标记错误 |
| E420_NO_TRANSLATE_CHANGED | 禁翻片段被修改 | 标记错误 |

### Warning（质量告警）

| Code | 含义 | 处理 |
|------|------|------|
| W211_VAR_EXTRA | 译文含原文没有的 `[var]` 变量 | 仅告警 |
| W251_PLACEHOLDER_ORDER | 占位符顺序与原文不一致（集合相同） | 仅告警，仍 apply |
| W310_ESCAPED_NL_MISMATCH | 转义换行符 `\n` 数量不一致 | 仅告警 |
| W410_GLOSSARY_MISS | 术语表未命中 | 仅告警 |
| W420_SUSPECT_UNTRANSLATED | 疑似漏翻（原文 = 译文且符合英文特征） | 仅告警 |
| W430_LEN_RATIO_SUSPECT | 译文长度比例异常（过短或过长） | 仅告警 |
| W440_MODEL_SPEAKING | 译文含模型自我描述或多余解释 | 仅告警 |
| W441_PUNCT_MIX | 中英标点连续混用 | 仅告警 |
| W442_SUSPECT_ENGLISH_OUTPUT | 中文字符占比极低 | 仅告警 |

---

## 关键发现与经验

1. **对话密度是漏翻率最强相关因子**：< 10% 密度文件漏翻中位数 57.69%，≥ 40% 仅 4.54%
2. **Prompt 强化无效甚至有害**：CRITICAL RULE 降低 AI 返回率 5pp，引入翻译不一致性
3. **tl-mode 精度远高于 direct-mode**：行号精确定位 vs 文本匹配回写，可消除"回写失败"类漏翻
4. **AI 约 14% 概率返回带外层引号**：ASCII / 弯引号 / 全角，需循环剥离
5. **旧增量架构有结构性缺陷**：两次翻译覆盖范围不一致时丢数据，retranslate 模式解决
6. **占位符保护对 Checker 通过率有显著正面影响**：从基线到 +2pp
