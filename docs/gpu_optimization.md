# GPU 加速优化指南

## 当前状态分析

您的系统：
- **GPU**: NVIDIA RTX 5070 (8GB VRAM)
- **CUDA**: 13.0
- **Ollama**: 已安装并运行

## 重要提示 ⚠️

**不推荐使用 DeepSeek R1 系列做翻译**：
- R1 是推理模型，会生成 `<think>...</think>` 思考过程
- 思考内容会污染翻译输出
- 速度慢，Token 消耗大
- 格式不稳定

**推荐使用 Qwen2.5 系列**：
- 专为文本生成优化
- 输出格式稳定
- 速度快 2-3 倍
- 翻译质量优秀

## 推荐模型 ✅

根据您的 8GB 显存，推荐：

### 最佳选择：qwen2.5:14b
```bash
ollama pull qwen2.5:14b
```
- 大小：约 **9 GB**
- 显存占用：**8 GB** (会用少量系统内存)
- GPU 使用率：**85-95%**
- 翻译质量：**最佳平衡**
- 速度：**快**

### 完全 GPU 加载：qwen2.5:7b
```bash
ollama pull qwen2.5:7b
```
- 大小：约 **4.7 GB**
- 显存占用：**4.7 GB**
- GPU 使用率：**100%**
- 翻译质量：**良好**
- 速度：**最快**

### 预算显存：qwen2.5:3b
```bash
ollama pull qwen2.5:3b
```
- 大小：约 **2 GB**
- 显存占用：**2 GB**
- GPU 使用率：**100%**
- 翻译质量：**可接受**
- 速度：**极快**
- 专为翻译优化

### 方案 3：增加系统 RAM 作为 GPU 扩展

## GPU 加速配置

launcher.ps1 已自动配置最佳 GPU 设置：

```powershell
$env:OLLAMA_NUM_GPU = "999"      # 尽可能多的层放到 GPU
$env:OLLAMA_GPU_OVERHEAD = "0"   # 减少 GPU 开销保留
```

这会让 Ollama 自动优化 GPU 使用率。

## 性能对比 📊

以 RTX 5070 (8GB) 为例：

| 模型 | GPU 使用率 | 速度 (tokens/s) | 显存占用 | 翻译质量 |
|------|-----------|----------------|----------|----------|
| qwen2.5:3b | 100% | ~150 | 2 GB | 良好 |
| qwen2.5:7b | 100% | ~100 | 4.7 GB | 优秀 |
| qwen2.5:14b | 85-95% | ~60 | 8 GB | 最佳 |
| qwen2.5:32b | 40-50% | ~30 | 16 GB | 顶级 |

**推荐**：qwen2.5:14b (速度与质量的最佳平衡)

## 如何验证 GPU 使用 ✅

### 方法 1：实时监控

```powershell
# 在另一个终端窗口运行
nvidia-smi -l 1
```

### 方法 2：查看 Ollama 模型分配

```powershell
ollama ps
```

查看 `PROCESSOR` 列，应该看到 GPU 百分比。

### 方法 3：使用翻译脚本的内置显示

`translate.py` 会自动显示：

```
🎮 GPU: 95% | VRAM: 7200/8151 MB
```

## 常见问题 🔧

### GPU 显存不足

如果看到错误：`CUDA out of memory`

```bash
# 停止当前模型
ollama stop <模型名>

# 使用更小的模型
ollama pull qwen2.5:7b
```

### GPU 未使用

检查环境变量：

```powershell
$env:CUDA_VISIBLE_DEVICES  # 应该为空或 "0"
$env:OLLAMA_NUM_GPU         # 应该 > 0
```

### 翻译很慢

- 检查 `ollama ps` 确认模型已加载到 GPU
- 使用 `nvidia-smi` 查看 GPU 使用率
- 尝试调整 workers 数量（GUI 高级设置）
- 考虑使用更小的模型（qwen2.5:7b）

## 模型下载命令 📥

```bash
# 推荐：平衡版本 (8GB 显存)
ollama pull qwen2.5:14b

# 快速版本 (4GB 显存)
ollama pull qwen2.5:7b

# 轻量版本 (2GB 显存)
ollama pull qwen2.5:3b

# 高质量版本 (16GB+ 显存)
ollama pull qwen2.5:32b
```
