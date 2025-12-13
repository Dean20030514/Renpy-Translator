# 字体替换功能使用说明

## 功能介绍

自动替换 Ren'Py 游戏中的原始字体为 Noto Sans SC 中文字体。

## 准备工作

### 1. 下载中文字体

访问 [Google Fonts - Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC)

点击 "Download family" 下载字体包。

### 2. 放置字体文件

将下载的字体文件重命名并放到 `data/fonts/` 目录：

```
data/fonts/
├── NotoSansSC.ttf         (原文件: NotoSansSC-Regular.ttf)
└── NotoSansSCBold.ttf     (原文件: NotoSansSC-Bold.ttf)
```

## 使用方法

### 自动模式（集成在 START.bat 中）

运行 START.bat 后，在构建步骤会自动替换字体。

### 手动模式

```bash
# 基本用法
python tools/replace_fonts.py <游戏根目录>

# 带备份（推荐）
python tools/replace_fonts.py <游戏根目录> --backup

# 试运行（查看将要执行的操作）
python tools/replace_fonts.py <游戏根目录> --dry-run

# 指定字体源目录
python tools/replace_fonts.py <游戏根目录> --font-dir "path/to/fonts"
```

## 工作原理

该工具会执行以下操作：

1. **删除旧字体**: 删除游戏中所有 `.ttf` 和 `.otf` 字体文件
2. **复制新字体**: 将 NotoSansSC 字体复制到 `game/fonts/` 目录
3. **更新引用**: 自动修改所有 `.rpy` 文件中的字体引用

### 示例：修改前后对比

**修改前** (gui.rpy):
```renpy
define gui.text_font = "DejaVuSans.ttf"
define gui.name_text_font = "Arial-Bold.ttf"
```

**修改后** (gui.rpy):
```renpy
define gui.text_font = "fonts/NotoSansSC.ttf"
define gui.name_text_font = "fonts/NotoSansSCBold.ttf"
```

## 注意事项

- ✅ 建议先用 `--dry-run` 查看将要执行的操作
- ✅ 使用 `--backup` 参数会将原字体备份到 `outputs/font_backup/`
- ✅ 字体替换后建议先测试游戏是否正常运行
- ⚠️ 如果游戏使用了特殊字体效果，可能需要手动调整

## 常见问题

### Q: 字体替换后游戏无法启动？
A: 检查字体文件是否正确放置在 `game/fonts/` 目录，文件名是否正确。

### Q: 部分文字显示为方框？
A: Noto Sans SC 支持所有常用中文字符，如果出现方框可能是游戏代码问题。

### Q: 能否保留原字体的特殊效果？
A: 字体替换只改变字体文件，样式（大小、颜色等）会保留。

## 示例输出

```
============================================================
Ren'Py 游戏字体替换工具
============================================================
游戏目录: E:\Games\MyRenpyGame
字体源: E:\Renpy汉化\data\fonts

▶ 步骤 1: 删除旧字体文件
  发现 3 个字体文件:
    - game/fonts/DejaVuSans.ttf
    - game/fonts/Arial.ttf
    - game/fonts/Arial-Bold.ttf
  备份: DejaVuSans.ttf -> E:\Games\outputs\font_backup\DejaVuSans.ttf
  删除: game/fonts/DejaVuSans.ttf
  备份: Arial.ttf -> E:\Games\outputs\font_backup\Arial.ttf
  删除: game/fonts/Arial.ttf
  备份: Arial-Bold.ttf -> E:\Games\outputs\font_backup\Arial-Bold.ttf
  删除: game/fonts/Arial-Bold.ttf
  ✓ 已删除 3 个字体文件

▶ 步骤 2: 复制中文字体
  复制: NotoSansSC.ttf -> game/fonts/NotoSansSC.ttf
  复制: NotoSansSCBold.ttf -> game/fonts/NotoSansSCBold.ttf
  ✓ 已复制 2 个字体文件

▶ 步骤 3: 更新 .rpy 文件中的字体引用
  更新: game/gui.rpy
  更新: game/screens.rpy
  ✓ 已更新 2 个文件

============================================================
✓ 字体替换完成！
============================================================
```
