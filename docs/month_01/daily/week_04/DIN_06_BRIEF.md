Log: [`../../logs/WEEK_04.md`](../../logs/WEEK_04.md) · Sealed: [`DIN_06_KEY.md`](DIN_06_KEY.md) ·
Kal: [`DIN_05_BRIEF.md`](DIN_05_BRIEF.md)

**Goal:** Month 1 band karo. Chaar decisions publish karo, chain jodo, aur wo **do artifacts** banao jo resume
pe jaate hain. **Aaj `src/` me ek line bhi nahi badalti.**

**Architectural invariant (aaj ke baad):**
> Month 1 ka har contract promise ek verdict ke saath likha hua hai — **`protected`** / **`narrowed`** /
> **`[NO EVIDENCE]`** — aur har verdict ke peeche **ek job id ya ek measured number** hai. `protected` ke saath
> uska **scope** likha hua hai, warna wo overclaim hai.

**Deliverable:** `D-26`–`D-29` (+ paanch amendments) · `README.md` · blog post · `WEEK_04_HANDOFF.md` with the
Month 1 verdict table · `LEARNING_LOG.md` · `MAP.md` · `POSTMORTEMS.md` · `CURRENT_WEEK.md` ka full rewrite ·
aur Month 1 close ka DoD audit.

**Budget:** `15 + 30 + 55 + 40 + 35 + 25 = 200 min`. Plan me `185` tha; Step 0 (`+15`) freeze aur do gate ke
liye add hua hai, aur wo `D-` collision check ke liye load-bearing hai — wo collision **do baar** ho chuki hai.

**Cut order — aur aaj ye ulti hai.** Poora din *"not cuttable"* hai, par uske andar bhi ek order hai:
**Step 1 (chain) aur Step 5 (verdict + DoD) kabhi nahi kat sakte** — wo Month 1 ka poora evidence hain.
Uske baad `D-26`–`D-29` **kabhi nahi** (numbers reserved hain aur chaar din ka `Faisla` input unpe khada hai) →
README ka **failure matrix** rakhna → README ka *"Numbers"* section **trim** kar sakte ho traceable subset pe →
**blog post kaat sakte ho**, aur kaate to wo ek `owner` ke saath likha jaata hai, *"kal likhoonga"* nahi.
Reason: blog ek **publishing** artifact hai; baaki sab **evidence** hai. **Adhoora evidence adhoore blog se
bura hai.**

---

## Rules — ye chhe roz wahi hain

> **Paste rule:** Part A, Part C, Part D Gemini ko ja sakte hain. **Part B kabhi nahi. KEY kabhi nahi.**
>
> **Seal rule:** paanchon answers **Step 0 me** freeze honge, Step 1 shuru hone se pehle. Har KEY section tabhi
> khulta hai jab uss step ka **kaam** ho chuka ho. Aaj *"measurement"* ka matlab thoda alag hai — aaj zyada kaam
> likhna hai, naapna nahi — to rule ye hai: **KEY ka section tabhi khulta hai jab uss step ka deliverable
> draft ho chuka ho.** Q1 chain ke baad, Q2/Q3 verdict table ke baad, Q4 `D-29` ke baad, Q5 failure matrix ke
> baad.
>
> **Provenance rule:** iss BRIEF ke saare numbers `[MEASURED-R 2026-09-10]` hain — Din 5 ke closeout review me
> actually chalaye gaye, evidence DB `relay` pe read-only. Jo tum chalao wo `[MEASURED]`.
>
> **Aaj ka apna rule, aur ye sabse zaroori hai:** aaj **koi naya measurement nahi** hai. To har number ka
> **source** likhna hai — job id, log line, ya din. Ek bhi number bina source README me ja gaya, to wo blog me
> bhi jaayega aur interview me poocha jaayega. Aur teen numbers pe `[REPORTED, NOT VERIFIABLE]` likhna hai,
> chhupana nahi (`P-45`).
>
> **Scoring rule, teesri baar:** score sirf `DIN_06_PREDICTIONS_FROZEN.md` ke text ka hota hai. Kal scoring
> table me frozen answer ko **paraphrase** kar diya gaya tha aur wo teen jagah upar ki taraf tha — Q2 pe wo
> `0.25` ka overcredit bana. **Aaj scoring table me frozen answer `quote` hoga, summarise nahi.**

### Read order — isko literally follow karo

1. Sirf **Step 0** padho (`0A`–`0C`).
2. Editor outline se seedha **Part B** pe jao. Step 1–5 aur Part C abhi mat kholo.
3. Paanch predictions likho (`idk` valid hai aur `0` score karta hai), phir Step 0 ke seal command pe wapas aao.
4. Frozen hash print hone ke baad **C0** kholo. C0 pass ho tab baaki sab khulta hai.

### Kal jo sach nikla — saat cheezein aaj ka kaam badalti hain

`[MEASURED-R 2026-09-10, Din 5 closeout review]`. Ye **prediction ke jawab nahi** hain; ye aaj ke maidan ki
shape hain, aur inhe na jaanne se aaj ka verdict jhoota ho jaayega.

| Kya | Actual | Aaj ka asar |
|---|---|---|
| **Worker DB outage me mara, zinda nahi raha** | `logs/w4d5_step5_worker.stderr.log` ka outermost frame `worker.py:321 asyncio.run(run_worker())` → `worker.py:185 await session.execute(claim_query)`. `except Exception` **sirf** handler execution wrap karta hai; claim aur terminal-mark unguarded hain. `src/reaper.py` bhi wahi shape. stdout `15:22:16.128` pe khatam, dobara shuru nahi hoti | **Step 5.** Promise #4 (*crashes recoverable*) `protected` **nahi** ho sakta. Row-level `narrowed`, process-level `[NO EVIDENCE]`. Aur README ke failure matrix me ek naya row hai (`P-43`) |
| **Reaper ka `7.9 s` ek artifact hai** | Reaper ki pehli engine line (`select pg_catalog.version()`) `15:22:46.428` pe — process **DB waapas aane ke baad** launch hua, reclaim uske pehle poll pe `63 ms` baad. Agar wo outage me chal raha hota to worker ke saath marta aur job `1` ko koi reclaim nahi karta. **Relay me koi supervisor nahi hai** | **Step 3 + Step 5.** Failure matrix ke *"Postgres beech me down"* row ka Recovery cell *"reaper reclaims"* **nahi** likh sakta. Wo *"reaper reclaims — jab reaper zinda ho; iss run me usko haath se start kiya gaya"* hai |
| **`sink_deliveries` `10` se `7` ho gaya** | `cb17c36` ne `w4d4_sink_unique` ke `upgrade()` me ek unguarded `DELETE … USING` daala aur wo `relay` pe chali. Bache ids `1,2,4,6,7,8,9`; gaye `3,5,10`; sequence abhi bhi `10`. Delta gate isko dekh **nahi** sakta tha kyunki `sink_deliveries` frozen set se bahar hai | **Step 1.** Chain ka `sink_deliveries` bucket **`-3`** ke bina join **nahi** karega. Ye Q1 ka asli subject hai (`P-46`) |
| **Teen headline numbers ka koi artifact nahi** | `logs/w4d5_step2*` aur `w4d5_step3*` maujood nahi, koi probe script bhi nahi. To pool timeout `3.0055 s`, `P-41` ka `2.8133 s` vs `0.4703 s`, aur `/healthz` ka `3.1618 s` repo se dobara nahi nikalte. Aur `DIN_05_DESIGN.md` Faisla 3 `step4_load_probe.py` ko `Chosen` likhta hai — **wo file tree me nahi hai** | **Step 3 + Step 5.** README ke *"Numbers"* section me ye teen `[REPORTED, NOT VERIFIABLE]` label ke saath jaate hain. `requirements.txt` me **koi version pinned nahi hai** — DoD ka item `slipped` hai (`P-45`) |
| **Drain rate reproducible hai, aur wo aaj ka sabse strong number hai** | `186` marks, first claim `15:11:37.299` → last mark `15:12:03.690` = `26.391 s` → **`7.01 jobs/s`**, per-job **`0.1427 s`**. Engine handshake include karo to `6.53 jobs/s`. `186 + 214 = 400` closes. `0` empty-queue polls during backlog | **Step 3 + Step 4.** Ye README aur blog dono me ja sakta hai **bina** hedge ke. Binding constraint **handler duration** hai (`0.1 s` of `0.1427 s`), `echo=True` `~11 ms` = `~8%` — Faisla 1 ka `Cost` isko ulta likhta hai aur wo `D-28` me theek hona chahiye |
| **Connection headroom `~3-5` hai, `22` nahi** | Log kehta hai `97 − 75 = 22 comfortable`. Wo load script ka apna engine (`+15` tak) aur `psql`/`docker exec` sessions (`+2-4`) chhod deta hai. Poori ginti `~92-94` against `97` | **Step 2 (`D-28`) + Step 3.** `narrow` likho. Aur *"comfortable single-digit/double-digit buffer"* apne aap me contradiction hai — wo phrase copy nahi karni |
| **`MAX_ATTEMPTS` ka DB-outage sawaal aaj bhi unmeasured hai** | `attempts` **claim ki `UPDATE`** me increment hota hai, `except` block me nahi — wo sirf `current_attempts` padhta hai. Outage ke waqt koi job handler me nahi thi. To: claim-time outage ka cost **`0`**; handler-time outage ka cost **`2` attempts** (claim ka committed increment + reaper reclaim ke baad ka dobara increment); post-handler-pre-mark outage me upar se ek **duplicate execution**. Sirf pehla case chala | **Step 2 (`D-26`/`D-27` ka `Cost`).** Teeno case alag likho, ek line me nahi. Aur case 2 aur 3 pe `[NOT TESTED]` likhna hai |

### Aur do vocabulary cheezein, taaki Situation 1 ke liye KEY na kholni pade

**Terms used today** — ye *"cheez kya hai"* batata hai, *"kya hoga"* nahi:

- **reconcile chain** — ek arithmetic table: week ka opening count `+` har din ka recorded delta `=` expected
  closing count, aur uske neeche aaj ka **actual** count. Do numbers match karein to chain *"judi"* hai.
- **compensating errors** — do galtiyan jo ulti direction me hain aur total me cancel ho jaati hain, to
  aggregate sahi dikhta hai aur dono galtiyan chhup jaati hain. Isi liye chain per-line check hoti hai, total pe
  nahi.
- **`protected` / `narrowed` / `[NO EVIDENCE]`** — ek promise ka verdict. `protected` = *"tested failures ke
  against hold karta hai"*. `narrowed` = *"window chhota hua, band nahi hua"*. `[NO EVIDENCE]` = *"iss hafte
  test nahi hua"* — aur ye *"toota hua"* se **alag** hai.
- **liveness vs readiness** — *"process zinda hai"* (nahi hai to restart karo) versus *"traffic le sakta hai"*
  (nahi le sakta to traffic hatao). Do alag remediation.
- **advisory lock** — Postgres ka ek application-level lock (`pg_advisory_lock` / `pg_try_advisory_lock`) jo
  kisi row ya table se juda nahi hota; ek number pe lock lagta hai aur wo session ya transaction tak rehta hai.
  Iska koi built-in expiry nahi hai.
- **fencing token** — ek monotonically badhne wala number jo *"ye claim kaunsi hai"* identify karta hai, taaki
  ek purana writer apna kaam commit na kar sake. Relay me wo `jobs.claim_generation` hai.
- **DoD audit** — Definition of Done ki list pe line-by-line pass, jisme har untick ke saath **ek** line hoti
  hai: `deliberately deferred` (owner ke saath) **ya** `slipped` (kya specifically chahiye). Do me se ek, dono
  nahi, koi nahi bhi nahi.
- **`[REPORTED, NOT VERIFIABLE]`** — number likha gaya tha, mechanism plausible hai, aur uska artifact repo me
  nahi bacha, to wo dobara nikala nahi ja sakta. Ye *"galat"* nahi hai aur *"measured"* bhi nahi hai.

---

# Part A — Steps

## Step 0 — 15 min: commit, freeze, aur do gate jo aaj print nahi hain

### 0A — tree saaf hai, aur aaj wo ek assert hai

Kal ke close pe tree clean tha. Aaj **koi `src/` change nahi** hona chahiye, aur wo C0 aur C6 dono pe assert
hota hai. Agar kuch uncommitted hai to pehle commit karo, warna aaj ka *"`src/` untouched"* gate kuch prove
nahi karta.

### 0B — `D-` collision grep, aur ye **print nahi, `throw`** hai

`D-26`–`D-29` **aaj pehli baar** likhe jaayenge. Collision do baar ho chuki hai (`D-09` roadmap Part 2 me
reserved tha; `P-07` do baar claim hua). To likhne se **pehle** grep karo aur zero match assert karo. Command
C0 me hai.

### 0C — predictions freeze karo

`DIN_06_ANSWERS.md` banao (kal ke template ki shape me: `## Q1`–`## Q5`, har ek me `### Prediction`,
`### Observed + meri explanation`, `### After KEY`), sirf `### Prediction` bharo, aur freeze karo. Seal command
baaki do headings ke non-empty hone pe `throw` karta hai.

**Aaj ke paanch sawaal iss hafte ke apne evidence pe hain, kisi library ke behaviour pe nahi.** Wo jaan-boojh ke
hai: kal `9` sub-answers me `6` pe `idk` tha aur unme se teen ka jawab **source padhne** se milta tha. Aaj `idk`
ka matlab alag hai — wo *"maine apne hi hafte ka evidence nahi padha"* kehta hai. **Phir bhi `idk` likhna guess
se behtar hai.**

## Step 1 — 30 min: reconcile chain, aur ek bucket jo join nahi karega

### 1A — arithmetic pehle, query baad me (15 min)

Table banao **recorded deltas se**, aaj ke count se nahi. Line-by-line, aur har line ka **source** naam se:

| Line | Kahan se |
|---|---|
| Week 4 opening | Week 3 close ka BENCH: `119` jobs · `107` executions · `9` effects |
| `+` drain-run delta (Din 1 Step 0) | **alag line** — Din 1 ke experiment delta se juda hua nahi |
| `+` Din 1..Din 5 ka har din ka delta | har din ka `group by`, report ki gin-ti se **nahi** |
| `+` naye bucket | `outbox` rows · `sink_deliveries` rows (dono Din 3 se) |
| `=` expected closing | arithmetic |
| Din 5 ka delta | **`0` expected on the eight asserted counters** — aur `sink_deliveries` pe **nahi** |
| Chain judi? | `[MEASURED]` ya cause ke saath |

**Aur ek line jo pehle se maloom hai aur usko chhupana nahi hai:** `sink_deliveries` Din 3/Din 4 close pe `10`
tha aur aaj `7` hai. Delta **`-3`**, cause `cb17c36` ka `DELETE … USING` (`P-46`). Wo `-3` chain me **naam se**
likho, warna do cheezon me se ek hoga: chain tootegi, ya wo kisi doosri galti ke saath cancel ho jaayegi.

### 1B — aaj ke actual counts, aur unka shape (15 min)

Paanchon status buckets `+` total, `+` `running`/`pending` at close **ids ke saath** (zero ho ya na ho, dono
likhe jaate hain), `+` sequences aur naye gaps, `+` yeh:

```sql
select job_id, count(*) from side_effects group by 1 having count(*) > 1;
```

Har row ke aage **`expected` ya `unexpected`** naam se. Aur `sink_deliveries` ke `id` gaps (`3, 5, 10`) ko
`P-46` ke saath link karo — wo `P-05` ke gap list se **alag** cheez hai aur unhe ek nahi likhna.

## Step 2 — 55 min: `D-26` · `D-27` · `D-28` · `D-29`, aur paanch amendments

Format wahi jo `DECISIONS.md` me chal raha hai. **`Rejected` field khaali nahi rehta** (`AGENTS` rule 28).

### 2A — `D-26` (14 min): `jobs.claim_generation`

Ek monotonic epoch, kyunki `status` **cycle** karta hai (`running → pending → running` reclaim se reachable) aur
compare-and-set generation-blind hai.

- **Rejected jo maarne hain:** `claimed_at` ko hi token maan lena (heartbeat usko badalta hai, to wo identity
  nahi hai) · per-claim `uuid` (monotonic nahi, to *"naya kaun hai"* compare nahi hota).
- **`Cost` me aaj jo naya jaata hai:** `MAX_ATTEMPTS` ka bound `except Exception` me **evaluate** hota hai par
  `attempts` ka **increment** claim ki `UPDATE` me hai — aur iss farq se DB outage ka cost teen alag numbers hai
  (`0` / `2` attempts / `2` attempts + ek duplicate execution). Case 1 `[MEASURED]`, case 2-3 `[NOT TESTED]`.

### 2B — `D-27` (14 min): transactional outbox

Intent effect ke saath atomic, delivery **at-least-once**, exactly-once **receiver ka kaam**.

- **Rejected:** handler ke andar seedha HTTP call (`crash-before-commit` → effect do baar; `commit-before-effect`
  → effect zero) · 2PC/XA (Postgres prepared transactions + ek HTTP endpoint pe — operational cost aur orphaned
  prepared transaction ka blast radius).
- **`Cost` me chaar line, aur teen already measured hain:** `P-35` (dispatcher pe koi delay term aur koi bound
  nahi) · `P-40` (`UNIQUE` ne apna hi negative control maar diya) · `P-41` (`ON CONFLICT DO NOTHING` **wait**
  karta hai, `SKIP LOCKED` nahi — `[REPORTED, NOT VERIFIABLE]`) · `P-42` (delivery identity ka koi likha hua
  invariant nahi; `src/dispatcher.py` `f"job:{job_id}"` minta hai, ek key per **job**).
- **Aur ek line jo aaj add hui:** receiver ka dedup fix uss problem ka **evidence kha gaya** jise wo fix kar
  raha tha (`P-46`).

### 2C — `D-28` (14 min): observability — kya naapa **aur kya expose nahi kiya**

`completed_at`-derived latency · SQL-side queue depth · `/healthz` **liveness-only**.

- **Rejected:** `/metrics` ya `/stats` endpoint jo counts deta hai (auth nahi hai — `D-03` ka enumeration
  argument, aur `pending` count business volume hai) · Prometheus/Grafana stack (Month 1 ke aakhri hafte me ek
  naya dependency, aur usko padhne wala aaj ek insaan hai).
- **`/healthz` ke saath wo likho jo wo *nahi* bata raha:** worker liveness (heartbeat sirf job ke dauran chalta
  hai, `P-21`, to idle worker *"dead"* dikhega) · dispatcher liveness · queue backlog · **aur khud ki pool
  saturation**, kyunki wo usi pool se peeta hai.
- **Teen corrections jo `DIN_05_DESIGN.md` se aati hain aur yahan theek honi hain:** headroom `~3-5` hai `22`
  nahi · binding constraint **handler duration** hai `echo=True` nahi (`0.1 s` of `0.1427 s`; echo `~8%`) ·
  aur Faisla 4 ka `pool_pre_ping` argument ka **premise jhoota** hai (worker/reaper me *"built-in exception
  handling"* nahi hai — `P-43`), to us faisle ko yahan **dobara** likhna hai: order pehle exception boundary,
  phir `pool_pre_ping` ki keemat.
- **Aur endpoint inventory:** `/health` · `/healthz` · `/db-ping` teen hain aur aakhri do duplicate hain; aur
  `/slow-hold` production module me hai, unauthenticated, unbounded (`P-44`). Kaunse zinda rehte hain, wo ek
  line me likho.

### 2D — `D-29` + amendments (13 min): leader election **nahi** kiya

Ek reaper, aur uska tradeoff naam se.

- **Rejected:** Raft/etcd/Consul lease (poora naya failure domain) · **Postgres advisory lock se leader — ye
  sabse strong hai** aur isko theek se maarna padega, kyunki wo already available hai aur zero naye dependency
  maangta hai.
- **Aur yahan honesty ka test hai.** `D-29` ka `Rejected` advisory lock ko *"single-reaper ke Din 5 numbers se"*
  **nahi** maar sakta, kyunki wo numbers nahi liye gaye: reaper outage me chal hi nahi raha tha aur do-reaper ka
  koi run nahi hua. Likho jo sach hai. (Q4 exactly yahi poochta hai — wo answer karne se **pehle** freeze ho
  chuka hoga.)

**Paanch amendments — naye entries nahi, purane entries pe amendment blocks:**

| Entry | Kya badalta hai |
|---|---|
| `D-06` | compare-and-set ab generation-aware hai; original entry ka *"transitions are enforced by compare-and-set"* ab adhoora hai |
| `D-21` | `job_executions` pe `claim_generation` aa gaya (`P-11` slipped debt), aur purani `107` rows honest `NULL` hain |
| `D-22` | Cost 7 (fencing) aur Cost 10 (`completed_at`) ab **built** hain; Cost 8 (shutdown-vs-lease run) ab **measured** hai |
| `D-23` | `last_error` aa gaya; `dead_letter` ab verdict **aur** ek diagnosis carry karta hai |
| `D-25` | `effect_key` ka generation ke saath rishta (Din 1 Faisla 3) aur delivery ke saath rishta (Din 3 Step 3) ab likha hua hai |

## Step 3 — 40 min: `README.md` — **ye artifact hai, documentation nahi**

### 3A — problem statement + architecture diagram (15 min)

**Problem statement, do paragraph.** *"Job queue banaya"* **nahi**; **kaunsi guarantee, kaunse failure ke
against.** Paanch contract promises yahan hain.

**Architecture diagram** — ASCII ya Mermaid, aur usme **paanch process** dikhne chahiye (API, worker × 2,
reaper, dispatcher, receiver) plus **chaar table** (`jobs`, `job_executions`, `side_effects`, `outbox`) aur
receiver ki `sink_deliveries`. **Diagram me transaction boundaries dikhni chahiye** — wahi iss project ka poora
point hai aur wahi ek generic queue diagram me nahi hota.

### 3B — failure matrix (15 min) — **README ka sabse valuable hissa**

| Crash point | State turant baad | Recovery mechanism | Evidence |
|---|---|---|---|
| post-flush pre-commit | … | … | job id / number |
| post-commit pre-mark | … | … | … |
| handler `>` lease, worker zinda | … | … | job `95`, `14.783 s` |
| mark after reclaim (stale writer) | … | `claim_generation` fence | Din 1 / Din 4 ka `rowcount = 0` |
| delivery ke baad dispatcher crash | … | receiver dedup | Din 3 ke do numbers |
| Postgres beech me down, **worker idle-polling** | … | … | Din 5 |
| Postgres beech me down, **worker mid-handler** | … | … | ? |
| Postgres down, **worker aur reaper dono mare** | … | … | ? |

**Har row me ek evidence cell hai. Khaali cell allowed nahi — `[NO EVIDENCE]` likha jaata hai.** Aakhri do row
jaan-boojh ke add ki gayi hain; Q5 unhi ke baare me hai.

### 3C — numbers + links (10 min)

`14.783 s` overlap · `attempts = 4` overdraft · effect count `1` vs delivery count `2` · Din 5 ka
**`7.01 jobs/s`** aur `0.1427 s` per job · Hypothesis examples ka count. **Har number ke saath uska `n` aur
uski condition.** Aur teen numbers pe `[REPORTED, NOT VERIFIABLE]` (`P-45`).

`DECISIONS.md` **aur** `PROBLEMS.md` dono ka link — `45`+ named problems ek asli artifact hai.

**Aur ek cheez README me nahi jaani chahiye:** *"production-ready"*, *"scalable"*, *"robust"*. Iss project ki
poori value **honest scoping** me hai. `narrows` · `bounds` · `under the failures tested` — yahi vocabulary hai.

## Step 4 — 35 min: blog post

Title: *"Building a durable job queue on Postgres: what breaks and why"*.

Shape jo evidence se seedha aata hai, aur jo generic tutorial se ulta hai: **har section ek failure se shuru
hota hai, feature se nahi.**

| Section | Kya hai |
|---|---|
| Hook | `SELECT … FOR UPDATE SKIP LOCKED` sahi tha, har compare-and-set sahi tha, aur **phir bhi** ek job do baar chali — `14.783 s` overlap ke saath. **Lease wo guess thi jo galat thi** |
| 1 | Claim: `SKIP LOCKED` + CAS, aur `rowcount` padhna kyu zaroori hai |
| 2 | Lease aur heartbeat: `P-21` — *heartbeat ki usefulness uss failure ki severity ke ulta proportional hai jise lease pakadne aaya tha* |
| 3 | Bounded retry: `MAX_ATTEMPTS` **scheduling** bound karta hai, dispatches nahi — `attempts = 4` |
| 4 | Idempotency do layer me: enqueue vs execute, aur dono alag failure domain |
| 5 | `UNIQUE` + `ON CONFLICT DO NOTHING`: conflict ko exception se `rowcount = 0` me badalna |
| 6 | Fencing: `status` cycle karta hai, epoch nahi |
| 7 | Outbox: intent atomic, delivery at-least-once, aur exactly-once **receiver ka kaam** hai |
| Close | Kya **abhi bhi** khula hai — aur ye section post ka sabse valuable hissa hai |

**Ek rule blog ke liye:** har claim ke saath ya ek number hai, ya ek *"ye maine measure nahi kiya"*.

**Aur ek line jo Close section me jaani chahiye, kyunki wo sabse honest hai:** worker ek DB restart se mar jaata
hai aur usko koi wapas nahi laata (`P-43`) — matlab *"crashes are recoverable"* **row** ka sach hai, **process**
ka nahi.

## Step 5 — 25 min: handoff, Month 1 verdict, DoD audit

`docs/daily/WEEK_04_HANDOFF.md` — wahi teen headings, **pehli do word-for-word** `WEEK_01`/`02`/`03` jaisi:
*What Stuck* · *What Needs Reinforcement* · *What Month 2 Must Not Assume*.

**Month 1 ka verdict table:**

| # | Promise | Verdict | Evidence |
|---|---|---|---|
| 1 | accepted job never silently lost | ? | Din 5 ka Postgres-down + `202` ka semantics |
| 2 | duplicate execution ≠ duplicate side effect | ? | local: Week 3 + Din 4 · external: Din 3 ka receiver-dependent claim |
| 3 | retries bounded | ? | `D-23` + `P-27` ka overdraft |
| 4 | crashes recoverable | ? | Din 4 ke chaar interleavings, **aur `P-43`** |
| 5 | terminal failures → DLQ | ? | `dead_letter` + `last_error` |

**`?` ki jagah sirf teen shabd allowed hain: `protected` / `narrowed` / `[NO EVIDENCE]`.** Aur `protected` ke
saath uska **scope** likhna zaroori hai — *"tested failures ke against"* — warna wo overclaim hai.

**DoD audit:** har untick pe **ek** line — `deliberately deferred` (owner ke saath) **ya** `slipped` (kya
specifically chahiye). Iss hafte ke carried debts jo audit me naam se aane chahiye: Week 2 ke `💡`/`🧠`
sections · paanch Week 2 answers · `DDIA_CH8_LINKS.md` lines 10–13 · Week 1 Din 7 ka log · `P-29` ka
raw-evidence retention · **`requirements.txt` me zero pinned versions** · **Step 2/3 ke missing artifacts**
(`P-45`).

---

# Part B — PREDICTION QUESTIONS

> **Ye block Gemini ko kabhi nahi jaata.** Answers `DIN_06_ANSWERS.md` me Step 0C pe likhe jaate hain, aur wahan
> se `DIN_06_PREDICTIONS_FROZEN.md` freeze hoti hai. **`idk` ek valid likha hua answer hai aur wo `0` score
> karta hai — guess dressed as knowledge se behtar hai.**
>
> **Aaj ke sawaal iss hafte ke apne evidence pe hain.** Koi library behaviour nahi, koi naya mechanism nahi.
> Har jawab tumhare hi paanch din ke logs, `PROBLEMS.md`, aur `DECISIONS.md` me maujood hai. **Mechanism
> likho** — kaunsa job id, kaunsa number, kaunsa problem card.

## Q1 — reconcile chain aur uska `0`

Din 5 ka delta **`0` expected** hai kyunki poora din disposable DBs pe chala.
(a) Agar wo `0` **nahi** nikla, to sabse likely cause kya hai — aur usko `git` / `psql` se **exactly** kaise
pakdoge? Ek command likho.
(b) Chain ke **kaunse bucket** pe `0` expect karna hi **galat** hai, aur kyun?
(c) Chain ka **total** match kar jaaye par ek line galat ho — ye kaise possible hai, aur uska naam kya hai?

## Q2 — promise #2 ka verdict

Promise #2: *duplicate execution ≠ duplicate side effect*.
(a) Verdict kya hoga — `protected`, `narrowed`, ya `[NO EVIDENCE]`?
(b) Uska **scope statement** exactly kya hoga? Ek vaakya likho jo overclaim **na** ho.
(c) **Local** effect aur **external** delivery ka verdict **ek** hai ya **alag**? Agar alag, to dono likho.

## Q3 — promise #1 ka verdict, aur ek untested failure

Promise #1: *accepted job is never silently lost*.
(a) Din 5 ka Postgres-down run isko `protected` banata hai ya nahi? Aur `202` ka semantics iss jawab me kaise
aata hai?
(b) **Ek failure naam se likho** jo isko todta hai aur jo **iss hafte test nahi hua**.
(c) Ek job jo `running` thi aur DB down thi — uske `pending` hone ka **bound** kya hai? Bound likho, ek number
nahi.

## Q4 — `D-29` ka sabse strong rejected alternative

`D-29` = leader election **nahi** kiya. Uska strongest rejected alternative Postgres **advisory lock** hai.
(a) Usko honestly maarne ke liye **kaunsa Din 5 ka number** chahiye tha?
(b) Wo number aaj maujood hai ya nahi?
(c) Agar nahi hai, to `D-29` ka `Rejected` field **exactly** kya kehna chahiye? Ek vaakya likho.

## Q5 — failure matrix ka `[NO EVIDENCE]` row

README ke failure matrix me har row ka evidence cell bharna hai.
(a) **Kaunsi row** aisi hogi jiska evidence cell `[NO EVIDENCE]` likhna padega? Naam se likho.
(b) Uss row ka **Recovery mechanism** cell kya kehta hai — aur wo cell `[NO EVIDENCE]` hone ke baad bhi bhara
ja sakta hai ya nahi?
(c) Agar tumhe lagta hai ki koi row `[NO EVIDENCE]` **nahi** hogi, wo bhi likho — aur Step 3B pe check karo.

---

# Part C — Verification

## C0 — clean tree, `src/` baseline, `D-` collision, seal

```powershell
# 1. Clean tree — aaj ye ASSERT hai
$dirty = git status --porcelain
if ($dirty) { throw "C0: tree dirty, pehle commit karo:`n$dirty" }

# 2. src/ ka baseline SHA — C6 isse compare karega
$script:C0_SRC = (git rev-parse HEAD:src)
"C0 src tree: $script:C0_SRC"

# 3. D-26..D-29 free hain — aur ye print nahi, THROW hai (collision do baar ho chuki hai)
$dhit = Select-String -Path docs\DECISIONS.md -Pattern '^## D-2[6-9]'
if ($dhit) { throw "C0: D-26..D-29 collision, pehle se maujood:`n$($dhit.Line -join "`n")" }
# P-46 Din 5 ke review me likhi ja chuki hai, to next free P-47 hai
$phit = Select-String -Path docs\PROBLEMS.md -Pattern '^## P-4[7-9]'
if ($phit) { throw "C0: P-47+ collision:`n$($phit.Line -join "`n")" }
"C0 numbering: D-26..D-29 free, P-47 free"

# 4. Opening bench — CAPTURE, hardcode nahi. Aaj sink_deliveries BENCH me HAI.
$benchSql = @"
select (select count(*) from jobs), (select count(*) from job_executions),
       (select count(*) from side_effects), (select count(*) from outbox),
       (select count(*) from sink_deliveries),
       (select last_value from side_effects_id_seq), (select last_value from outbox_id_seq),
       (select count(*) from jobs where status='pending'),
       (select count(*) from jobs where status='running')
"@
$script:C0_BENCH = docker exec relay-db-1 psql -U postgres -d relay -At -c $benchSql
"C0 bench (9 data counters, NO revision column): $script:C0_BENCH"

# 5. Revision ALAG se — kal ka gate isi ko ek hi string me mila ke unsatisfiable ho gaya tha (P-31)
$script:C0_REV = docker exec relay-db-1 psql -U postgres -d relay -At -c "select version_num from alembic_version"
"C0 revision: $script:C0_REV"

# 6. Job 136 baseline
$script:C0_136 = docker exec relay-db-1 psql -U postgres -d relay -At -c `
  "select id,status,attempts,claim_generation from jobs where id=136"
if ($script:C0_136 -notmatch '^136\|') { throw "C0: job 136 baseline missing" }

# 7. Frozen seal
$script:FROZEN = (Get-FileHash -Algorithm SHA256 docs/daily/week_04/DIN_06_PREDICTIONS_FROZEN.md).Hash
"C0 frozen: $script:FROZEN"

# 8. Zero Relay processes
if ((Get-Process python,python3,pythonw -ErrorAction SilentlyContinue).Count -ne 0) { throw "C0: Relay processes running" }
"C0=pass"
```

**Kal ki galti jo aaj repeat nahi ho rahi:** bench se `alembic_version` **nikal diya** gaya hai aur wo apni
alag variable me hai. Kal wo nauve column ki tarah bench me tha aur usi din wo revision **badalna** tha, to
whole-row equality assert **satisfy hi nahi ho sakta tha** aur usko runtime pe relax karna pada (`P-31`).
**Frozen quantities aur intentionally-moving quantities ko ek hi assert me nahi daalna.**

## C1 — reconcile chain, aur ye check fail hone laayak hona chahiye

| Check | Kaise | Mechanism maujood | Mechanism ghayab |
|---|---|---|---|
| Chain judi | reconcile table, **line-by-line** | Har line ka source naam se, aur mismatch pe cause | Sirf total match → **do compensating errors chhup sakti hain** (Week 2 ka wahi bug) |
| `sink_deliveries` ka `-3` | `select count(*) from sink_deliveries` **aur** `select id from sink_deliveries order by id` | `7`, ids `1,2,4,6,7,8,9`, gaps `3,5,10` **naam se**, cause `cb17c36` / `P-46` | `7` likh ke aage badh gaye → chain ka ek bucket `-3` se galat hai aur wo kisi doosri line me cancel ho sakta hai |
| Din 5 ka delta `0` | `9`-counter bench vs Din 4 close ke `8` + `sink_deliveries` | `8` counters pe `0` **aur** `sink_deliveries` pe `-3` — **do alag statement** | *"delta strictly `0`"* → wo ek exclusion pe khada hai jiska naam nahi liya gaya |
| `side_effects` duplicates | `group by job_id having count(*) > 1` | Har row `expected` ya `unexpected` naam se | Query chali aur output copy ho gaya → ek `unexpected` row chhup jaata hai |
| `running`/`pending` at close | `group by status` + ids | Zero ho ya na ho, **dono likhe jaate hain**, ids ke saath | Omit kiya kyunki zero tha → `P-12` ka shape, ek flat number ek non-event bhi ho sakta hai |

**Aur ek differential jo `-3` ke liye specifically hai** — ek arm se ye pakda nahi jaata:

| Arm | Kya | Expected |
|---|---|---|
| 1 | `select count(*) from sink_deliveries` | `7` |
| 2 | `select count(distinct idempotency_key) from sink_deliveries` | `7` — **arm 1 ke barabar**, matlab koi duplicate nahi bacha |
| 3 | `select last_value from sink_deliveries_id_seq` | `10` — **`7` nahi**, aur yahi `-3` ka proof hai |

Arm 1 akela *"`7` rows hain"* kehta hai aur ek fresh reader usko *"`7` deliveries hui thi"* padh lega. Arm 3
batata hai ki **das** hui thi. **Sequence hi wo gawaah hai jo `DELETE` ke baad bacha hai.**

## C2 — chaar decisions

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Chaar `D-` numbers free the | C0 ka grep zero match pe pass hua, **likhne se pehle** | Grep baad me chalaya → collision ka pata hi nahi chalta, aur ye teesri baar hoga |
| Har `Rejected` bhara hua | Chaaron entries me non-empty `Rejected`, aur usme ek **named** alternative | *"Alternatives considered"* jaisa khaali phrase → antithesis slaughter nahi hui (rule 28) |
| `D-29` ka advisory lock **honestly** maara gaya | Likha hua ki wo number **nahi** liya gaya, aur `Rejected` uske bina kya claim kar sakta hai | *"Single reaper ke numbers se reject kiya"* → wo numbers exist nahi karte, aur ye poore entry ka sabse aasaan jhooth hai |
| `Cost` lines measured hain | Har `Cost` ke aage `[MEASURED]` / `[REPORTED, NOT VERIFIABLE]` / `[NOT TESTED]` | Bare `Cost` line → ek plausible number ek measured number jaisa padhta hai |
| Paanch amendments likhi | `D-06` `D-21` `D-22` `D-23` `D-25` pe amendment block | Naya entry bana diya → do jagah do sach, aur purana entry aaj bhi galat padha jaata hai |

## C3 — README

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Failure matrix me khaali cell nahi | Table scan; har cell me evidence **ya** `[NO EVIDENCE]` | Khaali cell → matrix reassuring dikhta hai aur kuch prove nahi karta |
| Har number traceable | Har number ke aage source (job id / log line / din) | Ek bhi number bina source → wo blog me bhi jaayega aur interview me poocha jaayega |
| Teen numbers labelled | Pool timeout · `P-41` wait · `/healthz` timeout pe `[REPORTED, NOT VERIFIABLE]` | Bare numbers → `P-45` README me chhup gaya, aur README ka poora point honest scoping hai |
| Diagram me transaction boundaries | Boundaries dikhti hain, sirf arrows nahi | Generic queue diagram → wo kisi bhi project ka ho sakta hai |
| Banned vocabulary absent | `Select-String -Path README.md -Pattern 'production-ready\|scalable\|robust'` → zero match | Match mila → teen hafte ki honest scoping ek adjective se undo ho gayi |
| **`protected` ka scope** | Har `protected` ke saath *"under the failures tested"* | Bare `protected` → wahi overclaim jo iss project ne teen hafte se avoid kiya hai |

## C4 — blog post

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Har section failure se shuru | Aath section ka pehla vaakya ek failure hai | Feature se shuru → wo generic tutorial ban gaya, aur uski koi value nahi |
| Har claim ke saath number ya disclaimer | Ek number, **ya** *"ye maine measure nahi kiya"* | Claim bina dono ke → wo ek opinion hai |
| Close section me jo khula hai | `P-43` naam se, aur *"row recoverable, process nahi"* ka farq | Close me sirf *"future work"* → post ka sabse valuable hissa gayab |

## C5 — handoff, verdict, DoD

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Paanchon promises ka verdict | Paanch me se har ek pe teen shabdon me se ek | Chautha promise `protected` → `P-43` ko dekha hi nahi gaya |
| Har verdict ke peeche job id / number | Paanch evidence cells, sab non-empty | Verdict bina evidence → wo ek raay hai |
| DoD ka har untick | **Ek** line: `deliberately deferred` (owner) **ya** `slipped` (kya chahiye) | Dono, ya koi nahi → wahi silent carry jo dus baar ho chuka hai |
| Handoff ki pehli do heading | *What Stuck* · *What Needs Reinforcement* word-for-word | Reword kiya → chaar hafte ka handoff series compare nahi hota |

## C6 — `src/` untouched, aur close

```powershell
# AAJ KA SABSE ZAROORI GATE — aaj koi code change nahi hua
$srcDiff = git diff --stat -- src/
if ($srcDiff) { throw "C6: src/ badla hai, aaj wo allowed nahi tha:`n$srcDiff" }
if ((git rev-parse HEAD:src) -ne $script:C0_SRC) { throw "C6: src tree SHA badla hai" }
"C6 src untouched=pass"

# Evidence DB — 9 data counters, delta 0 (aaj koi experiment nahi tha)
$closeBench = docker exec relay-db-1 psql -U postgres -d relay -At -c $benchSql
if ($closeBench -ne $script:C0_BENCH) { throw "C6: evidence DB delta non-zero`nC0:  $script:C0_BENCH`nnow: $closeBench" }

# Revision — ALAG assert, aur aaj wo BADALNA NAHI chahiye
$closeRev = docker exec relay-db-1 psql -U postgres -d relay -At -c "select version_num from alembic_version"
if ($closeRev -ne $script:C0_REV) { throw "C6: revision badla ($script:C0_REV -> $closeRev), aaj koi migration nahi thi" }

$close136 = docker exec relay-db-1 psql -U postgres -d relay -At -c `
  "select id,status,attempts,claim_generation from jobs where id=136"
if ($close136 -ne $script:C0_136) { throw "C6: job 136 chhoo gaya" }

$now = (Get-FileHash -Algorithm SHA256 docs/daily/week_04/DIN_06_PREDICTIONS_FROZEN.md).Hash
if ($now -ne $script:FROZEN) { throw "C6: frozen file badal gayi" }

$probes = docker exec relay-db-1 psql -U postgres -At -c `
  "select count(*) from pg_database where datname like 'relay_%'"
if ([int]$probes -ne 0) { throw "C6: probe DBs bachi hui hain: $probes" }

# Chaar decisions ab MAUJOOD hone chahiye — C0 pe zero the, ab exactly 4
$dcount = (Select-String -Path docs\DECISIONS.md -Pattern '^## D-2[6-9]').Count
if ($dcount -ne 4) { throw "C6: D-26..D-29 me se sirf $dcount likhe gaye" }

# Banned vocabulary
$banned = Select-String -Path README.md -Pattern 'production-ready|scalable|robust'
if ($banned) { throw "C6: README me banned vocabulary:`n$($banned.Line -join "`n")" }

# Failure matrix me khaali cell nahi — `| |` ya `|  |` ka koi occurrence nahi
"C6=pass"
```

**Note, aur ye kal ki wording ka fix hai:** aaj ka delta check **nau data counters** pe hai aur revision ka
apna alag assert hai. Log me wahi likho jo assert hua: *"delta `0` on the nine asserted data counters, revision
unchanged"* — **`sink_deliveries` aaj frozen set ke andar hai**, kyunki aaj receiver ka schema nahi badal raha.

---

# Part D — Scope guard: aaj **nahi**

| Kya | Owner | Aaj karne se kya khota hai |
|---|---|---|
| **`P-43` ka fix** (worker/reaper pe exception boundary, ya supervisor) | **Month 2** | Aaj wo `[NO EVIDENCE]` verdict ka **input** hai. Fix karne se Month 1 ka verdict ek aisi cheez pe likha jaayega jo Month 1 me maujood nahi thi — aur wo verdict table ka poora point hi jhoota kar deta hai |
| **`P-44` ka fix** (`/slow-hold` hatana ya bound lagana) | **Month 2** | Wo ek `src/` change hai aur aaj `git diff --stat -- src/` ek gate hai. Aur `D-28` ka endpoint inventory usko **naam se** carry karta hai; hata dene se decision ka subject gayab |
| **`pool_pre_ping` ka faisla badalna** | **Month 2**, `P-43` ke fix ke **baad** | Order load-bearing hai: pehle exception boundary, phir `pool_pre_ping` ki keemat. Aaj flag add karna ek galat premise pe (Faisla 4) likha hua faisla implement kar dena hai |
| **Step 2 / Step 3 dobara chalana** taaki missing numbers recover ho | **Month 2** | Aaj ka pool configuration kal ka nahi hai. Dobara chalane se ek **chautha** number aayega, un teen ka evidence nahi. `[REPORTED, NOT VERIFIABLE]` likhna zyada honest hai (`P-45`) |
| **`requirements.txt` pin karna** | **Month 2** — aaj DoD me `slipped` likha jaata hai | Pin karna ek dependency-resolution run maangta hai aur wo aaj ke `200 min` me nahi hai. Aur ek galat pin `pytest` ko tod ke poora din kha sakta hai |
| **`w4d4_sink_unique` ka `DELETE` theek karna** | **kabhi nahi** — wo migration already chal chuki hai jahan chalni thi | Ek chali hui migration ka body badalna do DB ko divergent history de deta hai. `P-46` ka rule **future** revisions pe lagta hai |
| **Teen deleted `sink_deliveries` rows wapas laana** | **kabhi nahi** | Wo irreversible hai aur unka **absence** ab evidence hai (`P-46`, sequence `10` vs `7` rows). Invent karna log ko falsify karna hai |
| Job `136` ko haath se terminal karna | **kabhi nahi** | `P-05`. Wo Din 6 ke close pe ek naam wali carried row hai, mechanism `P-36` me likha hai |
| **Month 2 ka plan** | `BACKEND_ROADMAP_PART2.md`, aur wo Month 1 close hone **ke baad** khulti hai | Aaj wo kholna Month 1 ke verdict ko *"Month 2 me theek ho jaayega"* ke lens se likh dena hai. Verdict aaj ke evidence pe likha jaata hai, kal ke plan pe nahi |
| Handler timeout · retention · partitioning · `job_executions` pe index | **Month 2** | Chaaron `Cost` lines hain aaj, features nahi. `P-05` ki gap list aur `job_executions` ka growth aaj **evidence** hain |
| Redis · `LISTEN`/`NOTIFY` · leader election | Sirf `D-29` me **likha** jaata hai, banaya nahi | `D-29` ka poora kaam un teenon ko **price** karna hai. Ek bhi banane se comparison khatam |
| Naye test | **Month 2** (`P-37`) | Aaj ka budget `200 min` hai aur README + blog + chaar decisions usme se `130` le rahe hain. Aur README ki ek line `P-37` ko honestly carry kar deti hai |
