# WEEK 2 — Lease, heartbeat, reaper: atka hua job wapas kaun laayega

**Layer: L0 + L2** · Daily log with measurements, self-checks, and unresolved items.
Plan: [`../planning/WEEK_02.md`](../planning/WEEK_02.md) · Decisions: [`../DECISIONS.md`](../DECISIONS.md)

> **Plan intent rakhta hai, ye file outcome rakhti hai.** Jo bhi number, verdict ya score iss hafte me
> nikla, wo yahan aata hai — plan me kabhi nahi. Aur plan ko reality se match karne ke liye **edit nahi**
> karna: dono files apna sach rakhti hain, aur unka farq khud ek finding hai (E2).
>
> **Ye file abhi khali template hai.** Har `____` ek jagah hai jo uss din shaam bharti hai. Jo value aaj
> tak measure nahi hui, wo `____` rehti hai — plausible number likhna sabse mehnga shortcut hai. Agar koi
> cheez measure nahi ho paayi, `[NO EVIDENCE]` likho, blank ko guess se mat bharo.
>
> Har claim pe ek label: `[MEASURED]` (tumne khud chalaya) · `[MEASURED-R]` (reviewer ne chalaya) ·
> `[INFERRED]` (mechanism se reason kiya) · `[NO EVIDENCE]` (judgement, aur waise hi labelled).

---

## Contents

- [Stage Day — slip register](#stage-day--slip-register)
- [Divergence — Din 1 ki subah ka bench check (E2)](#divergence--din-1-ki-subah-ka-bench-check-e2)
- [Din 1 — Problem statement, phir lease column](#din-1--problem-statement-phir-lease-column-____)
- [Din 2 — Reaper: recovery bahar se aati hai](#din-2--reaper-recovery-bahar-se-aati-hai-____)
- [Din 3 — 🎯 Zinda par slow worker: ek job, do execution](#din-3--zinda-par-slow-worker-ek-job-do-execution-____)
- [Din 4 — Bounded retry, backoff, jitter](#din-4--bounded-retry-backoff-jitter-____)
- [Din 5 — `dead_letter` + graceful shutdown](#din-5--dead_letter--graceful-shutdown-____)
- [Din 6 — Close: reconcile, likho, handoff](#din-6--close-reconcile-likho-handoff-____)
- [Week close — reconcile chain aur handoff](#week-close--reconcile-chain-aur-handoff)

---

## Stage Day — slip register

Stage Day ka apna din hai (Din 7 ke agle din), aur uska **koi** `src/` change nahi hai. Yahan sirf ek cheez
likhi jaati hai: kaunsa item exit pe **file me** dikha aur kaunsa nahi. Exit criterion ek **file state** hai
— file kholke check hota hai, "kar liya" se nahi.

Label ek hi hai: **slip**. *Deferral* nahi. Deferral ek faisla hai jiska owner hota hai; slip ek din hai jo
nikal gaya. `POSTMORTEMS.md` ki entry #2 poore Week 0 se *"deferred"* label ke saath ghoom rahi thi jabki
honest label hamesha *"slipped"* tha — wahi galti dobara nahi.

**Stage Day date:** `2026-08-22` `[MEASURED-R]` — from file mtimes on the four artifacts plus the system date, not from a recorded start.

> **A gap in the date chain, recorded because it cannot be reconstructed later.** Din 6's log entry is
> `2026-08-19`. The plan's BENCH block *inferred* Din 7 as `2026-08-20`. Stage Day measures as
> `2026-08-22`. **Din 7 has no log entry at all** (`docs/logs/WEEK_01.md` ends at `# DIN 6`), so the
> day between `08-19` and `08-22` is unaccounted for in writing. This is not a Stage Day slip — it is a
> Week 1 Din 7 documentation gap, and it is carried below.

| Item | Exit criterion (file state) | Exit pe file me kya tha | Slip? | Ye item **specifically** kya maangta hai |
|---|---|---|---|---|
| `POSTMORTEMS.md` entry #2 | Third `## Incident` heading exists; answers the protection-vs-coverage question | `## Incident 02 — Cloudflare` present. Protection-vs-coverage answered explicitly, with a `[INFERRED — Relay extension]` tag separating the reviewer-supplied framing from the source | **No** | Nothing. Closed. Reviewer applied 9 factual corrections against the source — see corrections table below |
| `POSTMORTEMS.md` entry #3 (`P-06`, apna incident) | `## Incident` heading; cites `P-06` by name; contains the `pg_stat_activity` blast-radius table, the "resolution came from outside" line, and the age-not-established uncertainty | All four present. Blast-radius table has PIDs 53/61/45/1724, `pg_terminate_backend` line present, 5-day inferred-upper-bound recorded as inferred | **No** | Nothing. Closed. Reviewer removed one **fabricated** number (`12ms`) and corrected the four-session state claim, which contradicted `P-06`'s own table |
| DDIA Ch 7 doosra pass + Ch 8 intro | `DDIA_CH7_SUMMARY.md` ends with a `## Links` section, each line → a named `D-`/`P-`; `DDIA_CH8_LINKS.md` exists with ≥5 lines, no prose summary | CH7: `## Links — kaunsi line kis entry se judi hai`, 5 lines, each with a named entry. CH8: new file, 5 lines, no prose | **No** | Nothing. Closed. One right-hand side (`"Week 2 Reaper"`) was not an existing entry and was repointed to `P-06` by the reviewer |
| `docs/daily/WEEK_01_HANDOFF.md` (teen headings) | Three headings, exact names, exact order; none empty; both definitions written in the file | All three present in order, 4 + 2 + 4 lines, both definitions written out | **No** | Nothing. Closed |

**Gate arithmetic: 3 items, 3 closed. 0 slipped.** First week in the project where the Stage-Day-style
items did not slip — and the reason is structural, not motivational: they had their own day with
file-state exit criteria instead of being absorbed into a build day. `POSTMORTEMS.md` entry #2 had been
carrying a *"deferred"* label since Week 0; it is now closed, and the label was always *"slipped"*.

> **One process finding, and it is the plan's own warning firing on the plan's own gate.** The first
> gate check ran against **unsaved editor buffers**: all four files were on disk as
> `0 B` / stale (`POSTMORTEMS.md` `2787 B`, last written `2026-08-14`; `DDIA_CH7_SUMMARY.md` last
> written `2026-08-11`; the two new files `0 B`). The work was reported complete and, measured, was
> absent. Eight minutes later the same four paths measured `10415 / 48850 / 2188 / 1962 B`.
>
> Nothing was lost, and this is worth a line rather than a shrug: the plan says *"check karne ka
> tareeka teen file kholna hai, 'lagta hai ho gaya' nahi"* — and the thing that nearly passed the gate
> was **an editor showing content that the filesystem did not have**. Opening the file in the editor
> would *also* have shown content. So the check has to read the file **from disk**, and `git status`
> cannot help here because `docs/daily/` and `docs/roadmap/` are gitignored. This is `P-18`'s shape at
> the process level: a verification step that passes equally whether or not the mechanism is present.

**Slip line kaisi honi chahiye.** *"postmortems pending"* ek slip line nahi hai — wo status hai. Slip line
me wo cheez hoti hai jo item ko **abhi** chahiye: kaunsa source pick nahi hua, kaunse kitne pages bache,
kaunsi heading khali hai. Agar line padh ke agla kadam pata nahi chalta, line adhoori hai.

**Partial completion per item likhi jaati hai**, item-level pe — "Stage Day mostly ho gaya" jaisi line
kahin nahi jaati.

**Ye slip zinda kahan rehta hai:**

| Kahan | Kya likha jaata hai | Bhara? |
|---|---|---|
| DoD ka carried-debt group (`WEEK_02.md`) | Stage Day items: **nothing to carry, 3/3 closed.** What *does* carry is the Din 7 debt below, and it is a Week 1 item, not a Stage Day one | ✅ recorded here |
| `LEARNING_LOG.md` open-items table | Same — no Stage Day item to add. The Din 7 debt needs a row, owner = user | ❌ **not done** — needs the Din 7 question answered first (see below) |

**Carried into Din 1 — Week 1 Din 7 debt, and this is the only open item on the board:**

| Item | Status | What it specifically needs |
|---|---|---|
| **Din 7 has no log entry** | Open `[MEASURED-R]` — `docs/logs/WEEK_01.md` ends at `# DIN 6` (`2026-08-19`) | Either the Din 7 entry gets written from the day's actual output, **or** it is recorded that Din 7 was not run and the BENCH block's provenance is corrected. Right now the plan's BENCH block says *"Measured on: Din 7 ke end pe"* and reports 86 rows / `max(id) 87`, while `CURRENT_WEEK.md` reports Din 6 close as 78 rows / `max(id) 78` / seq `79`. **Those two cannot both be Din 6.** So something was run and measured after Din 6 — but there is no entry saying what |
| **The five written Week 2 answers** | Open, and this is the fourth slip in a row for the same item | `CURRENT_WEEK.md` names them: the reaper's predicate with today's columns and why it fails, the smallest schema addition and the new failure it creates, 41 versus 63, and the short lease. Slipped Din 5 Step 6 → Din 6 Step 2 → Din 7 → now. `CURRENT_WEEK.md` states the blocking rule in its own words: *"Week 2 Din 1 should not start before it exists in his own words."* **This is deliberately not being written for the user** |
| `CURRENT_WEEK.md` still points at Week 1 | Open | Repoint to Week 2 + update the week status table. Plan assigns this to **Din 1's** log obligation, so it is on schedule, not late |

**Gate ka result:** Din 1 tab tak shuru nahi hota jab tak teeno exit criteria satisfy na ho. Handoff list
ki **teesri heading** khali hone wala slip Din 1 ko **rok deta hai** — wo heading Din 1 Step 1 ka input hai.

- **Gate result:** ✅ **PASS** on all three Stage Day exit criteria, verified by reading the four files
  **from disk** (sizes and `## ` headings grepped, not eyeballed in an editor).
- Din 1 shuru hua? **Not yet.** The Stage Day gate is clear; Din 1's own prereq table is not — the
  `psql` bench check is still unrun, and it is Din 1's first executable step.
- Kitne din late, aur kis item ki wajah se? Stage Day itself: **zero days late.** The unaccounted day
  sits between Din 6 (`08-19`) and Stage Day (`08-22`), and it belongs to Din 7, not here.
- Din 1 kis named debt ke saath shuru hua? **Two named debts, both Week 1's:** (1) no Din 7 log entry,
  so the BENCH block's `[MEASURED]` provenance is unverifiable; (2) the five written Week 2 answers,
  fourth consecutive slip. Din 1's Step 1 consumes the handoff's third heading **and** *"Din 5/Din 7 ka
  likha hua text"* as given — half of that given does not exist.
- **What this does NOT block:** the handoff file's third heading exists and is good, so Din 1 Step 1 has
  its primary input. The BRIEF for Din 1 is written and carries the five answers as **Step 0**, which is
  the honest place for a debt that has now outlived three attempts to schedule it.

---

## Divergence — Din 1 ki subah ka bench check (E2)

Din 1 Step 1 se **pehle** bench check hota hai. Match kare to ek line likh do aur aage badho. Match na kare
to **Step 1 rukta hai**, pehle divergence classify hoti hai — classify ka matlab naye numbers ka **cause**
naam lena hai, *"numbers alag hain"* likhna nahi.

**Check ki date:** `____` · **Match?** `____`

| Kya check kiya | Expected (BENCH block se copy) | Mila (`psql` se, verbatim) | Match? |
|---|---|---|---|
| `failed` / `running` / `succeeded` counts | `____` | `____` | `____` |
| total rows | `____` | `____` | `____` |
| `max(id)` aur `jobs_id_seq` `last_value` | `____` | `____` | `____` |
| `job_executions` rows | `____` | `____` | `____` |
| jobs 41 / 63 / 65 ka `status` | `____` | `____` | `____` |
| job 75 ka `status` | `____` | `____` | `____` |
| `\d jobs` — columns aur `pg_constraint` definition | `____` | `____` | `____` |
| connections to `relay`, `idle in transaction`, worker processes | `____` | `____` | `____` |

**Classification — E2 ki kaunsi row lagi:** `____`
*(bhoola hua worker `P-13` · fixture chhed di gayi · job 75 resurrect · rows delete / consumed sequence
value `P-05` · koi migration chali)*

**Cause, naam se:** `____`
**Evidence jo cause ko support karta hai** (PID + start time, `alembic history` / `alembic current` ka
output, jo bhi laagu ho): `____`
**Naya baseline — iss hafte ka arithmetic yahan se shuru hoga:** `____`

**Ye nahi hota, aur rule dono directions me lagta hai:**

- Plan ka BENCH block **edit nahi** hota. Wo Din 7 ke end ka `[MEASURED]` snapshot hai; usko badalna ye
  record mita dena hai ki plan **kis** state ke against likha gaya tha.
- Reality **repair nahi** hoti. Counts wapas plan wale numbers pe laane ke liye rows insert/delete karna
  manufactured evidence hai, aur uske baad poore hafte ka arithmetic ek banayi hui baseline pe khada hoga.

**Agar fixture (41/63/65) khatam ho gayi:** Din 2 apni stuck rows **seed** karega, aur yahan likha jaata
hai ki 41/63/65 ka evidence dobara reproducible **nahi** hai: `____`

---

## Din 1 — Problem statement, phir lease column (`____`)

**Original goal (from the plan):** `____`

**Goal met?** `____` — yes / no / partial me se ek. `partial` likho to **kaunsa hissa** hua aur kaunsa nahi,
wo isi line me.

**Anything else learned?** `____` — ye field goal-met se **alag** hai aur alag hi rehta hai. Kuch naya
seekhna aur jo shuru kiya tha usko khatam karna do alag baatein hain; ek se doosri ko dhakna iss log ki
sabse purani galti hai.

---

### 📊 Measured / Observed

**Opening check (`P-13`, `P-06`) — din ka pehla kaam, aur ye har din hota hai:**

| Kya | Value | Label |
|---|---|---|
| worker processes chal rahe hain | `____` | `____` |
| `idle in transaction` sessions | `____` | `____` |
| connections to `relay` | `____` | `____` |

**M1 — `____`**

```
____
```

**M2 — `____`**

```
____
```

**Aaj ye numbers likhne hain (plan ka Din 1 obligation):**

| Kya | Value / text | Label |
|---|---|---|
| **Problem statement ka poora text** (apne shabdon me, Step 1 ka output) | `____` | — |
| Chuna hua column name, type, nullability | `____` | `____` |
| Migration up + down chala — `downgrade` ka actual output | `____` | `____` |
| `NULL` backfill ka faisla (migration me backfill **ya** `IS NULL` branch) | `____` | — |
| Uss faisle ki **cost**, apne shabdon me | `____` | — |
| Claim ke baad ek row ka lease value (non-null) | `____` | `____` |
| Purani `running` rows (41/63/65) pe lease column ka value | `____` | `____` |
| Three-valued logic wala differential — dono counts | `____` | `____` |
| `Interim_Guarantee` — kaunsa contract point kis ke against trade hua (*narrows*, *does not close*) | `____` | — |

**Closing reconciliation** — opening counts BENCH block se, delta aaj ka. **Kabhi `max(id)` se nahi, kabhi
id contiguity se nahi:**

| Line | Value |
|---|---|
| opening `pending` / `running` / `succeeded` / `failed` / total (BENCH block) | `____` |
| `+` aaj enqueue hui probe jobs (ids **naam se**) | `____` |
| `−` unme se jo `succeeded` / `failed` hui | `____` |
| `=` closing counts | `____` |
| `psql` ke actual counts | `____` |
| Match? | `____` |
| `job_executions` delta | `____` |
| Migration ne kisi row ka `status` badla? | `____` |

Match na kare to wo **finding** hai (E5), adjust karke balance nahi hoti. Pehla suspect ek bhoola hua worker
(`P-13`). Finding: `____`

**Cleanup:** stdout capture file (`python -u` wali) delete hui? `____` — relevant output pehle upar copy
hua? `____` · Probe **rows delete nahi** hoti; unke ids: `____`

**Commit:** staged paths naam se (`.` kabhi nahi): `____`

---

### 💡 What I Understood

`____`

*(Apne shabdon me. Jo cheez sirf padh ke samajh aayi, uske saath likho ki wo padhi hui hai — recognisable
aur recallable me farq isi line se dikhta hai.)*

---

### 🧠 Self-Check (honest — `____` / `____` self-answered)

`____`

`idk` ek valid answer hai aur wo **not-answered** ki tarah score hota hai. Guess ko knowledge ki tarah
likhna dono directions me dishonest hai — jo aata tha usko miss likhna bhi revision material kharab karta
hai.

**Corrections — jo maine kaha aur jo measurement/review ne refute kiya:**

| # | I said | Actual | The transferable lesson |
|---|---|---|---|
| `__` | `____` | `____` | `____` |

*(Ye table kabhi delete nahi hoti, na chhoti hoti hai.)*

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

## Din 2 — Reaper: recovery bahar se aati hai (`____`)

**Original goal (from the plan):** `____`

**Goal met?** `____` — yes / no / partial, aur partial pe kaunsa hissa.

**Anything else learned?** `____` — goal-met se alag field.

---

### 📊 Measured / Observed

**Opening check (`P-13`, `P-06`) plus aaj ka extra: 41/63/65 aur 75 abhi bhi wahi hain?**

| Kya | Value | Label |
|---|---|---|
| worker processes / `idle in transaction` / connections | `____` | `____` |
| jobs 41 / 63 / 65 ka `status` | `____` | `____` |
| job 75 ka `status` | `____` | `____` |

**Pre-reclaim state — reaper chalane se PEHLE ka verbatim output.** Ye reclaim ke baad **wapas nahi aa
sakta**, isliye pehle yahan:

```
____
```

**M1 — `____`**

```
____
```

**Aaj ye numbers likhne hain (plan ka Din 2 obligation):**

| Kya | Value / text | Label |
|---|---|---|
| Likha hua predicate, **as-written** (traps padhne se pehle wala) | `____` | — |
| Per-row verdict — job **41** | `____` | `____` |
| Per-row verdict — job **63** (duplicate risk noted?) | `____` | `____` |
| Per-row verdict — job **65** (duplicate risk noted?) | `____` | `____` |
| Per-row verdict — job **75** (untouched?) | `____` | `____` |
| Ek hi output me chaar rows ka farq dikha? | `____` | `____` |
| Reclaim latency | `____` | `____` |
| Chuna hua lease expiry + reaper poll interval, **apne reason ke saath** | `____` | — |
| Compare-and-set guard ka affected-row-count | `____` | `____` |
| Din 5 ke liye notice hui baat (`status` akela guard kaafi nahi rehta) | `____` | — |
| Kaunsa number **measure** kiya aur kaunsa **choose** kiya | `____` | — |

**Agar reaper ne fixture row strand ki, ya terminal row sweep kar li (E4):** dono directions finding hain,
aur dono **predicate** ke baare me hain — row ke baare me nahi. Kya hua, aur predicate ka kaunsa hissa
zimmedaar tha: `____`

**Closing reconciliation** — opening counts **Din 1 ke log se** (BENCH block se nahi, wo Din 1 ka opening
tha):

| Line | Value |
|---|---|
| opening counts (Din 1 log) | `____` |
| `+` aaj enqueue hui probe jobs (ids naam se) | `____` |
| `±` reclaim se `running` → `pending` shift | `____` |
| `=` closing counts | `____` |
| `psql` ke actual counts | `____` |
| Match? | `____` |
| `job_executions` delta | `____` |
| Job 75 abhi bhi `failed` aur count me hai? | `____` |

Match na kare to finding (E5), pehla suspect `P-13`: `____`

**Cleanup:** reaper ka stdout capture delete hua? `____` — output pehle log me copy hua? `____` · Reclaim ki
hui rows **delete nahi** hoti, wo ab normal rows hain: `____`

**`DECISIONS.md` me aaj kuch nahi jaata.** `D-22` Din 6 pe likhi jaayegi. Aaj ke numbers yahan `[MEASURED]`
tag ke saath baithe rehte hain taki Din 6 unhe utha sake.

---

### 💡 What I Understood

`____`

---

### 🧠 Self-Check (honest — `____` / `____` self-answered)

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

## Din 3 — 🎯 Zinda par slow worker: ek job, do execution (`____`)

**Original goal (from the plan):** `____`

**Goal met?** `____` — yes / no / partial, aur partial pe kaunsa hissa.

**Anything else learned?** `____` — goal-met se alag field.

---

### 📊 Measured / Observed

**Opening check (`P-13`, `P-06`), plus aaj ka extra:**

| Kya | Value | Label |
|---|---|---|
| worker processes / `idle in transaction` / connections | `____` | `____` |
| 41/63/65 ki current state (Din 2 ke baad) | `____` | `____` |
| job 75 abhi bhi `failed`? | `____` | `____` |
| Aaj ki seeded stuck rows ke ids | `____` | `____` |

**Paanch-sawaal ka diagnosis — isi fixed order me, aur count iske BAAD (E3, `P-12`, `P-18`):**

| # | Sawaal | Jawab | Label |
|---|---|---|---|
| 1 | Do distinct `worker_id`, overlapping `executed_at`? | `____` | `____` |
| 2 | Lease expiry versus handler duration — **ek hi clock** me | `____` | `____` |
| 3 | Reaper uss window me actually chala? | `____` | `____` |
| 4 | Row uss waqt claimable thi? | `____` | `____` |
| 5 | Log poora hai (`python -u`, aakhri line adhoori nahi)? | `____` | `____` |

**Duplicate count — sirf paanchon jawab likhne ke BAAD:**

| Run | Duplicate count | Overlap window proven? | Label |
|---|---|---|---|
| Run 1 — heartbeat **ke bina** | `____` | `____` | `____` |
| Run 2 — heartbeat **ke saath** | `____` | `____` | `____` |

**Zero ka matlab:** zero duplicates ka matlab hai overlap window **bani hi nahi** — ye nahi ki system safe
hai. Jis sawaal pe "nahi" mila wahi aaj ka result hai: `____` · Agle run me badalne wala **ek** variable
(handler duration / lease duration / reaper poll interval): `____`

**Aaj ye likhna hai (plan ka Din 3 obligation):**

| Kya | Value / text | Label |
|---|---|---|
| Chuna hua handler duration, apne reason ke saath | `____` | — |
| Dono run ka expiry-se-completion gap | `____` | `____` |
| Heartbeat ke teen faisle — interval | `____` | — |
| Heartbeat ke teen faisle — guard | `____` | — |
| Heartbeat ke teen faisle — sender (kaun bhejta hai) | `____` | — |
| Teeno ki cost | `____` | — |
| Pehle worker ke mark statement ka **verbatim** output | `____` | `____` |
| Heartbeat ne window **narrow** kiya — kitna, aur wo band kyun nahi hua | `____` | `____` |
| `count(*) > 1` ka matlab badalna (`P-11`) — aaj ka evidence | `____` | `____` |

**Closing reconciliation** — opening counts **Din 2 ke log se**:

| Line | Value |
|---|---|
| opening counts (Din 2 log) | `____` |
| `+` aaj seed/enqueue hui rows (ids naam se) | `____` |
| `=` closing counts, aur `psql` ka actual | `____` |
| Match? | `____` |
| `job_executions` delta — duplicate rows isme count hote hain | `____` |

Match na kare to finding (E5). Pehla suspect ek bhoola hua teesra worker (`P-13`), doosra suspect reaper ka
ek extra run: `____`

**Cleanup:** teen stdout capture files (worker A, worker B, reaper) delete hui? `____` — andar ka relevant
output pehle upar copy hua? `____` · Probe rows delete nahi hoti, ids: `____`

**`DECISIONS.md` me aaj kuch nahi.** `D-21` ka amendment aur `D-22` dono Din 6 pe. Aaj sirf evidence banta
hai.

---

### 💡 What I Understood

`____`

---

### 🧠 Self-Check (honest — `____` / `____` self-answered)

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

## Din 4 — Bounded retry, backoff, jitter (`____`)

**Original goal (from the plan):** `____`

**Goal met?** `____` — yes / no / partial, aur partial pe kaunsa hissa.

**Anything else learned?** `____` — goal-met se alag field.

---

### 📊 Measured / Observed

**Opening check (`P-13`, `P-06`):**

| Kya | Value | Label |
|---|---|---|
| worker processes / `idle in transaction` / connections | `____` | `____` |
| `attempts` ka current state (kitni rows non-zero) | `____` | `____` |

**Aaj ye likhna hai (plan ka Din 4 obligation):**

| Kya | Value / text | Label |
|---|---|---|
| `attempts` increment point ka faisla (claim pe ya failure pe), **apni cost ke saath** | `____` | — |
| *"abhi nahi"* store karne ka faisla, apni cost ke saath | `____` | — |
| Backoff ka formula, **verbatim** | `____` | — |
| Jitter ka formula, alag se | `____` | — |
| Jitter kyun — apne shabdon me | `____` | — |
| Retry ka `status` write compare-and-set guard ke saath? affected-row-count | `____` | `____` |
| Ek always-failing job ke **measured inter-attempt gaps** (`executed_at` diffs, `Etc/UTC`) | `____` | `____` |
| Kai jobs ka **jitter spread** | `____` | `____` |
| Bounded-out job pe final `attempts` | `____` | `____` |
| Log poora hai — failure lines ka count versus `attempts` (`P-18`) | `____` | `____` |

**M1 — `____`**

```
____
```

**Closing reconciliation** — opening counts **Din 3 ke log se**:

| Line | Value |
|---|---|
| opening counts (Din 3 log) | `____` |
| `+` aaj enqueue hui `boom` jobs (ids naam se) | `____` |
| `=` closing counts, aur `psql` ka actual | `____` |
| Match? | `____` |
| `job_executions` delta — har attempt ek row | `____` |

Match na kare to finding (E5): `____`

**Cleanup:** worker stdout capture delete hua? `____` — output pehle upar copy hua? `____` · `boom` jobs ke
ids (rows delete nahi hoti): `____`

**`DECISIONS.md` me aaj kuch nahi.** `D-23` Din 6 pe likhi jaati hai, aaj ke measured delays ke saath.

---

### 💡 What I Understood

`____`

---

### 🧠 Self-Check (honest — `____` / `____` self-answered)

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

## Din 5 — `dead_letter` + graceful shutdown (`____`)

**Original goal (from the plan):** `____`

**Goal met?** `____` — yes / no / partial, aur partial pe kaunsa hissa.

**Anything else learned?** `____` — goal-met se alag field.

---

### 📊 Measured / Observed

**Opening check (`P-13`, `P-06`):**

| Kya | Value | Label |
|---|---|---|
| worker processes / `idle in transaction` / connections | `____` | `____` |
| `attempts` aur `status` ka current spread | `____` | `____` |

**Aaj ye likhna hai (plan ka Din 5 obligation):**

| Kya | Value / text | Label |
|---|---|---|
| Constraint ka **purana naam aur purani definition, verbatim** | `____` | `____` |
| Ek migration ya do — faisla, apni cost ke saath | `____` | — |
| `NOT VALID` ke baad `VALIDATE CONSTRAINT` — dono ka output | `____` | `____` |
| `downgrade` ka actual output **ek `dead_letter` row ke saath** | `____` | `____` |
| Terminal writer ka faisla (A ya B), apni cost ke saath | `____` | — |
| `max_attempts` → `dead_letter` transition ka guard + affected-row-count | `____` | `____` |
| Always-failing job ka `attempts` count `dead_letter` pe pahunchte waqt | `____` | `____` |
| Shutdown pe lease ka faisla, apni cost ke saath | `____` | — |
| Teen durations ek line pe: handler · lease · grace period | `____` | `____` |
| SIGTERM ke baad naye `running` rows | `____` | `____` |
| `ACCESS EXCLUSIVE` measurement ka result — **ya** saaf likha hua ki attempt fail hua aur procedure kya thi | `____` | `____` |
| Log poora hai — `Claimed job` lines ka count, aur file ka aakhri line (`P-18`) | `____` | `____` |

**Shutdown ek lease ka sawaal hai, signals ka nahi (`P-15`):** grace period handler se bandha hai, aur
Relay handler ko bound nahi karta. Aaj ka evidence: `____`

**Closing reconciliation** — opening counts **Din 4 ke log se**. Kabhi `max(id)` se nahi:

| Line | Value |
|---|---|
| opening counts (Din 4 log) | `____` |
| `+` aaj enqueue hui probe rows (ids naam se) | `____` |
| `±` `dead_letter` me gayi rows (paanchwan bucket ab exist karta hai) | `____` |
| `=` closing counts, aur `psql` ka actual — **paanchon** buckets | `____` |
| Match? | `____` |
| `job_executions` delta | `____` |

Match na kare to finding (E5): `____`

**Cleanup:**
- Worker aur reaper stdout capture delete hua? `____` — relevant output pehle upar copy hua? `____`
- Lock-queue measurement ke liye jaan-boojh ke banayi `idle in transaction` session band hui —
  `COMMIT`/`ROLLBACK` se ya `pg_terminate_backend` se? `____` · **PID naam se:** `____`
  *(`P-06` ka pura sabaq: chhoda hua session locks pakde baitha rehta hai, aur koi participant khud usko
  resolve nahi kar sakta. Aaj wo session jaan-boojh ke bani thi, to uska hatana bhi jaan-boojh ke likha
  jaata hai.)*
- `boom` jobs aur `dead_letter` probe row ke ids (rows delete nahi hoti): `____`

**`DECISIONS.md` me aaj kuch nahi.** `D-06` ka amendment Din 6 pe. Aaj sirf evidence — `D-06` ka Cost 4 ek
**prediction** hai, aur aaj ka output batata hai wo prediction poora tha ya adhoora: `____`

---

### 💡 What I Understood

`____`

---

### 🧠 Self-Check (honest — `____` / `____` self-answered)

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

## Din 6 — Close: reconcile, likho, handoff (`____`)

**Original goal (from the plan):** `____`

**Goal met?** `____` — yes / no / partial, aur partial pe kaunsa hissa.

**Anything else learned?** `____` — goal-met se alag field.

---

### 📊 Measured / Observed

**Opening check (`P-13`, `P-06`):**

| Kya | Value | Label |
|---|---|---|
| worker processes / `idle in transaction` / connections | `____` | `____` |

**Aaj ka grep output — number assign karne ke din chalta hai, plan likhne ke din nahi (E6):**

```
grep -n "^## \`\?D-" docs/DECISIONS.md
____

grep -n "^## P-" docs/PROBLEMS.md
____
```

| Kya | Value |
|---|---|
| Grep plan ke expected ranges se match karta hai? | `____` |
| Aaj assign hue `D-` numbers | `____` |
| Aaj assign hue `P-` numbers | `____` |
| Collision mili? (naya entry hilta hai, purana kabhi nahi) | `____` |
| Dangling citation mili? | `____` |

**Doc-sync — kya actually likha gaya (files kholke check, `git status` se nahi):**

| File | Kya gaya | Ho gaya? |
|---|---|---|
| `docs/DECISIONS.md` — `D-22` (lease duration + handler timeout, ek decision) | `____` | `____` |
| `docs/DECISIONS.md` — `D-23` (retry policy: increment point, backoff formula, jitter ka reason) | `____` | `____` |
| `docs/DECISIONS.md` — `D-06` amendment (`dead_letter` via `NOT VALID` + `VALIDATE CONSTRAINT`) | `____` | `____` |
| `docs/DECISIONS.md` — `D-21` amendment (`count(*) > 1` ka matlab) | `____` | `____` |
| Har naye entry ka **non-empty `Cost`**, aur har `Cost`/`Rejected` line pe ek provenance tag | `____` | `____` |
| `docs/PROBLEMS.md` — Din 1–5 ki bachi hui entries | `____` | `____` |
| `docs/MAP.md` — per naye entry ek index row, **reasoning nahi** | `____` | `____` |
| `docs/LEARNING_LOG.md` — open-items table, Week 2 row, next-free numbers | `____` | `____` |
| `docs/roadmap/CURRENT_WEEK.md` — week status table + pointer Week 3 pe | `____` | `____` |
| `docs/daily/WEEK_02_HANDOFF.md` — teen headings, dono definitions, content | `____` | `____` |
| Commit — staged paths naam se, `.` kabhi nahi | `____` | `____` |

`docs/roadmap/` aur `docs/daily/` gitignored hain — wo do files `git status` me dikhengi hi nahi, isliye
kholke check hoti hain.

**Cleanup:** aaj naye probe rows nahi bante. Reconcile ke liye koi temporary capture file bani? `____` —
delete hui? `____` — output pehle log me copy hua? `____` · Hafte bhar ki probe rows **delete nahi** hoti,
unke ids aaj ki chain me count hote hain: `____`

---

### 💡 What I Understood

`____`

---

### 🧠 Self-Check (honest — `____` / `____` self-answered)

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

**Full reconcile chain:**

| Line | Kahan se | Value |
|---|---|---|
| Week opening counts | BENCH block (ya E2 ka naya baseline) | `____` |
| `+` Din 1 delta | Din 1 log entry | `____` |
| `+` Din 2 delta | Din 2 log entry | `____` |
| `+` Din 3 delta | Din 3 log entry | `____` |
| `+` Din 4 delta | Din 4 log entry | `____` |
| `+` Din 5 delta | Din 5 log entry | `____` |
| `=` expected closing | arithmetic | `____` |
| aaj ke `psql` counts — **paanchon** status buckets + total | aaj ka opening check | `____` |
| `job_executions` — opening + per-din delta = aaj ka count | log + aaj ka output | `____` |
| **Chain juda?** | — | `____` |

**Week close pe `running` rows — ye ek DoD item hai, aur zero ho ya na ho, dono cases likhe jaate hain:**

| Kya | Value | Label |
|---|---|---|
| `running` count at close | `____` | `____` |
| Uske ids (agar zero nahi) | `____` | `____` |
| Ye ids Week 3 ka input hain — handoff me gaye? | `____` | — |

Non-zero `running` ka matlab hai hafte ke end pe bhi kaam atka pada hai. Usko *"reaper chalake saaf kar
diya"* karke count zero banana **arithmetic adjust karna** hai — wo E5 hai aur wo nahi hota.

**Sequence:**

| Kya | Value | Label |
|---|---|---|
| `jobs_id_seq` `last_value` | `____` | `____` |
| `max(id)` | `____` | `____` |
| Gap — aur wo `P-05` ka evidence hai | `____` | `____` |

**Agar chain nahi judi (E5):** mismatch **finding ki tarah** likhi jaati hai, difference ko kisi din me fit
karke chain band nahi hoti.

| Kya | Value |
|---|---|
| Kaunsa din toota | `____` |
| Kitna difference | `____` |
| Kya check kiya gaya (bhoola hua worker `P-13`, extra reaper run, delete hui row, consumed sequence value) | `____` |
| **Ye din handoff ki teesri heading me naam se gaya?** | `____` |

Toote hue din ka naam Week 2 ke handoff ki teesri heading me jaata hai, kyunki Week 3 ko pata hona chahiye
ki **kis din ka number bharosa ke layak nahi hai**.

---

### Definition of Done — week close pe audit

Plan ka koi box shipped file me ticked nahi tha. Ab har item ka ek status hai, aur **har untick ek line
maangta hai**: *deliberately deferred* apne **owner** ke saath, **ya** *slipped* uske saath jo usko
**specifically** chahiye. Do me se ek — dono nahi, koi nahi bhi nahi.

| Group | DoD item | Status | Evidence | Untick ho to: deferred (owner) / slipped (kya chahiye) |
|---|---|---|---|---|
| Build | `____` | `____` | `____` | `____` |
| Measured | Centrepiece duplicate count | `____` | `____` | `____` |
| Measured | Reaper ki reclaim latency | `____` | `____` | `____` |
| Measured | Chuni hui lease duration + uske peeche ka measurement | `____` | `____` | `____` |
| Measured | Always-failing job ka `attempts` `dead_letter` pe | `____` | `____` | `____` |
| Measured | Week close pe `running` rows ka count | `____` | `____` | `____` |
| Measured | Reaper run jo 41 · 63 · 75 ko **alag** karta hai | `____` | `____` | `____` |
| Likha | `____` | `____` | `____` | `____` |
| Carried debt | Stage Day exit criteria (slip yahan zinda rehta hai) | `____` | `____` | `____` |

**Kitne clean, kitne nahi:** `____`

---

### Week 2 handoff — Week 3 ka input

Teen headings, exactly ye teen, Stage Day wale handoff ke **same shape** me. File:
`docs/daily/WEEK_02_HANDOFF.md`.

| Heading | Matlab | Likha? |
|---|---|---|
| **What Stuck** | bina notes ke, scratch se rebuild kar sakta hoon | `____` |
| **What Needs Reinforcement** | pehchaan leta hoon, par viva pressure me derive nahi kar paunga | `____` |
| **What Week 3 Must Not Assume** | wo baatein jo Week 3 taken-for-granted na le — isme toote hue din ka naam bhi | `____` |

---

### Hafte ke process findings

Ye numbers nahi hain, par ye hi batate hain ki hafte ka evidence kitna bharosemand hai.

| Kya | Kitni baar / kahan | Detail |
|---|---|---|
| **Seal tooti (E8)** — kisi step ka KEY section measurement se **pehle** khula | `____` | Wo step reconstruction ki tarah score hota hai, aur wo yahan naam se likha jaata hai: `____` |
| **Decorative check ship hui (E7)** — *mechanism maujood* aur *mechanism ghayab* column same nikle | `____` | Kaunsi check, aur uska rewrite: `____` |
| **Scope pressure (E9)** — mann kiya ki agla item aaj hi kar lein | `____` | Kaunsa item, aur wo signal kis hard problem ko avoid kar raha tha: `____` |
| **Score wapas aaya?** — Week 1 me chaar din bina score gaye the, aur missing score ek acha score nahi hota | `____` | Kitne din score ke saath: `____` |

---

### ❓ Week 3 ki taraf — pehla sawaal

`____`

*(Week 3 ka preview plan me ek line hai: idempotency key, aur crash/retry interleavings ke upar ek property
test. Iss hafte ke evidence me se wo sawaal jo uss line ko sharp karta hai — wo yahan.)*
