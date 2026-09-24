$ErrorActionPreference = "Continue"

Write-Host "=== STEP 6: TERMINAL-MARK OUTAGE EXPERIMENT ==="

$env:DATABASE_URL = "postgresql+asyncpg://postgres:relay@localhost:5433/relay_w5d1"

$stdoutLog = "logs\w5d1_step6_worker.stdout.log"
$stderrLog = "logs\w5d1_step6_worker.stderr.log"

if (Test-Path $stdoutLog) { Remove-Item $stdoutLog -Force }
if (Test-Path $stderrLog) { Remove-Item $stderrLog -Force }

# 1. Ensure an effect job is present in relay_w5d1
Write-Host "1. Checking/seeding effect job in relay_w5d1..."
$pendingCount = (docker compose exec db psql -U postgres -d relay_w5d1 -At -c "SELECT count(*) FROM jobs WHERE status = 'pending';").Trim()
if ([int]$pendingCount -eq 0) {
    .\.venv\Scripts\python.exe .\scratch\seed_step6.py | Out-Null
}

# 2. Launch worker
Write-Host "2. Launching worker..."
$workerProc = Start-Process -FilePath ".\.venv\Scripts\python.exe" `
    -ArgumentList "-u", "-m", "src.worker" `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru

Write-Host "Worker PID: $($workerProc.Id). Waiting 2.5s for job claim & side-effect commit..."
Start-Sleep -Seconds 2.5

# 3. Stop Postgres while handler is sleeping (post-commit, pre-mark)
$tStop = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss.fff")
Write-Host "3. Stopping Postgres at $tStop (UTC) while handler is in-flight..."
docker compose stop db | Out-Null

Write-Host "4. Waiting 8s for handler sleep to finish and mark attempt while DB is down..."
Start-Sleep -Seconds 8

# 5. Check if worker is alive or dead
$isAlive = Get-Process -Id $workerProc.Id -ErrorAction SilentlyContinue
if ($isAlive) {
    Write-Host "WORKER_STATUS_PRE_RESTART: ALIVE (PID: $($workerProc.Id))"
} else {
    Write-Host "WORKER_STATUS_PRE_RESTART: DEAD"
}

# 6. Start Postgres back up
$tStart = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss.fff")
Write-Host "5. Starting Postgres at $tStart (UTC)..."
docker compose start db | Out-Null
Start-Sleep -Seconds 4

# 7. Query DB state
Write-Host "`n=== STEP 6 DB STATE OBSERVATIONS ==="
Write-Host "--- jobs table ---"
docker compose exec db psql -U postgres -d relay_w5d1 -c "SELECT id, type, status, attempts, claim_generation, claimed_at FROM jobs;"

Write-Host "--- side_effects table ---"
docker compose exec db psql -U postgres -d relay_w5d1 -c "SELECT id, effect_key, job_id, worker_id, created_at FROM side_effects;"

Write-Host "--- outbox table ---"
docker compose exec db psql -U postgres -d relay_w5d1 -c "SELECT id, effect_key, job_id, created_at FROM outbox;"

# 8. Check worker logs
Write-Host "`n=== WORKER LOG SUMMARY ==="
if (Test-Path $stderrLog) {
    $stderrSize = (Get-Item $stderrLog).Length
    Write-Host "stderr size: $stderrSize bytes"
    if ($stderrSize -gt 0) {
        Write-Host "Traceback tail:"
        Get-Content $stderrLog -Tail 15
    }
}

# Clean up worker process if still alive
if ($isAlive) {
    Stop-Process -Id $workerProc.Id -Force -ErrorAction SilentlyContinue
}
