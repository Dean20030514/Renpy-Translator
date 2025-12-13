@echo off
chcp 65001 >nul
title Ren'Py 汉化工具 - 一键启动

echo.
echo ====================================================
echo    Ren'Py 汉化工具 - 环境检查 ^& 启动
echo ====================================================
echo.

cd /d "%~dp0"

:: ========================================
:: 系统架构检查
:: ========================================
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" goto arch_ok
if "%PROCESSOR_ARCHITEW6432%"=="AMD64" goto arch_ok
if exist %windir%\SysWOW64 goto arch_ok

echo ❌ 不支持 32 位系统
echo    32-bit system not supported
pause
exit /b 1

:arch_ok

:: ========================================
:: 权限检查
:: ========================================
echo [0/5] 检查目录权限...
set "TEST_FILE=%~dp0permission_test.tmp"
echo test > "%TEST_FILE%" 2>nul
if exist "%TEST_FILE%" (
    del "%TEST_FILE%" >nul 2>&1
    echo ✅ 目录权限正常
) else (
    echo ❌ 当前目录没有写入权限
    echo    请将工具移至有权限的位置，或使用管理员权限运行
    echo.
    pause
    exit /b 1
)

:: ========================================
:: 环境检查
:: ========================================

echo [1/5] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装
    echo.
    echo 请运行 INSTALL_ALL.bat 自动安装所有环境
    echo 或手动访问：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i
)

echo [2/5] 检查 Python 依赖...
python -c "import rich; import rapidfuzz; print('OK')" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Python 依赖未安装，正在自动安装...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ✅ Python 依赖已安装
)

echo [3/5] 检查 Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama 未安装
    echo.
    echo 请运行 INSTALL_ALL.bat 自动安装所有环境
    echo 或手动访问：https://ollama.ai/
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('ollama --version') do echo ✅ %%i
)

echo [4/5] 检查已安装的模型...
ollama list | findstr /i "qwen" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  未找到 qwen 模型，推荐安装 qwen2.5:7b
    echo.
    choice /C YN /M "是否现在下载 qwen2.5:7b (4.7GB)？"
    if %errorlevel% equ 1 (
        echo 正在下载模型...
        ollama pull qwen2.5:7b
        if %errorlevel% neq 0 (
            echo ❌ 模型下载失败
            pause
            exit /b 1
        )
    ) else (
        echo 跳过模型下载，请稍后手动运行：ollama pull qwen2.5:7b
    )
) else (
    echo ✅ 已安装 qwen 模型
)

echo [5/5] 检查 GPU 并启用 CUDA...
where nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  未检测到 NVIDIA GPU
    echo    工具将使用 CPU 模式（速度较慢）
) else (
    echo ✅ 检测到 NVIDIA GPU
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    
    echo.
    echo 正在启用 CUDA 环境...
    powershell.exe -NoProfile -Command "ecuda" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ CUDA 环境已启用
    ) else (
        echo ⚠️  CUDA 环境启用失败（如果已安装 ecuda 请忽略）
    )
)

echo.
echo ====================================================
echo    ✅ 环境检查完成，正在启动工具...
echo ====================================================
echo.

timeout /t 2 >nul

:: ========================================
:: 启动主程序
:: ========================================

powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "& {$OutputEncoding=[Console]::OutputEncoding=[Console]::InputEncoding=[System.Text.Encoding]::UTF8; . '%~dp0tools\menu.ps1'}"

if %errorlevel% neq 0 (
    echo.
    echo ❌ 工具启动失败
    echo.
    echo 故障排除：
    echo 1. 尝试运行 START_SAFE.bat（禁用 GPU 加速）
    echo 2. 查看 docs/troubleshooting.md 了解常见问题
    echo 3. 检查是否有杀毒软件拦截
    echo.
)

pause
