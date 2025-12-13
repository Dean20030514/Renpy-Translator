#!/usr/bin/env pwsh
# ============================================================================
# Ren'Py 游戏汉化工具集 v2.1 - 主菜单 (优化版)
# ============================================================================
# 
# 主要改进:
# 1. ✅ 完全修复 UTF-8 编码问题
# 2. ✅ 统一错误处理机制
# 3. ✅ 优化用户交互流程
# 4. ✅ 添加详细的进度提示
# 5. ✅ 支持图形界面选择文件/文件夹
#
# ============================================================================

#Requires -Version 5.1

# ==================== 编码配置（关键修复）====================
# 强制设置 PowerShell 所有输出为 UTF-8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 设置 Python 环境变量以确保 UTF-8 输出
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# 错误处理
$ErrorActionPreference = "Continue"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# ==================== 工具函数 ====================

function Show-Header {
    Clear-Host
    Write-Host ""
    Write-Host ("=" * 72) -ForegroundColor Cyan
    Write-Host "          Ren'Py 游戏汉化工具集 v2.1                           " -ForegroundColor Cyan
    Write-Host "          Ren'Py Game Translation Toolkit                      " -ForegroundColor Cyan
    Write-Host ("=" * 72) -ForegroundColor Cyan
    Write-Host ""
}

function Show-MainMenu {
    Write-Host "【主菜单】请选择功能：" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  一键流程：" -ForegroundColor Green
    Write-Host "    1. 🚀 一键自动汉化（Ollama 本地）" -ForegroundColor White
    Write-Host "    2. ⚡ 一键快速翻译（云端 API）" -ForegroundColor White
    Write-Host "    3. 🆓 一键免费机翻（Google/Bing）" -ForegroundColor White
    Write-Host ""
    Write-Host "  分步操作：" -ForegroundColor Green
    Write-Host "    4. 📤 提取文本" -ForegroundColor White
    Write-Host "    5. 📚 生成字典" -ForegroundColor White
    Write-Host "    6. 🔄 字典预填" -ForegroundColor White
    Write-Host "    7. 🤖 翻译文本" -ForegroundColor White
    Write-Host "    8. 🔍 质量检查" -ForegroundColor White
    Write-Host "    9. 📥 回填翻译" -ForegroundColor White
    Write-Host ""
    Write-Host "  高级功能：" -ForegroundColor Green
    Write-Host "   10. 🛠️  质量修复工具" -ForegroundColor White
    Write-Host "   11. 📊 翻译统计" -ForegroundColor White
    Write-Host "   12. ⚙️  环境配置" -ForegroundColor White
    Write-Host ""
    Write-Host "    0. ❌ 退出" -ForegroundColor Red
    Write-Host ""
    Write-Host ("━" * 72) -ForegroundColor DarkGray
}

function Write-Step {
    param(
        [string]$Message,
        [string]$Color = "Cyan"
    )
    Write-Host ""
    Write-Host $Message -ForegroundColor $Color
    Write-Host ("-" * 60) -ForegroundColor DarkGray
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "  • $Message" -ForegroundColor White
}

function Invoke-SafePythonCommand {
    param(
        [string]$Script,
        [string[]]$Arguments,
        [string]$Description
    )
    
    if ($Description) {
        Write-Step $Description
    }
    
    # 确保使用 UTF-8 编码调用 Python
    $prevEncoding = $OutputEncoding
    try {
        $OutputEncoding = [System.Text.Encoding]::UTF8
        
        # 构建完整命令
        $fullArgs = @($Script) + $Arguments
        $command = "python $($fullArgs -join ' ')"
        
        Write-Host "执行: $command" -ForegroundColor DarkGray
        Write-Host ""
        
        # 执行命令
        & python @fullArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMsg "执行失败 (退出码: $LASTEXITCODE)"
            return $false
        }
        
        Write-Host ""
        Write-Success "执行成功"
        return $true
    }
    finally {
        $OutputEncoding = $prevEncoding
    }
}

function Select-Folder {
    param([string]$Description = "选择文件夹")
    
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
        $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
        $folderBrowser.Description = $Description
        $folderBrowser.RootFolder = [System.Environment+SpecialFolder]::MyComputer
        
        if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            return $folderBrowser.SelectedPath
        }
    }
    catch {
        Write-Warning "无法使用图形界面，请手动输入路径"
        $path = Read-Host "请输入路径"
        if ($path -and (Test-Path $path)) {
            return $path
        }
    }
    return $null
}

function Select-File {
    param(
        [string]$Title = "选择文件",
        [string]$Filter = "All files (*.*)|*.*"
    )
    
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
        $fileBrowser = New-Object System.Windows.Forms.OpenFileDialog
        $fileBrowser.Title = $Title
        $fileBrowser.Filter = $Filter
        
        if ($fileBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            return $fileBrowser.FileName
        }
    }
    catch {
        Write-Warning "无法使用图形界面，请手动输入路径"
        $path = Read-Host "请输入文件路径"
        if ($path -and (Test-Path $path)) {
            return $path
        }
    }
    return $null
}

function Get-OllamaModels {
    try {
        $output = ollama list 2>&1 | Out-String
        $models = @()
        
        # 解析 Ollama 输出
        foreach ($line in $output -split "`n") {
            # 跳过标题行和空行
            if ($line -match '^(\S+)' -and $line -notmatch '^NAME' -and $line.Trim()) {
                $modelName = $matches[1].Trim()
                if ($modelName) {
                    $models += $modelName
                }
            }
        }
        
        return $models
    }
    catch {
        return @()
    }
}

function Show-APIProviderMenu {
    Write-Host ""
    Write-Host "【选择 API 提供商】" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. DeepSeek (推荐，￥1/百万Token)" -ForegroundColor Green
    Write-Host "  2. Grok (xAI，￥35/百万Token)" -ForegroundColor Cyan
    Write-Host "  3. OpenAI GPT-3.5 (￥7/百万Token)" -ForegroundColor White
    Write-Host "  4. OpenAI GPT-4 (￥70/百万Token)" -ForegroundColor Yellow
    Write-Host "  5. Claude Haiku (￥3.5/百万Token)" -ForegroundColor Magenta
    Write-Host "  6. Claude Sonnet (￥21/百万Token)" -ForegroundColor Magenta
    Write-Host ""
    
    $choice = Read-Host "请选择 (1-6)"
    
    switch ($choice) {
        "1" { return "deepseek" }
        "2" { return "grok" }
        "3" { return "openai-gpt35" }
        "4" { return "openai-gpt4" }
        "5" { return "claude-haiku" }
        "6" { return "claude-sonnet" }
        default { return "deepseek" }
    }
}

function Show-FreeMTMenu {
    Write-Host ""
    Write-Host "【选择免费机翻引擎】" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Google Translate (推荐)" -ForegroundColor Green
    Write-Host "  2. Bing Translator" -ForegroundColor Cyan
    Write-Host "  3. DeepL Free (需注册)" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "请选择 (1-3)"
    
    switch ($choice) {
        "1" { return "google" }
        "2" { return "bing" }
        "3" { return "deepl" }
        default { return "google" }
    }
}

function Show-ConfirmDialog {
    param(
        [string]$GamePath,
        [string]$Model,
        [string]$OutputDir
    )
    
    Write-Host ""
    Write-Host ("━" * 60) -ForegroundColor DarkGray
    Write-Host "准备执行汉化流程：" -ForegroundColor Yellow
    Write-Info "游戏目录: $GamePath"
    Write-Info "翻译模型: $Model"
    Write-Info "输出目录: $OutputDir"
    Write-Host ("━" * 60) -ForegroundColor DarkGray
    
    $confirm = Read-Host "`n是否开始？(Y/N)"
    return ($confirm -eq "Y" -or $confirm -eq "y")
}

# ==================== 功能函数 ====================

function Invoke-OneClickOllama {
    Show-Header
    Write-Host "【一键自动汉化 - Ollama 本地】" -ForegroundColor Green
    Write-Host ""
    
    # 步骤 1: 选择游戏目录
    Write-Step "步骤 1/3: 选择游戏目录"
    $gamePath = Select-Folder -Description "选择 Ren'Py 游戏根目录"
    
    if (-not $gamePath) {
        Write-Host "请手动输入游戏路径：" -ForegroundColor Yellow
        $gamePath = Read-Host "游戏根目录"
    }
    
    if (-not (Test-Path $gamePath)) {
        Write-ErrorMsg "目录不存在: $gamePath"
        Read-Host "按回车继续"
        return
    }
    Write-Success "已选择: $gamePath"
    
    # 步骤 2: 检测 Ollama 模型
    Write-Step "步骤 2/3: 检测 Ollama 模型"
    
    # 先检查 Ollama 是否运行
    try {
        $null = ollama list 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Ollama 未运行"
        }
    }
    catch {
        Write-ErrorMsg "未检测到 Ollama 或 Ollama 未运行"
        Write-Host ""
        Write-Host "请先执行以下操作：" -ForegroundColor Yellow
        Write-Host "  1. 下载安装 Ollama: https://ollama.ai" -ForegroundColor White
        Write-Host "  2. 启动 Ollama 服务" -ForegroundColor White
        Write-Host "  3. 下载模型: ollama pull qwen2.5:7b" -ForegroundColor White
        Read-Host "`n按回车继续"
        return
    }
    
    $models = Get-OllamaModels
    
    if ($models.Count -eq 0) {
        Write-ErrorMsg "未检测到已安装的模型"
        Write-Host ""
        Write-Host "请先下载模型，推荐命令：" -ForegroundColor Yellow
        Write-Host "  ollama pull qwen2.5:7b" -ForegroundColor White
        Write-Host "  ollama pull qwen2.5:14b" -ForegroundColor White
        Read-Host "`n按回车继续"
        return
    }
    
    Write-Success "检测到 $($models.Count) 个模型"
    for ($i = 0; $i -lt $models.Count; $i++) {
        Write-Host "    $($i+1). $($models[$i])" -ForegroundColor Gray
    }
    
    Write-Host ""
    $modelChoice = Read-Host "请选择模型编号 (1-$($models.Count))"
    
    try {
        $selectedModel = $models[[int]$modelChoice - 1]
        Write-Success "已选择: $selectedModel"
    }
    catch {
        Write-ErrorMsg "无效的选择"
        Read-Host "按回车继续"
        return
    }
    
    # 步骤 3: 确认并执行
    Write-Step "步骤 3/3: 执行翻译流程"
    
    $outputDir = Join-Path $WorkspaceRoot "outputs\$(Split-Path $gamePath -Leaf)_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    if (-not (Show-ConfirmDialog -GamePath $gamePath -Model $selectedModel -OutputDir $outputDir)) {
        Write-Host "已取消" -ForegroundColor Yellow
        Read-Host "按回车继续"
        return
    }
    
    # 执行完整流程
    Write-Host ""
    $pipelineScript = Join-Path $WorkspaceRoot "tools\pipeline.py"
    
    $success = Invoke-SafePythonCommand `
        -Script $pipelineScript `
        -Arguments @($gamePath, "--model", $selectedModel, "--host", "http://127.0.0.1:11434") `
        -Description "正在执行 Ollama 翻译流程..."
    
    Write-Host ""
    if ($success) {
        Write-Host "✅ 汉化完成！" -ForegroundColor Green
        Write-Host "输出目录: $outputDir" -ForegroundColor Yellow
    }
    else {
        Write-Host "❌ 流程执行失败" -ForegroundColor Red
    }
    
    Read-Host "`n按回车继续"
}

function Invoke-OneClickAPI {
    Show-Header
    Write-Host "【一键快速翻译 - 云端 API】" -ForegroundColor Green
    Write-Host ""
    
    # 步骤 1: 选择游戏目录
    Write-Step "步骤 1/4: 选择游戏目录"
    $gamePath = Select-Folder -Description "选择 Ren'Py 游戏根目录"
    
    if (-not $gamePath) {
        $gamePath = Read-Host "请输入游戏根目录路径"
    }
    
    if (-not (Test-Path $gamePath)) {
        Write-ErrorMsg "目录不存在"
        Read-Host "按回车继续"
        return
    }
    Write-Success "已选择: $gamePath"
    
    # 步骤 2: 选择 API 提供商
    Write-Step "步骤 2/4: 选择 API 提供商"
    $provider = Show-APIProviderMenu
    Write-Success "已选择: $provider"
    
    # 步骤 3: 输入 API Key
    Write-Step "步骤 3/4: 配置 API Key"
    $apiKey = Read-Host -AsSecureString "请输入 API Key"
    $apiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
    )
    
    if ([string]::IsNullOrWhiteSpace($apiKeyPlain)) {
        Write-ErrorMsg "API Key 不能为空"
        Read-Host "按回车继续"
        return
    }
    Write-Success "API Key 已设置"
    
    # 步骤 4: 执行流程
    Write-Step "步骤 4/4: 执行翻译流程"
    
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $outputBase = Join-Path $WorkspaceRoot "outputs\api_$timestamp"
    
    if (-not (Show-ConfirmDialog -GamePath $gamePath -Model $provider -OutputDir $outputBase)) {
        Write-Host "已取消" -ForegroundColor Yellow
        Read-Host "按回车继续"
        return
    }
    
    Write-Host ""
    
    # 子步骤 1: 提取
    $extractOut = Join-Path $outputBase "extract"
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\extract.py") `
        -Arguments @($gamePath, "--glob", "**/*.rpy", "-o", $extractOut) `
        -Description "[1/5] 提取文本..."
    
    if (-not $success) {
        Read-Host "按回车继续"
        return
    }
    
    # 子步骤 2: 分批
    $batchesOut = Join-Path $outputBase "batches"
    $sourceJsonl = Join-Path $extractOut "project_en_for_grok.jsonl"
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\split.py") `
        -Arguments @($sourceJsonl, $batchesOut, "--skip-has-zh", "--max-tokens", "100000") `
        -Description "[2/5] 分批处理..."
    
    if (-not $success) {
        Read-Host "按回车继续"
        return
    }
    
    # 子步骤 3: 翻译
    $resultsOut = Join-Path $outputBase "results"
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\translate_api.py") `
        -Arguments @($batchesOut, "-o", $resultsOut, "--provider", $provider, "--api-key", $apiKeyPlain, "--workers", "10") `
        -Description "[3/5] API 翻译..."
    
    if (-not $success) {
        Read-Host "按回车继续"
        return
    }
    
    # 子步骤 4: 合并
    $mergedOut = Join-Path $outputBase "merged.jsonl"
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\merge.py") `
        -Arguments @($sourceJsonl, $resultsOut, "-o", $mergedOut) `
        -Description "[4/5] 合并结果..."
    
    if (-not $success) {
        Read-Host "按回车继续"
        return
    }
    
    # 子步骤 5: 回填
    $patchOut = Join-Path $outputBase "patched"
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\patch.py") `
        -Arguments @($gamePath, $mergedOut, "-o", $patchOut, "--advanced") `
        -Description "[5/5] 回填翻译..."
    
    Write-Host ""
    if ($success) {
        Write-Host "✅ API 翻译完成！" -ForegroundColor Green
        Write-Host "汉化文件: $patchOut" -ForegroundColor Yellow
    }
    else {
        Write-Host "❌ 流程执行失败" -ForegroundColor Red
    }
    
    Read-Host "`n按回车继续"
}

function Invoke-OneClickFreeMT {
    Show-Header
    Write-Host "【一键免费机翻】" -ForegroundColor Green
    Write-Host ""
    
    # 步骤 1: 选择游戏目录
    Write-Step "步骤 1/3: 选择游戏目录"
    $gamePath = Select-Folder -Description "选择 Ren'Py 游戏根目录"
    
    if (-not $gamePath) {
        $gamePath = Read-Host "请输入游戏根目录路径"
    }
    
    if (-not (Test-Path $gamePath)) {
        Write-ErrorMsg "目录不存在"
        Read-Host "按回车继续"
        return
    }
    Write-Success "已选择: $gamePath"
    
    # 步骤 2: 选择引擎
    Write-Step "步骤 2/3: 选择翻译引擎"
    $provider = Show-FreeMTMenu
    Write-Success "已选择: $provider"
    
    # DeepL 需要 API Key
    $apiKey = ""
    if ($provider -eq "deepl") {
        Write-Host ""
        $apiKey = Read-Host "请输入 DeepL API Key"
        if ([string]::IsNullOrWhiteSpace($apiKey)) {
            Write-ErrorMsg "API Key 不能为空"
            Read-Host "按回车继续"
            return
        }
        Write-Success "API Key 已设置"
    }
    
    # 步骤 3: 执行流程
    Write-Step "步骤 3/3: 执行翻译流程"
    
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $outputBase = Join-Path $WorkspaceRoot "outputs\free_$timestamp"
    
    if (-not (Show-ConfirmDialog -GamePath $gamePath -Model $provider -OutputDir $outputBase)) {
        Write-Host "已取消" -ForegroundColor Yellow
        Read-Host "按回车继续"
        return
    }
    
    Write-Host ""
    
    # 提取
    $extractOut = Join-Path $outputBase "extract"
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\extract.py") `
        -Arguments @($gamePath, "--glob", "**/*.rpy", "-o", $extractOut) `
        -Description "[1/5] 提取文本..."
    
    if (-not $success) {
        Read-Host "按回车继续"
        return
    }
    
    # 分批
    $batchesOut = Join-Path $outputBase "batches"
    $sourceJsonl = Join-Path $extractOut "project_en_for_grok.jsonl"
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\split.py") `
        -Arguments @($sourceJsonl, $batchesOut, "--skip-has-zh", "--max-tokens", "50000") `
        -Description "[2/5] 分批处理..."
    
    if (-not $success) {
        Read-Host "按回车继续"
        return
    }
    
    # 翻译
    $resultsOut = Join-Path $outputBase "results"
    $translateArgs = @($batchesOut, "-o", $resultsOut, "--provider", $provider, "--workers", "5")
    if ($apiKey) {
        $translateArgs += @("--api-key", $apiKey)
    }
    
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\translate_free.py") `
        -Arguments $translateArgs `
        -Description "[3/5] 免费机翻..."
    
    if (-not $success) {
        Read-Host "按回车继续"
        return
    }
    
    # 合并
    $mergedOut = Join-Path $outputBase "merged.jsonl"
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\merge.py") `
        -Arguments @($sourceJsonl, $resultsOut, "-o", $mergedOut) `
        -Description "[4/5] 合并结果..."
    
    if (-not $success) {
        Read-Host "按回车继续"
        return
    }
    
    # 回填
    $patchOut = Join-Path $outputBase "patched"
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\patch.py") `
        -Arguments @($gamePath, $mergedOut, "-o", $patchOut, "--advanced") `
        -Description "[5/5] 回填翻译..."
    
    Write-Host ""
    if ($success) {
        Write-Host "✅ 免费机翻完成！" -ForegroundColor Green
        Write-Host "汉化文件: $patchOut" -ForegroundColor Yellow
    }
    else {
        Write-Host "❌ 流程执行失败" -ForegroundColor Red
    }
    
    Read-Host "`n按回车继续"
}

function Invoke-ExtractText {
    Show-Header
    Write-Host "【提取文本】" -ForegroundColor Green
    Write-Host ""
    
    $gamePath = Select-Folder -Description "选择游戏根目录"
    if (-not $gamePath) {
        $gamePath = Read-Host "请输入游戏根目录路径"
    }
    
    if (-not (Test-Path $gamePath)) {
        Write-ErrorMsg "目录不存在"
        Read-Host "按回车继续"
        return
    }
    
    $outputDir = Join-Path $WorkspaceRoot "outputs\extract_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\extract.py") `
        -Arguments @($gamePath, "--glob", "**/*.rpy", "-o", $outputDir) `
        -Description "正在提取文本..."
    
    Write-Host ""
    if ($success) {
        Write-Success "提取完成: $outputDir"
    }
    
    Read-Host "按回车继续"
}

function Invoke-GenerateDict {
    Show-Header
    Write-Host "【生成字典】" -ForegroundColor Green
    Write-Host ""
    
    $jsonlFile = Select-File -Title "选择源 JSONL 文件" -Filter "JSONL files (*.jsonl)|*.jsonl|All files (*.*)|*.*"
    if (-not $jsonlFile) {
        $jsonlFile = Read-Host "请输入源 JSONL 路径"
    }
    
    if (-not (Test-Path $jsonlFile)) {
        Write-ErrorMsg "文件不存在"
        Read-Host "按回车继续"
        return
    }
    
    $outputDir = Join-Path $WorkspaceRoot "outputs\dictionaries_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\generate_dict.py") `
        -Arguments @($jsonlFile, "-o", $outputDir) `
        -Description "正在生成字典..."
    
    Write-Host ""
    if ($success) {
        Write-Success "字典生成完成: $outputDir"
    }
    
    Read-Host "按回车继续"
}

function Invoke-PrefillDict {
    Show-Header
    Write-Host "【字典预填】" -ForegroundColor Green
    Write-Host ""
    
    $sourceJsonl = Select-File -Title "选择源 JSONL 文件" -Filter "JSONL files (*.jsonl)|*.jsonl"
    if (-not $sourceJsonl) {
        $sourceJsonl = Read-Host "请输入源 JSONL 路径"
    }
    
    if (-not (Test-Path $sourceJsonl)) {
        Write-ErrorMsg "源文件不存在"
        Read-Host "按回车继续"
        return
    }
    
    $dictFile = Select-File -Title "选择字典文件" -Filter "CSV files (*.csv)|*.csv|JSONL files (*.jsonl)|*.jsonl"
    if (-not $dictFile) {
        $dictFile = Read-Host "请输入字典文件路径"
    }
    
    if (-not (Test-Path $dictFile)) {
        Write-ErrorMsg "字典文件不存在"
        Read-Host "按回车继续"
        return
    }
    
    $outputFile = Join-Path $WorkspaceRoot "outputs\prefilled_$(Get-Date -Format 'yyyyMMdd_HHmmss').jsonl"
    
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\prefill.py") `
        -Arguments @($sourceJsonl, $dictFile, "-o", $outputFile, "--case-insensitive") `
        -Description "正在预填字典..."
    
    Write-Host ""
    if ($success) {
        Write-Success "预填完成: $outputFile"
    }
    
    Read-Host "按回车继续"
}

function Invoke-TranslateText {
    Show-Header
    Write-Host "【翻译文本】" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "选择翻译方式：" -ForegroundColor Yellow
    Write-Host "  1. Ollama 本地翻译"
    Write-Host "  2. 云端 API 翻译"
    Write-Host "  3. 免费机器翻译"
    Write-Host ""
    
    $method = Read-Host "请选择 (1-3)"
    
    switch ($method) {
        "1" { 
            # Ollama 翻译逻辑
            Write-Host "提示：请使用菜单选项 1 进行 Ollama 一键翻译" -ForegroundColor Yellow
        }
        "2" { 
            # API 翻译逻辑
            Write-Host "提示：请使用菜单选项 2 进行 API 一键翻译" -ForegroundColor Yellow
        }
        "3" { 
            # 免费翻译逻辑
            Write-Host "提示：请使用菜单选项 3 进行免费机翻" -ForegroundColor Yellow
        }
        default {
            Write-ErrorMsg "无效选择"
        }
    }
    
    Read-Host "按回车继续"
}

function Invoke-QualityCheck {
    Show-Header
    Write-Host "【质量检查】" -ForegroundColor Green
    Write-Host ""
    
    $sourceJsonl = Select-File -Title "选择源 JSONL" -Filter "JSONL files (*.jsonl)|*.jsonl"
    if (-not $sourceJsonl) {
        $sourceJsonl = Read-Host "请输入源 JSONL 路径"
    }
    
    $translatedJsonl = Select-File -Title "选择译文 JSONL" -Filter "JSONL files (*.jsonl)|*.jsonl"
    if (-not $translatedJsonl) {
        $translatedJsonl = Read-Host "请输入译文 JSONL 路径"
    }
    
    if (-not (Test-Path $sourceJsonl)) {
        Write-ErrorMsg "源文件不存在"
        Read-Host "按回车继续"
        return
    }
    
    if (-not (Test-Path $translatedJsonl)) {
        Write-ErrorMsg "译文文件不存在"
        Read-Host "按回车继续"
        return
    }
    
    $qaDir = Join-Path $WorkspaceRoot "outputs\qa_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $qaDir -Force | Out-Null
    
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\validate.py") `
        -Arguments @(
            $sourceJsonl, 
            $translatedJsonl,
            "--qa-json", (Join-Path $qaDir "qa.json"),
            "--qa-tsv", (Join-Path $qaDir "qa.tsv"),
            "--qa-html", (Join-Path $qaDir "qa.html"),
            "--ignore-ui-punct"
        ) `
        -Description "正在执行质量检查..."
    
    Write-Host ""
    if ($success) {
        Write-Success "质量检查完成"
        Write-Info "报告位置: $qaDir"
        
        # 尝试打开 HTML 报告
        $htmlReport = Join-Path $qaDir "qa.html"
        if (Test-Path $htmlReport) {
            $openReport = Read-Host "是否打开 HTML 报告？(Y/N)"
            if ($openReport -eq "Y" -or $openReport -eq "y") {
                Start-Process $htmlReport
            }
        }
    }
    
    Read-Host "按回车继续"
}

function Invoke-PatchRPY {
    Show-Header
    Write-Host "【回填翻译】" -ForegroundColor Green
    Write-Host ""
    
    $gamePath = Select-Folder -Description "选择游戏根目录"
    if (-not $gamePath) {
        $gamePath = Read-Host "请输入游戏根目录路径"
    }
    
    $translatedJsonl = Select-File -Title "选择译文 JSONL" -Filter "JSONL files (*.jsonl)|*.jsonl"
    if (-not $translatedJsonl) {
        $translatedJsonl = Read-Host "请输入译文 JSONL 路径"
    }
    
    if (-not (Test-Path $gamePath)) {
        Write-ErrorMsg "游戏目录不存在"
        Read-Host "按回车继续"
        return
    }
    
    if (-not (Test-Path $translatedJsonl)) {
        Write-ErrorMsg "译文文件不存在"
        Read-Host "按回车继续"
        return
    }
    
    $outputDir = Join-Path $WorkspaceRoot "outputs\patched_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    $success = Invoke-SafePythonCommand `
        -Script (Join-Path $WorkspaceRoot "tools\patch.py") `
        -Arguments @($gamePath, $translatedJsonl, "-o", $outputDir, "--advanced") `
        -Description "正在回填翻译..."
    
    Write-Host ""
    if ($success) {
        Write-Success "回填完成: $outputDir"
    }
    
    Read-Host "按回车继续"
}

function Invoke-QualityFix {
    Show-Header
    Write-Host "【质量修复工具】" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "选择功能：" -ForegroundColor Yellow
    Write-Host "  1. 自动修复常见问题"
    Write-Host "  2. 检测英文残留"
    Write-Host ""
    
    $choice = Read-Host "请选择 (1-2)"
    
    $sourceJsonl = Select-File -Title "选择源 JSONL" -Filter "JSONL files (*.jsonl)|*.jsonl"
    if (-not $sourceJsonl) {
        $sourceJsonl = Read-Host "请输入源 JSONL 路径"
    }
    
    $translatedJsonl = Select-File -Title "选择译文 JSONL" -Filter "JSONL files (*.jsonl)|*.jsonl"
    if (-not $translatedJsonl) {
        $translatedJsonl = Read-Host "请输入译文 JSONL 路径"
    }
    
    if (-not (Test-Path $sourceJsonl) -or -not (Test-Path $translatedJsonl)) {
        Write-ErrorMsg "文件不存在"
        Read-Host "按回车继续"
        return
    }
    
    $outputFile = Join-Path $WorkspaceRoot "outputs\fixed_$(Get-Date -Format 'yyyyMMdd_HHmmss').jsonl"
    
    switch ($choice) {
        "1" {
            $success = Invoke-SafePythonCommand `
                -Script (Join-Path $WorkspaceRoot "tools\autofix.py") `
                -Arguments @($sourceJsonl, $translatedJsonl, "-o", $outputFile) `
                -Description "正在自动修复..."
            
            if ($success) {
                Write-Success "修复完成: $outputFile"
            }
        }
        "2" {
            $success = Invoke-SafePythonCommand `
                -Script (Join-Path $WorkspaceRoot "tools\fix_english_leakage.py") `
                -Arguments @($translatedJsonl, "--check-only") `
                -Description "正在检测英文残留..."
            
            if ($success) {
                Write-Host ""
                $fix = Read-Host "是否尝试自动修复？(Y/N)"
                if ($fix -eq "Y" -or $fix -eq "y") {
                    Invoke-SafePythonCommand `
                        -Script (Join-Path $WorkspaceRoot "tools\fix_english_leakage.py") `
                        -Arguments @($translatedJsonl, "-o", $outputFile) `
                        -Description "正在修复..."
                    
                    Write-Success "修复完成: $outputFile"
                }
            }
        }
        default {
            Write-ErrorMsg "无效选择"
        }
    }
    
    Read-Host "按回车继续"
}

function Show-Statistics {
    Show-Header
    Write-Host "【翻译统计】" -ForegroundColor Green
    Write-Host ""
    
    $jsonlFile = Select-File -Title "选择 JSONL 文件" -Filter "JSONL files (*.jsonl)|*.jsonl"
    if (-not $jsonlFile) {
        $jsonlFile = Read-Host "请输入 JSONL 文件路径"
    }
    
    if (-not (Test-Path $jsonlFile)) {
        Write-ErrorMsg "文件不存在"
        Read-Host "按回车继续"
        return
    }
    
    Write-Step "正在分析..."
    
    $total = 0
    $translated = 0
    $empty = 0
    $hasZh = 0
    
    try {
        # 使用 UTF-8 编码读取文件
        $lines = Get-Content $jsonlFile -Encoding UTF8
        
        foreach ($line in $lines) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            
            try {
                $obj = $line | ConvertFrom-Json
                $total++
                
                if ($obj.PSObject.Properties['zh'] -and -not [string]::IsNullOrWhiteSpace($obj.zh)) {
                    $translated++
                    if ($obj.zh -match '[\u4e00-\u9fa5]') {
                        $hasZh++
                    }
                }
                else {
                    $empty++
                }
            }
            catch {
                # 跳过无效的 JSON 行
                continue
            }
        }
    }
    catch {
        Write-ErrorMsg "读取文件失败: $_"
        Read-Host "按回车继续"
        return
    }
    
    $percentage = if ($total -gt 0) { [math]::Round(($translated / $total) * 100, 2) } else { 0 }
    $zhPercentage = if ($total -gt 0) { [math]::Round(($hasZh / $total) * 100, 2) } else { 0 }
    
    Write-Host ""
    Write-Host ("═" * 60) -ForegroundColor Cyan
    Write-Host " 📊 翻译统计报告" -ForegroundColor Yellow
    Write-Host ("═" * 60) -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 文件: $(Split-Path $jsonlFile -Leaf)" -ForegroundColor White
    Write-Host ""
    Write-Host " 总文本数:     $total" -ForegroundColor White
    Write-Host " 已翻译数:     $translated" -ForegroundColor Green
    Write-Host " 含中文数:     $hasZh" -ForegroundColor Cyan
    Write-Host " 未翻译数:     $empty" -ForegroundColor Yellow
    Write-Host ""
    Write-Host " 填充完成度:   $percentage%" -ForegroundColor $(if ($percentage -ge 90) { "Green" } elseif ($percentage -ge 50) { "Yellow" } else { "Red" })
    Write-Host " 中文覆盖率:   $zhPercentage%" -ForegroundColor $(if ($zhPercentage -ge 90) { "Green" } elseif ($zhPercentage -ge 50) { "Yellow" } else { "Red" })
    Write-Host ""
    Write-Host ("═" * 60) -ForegroundColor Cyan
    
    Write-Host ""
    Read-Host "按回车继续"
}

function Show-EnvironmentConfig {
    Show-Header
    Write-Host "【环境配置】" -ForegroundColor Green
    Write-Host ""
    
    Write-Host ("═" * 60) -ForegroundColor Cyan
    Write-Host " 🔧 环境检测报告" -ForegroundColor Yellow
    Write-Host ("═" * 60) -ForegroundColor Cyan
    
    # Python
    Write-Host ""
    Write-Host " Python:" -ForegroundColor Cyan
    try {
        $pythonVer = python --version 2>&1
        Write-Host "  ✓ $pythonVer" -ForegroundColor Green
        
        # 检查关键包
        $packages = @("tqdm", "requests", "colorama")
        foreach ($pkg in $packages) {
            try {
                $null = python -c "import $($pkg.Replace('-', '_'))" 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    ✓ $pkg" -ForegroundColor Gray
                }
                else {
                    Write-Host "    ✗ $pkg (未安装)" -ForegroundColor Yellow
                }
            }
            catch {
                Write-Host "    ✗ $pkg (未安装)" -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host "  ✗ 未安装" -ForegroundColor Red
        Write-Host "    下载: https://www.python.org/" -ForegroundColor Yellow
    }
    
    # Ollama
    Write-Host ""
    Write-Host " Ollama:" -ForegroundColor Cyan
    try {
        $ollamaVer = ollama --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $ollamaVer" -ForegroundColor Green
            
            # 检查模型
            $models = Get-OllamaModels
            if ($models.Count -gt 0) {
                Write-Host "    已安装 $($models.Count) 个模型:" -ForegroundColor Gray
                foreach ($model in $models) {
                    Write-Host "      • $model" -ForegroundColor DarkGray
                }
            }
            else {
                Write-Host "    ⚠ 未安装模型" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "  ⚠ 未运行或未安装" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  ✗ 未安装" -ForegroundColor Red
        Write-Host "    下载: https://ollama.ai" -ForegroundColor Yellow
    }
    
    # GPU
    Write-Host ""
    Write-Host " GPU:" -ForegroundColor Cyan
    try {
        $gpu = nvidia-smi --query-gpu=name --format=csv,noheader 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $gpu" -ForegroundColor Green
            
            # CUDA 版本
            try {
                $cudaVer = nvidia-smi | Select-String "CUDA Version"
                if ($cudaVer) {
                    Write-Host "    $cudaVer" -ForegroundColor Gray
                }
            }
            catch {}
        }
        else {
            Write-Host "  ⚠ 未检测到 NVIDIA GPU" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  ⚠ 未检测到 GPU 或驱动" -ForegroundColor Yellow
    }
    
    # 磁盘空间
    Write-Host ""
    Write-Host " 磁盘空间:" -ForegroundColor Cyan
    try {
        $drive = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -eq (Split-Path $WorkspaceRoot -Qualifier) + "\" }
        if ($drive) {
            $freeGB = [math]::Round($drive.Free / 1GB, 2)
            $usedGB = [math]::Round($drive.Used / 1GB, 2)
            $totalGB = [math]::Round(($drive.Free + $drive.Used) / 1GB, 2)
            
            Write-Host "  可用: $freeGB GB / $totalGB GB" -ForegroundColor $(if ($freeGB -gt 10) { "Green" } elseif ($freeGB -gt 5) { "Yellow" } else { "Red" })
        }
    }
    catch {
        Write-Host "  ⚠ 无法获取信息" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host ("═" * 60) -ForegroundColor Cyan
    
    Write-Host ""
    Read-Host "按回车继续"
}

# ==================== 主循环 ====================

# 显示欢迎信息
Show-Header
Write-Host "欢迎使用 Ren'Py 汉化工具集！" -ForegroundColor Green
Write-Host "本工具支持多种翻译方案，请根据需要选择。" -ForegroundColor White
Write-Host ""
Write-Host "注意: 所有文件均使用 UTF-8 编码，确保中文正常显示。" -ForegroundColor Yellow
Write-Host ""
Start-Sleep -Seconds 2

while ($true) {
    Show-Header
    Show-MainMenu
    
    $choice = Read-Host "请输入选项 (0-12)"
    
    switch ($choice) {
        "1" { Invoke-OneClickOllama }
        "2" { Invoke-OneClickAPI }
        "3" { Invoke-OneClickFreeMT }
        "4" { Invoke-ExtractText }
        "5" { Invoke-GenerateDict }
        "6" { Invoke-PrefillDict }
        "7" { Invoke-TranslateText }
        "8" { Invoke-QualityCheck }
        "9" { Invoke-PatchRPY }
        "10" { Invoke-QualityFix }
        "11" { Show-Statistics }
        "12" { Show-EnvironmentConfig }
        "0" {
            Clear-Host
            Write-Host ""
            Write-Host "感谢使用 Ren'Py 汉化工具集！" -ForegroundColor Green
            Write-Host "Goodbye!" -ForegroundColor Cyan
            Write-Host ""
            exit 0
        }
        default {
            Write-Host ""
            Write-Host "无效选项，请重新选择" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
