# API 翻译指南

本文档介绍所有云端 API 和免费机翻方案，包括 DeepSeek、Grok (xAI)、OpenAI、Claude 等。

---

## API 提供商对比

| 提供商 | 模型 | 成本/百万Token | 质量 | 速度 | 推荐指数 |
|--------|------|----------------|------|------|----------|
| **DeepSeek** | deepseek-chat | ￥1 | ⭐⭐⭐⭐ | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ |
| Claude Haiku | claude-3-haiku | ￥3.5 | ⭐⭐⭐⭐ | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ |
| **Grok** | grok-4-fast-reasoning | ￥1.4 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ |
| OpenAI GPT-4o | gpt-4o | ￥35 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | ⭐⭐⭐ |
| Claude Sonnet | claude-3.5-sonnet | ￥21 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ |

**推荐选择：**
- 💰 **追求性价比**：DeepSeek 或 Grok Fast（质量好且最便宜）
- 🎯 **追求质量**：Claude Sonnet 或 Grok 4（贵但效果好）
- ⚡ **追求速度**：DeepSeek（并发高，响应快）

---

## 快速开始

### 1. DeepSeek API（推荐）

**获取 API Key：**
1. 访问 https://platform.deepseek.com/
2. 注册账号并充值（最低 ￥10）
3. 创建 API Key

**翻译命令：**
```bash
python tools/translate_api.py outputs/llm_batches \
  -o outputs/llm_results \
  --provider deepseek \
  --api-key YOUR_API_KEY \
  --workers 20
```

**成本估算：**
- 小型游戏 (3000条)：约 ￥2-5
- 中型游戏 (5万条)：约 ￥10-30
- 大型游戏 (10万条)：约 ￥20-50

---

### 2. Grok API (xAI)

**获取 API Key：**
1. 访问 https://console.x.ai 注册并创建 API Key

**单文件模式（推荐）：**
```powershell
python tools/translate_grok.py outputs/extract/project_en_for_grok.jsonl `
    -o outputs/results `
    --api-key YOUR_XAI_API_KEY `
    --model grok-4-fast-reasoning
```

**批次目录模式（超大项目 > 50 万行时）：**
```powershell
# 1. 分批
python tools/split.py outputs/extract/project_en_for_grok.jsonl `
    outputs/llm_batches --skip-has-zh --max-tokens 50000

# 2. 批量翻译
python tools/translate_grok.py outputs/llm_batches -o outputs/llm_results `
    --api-key YOUR_XAI_API_KEY --model grok-4-fast-reasoning `
    --workers 10 --batch-size 50

# 3. 合并结果
python tools/merge.py outputs/extract/project_en_for_grok.jsonl `
    outputs/llm_results -o outputs/final/translated.jsonl
```

**特点：**
- ✅ 2M tokens 上下文，可直接处理大文件
- ✅ 支持断点续传（API 失败自动重试）
- ✅ 100 万字游戏汉化只需 ¥8.5（grok-4-fast-reasoning）

**Grok 模型选择：**

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 大规模游戏（100万字+） | `grok-4-fast-reasoning` | 成本低、速度快、2M 上下文 |
| 追求极致质量 | `grok-4` | 最强性能，但贵 15 倍 |

**Grok `translate_grok.py` 参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `source` | 输入 JSONL 文件或批次目录 | 必填 |
| `-o, --output` | 输出目录 | 必填 |
| `--api-key` | xAI API Key | 必填 |
| `--model` | 模型名称 | `grok-4-fast-reasoning` |
| `--workers` | 并发数 | 5 |
| `--batch-size` | 每次请求行数 | 50 |

---

### 3. OpenAI API

**获取 API Key：**
1. 访问 https://platform.openai.com/
2. 注册并充值
3. 创建 API Key

```bash
python tools/translate_api.py outputs/llm_batches \
  -o outputs/llm_results \
  --provider openai \
  --api-key YOUR_API_KEY \
  --workers 10
```

---

### 4. Claude API (Anthropic)

**获取 API Key：**
1. 访问 https://console.anthropic.com/
2. 注册并充值
3. 创建 API Key

```bash
# Haiku（快速便宜）
python tools/translate_api.py outputs/llm_batches \
  -o outputs/llm_results \
  --provider claude --api-key YOUR_API_KEY --workers 15

# Sonnet（质量和价格平衡）
python tools/translate_api.py outputs/llm_batches \
  -o outputs/llm_results \
  --provider claude-sonnet --api-key YOUR_API_KEY --workers 10
```

---

## 免费机器翻译

无需 API Key，完全免费：

### Google Translate（推荐）

```bash
python tools/translate_free.py outputs/llm_batches \
  -o outputs/google_results --provider google --workers 10
```

### Bing Translator

```bash
python tools/translate_free.py outputs/llm_batches \
  -o outputs/bing_results --provider bing --workers 10
```

### DeepL Free

```bash
python tools/translate_free.py outputs/llm_batches \
  -o outputs/deepl_results --provider deepl \
  --api-key YOUR_FREE_API_KEY --workers 5
```

> DeepL 免费版：https://www.deepl.com/pro-api ，每月 50 万字符。

---

## 推荐工作流程

### 方案 A：纯 API 流程（推荐）

```bash
# 1. 提取文本
python tools/extract.py "游戏目录" --glob "**/*.rpy" -o outputs/extract

# 2. 分批处理
python tools/split.py outputs/extract/project_en_for_grok.jsonl outputs/llm_batches

# 3. DeepSeek / Grok 翻译
python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
  --provider deepseek --api-key YOUR_KEY --workers 20

# 4. 合并结果
python tools/merge.py outputs/extract/project_en_for_grok.jsonl outputs/llm_results \
  -o outputs/merged.jsonl

# 5. 质量检查
python tools/validate.py outputs/extract/project_en_for_grok.jsonl outputs/merged.jsonl \
  --qa-html outputs/qa/qa.html --ignore-ui-punct

# 6. 回填
python tools/patch.py "游戏目录" outputs/merged.jsonl -o outputs/patched --advanced
```

### 方案 B：混合流程（省钱）

```bash
# 1. Google 机翻打底（免费）
python tools/translate_free.py outputs/llm_batches -o outputs/google_base \
  --provider google --workers 10

# 2. 检测质量差的部分
python tools/fix_english_leakage.py outputs/google_base --check-only

# 3. 用 DeepSeek API 重翻关键部分
python tools/translate_api.py outputs/to_refine -o outputs/refined \
  --provider deepseek --api-key YOUR_KEY --workers 20

# 4. 合并基础翻译 + 优化翻译
python tools/merge.py outputs/extract/project_en_for_grok.jsonl \
  outputs/google_base outputs/refined -o outputs/merged.jsonl
```

---

## 高级参数

### translate_api.py 参数

```bash
python tools/translate_api.py <input> -o <output> \
  --provider <deepseek|grok|openai|openai-gpt4|claude|claude-sonnet> \
  --api-key <YOUR_KEY> \
  --workers 20 \           # 并发数
  --timeout 30 \           # 超时时间（秒）
  --temperature 0.2 \      # 采样温度（0.1-0.3 保守）
  --rpm 60 \               # 每分钟最大请求数（速率限制）⭐
  --rps 5 \                # 每秒最大请求数 ⭐
  --tpm 100000 \           # 每分钟最大 token 数 ⭐
  --batch-mode \           # 启用批量 JSON 模式 ⭐
  --batch-size 10 \        # 批量大小 ⭐
  --prompt-template data/prompt_template.json  # 自定义 Prompt ⭐
```

### translate_free.py 参数

```bash
python tools/translate_free.py <input> -o <output> \
  --provider <google|bing|deepl> \
  --workers 10 \           # 并发数
  --timeout 15 \           # 超时时间
  --delay 0.1              # 请求间隔（避免限流）
```

---

## 翻译保护机制

所有 API 翻译工具均内置：
- ✅ 占位符保护：`[pov]`, `[name]`, `[mother]` 等
- ✅ Ren'Py 标签保护：`{i}`, `{b}`, `{color=...}`, `{w}`, `{nw}`
- ✅ 格式化字符串保护：`%(name)s`, `%(n)d`
- ✅ 特殊字符保护：`\n`, `\t`

---

## 常见问题

### API Key 无效

**错误：** `401 Unauthorized`

**解决：** 检查 Key 是否正确复制（无空格），检查账户余额是否充足。

### 速率限制

**错误：** `429 Too Many Requests`

**解决：**
1. 使用三级速率限制（推荐）：
```bash
python tools/translate_api.py ... --rpm 60 --rps 5 --tpm 100000
```
2. 降低 `--workers` 并发数（DeepSeek: 20→10，OpenAI: 10→5）
3. 启用批量模式减少请求次数：`--batch-mode --batch-size 10`

### 超时错误

**解决：** 增加 `--timeout`（30→60），检查网络连接。

### 翻译质量差

```bash
# 检测问题
python tools/fix_english_leakage.py outputs/llm_results --check-only

# 自动修复（使用更好的模型）
python tools/fix_english_leakage.py outputs/llm_results --fix --model qwen3:8b
```

---

## 速率限制详解

v3.0 内置三级速率限制器 `RateLimiter`，精确控制 API 调用频率：

| 参数 | 功能 | 适用场景 |
|------|------|----------|
| `--rpm 60` | 每分钟最大 60 次请求 | 所有有配额限制的 API |
| `--rps 5` | 每秒最大 5 次请求 | 突发限制严格的 API |
| `--tpm 100000` | 每分钟最大 10 万 token | 有 token 配额的 API |

**各 API 推荐设置：**

| 提供商 | `--rpm` | `--rps` | `--tpm` |
|--------|---------|---------|---------|
| DeepSeek | 60 | 5 | 100000 |
| OpenAI GPT-4o | 60 | 10 | 90000 |
| Claude | 60 | 5 | 100000 |
| Grok | 60 | 10 | 200000 |

如果不指定，则不限速（依赖 API 自身限制 + 重试）。

---

## 批量 JSON 模式

将多条翻译文本合并为一次 API 调用，大幅减少请求数和成本：

```bash
python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
  --provider deepseek --api-key YOUR_KEY \
  --batch-mode --batch-size 10
```

**工作原理：**
1. 将 10 条待翻译文本打包为 JSON key-value 格式
2. 发送一次 API 请求翻译全部 10 条
3. 解析返回的 JSON，拆分到各条记录
4. 如果请求失败，自动递归拆分（10 → 5+5 → 2+3+2+3 → ...）

**优势：**
- API 调用次数减少 90%
- 成本降低（输入 token 中的 system prompt 被复用）
- 适合大规模翻译

---

## 自定义 Prompt 模板

使用 JSON 文件定义翻译提示词，无需修改代码：

```bash
python tools/translate_api.py ... --prompt-template data/prompt_template.json
```

模板使用 OpenAI messages 格式，支持占位符：
- `#SOURCE_LANGUAGE#` → 源语言名称
- `#TARGET_LANGUAGE#` → 目标语言名称
- `#JSON_DATA#` → 翻译数据

默认模板见 `data/prompt_template.json`。

---

## 成本控制建议

1. **先测试小批次**：`python tools/translate_api.py outputs/llm_batches/batch_0001.jsonl -o outputs/test --provider deepseek --api-key YOUR_KEY`
2. **使用 DeepSeek / Grok Fast**：最便宜的 AI 翻译
3. **混合机翻 + AI**：Google 打底 + DeepSeek 修正关键部分
4. **避免重复翻译**：使用 `--skip-exists` 跳过已翻译内容

---

## 性能对比实测

测试环境：basement.rpy (3078 条文本)

| 方案 | 耗时 | 成本 | 质量 | 综合评分 |
|------|------|------|------|----------|
| 本地 Ollama 7B | 30+ 分钟 | ￥0 | ⭐⭐ | ⭐⭐ |
| Google 机翻 | 9 分钟 | ￥0 | ⭐⭐⭐ | ⭐⭐⭐ |
| **DeepSeek API** | **2-3 分钟** | **￥3** | **⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** |
| Grok Fast | 3-4 分钟 | ￥8 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Claude Sonnet | 3-4 分钟 | ￥20 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**结论：DeepSeek API 和 Grok Fast 是最佳选择。**
