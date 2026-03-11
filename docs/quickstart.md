# 10 分钟上手：从抽取到构建

本页以一个极小的 Ren'Py 项目为例，演示完整的端到端流程。

## 准备一个 demo 项目

目录：

```text
demo/game/script.rpy
```

内容：

```renpy
label start:
    e "Hello, world!"
    "Click to continue"
    menu:
        "Go outside":
            jump outside
        "Stay home":
            "OK"
label outside:
    "You went out."
```

## 0) RPA 解包（如需要）

如果游戏将脚本打包在 `.rpa` 存档中，先解包：

```pwsh
python tools/unrpa.py demo/game/archive.rpa -o demo/game/ --scripts-only
```

> 支持 RPA-2.0 和 RPA-3.0 格式。如果游戏目录下已有 `.rpy` 文件，可跳过此步。

## 1) 抽取英文文案

```pwsh
python tools/extract.py demo -o outputs/extract --workers auto
```

生成：

- `outputs/extract/project_en_for_grok.jsonl`
- `outputs/extract/per_file_jsonl/...`
- `outputs/extract/manifest.csv`

> v3.0 会自动识别 screen 块中的 UI 文本（按钮、标签、tooltip），并标记 `is_screen_text`。

## 2) 预填术语/TM（可选）

```pwsh
python tools/prefill.py outputs/extract/project_en_for_grok.jsonl data/dictionaries -o outputs/prefilled/prefilled.jsonl --case-insensitive --dict-backend memory
```

说明：

- 支持分层字典（names/ui/general）与 TM 精确复用。
- 大词典可用 `--dict-backend sqlite` 避免大内存。

## 3) 质量校验与 QA 报告

```pwsh
python tools/validate.py outputs/extract/project_en_for_grok.jsonl outputs/prefilled/prefilled.jsonl --qa-json outputs/qa/qa.json --qa-tsv outputs/qa/qa.tsv --qa-html outputs/qa/qa.html --ignore-ui-punct
```

检查项包括：占位符集合、标签成对/嵌套、末尾标点、换行、长度比，以及中文/英文混排空格、全角/半角、UI 中文宽度等。

## 4) 回填（高级匹配）

```pwsh
python tools/patch.py demo outputs/prefilled/prefilled.jsonl -o outputs/out_patch --advanced
```

输出 `.zh.rpy` 镜像树到 `outputs/out_patch`。

## 5) 构建中文包

```pwsh
python tools/build.py demo -o outputs/build_cn --mode auto --zh-mirror outputs/out_patch --lang zh_CN
```

可选：加入 `--gen-hooks` 自动生成语言切换器和字体配置 Hook：

```pwsh
python tools/build.py demo -o outputs/build_cn --mode auto --zh-mirror outputs/out_patch --lang zh_CN --gen-hooks --font "SourceHanSansCN-Regular.otf"
```

二次自检会阻止 `.zh.rpy` 残留或 mirror/tl 双载冲突。

## 6) LLM 两段式翻译（可选）

```pwsh
# 分包（跳过已有译文）
python tools/split.py outputs/prefilled/prefilled.jsonl outputs/llm_batches --skip-has-zh --max-tokens 2000

# API 翻译（可选速率限制 + 批量模式）
python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
    --provider deepseek --api-key YOUR_KEY --workers 20 \
    --rpm 60 --batch-mode --batch-size 10

# 合并结果（仅填充空译；冲突按质量评分选择最优）
python tools/merge.py outputs/prefilled/prefilled.jsonl outputs/llm_results -o outputs/prefilled/prefilled_llm_merged.jsonl --conflict-tsv outputs/qa/llm_conflicts.tsv
```

随后重新执行 validate → patch → build。

## 7) QA 自动修复（可选）

当 QA 报告出现以下常见问题时，可用自动修复快速处理：


```pwsh
python tools/autofix.py outputs/extract/project_en_for_grok.jsonl outputs/prefilled/prefilled.jsonl -o outputs/prefilled/prefilled_autofixed.jsonl
```
