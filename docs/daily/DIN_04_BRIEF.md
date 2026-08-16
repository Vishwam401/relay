# DIN 4 — Two workers, one job: build the instrument, then break the queue

**Week 1 · Layer L1 · Budget ~2h15m** · Plan: [`../planning/WEEK_01.md`](../planning/WEEK_01.md) (DIN 4 section)

> **How to use this file.** Part A + Part C are safe to paste to Gemini, along with
> [`GEMINI_RULES.md`](GEMINI_RULES.md) and the SHARED CONTEXT block from the week plan.
> **Part B is not.** `DIN_04_KEY.md` stays closed until each step's experiment has actually run.
>
> **Order per step:** answer that step's Part B questions from your own head → build → run Part C →
> compare with your prediction and write your own explanation of any difference → *then* open that
> step's KEY section.

---

## Today in one line

Din 3 proved the claim is correct **with one worker**, where "correct" was never tested against a
competitor. Today a second worker arrives, and the first thing you will discover is that the `jobs`
table **cannot tell you whether anything went wrong**. So today's real order is: build the
measurement, then create the failure, then measure it.

---

## Bench state as of right now `[MEASURED by reviewer, 2026-08-16]`

```
jobs: 27 rows — succeeded 21, failed 6, running 0, pending 0
attempts = 0 on every row
max(id) = 27
No index beyond jobs_pkey. No extra columns.
```

Bench is clean: nothing stuck, nothing left mid-flight. **Write down this starting count before
Step 1** — every arithmetic check today is relative to it, and Din 3's log had to reconcile against a
number that had already moved once.

---

## What Din 3 established, because today builds directly on three of its findings

| Din 3 finding | Why it decides something today |
|---|---|
| `LockRows` sits **below** `Limit` in the claim plan `[MEASURED]` | The row is locked *before* `Limit` is satisfied. This is the whole mechanism behind today's Step 3 |
| Claim commits before the handler runs; `state='idle'`, `xact_start NULL` `[MEASURED]` | So a blocked second worker is blocked for **claim duration only**, not handler duration. Predict what that does to throughput |
| The `jobs` table showed nothing wrong when two writers wrote the same value (Week 0 Day 5) | Step 1 exists because of this. You cannot detect double execution from `jobs` |
| `ORDER BY created_at` has **no tiebreak**, and `now()` is per-transaction | Step 0 fixes this *before* seeding, or today's central question becomes unanswerable |

---

# PART A — Steps

Six steps. Each ends in something runnable. If a step passes ~15 minutes, it is too big — split it.

Today you may add **one** table (`job_executions`) and **one** claim-query change (`SKIP LOCKED`,
and only in Step 5). Nothing else. `lease_expires_at`, `locked_by`, retry, `attempts` increments,
`dead_letter` — all still Week 2 (Part D).

---

## Step 0 — Make ordering falsifiable, and pick your seeding method (10 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| Tiebreak | A second `ORDER BY` column that decides when the first column ties |
| `now()` | Transaction timestamp — identical for every row written by one transaction |
| `clock_timestamp()` | Wall clock read at each call, so it differs within one transaction |
| `generate_series(1,10)` | Set-returning function; a single `INSERT ... SELECT` over it writes 10 rows in one statement |

**Do:**
1. Record the starting counts (command in Part C, C0).
2. Decide the claim query's ordering. `ORDER BY created_at` alone has no tiebreak;
   `ORDER BY created_at, id` does. **This is a design judgement — decide it and write the cost.**
   Cost hint to reason about: what does adding `id` to the sort do to `P-03`'s eventual index, and
   what does *not* adding it do to today's conclusions?
3. Decide how you will seed 10 jobs, and write down which you chose:
   - ten separate `INSERT` statements (ten transactions, ten distinct `created_at`), or
   - one `INSERT ... SELECT ... generate_series` (one transaction — think about `created_at`).
4. Write a tiny seed helper you will reuse all day. It must be re-runnable, and it must print the id
   range it created.

**Runnable end state:** you can produce 10 fresh `pending` jobs on demand and state their id range.

---

## Step 1 — Build the instrument before the experiment (20 min)

**You cannot skip this and "just watch the statuses."** Week 0 Day 5's own log: *"dono ne same value
likhi, row bilkul theek dikhi."*

**Terms used in this step**

| Term | What it is |
|---|---|
| Side-effect record | A row written *by the handler*, evidencing that execution actually happened |
| `worker_id` | Something that distinguishes two worker processes in the same output. Din 3 used `worker-<pid>` |
| Append-only table | A table nothing updates or deletes; each row is a fact that happened |

**Do:**
1. New table, via **a new Alembic migration** (not `create_all`): `job_executions`, holding at
   minimum `job_id`, `worker_id`, and an execution timestamp. Decide for yourself: its own `id`?
   A foreign key to `jobs`? Nullable anything? Each is a decision with a cost — write them down.
2. The handler writes one row **every time it runs**. Not the claim. Not the mark. **The handler.**
   Think about where exactly that write goes so that it records execution rather than intent.
3. `alembic downgrade -1` then `upgrade head` must both work. `alembic check` must be clean after.
4. Run one job through the Din 3 worker with one worker only, and confirm exactly one row appears.

**Design judgement — decide and record the cost:**
- Does the execution row get written in the **same transaction** as the terminal mark, or its own?
  One of these can lose the evidence; the other can record an execution that later looks
  contradictory. Name which is which, pick one, and write why.
- Foreign key to `jobs(id)` or not? Consider Week 4 retention deleting old jobs.

**Runnable end state:** one job → exactly one `job_executions` row, and the migration is reversible.

---

## Step 2 — Two workers, no `SKIP LOCKED`, and watch (15 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| `Lock` / `transactionid` | `wait_event` shown when a backend waits for another transaction to end |
| `Lock` / `tuple` | Waiting for a specific row's lock queue position |
| Blocked vs skipped | Two different responses to contention: wait for the row, or move to another |

**Do:**
1. Seed 10 jobs (Step 0's helper). Record the id range.
2. Start **two** workers in two terminals. Tag their output — Din 3's `worker-<pid>` is enough.
3. **Time the whole run.** Start when the second worker is up, stop when both are idle-polling.
4. While it runs, from a third terminal, take at least two `pg_stat_activity` snapshots (Part C, C2).
   You are looking for whether anything is waiting, and on **what**.
5. When both are idle: duplicate check on `job_executions`, plus the status counts.

**Do NOT change the claim query yet.** The contrast is the entire point, and it needs a "before".

**Runnable end state:** 10 jobs terminal, a recorded total time, and a duplicate count that is a
number.

---

## Step 3 — What did the blocked worker get? (15 min)

This is **today's central question** and Din 3 deliberately left it open. Din 3 measured that
`LockRows` sits *below* `Limit` — so the second worker blocks inside a query that has not yet
finished choosing a row.

**Terms used in this step**

| Term | What it is |
|---|---|
| `READ COMMITTED` re-check | When a lock is finally granted, Postgres re-evaluates the row against the query's `WHERE` using the *new* committed version |
| `EvalPlanQual` | The internal name for that re-check |
| Zero-row claim | A claim iteration that returns no job even though jobs exist |

**Do:**
1. Make the blocking window big enough to observe: **temporarily** slow the *claim* side, not the
   handler. Simplest honest way is a second `psql` session acting as worker B's competitor:
   ```sql
   BEGIN;
   SELECT id FROM jobs WHERE status='pending' ORDER BY created_at, id LIMIT 1 FOR UPDATE;
   -- hold here, do not commit yet
   ```
   Then start **one** real worker and watch what it does while that session holds the row.
2. Now commit the `psql` session *after* setting the row to a non-`pending` status by hand, and
   separately try it committing *without* changing the status. **These two cases have different
   answers** — run both, record both.
3. Record, for each case: did the worker claim that row, a different row, or nothing? What was its
   `rowcount`? Did it log a conflict?

**Runnable end state:** two recorded outcomes, one per case, in the worker's own log lines.

---

## Step 4 — Force the duplicate, and prove you can see it (15 min)

Din 3 concluded the engine is currently **at-most-once** on worker death (`P-09`), because nothing
puts a job back. Two workers is one of exactly two routes to a second execution. Find out whether
`FOR UPDATE` alone actually produces it.

**Do:**
1. From Step 2's run: `SELECT job_id, count(*) FROM job_executions GROUP BY job_id HAVING count(*) > 1;`
2. If the count is zero, **do not conclude "no duplicates are possible"**. Your instrument has to be
   proven capable of showing one. So produce a duplicate deliberately — the honest way is to run the
   *same job* through the handler path twice by hand (e.g. reset one row to `pending` after it
   finished, with a `psql` `UPDATE`, and let a worker pick it up again).
3. Confirm the query above now returns that row with `count = 2`, then record both facts:
   *natural duplicates observed = N*, *instrument can detect duplicates = yes/no*.

> This is the Din 2 `413` discipline applied to a measurement rather than a check: an instrument that
> has never shown a positive is not yet known to work.

**Runnable end state:** the duplicate-detection query returns a row, because you made one.

---

## Step 5 — Add `SKIP LOCKED` and re-run identically (15 min)

**One variable.** Same seed count, same two workers, same timing method, same snapshots. The only
change is `SKIP LOCKED` on the claim query.

**Do:**
1. Reset the bench: fresh 10 jobs (and record the range). Do **not** delete `job_executions` history
   unless you write down that you did and why — arithmetic depends on it.
2. Add `SKIP LOCKED`. Nothing else changes.
3. Same run, same timing, same snapshots, same duplicate check.
4. Fill in C5's comparison table with real numbers in every cell.

**Runnable end state:** two runs you can put side by side, differing in one variable.

---

## Step 6 — Read prefetch, and answer the question it raises about your own worker (20 min)

**Do:**
1. Read the RabbitMQ **prefetch** docs. Write one line each: (a) what prefetch actually limits,
   (b) what happens to a consumer's prefetched-but-unacked messages when it dies, (c) why a large
   prefetch can make a *fast* consumer slower for everyone else.
2. Then answer, about **your** worker: it claims exactly one job at a time. Name one thing that gets
   worse if it claimed five, and one thing that gets better. `[This is Week 4's throughput question —
   note it, do not build it.]`

**Runnable end state:** three lines and one trade-off, in your own words, in the log.

---

# PART B — Prediction questions

> ⛔ **DO NOT PASTE THIS SECTION TO GEMINI. DO NOT OPEN THE KEY TO ANSWER IT.**
>
> Answer each step's questions **before** writing that step's code, from your own head, in writing.
> `idk` is a legitimate answer and is recorded as one.
>
> Vocabulary questions are fine to ask Gemini — the glossaries in Part A exist for that. If knowing
> the answer to your question would also answer one of these, do not ask it.

```
STEP 0 — ordering
0.1  You seed 10 jobs with ONE INSERT ... SELECT generate_series statement. What will the 10
     created_at values look like relative to each other, and why?
0.2  With ORDER BY created_at and no tiebreak, and all 10 rows tied: which row does LIMIT 1
     return? Is that answer stable across two runs of the same query?
0.3  Does adding `id` to the ORDER BY change what index P-03 would eventually need? Yes/no and why.

STEP 1 — the instrument
1.1  The handler writes its job_executions row, then the mark UPDATE fails (DB restarted).
     What does job_executions say, what does jobs say, and which one is telling the truth?
1.2  If the execution row is written in the SAME transaction as the terminal mark, name the
     scenario where the evidence of an execution is lost entirely.
1.3  You add a foreign key job_executions.job_id -> jobs(id). Week 4 wants to delete jobs older
     than 30 days. What breaks, and what are your two options at that moment?
1.4  Why can `jobs` alone never show a double execution? Answer in terms of what UPDATE does,
     not in terms of what you would like to see.

STEP 2 — two workers, FOR UPDATE only
2.1  Both workers poll at the same moment, 10 pending jobs. Do they claim different jobs, the
     same job, or does one block? State the mechanism, not the hope.
2.2  If one blocks: for how long is it blocked — claim duration, or handler duration? Which
     Din 3 measurement decides your answer?
2.3  Predict wait_event_type / wait_event for the blocked worker, if any.
2.4  10 jobs, 2 workers, handler = 2 s each. Predict total wall-clock time. Show the arithmetic
     you used, because the arithmetic is what gets scored, not the number.
2.5  Predict the duplicate count in job_executions. Then state what result would make you
     believe your instrument is broken rather than that there were no duplicates.

STEP 3 — the blocked claim
3.1  Session X holds `SELECT ... LIMIT 1 FOR UPDATE` on job 5 and does NOT commit. Your worker
     starts. What does the worker's claim statement do — return job 6, block, or return nothing?
3.2  X now sets job 5 to 'running' by hand and commits. The blocked worker wakes up. Does it get
     job 5, a different job, or zero rows? What is its rowcount, and does your conflict branch fire?
3.3  Same, but X commits WITHOUT changing the status (job 5 still 'pending'). Same three questions.
3.4  Are 3.2 and 3.3 the same answer? If not, name the mechanism that separates them.
3.5  Your worker's loop treats "no job found" as "queue empty, sleep the poll interval". Under
     contention, is that the right response? What is the cost, in throughput terms?

STEP 4 — duplicates
4.1  Before running it: can FOR UPDATE (no SKIP LOCKED) with a compare-and-set guard produce a
     genuine double execution today? Yes/no, and name the step in claim->execute->mark where the
     two workers would have to interleave for it to happen.
4.2  If your answer to 4.1 is "no", then what exactly is Din 4 measuring? Write that down before
     you run anything — it is the honest version of today's goal.
4.3  You reset a finished job to 'pending' by hand to force a duplicate. Which contract point does
     that hand-edit simulate, and which week owns doing it automatically?

STEP 5 — SKIP LOCKED
5.1  Predict duplicate count with SKIP LOCKED. Same or different from Step 2? Why?
5.2  Predict total time with SKIP LOCKED vs without. Which is faster, and by roughly what factor?
     Show the arithmetic.
5.3  Predict what pg_stat_activity looks like now. Which row from the Step 2 snapshot disappears?
5.4  SKIP LOCKED skips locked rows. Name a situation where skipping is the WRONG behaviour and
     blocking would have been correct. (There is one — it is not a job queue.)
5.5  With SKIP LOCKED, can two workers still end up executing the same job? If yes, by what route?

STEP 6 — prefetch
6.1  Your worker claims one job at a time. If it claimed five, what happens to those five when it
     is killed mid-batch? Answer using Din 3's P-09 reasoning.
6.2  Which is worse at 2 workers and 1000 queued jobs: claiming 1 at a time, or claiming 50?
     Name the cost on each side.
```

---

# PART C — Verification

Each check is written to **distinguish** a working implementation from a plausible broken one. For
every check ask the Din 2 question: *what wrong implementation would also pass this?*

Environment: PowerShell, repo root, `.venv` active. Statement separator is `;`, never `&&`.
Two worker terminals, one `psql` terminal, API only if you enqueue over HTTP.

> **Windows note, learned the hard way on Din 3:** a worker started in a foreground shell blocks that
> shell until `Ctrl+C`. Give each worker its **own terminal**, and keep a third free for `psql`.

---

### C0 — Starting state (1 min)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT max(id) FROM jobs;"
```

Write both numbers down. Reviewer's reading at hand-off: 21 `succeeded`, 6 `failed`, `max(id) = 27`.

---

### C1 — The instrument records executions, not intentions (Step 1)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "\d job_executions"
docker compose exec -T db psql -U postgres -d relay -c "SELECT * FROM job_executions ORDER BY id DESC LIMIT 5;"
```

One job through one worker must produce **exactly one** row.

| Would also pass "a row appeared" | Caught by |
|---|---|
| Row written at **claim** time, not execution time | Kill the worker mid-handler: a claim-time row exists for work that never finished. Run it and record |
| Row written at **mark** time | Same kill test: no row at all, despite the handler having run |
| Row written twice per execution (once per retry of the same code path) | Count must be exactly 1 for a clean single run |

**Also required:** `alembic downgrade -1`, `alembic upgrade head`, `alembic check` → clean. Din 1's
leftover-tables lesson: a red `alembic check` is a diagnostic you will learn to ignore.

---

### C2 — Two workers without `SKIP LOCKED`, observed while it happens (Step 2)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT pid, state, wait_event_type, wait_event, xact_start IS NOT NULL AS has_xact, left(query,60) AS q FROM pg_stat_activity WHERE datname='relay' ORDER BY pid;"
```

Take it **at least twice** during the run. Record every row verbatim, and be able to say which PID is
which worker — Din 3's Step 5 established that a snapshot you cannot attribute proves nothing.

Then:

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT job_id, count(*) FROM job_executions GROUP BY job_id HAVING count(*) > 1;" -c "SELECT worker_id, count(*) FROM job_executions GROUP BY worker_id ORDER BY worker_id;"
```

The third query is the one that makes "two workers actually shared the work" checkable. A single
worker doing all ten would satisfy the first two queries completely.

---

### C3 — The blocked claim, both cases (Step 3)

Both rows must be real output from your worker's log, including `rowcount`:

| Case | Row the worker got | `rowcount` | Conflict branch fired? |
|---|---|---|---|
| X commits **after** changing job 5 to `running` | | | |
| X commits **without** changing job 5 | | | |

If both cases give the same answer, say so — that is a finding, not a failure. If your worker
returned zero rows in either case, record what it did next and how long it waited.

---

### C4 — The duplicate detector is proven capable (Step 4)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT job_id, count(*) AS executions FROM job_executions GROUP BY job_id HAVING count(*) > 1;"
```

Record **two separate numbers**, and do not merge them:

- natural duplicates from the Step 2 run: `N = ?`
- duplicates after deliberately forcing one: must be `>= 1`, or the instrument is not trusted

A zero in the first line with no successful forced duplicate means the conclusion is
**"not established"** — not "no duplicates occur".

---

### C5 — The `SKIP LOCKED` contrast, one variable (Step 5)

| | Without `SKIP LOCKED` | With `SKIP LOCKED` |
|---|---|---|
| Jobs seeded | 10 | 10 |
| Total wall-clock time | | |
| Duplicate executions (`job_executions`) | | |
| Executions per `worker_id` (split) | | |
| `wait_event_type` / `wait_event` seen | | |
| Zero-row claims logged | | |

Fill every cell from real output. If the two time figures are within noise of each other, **say
that** rather than reporting a factor — one run each is not a throughput measurement, and Din 2's
"~11 ms unexplained" is the standing reminder of what happens when a number is quoted past what it
can support.

---

### C6 — Day-close state (2 min)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT count(*) FROM jobs WHERE status='running';" -c "SELECT count(*) FROM jobs WHERE attempts <> 0;" -c "SELECT count(*) FROM job_executions;"
```

Reconcile the arithmetic against C0 explicitly: *start + seeded = terminal + still-pending*. If it
does not close, write that it does not close. Anything left in `running` needs a named reason —
tomorrow's experiment is exactly that, so a stuck row today is a *finding*, not a mess to tidy.

---

# PART D — Scope guard

**Not today. Each one has an owner.**

| Tempting | Owner | What you lose by building it now |
|---|---|---|
| Lease, `lease_expires_at`, `locked_by`, heartbeat, reaper | **Week 2** | Din 5 must first show you a job stuck forever. Building the fix before seeing the failure is copying a solution |
| Retry, backoff, incrementing `attempts`, `dead_letter` | **Week 2** | Same. `attempts` stays `0` all day — if you increment it, that is a decision to write down |
| Idempotency key, dedup, payload hashing | **Week 3** | `P-07`. Today's job is to *see* duplication, not to prevent it |
| Making the claim query claim N jobs at once (prefetch) | **Week 4** | Step 6 reads about it deliberately without building it. It changes throughput *and* crash blast radius at the same time — two variables |
| Index on the claim query | **Week 4** | `P-03`. Today's `Seq Scan` at 30-ish rows is not evidence either way |
| Throughput conclusions from one run each | **Week 4** | One run is not a measurement. Record the numbers, resist the factor |
| `LISTEN` / `NOTIFY` to remove polling | Month 2+ | `P-10` records why it does not remove the sweep |
| Tests in `tests/` | Not Week 1 | |
| Turning `echo=False` | — | The SQL log is again today's primary evidence (C2, C3) |

**Specifically: when Step 4's duplicate count comes back `0`, the temptation is to conclude the
design is safe.** It is not safe; it is **unrecoverable**, which is a different thing (`P-09`). Write
that sentence in the log and leave the gap open — Din 5 is what turns it from an argument into a
sight.

---

## What the day should produce for the log

- C0 and C6 counts, with the arithmetic written out.
- The `job_executions` schema decisions: transaction placement, FK or not, each with its cost.
- C2's `pg_stat_activity` rows verbatim, with each PID attributed to a worker.
- C3's two-case table — today's central finding.
- Both duplicate numbers from C4: natural, and forced-to-prove-the-instrument.
- C5's table, every cell, plus an explicit note if the time difference is inside noise.
- The per-`worker_id` execution split for both runs.
- One sentence, your own words: *what did `SKIP LOCKED` solve that `FOR UPDATE` could not, and what
  did it not solve?*
- Every question you answered `idk`. Those are the day's real output.
