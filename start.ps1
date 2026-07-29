$ErrorActionPreference = "Stop"

Write-Host "Starting FAOS TradingAgents..." -ForegroundColor Cyan

# Check if ports are already in use
$backendPort = 8088
$frontendPort = 3000

$backendInUse = Get-NetTCPConnection -LocalPort $backendPort -ErrorAction SilentlyContinue
if ($backendInUse) {
    Write-Host "Warning: Port $backendPort is already in use. You may need to run stop.ps1 first." -ForegroundColor Yellow
}

# Start Backend
Write-Host "Starting FastAPI Backend on port $backendPort..." -ForegroundColor Green
$pythonCmd = if (Test-Path ".\venv\Scripts\python.exe") { ".\venv\Scripts\python.exe" } else { "python" }
$backendInfo = New-Object System.Diagnostics.ProcessStartInfo
$backendInfo.FileName = "powershell.exe"
$backendInfo.Arguments = "-NoExit -Command Set-Location '$PSScriptRoot'; `$env:PYTHONPATH='.'; & '$pythonCmd' -m uvicorn faos.api.server:app --port $backendPort --host 127.0.0.1 --reload"
$backendInfo.UseShellExecute = $true
$backendProcess = [System.Diagnostics.Process]::Start($backendInfo)

# Start Frontend
Write-Host "Starting Vite Frontend on port $frontendPort..." -ForegroundColor Green
$frontendInfo = New-Object System.Diagnostics.ProcessStartInfo
$frontendInfo.FileName = "powershell.exe"
$frontendInfo.Arguments = "-NoExit -Command Set-Location '$PSScriptRoot\frontend'; npm run dev"
$frontendInfo.UseShellExecute = $true
$frontendProcess = [System.Diagnostics.Process]::Start($frontendInfo)

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Services Started Successfully!" -ForegroundColor Green
Write-Host "Backend API: http://127.0.0.1:$backendPort"
Write-Host "Frontend UI: http://localhost:$frontendPort"
Write-Host "To shut down the servers, run .\stop.ps1" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Cyan

# Save process IDs to a file so stop.ps1 can kill them safely
$pids = @{
    BackendPID = $backendProcess.Id
    FrontendPID = $frontendProcess.Id
}
$pids | ConvertTo-Json | Out-File -FilePath ".faos.pids" -Encoding utf8
