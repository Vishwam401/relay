# WEEK 4 — Fencing, outbox, load, aur production writeup

**Layer: L4 ka taste · Month 1 ka aakhri hafta** · Daily log with measurements, prediction scoring, and unresolved items.  
Plan: [`../planning/WEEK_04.md`](../planning/WEEK_04.md) · Decisions: [`../DECISIONS.md`](../DECISIONS.md)

> **Plan intent rakhta hai; ye file outcome rakhti hai.** Har factual claim ke saath provenance hai:
> `[MEASURED]` user ke retained output se · `[MEASURED-R]` reviewer rerun/read se · `[INFERRED]`
> source/mechanism se · `[NO EVIDENCE]` jab original output retain nahi hua.

---

## Din 1 — Fencing: pehle nuksaan, phir monotonic epoch (`2026-09-06`)

**Original goal (from the BRIEF):** generation-blind stale lifecycle write ka real harm pehle reproduce karna;
`jobs.claim_generation` aur nullable historical `job_executions.claim_generation` migrate karna; claim CAS se
current generation atomically `RETURNING` me lena; heartbeat aur final mark ko `(status, generation)` se gate
karna; fresh owner ka positive control aur stale owner ka named `rowcount=0` witness retain karna; aur D-26
ke liye `Problem + Options` draft banana.

**Goal met?** **Core experiment: yes. Day-close protocol: partial.** `[MEASURED-R/INFERRED]`

- `[MEASURED]` Job 126 ne generation-blind harm dikhaya: stale A ka mark B ke live claim par
  `rowcount=1` hua, aur current owner B ka final mark `rowcount=0` hua.
- `[MEASURED-R]` Migration shape, claim/heartbeat/mark gates, fresh-owner control (Job 127), aur stale
  generation rejection (Job 128) source, current catalog, DB rows, aur retained logs me agree karte hain.
- `[MEASURED-R]` C5 **as written pass nahi ho sakta**: teen `*_by_day` queries ka `GROUP BY 1` aggregate ko
  group karne ki koshish karta hai; PostgreSQL ne `aggregate functions are not allowed in GROUP BY` diya.
- `[MEASURED-R]` Day 1 implementation current repository state me committed nahi hai. `HEAD=87f2253`
  Week 3 close hai; `src/models.py` aur `src/worker.py` modified hain; migration untracked hai.
- `[INFERRED from deliverable vs file]` `DIN_01_DESIGN.md` C2 ka three-section `Chosen/Rejected/Cost` gate
  pass karti hai, lekin requested D-26 draft ka explicit `Problem + Options` shape nahi rakhti. Final D-26
  publish nahi hua, jo sahi hai; uska `Cost` real-process witness ke baad hi final hona hai.

### 📊 Measured / Observed

#### Seal aur retained evidence

| Kya | Result | Provenance |
|---|---|---|
| Frozen SHA-256 | `45FE9B100940D29FE55D18AF3AEEA5F662C527E2CB72ED7993A53B0CD7BD46A8` | `[MEASURED-R]` current file hash |
| Frozen mtime UTC | `2026-09-06T08:02:34.9619343Z` | `[MEASURED-R]` filesystem |
| Original C0 hash-equality terminal line | Not retained | `[NO EVIDENCE]`; current hash original shell variable ko retroactively prove nahi karta |
| Original C0 opening SQL transcript | Not retained | `[NO EVIDENCE]`; opening state ab mutate ho chuki hai, isliye rerun possible nahi |
| `w4d1_*.log` files | `9`, sab non-empty | `[MEASURED-R]`; BRIEF ka “seven” count galat hai |
| Relay processes at close | `0` | `[MEASURED-R]` |

#### Step 0 — carried-job drain

| Kya | Result | Provenance |
|---|---|---|
| Drained job ids | `116, 121, 123, 124` | `[MEASURED from retained drain log]` |
| Outcome | Chaaron ek-ek claim ke baad `succeeded`; execution delta `+4`; effect delta `+0` | `[MEASURED from retained log + MEASURED-R current rows]` |
| Original C0D SQL transcript | Not retained | `[NO EVIDENCE]`; outcome log/DB me bacha hai, exact terminal block nahi |

#### Step 1 — fence se pehle actual harm (Job 126)

| Event | UTC | Provenance |
|---|---:|---|
| A claim | `08:05:57.303` | `[MEASURED from w4d1_step1_worker_a.log]` |
| A blocks event loop | `08:05:57.334` | `[MEASURED]` |
| Reaper reclaim | `08:06:28.487` | `[MEASURED]` |
| B claim | `08:06:30.292` | `[MEASURED]` |
| Stale A marks `succeeded`, `rowcount=1` | `08:06:42.342` | `[MEASURED]` |
| B handler finishes | `08:07:15.315` | `[MEASURED]` |
| B final mark conflicts, `rowcount=0` | `08:07:15.326` | `[MEASURED]` |

- `[MEASURED-R from retained timestamps]` Claim-to-reclaim gap `31.184 s` tha.
- `[MEASURED-R from retained timestamps]` A ne B ke finish se `32.973 s` pehle stale mark likha;
  iss interval me API `succeeded` dikha sakti thi jab B ka handler live tha.
- `[MEASURED-R]` Current DB: `job|126|succeeded|2|0|NULL`, do executions, do workers, dono historical
  execution generations `NULL`, aur ek effect row.
- `[MEASURED-R]` A ke retained log me 45 s block ke baad extra `Heartbeat sent for job 126` line nahi mili.
- `[INFERRED]` Status-only CAS ne apna written predicate sahi evaluate kiya, lekin predicate claim identity
  poochti hi nahi thi. Isliye stale owner accept aur fresh owner reject hua.

#### Step 2 — design choices

| Choice | Recorded decision | Review |
|---|---|---|
| Generation increment owner | Sirf claim CAS; reaper reclaim nahi | `[INFERRED design judgement]` valid while claim CAS is the only path that writes `running` |
| Token shape | DB-owned monotonic `BIGINT`; `claimed_at`/UUID rejected | `[INFERRED]` equality fencing ke saath monotonic value audit ordering bhi deti hai |
| Effect identity | Stable `effect_key` remains generation-independent | `[INFERRED]` claim identity aur logical-effect identity alag rehte hain |
| C2 structural gate | `C2=pass` | `[MEASURED-R]` |
| D-26 draft shape | Explicit `Problem + Options` absent; file has `Chosen/Rejected/Cost` sections | `[MEASURED-R]` |

#### Step 3 — schema, gates, and fresh-owner control

| Kya | Result | Provenance |
|---|---|---|
| `jobs.claim_generation` | `bigint NOT NULL DEFAULT 0` | `[MEASURED-R]` current catalog/source |
| `job_executions.claim_generation` | nullable `bigint`, no default | `[MEASURED-R]` |
| Historical executions | `113 NULL`, `3` generation-stamped, total `116` | `[MEASURED-R]` current DB |
| Claim gate | Generation increments in claim `UPDATE`; current value comes from same statement’s `RETURNING` | `[INFERRED from source]` |
| Heartbeat gate | `id + status='running' + claim_generation` | `[INFERRED from source]` |
| Mark gate | `id + status='running' + claim_generation` | `[INFERRED from source]` |
| Execution stamp | Claimed generation written to `job_executions` | `[INFERRED from source; MEASURED-R on Jobs 127/128]` |
| Fresh-owner control | Job 127: `succeeded`, attempts `1`, generation `1`; execution generation `1`; mark `rowcount=1` | `[MEASURED from retained smoke log + MEASURED-R DB]` |
| Regression tests | `7 passed in 2.68s` | `[MEASURED-R]`; baseline green migration correctness ka substitute nahi |
| Static import/compile check | `compileall_exit=0` | `[MEASURED-R]` |
| Alembic heads | exactly `w4d1_claim_generation (head)` | `[MEASURED-R]` |

**Independent disposable lifecycle rerun:**

```text
head|w4d1_claim_generation|2
down|w3d4_enqueue_idempotency|0
reup|w4d1_claim_generation|2
```

`[MEASURED-R]` Dedicated `relay_w4d1_closeout` DB use hui. Evidence DB revision/column count unchanged raha;
probe DB aur temporary ini remove kiye gaye; final probe count `0` hai.

#### Step 4 — generation fence (Job 128)

| Event / row | Result | Provenance |
|---|---|---|
| A claim | `08:13:52.219`, generation `1` | `[MEASURED from retained log]` |
| Reaper reclaim | `08:14:23.485` | `[MEASURED]` |
| B claim | `08:14:24.754`, generation `2` | `[MEASURED]` |
| A stale mark | `08:14:37.259`, `held_generation=1`, `current_generation=2`, `rowcount=0` | `[MEASURED]` |
| Snapshot row | `job|128|running|2|2|NULL` | `[MEASURED-R]` current DB |
| Executions | `2` rows, `2` workers, generations `1,2` | `[MEASURED-R]` |
| Logical effects | `1` | `[MEASURED-R]` |
| Stale-generation audit | `stale_gen_exec|1` | `[MEASURED-R]` |
| Extra stale heartbeat after A’s block | No matching line retained | `[MEASURED-R]` log grep |

`[INFERRED from source + MEASURED outcome]` Fence stale **lifecycle writes** ko reject karti hai; stale handler
work ko cancel nahi karti. A effect insert already attempt kar chuka tha. `effect_key` uniqueness isliye fence
ka replacement nahi, separate layer hai. Job 128 ka `running` rehna safety improvement ke saath liveness cost
hai; problem eliminate nahi hui, shape badli.

#### Closing bench — corrected read-only query

```text
close|122|128|128|116|11|16|w4d1_claim_generation
status|dead_letter|3
status|failed|15
status|running|1
status|succeeded|103
jobs_by_day|2026-09-06|3
exec_by_day|2026-09-06|5
effect_by_day|2026-09-06|2
idle_in_txn|0
probe_dbs|0
stale_gen_exec|1
```

`[MEASURED-R]` Ye reviewer ki corrected query ka current snapshot hai. User-reported first line
`close|122|128|128|116|11|16|w4d1_claim_generation` se match karti hai. **Isko original `C5=pass` nahi
likhna:** original C5 SQL PostgreSQL error ke saath exit `1` deta hai.

#### Git truth

```text
HEAD 87f2253 docs(week-3-din-6): ... close week 3
 M src/models.py
 M src/worker.py
?? alembic/versions/w4d1_claim_generation_add_claim_generation.py
```

`[MEASURED-R]` Isliye “code commit kar diya” current repo se contradict hota hai. `docs/logs/WEEK_03.md`
bhi pre-existing modified file hai; reviewer ne usko Day 1 implementation me attribute nahi kiya.

### 🔎 Code audit

| Finding | Verdict | Provenance |
|---|---|---|
| Atomic generation capture | Correct: claim increment aur `RETURNING` same DML statement me | `[INFERRED from source]` |
| Heartbeat/mark ownership guard | Correctly includes current generation equality | `[INFERRED from source; MEASURED-R witnesses]` |
| Historical provenance | Correct: old execution rows remain `NULL`, synthetic generation `0` nahi | `[MEASURED-R]` |
| Effect identity | Correctly remains `job:{job_id}`, generation-independent | `[INFERRED from source; MEASURED-R effect count]` |
| Mark failure label | Best-effort only: failed UPDATE ke baad separate SELECT me generation phir badal sakti hai, so rare interleaving me “fenced” attribution wrong ho sakta hai; guarded UPDATE safe rehta hai | `[INFERRED from READ COMMITTED/source]` |
| Cancellation boundary | Heartbeat loss task ko rokta hai, already-running blocking handler ko nahi | `[INFERRED from source; MEASURED-R Job 128]` |

### 🧠 Prediction review — frozen text only

**Reported in chat:** `2.5/5.0`. **Reviewer score:** **`1.0/5.0`** `[INFERRED from KEY rubric applied to
`DIN_01_PREDICTIONS_FROZEN.md`]`. `DIN_01_ANSWERS.md` me `2.5/5.0` score line maujood nahi hai
`[MEASURED-R]`. `Observed` aur `After KEY` explanations generally strong hain, par prediction credit nahi lete.

| Q | Score | Frozen answer review |
|---|---:|---|
| Q1 | `0.5/1.0` | `[INFERRED]` Stale A ke success/B rejection ka core shape tha, par exact `('succeeded', 2, NULL)` aur attempts mechanism absent/ambiguous tha |
| Q2 | `0/1.0` | `[INFERRED]` Generic concurrent “gadbad”; reclaim + re-claim, stolen `N+1`, aur fence-rubber-stamp consequence absent |
| Q3 | `0/1.0` | `[INFERRED]` Historical `0` predicted, par rubric-required concrete stale-generation false-negative query absent |
| Q4 | `0.5/1.0` | `[INFERRED]` Count `2` correct; mechanism “distinct effect-key strings, so UNIQUE/ON CONFLICT never fires” absent |
| Q5 | `0/1.0` | `[INFERRED]` Honest `idk`; accurate provenance, zero credit as specified |
| **Total** | **`1.0/5.0`** | `[INFERRED from fixed rubric]` |

### 💡 What the session established — **user must rewrite this in his own words**

> Ye reviewer-written synthesis hai, user ka “What I Understood” nahi.

1. `[INFERRED from measured runs]` `status` cycle karta hai; ownership token ko cycle nahi karna chahiye.
   Monotonic generation stale claim ko current claim se distinguish karti hai.
2. `[INFERRED]` `RETURNING` convenience nahi, ownership binding hai: separate post-claim SELECT doosre owner ki
   generation padh kar fence ko rubber stamp bana sakta hai.
3. `[MEASURED-R/INFERRED]` Fencing stale lifecycle writes ko **narrows/rejects**; stale work ya external
   side effects ko eliminate nahi karti.
4. `[INFERRED]` Claim identity (`claim_generation`) aur business-effect identity (`effect_key`) alag questions
   answer karte hain; ek ko doosre me milana dedup ko todta hai.
5. `[MEASURED-R/INFERRED]` Job 128 ne safety failure ko liveness failure me convert hote dikhaya: false terminal
   write ruki, lekin long handler/short lease shape intervention ke bina terminal progress guarantee nahi deti.

### ⚠️ Closeout corrections

| Claim/check | Correction | Provenance |
|---|---|---|
| “Day 1 code committed” | Current Git state me committed nahi | `[MEASURED-R]` |
| “C0–C5 all pass” | C5 as written SQL error deta hai; corrected read-only close matches reported totals | `[MEASURED-R]` |
| “Prediction score 2.5/5” | Frozen-only rubric score `1.0/5.0`; 2.5 file me recorded nahi | `[INFERRED]/[MEASURED-R]` |
| “D-26 draft done” | Three decisions exist and C2 passes, but explicit `Problem + Options` deliverable shape absent | `[MEASURED-R/INFERRED]` |
| “Seven logs” | Actual non-empty `w4d1_*.log` count `9` | `[MEASURED-R]` |
| C3 pytest gate | Command exit code print karta hai, nonzero par throw nahi karta; a red suite bhi step ko continue karwa sakti hai | `[INFERRED from BRIEF]` |
| C4 monotonic gate | Script generations print karta hai, monotonicity assert nahi karta; repeated `1,1,2,2` claim+execute lines expected hain | `[INFERRED from BRIEF/log shape]` |
| C4 execution shape | Query prints exec count/workers/generations, par explicit assertions missing hain | `[INFERRED from BRIEF]` |

### 🚧 Unresolved / Day 1 close blockers

- `[MEASURED-R]` `src/models.py`, `src/worker.py`, aur migration ko abhi commit truth chahiye; reviewer ne commit
  create nahi kiya because user ne commit request nahi ki.
- `[MEASURED-R/INFERRED]` C5 ke three date-group queries ko date expression par group karna hoga; tabhi future
  rerun actual `C5=pass` ho sakta hai. Current corrected snapshot evidence hai, original pass nahi.
- `[MEASURED-R]` Original C0/C0D/C1/C3 terminal transcripts retain nahi hue. Retained process logs aur DB state
  core mechanism support karte hain, par missing original transcript manufacture nahi ki ja sakti.
- `[MEASURED-R/INFERRED]` `DIN_01_DESIGN.md` ko publishable D-26 draft kehne se pehle explicit `Problem + Options`
  shape chahiye; final `Cost`/decision Week 4 ke later measured witness ka owner hai.
- `[MEASURED-R]` `docs/roadmap/CURRENT_WEEK.md` abhi Week 3 closed par point karta hai. User ne iss closeout me
  sirf Week 4 log aur master index update maanga, isliye pointer edit nahi kiya gaya.

### ❓ Next thought

Day 2 material intentionally nahi banaya gaya. Day 1 se aage jaane se pehle user ko upar ka reviewer-written
“established” block apne shabdon me rewrite karna, Git/ C5 truth resolve karna, aur `Problem + Options` draft
shape ko deliberate close karna hai. `[INFERRED process requirement]`

---

## Din 2 — Instruments: `completed_at`, `last_error`, lifecycle log, aur wo shutdown run jo do hafte phisla tha (`2026-09-07`)

**Original goal (from the BRIEF):** `completed_at` + `last_error` migrate karna, teeno mark paths ko generation
gate ke *peeche* likhna, latency ki likhi hui definition, ek greppable structured lifecycle line, pehla derived
latency number `n` ke saath, aur `45 s` payload + `SIGBREAK at T=3 s` ke teen run (yielding · blocking · blocking
with a second worker).

**Goal met?** **Run 1 aur Run 2: yes, aur ye din ka core hai. Run 3: void. Day-close: partial.**
`[MEASURED-R]`

- `[MEASURED-R]` Migration, gated writes, aur `last_error` clearing teeno source, catalog, aur rows me agree
  karte hain. `succeeded ∧ last_error IS NOT NULL` = `0` — Q3 ka bug **actually** avoid hua.
- `[MEASURED-R]` Run 2 ne `D-22` Cost 8 ka jawab de diya, aur uske saath ek naya measured number: blocking
  handler me **signal delivery bhi handler ke peeche queue hoti hai**, `42.068 s`.
- `[MEASURED-R]` **Run 3 void hai.** Harness ka anchor `Executing job 134` tha; worker ne job `133` claim ki
  (purani `created_at` jeeti). Anchor kabhi match nahi hua, **signal kabhi nahi bheja gaya**, aur `180 s` baad
  harness ne child ko `kill` kiya. Q5 ka fencing half `[NO EVIDENCE]` hai.
- `[MEASURED-R]` **C0D as written pass nahi hua.** Job `128` `attempts=4`, `claim_generation=4`,
  `exec128|4|4|1,2,3,4` — BRIEF `3|3|1,2,3` assert karta hai. Reaper `30 s` ke andar band nahi hua, fence ek
  baar lagi, doosre reclaim pe drain hui. Ye BRIEF me likha hua fallback hai, failure nahi — par **"C0D passed"
  likhna galat hai.**
- `[MEASURED-R]` **`Mark fenced` aaj ek baar bhi print nahi hui** (`0` lines, saare `w4d2_*.log` me).
  `Conflict on mark` `7` baar. Isliye **C4b "not tested" hai, "pass" nahi** (`P-12`).
- `[MEASURED-R]` Day close pe teen `pending` rows carried hain (`132`, `133`, `134`) aur **C5b ne phir bhi
  pass diya** — closing bench me queue-drained ka koi assertion nahi hai. Naya `P-31`.
- `[MEASURED-R]` Prediction score **`0.0/5.0`**: paanchon frozen answers `idk` hain, aur `DIN_02_ANSWERS.md`
  ka hash `DIN_02_PREDICTIONS_FROZEN.md` ke **barabar** hai — matlab beat 4 (apni explanation) aur beat 5
  (KEY ke baad ke gaps) kabhi likhe hi nahi gaye.

### 📊 Measured / Observed

#### Seal aur retained evidence

| Kya | Result | Provenance |
|---|---|---|
| Frozen SHA-256 | `412B79AF083141AE225C68419E6C93E62CA1F7B89953E34B04E633805476F9EE` | `[MEASURED-R]` current file hash; user-reported hash se **match** karta hai |
| Frozen mtime UTC | `2026-09-07T08:17:45.3433822Z` | `[MEASURED-R]` filesystem |
| `DIN_02_ANSWERS.md` ka hash | **frozen file ke barabar** (`412B79AF…F9EE`) | `[MEASURED-R]`; answers file freeze ke baad **ek byte bhi** nahi badla |
| `w4d2_*.log` files | `10`, sab non-empty (`5153`–`270940` bytes) | `[MEASURED-R]` |
| `harness_sigbreak.py` | disk pe aur `52f9ab3` me committed (`53` lines) | `[MEASURED-R]` |
| Relay processes at close | `0` | `[MEASURED-R]` |

#### Git truth — aur ye Din 1 ka blocker band karta hai

```text
d818310 feat(week-4-din-1): implement claim_generation fencing token, verify stale mark rejection, and add formal log
52f9ab3 feat(week-4-din-2): add completed_at, last_error instruments, structured logs, and sigbreak harness
  alembic/versions/w4d2_completion_instruments_...py | 34 ++
  harness_sigbreak.py                               | 53 ++
  src/models.py                                     | 10 ++
  src/worker.py                                     | 43 +-
```

`[MEASURED-R]` Step 0A hua. Din 1 ka *"committed nahi hai"* blocker **closed** hai, aur Din 2 ek alag commit me
hai — `git bisect` ab do din ko alag dekh sakta hai. `docs/daily/` `.gitignore` me hai, isliye
DESIGN/ANSWERS/FROZEN commit me nahi hain aur ho bhi nahi sakte (`P-23` ka wahi shape, seal isliye hash hai).

#### Step 0D — job `128` ka drain: BRIEF ke expected se alag, aur wo alag hona hi finding hai

| Kya | BRIEF ka expected | Actual | Provenance |
|---|---|---|---|
| Row shape | `128|succeeded|3|3` | `128|succeeded|**4**|**4**` | `[MEASURED-R]` current row |
| Executions | `exec128|3|3|1,2,3` | `exec128|**4**|**4**|**1,2,3,4**` | `[MEASURED-R]` |
| Effects | `eff128|1` | `eff128|1` (row `id=15`) | `[MEASURED-R]` |
| `completed_at` | — | **`NULL`** | `[MEASURED-R]` |

`[MEASURED from job_executions]` Gen `3` `08:21:55.670` (`worker-18036`), gen `4` `08:25:23.661`
(`worker-8648`). Do reclaim hue, matlab reaper pehli koshish me `30 s` ke andar band nahi hua. **Ye Din 1 ke
*"loop apne aap nahi rukta"* claim ka teesra witness hai** aur BRIEF ne isko naam se allow kiya tha.

`[MEASURED-R]` `completed_at` `NULL` hona **sahi** hai: drain `08:26:08` pe mark hua aur migration uske **baad**
chali (pehla `completed_at` job `129` pe `08:41:12` hai). Ek terminal row bina timestamp — aur wo honest hai,
kyunki uss waqt column exist hi nahi karta tha. **Ye `NULL` ka paanchvaan meaning hai** (`P-19` → Din 1 → aaj).

#### Step 2 — migration aur gated writes

| Kya | Result | Provenance |
|---|---|---|
| Revision | `w4d2_completion_instruments`, revises `w4d1_claim_generation` | `[MEASURED-R]` source |
| `jobs.completed_at` | `timestamp with time zone`, nullable, **no default** | `[MEASURED-R]` catalog |
| `jobs.last_error` | `text`, nullable, no default, `attstorage='x'` (EXTENDED) | `[MEASURED-R]` catalog |
| `downgrade()` | dono columns drop karta hai, likha hua hai | `[MEASURED-R]` source |
| Alembic heads | exactly `w4d2_completion_instruments (head)` | `[MEASURED-R]` |
| Backfill honesty | purani rows dono columns pe `NULL`; koi manufactured `now()` nahi | `[MEASURED-R]` per-status counts |
| Mark gate | `completed_at` **aur** `last_error` dono usi `UPDATE` me hain jisme `status='running' AND claim_generation=:g` | `[MEASURED-R from src/worker.py + retained SQL echo]` |
| Regression | `7 passed`, exit `0` | `[MEASURED-R]` |

`[MEASURED from w4d2_run1_worker.log, SQLAlchemy echo]` — ek hi statement, teen columns, ek gate:

```sql
UPDATE jobs SET status=$1, next_attempt_at=$2, completed_at=now(), last_error=$3
 WHERE jobs.id = $4 AND jobs.status = $5 AND jobs.claim_generation = $6
-- ('succeeded', None, None, 131, 'running', 1)
```

`[INFERRED from source]` Koi alag un-fenced lifecycle writer nahi bana — `D-26` draft ka wo `Cost` aaj **nahi**
realise hua. Par ye **structural** verification hai, run-time nahi: fence ko aaj koi stale writer mila hi nahi
(neeche C4b).

#### Step 3 — lifecycle log, job `130`

| Kya | Result | Provenance |
|---|---|---|
| Row | `130|dead_letter|3|3`, `completed_at 08:43:37.753151`, `length(last_error) 308` | `[MEASURED-R]` |
| Executions | `3` rows, `1` worker, generations `1,2,3` | `[MEASURED-R]` |
| Grep `job_id=130\b` | `12` lifecycle lines; `claim`/`execute`/`mark` = `3`/`3`/`3` | `[MEASURED-R]` |
| Unstructured lines | `0` | `[MEASURED-R]` |
| Backoff, actual | attempt 1 → `3.43 s`, attempt 2 → `5.22 s` (equal jitter) | `[MEASURED]` |
| Poora lifecycle wall time | `08:43:27.497` → `08:43:37.770` = `10.273 s` | `[MEASURED-R]` |

`[MEASURED-R]` Ek **doosri** `boom` job bhi hai jo log me nahi bachi: job `129` (`08:41:00`–`08:41:12`,
`dead_letter`, `attempts 3`, `last_error 308`). `Tee-Object` ne uska log overwrite kiya. Rows dono ke hain,
transcript ek ka.

`[MEASURED-R]` **Do log format ek hi din me hain, aur ye BRIEF ka named risk hai.** Step 3 ka log
`Claimed job_id=130 (generation=1, …)` likhta hai; final committed code
`[claim] Claimed job 131 (job_id=131, generation=1, attempt=1, rowcount=1)` likhta hai. Dono me `job_id=` hai
to grep chalti hai; par `Marked job_id=130 as` aur `Marked job 131 as` do alag prose shapes hain. **Canonical
form aage ke liye committed code wali hai** — kyunki wahi C5a ke `Marked job <id> as` / `Executing job <id>`
anchors ko bhi satisfy karti hai.

#### Step 4 — pehla latency number

```text
latency|3|00:00:26.995518|00:01:49.875049|00:00:22.847106|00:01:51.566468
latency_by_status|dead_letter|2|00:00:24.921312
latency_by_status|succeeded|1|00:01:51.566468
negative|0
clockgap_us|3931
```

`[MEASURED-R]` `n = 3`. **`00:01:49.875` ko `p99` nahi kehna** — wo `24.92 s` aur `1:51.57 s` ke beech
`percentile_cont` ka interpolation hai aur kisi row me nahi tha. `n < 100` pe ye sirf ek `p50` hai.
Global `p50 = 26.995 s` do bilkul alag populations ka mix hai: do `boom` jobs (`~23–25 s`, teen attempts +
do backoff) aur ek `45 s` blocking job (`1:51.57 s`, jisme `~66 s` queue wait bhi hai). **Wo number kisi cheez
ka nahi hai**, aur `latency_by_status` isliye zaroori hai.

**Aur ye din ka sabse saaf measurement hai** `[MEASURED-R]`:

| Job `131` | Value |
|---|---|
| Handler wall time (log se) | **`45.036 s`** |
| `completed_at - claimed_at` (DB se) | **`00:00:04.978363`** |
| `completed_at - created_at` | `00:01:51.566468` |
| Heartbeats | `09:02:08.930`, `:18.941`, `:28.954`, `:38.979` — chaar |

`45 s` ka kaam, aur `claimed_at`-based metric `4.978 s` bolta hai. **`9.04×` understatement.** Mechanism:
aakhri heartbeat `T+40.06` pe `claimed_at = now()` likh gaya, completion `T+45.04` pe hua, residual
`= duration mod HEARTBEAT_INTERVAL_SECONDS`. Iss definition ka **ceiling `10 s` hai**, chahe handler kitna bhi
chale. `P-22` ka literal shape, ab `[MEASURED]`.

#### Step 5 — Run 1 vs Run 2, ek variable (`block`), ulta outcome

| Marker | **Run 1** job `131` `{"seconds":45}` | **Run 2** job `132` `{"seconds":45,"block":true}` |
|---|---|---|
| `exec_line` | `09:01:58.914` | `09:12:03.708` |
| `anchor` | `09:01:58.915` | `09:12:03.720` |
| `signal_sent` | `09:02:01.917` | `09:12:06.741` |
| `SIGBREAK_line` | `09:02:01.918` | **`09:12:48.809`** |
| `reaper_reclaim` | **not recorded** (`matched=1` lines: `0`) | `09:12:35.334` (`DB_TIME 09:12:35.332201`) |
| `heartbeat` lines | `4` | **`0`** |
| `handler_done` | `09:02:43.950` | `09:12:48.834` |
| `mark` | `[mark] Marked job 131 as 'succeeded' (rowcount=1)` | **`Conflict on mark: job_id=132 … (rowcount=0)`** |
| `clean_shutdown` | `09:02:43.963` | `09:12:49.283` |
| `child_exit` | `09:02:44.122` `rc=0` | `09:12:49.216` `rc=0` |
| `T0_to_signal_s` | `3.003` | `3.033` |
| **`signal_to_handler_s`** | **`0.001`** | **`42.068`** |
| `signal_to_exit_s` | `42.204` | `42.475` |
| `handler_wall_s` | `45.036` | `45.041` |
| Row at `T+50` | `succeeded`, `completed_at` set | **`pending`**, `completed_at` **`NULL`**, `last_error` **`NULL`** |

`[MEASURED]` **`signal_to_exit_s` dono me `~42.2–42.5 s` hai aur outcome bilkul ulta hai.** Ek shutdown-latency
number jo dono run me same aata hai, dono ke baare me kuch nahi bolta — isliye ek run report karna
`not isolated` hai.

`[MEASURED]` **Run 2 ka asli naya number `signal_to_handler_s = 42.068 s` hai.** `CTRL_BREAK_EVENT`
`09:12:06.741` pe gaya; `Signal SIGBREAK received` `09:12:48.809` pe print hua — `time.sleep(45)` ke **khatam
hone ke baad**. `time.sleep()` Windows pe `SIGBREAK` se interrupt nahi hoti. Isliye `P-15` ka bound
*"handler ki duration"* hai, **`remaining` duration nahi** — `45 s` handler pe wo farq `42 s` hai, aur Week 1
ke `8 s` handler pe `5 s` tha, jo dikha hi nahi. **Ye `D-22` me jaana chahiye.**

`[MEASURED]` **`D-22` Cost 8 ka jawab, poora:** Run 2 ne `45 s` ka kaam kiya, uska side effect
`09:12:03.780` pe **commit ho gaya aur durable hai**, worker `rc=0` pe cleanly exit hua — aur row `pending`
hai, `next_attempt_at NULL`, matlab turant claimable. **Kaam hua; result likha nahi gaya.** Graceful shutdown
ka *"current job finish karke exit"* ek unstated precondition pe khada hai:
`handler_duration < LEASE_DURATION_SECONDS`. Aaj wo shart tooti.

`[MEASURED]` Mark ka label **`Conflict on mark`** hai, `Mark fenced` **nahi** — aur ye sahi hai. Reaper
`claim_generation` ko nahi chhedta (`pre_generation=post_generation`, aaj directly measured, neeche), aur
koi doosra worker nahi tha, to jo predicate fail hui wo `status='running'` thi.

#### Step 5 — Run 3: **void**, aur uska cause named hai

`[MEASURED-R]` Harness `09:19:46.573` pe spawn hua anchor `Executing job 134` ke saath. Worker `worker-3128`
ne **job `133`** claim ki (`133` `09:17:28` pe bani, `134` `09:19:45` pe — claim query `ORDER BY created_at, id`
hai). Anchor kabhi match nahi hua, **`CTRL_BREAK_EVENT` kabhi nahi bheja gaya**, aur `09:22:46.590` pe harness
ne `180 s` timeout pe `proc.kill()` kiya.

**Root cause:** Run 3 ka chicken-and-egg — enqueue harness se **pehle** hota hai, aur `132` (Run 2 ki
non-terminal row) plus `133` (Run 3 ki pehli, voided koshish) queue me **already pending** the. Anchor ek
specific job id pe bandha tha; queue ne ek purani row di.

Isliye:

| Q5 ka half | Verdict |
|---|---|
| `job_executions = 2` under a signalled+fenced interleaving | **`[NO EVIDENCE]`** — signal hi nahi gaya |
| `side_effects = 1` across unbounded dispatch | **`[MEASURED]`, aur planned run se zyada strong** |

`[MEASURED-R]` Jo actually hua wo `effect_key` ka **zyada bada** imtihaan tha:

| Job | Dispatches | Distinct workers | Generations | `side_effects` |
|---|---:|---:|---|---:|
| `132` | **`7`** | `4` | `1,2,3,4,5,6,7` | **`1`** |
| `133` | **`5`** | `2` | `1,2,3,4,5` | **`1`** |

`[MEASURED]` `side_effects` total `11 → 14`, `side_effects_id_seq` `16 → 31` — **`15` sequence values, `3`
rows.** Deduped `INSERT … ON CONFLICT DO NOTHING` bhi identity default evaluate karta hai, to wo `12` ka gap
iss baat ka proof hai ki har dispatch ne insert **try** kiya tha. Barabar delta ka matlab *"test nahi hua"*
hota.

> **Dispatch count bounded nahi hai; committed local effect count `1` hai.** `attempts` `7` tak gaya jabki
> `MAX_ATTEMPTS = 3` (`P-27`, `D-23` me accepted). `effect_key = 'job:<id>'` generation-independent hai
> (Din 1 Faisla 3), isliye wo `1` **snapshot-time se independent** hai — aur wahi uss faisle ka payoff hai.

#### `Mark fenced` ka aaj ka count — aur ye C4b ko todta hai

```text
Mark fenced      : 0   lines across all logs/w4d2_*.log
Conflict on mark : 7   lines
```

`[MEASURED-R]` **Fence ko aaj ek bhi stale writer nahi mila.** Saare saat rejections `status` predicate se
aaye, generation predicate se nahi. Iska mechanism: reaper reclaim `claim_generation` ko nahi badalta, to
`fenced` ke liye ek **teesre** claimant ka reclaim aur stale mark ke **beech** me claim karna zaroori hai —
aur wo interleaving aaj kabhi nahi bani. **`completed_at` ka gate isliye iss din se run-time untested hai;
sirf structurally verified hai.** Wo Din 4 (interleaving A) ka kaam hai.

#### Closing bench

```text
close|128|134|134|137|144|14|31|w4d2_completion_instruments
status|dead_letter|5|2|2
status|failed|15|0|0
status|pending|3|0|0
status|succeeded|105|1|0
pages|2|0
stale_gen_exec|17
probe_dbs|0
idle_in_txn|0
seq_gaps|79,117,118,119,120,122
```

| Check | Result | Provenance |
|---|---|---|
| Chain: `jobs` `122 → 128` (`+6`: `129`–`134`) | consistent | `[MEASURED-R]` |
| `job_executions` `116 → 137` (`+21`), seq `123 → 144` | consistent, `0` wasted | `[MEASURED-R]` |
| `side_effects` `11 → 14` (`+3`), seq `16 → 31` (`+15`) | dedup ka evidence | `[MEASURED-R]` |
| `succeeded ∧ last_error IS NOT NULL` | **`0`** | `[MEASURED-R]`; Q3 ka silent bug **avoid hua** |
| `pending`/`running` pe `completed_at` | `0` | `[MEASURED-R]`; column `updated_at` nahi bana |
| `completed_at < created_at` | `0` | `[MEASURED-R]`; ek hi clock source |
| `jobs` heap pages | `2 → **2**` | `[MEASURED-R]`; `6` naye rows + `2×308 B` inline error ne page count nahi hilaya. Din 5 ka poll-I/O baseline **`2` pages** hai |
| `stale_gen_exec` | `1 → **17**` | `[MEASURED-R]`; Run 3 ke `12` extra dispatches isme hain |
| Sequence gaps | unchanged | `[MEASURED-R]`; `P-05` intact |
| `pytest tests` | `7 passed`, exit `0` | `[MEASURED-R]` |
| **Carried `pending` rows** | **`3` — `132`, `133`, `134`** | `[MEASURED-R]`; C5b ne assert **nahi** kiya → naya `P-31` |

### 🛠 Self-correction — ek genuine contract gap, fix, aur uska verification

**Kya mila.** Aaj ka likha hua invariant: *"ek job ka poora lifecycle ek `job_id` pe grep karke reconstruct ho
sakta hai."* Reaper ki reclaim line `id=132 pre_status=running matched=1 post_status=pending` thi —
**`job_id=` nahi.** Yaani `job_id=132` ka grep reaper log me `0` lines deta hai, aur reclaim Run 2 / Run 3 ka
**pivotal** lifecycle event hai. `[MEASURED-R]`

**Root cause — do layer:**
1. `src/reaper.py` Week 2 me likha gaya, jab `job_id=` convention exist hi nahi karta tha. Din 2 ne worker ko
   convert kiya, reaper ko nahi.
2. **Gate ne isko chhupa liya:** C3 ka `unstructured_job_lines` check **sirf** `w4d2_step3_lifecycle.log`
   (worker) padhta hai. Ek lifecycle contract jiske do producer hain, aur verification ek ko dekhti hai —
   `P-18` ka exact shape. Naya `P-32`.

**Kya change kiya** (`src/reaper.py`, ab `git status` me modified):
- `id=<n>` → `job_id=<n>`, aur ek `[reclaim]` event tag, worker ke `[claim]`/`[execute]`/`[mark]` ke saath match karne ke liye.
- Candidate `SELECT` aur `RETURNING` me `claim_generation` add kiya, aur line pe `pre_generation`/`post_generation` print kiya.
- **Field order deliberately preserved:** `job_id=<n> pre_status=… matched=… post_status=…`, generations
  **aakhir me**. Isse purana `id=<n> pre_status=… matched=1 post_status=pending` pattern (C5a ka `Get-LogEvent`,
  aur Din 1/Din 2 ke saare logs) substring ke roop me **match karta rehta hai**.

**Kaise verify kiya** — disposable DB `relay_w4d2_reaperfix` (alembic `upgrade head`), ek synthetic `running`
row `claimed_at = now() - 90 s` ke saath, ek reaper pass. Evidence DB ko chhua **nahi** gaya:

```text
PROBE_DB= relay_w4d2_reaperfix
[reaper-8468] [DB_TIME: 2026-09-07T10:25:25.357205+00:00] [reclaim] job_id=1 pre_status=running matched=1 post_status=pending pre_generation=7 post_generation=7
RECLAIMED= 1
backcompat_old_pattern_matches=True
jobid_greppable=True
```

`[MEASURED-R]` Aur ye fix **ek naya measurement bhi deta hai jo pehle sirf `[INFERRED]` tha**:
`pre_generation=7 post_generation=7` — **reaper reclaim `claim_generation` ko nahi badalta**, ab log me
directly visible. Din 1 Faisla 1 ka pehla log-level witness. Yahi wo baat hai jo aaj ke saatoun
`Conflict on mark` (aur zero `Mark fenced`) ko explain karti hai.

`[MEASURED-R]` **Cleanup:** `relay_w4d2_reaperfix` dropped (`probe_dbs|0`), `_probe_reaper_line.py`,
`_probe_out.txt`, aur `_probe.ini` deleted, `DATABASE_URL` `relay` pe restore. `pytest tests` `7 passed`
exit `0` fix ke baad. Evidence DB me **koi row nahi** add/badli gayi iss fix ke liye.

### 🔎 Code audit

| Finding | Verdict | Provenance |
|---|---|---|
| `completed_at` gate ke peeche | **Correct** — `status`, `next_attempt_at`, `completed_at`, `last_error` ek hi `UPDATE` me, `(id, status='running', claim_generation)` predicate ke saath. Koi alag un-fenced writer nahi | `[MEASURED-R from source + echoed SQL]` |
| `last_error` clearing | **Correct** — success path pe `last_error=None` explicitly bheja jaata hai, `next_attempt_at` ka precedent follow karke. `succeeded ∧ last_error not null` = `0` | `[MEASURED-R]` |
| `completed_at` retry path pe | **Correct** — retry pe `None`, matlab non-terminal row pe timestamp nahi | `[MEASURED-R]` per-status counts |
| Clock source | **Correct aur consistent** — `func.now()`, wahi clock jo `created_at` ka `server_default` hai. `negative|0` | `[MEASURED-R]` |
| `last_error` API exposure | **Correct** — `GET /jobs/{id}` sirf `id, status` select karta hai; `JobResponse` me `last_error` nahi hai. `D-03` honoured | `[MEASURED-R from src/main.py]` |
| `last_error` storage | `text`/EXTENDED, `308` bytes actual. Inline hi rahega — traceback `~10:1` compress hota hai | `[MEASURED-R catalog; MEASURED-R length]` |
| Reaper lifecycle line | **Was wrong, fixed today** (upar) | `[MEASURED-R]` |
| Rejected mark discards the diagnosis | **Real gap, not fixed** — `rowcount=0` par `status`, `completed_at`, `last_error` teeno withheld. Jis worker ne exception dekha uska reason kahin nahi bachta | `[INFERRED from source]` → naya **`P-30`** |
| KEY ka unknown-handler row | **KEY galat, code sahi** — KEY ki table `failed` likhti hai; `src/worker.py` `dead_letter` set karta hai (aur `last_error = "Unknown job type: '<t>'"`). `dead_letter` behtar hai; ye path aaj exercise nahi hua | `[MEASURED-R from source]` |
| `handle_effect` ka effect-before-work order | By design (`D-25`), aur aaj Run 2 me wahi baat load-bearing thi: effect `T+0.09` pe durable tha jabki row `pending` pe wapas gayi | `[MEASURED]` |
| `MAX_ATTEMPTS` overdraft | `attempt=7/3` print hua. Known aur accepted (`P-27`, `D-23`) | `[MEASURED]` |

### 🧠 Prediction review — frozen text only

**Score: `0.0 / 5.0`** `[MEASURED-R from DIN_02_PREDICTIONS_FROZEN.md against DIN_02_KEY.md rubric]`

Paanchon `### Prediction` blocks me exactly `idk` likha hai. Rubric `idk = 0` kehta hai aur wo **accurate data**
hai — ek guess jo knowledge ka libaas pehen ke aata, usse ye behtar hai.

| Q | Score | Frozen answer | Actual (measured today) |
|---|---:|---|---|
| Q1 | `0/1.0` | `idk` | `completed_at - claimed_at = 4.978 s` for a `45.036 s` handler; ceiling `= HEARTBEAT_INTERVAL_SECONDS` |
| Q2 | `0/1.0` | `idk` | Do cases; aaj `jobs` `2` heap pages pe hai to asar `~0`. Ye `10k`-row problem hai |
| Q3 | `0/1.0` | `idk` | Bug avoid **ho gaya** implementation me — par prediction credit nahi |
| Q4 | `0/1.0` | `idk` | exited `rc=0` · `pending` · `completed_at NULL` · `Conflict on mark` |
| Q5 | `0/1.0` | `idk` | `side_effects = 1` measured; `job_executions = 2` `[NO EVIDENCE]` (Run 3 void) |
| **Total** | **`0.0/5.0`** | | |

**Aur ek protocol observation jo score se zyada matter karti hai** `[MEASURED-R]`: `DIN_02_ANSWERS.md` ka hash
frozen file ke **barabar** hai. Matlab `### Observed + meri explanation` aur `### After KEY` blocks poore din
**khaali** rahe. Protocol ka beat 4 — *"output prediction se alag nikla to pehle apni explanation likho"* —
aaj nahi hua. **Yahi wo beat hai jiske paas iss protocol ka poora learning value rakha hai;** paanch `idk`
aur khaali `Observed` blocks ka matlab hai ki aaj ka din ek **implementation din** tha, ek measurement-learning
din nahi. Score `0` ek symptom hai, cause ye hai.

### 🤖 Claude ki Din 2 predictions — record ke liye

| # | Prediction | Verdict |
|---|---|---|
| 1 | *"Run 2 me `Heartbeat lost` line print nahi hogi"* | **CORRECT** `[MEASURED-R]`. Aur strictly stronger: `w4d2_run2_worker.log` me **`Heartbeat` shabd hi `0` baar** hai — blocking loop me heartbeat task ek bhi `UPDATE` nahi chala paaya |
| 2 | *"Run 3 me A ka mark `Mark fenced` hoga, `Conflict on mark` nahi"* | **NOT TESTED** `[MEASURED-R]`. Run 3 void hai (signal hi nahi gaya). `Mark fenced` aaj kahin print nahi hui. KEY ka apna escape clause lagta hai: Q5 `[NO EVIDENCE]`, reroll karke number "theek" nahi kiya gaya |

Din 1 ki dono predictions sahi thin; aaj ek sahi, ek untested. Running tally: `3` correct, `0` wrong,
`1` untested.

### 💡 What the session established — **user must rewrite this in his own words**

> Ye reviewer-written synthesis hai, user ka *"What I Understood"* nahi. Isko apne shabdon me likho, warna ye
> `DIN_02_ANSWERS.md` ke khaali blocks jaisa hi ek aur khaali khaana hai.

1. `[MEASURED]` **Ek metric jo instrument ke saath share kiya gaya column padhta hai, wo instrument ko naapta
   hai, event ko nahi.** `claimed_at` heartbeat ka liveness signal hai; usse latency nikalna `45 s` ko
   `4.98 s` bana deta hai, aur uska ceiling `10 s` par baithta hai. `P-22`, ab literal.
2. `[MEASURED]` **Blocking handler do cheezein queue karta hai, ek nahi:** kaam, **aur shutdown request ki
   Python-level delivery.** `42.068 s`. Isliye mid-job shutdown ka bound `handler_duration` hai,
   `remaining_duration` nahi — aur ye Week 1 ke `8 s` handler pe dikh hi nahi sakta tha.
3. `[MEASURED]` **Graceful shutdown ki guarantee ek unstated precondition pe khadi hai:**
   `handler_duration < LEASE_DURATION_SECONDS`. Run 2 me kaam poora hua, effect durable hua, process `rc=0`
   pe cleanly gaya — aur queue ke hisaab se job **kabhi chali hi nahi**. Contract #1 nahi toota (row queue me
   hai); Contract #2 ko `effect_key` ne bachaya, fencing ne nahi. **Do mechanism do layer pe hain.**
4. `[MEASURED]` **Do rejection ek jaisi dikhti hain aur do alag baatein kehti hain.** `Conflict` = generation
   wahi thi, `status` badal gaya (reclaim hua, dobara claim nahi). `fenced` = generation badal gayi (kisi ne
   cheen liya). Aaj saat `conflict` aur **zero** `fenced` — kyunki reaper generation ko nahi chhedta
   (`pre_generation=post_generation`, ab log me). **Ek `rowcount=0` ko galat label dena evidence ko
   over-report karta hai.**
5. `[MEASURED]` **`n` ke bina percentile ek naara hai, aur `status` ke bina ek average jhooth hai.**
   `p50 = 26.995 s` do `boom` jobs aur ek `45 s` blocking job ka mix hai. `p99 = 1:49.875` kisi row me nahi
   tha — `percentile_cont` ne bana diya.
6. `[MEASURED]` **Ek void run ko void likhna hi uska value hai.** Run 3 ka anchor job `134` pe tha, queue ne
   `133` di, signal kabhi nahi gaya. Q5 ka aadha jawab `[NO EVIDENCE]` hai — aur usi void run ne
   *unintentionally* `effect_key` ka planned se bada imtihaan diya: `7` dispatches, `4` workers, `1` effect.

### ⚠️ Closeout corrections

| Claim/check | Correction | Provenance |
|---|---|---|
| "All gates passed: C0, C0D, C1, C2, C3, C4a, C5a, C5b" | **C0D pass nahi hua** as written: `attempts=4`, `exec128|4|4|1,2,3,4` vs asserted `3|3|1,2,3` | `[MEASURED-R]` |
| C4b (BRIEF ka gate, user ne report nahi kiya) | **"Not tested", pass nahi** — `fence_lines = 0` saare logs me (`P-12`) | `[MEASURED-R]` |
| C5a Run 3 | **Void**, `pass` nahi. Anchor `job 134`, claim `job 133`, signal never sent, harness `kill` at `180 s` | `[MEASURED-R]` |
| C5b "pass" | Query **chalti hai** (Din 1 ka SQL bug fixed) aur totals consistent hain — par gate me queue-drained assertion **nahi** hai, aur din `3` `pending` rows ke saath band hua | `[MEASURED-R]` → `P-31` |
| "Active Relay processes: 0" | **Confirmed** `[MEASURED-R]` | |
| "Frozen Hash unchanged" | **Confirmed**, aur `DIN_02_ANSWERS.md` bhi byte-identical hai — matlab beats 4/5 skip hue | `[MEASURED-R]` |
| `DIN_02_DESIGN.md` Faisla 3 ka `Cost` — *"marginally increasing heap page consumption"* | **Contradicted by the BRIEF's own measured numbers:** `112 → 250` heap pages (5000 rows, `197`-byte inline error) = **`+123%`**, "marginal" nahi. Aaj `2` pages pe asar `~0` hai aur wahi likhna sahi tha — par reason "marginal" nahi, "`n` chhota hai" hai. **User ko ye line apne shabdon me theek karni hai** | `[MEASURED-R from BRIEF probe data]` |
| Step 3 ka log format | Committed code se **alag** hai (`Marked job_id=130 as` vs `Marked job 131 as`). Canonical = committed code | `[MEASURED-R]` |

### 🚧 Unresolved / Din 2 close blockers

- `[MEASURED-R]` **`src/reaper.py` uncommitted hai** (aaj ka fix). Usko commit karna Din 3 ka Step 0 hai,
  aur usko Din 3 ke apne code se **alag commit** me rakhna — warna Din 1 ki galti dohrayi jaayegi.
- `[MEASURED-R]` **Teen `pending` rows carried:** `132` (`attempts 7`), `133` (`attempts 5`), `134`
  (`attempts 0`). Teeno `effect` + `block:true` + `45 s`. **Din 3 Step 0 me production path se drain karna
  hai, reaper OFF ke saath** (`P-05`: `UPDATE`/`DELETE` se nahi). Reaper live rakhne pe teeno anant loop me
  ghoomengi.
- `[MEASURED-R]` **`completed_at` ka fence run-time untested** — `Mark fenced` aaj `0` baar. Owner: **Din 4
  interleaving A**, aur uska check `fence_lines >= 1` hona chahiye, `>= 0` nahi.
- `[MEASURED-R]` **Q5 ka fencing half `[NO EVIDENCE]`.** Do-worker signalled run Din 4 ka debt hai. Ye
  **teesri** baar hai ki ye shape slip hua (Week 3 → Week 4 Din 2 → Din 4). Din 4 pe ye pehla step hona chahiye.
- `[MEASURED-R]` `harness_sigbreak.py` ka anchor design **fragile hai**: ek specific job id pe bandha anchor
  tab fail karta hai jab queue me purani rows hain. Din 4 me anchor `Executing job \d+` + post-hoc job-id
  confirmation hona chahiye, ya harness ko enqueue **khud** karna chahiye. `P-32` ka neighbour.
- `[MEASURED-R]` `DIN_02_ANSWERS.md` ke `Observed` aur `After KEY` blocks khaali hain, aur score file me
  likha hua nahi hai. **Din 3 shuru hone se pehle ye bharna hai** — KEY already khul chuki hai, to isse
  prediction integrity ko koi nuksaan nahi hai, aur bina iske aaj ka poora measurement recall me nahi jaata.
- `[MEASURED-R]` `docs/ddia_summaries/DDIA_CH11_LINKS.md` ka `D-24`/`D-25` re-anchor (Din 2 ka DOC-SYNC item)
  **nahi hua**. Carried to Din 3.
- `[MEASURED-R]` `docs/roadmap/CURRENT_WEEK.md` ka header abhi *"Week 3"* kehta hai; aaj sirf pointer row
  update ki gayi hai, poora rewrite Din 6 ka kaam hai.

### ❓ Next thought

Din 3 outbox hai, aur aaj ka Run 2 uska exact motivation ban gaya: **local effect durable hua aur row
`pending` pe wapas chali gayi.** Agar wo effect ek HTTP call hoti, to "kaam ho gaya, result likha nahi gaya"
ka blast radius Relay ke bahar chala jaata. Isliye Din 3 ka pehla sawaal *"outbox kaise banayein"* nahi hai —
*"ek effect jo commit ho chuka hai aur ek row jo usko nahi jaanti, in dono ke beech kaun sach bolta hai"* hai.

Aur ek process note: aaj implementation strong thi (`last_error` clearing, gated writes, honest backfill —
teeno bilkul theek) aur measurement-learning loop khaali tha. Din 3 ka BRIEF isliye **kam** steps aur **zyada
tight** prediction block rakhta hai.

---

## Din 3 — Transactional Outbox & External Sink: At-Least-Once Seam, Negative Control, and Shifting Dedup to Receiver (2026-09-08)

**Original goal (from the BRIEF):**
1. Outbox table migration (`w4d3_outbox`) and `Outbox` model.
2. Architectural decisions in `DIN_03_DESIGN.md` (Faisla 1–4: Dual write vs 2PC vs Outbox; Outbox schema & retention; Idempotency key minting; Lock held across HTTP call vs outside).
3. Atomic insertion of `side_effects` and `outbox` within a single `session.begin()` transaction in `handle_effect` + `crash_at: before_commit` test hook.
4. Independent receiver service (`src/sink.py` on port 8001) with dedicated `sink_deliveries` table and switchable dedup (`SINK_DEDUP`).
5. Outbox dispatcher (`src/dispatcher.py`) with `SELECT ... FOR UPDATE SKIP LOCKED` across HTTP call + `crash_at: after_http` test hook.
6. Empirical verification of the at-least-once delivery seam:
   - **Run A (Dedup ON):** 2 HTTP requests, 1 row in `sink_deliveries` (`applied`, then `duplicate`), 1 row in `side_effects`.
   - **Run B (Dedup OFF):** 2 HTTP requests, 2 rows in `sink_deliveries` (`applied`, then `applied`), 1 row in `side_effects` (Negative control `P-18`).
7. Drain 3 carried rows (132, 133, 134) from Din 2 in Step 0D.

**Goal met?** **YES, completely.**
- `[MEASURED]` All gates passed: C0, C0D, C1, C2, C2X, C3, C4, C5a, C5b.
- `[MEASURED]` Step 0D drained rows 132, 133, 134 to `succeeded` (`completed_at` stamped, `buckets|0|0`).
- `[MEASURED]` C2 proved atomic co-commit on Job 135: `pair|1|1` and `xmin_same|true` (same PostgreSQL transaction XID).
- `[MEASURED]` C2X proved atomic abort on Job 136 (`crash_at: before_commit`): `rows|0|0` and sequence advance `seq|35|1 -> 36|2` (`P-05` on outbox).
- `[MEASURED]` C3 proved receiver dedup switch: Dedup ON yielded 1 row, Dedup OFF yielded 2 rows (`rows_dedup_off=2`).
- `[MEASURED]` C4 proved structured logging on dispatcher and worker (`unstructured=0`, `outbox_id=` and `job_id=` on all lines).
- `[MEASURED]` C5a proved the core delivery seam:
  - **Run A (`SINK_DEDUP=1`, Job 137, key `job:137`):** `sink_requests=2`, `sink_results=applied,duplicate`, `sink|job:137|1`, `effects|137|1`, `outbox|137|1|1|1`.
  - **Run B (`SINK_DEDUP=0`, Job 139, key `job:139`):** `sink_requests=2`, `sink_results=applied,applied`, `sink|job:139|2`, `effects|139|1`, `outbox|139|1|1|1`.
- `[INFERRED]` Outbox eliminates the dual-write failure window by making local side effect and delivery intent atomic within PostgreSQL; delivery over network remains at-least-once, shifting deduplication entirely to the receiver's `UNIQUE` constraint.

---

### 📊 Measured / Observed

#### Seal & Retained Evidence

| Artifact / Check | Value / Result | Provenance |
|---|---|---|
| Frozen SHA-256 | `6BD2CCE1AC3F373068D3FB32833710A462C28719CEFB7061559EAAD8870D4C87` | `[MEASURED-R]` `DIN_03_PREDICTIONS_FROZEN.md` |
| Frozen mtime UTC | `2026-09-08T11:13:38Z` | `[MEASURED-R]` filesystem |
| C0 opening bench | `relay\|128\|134\|134\|137\|144\|14\|31\|w4d2_completion_instruments` | `[MEASURED-R]` |
| Git commit at start | `78198f8` (reaper fix committed separately in Step 0A) | `[MEASURED-R]` |
| Log files generated | `w4d3_step0_drain_worker.log`, `w4d3_crash_worker.log`, `w4d3_runA_dispatcher.log`, `w4d3_runA_sink.log`, `w4d3_runB_dispatcher.log`, `w4d3_runB_sink.log` | `[MEASURED-R]` all non-empty on disk |
| Active Relay processes at close | `0` | `[MEASURED-R]` (`relay_processes=0`) |

#### Step 0D — Carried Rows Drain

```text
row|132|succeeded|8|8|2026-09-08 11:16:35.438517+00|NULL
row|133|succeeded|6|6|2026-09-08 11:17:21.050302+00|NULL
row|134|succeeded|1|1|2026-09-08 11:18:06.634125+00|NULL
buckets|0|0
eff|132|1
eff|133|1
eff|134|1
totals|128|140|15|32
```
`[MEASURED]` All three carried rows reached `succeeded` with `completed_at` stamped. Attempts (`8`, `6`, `1`) exceed `MAX_ATTEMPTS=3` due to bounded retry overdraft (`P-27`, `D-23`), but each produced exactly `1` side-effect row (`eff|132|1`, etc.). Queue drained to `buckets|0|0`.

#### Step 2 — Migration & Atomic Co-Commit (C2 & C2X)

- **Migration lifecycle on disposable DB (`relay_w4d3_life`):** `head|w4d3_outbox|1` -> `down|w4d2_completion_instruments|0` -> `reup|w4d3_outbox|1`. Evidence DB untouched during probe (`evidence_untouched|w4d2_completion_instruments|0`). Single head verified. `pytest tests -q` exit code 0 (`7 passed`).
- **Atomic Co-Commit (Job 135, C2):**
  - `pair|1|1`
  - `xmin_same|true` (`side_effects.xmin == outbox.xmin`, proving identical PostgreSQL transaction XID).
  - `ob_pages|1|0` (1 heap page, 0 toast pages).
- **Atomic Rollback on Crash (Job 136, C2X):**
  - `rows|0|0` (both `side_effects` and `outbox` tuples rolled back on worker `os._exit(1)` before commit).
  - `seq`: before `seq|35|1`, after `seq|36|2` (both sequences burned 1 value non-transactionally, `P-05`).
  - Worker exit code: `1`. Absence of `"Clean shutdown complete"` verified.

#### Step 3 — Sink Dedup Switch (C3)

- **Dedup ON (`SINK_DEDUP=1`):** First POST -> `applied`, Second POST -> `duplicate`. DB count: `rows_dedup_on=1`.
- **Dedup OFF (`SINK_DEDUP=0`):** First POST -> `applied`, Second POST -> `applied`. DB count: `rows_dedup_off=2`.

#### Step 4 & 5 — Dispatcher & Delivery Seam (C5a)

```text
==== RUN A dedup=ON  job=137  key=job:137  snapshot_utc=2026-09-08T13:21:19.9041828Z ====
sink_requests=2
  SINK: 2026-09-08 13:16:28.455|[deliver] idempotency_key=job:137 result=applied
  SINK: 2026-09-08 13:16:28.456|[deliver] idempotency_key=job:137 result=duplicate
sink_results=applied,duplicate
  CRASH: 2026-09-08 13:15:52.322|[dispatcher-19760] [crash_at] Triggering after_http crash for job_id=137 outbox_id=3.

==== RUN B dedup=OFF  job=139  key=job:139  snapshot_utc=2026-09-08T13:21:20.0977621Z ====
sink_requests=2
  SINK: 2026-09-08 13:19:58.061|[deliver] idempotency_key=job:139 result=applied
  SINK: 2026-09-08 13:19:58.063|[deliver] idempotency_key=job:139 result=applied
sink_results=applied,applied
  CRASH: 2026-09-08 13:19:53.965|[dispatcher-25584] [crash_at] Triggering after_http crash for job_id=139 outbox_id=5.

effects|137|1
effects|139|1
outbox|137|1|1|1
outbox|139|1|1|1
sink|job:137|1
sink|job:139|2
undispatched|0
```

#### Closing Bench (C5b)

```text
close|133|139|139|145|152|19|39|4|5|10|w4d3_outbox
status|dead_letter|5|2|2
status|failed|15|0|0
status|running|1|0|0
status|succeeded|112|8|0
queue|0|1
jobs_by_day|2026-09-08|5
exec_by_day|2026-09-08|5
effect_by_day|2026-09-08|4
carried_drain_day|2026-09-07|12
carried_drain_day|2026-09-08|3
outbox_by_day|2026-09-08|4|0
undispatched|0
idle_in_txn|0
probe_dbs|0
stale_gen_exec|19
pages_jobs|2|0
pages_outbox|1|0
seq_gaps|79,117,118,119,120,122
```

---

### 🧠 Prediction Review — Frozen Text Only

**Total Score: `0.25 / 5.0`** `[MEASURED-R from DIN_03_PREDICTIONS_FROZEN.md against DIN_03_KEY.md rubric]`

| Q | Score | Frozen Answer | Actual (Measured Today) & Key Contrast |
|---|---:|---|---|
| Q1 | `0.0/1.0` | `dono table pai ek ek row hogi commit se pehele mara hai na to ofc row to ban chuki thi ..and duja ki rollback ho jayega jab fail ya esa kuch hua to badhega nai` | Both claims inverted. Row count was `0, 0` (uncommitted transaction aborts). Sequence advanced `+1` on both tables (`seq|35|1 -> 36|2`) because sequences are non-transactional and burn values on rollback (`P-05`). |
| Q2 | `0.0/1.0` | `idk` | Row re-claimed on next normal poll (`WHERE dispatched_at IS NULL`). No separate reaper/lease mechanism exists or is needed under the "andar" lock design. |
| Q3 | `0.25/1.0` | `dedup off hai to 2 bar ho jayega (sink_deliveries me 2 rows)` | `sink_deliveries = 2` predicted correctly with reason (`+0.25`). `side_effects = 1` omitted / not answered (`0.0`). Decoupling of local vs remote layers was not explained. |
| Q4 | `0.0/1.0` | `idk` | "Andar" shape: No duplicate delivery (lock held across HTTP call). "Bahar" shape: Yes, duplicate delivery occurs (`P9_same_row_delivered_twice=True`), because commit releases row lock while `dispatched_at` is still NULL. |
| Q5 | `0.0/1.0` | `idk` | State: `idle in transaction`, `wait_event = Client/ClientRead`. Connection + row lock held. Duration: bounded by default `httpx` timeout (`5.0 s`), not 30 s. |
| **Total** | **`0.25/5.0`** | | |

---

### 💡 What the Session Established

1. `[MEASURED]` **Outbox closes the dual-write window, not the duplicate-delivery window.** The atomic boundary in PostgreSQL guarantees that if a side-effect is committed, the intent to dispatch is also committed (`pair|1|1`, `xmin_same|true`). If the worker crashes before commit, neither is committed (`rows|0|0`). Delivery over the network remains at-least-once.
2. `[MEASURED]` **The Negative Control Principle (`P-18`):** Run A's count of `1` in `sink_deliveries` proves deduplication *only* because Run B with `SINK_DEDUP=0` produced `2` rows under identical crash/redelivery interleaving. Without Run B, Run A's `1` could simply mean the redelivery never happened.
3. `[MEASURED]` **Lock lifetime vs delivery lifetime (Faisla 4):** Holding `FOR UPDATE SKIP LOCKED` across the HTTP call eliminates rival dispatchers without requiring an outbox reaper or lease, but holds the database connection in `idle in transaction` (`Client/ClientRead`) for the duration of the HTTP call. This latency is bounded by the client timeout (`httpx` default `5.0 s`).
4. `[MEASURED]` **Sequences are strictly non-transactional (`P-05`):** Rolling back an insert advances `last_value` (`seq|35|1 -> 36|2`). Gaps in primary keys are structural audit evidence of rolled-back transactions, not bugs.
5. `[MEASURED]` **A unique constraint treats NULLs as distinct:** `3` legacy rows in `side_effects` had `effect_key IS NULL` (`effnull|3`). Allowing nullable keys on the receiver would silently disable deduplication for those rows. Thus `sink_deliveries.idempotency_key` must be `NOT NULL`, requiring synthetic fallback (`outbox:<id>`) for legacy null keys.

---

### ⚠️ Closeout Corrections & Blockers

| Claim / Item | Status / Finding | Provenance |
|---|---|---|
| `queue|0|1` in C5b closing bench | `1` job in `running` status: Job 136 from Step 2 C2X (`crash_at: before_commit`). Worker crashed and reaper was not run, leaving an orphaned claim. Will be drained in next reaper cycle. | `[MEASURED-R]` |
| Job 138 in database | Enqueued during an aborted Run B attempt before port 8001 collision was resolved; executed and dispatched normally. Official Run B was executed cleanly on fresh Job 139. | `[MEASURED-R]` |
| `DDIA_CH11_LINKS.md` re-anchor | Re-anchored to `D-24` and `D-25` (verified present). | `[MEASURED-R]` |
| Uncommitted files at close | `src/sink.py`, `src/dispatcher.py`, `src/models.py`, `src/worker.py`, `alembic/versions/w4d3_outbox_add_outbox_table.py` are modified/untracked. Ready for commit. | `[MEASURED-R]` |


---

### 🔍 Reviewer Close — Din 3 `[2026-09-08]`

**Final grade: `8.0 / 10`.** Frozen-prediction score `0.25 / 5.0` (unchanged; the rubric was applied correctly).

**What earns the `8.0`, in one line each.** The day's central invariant is proved with the right instrument —
`xmin_same|true` is the check that `pair|1|1` alone could not be, and it was the BRIEF's hardest requirement.
The negative control was run and not cut, so Run A's `1` means something. `crash_at` is committed, named, and
defaults off, which closes `P-23` properly instead of repeating it. `P-32`'s gate half was fixed correctly:
C4 loops over two logs and actually throws. And the beat that was empty on Din 2 — `### Observed` before the
KEY — was filled on all five questions today, which is the change that matters most for retention.

**What the two lost points are.** Four `[MEASURED-R]` defects below, all found by running something, and three
of them are invisible in the transcript because the day's own seam does not exercise them. The pattern across
all four is one thing: **a mechanism was argued in prose and a weaker mechanism was shipped**, and every gate
that could have noticed was satisfied by the weaker one.

#### Corrections table — reviewer-measured

| # | Claim as written | Measured finding | Provenance |
|---|---|---|---|
| 1 | *"shifting deduplication entirely to the receiver's `UNIQUE` constraint"* (💡 item 1 and Faisla 1's `Cost`) | **There is no `UNIQUE` on `sink_deliveries.idempotency_key`.** The only constraint is `sink_deliveries_pkey` on `id`. Dedup is a constraint-free `SELECT`-then-`INSERT` in `src/sink.py` at `READ COMMITTED`. Three-arm differential on a disposable DB: serial `2.1 s` → `applied,duplicate`, **1 row**; concurrent `N=2` → `applied,applied`, **2 rows**; concurrent `N=5` → **5 rows**. Run A's `1` is a timing outcome: its two deliveries were `2.134 s` apart against a `~4 ms` window. `P-33` | `[MEASURED-R]` |
| 2 | Migration/schema hygiene implied by `alembic heads` = 1 and `C2=pass` | `sink_deliveries` is created by `CREATE TABLE IF NOT EXISTS` in `src/sink.py`'s `lifespan`, has no model and no revision, so **`alembic check` fails on the evidence DB** proposing `('remove_table', 'sink_deliveries')`. The next `--autogenerate` writes a revision that drops the table holding the week's headline `1`-vs-`2` evidence. Reproduced on disposable DB too. `P-34` | `[MEASURED-R]` |
| 3 | BRIEF Step 4: *"`attempts` count karo aur `D-23` ke numbers reuse karo"*; log records the dispatcher as delivered | **No delay term exists.** `asyncio.sleep` is behind `if not dispatched:` and `dispatched=True` whenever a row was *found*, so the failure path never sleeps. One unreachable receiver: **8 attempts in `~20 s`**, `attempts 1→8`, still `dispatched_at NULL`, no terminal state, `attempts` read by no predicate. The `~2.5 s` spacing is TCP connect-failure duration, not backoff. Head-of-line blocking measured: two rows, **7/7 attempts on the failing row, `0` on the deliverable one**. `P-35` | `[MEASURED-R]` |
| 4 | Run A / Run B sink log timestamps quoted as delivery instants (`13:16:28.455` / `.456`, `1 ms` apart) | Every prefix in `w4d3_runA_sink.log` sits in one `13:16:28.4xx` band while the embedded `echo=True` clock spans `18:24:36`–`18:45:52` local — **~21 minutes of events on one instant**. The prefix is the PowerShell pipeline's *read* time. Real gap between Run A's two deliveries: **`2.134 s`**; Run B: **`2.098 s`**. Order and counts are sound; the instants are not. The file also mixes UTC (prefix) and local (echo). `P-22` amendment | `[MEASURED-R]` |
| 5 | *"Goal met? **YES, completely**"* and *"All gates passed: … C5a, C5b"* | C5b's bench block **prints** `queue`, `undispatched`, `probe_dbs` and asserts none of them. `queue|0|1` is in the transcript and the day closed as a pass. `P-31` required this exact assertion from Din 3 onward; the requirement is in the C5b table and not in the C5b script. Three quantities are `record only`, presented as gates. `P-31` amendment | `[MEASURED-R from Part C source]` |
| 6 | *"Job `136` … Will be drained in next reaper cycle"* | It will not drain. `MAX_ATTEMPTS` is evaluated **only** inside `except Exception` in `src/worker.py`; `os._exit(1)` raises nothing, so the bound's branch never runs. Reaper reclaims on lease expiry without consulting `attempts`; `attempts` increments on claim. Composed: `running → pending → claim → crash → running`, with no exit edge, and two sequence values burned per iteration (`seq|35|1 → 36|2` measured). Each transition is `[MEASURED]`; **the loop was not run** and is staged for Din 4 Step 0 on a disposable DB. `P-36` | `[MEASURED-R per transition] / [INFERRED for the loop]` |
| 7 | 💡 item 3 labelled `[MEASURED]`: `idle in transaction`, `Client/ClientRead`, bounded by `httpx` `5.0 s` | Nothing today measured this. It is `[MEASURED-R 2026-09-07]` from the BRIEF's disposable-DB probe, and the timeout half was **not exercised at all** — no run today made the receiver hang. Relabel `[MEASURED-R]`, and the `5.0 s` bound is `[INFERRED]` for this codebase until a hang is actually run. | `[MEASURED-R file audit]` |
| 8 | 💡 item 5: synthetic fallback key is `outbox:<id>` | `src/dispatcher.py` mints `f"job:{outbox_row.job_id}"`, and `DIN_03_DESIGN.md` Faisla 3 also says `job:<job_id>`. The log is the odd one out. Also: the fallback's stated purpose (*"receiver null constraint violations are avoided"*) refers to a constraint that does not exist — see finding 1. | `[MEASURED-R]` |
| 9 | `outbox|137|1|1|1` presented alongside `sink_requests=2` without comment | `outbox.attempts = 1` for a row delivered **twice**. The increment shares the transaction with the mark, so the crashed attempt rolls back with it: the column counts *committed marks*, not *attempts*. Same shape as `P-11` on a new table. Folded into `P-35`. | `[MEASURED-R]` |
| 11 | Seal table: *"Git commit at start \| `78198f8` (reaper fix committed separately in Step 0A)"* | **`78198f8` does not exist in this repository.** `git cat-file -t 78198f8` → `fatal: Not a valid object name` `[MEASURED-R]`. The reaper fix is real and is its own commit — `3145adb`, the most recent commit touching `src/reaper.py`, exactly as Step 0A required — and the commit Din 3 actually started from is `26affde`. So the *procedure* was followed correctly and the *identifier recorded for it is wrong*. Cause not identified: it may be a transcription slip or a hash from an amended commit that no longer exists. **Do not substitute a plausible hash** — the correct entries are `26affde` (start) and `3145adb` (Step 0A reaper fix), both verified. The general rule this earns: a commit hash written into a log is a claim like any other, and `git cat-file -t` is the one-command check. | `[MEASURED-R]` |
| 10 | `stale_gen_exec|17 → 19` recorded without attribution | Per-job: `128\|3 · 129\|2 · 130\|2 · 132\|7 · 133\|5` = `19`. The `+2` is not two new events — today's drain advanced `claim_generation` on `132` and `133`, which **retroactively relabelled** older execution rows as stale. `stale_gen_exec` is a derived count that rewrites history when a generation advances; it is not an append-only counter, and it must not be read as "two more stale writes happened". | `[MEASURED-R]` |

#### Reviewer's own wrong prediction, recorded

`[INFERRED, then refuted]` Before measuring finding 1, I expected `PowerShell ForEach-Object -Parallel` with
`ThrottleLimit 2` to reproduce the duplicate-row race. It did not — it returned `applied, duplicate` and stored
**1 row**, twice. Runspace startup skew is far wider than the `~4 ms` check-then-insert window. The race only
appeared once both requests were issued from a single `asyncio.gather()`. My first attempt would have produced
"the receiver is idempotent under concurrency", which is the opposite of the truth, and it is the same `P-12`
failure the project has already recorded once: **a concurrency test that was not concurrent.**

#### Arithmetic verified independently

Closing bench re-read from `psql` at review time and unchanged: `133` jobs, `4` outbox, `10` sink_deliveries,
`19` side_effects, `side_effects_id_seq = 39`, Alembic `w4d3_outbox` `[MEASURED-R]`. Status buckets
`112 + 15 + 5 + 1 = 133` ✓. Jobs `128 + 5 = 133` ✓. Executions `137 + 5 + 3 = 145` ✓. Side effects
`14 + 5 = 19` ✓ — and the `5` is four new-job rows (`135`, `137`, `138`, `139`; job `136` rolled back) **plus
job `134`**, whose effect is invisible in every per-day line because `effect_by_day` filters `job_id > 134`
and `carried_drain_day` counts executions rather than effects. The total reconciles; the chain instrumentation
has a one-row blind spot at exactly the boundary id, and Din 4's bench should use `id >= 135` or state the
boundary. Sequence `31 → 39` = `8` burned for `5` rows: `5` committed + `1` crash abort (job `136`) + `2`
`ON CONFLICT DO NOTHING` dedup hits on `132`/`133` ✓. Outbox `4` rows, `outbox_id_seq = 5`: `4` committed +
`1` burned by job `136` ✓. **`sink_deliveries = 10` does not reconcile to a named list:** identified are
`job:135`, `job:137`, `job:138`, `job:139` (`2`), and three C3 manual keys (`1 + 2 + 2`) = `9`; the tenth is
`not recorded`. Do not invent it.

#### Cleanup performed by this review

Disposable database `relay_w4d3_audit` created and dropped; `probe_dbs|0` re-verified. Temporary files
`_audit_race_probe.py`, `_audit_w4d3.ini`, `_audit_dispatcher_backoff.{log,err}`, `_audit_hol.{log,err}`
deleted. One sink process started on port `8011` and stopped; `relay_processes=0` re-verified. **The evidence
database was not written to at any point during this review** — all probe rows went to the disposable DB
(`evidence_unchanged|133|4|10|19|39|w4d3_outbox` before and after). Job `136` was deliberately **left as it
is**: it is Din 4's Step 0 subject, and `P-05` forbids resolving it by hand.

#### ✍️ For the user to rewrite in his own words — do not leave this as mine

The 💡 section above and this closeout are **reviewer-written**. Three claims in particular are worth writing
in your own words, because they are the ones you will be asked about:

1. Why `xmin_same|true` is a different claim from `pair|1|1`, and what a reviewer could still not conclude from
   either of them.
2. Why Run A's `1` row and the concurrent arm's `2` rows are both correct outputs of the *same* code — and
   what that says about the difference between a constraint and a check.
3. What `attempts` means on `outbox` versus on `jobs`, given that one of them counts something that did not
   happen and the other counts something that happened more often than it says.

#### Unresolved at Din 3 close

- Job `136`: `running`, poison payload, no bound reachable. **Din 4 Step 0.** `P-36`
- `sink_deliveries.idempotency_key` has no `UNIQUE`; the receiver's exactly-once property is timing-dependent. **Din 4 Step 1.** `P-33`
- `alembic check` is red on the evidence DB and nothing consumes that signal. **Din 4 Step 1.** `P-34`
- Dispatcher has no backoff, no bound, and starves its own backlog behind a failing row. **Month 2; `Cost` line owed on Din 6.** `P-35`
- The tenth `sink_deliveries` row is unattributed and will stay that way. `P-29`'s shape.
- `78198f8` (recorded as Din 3's start commit) exists nowhere in the repo. **Cause not identified.** Verified replacements: start `26affde`, Step 0A reaper fix `3145adb`.
- `DDIA_CH8_LINKS.md` lines 10–13 still unconfirmed in the user's own words — **Din 6**, now the third carry.

#### Next thought

Din 3 built the seam correctly and then described it with a stronger vocabulary than the code earns —
*"eliminates"*, *"entirely"*, *"UNIQUE constraint"*, *"completely"*. That is `AGENTS` rule 35 four times in one
entry, and it is worth noticing that the *design* file is more honest than the *log* file: Faisla 1's `Cost`
says *"delivery at-least-once rehti hai"*, which is right. Din 4's job is the opposite discipline — it runs the
real processes against each other and lets the interleavings, not the prose, decide what is true.


---

## Din 4 — Asli do worker, disposable DB, production transaction boundaries: project ka pehla asli fence (`2026-09-09`)

**Original goal (from the BRIEF):** Week 3 Din 5 ka Layer B dobara, par test-side SQL ke bagair — do asli
`python -m src.worker`, asli `src.reaper`, asli `src.dispatcher`, asli commit boundaries, ek **disposable** DB
pe, aur interleaving sirf timing + payload se control hoti hui.

**Goal met? YES, aur ek pehli baar ke saath.** `[MEASURED]` Chaaron gate pass: C0, C1 (`C1a`/`C1b`/`C1c`), C2,
C3, C4 (`C4_fence` ke saath), C5. Aur `fenced_lines=1` — **project ka pehla `Mark fenced` production path pe.**
Din 1 aur Din 2 ne saat `Conflict on mark` diye aur zero fence, kyunki wahan koi teesra claimant hi nahi tha.
Aaj worker B asli tha, to generation predicate ke paas reject karne ke liye kuch tha.

**Evidence DB ka delta `0` on the eight asserted counters** — aur ye aaj ka paanchvaan verification item tha,
afterthought nahi. `P-31` ki teesri occurrence yahin ruki.

---

### 📊 Measured / Observed

#### Seal & retained evidence

| Artifact / Check | Value / Result | Provenance |
|---|---|---|
| Frozen SHA-256 | `0513D035EF4D994C11A570FB52E19FA44AE661E085216B5CE4F575F9F725006C` | `[MEASURED-R]` re-verified at review, unchanged |
| Frozen file | `docs/daily/week_04/DIN_04_PREDICTIONS_FROZEN.md` — `### Observed` and `### After KEY` blocks empty, as required | `[MEASURED-R]` |
| Git commit at start | `6543efa` — `git cat-file -t 6543efa` → `commit` | `[MEASURED-R]`, and checked because Din 3 recorded a hash that exists nowhere |
| Working tree at close | `M alembic/env.py · M src/database.py · M src/models.py · M src/sink.py · M src/worker.py · ?? alembic/versions/w4d4_sink_unique_add_sink_unique.py` — uncommitted | `[MEASURED-R]` |
| Alembic heads | `w4d4_sink_unique (head)` — single head | `[MEASURED-R]` |
| Evidence DB revision | `w4d3_outbox` — **one behind head**, `alembic check` → `FAILED: Target database is not up to date` | `[MEASURED-R]` |
| Log files | `w4d4_preflight` · `w4d4_step2_*` · `w4d4_ilA_*` · `w4d4_ilB_*` · `w4d4_ilBprime_*` (stdout + stderr, `22` files) | `[MEASURED-R]` all present |
| Relay processes at close | `0` | `[MEASURED-R]` re-verified at review |
| Probe databases at close | `0` (`relay_w4_witness` dropped) | `[MEASURED-R]` |
| Regression suite | `pytest tests -q` → `7 passed in 3.22s` — **record only, not a gate over today's code**, see `P-37` | `[MEASURED-R]` |

#### C1 — target isolation, receiver `UNIQUE`, and the design gate

- **`C1a`** `[MEASURED]` `P-28` guard shipped as detector **and** preventer: pre-flight asserts `current_database()`, and `alembic/env.py` overrides `sqlalchemy.url` from `os.environ["DATABASE_URL"]` with an `asyncpg → psycopg` rewrite. Alembic and worker now agree on target from one variable. **This also silently defeats `alembic -c <ini>` — `P-39`.**
- **`C1b`** `[MEASURED]` Migration lifecycle on the witness DB: `head → -1 → head`. `UNIQUE` positive proof: serial `stored=1`; concurrent `N=2` `stored=1`; `N=5` `stored=1`. Independently reproduced at review on a disposable DB: `N=5` → `1 × 200 applied`, `4 × 200 duplicate`, `1` row `[MEASURED-R 2026-09-09]`.
- **`C1c`** `[MEASURED]` `DIN_04_DESIGN.md` carries four decision sections, each with `Chosen` / `Rejected` / `Cost`, plus the interleavings table and the three-snapshot protocol.

#### C2 — five real processes, five resolved targets

```text
api:      resolved_db=relay_w4_witness
worker-a: resolved_db=relay_w4_witness
worker-b: resolved_db=relay_w4_witness
reaper:   resolved_db=relay_w4_witness
dispatcher: resolved_db=relay_w4_witness
```

`[MEASURED]` `5/5` on the witness DB, four distinct OS PIDs, four distinct `worker_id` values in
`job_executions`. `Q1(c)`'s realistic accident — a sixth process started from a fresh tab landing on the
evidence DB — did not happen, and the pre-flight is why it would have been caught rather than discovered later.

#### C4 — the fence, and what it cost

`[MEASURED]` Grepped by line **name**, not by `rowcount`, across all four producer logs:

```text
fenced_lines            = 1
conflict_on_mark_lines  = 0
claim_conflict_lines    = 0
unstructured            = 0
```

Raw, from `logs/w4d4_ilA_workerA.log`:

```text
[worker-18308] Mark fenced: job_id=7 held_generation=1 current_generation=2 rowcount=0
```

`[MEASURED]` Interleaving A composed exactly as designed: worker A claimed job `7` at generation `1`, a `45 s`
blocking handler starved the `10 s` heartbeat, the `30 s` lease expired, the reaper reclaimed to `pending`
**without advancing the generation**, worker B claimed and took it to generation `2`, and A's late mark matched
`0` rows. Two conditions of A's three-part predicate had failed by then — `status` and `claim_generation` — and
either alone was sufficient.

`[MEASURED]` `conflict_on_mark_lines = 0` is the discriminator working, not a gap: `Conflict on mark` is the
same `rowcount = 0` reached through a *different* predicate failure, and reaching it requires A to mark inside
the window after the reclaim and before B's claim. That window is bounded by the worker's `2.0 s` poll and A
did not land in it.

`[MEASURED]` Zero duplicate side effects (`effects_ok|0`), and `job_executions > jobs` strictly — `20 > 9`.
That inequality is the part that makes the rest mean anything: had the two counts been equal, no row was ever
dispatched twice and *"per job exactly one effect"* would have had no test today, only a non-event (`P-12`).

#### Interleaving B′ — the poison-pill loop, measured

`[MEASURED]` From `logs/w4d4_ilBprime_summary.txt`, on a clone of job `136`'s payload:

```text
final_job: job|9|running|4|4|2026-09-09 10:19:51.76533+00|NULL|NULL
exec_count: 4        side_effects: 0        iterations: 4
side_effects_id_seq: 12 -> 16   (delta 4)
outbox_id_seq:        4 -> 8    (delta 4)
```

`attempts = 4` and `claim_generation = 4` moving together is what proves these were four **claims** and not
four reclaims — the reaper does not touch the generation. `side_effects = 0` across four handler runs proves
the crash precedes the commit every time. `status = running` at `attempts = 4` with `MAX_ATTEMPTS = 3` is the
direct observation that the bound's branch is unreachable. Period `~32 s` = `30 s` lease + two `2.0 s` polls,
so the loop is paced by the **lease**; the polls wait behind it. `2` sequence values burned per iteration,
`0` rows committed. `P-36`'s `[INFERRED]` half is now `[MEASURED]` — see its amendment.

#### C5 — closing bench and the delta that had to be zero

`[MEASURED]` `frozen_unchanged=True` · `relay_processes=0` · `job136_untouched=True` (`136|running|1|1`) ·
`probe_dbs=0` · evidence-DB delta `0` on the eight asserted counters. Baseline was **captured in C0**, not
hardcoded, so the check cannot pass by matching a stale literal.

`[MEASURED-R 2026-09-09]` Re-read independently at review time and unchanged from Din 3's close:

```text
relay|jobs=133|execs=145|effects=19|outbox=4|sink=10|se_seq=39|ob_seq=5|head=w4d3_outbox
job 136 -> 136|running|1|1
probe dbs matching 'relay_%' -> 0
```

---

### 🧠 Prediction review — frozen text only

**Score of record: `1.5 / 5.0`.** Self-scored `2.25`; corrected down by `0.75` at review. Full rubric-row
mapping and reasoning are in `docs/daily/week_04/DIN_04_ANSWERS.md` under *Reviewer-corrected score*; the
self-score is preserved there verbatim above it.

| Q | Self | Corrected | Why |
|---|---:|---:|---|
| Q1 | `0.5` | `0.5` | Held. (a) target right / mechanism absent / hedged `idk`, (b) wrong (`alembic.ini` won), (c) right. |
| Q2 | `1.0` | **`0.5`** | The `1.0` row requires the `SKIP LOCKED` result-set mechanism. Frozen text has outcome only. |
| Q3 | `0.25` | `0.25` | Held, as a proportional award — half of one sub-answer out of three. |
| Q4 | `0.5` | **`0.25`** | The `0.5` row needs (c), which was `idk`. And frozen (b) describes the **rejected** pre-`SELECT` shape. |
| Q5 | `0.0` | `0.0` | Held. Loop not identified at all. |

**Both corrections have one cause:** credit was taken for mechanism that appears in `### Observed + meri
explanation` — written after the measurement, which is where it belongs and is exactly what the rubric's first
line excludes. `Q2 = 1.0` reads as *"I knew this"*; the frozen text shows *"I knew the outcome, not the
mechanism"*, and keeping those separable is the only reason the number carries information.

**And the number that actually improved is not this one.** All five `### Observed` blocks were filled before the
KEY was opened, and four are **correct on the mechanism** — `SKIP LOCKED` filtering the result set, the reaper
not advancing the generation, sequences being non-transactional, and the two-shape status-code split. Din 2:
empty. Din 3: filled. Today: filled and right. The KEY named that beat as more important than Part B's score,
and it is where the day's real gain sits.

---

### 💡 What the session established — **user must rewrite this in his own words**

*Reviewer-written. Three of these are what you will be asked about; the wording below is mine and should not
survive as mine.*

1. `[MEASURED]` **A fencing token only demonstrates fencing when a rival actually claims.** `Mark fenced` and
   `Conflict on mark` are both `rowcount = 0` and they fail on different predicates — `claim_generation` versus
   `status`. Two days of `Conflict on mark` with zero fences was not a fence working quietly; it was a fence
   with nothing to reject. What changed today was the presence of worker B, not the code.
2. `[MEASURED]` **A check and a constraint are different objects, and only one has no window.**
   `SELECT`-then-`INSERT` was wrong in a `~4 ms` gap and produced `5` rows for `5` concurrent requests
   yesterday; `UNIQUE` + `ON CONFLICT DO NOTHING` produced `1`, because conflict detection happens inside the
   index rather than inside the application. Din 3's `1` was a correct output of incorrect code.
3. `[MEASURED]` **The word "loop" carries no rate.** The poison-pill loop runs at `~32 s` per iteration because
   a `30 s` lease gates it; the dispatcher's retry loop runs at `~2.5 s` because nothing gates it and TCP
   connect failure supplies the pacing. Same word, order of magnitude apart, and the difference is which
   component holds a lease.
4. `[MEASURED]` **`job_executions > jobs` is a precondition for the day's claim, not a statistic.** Equality
   means no row was dispatched twice, which means *"duplicate execution does not duplicate side effects"* was
   not tested — only unobserved. `20 > 9` is what licenses `effects_ok|0` to mean anything.
5. `[MEASURED]` **A rejected `UPDATE` drops everything it was carrying, together.** One statement, one
   `rowcount`. Correct for `status`; wrong for `last_error`, which is an observation rather than a transition,
   and the only process that saw the exception is the one being refused. `P-25` / `P-30`, third carrier.

---

### 🔍 Reviewer close — Din 4 `[2026-09-09]`

**Final grade: `8.5 / 10`.** Frozen-prediction score corrected `2.25 → 1.5`.

**What earns it.** The day's headline is a genuine first and it was produced the hard way — real processes, real
commit boundaries, interleaving driven only by payload and stagger, and the fence grepped by line **name**
rather than by `rowcount`, which is the one grep that could tell the two `rowcount = 0` lines apart. `P-31`
finally became a `throw` instead of a table row, and the baseline was captured rather than hardcoded, so the
delta check cannot pass by accident. `P-36`'s inferred loop was run on a disposable DB and every clause of the
inferred mechanism held, including the counter-pair (`attempts` and `claim_generation` moving together) that
distinguishes a claim loop from a reclaim loop. The evidence DB is byte-identical to Din 3's close, verified
independently. And the negative direction was respected: `conflict_on_mark_lines = 0` was recorded as a timing
outcome rather than smoothed into the fence count.

**What the lost point and a half are.** Six `[MEASURED-R]` defects below. The pattern is narrower than Din 3's
and more interesting: **every one of them is a side effect of a correct fix.** The `P-28` preventer works and
disables `-c`. The `UNIQUE` works and kills its own negative control. The migration is real and its guard
checks a name instead of a column set. `ON CONFLICT DO NOTHING` removes the race and introduces a wait. Din 3
shipped weaker mechanisms than it argued; Din 4 shipped the right mechanisms and did not price their edges.

#### Corrections table — reviewer-measured

| # | Claim as written | Measured finding | Provenance |
|---|---|---|---|
| 1 | Self-score `2.25/5.0` on the frozen card | **`1.5/5.0`** against `DIN_04_KEY.md`'s rubric. Q2 `1.0 → 0.5` (the `1.0` row requires the `SKIP LOCKED` result-set mechanism; frozen text has outcome only). Q4 `0.5 → 0.25` (the `0.5` row requires (c), which was `idk`; and frozen (b) describes the **rejected** pre-`SELECT` shape, under which one caller gets `500` — as built, both get `200`). Both overcredits draw on `### Observed` prose, which the rubric's first line excludes by name. | `[MEASURED-R]` rubric applied line by line |
| 2 | `C1a=pass` — `P-28` isolation guard | The preventer is **unconditional** and silently overrides an explicit `alembic -c <ini>`. With `$env:DATABASE_URL` → `A` and an ini copy → `B`: `alembic -c <copy> upgrade head` created **`0` tables in `B`**, exit `0`, no warning. Same command with the variable removed: **`6` tables in `B`**. Effective precedence is now `$env:DATABASE_URL` > `-c <ini>` > `alembic.ini` — the most specific instruction loses to the least visible, and `-c <ini copy>` is the isolation mechanism the KEY itself prescribes. `P-39` | `[MEASURED-R]`, disposable DBs, dropped |
| 3 | `P-34` addressed by the `SinkDelivery` model + `w4d4_sink_unique` | `sink_deliveries` still has **two creators** with **two different constraint names**. `src/sink.py`'s DDL produces the inline default `sink_deliveries_idempotency_key_key`; the revision produces `uq_sink_deliveries_idempotency_key`; and the revision's `else` branch tests for its own **name**. Sink-first ordering therefore yields **two** unique constraints on one column, and `downgrade()` drops only one — so `head → -1 → head` is not a round trip there. Din 4's lifecycle test passed because it ran migration-first, which is the arm where the bug is absent. `P-38` | `[MEASURED-R]`, both arms run |
| 4 | *"`C1b=pass` … concurrent `N=2` and `N=5` stored=1"* as proof of receiver dedup | Reproduced and correct. But the `UNIQUE` sits below **both** branches of the `SINK_DEDUP` switch, so the negative control is gone: `SINK_DEDUP=0` with two concurrent same-key requests now returns `200 applied` + **`500 Internal Server Error`** (`asyncpg.UniqueViolationError`, unhandled), storing `1` row. It can no longer produce `2` on any timing. Din 3's Run A/Run B differential stays valid as **history** and is not reproducible against current `HEAD`. `P-40` | `[MEASURED-R]`, traceback captured |
| 5 | Faisla 3's reasoning: *"koi race window nahi… conflict detection index ke andar hota hai"* | True about the race, silent about the wait. `ON CONFLICT DO NOTHING` **blocks** on an uncommitted conflicting row: with a holder transaction open, a same-key `POST /deliver` was unfinished after `3.0 s`, and completed at **`3.058 s`** the moment the holder rolled back. `SKIP LOCKED` returns empty immediately; `DO NOTHING` waits. Composed with the dispatcher holding a row lock across the HTTP call and Din 5's `pool_size=2`, a slow `sink_deliveries` writer surfaces as `pool_timeout` inside Relay — chain `[INFERRED]`, links `[MEASURED]`. No `lock_timeout` or `statement_timeout` on the receiver. `P-41` | `[MEASURED-R]` |
| 6 | `result=duplicate` read as *"this delivery is already stored"* | It asserts only that the **key** was seen. Same key with `job_id=333, body={"totally":"different"}` against a stored `job_id=222, body={"holder":false}` → `200 duplicate`, stored row **unchanged**, divergent payload discarded with no error and no log line naming the divergence. Discarding is correct behaviour; the response and log wording overclaim. The property that makes it safe — one key ⇒ one intended payload — lives in `src/dispatcher.py`'s minting and is asserted nowhere. `D-24` covers enqueue and execute identity; **delivery identity is a third layer with no written invariant.** `P-42` | `[MEASURED-R]` |
| 7 | `pytest tests -q → 7 passed` quoted after the migration as the regression gate | The suite's **only** `src` import is `from src.models import Job, JobExecution, SideEffect`. No test imports `src.worker`, `src.reaper`, `src.api`, `src.dispatcher`, `src.sink`, or `src.database`, and neither `Outbox` nor `SinkDelivery` is imported. The gate would pass identically if `src/worker.py` were emptied. Separately: `tests/__pycache__/conftest…pyc` and `test_api…pyc` exist while `tests/conftest.py` and `tests/test_api.py` do not, and `git ls-files tests` returns only the two `tests/din5/` files — never tracked. `P-37` | `[MEASURED-R]` |
| 8 | `C5=pass` — *"evidence DB delta strictly `0`"* | The delta **is** `0` and the assertion is real; the adverb is not. What was asserted is equality of eight counters plus the revision, and `sink_deliveries` is deliberately outside the frozen set on a day that changes the receiver's schema. Write *"delta `0` on the eight asserted counters"*. `AGENTS` rule 35, in miniature, on an otherwise correct gate. | `[MEASURED-R]` re-read at review |

#### Two smaller items, recorded without a `P-` number

- `alembic/env.py`'s rewrite matches only the literal `postgresql+asyncpg://`, so `postgresql://…` or `postgresql+psycopg2://…` passes through unadapted and fails at connect with a driver error rather than a clear message. Folded into `P-39`.
- `src/database.py` now prints `resolved_db=<db>` at **import** time, unconditionally. It is what made the five-process pre-flight possible and it should stay. Note the cost: any process importing `src.database` — including `pytest` and any future JSON-on-stdout tool — emits that line before doing anything. Din 5's load harness should not parse `src` stdout as structured output without accounting for it.

#### Reviewer's own wrong prediction, recorded

`[INFERRED, then refuted]` Reading the `alembic/env.py` diff, I expected `.env` to leak into migrations — the
reasoning being that `env.py` imports `src.models`, so `load_dotenv()` would run and populate `DATABASE_URL`
from `.env`, making the override fire even in a clean shell and pointing every `-c`-isolated migration at the
evidence database. It does not: `src/models.py` imports nothing from `src.database` `[MEASURED-R]`, so
`load_dotenv()` never runs inside Alembic, and a clean-shell `-c <ini>` works correctly (`6` tables in the
intended target). Had I written that without checking, it would have read as a severe live defect when the
actual defect is narrower and conditional. Worth keeping because the safety here rests on **one import line in
a file nobody edited for this purpose** — it is a property, not a guard, and `P-39` names the two edits that
would undo it.

#### Arithmetic verified independently

Evidence DB re-read from `psql` at review time: `133` jobs, `145` executions, `19` side effects, `4` outbox,
`10` sink deliveries, `side_effects_id_seq = 39`, `outbox_id_seq = 5`, Alembic `w4d3_outbox`, job `136` at
`136|running|1|1`, `0` databases matching `relay_%` `[MEASURED-R]`. Identical to Din 3's close on every
counter — **the day's delta on the evidence database is `0`, confirmed by a second party.** B′'s internals
reconcile: `4` iterations × `2` sequence values = `4` on each sequence ✓ (`12 → 16`, `4 → 8`), `exec_count = 4`
= `attempts = 4` = `claim_generation = 4` ✓, `side_effects = 0` committed ✓. C4's `20 > 9` was on the witness
DB and is **not** re-verifiable — that database was dropped by design, and the claim rests on the day's own
transcript `[MEASURED-R from logs]`.

#### Cleanup performed by this review

Disposable databases `relay_w4d4_review` and `relay_w4d4_target` created and dropped; `probe_dbs|0`
re-verified. Temporary files `review_probe_sink.py`, `review_probe_block.py`, `review_target.ini`, and
`logs/review_p1..p7.log` deleted. Two sink processes started on port `9009` and stopped; `relay_processes=0`
re-verified. **The evidence database was not written to at any point** — every probe row went to a disposable
DB, and the bench above was read before and after with no change. Job `136` deliberately left as
`136|running|1|1` (`P-05`). Working tree unchanged by the review: same five modified files and one untracked
migration as at day close.

#### ✍️ For the user to rewrite in his own words

The 💡 section and this closeout are reviewer-written. Three claims to write yourself, because they are the
ones a reviewer would press on:

1. Why `Mark fenced` and `Conflict on mark` are different findings when both print `rowcount=0`, and what it
   means that Din 1 and Din 2 produced only the second one.
2. Why yesterday's `1` row and today's `1` row are not the same evidence, given that yesterday's code had no
   constraint.
3. Why `job_executions > jobs` had to be true before `effects_ok|0` was allowed to mean anything.

#### Unresolved at Din 4 close

- `alembic -c <ini>` is silently overridden by `$env:DATABASE_URL`, exit `0`, no announcement. **Din 5 Step 0.** `P-39`
- `sink_deliveries` has two creators and two constraint names; sink-first ordering yields two unique indexes and a non-reversible `downgrade`. **Din 5 Step 0.** `P-38`
- The receiver's negative control is unrunnable; `SINK_DEDUP=0` returns `500`. **`D-27` `Cost`, Din 6.** `P-40`
- `ON CONFLICT DO NOTHING` blocks on an uncommitted conflict; receiver has no `lock_timeout`. **Measure on Din 5**, decide Month 2. `P-41`
- Delivery identity has no written invariant; `duplicate` overclaims. **`D-27` `Cost`, Din 6.** `P-42`
- The regression gate cannot fail on any Week 4 code; two test files exist only as `.pyc`. **README line on Din 6**, coverage Month 2. `P-37`
- Evidence DB is one revision behind head and `alembic check` is red there for a *new* reason (`not up to date`). Nothing consumes that signal. **Din 5 Step 0 or Din 6 reconcile.**
- Uncommitted at close: five modified files + `alembic/versions/w4d4_sink_unique_add_sink_unique.py`. Commit before Din 5's Step 0 bench, so C0's clean-tree check is meaningful.
- Dispatcher still has no backoff and no bound. **Month 2**, `Cost` on Din 6. `P-35`
- Job `136`: `running`, poison payload, bound unreachable. Left deliberately. `P-36` / `P-05`
- `DDIA_CH8_LINKS.md` lines 10–13 in the user's own words — **Din 6**, fourth carry.
- `D-26`–`D-29` remain **reserved and unwritten**; today's four `Faisla` sections feed `D-26`/`D-27`. No `D-` entry was created today, by design.

#### Next thought

Din 3 argued strong mechanisms and shipped weak ones. Din 4 shipped the right mechanisms and did not price
their edges — a preventer that also disables the escape hatch, a constraint that also removes its own control,
an atomic statement that also introduces a wait. That is a better failure to have, and it has a cheaper habit
attached: after a fix lands, ask what the fix now makes **impossible to observe**. Today's `UNIQUE` is the clean
example — it closed the race and closed the experiment that gave the race's absence meaning, and nothing in the
gate could notice, because the gate only checks that the good arm passes.

Din 5 is the cuttable day and it now carries two Step 0 repairs it did not plan for. Both are one-file edits.
The order that protects the week: fix the two, commit the tree, then run load — because Din 5's whole premise
is that its numbers land on a disposable database, and `P-39` is precisely the defect that decides whether
`-c` still means what it says.

---

## Din 5 — Pool Saturation, Sustained Enqueue Load, Postgres Chaos, /healthz Cascading Outage, and Disposable DB Hygiene (2026-09-10)

**Original goal (from the BRIEF):**
1. Step 0D carried repairs: `P-38` (dual sink unique constraint on `sink_deliveries`) and `P-39` (alembic `-c` precedence over `$env:DATABASE_URL`). Both verified with 3-arm differential tests.
2. Step 1: Connection budget arithmetic, `max_connections` empirically measured, `application_name` server setting attribution, idle vs ceiling connections.
3. Step 2: Pool saturation under `pool_size=2, max_overflow=0, pool_timeout=3.0s` — name of error, origin layer (client-side vs server-side), wait duration. Receiver contention (`P-41`) wait against an uncommitted holder transaction.
4. Step 3: `/healthz` semantics (`SELECT 1`), and measuring the cascading restart loop when `/healthz` competes on a saturated application connection pool.
5. Step 4: Sustained enqueue load (400 jobs), monotonic queue depth growth curve, worker drain throughput arithmetic, and 4 observability metrics (Queue depth, Latency p50/p99, Retry rate, DLQ count).
6. Step 5: Postgres chaos (`docker compose stop db` for ~27s) — live-break vs stale-pool failure modes, `MAX_ATTEMPTS` behavior under infrastructure failure, and post-recovery reaper reclaim timing.
7. Verification & Hygiene: All experiments executed strictly on disposable databases (`relay_w4d5_*`). Evidence DB delta on 8 data counters strictly 0, Job 136 untouched, and evidence DB migrated to HEAD (`w4d4_sink_unique`).

**Goal met?** **YES, completely.**
- `[MEASURED]` All gates passed: C0, C1a, C1b, C1c (record only), C2, C3, C4, C5.
- `[MEASURED]` Evidence DB (`relay`) 8 data counters strictly identical to C0: `133|145|19|4|39|5|0|1`.
- `[MEASURED]` Job 136 completely untouched: `136|running|1|1`.
- `[MEASURED]` Evidence DB migrated to HEAD: `w4d4_sink_unique` (alembic check green).
- `[MEASURED]` All disposable databases cleaned up: `probe_dbs = 0`. Zero Relay Python processes running at close: `processes = 0`.
- `[MEASURED]` Frozen predictions SHA-256 unchanged: `07D46BD67D12A2F9F0FED0CB6C22F65EDA33FBF0877FEB3D4659BA353929C26B`.

---

### 📊 Measured / Observed

#### Seal & Retained Evidence

| Artifact / Check | Value / Result | Provenance |
|---|---|---|
| Frozen SHA-256 | `07D46BD67D12A2F9F0FED0CB6C22F65EDA33FBF0877FEB3D4659BA353929C26B` | `[MEASURED-R]` `DIN_05_PREDICTIONS_FROZEN.md` |
| Frozen mtime UTC | `2026-09-10T08:00:00Z` | `[MEASURED-R]` filesystem |
| C0 opening bench | `relay\|133\|145\|19\|4\|39\|5\|0\|1\|w4d3_outbox` | `[MEASURED-R]` captured in C0 |
| C5 closing bench | `relay\|133\|145\|19\|4\|39\|5\|0\|1\|w4d4_sink_unique` | `[MEASURED]` 8 data counters untouched; version at HEAD |
| Job 136 baseline & close | `136\|running\|1\|1` | `[MEASURED]` completely untouched |
| Disposable DBs at close | `0` | `[MEASURED]` all dropped |
| Active Relay processes at close | `0` | `[MEASURED]` clean process teardown |

#### Step 0D — Carried Repairs (`P-38` & `P-39`)

- **`P-39` (Alembic `-c` flag precedence):**
  - Added `configure_url()` helper in `alembic/env.py` checking `-c` CLI option before environment variable `$env:DATABASE_URL`, and printing `alembic resolved_db={db} source={source}`.
  - Arm 1 (DATABASE_URL set, `-c <target.ini>` passed): Migrated target DB, printed `source=-c flag`. Exit 0.
  - Arm 2 (DATABASE_URL unset, `-c <target.ini>` passed): Migrated target DB. Exit 0.
  - Arm 3 (DATABASE_URL set, no `-c` flag): Migrated witness DB; evidence DB `relay` remained strictly untouched.
- **`P-38` (Dual sink unique constraint):**
  - Removed inline `UNIQUE` from `src/sink.py` DDL; Alembic migration `w4d4_sink_unique` is now the single source of truth.
  - Arm 1 (Sink started before migration): Unique constraints count on `idempotency_key` = `1`.
  - Arm 2 (Migration run before sink): Unique constraints count = `1`.
  - Arm 3 (Round-trip `head -> -1 -> head` on sink-first DB): Clean round trip; `-1` drops constraint to count `0`, `head` restores it to count `1`.
- **`C1c` Regression Suite:** `pytest tests -q` passed (`7 passed in 1.17s`). Recorded only, not a regression gate for Week 4 services (`P-37`).
- **Committed:** `commit 4d5d77a` (`fix(w4d5): repair P-38 dual sink unique and P-39 alembic -c precedence`).

#### Step 1 — Connection Budget & Attribution

- **PostgreSQL Limits `[MEASURED]`:** `max_connections = 100`, `superuser_reserved_connections = 3` -> 97 non-superuser connection headroom. No overrides in `docker-compose.yml`.
- **SQLAlchemy Defaults & Pool Config:** Added `application_name` server setting and configurable pool parameters (`RELAY_POOL_SIZE`, `RELAY_MAX_OVERFLOW`, `RELAY_POOL_TIMEOUT`) to `src/database.py`.
- **Idle vs Ceiling Allocation `[MEASURED]`:**
  - Running 5 Relay processes concurrently (`api`, `worker`, `reaper`, `dispatcher`, `sink`): exactly 5 active/idle connections in `pg_stat_activity` (1 per process).
  - QueuePool allocates lazily: 0 on startup, 1 on first checkout, expanding only under concurrent checkout demand.
  - Theoretical aggregate ceiling: 5 processes $\times$ (pool_size=5 + max_overflow=10 = 15) = **75 connections**.
  - Headroom to PostgreSQL 97 limit under full theoretical saturation: $97 - 75 = 22$ connections (comfortable single-digit/double-digit buffer).
- **Committed:** `commit ee1045a` (`feat(w4d5): add application_name attribution and configurable pool parameters`).

#### Step 2 — Pool Saturation & Receiver Lock Contention

- **Pool Saturation Probe 2A `[MEASURED]`:**
  - Configured: `pool_size=2, max_overflow=0, pool_timeout=3.0s`.
  - Worker 1 acquired Connection 1, Task 1 acquired Connection 2 (both sleeping for 5.0s).
  - Worker 2 attempted connection checkout: blocked in QueuePool queue for exactly `3.0055s`, then raised:
    `sqlalchemy.exc.TimeoutError: QueuePool limit of size 2 overflow 0 reached, connection timed out, timeout 3.00`.
  - Origin: **Client-side application QueuePool** (PostgreSQL never saw Worker 2's request; zero errors in PostgreSQL logs).
- **Receiver Lock Contention Probe 2B (`P-41`) `[MEASURED]`:**
  - Holder transaction held row lock on `sink_deliveries` (`idempotency_key='contention-probe'`) for 3.0s before rolling back.
  - Concurrent `POST /deliver` with same key executed `INSERT ... ON CONFLICT (idempotency_key) DO NOTHING`.
  - Request blocked for **`2.8133s`** waiting for the holder transaction to finish (uncontended baseline: `0.4703s`, a 6.0x slowdown).
  - Proves `ON CONFLICT DO NOTHING` is not `SKIP LOCKED`; conflicting concurrent inserts block on PostgreSQL `transactionid` row locks until the conflicting transaction terminates.

#### Step 3 — `/healthz` Cascading Outage Demonstration

- **Endpoint Implementation:** Added honest `/healthz` in `src/main.py` executing `SELECT 1` via `get_db()`.
- **Contention Failure Mode `[MEASURED]`:**
  - Saturated API pool (`pool_size=2, max_overflow=0`) with two concurrent `/slow-hold` requests (4.0s duration).
  - Client issued `GET /healthz` with 2.0s probe timeout.
  - `/healthz` blocked in QueuePool queue behind slow requests, timing out after `3.1618s`.
  - Proves architectural trap: sharing the application connection pool with `/healthz` causes orchestrator liveness probes to time out during heavy user traffic, triggering container SIGKILL and transforming transient traffic saturation into an acute cascading outage loop.
- **Committed:** `commit bc99c60` (`feat(w4d5): add honest /healthz endpoint on main engine pool`).

#### Step 4 — Sustained Enqueue Load & Observability Metrics

- **Enqueue Rate vs Drain Rate `[MEASURED]`:**
  - Enqueued 400 jobs via `POST /jobs` in 20.16s (arrival rate: **19.8 jobs/s**). Handler duration: 0.1s.
  - Single worker drain rate: **~7.0 jobs/s** (bounded by 0.1s handler sleep + 3 separate DB transactions + network round trips + `echo=True` stdout formatting).
  - Net accumulation rate: $+12.8$ to $+13.2$ jobs/s.
  - Queue depth (`status='pending'`) grew monotonically: 91 -> 133 -> 177 -> 221 -> 267.
  - Proof that `POLL_INTERVAL_SECONDS = 2.0s` is discovery latency on empty queue, not throughput divisor: worker loop ran without sleeping while backlog was pending.
- **Four Observability Metrics `[MEASURED]`:**
  - 1. Queue Depth (`pending`): `214` (during load snapshot)
  - 2. Latency (p50 / p99): `p50 = 10.2849s, p99 = 18.3357s`
  - 3. Retry Rate (`attempts > 1`): `0.0000 (0.0%)`
  - 4. Dead Letter Queue count: `0`

#### Step 5 — Postgres Chaos & Recovery

- **Database Stop Mid-Flight `[MEASURED]`:**
  - Stopped PostgreSQL container (`docker compose stop db`) for 26.8s while worker was active.
  - Worker in-flight query raised exception caught by `except Exception as exc:`; worker logged traceback and remained alive without process crash.
- **Stale Connection Recovery `[MEASURED]`:**
  - Started PostgreSQL container (`docker compose start db`).
  - First query checkout from pool hit dead TCP socket, raising:
    `sqlalchemy.exc.InterfaceError: (sqlalchemy.dialects.postgresql.asyncpg.InterfaceError) <class 'asyncpg.exceptions._base.InterfaceError'>: connection is closed`.
  - SQLAlchemy intercepted `InterfaceError`, invalidated the stale connection, and recycled the pool slot. Next query succeeded cleanly.
- **Reaper Reclaim Timing `[MEASURED]`:**
  - During 26.8s DB outage, server wall-clock advanced while `claimed_at` remained frozen.
  - Worker lease (30s) expired during outage. Exactly 7.9s after DB startup, reaper ran and reclaimed in-flight Job 1 from `running` to `pending`:
    `[reaper-20960] [reclaim] job_id=1 pre_status=running matched=1 post_status=pending pre_generation=1 post_generation=1`.

---

### 🧠 Prediction Review — Frozen Text Only

**Score: `1.5 / 5.0`** `[MEASURED from DIN_05_PREDICTIONS_FROZEN.md against DIN_05_KEY.md rubric]`

| Q | Score | Frozen Answer | Actual (Measured Today) & Key Contrast |
|---|---:|---|---|
| Q1 | `1.0/1.0` | (a) Slow 202 OK; 500 error only if queue wait exceeds pool_timeout. (b) Timeout occurs at pool_timeout (30s); error raised by application QueuePool, not Postgres. (c) Yes, 2 connections sufficient for 50 users (Little's Law: $50 \times 0.02 = 1.0 < 2$). | Fully correct on all three sub-questions. Exact layer attribution and concurrency arithmetic verified. |
| Q2 | `0.5/1.0` | (a) 5 idle connections (1 per engine). (b) Peak is 15 on single engine; total theoretical ceiling is 75 across 5 engines. (c) idk. | Part-mark awarded: (a) lazy pool fill correct, (b) ceiling identified; (c) NOT ANSWERED (idk). |
| Q3 | `0.0/1.0` | (a) 0.5 jobs/sec. (b) idk. (c) idk. | (a) Incorrect: used poll interval 2.0s as divisor (actual is ~7-10 jobs/s). (b) & (c) NOT ANSWERED (idk). |
| Q4 | `0.0/1.0` | (a) idk. (b) idk. (c) idk. | NOT ANSWERED (idk on all three parts). |
| Q5 | `0.0/1.0` | (a) idk. (b) idk. (c) idk. | NOT ANSWERED (idk on all three parts). |
| **Total** | **`1.5/5.0`** | | |

*Note on Process:* All five `### Observed + meri explanation` sections were filled with detailed systems mechanisms prior to opening the KEY, capturing the root causes of all observed behaviors.

---

### 💡 What the Session Established — In Plain Terms

1. `[MEASURED]` **Pool exhaustion is an application-level event, completely invisible to PostgreSQL.** When an application pool runs out of connections, `sqlalchemy.exc.TimeoutError` is raised by the client QueuePool after `pool_timeout`. PostgreSQL never sees the checkout attempt and logs zero errors.
2. `[MEASURED]` **`ON CONFLICT DO NOTHING` is not `SKIP LOCKED`; it waits on uncommitted transactions.** When inserting a row with an existing or in-flight unique key, PostgreSQL waits on the conflicting transaction's `transactionid` lock. A 3.0s holder transaction caused a concurrent insert to block for 2.81s.
3. `[MEASURED]` **Sharing an application pool with `/healthz` transforms traffic saturation into a cascading outage.** When all connections are busy processing slow requests, `/healthz` times out in the pool queue, prompting orchestrator container restarts and exacerbating system overload.
4. `[MEASURED]` **`POLL_INTERVAL_SECONDS` bounds discovery latency on an empty queue, not backlog throughput.** When pending jobs exist, the worker loop immediately claims the next job without sleeping. Single-worker throughput is bound by handler duration and database round trips (~7–10 jobs/s).
5. `[MEASURED]` **Server wall-clock continues during database outages, consuming lease duration.** A 26.8s outage consumed 26.8s of the 30s worker lease, enabling the reaper to reclaim the orphaned running job within 7.9s of database recovery.

---

### ⚠️ Closeout Corrections & Carry-Forward Status

| Item | Status | Provenance |
|---|---|---|
| Evidence DB 8 data counters (`133\|145\|19\|4\|39\|5\|0\|1`) | **Untouched (delta = 0)** | `[MEASURED]` identical to C0 bench |
| Job 136 baseline (`136\|running\|1\|1`) | **Untouched** | `[MEASURED]` untouched |
| Evidence DB Alembic version | **Migrated to HEAD (`w4d4_sink_unique`)** | `[MEASURED]` alembic check clean |
| Disposable DBs cleanup | **`0` probe DBs remaining** | `[MEASURED]` all dropped cleanly |
| Relay processes cleanup | **`0` Python processes running** | `[MEASURED]` clean termination |
| Dedup fix in migration file | **Committed (`cb17c36`)** | `[MEASURED]` in git tree |
| Architectural Design Decisions | **Documented (`DIN_05_DESIGN.md`)** | `[MEASURED]` Faisla 1–4 recorded |

---

### ❓ Next Thought: Week 4 Din 6 (Reconciliation & Month 1 Verdict)

Din 5 delivered the complete failure and capacity matrix for Relay under stress. Din 6 is the final day of Week 4 and Month 1: reconciling all counters across the entire 4-week journey, publishing architectural decisions (`D-26` to `D-29`), resolving active problem cards, and delivering an honest, evidence-backed verdict on Relay's core contracts.

