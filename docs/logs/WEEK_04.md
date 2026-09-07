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
