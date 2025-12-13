# Ren'Py 汉化工具 - 智能安装器
# 自动下载并安装所有依赖

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   Ren'Py 汉化工具 - 智能安装器" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "本脚本将自动检测并安装缺失的环境：" -ForegroundColor Yellow
Write-Host "  1. Python 3.12 (如未安装)"
Write-Host "  2. Ollama (如未安装)"
Write-Host "  3. Python 依赖库"
Write-Host "  4. qwen2.5:7b 翻译模型"
Write-Host ""
Write-Host "需要下载约 5GB，请确保网络连接正常" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "是否继续？(Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    exit
}

$tempDir = "$PSScriptRoot\temp_install"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

# ========================================
# 1. 检查并安装 Python
# ========================================
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "[1/4] 检查 Python..." -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

$pythonInstalled = $false
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python 已安装: $pythonVersion" -ForegroundColor Green
    $pythonInstalled = $true
} catch {
    Write-Host "[!] Python 未安装" -ForegroundColor Yellow
}

if (-not $pythonInstalled) {
    Write-Host "正在下载 Python 3.12..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    $pythonInstaller = "$tempDir\python-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing
        Write-Host "[OK] 下载完成" -ForegroundColor Green
        
        Write-Host "正在安装 Python（静默安装）..." -ForegroundColor Yellow
        Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait
        
        $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
        $env:Path = $machinePath + ";" + $userPath
        
        Start-Sleep -Seconds 3
        
        try {
            $pythonVersion = python --version 2>&1
            Write-Host "[OK] Python 安装成功: $pythonVersion" -ForegroundColor Green
        } catch {
            Write-Host "[X] Python 安装失败，请手动安装" -ForegroundColor Red
            Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
            Read-Host "按回车键退出"
            exit 1
        }
    } catch {
        Write-Host "[X] Python 下载失败: $_" -ForegroundColor Red
        Write-Host "请手动下载: https://www.python.org/downloads/" -ForegroundColor Yellow
        Read-Host "按回车键退出"
        exit 1
    }
}

# ========================================
# 2. 安装 Python 依赖
# ========================================
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "[2/4] 安装 Python 依赖..." -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

$depsInstalled = $false
try {
    $null = python -c "import rich; import rapidfuzz" 2>&1
    Write-Host "[OK] Python 依赖已安装" -ForegroundColor Green
    $depsInstalled = $true
} catch {
    Write-Host "[!] 需要安装依赖库" -ForegroundColor Yellow
}

if (-not $depsInstalled) {
    Write-Host "正在安装依赖库（使用清华镜像）..." -ForegroundColor Yellow
    $requirementsPath = Join-Path $PSScriptRoot "..\requirements.txt"
    try {
        pip install -r $requirementsPath -i https://pypi.tuna.tsinghua.edu.cn/simple
        Write-Host "[OK] 依赖安装完成" -ForegroundColor Green
    } catch {
        Write-Host "[!] 清华镜像失败，尝试官方源..." -ForegroundColor Yellow
        pip install -r $requirementsPath
        Write-Host "[OK] 依赖安装完成" -ForegroundColor Green
    }
}

# ========================================
# 3. 检查并安装 Ollama
# ========================================
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "[3/4] 检查 Ollama..." -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

$ollamaInstalled = $false
try {
    $ollamaVersion = ollama --version 2>&1
    Write-Host "[OK] Ollama 已安装: $ollamaVersion" -ForegroundColor Green
    $ollamaInstalled = $true
} catch {
    Write-Host "[!] Ollama 未安装" -ForegroundColor Yellow
}

if (-not $ollamaInstalled) {
    Write-Host "正在下载 Ollama..." -ForegroundColor Yellow
    $ollamaUrl = "https://ollama.com/download/OllamaSetup.exe"
    $ollamaInstaller = "$tempDir\OllamaSetup.exe"
    
    try {
        Invoke-WebRequest -Uri $ollamaUrl -OutFile $ollamaInstaller -UseBasicParsing
        Write-Host "[OK] 下载完成" -ForegroundColor Green
        
        Write-Host "正在安装 Ollama..." -ForegroundColor Yellow
        Start-Process -FilePath $ollamaInstaller -ArgumentList "/S" -Wait
        
        Write-Host "等待 Ollama 服务启动..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
        $env:Path = $machinePath + ";" + $userPath
        
        try {
            $ollamaVersion = ollama --version 2>&1
            Write-Host "[OK] Ollama 安装成功: $ollamaVersion" -ForegroundColor Green
        } catch {
            Write-Host "[X] Ollama 安装失败，请手动安装" -ForegroundColor Red
            Write-Host "下载地址: https://ollama.ai/" -ForegroundColor Yellow
            Read-Host "按回车键退出"
            exit 1
        }
    } catch {
        Write-Host "[X] Ollama 下载失败: $_" -ForegroundColor Red
        Write-Host "请手动下载: https://ollama.ai/" -ForegroundColor Yellow
        Read-Host "按回车键退出"
        exit 1
    }
}

# ========================================
# 4. 下载翻译模型
# ========================================
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "[4/4] 下载翻译模型..." -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

$modelList = ollama list 2>&1 | Out-String
if ($modelList -match "qwen2\.5:7b") {
    Write-Host "[OK] qwen2.5:7b 模型已安装" -ForegroundColor Green
} else {
    Write-Host "正在下载 qwen2.5:7b 模型 (4.7GB)..." -ForegroundColor Yellow
    Write-Host "这可能需要 10-30 分钟，请耐心等待" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        ollama pull qwen2.5:7b
        Write-Host "[OK] 模型下载成功" -ForegroundColor Green
    } catch {
        Write-Host "[X] 模型下载失败" -ForegroundColor Red
        Write-Host "请稍后手动运行: ollama pull qwen2.5:7b" -ForegroundColor Yellow
    }
}

# ========================================
# 清理临时文件
# ========================================
Write-Host ""
Write-Host "清理临时文件..." -ForegroundColor Yellow
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

# ========================================
# 完成
# ========================================
Write-Host ""
Write-Host "====================================================" -ForegroundColor Green
Write-Host "   安装完成！" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "已安装：" -ForegroundColor Cyan
Write-Host "  [OK] Python" -ForegroundColor Green
Write-Host "  [OK] Python 依赖库" -ForegroundColor Green
Write-Host "  [OK] Ollama" -ForegroundColor Green
Write-Host "  [OK] qwen2.5:7b 翻译模型" -ForegroundColor Green
Write-Host ""
Write-Host "现在可以运行 START.bat 开始使用工具！" -ForegroundColor Yellow
Write-Host ""
Read-Host "按回车键退出"