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

### 📊 Measured Numbers & Exit Codes

- `SIGINT` (Abort Semantics)        : Job abandoned mid-step when Ctrl+C pressed.
- `SIGINT` (Finish-Current Semantics): In-flight job finished completely before exit.
- `docker stop` (SIGTERM - Graceful): **Exit Code 0** `[status: clean exit within 10s grace period]`
- `docker kill` (SIGKILL - Force)   : **Exit Code 137** `[status: process killed immediately by OS, 0 cleanup]`
- Grace Timeout Exceeded (>10s job) : **Exit Code 137** `[status: escalated from SIGTERM to SIGKILL after 10s]`
- Unhandled PID 1 SIGTERM            : **Exit Code 137** `[status: Linux kernel drops unhandled signals for PID 1, causing Docker timeout escalation]`

---

### 💡 What I Understood

Today I explored POSIX signals (`SIGTERM` vs `SIGKILL`) and graceful process shutdown. `SIGTERM` (15) can be caught using signal handlers to set a shutdown flag, allowing the worker process to complete in-flight tasks before exiting cleanly with exit code 0.

However, `SIGKILL` (9) is uncatchable by design. When an orchestrator or OS issues `SIGKILL` (or when a 10s `docker stop` grace period expires), the process is forcefully killed, producing exit code 137 ($128 + 9$) without running any signal handlers, cleanup routines, or `finally` blocks.

If a worker is killed via `SIGKILL`, jobs in PostgreSQL remain stuck in `running` state indefinitely. This forms the architectural necessity for Week 2's **Lease Reclaimer / Reaper Engine** to detect timed-out stuck jobs and reset them back to `pending`.

Furthermore, blocking calls delay signal handler execution because Python signal handlers execute on the main thread between CPython bytecode instructions. Thus, blocking code degrades both throughput and shutdown-ability.

---

### 🚧 What Blocked Me

Windows `Stop-Process` invokes `TerminateProcess` directly without delivering catchable `SIGTERM` signals. Using Docker containers was required to test POSIX `SIGTERM` (15) vs `SIGKILL` (9).

---

### ❓ Question / Next Thought

How will database connection pools react when a worker holding a connection gets `SIGKILL`'d mid-transaction? → *(Explored in Day 3)*

---


## Day 2 — Signals & Process Death (2026-08-08)

### 📊 Measured / Observed

| Run | What I did | Handler registered? | Handler ran? | Job finished? | Exit code |
|---|---|---|---|---|---|
| 1 | `docker stop` (job shorter than grace) | Yes | Yes | Yes | **0** |
| 2 | `docker kill` | Yes | No | No | **137** |
| 3 | `docker stop`, handler commented out | No | No | No | **137** (not 143) |
| 4 | `docker stop`, job 30s vs 10s grace | Yes | Yes | **No — died at step 23/30** | **137** |

Run 4 log evidence — the signal arrived mid-job and the loop kept going:

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

**The handler does not interrupt running code.** It only sets a flag and returns. My logs prove it — `Step 23/30` printed *after* the `[SIGNAL]` line. The loop kept working because nothing forced it to stop. This connects directly to Day 1: if the process is stuck inside a long blocking call, the shutdown request just sits there and waits. So blocking code doesn't only hurt throughput, it also delays my ability to shut down cleanly.

**PID 1 inside a container has a special rule.** The first process in a container gets PID 1, and Linux protects it: if PID 1 has not registered its own handler, SIGTERM is **dropped entirely** instead of killing it. That is why Run 3 gave me `137` instead of `143` — the SIGTERM was never delivered, the process kept running, and Docker force-killed it after the grace period expired.

**Exit codes tell me who ended the process.**
- `0` → the process exited by itself, cleanly
- `128 + signal number` → something killed it. `137 = 128 + 9` is SIGKILL.

The useful distinction is not the arithmetic, it is: *did the process choose to exit, or was it killed?*

**The most important finding (Run 4):** if the graceful shutdown period is shorter than the job execution time, SIGTERM's benefit disappears. My handler ran, the flag was set, my code politely tried to finish the current job — and it was still force-killed at step 23 with the job half-done and no cleanup. So writing graceful shutdown code is not enough. It only works when **grace period ≥ max job duration**. Otherwise graceful shutdown is just a lie that looks good in the logs.

---

### 🚧 What Blocked Me / Unresolved

**Run 4's exit code does not match my arithmetic.** The signal arrived after step 22, so the job needed about 7 more seconds to reach step 30. Docker's default grace period is 10 seconds, so the job should have finished at ~7s and exited with code `0`. Instead I got `137`, and the last log line is step 23 — meaning the process died 1-2 seconds after the signal, not 10.

This cannot be explained by lost log buffering, because if the job had actually completed, the exit code would have been `0` regardless of missing log lines.

I did not measure how long `docker stop` actually took, and that is exactly the measurement that would resolve this. **Open item:** re-run with timing and confirm what the effective grace period really was.

---

### ❓ Question / Next Thought

The roadmap question I need to answer, because Week 2's entire design is the answer to it:

> **If my worker dies via `kill -9`, what happens to the job state in PostgreSQL, and who or what is responsible for recovering it?**

What I can already reason: the job row would stay at `status = 'running'` forever, because the worker died before it could update the row. Nobody inside the dead process can fix it — so recovery has to come from **outside** the worker. That external thing needs a way to tell "this job is genuinely being worked on" apart from "the worker holding this job is dead", and the only evidence available is time.

→ To be designed in Week 2 (lease + reaper).
