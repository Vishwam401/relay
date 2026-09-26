# DIN 3 BRIEF — 🎯 Zinda par slow worker: ek job, do execution

**Week 2 · Din 3** · Plan: [`../../planning/WEEK_02.md`](../../planning/WEEK_02.md) (DIN 3 section) ·
Log: [`../../logs/WEEK_02.md`](../../logs/WEEK_02.md) · Sealed: [`DIN_03_KEY.md`](DIN_03_KEY.md)

**Budget:** plan says **150 min**. This BRIEF adds **Step 1** (~15 min) and **Step 2** (~15 min), which are
Din 2's unpaid debts and not new work. Honest number today: **~175 min**.

> **Paste rule.** Parts A, C and D go to Gemini. **Part B never travels. The KEY never travels.**
> Part B does not live in this file — it is in `WEEK_02.md`'s `PART B` block, `## Din 3` subsection,
> six questions.
>
> **Seal rule.** A step's KEY section opens **after that step's measurement has run** — not after you have
> written your answer.
>
> **Two days, `0/6` and `0/6`, both for absence of data.** Neither day's answers were written down. That
> means Din 1 and Din 2's measurements have **no** prediction baseline, and today is the day the project
> either starts producing that data or stops pretending it will. Write today's six first. `idk` is a valid
> written answer, it scores as not-answered, and that is accurate.

---

## Today's shape, in one paragraph, because it is different from the plan's

The plan expected Din 3 to walk in holding two numbers from Din 2: a **measured reclaim latency** and a
**configured lease duration**. It has one of them. Reclaim latency was never measured, because nothing ever
expired — all three reclaims fired the `IS NULL` branch. **The expiry branch has still never been evaluated
against a single row.** And the lease that *was* configured (`30 s`) is longer than the only long handler in
`REGISTRY` (`8 s`), which means with today's numbers the centrepiece **cannot happen**. So today opens by
paying two debts and taking one decision, and only then builds the failure.

---

## Prereq — five things, and only two of them are clean

| Kya | Kya dikhna chahiye | Status |
|---|---|---|
| Reaper exists as a separate process, guard + `rowcount` + predicate in `WHERE` | `src/reaper.py`, and the compiled SQL matches what was written | ✅ Din 2, `[MEASURED-R]` |
| Reclaim actually moved rows | 41/63/65 `pending` + `claimed_at NULL`, 75 `failed` | ✅ Din 2, `[MEASURED-R]` |
| **Din 2's measured reclaim latency** | ❌ **Does not exist.** Undefined, not zero — nothing expired | ⬜ **Step 2 today** |
| **A reaper output that can answer "did the reaper run in that window?"** | ❌ `post_status` is asserted, and an empty pass prints nothing (`P-20`) | ⬜ **Step 1 today** |
| **A handler longer than the lease** | ❌ `handle_slow` = `8.0 s`, lease = `30 s` | ⬜ **Step 3 + 4 today** |

**And one prereq that is negative:** 41, 63, 65 are **not** a fixture any more. They are ordinary `pending`
rows. Re-sticking them to `running` is manufactured evidence. Today seeds its own.

---

# PART A — STEPS

---

## Step 0 — Opening check, and the queue is *not* empty (10 min) · executable

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId, ParentProcessId, ThreadCount, CommandLine
```

**Read `ParentProcessId`, not the row count.** Din 2 measured that two OS PIDs can be one interpreter — the
parent was a 1-thread/3.9 MB stub and the child was the real process, with **one** DB connection between
them `[MEASURED-R]`. Today you need **two real workers**, and a count of `2` in that table is not evidence
of two workers. It is evidence of two rows.

```sql
select pid, state, xact_start, backend_start, application_name, left(query,50) as q
  from pg_stat_activity where datname = 'relay' order by backend_start;

select status, count(*) from jobs group by status order by status;
select count(*) as total, max(id) as maxid from jobs;
select last_value from jobs_id_seq;
select count(*) from job_executions;
select id, type, status, claimed_at, created_at from jobs where status <> 'succeeded' and status <> 'failed' order by created_at, id;
select id, status from jobs where id = 75;
```

**Expected against Din 2's close:** `3 pending / 0 running / 75 succeeded / 9 failed`, total `87`,
`max(id) 88`, seq `88`, `job_executions 58`, `attempts = 0` everywhere, 75 `failed`. Anything else is an
`E2` divergence and Step 1 waits.

### The thing this step exists for, and it will bite silently otherwise

The three `pending` rows are **the oldest rows in the table**:

| id | type | handler | `created_at` |
|---|---|---|---|
| 41 | `sleep` | `2.0 s` | `2026-08-17 13:57:24+00` |
| 63 | `slow` | `8.0 s` | `2026-08-18 13:55:22+00` |
| 65 | `slow` | `8.0 s` | `2026-08-18 14:10:18+00` |

The claim query is `order_by(Job.created_at, Job.id).limit(1)`. So **any** worker you start today claims
41, then 63, then 65 — roughly **18 seconds of handler time** — *before* it looks at anything you enqueue.
They cannot be deleted: row deletion breaks the delta arithmetic and destroys `P-05`'s evidence.

**Decide in writing, before starting a worker, and do not revisit it after seeing the output:**

| Choice | What you get | What you lose |
|---|---|---|
| **Drain them first** — one worker, no reaper, let all three finish, then start the real run | A clean empty queue for the centrepiece, and **free evidence**: 63 and 65 will each get a **second** `job_executions` row with a **different** `worker_id`. That is the duplicate door Din 2 opened, executing | ~20 s, and three rows leave `pending` so today's delta has two separate causes in it |
| **Leave them and enqueue anyway** | Nothing extra to do | Your centrepiece job sits behind 18 s of unrelated handler time, worker B's timing is unrelated to your lease, and the run's clock arithmetic is polluted |

**Whichever you pick, one thing is not optional:** before that worker runs, record
`select job_id, worker_id, executed_at from job_executions where job_id in (41,63,65) order by job_id;`
Right now that returns **two** rows (63 and 65 from Aug 18) and **41 has none**. After the drain it will
return four, and 41 will have its first. That before/after pair is the only place the door being open is
visible as a measurement rather than an argument.

> **Terms used in this step**
> - **`ParentProcessId`** — the PID that created this process. A launcher stub and the interpreter it
>   spawned both appear in the process table under the same command line.
> - **Drain** — letting the queue empty by running a worker with nothing else changed.

---

## Step 1 — Make the reaper's output readable, because two of today's five diagnosis questions depend on it (15 min) · executable

**This is `P-20`, and it is not polish.** Two facts, both measured on Din 2:

- `post_status = "pending" if matched == 1 else candidate.status` — the row is **never re-read**. That
  field is a restatement of `rowcount`, so the line reports what the code believes.
- A pass with no candidates prints **zero** per-row lines. Over 7 seconds and 3 passes, the only reason
  there was any output at all was `echo=True` in `src/database.py` `[MEASURED-R]`.

**Today's diagnosis question #3 is literally *"did the reaper run inside that window?"*** With the current
output there is no line to read. And a run with `0` duplicates would be indistinguishable from a run where
the reaper never reclaimed anything — which is `P-12`'s exact failure, arriving through the logging layer.

**Two changes, both small:**

1. **The `UPDATE` returns its own result instead of you asserting it.** A `RETURNING` clause can carry more
   than one expression, and one of them can be **the database's own clock**. Think about what that buys you
   before writing it: today's whole experiment is three timestamps subtracted from each other, two of which
   come from process stdout on a different clock. If the reclaim instant arrives from the database, that
   subtraction loses one clock conversion.
2. **Every pass prints one line, including the empty ones** — pass number or timestamp, and the candidate
   count. `0` must print. The reason is stated once and it is the whole point: *an idle reaper and a dead
   reaper must not produce the same stdout.*

**Do not touch** the predicate, the lease duration, or the poll interval. **This step changes reporting, not
behaviour** — and the reason that is allowed today, when the plan freezes the reaper's numbers, is that
Din 2 produced **no** reclaim-latency number to stay comparable with. There is nothing to break
comparability *with*. Write that sentence in the log; it is the justification, and without it this looks
like a tweak.

**End state:** run the reaper for ~6 s against the current database and see per-pass lines with a candidate
count of `0`, and no per-row lines. Then `Ctrl+C` it.

> **Terms used in this step**
> - **`RETURNING`** — a Postgres clause on `INSERT`/`UPDATE`/`DELETE` that sends back values from the rows
>   it touched, in the same round trip.
> - **`clock_timestamp()`** — the real current instant, which advances *within* a statement. Distinct from
>   `now()`, which is transaction-start.

---

## Step 2 — Measure reclaim latency, on a row with a real lease (15 min) · executable

**This is the first time the expiry branch will be evaluated against anything.** Din 2's Part D deferred
seeding a `running` row with a non-null `claimed_at` to today, on purpose, and today is when it pays.

Seed **one** row and put it into a state that has actually expired. Enqueue it normally (so the id is real
and counts in the delta), then move it by hand with `psql`:

```sql
-- id comes from the enqueue; write it down
update jobs
   set status = 'running', claimed_at = now() - interval '25 seconds'
 where id = <seeded id> and status = 'pending';
```

`25 s` against a `30 s` lease means the row is **not yet** reclaimable. That is deliberate: it lets you
watch the boundary get crossed instead of arriving after it.

**Before starting the reaper, record both instants in the database's clock:**

```sql
select id, status, claimed_at,
       claimed_at + interval '30 seconds' as expires_at,
       now() as read_at
  from jobs where id = <seeded id>;
```

Then start the reaper (`python -u`, capture to a file) and let it reclaim the row.

**Output:** `expires_at` (DB clock), the reclaim instant (from Step 1's `RETURNING`, so also DB clock), and
their **difference**. That difference is reclaim latency — the real quantity, the one Din 2 could not
produce.

**Then answer in writing, before Step 3:** is that number bounded by the lease duration, by the poll
interval, or by both? And **which part of it did you measure and which part did you choose?** The poll
interval measured `2.020 s` / `2.013 s` on Din 2, not a flat `2.0 s`, because the sleep happens *after* the
work `[MEASURED-R]`.

**Also record what query (b) does now**, since today it finally has a target:

```sql
select id, status, claimed_at from jobs
 where status = 'running' and claimed_at < now() - interval '30 seconds' order by id;
```

Run it **before** the reaper gets there. Din 2's log says *"the expiry branch matched 0 rows and was not
exercised"*; today that sentence gets replaced by a number, and that replacement belongs in the log
explicitly.

> **Terms used in this step**
> - **Reclaim latency** — the gap between the instant a claim became reclaimable under the predicate and the
>   instant the row actually became `pending`. Not the same as reaper-start-to-`pending`.
> - **Seeded row** — a row put into a known broken state on purpose, so an experiment has a real target.

---

## Step 3 — One decision, written before the run: which variable moves? (10 min)

**With today's numbers the centrepiece is arithmetically impossible.** `handle_slow` sleeps `8.0 s`. The
lease is `30 s`. `8 < 30`, so the lease cannot expire while the handler runs, so the reaper can never
reclaim a live claim, so there is no second execution to observe.

For an overlap to exist, the handler must still be running when the row becomes claimable *and* be running
when worker B picks it up:

```
handler_duration  >  lease_duration + reclaim_latency + claim_delay
                     ^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^   ^^^^^^^^^^^
                     chosen (30 s)    measured in Step 2  ≤ worker poll interval (2.0 s)
```

Exactly one of the two knobs moves today. Both are defensible; the plan has a default and the
counter-argument is real:

| Option | What happens | Cost |
|---|---|---|
| **A — handler gets longer** (plan's default: *"aaj ka variable handler duration hai"*) | A new long handler, or a duration read from `payload`. Needs to exceed `30 + Step 2's number + 2` | Each run costs ~1 minute of wall clock, twice (Run 1 and Run 2). And a `payload`-driven duration is a small API-shape decision arriving in the middle of an experiment |
| **B — lease gets shorter** | Reaper's `LEASE_DURATION_SECONDS` drops so that `8 s` handler > lease + latency | The plan freezes the reaper's numbers so Din 2's reclaim latency stays comparable — **and Din 2 produced no such number**, so this cost is smaller than the plan assumed. But it changes the very number `D-22` will be written about, and then `D-22` is being written about a value that was chosen on Din 2, changed on Din 3, and defended on Din 6 |

**Write the pick, the number, and the reason. Then write the sentence that will be true on Din 6:** which of
these two numbers you will be defending as *chosen* and which as *measured*.

**One thing is not a choice:** whichever you move, **only one moves.** Both Run 1 and Run 2 use identical
handler duration, identical lease, identical poll interval. Run 2's only new variable is the heartbeat.

> **Terms used in this step**
> - **Claim delay** — the gap between a row becoming `pending` and a worker noticing. Bounded above by the
>   worker's `POLL_INTERVAL_SECONDS`, which is `2.0`.

---

## Step 4 — Build the long handler, and prove the lease expires before it returns (15 min) · executable

The handler needs two properties and both are required: **duration greater than the lease** and **staying
alive** — no crash, no exit, no exception. `handle_slow` already prints its start and end lines, and those
two lines are today's most important evidence, because `job_executions` holds exactly **one** timestamp
(`executed_at`) and it can never tell you when a handler **finished**.

And `executed_at` is earlier than you probably think. In `worker.py` the order is:

```
print "Executing job ..."  →  record_execution() [own transaction, COMMITS]  →  handler() → prints "started" ... sleeps ... prints "completed"
```

So `executed_at` is the **dispatch** instant, written and committed *before* the handler body begins, and it
survives a crash. `[MEASURED-R from source]`

**The check that makes this step executable — one job, no reaper, no second worker:**

Start one worker on a single job of the new shape, and while the handler is mid-flight run:

```sql
select id, status, claimed_at, now(),
       claimed_at + interval '30 seconds' as expires_at,
       now() > claimed_at + interval '30 seconds' as is_expired
  from jobs where id = <job>;
```

**You are looking for `is_expired = true` while the handler's "completed" line has not yet appeared.** If
you cannot get that pair, the centrepiece cannot happen and Step 5 is pointless — go back to Step 3 and
move the number further, in **one** direction.

**Output:** the `is_expired = true` row verbatim, the handler's start line, and the absence of the end line
at that moment — with each timestamp labelled with its clock.

> **Terms used in this step**
> - **Alive but slow** — a process that is running normally and simply has not finished. Distinct from a
>   crashed process, and from the outside the two are indistinguishable (Ch 8, *Process Pauses*).

---

## Step 5 — Run 1: the centrepiece, no heartbeat (20 min) · executable

**Three processes, three separate `python -u` captures, three separate files.** Two workers must be two
**processes** — `WORKER_ID = f"worker-{os.getpid()}"`, so two tasks inside one process share a `worker_id`
and the overlap becomes unprovable. Verify with `ParentProcessId` (Step 0), not with a count.

Sequence, and nothing in it is optional:

1. Queue empty (Step 0's decision has been carried out), reaper **not** running, one job of the new shape
   enqueued. Write the id down.
2. **Worker A** starts, claims it, enters the handler.
3. **Reaper** starts. Lease expires. Reaper reclaims → row goes `pending`.
4. **Worker B** starts, claims the *same* job, begins the *same* handler. Worker A is still running.
5. Worker A's handler finishes and it runs its mark statement:
   `UPDATE jobs SET status = ... WHERE id = :id AND status = 'running'`.

**Do not kill worker A to "clean up".** Its mark line is the single most expensive piece of evidence today,
and if the process dies you never get it.

**Output:** all three captures' relevant lines copied into the log, plus:

```sql
select job_id, worker_id, executed_at from job_executions where job_id = <job> order by executed_at;
select id, status, claimed_at, attempts from jobs where id = <job>;
```

`attempts` should still be `0` — it is Din 4's column and nothing today writes it.

> **Terms used in this step**
> - **Overlap** — two handler *intervals* intersecting in time. Two rows in `job_executions` is not overlap;
>   two rows plus intersecting intervals is.

---

## Step 6 — The five-question diagnosis, in order, and the count comes *after* (15 min)

**No count is interpreted until all five are answered in writing.** This is `E3`, and `P-12` exists because
a zero was once read as a result.

| # | Question | How it is answered | If "no", what it means |
|---|---|---|---|
| **1** | Did two workers exist and **overlap**? | Two **different** `worker_id` on the same `job_id`, **and** worker B's `executed_at` falling between worker A's handler start and end lines, all in one clock | Effectively one worker. The run proves nothing and the count is meaningless |
| **2** | Did the lease **actually** expire before the handler returned? | Step 4's `is_expired` pair, and handler duration versus lease duration in one clock | The lease never expired. Reclaim had no opening and a duplicate was impossible |
| **3** | Did the reaper **run** inside that window? | The reaper's per-pass and per-row lines from Step 1, with the reclaim instant | The poll period was larger than the expiry-to-completion gap. Nothing was reclaimed, so nothing could duplicate |
| **4** | Was the row **claimable** after the reclaim? | `select id, status, claimed_at from jobs where id = <job>;` immediately after the reclaim line | Predicate did not match, or the guard rejected. The row never returned to `pending` |
| **5** | Is the log **complete**? | Count `Claimed job` lines in each capture against the expected count, and check the last line is not truncated | Truncated log and genuine zero are the same output (`P-18`). Nothing from this run is interpretable |

**`echo=True` is on, so counting lines by eye will not work.** Grep:

```powershell
Select-String -Path <capture> -Pattern 'Claimed job' | Measure-Object | Select-Object Count
```

**Then, and only then:**

```sql
select job_id, count(*) from job_executions where job_id = <job> group by job_id;
```

**And the decoy you have to name before you read that number.** If Step 0's decision was *drain*, then
jobs 63 and 65 **also** now have two `job_executions` rows each with two different `worker_id` values —
and those are **not** overlaps. They are sequential re-executions separated by a week. So today
`count(*) > 1` appears on rows for **two structurally different reasons**, in the same table, in the same
day. The word *"duplicate"* attaches only to rows whose **overlap** was proved by question 1. Write which
job ids are in which category.

**If all five are "yes" and the count is still `1`:** that is a genuine and interesting result. Record it as
such, with the note that a zero obtained on one schedule is **not** a safety property.

> **Terms used in this step**
> - **Decoy** — a row that produces the same summary statistic as the phenomenon you are looking for, by a
>   different mechanism.

---

## Step 7 — Heartbeat: three decisions, each with its cost, written before it is built (15 min)

**Heartbeat comes now — after the duplicate has been seen, not before.** The reason is in `WEEK_01.md` four
times: a mitigation built before the failure is a mitigation you cannot size.

A heartbeat is a periodic write by the lease holder that pushes the deadline forward. Three decisions:

| Decision | What you are choosing | The cost that must be written |
|---|---|---|
| **Interval** | How often the lease is extended | Must be **smaller** than the lease duration, or the heartbeat arrives after expiry and does nothing. Smaller means more writes — every heartbeat is an `UPDATE`, and the reaper is already polling |
| **Guard** | The heartbeat's `WHERE` | Same compare-and-set discipline: `WHERE id = :id AND status = 'running'`, plus a `rowcount` check (`D-06`, `P-17`). Without it, a heartbeat extends the lease of a row the reaper has **already** made `pending` — and the old worker takes the new claim back |
| **Sender** | What runs alongside the handler | `handle_slow`'s body is `await asyncio.sleep(...)`, so it yields and the heartbeat's own sleep gets scheduled. A **CPU-bound or blocking** handler would never yield, and the heartbeat would not be sent at all. That is precisely where heartbeat **narrows** the window and does **not** close it |

**Write all three plus their costs before writing any code.** They are `D-22`'s raw material and Din 6
copies them.

> **Terms used in this step**
> - **Heartbeat** — a periodic write that renews a lease while work is still in progress.
> - **Yield** — an `await` handing control back to the event loop so other tasks can run.

---

## Step 8 — Run 2: identical setup, heartbeat on, exactly one new variable (20 min) · executable

Same job shape, same handler duration, same lease, same reaper predicate and poll interval, same two-process
layout. **Only the heartbeat is new.**

**The purpose of Run 2 is not to reach zero duplicates.** It is to show the **window got smaller**. So the
number that matters is the same one in both runs: the gap between **lease expiry** and **handler
completion**, in one clock.

**Two checks while the handler is mid-flight, and they must be two separate reads:**

```sql
select id, claimed_at, now() from jobs where id = <job>;   -- run this twice, ~1 heartbeat apart
```

`claimed_at` must have **moved forward** between the two reads. If it has not, the heartbeat is written but
not running, or its guard is rejecting it — and `rowcount` tells you which.

**Output:** both runs' expiry-to-completion gaps side by side, the duplicate count for Run 2 against Run 1,
and the sentence in the right words. **`narrows`. `reduces the window`. Not `fixes`, not `prevents`, not
`no longer possible`** — even if Run 2 produced no duplicate at all. A clean run is not an elimination; it
is one schedule.

---

## Step 9 — Is the heartbeat's guard a real guard? (10 min) · executable

Deliberately invert the order: let the reaper reclaim the row **first**, then let the heartbeat fire on it.

**Output:** the heartbeat's `rowcount` on that write.

- `rowcount = 0` → the guard rejected it. The row was `pending`, the heartbeat did not resurrect a dead
  lease.
- `rowcount = 1` → the heartbeat extended the lease of a row the reaper had already released, and the old
  worker has taken the new claim back. **That is a `PROBLEMS.md` entry, and today's number for it.**

This check is here because Din 2 shipped a guard that was **present and untested** — the `SELECT` had
already filtered the rows the guard was supposed to reject, so the guard was never asked a question it
could answer wrongly (`P-20`). Do not repeat that with the heartbeat.

---

## Step 10 — Reading: Ch 8 *Unreliable Clocks* + *Process Pauses* (15 min)

*Monotonic Versus Time-of-Day Clocks*, then *Process Pauses*. Section names are authoritative; page numbers
in your copy may differ.

**Output:** one-line links appended to `docs/ddia_summaries/DDIA_CH8_LINKS.md`, each right-hand side an
**existing** named `D-`/`P-` entry. `P-02`, `P-11`, `P-13`, `P-15` are natural fits. No new numbers.

**Carried debt, and it is now four lines, not two:** Din 1 owed two and Din 2 owed two, and that file's
mtime is still `2026-08-22 17:28` `[MEASURED-R]` — Stage Day's. **One of Din 2's two must land on `P-02`.**
Note that lines 2 and 3 already cite `pp. 278–284` and `281–283`, so new lines go **past** them rather than
restating them.

---

## Step 11 — Log, reconciliation, cleanup, commit (15 min)

Full shape: goal → goal met (yes/no/partial) → **anything else learned** (separate field) → 📊 Measured →
💡 Understood → 🧠 self-check with an honest score → corrections table → 🚧 Unresolved → ❓ Next thought.

Into the log specifically: **the five diagnosis answers in order, and the count after them**; the chosen
handler duration with its reason; **both runs' expiry-to-completion gap**; Step 2's reclaim latency with the
measured-versus-chosen split; the heartbeat's three decisions with costs; and **worker A's mark statement
verbatim**.

**Reconciliation** — opening counts from **Din 2's log entry**, not the BENCH block:
`3 pending / 0 running / 75 succeeded / 9 failed / 87 total`, `job_executions 58`. Never `max(id)`, never id
contiguity.

Today's delta has **three** sources and they must be listed separately, because merging them makes the
`job_executions` number uninterpretable:

| Source | Effect |
|---|---|
| Step 0's drain (if chosen) | 41/63/65 leave `pending`; `job_executions` `+3` (41's first row, 63's and 65's **second**) |
| Step 2's seeded row | `+1` job; `+1` execution row after the reclaimed row is eventually claimed |
| Steps 5 and 8's centrepiece jobs | `+2` jobs; `job_executions` **more than** `+2`, and that excess is the point |

**`job_executions` delta will exceed the `jobs` delta today, and that is the day's headline** — but
`count(*) > 1` is a **question**, not an answer (`P-11`). Every multi-row job gets its `worker_id` and
`executed_at` written out, and the word *"duplicate"* only where overlap was proved.

**`PROBLEMS.md`** — likely a new entry (candidates: lease expiry cannot stop a worker, only outrun it; or
the heartbeat guard result from Step 9). **Grep for the next free number on the day you assign it.** `P-20`
was taken on Din 2, so `P-21` is the likely one, and the grep still runs:

```powershell
Select-String -Path docs\PROBLEMS.md -Pattern '^## P-'
```

**`DECISIONS.md` gets nothing today.** `D-21`'s amendment and `D-22` are Din 6's. Today's numbers sit in the
log with `[MEASURED]` tags.

**Cleanup, and this has now failed two days running:**

- Delete the three stdout captures **after** copying the relevant lines into the log, and say so.
- **Kill every worker, the reaper, and the heartbeat sender.** Then run the process check **again** and put
  its output in the log. Din 1 left a worker alive; Din 2 left a reaper alive for ~33 minutes. Both times
  the opening check ran and the closing check did not. `idle in transaction = 0` (which `P-06` watches) and
  `processes = 0` (which `P-13` watches) are **two different checks**.
- Probe **rows are not deleted** — ids go into the log by name and count in the delta.

**Commit:** staged paths **by name**, never `.`. Din 2's commit never happened, so today also carries
`src/reaper.py`. `labs/day2_signals.py` is still modified with an mtime of `2026-08-20` — it is not today's
work and not Din 2's either; give it its own commit or revert it.

**One process note for the log:** the plan's per-evening checklist item 13 calls
`python -m tests.plan_lint` *"a gate, not a formality"*. **That module does not exist** — `tests/` holds
only stale `__pycache__` from deleted files `[MEASURED-R]`. So no BRIEF this week has been linted, and the
gate has been passing by not being run. Record it; do not claim it passed.

---

# PART B — PREDICTION QUESTIONS

**Not in this file, on purpose.** `docs/planning/WEEK_02.md`, `PART B — PREDICTION QUESTIONS` block,
`## Din 3` subsection — six questions.

Answer from your own head **before** the relevant step runs. `idk` is a valid written answer and scores as
not-answered, which is accurate.

| Part B question | Answer it before |
|---|---|
| 1 (both claims were legit — so duplicate is a failure of the guard, or of the window?) | Step 5 |
| 2 (`executed_at` is one instant — what is missing for proving overlap, and where does it come from?) | Step 4 |
| 3 (worker A's mark — when `rowcount 0`, and when `rowcount 1` while B does the work?) | Step 5 |
| 4 (heartbeat narrows the window — where does it not help **at all**, and how is that different from `handle_slow`?) | Step 7 |
| 5 (after `running → pending`, what does `count(*) > 1` mean? Name both causes) | Step 6 |
| 6 (in a zero-duplicate run, which of the five was "no" — and what did that say about the setup?) | Step 6 |

---

# PART C — VERIFICATION

**Clock discipline:** `select`s run in the DB session (`Etc/UTC`); worker and reaper stdout are **local
(IST)**. The offset is measured, not assumed: `local − db_utc = 5:29:59.994671`, read gap `7.262 ms`
`[MEASURED-R]`. Label every timestamp with its clock. All three captures use `python -u`.

Each row below was written by asking: *what wrong implementation would also pass this?*

| Check | Command | Mechanism present | Mechanism absent |
|---|---|---|---|
| **Two workers, not two PIDs** | `Get-CimInstance Win32_Process -Filter "Name='python.exe'" \| Select ProcessId, ParentProcessId, ThreadCount` | Two PIDs whose `ParentProcessId` values are **not** each other, and two asyncpg backends in `pg_stat_activity` | Two PIDs where one is the other's parent — that is **one** interpreter and one connection, and Din 1 recorded it as two workers for two days (`M7`) |
| **Two execution rows, two different workers** | `select job_id, worker_id, executed_at from job_executions where job_id = <job> order by executed_at;` | ≥2 rows, ≥2 distinct `worker_id` | One row, or two rows with the **same** `worker_id` — one process claimed twice, or two tasks shared a process. No overlap window existed |
| **Overlap, not just two rows** | Both worker captures' handler start/end lines + the query above, converted to one clock | Worker B's `executed_at` falls **between** worker A's handler start and handler end | B's `executed_at` is **after** A's end — two sequential executions, no concurrent side effect. **Jobs 63 and 65 are exactly this shape today**, so a check that cannot separate them is decorative (`P-12`) |
| **The lease expired before the handler returned** | `select id, claimed_at, now(), now() > claimed_at + interval '30 seconds' as is_expired from jobs where id = <job>;` mid-handler | `is_expired = true` while the handler's "completed" line has **not** appeared | `is_expired = false` right up to completion — the handler was shorter than the lease. **This is today's default state** (`8 s` handler, `30 s` lease), so the check must be run, not assumed |
| **The reaper ran inside the window** | The reaper's `python -u` capture, per-pass lines and the reclaim line | A reclaim line with an instant that sits after expiry and before the handler's end line | **No line at all** — and with Din 2's reaper that is what a correct empty pass, a dead process, and a truncated capture all produce. Step 1 exists to make this row able to fail (`P-20`) |
| **Reclaim latency is a real number** | Step 2's `expires_at` and the reclaim instant, both DB clock | Two instants in the **same** clock and their difference | A difference computed across two clocks by assuming `+5:30`. The offset is measured, but assuming it is exactly what the measurement was for |
| **Expiry branch finally fired** | Step 2's query (b), before the reaper reaches the row | (b) returns the seeded row | (b) returns nothing — the row's `claimed_at` was not set into the past, and the branch is **still** unexercised after three days |
| **Worker A's mark is captured** | Worker A's stdout, its mark line | Either the `rowcount=0` conflict line, or `Marked job ... as 'succeeded'` **while B's handler is still running** — both are results, and which one appeared is the finding | No mark line at all — worker A was killed. The most expensive line of the day, unrecoverable |
| **The heartbeat actually advances the lease** | `select id, claimed_at, now() from jobs where id = <job>;` twice, ~1 heartbeat apart, mid-handler | `claimed_at` **moved forward** between the two reads | `claimed_at` unchanged — written but not running, or its guard is rejecting it. `rowcount` says which. A single read cannot tell these apart |
| **The heartbeat narrowed the window** | Both runs' expiry-to-completion gap, one clock, side by side | Run 2's gap is **smaller** | The two gaps are the same — the heartbeat is doing nothing, and any difference in duplicate count came from something else (`E5`: two variables in one run) |
| **The heartbeat's guard is a real guard** | Step 9: reaper first, then the heartbeat's write | `rowcount = 0` — row was `pending`, guard rejected | `rowcount = 1` — a released lease got extended and the old worker took the claim back. Record it, do not fix it today |
| **75 untouched** | `select id, status from jobs where id = 75;` | `failed` | `pending` or `running` — a terminal row resurrected. `E4`: record it, put it back, **and record the revert** |
| **Log completeness** | `Select-String -Path <capture> -Pattern 'Claimed job' \| Measure-Object` | Count equals expected claims, and the last line of each file is intact | Count low, or a file cut mid-line. Then *"the duplicate did not happen"* and *"the log ended"* are the same output (`P-18`). Do not eyeball this — `echo=True` buries it |
| **Nothing else moved** | `select status, count(*) from jobs group by status;` vs Din 2's close, and `job_executions` count | `job_executions` delta **exceeds** the `jobs` delta, and every multi-row job's extra rows are attributed to a **named** cause (drain / reclaim / retry-none) | Delta matches with no excess — no re-execution happened anywhere. Or the excess is reported as one number, which cannot separate the drain from the centrepiece |

**Two checks deliberately absent.** Anything claiming the duplicate is now prevented — nothing today
prevents it, and Week 3 owns that. And anything claiming the heartbeat interval is *correct* — it was
chosen, and blessing it would be manufacturing confidence.

---

# PART D — SCOPE GUARD

| Tempting | Owner | What you lose by doing it today |
|---|---|---|
| Add an idempotency key — the duplicate is right there and the fix is obvious | **Week 3** | The biggest trap of the week. Living with the duplicate **before** seeing the fix is what makes Week 3's property test a proof instead of paperwork. And Week 2's honest guarantee — *"the reaper narrows the duplicate window, it does not close it"* — stops being worth writing |
| Build the heartbeat first, then try for the duplicate | **order is locked** | Then you never learn what the heartbeat narrowed. Run 1 must be heartbeat-free and its output logged separately |
| Tweak the lease **or** the reaper interval in Run 2 as well | **one variable per run** | Run 2's only new variable is the heartbeat. Move two and the difference belongs to neither |
| Delete 41/63/65 to get a clean queue | **never** | Row deletion breaks the delta arithmetic and destroys `P-05`'s evidence. Drain them or work behind them — those are the two options |
| Re-stick 41/63/65 to `running` to reuse the old fixture | **never** | They were reclaimed on Din 2. Re-sticking is manufactured evidence, and Din 2's pre-reclaim dump is the only surviving record of what they were |
| Lock the final lease duration today | **`D-22`, Din 6** | Its `Cost` needs today's duplicate count **and** Din 5's mid-job shutdown. Choosing today means not being able to defend it later |
| Replace the `status` guard with a fencing token | **Din 5** | Today **measures** the need. Fixing it now turns Din 5's argument from a measurement back into a memory |
| Touch `attempts`, start retry or backoff | **Din 4 (`D-23`)** | Reclaim and retry are two transitions. Run both today and the inter-attempt delay belongs to nobody |
| `dead_letter`, shutdown path changes | **Din 5** | New `status` writers get their own day, with the `ACCESS EXCLUSIVE` window measured |
| Two reapers, so the window is guaranteed to open | **Week 4** | `P-12` inverted — adding a variable to manufacture the window. You would not know which reaper produced which reclaim |
| Turn off `echo=True` because the captures are noisy | **Week 4, with metrics** | It is currently the **only** thing distinguishing a live idle reaper from a dead one. Step 1's per-pass line must exist first |
| Add a `failed_reason` / error column while you are in there | **outside this week** | Today is a transition and a measurement, not a new field |

**Not being built today:** idempotency, dedup, fencing tokens, `attempts`, retry, backoff, jitter,
`dead_letter`, shutdown changes, metrics, indexes, a second reaper. Today produces **one measured reclaim
latency, one reaper output that can be read, one observed duplicate with proved overlap, worker A's mark
statement verbatim, and two expiry-to-completion gaps** — and the overlap proof is the part Week 3 rests on.
