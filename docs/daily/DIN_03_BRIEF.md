# DIN 3 — Worker loop: `claim → execute → mark`

**Week 1 · Layer L1 · Budget ~2h15m** · Plan: [`../planning/WEEK_01.md`](../planning/WEEK_01.md) (DIN 3 section)

> **How to use this file.** Part A + Part C are safe to paste to Gemini, along with
> [`GEMINI_RULES.md`](GEMINI_RULES.md) and the SHARED CONTEXT block from the week plan.
> **Part B is not.** `DIN_03_KEY.md` stays closed until each step's experiment has actually run.
>
> **Order per step:** answer that step's Part B questions from your own head → build → run Part C →
> compare with your prediction and write your own explanation of any difference → *then* open that
> step's KEY section.

---

## Today in one line

Din 2 proved that **commit, then tell the caller** creates the durability guarantee.
Today the same operation runs in reverse: the worker must **commit the claim before doing the work**,
and that commit is what removes the job's protection. Same mechanic, opposite effect.

---

## Bench state as of right now (measured by reviewer, not by you)

```
jobs table:  9 rows, all status='pending'
max(id) = 37 · jobs_id_seq.last_value = 37, is_called = t
All 9 rows have distinct created_at (each POST was its own transaction)
```

Those 9 rows are leftovers from Din 2's probing. **Decide what to do with them before Step 1**
(Step 0). Din 1 already showed what leftovers cost: Week 0's `counters`/`doctors` tables made
`alembic check` permanently red. Same class of problem — a dirty bench makes "3 jobs enqueue karo →
worker sab uthata hai" unverifiable.

---

# PART A — Steps

Seven small steps. Each ends in something you can run. If a step is taking more than ~15 minutes,
it is too big — stop and split it.

Do **not** create any new columns or tables today. `started_at`, `locked_by`, `last_error`,
`lease_expires_at`, `job_executions` — every one of those belongs to a later week (see Part D).

---

## Step 0 — Clean bench + the reading you owe (15 min)

The `RabbitMQ acknowledgements` reading was deferred from Din 2 *specifically* to sit here, because
it is the same question as today's build in different vocabulary.

**Terms used in this step**

| Term | What it is |
|---|---|
| `ack` | A consumer's message to the broker: "this message is dealt with, drop it" |
| `auto-ack` | Broker treats a message as acked the moment it is *delivered*, not when it is processed |
| `nack` | Negative acknowledgement — "I did not deal with this" |
| `requeue` | Put a nacked/unacked message back into the queue for redelivery |
| `redelivered` flag | Marks a message the broker has handed out at least once before |

**Do:**
1. Read the RabbitMQ acknowledgements docs. Write **one line each**: (a) when should `ack` be sent
   relative to the work, (b) what exactly makes `auto-ack` dangerous, (c) what `nack` + `requeue`
   does that dropping the connection does not.
2. Decide the fate of the 9 pending rows. Whatever you choose, **write down the starting state**:
   ```powershell
   docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;"
   ```
3. Keep that number. Every later count today is relative to it.

**Scheduling note:** the plan also lists *DDIA Ch 7 second pass, pages 233–251* for today. Both
readings will not fit in the budget. RabbitMQ acks first — it is owed, and it maps directly onto
Steps 2–4. If DDIA slips to Din 5, record that as a deliberate slip, not an omission.

---

## Step 1 — A worker process that only polls (10 min)

No claiming yet. Just prove a second process exists, connects, finds nothing, and sleeps.

**Terms used in this step**

| Term | What it is |
|---|---|
| Polling | Asking the database "is there work?" on a timer, rather than being notified |
| Engine (SQLAlchemy) | The object owning a connection pool and dialect config. One per process, normally |
| `async_sessionmaker` | A factory producing `AsyncSession` objects; the session is the unit of work |
| Session scope | The span between getting a session and closing it — one transaction boundary by default |

**Do:**
1. New file, separate process — something like `src/worker.py`, runnable as
   `python -m src.worker` from the repo root.
2. It is **not** part of the FastAPI app. No `Depends`, no `get_db`. `get_db` is a request-scoped
   generator; a worker's unit of work is a job, not a request.
3. Loop: look for work → find nothing → sleep → repeat. Log every iteration with a worker
   identifier of some kind, because Din 4 runs two of these at once and untagged logs will be
   useless then.
4. Run it against the current queue state and watch it poll.

**Design judgement — decide it, note the cost, do not ask anyone for the pick:**
- Does the worker import the engine from `src/database.py`, or build its own?
  Same file = one config to keep straight; separate = independently tunable pool later.
  These are two different processes either way — be clear with yourself about *why* that is true.
- Poll interval. Name what gets worse at 10 ms and what gets worse at 10 s.
  This is `D-01`'s raw material (Din 6), so write the reasoning, not just the number.

**Runnable end state:** worker prints polls and sleeps in a loop. Killing it however you like is
fine at this step — Step 6 makes shutdown deliberate.

---

## Step 2 — Claim only. No execution. (15 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| `FOR UPDATE` | Row-level lock taken by a `SELECT`; another transaction wanting the same row's lock waits |
| Row-level lock lifetime | Until the holding transaction commits or rolls back. There is no shorter unlock |
| Compare-and-set | Write conditioned on the value you believe is current: `SET status='running' WHERE id=$1 AND status='pending'` |
| Affected row count | How many rows a DML statement actually changed. SQLAlchemy exposes it as `result.rowcount` |
| `READ COMMITTED` | Postgres default isolation. Each *statement* sees a fresh snapshot of committed data |
| `LockRows` / `Limit` | Query plan nodes: one takes row locks, one stops after N rows |

**Do:**
1. Claim in **one transaction**:
   ```
   BEGIN
     SELECT id, type, payload FROM jobs WHERE status='pending' ORDER BY created_at LIMIT 1 FOR UPDATE
     UPDATE jobs SET status='running' WHERE id=$1 AND status='pending'
     -- check the affected row count
   COMMIT
   ```
   **No `SKIP LOCKED`.** That is deliberate and Din 4 depends on it being absent.
2. The worker prints the claimed id and the affected row count, then goes back to polling.
   **It does not execute anything yet.**
3. Handle the affected row count being `0` explicitly, even though today you will struggle to
   produce that case. Silence there is the bug Week 0 Day 5 was about.
4. Record the plan:
   ```powershell
   docker compose exec -T db psql -U postgres -d relay -c "EXPLAIN SELECT id, type, payload FROM jobs WHERE status='pending' ORDER BY created_at LIMIT 1 FOR UPDATE;"
   ```
   Write down the node order. Predict it first (Part B).

**Do NOT try to resolve Trap 3 today.** Whether a *blocked* second worker eventually gets the same
job, a different job, or nothing at all is Din 4's measurement. Note the question, leave it open.

**Runnable end state:** one `pending` job becomes `running` and stays there. Worker keeps polling and
finds nothing more.

---

## Step 3 — Execute, then mark (15 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| Transaction boundary | Where a `COMMIT` sits. Moving one changes what is atomic, not just what is fast |
| Handler | The function that does a job's actual work. Today: sleep and print. No real side effect |
| Transition guard | The `AND status='running'` in the mark statement. Without it the write is unconditional |
| `expire_on_commit` | SQLAlchemy setting controlling whether ORM attributes are invalidated on commit. Already `False` in `src/database.py` |

**Do:**
1. Handler: `asyncio.sleep(2)` + a print. **Not** `time.sleep` — Week 0 Day 1 measured what that
   does to an event loop (6.04 s vs 2.04 s).
2. Execute **after** the claim transaction has committed.
3. Mark in a **new** transaction, guarded:
   `UPDATE jobs SET status='succeeded' WHERE id=$1 AND status='running'`
4. Check the affected row count here too, and log a conflict if it is `0`.
5. Full path: enqueue 3 jobs, run the worker, all three end `succeeded`.

**Runnable end state:** `pending → running → succeeded` for 3 jobs, visible both in `psql` and via
`GET /jobs/{id}`.

---

## Step 4 — The failure path (12 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| Handler registry | A mapping from `type` string to handler function |
| Terminal state | A state nothing will move the job out of. Whether `failed` is one is a decision, not a fact |

**Do:**
1. A registry mapping `type` → handler. Register at least: one sleeper, one that raises.
2. Enqueue a job whose handler raises. It must end `failed`, using the same guarded update shape.
3. The exception must not kill the worker loop. It processes the next job.
4. No error text column exists and you are **not** adding one today. Log the exception to stdout.

**Design judgement — pick and record the cost:**
- Unknown `type` arrives (the DB has no constraint on `type`, by `D-04`). Options: mark `failed`,
  leave `pending`, or crash the worker. Each has a distinct failure mode. Choose, and write what
  the choice costs when Week 2's retry loop exists.
- What does `failed` **mean** today, given retries arrive in Week 2? Define it now so Week 2 does not
  have to redefine it. A definition that Week 2 must change is a definition that was wrong today.

**Runnable end state:** a `failed` job, and a worker still running afterwards.

---

## Step 5 — Trap 2, checked so that it can actually fail (15 min)

The Din 2 lesson, applied before the fact: *a check that only ever sees the correct implementation
proves nothing.* So run this one **twice**, deliberately wrong first.

**Terms used in this step**

| Term | What it is |
|---|---|
| `pg_stat_activity` | System view with one row per backend connection |
| `state` | `active` (running a statement), `idle` (no transaction), `idle in transaction` (open transaction, no statement running) |
| `wait_event_type` / `wait_event` | What a backend is blocked on, e.g. `Client`/`ClientRead`, `Lock`/`transactionid`, `Lock`/`relation` |

**Do:**
1. Temporarily raise the sleeper handler to ~10 s so you have time to look.
2. **Run A — deliberately wrong.** Keep the claim transaction **open** across the handler
   (commit only after the mark). While the handler sleeps, from a second terminal:
   ```powershell
   docker compose exec -T db psql -U postgres -d relay -c "SELECT pid, state, wait_event_type, wait_event, xact_start, query FROM pg_stat_activity WHERE datname='relay' ORDER BY pid;"
   ```
   Record every row verbatim.
3. **Run B — correct.** Commit the claim before executing. Same observation, same command.
4. Put the sleeper back to 2 s.

**The point of the pairing:** if you had only run B, "no `idle in transaction`" would also pass for a
worker that never opened a transaction at all, or for a query that was looking at the wrong database.
Run A is what establishes the check can detect the thing it claims to detect.

**Runnable end state:** two recorded `pg_stat_activity` snapshots that differ.

---

## Step 6 — Graceful shutdown: finish current, take no new (15 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| `SIGINT` | Ctrl+C in the console. Python's default handler raises `KeyboardInterrupt` |
| `SIGBREAK` | Windows-only, signal 21. Raised by Ctrl+Break, or `CTRL_BREAK_EVENT` sent to a process group |
| `signal.signal(sig, fn)` | Registers a Python-level handler. Registration succeeding says nothing about whether the OS will ever deliver that signal |
| `loop.add_signal_handler` | asyncio's own signal hook |
| `asyncio.CancelledError` | Raised *inside* an await when the surrounding task is cancelled |
| finish-current vs abort | Two different shutdown semantics: complete the in-flight job, or drop it |

**Two platform facts, measured by the reviewer on this machine today, so you do not lose 40 minutes
to them.** Both are about what the OS *permits*, not about what your code will do:

| Measured | Consequence |
|---|---|
| `loop.add_signal_handler(...)` → `NotImplementedError` on `ProactorEventLoop` (Python 3.13.5, win32) | Use `signal.signal`, not the asyncio hook |
| `os.kill(os.getpid(), signal.SIGTERM)` with a registered SIGTERM handler → handler **never ran**, process exited with code `15` | Real `SIGTERM` is not testable on Windows natively. Ctrl+C is your catchable signal today; the Docker route for genuine `SIGTERM` is Din 5's problem |

**Do:**
1. Register a handler that **sets a flag**. It must not do database work and must not raise.
2. The loop checks the flag *before claiming*. In-flight job is left alone.
3. Exit cleanly — exit code `0`.
4. Test twice, because the two cases are different: Ctrl+C **while a job is mid-flight**, and
   Ctrl+C **while idle-polling**.
5. Register `SIGTERM` too even though you cannot trigger it here. It will matter inside Docker.

**Runnable end state:** Ctrl+C mid-job → the job reaches a terminal status, worker exits `0`, and
nothing is left sitting in `running`.

---

# PART B — Prediction questions

> ⛔ **DO NOT PASTE THIS SECTION TO GEMINI. DO NOT OPEN THE KEY TO ANSWER IT.**
>
> Answer each step's questions **before** writing that step's code, from your own head, in writing.
> `idk` is a legitimate answer and is recorded as one. A guess dressed as knowledge is worse data
> than an honest `idk` — Din 1 scored `0/9` precisely because the questions were never attempted.
>
> If you do not know what a *term* means, the glossary in Part A is there for that, and asking
> Gemini about a term is allowed. If knowing the answer to your question would also answer one of
> these, do not ask it.

```
STEP 1 — polling
1.1  Worker imports the engine from src/database.py. Is it sharing a connection pool with the
     running API process? Yes or no, and state the mechanism that makes your answer true.
1.2  Poll interval: name one thing that gets worse at 10 ms and one thing that gets worse at 10 s.
1.3  The worker holds a pool of connections and finds no work for an hour. What, if anything,
     is being consumed on the Postgres side during that hour?

STEP 2 — claim
2.1  Only ONE worker is running today. Does FOR UPDATE protect anything right now? Against what?
2.2  You already SELECTed the row and know its status is 'pending'. So what can the affected row
     count of the following UPDATE ... WHERE status='pending' possibly tell you that the SELECT
     did not? Under what circumstance is it not 1?
2.3  EXPLAIN: predict the node order. Does LockRows sit above or below Limit? Which executes first?
2.4  Claim commits. The process dies before the handler starts. What is the job's status one
     second later? One hour later? Who changes it?
2.5  You wrote the SELECT and the UPDATE in one transaction. Suppose you split them into two
     transactions instead. Which Week 0 Day 5 experiment have you just recreated, and what would
     be visibly wrong in the jobs table afterwards?

STEP 3 — execute and mark
3.1  Between COMMIT of the claim and COMMIT of 'succeeded', the worker crashes and is restarted,
     repeatedly. How many times can the handler's side effect run? Give a number or a bound.
3.2  Mark 'succeeded' affects 0 rows. Name every situation that could cause it, today and in
     Week 2. What should the worker do in each?
3.3  Does expire_on_commit=False change what you can read off the row after the mark commits?
     Does it matter whether you used the ORM or a Core update() statement?
3.4  Handler takes 2 s. During those 2 s, how many database connections is the worker holding,
     and how many open transactions?

STEP 4 — failure
4.1  The handler raises. Where does that exception surface relative to your transaction — is any
     transaction open at that moment?
4.2  The mark-'failed' UPDATE itself raises (say the DB restarted). What is the job's status now,
     and what happens on the worker's next loop iteration?
4.3  Is 'failed' terminal today? Write the definition you will hold to in Week 2.
4.4  A job with an unregistered type arrives. What did you choose, and what does that choice cost
     once retries exist?

STEP 5 — pg_stat_activity
5.1  Run A (transaction held open across the handler). Predict the worker's row: which state?
     Which wait_event_type / wait_event? Will xact_start be present?
5.2  Run B (claim committed before executing). Predict the same three fields.
5.3  In Run A, with only ONE worker, is anything actually blocked? Name a specific statement that
     would block, and say who would have to issue it.
5.4  If you only ever ran B, name two broken implementations that would also pass the check
     "no idle in transaction visible".

STEP 6 — shutdown
6.1  Ctrl+C arrives while the handler is inside `await asyncio.sleep(10)`. Does that sleep finish,
     or does the await raise? If it raises, what exception, and where is it caught?
6.2  Your handler only sets a flag. When does the loop actually observe that flag — immediately,
     at the next await, or at the next poll?
6.3  Predict the exit code.
6.4  Predict the in-flight job's final status: succeeded, running, or failed?
6.5  Ctrl+C while idle-polling instead. Predict exit code and elapsed time to exit.
6.6  Without running it: how would kill -9 differ? Which of 6.1–6.4 would change?
```

---

# PART C — Verification

Each check below is written to **distinguish** a working implementation from a plausible broken one.
Before accepting any check as passed, ask the Din 2 question: *what wrong implementation would also
pass this?*

Environment: PowerShell, repo root, `.venv` active. Statement separator is `;`, never `&&`.
API in one terminal, worker in another, `psql` in a third.

```powershell
# terminal 1
uvicorn src.main:app --reload
```

Enqueue helper (Day 2 used curl; `Invoke-RestMethod` avoids PowerShell's curl alias entirely):

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/jobs -ContentType application/json -Body '{"type":"sleep","payload":{}}'
```

---

### C1 — Claim really is one transaction (Step 2)

Status alone cannot check this. A worker that `SELECT`s in one transaction and `UPDATE`s in another
produces an identical `running` row with one worker running. The distinguisher is the SQL log, and
you already have `echo=True` for exactly this reason.

**Check:** in the worker's log, find the claim. Expect **one** `BEGIN` whose `COMMIT` comes *after*
both the `SELECT ... FOR UPDATE` and the `UPDATE`.

```
BEGIN (implicit)
SELECT jobs.id, jobs.type, jobs.payload FROM jobs WHERE jobs.status = $1 ORDER BY jobs.created_at LIMIT $2 FOR UPDATE
UPDATE jobs SET status=$1 WHERE jobs.id = $2 AND jobs.status = $3
COMMIT
```

| Would also pass a status check | Caught by the log check |
|---|---|
| `SELECT` and `UPDATE` in separate transactions | ✅ two `BEGIN`/`COMMIT` pairs appear |
| `FOR UPDATE` omitted entirely | ✅ absent from the emitted SQL |
| `UPDATE` without the `AND status=` guard | ✅ visible in the statement |

Record the affected row count your code observed. Not "it worked" — the number.

---

### C2 — The transition guard is load-bearing, not decorative (Step 3)

An unguarded `UPDATE ... SET status='succeeded' WHERE id=$1` passes every happy-path test. Make
something else touch the row while the handler is asleep, and the two implementations separate.

```powershell
# 1. enqueue one job, start the worker, and while the handler is sleeping:
docker compose exec -T db psql -U postgres -d relay -c "UPDATE jobs SET status='failed' WHERE id=<ID> AND status='running'; SELECT id, status FROM jobs WHERE id=<ID>;"
# 2. let the worker finish, then:
docker compose exec -T db psql -U postgres -d relay -c "SELECT id, status FROM jobs WHERE id=<ID>;"
```

| Implementation | Affected rows on the mark | Final status |
|---|---|---|
| Guarded (`AND status='running'`) | `0`, and your code logs a conflict | stays `failed` |
| Unguarded | `1`, silently | becomes `succeeded` — the other writer's decision is gone |

Record which one you got. If it is the second row, that is a real bug found by a real check, and it
is the same shape as Din 2's `413`: a passing test over an absent mechanism.

---

### C3 — Three jobs end up succeeded, and the transition was observable (Step 3)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;"
```

Counts must reconcile against your Step 0 starting state. Write the arithmetic out; if it does not
close, say so rather than rounding it off.

While the worker is mid-job, hit `GET /jobs/{id}` and record the response. `running` must be
observable through the API, not just in `psql` — "it can always say where a job is" is contract
point 5, and if `running` is never visible externally the contract is unmet even though the final
status is right.

---

### C4 — A failing handler produces `failed` and does not kill the worker (Step 4)

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/jobs -ContentType application/json -Body '{"type":"boom","payload":{}}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/jobs -ContentType application/json -Body '{"type":"sleep","payload":{}}'
```

Enqueue the failing one **first**, then a good one. Expected: `failed`, then `succeeded`, and the
worker is still polling. Enqueueing only the failing job would not distinguish "handled the
exception" from "the loop died right after marking it".

Then the unregistered type:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/jobs -ContentType application/json -Body '{"type":"does_not_exist","payload":{}}'
```

Record what happened and whether it matches what you decided in Step 4. If the worker spins on it
in a tight loop, record that — it is a real finding about your unknown-type choice.

---

### C5 — Trap 2, differential (Step 5)

Fill this in from your two runs. Both rows must be real output.

| | `state` | `wait_event_type` / `wait_event` | `xact_start` present? |
|---|---|---|---|
| Run A — transaction held open across the handler | | | |
| Run B — claim committed before executing | | | |

Also record the API process's own connections, so you can tell the worker's backend apart from
theirs. If both runs produce identical rows, the check did not work and the conclusion is
"not established" — not "Run B is fine".

---

### C6 — Graceful shutdown (Step 6)

```powershell
# worker terminal: start it, enqueue a job, wait until the handler is clearly mid-flight, then Ctrl+C
# immediately after the process exits:
echo $LASTEXITCODE
docker compose exec -T db psql -U postgres -d relay -c "SELECT id, status FROM jobs WHERE status='running';"
```

| | Finish-current (what you are building) | Abort-on-signal (the plausible wrong version) |
|---|---|---|
| Job's final status | terminal (`succeeded`/`failed`) | stays `running` |
| Rows left in `running` after exit | `0` | `1` |
| Exit code | `0` | `0` or `1` — **this field alone cannot tell them apart** |
| Time from Ctrl+C to exit | ≈ remaining handler time | ≈ immediate |

The exit-code row is the reason this is a table and not a single assertion. Exit code `0` is
satisfied by the wrong implementation too. The `running` count and the elapsed time are what
separate them.

Repeat with Ctrl+C while idle-polling and record both fields again — same command, different
starting condition.

---

### C7 — Day-close state (2 min)

```powershell
docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT count(*) FROM jobs WHERE attempts <> 0;"
```

Note anything stuck in `running` and why. `attempts` should still be `0` everywhere unless you
deliberately chose to increment it — if you did, that is a decision to write down, not a detail.

---

# PART D — Scope guard

**Not today. Each one has an owner.**

| Tempting | Owner | What you lose by building it now |
|---|---|---|
| `FOR UPDATE SKIP LOCKED` | **Din 4** | Din 4's whole measurement is the *contrast*. With `SKIP LOCKED` already in place there is nothing to contrast against |
| A second worker | **Din 4** | Same. Today is one worker on purpose |
| `job_executions` side-effect counter | **Din 4** | Din 4 opens by establishing that you cannot detect double execution from the `jobs` table at all. Building the counter early skips that realisation |
| Lease, heartbeat, reaper, `locked_by`, `lease_expires_at` | **Week 2** | Week 2 exists because you will have *seen* a job stuck forever. Din 5 produces that sight |
| Retry, backoff, DLQ, `dead_letter` status, incrementing `attempts` on failure | **Week 2** | Same |
| Idempotency key, dedup, payload hashing | **Week 3** | `P-07` |
| Index on the claim query | **Week 4** | `P-03` — to be settled by `EXPLAIN ANALYZE`, not by guessing. Note today's plan shape; do not act on it |
| Metrics, load test, throughput numbers | **Week 4** | |
| Tests in `tests/` | Not Week 1 | |
| `last_error` / `started_at` columns | **Week 2** | A migration today would bundle the column decision with backfill semantics for in-flight rows — the same argument `D-08` used for `attempts` |
| Turning `echo=False` | — | The SQL log is the day's primary evidence. C1 depends on it |

**Specifically: if you find yourself wanting to fix the fact that a `running` job has nothing
protecting it — stop.** That is not a gap in today's work. It is today's *finding*, and it is Week 2's
entire problem statement. Write it down and leave it broken.

---

## What the day should produce for the log

- The affected row counts you actually observed (C1, C2) — numbers, not "worked".
- The `EXPLAIN` node order, alongside your prediction of it.
- The C5 differential table, both rows, verbatim.
- The C6 table, with the elapsed time and the `running` count.
- Your poll-interval decision **with its cost** — raw material for `D-01`.
- Your definition of `failed`, and the unknown-type choice with its cost.
- One sentence, your own words: *what did committing the claim buy, and what did it cost?*
- Every question you wrote `idk` for. Those are the day's real output.
