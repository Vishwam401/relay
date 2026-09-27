# WEEK 5 · DIN 5 — `2026-09-28` — Wo chain jo Din 4 dekh nahi paaya, aur `D-30` ke do gate jinke bina Din 6 close nahi kar sakta

**Budget `110 min` · Layer L2 · `src/` me aaj bhi ek line nahi badlegi — lagatar teesra din.** Aaj `labs/` me ek naya
probe banega aur `scripts/supervisor.py` badlega. Dono `src/` nahi hain, aur dono ka kaam instrument hai, feature nahi.

> **Din 4 ne din ka sabse mushkil gate saaf paar kiya aur sabse valuable step pe chuka.** `C1` — pool premise
> *observe* hui, sirf set nahi: print `pool=2+0`, `pg_stat_activity` peak `2 active`, teesra request `500`, aur engine
> ka apna `QueuePool limit of size 2 overflow 0 … timeout 3.00`. `P-45` ka gate pehli baar satisfy hua. Aur
> `/slow-hold?seconds=20` ne dikhaya ki client `3 s` pe chala jaata hai aur statement `20.025 s` chalti hai.
>
> **Par Step 5 ne jo dikhaya, wo usne naapa nahi.** *"Lock held for `7.6771 s`"* ek `Popen` → stdout-line clock tha,
> jisme `~2.6 s` sirf dispatcher ka process start tha. Lock kabhi observe nahi hua. Sink ki wait kabhi observe nahi
> hui — ek-matra snapshot dispatcher ki pehli SQL se pehle liya gaya, aur sink ka stdout ek aisi pipe me gaya jise
> kisi ne padha hi nahi. Aur holder pehle hi error ke baad rollback ho gaya, to **sirf ek dispatch attempt chala.**
> Jo measured hai: `[dispatch_error] job_id=42 outbox_id=1 error= attempts=1` — `error=` ke baad kuch nahi (`P-55`).
>
> **To aaj ka pehla half wahi chain hai, ek variable ke saath:** holder kitni der zinda rehta hai, dispatcher ke
> `5.0 s` timeout ke relative. Teen values — chhota, thoda bada, bahut bada. **Doosra half `D-30` hai:** `~30 s` ka
> DB-down run jo Din 2 ne skip kiya, teeno process supervisor ke neeche ek saath, backlog ke saath — aur usi outage
> pe `D-28` ke discriminator ka wo column jo Din 4 pe khaali raha.

---

## PART A — Steps

### Step 0 — 10 min: bench, Din 4 ka commit, aur seal — is baar hash bhi file me

**Pehle ye check: Din 4 commit hua ya nahi.** Din 4 ka frozen file aur dono probes kal raat untracked the.

```powershell
cd d:\PROJECTS\relay
(git ls-files -- docs/daily/week_05/DIN_04_PREDICTIONS_FROZEN.md labs/w5d4_pool_probe.py labs/w5d4_composed_failure.py | Measure-Object).Count | Out-File -Encoding utf8 logs\w5d5_step0_d4_tracked.txt
Get-Content logs\w5d5_step0_d4_tracked.txt        # 3 chahiye
```

**Agar `3` nahi hai, pehle Din 4 commit karo — named files, `-A` kabhi nahi.** `P-54` ki bees files aaj bhi ek gate
hain, aur `docs/month_01/daily/week_04/DIN_05_DESIGN.md` unme se ek hai (kal usme ek reviewer note juda — wo bhi
**stage nahi** hogi):

```powershell
git add docs/daily/week_05/DIN_04_PREDICTIONS_FROZEN.md labs/w5d4_pool_probe.py labs/w5d4_composed_failure.py docs/logs/WEEK_05.md docs/DECISIONS.md docs/PROBLEMS.md docs/LEARNING_LOG.md docs/daily/week_05/DIN_05_BRIEF.md
git diff --cached --name-only | Out-File -Encoding utf8 logs\w5d5_step0_staged.txt
Get-Content logs\w5d5_step0_staged.txt            # exactly ye 8 files. Koi *_KEY.md nahi, koi _ANSWERS/_DESIGN/_PROBLEM/_PROPERTY nahi
git commit -m "docs(w5d4): Din 4 review, probes, frozen seal"
```

`docs/roadmap/CURRENT_WEEK.md` aur `docs/planning/WEEK_05.md` bhi kal update hui hain, **par dono abhi bhi ignored hain**
(`.gitignore:50` `docs/roadmap/`, `.gitignore:46` `**/planning/`) — unka publish hona `D-32` ka Din 6 wala faisla hai
(`47` dangling links). **Unhe `-f` se add mat karo**; list me daalne pe `git add` exit `1` deta hai
`[MEASURED 2026-09-27, dry-run]`.

**Phir bench — har output file me:**

```powershell
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("src_diff=" + (git diff --name-only HEAD -- src/ | Measure-Object).Count)
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py src/sink.py | ForEach-Object { $o.Add("hash $_") }
$o.Add("heads=" + ((.\.venv\Scripts\python.exe -m alembic heads 2>&1) -join ' | '))
$o.Add("relay_python=" + (Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count)
$o.Add("p54=" + (git status --porcelain | Select-String -CaseSensitive "_ANSWERS\.md|_DESIGN\.md|_PROBLEM\.md|_PROPERTY\.md" | Measure-Object).Count)
$o.Add("w5d2_supervisor_log_sha256=" + (Get-FileHash -Algorithm SHA256 logs\w5d2_step4_supervisor.log).Hash)
$o | Out-File -Encoding utf8 logs\w5d5_step0_bench.txt
Get-Content logs\w5d5_step0_bench.txt
```

Expected: `src_diff=0` · chhe hashes — `a2ec8e9f…` `edcde815…` `dcdb6343…` `d55e3b8a…` `fc5bde22…` `fcfc9059…`
(chhatha `src/sink.py` hai; aaj wo bhi system ka hissa hai) · `heads=w4d4_sink_unique (head)` — **string pe assert,
exit code pe nahi** · `relay_python=0` · `p54=20` · `w5d2_supervisor_log_sha256=9ABF8EA2…5A6F`. **Aakhri line Step 5 ka
control hai** — kyun, wo Step 5 me hai.

Nau counters evidence DB `relay` pe (role `postgres`):

```powershell
docker exec relay-db-1 psql -U postgres -d relay -t -A -F "|" -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');" | Out-File -Encoding utf8 logs\w5d5_step0_counters.txt
Get-Content logs\w5d5_step0_counters.txt          # 133|145|19|4|7|39|5|0|1
```

**Seal:** `DIN_05_PREDICTIONS_FROZEN.md` likho — Part B ke paanch jawab, `idk` included — **aur hash is baar file me:**

```powershell
Get-FileHash -Algorithm SHA256 docs\daily\week_05\DIN_05_PREDICTIONS_FROZEN.md | Format-List | Out-File -Encoding utf8 logs\w5d5_step0_frozen_hash.txt
```

Din 4 pe Step 0 ka hash kisi file me nahi tha — sirf report me. Aaj wo file me hai, to Step 7 uske against compare karega,
shell variable ke against nahi.

**Executable end:** `w5d5_step0_d4_tracked.txt` me `3` (commit ke baad), bench file, counters file, frozen hash file.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| named `git add` | sirf naam li hui files stage karna. `-A` har untracked file utha leta hai — aaj unme `P-54` ki bees files hain, aur publishing one-way door hai |
| `git diff --cached --name-only` | jo files stage ho chuki hain unki list. Commit se pehle ka last check |
| `git hash-object` vs `Get-FileHash` | pehla git ka blob hash (SHA-1, content + header), doosra file ka raw SHA-256. Dono content pe bandhe hain; alag algorithms, alag numbers |
| hash-in-a-file | hash ek measurement hai. Console pe dikha hash baad me kisi cheez se compare nahi ho sakta |

---

### Step 1 — 10 min: Din 4 ke teen artifacts annotate karo, aur dono generators se prose hatao

`P-52` amendment me chhe lines ki table hai. **Wo lines measurement jaisi dikhti hain aur measurement nahi hain** — aur
ek (`error=The read operation timed out`) usi file ki measured line (`error=`) ke khilaaf hai.

**Do kaam, Din 3 ke method se:**

1. **Artifacts — annotate, delete nahi.** Teen files: `logs/w5d4_step2_20260927_073239_386109.log`,
   `logs/w5d4_step2_20260927_073712_649495.log`, `logs/w5d4_step5_20260927_081356_093927.log`. Har us line ke saath
   (ya neeche) ek note jo `[ANNOTATED 2026-09-28: …]` se shuru ho aur **ek line me provenance** de: ye string literal
   hai / ye `Popen` se shuru hota clock hai / ye prewritten verdict hai. **Values ko mat chhedo** — `3.0501`,
   `error=`, `attempts=1` wagaira measured hain.
2. **Generators — prose hatao.** `labs/w5d4_pool_probe.py` aur `labs/w5d4_composed_failure.py` me se wo lines hatao ya
   aisi line se badlo jo system se padhi hui value print kare. **Rule (`P-52` amendment): harness ki line ya ek value
   hai, ya uska label. Nateeja ek insaan likhta hai, run ke baad, provenance ke saath.**

**Executable end:**

```powershell
(Select-String -Path labs\w5d4_pool_probe.py, labs\w5d4_composed_failure.py -Pattern "The read operation timed out|Reproduced at|Bound analysis|Active Config|Lock Duration|deduce root cause" | Measure-Object).Count | Out-File -Encoding utf8 logs\w5d5_step1_prose_left.txt
(Select-String -Path logs\w5d4_step2_20260927_073239_386109.log, logs\w5d4_step2_20260927_073712_649495.log, logs\w5d4_step5_20260927_081356_093927.log -SimpleMatch "[ANNOTATED 2026-09-28" | Measure-Object).Count | Out-File -Append -Encoding utf8 logs\w5d5_step1_prose_left.txt
.\.venv\Scripts\python.exe -m py_compile labs\w5d4_pool_probe.py labs\w5d4_composed_failure.py *>> logs\w5d5_step1_prose_left.txt
Get-Content logs\w5d5_step1_prose_left.txt        # pehli line 0 · doosri >= 9 · teesri kuch nahi (compile error nahi)
```

**Terms used in this step**

| Term | Kya hai |
|---|---|
| artifact vs generator | artifact wo file hai jo ek run ne likhi; generator wo script jo usko likhti hai. Artifact theek karna agla run theek nahi karta |
| annotate in place | purani line ke saath ek labelled note jodna, line ko mitaye bina. Provenance bachi rehti hai — kaun si line kahan se aayi |
| provenance | ek number ya line ka source: system se padha, script ne assume kiya, ya insaan ne derive kiya |

---

### Step 2 — 25 min: arm A — receiver contention, `P-45` ka teesra number, aur aaj ke probe ka poora dhaancha

Week 4 Din 5 ka teesra khoya hua number: *"receiver wait `2.8133 s` against an uncontended `0.4703 s`"*
`[REPORTED, NOT VERIFIABLE]`. Aaj isko retained artifact ke saath replace karna hai — **aur jo probe ye karega wahi
Step 3 aur Step 4 chalayega**, isliye aaj ka sabse bada likhne ka kaam yahi hai.

**Disposable DB.** Evidence DB `relay` ko aaj koi process nahi chhuega jo likhta ho:

```powershell
docker exec relay-db-1 psql -U postgres -d postgres -c "CREATE DATABASE relay_w5d5;" *> logs\w5d5_step2_createdb.txt
$env:DATABASE_URL = (Get-Content .env | Select-String '^DATABASE_URL=').Line.Split('=',2)[1] -replace '/relay$','/relay_w5d5'
.\.venv\Scripts\python.exe -m alembic upgrade head *> logs\w5d5_step2_migrate.txt
Select-String -Path logs\w5d5_step2_migrate.txt -Pattern "resolved_db="          # alembic resolved_db=relay_w5d5 source=env
docker exec relay-db-1 psql -U postgres -d relay_w5d5 -t -A -c "SELECT current_database() || '|' || (SELECT version_num FROM alembic_version);" | Out-File -Encoding utf8 logs\w5d5_step2_target.txt
Get-Content logs\w5d5_step2_target.txt           # relay_w5d5|w4d4_sink_unique
```

`$env:DATABASE_URL` ki wo line `.env` se URL padhti hai aur sirf database ka naam badalti hai — **password BRIEF me
likhne ki zaroorat nahi.** Har terminal jo koi Relay process launch karta hai, usme ye line pehle chalni hai.

**Probe: `labs/w5d5_chain_probe.py` — tu likhega. Ye uski requirements hain, code nahi.** Din 4 ka
`labs/w5d4_composed_failure.py` ek base hai; neeche ki har row Din 4 ke kisi measured defect se aayi hai.

| # | Requirement | Kis defect se |
|---|---|---|
| 1 | CLI `--arm A\|B\|C` aur `--hold <seconds>`. Run id `%Y%m%d_%H%M%S_%f`. Files: `logs/w5d5_<arm>_<runid>_{probe,sink,dispatcher,poll}.log` | `P-50` |
| 2 | **Har line jo probe likhta hai, likhne ke waqt ka local timestamp (ms tak) ke saath** | `P-53(f)` |
| 3 | Pehle kisi bhi write se: `current_database()` padho, log karo, aur `relay_w5d5` na ho to non-zero exit | `P-28` |
| 4 | Setup: `TRUNCATE outbox, sink_deliveries RESTART IDENTITY`. Arms B/C: do outbox rows, `job_id=42`, `effect_key='job:42'` | Din 4 ka shape |
| 5 | Sink subprocess: `RELAY_PROCESS_NAME=sink_w5d5`, `RELAY_POOL_SIZE=2`, `RELAY_MAX_OVERFLOW=0`, `RELAY_POOL_TIMEOUT=3.0`, `SINK_DEDUP=1`, `PYTHONUNBUFFERED=1`, `DATABASE_URL`. **stdout + stderr ek file me, pipe me nahi.** uvicorn default log level (access lines chahiye). `/health` `200` ke baad sink log ki `resolved_db=` line probe log me copy karo | Din 4: sink ka premise set hua, observe nahi |
| 6 | Arm A only — preamble: `10` sequential direct `POST /deliver`, alag keys `pre:<runid>:<i>`, har ek ka status + latency | `P-45` ka `0.4703 s` |
| 7 | Holder: asyncpg, `application_name=holder_w5d5`, `BEGIN`, `INSERT` key `job:42`. Log karo `holder_start` aur holder ka `pg_backend_pid()` | poll file ko join karne ke liye |
| 8 | Arm A: holder_start ke turant baad ek direct `POST /deliver` for `job:42`, background task me, `15 s` client timeout; complete hone pe status + latency. **Arms B/C: iski jagah dispatcher subprocess** — `RELAY_PROCESS_NAME=dispatcher_w5d5`, `SINK_URL=http://127.0.0.1:8001/deliver`, `DATABASE_URL`, `python -u -m src.dispatcher`. **Uska poora output ek file me, har line timestamp ke saath, aur pehli `[dispatch_error]` pe padhna band nahi** | Din 4 pehle error pe `break` hua, to transaction ka end kabhi log me aaya hi nahi |
| 9 | **Anchor.** Arms B/C: jis waqt dispatcher ki pehli `Attempting dispatch` line aaye — `anchor` log karo. **`--hold` anchor se naapa jaata hai, holder_start se nahi.** Arm A: anchor = holder_start | dispatcher start hone me `~2.6 s` leta hai (Din 4) |
| 10 | Poller: holder_start se holder_end + `8 s` tak, har `250 ms`, poll file me: (a) `pg_stat_activity` — `relay_w5d5` me `sink_w5d5`, `dispatcher_w5d5`, `holder_w5d5` ke liye `application_name, pid, state, wait_event_type, wait_event, pg_blocking_pids(pid), now()-query_start, left(query,40)`; (b) `pg_locks` jinka `relation = 'outbox'::regclass` — `application_name, mode, granted`. **Jis poll me koi row na aaye, wo `rows=0` line likhe** | Din 4 ka zero jo file me nahi pahuncha |
| 11 | Anchor + hold pe holder `ROLLBACK`; `holder_end` log karo | |
| 12 | holder_end + `8 s` pe final state probe log me: outbox rows (`id, attempts, dispatched_at`), `sink_deliveries` rows for `job:42` (`id, received_at`), aur sink log ka census — har `result=` value ki ginti, har exception class ki ginti (Step 6 ke `api_exc` jaisa), aur access-log lines ki ginti | census specific patterns nahi dhoondhta — jo aaya wo ginta hai |
| 13 | Sink aur dispatcher ko `taskkill /T /F /PID <pid>` se band karo (venv launcher + child — do PIDs, reviewer ne Din 4 pe dekha), phir probe ke alawa Relay python count likho | Din 4 reviewer ka apna probe latak gaya tha |
| 14 | **Kisi file me koi nateeja-sentence nahi.** Values aur labels | `P-52` |

**Run arm A:**

```powershell
.\.venv\Scripts\python.exe labs\w5d5_chain_probe.py --arm A --hold 3
```

**Executable end — ek table, har cell ke saath file ka naam:**

| Observation | Value | File |
|---|---|---|
| sink ki `resolved_db=` line | | probe log |
| uncontended: pehla, nau ka median, max | | probe log |
| contended `POST job:42`: status + latency | | probe log |
| poll me `sink_w5d5` ki rows holder ke dauran: kitni, `state`, `wait_event_type`, `wait_event`, `pg_blocking_pids` vs holder ka pid | | poll log |
| sink log me us wait ke dauran nayi lines | | sink log |

Aur ek line: **`2.8133 s` / `0.4703 s` ka aaj ka replacement**, `n` ke saath, `echo=True` ke saath.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `pg_blocking_pids(pid)` | Postgres function: un sessions ke pids jo is session ko block kar rahe hain. Khaali array = koi block nahi kar raha |
| `wait_event_type` / `wait_event` | `pg_stat_activity` ke do columns jo batate hain ki session kis cheez ka intezaar kar raha hai — type (`Lock`, `LWLock`, `IO`, `Client`, `Activity`, …) aur us type ke andar specific naam. `NULL` = kisi cheez ka intezaar nahi |
| `lifespan` | FastAPI ka startup/shutdown hook — app requests lena shuru kare usse pehle chalne wala code |
| uncontended vs contended | bina kisi conflicting writer ke vs ek khule transaction ke saath jo wahi key hold kar raha hai |
| reader-side timestamp | jab doosre process ki line padhne wala timestamp lagata hai — wo *padhne* ka waqt hai, *likhne* ka nahi (`P-22`). Label karo |
| `taskkill /T /F` | Windows: process aur uske saare child processes band karna |

---

### Step 3 — 15 min: arm B — holder dispatcher ke timeout se thoda zyada zinda

Same probe, same sink config, ek variable badla: **holder anchor ke `6 s` baad rollback hota hai** — dispatcher ke
`timeout=5.0` (`src/dispatcher.py:34`) se thoda aage.

```powershell
.\.venv\Scripts\python.exe labs\w5d5_chain_probe.py --arm B --hold 6
```

**Executable end:**

| Observation | Value | Source |
|---|---|---|
| holder_end se pehle kitne `Attempting dispatch`, aur har ek anchor ke kitne baad | | dispatcher log |
| har attempt ka lock hold: `SELECT … FOR UPDATE` echo timestamp → us transaction ke end ki echo line ka timestamp — **aur wo end kaunsa statement tha, wo bhi likho** | | dispatcher log |
| har attempt ki result line | | dispatcher log |
| outbox row `1` aur `2`: `attempts`, `dispatched_at` | | probe log |
| `sink_deliveries` `job:42`: kitni rows, `received_at` | | probe log |
| `received_at` kis attempt ke start ke sabse paas hai | | derived — dono timestamps likho |

Aur ek line: **Relay ki `[dispatch] … status=dispatched` line — agar aayi — us request ke baare me hai jisne effect
apply kiya, ya kisi aur ke?**

**Terms used in this step**

| Term | Kya hai |
|---|---|
| anchor | ek measured moment jisse baaki times naape jaate hain. Galat anchor ek sahi duration ko galat cheez ka bana deta hai (Din 4 ka `Popen`) |
| lock hold per attempt | `FOR UPDATE` wala statement jab lock leta hai, us transaction ke khatam hone tak ka waqt. Do endpoints, dono echo lines se |
| `received_at` | `sink_deliveries` ka column, sink ka `INSERT` `now()` likhta hai. Postgres me `now()` **transaction ke start** ka time hai, statement ke khatam hone ka nahi |
| `RowShareLock` | wo table-level lock jo `SELECT … FOR UPDATE` apni table pe transaction ke poore dauran rakhta hai. `pg_locks` me row-level lock khud nahi dikhta jab tak koi uspe wait na kare |

---

### Step 4 — 10 min: arm C — holder dispatcher ke kai timeouts tak zinda

```powershell
.\.venv\Scripts\python.exe labs\w5d5_chain_probe.py --arm C --hold 20
```

**Executable end — poll, dispatcher aur sink logs se ek timeline:**

| `t − anchor` | `sink_w5d5` sessions, `wait_event_type = Lock` (count) | dispatcher ki last result line | sink log ki nayi lines (kis tarah ki) |
|---|---|---|---|
| `≈ +2 s` | | | |
| `≈ +7 s` | | | |
| `≈ +12 s` | | | |
| `≈ +17 s` | | | |
| `≈ +22 s` (holder_end ke baad) | | | |

Aur do lines: (1) **`QueuePool limit` kahin aaya? Kis process ke log me, pehli baar anchor ke kitne baad?** (2)
**`P-41` ka chain-sentence dobara likho** — kaunsa pool, kis process ka, kitne dispatchers — sirf aaj ke files ke basis
pe.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| do alag queues | `QueuePool` ki queue Python process ke andar hai — wahan wait karta request Postgres ko dikhta hi nahi. Postgres ki lock queue database ke andar hai — wahan wait karta session `pg_stat_activity` me dikhta hai |
| access log vs application print | access log uvicorn likhta hai jab response bheja jaata hai; application print handler khud likhta hai. Do alag writers, do alag conditions |
| `dispatch_error` vs `dispatch_failed` | dispatcher ki do alag lines: pehli tab jab `client.post` exception raise kare, doosri tab jab response aaye par `200` na ho (`src/dispatcher.py`) |

---

### Step 5 — 10 min: supervisor ka instrument — log prefix, aur teesra process

**`scripts/supervisor.py` me ek trap hai jo aaj ke doosre half ko Din 2 ki evidence pe likh deta.** Uske log paths
hardcoded hain — `logs/w5d2_step4_supervisor.log`, `logs/w5d2_step4_worker.stdout.log`, … — aur files **append mode**
me khulti hain `[MEASURED, source read 2026-09-27]`. Unchanged chalane ka matlab: Din 2 ke retained artifacts me aaj ki
lines jud jaati. **Aur wo sirf worker aur reaper ko supervise karta hai** — dispatcher uske bahar hai, jabki `D-30` ka
gate *"teeno process ek saath"* maangta hai.

**Do edits, tera design:**

1. Log file ka prefix environment se aaye (ek variable, jaise `RELAY_SUPERVISOR_PREFIX`). Naming shape wahi rahe:
   `logs/<prefix>_supervisor.log`, `logs/<prefix>_<name>.stdout.log`, `logs/<prefix>_<name>.stderr.log`. **Prefix na
   ho to kya hona chahiye — wo tera faisla hai, aur uska ek cost hai; ek line me likho.**
2. Dispatcher teesra supervised process bane.

**Dry run, `10 s`, disposable DB pe:**

```powershell
Remove-Item Env:RELAY_PROCESS_NAME, Env:RELAY_POOL_SIZE, Env:RELAY_MAX_OVERFLOW, Env:RELAY_POOL_TIMEOUT -ErrorAction SilentlyContinue
$env:DATABASE_URL = (Get-Content .env | Select-String '^DATABASE_URL=').Line.Split('=',2)[1] -replace '/relay$','/relay_w5d5'
$env:RELAY_SUPERVISOR_PREFIX = "w5d5_step5"
$env:PYTHONUNBUFFERED = "1"
.\.venv\Scripts\python.exe scripts\supervisor.py
# ~10 s baad Ctrl+C
```

Pehli line isliye: supervisor apna environment children ko deta hai. Agar is terminal me pehle ka `RELAY_PROCESS_NAME`
bacha hai, to teeno children ek hi `application_name` ke saath chalenge aur `pg_stat_activity` unhe alag nahi kar
payega.

**Executable end:**

```powershell
(Select-String -Path logs\w5d5_step5_supervisor.log -Pattern "Started (worker|reaper|dispatcher)" | Measure-Object).Count | Out-File -Encoding utf8 logs\w5d5_step5_check.txt
(Get-FileHash -Algorithm SHA256 logs\w5d2_step4_supervisor.log).Hash | Out-File -Append -Encoding utf8 logs\w5d5_step5_check.txt
(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count | Out-File -Append -Encoding utf8 logs\w5d5_step5_check.txt
Get-Content logs\w5d5_step5_check.txt          # 3 · Step 0 wala SHA-256 · 0
```

**Terms used in this step**

| Term | Kya hai |
|---|---|
| append mode | file kholne ka mode jisme naya content purane ke **baad** judta hai. Purani file mitti nahi — mix hoti hai, jo zyada khatarnaak hai |
| supervision scope | supervisor kin processes ko dekhta hai. Jo bahar hai uska crash kisi ko nahi dikhta |
| control hash | ek file ka hash jo *nahi badalna chahiye*. Wo check tabhi kuch kehta hai jab uski value pehle file me likhi ho |

---

### Step 6 — 20 min: `35 s` outage — teen process supervisor ke neeche, API, aur backlog

`D-30` ke do gate `[NOT SATISFIED BY EVIDENCE]` hain: *"~`30 s` DB-down run"* (Din 2 ka supervisor log `12.1 s` ka tha)
aur *"`n = 1`, never under load"*. Aur `D-28` ke discriminator ka DB-down column khaali hai. **Ek outage, dono.**

**Terminal A — supervisor** (worker, reaper, dispatcher):

```powershell
Remove-Item Env:RELAY_PROCESS_NAME, Env:RELAY_POOL_SIZE, Env:RELAY_MAX_OVERFLOW, Env:RELAY_POOL_TIMEOUT -ErrorAction SilentlyContinue
$env:DATABASE_URL = (Get-Content .env | Select-String '^DATABASE_URL=').Line.Split('=',2)[1] -replace '/relay$','/relay_w5d5'
$env:RELAY_SUPERVISOR_PREFIX = "w5d5_step6"
$env:PYTHONUNBUFFERED = "1"
.\.venv\Scripts\python.exe scripts\supervisor.py
```

**Terminal B — API**, Din 4 ki config pe, disposable DB pe:

```powershell
$env:DATABASE_URL = (Get-Content .env | Select-String '^DATABASE_URL=').Line.Split('=',2)[1] -replace '/relay$','/relay_w5d5'
$env:RELAY_PROCESS_NAME = "api_w5d5"; $env:RELAY_POOL_SIZE = "2"; $env:RELAY_MAX_OVERFLOW = "0"; $env:RELAY_POOL_TIMEOUT = "3.0"
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000 *> logs\w5d5_step6_api.log
```

**Terminal C — pehle premise check, phir backlog, sampler, outage:**

```powershell
# 1. premise: chaaron process relay_w5d5 pe hain? (0 matches kisi bhi file me = ruk jao)
Select-String -Path logs\w5d5_step6_api.log, logs\w5d5_step6_worker.stdout.log, logs\w5d5_step6_reaper.stdout.log, logs\w5d5_step6_dispatcher.stdout.log -Pattern "^resolved_db=" | ForEach-Object { $_.Line } | Out-File -Encoding utf8 logs\w5d5_step6_premise.txt
Get-Content logs\w5d5_step6_premise.txt        # chaar lines, chaaron resolved_db=relay_w5d5

# 2. backlog: 30 sleep jobs, 1.0 s each — ids ek file me
1..30 | ForEach-Object { (Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/jobs -ContentType 'application/json' -Body '{"type":"sleep","payload":{"seconds":1.0}}').job_id } | Out-File -Encoding utf8 logs\w5d5_step6_jobs.txt

# 3. sampler: har ~3 s, teeno endpoints, timestamp ke saath, file me
$sampler = Start-Job -ArgumentList (Get-Location).Path -ScriptBlock {
  param($root); Set-Location $root
  while ($true) {
    foreach ($p in 'health','healthz','db-ping') {
      $r = curl.exe -s -o NUL --max-time 10 -w "%{http_code} %{time_total}" "http://127.0.0.1:8000/$p"
      "$((Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz')) $p $r" | Out-File -Append -Encoding utf8 logs\w5d5_step6_sampler.txt
    }
    Start-Sleep -Seconds 3
  }
}

# 4. backlog ko drain hone do, phir outage — har boundary ka timestamp file me
Start-Sleep -Seconds 5
function Stamp($m) { "$((Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz')) $m" | Out-File -Append -Encoding utf8 logs\w5d5_step6_fault.txt }
Stamp "stop_begin";  docker compose stop db  *> logs\w5d5_step6_compose_stop.txt;  Stamp "stop_returned"
Start-Sleep -Seconds 35
Stamp "start_begin"; docker compose start db *> logs\w5d5_step6_compose_start.txt; Stamp "start_returned"

# 5. recovery + drain, phir sampler band
Start-Sleep -Seconds 60
Stop-Job $sampler; Remove-Job $sampler

# 6. final state — har query ek row lautati hai, zero bhi
docker exec relay-db-1 psql -U postgres -d relay_w5d5 -t -A -F "|" -c "SELECT status, attempts, count(*) FROM jobs GROUP BY 1,2 ORDER BY 1,2;" | Out-File -Encoding utf8 logs\w5d5_step6_final_jobs.txt
docker exec relay-db-1 psql -U postgres -d relay_w5d5 -t -A -c "SELECT 'pending_or_running=' || count(*) FROM jobs WHERE status IN ('pending','running');" | Out-File -Append -Encoding utf8 logs\w5d5_step6_final_jobs.txt
```

Phir Terminal A aur B me `Ctrl+C`, aur:

```powershell
$s = [System.Collections.Generic.List[string]]::new()
$s.Add("exited_lines=" + (Select-String -Path logs\w5d5_step6_supervisor.log -SimpleMatch "EXITED" | Measure-Object).Count)
# har process ke log ka tag census: [poll_error], [claim], ... jo bhi tag aaya, uski ginti
foreach ($p in 'worker','reaper','dispatcher') {
  Select-String -Path "logs\w5d5_step6_$p.stdout.log" -Pattern '\[([a-z_]+)\]' -AllMatches -CaseSensitive | ForEach-Object { $_.Matches } | ForEach-Object { $_.Groups[1].Value } | Group-Object | Sort-Object Name | ForEach-Object { $s.Add("$p tag[" + $_.Name + "]=" + $_.Count) }
}
Select-String -Path logs\w5d5_step6_api.log -Pattern '^[A-Za-z_.]+(Error|Exception)\b' | ForEach-Object { ($_.Line -split ':')[0] } | Group-Object | ForEach-Object { $s.Add("api_exc " + $_.Count + " " + $_.Name) }
$s.Add("relay_python=" + (Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count)
$s | Out-File -Encoding utf8 logs\w5d5_step6_summary.txt
Get-Content logs\w5d5_step6_summary.txt
```

**Outage ke waqt handler me jo job tha, uska poora raasta:** worker log me pehli failure line (koi bhi `_error` tag) se
theek pehle ki aakhri `[execute]` line se uska `job_id` nikalo, phir:

```powershell
$jid = <wo job_id>
Select-String -Path logs\w5d5_step6_worker.stdout.log, logs\w5d5_step6_reaper.stdout.log -Pattern "job_id=$jid\b" | ForEach-Object { "$($_.Filename):$($_.LineNumber): $($_.Line)" } | Out-File -Encoding utf8 logs\w5d5_step6_inflight.txt
```

**Executable end — ek table, aur `D-30` ke liye do lines:**

| Observation | Value | File |
|---|---|---|
| outage window: `stop_returned` → `start_begin` | | `w5d5_step6_fault.txt` |
| supervisor restarts (`EXITED` lines) | | `w5d5_step6_summary.txt` |
| har process ka tag census · outage ke baad us process ki pehli successful DB activity ka echo timestamp | | summary + stdout logs |
| in-flight job ka poora raasta, line by line | | `w5d5_step6_inflight.txt` |
| jobs final: status × attempts | | `w5d5_step6_final_jobs.txt` |
| sampler, outage ke andar: `/health`, `/healthz`, `/db-ping` — status + latency, pehla sample aur baad wale | | `w5d5_step6_sampler.txt` |
| API log ke exception classes, count ke saath (count = traceback lines, requests nahi — ek chained traceback do lines deta hai) | | summary |

**`D-30` gate 1** (*restarts bounded over a `~30 s` DB-down*) aur **gate 2** (*teeno ek saath, backlog ke neeche*):
satisfied ya nahi, number ke saath. **`D-30` ka section Din 6 likhega — aaj sirf ye do lines.**

**Terms used in this step**

| Term | Kya hai |
|---|---|
| outage window | wo interval jisme DB request accept nahi karta. `docker compose stop` ka return aur Postgres ka asal band hona do alag moment hain — isliye dono taraf stamp |
| `CannotConnectNowError` | Postgres ka error jab wo start ho raha hai aur abhi connections nahi le raha (Din 1 pe measured) |
| backlog | queue me pending jobs jinko worker drain kar raha hai |
| mark retry deadline | worker ka terminal mark fail ho to wo ek fixed `10 s` tak retry karta hai (`src/worker.py`, Din 2) |
| lease | `30 s` — `claimed_at` isse purana ho aur status `running` ho to reaper row wapas `pending` karta hai (`src/reaper.py`) |
| echo timestamp format | SQLAlchemy `echo` lines `2026-09-28 10:15:02,420` shape me aati hain (local, bina offset); `Stamp` ISO + offset likhta hai. Compare karte waqt dono ko local maano |

---

### Step 7 — 10 min: close bench, sab file me

```powershell
docker exec relay-db-1 psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS relay_w5d5 WITH (FORCE);" *> logs\w5d5_step7_drop.txt
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("src_diff=" + (git diff --name-only HEAD -- src/ | Measure-Object).Count)
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py src/sink.py | ForEach-Object { $o.Add("hash $_") }
$o.Add("heads=" + ((.\.venv\Scripts\python.exe -m alembic heads 2>&1) -join ' | '))
$o.Add("except_BaseException=" + (Select-String -Path src\*.py -Pattern "except BaseException" | Measure-Object).Count)
$o.Add("relay_underscore_dbs=" + ((docker exec relay-db-1 psql -U postgres -d postgres -t -A -c "SELECT count(*) FROM pg_database WHERE datname LIKE 'relay\_%';") -join ''))
$o.Add("relay_python=" + (Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count)
$o.Add("key_index=" + (git ls-files -- "*_KEY.md" | Measure-Object).Count)
$o.Add("key_tree=" + (git ls-tree -r --name-only HEAD | Select-String -CaseSensitive "_KEY\.md" | Measure-Object).Count)
$o.Add("pyc_control=" + (git ls-files -- "*.pyc" | Measure-Object).Count)
$o.Add("p54=" + (git status --porcelain | Select-String -CaseSensitive "_ANSWERS\.md|_DESIGN\.md|_PROBLEM\.md|_PROPERTY\.md" | Measure-Object).Count)
$o.Add("labs_w5d5_ignored=" + ((git check-ignore -v --no-index labs/w5d5_chain_probe.py 2>&1) -join ' | '))
$o.Add("frozen_sha256=" + (Get-FileHash -Algorithm SHA256 docs\daily\week_05\DIN_05_PREDICTIONS_FROZEN.md).Hash)
$o.Add("counters=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -F "|" -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');") -join ''))
$o | Out-File -Encoding utf8 logs\w5d5_step7_bench.txt
Get-Content logs\w5d5_step7_bench.txt
Get-Content logs\w5d5_step0_frozen_hash.txt | Select-String "Hash"
```

Expected: `src_diff=0` · chhe hashes Step 0 ke barabar · `heads=w4d4_sink_unique (head)` · `except_BaseException=0` ·
`relay_underscore_dbs=0` · `relay_python=0` · `key_index=0` · `key_tree=0` · `pyc_control=1` · `p54=20` ·
`labs_w5d5_ignored=` **khaali** (probe publish hone layak hai) · `frozen_sha256` = Step 0 file ki value ·
`counters=133|145|19|4|7|39|5|0|1`.

---

## PART B — Prediction questions

> **Inhe Part A ya Part C ke saath Gemini ko NAHI dena. Har sawaal apne step se PEHLE, apne head se, likha hua. `idk`
> valid hai aur `0` score karta hai.** Din 4 pe paanchon `idk` the aur teeno din se inflation zero hai — wo record saaf
> hai. **Ek nayi baat:** Din 4 ke teen sawaalon ka ek hissa run se pehle `src/` padh ke nikal sakta tha, aur `idk` aaya.
> **Jis sawaal me ek file ya line ka naam hai, `idk` likhne se pehle wo file kholo** — wo Situation 1 hai (padhna), 2
> nahi (naapna).

```text
Q1 (Step 2 se pehle — arm A)
(a) Din 4 pe API ki pehli DB request 0.17 s thi aur baaki milliseconds me.
    Sink ki PEHLI uncontended /deliver baaki nau jaisi hogi, ya pehli wali
    mehngi padegi? Mechanism ek line me — src/sink.py padh ke.
(b) Holder 3 s ka. job:42 wali direct POST kitni der me, kis status ke saath
    lautegi — ek number, aur wo number kis cheez se bandha hai.
(c) Wait ke dauran poll file me sink_w5d5 ki row: state, wait_event_type,
    wait_event — teen shabd. Aur pg_blocking_pids me kiska pid hoga?
(d) Wait ke dauran sink ke apne log me us request ke baare me kya likha hoga?
    Aur holder ke rollback ke baad sink kya print karega — applied ya duplicate?

Q2 (Step 3 se pehle — arm B, holder anchor ke 6 s baad khatam)
(a) holder_end se pehle kitne dispatch attempts sink tak pahunchenge? Ek number,
    aur har attempt anchor ke lagbhag kitne second baad shuru hoga.
(b) Attempt 1 ke liye outbox row 1 ka lock kitni der held rahega, aur kis
    statement pe khatam hoga? (src/dispatcher.py — ye padh ke nikalta hai.)
(c) Holder rollback hone pe job:42 ki INSERT kis request ki land karegi —
    attempt 1 ki ya attempt 2 ki? Aur data me kaunsa column padh ke tu ye
    decide karega?
(d) Final: outbox row 1 ka attempts aur dispatched_at. Aur Relay ki
    "[dispatch] ... status=dispatched" line — kya wo us request ke baare me
    hai jisne effect apply kiya?

Q3 (Step 4 se pehle — arm C, holder anchor ke 20 s baad khatam)
(a) Anchor + 12 s pe poll file me kitne sink_w5d5 sessions
    wait_event_type = Lock pe honge? Ek number, aur kyun wahi number.
(b) In 20 s me dispatcher ke log me kaunsi result-line shapes aayengi, kis
    order me? ("[dispatch_error] ... error=" / "[dispatch_failed] ...
    status_code=..." / "[dispatch] ... status=dispatched")
(c) "QueuePool limit ... timeout 3.00" kahin aayega? Kis process ke log me,
    aur pehli baar anchor ke lagbhag kitne second baad?
(d) P-41 kehta hai: "two dispatch attempts stalled behind one slow
    sink_deliveries writer exhaust the pool, and the symptom surfaces as
    pool_timeout in Relay". Run se pehle is sentence ko apne shabdon me
    dobara likho — kaunsa pool, kis process ka, kitne dispatchers chahiye.

Q4 (Step 6 se pehle — supervised fleet, 35 s outage, backlog)
(a) Outage ke dauran supervisor kitni baar restart karega? Ek number, aur
    Din 1–2 ke measured record se derive karo.
(b) Jo job outage shuru hote waqt handler me tha (sleep 1.0), uska final
    attempts kya hoga — aur usko 'running' se wapas kaun laayega? Log lines
    ke naam se raasta likho.
(c) Backlog ke BAAKI jobs me se kisi ka attempts > 1 hoga? Haan/nahi aur kyun.
(d) P-53(d) ka backoff defect (>= 5 s uptime pe reset) — is run me exercise
    hoga ya nahi? Kyun?

Q5 (Step 6 se pehle — API, usi outage ke dauran)
(a) Outage ke dauran /health, /healthz, /db-ping — teeno ka status.
(b) /healthz ka latency outage ke dauran Din 4 ke saturated 3.03 s se
    distinguishable hoga? Pehla failing sample aur baad wale — same ya alag?
(c) Pool starvation ko DB down se alag karne wali EK observation kaunsi hai —
    aur kya ek HTTP prober usko dekh sakta hai?
(d) DB wapas aane ke baad pehla /healthz — 200 ya 500? (D-31:
    pool_pre_ping = False.)
```

---

## PART C — Verification

**Din 4 ka ek naya sabak yahan shuru hota hai:** Din 4 ke Part C ne Part B ke kai jawab likh diye the (*"peak `≤ 2`"*,
*"teesra request fail karta hai"*, *"DB na chhune wala endpoint `200`"*). **Is Part C me jahan outcome khud ek Part B
sawaal hai, wahan uski value nahi di gayi — sirf ye check kiya gaya hai ki instrument us value ko pakad sakta tha.**
Har row ke saath sawaal wahi hai: **kaunsa galat implementation isko bhi pass kar dega?** Aur har check ka subject naam
se hai.

### C1 — Target aur isolation

| Subject | Check | Broken reading |
|---|---|---|
| `logs/w5d5_step2_target.txt` | exactly `relay_w5d5\|w4d4_sink_unique` | `relay\|…` — evidence DB pe migrate |
| har probe log ki shuruaati lines | `current_database()` ki value `relay_w5d5` likhi hui, pehle write se pehle | line na ho = assert chala hi nahi |
| `logs/w5d5_step6_premise.txt` | chaar lines, chaaron `resolved_db=relay_w5d5` | ek bhi `resolved_db=relay` = `30` jobs evidence DB me |
| nau counters, Step 7 | `133\|145\|19\|4\|7\|39\|5\|0\|1` | koi bhi delta |

### C2 — Har premise observe hui, sirf set nahi (Din 4 ka `C1`, sink aur fleet pe)

| Subject | Check | Kya pakadta hai |
|---|---|---|
| sink, arms A/B/C | har sink log me sink ki apni `resolved_db=relay_w5d5 app_name=sink_w5d5 pool=2+0` line, aur wo probe log me copy hui | Din 4 Step 5: sink ka config set hua, kabhi observe nahi hua |
| dispatcher, arms B/C | har dispatcher log me `resolved_db=relay_w5d5 app_name=dispatcher_w5d5` | |
| supervisor ka scope | `w5d5_step6_supervisor.log` me `Started` ki teen alag names | dispatcher phir bahar |
| Din 2 ki evidence | `logs/w5d2_step4_supervisor.log` SHA-256 = Step 0 ki value (`9ABF8EA2…5A6F`) | append mode ne Din 2 ke artifact me aaj ki lines jod di |

### C3 — Instrument wo dekh sakta hai jo wo claim karta hai (outcome-neutral)

| Subject | Check | Broken instrument kya deta hai |
|---|---|---|
| poll log, har arm | holder_start → holder_end + `8 s` ka poora window covered, `250 ms` pe — kam se kam `80%` expected polls, **`rows=0` lines samet** | window me ek gap ek zero banata hai jo *"koi wait nahi"* jaisa padhta hai |
| dispatcher log, arms B/C | **har** `Attempting dispatch` ke baad ek result line **aur** us transaction ke end ki echo line — jo bhi statement ho | pehle error pe padhna band — lock ka end kabhi dikhta nahi (Din 4) |
| anchor, arms B/C | `anchor` probe log me, aur `holder_end − anchor = hold ± 0.3 s` | hold holder_start se naapa gaya — arm B chupke se arm A ban jaata hai |
| har reported duration | dono endpoints naam se (jaise `SELECT … FOR UPDATE` echo → transaction-end echo) | Din 4 ka `7.6771 s` |
| teeno probe logs | neeche wala command → `0` | `P-52` — nateeja-sentence harness ne likha |

```powershell
(Select-String -Path logs\w5d5_*_probe.log -Pattern "occurred at|Reproduced|anchored on|\? NO|\? YES" | Measure-Object).Count | Out-File -Encoding utf8 logs\w5d5_c3_prose.txt
```

### C4 — Ek variable, do arms

| Check | Kyun |
|---|---|
| arms B aur C ke probe log headers me generator ka SHA-256 **identical**, aur sink config identical | B/C ka farak **sirf** `--hold` hona chahiye. Do cheez ek saath badli to farak kis ka hai, pata nahi chalega |
| arm A ka role alag hai aur wo naam se likha hai | arm A me dispatcher nahi hai — wo `P-45` ka re-take hai, differential ka hissa nahi |

### C5 — Outage ka timeline (Step 6)

| Subject | Check | Broken reading |
|---|---|---|
| `logs/w5d5_step6_fault.txt` | chaar stamps — `stop_begin`, `stop_returned`, `start_begin`, `start_returned` | `P-53` chauthi baar |
| outage ki lambai | `start_begin − stop_returned ≥ 35 s` | Din 2 ka `12.1 s` — gate decorative |
| sampler | `stop_returned` aur `start_begin` ke **beech** har endpoint ka kam se kam ek sample | DB-down column phir khaali |
| backlog | `logs/w5d5_step6_jobs.txt` me `30` ids | |
| final jobs | `pending_or_running=` wali row file me maujood — value chahe jo ho | ek zero jo file me nahi pahuncha |

### C6 — `src/` aur publishing surface unchanged

| Check | Expected |
|---|---|
| `git diff --name-only HEAD -- src/` | `0` |
| chhe `src` hashes | Step 0 ke barabar |
| `alembic heads` | exactly `w4d4_sink_unique (head)` — string pe |
| `except BaseException` in `src/` | `0` |
| `*_KEY.md` index · tree · `*.pyc` control | `0` · `0` · `1` |
| `P-54` surface | **`20`** — kam ya zyada dono galat |
| `labs/w5d5_chain_probe.py` | `check-ignore` khaali — `labs/` publish hota hai (`D-32`) |

### C7 — Close

| Check | Expected |
|---|---|
| `pg_database LIKE 'relay\_%'` | `0` |
| Relay python processes | `0` |
| frozen hash | Step 0 ki **file** aur Step 7 ki line identical |
| har number jo report me jaaye | `[MEASURED 2026-09-28]` + file ka naam |

### C8 — Aaj ye quote nahi honge

| Check | Kyun |
|---|---|
| `7.6771 s` lock duration ke naam se | `Popen` → stdout clock tha (`P-41` amendment) |
| `3.0055 s`, `3.1618 s` bina *"retired"* ke | Din 4 pe replace hue, confirm nahi |
| `2.8133 s` / `0.4703 s` Step 2 ke baad | aaj replace honge |
| *"connection leak"* Din 4 Step 4 ke liye | connection `20.025 s` pe wapas aayi — leak nahi, cancellation nahi |
| *"PostgreSQL enforced the pool ceiling"* | `QueuePool` ne process ke andar kiya |

---

## PART D — Scope guard

| Kya | Owner | Kyun aaj nahi |
|---|---|---|
| Koi bhi `src/` edit — `P-55` ki class, `P-44` router, `P-51`, `echo`, sink pe `lock_timeout` | **Week 6** | Week rule. Aaj ke runs `src/` ko **waisa hi** padhte hain jaisa wo hai — wahi measurement hai |
| Doosra dispatcher process | **plan me nahi** | `P-41` ka original *concurrent attempts* shape. Aaj ka sawaal ye hai ki ek kaafi hai ya nahi |
| Sink pe `lock_timeout` / `statement_timeout` ka faisla | **Week 6**, `D-27` ka `Cost` | Fix chain ko `narrow` karta hai. Aaj unfixed chain naapi ja rahi hai |
| Supervisor ka backoff redesign | **Din 6**, `D-30` | Aaj naapna hai; `D-30` decide karega |
| Supervisor ka child PID log karna (`P-53(b)`) | **Din 6 ya baad** | Aaj ke counts ke liye zaroori nahi |
| Processes ko Compose me le jaana | `D-30` option (a), **Month 2 ke baad** | Har retained Week 5 baseline invalid ho jaata hai |
| README rows 7/9, promise #4 ka verdict | **Din 6** | Aaj uska evidence banta hai, verdict nahi |
| `P-54` ke faisle, `.pyc` ka `rm --cached` | **Din 6** | Bees files aaj bhi gate hain |
| `logs/` ki purani files delete karna | **Din 6 ke baad** | Retention ka doosra half likha nahi gaya |
| `/slow-hold?seconds=100000` | **kabhi nahi** | Ek connection `~27.8` ghante |
| History rewrite | **kabhi nahi, bina explicit faisle ke** | |
| Receiver apni alag DB me | **Month 3** | Architecture change |
| Koi bhi migration | **Week 6** | `alembic heads` gate |
| `POST /jobs` evidence DB `relay` pe | **kabhi nahi** | `C1` |

**Cut order, agar time khatam ho:** Step 3 (arm B) → Step 1 (Din 6 pe ek line) → Step 4 ki timeline sirf `+12 s` row.
**Kabhi cut nahi:** Step 6 — uske bina `D-30` Din 6 pe wahi *"not satisfied by evidence"* ke saath band hoga jo Din 2 ne
likha tha — aur Step 2, kyunki Step 3 aur 4 usi probe pe chalte hain.

---

*Wapas:* [`../../logs/WEEK_05.md`](../../logs/WEEK_05.md) ·
*Din 4 BRIEF:* [`DIN_04_BRIEF.md`](DIN_04_BRIEF.md) ·
*Seal:* `DIN_05_PREDICTIONS_FROZEN.md` (Step 0 pe banegi)
