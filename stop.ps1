Write-Host "Stopping FAOS TradingAgents..." -ForegroundColor Cyan

$pidFile = ".faos.pids"

if (Test-Path $pidFile) {
    $pids = Get-Content $pidFile | ConvertFrom-Json
    
    if ($pids.BackendPID) {
        Write-Host "Stopping Backend (PID: $($pids.BackendPID))..." -ForegroundColor Yellow
        Stop-Process -Id $pids.BackendPID -Force -ErrorAction SilentlyContinue
    }
    
    if ($pids.FrontendPID) {
        Write-Host "Stopping Frontend (PID: $($pids.FrontendPID))..." -ForegroundColor Yellow
        Stop-Process -Id $pids.FrontendPID -Force -ErrorAction SilentlyContinue
    }
    
    Remove-Item $pidFile -Force
    Write-Host "Services stopped from tracked PIDs." -ForegroundColor Green
} else {
    Write-Host "No .faos.pids file found. Attempting to kill processes by port..." -ForegroundColor Yellow
}

# Fallback: Kill anything running on our ports
function Kill-Port {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        Write-Host "Killing process $($conn.OwningProcess) listening on port $Port..." -ForegroundColor Red
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Kill-Port -Port 8001
Kill-Port -Port 5173

Write-Host "All FAOS services stopped successfully." -ForegroundColor Green
