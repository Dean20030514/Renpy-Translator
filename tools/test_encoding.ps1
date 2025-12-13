# 编码测试脚本
# 用于验证 menu.ps1 的编码配置是否正确

Write-Host ""
Write-Host "=" * 72 -ForegroundColor Cyan
Write-Host "   Ren'Py 汉化工具 - 编码测试" -ForegroundColor Cyan
Write-Host "=" * 72 -ForegroundColor Cyan
Write-Host ""

# 测试 1: 中文字符
Write-Host "【测试 1】中文字符显示测试:" -ForegroundColor Yellow
Write-Host "  简体中文: 你好世界！欢迎使用 Ren'Py 汉化工具" -ForegroundColor White
Write-Host "  繁体中文: 你好世界！歡迎使用 Ren'Py 漢化工具" -ForegroundColor White

# 测试 2: Emoji 图标
Write-Host ""
Write-Host "【测试 2】Emoji 图标显示测试:" -ForegroundColor Yellow
Write-Host "  常用图标: 🚀 ⚡ 🆓 📤 📚 🔄 🤖 🔍 📥" -ForegroundColor White
Write-Host "  状态图标: ✅ ❌ ⚠️ 🛠️ 📊 ⚙️" -ForegroundColor White

# 测试 3: 特殊字符
Write-Host ""
Write-Host "【测试 3】特殊字符显示测试:" -ForegroundColor Yellow
Write-Host "  符号: ═ ━ ─ │ ┃ ┏ ┓ ┗ ┛" -ForegroundColor White
Write-Host "  标点: 、。，；：？！「」『』【】〈〉《》" -ForegroundColor White

# 测试 4: 混合内容
Write-Host ""
Write-Host "【测试 4】混合内容显示测试:" -ForegroundColor Yellow
Write-Host "  ✓ Python 版本: 3.11.0" -ForegroundColor Green
Write-Host "  ✗ Ollama 未安装" -ForegroundColor Red
Write-Host "  • 游戏目录: E:\Games\MyGame" -ForegroundColor White

# 测试 5: 颜色测试
Write-Host ""
Write-Host "【测试 5】颜色显示测试:" -ForegroundColor Yellow
Write-Host "  Black" -ForegroundColor Black -BackgroundColor White
Write-Host "  DarkBlue" -ForegroundColor DarkBlue
Write-Host "  DarkGreen" -ForegroundColor DarkGreen
Write-Host "  DarkCyan" -ForegroundColor DarkCyan
Write-Host "  DarkRed" -ForegroundColor DarkRed
Write-Host "  DarkMagenta" -ForegroundColor DarkMagenta
Write-Host "  DarkYellow" -ForegroundColor DarkYellow
Write-Host "  Gray" -ForegroundColor Gray
Write-Host "  DarkGray" -ForegroundColor DarkGray
Write-Host "  Blue" -ForegroundColor Blue
Write-Host "  Green" -ForegroundColor Green
Write-Host "  Cyan" -ForegroundColor Cyan
Write-Host "  Red" -ForegroundColor Red
Write-Host "  Magenta" -ForegroundColor Magenta
Write-Host "  Yellow" -ForegroundColor Yellow
Write-Host "  White" -ForegroundColor White

# 测试 6: 当前编码设置
Write-Host ""
Write-Host "【测试 6】当前编码设置:" -ForegroundColor Yellow
Write-Host "  控制台输入编码: $([Console]::InputEncoding.EncodingName)" -ForegroundColor White
Write-Host "  控制台输出编码: $([Console]::OutputEncoding.EncodingName)" -ForegroundColor White
Write-Host "  PowerShell 输出编码: $($OutputEncoding.EncodingName)" -ForegroundColor White
Write-Host "  系统代码页: $(chcp | Select-String '\d+')" -ForegroundColor White

# 测试 7: 环境变量
Write-Host ""
Write-Host "【测试 7】Python 环境变量:" -ForegroundColor Yellow
if ($env:PYTHONIOENCODING) {
    Write-Host "  ✓ PYTHONIOENCODING = $env:PYTHONIOENCODING" -ForegroundColor Green
} else {
    Write-Host "  ✗ PYTHONIOENCODING 未设置" -ForegroundColor Red
}

if ($env:PYTHONUTF8) {
    Write-Host "  ✓ PYTHONUTF8 = $env:PYTHONUTF8" -ForegroundColor Green
} else {
    Write-Host "  ✗ PYTHONUTF8 未设置" -ForegroundColor Red
}

# 测试结果
Write-Host ""
Write-Host "=" * 72 -ForegroundColor Cyan
Write-Host "【测试结果】" -ForegroundColor Yellow
Write-Host ""
Write-Host "如果上述所有内容都能正常显示（无乱码、方框）," -ForegroundColor White
Write-Host "则说明编码配置正确，可以正常使用 menu.ps1。" -ForegroundColor Green
Write-Host ""
Write-Host "如果出现乱码或方框:" -ForegroundColor Yellow
Write-Host "  1. 确认使用支持 UTF-8 的终端（推荐 Windows Terminal）" -ForegroundColor White
Write-Host "  2. 确认字体支持中文和 Emoji（推荐: 微软雅黑, Consolas, Cascadia Code）" -ForegroundColor White
Write-Host "  3. 尝试运行: chcp 65001" -ForegroundColor White
Write-Host "  4. 重新启动 PowerShell" -ForegroundColor White
Write-Host ""
Write-Host "=" * 72 -ForegroundColor Cyan
Write-Host ""

Read-Host "按回车键退出"
