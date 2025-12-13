# Ren'Py 游戏汉化工具 - GUI 使用指南

## 快速开始

### 方法 1: 双击启动 (推荐)

1. 双击 `START.bat`
2. 按照提示选择游戏文件夹
3. 配置翻译选项
4. 选择 AI 模型
5. 等待完成

### 方法 2: PowerShell 启动

```powershell
.\tools\launcher.ps1
```

## 功能说明

### 🎯 自动识别游戏

- 启动后会弹出文件夹选择器
- 选择 Ren'Py 游戏的**根目录** (包含 `game` 文件夹的那个)
- 工具会自动验证是否为有效的 Ren'Py 游戏

### 📖 自动生成字典

工具会自动分析游戏文本,生成以下字典:

1. **UI 术语字典** - 识别短小的界面文本
   - 按钮文本 (Save, Load, Quit 等)
   - 菜单项
   - 设置选项

2. **占位符字典** - 自动提取所有变量占位符
   - `[角色名]` 格式
   - `{变量名}` 格式
   - 标记为"保留不翻译"

3. **地点字典** - 识别场景地点名称
   - 从文件名推断 (kitchen.rpy, bedroom.rpy 等)
   - 短文本且包含地点关键词

4. **关系字典** - 识别角色关系称谓
   - Mom, Dad, Sister 等
   - 家庭关系词汇

**生成位置**: `outputs/[游戏名]/dictionaries/`

**编辑方法**:

1. 打开生成的 CSV 文件
2. 在 `zh` 列填入中文翻译
3. 保存文件
4. 重新运行工具时会自动使用

### 🤖 AI 模型选择

工具会**自动检测**您电脑上已安装的 Ollama 模型:

#### 自动识别功能

1. **启动时自动扫描**: 运行 `ollama list` 检测本地模型
2. **显示所有可用模型**: 列出已下载的所有模型
3. **智能推荐**: 自动选中 qwen2.5:14b (如有)
4. **实时刷新**: 点击"刷新"按钮重新检测模型

#### 模型质量对比

| 参数规模 | 内存需求 | 速度 | 质量 | 推荐场景 |
|---------|---------|------|------|---------|
| 32b | 18GB+ | ⭐ | ⭐⭐⭐⭐⭐ | 正式发布版本 |
| 14b | 10GB | ⭐⭐⭐ | ⭐⭐⭐⭐ | 日常使用 (推荐) |
| 7b | 6GB | ⭐⭐⭐⭐ | ⭐⭐⭐ | 快速测试 |
| 3b | 3GB | ⭐⭐⭐⭐⭐ | ⭐⭐ | 草稿翻译 |

#### 安装新模型

如果没有检测到模型,按以下步骤安装:

```powershell
# 安装 Ollama (如未安装)
# 下载: https://ollama.ai/

# 安装推荐模型 (14b)
ollama pull qwen2.5:14b

# 或安装其他模型
ollama pull qwen2.5:7b   # 更快
ollama pull qwen2.5:32b  # 更好

# 安装后点击"刷新"按钮重新检测
```

#### 手动输入模型

如果需要使用特殊模型:

1. 选择列表底部的"手动输入其他模型..."
2. 在文本框中输入模型名称
3. 例如: `deepseek-coder:6.7b`, `mistral:7b`

**前提条件**: 
- ✅ 已安装 Ollama: <https://ollama.ai/>
- ✅ 已下载至少一个模型
- ✅ Ollama 服务正在运行

### ⚙️ 翻译选项

#### 跳过 AI 翻译
- ✅ 只使用字典预填
- ✅ 速度极快 (1-2 分钟)
- ❌ 翻译不完整
- **适用**: 快速预览、只翻译 UI

#### 跳过游戏构建
- ✅ 只生成翻译 JSONL 文件
- ✅ 节省时间
- ❌ 不能直接玩
- **适用**: 多次调整翻译、团队协作

#### 自动生成字典
- ✅ 自动分析并生成专用字典
- ✅ 每个游戏都有定制字典
- ✅ 可手动编辑完善
- **建议**: 首次翻译游戏时启用

#### 工作线程数
- 推荐: 4 (默认)
- 范围: 1-16
- 影响: 提取和回填速度
- 注意: 过高可能导致系统卡顿

## 工作流程

### 完整流程 (首次翻译)

```
选择游戏文件夹
    ↓
配置选项 (启用自动生成字典)
    ↓
选择 AI 模型
    ↓
1. 提取文本 (1-2 分钟)
    ↓
2. 自动生成字典 (10 秒)
    ↓
3. 字典预填 (30 秒)
    ↓
4. AI 翻译 (30-60 分钟)
    ↓
5. 质量检查 (1 分钟)
    ↓
6. 回填游戏 (2-3 分钟)
    ↓
7. 构建中文版 (1 分钟)
    ↓
完成! 查看 QA 报告
```

**总耗时**: 约 40-70 分钟 (主要在 AI 翻译)

### 快速测试流程

```
选择游戏文件夹
    ↓
配置选项
  ✓ 跳过 AI 翻译
  ✓ 自动生成字典
    ↓
1. 提取文本
2. 生成字典
3. 字典预填
4. 质量检查
    ↓
完成! (约 5 分钟)
```

### 编辑字典后重新翻译

```
1. 打开 data/dictionaries/auto/*.csv
2. 编辑 zh 列添加翻译
3. 保存文件
4. 重新运行工具
5. 选择游戏文件夹 (同一个)
6. 配置选项:
   ✗ 跳过 AI 翻译 (或使用 AI)
   ✗ 不需要重新生成字典
7. 开始处理
```

## 输出说明

### 目录结构

```
outputs/
└── [游戏名称]/
    ├── extract/
    │   └── project_en_for_grok.jsonl    # 提取的英文文本
    ├── dictionaries/                    # 游戏专用字典 (自动生成)
    │   ├── [游戏名]_ui_auto.csv
    │   ├── [游戏名]_placeholders_auto.csv
    │   ├── [游戏名]_locations_auto.csv
    │   ├── [游戏名]_relationships_auto.csv
    │   └── [游戏名]_dict_report.txt
    ├── prefilled/
    │   └── prefilled.jsonl              # 字典预填结果
    ├── llm_batches/                     # LLM 翻译批次
    ├── llm_results/                     # LLM 翻译结果
    ├── final/
    │   └── translated.jsonl             # 最终翻译文件
    ├── qa/
    │   ├── qa.html                      # 质量报告 (推荐查看)
    │   ├── qa.json                      # 质量数据
    │   └── qa.tsv                       # 质量表格
    ├── patched/                         # 回填后的 .zh.rpy 文件
    └── cn_build/                        # 中文版游戏 (可直接运行)
```

### 关键文件

#### translated.jsonl
最终翻译文件,格式:
```json
{
  "id": "intro.rpy:15:0",
  "file": "game/intro.rpy",
  "line": 15,
  "en": "Hello, world!",
  "zh": "你好,世界!"
}
```

可以手动编辑这个文件来修正翻译,然后重新运行回填和构建步骤。

#### qa.html
质量检查报告,包含:
- 错误列表 (占位符丢失、标签不匹配等)
- 警告列表 (长度异常、标点问题等)
- 统计信息

**建议**: 每次翻译完成后都查看这个报告!

### 自动生成的字典

```
outputs/[游戏名]/dictionaries/
├── [游戏名]_ui_auto.csv              # UI 术语
├── [游戏名]_placeholders_auto.csv    # 占位符
├── [游戏名]_locations_auto.csv       # 地点
├── [游戏名]_relationships_auto.csv   # 关系
└── [游戏名]_dict_report.txt          # 生成报告
```

**CSV 格式**:
```csv
en,zh,category,notes
"Save",,ui,出现 23 次
"Load",,ui,出现 18 次
[pov],[pov],placeholder,占位符-保留不翻译 (出现 156 次)
```

在 `zh` 列填入翻译:
```csv
en,zh,category,notes
"Save","保存",ui,出现 23 次
"Load","读取",ui,出现 18 次
[pov],[pov],placeholder,占位符-保留不翻译 (出现 156 次)
```

## 常见问题

### Q: 没有安装 Ollama 怎么办?

**A**: 有两种方案:

**方案 1: 只使用字典翻译**

- 选择"跳过 AI 翻译"选项
- 只使用字典预填
- 速度极快但翻译不完整

**方案 2: 安装 Ollama**

1. 下载 Ollama: <https://ollama.ai/>
2. 安装并启动
3. 打开终端,安装模型:

```powershell
# 推荐: 速度与质量平衡
ollama pull qwen2.5:14b

# 或选择其他版本
ollama pull qwen2.5:7b   # 更快,需要 6GB 内存
ollama pull qwen2.5:32b  # 最好,需要 18GB 内存
```

4. 重新运行汉化工具
5. 点击"刷新"按钮检测新安装的模型

### Q: 字典翻译不准确怎么办?

**A**:

1. 打开 `outputs/[游戏名]/dictionaries/` 中的 CSV 文件
2. 修改 `zh` 列的翻译
3. 保存文件
4. 重新运行工具

字典会按以下优先级加载:

- **游戏专用字典** (`outputs/[游戏名]/dictionaries/`) - 优先级最高
- **通用字典** (`data/dictionaries/`) - 回退选项

建议每个游戏都生成专用字典,这样不同游戏的翻译不会互相干扰。### Q: 可以中途停止吗?

**A**: 
- 可以按 Ctrl+C 停止
- 已完成的步骤会保存在 `outputs/[游戏名]/` 中
- 下次运行时选择"跳过提取"可以继续

### Q: 翻译质量不好怎么办?

**A**: 
1. 查看 `qa.html` 报告
2. 编辑 `final/translated.jsonl` 修正翻译
3. 重新运行,选择:
   - ✓ 跳过提取
   - ✓ 跳过 AI 翻译
   - ✗ 不跳过构建

### Q: 字体不支持中文?

**A**: 
游戏的字体文件通常在 `game/` 目录下 (.ttf 或 .otf)

解决方法:
1. 下载支持中文的字体 (如思源黑体)
2. 替换游戏目录中的字体文件
3. 重新运行游戏

### Q: MOD 和旧版本文件也会翻译吗?

**A**: 
是的! 新版工具会翻译所有文件,包括:
- MOD 目录 (SAZMOD 等)
- 旧版本更新文件 (update71, v06.rpy 等)
- 所有 .rpy 文件

### Q: 如何查看我安装了哪些模型?

**A**: 

**在终端中查看:**

```powershell
ollama list
```

**在汉化工具中查看:**

1. 运行汉化工具
2. 在模型选择界面会自动显示所有已安装的模型
3. 点击"刷新"按钮重新检测

### Q: 模型列表是空的怎么办?

**A**: 可能的原因和解决方法:

1. **Ollama 未安装**
   - 下载安装: <https://ollama.ai/>

2. **Ollama 未运行**
   - Windows: 检查系统托盘是否有 Ollama 图标
   - 或打开终端运行: `ollama serve`

3. **未安装任何模型**
   - 运行: `ollama pull qwen2.5:14b`

4. **PATH 环境变量问题**
   - 重启电脑
   - 或重新安装 Ollama

**A**: 
目前需要手动操作:
1. 提取后编辑 `extract/project_en_for_grok.jsonl`
2. 删除不需要的条目
3. 继续后续步骤

或者使用命令行版本:
```powershell
python tools/extract.py 游戏路径 --glob "intro.rpy"
```

### Q: 可以团队协作翻译吗?

**A**: 
可以! 方法:
1. A 运行工具提取文本
2. 分享 `extract/project_en_for_grok.jsonl`
3. 每人翻译不同的条目
4. 合并 JSONL 文件
5. 运行回填和构建步骤

### Q: 换一个游戏需要重新生成字典吗?

**A**:

是的! 每个游戏都应该生成专用字典:

- ✅ 启用"自动生成字典"选项
- ✅ 工具会分析该游戏的文本特征
- ✅ 生成针对性的字典到 `outputs/[游戏名]/dictionaries/`
- ✅ 不同游戏的字典互不干扰

**字典隔离的好处**:

- 不同游戏的占位符名称不同 (`[mom]` vs `[mother]`)
- UI 文本可能不同 (有的游戏是 "Save Game",有的是 "Save")
- 地点名称各不相同
- 避免工具本身目录变得臃肿

**复用通用字典**:

如果您有一些通用的翻译 (如标准 UI 术语),可以放在:
- `data/dictionaries/` - 所有游戏共享
- 游戏专用字典会覆盖通用字典中的相同条目## 高级用法

### 手动调整字典优先级

字典加载规则:

1. **游戏专用字典** (优先)
   - 位置: `outputs/[游戏名]/dictionaries/`
   - 自动生成或手动创建
   - 针对特定游戏

2. **通用字典** (回退)
   - 位置: `data/dictionaries/`
   - 跨游戏共享
   - 标准 UI 术语等

**覆盖规则**:
- 如果游戏专用字典存在,优先使用
- 如果不存在,回退到通用字典
- 相同条目时,游戏专用字典优先

**推荐实践**:

```
data/dictionaries/          # 通用字典 (可选)
├── common_ui.csv          # 通用 UI 术语
└── common_names.csv       # 通用人名翻译

outputs/
├── GameA/
│   └── dictionaries/      # GameA 专用字典
│       ├── GameA_ui_auto.csv
│       └── GameA_placeholders_auto.csv
└── GameB/
    └── dictionaries/      # GameB 专用字典
        ├── GameB_ui_auto.csv
        └── GameB_placeholders_auto.csv
```

### 批量处理多个游戏

创建批处理脚本:
```powershell
$games = @(
    "C:\Games\Game1",
    "C:\Games\Game2",
    "C:\Games\Game3"
)

foreach ($game in $games) {
    Write-Host "处理: $game"
    # 使用命令行版本...
}
```

### 自定义翻译提示词

编辑 `tools/translate.py`:
- 找到 `system_prompt` 变量
- 修改翻译指令
- 保存后重新运行

## 性能优化

### 提速技巧

1. **使用更快的模型**: qwen2.5:7b 比 32b 快 4 倍
2. **增加工作线程**: 提取和回填时可用 8 线程
3. **跳过不必要的步骤**: 
   - 已有字典时不重新生成
   - 只调整翻译时跳过提取
4. **使用 SSD**: 大量文件 I/O 操作

### 资源需求

| 模型 | 内存 | 速度 | 质量 |
|------|------|------|------|
| 32b | 18GB+ | 慢 | 最好 |
| 14b | 10GB | 中等 | 很好 |
| 7b | 6GB | 快 | 良好 |
| 3b | 3GB | 很快 | 一般 |

## 技术支持

- 主文档: [README.md](../README.md)
- 故障排查: [docs/troubleshooting.md](../docs/troubleshooting.md)
- TheTyrant 专题: [docs/tyrant_quickstart.md](../docs/tyrant_quickstart.md)

---

**享受汉化过程!** 🎮✨
