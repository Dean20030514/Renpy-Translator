@echo off
chcp 65001 >nul
title 打包工具

echo.
echo ====================================================
echo    Ren'Py 汉化工具 - 打包脚本
echo ====================================================
echo.

cd /d "%~dp0"

set OUTPUT_DIR=Renpy汉化_便携版
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set PACKAGE_NAME=Renpy汉化工具_%TIMESTAMP%.zip

echo [1/4] 清理临时文件...
if exist "%OUTPUT_DIR%" rd /s /q "%OUTPUT_DIR%"
mkdir "%OUTPUT_DIR%"

echo [2/4] 复制核心文件...
xcopy /E /I /Y "tools" "%OUTPUT_DIR%\tools" >nul
xcopy /E /I /Y "data" "%OUTPUT_DIR%\data" >nul
xcopy /E /I /Y "docs" "%OUTPUT_DIR%\docs" >nul

copy /Y "START.bat" "%OUTPUT_DIR%\" >nul
copy /Y "CHECK_ENV.bat" "%OUTPUT_DIR%\" >nul
copy /Y "README.md" "%OUTPUT_DIR%\" >nul
copy /Y "INSTALL.md" "%OUTPUT_DIR%\" >nul
copy /Y "requirements.txt" "%OUTPUT_DIR%\" >nul
copy /Y "pyproject.toml" "%OUTPUT_DIR%\" >nul

echo [3/4] 排除输出目录...
if exist "%OUTPUT_DIR%\outputs" rd /s /q "%OUTPUT_DIR%\outputs"
if exist "%OUTPUT_DIR%\__pycache__" rd /s /q "%OUTPUT_DIR%\__pycache__"

echo [4/4] 创建 README...
(
echo ====================================================
echo    Ren'Py 汉化工具 - 便携版
echo ====================================================
echo.
echo 📦 安装指南：
echo    1. 阅读 INSTALL.md 完成环境配置
echo    2. 运行 CHECK_ENV.bat 检查环境
echo    3. 运行 START.bat 开始使用
echo.
echo 📋 系统要求：
echo    - Python 3.10+
echo    - Ollama
echo    - Windows 10/11
echo.
echo 💡 推荐模型：
echo    - ollama pull qwen2.5:7b ^(8GB VRAM^)
echo    - ollama pull qwen2.5:14b ^(12GB+ VRAM^)
echo.
echo 🐛 常见问题：
echo    请查看 docs/troubleshooting.md
echo.
echo ====================================================
) > "%OUTPUT_DIR%\使用说明.txt"

echo.
echo ====================================================
echo    ✅ 打包完成！
echo ====================================================
echo.
echo 输出目录：%OUTPUT_DIR%
echo.
echo 📦 如需压缩，请手动将 "%OUTPUT_DIR%" 文件夹压缩为 ZIP
echo    （Windows：右键 → 发送到 → 压缩文件夹）
echo.
echo 📤 分享到其他电脑时，请提醒对方：
echo    1. 先阅读 INSTALL.md 安装环境
echo    2. 运行 CHECK_ENV.bat 检查
echo    3. 再运行 START.bat 使用
echo.
pause
