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
| 第六轮 | 代码优化与新功能 | chunk重试 + logging + 模块拆分 + 术语提取 + 退避优化 + show修复 + 全文扫描安全性 + 截断阈值提升 + tl_parser 测试扩充 |
| 第七轮 | 全量验证（第六轮改进） | 99.99% 成功率（未翻译 25→7，Checker 丢弃 4→2）；9 条遗漏全为边界 case |
| 第八轮 | 代码质量八阶段优化 | 消除重复 + 大函数拆分 + validator 结构化 + Magic Number 收敛 + except 精细化 + 测试 36→42 + LICENSE/pyproject.toml + CI 增强 |
| 第九轮 | 深度优化六阶段 | 线程安全修复 + 深层重复消除(`_filter_checked`/`_deduplicate`) + 性能O(1)fallback + API 404/401/推理timeout + 测试 42→50 + `has_entry`封装 |
| 第十轮 | 功能加固与生态完善 | 控制标签覆盖确认 + CI零依赖+dry-run + 跨平台路径 + Glossary连字符+信心度 + getpass安全输入 + README故障排查/调优/示例 + 测试 50→53 |
| 第十一轮 阶段一 | main.py 模块拆分 | main.py 2400→233 行，拆分为 direct_translator / retranslator / tl_translator / translation_utils 四个独立模块 + TranslationContext 闭包重构 |
| 第十一轮 阶段二+三 | 回写失败分析与修复 | diagnostic 记录 + analyze 工具 + 前缀剥离 + 转义引号正则 + 回写失败 609→28→~0 + 测试 53→55 |
| 第十一轮 阶段四 | config.json 配置文件 | Config 类（三层合并）+ resolve_api_key + renpy_translate.example.json + argparse default=None + 测试 55→58 |
| 第十一轮 阶段五 | Review HTML + 进度条 | ProgressBar（GBK/ASCII 自适应）+ review_generator.py（HTML 校对报告）+ direct_translator 集成 + 测试 58→60 |
| 第十一轮 阶段六 | 类型注解 | 全部公共 API 返回/参数注解 + py.typed PEP 561 + CI mypy informational |
| 第十一轮 阶段七 | 目标语言参数化 | LanguageConfig dataclass + 4 预置语言 + 文字检测 + resolve_translation_field + 测试 60→63 |
| 第十一轮 阶段八 | Prompt + Validator 多语言 | 中文/英文 prompt 分支 + W442 参数化 + 中文零变更验证 + 测试 63→66 |
| 第十二轮 | 阶段零四项优化 | chunk 截断自动拆分重试 + pipeline main() 拆分 + .rpyc 精确清理 + dry-run verbose 增强 + 测试 66→70 |
| 第十二轮 阶段一 | 引擎抽象层骨架 | EngineProfile + TranslatableUnit + EngineBase ABC + EngineDetector + RenPyEngine 薄包装 + `--engine` CLI + 引擎测试 25 个 |
| 第十二轮 阶段二 | CSV/JSONL + 通用流水线 | CSVEngine（CSV/TSV/JSONL/JSON 读写）+ generic_pipeline（6 阶段通用翻译）+ checker/prompts 参数化适配 + 引擎测试 25→47 |
| 第十二轮 阶段三 | RPG Maker MV/MZ | RPGMakerMVEngine（事件指令 401/405 合并 + 102 选项 + 8 种数据库 + System.json）+ glossary.scan_rpgmaker_database + 引擎测试 47→62 |
| 第十二轮 阶段四 | 文档 + 发布 | start_launcher.py 新增模式 8/9（RPG Maker / CSV）+ 全部文档更新 + 里程碑 M4 达成 |
| 第十二轮 结构整理 | 项目目录重构 | 根目录 .py 27→17：测试→tests/ + 工具→tools/ + 引擎抽象→engines/ 包合并 + import 路径更新 |
| 第十二轮 GUI | 图形界面 + 打包 | gui.py Tkinter GUI（3 Tab + 内嵌日志 + 命令预览 + 配置加载）+ build.py PyInstaller 打包（32MB 单文件 .exe） |

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
| 36 | `tl_parser.py` 独立解析模块：状态机（IDLE / DIALOGUE / STRINGS / SKIP）、`DialogueEntry` / `StringEntry` / `TlParseResult` 数据类、UTF-8 BOM 处理、75 个内建测试 | `tl_parser.py` | 新增模块 |
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
| 49 | 全文扫描安全性：第四遍 `apply_translations` 跳过已被前面 pass 修改的行（`modified_lines` + `full_scan`），防止同一原文多次出现时误替换 | `file_processor/patcher.py` | 降低回写错误 |
| 50 | 截断匹配阈值从 0.5 提高到 0.7（阶段 3e），减少 AI 截断文本误匹配 | `file_processor/patcher.py` | 提升匹配精度 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 51 | tl_parser 内建自测新增 19 个断言（56→75）：`_sanitize_translation` 12 个边界 + `fill_translation` 7 个边界 | `tl_parser.py` | 测试覆盖 |

---

## 第七轮：全量验证（第六轮 15 项改进）

### 验证数据（The Tyrant, 105 文件, 10 线程）

| 指标 | 第五轮（基线） | 第七轮（本次） | 变化 |
|------|---------------|----------------|------|
| 总槽位 | 76,169 | 76,225 | +56 |
| 待翻译 | 74,044 | 74,098 | +54 |
| **翻译成功** | **74,019（99.97%）** | **74,091（99.99%）** | **+72 条, +0.024pp** |
| 未翻译 | 25 | **7** | **-18（-72%）** |
| Checker 丢弃 | 4 | **2** | **-2（-50%）** |
| Fallback 匹配 | — | 3 | 新增指标 |
| API 请求 | 2,541 | 2,572 | +31 |
| Input tokens | 4.09M | 4.23M | +3.4%（chunk 上下文 5 行导致） |
| Output tokens | 3.83M | 3.83M | 持平 |
| 费用 | $2.73 | $2.76 | +$0.03（+1.1%） |
| 耗时 | 73.1 min | 82.3 min | +9.2 min |

### translation_db 质量

- 74,004 条全部 status=ok，**0 error、0 warning**
- 325 条原文=译文（同值保留），全部合理：拟声词 315 + 人名/格式标签 10
- 中文占比 ≥ 30% 的条目占 92.7%（68,241/73,639），其余为短文本/拟声词/占位符混合

### 9 条未翻译条目逐条追查

#### 2 条空对话 — 原文为单个空格

| 文件 | 源码行 | 原文 | 根因 |
|------|--------|------|------|
| `v06.rpy:3451` | `v06.rpy:1311` | `" "`（空格） | 原文无实际内容，是剧情中的空白停顿 |
| `v06.rpy:3733` | `v06.rpy:1408` | `" "`（空格） | 同上 |

#### 7 条空字符串 — 命名输入框 / 游戏标题 / UI 按钮

| 文件 | 原文 | 根因 |
|------|------|------|
| `living_room.rpy:8821` | `My name is... (default = Irina)` | 命名输入框提示，含括号说明 |
| `living_room.rpy:8825` | `Her name is... (default = Miranda` | 同上，且原文**右括号缺失**（原文 bug） |
| `options.rpy:7` | `The Tyrant` | 游戏标题，通常不翻译 |
| `subway.rpy:2581` | `Her name is... (default = Susan)` | 命名输入框 |
| `stats.rpy:7` | `close` | UI 按钮文本，单词过短 |
| `fitness_studio.rpy:6661` | `My name is... (If left blank, her name will be Vivian.)` | 命名输入框，含长括号说明 |
| `subway.rpy:5125` | `Her name is... (If left blank, her name will be Susan.)` | 同上 |

#### 根因分类

| 根因 | 条数 | 说明 |
|------|------|------|
| 原文为空格（无需翻译） | 2 | `" "` 空白停顿 |
| 命名输入框提示语 | 4 | 含 `(default = xxx)` 括号说明，AI 视为系统文本 |
| 游戏标题 | 1 | `The Tyrant` — 通常保留原名 |
| UI 按钮 | 1 | `close` — 单词过短被忽略 |
| 原文有 bug（括号未闭合） | 1 | `(default = Miranda` — 缺右括号 |

**结论**：9 条遗漏全为边界 case，0 条正常对话漏翻。其中 3 条（2 空格 + 1 标题）本就不应翻译，实际有意义的遗漏仅 6 条（0.008%）。

### 改进效果确认

| 改进项 | 效果验证 |
|--------|----------|
| chunk 自动重试 | Checker 丢弃 4→2（-50%），API 瞬时故障恢复有效 |
| `[MULTILINE]` 标记 | 含 `\n` 多行条目未翻译从上次的 3 条降至 0（不计入本次 9 条中） |
| chunk 上下文 5 行 | Input tokens +3.4%，翻译连贯性改善（无法量化但成本可控） |
| 429/5xx 退避优化 | 10 线程 82 分钟无中断完成，多线程稳定性验证通过 |
| logging 系统 | `--verbose`/`--quiet` 正常工作，日志可读性提升 |
| file_processor 包拆分 | 外部 import 无变化，功能完全兼容 |
| 全文扫描安全性 | 0 条回写错误（translation_db 0 error） |
| 截断匹配阈值 0.7 | 0 条误匹配（上次有少量截断匹配错误） |
| tl_parser 75 项测试 | 全部通过，引号剥离/清理/后处理回归安全 |

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

## 第八轮：代码质量八阶段优化

### 阶段一：错误处理加固（commit afb51e0）

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 52 | 8 处 `except Exception` 精细化为具体异常类型 | 多文件 | 更精确的错误处理 |
| 53 | `.tmp` 临时文件清理 | `main.py` | 进程安全性 |

### 阶段二：消除代码重复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 54 | 提取 `_restore_placeholders_in_translations()` 统一 4 处占位符还原逻辑 | `main.py` | 代码量 -20 行，维护点 4→1 |
| 55 | 提取 `_strip_char_prefix()` + `_CHAR_PREFIX_RE` 统一 2 处角色前缀清理 | `main.py` | 消除重复编译正则 |
| 56 | 提取 `_is_untranslated_dialogue()` + `_extract_dialogue_text()` 消除漏翻检测重复 | `one_click_pipeline.py` | 两个函数共享检测逻辑 |
| 57 | 删除 4 处冗余 `import re as _re`（模块级已有 `import re`） | `main.py` | 清理冗余 import |

### 阶段三：大函数拆分

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 58 | `one_click_pipeline.main()` 补翻阶段拆分为 `_run_retranslate_phase()` | `one_click_pipeline.py` | ~110 行独立函数 |
| 59 | `one_click_pipeline.main()` 最终报告拆分为 `_run_final_report()` | `one_click_pipeline.py` | ~120 行独立函数 |
| 60 | `run_tl_pipeline` 重试块使用 `_restore_placeholders_in_translations` 简化 | `main.py` | 消除 6 行重复代码 |

### 阶段四：validator 结构化拆分

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 61 | `validate_translation` 293 行拆为 4 个子检查函数 + 主入口调度 | `file_processor/validator.py` | 可读性大幅提升 |
|   | `_check_structural_integrity` — 缩进/非字符串行/引号结构/代码关键字 | | |
|   | `_check_placeholders_and_tags` — 变量/标签/菜单ID/格式化/顺序 | | |
|   | `_check_glossary_compliance` — 术语锁定/禁翻/漏翻疑似 | | |
|   | `_check_quality_heuristics` — 风格/长度比例/中文占比 | | |

### 阶段五：测试体系升级

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 62 | 新增 6 个集成测试（36→42）：密度自适应 / 跳过名单 / 漏翻检测 / TranslationDB 往返 / `_is_untranslated_dialogue` / `_restore_placeholders_in_translations` | `test_all.py` | 测试覆盖扩展 |
| 63 | CI 增加 `py_compile` 语法检查步骤（14 个 .py 文件） | `.github/workflows/test.yml` | CI 加固 |

### 阶段六：Magic Number 收敛

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 64 | `CHECKER_DROP_RATIO_THRESHOLD` / `MIN_DROPPED_FOR_WARNING` / `MIN_DIALOGUE_LENGTH` | `main.py` | 3 处硬编码→命名常量 |
| 65 | `MAX_FILE_RANK_SCORE` / `RISK_KEYWORD_SCORE` / `SAZMOD_BONUS_SCORE` / `MIN_UNTRANSLATED_TEXT_LENGTH` / `MIN_ENGLISH_CHARS_FOR_UNTRANSLATED` | `one_click_pipeline.py` | 5 处硬编码→命名常量 |
| 66 | `MIN_CHINESE_RATIO` | `file_processor/validator.py` | W442 阈值命名化 |

### 阶段七：项目工程化

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 67 | MIT LICENSE 文件 | `LICENSE`（新增） | 开源许可证 |
| 68 | `pyproject.toml`（name/version/requires-python/零依赖） | `pyproject.toml`（新增） | 项目元数据 |
| 69 | 4 处硬编码 Windows 路径改为环境变量可配置 | `test_single.py` / `verify_alignment.py` / `patch_font_now.py` / `revalidate.py` | 可移植性 |

### 阶段八：代码细节打磨

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 70 | 6 处 `except Exception:` 精细化为 `(KeyError, AttributeError, ValueError)` 等具体类型 | `api_client.py` / `glossary.py` / `translation_db.py` | 异常处理更精确 |
| 71 | `_SKIP_TOKENS` 常量提取（validator 中资源路径检测元组） | `file_processor/validator.py` | 可读性 |

---

## 第九轮：深度优化六阶段

### 阶段一：线程安全与健壮性加固

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 72 | 并发锁修复：`run_tl_pipeline` 的 `as_completed` 回调中 `n` → `n_completed` 局部变量，在锁内赋值锁外使用 | `main.py` | 消除潜在竞态 |
| 73 | CLI 参数校验：`_positive_int` / `_positive_float` / `_ratio_float` 三个校验函数，rpm/rps/timeout/max-chunk-tokens/max-response-tokens/min-dialogue-density 负值/零值防御 | `main.py` | 参数错误提前报错 |
| 74 | 词典文件提前校验：3 处 `load_dict` 前检查文件存在，不存在则 warning | `main.py` | 防静默忽略拼错路径 |
| 75 | ProgressTracker 规范化：`_load()` 捕获 JSON 损坏 + `setdefault` 确保必需 key | `main.py` | 防损坏文件 KeyError |

### 阶段二：深层代码重复消除

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 76 | `_filter_checked_translations()` 提取：checker 逐条过滤 + kept/dropped 分流（4 处→1 函数） | `main.py` | 消除 4 处重复 |
| 77 | `_deduplicate_translations()` 提取：`(line, original)` 去重（3 处→1 函数） | `main.py` | 消除 3 处重复 |

### 阶段三：性能优化

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 78 | `_build_fallback_dicts()` + `_match_string_entry_fallback()`：StringEntry 四层 fallback O(n*m)→O(1) 预建查找表 | `main.py` | 大项目性能提升 |
| 79 | ProgressTracker 批量写入：`SAVE_INTERVAL=10`，每 10 次 mark 才写磁盘 | `main.py` | 减少磁盘 I/O |

### 阶段四：API 兼容性加固

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 80 | 空 choices 响应显式 warning（不再静默返回空字符串） | `api_client.py` | 更好的错误诊断 |
| 81 | HTTP 404 → 立即报错"模型不存在"（不重试）；HTTP 401 → 立即报错"认证失败" | `api_client.py` | 避免无意义重试 |
| 82 | 推理模型自动 timeout 提升：`is_reasoning_model()` 检测到时 timeout 从 180s 提升到 300s | `api_client.py` | 推理模型稳定性 |

### 阶段五：测试深度覆盖

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 83 | 新增 8 个测试（42→50）：progress resume/normalize、`_filter_checked_translations`、`_deduplicate_translations`、`_match_string_entry_fallback`、推理模型检测、CLI 参数校验、推理模型 timeout | `test_all.py` | 测试覆盖扩展 |

### 阶段六：文档与代码卫生

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 84 | `TranslationDB.has_entry()` 公共方法替代 `_index` 直接访问 | `translation_db.py` `main.py` | 封装性 |
| 85 | 过期注释修正（"外部模板" → "术语表 + 项目名"） | `main.py` | 准确性 |

---

## 第十轮：功能加固与生态完善六阶段

### 阶段一：控制标签保护确认

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 86 | 确认现有 tag 正则 `\{/?[a-zA-Z]+=?[^}]*\}` 已覆盖 `{w}/{p}/{nw}/{fast}/{cps=N}/{done}` 等控制标签；新增测试 `test_protect_control_tags` 确认 | `test_all.py` | 测试覆盖 |

### 阶段二：启动器安全增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 87 | API Key 输入改用 `getpass.getpass()` 隐藏明文回显 | `start_launcher.py` | 安全性 |
| 88 | 命令预览中 API Key 显示为 `****` | `start_launcher.py` | 安全性 |

### 阶段三：CI 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 89 | 零第三方依赖自动检查：扫描全部 .py import，排除标准库和本地模块后报错 | `.github/workflows/test.yml` | CI 防护 |
| 90 | `--dry-run` 集成测试：用 `tests/tl_priority_mini` 目录验证完整 dry-run 流程不崩溃 | `.github/workflows/test.yml` | CI 防护 |

### 阶段四：Glossary 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 91 | 连字符人名正则：`[A-Z][a-z]+(?:-[A-Z][a-z]+)*` 匹配 `Mary-Jane` 等复合人名 | `glossary.py` | 术语提取准确率 |
| 92 | 翻译记忆信心度：`_memory_count` 追踪出现次数，`to_prompt_text` 只输出 count>=2 的记忆 | `glossary.py` | Prompt 质量 |

### 阶段五：文档完善

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 93 | README 新增"各提供商用法示例"：xAI/OpenAI/DeepSeek/Claude/Gemini 各一个完整命令行 | `README.md` | 用户体验 |
| 94 | README 新增"性能调优"表：各提供商推荐 workers/rpm/rps 配置 | `README.md` | 用户体验 |
| 95 | README 新增"故障排查"FAQ：API 超时/编码错误/进度损坏/漏翻率/词典不生效 5 项 | `README.md` | 用户体验 |

### 阶段六：跨平台兼容

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 96 | subprocess 调用 main.py 改用 `Path(__file__).parent / "main.py"` 绝对路径 | `one_click_pipeline.py` | Linux/Mac 兼容 |

---

## 第十一轮阶段一：main.py 模块拆分

### 结构变更

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 97 | 新建 `translation_utils.py`（263 行）：从 main.py 提取 ChunkResult / ProgressTracker / 所有公共辅助函数和常量 | `translation_utils.py`（新增）`main.py` | 公共基础设施独立 |
| 98 | 新建 `direct_translator.py`（943 行）：从 main.py 迁移 translate_file / _translate_file_targeted / run_pipeline | `direct_translator.py`（新增）`main.py` | direct-mode 引擎独立 |
| 99 | 新建 `retranslator.py`（487 行）：从 main.py 迁移 retranslate_file / find_untranslated_lines / build_retranslate_chunks / calculate_dialogue_density / run_retranslate_pipeline | `retranslator.py`（新增）`main.py` | 补翻引擎独立 |
| 100 | 新建 `tl_translator.py`（638 行）：从 main.py 迁移 run_tl_pipeline / build_tl_chunks / _apply_tl_game_patches / _inject_language_buttons / _clean_rpyc | `tl_translator.py`（新增）`main.py` | tl-mode 引擎独立 |
| 101 | main.py 瘦身为 233 行 CLI 入口 + 向后兼容 re-export（确保 `from main import ...` 不断裂） | `main.py` | 降幅 89% |
| 102 | CI 增加 4 个新模块的 py_compile 语法检查 | `.github/workflows/test.yml` | CI 覆盖 |
| 103 | 清理未使用 import（tl_translator.py 中 `apply_font_patch` 未使用已移除） | `tl_translator.py` | 代码卫生 |
| 104 | 新增 `TranslationContext` dataclass，替代嵌套函数的闭包变量捕获（`client` / `system_prompt` / `rel_path`） | `translation_utils.py` | 闭包重构 |
| 105 | `_translate_chunk` / `_should_retry` / `_translate_chunk_with_retry` 从 translate_file 内嵌套函数提升为模块级函数（接收 ctx 参数） | `direct_translator.py` | 闭包重构 |
| 106 | `_translate_one_tl_chunk` 从 run_tl_pipeline 内嵌套函数提升为模块级函数 | `tl_translator.py` | 闭包重构 |

---

## 第十一轮阶段二+三：回写失败分析与修复

### 阶段二：数据采集与分析

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 107 | `_diagnose_writeback_failure()` 诊断函数：分析每条回写失败的根因（WF-01~08 分类） | `file_processor/patcher.py` | 新增 ~80 行 |
| 108 | `apply_translations` 失败路径记录 `status="writeback_failed"` + diagnostic 字段到 translation_db | `direct_translator.py` | 数据采集 |
| 109 | `analyze_writeback_failures.py` 独立分析脚本（分类统计 + 典型样本 + JSON 报告） | 新增 | ~120 行 |

### 分析结果（The Tyrant, 140 文件, direct-mode）

| 指标 | 第三轮基线 | 第十一轮 |
|------|-----------|---------|
| 回写失败总数 | 609 | **28**（降 95%） |
| 主要失败类型 | 未分类 | WF-08（82%）：`_replace_string_in_line` 不支持含前缀的 original |

### 阶段三：基于数据的修复

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 110 | `_replace_string_in_line` 阶段 1b：剥离 AI 返回的行前缀（`text _("` / `textbutton "` / `text "`） | `file_processor/patcher.py` | 修复 WF-08 主因 |
| 111 | 阶段 3 正则升级：`"([^"]+)"` → `"((?:[^"\\]|\\.)+)"` 支持转义引号 | `file_processor/patcher.py` | 修复 WF-04 |
| 112 | 阶段 3f：用剥离后 original 在 quoted_parts 中 fallback 匹配 | `file_processor/patcher.py` | 兜底修复 |
| 113 | 新增 2 个测试：`test_replace_string_prefix_strip` + `test_replace_string_escaped_quotes` | `test_all.py` | 测试 53→55 |

---

## 第十一轮阶段四：config.json 配置文件支持

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 114 | `config.py` 新增（~140行）：Config 类 + DEFAULTS 字典 + 三层合并（CLI>配置文件>DEFAULTS）+ `resolve_api_key()`（api_key_env/api_key_file） | `config.py`（新增） | 配置管理 |
| 115 | `renpy_translate.example.json` 示例配置文件 | 新增 | 用户模板 |
| 116 | main.py argparse 18 个参数改 `default=None` + 新增 `--config` 参数 + Config 集成填充 args | `main.py` | CLI 行为变更（向后兼容） |
| 117 | `.gitignore` 新增 `renpy_translate.json` 排除 | `.gitignore` | 防误提交 |
| 118 | CI 新增 `config.py` + `analyze_writeback_failures.py` py_compile | `.github/workflows/test.yml` | CI 覆盖 |
| 119 | 新增 3 个测试（55→58）：config 默认值 / CLI 覆盖 / 配置文件加载 | `test_all.py` | 测试覆盖 |
| 120 | README 新增"配置文件（可选）"章节 | `README.md` | 用户文档 |

---

## 第十一轮阶段五：Review HTML + 进度增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 121 | `ProgressBar` 类加入 translation_utils.py（~60行）：Unicode/ASCII 自适应 + `_detect_unicode_support()` GBK 安全 | `translation_utils.py` | 进度显示 |
| 122 | `review_generator.py` 新增（~150行）：HTML 翻译校对报告（side-by-side + 深色主题 + 按文件折叠 + error/warning/fail 颜色高亮 + 统计摘要） | `review_generator.py`（新增） | 校对工具 |
| 123 | `direct_translator.py` run_pipeline 集成 ProgressBar（非 quiet/dry-run 模式） | `direct_translator.py` | 用户体验 |
| 124 | main.py re-export ProgressBar + CI 新增 review_generator.py py_compile | `main.py` `.github/workflows/test.yml` | 兼容+CI |
| 125 | 新增 2 个测试（58→60）：ProgressBar 渲染 + review HTML 生成 | `test_all.py` | 测试覆盖 |

---

## 第十一轮阶段六：类型注解

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 126 | 全部公共 API 补齐返回类型注解（ProgressTracker 6 个方法 + APIConfig.__post_init__） | `translation_utils.py` `api_client.py` | 类型安全 |
| 127 | `read_file(path)` → `read_file(path: object)` 参数注解 | `file_processor/splitter.py` | 参数注解 |
| 128 | `update_stats(value)` → `update_stats(value: object)` 参数注解 | `translation_utils.py` | 参数注解 |
| 129 | `py.typed` PEP 561 marker 文件 | `py.typed`（新增） | 类型包标记 |
| 130 | CI 新增 mypy 步骤（`continue-on-error: true`，informational） | `.github/workflows/test.yml` | CI 类型检查 |

---

## 第十一轮阶段七：目标语言参数化抽象层

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 131 | `lang_config.py` 新增（~130行）：LanguageConfig dataclass（code/name/native_name/detector/min_ratio/instruction/style_notes/glossary_field/field_aliases） | `lang_config.py`（新增） | 多语言基础设施 |
| 132 | 预置 4 种语言配置：zh（简体中文）/ zh-tw（繁体中文）/ ja（日语）/ ko（韩语） | `lang_config.py` | 开箱即用 |
| 133 | `detect_chinese/japanese/korean_ratio()` 文字检测函数 | `lang_config.py` | W442 参数化基础 |
| 134 | `get_language_config()` 查找 + 不存在回退 zh；`resolve_translation_field()` 兼容别名读取 | `lang_config.py` | 容错 + 兼容 |
| 135 | main.py 集成：`args.lang_config = get_language_config(args.target_lang)` | `main.py` | 全局挂载 |
| 136 | 中文 prompt 基线 `tests/zh_prompt_baseline.txt` + 零变更回归验证 | `tests/`（新增） | 安全网 |
| 137 | 新增 3 个测试（60→63）：语言检测 / 配置查找与回退 / 兼容字段读取 | `test_all.py` | 测试覆盖 |
| 138 | CI 新增 `lang_config.py` py_compile | `.github/workflows/test.yml` | CI |

---

## 第十一轮阶段八：Prompt + Validator 多语言适配

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 139 | `build_system_prompt` 新增 `lang_config` 参数：zh/zh-tw 走 `_build_chinese_system_prompt`（现有逻辑零变更），其他走 `_build_generic_system_prompt` | `prompts.py` | Prompt 多语言 |
| 140 | `_GENERIC_SYSTEM_PROMPT_TEMPLATE` 英文通用模板（含动态 `{field}` JSON 字段名 + 语言指令 + 风格注释） | `prompts.py` | ja/ko 支持 |
| 141 | `validate_translation` + `_check_quality_heuristics` 新增 `lang_config` 参数：W442 使用 `target_script_detector` + `min_target_ratio` 参数化 | `file_processor/validator.py` | W442 多语言 |
| 142 | 新增 3 个测试（63→66）：中文 prompt 零变更回归 / 日语通用模板内容验证 / validator lang_config 参数化 | `test_all.py` | 测试覆盖 |

---

## 第十二轮：阶段零四项优化

> 对应 EXPANSION_PLAN.md §1「当前 Ren'Py 工具优化」，在多引擎扩展之前落地四项低风险高价值改进。

### 新增功能

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 143 | chunk 截断自动拆分重试：`_should_retry` 返回 `(should, needs_split)` 元组，`returned < expected * 0.5` 触发截断检测；`_split_chunk` 三级拆分（label/screen 边界 > 空行 > 二等分）；`_translate_chunk_with_retry` 拆分后分别翻译再合并，单层不递归 | `direct_translator.py` | 大 chunk 截断时翻译完整度提升 |
| 144 | tl-mode .rpyc 精确清理：`_clean_rpyc` 新增 `modified_files` 参数，只删除本次修改的 .rpy 对应的 .rpyc；`run_tl_pipeline` 收集 `modified_rpy_files` 集合 | `tl_translator.py` | 精确清理而非全目录 |
| 145 | `--no-clean-rpyc` CLI 参数：禁用 tl-mode 翻译后的 .rpyc 缓存清理 | `main.py` | 新增 CLI 参数 |
| 146 | dry-run verbose 增强：`--verbose` 时输出每文件对话行数/密度/策略/费用 + 密度分布直方图 + 术语扫描预览 | `direct_translator.py` | 仅 verbose 模式新增输出 |

### 增强

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 147 | `one_click_pipeline.py` main() 拆分：提取 `_run_pilot_phase` / `_run_full_translation_phase` / `_run_tl_mode_phase` 三个阶段函数，main() 从 ~280 行缩减到 ~113 行纯编排 | `one_click_pipeline.py` | 纯重构，零行为变更 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 148 | 新增 4 个测试（66→70）：`test_should_retry_truncation`（截断检测 + 边界 returned=0/expected=0）/ `test_should_retry_normal`（正常+丢弃率过高）/ `test_split_chunk_basic`（行数守恒+offset）/ `test_split_chunk_at_empty_line`（空行拆分优先） | `test_all.py` | 测试覆盖 |

---

## 第十二轮 阶段一：引擎抽象层骨架

> 对应 EXPANSION_PLAN.md §2「引擎抽象层设计」+ §9 阶段一里程碑 M1。

### 新增文件

| # | 描述 | 文件 | 行数 |
|---|------|------|------|
| 149 | `EngineProfile` 数据类（9 字段 + 占位符/skip 编译方法）+ `TranslatableUnit` 数据类（8 字段）+ `EngineBase` ABC（4 抽象 + 3 可选方法）+ 内置 Profile 常量（RENPY / RPGMAKER_MV / CSV）+ `ENGINE_PROFILES` 注册表 | `engine_base.py`（新增） | ~202 |
| 150 | `EngineType` 枚举（6 值）+ `detect_engine_type` 目录特征扫描（5 级优先：Ren'Py > MV > MZ > VXAce > Unknown）+ `create_engine` 延迟导入工厂 + `resolve_engine` CLI 路由 + 未识别时 top 10 扩展名诊断 | `engine_detector.py`（新增） | ~160 |
| 151 | `RenPyEngine` 薄包装：`detect()` 检查 .rpy/.rpa、`run()` 路由到三条管线（延迟导入 + try-except）、`extract_texts()`/`write_back()` 抛 NotImplementedError | `engines/renpy_engine.py`（新增） | ~74 |
| 152 | 引擎实现包声明 | `engines/__init__.py`（新增） | ~3 |

### 修改文件

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 153 | `--engine` CLI 参数（auto/renpy/rpgmaker/csv/jsonl）；路由：auto/renpy 走原路径零改动，其他走 `resolve_engine()` | `main.py` | 向后兼容，默认行为不变 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 154 | 新增 `test_engines.py`（25 个测试）：EngineProfile 编译 6 + TranslatableUnit 默认值 3 + 引擎检测 10 + RenPyEngine 5 + EngineBase dry_run 1 | `test_engines.py`（新增） | 引擎抽象层全覆盖 |

---

## 第十二轮 阶段二：CSV/JSONL + 通用翻译流水线

> 对应 EXPANSION_PLAN.md §4-§6 阶段二里程碑 M2。

### 新增文件

| # | 描述 | 文件 | 行数 |
|---|------|------|------|
| 155 | 通用翻译流水线（6 阶段：提取→初始化→分块→并发翻译→回写→报告）+ GenericChunk 数据类 + build_generic_chunks 按 file_path 分组拆块 + translation_db 断点恢复 + RPG Maker 术语扫描钩子 + 原子进度写入 | `generic_pipeline.py`（新增） | ~414 |
| 156 | CSVEngine（CSV/TSV/JSONL/JSON 读写）：列名别名自动匹配（original/source/text/en 等 6 组）+ UTF-8 BOM + 多行 CSV 值安全读取 + 目录批量扫描 + 按源格式分流回写 | `engines/csv_engine.py`（新增） | ~317 |

### 修改文件

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 157 | `protect_placeholders` 新增 `patterns` 参数；`check_response_item` 新增 `placeholder_re` 参数；`_extract_placeholder_sequence` 新增 `regex` 参数。全部默认 None 走 Ren'Py 模式 | `file_processor/checker.py` | 向后兼容 |
| 158 | `_ENGINE_PROMPT_ADDONS` 字典（rpgmaker/generic 两条 addon）+ `build_system_prompt` 新增 `engine_profile` 参数；None 时零变更 | `prompts.py` | 向后兼容 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 159 | 新增 22 个引擎测试（25→47）：CSV 提取 5 + JSONL 3 + 回写 2 + 目录扫描 1 + 分块 3 + 匹配 2 + patcher 参数化 2 + checker 参数化 2 + prompts addon 2 | `test_engines.py` | 引擎测试覆盖 |

---

## 第十二轮 阶段三：RPG Maker MV/MZ 引擎

> 对应 EXPANSION_PLAN.md §3 阶段三里程碑 M3。

### 新增文件

| # | 描述 | 文件 | 行数 |
|---|------|------|------|
| 160 | RPGMakerMVEngine：目录定位（MV www/data/ vs MZ data/）+ 事件指令提取（401/405 连续合并、102 选项遍历、402 When、320/324 改名）+ 8 种数据库文件提取（_DB_FIELDS 配置表）+ System.json 提取（简单字段 + 数组 + terms.*）+ JSON path 导航回写（_navigate_to_node + _patch_by_json_path）+ 对话块拆分回写（行数不匹配处理）+ 紧凑 JSON 输出 + 字体安装提示 | `engines/rpgmaker_engine.py`（新增） | ~636 |

### 修改文件

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 161 | `scan_rpgmaker_database(game_dir)` 新增：从 Actors.json 提取角色名（name/nickname）+ 从 System.json 提取系统术语（terms.basic/commands/params）；线程安全 | `glossary.py` | 新增方法，现有行为不变 |

### 测试

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 162 | 新增 15 个 RPG Maker 测试（47→62）：检测 3 + 目录定位 1 + 事件指令 4（401 合并/102 选项/405 滚动/320 改名）+ 数据库 1 + System 1 + 回写 2 + JSON path 2 + glossary 1 | `test_engines.py` | 引擎测试覆盖 |

---

## 第十二轮 阶段四：文档 + 发布

> 对应 EXPANSION_PLAN.md §9 阶段四里程碑 M4。

| # | 描述 | 涉及文件 | 影响 |
|---|------|----------|------|
| 163 | start_launcher.py 新增模式 8（RPG Maker MV/MZ 翻译）和模式 9（CSV/JSONL 通用格式翻译）；菜单标题改为「多引擎游戏汉化统一启动器」；分类显示（Ren'Py / 其他引擎 / 工具） | `start_launcher.py` | 新增菜单选项 |
| 164 | README/CHANGELOG/TEST_PLAN/.cursor_prompt/EXPANSION_PLAN 全部文档已在各阶段增量更新完成 | 多文件 | 文档齐全 |

---

## 第十二轮 结构整理：项目目录重构

| # | 描述 | 影响 |
|---|------|------|
| 165 | 测试文件移入 `tests/`：test_all.py / test_engines.py / test_single.py + sys.path 修正 | 根目录 -3 |
| 166 | 独立工具移入 `tools/`（新建）：verify_alignment / revalidate / patch_font_now / analyze_writeback_failures + sys.path 修正 | 根目录 -4 |
| 167 | 引擎抽象层合并到 `engines/` 包：engine_base / engine_detector / generic_pipeline 移入 + `engines/__init__.py` 新增 re-export（EngineProfile / TranslatableUnit / EngineBase / EngineType 等） | 根目录 -3 |
| 168 | 全量 import 路径更新：`from engine_base import` → `from engines.engine_base import`（main.py + 4 引擎 + 3 测试 + 3 工具共 11 个文件） | 零功能变更 |
| 169 | 清理所有 `__pycache__/` 目录 | 磁盘清理 |

**结果**：根目录 .py 文件 **27 → 17**，目录结构清晰分层。132 测试全绿。

---

## 第十二轮 GUI：图形界面 + PyInstaller 打包

| # | 描述 | 文件 | 行数 |
|---|------|------|------|
| 170 | Tkinter GUI 启动器：3 Tab 分页（基本设置 + 翻译设置动态引擎面板 + 高级设置）、引擎选择联动面板切换、API key 隐藏（Entry show="*" + 命令预览 ****）、命令预览实时更新、内嵌 ScrolledText 日志（queue.Queue 线程安全轮询）、subprocess 后台执行 + kill 停止、配置加载/保存（JSON）、工具菜单（Dry-run 摘要弹窗 + 升级扫描）、DPI 适配 | `gui.py`（新增） | ~753 |
| 171 | PyInstaller 打包脚本：29 个 hidden-import + 资源文件打包 → 单文件 .exe（32MB） | `build.py`（新增） | ~100 |
| 172 | .gitignore 新增 build/dist/*.spec 排除 | `.gitignore` | +4 行 |

---

## 关键发现与经验

1. **对话密度是漏翻率最强相关因子**：< 10% 密度文件漏翻中位数 57.69%，≥ 40% 仅 4.54%
2. **Prompt 强化无效甚至有害**：CRITICAL RULE 降低 AI 返回率 5pp，引入翻译不一致性
3. **tl-mode 精度远高于 direct-mode**：行号精确定位 vs 文本匹配回写，可消除"回写失败"类漏翻
4. **AI 约 14% 概率返回带外层引号**：ASCII / 弯引号 / 全角，需循环剥离
5. **旧增量架构有结构性缺陷**：两次翻译覆盖范围不一致时丢数据，retranslate 模式解决
6. **占位符保护对 Checker 通过率有显著正面影响**：从基线到 +2pp
7. **tl-mode 剩余遗漏全为边界 case**：空格原文、命名输入框提示、游戏标题、原文 bug（括号未闭合），0 条正常对话漏翻
8. **chunk 自动重试对 Checker 丢弃有直接效果**：4→2（-50%），验证了重试策略的价值
