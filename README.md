# Ren'Py 游戏汉化工具 v3.0

一键式 Ren'Py 游戏汉化工具，支持 **Ollama 本地翻译**、**云端 API 翻译**、**免费机器翻译** 等多种方案。

---

## ✨ 新特性 (v3.0)

- 📦 **RPA 解包**：自动解包 RPA-2.0/3.0 存档，提取 .rpy/.rpyc 脚本
- 🪝 **运行时 Hook**：语言切换器、字体配置、RPYC 提取、默认语言设置
- 🔄 **三级速率限制**：RPM/RPS/TPM 精确限速，适配各 API 配额
- 📝 **自定义 Prompt 模板**：JSON 格式可复用提示词模板
- 🚀 **批量 JSON 翻译**：多条合并请求，大幅降低 API 调用次数
- 🖥️ **屏幕文本提取**：自动识别 screen 块中的 UI 文本（按钮/标签/tooltip）
- 🔍 **英文残留检测**：上下文感知检测+自动修复
- 🎯 **术语一致性校验**：字典术语不一致自动报警+修复
- ⚡ **断点续传**：translate.py / pipeline.py 支持 `--resume` 从中断处继续
- 📊 **翻译记忆**：TM 引擎支持精确/模糊匹配，跨项目复用

---

## 🚀 快速开始

### 💻 全新电脑（零配置）

```bash
第1步：双击 INSTALL_ALL.bat → 自动安装所有环境（约5GB）
第2步：双击 START.bat → 选择翻译方案
```

### 📦 已有环境

```bash
双击 START.bat → 开始使用
```

### 🎯 三种翻译方案

**方案 1：云端 API（推荐）**
- ✅ 速度最快（2-5 分钟）
- ✅ 质量最好（接近人工）
- ✅ 成本低（￥3-10）
- 📝 支持：DeepSeek / Grok / OpenAI / Claude

**方案 2：免费机翻**
- ✅ 完全免费
- ✅ 速度较快（5-15 分钟）
- ⚠️ 质量一般（机翻水平）
- 📝 支持：Google / Bing / DeepL

**方案 3：本地 Ollama**
- ✅ 完全免费
- ✅ 完全离线
- ⚠️ 速度较慢（30-60 分钟）
- 📝 需要：Ollama + 模型（4-8GB）

---

## 📖 文档

### 用户文档
| 文档 | 说明 |
|------|------|
| [**快速开始**](docs/quickstart.md) | ⭐⭐⭐ 10 分钟快速上手教程 |
| [**完整使用指南**](docs/USER_GUIDE.md) | 功能详解 + GUI 使用 + 完整教程 |
| [**API 翻译指南**](docs/API_GUIDE.md) | 云端 API 使用指南（DeepSeek / Grok / OpenAI） |
| [**安装指南**](docs/SETUP_GUIDE.md) | 安装流程 + GPU / CUDA 配置 |
| [**故障排查**](docs/troubleshooting.md) | 常见问题解决方案 |

### 技术文档
| 文档 | 说明 |
|------|------|
| [**字体替换说明**](docs/font_replacement.md) | 中文字体配置 |
| [**开发指南**](docs/DEVELOPMENT.md) | 项目架构 + 贡献指南 |
| [**更新日志**](docs/CHANGELOG.md) | 版本变更记录 |

---

## ⚡ 主要功能

- ✅ **一键安装** - 自动安装 Python、Ollama 和翻译模型
- ✅ **RPA 解包** - 解包 RPA-2.0/3.0 存档提取 .rpy 脚本
- ✅ **文本提取** - 批量提取 .rpy 文件中的对话和屏幕文本
- ✅ **字典预填** - 使用术语字典预填常用词汇
- ✅ **AI 翻译** - 本地 Ollama / 云端 API / 免费机翻
- ✅ **速率限制** - RPM/RPS/TPM 三级限速，防止 API 封禁
- ✅ **批量翻译** - 多条合并 JSON 请求，降低调用次数
- ✅ **质量检查** - 占位符、格式、标点、术语一致性多级检查
- ✅ **自动修复** - 占位符补齐、换行修复、英文残留清除
- ✅ **自动回填** - 将译文回填到游戏文件
- ✅ **字体替换** - 自动替换为中文字体
- ✅ **运行时 Hook** - 语言切换器、字体配置、默认语言
- ✅ **构建打包** - 生成可玩的中文版本
- ✅ **断点续传** - 中断后从断点恢复

---

## 💻 系统要求

### 必需

- Windows 10/11（64位）
- 10GB 磁盘空间

### 推荐（GPU 加速）

- NVIDIA GPU（6GB+ 显存）
- 最新驱动程序

### 模型推荐

| 显存 | 推荐模型 | 大小 | 速度 |
|------|---------|------|------|
| 6-8GB | qwen2.5:7b | 4.7GB | ⚡ 快 |
| 12GB+ | qwen2.5:14b | 9GB | 🔥 中等 |
| 24GB+ | qwen2.5:32b | 19GB | 🎯 慢但最佳 |

---

## 📦 工作流程

```text
0. 解包 (unrpa.py)       → 解包 RPA 存档（可选）
1. 提取 (extract.py)     → 从 .rpy 文件提取文本（含 screen 文本）
2. 预填 (prefill.py)     → 使用字典预填常用词
3. 分包 (split.py)       → 分割成适合翻译的批次
4. 翻译 (translate*.py)  → AI 翻译（Ollama / API / 免费）
5. 合并 (merge.py)       → 合并翻译结果
6. 校验 (validate.py)    → 质量检查
7. 修复 (autofix.py)     → 自动修复常见问题
8. 回填 (patch.py)       → 回填译文到 .rpy 文件
9. 构建 (build.py)       → 生成中文版本（可含 Hook 脚本）
```

详细说明：[快速开始文档](docs/quickstart.md)

---

## 🔧 核心工具

| 工具 | 功能 |
|------|------|
| `unrpa.py` | RPA 存档解包（RPA-2.0/3.0） |
| `extract.py` | 提取 .rpy 对话和屏幕文本 |
| `prefill.py` | 字典预填 |
| `split.py` | 分包处理 |
| `translate.py` | Ollama 本地翻译（支持 `--use-optimized` 优化模式） |
| `translate_api.py` | API 翻译（DeepSeek/OpenAI/Claude，支持速率限制+批量模式） |
| `translate_grok.py` | Grok API 翻译（2M 上下文） |
| `translate_free.py` | 免费机翻（Google/Bing/DeepL） |
| `merge.py` | 合并结果（质量评分冲突解决） |
| `validate.py` | 质量检查（支持 `--autofix`） |
| `autofix.py` | 自动修复 |
| `patch.py` | 回填译文（支持 `--resume` 断点续传） |
| `build.py` | 构建中文包（支持 `--gen-hooks` 生成 Hook） |
| `gen_hooks.py` | 生成运行时 Hook 脚本（语言切换/字体/提取） |
| `replace_fonts.py` | 替换字体 |
| `pipeline.py` | 一键全流程（支持 `--resume` / `--unrpa` / `--gen-hooks`） |
| `diff_dirs.py` | 中英对比 |
| `build_memory.py` | 构建翻译记忆 (TM) |
| `fix_english_leakage.py` | 英文残留检测修复 |
| `generate_dict.py` | 术语字典生成 |

### 🚀 API 翻译增强

`translate_api.py` 支持高级控制：

```bash
# 基础用法
python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
    --provider deepseek --api-key YOUR_KEY --workers 20

# 启用速率限制（推荐用于有配额限制的 API）
python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
    --provider deepseek --api-key YOUR_KEY --rpm 60 --rps 5 --tpm 100000

# 启用批量 JSON 模式（减少 API 调用次数）
python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
    --provider deepseek --api-key YOUR_KEY --batch-mode --batch-size 10

# 使用自定义 Prompt 模板
python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
    --provider deepseek --api-key YOUR_KEY --prompt-template data/prompt_template.json
```

### 🪝 运行时 Hook 生成

```bash
# 生成所有 Hook（语言切换+字体配置+提取+默认语言）
python tools/gen_hooks.py -o "E:\MyGame\game" --lang zh_CN --font "fonts/zh.ttf"

# 仅生成语言切换器
python tools/gen_hooks.py -o hooks/ --only language --lang zh_CN

# 构建时自动生成 Hook
python tools/build.py game_dir -o output/ --gen-hooks --font "zh.ttf"
```

---

## ❓ 常见问题

**Q: 完全不懂技术，能用吗？**  
A: 能！双击 `INSTALL_ALL.bat` 全自动安装，然后双击 `START.bat` 开始使用。

**Q: 没有 NVIDIA 显卡可以用吗？**  
A: 可以！会使用 CPU 模式，速度慢一些但完全可用。也可使用云端 API 方案，无需 GPU。

**Q: 翻译质量如何？**  
A: Ollama 本地约 80-88%，DeepSeek/Grok 约 88-92%，GPT-4/Claude 约 90-95%。启用优化模式可再提升 29%。

**Q: 游戏有 RPA 存档怎么办？**  
A: 使用菜单中的"RPA 解包"功能或运行 `python tools/unrpa.py game/archive.rpa -o extracted/`。

更多问题：[故障排查文档](docs/troubleshooting.md)

---

## 🎉 开始使用

```bash
# 新电脑
双击 INSTALL_ALL.bat → 双击 START.bat

# 已有环境
双击 START.bat
```

**就这么简单！** 🚀
