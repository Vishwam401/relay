# WEEK 6 · DIN 2 — Test lab: ek fake provider jiski failures deterministic hain, aur `P-44` ka gate

**Budget `125 min` · Layer L2 · `src/` me do cheezein: `main.py` ki ek edit (`P-44`) aur ek nayi file
`src/fake_provider.py`.** Baaki saat hashes (`worker` `0eb94373` · `reaper` `95518640` · `dispatcher` `920d0d4a` ·
`database` `fc5bde22` · `sink` `fcfc9059` · `models` `04f04f84` · `schemas` `a53e7cc8`) Step 0 = Step 5. Koi migration
nahi, koi disposable DB nahi, evidence DB `relay` pe koi write nahi.

> **Kal Relay ki log lines ne pehli baar database ki ginti se match kiya.** Aaj pehli baar Relay ke saamne ek aisa
> process khada hoga jo **apni ginti khud rakhta hai** — fake provider ka call ledger. Din 3 se Relay isi ke through
> `llm_completion` chalayega, Din 4 pe `D-11` isi ki failures classify karega, Din 5 ke teen experiments isi pe chalenge.
> **Isliye aaj ka sawaal provider nahi, caller hai:** `httpx.AsyncClient(timeout=5.0)` ko har mode kaisa dikhta hai —
> status, exception class, elapsed — aur kis mode me caller aur provider ki ginti alag ho jaati hai.
>
> Usse pehle `P-44`: `/slow-hold` ek unauthenticated, unbounded connection hold hai production module me. Faisla Week 5
> Din 4 pe ho chuka (environment-gated, `ENABLE_TEST_ROUTES=1`, `/db-ping` hatao). Aaj implement, aur **ek differential
> jo galat gate ko pass nahi hone deta** — reviewer ne teen galat implementations pe chala ke dekha hai.

**Aaj ki files** (`D-32`: BRIEF/FROZEN publish, KEY/ANSWERS Local):

| File | Kya | Kaun likhta hai |
|---|---|---|
| `labs/w6d2_gate_check.ps1` | API ko har flag value pe start karke routes ka status file me | BRIEF me diya hai — save karo |
| `labs/w6d2_provider_probe.py` | caller ka view, har mode. **Do hooks tere** (Step 2 ka design) | skeleton BRIEF me, hooks **tu** |
| `src/main.py` | `P-44` | **tu** |
| `src/fake_provider.py` | fake provider | **tu** |
| `docs/logs/WEEK_05.md` · `docs/logs/WEEK_06.md` | do `💡` own-words blocks | **tu** |
| `docs/daily/week_06/DIN_02_PREDICTIONS_FROZEN.md` | Part B ke jawab, seal — **aaj Step 0 pe hi apne commit me** | **tu** |
| `docs/daily/week_06/DIN_02_ANSWERS.md` | har step: observed + meri explanation (Beat 4). **Local** | **tu** |

Dono harness scripts reviewer ne **throwaway copies pe chala ke dekhe hain** (gate check aaj ke `main.py` pe aur teen
temp variants pe; probe ek throwaway server pe) — wo chalte hain. Tere code pe unka *output* kya hoga, wo Part B hai.

**Kal ke do record defects, aaj ka fix:**

| Kal | Aaj |
|---|---|
| `frozen_hash.txt` me chaar lines, do khaali `git_blob=`, mtime commit ke `21 s` baad | hash file **ek command** me, `2` lines, dobara kabhi nahi chhooni. Aur seal **Step 0 pe apne commit me** — experiment se pehle ka ek git record |
| `ANSWERS` ki ek hi mtime, Step 7 ke baad — *"KEY se pehle"* verify nahi hua | har step ke baad ek **trail line** (`logs\w6d2_answers_trail.txt`): time + file ka hash. KEY us line ke baad khulta hai |

---

## PART A — Steps

### Step 0 — 10 min: kal raat ka commit, bench, seal

**0a. Kal raat ke review docs + ye BRIEF — named files, `-A` kabhi nahi.**

```powershell
cd d:\PROJECTS\relay
git status --short
git add docs/DECISIONS.md docs/LEARNING_LOG.md docs/PROBLEMS.md docs/logs/WEEK_06.md docs/daily/week_06/DIN_02_BRIEF.md
git diff --cached --name-only | Out-File -Encoding utf8 logs\w6d2_step0_staged.txt
Get-Content logs\w6d2_step0_staged.txt          # exactly ye 5. Koi *_KEY.md nahi
git commit -m "docs(w6d1-review): Din 1 review, P-55/P-56/P-57 amendments, P-58, Din 2 brief"
```

`git status` me in paanch ke alawa koi aur *tracked* file `M` dikhe to use add mat karo — `ANSWERS` me ek line.
`docs/revision/` (`??`) tera hai, list me nahi.

**0b. Bench — har line file me.**

```powershell
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("head=" + (git rev-parse --short HEAD))
$o.Add("src_diff=" + @(git diff --name-only HEAD -- src/).Count)
$o.Add("src_untracked=" + @(git ls-files --others --exclude-standard -- src/).Count)
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py src/sink.py src/models.py src/schemas.py | ForEach-Object { $o.Add("hash " + $_) }
$o.Add("heads=" + ((.\.venv\Scripts\python.exe -m alembic heads 2>&1) -join ' | '))
$o.Add("relay_python=" + @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" }).Count)
$o.Add("listen_8000_8002=" + @(Get-NetTCPConnection -State Listen -LocalPort 8000, 8002 -ErrorAction SilentlyContinue).Count)
$o.Add("dbs=" + ((docker exec relay-db-1 psql -U postgres -d postgres -t -A -c "SELECT string_agg(datname, ',' ORDER BY datname) FROM pg_database WHERE NOT datistemplate;") -join ''))
$o.Add("counters=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -F '|' -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');") -join ''))
$o.Add("protected=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -c "SELECT string_agg(id || '|' || status || '|' || attempts || '|' || claim_generation, ' ; ' ORDER BY id) FROM jobs WHERE id IN (108, 128, 136);") -join ''))
$o.Add("dotenv_mentions_flag=" + @(Select-String -Path .env -SimpleMatch 'ENABLE_TEST_ROUTES').Count)
$o.Add("key_index=" + @(git ls-files -- "*_KEY.md").Count)
$o.Add("brief_control=" + @(git ls-files -- "*_BRIEF.md").Count)
$o | Out-File -Encoding utf8 logs\w6d2_step0_bench.txt
pwsh -File scripts\seal_audit.ps1 -Out logs\w6d2_step0_seals.txt
Get-Content logs\w6d2_step0_bench.txt
```

Expected (instrument, outcome nahi): `src_diff=0` · `src_untracked=0` · aath hashes `0eb94373…` (worker) `95518640…`
(reaper) `920d0d4a…` (dispatcher) `d55e3b8a…` (main) `fc5bde22…` (database) `fcfc9059…` (sink) `04f04f84…` (models)
`a53e7cc8…` (schemas) · `heads=w4d4_sink_unique (head)` · `relay_python=0` · `listen_8000_8002=0` · `dbs=postgres,relay` ·
counters `133|145|19|4|7|39|5|0|1` · `protected=108|dead_letter|4|0 ; 128|succeeded|4|4 ; 136|running|1|1` ·
`dotenv_mentions_flag=0` · `key_index=0` · `brief_control=31` · seals file me `seals=17 … blocked=0`.

`dotenv_mentions_flag` aaj ka naya premise hai: `.env` me flag likha ho to *"unset"* wala arm unset nahi rehta (Part B
`Q1(b)`). `0` nahi aaya to ruk jao aur `ANSWERS` me likho.

**0c. Seal — Part B ke jawab, abhi, kisi experiment se pehle.** `docs/daily/week_06/DIN_02_PREDICTIONS_FROZEN.md`: har
sub-part ka alag jawab. **`[padh ke]` sub-part me likho kya padha (file:line)** — tag dohraana *"kya padha"* nahi hai
(kal ke gyarah `idk` isi wajah se reading gap gine gaye). Phir **ek command**, aur ye file dobara kabhi nahi:

```powershell
$f = "docs\daily\week_06\DIN_02_PREDICTIONS_FROZEN.md"
@(("sha256=" + (Get-FileHash -Algorithm SHA256 $f).Hash), ("git_blob=" + (git hash-object $f))) | Out-File -Encoding utf8 logs\w6d2_step0_frozen_hash.txt
git add docs/daily/week_06/DIN_02_PREDICTIONS_FROZEN.md
git commit -m "seal(w6d2): Din 2 predictions frozen before any experiment"
"head_blob=" + (git rev-parse "HEAD:docs/daily/week_06/DIN_02_PREDICTIONS_FROZEN.md") | Out-File -Encoding utf8 logs\w6d2_step0_seal_commit.txt
"seal_commit_time=" + (git log -1 --format=%cI) | Out-File -Append -Encoding utf8 logs\w6d2_step0_seal_commit.txt
Get-Content logs\w6d2_step0_frozen_hash.txt, logs\w6d2_step0_seal_commit.txt
```

`git_blob` = `head_blob` hona chahiye. Seal ka apna commit kyun: kal *"frozen before the run"* sirf ek mtime pe tika tha,
jo badla ja sakta hai. Ek commit jo pehle experiment se pehle bana, wo ek doosra record hai — local hai, isliye
**attested nahi, narrowed** (`P-47`).

**0d. `DIN_02_ANSWERS.md`** banao — har step ka heading, aur har heading ke neeche do line: `Observed:` (file + value)
aur `Meri explanation (KEY se pehle):`. **Har step ki do line likhne ke baad, KEY kholne se pehle**, ye ek line:

```powershell
"step=<N> at=" + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff') + " sha=" + (Get-FileHash -Algorithm SHA256 docs\daily\week_06\DIN_02_ANSWERS.md).Hash.Substring(0, 12) | Out-File -Append -Encoding utf8 logs\w6d2_answers_trail.txt
```

**Executable end:** `w6d2_step0_staged.txt` (5) · commit · `w6d2_step0_bench.txt` · `w6d2_step0_seals.txt` ·
`w6d2_step0_frozen_hash.txt` (**exactly 2** lines, koi line `=` pe khatam nahi) · seal commit ·
`w6d2_step0_seal_commit.txt`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `git rev-parse HEAD:<path>` | commit me jo blob hai uska id; working copy nahi dekhta |
| `%cI` | `git log` format: committer date, ISO 8601 |
| trail line | ek append-only line jo ek moment pe file ka hash pakadti hai. Baad me file badli to hash alag |

---

### Step 0.5 — 15 min: do `💡`, apne shabdon me — Week 5 Din 6 aur Week 6 Din 1

Dono `💡` reviewer ke likhe hain: `docs/logs/WEEK_05.md` Din 6 (`### 💡 What the session established` `~1951`) aur
`docs/logs/WEEK_06.md` Din 1 (`~308`). **Ye step cut nahi hota** — plan ka rule: kal ka `💡` aaj, taaki debt jama na ho.

**Procedure, har block (kal wala hi):**

1. Us din ka `📊 Measured / Observed` padho (Week 5 Din 6 `~1812`, Week 6 Din 1 `~47`). **`💡` section mat padho.**
2. Reviewer ke section ke **upar**: `### 💡 What I understood — own words, <aaj ki asli date>`. Teen se paanch points,
   har point me ek number ya ek file. **Date wo jis din likh raha hai** — kal ki headings plan ki date carry kar rahi thi
   (Din 1 correction #8).
3. **Ab** reviewer ka section padho. Uske upar, apne block ke theek neeche, ek line: `Gaps vs reviewer: …`
4. Reviewer section mitao mat.

**Executable end** — check section ke andar ginta hai, poori file me nahi (kal ka `gaps_lines=6` ek purani line gin raha
tha):

```powershell
$r = [System.Collections.Generic.List[string]]::new()
foreach ($spec in @(@('docs\logs\WEEK_05.md', '^## Din 6 '), @('docs\logs\WEEK_06.md', '^## Din 1 '))) {
  $f = $spec[0]; $lines = @(Get-Content $f)
  $din = ($lines | Select-String -Pattern $spec[1] | Select-Object -First 1).LineNumber
  $next = ($lines | Select-String -Pattern '^## Din ' | Where-Object { $_.LineNumber -gt $din } | Select-Object -First 1).LineNumber
  if (-not $next) { $next = $lines.Count + 1 }
  $in = { param($m) $m.LineNumber -gt $din -and $m.LineNumber -lt $next }
  $own = @($lines | Select-String -Pattern '^### 💡 What I understood — own words' | Where-Object { & $in $_ })
  $gap = @($lines | Select-String -Pattern '^Gaps vs reviewer:' | Where-Object { & $in $_ })
  $rev = @($lines | Select-String -Pattern '^### 💡 What the session established' | Where-Object { & $in $_ })
  $order = ($own.Count -eq 1 -and $gap.Count -eq 1 -and $rev.Count -eq 1 -and $own[0].LineNumber -lt $gap[0].LineNumber -and $gap[0].LineNumber -lt $rev[0].LineNumber)
  $r.Add("$f section_from=$din own=$($own.Count) gaps=$($gap.Count) rev=$($rev.Count) order_own_gaps_rev=$order")
  $r.Add("$f file_total own=" + @($lines | Select-String -Pattern '^### 💡 What I understood — own words').Count + ' gaps=' + @($lines | Select-String -Pattern '^Gaps vs reviewer:').Count + ' rev=' + @($lines | Select-String -Pattern '^### 💡 What the session established').Count)
}
$r | Out-File -Encoding utf8 logs\w6d2_step05_rewrites.txt
Get-Content logs\w6d2_step05_rewrites.txt
```

Aaj se pehle `[MEASURED-R 2026-10-02]`: dono sections `own=0 gaps=0 rev=1 order_own_gaps_rev=False`; file totals
`WEEK_05` `5 · 5 · 6`, `WEEK_06` `0 · 0 · 1`. Step ke baad: dono sections `own=1 gaps=1 rev=1 order_own_gaps_rev=True`;
totals `6 · 6 · 6` aur `1 · 1 · 1`. Trail line `step=0.5`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| recall vs recognition | bina dekhe likh paana recall; padh ke *"haan yahi"* kehna recognition. Order isi liye hai |
| section-scoped count | sirf us din ke `## Din N` heading se agle `## Din` tak ginna |

---

### Step 1 — 20 min (`5` + `15`): `P-44` — gate, `/db-ping` hatao, flag startup pe dikhe

**Pehle `P-44` padho** — `docs/PROBLEMS.md` original card (`~1760`) aur Week 5 Din 4 amendment (`~2681`). Decision wahan
likha hai: option (b), environment-gated, *"test routes register only when `ENABLE_TEST_ROUTES=1`"*, `/health` aur
`/healthz` rahte hain, `/db-ping` jaata hai. Reviewer note (a): *"flag ki value ek premise hai … start-up pe observable
honi chahiye."*

**1a — 5 min: control, aaj ke `main.py` pe.** `labs/w6d2_gate_check.ps1` save karo:

```powershell
# labs/w6d2_gate_check.ps1 -- Week 6 Din 2, Step 1 (P-44).
# Starts the API (src.main:app) once per value of ENABLE_TEST_ROUTES and records what each route answers.
# Read-only against the evidence DB: /healthz runs SELECT 1, /slow-hold is called with seconds=0.
# Usage: pwsh -File labs\w6d2_gate_check.ps1 -Phase control   (today's main.py, before the edit)
#        pwsh -File labs\w6d2_gate_check.ps1 -Phase fixed     (after the Step 1 edit)
# Every line it writes is a value or a label. It writes no conclusions (P-52).
param(
  [Parameter(Mandatory = $true)][ValidatePattern('^[a-z]+$')][string]$Phase,
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
  [string]$OutDir = '',
  [int]$Port = 8000
)
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
Set-Location $RepoRoot
if ($OutDir -eq '') { $OutDir = Join-Path $RepoRoot 'logs' }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$run = "w6d2_gate_${Phase}_" + (Get-Date -Format 'yyyyMMdd_HHmmss_ffffff')
$py  = (Resolve-Path (Join-Path $RepoRoot '.venv\Scripts\python.exe')).Path
$B   = "http://127.0.0.1:$Port"
$out = Join-Path $OutDir "${run}_census.txt"

function Hit([string]$method, [string]$path) {
  try { return [string][int](Invoke-WebRequest -Method $method -Uri ($B + $path) -TimeoutSec 10 -SkipHttpErrorCheck).StatusCode }
  catch { return 'ERR:' + $_.Exception.GetType().Name }
}
function Sweep {
  foreach ($c in @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like "*$RepoRoot*" -and $_.CommandLine -match 'src\.main:app' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

if (@(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue).Count -ne 0) { throw "port $Port already has a listener -- stop it first" }
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("run_id=$run")
$o.Add("main_hash=" + (git hash-object src/main.py))
$o.Add("src_diff_files_vs_HEAD=" + ((git diff --name-only HEAD -- src/) -join ','))
$o.Add("dotenv_mentions_flag=" + @(Select-String -Path (Join-Path $RepoRoot '.env') -SimpleMatch 'ENABLE_TEST_ROUTES' -ErrorAction SilentlyContinue).Count)
$saved = @{}
foreach ($k in 'ENABLE_TEST_ROUTES', 'RELAY_PROCESS_NAME', 'PYTHONUNBUFFERED') { $saved[$k] = [Environment]::GetEnvironmentVariable($k) }
$env:PYTHONUNBUFFERED = '1'
$arms = @(@('unset', $null), @('empty', ''), @('zero', '0'), @('true', 'true'), @('garbage', 'banana'), @('one', '1'))
try {
  foreach ($a in $arms) {
    $name = $a[0]
    if ($null -eq $a[1]) { Remove-Item Env:ENABLE_TEST_ROUTES -ErrorAction SilentlyContinue } else { $env:ENABLE_TEST_ROUTES = $a[1] }
    $env:RELAY_PROCESS_NAME = "api_w6d2_$name"
    $log = Join-Path $OutDir "${run}_${name}_api.log"
    $p = Start-Process -FilePath $py -ArgumentList '-u', '-m', 'uvicorn', 'src.main:app', '--host', '127.0.0.1', '--port', "$Port" `
         -WorkingDirectory $RepoRoot -PassThru -NoNewWindow -RedirectStandardOutput $log -RedirectStandardError "$log.err"
    $null = $p.Handle
    $up = $false
    for ($i = 0; $i -lt 40 -and -not $up -and -not $p.HasExited; $i++) {
      if ((Hit 'GET' '/health') -eq '200') { $up = $true } else { Start-Sleep -Milliseconds 300 }
    }
    if ($up) {
      $paths = @((Invoke-RestMethod -Uri "$B/openapi.json" -TimeoutSec 5).paths.PSObject.Properties.Name)
      $line = "arm=$name listening=True health=" + (Hit 'GET' '/health') + ' healthz=' + (Hit 'GET' '/healthz') +
              ' slow_hold_get=' + (Hit 'GET' '/slow-hold?seconds=0') + ' slow_hold_post=' + (Hit 'POST' '/slow-hold?seconds=0') +
              ' db_ping=' + (Hit 'GET' '/db-ping') +
              ' openapi_slow_hold=' + @($paths | Where-Object { $_ -eq '/slow-hold' }).Count +
              ' openapi_db_ping=' + @($paths | Where-Object { $_ -eq '/db-ping' }).Count
    }
    else {
      Start-Sleep -Milliseconds 500
      $line = "arm=$name listening=False exited=" + $p.HasExited + ' exit_code=' + $(if ($p.HasExited) { $p.ExitCode } else { '-' })
    }
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    Sweep
    Start-Sleep -Milliseconds 500
    $all = @(Get-Content $log, "$log.err" -ErrorAction SilentlyContinue)
    $flag = @($all | Where-Object { $_ -match '^test_routes=' })
    $line += ' flag_lines=' + $flag.Count + ' err_mentions_flag=' + @(Get-Content "$log.err" -ErrorAction SilentlyContinue | Where-Object { $_.Contains('ENABLE_TEST_ROUTES') }).Count
    $o.Add($line)
    if ($flag.Count -gt 0) { $o.Add("arm=$name flag_line: " + $flag[0]) }
  }
}
finally {
  Sweep
  foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) }
}
$o.Add('relay_python_after=' + @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*$RepoRoot*" }).Count)
$o | Out-File -Encoding utf8 $out
Get-Content $out
```

```powershell
pwsh -File labs\w6d2_gate_check.ps1 -Phase control
```

`~40 s`. Chhe arms: `unset` · `empty` (`''`) · `zero` · `true` · `garbage` (`banana`) · `one`. Har arm ek naya API process.
`/slow-hold?seconds=0` = `pg_sleep(0)` evidence DB pe — read-only, Step 5 ke counters isko prove karte hain.

**1b — 15 min: edit, phir wahi script.**

**Pehle 3 min, ek chhota design pick (Situation 3 — Gemini se options aur cost, pick tera):** `"1"` ke alawa koi value
aaye to kya?

| Option | Shape | Cost |
|---|---|---|
| (i) **sirf exact `1` = on, baaki sab off** | ek comparison | typo (`ture`, `yes`) chupchaap off — test routes nahi milte, par production me kuch khulta nahi |
| (ii) **`1` on, unset/`''`/`0` off, baaki pe start hi mat ho** | allowlist + startup error | misconfig ka pata pehle second me; par ek galat env value ab API ko start nahi hone deti — availability ka cost |
| (iii) **truthy set** (`1`, `true`, `yes`, …) | set membership | convenience; kaunsi value on hai, ye ek list yaad rakhni padti hai, aur list badhti hai |

Pick + ek line cost `ANSWERS` me. `P-44` ka text *"`ENABLE_TEST_ROUTES=1`"* kehta hai — (iii) chuno to wo bhi likho.

**Rules, pick jo bhi ho:**

1. **Test route sirf flag on hone pe register ho.** Handler ke andar *"flag off hai to 404 raise karo"* register-time gate
   nahi hai — route phir bhi app me hai. Part C isko pakadta hai.
2. **`/db-ping` delete.** `/health` aur `/healthz` bilkul untouched.
3. **Flag ki state startup pe ek baar print**, line `test_routes=` se shuru (ye prefix grep contract hai — script isi ko
   ginta hai), aur usme **raw value** bhi ho (`repr`), sirf on/off nahi. `flush=True`.
4. **`/slow-hold` ka handler body wahi.** `seconds` ka cap (`P-44` reviewer note (b)) chuna nahi gaya — aaj nahi.
5. Middleware, `/jobs`, `get_db` — kuch nahi badalta.

Flag kahan padhna hai (file me kis line pe), tera faisla — uska asar Part B `Q1(b)` hai.

```powershell
.\.venv\Scripts\python.exe -m py_compile src\main.py; "py_compile_exit=$LASTEXITCODE" | Out-File -Encoding utf8 logs\w6d2_step1_edit.txt
git diff --stat -- src/ | Out-File -Append -Encoding utf8 logs\w6d2_step1_edit.txt
"db_ping_mentions=" + @(Select-String -Path src\main.py -SimpleMatch 'db-ping').Count | Out-File -Append -Encoding utf8 logs\w6d2_step1_edit.txt
pwsh -File labs\w6d2_gate_check.ps1 -Phase fixed
$c = Get-ChildItem logs -Filter 'w6d2_gate_control_*_census.txt' | Sort-Object Name | Select-Object -Last 1
$x = Get-ChildItem logs -Filter 'w6d2_gate_fixed_*_census.txt' | Sort-Object Name | Select-Object -Last 1
@("control=" + $c.Name) + (Get-Content $c.FullName) + @("fixed=" + $x.Name) + (Get-Content $x.FullName) | Out-File -Encoding utf8 logs\w6d2_step1_both.txt
Get-Content logs\w6d2_step1_edit.txt, logs\w6d2_step1_both.txt
```

`labs/w5d4_pool_probe.py` `/slow-hold` pe chalta hai — aage kabhi chalana ho to flag on karke. Ek line `ANSWERS` me.

**Executable end:** `w6d2_step1_edit.txt` (`py_compile_exit=0`, diff me sirf `src/main.py`, `db_ping_mentions=0`) ·
`w6d2_step1_both.txt` (do census, chhe-chhe arms). Trail line `step=1`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| environment variable | process ko start pe mila key=value; child process parent ka copy leta hai |
| `.env` + `load_dotenv()` | `src/database.py:2–4` file ki lines ko process ke environment me daalta hai |
| route registration | `@app.get(...)` decorator jab *chalta* hai tab route app ki list me judta hai. Module-level decorator import pe chalta hai |
| `openapi.json` | FastAPI ka generated document — app me registered har route ki list |
| `404` / `405` | `404` = server ko is path ka koi route nahi mila · `405` = path ka route hai, par is HTTP method ke liye nahi |
| fail-fast | galat config pe process start hi na ho, taaki galti chhupe nahi |

---

### Step 2 — 15 min: fake provider ka design (Situation 3) — aur design probe ke hook me utarta hai

**Gemini se options aur unke cost, kabhi pick nahi.** Teen faisle, phir paanch line `ANSWERS` me.

**Faisla 1 — ek request apna failure mode kaise chunti hai?**

| Option | Kya milta hai | Cost |
|---|---|---|
| (A) **request body ka field** (jaise `"mode": "429"`) | har request apna mode le ke aati hai; ek run me saare modes; parallel requests ek doosre ko nahi chhoote | test knob provider ke request schema me baith jaata hai. Din 3 ka `complete(prompt, params)` use `params` me le jaayega → job ke `payload` (jsonb) me, aur `echo=True` har SQL parameter log karta hai. Real provider ko wahi field = unknown field |
| (B) **request header** (jaise `X-Fake-Mode`) | body saaf; per-request, parallel-safe | Din 3 ke interface ko headers pass karne ka rasta chahiye. Header Relay ki DB me kahin record nahi — kis mode ne job giraayi, baad me sirf provider ke log se |
| (C) **server-wide mode** (start pe env/CLI, ya ek admin route) | Relay ka code bilkul real provider jaisa; Din 5 ka `429` storm (*"provider sabke liye down"*) isi shakal ka hai | ek waqt pe ek mode. Aaj ka probe ek run me 11 labels bhejta hai → 11 restarts, ya ek **admin route** — ek aur unauthenticated control endpoint, `P-44` ki shakal. Probe ka `request_for()` us case me kaafi nahi, ek teesra hook chahiye |
| (D) **scripted sequence per key** (jaise key `job-7` → `500, 500, ok`) | *"do baar fail, phir success"* — Din 4 ke retry/`D-11` experiments yahi chahte hain | sabse zyada state: script kahan se aata hai, key kya hai (job id? attempt?), reset kab, restart pe script gaya. Key retries ke across stable rehni chahiye |

Combination allowed hai. Din 4 Step 5 ko *seeded* `30%` `500` chahiye — jo bhi chuno, use rokna nahi chahiye.

**Faisla 2 — provider-side ledger kahan rehta hai?**

| Option | Kya milta hai | Cost |
|---|---|---|
| (i) **memory counter + ek read route** | sasta; probe seedha padh leta hai | restart = `0`; process-local (`--workers 2` = do ledgers); read route khud ek request hai — counter agar *har request* ginta hai to apni reads bhi ginega |
| (ii) **har call pe ek append-only log line** | restart ke baad bhi file; Relay ke log-evidence style se match; grep contract | ginti ke liye parse; aur Din 1 wala sawaal — line kis moment ka record hai (request aate hi? response ke baad?) |
| (iii) **Postgres table** | durable; Relay ki `jobs` se join — Din 5 Arm C (*provider ne bill kiya, Relay ne record nahi kiya*) ek query | fake provider ab DB pe depend — DB outage provider ka behaviour badalta hai. **Aaj migration aur evidence DB pe write, dono Part D me bahar hain**; to aaj iska matlab ek alag DB ya kal tak ruko |

**Faisla 3 — counter request ke raaste me kahan baithta hai, yaani wo *kya* ginta hai?** Middleware (har HTTP request jo
server tak pahunchi) · handler ki pehli line (jo validate hokar handler tak aayi) · response bhejne ke baad (jinka jawab
gaya). Har jagah ek alag sawaal ka jawab hai: *"kitni calls aayi"*, *"kitni process hui"*, *"kitni ka jawab gaya"*. Part B
`Q4` isi pe hai.

**`ANSWERS` me paanch line:** (1) trigger pick + cost · (2) ledger pick + cost · (3) counter position + wo kya ginta hai ·
(4) deterministic token rule (*same prompt → same `tokens_in`, lamba prompt → alag*; jaise word count) · (5) `hang` ki do
shakal request kaise chunegi (Step 3b).

**Executable end — design ek function me.** `labs/w6d2_provider_probe.py` save karo, aur **sirf HOOK 1**
(`request_for`) apne Faisla 1 se bharo. HOOK 2 Step 3a me.

```python
r"""labs/w6d2_provider_probe.py -- Week 6 Din 2, Step 4: the fake provider as the CALLER sees it.
One httpx.AsyncClient(timeout=5.0), calls strictly one at a time. Pass 1 posts once per label and records status,
exception class, str(exc), elapsed, Retry-After, and the provider's own ledger before and after the call. Pass 2
streams three labels to record when the response headers arrived and the largest gap between body chunks.
Prints values only; it writes no conclusions (P-52).
Usage: .\.venv\Scripts\python.exe -u labs\w6d2_provider_probe.py                 (every label + both passes)
       .\.venv\Scripts\python.exe -u labs\w6d2_provider_probe.py ok ok_repeat   (only these labels, pass 1 only)
The TWO HOOKS marked below depend on your Step 2 design and are yours to fill in. Nothing else needs editing."""
import asyncio
import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8002"
TIMEOUT = 5.0
SLOW_BELOW_S = 3.0  # provider waits this long before answering: below the client timeout
SLOW_ABOVE_S = 7.0  # and this long: above it
PROMPT = "the quick brown fox"
LONGER = "the quick brown fox jumps over the lazy dog again and again"
LABELS = ["ok", "ok_repeat", "ok_longer", "429", "500", "400", "401", "slow_below", "slow_above", "hang", "trickle"]
STREAM_LABELS = ["slow_below", "hang", "trickle"]


# ---------------------------------------------------------------------------------------------------------------
# HOOK 1 (yours): how ONE request selects ONE mode. Return (headers, json_body).
#   - every body carries a prompt: PROMPT, except "ok_longer" which carries LONGER
#   - "ok" and "ok_repeat" must be byte-identical requests
#   - "slow_below" / "slow_above" must make the provider wait SLOW_BELOW_S / SLOW_ABOVE_S before it answers
def request_for(label: str) -> tuple[dict, dict]:
    raise NotImplementedError("fill request_for() from your Step 2 trigger design")


# HOOK 2 (yours): the provider's OWN total call count, from YOUR ledger (an endpoint, a log file, or a table).
async def read_ledger(client: httpx.AsyncClient) -> int:
    raise NotImplementedError("fill read_ledger() from your Step 2 ledger design")
# ---------------------------------------------------------------------------------------------------------------


async def post_once(client, label, headers, body=None, content=None):
    before = await read_ledger(client)
    t = time.perf_counter()
    status, exc, msg, ra, text = "-", "none", "", None, ""
    try:
        if content is not None:
            r = await client.post(f"{BASE}/v1/complete", headers=headers, content=content)
        else:
            r = await client.post(f"{BASE}/v1/complete", headers=headers, json=body)
        status, ra, text = str(r.status_code), r.headers.get("retry-after"), r.text
    except Exception as e:  # recorded, not handled: the class IS the measurement
        exc, msg = type(e).__name__, str(e)
    elapsed = time.perf_counter() - t
    after = await read_ledger(client)
    print(f"label={label} status={status} exc={exc} str={msg!r} elapsed={elapsed:.3f} retry_after={ra!r} "
          f"ledger_delta={after - before} body={text.strip()[:70]!r}", flush=True)
    return text


async def stream_once(client, label):
    headers, body = request_for(label)
    t = time.perf_counter()
    headers_at, chunks, max_gap, exc = None, 0, 0.0, "none"
    try:
        async with client.stream("POST", f"{BASE}/v1/complete", headers=headers, json=body) as r:
            headers_at = time.perf_counter() - t
            last = time.perf_counter()
            async for _ in r.aiter_raw():
                now = time.perf_counter()
                max_gap, last, chunks = max(max_gap, now - last), now, chunks + 1
    except Exception as e:
        exc = type(e).__name__
    h = "-" if headers_at is None else f"{headers_at:.3f}"
    print(f"stream label={label} headers_at={h} chunks={chunks} max_gap={max_gap:.3f} exc={exc} "
          f"total={time.perf_counter() - t:.3f}", flush=True)


def tokens(text):
    try:
        d = json.loads(text)
        return d.get("tokens_in"), d.get("tokens_out"), sorted(d.keys())
    except Exception:
        return None, None, []


async def main(selected):
    full = selected == LABELS
    sent = 0
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        print(f"timeout_repr={client.timeout!r} labels={','.join(selected)}", flush=True)
        a, b = await read_ledger(client), await read_ledger(client)
        print(f"ledger_read_stable={a == b} ledger_start={a}", flush=True)
        bodies = {}
        for label in selected:
            headers, body = request_for(label)
            bodies[label] = await post_once(client, label, headers, body)
            sent += 1
        if full:
            await post_once(client, "malformed", {"content-type": "application/json"}, content=b"{not json")
            sent += 1
            for label in STREAM_LABELS:
                await stream_once(client, label)
                sent += 1
        if all(k in bodies for k in ("ok", "ok_repeat", "ok_longer")):
            ok, rep, lon = tokens(bodies["ok"]), tokens(bodies["ok_repeat"]), tokens(bodies["ok_longer"])
            print(f"ok_keys={','.join(ok[2])} tokens_ok={ok[:2]} tokens_repeat={rep[:2]} tokens_longer={lon[:2]}", flush=True)
            print(f"tokens_same_for_same_prompt={ok[:2] == rep[:2] and ok[0] is not None} "
                  f"tokens_in_differs_for_longer_prompt={lon[0] is not None and lon[0] != ok[0]}", flush=True)
        end = await read_ledger(client)
        print(f"posts_sent={sent} ledger_end={end} ledger_total_delta={end - a}", flush=True)


if __name__ == "__main__":
    chosen = sys.argv[1:] or LABELS
    unknown = [x for x in chosen if x not in LABELS]
    if unknown:
        raise SystemExit(f"unknown label(s): {unknown}; known: {LABELS}")
    asyncio.run(main(chosen))
```

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'labs'); import w6d2_provider_probe as p; r = {l: p.request_for(l) for l in p.LABELS}; [print(l, r[l]) for l in p.LABELS]; print('labels=' + str(len(r)) + ' ok_equals_repeat=' + str(r['ok'] == r['ok_repeat']) + ' distinct_requests=' + str(len({repr(v) for v in r.values()})))" | Out-File -Encoding utf8 logs\w6d2_step2_requests.txt
Get-Content logs\w6d2_step2_requests.txt
```

Expected: 11 lines + `labels=11 ok_equals_repeat=True distinct_requests=10`. **`distinct_requests` `10` se kam** = do
alag labels ek hi request bhej rahe hain → provider unhe alag kar hi nahi sakta (Faisla 1 ka (C) yahan `2` dega — wo
galti nahi, us option ka cost hai; tab teesra hook `ANSWERS` me likho). Trail line `step=2`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| failure injection | test ke liye jaan-boojh ke ek chuni hui failure paida karna, har baar same |
| ledger | provider ka apna record ki usse kitni (aur kaunsi) calls aayi — Relay ke kisi bhi record se alag |
| middleware | har request handler se pehle (aur response ke baad) chalne wala code — `src/middleware.py` jaisa |
| deterministic | same input → same output, har run, har machine |

---

### Step 3 — 30 min (`15` + `15`): `src/fake_provider.py` — tu likhta hai

Shape `src/sink.py` jaisa: ek FastAPI app, `uvicorn` se chalta hai. **Code reviewer nahi likhega** — Gemini se
concepts/hints, code tera.

**Contract (requirement, prediction nahi):**

| | |
|---|---|
| Endpoint | `POST /v1/complete` |
| `ok` | `200` + JSON body, exactly teen keys: `text`, `tokens_in`, `tokens_out` (ints). Token rule deterministic (Step 2 line 4) |
| `429` | status `429` + `Retry-After` header, **integer seconds** (jaise `2`) |
| `500` · `400` · `401` | wahi status, chhota JSON error body |
| `slow` | request ke chune hue seconds tak ruko, phir `ok` wala hi jawab |
| `hang` — shakal 1, **silence** | na status, na header, na ek byte — kam se kam `2 × 5 s`, ya process maarne tak |
| `hang` — shakal 2, **trickle** | status `200` + headers turant, phir har `~1 s` pe ek-do bytes (har gap `< 5 s`), kul `≥ 8 s`, aur end pe body valid JSON |
| Ledger | Step 2 ka design. Probe ka HOOK 2 ise padhta hai |
| Bind | **sirf `127.0.0.1:8002`** — ye unauthenticated hai aur `hang` ek connection pakde rakhta hai (`P-44` ki shakal) |
| Startup | ek line jo port aur ledger ki shape bataye (premise, jaise `resolved_db=` hai) |
| DB | **koi nahi.** `src.database` import mat karo — wo import pe hi engine banata hai aur `resolved_db=` print karta hai |

Chalane ka tareeka (har baar same, log file ke saath):

```powershell
$env:PYTHONUNBUFFERED = '1'
$fp = Start-Process -FilePath .\.venv\Scripts\python.exe -ArgumentList '-u', '-m', 'uvicorn', 'src.fake_provider:app', '--host', '127.0.0.1', '--port', '8002' -PassThru -NoNewWindow -RedirectStandardOutput logs\w6d2_<step>_provider.log -RedirectStandardError logs\w6d2_<step>_provider.err.log
Start-Sleep -Seconds 3
# ... checks ...
Stop-Process -Id $fp.Id -Force
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'src\.fake_provider' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

(Venv ka `python.exe` ek launcher stub hai; asli interpreter child hai — isliye command-line sweep, `P-53(b)`.)

**3a — 15 min: `ok` + token rule + ledger + bind.** Phir probe ka **HOOK 2** bharo. `<step>` = `step3a`:

```powershell
# provider upar wale snippet se start karo, phir:
"listen=" + ((Get-NetTCPConnection -State Listen -LocalPort 8002 -ErrorAction SilentlyContinue | ForEach-Object { $_.LocalAddress }) -join ',') | Out-File -Encoding utf8 logs\w6d2_step3a_check.txt
.\.venv\Scripts\python.exe -u labs\w6d2_provider_probe.py ok ok_repeat ok_longer | Out-File -Append -Encoding utf8 logs\w6d2_step3a_check.txt
# provider band karo (snippet), phir:
"imports_database=" + @(Select-String -Path src\fake_provider.py -Pattern 'src\.database|from src import database').Count | Out-File -Append -Encoding utf8 logs\w6d2_step3a_check.txt
"resolved_db_lines=" + @(Select-String -Path logs\w6d2_step3a_provider.log, logs\w6d2_step3a_provider.err.log -SimpleMatch 'resolved_db=').Count | Out-File -Append -Encoding utf8 logs\w6d2_step3a_check.txt
Get-Content logs\w6d2_step3a_check.txt
```

Expected: `listen=127.0.0.1` (exactly, `0.0.0.0` ya `::` nahi) · `ledger_read_stable=True` · teeno `status=200` · har
`ledger_delta=1` · `ok_keys=text,tokens_in,tokens_out` · `tokens_same_for_same_prompt=True` ·
`tokens_in_differs_for_longer_prompt=True` · `ledger_total_delta=3` · `imports_database=0` · `resolved_db_lines=0`.

**3b — 15 min: `429`, `500`, `400`, `401`, `slow`, aur `hang` ki dono shakal.** `<step>` = `step3b`:

```powershell
# provider start, phir:
.\.venv\Scripts\python.exe -u labs\w6d2_provider_probe.py 429 500 400 401 slow_below | Out-File -Encoding utf8 logs\w6d2_step3b_check.txt
# provider band, phir:
.\.venv\Scripts\python.exe -m py_compile src\fake_provider.py; "py_compile_exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 logs\w6d2_step3b_check.txt
Get-Content logs\w6d2_step3b_check.txt
```

Expected: `status=429` ke saath `retry_after` `None` nahi · `status=500` · `status=400` · `status=401` ·
`slow_below` `status=200` aur `elapsed ≥ 3.0` · `py_compile_exit=0`. **`hang` aur `slow_above` jaan-boojh ke yahan nahi** —
unka pehla run Step 4 hai, Part B ke baad. `exc=` column bhi abhi Part B hai — jo aaye, likh lo, explanation `ANSWERS` me.

Trail lines `step=3a`, `step=3b`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `Retry-After` | response header: client ko kitni der baad dobara aana chahiye. HTTP spec me do valid forms — seconds ki integer, ya ek HTTP-date |
| `StreamingResponse` | Starlette/FastAPI ka response jo body ek generator se tukdon me bhejta hai; status aur headers pehle tukde se pehle chale jaate hain |
| `asyncio.sleep` | event loop ko chhodte hue intezaar — baaki requests is dauran chal sakti hain |
| bind address | socket kis interface pe sunta hai. `127.0.0.1` = sirf isi machine se; `0.0.0.0` = har interface |

---

### Step 4 — 25 min (`12` + `13`): caller ka view, naapa hua

**4a — 12 min: poora probe.** `<step>` = `step4`:

```powershell
# provider Step 3 wale snippet se start karo (<step> = step4), phir:
"listen=" + ((Get-NetTCPConnection -State Listen -LocalPort 8002 -ErrorAction SilentlyContinue | ForEach-Object { $_.LocalAddress }) -join ',') | Out-File -Encoding utf8 logs\w6d2_step4_bind.txt
.\.venv\Scripts\python.exe -u labs\w6d2_provider_probe.py | Out-File -Encoding utf8 logs\w6d2_step4_probe.txt
Start-Sleep -Seconds 12        # provider ko band karne se pehle: uska log run ke baad ka bhi record kare
# provider band karo (snippet), phir:
"relay_python_after=" + @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" }).Count | Out-File -Append -Encoding utf8 logs\w6d2_step4_bind.txt
Get-Content logs\w6d2_step4_bind.txt, logs\w6d2_step4_probe.txt
```

`~40 s`. Pass 1: 11 labels + ek malformed body, ek-ek karke. Pass 2: `slow_below`, `hang`, `trickle` stream ke through —
headers kab aaye, body ke tukdon ke beech sabse bada gap.

**4b — 13 min: provider ki taraf ki ginti, aur teen shaklon ki tulna.**

```powershell
$pl = 'logs\w6d2_step4_provider.log'
$o = [System.Collections.Generic.List[string]]::new()
$o.Add((Select-String -Path logs\w6d2_step4_probe.txt -Pattern '^posts_sent=').Line)
$o.Add("access_lines_post_v1_complete=" + @(Select-String -Path $pl -SimpleMatch '"POST /v1/complete HTTP/1.1"').Count)
foreach ($code in 200, 400, 401, 422, 429, 500) { $o.Add("access_$code=" + @(Select-String -Path $pl -SimpleMatch "`"POST /v1/complete HTTP/1.1`" $code ").Count) }
$o.Add("distinct_client_ports=" + @(Select-String -Path $pl -Pattern '127\.0\.0\.1:(\d+) - "POST /v1/complete' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique).Count)
$o | Out-File -Encoding utf8 logs\w6d2_step4_census.txt
Get-Content logs\w6d2_step4_census.txt
```

Uvicorn ka default access log on rehna chahiye (`--no-access-log` nahi) — ye census usi ko ginta hai.

Phir `ANSWERS` me ek table, `w6d2_step4_probe.txt` se: `slow_above` · `hang` · `trickle` — har ek ka `status`/`exc`,
`elapsed`, `ledger_delta`, stream ka `headers_at`, aur provider ke access log me line hai ya nahi. **Teen sawaal, apne
shabdon me, KEY se pehle:** caller ki taraf se kaunsi do shakal ek jaisi dikhti hain? Provider ki ginti aur caller ka
outcome kahan alag hain? `timeout=5.0` asal me kis cheez ki seema hai?

**Executable end:** `w6d2_step4_bind.txt` · `w6d2_step4_probe.txt` · `w6d2_step4_census.txt` · provider log. Trail lines
`step=4a`, `step=4b`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `httpx.Timeout(5.0)` | ek number, chaar alag timeouts: connect, read, write, pool — har ek `5 s` |
| read timeout | ek single network *read* ke liye intezaar ki seema |
| `client.stream(...)` | response ke headers milte hi block me ghuso; body tukdon me `aiter_raw()` se |
| access log | uvicorn ki har request pe ek `INFO` line (`"POST /path HTTP/1.1" 200 OK`), stdout pe |
| keep-alive | ek TCP connection pe kai requests; client port wahi rehta hai jab tak connection wahi hai |

---

### Step 5 — 10 min: close — bench, seals, commit

```powershell
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("src_status=" + ((git status --porcelain -- src/) -join ' ; '))
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py src/sink.py src/models.py src/schemas.py | ForEach-Object { $o.Add("hash " + $_) }
$o.Add("heads=" + ((.\.venv\Scripts\python.exe -m alembic heads 2>&1) -join ' | '))
$o.Add("dbs=" + ((docker exec relay-db-1 psql -U postgres -d postgres -t -A -c "SELECT string_agg(datname, ',' ORDER BY datname) FROM pg_database WHERE NOT datistemplate;") -join ''))
$o.Add("relay_python=" + @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" }).Count)
$o.Add("listen_8000_8002=" + @(Get-NetTCPConnection -State Listen -LocalPort 8000, 8002 -ErrorAction SilentlyContinue).Count)
$o.Add("counters=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -F '|' -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');") -join ''))
$o.Add("protected=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -c "SELECT string_agg(id || '|' || status || '|' || attempts || '|' || claim_generation, ' ; ' ORDER BY id) FROM jobs WHERE id IN (108, 128, 136);") -join ''))
$o.Add("key_index=" + @(git ls-files -- "*_KEY.md").Count)
$o.Add("key_tree=" + @(git ls-tree -r --name-only HEAD | Select-String -CaseSensitive "_KEY\.md").Count)
$o.Add("frozen_sha256=" + (Get-FileHash -Algorithm SHA256 docs\daily\week_06\DIN_02_PREDICTIONS_FROZEN.md).Hash)
$o.Add("frozen_git_blob=" + (git hash-object docs\daily\week_06\DIN_02_PREDICTIONS_FROZEN.md))
$sealAt = [datetimeoffset]::Parse((git log -1 --format=%cI -- docs/daily/week_06/DIN_02_PREDICTIONS_FROZEN.md))
$firstExp = Get-ChildItem logs -Filter 'w6d2_gate_control_*' | Sort-Object LastWriteTime | Select-Object -First 1
$o.Add("seal_before_first_experiment=" + ($sealAt.LocalDateTime -lt $firstExp.LastWriteTime) + " first_experiment_file=" + $firstExp.Name)
$trail = @(Get-Content logs\w6d2_answers_trail.txt)
$o.Add("trail_lines=" + $trail.Count + " trail_distinct_sha=" + @($trail | ForEach-Object { ($_ -split 'sha=')[1] } | Sort-Object -Unique).Count)
$o | Out-File -Encoding utf8 logs\w6d2_step5_bench.txt
pwsh -File scripts\seal_audit.ps1 -Out logs\w6d2_step5_seals.txt
Get-Content logs\w6d2_step5_bench.txt
```

**Commit — named files, `-A` kabhi nahi:**

```powershell
git add src/main.py src/fake_provider.py labs/w6d2_gate_check.ps1 labs/w6d2_provider_probe.py docs/logs/WEEK_05.md docs/logs/WEEK_06.md
git diff --cached --name-only | Out-File -Encoding utf8 logs\w6d2_step5_staged.txt
Get-Content logs\w6d2_step5_staged.txt
git commit -m "feat(w6d2): test routes behind ENABLE_TEST_ROUTES (P-44), fake provider with injectable failures; gate check, provider probe"
```

`DIN_02_ANSWERS.md` aur KEY list me **nahi** — dono Local, aur ignored path pe `git add` poori command fail karta hai.
`DIN_02_PREDICTIONS_FROZEN.md` bhi nahi — wo Step 0 pe apne commit me ja chuka.

---

## PART B — Prediction questions

> **Gemini ko NAHI. Step 0c pe, kisi bhi experiment se pehle, apne head se.** `[padh ke: …]` wale sub-part ka jawab repo
> me hai — pehle wo file/line kholo, aur jawab ke saath likho **kya padha** (file:line + ek line ki tune kya dekha). Us
> sub-part ka `idk` tabhi `idk` hai jab saath me likha ho kya padha; warna reading gap. `[chala ke]` wale ka `idk`
> bilkul theek hai. **`idk` sub-part level pe.** Dus sub-parts, paanch `[padh ke]`.

```text
Q1 (Step 1 se pehle — P-44)
(a) [padh ke: src/main.py:27–37] Control run (aaj ka main.py), `garbage` arm
    (ENABLE_TEST_ROUTES=banana): slow_hold_get, slow_hold_post, db_ping,
    flag_lines — chaar values, aur ek line mechanism.
(b) [padh ke: src/main.py:5 · src/database.py:1–4 ·
    .venv/Lib/site-packages/dotenv/main.py:105 aur :383–387] Fix ke baad maan
    lo `.env` me `ENABLE_TEST_ROUTES=1` likha hai. Shell me variable unset →
    gate on ya off? Shell me `0` → ? Aur kya jawab is pe depend karta hai ki
    tu main.py me flag kis line pe padhta hai?
(c) [chala ke] Fix ke baad, flag off: `POST /slow-hold` ka status? Aur ek
    galat fix ke neeche (route hamesha registered, handler ke andar 404 raise)
    wahi request? Mechanism.

Q2 (Step 3b se pehle — HTTP errors, caller ki taraf)
(a) [padh ke: src/dispatcher.py:60–99] `await client.post(...)` provider ke
    429 / 500 / 400 / 401 pe exception raise karta hai ya response lautata
    hai? Probe ka `exc=` column in chaaron ke liye kya hoga?
(b) [chala ke] `r.headers.get("retry-after")` ka Python type? Aur `int()` is
    header ke dono valid forms pe kya karta hai?

Q3 (Step 4 se pehle — timeouts)
(a) [padh ke: docs/PROBLEMS.md "P-55 — amendment (Week 6 Din 1)" (~3080) ·
    docs/logs/WEEK_06.md Din 1 ki P-55 table (~146)] `slow_above` (provider
    7 s ruk ke jawab deta hai) aur `hang`-silence: dono ke liye exc, str(exc),
    elapsed (±0.2 s). Kya caller in dono ko alag bata sakta hai?
(b) [chala ke] `trickle` (headers turant, har ~1 s ek byte, kul ≥ 8 s),
    `timeout=5.0`, non-streaming `client.post`: status ya exception? elapsed
    lagbhag? Mechanism.

Q4 (Step 4 se pehle — ledger)
(a) [padh ke: docs/DECISIONS.md:650] Malformed body (`{not json`) ka
    ledger_delta — counter handler ki pehli line pe ho to? Middleware me ho
    to? Kyun?
(b) [chala ke] `hang`-silence ka ledger_delta (client ke ReadTimeout ke BAAD
    padha gaya), counter handler ki pehli line pe maan ke. Provider ki ginti
    me ye call hai ya nahi, aur caller ke paas iska kya record hai — ek line.

Q5 (Step 4b se pehle — provider ka apna log)
(a) [chala ke] Full probe ke 15 POSTs ke liye provider ke uvicorn access log
    me `POST /v1/complete` ki kitni lines? Kaunse labels ki line nahi aayegi,
    aur kyun?
```

---

## PART C — Verification

**Har check ki ek file.** Jahan value Part B ka sawaal hai, wahan value nahi di — sirf ye ki instrument use pakadta hai.
Har row ka aakhri column: **kaunsa galat implementation is check ko pass nahi karega.**

### C0 — Step 0

| Subject | Check | Broken reading |
|---|---|---|
| `w6d2_step0_staged.txt` | exactly `5` lines, `0` `_KEY\.md` | `-A` ne kuch aur utha liya |
| `w6d2_step0_bench.txt` | Step 0b ke expected values | koi hash alag = kal raat se kuch badla; `dotenv_mentions_flag ≠ 0` = *unset* arm unset nahi |
| `w6d2_step0_seals.txt` | `seals=17 … blocked=0` | ek seal ka content badla |
| `w6d2_step0_frozen_hash.txt` | **exactly `2` lines**, koi line `=` pe khatam nahi | kal wala: khaali `git_blob=`, ya baad me append |
| `w6d2_step0_seal_commit.txt` | `head_blob` = `git_blob` | commit me kuch aur gaya, ya hash ke baad file badli |

### C1 — `P-44` (Step 1)

Premise, dono phases: `relay_python_after=0` · chhe `arm=` lines · `dotenv_mentions_flag=0`. Control: `main_hash=d55e3b8a…`,
`src_diff_files_vs_HEAD=` khaali. Fixed: `main_hash` alag, `src_diff_files_vs_HEAD=src/main.py`.

| Arm (fixed) | Required | Kaunsa galat gate pass nahi karega |
|---|---|---|
| `unset` · `empty` · `zero` | `listening=True health=200 healthz=200 slow_hold_get=404 db_ping=404 openapi_slow_hold=0 openapi_db_ping=0 flag_lines=1` | `bool(raw)` parse → `zero` on · runtime `404` inside handler → `openapi_slow_hold=1` · `/db-ping` bacha → `200` · flag print nahi → `flag_lines=0` |
| `one` | `listening=True health=200 healthz=200 slow_hold_get=200 db_ping=404 openapi_slow_hold=1 openapi_db_ping=0 flag_lines=1` | gate kabhi on nahi hota (galat naam, galat comparison) → `404`; `/db-ping` *flag ke peeche* chhupa → `db_ping=200` yahan |
| `true` · `garbage` | tere Step 1b pick ke mutabik: (i) → off arm jaisa · (ii) → `listening=False exited=True`, exit code `≠ 0`, `err_mentions_flag ≥ 1` · (iii) → `true` on arm jaisa, `garbage` off | `garbage` pe `slow_hold_get=200` = koi bhi pick nahi, truthy parse |
| har arm | `flag_line:` me raw value dikhe (`'banana'`, `''`, `None` …) | line sirf on/off kehti hai → *unset* aur *empty* alag nahi dikhte |
| har off arm | `slow_hold_post` — **Part B `Q1(c)`**, value file me, compare `ANSWERS` me | |
| `w6d2_step1_edit.txt` | `py_compile_exit=0`, diff me sirf `src/main.py`, `db_ping_mentions=0` | |

**Reviewer ne ye table teen temp variants pe chala ke dekha hai** (`%TEMP%` me `src/` ki copies — repo ka `src/` nahi chhua):
ek sahi gate, ek *runtime-refusal + `bool()`* gate, ek fail-fast gate. Galat variant `zero`, `true`, `garbage` arms aur
`openapi_slow_hold`, `db_ping` columns pe fail hua.

### C2 — Design (Step 2)

| Subject | Check | Broken reading |
|---|---|---|
| `w6d2_step2_requests.txt` | `labels=11 ok_equals_repeat=True distinct_requests=10` | do labels ek hi request → provider unhe alag nahi kar sakta |
| `ANSWERS` | paanch design lines, har ek me cost | |

### C3 — Provider (Step 3)

| Subject | Check | Kaunsa galat implementation pass nahi karega |
|---|---|---|
| `listen=` | exactly `127.0.0.1` | `--host 0.0.0.0` ya code me `0.0.0.0` |
| `ledger_read_stable` | `True` | counter apni hi read requests gin raha hai |
| `ok` / `ok_repeat` / `ok_longer` | `status=200`, `ledger_delta=1` har ek, `ledger_total_delta=3` | counter double-count (`2`) ya ginta hi nahi (`0`) |
| `ok_keys` | `text,tokens_in,tokens_out` | extra/missing key |
| tokens | `tokens_same_for_same_prompt=True` **aur** `tokens_in_differs_for_longer_prompt=True` | constant tokens (pehla pass, doosra fail) · random tokens (pehla fail) — **sirf pair dono ko pakadta hai** |
| `imports_database` · `resolved_db_lines` | `0` · `0` | provider ne `src.database` import kiya → evidence DB ka engine |
| `429` | `status=429`, `retry_after` `None` nahi | header bhoola |
| `500` · `400` · `401` | wahi status | |
| `slow_below` | `status=200`, `elapsed ≥ 3.0` aur `< 4.0` | `slow` ruka hi nahi (`~0.01 s`) |
| `exc=` column | **Part B `Q2(a)`** | |

### C4 — Caller ka view (Step 4)

| Subject | Check | Kaunsa galat implementation pass nahi karega |
|---|---|---|
| `timeout_repr` | `Timeout(timeout=5.0)` | probe badla |
| statuses | `ok*` `200` · `429` · `500` · `400` · `401` · `slow_below` `200` | |
| `stream label=hang` | `headers_at=-` aur `chunks=0` | *silence* jo headers bhej deti hai (`StreamingResponse` + lamba pehla sleep) → `headers_at` chhota |
| `stream label=trickle` | `headers_at < 1.0`, `chunks ≥ 3`, `max_gap < 5.0` | *trickle* jo `sleep(8)` karke sab ek saath bhejta hai → `headers_at ≈ 8`, `chunks=1` |
| `stream label=slow_below` | `headers_at ≥ 3.0` | `slow` jo headers pehle bhej deta hai — wo trickle hai, slow nahi |
| `slow_above` · `hang` · `trickle` — `exc`, `str`, `elapsed`, `status` | **Part B `Q3`** | |
| har `ledger_delta` | `0` ya `1`, kabhi `≥ 2`; aur jo tera Step 2 line 3 kehta hai wahi (`429`/`400`/`401` pe bhi) | design kuch kehta hai, code kuch aur karta hai |
| `malformed`, `hang` ka `ledger_delta` · `ledger_total_delta` | **Part B `Q4`** | |
| `posts_sent` | `15` | |
| `w6d2_step4_bind.txt` | `listen=127.0.0.1`, `relay_python_after=0` | provider ya uska child bacha |
| `w6d2_step4_census.txt` | saare lines maujood; `access_lines_post_v1_complete` — **Part B `Q5`** | access log band (`0` sab) |

### C5 — `💡` aur close

| Subject | Check |
|---|---|
| `w6d2_step05_rewrites.txt` | dono sections `own=1 gaps=1 rev=1 order_own_gaps_rev=True` · totals `6 · 6 · 6` aur `1 · 1 · 1` |
| `w6d2_step5_bench.txt` | `src_status= M src/main.py ; ?? src/fake_provider.py` · baaki saat hashes Step 0 jaise (main ka badla) · `heads=w4d4_sink_unique (head)` · `dbs=postgres,relay` · `relay_python=0` · `listen_8000_8002=0` · counters `133\|145\|19\|4\|7\|39\|5\|0\|1` · protected wahi · `key_index=0` · `key_tree=0` · frozen dono = Step 0 · `seal_before_first_experiment=True` · `trail_lines ≥ 7` aur `trail_distinct_sha = trail_lines` |
| `w6d2_step5_seals.txt` | `seals=18 … blocked=0` |
| `w6d2_step5_staged.txt` | exactly `6` lines, `0` KEY, `0` `ANSWERS`, `0` `PREDICTIONS_FROZEN` |

`trail_distinct_sha < trail_lines` = do steps ke beech `ANSWERS` badli hi nahi — matlab do steps ki lines ek saath likhi gayi.

### C6 — Aaj ye quote nahi honge

| Kya | Kyun |
|---|---|
| *"`P-44` closed"* | gate ek env var hai jise production me off rakhna koi enforce nahi karta; flag on pe `seconds` ab bhi unbounded (`P-44` note (b)) → `narrowed` |
| *"fake provider = real provider"* | failure shapes chune hue hain; real provider ke rate limits, partial responses, billing rules aaj naape nahi |
| *"`/slow-hold` ab safe hai"* | sirf flag off hone tak; flag on wala process wahi amplifier hai |
| *"provider calls = Relay attempts"* | aaj Relay provider ko call hi nahi karta — wo Din 3 |

---

## PART D — Scope guard

| Kya | Owner | Kyun aaj nahi |
|---|---|---|
| Provider interface `complete(prompt, params)`, fake client, **real provider** | **Din 3** | aaj sirf server; client ka shape Din 3 ka faisla hai, aur Step 2 ka trigger design usko input deta hai |
| `llm_completion` job type, result storage, Month 2 ki pehli migration | **Din 3** | aaj koi migration nahi |
| Retryable vs non-retryable classification (`D-11`), `P-51` | **Din 4** | aaj caller sirf *naapta* hai, kuch decide nahi karta |
| `429` pe retry/backoff, **`Retry-After` honour karna** | **Week 7** (Din 5 sirf naapta hai ki aaj respect hota hai ya nahi) | aaj provider header *bhejta* hai; padhne wala code nahi banta |
| Token bucket, rate limiter, Redis, `D-09` | **Week 7** | |
| Circuit breaker, fallback chain | **Month 3** | |
| Max-cost-per-job cap | **Din 4** · `job_costs`, budget → **Week 8** | |
| Seeded `30%` `500` mode | **Din 4 Step 5** | aaj ka design use rokna nahi chahiye, par aaj banta nahi |
| Tests jo fake provider use karein (`P-37`) | **Month 3** | aaj wo cheez banti hai jiske bina test likhna phir schema-only suite hota |
| Handler timeout (`D-22`), provider hang vs lease | **Din 5** (numbers) · faisla **Month 3** | aaj sirf caller ka timeout, worker nahi |
| `/slow-hold` ke `seconds` ka cap (`P-44` note (b)) | **user ka faisla**, chuna nahi gaya | aaj gate; cap ek alag option tha |
| README ka endpoint table (`/db-ping`, `/slow-hold` rows) | **Din 6 Step 3** (README pass) | aaj ke baad README ki do rows purani — `ANSWERS` me ek line |
| Fake provider ko supervisor me daalna | **nahi aaj** | wo test lab hai, Relay ka process nahi |
| Streaming LLM responses | **Month 2 me nahi** | `trickle` ek failure *shakal* hai, streaming API nahi |
| Evidence DB `relay` pe koi write, koi migration | **kabhi nahi aaj** | counters gate |
| `git push` | **user ka faisla** | push se pehle `git log --stat origin/main..HEAD` |

**Cut order, agar time khatam ho** (plan: Din 2 me `10 min` slack): pehle Step 4b ka census (`ANSWERS` table rahe, census
Din 3 Step 0.5 ke saath, DoD me `slipped`) → phir Step 4a ka stream pass (probe bina args ke chalta hai; cut = DoD me
*"dono hang shapes ka headers view"* `slipped`). **Kabhi cut nahi:** Step 0 (seal commit samet), Step 0.5, Step 1 (`P-44`
ka differential), Step 3a ka bind aur ledger checks, Step 5.

---

*Plan:* [`../../planning/WEEK_06.md`](../../planning/WEEK_06.md) · *Pichhla din:* [`DIN_01_BRIEF.md`](DIN_01_BRIEF.md) ·
*Seal:* `DIN_02_PREDICTIONS_FROZEN.md` (Step 0c pe banegi, Step 0c pe hi commit) · *Log:* [`../../logs/WEEK_06.md`](../../logs/WEEK_06.md)
