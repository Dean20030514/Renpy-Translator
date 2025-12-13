# 中文字体文件

## 所需字体

请将以下字体文件放置到此目录：

1. **NotoSansSC.ttf** - Noto Sans SC 常规字体
2. **NotoSansSCBold.ttf** - Noto Sans SC 粗体

## 下载地址

### 官方源（推荐）
- Google Fonts: https://fonts.google.com/noto/specimen/Noto+Sans+SC
- 点击 "Download family" 下载完整字体包
- 解压后找到对应的字体文件重命名即可

### 字体对应关系
```
NotoSansSC-Regular.ttf  →  NotoSansSC.ttf
NotoSansSC-Bold.ttf     →  NotoSansSCBold.ttf
```

## 使用方法

放置好字体后，运行字体替换工具：

```bash
# 基本用法
python tools/replace_fonts.py <游戏根目录>

# 备份旧字体
python tools/replace_fonts.py <游戏根目录> --backup

# 试运行（查看将要执行的操作）
python tools/replace_fonts.py <游戏根目录> --dry-run
```

## 功能说明

字体替换工具会自动：
1. 删除游戏中的所有原字体文件（.ttf, .otf）
2. 复制 NotoSansSC 字体到游戏的 `game/fonts/` 目录
3. 更新所有 .rpy 文件中的字体引用

## 注意事项

- 建议先用 `--dry-run` 查看将要执行的操作
- 使用 `--backup` 参数会将原字体备份到 `outputs/font_backup/`
- 字体替换后建议测试游戏是否正常运行
