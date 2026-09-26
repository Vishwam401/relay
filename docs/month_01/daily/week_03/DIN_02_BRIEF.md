# DIN 2 BRIEF — Dedup at execute: constraint kaam karti hai, `SELECT`-then-`INSERT` nahi

**Week 3 · Din 2** · Plan: [`../../planning/WEEK_03.md`](../../planning/WEEK_03.md) ·
Log: [`../../logs/WEEK_03.md`](../../logs/WEEK_03.md) · Sealed: [`DIN_02_KEY.md`](DIN_02_KEY.md)

**Budget:** ~2h15m. Har active step 10–15 min; 45-second handler ka wait active coding time nahi hai.

> **Paste rule:** Part A + Part C Gemini ko de sakte ho. **Part B kabhi nahi. KEY kabhi nahi.**
>
> **Seal rule:** Har step ka output aane ke baad, aur prediction mismatch par apni explanation likhne ke
> baad hi KEY ka corresponding section kholo.
>
> **Provenance rule — Din 1 ki correction:** `DIN_01_ANSWERS.md` me original five `idk` final verified
> answers se overwrite ho gaye; current file se `1/6` independently verify nahi hota. Aaj har question ke
> neeche teen permanent blocks honge: **Prediction (freeze; never edit)** → **Observed + my explanation** →
> **After KEY**. Original prediction ko correct answer se replace karna mana hai.

## Aaj ka one-line target

Din 1 ka exact failure **phir produce** hoga—do workers, do dispatches, proved overlap—but aaj us job ka
committed local effect count **`1`** hoga. `1` tabhi evidence hai jab duplicate execution independently
prove ho. Aaj duplicate delivery eliminate nahi hoti; uska damage local ledger row par narrow hota hai.

## Din 1 se inherited measured state

```text
[MEASURED-R reviewer close, 2026-08-31]
jobs: 91 succeeded / 15 failed / 3 dead_letter / 0 pending / 0 running = 109
max(id)=110 · jobs_id_seq=110 · job_executions=97
side_effects=3: job 109 -> 1 row; job 110 -> 2 rows
alembic head=4b0e6dcfdfa1 · python workers=0 · idle in transaction=0
Din 1 collision: job 110, 2 workers, 2 effects, attempts=2, overlap=2.429 s
```

**Load-bearing trap:** Job 110 ki do ledger rows evidence hain; delete/update/backfill karke ek canonical
row banana aaj allowed nahi. Isliye current table par seedha `UNIQUE(job_id)` add karna expected migration
nahi hai. Pehle us impossibility ko safe transaction me observe karo, phir evidence-preserving shape chuno.

---

# PART A — STEPS

## Step 0 — Answers freeze + opening bench (10 min) · executable

Pehle `docs/daily/week_03/DIN_02_ANSWERS.md` banao. Har Q ke neeche:

```text
### Prediction — frozen before the step
...
### Observed + meri explanation — output ke baad, KEY se pehle
...
### After KEY — original prediction edit nahi hogi
...
```

Q1–Q6 ke predictions relevant step se pehle save karo; `idk` valid hai. File ka first-save aur last-write
time Step 4 ke worker output ke saath log me jayega.

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Select-Object ProcessId, ParentProcessId, CommandLine
```

```powershell
@"
select pid, application_name, state, backend_start, xact_start
  from pg_stat_activity where datname='relay' order by backend_start;
select status, count(*) from jobs group by status order by status;
select count(*) as total, max(id) as maxid from jobs;
select last_value from jobs_id_seq;
select count(*) as executions from job_executions;
select count(*) as effects from side_effects;
select job_id, count(*) from side_effects group by job_id order by job_id;
select version_num from alembic_version;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

**Expected:** inherited block exactly. `GROUP BY status` me zero-valued `pending`/`running` rows print nahi
hongi; log me dono `0` likho. Divergence aaye to aage mat badho—cause naam se record karo.

> **Terms used in this step**
> - **Prediction provenance** — evidence ki answer output se pehle freeze hua tha; final correctness se alag property.
> - **Legacy row** — nayi invariant se pehle committed row; history preserve hoti hai, retroactively clean nahi.

---

## Step 1 — Identity choose karo; direct constraint ko safely probe karo (15 min) · executable

**Q1 aur Q3 pehle freeze.** Phir current data padho:

```powershell
@"
select job_id, count(*) as effects
  from side_effects
 group by job_id
having count(*) > 1
 order by job_id;

begin;
alter table side_effects
  add constraint uq_side_effects_job_id_probe unique (job_id);
rollback;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

Expected first query: `110 | 2`. `ALTER` expected to fail; transaction rollback ke baad verify:

```powershell
@"
select conname from pg_constraint
 where conrelid='side_effects'::regclass order by conname;
select count(*) from side_effects;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

Expected: probe constraint absent; count still `3`.

Ab **design judgement** likho—result nahi, choice + cost:

| Shape | Benefit | Cost |
|---|---|---|
| New nullable stable `effect_key`, named `UNIQUE(effect_key)` | Legacy rows `NULL`; new effects invariant me enter; evidence untouched | Guarantee keyed rows se start hoti hai, historical rows retroactively protected nahi |
| Separate protected effect table | Old raw evidence aur new invariant physically separate | Do stores, more schema and reconciliation |
| Canonical legacy row choose/backfill, then `UNIQUE(job_id)` | One obvious column | Historical evidence rewrite/delete; aaj forbidden |
| ID/date cutoff partial index | Quick | Data accident policy ban jaata hai; future replays ke holes; reject unless explicitly justified |

Current scope me smallest evidence-preserving option **nullable stable effect identity** hai; final column name,
type, key format tum choose karo. Key same logical effect ke every dispatch me identical honi chahiye.
`attempts`, `worker_id`, execution id, timestamp, random UUID ko key me include karoge to duplicate deliveries
alag identities ban jayengi.

Ek line log me: **“row ka matlab kya hai?”** Aaj ledger row khud committed local effect hai—not “work
reserved” and not an external effect ka completion receipt.

> **Terms used in this step**
> - **Logical-effect identity** — delivery/attempt se independent naam of the business effect being protected.
> - **Stable key** — retry, reclaim, aur doosre worker par same rehne wali identity.
> - **Named constraint** — catalog me explicit naam, jise conflict handling narrowly target kar sakti hai.

---

## Step 2 — Additive migration, down/up, legacy evidence intact (15 min) · executable

`SideEffect` model aur ek new Alembic revision me chosen nullable key + named `UNIQUE` add karo.

Requirements:

1. New key nullable, **no server default**. Existing three rows untouched `NULL` rahengi.
2. Named uniqueness only chosen key par.
3. `upgrade()` column then constraint add kare; `downgrade()` constraint then column drop kare.
4. No FK, no cleanup, no update/backfill, no job-id cutoff.
5. `models.py` disk pe save karke autogenerate; generated body manually inspect.

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

Catalog verification (`<key_column>`/`<constraint_name>` replace karo):

```powershell
@"
select column_name, is_nullable, column_default
  from information_schema.columns
 where table_name='side_effects'
 order by ordinal_position;
select conname, pg_get_constraintdef(oid)
  from pg_constraint
 where conrelid='side_effects'::regclass
 order by conname;
select id, job_id, <key_column> from side_effects order by id;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

**Down/up verification keyed rows create karne se pehle hi:**

```powershell
.\.venv\Scripts\alembic.exe downgrade -1
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

Phir catalog query repeat. Expected invariant after final upgrade: 3 legacy rows remain; all chosen keys
`NULL`; named unique exists; Alembic new head par.

> **Terms used in this step**
> - **Shape-reversible** — downgrade columns/constraints ka old shape la sakta hai; historical guarantee undo hona separate cost hai.
> - **Ordinary PostgreSQL `UNIQUE` + `NULL`** — key absence aur key equality ko database alag treat karta hai; exact behaviour predict Q3 me.

---

## Step 3 — Conflict-safe insert + one-dispatch baseline (15 min) · executable

**Q2 aur Q6 freeze.** `handle_effect` ka insert narrow conflict-safe banao. Approach constraints:

- PostgreSQL dialect insert API use karo, because generic SQLAlchemy `insert()` conflict method expose nahi karta.
- Chosen **named constraint** target karo; unrelated integrity error ko silently swallow mat karo.
- Stable key derive karo from logical effect + `job_id`; same job ke attempts `1`, `2`, `3` par same rahe.
- Execute result ka `rowcount` read/print karo.
- `rowcount=1` aur `rowcount=0` dono handler success outcomes hon; meanings alag log lines me.
- “Side-effect written” tab mat print karo jab rowcount `0` ho.
- Retry/lease/heartbeat/mark logic unchanged.

**No ready-made code:** implementation tum likhoge. Step ends with one short job.

```powershell
@"
insert into jobs(type,payload)
values ('effect','{"seconds":2,"block":false}'::jsonb)
returning id, status, attempts;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

Fresh terminal me worker manually run karo:

```powershell
.\.venv\Scripts\python.exe -m src.worker
```

Job terminal hone par worker stop. Returned id ko `<baseline_id>` me use karo:

```powershell
@"
select id,status,attempts from jobs where id=<baseline_id>;
select job_id,worker_id,<key_column>,created_at
  from side_effects where job_id=<baseline_id> order by id;
select count(*) from job_executions where job_id=<baseline_id>;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

Expected relative output: `succeeded`, attempts `1`, one execution, one keyed effect, insert `rowcount=1`.
No divergence ho to id expected `111`, but returned id source of truth hai.

> **Terms used in this step**
> - **`ON CONFLICT DO NOTHING`** — conflicting insert ko statement-level no-op banata hai; transaction abort nahi hoti.
> - **`rowcount`** — us statement ne kitni rows affect ki, table ka total count nahi.
> - **Conflict target** — exact uniqueness rule whose conflict is intentionally handled.

---

## Step 4 — Din 1 collision exactly repeat karo (15 min active) · centrepiece

**Q5 freeze. Fault model change nahi:** `45 s`, `block=true`, lease `30 s`, heartbeat task event-loop
starvation ki wajah se `0` runs, 2 workers, 1 reaper. Lease/poll/backoff constants untouched.

Enqueue:

```powershell
@"
insert into jobs(type,payload)
values ('effect','{"seconds":45,"block":true}'::jsonb)
returning id,status,attempts;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

Teen separate terminals:

```powershell
.\.venv\Scripts\python.exe -m src.worker
.\.venv\Scripts\python.exe -m src.worker
.\.venv\Scripts\python.exe -m src.reaper
```

Relevant stdout delete/close se pehle copy:

- both claims + worker IDs
- both execution starts/ends
- both effect insert `rowcount`
- reaper reclaim line
- both terminal mark `rowcount`
- heartbeat lines (expected count ko output se report karo, assume nahi)

Returned id `<collision_id>`:

```powershell
@"
select id,status,attempts,claimed_at from jobs where id=<collision_id>;
select id,job_id,worker_id,executed_at
  from job_executions where job_id=<collision_id> order by executed_at;
select id,job_id,worker_id,<key_column>,created_at
  from side_effects where job_id=<collision_id> order by id;
select count(*) as effect_count
  from side_effects where job_id=<collision_id>;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

**Success requires all three together:**

1. two execution rows, two distinct workers;
2. second dispatch falls inside first handler interval—overlap seconds measured;
3. one effect row, with logs showing one insert `rowcount=1` and duplicate `rowcount=0`.

Ek execution row aayi to count `1` **dedup evidence nahi**. Fresh job par experiment repeat karo; failed
fixture ko delete mat karo, closing delta me naam do.

> **Terms used in this step**
> - **Dedup at execute** — delivery allowed; effect store same logical identity ko once admit karta hai.
> - **Arbiter** — unique index deciding which same-key insert can create the row.
> - **Overlap proof** — second dispatch instant first handler interval ke andar; two rows alone insufficient.

---

## Step 5 — Rejected alternative: deterministic `SELECT`-then-`INSERT` race (15 min) · executable

**Q4 freeze.** Main protected table par ye negative control mat chalao: unique constraint second insert ko
commit hone se rok degi, so count `1` aayega even if app check racy hai. Wo decorative check hogi.

Chosen fixture: separate **UNLOGGED constraint-free probe table**. Output log me copy hoga; table end me
drop hogi. Ye real `side_effects` rows ko touch nahi karti.

Setup:

```powershell
@"
drop table if exists side_effects_check_then_insert_probe;
create unlogged table side_effects_check_then_insert_probe(
  id bigint generated always as identity primary key,
  effect_key text not null,
  worker_id text not null,
  created_at timestamptz not null default now()
);
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

Do interactive psql terminals kholo:

```powershell
docker exec -it relay-db-1 psql -U postgres -d relay
```

**Order exactly:**

```sql
-- Session A
begin;
select count(*) from side_effects_check_then_insert_probe where effect_key='job:probe';

-- Session B
begin;
select count(*) from side_effects_check_then_insert_probe where effect_key='job:probe';

-- Session A (only after BOTH selects returned)
insert into side_effects_check_then_insert_probe(effect_key,worker_id)
values ('job:probe','worker-A');

-- Session B
insert into side_effects_check_then_insert_probe(effect_key,worker_id)
values ('job:probe','worker-B');

-- Session A
commit;
-- Session B
commit;
```

Final read and cleanup:

```powershell
@"
select effect_key,worker_id,created_at
  from side_effects_check_then_insert_probe order by id;
select count(*) from side_effects_check_then_insert_probe where effect_key='job:probe';
drop table side_effects_check_then_insert_probe;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

Expected: both pre-checks `0`; both inserts succeed; final count `2`. Race window deliberately barrier se
wide ki gayi: both reads finish before either write. Log me fixture name + ordering likho.

> **Terms used in this step**
> - **Check-then-act** — invariant check aur state change do statements me; doosra transaction beech me enter kar sakta hai.
> - **Negative control** — knowingly broken mechanism jo verification ko fail-able prove karta hai.
> - **UNLOGGED table** — Postgres table without WAL durability; isolated experiment, production guarantee nahi.

---

## Step 6 — Closing reconciliation + cleanup (10 min) · executable

```powershell
@"
select created_at::date,count(*) from jobs where id>110 group by 1 order by 1;
select executed_at::date,count(*) from job_executions where job_id>110 group by 1 order by 1;
select status,count(*) from jobs group by status order by status;
select count(*) as total,max(id) as maxid from jobs;
select last_value from jobs_id_seq;
select count(*) as executions from job_executions;
select count(*) as effects from side_effects;
select job_id,count(*) as effect_count
  from side_effects group by job_id having count(*)>1 order by job_id;
select pid,application_name,state,backend_start,xact_start
  from pg_stat_activity where datname='relay' order by backend_start;
"@ | docker exec -i relay-db-1 psql -U postgres -d relay
```

Agar sirf baseline + successful collision jobs bane:

```text
jobs +2; executions +3; effects +2
closing: 93 succeeded / 15 failed / 3 dead_letter = 111
executions 100 · effects 5
historical count>1: only job 110 -> 2
new collision job: executions 2, effects 1
```

Ye relative arithmetic hai; extra failed fixtures hon to ids + causes naam se add karo. Final checks:

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Select-Object ProcessId,ParentProcessId,CommandLine
git diff -- src/worker.py src/models.py alembic/versions
.\.venv\Scripts\python.exe -m py_compile src\worker.py src\models.py
.\.venv\Scripts\alembic.exe current
```

Worker/reaper zero; idle-in-transaction zero; probe table absent; unique constraint present; legacy rows
still present; stdout copied before closing. **Commit tabhi when user explicitly chooses to commit.**

> **Terms used in this step**
> - **Excess execution** — jobs delta se zyada execution delta; duplicate delivery ka named evidence.
> - **Guarantee boundary** — keyed local ledger effects protected; legacy NULL rows and external effects outside claim.

---

# PART B — PREDICTION QUESTIONS — DO NOT PASTE

> Har answer relevant step se pehle **Prediction — frozen** block me. `idk` legitimate hai. Measurement ke
> baad prediction edit nahi; observed/explanation append. KEY corresponding output ke baad hi.

1. **Identity:** Din 1 collision me attempts `2` hua. Key `job_id`, `job_id + attempts`, ya payload hash me
   se kaunsa duplicate delivery ko same identity dega? Ek option turant kyu fail hota hai?
2. **Conflict result:** One-row `INSERT ... ON CONFLICT DO NOTHING` first insert aur duplicate insert par
   exception/rowcount me exactly kya return karega?
3. **Legacy NULLs:** Named `UNIQUE(effect_key)` ke under existing teen rows ki key `NULL` ho to migration
   accept hogi ya second/third `NULL` reject hoga? Reason likho.
4. **Rejected check:** Do transactions dono `SELECT count=0` dekh kar insert karein. Race window kis do
   instants ke beech hai, aur deterministic barrier usko kaise widen karta hai?
5. **Proof:** Collision job par effect count `1` aaye to kaunsa minimum DB + stdout evidence prove karega
   ki unique dedup ne kaam kiya, heartbeat ne duplicate avoid nahi kiya?
6. **Exception path:** Agar named conflict handling hata di aur duplicate insert `UniqueViolation` raise
   kare, current `worker.py` us exception ko kis branch me le jayega? `attempts < MAX_ATTEMPTS` aur terminal
   bound par statuses kya honge?

---

# PART C — VERIFICATION

| Check | Exact evidence | Correct mechanism | Wrong implementation jo otherwise pass hoti |
|---|---|---|---|
| Opening baseline intact | Job 110 effects `2`, total effects `3` | Din 1 evidence preserved | Table cleanup/backfill ne history rewrite ki |
| Direct unique impossibility measured | Safe transaction reports duplicate job 110; probe constraint absent after rollback | Migration problem data se derived | Assumption-only design; migration day par surprise |
| Migration preserves evidence | New key nullable; 3 old rows `NULL`; named unique exists; down/up me rows remain | Additive invariant boundary | `UNIQUE(job_id)` ke liye old row delete/update |
| Baseline insert works | One dispatch, one keyed row, insert `rowcount=1` | New effect admitted | Handler always no-op karta hai; collision count bhi `1` dikhega |
| Duplicate actually happened | Two execution rows, distinct workers, proved overlap, attempts `2` | Same Din 1 failure reproduced | One dispatch due heartbeat; count `1` dedup naam se mislabel |
| Dedup direct evidence | Effect count `1`; one insert `rowcount=1`, other `0`; same stable key | Unique constraint arbitrates | Application `if`, mark rollback, or no duplicate |
| Wrong check fails | Constraint-free two-session probe: both reads `0`, final `2` | Check-then-act race visible | Protected table use ki; constraint ne broken app check ko mask kiya |
| Constraint narrowly targeted | Named constraint in catalog and conflict code | Intended duplicate handled | Bare “ignore any conflict” hides unrelated data bug |
| Legacy boundary honest | Job 110 still has two NULL-key rows; new guarantee keyed rows se | No retroactive claim | “All side effects exactly once” overclaim |
| Cleanup | Probe table absent; workers/reaper 0; idle tx 0 | Experiment isolated | Open psql transaction locks later migration |
| Answers provenance | Frozen prediction text remains; observed appended; mtime before Step 4 | Score inspectable | Din 1 shape: final answers overwrite original idk |

**Expected centrepiece output shape, exact values that matter:**

```text
job_executions(collision_job) = 2
count(distinct worker_id)      = 2
overlap_seconds                = MUST BE MEASURED
side_effects(collision_job)    = 1
insert rowcounts               = {1, 0}
check-then-insert probe count  = 2
```

---

# PART D — SCOPE GUARD

| Tempting | Owner | Aaj karne se kya khota hai |
|---|---|---|
| Job 110 ki duplicate row delete/backfill karna | Never as cleanup; explicit data migration only with separate decision | Din 1 ka only live damage evidence mit jaata hai |
| Fencing token / claim generation | Week 4 build; Din 5 question | Aaj prove karna hai effect dedup generation blindness ke bawajood works |
| Enqueue `idempotency_key` | Din 4 | Do layers ek saath; count `1` kis layer se aaya attribution lost |
| Side effect + job mark same transaction | Din 3 decision | Crash-between-writes experiment disappear; external effects still outside transaction |
| Outbox build | Week 4 | Aaj local row invariant hai; external delivery atomicity separate problem |
| Retry/lease/heartbeat constants change | Not Din 2 | Din 1 vs Din 2 controlled comparison toot jaata hai |
| Generic `except IntegrityError: pass` | Never as dedup mechanism | Unrelated FK/NOT NULL/other unique bugs silently success ban sakte hain |
| Partial index with `job_id > 110` | Reject unless separately decided | Dataset boundary business policy ban jaata hai; replay holes |
| External email/HTTP/payment exactly-once claim | Week 4+ receiver cooperation | Database row uniqueness external effect ko rollback/dedup nahi kar sakti |
| Property test | Din 5 | Aaj pehle one concrete collision + one negative control close honge |

## Din 2 log obligation

`docs/logs/WEEK_03.md` me: opening bench; direct unique probe output; key choice + cost; row ka meaning;
migration up/down and named constraint; legacy NULL boundary; baseline rowcount; two worker IDs + measured
overlap; `{1,0}` insert rowcounts; effect count `1` Din 1 ke `2` ke against; constraint-free probe count `2`;
closing group-by reconciliation; cleanup; honest prediction score with preserved originals; apne shabdon me
`💡`; unresolved items with named owner.

`PROBLEMS.md` number **grep ke baad** only if measurement creates a genuinely new problem. `D-25` aaj
finalise mat karo; Din 6 writes decisions, while today supplies its measured `Rejected` evidence.