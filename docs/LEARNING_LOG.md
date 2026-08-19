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
| **Week 1** | Job Engine & DB-backed Queue (`SKIP LOCKED`) | [plan](planning/WEEK_01.md) | [**log**](logs/WEEK_01.md) | 🔄 Din 1–6 done · Din 7 = review checkpoint |
| **Week 2** | Durability, Leases & Reaper Design | not written | — | ⏳ Upcoming |
| **Week 3** | Idempotency & Deduplication Engine | not written | — | ⏳ Upcoming |
| **Week 4** | Rate Limiting, Backoff & Production Hardening | not written | — | ⏳ Upcoming |

---

## 🔗 Companion documents

| File | Contents |
|---|---|
| [`DECISIONS.md`](DECISIONS.md) | Architecture decisions. **`D-01` and `D-02` written on Din 6** — Postgres-as-queue, and the two-part claim. `D-03`..`D-08` = `jobs` schema, `D-21` = `job_executions` instrument. `D-09`..`D-20` belong to roadmap Part 2, so Week 2 continues from **`D-22`** |
| [`PROBLEMS.md`](PROBLEMS.md) | Problem explorations, `P-01`..`P-18`. Next free: **`P-19`** |
| [`POSTMORTEMS.md`](POSTMORTEMS.md) | Others' incidents. **1 entry** — Week 0 DoD wants 2, Week 1 DoD wants 3. Cloudflare still open |

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
| DDIA Ch 7 second pass (pp. 233–251) | Week 1 Din 1/3/5/6 | **Slipped a fourth time** — now Din 7. Two corrections to earlier framing: (i) Ch 7 does **not** name the dead-versus-slow problem in `P-16`; that is **Ch 8, "The Trouble with Distributed Systems"** — stop looking for it in Ch 7. (ii) Ch 7 **does** name Din 6's variant-1 failure: **lost update**, with compare-and-set as one of the standard remedies, which is `D-06`'s guard. So Din 6 produced the textbook disease for a remedy Relay already shipped |
| Throughput comparison for `D-01` / `D-02` | Week 1 Din 4 (`P-12`) → Din 5 | ⚠️ **`P-12` repaid; the comparison still not made.** Din 5 gave a clean *baseline* for `SKIP LOCKED` — proven overlap, 4/4 split, 0 duplicates, 32.2 s vs 32 s predicted. There is still no like-for-like run of plain `FOR UPDATE`, `SERIALIZABLE`, or advisory locks. **`D-02` must not claim a throughput result**; use Din 4's lock-wait figure (1.25 s into a 6 s lock vs the full 6 s) |
| ~~Option (c) `UPDATE ... WHERE status='pending' RETURNING`~~ | Week 1 Din 6 (`D-02`) | ✅ **Closed Din 6, and the answer is a distinction rather than a verdict: option (c) is not broken — the naive form of it is.** Two live `psql` sessions, session 1 uncommitted. `WHERE id = (subquery)` → session 2 **blocked**, then returned **the same id** with `rowcount = 1`: a silent duplicate claim, and the row's final state is indistinguishable from one correct claim. Adding `AND status='pending'` → `rowcount = 0`, safe. `FOR UPDATE SKIP LOCKED` in the subquery → no blocking, **next** id. So (c)-with-guard is a sound single-statement claim; what it gives up is that the loser of a race gets nothing instead of doing useful work. `D-02`'s Rejected line now says that |
| ~~`EvalPlanQual` protects concurrent writers~~ | Week 1 Din 4 → corrected Din 6 (`P-17`) | ⚠️ **Din 4 learned the wrong lesson from a happy accident.** EPQ rechecks **the predicate you wrote**, not the invariant you meant. `EXPLAIN` `[R]` shows the uncorrelated subquery compiled to an `InitPlan` constant, so the outer qual is `Filter: (id = $0)` with `status` absent — and the recheck therefore passes. Variants 1 and 2 are the same mechanism producing opposite outcomes. Also: DDIA Ch 7 names variant 1 a **lost update** and names compare-and-set as the remedy Relay already uses |
| Step 2 — the five written Week 2 answers | Week 1 Din 5 → Din 6 → **Din 7** | 🔴 **Third slip, and the highest-priority open item in the project.** The reaper's predicate using only today's columns and why it fails; the smallest schema addition and the new failure it creates; job 41 vs 63; a lease shorter than the slowest handler. **Deliberately not written for him** — the value is in naming which column is missing and what adding it breaks, and reading that as prose produces recognition rather than recall. `P-16` has the sub-decisions, `D-01` Cost 1–3 has the framing. **Week 2 Din 1 should not start before this exists in his own words** |
| Job 75 is a landmine for Week 2's fixture | Week 1 Din 6 (`M11`, `[R]`) | **New, and it goes off on its own.** Job 75 is `pending` with `type='send_receipt'`, which is **not** in the worker's `REGISTRY`. The next worker start claims it, marks it `failed`, and writes **no** execution row — `pending 4 → 3`, `failed 8 → 9`, and a **fourth** fixture shape appears. Not fixed because the fix is a choice: deleting it breaks the Case A reconciliation, retyping it falsifies the log. **Din 7 Step 0 decides deliberately.** `P-13`'s shape at row level rather than process level |
| Sequence gap at 79 | Week 1 Din 6 (`M10`, `[R]`) | **First gap in `jobs_id_seq`.** A reviewer probe rolled back an `INSERT`, which consumed the value permanently. `jobs` = 78 rows, `max(id) = 78`, `last_value = 79`, so **the next enqueue is id 80.** Reproduces Din 2's M16, so `P-05`'s first half now rests on two measurements. Week 2's reconciliation arithmetic needs to know |
| Conflict path costs a full poll interval | Week 1 Din 6 (`D-02` Cost 5) | `[INFERRED from code]`. In `run_worker()` the `rowcount == 0` branch leaves `claimed_job` as `None`, which falls through to `asyncio.sleep(POLL_INTERVAL_SECONDS)` — so a worker losing a claim race waits **2 s** even when other `pending` rows are free. Step 6 makes `rowcount = 0` a demonstrated outcome, but it has still never been observed **in the worker**. Cheap to change; not changed in Week 1 |
| `CURRENT_WEEK.md` and `CHAT_HANDOFF.md` are untracked | Week 1 Din 6 | `[MEASURED]` `.gitignore` excludes `docs/roadmap/`, `docs/daily/`, `docs/planning/` and `*CHAT_HANDOFF*`. Deliberate and it keeps the repo clean — but **the two documents a cold reader opens first have no history**, while everything they point into does. BRIEFs and KEYs do not need version control; the pointer arguably does. Din 7 Step 8 |
| A check that cannot fail | Week 1 Din 6 (`P-18`) | **Third instance in six days, first where the flaw was in the *design* rather than the reporting.** Din 6's own Case B never inserted a job, so its sequence reading distinguished nothing — and the BRIEF that contains that check opens by restating the rule it broke. **Carry-forward is mechanical, not a maxim:** for every Part C check write the output if the mechanism is present and the output if it is absent, and if the two lines match, rewrite the check |
| Which mechanism made Din 5's 4 µs claims safe | Week 1 Din 5 (`P-14`) → Din 6 | 🟡 **Still `[INFERRED]`, and Din 6 did not settle it** — Step 6 ran in `psql`, not in the worker, so it priced the two halves separately without saying which one fired in Din 5's convoy. This is now the **last `[INFERRED]` in `D-02`**, and it is ~10 minutes of work: re-run the convoy, capture worker stdout, grep for the `rowcount=0` conflict line. **Zero** occurrences alongside a clean split ⇒ `SKIP LOCKED` did the work and the guard is a backstop. **Any** occurrence ⇒ both mechanisms are live. Either answer is publishable; the current state is the only one that is not. Din 7 Step 3 |
| Does the convoy survive unequal handler durations? | Week 1 Din 5 (`P-14`) | **Open.** One run with alternating 8 s / 2 s handlers would answer it and give `SKIP LOCKED` a more honest workload. Week 4 |
| Poll-interval jitter | Week 1 Din 5 (`P-14`) | **New question, not a fix.** First measured evidence that lockstep is real (4 µs, three consecutive rounds). Trade-off: jitter costs latency to reduce contention that `SKIP LOCKED` already handles cheaply. Week 4 |
| Attempt / claim identifier on `job_executions` — **possibly needed earlier than the roadmap assumes** | Week 1 Din 4 (`P-11`) → Din 6 | `count(*) > 1` stops meaning "duplicate" the moment Week 2 retries land. Din 6 adds the first evidence that the ordering may be wrong: Step 6 produced a duplicate claim that **`jobs` cannot record at all** (the row's final state is identical to one correct claim), so `job_executions` is the only place it would have shown — two rows, one `job_id`. The instrument that would catch it expires in the same week that introduces the reaper, i.e. the second writer to `status`. **`D-22`-shaped question: does the identifier need to exist *before* the reaper rather than *with* the retry logic?** |
| FK and `job_id` index on `job_executions` | Week 1 Din 4 (`D-21`) | Deferred on purpose. FK's three branches all conflict with Week 4 retention; index waits for a measurement (`P-03`) |
| Crash window between claim commit and execution-row commit | Week 1 Din 4 (`D-21` Cost 4) | `[INFERRED from code]`, order-of-milliseconds. Reproducing it needs a sleep injected between the two commits |
| `rowcount = 0` branch — **observed, but not in the worker** | Week 1 Din 4 → Din 5 → Din 6 | ⚠️ **Half closed.** Din 6 Step 6 variant 2 produced `rowcount = 0` on demand in `psql` — the **first observation in the project**, after Din 1 called the guard load-bearing and Din 4/Din 5 both recorded the branch as never having fired (Din 5's two workers claimed 4 µs apart without provoking it). The **worker's** `rowcount == 0` branch is still unexecuted code, and Cost 5 above is why that matters |
| Crash window reachable another way | Week 1 Din 5 (`P-16`) | Job **41** is `running` with **no execution row** — the state Din 4 called `[INFERRED]` and millisecond-wide. Reachable by a lock probe, so a reaper cannot dismiss it as improbable |
| Three stuck rows, two different shapes | Week 1 Din 5 (`P-16`) | **Left on purpose** — jobs **41** (no execution row), **63**, **65** (execution rows present) are Week 2's test fixture. `status='running'` is one value covering two situations that differ in whether side effects may have occurred. A reaper keyed on the execution row would silently strand 41 |
| Reaper safety depends on Week 3, not Week 2 | Week 1 Din 5 (`P-16`) | **Roadmap ordering issue worth noticing now.** Resetting job 63 may repeat side effects; nothing before Week 3 prevents that. The interim guarantee is honestly *"recovered, and possibly duplicated"* — write it down rather than discover it |
| Process/connection count before and after worker runs | Week 1 Din 4 (`P-13`) | New standing habit. Four forgotten workers claimed jobs during someone else's measurement; 3 idle connections, ~2 tx/s for zero work |
