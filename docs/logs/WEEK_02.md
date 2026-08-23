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

**Check ki date:** `2026-08-23` · **Match?** **Haan — zero divergence, saari aath lines pe.**

| Kya check kiya | Expected (BENCH block se copy) | Mila (`psql` se, verbatim) | Match? |
|---|---|---|---|
| `failed` / `running` / `succeeded` counts | 9 / 3 / 74 | 9 / 3 / 74 | ✅ |
| total rows | 86 | 86 | ✅ |
| `max(id)` aur `jobs_id_seq` `last_value` | 87 / 87 | 87 / 87 | ✅ |
| `job_executions` rows | 57 | 57 | ✅ |
| jobs 41 / 63 / 65 ka `status` | teeno `running` | teeno `running` | ✅ |
| job 75 ka `status` | `failed` | `failed` | ✅ |
| `\d jobs` — columns aur `pg_constraint` definition | 6 columns, `jobs_status_check` 4 values pe | 6 columns, `jobs_status_check` 4 values pe | ✅ |
| connections to `relay`, `idle in transaction`, worker processes | 1 / 0 / 0 | idle sessions 0, worker processes 0 | ✅ |

**Classification — E2 ki kaunsi row lagi:** **koi nahi. E2 aaj trigger hua hi nahi.**

**Aur ye result apne aap me ek finding hai, kyunki iska ek doosra sawaal band hota hai.** BENCH block ka
label `[MEASURED] on Din 7 ke end` tha, par `docs/logs/WEEK_01.md` `# DIN 6` pe khatam hoti hai — Din 7 ki
koi entry nahi hai. To Din 1 ki subah tak ye khula tha ki BENCH block ke numbers asli hain ya kahin se
aaye hain. **Aaj ke bench ne unhe exactly reproduce kar diya (86 / `max(id)` 87 / seq 87 / 57), Din 6 ke
numbers ko nahi (78 / 78 / 79 / 46).** Matlab: Din 7 **chala tha aur measure hua tha** — jo gayab hai wo
sirf uski log entry hai. BENCH block ki provenance theek hai; documentation gap asli hai.

Ye Week 2 ke KEY ki teen possibilities me se **pehli** thi, aur wo `E2`/`P-13` wali nahi thi. Uss
distinction ko `[MEASURED]` ki tarah likhna theek hai, kyunki dono candidate baselines me `8` rows aur
`11` sequence values ka farq tha — reproduce hone ki gunjaish nahi thi.

**Naya baseline — iss hafte ka arithmetic yahan se shuru hoga:** **BENCH block hi baseline hai**, badla
nahi. Din 1 ka closing (niche) usme se delta nikaal ke banta hai.

**Ek carried debt band hota hai, ek nahi:**

| Debt | Ab kya hai |
|---|---|
| *"BENCH block ki `[MEASURED]` provenance unverifiable hai"* | **Band.** Aaj ke bench ne reproduce kar diya `[MEASURED]` |
| *"Din 7 ki log entry maujood nahi hai"* | **Khula.** Numbers verify ho gaye, par Din 7 me kya hua — kaunsa experiment, kaunsa verdict — wo kahin likha nahi hai aur reconstruct nahi hoga. `WEEK_01.md` me ye gap ek line ki tarah rehna chahiye, silently bhara nahi jaana chahiye |

**Ye nahi hota, aur rule dono directions me lagta hai:**

- Plan ka BENCH block **edit nahi** hota. Wo Din 7 ke end ka `[MEASURED]` snapshot hai; usko badalna ye
  record mita dena hai ki plan **kis** state ke against likha gaya tha.
- Reality **repair nahi** hoti. Counts wapas plan wale numbers pe laane ke liye rows insert/delete karna
  manufactured evidence hai, aur uske baad poore hafte ka arithmetic ek banayi hui baseline pe khada hoga.

**Agar fixture (41/63/65) khatam ho gayi:** Din 2 apni stuck rows **seed** karega, aur yahan likha jaata
hai ki 41/63/65 ka evidence dobara reproducible **nahi** hai: `____`

---

## Din 1 — Problem statement, phir lease column (`2026-08-23`)

**Original goal (from the plan):** Problem statement apne shabdon me likhna (aaj ke columns kya measure
karte hain, naive predicate kis direction me fail karta hai, sabse chhoti schema addition, wo addition
kaunsa naya failure laati hai, `Interim_Guarantee`) — **phir** ek column, ek migration dono direction me,
aur claim `UPDATE` me lease ka write. Lease ki **duration** aaj decide nahi hoti.

**Goal met? — `partial`.** Jo hua: bench check (zero divergence), migration up+down, claim lease likhti
hai, backfill decision Option B cost ke saath, three-valued logic differential measured. Jo **nahi** hua:
**Step 0 ke paanch likhe hue answers** (paanchwi baar slip), **Part B ke prediction answers likhit roop me**
(is review ko supply nahi hue, to score nahi ho sakte), **Ch 8 links file me append** (`DDIA_CH8_LINKS.md`
ka mtime abhi bhi `2026-08-22 17:28`, Stage Day ka), aur **cleanup** — Step 7 ke **do worker processes
abhi bhi zinda hain**.

**Anything else learned?** Haan, teen cheezein jo plan ne poochhi hi nahi thi:

1. **Migration chain me ek khaali revision permanently baithi hai** (`79cb2ee38481`, `upgrade(): pass`).
   Step 6 ka reversibility check **pass hua, par ek layer shallow reason se** — `downgrade -1` uss khaali
   revision pe utra, aur wahan column drop hona hi tha. Doosra `downgrade -1` success report karke kuch
   nahi badalta.
2. **Column ka naam `claimed_at` chuna gaya, aur wo *event* hai, *deadline* nahi** — matlab lease ki
   duration Din 2 ke predicate me ghus aayi hai, jabki plan usko `D-22`/Din 6 tak defer karta hai.
3. **Job 88 ka enqueue-to-claim gap `00:01:33.705`** `[MEASURED-R]` — yaani aaj ki apni row pe naive
   `created_at` predicate ka dangerous failure literally reproduce ho sakta tha. Ye number report me nahi
   tha aur ye Step 2 ki poori argument ka apna evidence hai.

---

### 📊 Measured / Observed

**Opening check (`P-13`, `P-06`) — din ka pehla kaam, aur ye har din hota hai:**

| Kya | Value | Label |
|---|---|---|
| worker processes chal rahe hain | 0 | `[MEASURED]` |
| `idle in transaction` sessions | 0 | `[MEASURED]` |
| connections to `relay` | not recorded separately; `idle in transaction` = 0 tha | `[MEASURED]` |

**M1 — bench, zero divergence.** Poora table upar ke Divergence section me hai. Short: `9 / 3 / 74`,
total `86`, `max(id) 87`, seq `87`, `job_executions 57`, 41/63/65 `running`, 75 `failed`. `[MEASURED]`

**M2 — `\d jobs` migration ke pehle aur baad, aur `downgrade` ka cycle** `[MEASURED]`

```
alembic downgrade -1   -> \d jobs  =  6 columns  (claimed_at absent)
alembic upgrade head   -> \d jobs  =  7 columns  (claimed_at | timestamp with time zone | nullable)
```

Aaj shaam re-verified `[MEASURED-R]`:

```
 claimed_at | timestamp with time zone |           |          |
 alembic_version.version_num = 75a845575d2e
```

**M3 — claim lease likhti hai (job 88, `slow` handler, 8 s)** `[MEASURED]`

```
id 88 | status running | claimed_at 2026-08-23 09:46:55.549422+00 | now() 2026-08-23 09:47:05+00   (Etc/UTC)
```

Shaam ko wahi row `[MEASURED-R]`:

```
 id | type | status    | created_at                   | claimed_at                    | claimed_at - created_at
 88 | slow | succeeded | 2026-08-23 09:45:21.84424+00 | 2026-08-23 09:46:55.549422+00 | 00:01:33.705182
 job_executions: job_id 88 | worker-32636 | 2026-08-23 09:46:55.597239+00
```

Teesra column aaj ka sabse kaam ka number hai aur report me nahi tha: **enqueue se claim tak 93.7 s**.
Naive predicate `created_at < now() - interval '60 seconds'` iss row pe **claim hone ke instant** match
kar jaata — job zinda, handler abhi shuru bhi nahi hua, aur reaper usko utha leta. Step 2 ka
"dangerous direction" wala argument aaj apni hi row pe reproduce ho sakta tha.

**M4 — three-valued logic differential** `[MEASURED]`, aaj shaam reproduce `[MEASURED-R]`

```
select count(*) from jobs where status='running' and claimed_at < now();                          -> 0
select count(*) from jobs where status='running' and (claimed_at is null or claimed_at < now());   -> 3
```

**Aaj ye numbers likhne hain (plan ka Din 1 obligation):**

| Kya | Value / text | Label |
|---|---|---|
| **Problem statement ka poora text** (apne shabdon me, Step 1 ka output) | Substance niche 💡 me hai, par **apne shabdon me disk pe nahi likha gaya** — ye field abhi bhi user ka hai | `[NO EVIDENCE]` for authorship |
| Chuna hua column name, type, nullability | `claimed_at`, `DateTime(timezone=True)` → `timestamptz`, `nullable=True` | `[MEASURED]` |
| Migration up + down chala — `downgrade` ka actual output | M2, dono `\d jobs` | `[MEASURED]` |
| `NULL` backfill ka faisla (migration me backfill **ya** `IS NULL` branch) | **Option B** — `NULL` rehne diya, predicate me `IS NULL` branch | — |
| Uss faisle ki **cost**, apne shabdon me | `D-07` ka argument: backfilled value 41/63/65 ke liye **fiction** hoti, aur `downgrade` usko wapas nahi laa sakti — migration shape me reversible hoti, information me nahi. Iski keemat: `IS NULL` branch **hamesha** predicate me rahegi, aur wo har `NULL`-lease row ko reclaimable banati hai — including koi future writer jo `SET` me `claimed_at` likhna bhool jaaye | — |
| Claim ke baad ek row ka lease value (non-null) | M3 | `[MEASURED]` |
| Purani `running` rows (41/63/65) pe lease column ka value | teeno pe `NULL` | `[MEASURED]` |
| Three-valued logic wala differential — dono counts | `0` aur `3` | `[MEASURED]` |
| `Interim_Guarantee` — kaunsa contract point kis ke against trade hua | Contract **#1** behtar hota hai: accepted job hamesha ke liye `running` me atki nahi rehti, wo wapas claimable ho jaati hai. Iski keemat contract **#2** deta hai: reclaim ka matlab hai ek handler jo already chal chuka hai dobara chal sakta hai, aur dono executions individually legit hain. To lease + reaper stranded-work ka window **narrow karta hai** aur duplicate side effect ka window **band nahi karta**. #2 Week 3 ke dedup tak **unprotected** rehta hai. Aur ye strict improvement nahi, ek **trade** hai: pehle atki hui job bekaar padi rehti thi — bura, par **ek baar**. Ab wo dobara chalayi jaayegi jabki pehla worker possibly abhi bhi chal raha hai | — |

**Aur ek cheez jo aaj plan ne poochhi nahi thi par reaper ka faisla decide karti hai** — `claimed_at`
naam ka structural asar:

`claimed_at` ek **event** hai, `lease_expires_at` ek **deadline** hota. Farq predicate me dikhta hai:

```
deadline column:  WHERE lease_expires_at < now()                        -- duration query me nahi hai
event column:     WHERE claimed_at < now() - interval '<duration>'      -- duration ab har predicate me hai
```

Matlab lease ki **duration** — jo plan `D-22` / Din 6 tak defer karta hai, kyunki uski `Cost` line Din 3
ke duplicate number ke bina likhi hi nahi ja sakti — **Din 2 ke predicate me aa gayi hai**. Ye galat
choice nahi hai (`claimed_at` sach record karta hai: ye row iss instant claim hui; `lease_expires_at` ek
policy record karta hai jo tab badalti hai jab duration badalti hai), par iski keemat aaj likhni hai:
Din 2 ko ek duration **chunni padegi**, aur wo number Din 3 ka evidence aane se **pehle** chuna hua
number hoga. `D-22` ko Din 6 pe likhte waqt ye baat yaad rakhni hai — us waqt sawaal hoga
*"ye number measure kiya ya choose kiya"*, aur jawab "choose kiya, Din 2 pe, evidence se pehle" hoga.

**Aur isi wajah se Step 9 ki pehli query reaper ka predicate nahi hai.** `claimed_at < now()` ka matlab
hai *"kabhi bhi claim hui thi"* — yaani **zero-second lease**. Aaj usne `0` diya sirf isliye ki teeno
`running` rows pe `claimed_at` `NULL` hai. Agar job 88 uss waqt `running` hoti, ye query usko claim hone
ke **usi second** utha leti. Differential (`0` vs `3`) `NULL` trap theek dikhata hai — aur usi line me ek
doosra defect chhupa rehta hai. Din 2 ka predicate iss query ki shape se **nahi** aa sakta.

**Closing reconciliation** — opening counts BENCH block se, delta aaj ka. **Kabhi `max(id)` se nahi, kabhi
id contiguity se nahi:**

| Line | Value |
|---|---|
| opening `pending` / `running` / `succeeded` / `failed` / total (BENCH block) | `0 / 3 / 74 / 9 / 86` |
| `+` aaj enqueue hui probe jobs (ids **naam se**) | **id 88** (`type='slow'`) — ek row |
| `−` unme se jo `succeeded` / `failed` hui | 88 → `succeeded` |
| `=` closing counts | `0 / 3 / 75 / 9 / 87` |
| `psql` ke actual counts | `running 3`, `succeeded 75`, `failed 9`, total `87`, `max(id) 88`, seq `88` — `[MEASURED-R]` aaj shaam |
| Match? | **Haan.** `9 + 3 + 75 = 87` |
| `job_executions` delta | `57 → 58`, `+1`. Sirf ek job dispatch hui, to `+1` sahi hai `[MEASURED-R]` |
| Migration ne kisi row ka `status` badla? | **Nahi.** `running` opening `3` (41/63/65) tha aur closing bhi `3` hai, aur wo wahi teen ids hain `[MEASURED-R]`. `attempts <> 0` wali rows aaj bhi `0` hain — retry ka koi rasta galti se nahi chala `[MEASURED-R]` |

Match na kare to wo **finding** hai (E5), adjust karke balance nahi hoti. Pehla suspect ek bhoola hua worker
(`P-13`). **Finding: reconciliation match karta hai, par `P-13` phir bhi hua — sirf usne counts contaminate
nahi kiye.** Niche cleanup dekho: do worker abhi zinda hain, aur unhone kuch claim nahi kiya kyunki
`pending` count `0` hai aur `running` rows claim query ko dikhti hi nahi (`P-16`). **Yaani clean
reconciliation ne ek asli hygiene failure ko chhupa liya.** Arithmetic ne wo cheez detect nahi ki jo
detect karne ke liye wo likhi gayi thi — aur agar aaj ek bhi `pending` row hoti, ye entry galat hoti.

**Cleanup — ye hissa fail hua, aur ye sabse important line hai iss entry me:**

| Kya | Status |
|---|---|
| stdout capture file (`python -u` wali) delete hui? | not recorded — report me mention nahi tha, aur koi capture file repo me nahi mili |
| Worker processes band hue? | **Nahi.** `2026-08-23 10:27 UTC` pe **do** processes zinda the: OS PID `34280` aur `32636`, dono `python -m src.worker`, dono `StartTime 15:16:54 IST` `[MEASURED-R]` |
| Live DB backend? | **Haan, ek.** backend PID `3119`, `application_name` khali (asyncpg), `backend_start 09:46:55.463+00`, aur `state_change` do baar 2 s ke andar aage badha (`10:26:29.02`, phir `10:27:21.67`) — **~40 minute baad bhi poll kar raha tha** `[MEASURED-R]` |
| Kaunsa process job 88 chalayi thi? | `job_executions.worker_id = worker-32636` → OS PID `32636` `[MEASURED-R]` |
| Do process, par ek hi asyncpg backend — kyun? | **Not established.** Ek hi non-psql connection dikhi. Doosre process ka connection kahan hai, ye measure nahi hua |
| Leftover `psql` sessions | `8`, sabhi `state = 'idle'`, sabka `xact_start` `NULL`, sabse purani `09:17:53+00` `[MEASURED-R]`. **`idle in transaction` zero hai** — matlab `P-06` ka mechanism (locks pakde baithna) maujood **nahi** hai. Ye hygiene hai, lock hazard nahi |
| Probe **rows delete nahi** hoti; unke ids | **id 88** — rakhi gayi hai, delta me count hai |

**Ye `P-13` ka teesra instance hai** aur pehla jisme wo *bina nuksaan* hua. Nuksaan na hone ki wajah luck
hai, discipline nahi: `pending` count `0` thi. Aur closing report me *"Zero idle sessions"* likha gaya tha —
wo `idle in transaction` ke liye sach hai, par *"0 worker processes"* closing pe **re-verify nahi hua**, aur
wo sach nahi tha.

**Commit:** **nahi hua.** `git log` ka HEAD abhi bhi `9d60df7 docs: complete Stage Day requirements` hai,
aur `git status` ye dikhata hai `[MEASURED-R]`:

```
 M labs/day2_signals.py
 M src/models.py
 M src/worker.py
?? alembic/versions/75a845575d2e_add_claimed_at_to_jobs.py
?? alembic/versions/79cb2ee38481_add_claimed_at_to_jobs.py
```

`labs/day2_signals.py` bhi modified hai — wo Din 1 ke scope me nahi tha. Kya badla, ye recorded nahi hai;
stage karne se pehle uska diff dekh lena chahiye, aur agar wo aaj ka kaam nahi hai to usko **alag** commit
me rakhna hai. `docs/planning/`, `docs/roadmap/` aur `docs/daily/` gitignored hain, to khali `git status`
ka matlab "kuch likha nahi" **nahi** hai.

---

### 🔧 Migration chain — ek khaali revision jo permanently baithi rahegi

Ye report me nahi tha aur reversibility check ke matlab ko badalta hai `[MEASURED-R]`.

```
$ python -m alembic history
79cb2ee38481 -> 75a845575d2e (head), add claimed_at to jobs
4bc263254b10 -> 79cb2ee38481, add claimed_at to jobs
81b6e20c9ea7 -> 4bc263254b10, create_job_executions_table
<base> -> 81b6e20c9ea7, create_jobs_table
```

**Do revisions, ek hi message, aur pehli khaali hai:**

| Revision | Create Date | `upgrade()` | `downgrade()` |
|---|---|---|---|
| `79cb2ee38481` | `15:07:40.511` | `pass` | `pass` |
| `75a845575d2e` | `15:09:36.624` | `op.add_column('jobs', sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True))` | `op.drop_column('jobs', 'claimed_at')` |

**Cause, aur ye mtime se establish hota hai:** `src/models.py` ka mtime `15:08:44` hai — pehli revision
`15:07:40` pe generate hui, yaani **`claimed_at` model me aane se pehle**. Autogenerate ne diff nahi paaya,
`pass` likh diya, aur **exit status zero** diya. `[MEASURED-R]`

**Iska asar Step 6 ke verification pe:**

- `alembic downgrade -1` head (`75a845575d2e`) se **khaali revision** pe utra. Column drop hua, `\d jobs`
  ne 6 columns dikhaye. Check **pass**, aur uska mechanism asli tha.
- Par ek **doosra** `alembic downgrade -1` khaali revision ka `downgrade()` chalata — `pass` — aur success
  report karke **kuch nahi badalta**. Yaani chain me ek step hai jo hamesha "chala" bolega aur kabhi kuch
  nahi karega.
- **Aur asli baat:** agar sirf wahi khaali revision bani hoti, `alembic upgrade head` `Running upgrade
  4bc263254b10 -> 79cb2ee38481` print karke exit `0` deta, aur column **nahi** banta. Migration ka output
  success aur no-op me **farq nahi** karta.

Ye `P-18` ki exact shape hai, migration layer pe: **ek verification jiska expected output mechanism ke
hone aur na hone, dono se milta hai.** Iss baar wo pakda gaya kyunki agli hi statement (claim ka
`SET claimed_at=...`) column ke bina **loud** fail karti. Silent version wo hota jo `DIN_01_KEY.md` Step 7
me likha hai: column migration me ho aur `models.py` me na ho.

**Aaj isko theek nahi karna.** Khaali revision chain ka hissa hai aur `alembic_version` usse guzar chuki
hai; usko delete karna history rewrite hai. Wo wahan rehti hai aur **iss log me uska naam** likha rehta
hai — yahi record hai ki wo dead hai, bhooli hui nahi.

---

### 💡 What I Understood

> ⚠️ **Ye section reviewer ne likha hai, user ne nahi.** Isme wo hai jo aaj ke session ne **establish**
> kiya — user ki samajh ka record nahi. Iska poora point yahi hai ki ise **apne shabdon me replace kiya
> jaaye**, aur jo cheez sirf padhke aayi uske saath likha jaaye ki wo padhi hui hai. Jab tak replace nahi
> hota, ye entry apni sabse zaroori field pe `[NO EVIDENCE]` carry karti hai.

Aaj ke session ne teen cheezein establish ki, aur teeno measurement se aayi hain:

**1. Column add karna aasan tha; column ka *naam* asli decision tha.** `claimed_at` aur
`lease_expires_at` ek hi type, ek hi nullability, ek hi migration lete hain — aur do bilkul alag
predicates maangte hain. Event column duration ko **query me** rakhta hai, deadline column duration ko
**writer me** rakhta hai. Kyunki `claimed_at` chuna gaya, lease ki duration Din 2 ke predicate me aa gayi
hai, jabki plan usko `D-22`/Din 6 tak defer kar raha tha. Aaj ka sabaq: schema ka shape decide karte waqt
ye poochhna padta hai ki **iss column ko padhne wali query kaisi dikhegi**, sirf ye nahi ki column me kya
store hoga.

**2. `NULL` ne `false` ki tarah behave nahi kiya, aur wo do counts me dikha — `0` versus `3`.** Ye
prediction se aayi baat nahi hai, output se aayi hai. Aur ek layer neeche: Step 9 ki pehli query
(`claimed_at < now()`) ne `0` diya, aur wo `0` **do** wajah se aa sakta tha — `NULL` trap, ya "koi row
expired nahi thi". Aaj wo pehli wajah thi. Same output, do kahaniyan; farq sirf doosri query ne dikhaya.
**Ek count kabhi apna cause nahi batata.**

**3. Ek migration jo "chali" aur kuch nahi badla.** `--autogenerate` ne khaali `upgrade(): pass` likha
kyunki `models.py` me column tab tha hi nahi, aur usne exit status `0` diya. Yahan wo silent nahi raha
sirf isliye ki agli statement column ke bina loud fail karti. Ye `P-18` ka wahi shape hai jo Din 6 pe
verification me mila tha — ab tooling layer pe. **Exit code `0` ka matlab "kaam hua" nahi hai; matlab
"error nahi aayi" hai.**

**Aur ek cheez jo aaj sabse mehngi nahi thi par ho sakti thi:** clean reconciliation ne ek asli failure
chhupa liya. Do worker chalte reh gaye, aur arithmetic ne unhe nahi pakda — kyunki `pending` count `0`
thi. Agar ek bhi `pending` row hoti, closing counts galat hote. Reconciliation ne aaj kaam kiya, par wo
`P-13` ko **detect** nahi kar sakti; uske liye process check chahiye, aur wo closing pe chala hi nahi.

---

### 🧠 Self-Check (honest — 0 / 6 self-answered on Part B, aur ye score data ke absence ka hai, galat jawab ka nahi)

`____`

**Part B ke chhe sawaalon ka koi likha hua pre-measurement answer iss review ko supply nahi hua.** Report
me **outcomes** the, predictions nahi. Reviewer rule 1 aur 6 saaf hain: jo field report nahi hui uska
plausible value nahi bharna, aur jo answer nahi hua usko correct me count nahi karna. To aaj ka honest
score **0/6 scorable** hai — iska matlab "chhe galat" nahi, iska matlab "chhe ka evidence nahi".

Agar wo chhe jawab kaagaz pe ya kisi file me likhe hue hain, unhe paste karo aur ye section per-question
re-score ho jaayega. **Aur agar wo likhe hi nahi gaye the, to wahi likhna hai** — kyunki uske bina din ke
measurements ka comparison base hi nahi banta, aur `DIN_01_KEY.md` khulne ke baad wo base dobara nahi ban
sakta (`E8` — seal khulne ke baad answer *reconstruction* score karta hai, *answered* nahi).

Per-question status, taki gap naam se dikhe:

| Part B Q | Kya poochha gaya | Status |
|---|---|---|
| 1 | `created_at` kya measure karta hai; naive predicate safe ya dangerous direction | **not supplied.** Report ka content isse cover karta hai, par execution ke **baad** aaya |
| 2 | `job_executions` row = claim current? `record_execution()` kis transaction me | **not supplied.** Report me `D-21`/evidence-not-control-input ka jawab hai, phir bhi post-hoc |
| 3 | `now()` transaction-start ya statement time; lambi reaper transaction me matlab | **not supplied**, aur ye Din 2 ka direct input hai |
| 4 | `NOT NULL` 86 rows se kya demand karta hai; `NULL` predicate se kya | **not supplied.** Faisla (Option B) aur uski cost aayi — wo Step 8 ka deliverable hai, Q4 ka answer nahi |
| 5 | Kaunsa contract point behtar, kaunsa kamzor | **not supplied.** `Interim_Guarantee` ka text sahi shape me aaya (`narrows` / `does not close`), par prediction ki tarah nahi |
| 6 | Claim ka `rowcount` ab kuch **naya** batata hai? | **not supplied**, aur ye woh sawaal hai jiska galat jawab sabse mehnga hota — `rowcount = 1` lease likhne ka proof **nahi** hai |

**Step 0 — paanch likhe hue answers: paanchwi baar slip.** `docs/logs/WEEK_02.md` ka mtime din shuru hone
tak `2026-08-22 18:01` tha, to wo paanch answers disk pe nahi the `[MEASURED-R]`. Report ka content
teen-chaar ko cover karta hai, par wo BRIEF aur plan padhne ke **baad** likha gaya — `E8` ke hisaab se wo
**reconstruction** hai, *answered* nahi. Paanchwa item (*"short lease — handler se chhoti lease me kya
galat hota hai"*) report me bilkul nahi aaya, aur wo **Din 3 ka centrepiece** hai.

`idk` ek valid answer hai aur wo **not-answered** ki tarah score hota hai. Guess ko knowledge ki tarah
likhna dono directions me dishonest hai — jo aata tha usko miss likhna bhi revision material kharab karta
hai.

**Corrections — jo maine kaha aur jo measurement/review ne refute kiya:**

| # | I said | Actual | The transferable lesson |
|---|---|---|---|
| 1 | *"Week 2 Din 1 ka execution **100% complete aur verify** ho gaya hai"* | **Partial.** Step 0 (paanch answers) nahi hua, Step 10 ka deliverable disk pe nahi hai (`DDIA_CH8_LINKS.md` mtime abhi bhi Stage Day ka `2026-08-22 17:28`), Step 11 ka log / `PROBLEMS.md` / `CURRENT_WEEK.md` / commit nahi hua, aur cleanup fail hua `[MEASURED-R]` | "Verified" ka matlab **file state check karna** hai. Ye wahi galti hai jo Stage Day pe unsaved buffers ke saath hui thi — us din bhi kaam complete report hua tha aur disk khali tha. Do baar, ek hi hafte me |
| 2 | *"Zero idle sessions"* aur implicitly clean close | `idle in transaction` **0** — ye sach hai. Par closing pe **do worker process zinda** the aur ek asyncpg backend `~40 min` baad bhi poll kar raha tha `[MEASURED-R]` | `idle in transaction = 0` aur `workers = 0` do **alag** checks hain. Pehla lock hazard dekhta hai (`P-06`), doosra measurement contamination (`P-13`). Ek ko dekhkar doosre ka dava nahi kar sakte |
| 3 | *"Migration 'add claimed_at to jobs' generated"* — ek migration | **Do** revisions bani, dono ka message same, aur pehli (`79cb2ee38481`) **khaali** hai — `upgrade(): pass` `[MEASURED-R]` | `--autogenerate` model state ke against diff leta hai. Model me column aane se **pehle** chalane pe wo khaali revision banata hai aur exit `0` deta hai. Ek `alembic revision` ka success uske andar kuch hone ka proof nahi hai |
| 4 | Step 7 ka clock evidence: `claimed_at 09:46:55+00` aur `now() 09:47:05+00` | Dono **DB clock** ke hain. Ye pair lease value verify karta hai — par KEY ne jo maanga tha (DB clock versus worker stdout ka **offset**) wo isse measure hi nahi hota `[MEASURED-R]` | *"Ek hi query me dono"* clock-consistency ke liye sahi hai, par do **different** clocks ka offset measure karne ke liye dono clocks ko padhna padta hai. Ek clock ko do baar padhna offset nahi deta |
| 5 | Step 9 ka `claimed_at < now()` → `0` = *"koi expired lease nahi"* | `0` aaya kyunki teeno rows pe `claimed_at` `NULL` hai. **Aur usi query me ek doosra defect hai:** `claimed_at` event column hai, to `< now()` ka matlab zero-second lease hai — job 88 `running` hoti to wo claim ke **usi second** match kar jaati `[MEASURED-R]` | Ek `0` count ke kai causes hote hain. Aur ek query ka differential ek defect dikha ke doosre ko chhupa sakta hai — Step 9 ne `NULL` trap dikhaya aur duration ki gayabi chhupa li |

*(Ye table kabhi delete nahi hoti, na chhoti hoti hai.)*

---

### 🚧 Unresolved / Follow-ups

**New, from today:**

| # | Item | Kya specifically chahiye |
|---|---|---|
| 1 | **Do worker process abhi zinda hain** — OS PID `34280` aur `32636` | Din 2 ka pehla kaam. Inhe band karo (`Stop-Process -Id 34280,32636`), phir opening check **dobara** chalao. Jab tak ye chal rahe hain, Din 2 ka opening bench contaminated hai — aur Din 2 ka poora experiment 41/63/65 pe hai, jo reclaim hone ke baad `pending` ban jaayengi aur **turant claimable** ho jaayengi. Ek chalta worker unhe uthaa lega aur reclaim latency ka number kisi ka nahi hoga |
| 2 | **Do process, ek asyncpg backend** — kyun? | Not established. Measure karne layak hai: dono PIDs ka `pg_stat_activity` me mapping. Ho sakta hai ek process apna connection kho chuka hai aur retry kar raha hai, ya wo loop me hi nahi hai |
| 3 | **`claimed_at` event column hai, to duration Din 2 ke predicate me aa gayi** | Din 2 pe ek duration **chunni** padegi, Din 3 ka evidence aane se pehle. Din 6 pe `D-22` likhte waqt ye line jaani chahiye: *"ye number choose kiya gaya, Din 2 pe, measurement se pehle"* |
| 4 | **`79cb2ee38481` — khaali revision chain me permanent hai** | Aaj theek **nahi** karna (history rewrite). Naam iss log me hai, wahi record hai. Follow-up ye hai: aage `alembic revision --autogenerate` chalane se pehle `models.py` save ho chuki hai, ye check karna |
| 5 | **`labs/day2_signals.py` modified hai aur wo Din 1 ka scope nahi tha** | Uska diff dekho. Agar aaj ka kaam nahi hai to alag commit, ya revert |
| 6 | **Clock offset ka aadha measurement** | DB session versus **worker stdout** — dono ko ek jagah padho aur actual difference likho. Aaj ka `+5:30` process-start versus `backend_start` se nikla hai, jisme `~1.5 s` interpreter startup ka hai |

**Deliberately open (owner ke saath):**

- **Lease ki duration** — `D-22`, Din 6. Aaj number nahi chuna, aur ye sahi hai. Par item 3 ke wajah se
  Din 2 pe ek **working** number chunna padega; wo `D-22` nahi hai, wo Din 2 ka input hai.
- **Contract #2 unprotected hai** — Week 3 ke dedup tak. Ye iss hafte ka accepted trade hai, gap nahi.
- **`ADD COLUMN` fast-path ka number** — Option B ne `DEFAULT` use nahi kiya, to KEY ka `now()`-as-default
  sawaal iss path pe uthta hi nahi. Agar Option A kabhi revisit hui, `\timing` ke saath measure karna.

**Slipped (aur specifically kya chahiye):**

| Item | Kaunsi baar | Kya chahiye |
|---|---|---|
| **Step 0 ke paanch likhe hue answers** | **paanchwi** | Paanchon apne shabdon me, iss log ki Din 1 entry me. Chaar ka content report me hai par execution ke baad aaya (`E8` — reconstruction). **Paanchwa — *"lease handler se chhoti ho to kya galat hota hai"* — bilkul nahi aaya**, aur wo Din 3 ka centrepiece hai. Ye ek hi item hai jo Din 3 ko technically block karta hai |
| **Part B ke chhe prediction answers** | pehli | Likhit roop me, measurement se pehle. Aaj ke liye ab reconstruct **nahi** ho sakte — seal khul chuki hai. Din 2 ke chhe sawaal `WEEK_02.md` ke PART B block me hain; unhe **kal subah, kaam shuru karne se pehle** likhna hai |
| **Ch 8 links append** | pehli | `DDIA_CH8_LINKS.md` me kam se kam **do naye** one-line links, *Network Faults in Practice* aur *Detecting Faults* se, har ek ka right-hand side ek **existing** named `D-`/`P-`. Note: file me line 2 aur 3 already `pp. 278–284` aur `281–283` cite karti hain — wo Stage Day pe likhi gayi thi, to aaj ka reading un lines se **aage** jaana chahiye, unhe dohrana nahi |
| **Commit** | pehli | Staged paths naam se: `src/models.py`, `src/worker.py`, `alembic/versions/75a845575d2e_*.py`, `alembic/versions/79cb2ee38481_*.py`, `docs/logs/WEEK_02.md`, `docs/PROBLEMS.md`. `docs/planning/`, `docs/roadmap/`, `docs/daily/` gitignored hain |

**Carried forward, unchanged:**

- **Din 7 ki log entry maujood nahi hai.** Aaj ke bench ne BENCH block ke **numbers** verify kar diye, to
  provenance wala aadha band ho gaya. Par Din 7 me kya chala aur kya verdict nikla — wo kahin likha nahi
  hai aur reconstruct nahi hoga. `WEEK_01.md` me ye ek line ki tarah rehna chahiye.
- **`LEARNING_LOG.md` ka open-items table** — Din 7 debt ke liye row abhi bhi nahi bani.

---

### ❓ Question / Next Thought

**Kal ka asli sawaal, aur ye Din 2 ka experiment define karta hai:** predicate `claimed_at` pe likha
jaayega, aur `claimed_at` ek **event** hai — to predicate me ek duration term aayega jo aaj tak kisi
evidence se nahi aaya. To Din 2 pe do cheezein ek saath hongi: ek **measurement** (predicate ne 41/63/65/75
pe kya kiya) aur ek **choice** (duration kitni). Aur `P-12` ka pura sabaq yahi hai ki ek run me do
variable rakhne se pata nahi chalta ki result kis ka tha.

Isliye kal ka sawaal ye hai: **agar predicate ne 41/63/65 ko utha liya, to wo mere predicate ke sahi hone
ka evidence hai, ya meri chuni hui duration ke uss row ke age se chhoti hone ka?** Dono ek hi output dete
hain. Farq nikalne ka ek hi tareeka hai — duration ko **pehle** likhna, uske reason ke saath, aur phir
chalana. Reverse order me wo number "jo kaam kar gaya" ban jaayega, aur Din 6 pe `D-22` uske upar khadi
nahi ki ja sakti.

**Aur ek chhota sawaal jo aaj ka output khud utha raha hai:** teeno fixture rows pe `claimed_at` `NULL`
hai, to `IS NULL` branch unhe reclaim karegi. Par wo branch ye nahi jaanti ki row **kab** atki. Yaani
41/63/65 ke liye reaper ke paas duration ka koi input hi nahi hai — wo unhe reclaim karega kyunki wo
`NULL` hain, na ki kyunki wo expired hain. **Kal wo teen rows expiry ki wajah se reclaim nahi hongi;
`NULL` ki wajah se hongi.** Ye do bilkul alag reasons hain aur reaper ka output dono me same dikhega.

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
