# Grok API 集成测试脚本
# 用于验证 menu.ps1 + translate_grok.py 是否正常工作

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [Console]::InputEncoding = [System.Text.Encoding]::UTF8

Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Grok API 集成测试" -ForegroundColor Green
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 测试文件路径
$testJsonl = "outputs\test_basement\extract\project_en_for_grok.jsonl"
$testOutput = "outputs\grok_integration_test"

# 检查测试文件
if (-not (Test-Path $testJsonl)) {
    Write-Host "❌ 测试文件不存在: $testJsonl" -ForegroundColor Red
    Write-Host "请先运行 Extract RPY 任务生成测试数据" -ForegroundColor Yellow
    Read-Host "按回车退出"
    exit 1
}

# 统计行数
$lineCount = (Get-Content $testJsonl -Encoding UTF8).Count
Write-Host "✓ 测试文件: $testJsonl" -ForegroundColor Green
Write-Host "  行数: $lineCount" -ForegroundColor White
Write-Host ""

# 成本预估
Write-Host "💰 成本预估 (grok-4-fast-reasoning):" -ForegroundColor Cyan
$estimatedInputTokens = [int]($lineCount * 50)
$estimatedOutputTokens = [int]($estimatedInputTokens * 1.2)
$inputCostUSD = ($estimatedInputTokens / 1000000.0) * 0.20
$outputCostUSD = ($estimatedOutputTokens / 1000000.0) * 0.50
$totalCostUSD = $inputCostUSD + $outputCostUSD
$totalCostCNY = $totalCostUSD * 7.1

Write-Host "   输入: $estimatedInputTokens tokens × $0.20/M = `$$([math]::Round($inputCostUSD, 4))" -ForegroundColor White
Write-Host "   输出: $estimatedOutputTokens tokens × $0.50/M = `$$([math]::Round($outputCostUSD, 4))" -ForegroundColor White
Write-Host "   总计: `$$([math]::Round($totalCostUSD, 3)) ≈ ¥$([math]::Round($totalCostCNY, 2))" -ForegroundColor Yellow
Write-Host ""

# 提示输入 API Key
Write-Host "请输入 xAI API Key (测试用):" -ForegroundColor Yellow
Write-Host "（如果没有 API Key，按 Ctrl+C 取消）" -ForegroundColor Gray
$apiKey = Read-Host -AsSecureString "API Key"
$apiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
)

if ([string]::IsNullOrWhiteSpace($apiKeyPlain)) {
    Write-Host "❌ API Key 不能为空" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

Write-Host ""
Write-Host "开始测试翻译..." -ForegroundColor Green
Write-Host "命令: python tools\translate_grok.py `"$testJsonl`" -o `"$testOutput`" --model grok-4-fast-reasoning --api-key ****" -ForegroundColor Gray
Write-Host ""

# 执行翻译
try {
    $process = Start-Process -FilePath "python" `
        -ArgumentList "tools\translate_grok.py", $testJsonl, "-o", $testOutput, "--model", "grok-4-fast-reasoning", "--api-key", $apiKeyPlain `
        -NoNewWindow -Wait -PassThru
    
    if ($process.ExitCode -eq 0) {
        Write-Host ""
        Write-Host "✅ 翻译成功！" -ForegroundColor Green
        
        # 检查输出文件
        $outputFile = Join-Path $testOutput "translated.jsonl"
        if (Test-Path $outputFile) {
            $outputLines = (Get-Content $outputFile -Encoding UTF8).Count
            Write-Host "✓ 输出文件: $outputFile" -ForegroundColor Green
            Write-Host "  翻译行数: $outputLines" -ForegroundColor White
            
            # 检查是否有 zh 字段
            $sampleLine = Get-Content $outputFile -Encoding UTF8 -TotalCount 1
            $sampleObj = $sampleLine | ConvertFrom-Json
            if ($sampleObj.zh) {
                Write-Host "  示例翻译: $($sampleObj.en) → $($sampleObj.zh)" -ForegroundColor Cyan
            }
            else {
                Write-Host "⚠ 警告: 输出文件没有 zh 字段" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "⚠ 警告: 输出文件不存在" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host ""
        Write-Host "❌ 翻译失败 (退出码: $($process.ExitCode))" -ForegroundColor Red
    }
}
catch {
    Write-Host ""
    Write-Host "❌ 执行失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Read-Host "按回车退出"
