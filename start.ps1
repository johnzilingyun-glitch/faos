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
$env:PYTHONPATH="." # Ensure local imports work before starting process
$backendProcess = Start-Process -FilePath "uvicorn" -ArgumentList "faos.api.server:app", "--port", "$backendPort", "--host", "0.0.0.0" -PassThru -NoNewWindow

# Start Frontend
Write-Host "Starting Vite Frontend on port $frontendPort..." -ForegroundColor Green
Set-Location -Path ".\frontend"
$frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -PassThru -NoNewWindow
Set-Location -Path ".."

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Services Started Successfully!" -ForegroundColor Green
Write-Host "Backend API: http://localhost:$backendPort"
Write-Host "Frontend UI: http://localhost:$frontendPort"
Write-Host "To shut down the servers, run .\stop.ps1" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Cyan

# Save process IDs to a file so stop.ps1 can kill them safely
$pids = @{
    BackendPID = $backendProcess.Id
    FrontendPID = $frontendProcess.Id
}
$pids | ConvertTo-Json | Out-File -FilePath ".faos.pids"
