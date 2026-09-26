# Week 4 Din 1 BRIEF — fencing: pehle nuksaan, phir monotonic epoch

**Week 4 · Din 1** · Plan: [`../../planning/WEEK_04.md`](../../planning/WEEK_04.md) ·
Log: [`../../logs/WEEK_04.md`](../../logs/WEEK_04.md) (aaj banegi) ·
Sealed: [`DIN_01_KEY.md`](DIN_01_KEY.md)

**Goal:** `status` ke compare-and-set ko generation-aware banao — **aur pehle prove karo ki uske bina ek
stale writer asli nuksaan karta hai.**

**Architectural invariant (aaj ke baad):**
> Ek `jobs` row pe koi bhi lifecycle write (heartbeat, mark) sirf uss worker se accept hoti hai jiske paas
> uss row ka **current** `claim_generation` hai. `claim_generation` per row **monotonically increasing** hai —
> `status` cycle karta hai, generation nahi.

**Deliverable:** ek migration · claim/heartbeat/mark generation-gated · ek **measured stale-write rejection**
(`rowcount = 0`, stale worker ke stdout me, naam wali line) · `D-26` ka draft (`Problem` + `Options` only;
`Cost` Din 4 ke real-process witness ke baad).

**Budget:** `20 + 30 + 25 + 40 + 25 = 140 min`. Overflow `+5`. Cut order plan me likha hai: **Step 0 ka drain
run agle din subah ho sakta hai, par Step 1 se pehle.** Step 1–4 me se kuch nahi kata.

---

## Rules — ye teen roz wahi hain

> **Paste rule:** Part A, Part C, Part D Gemini ko ja sakte hain. **Part B kabhi nahi. KEY kabhi nahi.**
>
> **Seal rule:** paanchon answers **Step 0 me** freeze honge, Step 1 shuru hone se pehle. Har KEY section
> tabhi khulta hai jab uss step ka **measurement** ho chuka ho — prediction likhne ke baad nahi. Output
> prediction se alag nikla to **pehle apni explanation likho**, phir Gemini ke saath uss output pe reason karo
> (outcome ab secret nahi), phir KEY.
>
> **Provenance rule:** iss BRIEF ka bench `[MEASURED-R 2026-09-05]` hai — generation ke waqt read-only
> `psql` se padha gaya, tumhara Din 1 measurement nahi. Jo tum chalao wo `[MEASURED]`. Jo iss file me
> `[INFERRED]` likha hai wo **prediction nahi hai**, wo ek assumption hai jise C-block todh sakta hai.

### Read order — isko literally follow karo

1. Sirf **Step 0** padho.
2. Editor outline se seedha **Part B** pe jao. Step 1–4 aur Part C abhi mat kholo.
3. Paanch predictions likho (`idk` valid hai aur `0` score karta hai), phir Step 0 ke **seal command** pe
   wapas aao.
4. Frozen hash print hone ke baad **Part C ka C0** kholo. C0 pass ho tab Step 1 aur baaki Part A/Part C khulte
   hain.

Part A ko Gemini ko tabhi paste karna jab frozen hash already exist karta ho.

### Do cheezein jo plan me likhi hain aur aaj **kaam nahi karengi** — ye divergence nahi hai, ye pehle se pata hai

| Plan kehta hai | Reality | Aaj kya karna hai |
|---|---|---|
| *"Frozen file uss step se pehle **commit** hoti hai, `git log` mtime se strong evidence hai"* | `.gitignore` me `docs/daily/` hai — ye file stage hi nahi ho sakti | Commit ki jagah **printed SHA-256 + `LastWriteTime`**. Wahi hash C0 aur C5 dono me dobara assert hota hai |
| Verification row: *"`job_executions` → `107` (historical rows honest `NULL`)"* | `107` **Din 1 ke pehle** ka number hai. Step 0 ka drain `+4` aur Step 1 ka run `+2` deta hai, to migration ke waqt honest-`NULL` count `113` hai | C3 hardcoded `107` se compare **nahi** karega. C1 pre-migration count ko `$preMigrationExecutions` me capture karta hai; C3 usse compare karta hai |

---

# Part A — Steps

## Step 0 — 20 min: opening bench, paanch predictions freeze, aur chaar carried jobs ka drain run

**Terms used in this step**
- **Evidence DB:** `relay` — teen hafte ka permanent record. Rows `DELETE` nahi hoti, sequence reset nahi hota (`P-05`).
- **Opening bench:** pehli database read. Ye Week 3 ke close ke saath match karni chahiye; na kare to Din 1 rukta hai (`E2`).
- **Drain run:** Week 3 ke close pe bache chaar `pending` rows ko jaan-boojh ke chalana, taaki Din 1 ka experiment sirf Din 1 ki banayi hui job pe ho. Inka delta **alag line** me log hota hai.
- **Frozen prediction:** answer ki immutable copy + SHA-256, measurement se pehle. Post-run explanation prediction credit nahi leti.
- **`-u` / `PYTHONUNBUFFERED`:** Python ka stdout jab file/pipe pe jaata hai to block-buffered ho jaata hai. `-u` usko unbuffered karta hai. Aaj ke saare ordering proofs stdout se aate hain, isliye ye optional nahi hai.

### 0A — logs folder aur environment

`logs/` repo me exist nahi karta (`[MEASURED-R 2026-09-05]`), aur `.gitignore` me `*.log` hai — matlab aaj ka
stdout evidence **sirf disk pe** rahega, commit me nahi. Har naye terminal me pehli do lines yahi hain.

```powershell
New-Item -ItemType Directory -Path .\logs -Force | Out-Null
$env:PYTHONUNBUFFERED = "1"
$env:DATABASE_URL     = 'postgresql+asyncpg://postgres:relay@localhost:5433/relay'
```

### 0B — predictions likho aur freeze karo

1. `docs\daily\week_04\DIN_01_ANSWERS.md` banao. Part B ke paanch sawaal **exactly** copy karo. Structure:
   `## Q1` … `## Q5`, aur har ek ke neeche exactly `### Prediction`, `### Observed + meri explanation`,
   `### After KEY`.
2. `### Prediction` non-empty (`idk` valid). Baaki do blocks freeze ke waqt **khaali**.
3. Phir neeche ka seal command **usi PowerShell terminal** me chalao (C5 usi variable ko dobara maangega).

```powershell
$answers = 'docs\daily\week_04\DIN_01_ANSWERS.md'
$frozen  = 'docs\daily\week_04\DIN_01_PREDICTIONS_FROZEN.md'
if (-not (Test-Path $answers)) { throw "Missing $answers" }
if (Test-Path $frozen) { throw "Frozen file already exists; overwrite forbidden: $frozen" }

$text = (Get-Content $answers -Raw) -replace "`r`n","`n"
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
$d1FrozenHash = (Get-FileHash $frozen -Algorithm SHA256).Hash
$d1FrozenTime = (Get-Item $frozen).LastWriteTimeUtc.ToString('o')
"D1_FROZEN_SHA256=$d1FrozenHash"
"D1_FROZEN_MTIME_UTC=$d1FrozenTime"
```

Dono lines log me chipka do. Ab **Part C ka C0** kholo aur chalao.

### 0C — drain run: chaar carried rows

C0 pass hone ke baad. **Reaper band, exactly ek worker.** Chaar rows — `116, 121, 123, 124` — chaaron
`type = sleep`, `attempts = 0`, `next_attempt_at = NULL` (`[MEASURED-R 2026-09-05]`), yaani chaaron pehle claim
pe hi chalengi aur inme se koi bhi `effect` handler nahi hai.

```powershell
.\.venv\Scripts\python.exe -u -m src.worker *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d1_step0_drain.log
```

Chaar `Marked job … as 'succeeded'` lines dikhein to `Ctrl+C`. Phir **C0D** chalao. Iska delta Din 1 ke
experiment ke delta me **nahi** judta — log me alag line, alag heading.

**Executable end:** printed frozen hash + mtime; C0 ka exact tuple screen pe; drain ke baad C0D pass; `pending`
`0`; drain delta apni alag line me likha hua.

**KEY:** closed. Opening output aur drain outcome kisi Part B sawaal ka jawab nahi kholte.

---

## Step 1 — 30 min: stale write ka nuksaan reproduce karo, **fencing se pehle**

Ye `D-21` ka established pattern hai — **instrument/harm pehle, fix baad me.** Aaj ka harm
`WEEK_03_HANDOFF.md` ke *"Status Cycle vs Monotonic Epochs"* me **recognisable** likha hai par kabhi **run**
nahi hua.

**Terms used in this step**
- **Compare-and-set (CAS):** `UPDATE … WHERE <expected old state>`. `rowcount = 1` matlab maine jeeta, `0` matlab mera expected state ab sach nahi hai.
- **Lease:** `30 s`. Reaper `running` row ko `pending` kar deta hai agar `claimed_at` `30 s` se purana ho.
- **Heartbeat:** har `10 s` `claimed_at = now()` — lease ko aage dhakelta hai. Ye ek `asyncio` task hai, matlab isko chalne ke liye event loop free chahiye.
- **Blocking handler:** `time.sleep()` — event loop ko block karta hai. `asyncio.sleep()` yield karta hai. Farq iss experiment ka poora mechanism hai.
- **Stale writer:** wo worker jiska lease chhin gaya, par jiska handler abhi bhi chal raha hai.
- **Generation-blind:** aaj ka mark `WHERE status = 'running'` hai. Ye "kaunsa claim" nahi poochta, sirf "koi claim hai kya" poochta hai.

### Mechanism naam se — kyunki ye already commit me hai (`P-23`)

`type = "effect"`, `payload = {"seconds": 45, "block": true}`.

- `block: true` → `handle_effect` me `time.sleep(45)` chalta hai → event loop block → `send_heartbeat` task
  **run hi nahi kar paata** → `claimed_at` T=0 pe atka rehta hai → lease `30 s` pe expire hoti hai.
- `block` ke bina `asyncio.sleep` yield karta hai, heartbeat har `10 s` `claimed_at` aage dhakelta hai, aur
  lease **kabhi** expire nahi hoti — Week 2 Din 3 Run 2 ka record: job 96, `40.295 s` aage, zero duplicate.

**Naya handler mat likho, naya flag mat banao, `MAX_ATTEMPTS`/lease/backoff ko haath mat lagao.**

### Aaj ka observable **effect count nahi hai**

Effect count ko `UNIQUE uq_side_effects_effect_key` already bachaata hai (`D-25`). Aaj ka nuksaan doosri jagah
hai aur tumhe usko naam dena hai: **A ka mark B ke live claim pe kya likh deta hai**, aur **B ka apna mark
phir kya karta hai.** Ye `P-25` ka doosra roop hai — *"ek guard jo stale transition reject karta hai wo uss
transition ki policy bhi phenk deta hai"* — aur uska carrier `next_attempt_at` / `attempts` hai.

### Launch order — ye load-bearing hai, warna galat worker claim kar lega

Dono worker poll karte hain. A ko pehle claim karna **hai**, warna experiment ulta ho jaayega. Isliye teen
terminal pehle se taiyaar rakho aur ye order follow karo:

| # | Terminal | Kab |
|---|---|---|
| 1 | **reaper** | sabse pehle. Khaali queue pe ye sirf `candidates=0 reclaimed=0` print karta hai, kuch todta nahi |
| 2 | **worker A** | reaper ke baad |
| 3 | **API** (uvicorn) + enqueue | A ke `Starting worker process` ke baad |
| 4 | **worker B** | **A ka `[EFFECT HANDLER] Blocking event loop (45.0s)...` line dikhne ke baad** — aur T=30 se pehle, matlab tumhare paas ~25 s hai. Command pehle se type karke rakho, sirf Enter dabana hai |

```powershell
# terminal 1 — reaper
.\.venv\Scripts\python.exe -u -m src.reaper *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d1_step1_reaper.log

# terminal 2 — worker A
.\.venv\Scripts\python.exe -u -m src.worker *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d1_step1_worker_a.log

# terminal 3 — API (no --reload)
.\.venv\Scripts\python.exe -u -m uvicorn src.main:app --host 127.0.0.1 --port 8000

# terminal 4 — worker B (Enter sirf A ke "Blocking event loop" ke baad)
.\.venv\Scripts\python.exe -u -m src.worker *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d1_step1_worker_b.log
```

Enqueue (terminal 5, ya API terminal ke saath ek aur):

```powershell
$body = @{ type='effect'; payload=@{ seconds=45; block=$true }
           idempotency_key = "w4d1-step1-$([guid]::NewGuid().ToString('N'))" } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/jobs' -Method Post -ContentType 'application/json' -Body $body
$step1Job = [int]$r.job_id
"STEP1_JOB=$step1Job"
```

`$step1Job` ko **isi terminal me** rakho — C1 usko use karta hai. Alag terminal me kaam kar rahe ho to number
haath se likh lo.

### Pehle likho, chalane se pehle (Q1 iska formal roop hai)

Kaunsi do rows ka pair — `(status, attempts, next_attempt_at)` — galat hoga, aur **kis worker ka intent** uss
row me jeeta hoga. Ye Part B Q1 hai aur Step 0 me already frozen hona chahiye.

**Executable end:** teen timestamped log files disk pe; `$step1Job` ka final row snapshot; C1 pass; teeno
process `Ctrl+C` se band (worker B `45 s` block me hai — `Ctrl+C` `time.sleep` ko todta hai ya nahi, ye
**measure karna hai, predict nahi**; jo hua wo log me likho).

**KEY:** C1 ka output aur apni explanation likhne ke baad → **"Open after Step 1 / C1 — Q1"**.

---

## Step 2 — 25 min: `claim_generation` ka design — teen faisle, teenon ki cost likhi hui

Aaj koi code nahi. Ek file: `docs\daily\week_04\DIN_01_DESIGN.md`. Teen H2 headings, aur har ek me exactly
teen labelled lines: `Chosen:`, `Rejected:`, `Cost:`. C2 ise mechanically padhta hai.

**Terms used in this step**
- **Fencing token:** ek value jo resource ke saath rakhi jaati hai; writer ko apni copy dikhani padti hai; resource purani copy reject karta hai. Kleppmann ka *"How to do distributed locking"* — sirf fencing wala hissa aur wo diagram jahan client 1 GC pause ke baad likhta hai.
- **Monotonic:** per row kabhi ghatta nahi. `status` cycle karta hai (`running → pending → running`); monotonic value nahi karti.
- **Epoch / generation:** ek ownership period ka number. "Ye row ab kis claim ki hai" — "ye row claimed hai kya" se alag sawaal.
- **`RETURNING`:** `UPDATE … RETURNING col` — badla hua row usi statement se wapas aata hai.
- **Effect identity:** wo naam jisse bahar ki duniya ek logical effect ko ek maanti hai (`side_effects.effect_key`).
- **Claim identity:** wo naam jisse hum ek dispatch ko doosre dispatch se alag karte hain.

### Faisla 1 — kaun badhata hai

Claim CAS badhata hai, ye clear hai. Sawaal: **reaper ka reclaim bhi badhata hai ya nahi?**

| Option | Kya milta hai | Kya cost |
|---|---|---|
| Sirf claim badhaye | Ek writer, ek jagah, samajhna aasan | Stale worker reclaim ke baad bhi fenced nahi hota jab tak koi doosra worker claim na kare. Khaali queue pe wo window khuli rehti hai |
| Reclaim bhi badhaye | Fence reclaim ke **instant** lag jaata hai | Generation do jagah badhta hai; `reaper.py` ab lifecycle writer ban gaya aur usko apna `rowcount = 0` case handle karna padega |

Ye faisla Part B **Q5** se seedha juda hai. Q5 Step 0 me frozen hai; ab faisla likho.

### Faisla 2 — generation ka type aur origin

Teen candidates. **Teesra jaan-boojh ke likhna hai aur maarna hai** (AGENTS rule 28):

- `bigint` counter DB me — `claim_generation + 1`.
- `uuid` per claim — application me generate.
- `claimed_at` ko hi token maan lena — **`claimed_at` heartbeat se badalta hai**, isliye token claim ke poore
  jeevan me constant nahi rehta. `uuid` monotonic nahi hota, to *"kaunsa naya hai"* compare nahi kar sakte.

Likho: aaj ke fence ko equality chahiye ya ordering chahiye — aur agar sirf equality chahiye, to monotonic
hone se **kya extra** milta hai. Ye ek line hai aur `D-26` me jaati hai.

### Faisla 3 — `effect_key` ka generation ke saath rishta

Ye sabse khatarnak faisla hai aur iska poora asar **Din 3** pe dikhta hai. Aaj `effect_key = f"job:{job_id}"`
hai. Doosra option `f"job:{job_id}:gen{g}"` hai. **Ek option Week 3 ka poora kaam undo kar deta hai — kaunsa,
ye tumhara derive karna hai, aur ye Part B ka Q4 hai.**

C-block me iska measured discriminator hai: Step 4 ke job pe `select count(*) from side_effects where
job_id = <id>`. Faisla galat hoga to wo number `1` nahi aayega.

**Executable end:** `DIN_01_DESIGN.md` disk pe, teen headings, har heading me `Chosen:` / `Rejected:` /
`Cost:` teeno non-empty; C2 pass.

**KEY:** C2 pass hone ke baad → **"Open after Step 2 / C2 — Q4 and Q5, aur teeno faislon ka mechanism"**.

---

## Step 3 — 40 min: migration + gated writes + ek chhota smoke run

**Terms used in this step**
- **Fast default:** PostgreSQL 11+ me `ADD COLUMN … NOT NULL DEFAULT <constant>` table rewrite nahi karta; value catalog me rakhi jaati hai aur read pe materialise hoti hai.
- **`NULL` = "value historically exist nahi karta"** — `0` = "value exist karta hai aur wo zero hai". Ye do alag statements hain aur aaj ka poora `job_executions` faisla isi farq pe hai.
- **Disposable DB:** ek throwaway database jo sirf migration ka `downgrade`/`upgrade` lifecycle prove karne ke liye banti hai aur usi step me drop hoti hai. Evidence DB pe downgrade **nahi** hota.
- **`P-28`:** `alembic.ini` line 89 pe `sqlalchemy.url = postgresql+psycopg://…/relay` hardcoded hai, aur `alembic/env.py` line 41 `config.get_main_option("sqlalchemy.url")` padhta hai — matlab **`$env:DATABASE_URL` Alembic ke liye exist hi nahi karta** (`[MEASURED-R 2026-09-05]`). Disposable DB ko target karne ka ek hi safe raasta hai: ini ki ek copy, uski `sqlalchemy.url` badli hui, aur `alembic -c <copy>`.

### 3A — migration

Ek revision, `down_revision = 'w3d4_enqueue_idempotency'`. Repo me custom slug ka precedent hai, to:

```powershell
.\.venv\Scripts\python.exe -m alembic revision -m "add claim generation" --rev-id w4d1_claim_generation
```

Do columns:

| Column | Shape | Kyu |
|---|---|---|
| `jobs.claim_generation` | `bigint NOT NULL DEFAULT 0` | `119` existing rows ko backfill statement nahi chahiye. `D-04` asymmetric reversibility: column add karna backward-compatible hai |
| `job_executions.claim_generation` | `bigint NULL` | Purani rows ka generation **historically exist hi nahi karta**. `0` likhna log ko jhootha banata hai. `P-11` ka slipped debt yahan close hota hai — honestly |

`downgrade()` **likha jaata hai** aur disposable DB pe chalaya jaata hai (`upgrade head` → `downgrade -1` →
`upgrade head`). Reason: Din 4 aur Din 5 ki disposable DB har baar `upgrade head` se banegi, aur ek toota
downgrade uss din pakda jaayega jis din time nahi hoga.

**Order load-bearing hai:** pehle disposable lifecycle, phir evidence DB ka upgrade. Isse `P-28` ka
discriminator kaam karta hai — disposable ke baad `relay` ka `version_num` abhi bhi `w3d4_enqueue_idempotency`
hona chahiye. Ulta order me ye check kuch prove nahi karta. C3 isi order me likha hua hai.

### 3B — code, teen jagah

**Ready-made code iss BRIEF me nahi hai. SQL ki shape hai; Python tumhari.**

1. **Claim CAS** — ek hi statement, `RETURNING`:

```sql
UPDATE jobs
   SET status           = 'running',
       claimed_at       = now(),
       attempts         = attempts + 1,
       claim_generation = claim_generation + 1
 WHERE id = :id AND status = 'pending'
RETURNING claim_generation;
```

Worker iss `g` ko poore dispatch ke liye rakhta hai. **Alag `SELECT claim_generation` mat karo** — Part B Q2
usi window ke baare me hai, aur wo Step 0 me frozen hai.

2. **Heartbeat** — gate add karo:

```sql
UPDATE jobs SET claimed_at = now()
 WHERE id = :id AND status = 'running' AND claim_generation = :g;
```

`rowcount = 0` → ye worker fenced hai. Aur ek sawaal jo aaj lena hai: **fenced worker apna handler rok deta
hai ya chalne deta hai?** Iska honest jawab yahi hai ki handler already chal raha hai — DB ka `rowcount` usko
rok nahi sakta. Isliye fencing **DB writes** ko fence karti hai, **kaam** ko nahi. Ye line `D-26` me jaati hai.

3. **Mark** (`succeeded` / `failed` / `dead_letter`) — gate add karo, `status = 'running'` **hataana nahi**:

```sql
UPDATE jobs SET status = :new_status, next_attempt_at = :next_attempt_at
 WHERE id = :id AND status = 'running' AND claim_generation = :g;
```

`rowcount = 0` pe ek **naam wali** line chahiye jo `Conflict on mark` se alag ho — wo line Week 2 se exist
karti hai aur uska matlab kuch aur hai. Do lines chahiye, aur unhe alag karne ke liye rowcount `0` ke baad
`(status, claim_generation)` ka ek follow-up read karo:

- `claim_generation <> :g` → `Mark fenced: job_id=<id> held_generation=<g> rowcount=0`
- warna → purani `Conflict on mark: …` line jaisi hai waisi rahegi

Ye follow-up read **ek alag statement** hai, matlab wo *label* best-effort hai; *decision* pehle hi `UPDATE`
le chuka hai. Log me isko aise hi likho.

4. **`job_executions` insert** — `claim_generation = g` stamp karo. Yahan dispatch identity ka ghar hai.

**Lease `30 s`, heartbeat `10 s`, poll `2.0 s`, backoff, `MAX_ATTEMPTS = 3` — aaj kuch nahi badalta.**

### 3C — smoke run, aur ye Step 4 ka **negative control** hai

Ek chhoti job: `type = sleep`, `payload = {"seconds": 2}`. Ek worker, reaper band.

```powershell
$body = @{ type='sleep'; payload=@{ seconds=2 }
           idempotency_key = "w4d1-step3-$([guid]::NewGuid().ToString('N'))" } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/jobs' -Method Post -ContentType 'application/json' -Body $body
$step3Job = [int]$r.job_id
"STEP3_JOB=$step3Job"
```

```powershell
.\.venv\Scripts\python.exe -u -m src.worker *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d1_step3_smoke.log
```

Stdout me `generation` `1` dikhna chahiye aur mark `rowcount=1` hona chahiye. **Ye row Step 4 ke liye zaroori
hai:** agar gate hamesha `0` return karta, to ye job kabhi terminal nahi hoti. Matlab "gate sabko reject nahi
karta" ka saboot yahan banta hai, Step 4 me nahi.

**Executable end:** `alembic heads` ek line; disposable lifecycle pass; evidence DB upgraded; `pytest tests -q`
chala; smoke job terminal with `generation = 1` stdout me aur `job_executions.claim_generation = 1` DB me;
C3 pass.

**KEY:** C3 pass hone ke baad → **"Open after Step 3 / C3 — Q2 and Q3, migration traps"**.

---

## Step 4 — 25 min: wahi run dobara, **ek** variable badla hua

Step 1 ka **exactly wahi** setup — wahi payload `{"seconds": 45, "block": true}`, wahi launch order, wahi
reaper, wahi do worker. Ek variable badla: generation gate. Setup me kuch aur bhi badla to conclusion
`not isolated` mark hota hai (AGENTS rule 7).

**Terms used in this step**
- **Fence fired:** stale writer ne khud `rowcount = 0` report kiya. Ek `0` jo kisi ne report nahi kiya, wo evidence nahi hai.
- **Negative control:** Step 3 ka smoke job — sahi owner ka mark `rowcount = 1` deta hai. Iske bina "sab reject ho raha hai" aur "stale reject ho raha hai" ek jaise dikhte hain (`P-18`).
- **Liveness:** kaam aage badh raha hai ya nahi. Safety se alag axis: ek row jispe kuch galat nahi likha, par jo kabhi terminal bhi nahi hoti, safe hai aur live nahi.

### Stop rule — isko padhe bina Step 4 shuru mat karo

Handler `45 s` ka hai aur lease `30 s` ki hai. Matlab **koi bhi** dispatch apne lease ko outlive karta hai.
Jaise hi A ka mark fenced hota hai, row terminal nahi hoti — aur reaper usko dobara reclaim karne ke liye
azad hai. **Ye loop apne aap nahi rukta.**

Isliye: **A ki `Mark fenced` line dikhte hi — usi minute — C4 chalao, phir teeno process band karo.** Wall
clock note karo. `attempts` ka exact number iss baat pe depend karta hai ki tumne kitni der chhoda; isliye
`attempts` ke saath **snapshot ka time** likhna zaroori hai, warna number compare karne layak nahi.

Aur ye khud ek finding hai, irritation nahi: likh ke rakho ki fencing ne kya **badla** aur kya **naya bana
diya**.

### Enqueue aur logs — sirf naam badle hain

```powershell
$body = @{ type='effect'; payload=@{ seconds=45; block=$true }
           idempotency_key = "w4d1-step4-$([guid]::NewGuid().ToString('N'))" } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/jobs' -Method Post -ContentType 'application/json' -Body $body
$step4Job = [int]$r.job_id
"STEP4_JOB=$step4Job"
```

Log files: `.\logs\w4d1_step4_reaper.log`, `.\logs\w4d1_step4_worker_a.log`, `.\logs\w4d1_step4_worker_b.log`.
Launch order Step 1 se copy hota hai, dobara invent nahi hota: reaper → A → enqueue → (A ka
`Blocking event loop` line) → B.

### Do run side by side, ek table me

| | Step 1 (gate ke bina) | Step 4 (gate ke saath) |
|---|---|---|
| A ka claim | `attempts`, generation | |
| Reaper reclaim | timestamp, `matched` | |
| B ka claim | `attempts`, generation | |
| A ka mark | `rowcount`, kaunsi line | |
| B ka mark | `rowcount`, kaunsi line | |
| Final `(status, attempts, next_attempt_at)` | | |
| `job_executions` rows / distinct workers | | |
| `side_effects` rows | | |

**Executable end:** Step 4 ke teen timestamped logs; A ke stdout me `Mark fenced … rowcount=0`; C4 pass;
do-run comparison table log me bhari hui; C5 (closing bench + cleanup) pass.

**KEY:** C4 ke baad → **"Open after Step 4 / C4 — fence ka measured shape aur uski nayi cost"**. Uske baad
**"Final scoring rubric"** kholo aur frozen text ko `/5` pe grade karo. Post-run prose ko credit nahi milta.

---

## Din close pe reviewer ko kya dena hai

Plan ka DOC-SYNC Din 1 ke liye: `logs/WEEK_04.md` (nayi) · `roadmap/CURRENT_WEEK.md` (Week 4 pe repoint) ·
`PROBLEMS.md`. **`DECISIONS.md` me aaj kuch nahi** — `D-26` ka `Cost` Din 4 ke real-process witness ke bina
likha hi nahi ja sakta, isliye aaj sirf `Problem` + `Options` ka draft.

Reviewer ko chaar cheezein chahiye: `DIN_01_PREDICTIONS_FROZEN.md` + printed hash, `DIN_01_DESIGN.md`, saaton
log files, aur C0–C5 ka raw output. `P-` number chahiye to **uss din grep karo** (`E6`) — aaj ka expected
next-free `P-30` hai, par register hi sach hai.

---

# Part B — Prediction questions — **Gemini ko paste mat karna**

> Step 0 me **paanchon** answer aur freeze karo, Step 1 shuru hone se pehle. `idk` valid hai aur `0` score
> karta hai. `idk — <sahi jawab>` bhi `0` hai. Inke jawab iss block me nahi hain, aur BRIEF me kahin nahi hain.

```text
Q1. Step 1 (fencing se pehle) me worker A 45 s blocking handler pe hai, reaper ne 30 s pe reclaim kiya,
    B ne claim kiya. A wapas aakar WHERE status = 'running' se succeeded mark karta hai. Uss instant ke
    baad row ka (status, attempts, next_attempt_at) kya hoga, aur B ka handler jab khatam hoga to uska
    mark kya karega?

Q2. Claim CAS me RETURNING claim_generation vs claim ke baad ek alag SELECT claim_generation — in dono ke
    beech ek window hai. Wo window kis cheez ko allow karti hai?

Q3. job_executions.claim_generation ko NOT NULL DEFAULT 0 banaya jaaye to purani rows me kya likha
    jaayega, aur kaunsi future query uss value se galat jawab degi?

Q4. Agar effect_key ke andar claim_generation chala jaaye, to Din 1 Step 4 ke run me
    select count(*) from side_effects where job_id = <id> kya dega? Aur kyu?

Q5. Reaper ke reclaim UPDATE me generation nahi badhaya, aur queue khaali hai (koi doosra worker claim
    nahi karta). Stale worker A wapas aata hai. Uska mark accept hoga ya fenced?
```

---

# Part C — Verification

Sab PowerShell 7 syntax hai aur repo root `d:\PROJECTS\relay` se chalta hai. `docker compose` service ka naam
`db` hai; container name use nahi hota. Jahan `throw` hai wahan step **rukta** hai — stray worker chala ke
state "repair" mat karna.

**Har check ke saath do column hain: mechanism maujood, aur mechanism ghayab. Jis check ka dono column same
output deta hai, wo check decorative hai (`P-18`).**

## C0 — opening bench + seal + single Alembic head

Seal command ke **usi terminal** me:

```powershell
if (-not $d1FrozenHash) { throw 'Step 0B hash variable missing; C0 must run in the same PowerShell terminal' }
$frozen = 'docs\daily\week_04\DIN_01_PREDICTIONS_FROZEN.md'
if ((Get-FileHash $frozen -Algorithm SHA256).Hash -ne $d1FrozenHash) { throw 'Frozen predictions changed after Step 0B' }
"D1_FROZEN_SHA256_UNCHANGED=$d1FrozenHash"

$head = (git rev-parse --short HEAD).Trim()
"HEAD=$head   (Week 3 close-content commit was 87f2253; agar alag hai to beech ka commit naam se log me likho)"

$env:DATABASE_URL = 'postgresql+asyncpg://postgres:relay@localhost:5433/relay'
$runtimeDb = (& .\.venv\Scripts\python.exe -c "from src.database import engine; print(engine.url.database)") -join ''
if ($runtimeDb.Trim() -ne 'relay') { throw "Runtime DB mismatch: $runtimeDb" }
"python_runtime_database=relay"

$relayProcs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper|dispatcher)' })
$relayProcs | Select-Object ProcessId, ParentProcessId, CommandLine
if ($relayProcs.Count -ne 0) { throw "Relay process count is $($relayProcs.Count), expected 0" }
"relay_processes=0"

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
select string_agg(id::text||':'||type||':'||attempts::text, ',' order by id) || '|' || count(*)::text
  from jobs where status='pending';
select count(*) from pg_stat_activity
  where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select count(*) from pg_database where datname like 'relay_w4%';
select count(*) from information_schema.columns where column_name='claim_generation';
'@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'C0 SQL failed' }
$actual = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$actual
$expected = @(
  'relay|119|125|125|107|9|12|w3d4_enqueue_idempotency',
  '97|15|4|3|0|119',
  '116:sleep:0,121:sleep:0,123:sleep:0,124:sleep:0|4',
  '0',
  '0',
  '0'
)
if (($actual -join "`n") -ne ($expected -join "`n")) {
  throw "C0 fingerprint mismatch.`nACTUAL:`n$($actual -join "`n")`nEXPECTED:`n$($expected -join "`n")"
}
'C0=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Bench Week 3 close se match | Wahi `119/125/125/107/9/12` tuple, `w3d4_enqueue_idempotency` | Koi bhi farq → **divergence**, Din 1 rukta hai jab tak cause naam se na mile (`E2`) |
| Chaar pending rows ka type bhi assert hua | `116:sleep:0,…` — chaaron `sleep`, `attempts=0` | Sirf id list match karti par type na hoti → drain ka expected `side_effects` delta guess ban jaata |
| `claim_generation` **exist nahi karta** | `information_schema.columns` count `0` | Non-zero → migration pehle se chal chuki hai, aur Step 3 ka before/after compare khatam |
| Single head | ek `(head)` line | Do heads → branch ban gayi, aur repo me `75a845575d2e`/`79cb2ee38481` ka confusion dobara |
| Koi Relay process zinda nahi | `relay_processes=0` | Ek purana worker → wo Din 1 ki job claim kar lega aur attribution khatam (`P-13`) |
| Frozen predictions immutable | hash unchanged | Hash badla → uss sawaal ka score `seal broken` |

## C0D — drain run ka delta, alag line me

```powershell
$sql = @'
select concat_ws('|','drain', count(*), (select count(*) from job_executions),
  (select count(*) from side_effects), (select last_value from jobs_id_seq),
  (select count(*) from jobs where status='pending')) from jobs;
select concat_ws('|','row', id, status, attempts,
  coalesce(next_attempt_at::text,'NULL'), coalesce(claimed_at::text,'NULL'))
  from jobs where id in (116,121,123,124) order by id;
select concat_ws('|','exec', job_id, count(*), count(distinct worker_id))
  from job_executions where job_id in (116,121,123,124) group by job_id order by job_id;
'@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
$raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
```

Expected shape:

```text
drain|119|111|9|125|0
row|116|succeeded|1|NULL|<ts>
row|121|succeeded|1|NULL|<ts>
row|123|succeeded|1|NULL|<ts>
row|124|succeeded|1|NULL|<ts>
exec|116|1|1
exec|121|1|1
exec|123|1|1
exec|124|1|1
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Chaaron drain hui, ek-ek dispatch me | `attempts = 1`, `exec … 1|1` chaaron pe | `attempts = 2` ya `exec 2` → reaper chal raha tha, ya doosra worker zinda tha. Drain contaminated |
| `side_effects` **hila nahi** | `9` | `10+` → in chaar me se koi `effect` handler pe gayi, ya koi aur writer zinda hai. Chaaron `sleep` hain (C0 ne type assert kiya), to +0 hi ek honest number hai |
| `jobs` count / seq nahi badle | `119` aur `125` | Badle → drain ke dauran koi enqueue hua, aur Din 1 ka baseline shift ho gaya |
| `pending = 0` | `0` | Non-zero → Step 1 ka worker Din 1 ki job ke saath ek purani job bhi utha lega |

## C1 — Step 1 ka harm, aur uska overlap proof

`$step1Job` usi terminal me hona chahiye jahan enqueue kiya tha. **`claim_generation` abhi exist nahi karta** —
Step 1 ke SQL me use select karne ki koshish mat karo, error aayega.

```powershell
if (-not $step1Job) { throw 'STEP1_JOB missing; enqueue wale terminal se hi C1 chalao' }
$sql = @"
select concat_ws('|','job', id, status, attempts,
  coalesce(next_attempt_at::text,'NULL'), coalesce(claimed_at::text,'NULL')) from jobs where id = $step1Job;
select concat_ws('|','exec', count(*), count(distinct worker_id), string_agg(worker_id, ',' order by id))
  from job_executions where job_id = $step1Job;
select concat_ws('|','effect', count(*), coalesce(string_agg(worker_id, ','),''))
  from side_effects where job_id = $step1Job;
select concat_ws('|','effect_seq', (select last_value from side_effects_id_seq), (select count(*) from side_effects));
select concat_ws('|','totals', (select count(*) from jobs), (select count(*) from job_executions),
  (select count(*) from side_effects));
"@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'C1 SQL failed' }
$raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }

$execRow = $raw | Where-Object { $_ -match '^exec\|' }
$execParts = $execRow.Trim().Split('|')
if ([int]$execParts[1] -ne 2) { throw "Expected 2 dispatches for job $step1Job, got $($execParts[1]) — do dispatch hue hi nahi, Step 1 void" }
if ([int]$execParts[2] -ne 2) { throw "Expected 2 distinct worker_ids, got $($execParts[2]) — dono dispatch ek hi worker ke, Step 1 void" }
'C1_dispatch_shape=ok'

# Pre-migration execution count — C3 isko use karega, hardcoded 107 ko nahi
$preMigrationExecutions = [int](($raw | Where-Object { $_ -match '^totals\|' }).Trim().Split('|')[2])
"PRE_MIGRATION_EXECUTIONS=$preMigrationExecutions"
```

Ab **overlap proof** — dono timestamped logs se. Ye wo check hai jo "A ne B ke **live** claim pe likha" ko
"A ne B ke khatam hone ke **baad** likha" se alag karta hai:

```powershell
function Get-LogEvent {
  param([string]$Path,[string]$Pattern)
  $hit = @(Get-Content $Path | Where-Object { ($_ -split '\|',2)[1] -match $Pattern })
  if ($hit.Count -eq 0) { return $null }
  [datetime]::ParseExact(($hit[0] -split '\|',2)[0],'yyyy-MM-dd HH:mm:ss.fff',[cultureinfo]::InvariantCulture)
}

$a = '.\logs\w4d1_step1_worker_a.log'
$b = '.\logs\w4d1_step1_worker_b.log'
$r = '.\logs\w4d1_step1_reaper.log'

$aClaim  = Get-LogEvent $a "Claimed job $step1Job\b"
$aBlock  = Get-LogEvent $a 'Blocking event loop'
$reclaim = Get-LogEvent $r "id=$step1Job pre_status=running matched=1 post_status=pending"
$bClaim  = Get-LogEvent $b "Claimed job $step1Job\b"
$aMark   = Get-LogEvent $a "Marked job $step1Job as"
$bDone   = Get-LogEvent $b "Work completed for job $step1Job"
$bMark   = Get-LogEvent $b "job $step1Job"

foreach ($n in 'aClaim','aBlock','reclaim','bClaim','aMark') {
  if (-not (Get-Variable $n -ValueOnly)) { throw "Missing log event: $n — iske bina Step 1 ka conclusion nahi likha ja sakta" }
}
'{0,-10} {1:HH:mm:ss.fff}' -f 'A_claim',  $aClaim
'{0,-10} {1:HH:mm:ss.fff}' -f 'A_block',  $aBlock
'{0,-10} {1:HH:mm:ss.fff}' -f 'reclaim',  $reclaim
'{0,-10} {1:HH:mm:ss.fff}' -f 'B_claim',  $bClaim
'{0,-10} {1:HH:mm:ss.fff}' -f 'A_mark',   $aMark
if ($bDone) { '{0,-10} {1:HH:mm:ss.fff}' -f 'B_done', $bDone } else { 'B_done     not recorded' }

if ($aClaim -ge $reclaim) { throw 'Reclaim A ke claim se pehle? ordering galat, run void' }
if ($reclaim -ge $bClaim) { throw 'B ne reclaim se pehle claim kiya? ordering galat, run void' }
if ($bClaim -ge $aMark)   { throw 'A ka mark B ke claim se PEHLE hua — stale-write overlap reproduce nahi hua' }
"lease_gap_seconds=$([math]::Round(($reclaim - $aClaim).TotalSeconds,3))"
if ($bDone) {
  if ($aMark -ge $bDone) { throw 'A ka mark B ke kaam khatam hone ke BAAD hua — ye stale write nahi, ye sequential run hai' }
  "A_mark_before_B_finished=True  (overlap = $([math]::Round(($bDone - $aMark).TotalSeconds,3)) s)"
} else {
  'B_done=not recorded — overlap proof adhoora, aur ye log me waise hi likho'
}
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **A ka mark B ke live claim pe gira** | `B_claim < A_mark < B_done`, aur A ka `Marked … rowcount=1` | `A_mark > B_done` → ye ek sequential run hai, harm reproduce nahi hua. Sirf final row dekhne se ye dono ek jaise dikhte hain (`P-29`) |
| Do asli dispatch hue | `exec` → `2|2`, do alag `worker_id` | `2|1` → ek hi worker ne do baar claim kiya (reaper + wahi worker), aur "stale writer vs fresh owner" ka frame galat |
| Effect dedup ne apna kaam kiya | `effect` → `1`, aur uska `worker_id` = A | `2` → `uq_side_effects_effect_key` ya `ON CONFLICT` toota hai, aur ye Din 1 ka nahi, `D-25` ka bug hai |
| **Doosre dispatch ne insert try kiya tha** | `side_effects_id_seq` ka delta rows ke delta se **bada** | Dono delta barabar → B ka handler `INSERT` tak pehancha hi nahi, matlab `1` ka matlab *"dedup ne kaam kiya"* nahi, *"test nahi hua"* hai |
| Lease arithmetic sane | `lease_gap_seconds` ~`30`–`32` | `< 30` → reaper ka predicate/lease galat padha; `>> 32` → reaper poll miss kar raha tha |
| B ka mark reject hua | B ke log me uss job pe `rowcount=0` wali line | B ka mark `rowcount=1` → B ne A ke likhe `succeeded` ko overwrite kiya, aur harm ka shape kuch aur hai — usko naam do |

## C2 — Step 2 ka design file, structural gate

```powershell
$design = 'docs\daily\week_04\DIN_01_DESIGN.md'
if (-not (Test-Path $design)) { throw "Missing $design" }
$text = (Get-Content $design -Raw) -replace "`r`n","`n"
$sections = [regex]::Matches($text,'(?ms)^## (?<title>[^\n]+)\n(?<body>.*?)(?=^## |\z)')
if ($sections.Count -ne 3) { throw "Expected exactly 3 '## ' decision sections, got $($sections.Count)" }
foreach ($s in $sections) {
  $title = $s.Groups['title'].Value.Trim()
  $body  = $s.Groups['body'].Value
  foreach ($label in 'Chosen','Rejected','Cost') {
    $m = [regex]::Match($body,"(?m)^\s*(?:[-*]\s*)?(?:\*\*)?$label(?:\*\*)?\s*:\s*(?<v>.+)$")
    if (-not $m.Success)            { throw "[$title] missing '${label}:' line" }
    if ($m.Groups['v'].Value.Trim().Length -lt 20) { throw "[$title] '${label}:' too short to be a reason" }
  }
  "OK: $title"
}
if ($text -notmatch '(?i)effect_key')       { throw 'Faisla 3 ka naam (effect_key) file me nahi hai' }
if ($text -notmatch '(?i)claimed_at')       { throw 'Faisla 2 ka maara hua option (claimed_at as token) file me nahi hai' }
if ($text -notmatch '(?i)reclaim|reaper')   { throw 'Faisla 1 (reclaim badhaye ya nahi) file me nahi hai' }
'C2=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Teen faisle, teenon ka rejected option likha hua | 3 sections × (`Chosen`/`Rejected`/`Cost`) | Sirf `Chosen` → wo faisla nahi, wo preference hai. `D-26` ka `Rejected` field khaali reh jaayega |
| Maara hua option naam se maujood | `claimed_at` mention | Missing → AGENTS rule 28 (jo option maara, wo likha jaana chahiye) toota |
| `effect_key` ka faisla likha hua | `effect_key` mention | Missing → Din 3 pe ye faisla implicitly ho jaayega, aur tab uska ulta side dikhega |

**Note:** ye gate structure check karta hai, reasoning ki quality nahi. Ek khaali-dimaag se bhari hui file bhi
pass karegi — reasoning reviewer padhega. Isko fully-automated proof mat samajho.

## C3 — migration: disposable lifecycle pehle, phir evidence DB

**Order badla to `P-28` ka discriminator kaam nahi karega.**

```powershell
$disposable = "relay_w4d1_life_$PID"
$iniCopy    = ".\_w4d1_$PID.ini"
try {
  docker compose exec -T db psql -X -Atq -U postgres -d postgres -c "create database $disposable" 2>&1
  ((Get-Content .\alembic.ini -Raw) -replace 'sqlalchemy\.url = .*', "sqlalchemy.url = postgresql+psycopg://postgres:relay@localhost:5433/$disposable") |
    Set-Content -Path $iniCopy -Encoding utf8
  (Select-String -Path $iniCopy -Pattern '^sqlalchemy\.url').Line   # target on screen, before any DDL

  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy upgrade head
  if ($LASTEXITCODE -ne 0) { throw 'disposable upgrade head failed' }
  $q = "select 'head|'||(select version_num from alembic_version)||'|'||(select count(*) from information_schema.columns where column_name='claim_generation');"
  $q | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $disposable

  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy downgrade -1
  if ($LASTEXITCODE -ne 0) { throw 'downgrade -1 failed — ye aaj pakda gaya, Din 4/5 pe nahi' }
  ($q -replace '^select ''head','select ''down') | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $disposable

  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy upgrade head
  if ($LASTEXITCODE -ne 0) { throw 're-upgrade head failed' }
  ($q -replace '^select ''head','select ''reup') | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $disposable

  # P-28 discriminator: evidence DB ko chhua bhi nahi gaya
  $g = "select 'evidence_untouched|'||(select version_num from alembic_version)||'|'||(select count(*) from information_schema.columns where column_name='claim_generation');"
  $ev = @($g | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
        ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
  $ev
  if ($ev[0] -ne 'evidence_untouched|w3d4_enqueue_idempotency|0') {
    throw "P-28 fired: disposable ka Alembic evidence DB pe chala. ACTUAL: $($ev[0])"
  }
} finally {
  docker compose exec -T db psql -X -Atq -U postgres -d postgres -c "drop database if exists $disposable" 2>&1 | Out-Null
  Remove-Item $iniCopy -Force -ErrorAction SilentlyContinue
  $c = "select 'cleanup|'||(select count(*) from pg_database where datname like 'relay_w4d1%');"
  $c | docker compose exec -T db psql -X -Atq -U postgres -d postgres
}
```

Expected teen lines: `head|w4d1_claim_generation|2` → `down|w3d4_enqueue_idempotency|0` →
`reup|w4d1_claim_generation|2`, phir `evidence_untouched|w3d4_enqueue_idempotency|0`, phir `cleanup|0`.

Ab evidence DB upgrade karo:

```powershell
& .\.venv\Scripts\python.exe -m alembic upgrade head       # alembic.ini already relay pe point karta hai (P-28)
if ($LASTEXITCODE -ne 0) { throw 'evidence upgrade failed' }
$heads = @(& .\.venv\Scripts\python.exe -m alembic heads 2>&1 | Where-Object { $_ -match '\(head\)' })
if ($heads.Count -ne 1) { throw "Expected one head after migration, got $($heads.Count)" }
$heads

if (-not $preMigrationExecutions) { throw 'PRE_MIGRATION_EXECUTIONS missing; C1 se lo, 107 hardcode mat karo' }
$sql = @"
select concat_ws('|','jobs_col', data_type, is_nullable, coalesce(column_default,'NONE'))
  from information_schema.columns where table_name='jobs' and column_name='claim_generation';
select concat_ws('|','exec_col', data_type, is_nullable, coalesce(column_default,'NONE'))
  from information_schema.columns where table_name='job_executions' and column_name='claim_generation';
select concat_ws('|','jobs_null', count(*) filter (where claim_generation is null),
  count(*) filter (where claim_generation = 0), count(*)) from jobs;
select concat_ws('|','exec_null', count(*) filter (where claim_generation is null),
  count(claim_generation), count(*)) from job_executions;
"@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
$out = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
if ($out[0] -ne 'jobs_col|bigint|NO|0')     { throw "jobs.claim_generation shape wrong: $($out[0])" }
if ($out[1] -ne 'exec_col|bigint|YES|NONE') { throw "job_executions.claim_generation shape wrong: $($out[1])" }
if ($out[2] -ne "jobs_null|0|119|119")      { throw "jobs backfill wrong: $($out[2])" }
if ($out[3] -ne "exec_null|$preMigrationExecutions|0|$preMigrationExecutions") {
  throw "job_executions honest-NULL count wrong. Expected $preMigrationExecutions NULLs. ACTUAL: $($out[3])"
}
'C3_catalog=pass'

& .\.venv\Scripts\python.exe -m pytest tests -q
"pytest_exit=$LASTEXITCODE   (Week 3 baseline: 7 passed)"
```

Smoke job ke baad:

```powershell
$sql = @"
select concat_ws('|','smoke', id, status, attempts, claim_generation) from jobs where id = $step3Job;
select concat_ws('|','smoke_exec', count(*), coalesce(min(claim_generation)::text,'NULL'),
  coalesce(max(claim_generation)::text,'NULL')) from job_executions where job_id = $step3Job;
"@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
$out = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
if ($out[0] -ne "smoke|$step3Job|succeeded|1|1") { throw "Smoke job shape wrong: $($out[0]) — gate ne sahi owner ko bhi reject kar diya?" }
if ($out[1] -ne "smoke_exec|1|1|1")              { throw "Smoke execution stamp wrong: $($out[1])" }
@(Get-Content .\logs\w4d1_step3_smoke.log | Where-Object { ($_ -split '\|',2)[1] -match "job $step3Job.*rowcount=1" }) |
  ForEach-Object { "SMOKE: $_" }
'C3_smoke=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| `jobs` ki purani rows toota nahi | `jobs_null|0|119|119` — sab `0`, koi `NULL` nahi | `NULL` mila → `NOT NULL DEFAULT` nahi laga, aur gate `claim_generation = :g` `NULL` ke against hamesha false dega |
| `job_executions` ki history honest hai | `exec_null|113|0|113` — **saari** purani rows `NULL`, `count(col) = 0` | `0`s bhare hue → history me ek generation invent ho gaya, aur "kaunsi execution stale generation ki thi" wali query hamesha *zero staleness* bolegi |
| Migration reversible hai | `head|…|2` → `down|…|0` → `reup|…|2` | `downgrade` fail → Din 4/Din 5 ki disposable DB uss din tootegi jab time nahi hoga |
| Alembic ne **evidence** DB ko nahi chhua | `evidence_untouched|w3d4_enqueue_idempotency|0` | Kuch aur → `P-28` fired: disposable ka command `relay` pe gaya |
| Disposable DB bacha nahi | `cleanup|0` | Non-zero → `pg_database` me kachra, aur Din 4/5 ki naming collide karegi |
| **Sahi owner ka mark accept hota hai** (Step 4 ka negative control) | `smoke|…|succeeded|1|1` | `running`/`pending` reh gayi → gate sabko reject kar raha hai. Iske bina Step 4 ka `rowcount=0` "fence" nahi, "sab toota hua" hai |
| Regression gate chala | `7 passed` | Red → asli finding. **Par green bhi safety ka proof nahi:** `tests/din5/test_model.py` me koi DB import nahi hai (`[MEASURED-R 2026-09-05]`), wo pure in-memory model hai aur migration ko dekh hi nahi sakta |

## C4 — **fence actually fired** — aaj ka sabse important check

Step 4 ke `Mark fenced` line ke turant baad chalao, phir process band karo.

```powershell
if (-not $step4Job) { throw 'STEP4_JOB missing' }
"SNAPSHOT_AT_UTC=$((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss.fff'))"

$a4 = '.\logs\w4d1_step4_worker_a.log'
$b4 = '.\logs\w4d1_step4_worker_b.log'
$r4 = '.\logs\w4d1_step4_reaper.log'

$fenced = @(Get-Content $a4 | Where-Object { ($_ -split '\|',2)[1] -match "fenced.*job_id=$step4Job\b.*rowcount=0" })
$fenced | ForEach-Object { "FENCE: $_" }
if ($fenced.Count -lt 1) {
  throw "Zero fenced lines in worker A's log. Ye PASS nahi hai — ye 'test nahi hua' hai (P-12). Fence ko stale writer mila hi nahi."
}
"fence_lines_in_A=$($fenced.Count)"

# stale worker ne jo generation hold ki thi
$held = [int]([regex]::Match(($fenced[0] -split '\|',2)[1],'held_generation=(?<g>\d+)').Groups['g'].Value)
"A_held_generation=$held"

# generation ka observed sequence — kabhi ghatta nahi
$gens = @(Get-Content $a4, $b4 |
  ForEach-Object { [regex]::Match(($_ -split '\|',2)[1], "job $step4Job.*generation=(?<g>\d+)") } |
  Where-Object { $_.Success } | ForEach-Object { [int]$_.Groups['g'].Value })
"observed_generations=$($gens -join ',')"

$sql = @"
select concat_ws('|','job', id, status, attempts, claim_generation,
  coalesce(next_attempt_at::text,'NULL')) from jobs where id = $step4Job;
select concat_ws('|','exec', count(*), count(distinct worker_id),
  string_agg(coalesce(claim_generation::text,'NULL'), ',' order by id)) from job_executions where job_id = $step4Job;
select concat_ws('|','effect', count(*)) from side_effects where job_id = $step4Job;
select concat_ws('|','effect_seq', (select last_value from side_effects_id_seq), (select count(*) from side_effects));
"@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
$out = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out

$jobParts = $out[0].Split('|')
$currentGen = [int]$jobParts[4]
if ($currentGen -le $held) { throw "A ki held generation ($held) current ($currentGen) se choti nahi hai — matlab wo stale hi nahi thi, aur fence line ka matlab kuch aur hai" }
"stale_proof: held=$held < current=$currentGen"

$effectCount = [int]($out[2].Split('|')[1])
if ($effectCount -ne 1) { throw "side_effects for job $step4Job = $effectCount, expected 1 — effect_key me generation ghus gaya, D-25 iss migration se toot gaya" }
'C4=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Fence fired** | `≥ 1` `fenced … rowcount=0` line **worker A ke log me** | Zero → fence ko stale writer mila hi nahi. **Ye pass nahi hai, ye "test nahi hua" hai** (`P-12`) |
| Fence ne **stale** writer ko roka | `A_held_generation < jobs.claim_generation` | `held == current` → jise fence kiya wo stale hi nahi thi, aur gate ka `:g` galat pass ho raha hai |
| Generation monotonic hai | `observed_generations` strictly increasing, aur `status` do baar `running` hua par generation do alag values | Value `status` ke saath wapas aa gayi → wo generation nahi, wo `status` ka doosra naam hai |
| Fence ne **sabko** nahi roka | C3 ka smoke job `succeeded` with `rowcount=1` | Wo bhi `rowcount=0` → gate hamesha false hai, aur `rowcount=0` ka koi matlab nahi |
| Effect dedup **abhi bhi** kaam karta hai | `effect|1` | `2` → `effect_key` me generation aa gaya, aur `D-25` iss migration se toot gaya |
| `job_executions` pe generation stamp | `exec|2|2|<g1>,<g2>`, dono non-`NULL`, alag | `NULL` → Step 3 ka stamp code claim path se juda hi nahi |
| Step 1 vs Step 4 isolated | Payload, launch order, reaper, worker count **byte-for-byte** same, sirf gate badla | Kuch aur badla → conclusion `not isolated` (AGENTS rule 7) |

## C5 — closing bench, chain, cleanup

```powershell
$frozen = 'docs\daily\week_04\DIN_01_PREDICTIONS_FROZEN.md'
if ((Get-FileHash $frozen -Algorithm SHA256).Hash -ne $d1FrozenHash) { throw 'Frozen predictions changed during the day' }
'frozen_unchanged=True'

$relayProcs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper|dispatcher)' })
$relayProcs | Select-Object ProcessId, CommandLine
if ($relayProcs.Count -ne 0) { throw "Din 1 ke baad $($relayProcs.Count) Relay process zinda hain (P-13)" }

$sql = @'
set time zone 'UTC';
select concat_ws('|','close', count(*), max(id), (select last_value from jobs_id_seq),
  (select count(*) from job_executions), (select count(*) from side_effects),
  (select last_value from side_effects_id_seq), (select version_num from alembic_version)) from jobs;
select concat_ws('|','status', status, count(*)) from jobs group by status order by status;
select concat_ws('|','jobs_by_day', created_at::date, count(*)) from jobs where id > 125 group by 1 order by 1;
select concat_ws('|','exec_by_day', executed_at::date, count(*)) from job_executions where job_id > 125 group by 1 order by 1;
select concat_ws('|','effect_by_day', created_at::date, count(*)) from side_effects where job_id > 125 group by 1 order by 1;
select concat_ws('|','idle_in_txn', count(*)) from pg_stat_activity
  where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select concat_ws('|','probe_dbs', (select count(*) from pg_database where datname like 'relay_w4%'));
select concat_ws('|','stale_gen_exec', count(*)) from job_executions e join jobs j on j.id = e.job_id
  where e.claim_generation is not null and e.claim_generation <> j.claim_generation;
'@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
$raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }

Get-ChildItem .\logs\w4d1_*.log | Select-Object Name, Length, LastWriteTime
git status --porcelain=v1 -- src alembic
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Chain per-day `group by` se juda, `max(id)` se nahi | Teen `*_by_day` lines, aur unka jod din ki report se match | Sirf total match → do compensating errors chhup sakti hain (Week 2 ka wahi bug) |
| Koi process zinda nahi | `0` | Non-zero → agla din contaminated (`P-13`) |
| Koi disposable DB nahi bachi | `probe_dbs|0` | Non-zero → Din 4/5 collide karega |
| Stale-generation executions ab **visible** hain | `stale_gen_exec` `≥ 1` (Step 4 ka A). Exact number iss baat pe depend karta hai ki loop kitni baar cycle hua — snapshot ke time ke saath likho | `0` → ya stamp nahi hua, ya history current jaisi lag rahi hai. Pehli baar ye query kuch bolti hai; `0` iska matlab result nahi, sawaal hai |
| `logs/` ka evidence disk pe hai | saat `w4d1_*.log` files, non-zero length | Missing → `-u`/wrapper chhoot gaya, aur ordering proof gaya (`P-29`) |
| Sequence reset nahi hua | `jobs_id_seq` ≥ `max(id)`, gaps intact | Reset → `P-05` toota, aur teen hafte ka evidence rewrite ho gaya |

---

# Part D — Scope guard: aaj **nahi**

| Kya | Owner | Aaj karne se kya khota hai |
|---|---|---|
| `completed_at`, `last_error`, structured lifecycle log | **Din 2** | Aaj latency naapne ka koi tareeka nahi hai aur wo theek hai. `completed_at` ko generation gate ke saath **usi din** add karna do variables ek saath hilaana hai |
| `45 s` + `SIGBREAK` at `T = 3 s` shutdown run | **Din 2** | Wo run pehli baar generation ke saath honi chahiye — matlab aaj ka gate uska **precondition** hai, competitor nahi |
| Transactional outbox, dispatcher, receiver | **Din 3** | Aaj `effect_key` ka faisla likha jaata hai; uska ulta side Din 3 pe dikhta hai. Dono ek din me karne se attribution khatam |
| Do asli worker ka witness disposable DB pe | **Din 4** | Wahi din `D-26` ka `Cost` field bharta hai. Aaj `Cost` likhna measurement ke bina likhna hai |
| Pool exhaustion, Locust, `/healthz`, p50/p99 | **Din 5** | `completed_at` ke bina latency exist hi nahi karti |
| `D-26` ka `Cost` / `Rejected` final text | **Din 6** (Din 4 ke evidence ke saath) | Aaj sirf `Problem` + `Options` draft |
| Handler timeout (`asyncio.wait_for`) | **Month 2 ka pehla item** (`P-15`) | Timeout ka pehla sawaal hai *"timed-out handler ka `status` kya hai"* — aur wo `claim_generation` ke saath usi week me badla to attribution khatam. AGENTS rule 7: ek run me ek variable |
| `attempts < :max` claim gate | **Month 2, agar kabhi** | `P-27` ka overdraft `D-23` me **accept** kiya hua hai. Fix karne se Week 3 ka property baseline non-comparable ho jaata hai |
| Lease `30 s`, heartbeat `10 s`, poll `2.0 s`, backoff numbers | **kabhi nahi, iss hafte** | Week 2–3 ke saare measurements inhi numbers pe khade hain |
| `job_executions` pe FK / index / retention | **Month 2** | Load numbers ke bina ye guess hai (`D-21` ki teen branches) |
| `GET /jobs/{id}` me generation ya counts expose karna | **auth ke baad** | `D-03` ka argument: sequential ids + no auth + counts = enumeration surface |
| Rows `116, 121, 123, 124` delete karna | **kabhi nahi** | Step 0 unhe **chalata** hai. `95`, `108`, `110`, `115` ko bhi haath nahi (`P-05`) |
