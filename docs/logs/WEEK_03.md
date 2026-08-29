# WEEK 3 — Idempotency, dedup, exactly-once: ek kaam do baar chala, side effect ek baar kyu hua

**Layer: L2 ka core** · Daily log with measurements, self-checks, and unresolved items.
Plan: [`../planning/WEEK_03.md`](../planning/WEEK_03.md) · Decisions: [`../DECISIONS.md`](../DECISIONS.md)

> **Plan intent rakhta hai, ye file outcome rakhti hai.** Jo bhi number, verdict ya score iss hafte me
> nikla, wo yahan aata hai — plan me kabhi nahi. Aur plan ko reality se match karne ke liye **edit nahi**
> karna: dono files apna sach rakhti hain, aur unka farq khud ek finding hai (`E2`).
>
> **Ye file abhi khali template hai.** Har `____` ek jagah hai jo uss din shaam bharti hai. Jo value aaj
> tak measure nahi hui, wo `____` rehti hai — **plausible number likhna sabse mehnga shortcut hai.** Agar
> koi cheez measure nahi ho paayi, `[NO EVIDENCE]` likho, blank ko guess se mat bharo.
>
> Har claim pe ek label: `[MEASURED]` (tumne khud chalaya) · `[MEASURED-R]` (reviewer ne chalaya) ·
> `[INFERRED]` (mechanism se reason kiya) · `[NO EVIDENCE]` (judgement, aur waise hi labelled).
>
> **Iss hafte do naye rules, aur dono Week 2 ke measured failures se aaye hain:**
> 1. **Har din ka `💡 What I Understood` uss din, apne shabdon me.** Week 2 ke **paanchon** `💡` reviewer
>    ke likhe hue hain, aur uska nateeja ye hai ki `WEEK_02_HANDOFF.md` ka *What Stuck* list ek claim hai
>    jiske peeche koi test nahi.
> 2. **`DIN_0N_ANSWERS.md` ka mtime khud ek measurement hai**, aur wo har din ke 🧠 section me likha jaata
>    hai. Week 2 me chhe din me se ek din answers pehle likhe gaye — aur wahi ek din `5/6` aaya.

---

## Contents

- [Divergence — Din 1 ki subah ka bench check (E2)](#divergence--din-1-ki-subah-ka-bench-check-e2)
- [Din 1 — Side effect pehli baar exist karta hai](#din-1--side-effect-pehli-baar-exist-karta-hai-____)
- [Din 2 — Dedup at execute: constraint kaam karti hai](#din-2--dedup-at-execute-constraint-kaam-karti-hai-____)
- [Din 3 — 🎯 Crash side effect ke BEECH me](#din-3--crash-side-effect-ke-beech-me-____)
- [Din 4 — Dedup at enqueue: `idempotency_key`, aur `P-07`](#din-4--dedup-at-enqueue-idempotency_key-aur-p-07-____)
- [Din 5 — Property test: evidence, opinion nahi](#din-5--property-test-evidence-opinion-nahi-____)
- [Din 6 — Close: reconcile, likho, handoff](#din-6--close-reconcile-likho-handoff-____)
- [Week close — reconcile chain aur handoff](#week-close--reconcile-chain-aur-handoff)

---

## Iss hafte ka ek sawaal, jiske against har din padha jaata hai

**Contract #2 — *duplicate execution side effects duplicate nahi karta* — aaj tak unprotected hai, aur
Week 2 tak wo *untestable* bhi tha.**

| Din | Wo cheez jo uss din pehli baar exist karti hai |
|---|---|
| Din 1 | **Ek side effect**, aur uska count `2` |
| Din 2 | **Ek `UNIQUE`**, aur wahi count `1` |
| Din 3 | **Do states jo `jobs` me identical dikhti hain** aur side-effect store me alag |
| Din 4 | **Do dedup layers**, alag scope ke saath (`P-07` band hoti hai) |
| Din 5 | **Ek property**, aur uske known limits |
| Din 6 | `D-24`, `D-25`, aur wo line jo decide karti hai: *protected* ya *narrowed* |

**Aur ek rule jo poore hafte lagta hai:** side effect count `1` **kuch prove nahi karta** jab tak wo
duplicate execution **prove** na ho jo `2` deta. Zero-duplicate run dedup ka evidence nahi — wo *koi test
nahi hua* ka evidence hai. `P-12` ka wahi shape, ek layer neeche.

---

## Divergence — Din 1 ki subah ka bench check (E2)

Din 1 Step 1 se **pehle** bench check hota hai. Match kare to ek line likh do aur aage badho. Match na kare
to **wo divergence khud ek finding hai** aur Step 1 tab tak rukta hai jab tak uska **naam wala cause** na
mile.

**Expected (Week 2 close, `[MEASURED 2026-08-29]`):**

```
89 succeeded / 15 failed / 3 dead_letter / 0 pending / 0 running     total 107
max(id) 108 · jobs_id_seq 108 · job_executions 94
attempts:  0|95 · 1|3 · 3|8 · 4|1
alembic_version = 682e01d87be9 · python.exe = 0 · idle in transaction = 0
```

| Kya | Expected | Actual | Match? |
|---|---|---|---|
| `succeeded` / `failed` / `dead_letter` / `pending` / `running` | `89 / 15 / 3 / 0 / 0` | `____` | `____` |
| total rows | `107` | `____` | `____` |
| `max(id)` | `108` | `____` | `____` |
| `jobs_id_seq.last_value` | `108` | `____` | `____` |
| `job_executions` | `94` | `____` | `____` |
| `attempts` distribution | `0|95 · 1|3 · 3|8 · 4|1` | `____` | `____` |
| `alembic_version` | `682e01d87be9` | `____` | `____` |
| `python.exe` processes | `0` | `____` | `____` |
| `idle in transaction` | `0` | `____` | `____` |
| **teesra check** — `backend_start`, oldest first | sirf aaj ki session | `____` | `____` |

**Ye nahi hota, aur rule dono directions me lagta hai:**

- **BENCH block edit nahi hota.** Wo Week 2 ke close ka `[MEASURED]` snapshot hai; usko badalna ye record
  mita dena hai ki plan **kis** state ke against likha gaya tha.
- **Reality repair nahi hoti.** Counts wapas plan wale numbers pe laane ke liye rows insert/delete karna
  manufactured evidence hai, aur uske baad poore hafte ka arithmetic ek banayi hui baseline pe khada hoga.

**Agar divergence mili:** pehla suspect ek bhoola hua worker/reaper hai (`P-13`, Week 2 me teen instance),
doosra ek extra reaper run, teesra ek rolled-back `INSERT` (`P-05`, sequence value kha jaata hai par row
nahi banti).

| Kya | Value |
|---|---|
| Divergence mili? | `____` |
| Uska naam wala cause | `____` |
| Naya baseline (agar divergence accept hui) | `____` |

---

## Din 1 — Side effect pehli baar exist karta hai (`____`)

**Original goal (from the plan):** problem statement apne shabdon me (chaar paragraph, disk pe) · ek
side-effect store, uska shape **chuna hua aur cost ke saath** · ek handler jo asli side effect karta hai,
duration `payload` se · aur **ek duplicate deliberately produce karke uska side effect count measure karna**.
**Aaj protection nahi banti — `UNIQUE` Din 2 ka kaam hai.**

**Goal met?** `____` — yes / no / partial, aur partial pe kaunsa hissa.

**Anything else learned?** `____` — goal-met se alag field.

---

### 📊 Measured / Observed

**Opening check (`P-13`, `P-06`) — teeno, aur teesra bhi:**

| Kya | Value | Label |
|---|---|---|
| `python.exe` processes | `____` | `____` |
| `idle in transaction` | `____` | `____` |
| `datname='relay'` connections, `backend_start` oldest first | `____` | `____` |
| `alembic_version` | `____` | `____` |

**Aaj ye likhna hai (plan ka Din 1 obligation):**

| Kya | Value / text | Label |
|---|---|---|
| Problem statement ka **path** (text nahi — wo tumhari file hai) | `____` | `[NO EVIDENCE]` for authorship jab tak file exist na kare |
| `Interim_Guarantee`, ek line — aur `narrows`/`closes` ka rule yahan lagta hai | `____` | — |
| Side-effect store ka shape (counter / ledger) + **uski cost** | `____` | — |
| Table ka naam, columns, aur **kya `UNIQUE` nahi laga** | `____` | `____` |
| Migration up **aur** down ka actual output | `____` | `____` |
| Handler ka naam, aur duration ka source (`payload` ka kaunsa key) | `____` | `____` |
| `git log --all -S"<handler name>"` — ek hi naam, ya naye names? (`P-23`) | `____` | `____` |
| Baseline: ek job, ek dispatch, side effect count | `____` | `____` |
| **Duplicate ka setup** — handler duration, lease, worker count, dono workers ka start time | `____` | `____` |
| **Heartbeat ka kya kiya** — chalne diya / band kiya / handler ko yield na karne diya — aur **kyu** | `____` | — |
| `claimed_at` ka pehle dispatch se farq (`~25 ms` = heartbeat nahi chala · `~10 s` ke multiples = chala) | `____` | `____` |
| **`job_executions` rows** uss job pe — count, aur **dono `worker_id`** | `____` | `____` |
| **Overlap**, seconds me, aur **kaunsi derivation** use ki | `____` | `____` |
| **🎯 Side effect count** — aur uske saath Part B ka pehle likha hua prediction | `____` | `____` |
| `attempts` duplicate ke baad | `____` | `____` |
| Dono marks ka `rowcount` — kaunse worker ko `1` mila aur kaunse ko `0` | `____` | `____` |

**M1 — `____`**

```
____
```

**M2 — `____`**

```
____
```

**Closing reconciliation** — opening counts BENCH block se, delta aaj ka. **Kabhi `max(id)` se nahi, kabhi
id contiguity se nahi** (`P-05`). Aur per-day delta **`created_at`/`executed_at` ke `group by` se**, gin-ti
se nahi:

```sql
select created_at::date, count(*) from jobs where id > 108 group by 1 order by 1;
select executed_at::date, count(*) from job_executions group by 1 order by 1;
```

| Line | Value |
|---|---|
| opening — `succeeded`/`failed`/`dead_letter`/`pending`/`running`/total | `89 / 15 / 3 / 0 / 0` = `107` · `job_executions 94` |
| `+` aaj ki nayi rows, **ids naam se** | `____` |
| `±` bucket shifts (naye rows nahi) | `____` |
| `=` expected closing | `____` |
| aaj ke `psql` counts — paanchon bucket + total | `____` |
| `job_executions` delta | `____` — **aur ye `jobs` ke delta se BADA hona chahiye.** Excess **naam se**: `____` |
| `created_at` ka `group by` isse agree karta hai? | `____` |
| **Chain juda?** | `____` |
| `jobs_id_seq` vs `max(id)` — naya gap bana? | `____` |

Match na kare to wo **finding** hai (`E5`), difference ko kisi din me fit karke chain band nahi hoti.

**Cleanup:**

| Kya | Status | Label |
|---|---|---|
| worker / reaper processes at close | `____` | `____` |
| `idle in transaction` | `____` | `____` |
| **Teesra check — `backend_start`** | `____` | `____` |
| stdout capture — relevant lines **delete se pehle** log me copy hui? | `____` | `____` |
| `src/` ka koi temporary change (heartbeat?) — reverted? | `____` | `____` |
| Probe rows **delete nahi** hoti; unke ids | `____` | `____` |
| Commit — staged paths naam se | `____` | `____` |

---

### 💡 What I Understood

> **Ye section aaj, apne shabdon me.** Week 2 me paanchon din ye reviewer ne likha, aur wahi hafte ka
> sabse bada retention debt ban gaya.

`____`

---

### 🧠 Self-Check (honest — `____` / `6` self-answered)

| Kya | Value |
|---|---|
| `DIN_01_ANSWERS.md` exist karti hai? | `____` |
| Uska mtime **Step 4 ke output se pehle** hai? (`E8`) | `____` |
| Score | `____` / 6 |
| `idk` kitne? (aur `idk` **not-answered** score karta hai, jo accurate hai) | `____` |
| `idk — <phir poora jawab>` kitne? (ye **self-inflicted zero** hai) | `____` |

`____`

**Corrections:**

| # | I said | Actual | The transferable lesson |
|---|---|---|---|
| `__` | `____` | `____` | `____` |

---

### 🚧 Unresolved / Follow-ups

**New, from today:** `____`

**Deliberately open (owner ke saath):** `____`

**Slipped (aur specifically kya chahiye):** `____`

**Carried forward, unchanged:** `____`

---

### ❓ Question / Next Thought

`____`

---

## Din 2 — Dedup at execute: constraint kaam karti hai (`____`)

**Original goal (from the plan):** side effect ki identity pe **`UNIQUE`** · insert conflict-safe aur uska
`rowcount`/exception **padha hua** · Din 1 ka run **bilkul wahi** dobara, ek variable badla (dedup) · aur
phir **wo galat version chalao** (`SELECT`-phir-`INSERT`) taki `D-25` ka `Rejected` **measured** ho.

**Goal met?** `____`

**Anything else learned?** `____`

---

### 📊 Measured / Observed

| Kya | Value | Label |
|---|---|---|
| Opening check (teeno) | `____` | `____` |
| Din 1 ka baseline abhi bhi wahan hai? (uss job ka execution count + side effect count) | `____` | `____` |
| **Side effect ki identity** — key kis cheez pe hai, aur kyu | `____` | — |
| Din 1 ka `attempts` (jo `2` tha) ne kaunsa option **kaata** | `____` | — |
| Migration up + down ka output | `____` | `____` |
| `INSERT ... ON CONFLICT DO NOTHING` ka **`rowcount`** conflict pe | `____` | `____` |
| `UNIQUE` + `NULL` ka behaviour (agar key nullable hai) | `____` | `____` |
| **Duplicate PHIR BHI hua?** — do `worker_id`, overlap seconds me | `____` | `____` |
| **🎯 Side effect count** — Din 1 ke number ke **against** | `____` | `____` |
| Constraint ne kaam kiya iska direct evidence (`rowcount = 0` print / `UniqueViolation` verbatim) | `____` | `____` |
| **Galat version** (`SELECT`-phir-`INSERT`) ka side effect count | `____` | `____` |
| Agar race reproduce **nahi** hui: kitni koshish, window kitni chaudi, kya badalna padta | `____` | `____` |
| `UniqueViolation` handler me uncaught hui to job ka `status` kahan gaya | `____` | `____` |

**M1 — `____`**

```
____
```

**Closing reconciliation** — opening counts **Din 1 ke log se**:

| Line | Value |
|---|---|
| opening | `____` |
| `+` nayi rows, ids naam se | `____` |
| `=` expected closing | `____` |
| `psql` actual | `____` |
| `job_executions` delta, aur excess naam se | `____` |
| `created_at`/`executed_at` `group by` agree karta hai? | `____` |
| **Chain juda?** | `____` |

**Cleanup:** `____`

---

### 💡 What I Understood

> **Aaj, apne shabdon me.**

`____`

---

### 🧠 Self-Check (honest — `____` / `6` self-answered)

| Kya | Value |
|---|---|
| Answers file ka mtime uss step se pehle? | `____` |
| Score | `____` / 6 |

`____`

**Corrections:**

| # | I said | Actual | The transferable lesson |
|---|---|---|---|
| `__` | `____` | `____` | `____` |

---

### 🚧 Unresolved / Follow-ups

**New, from today:** `____`

**Deliberately open (owner ke saath):** `____`

**Slipped:** `____`

---

### ❓ Question / Next Thought

`____`

---

## Din 3 — 🎯 Crash side effect ke BEECH me (`____`)

**Original goal (from the plan):** crash point `payload` se controllable, crash **asli** (`os._exit()` /
bahar se `kill`, `raise` **nahi**) · teeno crash points chalao aur **reaper chalne se PEHLE** ka DB state
verbatim likho · phir reaper chalao aur dobara padho · aur outbox ka faisla likho (side effect + mark ek
transaction me **kyu nahi**).

**Goal met?** `____`

**Anything else learned?** `____`

---

### 📊 Measured / Observed

| Kya | Value | Label |
|---|---|---|
| Opening check (teeno) | `____` | `____` |
| Crash point kaise controllable banaya (`payload` ka key) | `____` | `____` |
| Crash ka mechanism (`os._exit` / `kill` / kuch aur) | `____` | `____` |

**Teen crash points — reaper se PEHLE ka state. Ye state reclaim ke baad WAPAS NAHI AA SAKTI:**

| Crash kahan | side-effect record | `jobs.status` | `attempts` | `claimed_at` | `job_executions` count |
|---|---|---|---|---|---|
| side effect commit se **pehle** | `____` | `____` | `____` | `____` | `____` |
| side effect ke **baad**, mark se **pehle** | `____` | `____` | `____` | `____` | `____` |
| mark ke **baad** | `____` | `____` | `____` | `____` | `____` |

**Reaper ke BAAD:**

| Crash kahan | `status` | Handler dobara chala? (`job_executions` delta) | **Side effect count** | Label |
|---|---|---|---|---|
| pehle | `____` | `____` | `____` | `____` |
| **beech me** 🎯 | `____` | `____` | `____` | `____` |
| baad me | `____` | `____` | `____` | `____` |

| Kya | Value / text | Label |
|---|---|---|
| **Do states jo `jobs` me identical dikhti hain** — wo actually identical thi? | `____` | `____` |
| Aur side-effect store me wo **alag** dikhi? | `____` | `____` |
| `1` aaya — **dedup ki wajah se ya handler dobara chala hi nahi?** (`job_executions` count separate karta hai) | `____` | `____` |
| **Outbox ka faisla** — side effect + mark ek transaction me? Do reason, aur ek aisa side effect jise transaction me rakha hi nahi ja sakta | `____` | — |
| `P-16` ka aaj ka roop — `running` ke do situations database se distinguishable hui? | `____` | `____` |
| `D-22` Cost 10 (`completed_at`) — aaj usne kaise chubha, aur faisla kya | `____` | — |

**M1 — `____`**

```
____
```

**Closing reconciliation:** `____`

**Cleanup:** `____`

---

### 💡 What I Understood

> **Aaj, apne shabdon me.**

`____`

---

### 🧠 Self-Check (honest — `____` / `6` self-answered)

`____`

**Corrections:**

| # | I said | Actual | The transferable lesson |
|---|---|---|---|
| `__` | `____` | `____` | `____` |

---

### 🚧 Unresolved / Follow-ups

**New, from today:** `____`

---

### ❓ Question / Next Thought

`____`

---

## Din 4 — Dedup at enqueue: `idempotency_key`, aur `P-07` (`____`)

**Original goal (from the plan):** `idempotency_key text NULL UNIQUE` `jobs` pe, migration up aur down ·
`POST /jobs` ka replay behaviour ek **decision** ke saath · `P-07` ke **chaar** sawaalon ka jawab, apni cost
ke saath · aur do **concurrent** identical `POST`.

**Goal met?** `____`

**Anything else learned?** `____`

---

### 📊 Measured / Observed

| Kya | Value | Label |
|---|---|---|
| Opening check (teeno) | `____` | `____` |
| Migration up + down | `____` | `____` |

**`P-07` ke chaar sawaal — aaj jawab ke saath:**

| Sawaal | Chuna hua jawab | Uski cost | Label |
|---|---|---|---|
| Key kaun mint karta hai (caller / payload hash) | `____` | `____` | — |
| Dedup window (forever / N time) | `____` | `____` | — |
| Duplicate request ko kya milta hai (`202` + original id / `409`) | `____` | `____` | — |
| Race pe kya hota hai | **measured, decided nahi:** `____` | — | `____` |

| Kya | Value | Label |
|---|---|---|
| Sequential replay — `count(*)` badla? `jobs_id_seq` badla? | `____` | `____` |
| Loser ko kya mila — exception / `rowcount = 0` / block — aur `INSERT` pe ya `commit()` pe | `____` | `____` |
| `25P02` (*current transaction is aborted*) — mila? Aur usko kaise handle kiya | `____` | `____` |
| **Do concurrent identical `POST`** — dono ke status code, dono ke `job_id`, `jobs` ka `count(*)` | `____` | `____` |
| Bina key wale POST abhi bhi do rows banate hain? (`NULL` + `UNIQUE`) | `____` | `____` |
| **Regression check** — Din 2 ka execute-side dedup abhi bhi kaam karta hai? | `____` | `____` |
| `P-07` band hui, ya uska kaunsa hissa khula raha | `____` | — |

**M1 — `____`**

```
____
```

**Closing reconciliation:** `____`

**Cleanup:** `____`

---

### 💡 What I Understood

> **Aaj, apne shabdon me.**

`____`

---

### 🧠 Self-Check (honest — `____` / `6` self-answered)

`____`

**Corrections:**

| # | I said | Actual | The transferable lesson |
|---|---|---|---|
| `__` | `____` | `____` | `____` |

---

### 🚧 Unresolved / Follow-ups

**New, from today:** `____`

---

### ❓ Question / Next Thought

`____`

---

## Din 5 — Property test: evidence, opinion nahi (`____`)

**Original goal (from the plan):** property ka **wording** pehle likhna (code se pehle), aur uske do hisse
iss hafte ke measurements ke hisaab se theek karna (`har job` ka scope, aur `= 1` vs `<= 1` — `P-27`) ·
Hypothesis se random **interleavings** · test isolation ka faisla (107 purani rows, aur wo **delete nahi**
hoti) · aur **dedup hata ke test red hona verify karna**.

**Goal met?** `____`

**Anything else learned?** `____`

---

### 📊 Measured / Observed

| Kya | Value / text | Label |
|---|---|---|
| Opening check (teeno) | `____` | `____` |
| **Property ka wording, subah likha hua** | `____` | — |
| **Property ka wording, shaam ka** — aur jo badla, wo kis measurement se badla | `____` | — |
| Scope: `har job` ya `wo jobs jinka handler ek baar poora chala`? Aur wo kis column se pata chalta hai | `____` | — |
| `= 1` ya `<= 1`? (`P-27`) Aur kaunsa asli contract hai | `____` | — |
| Test isolation ka faisla (separate DB / rollback per example / key prefix) + cost | `____` | — |
| `jobs` ka `count(*)` test se **pehle** aur **baad** | `____` | `____` |
| Hypothesis ki **example count** | `____` | `____` |
| Kitne examples me **do dispatch** hue (warna test ne duplicate dekha hi nahi — `P-12`) | `____` | `____` |
| **Dedup hata ke test red hui?** — ye aaj ka sabse zaroori check hai | `____` | `____` |
| Property fail hui? **Shrunk counterexample verbatim** | `____` | `____` |
| Property paas hui **bina** fencing token ke? | `____` | `____` |
| **Ek concrete interleaving jo dedup se bachta hai par fencing se rukta hai** (Week 4 ka input) | `____` | `____` |
| Property ke **known limits** — kya ye test check **nahi** karta | `____` | — |

**M1 — `____`**

```
____
```

**Closing reconciliation:** `____`

**Cleanup:** `____`

---

### 💡 What I Understood

> **Aaj, apne shabdon me.**

`____`

---

### 🧠 Self-Check (honest — `____` / `6` self-answered)

`____`

**Corrections:**

| # | I said | Actual | The transferable lesson |
|---|---|---|---|
| `__` | `____` | `____` | `____` |

---

### 🚧 Unresolved / Follow-ups

**New, from today:** `____`

---

### ❓ Question / Next Thought

`____`

---

## Din 6 — Close: reconcile, likho, handoff (`____`)

**Original goal (from the plan):** paanch din ka evidence entries banta hai — chain, `D-24`, `D-25`,
`D-03`/`D-05`/`D-21`/`D-22` ke amendments, `MAP.md`, `LEARNING_LOG.md`, `CURRENT_WEEK.md`,
`WEEK_03_HANDOFF.md`, carried debts ka verdict, aur commit. **Koi `src/` change nahi.**

**Goal met?** `____`

**Anything else learned?** `____`

---

### 📊 Measured / Observed

**Opening check — aur ye Step 1 se PEHLE chalta hai:**

| Kya | Value | Label |
|---|---|---|
| worker processes / `idle in transaction` / connections (teeno) | `____` | `____` |

**Aaj ka grep output — number assign karne ke din chalta hai, plan likhne ke din nahi (`E6`):**

```
Select-String -Path docs\DECISIONS.md -Pattern '^## `?D-'
____

Select-String -Path docs\PROBLEMS.md -Pattern '^## P-'
____
```

| Kya | Value |
|---|---|
| Grep plan ke expected ranges se match karta hai? (`D-24`, `P-28`) | `____` |
| Aaj assign hue `D-` numbers | `____` |
| Aaj assign hue `P-` numbers | `____` |
| Collision mili? (naya entry hilta hai, purana kabhi nahi) | `____` |
| Dangling citation mili? | `____` |

**Doc-sync — kya actually likha gaya (files kholke check, `git status` se nahi):**

| File | Kya gaya | Ho gaya? |
|---|---|---|
| `docs/DECISIONS.md` — `D-24` (dedup at enqueue vs at execute) | `____` | `____` |
| `docs/DECISIONS.md` — `D-25` (`UNIQUE` vs application-level check, `Rejected` me **measured** race) | `____` | `____` |
| `docs/DECISIONS.md` — `D-03` amendment (PK vs idempotency key) | `____` | `____` |
| `docs/DECISIONS.md` — `D-05` amendment (payload hash, `jsonb` normalisation) | `____` | `____` |
| `docs/DECISIONS.md` — `D-21` amendment (identifier — do hafte se overdue) | `____` | `____` |
| `docs/DECISIONS.md` — `D-22` amendment (fencing token, `completed_at`) | `____` | `____` |
| Har naye entry ka **non-empty `Cost`**, aur har `Cost`/`Rejected` line pe **ek** provenance tag | `____` | `____` |
| `docs/PROBLEMS.md` — naye entries, `P-28` se | `____` | `____` |
| `docs/MAP.md` — per entry ek index row (A/B/C), amend hue rows **update**, **reasoning nahi** | `____` | `____` |
| `docs/LEARNING_LOG.md` — open items ka verdict, Week 3 row, next-free numbers | `____` | `____` |
| `docs/roadmap/CURRENT_WEEK.md` — week close, pointer **Week 4** pe | `____` | `____` |
| `docs/daily/WEEK_03_HANDOFF.md` — teen headings, pehli do **word-for-word**, dono definitions file me | `____` | `____` |
| Commit — staged paths naam se, `.` kabhi nahi | `____` | `____` |

`docs/roadmap/`, `docs/daily/`, `docs/planning/`, `docs/ddia_summaries/` **gitignored hain** — wo files
`git status` me dikhengi hi nahi, isliye kholke check hoti hain. `git check-ignore -v` se confirm, memory
se nahi.

**Carried debts ka verdict — har item ko *closing measurement* ya *named owner*, teesra option nahi:**

| Item | Verdict |
|---|---|
| Week 2 ke `💡`/`🧠` sections (paanchon reviewer ke) | `____` |
| Paanch written Week 2 answers (dasva carry, `slipped`) | `____` |
| `DDIA_CH8_LINKS.md` lines 10–13 | `____` |
| Teesra cleanup check (`backend_start`) | `____` |
| Week 1 Din 7 ka log entry · `2026-08-24` | `____` |
| `job_executions` ka attempt/claim identifier (`P-11`, `D-21`) | `____` |
| `completed_at` / completion evidence (`D-22` Cost 10) | `____` |
| Shutdown-versus-lease ka run (`D-22` Cost 8, `[INFERRED]`) | `____` |

**Cleanup:** `____`

---

### 💡 What I Understood

`____`

---

### 🧠 Self-Check (honest — `____` / `7` self-answered)

`____`

**Corrections:**

| # | I said | Actual | The transferable lesson |
|---|---|---|---|
| `__` | `____` | `____` | `____` |

---

### 🚧 Unresolved / Follow-ups

**New, from today:** `____`

**Deliberately open (owner ke saath):** `____`

**Slipped (aur specifically kya chahiye):** `____`

**Carried forward, unchanged:** `____`

---

### ❓ Question / Next Thought

`____`

---

## Week close — reconcile chain aur handoff

Din 6 ka closing **hi** hafte ka closing hai. Chain ka shape ek hi hai: **week opening + har din ka delta =
aaj ke actual counts.** Chain kabhi `max(id)` se nahi jodi jaati — id contiguity `jobs` ka invariant nahi
hai, aur `P-05` hi uska evidence hai.

**Aur per-day delta `created_at`/`executed_at` ke `group by` se aata hai, uss din ki report ki gin-ti se
nahi.** Week 2 me report-based chain ka **total sahi tha aur do per-day deltas galat the** — Din 3 aur
Din 4, opposite direction me, to error cancel ho gaya aur chain "judi hui" dikhi. Boundary row `97` thi:
`created_at` Din 3 ka, pehla dispatch Din 4 ka. **Total match karna do compensating errors ko chhupa leta
hai.**

```sql
select created_at::date, count(*) from jobs where id > 108 group by 1 order by 1;
select executed_at::date, count(*) from job_executions group by 1 order by 1;
```

**Full reconcile chain:**

| Line | Kahan se | Value |
|---|---|---|
| Week opening counts | BENCH block (Week 2 close) | `89 / 15 / 3 / 0 / 0` = `107` · `job_executions 94` |
| `+` Din 1 delta | Din 1 entry, `created_at` `group by` se | `____` |
| `+` Din 2 delta | Din 2 entry | `____` |
| `+` Din 3 delta | Din 3 entry | `____` |
| `+` Din 4 delta | Din 4 entry | `____` |
| `+` Din 5 delta | Din 5 entry | `____` |
| `=` expected closing | arithmetic | `____` |
| aaj ke `psql` counts — **paanchon** status buckets + total | aaj ka opening check | `____` |
| `job_executions` — opening + per-din delta = aaj ka count | log + aaj ka output | `____` |
| `group by` wali reading report wali reading se **match karti hai**? | dono side by side | `____` |
| **Chain juda?** | — | `____` |

**Iss hafte `job_executions` ka delta `jobs` ke delta se BADA hoga**, aur wo expected hai — duplicate
dispatches. Excess **naam se** likha jaata hai (Week 2 Din 3 me wo `+4` tha).

**Aur ek naya bucket iss hafte:** side-effect store. Uski bhi chain jodi jaati hai:

| Line | Value |
|---|---|
| side-effect rows / counter total, week close pe | `____` |
| **Kitne jobs pe count `> 1` hai** — aur unme se kitne **expected** hain (Din 1 ka deliberate duplicate) | `____` |
| Koi **unexpected** `> 1`? | `____` |

**Week close pe `running` aur `pending` rows — DoD item, aur zero ho ya na ho dono likhe jaate hain:**

| Kya | Value | Label |
|---|---|---|
| `running` count at close | `____` | `____` |
| `pending` count at close | `____` | `____` |
| Uske ids (agar zero nahi) | `____` | `____` |
| Ye ids Week 4 ka input hain — handoff me gaye? | `____` | — |

**Sequence:**

| Kya | Value | Label |
|---|---|---|
| `jobs_id_seq` `last_value` | `____` | `____` |
| `max(id)` | `____` | `____` |
| Naya gap bana? (aur purana gap id `79` par hai — `P-05`) | `____` | `____` |

**Agar chain nahi judi (`E5`):** mismatch **finding ki tarah** likhi jaati hai, difference ko kisi din me
fit karke chain band nahi hoti.

| Kya | Value |
|---|---|
| Kaunsa din toota | `____` |
| Kitna difference | `____` |
| Kya check kiya gaya (bhoola hua worker `P-13`, extra reaper run, delete hui row, consumed sequence value) | `____` |
| **Ye din handoff ki teesri heading me naam se gaya?** | `____` |

---

### Definition of Done — week close pe audit

**Har untick ek line maangta hai:** *deliberately deferred* apne **owner** ke saath, **ya** *slipped* uske
saath jo usko **specifically** chahiye. Do me se ek — dono nahi, koi nahi bhi nahi.

| Group | DoD item | Status | Evidence | Untick ho to: deferred (owner) / slipped (kya chahiye) |
|---|---|---|---|---|
| Build | Side-effect store + shape ka faisla | `____` | `____` | `____` |
| Build | Side-effecting handler, duration `payload` se | `____` | `____` | `____` |
| Build | `UNIQUE` side effect ki identity pe | `____` | `____` | `____` |
| Build | Conflict-safe insert, `rowcount` padha hua | `____` | `____` | `____` |
| Build | Dedup row ka **matlab** likha hua + uska khula hole | `____` | `____` | `____` |
| Build | Galat version (`SELECT`-phir-`INSERT`) **chalaya hua**, **constraint-free fixture** pe | `____` | `____` | `____` |
| Build | Constraint **wapas lagi hui** (agar downgrade route liya) | `____` | `____` | `____` |
| Build | Crash point `payload` se, crash **asli** | `____` | `____` | `____` |
| Build | **Post-mark crash** ka mechanism (worker-level hook / bahar se `kill`) | `____` | `____` | `____` |
| Build | Har crash case: apna job, reaper **band**, pre-reaper snapshot, phir reaper | `____` | `____` | `____` |
| Build | `idempotency_key` + `UNIQUE` | `____` | `____` | `____` |
| Build | `POST /jobs` replay behaviour, **ek** enforcement point | `____` | `____` | `____` |
| Build | **Wahi key + alag payload** ka behaviour (fingerprint compare) | `____` | `____` | `____` |
| Build | Duplicate `POST` ka path **abort-safe** (`rollback()` / `ON CONFLICT ... RETURNING`) | `____` | `____` | `____` |
| Build | Property test **Layer A** — deterministic model, genuinely shrinkable | `____` | `____` | `____` |
| Build | Property test **Layer B** — asli witnesses, **separate test DB** pe | `____` | `____` | `____` |
| Build | Property ka scope durable effect fact pe (ya `completed_at` ka owner) | `____` | `____` | `____` |
| Build | Property test **red ho sakti hai** — verify kiya hua | `____` | `____` | `____` |
| Build | **Guarantee ka wording** — local effect tak limited, external `[NO EVIDENCE]` | `____` | `____` | `____` |
| Build | Roadmap ka outbox **build** item `deferred (Week 4)` mark kiya hua | `____` | `____` | `____` |
| Measured | Din 1 ka side effect count (+ do `worker_id` + prove hua overlap) | `____` | `____` | `____` |
| Measured | Din 2 ka side effect count, Din 1 ke against | `____` | `____` | `____` |
| Measured | `ON CONFLICT DO NOTHING` ka `rowcount` | `____` | `____` | `____` |
| Measured | Galat version ka count (ya: koshish + window ki chaudai) | `____` | `____` | `____` |
| Measured | Teen crash points ka pre-reaper state | `____` | `____` | `____` |
| Measured | Recovery ke baad count + `job_executions` count | `____` | `____` | `____` |
| Measured | Do concurrent `POST` ka outcome | `____` | `____` | `____` |
| Measured | `jobs_id_seq` ek rejected duplicate `INSERT` ke baad | `____` | `____` | `____` |
| Measured | Property test ki example count + do-dispatch examples | `____` | `____` | `____` |
| Measured | Shrunk counterexample | `____` | `____` | `____` |
| Measured | Week close pe paanchon buckets + `running`/`pending` | `____` | `____` | `____` |
| Measured | Per-day delta `group by` se, **har din** | `____` | `____` | `____` |
| Likha | Chhe log entries, poori shape me | `____` | `____` | `____` |
| Likha | **Har din ka `💡` uss din, apne shabdon me** | `____` | `____` | `____` |
| Likha | Chhe `ANSWERS.md` files, mtime step se pehle | `____` | `____` | `____` |
| Likha | `D-24` · `D-25` · chaar amendments | `____` | `____` | `____` |
| Likha | `PROBLEMS.md` · `MAP.md` · `LEARNING_LOG.md` · `CURRENT_WEEK.md` · handoff | `____` | `____` | `____` |
| Likha | `DDIA_CH11_LINKS.md` — har reading din se do lines | `____` | `____` | `____` |
| Likha | Chhe staged commits, paths naam se | `____` | `____` | `____` |
| Carried debt | Week 2 ke `💡`/`🧠` sections | `____` | `____` | `____` |
| Carried debt | Paanch written Week 2 answers | `____` | `____` | `____` |
| Carried debt | `DDIA_CH8_LINKS.md` lines 10–13 | `____` | `____` | `____` |
| Carried debt | Teesra cleanup check | `____` | `____` | `____` |
| Carried debt | Week 1 Din 7 · `2026-08-24` | `____` | `____` | `____` |
| Carried debt | `job_executions` ka identifier (`P-11`) | `____` | `____` | `____` |
| Carried debt | `completed_at` (`D-22` Cost 10) | `____` | `____` | `____` |
| Carried debt | Shutdown-vs-lease run (`D-22` Cost 8) | `____` | `____` | `____` |
| Carried debt | **Contract #2 — *protected* ya *narrowed*?** | `____` | `____` | `____` |

**Kitne clean, kitne nahi:** `____`

---

### Week 3 handoff — Week 4 ka input

Teen headings, exactly ye teen, aur **pehli do word-for-word `WEEK_01`/`WEEK_02` jaisi.** File:
`docs/daily/WEEK_03_HANDOFF.md`.

> **Week 2 me ye check FAIL hui thi** — headings `## 1. What Stuck` shape me likhi gayi thi, to
> *"word-for-word identical"* wali condition tooti. Content sahi tha, shape galat. `Select-String -Pattern
> '^## What'` se pakdi gayi.

| Heading | Matlab | Likha? |
|---|---|---|
| **What Stuck** | bina notes ke, blank editor, scratch se rebuild kar sakta hoon | `____` |
| **What Needs Reinforcement** | pehchaan leta hoon, par viva pressure me derive nahi kar paunga — *"haan haan ye to pata hai"* iss category ka signal hai | `____` |
| **What Week 4 Must Not Assume** | wo empirical reality aur khule hole jo Week 4 Din 1 given maane — aur agar chain kisi din pe tooti, uss din ka naam bhi | `____` |

**Dono definitions file me likhi jaati hain**, memory me nahi. Seeds starting points hain, verdict nahi —
agar honest jawab alag hai to item **move** hota hai, aur wahi iss list ka poora point hai.

| Heading | Seeds (verdict nahi) |
|---|---|
| **What Stuck** | side effect ki identity pe `UNIQUE` · `ON CONFLICT` ka `rowcount` padhna · dedup at enqueue aur at execute ke **alag scopes** · crash beech me: side effect committed + mark lost |
| **What Needs Reinforcement** | outbox ki atomicity ki asli limit (database ke bahar wala side effect) · `25P02` aur aborted transactions · property test ka scope vs uska wording · `NULL` + `UNIQUE` |
| **What Week 4 Must Not Assume** | fencing token **abhi bhi nahi hai** (`D-22` Cost 7) · `attempts = 4` overdraft (`P-27`) · property test ke known limits · aur jo bhi iss hafte `[INFERRED]` raha |

---

### Hafte ke process findings

Ye numbers nahi hain, par ye hi batate hain ki hafte ka evidence kitna bharosemand hai.

| Kya | Kitni baar / kahan | Detail |
|---|---|---|
| **Seal tooti (`E8`)** — kisi step ka KEY section measurement se **pehle** khula, ya answers file ka mtime baad ka tha | `____` | Wo step *reconstruction* score karta hai, aur wo yahan naam se likha jaata hai: `____` |
| **Decorative check ship hui (`P-18`/`E7`)** — *mechanism maujood* aur *mechanism ghayab* column same nikle | `____` | Kaunsi check, aur uska rewrite: `____` |
| **Zero-duplicate run ko dedup ka evidence samajha gaya** (`P-12` iss hafte ka roop) | `____` | Kahan, aur wo pakda gaya ya ship ho gaya: `____` |
| **Scope pressure (`E9`)** — mann kiya ki agla item aaj hi kar lein | `____` | Kaunsa item, aur wo signal kis hard problem ko avoid kar raha tha: `____` |
| **`💡` apne shabdon me** — iss hafte ka naya rule | `____` / 6 din | Week 2 me ye `0 / 5` tha |
| **Answers file, step se pehle** | `____` / 6 din | Week 2 me ye `1 / 6` tha (Din 3) |
| **Score wapas aaya?** — missing score ek acha score nahi hota | `____` | Kitne din score ke saath: `____` |

---

### ❓ Week 4 ki taraf — pehla sawaal

`____`

*(Week 4 ka preview plan me ek line hai: load, observability, aur writeup. Iss hafte ke evidence me se wo
sawaal jo uss line ko sharp karta hai — wo yahan.)*
