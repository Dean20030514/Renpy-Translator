> 仅在修改一键流水线或核心算法时加载此文档。

# 一键流水线 + 核心算法

## 四阶段一键流水线（one_click_pipeline.py）

```
main() 纯编排入口（~113 行）
  │
  ├─ (if tl-mode) → _run_tl_mode_phase()
  │     跳过试跑，直接 tl 全量翻译 → 读取报告
  │
  └─ (if direct-mode)
      ├─ Stage 1/4 → _run_pilot_phase()
      │   pick_pilot_files(): 按风险评分选 20 个文件
      │   score = min(size/1KB, 200) + [80 if risk_keyword] + [30 if sazmod]
      │   → run_main() 翻译 → evaluate_gate() → AI 术语提取
      │   → errors > 0 则中止；ratio 超阈值则警告继续
      │
      ├─ Stage 2/4 → _run_full_translation_phase()
      │   run_main() 翻译全部文件 → evaluate_gate()
      │   → errors > 0 则中止
      │
      ├─ Stage 3/4 → _run_retranslate_phase()
      │   collect_files_with_untranslated() → retranslate_file() × N
      │   → 原地补翻残留英文行
      │
      └─ Stage 4/4 → _run_final_report()
          evaluate_gate() 最终评估
          attribute_untranslated() 漏翻归因
          write_report_summary_md() 生成报告
          package_output() → zip 打包

目录结构：
  output/projects/<project_name>/
    ├─ stage0_raw/          (预留)
    ├─ stage1_normalized/   (预留)
    ├─ stage2_translated/   (全量翻译结果)
    ├─ stage3_polished/     (预留)
    └─ _pipeline/
        ├─ pilot_input/     (试跑输入)
        ├─ pilot_output/    (试跑输出)
        └─ *.log
```

## 核心算法

### Token 估算
```python
token_count = ascii_chars // 4 + non_ascii_chars // 2 + 1
```

### 占位符保护
```
"[name] says: {color=#f00}Hello{/color}"
→ "__RENPY_PH_0__ says: __RENPY_PH_1__Hello__RENPY_PH_2__"
映射: [(0, "[name]"), (1, "{color=#f00}"), (2, "{/color}")]
```

### 文件拆分策略（split_file）
1. 识别顶层 Ren'Py 块边界（label / screen / define / init / translate / menu 等）
2. 按块累积 token，超过 `max_chunk_tokens`（默认 4000）时断开
3. 单块超限 → 按行数拆分，优先空行处断开
4. 每个 chunk 携带行偏移量（base_line_offset），确保多块重组

### 密度计算
```python
dialogue_density = dialogue_lines / non_empty_lines
if density < 0.20:  # 走定向翻译
```

### 风险评分（试跑文件选择）
```python
score = min(file_size / 1024, MAX_FILE_RANK_SCORE)
      + RISK_KEYWORD_SCORE * (any keyword in filename)
      + SAZMOD_BONUS_SCORE * ("sazmod" in filename)
```

### tl-mode StringEntry 四层 fallback 匹配
1. 精确匹配 `entry.old == api_returned_id`
2. strip 空白后匹配
3. 去占位符令牌后匹配
4. 转义规范化（`\"` → `"`, `\n` → 换行）后匹配
