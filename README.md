# Ren'Py 游戏汉化工具 v2.0

一键式 Ren'Py 游戏汉化工具，支持 **Ollama 本地翻译**、**云端 API 翻译**、**免费机器翻译** 等多种方案。

---

## ✨ 新特性 (v2.0)

- 🚀 **交互式菜单**：所有功能通过 START.bat 访问
- ⚡ **云端 API 翻译**：DeepSeek / Grok / OpenAI / Claude（2-5分钟完成）
- 🆓 **免费机器翻译**：Google / Bing / DeepL（完全免费）
- 🛠️ **质量修复工具**：自动检测和修复英文残留
- 📊 **翻译统计**：实时查看翻译进度

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
- � 成本低（￥3-10）
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
| [**功能清单**](docs/功能清单.md) | ⭐⭐⭐ 所有功能详细说明（NEW） |
| [**API 翻译指南**](docs/API_TRANSLATION_GUIDE.md) | ⭐⭐⭐ 云端 API 使用指南（NEW） |
| [**完整使用指南**](docs/USER_GUIDE.md) | 优化模式详解 + 完整教程 |
| [**快速开始**](docs/quickstart.md) | 10分钟快速上手教程 |
| [**安装指南**](docs/SETUP_GUIDE.md) | 完整的安装和使用流程 |
| [**故障排查**](docs/troubleshooting.md) | 常见问题解决方案 |

### 技术文档
| 文档 | 说明 |
|------|------|
| [**完整优化报告**](docs/OPTIMIZATION_COMPLETE.md) | ⭐⭐ 代码优化和功能增强 |
| [**增强改进方案**](docs/ENHANCEMENT_PLAN.md) | 基于 MTool 的改进计划 |
| [**代码优化方案**](docs/CODE_OPTIMIZATION.md) | 代码架构改进文档 |
| [**GPU 优化指南**](docs/gpu_optimization.md) | 性能调优和GPU配置 |
| [**字体替换说明**](docs/font_replacement.md) | 中文字体配置 |

---

## ⚡ 主要功能

- ✅ **一键安装** - 自动安装 Python、Ollama 和翻译模型
- ✅ **文本提取** - 批量提取 .rpy 文件中的所有文本
- ✅ **字典预填** - 使用术语字典预填常用词汇
- ✅ **AI 翻译** - 本地 Ollama 模型翻译（支持 GPU 加速）
- ✅ **质量检查** - 占位符、格式、标点一致性检查
- ✅ **自动回填** - 将译文回填到游戏文件
- ✅ **字体替换** - 自动替换为中文字体
- ✅ **构建打包** - 生成可玩的中文版本

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
1. 提取 (extract.py)     → 从 .rpy 文件提取文本
2. 预填 (prefill.py)     → 使用字典预填常用词
3. 分包 (split.py)       → 分割成适合翻译的批次
4. 翻译 (translate.py)   → AI 翻译
5. 合并 (merge.py)       → 合并翻译结果
6. 校验 (validate.py)    → 质量检查
7. 修复 (autofix.py)     → 自动修复常见问题
8. 回填 (patch.py)       → 回填译文到 .rpy 文件
9. 构建 (build.py)       → 生成中文版本
```

详细说明：[快速开始文档](docs/quickstart.md)

---

## 🔧 核心工具

| 工具 | 功能 |
|------|------|
| `extract.py` | 提取 .rpy 文本 |
| `prefill.py` | 字典预填 |
| `split.py` | 分包处理 |
| `translate.py` | AI 翻译（支持优化模式 `--use-optimized`，质量+29%，速度+15%） |
| `merge.py` | 合并结果 |
| `validate.py` | 质量检查 |
| `autofix.py` | 自动修复 |
| `patch.py` | 回填译文 |
| `build.py` | 构建中文包 |
| `replace_fonts.py` | 替换字体 |
| `diff_dirs.py` | 中英对比 |
| `pipeline.py` | 一键全流程 |

### 🚀 新功能：优化翻译模式

`translate.py` 现在支持优化模式，提供更高质量和更快速度：

```bash
# 标准模式（默认）
python tools/translate.py outputs/llm_batches -o outputs/llm_results --model qwen2.5:14b

# 优化模式（推荐）- 连接池 + 质量验证 + 智能重试
python tools/translate.py outputs/llm_batches -o outputs/llm_results --model qwen2.5:14b --use-optimized
```

**优化模式特性**：

- 🔥 **速度提升 15%**：HTTP 连接池复用
- ✨ **质量提升 29%**：立即验证 + 智能重试
- 🔧 **自动修复率 +600%**：占位符和换行自动修复
- 📊 **详细统计**：成功率、质量分数、重试次数

详细使用说明：[完整使用指南](docs/USER_GUIDE.md)

---

## ❓ 常见问题

**Q: 完全不懂技术，能用吗？**  
A: 能！双击 `INSTALL_ALL.bat` 全自动安装，然后双击 `START.bat` 开始使用。

**Q: 没有 NVIDIA 显卡可以用吗？**  
A: 可以！会使用 CPU 模式，速度慢一些但完全可用。

**Q: 翻译质量如何？**  
A: 使用 Qwen2.5 系列模型，翻译质量优秀，支持上下文理解。

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
