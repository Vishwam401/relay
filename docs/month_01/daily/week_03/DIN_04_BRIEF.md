# Week 3 Din 4 BRIEF — dedup at enqueue

**Aaj ek nayi dedup layer banti hai: client retry se do `jobs` rows banne se rokna. Ye Din 2/3 execute dedup ko replace nahi karti.**

Seal rule: Part B ke six answers pehle `DIN_04_ANSWERS.md` me; immutable copy + SHA-256; phir har step ka experiment; output ke against apni explanation; tab corresponding KEY section. `idk` valid hai. Part B Gemini ko paste nahi karna. KEY ka section experiment se pehle nahi kholna.

Current bench `[MEASURED-R 2026-09-02]`: `114` jobs (`96 succeeded / 15 failed / 3 dead_letter`), max/`jobs_id_seq=115`, `105` executions, `8` effects, `side_effects_id_seq=10`, Alembic `dbe13b69056d`, zero Relay Python processes, zero idle transactions. Jobs `113/114/115` and effects `7/8/10` preserve Din 3 evidence.

**Provenance note:** Part C ke “Expected” outputs and Part A ke future-state claims `[INFERRED from current source/schema and PostgreSQL semantics]` hain until tum corresponding command chala kar actual output `[MEASURED]` record karo. Exact IDs, sequence movement, winner, waits, and timings pre-fill nahi hote.

---

# Part A — Steps

## Step 0 — 10 min: freeze predictions + opening bench

**Terms used in this step**
- **Enqueue idempotency:** same caller intent retry hone par ek hi accepted job identity milna.
- **Prediction provenance:** run se pehle ka immutable text; later correction prediction credit nahi hoti.
- **Evidence database:** `relay`; migration downgrade/lifecycle probes is database par nahi chalenge.

1. Part B ke exact six questions `DIN_04_ANSWERS.md` me answer karo. Har question ke neeche permanent `Prediction`, empty `Observed + meri explanation`, and empty `After KEY` blocks rakho.
2. Answers ko `DIN_04_PREDICTIONS_FROZEN.md` me copy karo; SHA-256 log me paste karo; frozen file phir edit mat karo.
3. Opening direct DB, **Python runtime DB target**, schema, process, and source checks run karo. Mismatch ho to stop; Din 3 rows silently repair mat karo.
4. `git diff HEAD -- src alembic` opening state preserve karo. Whole-repo clean expected nahi—review docs changed ho sakte hain.

**Executable end:** frozen predictions + opening output; no DB/process/source delta.

## Step 1 — 10–15 min: contract card + request identity

**Terms used in this step**
- **Caller-minted key:** caller one logical operation ke retries me same opaque key bhejta hai; new operation ko new key.
- **Request fingerprint:** cleaned `type` + canonical payload ka stable digest; key reuse with changed content detect karta hai.
- **Canonical JSON:** object-key order se independent deterministic representation.
- **Replay contract:** same key + same fingerprint ko API kya response deti hai.

Code se pehle log me contract card fill karo:

1. Key caller mint karega. Cost: caller discipline required; Relay-generated/payload-only identity lost-response retry ko link nahi kar sakti ya legitimate identical jobs collapse kar sakti hai.
2. API transport today: optional JSON field `idempotency_key`. Omitted means opt-out. Non-blank trimmed key; finite max length choose karke contract card me record karo aur `src.schemas.IDEMPOTENCY_KEY_MAX_LENGTH` ke naam se expose karo, taki boundary probe wahi value test kare.
3. Dedup window today: row/key retained rehne tak. Time window claim tab tak nahi jab tak expiry/cleanup exists nahi.
4. Same key + same fingerprint ke liye **one** replay contract choose and freeze:
   - `202-original`: original `job_id` + current status; or
   - `409-replay`: stable code `idempotent_replay` + original `job_id`.
5. Same key + different fingerprint always `409`, code `idempotency_key_mismatch`; changed request ko false replay success nahi milna chahiye.
6. Fingerprint contract: cleaned `type` and canonical payload included; key excluded. Required interface: `request_fingerprint(job_type, payload) -> 64-char lowercase SHA-256 hex`—implementation tum likhoge.
7. `JobCreate` me optional key and fingerprint helper add karo. Endpoint DB behavior abhi mat badlo.

**Executable end:** key trimming/blank rejection works; key order same fingerprint deta hai; same payload with different type and same type with different payload dono fingerprint badalte hain; digest exactly lowercase 64-hex hai.

**KEY:** Step 1 card freeze hone ke baad hi “Contract trade-offs” compare karo.

## Step 2 — 10–15 min: schema source + disposable catalog proof

**Terms used in this step**
- **Named unique constraint:** stable name se expected conflict identify aur migration audit hota hai.
- **Nullable uniqueness:** ordinary PostgreSQL uniqueness non-null keys arbitrate karti hai; `NULL` control Step 7 me.
- **Target assertion:** every Alembic invocation se pehle usi exact overridden URL par `current_database()` verify karna (`P-28`).

1. Checked Alembic helper se deterministic revision `w3d4_enqueue_idempotency`, parent `dbe13b69056d`, create karo.
2. Model + migration me additive nullable columns:
   - `idempotency_key TEXT NULL`;
   - `request_fingerprint TEXT NULL`;
   - named `UNIQUE(idempotency_key)` constraint `uq_jobs_idempotency_key`.
3. No default/backfill/rewrite.
4. GUID/PID catalog DB create karo. Exact URL helper ko do; helper same URL se `current_database()` assert **before** `upgrade`.
5. Head catalog me both columns + named validated constraint prove karo; `finally` me DB drop and absence prove karo.

**Executable end:** source compiles, migration head deterministic hai, disposable catalog exact shape dikhata hai, catalog DB absent hai, evidence DB still old head par hai.

**KEY:** abhi schema outcome section mat kholo; lifecycle abhi baaki hai.

## Step 3 — 10–15 min: down/up lifecycle + evidence upgrade

**Terms used in this step**
- **Lifecycle proof:** empty disposable DB me upgrade→downgrade→upgrade se both directions execute karna.
- **Evidence upgrade:** retained `relay` data par upgrade only; downgrade forbidden.
- **Explicit override:** `Config.set_main_option("sqlalchemy.url", exact_url)`; default `alembic.ini` invocation forbidden.

1. Fresh GUID/PID lifecycle DB create karo.
2. Har upgrade/downgrade se pehle helper exact overridden URL par target DB assert kare.
3. Head shape `2 columns / 1 constraint`; parent shape `0 / 0`; re-upgrade new head.
4. Failure ho tab bhi `finally` DB terminate/drop kare and absence prove kare.
5. Evidence URL explicitly helper ko do; helper `relay` assert kare, then **upgrade only**.
6. Existing `114` rows `NULL/NULL`, count unchanged, new head and catalog prove karo.

**Executable end:** disposable lifecycle gone; evidence DB new head par with unchanged old rows.

**KEY:** ab **“Open after Step 3 — schema/lifecycle traps”** kholo.

## Step 4 — 10–15 min: first keyed enqueue + sequential replay

**Terms used in this step**
- **Conflict-safe insert:** database uniqueness final arbiter; expected duplicate generic failure nahi banti.
- **Replay:** same key **and** same fingerprint.
- **Sequence attribution:** row count aur sequence allocation ko separate role-wise record karna.

1. Keyed `POST /jobs` path implement karo with one database arbiter. Valid shapes:
   - named idempotency `IntegrityError`, explicit rollback, then original read; or
   - `INSERT ... ON CONFLICT ON CONSTRAINT uq_jobs_idempotency_key DO NOTHING RETURNING ...`, then later original read.
2. Every `IntegrityError` ko replay mat banao; Step 5 iska negative control hai.
3. First request: `sleep` + payload `{a:1,b:2}` + fresh key.
4. Replay: same key + logically same payload reversed `{b:2,a:1}`.
5. Required: one DB row; first `202`; replay frozen contract; full stored fingerprint lowercase 64-hex.
6. Capture `jobs_id_seq` as `$seq0 → $seq1 → $seq2` and log first/replay deltas separately. Exact movement predict mat karo.

**Executable end:** sequential retry reaches one database verdict, creates no second row, and returns original identity according to frozen contract.

**KEY:** ab **Q2** kholo.

## Step 5 — 15 min: mismatch + failed-session + unrelated-integrity controls

**Terms used in this step**
- **Key misuse:** same key, changed request content.
- **Aborted transaction:** failed SQL statement ke baad rollback tak transaction/session usable nahi.
- **Constraint attribution:** expected `uq_jobs_idempotency_key` conflict ko unrelated integrity failures se distinguish karna.

1. Step 4 key ke saath **same type** `sleep`, but changed payload `{a:1,b:3}` bhejo. Required `409 idempotency_key_mismatch`.
2. Full `id/type/payload/request_fingerprint` before/after compare karo; original row byte-for-byte query output me unchanged rehni chahiye. Capture `$seq3` after mismatch.
3. Isolated AsyncSession probe duplicate key intentionally `flush()` kare, then rollback se pehle SELECT try kare. Exact `PendingRollbackError` or DBAPI `25P02` record karo; rollback ke baad original SELECT works prove karo.
4. Temporary trigger same existing key ke attempted INSERT ko unrelated named `jobs_status_check` violation me turn kare. Correct endpoint must **not** return replay/mismatch; expected HTTP `500` + API log `23514/jobs_status_check`. Catch-all `IntegrityError => replay` implementation is control me fail hogi.
5. Trigger/function `finally` me remove karo; both `pg_trigger` and `pg_proc` absence prove karo.
6. Role-wise sequence capture: mismatch, failed-session duplicate, unrelated integrity attempt.

**Executable end:** changed payload false success nahi paata; failed session rollback requirement measured hai; unrelated integrity error replay me misclassified nahi hoti; no probe objects/rows survive.

**KEY:** ab **Q4 and Q5** kholo.

## Step 6 — 15 min: two genuinely concurrent identical POSTs

**Terms used in this step**
- **Unique-index arbitration:** concurrent contenders ka winner database chooses; app timing nahi.
- **Transaction wait:** loser winner commit/rollback decision tak block kar sakta hai.
- **Overlap fixture:** temporary `AFTER INSERT` trigger winner transaction ko 5 s hold karta hai.

1. API `--reload` ke bina live rakho.
2. Temporary trigger only `din4-race-*` keys par `pg_sleep(5)` kare.
3. Two PowerShell jobs same key/body concurrently POST karein.
4. Hold ke beech observer me winner `Timeout/PgSleep` and contender `Lock/transactionid` assert karo; observer backend exclude karo.
5. Responses/elapsed preserve; final keyed rows `1`; capture `$raceSeqBefore/$raceSeqAfter`.
6. `try/finally` clients and trigger/function clean kare; both catalogs zero prove kare.

**Executable end:** requests actually overlap; one-row result sequential luck nahi; race sequence delta has its own role.

**KEY:** ab **Q3** kholo.

## Step 7 — 10 min: opt-out control — two unkeyed requests

**Terms used in this step**
- **Opt-in dedup:** key omitted ho to each request distinct intent.
- **`NULLS DISTINCT`:** ordinary PostgreSQL unique behavior; multiple null keys coexist.
- **Negative control:** mechanism absent path intentionally different output deta hai.

Same type + same payload ke two requests without key bhejo. Required: both `202`, distinct IDs, exactly two rows, both key/fingerprint `NULL`. One row means dedup accidentally mandatory/payload-derived ho gayi.

**Executable end:** keyed path collapses; same unkeyed payload does not.

**KEY:** ab **Q1** kholo.

## Step 8 — 15 min: execute-layer regression with heartbeat-safe reclaim barrier

**Terms used in this step**
- **Enqueue dedup:** same caller key se duplicate job rows rokti hai.
- **Execute dedup:** one job ki legal redispatch se duplicate keyed local effect row rokti hai.
- **Non-yielding handler:** `block=true` uses `time.sleep`, so event loop heartbeat run nahi kar sakta.
- **Committed reclaim barrier:** Worker B tab start hota hai jab DB visibly `pending/claimed_at NULL` ho; stdout line alone commit proof nahi.

1. Exact four HTTP fixtures pre-read by ID (sequential, race, two unkeyed). All must be `pending` with null schedule. Only those IDs ko `next_attempt_at='infinity'` gate karo.
2. Fresh keyed `effect` target `{seconds:45, block:true}` enqueue karo. Capture job/effect sequences before/after roles.
3. Worker A effect `rowcount=1` + blocking line ke baad target `claimed_at` manually 31 s old karo. Non-yielding block prevents the 10 s heartbeat from refreshing it.
4. Reaper must print target `matched=1`; then DB committed barrier must read `pending`, attempts `1`, `claimed_at NULL`. Only then Worker B start.
5. Worker B must claim attempt 2 and effect replay `rowcount=0`. Both workers finish; expected final `succeeded/attempts2/executions2/workers2/effects1`.
6. Main-terminal `try/finally` exact four fixture IDs reset kare, even on assertion failure; global infinity count zero prove kare. Failure path me processes stop karke hi gate release karo.

**Executable end:** enqueue uniqueness did not replace execute uniqueness; reclaim definitely happened; yielding heartbeat cannot invalidate the experiment; no gate survives.

**KEY:** ab **Q6** kholo.

## Step 9 — 10 min: comparison, Din 6 decision input, reconciliation

**Terms used in this step**
- **Layered idempotency:** different duplicate causes ko different identities/invariants absorb karte hain.
- **Retention-bound window:** key row delete hone tak remembered; deletion ke baad old retry new request ban sakta hai.
- **Named reconciliation:** every new row returned ID/role se explained; sequence contiguity required nahi.

1. Log me **D-24 decision input** likho—`DECISIONS.md` edit/publish mat karo. Governing Week 3 plan ke mutabik Din 6 grep ke baad `D-24` publish karega:
   - enqueue vs execute distinct scopes and why both remain;
   - caller-key, retention-window, replay-response costs;
   - same-key/different-request rule;
   - measured concurrent wait;
   - neither gives exactly-once external effects.
2. Row delta by role: sequential `+1`, mismatch/controls `+0`, race `+1`, unkeyed `+2`, execute regression `+1` = `+5 jobs`; regression `+2 executions`, `+1 effect`.
3. Expected close: `119 jobs`, `107 executions`, `9 effects`; statuses `97 succeeded / 15 failed / 3 dead_letter / 4 pending / 0 running`.
4. Max and sequences measure, don't predict. Log each conflict role's delta.
5. API/workers/reaper stop; PowerShell jobs, both temporary trigger/functions, catalog/lifecycle DBs, infinity gate absent; zero idle transactions.
6. Compile, diff checks, frozen hash, migration head, named rows. WEEK_03 template fill; “What I Understood” apne words me.

**Executable end:** cold reader every row, both dedup layers, API contract, sequence gaps, and cleanup explain kar sakta hai; `D-24` remains reserved for Din 6 publication.

---

# Part B — Prediction questions — Gemini ko paste mat karna

```text
Q1. jobs.idempotency_key nullable aur UNIQUE hai. Same body ke do POST, dono key omit karte hain. Final rows
    1 hongi ya 2? PostgreSQL mechanism naam se likho.

Q2. Same non-null key ka sequential replay atomic INSERT path tak pahunchta hai. jobs count aur jobs_id_seq
    ke baare me separately predict karo. Integrity conflict Python/SQLAlchemy me execute, flush, ya commit me
    kahan surface hoga—apne chosen implementation ke liye exact bolo.

Q3. Do identical keyed POST genuinely concurrent hain; winner commit se pehle 5 s trigger me held hai.
    Loser immediately answer karega ya wait? pg_stat_activity me expected wait_event_type/wait_event kya hai,
    aur final row count kya hoga?

Q4. Same key pe pehle type=sleep,payload={a:1,b:2}; phir type=sleep,payload={a:1,b:3}. Sirf original
    job_id return kar dena kis correctness bug ko create karta hai? Fingerprint me type aur payload dono kyu
    hone chahiye, aur JSON object-key order ka kya?

Q5. IntegrityError catch karne ke baad rollback se pehle usi AsyncSession par original row SELECT kar sakte
    ho? SQLAlchemy/PostgreSQL kis failed-transaction behavior se rokta hai? Har IntegrityError ko replay
    treat karna kyu unsafe hai?

Q6. Enqueue UNIQUE ship hone ke baad side_effects.effect_key UNIQUE hata sakte hain? Ek client-retry case aur
    ek lease-reclaim case se derive karo.
```

---

# Part C — Verification — exact commands and expected output

Long-running API/worker/reaper commands separate PowerShell terminals me manually run karo. API par `--reload` mat use karo. Every native command ka exit code record karo. SQL blocks `-X -v ON_ERROR_STOP=1` unless an error deliberate subject hai. **Har PowerShell terminal me Python process start karne se pehle** exact evidence target set karo: `$env:DATABASE_URL='postgresql+asyncpg://postgres:relay@localhost:5433/relay'`. `.env` sahi hone ke baad bhi inherited environment usse override kar sakta hai; C0 Python runtime target independently assert karta hai.

## C0 — frozen provenance + opening

Predictions likhne ke **baad**:

```powershell
if (Test-Path docs\daily\week_03\DIN_04_PREDICTIONS_FROZEN.md) {
  throw 'Frozen file already exists; overwrite mat karo'
}
Copy-Item docs\daily\week_03\DIN_04_ANSWERS.md docs\daily\week_03\DIN_04_PREDICTIONS_FROZEN.md
Get-FileHash docs\daily\week_03\DIN_04_PREDICTIONS_FROZEN.md -Algorithm SHA256

$runtimeUrl='postgresql+asyncpg://postgres:relay@localhost:5433/relay'
$env:DATABASE_URL=$runtimeUrl
$runtimeDb=@(.\.venv\Scripts\python.exe -c "from src.database import engine; print(engine.url.database)")
if ($LASTEXITCODE -ne 0) { throw 'Python runtime target probe failed' }
$runtimeDb=($runtimeDb -join '').Trim()
if ($runtimeDb -ne 'relay') { throw "Python runtime points at $runtimeDb, expected relay" }
"python_runtime_database=$runtimeDb"

$q=@"
select current_database();
select status,count(*) from jobs group by status order by status;
select count(*) as jobs,max(id) as max_id from jobs;
select last_value from jobs_id_seq;
select count(*) as executions from job_executions;
select count(*) as effects from side_effects;
select last_value from side_effects_id_seq;
select id,job_id,effect_key from side_effects where job_id in (113,114,115) order by id;
select count(*) from information_schema.columns
 where table_schema='public' and table_name='jobs'
 and column_name in ('idempotency_key','request_fingerprint');
select version_num from alembic_version;
select count(*) from pg_stat_activity
 where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select count(*) from jobs where next_attempt_at='infinity'::timestamptz;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw 'C0 SQL failed' }

$relay=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'uvicorn|src\.(worker|reaper)' })
"relay_processes=$($relay.Count)"
$relay | Select-Object ProcessId,CommandLine
git diff HEAD -- src alembic
```

Expected: direct SQL target `relay`; Python runtime target `python_runtime_database=relay`; `96 succeeded / 15 failed / 3 dead_letter`; jobs `114`, max/seq `115`; executions `105`; effects `8`, effect sequence `10`, rows `7→113, 8→114, 10→115`; new columns `0`; revision `dbe13b69056d`; idle/process/infinity `0`; no opening `src`/Alembic diff.

## C1 — request schema + fingerprint differentials

```powershell
.\.venv\Scripts\python.exe -m py_compile src\schemas.py src\main.py
if ($LASTEXITCODE -ne 0) { throw 'C1 compile failed' }

$probe=@'
import re
from pydantic import ValidationError
from src.schemas import IDEMPOTENCY_KEY_MAX_LENGTH, JobCreate
from src.main import request_fingerprint

def key_accepted(value: str) -> bool:
    try:
        JobCreate(type="sleep", payload={}, idempotency_key=value)
    except ValidationError:
        return False
    return True

if not isinstance(IDEMPOTENCY_KEY_MAX_LENGTH, int) or IDEMPOTENCY_KEY_MAX_LENGTH < 1:
    raise AssertionError("IDEMPOTENCY_KEY_MAX_LENGTH must be a positive integer")

a = JobCreate(type=" sleep ", payload={"a": 1, "b": 2}, idempotency_key=" client-abc ")
b = JobCreate(type="sleep", payload={"b": 2, "a": 1})
f = request_fingerprint(a.type, a.payload)
print("type=" + a.type)
print("key=" + str(a.idempotency_key))
print("unkeyed=" + str(b.idempotency_key))
print("max_key_length=" + str(IDEMPOTENCY_KEY_MAX_LENGTH))
print("blank_rejected=" + str(not key_accepted("   ")))
print("at_limit_accepted=" + str(key_accepted("k" * IDEMPOTENCY_KEY_MAX_LENGTH)))
print("over_limit_rejected=" + str(not key_accepted("k" * (IDEMPOTENCY_KEY_MAX_LENGTH + 1))))
print("hex64_lower=" + str(re.fullmatch(r"[0-9a-f]{64}", f) is not None))
print("order_same=" + str(f == request_fingerprint("sleep", {"b": 2, "a": 1})))
print("type_changes=" + str(f != request_fingerprint("boom", {"a": 1, "b": 2})))
print("payload_changes=" + str(f != request_fingerprint("sleep", {"a": 1, "b": 3})))
'@
.\.venv\Scripts\python.exe -c $probe
if ($LASTEXITCODE -ne 0) { throw 'C1 behavior probe failed' }
```

Expected: `max_key_length` contract card me frozen positive integer ke exactly equal ho; baaki lines exactly:

```text
type=sleep
key=client-abc
unkeyed=None
max_key_length=<frozen contract-card integer>
blank_rejected=True
at_limit_accepted=True
over_limit_rejected=True
hex64_lower=True
order_same=True
type_changes=True
payload_changes=True
```

Blank/limit checks validator ko decorative hone se rokte hain; three fingerprint differentials `hash(type)` and `hash(payload)` impostors separately defeat karte hain.

## C2 — checked Alembic helper + catalog proof

Define once in the current PowerShell terminal; fresh terminal ho to same block rerun:

```powershell
$evidenceUrl='postgresql+psycopg://postgres:relay@localhost:5433/relay'
function Invoke-Din4Alembic {
  param(
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$true)][string]$ExpectedDb,
    [Parameter(Mandatory=$true)][ValidateSet('revision','heads','upgrade','downgrade')][string]$Action,
    [string]$Target=''
  )
  $env:DIN4_ALEMBIC_URL=$Url
  $env:DIN4_EXPECTED_DB=$ExpectedDb
  $env:DIN4_ALEMBIC_ACTION=$Action
  $env:DIN4_ALEMBIC_TARGET=$Target
  $runner=@'
import os
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

url = os.environ["DIN4_ALEMBIC_URL"]
expected = os.environ["DIN4_EXPECTED_DB"]
action = os.environ["DIN4_ALEMBIC_ACTION"]
target = os.environ.get("DIN4_ALEMBIC_TARGET", "")
engine = create_engine(url)
try:
    with engine.connect() as conn:
        actual = conn.scalar(text("select current_database()"))
finally:
    engine.dispose()
if actual != expected:
    raise SystemExit(f"REFUSING ALEMBIC: expected={expected} actual={actual}")
print(f"alembic_target_checked={actual}")
config = Config("alembic.ini")
config.set_main_option("sqlalchemy.url", url)
if action == "revision":
    command.revision(config, message="add enqueue idempotency", rev_id=target)
elif action == "heads":
    command.heads(config)
else:
    getattr(command, action)(config, target)
'@
  $exit=0
  try {
    .\.venv\Scripts\python.exe -c $runner
    $exit=$LASTEXITCODE
  } finally {
    Remove-Item Env:DIN4_ALEMBIC_URL,Env:DIN4_EXPECTED_DB,Env:DIN4_ALEMBIC_ACTION,Env:DIN4_ALEMBIC_TARGET -ErrorAction SilentlyContinue
  }
  if ($exit -ne 0) { throw "checked Alembic failed: $Action $Target" }
}

$migration='alembic\versions\w3d4_enqueue_idempotency_add_enqueue_idempotency.py'
if (Test-Path $migration) { throw "revision already exists: $migration" }
Invoke-Din4Alembic -Url $evidenceUrl -ExpectedDb relay -Action revision -Target w3d4_enqueue_idempotency
```

Write model/migration yourself, then:

```powershell
.\.venv\Scripts\python.exe -m py_compile src\models.py $migration
if ($LASTEXITCODE -ne 0) { throw 'migration compile failed' }
Invoke-Din4Alembic -Url $evidenceUrl -ExpectedDb relay -Action heads
```

Expected includes `alembic_target_checked=relay` and `w3d4_enqueue_idempotency (head)`.

Catalog DB, with cleanup on every path:

```powershell
$catalogDb="relay_din4_catalog_${PID}_$([guid]::NewGuid().ToString('N').Substring(0,8))"
if ($catalogDb -notmatch '^relay_din4_catalog_\d+_[0-9a-f]{8}$') { throw 'unsafe catalog DB name' }
$catalogUrl="postgresql+psycopg://postgres:relay@localhost:5433/$catalogDb"
$catalogCreated=$false
try {
  "create database $catalogDb;" | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d postgres
  if ($LASTEXITCODE -ne 0) { throw 'catalog DB create failed' }
  $catalogCreated=$true
  Invoke-Din4Alembic -Url $catalogUrl -ExpectedDb $catalogDb -Action upgrade -Target w3d4_enqueue_idempotency
  $q=@"
select current_database();
select version_num from alembic_version;
select count(*) from information_schema.columns
 where table_schema='public' and table_name='jobs'
 and column_name in ('idempotency_key','request_fingerprint');
select count(*) from pg_constraint
 where conname='uq_jobs_idempotency_key' and conrelid='jobs'::regclass and convalidated;
"@
  $q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d $catalogDb
  if ($LASTEXITCODE -ne 0) { throw 'catalog proof failed' }
} finally {
  $q=@"
select pg_terminate_backend(pid) from pg_stat_activity
 where datname='$catalogDb' and pid<>pg_backend_pid();
drop database if exists $catalogDb;
"@
  $q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d postgres
  if ($LASTEXITCODE -ne 0) { throw 'catalog cleanup failed' }
}
$remaining=@("select count(*) from pg_database where datname='$catalogDb';" |
  docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d postgres)
if (($remaining -join '').Trim() -ne '0') { throw 'catalog DB survived cleanup' }
"catalog_db_remaining=0"
```

Expected catalog: exact DB name, revision new head, columns `2`, named validated constraint `1`; then `catalog_db_remaining=0`. Evidence DB is still old head.

## C3 — lifecycle + explicit evidence upgrade

C2 helper must exist in this terminal. Fresh lifecycle DB:

```powershell
$lifecycleDb="relay_din4_lifecycle_${PID}_$([guid]::NewGuid().ToString('N').Substring(0,8))"
if ($lifecycleDb -notmatch '^relay_din4_lifecycle_\d+_[0-9a-f]{8}$') { throw 'unsafe lifecycle DB name' }
$lifecycleUrl="postgresql+psycopg://postgres:relay@localhost:5433/$lifecycleDb"
try {
  "create database $lifecycleDb;" | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d postgres
  if ($LASTEXITCODE -ne 0) { throw 'lifecycle DB create failed' }

  Invoke-Din4Alembic -Url $lifecycleUrl -ExpectedDb $lifecycleDb -Action upgrade -Target w3d4_enqueue_idempotency
  $q=@"
select current_database(),version_num from alembic_version;
select count(*) from information_schema.columns where table_schema='public' and table_name='jobs'
 and column_name in ('idempotency_key','request_fingerprint');
select count(*) from pg_constraint where conname='uq_jobs_idempotency_key' and conrelid='jobs'::regclass;
"@
  $q | docker exec -i relay-db-1 psql -X -At -v ON_ERROR_STOP=1 -U postgres -d $lifecycleDb

  Invoke-Din4Alembic -Url $lifecycleUrl -ExpectedDb $lifecycleDb -Action downgrade -Target dbe13b69056d
  $q=@"
select current_database(),version_num from alembic_version;
select count(*) from information_schema.columns where table_schema='public' and table_name='jobs'
 and column_name in ('idempotency_key','request_fingerprint');
select count(*) from pg_constraint where conname='uq_jobs_idempotency_key';
"@
  $q | docker exec -i relay-db-1 psql -X -At -v ON_ERROR_STOP=1 -U postgres -d $lifecycleDb

  Invoke-Din4Alembic -Url $lifecycleUrl -ExpectedDb $lifecycleDb -Action upgrade -Target w3d4_enqueue_idempotency
  $reupgraded=@("select current_database()||'|'||version_num||'|'||(select count(*) from information_schema.columns where table_schema='public' and table_name='jobs' and column_name in ('idempotency_key','request_fingerprint'))::text||'|'||(select count(*) from pg_constraint where conname='uq_jobs_idempotency_key' and conrelid='jobs'::regclass)::text from alembic_version;" |
    docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $lifecycleDb)
  if ($LASTEXITCODE -ne 0) { throw 'lifecycle re-upgrade assertion query failed' }
  $reupgraded=($reupgraded -join '').Trim()
  $expectedReupgraded="$lifecycleDb|w3d4_enqueue_idempotency|2|1"
  if ($reupgraded -ne $expectedReupgraded) { throw "lifecycle re-upgrade shape failed: actual=$reupgraded expected=$expectedReupgraded" }
  "lifecycle_reupgrade=$reupgraded"
} finally {
  $q=@"
select pg_terminate_backend(pid) from pg_stat_activity
 where datname='$lifecycleDb' and pid<>pg_backend_pid();
drop database if exists $lifecycleDb;
"@
  $q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d postgres
  if ($LASTEXITCODE -ne 0) { throw 'lifecycle cleanup failed' }
}
$remaining=@("select count(*) from pg_database where datname='$lifecycleDb';" |
  docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d postgres)
if (($remaining -join '').Trim() -ne '0') { throw 'lifecycle DB survived cleanup' }
"lifecycle_db_remaining=0"
```

Expected lifecycle roles: first head `2/1`; parent `0/0`; re-upgrade output ends `|w3d4_enqueue_idempotency|2|1` and is mechanically asserted; remaining DB count `0`.

Evidence upgrade uses the same explicit URL and helper—never bare `alembic upgrade`:

```powershell
$before=@("select current_database()||'|'||version_num from alembic_version;" |
  docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if (($before -join '').Trim() -ne 'relay|dbe13b69056d') { throw "unexpected evidence target/head: $before" }
Invoke-Din4Alembic -Url $evidenceUrl -ExpectedDb relay -Action upgrade -Target w3d4_enqueue_idempotency
$q=@"
select current_database();
select version_num from alembic_version;
select count(*) as jobs from jobs;
select count(*) as old_rows_still_null from jobs
 where idempotency_key is null and request_fingerprint is null;
select count(*) as columns from information_schema.columns
 where table_schema='public' and table_name='jobs'
 and column_name in ('idempotency_key','request_fingerprint');
select conname,convalidated from pg_constraint
 where conname='uq_jobs_idempotency_key' and conrelid='jobs'::regclass;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw 'evidence upgrade proof failed' }
```

Expected: helper prints `alembic_target_checked=relay` **before DDL**; revision new head; jobs `114`; old null rows `114`; columns `2`; named constraint validated.

## C4 — first + sequential replay

API terminal, no reload:

```powershell
$env:DATABASE_URL='postgresql+asyncpg://postgres:relay@localhost:5433/relay'
.\.venv\Scripts\python.exe -u -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Main terminal:

```powershell
$replayMode='202-original'  # OR exactly '409-replay', matching frozen card
if ($replayMode -notin @('202-original','409-replay')) { throw 'freeze replayMode first' }
function Read-Scalar([string]$Sql) {
  $x=@($Sql | docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
  if ($LASTEXITCODE -ne 0) { throw 'scalar SQL failed' }
  return ($x -join '').Trim()
}
function Send-Job($Body) {
  $json=$Body | ConvertTo-Json -Depth 8 -Compress
  Invoke-WebRequest -Method Post -Uri http://127.0.0.1:8000/jobs `
    -ContentType 'application/json' -Body $json -SkipHttpErrorCheck
}
function Read-JobSnapshot([long]$Id) {
  Read-Scalar "select json_build_object('id',id,'type',type,'payload',payload,'request_fingerprint',request_fingerprint)::text from jobs where id=$Id;"
}

$seqKey='din4-seq-'+[guid]::NewGuid().ToString('N')
$seq0=[long](Read-Scalar 'select last_value from jobs_id_seq;')
$first=Send-Job ([ordered]@{type='sleep';payload=[ordered]@{a=1;b=2};idempotency_key=$seqKey})
$seq1=[long](Read-Scalar 'select last_value from jobs_id_seq;')
$replay=Send-Job ([ordered]@{type='sleep';payload=[ordered]@{b=2;a=1};idempotency_key=$seqKey})
$seq2=[long](Read-Scalar 'select last_value from jobs_id_seq;')
$firstBody=$first.Content | ConvertFrom-Json
$replayBody=$replay.Content | ConvertFrom-Json
if ($first.StatusCode -ne 202) { throw "first status=$($first.StatusCode)" }
if ($replayMode -eq '202-original') {
  if ($replay.StatusCode -ne 202 -or $firstBody.job_id -ne $replayBody.job_id) { throw '202 replay contract failed' }
} else {
  if ($replay.StatusCode -ne 409 -or $replayBody.detail.code -ne 'idempotent_replay' -or
      $replayBody.detail.job_id -ne $firstBody.job_id) { throw '409 replay contract failed' }
}
$seqJobId=[long]$firstBody.job_id
$rowsForKey=[int](Read-Scalar "select count(*) from jobs where idempotency_key='$seqKey';")
if ($rowsForKey -ne 1) { throw "rows_for_key=$rowsForKey" }
$originalSnapshot=Read-JobSnapshot $seqJobId
$originalObject=$originalSnapshot | ConvertFrom-Json
if ($originalObject.request_fingerprint -notmatch '^[0-9a-f]{64}$') { throw 'stored fingerprint is not lowercase 64-hex' }
"seq_first: before=$seq0 after=$seq1 delta=$($seq1-$seq0)"
"seq_replay: before=$seq1 after=$seq2 delta=$($seq2-$seq1)"
"seqKey=$seqKey job_id=$seqJobId first=$($first.StatusCode) replay=$($replay.StatusCode) rows=$rowsForKey"
"original_snapshot=$originalSnapshot"
```

Expected: first `202`; replay frozen mode; same original ID named; rows `1`; full fingerprint regex passes. Sequence deltas are measured, not prescribed.

## C5 — mismatch, failed session, unrelated integrity

Mismatch changes payload while keeping type fixed:

```powershell
$beforeMismatch=Read-JobSnapshot $seqJobId
$mismatch=Send-Job ([ordered]@{type='sleep';payload=[ordered]@{a=1;b=3};idempotency_key=$seqKey})
$seq3=[long](Read-Scalar 'select last_value from jobs_id_seq;')
$mismatchBody=$mismatch.Content | ConvertFrom-Json
$afterMismatch=Read-JobSnapshot $seqJobId
if ($mismatch.StatusCode -ne 409 -or $mismatchBody.detail.code -ne 'idempotency_key_mismatch' -or
    $mismatchBody.detail.job_id -ne $seqJobId) { throw 'mismatch contract failed' }
if ($beforeMismatch -cne $afterMismatch) { throw "original row changed`nbefore=$beforeMismatch`nafter=$afterMismatch" }
"seq_mismatch: before=$seq2 after=$seq3 delta=$($seq3-$seq2)"
"mismatch_status=$($mismatch.StatusCode) code=$($mismatchBody.detail.code)"
"before_mismatch=$beforeMismatch"
"after_mismatch=$afterMismatch"
```

Expected: `409 idempotency_key_mismatch`; before/after full type, payload, fingerprint identical; this catches fingerprints that hash only type.

Isolated failed-session probe (no surviving row):

```powershell
$env:DIN4_DUP_KEY=$seqKey
$failedSeqBefore=[long](Read-Scalar 'select last_value from jobs_id_seq;')
$failedProbe=@'
import asyncio
import os
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError, IntegrityError, PendingRollbackError
from src.database import async_session, engine
from src.models import Job

def metadata(exc):
    objects = [exc, getattr(exc, "orig", None), getattr(getattr(exc, "orig", None), "__cause__", None)]
    state = next((getattr(o, name) for o in objects if o for name in ("sqlstate", "pgcode") if getattr(o, name, None)), None)
    constraint = next((getattr(o, "constraint_name") for o in objects if o and getattr(o, "constraint_name", None)), None)
    return state, constraint

async def main():
    key = os.environ["DIN4_DUP_KEY"]
    try:
        async with async_session() as session:
            session.add(Job(type="sleep", payload={"probe": "failed-session"}, idempotency_key=key, request_fingerprint="0" * 64))
            try:
                await session.flush()
            except IntegrityError as exc:
                state, constraint = metadata(exc)
                print(f"duplicate_integrity=IntegrityError sqlstate={state} constraint={constraint}")
                if state != "23505" or constraint != "uq_jobs_idempotency_key":
                    raise
                try:
                    await session.execute(select(Job.id).limit(1))
                except PendingRollbackError:
                    print("before_rollback=PendingRollbackError")
                except DBAPIError as blocked:
                    blocked_state, _ = metadata(blocked)
                    print(f"before_rollback={type(blocked).__name__} sqlstate={blocked_state}")
                    if blocked_state != "25P02":
                        raise
                else:
                    raise AssertionError("SELECT unexpectedly worked before rollback")
                await session.rollback()
                rows = await session.scalar(select(func.count()).select_from(Job).where(Job.idempotency_key == key))
                print(f"after_rollback_rows={rows}")
                if rows != 1:
                    raise AssertionError(rows)
            else:
                raise AssertionError("duplicate flush unexpectedly succeeded")
    finally:
        await engine.dispose()

asyncio.run(main())
'@
try {
  .\.venv\Scripts\python.exe -c $failedProbe
  if ($LASTEXITCODE -ne 0) { throw 'failed-session probe failed' }
} finally {
  Remove-Item Env:DIN4_DUP_KEY -ErrorAction SilentlyContinue
}
$failedSeqAfter=[long](Read-Scalar 'select last_value from jobs_id_seq;')
"seq_failed_session: before=$failedSeqBefore after=$failedSeqAfter delta=$($failedSeqAfter-$failedSeqBefore)"
```

Expected: duplicate is `23505/uq_jobs_idempotency_key`; pre-rollback operation is exact `PendingRollbackError` (or lower-level DBAPI `25P02`, if that path is used); after rollback rows `1`.

Unrelated integrity control through HTTP; cleanup runs even if assertions fail:

```powershell
$unrelatedSeqBefore=[long](Read-Scalar 'select last_value from jobs_id_seq;')
try {
  $q=@"
drop trigger if exists din4_force_unrelated_integrity_trigger on jobs;
drop function if exists din4_force_unrelated_integrity();
create function din4_force_unrelated_integrity() returns trigger language plpgsql as `$`$
begin
  if new.idempotency_key = '$seqKey' then
    new.status := 'din4_invalid_status';
  end if;
  return new;
end
`$`$;
create trigger din4_force_unrelated_integrity_trigger
before insert on jobs for each row execute function din4_force_unrelated_integrity();
"@
  $q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
  if ($LASTEXITCODE -ne 0) { throw 'unrelated trigger install failed' }
  $unrelated=Send-Job ([ordered]@{type='sleep';payload=[ordered]@{a=1;b=2};idempotency_key=$seqKey})
  if ($unrelated.StatusCode -ne 500) { throw "catch-all IntegrityError likely misclassified: status=$($unrelated.StatusCode) body=$($unrelated.Content)" }
  if ($unrelated.Content -match 'idempotent_replay|idempotency_key_mismatch') { throw 'unrelated integrity became replay/mismatch' }
  if ((Read-Scalar "select count(*) from jobs where idempotency_key='$seqKey';") -ne '1') { throw 'unrelated control changed row count' }
  if ((Read-JobSnapshot $seqJobId) -cne $originalSnapshot) { throw 'unrelated control changed original row' }
  "unrelated_status=$($unrelated.StatusCode) body=$($unrelated.Content)"
  'Record API terminal evidence: SQLSTATE 23514, constraint jobs_status_check.'
} finally {
  $q=@"
drop trigger if exists din4_force_unrelated_integrity_trigger on jobs;
drop function if exists din4_force_unrelated_integrity();
select count(*) from pg_trigger where tgname='din4_force_unrelated_integrity_trigger' and not tgisinternal;
select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='din4_force_unrelated_integrity';
"@
  $q | docker exec -i relay-db-1 psql -X -At -v ON_ERROR_STOP=1 -U postgres -d relay
  if ($LASTEXITCODE -ne 0) { throw 'unrelated fixture cleanup failed' }
}
$unrelatedSeqAfter=[long](Read-Scalar 'select last_value from jobs_id_seq;')
"seq_unrelated_integrity: before=$unrelatedSeqBefore after=$unrelatedSeqAfter delta=$($unrelatedSeqAfter-$unrelatedSeqBefore)"
```

Expected HTTP `500`, API terminal names `23514/jobs_status_check`, original row unchanged, and cleanup prints `0` then `0`. If response is replay contract, constraint filtering is broken.

## C6 — deterministic concurrent POST race

```powershell
$raceKey='din4-race-'+[guid]::NewGuid().ToString('N')
$raceSeqBefore=[long](Read-Scalar 'select last_value from jobs_id_seq;')
$clients=@()
try {
  $q=@'
drop trigger if exists din4_hold_race_insert_trigger on jobs;
drop function if exists din4_hold_race_insert();
create function din4_hold_race_insert() returns trigger language plpgsql as $$
begin
  if new.idempotency_key like 'din4-race-%' then
    perform pg_sleep(5);
  end if;
  return new;
end
$$;
create trigger din4_hold_race_insert_trigger
after insert on jobs for each row execute function din4_hold_race_insert();
'@
  $q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
  if ($LASTEXITCODE -ne 0) { throw 'race trigger install failed' }

  $raceBody=([ordered]@{type='sleep';payload=@{probe='concurrent'};idempotency_key=$raceKey} |
    ConvertTo-Json -Depth 8 -Compress)
  $clientBlock={
    param($Body)
    $sw=[Diagnostics.Stopwatch]::StartNew()
    $r=Invoke-WebRequest -Method Post -Uri http://127.0.0.1:8000/jobs `
      -ContentType 'application/json' -Body $Body -SkipHttpErrorCheck
    $sw.Stop()
    [pscustomobject]@{status=[int]$r.StatusCode;body=$r.Content;elapsed_ms=[math]::Round($sw.Elapsed.TotalMilliseconds,1)}
  }
  $clients=@(
    Start-Job -ScriptBlock $clientBlock -ArgumentList $raceBody
    Start-Job -ScriptBlock $clientBlock -ArgumentList $raceBody
  )
  Start-Sleep -Seconds 2
  $lockWaiters=[int](Read-Scalar "select count(*) from pg_stat_activity where pid<>pg_backend_pid() and datname='relay' and state='active' and query ilike '%insert into jobs%' and wait_event_type='Lock' and wait_event='transactionid';")
  $sleepers=[int](Read-Scalar "select count(*) from pg_stat_activity where pid<>pg_backend_pid() and datname='relay' and state='active' and query ilike '%insert into jobs%' and wait_event_type='Timeout' and wait_event='PgSleep';")
  $q=@"
select pid,wait_event_type,wait_event,left(query,90)
from pg_stat_activity
where pid<>pg_backend_pid() and datname='relay' and state='active' and query ilike '%insert into jobs%'
order by wait_event_type,wait_event;
"@
  $q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
  if ($lockWaiters -lt 1 -or $sleepers -lt 1) { throw "overlap not proved: lock=$lockWaiters sleepers=$sleepers" }

  $results=@($clients | Wait-Job | Receive-Job)
  if ($results.Count -ne 2) { throw "client result count=$($results.Count)" }
  $results | Sort-Object status | Format-Table -AutoSize
  $statuses=(@($results.status | Sort-Object) -join ',')
  if ($replayMode -eq '202-original' -and $statuses -ne '202,202') { throw "race statuses=$statuses" }
  if ($replayMode -eq '409-replay' -and $statuses -ne '202,409') { throw "race statuses=$statuses" }
  $ids=@()
  foreach ($r in $results) {
    $body=$r.body | ConvertFrom-Json
    if ($r.status -eq 202) { $ids += [long]$body.job_id }
    else { $ids += [long]$body.detail.job_id }
  }
  if (@($ids | Sort-Object -Unique).Count -ne 1) { throw "race returned identities=$ids" }
  $raceJobId=[long]$ids[0]
  if ((Read-Scalar "select count(*) from jobs where idempotency_key='$raceKey';") -ne '1') { throw 'race row count is not one' }
  $raceSnapshot=Read-JobSnapshot $raceJobId
  if (($raceSnapshot | ConvertFrom-Json).request_fingerprint -notmatch '^[0-9a-f]{64}$') { throw 'race fingerprint invalid' }
  $raceSeqAfter=[long](Read-Scalar 'select last_value from jobs_id_seq;')
  "race_observer: sleepers=$sleepers lock_waiters=$lockWaiters"
  "race_sequence: before=$raceSeqBefore after=$raceSeqAfter delta=$($raceSeqAfter-$raceSeqBefore)"
  "raceKey=$raceKey raceJobId=$raceJobId snapshot=$raceSnapshot"
} finally {
  foreach ($j in @($clients)) {
    if ($j.State -eq 'Running') { Stop-Job $j -ErrorAction SilentlyContinue }
    Remove-Job $j -Force -ErrorAction SilentlyContinue
  }
  $q=@"
drop trigger if exists din4_hold_race_insert_trigger on jobs;
drop function if exists din4_hold_race_insert();
select count(*) from pg_trigger where tgname='din4_hold_race_insert_trigger' and not tgisinternal;
select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='din4_hold_race_insert';
"@
  $q | docker exec -i relay-db-1 psql -X -At -v ON_ERROR_STOP=1 -U postgres -d relay
  if ($LASTEXITCODE -ne 0) { throw 'race fixture cleanup failed' }
}
```

Expected observer `sleepers>=1`, `lock_waiters>=1`; responses frozen contract; same original ID; one row; cleanup prints `0` then `0`. Second activity query excludes its own PID.

## C7 — two unkeyed POSTs

```powershell
$unkeyedProbe='din4-unkeyed-'+[guid]::NewGuid().ToString('N')
$u1=Send-Job ([ordered]@{type='sleep';payload=@{probe=$unkeyedProbe}})
$u2=Send-Job ([ordered]@{type='sleep';payload=@{probe=$unkeyedProbe}})
$u1b=$u1.Content | ConvertFrom-Json
$u2b=$u2.Content | ConvertFrom-Json
if ($u1.StatusCode -ne 202 -or $u2.StatusCode -ne 202) { throw 'unkeyed POST rejected' }
if ($u1b.job_id -eq $u2b.job_id) { throw 'unkeyed requests collapsed' }
$q=@"
select id,status,idempotency_key,request_fingerprint,payload
from jobs where payload->>'probe'='$unkeyedProbe' order by id;
select count(*) from jobs where payload->>'probe'='$unkeyedProbe'
 and idempotency_key is null and request_fingerprint is null;
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw 'unkeyed proof failed' }
"unkeyed_ids=$($u1b.job_id),$($u2b.job_id)"
```

Expected two distinct pending rows; second count `2`; both key/fingerprint `NULL`.

## C8 — heartbeat-safe execute regression + guaranteed gate cleanup

Prepare Worker A, Reaper, and Worker B terminals with this command, but start only when prompted:

```powershell
$env:DATABASE_URL='postgresql+asyncpg://postgres:relay@localhost:5433/relay'
.\.venv\Scripts\python.exe -u -m src.worker
# Reaper and Worker B terminals bhi same DATABASE_URL set karein.
# Reaper terminal uses: .\.venv\Scripts\python.exe -u -m src.reaper
```

Main terminal runs this whole block. `Read-Host` prompts coordinate manual terminals; `finally` is load-bearing:

```powershell
$fixtureIds=[long[]]@($seqJobId,$raceJobId,[long]$u1b.job_id,[long]$u2b.job_id)
if (@($fixtureIds | Sort-Object -Unique).Count -ne 4) { throw "fixture IDs not four distinct values: $fixtureIds" }
$fixtureCsv=($fixtureIds -join ',')
$preGate=[int](Read-Scalar "select count(*) from jobs where id in ($fixtureCsv) and status='pending' and next_attempt_at is null;")
if ($preGate -ne 4) { throw "exact fixtures not pending/null: matched=$preGate ids=$fixtureCsv" }
if ([int](Read-Scalar "select count(*) from jobs where next_attempt_at='infinity'::timestamptz;") -ne 0) { throw 'pre-existing infinity gate' }

$execKey='din4-exec-'+[guid]::NewGuid().ToString('N')
$execJobSeqBefore=[long](Read-Scalar 'select last_value from jobs_id_seq;')
$effectSeqBefore=[long](Read-Scalar 'select last_value from side_effects_id_seq;')
$execResponse=Send-Job ([ordered]@{type='effect';payload=@{seconds=45;block=$true};idempotency_key=$execKey})
if ($execResponse.StatusCode -ne 202) { throw 'execution fixture enqueue failed' }
$execId=[long](($execResponse.Content | ConvertFrom-Json).job_id)
$execJobSeqAfter=[long](Read-Scalar 'select last_value from jobs_id_seq;')

try {
  $returned=@("update jobs set next_attempt_at='infinity'::timestamptz where id in ($fixtureCsv) and status='pending' and next_attempt_at is null returning id;" |
    docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay |
    Where-Object { $_ -match '^\d+$' } | ForEach-Object { [long]$_.Trim() })
  if ((@($returned | Sort-Object) -join ',') -ne (@($fixtureIds | Sort-Object) -join ',')) { throw "gate mismatch expected=$fixtureIds returned=$returned" }
  if ([int](Read-Scalar "select count(*) from jobs where id in ($fixtureCsv) and next_attempt_at='infinity'::timestamptz;") -ne 4) { throw 'four-row gate not durable' }

  Read-Host "Start Worker A. Target $execId must print rowcount=1 and 'Blocking event loop (45.0s)'. Then press Enter; do NOT start reaper/B yet"
  $aReady=[int](Read-Scalar "select count(*) from jobs j where j.id=$execId and j.status='running' and j.attempts=1 and (select count(*) from job_executions e where e.job_id=j.id)=1 and (select count(*) from side_effects s where s.job_id=j.id)=1;")
  if ($aReady -ne 1) { throw 'Worker A durable precondition not met' }
  $aged=[int](Read-Scalar "with u as (update jobs set claimed_at=now()-interval '31 seconds' where id=$execId and status='running' and attempts=1 returning id) select count(*) from u;")
  if ($aged -ne 1) { throw 'target age update did not match once' }

  Read-Host "Start reaper. Wait for id=$execId matched=1 post_status=pending, then press Enter"
  $deadline=[DateTime]::UtcNow.AddSeconds(12)
  do {
    $barrier=Read-Scalar "select status||'|'||attempts||'|'||(claimed_at is null)::text from jobs where id=$execId;"
    if ($barrier -eq 'pending|1|true') { break }
    Start-Sleep -Milliseconds 200
  } while ([DateTime]::UtcNow -lt $deadline)
  if ($barrier -ne 'pending|1|true') { throw "reclaim did not commit: $barrier" }
  "reclaim_committed_barrier=$barrier"

  Read-Host "Ctrl+C reaper and wait clean exit. Ctrl+C Worker A once while it is still blocking. Start Worker B; wait for attempt=2, rowcount=0, and Blocking line; then press Enter"
  $bReady=[int](Read-Scalar "select count(*) from jobs j where j.id=$execId and j.status='running' and j.attempts=2 and (select count(*) from job_executions e where e.job_id=j.id)=2 and (select count(*) from side_effects s where s.job_id=j.id)=1;")
  if ($bReady -ne 1) { throw 'Worker B durable precondition not met' }

  Read-Host "Ctrl+C Worker B once. Wait for both workers clean exit; preserve zero heartbeat lines plus mark rowcounts; then press Enter"
  $finalOk=[int](Read-Scalar "select count(*) from jobs j where j.id=$execId and j.status='succeeded' and j.attempts=2 and (select count(*) from job_executions e where e.job_id=j.id)=2 and (select count(distinct e.worker_id) from job_executions e where e.job_id=j.id)=2 and (select count(*) from side_effects s where s.job_id=j.id)=1;")
  if ($finalOk -ne 1) { throw 'execute regression final matrix failed' }
  $effectSeqAfter=[long](Read-Scalar 'select last_value from side_effects_id_seq;')
  $q=@"
select j.id,j.status,j.attempts,j.idempotency_key,
 count(distinct e.id) as executions,count(distinct e.worker_id) as workers,count(distinct s.id) as effects
from jobs j left join job_executions e on e.job_id=j.id left join side_effects s on s.job_id=j.id
where j.id=$execId group by j.id,j.status,j.attempts,j.idempotency_key;
select id,effect_key,worker_id from side_effects where job_id=$execId;
"@
  $q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
  "exec_job_sequence: before=$execJobSeqBefore after=$execJobSeqAfter delta=$($execJobSeqAfter-$execJobSeqBefore)"
  "exec_effect_sequence: before=$effectSeqBefore after=$effectSeqAfter delta=$($effectSeqAfter-$effectSeqBefore)"
} finally {
  Read-Host 'Failure or success cleanup barrier: stop any Worker/Reaper still live, then press Enter to release only the exact four fixture IDs'
  $releasedOutput=@("update jobs set next_attempt_at=null where id in ($fixtureCsv) and next_attempt_at='infinity'::timestamptz returning id;" |
    docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
  $releaseExit=$LASTEXITCODE
  if ($releaseExit -ne 0) { throw 'exact gate reset failed' }
  $released=@($releasedOutput | Where-Object { $_ -match '^\d+$' } | ForEach-Object { [long]$_.Trim() })
  if ((@($released | Sort-Object) -join ',') -ne (@($fixtureIds | Sort-Object) -join ',')) {
    throw "gate release mismatch expected=$fixtureIds released=$released"
  }
  $exactRemaining=[int](Read-Scalar "select count(*) from jobs where id in ($fixtureCsv) and next_attempt_at='infinity'::timestamptz;")
  $globalRemaining=[int](Read-Scalar "select count(*) from jobs where next_attempt_at='infinity'::timestamptz;")
  "gate_reset_ids=$(@($released | Sort-Object) -join ',') exact_remaining=$exactRemaining global_remaining=$globalRemaining"
  if ($exactRemaining -ne 0 -or $globalRemaining -ne 0) { throw 'infinity gate survived cleanup' }
}
```

Expected: exact four gated/reset; target `succeeded`, attempts/executions/workers/effects `2/2/2/1`; effect stdout `{1,0}`; reaper `matched=1` plus committed `pending|1|true`; **zero target heartbeat lines**; gate cleanup `0/0`. Do not call the run passing if reclaim barrier or heartbeat evidence is absent.

## C9 — closing reconciliation and cleanup

Stop API with `Ctrl+C`, wait clean exit, then:

```powershell
.\.venv\Scripts\python.exe -m py_compile src\main.py src\schemas.py src\models.py src\worker.py src\reaper.py alembic\versions\w3d4_enqueue_idempotency_add_enqueue_idempotency.py
if ($LASTEXITCODE -ne 0) { throw 'closing compile failed' }
git diff HEAD --check
if ($LASTEXITCODE -ne 0) { throw 'diff check failed' }
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'cached diff check failed' }
git status --short

$q=@"
select status,count(*) from jobs group by status order by status;
select count(*) as jobs,max(id) as max_id from jobs;
select last_value as jobs_sequence from jobs_id_seq;
select count(*) as executions from job_executions;
select count(*) as effects from side_effects;
select last_value as effects_sequence from side_effects_id_seq;
select version_num from alembic_version;
select id,type,status,attempts,idempotency_key,request_fingerprint from jobs
 where idempotency_key in ('$seqKey','$raceKey','$execKey') order by id;
select id,status,idempotency_key,request_fingerprint,payload from jobs
 where payload->>'probe'='$unkeyedProbe' order by id;
select count(*) from pg_trigger where tgname in ('din4_hold_race_insert_trigger','din4_force_unrelated_integrity_trigger') and not tgisinternal;
select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname in ('din4_hold_race_insert','din4_force_unrelated_integrity');
select count(*) from jobs where next_attempt_at='infinity'::timestamptz;
select count(*) from pg_stat_activity
 where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
"@
$q | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d relay
if ($LASTEXITCODE -ne 0) { throw 'closing SQL failed' }

$probeDbs=@("select count(*) from pg_database where datname like 'relay_din4_catalog_%' or datname like 'relay_din4_lifecycle_%';" |
  docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d postgres)
"remaining_probe_dbs=$(($probeDbs -join '').Trim())"
$relay=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'uvicorn|src\.(worker|reaper)' })
"relay_processes=$($relay.Count)"
$relay | Select-Object ProcessId,CommandLine
"powershell_jobs=$(@(Get-Job).Count)"
Get-FileHash docs\daily\week_03\DIN_04_PREDICTIONS_FROZEN.md -Algorithm SHA256
```

Clean first run expected:

```text
dead_letter 3
failed 15
pending 4
succeeded 97
jobs 119
executions 107
effects 9
revision w3d4_enqueue_idempotency
trigger objects 0
function objects 0
infinity rows 0
idle transactions 0
remaining_probe_dbs 0
relay_processes 0
powershell_jobs 0
```

`max_id`, all sequence values/deltas, IDs, response times, and concurrent winner must be recorded, not predicted. If row delta is not `+5/+2/+1`, reconcile by returned role/ID before grading.

---

# Part D — Scope guard

| Aaj tempting kya hai | Owner | Aaj karne se kya khota hai |
|---|---|---|
| Publish `D-24` in `DECISIONS.md` | **Din 6**, after same-day number grep | Din 4 input ko premature final decision/provenance bana doge |
| Outbox table/dispatcher | Week 4 | Enqueue identity and remote-delivery identity mix ho jaati hain |
| Fencing token / claim generation | Din 5 question; Week 4 build input | Client retry vs legal redispatch isolate karni hai |
| Time-based key expiry/cleanup worker | Week 4 retention | “N-hour window” without cleanup false contract hai |
| Redis idempotency cache | Month 2 / after DB evidence | Second source of truth before Postgres invariant understood |
| Auth, per-tenant key scope, multi-tenancy | Later month | Month 1 contract suddenly tenant model demand karega |
| Payload-derived automatic key | Rejected today | Legitimately identical jobs accidentally collapse ho sakti hain |
| Property/Hypothesis suite | Din 5 | Exact sequential/concurrent failure surfaces first readable rehni chahiye |
| Alembic config refactor (`P-28`) | Week 4 hardening | Today checked explicit override use karo; unrelated refactor nahi |
| Delete evidence rows / reset sequences | Never for cosmetic cleanup | Named reconciliation and sequence-gap lessons erase ho jaate hain |
