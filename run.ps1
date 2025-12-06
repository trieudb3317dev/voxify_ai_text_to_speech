# PowerShell script để chạy pipeline recipe chatbot
# Usage: .\run.ps1 [-Source recipes.json] [-SkipPrepare] [-SkipEmbed] [-Port 8000]

param(
    [string]$Source = "recipes.json",
    [switch]$SkipPrepare,
    [switch]$SkipEmbed,
    [int]$Port = 8000,
    [string]$Host = "0.0.0.0",
    [switch]$Reload
)

# Set execution policy cho session này
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

$ErrorActionPreference = "Stop"

# Kiểm tra venv
$venvPython = ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = ".venv\bin\python"
    if (-not (Test-Path $venvPython)) {
        Write-Host "⚠️  Không tìm thấy .venv, sử dụng Python hệ thống" -ForegroundColor Yellow
        $venvPython = "python"
    }
} else {
    Write-Host "✅ Sử dụng Python từ venv: $venvPython" -ForegroundColor Green
}

# Bước 1: Prepare recipes
if (-not $SkipPrepare) {
    if (-not $Source.StartsWith("api://") -and -not (Test-Path $Source)) {
        Write-Host "⚠️  File $Source không tồn tại, bỏ qua bước prepare" -ForegroundColor Yellow
        $SkipPrepare = $true
    }
}

if (-not $SkipPrepare) {
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "📋 Bước 1: Chuẩn hóa recipes thành docs.jsonl" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "🔧 Command: $venvPython prepare_recipes.py --source $Source --out docs.jsonl`n" -ForegroundColor Gray
    
    & $venvPython prepare_recipes.py --source $Source --out docs.jsonl
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ Lỗi khi chạy prepare_recipes.py" -ForegroundColor Red
        exit 1
    }
    Write-Host "`n✅ Hoàn thành: Chuẩn hóa recipes" -ForegroundColor Green
} else {
    Write-Host "`n⏭️  Bỏ qua bước prepare" -ForegroundColor Yellow
}

# Bước 2: Embed và tạo index
if (-not $SkipEmbed) {
    if (-not (Test-Path "docs.jsonl")) {
        Write-Host "`n❌ File docs.jsonl không tồn tại. Chạy prepare trước!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "📋 Bước 2: Tạo embeddings và index" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "🔧 Command: $venvPython embed_and_index.py --docs docs.jsonl --index out.index --meta meta.json`n" -ForegroundColor Gray
    
    & $venvPython embed_and_index.py --docs docs.jsonl --index out.index --meta meta.json
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ Lỗi khi chạy embed_and_index.py" -ForegroundColor Red
        exit 1
    }
    Write-Host "`n✅ Hoàn thành: Tạo embeddings và index" -ForegroundColor Green
} else {
    Write-Host "`n⏭️  Bỏ qua bước embed" -ForegroundColor Yellow
}

# Bước 3: Chạy API server
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "🚀 Bước 3: Khởi động API server" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$uvicornArgs = @(
    "-m", "uvicorn",
    "serve_vector:app",
    "--host", $Host,
    "--port", $Port.ToString()
)
if ($Reload) {
    $uvicornArgs += "--reload"
}

Write-Host "🔧 Command: $venvPython $($uvicornArgs -join ' ')" -ForegroundColor Gray
Write-Host "`n📡 API sẽ chạy tại: http://$Host`:$Port" -ForegroundColor Green
Write-Host "📚 API docs: http://$Host`:$Port/docs" -ForegroundColor Green
Write-Host "`n⚠️  Nhấn Ctrl+C để dừng server`n" -ForegroundColor Yellow

try {
    & $venvPython $uvicornArgs
} catch {
    Write-Host "`n👋 Đã dừng server" -ForegroundColor Yellow
}

