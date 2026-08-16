# DIN 3 — KEY (sealed)

> 🔒 **Open one step's section only after that step's experiment has been run.**
> Not after you have written your answer. After the **measurement**.
>
> Reason, from your own Din 1 log: the failure mode is being *"recognisable, not recallable."*
> Reading this before running the code converts today into recognition, which is what produced
> `0/9`.
>
> **Never paste this file to Gemini.**
>
> Every claim below is labelled `[MEASURED]` (someone observed it) or `[INFERRED]` (reasoning or
> documentation). Where an answer genuinely depends on your machine or your implementation, it says
> **must be measured** rather than giving you a number.

---

## STEP 1 — polling

**1.1 — Shared pool? No.**
`[INFERRED, mechanism is definitional]` A connection pool is in-process memory holding open TCP
sockets. Importing `src/database.py` in the worker process executes that module *again*, in that
process, producing a second `engine` object with its own pool. Nothing crosses the process boundary.

What this means practically: total Postgres backends = the sum over processes, and that sum is what
`max_connections` (default `100`) bounds. Sharing a *URL* is not sharing a *pool*. Week 0 Day 3's
pool-exhaustion finding therefore applies per process, not per app.

Second-order point worth keeping: asyncpg connections are bound to the event loop that created them.
Two processes each with their own loop is the clean arrangement. This is one of the reasons a worker
is a separate process rather than a background task inside the API.

**1.2 — Poll interval. Design judgement, so here are the two directions, not a pick.**

| Direction | What gets worse |
|---|---|
| Short (10 ms) | Every poll is a transaction and a round trip against a table with **no index and a `Seq Scan`** today. It burns a connection slot, CPU on both sides, and produces log volume that makes the SQL echo useless as evidence. It does **not** write WAL — the polls are read-only |
| Long (10 s) | The interval is an upper bound on enqueue-to-start latency for an idle queue. A job posted just after a poll waits nearly the whole interval before anything happens |

The framing that belongs in `D-01`: **the poll interval is the price of using a database as a queue.**
A broker pushes; a table must be asked. There is no interval that is correct — there is a latency
budget and a query-rate budget, and the interval is where you spend one to buy the other.
Do not invent a number for either cost; `P-03` exists because a guessed number was already written
once on this project.

One more consequence, and it bites on Din 5 / Week 2: if the loop sleeps the whole interval in one
`await`, the shutdown delay is bounded by the interval too — see **6.5**.

*(Postgres does have a push mechanism, `LISTEN`/`NOTIFY`. It is not in this month's scope and it does
not remove the need for polling as a backstop. Noting it exists so you are not surprised later; do
not build it.)*

**1.3 — An hour of finding nothing.**
`[INFERRED, verifiable with the C5 command]` Each pooled connection is a real Postgres backend
process holding a `max_connections` slot. Its `state` is `idle`, not `idle in transaction` — and that
distinction is the whole answer:

| State | Holds locks? | Holds back the vacuum horizon? |
|---|---|---|
| `idle` | No | No |
| `idle in transaction` | Yes | Yes |

An idle *connection* is cheap and boring. An idle *transaction* is Day 1's `P-06` — PID 53, blocking
a `DROP TABLE` that had nothing to do with it. Step 5 is about not becoming that.

Do not state a memory figure per backend. That has to be measured, and today it does not matter.

---

## STEP 2 — claim

**2.1 — With one worker, `FOR UPDATE` protects against exactly one thing: you, at the `psql` prompt.**
`[INFERRED]` No other session competes for the row today. That is precisely why C2 has to *create*
interference by hand.

The sharper point, and the one worth carrying: **`FOR UPDATE` is not what makes the claim correct.
The compare-and-set is.** They are two different mechanisms doing two different jobs:

| Mechanism | Job |
|---|---|
| `... AND status='pending'` + affected-row-count check | **Correctness.** Detects that your belief about the row was stale, atomically, because the check and the write are one statement |
| `FOR UPDATE` | **Efficiency and ordering under contention.** Changes what a competing claimer *does* while another holds the row |

Which of those two costs you what, under two real workers, is **Din 4's measurement**. Do not resolve
it from here.

**2.2 — Today the affected row count is an assertion about your own code, not about concurrency.**
`[INFERRED]` Once `FOR UPDATE` has returned the row, your transaction holds the row lock, so within
that transaction the guarded `UPDATE` matches. Under one worker, a correct implementation gets `1`
every time.

So why check it? Because it returns `0` for these, all of which are silent otherwise:

- the `SELECT` and the `UPDATE` are in **different** transactions (Week 0 Day 5 Exp 1, reproduced),
- `FOR UPDATE` was never emitted,
- the guard predicate names the wrong expected value,
- you are marking an id you did not claim,
- and from Week 2 onward: a reaper moved the row while you held stale knowledge of it.

That is the shape of a good assertion — it is boring on correct code and the only signal you get on
broken code. Same family as `alembic check` on Din 1: valuable exactly because it normally says
nothing.

**2.3 — The plan.** `[MEASURED, reviewer, on the current 9-row table]`

```
Limit  (cost=1.14..1.15 rows=1 width=48)
  ->  LockRows  (cost=1.14..1.24 rows=8 width=48)
        ->  Sort  (cost=1.14..1.16 rows=8 width=48)
              Sort Key: created_at
              ->  Seq Scan on jobs  (cost=0.00..1.10 rows=8 width=48)
                    Filter: (status = 'pending'::text)
```

Read it bottom-up for execution order: scan → sort → **lock** → then `Limit` stops. `LockRows` sits
*below* `Limit`, so the row is locked **before** `Limit` has decided it has enough rows.

What that implies when a second worker is blocked on that lock is **Din 4**, and it is the one thing
in this file deliberately left unanswered. Note the plan shape, note the question, stop.

`Seq Scan` is correct at this size — with 9 rows an index would very likely be ignored even if one
existed. That is `P-03`, Week 4, by `EXPLAIN ANALYZE`.

**2.4 — Claim committed, process dies before the handler: the job is `running` forever.**
`[INFERRED, and Din 5 measures it]` One second later: `running`. One hour later: `running`. Nobody
changes it, because nothing in this repository can. Three facts you already measured combine here:

- Week 0 Day 2: on `kill -9` the handler does not run. The worker cannot clean up after itself.
- Week 0 Day 3: when the process dies, Postgres notices and rolls back its **open** transaction.
  The claim was **committed**, so there is nothing to roll back. Commit is what removed the safety net.
- Week 0 Day 5: nothing outside can distinguish a dead worker from a slow one. Only a deadline can.

Hence recovery has to come from **outside** every participant and it has to trust a clock. That is
`lease + reaper`, Week 2, and Din 5's job is to make you look at the stuck row before you are allowed
to fix it.

**2.5 — Split the claim into two transactions and you have rebuilt Week 0 Day 5 Exp 1.**
`[MEASURED in Week 0]` And the answer to "what would look wrong in the `jobs` table" is the
uncomfortable one: **nothing.** Both workers write `status='running'`. Same column, same value, one
row, no constraint violated. Your Week 0 log already recorded it — *"dono ne same value likhi, row
bilkul theek dikhi."*

Which is why the `jobs` table is the wrong instrument for detecting double execution, and why Din 4
opens by building a different one.

---

## STEP 3 — execute and mark

**3.1 — At most once. Not twice, and that is the surprise.**
`[INFERRED]` Crash after the claim commits, restart, crash again, forever: the handler runs **once**,
because the claim query filters `status='pending'` and the stuck row is `running`. No restart
re-executes it.

So today's system, on worker death, is **at-most-once** — the exact opposite of the week's title.
At-least-once needs something that puts a job *back*, and there are only two such things:

| Route to a second execution | Arrives in |
|---|---|
| Two workers claiming the same job | **Din 4** (with `FOR UPDATE` alone, no `SKIP LOCKED`) |
| Something resetting `running → pending` after a timeout | **Week 2** (the reaper) |

Neither exists yet. Write that down, because it reframes the whole week: *duplicate execution is the
price of recovery, not a bug that showed up on its own.* You cannot have "never lost" and "never
duplicated" from a single status column and a crash — and that tension is contract points 1 and 2
pulling against each other.

**3.2 — Mark affects `0` rows. Causes, and what to do.**
`[INFERRED]`

| Cause | When | Correct response |
|---|---|---|
| Another writer changed the status (C2 does this by hand) | Today | Log loudly. **Do not** rewrite it |
| Row deleted | Din 4/5 resets, Week 4 retention | Log, move on |
| Wrong expected value in the guard | Bug | Fix the code |
| Marking an id you never claimed | Bug | Fix the code |
| A reaper decided your lease expired and requeued the job | **Week 2** | Abandon quietly. Another worker may already be running it |

The rule underneath: **`rowcount = 0` means "my belief about this job is stale."** The one thing you
must not do is force the write, because forcing it overwrites a decision that was made with better
information than you have. Never crash the worker over it either — one confused row must not stop the
queue.

**3.3 — `expire_on_commit=False` only matters if an ORM instance outlives the commit.**
`[INFERRED]`

- **Core** (`session.execute(update(...))`, `select(Job.id, Job.status)`): rows come back as plain
  `Row` objects. There is nothing to expire; the setting is irrelevant to that path.
- **ORM instance**, default `expire_on_commit=True`: touching `job.status` after commit triggers a
  refresh `SELECT` — an extra round trip, and a `DetachedInstanceError` if the session is gone.
- **ORM instance**, `False` (your current setting): attributes keep their last-loaded values. No extra
  query, and the value may now be **stale**. That is fine as long as you never treat it as
  authoritative.

Day 2's M3 is the related measurement: `INSERT ... RETURNING` already fetched `id, status, attempts,
created_at` in one statement, which is why no `refresh()` was needed there. An `UPDATE` gives you no
such thing unless you ask for `RETURNING` explicitly.

**3.4 — During the 2 s handler: one pooled connection, zero open transactions.**
`[INFERRED — and this is exactly what C5 Run B measures, so measure it rather than believing this.]`
`Session.commit()` ends the transaction and returns the connection to the pool, so the backend should
show `state = 'idle'`. If your snapshot shows `idle in transaction`, your commit is not where you
think it is — which is the entire point of Step 5.

---

## STEP 4 — failure

**4.1 — When the handler raises, no transaction is open.**
`[INFERRED]` The claim already committed; the mark has not begun. So there is nothing to roll back,
and **rollback cannot undo the claim**. The `running` row is durable and the exception cannot touch it.

If you happened to wrap the handler inside a session context manager anyway, its exit emits a
`ROLLBACK` even though nothing failed at the database level. That log line is harmless — Day 2's M2
already established that `ROLLBACK` in the echo is usually session teardown, not an error.

**4.2 — If the mark itself fails, the job stays `running` and the worker never sees it again.**
`[INFERRED]` Same terminal position as 2.4, reached by a different route.

Worth naming the symmetry, because it is the same shape as Day 2's finding: there is a window between
**doing the work** and **recording that the work was done**, and no ordering of your statements closes
it. Day 2 had the window between `COMMIT` and the client learning about it (`P-07`). Today's window is
between the side effect and its record. Week 3 *bounds* one of these. Neither ever closes.
`narrows`, not `closes` — this is the wording error you made three times on Day 2.

**4.3 — `failed` is terminal today and must not be defined that way.**
A definition that survives Week 2:

> **`failed`** — this attempt ended in an exception, and no worker is currently working on the job.

Notice what it does not say: it says nothing about whether the job will ever run again. That is why
Week 2 can add retries without rewriting it, and why Week 2 adds a **separate** `dead_letter` state
for "will never run again" instead of overloading `failed`. Contract point 4 wants a DLQ, not silence,
and a DLQ needs a state that means *exhausted*, distinct from a state that means *this attempt broke*.

If your written definition was "the job is dead", Week 2 has to redefine it, and a definition Week 2
must redefine was wrong today.

**4.4 — Unknown `type`. Three options, real costs, no pick.**

| Option | Cost |
|---|---|
| Mark `failed` | A **deployment ordering mistake** (worker rolled out before the handler was registered) becomes permanent data loss. With Week 2's retries it burns every attempt and lands in the DLQ for a reason that has nothing to do with the job |
| Leave it claimable | Survives the deploy race, but the worker re-encounters it every poll — a hot loop on a table you are already `Seq Scan`ning. And "leave it `pending`" after you already wrote `running` is a `running → pending` transition, which is **Week 2's reaper's job**. So this option is less clean than it sounds, and honestly it argues for not claiming unknown types in the first place |
| Crash the worker | Loudest possible signal, largest blast radius: one bad row stops the entire queue |

`D-04` deliberately left `type` unconstrained in the database because the DB cannot see the handler
registry. This question is the bill for that decision arriving. That is not an argument against `D-04`
— it is what "the invariant lives in the application" actually costs, and it belongs in your notes
next to `D-04` rather than as a new decision.

---

## STEP 5 — `pg_stat_activity`

**5.1 / 5.2 — Expected shape.** `[INFERRED for your run; the same pattern was MEASURED on Day 1 (M6)]`

| | `state` | `wait_event_type` / `wait_event` | `xact_start` |
|---|---|---|---|
| Run A — transaction held open across the handler | `idle in transaction` | `Client` / `ClientRead` | present, and ageing |
| Run B — claim committed first | `idle` | `Client` / `ClientRead` | `NULL` |

Two things to notice, because both are counter-intuitive:

- `Client`/`ClientRead` appears in **both** rows. The backend is waiting for its client either way;
  that wait event is not the signal. **`state` is the signal, and `xact_start` is the corroboration.**
- Run A's row is *identical in shape* to Day 1's PID 53 — the session that blocked a `DROP TABLE`
  five days after anyone was thinking about it. You would be reproducing your own `P-06`, on purpose,
  in your own worker.

If your actual rows differ from this table, your rows win. Record them verbatim and work out why.

**5.3 — In Run A, with one worker, nothing is blocked. That is the trap, not the reassurance.**
`[INFERRED]` No other session wants that row, so there is no visible victim. Two costs are still real
and both are invisible in the output:

- The open transaction has a real transaction id (it wrote), so it **holds back the vacuum horizon**
  for the whole cluster while it sleeps. Dead tuples cannot be cleaned up behind it.
- Any statement needing `ACCESS EXCLUSIVE` on `jobs` — `alembic upgrade`, `ALTER TABLE`, `DROP TABLE`
  — would queue behind it. That is `P-06` exactly: the blocked statement was routine maintenance with
  no visible connection to the cause.

So the honest conclusion from Run A is not "nothing bad happened". It is *"the damage from this
pattern does not appear until something unrelated needs the table, which is why it survived five days
last time."*

**5.4 — Broken implementations that also pass a B-only check.**
`[INFERRED]` At least these:

1. A worker that crashed before claiming anything — no transaction, nothing to see.
2. A snapshot taken between polls, or after the handler already finished. The mechanism could be
   completely wrong and the sample would still be clean.
3. The wrong `datname`, the wrong container, or the wrong database entirely.

So the check has a precondition it does not state: **you must be able to positively identify the
worker's backend in the output.** If you cannot point at its row, "no `idle in transaction`" is not
evidence of anything. A cheap way to make that possible is to set `application_name` on the worker's
connections so its backend is labelled in `pg_stat_activity` — optional, and it is a diagnostic, not
a feature.

This is the Day 2 `413` lesson arriving one day early: the checklist item passed, and the mechanism
was absent.

---

## STEP 6 — shutdown

Everything here is Windows-specific and most of it cannot be derived by reading. The four platform
facts below were **measured by the reviewer on this machine today** (Python 3.13.5, win32,
`WindowsProactorEventLoopPolicy`) with a temporary probe script that has since been deleted.

**T-a — `loop.add_signal_handler` does not exist here.** `[MEASURED]`
```
CHILD: loop.add_signal_handler(SIGINT) -> NotImplementedError:
CHILD: loop=ProactorEventLoop
```
Use `signal.signal`. Every tutorial that reaches for the asyncio hook is written for Linux.

**T-b — `signal.signal` registration succeeds for `SIGINT`, `SIGBREAK` *and* `SIGTERM`.** `[MEASURED]`
Registration succeeding tells you **nothing** about whether the OS will ever deliver that signal.
This is the trap: the code looks correct and one third of it is dead.

**T-c — `os.kill(os.getpid(), signal.SIGTERM)` with a handler registered: the handler never ran and
the process exited with code `15`.** `[MEASURED]`
```
CHILD2: registered SIGTERM handler, calling os.kill(self, SIGTERM)
PARENT: child2 exit code = 15
```
On Windows `os.kill` with `SIGTERM` is `TerminateProcess`. It is `kill -9` wearing `SIGTERM`'s name.
Week 0 Day 2 found this from the outside (container PID 1 never received a catchable `SIGTERM`); this
is the same fact from the inside, in one process. **Real `SIGTERM` is not testable natively on this
machine** — the Docker route is Din 5's problem, and Din 5's plan already says to use `docker stop`.

**T-d — `taskkill /PID` without `/F` refuses outright for a console process.** `[MEASURED]`
```
ERROR: The process with PID 28960 could not be terminated.
Reason: This process can only be terminated forcefully (with /F option).
```
The process kept running and finished normally. So `taskkill` gives you either nothing or a
`kill -9`; there is no graceful option there.

---

**6.1 — The sleep finishes. Nothing raises.** `[MEASURED]`
```
CHILD: entering one long await asyncio.sleep(6)
PARENT: sending CTRL_BREAK_EVENT
CHILD: handler ran, signum=21 (SIGBREAK)
CHILD: sleep completed normally after 6.01s
CHILD: handler had fired 1.65s into the sleep
CHILD: clean exit          → exit code 0
```
A flag-setting `signal.signal` handler ran **1.65 s into a 6 s await**, and the await still completed
normally at 6.01 s.

Mechanism `[INFERRED]`: the handler runs on the main thread at the next bytecode boundary and
**returns normally**. It never touches the pending future, so the coroutine resumes and the timer
plays out. No `KeyboardInterrupt`, no `CancelledError` — because nothing raised.

Two caveats, stated rather than papered over:
- This was measured with **`SIGBREAK`** (`CTRL_BREAK_EVENT`), not `SIGINT`. Ctrl+C with a custom
  flag-setting handler is expected to behave identically because it is the same CPython machinery,
  but that is `[INFERRED]` — **your run is the measurement.**
- If you leave the **default** `SIGINT` handler in place, the default handler *raises*
  `KeyboardInterrupt` at that same bytecode boundary. It propagates out of the await, out of
  `asyncio.run`, and the job is abandoned mid-flight with the row left `running`. That is
  abort semantics, and it is the C6 "plausible wrong version" column. `[INFERRED]`

**The single sentence worth keeping:** finish-current versus abort is decided by **whether your
handler raises**, not by anything asyncio does.

**6.2 — Signal delivery and flag observation are two different instants.** `[MEASURED above]`
Delivered at 1.65 s; observed by the loop only when control returns to the top of the loop, i.e. after
the remaining handler time. If you predicted "immediately", you predicted the delivery and the
question asked about the observation.

**6.3 — `0`** if the loop returns normally (`[MEASURED]` for the probe child).
The exit code for an **unhandled** `KeyboardInterrupt` on Windows was **not measured** — record what
you get rather than assuming `1` or `130`.

**6.4 — `succeeded`.** The handler was never interrupted, so the mark runs normally. `[INFERRED]`

**6.5 — Ctrl+C while idle-polling: exit time is bounded by your poll interval.** `[INFERRED]`
If the loop sleeps the whole interval in one `await`, the flag is set immediately and noticed up to a
full interval later. So:

> **poll interval ≤ shutdown budget.** Docker's default `stop` grace period is 10 s (Week 0 Day 2,
> measured, including the `137`). A 10 s poll interval sitting inside a 10 s grace period is a
> `SIGKILL` waiting to be scheduled, and the job it kills will be one nobody was even working on.

Fixes exist (sleep in small slices, or wait on an `asyncio.Event` so the signal can wake it). Choosing
one is a Week 2 shutdown-hardening decision; noticing the coupling is today's finding.

**6.6 — `kill -9`: no handler runs at all.** `[MEASURED in Week 0 Day 2, and again in T-c today]`
The job stays `running`, forever, with `job_executions`-style evidence that it started and no evidence
that it finished. That is Din 5, and building the fix today is the one thing Part D asks you hardest
not to do.

---

## Known traps — things you cannot find by reading

**K1 — The ORM silently deletes your compare-and-set guard.** `[INFERRED — verify in the echo, it is
visible there]` This one is the most likely bug in today's code. If you claim like this:

```python
job = (await session.execute(select(Job).where(...).limit(1).with_for_update())).scalar_one()
job.status = "running"
await session.commit()
```

the unit of work generates `UPDATE jobs SET status=$1 WHERE jobs.id = $2` — **primary key only, no
status predicate.** The guard that `GEMINI_RULES.md` lists as a locked decision (*"never write a
status update without a `WHERE` guard on the old value"*) has vanished, the code reads correctly, and
`rowcount` is `1` every time so the assertion never fires.

To keep compare-and-set you need an explicit statement carrying the predicate:
`update(Job).where(Job.id == id, Job.status == "pending").values(status="running")`, then read
`result.rowcount`.

C1 catches this, and it catches it only because you are reading the emitted SQL rather than the
resulting status. Same method as Day 1's `server_default` bug: compiling the DDL found what reading
the model could not.

**K2 — `now()` is the transaction timestamp, so one statement inserting many rows gives them all the
same `created_at`.** `[MEASURED today]`
```
SELECT now() AS a, now() AS b FROM generate_series(1,3);
→ 2026-08-15 20:17:56.264363+00  (identical in all three rows, and a = b)
```
Your current 9 rows have 9 distinct `created_at` values `[MEASURED]` because each `POST` was its own
transaction. But the moment you seed jobs with a single `INSERT ... SELECT ... generate_series` — very
tempting for Din 4's ten jobs — every row ties, and `ORDER BY created_at LIMIT 1` has **no defined
tiebreak**. Any conclusion about *which* job a worker picked becomes unfalsifiable.
Insert them one statement each, or order by `(created_at, id)`. `D-08` chose `now()` over
`clock_timestamp()` deliberately — one clock per transaction — and this tie is the other face of that
choice, not a mistake in it.

**K3 — `rowcount` is only available if you ask for it.** With `session.execute(update(...))` you get a
`CursorResult` and `.rowcount`. With ORM attribute mutation plus `commit()` there is no result object
to inspect at all. "Verify by running it" — and note that `rowcount` on a `SELECT` is not meaningful.

**K4 — `python src/worker.py` will break your imports; `python -m src.worker` from the repo root will
not.** `[INFERRED]` Running the file directly puts `src/` on `sys.path` instead of the repo root, so
`from src.models import Job` fails. `src/__init__.py` already exists, so `-m` works.

**K5 — If the worker builds its own engine instead of importing `src/database.py`, it must load the
`.env` itself.** `[INFERRED]` `DATABASE_URL` is read with `os.environ[...]` inside `database.py` after
`load_dotenv()`. Skip that and you get a `KeyError` on `DATABASE_URL`, which reads like a config
mystery and is a two-line import problem.

**K6 — Leftover rows will wreck your arithmetic.** There are **9 `pending` rows** right now
`[MEASURED]`. A worker started before Step 0's cleanup will claim all nine, oldest first, before it
ever touches the three you just enqueued. Your counts then fail to reconcile and the natural
temptation is to round the discrepancy off. Day 1's leftover `counters`/`doctors` tables are the same
lesson: a dirty bench does not fail loudly, it fails confusingly.

**K7 — `time.sleep` in the handler blocks the event loop.** `[MEASURED in Week 0 Day 1: 6.04 s vs
2.04 s]` With one worker and one job you will not notice today. You will notice in Week 4.

---

## Outputs that will look wrong and are correct

| You will see | Why it is fine |
|---|---|
| `ROLLBACK` in the echo when nothing failed | Session teardown returning the connection to the pool. Day 2's M2 measured this |
| `BEGIN (implicit)` | SQLAlchemy's log marker for the transaction starting lazily, not a statement it sent |
| `SET status=$1::VARCHAR` on a `TEXT` column | asyncpg parameter typing. The column is still `text` |
| `LIMIT $2` rather than `LIMIT 1` | Parameterised, not inlined |
| `state='idle'`, `wait_event='ClientRead'` | A backend waiting for its client. Normal, and present in Run B too |
| `Seq Scan on jobs` | Correct at 9 rows. An index would probably be ignored at this size. `P-03`, Week 4 |
| `attempts = 0` on succeeded and failed jobs | Nothing increments it in Week 1 |
| Handler prints interleaved with SQL echo | Two writers on one stdout. If it becomes unreadable, tag the worker's lines — Din 4 needs that anyway |

---

## Reading — RabbitMQ acknowledgements, and the mapping that matters

Answers to the three one-liners `[INFERRED from documentation]`:

1. **`ack` goes after the work.** An ack means "this message is dealt with, forget it". Sending it
   before the work means the broker forgets a message whose work has not happened.
2. **`auto-ack` acks on *delivery*.** So consumer death loses the message: at-most-once. It also
   removes the flow-control that unacked-message limits give you, because the broker keeps pushing.
3. **`nack` + `requeue` is an explicit return.** It also lets you distinguish *put it back* from
   *stop trying* (`requeue=false` → dead-letter exchange). Dropping the connection also causes
   redelivery of unacked messages — but only after the broker **detects** the disconnection, and it
   cannot tell slow from dead. That is Week 0 Day 5's conclusion in a different product.

**Now the mapping, which is the actual reason this reading sits on Din 3:**

| RabbitMQ | Relay today |
|---|---|
| Delivery to a consumer | Your claim (`status='running'`, committed) |
| Message in-flight, unacked | A row sitting in `running` |
| `ack` | The terminal mark (`succeeded`) |
| Broker redelivers unacked messages when a consumer's connection drops | **Nothing.** No equivalent exists |

So committing the claim before executing is **not** auto-ack — auto-ack would be marking `succeeded`
before running the handler. What you have is *manual-ack semantics without the broker's redelivery
mechanism*: the job is not deleted, and also not recoverable.

That is worth one line in your own words, because it is the day's real content:

> RabbitMQ can redeliver because it holds a connection to the consumer and notices when it breaks.
> Postgres holds a connection to my worker too, and notices — but it has no idea that connection was
> supposed to finish a job, so noticing buys nothing. Relay's replacement for "the broker noticed"
> has to be a **deadline**, not a connection, which is why the reaper is timeout-based.

---

## What must be measured, not predicted

- The exit code of an unhandled `KeyboardInterrupt` on this machine.
- Whether `SIGINT` with a custom flag-setting handler behaves as `SIGBREAK` did (measured) — same
  machinery, but not the same test.
- Your actual `rowcount` values at both the claim and the mark.
- Your `pg_stat_activity` rows for Run A and Run B, verbatim, with the worker's backend positively
  identified.
- Elapsed time from Ctrl+C to process exit, in both the mid-job and idle-polling cases.
- Whether the ORM path in **K1** is what you wrote. Read the emitted SQL; do not read your own code.
