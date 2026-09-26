# WEEK 5 · DIN 2 — `2026-09-25` — Baaki teen process, ek supervisor, aur `pool_pre_ping` ki re-pricing

**Budget `140 min` · Layer L2 · `P-43` ka doosra half**
**Aaj ke baad `P-43` band hona chahiye — ya uske bache hue hisse ka naam aur owner hona chahiye.**

> **Kal ka ek natija poore din ka shape decide karta hai.** Kal claim poll pe boundary lagi aur worker ek
> `26.373 s` outage se zinda nikla. Phir Step 6 me DB ko handler ke **baad** aur mark se **pehle** roka gaya,
> aur worker phir bhi mar gaya — `worker.py:305`, matlab `session.execute(mark_stmt)`.
> **Boundary ne crash hataya nahi. Usne crash ko agle unguarded statement pe shift kar diya.**
>
> Aur ek number jo aaj ka asli target hai: reaper launch se reclaim tak `3.44 s` lage — **par wo recovery
> latency nahi hai, wo process-launch latency hai.** Lease reaper ke exist karne se `~64 s` pehle expire ho
> chuki thi, kyunki reaper outage me marta hai aur usko koi restart nahi karta. **Aaj ke code me fault se
> reclaim tak ka time unbounded hai**, aur wo Week 4 Din 5 ke `7.9 s` wala trap exactly dobara hai.
>
> **Isliye aaj ka Step 4 (supervisor) cut nahi hota.** Baaki sab pe order lagi hui hai; wo step nahi.

---

## PART A — Steps

### Step 0 — 10 min: bench, aur do document defects jo gate ke input hain

```powershell
cd d:\PROJECTS\relay
git status --short
git diff --stat -- src/ docker-compose.yml
git rev-parse HEAD:src
.\.venv\Scripts\python.exe -m alembic heads
(Get-Process python -ErrorAction SilentlyContinue | Measure-Object).Count
```

Nau counters evidence DB `relay` pe — **expected `133 | 145 | 19 | 4 | 7 | 39 | 5 | 0 | 1`**, delta `0`.

**Do cheez `git diff` me already hain aur unhe dekhna aaj ke Step 4 se pehle zaroori hai:**

- `docker-compose.yml` me ek `external: true` named volume add ho chuka hai (`P-49`). **Aaj Step 4 usi file me
  likhta hai** — pehle diff padho, warna do changes ek unattributable diff ban jaayenge.
- `src/worker.py` me kal ki claim boundary hai. Aaj usi function me do jagah aur likhni hai.

**Aur do document defects theek karo — dono gate ke input hain, cosmetic nahi:**

| Kya | Kya galat hai | Kyun ye gate ka input hai |
|---|---|---|
| `planning/WEEK_05.md` ka shared context | job `128` `running\|2\|2` likha tha; measured `succeeded\|4\|4`. **Ye kal theek kar diya gaya — sirf verify karo** | Roz ka bench inn rows ko assert karta hai. Galat expected value ka matlab gate **sahi tareeke se fail nahi kar sakta** |
| `docs/daily/week_05/DIN_01_PREDICTIONS_FROZEN.md` | exist nahi karti | Kal ke `Q1`–`Q5` isliye `not scored` hain. **Aaj ka frozen file Step 1 se pehle banna hai**, warna aaj bhi wahi hoga |

**Executable end:** nau counters ka output, aur **aaj ka `DIN_02_PREDICTIONS_FROZEN.md` likha aur hash liya
hua** — Part B ke paanch jawab, `idk` included.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `git rev-parse HEAD:src` | `src/` ke poore content ka ek tree hash; do waqt pe compare karke pata chalta hai koi file badli ya nahi |
| `external: true` (compose volume) | Compose us volume ko **banayega nahi**, sirf attach karega. Na mile to `up` fail hota hai |
| gate ka input | wo expected value jiske against ek check compare karta hai. Galat input wala check pass/fail dono galat de sakta hai |

---

### Step 1 — 20 min: heartbeat ka death point — **pehle measure, edit baad me**

Kal ka Step 6 `payload {"seconds": 8.0}` pe chala tha, **deliberately** `HEARTBEAT_INTERVAL_SECONDS = 10` ke
neeche, taaki maut ka point clean rahe. Matlab ek raasta aaj tak chala hi nahi hai.

`src/worker.py` padho, teen cheez naam se locate karo — **aur padhna hi kaafi hai, chalana Part B ke baad:**

1. `send_heartbeat` ka `except asyncio.TimeoutError:` branch — usme kya chalta hai
2. `run_worker` ka `finally:` block jo handler ke around hai — usme kya `await` hota hai
3. Python ka rule: `finally` ke andar raise hui exception ke saath **kya hota hai** jab usi `try` ka
   `except Exception` already handle kar chuka ho

**Run (edit kuch nahi):** ek job `type=effect`, `payload {"seconds": 25.0}` — heartbeat interval se **zyada**.
Worker chalao. Claim aur `side_effects` COMMIT dekho. Uske **`3 s` baad** `docker compose stop db`. Phir
`~35 s` ruko.

**Executable end — chaar cheez, aur teesri wali aaj ka naya number hai:**

- worker zinda hai ya nahi
- stderr ka **deepest application frame** — kaunsi file, kaunsi line, kaunse function me
- wo line `305` se **pehle** hai ya **baad** — matlab maut mark tak pahunchi bhi ya nahi
- `jobs` row ka `claimed_at`: claim ke waqt ka hai, ya kisi heartbeat ne usko aage badhaya

Logs: `logs/w5d2_step1_worker.{stdout,stderr}.log`. Disposable DB `relay_w5d2`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `asyncio.Task` ka exception | ek task ke andar ki exception task ko *done-with-exception* bana deti hai; wo raise sirf tab hoti hai jab koi us task ko `await` kare |
| `finally` | wo block jo `try` ke exit hone pe chalta hai, exception aayi ho ya na aayi ho |
| deepest application frame | traceback ka wo sabse andar wala frame jo **teri** file me hai, library me nahi |
| `claimed_at` | lease ka anchor. Heartbeat isko `now()` pe refresh karti hai; reaper `claimed_at + LEASE_DURATION_SECONDS` dekhta hai |

---

### Step 2 — 30 min: worker ke do bache hue statements, aur mark ka faisla

**Ye din ka sabse mehenga faisla hai aur iska koi ek "sahi" jawab nahi hai.** Do jagah boundary chahiye:

1. **Heartbeat ka DB call** — Step 1 ne dikha diya hoga ki wo kahan girta hai
2. **Terminal mark block** — `worker.py:305`, kal measured

Mark ke liye **do options hain aur dono ki keemat hai.** Kal ki measurement ne unme se ek ki keemat le li:

| Option | Kal ka measured result | Kya abhi nahi pata |
|---|---|---|
| **Mark kho do** — catch karo, log karo, loop continue | `attempts = 2`, `side_effects = 1`, `seq = 2`, `execs = 2`, `succeeded`. Ek fault = **do attempts** | — |
| **Mark retry karo** — DB wapas aane tak | — | Retry ke doran **lease ka kya hota hai**, aur kya reaper job ko beech me hi nikal le jaata hai. **Part B ka Q2** |

**Ek teesra option jo naam se likhna chahiye:** mark ko **bounded** retry karo — jab tak lease bachi hai, uske
baad chhod do. Ye pehle do ke beech me hai aur uska cost dono se alag hai.

**Faisla tera hai.** Gemini se options aur unke costs discuss kar sakta hai; **pick usse nahi poochna.**

**Executable end:** ek normal job end-to-end `succeeded` (matlab kuch toota nahi), **aur** Step 1 ka wahi run
dobara — ab worker zinda rehna chahiye. Dono ke logs: `logs/w5d2_step2_*`.

**Ek cheez jo mat karna:** `BaseException`. Aur ek aur: mark ke `except` me **naked `await
session.rollback()`** — DB down hai to wo bhi fail karega. Claim boundary me ye problem nahi thi aur **kyun
nahi thi, wo Q2 ka hissa hai.**

**Terms used in this step**

| Term | Kya hai |
|---|---|
| terminal mark | wo `UPDATE` jo job ko `succeeded`/`failed`/`dead_letter` pe le jaata hai, `(status, claim_generation)` gate ke saath |
| lease remainder | `LEASE_DURATION_SECONDS` minus wo waqt jo `claimed_at` se guzar chuka hai. Server ke wall clock pe chalta hai, activity pe nahi |
| bounded retry | ek retry jiski limit **attempts** nahi, **ek external condition** hai (jaise "jab tak lease hai") |
| pinned worker | wo worker jo ek job pe atka hai aur doosra kaam nahi le sakta |

---

### Step 3 — 25 min: reaper aur dispatcher — ek shape, do blast radius

Dono me boundary lagni hai aur **dono ek jaisi nahi hai.** Ye step tab tak khatam nahi jab tak ye farak likha
na jaaye.

**`src/reaper.py`** — `run_reaper()` ka loop: `while not SHUTDOWN_REQUESTED: await reap_stuck_jobs(); await
asyncio.sleep(...)`. **Usme koi `try` hai hi nahi.** Reaper ka kaam read + ek `UPDATE` hai, dono ek transaction
me, aur fail hone pe kuch nahi hota — agla pass dobara dekh lega.

**`src/dispatcher.py`** — shape same dikhti hai aur **teen cheez alag hai**, aur teeno padhni hain:

1. Uska `except Exception` **sirf** `client.post(...)` ko wrap karta hai, DB ko nahi
2. Wo `FOR UPDATE SKIP LOCKED` ka row lock **HTTP call ke across** hold karta hai (`timeout=5.0`)
3. HTTP fail hone pe wo `attempts` badhata hai — **par wo increment persist hone ke liye COMMIT chahiye**, aur
   COMMIT unguarded hai

**Executable end:**

- Reaper: ek outage ke doran zinda rahe, aur outage ke **baad** ek stale lease reclaim kare. Uska
  `[reclaim] ... matched=1` line log me ho. `logs/w5d2_step3_reaper.*`
- Dispatcher: ek outage ke doran zinda rahe, aur uske baad ek pending outbox row deliver kare.
  `logs/w5d2_step3_dispatcher.*`
- **Aur ek likhi hui line:** dispatcher ka blast radius reaper se kaise alag hai — HTTP success ke **baad** aur
  COMMIT se **pehle** DB marne pe kya hota hai. Ye Q3 hai.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| blast radius | ek failure ka asar kahan tak jaata hai — ek row, ek process, ya ek doosri service |
| row lock across a network call | ek DB lock jo ek HTTP request ke poore duration tak hold hota hai. Lock ka lifetime ab ek remote service pe depend karta hai |
| `dispatched_at` | outbox row ka marker ki delivery ho chuki hai. Ye **COMMIT** hone pe persist hota hai, HTTP `200` milne pe nahi |
| at-least-once | wo guarantee jisme delivery **kam se kam** ek baar hoti hai, aur do baar bhi ho sakti hai |

---

### Step 4 — 30 min: supervisor — **aur ye step cut nahi hota**

Kal ka `3.44 s` ek insaan ke enter dabane se shuru hua tha. **Jab tak koi process ko wapas nahi laata, boundary
ke baad bhi recovery ka koi bound nahi hai.**

**Ek scope defect jo plan me hai aur usko naam se dekhna hai:** `WEEK_05.md` kehta hai *"`docker-compose.yml` me
`restart:` policy, **paanchon process pe**"*. **Relay ke paanch process compose me nahi hain** — `docker
compose ps` me sirf `db` hai. Matlab `restart:` likhne se pehle un processes ko compose me **laana** padega, aur
wo ek alag aur bada change hai (image ya mount, aur `DATABASE_URL` ka host `localhost:5433` se `db:5432` ban
jaata hai).

**To pehle ek faisla, phir measurement. Teen options, teeno ka cost:**

| Option | Kya karna padega | Cost |
|---|---|---|
| (a) paanch process compose me + `restart: unless-stopped` | Dockerfile ya base image + source mount, network rename, `.env` ka `DATABASE_URL` badalna | Production ka sahi jawab. Aaj ke budget se bahar, aur wo `DATABASE_URL` change kal ke saare logs ko non-reproducible bana deta hai |
| (b) host pe ek chhota supervisor — ek wrapper jo process exit hone pe usko dobara launch kare | ~15 lines, `src/` ke bahar (`scripts/`) | Aaj measure ho sakta hai. Windows-specific, aur wo production artifact nahi hai |
| (c) `restart:` sirf `db` pe | ek line | Relay ke kisi process ko restart nahi karta. Matlab aaj ka sawaal answer nahi hota |

**Faisla tera hai.** Par jo bhi chune, **aaj ka measurement wahi hona chahiye jo Month 1 me kabhi nahi hua:
worker aur reaper dono ek hi outage me maro, aur dekho kaun wapas aata hai.** Wo README ka row 9 hai aur uska
verdict abhi bhi `[NO EVIDENCE]` hai.

**Executable end — chaar number, aur teesra wala aaj ka asli deliverable hai:**

| Number | Kaise nikalega |
|---|---|
| `restarts` | outage ke doran supervisor ne kitni baar launch kiya |
| `restart_to_first_claim` | supervisor ka launch → log me pehla successful claim/poll. **Aur uska source ek file me likho, console pe nahi** (`P-50`) |
| **`fault_to_reclaim`** | job ke `claimed_at` se us moment tak jab reaper ne usko `pending` kiya. **Yahi wo number hai jo kal `unbounded` tha** |
| `crash_loop` behaviour | DB ko **down hi rehne do `~30 s`**. Supervisor kitni baar relaunch karta hai? Koi backoff hai? |

**Ek cheez jispe dhyaan dena hai aur wo Step 2 ke order ki wajah se hai:** Step 2 ke baad worker poll **aur**
mark **aur** heartbeat, teeno pe guarded hai. To supervisor ko fire karne ke liye ab koi wajah bachi hai ya
nahi — ye khud ek finding hai, aur wo Q4 ka doosra half hai.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| supervisor | wo cheez jo ek process ke exit hone pe usko dobara start karti hai. `restart:` policy, `systemd`, ya ek wrapper loop |
| `restart: unless-stopped` | Compose policy: container exit hone pe restart karo, **siwaay** jab user ne khud stop kiya ho |
| crash-loop backoff | restart ke beech ka badhta hua wait, taaki ek permanently-down dependency restart storm na bane |
| `fault_to_reclaim` | fault ke moment se us moment tak jab row dobara claimable ho jaati hai. **Ye system ka recovery bound hai, ek process ka launch time nahi** |

---

### Step 5 — 25 min: `pool_pre_ping` — ab premise sach hai

Week 4 Din 5 ne `pool_pre_ping=True` ko reject kiya tha iss stated ground pe ki worker/reaper *"polling loops
with built-in exception handling"* hain. **Us waqt wo handling exist nahi karti thi. Aaj karti hai.** To ye
faisla dobara hota hai, aur uska jawab palat sakta hai — **ya nahi bhi.** Dono outcomes valid hain.

Do cheez measure karni hain, aur unhe mila dena aaj ka sabse aasan tareeka hai galti karne ka:

1. **Outcome** — `pre_ping` ke saath aur bina, wahi `~25 s` outage pe, `poll_failures` ka number
2. **Cost** — per-checkout ek extra round trip. Kitne ms? **Ye ek asli measurement hai, ek guess nahi.**

**Ek teesri cheez jo outcome se zyada important hai:** `pool_pre_ping` `src/database.py` ke ek hi
`create_async_engine` pe set hoti hai, aur **paanchon process wahi module import karte hain.** Matlab ek flag,
paanch process. Worker `~0.5` checkouts/second karta hai; API **per request** karti hai. **Cost dono pe barabar
nahi padta, aur decision ek hi hai.**

**Executable end:** ek table — `pre_ping` off vs on, `poll_failures`, aur per-checkout cost `ms` me, `n` ke
saath. `logs/w5d2_step5_preping.log`. Aur ek line: **kaunsa chuna aur kis number ki wajah se.** Ye `D-31` hai.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `pool_pre_ping` | SQLAlchemy ka flag: **checkout pe** ek halki ping bhejta hai; fail hone pe connection discard karke nayi banata hai |
| checkout | pool se ek connection lene ka act. Worker ka har poll ek checkout hai |
| stale connection | pool me padi connection jo application ke hisaab se open hai par server side pe band ho chuki hai |
| round trip | ek request client se server tak jaake wapas aane ka waqt |

---

### Step 6 — 10 min: close bench

```powershell
git rev-parse HEAD:src      # Step 0 se badla hua — aaj teen files change hui hain
.\.venv\Scripts\python.exe -m alembic heads   # ek head. Aaj koi migration NAHI
(Get-Process python -ErrorAction SilentlyContinue | Measure-Object).Count   # 0
```

Nau counters — delta `0`. `SELECT datname FROM pg_database WHERE datname LIKE 'relay\_%'` — `0` rows.
`relay_w5d2` drop karo. **`logs/w5d2_*` rakho**, aur `logs/w5d1_*` + `logs/w5d1r_*` bhi — Din 3 tak teeno
zinda rehne hain.

---

## PART C — Verification

Har check ke saath ek sawaal: **kaunsa galat implementation isko bhi pass kar dega?**

### C1 — Normal path teeno process pe toota nahi

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Ek job end-to-end `succeeded` | claim → execute → mark, ek log me | Job `pending` pe atki — boundary ne claim kha liya |
| Reaper ek stale lease reclaim karta hai | `[reclaim] ... matched=1` | `candidates=0` forever — boundary ne `reap_stuck_jobs()` ko hi swallow kar liya |
| Dispatcher ek outbox row deliver karta hai | `[dispatch] ... status=dispatched` | `undispatched` row bachi rahi |
| `except BaseException` in `src/` | `0` matches | graceful shutdown aur `CancelledError` dono toot gaye |

### C2 — "Zinda hai" akela kaafi nahi hai, aur kal isne teen implementations ko alag kiya tha

Kal ka C2 abhi bhi lagoo hai aur **aaj usme ek chauthi row add hoti hai**, kyunki aaj teen process hain:

| Observation | `except: pass` | catch, session poisoned | catch, par **reaper** ka `UPDATE` swallow | **Sahi** |
|---|---|---|---|---|
| Process outage ke baad zinda | ✅ | ✅ | ✅ | ✅ |
| Recovery ke baad ek successful **claim** | ✅ | ❌ | ✅ | ✅ |
| Recovery ke baad ek successful **reclaim** (`matched=1`) | ✅ | ❌ | ❌ | ✅ |
| `poll_failures` `<= outage / (POLL_INTERVAL + failure_cost) + 2` | ❌ | ✅ | ✅ | ✅ |

**Chaaron record karo.** Teesri row aaj naya add hui hai aur wo sirf reaper ke liye hai — ek zinda reaper jo
kabhi reclaim nahi karta, `Get-Process` ke liye success dikhta hai.

### C3 — Supervisor ka check teen requests wala hai, ek nahi

**Ye aaj ka sabse important gate hai**, kyunki *"process wapas aa gaya"* **do** galat setups ko bhi pass karta
hai:

| Observation | supervisor bina backoff, DB permanently down | supervisor jo start hota hai par claim nahi karta | **Sahi** |
|---|---|---|---|
| Outage ke baad process maujood | ✅ | ✅ | ✅ |
| `fault_to_reclaim` ek **finite** number | ✅ | ❌ | ✅ |
| DB `30 s` down rakhne pe `restarts` **bounded** | ❌ — restart storm | ✅ | ✅ |

**Teesri observation ke liye DB ko jaan-boojh ke down rehne dena padega.** Wo run skip karna gate ko decorative
banata hai.

### C4 — Numbers ke saath unka `n`, unki condition, **aur unka file-based source**

| Number | Kya likhna hai saath me |
|---|---|
| `poll_failures` (dono `pre_ping` arms) | outage length, `POLL_INTERVAL_SECONDS`, `failure_cost`, aur `n` |
| `restart_to_first_claim` | supervisor launch ka wall clock, **aur wo kis file me likha hai** |
| `fault_to_reclaim` | `claimed_at` ka value aur reclaim line ka `DB_TIME` — dono log se |
| `pre_ping` per-checkout cost | `n`, aur kya wo worker ke `0.5`/s pe measure hua ya API ke per-request pe |

**`P-50` ki wajah se ek naya rule, aur wo aaj se lagoo hai:** koi bhi harness apne log ko `Remove-Item` **nahi**
karega, aur koi bhi wall clock sirf `Write-Host` pe **nahi** jaayega. Kal ka sabse valuable chain isi do galtiyon
se gaya.

### C5 — Aaj ke numbers kal ke numbers ko replace nahi karte

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Kahin bhi `3.44 s` recovery bound ki tarah quote nahi hua | grep zero match | Wo process-launch latency hai. Kal ka log naam se rok lagata hai, aur `7.9 s` pe bhi wahi rok hai |
| Kahin bhi `7.9 s` quote nahi hua | grep zero match | Wahi galti, Week 4 se |
| Aaj ka har number `[MEASURED 2026-09-25]` label ke saath | har line pe label | Bina label wo kal ke `[REPORTED, NOT VERIFIABLE]` recovery numbers ke saath mix ho jaayega |
| `recovery_to_first_claim` ke kal ke `1.668 s` / `2.176 s` **abhi bhi** `[REPORTED, NOT VERIFIABLE]` hain | label maujood | Aaj ka naya number unka **replacement** hai, **confirmation** nahi |

### C6 — Evidence DB untouched, aur frozen seal exist karti hai

| Check | Expected |
|---|---|
| Nau counters delta | `0` |
| Job `136` | `136\|running\|1\|1` |
| Job `108` · Job `128` | `dead_letter\|4\|0` · `succeeded\|4\|4` |
| `pg_database LIKE 'relay\_%'` | `0` rows |
| `alembic heads` | ek — `w4d4_sink_unique` |
| **`DIN_02_PREDICTIONS_FROZEN.md`** | **maujood hai**, aur uska hash C0 aur C6 dono pe liya gaya. Kal ye file thi hi nahi |
| `git rev-parse HEAD:src` | Step 0 se **badla hua** |

---

## PART D — Scope guard

Aaj ye **nahi** banega. Har ek ka owner naam se:

| Kya | Owner | Kyun aaj nahi |
|---|---|---|
| Retention rule / `.gitignore` / `logs/evidence/` | **Din 3** | `P-50` ne uska scope badal diya hai — ab usme harness transcripts bhi aate hain. Aaj ke logs **delete nahi** karne |
| `requirements.txt` pins | **Din 3** | Retention decision ke saath, ek hi step |
| `pg_dump` / evidence backup ka faisla | **Din 3** | `P-49` ka doosra half. Ye *"evidence survive karti hai"* ka sawaal hai; Din 3 ka `D-32` *"evidence public hoti hai"* ka hai. Dono ek hi din, do alag fields |
| Pool exhaustion ke numbers, queue-lag series | **Din 4** | Din 3 ke retention rule pe depend karte hain |
| `/slow-hold` ka faisla | **Din 4, Step 5** | Uska fix Din 4 ke Step 2 ki measurement ko weak karta hai, to measurement pehle |
| Do-reaper run (`D-29` ka weakest field) | **Din 5 ka khaali slot** | Blog post `2026-09-19` pe publish ho chuki hai, to Din 5 ka slot free hai. **Us slot ka faisla Din 6 pe hoga, aaj nahi** |
| Handler timeout | **Month 3** | Ek sawaal pehle chahiye: *timed-out handler ka status kya hai?* |
| `P-36` (`os._exit` boundary se nikal jaata hai) | **Month 3** | Aaj ka koi bhi change isko theek **nahi** karta, aur wo likhna zaroori hai |
| Naye tests | **Month 3, Week 6 ke baad** | Week 6 ka fake provider pehli cheez hai jo integration test possible banati hai |
| README rows 7/9, promise 4 ka verdict | **Din 6** | Aaj ke baad row 9 ka verdict badal sakta hai — **par usko likhna Din 6 ka kaam hai** |
| `D-30` ka `Supervisor` section aur uska close | **Din 6** | Aaj us section ke liye **notes** banti hain. Entry Din 6 pe close hoti hai |
| Koi bhi migration | **iss hafte nahi** | `alembic heads` gate hai |
| LLM, provider, Redis, rate limit, token, budget | **Weeks 6–8** | [`../../planning/MONTH_02.md`](../../planning/MONTH_02.md) Section 0 |

### Budget ki honest arithmetic

Step times ka jod: `10 + 20 + 30 + 25 + 30 + 25 + 10 = 150 min`. Budget `140`. **Overflow `+10`.**

**Cut order, aur wo naam se hai:**

1. **Pehla cut — Step 5 (`pool_pre_ping`) Din 3 ke opening slot me slip hota hai.** Din 3 `125 min` ka hai
   against `135`, to wahan jagah hai. Uska precondition (*boundary exist karti hai*) Step 2/3 ke baad satisfy ho
   jaata hai, aur wo Din 3 pe bhi satisfy rahega.
2. **Step 4 cut NAHI hota.** Wo promise #4 ka process half hai aur aaj ke din ki poori wajah wahi hai.
3. Agar phir bhi overflow hai: Step 3 ka **dispatcher** half slip karo, reaper half nahi — reaper `fault_to_reclaim`
   ke raaste me hai, dispatcher nahi.

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  PART B — PREDICTION QUESTIONS                                               ║
║  Ye block Gemini ko paste NAHI hota.                                         ║
║  Jawab apne head se, us step se PEHLE,                                       ║
║  docs/daily/week_05/DIN_02_PREDICTIONS_FROZEN.md me. Phir hash lo.           ║
║  Kal wo file exist hi nahi karti thi, isliye Q1-Q5 `not scored` gaye.        ║
║  `idk` ek valid jawab hai aur wo 0 score karta hai — aur wo accurate hai.     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Q1 (Step 1 se pehle)
    Handler `25 s` chalta hai, HEARTBEAT_INTERVAL_SECONDS = 10, aur DB claim ke `3 s`
    baad marta hai. Worker marega ya nahi? Agar marega, to `worker.py:305` (mark) se
    PEHLE ya BAAD me? Ek line number ya ek function ka naam likho.
    Aur: us job ka `claimed_at` claim ke waqt ka hoga, ya kisi heartbeat ne usko aage
    badhaya hoga?

Q2 (Step 2 se pehle)
    Maano tu mark ko retry karta hai jab tak DB wapas na aaye.
    Retry ke DORAN job ki lease ka kya hota hai — kaun usko refresh kar raha hai?
    Aur agar ek reaper zinda hai aur lease expire ho jaati hai: wo job ko reclaim kar
    lega ya nahi? Agar haan, to jab DB wapas aaye aur tera retry ka UPDATE chale, uska
    `rowcount` kya hoga, aur worker kaunsi line print karega — `Mark fenced` ya
    `Conflict on mark`? Ek chuno, aur mechanism likho.

Q3 (Step 3 se pehle)
    Dispatcher HTTP `200` le chuka hai. `dispatched_at` set ho gaya hai object pe, par
    COMMIT abhi nahi hua. Ab DB marta hai.
    Boundary lagane ke BAAD: `outbox` row `dispatched` hui ya nahi? Recovery ke baad wo
    row dobara deliver hogi ya nahi? Aur `outbox.attempts` ka number sahi hoga ya kam?
    Aur: delivery ka at-least-once property preserve hua, kharab hua, ya waisa hi raha?

Q4 (Step 4 se pehle)
    Supervisor lag gaya. Worker aur reaper dono ek `25 s` outage me marte hain.
    `restart_to_first_claim` ka ek number likho, aur `restarts` ka ek number likho.
    Aur doosra half, jo number nahi hai: Step 2 ke baad worker poll, mark AUR heartbeat
    teeno pe guarded hai. To supervisor ko fire karne ki koi wajah bachi hai? Agar haan,
    to kaunsi — naam se ek failure.

Q5 (Step 5 se pehle)
    Boundary ab maujood hai. `pool_pre_ping=True` ke saath, wahi `~25 s` outage pe,
    `poll_failures` `5` se `4` hoga, `0` hoga, ya waisa hi rahega? Mechanism likho.
    Aur per-checkout cost ka ek number `ms` me likho.
    Aur teesra: `pre_ping` kal ki DO maut (mark pe aur heartbeat pe) me se kisi ko
    bachata hai? Haan/nahi, aur kyun.
```

---

*Aaj ke measurement ke **baad** kholna:* [`DIN_02_KEY.md`](DIN_02_KEY.md)
*Kal ka log:* [`../../logs/WEEK_05.md`](../../logs/WEEK_05.md) ·
*Plan:* [`../../planning/WEEK_05.md`](../../planning/WEEK_05.md)
