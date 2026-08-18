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
| **Week 1** | Job Engine & DB-backed Queue (`SKIP LOCKED`) | [plan](planning/WEEK_01.md) | [**log**](logs/WEEK_01.md) | 🔄 Din 1–5 done |
| **Week 2** | Durability, Leases & Reaper Design | not written | — | ⏳ Upcoming |
| **Week 3** | Idempotency & Deduplication Engine | not written | — | ⏳ Upcoming |
| **Week 4** | Rate Limiting, Backoff & Production Hardening | not written | — | ⏳ Upcoming |

---

## 🔗 Companion documents

| File | Contents |
|---|---|
| [`DECISIONS.md`](DECISIONS.md) | Architecture decisions. `D-03`..`D-08` = `jobs` schema, `D-21` = `job_executions` instrument. `D-01`, `D-02` reserved for Week 1 Din 6; `D-09`..`D-20` belong to roadmap Part 2, so Week 1 continues from **`D-22`** |
| [`PROBLEMS.md`](PROBLEMS.md) | Problem explorations, `P-01`..`P-16`. Next free: **`P-17`** |
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
| ~~C6 shutdown numbers — exit code, elapsed time (mid-job and idle)~~ | Week 1 Din 3 | ✅ **Closed Din 5**, but `[R]`. Exit codes `0`/`0` are the user's. The elapsed times were reported as ranges (*"~5–6 s"*, *"~1–2 s"*) and had to be measured by the reviewer: **idle `1.123 s`**, **mid-job `5.167 s`**, via `SIGBREAK` + `perf_counter`. `P-10`'s idle claim is now `[MEASURED]` — the flag was observed `0.962 s` late against `0.959 s` of remaining sleep. **Re-run once yourself** so the two headline numbers stop being borrowed |
| Handler timeout — mid-job shutdown is unbounded | Week 1 Din 5 (`P-15`) | **New.** Idle shutdown is bounded by `POLL_INTERVAL_SECONDS`; mid-job is bounded by the handler, which Relay does not bound. So the graceful path becomes the crash path whenever handler duration exceeds the supervisor's grace period. Week 2, and it is **one** decision with the lease, not two |
| Week 0 Day 2's exit code `137` — now a specific hypothesis | Week 1 Din 5 (`P-15`) | `137 = 128 + 9` (SIGKILL). A handler outliving `docker stop`'s 10 s grace produces exactly this. **Not confirmed** — needs `Measure-Command { docker stop ... }` against a known handler duration |
| Completion evidence is a `print`, not a row | Week 1 Din 5 Step 1 | **Design judgement not recorded.** Din 5 measured that "handler finished but the mark was lost" and "died mid-handler" leave *identical* database state; only a terminal distinguishes them. Mirror of `D-21`. Price it with the reaper's requirements — Week 2, at `D-22` |
| ~~`ORDER BY created_at` has no tiebreak~~ | Week 1 Din 3 | ✅ **Closed Din 4 Step 0** — claim query orders by `(created_at, id)`, and it was load-bearing for the Din 4 timeline reconstruction |
| ~~`signal.SIGBREAK` unregistered / untested~~ | Week 1 Din 3 | ✅ **Fully closed Din 5** `[R]` — `SIGBREAK` delivered, handler ran in 2–3 ms, exit code `0`, no stuck job. A real `Ctrl+C` keypress (`SIGINT`) is still untimed, but every line after the flag is set is identical |
| DDIA Ch 7 second pass (pp. 233–251) | Week 1 Din 1/3/5 | **Slipped a third time** — Din 5 Step 6 was not delivered. Now Din 6 Step 8. Note: `P-15`/`P-16` are **Ch 8** territory, not Ch 7 |
| Throughput comparison for `D-01` / `D-02` | Week 1 Din 4 (`P-12`) → Din 5 | ⚠️ **`P-12` repaid; the comparison still not made.** Din 5 gave a clean *baseline* for `SKIP LOCKED` — proven overlap, 4/4 split, 0 duplicates, 32.2 s vs 32 s predicted. There is still no like-for-like run of plain `FOR UPDATE`, `SERIALIZABLE`, or advisory locks. **`D-02` must not claim a throughput result**; use Din 4's lock-wait figure (1.25 s into a 6 s lock vs the full 6 s) |
| Option (c) `UPDATE ... WHERE status='pending' RETURNING` | Week 1 Din 6 (`D-02`) | **Zero evidence of any kind.** The plan asks whether it would also work; nobody has run it. Din 6 Step 6 runs it in two `psql` sessions |
| Which mechanism made Din 5's 4 µs claims safe | Week 1 Din 5 (`P-14`) | `[INFERRED]`. `SKIP LOCKED` steering to the next row, or the compare-and-set guard firing, are both consistent with the data. Settled cheaply by capturing worker stdout during a convoy run and grepping for the `rowcount=0` conflict line — Din 5 did not capture it |
| Does the convoy survive unequal handler durations? | Week 1 Din 5 (`P-14`) | **Open.** One run with alternating 8 s / 2 s handlers would answer it and give `SKIP LOCKED` a more honest workload. Week 4 |
| Poll-interval jitter | Week 1 Din 5 (`P-14`) | **New question, not a fix.** First measured evidence that lockstep is real (4 µs, three consecutive rounds). Trade-off: jitter costs latency to reduce contention that `SKIP LOCKED` already handles cheaply. Week 4 |
| Attempt / claim identifier on `job_executions` | Week 1 Din 4 (`P-11`) | `count(*) > 1` stops meaning "duplicate" the moment Week 2 retries land. Decide **with** the retry logic, not after |
| FK and `job_id` index on `job_executions` | Week 1 Din 4 (`D-21`) | Deferred on purpose. FK's three branches all conflict with Week 4 retention; index waits for a measurement (`P-03`) |
| Crash window between claim commit and execution-row commit | Week 1 Din 4 (`D-21` Cost 4) | `[INFERRED from code]`, order-of-milliseconds. Reproducing it needs a sleep injected between the two commits |
| `rowcount = 0` branch never observed under `skip_locked` | Week 1 Din 4 → Din 5 | Still untested code, and Din 5 made it more interesting: two workers claimed **4 µs apart** and it still did not fire. Din 6 Step 6 variant 2 provokes it deliberately in `psql` |
| Crash window reachable another way | Week 1 Din 5 (`P-16`) | Job **41** is `running` with **no execution row** — the state Din 4 called `[INFERRED]` and millisecond-wide. Reachable by a lock probe, so a reaper cannot dismiss it as improbable |
| Three stuck rows, two different shapes | Week 1 Din 5 (`P-16`) | **Left on purpose** — jobs **41** (no execution row), **63**, **65** (execution rows present) are Week 2's test fixture. `status='running'` is one value covering two situations that differ in whether side effects may have occurred. A reaper keyed on the execution row would silently strand 41 |
| Reaper safety depends on Week 3, not Week 2 | Week 1 Din 5 (`P-16`) | **Roadmap ordering issue worth noticing now.** Resetting job 63 may repeat side effects; nothing before Week 3 prevents that. The interim guarantee is honestly *"recovered, and possibly duplicated"* — write it down rather than discover it |
| Process/connection count before and after worker runs | Week 1 Din 4 (`P-13`) | New standing habit. Four forgotten workers claimed jobs during someone else's measurement; 3 idle connections, ~2 tx/s for zero work |
