# MAP.md — index and threads

**Layer: cross-cutting.** This file holds **no new knowledge**. It is an index into the three
files that do, plus the connections between them that none of those files can structurally contain.

## What each file is for, so you stop asking this file to be them

| File | Its job | Ask it |
|---|---|---|
| `DECISIONS.md` | ADR. Why X was chosen, what was rejected, what it costs, when to revisit | *"I am about to change this column / endpoint — what did I already decide and why?"* |
| `PROBLEMS.md` | Failure-mode catalog. One entry per edge case, with what is measured vs inferred | *"I have this symptom — has it already been characterised?"* |
| `logs/WEEK_NN.md` | Evidence and provenance, in time order. What was measured, what was guessed, what was corrected | *"Is this claim trustworthy, and who established it?"* |
| **`MAP.md`** (this) | Index + recurring patterns. Pure cross-reference | *"Where do I look?"* and *"how does this connect to the rest?"* |

**Honest limit of this file.** Reading it produces *recognition*, not recall. It is a lookup tool
for when you already have a symptom or a component in hand. It is not a substitute for a cold,
closed-book test — that is a separate exercise, and the distinction is the one recorded in the
Week 1 Day 1 log (*recognisable, not recallable*).

**Maintenance rule.** When a new `D-` or `P-` entry lands, add a row here. When an entry is
amended, update the row. This file rots the moment it stops being a pure index — so never copy
reasoning into it, only pointers.

---

# Index A — symptom → mechanism → entry

Read left to right. The middle column is the thing to say out loud; the right column is where the
evidence lives.

## Hangs and freezes

| Symptom | Mechanism | Entry |
|---|---|---|
| Something is frozen, **no error anywhere, nothing in any log** | An abandoned transaction is holding row locks. `pg_stat_activity`: culprit is `idle in transaction` / `Client`; victim is `active` / `Lock` / `transactionid`. Monitoring intuition is inverted — the idle one is doing the damage | `P-06`, W0 D5 Exp 3, W0 D3 |
| Postgres never cleans up the culprit | It will not, by default. Needs `idle_in_transaction_session_timeout`. `[MEASURED]` — sessions survived days | `P-06` |
| `DROP TABLE` / `ALTER TABLE` hangs | DDL needs `ACCESS EXCLUSIVE`, which queues behind existing row locks — and then **every subsequent read and write queues behind the DDL**. Wait shows as `Lock` / `relation`, a different name from `transactionid` | `P-06`, `D-07` |
| Fix cannot come from inside | None of the blocked sessions can act, and the culprit does not know it is one. Resolution was `pg_terminate_backend` from outside. Same shape as a crashed worker needing an external reaper | `P-06`, W0 D2 |
| Timeout is configured and the request still hangs forever | A per-phase read timeout bounds the **gap between chunks**, not the request's lifetime. A server dribbling one byte every 0.4s against a 0.5s read timeout never trips it. Needs a separate total deadline | W0 D4, `P-02` |

## Latency, pools, and the event loop

| Symptom | Mechanism | Entry |
|---|---|---|
| Latency is up, but DB metrics look completely normal | Pool exhaustion. The error is raised **inside your own process** by SQLAlchemy's pool — those requests never reached Postgres, so server-side monitoring shows nothing. The `sqlalche.me` link in the text is the tell | W0 D3 Exp B |
| Reported latency far exceeds the query's real cost | Latency includes queue time. `[MEASURED]` 5.20s reported on a 1s query — ~4.2s was waiting at the pool | W0 D3 Exp A |
| Raise `pool_size` → latency improves | The bottleneck **was** the pool. `[MEASURED]` 2→10 connections: 5.25s → 1.66s | W0 D3 |
| Raise `pool_size` → **nothing changes** | The bottleneck is one layer below: the event loop is blocked. `[MEASURED]` sync driver 10.02s at pool 2 → 10.03s at pool 10, a 0% change | W0 D3 R1, W0 D1 |
| Blocking call inside async code | Single-threaded event loop freezes for everyone. `[MEASURED]` 3 concurrent requests: 6.04s blocking vs 2.04s non-blocking. A large `json.loads` is this | W0 D1, `P-08` |
| Latency graph improved and something feels wrong | Fail-fast drops work, and failed requests do not appear in latency percentiles. `[MEASURED]` Exp B finished 4x faster and threw away 8 of 10 requests. **Latency is only readable next to error rate** | W0 D3 |
| Which limit actually bit? | Three ceilings at three layers — app `pool_size`, OS fd limit, Postgres `max_connections`. Smallest breaks first, and each gives a different error at a different layer | W0 D3 |
| First requests slower than later ones at the same pool size | Connection setup cost — TCP handshake, auth, Postgres forking a backend per connection. `[MEASURED]` ~0.6s to build 10 cold vs ~0.15s for 2. That amortisation is why pools exist | W0 D3 Exp C |

## Process death and shutdown

| Symptom | Mechanism | Entry |
|---|---|---|
| Graceful-shutdown code exists and the process still got force-killed | Grace period < job duration. `[MEASURED]` signal at step 22/30, died at step 23, exit `137`. Graceful shutdown requires **grace period ≥ max job duration**, otherwise it is a lie that looks good in logs | W0 D2 Run 6 |
| Exit `137` where `143` was expected | PID 1 in a container with **no registered handler** has SIGTERM dropped entirely, so the process survives until Docker force-kills it. Graceful shutdown is a joint property of code **and** deployment | W0 D2 Run 5 |
| Exit code reading | `0` = it chose to exit. `128 + n` = something killed it (`137` = `128+9`, SIGKILL). The useful question is *chose or was killed*, not the arithmetic | W0 D2 |
| Signal arrived, handler ran, loop kept going | A handler cannot preempt running code. It sets a flag and returns; Python delivers handlers between bytecode instructions. `[MEASURED]` `Step 23/30` printed **after** `[SIGNAL]` | W0 D2 |
| Shutdown observed up to a full poll interval late | The loop sleeps the whole interval in a single `await` and checks the flag only at the top. Fix is sliced sleep or an `asyncio.Event` | `P-10` |
| SIGKILL leaves no cleanup | Uncatchable. No handler, no `finally`. Anything the process owed is now owed by something outside it | W0 D2, `P-09` |

## Retries and duplicate side effects

| Symptom | Mechanism | Entry |
|---|---|---|
| Is this retry safe? | The failure type decides, and only the failure type. **connect timeout = pahuncha nahi** (nothing happened, safe). **read timeout = pata nahi** (delivered, response lost, may duplicate). A retry is not added reliability — it is a decision to risk duplicate work for a chance at completion | `P-01`, W0 D4 |
| After a read timeout, which was it? | The information does not exist on your side. So safety cannot come from the sender; the receiver has to be idempotent | `P-01`, `P-07` |
| Client retried a `POST` and got two legitimate jobs | The window is **everything after `COMMIT`** — serialisation, socket write, process staying alive. Not just the network: an `await db.refresh()` after commit had the same shape with no network involved. Removing it **narrowed** the window; nothing closes it | `P-07` |
| Retry budget arithmetic looks fine and the last attempt is useless | Total is `attempts × timeout + sum(backoff)`, not `attempts × timeout`. Once the parent's timeout has passed, the remaining attempts only burn CPU and connections | W0 D4 |
| "Slow" vs "down" cannot be told apart | TCP silently retransmits; the application layer is never told a loss happened. Both look like delay. So a timeout is a **deadline guess, not a measurement** | W0 D4 |
| A timeout fires but does not stop the work | `[MEASURED, hypothesis REJECTED]` The original 2.172s-on-a-0.5s-timeout was **not** deferred cancellation — with a 10s server the abort came at 0.505s. The likely cause was `__aexit__` blocking on the server's response during teardown, `[INFERRED]`, two variables changed in that run | W0 D4 R4, `P-02` |

## Transactions, isolation, and locks

| Symptom | Mechanism | Entry |
|---|---|---|
| Counter reads 101 where 102 was expected, **no error** | Lost update at Read Committed. Read Committed uses a **separate snapshot per query**, so the `SELECT` saw a value the `UPDATE` then overwrote. It prevents dirty writes, not lost updates | W0 D5 Exp 1 |
| Same experiment, other levels | `[MEASURED]` `FOR UPDATE` → 102, T2 **blocked** (no error). `REPEATABLE READ` → `40001`, PostgreSQL detects lost update and aborts (MySQL's does not) | W0 D5 Exp 1, R2 |
| A business rule broke, every individual write was legal, **no error** | Write skew. The rule was never expressed to the database — it lived in an application `if`. `[MEASURED]` Read Committed → 0 on call, `REPEATABLE READ` → **also 0** | W0 D5 Exp 2 |
| Why `REPEATABLE READ` did not save it | Snapshot isolation takes **no read locks** — *readers never block writers* is its whole design. Nothing to conflict on when two transactions write different rows | W0 D5 |
| `ERROR: could not serialize access … Canceled on identification as a pivot` | SERIALIZABLE (SSI) detected a dangerous read-write dependency and aborted the **pivot** — the second committer. First-committer-wins, and it is not fair: under contention the same long transaction keeps losing | W0 D5 |
| Choosing SERIALIZABLE | `HINT: might succeed if retried` is a contract. It means committing to retry logic — which reopens `P-01`'s question of whether the retry is safe | W0 D5, `D-02` (reserved) |
| The conflicting row does not exist yet, so there is nothing to lock | Phantom. Three exits: SERIALIZABLE, materialising conflicts (DDIA calls it *ugly* — concurrency control leaks into the data model), or a unique constraint | W0 D5 |
| `FOR UPDATE` "enforced" the rule | It did not. It **refreshed the read**; the application `if` then made the call. SERIALIZABLE is the version where the database decides. Same outcome, two different mechanisms — do not merge them | W0 D5 |
| Two workers both claim one job | Mechanism is lost update; **consequence is duplicate execution**, and the damage is outside the database (email sent twice). DB state looks perfectly correct — both wrote `running` | W0 D5 |
| `SKIP LOCKED` is not enough | Once the claim **commits**, no lock exists. Lease expiry cannot stop a live-but-slow worker, so a reaper's requeue produces two executions that are both legal | W0 D5, `P-09`, `P-02` |
| Second worker frozen in front of a locked row | `Lock` / `transactionid`. `[MEASURED]` with a 6s lock held on the oldest pending row: `SKIP LOCKED` worker began real work at **1.25s**; plain `FOR UPDATE` waited the full **6s**. Cost: the skipped row is deferred, so FIFO gets more approximate | W1 D4, `P-05` |
| `SKIP LOCKED` prevents duplicates | It does not. `FOR UPDATE` plus the compare-and-set guard already did. `[MEASURED]` two workers claimed different rows **6 ms apart**, no duplicate. What `SKIP LOCKED` removes is *waiting*, not duplication | W1 D4, `D-02` (reserved) |
| `EXPLAIN` shows `LockRows` **below** `Limit` | The lock is taken before the limit is satisfied, so a blocked worker is waiting inside a query that has not yet decided which row it wants | W1 D3 |

## Constraints, schema, and migrations

| Symptom | Mechanism | Entry |
|---|---|---|
| A `CHECK` exists and the rule is still violated | The invariant did not fit in one row at one instant. A constraint cannot see the worker's handler registry, cannot see the row's **previous** value, and cannot aggregate across rows | `P-04`, `D-04`, `D-06` |
| Illegal state transition, all constraints satisfied | `UPDATE jobs SET status='running' WHERE id=1` on a `succeeded` row passes every constraint. Enforcement is the compare-and-set: `... WHERE id=$1 AND status='pending'` **plus checking the affected row count**. The `AND` is the guard, not an optimisation | `D-06`, `P-04` |
| Enum value chosen wrong | `DROP VALUE` does not exist at all. And Alembic does not autogenerate enum value changes, so `--autogenerate` runs, detects nothing, and gives a false all-clear. `[MEASURED]` the *other* common argument is false on PG 16 — `ALTER TYPE … ADD VALUE` **does** run in a transaction block; the value just cannot be used until that transaction commits | `D-06` |
| Does `ADD COLUMN … DEFAULT` rewrite the table? | `[MEASURED]` on 50,000 rows via `pg_class.relfilenode`: constant default → **no** rewrite (24660 unchanged); volatile default like `clock_timestamp()` → **yes** (24665). The real hazard is the `ACCESS EXCLUSIVE` **lock queue**, which is `[INFERRED]`, not measured. Mitigate with `lock_timeout` | `D-07` |
| A counter never increments / retries never bound | `NULL + 1 = NULL`. A nullable `attempts` stays NULL forever, `attempts >= max_attempts` is never true, retries run forever — silently. **Counters, flags and states are never nullable** | `D-07` |
| `ORDER BY created_at` gives ties, or the wrong order | `now()` is **transaction start** time, and `id` assignment order is not commit order. Assignment happens at statement time; visibility at commit. No column can record an event that happens after the row is written | `P-05`, `D-03`, `D-08` |
| So what is Relay's ordering? | **Best-effort FIFO, not guaranteed.** Acceptable because ordering is not one of the five contract promises. Every ordered query needs a tiebreaker: `ORDER BY created_at, id` | `P-05` |
| Ties within one transaction | Correct, not a defect — those rows became real at the same instant. `clock_timestamp()` would invent an ordering with no business meaning, which is fake precision and therefore worse | `D-08` |
| `timestamp` vs `timestamptz` | `timestamptz` stores an unambiguous instant (as UTC; it does **not** remember the zone). With three processes and a reaper doing `now() - created_at`, `timestamp` makes that arithmetic silently wrong — a live job declared dead is duplicate execution with no error raised. Zero cost, both 8 bytes | `D-08` |
| Who supplies the timestamp | The database, because there is exactly one of it. Application-generated means multiple clocks in the one column the claim query orders by. Week 2's lease rests on this: *whose clock decides expiry?* | `D-08`, W0 synthesis |

## API layer

| Symptom | Mechanism | Entry |
|---|---|---|
| Oversized body returns `413` sometimes and `422` other times | The size check ran **after** the body was buffered and parsed. `[MEASURED]` the proof was `loc: ["body", 306274]` — the JSON parser had reached character 306,274. FastAPI reads and parses the body while resolving parameters, before the function body, so not even a `Depends` guard is early enough. Fix: HTTP middleware | `P-08`, `D-05` amendment |
| Two checks disagreeing | Middleware bound plus a Pydantic validator gave different status codes for the same oversized request. One enforcement point now; the validator was removed | `D-05` amendment |
| The limit does not protect against an attacker | It reads `Content-Length`, which the **sender controls** — absent under `Transfer-Encoding: chunked`, optional in HTTP/2, and the check is skipped when missing. Threat model is an honest client that made a mistake. Deliberately unfixed until Week 4; the eventual stream-counting fix also overshoots by one chunk | `P-08` |
| The DB column is still unbounded | The limit constrains **one entry point**, not the column. `psql` inserts bypass it entirely, and Din 4/5 are `psql`-driven | `P-08`, `D-05`, `D-04` |
| Why `GET /jobs/{id}` returns so little | Not I/O. `[MEASURED reasoning]` PostgreSQL is a row-store reading whole 8 KB pages, so adding `type` or `created_at` is near-free; only the TOAST dereference is saved by excluding `payload`. The real reason is **adding a response field is backward-compatible, removing one is breaking** — so minimal is the reversible start | `D-05` amendment |
| Guessable ids | `D-03` accepted them: an unguessable id is obscurity, not security, and the real fix is authorization. Excluding `payload` **narrows** exposure; it does not eliminate it — `404` vs `200` still reveals which ids exist | `D-03`, `D-05` amendment |

## Worker and instrument

| Symptom | Mechanism | Entry |
|---|---|---|
| Job stuck in `running` forever; restarts do not help | The claim committed (it must, or the worker becomes `P-06`'s culprit), which released every protection. Nothing watches `running`, and the claim query filters `status='pending'`. `[MEASURED]` job 41 sat `running` for an hour, invisible to all of Relay | `P-09`, `P-06` |
| Week 1 is titled at-least-once and delivers at-most-once | The absence of duplicates is not engineered safety — it is the symptom of having no recovery. Nothing puts a job back, so nothing can run it twice | `P-09` |
| Contract #1 and #2 look independent | They are not. **Every route to satisfying "never lost" after a crash creates the "never duplicated" risk.** Duplicate execution is the *price* of recovery, which is why Week 2 must precede Week 3 | `P-09` |
| Unregistered job `type` | `[MEASURED]` claimed once, marked `failed` once, worker returned to polling — no hot loop, no crash, nothing else affected. The claim is consumed deliberately; the alternative (`running → pending`) is Week 2's reaper transition | `D-04` amendment, W1 D3 |
| The real cost of app-level type validation | A **deployment ordering** mistake — worker rolled out before its handler is registered — becomes permanent for those rows instead of self-healing, and burns every retry attempt into the DLQ for a reason unrelated to the job. Nothing in the DB can enforce that ordering | `D-04` amendment |
| Job `failed` but **no** row in `job_executions` | The instrument records **handler dispatch**, not claims and not completions. `[MEASURED]` job 57 (`boom`, handler raises) → row; job 58 (`does_not_exist`, no handler) → no row. Both look identical in `jobs` | `P-11`, `D-21` |
| Why the row is written before the handler, in its own transaction | Evidence must not share a fate with the thing it is evidence about. Written at mark time, a worker killed mid-handler leaves no trace; written in the mark's transaction, a failed mark rolls back the proof it ran. The **disagreement** between the two tables is the diagnostic | `D-21` |
| `count(*) > 1` as a duplicate test | Has an expiry date. Week 2's retry legitimately writes a second row, and the query then silently starts meaning something else. Fix is a column — attempt number or claim id — decided **with** the retry logic, not after | `P-11` |
| Orphan rows in the instrument | `[MEASURED]` no FK, so `job_id = 999999` inserted fine. The FK is deferred, not forgotten: its three branches all hurt until a retention policy exists — plain FK blocks the delete, `CASCADE` deletes the audit trail with its subject, `SET NULL` orphans by design | `D-21` |
| An idle fleet's cost | `[MEASURED]` the idle poll is a **full transaction** per poll (`BEGIN` / `SELECT … FOR UPDATE` / `COMMIT`), 0.5 tx/s per worker at a 2s interval, each a `Seq Scan`. Load scales with **worker count × 1/interval**, not job count. Four strays = 3 idle connections and ~2 tx/s for zero work | `P-10`, `P-13` |
| Poll interval is not one knob | It prices three things at once: DB load, enqueue-to-start latency, **and shutdown latency**. The binding constraint is external: **poll interval ≤ shutdown budget**, and the budget is set by whoever runs the container (Docker's default grace is 10s) | `P-10` |
| "Two workers, 0 duplicates" | `[MEASURED]` both Din 4 runs had the second worker start **+10.1s** and **+24.3s** late, so the splits are start-time artifacts and the `SKIP LOCKED` run had essentially one worker. A zero means nothing until the run proves two were competing | `P-12` |
| Jobs executed by a worker you did not start | `[MEASURED]` four workers outlived their experiment by 38 minutes, still polling and claiming. Connections to `relay` dropped 4 → 1 when killed. The symptom was **not an error** — it was a plausible measurement with the wrong `worker_id` in it | `P-13` |
| "How many workers are running?" | Relay cannot answer. `worker_id` is a self-chosen PID string, so it collides across hosts, and a restarted process gets a new identity while its stranded row keeps the old one. Week 2's reaper must reason about liveness with no roster | `P-13` |

---

# Index B — decision → cost → what triggers a revisit

| Entry | Chose | The cost that actually landed | Revisit when |
|---|---|---|---|
| `D-03` `jobs.id` | DB-generated `bigint` identity | Ordering is not guaranteed (`P-05`); door to client-generated ids closed; ids leak approximate volume | Multi-region id generation, or a client needs the id before the round-trip |
| `D-04` `jobs.type` | unconstrained `text`, validation in the app | Typos reach the DB (`[MEASURED]` visible and contained); no single place lists valid types; **deploy-ordering hazard is the real bill** | Week 4 needs per-type config → lookup table brings validation for free |
| `D-05` `jobs.payload` | `jsonb NOT NULL DEFAULT '{}'` | Byte-exact input unrecoverable (breaks payload signing forever); slightly costlier insert; TOAST on large values | A signed payload needs verification, or Week 4 measures real payload sizes |
| `D-05` amendment (ingress) | 266,240-byte body bound in **middleware**, `413` | Rests on a sender-controlled header (`P-08`); DB column still unbounded; the number is a judgement, not a measurement | Week 4 hardening, or non-API write paths start mattering |
| `D-05` amendment (egress) | `GET` returns `{job_id, status}` only | Nothing costly — `404` vs `200` still leaks existence. Kept minimal for **response-surface reversibility** | A consumer needs `type` / `created_at` (near-free to add) |
| `D-06` `jobs.status` | `text` + `CHECK`; transitions by compare-and-set | **Illegal transitions are prevented only where the guard is written.** Any future `status` update without a `WHERE` on the old value bypasses it, and the DB will not remind you | `dead_letter` in Week 2 → `NOT VALID` + `VALIDATE CONSTRAINT` |
| `D-07` `jobs.attempts` | added in Week 1, `NOT NULL DEFAULT 0` | An unused column for a week; its **update policy** (increment at claim or at failure) is still undecided | Week 2 retry logic |
| `D-08` `jobs.created_at` | `timestamptz NOT NULL DEFAULT now()`, DB-generated | Not true FIFO either (`P-05`); ties guaranteed within a transaction; enqueue cannot be attributed to an API instance | Per-instance latency attribution is ever needed |
| `D-21` `job_executions` | append-only, written before the handler, own transaction, no FK, no index | Records dispatch not claims (`[MEASURED]`); `count(*)>1` expires with retries; orphans accepted (`[MEASURED]`); a crash in the claim→record gap under-counts (`[INFERRED]`) | Week 2 retries force an attempt/claim id; Week 4 retention forces the FK question |
| `D-01` *reserved* | Postgres vs Redis vs RabbitMQ | Cost field partly collected: polling is 1 tx per worker per interval; an idle fleet is not free. **Still missing** a clean throughput comparison | Din 6, after a clean concurrency run |
| `D-02` *reserved* | `FOR UPDATE SKIP LOCKED` vs `SERIALIZABLE` | **Not writable yet.** The mechanism half is measured (`SKIP LOCKED` removes waiting, not duplicates). The throughput half is not — `P-12`. `SERIALIZABLE` was never run at all | A run with a **proven overlap window** exists |

**Numbering:** `D-09`..`D-20` belong to the Month 2–4 roadmap; `D-01`/`D-02` are reserved. New Week 1
decisions continue from `D-21`. Grep before assigning a number — collisions have happened twice.

---

# Index C — component → everything that touches it

| Component | Entries |
|---|---|
| `jobs.id` | `D-03`, `P-05` (ordering), `D-05` amendment (guessable ids + egress) |
| `jobs.type` | `D-04` + Din 3 amendment, `P-04`, `P-11` (unregistered type leaves no execution row) |
| `jobs.payload` | `D-05` + Din 2 amendment, `P-08`, `P-07` (payload hash as idempotency key) |
| `jobs.status` | `D-06`, `P-04`, `P-09`, W0 D5 (lost update / two-worker analysis) |
| `jobs.attempts` | `D-07`, `P-11` (attempt number needed on the instrument) |
| `jobs.created_at` | `D-08`, `P-05`, `P-03` (composite index candidate) |
| `job_executions` | `D-21`, `P-11`, `P-12` (its `executed_at` is what caught the bad experiment), `P-13` (its `worker_id` is what caught the strays) |
| Claim query | `P-03` (index, Week 4), `P-05` (tiebreak), `D-06` (the guard), W1 D3 (`LockRows` below `Limit`), W1 D4 (`SKIP LOCKED`) |
| `POST /jobs` | `P-07`, `P-08`, `D-05` amendment, W1 D2 |
| `GET /jobs/{id}` | `D-05` amendment (egress), `D-03` (enumeration) |
| Middleware | `P-08`, `D-05` amendment |
| Worker loop | `P-09`, `P-10`, `P-06` (do not hold the claim transaction), W0 D2 (shutdown), `P-13` (strays) |
| Handler registry | `D-04` + amendment, `P-04`, `P-11` |
| Poll interval | `P-10`, `D-01` (reserved) |
| Connections / pool | W0 D3, `P-13`, `P-06` (`idle_in_transaction_session_timeout`, Week 4) |
| Shutdown | W0 D2, `P-10`, deferred: `SIGBREAK` on Windows (Week 2) |

---

# Threads — the patterns that run across days

This is the part no other file can hold, because each thread spans several days and several files.
These are the questions an interview actually probes, and the reason your Week 0 work is load-bearing
rather than background.

## T1 — The name promises more than the mechanism delivers

| Mechanism | What the name suggests | What it actually does |
|---|---|---|
| `SIGTERM` | terminates gracefully | **Requests** termination. Default action is immediate death. Graceful behaviour is entirely your handler — proved by commenting it out |
| `timeout=0.5` | this will not exceed 0.5s | Bounds one phase. A read timeout bounds the **gap between chunks**, so a dribbling server hangs forever |
| `REPEATABLE READ` | stronger than snapshot isolation | Is snapshot isolation. Takes **no read locks**. DDIA: *"nobody really knows what repeatable read means"* |
| `CHECK` constraint | enforces a rule | Constrains a **value**, in one row, at one instant. Cannot see the previous value or other rows |
| `Content-Length` limit | bounds request size | Bounds it **for senders who volunteer the header** |
| `bigserial` "monotonic" | order is reliable | Monotonic in **assignment**, not in **visibility**. A queue needs the second one |

**The move:** never reason from the name. Ask what the mechanism literally does, then ask what it
cannot see. `P-04` is the sharpest form of this: a **partial** constraint is worse than none, because
the confidence is real and the protection is not, and the middle position is where the bug lives.

## T2 — No process can observe another's true state; deadlines are the only substitute

Four days, four costumes, one problem:

| Day | The question that cannot be answered |
|---|---|
| W0 D2 | is the worker dead, or slow? |
| W0 D3 | is the client dead, or thinking? (`idle in transaction`) |
| W0 D4 | is the network down, or slow? (TCP retransmits silently) |
| `P-05` | was this row created earlier, or committed earlier? |
| `P-13` | how many workers are alive? — Relay cannot answer at all |

**The only remedy is a deadline** — timeout, lease, heartbeat, TTL — and a deadline is a **guess**
with a symmetric cost that cannot be escaped:

- **Short** → false positives. A live worker declared dead → duplicate execution. W0 D2 Run 6 is this, measured.
- **Long** → slow detection. Locks held, pool slots occupied, the system degrades quietly.

Two consequences that are already load-bearing:

1. **Recovery must come from outside.** Nothing inside a stuck thing can act, and the culprit does not
   know it is one. `P-06` needed `pg_terminate_backend`; a SIGKILLed worker needs a reaper.
2. **`P-02` closes the loop:** a timeout bounds intent, not reality. So the reaper cannot *stop* the
   first worker — only outrun it. That is Week 2's central question and Week 3's justification.

> System design here is not about finding a correct setting. It is about **choosing which risk to
> accept**: false-positive duplicate execution, or slow-failure resource starvation.

## T3 — Placement decides whether a check is real or decorative

Not "weak check" — **decorative**. It runs, it returns the right status, and it prevents nothing.

- `413` inside the handler ran after 306 KB was buffered and parsed. `loc: ["body", 306274]` is the
  receipt. `[MEASURED]` before and after.
- Two independent limits (middleware + validator) disagreed, so the status code for an oversized body
  depended on whether the body happened to be **valid**.
- The Day 2 checklist item *"over-limit payload → 413"* **passed** against a limit that protected nothing.

**Two rules, and the second is the harder one:**

1. For each check: *what wrong implementation would also pass this?* If the answer is "a broken one",
   the check is decorative. Prefer **differential** checks — one oversized request could not tell the
   two implementations apart; three could.
2. For each experiment: *what would produce this same result if the phenomenon never occurred?*
   For "two workers, 0 duplicates" the answer is "one worker" — which is exactly what happened
   (`P-12`). A negative result must first prove the condition it was testing existed.

## T4 — Commit buys visibility and sells protection

The same ordering creates a guarantee in one place and removes one in another.

| | Before `COMMIT` | After `COMMIT` |
|---|---|---|
| `POST /jobs` (W1 D2) | row not durable, caller not promised anything | row durable → contract #1 holds. **But** everything after commit — serialisation, socket write, staying alive — is outside the transaction's protection → `P-07` |
| Worker claim (W1 D3) | row locked, nobody else can take it. **But** the worker is `P-06`'s culprit, holding locks across a sleep | `running` is visible to everyone including `GET`. **But** nothing guards it → `P-09` |

Din 2's lesson is *commit, then tell the caller.* Din 3 cannot use it, and that is not a bug to fix —
it is Week 2's problem statement. W0 D5 already contained the conclusion: once the claim commits,
no lock exists, so `SKIP LOCKED` can do nothing about a lease-expiry double execution.

## T5 — Silent wrongness has two different root causes, and the fix differs

| Root cause | Example | What to do |
|---|---|---|
| **The promise was smaller than you assumed** | Read Committed prevents dirty writes, not lost updates. The DB kept its word; the assumption was wrong | Read what the mechanism actually guarantees, then measure it |
| **The rule was never expressed to it** | No constraint on `doctors`. Two legal boolean flips. Nothing for Postgres to object to | Put the rule somewhere that can see it — or accept that it lives in the app and write the guard |

Compressed, from your own log: *Exp 1 = the promise was smaller than I assumed. Exp 2 = the rule was
never in the database at all.*

Both recur in Relay. `D-04`: the DB cannot see the handler registry. `D-06`: the DB cannot see the
row's previous value. **Diagnostic question when nothing errored:** *did the mechanism promise less
than I assumed, or was the rule never expressed to it?*

## T6 — The invariant's scope decides where enforcement can live

This is the single most reusable table in the project.

| Invariant spans | Constraint can hold it? | Example | Where enforcement actually lives |
|---|---|---|---|
| one column, one row | ✅ | `UNIQUE(username)`, `UNIQUE(idempotency_key)` | database |
| one row, one instant | ✅ | `CHECK (status IN …)`, `attempts NOT NULL` | database |
| **two versions** of one row | ❌ | `succeeded → running` is illegal | compare-and-set: `UPDATE … WHERE status='pending'` **+ affected-row-count check** |
| an aggregate **across** rows | ❌ | at least one doctor on call | `SERIALIZABLE`, or `FOR UPDATE` + application `if` |
| rows that **do not exist yet** | ❌ | no overlapping booking (phantom) | `SERIALIZABLE`, materialising conflicts, or a unique constraint |
| state **outside** the database | ❌ | a handler is registered; the email was already sent | app registry; idempotent side effect at the boundary |

Bottom two rows are why Week 3 exists: double execution's damage happens **outside** the database, so
no isolation level can prevent it. Isolation governs database state only.

## T7 — An instrument is not neutral: it has a blind spot and a shelf life

| The instrument | Its blind spot | Its expiry |
|---|---|---|
| `job_executions` | records **handler dispatch** — not claims, not completions (`[MEASURED]` jobs 57 vs 58) | `count(*)>1` stops meaning "duplicate" when Week 2 retries land |
| `worker_id` | a self-chosen PID, collides across hosts, changes on restart | Week 2 needs a real identity |
| Day 4 timing harness | measured client teardown as well as the network | fixed in R3 — 1.707s → 1.002s |
| A quiz auto-scored "3/3 PERFECT" | one question was answered `idk` | corrected in the log rather than left standing |

**The payoff, and it is concrete:** `executed_at` is the only reason `P-12` was catchable — a column
added to answer question A let a finished experiment be re-interrogated and its central claim
withdrawn. `worker_id` is the only reason `P-13` was catchable; without it the stray workers' jobs
would have reconciled perfectly and the conclusion would have been quietly about a different fleet.

> **Timestamps and identities on evidence rows are cheap, and they let you audit a run that is
> already over.** Also: state an instrument's meaning in words before trusting its numbers.

---

# Trust ledger — what is actually established

Keep this distinction. It is not a score; it is whether a claim can be leaned on.

**`[MEASURED]` on this machine, with output recorded**
Blocking vs non-blocking (6.04s / 2.04s) · signal non-preemption (step 23 after `[SIGNAL]`) ·
PID 1 dropping SIGTERM (`137`, not `143`) · pool staircase and exhaustion (5.25s / 1.18s / 1.66s) ·
pool error origin (SQLAlchemy, not Postgres) · sync-driver blocking (10.02 → 10.03, 0%) ·
clean connect timeouts (1.002s / 1.006s) · deferred-cancellation hypothesis **rejected** (0.505s) ·
lost update at Read Committed (101) / `FOR UPDATE` (102) / `REPEATABLE READ` (`40001`) ·
write skew at RC and RR (0) / SERIALIZABLE (pivot abort) / RC + `FOR UPDATE` (1) ·
`pg_stat_activity` roles (culprit idle, victim active) · abandoned sessions blocking `DROP TABLE` ·
enum `ADD VALUE` inside a transaction on PG 16 · `ADD COLUMN` rewrite by `relfilenode` (24660 / 24665) ·
the `413` triple and the parser offset · unregistered type claimed once then failed ·
idle poll = one transaction per poll · instrument coverage (job 57 row, job 58 none) ·
orphan insert accepted · `SKIP LOCKED` 1.25s vs `FOR UPDATE` 6s · two claims 6 ms apart ·
staggered worker starts (+10.1s / +24.3s) · four stray workers, connections 4 → 1

**`[INFERRED]`, and must not be quoted as measured**
The `ACCESS EXCLUSIVE` lock-queue hazard (`D-07`) · the shutdown-latency half of `P-10` ·
the claim→record under-count gap (`D-21` Cost 4) · `P-07`'s duplicate window (the *ordering* is
measured; no duplicate was produced) · the explanation for the original 2.172s (`W0 D4 R4`, two
variables changed) · most of `D-03`..`D-08`'s PostgreSQL reasoning beyond the two verified claims

**Borrowed — read, not derived. Highest re-test priority.**
The six schema decisions `D-03`..`D-08` carry a written provenance note saying so. Also flagged in
the logs: the drip-server trap, timeout budget arithmetic, TCP retransmission as the reason slow and
down are indistinguishable, the unified deadline pattern, phantoms and why `FOR UPDATE` cannot
attach a lock, why a unique constraint solves usernames but not doctors, and why row-level detection
misses write skew (**this last one failed twice**).

**Known-false things recorded so they are not re-learned**
`SIGTERM` finishing the current job by itself · Read Committed fixing lost update ·
`FOR UPDATE` raising `40001` (it blocks; `40001` is SERIALIZABLE's) ·
`REPEATABLE READ` taking read locks · Postgres killing `idle in transaction` by default ·
"adding a column with a default rewrites the table" (false for a constant default on PG 16) ·
"you cannot add an enum value in a transactional migration" (false on PG 12+) ·
deferred cancellation of in-flight I/O (rejected by measurement)

---

# Open ledger — what is unanswered, and who owns it

| Open question | Owner | Entry |
|---|---|---|
| Which index does the claim query need — composite, partial, or none? | Week 4, by `EXPLAIN ANALYZE` | `P-03` |
| A clean two-worker run with a **proven overlap window** | before `D-01` / `D-02` can be written | `P-12` |
| `SERIALIZABLE` for the claim — never run | `D-02` | W0 D5 |
| Who mints the idempotency key, what the dedup window is, and what a duplicate receives (`202` with the original id, or `409`) | Week 3 | `P-07` |
| Where the dedup check belongs — enqueue or execute | Week 3 | W0 D5 |
| Reaper deadline wrong in the *safe-looking* direction: live-but-slow worker, lease expires, two legal executions | Week 2 | `P-09`, `P-02` |
| Attempt number vs claim id on `job_executions` — must be decided **with** the retry logic | Week 2 | `P-11` |
| Worker identity: host+PID, startup UUID, or a `workers` table with a heartbeat | Week 2 | `P-13` |
| `idle_in_transaction_session_timeout` as a deliberate setting | Week 4, with pool sizing | `P-06` |
| Stream-level body limit, independent of `Content-Length` (and record its own overshoot) | Week 4 | `P-08` |
| FK + index on `job_executions.job_id` — needs a retention policy first | Week 4 | `D-21` |
| `LISTEN`/`NOTIFY` as a push mechanism, with polling still needed as a backstop | Month 2 at the earliest | `P-10` |
| Starvation of a job enqueued inside a long transaction | unplanned, recorded not fixed | `P-05` |
| What strict FIFO would actually cost | deliberately unresolved | `P-05` |
| `SIGBREAK` registration on Windows | Week 2 | `D-21` deferred table |
| DB-level `CHECK (length(type) <= 100)` | Week 4 | `D-04` Cost 3 |
| Exp B's fast-fail vs slow-fail contrast — never reproduced, cause unidentified | someday, on Linux/WSL | W0 D4 |
| W0 D3 Exp D — `pg_stat_activity` count during pool load, never recorded | short, unowned | W0 D3 |
| W0 D2 — why `docker stop` escalated to `137` in ~1-2s instead of 10s | short, unowned | W0 D2 |
| Should an unregistered type write an execution row? | recorded, not designed | `P-11` |
| Is `413` even the right answer, or should the API point callers at object storage? | contract question | `P-08` |
