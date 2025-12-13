@echo off
chcp 65001 >nul
title Ren'Py 汉化工具 - 安全模式（禁用 GPU）

echo.
echo ====================================================
echo    🛡️ 安全模式启动（禁用 GPU 加速）
echo    Safe Mode Launch (GPU Disabled)
echo ====================================================
echo.
echo 此模式用于：
echo - 显卡驱动问题导致工具无法启动
echo - CUDA 环境配置错误
echo - 低配置电脑或虚拟机
echo.
echo 注意：CPU 模式翻译速度会显著降低
echo.

pause

cd /d "%~dp0"

:: 设置环境变量禁用 GPU
set CUDA_VISIBLE_DEVICES=-1
set HIP_VISIBLE_DEVICES=-1

echo [1/3] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装，请先运行 INSTALL_ALL.bat
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i
)

echo [2/3] 检查 Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama 未安装，请先运行 INSTALL_ALL.bat
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('ollama --version') do echo ✅ %%i
)

echo [3/3] 启动工具（CPU 模式）...
echo.

powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "& {$OutputEncoding=[Console]::OutputEncoding=[Console]::InputEncoding=[System.Text.Encoding]::UTF8; . '%~dp0tools\menu.ps1'}"

pause
