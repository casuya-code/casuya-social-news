# Casuya Social News — launch server + operator + main client
# Run from PowerShell: .\tools\launch_demo.ps1

$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root "server-python\.venv\Scripts\python.exe"
$godot = Join-Path $root "client-godot\.godot-bin\Godot_v4.7.1-stable_win64_console.exe"
$client = Join-Path $root "client-godot"

# --- Kill any existing server on port 8000 ---
$existing = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($existing) { Stop-Process -Id $existing.OwningProcess -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2 }

# --- Start the server (reads .env for API keys) ---
Write-Host "Starting server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
$env:SCHEDULER_ENABLED = "true"
Start-Process -FilePath $py -ArgumentList "-m","uvicorn","main:app","--host","127.0.0.1","--port","8000" `
    -WorkingDirectory (Join-Path $root "server-python")

# Wait for server to be ready
Start-Sleep -Seconds 8
try {
    $health = curl.exe -s -m 10 "http://127.0.0.1:8000/api/v1/health" | ConvertFrom-Json
    Write-Host "Server UP — status: $($health.status)" -ForegroundColor Green
    Write-Host "Scheduler: $($health.scheduler.running) | Stories: $($health.scheduler.stories_generated)" -ForegroundColor DarkGray
} catch {
    Write-Host "Server may still be starting..." -ForegroundColor Yellow
}

# --- Open the main client (character drama) ---
Write-Host "`nOpening main client..." -ForegroundColor Cyan
Start-Process $godot -ArgumentList "--editor","--path","$client","--scene","res://scenes/main.tscn"

Write-Host "`n=== Casuya Social News ===" -ForegroundColor Yellow
Write-Host "Server:    http://127.0.0.1:8000"
Write-Host "Main:      client-godot/scenes/main.tscn"
Write-Host "Operator:  Click 'Msimamizi' button in main scene"
Write-Host "Scheduler: Fetches news + weather every 5 minutes"
Write-Host "==========================" -ForegroundColor Yellow
