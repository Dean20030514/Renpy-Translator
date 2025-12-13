#!/usr/bin/env pwsh
# GUI 启动器 - 带图形界面的 Ren'Py 游戏汉化工具
# 自动文件夹选择、模型选择、字典生成

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = "Stop"

# ==================== 函数定义 ====================

function Show-FolderBrowser {
    param([string]$Description = "选择文件夹")
    
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = $Description
    $folderBrowser.RootFolder = [System.Environment+SpecialFolder]::MyComputer
    $folderBrowser.ShowNewFolderButton = $false
    
    if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $folderBrowser.SelectedPath
    }
    return $null
}

function Get-InstalledOllamaModels {
    try {
        # 检查 Ollama 是否安装
        $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
        if (-not $ollamaCmd) {
            return @{
                Success = $false
                Error = "未安装 Ollama"
                Models = @()
            }
        }

        # 获取模型列表 (使用后台作业避免卡死)
        $job = Start-Job -ScriptBlock {
            ollama list 2>&1 | Out-String
        }
        
        # 等待最多 10 秒
        $completed = Wait-Job $job -Timeout 10
        
        if ($null -eq $completed) {
            # 超时
            Stop-Job $job
            Remove-Job $job
            return @{
                Success = $false
                Error = "Ollama 响应超时 (可能未启动)"
                Models = @()
            }
        }
        
        $output = Receive-Job $job
        Remove-Job $job
        
        if (-not $output) {
            return @{
                Success = $false
                Error = "Ollama 未运行或出错"
                Models = @()
            }
        }

        # 解析输出
        $models = @()
        $lines = $output -split "`n"
        foreach ($line in $lines) {
            # 跳过空行和标题行
            if ([string]::IsNullOrWhiteSpace($line) -or $line -match '^NAME\s+ID\s+SIZE') {
                continue
            }
            
            # 提取模型名称 (第一列)
            if ($line -match '^(\S+)') {
                $modelName = $matches[1].Trim()
                if ($modelName -and $modelName -ne 'NAME') {
                    $models += $modelName
                }
            }
        }

        return @{
            Success = $true
            Error = $null
            Models = $models
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
            Models = @()
        }
    }
}

function Show-ModelSelector {
    # 获取已安装的模型
    Write-Host "正在检测本地 Ollama 模型..." -ForegroundColor Cyan
    $modelInfo = Get-InstalledOllamaModels
    
    # 创建窗口
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "选择翻译模型"
    $form.Size = New-Object System.Drawing.Size(500, 480)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    
    # 标签
    $label = New-Object System.Windows.Forms.Label
    $label.Location = New-Object System.Drawing.Point(10, 10)
    $label.Size = New-Object System.Drawing.Size(470, 40)
    
    if ($modelInfo.Success) {
        $label.Text = "检测到 $($modelInfo.Models.Count) 个本地模型，请选择:"
        $label.ForeColor = [System.Drawing.Color]::Green
    } else {
        $label.Text = "⚠ $($modelInfo.Error)`n请先安装 Ollama: https://ollama.ai/"
        $label.ForeColor = [System.Drawing.Color]::Red
    }
    $form.Controls.Add($label)
    
    # 模型列表
    $listBox = New-Object System.Windows.Forms.ListBox
    $listBox.Location = New-Object System.Drawing.Point(10, 55)
    $listBox.Size = New-Object System.Drawing.Size(470, 200)
    $listBox.Font = New-Object System.Drawing.Font("Consolas", 10)
    
    # 添加检测到的模型
    if ($modelInfo.Success -and $modelInfo.Models.Count -gt 0) {
        foreach ($model in $modelInfo.Models) {
            Write-Host "  ✓ $model" -ForegroundColor Green
            [void]$listBox.Items.Add($model)
        }
        
        # 优先选择推荐的模型
        $preferredModels = @('qwen2.5:14b', 'qwen2.5:7b', 'qwen2.5:32b')
        foreach ($preferred in $preferredModels) {
            $index = $listBox.Items.IndexOf($preferred)
            if ($index -ge 0) {
                $listBox.SelectedIndex = $index
                break
            }
        }
        
        # 如果没有推荐模型，选择第一个
        if ($listBox.SelectedIndex -eq -1) {
            $listBox.SelectedIndex = 0
        }
    } else {
        [void]$listBox.Items.Add("(无可用模型)")
        $listBox.Enabled = $false
    }
    
    # 添加分隔线和自定义选项
    [void]$listBox.Items.Add("─────────────────────")
    [void]$listBox.Items.Add("手动输入其他模型...")
    
    $form.Controls.Add($listBox)
    
    # 自定义输入框
    $customLabel = New-Object System.Windows.Forms.Label
    $customLabel.Location = New-Object System.Drawing.Point(10, 265)
    $customLabel.Size = New-Object System.Drawing.Size(470, 20)
    $customLabel.Text = "手动输入模型名称 (选择'手动输入其他模型...'时填写):"
    $form.Controls.Add($customLabel)
    
    $customTextBox = New-Object System.Windows.Forms.TextBox
    $customTextBox.Location = New-Object System.Drawing.Point(10, 290)
    $customTextBox.Size = New-Object System.Drawing.Size(390, 25)
    $customTextBox.Enabled = $false
    $customTextBox.Text = "例如: qwen2.5:7b"
    $customTextBox.ForeColor = [System.Drawing.Color]::Gray
    $form.Controls.Add($customTextBox)
    
    # 刷新按钮
    $refreshButton = New-Object System.Windows.Forms.Button
    $refreshButton.Location = New-Object System.Drawing.Point(410, 288)
    $refreshButton.Size = New-Object System.Drawing.Size(70, 28)
    $refreshButton.Text = "刷新"
    $refreshButton.Add_Click({
        $form.Tag = "refresh"
        $form.Close()
    })
    $form.Controls.Add($refreshButton)
    
    # 监听选择变化
    $listBox.Add_SelectedIndexChanged({
        $selected = $listBox.SelectedItem
        if ($selected -eq "手动输入其他模型...") {
            $customTextBox.Enabled = $true
            if ($customTextBox.Text -eq "例如: qwen2.5:7b") {
                $customTextBox.Text = ""
                $customTextBox.ForeColor = [System.Drawing.Color]::Black
            }
            $customTextBox.Focus()
        } elseif ($selected -ne "─────────────────────" -and $selected -ne "(无可用模型)") {
            $customTextBox.Enabled = $false
        }
    })
    
    # 提示信息
    $infoLabel = New-Object System.Windows.Forms.Label
    $infoLabel.Location = New-Object System.Drawing.Point(10, 325)
    $infoLabel.Size = New-Object System.Drawing.Size(470, 40)
    if ($modelInfo.Success -and $modelInfo.Models.Count -gt 0) {
        $infoLabel.Text = "✓ Ollama 运行正常 | 推荐: qwen2.5:14b (速度与质量平衡)"
        $infoLabel.ForeColor = [System.Drawing.Color]::DarkGreen
    } else {
        $infoLabel.Text = "安装命令: ollama pull qwen2.5:14b`n下载地址: https://ollama.ai/"
        $infoLabel.ForeColor = [System.Drawing.Color]::DarkOrange
    }
    $form.Controls.Add($infoLabel)
    
    # 确定按钮
    $okButton = New-Object System.Windows.Forms.Button
    $okButton.Location = New-Object System.Drawing.Point(300, 395)
    $okButton.Size = New-Object System.Drawing.Size(80, 30)
    $okButton.Text = "确定"
    $okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
    if (-not $modelInfo.Success -or $modelInfo.Models.Count -eq 0) {
        $okButton.Enabled = $false
    }
    $form.Controls.Add($okButton)
    $form.AcceptButton = $okButton
    
    # 取消按钮
    $cancelButton = New-Object System.Windows.Forms.Button
    $cancelButton.Location = New-Object System.Drawing.Point(390, 395)
    $cancelButton.Size = New-Object System.Drawing.Size(80, 30)
    $cancelButton.Text = "取消"
    $cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
    $form.Controls.Add($cancelButton)
    $form.CancelButton = $cancelButton
    
    # 显示窗口
    $result = $form.ShowDialog()
    
    # 检查是否点击了刷新
    if ($form.Tag -eq "refresh") {
        return @{ Refresh = $true }
    }
    
    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        $selectedModel = $listBox.SelectedItem
        
        # 跳过分隔线
        if ($selectedModel -eq "─────────────────────" -or $selectedModel -eq "(无可用模型)") {
            [System.Windows.Forms.MessageBox]::Show("请选择一个有效的模型", "提示", "OK", "Warning")
            return $null
        }
        
        if ($selectedModel -eq "手动输入其他模型...") {
            $modelName = $customTextBox.Text.Trim()
            if ([string]::IsNullOrEmpty($modelName)) {
                [System.Windows.Forms.MessageBox]::Show("请输入模型名称", "错误", "OK", "Error")
                return $null
            }
            return @{ Model = $modelName; Refresh = $false }
        } else {
            return @{ Model = $selectedModel; Refresh = $false }
        }
    }
    
    return $null
}

function Show-OptionsDialog {
    # 创建窗口
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "翻译选项"
    $form.Size = New-Object System.Drawing.Size(450, 420)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    
    # 标题
    $label = New-Object System.Windows.Forms.Label
    $label.Location = New-Object System.Drawing.Point(10, 10)
    $label.Size = New-Object System.Drawing.Size(420, 30)
    $label.Text = "选择翻译选项:"
    $label.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 10, [System.Drawing.FontStyle]::Bold)
    $form.Controls.Add($label)
    
    # 选项 1: 跳过翻译
    $checkSkipTranslate = New-Object System.Windows.Forms.CheckBox
    $checkSkipTranslate.Location = New-Object System.Drawing.Point(20, 50)
    $checkSkipTranslate.Size = New-Object System.Drawing.Size(400, 30)
    $checkSkipTranslate.Text = "跳过 AI 翻译 (仅使用字典预填)"
    $checkSkipTranslate.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $form.Controls.Add($checkSkipTranslate)
    
    # 选项 2: 跳过构建
    $checkSkipBuild = New-Object System.Windows.Forms.CheckBox
    $checkSkipBuild.Location = New-Object System.Drawing.Point(20, 90)
    $checkSkipBuild.Size = New-Object System.Drawing.Size(400, 30)
    $checkSkipBuild.Text = "跳过游戏构建 (仅生成翻译文件)"
    $checkSkipBuild.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $form.Controls.Add($checkSkipBuild)
    
    # 选项 3: 自动生成字典
    $checkAutoDict = New-Object System.Windows.Forms.CheckBox
    $checkAutoDict.Location = New-Object System.Drawing.Point(20, 130)
    $checkAutoDict.Size = New-Object System.Drawing.Size(400, 30)
    $checkAutoDict.Text = "自动生成游戏专用字典"
    $checkAutoDict.Checked = $true
    $checkAutoDict.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $form.Controls.Add($checkAutoDict)
    
    # 高级设置按钮
    $advancedButton = New-Object System.Windows.Forms.Button
    $advancedButton.Location = New-Object System.Drawing.Point(20, 170)
    $advancedButton.Size = New-Object System.Drawing.Size(100, 28)
    $advancedButton.Text = "⚙ 高级设置"
    $advancedButton.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $form.Controls.Add($advancedButton)
    
    # 高级设置状态标签
    $advancedLabel = New-Object System.Windows.Forms.Label
    $advancedLabel.Location = New-Object System.Drawing.Point(130, 172)
    $advancedLabel.Size = New-Object System.Drawing.Size(300, 25)
    $advancedLabel.Text = "过滤: 开 | Workers: 自动 | Flush: 20 | 优化: 关"
    $advancedLabel.ForeColor = [System.Drawing.Color]::Gray
    $advancedLabel.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 8)
    $form.Controls.Add($advancedLabel)
    
    # 高级设置默认值
    $advancedSettings = @{
        SkipNonDialog = $true
        WorkersMode = "auto"
        WorkersValue = 4
        FlushInterval = 20
        UseOptimized = $false        # 新增：是否启用优化翻译模式
        QualityThreshold = 0.7       # 新增：优化模式质量阈值
    }
    
    # 高级设置点击事件
    $advancedButton.Add_Click({
        $advResult = Show-AdvancedDialog -CurrentSettings $advancedSettings
        if ($advResult) {
            $advancedSettings = $advResult
            
            # 更新状态标签
            $filterText = if ($advancedSettings.SkipNonDialog) { "开" } else { "关" }
            $optimizedText = if ($advancedSettings.UseOptimized) { "开" } else { "关" }
            if ($advancedSettings.WorkersMode -eq "auto") {
                $advancedLabel.Text = "过滤: $filterText | Workers: 自动 | Flush: $($advancedSettings.FlushInterval) | 优化: $optimizedText"
            } else {
                $advancedLabel.Text = "过滤: $filterText | Workers: $($advancedSettings.WorkersValue) | Flush: $($advancedSettings.FlushInterval) | 优化: $optimizedText"
            }
        }
    })
    
    # 说明
    $labelInfo = New-Object System.Windows.Forms.Label
    $labelInfo.Location = New-Object System.Drawing.Point(20, 210)
    $labelInfo.Size = New-Object System.Drawing.Size(400, 100)
    $labelInfo.Text = @"
提示: 
• 自动生成的字典会保存在游戏输出目录
  outputs/[游戏名]/dictionaries/
  您可以手动编辑后用于后续翻译
• 高级设置可调整并发线程、过滤规则和保存频率
"@
    $labelInfo.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 8)
    $labelInfo.ForeColor = [System.Drawing.Color]::Gray
    $form.Controls.Add($labelInfo)
    
    # 确定按钮
    $okButton = New-Object System.Windows.Forms.Button
    $okButton.Location = New-Object System.Drawing.Point(240, 330)
    $okButton.Size = New-Object System.Drawing.Size(80, 30)
    $okButton.Text = "确定"
    $okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $form.Controls.Add($okButton)
    $form.AcceptButton = $okButton
    
    # 取消按钮
    $cancelButton = New-Object System.Windows.Forms.Button
    $cancelButton.Location = New-Object System.Drawing.Point(330, 330)
    $cancelButton.Size = New-Object System.Drawing.Size(80, 30)
    $cancelButton.Text = "取消"
    $cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
    $form.Controls.Add($cancelButton)
    $form.CancelButton = $cancelButton
    
    # 显示窗口
    $result = $form.ShowDialog()
    
    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        return @{
            SkipTranslate = $checkSkipTranslate.Checked
            SkipBuild = $checkSkipBuild.Checked
            AutoDict = $checkAutoDict.Checked
            Advanced = $advancedSettings
        }
    }
    
    return $null
}

function Show-AdvancedDialog {
    param([hashtable]$CurrentSettings)
    
    # 创建窗口
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "高级设置"
    $form.Size = New-Object System.Drawing.Size(480, 520)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    
    # 标题
    $labelTitle = New-Object System.Windows.Forms.Label
    $labelTitle.Location = New-Object System.Drawing.Point(15, 15)
    $labelTitle.Size = New-Object System.Drawing.Size(440, 30)
    $labelTitle.Text = "翻译高级设置"
    $labelTitle.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 11, [System.Drawing.FontStyle]::Bold)
    $form.Controls.Add($labelTitle)
    
    # ========== 分组框1: 内容过滤 ==========
    $groupFilter = New-Object System.Windows.Forms.GroupBox
    $groupFilter.Location = New-Object System.Drawing.Point(15, 50)
    $groupFilter.Size = New-Object System.Drawing.Size(440, 60)
    $groupFilter.Text = " 内容过滤 "
    $groupFilter.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $form.Controls.Add($groupFilter)
    
    $checkSkipNonDialog = New-Object System.Windows.Forms.CheckBox
    $checkSkipNonDialog.Location = New-Object System.Drawing.Point(15, 25)
    $checkSkipNonDialog.Size = New-Object System.Drawing.Size(400, 25)
    $checkSkipNonDialog.Text = "过滤非台词内容 (跳过路径、变量名、代码等)"
    $checkSkipNonDialog.Checked = $CurrentSettings.SkipNonDialog
    $checkSkipNonDialog.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $groupFilter.Controls.Add($checkSkipNonDialog)
    
    # ========== 分组框2: 并发设置 ==========
    $groupWorkers = New-Object System.Windows.Forms.GroupBox
    $groupWorkers.Location = New-Object System.Drawing.Point(15, 120)
    $groupWorkers.Size = New-Object System.Drawing.Size(440, 85)
    $groupWorkers.Text = " 并发线程 "
    $groupWorkers.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $form.Controls.Add($groupWorkers)
    
    # Workers 模式选择
    $radioAuto = New-Object System.Windows.Forms.RadioButton
    $radioAuto.Location = New-Object System.Drawing.Point(15, 25)
    $radioAuto.Size = New-Object System.Drawing.Size(180, 25)
    $radioAuto.Text = "自动选择 (推荐)"
    $radioAuto.Checked = ($CurrentSettings.WorkersMode -eq "auto")
    $radioAuto.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $groupWorkers.Controls.Add($radioAuto)
    
    $radioManual = New-Object System.Windows.Forms.RadioButton
    $radioManual.Location = New-Object System.Drawing.Point(200, 25)
    $radioManual.Size = New-Object System.Drawing.Size(100, 25)
    $radioManual.Text = "手动设置:"
    $radioManual.Checked = ($CurrentSettings.WorkersMode -eq "manual")
    $radioManual.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $groupWorkers.Controls.Add($radioManual)
    
    $numericWorkers = New-Object System.Windows.Forms.NumericUpDown
    $numericWorkers.Location = New-Object System.Drawing.Point(305, 23)
    $numericWorkers.Size = New-Object System.Drawing.Size(70, 25)
    $numericWorkers.Minimum = 1
    $numericWorkers.Maximum = 32
    $numericWorkers.Value = $CurrentSettings.WorkersValue
    $numericWorkers.Enabled = ($CurrentSettings.WorkersMode -eq "manual")
    $numericWorkers.Font = New-Object System.Drawing.Font("Consolas", 10)
    $groupWorkers.Controls.Add($numericWorkers)
    
    $labelWorkersHint = New-Object System.Windows.Forms.Label
    $labelWorkersHint.Location = New-Object System.Drawing.Point(15, 55)
    $labelWorkersHint.Size = New-Object System.Drawing.Size(410, 20)
    $labelWorkersHint.Text = "💡 自动模式会根据模型大小和 GPU 配置选择最佳线程数"
    $labelWorkersHint.ForeColor = [System.Drawing.Color]::Gray
    $labelWorkersHint.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 8)
    $groupWorkers.Controls.Add($labelWorkersHint)
    
    # Radio 事件
    $radioAuto.Add_Click({
        $numericWorkers.Enabled = $false
    })
    $radioManual.Add_Click({
        $numericWorkers.Enabled = $true
    })
    
    # ========== 分组框3: 保存设置 ==========
    $groupSave = New-Object System.Windows.Forms.GroupBox
    $groupSave.Location = New-Object System.Drawing.Point(15, 215)
    $groupSave.Size = New-Object System.Drawing.Size(440, 85)
    $groupSave.Text = " 自动保存 "
    $groupSave.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $form.Controls.Add($groupSave)
    
    $labelFlush = New-Object System.Windows.Forms.Label
    $labelFlush.Location = New-Object System.Drawing.Point(15, 30)
    $labelFlush.Size = New-Object System.Drawing.Size(140, 25)
    $labelFlush.Text = "每翻译多少条保存:"
    $labelFlush.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $labelFlush.TextAlign = [System.Drawing.ContentAlignment]::MiddleLeft
    $groupSave.Controls.Add($labelFlush)
    
    $numericFlush = New-Object System.Windows.Forms.NumericUpDown
    $numericFlush.Location = New-Object System.Drawing.Point(160, 28)
    $numericFlush.Size = New-Object System.Drawing.Size(70, 25)
    $numericFlush.Minimum = 0
    $numericFlush.Maximum = 100
    $numericFlush.Value = $CurrentSettings.FlushInterval
    $numericFlush.Font = New-Object System.Drawing.Font("Consolas", 10)
    $groupSave.Controls.Add($numericFlush)
    
    $labelFlushUnit = New-Object System.Windows.Forms.Label
    $labelFlushUnit.Location = New-Object System.Drawing.Point(240, 30)
    $labelFlushUnit.Size = New-Object System.Drawing.Size(40, 25)
    $labelFlushUnit.Text = "条"
    $labelFlushUnit.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $labelFlushUnit.TextAlign = [System.Drawing.ContentAlignment]::MiddleLeft
    $groupSave.Controls.Add($labelFlushUnit)
    
    $labelFlushHint = New-Object System.Windows.Forms.Label
    $labelFlushHint.Location = New-Object System.Drawing.Point(15, 58)
    $labelFlushHint.Size = New-Object System.Drawing.Size(410, 20)
    $labelFlushHint.Text = "💡 设为 0 表示仅在最后保存 | 推荐值: 20 (防止崩溃丢失进度)"
    $labelFlushHint.ForeColor = [System.Drawing.Color]::Gray
    $labelFlushHint.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 8)
    $groupSave.Controls.Add($labelFlushHint)
    
    # ========== 分组框4: 优化模式 (新增) ==========
    $groupOptimized = New-Object System.Windows.Forms.GroupBox
    $groupOptimized.Location = New-Object System.Drawing.Point(15, 310)
    $groupOptimized.Size = New-Object System.Drawing.Size(440, 85)
    $groupOptimized.Text = " 🚀 优化翻译模式 "
    $groupOptimized.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $form.Controls.Add($groupOptimized)
    
    $checkUseOptimized = New-Object System.Windows.Forms.CheckBox
    $checkUseOptimized.Location = New-Object System.Drawing.Point(15, 25)
    $checkUseOptimized.Size = New-Object System.Drawing.Size(380, 25)
    $checkUseOptimized.Text = "启用优化模式 (连接池+质量验证，质量+29%，速度+15%)"
    $checkUseOptimized.Checked = $CurrentSettings.UseOptimized
    $checkUseOptimized.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $groupOptimized.Controls.Add($checkUseOptimized)
    
    $labelQualityHint = New-Object System.Windows.Forms.Label
    $labelQualityHint.Location = New-Object System.Drawing.Point(15, 55)
    $labelQualityHint.Size = New-Object System.Drawing.Size(410, 20)
    $labelQualityHint.Text = "💡 推荐大规模翻译启用 | 质量阈值: 0.7 | 自动重试+修复"
    $labelQualityHint.ForeColor = [System.Drawing.Color]::Gray
    $labelQualityHint.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 8)
    $groupOptimized.Controls.Add($labelQualityHint)
    
    # ========== 按钮 ==========
    $okButton = New-Object System.Windows.Forms.Button
    $okButton.Location = New-Object System.Drawing.Point(260, 425)
    $okButton.Size = New-Object System.Drawing.Size(90, 35)
    $okButton.Text = "确定"
    $okButton.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $form.Controls.Add($okButton)
    $form.AcceptButton = $okButton
    
    $cancelButton = New-Object System.Windows.Forms.Button
    $cancelButton.Location = New-Object System.Drawing.Point(360, 425)
    $cancelButton.Size = New-Object System.Drawing.Size(90, 35)
    $cancelButton.Text = "取消"
    $cancelButton.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
    $form.Controls.Add($cancelButton)
    $form.CancelButton = $cancelButton
    
    # 显示窗口
    $result = $form.ShowDialog()
    
    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        return @{
            SkipNonDialog = $checkSkipNonDialog.Checked
            WorkersMode = if ($radioAuto.Checked) { "auto" } else { "manual" }
            WorkersValue = $numericWorkers.Value
            FlushInterval = $numericFlush.Value
            UseOptimized = $checkUseOptimized.Checked
            QualityThreshold = $CurrentSettings.QualityThreshold  # 保持原值
        }
    }
    
    return $null
}

# ==================== 主流程 ====================

Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "            Ren'Py 游戏汉化工具 - GUI 启动器            " -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 前置检查: 启用 CUDA 环境
$initCudaScript = Join-Path $PSScriptRoot "init_cuda.ps1"
if (Test-Path $initCudaScript) {
    & $initCudaScript
}

# 步骤 1: 选择游戏文件夹
Write-Host "▶ 步骤 1: 选择 Ren'Py 游戏文件夹" -ForegroundColor Yellow
$gamePath = Show-FolderBrowser -Description "选择 Ren'Py 游戏根目录 (包含 game 文件夹)"

if ([string]::IsNullOrEmpty($gamePath)) {
    Write-Host "❌ 已取消" -ForegroundColor Red
    exit 0
}

# 验证是否是 Ren'Py 游戏
$gameDir = Join-Path $gamePath "game"
if (-not (Test-Path $gameDir)) {
    [System.Windows.Forms.MessageBox]::Show(
        "所选文件夹不是有效的 Ren'Py 游戏目录`n(找不到 game 子文件夹)",
        "错误",
        "OK",
        "Error"
    )
    exit 1
}

Write-Host "✓ 已选择: $gamePath" -ForegroundColor Green
Write-Host ""

# 步骤 2: 选择翻译选项
Write-Host "▶ 步骤 2: 配置翻译选项" -ForegroundColor Yellow
$options = Show-OptionsDialog

if ($null -eq $options) {
    Write-Host "❌ 已取消" -ForegroundColor Red
    exit 0
}

Write-Host "✓ 选项已配置" -ForegroundColor Green
Write-Host "  跳过 AI 翻译: $($options.SkipTranslate)" -ForegroundColor Gray
Write-Host "  跳过游戏构建: $($options.SkipBuild)" -ForegroundColor Gray
Write-Host "  自动生成字典: $($options.AutoDict)" -ForegroundColor Gray
Write-Host "  过滤非台词: $(if ($options.Advanced.SkipNonDialog) { '开' } else { '关' })" -ForegroundColor Gray
if ($options.Advanced.WorkersMode -eq "auto") {
    Write-Host "  并发线程: 自动选择" -ForegroundColor Gray
} else {
    Write-Host "  并发线程: $($options.Advanced.WorkersValue) (手动)" -ForegroundColor Gray
}
Write-Host "  最少词数: $($options.Advanced.MinWords)" -ForegroundColor Gray
Write-Host "  自动保存间隔: $($options.Advanced.FlushInterval)" -ForegroundColor Gray
Write-Host ""

# 步骤 3: 选择模型 (如果不跳过翻译)
$model = $null
if (-not $options.SkipTranslate) {
    Write-Host "▶ 步骤 3: 选择翻译模型" -ForegroundColor Yellow
    
    # 支持刷新功能
    do {
        $modelResult = Show-ModelSelector
        
        if ($null -eq $modelResult) {
            Write-Host "❌ 已取消" -ForegroundColor Red
            exit 0
        }
        
        # 如果点击了刷新，重新显示对话框
        if ($modelResult.Refresh) {
            Write-Host "正在刷新模型列表..." -ForegroundColor Cyan
            continue
        }
        
        $model = $modelResult.Model
        break
    } while ($true)
    
    Write-Host "✓ 已选择模型: $model" -ForegroundColor Green
    Write-Host ""
}

# 提取游戏名称
$gameName = Split-Path -Leaf $gamePath
$outputRoot = "outputs/$gameName"

Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "开始处理..." -ForegroundColor Green
Write-Host "游戏: $gameName" -ForegroundColor White
Write-Host "输出: $outputRoot" -ForegroundColor White
if ($model) {
    Write-Host "模型: $model" -ForegroundColor White
}
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 创建输出目录
$dirs = @(
    "$outputRoot/extract",
    "$outputRoot/prefilled",
    "$outputRoot/llm_batches",
    "$outputRoot/llm_results",
    "$outputRoot/final",
    "$outputRoot/qa",
    "$outputRoot/patched",
    "$outputRoot/cn_build",
    "$outputRoot/dictionaries"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }
}

# ========== 步骤 1: 提取文本 ==========
Write-Host "▶ 步骤 1/7: 提取游戏文本" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

# 根据高级设置决定 workers
$extractWorkers = if ($options.Advanced.WorkersMode -eq "auto") { 4 } else { $options.Advanced.WorkersValue }

python tools/extract.py `
    "$gamePath" `
    -o "$outputRoot/extract" `
    --workers $extractWorkers

if ($LASTEXITCODE -ne 0) { 
    [System.Windows.Forms.MessageBox]::Show("文本提取失败", "错误", "OK", "Error")
    exit 1 
}

$extractedJsonl = "$outputRoot/extract/project_en_for_grok.jsonl"
$lineCount = (Get-Content $extractedJsonl).Count
Write-Host "✓ 成功提取 $lineCount 条文本" -ForegroundColor Green
Write-Host ""

# ========== 自动生成字典 ==========
if ($options.AutoDict) {
    Write-Host "▶ 自动生成游戏字典" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    
    python tools/generate_dict.py `
        "$extractedJsonl" `
        -o "$outputRoot/dictionaries" `
        --game-name $gameName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 字典生成完成: $outputRoot/dictionaries" -ForegroundColor Green
        Write-Host "  提示: 您可以编辑生成的 CSV 文件来完善翻译" -ForegroundColor Yellow
    } else {
        Write-Warning "字典生成失败,将继续使用现有字典"
    }
    Write-Host ""
}

# ========== 步骤 2: 字典预填 ==========
Write-Host "▶ 步骤 2/7: 使用字典预填翻译" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

# 使用通用字典 (最高优先级) + 游戏专用字典 (补充)
$dictToUse = $null

if (Test-Path "data/dictionaries") {
    $dictToUse = "data/dictionaries"
    Write-Host "  使用通用字典: data/dictionaries" -ForegroundColor Cyan
    
    # 如果游戏专用字典也存在，合并使用
    if (Test-Path "$outputRoot/dictionaries") {
        # prefill.py 支持传入目录，会自动加载所有字典
        # 这里我们传入通用字典，稍后可以手动合并或使用多次预填
        Write-Host "  游戏专用字典也存在: $outputRoot/dictionaries" -ForegroundColor Gray
        Write-Host "  提示: 通用字典优先，游戏字典作为补充" -ForegroundColor Yellow
    }
} elseif (Test-Path "$outputRoot/dictionaries") {
    $dictToUse = "$outputRoot/dictionaries"
    Write-Host "  使用游戏专用字典: $outputRoot/dictionaries" -ForegroundColor Cyan
    Write-Host "  提示: 通用字典不存在" -ForegroundColor Yellow
} else {
    Write-Warning "未找到任何字典文件,预填可能不会有效果"
    Write-Host "  建议: 在 data/dictionaries/ 添加通用字典" -ForegroundColor Yellow
    # 创建空字典目录避免错误
    $dictToUse = "$outputRoot/dictionaries"
    New-Item -Path $dictToUse -ItemType Directory -Force | Out-Null
}

python tools/prefill.py `
    "$extractedJsonl" `
    $dictToUse `
    -o "$outputRoot/prefilled/prefilled.jsonl" `
    --case-insensitive `
    --dict-backend memory

if ($LASTEXITCODE -ne 0) { 
    [System.Windows.Forms.MessageBox]::Show("字典预填失败", "错误", "OK", "Error")
    exit 1 
}
Write-Host ""

$prefilledJsonl = "$outputRoot/prefilled/prefilled.jsonl"

# ========== 步骤 3-5: LLM 翻译 ==========
if (-not $options.SkipTranslate) {
    Write-Host "▶ 步骤 3/7: 拆分 LLM 翻译批次" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    
    python tools/split.py `
        "$prefilledJsonl" `
        "$outputRoot/llm_batches" `
        --skip-has-zh `
        --max-tokens 50000
    
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host ""
    
    Write-Host "▶ 步骤 4/7: 使用 Ollama 翻译" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "模型: $model" -ForegroundColor Cyan
    Write-Host ""
    
    # 优化 GPU 使用：尽可能多的层放到 GPU
    $env:OLLAMA_NUM_GPU = "999"
    $env:OLLAMA_GPU_OVERHEAD = "0"
    
    # 根据高级设置构建参数
    $workersArg = if ($options.Advanced.WorkersMode -eq "auto") { "auto" } else { $options.Advanced.WorkersValue }
    $skipNonDialogArg = if ($options.Advanced.SkipNonDialog) { "--skip-non-dialog" } else { "--no-skip-non-dialog" }
    
    # 构建翻译命令
    $translateArgs = @(
        "$outputRoot/llm_batches",
        "-o", "$outputRoot/llm_results",
        "--model", $model,
        "--workers", $workersArg,
        "--timeout", "180",
        $skipNonDialogArg,
        "--flush-interval", $options.Advanced.FlushInterval
    )
    
    # 如果启用优化模式，添加相应参数
    if ($options.Advanced.UseOptimized) {
        $translateArgs += "--use-optimized"
        $translateArgs += "--quality-threshold"
        $translateArgs += $options.Advanced.QualityThreshold
    }
    
    python tools/translate.py @translateArgs
    
    if ($LASTEXITCODE -ne 0) { 
        [System.Windows.Forms.MessageBox]::Show("AI 翻译失败", "错误", "OK", "Error")
        exit 1 
    }
    Write-Host ""
    
    Write-Host "▶ 步骤 5/7: 合并翻译结果" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    
    python tools/merge.py `
        "$prefilledJsonl" `
        "$outputRoot/llm_results" `
        -o "$outputRoot/final/translated.jsonl" `
        --conflict-tsv "$outputRoot/qa/llm_conflicts.tsv"
    
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host ""
} else {
    Write-Host "⊘ 跳过步骤 3-5: LLM 翻译" -ForegroundColor Yellow
    Copy-Item "$prefilledJsonl" "$outputRoot/final/translated.jsonl"
}

$translatedJsonl = "$outputRoot/final/translated.jsonl"

# ========== 步骤 6: 质量检查 ==========
Write-Host "▶ 步骤 6/7: 翻译质量检查" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

python tools/validate.py `
    "$extractedJsonl" `
    "$translatedJsonl" `
    --qa-json "$outputRoot/qa/qa.json" `
    --qa-tsv "$outputRoot/qa/qa.tsv" `
    --qa-html "$outputRoot/qa/qa.html" `
    --ignore-ui-punct `
    --require-ph-count-eq `
    --require-newline-eq

if ($LASTEXITCODE -ne 0) { 
    Write-Warning "质量检查发现问题,请查看报告: $outputRoot/qa/qa.html"
}
Write-Host ""

# ========== 步骤 7: 回填并构建 ==========
if (-not $options.SkipBuild) {
    Write-Host "▶ 步骤 7a/7: 回填翻译到游戏文件" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    
    $patchWorkers = if ($options.Advanced.WorkersMode -eq "auto") { 4 } else { $options.Advanced.WorkersValue }
    
    python tools/patch.py `
        "$gamePath" `
        "$translatedJsonl" `
        -o "$outputRoot/patched" `
        --advanced `
        --workers $patchWorkers
    
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host ""
    
    Write-Host "▶ 步骤 7b/7: 构建中文游戏包" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    
    python tools/build.py `
        "$gamePath" `
        -o "$outputRoot/cn_build" `
        --mode mirror `
        --zh-mirror "$outputRoot/patched" `
        --lang zh_CN
    
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host ""
    
    # 步骤 7c: 替换中文字体
    Write-Host "▶ 步骤 7c/7: 替换游戏字体为中文字体" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    
    # 检查字体文件是否存在
    $fontDir = "data/fonts"
    $font1 = Join-Path $fontDir "NotoSansSC.ttf"
    $font2 = Join-Path $fontDir "NotoSansSCBold.ttf"
    
    if ((Test-Path $font1) -and (Test-Path $font2)) {
        python tools/replace_fonts.py `
            "$gamePath" `
            --backup
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ 字体替换完成" -ForegroundColor Green
        } else {
            Write-Warning "字体替换失败，但不影响汉化结果"
        }
    } else {
        Write-Host "  ⊘ 跳过字体替换（请将字体文件放到 data/fonts/ 目录）" -ForegroundColor Yellow
        Write-Host "    需要: NotoSansSC.ttf 和 NotoSansSCBold.ttf" -ForegroundColor Gray
    }
    Write-Host ""
} else {
    Write-Host "⊘ 跳过步骤 7: 回填和构建" -ForegroundColor Yellow
}

# ========== 完成 ==========
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "                  ✓ 汉化流水线完成!                    " -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# 统计信息
if (Test-Path $translatedJsonl) {
    $totalLines = (Get-Content $translatedJsonl).Count
    $translatedCount = 0
    foreach ($line in Get-Content $translatedJsonl) {
        $obj = $line | ConvertFrom-Json
        if ($obj.zh -and $obj.zh -ne "") {
            $translatedCount++
        }
    }
    $percentage = [math]::Round(($translatedCount / $totalLines) * 100, 2)
    
    Write-Host "📊 翻译统计:" -ForegroundColor Cyan
    Write-Host "   总文本数: $totalLines" -ForegroundColor White
    Write-Host "   已翻译数: $translatedCount" -ForegroundColor White
    Write-Host "   完成度: $percentage%" -ForegroundColor White
    Write-Host ""
}

Write-Host "📁 输出位置:" -ForegroundColor Cyan
Write-Host "   翻译文件: $translatedJsonl"
Write-Host "   QA 报告: $outputRoot/qa/qa.html"
if (-not $options.SkipBuild) {
    Write-Host "   中文游戏: $outputRoot/cn_build/"
}
if ($options.AutoDict) {
    Write-Host "   生成字典: data/dictionaries/auto/"
}
Write-Host ""

# 询问是否打开 QA 报告
$openQA = [System.Windows.Forms.MessageBox]::Show(
    "汉化完成！是否打开质量检查报告？",
    "完成",
    "YesNo",
    "Information"
)

if ($openQA -eq [System.Windows.Forms.DialogResult]::Yes) {
    Start-Process "$outputRoot/qa/qa.html"
}

Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
