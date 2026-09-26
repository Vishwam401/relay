# Week 3 Din 3 BRIEF — crash effect ke beech me

**Aaj mitigation build nahi hoti. Aaj three durable boundaries ko real process death se separate karke read kiya jaata hai.**

Seal rule: prediction pehle `DIN_03_ANSWERS.md` me; experiment; output ke against apni explanation; tab corresponding KEY section. `idk` valid hai. Step 0 me immutable working copy `DIN_03_PREDICTIONS_FROZEN.md` banti hai—ye provenance stronger karti hai, tamper-proof nahi.

Current bench `[MEASURED-R 2026-09-01]`: `111` jobs, `100` executions, `5` effects, max/sequence `112`, Alembic `dbe13b69056d`, zero Relay Python processes, zero idle transactions.

---

# Part A — Steps

## Step 0 — 10 min: predictions freeze + bench

**Terms used in this step**
- **Commit boundary:** instant jiske baad write process death ke baad durable hai.
- **Pre-reaper snapshot:** crash ke baad, recovery writer se pehle ki state; baad me recreate nahi hoti.
- **Frozen copy:** predictions ka never-edit snapshot; hash accidental edits detect karta hai, authorship prove nahi.

1. Part B ke exact six questions `DIN_03_ANSWERS.md` me answer karo; har question ke neeche empty Observed/After KEY blocks rakho.
2. Us file ko `DIN_03_PREDICTIONS_FROZEN.md` me copy karo, SHA-256 output WEEK_03 log me paste karo, frozen copy phir edit mat karo.
3. Opening DB/process checks run karo. Mismatch ho to stop—Din 2 evidence silently repair mat karo.
4. IDs guess/reserve mat karo. Har successful `RETURNING id` ko named PowerShell variable aur log me record karo.

**Executable end:** frozen copy + hash + opening output; no process, no DB delta.

## Step 1 — 15 min: temporary fault vocabulary, exact source boundaries

**Terms used in this step**
- **`os._exit(86)`:** immediate process termination; `except`, `finally`, graceful shutdown bypass.
- **Fault hook:** measurement-only exact-value branch.
- **Transaction context:** `async with session.begin()`; normal context exit ke baad commit complete.

Temporary `payload["crash_at"]` vocabulary add karo—new handler nahi:

- `before_effect_commit`: effect transaction/insert start hone se pehle.
- `after_effect_commit`: effect transaction context exit ke baad, handler return/mark se pehle.
- `after_mark_commit`: mark transaction context exit ke baad.

Requirements:
- exact equality only; missing/unknown value no-op;
- first two hooks `handle_effect` ke andar;
- post-mark hook additionally `job_type == "effect"` guard kare;
- exit se pehle worker id, job id, boundary print with flush;
- mark-block ke andar ka print commit proof nahi.

`py_compile` run karo. `git diff HEAD -- src/worker.py` verbatim log me copy karo **before** first crash, so reverted hook placement reviewer-readable rahe.

**Executable end:** compile pass, focused diff preserved, no DB delta.

## Step 2 — 15 min: crash **before effect commit**

**Terms used in this step**
- **Dispatch evidence:** `job_executions` row; completion proof nahi.
- **Lease ageing:** snapshot ke baad `claimed_at` ko past me move karke deterministic reclaim.
- **Recovery dispatch:** reaper ke baad next legal claim/execution.

1. Reaper off. Fresh effect job with `before_effect_commit`; returned id ko `$beforeId` me capture karo.
2. One worker run; hook line and native exit code `86` record karo.
3. Pre-reaper snapshot: job row, execution count, effect rows.
4. Marker remove + `claimed_at=now()-31s`; reaper ko one reclaim tak run karke stop karo.
5. One worker recovery complete hone do, success line ke baad gracefully stop karo.
6. Post-recovery snapshot.

**Executable end:** first dispatch effect se pehle died; second dispatch effect once + terminal mark.

**KEY:** sirf **“Open after Step 2”** section ab kholo.

## Step 3 — 15 min: crash **after effect commit, before mark** — centrepiece

**Terms used in this step**
- **Durable orphan effect:** effect committed, job still `running`.
- **Dedup verdict:** second insert `rowcount=0`; count `1` alone enough nahi.
- **Recovery-relevant projection:** `status`, `attempts`, lease presence, execution count—synthetic payload/id/timestamps excluded.

1. Reaper off. Fresh job with `after_effect_commit`; returned id `$middleId`.
2. Worker exits `86` only after effect COMMIT; pre-reaper snapshot.
3. Marker remove + age lease; reaper se exactly one reclaim, then stop.
4. Recovery worker. Required evidence: executions `1→2`, replay `rowcount=0`, effects `1→1`, final success.

**Executable end:** actual redispatch hua aur database arbiter ne second ledger insert suppress kiya.

**KEY:** ab **Q1, Q2, Q4** section kholo.

## Step 4 — 15 min: crash **after committed mark** — control

**Terms used in this step**
- **Terminal state:** claim/reaper predicates se unreachable `succeeded` row.
- **Negative recovery:** live observers ke bawajood no reclaim/dispatch.
- **Liveness evidence:** startup PID + process present + repeated poll/pass output; silence proof nahi.

1. Reaper off. Fresh job with `after_mark_commit`; returned id `$afterId`.
2. Worker output order: mark UPDATE, COMMIT, hook line, exit `86`. DB must already show success/effect/execution.
3. Marker remove.
4. Reaper `>=6s`: startup/PID + at least three idle-pass lines preserve; process list while live; stop.
5. Worker `>=6s`: startup/PID + repeated pending polls preserve; process list while live; stop.
6. Counts unchanged and no target-id reclaim/claim line.

**Executable end:** terminal commit survived death; proven-live recovery components ignored it.

**KEY:** ab **Q5, Q6** section kholo.

## Step 5 — 10 min: compare states + outbox decision

**Terms used in this step**
- **Atomic local write:** one Postgres transaction me all-or-nothing writes.
- **External side effect:** email/HTTP/payment, Postgres rollback se undo nahi hota.
- **Transactional outbox:** business state + delivery intent one DB transaction; dispatcher later delivers.

Write in your own words:

1. Before/middle jobs ka **recovery-relevant projection** same tha ya nahi? IDs, timestamps, and different synthetic `crash_at` payloads “identical” claim ka part nahi.
2. Local ledger insert + job mark ko one transaction me merge karne ka real cost: handler/worker transaction ownership coupling; current ordering preserve karoge to transaction handler work ke across long ho sakti hai; and mark `rowcount=0` must force rollback or effect can still commit alone. `job_executions` (`D-21`) independently committed reh sakti hai—D-21 merge ke against reason nahi.
3. External effect same transaction me kyu nahi aa sakta? Outbox local state+intent atomic banata hai, remote execution exactly-once nahi; receiver idempotency remains.

No outbox table/dispatcher/external sink today.

**Executable end:** D-24 ke future Cost ke liye measured seam + written trade-off.

**KEY:** ab **Q3** section kholo.

## Step 6 — 10 min: revert, reconcile, cleanup

**Terms used in this step**
- **HEAD-relative diff:** staged aur unstaged dono changes detect karne ke liye comparison against commit.
- **Named reconciliation:** returned IDs explain deltas; contiguous sequence assumption nahi.
- **Residual process:** terminal wrapper band hone ke baad child interpreter still alive ho sakta hai.

1. Three hooks revert; normal Din 2 worker restore.
2. Expected clean delta: `+3 jobs`, `+5 executions`, `+3 effects`; attempts by named job `2/2/1`.
3. Named IDs pe `payload ? 'crash_at' = false`; zero pending/running.
4. Date-group + named-ID reconciliation; max/sequence observe karo, grade mat karo.
5. `git diff HEAD`, cached diff/check, status, and source search prove no crash hook—even if staged.
6. Zero worker/reaper, zero idle transaction; temporary captures remove only after relevant lines log me copied.
7. WEEK_03 template fill; “What I Understood” apne words me.

**Executable end:** no instrumentation/process artifact; durable DB evidence remains.

---

# Part B — Prediction questions — Gemini ko paste mat karna

```text
Q1. Side effect commit ho gaya, mark se pehle worker mar gaya. jobs me row kis state me hai? Aur ye state
    Week 2 ke kis entry me already likhi hui hai?

Q2. Uss row ko reaper reclaim karega. Naya worker handler dobara chalayega—side effect count 1 rahega ya
    2 hoga? Tumhara jawab Din 2 key ke scope par depend karta hai; dependency likho.

Q3. Side effect aur mark ek hi transaction me hote to middle crash state exist nahi karti. To wo ek
    transaction me kyu nahi hain? Do reasons aur ek external side effect likho.

Q4. Recovery ke baad count 1 do wajah se aa sakta hai—dedup, ya handler dobara chala hi nahi. Kaunsa ek
    number in dono ko separate karta hai?

Q5. os._exit() aur raise—dono ko “worker mar gaya” kehna kyu galat hai? Handler-level aur post-mark
    placement ko separately reason karo.

Q6. Teen crash cases ke final attempts kya honge, aur D-23 increment-on-claim se kaise derive hote hain?
```

---

# Part C — Verification — exact commands and expected output

Long-running commands separate PowerShell terminals me. Every native command ke baad exit code record karo. SQL blocks always `-X -v ON_ERROR_STOP=1`.

## C0 — opening + frozen provenance

```powershell
Copy-Item docs\daily\week_03\DIN_03_ANSWERS.md docs\daily\week_03\DIN_03_PREDICTIONS_FROZEN.md
Get-FileHash docs\daily\week_03\DIN_03_PREDICTIONS_FROZEN.md -Algorithm SHA256

$q = @"
select status,count(*) from jobs group by status order by status;
select count(*) as jobs,max(id) as max_id from jobs;
select last_value from jobs_id_seq;
select count(*) as executions from job_executions;
select count(*) as effects from side_effects;
select version_num from alembic_version;
select count(*) as idle_in_transaction from pg_stat_activity where datname='relay' and state='idle in transaction';
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "opening SQL failed: $LASTEXITCODE" }

$relay = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'src\.(worker|reaper)' })
"relay_processes=$($relay.Count)"
$relay | Select-Object ProcessId,CommandLine
```

Expected: `93 succeeded / 15 failed / 3 dead_letter`; jobs `111`, max/seq `112`; executions `100`; effects `5`; revision `dbe13b69056d`; idle `0`; processes `0`.

## C1 — instrumentation inspection

```powershell
.\.venv\Scripts\python.exe -m py_compile src\worker.py
if ($LASTEXITCODE -ne 0) { throw "compile failed" }
$instrumentationDiff=@(git diff HEAD -- src\worker.py)
if ($LASTEXITCODE -ne 0) { throw "instrumentation diff failed" }
$instrumentationDiff
if ($instrumentationDiff.Count -eq 0) { throw "expected temporary worker instrumentation diff" }
Select-String -Path src\worker.py -Pattern 'crash_at|before_effect_commit|after_effect_commit|after_mark_commit'
$q='select count(*) from jobs; select count(*) from job_executions; select count(*) from side_effects;'
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "C1 SQL failed" }
```

Expected DB unchanged `111/100/5`. Preserve focused diff. Inspect exact-equality/no-op behavior and `job_type=='effect'` on post-mark hook.

## C2 — Case A: before effect

```powershell
$sql=@"
insert into jobs(type,payload) values
('effect','{"crash_at":"before_effect_commit"}'::jsonb)
returning id;
"@
$out=@($sql | docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw "case A insert failed" }
$idLines=@($out | ForEach-Object { "$($_)".Trim() } | Where-Object { $_ -match '^\d+$' })
if ($idLines.Count -ne 1) { throw "expected one returned id, got: $($out -join ' | ')" }
[long]$beforeId=$idLines[0]
"beforeId=$beforeId"
```

Crash-worker terminal:

```powershell
.\.venv\Scripts\python.exe -u -m src.worker
$beforeExit=$LASTEXITCODE
"before_worker_exit=$beforeExit"
if ($beforeExit -ne 86) { throw "expected 86" }
```

Snapshot:

```powershell
$q=@"
select id,status,attempts,claimed_at,payload from jobs where id=$beforeId;
select count(*) as executions from job_executions where job_id=$beforeId;
select id,effect_key,worker_id,created_at from side_effects where job_id=$beforeId;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "case A snapshot failed" }
```

Expected pre-reaper: `running`, attempts `1`, executions `1`, zero effect rows.

```powershell
$q=@"
update jobs set payload=payload-'crash_at', claimed_at=now()-interval '31 seconds'
where id=$beforeId and status='running'
returning id,status,attempts,claimed_at,payload;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "case A harness update failed" }
```

Reaper terminal—target line ke **baad SQLAlchemy `COMMIT`** dekho, then `Ctrl+C` once:

```powershell
.\.venv\Scripts\python.exe -u -m src.reaper
$beforeReaperExit=$LASTEXITCODE
"before_reaper_exit=$beforeReaperExit"
if ($beforeReaperExit -ne 0) { throw "case A reaper did not stop cleanly" }
```

Expected target line: `id=$beforeId ... matched=1 post_status=pending`, followed by `COMMIT`.

Recovery-worker terminal—`Marked job $beforeId as 'succeeded'` ke **baad `COMMIT`** dekho, then `Ctrl+C` once:

```powershell
.\.venv\Scripts\python.exe -u -m src.worker
$beforeRecoveryExit=$LASTEXITCODE
"before_recovery_exit=$beforeRecoveryExit"
if ($beforeRecoveryExit -ne 0) { throw "case A recovery worker did not stop cleanly" }
```

Expected recovery: effect insert `rowcount=1`, mark `rowcount=1`, then clean exit `0`.

```powershell
$q=@"
select id,status,attempts,payload ? 'crash_at' as has_hook from jobs where id=$beforeId;
select count(*) as executions from job_executions where job_id=$beforeId;
select count(*) as effects from side_effects where job_id=$beforeId;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "case A final failed" }
```

Expected: success, attempts `2`, hook false, executions `2`, effects `1`.

## C3 — Case B: after effect, before mark

```powershell
$sql=@"
insert into jobs(type,payload) values
('effect','{"crash_at":"after_effect_commit"}'::jsonb)
returning id;
"@
$out=@($sql | docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw "case B insert failed" }
$idLines=@($out | ForEach-Object { "$($_)".Trim() } | Where-Object { $_ -match '^\d+$' })
if ($idLines.Count -ne 1) { throw "expected one returned id, got: $($out -join ' | ')" }
[long]$middleId=$idLines[0]
"middleId=$middleId"
```

Crash-worker terminal:

```powershell
.\.venv\Scripts\python.exe -u -m src.worker
$middleExit=$LASTEXITCODE
"middle_worker_exit=$middleExit"
if ($middleExit -ne 86) { throw "expected 86" }
```

Required stdout order: effect `INSERT` → effect transaction `COMMIT` → hook line → exit `86`.

```powershell
$q=@"
select id,status,attempts,claimed_at,payload from jobs where id=$middleId;
select count(*) as executions from job_executions where job_id=$middleId;
select id,effect_key,worker_id,created_at from side_effects where job_id=$middleId;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "case B snapshot failed" }
```

Expected pre-reaper: `running`, attempts `1`, executions `1`, one effect with key `job:$middleId`.

```powershell
$q=@"
update jobs set payload=payload-'crash_at', claimed_at=now()-interval '31 seconds'
where id=$middleId and status='running'
returning id,status,attempts,claimed_at,payload;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "case B harness update failed" }
```

Reaper terminal—target line ke baad `COMMIT`, then `Ctrl+C`:

```powershell
.\.venv\Scripts\python.exe -u -m src.reaper
$middleReaperExit=$LASTEXITCODE
"middle_reaper_exit=$middleReaperExit"
if ($middleReaperExit -ne 0) { throw "case B reaper did not stop cleanly" }
```

Recovery-worker terminal—dedup line and successful mark ke baad `COMMIT`, then `Ctrl+C`:

```powershell
.\.venv\Scripts\python.exe -u -m src.worker
$middleRecoveryExit=$LASTEXITCODE
"middle_recovery_exit=$middleRecoveryExit"
if ($middleRecoveryExit -ne 0) { throw "case B recovery worker did not stop cleanly" }
```

Required stdout: `Side-effect deduped ... rowcount=0`, mark `rowcount=1`.

```powershell
$q=@"
select id,status,attempts,payload ? 'crash_at' as has_hook from jobs where id=$middleId;
select count(*) as executions from job_executions where job_id=$middleId;
select count(*) as effects from side_effects where job_id=$middleId;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "case B final failed" }
```

Expected: success, attempts `2`, hook false, executions **2**, effects **1**. Broken no-recovery gives executions `1`; broken dedup gives effects `2` or exception path.

## C4 — Case C: after committed mark

```powershell
$sql=@"
insert into jobs(type,payload) values
('effect','{"crash_at":"after_mark_commit"}'::jsonb)
returning id;
"@
$out=@($sql | docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw "case C insert failed" }
$idLines=@($out | ForEach-Object { "$($_)".Trim() } | Where-Object { $_ -match '^\d+$' })
if ($idLines.Count -ne 1) { throw "expected one returned id, got: $($out -join ' | ')" }
[long]$afterId=$idLines[0]
"afterId=$afterId"
```

Crash-worker terminal:

```powershell
.\.venv\Scripts\python.exe -u -m src.worker
$afterExit=$LASTEXITCODE
"after_worker_exit=$afterExit"
if ($afterExit -ne 86) { throw "expected 86" }
```

Required order: mark `UPDATE` → transaction `COMMIT` → post-mark hook → exit `86`.

```powershell
$q=@"
select id,status,attempts,claimed_at,payload from jobs where id=$afterId;
select count(*) as executions from job_executions where job_id=$afterId;
select count(*) as effects from side_effects where job_id=$afterId;
update jobs set payload=payload-'crash_at' where id=$afterId returning id,payload;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "case C snapshot/cleanup failed" }
```

Expected before control: success, attempts `1`, executions `1`, effects `1`.

Reaper terminal start karo; is terminal ko observer check complete hone tak live rakho:

```powershell
.\.venv\Scripts\python.exe -u -m src.reaper
$afterReaperExit=$LASTEXITCODE
"after_reaper_exit=$afterReaperExit"
if ($afterReaperExit -ne 0) { throw "case C control reaper did not stop cleanly" }
```

Separate observer terminal while reaper is live:

```powershell
Start-Sleep -Seconds 6
$reapers=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'src\.reaper' })
$reapers | Select-Object ProcessId,CommandLine
if ($reapers.Count -ne 1) { throw "expected exactly one live reaper, got $($reapers.Count)" }
```

Reaper terminal me startup PID + at least three `candidates=0 reclaimed=0` lines preserve karo; observer PID startup PID se match karo; then `Ctrl+C`. Target `$afterId` ke liye reclaim line nahi honi chahiye.

Worker terminal start karo; observer check complete hone tak live rakho:

```powershell
.\.venv\Scripts\python.exe -u -m src.worker
$afterControlWorkerExit=$LASTEXITCODE
"after_control_worker_exit=$afterControlWorkerExit"
if ($afterControlWorkerExit -ne 0) { throw "case C control worker did not stop cleanly" }
```

Separate observer terminal while worker is live:

```powershell
Start-Sleep -Seconds 6
$workers=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'src\.worker' })
$workers | Select-Object ProcessId,CommandLine
if ($workers.Count -ne 1) { throw "expected exactly one live worker, got $($workers.Count)" }
```

Worker startup PID + at least three idle claim-query passes preserve karo; observer PID startup PID se match karo; then `Ctrl+C`. Target `$afterId` ke liye claim line nahi honi chahiye.

```powershell
$q=@"
select id,status,attempts,payload ? 'crash_at' as has_hook from jobs where id=$afterId;
select count(*) as executions from job_executions where job_id=$afterId;
select count(*) as effects from side_effects where job_id=$afterId;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "case C final failed" }
```

Expected unchanged: success, attempts `1`, hook false, executions `1`, effects `1`. Silence alone does not pass; both live-process reads and repeated passes are required.

## C5 — named three-case differential

If a new terminal is used, restore variables from recorded `RETURNING` output:

```powershell
[long]$beforeId=<recorded-before-id>
[long]$middleId=<recorded-middle-id>
[long]$afterId=<recorded-after-id>
$q=@"
select j.id,j.status,j.attempts,j.payload ? 'crash_at' as has_hook,
       count(distinct e.id) as executions,count(distinct s.id) as effects
from jobs j
left join job_executions e on e.job_id=j.id
left join side_effects s on s.job_id=j.id
where j.id in ($beforeId,$middleId,$afterId)
group by j.id,j.status,j.attempts,j.payload
order by j.id;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "C5 failed" }
```

Expected by **role**, not contiguous id:

```text
before -> succeeded | attempts 2 | hook false | executions 2 | effects 1
middle -> succeeded | attempts 2 | hook false | executions 2 | effects 1
after  -> succeeded | attempts 1 | hook false | executions 1 | effects 1
```

## C6 — closing and artifact check

After hook revert:

```powershell
.\.venv\Scripts\python.exe -m py_compile src\worker.py
if ($LASTEXITCODE -ne 0) { throw "compile failed" }

git diff HEAD --check
if ($LASTEXITCODE -ne 0) { throw "git diff HEAD --check failed" }
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw "git diff --cached --check failed" }
$workerDiff=@(git diff HEAD -- src\worker.py)
if ($LASTEXITCODE -ne 0) { throw "worker diff command failed" }
$workerDiff
if ($workerDiff.Count -ne 0) { throw "src/worker.py differs from HEAD; hook revert incomplete" }
git status --short
if ($LASTEXITCODE -ne 0) { throw "git status failed" }

$hooks=@(Select-String -Path src\worker.py -Pattern 'crash_at|before_effect_commit|after_effect_commit|after_mark_commit')
"remaining_hook_lines=$($hooks.Count)"
if ($hooks.Count -ne 0) { throw "temporary hook remains" }

$q=@"
select status,count(*) from jobs group by status order by status;
select count(*) as jobs,max(id) as max_id from jobs;
select last_value from jobs_id_seq;
select count(*) as executions from job_executions;
select count(*) as effects from side_effects;
select id,status,attempts,payload ? 'crash_at' as has_hook
from jobs where id in ($beforeId,$middleId,$afterId) order by id;
select created_at::date,count(*) from jobs group by created_at::date order by created_at::date;
select executed_at::date,count(*) from job_executions group by executed_at::date order by executed_at::date;
select count(*) as idle_in_transaction from pg_stat_activity where datname='relay' and state='idle in transaction';
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw "closing SQL failed" }

Get-FileHash docs\daily\week_03\DIN_03_PREDICTIONS_FROZEN.md -Algorithm SHA256
$relay=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'src\.(worker|reaper)' })
"relay_processes=$($relay.Count)"
$relay | Select-Object ProcessId,CommandLine
if ($relay.Count -ne 0) { throw "Relay process cleanup failed" }
```

Clean first run expected: `96 succeeded / 15 failed / 3 dead_letter`; jobs `114`; executions `105`; effects `8`; named attempts `2/2/1`; all hooks false; idle/processes `0`. **Max/sequence exact value must be recorded, not predicted**—failed/repeated inserts can consume sequence values.

---

# Part D — Scope guard

| Aaj tempting kya hai | Owner | Aaj karne se kya khota hai |
|---|---|---|
| Outbox table/dispatcher | **Week 4**; decision/cost evidence today for future D-24 | Raw crash states mitigation ke peeche hide hoti hain |
| External HTTP/email/payment sink | **Week 4 integration/outbox work** | Local ledger and remote receiver semantics mix hote hain |
| Fencing token/generation | Din 5 question; Week 4 build input | Aaj legal redispatch + dedup isolate karni hai |
| Enqueue `idempotency_key` | Din 4 | Two dedup layers same result explain karengi |
| Permanent crash handler/type | Never; temporary exact payload hook only | Test vocabulary production API banegi |
| Property/random test | Din 5 | Exact three boundaries pehle manually visible honi chahiye |
