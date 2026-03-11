# 完整安装和使用指南

本指南包含从零开始配置环境、GPU 加速优化到分享部署的所有内容。

---

## 快速开始（推荐）

### 全新电脑

```bash
第1步：双击 INSTALL_ALL.bat
      → 自动下载并安装所有环境（约5GB）
      → 等待 10-30 分钟

第2步：双击 START.bat
      → 自动检查环境
      → 自动启动工具
      → 开始翻译
```

### 已有环境

```bash
直接双击 START.bat → 开始使用
```

---

## 系统要求

### 必需
- **操作系统**: Windows 10/11（64位）
- **磁盘空间**: 至少 10GB

### 推荐（GPU 加速）
- **NVIDIA GPU**: 至少 6GB VRAM
- **驱动**: 最新版 NVIDIA 驱动

---

## 🔧 自动安装详解

### INSTALL_ALL.bat 功能

自动下载并安装：

1. **Python 3.12** (~30MB)
   - 从官网下载
   - 静默安装
   - 自动添加到 PATH

2. **Python 依赖库** (~10MB)
   - rich（彩色输出）
   - rapidfuzz（模糊匹配）
   - 使用清华镜像加速

3. **Ollama** (~100MB)
   - 从官网下载
   - 静默安装
   - 自动启动服务

4. **qwen2.5:7b 模型** (~4.7GB)
   - 最适合翻译的模型
   - 适合 8GB VRAM

### 安装时间
- 国内网络: 10-20分钟
- 国际网络: 20-40分钟

### 安装失败？

运行 START.bat 会提示缺少的组件，然后：

**手动安装**：
1. Python: https://www.python.org/downloads/
   - ⚠️ 安装时勾选 "Add Python to PATH"
2. Ollama: https://ollama.ai/
3. 依赖: `pip install -r requirements.txt`
4. 模型: `ollama pull qwen2.5:7b`

---

## 🎮 START.bat 功能

一键启动器，集成：

### ✅ 自动环境检查
- Python 是否安装
- 依赖库是否完整（缺失自动安装）
- Ollama 是否安装
- 翻译模型是否下载（可选择立即下载）
- GPU 检测（可选）

### ✅ 自动修复
- 依赖缺失 → 自动安装
- 模型未下载 → 询问是否下载
- GPU 未检测到 → 提示但不影响使用

### ✅ 一键启动
环境检查通过后自动启动主程序

---

## 📤 分享到其他电脑

### 方法一：使用打包工具（推荐）

**在当前电脑**：
```bash
1. 双击 PACKAGE.bat
2. 压缩生成的文件夹
3. 分享压缩包
```

**在新电脑**：
```bash
1. 解压文件
2. 双击 INSTALL_ALL.bat（自动安装环境）
3. 双击 START.bat（开始使用）
```

### 方法二：手动复制

**需要复制**：
```
Renpy汉化/
├── tools/           ✅ 必需
├── src/             ✅ 必需（核心库）
├── data/            ✅ 必需
├── docs/            ✅ 推荐
├── START.bat     ✅ 必需
├── INSTALL_ALL.bat  ✅ 必需
├── PACKAGE.bat      ✅ 推荐
├── README.md        ✅ 推荐
├── requirements.txt ✅ 必需
└── pyproject.toml   ⚠️ 可选
```

**不需要复制**：
- ❌ `outputs/` - 之前的翻译输出（太大）
- ❌ `__pycache__/` - Python 缓存

### 离线安装（无网络环境）

**在有网络的电脑**：
1. 下载安装包：
   - Python: https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
   - Ollama: https://ollama.com/download/OllamaSetup.exe
2. 导出 Ollama 模型：
   - 位置: `C:\Users\用户名\.ollama\models`
   - 复制整个 `models` 文件夹

**在目标电脑**：
1. 手动安装 Python 和 Ollama
2. 复制模型文件到相同位置
3. 安装依赖: `pip install -r requirements.txt`

---

## 🎯 使用流程

### 翻译游戏

```bash
1. 双击 START.bat
2. 选择游戏目录（包含 game/ 文件夹的根目录）
3. 选择模型（推荐: qwen2.5:7b 或 huihui_ai/qwen2.5-abliterate:7b）
4. 配置选项：
   - 跳过非对话内容: ✅ 推荐勾选
   - 并发线程: 4（默认）
   - 自动保存间隔: 50（默认）
5. 点击"开始翻译"
6. 等待完成（时间取决于游戏大小和硬件）
```

### 翻译完成后

自动生成：
- `outputs/[游戏名]/cn_build/` - 中文版游戏包
- `outputs/[游戏名]/qa/` - 质量检查报告

---

## ❓ 常见问题

### Q1: INSTALL_ALL.bat 下载失败

**A**: 检查网络连接，或手动安装：
1. Python → https://www.python.org/downloads/
2. Ollama → https://ollama.ai/
3. 然后运行依赖安装

### Q2: 提示 "Python 未安装" 但已安装

**A**: 重启电脑让环境变量生效

### Q3: Ollama 下载模型很慢

**A**: 
- 国内用户: 正常，耐心等待 10-30 分钟
- 可以使用代理加速
- 或在其他电脑下载后复制模型文件

### Q4: 翻译速度很慢

**A**: 检查以下项：
1. 是否使用了推荐的模型（qwen2.5:7b）
2. GPU 是否被识别（运行 `nvidia-smi`）
3. 是否选择了合适的并发数（推荐4）
4. 检查 GPU 利用率（应该 >80%）

### Q5: 没有 NVIDIA GPU 可以用吗？

**A**: 可以！会使用 CPU 模式：
- 速度较慢（约慢 5-10 倍）
- 但完全可用
- 推荐使用更小的模型（qwen2.5:7b）

### Q6: 翻译结果有代码标识符

**A**: 这是过滤规则的问题，已在新版本修复：
- 重新运行 START.bat 使用最新版本
- 或手动清理: `Remove-Item outputs\[游戏名]\llm_results\* -Force`

### Q7: 能同时翻译多个游戏吗？

**A**: 不推荐，但可以：
- Ollama 一次只能加载一个模型
- 并发翻译会导致速度变慢
- 建议一个一个来

---

## 选择合适的模型

| 模型 | 大小 | VRAM | 速度 | 质量 | 推荐场景 |
|------|------|------|------|------|----------|
| qwen2.5:3b | 2GB | 2GB | 极快 | 可接受 | 轻量测试 |
| qwen2.5:7b | 4.7GB | 6GB | 快 | 优秀 | 8GB VRAM（推荐） |
| qwen2.5:14b | 9GB | 10GB | 中 | 最佳平衡 | 12GB+ VRAM |
| qwen2.5:32b | 19GB | 18GB+ | 慢 | 顶级 | 24GB VRAM |

```bash
# 安装模型
ollama pull qwen2.5:7b    # 推荐：速度与质量平衡
ollama pull qwen2.5:14b   # 更好质量
```

> **注意**：不推荐使用 DeepSeek R1 系列做翻译——R1 是推理模型，会生成 `<think>...</think>` 思考过程，污染翻译输出且速度慢。

---

## GPU 加速配置

### 自动配置

`START.bat` 启动时会自动检测 GPU 并配置 Ollama：

```powershell
$env:OLLAMA_NUM_GPU = "999"      # 尽可能多的层放到 GPU
$env:OLLAMA_GPU_OVERHEAD = "0"   # 减少 GPU 开销保留
```

### CUDA 加速（可选）

如果已安装 CUDA Toolkit，可手动启用以获得额外 10-15% 加速：

```powershell
.\tools\init_cuda.ps1
```

**CUDA 配置要求：**
- NVIDIA GPU（计算能力 6.0+）
- CUDA Toolkit 11.0+（推荐 12.x）
- cuDNN（与 CUDA 版本匹配）

> 没有 CUDA 也完全可以使用——Ollama 内置 GPU 支持已经很快。

### 验证 GPU 使用

```powershell
# 查看 GPU 信息
nvidia-smi

# 查看 Ollama 模型加载情况
ollama ps

# 实时监控（另一个终端窗口）
nvidia-smi -l 1
```

### GPU 性能参考（qwen2.5 系列）

| 模型 | GPU 使用率 | 速度 (tokens/s) | 显存占用 |
|------|-----------|----------------|----------|
| qwen2.5:3b | 100% | ~150 | 2 GB |
| qwen2.5:7b | 100% | ~100 | 4.7 GB |
| qwen2.5:14b | 85-95% | ~60 | 8-10 GB |
| qwen2.5:32b | 40-50% | ~30 | 16+ GB |

### GPU 常见问题

**GPU 显存不足：**
```bash
ollama stop <模型名>       # 停止当前模型
ollama pull qwen2.5:7b    # 换更小的模型
```

**GPU 未使用：**
- 检查 `ollama ps`，确认 PROCESSOR 列显示 GPU 百分比
- 检查环境变量：`$env:OLLAMA_NUM_GPU` 应该 > 0

**GPU 问题应急：** 双击 `START_SAFE.bat` 以 CPU 模式启动。

---

## 分享到其他电脑

### 方法一：使用打包工具（推荐）

```bash
# 当前电脑
1. 双击 PACKAGE.bat → 生成打包文件夹
2. 压缩后分享

# 新电脑
1. 解压
2. 双击 INSTALL_ALL.bat
3. 双击 START.bat
```

### 方法二：手动复制

**需要复制：** `tools/`, `data/`, `src/`, `START.bat`, `INSTALL_ALL.bat`, `requirements.txt`

**不需要复制：** `outputs/`（翻译产出）, `__pycache__/`

### 离线安装

在有网络的电脑预先下载：
1. Python: https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
2. Ollama: https://ollama.com/download/OllamaSetup.exe
3. 模型文件: `C:\Users\用户名\.ollama\models\`（整个目录）
