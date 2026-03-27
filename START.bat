@echo off
setlocal

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.9+ is required.
    pause
    exit /b 1
)

python "%~dp0start_launcher.py"
set CODE=%ERRORLEVEL%

echo.
echo Exit code: %CODE%
pause
exit /b %CODE%
