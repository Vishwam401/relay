# LEARNING_LOG.md — Master Index

> [!IMPORTANT]
> **This is an index only.** Detailed daily logs — measurements, code evidence,
> self-checks, and unresolved items — live in one file per week under `logs/`.

---

## 📁 Where things live

| Folder | Holds | Written |
|---|---|---|
| `planning/WEEK_NN.md` | The **plan** — what to do, experiments, checklists | Once, before the week starts |
| `logs/WEEK_NN.md` | The **log** — what happened, measured numbers, self-checks | Daily, during the week |
| `roadmap/CURRENT_WEEK.md` | Pointer to the active week | On week change |

**Plan and log are never the same file.** The plan states intent, the log states outcome.
Keeping them apart is what makes *"did the original goal get met?"* answerable later.

---

## 📚 Logs by Week

| Week | Title / Focus | Plan | Log | Status |
|---|---|---|---|---|
| **Week 0** | Systems & Concurrency Foundations (Days 1–5) | [plan](planning/WEEK_00.md) | [**log**](logs/WEEK_00.md) | ✅ Complete |
| **Week 1** | Job Engine & DB-backed Queue (`SKIP LOCKED`) | [plan](planning/WEEK_01.md) | [**log**](logs/WEEK_01.md) | 🔄 Din 1–4 done |
| **Week 2** | Durability, Leases & Reaper Design | not written | — | ⏳ Upcoming |
| **Week 3** | Idempotency & Deduplication Engine | not written | — | ⏳ Upcoming |
| **Week 4** | Rate Limiting, Backoff & Production Hardening | not written | — | ⏳ Upcoming |

---

## 🔗 Companion documents

| File | Contents |
|---|---|
| [`DECISIONS.md`](DECISIONS.md) | Architecture decisions. `D-03`..`D-08` = `jobs` schema, `D-21` = `job_executions` instrument. `D-01`, `D-02` reserved for Week 1 Din 6; `D-09`..`D-20` belong to roadmap Part 2, so Week 1 continues from **`D-22`** |
| [`PROBLEMS.md`](PROBLEMS.md) | Problem explorations, `P-01`..`P-13` |
| [`POSTMORTEMS.md`](POSTMORTEMS.md) | Others' incidents. **1 entry** — Week 0 DoD wants 2, Cloudflare still open |

---

## 🚧 Open items across all weeks

Kept here so nothing quietly disappears between weeks.

| Item | From | Status |
|---|---|---|
| `POSTMORTEMS.md` entry #2 (Cloudflare) | Week 0 DoD | Open by choice |
| Day 2's exit code `137` where arithmetic predicted `0` | Week 0 Day 2 | **Cause not identified.** Needs `Measure-Command { docker stop ... }` |
| Day 3 Exp D — `pg_stat_activity` count during pool load | Week 0 Day 3 | Never recorded |
| Day 4 Exp B — fast-fail vs slow-fail contrast | Week 0 Day 4 | **Goal never met, cause not identified.** Raw socket ruled out httpx; retry on Linux/WSL |
| Claim query index | Week 1 Din 1 (`P-03`) | To be **measured** in Week 4, not guessed |
| `ACCESS EXCLUSIVE` lock-queue hazard | Week 1 Din 1 (`D-07`) | Inference only — not measured |
| Age of the abandoned transactions | Week 1 Din 1 (`P-06`) | Upper bound inferred, not measured |
| `idle_in_transaction_session_timeout` decision | Week 1 Din 1 (`P-06`) | Belongs with pool sizing, Week 4 |
| `ACCESS EXCLUSIVE` hazard — measurement **attempted and failed** | Week 1 Din 3 | Lock granted because no live `idle in transaction` session existed at that moment. Test procedure now known |
| C6 shutdown numbers — exit code, elapsed time (mid-job and idle) | Week 1 Din 3 | Run by the user, **not recorded**. `P-10`'s idle claim is still inference from code. **Din 5 Step 4 closes this**, with the timing method stated |
| ~~`ORDER BY created_at` has no tiebreak~~ | Week 1 Din 3 | ✅ **Closed Din 4 Step 0** — claim query orders by `(created_at, id)`, and it was load-bearing for the Din 4 timeline reconstruction |
| ~~`signal.SIGBREAK` unregistered in the worker~~ | Week 1 Din 3 | ✅ **Registered** behind a `hasattr` guard. Whether `Ctrl+Break` is actually graceful is still unmeasured |
| DDIA Ch 7 second pass (pp. 233–251) | Week 1 Din 1/3 | **Deliberate slip** to Din 5, not an omission |
| Throughput comparison for `D-01` / `D-02` | Week 1 Din 4 (`P-12`) | **Not measured.** Both two-worker runs had a staggered second worker, so their splits and elapsed times are artifacts. Needs one run with a proven overlap window — Din 5 Step 5 |
| Attempt / claim identifier on `job_executions` | Week 1 Din 4 (`P-11`) | `count(*) > 1` stops meaning "duplicate" the moment Week 2 retries land. Decide **with** the retry logic, not after |
| FK and `job_id` index on `job_executions` | Week 1 Din 4 (`D-21`) | Deferred on purpose. FK's three branches all conflict with Week 4 retention; index waits for a measurement (`P-03`) |
| Crash window between claim commit and execution-row commit | Week 1 Din 4 (`D-21` Cost 4) | `[INFERRED from code]`, order-of-milliseconds. Reproducing it needs a sleep injected between the two commits |
| `rowcount = 0` branch never observed under `skip_locked` | Week 1 Din 4 | Untested code. Only observation of the branch is Din 3's `M4` |
| Stuck job 41, `running` since Din 4 | Week 1 Din 4 | **Left there on purpose** — it is Din 5's baseline and Week 2's input. Din 5 stuck counts start from 1 |
| Process/connection count before and after worker runs | Week 1 Din 4 (`P-13`) | New standing habit. Four forgotten workers claimed jobs during someone else's measurement; 3 idle connections, ~2 tx/s for zero work |
