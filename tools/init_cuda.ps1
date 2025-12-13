$ErrorActionPreference = 'SilentlyContinue'

Write-Host 'Initializing CUDA environment...' -ForegroundColor Cyan

$hasGPU = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if (-not $hasGPU) {
    Write-Host 'No NVIDIA GPU detected' -ForegroundColor Yellow
    return
}

try {
    $gpuInfo = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    Write-Host "GPU detected: $gpuInfo" -ForegroundColor Green
} catch {
    Write-Host 'Cannot read GPU info' -ForegroundColor Yellow
}

$cudaCmd = Get-Command ecuda -ErrorAction SilentlyContinue
if ($cudaCmd) {
    try {
        Write-Host '  Loading CUDA toolkit...' -ForegroundColor Gray
        ecuda | Out-Null
        if ($env:CUDA_PATH) {
            Write-Host '  CUDA environment loaded successfully' -ForegroundColor Green
        } else {
            Write-Host '  CUDA_PATH not set' -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  CUDA initialization error: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host '  ecuda command not found' -ForegroundColor Yellow
    Write-Host '  Ollama will try to use GPU automatically' -ForegroundColor Gray
}

Write-Host ''
