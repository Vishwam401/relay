# WEEK 5 · DIN 1 — `2026-09-14` — Worker ka exception boundary

**Budget `130 min` · Layer L2 · Month 2 ka pehla din**
**Aaj `P-43` ka pehla half band hota hai — aur `P-43` handoff me *"Month 2, and it is the first item"* likha hai.**

**Deliverable:** ek worker jo database restart se **zinda** nikalta hai, aur teen numbers jo Month 1 ne kabhi
nahi liye — failed-poll count, recovery-to-first-claim, aur catch ke baad ka retry behaviour.

> **Aaj ka poora din ek galat line theek karne pe khada hai.** Din 5 ke log me likha hai ki worker ne
> *"exception pakda aur zinda raha."* **Wo jhoot hai.** `w4d5_step5_worker.stderr.log` ka outermost frame
> `worker.py:321 asyncio.run(run_worker())` → `worker.py:185 await session.execute(claim_query)` hai. Process
> mar gaya tha. Aaj wo pehle **dobara produce** hota hai (control), phir fix hota hai.
>
> **Aur ek cheez jo aaj NAHI hogi:** `pool_pre_ping`. Wo Din 2 ka Step 4 hai, aur order load-bearing hai —
> uska jawab boundary exist karne ke baad **palat sakta hai**. Aaj usko chhuna measurement ko spoil karna hai.

---

## PART A — Steps

### Step 0 — 15 min: baseline aur bench

Aaj kuch bhi chhune se pehle nau counters aur tree state.

```powershell
cd d:\PROJECTS\relay
git status --short
git rev-parse HEAD:src
.\.venv\Scripts\python.exe -m alembic heads
Get-Process python -ErrorAction SilentlyContinue | Measure-Object
```

Evidence DB `relay` pe nau counters:

```sql
SELECT
  (SELECT count(*) FROM jobs)             AS jobs,
  (SELECT count(*) FROM job_executions)   AS execs,
  (SELECT count(*) FROM side_effects)     AS effects,
  (SELECT count(*) FROM outbox)           AS outbox,
  (SELECT count(*) FROM sink_deliveries)  AS sink,
  (SELECT last_value FROM side_effects_id_seq) AS eff_seq,
  (SELECT last_value FROM outbox_id_seq)       AS out_seq,
  (SELECT count(*) FROM jobs WHERE status='pending') AS pending,
  (SELECT count(*) FROM jobs WHERE status='running') AS running;
```

**Expected:** `133 | 145 | 19 | 4 | 7 | 39 | 5 | 0 | 1`. Job `136` `running` hai — wo poison pill hai aur
untouched rehta hai.

**Aur ek naya kaam aaj se:** aaj ke saare logs `logs/w5d1_*` naam se rakho aur **delete nahi karna**. `logs/`
abhi bhi gitignored hai; Din 3 usko theek karega, aur tab aaj ke artifacts commit ho payenge.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `git rev-parse HEAD:src` | `src/` directory ke poore content ka ek tree hash — do waqt pe compare karke pata chalta hai ki koi file badli ya nahi |
| bench | ek fixed set of counters jo din ke shuru aur end me padhe jaate hain, delta nikalne ke liye |
| poison pill | ek aisa job jo har execution pe process ko maar deta hai, to wo terminal state tak pahunch hi nahi paata |

---

### Step 1 — 15 min: maut dobara produce karo — aaj ka control

Fix karne se pehle **failure aaj ki machine pe reproduce** hona chahiye. Warna baad ka *"zinda raha"* kis cheez
ke against hai, ye pata nahi.

1. Ek disposable database banao — `relay_w5d1`. Evidence DB pe outage **nahi** karna.
2. Us DB pe migrate karo, ek `pending` job daalo.
3. Worker chalao, `python -u`, stdout **aur** stderr dono file me: `logs/w5d1_step1_worker.{stdout,stderr}.log`
4. Worker ko idle poll karne do — koi job claim na kare, ya kar ke khatam kar de.
5. `docker compose stop <postgres-service>`. **Wall clock note karo.**
6. `~25 s` ruko. `docker compose start`. Phir wall clock note karo.
7. `~30 s` aur ruko.

**Executable end:** teen cheez record karo —

- `Get-Process python | Measure-Object` — worker process **abhi bhi hai ya nahi**
- `logs/w5d1_step1_worker.stdout.log` ki **aakhri line ka timestamp**
- `logs/w5d1_step1_worker.stderr.log` ka **outermost frame** — file aur line number

**Terms used in this step**

| Term | Kya hai |
|---|---|
| disposable database | ek alag database jo experiment ke liye banti hai aur end pe drop ho jaati hai; evidence DB ko chhuti nahi |
| idle poll | worker ka wo loop jab queue khaali hai — claim query chalti hai, kuch nahi milta, wait, dobara |
| outermost frame | traceback ki **sabse upar** wali line — wo batati hai ki exception kahan tak chadha, kahan raise hua wo nahi |
| control | ek run jo fix se **pehle** liya jaata hai, taaki baad ka result kis cheez ke against hai wo pata ho |

---

### Step 2 — 15 min: exception ka naam pehchano

Boundary likhne se pehle pata hona chahiye ki **kaunsa** exception aata hai. Ek galat class pakadna ek boundary
jaisa dikhta hai aur kuch pakadta nahi.

1. `logs/w5d1_step1_worker.stderr.log` me exception ki **poori class chain** dhoondo — module ke saath
   (`sqlalchemy.exc.X`, aur uske neeche `asyncpg.exceptions.Y` ya `ConnectionResetError`)
2. SQLAlchemy ki class hierarchy me un classes ko locate karo — kaun kiska parent hai
3. Likho: DB down hone ke **do alag moment** hain — (a) connection pehle se open thi aur toot gayi, (b) nayi
   connection banane ki koshish hui aur refuse hui. **Kya dono ek hi class deti hain?**

**Executable end:** ek chhota script `labs/w5d1_exc_probe.py` jo deliberately DB-down state me ek query chalata
hai aur `type(e).__mro__` print karta hai. Do baar chalao — ek baar jab pool me stale connection hai, ek baar
fresh process me. Output `logs/w5d1_step2_exc.log` me.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `__mro__` | Method Resolution Order — ek class ke saare parents ka ordered list. Isse pata chalta hai `except X` kis kis cheez ko pakdega |
| `sqlalchemy.exc.DBAPIError` | SQLAlchemy ka wrapper jo underlying driver (asyncpg) ke exception ko lapet ke deta hai |
| `stale connection` | pool me padi ek connection jo application ke hisaab se open hai par server side pe band ho chuki hai |

---

### Step 3 — 15 min: boundary — sirf claim poll pe

**Sirf claim.** Terminal mark Step 6 me hai aur wo ek **alag** decision hai.

Jo likhna hai wo teen cheez hai, aur teeno naam se:

1. Claim poll ke around ek `try`
2. Exception pakadne ke baad **session ka kya karna hai** — ye ek sawaal hai, aur iska jawab Part B me hai
3. Uske baad loop kya karta hai — ye doosra sawaal hai, aur wo bhi Part B me hai

**Ek cheez jo mat pakadna:** `BaseException`. Graceful shutdown aur `CancelledError` uspe khade hain aur
`P-36` ne dikha diya hai ki `os._exit` unme se bhi nikal jaata hai.

**Executable end:** worker start ho, ek job claim kare, khatam kare, `succeeded` mark ho. Matlab **normal path
toota nahi.** `logs/w5d1_step3_worker.stdout.log`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `BaseException` | Python ke exception tree ka root. `Exception` uska child hai; `KeyboardInterrupt`, `SystemExit`, `asyncio.CancelledError` uske **direct** children hain, `Exception` ke neeche nahi |
| session rollback | SQLAlchemy session ko ek failed transaction se saaf karna, taaki agli query chal sake |
| normal path | wo raasta jisme kuch nahi tootta — aaj ke change ke baad wo pehle jaisa chalna chahiye |

---

### Step 4 — 15 min: wahi outage dobara, ab teen numbers ke saath

Step 1 ka **exactly wahi** sequence. Timing badalni nahi hai — warna comparison nahi banta.

1. `relay_w5d1` fresh karo (drop + create + migrate), ek `pending` job
2. Worker chalao, `logs/w5d1_step4_worker.{stdout,stderr}.log`
3. Idle poll, phir `docker compose stop`. Wall clock.
4. `~25 s`. `docker compose start`. Wall clock.
5. `~30 s`.

**Executable end — teen number, aur teeno pehli baar hain:**

| Number | Kaise nikalega |
|---|---|
| `poll_failures` | outage ke doran log me kitni failed claim attempts hain — **ginо** |
| `recovery_to_first_claim` | DB start ka wall clock → log me pehla **successful** claim/poll line |
| `alive` | `Get-Process python` — worker abhi bhi hai? |

Aur ek chauthi cheez jo number nahi hai par usse zyada important hai: **DB wapas aane ke baad pehla poll
success hua, ya wo bhi fail hua?** README ka bound isko *"possibly one failed poll"* kehta hai — aaj wo
`[MEASURED]` ban sakta hai.

---

### Step 5 — 15 min: catch ke baad kya — ye ek decision hai

Step 4 ka `poll_failures` number aa gaya. Ab uska matlab dekho.

Teen possible behaviours, aur teeno ka ek measurable cost hai:

| Behaviour | Recovery latency | Cost |
|---|---|---|
| turant retry (`continue`, koi sleep nahi) | sabse kam | ? |
| `POLL_INTERVAL_SECONDS` wait | ? | ? |
| backoff (badhta hua) | ? | ? |

`?` bharne ke liye **do run** chahiye, ek nahi. Jo behaviour Step 3 me likha wo ek arm hai; doosra arm chalao
aur `poll_failures` aur `recovery_to_first_claim` dono compare karo.

**Executable end:** do arms ke numbers ek table me, `logs/w5d1_step5_arms.log`. Aur ek line: **kaunsa chuna aur
kis number ki wajah se.** Ye `D-30` ka `Cost` field banega.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| busy-spin | ek loop jo bina rukе dobara dobara chalta hai — CPU aur (yahan) DB pe load daalta hai |
| recovery latency | wo waqt jo failure khatam hone ke baad system ko normal kaam shuru karne me lagta hai |
| arm | ek experiment ka ek version. Do arms compare karne se ek variable ka effect pata chalta hai |

---

### Step 6 — 15 min: terminal-mark block ka boundary — aur ye claim se alag hai

Claim fail hona **safe** hai: kuch nahi hua, dobara try kar lo. Terminal mark fail hona **alag** hai — handler
already chal chuka hai, side effect already commit ho chuka ho sakta hai.

Do case alag karo:

1. Handler ke **pehle**/claim ke waqt DB gaya → job `pending` hai ya `running` lease ke saath. Reaper ka kaam.
2. Handler ke **baad**, mark se **pehle** DB gaya → `side_effects` + `outbox` commit ho chuke hain, `jobs` row
   `running` hai. Ye README ka row 2 hai aur wo `[MEASURED]` hai — par wahan **process zinda tha**.

**Executable end:** ek run jisme handler ke baad aur mark se pehle DB stop hota hai. Record karo: worker zinda?
`side_effects` count? `jobs` row ka status? Aur — job ka `attempts` kitna hua?

**Terms used in this step**

| Term | Kya hai |
|---|---|
| terminal mark | wo `UPDATE` jo job ko `succeeded`/`failed`/`dead_letter` pe le jaata hai, generation gate ke saath |
| lease | `claimed_at` + `LEASE_DURATION_SECONDS`. Server ke wall clock pe chalti hai, activity pe nahi |

---

### Step 7 — 15 min: close bench

```powershell
git rev-parse HEAD:src      # Step 0 se compare karo — src badla hai, aur wo expected hai
.\.venv\Scripts\python.exe -m alembic heads   # ek head. Aaj koi migration NAHI honi chahiye
Get-Process python -ErrorAction SilentlyContinue | Measure-Object   # 0
```

Nau counters dobara — **delta `0` hona chahiye** (saara kaam `relay_w5d1` pe hua). Phir:

```sql
SELECT datname FROM pg_database WHERE datname LIKE 'relay_%';   -- 0 rows
```

`relay_w5d1` drop karo. `logs/w5d1_*` **rakho**.

---

## PART C — Verification

Har check ke saath ek sawaal: **kaunsa galat implementation isko bhi pass kar dega?**

### C1 — Boundary actually exist karti hai, aur normal path toota nahi

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Ek job end-to-end `succeeded` | Step 3 ka log, ek claim → ek mark | Job `pending` pe atki → boundary ne claim ko hi kha liya |
| `git diff src/worker.py` me `except BaseException` **nahi** hai | grep zero match | `BaseException` pakda gaya → graceful shutdown aur `CancelledError` dono toot gaye |

### C2 — Worker zinda hai — aur ye teen requests wala check hai, ek nahi

**Ye C-gate ka sabse important hissa hai.** *"Worker zinda hai"* akela check **do galat implementations ko bhi
pass** kar deta hai:

| Observation | `except: pass` (busy-spin) | catch, par session rollback nahi | **Sahi** |
|---|---|---|---|
| Process outage ke baad zinda | ✅ pass | ✅ pass | ✅ pass |
| DB recovery ke baad ek **successful claim** | ✅ pass | ❌ **fail** — har agli query `PendingRollbackError` deti hai | ✅ pass |
| `poll_failures` `<= outage_seconds / POLL_INTERVAL + 2` | ❌ **fail** — hazaaron | ✅ pass | ✅ pass |

**Ek observation teeno ko alag nahi kar sakti. Teen kar sakti hain.** Teeno record karo, warna gate decorative
hai.

### C3 — Numbers ke saath unka `n` aur condition

| Number | Kya likhna hai saath me |
|---|---|
| `poll_failures` | outage ki length, `POLL_INTERVAL_SECONDS`, aur `n = 1` |
| `recovery_to_first_claim` | DB start ka wall clock **source** — `docker` ka output ya `psql` ka pehla connect |
| do arms ka comparison | dono arms ki outage length **same** thi — warna comparison invalid hai |

### C4 — Aaj ke numbers Din 5 ke numbers ko replace nahi karte

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Kahin bhi `7.9 s` quote nahi hua | grep zero match | Wo process-launch latency hai, recovery bound nahi. Handoff ne naam se rok lagayi hai |
| Aaj ka har number `[MEASURED 2026-09-14]` label ke saath | har line pe label | Bina label → wo Din 5 ke `[REPORTED, NOT VERIFIABLE]` numbers ke saath mix ho jaayega |

### C5 — Evidence DB untouched

| Check | Expected |
|---|---|
| Nau counters delta | `0` |
| Job `136` | `136|running|1|1` |
| `pg_database LIKE 'relay_%'` | `0` rows |
| `alembic heads` | ek — `w4d4_sink_unique` |
| `git rev-parse HEAD:src` | Step 0 se **badla hua** (aaj `src/` change hua hai) |

---

## PART D — Scope guard

Aaj ye **nahi** banega. Har ek ka owner naam se:

| Kya | Owner | Kyun aaj nahi |
|---|---|---|
| `pool_pre_ping` | **Din 2, Step 4** | Order load-bearing hai. Boundary exist karne ke baad deletion test ka jawab **palat sakta hai** |
| Reaper aur dispatcher ka boundary | **Din 2** | Aaj worker pe ek clean measurement chahiye. Teen process ek din me change karne se pata nahi chalega kis change ne kya kiya |
| Supervisor (`restart:` policy) | **Din 2, Step 3** | Supervisor **boundary ke baad** aata hai. Pehle supervisor lagane se process restart ho jaayega aur aaj ka `poll_failures` measure hi nahi hoga |
| Retention / `.gitignore` / `logs/evidence/` | **Din 3** | Aaj ke logs isliye **delete nahi** karne hain |
| Pool exhaustion ke numbers | **Din 4** | Wo Din 3 ke retention rule pe depend karte hain |
| `/slow-hold` | **Din 4, Step 5** | Uska fix Step 2 ki measurement ko weak karta hai, to measurement pehle |
| Handler timeout | **Month 3** | Ek sawaal pehle chahiye: *timed-out handler ka status kya hai?* Month 2 ka cost model wo jawab dega |
| Naye tests | **Month 3, Week 6 ke baad** | Week 6 ka fake provider iss project ki pehli cheez hai jo integration test possible banati hai |
| Koi bhi migration | **iss hafte nahi** | `alembic heads` gate hai. Aaj schema change karna scope creep hai |
| LLM, provider, Redis, rate limit, token, budget | **Weeks 6–8** | [`../../planning/MONTH_02.md`](../../planning/MONTH_02.md) Section 0 |

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  PART B — PREDICTION QUESTIONS                                               ║
║  Ye block Gemini ko paste NAHI hota.                                         ║
║  Jawab apne head se, us step se PEHLE,                                       ║
║  docs/daily/week_05/DIN_01_PREDICTIONS_FROZEN.md me. Phir hash lo.           ║
║  `idk` ek valid jawab hai aur wo 0 score karta hai — aur wo accurate hai.     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Q1 (Step 2 se pehle)
    Postgres down hone ke DO moment hain: (a) connection pehle se open thi aur toot gayi,
    (b) nayi connection banane ki koshish refuse hui.
    Kya SQLAlchemy dono pe ek hi exception class deta hai? Agar nahi, to kaunsi kaunsi?

Q2 (Step 3 se pehle)
    Claim poll me exception pakdne ke baad, agar main session pe kuch NA karu aur seedhe
    loop continue kar du — DB wapas aane ke baad agla `session.execute()` chalega ya nahi?
    Agar nahi, to kya error aayega?

Q3 (Step 4 se pehle)
    Ek `25 s` ke outage me, `POLL_INTERVAL_SECONDS = 2.0` ke saath, `poll_failures` ka
    number kya hoga? Ek number likho, range nahi.
    Aur: DB start hone ke baad PEHLA poll success hoga ya wo bhi fail hoga? Kyun?

Q4 (Step 5 se pehle)
    Do arms — (i) catch ke baad turant retry, (ii) catch ke baad POLL_INTERVAL wait.
    Kaunsa arm `recovery_to_first_claim` kam dega, aur uska cost kya hai?
    (Cost ek number hona chahiye ya ek naam, "load badhega" nahi.)

Q5 (Step 6 se pehle)
    Handler khatam, side effect COMMIT ho gaya, aur mark se PEHLE DB chala gaya.
    Boundary lagane ke BAAD: is job ka `attempts` kitna hoga jab wo eventually
    `succeeded` hota hai? Aur `side_effects` me kitni rows?
```

---

*Aaj ke measurement ke **baad** kholna:* [`DIN_01_KEY.md`](DIN_01_KEY.md)
*Plan:* [`../../planning/WEEK_05.md`](../../planning/WEEK_05.md)
