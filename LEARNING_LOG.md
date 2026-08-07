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

