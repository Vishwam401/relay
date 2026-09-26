# Week 4 Din 4 BRIEF — do asli worker, asli reaper, asli dispatcher: jo claim likha hai wahi chalta hai

**Week 4 · Din 4** · Plan: [`../../planning/WEEK_04.md`](../../planning/WEEK_04.md) ·
Log: [`../../logs/WEEK_04.md`](../../logs/WEEK_04.md) · Sealed: [`DIN_04_KEY.md`](DIN_04_KEY.md) ·
Kal: [`DIN_03_BRIEF.md`](DIN_03_BRIEF.md)

**Goal:** Week 3 Din 5 ka Layer B dobara — par iss baar **test-side SQL nahi**. Do asli
`python -m src.worker` process, asli `src.reaper`, asli `src.dispatcher`, asli commit boundaries, ek
**disposable** DB pe. Interleaving sirf **timing aur payload** se control hoti hai, code se nahi.

**Architectural invariant (aaj ke baad):**
> Jo bhi safety claim iss project me likhi hai, wo **usi code path** ke against measured hai jo production me
> chalta hai — model ke against nahi. Aur wo measurement **evidence DB ko chhue bina** dobara chalayi ja sakti hai.

**Deliverable:** `DIN_04_DESIGN.md` (chaar faisle) · `sink_deliveries` pe ek asli `UNIQUE` + uski migration ·
paanch process ka pre-flight DB assert · chaar interleaving ka `[MEASURED]` table, har ek ke **teen** snapshot
ke saath · project ka **pehla asli `Mark fenced`** · aur evidence DB ka delta **`0`**.

**Budget:** `20 + 20 + 25 + 15 + 35 + 15 = 130 min`. Plan me bhi `130` hai.
**Cut order, agar khinche:** Interleaving **D** kata ja sakta hai (wo Week 1 ka claim dobara hai, sirf
generation ke saath) aur uska owner Din 5 ka load step hai. **A, B, C kabhi nahi kat sakte** — A ke bina fence
production path pe kabhi measure nahi hua, B ke bina `D-25` model-only reh jaata hai, aur C ke bina kal ka
`P-33` khula reh jaata hai. Agar time khatam ho raha hai to **Step 5 kaato mat** — evidence DB ka delta check
aaj ka paanchvaan verification item hai, afterthought nahi.

---

## Rules — ye chaar roz wahi hain

> **Paste rule:** Part A, Part C, Part D Gemini ko ja sakte hain. **Part B kabhi nahi. KEY kabhi nahi.**
>
> **Seal rule:** paanchon answers **Step 0 me** freeze honge, Step 1 shuru hone se pehle. Har KEY section tabhi
> khulta hai jab uss step ka **measurement** ho chuka ho. Output prediction se alag nikla to **pehle apni
> explanation likho**, phir Gemini ke saath uss output pe reason karo, phir KEY.
>
> **Provenance rule:** iss BRIEF ke saare numbers `[MEASURED-R 2026-09-08]` hain — Din 3 ke closeout review me
> actually chalaye gaye, disposable DB `relay_w4d3_audit` pe (drop ho gayi). Jo tum chalao wo `[MEASURED]`.
>
> **Aaj ka apna rule, aur ye naya hai:** aaj ka koi bhi row evidence DB me **nahi** jaata. Ek bhi. Step 5 usko
> naapta hai, aur wo check kal ke `queue|0|1` ki tarah **print** nahi hoga — wo `throw` karega.

### Read order — isko literally follow karo

1. Sirf **Step 0** padho (`0A`–`0D`).
2. Editor outline se seedha **Part B** pe jao. Step 1–5 aur Part C abhi mat kholo.
3. Paanch predictions likho (`idk` valid hai aur `0` score karta hai), phir Step 0 ke seal command pe wapas aao.
4. Frozen hash print hone ke baad **C0** kholo. C0 pass ho tab Step 1 aur baaki Part A/Part C khulte hain.

### Kal jo sach nikla — chaar cheezein aaj ka kaam badalti hain

`[MEASURED-R 2026-09-08, Din 3 closeout review]`. Ye chaaron **prediction ke jawab nahi** hain; ye aaj ke
maidan ki shape hain, aur inhe na jaanne se aaj ka din galat measure hoga.

| Kya | Actual | Aaj ka asar |
|---|---|---|
| **Job `136` ek poison pill hai** | `running`, `claimed_at 2026-09-08 11:30:34+00`, `attempts=1`, payload `{"seconds": 1, "crash_at": "before_commit"}` | Step 0D. Kal ke log me likha tha *"next reaper cycle me drain ho jaayegi"* — **wo galat hai.** `MAX_ATTEMPTS` sirf `except Exception` ke andar evaluate hota hai aur `os._exit` koi exception raise nahi karta, to bound ka branch **kabhi** nahi chalta (`P-36`). Isko `UPDATE`/`DELETE` se nahi chhuna (`P-05`) |
| **`sink_deliveries.idempotency_key` pe koi `UNIQUE` nahi hai** | Sirf `sink_deliveries_pkey` on `id`. Dedup `src/sink.py` me ek constraint-free `SELECT`-then-`INSERT` hai. Serial `2.1 s` → `1` row; concurrent `N=2` → **`2` rows**; `N=5` → **`5` rows** | Step 1. **Interleaving C iske pehle chal hi nahi sakti** — warna aaj ka `1` phir ek timing outcome hoga, dedup ka evidence nahi (`P-33`) |
| **`alembic check` evidence DB pe RED hai** | Proposed operation: `('remove_table', 'sink_deliveries')`, kyunki wo table `src/sink.py` ke `lifespan` ki `CREATE TABLE IF NOT EXISTS` se banti hai — koi model nahi, koi revision nahi | Step 1. Aaj tum ek nayi migration likhoge. Agar autogenerate use kiya, wo `drop_table` **chupchaap** usme daal degi aur wo kal ke poore measurement ka evidence le jaayegi (`P-34`) |
| **Dispatcher me na backoff hai na bound** | Ek closed port pe: `8` attempts `~20 s` me, `attempts 1→8`, `dispatched_at` still `NULL`. Do rows ke saath: `7/7` attempts failing row pe, `0` deliverable row pe | Aaj ise **fix nahi karna** (Part D). Aaj ise interleaving table me **do `[MEASURED]` row** ki tarah likhna hai. Aur Interleaving C plan karte waqt yaad rakhna: ek failing sink poore backlog ko rok deta hai (`P-35`) |

### Aur ek measured fact jo Step 2 ki harness ka design badal deta hai

`[MEASURED-R 2026-09-08]` `python-dotenv` ka installed signature:

```text
load_dotenv(dotenv_path=None, stream=None, verbose=False, override=False, interpolate=True, encoding='utf-8')
```

`src/database.py` line 1–10 pe `load_dotenv()` **import time** pe chalta hai, phir `DATABASE_URL =
os.environ["DATABASE_URL"]` ek **module-level constant** hai aur `engine` usi waqt ban jaata hai. Matlab galat
target ki galti **pehli query se pehle** ho chuki hoti hai — aur `.env` file repo root me maujood hai.

`override=False` ka **matlab** kya hai, ye ek Situation-1 vocabulary baat hai: *jo variable pehle se
`os.environ` me hai usko `.env` overwrite karta hai ya nahi.* Iska **outcome** aaj ka Part B **Q1** hai, aur wo
jawab iss BRIEF me kahin nahi hai. Ye ek library default hai jo tumhare experiment ka boundary set karta hai —
ye prediction nahi hai, par uska maidan hai.

---

# Part A — Steps

## Step 0 — 20 min: bench, freeze, aur job `136` ka faisla

**Terms used in this step**
- **Evidence DB:** `relay` — chaar hafte ka permanent record. Rows `DELETE` nahi hoti, sequence reset nahi hota (`P-05`).
- **Disposable / witness DB:** aaj ki `relay_w4_witness`. Aaj ka **saara** kaam isme hota hai. Din ke ant me `DROP`.
- **Frozen prediction:** answer ki immutable copy + SHA-256, measurement se pehle.
- **Poison pill:** ek payload jo handler ko crash karwata hai, aur isliye kisi bhi bound ke code path tak pahunchta hi nahi. Job `136` ka payload wahi hai.
- **`os._exit(n)` vs `sys.exit(n)`:** `sys.exit` ek exception raise karta hai (to `except`/`finally` chalte hain); `os._exit` process ko turant maar deta hai — `finally`, `atexit`, aur pending `COMMIT`, teeno skip.
- **Terminalise:** ek row ko `succeeded`/`failed`/`dead_letter` pe le jaana, taaki wo claim query ke predicate se bahar ho jaaye.

### 0A — commit state aur bench

Kal ka code **commit ho chuka hai** (`0129e5b`), aur docs bhi. To aaj Step 0A ek check hai, ek kaam nahi:
`git status --porcelain=v1 -- src alembic` khaali hona chahiye. Khaali nahi hai → pehle wo samjho, phir aage.

### 0B — environment aur logs

```powershell
New-Item -ItemType Directory -Path .\logs -Force | Out-Null
$env:PYTHONUNBUFFERED = "1"
```

**`DATABASE_URL` abhi set mat karo.** Aaj wo Step 1 ka subject hai aur Q1 uska padosi hai. Agar tumne isko
reflex me set kar diya, to Step 1 ka pre-flight assert ek cheez prove karega jo tumne haath se sach banayi hai.

### 0C — predictions likho aur freeze karo

1. `docs\daily\week_04\DIN_04_ANSWERS.md` **already exist karti hai** ek template ke roop me — Q1–Q5 ke
   headings aur khaali blocks ke saath. Usme sirf `### Prediction` bharo.
2. `### Prediction` non-empty (`idk` valid hai aur `0` score karta hai). Baaki do blocks freeze ke waqt **khaali**.
3. Phir neeche ka seal command **usi PowerShell terminal** me chalao (C0 aur C5 usi variable ko dobara maangenge).

```powershell
$answers = 'docs\daily\week_04\DIN_04_ANSWERS.md'
$frozen  = 'docs\daily\week_04\DIN_04_PREDICTIONS_FROZEN.md'
if (-not (Test-Path $answers)) { throw "Missing $answers" }
if (Test-Path $frozen) { throw "Frozen file already exists; overwrite forbidden: $frozen" }

$text  = (Get-Content $answers -Raw) -replace "`r`n","`n"
$cards = [regex]::Matches($text,'(?ms)^## Q(?<id>[1-5])[ \t]*\n(?<q>.*?)^### Prediction[ \t]*\n(?<p>.*?)^### Observed \+ meri explanation[ \t]*\n(?<o>.*?)^### After KEY[ \t]*\n(?<a>.*?)(?=^## Q[1-5][ \t]*$|^---[ \t]*$|^## Total Score[ \t]*$|\z)')
if ($cards.Count -ne 5) { throw "Expected 5 ordered answer cards, got $($cards.Count)" }
$ids = @($cards | ForEach-Object { [int]$_.Groups['id'].Value })
if (($ids -join ',') -ne '1,2,3,4,5') { throw "Cards must be Q1..Q5 in order; got $($ids -join ',')" }
foreach ($c in $cards) {
  $id = $c.Groups['id'].Value
  if (-not $c.Groups['p'].Value.Trim()) { throw "Q$id prediction empty; write idk if unknown" }
  if ($c.Groups['o'].Value.Trim())      { throw "Q$id Observed block must be empty before freeze" }
  if ($c.Groups['a'].Value.Trim())      { throw "Q$id After KEY block must be empty before freeze" }
}

# Kal ka reflection actually hua tha — aaj wo gate pass hona chahiye, aur ye reminder nahi hai
$d3 = (Get-Content 'docs\daily\week_04\DIN_03_ANSWERS.md' -Raw) -replace "`r`n","`n"
$d3Frozen = (Get-FileHash 'docs\daily\week_04\DIN_03_PREDICTIONS_FROZEN.md' -Algorithm SHA256).Hash
if ((Get-FileHash 'docs\daily\week_04\DIN_03_ANSWERS.md' -Algorithm SHA256).Hash -eq $d3Frozen) {
  throw 'DIN_03_ANSWERS.md is byte-identical to its frozen copy: Din 3 reflection missing'
}
if ($d3 -notmatch '(?im)^SCORE:\s*0\.25/5\.0') { throw 'DIN_03_ANSWERS.md has no SCORE line' }
'din3_reflection=done'

Copy-Item $answers $frozen
$d4FrozenHash = (Get-FileHash $frozen -Algorithm SHA256).Hash
$d4FrozenTime = (Get-Item $frozen).LastWriteTimeUtc.ToString('o')
"D4_FROZEN_SHA256=$d4FrozenHash"
"D4_FROZEN_MTIME_UTC=$d4FrozenTime"
```

Dono lines log me chipka do. Ab **C0** kholo aur chalao.

### 0D — job `136`: aaj ka pehla asli faisla, aur ye ek trap hai

Job `136` `running` hai. Uska payload handler ko crash karwata hai. Teen raaste hain aur **do galat hain**:

| Raasta | Kya hota hai | Verdict |
|---|---|---|
| Reaper chala do aur worker chala do | Reclaim → claim → `os._exit` → `running` → reclaim → … `attempts` badhta rehta hai, aur har iteration **do** sequence value jalati hai (`side_effects` + `outbox`) | **Galat.** Ye `P-36` ka loop hai. Agar tumne ye galti se chala diya, usko **band karo aur log me likho ki kitni iteration hui** — wo data hai, chhupane ki cheez nahi |
| `UPDATE jobs SET status='dead_letter' WHERE id=136` | Row terminal ho jaati hai | **Galat.** `P-05` evidence DB pe hand-write forbid karta hai, aur ye Week 1 se ek bhi baar nahi toota |
| Row ko **jaisi hai waisi chhod do**, reaper aaj **kabhi** evidence DB pe na chalao, aur uska loop **disposable DB pe** naapo | Evidence DB ka delta `0` rehta hai. `P-36` ka `[INFERRED]` `[MEASURED]` ban jaata hai, bina evidence DB me kachra dale | **Yahi karo** |

To Step 0D ka actual kaam ek line ka hai: **evidence DB pe aaj koi Relay process nahi chalega.** Job `136`
`running` hi rahega aur wo Din 6 ke close pe ek naam wali carried row hai. Uska loop Step 4 me interleaving
**B'** ki tarah disposable DB pe chalega, jahan sequence jal jaane se kisi ko farq nahi padta.

**Ye Part B Q5 ka maidan hai** — sawaal ka jawab nahi, par uski jagah.

**Executable end:** `git status --porcelain=v1 -- src alembic` khaali; printed frozen hash + mtime; C0 ka exact
tuple screen pe; `relay_processes=0`; aur likha hua faisla ki job `136` chhua nahi jaayega.

**KEY:** closed. Bench aur ye faisla kisi Part B sawaal ka jawab nahi kholte.

---

## Step 1 — 20 min: pehle guard, phir kaam — `P-28`, `P-34`, aur receiver ka `UNIQUE`

**Terms used in this step**
- **`P-28`:** Alembic Relay ke runtime `DATABASE_URL` ko **ignore** karta hai; `alembic/env.py` apna engine `alembic.ini` ke `sqlalchemy.url` (line 89, hardcoded) se banata hai. Ek disposable command chupchaap evidence DB pe chal sakta hai.
- **`alembic check`:** ek non-destructive command jo `Base.metadata` ko live DB se compare karta hai aur agar koi difference ho to **fail** karta hai. Wo kuch likhta nahi.
- **Autogenerate drift:** DB me ek object hai jise `models.py` nahi jaanta. Autogenerate uska `drop` propose karta hai, kyunki uske liye metadata sach hai.
- **`include_object`:** `alembic/env.py` ka ek hook jo autogenerate ko ek naam wale object ko **ignore** karne ko keh sakta hai.
- **Detector vs preventer:** ek assert jo galat target **pakadta** hai, versus ek config jo usko **hone hi nahi deta**. Dono chahiye aur dono ek nahi hain.
- **`23505`:** PostgreSQL ka `unique_violation` SQLSTATE.
- **`ON CONFLICT DO NOTHING` + `rowcount`:** `D-25` ka established local pattern — insert try karo, aur `rowcount` se pata karo ki row banī ya conflict hua. Guess nahi, `rowcount`.

### Faisla 1 — `P-28`: detector, preventer, ya dono

`DIN_04_DESIGN.md` ki pehli heading. Do option, dono ki `Cost` likhni hai:

| Option | Kya milta hai | Cost |
|---|---|---|
| `alembic/env.py` `DATABASE_URL` ko prefer kare (env → fallback `alembic.ini`) | Ek jagah fix, har future disposable run ke liye | `env.py` ka behaviour badla — Week 1 se aaj tak ki **saari** migrations isi file se chali hain, aur ye ek `src/`-adjacent change hai |
| Har disposable command se pehle ek **assert**: resolved URL print karo, DB naam match karo, warna abort | Zero code change, aur guard **dikhta** hai | Manual, aur ek din bhoolne pe guard nahi hai |

Aur chaahe kuch bhi chuno, **ek cheez aaj non-negotiable hai** kyunki aaj **paanch** process chal rahe hain
(API, worker × 2, reaper, dispatcher) aur **kisi ek** ka galat DB pe hona kaafi hai:

> **Har process apna resolved database naam startup pe print karta hai, aur harness paanchon lines match karne
> tak koi job enqueue nahi karta.** Ek bhi line `relay` kehti hai → sab band, run abort.

Step 5 ka post-hoc delta check **iske baad bhi** chalta hai. Dono ek jaisi cheez nahi pakadte: pre-flight galat
target **rokta** hai, delta check ek **chhoot gaye** process ko pakadta hai.

### Faisla 2 — `P-34`: `sink_deliveries` Alembic ke andar aaye ya bahar rahe

Teesri heading. Aur ye ek **design judgement** hai, iska koi ek sahi jawab nahi — Gemini se options aur unki
cost poochho, **pick nahi**.

Tension asli hai: kal ka design jaan-boojh ke sink ko Relay se **bahar** rakhta hai; usko `models.py` me daalna
uss boundary ko chupchaap khatam kar deta hai. Chaar option, aur chaaron me se ek chunna hai:

| Option | Kya milta hai | Kya todta hai |
|---|---|---|
| `SinkDelivery` model `src/models.py` me + ek migration | Autogenerate saaf, `UNIQUE` migration me | Receiver ki private storage Relay ka schema ban gayi — kal ka poora *"wo bahar hai"* argument gaya |
| Sink ki apni DB | Boundary bach gayi | Doosra `DATABASE_URL`, doosra Alembic tree. Kal ka *"alag DB ka koi measurement value nahi"* aaj sach nahi rehta |
| Sink ka apna metadata + `env.py` me `include_object` se exclude | Ek DB, aur exclusion **explicit aur greppable** | `env.py` change (Faisla 1 se overlap), aur `UNIQUE` phir startup DDL me hi jaata hai |
| Startup DDL rehne do + ek standing `alembic check` gate | Zero code change | **Detector hai, preventer nahi** — aur exactly wahi cheez kal job `136` ko nikal gayi thi |

**Jo cheez sawaal me nahi hai:** aaj ki state — jahan `alembic check` red hai aur us signal ko koi consume nahi
karta — wo ek hi option hai jiske liye koi argument nahi hai.

**Aur ek warning jo aaj ka evidence bacha sakti hai:** agar tum aaj `alembic revision --autogenerate` chalao,
uski body **padho** commit karne se pehle. `[MEASURED-R]` aaj wo `op.drop_table('sink_deliveries')` propose
karegi, aur wo revision review me bilkul routine dikhegi.

### Faisla 3 — receiver ka `UNIQUE`, aur `src/sink.py` ka insert shape

Doosri heading. `sink_deliveries.idempotency_key` pe `UNIQUE` aaj aata hai. Wo aasaan hissa hai. Asli faisla ye
hai ki `src/sink.py` ka pre-`SELECT` **rehta hai ya jaata hai**:

| Option | Kya hota hai jab do delivery overlap karti hain | Cost |
|---|---|---|
| `SELECT` rehta hai, `UNIQUE` bas peeche khada hai | Loser ka `INSERT` `23505` uthata hai. Wo `500` banta hai ya `duplicate`, ye tumhare exception handling pe hai — aur agar session reuse hua to Week 3 Din 4 ka `PendingRollbackError` bhi maidan me hai | Do code path jo ek hi baat kehte hain, aur unme se ek sirf race me chalta hai — matlab wo path aksar untested rehta hai |
| `SELECT` hatao, `ON CONFLICT DO NOTHING` + `rowcount` (`D-25` ka local pattern) | `rowcount=0` → `duplicate`, `rowcount=1` → `applied`. Ek statement, ek round trip, koi race window nahi | `applied`/`duplicate` ka label ab `rowcount` se aata hai — jo `D-25` ne local layer pe pehle hi decide kiya tha, to ye consistency hai, naya invention nahi |

**Ek chuno aur likho.** Aur ek line likhna zaroori hai: *`UNIQUE` add karne ke baad Run A ka `1` **kis cheez**
ka evidence ban jaata hai, jo kal nahi tha?* Ye Part B **Q4** ka padosi hai — jawab nahi, maidan.

**Ye `src/` code hai, matlab tum likhoge. Ready-made code iss BRIEF me nahi hai.**

**Executable node:** migration ka `downgrade()` **likha jaata hai** aur disposable DB pe chalta hai
(`upgrade head` → `downgrade -1` → `upgrade head`). `alembic heads` iske baad **exactly ek** line.

**Executable end:** `DIN_04_DESIGN.md` teen headings ke saath (chauthi Step 2 me); witness DB bani hui aur
Alembic uspe assert ke saath chali; `alembic check` **green** — ya red with a written, named reason;
`sink_deliveries` pe ek naam wala `UNIQUE` maujood; `pytest tests -q` exit `0`; C1 pass.

**KEY:** C1 pass hone ke baad → **"Open after Step 1 / C1 — Q1"**.

---

## Step 2 — 25 min: witness harness — "asli" ka matlab chaar cheezein hain

**Terms used in this step**
- **Layer B:** ek witness jo asli system ke against chalta hai, ek model ke against nahi. Week 3 Din 5 ka `6.5/10` isi ke na hone se aaya tha.
- **Production transaction boundary:** wo `BEGIN`/`COMMIT` jo `src/` ka code khud kholta hai. Test ka apna `BEGIN` uska substitute **nahi** hai.
- **Advisory lock:** `pg_advisory_lock(key)` — ek application-level lock jo kisi row se bandha nahi hai. Uski lifetime session ya transaction ho sakti hai.
- **`pg_sleep(n)`:** DB ke andar `n` second rukna, backend ke andar, client ke bahar.
- **Process suspend:** ek chal rahe process ko OS se rok dena. Windows pe koi `SIGSTOP` nahi hai; equivalent ek debugger-level suspend hai.
- **Barrier:** wo cheez jo do process ko *"ab"* pe sync karti hai. Uske bina "same instant" ek ummeed hai, measurement nahi.

### Chaar cheezein, aur ek bhi chhooti to ye phir Layer B nahi hai

1. **Do alag OS process**, `python -m src.worker`, apne `WORKER_ID = worker-<pid>` ke saath — ek process me do
   coroutine **nahi**. `job_executions.worker_id` me **do alag** value dikhni chahiye.
2. **Asli `src.reaper`** process, apne `2.0 s` poll aur `30 s` lease ke saath.
3. **Asli `src.dispatcher`** (kal se), kyunki `outbox` ab effect path ka hissa hai.
4. **Production transaction boundaries** — koi test-side `BEGIN`/`COMMIT` nahi, koi hand-written `INSERT INTO
   jobs` / `UPDATE jobs` nahi. Harness sirf **enqueue (HTTP)** aur **process orchestration** karti hai.

### Faisla 4 — interleaving deterministic kaise banate ho jab code me hook nahi daal sakte

Chauthi heading. Aur ye aaj ka sabse asli architectural sawaal hai, kyunki har option ka apna jawab hai
*"kya ye production path ko badalta hai"*:

| Option | Kya deta hai | Kya badalta hai |
|---|---|---|
| Payload-driven timing (`seconds`, `block`, `crash_at`) — **already exist karta hai** | Zero code change. Yahi kal Run A/B ko deterministic banaya tha | Resolution `POLL_INTERVAL_SECONDS = 2.0` ka hai. `P-24` ka poora sabak: quantum se chhota interval naapa nahi ja sakta |
| `pg_sleep` handler ke andar | Delay DB side pe, connection hold karke | Ek naya handler chahiye → `src/` badla, aur wo phir *"asli production path"* nahi rehta |
| Advisory lock se ek process ko rokna | Precise, aur bahar se control hota hai | Lock **bahar** se liya jaata hai. Wo production me exist nahi karta, to interleaving asli hai par uska trigger nahi |
| Process ko bahar se suspend karna | Production code bilkul nahi chhua | Windows pe ye clean nahi hai, aur ek suspended process ka TCP/lease behaviour **khud** ek unmeasured variable ban jaata hai |
| Staggered start + `45 s` blocking payload | Lease expiry ke against reliable, kal measured | `45 s` ka wall clock. Aaj chaar interleaving hain — arithmetic pehle karo |

**Ek chuno per interleaving** (sab ek hi hona zaroori nahi), aur har ek ke saath likho: *iss interleaving ka
trigger production me exist karta hai ya nahi.* Agar nahi karta, to wo **interleaving** asli hai aur uska
**cause** artificial — aur wo distinction log me likhi jaati hai, chhupayi nahi jaati.

**Aur ek cheez jo naam se likhni hai:** kal ka `P-22` amendment. Aaj **koi** PowerShell wrapper per-line
timestamp nahi lagayega jahan tum ordering ya duration claim karne wale ho. Process ka apna clock use karo
(`echo=True` already ek in-process clock deta hai) aur **timezone likho**. Jahan sirf order maayne rakhta hai,
`order only` likho, instant quote mat karo.

**Executable end:** `DIN_04_DESIGN.md` chaaron headings ke saath; paanch process start hote hain aur paanchon ka
`resolved_db` line screen pe `relay_w4_witness` kehti hai; ek smoke job witness DB pe enqueue hota hai aur
`succeeded` hota hai; C2 pass.

**KEY:** C2 pass hone ke baad → **"Open after Step 2 / C2 — Q2"**.

---

## Step 3 — 15 min: chaar interleaving, chalane se **pehle** likhi hui

**Terms used in this step**
- **`Mark fenced` vs `Conflict on mark`:** dono `rowcount = 0` hain aur `src/worker.py` unhe **alag** print karta hai. `fenced` = `claim_generation` badal gaya. `Conflict` = generation wahi hai par `status` predicate nahi mila.
- **Pre-reaper snapshot:** reaper ke chalne se **pehle** liya gaya DB read. Iske bina final row kuch prove nahi karti (`P-29`).
- **`claim_generation`:** ek monotonic integer jo **claim** pe badhta hai (Din 1). Reaper usko **nahi** badhata `[MEASURED-R]`.

Aaj ke chaar (aur ek paanchvaan jo kal ke closeout se aaya hai). **Har row ka expected outcome Part B me freeze
ho chuka hai** jahan wo ek prediction sawaal hai; baaki ke expected outcome yahan **assertion** hain, prediction
nahi:

| # | Interleaving | Kya specifically test ho raha hai |
|---|---|---|
| **A** | Worker A `45 s` blocking, lease expire, reaper reclaim, worker B claim, phir **A wapas aa ke mark kare** | `claim_generation` fence **production path pe**. Aaj ka target: project ka **pehla asli `Mark fenced`** — Din 2 ne `7` `Conflict on mark` diye aur `0` `fenced`, kyunki teesra claimant hi nahi tha |
| **B** | A effect commit karne ke **baad** `os._exit`, reaper reclaim, B re-execute | `D-25` ka `ON CONFLICT DO NOTHING` + `rowcount=0` production path pe. Per-job `side_effects` count `1` rehna chahiye |
| **B′** | Job `136` ka **clone** disposable DB pe: `crash_at: before_commit`, reaper + worker dono live, `~90 s` chalao | `P-36` ka `[INFERRED]` loop ko `[MEASURED]` banana. Iteration count, `attempts`, aur **dono sequence** ka delta record karo |
| **C** | A effect + outbox commit, dispatcher HTTP `200` ke baad crash, redeliver — **aur** Step 1 ke `UNIQUE` ke saath do dispatcher concurrently | `D-27` ka at-least-once + receiver dedup, **aur** `P-33` ka fix. Serial half kal pass hua tha; **concurrent half aaj pehli baar chalega** |
| **D** | Do worker ek hi `pending` row pe, same instant, koi crash nahi (**cuttable**) | `FOR UPDATE SKIP LOCKED` + CAS — Week 1 ka claim, aaj generation ke saath |

**Interleaving A ka ek trap jo abhi likh lo:** worker ka heartbeat `10.0 s` pe `claimed_at` **aage dhakelta**
hai. To reaper ko `30 s` **aakhri heartbeat** se ginne hote hain, crash se nahi. Ek `45 s` blocking handler
event loop **block** karta hai (`block: true` → `time.sleep`), to heartbeat coroutine chal hi nahi paati —
aur yahi wajah hai ki lease actually expire hoti hai. `block: false` rakh diya to heartbeat chalti rahegi,
lease kabhi expire nahi hogi, aur interleaving A **chup-chaap** kuch aur naap legi.

**Executable end:** interleaving table disk pe (`DIN_04_DESIGN.md` ke neeche ya ek alag section me), har row ka
expected outcome likha hua, aur ye **Step 4 se pehle**. Koi command nahi chalti — ye Step ka executable end ek
**file** hai, aur C3 usko structurally padhta hai.

**KEY:** closed. Expected outcome likhna KEY kholne ka bahana nahi hai.

---

## Step 4 — 35 min: chalao, aur har run ka **teen** snapshot lo

**Terms used in this step**
- **Snapshot:** ek DB read ek naam wale instant pe, UTC time ke saath likha hua.
- **`stale_gen_exec`:** wo `job_executions` rows jinki `claim_generation` job ki current generation se alag hai. `[MEASURED-R]` ye ek **derived** count hai — generation aage badhne pe wo **purani** rows ko retroactively stale label kar deta hai. Isliye ise "kitne stale writes hue" ki tarah **nahi** padha jaata.

Week 3 Din 3 ka established rule, aur wo aaj bhi lagu hai: **pre-reaper snapshot ke bina final row kuch prove
nahi karti** (`P-29`). Har interleaving ke liye teen snapshot:

1. crash/fence ke turant baad, **reaper band**
2. reaper ke **ek** pass ke baad
3. terminal hone ke baad

Teeno me: `jobs` ka relevant row (`status`, `attempts`, `claim_generation`, `claimed_at`, `completed_at`,
`last_error` ka non-null ya null), `job_executions` ka count + `worker_id` list, `side_effects` ka count,
`outbox` ka `count(*)`/`count(dispatched_at)`/`attempts`, aur `sink_deliveries` ka count uss key pe. Har
snapshot ke saath **UTC time**.

**Interleaving B′ alag hai** — usme teen snapshot nahi, ek **time series** hai: har iteration pe `attempts`,
`side_effects_id_seq`, `outbox_id_seq`. `~90 s` chalao, phir **band karo**, phir ginti karo. Aur ek cheez
naapna mat bhoolo jo `P-36` me `[INFERRED]` hai: **iteration ka period.** Lease `30 s` hai, reaper poll
`2.0 s`, worker poll `2.0 s` — teeno compose hote hain, aur nateeja `2 s` ke order ka hai ya `30 s` ke, ye
**naapna** hai, sochna nahi.

**Stop rule:** dono worker, reaper, dispatcher, sink — sab loop hain. Har interleaving ka teesra snapshot lene
ke turant baad **uss interleaving ke process band karo**. Agla interleaving saaf process se shuru hota hai,
warna attribution khatam (`P-13`).

**Executable end:** chaar (ya paanch) interleaving ke `[MEASURED]` outcome, teen-teen snapshot ke saath; kam se
kam ek `Mark fenced` line kisi worker ke stdout me; `logs\w4d4_*.log` disk pe; C4 pass.

**KEY:** C4 pass hone ke baad → **"Open after Step 4 / C4 — Q3, Q4, Q5"**.

---

## Step 5 — 15 min: cleanup, aur cleanup khud ek measurement hai

**Terms used in this step**
- **Evidence delta:** `relay` DB ke counts, aaj ke shuru me aur aaj ke ant me. Aaj expected delta **`0`** hai.
- **Detector vs preventer, dobara:** pre-flight galat target rokta hai; ye delta check ek **chhoot gaye** process ko pakadta hai. Dono chalte hain.

Paanch cheezein, aur paanchvi hi aaj ki nayi hai:

1. Saare Relay process band, aur ginti `0`.
2. Witness DB `DROP`, aur `probe_dbs` count `0`.
3. `logs\w4d4_*.log` disk pe, non-zero length.
4. `git status --porcelain=v1 -- src alembic` me sirf aaj ki expected files.
5. **Evidence DB ka delta `0`** — `relay` me aaj ek bhi naya row nahi jaana chahiye. Job `136` still `running`,
   `attempts` still `1`. Agar `attempts` badh gaya hai, to reaper evidence DB pe chala tha aur `P-36` ka loop
   waha shuru ho gaya — usko band karo aur log me **ginti** likho.

**Executable end:** C5 pass, jisme evidence delta `0` ek `throw` hai, `print` nahi.

**KEY:** C5 ke baad **"Known traps"**, phir **"Final scoring rubric"** kholo aur frozen text ko `/5` pe grade
karo. Post-run prose ko credit nahi milta.

---

## Din close pe reviewer ko kya dena hai

Plan ka DOC-SYNC Din 4 ke liye: `logs/WEEK_04.md` · `PROBLEMS.md` (`P-28` update, aur `P-33`/`P-34`/`P-36` ka
outcome) · `DECISIONS.md` me **kuch nahi** (`D-26`–`D-29` Din 6 ke hain, aur `D-26` ka `Cost` aaj ke witness se
banta hai — usko aaj **evidence** ki tarah likho, entry ki tarah nahi).

`P-` number chahiye to **uss din grep karo** (`E6`). `[MEASURED-R 2026-09-08]` aaj ka expected next-free
**`P-37`** hai (`PROBLEMS.md` ka last entry `P-36`), aur `D-` ka next-free **`D-26`** — par register hi sach hai.

Reviewer ko aath cheezein chahiye: `DIN_04_PREDICTIONS_FROZEN.md` + printed hash, bhara hua `DIN_04_ANSWERS.md`,
`DIN_04_DESIGN.md` (chaar heading), interleaving table apne teen-teen snapshot ke saath, `Mark fenced` line ka
raw stdout, B′ ka iteration count + period + sequence delta, saare `w4d4_*.log`, aur C0–C5 ka raw output.

---

# Part B — Prediction questions — **Gemini ko paste mat karna**

> Step 0 me **paanchon** answer aur freeze karo, Step 1 shuru hone se pehle. `idk` valid hai aur `0` score
> karta hai. `idk — <sahi jawab>` bhi `0` hai. Inke jawab iss block me nahi hain, aur BRIEF me kahin nahi hain.
>
> Kal ka accha beat dobara: `### Observed` block **uss step ke turant baad** bharo, Step 0 me nahi, aur KEY se
> **pehle**. Kal wo paanchon bhare gaye the — wo iss hafte ka sabse bada process improvement hai, usko todna nahi.

```text
Q1. src/database.py import pe load_dotenv() chalata hai (override=False) aur phir
    DATABASE_URL = os.environ["DATABASE_URL"] ek module-level constant hai. Repo root me .env maujood
    hai aur usme DATABASE_URL relay pe point karta hai. Tum PowerShell me $env:DATABASE_URL ko
    relay_w4_witness pe set karke `python -m src.worker` chalate ho.
    (a) Worker kis DB pe connect karega, aur kaun jeeta — .env ya shell?
    (b) Ab wahi terminal se `python -m alembic upgrade head` chalao. Wo kis DB pe chalega, aur kyu?
    (c) Ek naya PowerShell tab kholke, bina kuch set kiye, wahi worker command chalao. Kis DB pe?

Q2. Do asli worker process, ek hi pending row, dono ka claim query
    SELECT ... WHERE status='pending' ORDER BY created_at, id LIMIT 1 FOR UPDATE SKIP LOCKED
    ke baad ek guarded UPDATE ... WHERE id=:id AND status='pending'. READ COMMITTED.
    Kitne worker row claim karenge, aur HAARNE WALE worker ke stdout me kya aayega -- teen possible
    lines hain (empty poll, "Conflict: ... rowcount=0", ya ek error) aur uska jawab isi pe hai ki
    SKIP LOCKED ne usko row DIKHAYI thi ya nahi. Ek chuno aur mechanism likho.

Q3. Interleaving A: worker A ne job claim kiya (generation g), 45 s blocking handler chal raha hai,
    lease 30 s pe expire hui, reaper ne reclaim kiya, worker B ne claim kiya. Ab A wapas aata hai aur
    apna mark UPDATE chalata hai:
    WHERE id=:id AND status='running' AND claim_generation=:g
    (a) rowcount kya hoga?
    (b) A ke stdout me "Mark fenced" aayega ya "Conflict on mark" -- aur reaper ke reclaim ke BAAD
        par B ke claim se PEHLE A mark karta to kaunsa aata?
    (c) A ke paas status, next_attempt_at, completed_at, aur last_error -- chaar value thi. Rejection
        ke baad in chaar ka DB me kya hota hai?

Q4. Step 1 me sink_deliveries.idempotency_key pe UNIQUE aa gaya hai. Ab do dispatcher process ek hi
    outbox row pe, bilkul same instant, dono ne HTTP 200 se pehle wahi idempotency_key bheji.
    (a) sink_deliveries me kitni rows?
    (b) Dono dispatcher ko HTTP se kya status code milega -- aur ye jawab iss pe depend karta hai ki
        src/sink.py me pre-SELECT hai ya ON CONFLICT DO NOTHING. Dono ke liye alag likho.
    (c) Jis dispatcher ko non-200 mila, uske outbox row ka dispatched_at aur attempts ka kya hoga?

Q5. Interleaving B': job 136 ka clone disposable DB pe -- payload {"seconds": 1,
    "crash_at": "before_commit"}, reaper aur worker dono live, 90 s tak chhod do.
    (a) Kitni iteration hongi? (Number nahi -- ORDER OF MAGNITUDE aur uska mechanism: kaun sa timer
        period decide karta hai?)
    (b) 90 s ke baad attempts kya hoga, aur status kya hoga?
    (c) side_effects_id_seq aur outbox_id_seq ka total delta kya hoga, aur per iteration kitna?
```

---

# Part C — Verification

Sab **PowerShell 7** syntax hai aur repo root `d:\PROJECTS\relay` se chalta hai. `docker compose` service ka
naam **`db`** hai. PostgreSQL **16.14**, port **5433**, `-U postgres`. Jahan `throw` hai wahan step **rukta**
hai — stray process chala ke state "repair" mat karna. **`&&` kahin nahi hai; separator `;` hai.**

**Har check ke saath do column hain: mechanism maujood, aur mechanism ghayab. Jis check ka dono column same
output deta hai, wo check decorative hai (`P-18`).**

**Aur aaj ka apna rule, kal ke `P-31` amendment se:** iss Part C me jo bhi quantity *"Mechanism ghayab"* column
me appear karti hai, uske liye ek `throw` hai. Jahan sirf record karna hai, wahan **`record only, not asserted`**
likha hua hai. Kal C5b ne `queue|0|1` print kiya aur din *"YES, completely"* pe band hua — wo dobara nahi hoga.

## C0 — clean tree, opening bench, seal, single head, aur job `136` ka baseline

Seal command ke **usi terminal** me:

```powershell
if (-not $d4FrozenHash) { throw 'Step 0C hash variable missing; C0 must run in the same PowerShell terminal' }
$frozen = 'docs\daily\week_04\DIN_04_PREDICTIONS_FROZEN.md'
if ((Get-FileHash $frozen -Algorithm SHA256).Hash -ne $d4FrozenHash) { throw 'Frozen predictions changed after Step 0C' }
"D4_FROZEN_SHA256_UNCHANGED=$d4FrozenHash"

$dirty = @(git status --porcelain=v1 -- src alembic)
$dirty
if ($dirty.Count -ne 0) { throw "src/ or alembic/ is dirty before Din 4 starts:`n$($dirty -join "`n")" }
$head = (git rev-parse --short HEAD).Trim()
"HEAD=$head"
@(git log --oneline -3)

# kal ka code actually tree me hai — commit message par bharosa nahi
if (-not (Test-Path src\dispatcher.py)) { throw 'src/dispatcher.py missing' }
if (-not (Test-Path src\sink.py))       { throw 'src/sink.py missing' }
if ((Get-Content src\worker.py -Raw) -notmatch 'Outbox')      { throw 'worker.py does not reference Outbox; Din 3 co-commit missing' }
if ((Get-Content src\worker.py -Raw) -notmatch 'before_commit'){ throw 'worker.py has no before_commit crash hook (P-23)' }
'din3_code_present=True'

$relayProcs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper|dispatcher|sink)' })
$relayProcs | Select-Object ProcessId, ParentProcessId, CommandLine
if ($relayProcs.Count -ne 0) { throw "Relay process count is $($relayProcs.Count), expected 0" }
"relay_processes=0   (reminder: one logical process = 2 rows here, venv shim + interpreter)"

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
  (select count(*) from outbox),
  (select last_value from outbox_id_seq),
  (select count(*) from sink_deliveries),
  (select version_num from alembic_version)) from jobs;
select concat_ws('|', count(*) filter (where status='succeeded'), count(*) filter (where status='failed'),
  count(*) filter (where status='pending'), count(*) filter (where status='dead_letter'),
  count(*) filter (where status='running'), count(*)) from jobs;
select coalesce(string_agg(id::text||':'||status||':'||attempts::text||':'||claim_generation::text, ',' order by id),'none')
  from jobs where status in ('running','pending');
select concat_ws('|','job136_payload', payload::text) from jobs where id=136;
select concat_ws('|','sink_uniq', coalesce(string_agg(conname, ',' order by conname),'NONE'))
  from pg_constraint where conrelid='sink_deliveries'::regclass and contype='u';
select concat_ws('|','undispatched', count(*)) from outbox where dispatched_at is null;
select concat_ws('|','idle_in_txn', count(*)) from pg_stat_activity
  where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select concat_ws('|','probe_dbs', count(*)) from pg_database where datname like 'relay_w4%';
'@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'C0 SQL failed' }
$actual = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$actual
$expected = @(
  'relay|133|139|139|145|19|39|4|5|10|w4d3_outbox',
  '112|15|0|5|1|133',
  '136:running:1:1',
  'job136_payload|{"seconds": 1, "crash_at": "before_commit"}',
  'sink_uniq|NONE',
  'undispatched|0',
  'idle_in_txn|0',
  'probe_dbs|0'
)
if (($actual -join "`n") -ne ($expected -join "`n")) {
  throw "C0 fingerprint mismatch.`nACTUAL:`n$($actual -join "`n")`nEXPECTED:`n$($expected -join "`n")"
}
'C0=pass'

# Step 5 ka delta check hardcode nahi karega — baseline yahan capture hota hai
$evBase = $actual[0]
"EVIDENCE_BASELINE=$evBase"
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Kal ka code commit **aur** tree me hai | `src/dispatcher.py` + `src/sink.py` maujood, `worker.py` me `Outbox` aur `before_commit` | `git log` dekhna kaafi nahi: ek commit message *"add outbox"* keh sakta hai jabki hook revert ho gaya ho. Isliye source ka grep bhi hai |
| Bench Din 3 close se match | poora `8`-line tuple | Koi bhi farq → **divergence**, Din 4 rukta hai jab tak cause naam se na mile (`E2`) |
| **Job `136` ka exact shape** | `136:running:1:1` **aur** payload line | Sirf count match karta par payload na hoti → aaj B′ ka clone galat payload pe banta. Aur `attempts` `1` se **bada** hai → reaper evidence DB pe chal chuka hai aur `P-36` ka loop shuru ho gaya. **Wo ek finding hai, ek error nahi — ginti likho** |
| **`sink_deliveries` pe koi `UNIQUE` nahi hai, aaj ke shuru me** | `sink_uniq|NONE` | Kuch aur → koi ne Step 1 pehle kar liya, aur Interleaving C ka before/after compare khatam. **Ye line aaj ka pehla `[MEASURED]` baseline hai** (`P-33`) |
| `pending 0` **aur** `running 1` dono asserted | `112\|15\|0\|5\|1\|133` | Kal C5b ne ye print kiya aur assert nahi kiya. Aaj ye `$expected` ke andar hai, to `throw` hai |
| Single head | ek `(head)` line | Do heads → branch ban gayi. Aaj **chauthi** consecutive migration hai |
| Koi process zinda nahi | `relay_processes=0` | Ek purana worker → wo job `136` utha lega aur `P-36` ka loop evidence DB pe chal padega (`P-13`) |
| Frozen predictions immutable | hash unchanged | Hash badla → uss sawaal ka score `seal broken` |

## C1 — `P-28` guard, witness DB, `UNIQUE`, aur `DIN_04_DESIGN.md` ka structural gate

### C1a — witness DB banao, aur Alembic ka target **assert** karo (yahi `P-28` hai)

```powershell
$witness = 'relay_w4_witness'
docker compose exec -T db psql -X -Atq -U postgres -d postgres -c "drop database if exists $witness" | Out-Null
docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d postgres -c "create database $witness" | Out-Null
$iniCopy = ".\_w4d4_$PID.ini"
((Get-Content .\alembic.ini -Raw) -replace 'sqlalchemy\.url = .*', "sqlalchemy.url = postgresql+psycopg://postgres:relay@localhost:5433/$witness") |
  Set-Content -Path $iniCopy -Encoding utf8

# ASSERT, print nahi: resolved URL me witness DB ka naam hona chahiye
$resolved = (Select-String -Path $iniCopy -Pattern '^sqlalchemy\.url').Line
$resolved
if ($resolved -notmatch [regex]::Escape($witness)) { throw "P-28: ini copy does not target $witness" }
if ($resolved -match '/relay\s*$')                 { throw "P-28: ini copy still targets the evidence DB" }
'p28_target_asserted=True'
```

### C1b — migration lifecycle witness DB pe, phir `UNIQUE` ka **positive** proof

```powershell
$q = "select concat_ws('|','X',(select version_num from alembic_version), (select count(*) from pg_constraint where conrelid='sink_deliveries'::regclass and contype='u'));"
try {
  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy upgrade head
  if ($LASTEXITCODE -ne 0) { throw 'witness upgrade head failed' }
  ($q -replace "'X'", "'head'") | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $witness
  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy downgrade -1
  if ($LASTEXITCODE -ne 0) { throw 'downgrade -1 failed — ye aaj pakda gaya, Din 5 pe nahi' }
  ($q -replace "'X'", "'down'") | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $witness
  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy upgrade head
  if ($LASTEXITCODE -ne 0) { throw 're-upgrade head failed' }
  ($q -replace "'X'", "'reup'") | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $witness

  # P-28 ka discriminator: evidence DB chhui gayi ya nahi
  $ev = @(("select concat_ws('|','evidence_untouched',(select version_num from alembic_version),(select count(*) from jobs));" |
    docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)) |
    ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
  $ev
  if ($ev[0] -notmatch '^evidence_untouched\|') { throw 'evidence probe failed' }
  if ($ev[0] -ne "evidence_untouched|$(($EvidenceHead = 'w4d4_sink_unique'))|133" -and $ev[0] -notmatch '\|133$') {
    throw "P-28 fired or evidence jobs count moved: $($ev[0])"
  }
} finally {
  Remove-Item $iniCopy -Force -ErrorAction SilentlyContinue
}
```

> **Note on the line above:** the evidence DB's `version_num` **will** change today, because the new
> `sink_deliveries` `UNIQUE` migration has to be applied to `relay` as well if you keep the table in `relay`.
> That is a **consequence of Faisla 2** and it is the one thing in this Part C you must adjust by hand once
> Faisla 2 is written. If Faisla 2 puts the sink in its own database or excludes it via `include_object`, then
> `relay`'s `version_num` must **not** change and the assertion above stays as-is. **Write which case you are
> in before running this**, because otherwise this check will pass for the wrong reason.

Ab `UNIQUE` ka teen-arm differential — **yahi kal ka missing check hai** (`P-33`). Sink witness DB pe chalao:

```powershell
# uvicorn src.sink:app --port 8011  with $env:DATABASE_URL pointing at relay_w4_witness, $env:SINK_DEDUP='1'
$kS = "w4d4-serial-$([guid]::NewGuid().ToString('N'))"
$b  = @{ idempotency_key=$kS; job_id=0; body=@{p=1} } | ConvertTo-Json -Compress
$r1 = Invoke-RestMethod -Uri 'http://127.0.0.1:8011/deliver' -Method Post -ContentType 'application/json' -Body $b
Start-Sleep -Milliseconds 2100
$r2 = Invoke-RestMethod -Uri 'http://127.0.0.1:8011/deliver' -Method Post -ContentType 'application/json' -Body $b
"serial=$($r1.result),$($r2.result)"
```

Concurrent arm ko **PowerShell se mat chalao** — `[MEASURED-R 2026-09-08]` `ForEach-Object -Parallel` ki
runspace startup skew `~4 ms` window se kaafi zyada hai aur wo race ko **reproduce nahi karti** (`applied,
duplicate`, `1` row). Ek chhoti Python script se `asyncio.gather()` pe chalao, aur usko din ke ant me delete
karo — **ya** usko `tests/` me rakho aur wo ek decision hai jo likha jaata hai.

```powershell
$rows = @(("select concat_ws('|','k', idempotency_key, count(*)) from sink_deliveries group by idempotency_key order by min(id);" |
  docker compose exec -T db psql -X -Atq -U postgres -d relay_w4_witness)) |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
$rows
$serialRows = [int](($rows | Where-Object { $_ -match [regex]::Escape($kS) }) -split '\|')[-1]
if ($serialRows -ne 1) { throw "Serial arm stored $serialRows rows, expected 1" }
# concurrent arm: N=2 aur N=5, dono ke stored rows 1 hone chahiye
'C1b=pass'
```

### C1c — `DIN_04_DESIGN.md`, structural gate

```powershell
$design = 'docs\daily\week_04\DIN_04_DESIGN.md'
if (-not (Test-Path $design)) { throw "Missing $design" }
$text = (Get-Content $design -Raw) -replace "`r`n","`n"
$sections = [regex]::Matches($text,'(?ms)^## (?<title>[^\n]+)\n(?<body>.*?)(?=^## |\z)')
if ($sections.Count -ne 4) { throw "Expected exactly 4 '## ' decision sections, got $($sections.Count)" }
foreach ($s in $sections) {
  $title = $s.Groups['title'].Value.Trim(); $body = $s.Groups['body'].Value
  foreach ($label in 'Chosen','Rejected','Cost') {
    $m = [regex]::Match($body,"(?m)^\s*(?:[-*]\s*)?(?:\*\*)?$label(?:\*\*)?\s*:\s*(?<v>.+)$")
    if (-not $m.Success)                           { throw "[$title] missing '${label}:' line" }
    if ($m.Groups['v'].Value.Trim().Length -lt 20) { throw "[$title] '${label}:' too short to be a reason" }
  }
  "OK: $title"
}
if ($text -notmatch '(?i)detector')                       { throw 'Faisla 1 me detector-vs-preventer ka farq nahi hai' }
if ($text -notmatch '(?i)alembic\.ini|env\.py')           { throw 'Faisla 1 me P-28 ka actual mechanism nahi hai' }
if ($text -notmatch '(?i)autogenerate|include_object')    { throw 'Faisla 2 me P-34 ka mechanism nahi hai' }
if ($text -notmatch '(?i)on conflict|23505|rowcount')     { throw 'Faisla 3 me insert shape ka mechanism nahi hai' }
if ($text -notmatch '(?i)production path|production ke')  { throw 'Faisla 4 me "kya ye production path badalta hai" ka jawab nahi hai' }
# negative gate: aaj bhi overclaim allowed nahi
if ($text -match '(?i)(unique|constraint)[^.\n]*(eliminat|guarantees exactly.?once|exactly.?once guarantee)') {
  throw 'File claims a UNIQUE eliminates duplicate delivery. It narrows duplicate STORAGE; delivery stays at-least-once'
}
'C1c=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **`P-28` assert hua, print nahi** | `p28_target_asserted=True`, aur `throw` on `/relay$` | Sirf `Select-String` print → wahi Week 3 Din 2 ki galti, aur ek din bhoolne pe guard nahi hai |
| **Serial arm `1` row** | `serial=applied,duplicate` + stored `1` | Kal ye pass hua tha **bina `UNIQUE`**. To ye check akela `UNIQUE` ka evidence **nahi** hai — concurrent arm hi discriminator hai |
| **Concurrent arm `1` row** | `N=2` aur `N=5`, dono stored `1` | `2` ya `5` → `UNIQUE` add nahi hua ya `src/sink.py` usko catch nahi kar raha. **Kal exactly ye `2` aur `5` mile the** (`P-33`) |
| Concurrent arm actually concurrent tha | `asyncio.gather()` se, PowerShell se nahi | `ForEach-Object -Parallel` → `[MEASURED-R]` race reproduce nahi hoti, aur nateeja *"receiver idempotent hai"* aata hai jo galat hai (`P-12`) |
| Migration reversible | `head` → `down` → `reup` | `downgrade` fail → Din 5 ki disposable DB uss din tootegi jab time nahi hoga |
| Chaar faisle, chaaron ka rejected option | 4 × (`Chosen`/`Rejected`/`Cost`) | Sirf `Chosen` → wo faisla nahi, preference hai (AGENTS rule 28) |
| **Overclaim guard** | Regex `unique … eliminates` par `throw` | Kal ka poora sabak: `UNIQUE` duplicate **storage** ko rokta hai. Delivery at-least-once **rehti** hai. `narrows`, `closes` nahi |

## C2 — paanch process, paanch resolved DB names, aur ek smoke job

```powershell
$witness = 'relay_w4_witness'
# Har process ka startup pe resolved DB naam. Ye harness ka pehla gate hai, aur wo THROW karta hai.
$expectedProcs = @('api','worker-a','worker-b','reaper','dispatcher')
$resolvedLines = @(Get-Content .\logs\w4d4_preflight.log | Where-Object { $_ -match 'resolved_db=' })
$resolvedLines
if ($resolvedLines.Count -ne 5) { throw "Expected 5 resolved_db lines, got $($resolvedLines.Count)" }
$bad = @($resolvedLines | Where-Object { $_ -notmatch "resolved_db=$witness\b" })
$bad | ForEach-Object { "WRONG_TARGET: $_" }
if ($bad.Count -ne 0) { throw "$($bad.Count) process(es) resolved to the wrong database. Stop everything (P-28)" }
'preflight_five_of_five=True'

$procs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper|dispatcher|sink)' })
$procs | Select-Object ProcessId, CommandLine
$workerPids = @($procs | Where-Object { $_.CommandLine -match 'src\.worker' } | Select-Object -ExpandProperty ProcessId -Unique)
"worker_pid_count=$($workerPids.Count)"
if ($workerPids.Count -lt 2) { throw "Fewer than 2 distinct worker PIDs; this is not Layer B (handoff item 4)" }
```

```powershell
$sql = @"
select concat_ws('|','smoke', id, status, attempts, claim_generation, coalesce(completed_at::text,'NULL')) from jobs order by id;
select concat_ws('|','workers', coalesce(string_agg(distinct worker_id, ',' order by worker_id),'NONE')) from job_executions;
"@
$out = @(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $witness) |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
$distinctWorkers = @((($out | Where-Object { $_ -match '^workers\|' }) -split '\|')[1] -split ',')
"distinct_worker_ids=$($distinctWorkers.Count)"
if ($distinctWorkers.Count -lt 2) { throw "job_executions shows $($distinctWorkers.Count) worker_id(s); one process ran twice, not two processes" }
'C2=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Paanchon process ne witness DB resolve kiya** | `preflight_five_of_five=True` | Ek bhi `relay` → aaj ka delta `0` nahi rahega, aur `P-36` ka loop evidence DB pe chal sakta hai. **Ye print nahi, `throw` hai** |
| **Do alag OS process** | Do distinct `ProcessId` **aur** `job_executions` me do distinct `worker_id` | Ek `worker_id` do baar → ek process, aur ye phir Layer B nahi hai. Wahi `6.5/10` ki wajah thi. **PID count akela kaafi nahi** — DB side se bhi confirm hota hai |
| Transaction boundaries production ki thi | Harness me zero `INSERT INTO jobs` / `UPDATE jobs` | Hand-written claim SQL → Week 3 ki wahi galti, naye naam se. `Select-String` se apni harness khud grep karo |
| Smoke job terminal hua | `succeeded` + `completed_at` non-`NULL` | Nahi hua → aage koi interleaving trust karne layak nahi |

## C3 — interleaving table chalane se **pehle** disk pe

```powershell
$il = 'docs\daily\week_04\DIN_04_DESIGN.md'
$text = (Get-Content $il -Raw) -replace "`r`n","`n"
foreach ($tag in 'Interleaving A','Interleaving B','Interleaving C') {
  if ($text -notmatch [regex]::Escape($tag)) { throw "$tag not described before Step 4" }
}
if ($text -notmatch '(?i)Mark fenced')      { throw 'Interleaving A ka expected outcome (Mark fenced) likha nahi hai' }
if ($text -notmatch '(?i)pre-reaper|reaper band') { throw 'Teen-snapshot protocol (P-29) likha nahi hai' }
'C3=pass   (record only for the expected values themselves: they are predictions, not assertions)'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Expected outcomes **pehle** likhe gaye | Teeno interleaving + `Mark fenced` + snapshot protocol file me | Baad me likhe → wo observation hai, prediction nahi, aur din ka poora point chala gaya |
| Expected values khud asserted **nahi** hain | `record only` | Unko assert karna prediction ko test me badal dena hai. Wo galat hai — wo Part B ka kaam hai |

## C4 — interleaving ke outcomes, aur pehla asli `Mark fenced`

```powershell
# P-32 ka gate half, aaj TEEN producers pe: worker A, worker B, reaper, dispatcher
$jobIdA = $ilAJob
if (-not $jobIdA) { throw 'ilAJob missing; C4 ko usi terminal se chalao jisne enqueue kiya' }
foreach ($f in @('.\logs\w4d4_ilA_workerA.log','.\logs\w4d4_ilA_workerB.log','.\logs\w4d4_ilA_reaper.log','.\logs\w4d4_ilA_dispatcher.log')) {
  if (-not (Test-Path $f)) { throw "Missing $f" }
  $decay = @(Get-Content $f | Where-Object { $_ -match "\b(job|outbox row) $jobIdA\b" -and $_ -notmatch 'job_id=' })
  "unstructured[$([IO.Path]::GetFileName($f))]=$($decay.Count)"
  $decay | ForEach-Object { "UNSTRUCTURED: $_" }
  if ($decay.Count -gt 0) { throw "$f mentions the job without job_id= — P-32 with four producers" }
}

# aaj ka centrepiece: project ka pehla asli fence
$fenced = @(Get-Content .\logs\w4d4_ilA_workerA.log | Where-Object { $_ -match 'Mark fenced: job_id=' })
"fenced_lines=$($fenced.Count)"
$fenced | ForEach-Object { "FENCE: $_" }
if ($fenced.Count -lt 1) { throw 'Zero "Mark fenced" lines: interleaving A never produced a third claimant. Run invalid, repeat' }
$conflicts = @(Get-Content .\logs\w4d4_ilA_workerA.log | Where-Object { $_ -match 'Conflict on mark' })
"conflict_on_mark_lines=$($conflicts.Count)   (record only: this distinguishes fence from status-only rejection)"
'C4_fence=pass'
```

```powershell
$sql = @"
select concat_ws('|','dup_effects', job_id, count(*)) from side_effects group by job_id having count(*) > 1;
select concat_ws('|','effects_ok', count(*)) from (select job_id from side_effects group by job_id having count(*) > 1) x;
select concat_ws('|','exec_vs_jobs', (select count(*) from job_executions), (select count(*) from jobs));
select concat_ws('|','outbox', job_id, count(*), count(dispatched_at), max(attempts)) from outbox group by job_id order by job_id;
select concat_ws('|','sink', idempotency_key, count(*)) from sink_deliveries group by idempotency_key order by min(id);
"@
$out = @(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay_w4_witness) |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
$dupCount = [int](( ($out | Where-Object { $_ -match '^effects_ok\|' }) -split '\|')[1])
if ($dupCount -ne 0) { throw "$dupCount job(s) have more than one side_effect row — D-25 broke on the production path" }
$ev = (($out | Where-Object { $_ -match '^exec_vs_jobs\|' }) -split '\|')
if ([int]$ev[1] -le [int]$ev[2]) { throw "job_executions ($($ev[1])) <= jobs ($($ev[2])): no duplicate dispatch happened, so 'exactly once' was not tested today" }
'C4=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Fence production path pe fired** | `fenced_lines >= 1` in worker A's stdout | Zero → interleaving A ne overlap banaya hi nahi. **Run invalid, repeat.** Din 2 ne `7` conflict aur `0` fence diye, to ye pehli baar hai |
| **`fenced` aur `Conflict on mark` alag ginte hain** | dono counts screen pe | Sirf `rowcount=0` dekhna dono ko ek kar deta hai, aur wo do bilkul alag rejections hain (`claim_generation` vs `status`) |
| Per-job effect count `1` | `effects_ok\|0` | Non-zero → `D-25` production path pe toota, aur wo iss hafte ka sabse bada finding hoga |
| **`job_executions > jobs`** | strict `>` | Barabar → koi duplicate dispatch hua hi nahi, matlab *"exactly once"* ka aaj **koi test nahi hua**. Ye `P-12` ka gate hai: test hua ya nahi, ye pass/fail se pehle ka sawaal hai |
| Chaaron producer ka log check hota hai | `unstructured[...]=0` × 4 | Sirf ek log → `P-32` teesri baar, aur ab **chaar** producer hain |

## C5 — cleanup, aur evidence DB ka delta `0` ek `throw` ki tarah

```powershell
$frozen = 'docs\daily\week_04\DIN_04_PREDICTIONS_FROZEN.md'
if ((Get-FileHash $frozen -Algorithm SHA256).Hash -ne $d4FrozenHash) { throw 'Frozen predictions changed during the day' }
'frozen_unchanged=True'

$relayProcs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper|dispatcher|sink)' })
$relayProcs | Select-Object ProcessId, ParentProcessId, CommandLine
if ($relayProcs.Count -ne 0) { throw "Din 4 ke baad $($relayProcs.Count) Relay process zinda hain (P-13)" }

# witness DB ka closing bench pehle — DROP se PEHLE, warna evidence chala jaata hai
$sql = @'
set time zone 'UTC';
select concat_ws('|','witness_close', (select count(*) from jobs), (select count(*) from job_executions),
  (select count(*) from side_effects), (select count(*) from outbox), (select count(*) from sink_deliveries),
  (select version_num from alembic_version));
select concat_ws('|','status', status, count(*), count(completed_at), count(last_error)) from jobs group by status order by status;
select concat_ws('|','queue', count(*) filter (where status='pending'), count(*) filter (where status='running')) from jobs;
select concat_ws('|','undispatched', count(*)) from outbox where dispatched_at is null;
select concat_ws('|','stale_gen_exec', count(*)) from job_executions e join jobs j on j.id=e.job_id
  where e.claim_generation is not null and e.claim_generation <> j.claim_generation;
'@
@(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay_w4_witness) |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
```

```powershell
# AAJ KA PAANCHVAAN ITEM: evidence DB ka delta 0, aur ye print nahi hai
$sql = @'
select concat_ws('|', current_database(), count(*), max(id),
  (select last_value from jobs_id_seq),
  (select count(*) from job_executions),
  (select count(*) from side_effects),
  (select last_value from side_effects_id_seq),
  (select count(*) from outbox),
  (select last_value from outbox_id_seq),
  (select count(*) from sink_deliveries),
  (select version_num from alembic_version)) from jobs;
select concat_ws('|','job136', id, status, attempts, claim_generation) from jobs where id=136;
'@
$now = @(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$now
"EVIDENCE_BASELINE=$evBase"
# alembic_version aur sink_deliveries Faisla 2 ke hisaab se badal SAKTE hain; jobs/exec/effects/outbox NAHI
$b = $evBase.Split('|'); $a = $now[0].Split('|')
foreach ($i in 1,2,3,4,5,6,7,8) {
  if ($a[$i] -ne $b[$i]) { throw "EVIDENCE DB DELTA at field $i : baseline=$($b[$i]) now=$($a[$i]). A process ran against relay (P-28/P-36)" }
}
'evidence_delta=0'
if ($now[1] -ne 'job136|136|running|1|1') { throw "Job 136 moved: $($now[1]). The P-36 loop ran on the evidence DB — count the iterations and write them down" }
'job136_untouched=True'

docker compose exec -T db psql -X -Atq -U postgres -d postgres -c "drop database if exists relay_w4_witness" | Out-Null
$pd = @(("select concat_ws('|','probe_dbs', count(*)) from pg_database where datname like 'relay_w4%';" |
  docker compose exec -T db psql -X -Atq -U postgres -d postgres)) | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
$pd
if ($pd[0] -ne 'probe_dbs|0') { throw "Disposable DB survived: $($pd[0]) — Din 5 ki naming collide karegi" }

Get-ChildItem .\logs\w4d4_*.log | Select-Object Name, Length, LastWriteTime
git status --porcelain=v1 -- src alembic
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Evidence DB ka delta `0`, asserted** | `evidence_delta=0` — aath field ka field-by-field compare | Kal C5b ne pandrah quantity print ki aur do assert ki. Aaj ye `throw` hai. **Delta non-zero → kisi ek process ka `DATABASE_URL` galat gaya**, aur pre-flight uske baad bhi chala tha |
| **Job `136` hila nahi** | `job136\|136\|running\|1\|1` | `attempts > 1` → reaper evidence DB pe chala aur `P-36` ka loop wahan shuru ho gaya. Usko band karo aur **iteration ginti** likho — wo data hai |
| Witness bench **`DROP` se pehle** liya gaya | `witness_close` line | Baad me → aaj ka saara evidence chala gaya (`P-29`) |
| Queue ka state record hua | `queue\|…` witness DB pe — `record only`, kyunki witness DB drop ho rahi hai | Evidence DB pe ye assert hai (C0 aur upar ka delta check) |
| Koi disposable DB nahi bachi | `probe_dbs\|0` | Non-zero → Din 5 collide karega |
| Frozen predictions immutable | hash unchanged | Hash badla → `seal broken` |
| `logs/` ka evidence disk pe | `w4d4_*.log`, non-zero length | Missing → ordering proof gaya (`P-29`). `.gitignore` me `*.log` aur `logs/` dono hain |

---

# Part D — Scope guard: aaj **nahi**

| Kya | Owner | Aaj karne se kya khota hai |
|---|---|---|
| **Dispatcher ka backoff aur bound** (`next_attempt_at` on `outbox`, outbox DLQ) | **Month 2**, `Cost` line Din 6 pe | `P-35` ke do measured numbers (`8` attempts / `~20 s`, `7/7` vs `0`) aaj interleaving table me **evidence** ban rahe hain. Aaj fix kar dene se `D-27` ka `Cost` ek imaginary number pe likha jaayega |
| **`MAX_ATTEMPTS` ko claim gate me daalna** | **Month 2**; Week 2 Din 6 ne ye already price kiya aur declined kiya | Ye ek **paanchvaan** `status` writer hai aur uske saath ek sweep chahiye. Aur `P-36` ka poora point ye hai ki bound ka *location* galat hai — usko aaj hilana Din 6 ke argument ko chura lena hai |
| Job `136` ko haath se terminal karna | **kabhi nahi** | `P-05`. Aur wo Din 6 ke close pe ek naam wali carried row hai, jiska mechanism `P-36` me likha hai |
| `LISTEN`/`NOTIFY`, leader election, dispatcher coordination | `D-29` me **likha** jaata hai, banaya nahi | Kal ka `P9` `[MEASURED-R]` already bata chuka hai ki *"bahar"* shape me do dispatcher ek row do baar deliver karte hain. Aaj ka kaam usko **dikhana** hai |
| Pool `2` pe, Locust, `10k` rows, `/healthz` | **Din 5**, disposable DB pe | Aaj paanch engine chal rahe hain (`pool_size=5, max_overflow=10` → `15` connections **per engine**). Aaj pool chhota karna do variable ek saath hilaana hai (AGENTS rule 7) |
| `echo=True` band karna | **Din 5**, aur wahan wo ek naam wala variable hai | Week 2 me `2.3 ms` per statement measure hua tha. Aur aaj `echo` hi wo **in-process clock** hai jo `P-22` ka amendment maangta hai — usko aaj band karna aaj ka timing evidence le jaayega |
| Hypothesis ke naye strategies / Layer A badalna | **kabhi nahi, iss hafte** | Week 3 ka Layer A pass hai. Usko badal diya to Layer A vs Layer B ka comparison — jo aaj ka poora point hai — khatam |
| Lease `30 s`, heartbeat `10 s`, poll `2.0 s`, backoff numbers, `MAX_ATTEMPTS`, `effect_key` badalna | **kabhi nahi, iss hafte** | Week 2–4 ke saare measurements inhi numbers pe khade hain |
| Naya handler `src/` me (`pg_sleep` wala, `super_slow`) | — | Faisla 4 ka poora sawaal ye hai ki interleaving ka trigger production me exist karta hai ya nahi. Ek naya handler likhne ka matlab hai production path badal ke usko measure karna |
| `sink_deliveries.body` ko kisi endpoint pe expose karna | **auth ke baad** | `D-03`. Wo ek naya exposure surface hai aur usme delivery payload hai |
| `DDIA_CH8_LINKS.md` lines 10–13 | **Din 6** | Teesra carry. Aaj reading Hypothesis ke stateful-testing docs hai — model aur real system ko compare karna, jo aaj ka subject hai |
| README, blog post, `D-26`–`D-29` ki entries | **Din 6**, aur Din 6 kaata nahi ja sakta | Aaj ka witness `D-26` ka `Cost` field **feed** karta hai. Entry aaj likhna Din 6 se uska sabse bada input chura lena hai |
