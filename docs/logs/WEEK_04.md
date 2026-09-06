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
