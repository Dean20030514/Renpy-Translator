# 📦 完整安装和使用指南

本指南包含从零开始配置环境到分享到其他电脑的所有内容。

---

## 🚀 快速开始（推荐）

### 💻 全新电脑（什么都没装）

```bash
第1步：双击 INSTALL_ALL.bat
      → 自动下载并安装所有环境（约5GB）
      → 等待 10-30 分钟

第2步：双击 ONECLICK.bat
      → 自动检查环境
      → 自动启动工具
      → 开始翻译
```

### 📦 已有环境的电脑

```bash
直接双击 ONECLICK.bat → 开始使用
```

---

## 📋 系统要求

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

运行 ONECLICK.bat 会提示缺少的组件，然后：

**手动安装**：
1. Python: https://www.python.org/downloads/
   - ⚠️ 安装时勾选 "Add Python to PATH"
2. Ollama: https://ollama.ai/
3. 依赖: `pip install -r requirements.txt`
4. 模型: `ollama pull qwen2.5:7b`

---

## 🎮 ONECLICK.bat 功能

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
3. 双击 ONECLICK.bat（开始使用）
```

### 方法二：手动复制

**需要复制**：
```
Renpy汉化/
├── tools/           ✅ 必需
├── data/            ✅ 必需
├── docs/            ✅ 推荐
├── ONECLICK.bat     ✅ 必需
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
1. 双击 ONECLICK.bat
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
- 重新运行 ONECLICK.bat 使用最新版本
- 或手动清理: `Remove-Item outputs\[游戏名]\llm_results\* -Force`

### Q7: 能同时翻译多个游戏吗？

**A**: 不推荐，但可以：
- Ollama 一次只能加载一个模型
- 并发翻译会导致速度变慢
- 建议一个一个来

---

## 💡 高级技巧

### 选择合适的模型

| 模型 | 大小 | VRAM | 速度 | 质量 | 推荐场景 |
|------|------|------|------|------|----------|
| qwen2.5:7b | 4.7GB | 6GB | 快 | 优秀 | 8GB VRAM |
| qwen2.5:14b | 9GB | 12GB | 中 | 更好 | 12GB+ VRAM |
| qwen2.5:32b | 19GB | 24GB | 慢 | 最好 | 24GB VRAM |

### 优化翻译速度

1. **使用 GPU**: 确保 NVIDIA 驱动最新
2. **合适的模型**: 7b 模型最快
3. **并发数**: 4 是最佳平衡（不要设太高）
4. **关闭其他程序**: 释放 GPU 资源

### 批量部署（多台电脑）

1. 在一台电脑上完成 INSTALL_ALL.bat
2. 导出 Ollama 模型文件
3. 使用 PACKAGE.bat 打包工具
4. 制作包含安装程序的完整安装包
5. 在其他电脑批量部署

---

## 📞 获取更多帮助

- **GPU 优化**: 查看 `docs/gpu_optimization.md`
- **故障排查**: 查看 `docs/troubleshooting.md`
- **项目主页**: 查看 `README.md`

---

## 🎉 总结

### 新手流程
```
INSTALL_ALL.bat → ONECLICK.bat → 选择游戏 → 开始翻译
```

### 老手流程
```
ONECLICK.bat → 开始翻译
```

### 分享流程
```
PACKAGE.bat → 压缩 → 分享 → INSTALL_ALL.bat → ONECLICK.bat
```

**就这么简单！** 🚀
