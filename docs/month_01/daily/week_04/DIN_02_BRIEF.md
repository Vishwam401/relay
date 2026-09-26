# Week 4 Din 2 BRIEF — instruments: `completed_at`, `last_error`, lifecycle log, aur wo shutdown run jo phisal gaya tha

**Week 4 · Din 2** · Plan: [`../../planning/WEEK_04.md`](../../planning/WEEK_04.md) ·
Log: [`../../logs/WEEK_04.md`](../../logs/WEEK_04.md) · Sealed: [`DIN_02_KEY.md`](DIN_02_KEY.md) ·
Kal: [`DIN_01_BRIEF.md`](DIN_01_BRIEF.md)

**Goal:** wo teen cheezein banao jinke bina Din 5 ka koi latency number likha hi nahi ja sakta, **aur** Week 3
ka slipped shutdown-vs-lease run aaj chalao — pehli baar generation gate ke saath.

**Architectural invariant (aaj ke baad):**
> Har terminal transition ek **timestamp** chhodta hai, har failure ek **reason** chhodta hai, aur ek job ka
> poora lifecycle ek `job_id` pe grep karke reconstruct ho sakta hai — DB ke bahar, stdout se. Aur ye teeno
> writes **usi generation gate** ke peeche hain jo kal bani: `completed_at` ek stale worker se nahi likha jaata.

**Deliverable:** `completed_at` + `last_error` migration · latency ki **likhi hui definition** · structured
lifecycle log line · pehla **derived latency number** `n` ke saath · aur `45 s` payload + `SIGBREAK` at
`T = 3 s` ke **do** run (yielding aur `block: true`), alag-alag likhe hue.

**Budget:** `20 + 15 + 20 + 20 + 20 + 30 = 125 min`. Plan me `105` likha hai; wo Step 0 ke bina hai aur Step 0
aaj **skip nahi ho sakta** (neeche wajah likhi hai). Overflow `+(-10)` vs `135` budget, matlab aaj space hai.
**Cut order, agar khinche:** Step 4 ka latency number Step 5 ke baad bhi liya ja sakta hai (query 30 s ki hai).
**Step 5 kabhi nahi kata** — wo do hafte ka slipped debt hai.

---

## Rules — ye teen roz wahi hain

> **Paste rule:** Part A, Part C, Part D Gemini ko ja sakte hain. **Part B kabhi nahi. KEY kabhi nahi.**
>
> **Seal rule:** paanchon answers **Step 0 me** freeze honge, Step 1 shuru hone se pehle. Har KEY section
> tabhi khulta hai jab uss step ka **measurement** ho chuka ho — prediction likhne ke baad nahi. Output
> prediction se alag nikla to **pehle apni explanation likho**, phir Gemini ke saath uss output pe reason karo
> (outcome ab secret nahi), phir KEY.
>
> **Provenance rule:** iss BRIEF ke saare bench numbers, page counts, aur signal timings `[MEASURED-R 2026-09-06]`
> hain — BRIEF generate karte waqt actually chalaye gaye. Jo tum chalao wo `[MEASURED]`. Jo `[INFERRED]` likha
> hai wo **prediction nahi**, wo ek assumption hai jise C-block todh sakta hai.

### Read order — isko literally follow karo

1. Sirf **Step 0** padho (uske andar ka `0D` bhi — wo aaj ka structural blocker hai).
2. Editor outline se seedha **Part B** pe jao. Step 1–5 aur Part C abhi mat kholo.
3. Paanch predictions likho (`idk` valid hai aur `0` score karta hai), phir Step 0 ke **seal command** pe wapas aao.
4. Frozen hash print hone ke baad **Part C ka C0** kholo. C0 pass ho tab Step 1 aur baaki Part A/Part C khulte hain.

Part A ko Gemini ko tabhi paste karna jab frozen hash already exist karta ho.

---

## Kal ka sach, aur usme se do cheezein aaj ka kaam badalti hain

`[MEASURED-R 2026-09-06]` — ye BRIEF banate waqt padha gaya, tumhari report se nahi:

| Kya | Actual | Aaj ka asar |
|---|---|---|
| **Din 1 committed nahi hai** | `HEAD = 87f2253` (Week 3 close). `src/models.py` aur `src/worker.py` **modified**, `alembic/versions/w4d1_claim_generation_*.py` **untracked**, `docs/logs/WEEK_04.md` untracked | Tumne kaha "committed ho chuka hai" — **repo isse contradict karta hai.** Aaj Step 0 ka pehla kaam Din 1 ko commit karna hai, warna Din 2 ki migration ek uncommitted migration ke upar chadhti hai aur `git bisect` do din ko ek maan lega |
| **Job `128` abhi bhi `running` hai** | `128 | running | attempts=2 | claim_generation=2 | claimed_at=2026-09-06 08:14:24`, payload `{"block": true, "seconds": 45}` | Iska lease **kab ka** expire ho chuka hai. Aaj ka **pehla** reaper pass isko `pending` karega, ek worker claim karega, `45 s` block karega, lease phir expire hogi, fence phir lagegi — **har `~32 s` me ek naya `job_executions` row.** 105 min me ye ~180 rows hai. Din 2 ka poora chain padhne layak nahi rahega |
| Bench | `jobs 122 | max(id) 128 | jobs_id_seq 128 | job_executions 116 | job_executions_id_seq 123 | side_effects 11 | side_effects_id_seq 16 | alembic w4d1_claim_generation` | C0 ka fingerprint |
| Buckets | `succeeded 103 | failed 15 | dead_letter 3 | running 1 | pending 0` → `122` | `pending` `0` hai — matlab aaj **koi drain nahi**, sirf `128` ka resolution |
| `jobs` ka size | `heap_pages = 2`, `toast_pages = 0`, TOAST relation **exist karta hai** | Step 2 ka `last_error` faisla iss number ke against likha jaata hai, `[INFERRED]` ke against nahi |
| Claim query ka plan | `Limit → LockRows → Sort(quicksort 25 kB) → Seq Scan on jobs`, `Rows Removed by Filter: 122`, `Buffers: shared read=2` | **Poll ek full seq scan hai.** Isliye `jobs` ke heap pages ka count seedha poll ke I/O me jaata hai. Ye Q2 ka asli maidan hai |
| `job_executions` pe `claim_generation` | `113` honest `NULL`, `3` stamped, total `116` | Aaj ye number badlega; C0 usko capture karta hai, hardcode nahi |

### Ek naya measured fact jo aaj ke process counting ko todta hai

`[MEASURED-R 2026-09-06]` `.venv\Scripts\python.exe` (virtualenv `20.38.0`, CPython `3.13.5`) ek **redirector
shim** hai. Ek logical worker = **do `python.exe` process**, dono ka command line **byte-for-byte same**:

```text
StartProcess_reported_pid=9232
matched_count=2
  pid=9232 ppid=23840 cmd="D:\PROJECTS\relay\.venv\Scripts\python.exe" -u -m src.worker
  pid=7616 ppid=9232 cmd="D:\PROJECTS\relay\.venv\Scripts\python.exe" -u -m src.worker
```

Teen consequences, aur teenon aaj kaam me aate hain:

1. **`Get-CimInstance … src\.worker` ka count double hai.** Aaj Step 5 me do worker = **`4`** matching rows.
   Din 1 ka `-ne 0` check theek tha (zero ka zero hi hota hai); "kitne worker chal rahe hain" wala check nahi hai.
2. **`WORKER_ID = worker-{os.getpid()}` asli interpreter ka pid hai, shim ka nahi.** Matlab DB ka `worker_id`
   `Start-Process`/`Popen` ke pid se **kabhi match nahi karega**. Mapping `ParentProcessId` se banti hai.
3. **`os.kill(pid, CTRL_BREAK_EVENT)` sirf group leader pe kaam karta hai.** `CREATE_NEW_PROCESS_GROUP` ke saath
   spawn kiya hua **shim** group leader hai, aur signal poore group ko jaata hai — isliye grandchild interpreter
   ko bhi milta hai. Agar tum `Get-CimInstance` se asli interpreter ka pid nikaal ke usko signal karoge, wo
   **fail karega** — wo pid kisi group ka leader nahi hai. Step 5 ka harness isliye `Popen`-returned pid use karta hai.

---

# Part A — Steps

## Step 0 — 20 min: commit Din 1, opening bench, paanch predictions freeze, aur job `128` ka resolution

**Terms used in this step**
- **Evidence DB:** `relay` — teen hafte ka permanent record. Rows `DELETE` nahi hoti, sequence reset nahi hota (`P-05`).
- **Opening bench:** pehli database read. Ye kal ke close se match karni chahiye; na kare to Din 2 rukta hai (`E2`).
- **Frozen prediction:** answer ki immutable copy + SHA-256, measurement se pehle. Post-run explanation prediction credit nahi leti.
- **Carried `running` row:** ek row jo `running` me atki hai kyunki uska worker mar/band ho gaya. Uska lease expired hai, matlab reaper usko reclaim karne ke liye eligible hai.
- **Lease:** `30 s`. `LEASE_DURATION_SECONDS` `src/reaper.py` me hai. Reaper `running` row ko `pending` karta hai jab `claimed_at` `30 s` se purana ho.
- **`-u` / `PYTHONUNBUFFERED`:** Python ka stdout jab file/pipe pe jaata hai to block-buffered ho jaata hai. `-u` usko unbuffered karta hai. Aaj ke saare ordering proofs stdout se aate hain.

### 0A — commit Din 1 (aaj ka pehla kaam, aur ye negotiable nahi)

Aaj **doosri** consecutive migration jaa rahi hai. Ek uncommitted migration ke upar doosri migration ka matlab
hai ki `git log` do din ko ek revision me collapse kar dega, aur `downgrade -1` ka blame kis din ka hai — ye
sawaal aage kabhi answer nahi hoga.

```powershell
git add src/models.py src/worker.py alembic/versions/w4d1_claim_generation_add_claim_generation.py
git status --short
git commit -m "feat(week-4-din-1): add claim_generation fencing to claim, heartbeat, and mark paths"
git rev-parse --short HEAD
```

`docs/logs/WEEK_04.md` **alag commit** me jaati hai (content vs provenance, Week 3 ka established pattern).
`docs/LEARNING_LOG.md` aur `docs/logs/WEEK_03.md` bhi modified hain — wo **aaj ke commit me nahi** aane chahiye
jab tak tum unhe padh ke confirm na karo; `git add` naam se karo, `git add .` se nahi.

### 0B — logs folder aur environment

```powershell
New-Item -ItemType Directory -Path .\logs -Force | Out-Null
$env:PYTHONUNBUFFERED = "1"
$env:DATABASE_URL     = 'postgresql+asyncpg://postgres:relay@localhost:5433/relay'
```

### 0C — predictions likho aur freeze karo

1. `docs\daily\week_04\DIN_02_ANSWERS.md` banao. Part B ke paanch sawaal **exactly** copy karo. Structure:
   `## Q1` … `## Q5`, aur har ek ke neeche exactly `### Prediction`, `### Observed + meri explanation`, `### After KEY`.
2. `### Prediction` non-empty (`idk` valid). Baaki do blocks freeze ke waqt **khaali**.
3. Phir neeche ka seal command **usi PowerShell terminal** me chalao (C5 usi variable ko dobara maangega).

```powershell
$answers = 'docs\daily\week_04\DIN_02_ANSWERS.md'
$frozen  = 'docs\daily\week_04\DIN_02_PREDICTIONS_FROZEN.md'
if (-not (Test-Path $answers)) { throw "Missing $answers" }
if (Test-Path $frozen) { throw "Frozen file already exists; overwrite forbidden: $frozen" }

$text  = (Get-Content $answers -Raw) -replace "`r`n","`n"
$cards = [regex]::Matches($text,'(?ms)^## Q(?<id>[1-5])[ \t]*\n(?<q>.*?)^### Prediction[ \t]*\n(?<p>.*?)^### Observed \+ meri explanation[ \t]*\n(?<o>.*?)^### After KEY[ \t]*\n(?<a>.*?)(?=^## Q[1-5][ \t]*$|\z)')
if ($cards.Count -ne 5) { throw "Expected 5 ordered answer cards, got $($cards.Count)" }
$ids = @($cards | ForEach-Object { [int]$_.Groups['id'].Value })
if (($ids -join ',') -ne '1,2,3,4,5') { throw "Cards must be Q1..Q5 in order; got $($ids -join ',')" }
foreach ($c in $cards) {
  $id = $c.Groups['id'].Value
  if (-not $c.Groups['p'].Value.Trim()) { throw "Q$id prediction empty; write idk if unknown" }
  if ($c.Groups['o'].Value.Trim())      { throw "Q$id Observed block must be empty before freeze" }
  if ($c.Groups['a'].Value.Trim())      { throw "Q$id After KEY block must be empty before freeze" }
}

Copy-Item $answers $frozen
$d2FrozenHash = (Get-FileHash $frozen -Algorithm SHA256).Hash
$d2FrozenTime = (Get-Item $frozen).LastWriteTimeUtc.ToString('o')
"D2_FROZEN_SHA256=$d2FrozenHash"
"D2_FROZEN_MTIME_UTC=$d2FrozenTime"
```

Dono lines log me chipka do. Ab **Part C ka C0** kholo aur chalao.

### 0D — job `128` ka resolution: production path se, hand-write se nahi

**Ye aaj ka structural blocker hai.** `128` `running` me atki hai, uska lease `08:14:24` pe khatam ho chuka
tha, aur uska payload `{"block": true, "seconds": 45}` hai. Agar tum ise chhod ke reaper start karte ho, ye
`~32 s` ke cycle me hamesha ke liye ghoomti rahegi aur aaj ka `job_executions` delta kachra ho jaayega.

Do raaste hain aur inme ek clearly behtar hai:

| Option | Kya hota hai | Cost |
|---|---|---|
| **Chosen — ek reaper pass, phir reaper band, ek worker** | Reaper `128` ko `pending` karta hai (production code path). Worker claim karta hai → generation `3`. `time.sleep(45)` chalta hai. Reaper band hai to koi reclaim nahi. Mark `WHERE status='running' AND claim_generation=3` → `rowcount=1` → `succeeded` | Timing-sensitive: reaper ko worker ke claim ke **`30 s` ke andar** band karna hai. `45 s` lagta hai |
| Rejected — `UPDATE jobs SET status='succeeded' WHERE id=128` | Instant | Evidence DB me ek hand-written terminal transition. Aur ye exactly wo **naya lifecycle writer** hai jise Din 1 ka `D-26` draft `Cost` me *fragility* likh ke chhoda tha. Ek hafte purani decision ko doosre din todna |

**Launch order, aur ye load-bearing hai:**

| # | Terminal | Kab |
|---|---|---|
| 1 | **worker** | pehle. `pending` `0` hai, to ye sirf poll karega, kuch claim nahi karega |
| 2 | **reaper** | worker ke baad. Pehle pass me `id=128 pre_status=running matched=1 post_status=pending` print karega |
| 3 | — | Reaper ki uss line ke turant baad: **reaper ko `Ctrl+C`.** Worker `2.0 s` ke andar claim karega |

```powershell
# terminal 1 — worker
.\.venv\Scripts\python.exe -u -m src.worker *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d2_step0_drain_worker.log

# terminal 2 — reaper (ek pass ke baad Ctrl+C)
.\.venv\Scripts\python.exe -u -m src.reaper *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d2_step0_drain_reaper.log
```

`Marked job 128 as 'succeeded'` dikhne ke baad worker ko `Ctrl+C`, phir **C0D** chalao. Iska delta Din 2 ke
experiments ke delta me **nahi** judta — log me alag heading.

**Agar timing do baar miss ho jaaye** (reaper `30 s` ke andar band nahi hua aur fence phir lag gayi): rukho,
`attempts` note karo, aur usko log me `[MEASURED]` likho — wo Din 1 ke *"loop apne aap nahi rukta"* claim ka
teesra witness hai. Phir teesri koshish karo. **Hand-write tab bhi nahi.**

**Executable end:** `git rev-parse --short HEAD` naye commit pe; printed frozen hash + mtime; C0 ka exact tuple
screen pe; `128` `succeeded`; C0D pass; `running` `0` aur `pending` `0`.

**KEY:** closed. Bench aur drain kisi Part B sawaal ka jawab nahi kholte.

---

## Step 1 — 15 min: latency ki **definition** likho, column banane se pehle

Aaj koi code nahi, koi migration nahi. Ek file: `docs\daily\week_04\DIN_02_DESIGN.md`. **Teen** H2 headings,
har ek me exactly teen labelled lines: `Chosen:`, `Rejected:`, `Cost:`. C1 ise mechanically padhta hai.

**Terms used in this step**
- **`now()`:** PostgreSQL me ye **transaction start** ka waqt hai. Ek transaction me kitni baar bhi bulao, wahi value.
- **`clock_timestamp()`:** statement execute hone ke waqt ka asli wall clock. Ek hi transaction me do call do values dete hain.
- **`statement_timestamp()`:** teesra option — current statement ke shuru ka waqt. `now()` aur `clock_timestamp()` ke beech.
- **p50 / p99:** distribution ke percentile. `percentile_cont` interpolate karta hai, `percentile_disc` actual data point deta hai.
- **`n`:** distribution me kitne data points hain. `n` ke bina p99 ek naara hai (`P-22`).
- **Server-side vs client-side timestamp:** DB likhe to sab process ek hi ghadi share karte hain; Python likhe to har process apni ghadi laata hai.

### Faisla 1 — latency ka matlab kya hai

| Definition | Kya naapta hai | Kis cheez pe blame lagata hai |
|---|---|---|
| `completed_at - created_at` | end-to-end: queue wait + saare retries + aakhri execution | queue depth **aur** handler dono |
| `completed_at - claimed_at` | sirf aakhri execution | handler, retries chhupa ke |
| `completed_at - created_at` **plus** `attempts` | poori kahani | dono, par ek number nahi rehta |

**Ek chuno, likho, aur Din 5 me wahi chalega.**

Aur ek trap jo aaj naam se likhna hai, kyunki iska mechanism repo me already maujood hai: **heartbeat
`claimed_at = now()` likhta hai har `10 s`** (`src/worker.py`, `send_heartbeat`). Matlab `claimed_at` claim ka
waqt **nahi** hai — wo *"aakhri baar jab is worker ne zinda hone ka signal bheja"* hai. `P-22` ka wahi shape:
number arithmetically sahi, naap raha kuch aur. Ye Part B **Q1** hai aur Step 0 me frozen hona chahiye.

### Faisla 2 — kaunsa clock `completed_at` likhta hai

Iss repo me **dono** pattern already maujood hain, aur ye guess nahi hai:

- `jobs.created_at` → `server_default=func.now()` (`src/models.py`) — `D-08`, DB-generated, **transaction start**.
- `src/reaper.py` → `.returning(Job.status, func.clock_timestamp())` — apne logging me **statement clock**.

`completed_at - created_at` do timestamps ko subtract karta hai. Agar wo do **alag clocks** se aaye to number
ek chhota constant offset carry karega. Aaj wo offset ek measured bound hai, `[INFERRED]` nahi:

```text
[MEASURED-R 2026-09-06, PostgreSQL 16.14, docker compose exec psql]
clock_timestamp() - now(), same transaction:
  first statement after BEGIN   =    535 us
  second statement              =   1178 us
  single-statement (autocommit) =   4200 us   <- ye psql ka round-trip hai, app ka nahi
```

Teesra option jo likhna aur **maarna** hai (AGENTS rule 28): **Python side se `datetime.now(timezone.utc)`.**
Wo do naye problem laata hai jo DB ke paas nahi hain: (a) `created_at` DB clock pe hai, to subtraction do
machine clocks mix karega — aur Din 4 me paanch process hain; (b) worker ka `completed_at` uske apne mark
statement se pehle compute hoga, to `time.sleep` / GC pause seedha number me chala jaayega.

### Faisla 3 — `last_error` me kya jaata hai, aur kya bahar jaata hai

Teen sub-faisle, ek `Chosen/Rejected/Cost` triple me:

- **Kya store hota hai:** `str(exc)` vs `repr(exc)` vs poora traceback. Aaj ke handlers ke asli sizes
  `[MEASURED-R 2026-09-06]` hain: `str(exc)` `32` bytes, `repr(exc)` `48` bytes,
  `traceback.format_exc()` `285` bytes. **Ye numbers guess nahi hain, aur ye Q2 ka maidan hain.**
- **Kya leak hota hai:** exception message me payload ka hissa aa sakta hai. `GET /jobs/{id}` pe auth nahi hai
  (`D-03` ka enumeration argument), aur wo endpoint aaj `job_id` + `status` hi return karta hai
  (`src/main.py`). `last_error` API response me **jaayega ya nahi** — faisla likho, aur default `nahi` hona
  chahiye jab tak auth na aaye.
- **Clearing — ye ek code path hai, faisla nahi:** aaj ka mark `UPDATE` `next_attempt_at` ko success pe `NULL`
  set karta hai (`.values(status=..., next_attempt_at=next_attempt_at)`, aur success pe wo `None` hai).
  `last_error` ko **wahi** treatment chahiye, warna attempt 1 ka error attempt 2 ke `succeeded` row pe pada
  rehta hai aur DLQ ka diagnosis jhootha ho jaata hai. **Ye bhoolna silent hai** — koi error nahi aayega, bas
  data galat hoga. Ye Part B **Q3** hai.

**Executable end:** `DIN_02_DESIGN.md` disk pe, teen headings, har heading me `Chosen:` / `Rejected:` / `Cost:`
teeno non-empty; C1 pass.

**KEY:** C1 pass hone ke baad → **"Open after Step 1 / C1 — Q1"**.

---

## Step 2 — 20 min: migration — `completed_at` + `last_error`, aur teenon gated writes

**Terms used in this step**
- **8 KB heap page:** PostgreSQL disk se **pages** padhta hai, columns nahi. `block_size = 8192` `[MEASURED-R]`. Ek page pe jitni rows fit hoti hain, utni ek read me aa jaati hain.
- **`TOAST_TUPLE_THRESHOLD` = `2032` bytes:** compiled constant. Tuple isse bada hone lage to PostgreSQL pehle `EXTENDED` columns ko **compress** karta hai, aur agar phir bhi bada rahe to **out of line** bhejta hai.
- **`attstorage = 'x'` (EXTENDED):** `text` aur `jsonb` ka default. Matlab "compress karo, phir zaroorat pade to TOAST me bhejo". `[MEASURED-R]` `last_error`, `payload`, `type`, `status` — chaaron `x`.
- **Out-of-line datum:** heap tuple me `18`-byte pointer rehta hai; asli bytes `pg_toast.pg_toast_<oid>` me chunks me jaate hain. Padhne pe ek **extra index lookup + N chunk reads**.
- **`lp_len`:** `heap_page_items()` se aane wala **asli on-disk tuple length**. `pg_column_size()` isse alag cheez hai (neeche trap likha hai).
- **Fast default:** PostgreSQL 11+ me `ADD COLUMN … NOT NULL DEFAULT <constant>` table rewrite nahi karta. Aaj dono naye column **nullable** hain, to ye path lagta hi nahi.
- **Seq scan:** poori table page-by-page padhna. `[MEASURED-R]` worker ka poll aaj yahi karta hai.

### 2A — migration

Ek revision, `down_revision = 'w4d1_claim_generation'`. Repo me custom slug ka precedent hai:

```powershell
.\.venv\Scripts\python.exe -m alembic revision -m "add completed_at and last_error to jobs" --rev-id w4d2_completion_instruments
```

Do columns, dono `NULL`, aur dono ka `NULL` **alag baat** kehta hai:

| Column | Shape | `NULL` ka matlab |
|---|---|---|
| `jobs.completed_at` | `timestamptz NULL` | *"ye row terminal nahi hui"* — aur ye iss schema me `NULL` ka **chautha** meaning hai (`P-19` ne teen gine the, Din 1 ne chautha add kiya: *"jab ye row likhi gayi thi ye column exist hi nahi karta tha"*). Matlab ye **paanchvaan** hai. Isko `DIN_02_DESIGN.md` me likho |
| `jobs.last_error` | `text NULL` | *"is row ki aakhri attempt fail nahi hui"* — aur **`NULL` ≠ empty string**, kyunki `''` ka matlab "fail hui par message khaali tha" hoga |

`downgrade()` **likha jaata hai** aur disposable DB pe chalaya jaata hai (`upgrade head` → `downgrade -1` →
`upgrade head`). Do consecutive migration days hi wo shape hai jisme branch banti hai; `alembic heads` iske
baad **exactly ek** line deni chahiye.

**`P-28` ka guard, kal se copy hota hai, dobara invent nahi hota:** `alembic.ini` line 89 pe
`sqlalchemy.url` **hardcoded** hai aur `alembic/env.py` line 41 `config.get_main_option("sqlalchemy.url")`
padhta hai — matlab `$env:DATABASE_URL` Alembic ke liye **exist hi nahi karta**. Disposable DB ko target karne
ka ek hi safe raasta hai: ini ki ek **copy**, uski `sqlalchemy.url` badli hui, aur `alembic -c <copy>`.

### 2B — code, chaar jagah

**Ready-made code iss BRIEF me nahi hai. SQL ki shape hai; Python tumhari.**

1. **Mark, success path** — `completed_at` set karo, `last_error` **clear** karo, aur **gate wahi rehti hai**:

```sql
UPDATE jobs
   SET status = 'succeeded', next_attempt_at = NULL,
       completed_at = <clock choice from Faisla 2>, last_error = NULL
 WHERE id = :id AND status = 'running' AND claim_generation = :g;
```

2. **Mark, retry path** (`status = 'pending'`) — `completed_at` ko **haath nahi**, `last_error` **likho**:
   ye row terminal nahi hui, to `completed_at` `NULL` rehna chahiye.
3. **Mark, terminal failure path** (`failed` / `dead_letter`) — `completed_at` **aur** `last_error` dono.
4. **Structured log line** — Step 3.

**Aaj ka teesra gate ek naya nahi hai, wahi purana hai:** `completed_at` mark ke usi `UPDATE` me likha jaata
hai, isliye wo `claim_generation = :g` ke **peeche already** hai. Agar tum usko ek alag `UPDATE` me nikalte
ho, tum ek naya un-fenced lifecycle writer bana rahe ho — aur wahi cheez `D-26` ke draft me `Cost` likhi hai.
C4 iska discriminator chalata hai.

**Lease `30 s`, heartbeat `10 s`, poll `2.0 s`, backoff, `MAX_ATTEMPTS = 3`, `effect_key` — aaj kuch nahi badalta.**

### 2C — `last_error` ka disk I/O: aaj ka rule-34 faisla, aur uske numbers measured hain

Naive statement ye hai: *"traceback bada hai → TOAST me jaayega → poll ka `SELECT` TOAST fetch karega → I/O
badhega."* **Measurement iss statement ko todta hai, do jagah se.**

`[MEASURED-R 2026-09-06, PostgreSQL 16.14, disposable DB, `heap_page_items()` se asli `lp_len`]` — ek `jobs`-shaped
table, ek row per size class:

| `last_error` ka kind | raw bytes | `pg_column_size` | **on-disk `lp_len`** | verdict |
|---|---:|---:|---:|---|
| compressible (repeated traceback frames) | `640` | `644` | `724` | inline, raw |
| compressible | `1920` | `1924` | `2004` | inline, raw — threshold ke neeche |
| compressible | `2080` | `207` | **`287`** | **compress hua, inline hi raha** |
| compressible | `3200` | `220` | `300` | compressed inline |
| compressible | `10240` | `298` | **`378`** | `10 KB` value, tuple `378` bytes — **kabhi out of line nahi gaya** |
| incompressible (md5 stream) | `128` | `132` | `212` | inline |
| incompressible | `512` | `516` | `596` | inline |
| incompressible | `2016` | `2016` | **`98`** | **OUT OF LINE** (18-byte pointer) |
| incompressible | `9600` | `9600` | **`98`** | **OUT OF LINE** |

Aur phir 5000 rows pe, teen alag tables, same shape:

```text
[MEASURED-R 2026-09-06]  5000 rows each, block_size 8192
 last_error = NULL                          heap = 112 pages   toast =     0 pages
 last_error = 197-byte traceback (inline)    heap = 250 pages   toast =     0 pages
 last_error = 64000-byte incompressible      heap = 132 pages   toast = 40118 pages
```

**Do cheezein ye numbers kehte hain, aur dono ko `DIN_02_DESIGN.md` me likhna hai:**

- **Python traceback ~10:1 compress hota hai** (repeated file paths, repeated frame text) — isliye wo
  **realistically kabhi TOAST out-of-line nahi jaata**. Yaani "TOAST pointer dereference" wala I/O cost, jo
  AGENTS rule 34 ke hisaab se **ek hi** asli column-level saving hai, `last_error` pe **lagta hi nahi**.
- **Asli I/O cost heap pages ka hai, aur wo column list se independent hai.** `112 → 250` pages ka matlab hai
  poll ka seq scan `2.2×` zyada pages padhega — chahe `last_error` `SELECT` list me ho ya na ho. Aur poll seq
  scan **hai**, ye `[MEASURED-R]` hai:

```text
Limit → LockRows → Sort (quicksort 25 kB) → Seq Scan on jobs
  Filter: status = 'pending' AND (next_attempt_at IS NULL OR next_attempt_at <= now())
  Rows Removed by Filter: 122
  Buffers: shared read=2
```

Aur ek inversion jo likhne layak hai kyunki wo ulti direction me chalti hai: **ek bada out-of-line error poll
ke liye SASTA hai** (`132` pages) ek chhote inline error se (`250` pages), kyunki pointer tuple ko chhota kar
deta hai. `40118` TOAST pages tabhi padhi jaati hain jab koi `last_error` **maangta** hai — aur poll nahi
maangta (`src/worker.py` ka claim `select` sirf `id, type, payload, attempts, claim_generation` leta hai).

**Isliye aaj ka faisla ye nahi hai "TOAST se bacho".** Faisla ye hai: *`last_error` ki inline size ko bounded
rakhna hai ya nahi, aur bound ka reason `jobs` ke heap page count me hai, TOAST me nahi.* Ye Part B **Q2** hai.

**Executable end:** `alembic heads` ek line; disposable lifecycle pass (`head` → `down` → `reup`); evidence DB
upgraded; `pytest tests -q` chala aur **exit code check hua**; C2 pass.

**KEY:** C2 pass hone ke baad → **"Open after Step 2 / C2 — Q2 aur Q3"**.

---

## Step 3 — 20 min: structured lifecycle log, aur wo ek job jo usko prove karti hai

Roadmap ki line: *"Structured logs with `job_id` (ek job ka pura lifecycle trace ho sake)"*.

**Terms used in this step**
- **Structured log line:** ek line jisme fields **machine-splittable** hain (`k=v` ya JSON), prose me embedded nahi.
- **Lifecycle events (aaj ke code me jo already hain):** `claim` · `execute` · `heartbeat` · `effect` · `mark` · `fenced` · `conflict` · `shutdown`.
- **`echo=True`:** `src/database.py` me `create_async_engine(DATABASE_URL, echo=True)`. Har SQL statement **usi stdout** pe jaata hai jisme lifecycle lines. Log bada hoga — ye normal hai.

### Aaj ka minimum

Ek consistent, greppable prefix jisme **chaar** field hon: `job_id`, `worker_id`, `claim_generation`, aur event
ka naam. Aaj ka code already `[worker-<pid>]` prefix aur `job <id>` phrase use karta hai — wo **grep-able nahi
hai** kyunki `job 12` `job 128` se bhi match karta hai, aur `Marked job` SQLAlchemy ke parameter dump se bhi
match kar sakta hai.

```powershell
Get-Content .\logs\w4d2_step3_lifecycle.log | Select-String 'job_id=(\d+)\b' | Select-Object -First 5
Get-Content .\logs\w4d2_step3_lifecycle.log | Select-String "job_id=$step3Job\b"
```

**Aur ek faisla jo aaj lena hai — JSON lines vs `k=v`:** JSON parse karna aasan, par `Select-String` se padhna
mushkil, aur iss hafte ka reader **tum** ho, koi log aggregator nahi. Ulta side: `k=v` ko Din 5 pe `10k` lines
me aggregate karna hand-written regex maangega. Decide karo aur reason likho — *"industry best practice"*
reason **nahi** hai (AGENTS rule 17). Ye `DIN_02_DESIGN.md` me chauthi heading **nahi** banti; ek line kaafi
hai, kyunki iska koi measured discriminator aaj nahi hai.

**Ek cheez jo aaj naam se karni hai:** `fenced` aur `conflict` ki lines me bhi `job_id=` aana chahiye. Din 1 me
`Mark fenced: job_id=<id>` already iss shape me hai; `Conflict on mark: Job <id> …` **nahi** hai. Do lines ek
hi din me do format me rehna wahi cheez hai jisse Din 5 pe grep aadha jawab deta hai.

### Aaj ka witness job — ek `boom`, aur wo `last_error` bhi prove karta hai

`type = "boom"` `MAX_ATTEMPTS = 3` tak jaata hai aur `dead_letter` pe khatam hota hai — matlab ek hi job
teen cheezein prove kar deti hai: retry ka `last_error` likhna, terminal ka `completed_at` likhna, aur teen
attempts ka lifecycle ek `job_id` pe grep hona. Backoff `5 s` → `10 s` (equal jitter), to poori job
`~15–25 s` me khatam hoti hai.

```powershell
$body = @{ type='boom'; payload=@{}
           idempotency_key = "w4d2-step3-$([guid]::NewGuid().ToString('N'))" } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/jobs' -Method Post -ContentType 'application/json' -Body $body
$step3Job = [int]$r.job_id
"STEP3_JOB=$step3Job"
```

```powershell
.\.venv\Scripts\python.exe -u -m src.worker *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d2_step3_lifecycle.log
```

Reaper **band**. `Marking terminal 'dead_letter'` dikhne ke baad `Ctrl+C`, phir C3.

**Executable end:** ek `dead_letter` row jisme `completed_at` non-`NULL` aur `last_error` non-`NULL`; ek grep
jo teen attempts ka poora sequence deta hai; C3 pass.

**KEY:** C3 pass hone ke baad → **"Open after Step 3 / C3 — Q3 ka measured half"**.

---

## Step 4 — 20 min: pehla latency number, aur wo SQL se aata hai

**Terms used in this step**
- **`percentile_cont`:** continuous percentile — data points ke beech **interpolate** karta hai. `interval` pe kaam karta hai `[MEASURED-R]`.
- **`percentile_disc`:** discrete — ek actual maujood value deta hai.
- **`count(col)` vs `count(*)`:** `count(col)` `NULL` skip karta hai. `[MEASURED-R]` `count(*)=3`, `count(col)=1`, `count(*) filter (where col is not null)=1` — aakhri do same hain.
- **`n`:** kitne rows distribution me aaye. Bina `n` ke p99 ek naara hai.

```sql
select count(*) filter (where completed_at is not null) as terminal_with_ts,
       percentile_cont(0.5)  within group (order by completed_at - created_at) as p50,
       percentile_cont(0.99) within group (order by completed_at - created_at) as p99
  from jobs where completed_at is not null;
```

**Aaj ye number chhota aur bekaar hoga** — `n` do-teen hoga (`122` purani rows ka `completed_at` `NULL` hai
aur wo honest hai, kyunki wo timestamps kabhi record nahi hue). Aur wo **theek** hai. Aaj ka point ye hai ki
**query exist karti hai aur chalti hai**, taaki Din 5 pe wahi query `10k` rows pe chale.

`[MEASURED-R 2026-09-06]` `percentile_cont` `interval` pe interpolate karta hai:

```text
input: 3.5 s, 45.2 s, 2.001 s
p50 = 00:00:03.5      p99 = 00:00:44.366      n = 3
```

`p99 = 44.366` **koi actual data point nahi hai** — `percentile_cont` ne `3.5` aur `45.2` ke beech interpolate
kiya. `n = 3` pe p99 ka matlab *"sabse bada value, thoda kam"* hai. Isliye aaj number ke saath `n` likhna
**zaroori** hai, aur `n < 100` pe p99 ko p99 **kehna hi nahi** chahiye.

**Aur ek cheez jo aaj alag likhni hai:** ye latency `succeeded` **aur** `dead_letter` dono ko mix karti hai
(dono terminal hain, dono ka `completed_at` set hai). Step 3 ka `boom` job teen attempts + do backoff sleeps
ke saath `~20 s` legi, aur Step 0 ka drain job `~45 s`. Ek `n = 3` ka p50 jisme ek failure aur ek 45-second
blocking job hai — wo kis cheez ka number hai? **Isko log me naam do**, aur agar tumhe `status` ke hisaab se
alag karna hai to wo ek line ka `group by` hai aur wo aaj hi likh do.

**Executable end:** query chali, teen values screen pe, `n` ke saath log me likhi hui; C4 pass (jo `completed_at`
ka gate discriminator bhi chalata hai).

**KEY:** C4 pass hone ke baad → **"Open after Step 4 / C4 — latency ke traps"**.

---

## Step 5 — 30 min: slipped debt — `45 s` payload + `SIGBREAK` at `T = 3 s`

`D-22` Cost 8 se. Week 3 me **slipped**, Week 3 se pehle bhi ek baar (`CURRENT_WEEK.md`: wo run *"hua, par
uska subject nahi hua"* — `handle_slow` ka default `8.0 s` `30 s` lease ke against chalaya gaya tha, to lease
expire hi nahi ho sakti thi). **Aaj wo actually chalti hai.**

Sawaal jo isne kabhi answer nahi kiya:

> Graceful shutdown kehta hai *"current job finish karke exit"*. Handler `45 s` ka hai, lease `30 s` ka hai.
> `T = 3 s` pe `SIGBREAK` aata hai. **Shutdown pehle poora hota hai ya lease pehle expire hoti hai — aur jab
> reaper beech me reclaim kar leta hai, to shutdown ke waqt worker ka mark ka kya hota hai?**

**Aaj ye run pehli baar generation gate ke saath hoti hai**, aur wahi iska naya hissa hai: mark `fenced` hoga,
`conflict` hoga, ya accept hoga — **teen** possible outcomes, aur teen alag matlab.

**Terms used in this step**
- **`SIGBREAK` / `CTRL_BREAK_EVENT`:** Windows ka console control event. `signal.SIGBREAK` uska Python naam hai. `src/worker.py` isko `hasattr` guard ke peeche register karta hai, `SIGINT`/`SIGTERM` ke saath **same** handler pe.
- **Kyu `SIGBREAK` aur `SIGINT` nahi:** Windows pe `SIGINT` **doosre process ko deliver nahi ho sakta** (`P-15` ka signal caveat). `os.kill(pid, signal.SIGTERM)` Windows pe `TerminateProcess` hai — wo `kill -9` hai jo `SIGTERM` ka naam pehen ke aata hai (Week 1 Din 3 `T-c`, `[MEASURED]`). Isliye script se testable ek hi catchable path `SIGBREAK` hai.
- **Process group:** `CREATE_NEW_PROCESS_GROUP` ke saath spawn kiya process apne group ka **leader** hai. `os.kill(leader_pid, CTRL_BREAK_EVENT)` poore group ko event deta hai. Non-leader pid pe ye **fail** karta hai.
- **`request_shutdown`:** sirf ek global flag set karta hai. Flag **ek hi jagah** padha jaata hai: `while not SHUTDOWN_REQUESTED`, matlab loop ke top pe. Handler ke beech me koi check nahi hai.
- **Yielding vs blocking handler:** `asyncio.sleep(45)` event loop ko chhodta hai; `time.sleep(45)` usko pakad ke baithta hai. Aaj ka **ek** variable yahi hai.

### Payload — ek variable, aur wo `block` hai

Dono run `type = "effect"` hain. Sirf `block` badalta hai. `type` badalna do variables hilaana hai
(AGENTS rule 7), aur `handle_slow` me `block` flag exist hi nahi karta.

| Run | Payload | Kya specifically pooch rahe hain |
|---|---|---|
| **1** | `{"seconds": 45}` | Heartbeat zinda hai (`asyncio.sleep` yield karta hai), lease expire **nahi** hoti. Sawaal sirf shutdown ka: `SIGBREAK` ke baad worker `45 s` pura karta hai ya nahi, aur kab exit karta hai |
| **2** | `{"seconds": 45, "block": true}` | Heartbeat block hai, lease expire hoti hai, reaper reclaim karta hai. **`D-22` Cost 8 ka jawab yahi run deta hai.** Run 1 iska control hai |
| **3** (Q5) | `{"seconds": 45, "block": true}`, **do** worker, doosre ko signal nahi | Ab reclaim ke baad ek doosra claimant maujood hai. `job_executions` aur `side_effects` ke do alag numbers |

**Aur ek cheez jo Run 2 me alag se record karni hai, aur ye plan ka naam-liya sawaal hai:** `time.sleep()` ke
**andar** `CTRL_BREAK_EVENT` ka **Python-level** handler kab chalta hai — turant, ya `time.sleep` khatam hone
pe? **Ye measure karna hai, predict nahi.** Log me `Signal SIGBREAK received` line ka timestamp dhoondho aur
usko signal bhejne ke timestamp se subtract karo. Agar handler late chala, to **Run 2 ka shutdown timing
number Run 1 se compare karne layak nahi hai** — aur wo khud ek finding hai, irritation nahi.

### 5A — harness (repo root pe, `src/` me nahi)

Ye `src/` code nahi hai, ye ek measurement instrument hai — Week 1 ka `Popen` + `os.kill` mechanism, par
uss din ka script kisi commit me nahi bacha (`P-23` ka shape). Isliye aaj ye file **disk pe rehti hai** aur
uska path log me likha jaata hai.

`harness_sigbreak.py`:

```python
"""Spawn src.worker in a new process group, wait for an anchor line, send CTRL_BREAK_EVENT.

Usage:
  python -u harness_sigbreak.py "<anchor regex>" <delay_seconds> <log path>
Log format matches the PowerShell wrapper: 'yyyy-MM-dd HH:mm:ss.fff|<line>' in UTC,
so Get-LogEvent works across the worker log, the reaper log, and this one.
"""
import os, re, signal, subprocess, sys, threading, time
from datetime import datetime, timezone

anchor = re.compile(sys.argv[1])
delay = float(sys.argv[2])
log = open(sys.argv[3], "w", encoding="utf-8", buffering=1)

def stamp(text):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.") + f"{datetime.now(timezone.utc).microsecond // 1000:03d}"
    line = f"{ts}|{text}"
    log.write(line + "\n")
    print(line, flush=True)

proc = subprocess.Popen(
    [sys.executable, "-u", "-m", "src.worker"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
)
stamp(f"[harness] spawned group_leader_pid={proc.pid} anchor={anchor.pattern!r} delay={delay}")

hit = threading.Event()

def pump():
    for raw in proc.stdout:
        text = raw.rstrip("\r\n")
        stamp(text)
        if not hit.is_set() and anchor.search(text):
            stamp(f"[harness] ANCHOR matched")
            hit.set()

threading.Thread(target=pump, daemon=True).start()

if not hit.wait(timeout=180):
    stamp("[harness] ANCHOR never matched; aborting without signal")
    proc.kill(); sys.exit(2)

time.sleep(delay)
os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
stamp(f"[harness] CTRL_BREAK_EVENT sent to group {proc.pid}")

t0 = time.perf_counter()
rc = proc.wait()
stamp(f"[harness] child exited rc={rc} signal_to_exit={time.perf_counter() - t0:.3f}s")
time.sleep(0.5)
log.close()
```

**Anchor line ka choice load-bearing hai.** Use `Executing job <id>` — wo `run_worker` me handler se **just
pehle** print hota hai, aur **dono** run me identical hai. `Blocking event loop` sirf Run 2 me aata hai, to
usko anchor banane se Run 1 aur Run 2 ka `T = 0` do alag jagah se ginne lagta hai. Anchor aur asli handler
start ke beech ek `record_execution` DB round trip hai — wo `[MEASURED]` karo, `[INFERRED]` mat chhodo.

### 5B — Run 1: yielding, reaper live

```powershell
$body = @{ type='effect'; payload=@{ seconds=45 }
           idempotency_key = "w4d2-run1-$([guid]::NewGuid().ToString('N'))" } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/jobs' -Method Post -ContentType 'application/json' -Body $body
$run1Job = [int]$r.job_id
"RUN1_JOB=$run1Job"
```

Reaper pehle (apne log ke saath), phir harness:

```powershell
# terminal 1 — reaper
.\.venv\Scripts\python.exe -u -m src.reaper *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d2_run1_reaper.log

# terminal 2 — harness (worker spawn + signal at T+3s)
.\.venv\Scripts\python.exe -u harness_sigbreak.py "Executing job $run1Job\b" 3.0 .\logs\w4d2_run1_worker.log
```

Snapshots: **teen**, aur teeno C5 ka hissa hain — `T ≈ 4 s` (signal ke turant baad), `T ≈ 33 s` (jahan lease
expire hoti agar heartbeat zinda na hoti), aur harness ke `child exited` ke baad.

### 5C — Run 2: blocking, reaper live, ek variable badla

**Sirf `block: true` add hota hai.** Baaki sab byte-for-byte same: same `type`, same `seconds`, same reaper,
same anchor, same `3.0`, ek worker.

```powershell
$body = @{ type='effect'; payload=@{ seconds=45; block=$true }
           idempotency_key = "w4d2-run2-$([guid]::NewGuid().ToString('N'))" } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/jobs' -Method Post -ContentType 'application/json' -Body $body
$run2Job = [int]$r.job_id
"RUN2_JOB=$run2Job"
```

Logs: `.\logs\w4d2_run2_reaper.log`, `.\logs\w4d2_run2_worker.log`.

**Teen snapshots, aur `P-29` ka reason:** final row crash/reclaim ko prove **nahi** karti. Isliye:

| # | Kab | Kya capture karna hai |
|---|---|---|
| S1 | signal ke turant baad (`T ≈ 4 s`) | `status`, `attempts`, `claim_generation`, `claimed_at`, `completed_at`, `last_error` |
| S2 | reaper ki `matched=1 post_status=pending` line ke turant baad | wahi chha field — **aur specifically `claim_generation` badla ya nahi** |
| S3 | harness ke `child exited` ke baad | wahi chha field |

### 5D — Run 3 (Q5): do worker, doosre ko signal nahi

Run 2 se **ek** variable badalta hai: ek doosra worker bhi chal raha hai. A wahi harness-spawned worker hai
(usko signal milta hai); B seedha PowerShell wrapper se chalta hai (usko signal **nahi** jaana hai).

**Launch order — Din 1 Step 1 se copy hota hai, dobara invent nahi hota:**

| # | Terminal | Kab |
|---|---|---|
| 1 | **reaper** (`w4d2_run3_reaper.log`) | sabse pehle. Khaali queue pe sirf `candidates=0 reclaimed=0` |
| 2 | **harness → worker A** (`w4d2_run3_worker.log`) | reaper ke baad. A polling shuru karta hai |
| 3 | **enqueue** | A ke `Starting worker process` ke baad. A `2.0 s` ke andar claim karega |
| 4 | **worker B** (`w4d2_run3_worker_b.log`) | **A ka `Blocking event loop (45.0s)...` line dikhne ke baad.** Command pehle se type karke rakho, sirf Enter dabana hai |

B ko A ke claim **ke baad** uthana zaroori hai. Ulta order me B pehle claim kar lega (dono ek jaisa poll karte
hain) aur run **void** ho jaayega — signal galat worker ko jaayega. Void run ko log me likho, chhupao mat.

```powershell
$body = @{ type='effect'; payload=@{ seconds=45; block=$true }
           idempotency_key = "w4d2-run3-$([guid]::NewGuid().ToString('N'))" } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/jobs' -Method Post -ContentType 'application/json' -Body $body
$run3Job = [int]$r.job_id
"RUN3_JOB=$run3Job"
```

```powershell
# terminal 2 — harness → worker A (signal isko milta hai)
.\.venv\Scripts\python.exe -u harness_sigbreak.py "Executing job $run3Job\b" 3.0 .\logs\w4d2_run3_worker.log

# terminal 4 — worker B, koi signal nahi
.\.venv\Scripts\python.exe -u -m src.worker *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d2_run3_worker_b.log
```

**Ek chicken-and-egg jo yahan hai aur Run 1/Run 2 me nahi tha:** harness ka anchor regex me `$run3Job` chahiye,
matlab **enqueue pehle hoga aur harness baad me**. Iska matlab job `pending` me `2–5 s` baithegi jab tak A up
nahi hota — aur uss dauran **B usko utha lega** agar B pehle se chal raha ho. Isliye Run 3 ka order upar wali
table me hai: **B sabse aakhir me**. Agar tumhe B ko pehle chahiye, to anchor `Executing job \d+` rakho aur
job id log se padho — par tab tum manually verify karoge ki anchor **A** ki line thi, aur wo ek extra manual
step hai jo galat ho sakta hai.

**`CTRL_BREAK_EVENT` B tak nahi pahunchega, aur ye assumption nahi hai:** signal `GenerateConsoleCtrlEvent`
se ek **process group id** pe jaata hai. Harness ne A ko `CREATE_NEW_PROCESS_GROUP` ke saath spawn kiya, to A
apne group ka leader hai. B apne shell ke group me hai. Agar tumne B ko **usi** harness terminal se chalaya, to
ye separation toot jaata hai — B ko apna terminal do.

### Stop rule — isko padhe bina Run 3 shuru mat karo

**Run 3 apne aap khatam nahi hoti.** B ka handler bhi `45 s` ka hai aur lease `30 s` ki hai, to B bhi apna
lease outlive karta hai. B ko koi signal nahi mila, matlab uska loop chalta rehta hai: reclaim → claim →
`45 s` → mark reject → poll → claim. `attempts` aur `job_executions` badhte rehte hain.

Isliye: **A ke mark ki line (`Mark fenced` / `Conflict on mark`) aur `child exited` dikhte hi — usi minute —
C5 ka Run 3 block chalao, phir B ko `Ctrl+C` aur reaper ko `Ctrl+C`.** Wall clock note karo. **`attempts`,
`job_executions`, aur `side_effects` ke numbers snapshot ke time pe depend karte hain** — isliye teeno ke
saath snapshot ka UTC time likhna zaroori hai, warna numbers compare karne layak nahi.

`Ctrl+C` B ko `time.sleep(45)` ke beech me milega. **Wo turant rukega ya `45 s` pura karega — ye measure karna
hai, predict nahi.** Jo hua wo log me likho.

**Agar time khatam ho raha hai:** Run 3 kata ja sakta hai. Uska seedha nateeja: **Q5 `[NO EVIDENCE]` band hoti
hai**, C4b ka data nahi milta, aur log me `slipped` uske owner (Din 4 ka interleaving A) ke saath likha jaata
hai. Run 1 aur Run 2 **kabhi nahi** kat sakte.

**Executable end:** saat logs (`w4d2_run1_worker.log`, `w4d2_run1_reaper.log`, `w4d2_run2_worker.log`,
`w4d2_run2_reaper.log`, `w4d2_run3_worker.log`, `w4d2_run3_worker_b.log`, `w4d2_run3_reaper.log`); har run ka
`signal_to_handler_s` **aur** `signal_to_exit_s` harness se; Run 2 ka teen-snapshot table; Run 3 ka snapshot
UTC time ke saath; C5 pass (C5 me closing bench, chain, aur cleanup bhi hai).

**KEY:** C5 ke baad → **"Open after Step 5 / C5 — Q4 aur Q5"**. Uske baad **"Known traps"**, phir
**"Final scoring rubric"** kholo aur frozen text ko `/5` pe grade karo. Post-run prose ko credit nahi milta.

---

## Din close pe reviewer ko kya dena hai

Plan ka DOC-SYNC Din 2 ke liye: `logs/WEEK_04.md` · `PROBLEMS.md` · `ddia_summaries/DDIA_CH11_LINKS.md`
(**slipped debt close**). `DECISIONS.md` me aaj **kuch nahi** — `D-28` (observability) Din 6 ka hai, aur uska
`Cost` Din 5 ke latency numbers ke bina likha nahi ja sakta.

**`DDIA_CH11_LINKS.md` ka repair, naam se:** uss file ka reviewer-close (`2026-08-31`) kehta hai ki uske
right-hand mappings apne hi rule ko satisfy nahi karte kyunki `D-24` aur `D-25` uss din exist nahi karte the.
`[MEASURED-R 2026-09-06]` **aaj wo dono `DECISIONS.md` me hain** (`D-24` two-layer idempotency, `D-25`
execute-time dedup). Matlab aaj ka kaam ek line ka hai: teen mappings ko un asli headings pe re-anchor karo,
aur jo line **abhi bhi** attach nahi hoti usko *"abhi attach nahi hui"* likho — jhoothi attach mat karo.
`DDIA_CH8_LINKS.md` lines 10–13 aaj ka scope **nahi** hai (wo carried debt hai, Din 6 pe naam se).

`P-` number chahiye to **uss din grep karo** (`E6`). `[MEASURED-R 2026-09-06]` aaj ka expected next-free
**`P-30`** hai (`PROBLEMS.md` ka last entry `P-29`), aur `D-` ka next-free **`D-26`** — par register hi sach hai.

Reviewer ko chhe cheezein chahiye: `DIN_02_PREDICTIONS_FROZEN.md` + printed hash, `DIN_02_DESIGN.md`,
`harness_sigbreak.py`, saare `w4d2_*.log`, Run 2 ka teen-snapshot table, aur C0–C6 ka raw output.

---

# Part B — Prediction questions — **Gemini ko paste mat karna**

> Step 0 me **paanchon** answer aur freeze karo, Step 1 shuru hone se pehle. `idk` valid hai aur `0` score
> karta hai. `idk — <sahi jawab>` bhi `0` hai. Inke jawab iss block me nahi hain, aur BRIEF me kahin nahi hain.

```text
Q1. completed_at - claimed_at ko latency maana jaaye, aur handler 45 s ka ho jisme heartbeat har 10 s pe
    claimed_at = now() likhta hai (yielding handler, lease kabhi expire nahi hoti). Computed latency kya
    aayegi, aur wo asli execution time se kitni alag hogi? Number likho, aur mechanism.

Q2. last_error me poora Python traceback jaata hai. Worker ka poll SELECT jobs ki rows uthata hai par
    last_error ko SELECT list me nahi maangta. Poll ka disk I/O badhta hai ya nahi — aur AGENTS.md rule 34
    ke hisaab se KIS EXACT CONDITION me badhta hai? (Do alag cases hain; dono likho.)

Q3. Ek job retry hoti hai: attempt 1 fail (last_error likha), attempt 2 succeed. Attempt 2 ke baad row me
    last_error kya hoga? Ye behaviour tumhare implementation ka faisla hai — likho ki tum kya CHAHTE ho,
    aur phir kya HOGA agar tum aaj ke mark UPDATE me last_error ko chhedte hi nahi.

Q4. Run 2: type=effect, payload {"seconds": 45, "block": true}, lease 30 s, SIGBREAK at T = 3 s, reaper
    live, generation gate lagi hui, EK worker. T = 50 s par teen cheezein:
    (a) worker process zinda hai ya exit kar gaya?
    (b) row ka status kya hai?
    (c) completed_at set hai ya NULL — aur worker ka mark accept hua, `fenced` hua, ya `conflict` hua?

Q5. Run 3: wahi Run 2, par ab DO worker hain aur doosre ko SIGBREAK nahi mila. Us job ke liye
    job_executions me kitni rows hongi, aur side_effects me kitni? Do numbers alag-alag likho, aur kyu.
```

---

# Part C — Verification

Sab **PowerShell 7** syntax hai aur repo root `d:\PROJECTS\relay` se chalta hai. `docker compose` service ka
naam **`db`** hai (container ka naam `relay-db-1`; commands me service naam use hota hai). PostgreSQL **16.14**,
port **5433**, `-U postgres -d relay`. Jahan `throw` hai wahan step **rukta** hai — stray worker chala ke state
"repair" mat karna. **`&&` kahin nahi hai; PowerShell me separator `;` hai.**

**Har check ke saath do column hain: mechanism maujood, aur mechanism ghayab. Jis check ka dono column same
output deta hai, wo check decorative hai (`P-18`).**

## C0 — Din 1 committed, opening bench, seal, single Alembic head

Seal command ke **usi terminal** me:

```powershell
if (-not $d2FrozenHash) { throw 'Step 0C hash variable missing; C0 must run in the same PowerShell terminal' }
$frozen = 'docs\daily\week_04\DIN_02_PREDICTIONS_FROZEN.md'
if ((Get-FileHash $frozen -Algorithm SHA256).Hash -ne $d2FrozenHash) { throw 'Frozen predictions changed after Step 0C' }
"D2_FROZEN_SHA256_UNCHANGED=$d2FrozenHash"

# Din 1 ka code commit me hona chahiye, warna aaj ki migration ek untracked migration pe chadhegi
$dirty = @(git status --porcelain=v1 -- src alembic)
$dirty
if ($dirty.Count -ne 0) { throw "src/ or alembic/ is dirty before Din 2 starts. Step 0A pehle poora karo:`n$($dirty -join "`n")" }
$head = (git rev-parse --short HEAD).Trim()
"HEAD=$head"
if ($head -eq '87f2253') { throw 'HEAD is still the Week 3 close commit; Din 1 was not committed (Step 0A)' }
@(git log --oneline -3)

$env:DATABASE_URL = 'postgresql+asyncpg://postgres:relay@localhost:5433/relay'
$runtimeDb = (& .\.venv\Scripts\python.exe -c "from src.database import engine; print(engine.url.database)") -join ''
if ($runtimeDb.Trim() -ne 'relay') { throw "Runtime DB mismatch: $runtimeDb" }
"python_runtime_database=relay"

$relayProcs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper|dispatcher)' })
$relayProcs | Select-Object ProcessId, ParentProcessId, CommandLine
if ($relayProcs.Count -ne 0) { throw "Relay process count is $($relayProcs.Count), expected 0" }
"relay_processes=0   (reminder: one logical worker = 2 rows here, venv shim + interpreter)"

$heads = @(& .\.venv\Scripts\python.exe -m alembic heads 2>&1 | Where-Object { $_ -match '\(head\)' })
$heads | ForEach-Object { "ALEMBIC_HEAD: $_" }
if ($heads.Count -ne 1) { throw "Expected exactly one Alembic head, got $($heads.Count)" }
```

```powershell
$sql = @'
set time zone 'UTC';
select concat_ws('|', current_database(), count(*), max(id),
  (select last_value from jobs_id_seq),
  (select count(*) from job_executions),
  (select last_value from job_executions_id_seq),
  (select count(*) from side_effects),
  (select last_value from side_effects_id_seq),
  (select version_num from alembic_version)) from jobs;
select concat_ws('|',
  count(*) filter (where status='succeeded'),
  count(*) filter (where status='failed'),
  count(*) filter (where status='pending'),
  count(*) filter (where status='dead_letter'),
  count(*) filter (where status='running'),
  count(*)) from jobs;
select coalesce(string_agg(id::text||':'||status||':'||attempts::text||':'||claim_generation::text, ',' order by id), 'none')
  from jobs where status in ('running','pending');
select count(*) from pg_stat_activity
  where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select count(*) from pg_database where datname like 'relay_w4%';
select count(*) from information_schema.columns
  where table_name='jobs' and column_name in ('completed_at','last_error');
select concat_ws('|', count(*) filter (where claim_generation is null), count(claim_generation), count(*))
  from job_executions;
'@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'C0 SQL failed' }
$actual = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$actual
$expected = @(
  'relay|122|128|128|116|123|11|16|w4d1_claim_generation',
  '103|15|0|3|1|122',
  '128:running:2:2',
  '0',
  '0',
  '0',
  '113|3|116'
)
if (($actual -join "`n") -ne ($expected -join "`n")) {
  throw "C0 fingerprint mismatch.`nACTUAL:`n$($actual -join "`n")`nEXPECTED:`n$($expected -join "`n")"
}
'C0=pass'

# C2 hardcoded 113 se compare nahi karega — pre-migration counts yahan capture hote hain
$preExecNull  = [int]($actual[6].Split('|')[0])
$preExecTotal = [int]($actual[6].Split('|')[2])
$preJobsTotal = [int]($actual[0].Split('|')[1])
"PRE_EXEC_NULL=$preExecNull  PRE_EXEC_TOTAL=$preExecTotal  PRE_JOBS_TOTAL=$preJobsTotal"
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Din 1 commit me hai** | `src`/`alembic` clean, `HEAD` `87f2253` se alag, `git log` me Din 1 ka message | Dirty ya wahi `HEAD` → aaj ki migration ek untracked migration pe chadhegi, aur `downgrade -1` ka blame do din me bat jaayega |
| Bench Din 1 close se match | `relay|122|128|128|116|123|11|16|w4d1_claim_generation` | Koi bhi farq → **divergence**, Din 2 rukta hai jab tak cause naam se na mile (`E2`) |
| Carried row ka **exact shape** assert hua | `128:running:2:2` — ek hi row, `running`, `attempts=2`, generation `2` | Sirf count match karta par shape na hoti → Step 0D ka expected outcome guess ban jaata. Aur `pending` bucket `0` hai, matlab aaj koi purana `pending` nahi hai |
| `completed_at`/`last_error` **exist nahi karte** | `information_schema.columns` count `0` | Non-zero → migration pehle se chal chuki hai, aur Step 2 ka before/after compare khatam |
| Single head | ek `(head)` line | Do heads → branch ban gayi. Ye **doosri** consecutive migration hai, matlab aaj wo shape maujood hai |
| Koi Relay process zinda nahi | `relay_processes=0` | Ek purana worker → wo `128` ya Din 2 ki job claim kar lega aur attribution khatam (`P-13`) |
| Frozen predictions immutable | hash unchanged | Hash badla → uss sawaal ka score `seal broken` |

## C0D — job `128` ka resolution, alag line me

```powershell
$sql = @'
select concat_ws('|','row128', id, status, attempts, claim_generation,
  coalesce(next_attempt_at::text,'NULL'), coalesce(claimed_at::text,'NULL')) from jobs where id = 128;
select concat_ws('|','exec128', count(*), count(distinct worker_id),
  string_agg(coalesce(claim_generation::text,'NULL'), ',' order by id)) from job_executions where job_id = 128;
select concat_ws('|','eff128', count(*)) from side_effects where job_id = 128;
select concat_ws('|','totals', (select count(*) from jobs), (select count(*) from job_executions),
  (select count(*) from side_effects), (select last_value from side_effects_id_seq),
  (select count(*) from jobs where status='running'), (select count(*) from jobs where status='pending'));
select concat_ws('|','stale_gen_exec', count(*)) from job_executions e join jobs j on j.id = e.job_id
  where e.claim_generation is not null and e.claim_generation <> j.claim_generation;
'@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
$out = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
if ($out[0] -notmatch '^row128\|128\|succeeded\|3\|3\|NULL\|') { throw "Job 128 drain shape wrong: $($out[0])" }
if ($out[1] -ne 'exec128|3|3|1,2,3')  { throw "Job 128 execution stamps wrong: $($out[1]) — expected three dispatches, generations 1,2,3" }
if ($out[2] -ne 'eff128|1')           { throw "Job 128 effect count wrong: $($out[2]) — effect_key dedup toota" }
'C0D=pass'
```

Expected shape:

```text
row128|128|succeeded|3|3|NULL|<ts>
exec128|3|3|1,2,3
eff128|1
totals|122|117|11|17|0|0
stale_gen_exec|2
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| `128` ek hi extra dispatch me terminal hui | `attempts = 3`, generation `3`, `exec` `3|3|1,2,3` | `attempts ≥ 4` ya generation `≥ 4` → reaper `30 s` ke andar band nahi hua aur fence phir lagi. Wo ek asli finding hai (Din 1 ke *"loop apne aap nahi rukta"* ka teesra witness) — log me likho, phir dobara chalao |
| `side_effects` **hila nahi**, par `seq` hila | `eff128|1` aur `side_effects_id_seq` `16 → 17` | Rows `2` → `effect_key` ka scope toota. Seq **nahi** hila → doosra dispatch `INSERT` tak pehancha hi nahi, matlab `1` "dedup ne kaam kiya" ka evidence nahi hai (`ON CONFLICT DO NOTHING` identity default evaluate karta hai, isliye seq delta expected hai) |
| Queue actually khaali hai | `running` `0` **aur** `pending` `0` | Non-zero → Step 5 ka reaper ek purani row utha lega aur Run 1/Run 2 ka delta contaminated |
| `jobs` count / max nahi badle | `122` aur `128` | Badle → drain ke dauran koi enqueue hua, aur Din 2 ka baseline shift ho gaya |
| Stale-generation audit aage badha | `stale_gen_exec` `1 → 2` | `2` nahi aaya → ya naya dispatch stamp nahi hua, ya generation nahi badhi. Ye query pehli baar Din 1 pe bola thi; aaj uska **delta** check hota hai |

## C1 — Step 1 ka design file, structural gate

```powershell
$design = 'docs\daily\week_04\DIN_02_DESIGN.md'
if (-not (Test-Path $design)) { throw "Missing $design" }
$text = (Get-Content $design -Raw) -replace "`r`n","`n"
$sections = [regex]::Matches($text,'(?ms)^## (?<title>[^\n]+)\n(?<body>.*?)(?=^## |\z)')
if ($sections.Count -ne 3) { throw "Expected exactly 3 '## ' decision sections, got $($sections.Count)" }
foreach ($s in $sections) {
  $title = $s.Groups['title'].Value.Trim()
  $body  = $s.Groups['body'].Value
  foreach ($label in 'Chosen','Rejected','Cost') {
    $m = [regex]::Match($body,"(?m)^\s*(?:[-*]\s*)?(?:\*\*)?$label(?:\*\*)?\s*:\s*(?<v>.+)$")
    if (-not $m.Success)                           { throw "[$title] missing '${label}:' line" }
    if ($m.Groups['v'].Value.Trim().Length -lt 20) { throw "[$title] '${label}:' too short to be a reason" }
  }
  "OK: $title"
}
# naam se maare gaye alternatives file me hone chahiye
if ($text -notmatch '(?i)heartbeat')            { throw 'Faisla 1 ka trap (heartbeat claimed_at ko aage dhakelta hai) file me nahi hai' }
if ($text -notmatch '(?i)clock_timestamp')      { throw 'Faisla 2 ka doosra clock (clock_timestamp) file me nahi hai' }
if ($text -notmatch '(?i)datetime|python.*clock|client.?side') { throw 'Faisla 2 ka maara hua option (Python-side timestamp) file me nahi hai' }
if ($text -notmatch '(?i)heap|page')            { throw 'Faisla 3 me heap page reasoning nahi hai — TOAST-only reason rule 34 ke against adhoora hai' }
if ($text -notmatch '(?i)traceback')            { throw 'Faisla 3 ka store-kya-hota-hai option file me nahi hai' }
if ($text -notmatch '(?i)auth')                 { throw 'Faisla 3 ka leak side (API exposure without auth) file me nahi hai' }
'C1=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Teen faisle, teenon ka rejected option likha hua | 3 sections × (`Chosen`/`Rejected`/`Cost`) | Sirf `Chosen` → wo faisla nahi, wo preference hai (AGENTS rule 28) |
| Latency ka trap naam se maujood | `heartbeat` mention Faisla 1 me | Missing → `claimed_at`-based definition Din 5 pe chup-chaap jhooth bolegi (`P-22`) |
| Clock ka faisla dono option ke saath | `now()` **aur** `clock_timestamp()` dono, aur Python-side option maara hua | Ek clock ka naam → doosra clock repo me already maujood hai (`reaper.py`), aur mixing ka sawaal implicitly rah jaayega |
| `last_error` ka I/O reason **heap pages** pe hai | `heap`/`page` mention | Sirf TOAST reason → rule 34 ka ulta padh liya. Measured numbers kehte hain traceback out-of-line jaata hi nahi |
| Leak side likha hua | `auth` mention | Missing → `last_error` API me chala jaayega aur `D-03` ka argument dobara |

**Note:** ye gate structure check karta hai, reasoning ki quality nahi. Ek khaali-dimaag se bhari hui file bhi
pass karegi — reasoning reviewer padhega. Isko fully-automated proof mat samajho.

## C2 — migration: disposable lifecycle pehle, phir evidence DB

**Order badla to `P-28` ka discriminator kaam nahi karega.**

```powershell
$disposable = "relay_w4d2_life_$PID"
$iniCopy    = ".\_w4d2_$PID.ini"
try {
  docker compose exec -T db psql -X -Atq -U postgres -d postgres -c "create database $disposable" 2>&1
  ((Get-Content .\alembic.ini -Raw) -replace 'sqlalchemy\.url = .*', "sqlalchemy.url = postgresql+psycopg://postgres:relay@localhost:5433/$disposable") |
    Set-Content -Path $iniCopy -Encoding utf8
  (Select-String -Path $iniCopy -Pattern '^sqlalchemy\.url').Line   # target on screen, before any DDL

  $q = "select 'X|'||(select version_num from alembic_version)||'|'||(select count(*) from information_schema.columns where table_name='jobs' and column_name in ('completed_at','last_error'));"

  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy upgrade head
  if ($LASTEXITCODE -ne 0) { throw 'disposable upgrade head failed' }
  ($q -replace "'X\|'", "'head|'") | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $disposable

  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy downgrade -1
  if ($LASTEXITCODE -ne 0) { throw 'downgrade -1 failed — ye aaj pakda gaya, Din 4/5 pe nahi' }
  ($q -replace "'X\|'", "'down|'") | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $disposable

  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy upgrade head
  if ($LASTEXITCODE -ne 0) { throw 're-upgrade head failed' }
  ($q -replace "'X\|'", "'reup|'") | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $disposable

  # P-28 discriminator: evidence DB ko chhua bhi nahi gaya
  $g = "select 'evidence_untouched|'||(select version_num from alembic_version)||'|'||(select count(*) from information_schema.columns where table_name='jobs' and column_name in ('completed_at','last_error'));"
  $ev = @($g | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
        ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
  $ev
  if ($ev[0] -ne 'evidence_untouched|w4d1_claim_generation|0') {
    throw "P-28 fired: disposable ka Alembic evidence DB pe chala. ACTUAL: $($ev[0])"
  }
} finally {
  docker compose exec -T db psql -X -Atq -U postgres -d postgres -c "drop database if exists $disposable" 2>&1 | Out-Null
  Remove-Item $iniCopy -Force -ErrorAction SilentlyContinue
  "cleanup|$((@("select count(*) from pg_database where datname like 'relay_w4d2%';" | docker compose exec -T db psql -X -Atq -U postgres -d postgres) | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })[0])"
}
```

Expected teen lines: `head|w4d2_completion_instruments|2` → `down|w4d1_claim_generation|0` →
`reup|w4d2_completion_instruments|2`, phir `evidence_untouched|w4d1_claim_generation|0`, phir `cleanup|0`.

Ab evidence DB upgrade karo:

```powershell
& .\.venv\Scripts\python.exe -m alembic upgrade head        # alembic.ini already relay pe point karta hai (P-28)
if ($LASTEXITCODE -ne 0) { throw 'evidence upgrade failed' }
$heads = @(& .\.venv\Scripts\python.exe -m alembic heads 2>&1 | Where-Object { $_ -match '\(head\)' })
if ($heads.Count -ne 1) { throw "Expected one head after migration, got $($heads.Count)" }
$heads

if (-not $preJobsTotal) { throw 'PRE_JOBS_TOTAL missing; C0 se lo, 122 hardcode mat karo' }
$sql = @"
select concat_ws('|','completed_col', data_type, is_nullable, coalesce(column_default,'NONE'))
  from information_schema.columns where table_name='jobs' and column_name='completed_at';
select concat_ws('|','error_col', data_type, is_nullable, coalesce(column_default,'NONE'))
  from information_schema.columns where table_name='jobs' and column_name='last_error';
select concat_ws('|','backfill', count(*) filter (where completed_at is null),
  count(*) filter (where last_error is null), count(*)) from jobs;
select concat_ws('|','storage', attname, attstorage::text) from pg_attribute
  where attrelid='jobs'::regclass and attname in ('last_error','payload') order by attname;
select concat_ws('|','pages', (pg_relation_size('jobs'::regclass)/8192),
  coalesce((select pg_relation_size(reltoastrelid)/8192 from pg_class where oid='jobs'::regclass),0));
"@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
$out = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
if ($out[0] -ne 'completed_col|timestamp with time zone|YES|NONE') { throw "jobs.completed_at shape wrong: $($out[0])" }
if ($out[1] -ne 'error_col|text|YES|NONE')                        { throw "jobs.last_error shape wrong: $($out[1])" }
if ($out[2] -ne "backfill|$preJobsTotal|$preJobsTotal|$preJobsTotal") {
  throw "Backfill wrong. Expected all $preJobsTotal rows NULL on both columns. ACTUAL: $($out[2])"
}
if ($out[3] -ne 'storage|last_error|x') { throw "last_error storage is not EXTENDED: $($out[3])" }
'C2_catalog=pass'

& .\.venv\Scripts\python.exe -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw "pytest exit=$LASTEXITCODE — Layer A red after migration. Ye ek asli finding hai, isse aage mat jao." }
'C2_pytest=pass   (Week 3 baseline: 7 passed)'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Purani rows pe dono column `NULL`** | `backfill|122|122|122` | Koi non-`NULL` → migration ne ek value **manufacture** ki. `completed_at = now()` de dena `122` rows ke liye ek jhoothi completion time likh deta, aur Step 4 ka p50 turant `[NO EVIDENCE]` ban jaata |
| `completed_at` ka koi default nahi | `NONE` | `DEFAULT now()` → column `updated_at` ban gaya, `completed_at` nahi, aur `NULL` ka *"terminal nahi hui"* meaning khatam |
| `last_error` `EXTENDED` hai | `storage|last_error|x` | `p` (PLAIN) → compression aur out-of-line dono band, aur ek bada error tuple ko `8160` bytes ki limit pe le jaayega → `INSERT`/`UPDATE` **fail** karega |
| Migration reversible hai | `head|…|2` → `down|…|0` → `reup|…|2` | `downgrade` fail → Din 4/Din 5 ki disposable DB uss din tootegi jab time nahi hoga |
| Alembic ne **evidence** DB ko nahi chhua | `evidence_untouched|w4d1_claim_generation|0` | Kuch aur → `P-28` fired: disposable ka command `relay` pe gaya |
| Disposable DB bacha nahi | `cleanup|0` | Non-zero → Din 4/5 ki naming collide karegi |
| Regression gate chala **aur exit code check hua** | `C2_pytest=pass` | Din 1 me ye gate sirf exit code **print** karta tha, `throw` nahi karta tha — ek red suite step ko continue karwa deti thi. **Par green bhi safety ka proof nahi:** `tests/din5/test_model.py` pure in-memory hai, migration ko dekh hi nahi sakta |

## C3 — lifecycle log + `last_error` / `completed_at` ka retry semantics

```powershell
if (-not $step3Job) { throw 'STEP3_JOB missing; enqueue wale terminal se hi C3 chalao' }
$log = '.\logs\w4d2_step3_lifecycle.log'
if (-not (Test-Path $log)) { throw "Missing $log" }

# 1. grep se poora lifecycle — aur word-boundary galat match nahi laata
$hits = @(Get-Content $log | Where-Object { ($_ -split '\|',2)[1] -match "job_id=$step3Job\b" })
"lifecycle_lines=$($hits.Count)"
$hits | ForEach-Object { "LC: $_" }
foreach ($ev in 'claim','execute','mark') {
  $n = @($hits | Where-Object { $_ -match "(?i)\b$ev\b" }).Count
  "event_$ev=$n"
  if ($n -lt 1) { throw "No '$ev' line carries job_id=$step3Job — grep ek job ka aadha jeevan hi dega" }
}
# 2. prefix decay check: kitni lines me job number hai PAR job_id= nahi hai
$decay = @(Get-Content $log | Where-Object {
  $b = ($_ -split '\|',2)[1]
  $b -match "\bjob $step3Job\b" -and $b -notmatch 'job_id='
})
"unstructured_job_lines=$($decay.Count)"
$decay | ForEach-Object { "UNSTRUCTURED: $_" }
if ($decay.Count -gt 0) { throw "$($decay.Count) lifecycle lines mention the job without job_id= — Din 5 pe grep aadha jawab dega" }
'C3_log=pass'
```

```powershell
$sql = @"
select concat_ws('|','row', id, status, attempts, claim_generation,
  coalesce(completed_at::text,'NULL'),
  coalesce(length(last_error)::text,'NULL'),
  coalesce(pg_column_size(last_error)::text,'NULL'),
  coalesce(next_attempt_at::text,'NULL')) from jobs where id = $step3Job;
select concat_ws('|','exec', count(*), count(distinct worker_id),
  string_agg(coalesce(claim_generation::text,'NULL'), ',' order by id)) from job_executions where job_id = $step3Job;
select concat_ws('|','terminal_ts', status, count(*), count(completed_at)) from jobs group by status order by status;
select concat_ws('|','errored', count(*) filter (where last_error is not null),
  count(*) filter (where status='succeeded' and last_error is not null),
  coalesce(max(length(last_error))::text,'NULL')) from jobs;
select concat_ws('|','ondisk', h.lp_len) from heap_page_items(get_raw_page('jobs', (select (ctid::text::point)[0]::int from jobs where id = $step3Job))) h
  where h.lp = (select (ctid::text::point)[1]::int from jobs where id = $step3Job);
"@
$raw = @($sql | docker compose exec -T db psql -X -Atq -U postgres -d relay)
$out = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
$row = $out[0].Split('|')
if ($row[2] -ne 'dead_letter')  { throw "Expected dead_letter, got $($row[2]) — boom job MAX_ATTEMPTS tak pahunchi nahi" }
if ($row[3] -ne '3')            { throw "Expected attempts=3, got $($row[3])" }
if ($row[5] -eq 'NULL')         { throw 'completed_at NULL on a terminal row — terminal transition ne timestamp nahi chhoda' }
if ($row[6] -eq 'NULL')         { throw 'last_error NULL on a dead_letter row — failure ne reason nahi chhoda' }
if ($out[1] -ne "exec|3|1|1,2,3") { throw "Execution stamps wrong: $($out[1]) — teen dispatch, ek worker, generations 1,2,3 expected" }
'C3_rows=pass'
```

> `heap_page_items` ke liye `pageinspect` extension chahiye. Nahi hai to:
> `docker compose exec -T db psql -X -Atq -U postgres -d relay -c "create extension if not exists pageinspect"`.
> Ye ek **read-only introspection** extension hai; agar tum ise install nahi karna chahte, `ondisk` line chhod
> do aur log me `not recorded` likho — `pg_column_size` uska substitute **nahi** hai (neeche wajah).

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| `completed_at` **sirf** terminal pe | `terminal_ts` me `succeeded`/`failed`/`dead_letter` pe `count(*) == count(completed_at)`, aur `pending`/`running` pe `count(completed_at) = 0` | `pending` rows pe timestamp → wo `updated_at` hai, `completed_at` nahi. **Aaj purani `122` rows iss check ko chhupa sakti hain** — isliye `group by status` chahiye, ek global count nahi |
| `last_error` retry ke baad clear hota hai | `errored` ka doosra field `0` — koi `succeeded` row jispe error pada ho | Non-zero → attempt 1 ka error attempt 2 ke success pe pada hai, aur DLQ ka diagnosis jhootha ho gaya. **Ye failure silent hai**: koi exception nahi aayega |
| **Ek job ka lifecycle ek grep se aata hai** | `claim`/`execute`/`mark` teeno lines `job_id=` ke saath, aur `unstructured_job_lines=0` | Aadhi lines me `job_id` nahi → grep ek hissa deta hai. Aur `job 12` ka grep `job 128` ko bhi match karega, isliye `\b` ke bina ye check khud jhootha hai |
| Teen attempts, ek worker, teen generations | `exec|3|1|1,2,3` | `1,1,1` → claim generation nahi badha raha, aur Din 1 ka monotonic claim aaj hi toot gaya |
| `last_error` **out of line gaya ya nahi** | `ondisk` ka `lp_len` `length(last_error)` se **bada** → inline. `lp_len ≈ 98` → out of line | `pg_column_size` se ye decide karna **galat** hai: `[MEASURED-R]` ek `2016`-byte out-of-line value ka `pg_column_size` `2016` aata hai (pointer ka `18` nahi), aur ek `10240`-byte compressed-inline value ka `298`. Sirf `lp_len` sach bolta hai |

## C4 — pehla latency number, **aur** `completed_at` ka fence discriminator

### C4a — number, `n` ke saath

```powershell
$sql = @'
select concat_ws('|','latency',
  count(*) filter (where completed_at is not null),
  coalesce(percentile_cont(0.5)  within group (order by completed_at - created_at)::text,'NULL'),
  coalesce(percentile_cont(0.99) within group (order by completed_at - created_at)::text,'NULL'),
  coalesce(min(completed_at - created_at)::text,'NULL'),
  coalesce(max(completed_at - created_at)::text,'NULL'))
  from jobs where completed_at is not null;
select concat_ws('|','latency_by_status', status,
  count(*), percentile_cont(0.5) within group (order by completed_at - created_at)::text)
  from jobs where completed_at is not null group by status order by status;
select concat_ws('|','negative', count(*)) from jobs
  where completed_at is not null and completed_at < created_at;
select concat_ws('|','clockgap_us', round(extract(epoch from (clock_timestamp() - now()))*1000000)::text);
'@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
$out = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
$n = [int]($out[0].Split('|')[1])
if ($n -lt 1) { throw 'n = 0 — koi terminal row completed_at ke saath nahi. Query chalti hai par kuch naapti nahi' }
"LATENCY_N=$n"
if ($n -lt 100) { "WARNING: n=$n. Ye p50 hai; ise p99 KEHNA nahi hai. Din 5 pe n >= 100 chahiye." }
if (($out | Where-Object { $_ -match '^negative\|' }) -ne 'negative|0') {
  throw "completed_at < created_at on some row — clock choice ya mark path galat hai"
}
'C4a=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Query chalti hai **aur** `n` bolti hai | `latency|<n>|<p50>|<p99>|<min>|<max>`, aur `n` log me likha hua | `n` report na karna → `n = 2` pe `p99` likhna ek naara hai (`P-22`). `[MEASURED-R]` `n=3` pe `percentile_cont` ne `p99 = 44.366` diya jo **kisi row me nahi tha** — wo `3.5` aur `45.2` ke beech interpolation tha |
| Latency ek **kind** naapti hai | `latency_by_status` alag rows deta hai, aur log me likha hai ki global p50 kis mix se aaya | Sirf global number → ek `dead_letter` (`~20 s`, teen attempts + do backoff) aur ek `45 s` blocking job ka p50 kis cheez ka number hai, ye kabhi answer nahi hoga |
| Do clocks mix nahi hue | `negative|0` | Non-zero → `completed_at` `created_at` se pehle hai, matlab do alag clock sources hain. `[MEASURED-R]` `now()`→`clock_timestamp()` gap ek short txn me `535–1178 us` hai, to `negative` sirf tab aayega jab clock **source** galat ho, jitter se nahi |

### C4b — `completed_at` fenced worker se **nahi** likha jaata

Ye Din 1 ke Step 4 setup ka dobara-chalna hai, par aaj ka question `completed_at` hai. **`45 s` blocking +
`30 s` lease + reaper live + do worker** = A fenced hoga. Iska ek chhota version Step 5 Run 3 me already
aa jaata hai — **agar Run 3 chala, to C4b ka data wahin se aata hai aur alag run ki zaroorat nahi.**

Run 3 (ya ek dedicated run) ke baad:

```powershell
if (-not $run3Job) { throw 'RUN3_JOB missing — C4b ke liye Run 3 (ya ek equivalent fenced run) chahiye' }
$sql = @"
select concat_ws('|','fencecheck', id, status, attempts, claim_generation,
  coalesce(completed_at::text,'NULL'), coalesce(length(last_error)::text,'NULL')) from jobs where id = $run3Job;
"@
$out = @(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
         ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
$fenceLines = @(Get-Content .\logs\w4d2_run3_worker.log | Where-Object { ($_ -split '\|',2)[1] -match "fenced.*job_id=$run3Job\b.*rowcount=0" })
$fenceLines | ForEach-Object { "FENCE: $_" }
"fence_lines=$($fenceLines.Count)"
if ($fenceLines.Count -lt 1) {
  'NOTE: zero fenced lines — ye pass nahi hai, ye "test nahi hua" hai (P-12). Kya B ne claim kiya tha? reaper live tha?'
}
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| `completed_at` gate ke **peeche** hai | Fenced worker ke `rowcount=0` ke baad row pe **ek hi** `completed_at` (ya `NULL`), aur wo fresh generation ka | Do writes ka last-write-wins, ya `completed_at` set jabki `status` `pending` hai → gate `completed_at` ke `UPDATE` me lagana bhool gaye, ya `completed_at` ek **alag** `UPDATE` me nikal diya. Doosra case hi asli khatra hai kyunki wo ek naya un-fenced lifecycle writer banata hai |
| Fence ko stale writer **mila** | `fence_lines >= 1` | `0` → fence ko kabhi stale writer mila hi nahi (`P-12`). `completed_at` ka gate iss run se **untested** hai, aur log me wahi likhna hai |
| Gate sabko reject nahi karta | C3 ka `boom` job aur C0D ka `128` dono terminal hue, `completed_at` set | Wo bhi `rowcount=0` → gate hamesha false hai, aur `fenced` ka koi matlab nahi (`P-18` ka negative control) |

## C5 — teen SIGBREAK run, closing bench, chain, cleanup

### C5a — per-run timeline, teeno run ke liye alag

```powershell
function Get-LogEvent {
  param([string]$Path,[string]$Pattern)
  $hit = @(Get-Content $Path | Where-Object { ($_ -split '\|',2)[1] -match $Pattern })
  if ($hit.Count -eq 0) { return $null }
  [datetime]::ParseExact(($hit[0] -split '\|',2)[0],'yyyy-MM-dd HH:mm:ss.fff',[cultureinfo]::InvariantCulture)
}

function Show-Run {
  param([string]$Tag,[int]$JobId,[string]$WorkerLog,[string]$ReaperLog)
  "==== $Tag  job=$JobId ===="
  $spawn   = Get-LogEvent $WorkerLog 'harness\] spawned group_leader_pid'
  $exec    = Get-LogEvent $WorkerLog "Executing job $JobId\b"
  $anchor  = Get-LogEvent $WorkerLog 'harness\] ANCHOR matched'
  $sent    = Get-LogEvent $WorkerLog 'harness\] CTRL_BREAK_EVENT sent'
  $sigline = Get-LogEvent $WorkerLog 'Signal SIGBREAK received'
  $hbLost  = Get-LogEvent $WorkerLog "Heartbeat lost: job $JobId\b"
  $done    = Get-LogEvent $WorkerLog "Work completed for job $JobId\b"
  $mark    = Get-LogEvent $WorkerLog "(Marked job $JobId as|Mark fenced: job_id=$JobId\b|Conflict on mark: Job $JobId\b)"
  $clean   = Get-LogEvent $WorkerLog 'Clean shutdown complete'
  $exit    = Get-LogEvent $WorkerLog 'harness\] child exited'
  $reclaim = if ($ReaperLog -and (Test-Path $ReaperLog)) { Get-LogEvent $ReaperLog "id=$JobId pre_status=running matched=1 post_status=pending" } else { $null }

  foreach ($p in @(@('spawn',$spawn),@('exec_line',$exec),@('anchor',$anchor),@('signal_sent',$sent),
                   @('SIGBREAK_line',$sigline),@('reaper_reclaim',$reclaim),@('heartbeat_lost',$hbLost),
                   @('handler_done',$done),@('mark',$mark),@('clean_shutdown',$clean),@('child_exit',$exit))) {
    if ($p[1]) { '{0,-16} {1:HH:mm:ss.fff}' -f $p[0], $p[1] } else { '{0,-16} not recorded' -f $p[0] }
  }
  if ($exec -and $sent)    { "  T0_to_signal_s      = $([math]::Round(($sent    - $exec).TotalSeconds,3))" }
  if ($sent -and $sigline) { "  signal_to_handler_s = $([math]::Round(($sigline - $sent).TotalSeconds,3))   <- ye number Run 1 vs Run 2 me alag hai to timings comparable NAHI hain" }
  if ($sent -and $exit)    { "  signal_to_exit_s    = $([math]::Round(($exit    - $sent).TotalSeconds,3))" }
  if ($exec -and $done)    { "  handler_wall_s      = $([math]::Round(($done    - $exec).TotalSeconds,3))" }
  # mark ka LABEL — teen possible, teen alag matlab
  $label = @(Get-Content $WorkerLog | Where-Object { ($_ -split '\|',2)[1] -match "(Marked job $JobId as '|Mark fenced: job_id=$JobId\b|Conflict on mark: Job $JobId\b)" })
  if ($label.Count -eq 0) { '  mark_label       = not recorded  <- iske bina D-22 Cost 8 ka jawab adhoora hai' }
  $label | ForEach-Object { "  MARK: $_" }
}

Show-Run 'RUN1 yielding'  $run1Job '.\logs\w4d2_run1_worker.log'   '.\logs\w4d2_run1_reaper.log'
Show-Run 'RUN2 blocking'  $run2Job '.\logs\w4d2_run2_worker.log'   '.\logs\w4d2_run2_reaper.log'
if ($run3Job) { Show-Run 'RUN3 blocking+2workers' $run3Job '.\logs\w4d2_run3_worker.log' '.\logs\w4d2_run3_reaper.log' }
```

Aur DB side, teeno run ke liye:

```powershell
$ids = @($run1Job, $run2Job) + @(if ($run3Job) { $run3Job })
$idList = ($ids -join ',')
$sql = @"
select concat_ws('|','row', id, status, attempts, claim_generation,
  coalesce(completed_at::text,'NULL'), coalesce(length(last_error)::text,'NULL'),
  coalesce(claimed_at::text,'NULL'), coalesce(next_attempt_at::text,'NULL')) from jobs where id in ($idList) order by id;
select concat_ws('|','exec', job_id, count(*), count(distinct worker_id),
  string_agg(coalesce(claim_generation::text,'NULL'), ',' order by id))
  from job_executions where job_id in ($idList) group by job_id order by job_id;
select concat_ws('|','eff', job_id, count(*)) from side_effects where job_id in ($idList) group by job_id order by job_id;
select concat_ws('|','effseq', (select last_value from side_effects_id_seq), (select count(*) from side_effects));
"@
@(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Do run, alag-alag likhe hue, ek variable ka farq** | Run 1 aur Run 2 ka timeline side by side, aur payload me sirf `block` ka farq | Ek hi run report hui, ya `block` flag log me likha hi nahi → shutdown aur lease-expiry do variables ek saath hile, conclusion `not isolated` (AGENTS rule 7). **Ya** sirf final row report ki → `P-29` dobara |
| Lease Run 1 me **nahi** expire hoti, Run 2 me hoti hai | Run 1: `reaper_reclaim` `not recorded`, aur reaper log me sirf `candidates=0`. Run 2: `reaper_reclaim` ~`T+30–32 s` | Run 1 me bhi reclaim → heartbeat chal hi nahi raha tha, aur Run 1 control ban hi nahi paaya. Run 2 me reclaim nahi → `block` flag payload me nahi gaya |
| **`signal_to_handler_s` alag se recorded hai** | Dono run ke liye ek number | Sirf `signal_to_exit_s` → agar ek run me Python handler late chala, to shutdown latency ka comparison meaningless hai aur wo pata bhi nahi chalega |
| Mark ka **label** recorded hai, teenon me se ek | `Marked job … as` / `Mark fenced:` / `Conflict on mark:` — line log me | `not recorded` → `D-22` Cost 8 ka jawab adhoora. **Aur teen labels teen alag baatein hain:** accept = koi ne cheena nahi; `fenced` = generation badal chuki thi; `conflict` = generation wahi thi par `status` badal chuka tha (`Q5` Case A, Din 1 KEY) |
| Heartbeat ka apna signal | Run 2 me `Heartbeat lost: job <id>` line hai ya `not recorded` | Run 2 me heartbeat lost line **hai** → matlab heartbeat task `time.sleep` ke dauran chala, jo blocking claim ko contradict karta hai. Ye ek asli finding hai, dono taraf |
| `side_effects` count vs seq | Run 3 me `eff|<id>|1` par `side_effects_id_seq` ka delta rows ke delta se **bada** | Seq delta barabar → doosre worker ka handler `INSERT` tak pehancha hi nahi, aur `1` "dedup ne kaam kiya" ka evidence nahi hai |

### C5b — closing bench, chain, cleanup

**Din 1 ka C5 SQL error deta tha** (`aggregate functions are not allowed in GROUP BY` — teen `*_by_day` queries
ne `GROUP BY 1` ko ek aggregate expression pe lagaya tha). Yahan wo fix hai: date expression pe group karo,
positional reference pe nahi.

```powershell
$frozen = 'docs\daily\week_04\DIN_02_PREDICTIONS_FROZEN.md'
if ((Get-FileHash $frozen -Algorithm SHA256).Hash -ne $d2FrozenHash) { throw 'Frozen predictions changed during the day' }
'frozen_unchanged=True'

$relayProcs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper|dispatcher)|harness_sigbreak' })
$relayProcs | Select-Object ProcessId, ParentProcessId, CommandLine
if ($relayProcs.Count -ne 0) { throw "Din 2 ke baad $($relayProcs.Count) Relay process zinda hain (P-13). Yaad rakho: ek logical worker = 2 rows" }

$sql = @'
set time zone 'UTC';
select concat_ws('|','close', count(*), max(id), (select last_value from jobs_id_seq),
  (select count(*) from job_executions), (select last_value from job_executions_id_seq),
  (select count(*) from side_effects), (select last_value from side_effects_id_seq),
  (select version_num from alembic_version)) from jobs;
select concat_ws('|','status', status, count(*), count(completed_at), count(last_error)) from jobs group by status order by status;
select concat_ws('|','jobs_by_day', d::text, c) from (
  select created_at::date as d, count(*) as c from jobs where id > 128 group by created_at::date) x order by d;
select concat_ws('|','exec_by_day', d::text, c) from (
  select executed_at::date as d, count(*) as c from job_executions where job_id > 128 group by executed_at::date) x order by d;
select concat_ws('|','effect_by_day', d::text, c) from (
  select created_at::date as d, count(*) as c from side_effects where job_id > 128 group by created_at::date) x order by d;
select concat_ws('|','carried_128_day', d::text, c) from (
  select executed_at::date as d, count(*) as c from job_executions where job_id = 128 group by executed_at::date) x order by d;
select concat_ws('|','idle_in_txn', count(*)) from pg_stat_activity
  where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select concat_ws('|','probe_dbs', (select count(*) from pg_database where datname like 'relay_w4%'));
select concat_ws('|','stale_gen_exec', count(*)) from job_executions e join jobs j on j.id = e.job_id
  where e.claim_generation is not null and e.claim_generation <> j.claim_generation;
select concat_ws('|','pages', (pg_relation_size('jobs'::regclass)/8192),
  coalesce((select pg_relation_size(reltoastrelid)/8192 from pg_class where oid='jobs'::regclass),0));
select concat_ws('|','seq_gaps', string_agg(g::text, ',' order by g)) from
  (select generate_series(1,(select max(id) from jobs)) g except select id from jobs) s;
'@
@(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })

Get-ChildItem .\logs\w4d2_*.log | Select-Object Name, Length, LastWriteTime
Get-Item .\harness_sigbreak.py | Select-Object FullName, Length, LastWriteTime
git status --porcelain=v1 -- src alembic
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **C5 ka SQL actually chalta hai** | Saari lines print hoti hain, `ON_ERROR_STOP=1` ke saath exit `0` | Error → Din 1 ka bug dobara. Ek check jo error deta hai wo `pass` nahi hai, aur usko `C5=pass` likhna log ko jhootha karta hai |
| Chain per-day `group by` se juda, `max(id)` se nahi | `jobs_by_day` / `exec_by_day` / `effect_by_day`, aur unka jod din ki report se match | Sirf total match → do compensating errors chhup sakti hain (Week 2 ka wahi bug) |
| Carried `128` ka delta **alag line** me | `carried_128_day` apni line me, aur wo `exec_by_day` me count **nahi** hota (`job_id > 128` filter) | Ek line me judna → Step 0D ka `+1` execution Din 2 ke experiments me chala jaayega |
| `completed_at`/`last_error` per-status honest hain | `status|<s>|<n>|<completed>|<errors>`, aur `pending`/`running` pe `completed` `0` | `pending` pe non-zero → `completed_at` `updated_at` ban gaya |
| `jobs` ke heap pages ka **naya** number | `pages|<heap>|<toast>` — Din 2 ka opening `2|0` tha | Iska badhna expected hai (naye rows + inline `last_error`). Ye number Din 5 ke poll I/O baseline hai; aaj record na karna Din 5 pe ek baseline chheen leta hai |
| Koi process zinda nahi | `0` | Non-zero → agla din contaminated (`P-13`) |
| Koi disposable DB nahi bachi | `probe_dbs|0` | Non-zero → Din 4/5 collide karega |
| Sequence reset nahi hua | `seq_gaps` me `79,117,118,119,120,122` **aur** aaj ke naye gaps, `jobs_id_seq >= max(id)` | Gaps gayab → `P-05` toota, aur teen hafte ka evidence rewrite ho gaya |
| `logs/` ka evidence disk pe hai | `w4d2_*.log` files, non-zero length, aur `harness_sigbreak.py` maujood | Missing → `-u`/harness chhoot gaya, aur ordering proof gaya (`P-29`). `.gitignore` me `*.log` hai, matlab ye evidence **sirf disk pe** hai |
| Naya code commit hone layak hai | `git status` me sirf aaj ki expected files | `docs/LEARNING_LOG.md`/`docs/logs/WEEK_03.md` bhi modified hain aur wo Din 1 se pehle ke hain — unhe aaj ke commit me **naam se** hi lena |

---

# Part D — Scope guard: aaj **nahi**

| Kya | Owner | Aaj karne se kya khota hai |
|---|---|---|
| Transactional outbox, `src/dispatcher.py`, receiver + `sink_deliveries` | **Din 3** | Aaj `completed_at` ka clock aur `last_error` ka bound decide hote hain. Outbox usi din add karna teen naye columns aur ek naya process ek run me hilaana hai (AGENTS rule 7) |
| Do asli worker ka witness **disposable DB** pe, chaar interleavings | **Din 4** | Aaj ke teen run **evidence DB** pe hain aur wo jaan-boojh ke hai — inka delta chain me jaata hai. Din 4 ka rule ulta hai: evidence DB delta `0`. Dono ek din me karne se dono rules toot jaate hain |
| Pool override (`pool_size=2, max_overflow=0`), Locust, `10k`, `/healthz`, p50/p99 `n >= 100` pe | **Din 5** | Aaj ka `n` do-teen hai aur wo theek hai. Aaj pool chhedne se latency number aur pool dono ek saath hilenge |
| `D-28` (observability) ka `Cost` / final text | **Din 6** | Aaj sirf `DIN_02_DESIGN.md`. `Cost` ke liye Din 5 ke numbers chahiye — bina unke wo ek guess hai |
| Handler timeout (`asyncio.wait_for`) | **Month 2 ka pehla item** (`P-15`) | Aaj ka Run 2 exactly wo shape hai jise timeout band karta hai. Aaj timeout add karne se `D-22` Cost 8 ka jawab **kabhi** nahi milega — measurement pehle, fix baad me (`D-21` ka pattern) |
| `attempts < :max` claim gate | **Month 2, agar kabhi** | `P-27` ka overdraft `D-23` me **accept** kiya hua hai. `128` ka `attempts = 3` aaj bhi usi bound ka witness hai |
| `last_error` ko `GET /jobs/{id}` me expose karna | **auth ke baad** | `D-03`: sequential ids + no auth + error text = exfiltration surface. Aur error text me payload ka hissa aa sakta hai |
| `last_error` pe truncation ko "TOAST se bachne ke liye" justify karna | **kabhi nahi** | Measured numbers isse todte hain: traceback ~10:1 compress hota hai aur out-of-line **jaata hi nahi**. Truncation ka asli reason **heap page count** hai (`112 → 250` pages, 5000 rows). Galat reason likhna `DECISIONS.md` ko bekaar karta hai (AGENTS rule 18) |
| `jobs.status` ya `next_attempt_at` pe index banana | **Din 5 ke numbers ke baad** | Poll aaj seq scan hai (`Buffers: shared read=2`, `122` rows). `2` pages pe index ka argument nahi banta; `10k` rows pe banega |
| Lease `30 s`, heartbeat `10 s`, poll `2.0 s`, backoff, `effect_key` badalna | **kabhi nahi, iss hafte** | Week 2–4 ke saare measurements inhi numbers pe khade hain. Aaj ka Run 1 vs Run 2 ka poora contrast `45 > 30` pe khada hai |
| Job `128` ko `DELETE` karna, ya `UPDATE` se terminal karna | **kabhi nahi** | Step 0D usko **chalata** hai. `95`, `108`, `110`, `115`, `126` ko bhi haath nahi (`P-05`) |
| `DDIA_CH8_LINKS.md` lines 10–13 | **Din 6** | Aaj sirf `DDIA_CH11_LINKS.md` ka re-anchor (`D-24`/`D-25` ab exist karte hain). Dono ek din me karne se Ch 8 ka repair bhi jaldi me hoga |
