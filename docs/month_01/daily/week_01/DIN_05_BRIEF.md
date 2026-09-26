# DIN 5 — `kill -9` mid-job: make a job disappear, then prove nobody can find it

**Week 1 · Layer L1 · Budget ~2h15m** · Plan: [`../planning/WEEK_01.md`](../../planning/WEEK_01.md) (DIN 5 section)

> **How to use this file.** Part A + Part C are safe to paste to Gemini, along with
> [`GEMINI_RULES.md`](../../../daily/GEMINI_RULES.md) and the SHARED CONTEXT block from the week plan.
> **Part B is not.** `DIN_05_KEY.md` stays closed until each step's experiment has actually run.
>
> **Order per step:** answer that step's Part B questions from your own head → build → run Part C →
> compare with your prediction and write your *own* explanation of any difference → *then* open that
> step's KEY section. `idk` is a legitimate answer and is recorded as one.

---

## Today in one line

Din 4 built an instrument and made a duplicate on purpose. Today you make the **opposite** failure:
a job that started and never finished, with nothing in the system able to notice. And the goal is
not to fix it — it is to find out **exactly what evidence the stuck job leaves behind**, because
that evidence is the only thing Week 2's reaper will have to work with.

---

## Bench state as of right now `[MEASURED by reviewer, 2026-08-17, after Din 4 close]`

```
jobs: 58 rows — succeeded 49, failed 8, running 1, pending 0
  running = job 41  (stuck since ~19:25 on Din 4, by a lock probe, not a crash)
attempts = 0 on every row
max(id) = 58

job_executions: 30 rows, max(id) = 30, next insert will get id 32 (31 consumed by a probe)
  one duplicate pair: job 44 has 2 rows
  jobs 55-58 are reviewer probe jobs, deliberately not deleted

worker processes running: 0    connections to relay: 1 (psql only)
```

**Two things to carry from this block into today's arithmetic:**

1. **The stuck-job baseline is `1`, not `0`.** Every "how many jobs are stuck?" count today must
   subtract job 41, or you will report a Din 4 artifact as a Din 5 result.
2. **Start from zero worker processes.** Din 4 lost a measurement to four forgotten workers that
   were still claiming jobs 38 minutes later (`P-13`). Check the process count before *and* after
   every step today — the command is in C0.

---

## What Din 4 established, because today leans on four of its findings

| Din 4 finding | Why it decides something today |
|---|---|
| `job_executions` is written **after the claim commits and before the handler runs** `[MEASURED]` | So a job killed mid-handler will already have its execution row. That is the evidence you are here to inspect |
| An unregistered `type` leaves **no** execution row; a raising handler leaves one `[MEASURED]` | The table means "a handler was entered", not "claimed". Do not read it as a claim log (`P-11`) |
| Job 41 sat in `running` for over an hour with nothing able to move it `[MEASURED]` | The stuck row does not need a crash. Any path that commits `running` and then stops produces it. Today's `kill -9` is one such path, not the only one |
| Both "two worker" runs had a **staggered** second worker, so the contention was mostly fake (`P-12`) | Step 5 starts all three workers from **one command** and reports the overlap window, not just the split |

And one Week 0 finding that decides how today's kills are done:

> **Windows signal reality** — `Stop-Process -Force` / `taskkill /F` terminate the process with **no
> handler run**; that is your `kill -9`. A catchable `SIGTERM` **cannot be delivered natively on
> Windows**; the graceful path is reached by **`Ctrl+C` in the worker's own console** (`SIGINT`), and
> possibly `Ctrl+Break` (`SIGBREAK` is registered now, never tested).

---

# PART A — Steps

Seven steps. Each ends in something runnable. If a step passes ~15 minutes, it is too big — split it.

Today you may add **one handler** (a slow one) and **nothing else**. No `lease_expires_at`, no
`claimed_at`, no reaper, no retry, no `attempts` increment. Part D lists the owners.

---

## Step 0 — Clean bench, and make "stuck" countable (10 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| Baseline | The count a result is measured *against*; a result without one is unreadable |
| Orphan process | A process still running after the run it belonged to ended |
| `pg_stat_activity` | One row per Postgres connection: state, current query, what it is waiting on |

**Do:**
1. Run C0. Write down: worker process count, `relay` connection count, status counts, `max(id)`.
2. Confirm the worker process count is `0` before you start. If it is not, kill them and say so in
   the log — that is data, not an inconvenience.
3. Write down, as one sentence, the query you will use to count stuck jobs today, **and what it
   returns right now.** (It should return 1: job 41.)

**Runnable end state:** a written baseline, and one command that answers "how many jobs are stuck?"

---

## Step 1 — A handler you can actually catch in the act (10 min)

Today's `sleep` handler runs 2 s. Killing a process inside a 2 s window while also reading its output
is a coin flip, and a missed kill will look like a result.

**Do:**
1. Add **one** handler to the registry — a slow one, ~8–10 s, that prints when it starts and prints
   again when it finishes. Two prints, not one: the first is "work started", the second is
   "work completed", and today's whole point is the gap between them.
2. Seed one job of that type, run one worker, and let it finish normally. Confirm: both prints
   appeared, `jobs.status = 'succeeded'`, exactly one `job_executions` row.
3. Note the id it got, and note that this is your **control run** — the same job type, not killed.

**Design judgement — decide and record:** the "finished" evidence is currently only a `print`, i.e.
it lives in a terminal and dies with it. Would you rather it were a row in a table? Name what that
would buy and what it would cost (hint: `D-21` argued the same question for the *start* evidence).

**Runnable end state:** a job type that takes long enough to interrupt, with a clean control run.

---

## Step 2 — `kill -9` mid-job, and snapshot immediately (15 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| `SIGKILL`-equivalent on Windows | `Stop-Process -Force` / `taskkill /F` — the process is terminated by the OS; no Python code runs |
| Buffered stdout | Python buffers output when it is redirected to a file; buffered bytes are lost if the process is killed |

**Do:**
1. One worker, its own terminal. Seed one slow job. Wait for the "work started" print.
2. Kill it hard: `Stop-Process -Id <pid> -Force`. Note the clock time.
3. Immediately snapshot (C2): the job's `status`, its `job_executions` row(s), and
   `pg_stat_activity` for `relay`.
4. Answer from the snapshot, in the log: **which of the two prints from Step 1 appeared, and which
   record exists?** That pair is the definition of a stuck job.

**Runnable end state:** one row in `running` that no process owns, with its execution row present and
its completion evidence absent.

---

## Step 3 — Wait, then prove nothing recovers it (15 min)

A snapshot taken one second after the kill cannot distinguish "stuck forever" from "recovers in a
moment". Two checks, and the second is the one that matters.

**Do:**
1. Re-run the stuck-count query at **+1 minute** and **+5 minutes**. Record all three readings
   (immediately, +1, +5) even though you expect them identical — an unchanging number is the result.
2. Now start a **fresh** worker and let it poll for ~30 s. Does it take the stuck job?
3. Explain **in one line, from the claim query**, why it does or does not. Not from what you hope.
4. Check `pg_stat_activity`: is there any trace left of the killed worker's connection?

**Runnable end state:** three identical stuck counts, plus a fresh worker that demonstrably ignores
the row, plus one sentence naming the reason.

---

## Step 4 — The graceful contrast, and finally record the shutdown numbers (20 min)

Din 3's checklist asked for exit code and elapsed shutdown time, twice, and **both were never
recorded** — it is still an open item in `LEARNING_LOG.md`. Close it today.

**Do, mid-job:**
1. One worker in its own terminal, seed one slow job, wait for "work started".
2. Press **`Ctrl+C`** once. Do not press it again — pressing twice measures a different thing, and
   if you do press twice, record that you did.
3. Record: did the handler finish? Final `status`? Exit code (`$LASTEXITCODE`)? And **elapsed time
   from the keypress to the process exiting** — method in C4, and report the resolution of your
   method, not a falsely precise number.
4. Stuck jobs afterwards: still just the baseline?

**Do, idle:**
5. Same worker, empty queue, press `Ctrl+C` while it is sleeping between polls. Record elapsed time
   and exit code again. This is `P-10`'s claim — *"the flag is observed up to one poll interval
   late"* — which is currently **inference from code**, not measurement.

**Runnable end state:** four recorded numbers (mid-job: exit code + elapsed; idle: exit code +
elapsed), and a note on how you timed them.

---

## Step 5 — Three workers, one killed, and this time prove they overlapped (20 min)

This step also repays Din 4's debt: its two-worker runs never really overlapped (`P-12`), so nothing
there is usable as a contention result.

**Do:**
1. Seed 9 slow jobs.
2. Start **three** workers from **one command** so their start times are within milliseconds, and
   capture each PID with its start time (C5 has the command).
3. While the first round is running, `Stop-Process -Force` **one** of them. Note which PID.
4. Let the other two drain the queue, then stop them gracefully.
5. Report, and this is the part Din 4 got wrong:
   - jobs per worker, **and** the overlap window (first-to-last worker start, and the time span in
     which more than one worker was executing — `job_executions.executed_at` gives you this);
   - duplicate count over the 9 jobs;
   - **stuck count, minus the baseline.**

**Runnable end state:** a table with jobs-per-worker, an overlap window in seconds, a duplicate
count, and a stuck count you can defend.

---

## Step 6 — Write the Week 2 problem statement, in your own words (15 min)

**Do:** answer these four in the log, in your own words, no more than three lines each.

1. What exactly is lost when a worker dies mid-job? Name the record, not the vibe.
2. Who can bring the job back, and why can it not be the worker itself, or Postgres?
3. Whatever brings it back must decide *"is this worker dead, or just slow?"* — **on what
   information?** List what the database can currently tell it. Be specific about what is missing.
4. If it guesses wrong — the worker is alive and merely slow, and the job is reset to `pending` —
   what does Relay's contract say has happened? Which contract point breaks, and which one is
   protected?

Then read **DDIA Ch 7, second pass, finish it** (pp. 233–251) and write one line on which of today's
observations the chapter names.

**Runnable end state:** four written answers, and the sentence Week 2 starts from.

---

# PART B — Prediction questions

> ⛔ **DO NOT PASTE THIS SECTION TO GEMINI. DO NOT OPEN THE KEY TO ANSWER IT.**
>
> Answer each step's questions **before** running that step, from your own head, in writing.
> Vocabulary questions are fine to ask Gemini — the glossaries in Part A exist for that. If the
> answer to your question would also answer one of these, do not ask it.

```
STEP 0 — baseline
0.1  Job 41 has been 'running' since yesterday. Name every mechanism in the repository today
     that could change its status. If the list is empty, say so and say what that implies.
0.2  Why does the stuck count need a baseline at all? What wrong conclusion does its absence allow?

STEP 1 — the slow handler
1.1  Your handler prints "started", sleeps 8 s, prints "finished". A worker is killed at t=4 s.
     Which prints exist, and where do those prints physically live?
1.2  If the worker's output was redirected to a file instead of a console, would your answer to
     1.1 change? Why or why not?
1.3  The execution row is written before the handler is entered. Name one thing that row proves
     and one thing it does NOT prove.

STEP 2 — kill -9
2.1  Immediately after the kill: what is the job's status, and why is it that value rather than
     'pending' or 'failed'? Answer in terms of what was committed and when.
2.2  The worker's DB connection died with the process. Postgres notices quickly (Week 0 Day 3).
     Does that roll anything back? What transaction was open at the moment of death?
2.3  Is there a row in job_executions for the killed job? Predict yes/no and give the reason from
     code, not from preference.
2.4  Name one crash timing where NO execution row would exist even though the job is 'running'.
     How wide is that window, roughly?

STEP 3 — recovery
3.1  Five minutes later, has anything changed? Which component would have had to act?
3.2  A fresh worker polls. Does it claim the stuck job? Quote the part of the claim query that
     decides it.
3.3  If you wanted a worker to pick that job up again, what is the minimum change to the row —
     and what would that change break if a second worker is still alive and running it?
3.4  What in pg_stat_activity distinguishes "worker died" from "worker is slow"? Answer honestly.

STEP 4 — graceful
4.1  Ctrl+C mid-job: does the current handler run to completion, or is it cut off? Which line of
     run_worker() decides that?
4.2  Predict the exit code, and say which line produces it.
4.3  Predict elapsed time from keypress to exit, mid-job. Show the arithmetic.
4.4  Same, but idle. Different number? Which single line of code sets the upper bound?
4.5  Any job left in 'running' after a graceful stop? Why or why not?
4.6  Would a second Ctrl+C, pressed while the handler is still running, be better or worse for
     Relay's contract? Which contract point does your answer trade away?

STEP 5 — scale
5.1  9 jobs, 3 workers, 8 s handler, one worker killed during the first round. Predict: stuck
     jobs (excluding baseline), total wall-clock, duplicate count. Show the arithmetic.
5.2  Predict stuck jobs if the worker claimed 5 jobs at a time instead of 1. Same arithmetic,
     one variable changed. (Din 4 Step 6's prefetch question, now with a number.)
5.3  Two workers claim within milliseconds of each other. Which Din 4 measurement tells you
     whether that produces a duplicate?
5.4  What result from this step would make you believe the experiment was broken rather than
     that the code is correct?

STEP 6 — Week 2
6.1  Write the reaper's decision rule as a single SQL predicate, using only columns that exist
     in `jobs` today. Then state why it does not work.
6.2  What is the smallest schema addition that makes it work, and what new failure does that
     addition introduce?
```

---

# PART C — Verification

Every check below is written to **distinguish** a working system from a plausible broken one. For
each, ask the Din 2 question: *what wrong implementation would also pass this?*

Environment: PowerShell, repo root, `.venv` active. Statement separator is `;`, never `&&`.
Give each worker its own terminal and keep one terminal free for `psql`.

> **Clock trap, and it already cost the reviewer time on Din 4.** `[MEASURED]` the database session's
> `TimeZone` is **`Etc/UTC`**, so every `executed_at` printed by `psql` is UTC, while the worker's
> `echo=True` log lines are **local (IST, +5:30)**. Comparing the two directly makes a kill look like
> it happened five and a half hours before the job started. Either convert
> (`executed_at AT TIME ZONE 'Asia/Kolkata'`) or stay inside one clock for a given calculation — and
> write down which clock each number is in.

---

### C0 — Baseline, including processes (2 min)

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*src.worker*' } | Select-Object ProcessId, CreationDate
docker compose exec -T db psql -U postgres -d relay -c "SELECT count(*) AS conns, count(*) FILTER (WHERE state LIKE 'idle in transaction%') AS idle_in_txn FROM pg_stat_activity WHERE datname='relay';" -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT max(id) FROM jobs;" -c "SELECT count(*) FROM job_executions;"
```

Expected right now `[MEASURED 2026-08-18]`: **0** worker processes, **1** connection (your `psql`),
**0** `idle in transaction`, `running = 1` (job 41), `max(id) = 58`, 30 execution rows.

> The `idle_in_txn` column is there for a reason: `idle_in_transaction_session_timeout` on this
> instance is **`0`**, i.e. unlimited `[MEASURED]`. If any probe session today is left mid-transaction,
> Postgres will never clean it up and `P-06` repeats — that entry is four abandoned sessions blocking
> a `DROP TABLE` for days.

| Would also pass "the bench looks fine" | Caught by |
|---|---|
| A forgotten worker still claiming jobs | The process list. Din 4 lost a measurement to exactly this (`P-13`) |
| A stuck job left from yesterday counted as today's result | `running = 1` recorded *before* anything runs |

---

### C1 — Control run: the slow handler completes (Step 1)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "INSERT INTO jobs (type) VALUES ('<your-slow-type>') RETURNING id;"
```

Then one worker, and afterwards:

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT id, status FROM jobs WHERE id = <id>;" -c "SELECT job_id, worker_id, executed_at FROM job_executions WHERE job_id = <id>;"
```

Required: both prints in the terminal, `status = 'succeeded'`, **exactly one** execution row.

| Would also pass "it worked" | Caught by |
|---|---|
| A handler that returns instantly (so nothing can be interrupted later) | Time it. It must actually take ~8–10 s |
| A handler that prints "finished" before doing the work | Read your own two prints against the sleep |

---

### C2 — Immediately after `kill -9` (Step 2)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT id, status, created_at, attempts FROM jobs WHERE status='running' ORDER BY id;" -c "SELECT job_id, worker_id, executed_at FROM job_executions ORDER BY id DESC LIMIT 3;" -c "SELECT pid, state, wait_event_type, wait_event, xact_start FROM pg_stat_activity WHERE datname='relay';"
```

Required: the killed job is `running`, has an execution row, `attempts = 0`, and **no** connection
belonging to the dead worker remains.

| Would also pass "the job is stuck" | Caught by |
|---|---|
| The job was never claimed at all (so `running` is someone else's row) | Match the `id` against the execution row's `job_id` **and** its `worker_id` against the killed PID |
| The handler had already finished and only the mark was lost | Your two prints: "finished" must be **absent**. This is the differential — same DB state, different truth |
| Postgres rolled the claim back when the connection died | The row would be `pending`. If it is `running`, nothing was rolled back — say why |

---

### C3 — Nothing recovers it (Step 3)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT count(*) AS stuck FROM jobs WHERE status='running';"
```

Run at +0, +1 min, +5 min. Then start a fresh worker for ~30 s and run it again.

| Would also pass "nothing recovers it" | Caught by |
|---|---|
| Nobody was polling, so of course nothing changed | The fresh worker must be **running and visibly polling** for the last reading |
| The stuck job is invisible because of a `WHERE` typo in your count | Count `status='running'` with no other predicate, and list the ids |

---

### C4 — Graceful shutdown, with numbers (Step 4)

Timing method, in order of preference — **report which one you used**:

1. `echo=True` stamps every SQL line with `HH:MM:SS,mmm`. The last poll `COMMIT` before your
   keypress and the final line after it bracket the elapsed time to within one poll. Resolution:
   coarse, honest.
2. Start a stopwatch in a second terminal at the keypress:
   `$sw=[Diagnostics.Stopwatch]::StartNew()` … then `$sw.Elapsed` when the process exits.
3. Exit code, after the process has exited, in its own terminal: `$LASTEXITCODE`.

Required rows in the log:

| Case | Handler finished? | Final status | Exit code | Elapsed | Stuck jobs |
|---|---|---|---|---|---|
| `Ctrl+C` mid-job | | | | | |
| `Ctrl+C` idle | — | — | | | |
| `Stop-Process -Force` mid-job (from Step 2) | | | | n/a | |

| Would also pass "graceful shutdown works" | Caught by |
|---|---|
| The worker exited immediately and abandoned the running job | Final status must be `succeeded`, and the "finished" print must exist |
| Elapsed time reported as a round number that was never measured | State the method and its resolution. "Not recorded" is a better entry than a plausible number |

---

### C5 — Three workers, proven overlap (Step 5)

Start them together, and capture start times in the same breath:

```powershell
1..3 | ForEach-Object { Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-u","-m","src.worker" -PassThru | Select-Object Id, StartTime }
```

> `-u` matters **only if you redirect output to a file**, and then it matters a lot. `[MEASURED
> 2026-08-18]`: a script that printed `started`, slept 6 s, and was force-killed at t=2 s left a
> **0-byte** file without `-u` and a **9-byte** file (`started`) with it. Redirected stdout is
> block-buffered, so the kill discards the evidence you are relying on. With `Start-Process` and no
> redirect each worker gets its own console (line-buffered), so `-u` is harmless there — keep it
> anyway, because the day you redirect is the day you forget.
>
> `-PassThru` gives `.StartTime` with millisecond precision. `[MEASURED]` two workers launched
> back-to-back this way started **57.8 ms apart** — against Din 4's accidental 10 s and 23 s. Record
> both start times; that pair is what makes the split interpretable.

Afterwards:

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT worker_id, count(*), min(executed_at), max(executed_at) FROM job_executions WHERE job_id >= <first_seeded_id> GROUP BY worker_id ORDER BY min(executed_at);" -c "SELECT job_id, count(*) FROM job_executions WHERE job_id >= <first_seeded_id> GROUP BY job_id HAVING count(*) > 1;" -c "SELECT count(*) AS stuck FROM jobs WHERE status='running';"
```

| Would also pass "three workers competed" | Caught by |
|---|---|
| One worker did almost everything while the others started late (**Din 4's actual failure**) | The `min/max(executed_at)` per worker — compute the window where more than one was executing, and report it in seconds |
| "0 duplicates" from a run with no real contention | A duplicate count is only meaningful next to a non-zero overlap window |
| Stuck count reported as 1 when the baseline was already 1 | Subtract job 41 explicitly, in writing |

---

### C6 — Close the bench (2 min)

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*src.worker*' } | Select-Object ProcessId
docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT count(*) FROM job_executions;" -c "SELECT count(*) FROM pg_stat_activity WHERE datname='relay';"
```

Required: worker processes `0`, and the closing arithmetic reconciles against C0 —
`jobs_after = jobs_before + everything you seeded`. **Do not clean up the stuck jobs.** They are
Week 2's input, and Week 2's first commit should be measured against them.

Delete any output files you redirected to (`labs\out\*`), and say in the log what you removed.

---

# PART D — Scope guard

**Not today. Each one has an owner.**

| Tempting | Owner | What you lose by building it today |
|---|---|---|
| A reaper resetting `running → pending` | **Week 2, Din 1** | Today's stuck job *is* its problem statement. Build the fix now and you copy a solution before understanding the failure |
| `lease_expires_at`, `claimed_at`, `locked_by`, heartbeats | Week 2 | Din 5's whole output is discovering **which column is missing** and why. Adding it on faith skips that |
| Retry / `attempts` increment / `dead_letter` | Week 2 | `attempts = 0` on a stuck job is a finding today, not a bug to fix |
| Any change to the claim query, including `SKIP LOCKED` tuning | Din 4 settled it; revisit Week 4 | One variable per day. Today's variable is worker death |
| Idempotency key, dedup | Week 3 | Today produces at-most-once loss, not duplication. They are different failures |
| An index on `job_executions.job_id`, or the FK | Week 4 / retention | `D-21` priced both and deferred them deliberately |
| Fixing shutdown latency (slicing the sleep, `asyncio.Event`) | Week 2 shutdown hardening | Today you **measure** it (Step 4). Fixing it before the number exists means never knowing what it was |
| Structured logging / metrics | Week 4 | Two prints and `echo=True` timestamps are enough for today's numbers |

**One handler added. Nothing else in `src/`.**
