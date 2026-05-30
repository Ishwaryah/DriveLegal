# DriveLegal — Start Backend and Expo for access ANYWHERE
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== DriveLegal remote startup ===" -ForegroundColor Cyan

# 1. Check Ollama
Write-Host "Checking Ollama..." -ForegroundColor Cyan
try {
    $null = ollama list 2>$null
    Write-Host "[OK] Ollama is available" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Ollama is not running! The AI will use 'Keyword Fallback' or Gemini instead." -ForegroundColor Yellow
    Write-Host "       To use Local AI, please open the Ollama app on your PC first." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}

# 2. Start Backend API
$on8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($on8000) {
    Write-Host "Stopping previous process on port 8000 ..." -ForegroundColor Yellow
    $on8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
}

Write-Host "Starting local backend on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @("-NoExit", "-Command", "Set-Location '$Root'; .\.venv\Scripts\python.exe backend\main.py")
Start-Sleep -Seconds 5

# 3. Start Cloudflare Tunnel for Backend (replaces broken localtunnel/ngrok)
Write-Host "Starting Cloudflare Tunnel for the backend API..." -ForegroundColor Cyan
Stop-Process -Name "cloudflared" -Force -ErrorAction SilentlyContinue
$tunnelLog = Join-Path $Root "cloudflare-tunnel.log"
if (Test-Path $tunnelLog) { Remove-Item $tunnelLog -Force -ErrorAction SilentlyContinue }

# Run cloudflared in the background, redirect stderr (where it logs) to the log file
Start-Process powershell -ArgumentList @("-WindowStyle", "Hidden", "-Command", "npx -y cloudflared tunnel --url http://127.0.0.1:8000 2>&1 | Tee-Object -FilePath '$tunnelLog'")

Write-Host "Waiting for Cloudflare tunnel to initialize (this may take ~15s on first run)..." -ForegroundColor Yellow
$tunnelUrl = ""
$attempts = 0
while (-not $tunnelUrl -and $attempts -lt 60) {
    Start-Sleep -Seconds 2
    $attempts++
    if (Test-Path $tunnelLog) {
        $content = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
        if ($content -and $content -match "(https://[a-z0-9\-]+\.trycloudflare\.com)") {
            $tunnelUrl = $matches[1]
        }
    }
}

if (-not $tunnelUrl) {
    Write-Host "[ERROR] Could not start Cloudflare tunnel after 120 seconds." -ForegroundColor Red
    Write-Host "Falling back to local Wi-Fi only mode..." -ForegroundColor Yellow
    $LAN_IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" } | Select-Object -First 1).IPAddress
    $tunnelUrl = "http://${LAN_IP}:8000"
}

Write-Host "[OK] Backend exposed at: $tunnelUrl" -ForegroundColor Green

# 4. Update mobile/.env
$mobileEnv = Join-Path $Root "mobile\.env"
if (Test-Path $mobileEnv) {
    $envContent = (Get-Content $mobileEnv) | Where-Object { $_ -notmatch "^EXPO_PUBLIC_API_URL" -and $_ -notmatch "^EXPO_PUBLIC_API_HOST" -and $_.Trim() -ne "" }
    if ($envContent) {
        $envContent | Set-Content $mobileEnv
    } else {
        "" | Set-Content $mobileEnv
    }
} else {
    New-Item -ItemType File -Path $mobileEnv -Force | Out-Null
}
Add-Content $mobileEnv "EXPO_PUBLIC_API_URL=$tunnelUrl"
Write-Host "[OK] Updated mobile/.env with tunnel URL" -ForegroundColor Green

# 5. Start Expo (Tunnel mode via ngrok — works on mobile data)
Write-Host "Starting Expo with Tunneling..." -ForegroundColor Cyan

Start-Process powershell -ArgumentList @("-NoExit", "-Command", "Set-Location '$Root\mobile'; npx.cmd expo start --tunnel -c")

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Everything is running!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API tunnel: $tunnelUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "SETUP:"
Write-Host "  1. Scan the QR code in the Expo terminal with your phone."
Write-Host "  2. The app and the backend API are BOTH tunneled."
Write-Host "  3. You can use Mobile Data (4G/5G) or any Wi-Fi network!"
Write-Host ""
Write-Host "NOTE: Both the App JS bundle (ngrok) and API (Cloudflare) are fully remote!" -ForegroundColor Green
