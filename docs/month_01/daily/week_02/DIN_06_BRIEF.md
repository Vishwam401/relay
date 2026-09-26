# DIN 6 BRIEF — Week 2 close: reconcile, likho, handoff

**Week 2 · Din 6** · Plan: [`../../planning/WEEK_02.md`](../../planning/WEEK_02.md) (DIN 6 section) ·
Log: [`../../logs/WEEK_02.md`](../../logs/WEEK_02.md) · Sealed: [`DIN_06_KEY.md`](DIN_06_KEY.md)

**Budget:** plan says **120 min**. This BRIEF adds **Step 0** (opening bench, which is also the week's
closing bench) and **Step 8** (the nine-times-slipped item gets a written verdict, either way). Honest
number: **~140 min**.

> **Paste rule.** Parts A, C and D go to Gemini. **Part B never travels. The KEY never travels.**
> Part B lives in `WEEK_02.md`'s `PART B` block, `## Din 6` subsection — **seven** questions today.
>
> **Seal rule.** A step's KEY section opens **after that step's output exists** — and today "output" means
> *a file on disk with the thing written in it*, not *a decision made in your head*.

---

## Today is different, and the difference is the whole risk

**No `src/` line changes. No migration. No experiment.** Five days of evidence become entries.

That sounds safe and it is the day with the most ways to quietly lose value, because **every output today is
prose**, and prose passes every check that does not read it. This week has already produced the exact
failure twice at the document layer:

| When | What happened |
|---|---|
| Stage Day | Four files reported complete, measured `0 B` / stale **on disk** — the editor was showing content the filesystem did not have. Eight minutes later they were real. `docs/daily/` and `docs/roadmap/` are gitignored, so `git status` could not help |
| Din 1–3 | `DDIA_CH8_LINKS.md` was "read and mapped" three days running while the file's mtime never moved |

So today's verification is not *"did I write it"*. It is **open the file and read the line**, for every one
of the seven files below. And two of those seven live on gitignored paths (`docs/roadmap/`, `docs/daily/`),
which means they will **never** appear in `git status` — their absence is silent by construction.

---

## Prereq — five log entries, and this is checked by opening the file

| Kya | How it is checked | What today builds from it |
|---|---|---|
| Din 1–5 entries in `docs/logs/WEEK_02.md`, each with a filled 📊 Measured section | Count the `## Din ` headings, then read each Measured block | **Today's entire raw material.** Nothing is recalled today — what is not in the log does not exist today |
| Each day's **closing reconciliation** with its own delta | Five closing blocks | Today's chain is built from those five deltas. A missing delta means the chain breaks **there**, by name |
| Din 1–5 **decisions with their costs** — backfill, expiry + poll interval, the heartbeat's three, `attempts` increment point, not-before storage, backoff formula, jitter formula, one-or-two migrations, terminal writer, lease-on-shutdown | Five entries | `D-22` and `D-23` are a **verbatim** copy of those decisions. **No new decision is taken today** — old ones get an address |

**All five entries exist and all five are filled** `[MEASURED-R 2026-08-28]`. Din 5's was written at close
and is marked as reviewer-written — **the 💡 and 🧠 sections of Din 1–5 still need rewriting in your own
words**, and that is not today's job unless you want it to be.

**One prereq is negative and it matters more than the positive ones:** today's evidence is frozen. Any
`src/` change after today makes this week's measured numbers non-comparable, and those numbers are the
entire base of `D-22` and `D-23`.

---

# PART A — STEPS

---

## Step 0 — Opening check, which is also the week's closing bench (10 min) · executable

**Take these readings first, write them down, then build the chain.** Reversed, the door opens to *"I re-ran
the query until the arithmetic matched"*.

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId, ParentProcessId, CommandLine
```

```sql
select pid, application_name, state, backend_start, xact_start, left(query,50) as q
  from pg_stat_activity where datname = 'relay' order by backend_start;

select status, count(*) from jobs group by status order by status;
select count(*) as total, max(id) as maxid from jobs;
select last_value from jobs_id_seq;
select count(*) from job_executions;
select attempts, count(*) from jobs group by attempts order by attempts;
select id, status, attempts from jobs where status in ('running','pending') order by id;
select id, status, attempts from jobs where status = 'dead_letter' order by id;
select conname, convalidated, pg_get_constraintdef(oid) from pg_constraint where conrelid = 'jobs'::regclass;
select version_num from alembic_version;
```

**Expected, from Din 5's close plus the reviewer probe** `[MEASURED-R 2026-08-28]`:

```
89 succeeded / 15 failed / 3 dead_letter / 0 pending / 0 running     total 107
max(id) 108 · jobs_id_seq 108 · job_executions 94
attempts:  0|95 · 1|3 · 3|8 · 4|1
dead_letter ids: 104 (attempts 3) · 105 (attempts 3) · 108 (attempts 4)
jobs_status_check convalidated = t, five values · alembic_version = 682e01d87be9
```

Anything else is `E2` and Step 1 waits until the divergence has a **named cause**.

### Three things in that output that the chain has to survive

1. **Job `108` is at `attempts = 4`.** It is the reviewer's `P-27` probe and it is the only row in the table
   above the bound. Name it in the chain; do not treat it as a normal `dead_letter`.
2. **`running = 0` and `pending = 0`.** Both are DoD items and **a measured zero still gets written**, with
   today's date. Omitting a zero because it is uninteresting is how next week inherits an unverifiable
   baseline.
3. **`max(id) = 108 = jobs_id_seq`.** No new gap this week; `P-05`'s single gap is still at id `79`. Write
   the gap as evidence, and do **not** reset the sequence to make the numbers look tidy.

> **Terms used in this step**
> - **`convalidated`** — `pg_constraint` boolean: `true` once the constraint has been checked against every
>   existing row.
> - **`backend_start` vs `xact_start`** — when the connection opened, versus when its current transaction
>   opened. `NULL` `xact_start` = connected, not in a transaction, holding no locks.

---

## Step 1 — The chain, five deltas, one line each (20 min)

**Shape: week opening + each day's delta = today's actual counts.** Never from `max(id)`, never from id
contiguity — `P-05` is the reason.

| Line | Where it comes from |
|---|---|
| Week opening — `failed` / `running` / `succeeded` / total / `job_executions` | the plan's BENCH block (Din 1's bench reproduced it exactly, so its provenance is settled) |
| `±` Din 1 delta | Din 1 entry — one new job (`88`) |
| `±` Din 2 delta | Din 2 entry — **zero** new rows; three rows moved buckets (`41`, `63`, `65`) |
| `±` Din 3 delta | Din 3 entry — eight new jobs (`89`–`96`), and `job_executions` grew **more** than `jobs` |
| `±` Din 4 delta | Din 4 entry — `boom` jobs plus retry's extra execution rows, and two probe rows |
| `±` Din 5 delta | Din 5 entry — two probes turned terminal, two new `slow` jobs, plus the `P-27` probe |
| `=` today's closing | must equal Step 0's output, **across five buckets** |

**Two rules, and they pull in opposite directions on purpose:**

- **If it joins, say what that does and does not prove.** It proves no row was created or destroyed outside
  the recorded deltas. It does **not** prove the days were clean — three days this week reconciled perfectly
  while a forgotten process was still running, every time because the leftover process had nothing to move.
  That is an empty queue, not detection.
- **If it does not join, that is the finding (`E5`).** Name the day it breaks on. Do not fit the difference
  into the nearest day. Suspects in order: a forgotten worker (`P-13`), an extra reaper run, a reclaim
  during Din 5's shutdown that no delta counted, and a day whose delta was never recorded.

**And the line that is new this week:** the chain closes across **five** status buckets where the week opened
with three. `dead_letter` did not exist on Din 1.

---

## Step 2 — The `failed` count is one number holding three contracts (10 min) · executable

This step exists because the chain will hide it.

```sql
select id, status, attempts from jobs where status = 'failed' order by attempts, id;
```

**After Din 5 the retry writer never writes `failed` again.** Its failure branch writes `pending` or
`dead_letter`; the **only** remaining live producer of `failed` is the unknown-`type` branch
`[MEASURED-R from source]`. So every `failed` row in the table is historical, and they do not mean the same
thing:

| Group | Example | What it means |
|---|---|---|
| unknown `type`, `attempts = 0` | job **75** (`send_receipt`) | no handler existed. Today's code still produces this |
| bounded out before `dead_letter` existed | job **98** (`attempts = 3`) | **today's code would call this `dead_letter`** |

**Write one sentence naming which `failed` rows are historical bounded-outs**, and one sentence saying that
`dead_letter` did not rename them. Without it, Week 3 reads `failed = 15` as *"jobs that failed once"* — and
the count would then be wrong in a direction that looks plausible.

**This is `D-21`'s amendment one layer up:** a summary count stops meaning one thing the moment a status
value's contract changes mid-week.

---

## Step 3 — Grep, then assign numbers (10 min) · executable

**The grep runs on the day you assign the number, not the day the plan was written (`E6`).** Two collisions
have already happened in this project (`D-09` was reserved in roadmap Part 2; `P-07` was claimed twice).

```powershell
Select-String -Path docs\DECISIONS.md -Pattern '^## `?D-'
Select-String -Path docs\PROBLEMS.md -Pattern '^## P-'
```

**Put the output in the log.** Expected `[MEASURED-R 2026-08-28]`: `P-01`..`P-27` present, so **next free is
`P-28`**; `D-` next free is **`D-22`**, and `D-09`..`D-20` belong to roadmap Part 2 and must not be reused.

Then check every `D-`/`P-` you cite today actually has a heading. A citation with no heading is a **dangling
citation**, not a typo — write the entry or drop the citation.

> **Terms used in this step**
> - **Dangling citation** — a reference to an entry number that no heading defines. It reads as authoritative
>   and resolves to nothing.

---

## Step 4 — `D-22`: lease duration **and** handler timeout, one entry (25 min)

One entry, not two, because of `P-15`: Relay does not bound its handlers, so a lease shorter than the handler
**manufactures** duplicate execution, and a lease longer than the handler slows recovery. Two ends of one
trade.

Shape as in `DECISIONS.md`: **Problem · Options · Chose · Cost · Rejected · Revisit when.** Plus:

- **`Cost` is never empty** — that is `DECISIONS.md`'s own rule, and an empty `Cost` means the decision was
  not understood.
- **Exactly one provenance tag per `Cost`/`Rejected` line:** `[MEASURED]` · `[MEASURED-R]` · `[INFERRED]` ·
  `[NO EVIDENCE]`. **An untagged line reads as `[MEASURED]`**, which is this file's most expensive default.
- **Cite inputs by name:** Din 2's reclaim latency, Din 3's two runs with their overlap evidence, Din 5's
  three durations on one line.

**And the hole has to be written as a hole.** Din 5 chose lease-on-shutdown Option A (do nothing, let the
handler finish) and **its cost was never paid**: the run used `handle_slow`'s default `8.0 s` against a `30 s`
lease, so the lease could not expire — no reclaim, no second claim, no contested mark, and the `10.0 s`
heartbeat never fired `[MEASURED-R]`. So *"graceful shutdown narrows the stranded-work window and does not
close the duplicate one"* is `[INFERRED]` today. **Tag it that way.** Naming the run that would close it
(`slow` with `payload {"seconds": 45}`, `SIGBREAK` at `T = 3 s`) belongs in `Revisit when`.

**Two open items take their answer here, and both point at `D-22` from `LEARNING_LOG.md`** — answer or defer
**with an owner**; staying silent is not the third option:

1. *"Completion evidence is a `print`, not a row"* — a finished handler whose mark was lost and a death
   mid-handler have **identical** database state.
2. `P-11`'s `D-22`-shaped question — **does an attempt/claim identifier on `job_executions` need to exist
   before the reaper rather than with the retry logic?**

**Never write a mitigation as an elimination.** `narrows`, not `closes`. The heartbeat's own limit is
measured and it is inverse to the severity of the failure a lease exists for (`P-21`).

---

## Step 5 — `D-23`: retry policy, and one sentence in it is already false (25 min)

Three things in one entry, because separating them would orphan each one's reason: the increment point, the
backoff formula, and why jitter.

- **Increment point** — Din 4 chose **on claim**, inside the claim's row lock. The rejected option's cost goes
  under `Rejected` in the same entry. **The reaper's reclaim is a third path** and it gets its own line.
- **Backoff formula, verbatim** — `BASE = 5.0`, `MULT = 2.0`, `CAP = 15.0`, `MAX_ATTEMPTS = 3`. `BASE` moved
  from `3.0` on Din 5 and the reason is arithmetic: equal jitter halves the floor, so the quantum check runs
  against `base/2`, and `2.50 s > 2.0 s` gives `0 %` masked `[MEASURED-R]`. **Say it was derived, not
  measured** — only one inter-attempt gap was produced on Din 5 (`6.130075 s`, bounding the delay to
  `(4.10, 6.13]`) and no multi-job distribution was re-measured, so `P-24`'s convoy half still rests on
  Din 4's rows.
- **`CAP` is inert and must be labelled as such** — it first binds at attempt `4` (`raw = 24.0`) and
  `MAX_ATTEMPTS = 3` means attempt 4 does not exist (`P-26`). Din 5's verdict: *reserved for a future
  `MAX_ATTEMPTS`, crossing point `n = 4`*. **Not "tuned".**
- **Why jitter** — Relay's own `[MEASURED]` argument is `P-14` (equal handler durations synchronise workers).
  Brooker's thundering-herd argument goes beside it tagged `[INFERRED]`. **Two lines, two tags**, because one
  was measured here and one was read.

### The sentence that cannot be written

*"`MAX_ATTEMPTS = 3` bounds `attempts`"* is **false, and the counterexample is in the table.** Job `108` is at
`attempts = 4` `[MEASURED-R]`: the reaper reclaimed a bound-crossed row, the claim gate does not consult
`attempts`, the worker printed `attempt=4/3`, `record_execution()` committed, the handler ran, **then**
`dead_letter` was written. `P-27`. The bound is evaluated in the failure branch, **after** the handler.

**Write one of two forms, and it is a decision, not phrasing:**

| Form | What it commits to |
|---|---|
| **Accept the overdraft** | *"bounds retry scheduling; a row re-entering the queue at the bound costs one more full dispatch, handler included"*. Cheap, honest, and it names a real extra side effect for any non-`boom` handler |
| **Move the term to the claim gate** | `AND attempts < :max` makes the bound-crossed row unclaimable — and immediately raises *then who terminalises it?* That is a sweep, a **fifth** `status` writer, and **not a Week 2 change** |

Also into `Cost`: Din 4's measured inter-attempt gaps by name, and the fact that `job_executions`'s
`count(*) > 1` now has **five** causes.

---

## Step 6 — Amend `D-06` and `D-21`, by appending (20 min)

**Amendments append. The old lines stay exactly as written** — deleting one destroys the record that the
entry *predicted* this, and that prediction is the entry's most valuable line.

### `D-06` — `dead_letter`, `NOT VALID`, and how complete the prediction was

`D-06`'s Cost 4 already described this pattern. Record how much of it held:

- **Which option ran and whether `NOT VALID`'s benefit was obtained.** Din 5 chose **two migrations**
  (`15a05eeb0f79` → `convalidated = false`, `682e01d87be9` → `true`) `[MEASURED-R]`. The missing condition in
  Cost 4 now has a name: **`NOT VALID`'s benefit is a property of transaction *boundaries*, not of the
  keyword** — Alembic wraps `upgrade()` in one transaction, so a single-migration version holds
  `ACCESS EXCLUSIVE` until commit and runs the validation scan under it.
- **The lock-queue result, split into its two halves and not merged.** `[MEASURED-R]`: the queue forms and a
  plain `SELECT` in an open transaction blocks the whole DDL — `wait_event_type = Lock`,
  `AccessExclusiveLock granted = false` behind `AccessShareLock granted = true`, ended by
  `lock_timeout = 9s`. **Declared substitution:** that was `LOCK TABLE ... IN ACCESS EXCLUSIVE MODE`, not the
  migration, so the **hold duration** is still `[INFERRED]` — and the hold duration is the whole Option A
  versus Option B number. Writing the hold duration as measured would be the most expensive lie in this
  system.
- **`downgrade`'s truth, both halves.** With a `dead_letter` row present the four-value constraint cannot come
  back: `check constraint "jobs_status_check" of relation "jobs" is violated by some row`, and **the error
  does not name the offending rows**. *Reversible in shape, conditional on data.* And separately:
  `downgrade -1` from head is a **no-op that reports success**, because Postgres cannot un-validate a
  constraint — so `alembic_version` and the schema can diverge with nothing in the output showing it.
- **Cost 1 now applies in five places.** `status` writers went one → five this week: claim, reaper, retry,
  terminal, **heartbeat**. The shutdown path writes **no** `status` (Option A) — and that absence is a
  decision, not an omission, so write it as one.

### `D-21` — `count(*) > 1` has expired

- **When it expired and from what** — the reaper's `running → pending` (Din 2/3) and retry (Din 4).
- **What it means now** — a **question**, not an answer. Each extra row needs its `worker_id`, its
  `executed_at`, and the job's `attempts` read alongside. The word *duplicate* applies only where **overlap
  was proved** — one job id, `95`.
- **Five causes now, by id:** same-worker re-dispatch (`44`), reclaim re-execution (`63`, `65`), overlapping
  duplicate (`95`), bounded retry (`98`–`104`), bound-crossed re-dispatch (`108`, `P-27`).
- **The identifier question**, cross-referenced with `D-22` — same answer in both places, or the same deferral
  with the same owner.

---

## Step 7 — `MAP.md`, `LEARNING_LOG.md`, `CURRENT_WEEK.md`, handoff (25 min)

**`MAP.md` — one index row per entry, and no reasoning.** Its own header says it: add a row for a new entry,
update the row for an amended one, copy no reasoning. Index A (symptom → mechanism → entry) in the correct
subsections; Index B (decision → cost → revisit) gets a row each for `D-22`/`D-23` and **updates** the
existing `D-06`/`D-21` rows rather than adding new ones; Index C (component → entries) gets `jobs.status`
(five writers), `jobs.attempts`, `next_attempt_at`, the lease column, the reaper, `Shutdown`; plus the
next-free numbers note. **One line per cell.** A paragraph copied from `DECISIONS.md` means two files now hold
the same truth, and they will diverge.

**`LEARNING_LOG.md` — three places, and every touched item gets a verdict:**
closed (**with the day and measurement that closed it, by name**) or carried (**with an owner, by name**).
*Carried* without an owner and *forgotten* read identically — `POSTMORTEMS.md` entry #2 carried a
*"deferred"* label through all of Week 0 when the honest label was *"slipped"*. Then the Logs-by-Week row for
Week 2, and the companion-documents table's next-free numbers and counts (which this session already
updated — **verify, do not assume**).

**`CURRENT_WEEK.md`** — week status table with Week 2's close, pointer moved to Week 3. This file is
gitignored, so open it.

**`docs/daily/WEEK_02_HANDOFF.md`** — three headings, the same shape as `WEEK_01_HANDOFF.md`, in this order:

1. `## What Stuck` — **rebuildable from scratch with no notes.** Blank editor, nothing open.
2. `## What Needs Reinforcement` — **recognisable, but not derivable under viva pressure.** *"haan haan ye to
   pata hai"* is this category's signal, not the previous one's.
3. `## What Week 3 Must Not Assume`

**Both definitions get written into the file**, not left in memory. Seeds are starting points, not verdicts —
if the honest answer differs, the item moves, and that movement is the list's whole purpose.

| Heading | Seeds |
|---|---|
| **What Stuck** | the lease as a deadline written at claim time · why the reaper is a separate process · compare-and-set on **every** `status` writer · extending a `CHECK` via `NOT VALID` + `VALIDATE` · why bounded retry, backoff and jitter |
| **What Needs Reinforcement** | dead node versus slow node · three-valued logic on `NULL` comparisons · `now()` being transaction-start time · fencing token versus compare-and-set · the five causes of `count(*) > 1` |

**The third heading is Week 3's Din 1 input**, exactly as Week 1's third heading was this week's. Two items go
in by name because the plan has known them since day one: **contract #2 is unprotected until Week 3's dedup**,
and **the reaper narrows the duplicate window and does not close it**. Add from this week's measurements: the
`attempts = 4` overdraft (`P-27`), the untested shutdown-lease interaction, and `P-23`'s open exercise half.
**And if the chain broke on a day, that day's name goes here too** — Week 3 needs to know which day's numbers
cannot be trusted.

---

## Step 8 — The nine-times-slipped item gets a verdict, not a tenth carry (10 min)

The **five written Week 2 answers** have slipped nine consecutive times: Week 1 Din 5 → Din 6 → Din 7 → Stage
Day → Week 2 Din 1 → 2 → 3 → 4 → 5. `CURRENT_WEEK.md` states the blocking rule in its own words — *"Week 2
Din 1 should not start before it exists in his own words"* — and Week 2 is over.

The four questions, named: the reaper's predicate using only Din 1's columns and why it fails · the smallest
schema addition and the new failure it creates · job 41 versus job 63 · a lease shorter than the slowest
handler.

**Today is the last day of the week, so there are exactly two honest endings:**

| Ending | What it costs |
|---|---|
| **Write them** — four of the five are now *measured*, so this is cheaper than it has ever been | ~20 min, and the answers are now partly recall of measurements rather than derivation. Say that |
| **Record that they were not written this week**, with an owner and a date | Honest, and it closes a nine-item carry. **`slipped`, not `deferred`** — a deferral has an owner and a plan; this was neither |

**A tenth silent carry is the one outcome that teaches nothing**, and the reason it is a step today is that
items which live only in a table stop being read.

Same treatment, one line each: Din 3's five unroled job ids (`89, 90, 92, 93, 94` — `94` matters most, a
`super_slow` with one dispatch and no duplicate), `2026-08-24` having no record, and Week 1 Din 7 having no
log entry.

---

## Step 9 — Log, cleanup, commit (15 min)

Into `docs/logs/WEEK_02.md`, full shape: goal → goal met (yes/no/partial) → **anything else learned** (a
separate field) → 📊 Measured → 💡 Understood → 🧠 self-check with an honest score → corrections table →
🚧 Unresolved → ❓ Next thought.

Specifically for today: **the full week chain with its five per-day deltas**, the break's day by name if it
broke, **Step 3's grep output**, the `running` count at week close (a measured zero is still written), and the
DoD audit where **every untick carries either an owner or what it specifically needs** — one of the two,
never both, never neither.

**Cleanup:** no new probe rows today. If a query's output went into a temporary file, copy the output into
the log **first**, then delete the file, then record that it was deleted. **The week's probe rows are not
deleted** — `88`, `97`, `104`, `105`, `108` are named in the log and counted in the chain; deleting one breaks
the delta arithmetic and destroys `P-05`'s evidence.

**And run the third connection check.** `psql` backend `37` has been connected since
`2026-08-25 09:55:12+00` — `~3 days`, `state = idle`, `xact_start NULL`, so zero locks `[MEASURED-R]`. It sat
through Din 5's `ACCESS EXCLUSIVE` DDL and both existing cleanup checks passed with it there. Close it or
record why not, with its PID.

**Commit: staged paths by name, never `.`** — and today that rule matters most, because seven files are
touched and **three sit on gitignored paths**, which means they will not show up in `git status` at all:

```
.gitignore excludes  docs/roadmap/   docs/daily/   docs/planning/   docs/ddia_summaries/
```

So `CURRENT_WEEK.md`, `WEEK_02_HANDOFF.md` **and `DDIA_CH8_LINKS.md`** are unstageable and invisible to
`git status` — open them to verify. (Din 5's BRIEF listed `DDIA_CH8_LINKS.md` as a commit path; that
instruction was wrong, and `git check-ignore -v` is how it was caught `[MEASURED-R]`.)

Committable list: `docs/DECISIONS.md`, `docs/PROBLEMS.md`, `docs/MAP.md`, `docs/LEARNING_LOG.md`,
`docs/logs/WEEK_02.md`.

---

# PART B — PREDICTION QUESTIONS

**Not in this file, on purpose.** `docs/planning/WEEK_02.md`, `PART B — PREDICTION QUESTIONS` block,
`## Din 6` subsection — **seven** questions.

Answer from your own head **before** the relevant step runs, in
**`docs/daily/week_02/DIN_06_ANSWERS.md`**, and hand over that path at day close.

**Two process notes from Din 5, and both are cheap to fix:**

1. **Din 5's answers file existed — that is real progress after Din 4's nothing-submitted.** But its mtime was
   `15:03`, *after* the migrations (`14:27`) and *after* both `dead_letter` transitions (`14:50–14:51`)
   `[MEASURED-R]`. One write at the end of the day is reconstruction, not prediction (`E8`). **Write each
   answer before its step**, and let the file's mtime carry seven separate saves if you like.
2. **`idk — <full correct answer>` is a self-inflicted zero.** All seven Din 5 answers opened with `idk` and
   then gave the mechanism correctly. `idk` means *I do not know* and scores as not-answered. **Pick one of
   the two, not both.**

| Part B question | Answer it before |
|---|---|
| 1 (which day did the chain break on — or did it join, and what was missing?) | Step 1 |
| 2 (which `D-22` `Cost` lines are `[MEASURED]` versus `[INFERRED]` — and if fewer than two are measured, was the entry writable today?) | Step 4 |
| 3 (`D-06` Cost 4 was a prediction — was it fully right, or was a condition missing? Name the condition in one line) | Step 6 |
| 4 (`D-21` predicted `count(*) > 1`'s expiry — which part was right, and which part got bigger?) | Step 6 |
| 5 (`status` writers went one → five — where does `D-06`'s Cost 1 apply now, and on which writer was a guard easiest to forget?) | Step 6 |
| 6 (does every carried open item have a named owner — is any left without one?) | Step 7 |
| 7 (which handoff item had to move from *What Stuck* to *What Needs Reinforcement* — and was that honest or comfortable?) | Step 7 |

---

# PART C — VERIFICATION

**Every check is differential, and the rule holds even though today's outputs are prose: a check that cannot
fail is not a check (`P-18`).** For each row, read both right-hand columns and confirm they differ.

| Check | Command / action | Mechanism present | Mechanism absent |
|---|---|---|---|
| The bench was taken before the chain was built | Step 0's output sits **above** Step 1's in the log | Ten query outputs recorded, then the chain | The chain first, then a bench that agrees with it. Both look identical afterwards — order is the only evidence |
| The chain is written per day | Read the week-close block | Five separate delta lines with job ids named, then closing counts against Step 0's `psql` output | One line: *"everything matched"*. That sentence is produced equally by a joined chain and by a chain nobody built |
| Job `108` is named, not absorbed | `Select-String -Path docs\logs\WEEK_02.md -Pattern '108'` | `108` appears in the chain with `attempts = 4` and its `P-27` role | It is counted inside `dead_letter 3` and the only row above the bound is invisible |
| The `failed` count is disambiguated | Read Step 2's sentences | Historical bounded-outs named by id, and one line saying `dead_letter` did not rename them | `failed 15` sits in the chain as a single number. Next week will read it as "jobs that failed once" and be wrong plausibly |
| Numbers came from a grep, not the plan | Step 3's output **in the log** | Grep output present, assigned numbers match its next-free | Numbers lifted from the plan's register. A collision surfaces weeks later, in another file |
| No dangling citations | `Select-String -Path docs\DECISIONS.md,docs\PROBLEMS.md -Pattern '^## `?D-22'` (and each cited number) | Every cited `D-`/`P-` resolves to a heading | A citation resolving to nothing — reads authoritative, defines nothing (`E6`) |
| Every new entry is fully priced | Open `D-22` and `D-23` | Every `Cost` line non-empty, **exactly one** provenance tag each | One untagged `Cost` line — and untagged reads as `[MEASURED]` |
| `D-22`'s hole is tagged as a hole | Read `D-22`'s `Cost` | The shutdown-lease interaction tagged `[INFERRED]`, with the `payload {"seconds": 45}` run named in `Revisit when` | It reads `[MEASURED]` because Din 5 "ran the shutdown test". The run happened; **its subject did not** |
| `D-23` does not claim a false invariant | `Select-String -Path docs\DECISIONS.md -Pattern 'attempts'` inside `D-23` | Either the overdraft is written, or the claim-gate change is decided and owned | *"bounds attempts"* — refuted by job `108`, which the same document's chain counts |
| The lock-queue substitution is declared | Read `D-06`'s amendment | Queue-forms `[MEASURED-R]`, hold-duration `[INFERRED]`, and `LOCK TABLE` named as the substitute | *"`ACCESS EXCLUSIVE` measured"* with no substitution noted — and Week 1 Din 3's failed attempt gets quietly overwritten |
| Amendments appended, not rewritten | Open `D-06` and `D-21` | Original `Cost` lines **verbatim**, amendment beneath with its date | An old line edited — and the record that the entry predicted this is gone |
| `MAP.md` has a row per entry and no reasoning | `Select-String -Path docs\MAP.md -Pattern 'D-22|D-23'`, then read the new rows | One row per entry in Index B, pointers in A/C, one line per cell | Either the entry is missing (so it is grep-only, defeating `MAP.md`) or a paragraph was pasted in (so two files hold one truth) |
| Open items tell the truth | Read `LEARNING_LOG.md`'s open-items tables | Every item this week touched carries a closing day **or** an owner | An item sits exactly as it did at Week 1's end — reading as "never touched" when it was |
| Next-free numbers agree in two places | `LEARNING_LOG.md`'s companion table beside Step 3's grep | Both say `P-28` / `D-22` | They disagree, and next week trusts the wrong one |
| Handoff headings match Stage Day's shape | `Select-String -Path docs\daily\WEEK_01_HANDOFF.md,docs\daily\WEEK_02_HANDOFF.md -Pattern '^## What'` | Three headings each, first two **word-for-word identical**, third differing only in week number | Renamed or reordered — and Week 3's Din 1 cannot consume it as input the way this week's Din 1 did |
| No handoff heading is empty | Open `WEEK_02_HANDOFF.md` | All three have at least one line; both definitions written in the file | An empty *What Week 3 Must Not Assume* — Week 3 inherits this week's assumptions with no record of them |
| The nine-times-slipped item has a verdict | `Select-String -Path docs\logs\WEEK_02.md -Pattern 'five written'` | Either the answers, or an explicit *slipped, owner, date* line | A tenth carry inside a table nobody reads |
| Files were read from disk, not from an editor | The `Select-String` commands above | Output from the filesystem | Content seen in an editor buffer. Stage Day nearly passed its gate on `0 B` files, and `git status` cannot help on gitignored paths |
| Something was actually committed | `git status` ; `git log --oneline -1` | Today's commit naming `docs/DECISIONS.md`, `docs/PROBLEMS.md`, `docs/MAP.md`, `docs/LEARNING_LOG.md`, `docs/logs/WEEK_02.md` | An empty `git status` read as "nothing to write". **Three** of today's files are gitignored and will never appear there |
| The gitignored set is actually known, not assumed | `git check-ignore -v docs\roadmap\CURRENT_WEEK.md docs\daily\WEEK_02_HANDOFF.md docs\ddia_summaries\DDIA_CH8_LINKS.md` | Three lines, each naming the `.gitignore` rule that excludes it | Assuming from memory which paths are ignored — Din 5's BRIEF listed `DDIA_CH8_LINKS.md` as committable and it is not |

---

# PART D — SCOPE GUARD

| Tempting | Owner | What doing it early costs |
|---|---|---|
| Fitting the chain's difference into the nearest day to make it balance | **never (`E5`)** | After that, where the error happened is unknowable and next week stands on an invented baseline. **A chain that does not join is a finding**, possibly this week's most honest output |
| Filling a missing number from memory today | **never** | A plausible number and a measured one look identical in this file, and six months from now this is revision material. `[NO EVIDENCE]` is fine; a wrong number is not |
| Adding `AND attempts < :max` to the claim gate because `P-27` is annoying | **Week 3** | It is a `src/` change on the day the week's numbers freeze, and it needs a sweep to terminalise the unclaimable row — a **fifth** `status` writer with its own guard and `rowcount`. Today `P-27` gets **written**, not fixed |
| Re-running Step 7 properly with `payload {"seconds": 45}` "since it only takes a minute" | **Week 3 Din 1, or a named catch-up slot** | It is the right experiment and it is not today's. Running it now adds execution rows to a chain being closed, and mixes a measurement day into a writing day. Name it in `D-22`'s `Revisit when` |
| One small `src/` cleanup — a Din 5 loose end | **outside this week** | Not one line today. Any code change after today makes this week's measured numbers non-comparable, and those numbers are `D-22`/`D-23`'s entire base |
| Designing the idempotency key today "so Week 3 is ready" | **Week 3** | The same trap on the week's last day. This week's honest guarantee — *the duplicate window narrowed, it did not close* — is already written; solving it today turns Week 3's property test into paperwork |
| Planning Week 3's first day today | **Week 3's own plan** | Week 3's plan stands on this week's handoff list, and that list is being written **today**. Planning before it exists makes the handoff decoration |
| "Fixing" the fixture rows (41/63/65) or the probe rows at week end | **never** | They were reclaimed on Din 2 and are ordinary rows now. Touching them breaks today's chain, and their pre-reclaim evidence survives only in Din 2's entry |
| Resetting `jobs_id_seq` so the closing numbers look tidy | **never** | The gap is `P-05`'s evidence. Resetting it deletes evidence |
| Quietly dropping an open item | **never** | The table exists so nothing disappears between weeks. An item closes with a **named measurement** or carries with a **named owner**. There is no third route |
| Renaming Week 1's `failed` rows to `dead_letter` for consistency | **never** | It would falsify the log. `dead_letter` is a new contract; history stays on the old one, and Step 2's job is to **say so**, not to erase the difference |
