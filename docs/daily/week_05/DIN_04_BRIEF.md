# WEEK 5 · DIN 4 — `2026-09-27` — Chaar khoye hue numbers, ek premise jo kabhi observe nahi hui, aur ek chain jo aaj tak compose nahi hui

**Budget `110 min` · Layer L2 · Aaj bhi `src/` me ek line nahi badlegi, aur aaj wo gate Din 3 se zyada mushkil hai
kyunki aaj ka poora kaam configuration aur measurement hai.**

> **Din 3 ne publishing decide ki. Aaj uska pehla test hai: aaj ke numbers ek aise rule ke neeche paida honge jo
> kal se exist karti hai.** Din 3 ka commit `e3121a3` — `52` files, jisme `13` `PREDICTIONS_FROZEN` aur
> `docs/logs/WEEK_05.md` **pehli baar** hain. `DIN_03_PREDICTIONS_FROZEN.md` ka SHA-256 disk pe aur `HEAD` se
> **identical** hai `[MEASURED 2026-09-26]` — matlab pehli baar wo hash kisi teesre insaan ke liye bhi
> auditable hai, aur `P-47` ka asli point wahi tha.
>
> **Aur Din 3 ka sabse bada finding ek ginti se aaya, kisi crash se nahi.** `D-32` ki policy table chaar artifact
> classes cover karti hai; disk pe **nau** hain. Bees files — `ANSWERS` `13`, `DESIGN` `5`, `PROBLEM` `1`,
> `PROPERTY` `1` — bina faisle public ho rahi thi, aur `C1` unhe **structurally** dekh nahi sakta tha. **Wo bees
> files deliberately commit me NAHI gayi.** `git status` aaj bhi `20` untracked dikhayega aur **wo sahi hai.**
> `P-54`.
>
> **Aaj ka subject Week 4 Din 5 ke chaar khoye hue numbers hain, aur unme se teen ek hi premise pe khade hain
> jo kabhi observe nahi hui.** `P-45` word-for-word: *"the `pool_size=2` premise of the whole step rests on the
> configuration having been set rather than on it having been observed."* **To aaj ka pehla kaam ek number
> re-take karna nahi hai — pehle wo premise naapna hai.** Agar premise ghalat nikli, teen numbers re-take karne
> ka matlab hi nahi banta.
>
> **Aur ek chain hai jo `P-41` `[INFERRED]` likh kar chhod deta hai, aur usko compose karne ke liye jo teen
> cheezein chahiye, wo aaj teeno ek saath maujood hongi.** Dispatcher `FOR UPDATE SKIP LOCKED` ko HTTP call ke
> **across** hold karta hai (`src/dispatcher.py:46` → `:66`), receiver ka `ON CONFLICT DO NOTHING` ek uncommitted
> conflicting key pe **wait** karta hai (`P-41`), aur pool `2` pe hai. **Teen measured links, aur poori chain aaj
> tak kabhi ek saath nahi chali.** Wo aaj ka sabse valuable output hai, aur wo Step 5 hai.

---

## PART A — Steps

### Step 0 — 10 min: bench, aur teen gate jo Din 3 se seedhe aa rahe hain

```powershell
cd d:\PROJECTS\relay
git status --short          # expected: 20 untracked files, 0 modified. Ye 20 P-54 hain — inhe stage NAHI karna
git log --oneline -1        # expected: e3121a3 feat(w5d3): publishing surface (D-32 DRAFT), ...
```

**`20` untracked files dikhengi aur wo aaj ka pehla trap hai.** Wo `*_ANSWERS.md`, `*_DESIGN.md`,
`*_PROBLEM.md`, `*_PROPERTY.md` hain. `D-32` unke baare me **chup** hai, aur publishing **one-way door** hai —
`git rm --cached` sirf `HEAD` se path hataata hai, blob us commit me padi rehti hai `[MEASURED 2026-09-26]`. **Aaj
`git add -A` mat chalana. `git add <named files>` chalana.**

**Teen gates, aur teeno Din 3 ke measured defects se aaye hain:**

```powershell
# 1. src/ gate — working tree, index aur commit dono se independent
(git diff --name-only HEAD -- src/ | Measure-Object).Count          # expected: 0
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py

# 2. alembic — exit 0 pe bharosa mat karo, STRING pe assert karo
.\.venv\Scripts\python.exe -m alembic heads > logs\w5d4_step0_heads.txt 2>&1
Get-Content logs\w5d4_step0_heads.txt        # expected exactly: w4d4_sink_unique (head)

# 3. Relay-only process count
(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count   # expected: 0
```

**Gate 2 pe dhyaan.** Din 3 pe reviewer ne pehle socha ki `alembic heads` ek decorative gate hai kyunki console
pe kuch nahi aaya — **aur wo reviewer ke apne tooling ka artifact tha, alembic ka nahi.** File redirect pe
`25` bytes aate hain. **Isliye gate `exit 0` pe nahi, string pe assert karta hai** — aur wo `P-53` ka rule bhi
satisfy karta hai, kyunki output ek file me hai.

Nau counters evidence DB `relay` pe. **Role `postgres` hai, `relay` nahi:**

```powershell
docker exec relay-db-1 psql -U postgres -d relay -t -A -F "|" -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');" | Tee-Object logs\w5d4_step0_counters.txt
```

**Expected `133|145|19|4|7|39|5|0|1`**, delta `0`.

**Executable end:** paanch `src` hashes, `heads` file jisme exact string hai, Relay-process count `0`, nau
counters ek file me, **aur `DIN_04_PREDICTIONS_FROZEN.md` likha aur `Get-FileHash -Algorithm SHA256` liya hua** —
Part B ke paanch jawab, `idk` included.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `git diff --name-only HEAD -- src/` | working tree aur `HEAD` ke beech `src/` me badli hui files. `HEAD:src` tree hash se alag — wo uncommitted changes nahi dekhta |
| one-way door | ek faisla jisko undo karne ka koi mechanism nahi. Publishing ek hai: path `HEAD` se hat sakta hai, blob history me rehti hai |
| string assertion vs exit code | `exit 0` *"command chala"* batata hai. String assertion *"sahi jawab aaya"* batati hai. Do alag claims |
| `Tee-Object` | output ko console **aur** file dono me bhejta hai. `P-53` ke rule ka sabse sasta compliance |

---

### Step 1 — 15 min: **jo premise kabhi observe nahi hui.** Pehle ye, phir baaki sab

`P-45` ka exact sentence: *"there is no record of that filter's output, so the `pool_size=2` premise of the whole
step rests on the configuration having been set rather than on it having been observed."*

**Do alag claims hain aur aaj tak dono ko ek samjha gaya hai:**

| Claim | Kaun prove karta hai |
|---|---|
| *"maine pool `2` **set** kiya"* | `src/database.py:47` ka import-time print — `pool=2+0` |
| *"process ne pool `2` **honour** kiya"* | `pg_stat_activity`, `application_name` se filtered — asli connection count |

**Pehla doosre ko imply nahi karta**, aur `P-45` ka gate exactly doosra maangta tha.

**Setup — aur yahan ek trap hai jo poora step chup-chaap default pool pe naap sakta hai.** `src/database.py`
lines `35`–`37` env vars ko **import time** pe padhti hain, aur `.env` me koi `RELAY_*` key nahi hai
`[MEASURED 2026-09-26]`. Matlab vars us shell me set hone chahiye jo **uvicorn launch** karta hai — us shell me
nahi jo probe chalata hai. Do terminal chahiye:

```powershell
# TERMINAL A — API. Ye env vars ISS shell me set hone hain, launch se PEHLE
$env:RELAY_PROCESS_NAME = "api_w5d4"
$env:RELAY_POOL_SIZE    = "2"
$env:RELAY_MAX_OVERFLOW = "0"
$env:RELAY_POOL_TIMEOUT = "3.0"
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000 *> logs\w5d4_step1_api.log
```

`RELAY_POOL_TIMEOUT = 3.0` **deliberately** hai — Week 4 Din 5 ka `3.0055 s` iske bina reproduce nahi hoga, aur
kyun wo `Q2` ka hissa hai.

```powershell
# TERMINAL B — observe
Select-String -Path logs\w5d4_step1_api.log -Pattern "^resolved_db="    # claim 1: set hua

# claim 2: honour hua — idle pe, phir load pe
docker exec relay-db-1 psql -U postgres -d relay -t -A -F "|" -c "SELECT application_name, count(*), array_agg(distinct state) FROM pg_stat_activity WHERE application_name LIKE 'api_w5d4%' GROUP BY 1;" | Tee-Object logs\w5d4_step1_idle.txt
```

**Idle pe jo number aayega wo `2` nahi hoga, aur wo galat nahi hai** — kyun, wo `Q1` hai. Ab peak:

```powershell
# teen concurrent /slow-hold, pool 2+0 pe. seconds ko chhota rakho
1..3 | ForEach-Object -Parallel { curl.exe -s -o NUL -w "%{http_code} %{time_total}`n" "http://127.0.0.1:8000/slow-hold?seconds=8" } -ThrottleLimit 3 |
  Tee-Object logs\w5d4_step1_peak_clients.txt
# ISKE CHALTE WAQT, terminal B me:
docker exec relay-db-1 psql -U postgres -d relay -t -A -F "|" -c "SELECT application_name, count(*), array_agg(distinct state) FROM pg_stat_activity WHERE application_name LIKE 'api_w5d4%' GROUP BY 1;" | Tee-Object logs\w5d4_step1_peak.txt
```

**Executable end — ek do-row table, aur uski doosri row wo cheez hai jo `P-45` ke baad se missing hai:**

| Observation | Value | File |
|---|---|---|
| import-time print, `pool=` | | `w5d4_step1_api.log` |
| `pg_stat_activity` count at **idle** | | `w5d4_step1_idle.txt` |
| `pg_stat_activity` count at **peak** | | `w5d4_step1_peak.txt` |

Aur ek line: **in teen numbers me se kaunsa `P-45` ka gate satisfy karta hai, aur kaunse do nahi.**

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `pool_size` vs `max_overflow` | `pool_size` persistent connections; `max_overflow` unke upar temporary. Ceiling `pool_size + max_overflow` |
| lazy allocation | `QueuePool` engine banne pe `0` connections rakhta hai aur zaroorat pe banata hai. Configured size ek **ceiling** hai, pre-allocation nahi |
| `application_name` | ek Postgres session setting jo `pg_stat_activity` me dikhti hai. Relay usko `connect_args.server_settings` se set karta hai |
| `pg_stat_activity.state` | `active` = statement chal raha hai · `idle` = session khaali · `idle in transaction` = transaction khula, statement nahi |
| import-time read | `os.environ.get(...)` module top pe. Value process start pe freeze hoti hai; baad me env badalne se kuch nahi hota |

---

### Step 2 — 15 min: pool saturation timeout — `3.0055 s` ko re-take karo, **artifact ke saath**

`P-45` ke teen `[REPORTED, NOT VERIFIABLE]` numbers me pehla. Aaj usko ek retained file me laana hai.

**Setup Step 1 ka hi hai** — pool `2+0`, `pool_timeout 3.0`. Teen concurrent `/slow-hold?seconds=8`: do
connection le lete hain, **teesra kya karta hai** — wo `Q2` hai.

```powershell
# probe labs/ me rakho, scratch/ me NAHI — D-32 ke hisaab se labs/ tracked hai
# run id MICROSECONDS ke saath: %Y%m%d_%H%M%S_%f. Second granularity collide karti hai [MEASURED 2026-09-26]
.\.venv\Scripts\python.exe labs\w5d4_pool_probe.py    # tu likhega; output logs\w5d4_step2_<runid>.log
```

Probe ko teen cheez record karni hain, per request: **HTTP status · wall-clock elapsed · exception class name
(agar koi)**. Aur API ke apne log se wo line uthani hai jisme error class hai.

**Ek cheez jo iss measurement ko contaminate karti hai aur aaj theek NAHI ho sakti:** `src/database.py:41` pe
`echo=True` **hardcoded** hai `[MEASURED 2026-09-26]`. Usko band karne ke liye `src/` edit chahiye, jo aaj
banned hai. **Achhi khabar: Week 4 Din 5 ne bhi `echo=True` ke saath naapa tha, to dono numbers comparable
hain** — aur Din 2 ne naapa ki `echo` dominant term **nahi** hai, run-to-run variance hai. **Har latency number
ke saath `echo=True` likhna hai.**

**Executable end:** ek retained log file jisme teen requests ka status, elapsed aur error class hai; aur ek line:
**`3.0055 s` reproduce hua ya nahi, aur wo number kis cheez se bandha hua hai** — `pool_timeout`, `seconds`, ya
kisi teesri cheez se.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `pool_timeout` | ek checkout kitni der queue me wait karega connection ke liye. Expire hone pe `sqlalchemy.exc.TimeoutError` |
| `sqlalchemy.exc.TimeoutError` | SQLAlchemy ka apna exception, Python ke builtin `TimeoutError` se **alag** class. `except TimeoutError` galat wali pakad sakta hai |
| saturation | jab checkout demand `pool_size + max_overflow` se zyada ho |
| retained artifact | wo file jo run ke baad bhi maujood hai aur usme wo number likha hai. Console pe dikhna retention nahi hai (`P-50`) |

---

### Step 3 — 15 min: `/healthz` starvation — `3.1618 s`, aur ek discriminator jo teen causes alag karta hai

Doosra `[REPORTED, NOT VERIFIABLE]` number. **Aur yahan ek cheez hai jo iss number se zyada value rakhti hai.**

**Ek failing `/healthz` ke teen bilkul alag causes hain**, aur teeno ka symptom ek jaisa dikhta hai:

| Cause | Kya hua |
|---|---|
| pool starvation | process zinda, DB zinda, connection nahi mil rahi |
| DB down | process zinda, DB mara hua |
| process dead | kuch nahi chal raha |

**Ek `/healthz` timeout teeno se aa sakta hai. To ek observation chahiye jo teeno ko alag kare.**
`src/main.py` me chaar relevant endpoints hain `[MEASURED 2026-09-26]`: `/health` (L16), `/healthz` (L21),
`/db-ping` (L27), `/slow-hold` (L33). **Unme se ek DB ko chhuta hi nahi.** Usko dhoondho — wo tumhara
discriminator hai, aur `Q3` uska doosra half hai.

```powershell
# pool saturated hone ke DORAN, teen endpoints ek saath
"health","healthz","db-ping" | ForEach-Object {
  "$_ => $(curl.exe -s -o NUL -w '%{http_code} %{time_total}' "http://127.0.0.1:8000/$_")"
} | Tee-Object logs\w5d4_step3_discriminator.txt
```

Aur `D-28` ke saath reconcile: us decision me `/healthz` ko **liveness** likha hai, readiness nahi. **Aaj ka
measurement uss label ko support karta hai ya contradict karta hai — ek line likho.**

**Executable end:** teen endpoints ka status+latency ek file me, saturation ke doran; aur ek line: **kaunsi ek
observation pool starvation ko DB-down se alag karti hai, aur wo `D-28` ke liye kya matlab rakhti hai.**

**Terms used in this step**

| Term | Kya hai |
|---|---|
| liveness vs readiness | liveness: *"process zinda hai?"* → fail pe restart. readiness: *"traffic le sakta hai?"* → fail pe traffic hatao. Ek ko doosra samajhna cascade banata hai |
| `Depends(get_db)` | FastAPI dependency jo handler chalne se **pehle** resolve hoti hai. Uska checkout handler ke andar nahi, uske pehle hota hai |
| discriminator | ek observation jo do ya zyada possible causes ko alag karti hai. Ek check jo sab causes pe same output de, wo cause ke baare me kuch nahi batati |
| cascade | jab ek mitigation (restart) us problem ko badha de jiska wo response thi |

---

### Step 4 — 10 min: client bhaag gaya — connection wapas aayi ya nahi

**Ye chaaron khoye hue numbers me se nahi hai. Ye naya hai, aur ye `P-44` ki keemat decide karta hai** — kyunki
`/slow-hold?seconds=<bada>` ka asli khatra *"request slow hai"* nahi hai, wo *"connection kitni der bandhi
rehti hai"* hai.

```powershell
# ek /slow-hold bhejo aur client ko 3s baad MAAR do
$job = Start-Job { curl.exe -s -m 3 "http://127.0.0.1:8000/slow-hold?seconds=20" }
Start-Sleep -Seconds 4
Stop-Job $job -ErrorAction SilentlyContinue; Remove-Job $job -Force -ErrorAction SilentlyContinue

# client mar chuka hai. Server par kya chal raha hai?
docker exec relay-db-1 psql -U postgres -d relay -t -A -F "|" -c "SELECT application_name, state, left(query,40), now()-query_start FROM pg_stat_activity WHERE application_name LIKE 'api_w5d4%';" | Tee-Object logs\w5d4_step4_after_disconnect.txt
```

Aur `20 s` beetne ke baad dobara wahi query. **Do snapshots ka farak `Q4` hai.**

**Executable end:** do `pg_stat_activity` snapshots — disconnect ke turant baad aur `seconds` khatam hone ke baad
— aur ek line: **client disconnect `pg_sleep` ko rokta hai ya nahi, aur connection kab pool me wapas aati hai.**

**Terms used in this step**

| Term | Kya hai |
|---|---|
| client disconnect | TCP connection band ho jaana request poori hone se pehle. Server ko iska pata chal sakta hai — aur wo **automatically** kuch karega, ye alag sawaal hai |
| cancellation propagation | ye sawaal ki ek abort hua request apne downstream kaam (DB statement) ko cancel karta hai ya nahi |
| `pg_cancel_backend` | Postgres ka explicit mechanism ek chal rahi query rokne ka. Apne aap nahi chalta |
| connection lifetime vs request lifetime | do alag durations. Inko ek maanna hi `P-44` ka core hai |

---

### Step 5 — 20 min: **wo chain jo `P-41` `[INFERRED]` likh kar chhod deta hai.** Aaj ke din ka sabse valuable output

`P-41` ka exact text: *"two dispatch attempts stalled behind one slow `sink_deliveries` writer exhaust the pool,
and the symptom surfaces as `pool_timeout` in Relay while the actual cause is a lock inside the receiver's
database. The chain is `[INFERRED]` — no run has composed it — and the two links are each `[MEASURED]`."*

**Teen links, teeno source me confirm `[MEASURED 2026-09-26]`:**

| Link | Kahan |
|---|---|
| dispatcher outbox row ka lock HTTP call ke **across** hold karta hai | `src/dispatcher.py:46` (`with_for_update(skip_locked=True)`) → `:66` (`client.post`) |
| receiver ka `ON CONFLICT DO NOTHING` uncommitted conflicting key pe **wait** karta hai | `P-41`, measured `3.058 s` — holder ki lifetime ko exactly track kiya |
| HTTP call ka timeout **explicit** `5.0 s` hai | `src/dispatcher.py:34` — `httpx.AsyncClient(timeout=5.0)` |

**Teesri line ek chhoti correction hai jo aaj record ho rahi hai:** `P-41` ne usko *"`httpx` default `5.0 s`,
itself still `[INFERRED]`"* likha tha. **Wo default nahi hai, wo likha hua hai.** Value ab `[MEASURED]` hai.
**Par *"wo lock hold ko bound karta hai"* abhi bhi `[INFERRED]` hai** — uske liye exception path pe rollback
hona chahiye, aur wo aaj naapna hai.

**Ye step rows likhta hai, to DISPOSABLE DB pe chalega.** Evidence DB `relay` ko chhuna nahi hai:

```powershell
docker exec relay-db-1 psql -U postgres -d postgres -c "CREATE DATABASE relay_w5d4;"
# DATABASE_URL isi shell me override karo, phir alembic upgrade head
# har process ka apna RELAY_PROCESS_NAME do, warna pg_stat_activity join nahi hoga
```

**Shape:** ek `asyncpg` connection `sink_deliveries` me key `K` insert kare aur transaction **khuli rakhe** ·
outbox me do rows jinki dispatcher-minted key wahi `K` ho (`src/dispatcher.py` `f"job:{outbox_row.job_id}"`
banata hai, to do rows ka `job_id` same chahiye) · sink pool `2+0` pe · dispatcher chalu.

**Chaar cheez record karni hain, aur chauthi wali sabse important hai:**

1. Dispatcher ka observed behaviour — `pool_timeout`, `httpx` timeout, ya kuch aur
2. **Kaunsa error class kahan dikhta hai** — aur wo error kis process ke log me hai
3. Outbox row ka lock kitni der held raha — `pg_locks` ya `pg_stat_activity` se
4. **Us error ko padh kar kya tu asli cause tak pahunch sakta hai?** `P-41` ki poori baat yahi hai: symptom
   Relay me hai, cause receiver ke DB me hai

**Executable end:** retained log, aur ek line: **chain compose hui ya nahi, aur agar hui to observable symptom
ne asli cause tak pahunchaya ya nahi.** Agar chain compose **nahi** hui, wo bhi ek finding hai — likho ki
kaunsi link tooti aur kyun.

**Cut rule:** agar `90 min` pe ye step shuru nahi hua, **Step 3 aur Step 4 ke numbers rakh ke isko Din 5 pe
bhej do** — Din 5 ka slot khaali hai. **Step 1 kabhi cut nahi hoga**, kyunki uske bina Step 2/3 ke numbers ka
matlab hi nahi.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `FOR UPDATE SKIP LOCKED` | locked rows ko result set se **hata deta hai** — wait nahi karta. `ON CONFLICT` ka ulta |
| lock held across an RPC | ek DB lock jo ek network call ke doran khula rehta hai. Lock ki duration remote party pe depend karti hai |
| composed failure | do systems ke interaction se paida hua failure, jisme symptom ek jagah hai aur cause doosri |
| `pg_locks` | wo view jo batata hai kaun kaunsa lock hold kar raha hai aur kaun wait kar raha hai |
| observability gap | jab ek symptom apne cause tak nahi pahunchata, chahe dono logged ho |

---

### Step 6 — 15 min: `P-44` ka faisla — **aur ye Step 2–5 ke BAAD hai, iska order load-bearing hai**

**Yahan `Q` nahi hai — ye design judgement hai, Situation 3.** Gemini se options aur costs discuss kar sakta
hai; **pick usse nahi poochna.**

`/slow-hold` ab `src/main.py:33` pe hai: `seconds` ek caller-supplied query param hai, **koi upper bound nahi**,
aur handler pool connection uski poori duration hold karta hai. Relay me authentication kahin nahi hai
(`D-03` deliberately). **Aaj tak ye ek theory thi. Step 2, 3 aur 4 ke baad uske teeno effects naape hue honge.**

**Order kyun load-bearing hai:** `/slow-hold` ko bound karna ya hatana Step 2/3/5 ki measurement **kamzor**
karta hai — wo harness app ke pool ko share karne ke liye hi app ke andar hai, aur pool share karna hi measurement
ka point hai. `P-44` khud kehta hai: *"a harness that used its own engine would have measured nothing."`
**Isliye pehle naapo, phir decide karo.**

**Teen shapes, aur teeno ka cost `P-44` me hai:** separate app factory sirf test ke liye · environment-gated
router · `seconds` pe hard cap + `statement_timeout`. **Aur chauthi cheez jo `P-44` naam se maangta hai:**
`/health`, `/healthz`, `/db-ping` teen overlapping endpoints hain aur aakhri do duplicate hain — **kaunse teen
me se kitne bachenge.** Step 3 ne unme se ek ko discriminator bana diya hai, to wo answer badal sakta hai.

**Executable end — koi `src/` edit nahi. Teen likhi hui cheezein:**

1. Chuna hua shape, aur **kaunsa cost accept kiya** — naam se
2. Uska **owner day**, ek naam. Agar `Month 3` hai to likho ki wo kis cheez ka wait kar raha hai
3. Ek line jo ye kehti ho: fix ke baad **kaunsi measurement dobara nahi li ja sakegi**, aur us artifact ka path
   jisme wo number ab retained hai

**Terms used in this step**

| Term | Kya hai |
|---|---|
| app factory | ek function jo `FastAPI()` instance banata hai, module-level global ki jagah. Test aur prod ko alag app dene ka seam |
| environment-gated route | ek endpoint jo sirf ek env var set hone pe register hota hai |
| `statement_timeout` | Postgres setting — ek statement itne ms se zyada chale to abort. Server-side bound, client-side nahi |
| observability debt | ek measurement jo sirf ek asurakshit mechanism ki wajah se possible thi. Usko theek karne ki keemat wo measurement hai |

---

### Step 7 — 10 min: close bench, aur ek record correction

```powershell
(git diff --name-only HEAD -- src/ | Measure-Object).Count       # 0
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py   # Step 0 ke barabar
.\.venv\Scripts\python.exe -m alembic heads > logs\w5d4_step7_heads.txt 2>&1
Get-Content logs\w5d4_step7_heads.txt                            # w4d4_sink_unique (head)
(Select-String -Path src\*.py -Pattern "except BaseException" | Measure-Object).Count       # 0

# disposable DB drop
docker exec relay-db-1 psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS relay_w5d4;"
docker exec relay-db-1 psql -U postgres -d postgres -t -A -c "SELECT count(*) FROM pg_database WHERE datname LIKE 'relay\_%';"   # 0

(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count            # 0
```

Nau counters — delta `0`. **Aur seal + `P-54` ka gate:**

```powershell
(git ls-files -- "*_KEY.md" | Measure-Object).Count                                          # 0
(git ls-tree -r --name-only HEAD | Select-String -CaseSensitive "_KEY\.md" | Measure-Object).Count  # 0
(git ls-files -- "*.pyc" | Measure-Object).Count                                             # 1 — positive control
(git status --porcelain | Select-String -CaseSensitive "_ANSWERS\.md|_DESIGN\.md|_PROBLEM\.md|_PROPERTY\.md" | Measure-Object).Count   # 20 — badalna NAHI chahiye
```

**Ek record correction jo aaj honi hai, `10` line se kam me.** `docs/month_01/daily/week_04/DIN_05_DESIGN.md`
Faisla 3 apna `Chosen` option `step4_load_probe.py` naam se likhta hai **aur wo file tree me nahi hai**
(`P-45`). Aaj tu ek load/pool probe likh raha hai. **Do me se ek karo:** us probe ko `labs/` me rakh kar Faisla 3
ke neeche ek amendment line likho jo naye path ko naam se de, **ya** likho ki Faisla 3 ka `Chosen` implementation
`[NOT RETAINED]` hai. **Dono acceptable hain; chhodna nahi** — Din 6 ka DoD audit isko maangta hai.

**Aur `labs/` vs `scratch/` ka faisla `D-32` ne kar diya hai: `labs/` tracked hai, `scratch/` nahi.** Aaj ka
har probe `labs/` me jaata hai, `w5d4_` prefix ke saath.

---

## PART B — Prediction questions

> **Inhe Part A ya Part C ke saath Gemini ko NAHI dena. Har sawaal apne step se PEHLE answer hota hai, apne
> head se, likha hua. `idk` ek valid jawab hai aur wo `0` score karta hai — aur wo ek guess ko knowledge ki
> tarah likhne se behtar hai. Din 3 pe paanchon `idk` the aur calibration `5/5` thi; wo record saaf hai.**

```text
Q1 (Step 1 se pehle)
Pool RELAY_POOL_SIZE=2, RELAY_MAX_OVERFLOW=0 set kar ke uvicorn chala.
(a) src/database.py ka import-time print kya likhega — exact shape.
(b) Koi request bhejne se PEHLE, pg_stat_activity me us application_name ke
    liye kitne rows honge — ek number.
(c) Teen concurrent /slow-hold ke DORAN kitne rows honge — ek number.
(d) Aur asli sawaal: (a) ka output (c) ke number ko prove karta hai ya nahi?
    Ek aisa scenario likho jisme print `pool=2+0` kahe aur process fir bhi
    2 se ZYADA connections hold kare. Agar aisa scenario possible nahi hai,
    to likho kyun nahi.

Q2 (Step 2 se pehle)
pool_size=2, max_overflow=0, pool_timeout=3.0. Teen concurrent
/slow-hold?seconds=8.
(a) Teesra request ka HTTP status code kya hoga — ek number.
(b) Wo kitni der me return karega — ek number, aur likho wo kis cheez se
    bandha hai: pool_timeout, seconds, ya kuch aur.
(c) Exception ka class name kya hoga — poora naam.
(d) Aur: agar RELAY_POOL_TIMEOUT set NA karta (default 30.0), to (b) ka
    number kya hota? Week 4 Din 5 ne 3.0055 s report kiya tha — us din
    pool_timeout kya raha hoga?

Q3 (Step 3 se pehle)
Pool saturated hai (do /slow-hold chal rahe hain).
(a) /healthz kya karega — 200, hang, ya error? Aur kitni der?
(b) /health kya karega? /db-ping kya karega? Teeno ka jawab same hai ya nahi?
(c) Aur asli sawaal: ek failing /healthz ke teen causes hain — pool starvation,
    DB down, process dead. Kaunsi EK observation pool starvation ko baaki do se
    alag karti hai? Naam se likho.
(d) Us observation ka D-28 ke "liveness, not readiness" label pe kya asar hai?

Q4 (Step 4 se pehle)
Ek /slow-hold?seconds=20 bheja, aur client ko 3 s baad maar diya.
(a) Server pe pg_sleep ruk jaayega ya chalta rahega? Haan/nahi aur mechanism.
(b) Pooled connection pool me kab wapas aayegi — 3 s pe, 20 s pe, ya kabhi nahi?
(c) pg_stat_activity disconnect ke turant baad us session ka state kya
    dikhayega — ek shabd.
(d) Iska /slow-hold?seconds=100000 ke liye kya matlab hai — ek line.

Q5 (Step 5 se pehle)
Ek asyncpg connection ne sink_deliveries me key K insert ki aur transaction
khuli rakhi. Do outbox rows ka job_id same hai, to dispatcher dono ke liye wahi
K mint karega. Sink ka pool 2+0 hai. Dispatcher chalu hai.
(a) Dispatcher ka pehla dispatch attempt kitni der me kya dega? Error class
    aur latency.
(b) Kaunsa timeout pehle firega — httpx ka 5.0 s, ya sink ka pool_timeout?
    Aur wo farak Relay ke logs me kis shakal me dikhega?
(c) Outbox row ka FOR UPDATE lock kitni der held rahega — aur kya wo HTTP
    timeout ke saath release hota hai? Mechanism.
(d) Aur asli sawaal: jo error Relay ke log me aayegi, usko padh kar kya tu
    asli cause (receiver ke DB me ek uncommitted row ka lock) tak pahunch
    sakta hai? Haan/nahi. Agar nahi, to kaunsi ek line log me hoti to
    pahunch jaata?
```

---

## PART C — Verification

Har check ke saath ek sawaal: **kaunsa galat implementation isko bhi pass kar dega?** Aur Din 3 ka naya sabak —
**check ka subject naam se likho, sirf property nahi.** `C3` Din 3 pe ek naye nau-line script se satisfy ho gaya
tha jabki bug wali script me bug bacha raha.

### C1 — Pool premise actually observe hui, sirf set nahi hui

Ye aaj ka sabse important gate hai, kyunki **`P-45` ka poora point yahi hai** aur teen numbers isi pe khade hain.

| Observation | Config set nahi hua (var galat shell me) | Config set hua, honour nahi hua | **Sahi** |
|---|---|---|---|
| `resolved_db=… pool=2+0` log me | ❌ (`pool=5+10` aayega) | ✅ | ✅ |
| `pg_stat_activity` peak count `≤ 2` | ❌ | ❌ | ✅ |
| teesra `/slow-hold` **fail** karta hai | ❌ (teeno pass honge) | ❌ | ✅ |

**Teeno record karo.** Pehli row akeli pass karna kaafi **nahi** hai — wo Week 4 Din 5 ka exact haal hai, aur
wahi `P-45` ka gate hai. **Aur teesri row wo differential hai jo doosri row ke instrument pe bharosa nahi
karta.**

### C2 — Latency numbers ka bound identify hua, sirf value nahi

| Check | Expected | Kya galti pakadta hai |
|---|---|---|
| Step 2 ka elapsed `pool_timeout` ke **paas** hai, `seconds` ke nahi | value + naam | agar elapsed `≈ seconds` hai to tu saturation nahi, **completion** naap raha hai |
| `RELAY_POOL_TIMEOUT` badal ke ek doosra run | elapsed us naye value ko **follow** kare | ek number jo config badalne pe nahi hilta, wo us config ko naap hi nahi raha |
| Exception class poora naam se | `sqlalchemy.exc.…` | `except TimeoutError` builtin pakadta hai, SQLAlchemy ka nahi — do alag classes |
| `echo=True` har latency number ke saath likha hua | maujood | wo line na ho to Din 6 pe ye numbers `echo=False` wale se compare ho jaayenge |

**Doosri row aaj ka asli differential hai:** ek run ek number deta hai; **do run at do configs** batate hain
ki number kis cheez ka hai.

### C3 — Discriminator teen causes ko alag karta hai, aur ye teen requests hai, ek nahi

| Request | pool starvation | DB down | process dead |
|---|---|---|---|
| DB ko na chhune wala endpoint | **`200`** | **`200`** | connection refused |
| `/healthz` | timeout / `5xx` | error | connection refused |
| `pg_stat_activity` count for `app_name` | **`= pool ceiling`** | `0` | `0` |

**Teen requests teeno causes ko alag karti hain; ek nahi kar sakti.** Aur ye Din 2 ke `413` gate ka ulta shape
hai — wahan ek request do implementations ko alag nahi kar payi thi.

**Aur ek control jo iss table ko naapne layak banata hai:** teeno requests **saturation ke bina** bhi ek baar
chalao. Agar `/healthz` saturation ke bina bhi fail kar raha hai, to poori table ka matlab badal jaata hai.

### C4 — Step 4 ka do-snapshot differential

| Check | Connection disconnect pe free hoti hai | Connection `seconds` tak held rehti hai |
|---|---|---|
| snapshot @ disconnect + `1 s` | `0` rows `active` | **`1` row `active`** |
| snapshot @ `seconds` + `2 s` | `0` rows | `0` rows |
| **dono snapshots zaroori hain** | — | pehla akela *"koi row nahi"* ko *"kabhi thi hi nahi"* se alag nahi karta |

**Doosra snapshot akela dono cases me identical hai.** Farak sirf pehle me hai — isliye do chahiye.

### C5 — Retention, aur iss baar check ka subject naam se

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| **`labs/w5d4_pool_probe.py`** — wahi file, do baar chalao, `logs/` me files gino | `2` | `1` — aur ye Din 3 ka exact miss hai: wahan check ek **doosri** script se pass ho gaya tha |
| Us file me run-id ka format | `%Y%m%d_%H%M%S_%f` | `%Y%m%d_%H%M%S` — ek hi second me collide karta hai `[MEASURED 2026-09-26]` |
| `git ls-files labs/w5d4_*` | `≥ 1` — `D-32` ke hisaab se `labs/` tracked hai | `0`, ya `scratch/` me padi hui |
| Har latency number ek file me, `Write-Host` pe nahi | har number | `P-53` ka rule, aur ye teesra din hai |

### C6 — `src/` aaj bhi nahi badla, aur `P-54` ka surface nahi badla

| Check | Expected |
|---|---|
| `git diff --name-only HEAD -- src/` | `0` |
| Paanch `src` hashes | Step 0 ke barabar |
| `alembic heads` file ka content | exactly `w4d4_sink_unique (head)` — **exit code pe nahi, string pe** |
| `except BaseException` in `src/` | `0` |
| `git ls-files -- "*_KEY.md"` · `ls-tree` text filter · `*.pyc` control | `0` · `0` · `1` |
| `git status --porcelain` me `ANSWERS\|DESIGN\|PROBLEM\|PROPERTY` | **`20`** — kam ya zyada dono galat hain |

**Aakhri row ek do-taraf ka gate hai:** `< 20` matlab kuch stage ho gaya (one-way door), `> 20` matlab ek naya
unclassified artifact ban gaya (`P-54` ka same shape dobara).

### C7 — Evidence DB untouched

| Check | Expected |
|---|---|
| Nau counters delta | `0` |
| `pg_database LIKE 'relay\_%'` | `0` rows — `relay_w5d4` drop ho chuki ho |
| `DIN_04_PREDICTIONS_FROZEN.md` | maujood, hash Step 0 aur Step 7 dono pe liya hua |
| Aaj ka har number | `[MEASURED 2026-09-27]` label ke saath, aur ek file ka naam saath me |

### C8 — Teen cheez jo aaj quote nahi honi chahiye

| Check | Kyun |
|---|---|
| `3.0055 s`, `3.1618 s`, `2.8133 s` **bina** aaj ke re-take ke | teeno `[REPORTED, NOT VERIFIABLE]` hain (`P-45`). Aaj unhe replace karna hai ya label ke saath rakhna hai — quote karna nahi |
| `35.191 s` `fault_to_reclaim` ke naam se | wo *lease-anchor to reclaim* hai. `P-53` |
| Din 3 ka *"`7` ignore-matched tracked files"* | honest count `1` hai. `.env.example` ek **negation** match tha |

---

## PART D — Scope guard

Aaj ye **nahi** banega. Har ek ka owner naam se:

| Kya | Owner | Kyun aaj nahi |
|---|---|---|
| Koi bhi `src/` edit | **Week 6** | Aaj ka `C6` gate hi yahi hai. `echo=True` band karna bhi ek `src/` edit hai, aur wo bhi aaj nahi |
| `P-44` ka **code** fix | Step 6 me naam se chuna gaya din | Fix Step 2/3/5 ki measurement kamzor karta hai. Order load-bearing hai |
| `P-51` ka code fix | **Week 6** | Din 3 pe decide hua. Aaj ka koi change isko **chhuta nahi** |
| `P-54` ke teen faisle (`ANSWERS`, `DESIGN`/`PROBLEM`/`PROPERTY`, rule ka shape) | **Din 6** | Aaj wo `20` untracked files ek **gate** hain, ek to-do nahi. Unhe chhedna `C6` ki aakhri row todta hai |
| `docs/planning/` aur `docs/roadmap/` ko public karna — `47` broken links | **Din 6, `D-32` ke final text me** | Wo bhi `P-54` ka hissa hai aur publishing one-way door hai |
| `.pyc` ko `rm --cached` | **Din 6** | Faisla *"`HEAD` se hataao aur maano blob `01f42c6` me rahegi"* hai, *"clean karo"* nahi |
| `step5_preping_bench.py` ka `_%f` fix | **jo bhi usko agla chalaye** | Aaj wo bench nahi chal raha. Naya probe pehle din se `_%f` ke saath likho |
| Koi bhi migration | **Week 6** | `alembic heads` gate. Aaj ek head, ek hi rahega |
| `/slow-hold?seconds=100000` chalana | **kabhi nahi** | Wo ek connection `27` ghante hold karega. Step 4 ka sawaal `seconds=20` se poora answer ho jaata hai |
| `logs/` ki purani files delete karna | **Din 6 ke baad** | `147` files. Retention ka doosra half abhi likha nahi gaya |
| History rewrite (`filter-repo`, force push) | **kabhi nahi, bina explicit faisle ke** | `Q3(b)` Din 3 pe measure ho chuka hai |
| `D-30` ka close, `D-32`/`D-33` ka final text | **Din 6** | Aaj notes banti hain |
| README rows 7/9, promise #4 ka verdict | **Din 6** | |
| `P-36` (`os._exit` boundary se nikal jaata hai) | **Month 3** | Aaj ka koi change isko **chhuta nahi** |
| Handler timeout, naye tests, `statement_timeout` | **Month 3 / Week 6** | `statement_timeout` Step 6 ke option me **naam se** aata hai — wo uska faisla hai, implementation nahi |

**Cut order, agar time khatam ho:** Step 5 → Din 5 (slot khaali hai) · phir Step 4 · phir Step 6 ka teesra
sub-point. **Step 1 kabhi cut nahi hoga** — uske bina Step 2 aur Step 3 ke numbers `P-45` wali haalat me hi
rehte hain, aur poora din bekaar ho jaata hai.

---

*Wapas:* [`../../logs/WEEK_05.md`](../../logs/WEEK_05.md) ·
*Din 3 BRIEF:* [`DIN_03_BRIEF.md`](DIN_03_BRIEF.md) ·
*Seal:* `DIN_04_PREDICTIONS_FROZEN.md` (Step 0 pe banegi)
