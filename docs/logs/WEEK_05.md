# WEEK 5 — Wo hole jo Month 1 ka verdict likh gaya, aur phir usko publish karna

**Month 2 ka pehla hafta · Layer L2** · Daily log with measurements, prediction scoring, and unresolved items.
Plan: [`../planning/WEEK_05.md`](../planning/WEEK_05.md) · Decisions: [`../DECISIONS.md`](../DECISIONS.md) ·
Problems: [`../PROBLEMS.md`](../PROBLEMS.md)

> **Plan intent rakhta hai; ye file outcome rakhti hai.** Har factual claim ke saath provenance hai:
> `[MEASURED]` user ke retained output se · `[MEASURED-R]` reviewer ke apne run/read se, iss machine pe ·
> `[REPORTED, NOT VERIFIABLE]` number record hua par uska artifact tree me nahi hai (`P-45`) ·
> `[NOT TESTED]` case enumerate hua, kabhi chala nahi · `[INFERRED]` source/mechanism se ·
> `[NO EVIDENCE]` judgement, aur wo label ke saath.
>
> **Ek untagged line `[MEASURED]` padhti hai, aur ye iss file ka sabse mehenga default hai.**

---

## Din 1 — Worker ka exception boundary: crash hata nahi, line 185 se line 305 pe shift hua (`2026-09-24`)

**Original goal (BRIEF se):** Din 5 ki maut aaj ki machine pe control ke taur pe dobara produce karna; DB-down
ke do moments ka exception class `__mro__` se pehchanna; **sirf** claim poll pe boundary lagana; wahi outage
dobara chalake teen numbers lena (`poll_failures`, `recovery_to_first_claim`, `alive`); catch-ke-baad ke
behaviour ko **do arms** se decide karna; aur terminal-mark ke crash seam pe `attempts` aur `side_effects`
measure karna.

**Goal met?** **Steps 1–5: yes, aur unhone KEY ki teen predictions galat sabit ki. Step 6: result sahi tha,
evidence overwrite ho gaya tha — reviewer ne aaj usko dobara measure kiya. Scoring: nahi ho saka.**

- `[MEASURED]` Control reproduce hua: worker `worker.py:185` pe mara, exactly Din 5 jaisa.
- `[MEASURED]` Boundary ke baad worker outage se zinda nikla, `5` failed polls ke saath, aur recovery ke baad
  **pehla** poll success hua — `17` consecutive clean `2.0 s` cycles uske baad.
- `[MEASURED-R]` Boundary ne worker ko outage se **nahi** bachaya. Usne **claim poll** ko bachaya. Terminal
  mark abhi bhi unguarded hai aur aaj ki maut `worker.py:305` pe hui.
- `[MEASURED-R]` `attempts = 2` for one fault — `D-26` ka `Cost 6`, jo `[NOT TESTED]` tha, ab `[MEASURED]` hai.
- **Q1–Q5 scored nahi hue:** `docs/daily/week_05/DIN_01_PREDICTIONS_FROZEN.md` **exist nahi karti**.

---

### 📊 Measured / Observed

#### Seal aur retained evidence

| Kya | Result | Provenance |
|---|---|---|
| `DIN_01_PREDICTIONS_FROZEN.md` | **File does not exist** | `[MEASURED-R]` `Get-ChildItem -Recurse -Filter "*PREDICTIONS*" docs` → `10` files, sab `month_01/daily/week_03` aur `week_04` me |
| Frozen SHA-256 | Not taken — koi file nahi thi | `[NO EVIDENCE]` |
| `logs/w5d1_*` (user ke) | `13` files, `2` zero-byte by design (`step3`/`step4` stderr) | `[MEASURED-R]` |
| `logs/w5d1r_*` (reviewer ke aaj ke) | `6` files | `[MEASURED-R]` |
| Relay processes at close | `0` | `[MEASURED-R]` |
| Probe databases at close | `0` (`relay\_%` pattern) | `[MEASURED-R]` |
| `alembic heads` | ek — `w4d4_sink_unique` | `[MEASURED-R]` |

#### Bench — evidence DB `relay`, close pe (reviewer ke re-measurement ke **baad**)

| Kya | Result | Provenance |
|---|---|---|
| Nau counters | `133 \| 145 \| 19 \| 4 \| 7 \| 39 \| 5 \| 0 \| 1` | `[MEASURED-R]` — delta `0`, aur ye reviewer ke apne probe run ke baad ka number hai |
| Job `136` | `136\|running\|1\|1` | `[MEASURED-R]` poison pill untouched |
| Job `108` | `dead_letter\|4\|0` | `[MEASURED-R]` |
| Job `128` | **`succeeded\|4\|4`** | `[MEASURED-R]` — `WEEK_05.md` ka shared context isko `running\|2\|2` likhta hai. **Document stale hai, data nahi** — nau counters aur `job_executions` Month 1 close se badle nahi hain |
| `sink_deliveries` | `count(*) = 7`, `last_value = 10` | `[MEASURED-R]` `P-46` ka permanent gap |

---

#### Step 1 — control: maut dobara produce hui

| Kya | Result | Provenance |
|---|---|---|
| Worker status | **DEAD** | `[MEASURED]` `w5d1_step1_worker.stderr.log`, `9149` bytes |
| Outermost frames | `worker.py:321 asyncio.run(run_worker())` → `worker.py:185 result = await session.execute(claim_query)` | `[MEASURED]` |
| Final exception | `sqlalchemy.exc.InterfaceError`, direct cause `asyncpg.exceptions._base.InterfaceError: connection is closed` | `[MEASURED]` |
| Failing statement | claim ka `... LIMIT $2 FOR UPDATE SKIP LOCKED` | `[MEASURED]` log me SQL echo ke saath |
| Normal path outage se pehle | `1` claim + `1` mark, `0` poll_errors | `[MEASURED]` `w5d1_step1_worker.stdout.log` |
| stdout ki aakhri line | `13:30:33,899`, phir kuch nahi | `[MEASURED]` |

**Din 5 ka log jhoot tha aur ab wo do machine-runs se jhoot hai.** Pehle `[MEASURED-R]`, aaj `[MEASURED]`.
Frame-for-frame same: line `321` → line `185`.

---

#### Step 2 — exception hierarchy: **aur yahan KEY galat thi**

`labs/w5d1_exc_probe.py`, output `logs/w5d1_step2_exc.log`.

| Moment | Caught class | `__mro__` | `e.orig` |
|---|---|---|---|
| (a) pool me padi stale connection, DB down | `sqlalchemy.exc.InterfaceError` | `InterfaceError → DBAPIError → StatementError → SQLAlchemyError → HasDescriptionCode → Exception` | `sqlalchemy.dialects.postgresql.asyncpg.InterfaceError` |
| (b) nayi connection, DB down | **`builtins.ConnectionRefusedError`** | `ConnectionRefusedError → ConnectionError → OSError → Exception` | **`None`** |

`[MEASURED]` dono rows.

**Ye din ka sabse valuable finding hai, aur wo KEY ke against hai.** `DIN_01_KEY.md` ne likha tha: *"Dono
`DBAPIError` ke neeche aate hain — par same subclass nahi dete"*, aur uske baad recommend kiya tha ki class ki
jagah `e.connection_invalidated` flag padho kyunki *"class badal sakti hai, flag ka matlab nahi badalta."*

**Measured: case (b) `DBAPIError` ke neeche nahi hai. Wo SQLAlchemy ka exception hi nahi hai.** `OSError` ka
subclass hai, `e.orig` `None` hai, aur `connection_invalidated` attribute uspe maujood nahi hai. Consequence,
aur ye theoretical nahi hai:

- `except sqlalchemy.exc.DBAPIError` Step 3 ka normal-path gate **pass** karta, aliveness check **pass** karta,
  aur ek asli outage ke **doosre** failure pe process maar deta.
- KEY ki `connection_invalidated` advice galat direction me galat thi — usne ek aisa discriminator suggest kiya
  jo un dono moments me se **ek** pe exist hi nahi karta.
- `except Exception` — jo user ne likha — **sahi hai, aur ek aise reason se sahi hai jo KEY me nahi tha.**
  `Exception` hi wo pehla common ancestor hai jo `InterfaceError` aur `ConnectionRefusedError` dono ko cover
  karta hai. Class-based narrow boundary **structurally** insufficient hai.

**Aur do moments nahi, chaar hain.** Din bhar ke logs me DB-down path pe chaar distinct types aaye
`[MEASURED-R]`, aur do KEY me naam se nahi hain:

| Class | Kab | Kahan measured |
|---|---|---|
| `sqlalchemy.exc.InterfaceError` | pool me stale connection, `connection is closed` | Step 1, 2, 4, 5, 6 — har run ka **pehla** failure |
| `ConnectionRefusedError` (`WinError 1225`) | port band, TCP refuse | Step 4 (`×4`), Step 5 arm 1 (`×6`) |
| `ConnectionError: unexpected connection_lost() call` | connection **accept** hui phir dropped — Postgres mid-shutdown ya Docker ka port proxy | Step 5 arm 1 (`×25`), Step 6 (`×1`) |
| `CannotConnectNowError: the database system is starting up` | Postgres process up hai aur clients ko **reject** kar raha hai | Step 5 arm 1 (`×1`), Step 6 (`×1`) |

Aakhri do KEY me nahi the. Chautha wala Step 5 ke decision ka poora basis ban gaya.

---

#### Step 3 — normal path toota nahi

| Check | Result | Provenance |
|---|---|---|
| Ek job end-to-end | `1` claim → `1` mark `succeeded` | `[MEASURED]` `w5d1_step3_worker.stdout.log` |
| `poll_errors` | `0` | `[MEASURED]` |
| stderr | `0` bytes | `[MEASURED]` |
| `except BaseException` in `src/` | `0` matches | `[MEASURED-R]` `Select-String -Path src\*.py -Pattern "BaseException"` |

C1 ki dono rows pass. `asyncio.CancelledError`, `KeyboardInterrupt`, `SystemExit` teeno iss handler ke liye
unreachable rehte hain, to graceful shutdown intact hai `[INFERRED from Python's exception tree]`.

---

#### Step 4 — teen numbers, aur KEY ka arithmetic toot gaya

| Number | Result | Provenance |
|---|---|---|
| `alive` | **True** — `WORKER_STATUS: ALIVE`, stderr `0` bytes | `[MEASURED]` |
| `poll_failures` | **`5`** = `InterfaceError × 1` + `ConnectionRefusedError × 4` | `[MEASURED]` `w5d1_step4_worker.stdout.log` |
| Outage jaisa **worker** ne dekha | **`26.373 s`** — aakhri successful SQL se pehli successful SQL tak, gap `14:13:14,920` pe khatam | `[MEASURED-R]` SQL echo timestamps se derive kiya |
| Recovery ke baad pehla poll | **Success.** Gap ke baad `0` poll_errors, `17` consecutive clean `2.0 s` cycles | `[MEASURED]` |
| `recovery_to_first_claim` | `1.668 s` — **`[REPORTED, NOT VERIFIABLE]`** | `docker compose start` ka wall clock sirf harness ke console pe tha; Step 4 ka harness `scratch/` me nahi hai |
| Outage length, `POLL_INTERVAL`, `n` | `~25 s` requested / `26.373 s` observed · `2.0` · `n = 1` | `[MEASURED-R]` |

**KEY ki `poll_failures` derivation falsify ho gayi.** KEY ne likha: `poll_failures ≈ outage / POLL_INTERVAL
≈ 25 / 2.0 ≈ 12–13`. **Measured `5`.** Wajah wo term hai jo derivation me tha hi nahi — **failed attempt ka
apna cost.** `26.373 / 5 = 5.27 s` per cycle `[MEASURED-R, derived]`, matlab `2.0 s` sleep ke **upar** ~`3.3 s`
har failed connection attempt me gaye. Sahi shape:

```
poll_failures  ≈  outage_seconds / (POLL_INTERVAL_SECONDS + failure_cost_seconds)
```

aur `failure_cost_seconds` wo number hai jo kisi ke paas nahi tha. KEY ne isko ek line me chhua tha
(*"agar TCP timeout lagta hai to har failure me second lagte hain aur count gir jaata hai"*) par `docker
compose stop` ko clean shutdown maan ke refusal ko **fast** infer kiya tha. Wo inference galat thi.

**Ek honest caveat:** `5.27 s` ek **mean** hai, per-failure breakdown nahi. `[poll_error]` ek bare `print()`
hai jisme timestamp nahi hai `[MEASURED-R from source]`, to log se spacing nikalna possible nahi — sirf
aggregate nikalta hai. Ek line ka fix, owner Din 2.

**Aur README ka bound ka ek half ab `[MEASURED]` hai.** README kehta hai `remaining lease + one reaper poll +
possibly one failed poll`. Wo *"possibly one failed poll"* worker ke liye **materialize nahi hua** — pool
generation invalidate hone ka mechanism jo KEY ne describe kiya tha, wo hold karta hai. **Ye KEY ka ek
`[INFERRED]` tha aur aaj wo verify hua.**

---

#### Step 5 — do arms, aur nateeja KEY ke ulta

| Metric | Arm 1 (no sleep) | Arm 2 (`POLL_INTERVAL` wait) | Provenance |
|---|---|---|---|
| `poll_failures` | **`33`** | **`5`** | `[MEASURED]` |
| Outage jaisa worker ne dekha | `26.082 s` | `26.373 s` | `[MEASURED-R]` echo timestamps se — **`0.29 s` ke andar, to C3 ki "same outage length" condition hold karti hai** |
| Error split | `InterfaceError × 1` · `ConnectionRefusedError × 6` · `unexpected connection_lost() × 25` · `CannotConnectNowError × 1` | `InterfaceError × 1` · `ConnectionRefusedError × 4` | `[MEASURED-R]` |
| Postgres startup window me attempt | **Haan** — `CannotConnectNowError` | Nahi | `[MEASURED]` |
| stdout log size | `9210` bytes | `13899` bytes (poora job bhi chala) | `[MEASURED-R]` |
| `recovery_to_first_claim` | `2.176 s` | `1.668 s` | `[REPORTED, NOT VERIFIABLE]` — dono, same cause |
| Worker liveness | ALIVE | ALIVE | `[MEASURED]` |

**KEY ka Q4 ulta nikla, aur yahi aaj ka doosra best result hai.** KEY ne likha tha: *"turant-retry arm
`recovery_to_first_claim` **kam** dega — aur uski keemat teen jagah pe hai."* Measured direction: **arm 1
slower tha** (`2.176 s` vs `1.668 s`). Mechanism measured hai even though numbers unverifiable hain — arm 1
Postgres ke **startup window** ke andar pahunch gaya aur `CannotConnectNowError` khaaya, phir ek aur attempt
ka cost pay kiya. Arm 2 ka `2.0 s` sleep Postgres ko start hone ka time de diya.

**Zero backoff ne recovery ko tez nahi, slow kiya.** Ye counter-intuitive hai aur `D-30` ka `Cost` field isi
sentence pe khada hona chahiye — *"latency bachane ke liye spin karo"* ka assumption iss measurement me ulta
nikla. Caveat: `n = 1`, dono recovery numbers unverifiable, to ye ek **direction** hai, magnitude nahi.

**KEY ka busy-spin magnitude bhi galat tha.** KEY: *"saikDon se hazaaron."* Measured: **`33`**, mean
`26.082 / 33 = 0.79 s` per attempt `[MEASURED-R, derived]`. Bina kisi sleep ke bhi loop **connection attempt
se rate-limited** hai, sleep se nahi. To arm 1 ka asli cost `6.6×` polls hai, teen orders of magnitude nahi.
Isi wajah se KEY ka `Cost 2` (*"log volume, megabytes me"*) bhi materialize nahi hua — arm 1 ka log arm 2 se
**chhota** tha.

**Ek language correction, aur ye user ki recurring galti hai.** `w5d1_step5_arms.log` aur summary report dono
*"thundering herd"* aur *"connection storm"* likhte hain. **`n = 1` pe herd nahi hota.** Jo measure hua wo hai:
ek client ne ek attempt Postgres ke startup window me bheja aur reject hua. `n = 5` processes pe herd ka risk
`[INFERRED, NOT MEASURED]` hai — aur wo Din 2 Step 3 ka natural by-product hai.

---

#### Step 6 — reviewer ne dobara measure kiya, aur do arms me toda

**Kyun dobara:** user ka reported chain sahi tha par uska artifact maujood nahi hai. `logs/w5d1_step6_*` me
`1` claim, **`0` marks**, stderr `0` bytes, aur poora log `15:21:42.873`–`15:21:43.114` = `0.24 s` ka hai
`[MEASURED-R]`. `scratch/step6_harness.ps1` koi reaper launch nahi karta, `8 s` wait karta hai `30 s` nahi, aur
end pe worker ko `Stop-Process -Force` karta hai — **aur shuru me apne dono log files delete karta hai**, to ek
re-run ne wo run overwrite kar diya jo user ne console pe dekha tha. `relay_w5d1` drop ho chuki hai, to
re-derive bhi possible nahi tha. `P-45` ka chautha recurrence.

Reviewer ne `relay_w5d1r` (disposable) pe poora seam dobara chalaya. Job: `effect`, `payload {"seconds": 8.0}`
— **deliberately `HEARTBEAT_INTERVAL_SECONDS = 10` se kam**, taaki maut ka point clean rahe aur heartbeat path
enter na ho.

**Arm A — jo Relay apne aap karta hai**

| Kya | Result | Provenance |
|---|---|---|
| Handler ka `side_effects` + `outbox` COMMIT | `10:20:38.378` UTC | `[MEASURED-R]` |
| `docker compose stop db` | issued `10:20:38.388`, returned `10:20:40.031` | `[MEASURED-R]` |
| workerA status | **DEAD**, stderr `9445` bytes | `[MEASURED-R]` |
| Outermost frames | `worker.py:328 <module>` → **`worker.py:305 in run_worker`** = `mark_result = await session.execute(mark_stmt)` | `[MEASURED-R]` |
| Exception | `sqlalchemy.exc.InterfaceError`, cause `asyncpg ... connection is closed` | `[MEASURED-R]` |
| Peechhe chhoota state | `job\|1\|running\|1\|1`, `claimed_at` NOT NULL, `effects 1`, `outbox 1`, `execs 1`, `eff_seq 1` | `[MEASURED-R]` |
| Kisi ne workerA ko restart kiya? | Nahi — `WORKER_A_STATUS_AFTER_RESTART=DEAD` | `[MEASURED-R]` |

**Aaj ka boundary crash ko hataya nahi, use line `185` se line `305` pe shift kiya.** Idle worker ke liye ye ek
asli improvement hai — wo apna zyada waqt claim poll me bitata hai. Par jo job in-flight hai uske liye maut
abhi bhi guaranteed hai.

**Arm B — declared substitution: reaper aur workerB **haath se** launch kiye gaye**

| Kya | Result | Provenance |
|---|---|---|
| Reaper launch | `10:22:09.197` UTC, by hand | `[MEASURED-R]` |
| Reclaim | DB clock `10:22:12.636997` — `job_id=1 pre_status=running matched=1 post_status=pending pre_generation=1 post_generation=1` | `[MEASURED-R]` `w5d1r_step6_reaper.stdout.log` |
| workerB claim | `generation=2, attempt=2, rowcount=1` | `[MEASURED-R]` |
| Handler dobara chala | `Side-effect deduped for job_id=1 (rowcount=0)` | `[MEASURED-R]` |
| Terminal mark | `Marked job 1 as 'succeeded' (rowcount=1)` | `[MEASURED-R]` |
| **FINAL** | `job\|1\|succeeded\|2\|2` · `side_effects count(*) = 1` · **`side_effects_id_seq.last_value = 2`** · `outbox = 1` · `job_executions = 2` rows, generations `1` aur `2` | `[MEASURED-R]` |

User ka reported Step 6 ka **har number confirm hua**. Teen cheezein jo uski report me nahi thi, ab record pe
hain:

1. Maut ka frame **line `305`** hai — mark. Boundary ne crash **move** kiya, remove nahi.
2. `count(*) = 1` par `last_value = 2` — no-op `ON CONFLICT` ne sequence value consume kiya. `P-46` ka wahi
   shape, **teesri baar** measure hua (Week 3 job `114`, `sink_deliveries` ka `7` vs `10`, aur ab ye).
3. `job_executions` me **`2`** rows hain, generations `1` aur `2`. **Duplicate execution record hoti hai
   chahe duplicate effect na ho** — ye dono contracts ka farak hai aur ye row usko dikhati hai.

**Aur wo correction jo inn teeno se zyada important hai.** Reaper launch se reclaim tak `3.44 s` lage. **Wo
recovery latency NAHI hai — wo process-launch latency hai.** Lease reaper ke exist karne se ~`64 s` pehle hi
expire ho chuki thi. Reaper outage ke baad **maujood nahi tha**, kyunki uske loop me koi `try` hi nahi hai.
**Aaj ke code ke saath fault-to-reclaim ka time unbounded hai**, aur ye run sirf isliye recover hua ki ek
insaan ne do process start kiye. **Ye Din 5 ke `7.9 s` ka exactly wahi trap hai. `3.44 s` ko recovery bound ki
tarah quote nahi karna.**

**`D-26` ka `Cost 6` ab `[MEASURED]` hai:** ek fault ki keemat **do attempts** hai. `MAX_ATTEMPTS = 3` pe do
aise outage ek **healthy** job ko `dead_letter` me daal dete hain.

---

### 🔎 Code audit — `src/worker.py`

1. **Boundary ka shape sahi hai, aur sahi reason se.** `try` poore `async with async_session() as session:`
   block ko lapetta hai, to poisoned session block ke exit pe discard ho jaati hai aur agla poll nayi banata
   hai. **Iss shape me explicit `rollback()` zaroori nahi hai**, aur recovery ke baad ke `17` clean cycles wo
   prove karte hain `[MEASURED + INFERRED from source]`. Ye KEY ke Q2 ka *per-poll session* fork hai, aur repo
   safe side pe hai. `session.begin()` ka `__aexit__` khud rollback try karta hai aur wo failure bhi isi `try`
   ke andar hai, to KEY ka trap 2 (*"`rollback()` bhi fail kar sakta hai"*) yahan already covered hai.
2. **`except Exception` correct hai, aur `BaseException` avoid hua.** grep `0`.
3. **Terminal mark abhi bhi unguarded hai (lines ~`288`–`318`), aur line `305` aaj ki maut ka point hai**
   `[MEASURED-R]`.
4. **`send_heartbeat` ka DB call bhi unguarded hai.** `except asyncio.TimeoutError:` branch ek poori session
   kholta hai bina `try` ke. Aur `run_worker` ka `finally: await heartbeat_task` us exception ko **`finally`
   ke andar se** re-raise karega. Matlab jis job ka handler `HEARTBEAT_INTERVAL_SECONDS = 10` se lamba hai,
   uske liye outage worker ko mark tak **pahunchne se pehle** hi maar dega — ek teesri line pe.
   **`[NOT TESTED]`** — aaj ka Step 6 `seconds = 8.0` pe chala, deliberately heartbeat interval ke neeche, to
   ye path enter hi nahi hua. **Owner: Din 2.**
5. **Boundary har `Exception` nigal jaati hai.** Claim query me ek genuine programming error (galat column, type
   error) ek infinite `2 s` retry loop ban jaayega, per-iteration ek line, aur koi escalation nahi. Aaj ki
   problem nahi; `D-30` ka ek `Cost` line hai.
6. **Boundary failures ko count nahi karti.** `poll_failures` sirf log grep karke milta hai, aur print me
   timestamp nahi hai. Do choti line ka fix, owner Din 2.
7. `src/reaper.py` ke `run_reaper()` loop me **koi `try` nahi hai** — `while not SHUTDOWN_REQUESTED: await
   reap_stuck_jobs(); await asyncio.sleep(...)` `[MEASURED-R from source]`. Aaj ye deliberately chhoda gaya.

---

### 🧠 Prediction review — **scored nahi ho saka**

`docs/daily/week_05/DIN_01_PREDICTIONS_FROZEN.md` **exist nahi karti** `[MEASURED-R]`, aur din ki summary me
bhi Q1–Q5 ke jawab nahi aaye. Iss hafte ka scoring rule hai *"frozen text ko **quote** karna hai, paraphrase
nahi"* — aur wo rule specifically isliye likha gaya tha ki Din 5 pe frozen text teen jagah upar ki taraf
re-write ho gaya tha.

**Score: `not scored`, `0` nahi.** `0` uske knowledge ke baare me ek claim hota; `not scored` record ke baare
me ek claim hai, aur sirf doosra wala accurate hai.

Jab frozen file ya likhe hue jawab aayenge, KEY ke gates ye maangte hain:

| Q | Full credit ke liye kya chahiye | Aaj ka measured jawab |
|---|---|---|
| Q1 | Do moments ko alag maana **aur** common ancestor naam se | Do nahi, **chaar** classes. Common ancestor **`Exception`** hai, `DBAPIError` nahi — KEY khud galat thi |
| Q2 | Session scope ka fork pehchana; sirf `PendingRollbackError` naam lena aadha | Repo per-poll session pe hai, to bina `rollback()` bhi recovery hua — `17` clean cycles |
| Q3 | Ek number **aur** uska mechanism; recovery-ke-baad ka half alag scored | `5`, aur mechanism `POLL_INTERVAL + failure_cost` hai. Recovery ke baad pehla poll **success** |
| Q4 | Cost ek **naam ya number** ho | Direction **ulta** nikla: no-sleep arm slower tha. `33` vs `5` polls, `CannotConnectNowError` in the startup window |
| Q5 | `side_effects = 1` **aur** `attempts` ke do branch | `side_effects = 1`, `seq = 2`, `attempts = 2` (Branch A). Branch B implement hi nahi hui — mark pe boundary nahi hai |

---

### 🤖 Reviewer ki apni galat predictions — record ke liye

`DIN_01_KEY.md` reviewer ne likhi thi. Aaj usme se **teen** claims galat nikle:

1. **"Dono moments `DBAPIError` ke neeche aate hain"** aur *"`e.connection_invalidated` class se zyada reliable
   hai"* — `ConnectionRefusedError` `DBAPIError` ke neeche nahi hai aur uspe wo flag exist nahi karta. **Ye
   khatarnak direction me galat tha:** iss advice pe bana boundary Step 3 ka gate pass karta aur asli outage ke
   doosre failure pe process maar deta.
2. **`poll_failures ≈ 12–13`** — measured `5`. Derivation me `failure_cost` term missing tha.
3. **Busy-spin = "saikDon se hazaaron"** aur *"log megabytes me"* — measured `33`, aur log arm 2 se chhota.
   Loop connection attempt se rate-limited hai, sleep se nahi.

Jo KEY ne **theek** kaha: per-poll session ka fork (Q2), pool generation invalidation ki wajah se recovery ke
baad pehla poll success hona (Q3 ka doosra half), `side_effects = 1` with `seq` advancing, aur `attempts` ka
Branch A.

---

### 💡 What I understood — own words, 2026-09-30

1. DB outage ke waqt python me do alag-alag exception trees aate hain: pool me padi stale connection tootne par `sqlalchemy.exc.InterfaceError` aata hai, par jab port band ho to OS-level `ConnectionRefusedError` (`OSError`) aata hai jisme `DBAPIError` ya `connection_invalidated` attribute exist hi nahi karta (`labs/w5d1_exc_probe.py`). Isliye sirf `except Exception` hi dono ko safely swallow kar pata hai.
2. Outage ke dauran poll failure count ka calculation simple `outage / interval` nahi hota. 26.373 s outage aur 2.0 s poll interval me expected 13 ki jagah sirf 5 failures measure hue (`w5d1_step4_worker.stdout.log`), kyunki har failed connection attempt ka apna TCP timeout/refusal cost hota hai (~3.27 s extra per cycle).
3. Bina sleep ke busy-retry karna recovery ko fast nahi balki slow banata hai: arm 1 (no sleep) me 33 failures aaye aur Postgres startup window me `CannotConnectNowError` khane ki wajah se recovery 2.176 s me hui, jabki 2.0 s sleep wale arm 2 me 1.668 s me hui.
4. `try/except` boundary ne worker ko crash hone se eliminate nahi kiya balki shift kiya: claim loop bacha par terminal status mark (`worker.py:305`) unguarded hone ke karan in-flight job wala worker wahin mar gaya, aur re-execution par `side_effects_id_seq` 1 se advance hokar 2 ho gaya.

Gaps vs reviewer: Reviewer ne explicitly emphasize kiya ki boundary ne process ko outage se nahi balki sirf ek loop ko bachaya, aur busy-spin loop sleep se nahi balki TCP connection attempt se rate-limited hota hai.

### 💡 What the session established — **user ko ye apne shabdon me dobara likhna hai**

> Ye section reviewer ne likha hai. Protocol ke hisaab se isko user ke apne shabdon me replace hona hai —
> aur ye Week 2 se chal raha `💡` debt hai, isliye ye line yahan naam se hai.

1. Ek exception boundary ka scope uske `try` ke scope se zyada nahi hota. Aaj claim poll bacha, aur maut agle
   unguarded statement pe chali gayi — `185` se `305`. Boundary ne process ko outage se nahi bachaya; usne
   **ek loop** ko bachaya.
2. Class-based `except` DB failures ke liye structurally unsafe hai, kyunki DB down hone ke saare raste ek
   library ke exception tree se nahi aate. `ConnectionRefusedError` ek `OSError` hai. Common ancestor
   `Exception` hai, aur wahi minimum viable boundary hai.
3. Retry loop ka rate uske sleep se nahi, uske **failure ke cost** se decide hota hai. `2 s` sleep pe cycle
   `5.27 s` ka nikla. Bina sleep ke bhi `0.79 s` se tez nahi ho paya.
4. Zero backoff ne recovery slow kar diya, tez nahi — kyunki spin karne wala client Postgres ke startup window
   me pahunch jaata hai jahan Postgres khud usko reject karta hai.
5. Ek process zinda rehna aur ek system recover karna do alag cheezein hain. Aaj worker zinda hai aur reaper
   nahi, to fault-to-reclaim ka time abhi bhi unbounded hai. Supervisor optional nahi hai.
6. Jo cheez measure karke record na ki jaaye, wo do ghante me gayab ho jaati hai. Aaj ka sabse valuable chain
   ek harness ne apne hi log delete karke overwrite kar diya.

---

### ⚠️ Closeout corrections

| # | Jaise report hua | Jo measured hai | Provenance |
|---|---|---|---|
| 1 | *"Git diff: sirf `src/worker.py` modified hai"* | **`docker-compose.yml` bhi modified hai** (`+7` lines): `db` pe ek `volumes:` mount, aur ek `external: true` named volume `fce3921d…`. Ye aaj ke scope guard me nahi tha (`docker-compose.yml` ka owner Din 2 hai) | `[MEASURED-R]` `git diff` |
| 2 | *"logs `logs/w5d1_*` me preserved hain"* | Step 6 ka log me `1` claim, **`0` marks**, `0`-byte stderr, `0.24 s` span. Reported chain usme nahi hai | `[MEASURED-R]` |
| 3 | *"Worker terminal mark UPDATE pe crash hua"* | **Sahi**, aur frame `worker.py:305` hai. Confirm reviewer ke re-run se hua, retained log se nahi | `[MEASURED-R]` |
| 4 | *"thundering herd / connection storm"* | `n = 1`. Ek client, ek attempt startup window me. Herd `[INFERRED]` hai | `[MEASURED-R]` |
| 5 | *"Arm 1 … bina kisi recovery latency benefit ke"* | Report se **strong** hai: arm 1 measurably **slower** tha. Par dono recovery numbers `[REPORTED, NOT VERIFIABLE]` hain | `[MEASURED-R]` |
| 6 | Arm 1 errors = *"ConnectionRefused/ConnectionError (31)"* | `ConnectionRefusedError × 6` **aur** `unexpected connection_lost() × 25`. Do alag mechanism, ek bucket me | `[MEASURED-R]` |
| 7 | *"recovery_to_first_claim = 1.668 s"* / *"2.176 s"* | Dono `[REPORTED, NOT VERIFIABLE]`. Harness ke `Write-Host` wall clocks kisi file me nahi gaye; Step 4 ka harness tree me nahi hai | `[MEASURED-R]` |
| 8 | (plan ka shared context) job `128 = running\|2\|2` | `succeeded\|4\|4`. **Document stale hai, data nahi** — nau counters aur `job_executions` Month 1 close se unchanged | `[MEASURED-R]` |

---

### 🚧 Unresolved / Din 1 close blockers

1. **`DIN_01_PREDICTIONS_FROZEN.md` missing** → Q1–Q5 unscored. Ye hafte ka pehla din hai aur seal ka record
   pehle hi din nahi bana.
2. **`recovery_to_first_claim` dono arms ka unverifiable** — `P-45` ka shape, Day 1 of the week whose Din 3 is
   supposed to close `P-45`.
3. **Terminal mark unguarded** — measured death at `worker.py:305`. **`P-48`.**
4. **Heartbeat ka DB call unguarded, aur `finally` se re-raise hota hai** — `[NOT TESTED]`. **`P-48`.**
5. **`docker-compose.yml` ka volume change undeclared aur unscoped** — do-taraf wala change, decision chahiye.
   **`P-49`.**
6. **Koi supervisor nahi** → fault-to-reclaim unbounded. Din 2 Step 3.
7. **`[poll_error]` me timestamp nahi** → per-failure spacing unmeasurable. Din 2.
8. **Step 6 ka harness apne logs delete karta hai aur wall clocks console pe print karta hai** — **`P-50`**, aur
   ye Din 3 ke retention decision ka scope badalta hai: rule ko *harness console output* bhi cover karna hai,
   sirf `logs/` nahi.
9. **README rows 7/9 aur promise 4 aaj update NAHI hue** — deliberate. Owner Din 6, reaper/dispatcher/supervisor
   ke baad. Row 9 ka verdict abhi bhi `[NO EVIDENCE]` hai.
10. **`logs/` abhi bhi gitignored hai.** `w5d1_*` (13 files) aur `w5d1r_*` (6 files) ko Din 3 tak zinda rakhna
    hai.
11. **`WEEK_05.md` ka shared context job `128` galat likhta hai** — Din 2 Step 0 pe theek karna, warna daily
    bench ka expected value hi galat hai aur gate sahi tareeke se fail nahi kar sakta.

---

### ❓ Next thought

Boundary ne worker ko outage se nahi bachaya — usne **claim poll** ko bachaya. Claim ke baad ka poora raasta
(`record_execution` → handler → heartbeat → mark) abhi bhi `asyncio.run` tak ek seedhi line hai. Din 2 ka asli
sawaal isliye *"reaper pe bhi wahi `try` lagao"* nahi hai. Wo hai: **ek boundary jo crash ko agle statement pe
shift kar deti hai, wo `restart:` policy ka substitute hai ya uska prerequisite?** Aaj ka `3.44 s` — jo ek
insaan ke enter dabane se shuru hua tha — iska jawab de deta hai, aur jawab *prerequisite* hai.

---

*Plan:* [`../planning/WEEK_05.md`](../planning/WEEK_05.md) ·
*Din 1 BRIEF:* [`../daily/week_05/DIN_01_BRIEF.md`](../daily/week_05/DIN_01_BRIEF.md) ·
*Din 1 KEY:* [`../daily/week_05/DIN_01_KEY.md`](../daily/week_05/DIN_01_KEY.md)

---

## Din 2 — Teen boundaries lagi, aur din ka sabse bada finding ek chauthi DB statement hai jo galat handler ke andar baithi hai (`2026-09-25`)

**Layer L2 · `P-43` ka doosra half · Steps 0–6 sab chale, `140 min` budget**

> **Aaj ka ek-line natija:** worker, reaper aur dispatcher teeno ek outage se zinda nikle, supervisor bana aur
> usne ek asli `os._exit` crash pakda — **aur review me ek chauthi DB statement mili jo kabhi crash nahi karti,
> isliye teen din ki traceback-reading usko dekh hi nahi payi.** `record_execution` handler ke `try` ke andar
> hai, to uska DB fault **job ki galti** ban jaata hai: measured `dead_letter`, `attempts = 3`, handler ek baar
> bhi nahi chala. **`P-51`.**
>
> Aur ek cheez jo pehli baar hui: **frozen predictions file bani, aur uska hash match hua.** Kal wo file exist
> hi nahi karti thi. Isliye aaj `Q1`–`Q5` pehli baar **scored** hain — `not scored` nahi.

---

### 📊 Measured / Observed

#### Seal — aur ye is hafte ka pehla satisfied seal hai

| Check | Value |
|---|---|
| `docs/daily/week_05/DIN_02_PREDICTIONS_FROZEN.md` | **maujood** |
| SHA-256, reviewer ke apne `Get-FileHash` se | `7D9351BE0E1BF7411DBC4B0FF0266933689786D9383361EE981094A9B5BF0D8C` — **user ke reported hash se exact match** `[MEASURED-R]` |
| Step 0 me likhi gayi, Step 1 se pehle | haan, aur paanchon jawab usme hain, `Q4` ka `idk` included |

#### Bench — evidence DB `relay`, reviewer ke apne probing ke **baad** dobara liya gaya

| Check | Expected | Measured |
|---|---|---|
| Nau counters | `133 \| 145 \| 19 \| 4 \| 7 \| 39 \| 5 \| 0 \| 1` | **exact match, delta `0`** `[MEASURED-R]` |
| Job `136` (poison pill) | `running\|1\|1` | `running\|1\|1` |
| Job `108` · Job `128` | `dead_letter\|4\|0` · `succeeded\|4\|4` | dono match |
| `pg_database LIKE 'relay\_%'` | `0` rows | `0` — `relay_w5d2` drop ho chuki hai |
| `alembic heads` | ek | `w4d4_sink_unique`, aur **aaj koi migration nahi** |
| `except BaseException` in `src/` | `0` | `0` — C1 ka gate pass |
| Modified files | teen | `src/worker.py`, `src/reaper.py`, `src/dispatcher.py` |

**Isolation discipline ka ek non-trivial result:** Step 4 me worker ne **job `136` claim kiya** — wahi poison
pill — aur uska `os._exit(1)` chala. Wo `relay_w5d2` ki copy thi, evidence DB ki nahi. **KEY ka trap #11 ek
live hazard tha aur wo hazard avoid hua**, jabki `.env` ka `DATABASE_URL` aaj bhi `relay` pe point karta hai.
Nau counters delta `0` isi baat ka proof hai.

#### Step 1 — death point, aur yahan sab kuch derivation ke hisaab se chala

Edit kuch nahi, pehle measure — jo BRIEF ne maanga tha, wahi hua.

| Cheez | Measured |
|---|---|
| Worker zinda? | **NAHI**, exit code `1` |
| Deepest application frames | `src/worker.py:287` in `run_worker` (`await heartbeat_task`) → `src/worker.py:57` in `send_heartbeat` (`session.execute(update_stmt)`) |
| Line `305` (mark) tak pahuncha? | **Nahi.** Traceback me `305` kahin nahi hai |
| Exception | `sqlalchemy.exc.InterfaceError: … connection is closed`, aur uske upar `TimeoutError` ke saath `During handling of the above exception` |
| Stdout ka order | `Work completed` → `Finished execution for job_id=140` → **phir** traceback |

**Mechanism confirmed exactly as KEY described it:** handler normally complete hua, `finally` chala,
`await heartbeat_task` pe held exception raise hui, aur `finally` se nikli exception us `try` ke `except` se
**nahi** pakdi gayi. Boundary dikh rahi thi aur us raaste pe kaam nahi kar rahi thi.

**Aur `claimed_at` pe KEY galat thi, aur user bhi.** Log me heartbeat 1 `11:31:46.305`–`.312` pe **succeed
hui aur COMMIT hui**. `claimed_at = 2026-09-25 06:01:46.307358+00` — wo **heartbeat 1 ka timestamp hai, claim
ka nahi** (claim `11:31:36`). Lease last *successful* heartbeat pe anchor hui, jo KEY ke mechanism section me
sahi likha tha aur uske headline answer ke ulta hai. Details `P-53(a)`.

#### Step 2 — boundaries, aur bounded retry ka asli cost

| Cheez | Measured |
|---|---|
| Heartbeat boundary | `try`/`except Exception` `send_heartbeat` ke DB block ke andar. Loop `break` nahi karta, agla interval dobara try karta hai |
| `await heartbeat_task` | `try`/`except Exception` me wrapped. **Ye `asyncio.shield()` NAHI hai** — neeche code audit dekho |
| Test 2A, normal path | `2 s` job: claim → execute → `[mark] … rowcount=1` `succeeded`. Kuch nahi toota |
| Test 2B, outage | **Worker `100%` zinda raha.** `Heartbeat sent` × 1, `[heartbeat_error] InterfaceError` × 1, `Finished execution`, phir `[mark_error] ConnectionRefusedError` × **3**, phir `[mark_abandoned]`, phir `[poll_error]` aur poll resume |

**`3` retry attempts, `10 s` deadline pe — aur ye number khud ek finding hai.** `1.0 s` sleep ke saath naive
arithmetic `~8` attempts deta hai. Mila `3`, kyunki **har failed attempt khud `~2.7 s` kha jaata hai** — Din 1
ka `failure_cost ≈ 3.3 s` term, dobara, ek nayi jagah. **Ek retry loop ka rate uske sleep se nahi, uske failure
ke cost se decide hota hai** — Din 1 ka `💡 3` iss hafte ka doosra confirmation le chuka hai.

**Aur bounded retry ne iss outage me kuch bhi nahi khareeda.** Outcome: mark abandoned → reaper reclaim →
`attempts = 2`. **Bilkul wahi jo "mark kho do" option deta hai**, plus `~10 s` ka pin. Wo case jahan bounded
retry jeetta hai — outage `min(deadline, lease remainder)` se chhota — **aaj run nahi hua. `[NOT TESTED]`.**

#### Step 3 — reaper aur dispatcher, dono zinda, aur blast radius ka farak

| Cheez | Measured |
|---|---|
| Reaper boundary | `try`/`except Exception` `reap_stuck_jobs()` ke around, `run_reaper()` ke loop me |
| Reaper outage me zinda | haan, aur recovery ke baad: `[reclaim] job_id=140 pre_status=running matched=1 post_status=pending` |
| Dispatcher boundary | `try`/`except Exception` poore `async with async_session()` ke around |
| Dispatcher outage me zinda | haan. `[poll_error]` × `3`: `ConnectionDoesNotExistError`, `ConnectionRefusedError`, `ConnectionError` — **teen alag classes, ek hi outage me**, Din 1 ke chaar-classes result ke saath consistent |
| Dispatcher recovery | outbox row `6` (job `999`) delivered, `status=dispatched attempts=2` |

**C2 ki teesri row pass hui** — ek zinda reaper jo kabhi `matched=1` nahi deta, `Get-Process` ke liye success
dikhta hai, aur wo yahan nahi hua.

**`P-35` aaj ke log me saaf dikh raha hai, aur boundary usko theek nahi karti.** Dispatcher ka
`status_code=500` wala attempt aur uske turant baad wala dobara attempt — **beech me koi sleep nahi**, kyunki
`dispatched = True` row **milne** pe set hota hai, HTTP success pe nahi. Do attempts back-to-back, measured.

**Aur Q3 ka asli scenario test hi nahi hua.** Q3 poochta hai: HTTP `200` ho gaya, COMMIT nahi hua, ab DB marta
hai. Test 3B ne DB ko **query phase** me maara. To Q3 ke chaar sub-answers aaj bhi KEY se derived hain,
measured nahi. `[NOT TESTED]`

#### Step 4 — supervisor, aur `restarts = 4` ka asli matlab

`scripts/supervisor.py`, option (b) — host script, `docker-compose.yml` untouched. Option pricing aur `Chose`
`D-30` ke `Supervisor` section me hai, jo **abhi bhi `OPEN` hai** aur Din 6 pe close hoga.

| Number | Value | Reading |
|---|---|---|
| `restarts` | `4` (2 worker, 2 reaper) | KEY ne `0` predict kiya tha. **Par `0` ka premise "plain outage, koi kill nahi" tha, aur aaj teen restarts deliberate `SIGKILL` se aaye.** To KEY ka `restarts = 0` **falsify nahi hua — wo test hi nahi hua.** `[NOT TESTED]` |
| Pehla worker exit | `exit 1` @ `2.04 s` uptime | **Ye chautha unguarded statement nahi hai — ye `P-36` hai.** Job `136` ka `crash_at` hook, `os._exit(1)`, jo har boundary se nikal jaata hai. **Supervisor ne usko wapas laaya, aur ye Q4 ke doosre half ka accidental live evidence hai** |
| `restart_to_first_claim` | `2.790 s` | `~0.99 s` interpreter start + `src.database` import, `~1.8 s` handshake + poll tick. **Launch/poll split jo KEY ne maanga tha** — par start clock console-only hai, `P-53(c)` |
| lease-anchor → reclaim | `35.191 s` = `30 s` lease + `5.19 s` | **Finite. Yahi poora point tha** — kal ye quantity unbounded thi. Label `fault_to_reclaim` overstate karta hai, `P-53(a)` |
| crash-loop backoff | `2.00 s` phir `1.00 s` | **Neeche gaya, upar nahi.** Uptime-gated with reset, ramp nahi. `[NOT A BOUND]`, `P-53(d)` |

**C3 ki teesri observation satisfy nahi hui.** Supervisor log `06:38:32.181` → `06:38:44.290` = **`12.1 s`**.
Gate `~30 s` DB-down maangta tha aur BRIEF ne likha tha ki wo run skip karna gate ko decorative banata hai.
**So *"restarts stay bounded"* is `[NOT SATISFIED BY EVIDENCE]`** — aur measured reset behaviour suggest karta
hai ki honest jawab *nahi* hai.

#### Step 5 — `pool_pre_ping`, aur yahan harness ne ek number likha jo usne naapa nahi

**Cost half asli measurement thi. Outcome half nahi thi.** `logs/w5d2_step5_preping.log` me
`poll_failures = 5` dono arms pe **print statements** hain — `False` arm Din 1 ka number re-print karta hai,
aur `True` arm **kabhi chala hi nahi**. Us step me koi outage inject nahi hua. **`P-52`, aur ye `P-45` ka
paanchva recurrence hai** — naya shape, kyunki pichle chaar me numbers *observe* hue the aur kho gaye; is baar
number observe hi nahi hua.

**Reviewer ne missing arm chalaya, to `D-31` ek `print` pe khada nahi hai.** Asli outage, `echo=False`,
`POLL_INTERVAL = 2.0 s`, outage `25 s`, dono arms ek hi disposable DB pe, ek variable:

| | `pre_ping=False` | `pre_ping=True` |
|---|---|---|
| `poll_failures` | `5` | `5` |
| **first error class** | `DBAPIError` | `ConnectionError` |
| recovery ke baad failed polls | `1` | `1` |
| recovery error classes | `ConnectionError` | `CannotConnectNowError` |
| first success after start | `2.191 s` | `2.156 s` |

`[MEASURED-R 2026-09-25]`

**Assertion sahi thi aur ab evidence bhi hai:** count genuinely `5` vs `5`. **Do cheez jo assertion nahi de
sakti thi:** flag **effective hai** — pehla failure stale handle se hatt kar connect path pe chala gaya, jo
wahi differential hai jo KEY ne *"flag set vs flag effective"* ke liye maanga tha; aur `pre_ping` ka **ek
theoretical benefit materialize nahi hua** — recovery ke baad failed polls **dono** arms me `1`.

**Cost, `echo` isolate karke, kyunki KEY ne wahi maanga tha:**

| `echo` | `pre_ping` | mean | p50 | p99 | source |
|---|---|---|---|---|---|
| not recorded | `False` | `0.1095 ms` | `0.0958 ms` | `0.2892 ms` (= max) | user, `n = 100` |
| not recorded | `True` | `3.1355 ms` | `2.7906 ms` | `4.5898 ms` (= max) | user, `n = 100` |
| `False` | `False` | `0.1085 ms` | `0.0928 ms` | `0.2726 ms` | reviewer, `n = 200` |
| `False` | `True` | `6.7723 ms` | `4.8446 ms` | **`33.7458 ms`** | reviewer, `n = 200` |
| `True` | `False` | `0.1624 ms` | `0.1512 ms` | `0.6812 ms` | reviewer, `n = 200` |
| `True` | `True` | `3.6695 ms` | `3.0064 ms` | `8.3245 ms` | reviewer, `n = 200` |

**Honest cost ek range hai, ek point nahi: `p50` `+2.70 ms` se `+4.75 ms`, aur tail `8.3 ms` se `33.7 ms`.**
Do instrument defects: user ke dono arms me **`p99` = `max`** (`n = 100` pe percentile index aakhri element de
raha hai), aur `pre_ping` arm high-variance hai to ek run tail ko understate karta hai. **Aur `echo` dominant
confound nahi tha — run-to-run variance hai**, jo KEY ke trap #9 ke ulta hai.

**`D-31` likhi gayi: `pool_pre_ping` `False` rehta hai.** Reason kal ka quote nahi hai — benefit measured `0`,
cost API pe per-request hai jahan benefit sabse kam hai.

---

### 🔎 Code audit — `src/worker.py`, `src/reaper.py`, `src/dispatcher.py`

**Jo theek hai:**

1. **Teeno boundaries `except Exception` hain, `BaseException` nahi.** `grep` `0` matches. KEY ka trap #2
   (`CancelledError` `BaseException` ka direct child hai) avoid hua, aur graceful shutdown intact hai.
2. **Heartbeat ka `except` loop ko `break` nahi karta**, to outage ke baad heartbeat dobara try karti hai. Ye
   sahi choice hai.
3. **Mark ke `except` me naked `await session.rollback()` nahi hai.** BRIEF ne specifically isko mana kiya
   tha; wo nahi hua.
4. **`async with async_session()` har retry attempt pe naya session banata hai**, to poisoned-session wala
   failure mode structurally absent hai — wo C2 ki doosri column thi.

**Jo theek karna hai:**

1. **`P-51` — `record_execution` galat `try` ke andar hai.** Ye din ka sabse bada finding hai aur wo review me
   mila, run me nahi. Neeche `⚠️` table row 1.
2. **"Shielded `await heartbeat_task`" — wo `asyncio.shield()` nahi hai, wo `try`/`except` hai.** Code **sahi**
   hai; naam galat hai, aur ye naam matter karta hai: `asyncio.shield()` cancellation se bachata hai aur
   exception ko **catch nahi** karta. Agar sach me `shield()` likha hota to Step 1 ki maut **waisi hi rehti**.
   Terminology correction, code correction nahi.
3. **Bounded retry ka bound `10.0 s` fixed hai, lease remainder nahi.** KEY ne explicitly likha tha ki iska
   implementation *"worker ko `claimed_at` ya lease remainder **yaad** rakhna padega"*. Fixed constant **dono
   directions me galat hai:**
   - handler `25 s`, lease `30 s` → remainder `5 s`, par retry `10 s` chalta hai → **lease ke `5 s` baad tak
     race karta hai**, jahan reaper reclaim kar sakta hai aur retry ka koi fayda nahi
   - handler `2 s` → remainder `28 s`, par retry `10 s` pe chhod deta hai → **jeet sakta tha, chhod diya**

   Ek line ka fix: `claimed_at` ko claim ke `RETURNING` se yaad rakho, deadline `claimed_at + LEASE - now()` se
   compute karo. **Owner: Din 3 ka faisla, `D-30` ke `Cost` field ke saath.**
4. **`asyncio.get_event_loop()` ek running coroutine ke andar.** Chalta hai, par deprecated shape hai;
   `asyncio.get_running_loop()` sahi call hai. Cosmetic, par do jagah hai.
5. **Dispatcher ka `dispatched = True` COMMIT fail hone pe ek poll sleep skip kar deta hai.** Boundary catch
   karti hai, `if not dispatched:` `False` hota hai, to sleep skip. **Ek** iteration ka effect, storm nahi —
   kyunki `dispatched` agli iteration ke top pe `False` ho jaata hai. `P-35` ka chhota naya face.

---

### 🧠 Prediction review — **pehli baar scored, kyunki pehli baar seal maujood hai**

Frozen text `docs/daily/week_05/DIN_02_PREDICTIONS_FROZEN.md` se **quote** kiya gaya, paraphrase nahi.

| Q | Frozen text (verbatim, trimmed) | Measured | Score |
|---|---|---|---|
| **Q1** | *"worker nai marega bcz 25 second ka kaam hai … but heart beat down hai to fir jab finnaly block mai jayega … to await chalega heartbeat or wo to behosh padi hai to waha error handle nai kiya apan ne to waha dikkat krega or **mark ke pehele marega** … heart beat ne usko nai badhaya wahi same rahega claim ka"* | Mark se pehle ✅ · `finally` + `await heartbeat` naam se ✅ · **`claimed_at` = heartbeat 1 ka time, claim ka nahi** ❌ | **`0.65 / 1.0`** |
| **Q2** | *"reaper ane ke baad wapis pending ho jayega but han rowcount 0 hi rahega and **fenced** ho jayega wo"* | Reaper reclaim ✅ · `rowcount = 0` ✅ · *"kaun lease refresh karta hai"* — **address hi nahi kiya** ❌ · `Conflict on mark` ki jagah `fenced` ❌ · mechanism ❌ | **`0.40 / 1.0`** |
| **Q3** | *"apan ne reveiiver idempotency lagaya hai to at leas once to rahege hi exaclty once nai possible um **idk** or to"* | At-least-once unchanged ✅, aur exactly-once receiver ka kaam hai ✅ (`D-27`) · baaki teen sub-answers explicit `idk` → **NOT ANSWERED** | **`0.25 / 1.0`** |
| **Q4** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q5** | *"poll faliour mai **change** ayega but minor hi miliseconds ka bcz extra query chalti hai sleect 1 usme **han of c bachata hai**"* | *unchanged* ❌ (measured `5` vs `5`) · count ka mechanism ❌ · teesra half *"bachata hai"* ❌ **confidently galat** · extra `SELECT 1` round trip aur `ms` ka order ✅ | **`0.15 / 1.0`** |

**Total: `1.45 / 5.0`.** Self-scored `1.95 / 5.0`.

**Do self-scores zyada the, aur pehla wala purana pattern hai.** `Q1` khud ko `1.0 / 1.0` diya *"Full credit:
… claimed_at = claim time"* likh kar — **jabki usi report me `claimed_at` ka measured value
`06:01:46.307358` diya gaya hai, aur wo heartbeat 1 ka timestamp hai.** Report ne ye bhi likha ki *"Heartbeat 1
succeeded at t=10s"*. **Do sach data points report me maujood the aur score unke against nahi liya gaya** — ye
wahi *"`3/3` claim karna un sawaalon pe jo derive nahi hue"* hai, naye kapdon me. `Q5` `0.3` se `0.15` hua:
KEY ke hisaab se cost ka number graded nahi hai, aur teen graded sub-parts me se `0` sahi the.

**Aur ek line jo genuinely earned hai:** `Q2`, `Q3`, `Q4` ke self-scores **exactly sahi** the, `idk` ko `idk`
likha gaya, aur seal Step 1 se pehle bani. **Teen me se teen calibration sahi** — ye Week 4 Din 6 ke `0/5`
reading gap se ek measurable improvement hai.

**`Q4` pe ek baat likhna zaroori hai:** jawab `idk` tha, aur uska full-credit requirement *"`P-36` naam se"*
tha. **`P-36` aaj ke run me khud chal gaya** — job `136`, `os._exit(1)`, `exit 1` @ `2.04 s`, supervisor ne
restart kiya. Answer repo me likha hua tha **aur** live ho gaya.

---

### 🤖 Reviewer ki apni galat predictions — record ke liye

`DIN_02_KEY.md` reviewer ne likhi thi. Aaj ka tally:

**KEY me galat:**

1. **`claimed_at` = claim time, *"koi heartbeat kabhi succeed nahi hui"*** — measured: heartbeat 1 succeed hui
   aur COMMIT hui, `claimed_at` `10 s` aage badha. KEY ne premise *"DB `t = 3 s` pe marta hai"* maan liya tha
   bina us premise ko verify kiye. **KEY ka apna mechanism section sahi tha** (*"lease aakhri successful
   heartbeat pe anchor hoti hai"*) aur headline answer usse contradict karta tha.
2. **`pre_ping` ke error classes** — KEY ne `InterfaceError` (without) vs `ConnectionRefusedError` family
   (with) predict kiya. Measured: `DBAPIError` vs `ConnectionError`. Shape sahi, exact classes galat. **Ye
   iss hafte KEY ki chauthi class-level galti hai** — Din 1 pe teen thi.
3. **Trap #9, *"`echo=True` Step 5 ke cost measurement ko contaminate karta hai"*** — isolate kiya, aur `echo`
   dominant term **nahi** hai; run-to-run variance hai. Trap #9 ko aage waise carry nahi karna.

**Review ke doran reviewer ki do live galtiyan, dono measurement se pakdi gayi:**

4. **"Supervisor `terminate()` stub ko maarega aur asli worker orphan ho jaayega"** — **galat.** Measure kiya:
   child stub ke saath mar gaya, aur `poll()` ne child ka apna exit code (`7`, ek `3.0 s` child pe `3.26 s`
   baad) forward kiya. **To supervisor ke `uptime`/`restarts`/exit codes sound hain** — sirf logged PID galat
   hai.
5. **"Dispatcher ki nayi boundary ek unbounded busy-spin banati hai"** — **galat.** Wo **ek** skipped sleep
   hai, kyunki `dispatched` agli iteration ke top pe reset ho jaata hai.

**KEY ne jo theek kaha:** `finally` ki exception `except` se nahi pakdi jaati (Q1 ka poora mechanism, exactly
as measured) · mark se pehle maut · `poll_failures` unchanged (Q5) · `pre_ping` checkout-time hai to
mark/heartbeat pe structurally useless · `restarts` ke non-zero hone ki do wajah, aur unme se ek — *"process
kisi aur wajah se mar raha hai"* — exactly `P-36` nikli · trap #11 ka poison-pill hazard, jo live tha.

---

### 💡 What I understood — own words, 2026-09-30

1. `finally` block ke andar se raise hone wali exceptions (`await heartbeat_task` at `src/worker.py:287`) outer `try/except` boundary se nahi pakdi jaati aur unhandled reh kar process maar deti hain. Heartbeat task ko try/except se wrap karke aur `send_heartbeat` ke DB block ko guard karke worker ko zinda rakha gaya.
2. Bounded retry loop me 1.0 s sleep ke bavajood 10 s deadline me keval 3 retry attempts ho payi, kyunki har failed connection attempt ~2.7 s kha gayi (failure cost). Ant me mark abandon hua aur reaper reclaim se `attempts = 2` hua — yaani bounded retry ne is outage me mark bachane ka koi fayda nahi diya.
3. Reaper (`src/reaper.py`) aur dispatcher (`src/dispatcher.py`) ke main loops me `try/except Exception` lagane se DB outage ke dauran dono zinda rahe aur recovery ke baad reaper ne stuck jobs reclaim kiye aur dispatcher ne outbox row 6 deliver kiya.
4. Process-level `os._exit(1)` (`P-36`, poison pill job 136) python ke kisi bhi `try/except` block se nahi pakda ja sakta; uske liye external supervisor (`scripts/supervisor.py`) ka hona anivarya hai jisne worker ko 4 restarts dekar wapas revive kiya.

Gaps vs reviewer: Reviewer ne note kiya ki `record_execution` par galat boundary lagne se infra DB fault job-level application failure me classify ho jata hai (P-51), aur fixed deadline lease duration se disconnected hone ke karan real bound provide nahi karti.

### 💡 What the session established — **user ko ye apne shabdon me dobara likhna hai**

> Ye section reviewer ne likha hai. Protocol ke hisaab se isko user ke apne shabdon me replace hona hai —
> aur ye Week 2 se chal raha `💡` debt hai, isliye ye line yahan naam se hai.

1. **Ek exception boundary "protection" nahi deti, wo ek *classification* deti hai.** Aaj ka sabse bada
   finding ye hai ki `record_execution` **already** ek `except Exception` ke andar thi — aur wahi problem hai.
   Wo infrastructure fault ko *job failure* bata kar retry/DLQ machine me daal deti hai. **Ek galat jagah lagi
   boundary crash se zyada khatarnak hai, kyunki crash dikhta hai aur misclassification `succeeded`-jaisa
   dikhta hai.**
2. **Wahi method jo teen bugs dhoondh paya, chauthe ko dekh hi nahi saka.** Din 1 aur Din 2 ke teeno boundaries
   **traceback padh kar** mile. `P-51` kabhi traceback nahi banata. **Jo failure crash nahi karta, wo
   crash-reading se nahi milta** — usko dhoondhne ke liye state padhni padti hai, stack nahi.
3. **`retry` ka bound uske counter se nahi, uske *external condition* se aana chahiye.** `10 s` fixed deadline
   lease se disconnected hai, to wo chhote outage pe jaldi haar jaata hai aur bade outage pe lease ke baad tak
   race karta hai. **Ek bound jo us cheez ko nahi jaanta jise wo bound kar raha hai, wo bound nahi hai** —
   aur wahi baat supervisor ke backoff pe bhi lagti hai, jo `5 s` uptime pe reset ho jaata hai.
4. **Ek number jo kisi script ne `print` kiya hai, wo measurement nahi hai.** `poll_failures = 5` dono arms pe
   sahi nikla — **par wo luck tha, evidence nahi.** Sahi jawab aur naapa hua jawab do alag cheezein hain, aur
   `D-31` ke case me dono match kar gaye.
5. **`os._exit` ke liye supervisor ka koi substitute nahi hai, aur boundary ke liye supervisor ka koi
   substitute nahi hai.** Aaj dono numbers saath me mile: boundary se recovery `~5.27 s` with state intact,
   restart se recovery `35.191 s` with in-flight lifecycle write kho jaana. Do different orders of magnitude.
6. **"DB `3 s` pe band kiya" ek intention hai, measurement nahi.** Jab tak wo moment kisi file me timestamp
   ke saath nahi likha, poori timeline ek yaad hai. Aaj teen steps ki timeline isi wajah se mis-dated hai.

---

### ⚠️ Closeout corrections

| # | Jaise report hua | Jo measured hai | Provenance |
|---|---|---|---|
| 1 | *"Applied try-except boundary … teen boundaries lag gayi"* (implicitly: worker ke saare DB touchpoints guarded) | **Ek chauthi DB statement hai jo guarded hai — galat handler se.** `record_execution` handler ke `try` me hai, to uska DB fault job failure ban jaata hai. Measured: healthy `sleep` job → `dead_letter`, `attempts = 3`, `last_error` = `UndefinedTableError` traceback, `side_effects = 0`, `outbox = 0` — **handler ek baar bhi nahi chala.** **`P-51`** | `[MEASURED-R]` fresh probe DB |
| 2 | *"Q1 → Score: 1.0 / 1.0 (Full credit: … `claimed_at` = claim time)"* | **`claimed_at` = `06:01:46.307358` = heartbeat 1 ka commit, claim ka nahi.** Claim `11:31:36`, heartbeat 1 `11:31:46`. **Ye contradiction report ke apne do data points se pakdi gayi**, kisi naye run se nahi. `Q1` = `0.65 / 1.0` | `[MEASURED-R]` step1 log |
| 3 | *"25s job, DB stopped at 3s"* (Step 1 aur Step 2B, dono) | **`t = 3 s` galat hai.** `docker compose stop db` `0.837 s`/`1.115 s` me return karta hai aur pehla failure uske `0.003 s`/`0.011 s` baad aata hai. Heartbeat 1 `t ≈ 10 s` pe COMMIT hui, to stop `t ≈ 10 s`–`20 s` ke beech laga. **Fault ka moment kisi file me nahi hai.** **`P-53(a)`** | `[MEASURED-R]` |
| 4 | *"poll_failures during 25s outage: Identical (5 failures on both arms)"* | **Wo naapa nahi gaya tha.** Step 5 me koi outage inject nahi hua; dono values `print` statements hain aur `False` arm Din 1 ka number hai. **Reviewer ne asli arm chalaya: conclusion sahi nikla (`5` vs `5`), aur error class ka differential — jo KEY ne maanga tha — pehli baar exist karta hai** (`DBAPIError` vs `ConnectionError`). **`P-52`** | `[MEASURED-R]` |
| 5 | *"Delta (Cost): +3.0260 ms Mean … roughly ~30x slower"* | Direction aur order sahi. **`p99` dono arms me `max` ke barabar hai** (`n = 100` ka indexing artifact), aur `pre_ping` arm high-variance hai: reviewer ka `n = 200` `p50 4.8446 ms`, **`p99 33.7458 ms`** deta hai. **Honest cost ek range hai: `p50 +2.70` se `+4.75 ms`.** Aur `echo` — jo KEY ne likhna maanga tha — log me nahi hai; isolate karne pe wo dominant term **nahi** nikla | `[MEASURED-R]` |
| 6 | *"crash-loop backoff (1s -> 2s -> 4s -> max 5s)"* | **Observed values sahi report hue (`2.00 s` → `1.00 s`), design ka description galat hai.** Code `if uptime < 5.0: backoff = min(backoff*2, 5.0) else: backoff = 1.0` — uptime-gated **reset**, ramp nahi. `≥ 5 s` jeene wala process backoff ko permanently `1.0 s` pe reset karta hai. **`[NOT A BOUND]`**, `P-53(d)` | `[MEASURED-R]` source + log |
| 7 | *"fault_to_reclaim: 35.191 s"* | Arithmetic sahi (`30 s` lease + `5.19 s`), **label overstate karta hai.** Ye *lease-anchor → reclaim* hai; *fault → reclaim* derivable nahi hai kyunki fault ka timestamp record nahi hua. **C3 ko jo chahiye tha — quantity finite hai — wo dono definitions pe satisfy hai** | `[MEASURED-R]` |
| 8 | *"Shielded `await heartbeat_task` in finally block"* | Code **sahi** hai, naam galat. Wo `try`/`except Exception` hai, `asyncio.shield()` nahi. **`asyncio.shield()` exception catch nahi karta — agar wo likha hota to Step 1 ki maut waisi hi rehti** | `[MEASURED-R]` diff |
| 9 | *"Bounded Retry for terminal mark with a 10.0s deadline"* | Implement hua, **par bound lease remainder nahi hai** — jo KEY ne explicitly maanga tha. Fixed `10 s` dono directions me galat hai (handler `25 s` pe lease ke baad tak race; handler `2 s` pe jeet sakta tha to chhod deta hai). Aur `10 s` deadline ne **`3`** attempts diye, `~8` nahi, kyunki har failure `~2.7 s` kha gaya | `[MEASURED-R]` |
| 10 | *"Relay python processes: 0 running"* | **Claim sahi hai** — koi Relay process nahi chal raha. Par BRIEF ka gate `(Get-Process python).Count == 0` hai aur host pe ek non-Relay python maujood tha, to **gate ne galat wajah se `1` diya.** Gate Relay processes ko baaki python se distinguish nahi karta — `RELAY_PROCESS_NAME` ya command-line filter chahiye | `[MEASURED-R]` |
| 11 | *"zero migrations created today"* + BRIEF ka Step 6 gate *"`git rev-parse HEAD:src` — Step 0 se badla hua"* | Migrations claim **sahi** (`1` head). Par wo gate **structurally pass nahi ho sakta**: `HEAD:src` **committed** tree padhta hai, aur aaj `0` commits hue. Tree `59a7545…` Step 0 aur Step 6 pe same rahega, chahe kitni files badlein. **BRIEF ka defect, user ka nahi** — working-tree ke liye `git stash create` ya `git diff --stat` chahiye | `[MEASURED-R]` |
| 12 | *"Test 3B (Dispatcher): … outbox row 6 dispatched post-recovery"* — Q3 ke evidence ke roop me | Run **hua aur pass hua**, par wo **Q3 ka scenario nahi hai.** Q3 = HTTP `200` ke **baad**, COMMIT se **pehle** DB marta hai. 3B ne DB ko query phase me maara. **Q3 ke chaar sub-answers aaj bhi `[NOT TESTED]` hain** | `[MEASURED-R]` step3 log |

---

### 🚧 Unresolved / carried

1. **`P-51` — `record_execution` ka misclassification.** Din ka sabse bada finding, aur **fix ek faisla hai,
   ek edit nahi** (teen options, teeno ki keemat `P-51` me). **Owner: Din 3 ka faisla.** Aaj ka koi change isko
   theek nahi karta.
2. **`P-52` — Step 5 ke outcome numbers naape nahi gaye the.** Reviewer ne replace kar diya, **par harness
   abhi bhi wahi text print karta hai.** Usko theek karna ya hata dena chahiye, warna agla din usi line ko
   quote karega.
3. **`P-53` — fault ka moment kahin record nahi hota.** `P-50` ka rule Din 1 pe likha gaya tha aur Din 2 uska
   pehla violation hai. Har fault injection ko file me timestamp ke saath jaana chahiye.
4. **`restarts = 0` (plain outage, koi kill nahi) — `[NOT TESTED]`.** KEY ka central Q4 prediction aaj run hi
   nahi hua, kyunki teen restarts deliberate `SIGKILL` se the.
5. **`~30 s` DB-down crash-loop run — `[NOT SATISFIED BY EVIDENCE]`.** C3 ki teesri row. Backoff reset wali
   baat isi run se price hogi.
6. **Q3 ka scenario (HTTP `200`, phir DB, phir COMMIT) — `[NOT TESTED]`.**
7. **Bounded retry ka jeetne wala case (outage < `min(deadline, lease remainder)`) — `[NOT TESTED]`.**
8. **`P-35` bachi rehti hai**, aur aaj ke log me dikhti hai: `dispatched = True` row **milne** pe set hota hai,
   HTTP success pe nahi.
9. **`P-36` bachi rehti hai.** `os._exit` har boundary se nikal jaata hai. **Aaj wo theek nahi hua — aaj wo
   pehli baar *observe* hua**, aur supervisor uska sirf mitigation hai, elimination nahi.
10. **`scripts/supervisor.py` kisi commit me nahi hai.** `.gitignore:74` `scripts/` ignore karta hai. **Aaj ka
    measurement instrument version control se bahar hai**, aur `logs/` (line `39`) bhi. `P-45`/`P-47`/`P-50`
    ke saath Din 3 ka scope.
11. **Aur ye file khud kisi commit me nahi hai — `P-47` ka amendment.** `.gitignore:39` ka `logs/` pattern
    unanchored hai, to wo `docs/logs/` ko bhi match karta hai. **Aur asymmetry ye hai:**
    `docs/month_01/logs/WEEK_00..04.md` **tracked hain** (`5` files — git already-tracked file ko pattern
    add hone pe untrack nahi karta), aur `docs/logs/WEEK_05.md` **ignored hai** `[MEASURED-R]`. Matlab
    *"weekly logs commit hote hain"* dikhta hai aur **Month 2 ka pehla log kisi commit me nahi hai.** Fix ek
    character ka hai (`/logs/`), aur `scripts/` (line `74`) me wahi defect hai.
11. **`D-30` `OPEN` hai.** `Supervisor` section me aaj ke notes gaye, entry Din 6 pe close hogi.
12. **README rows 7/9 aur promise #4 ka process half aaj update NAHI hue** — deliberate, KEY ke instruction ke
    hisaab se. Row 9 ka verdict abhi bhi `[NO EVIDENCE]`. Owner Din 6.
13. **Din 3 ka load badh gaya hai:** `P-51` ka faisla + `D-32` retention + `requirements.txt` pins + Step 5 ka
    slip-in (jo aaj ho gaya, to ye jagah khaali hui). **Din 3 ka budget dobara dekhna hoga.**

---

### ❓ Next thought

Aaj teen boundaries lagi aur teeno traceback padh kar mili thi. Chauthi galti traceback nahi banati — wo ek
healthy job ko `dead_letter` me daal deti hai aur `last_error` me Postgres ka error likh deti hai, aur wo
`[mark] rowcount=1` ke saath **successful** dikhti hai. **To agla sawaal *"kahan crash hota hai"* nahi hai. Wo
hai: kaunsi state transitions aisi hain jo galat wajah se hoti hain aur log me sahi dikhti hain?**
`attempts` ke teen carriers ab pata hain — job failure, kho hua mark (`D-26` `Cost 6`), aur ab infrastructure
fault (`P-51`). **Teeno ek hi counter badhate hain, aur `MAX_ATTEMPTS = 3` teeno ko ek jaisa treat karta hai.**
Din 3 ka pehla sawaal isliye retention nahi — wo hai: **kya `attempts` ek number hai, ya use do hona chahiye?**

---

*Plan:* [`../planning/WEEK_05.md`](../planning/WEEK_05.md) ·
*Din 2 BRIEF:* [`../daily/week_05/DIN_02_BRIEF.md`](../daily/week_05/DIN_02_BRIEF.md) ·
*Din 2 KEY:* [`../daily/week_05/DIN_02_KEY.md`](../daily/week_05/DIN_02_KEY.md) ·
*Seal:* [`../daily/week_05/DIN_02_PREDICTIONS_FROZEN.md`](../daily/week_05/DIN_02_PREDICTIONS_FROZEN.md)

---

## Din 3 — Publishing surface decide hui, seal held, aur din ka sabse bada finding ye hai ki rule ka **default publish** hai (`2026-09-26`)

**Layer L2, `C5` gate `100%` held: `git diff --name-only HEAD -- src/` → `0` files.** Do din ke baad pehla din
jisme `src/` ko chhua hi nahi gaya, aur wo ek gate tha, preference nahi.

**Aaj ka shape do din se ulta hai.** Din 1 aur Din 2 pe kaam *code* tha aur findings *traceback* se aaye. Aaj
kaam *policy* tha aur findings **census** se aaye. Aur wahi jagah hai jahan din chuka: rule theek likhi gayi,
`.gitignore` theek laga, teeno seal checks pass hue — **aur rule un chaar artifact classes ke baare me chup hai
jo disk pe maujood hain, to bees files bina faisle public ho gayi.** `P-54`.

**Seal ka SHA-256 reviewer ke independent hash se exactly match hua** —
`B2A10C31CB6C7F8DD149F70DEC81AAAD6ABF223F52EF05E0697B3B2CF661707B`. **Lagatar doosra din.**

---

### 📊 Measured / Observed

Saare numbers reviewer ne aaj live repository pe independently chalaye `[MEASURED 2026-09-26]`, user ke report
ke against — uske replacement nahi.

**1. Git surface, before aur after.**

| Cheez | Value | Note |
|---|---|---|
| `git ls-files` | `57` | unchanged, kyunki aaj commit se pehle naapa |
| `git ls-files docs/` | `11` | `P-47` amendment ka `eleven` confirm |
| disk `docs/` files | `133` | `130` Din 2 pe. `+3` = aaj ke BRIEF, KEY, FROZEN — **instrument apna output gin raha hai**, KEY ne isko naam se predict kiya tha |
| `logs/` paths ever committed | **`0`** | poori history, unchanged |
| `git add -A --dry-run` | **`69` paths** | `.gitignore` ke baad kya publish hoga |
| would-stage `*KEY*` | **`0`** | |
| `logs/` files on disk | `147` | `145` + do retention-probe files |

**2. Teeno seal checks, aur chautha control.** `C2` poora pass `[MEASURED 2026-09-26]`:

```
(git ls-files -- "*_KEY.md").Count                                        → 0
(git ls-files | Select-String -CaseSensitive "KEY").Count                 → 0
(git ls-tree -r --name-only HEAD | Select-String -CaseSensitive "_KEY\.md").Count → 0
git check-ignore -v --no-index docs/daily/week_05/DIN_03_KEY.md
  → .gitignore:47:**/daily/**/*KEY*.md    docs/daily/week_05/DIN_03_KEY.md
(git ls-files -- "*.pyc").Count                                           → 1   ← positive control
```

**Index, commit tree, aur pattern — teen alag cheezein, teeno `0`/`0`/ek line. Control `1`.** Ye pehla gate
iss hafte ka hai jo apne aap ko verify karta hai.

**3. `Q2` ka mechanism, user ke apne run se confirm.** `**/daily/` + `!**/daily/**/*BRIEF*` pe
`git add -A --dry-run` me `0` daily files. **Directory pruning** — ignored directory ke andar git jaata hi nahi,
to negation evaluate hi nahi hoti. Isliye final pattern negation nahi, **file-level ignore** hai:
`**/daily/**/*KEY*.md`.

**4. Teen `.gitignore` lines, aur intersection `7` → `2`.**

```
git ls-files | git check-ignore --no-index --stdin -v
  .gitignore:10:!.env.example    .env.example                                  ← negation, defect nahi
  .gitignore:19:__pycache__/     labs/__pycache__/day1_async.cpython-313.pyc   ← ek asli defect
```

**Honest count `6` → `1` hai, `7` → `2` nahi** — `.env.example` dono taraf noise hai, aur KEY ne isko trap `10`
me naam se likha tha. Paanch `docs/month_01/logs/WEEK_0*.md` anchor lagne se set se nikle.

**5. Artifact class census, poori — aur yahan din chuka `[MEASURED 2026-09-26]`:**

| Class | Count | `D-32` table me? | publish hota hai |
|---|---|---|---|
| `KEY` | `26` | haan, `Local` | nahi ✅ |
| `BRIEF` | `26` | haan, `Public` | haan ✅ |
| `PREDICTIONS_FROZEN` | `13` | haan, `Public` | haan ✅ |
| `HANDOFF` | `6` | haan, `Public` | haan ✅ |
| **`ANSWERS`** | **`13`** | **nahi** | **haan** |
| **`DESIGN`** | **`5`** | **nahi** | **haan** |
| **`PROBLEM`** / **`PROPERTY`** | **`2`** | **nahi** | **haan** |
| `UNCLASSIFIED` | `40` | directory rules se | zyadatar nahi |

**Step 1 ne chaar classes ginn ke `71` ka total nikala, disk pe `133` hain. `62` classify nahi hue, aur unme se
`20` public ho gaye.** `P-54`.

**6. Pattern ke do hole, probe se — padhne se nahi milte `[MEASURED 2026-09-26]`:**

| Path | Natija |
|---|---|
| `docs/daily/DIN_04_KEY.md` (bina week folder) | ignored — `**/` zero directories bhi match karta hai |
| `docs/daily/week_06/KEY_DIN_01.md` | ignored — `*KEY*` position-independent |
| **`DIN_04_KEY.txt`** | **publishes** — pattern `.md`-bound |
| **`DIN_04_SEALED.md`** | **publishes** — seal literal token `KEY` pe khadi hai |
| `DIN_04_key.md` | ignored **yahan**, kyunki `core.ignorecase = true`. `gitignore(5)` glob case-sensitive hai, to Linux clone pe ye publish hoga `[INFERRED — run nahi kiya]` |

**7. `Q5` ka `11 == 11` collision, independently reproduce hua `[MEASURED 2026-09-26]`:**
`pip freeze` `35` · `pip list --not-required` `11` · aur wo gyarah me `pip==26.0.1` **extra** hai,
`psycopg` + `psycopg-binary` **split** hai, `sqlalchemy` aur `pytest` **missing** hain. `requirements.txt` ab
`11` pins, `psycopg[binary]==3.3.4` extra ke saath, `pip` nahi.
`pip install --dry-run --ignore-installed` exit `0`, **`35` packages resolve** — fresh resolve pe koi conflict
nahi, aur wo KEY ki *"ye measure karna hai"* wali row thi.

**8. `P-52` ka artifact theek, aur script bhi `[MEASURED 2026-09-26]`:** log lines `23`–`26` pe
`[NOT MEASURED — see P-52]`, aur **teen lines ki provenance alag-alag likhi hui** (Din 1 quote · script
assertion · derived inference). `step5_preping_bench.py` me `p99` nearest-rank
(`max(0, math.ceil(0.99*n) - 1)`, line `53`), `os.remove` `0` matches, `RUN_ID` filename me.

**9. Retention check pass hua, aur wo galat script pe pass hua `[MEASURED 2026-09-26]`.** `C3` row 1 ne `2` log
files maangi aur `2` mili — par wo `scratch/test_probe_retention.py` ne likhi, jiska run id **microseconds**
(`%f`) hai. Jis script me fix hai, `step5_preping_bench.py`, uska run id **seconds** hai:

```
bench_runid_a = 20260926_063806
bench_runid_b = 20260926_063806
collide       = True
```

**Ek hi second me do run ka filename same, doosra pehle ko overwrite — ye `P-50` ka exact mechanism hai, `P-50`
jis script ko blame karta hai usi ke andar zinda.** `P-50` amendment.

**10. `step6_harness.ps1` history se padhi ja sakti hai `[MEASURED 2026-09-26]`:**
`git show 997f5cd:scratch/step6_harness.ps1` → `3068` bytes. `997f5cd` me commit, `2582b37` me untrack.
**`Q4` ka ulta half confirm.**

**11. Close bench, saara pass `[MEASURED 2026-09-26]`:**

| Gate | Expected | Measured |
|---|---|---|
| `git diff --name-only HEAD -- src/` | `0` | **`0`** ✅ |
| `src` hashes | teen | `a2ec8e9f…` `edcde815…` `dcdb6343…` |
| `alembic heads` | ek, `w4d4_sink_unique` | **`w4d4_sink_unique (head)`** ✅ |
| `except BaseException` in `src/` | `0` | `0` ✅ |
| Relay python processes | `0` | `0` ✅ |
| Nau counters | delta `0` | **`133\|145\|19\|4\|7\|39\|5\|0\|1`** ✅ |
| `pg_database LIKE 'relay\_%'` | `0` | `0` ✅ |

---

### 🧠 Prediction review — `0.00 / 5.0` scored, aur calibration `5/5`

Frozen text `docs/daily/week_05/DIN_03_PREDICTIONS_FROZEN.md` se **quote**, hash verify hua.

| Q | Frozen text (verbatim) | Measured | Score |
|---|---|---|---|
| **Q1** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q2** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q3** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q4** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q5** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |

**Total: `0.00 / 5.0`.** Self-score bhi `idk × 5` — **koi self-score inflation nahi.**

**Provenance, aur ye score se zyada important hai.** Paanchon jawab run se aaye, kisi bhi jawab me KEY pehle
nahi khuli, aur paanchon me se **char** ke mechanism user ne apne run ke output se likhe: `Q1` ka *"index-level
property, `.gitignore` already-tracked file ko untrack nahi karta"* · `Q2` ka *"directory pruning"* ·
`Q4` ka *"faisla `2582b37` ne kiya"* · `Q5` ka teen-defect breakdown. **Ye `0/5` ek `0/5` jaisa nahi hai — ye
`0` predicted aur `4` derived hai**, aur Din 1 ka `0/9` uske ulta tha.

**Ek line jo genuinely earned hai:** paanch me se paanch `idk` **honestly** likhe gaye. Din 2 pe do self-scores
zyada the aur unme se ek report ke apne data ke khilaaf tha. **Aaj zero.** Week 4 Din 6 ke `0/5` reading gap se
ab do din ka clean calibration record hai.

**Aur ek baat jo `0/5` ke saath likhni zaroori hai:** paanchon sawaal **Situation 2** the — samajh me aaye,
jawab pata nahi tha. Protocol ke hisaab se `idk` sahi jawab tha aur experiment hi uska raasta tha. **`idk` ko
avoid karne ki cheez samajhna hi wo galti hoti jo aaj nahi hui.**

---

### 🤖 Reviewer ki apni galat predictions — record ke liye

1. **`alembic heads` ko decorative gate samajh liya — galat, aur measurement se apni hi galti pakdi.** Pehle do
   run me command ne console pe kuch print nahi kiya, exit `0`, aur reviewer ne likhna shuru kiya ki *"ye gate
   hamesha pass karega"*. **File redirect karne pe `25` bytes aaye — `w4d4_sink_unique (head)` — aur
   pipeline capture pe bhi `1` line.** Khaali console reviewer ke apne tooling ka artifact tha, alembic ka nahi.
   **Gate sound hai.** `[MEASURED 2026-09-26]`
2. **`DIN_03_BRIEF.md` ka `C6` row galat likha tha.** *"Job `108` · `128` · `136` → `dead_letter|4|0` ·
   `succeeded|4|4` · `running|1|1`"* — teesra column teeno rows me **alag cheez** maangta hai: `108` pe
   `side_effects`, `128`/`136` pe `job_executions`. Ek hi query teeno ko satisfy nahi karti. Measured:
   `108|dead_letter|4|execs=1|effects=0` · `128|succeeded|4|execs=4|effects=1` · `136|running|1|execs=1|effects=0`.
   **State bilkul unchanged hai — column ka matlab BRIEF me ambiguous tha.** Ye `[MEASURED-R 2026-09-25]` wali
   row Din 2 ke close se hi aise likhi gayi thi. **BRIEF ka defect, user ka nahi.**
3. **KEY ne `Q2` Arm 3 ka default-open cost naam se likha, `DIN_05_ANSWERS.md` samet — aur `C1` aisa design
   kiya jo us cost ko dekh hi nahi sakta.** `C1` ki teen rows sirf `BRIEF` aur `KEY` poochti hain. **Trap likhna
   aur check likhna do alag kaam hain, aur aaj wo disconnect KEY ke apne page pe tha.** `P-54` ki teesri
   section wahi hai.
4. **KEY ne `logs/` ke `145` files likhe; aaj `147` hain.** Do retention-probe files aaj bani. Trivial, par
   number Din 6 ke reconcile me aayega.

**KEY ne jo theek kaha, aur ye teeno aaj live confirm hue:** directory pruning ka poora mechanism (`Q2`) ·
`check-ignore` tracked files ko skip karta hai aur `--no-index` chahiye (`Q3a`) · `ls-tree` pathspec wildmatch
nahi hai aur positive control ke bina `0` ka matlab nahi (`Q3a` addendum) · `11 == 11` coincidence aur teen
defects (`Q5`) · `step6_harness.ps1` history me zinda (`Q4`) · `.env.example` negation noise (trap `10`) ·
`BRIEF`/`KEY` ki ginti `26` aayegi `25` nahi (instrument apna output ginta hai) · aur *"fresh resolve measure
karo, predict mat karo"* — resolve chala, `35` packages, conflict `0`.

---

### 💡 What I understood — own words, 2026-09-30

1. Git me directory-level ignore rule (`**/daily/`) poori directory ko traverse hone se prune kar deta hai, jisse uske andar negation patterns (`!**/daily/**/*BRIEF*`) evaluate hi nahi hote (`docs/daily/week_05/DIN_03_BRIEF.md`). Isliye negation ke bajay direct file-level ignore `**/daily/**/*KEY*.md` use karna padta hai.
2. Seal audit me index (`git ls-files`), commit history (`git ls-tree`), aur pattern rules (`git check-ignore --no-index`) teen alag layers hain; tracked `.pyc` (count 1) positive control ki tarah prove karta hai ki checks bina pattern match ke empty output dekar false pass nahi ho rahe.
3. Incomplete allow-list security hole ban jaati hai (`P-54`): `D-32` ne 133 files me se sirf 4 classes (71 files) classify ki, jisse 20 files (`ANSWERS` 13, `DESIGN` 5, `PROBLEM` 2) default-open behavior ke karan public stage hone ke khatre me aa gayi.
4. `requirements.txt` me 11 pins aur `pip list --not-required` me 11 packages ka count match hona coincidence tha; `pip` extra tha, `psycopg` binary split tha, aur `sqlalchemy` missing tha. Fresh resolve par 35 packages clean install hue.
5. Log retention verification script (`scratch/test_probe_retention.py`) microsecond timestamp use karke pass ho gaya, jabki actual probe (`step5_preping_bench.py`) me second-level timestamp hone ke karan ek hi second me collision aur file overwrite ka risk zinda raha (`P-50`).

Gaps vs reviewer: Reviewer ne emphasize kiya ki rule ka shape un cheezon ka faisla leta hai jinke baare me rule chup rehta hai (default-open behavior), aur verification naye scratch script se satisfy hone par actual target script ka bug chhupa reh sakta hai.

### 💡 What the session established — **user ko ye apne shabdon me dobara likhna hai**

> Ye section reviewer ne likha hai. Protocol ke hisaab se isko user ke apne shabdon me replace hona hai —
> aur ye Week 2 se chal raha `💡` debt hai, isliye ye line yahan naam se hai.

1. **Ek allow-list ka default uske enumeration se aata hai, uske intent se nahi.** `D-32` ne chaar classes
   likhi aur nau exist karti hain, to paanch classes ka faisla *"publish"* ho gaya — kisi ne wo faisla liya
   nahi. **Rule ka shape faisla leta hai un cheezon ke baare me jinke baare me rule chup hai**, aur `.gitignore`
   ka default-open shape ne bees files ke liye wo faisla le liya.
2. **Ek check apne blind spot ke baare me chup rehti hai, aur wo chuppi pass jaisi dikhti hai.** Din 2 ka `413`
   gate *galat* tha. Aaj ka `C1` **sahi** hai — wo do failure modes ko theek se separate karta hai. Uska domain
   chhota tha. **Ek check jo galat hai aur ek check jiska domain chhota hai, output me dono `pass` likhti hain.**
3. **Verification ek naye file se satisfy ho jaye, to wo verification uss file ke baare me hai.** `C3` ne *"do
   log files"* maangi aur ek naya nine-line script bana ke wo mil gayi — jabki jis script me bug tha, usme
   bug ki shape (second-granular run id) abhi bhi hai. **Check ka subject named script hona chahiye tha, property
   nahi.**
4. **Tracking ek index-level property hai; ignoring ek pattern-level property hai; aur dono ek teesri cheez —
   history — ko control nahi karte.** `.pyc` paanch hafte se tracked hai kyunki pattern baad me aaya.
   `step6_harness.ps1` `HEAD` me nahi hai aur `997f5cd` se verbatim padhi ja sakti hai. **`.gitignore` sirf
   aage ka faisla karta hai, aur publishing ka faisla one-way door hai.**
5. **Ek tool ka output aur ek finding do alag cheezein hain.** `check-ignore -v` ne saat lines di aur unme se ek
   negation thi, paanch anchor-fix se khud hal ho gayi, aur **asli defect ek tha.** *"Saat files"* likhna tool ka
   output quote karna hai; *"ek defect"* likhna finding hai.
6. **Aaj ka din pehla din tha jisme sabse bada finding kisi crash se nahi, ek ginti se aaya.** Din 2 ne kaha
   tha *"jo failure crash nahi karta wo crash-reading se nahi milta"*. Aaj uska agla step mila: **jo cheez rule
   me likhi hi nahi, wo rule padhne se nahi milti — census se milti hai.**

---

### ⚠️ Closeout corrections

| # | Jaise report hua | Jo measured hai | Provenance |
|---|---|---|---|
| 1 | *"C1 & C2 Seal Checks Passed"* + policy table ki nau rows | **Seal checks poore sach hain** (`0`/`0`/ek line/control `1`). Par policy table chaar artifact classes cover karti hai aur disk pe **nau** hain. **`ANSWERS` `13` · `DESIGN` `5` · `PROBLEM` `1` · `PROPERTY` `1` — bees files bina faisle publish ho rahi hain**, aur `C1` structurally unhe dekh nahi sakta. **`P-54`** | `[MEASURED 2026-09-26]` full census + dry-run |
| 2 | *"`git ls-files ∩ ignored`: `7` files"* | **Honest count `6` tha, aur ab `1` hai.** `.env.example` line `10` ki **negation** se match hui — wo ignored nahi hai, deliberately re-included hai. `check-ignore -v` *"deciding line"* batata hai, *"ignored"* nahi — KEY trap `10`. Paanch Month 1 logs anchor-fix se nikal gaye. **Bacha hua ek: `.pyc`** | `[MEASURED 2026-09-26]` |
| 3 | *"Probe retention rule verified: harness do baar chalane pe `2` distinct log files"* | **`2` files mili, par wo `test_probe_retention.py` ne likhi** (`%f`, microseconds), **na ki `step5_preping_bench.py` ne** (`%H%M%S`, seconds). Measured: bench ke do consecutive run id **identical** → filename collide → overwrite. **`P-50` ka mechanism usi script me zinda hai jisko `P-50` blame karta hai.** Fix ek character: `_%f` | `[MEASURED 2026-09-26]` |
| 4 | *"`D-32` Selected Option 1: Directory split + path anchoring"* | Pattern **file-level ignore** hai (`**/daily/**/*KEY*.md`), directory split nahi — aur wo farak load-bearing hai. **Directory-level rule kaam nahi karta**, jo user ne khud measure kiya (`Q2`, `0` files staged). Naam KEY ke Arm 3 ka hai: *"sab track hota hai, siwaay KEY"*. **Uska cost default-open hai aur wahi `P-54` hai** | `[MEASURED 2026-09-26]` |
| 5 | *"`docs/daily/**/*KEY*.md` -> Local (Ignored to preserve epistemic seal)"* | Seal `.md` par aur literal token `KEY` par khadi hai. **`DIN_04_KEY.txt` aur `DIN_04_SEALED.md` dono publish hote hain.** Aur `DIN_04_key.md` yahan sirf `core.ignorecase = true` se ignored hai — **Linux clone pe wo publish hoga**, kyunki `gitignore(5)` glob case-sensitive hai | `[MEASURED 2026-09-26]` local; `[INFERRED]` Linux |
| 6 | *"`P-51` … Decision held for implementation in Week 6 (Month 2)"* aur *"Alternative (Control-Flow Decoupling) … Zero schema change needed"* | **Faisla sahi hai aur uska naya cost table me nahi tha.** `record_execution` ko handler ke `try` se bahar karne pe recovery `attempts`-bounded se **lease-bounded** ho jaati hai: row `running` rehti hai live `claimed_at` ke saath, aur reaper `30 s` baad reclaim karta hai (`D-22`). **`attempts` bachta hai, wall-clock kharab hota hai.** Wo naya cost `P-51` amendment me likha gaya. `[INFERRED — land hone pe naapna hai]` | `[MEASURED 2026-09-26]` `src/` diff `0` |
| 7 | *"Clean 11 Direct Pins Implemented"* | **Sach, aur `C4` ke paanchon sub-checks pass** (`11` · extra preserved · `pip` absent · `sqlalchemy`+`pytest` present · dry-run exit `0`, `35` resolved). **Ek cheez likhni chhoot gayi jo `D-33` maangta hai: operator ka kaaran.** Wo entry me likha gaya — `~=` reject hua kyunki wo do run ke beech unreviewed patch change allow karta hai, aur CI na hone pe wo pehli baar failing run ke roop me dikhega | `[MEASURED 2026-09-26]` |
| 8 | *"`logs/w5d2_step5_preping.log` annotated honestly: lines 23-26"* | **Confirm, aur ye din ka ek genuinely achha call hai.** Delete karne se teen lines ki **alag-alag provenance** (Din 1 quote · script assertion · derived inference) mit jaati. **Par annotation artifact pe hai, generator pe nahi** — bench abhi bhi wahi lines print karta hai, to next run ek unannotated copy banayega | `[MEASURED 2026-09-26]` |
| 9 | *"`scratch/d32_classification_rule.md` me draft"* | Draft theek likha hai. **Par wo file `scratch/` me hai, jo `.gitignore` se ignored hai — matlab publishing ka faisla ek unpublished file me hai.** Aaj ke liye acceptable (`D-32` ka final text Din 6 ka hai), aur isliye reviewer ne `D-32` ko `docs/DECISIONS.md` me `DRAFT` status ke saath likh diya hai, taaki wo tracked ho | `[MEASURED 2026-09-26]` |
| 10 | Din 3 BRIEF ka `C6`: *"Job `108` · `128` · `136` → `dead_letter|4|0` · `succeeded|4|4` · `running|1|1`"* | **Gate ka teesra column teeno rows me alag cheez maangta hai** — `108` pe `side_effects`, baaki do pe `job_executions`. Ek query teeno ko satisfy nahi karti. Measured: `108` execs `1`/effects `0` · `128` execs `4`/effects `1` · `136` execs `1`/effects `0`. **State unchanged; BRIEF ka defect** | `[MEASURED 2026-09-26]` |

---

### 🚧 Unresolved / carried

1. **`P-54` — `D-32` ka default publish hai.** Bees files chaar unenumerated classes me. **Teen faisle chahiye:
   `ANSWERS` · `DESIGN`/`PROBLEM`/`PROPERTY` · aur rule ka shape (ignore-allow-list vs publish-allow-list).**
   **Owner: Din 6, `D-32` ke final text ke saath.** Aaj `D-32` `DRAFT` hai isi wajah se.
2. **`P-50` narrowed, band nahi.** Rule likhi hui hai, ek script collision-safe hai, doosri nahi.
   `restart_to_first_claim` ka start clock abhi bhi console-only hai.
3. **`P-51` decided, implemented nahi.** Behaviour bilkul waisi hai jaisi Din 2 pe naapi thi — `src/` hash
   unchanged. **Owner: Week 6.** Naya lease-bounded cost `[INFERRED]` hai, land hone pe naapna hai.
4. **`P-52` ka generator.** Bench abhi bhi wo lines print karta hai. Artifact theek hai, script nahi.
5. **`labs/__pycache__/day1_async.cpython-313.pyc` abhi bhi index me hai.** Paanch hafte, do patterns jo usko
   match karte hain, aur kuch nahi hua. **Faisla ye hai: `HEAD` se hataao aur maano ki blob `01f42c6` me rahega,
   ya chhod do.** *"Clean karo"* koi option nahi hai. **Owner: Din 6.**
6. **`logs/` retention ka doosra half — kitne din, kaunsi files.** Deliberately aaj nahi likha. **Owner: Din 6
   ke baad.** `147` files.
7. **History me padi evidence.** `docs/blog/` ke nau, `scratch/`, `docs/career/`, `docs/dsa/` — sab readable.
   `D-32` isko naam se out-of-scope karta hai.
8. **Pin file lock file nahi hai.** `11` direct pinned, `24` transitive free. **Narrowed, not reproducible.**
9. **`P-36`, supervisor backoff, `30 s` crash-loop run, `D-30` `OPEN`, README rows 7/9** — sab Din 2 se
   unchanged. Aaj ka koi change inko **chhuta nahi**.
10. **Din 5 ke chaar khoye hue measurements — Din 4 ka kaam**, aur ab unke liye retention rule maujood hai.

---

### ❓ Next thought

Aaj do din ki technique khatam hui. Din 1–2 ne *traceback* padh ke chaar boundaries dhoondhi; Din 2 ne kaha ki
jo failure crash nahi karta wo crash-reading se nahi milta, aur `P-51` **state** padh ke mili. **Aaj teesri
technique chahiye padi: `P-54` na crash se mili na state se — wo ek *census* se mili.** Rule padhne se nahi
dikhi, kyunki rule usme chup thi. **To agla sawaal ye hai: Relay ke andar kaun-kaun si rule apne default se
faisla le rahi hai, us cheez ke baare me jiske baare me wo likhi nahi gayi?**

`MAX_ATTEMPTS = 3` teen carriers pe lagta hai aur teeno ko ek jaisa treat karta hai — wahi shape hai.
`jobs.type` unconstrained `text` hai (`D-04`) aur validation application me hai — wo bhi. Aur Din 4 ka pehla
sawaal isliye *"lost measurements"* nahi hai. Wo hai: **jab ek worker, ek reaper aur ek dispatcher ek saath
chalte hain, to kaunsa outcome kisi ke faisle se nahi, teen defaults ke overlap se aata hai?**

---

*Plan:* [`../planning/WEEK_05.md`](../planning/WEEK_05.md) ·
*Din 3 BRIEF:* [`../daily/week_05/DIN_03_BRIEF.md`](../daily/week_05/DIN_03_BRIEF.md) ·
*Din 3 KEY:* [`../daily/week_05/DIN_03_KEY.md`](../daily/week_05/DIN_03_KEY.md) ·
*Seal:* [`../daily/week_05/DIN_03_PREDICTIONS_FROZEN.md`](../daily/week_05/DIN_03_PREDICTIONS_FROZEN.md)

---

## Din 4 — Premise pehli baar observe hui, do khoye hue number retained artifact ke saath **replace** hue, aur din ke sabse valuable step ka headline number ek lock nahi, ek process-launch clock hai (`2026-09-27`)

**Layer L2, `src/` gate held: `git diff --name-only HEAD -- src/` → `0`, paanchon hashes Step 0 ke barabar.**
Lagatar doosra din jisme `src/` nahi chhua gaya, aur aaj ka poora kaam configuration aur measurement tha.

**Aaj ka sabse saaf result `C1` hai, aur wo exactly `P-45` ka gate tha.** Teen rows, teeno ek file me: import-time
print `pool=2+0` (*set hua*) · `pg_stat_activity` peak `api_w5d4|2|{active}` (*honour hua*) · teesra `/slow-hold`
`500 3.116546` (differential jo doosri row ke instrument pe bharosa nahi karta). **Aur ek chautha witness jo BRIEF
ne nahi maanga tha aur sabse strong hai:** `sqlalchemy.exc.TimeoutError: QueuePool limit of size 2 overflow 0
reached, connection timed out, timeout 3.00` — jo component limit enforce karta hai, wahi uski value bol raha hai.
Week 4 Din 5 se jo premise *"set hui thi"*, aaj *"honour hui"* hai.

**Aur din wahi chuka jahan BRIEF ne kaha tha ki sabse valuable output hoga.** Step 5 ka `7.6771 s` artifact me
*"Outbox Row Lock Duration: Held for 7.6771 s across the HTTP call"* likha hai — par `disp_t0` `subprocess.Popen`
se **pehle** set hota hai, to wo number dispatcher ka interpreter start + imports + engine handshake (`~2.6 s`) +
`5.0 s` httpx timeout hai. **Lock kabhi naapa hi nahi gaya:** probe ka ek-matra lock snapshot dispatcher ki pehli
SQL line (`13:44:02.420`) se pehle liya gaya, to usme sirf `holder_w5d4` ki rows hain. Aur usi file me ek prewritten
line *"error=The read operation timed out"* kehti hai, jabki do section upar asli line `error=` hai — **khaali.**
`P-52` ki shape, teesri baar, aaj ke dono naye generators me.

**Seal lagatar teesre din held:** `DIN_04_PREDICTIONS_FROZEN.md` SHA-256
`62196E9A6186A030BB59461D090A2544C31914007184FD859A114BB0BCCC909D` reviewer ke independent hash se exact match.
**Par file abhi kisi commit me nahi hai** (`git ls-files` → `0`). Din 3 ne frozen file ko pehli baar third-party
auditable banaya tha; **Din 4 ka hash tab tak sirf report aur reviewer ke beech hai jab tak Din 4 commit nahi hota.**

---

### 📊 Measured / Observed

Reviewer ne har user artifact padha aur teen differentials jo nahi chale the, khud chalaye. **Reviewer ke runs
`[MEASURED-R 2026-09-27]` hain, har ek `logs/w5d4r_*` me, aur har generator ka source uske apne log ke andar
embedded hai** — script `%TEMP%` me thi aur run ke baad delete hui, to generator artifact ke saath zinda hai (`P-45`
ka sabak reviewer pe bhi lagta hai).

#### 1. Bench — close pe, reviewer ke teen API runs ke **baad** dobara (`logs/w5d4r_close_bench.txt`)

| Gate | Measured |
|---|---|
| `git diff --name-only HEAD -- src/` | **`0`** ✅ |
| paanch `src` hashes | `a2ec8e9f…` `edcde815…` `dcdb6343…` `d55e3b8a…` `fc5bde22…` — Step 0 ke barabar ✅ |
| `alembic heads` | `w4d4_sink_unique (head)` ✅ |
| `except BaseException` in `src/` | `0` ✅ |
| nau counters, evidence DB `relay` | **`133\|145\|19\|4\|7\|39\|5\|0\|1`** — delta `0` on the nine counters ✅ |
| jobs `108` · `128` · `136` (status\|attempts\|execs\|effects) | `dead_letter\|4\|1\|0` · `succeeded\|4\|4\|1` · `running\|1\|1\|0` — untouched ✅ |
| `pg_database LIKE 'relay\_%'` | `0` ✅ |
| Relay python processes | `0` ✅ — host pe ek non-Relay python hai (KiroCrew), wahi jo Din 2 ke `(Get-Process python).Count` ko `1` bana raha tha |
| `*_KEY.md` in index · in `HEAD` tree · `*.pyc` control | `0` · `0` · `1` ✅ |
| `P-54` surface (`ANSWERS\|DESIGN\|PROBLEM\|PROPERTY` untracked) | **`20`** ✅ — kuch stage nahi hua, koi naya unclassified class nahi bana |
| untracked total | `23` = `20` + `DIN_04_PREDICTIONS_FROZEN.md` + do `labs/w5d4_*.py` |
| `git ls-files labs/w5d4_*` | **`0`** — `C5` row 3 as written **fail** hai. Files ignored nahi hain (`check-ignore` khaali), bas stage nahi hui |
| `HEAD` | `cbdea0c` — sirf `DIN_04_BRIEF.md`, koi KEY nahi. BRIEF ka Step 0 `e3121a3` expect karta tha; wo reviewer ki apni BRIEF-commit ke baad stale tha |
| `logs/` files | `159` (`146` pehle ki + `13` `w5d4_*`). Din 3 ne `147` likha tha — **ek file ka farak, record se identify nahi hota.** Din 6 ke reconcile ka item |

#### 2. `C1` — premise observed, aur ek zero jo structurally retain nahi ho sakta tha

| Observation | Value | File |
|---|---|---|
| import-time print | `resolved_db=relay app_name=api_w5d4 pool=2+0` | `w5d4_step1_api.log:1` |
| idle count | **`0` — report me hai, file me nahi** | `w5d4_step1_idle.txt` **exist nahi karti** |
| peak count | `api_w5d4\|2\|{active}` | `w5d4_step1_peak.txt` |
| teesra `/slow-hold` | `500 3.116546` | `w5d4_step1_peak_clients.txt` |
| engine ka apna bayan | `QueuePool limit of size 2 overflow 0 reached … timeout 3.00`, **paanch baar**, har baar `pool\impl.py:167 _do_get` se | `w5d4_step1_api.log` |

**Idle file ka ghayab hona ek mechanism hai, aur wo mechanism BRIEF ka hai** (`logs/w5d4r_tee_empty_probe.txt`,
pwsh `7.6.6`):

| Arm | Command | File bani? |
|---|---|---|
| A | Step 1 ka exact idle query (`GROUP BY`, `0` matching rows) `\| Tee-Object` | **nahi** |
| B | wahi filter, `count(*)` **bina** `GROUP BY` `\| Tee-Object` | haan, content `0` |
| C | `@() \| Tee-Object` | **nahi** |
| D | `@() \| Out-File` | haan, `0` bytes |

**`Tee-Object` khaali pipeline pe file banata hi nahi, aur `GROUP BY` zero rows pe koi line nahi deta.** To BRIEF ka
idle command ek zero ko **kabhi** retain nahi kar sakta tha — aur usi BRIEF ne `Tee-Object` ko *"`P-53` ke rule ka
sabse sasta compliance"* likha tha. Reviewer ne idle dobara naapa, `count(*)` bina `GROUP BY`, teen alag API
processes pe: **`total=0`** teeno me, aur pehli DB request ke baad `total=1 idle` — lazy allocation, ab file me
`[MEASURED-R]`.

**Aur engine ka error message ek aur cheez prove karta hai:** ceiling **API process ke andar** enforce hui. Paanchon
`TimeoutError` `sqlalchemy/pool/impl.py:167` pe raise hue; teen `500` wale `/slow-hold` ka `SELECT pg_sleep` API log
me kabhi issue hi nahi hua (`pg_sleep` statements `9` = `2+2+2+2+1`, teen `500` requests ka ek bhi nahi), aur
`/healthz`/`/db-ping` ka `SELECT 1` bhi **`0`** baar. Postgres ne `2` dekha kyunki teesri request uske paas pahunchi
hi nahi.

#### 3. `C2` — bound ab isolated hai, aur differential reviewer ne chalaya

User ke dono Step 2 runs **ek hi** uvicorn process pe the — `resolved_db=` API log me ek baar, PID `14628` — aur
dono ka message `timeout 3.00`. **To `C2` row 2 (*"`RELAY_POOL_TIMEOUT` badal ke ek doosra run"*) chala hi nahi,
jabki report ne *"Bound isolated"* likha.** Reviewer ka teen-arm run, same `src.main:app`, same `echo=True`,
evidence DB pe sirf read-only endpoints (`logs/w5d4r_c2c3_20260927_091113_681447.log` + teen
`w5d4r_api_t*_…log`):

| `RELAY_POOL_TIMEOUT` | teesra `/slow-hold` | `/healthz` saturated | `/db-ping` saturated | `/health` saturated | peak | engine ka text |
|---|---|---|---|---|---|---|
| `1.5` | `500 1.5878 s` | `500 1.5634 s` | `500 1.5640 s` | `200 0.0290 s` | `2 active` | `timeout 1.50` |
| `3.0` | `500 3.0956 s` | `500 3.0674 s` | `500 3.0658 s` | `200 0.0312 s` | `2 active` | `timeout 3.00` |
| `5.0` | `500 5.0755 s` | `500 5.0622 s` | `500 5.0601 s` | `200 0.0299 s` | `2 active` | `timeout 5.00` |

**Teen configs, teen elapsed, aur har ek apne config ko follow karta hai** — overhead `+60`–`+96 ms`, teeno arms me
lagbhag constant. **Ab ye claim earned hai ki bound `pool_timeout` hai.** Aur `/healthz` bhi follow karta hai, to
uska latency `SELECT 1` ka nahi — pool queue ka hai.

**Aur `3.0055 s` reproduce NAHI hua. Replace hua.** Aaj `pool_timeout = 3.0` pe aath measurements, teen clients:
overhead `+32.7` (`/healthz`, curl) · `+37.1` (`/db-ping`, curl) · `+43.0` · `+50.1` (user probe) · `+116.5`
(curl, Step 1) · `+65.8` · `+67.4` · `+95.6 ms` (reviewer). Week 4 Din 5 ka overhead `+5.5 ms` tha — **aaj ke
minimum se lagbhag `6×` chhota.** Bound wahi hai, overhead nahi, aur bina artifact ke ye pata nahi ki `+5.5 ms` kis
cheez ka tha. Probe ki line *"Reproduced at 3.0501 s"* kisi bhi value pe wahi likhti. Plan ne pehle hi likha tha:
*"replacement, confirmation nahi."*

#### 4. `C3` — control reviewer ne chalaya, aur discriminator abhi aadha hai

**Unsaturated control, teeno arms** `[MEASURED-R]`: `/health` `200` `0.010`–`0.014 s` · `/healthz` `200`
`0.168`–`0.182 s` (pehli DB request — connect cost, kyunki API ka koi `lifespan` nahi aur pool lazy hai) · `/db-ping`
`200` `0.015`–`0.016 s`. **`/healthz` saturation ke bina pass karta hai**, to Step 3 ki table ka matlab wahi hai jo
likha gaya.

User ka Step 3 (`w5d4_step3_discriminator.txt`): `health 200 0.006326` · `healthz 500 3.032650` · `db-ping 500
3.037055`. Saturating pair API log me `SELECT pg_sleep` `13:10:48.209`/`.234` → `ROLLBACK` `13:10:56.223`/`.248`,
to teeno requests saturation window ke andar the ✅.

**Par ye discriminator teen causes me se do hi alag karta hai.** `/health 200` *process dead* ko alag karta hai.
**Pool starvation aur DB down ko alag karne wali observation aaj naapi hi nahi gayi** — DB-down column `[NOT
TESTED]`, aur Q3(c) ka asli sawaal wahi tha. Aur BRIEF ki `C3` table me DB-down ki `pg_stat_activity` cell `0`
likhi thi — **galat:** DB down ho to wo query khud fail hoti hai. Observation *"`0`"* nahi, *"unobservable"* hai.
Reviewer ka defect.

#### 5. `C4` — client disconnect: din ka doosra sabse saaf result, aur usko settle karne wala instrument gate nahi, `echo` tha

| Cheez | Value | Source |
|---|---|---|
| snapshot 1 | `active\|SELECT pg_sleep($1)\|00:00:04.280962` + doosri connection `idle\|ROLLBACK;\|00:14:54` (Step 3 wali, `13:10:56.24` se idle) | `w5d4_step4_after_disconnect.txt` |
| statement start | `13:25:46.336 SELECT pg_sleep($1) (20.0,)` | API log (`echo`) |
| connection wapas pool me | `13:26:06.361 ROLLBACK` — **hold `20.025 s`** | API log (`echo`) |
| snapshot 2 | dono `idle\|ROLLBACK;` — **`13:31:28` pe liya gaya**, `seconds + 2 s` (`≈13:26:08`) pe nahi | `w5d4_step4_after_full_duration.txt` |
| access log me `seconds=20` request | **koi line nahi** — `11` `/slow-hold` lines, `12` requests | API log |
| disconnect ka moment | **kisi file me nahi** — `curl -m 3` ek `Start-Job` me, job output discard | — |

**Mechanism measured:** client `≤ 3 s` pe gaya, `pg_sleep` poore `20.025 s` chala, connection handler khatam hone
pe pool me wapas aayi. Cancellation propagate nahi hui. User ka *"connection lifetime is decoupled from HTTP request
lifetime"* bilkul sahi hai.

**Do cheez jo gate ke design ke baare me hain.** Snapshot 2 release se `5 min 22 s` baad liya gaya, to akela wo
*"`20 s` pe free hui"* ko *"`5 min` pe free hui"* se alag nahi kar sakta — **API log ka `ROLLBACK` timestamp karta
hai**, aur wo `echo=True` ki wajah se hai. **Aur access log ke hisaab se wo request hui hi nahi:** uvicorn
disconnected client ko response line nahi likhta. To orphaned request ka ek-matra nishaan `echo=True` ki do SQL lines
hain — aur `echo` band karna Week 6 ka candidate hai. `P-44` amendment.

#### 6. Step 5 — chain ek link tak compose hui; lock aur sink ki wait kabhi observe nahi hui

**Artifact me jo measured hai** (`logs/w5d4_step5_20260927_081356_093927.log`):

- holder ki uncommitted `INSERT` — snapshot me `holder_w5d4|idle in transaction`, `RowExclusiveLock` +
  `transactionid ExclusiveLock` granted
- dispatcher ka `SELECT … FOR UPDATE SKIP LOCKED` `13:44:02.464` pe (`echo`); dispatcher pool `5+10` (default)
- `[dispatch_error] job_id=42 outbox_id=1 error= attempts=1` — `error=` ke baad kuch nahi
- final: outbox `1` `attempts=1 dispatched_at=None` · outbox `2` `attempts=0` — **sirf ek dispatch attempt hua**

**Jo artifact nahi kehta, aur report ne kaha:**

| Report | Artifact |
|---|---|
| *"lock held … for 7.6771 s"* | `disp_elapsed = perf_counter() - disp_t0`, aur `disp_t0` `subprocess.Popen` se pehle set hota hai. Pehli engine line `13:44:02.420` — **`~2.6 s` sirf process start.** Lock duration nahi |
| *"holder … stalled Sink's `ON CONFLICT DO NOTHING`"* | ek-matra snapshot `t ≈ 2.0 s` (Popen se) pe, dispatcher ki pehli SQL se pehle → sirf holder rows. Sink ki wait **kabhi dekhi nahi gayi** `[INFERRED — 5.0 s ReadTimeout ke consistent]` |
| sink pool `2+0` | sink ka stdout ek `PIPE` me gaya jo kabhi padha nahi gaya, to uska `resolved_db … pool=2+0` kabhi observe nahi hua. **Jo premise-trap Step 1 ne todi, Step 5 ne usi din sink pe dobara bana di** |
| chain composed | holder ek attempt ke baad rollback ho gaya, to sink pe kabhi ek se zyada request nahi thi. KEY `Q5(b)` ka sink-pool arm `[NOT TESTED]` |

**Reviewer ne class naapi** (`logs/w5d4r_httpx_timeout_class_20260927_090729_963651.log`) — dispatcher ki exact
shape, `httpx.AsyncClient(timeout=5.0).post`, ek silent TCP server pe, httpx `0.28.1` / httpcore `1.0.9`:

```text
class=httpx.ReadTimeout      str_len=0      repr=ReadTimeout('')
__cause__=httpcore.ReadTimeout(TimeoutError())      isinstance(builtin TimeoutError)=False
timeout=5.0 → elapsed_s=5.0268      dispatcher_line_would_be='error='
```

**User ka claim *"`str(httpx.ReadTimeout)` is `""`"* sahi hai** — aur ab uska class naam se hai. Source se aur:
`src/` ki nau exception-print lines me se chhe `type(exc).__name__` likhti hain; dispatcher ki `[dispatch_error]`
**akeli** aisi hai jahan class na line me hai na kisi column me (`outbox` me error column hi nahi hai). **`P-55`.**
*(Reviewer ka probe dono arms log karne ke baad `async with server:` ke exit pe latak gaya — Python 3.12+ ka
`Server.wait_closed()` khuli connections ka intezaar karta hai — to dono `python.exe` haath se band kiye, source haath
se log me joda. Measurement lines us se pehle likhi ja chuki thi.)*

**Lock ka release mechanism, source se — aur Din 4 KEY yahan galat thi.** `except Exception` `async with
session.begin()` ke **andar** hai, to exception block se bahar nahi jaati; block normally exit hota hai → **`COMMIT`**
→ lock release, aur `attempts + 1` isi commit se persist hota hai. Final state `attempts=1` isse consistent hai. KEY
ne dono outcomes **rollback** ke likhe the. **Kitni der hold hua — `[NOT MEASURED]`. Din 5.**

#### 7. Step 6 aur Step 7 — faisla liya gaya, par repository me nahi likha gaya

- **Step 6 ka faisla sirf report me tha** — `ENABLE_TEST_ROUTES` repo me kahin nahi (grep, ignored files samet:
  `0`). Reviewer ne usko user ke shabdon ke saath `P-44` amendment me record kiya, aur `D-28` ka reconciliation
  `D-28` amendment me.
- **Faisla 3 ki record correction likhi gayi** (`docs/month_01/daily/week_04/DIN_05_DESIGN.md:32`) ✅ — pehla half
  sahi hai (`[NOT RETAINED]`, `P-45`). **Doosra half ek category error hai:** `labs/w5d4_pool_probe.py` teen `GET
  /slow-hold` bhejta hai; Faisla 3 ka `step4_load_probe.py` ek **load generator** tha (`400` jobs, `19.8 /s`
  arrival). Pool probe wo number dobara nahi naap sakta. BRIEF ne *"load/pool probe"* likh ke ye mix khud invite
  kiya tha. **Faisla 3 ka `Chosen` implementation `[NOT RETAINED]` hi rehta hai** — reviewer note file me joda gaya.
- Aur `DIN_05_DESIGN.md` khud `P-54` ki bees untracked files me se ek hai, to ye correction bhi **kisi commit me
  nahi** hai jab tak Din 6 `DESIGN` class decide nahi karta.

---

### 🧠 Prediction review — `0.00 / 5.0`, calibration `5/5`, aur teen me se teen derivable halves `idk`

Frozen text `docs/daily/week_05/DIN_04_PREDICTIONS_FROZEN.md` se **quote**, hash verify hua.

| Q | Frozen text (verbatim) | Measured | Score |
|---|---|---|---|
| **Q1** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q2** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q3** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q4** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q5** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |

**Total: `0.00 / 5.0`.** Self-score bhi `idk × 5` — **inflation zero, lagatar teesra din.** Week 5 frozen total:
**`1.45 / 20.0`**.

**Provenance, jo score se zyada batata hai.** Chaar mechanisms run se derive hue: `Q1` lazy pool + ceiling · `Q2`
bound + class · `Q3` `/health` vs `/healthz` · `Q4` cancellation absent — aur `Q4` wala din ka sabse saaf derived
mechanism hai. `Q5` aadha: `error=` khaali hona khud notice kiya, jo genuinely achha observation tha; lock ka number
galat instrument se aaya.

**Aur ek farak jo `0/5` ke andar chhupa hai.** KEY ke scoring note ne naam se likha tha ki `Q1(d)`, `Q3(c)` aur
`Q5(d)` **run se pehle derivable** hain. `Q3(c)` ka aadha jawab `src/main.py:16` me hai (`/health` pe koi
`Depends(get_db)` nahi); `Q1(d)` ka ek scenario `uvicorn --workers N` hai; `Q5(d)` `P-41` ke apne text me likha hai
(*"the symptom surfaces … while the actual cause is a lock inside the receiver's database"*). **Teeno `idk` aaye.**
Wo Situation 2 nahi the — source-reading ke the. Week 4 Din 6 ka reading gap, chhoti shakal me. `idk` likhna
galat nahi tha; question me naam liya hua code path pehle padhna chhoot gaya.

**Ek conceptual correction jo score se bahar hai aur zyada load-bearing hai:** report kehti hai *"PostgreSQL
strictly enforced the ceiling of 2 connections"*. **Nahi — `QueuePool` ne API process ke andar enforce kiya.**
Postgres ki apni ek hi limit hai (`max_connections = 100`), aur usne `2` isliye dekha kyunki teesri request uske
paas pahunchi hi nahi (upar section 2). `D-28` ki evidence line yahi kehti hai: *"pool exhaustion is client-side and
says so in the error."*

---

### 🤖 Reviewer ki apni galat predictions — record ke liye

1. **KEY `Q5(c)`: lock release ke dono outcomes rollback ke likhe.** Source me `except` `session.begin()` ke andar hai,
   to release **`COMMIT`** pe hota hai, aur wahi commit `attempts + 1` persist karta hai. `[MEASURED from source;
   final state consistent]`
2. **BRIEF Step 1 ka idle command ek zero retain nahi kar sakta tha** — `GROUP BY` + `Tee-Object`, dono zero pe
   chup. Aur BRIEF ne `Tee-Object` ko `P-53` ka compliance mechanism bataya tha. `[MEASURED-R, four arms]`
3. **BRIEF `C3` table ki DB-down `pg_stat_activity` cell `0` likhi thi** — DB down ho to query hi fail hoti hai.
4. **BRIEF Step 0 `git log -1` → `e3121a3` expect karta tha**; `HEAD` `cbdea0c` tha — reviewer ki apni BRIEF-commit,
   jo ye line likhne ke baad hui.
5. **BRIEF Step 7 ne *"load/pool probe"* likha**, jisse Faisla 3 amendment ka category error invite hua.
6. **BRIEF ke Part C ne Part B ke outcomes leak kiye:** `C1` (*"peak `≤ 2`"*, *"teesra `/slow-hold` fail karta hai"*),
   `C2` (*"elapsed `pool_timeout` ke paas"*), `C3` (*"DB na chhune wala endpoint `200`"*), `C4` (*"`1` row
   `active`"*). Paanchon jawab `idk` the to score contaminate nahi hua — **par BRIEF ne ye possible banaya.** Din 5 ka
   Part C sirf instrument check karta hai, outcome nahi.
7. **KEY `Q3(d)` ne ek hi jawab me do ulti baatein likhi:** *"`D-28` ka label survive karta hai"* aur *"wo liveness ke
   naam pe readiness naap raha hai"*. Measurement ne doosri ko sahi saabit kiya.
8. **KEY `Q5(b)` ne sink ke pool pressure ko sirf *concurrent clients* ke terms me socha.** Ye assumption Din 5 test
   karta hai, aur isliye yahan uska mechanism nahi likha.

**KEY ne jo theek kaha, aur aaj live confirm hua:** idle `0` (lazy pool) · peak `2`, teesri request Postgres tak
nahi pahunchi · `500`, `503` nahi · `sqlalchemy.exc.TimeoutError`, builtin nahi · elapsed floor ke **upar**
(`3.0055` nahi) · `/health` `200` jab `/healthz` `500` · `500` wale request ka `pg_sleep` kabhi issue nahi hua
(`Depends` me mara — `pg_sleep` count `9`) · `Q4` ko *"naapo, predict mat karo"* likha, aur jawab `20.025 s` nikla ·
`httpx` timeout default nahi, explicit hai — ab `5.0268 s` measured.

---

### 💡 What I understood — own words, 2026-09-30

1. Pool limit (`pool_size=2`, `max_overflow=0`) database server nahi balki client application ke andar SQLAlchemy engine enforce karta hai (`w5d4_step1_api.log`): teesri concurrent request ke waqt `_do_get` method me `TimeoutError` raise hua aur uska `SELECT pg_sleep` kabhi Postgres server tak pahuncha hi nahi.
2. Pool timeout ka bound isolation: `RELAY_POOL_TIMEOUT` ko 1.5 s, 3.0 s, aur 5.0 s set karke run karne par failure latency exact timeout ke mutabiq 1.588 s, 3.096 s, aur 5.076 s aayi, jisse prove hua ki starvation failure latency strictly pool timeout parameter se bound hoti hai.
3. Health check endpoints ka discrimination: Pool saturation ke dauran non-DB endpoint `/health` turant `200 OK` (0.03 s) deta hai jo process liveness prove karta hai, jabki `/healthz` aur `/db-ping` pool queue me block hokar 3.06 s baad `500` return karte hain (`w5d4_step3_discriminator.txt`).
4. Client-side HTTP disconnect hone par server-side DB work abort nahi hota: client ne 3 s pe timeout/disconnect kiya par Postgres me `SELECT pg_sleep(20)` poore 20.025 s chala aur tab tak pool connection held raha (`C4`).

Gaps vs reviewer: Reviewer ne note kiya ki `Tee-Object` khali pipeline par zero output retain nahi karta jisse absence verify karna mushkil ho jata hai, aur client disconnect ke dauran access log me request record hi nahi hoti.

### 💡 What the session established — **user ko ye apne shabdon me dobara likhna hai**

> Ye section reviewer ne likha hai. Protocol ke hisaab se isko user ke apne shabdon me replace hona hai, aur ye
> Week 2 se chal raha `💡` debt hai.

1. **"Set hua" aur "honour hua" do claims hain, aur unke teen alag instruments hain:** print config ka hai,
   `pg_stat_activity` behaviour ka, aur error message us component ka jo limit enforce karta hai. Teesra sabse strong
   hai kyunki wo khud limit hai jo bol rahi hai.
2. **Ek zero sabse mushkil number hai retain karna.** `Tee-Object` khaali input pe file nahi banata, `GROUP BY` zero
   rows pe line nahi deta. Jo instrument sirf *"kuch hua"* record kar sakta hai, wo *"kuch nahi hua"* ko *"record nahi
   hua"* se alag nahi kar sakta.
3. **Ek duration ke do endpoints hote hain, aur number ka naam uska measurement nahi hai.** `7.6771 s` ko lock duration
   kaha gaya; uska start `Popen` tha. Har duration ke saath dono endpoints naam se likhne hain.
4. **Client ka jaana server ka kaam nahi rokta.** `curl` `3 s` pe gaya, `pg_sleep` `20.025 s` chala, connection handler
   ke saath wapas aayi. Aur access log ne us request ko record hi nahi kiya.
5. **Ek run ek number deta hai; teen configs pe teen runs batate hain ki number kis cheez ka hai.** `1.588` · `3.096` ·
   `5.076` — elapsed `pool_timeout` ke peeche chalta hai.
6. **Prewritten verdict text measurement jaisa dikhta hai aur measurement ke khilaaf ja sakta hai** — usi file me
   `error=` aur *"error=The read operation timed out"*.

---

### ⚠️ Closeout corrections

| # | Jaise report hua | Jo measured hai | Provenance |
|---|---|---|---|
| 1 | *"All gates (C1–C8) are strictly PASSED"* | **Teen gate nahi chale ya fail hain:** `C2` row 2 (dono Step 2 runs ek process, `timeout 3.00`); `C3` control (API log me koi unsaturated `/healthz` nahi); `C5` row 3 (`git ls-files labs/w5d4_*` → `0`). `C7` ka Step 0 frozen hash kisi file me nahi hai. **Reviewer ne `C2` row 2 aur `C3` control chalaye, aur dono user ke nateeje ke haq me nikle** | `[MEASURED-R 2026-09-27]` |
| 2 | *"Idle count … 0 rows … (`logs/w5d4_step1_idle.txt`)"* | **Wo file exist nahi karti.** `Tee-Object` khaali input pe file nahi banata, aur `GROUP BY` zero rows pe line nahi deta. Reviewer ka re-take: `0`, file me | `[MEASURED-R]` four-arm probe |
| 3 | *"Clients: 200 (8.06s), 200 (8.04s), 500 (3.05s) (`logs/w5d4_step1_peak_clients.txt`)"* | **Us file me `500 3.116546` · `200 8.514253` · `200 8.515723` hai.** Quote kiye gaye numbers Step 2 run 1 ke hain (`w5d4_step2_20260927_073239_386109.log`). Week 4 Din 5 ka frozen-text paraphrase defect, is baar artifact ke saath | `[MEASURED]` file read |
| 4 | *"PostgreSQL strictly enforced the ceiling of 2 connections"* | **`QueuePool` ne API process ke andar enforce kiya** — paanchon `TimeoutError` `pool\impl.py:167` se, aur `500` wale requests ka koi statement Postgres tak nahi gaya. Postgres ne **observe** kiya, enforce nahi | `[MEASURED]` API log |
| 5 | *"Bound isolated: Anchored strictly on pool_timeout = 3.0s"* | **Ab sach hai, par aaj ke user runs se earned nahi tha** — ek config pe do runs *"`seconds` nahi"* prove karte hain, *"`pool_timeout` hai"* nahi. Reviewer ka teen-arm run: `1.5878` / `3.0956` / `5.0755 s` | `[MEASURED-R]` |
| 6 | *"Comparison with Week 4 Din 5 (3.0055 s): Reproduced"* | **Bound reproduce hua, overhead nahi.** `+5.5 ms` tab vs `+32.7`–`+116.5 ms` aaj, aath measurements. **Replacement, confirmation nahi** | `[MEASURED]` + `[MEASURED-R]` |
| 7 | *"Using `/healthz` as liveness under Kubernetes triggers cascading container restart loops"* | **Direction sahi.** Measured half: `/healthz` `500` jabki `/health` `200` — process zinda hai. **Restart, cascade aur "loops" `[INFERRED]`** — iss repo me koi orchestrator nahi hai | `[MEASURED]` / `[INFERRED]` |
| 8 | *"Client Disconnect Connection Leak"* | **Leak nahi hai** — connection `20.025 s` pe wapas aayi (API log `ROLLBACK`). Jo missing hai wo cancellation hai. *"Snapshot 2: `api_w5d4\|idle\|ROLLBACK;`"* — file me **do** rows hain, aur snapshot release ke `5 min 22 s` baad liya gaya | `[MEASURED]` |
| 9 | *"Dispatcher held FOR UPDATE lock … for 7.6771 s"* | **`Popen` → stdout-line clock.** Lock kabhi observe nahi hua. Release mechanism source se: `COMMIT` | `[MEASURED]` probe source + log |
| 10 | *"Uncommitted holder transaction on sink_deliveries stalled Sink's `ON CONFLICT DO NOTHING`"* | **Observe nahi hua** — snapshot dispatcher ki pehli SQL se pehle, sink ka stdout kabhi padha nahi gaya. `5.0 s` ReadTimeout ke consistent hai | `[INFERRED]` |
| 11 | *"`str(httpx.ReadTimeout)` is `""`"* | **Sahi**, aur class ab measured: `httpx.ReadTimeout`, `repr ReadTimeout('')`, `5.0268 s` | `[MEASURED-R]` |
| 12 | Probe ki line *"Relay Log Symptom: … error=The read operation timed out"* | **Prewritten, aur usi file ki measured line (`error=`) ke khilaaf.** `P-52` ki teesri recurrence | `[MEASURED]` |
| 13 | Step 6 ka faisla (Option B, `ENABLE_TEST_ROUTES=1`, owner Week 6) | **Faisla theek shape me hai — cost naam se, owner ek din. Par repo me kahin likha nahi tha.** Reviewer ne `P-44` amendment me user ke shabdon ke saath record kiya | `[MEASURED]` grep `0` |
| 14 | Faisla 3 amendment: *"re-taken and retained under `labs/w5d4_pool_probe.py`"* | **Pool probe load harness nahi hai** — wo `19.8 /s` enqueue rate dobara nahi naap sakta. Faisla 3 ka `Chosen` `[NOT RETAINED]` hi rehta hai | `[MEASURED]` source |
| 15 | *"Evidence Database (`relay`): Delta strictly `0`"* | **Sach, nau counters pe** — `P-31` ka wording sabak: *"delta `0` on the nine counters"*, *"strictly"* nahi | `[MEASURED-R]` |

---

### 🚧 Unresolved / carried

1. **Step 5 ke teen missing measurements — Din 5:** outbox lock ka hold (dono endpoints ke saath), sink ki wait
   (`pg_stat_activity` se, log se nahi), aur chain ka pool half.
2. **Discriminator ka DB-down column — Din 5.** Starvation aur DB-down ko alag karne wali ek observation abhi
   naapi nahi gayi.
3. **`P-45` ka teesra number** (`2.8133 s` vs `0.4703 s`, receiver contention) **re-take nahi hua — Din 5.** Aaj ke
   `3` me se `2` replace hue.
4. **`D-30` ke do gates** (`~30 s` DB-down run, `n = 1` / never under load) **— Din 5**, taaki Din 6 close kar sake.
5. **Din 4 commit nahi hua.** `DIN_04_PREDICTIONS_FROZEN.md`, `labs/w5d4_pool_probe.py`, `labs/w5d4_composed_failure.py`
   aur aaj ke docs — **named `git add`, `-A` nahi**, kyunki `P-54` ki bees files abhi bhi gate hain.
6. **`P-55` fix — Week 6**, `src/` edit, `P-44` aur `P-51` ke saath.
7. **`P-44` ka code (Option B) — Week 6.** Tab tak `/slow-hold?seconds=<anything>` unauthenticated aur unbounded hai.
8. **`echo=True` ek observability dependency ban gaya hai.** Orphaned request ka ek-matra nishaan wahi hai. Jo bhi
   faisla `echo` band karta hai, usko ye cost naam se likhna hai.
9. **Din 4 ke do generators aur teen artifacts me prewritten text — Din 5 Step 1**, annotate karna hai, delete nahi.
10. **`logs/` ka `147` vs `146`** — Din 6 ka reconcile.
11. **`P-51`, `P-54`, `P-36`, supervisor backoff, `D-30` `OPEN`, README rows 7/9** — Din 3 se unchanged. Aaj ka koi
    change inko **chhuta nahi**.

---

### ❓ Next thought

Din 3 ka sawaal tha: kaunsa outcome kisi ke faisle se nahi, defaults ke overlap se aata hai? **Aaj ek mila aur
measured hai:** `/slow-hold` ki connection client ke jaane ke baad `17 s` aur bandhi rahi. Ye kisi ne decide nahi
kiya — server ka default (disconnect pe handler cancel nahi hota) aur pool ka default (checkout request handler ke
saath jeeta hai) mil ke ye banate hain, aur access log dono ke beech kuch nahi dekhta.

Step 5 me dispatcher `5.0 s` pe haar maan ke chala gaya. **Sink ke nazariye se wo kaunsa event hai?** Aur jab
dispatcher chala jaata hai, us waqt sink ka `INSERT` kya kar raha hota hai — aur uske baad kya karta hai? Din 5 ka
pehla aadha isi sawaal ka hai, aur uska jawab kisi log me nahi, `pg_stat_activity` me milega.

---

*Plan:* [`../planning/WEEK_05.md`](../planning/WEEK_05.md) ·
*Din 4 BRIEF:* [`../daily/week_05/DIN_04_BRIEF.md`](../daily/week_05/DIN_04_BRIEF.md) ·
*Din 4 KEY:* [`../daily/week_05/DIN_04_KEY.md`](../daily/week_05/DIN_04_KEY.md) ·
*Seal:* [`../daily/week_05/DIN_04_PREDICTIONS_FROZEN.md`](../daily/week_05/DIN_04_PREDICTIONS_FROZEN.md)

---

## Din 5 — `P-41` ki chain end-to-end naapi gayi, `D-30` ke dono gate chale, aur outage ne ek aisi log line pakdi jo kabhi sach nahi thi (`2026-09-28`)

**Layer L2, `src/` gate held teesre din: `git diff --name-only HEAD -- src/` → `0`, chhe hashes Step 0 ke barabar.**
Aaj `labs/w5d5_chain_probe.py` naya bana aur `scripts/supervisor.py` badla — dono instrument hain, feature nahi.

**Din ka pehla half saaf compose hua, har link ek file me.** Arm C me ek hi sequential dispatcher ne receiver ka
`2+0` pool do timeouts me bhar diya: `pg_stat_activity` me do sink sessions `Lock / transactionid` pe, blocker holder
ka pid, aur teesre se paanchve attempt ne sink ke log me `QueuePool limit of size 2 overflow 0 reached … timeout
3.00` diya — jabki Relay ne sirf `status_code=500` likha. **Aur ek finding jo sawaal me nahi thi:** dono arms me
effect us request ne apply kiya jise Relay ne `[dispatch_error] … error=` likha, aur Relay ka `status=dispatched`
ek `duplicate` ko mila. `received_at` ne ye bataya, echo lines ne nahi.

**Doosra half `D-30` ke dono gate the, aur dono chale.** `35.006 s` DB-down (`stop_returned → start_begin`, file me),
teen process supervisor ke neeche, `30` jobs ka backlog: `EXITED` lines `0`, `30/30 succeeded`, `pending_or_running=0`.
**Par din ka sabse zaroori finding usi run ke in-flight job me chhupa tha aur report ne use miss kiya:** worker ne
`[mark] Marked job 8 as 'succeeded' (rowcount=1)` print kiya, **phir** uska `COMMIT` mara. Reaper ne 40 s baad job 8
ko `pre_status=running` pe paaya. Relay ki har lifecycle line `COMMIT` se pehle print hoti hai — **`P-56`**.

**Seal lagatar chauthe din held:** `DIN_05_PREDICTIONS_FROZEN.md` SHA-256
`8B38705BD0F9E21999BF5910DB0F7821B6B8D533E045AE30D1A3C00F0CDB10C2` — Step 0 ki **file**, Step 7 ki line, aur
reviewer ka independent hash, teeno barabar. File `13:39:03` pe likhi gayi, arm A `13:54:24` pe chala.

---

### 📊 Measured / Observed

User ke saare artifacts reviewer ne padhe. **Reviewer ke apne chaar measurements `[MEASURED-R 2026-09-28]` hain** —
httpx client construction, refused-connect cost, ek throwaway repo me `.gitignore` ke teen shapes, aur ek fresh local
clone me frozen files ke bytes (Din 6 ke liye; `P-57`). Temporary scripts delete hue; throwaway repo aur clone `%TEMP%`
me bane aur hataye gaye (`tmp_removed=True`, `clone_removed=True`).

#### 1. Bench, seal, aur ek timing note

| Gate | Measured | File |
|---|---|---|
| Din 4 commit | `c145a11`, exactly `8` staged files, koi KEY/`P-54` class nahi | `w5d5_step0_staged.txt`, `w5d5_step0_d4_tracked.txt` → `3` |
| `src_diff` · chhe hashes · `heads` | `0` · `a2ec8e9f…` `edcde815…` `dcdb6343…` `d55e3b8a…` `fc5bde22…` `fcfc9059…` · `w4d4_sink_unique (head)` — Step 0 aur Step 7 identical ✅ | `w5d5_step0_bench.txt`, `w5d5_step7_bench.txt` |
| Din 2 supervisor log SHA-256 | `9ABF8EA2…5A6F` — Step 0, Step 5 check, aur reviewer ka close re-read ✅ | `w5d5_step5_check.txt` |
| evidence DB, nau counters | `133\|145\|19\|4\|7\|39\|5\|0\|1` — Step 0, Step 7, aur reviewer ka close re-read; **delta `0` on the nine counters** ✅ | `w5d5_step0_counters.txt`, `w5d5_step7_bench.txt` |
| `relay_underscore_dbs` · `relay_python` · `key_index`/`key_tree`/`pyc_control` · `p54` · `labs_w5d5_ignored` | `0` · `0` · `0`/`0`/`1` · `20` · khaali ✅ | `w5d5_step7_bench.txt` |

**Timing note:** Step 0 ka bench aur counters `2026-09-27 18:37` pe bane — Din 4 ke commit ke turant baad, seal se
`19 h` pehle. `src/` ke liye Step 7 ki equality us gap ko cover karti hai; bench ka *"Step 0"* label kal raat ka hai.

#### 2. Step 1 — `P-52` ki cleanup

`9` annotations teen Din 4 artifacts me (`w5d4_step2_…073239` lines `7`/`26`/`28`, `…073712` `7`/`26`/`28`,
`w5d4_step5_…` `55`/`58`/`61`) ✅. Generators se chhe prose lines hati, `py_compile` clean ✅. **Ek residue:**
`w5d4_composed_failure.py` ab `Dispatcher elapsed : {disp_elapsed}` print karta hai — neutral label, par
`disp_elapsed` abhi bhi `Popen` se shuru hota hai. Label value ka start nahi batata.

#### 3. Arm A — `P-45` ka teesra number (`logs/w5d5_A_20260928_082424_934619_*`)

| Observation | Value | File |
|---|---|---|
| sink premise | `resolved_db=relay_w5d5 app_name=sink_w5d5 pool=2+0`, probe log me copy | probe + sink log |
| uncontended (`n = 10`) | first **`0.0305 s`** · median of nine **`0.0185 s`** · max `0.0305 s` | probe log |
| sink-side first request | `BEGIN 29.668 → COMMIT 29.680` (`12 ms`, `generated in 0.00022s`) vs `~4 ms` baad me (`cached since …`) | sink log |
| contended `POST job:42` | **`200`, `3.0565 s`**, `result=applied` | probe + sink log |
| sink ka lock wait, server side | `BEGIN 13:54:30.524 → COMMIT 13:54:32.986` = **`2.461 s`** | sink log (echo) |
| poll, holder ke dauran | `8` samples `sink_w5d5 active / Lock / transactionid`, `blockers=[62]` = holder ka pid; holder khud `idle in transaction / Client / ClientRead` (`8`) | poll log |
| sink log, wait ke dauran | **kuch nahi** — `INSERT` echo, phir `2.46 s` baad `COMMIT` aur `result=applied` | sink log |
| `received_at` | `08:24:30.527438+00` = `13:54:30.527` — `INSERT` ke transaction ka start, `COMMIT` (`32.986`) nahi | probe log |
| row id | `12` — `11` holder ke rolled-back `INSERT` ne khaya (sequence non-transactional) | probe log |

**Do contended numbers, `0.54 s` ka farak, aur wo lock se pehle hai.** `holder_start 29.982` → sink `BEGIN 30.524`.
Probe `httpx.AsyncClient()` timed task ke **andar** banata hai, aur reviewer ne naapa: construction **`0.366`–`0.700 s`**
(`n = 4`), synchronous, event loop pe `[MEASURED-R]`. Gap ko usi ko attribute karna `[INFERRED]` hai. Pehla poll bhi
`30.612` pe aaya (`+0.63 s`) — usi blocked loop ke consistent. **Replacement:** `0.4703 s` → `0.0305` / `0.0185 s`;
`2.8133 s` → client `3.0565 s`, server `2.461 s`. **Retired, reconcile nahi** (`P-45` amendment).

#### 4. Arm B — `--hold 6` (`logs/w5d5_B_20260928_082503_817815_*`)

| Observation | Value | Source |
|---|---|---|
| anchor | probe `13:55:09.852`; dispatcher ka `SELECT … FOR UPDATE` echo `09.791` — anchor **reader-side, `61 ms` late** | probe + dispatcher log |
| `holder_end − anchor` | `6.136 s` — `holder_end` line `conn.close()` ke **baad** likhi gayi; rollback `≤ 15.878` (sink ka applied `COMMIT`), anchor + 6 = `15.852` | probe + sink log |
| attempts before holder_end | **2** — `+0` aur `+5.055 s` (`cached since 5.055s ago`) | dispatcher log |
| attempt 1 lock hold | `SELECT 09.791 → COMMIT 14.839` = **`5.048 s`**; end = `UPDATE outbox SET attempts` + **`COMMIT`** | dispatcher log |
| attempt 2 lock hold | `SELECT 14.846 → COMMIT 16.089` = `1.243 s` | dispatcher log |
| result lines | `[dispatch_error] … error= attempts=1` · `[dispatch] … status=dispatched attempts=2` · row 2 `status=dispatched attempts=1` | dispatcher log |
| sink | H1 `BEGIN 09.830`, H2 `BEGIN 14.928`; `COMMIT 15.878 result=applied`, `COMMIT 15.920 result=duplicate` | sink log |
| wake-up, seen by Postgres | `15.868`: H2 (pid `71`) `blockers=[67]` — H1, holder nahi | poll log |
| final | row 1 `attempts=2`, `dispatched_at 13:55:14.847`; row 2 `attempts=1`; `sink_deliveries` **1** row, `received_at 13:55:09.831029` | probe log |
| census | `access_lines=3` · `applied 1, duplicate 2` | probe log |

**`received_at` = H1 ka `BEGIN`** → effect attempt 1 ki request ne apply kiya, jiska client `14.83` pe ja chuka tha.
H1 client ke jaane ke `1.04 s` baad bhi lock pe wait karta raha — **sink pe bhi cancellation nahi** (Din 4 ne API pe
naapa tha). Relay ka success attempt 2 ko mila, jise sink ne `duplicate` diya. Aur `dispatched_at` (`14.847`) effect ke
`COMMIT` (`15.878`) se **`1.03 s` pehle** hai — wo attempt 2 ke transaction ka start hai.

#### 5. Arm C — `--hold 20` (`logs/w5d5_C_20260928_082544_746686_*`)

Anchor probe `13:55:53.019`; offsets dispatcher echo `BEGIN 52.936` se, jahan diya hai.

| `t − anchor` | sink sessions `Lock` (poll) | dispatcher ki last result line | sink log ki nayi lines |
|---|---|---|---|
| `+2` (`55.127`) | `1` | — | H1 ka `INSERT` echo |
| `+7` (`59.969`) | `2` | `[dispatch_error] … attempts=1` | H2 ka `INSERT` echo |
| `+12` (`04.984`) | `2` | `[dispatch_error] … attempts=2` — attempt 3 `QueuePool` ki queue me, Postgres ko invisible | — |
| `+17` (`10.027`) | `2` | `[dispatch_failed] … status_code=500 attempts=4` | do `500` access lines + do `TimeoutError` tracebacks |
| `+22` (`15.072`) | `0` | `[dispatch] outbox_id=2 status=dispatched attempts=1` | `applied`, `duplicate` ×3, do `200` |

- **Max sink sessions in any poll: `2`**, `111` polls me. Pehla 2-lock poll `13:55:58.121`, aakhri lock poll `13:56:12.958`.
- Attempts `+0`, `+5.06`, `+10.10`, `+13.15`, `+16.18`, `+19.21 s`; shapes `error=`, `error=`, `500`, `500`, `500`,
  `dispatched`. Row 1 final **`attempts=6`**, ek effect ke liye.
- **`QueuePool limit … timeout 3.00`: sink ke log me, `3` baar; Relay ke log me kabhi nahi.** Pehli baar `+13.15 s` —
  dispatcher echo se, kyunki sink ki uvicorn error lines pe timestamp nahi hota.
- `received_at 13:55:52.973202` = H1 `BEGIN 52.971` — **phir attempt 1 ki orphan jeeti**, `n = 2`. Attempt 6 ko
  `13:56:13.031` pe connection mila (H1 ke `COMMIT 13.027` ke `4 ms` baad) aur `duplicate` aaya; Relay ne
  `status=dispatched attempts=6` likha. `dispatched_at 13:56:12.144` = attempt 6 ka start.
- Access lines `6` = `8` requests − `2` orphans. Census ka `exceptions={"exc.TimeoutError": 3, "sqlalchemy.exc.TimeoutError": 3}`
  **lines ginta hai, events nahi** — ek traceback do regex matches deta hai.

**`P-41` dobara likha, sirf aaj ki files se** (`P-41` amendment): har timed-out attempt receiver me ek handler chhodta
hai jo ek pooled connection pakde conflicting writer pe baitha rehta hai; **ek** sequential dispatcher do timeouts me
receiver ka `2+0` pool bhar deta hai; symptom receiver ke log me `pool_timeout`, Relay me `500`.

#### 6. Step 5 — supervisor

`RELAY_SUPERVISOR_PREFIX` na ho to `RuntimeError` — **fail-closed** ✅. Dispatcher teesra process ✅. Dry run: `3`
`Started` lines, Din 2 log SHA intact, `0` Relay python ✅. **BRIEF ne prefix-missing ke faisle ka cost ek line me
maanga tha — wo kisi file me nahi hai.** Supervisor log UTC likhta hai (`+00:00`), baaki sab local — join karte waqt
`+5:30`.

#### 7. Step 6 — `35 s` outage, fleet, backlog

**Timeline, sab files se:**

| Moment | Value | File |
|---|---|---|
| supervisor start | `16:03:02.022` (log me `10:33:02 UTC`) | `w5d5_step6_supervisor.log` |
| premise | chaar lines, chaaron `resolved_db=relay_w5d5` (API `api_w5d5 2+0`; baaki `5+10`, distinct names) ✅ | `w5d5_step6_premise.txt` |
| backlog | `30` ids | `w5d5_step6_jobs.txt` |
| job 8 claim / execution row | `UPDATE 16:03:55.643`, `COMMIT 55.660` / `COMMIT 55.717` | worker log |
| `stop_begin` · `stop_returned` | `16:03:55.974` · `16:03:57.355` | `w5d5_step6_fault.txt` |
| job 8 mark | `UPDATE 56.746` → print `Marked … 'succeeded' rowcount=1` → `COMMIT 56.751` **mara** | worker log |
| `start_begin` · `start_returned` | `16:04:32.361` · `16:04:33.387` → **outage `35.006 s`** ✅ | `w5d5_step6_fault.txt` |
| pehli successful DB activity | worker `16:04:35.001` (`+1.61 s`) · dispatcher `35.780` (`+2.39 s`) · reaper `35.902` (`+2.52 s`) | stdout logs |
| reclaim | `[reclaim] job_id=8 pre_status=running matched=1`, DB time `16:04:35.924` | reaper log |
| job 8 dobara | job **9** pehle claim hua (`35.066`); job 8 gen `2` attempt `2` `36.119`; mark `COMMIT 37.146` | worker log |
| final | `succeeded\|1\|29` · `succeeded\|2\|1` · `pending_or_running=0` | `w5d5_step6_final_jobs.txt` |

**Lease:** `claimed_at` ≈ `16:03:55.64` → lease `16:04:25.6` pe expire hua, **DB down ke dauran**. Reclaim reaper ke
pehle successful pass pe, expiry ke `10.3 s` baad. **Is run me recovery outage-bounded thi, lease-bounded nahi.**

**Tag census** (`w5d5_step6_summary.txt`): worker `claim 31 · execute 31 · mark 31 · mark_error 4 · mark_abandoned 1 ·
poll_error 5`; reaper `poll_error 7 · reclaim 1`; dispatcher `poll_error 7`. **`mark=31` prints hain, commits nahi** —
`30` jobs, ek print jhootha (`P-56`). `execute=31` = job 8 ka handler do baar chala (`sleep`, koi effect nahi).

**Failure classes per process** — teeno me same shape: pehli failure `InterfaceError` (stale pooled connection), phir
`5` × `ConnectionRefusedError`, aakhri `ConnectionError: unexpected connection_lost()` (Postgres start ho raha tha). Worker
ke mark path pe pehli failure `ConnectionDoesNotExistError: connection was closed in the middle of operation` — **`COMMIT`
ke beech**. `CannotConnectNowError` aaj kahin nahi aaya.

**Sampler — outage ke andar** (`w5d5_step6_sampler.txt` + API log):

| Endpoint | Samples | Exception (API log) |
|---|---|---|
| `/health` | `200` ×4, `0.0027`–`0.0487 s` | — |
| `/healthz` | pehla **`500 0.042 s`**, phir `500` `4.077` / `4.080` / `4.089 s` | pehla: `InterfaceError: connection is closed` (stale pooled, `pool_pre_ping=False`); baaki `ConnectionRefusedError` |
| `/db-ping` | `500` `4.186` / `4.101` / `4.091 s`, aakhri `500 1.551 s` (`16:04:33.675`) | `ConnectionRefusedError` ×3; aakhri `ConnectionError: unexpected connection_lost()` |
| recovery ke baad pehla `/healthz` | `16:04:36.800` **`200 0.060 s`**; phir sab `200` | — |

API log ki `api_exc` counts traceback lines hain: `8` failing requests = `1` stale (tin chained lines) + `6` refused +
`1` connection_lost.

**`4.08 s` kahan se aata hai — reviewer ne naapa** `[MEASURED-R]`: `DATABASE_URL` ka host `localhost` hai;
`getaddrinfo('localhost')` → `['::1', '127.0.0.1']`; closed port pe refused connect `127.0.0.1` `2.016`/`2.032 s`,
`::1` `2.017`/`2.032 s`, `localhost` **`4.046`/`4.062 s`**. Windows ek refused connect pe `~2 s` leta hai, aur asyncpg dono
addresses try karta hai. **DB-down `/healthz` = do refused connects + `~30 ms`.** Din 4 ka saturated `/healthz` `3.067 s` =
`pool_timeout`. Aaj latency `~1 s` se alag hui — **par do asambandhit configs ke sanyog se:** host `127.0.0.1` pe DB-down
`~2.03 s` hota, aur `pool_timeout = 4.0` pe starvation `~4.06 s` `[INFERRED from the measured parts, not run]`.

**`D-30` ke liye do lines:**
- **Gate 1 — restarts bounded over a `~30 s` DB-down: satisfied as written.** `35.006 s` outage, `EXITED` lines `0`
  (grep ka positive control: Din 2 log me `4`), teeno children zinda. **Bound boundaries se aaya, supervisor se nahi:**
  `0` exits ka matlab supervisor ka backoff code ek baar bhi nahi chala, to `P-53(d)` us exit class ke liye unpriced hai
  jo asal me matter karti hai (`os._exit`, `P-36`).
- **Gate 2 — teeno ek saath, backlog ke neeche: worker aur reaper ke liye satisfied, dispatcher ke liye aadha.** Worker ne
  `30` drain kiye, ek in-flight reclaim hua, `0` lost. **Dispatcher ke paas `0` outbox rows thi** (`sleep` jobs outbox nahi
  likhte) — wo outage survive kiya, load ke neeche nahi tha. `n = 2` total (Din 2 + Din 5).

#### 8. Part C — jo chala, jo nahi chala

| Check | Status |
|---|---|
| `C1`, `C2`, `C5`, `C6`, `C7` | chale, pass ✅ |
| `C3` prose check (`logs\w5d5_c3_prose.txt`) | **file exist nahi karti — chala hi nahi.** Reviewer ne chalaya: `0` Din 5 probe logs pe, positive control `2` Din 4 ke `w5d4_step5_…` pe `[MEASURED-R]` |
| `C3` poll coverage `≥ 80%` | A `39/44` (`89%`), B `62/66` (`94%`), C `111/124` (`90%`) ✅ — par pehla poll holder_start ke `0.21`–`1.11 s` baad; arm A me contended request **pehle poll se pehle** pahunchi |
| `C3` anchor `± 0.3 s` | A `3.011`, B `6.136`, C `20.013 s` ✅ |
| `C4` generator SHA-256 in headers | **probe ise log nahi karta** — BRIEF ki Step 2 requirement table me ye row thi hi nahi (reviewer ka defect). Reviewer ne mtime se answer kiya: probe `13:53:29`, arm A `13:54:24` — teeno arms same file |
| probe ki `cleanup: remaining_relay_python=1` | leak jaisa padhta hai; count apna PID exclude karta hai, venv launcher parent nahi. Reviewer ke apne probe ne same `2`-process shape dikhaya. Step 7 `relay_python=0` ✅ |

---

### 🧠 Prediction review — `0.00 / 5.0`, calibration `5/5`, aur aath derivable sub-parts `idk`

Frozen text `docs/daily/week_05/DIN_05_PREDICTIONS_FROZEN.md` se **quote**, hash verify hua.

| Q | Frozen text (verbatim) | Measured | Score |
|---|---|---|---|
| **Q1** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q2** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q3** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q4** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |
| **Q5** | *"idk"* | **NOT ANSWERED** | **`0.00 / 1.0`** |

**Total `0.00 / 5.0`. Week 5 frozen total: `1.45 / 25.0`.** Inflation zero, lagatar chautha din — ye record saaf hai.

**Par ye zero Din 4 wala zero nahi hai.** KEY ke scoring note ne aath sub-parts ko naam se *"run se pehle derivable"*
likha tha: `Q1(a)` (`src/sink.py` ka `lifespan`) · `Q2(a)`, `Q2(b)` (`src/dispatcher.py` + `P-35`) · `Q3(d)` · `Q4(a)`,
`Q4(c)`, `Q4(d)` (Din 1–2 ka record + `scripts/supervisor.py`) · `Q5(a)` (`src/main.py`). **`2.0` points padhne se mil
sakte the.** Aur is baar BRIEF ne Part B ke upar hi likha tha: *"Jis sawaal me ek file ya line ka naam hai, `idk` likhne
se pehle wo file kholo."* `Q1(a)` aur `Q2(b)` dono me file ka naam hai. **Do din se reading gap wahi hai, aur ek explicit
instruction ne use nahi hilaya.**

**Aur ek format note:** frozen file me har sawaal ka ek `idk` hai, sub-part ka nahi. `Q2(b)` source se padha ja sakta
tha aur `Q2(c)` genuinely naapna tha — ek hi `idk` dono ko barabar kar deta hai. **Din 6 se `idk` per sub-part.**

**Beat 4 ka record nahi hai.** Report ke mechanisms (*"Request that applied side effect was logged as error"*) sahi hain,
par Din 5 ke liye koi file nahi jisme run ke baad aur KEY se pehle apni explanation likhi ho. **Wo derived tha ya padha
gaya — ye `not recorded` hai**, aur protocol ki value isi beat me hai.

---

### 🤖 Reviewer ki apni galat predictions — record ke liye

1. **KEY `Q5(b)`: DB-down `/healthz` ko `~2.7`–`3.3 s` likha, *"saturated `3.03 s` se `~0.4 s` ke andar"*.** Measured
   `4.077`–`4.089 s`. Mechanism reviewer ne aaj naapa — `localhost` dual-stack × `~2.02 s` Windows refused connect. Din 1
   ka `failure_cost ≈ 3.3 s` ek derived mean tha, direct measurement nahi, aur KEY ne use constant ki tarah use kiya.
2. **KEY `Q4(b)` ne in-flight path *"mark `UPDATE` → DB down → `[mark_error]`"* likha.** `UPDATE` safal hua, success line
   print hui, `COMMIT` mara. **Print ki position Din 2 ke review me bhi nahi pakdi gayi** — `P-56`. Aur *"`~3` lines"* →
   `4` (`1` mark + `3` retries).
3. **KEY `Q1(b)` aur BRIEF requirement 8 ne ye nahi socha ki client ka `t0` kahan hai.** `httpx.AsyncClient()` banana
   `0.37`–`0.70 s` leta hai, aur probe use timed task ke andar banata hai. Client number `3.0565 s`, lock wait `2.461 s`.
4. **BRIEF `C4` ne generator ka SHA-256 header me maanga, par Step 2 ki requirements table me wo row thi hi nahi.** Probe
   ne use nahi likha; `C4` mtime se answer hua.
5. **BRIEF Step 6 ka tag census prints ginta hai** — `mark=31` ko marks padhna `P-56` ki galti dohrata hai. Census ko
   *"prints"* label chahiye tha.
6. **KEY trap `14` ne startup pe `CannotConnectNowError` expect kiya;** aaj teeno process me `ConnectionError:
   unexpected connection_lost()` aaya, `CannotConnectNowError` kahin nahi.

**KEY ne jo theek kaha, aur aaj live confirm hua:** `Q1(a)` ms ka farak (`30.5` vs `18.5 ms`) · `Q1(c)` `active / Lock /
transactionid`, blocker holder, holder `idle in transaction / ClientRead` · `Q1(d)` wait ke dauran sink silent, phir
`applied` · `Q2(a)` do attempts, `+5.055 s` · `Q2(b)` `COMMIT`, `~5.05 s` · `Q2(c)` race + `received_at` · `Q2(d)`
`attempts=2` aur asymmetry · `Q3(a)` `2` · `Q3(b)` poora order · `Q3(c)` sink ke log me, `+13 s`, access lines `= requests −
orphans` · `Q4(a)` `0` · `Q4(c)` nahi · `Q4(d)` exercise nahi hua · `Q5(a)` · `Q5(c)` class, HTTP nahi · `Q5(d)` `200` ·
pehla `/healthz` sabse tez failure. **Composition ka har link hold hua — teen measured facts ka jod hi prediction tha.**

---

### 💡 What I understood — own words, 2026-09-30

1. Client timeout hone par server-side request abort nahi hoti (`logs/w5d5_B_*`, `logs/w5d5_C_*`): dispatcher ne 5 s par HTTP timeout maan kar request drop kar di par sink server par orphaned handler lock release hone tak DB connection hold karke baitha raha. Is cascading effect se sequential dispatcher ne bhi sink ka 2+0 QueuePool saturate kar diya (`P-41`).
2. Request attribution aur actual effect me mismatch hota hai: Arm B me effect attempt 1 ki timed-out request ne apply kiya (`received_at 13:55:09.831`), jabki Relay ko `status=dispatched` attempt 2 par mila jise sink ne `duplicate` diya. 200 response milna is baat ka proof nahi hai ki usi request ne side-effect apply kiya.
3. Postgres ka `now()` function statement execution time ya commit time nahi balki transaction start time capture karta hai; isliye `received_at` aur `dispatched_at` transaction ke begin hone ka waqt darshate hain na ki actual effect ya commit ka.
4. Transaction ke andar print hui outcome line DB commit ki guarantee nahi hoti (`P-56`): Din 5 fleet outage me worker ne job 8 ke liye `Marked job 8 as 'succeeded'` print kiya par transaction rollback ho gayi, aur baad me reaper ne job 8 reclaim karke dobara run karwaya.

Gaps vs reviewer: Reviewer ne note kiya ki HTTP client starvation aur DB-down ko endpoint latency se alag nahi kiya ja sakta balki process log ke exception class se kiya jata hai, aur `restarts = 0` boundaries ke kaam karne ka proof hai par supervisor backoff limits ka test nahi.

### 💡 What the session established — **user ko ye apne shabdon me dobara likhna hai**

> Ye section reviewer ne likha hai. Protocol ke hisaab se isko user ke apne shabdon me replace hona hai.

1. **Client ka timeout server ke liye ek disconnect hai, aur server kaam karta rehta hai.** Isliye ek sequential client
   bhi server ka pool bhar sakta hai — server un clients ka kaam kar raha hai jo ja chuke hain.
2. **Jis request ne kaam kiya aur jis request ko credit mila, wo alag ho sakti hain.** `200` kehta hai *"ek `200` aaya"*,
   *"isne kiya"* nahi. Attribution us data se karo jo kaam **shuru** hote waqt likha gaya (`received_at`), response se nahi.
3. **Postgres ka `now()` transaction ka start hai.** `received_at`, `dispatched_at`, `claimed_at` teeno apne naam wale
   event ka nahi, us transaction ke shuru hone ka waqt hain.
4. **Transaction ke andar print hui line ek irada hai, tab tak jab tak `COMMIT` wapas na aaye.**
5. **`restarts = 0` ka matlab boundaries ne kaam kiya.** Supervisor ka apna bound us run me test hi nahi hua.
6. **Ek latency jo ek machine pe do causes alag karti hai, wo tab tak sanyog hai jab tak mechanism usko explain na kare.**
   `4.08 s` = do refused connects; `3.07 s` = `pool_timeout`. Ek config badlo aur dono mil jaate hain.
7. **HTTP starvation ko DB-down se alag nahi kar sakta; process ke log ki exception class kar sakti hai.**

---

### ⚠️ Closeout corrections

| # | Jaise report hua | Jo measured hai | Provenance |
|---|---|---|---|
| 1 | *"Saare gates strictly PASS"* | `C3` ka prose check chala hi nahi (file nahi hai; reviewer: `0`, control `2`) · `C4` ka generator hash log nahi hua (mtime se answer) · Step 5 ka cost line kisi file me nahi · Step 0 bench `19 h` pehle ka | `[MEASURED-R]` |
| 2 | *"Contended POST job:42 … 3.0565 s (replaces 2.8133 s)"* | Client number sahi, par usme `httpx.AsyncClient()` construction shamil hai (`0.37`–`0.70 s`, reviewer). Server-side lock wait **`2.461 s`**. Dono replacements hain | `[MEASURED]` sink echo + `[MEASURED-R]` |
| 3 | *"Holder rollback 13:55:15.988"* | Wo `holder_end` line `conn.close()` ke baad ki hai. Rollback `≤ 15.878` (sink ka applied `COMMIT`) | `[MEASURED]` probe + sink log |
| 4 | *"/healthz first 500 in 0.042 s fast connection refused"* | **`InterfaceError: connection is closed`** — stale pooled connection (`pool_pre_ping=False`). Refused uske baad aaye | `[MEASURED]` API log |
| 5 | *"/db-ping (500 in ~4.1 s)"* | teen `4.09`–`4.19 s`, aur aakhri **`1.551 s`** `ConnectionError: unexpected connection_lost()` ke saath, Postgres start ke dauran | `[MEASURED]` sampler + API log |
| 6 | *"sleep finished, 4 mark retries failed"* | `1` mark + `3` retries = `4` `mark_error`. **Aur mark ne `Marked job 8 as 'succeeded' (rowcount=1)` apne `COMMIT` se pehle print kiya, jo mara** — `P-56` | `[MEASURED]` worker + reaper log |
| 7 | *"At 16:04:35.924 (lease > 30s expired), Reaper reclaimed Job 8"* | Sahi. Lease `16:04:25.6` pe DB down ke dauran expire hua; reclaim `10.3 s` baad, reaper ke pehle successful pass pe — **outage-bounded**. Job 9 job 8 se pehle claim hua | `[MEASURED]` |
| 8 | *"Zero lost, zero corrupted"* | **Zero lost, `n = 1`** ✅. *"Corrupted"* naapa nahi gaya. Job 8 ka handler do baar chala (`execute=31`) — `sleep` me koi effect nahi, isliye yahan harmless | `[MEASURED]` / not measured |
| 9 | *"D-30 Gate 1 and Gate 2 strictly SATISFIED"* | Gate 1 as written satisfied — bound boundaries se, backoff kabhi nahi chala. Gate 2: dispatcher ke paas `0` outbox kaam tha. **"Satisfied", "strictly" nahi** | `[MEASURED]` |
| 10 | *"Attempt 6 succeeded at 20s on rollback"* | Relay ne `dispatched` likha; sink ne us request ko **`duplicate`** diya. Effect attempt 1 ki orphan ne apply kiya (`received_at 13:55:52.973`) | `[MEASURED]` |
| 11 | *"P-41 composed chain verified live"* | ✅ `n = 1` per arm, aur winner `n = 2` | `[MEASURED]` |
| 12 | *"Evidence DB relay delta = 0"* | ✅ reviewer ka close re-read identical — *"delta `0` on the nine counters"* | `[MEASURED-R]` |

---

### 🚧 Unresolved / carried

1. **`P-56`** — lifecycle prints `COMMIT` se pehle. Census aur fix dono Week 6 (`P-55` ke saath).
2. **`D-30` close — Din 6**, upar ki do lines ke saath. `os._exit` crash-loop pe backoff ka pricing **Week 6**.
3. **`D-28` amendment — Din 6:** discriminator ka teesra column logs me hai, HTTP me nahi; aur latency ka farak config ka
   sanyog hai.
4. **`P-41` fixes** (`lock_timeout`, cancellation, `P-35` backoff) — Week 6, sab `narrow`.
5. **Din 5 commit nahi hua:** frozen file, `labs/w5d5_chain_probe.py`, dono `labs/w5d4_*.py` edits, `scripts/supervisor.py`,
   aur aaj ke docs. Named `git add`, Din 6 Step 0.
6. **Din 5 ka saara evidence (`logs/w5d5_*`, `47` files) sirf is disk pe hai** — `/logs/` ignored hai. `D-32` ka retention
   half abhi bhi likha nahi gaya.
7. **`P-54` ke teen faisle, `.pyc`, `logs/` count** — Din 6.
7a. **`P-57`, review me mila:** seal ka SHA-256 working-copy bytes pe hai. `core.autocrlf = true`, koi `.gitattributes`
    nahi, aur is machine pe fresh clone LF-only frozen files ko CRLF me checkout karta hai — `DIN_03` `B2A10C31…` →
    `3B894833…`, `DIN_04` `62196E9A…` → `42D0F894…` `[MEASURED-R]`. Committed blob invariant hai. Faisla Din 6, `D-32` ke andar.
8. **Probe ke reuse ke liye chaar instrument notes:** client construction timed region ke andar · pehla poll `0.2`–`1.1 s`
   late · census regex lines ginta hai, events nahi · generator hash log nahi hota.
9. **Beat 4 ki file** — Din 5 ke liye koi nahi.

---

### ❓ Next thought

Din 3 ne poocha tha kaunsa outcome defaults ke overlap se aata hai. Aaj teen mile, aur teeno ek hi shape ke hain:
**record kisi aur moment ka hai jiska naam wo leta hai.** `received_at` transaction ka start hai, delivery nahi.
`dispatched_at` attempt ka start hai, confirmation nahi. `Marked … 'succeeded'` ek `UPDATE` ka rowcount hai, commit nahi.

Din 6 verdicts likhne ka din hai — `D-30`, `D-32`, README ka promise #4. **Har verdict ek record pe khada hoga. Kaunsa
record us cheez ka hai jiska wo naam leta hai, aur kaunsa kisi pichhle moment ka?**

---

*Din 5 BRIEF:* [`../daily/week_05/DIN_05_BRIEF.md`](../daily/week_05/DIN_05_BRIEF.md) ·
*Din 5 KEY:* [`../daily/week_05/DIN_05_KEY.md`](../daily/week_05/DIN_05_KEY.md) ·
*Seal:* [`../daily/week_05/DIN_05_PREDICTIONS_FROZEN.md`](../daily/week_05/DIN_05_PREDICTIONS_FROZEN.md) ·
*Din 6 BRIEF:* [`../daily/week_05/DIN_06_BRIEF.md`](../daily/week_05/DIN_06_BRIEF.md)

---

## Din 6 — Week close: faisle likhe gaye aur flip rule do positive controls ke saath chala, par din ki apni clone file me ek seal mismatch tha jo kisi ne nahi padha (`2026-09-29`)

**Layer L2 · `src/` gate held chauthe din: `git diff --name-only HEAD -- src/` → `0`, chhe hashes Step 0 = Step 10.**
Do commits: `88f2308` (`.pyc` untrack) aur `27d5f91` (week close, exactly `8` named files, koi KEY nahi). Evidence DB
delta `0`.

**Jo bana, har ek apni file ke saath:** `D-32` final (paanch picks, har ek ka `Rejected`), flip rule jo do positive
controls ke saath differential me pass hua, `.pyc` untrack aur uski jagah naya control, `D-30` ka decided section,
`D-28` ka discriminator block, README rows 4/7/8/9, Week 4 ke chaar `💡` apne shabdon me `Gaps vs reviewer` lines ke
saath, handoff, DoD audit, Incident 04, fresh clone.

**Review me chhe cheezein mili, aur sabse badi din ki apni file me thi:** `w5d6_step10_clone.txt` ki pehli line
`DIN_04 here=42D0F894 clone=62196E9A`. Clone ne original seal reproduce kiya; **author ki apni working copy ne nahi** —
`42D0F894` `P-57` table ka CRLF hash hai. Chaudah seals `2026-09-28 17:28:51` ke `git pull --rebase` se CRLF hain, aur
jo attribute likha gaya (`-text`) wo nahi hai jo `D-32` kehta hai (`eol=lf`). Baaki paanch: Incident 04 ka root cause
source me nahi hai · `D-30` ki status line abhi bhi `OPEN` thi · handoff `P-51` ko galat naam deta hai · README row 9
*"proving"* kehta hai · ek probe database (`blogprobe`) jo bench ko dikh hi nahi sakta.

**Seal held:** `DIN_06_PREDICTIONS_FROZEN.md` SHA-256 `C7F08739…4766`, blob `73b95b49…` — Step 0 file (`19:16:10`),
Step 10 bench, aur reviewer ka re-read, teeno barabar. File `19:15:53` pe likhi gayi; pehla measurement (Step 2) `19:24:36`.

---

### 📊 Measured / Observed

User ke saare `logs/w5d6_*` artifacts reviewer ne padhe. **Reviewer ke apne reads `[MEASURED-R 2026-09-29]`:** user ke
repo pe sirf read-only commands (`git ls-files --eol`, `Get-FileHash`, `git hash-object`, `git cat-file`, reflog), aur
har write do throwaway clones me (`%TEMP%`, dono hataye). Week 6 Din 1 ki KEY ke probes ek disposable `relay_w6d1r` pe
chale (dropped); unke logs `logs/w6d1r_*` sealed material hain aur yahan cite nahi hote.

#### 1. Bench, seal, commit

| Gate | Step 0 | Step 10 | File |
|---|---|---|---|
| `src_diff` · chhe hashes · `heads` | `0` · `a2ec8e9f…` `edcde815…` `dcdb6343…` `d55e3b8a…` `fc5bde22…` `fcfc9059…` · `w4d4_sink_unique (head)` | identical ✅ | `w5d6_step0_bench.txt`, `w5d6_step10_bench.txt` |
| nau counters | `133\|145\|19\|4\|7\|39\|5\|0\|1` | same ✅, aur reviewer ka close re-read bhi | `w5d6_step0_counters.txt` |
| `p54` | `20` | **`0`** — ignored, deleted nahi | |
| `tracked_ignored` | `1` (`.pyc`) | `1` (`GEMINI_RULES.md`) | |
| `frozen_tracked` · `logs_in_head` | `15` · `0` | — | KEY `Q1(a)`, `Q1(b)` ✅ |
| `key_index` · `key_tree` · `brief_control` | — | `0` · `0` · `29` | |
| `relay_python` · `relay_underscore_dbs` | `0` | `0` · `0` | — par §9 dekho |
| staged at close | — | `8` files, `0` KEY / `P-54` class | `w5d6_step10_staged.txt` |

#### 2. Flip rule — differential, dono positive controls ke saath (Step 2)

`w5d6_step2_rule.txt`: `DIN_99_BRIEF.md` **PUBLISH** · `DIN_99_KEY.txt`, `DIN_99_SEALED.md`, `DIN_99_NEWCLASS.md`
ignored · `frozen_05_publishable=True` · `dryrun_key_md=0` · `probes_left=0` · `tracked_ignored=2` = `GEMINI_RULES.md` +
`.pyc` — **exactly wo do jo KEY ne naam se likhe the.** Ye check galat rule pe fail ho sakta tha, aur sahi rule pe pass
hua. **Jo nahi chala:** purane rule ka arm aur *bina `!**/daily/**/` wala* flip (KEY `Q2(a)`, `Q2(b)`) asli repo pe
nahi naape gaye — sirf chuna hua rule. Wo do rows reviewer ke throwaway-repo measurements hi rehti hain.

#### 3. `.pyc` (Step 3) — `88f2308`

`pyc_tracked=0` · `pyc_in_01f42c6_bytes=868` · `pyc_on_disk=True` · `new_control_brief=29`. History untouched, control
usi din replace hua — `P-40` ka habit follow hua.

#### 4. Decisions (Steps 1, 4, 5)

`d32`: `0 · 0 · 1 · 5` · `d30`: `0 · 1 · 6 · 3 · 1` · `d28`: `1 · 3 · 3 · 6`. `w5d6_c3_removed_lines.txt` me teen `-`
lines — `D-32` ki heading aur uski do `— undecided` rows, jo bharni hi thi. Koi aur purani line nahi hati ✅.

**Par `d30_header_open=0` hamesha `0` tha.** `## D-30` heading me `OPEN` kabhi tha hi nahi; do line neeche status line
`> **Status: OPEN, and deliberately half-written.**` Din 6 ke baad bhi wahi thi. Check galat field padh raha tha — aur
wo check reviewer ka likha tha. Review pe status line ke upar ek amendment line judi (purana text chhoda).

#### 5. README (Step 6)

`w5d6_step6_readme.txt`: row 4 `week5=2` · row 7 `week5=1` · row 8 `week5=1`, `no_evidence=1` (Month 1 baseline ka zikr)
· row 9 `week5=2`, `no_evidence=1` (baseline) · **`cites_logs_dir=0` har row me** ✅ — KEY `Q4(c)`, aur `P-47` ka naya
instance nahi bana.

**Teen cheezein jo check nahi dekh sakta tha:** row 9 ka evidence *"proving crash point is averted by poll boundaries"*
kehta hai — `n = 2` outages, ek shape, dispatcher bina load ke; ye `narrows` hai. Row 4 `2.790 s` restart cite karta hai,
jiska start clock kisi file me nahi (`P-53(c)`). Aur matrix ke neeche ka prose ab bhi kehta hai *"Row 9's Recovery
mechanism cell says none"* aur *"Read rows 5 and 9 together … an untested hole"* — edited row ke khilaaf.

#### 6. `💡` rewrites (Step 7) — `4 · 4 · 6` ✅

`docs/month_01/logs/WEEK_04.md` lines `190`, `605`, `1094`, `2007` pe chaar own-words blocks, chaar `Gaps vs reviewer:`
lines, reviewer ke blocks rakhe gaye. Teesra hafta carry band hua. **Order (reviewer text band karke pehle likhna)
kisi file se verify nahi hota — `not recorded`.**

#### 7. Close + handoff (Step 8) — `0 · 29 · True · True`

Har untick ke saath reason hai ✅. **Do ticks review pe hold nahi karte:** *"Chhe din ki log entries"* — close pe `5`
thi, ye chhathi hai aur review pe likhi gayi; *"Ek external postmortem, `P-43` pe mapped"* — mapped hai, source ke
saath match nahi karta (§9).

#### 8. Fresh clone (Step 10) — aur wo column jo kisi ne nahi padha

| File | `here` | `clone` | `clone_blob` = `head_blob` |
|---|---|---|---|
| `DIN_04` | **`42D0F894`** | `62196E9A` | `90f6da79` ✅ |
| `DIN_05` | `8B38705B` | `8B38705B` | `1021825f` ✅ |
| `DIN_06` | `C7F08739` | `C7F08739` | `73b95b49` ✅ |

KEY `Q5(a)` ✅ (clone = `62196E9A`), `Q5(c)` ✅. `Q5(b)` ke do arms (purane commit ka checkout) nahi chale.
**`42D0F894` CRLF hash hai.** Poora mechanism `P-57` amendment me: `14/16` seals `w/crlf` since `pull --rebase`
`2026-09-28 17:28:51` (reflog), `git status` clean sirf stat cache ki wajah se, `git checkout --` aur `git restore` is
state me no-op, delete + checkout restore karta hai, aur `-text` ke neeche `git hash-object` bhi `HEAD` blob se alag
(`81584003…` vs `90f6da79…`) jabki `eol=lf` ke neeche barabar.

#### 9. Reviewer ke apne reads `[MEASURED-R 2026-09-29]`

- **`blogprobe` database exist karta hai** — `7655 kB`, ek table `jobs`. `docs/blog/POST_01_OUTLINE.md:337` kehta hai
  *"`blogprobe` dropped"*. Bench ka `relay\_%` filter isko dekh hi nahi sakta, to `relay_underscore_dbs=0` ek probe DB ke
  hote hue pass hua. Check naam pe chalta hai, `P-54` ki shakal me.
- **Incident 04 vs uska source.** GitHub ka [October 21 post-incident analysis](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/)
  ek alag kahani kehta hai: `43 s` connectivity loss ke baad Orchestrator ne primaries West Coast pe promote kar diye,
  dono data centers me aise writes aa gaye jo doosre me nahi the, safe fail-back possible nahi raha, aur degradation
  ghanton ke backup restore aur replication catch-up se bani; backlog me paanch million se zyada hook events the aur
  TTL paar karne wale `~200k` webhook payloads drop hue. Entry ka root cause — *workers unhandled lost-connection
  exceptions pe mare, poisoned pools, manual fleet restarts* — aur quoted `MySQL::Error: Lost connection` source me nahi
  hain. Entry ka link (`…/postmortem-of-october-21s-incident/`) `404` deta hai. *(Source summary rephrased for
  compliance with licensing restrictions.)* **Ritual ki value doosre ke incident se seekhna hai; ye entry Relay ka
  `P-43` GitHub pe project karti hai.**
- **Evidence DB, reviewer probing ke baad:** counters `133|145|19|4|7|39|5|0|1`, jobs `108` `dead_letter|4|0`, `128`
  `succeeded|4|4`, `136` `running|1|1` — unchanged. `0` `relay_` DBs, `0` Relay python, `git status` clean.

---

### 🧠 Prediction review — `0.00 / 5.0`, aur is baar ek bhi line number nahi

Frozen text `docs/daily/week_05/DIN_06_PREDICTIONS_FROZEN.md` se **quote**, hash verify hua.

| Q | Frozen text (verbatim) | Score |
|---|---|---|
| **Q1** | *"(a) idk (b) idk (c) idk"* | **`0.00 / 1.0`** |
| **Q2** | *"(a) idk (b) idk (c) idk (d) idk"* | **`0.00 / 1.0`** |
| **Q3** | *"(a) idk (b) idk"* | **`0.00 / 1.0`** |
| **Q4** | *"(a) idk (b) idk (c) idk"* | **`0.00 / 1.0`** |
| **Q5** | *"(a) idk (b) idk (c) idk (d) idk"* | **`0.00 / 1.0`** |

**Total `0.00 / 5.0`. Week 5 frozen total: `1.45 / 30.0`** (Din 1 `not scored`, Din 2 `1.45`, Din 3–6 `0.00`).

Sub-part level `idk` pehli baar hua — Din 5 ka format note follow hua. **Par BRIEF ka doosra naya rule — *"jis sub-part
me file ya command ka naam hai, uske jawab ke saath wo line number likho jo padha"* — solah me se ek bhi sub-part me
nahi.** KEY ke scoring note ne das sub-parts derivable likhe the (`Q1(a)`, `Q1(b)`, `Q2(a)`, `Q2(b)`, `Q2(d)`, `Q3(a)`,
`Q3(b)`, `Q4(a)`–`(c)`) — `~3.4` points padhne se.

**Ab ye paanchwa lagatar din hai jisme ek bhi prediction attempt nahi hui.** Inflation zero hai aur wo record saaf hai.
Par protocol ki mechanism — predict, phir measurement se takrao — paanch din se chali hi nahi. Week 6 ka plan isko format
se attack karta hai (kam sub-parts, har sub-part pe `[padh ke]` / `[chala ke]` tag, aur ek `[padh ke]` `idk` bina *"kya
padha"* ke reading gap gina jaata hai), kyunki instruction akele do din me nahi hili. **Beat 4 ki file — nahi.**

---

### 🤖 Reviewer ki apni galat predictions aur defects — record ke liye

1. **KEY trap 8 ne *"LF-only frozen files pe `-text` se koi farak nahi"* likha.** KEY `17:18` pe likhi gayi; `17:28:51`
   pe `pull --rebase` ne chaudah seals CRLF kar diye. Premise likhte waqt sach tha aur dus minute baad galat. Aur yahi wo
   jagah hai jahan `-text` farak dalta hai.
2. **BRIEF Step 10 ka clone check `here=` print karta tha, par Part C ki koi row use recorded seal se compare nahi karti
   thi.** Check author ki side pe fail ho hi nahi sakta tha. File me mismatch tha, aur na user ne padha na check ne.
3. **BRIEF Step 4 ka `d30_header_open` heading padhta tha** — hamesha `0`. `P-18` ki shakal, reviewer ke haath se.
4. **Bench ka `relay_underscore_dbs` naam-bound hai** (Week 4 se carry) — `blogprobe` jaisa probe usko dikhta hi nahi.

**KEY ne jo theek kaha, aur aaj measured:** `Q1(a)` `0` · `Q1(b)` `15` · `Q1(c)` same/same · `Q2(c)` exactly `.pyc` +
`GEMINI_RULES.md` · `Q2(d)` BRIEFs tracked rahe (`29`) · `Q3(a)` `0`/`868`/`True` · `Q4(c)` `0` · `Q5(a)` · `Q5(c)`.

---

### 💡 What I understood — own words, 2026-10-03

1. Git directory traversal: `.gitignore` me agar directory level ignore rule lagaya jaye to git us directory ke andar jata hi nahi, isliye `!**/daily/**/` jaise directory negations pehle lagane padte hain aur specific files baad me.
2. Allow-list vs deny-list ka default: Deny-list (sirf chuni hui files ignore) me nayi unclassified files chupchap public ho jati hain (`P-54`), jabki Flip rule (default-ignore) lagane se nayi unclassified files local rehti hain aur public leak prevent hota hai (`D-32`).
3. Tracked aur Ignored ka intersection: `.gitignore` pehle se tracked files ko untrack nahi karta; `.pyc` history me tracked tha isliye use explicit `git rm --cached` se clean kiya gaya, jabki `GEMINI_RULES.md` deliberate exception tha.
4. Positive controls expire hote hain: Jab `.pyc` repo se delete ho gaya to positive control ko usi din `*_BRIEF.md` par switch kiya gaya taaki checks functional rahein.

Gaps vs reviewer: Reviewer ne emphasize kiya ki galat field padhne wale check (heading vs status line) decorative hote hain jo hamesha pass dikhte hain, aur git attributes content ka canonical hash rule badalta hai disk ke actual bytes nahi.

### 💡 What the session established — **user ko ye apne shabdon me dobara likhna hai** (Week 6 Din 2, Step 0.5)

> Ye section reviewer ne likha hai. Protocol ke hisaab se isko user ke apne shabdon me replace hona hai.

1. **Default wahi decide karta hai jo us cheez ke saath hota hai jiska kisi ne naam nahi liya.** Ignores ki list → nayi
   class publish. Flip → nayi class chhup jaati hai. Fail-safe hai, fail-silent nahi: jo class publish honi chahiye thi
   wo bhi chupchaap local reh sakti hai.
2. **Git ignored directory me utarta hi nahi.** Isliye `!**/daily/**/` pehle, leaf negations baad me — traversal, ordering nahi.
3. **`.gitignore` kabhi untrack nahi karta**, aur tracked∩ignored hamesha defect nahi hota (`GEMINI_RULES.md`).
4. **Positive control apne subject ke saath expire hota hai.** `.pyc` gaya to control usi din `*_BRIEF.md` pe gaya.
5. **Galat field padhne wala check decorative hai** — heading vs status line, clone vs apni copy.
6. **Attribute ye badalta hai ki content ka hash kya *hona chahiye*, disk pe kya hai ye nahi.** Git tab dekhta hai jab stat badle.
7. **"Satisfied as written" aur "jo test karna tha wo test hua" alag claims hain** — `D-30` gate 1 ka bound boundaries se aaya.

---

### ⚠️ Closeout corrections

| # | Jaise record hua | Jo measured / source me hai | Provenance |
|---|---|---|---|
| 1 | Handoff §3.3: *"`P-51` (Stale reaper query) — update reaper query to check `claim_generation`"* | `P-51` = `record_execution` handler ke `try` ke andar, infra fault job failure gina jaata hai; decided shape: use `try` se bahar le jaana (`P-51` amendment, Din 3). Reaper query ka isse koi lena-dena nahi | `docs/PROBLEMS.md` `P-51` |
| 2 | `D-32` final item 4 + Cost 9: *"`.gitattributes` enforces `eol=lf`"* | File me `-text`. CRLF copy pe `hash-object`: `-text` `81584003…`, `eol=lf` `90f6da79…` = `HEAD` | `[MEASURED-R]`, `D-32` amendment |
| 3 | Handoff: *"dual-hash … to **ensure** cross-platform auditability"* | Author ki machine pe `14/16` seals dono hash pe fail. Sirf attribute wale commit ka fresh clone bachta hai → `narrows` | `[MEASURED-R]`, `P-57` amendment |
| 4 | `D-32` item 3: flip *"**guarantees** that any future unenumerated class is ignored"* | Default badalta hai; `git add -f` aur stage-all bache hain — `D-32` Cost 6 khud *narrows* kehta hai | `DECISIONS.md` |
| 5 | Step 4: `OPEN` header se hata (`d30_header_open=0`) | Status line `OPEN` hi thi; check heading padhta tha. Review pe amendment line | `[MEASURED-R]` |
| 6 | README row 9: *"**proving** crash point is averted"*; matrix ke neeche ka prose | `n = 2`, ek outage shape → `narrows`. Prose ab bhi row 9 ko *"none"* + *"untested hole"* kehta hai | README |
| 7 | README row 4: *"`2.790 s` restart in Week 5 Din 2"* | Start clock `12:08:31.188` kisi file me nahi (`P-53(c)`) | `P-53` |
| 8 | POSTMORTEMS Incident 04 ka root cause aur link | Source ek cross-region failover + split writes + restore/replication ki kahani hai; entry ka mechanism source me nahi; link `404` | GitHub post-incident analysis, §9 |
| 9 | DoD `[x]` *"Chhe din ki log entries"* | Close pe `5`. Ye chhathi hai, review pe | `WEEK_05.md` headings |
| 10 | Bench *"`0` probe DBs"* | `blogprobe` maujood; `POST_01_OUTLINE.md:337` usko dropped kehta hai | `[MEASURED-R]` |
| 11 | `D-30` Owner: *"containerized deployment … Week 6"* | Din 6 BRIEF Part D: *"Processes Compose me — Month 2 ke baad"*; `D-30` Rejected (a): *"remains the production target"*. Teen jagah teen owner. `WEEK_06.md` isko Month 4 (§5.5) deta hai, reason ke saath | `DECISIONS.md` |

---

### 🚧 Unresolved / carried → Week 6

1. **`P-57` restore + attribute ka faisla** — Week 6 Din 1 Step 0.
2. **Week 5 ke paanch `💡`** — Week 6 Din 1. **Is entry ka `💡`** — Week 6 Din 2 Step 0.5.
3. **`P-56` census + fix, `P-55`** — Week 6 Din 1.
4. **`P-44`** Din 2 · **`P-51`** Din 4 · **`P-45`** load harness Din 5 · **`P-53(d)`/`P-36`** crash-loop + `P-53(b)` Din 6.
5. **Incident 04 source se dobara, aur Incident 05** — Week 6 Din 6.
6. **README row 9 ka wording, uske neeche ka prose, row 4 ka number** — Week 6 Din 6.
7. **`D-32` ka retention half (`logs/`)** — Din 3 se unowned; `WEEK_06.md` isko Week 8 (Month 2 close) deta hai.
8. **`blogprobe`** — drop ya keep, user ka faisla, Week 6 Din 1 Step 0.
9. **SQL parallel track** (`MONTH_02.md` §2: *"chaaron hafte"*) — Week 5 me schedule hi nahi hua. Silent slip tha, ab
   record hai. Faisla `WEEK_06.md` me.

---

### Week 5 close

| Din | Subject | Grade | Frozen |
|---|---|---|---|
| 1 | Worker claim-poll boundary | `8.0` | `not scored` |
| 2 | Heartbeat/mark/reaper/dispatcher boundaries, supervisor, `D-31` | `7.5` | `1.45` |
| 3 | Publishing surface `D-32` `DRAFT`, `D-33` pins, `P-51` decided | `7.5` | `0.00` |
| 4 | Pool premise observed, two lost numbers replaced, `P-44` shape | `7.0` | `0.00` |
| 5 | `P-41` end to end, `D-30` gates, `P-56` | `7.5` | `0.00` |
| 6 | Week close — `D-30`, `D-32`, `D-28`, README, handoff | **`6.5`** | `0.00` |

**Din 6 `6.5/10`:** faisle aur checks ki shape achhi — `D-32` ka differential galat rule pe fail ho sakta tha aur hua
nahi, `.pyc` ka control usi din replace hua, `D-30` me `Rejected` naam se, README ke cells tracked files pe point karte
hain. Neeche khinchne wali cheezein: seal mismatch din ki apni file me tha aur padha nahi gaya; jo attribute likha gaya
wo faisla nahi tha; ek public file ek asli company ke incident ka galat root cause kehti hai; aur `ensure`, `guarantees`,
`proving` teen jagah wahan jahan evidence `narrows` kehta hai.

**Promise #4 ka process half `[NO EVIDENCE]` se `narrowed` hua — Week 5 ka main result, aur wo earned hai.**

---

### ❓ Next thought

Week 5 ne ek sawaal chhe shakal me poocha: *record kis moment ka hai?* Din 6 ne uska ek aur roop dikhaya — **record kis
jagah ka hai.** Clone ka hash sahi tha, author ki copy ka nahi. Heading me `OPEN` nahi tha, status line me tha. Postmortem
ne GitHub ka naam liya, kahani Relay ki thi.

Week 6 me pehli baar ek external cheez aa rahi hai jo apna record khud rakhti hai — provider ki call count, tokens, bill.
Relay ka record (`attempts`, log lines) usse alag hoga, aur Din 1 ke baad bhi log sirf utna sach bolega jitna `COMMIT`
bolta hai. **Jab dono record alag number dein, paisa kaunsa naapta hai?**

---

*Din 6 BRIEF:* [`../daily/week_05/DIN_06_BRIEF.md`](../daily/week_05/DIN_06_BRIEF.md) ·
*Seal:* [`../daily/week_05/DIN_06_PREDICTIONS_FROZEN.md`](../daily/week_05/DIN_06_PREDICTIONS_FROZEN.md) ·
*Handoff:* [`../daily/WEEK_05_HANDOFF.md`](../daily/WEEK_05_HANDOFF.md) ·
*Next:* [`../planning/WEEK_06.md`](../planning/WEEK_06.md) → [`../daily/week_06/DIN_01_BRIEF.md`](../daily/week_06/DIN_01_BRIEF.md)
