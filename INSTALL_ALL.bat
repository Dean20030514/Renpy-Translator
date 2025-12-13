@echo off
chcp 65001 >nul
title Ren'Py 汉化工具 - 自动安装器

echo.
echo ====================================================
echo    Ren'Py 汉化工具 - 自动安装所有环境
echo ====================================================
echo.

cd /d "%~dp0"

:: 使用 PowerShell 脚本进行智能安装
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "tools\smart_installer.ps1"

pause
