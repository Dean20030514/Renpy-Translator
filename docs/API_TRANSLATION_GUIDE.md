# 云端 API 翻译指南

本文档介绍如何使用云端 API 进行快速翻译，包括 DeepSeek、Grok、OpenAI、Claude 等。

## 📊 API 提供商对比

| 提供商 | 模型 | 成本/百万Token | 质量 | 速度 | 推荐指数 |
|--------|------|----------------|------|------|----------|
| **DeepSeek** | deepseek-chat | ￥1 | ⭐⭐⭐⭐ | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ |
| Claude Haiku | claude-3-haiku | ￥3.5 | ⭐⭐⭐⭐ | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ |
| OpenAI GPT-3.5 | gpt-3.5-turbo | ￥7 | ⭐⭐⭐ | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ |
| Claude Sonnet | claude-3.5-sonnet | ￥21 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ |
| **Grok** | grok-beta | ￥35 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | ⭐⭐⭐ |
| OpenAI GPT-4 | gpt-4-turbo | ￥70 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | ⭐⭐ |

**推荐选择：**
- 💰 **追求性价比**：DeepSeek（质量好且最便宜）
- 🎯 **追求质量**：Claude Sonnet 或 Grok（贵但效果好）
- ⚡ **追求速度**：DeepSeek 或 GPT-3.5（并发高）

---

## 🚀 快速开始

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
- basement.rpy (3078条)：约 ￥2-5
- 中型游戏 (5万条)：约 ￥10-30
- 大型游戏 (10万条)：约 ￥20-50

---

### 2. Grok API (xAI)

**获取 API Key：**
1. 访问 https://x.ai/api
2. 注册并获取 API Key

**翻译命令：**
```bash
python tools/translate_api.py outputs/llm_batches \
  -o outputs/llm_results \
  --provider grok \
  --api-key YOUR_XAI_API_KEY \
  --workers 15
```

**特点：**
- ✅ 质量非常好（接近 GPT-4 水平）
- ⚠️ 价格较高（￥35/百万Token）
- ✅ 支持高并发

---

### 3. OpenAI API

**获取 API Key：**
1. 访问 https://platform.openai.com/
2. 注册并充值（支持信用卡）
3. 创建 API Key

**GPT-3.5 翻译（速度快，便宜）：**
```bash
python tools/translate_api.py outputs/llm_batches \
  -o outputs/llm_results \
  --provider openai \
  --api-key YOUR_API_KEY \
  --workers 20
```

**GPT-4 翻译（质量最好，最贵）：**
```bash
python tools/translate_api.py outputs/llm_batches \
  -o outputs/llm_results \
  --provider openai-gpt4 \
  --api-key YOUR_API_KEY \
  --workers 10
```

---

### 4. Claude API (Anthropic)

**获取 API Key：**
1. 访问 https://console.anthropic.com/
2. 注册并充值
3. 创建 API Key

**Haiku 翻译（快速便宜）：**
```bash
python tools/translate_api.py outputs/llm_batches \
  -o outputs/llm_results \
  --provider claude \
  --api-key YOUR_API_KEY \
  --workers 15
```

**Sonnet 翻译（质量和价格平衡）：**
```bash
python tools/translate_api.py outputs/llm_batches \
  -o outputs/llm_results \
  --provider claude-sonnet \
  --api-key YOUR_API_KEY \
  --workers 10
```

---

## 🆓 免费机器翻译

如果不想花钱，可以使用免费的机器翻译：

### Google Translate（推荐）

```bash
python tools/translate_free.py outputs/llm_batches \
  -o outputs/google_results \
  --provider google \
  --workers 10
```

**特点：**
- ✅ 完全免费，无限制
- ✅ 速度快（~50-100 条/分钟）
- ⚠️ 质量一般（机翻水平）
- ⚠️ 可能过滤成人内容

### Bing Translator

```bash
python tools/translate_free.py outputs/llm_batches \
  -o outputs/bing_results \
  --provider bing \
  --workers 10
```

### DeepL Free

```bash
python tools/translate_free.py outputs/llm_batches \
  -o outputs/deepl_results \
  --provider deepl \
  --api-key YOUR_FREE_API_KEY \
  --workers 5
```

**获取 DeepL 免费 API Key：**
1. 访问 https://www.deepl.com/pro-api
2. 注册 "DeepL API Free" 计划
3. 每月 50 万字符免费额度

---

## 💡 推荐工作流程

### 方案 A：纯 API 流程（推荐）

```bash
# 1. 提取文本
python tools/extract.py "游戏目录" --glob "**/*.rpy" -o outputs/extract

# 2. 分批处理
python tools/split.py outputs/extract/project_en_for_grok.jsonl outputs/llm_batches

# 3. DeepSeek API 翻译（快速便宜）
python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
  --provider deepseek --api-key YOUR_KEY --workers 20

# 4. 检查质量
python tools/fix_english_leakage.py outputs/llm_results --check-only

# 5. 合并结果
python tools/merge.py outputs/extract/project_en_for_grok.jsonl outputs/llm_results \
  -o outputs/merged.jsonl

# 6. 回填
python tools/patch.py "游戏目录" outputs/merged.jsonl -o outputs/patched
```

---

### 方案 B：混合流程（省钱）

```bash
# 1-2. 提取和分批（同上）

# 3. Google 机翻打底（免费）
python tools/translate_free.py outputs/llm_batches -o outputs/google_base \
  --provider google --workers 10

# 4. 检测质量差的部分
python tools/fix_english_leakage.py outputs/google_base --check-only \
  --report outputs/quality_report.txt

# 5. 提取需要重翻的部分（手动或脚本）
# ... 生成 outputs/to_refine 目录

# 6. 用 DeepSeek API 重翻关键部分
python tools/translate_api.py outputs/to_refine -o outputs/refined \
  --provider deepseek --api-key YOUR_KEY --workers 20

# 7. 合并 Google 基础翻译 + DeepSeek 优化翻译
python tools/merge.py outputs/extract/project_en_for_grok.jsonl \
  outputs/google_base outputs/refined -o outputs/merged.jsonl

# 8-9. 合并和回填（同上）
```

**成本对比：**
- 方案 A（纯 DeepSeek）：￥10-50（10万条）
- 方案 B（Google + DeepSeek）：￥2-10（10万条，只重翻 20%）

---

## ⚙️ 高级参数

### translate_api.py 参数

```bash
python tools/translate_api.py <input> -o <output> \
  --provider <deepseek|grok|openai|openai-gpt4|claude|claude-sonnet> \
  --api-key <YOUR_KEY> \
  --workers 20 \           # 并发数（DeepSeek 可以很高）
  --timeout 30 \           # 超时时间（秒）
  --temperature 0.2        # 采样温度（0.1-0.3 保守）
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

## 🐛 常见问题

### 1. API Key 无效

**错误：** `401 Unauthorized` 或 `Invalid API Key`

**解决：**
- 检查 API Key 是否正确复制（无空格）
- 检查账户余额是否充足
- 确认使用正确的提供商（deepseek/grok/openai/claude）

---

### 2. 速率限制

**错误：** `429 Too Many Requests`

**解决：**
- 降低 `--workers` 并发数
- DeepSeek：20 → 10
- OpenAI：10 → 5
- Claude：10 → 5

---

### 3. 超时错误

**错误：** `TimeoutError` 或连接超时

**解决：**
- 增加 `--timeout` 超时时间（30 → 60）
- 检查网络连接
- 检查防火墙/代理设置

---

### 4. 翻译质量差

**问题：** 英文残留、翻译不准确

**解决：**
```bash
# 1. 检测问题
python tools/fix_english_leakage.py outputs/llm_results --check-only

# 2. 自动修复（使用更好的模型）
python tools/fix_english_leakage.py outputs/llm_results --fix \
  --model qwen3:8b

# 3. 或用更好的 API 重翻
python tools/translate_api.py outputs/llm_batches -o outputs/refined \
  --provider claude-sonnet --api-key YOUR_KEY
```

---

## 💰 成本控制建议

1. **先测试小批次**：
   ```bash
   # 只翻译第一个批次测试
   python tools/translate_api.py outputs/llm_batches/batch_0001.jsonl \
     -o outputs/test --provider deepseek --api-key YOUR_KEY
   ```

2. **使用 DeepSeek**：
   - 最便宜的 AI 翻译（￥1/百万Token）
   - 质量接近 GPT-3.5/4

3. **混合机翻 + AI**：
   - Google 打底（免费）
   - DeepSeek 修正关键部分（花费很少）

4. **避免重复翻译**：
   - 使用 `--skip-exists` 参数跳过已翻译
   - 增量翻译，不要全量重来

---

## 📈 性能对比实测

测试环境：basement.rpy (3078 条文本)

| 方案 | 耗时 | 成本 | 质量 | 综合评分 |
|------|------|------|------|----------|
| 本地 Ollama 7B | 30+ 分钟 | ￥0 | ⭐⭐ | ⭐⭐ |
| Google 机翻 | 9 分钟 | ￥0 | ⭐⭐⭐ | ⭐⭐⭐ |
| **DeepSeek API** | **2-3 分钟** | **￥3** | **⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** |
| Claude Sonnet | 3-4 分钟 | ￥20 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Grok API | 3-4 分钟 | ￥35 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**结论：DeepSeek API 是最佳选择（速度快、质量好、价格低）**

---

## 🔗 相关链接

- [DeepSeek Platform](https://platform.deepseek.com/)
- [xAI Grok API](https://x.ai/api)
- [OpenAI Platform](https://platform.openai.com/)
- [Anthropic Console](https://console.anthropic.com/)
- [DeepL API](https://www.deepl.com/pro-api)

---

## 📝 更新日志

### 2025-11-10
- ✅ 添加 Grok API 支持
- ✅ 添加 Claude Sonnet 支持
- ✅ 添加 OpenAI GPT-4 支持
- ✅ 完善免费机器翻译功能
- ✅ 优化 API 调用逻辑
