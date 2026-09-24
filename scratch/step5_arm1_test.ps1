$ErrorActionPreference = "Continue"

Write-Host "=== STEP 5: ARM 1 TEST (NO SLEEP / IMMEDIATE RETRY) ==="

$env:DATABASE_URL = "postgresql+asyncpg://postgres:relay@localhost:5433/relay_w5d1"

$stdoutLog = "logs\w5d1_step5_arm1_worker.stdout.log"
$stderrLog = "logs\w5d1_step5_arm1_worker.stderr.log"

if (Test-Path $stdoutLog) { Remove-Item $stdoutLog -Force }
if (Test-Path $stderrLog) { Remove-Item $stderrLog -Force }

Write-Host "1. Launching worker with Arm 1 (no sleep on failure)..."
$workerProc = Start-Process -FilePath ".\.venv\Scripts\python.exe" `
    -ArgumentList "-u", "-m", "src.worker" `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru

Write-Host "Worker PID: $($workerProc.Id). Waiting 5s for warmup & idle polling..."
Start-Sleep -Seconds 5

$tStop = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss.fff")
Write-Host "2. Stopping Postgres at $tStop (UTC)..."
docker compose stop db | Out-Null

Write-Host "3. Outage active. Waiting 25 seconds..."
Start-Sleep -Seconds 25

$tStart = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss.fff")
Write-Host "4. Starting Postgres at $tStart (UTC)..."
docker compose start db | Out-Null

Write-Host "5. Waiting 10s for recovery and post-recovery polling..."
Start-Sleep -Seconds 10

$isAlive = Get-Process -Id $workerProc.Id -ErrorAction SilentlyContinue
if ($isAlive) {
    Write-Host "WORKER_STATUS: ALIVE (PID: $($workerProc.Id))"
} else {
    Write-Host "WORKER_STATUS: DEAD"
}

Write-Host "6. Stopping worker process..."
if ($isAlive) {
    Stop-Process -Id $workerProc.Id -Force -ErrorAction SilentlyContinue
}

Write-Host "`n=== ARM 1 MEASUREMENT RESULTS ==="
Write-Host "T_STOP_UTC  : $tStop"
Write-Host "T_START_UTC : $tStart"

$pollFailures = 0
if (Test-Path $stdoutLog) {
    $pollFailures = (Get-Content $stdoutLog | Select-String -Pattern "\[poll_error\]").Count
    $fileSize = (Get-Item $stdoutLog).Length
    Write-Host "poll_failures count : $pollFailures"
    Write-Host "stdout log size     : $fileSize bytes"
}

$stderrSize = 0
if (Test-Path $stderrLog) {
    $stderrSize = (Get-Item $stderrLog).Length
    Write-Host "stderr log size     : $stderrSize bytes"
}
