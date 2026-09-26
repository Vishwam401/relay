**Week 4 · Din 5** · Plan: [`../../planning/WEEK_04.md`](../../planning/WEEK_04.md) ·
Log: [`../../logs/WEEK_04.md`](../../logs/WEEK_04.md) · Sealed: [`DIN_05_KEY.md`](DIN_05_KEY.md) ·
Kal: [`DIN_04_BRIEF.md`](DIN_04_BRIEF.md)

**Goal:** Relay ko todo, aur **naam se** todo. Pool `2` connections pe, sustained enqueue load, Postgres beech
me band, aur `/healthz` jiska matlab likha hua ho. Sab **disposable DB** pe — evidence DB ka delta `0`.

**Architectural invariant (aaj ke baad):**
> Har capacity claim ke saath uska **binding constraint** naam se likha hua hai — pool, `max_connections`,
> handler duration, ya poll interval — aur load ke neeche degradation ka **shape** (queue depth badhna,
> ek naam wala timeout, ya silent stall) **measured** hai, maana hua nahi.

**Deliverable:** `P-38` aur `P-39` ke do repair, dono differential test ke saath · connection budget ki
arithmetic, `max_connections` **measured** · pool exhaustion ka naam wala error + uska measured wait ·
`pending` count ka ek **series**, ek reading nahi · `/healthz` + jo wo **nahi** bata raha uska naam ·
Postgres-down ke **do alag** failures · aur `D-28`/`D-29` ke liye evidence.

**Budget:** `25 + 20 + 25 + 20 + 30 + 15 = 135 min`. Plan me `125` tha; Step 0 me do carried repair aa gaye
hain, aur wo `+10` hai.

**Cut order — plan se, aur ye badla nahi hai.** `Step 0` ke repair **kabhi nahi kat sakte** (Din 6 ka reconcile
chain unpe khada hai). Uske baad: pool exhaustion **rakhna** → Postgres-down **rakhna** → sustained load
**kaat sakte ho** → `10k` **kaat sakte ho**. Reason: pehle do **failure modes** hain jo README ke failure
matrix me jaate hain; baad ke do **numbers** hain jo *"kitna"* batate hain. **Adhoore numbers se adhoora matrix
bura hai.**

---

## Rules — ye paanch roz wahi hain

> **Paste rule:** Part A, Part C, Part D Gemini ko ja sakte hain. **Part B kabhi nahi. KEY kabhi nahi.**
>
> **Seal rule:** paanchon answers **Step 0 me** freeze honge, Step 1 shuru hone se pehle. Har KEY section tabhi
> khulta hai jab uss step ka **measurement** ho chuka ho. Output prediction se alag nikla to **pehle apni
> explanation likho**, phir Gemini ke saath uss output pe reason karo, phir KEY.
>
> **Provenance rule:** iss BRIEF ke saare numbers `[MEASURED-R 2026-09-09]` hain — Din 4 ke closeout review me
> actually chalaye gaye, disposable DB `relay_w4d4_review` / `relay_w4d4_target` / `relay_w4d5_probe` pe
> (teenon drop ho gayi). Jo tum chalao wo `[MEASURED]`.
>
> **Aaj ka apna rule, aur ye kal se sakht hai:** aaj ka koi bhi row evidence DB me **nahi** jaata, aur aaj ke
> baad `relay` **head pe** hona chahiye — kal wo ek revision peeche tha aur `alembic check` red thi. C5 dono
> cheez `throw` karta hai.
>
> **Aur ek scoring rule jo kal spasht hua:** score sirf `DIN_05_PREDICTIONS_FROZEN.md` ke text ka hota hai.
> Kal `### Observed` me likha gaya mechanism `Q2` aur `Q4` me galti se count ho gaya tha aur score `2.25` se
> `1.5` correct hua. **Prediction me mechanism likho, warna outcome sahi hone par bhi aadha score hai.**

### Read order — isko literally follow karo

1. Sirf **Step 0** padho (`0A`–`0D`).
2. Editor outline se seedha **Part B** pe jao. Step 1–5 aur Part C abhi mat kholo.
3. Paanch predictions likho (`idk` valid hai aur `0` score karta hai), phir Step 0 ke seal command pe wapas aao.
4. Frozen hash print hone ke baad **C0** kholo. C0 pass ho tab Step 1 aur baaki Part A / Part C khulte hain.

### Kal jo sach nikla — chhe cheezein aaj ka kaam badalti hain

`[MEASURED-R 2026-09-09, Din 4 closeout review]`. Ye chhe **prediction ke jawab nahi** hain; ye aaj ke maidan ki
shape hain, aur inhe na jaanne se aaj ka din galat measure hoga.

| Kya | Actual | Aaj ka asar |
|---|---|---|
| **`alembic -c <ini>` ab kuch nahi karta** | Kal ka `P-28` preventer `os.environ["DATABASE_URL"]` ko **unconditionally** `sqlalchemy.url` bana deta hai. Variable `A` pe, ini copy `B` pe → `alembic -c <copy> upgrade head` ne `B` me **`0` tables** banayi aur exit `0` diya. Variable hataya → **`6` tables**. Precedence ab `$env:DATABASE_URL` > `-c <ini>` > `alembic.ini`, bilkul chup-chaap | **Step 0C.** Ye aaj ka pehla repair hai, aur Step 1 ke pehle hona zaroori hai — aaj poora din disposable DB pe chalega aur `-c` hi wo escape hatch hai (`P-39`) |
| **`sink_deliveries` pe do creator, do naam** | `src/sink.py` ki DDL inline `UNIQUE` likhti hai → PostgreSQL usko `sink_deliveries_idempotency_key_key` naam deta hai. Migration `uq_sink_deliveries_idempotency_key` banati hai, aur uska `else` branch **apne hi naam** ko dhoondhta hai. Sink-pehle order pe: **do** unique constraint, ek hi column pe. `downgrade()` sirf ek girata hai | **Step 0C.** Doosra repair, do line ka. Aaj iss table pe write numbers aayenge — do index maintain ho rahe hain aur uska koi note nahi hai (`P-38`) |
| **`max_connections = 100`, aur `docker-compose.yml` me koi override nahi hai** | `show max_connections` → `100`. Compose file me `command`, `max_connections`, `shared_buffers` — teenon absent | **Step 1.** Ye number tumhe **khud** naapna hai (plan ka rule), par ye BRIEF me isliye hai ki Step 1 ka kaam *"naapna"* nahi *"arithmetic likhna"* hai. Ginti ka denominator diya hua hai; numerator tumhara kaam hai |
| **Pool **lazy** bharta hai — `pool_size=5` ka matlab `5` connections nahi hai** | `create_async_engine(...)` ke baad, kisi query se pehle: **`0`** connections. Ek query ke baad: `1`. `8` concurrent holds ke dauran: **`8`** (pool `5` + overflow `3`). Release ke baad: **`5`** retained, overflow band. `20` concurrent holds pe, limit `5+10=15`: **`15`**, aur baaki `5` `pool_timeout` pe **queue** me baith gaye aur succeed hue | **Step 1 aur Step 2.** *"Paanch process × `15` = `75`"* ek **ceiling** hai, ek observation nahi. Idle pe wo number bilkul aur hai |
| **`application_name` **khaali** hai** | SQLAlchemy + asyncpg default pe `pg_stat_activity.application_name = ''` — paanchon engine indistinguishable. `connect_args={"server_settings": {"application_name": "..."}}` dene pe wo dikhta hai `[MEASURED-R]` | **Step 1.** Plan ka verification command `... where application_name = :app` likhta hai. Wo command aaj **`0` lautayega**, aur `0` ko *"pool override load nahi hua"* padhna aaj ki sabse aasaan galti hai. Pehle `application_name` set karo, phir uss column pe filter karo |
| **Receiver ka `ON CONFLICT DO NOTHING` **wait** karta hai** | Ek holder transaction same key pe khuli rakhi → `POST /deliver` `3.0 s` pe **unfinished** tha, aur holder ke rollback pe `3.058 s` pe complete hua. Receiver pe koi `lock_timeout` nahi | **Step 2.** Ye pool ke saath compose hota hai: dispatcher HTTP call ke **across** row lock rakhta hai (Din 3 Faisla 4), to receiver ka wait ek Relay connection ko bhi rokta hai. `[links MEASURED, chain INFERRED]` — aaj chain ka receiver-half naapna hai (`P-41`) |

### Aur do vocabulary cheezein, taaki Situation 1 ke liye KEY na kholni pade

**Terms used today** — ye *"cheez kya hai"* batata hai, *"kya hoga"* nahi:

- **`pool_size`** — engine kitni connection **reuse** ke liye zinda rakhta hai. **`max_overflow`** — peak pe iske upar kitni **extra** khol sakta hai (release pe wo band ho jaati hain). **`pool_timeout`** — jab dono bhar gaye, ek naya caller kitni der **wait** karega error se pehle. Default `30 s`.
- **`max_connections`** — Postgres server ka total connection limit, saare databases aur saare clients ke liye. **`superuser_reserved_connections`** — usme se kitni sirf superuser ke liye bachi rehti hain (default `3`).
- **`pg_stat_activity`** — ek server-side view, ek row per connection, uske `state` (`active` / `idle` / `idle in transaction`), `wait_event`, `application_name` ke saath.
- **`application_name`** — ek client-supplied label jo `pg_stat_activity` me dikhta hai. Iska koi behaviour nahi hai; wo sirf attribution ke liye hai.
- **`pool_pre_ping`** — SQLAlchemy ka flag jo pool se connection dene se pehle ek sasti liveness query maarta hai. Aaj ye ek **faisla** hai, ek default nahi.
- **`statement_timeout` / `lock_timeout`** — Postgres ke server-side bounds: ek statement kitni der chal sakta hai, aur ek lock ka intezaar kitni der ho sakta hai.
- **liveness vs readiness** — *"process zinda hai"* versus *"process traffic le sakta hai"*. Ye do alag sawaal hain aur ek hi endpoint dono ka jawab nahi de sakta.

---

# Part A — Steps

## Step 0 — 25 min: commit, bench, freeze, aur do carried repair

### 0A — pehle commit, phir bench

Kal ke close pe **chhe cheezein uncommitted** thi: `alembic/env.py`, `src/database.py`, `src/models.py`,
`src/sink.py`, `src/worker.py`, aur untracked `alembic/versions/w4d4_sink_unique_add_sink_unique.py`.

**Pehle inhe commit karo.** Warna aaj ka C0 ka clean-tree check kuch assert nahi karta, aur aaj ke repair kal ke
feature ke saath ek hi diff me mil jaayenge — wahi `git bisect` ki galti jo Din 1 ne ek baar ki thi.

Do commit, ek nahi: **(1)** Din 4 ka feature work, **(2)** aaj ke `P-38`/`P-39` repair (0C ke baad).

Opening bench: `relay` ke aath counter + `alembic current` + `alembic heads` + job `136` ka baseline. C0 usko
capture karta hai, hardcode nahi.

### 0B — environment aur logs

Aaj `python -u` non-negotiable hai (plan, Measurement hygiene 1) — aaj timing naapi ja rahi hai aur buffered
stdout ek timing instrument ko jhooth bana deta hai.

Log naming: `logs/w4d5_<step>_<role>.log`, stdout aur stderr **alag**. Aur `P-22` ka amendment yaad rakho:
**PowerShell pipeline se timestamp mat lagao.** Aaj ke timing claims process ke apne clock se aayenge.

### 0C — predictions likho aur freeze karo

`DIN_05_ANSWERS.md` banao (kal ke template ka shape), paanchon `### Prediction` bharo, `### Observed` aur
`### After KEY` **khaali** chhodo, phir seal command chalao. Wo `DIN_05_PREDICTIONS_FROZEN.md` banata hai aur
uska SHA-256 print karta hai. Us copy ko phir kabhi nahi chhoona.

**Kal ka sabak, ek line me:** outcome likhna aadha score hai. **Mechanism likho** — kaunsa timer, kaunsa
predicate, kaunsi library default.

### 0D — do repair, dono ka differential test

**Repair 1 — `P-39`, `alembic/env.py`.** Do cheez chahiye: `-c` ka respect, aur ek **announcement**.

| Kya | Kyun |
|---|---|
| Override tabhi lage jab config explicitly supply nahi hui **ya** ek naam wale flag ke saath | *"Sabse specific instruction jeetta hai"* — abhi ulta hai |
| `env.py` har invocation pe resolved database **aur uska source** print kare (`env` / `-c` / `alembic.ini`) | Ek preventer jo chup-chaap jeetta hai, detector ka ulta hai. `src/database.py` runtime pe ye already karta hai; schema likhne wala path hi wo hai jahan ye nahi tha |

**Differential test — ek request se ye pakda nahi jaata, do se pakda jaata hai:**

| Arm | Broken (aaj ka code) | Fixed |
|---|---|---|
| `$env:DATABASE_URL` set, `alembic -c <ini→B> upgrade head` | `B` me `0` tables, exit `0` | `B` migrate hoti hai, **ya** ek naam wala error — chup-chaap nahi |
| `$env:DATABASE_URL` **unset**, wahi command | `B` migrate hoti hai | `B` migrate hoti hai (unchanged) |
| `$env:DATABASE_URL` set, `-c` **ke bina** | witness DB migrate hoti hai | witness DB migrate hoti hai (unchanged) |

**Teesra arm zaroori hai** — warna repair `P-28` ko dobara khol dega, aur wo kal ka poora Step 1 tha.

**Repair 2 — `P-38`, `src/sink.py` ki DDL.** `UNIQUE` ka **ek** owner hona chahiye. Constraint migration me
hai, to DDL se inline `UNIQUE` hataana hai.

**Differential test — aur iska arm wahi hai jo kal chala hi nahi:**

| Arm | Broken | Fixed |
|---|---|---|
| **Sink-pehle**: fresh DB → sink start (DDL) → `alembic upgrade head` → unique constraints ginno | `2` | `1` |
| Migration-pehle: fresh DB → `alembic upgrade head` → sink start → ginno | `1` | `1` |
| **Sink-pehle** DB pe `head → -1 → head` | round trip **nahi** (ek constraint reh jaata hai) | round trip |

**Aur ek cheez jo aaj `throw` karni hai:** ye do repair `src/` ke us hisse ko chhoote hain jiska koi test nahi
hai. `pytest tests -q` ka `7 passed` **aaj ke code ke liye gate nahi hai** — uska ek bhi test kisi service
module ko import nahi karta (`P-37`). Usko chalao, aur log me `record only` likho.

---

## Step 1 — 20 min: connection budget ki arithmetic, load se pehle

Aaj ka pehla kaam ek **ginti** hai, ek run nahi. **Pehle likho, phir naapo** — aur agar dono alag nikle, wahi
aaj ka sabse interesting finding hai.

Aaj ke code me: `create_async_engine(DATABASE_URL, echo=True)` aur SQLAlchemy async defaults `pool_size=5`,
`max_overflow=10`, `pool_timeout=30 s`. **Har process apna engine banata hai.**

**Teen number likho, teenon alag:**

| Number | Kya hai |
|---|---|
| **Ceiling** | Paanch process × `(pool_size + max_overflow)` = ? Aur uske saath `psql` sessions aur aaj ka load script |
| **Idle** | Paanch process khade hain, koi kaam nahi kar rahe. Kitni connections? |
| **Peak** | Load ke dauran, ek **series** me naapa hua |

Phir Postgres se poocho — maano nahi:

```sql
show max_connections;
show superuser_reserved_connections;
select count(*) from pg_stat_activity;
select count(*) from pg_stat_activity where datname = current_database();
select application_name, state, count(*) from pg_stat_activity
  where datname = current_database() group by 1,2 order by 1,2;
```

**Aur `application_name` pehle set karo.** Aaj wo khaali hai (upar wali table), to per-process attribution
possible **nahi** hai jab tak `connect_args` me `server_settings` na jaaye. Ye ek `src/database.py` ka chhota
change hai aur aaj ke poore Step 2 ka instrument hai — iske bina *"kis process ka pool"* naapa hi nahi ja
sakta, aur plan ka poora point wahi sawaal hai.

**Step executable end:** paanch process khade karo, `application_name` ke saath, aur idle number naapo.

## Step 2 — 25 min: pool `2` pe, aur **ek** variable badla

`pool_size=2, max_overflow=0`. **Aur yahan `AGENTS` rule 7 ka trap hai:** `echo=True` ka apna per-statement
cost hai (Week 2 me `2.3 ms`). Agar `pool_size` **aur** `echo` ek saath badle, to jo number aayega wo **not
isolated** hai.

| Option | Cost |
|---|---|
| `echo=True` rakho, sirf pool badlo | Number *"echo ke saath"* wala hai — aur wo honest hai, kyunki aaj tak ka poora project `echo=True` pe chala hai |
| Teen run: `(echo=True, pool=15)` → `(echo=True, pool=2)` → `(echo=False, pool=2)` | Do attributable delta. `25 min` me nahi hoga |

**Chuno, aur jo chuna wo log me likho.** Ek line, aur wo `D-28` me jaati hai.

**Aur aaj ka asli sawaal ye hai, aur ye plan me naam se likha hai:** pool exhaust hone pe **kaun** girta hai —
API ka `POST /jobs`, worker ka claim, ya dispatcher ka HTTP-inside-transaction? Teeno **alag process, alag
engine** hain, to *"pool exhaustion"* actually **per-process** event hai. *"Pool bhar gaya"* ek vague statement
hai; **kis process ka pool** — wahi measurement hai.

**Do cheez naapo, aur dono alag likho:**
1. Exhaustion ka **shape** — error ka poora naam, aur wo error **kahan se** aaya (client-side pool, ya Postgres).
2. Exhaustion se pehle ka **wait** — kitni der. Aur wo `pool_timeout` se match karta hai ya nahi.

**Aur ek receiver-side measurement jo kal ke `P-41` se aata hai, `10 min`:** ek holder transaction
`sink_deliveries` pe same key ke saath khuli rakho, phir ek `POST /deliver` maaro aur uski latency naapo.
Kal `3.058 s` measure hua tha ek `3.0 s` holder ke against. Aaj isko **apne** numbers se dohrao aur ek line
likho: receiver ka response time kis cheez se **bandha** hua hai.

## Step 3 — 20 min: `/healthz`, aur "healthy" ka matlab

Chaar candidate semantics, aur inme se ek hi honest hai:

| Semantics | Kya check karta hai | Kya **jhoot** bolta hai |
|---|---|---|
| `200` always | Sirf uvicorn zinda hai | DB gir gaya to bhi `200` |
| `SELECT 1` DB pe | DB reachable **iss process ke pool se** | Worker mar gaya to bhi `200` — jobs kabhi nahi chalengi |
| `SELECT 1` + `pending` count | Queue depth bhi | **Ye ek inventory leak hai.** Auth nahi hai (`D-03`), aur `pending` count business volume batata hai |
| `SELECT 1` + last worker heartbeat | Worker liveness | Heartbeat sirf **job ke dauran** chalta hai (`P-21`) — idle worker *"dead"* dikhega |

**Faisla lo, aur jo cheez `/healthz` **nahi** bata raha uska naam likho.** `D-28` me ye line jaani chahiye:
`/healthz` **liveness** deta hai, **readiness nahi**, aur **inventory kabhi nahi** — jab tak auth na aaye.

**Aur ek interaction jo Step 2 ke saath hi paida hoti hai, aur ye aaj ka sabse non-obvious finding ban sakta
hai:** `/healthz` agar `SELECT 1` karta hai to wo **usi pool** se connection maangta hai jo `pool_size=2` pe
hai. Load ke peak pe dono connections `POST /jobs` ke paas hain → `/healthz` `pool_timeout` tak **queue** me
baithega aur phir timeout dega. Nateeja: **service saturated hai, par health check *"dead"* keh raha hai** — aur
ek asli deployment me orchestrator usko restart kar dega, jo **saturation ko outage me badal deta hai.**

**Isko naapo** — load ke dauran `/healthz` maaro, latency note karo — aur `D-28` me likho. Ye ek `[MEASURED]`
line ban sakti hai jo blog post me seedha jaati hai.

## Step 4 — 30 min: sustained enqueue, aur queue lag ka **direction**

**Pehle ek faisla, aur ye `AGENTS` rule 20 se aata hai — install command nahi, faisla:**

| Option | Cost |
|---|---|
| Locust | `[MEASURED-R 2026-09-05]` `pip install --dry-run locust` iss venv pe → **28 packages**: poora Flask web-UI stack + gevent (monkey-patching) + pyzmq + pywin32. Month 1 ke aakhri hafte me `requirements.txt` ka footprint dugna. Badle me: ramp-up, distributed mode, ek UI jo aaj chahiye nahi |
| `httpx` + `asyncio` ka ~30-line script | `httpx` **already installed** hai, zero naya dependency. Badle me: ramp-up aur percentile reporting khud likhni padegi |

**Jo chuno wo `D-28` me ek line ke saath jaata hai.** Aur agar Locust chuna aur install `> 10 min` le raha hai,
wo signal hai ki scope kaatne ka waqt aa gaya — `requirements.txt` ke saath ladna aaj ka kaam nahi hai.

**Aur `10k` enqueue ka path khud ek faisla hai:** HTTP se (`POST /jobs` × `10k` — API + pool + middleware sab
naapte ho, par slow) versus ek bulk `INSERT ... SELECT generate_series(...)` (`10k` rows do second me, aur phir
tum **sirf worker drain** naapte ho). **Dono alag cheez naapte hain**, aur kaunsi naapni hai ye **pehle** likho.
Dono chahiye to wo do run hain, ek nahi.

**Aaj ka asli number `requests/sec` nahi hai.** Aaj ka number ye hai: **enqueue rate `X`/s pe, `pending` count
badhta hai ya flat rehta hai** — kyunki wahi backpressure ka sawaal hai. Aur wo Locust se nahi aata, DB se aata
hai, ek **series** me har `5 s`:

```sql
select now(), status, count(*) from jobs group by 2 order by 2;
```

**Chaar metrics, chaaron SQL se — koi `/metrics` endpoint nahi (`D-28` ka reason):** queue depth
(`pending` count) · latency p50/p99 (Din 2 ki query) · **retry rate** (`attempts > 1` wali rows ka share) ·
**DLQ count** (`status = 'dead_letter'`). **Chaaron ki query ek jagah likho** — ye Din 6 ke README ke *numbers*
section ka direct input hai, aur bina retry rate / DLQ count ke roadmap ka observability item adhoora rehta hai.

**Worker ka throughput bound likhne se pehle `worker.py` ka loop dobara padho, kyunki wahan ek trap hai:**
`await asyncio.sleep(POLL_INTERVAL_SECONDS)` **sirf** us branch me hai jahan koi job claim nahi hui
(`if not claimed_job: ... continue`). Job mil gayi to mark ke baad loop **turant** dobara claim karta hai.
Matlab `POLL_INTERVAL_SECONDS = 2.0` **backlog ke waqt throughput bound nahi karta** — wo sirf khaali queue pe
ek naye job ki **discovery latency** (`0` se `2.0 s`) bound karta hai. Backlog pe bound teen cheezon ka jod hai:
handler duration + per-job **teen alag transactions** (`record_execution`, effect, mark) + claim ka
`SELECT ... FOR UPDATE SKIP LOCKED ... LIMIT 1`. **Arithmetic pehle likho, phir naapo.**

## Step 5 — 15 min: Postgres beech me band

```powershell
docker compose stop db
# 20 s baad
docker compose start db
```

Roadmap ka sawaal: *"worker crash karta hai ya retry karta hai?"* Aur aaj **do alag** failures hain jinko alag
likhna hai:

1. Worker ka **live** connection toota (query ke beech).
2. Worker ne pool se ek **stale** connection uthaya (DB wapas aa gaya, par pool ko pata nahi).

Doosra pehle se zyada khatarnak hai kyunki wo **DB up hone ke baad** bhi failures deta hai. Aur uska mitigation
(`pool_pre_ping`) aaj **decide** hota hai, chup-chaap add nahi hota — `AGENTS` rule 22 ka **deletion test**
lagao: agar `pool_pre_ping=True` hata do, kya SQLAlchemy/asyncpg already handle karta hai? **Naapo, phir
likho.**

**Aur ek cheez jo aaj naap ke likhni hai:** jab DB down thi, uss dauran enqueue hui request ko **client ne kya
dekha**, aur **`running` rows ka kya hua** — kyunki reaper bhi down tha (wo bhi usi DB pe hai). Ye Contract #1
(*"accepted job is never silently lost"*) ka pehla asli stress hai, aur Din 6 ka Month 1 verdict iss number pe
khada hai.

---

## Din close pe reviewer ko kya dena hai

1. `DIN_05_PREDICTIONS_FROZEN.md` — hash ke saath, unchanged.
2. `DIN_05_ANSWERS.md` — paanchon `### Observed` bhare hue (**KEY se pehle**), phir `### After KEY`, phir
   `## Total Score`.
3. `DIN_05_DESIGN.md` — Faisla: `echo`/pool ka isolation · `/healthz` ki semantics · load tool · `10k` ka path ·
   `pool_pre_ping`. Har ek me `Chosen` / `Rejected` / `Cost`.
4. `logs/w4d5_*.log` — stdout aur stderr alag.
5. Do repair ke **teen-arm** aur **teen-arm** differential outputs, verbatim.
6. `pending` count ki **series** (ek reading nahi), aur exhaustion error ka poora text.
7. Evidence DB: delta `0` **aur** `relay` head pe.

---

# Part B — Prediction questions — **Gemini ko paste mat karna**

> Paanchon apne head se. `idk` valid hai aur `0` score karta hai — ek guess ko knowledge ki tarah likhna usse
> bura hai. **Aur mechanism likho, sirf outcome nahi** — kal `Q2` ka outcome sahi tha, mechanism nahi tha, aur
> wo `1.0` ke bajaye `0.5` tha.

**Q1.** `pool_size=2, max_overflow=0`, `pool_timeout=30`. `50` concurrent users `POST /jobs` maar rahe hain.
(a) Client ko kya milega — `500`, ek timeout, ya slow `202`? (b) **Pehla** error kitni der me, aur wo error
kis layer se aayega — Postgres se ya application se? (c) Agar handler ka DB kaam `5 ms` ka hai, to kya `50`
users ke liye `2` connections **kaafi** hain? Apni arithmetic likho.

**Q2.** Paanch process, har ek `create_async_engine` default pe (`pool_size=5, max_overflow=10`).
(a) **Idle** state me Postgres pe kitne connections dikhenge? (b) Load pe kitne? (c) `max_connections` ke
against ye safe hai ya nahi — aur **kaunsa** number tumne yahan use kiya, ceiling ya observed?

**Q3.** Ek worker, handler `0.1 s`, `POLL_INTERVAL_SECONDS = 2.0`.
(a) Theoretical max throughput kya hai jobs/sec me? **Arithmetic likho**, aur batao `2.0 s` uss arithmetic me
aata hai ya nahi. (b) Enqueue rate `20`/s pe `pending` count kaise behave karega? (c) Agar `pending` flat
rehta hai, to iska matlab throughput `20`/s se **zyada** hai — ya kuch aur bhi ho sakta hai?

**Q4.** `docker compose stop db` while a worker is mid-`SELECT`.
(a) Worker crash karega ya exception pakad ke poll karta rahega? Aur `MAX_ATTEMPTS` iss raaste pe **lagta hai
ya nahi**? (b) DB wapas aane ke baad **pehli** query ka kya hoga, `pool_pre_ping` ke **bina**? (c) DB down thi
`20 s`. Uss dauran ek row `running` thi jiska worker bhi mar gaya. **DB up hone ke baad wo row kab `pending`
hogi, aur kaun karega?**

**Q5.** `/healthz` `SELECT 1` karta hai, usi engine ke pool se, aur pool `pool_size=2` pe hai. Load ke peak pe
dono connections `POST /jobs` ke paas hain.
(a) `/healthz` ka response kya hoga, aur **kitni der** me? (b) Ek orchestrator jo `/healthz` pe liveness probe
lagaya hai — wo kya karega? (c) Iss ek interaction ki wajah se kaunsa **naya** failure mode paida hota hai jo
`/healthz` ke bina exist nahi karta?

---

# Part C — Verification

## C0 — clean tree, opening bench, seal, single head, job `136` ka baseline

```powershell
# 1. Clean tree — aaj ye ASSERT hai, kyunki kal chhe files uncommitted thi
$dirty = git status --porcelain
if ($dirty) { throw "C0: tree dirty, Din 4 ka kaam pehle commit karo:`n$dirty" }

# 2. Single head, aur uska naam
$heads = .\.venv\Scripts\python.exe -m alembic heads 2>&1 | Out-String
if (($heads -split "`n" | Where-Object { $_ -match '\(head\)' }).Count -ne 1) { throw "C0: not a single head" }

# 3. Opening bench — CAPTURE, hardcode nahi. Step 5 isi se compare karega.
$benchSql = @"
select (select count(*) from jobs), (select count(*) from job_executions),
       (select count(*) from side_effects), (select count(*) from outbox),
       (select last_value from side_effects_id_seq), (select last_value from outbox_id_seq),
       (select count(*) from jobs where status='pending'),
       (select count(*) from jobs where status='running'),
       (select version_num from alembic_version)
"@
$script:C0_BENCH = docker exec relay-db-1 psql -U postgres -d relay -At -c $benchSql
"C0 bench: $script:C0_BENCH"

# 4. Job 136 baseline — aaj bhi chhoona nahi hai
$script:C0_136 = docker exec relay-db-1 psql -U postgres -d relay -At -c `
  "select id,status,attempts,claim_generation from jobs where id=136"
if ($script:C0_136 -notmatch '^136\|') { throw "C0: job 136 baseline missing" }

# 5. Frozen seal
$script:FROZEN = (Get-FileHash -Algorithm SHA256 docs/daily/week_04/DIN_05_PREDICTIONS_FROZEN.md).Hash
"C0 frozen: $script:FROZEN"

# 6. Zero Relay processes
if ((Get-Process python* -ErrorAction SilentlyContinue).Count -ne 0) { throw "C0: Relay processes running" }
"C0=pass"
```

## C1 — the two repairs, and each check must be able to fail

**`C1a` — `P-39`, teen arm.** Ek arm se ye pakda nahi jaata; teen se pakda jaata hai.

| Arm | Command | Mechanism maujood | Mechanism ghayab |
|---|---|---|---|
| 1 | `$env:DATABASE_URL` → `W`; `alembic -c <ini→T> upgrade head`; `T` ke tables ginno | `T` migrate hui, **ya** ek naam wala error. Aur `env.py` ne resolved DB + source print kiya | `T` me `0` tables aur exit `0` → repair nahi laga |
| 2 | `$env:DATABASE_URL` **unset**; wahi command | `T` migrate hui | `T` khaali → repair ne `-c` bhi tod diya |
| 3 | `$env:DATABASE_URL` → `W`; `-c` **ke bina** | `W` migrate hui | `relay` migrate hui → **`P-28` dobara khul gaya**, aur ye arm sirf isliye hai |

```powershell
# arm 3 ka assert — aur ye print nahi, throw hai
$evHead = docker exec relay-db-1 psql -U postgres -d relay -At -c "select version_num from alembic_version"
if ($evHead -ne ($script:C0_BENCH -split '\|')[-1]) { throw "C1a arm3: evidence DB migrate ho gayi" }
```

**`C1b` — `P-38`, teen arm, aur pehla arm wahi hai jo kal chala hi nahi.**

| Arm | Order | Expected (fixed) | Broken |
|---|---|---|---|
| 1 | **sink pehle**, phir `upgrade head` | unique constraints on `idempotency_key` = **`1`** | `2` |
| 2 | migration pehle, phir sink | `1` | `1` — **ye arm dono me pass karta hai, isliye akela kaafi nahi** |
| 3 | arm-1 DB pe `head → -1 → head` | round trip, aur `-1` pe constraint count `0` | `-1` pe `1` bacha rehta hai |

```sql
-- arm 1 aur 2 ka count, naam se nahi, COLUMN SET se
select count(*) from pg_constraint c
where c.conrelid = 'sink_deliveries'::regclass and c.contype = 'u'
  and (select array_agg(a.attname order by a.attname)
       from unnest(c.conkey) k join pg_attribute a
         on a.attrelid = c.conrelid and a.attnum = k) = array['idempotency_key'];
```

**`C1c`** — `pytest tests -q` chalao aur output log me `record only, not a regression gate for today's code`
ke saath likho (`P-37`). Isko gate **na** banao.

## C2 — connection budget: ceiling, idle, peak — teen alag number

| Check | Command | Mechanism maujood | Mechanism ghayab |
|---|---|---|---|
| `max_connections` **measured** | `show max_connections;` **aur** `docker-compose.yml` me override ka grep | Ek number + *"compose me override nahi hai"* likha hua | Image default maan liya → denominator assumed hai, measured nahi |
| `application_name` attribution kaam karti hai | `select application_name, count(*) from pg_stat_activity where datname=current_database() group by 1` | Paanch distinct non-empty names | Ek `''` bucket → attribution possible nahi, aur `where application_name=:app` **`0`** dega. `0` ko *"pool override load nahi hua"* **na** padho |
| Idle ≠ ceiling | Paanch process khade, koi kaam nahi; count lo | Observed number, aur uske saath likha hua ceiling — **do alag number** | Ek number → ceiling aur observation ek maan liye |
| Peak | Load ke dauran har `2 s`, ek **series** | Series, aur usme max | Ek reading → peak miss ho sakta hai; release ke baad pool `pool_size` pe wapas aa jaata hai |

## C3 — pool exhaustion: naam wala error, aur uska measured wait

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Pool actually `2` tha | Uss process ke `2` connections peak pe, `3` kabhi nahi — `application_name` se filter karke | `15` dikha → override load hua hi nahi, aur test kuch aur naap raha tha |
| Exhaustion ka **shape** | Error ka **poora naam** + uska module, aur wo **client-side pool** se aaya ya Postgres se — likho | *"Slow ho gaya"* → koi error nahi mila, matlab concurrency pool se kam thi |
| Wait ka number | Measured wait, aur uska `pool_timeout` se comparison | Error mila par wait record nahi hua → `pool_timeout` ka koi evidence nahi |
| **Kis** process ka pool | Teen me se kaun gira — API / worker / dispatcher — naam se | *"Pool exhaust ho gaya"* → per-process event ko global bataya |
| Receiver ka wait (`P-41`) | Holder ke against measured latency, aur uska holder-lifetime se rishta | Ek healthy `POST` ki latency → wo contention naap hi nahi raha |

## C4 — load: direction, aur chaar metrics

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Queue lag ka **direction** | `pending` count ki ek series, aur usme monotonic-badhna ya flat — **shape** | Ek single reading → curve ka shape nahi pata, backpressure ka sawaal unanswered |
| Throughput ka bound **named** | Arithmetic pehle likhi hui, phir measured, aur binding constraint ka **naam** | Ek `jobs/sec` number bina bound ke naam → *"kitna"* pata hai, *"kyun"* nahi |
| Chaar metrics | Chaaron ki query ek jagah, chaaron ka number | Do metrics → roadmap ka observability item adhoora |
| `2.0 s` ka role | Likha hua ki wo **discovery latency** bound karta hai, throughput nahi | `2.0 s` ko throughput divisor ki tarah use kiya → `worker.py` ka loop padha nahi gaya |

## C5 — Postgres-down, `/healthz`, cleanup, aur do assert

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Postgres-down ke **do** failures | Live-break aur stale-pool **alag naam** se, dono ka error text | Ek generic *"connection error"* → dono ek maan liye, aur `pool_pre_ping` ka faisla evidence-free |
| `MAX_ATTEMPTS` iss raaste pe | Likha hua ki DB-down exception `except Exception` me girti hai ya nahi, aur uska nateeja | Chup → `P-36` ka sawaal (bound kis branch me hai) dobara unanswered |
| Contract #1 ka stress | DB down ke dauran ki request ka client-side result + `running` rows ka anjaam | Chup → Din 6 ka Month 1 verdict promise #1 pe `[NO EVIDENCE]` likhega |
| `/healthz` DB **down** pe | Non-`200`, ya ek response jo DB ko `down` **naam se** batata hai | `200` → endpoint process liveness bata raha hai aur usko *health* keh raha hai |
| `/healthz` pool **bhara** hone pe | Response aaya, aur uska matlab *saturated* hai — ya uska timeout **naam se** likha hua | `/healthz` `pool_timeout` pe timeout de raha hai aur usko *"DB down"* bola ja raha hai |

```powershell
# --- cleanup, aur cleanup khud ek measurement hai ---
$probes = docker exec relay-db-1 psql -U postgres -At -c `
  "select count(*) from pg_database where datname like 'relay_%'"
if ([int]$probes -ne 0) { throw "C5: probe DBs bachi hui hain: $probes" }

if ((Get-Process python* -ErrorAction SilentlyContinue).Count -ne 0) { throw "C5: Relay processes zinda" }

$now = (Get-FileHash -Algorithm SHA256 docs/daily/week_04/DIN_05_PREDICTIONS_FROZEN.md).Hash
if ($now -ne $script:FROZEN) { throw "C5: frozen file badal gayi" }

# AAJ KE DO ASSERT — aur ye print nahi hain
$closeBench = docker exec relay-db-1 psql -U postgres -d relay -At -c $benchSql
if ($closeBench -ne $script:C0_BENCH) { throw "C5: evidence DB delta non-zero`nC0:  $script:C0_BENCH`nnow: $closeBench" }

$close136 = docker exec relay-db-1 psql -U postgres -d relay -At -c `
  "select id,status,attempts,claim_generation from jobs where id=136"
if ($close136 -ne $script:C0_136) { throw "C5: job 136 chhoo gaya" }

# aur DOOSRA: relay HEAD pe hona chahiye — kal wo ek revision peeche thi
$evHead = docker exec relay-db-1 psql -U postgres -d relay -At -c "select version_num from alembic_version"
$headName = ((.\.venv\Scripts\python.exe -m alembic heads 2>&1 | Out-String) -split '\s+')[0]
if ($evHead -ne $headName) { throw "C5: evidence DB head pe nahi hai ($evHead vs $headName)" }
"C5=pass"
```

**Note, aur ye kal ki wording ka fix hai:** ye check *"delta strictly `0`"* nahi hai — ye **nau asserted
counters** pe `0` hai. `sink_deliveries` jaan-boojh ke frozen set se bahar hai un dino jab receiver ka schema
badalta hai. Log me wahi likho jo assert hua.

---

# Part D — Scope guard: aaj **nahi**

| Kya | Owner | Aaj karne se kya khota hai |
|---|---|---|
| **Dispatcher ka backoff aur bound** (`next_attempt_at` on `outbox`, outbox DLQ) | **Month 2**, `Cost` line Din 6 pe | `P-35` ke do measured numbers (`8` attempts / `~20 s`, `7/7` vs `0`) `D-27` ke `Cost` ka input hain. Aaj fix karne se wo `Cost` ek imaginary number pe likha jaayega |
| **`MAX_ATTEMPTS` ko claim gate me daalna** | **Month 2**; Week 2 Din 6 ne ise price kiya aur declined kiya | Paanchvaan `status` writer, aur uske saath ek sweep chahiye. `P-36` ka point ye hai ki bound ka *location* galat hai — usko aaj hilana Din 6 ka argument chura lena hai |
| **`SINK_DEDUP=0` arm ko *"negative control"* ki tarah chalana** | `D-27` `Cost`, Din 6 | Wo ab `500` deta hai, `2` rows nahi (`P-40`). Usko control kehna ek **jhoota** differential likhna hai. Chalana ho to `except IntegrityError` + naam wala `409` pehle, aur wo aaj ka kaam nahi |
| **Receiver pe `lock_timeout` / `statement_timeout` add karna** | Month 2, `Cost` Din 6 | `P-41` ka wait aaj ek **measurement** hai. Bound aaj lagane se number wo bound naapega, mechanism nahi |
| **Body-hash / `409 conflicting_payload` receiver pe** | `D-27` ki ek line, Din 6 | `P-42` ek contract statement hai, bug nahi. Aaj code badalna Din 6 ka invariant likhne se pehle usko implement kar dena hai |
| **Test coverage service modules pe** | **Month 2**; README ki ek line Din 6 pe | `P-37` asli hai aur aaj ka budget `135 min` hai. Ek test layer aaj likhna do measured failure mode (pool, Postgres-down) ke badle coverage kharidna hai — aur wo do README ke failure matrix me jaate hain |
| Job `136` ko haath se terminal karna | **kabhi nahi** | `P-05`. Wo Din 6 ke close pe ek naam wali carried row hai, mechanism `P-36` me likha hai |
| `LISTEN`/`NOTIFY`, leader election, dispatcher coordination | `D-29` me **likha** jaata hai, banaya nahi | Aaj ka pool number `D-29` ka `Rejected` (*"Redis/etcd lease"*) price karta hai. Banane se wo comparison khatam |
| Metrics endpoint / Prometheus | **kabhi nahi, Month 1 me** | Aaj chaar metrics **SQL se** aati hain, aur wahi `D-28` ka reason hai — ek endpoint likhne se `D-28` ka argument hi gayab |
| Redis | Sirf **padha** jaata hai, `D-29` ke liye | Aaj ka reading (persistence RDB vs AOF, eviction) `D-29` ka `Rejected` bharta hai. Install karna scope creep hai |
| `job_executions` pe index / FK | **Aaj sirf tab**, jab load ke numbers usko measurable banayen (`EXPLAIN ANALYZE` before/after); warna Month 2 | Bina before/after ke ek index *"lagta hai tez hoga"* hai, measurement nahi |
| Retention / partitioning | Month 2 | `P-05` ki gap list aur `job_executions` ka growth aaj **evidence** hain. Aaj tidy karna `P-05` ka ulta hai |
| Lease `30 s`, heartbeat `10 s`, poll `2.0 s`, backoff numbers, `MAX_ATTEMPTS`, `effect_key` badalna | **kabhi nahi, iss hafte** | Week 2–4 ke saare measurements inhi numbers pe khade hain. Aaj `pool` aur `echo` hi wo do variable hain jo hil sakte hain, aur wo bhi ek-ek |
| `DDIA_CH8_LINKS.md` lines 10–13 | **Din 6** | Chautha carry. Aaj reading DDIA Ch 9 skim + Redis persistence hai, aur wo `D-29` se bandhi hai |
| README, blog post, `D-26`–`D-29` ki entries | **Din 6**, aur Din 6 kaata nahi ja sakta | Aaj ke numbers `D-28` aur `D-29` ko **feed** karte hain. Entry aaj likhna Din 6 se uska sabse bada input chura lena hai |
