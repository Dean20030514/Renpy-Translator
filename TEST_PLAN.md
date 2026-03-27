# 测试方案

本文档定义项目的完整测试体系：已有测试的覆盖范围、待补充的测试用例、测试数据与执行方法。

---

## 一、测试体系总览

### 现有测试文件

| 文件 | 类型 | 覆盖范围 | 用例数 | 需 API |
|------|------|----------|--------|--------|
| `test_all.py` | 单元测试 | api_client / file_processor / glossary / prompts / main.ProgressTracker | 21 | 否 |
| `tests/smoke_test.py` | 冒烟测试 | validate_translation 所有 Warning/Error Code + strings 统计 | 13 | 否 |
| `tl_parser.py` (内建) | 自测试 | 状态机解析 / fill_translation / extract_quoted_text / postprocess | 56 | 否 |
| `test_single.py` | 端到端测试 | 单文件完整翻译流程（API→回写→校验） | 1 | **是** |

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

### test_all.py（21 个单元测试）

| # | 函数 | 覆盖模块 | 测试内容 |
|---|------|----------|----------|
| 1 | `test_api_config` | api_client | 5 个提供商的 endpoint / model 默认值 |
| 2 | `test_usage_stats` | api_client | token 累计、费用估算、summary 格式 |
| 3 | `test_rate_limiter` | api_client | RateLimiter acquire 不报错 |
| 4 | `test_estimate_tokens` | file_processor | 英文/中文 token 估算 > 0 |
| 5 | `test_find_block_boundaries` | file_processor | label/screen/init 块边界检测 |
| 6 | `test_safety_check` | file_processor | 变量丢失/多出、标签不匹配、换行符、{#id}、%(name)s、长度比例 |
| 7 | `test_apply_translations` | file_processor | 基本行级回写 |
| 8 | `test_apply_cascade` | file_processor | 多条翻译指向同一行时不重复替换 |
| 9 | `test_validate_translation` | file_processor | 无问题文件通过 + 变量丢失检出 |
| 10 | `test_glossary` | glossary | to_prompt_text / update_from_translations 过滤（短句/同值/数字/标点） |
| 11 | `test_prompts` | prompts | system_prompt 含风格/术语/规范 + user_prompt 含文件名/chunk 信息 |
| 12 | `test_json_parse` | api_client | 6 级 JSON 解析：直接/markdown/尾逗号/空数组/垃圾/逐对象/转义引号/字段顺序 |
| 13 | `test_force_split` | file_processor | 超大块强制拆分，总行数不丢 |
| 14 | `test_triple_quote_replacement` | file_processor | 三引号字符串替换 |
| 15 | `test_underscore_func_replacement` | file_processor | `_()` 包裹字符串替换 |
| 16 | `test_validate_menu_identifier` | file_processor | `{#identifier}` 保留/丢失检测 |
| 17 | `test_glossary_dedup` | glossary | terms 中已有的不重复进 memory |
| 18 | `test_image_block_boundary` | file_processor | image 声明作为块边界 |
| 19 | `test_glossary_thread_safety` | glossary | 4 线程 × 50 条并发写入 |
| 20 | `test_progress_cleanup` | main.ProgressTracker | mark_file_done 后 results 被清理 |
| 21 | `test_pricing_lookup` | api_client | 精确/前缀/兜底定价 + 推理模型检测 |

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

### tl_parser.py 内建自测（56 个断言）

通过 `python tl_parser.py` 直接运行 `_run_self_tests()`，覆盖：
- 状态机解析（IDLE / DIALOGUE / STRINGS / SKIP 状态切换）
- DialogueEntry / StringEntry 字段提取
- `extract_quoted_text` 各种引号场景
- `fill_translation` 行级回填（保留缩进/character 前缀/只替换第一个 `""`）
- `_sanitize_translation` 元数据清理 / 引号剥离 / 转义
- `postprocess_tl_file` nvl clear 移除 / 空块补 pass
- UTF-8 BOM 处理
- 源注释行（`# game/script.rpy:95`）解析

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

#### T1. protect_placeholders / restore_placeholders

| 用例 | 输入 | 期望 |
|------|------|------|
| 基本替换 | `"[name] says {color=#f00}hi{/color}"` | 3 个占位符被替换为 `__RENPY_PH_N__`，mapping 长度 3 |
| 相同占位符去重 | `"[name] says hi to [name]"` | 两个 `[name]` 用同一个 token，mapping 长度 1 |
| 空文本 | `""` | 原样返回，mapping 为空 |
| 无占位符 | `"Hello world"` | 原样返回，mapping 为空 |
| 还原正确 | protect 后 restore | 结果 == 原始输入 |
| `%(name)s` 格式 | `"Hello %(user)s"` | 1 个占位符 |
| 混合类型 | `"[a] {b} %(c)s"` | 3 个占位符，顺序 [a] → {b} → %(c)s |

```python
def test_protect_restore_roundtrip():
    text = "[name] says {color=#f00}Hello{/color} to [name]"
    protected, mapping = protect_placeholders(text)
    assert "__RENPY_PH_" in protected
    assert "[name]" not in protected
    assert "{color=#f00}" not in protected
    restored = restore_placeholders(protected.replace("Hello", "你好"), mapping)
    assert restored == "[name] says {color=#f00}你好{/color} to [name]"

def test_protect_dedup():
    text = "[name] greets [name]"
    _, mapping = protect_placeholders(text)
    assert len(mapping) == 1  # 相同占位符只出现一次

def test_protect_empty():
    text = ""
    result, mapping = protect_placeholders(text)
    assert result == "" and mapping == []

def test_protect_no_placeholders():
    text = "Hello world"
    result, mapping = protect_placeholders(text)
    assert result == text and mapping == []
```

#### T2. check_response_item

| 用例 | 输入 | 期望 |
|------|------|------|
| 正常条目 | `{"line":1, "original":"Hi", "zh":"你好"}` | 无警告 |
| 译文为空 | `{"line":1, "original":"Hi", "zh":""}` | 有警告 |
| 原文为空 | `{"line":1, "original":"", "zh":"你好"}` | 有警告 |
| 占位符丢失 | `{"line":1, "original":"Hi [name]", "zh":"你好"}` | 有警告（变量缺失） |
| 占位符保留 | `{"line":1, "original":"Hi [name]", "zh":"你好 [name]"}` | 无警告 |
| 缺少字段 | `{"line":1}` | 有警告 |

```python
def test_check_response_item_normal():
    warnings = check_response_item({"line":1, "original":"Hi", "zh":"你好"})
    assert len(warnings) == 0

def test_check_response_item_empty_zh():
    warnings = check_response_item({"line":1, "original":"Hi", "zh":""})
    assert len(warnings) > 0

def test_check_response_item_var_missing():
    warnings = check_response_item({"line":1, "original":"Hi [name]", "zh":"你好"})
    assert any("name" in w for w in warnings)
```

#### T3. check_response_chunk

| 用例 | chunk 内容 | 返回条数 | 期望 |
|------|-----------|---------|------|
| 条数一致 | 3 行含引号 | 3 条 | 无警告 |
| 条数偏少 | 3 行含引号 | 1 条 | 有警告（差值 -2） |
| 条数偏多 | 3 行含引号 | 5 条 | 有警告（差值 +2） |
| 空 chunk | 无引号行 | 0 条 | 无警告 |

```python
def test_check_response_chunk_match():
    chunk = 'e "A"\ne "B"\ne "C"'
    warnings = check_response_chunk(chunk, [{"zh":"1"}, {"zh":"2"}, {"zh":"3"}])
    assert len(warnings) == 0

def test_check_response_chunk_mismatch():
    chunk = 'e "A"\ne "B"\ne "C"'
    warnings = check_response_chunk(chunk, [{"zh":"1"}])
    assert len(warnings) > 0 and "不一致" in warnings[0]
```

#### T4. _sanitize_translation（tl_parser.py）

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

#### T5. fill_translation（tl_parser.py）

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
python main.py --game-dir "tests/tl_priority_mini/game" --provider xai --dry-run --tl-priority

# 不启用：script.rpy 和 tl/zh/script.rpy 均被选
python main.py --game-dir "tests/tl_priority_mini/game" --provider xai --dry-run
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

### 低优先级：需 API 的端到端测试

#### T11. 单文件翻译端到端

使用 `test_single.py`（需 API key），验证：
1. API 调用成功返回翻译
2. `apply_translations` 回写无崩溃
3. `validate_translation` 无 error 级 issue
4. 输出文件可正常保存

#### T12. tl-mode 小规模端到端

对含 5-10 个空槽位的 tl 文件运行 `--tl-mode`，验证：
1. `scan_tl_directory` 正确检出空槽位
2. API 调用返回翻译
3. `fill_translation` 精确回填
4. 引号剥离保护生效
5. `.bak` 备份创建
6. `tl_progress.json` 正确记录

#### T13. retranslate 补翻端到端

对含残留英文行的已翻译文件运行 `--retranslate`，验证：
1. `find_untranslated_lines` 正确检出
2. `build_retranslate_chunks` 构建合理
3. 补翻回写后残留英文行减少
4. 已有翻译不被破坏
5. `.bak` 备份创建

#### T14. 一键流水线端到端

用极小游戏目录（3-5 个文件）运行 `one_click_pipeline.py`，验证：
1. Stage 1-4 均正常完成
2. `pipeline_report.json` 结构完整
3. 闸门评估结果合理
4. `evaluate_gate` 返回字典包含所有预期字段

---

## 六、测试执行方法

### 无 API 测试（推荐日常使用）

```bash
# 1. 单元测试（21 个）
python test_all.py

# 2. 冒烟测试（13 个）
python tests/smoke_test.py

# 3. tl_parser 自测（56 个断言）
python tl_parser.py
```

全部通过预期输出：
```
ALL 21 TESTS PASSED          (test_all.py)
All tests passed              (smoke_test.py)
All 56 assertions passed.     (tl_parser.py)
```

### 需 API 测试

```bash
# 单文件端到端（需 xAI API key）
python test_single.py YOUR_API_KEY

# tl-mode 端到端
python main.py --game-dir "tests/tl_priority_mini/game" --provider xai --api-key YOUR_KEY --tl-mode --tl-lang zh

# 一键流水线（需真实游戏目录）
python one_click_pipeline.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY --pilot-count 3 --clean-output
```

### 推荐执行顺序

1. **快速验证**：`python test_all.py && python tests/smoke_test.py && python tl_parser.py`（< 5 秒，无 API）
2. **边界验证**：smoke_test 中的 boundary 测试已覆盖 W430/W251 边界
3. **密度/跳过**：构造低密度文件 + define.rpy 验证 `[DENSITY]` / `[SKIP-CFG]` 日志
4. **tl 优先**：`--dry-run` 模式验证文件选择（无需 API）
5. **端到端**：有 API key 时运行 `test_single.py`

---

## 七、测试覆盖率差距分析

### 已良好覆盖

| 模块 | 覆盖函数 | 测试数 |
|------|----------|--------|
| file_processor.validate_translation | 全部 12 个 E/W Code | 13（smoke_test） |
| file_processor._check_translation_safety | 变量/标签/换行/ID/格式/长度 | 10（test_all） |
| api_client | APIConfig / UsageStats / RateLimiter / JSON 解析 / 定价 | 5（test_all） |
| glossary | prompt_text / 过滤 / 去重 / 线程安全 | 4（test_all） |
| tl_parser | 状态机 / 回填 / 清理 / 后处理 | 56（内建） |

### 覆盖不足（需补充）

| 优先级 | 模块/函数 | 当前状态 | 补充建议 |
|--------|----------|----------|----------|
| **高** | `protect_placeholders` / `restore_placeholders` | 无独立测试 | T1：7 个用例 |
| **高** | `check_response_item` | 无独立测试 | T2：6 个用例 |
| **高** | `check_response_chunk` | 无独立测试 | T3：4 个用例 |
| **高** | `_sanitize_translation` | 仅内建测试 | T4：8 个用例（含边界） |
| 中 | `calculate_dialogue_density` | 无测试 | T6：3 个用例 |
| 中 | `find_untranslated_lines` 过滤 | 无测试 | T8：6 个用例 |
| 中 | `fill_translation` 边界 | 仅内建测试 | T5：6 个用例 |
| 低 | 端到端 tl-mode | 无自动化 | T12：需 API |
| 低 | 端到端 retranslate | 无自动化 | T13：需 API |

### 下一步行动

1. 将 T1-T3 的代码示例加入 `test_all.py` 或新建 `test_core.py`（高优先级，无需 API）
2. 将 T4-T5 的边界场景加入 `tl_parser.py` 内建测试
3. T6-T10 作为集成级测试，可在 smoke_test 中补充
4. T11-T14 的端到端测试需 API key，建议作为 CI 中的可选步骤
