# Week 4 Din 3 BRIEF — transactional outbox aur dispatcher: ek `COMMIT`, do intents, aur ek delivery jo do baar ho sakti hai

**Week 4 · Din 3** · Plan: [`../../planning/WEEK_04.md`](../../planning/WEEK_04.md) ·
Log: [`../../logs/WEEK_04.md`](../../logs/WEEK_04.md) · Sealed: [`DIN_03_KEY.md`](DIN_03_KEY.md) ·
Kal: [`DIN_02_BRIEF.md`](DIN_02_BRIEF.md)

**Goal:** local effect ke saath **usi transaction me** ek `outbox` row likho, ek alag process se usko bahar
bhejo, aur **delivery count** aur **effect count** ko pehli baar **alag-alag** naapo.

**Architectural invariant (aaj ke baad):**
> Local effect aur uske delivery ka **intent** ek hi `COMMIT` me hain — ya dono hain, ya dono nahi.
> **Delivery khud at-least-once hai**, aur uska exactly-once **receiver ki** idempotency key se aata hai,
> hamare dispatcher se nahi. `SKIP LOCKED` delivery ko exactly-once **nahi** banata; wo ek lock hai, lease nahi.

**Deliverable:** `outbox` migration · `src/sink.py` (receiver + `sink_deliveries`, dedup ek switch ke peeche) ·
`src/dispatcher.py` · ek reusable `crash_at` hook jo **iss baar commit me rehta hai** · aur **do measured
numbers ek hi job pe**: receiver ke access log me `2` requests, `sink_deliveries` me `1` row.

**Budget:** `20 + 15 + 25 + 25 + 30 + 35 = 150 min`. Plan me `130` hai; wo Step 0 ke bina hai, aur aaj Step 0
me **teen carried rows drain karni hain** jo `45 s` blocking payload wali hain — wo akela `~2.5 min` wall clock
hai plus setup. **Cut order, agar khinche:** Step 5 ka **Run C** (do dispatcher) kata ja sakta hai aur uska
owner Din 4 hai. **Run A aur Run B kabhi nahi kat sakte** — Run B ke bina Run A ka `1` kisi cheez ka evidence
nahi hai (`P-18`).

---

## Rules — ye teen roz wahi hain

> **Paste rule:** Part A, Part C, Part D Gemini ko ja sakte hain. **Part B kabhi nahi. KEY kabhi nahi.**
>
> **Seal rule:** paanchon answers **Step 0 me** freeze honge, Step 1 shuru hone se pehle. Har KEY section
> tabhi khulta hai jab uss step ka **measurement** ho chuka ho. Output prediction se alag nikla to **pehle
> apni explanation likho**, phir Gemini ke saath uss output pe reason karo, phir KEY.
>
> **Provenance rule:** iss BRIEF ke saare numbers `[MEASURED-R 2026-09-07]` hain — BRIEF generate karte waqt
> ek disposable DB (`relay_w4d3_probe`, drop ho gayi) pe actually chalaye gaye. Jo tum chalao wo `[MEASURED]`.

### Kal ka fail hua beat, aur ye aaj ka pehla kaam hai

`[MEASURED-R]` Kal `DIN_02_ANSWERS.md` ka SHA-256 `DIN_02_PREDICTIONS_FROZEN.md` ke **barabar** tha. Matlab
`### Observed + meri explanation` aur `### After KEY` **poore din khaali** rahe, aur paanchon predictions `idk`
thin → score `0.0/5.0`.

Implementation kal strong thi. Learning loop khaali tha. **Aaj Step 0 ka pehla item Din 2 ke wo blocks bharna
hai** — KEY already khul chuki hai, to isse kisi seal ko nuksaan nahi hai, aur bina iske kal ke chaar
measurements (`4.978 s`, `42.068 s`, `7 dispatches → 1 effect`, `conflict` vs `fenced`) recall me nahi
jaayenge, sirf log me padi rahengi.

### Read order — isko literally follow karo

1. Sirf **Step 0** padho (`0A`–`0E`).
2. Editor outline se seedha **Part B** pe jao. Step 1–5 aur Part C abhi mat kholo.
3. Paanch predictions likho (`idk` valid hai aur `0` score karta hai), phir Step 0 ke seal command pe wapas aao.
4. Frozen hash print hone ke baad **C0** kholo. C0 pass ho tab Step 1 aur baaki Part A/Part C khulte hain.

---

## Kal ka sach — teen cheezein aaj ka kaam badalti hain

`[MEASURED-R 2026-09-07]`:

| Kya | Actual | Aaj ka asar |
|---|---|---|
| **`src/reaper.py` uncommitted hai** | `HEAD = 52f9ab3` (Din 2). `src/reaper.py` **modified** — reviewer ne uski reclaim line ko `[reclaim] job_id=… pre_generation=… post_generation=…` banaya | Step 0A: usko **apne** commit me daalo, Din 3 ke code se pehle. Warna `git bisect` ek log-format change ko outbox feature me mila dega — Din 1 ki wahi galti |
| **Teen `pending` rows carried hain** | `132:pending:7:7`, `133:pending:5:5`, `134:pending:0:0` — teeno `effect` / `{"seconds": 45, "block": true}` | Step 0D. Reaper **band** rakhke drain karo, warna teeno anant loop me ghoomengi aur aaj ka outbox delta kachra ho jaayega. **`UPDATE`/`DELETE` se nahi** (`P-05`) |
| **`crash_at` / `os._exit` `src/` me exist hi nahi karta** | `grep 'crash_at|os\._exit' src/*.py` → **`0` matches** | Plan kehta hai *"Week 3 Din 3 ka mechanism reuse karo"*. **Wo mechanism kisi commit me nahi bacha** (`P-23`/`P-29`). Aaj usko dobara likhna hai, aur iss baar wo **commit me jaayega** — ek `payload` flag ke peeche, temporary diff ke roop me nahi |
| Bench | `relay|128|134|134|137|144|14|31|w4d2_completion_instruments` | C0 ka fingerprint |
| Buckets | `succeeded 105 | failed 15 | pending 3 | dead_letter 5 | running 0` → `128` | `pending` `3` hai — Step 0D ka subject |
| `side_effects` ka key state | `effnull|3|11|14` — **`3` legacy rows ka `effect_key` `NULL` hai** | Step 3 ka receiver-key faisla iss number ke against likha jaata hai, `[INFERRED]` ke against nahi |
| `outbox` / `sink_deliveries` | `tables|0` — dono exist nahi karte | C0 ka before/after compare isi pe khada hai |
| `jobs` heap pages | `2|0` | Din 2 ka baseline. Aaj `outbox` ka apna page count alag se record hota hai |
| PostgreSQL | `16.14`, `block_size 8192`, `max_connections 100`, `read committed`, `synchronous_commit on` | Aaj ke saare lock/visibility sawaal `read committed` pe khade hain |
| Deps | `httpx 0.28.1`, `fastapi 0.141.1`, `uvicorn 0.52.1` maujood. `requests` **nahi** | Receiver FastAPI se, client `httpx.AsyncClient` se. Kuch install nahi karna |

### Ek measured fact jo Step 4 ka faisla badal deta hai

`[MEASURED-R 2026-09-07]` **`httpx` ka default timeout `5.0 s` hai, infinite nahi:**

```text
httpx.__version__            = 0.28.1
httpx.AsyncClient().timeout  = Timeout(timeout=5.0)
connect to a closed port     = ConnectError after 2.650 s
```

Iska matlab: *"receiver `30 s` ke liye hang karta hai"* wala scenario, `httpx` ke defaults pe, **`30 s` ka nahi
hai — `5 s` ka hai.** Agar tum Step 5 me ek `30 s` hang naapna chahte ho, timeout **explicitly** badalna
padega, aur wo ek naam wala faisla hai — chup-chaap default pe chhod dena Q5 ka jawab hi badal deta hai.
Ye `[INFERRED]` nahi hai aur ye ek prediction bhi nahi hai; ye ek library default hai jo tumhare experiment
ka boundary set karta hai.

---

# Part A — Steps

## Step 0 — 20 min: Din 2 ka reflection band karo, commit, bench, freeze, aur teen carried rows drain

**Terms used in this step**
- **Evidence DB:** `relay` — chaar hafte ka permanent record. Rows `DELETE` nahi hoti, sequence reset nahi hota (`P-05`).
- **Opening bench:** pehli database read. Kal ke close se match karni chahiye; na kare to Din 3 rukta hai (`E2`).
- **Frozen prediction:** answer ki immutable copy + SHA-256, measurement se pehle.
- **Carried row:** ek `pending` row jo pichhle din se bachi hai. Uska `attempts` bound se bada ho sakta hai (`P-27`); wo normal hai aur usko theek nahi karna.
- **`[reclaim]` line:** reaper ki nayi log line. `pre_generation`/`post_generation` **barabar** hote hain — reaper generation nahi badhata. Aaj ye tumhare kaam aayega jab dispatcher ki lifecycle line ka format decide karoge.
- **Drain with the reaper off:** ek `45 s` handler `30 s` lease se lamba hai. Reaper live rakhne pe wo row reclaim ho jaayegi aur mark reject hoga (kal ka Run 2). Reaper band = mark accept.

### 0A — Din 2 ke ANSWERS bharo, phir commit (aur ye order hi point hai)

1. `docs\daily\week_04\DIN_02_ANSWERS.md` kholo. Paanchon `### Observed + meri explanation` blocks bharo —
   kal ke log (`docs/logs/WEEK_04.md`, Din 2 section) se numbers lo, aur **apne shabdon me** likho ki
   prediction (`idk`) aur observation me kya farq tha. Phir `### After KEY` bharo.
2. Uske neeche ek line: `SCORE: 0.0/5.0 (five idk, frozen-only rubric)`. **Chat me nahi, file me.**
3. `DIN_02_PREDICTIONS_FROZEN.md` ko **chhoona nahi**. Wo immutable hai; ANSWERS badalta hai.

```powershell
git add src/reaper.py
git status --short
git commit -m "fix(reaper): make the reclaim line greppable by job_id and log pre/post claim_generation"
git rev-parse --short HEAD
```

`docs/` **alag commit** me jaata hai (content vs provenance, Week 3 ka established pattern). `git add` naam se
karo, `git add .` se nahi.

### 0B — logs folder aur environment

```powershell
New-Item -ItemType Directory -Path .\logs -Force | Out-Null
$env:PYTHONUNBUFFERED = "1"
$env:DATABASE_URL     = 'postgresql+asyncpg://postgres:relay@localhost:5433/relay'
```

### 0C — predictions likho aur freeze karo

1. `docs\daily\week_04\DIN_03_ANSWERS.md` banao. Part B ke paanch sawaal **exactly** copy karo. Structure:
   `## Q1` … `## Q5`, har ek ke neeche exactly `### Prediction`, `### Observed + meri explanation`, `### After KEY`.
2. `### Prediction` non-empty (`idk` valid). Baaki do blocks freeze ke waqt **khaali**.
3. Phir neeche ka seal command **usi PowerShell terminal** me chalao (C5 usi variable ko dobara maangega).

```powershell
$answers = 'docs\daily\week_04\DIN_03_ANSWERS.md'
$frozen  = 'docs\daily\week_04\DIN_03_PREDICTIONS_FROZEN.md'
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

# Din 2 ka reflection actually hua ya nahi — ye aaj ka gate hai, reminder nahi
$d2 = (Get-Content 'docs\daily\week_04\DIN_02_ANSWERS.md' -Raw) -replace "`r`n","`n"
$d2Frozen = (Get-FileHash 'docs\daily\week_04\DIN_02_PREDICTIONS_FROZEN.md' -Algorithm SHA256).Hash
if ((Get-FileHash 'docs\daily\week_04\DIN_02_ANSWERS.md' -Algorithm SHA256).Hash -eq $d2Frozen) {
  throw 'DIN_02_ANSWERS.md is still byte-identical to its frozen copy: Din 2 reflection (Step 0A) not done'
}
if ($d2 -notmatch '(?im)^SCORE:\s*0\.0/5\.0') { throw 'DIN_02_ANSWERS.md has no SCORE line' }
'din2_reflection=done'

Copy-Item $answers $frozen
$d3FrozenHash = (Get-FileHash $frozen -Algorithm SHA256).Hash
$d3FrozenTime = (Get-Item $frozen).LastWriteTimeUtc.ToString('o')
"D3_FROZEN_SHA256=$d3FrozenHash"
"D3_FROZEN_MTIME_UTC=$d3FrozenTime"
```

Dono lines log me chipka do. Ab **C0** kholo aur chalao.

### 0D — teen carried rows ka drain: reaper band, ek worker, `~2.5 min`

`132`, `133`, `134` — teeno `effect` / `{"seconds": 45, "block": true}`. Reaper **band**, ek worker.
Har row: claim → `45 s` block → lease expire hoti hai par koi reclaim nahi → mark `rowcount=1` → `succeeded`.

```powershell
.\.venv\Scripts\python.exe -u -m src.worker *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d3_step0_drain_worker.log
```

Teesri `Marked job 134 as 'succeeded'` line ke baad `Ctrl+C`, phir **C0D**. Iska delta Din 3 ke experiments ke
delta me **nahi** judta — log me alag heading, `job_id <= 134` filter ke saath.

**`attempts` `8` aur `6` hoga aur wo theek hai** (`P-27`, `D-23` me accepted). Usko "theek" karne ki koshish
mat karo.

**Agar koi row `succeeded` nahi hoti** (mark `Conflict` deta hai): matlab reaper kahin chal raha tha.
`Get-CimInstance` se dhoondho, band karo, log me likho, phir dobara. **Hand-write tab bhi nahi.**

### 0E — kal ka `[reclaim]` line ek baar aankh se dekh lo

Aaj tum ek **teesra** process likh rahe ho jo `jobs`/`outbox` ki lifecycle me likhta hai. Kal ka `P-32` exactly
ye tha: ek lifecycle contract jiske do producer the aur verification ek ko dekhti thi. Aaj wo teen ho jaate hain.

```powershell
Select-String -Path .\logs\w4d3_step0_drain_worker.log -Pattern '\[claim\]|\[mark\]' | Select-Object -First 2 | ForEach-Object { $_.Line }
```

Dispatcher ki har line **usi shape** me hogi: `[<event>] … job_id=<n> outbox_id=<n> …`. Ye faisla abhi le lo,
code likhne ke baad nahi.

**Executable end:** `DIN_02_ANSWERS.md` bhara hua + `SCORE` line; `git rev-parse --short HEAD` naye commit pe;
printed frozen hash + mtime; C0 ka exact tuple screen pe; `132`/`133`/`134` `succeeded`; C0D pass; `pending 0`
aur `running 0`.

**KEY:** closed. Bench aur drain kisi Part B sawaal ka jawab nahi kholte.

---

## Step 1 — 15 min: ek effect naam se likho jo `COMMIT` me **aa hi nahi sakta**

Aaj koi code nahi. Ek file: `docs\daily\week_04\DIN_03_DESIGN.md`. **Chaar** H2 headings, har ek me exactly
teen labelled lines: `Chosen:`, `Rejected:`, `Cost:`. C1 ise mechanically padhta hai.

Pehli heading iss step ki hai; Faisla 2/3/4 Step 2/3/4 me aate hain.

**Terms used in this step**
- **Two-phase commit (2PC) / XA:** ek protocol jisme do resource manager (DB aur, kahin, ek mail server) ek coordinator ke neeche `PREPARE` aur `COMMIT` karte hain. PostgreSQL ka `PREPARE TRANSACTION` iska ek half hai.
- **Transactional participant:** wo cheez jiska rollback DB ke rollback ke saath ho sakta hai. Ek `INSERT` participant hai; ek `POST /charge` nahi hai (uska "rollback" ek doosri API call hai, jo khud fail ho sakti hai).
- **`ON COMMIT` trigger / `LISTEN`/`NOTIFY`:** PostgreSQL `NOTIFY` ko commit tak hold karta hai. Wo "commit ke baad kuch karo" ka ek in-DB mechanism hai — aur uska delivery **at-most-once** hai (koi listener nahi = message gaya).
- **At-least-once vs at-most-once vs exactly-once:** teen delivery guarantee. Network pe pehli do implementable hain; teesri ek **receiver-side property** hai jo pehli ke upar banti hai, ek delivery mechanism nahi.
- **Dual write:** ek hi logical operation ke do writes do systems me, bina ek atomic boundary ke. Yahi wo cheez hai jise outbox hataata hai.

### Faisla 1 — outbox kaunsi problem solve karta hai, aur kaunsi nahi

Ek paragraph likho: *PostgreSQL ke `COMMIT` me kya participate kar sakta hai aur kya nahi, aur `sendmail` /
`POST /charge` uss list ke kis taraf hai.* Phir usse ek line nikalo.

Teen options, aur teeno ko naam se maarna/chunna hai:

| Option | Kya deta hai | Kya nahi deta |
|---|---|---|
| **Dual write** — handler DB likhta hai, phir HTTP call karta hai | Simple, ek process | Do failure windows: DB likha + HTTP fail (intent gaya), ya HTTP hua + DB fail (effect bahar, record andar nahi) |
| **2PC / XA** | Ek atomic boundary do systems pe | Coordinator chahiye, HTTP endpoints XA bolte hi nahi, aur coordinator ka crash ek naya blocked-transaction problem hai |
| **Outbox** (chosen) | Effect aur delivery **intent** ek `COMMIT` me | **Delivery** ko atomic nahi banata. Delivery at-least-once rehti hai, aur duplicate ko rokna **receiver** ka kaam hai |

**Aur ek line jo likhni zaroori hai kyunki wahi aaj ka poora point hai:**

> Outbox *dual write* ko hataata hai. Wo *duplicate delivery* ko **nahi** hataata — wo usko ek jagah se
> doosri jagah shift karta hai, jahan use ek `UNIQUE` se roka ja sakta hai.

`narrows`, `closes` nahi. Agar tumhari file me *"outbox exactly-once delivery deta hai"* likha hai, wo line
galat hai aur C1 usko structurally pass kar dega — reviewer usko nahi karega.

**Executable end:** `DIN_03_DESIGN.md` disk pe pehli heading ke saath; C1 abhi **nahi** chalega (usko chaar
headings chahiye), to Step 1 ka end sirf file ka existence hai. C1 Step 4 ke baad chalta hai.

**KEY:** C1 Step 4 ke baad chalta hai, to Step 1 pe KEY **closed** rehti hai.

---

## Step 2 — 25 min: `outbox` table ka shape — teen sub-faisle, ek migration

**Terms used in this step**
- **`dispatched_at timestamptz NULL`:** ek nullable timestamp jo do baat ek column me kehta hai — *kab bheja* aur *bheja kya*. `P-19` ka shape.
- **Payload snapshot:** delivery ka body outbox row me copy karna, bajaye dispatcher ke `jobs` se padhne ke. Snapshot immutable hai; read-through fresh hai.
- **`jsonb` ka `attstorage`:** `x` (EXTENDED) — compress pehle, out of line baad me. Kal ka `TOAST_TUPLE_THRESHOLD = 2032` wala mechanism yahan bhi lagta hai.
- **Append-only instrument table:** `job_executions` ka pattern (`D-21`) — rows rehti hain, evidence banti hai, table badhta hai.
- **Fast default:** PostgreSQL 11+ me `ADD COLUMN … DEFAULT <constant>` rewrite nahi karta. Aaj naya **table** ban raha hai, to ye path lagta hi nahi.

### 2A — teen sub-faisle, `DIN_03_DESIGN.md` ki doosri heading me

| Sub-faisla | Options | Kya tolna hai |
|---|---|---|
| Pending ka representation | `dispatched_at IS NULL` **vs** apna `status` column | `status` column matlab ek doosra state machine aur `D-06` ka poora `CHECK` argument dobara. `dispatched_at IS NULL` ek column me do baat kehta hai (`P-19`) |
| Row ka payload | `job_id` + `effect_key` sirf (dispatcher `jobs` se padhega) **vs** poora payload snapshot | Snapshot immutable hai aur delivery ko job row se decouple karta hai. Par duplicate storage aur `jsonb` ka page cost |
| Retention | dispatch ke baad row rehti hai **vs** `DELETE` | Rehne se evidence banta hai (`D-21` ka precedent) aur table badhta hai. `DELETE` se dispatcher ka `SELECT` chhota rehta hai aur evidence jaata hai |

**Ek cheez jo faisla nahi hai:** `outbox` insert aur `side_effects` insert **ek hi session, ek hi `COMMIT`**.
Do transactions me hue to aaj ka poora din bekaar hai, aur C2 usko pakadta hai.

**Aur ek cheez jo kal ka measured data decide kar deta hai:** `side_effects.effect_key` **nullable** hai aur
evidence DB me `3` rows ka key `NULL` hai (`effnull|3|11|14`, `[MEASURED-R]`). `UNIQUE` `NULL`s ko distinct
maanta hai — `[MEASURED-R 2026-09-07]` ek `UNIQUE` column me teen `NULL` bina complaint ke ghus gaye. Matlab
receiver pe key nullable rakhne se **dedup un rows ke liye chup-chaap band** ho jaata hai. Isliye
`sink_deliveries.idempotency_key` **`NOT NULL`** hona chahiye, aur uska seedha nateeja Step 3 ka sawaal hai.

### 2B — migration

Ek revision, `down_revision = 'w4d2_completion_instruments'`:

```powershell
.\.venv\Scripts\python.exe -m alembic revision -m "add outbox table" --rev-id w4d3_outbox
```

Shape ki suggestion (Python tumhari):

| Column | Kyu |
|---|---|
| `id bigserial PK` | `D-21` ka pattern |
| `job_id bigint NOT NULL` | grep aur join ke liye. FK **nahi** — `D-21` ka precedent |
| `effect_key text` | nullable ya `NOT NULL`? **Ye tumhara faisla hai**, aur upar ka `effnull|3` uska data hai |
| `payload jsonb` ya kuch nahi | Sub-faisla 2 |
| `dispatched_at timestamptz NULL` | Sub-faisla 1 |
| `attempts integer NOT NULL DEFAULT 0` | Dispatcher ka retry counting (`D-23` ke numbers **reuse**, naye invent nahi) |
| `created_at timestamptz NOT NULL DEFAULT now()` | `D-08` ke saath consistent, aur per-day chain ke liye zaroori |
| `last_error text NULL` | Kal ka precedent. **Ya nahi** — likho kyun |

`downgrade()` **likha jaata hai** aur disposable DB pe chalaya jaata hai (`upgrade head` → `downgrade -1` →
`upgrade head`). `alembic heads` iske baad **exactly ek** line.

**`P-28` ka guard, kal se copy hota hai, dobara invent nahi hota:** `alembic.ini` line 89 pe `sqlalchemy.url`
**hardcoded** hai; `$env:DATABASE_URL` Alembic ke liye **exist hi nahi karta**. Disposable DB ka ek hi safe
raasta: ini ki ek **copy**, uski `sqlalchemy.url` badli hui, aur `alembic -c <copy>`.

### 2C — handler ka change: ek session, do inserts

`handle_effect` aaj `side_effects` ka insert apne `async_session()` me karta hai. Aaj usme **ek doosra insert
usi `session.begin()` block me** aata hai. **Ready-made code iss BRIEF me nahi hai.**

Ek trap jo naam se likhna hai: `ON CONFLICT DO NOTHING` `rowcount=0` de sakta hai (dedup hit). **Uss case me
outbox row likhni chahiye ya nahi?** Do jawab, dono defensible, aur ek naam se chunna hai:

- **Nahi likho:** dedup ka matlab "ye effect pehle ho chuka", to delivery bhi ho chuki hogi. Cost: agar pehli
  baar effect likha gaya par outbox row kisi wajah se dispatch nahi hui, ye branch usko **kabhi** repair nahi karega.
- **Likho:** delivery intent har dispatch pe refresh hota hai. Cost: ek job jo `7` baar dispatch hui (kal ka
  `132`) `7` outbox rows banayegi, aur `7` deliveries — receiver unhe dedup karega, par network traffic real hai.

`[MEASURED-R 2026-09-07]` Kal ke run me job `132` ne **`7`** dispatches liye. Ye number iss faisle ka data hai,
`[INFERRED]` nahi. Ye Part B **Q1** ka padosi hai — sawaal ka jawab nahi, par uska maidan.

**Lease `30 s`, heartbeat `10 s`, poll `2.0 s`, backoff, `MAX_ATTEMPTS = 3`, `effect_key` — aaj kuch nahi badalta.**

**Executable end:** `alembic heads` ek line; disposable lifecycle pass (`head` → `down` → `reup`); evidence DB
upgraded; `pytest tests -q` chala aur **exit code check hua**; ek job chali aur `1 side_effect + 1 outbox` di;
C2 pass.

**KEY:** C2 pass hone ke baad → **"Open after Step 2 / C2 — Q1"**.

---

## Step 3 — 25 min: receiver — ek sink jiske paas apni idempotency hai, aur ek switch

**Terms used in this step**
- **Receiver / sink:** ek alag process, alag port. Relay ka hissa nahi — wo *"bahar"* hai, aur wahi uska poora point hai.
- **`sink_deliveries`:** receiver ki apni table. `idempotency_key text NOT NULL UNIQUE`, `received_at`, `body jsonb`.
- **`applied` vs `duplicate`:** receiver ka response jo **naam se** batata hai ki row insert hui ya conflict hua. Ye `rowcount` se aata hai, guess se nahi.
- **Dedup switch:** ek env var ya query flag jisse receiver ka `ON CONFLICT` band ho jaaye. Iske bina Run A ka `1` kisi cheez ka evidence nahi (`P-18`).
- **Access log:** kitni **requests** aayin. Ye `sink_deliveries` ke row count se **alag number** hai, aur aaj ka poora din inhi do numbers ke farq pe khada hai.

### Aaj ka minimum

`src/sink.py` — ek FastAPI app, ek `POST /deliver`, `uvicorn` se `8001` pe. Uski table Relay ki hi PostgreSQL
me reh sakti hai (alag DB banane ka koi measurement value aaj nahi hai) — par **naam se likho** ki wo
conceptually receiver ki table hai, Relay ki nahi.

Do cheezein jo response me hona zaroori hain: `{"result": "applied"|"duplicate", "idempotency_key": "..."}`,
aur **har** request ek access log line jo `[deliver] idempotency_key=… result=… ` shape me ho.

### Faisla 3 — idempotency key kaun mint karta hai

`DIN_03_DESIGN.md` ki teesri heading:

| Option | Kya deta hai | Kya todta hai |
|---|---|---|
| **Dispatcher mint karta hai** (per delivery attempt, e.g. a UUID) | Har attempt ka apna audit trail | Dedup ka koi kaam nahi bachta — do attempts ki do keys hain, to `UNIQUE` kabhi fire nahi karta. Yahi Din 1 ka Q4 tha aur uska jawab `2` tha |
| **`effect_key` reuse hota hai** (`job:<id>`) | Ek logical effect = ek key. Dedup kaam karta hai | `effect_key` **nullable** hai aur `3` legacy rows ka `NULL` hai `[MEASURED-R]`. `NULL` key ke saath dispatcher kya kare — **skip** (Contract #1 ke against ek chhota hole) ya **synthetic key** (dedup ko meaningless karna)? Aur: ek `effect_key` kabhi do **alag** deliveries identify kar sakti hai ya nahi? |
| **Outbox row ka `id`** | Har outbox row ek key. `NOT NULL` free me | Agar Step 2C ne "dedup pe bhi outbox row likho" chuna, to `7` dispatches = `7` keys = `7` applied rows. Dedup phir bhi nahi fire karta |

**Ek chuno, likho, aur Run A/Run B usi pe chalengi.** Aur ek line likho: *ye key kis cheez ki identity hai —
effect ki, delivery attempt ki, ya outbox row ki?* Teen alag cheezein hain aur teeno ka `UNIQUE` teen alag
matlab rakhta hai.

**Executable end:** `uvicorn src.sink:app --port 8001` chalta hai; ek manual `POST` `applied` deta hai; wahi
`POST` dobara `duplicate` deta hai; dedup switch off karke wahi `POST` dobara `applied` deta hai aur
`sink_deliveries` me `2` rows aati hain. **Ye aakhri check hi switch ka proof hai.** C3 pass.

**KEY:** C3 pass hone ke baad → **"Open after Step 3 / C3 — Q3 ka receiver half"**.

---

## Step 4 — 30 min: `src/dispatcher.py` — aur aaj ka sabse bada faisla yahan hai

**Terms used in this step**
- **`FOR UPDATE SKIP LOCKED`:** ek row lock. Uski **lifetime transaction hai** — `COMMIT`/`ROLLBACK` pe wo chala jaata hai. Ye ek lease **nahi** hai; lease ek timestamp column hota hai jo transaction se bahar zinda rehta hai.
- **Lock lifetime vs delivery lifetime:** aaj ka central sawaal. HTTP call transaction ke andar hai to dono ek hain; bahar hai to lock delivery se pehle khatam ho jaata hai.
- **`idle in transaction`:** `pg_stat_activity.state` ka wo value jab ek backend ke paas open transaction hai aur wo client ka agla command wait kar raha hai. `[MEASURED-R]` `wait_event = Client/ClientRead`.
- **`crash_at`:** ek payload flag jo handler/dispatcher ko ek naam wale point pe `os._exit(<code>)` karwata hai. `os._exit` `finally`, `atexit`, aur pending `COMMIT` — **teeno** skip karta hai.
- **`os._exit(n)` vs `sys.exit(n)`:** `sys.exit` ek exception raise karta hai (so `finally` chalta hai); `os._exit` process ko turant maar deta hai.

### Faisla 4 — HTTP call transaction ke **andar** hai ya **bahar**, aur ye ek hi faisla hai do consequences ke saath

`[MEASURED-R 2026-09-07, disposable DB, PostgreSQL 16.14, read committed]` — dono shapes probe kiye gaye:

**Shape "bahar" (claim → `COMMIT` → HTTP → mark), do independent engines, ek hi row:**

```text
P9_picked   = {'A': [7], 'B': [7]}
P9_delivered= [('A', 7), ('B', 7)]
P9_same_row_delivered_twice = True
P9_final    = [(7, dispatched_at_is_null=False)]
```

**Dono dispatchers ne wahi row deliver ki.** `SKIP LOCKED` ne kuch nahi roka, kyunki uska lock uss ek
`SELECT` ke transaction ke saath khatam ho gaya — delivery uske baad hui. Aur final row **ek** `dispatched_at`
dikhati hai, to **row dekh ke ye pata nahi chalta** ki do deliveries hui thin (`P-29` ka shape).

**Shape "andar" (lock held across the call), ek rival dispatcher beech me, aur phir crash:**

```text
P8_holder_got             = [6]
P8_rival_during_hold      = []          <- rival ko kuch nahi mila, aur wo block bhi nahi hua
P8_holder_raised          = RuntimeError
P8_after_crash            = [(6, dispatched_at_is_null=True)]
P8_reclaimable_without_reaper = [6]
```

Aur ek chhota control `[MEASURED-R]`: ek hi undispatched row, do sessions →
`P6_one_row A=[4] B=[] B_blocked=False`. `SKIP LOCKED` **block nahi karta**, wo khaali haath bhejta hai.

| | **Andar** (lock held across the HTTP call) | **Bahar** (claim, commit, phir HTTP) |
|---|---|---|
| Do dispatcher, ek row | Rival ko kuch nahi milta `[MEASURED-R]` | **Dono deliver karte hain** `[MEASURED-R]` |
| Dispatcher crash | Rollback → row **turant** dobara claimable, `dispatched_at` still `NULL`, **koi lease/reaper nahi chahiye** `[MEASURED-R]` | Row "delivered but unmarked" hai aur usko dhoondhne ka koi mechanism nahi — ek lease + ek reaper chahiye |
| Pool | Network latency tak ek connection **aur** ek row lock blocked. `state = 'idle in transaction'`, `wait_event = Client/ClientRead` `[MEASURED-R]` | Connection turant free |
| Receiver hang | Ek backend `idle in transaction`, lock ke saath — aur uski duration `httpx` ke timeout se bandhi hai, jo default `5.0 s` hai `[MEASURED-R]`, `30 s` nahi | Koi DB resource nahi phansta |

**Aur ye plan me isliye hai ki "bahar" chunne ka matlab ek chhupa hua extra component hai:** Relay ka reaper
sirf `jobs` dekhta hai (`src/reaper.py`, `Job.status == "running"`); `outbox` ko koi nahi dekhta. *"Bahar"*
chuna to aaj ke din me ek aur loop add ho jaayega, aur wo scope se bahar hai — ya lease-free design chunna
padega. **Ye faisla likhne se pehle lo, code likhne ke baad nahi.**

### Do aur cheezein jo aaj naam se decide honi hain

1. **Mark fail ho gaya to?** Delivery ho chuki hai, `dispatched_at` nahi likha. **Yahi wo crash seam hai jo
   aaj ka measurement hai** — ise "handle" karne ki koshish aaj **nahi** karni, ise **dikhana** hai.
2. **Dispatcher ka retry/backoff:** receiver down hai to? Aaj ka minimum — `attempts` count karo aur `D-23`
   ke numbers (`base 5.0 s`, `×2`, cap `15.0 s`, equal jitter) **reuse** karo. Naye numbers invent mat karo
   (AGENTS rule 7: ek din me ek variable).

### `crash_at` — aaj likho, aur iss baar commit me rakho

`[MEASURED-R 2026-09-07]` `grep 'crash_at|os\._exit' src/*.py` → **`0` matches.** Plan ka *"reuse"* nahi ho
sakta; wo mechanism kisi commit me nahi bacha (`P-23`).

Aaj do crash points chahiye, dono ek `payload`/env flag ke peeche, aur dono **committed code** me:

| Point | Kahan | Kya prove karta hai |
|---|---|---|
| `crash_at: "before_commit"` | handler me, dono inserts ke **baad**, `COMMIT` se **pehle** | Effect aur intent dono gayab hote hain — ya dono, ya koi nahi. Ye Q1 hai |
| `crash_at: "after_http"` (dispatcher-side flag) | HTTP `200` ke **baad**, `dispatched_at` mark se **pehle** | Delivery hui, mark nahi. Ye Q2/Q3 hai |

**Ye `src/` code hai, matlab tum likhoge. Aur ye temporary diff nahi hai** — flag default off hai, path naam
wala hai, aur wo `git log` me rehta hai. `P-23` ka pura point yahi tha.

**Executable end:** `python -m src.dispatcher` chalta hai; ek backlog row uthata hai; receiver ke access log me
ek line; `outbox.dispatched_at` non-null; `[dispatch]` line me `job_id=` **aur** `outbox_id=`; C4 pass (jo
`DIN_03_DESIGN.md` ka C1 bhi chalata hai — chaar headings ab exist karti hain).

**KEY:** C4 pass hone ke baad → **"Open after Step 4 / C1+C4 — Q2 aur Q5"**.

---

## Step 5 — 35 min: teen run, do numbers, ek job

**Terms used in this step**
- **Run A:** dedup **ON**, dispatcher `crash_at: after_http`. Delivery do baar jaati hai, receiver ek maanta hai.
- **Run B:** dedup **OFF**, wahi crash. Ye Run A ke `1` ko meaning deta hai.
- **Run C (cuttable):** do dispatcher ek hi backlog pe, koi crash nahi.
- **Negative control:** wo run jiska kaam fail karna hai. Run B negative control hai; uske bina Run A ek assertion hai, measurement nahi.

### Run A — dedup ON, crash after HTTP

Expected shape (aur ye assertion hai, prediction nahi):

- receiver ke access log me uss key ke liye **`2`** request lines,
- `sink_deliveries` me uss key ke liye **`1`** row, pehli `applied` doosri `duplicate`,
- `side_effects` me uss `job_id` ke liye **`1`** row,
- `outbox.dispatched_at` eventually non-`NULL`.

**Requests `1` aayin to dispatcher crash hua hi nahi**, aur `1` row dedup ka evidence nahi hai (`P-12`).
Wo case "test nahi hua" hai, "pass" nahi — aur log me wahi likhna hai.

### Run B — dedup OFF, wahi crash

Ek variable badalta hai: receiver ka switch. **Payload, job type, crash point, sab byte-for-byte same.**
Rows `2` aane chahiye. `1` aaya → switch ne kuch off nahi kiya, aur Run A ka `1` kisi aur cheez se aa raha tha.

### Run C — do dispatcher, ek backlog, koi crash (cuttable, owner Din 4)

Do `python -m src.dispatcher` ek hi backlog pe. Har outbox row **ek hi baar** delivered — ya nahi. Iska jawab
Faisla 4 pe depend karta hai, aur upar ka `P9` `[MEASURED-R]` batata hai ki *"bahar"* shape me wo jawab
**nahi** hai.

### Stop rule

Dispatcher aur worker dono loop hain. **Run A ke `dispatched_at` non-null hote hi C5 chalao, phir sab band
karo.** `outbox` ka row count aur `sink_deliveries` ka row count **snapshot time pe depend karte hain** —
teeno numbers ke saath UTC time likhna zaroori hai, warna compare karne layak nahi.

**Executable end:** paanch logs (`w4d3_step0_drain_worker.log`, `w4d3_runA_dispatcher.log`,
`w4d3_runA_sink.log`, `w4d3_runB_dispatcher.log`, `w4d3_runB_sink.log`; Run C ke do agar chala); Run A aur
Run B ke do-number table UTC time ke saath; C5 pass (closing bench, chain, cleanup).

**KEY:** C5 ke baad → **"Open after Step 5 / C5 — Q3 aur Q4"**. Uske baad **"Known traps"**, phir
**"Final scoring rubric"** kholo aur frozen text ko `/5` pe grade karo. Post-run prose ko credit nahi milta.

---

## Din close pe reviewer ko kya dena hai

Plan ka DOC-SYNC Din 3 ke liye: `logs/WEEK_04.md` · `PROBLEMS.md` · `DECISIONS.md` me **kuch nahi**
(`D-27` Din 6 ka hai aur uska `Cost` Din 4 ke witness ke bina likha nahi ja sakta) · **plus do carried items:**
`ddia_summaries/DDIA_CH11_LINKS.md` ka `D-24`/`D-25` re-anchor (kal slip hua) aur `P-32` ka **gate half**
(C3-style unstructured check teeno logs pe).

`P-` number chahiye to **uss din grep karo** (`E6`). `[MEASURED-R 2026-09-07]` aaj ka expected next-free
**`P-33`** hai (`PROBLEMS.md` ka last entry `P-32`), aur `D-` ka next-free **`D-26`** — par register hi sach hai.

Reviewer ko saat cheezein chahiye: `DIN_03_PREDICTIONS_FROZEN.md` + printed hash, bhara hua
`DIN_02_ANSWERS.md`, `DIN_03_DESIGN.md`, `src/sink.py` + `src/dispatcher.py`, saare `w4d3_*.log`, Run A/Run B
ka do-number table, aur C0–C5 ka raw output.

---

# Part B — Prediction questions — **Gemini ko paste mat karna**

> Step 0 me **paanchon** answer aur freeze karo, Step 1 shuru hone se pehle. `idk` valid hai aur `0` score
> karta hai. `idk — <sahi jawab>` bhi `0` hai. Inke jawab iss block me nahi hain, aur BRIEF me kahin nahi hain.
>
> Aur kal ka sabak: **`### Observed` block bharna prediction score ka hissa nahi hai, par wo iss poore protocol
> ka hissa hai.** Aaj usko Step 0 me nahi, uss step ke turant baad bharo.

```text
Q1. Handler side_effects row aur outbox row EK HI session me insert karta hai, phir COMMIT se PEHLE
    os._exit(1). DB me kitni rows hongi (dono tables), aur side_effects_id_seq / outbox_id_seq ka
    last_value kya hoga? Do cheezein alag likho: row count, aur sequence value.

Q2. Dispatcher HTTP 200 le chuka hai aur dispatched_at mark karne se pehle mar jaata hai. Reaper outbox
    ko nahi dekhta (src/reaper.py sirf Job.status == 'running' padhta hai). Wo row dobara KAB uthegi,
    aur usko dobara uthane wala mechanism KAUNSA hai? Agar koi mechanism nahi hai to wahi likho.

Q3. Receiver ka dedup OFF hai, wahi crash (HTTP 200 ke baad, mark se pehle). sink_deliveries me kitni
    rows, aur side_effects me kitni? Do numbers alag-alag likho, aur kyu.

Q4. Do dispatcher process ek hi backlog pe, SELECT ... FOR UPDATE SKIP LOCKED + WHERE dispatched_at IS
    NULL, READ COMMITTED. Ek row do baar deliver ho sakti hai ya nahi — aur agar haan, to exactly kis
    sequence me? (Sochne se pehle ye tay karo: HTTP call transaction ke ANDAR hai ya BAHAR — jawab
    dono ke liye alag hai, aur dono likho.)

Q5. HTTP call transaction ke ANDAR hai. Receiver 30 s ke liye respond nahi karta. Uss dauran uss
    dispatcher ke pool ka kya haal hai, aur pg_stat_activity me wo backend kis state me dikhega?
    Aur ek doosra hissa: wo "30 s" actually 30 s hoga ya nahi?
```

---

# Part C — Verification

Sab **PowerShell 7** syntax hai aur repo root `d:\PROJECTS\relay` se chalta hai. `docker compose` service ka
naam **`db`** hai. PostgreSQL **16.14**, port **5433**, `-U postgres -d relay`. Jahan `throw` hai wahan step
**rukta** hai — stray worker/dispatcher chala ke state "repair" mat karna. **`&&` kahin nahi hai; separator `;` hai.**

**Har check ke saath do column hain: mechanism maujood, aur mechanism ghayab. Jis check ka dono column same
output deta hai, wo check decorative hai (`P-18`).**

## C0 — Din 2 committed, Din 2 ka reflection done, opening bench, seal, single head

Seal command ke **usi terminal** me:

```powershell
if (-not $d3FrozenHash) { throw 'Step 0C hash variable missing; C0 must run in the same PowerShell terminal' }
$frozen = 'docs\daily\week_04\DIN_03_PREDICTIONS_FROZEN.md'
if ((Get-FileHash $frozen -Algorithm SHA256).Hash -ne $d3FrozenHash) { throw 'Frozen predictions changed after Step 0C' }
"D3_FROZEN_SHA256_UNCHANGED=$d3FrozenHash"

$dirty = @(git status --porcelain=v1 -- src alembic)
$dirty
if ($dirty.Count -ne 0) { throw "src/ or alembic/ is dirty before Din 3 starts. Step 0A pehle poora karo:`n$($dirty -join "`n")" }
$head = (git rev-parse --short HEAD).Trim()
"HEAD=$head"
if ($head -eq '52f9ab3') { throw 'HEAD is still the Din 2 commit; the reaper fix was not committed (Step 0A)' }
@(git log --oneline -3)

# the reaper fix must actually be in the tree, not just committed as an empty change
$rl = (Get-Content src\reaper.py -Raw)
if ($rl -notmatch '\[reclaim\] job_id=')      { throw 'src/reaper.py has no [reclaim] job_id= line; P-32 fix missing' }
if ($rl -notmatch 'post_generation')          { throw 'src/reaper.py does not log post_generation' }
'reaper_fix_present=True'

$env:DATABASE_URL = 'postgresql+asyncpg://postgres:relay@localhost:5433/relay'
$runtimeDb = (& .\.venv\Scripts\python.exe -c "from src.database import engine; print(engine.url.database)") -join ''
if ($runtimeDb.Trim() -ne 'relay') { throw "Runtime DB mismatch: $runtimeDb" }
"python_runtime_database=relay"

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
  (select last_value from job_executions_id_seq),
  (select count(*) from side_effects),
  (select last_value from side_effects_id_seq),
  (select version_num from alembic_version)) from jobs;
select concat_ws('|',
  count(*) filter (where status='succeeded'), count(*) filter (where status='failed'),
  count(*) filter (where status='pending'), count(*) filter (where status='dead_letter'),
  count(*) filter (where status='running'), count(*)) from jobs;
select coalesce(string_agg(id::text||':'||status||':'||attempts::text||':'||claim_generation::text, ',' order by id),'none')
  from jobs where status in ('running','pending');
select concat_ws('|','effnull', count(*) filter (where effect_key is null), count(effect_key), count(*)) from side_effects;
select concat_ws('|','newtables', count(*)) from information_schema.tables
  where table_schema='public' and table_name in ('outbox','sink_deliveries');
select concat_ws('|','idle_in_txn', count(*)) from pg_stat_activity
  where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select concat_ws('|','probe_dbs', count(*)) from pg_database where datname like 'relay_w4%';
select concat_ws('|','terminal_ts',
  count(*) filter (where status in ('succeeded','failed','dead_letter')),
  count(*) filter (where status in ('succeeded','failed','dead_letter') and completed_at is not null)) from jobs;
'@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'C0 SQL failed' }
$actual = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$actual
$expected = @(
  'relay|128|134|134|137|144|14|31|w4d2_completion_instruments',
  '105|15|3|5|0|128',
  '132:pending:7:7,133:pending:5:5,134:pending:0:0',
  'effnull|3|11|14',
  'newtables|0',
  'idle_in_txn|0',
  'probe_dbs|0',
  'terminal_ts|125|3'
)
if (($actual -join "`n") -ne ($expected -join "`n")) {
  throw "C0 fingerprint mismatch.`nACTUAL:`n$($actual -join "`n")`nEXPECTED:`n$($expected -join "`n")"
}
'C0=pass'

# C2/C5 hardcode nahi karenge — pre-migration counts yahan capture hote hain
$preJobs   = [int]($actual[0].Split('|')[1])
$preExec   = [int]($actual[0].Split('|')[4])
$preEff    = [int]($actual[0].Split('|')[6])
$preEffSeq = [int]($actual[0].Split('|')[7])
"PRE_JOBS=$preJobs  PRE_EXEC=$preExec  PRE_EFF=$preEff  PRE_EFFSEQ=$preEffSeq"
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Din 2 ka reaper fix commit me hai aur tree me hai** | `src`/`alembic` clean, `HEAD ≠ 52f9ab3`, `[reclaim] job_id=` aur `post_generation` source me | Dirty ya wahi `HEAD` → aaj ki migration ek uncommitted fix ke upar chadhegi. Aur sirf `git log` dekhna kaafi nahi: ek commit message *"fix reaper"* keh sakta hai jabki line wapas revert ho gayi ho — isliye source ka grep bhi hai |
| **Din 2 ka reflection actually hua** | `DIN_02_ANSWERS.md` ka hash frozen se **alag**, aur `SCORE:` line maujood (Step 0C ka gate) | Hash barabar → beats 4/5 phir skip hue, aur ye din bhi implementation-only ban jaayega. **Ye reminder nahi hai, ye `throw` hai** |
| Bench Din 2 close se match | poora `8`-line tuple | Koi bhi farq → **divergence**, Din 3 rukta hai jab tak cause naam se na mile (`E2`) |
| Carried rows ka **exact shape** | `132:pending:7:7,133:pending:5:5,134:pending:0:0` | Sirf count match karta par shape na hoti → Step 0D ka expected outcome guess ban jaata. Aur `attempts 7`/`5` ka `MAX_ATTEMPTS 3` se bada hona **expected** hai (`P-27`) |
| **`outbox`/`sink_deliveries` exist nahi karte** | `newtables|0` | Non-zero → migration pehle se chal chuki hai, aur Step 2 ka before/after compare khatam |
| **`effect_key` ka `NULL` count** | `effnull|3|11|14` | Ye Step 3 Faisla 3 ka data hai. Miss karne pe receiver ka key nullable reh jaata hai aur dedup un rows pe chup-chaap band |
| `completed_at` ki honest coverage | `terminal_ts|125|3` — `125` terminal rows, sirf `3` pe timestamp | Sab pe timestamp → kisi ne `122` purani rows ko backfill kar diya, aur Din 2 ka poora honesty argument gaya |
| Single head | ek `(head)` line | Do heads → branch ban gayi. Ye **teesri** consecutive migration hai |
| Koi process zinda nahi | `relay_processes=0` | Ek purana worker → wo carried rows utha lega aur attribution khatam (`P-13`) |
| Frozen predictions immutable | hash unchanged | Hash badla → uss sawaal ka score `seal broken` |

## C0D — teen carried rows ka drain, alag line me

```powershell
$sql = @'
select concat_ws('|','row', id, status, attempts, claim_generation,
  coalesce(completed_at::text,'NULL'), coalesce(next_attempt_at::text,'NULL'))
  from jobs where id in (132,133,134) order by id;
select concat_ws('|','buckets', count(*) filter (where status='pending'), count(*) filter (where status='running'))
  from jobs;
select concat_ws('|','eff', job_id, count(*)) from side_effects where job_id in (132,133,134) group by job_id order by job_id;
select concat_ws('|','totals', (select count(*) from jobs), (select count(*) from job_executions),
  (select count(*) from side_effects), (select last_value from side_effects_id_seq));
'@
$raw = @($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
$out = @($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
foreach ($i in 0..2) {
  $f = $out[$i].Split('|')
  if ($f[2] -ne 'succeeded') { throw "Carried row $($f[1]) is '$($f[2])', expected succeeded: $($out[$i])" }
  if ($f[5] -eq 'NULL')      { throw "Carried row $($f[1]) is terminal with completed_at NULL" }
}
if ($out[3] -ne 'buckets|0|0') { throw "Queue not drained: $($out[3])" }
if ($out[4] -ne 'eff|132|1') { throw "Job 132 effect count wrong: $($out[4]) — effect_key dedup toota" }
'C0D=pass'
```

Expected shape:

```text
row|132|succeeded|8|8|<ts>|NULL
row|133|succeeded|6|6|<ts>|NULL
row|134|succeeded|1|1|<ts>|NULL
buckets|0|0
eff|132|1
eff|133|1
eff|134|1
totals|128|140|15|<seq>
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Teeno terminal hue **aur** timestamp chhoda | `succeeded` + `completed_at` non-`NULL` teeno pe | `Conflict on mark` → reaper kahin chal raha tha, aur aaj ka baseline shift ho gaya. **Ek bhi row `pending` reh gayi to Din 3 ka outbox delta contaminated hai** |
| `attempts` bound se bada hai aur **wo theek hai** | `8`/`6`/`1` | Ye `P-27` ka evidence hai. Isko "fix" karna Month 2 ka scope hai (`D-23` accepted) |
| `side_effects` per job **`1`** | `eff|132|1` — `8` dispatches ke baad bhi | `2` → `effect_key` ka scope toota, aur wo Din 1 ka faisla hai |
| `jobs` count nahi badla | `128` | Badla → drain ke dauran koi enqueue hua |
| **Queue actually khaali** | `buckets|0|0` | Non-zero → aaj ka dispatcher ek purani row ka effect utha lega. **Ye check kal ke C5b me nahi tha, aur wahi `P-31` hai** |

## C1 — `DIN_03_DESIGN.md`, structural gate (Step 4 ke baad chalta hai)

```powershell
$design = 'docs\daily\week_04\DIN_03_DESIGN.md'
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
if ($text -notmatch '(?i)dual.?write')                  { throw 'Faisla 1 me dual write naam se nahi hai' }
if ($text -notmatch '(?i)2pc|two.?phase|XA')            { throw 'Faisla 1 ka maara hua option (2PC/XA) file me nahi hai' }
if ($text -notmatch '(?i)at.?least.?once')              { throw 'Faisla 1 me delivery guarantee ka naam nahi hai' }
if ($text -notmatch '(?i)receiver')                     { throw 'Faisla 1/3 me receiver-side idempotency ka naam nahi hai' }
if ($text -notmatch '(?i)null')                         { throw 'Faisla 3 me NULL key ka case (effnull|3) nahi hai' }
if ($text -notmatch '(?i)skip locked')                  { throw 'Faisla 4 me SKIP LOCKED ka naam nahi hai' }
if ($text -notmatch '(?i)idle in transaction|pool')     { throw 'Faisla 4 ka pool/lock-lifetime cost file me nahi hai' }
# aur ek negative check: outbox ko exactly-once kehna galat hai
if ($text -match '(?i)outbox\s+\w*\s*(gives|deta|provides|ensures)[^.\n]*exactly.?once') {
  throw 'File claims the outbox provides exactly-once delivery. It does not: narrows, not closes'
}
'C1=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Chaar faisle, chaaron ka rejected option | 4 sections × (`Chosen`/`Rejected`/`Cost`) | Sirf `Chosen` → wo faisla nahi, preference hai (AGENTS rule 28) |
| Dual write **aur** 2PC dono naam se maare/chune gaye | `dual write` + `2PC`/`XA` mention | Ek option → outbox ek naya table ban jaata hai jiska point kisi ko nahi pata |
| Delivery guarantee likhi hui | `at-least-once` + `receiver` | Missing → aaj ka Run A/Run B ka farq kis cheez ka evidence hai, ye kabhi answer nahi hoga |
| `NULL` key ka case | `null` mention | Missing → `3` legacy rows pe dedup chup-chaap band, aur wo `[MEASURED-R]` hai |
| Faisla 4 ka pool cost | `idle in transaction` ya `pool` | Missing → *"andar"* chunne ka asli cost likha hi nahi gaya, aur Din 5 ka `2`-connection pool usko dhoondhega |
| **Overclaim guard** | Regex `outbox … exactly-once` par `throw` | Ye ek **negative** gate hai. Ek structurally-perfect file jo galat baat kehti hai, pass nahi honi chahiye. Note: ye ek regex hai, semantic reader nahi — reviewer phir bhi padhega |

**Note:** ye gate structure check karta hai, reasoning ki quality nahi. Isko fully-automated proof mat samajho.

## C2 — migration + ek `COMMIT`, do rows

**Order badla to `P-28` ka discriminator kaam nahi karega.**

```powershell
$disposable = "relay_w4d3_life_$PID"
$iniCopy    = ".\_w4d3_$PID.ini"
try {
  docker compose exec -T db psql -X -Atq -U postgres -d postgres -c "create database $disposable" 2>&1 | Out-Null
  ((Get-Content .\alembic.ini -Raw) -replace 'sqlalchemy\.url = .*', "sqlalchemy.url = postgresql+psycopg://postgres:relay@localhost:5433/$disposable") |
    Set-Content -Path $iniCopy -Encoding utf8
  (Select-String -Path $iniCopy -Pattern '^sqlalchemy\.url').Line   # target on screen, before any DDL

  $q = "select 'X|'||(select version_num from alembic_version)||'|'||(select count(*) from information_schema.tables where table_schema='public' and table_name='outbox');"

  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy upgrade head
  if ($LASTEXITCODE -ne 0) { throw 'disposable upgrade head failed' }
  ($q -replace "'X\|'", "'head|'") | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $disposable

  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy downgrade -1
  if ($LASTEXITCODE -ne 0) { throw 'downgrade -1 failed — ye aaj pakda gaya, Din 4/5 pe nahi' }
  ($q -replace "'X\|'", "'down|'") | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $disposable

  & .\.venv\Scripts\python.exe -m alembic -c $iniCopy upgrade head
  if ($LASTEXITCODE -ne 0) { throw 're-upgrade head failed' }
  ($q -replace "'X\|'", "'reup|'") | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $disposable

  $g = "select 'evidence_untouched|'||(select version_num from alembic_version)||'|'||(select count(*) from information_schema.tables where table_schema='public' and table_name='outbox');"
  $ev = @($g | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
        ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
  $ev
  if ($ev[0] -ne 'evidence_untouched|w4d2_completion_instruments|0') {
    throw "P-28 fired: disposable ka Alembic evidence DB pe chala. ACTUAL: $($ev[0])"
  }
} finally {
  docker compose exec -T db psql -X -Atq -U postgres -d postgres -c "drop database if exists $disposable" 2>&1 | Out-Null
  Remove-Item $iniCopy -Force -ErrorAction SilentlyContinue
  "cleanup|$((@("select count(*) from pg_database where datname like 'relay_w4d3%';" | docker compose exec -T db psql -X -Atq -U postgres -d postgres) | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })[0])"
}
```

Expected: `head|w4d3_outbox|1` → `down|w4d2_completion_instruments|0` → `reup|w4d3_outbox|1`, phir
`evidence_untouched|w4d2_completion_instruments|0`, phir `cleanup|0`.

Ab evidence DB upgrade karo, phir **ek `COMMIT`, do rows** ka discriminator:

```powershell
& .\.venv\Scripts\python.exe -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'evidence upgrade failed' }
$heads = @(& .\.venv\Scripts\python.exe -m alembic heads 2>&1 | Where-Object { $_ -match '\(head\)' })
if ($heads.Count -ne 1) { throw "Expected one head after migration, got $($heads.Count)" }
$heads
& .\.venv\Scripts\python.exe -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw "pytest exit=$LASTEXITCODE — Layer A red after migration" }
'C2_pytest=pass   (Week 3 baseline: 7 passed)'
```

**Dispatcher band rakho.** Ek `effect` job enqueue karo (no `block`, `seconds: 1`), ek worker chalao, `Ctrl+C`:

```powershell
$body = @{ type='effect'; payload=@{ seconds=1 }
           idempotency_key = "w4d3-c2-$([guid]::NewGuid().ToString('N'))" } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/jobs' -Method Post -ContentType 'application/json' -Body $body
$c2Job = [int]$r.job_id
"C2_JOB=$c2Job"
```

```powershell
$sql = @"
select concat_ws('|','pair', (select count(*) from side_effects where job_id=$c2Job),
                            (select count(*) from outbox where job_id=$c2Job));
-- do rows ek hi transaction me committed hui ya nahi: xmin barabar hona chahiye
select concat_ws('|','xmin_same',
  (select se.xmin::text::bigint = ob.xmin::text::bigint
     from side_effects se, outbox ob where se.job_id=$c2Job and ob.job_id=$c2Job limit 1)::text);
select concat_ws('|','ob_row', id, job_id, coalesce(effect_key,'NULL'),
  coalesce(dispatched_at::text,'NULL'), attempts) from outbox where job_id=$c2Job;
select concat_ws('|','ob_shape', column_name, data_type, is_nullable) from information_schema.columns
  where table_name='outbox' order by ordinal_position;
select concat_ws('|','ob_pages', (pg_relation_size('outbox'::regclass)/8192),
  coalesce((select pg_relation_size(reltoastrelid)/8192 from pg_class where oid='outbox'::regclass),0));
"@
$out = @(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
         ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$out
if ($out[0] -ne 'pair|1|1')      { throw "Not one effect + one outbox row: $($out[0])" }
if ($out[1] -ne 'xmin_same|true'){ throw "THE day's core invariant failed: the two rows were committed by DIFFERENT transactions ($($out[1]))" }
'C2=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Ek `COMMIT`, do rows** | `pair|1|1` **aur** `xmin_same|true` | `pair|1|0` ya `0|1` → do transactions, outbox ka poora point gaya. **Aur `pair|1|1` akela kaafi nahi:** do alag transactions bhi `1|1` deti hain. `xmin` wahi cheez hai jo unhe alag karti hai — ye check `1|1` ke bharose nahi chhodta |
| Migration reversible | `head|…|1` → `down|…|0` → `reup|…|1` | `downgrade` fail → Din 4/Din 5 ki disposable DB uss din tootegi jab time nahi hoga |
| Alembic ne **evidence** DB ko nahi chhua | `evidence_untouched|w4d2_completion_instruments|0` | Kuch aur → `P-28` fired |
| Disposable DB bacha nahi | `cleanup|0` | Non-zero → Din 4/5 ki naming collide karegi |
| `outbox` ka shape screen pe hai | `ob_shape` lines | Iske bina reviewer ko schema guess karna padta hai, aur `dispatched_at` nullable hai ya nahi ye Q2 ka aadha jawab hai |
| `outbox` ka page baseline | `ob_pages|…|…` | Aaj record na karna Din 5 pe ek baseline chheen leta hai (kal ka `jobs` `2|0` wahi role nibha raha hai) |
| Regression gate **exit code ke saath** | `C2_pytest=pass` | Green bhi safety ka proof nahi: `tests/din5/test_model.py` pure in-memory hai aur migration ko dekh hi nahi sakta |

## C2X — `crash_at: before_commit` ka discriminator (Q1 ka maidan)

```powershell
$body = @{ type='effect'; payload=@{ seconds=1; crash_at='before_commit' }
           idempotency_key = "w4d3-crash-$([guid]::NewGuid().ToString('N'))" } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/jobs' -Method Post -ContentType 'application/json' -Body $body
$crashJob = [int]$r.job_id
"CRASH_JOB=$crashJob"
```

Pehle sequences note karo, phir worker chalao (wo mar jaayega), phir dobara note karo:

```powershell
$q = "select concat_ws('|','seq', (select last_value from side_effects_id_seq), (select last_value from outbox_id_seq));"
$q | docker compose exec -T db psql -X -Atq -U postgres -d relay      # before
.\.venv\Scripts\python.exe -u -m src.worker *>&1 |
  ForEach-Object { '{0:yyyy-MM-dd HH:mm:ss.fff}|{1}' -f (Get-Date).ToUniversalTime(), $_ } |
  Tee-Object -FilePath .\logs\w4d3_crash_worker.log
"native_exit_code=$LASTEXITCODE"
$q | docker compose exec -T db psql -X -Atq -U postgres -d relay      # after
"select concat_ws('|','rows', (select count(*) from side_effects where job_id=$crashJob), (select count(*) from outbox where job_id=$crashJob));" |
  docker compose exec -T db psql -X -Atq -U postgres -d relay
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Dono rows gayab, **ya dono maujood** | `rows|0|0` | `rows|1|0` → effect committed, intent nahi. **Wahi hole hai jo outbox band karne aaya tha**, aur uska matlab hai ki do inserts do transactions me hain |
| Sequence ka delta **alag se** record hua | before/after `seq` lines, dono log me | Sirf row count → rollback ne sequence khaya ya nahi, ye pata nahi chalega, aur wo `P-05` ka poora subject hai |
| Native exit code record hua | `native_exit_code=<n>`, aur `os._exit` ka argument | Missing → *"crash hua"* ek claim hai, evidence nahi. `os._exit` `finally` skip karta hai, to koi *"Clean shutdown"* line nahi honi chahiye — uski **absence** bhi record karo |

## C3 — receiver, aur switch ka **positive** proof

```powershell
# sink chalne dena chahiye: uvicorn src.sink:app --port 8001 --log-level info
$k = "w4d3-manual-$([guid]::NewGuid().ToString('N'))"
$b = @{ idempotency_key=$k; job_id=0; body=@{ probe=$true } } | ConvertTo-Json -Compress
$r1 = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/deliver' -Method Post -ContentType 'application/json' -Body $b
$r2 = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/deliver' -Method Post -ContentType 'application/json' -Body $b
"dedup_on:  first=$($r1.result)  second=$($r2.result)"
if ($r1.result -ne 'applied')   { throw "First delivery should be 'applied', got '$($r1.result)'" }
if ($r2.result -ne 'duplicate') { throw "Second delivery should be 'duplicate', got '$($r2.result)'" }
"select concat_ws('|','rows_dedup_on', count(*)) from sink_deliveries where idempotency_key = '$k';" |
  docker compose exec -T db psql -X -Atq -U postgres -d relay
```

Ab switch **off** karke sink restart karo, ek **naya** key use karo:

```powershell
$k2 = "w4d3-manual-off-$([guid]::NewGuid().ToString('N'))"
$b2 = @{ idempotency_key=$k2; job_id=0; body=@{ probe=$true } } | ConvertTo-Json -Compress
1..2 | ForEach-Object { (Invoke-RestMethod -Uri 'http://127.0.0.1:8001/deliver' -Method Post -ContentType 'application/json' -Body $b2).result }
$rowsOff = (@("select count(*) from sink_deliveries where idempotency_key = '$k2';" |
  docker compose exec -T db psql -X -Atq -U postgres -d relay) | ForEach-Object { $_.Trim() } | Where-Object { $_ })[0]
"rows_dedup_off=$rowsOff"
if ([int]$rowsOff -ne 2) { throw "Dedup switch did not actually turn dedup off (rows=$rowsOff). Run A ka 1 tab kisi cheez ka evidence nahi hai" }
'C3=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Dedup ON: `applied` phir `duplicate`, `1` row | dono labels **aur** row count | Sirf row count → response `rowcount` se aata hai ya hardcoded hai, ye pata nahi chalega |
| **Dedup OFF: `2` rows** | `rows_dedup_off=2` | `1` → switch ne kuch off nahi kiya. **Ye check aaj ka poora din bachaata hai:** iske bina Run A ka `1` ya dedup ka proof hai ya ek constraint ka jo galti se `NOT NULL` reh gaya (`P-18`) |
| Key `NOT NULL` hai | `insert … (null, …)` fail hona chahiye — ek baar manually try karo | Nullable → `[MEASURED-R]` teen `NULL` ek `UNIQUE` column me bina complaint ghus jaate hain, aur dedup chup-chaap band |

## C4 — dispatcher ka happy path aur lifecycle line ka format

```powershell
$log = '.\logs\w4d3_runA_dispatcher.log'
if (-not (Test-Path $log)) { throw "Missing $log" }
if (-not $runAJob) { throw 'RUNA_JOB missing; enqueue wale terminal se hi C4 chalao' }

# P-32 ka gate half: teeno logs pe wahi unstructured check
foreach ($f in @('.\logs\w4d3_runA_dispatcher.log', '.\logs\w4d3_step0_drain_worker.log')) {
  $decay = @(Get-Content $f | Where-Object {
    $b = ($_ -split '\|',2)[1]
    $b -match "\b(job|outbox row) $runAJob\b" -and $b -notmatch 'job_id='
  })
  "unstructured[$([IO.Path]::GetFileName($f))]=$($decay.Count)"
  $decay | ForEach-Object { "UNSTRUCTURED: $_" }
  if ($decay.Count -gt 0) { throw "$f mentions the job without job_id= — P-32 dobara, ab teen producers ke saath" }
}
$hits = @(Get-Content $log | Where-Object { ($_ -split '\|',2)[1] -match "job_id=$runAJob\b" })
"dispatcher_lines=$($hits.Count)"
$hits | ForEach-Object { "DP: $_" }
if (@($hits | Where-Object { $_ -match 'outbox_id=' }).Count -lt 1) {
  throw 'No dispatcher line carries outbox_id= — ek job ke do outbox rows ko alag nahi kar paoge'
}
'C4_log=pass'
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Teeno producers ka log check hota hai** | `unstructured[...]=0` worker **aur** dispatcher pe | Sirf ek log → `P-32` dobara, aur ab teen producers hain to blast radius bada |
| `outbox_id=` line me hai | at least ek line | Missing → agar ek job ke do outbox rows hue (Step 2C ka "likho" branch), to grep unhe alag nahi kar payegi |
| `job_id=<n>\b` word boundary ke saath | `\b` maujood | `job_id=13` ka grep `job_id=134` ko bhi match karega. Aaj ke ids `135+` hain aur `13` maujood hai |

## C5 — Run A vs Run B, closing bench, chain, cleanup

### C5a — do numbers, ek job, aur UTC time ke saath

```powershell
function Show-Delivery {
  param([string]$Tag,[int]$JobId,[string]$Key,[string]$SinkLog,[string]$DispatcherLog)
  "==== $Tag  job=$JobId  key=$Key  snapshot_utc=$([datetime]::UtcNow.ToString('o')) ===="
  $reqs = @(Get-Content $SinkLog | Where-Object { $_ -match [regex]::Escape("idempotency_key=$Key") })
  "sink_requests=$($reqs.Count)"
  $reqs | ForEach-Object { "  SINK: $_" }
  $results = @($reqs | ForEach-Object { if ($_ -match 'result=(\w+)') { $Matches[1] } })
  "sink_results=$($results -join ',')"
  $crash = @(Get-Content $DispatcherLog | Where-Object { $_ -match 'crash_at|after_http' })
  $crash | ForEach-Object { "  CRASH: $_" }
  if ($crash.Count -eq 0) { "  crash_marker=not recorded  <- iske bina 'delivery do baar gayi' ek claim hai" }
}

Show-Delivery 'RUN A dedup=ON'  $runAJob $runAKey '.\logs\w4d3_runA_sink.log' '.\logs\w4d3_runA_dispatcher.log'
Show-Delivery 'RUN B dedup=OFF' $runBJob $runBKey '.\logs\w4d3_runB_sink.log' '.\logs\w4d3_runB_dispatcher.log'
```

```powershell
$ids = @($runAJob, $runBJob) + @(if ($runCJob) { $runCJob })
$idList = ($ids -join ',')
$sql = @"
select concat_ws('|','effects', job_id, count(*)) from side_effects where job_id in ($idList) group by job_id order by job_id;
select concat_ws('|','outbox', job_id, count(*), count(dispatched_at), max(attempts))
  from outbox where job_id in ($idList) group by job_id order by job_id;
select concat_ws('|','sink', s.idempotency_key, count(*)) from sink_deliveries s
  where s.idempotency_key in ('$runAKey','$runBKey') group by s.idempotency_key order by 1;
select concat_ws('|','undispatched', count(*)) from outbox where dispatched_at is null;
"@
@(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **Requests `2`, rows `1`** (Run A) | `sink_requests=2`, `sink_results=applied,duplicate`, `sink|<keyA>|1` | Requests `1` → dispatcher crash hua hi nahi, aur `1` row dedup ka evidence **nahi** hai (`P-12`). Ye "test nahi hua" hai |
| **Run B ke `2` rows** | `sink|<keyB>|2` | `1` → switch off nahi hua, aur Run A ka `1` kisi aur cheez se aa raha hai. **Run B kabhi cut nahi hota** |
| Local dedup toota nahi | `effects|<id>|1` dono run me | `2` → `effect_key` ab delivery attempt ya generation carry kar raha hai |
| Crash marker log me hai | `CRASH:` line dono run me | `not recorded` → *"delivery do baar gayi"* ek claim hai. Aur ek `crash_at` flag jo actually fire nahi hua wo Run A ko Run B jaisa banata hai |
| Snapshot ka UTC time likha hua | header me `snapshot_utc` | Missing → `outbox`/`sink_deliveries` counts snapshot-dependent hain aur compare karne layak nahi rehte (kal ka Run 3 ka sabak) |
| Koi row bina dispatch nahi bachi | `undispatched|0` — **ya** ek naam wali list | Non-zero aur unnamed → Q2 ka jawab (*"koi mechanism nahi hai"*) chup-chaap ek real backlog ban jaata hai, aur wo kal `P-31` ka shape tha |

### C5b — closing bench, chain, cleanup

```powershell
$frozen = 'docs\daily\week_04\DIN_03_PREDICTIONS_FROZEN.md'
if ((Get-FileHash $frozen -Algorithm SHA256).Hash -ne $d3FrozenHash) { throw 'Frozen predictions changed during the day' }
'frozen_unchanged=True'

$relayProcs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper|dispatcher|sink)' })
$relayProcs | Select-Object ProcessId, ParentProcessId, CommandLine
if ($relayProcs.Count -ne 0) { throw "Din 3 ke baad $($relayProcs.Count) Relay process zinda hain (P-13)" }

$sql = @'
set time zone 'UTC';
select concat_ws('|','close', count(*), max(id), (select last_value from jobs_id_seq),
  (select count(*) from job_executions), (select last_value from job_executions_id_seq),
  (select count(*) from side_effects), (select last_value from side_effects_id_seq),
  (select count(*) from outbox), (select last_value from outbox_id_seq),
  (select count(*) from sink_deliveries),
  (select version_num from alembic_version)) from jobs;
select concat_ws('|','status', status, count(*), count(completed_at), count(last_error)) from jobs group by status order by status;
select concat_ws('|','queue', count(*) filter (where status='pending'), count(*) filter (where status='running')) from jobs;
select concat_ws('|','jobs_by_day', d::text, c) from (
  select created_at::date as d, count(*) as c from jobs where id > 134 group by created_at::date) x order by d;
select concat_ws('|','exec_by_day', d::text, c) from (
  select executed_at::date as d, count(*) as c from job_executions where job_id > 134 group by executed_at::date) x order by d;
select concat_ws('|','effect_by_day', d::text, c) from (
  select created_at::date as d, count(*) as c from side_effects where job_id > 134 group by created_at::date) x order by d;
select concat_ws('|','carried_drain_day', d::text, c) from (
  select executed_at::date as d, count(*) as c from job_executions where job_id in (132,133,134) group by executed_at::date) x order by d;
select concat_ws('|','outbox_by_day', d::text, c, dn) from (
  select created_at::date as d, count(*) as c, count(*) filter (where dispatched_at is null) as dn
    from outbox group by created_at::date) x order by d;
select concat_ws('|','undispatched', count(*)) from outbox where dispatched_at is null;
select concat_ws('|','idle_in_txn', count(*)) from pg_stat_activity
  where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select concat_ws('|','probe_dbs', (select count(*) from pg_database where datname like 'relay_w4%'));
select concat_ws('|','stale_gen_exec', count(*)) from job_executions e join jobs j on j.id = e.job_id
  where e.claim_generation is not null and e.claim_generation <> j.claim_generation;
select concat_ws('|','pages_jobs', (pg_relation_size('jobs'::regclass)/8192),
  coalesce((select pg_relation_size(reltoastrelid)/8192 from pg_class where oid='jobs'::regclass),0));
select concat_ws('|','pages_outbox', (pg_relation_size('outbox'::regclass)/8192),
  coalesce((select pg_relation_size(reltoastrelid)/8192 from pg_class where oid='outbox'::regclass),0));
select concat_ws('|','seq_gaps', string_agg(g::text, ',' order by g)) from
  (select generate_series(1,(select max(id) from jobs)) g except select id from jobs) s;
'@
@(($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay) |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })

Get-ChildItem .\logs\w4d3_*.log | Select-Object Name, Length, LastWriteTime
git status --porcelain=v1 -- src alembic
```

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **C5 ka SQL actually chalta hai** | Saari lines print, `ON_ERROR_STOP=1` ke saath exit `0` | Error → Din 1 ka bug dobara. Ek check jo error deta hai wo `pass` nahi hai |
| **Queue drained assert hua** | `queue|0|0` | Non-zero → `P-31` teesri baar. **Ye line kal C5b me nahi thi aur wahi uska poora point hai** |
| **`undispatched|0` assert hua** | `0`, ya ek naam wali list jiska owner likha ho | Non-zero aur unnamed → outbox ka apna carried backlog ban gaya, aur uske liye koi reaper nahi hai (Q2) |
| Chain per-day `group by` se | `jobs_by_day` / `exec_by_day` / `effect_by_day` / `outbox_by_day` | Sirf total match → do compensating errors chhup sakti hain (Week 2 ka wahi bug) |
| Carried `132`/`133`/`134` ka delta **alag line** | `carried_drain_day` apni line me, aur `id > 134` filter uske bahar | Ek line me judna → Step 0D ke `3` dispatches Din 3 ke experiments me chale jaayenge |
| `outbox` ke page baseline | `pages_outbox|<heap>|<toast>` | Missing → Din 5 pe `10k` outbox rows ka comparison baseline ke bina hoga |
| `jobs` ke pages | `pages_jobs|…` — Din 2 ka close `2|0` tha | Iska badhna expected hai; record na karna Din 5 ka baseline chheenta hai |
| Koi process zinda nahi | `0` | Non-zero → agla din contaminated (`P-13`). **Aaj chaar tarah ke process hain** (worker, reaper, dispatcher, sink) aur regex chaaron ko cover karta hai |
| Koi disposable DB nahi bachi | `probe_dbs|0` | Non-zero → Din 4/5 collide karega |
| Sequence reset nahi hua | `seq_gaps` me `79,117,118,119,120,122` aur aaj ke naye gaps | Gaps gayab → `P-05` toota |
| `logs/` ka evidence disk pe | `w4d3_*.log`, non-zero length | Missing → ordering proof gaya (`P-29`). `.gitignore` me `*.log` hai |
| Naya code commit hone layak | `git status` me sirf aaj ki expected files | `src/sink.py`, `src/dispatcher.py`, `src/worker.py`, migration — aur `crash_at` ka code **isme hona chahiye** (`P-23`) |

---

# Part D — Scope guard: aaj **nahi**

| Kya | Owner | Aaj karne se kya khota hai |
|---|---|---|
| Asli SMTP / Stripe / koi real third-party | **Month 2+** | Aaj ka receiver jaan-boojh ke ek aisi cheez hai jiski dedup table tum padh sakte ho. Ek asli service ke saath `sink_deliveries` me `1` vs `2` ka farq **naapa hi nahi ja sakta**, aur wahi aaj ka poora measurement hai |
| Dispatcher ka leader election / do dispatcher ko coordinate karna | **`D-29` me likha jaata hai, banaya nahi jaata** | `P9` `[MEASURED-R]` kehta hai ki *"bahar"* shape me do dispatcher ek row do baar deliver karte hain. Aaj ka kaam usko **dikhana** hai (Run C), fix karna nahi |
| Outbox retention / `DELETE` after dispatch | **Month 2** | Aaj rows evidence hain (`D-21` ka precedent). Delete karne se Run A ka `2 requests / 1 row` ka trail chala jaayega |
| `10k` outbox rows ka load, dispatcher batch size tuning | **Din 5, disposable DB pe** | Aaj batch `1` rakho. Batch aur crash seam ek saath hilaana do variables hai (AGENTS rule 7) |
| Outbox ke liye ek reaper / lease | **pehle Q2 ka jawab likho, phir Din 4/Month 2** | Q2 poochta hai ki mechanism **hai ya nahi**. Aaj usko bana dena sawaal ko mita dena hai. **Measurement pehle, fix baad me** (`D-21` ka pattern) |
| `LISTEN`/`NOTIFY` se dispatcher ko wake karna | **Month 2** | `NOTIFY` at-most-once hai aur wo ek naya delivery guarantee introduce karta hai. Aaj poll `2.0 s` — `D-01` ke saath consistent |
| Handler timeout (`asyncio.wait_for`) | **Month 2 ka pehla item** (`P-15`) | Kal ka Run 2 exactly wo shape tha. Aaj timeout add karne se kal ka jawab retroactively dhundhla ho jaata hai |
| Lease `30 s`, heartbeat `10 s`, poll `2.0 s`, backoff, `MAX_ATTEMPTS`, `effect_key` badalna | **kabhi nahi, iss hafte** | Week 2–4 ke saare measurements inhi numbers pe khade hain |
| `httpx` timeout ko chupchaap chhodna ya chupchaap badalna | — | `[MEASURED-R]` default `5.0 s` hai. Q5 ka `30 s` iske saath conflict karta hai. **Jo chuno, likho** — na likhna wo ek chhupa hua variable hai |
| Rows `95`, `108`, `110`, `115`, `126`, `128`, `132`, `133`, `134` ko `UPDATE`/`DELETE` karna | **kabhi nahi** | `P-05`. Step 0D unhe **chalata** hai |
| `last_error` ko `GET /jobs/{id}` me expose karna | **auth ke baad** | `D-03`. Aur aaj `sink_deliveries.body` ek naya exposure surface hai — usko bhi kisi endpoint pe mat daalo |
| `DDIA_CH8_LINKS.md` lines 10–13 | **Din 6** | Aaj sirf `DDIA_CH11_LINKS.md` ka carried re-anchor |
