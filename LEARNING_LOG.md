# LEARNING_LOG.md

Daily log of concepts learned, experiment numbers, stuck points, and questions.

---

## Day 1 — Async vs Blocking Execution (2026-08-06)

### 📊 Measured Numbers

- `/blocking` (3 concurrent requests)    : **6.04s** `[status: 200, 200, 200]`
- `/nonblocking` (3 concurrent requests) : **2.04s** `[status: 200, 200, 200]`

---

### 💡 What I Understood

In these two functions, I mainly understood that `time.sleep()` blocks the entire async event loop thread because the async event loop is single-threaded. What `time.sleep()` does is freeze that entire thread, no matter what other work is pending.

On the other hand, `asyncio.sleep()` does not block the thread. In this function, the request pauses and waits, and meanwhile, the same thread works on other tasks. When the waiting time is up, the same thread returns to complete that task again.

So, this is what I learned today about the main difference between `time.sleep()` and `asyncio.sleep()`.

---

### 🚧 What Blocked Me

Nothing blocked me today. The setup and concept benchmarking went smoothly.

---

### ❓ Question / Next Thought

If a synchronous database driver (like standard `psycopg2`) is used inside an async FastAPI app, will it block the event loop just like `time.sleep()`? → *(Explored in Day 3)*

---

## Day 2 — Signals & Process Death (2026-08-07)

### 📊 Measured / Observed

| Run | What I did | Handler registered? | Handler ran? | Job finished? | Exit code |
|---|---|---|---|---|---|
| 1 | `Ctrl+C` (SIGINT), abort semantics | Yes | Yes | No — abandoned mid-step | n/a (local run) |
| 2 | `Ctrl+C` (SIGINT), finish-current semantics | Yes | Yes | Yes | n/a (local run) |
| 3 | `docker stop`, job shorter than grace | Yes | Yes | Yes | **0** |
| 4 | `docker kill` | Yes | No | No | **137** |
| 5 | `docker stop`, handler commented out (PID 1) | No | No | No | **137** (not 143) |
| 6 | `docker stop`, job 30s vs 10s grace | Yes | Yes | **No — died at step 23/30** | **137** |

Run 6 log evidence — the signal arrived mid-job and the loop kept going:

```
[JOB 2] Step 22/30...
[SIGNAL] Signal 15 received! Initiating shutdown...
[JOB 2] Step 23/30...
<no "Completed successfully!", no "[SHUTDOWN]", no "[CLEANUP]">
```

---

### 💡 What I Understood

Today I learned about graceful shutdown, and the difference between `SIGTERM` and `SIGKILL`.

**SIGTERM is only a request, not a behaviour.** This was my biggest correction today. I first thought "SIGTERM finishes the current job and stops taking new ones" — but SIGTERM does not do that. Its default action is to terminate the process immediately, which looks the same as SIGKILL from outside. The "finish current job, don't take the next one" behaviour came from **my own code** — the handler, the shutdown flag, and the loop design. I proved this myself: when I commented out the handler registration, SIGTERM produced no graceful behaviour at all.

**SIGKILL cannot be caught.** No handler runs, no cleanup, no `finally` block. The process just disappears mid-work.

**"Graceful" is a design choice, not one fixed behaviour.** I tested two variants of the same handler. In the abort variant, the shutdown flag was checked *inside* the job and the in-flight job was dropped halfway. In the finish-current variant, the flag was only checked *between* jobs, so the running job completed and no new job was picked up. Same signal, same handler — completely different durability outcome. For a job engine, finish-current is the correct semantic.

**The handler does not interrupt running code.** It only sets a flag and returns. My logs prove it — `Step 23/30` printed *after* the `[SIGNAL]` line. The loop kept working because nothing forced it to stop. This connects directly to Day 1: if the process is stuck inside a long blocking call, the shutdown request just sits there and waits. Python delivers signal handlers on the main thread between bytecode instructions, so a handler can never preempt arbitrary code. So blocking code doesn't only hurt throughput, it also delays my ability to shut down cleanly.

**PID 1 inside a container has a special rule.** The first process in a container gets PID 1, and Linux protects it: if PID 1 has not registered its own handler, SIGTERM is **dropped entirely** instead of killing it. That is why Run 5 gave me `137` instead of `143` — the SIGTERM was never delivered, the process kept running, and Docker force-killed it after the grace period expired. This also means graceful shutdown is a joint property of **code and deployment**, not code alone.

**Exit codes tell me who ended the process.**
- `0` → the process exited by itself, cleanly
- `128 + signal number` → something killed it. `137 = 128 + 9` is SIGKILL.

The useful distinction is not the arithmetic, it is: *did the process choose to exit, or was it killed?*

**The most important finding (Run 6):** if the graceful shutdown period is shorter than the job execution time, SIGTERM's benefit disappears. My handler ran, the flag was set, my code politely tried to finish the current job — and it was still force-killed with the job half-done and no cleanup. So writing graceful shutdown code is not enough. It only works when **grace period ≥ max job duration**. Otherwise graceful shutdown is just a lie that looks good in the logs.

**Why this forces Week 2's design:** if a worker is SIGKILL'd, the job row stays at `status = 'running'` forever, because the worker died before it could update it. This is the architectural reason a lease + reaper is needed — something outside the worker has to detect abandoned jobs and reset them to `pending`.

---

### 🚧 What Blocked Me / Unresolved

**Windows cannot deliver a catchable SIGTERM.** `Stop-Process` calls `TerminateProcess` directly, so my handler never ran and graceful vs forceful looked identical. Only `Ctrl+C` (SIGINT) is catchable locally. I had to use Docker containers to test real POSIX `SIGTERM` (`docker stop`) vs `SIGKILL` (`docker kill`) — which is closer to production anyway.

**Run 6's exit code does not match my arithmetic.** The signal arrived after step 22, so the job needed about 7 more seconds to reach step 30. Docker's default grace period is 10 seconds, so the job should have finished at ~7s and exited with code `0`. Instead I got `137`, and the last log line is step 23 — meaning the process died 1-2 seconds after the signal, not 10.

This cannot be explained by lost log buffering, because if the job had actually completed, the exit code would have been `0` regardless of missing log lines.

I did not measure how long `docker stop` actually took, and that is exactly the measurement that would resolve this. **Open item:** re-run with `Measure-Command` and confirm what the effective grace period really was. Until then I should not claim the escalation happened at 10s — I have not verified it.

---

### ❓ Question / Next Thought

The roadmap question I need to answer, because Week 2's entire design is the answer to it:

> **If my worker dies via `kill -9`, what happens to the job state in PostgreSQL, and who or what is responsible for recovering it?**

What I can already reason: the job row would stay at `status = 'running'` forever, because the worker died before it could update the row. Nobody inside the dead process can fix it — so recovery has to come from **outside** the worker. That external thing needs a way to tell "this job is genuinely being worked on" apart from "the worker holding this job is dead", and the only evidence available is time.

→ To be designed in Week 2 (lease + reaper).

Second question, which points at tomorrow: when a worker holding an open database connection gets `SIGKILL`'d mid-transaction, what happens to that connection and to the pool? → *(Explored in Day 3)*

---

## Day 3 — File Descriptors, Sockets & Connection Pools (2026-08-08)

### 📊 Measured / Observed

Setup for all runs: 10 concurrent requests, each executing `SELECT pg_sleep(1)` — so the real DB work per request is exactly 1 second. Only the pool config changed between runs.

| Exp | `pool_size` | `max_overflow` | `pool_timeout` | Total time | Success | Failures |
|---|---|---|---|---|---|---|
| A | 2 | 0 | 30s | **5.25s** | 10 | 0 |
| B | 2 | 0 | **1s** | **1.18s** | 2 | **8** |
| C | 10 | 0 | 30s | **1.66s** | 10 | 0 |
| D | — | — | — | *not recorded* | — | — |
| E | — | — | — | *not recorded* | — | — |

**Exp A — the staircase (this is the whole lesson in one shape):**

```
REQ 02: 1.15s   REQ 01: 1.17s    ← wave 1
REQ 03: 2.17s   REQ 04: 2.17s    ← wave 2
REQ 05: 3.18s   REQ 06: 3.18s    ← wave 3
REQ 07: 4.19s   REQ 08: 4.19s    ← wave 4
REQ 09: 5.20s   REQ 10: 5.20s    ← wave 5
```

Requests completed in pairs because only 2 connections existed. Each wave is **exactly +1.01s** over the previous one.

**Exp B — exact error text (this is what shows up in production logs):**

```
QueuePool limit of size 2 overflow 0 reached, connection timed out, timeout 1.00
(Background on this error at: https://sqlalche.me/e/20/3o7r)
```

**Exp C — all 10 requests ~1.62-1.65s**, even though no request waited for a connection.

---

### 💡 What I Understood

**A TCP connection costs a file descriptor.** An fd is an OS-level resource — every open file, socket, or pipe gets one. A connection is a socket, so it consumes an fd whether or not a pool exists. The pool is not what consumes it.

**There are three separate ceilings, at three different layers.** I initially thought "the limit is whatever pool_size I set" — that was wrong. It only looked true because `pool_size=2` happened to be the smallest ceiling in my setup.

| Layer | Ceiling | Who sets it |
|---|---|---|
| My app | `pool_size` | Me (self-imposed) |
| My process (OS) | fd limit (`ulimit -n`, often 1024) | OS / container config |
| Postgres server | `max_connections` (default 100) | DB config |

**Whichever is smallest breaks first.** This matters for Relay later: if I run 10 workers each with `pool_size=20`, that is 200 connections against a `max_connections` of 100. The pool would think everything is fine, and Postgres would refuse new connections with a completely different error: `FATAL: sorry, too many clients already`. Different layer, different error, different fix. So capacity planning means keeping `workers × pool_size` below `max_connections`.

**Latency includes queue time, and that is what makes this deceptive.** REQ 10 reported **5.20s** latency, but its query was only 1 second. About **4.2s of that was spent waiting at the pool for a free connection**, and only ~1s was actual database work. From the client's side this looks like "the database is slow." From the database's side it was a 1-second job done on time.

**The error came from SQLAlchemy, not from Postgres.** The `sqlalche.me` link in the error text proves it. Those 8 failed requests never reached Postgres at all — they asked the pool for a connection, the pool started its own 1-second stopwatch (`pool_timeout=1`), the stopwatch expired, and the pool itself raised the error. The whole thing happened inside my own process, in memory. Nothing went over the network.

The practical consequence: **pool exhaustion is a client-side problem that is invisible to server-side monitoring.** During Exp B, Postgres would have shown normal CPU, an empty slow query log, a normal connection count, and nothing in its error log — while 80% of my requests were failing. This is exactly how people end up spending hours "optimising the database" when the database was never the problem.

**Pool exhaustion has three possible behaviours, and the default is the dangerous one:**

1. **Wait** — block until a connection frees up (Exp A: all 10 succeeded, just slowly)
2. **Timeout** — wait a bounded time, then error (Exp B: `pool_timeout=1`)
3. **Immediate error** — fail without waiting

The default is **wait**, and waiting is what creates the "the DB feels slow" illusion. Timeout and fail-fast are things I have to configure deliberately.

**Fail-fast makes the latency graph prettier while doing less work.** Exp B finished in 1.18s versus Exp A's 5.25s — it looks 4x faster. But it threw away 8 of 10 requests. Failed requests do not appear in latency percentiles, so a p50 metric alone would have reported this config as an improvement. **Latency must always be read together with error rate.**

The deeper version of this tradeoff: the real question is not "wait or fail" but **"can the work be lost?"** With a retry mechanism (which Relay will have), fail-fast can be better, because a waiting request can blow up an upstream timeout anyway. Without retries, fail-fast means data loss.

**Connections are created, not free — and that cost is why pools exist.** In Exp C every request took ~1.62s with zero pool waiting. The extra ~0.6s was **connection setup cost**: TCP handshake, authentication, and Postgres forking a separate backend process per connection. Exp C had to build 10 connections cold and at once. Exp A's first wave (1.15s / 1.17s) only had to build 2, so it paid only ~0.15s.

The proof that pools work is in Exp A's later waves: each one is exactly ~1.01s apart, with no setup cost at all, because the same 2 connections were reused. **A pool pays the expensive setup once and then amortises it.**

**The diagnostic I now have for "latency went up":** raise `pool_size` and observe.
- Latency improves → the bottleneck was **pool exhaustion** (the event loop was fine, requests were queueing for connections)
- Nothing changes → the bottleneck is **event loop blocking** (a sync driver freezing the thread, exactly like Day 1's `time.sleep`) — pool size is irrelevant one layer down

My own data confirms the first branch: 2 → 10 connections took total time from 5.25s to 1.66s, so my bottleneck genuinely was the pool.

**A crashed worker's connection: `idle in transaction`.** When a worker is `kill -9`'d locally, the OS closes its fds, Postgres notices immediately, and the transaction is rolled back — the connection disappears from `pg_stat_activity` right away. That fast cleanup happens *because* it was a clean local kill.

Under a network partition there is no such signal. Postgres receives no FIN, no error, nothing. The connection sits in the **`idle in transaction`** state: open, transaction begun, no query running, client already dead.

The danger is **not** data inconsistency — nothing was committed, so the data is fine. The danger is **blocking**:
- The open transaction still holds its row locks, and locks are only released when the transaction ends
- Any other transaction touching those rows blocks indefinitely
- The connection slot stays occupied, which makes pool pressure worse

The chain: *crashed worker → Postgres never learns it died → transaction stays open → row locks held → other workers block on those rows → part of the system looks frozen with no crash in any log.*

For Relay this is direct: a worker that crashes holding a lock on a job row prevents other workers from claiming that row, and they get no explanation why.

---

### 🔗 The Connecting Insight (Day 2 + Day 3 are the same problem)

- **Day 2:** how does a reaper know whether a worker is dead or just slow?
- **Day 3:** how does Postgres know whether a client is dead or just thinking (`idle in transaction`)?

Neither side can ever know the truth. No system can directly inspect another process's liveness — it can only observe signals, or the absence of them. So both problems get solved the same way:

> **Set a deadline. If no proof of life arrives before it (heartbeat, lease renewal, activity), assume death and start reclaiming.**

That is a guess, not a certainty, and it comes with a symmetric tradeoff:
- **Short deadline** → false positives. A live worker gets declared dead — exactly what happened in my Day 2 Run 6, where the job was abandoned while the worker was still working.
- **Long deadline** → slow detection. Real crashes leave locks and jobs stuck for longer.

This is the same tradeoff that becomes **lease duration** in Week 2, and it is the core subject of DDIA Ch 8. In a distributed system, *"it is dead"* can never be proven — only *"it has not said anything for this long"* can be, and decisions have to be built on that.

---

### 🧠 Self-Check (where I was wrong)

| Question | My answer | Correction |
|---|---|---|
| What does a TCP connection consume at OS level? | "the pool consumes it, limit = pool_size" | **An fd.** Pool is a self-imposed app-level limit; fd limit and `max_connections` are imposed limits underneath |
| Who threw the Exp B error? | "Postgres, because of timeout" | **SQLAlchemy's pool.** Those requests never reached Postgres — hence invisible in DB monitoring |
| Where did Exp C's extra 0.6s go? | didn't know | **Connection setup cost** (handshake + auth + Postgres backend process per connection) — and this is exactly why pools exist |
| Danger of the stuck connection state? | "inconsistency later" | Data stays consistent; the danger is **held row locks blocking other transactions**. State name: **`idle in transaction`** |

Answered correctly: the wait-vs-fail tradeoff and why error rate must accompany latency; the pool-size diagnostic for distinguishing pool exhaustion from event loop blocking; the three exhaustion behaviours (naming needed tightening).

---

### 🚧 What Blocked Me / Unresolved

**Exp D not recorded.** I did not capture `SELECT count(*) FROM pg_stat_activity WHERE datname = 'relay';` during load, so I have not verified that the server-side connection count actually matches my configured `pool_size`. Client-side config and server-side reality should be confirmed to agree, not assumed. *(Tip for the re-run: raise `pg_sleep` to 5s so there is time to run the count.)*

**Exp E not recorded.** I did not measure the sync-driver variant. The key row is sync driver at `pool_size=10` — if total time stays ~10s while the async version drops to ~1.6s, that proves the bottleneck moved from the pool to the event loop. Right now I understand this argument but have not measured it, so it is borrowed knowledge, not evidence.

**Day 2's grace period question is still open.** I still have not measured how long `docker stop` actually took in Run 6, so I cannot explain why exit code was `137` when the arithmetic predicted `0`.

---

### ❓ Question / Next Thought

If a `pool_timeout` error and a genuine Postgres `too many clients already` error both surface as "requests are failing," how would I tell them apart from logs alone — and what should Relay log at enqueue time so that this is unambiguous later?

Also: since the default pool behaviour is to wait indefinitely, what should Relay's enqueue endpoint do when the pool is saturated — wait and risk the caller timing out, or fail fast with a 503 and let the caller retry? → *decision for Week 1/Week 4 (`DECISIONS.md`)*
