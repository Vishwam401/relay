# CURRENT WEEK → Week 1

> This file is a **pointer only**. It holds no plan content of its own, so there is
> nothing here to fall out of sync. Update the two links below when the week changes.

**Current week: Week 1 — Relay Core: queue banao, at-least-once ka matlab dekho**

| What | Where |
|---|---|
| 📋 **Plan — aaj kya karna hai** | [`../planning/WEEK_01.md`](../planning/WEEK_01.md) |
| 📓 **Log — kya hua, measured numbers** | [`../logs/WEEK_01.md`](../logs/WEEK_01.md) |

**Progress:** Din 1–4 complete (schema + migration; both API endpoints; worker loop `claim → execute → mark`; `job_executions` instrument + `FOR UPDATE SKIP LOCKED`). Next: **Din 5 — `kill -9` mid-job: make a job disappear, then prove nobody can find it**.

| Din 5 files | |
|---|---|
| 📄 **Open this** | [`../daily/DIN_05_BRIEF.md`](../daily/DIN_05_BRIEF.md) — 7 steps, prediction questions, differential verification, scope guard |
| 🔒 **Sealed** | [`../daily/DIN_05_KEY.md`](../daily/DIN_05_KEY.md) — one section per step, opened only *after* that step has been run |
| 📁 Done | [`../daily/DIN_03_BRIEF.md`](../daily/DIN_03_BRIEF.md) · [`../daily/DIN_03_KEY.md`](../daily/DIN_03_KEY.md) · [`../daily/DIN_04_BRIEF.md`](../daily/DIN_04_BRIEF.md) · [`../daily/DIN_04_KEY.md`](../daily/DIN_04_KEY.md) |

> **Three Din 4 findings that Din 5 depends on:**
> - The execution row is written **after the claim commits and before the handler runs** `[MEASURED]`,
>   so a job killed mid-handler already has its evidence row. That row is what Din 5 inspects.
> - **Job 41 has been stuck in `running` since Din 4** — set by a lock probe, not a crash. Din 5's
>   stuck-count arithmetic must **start from 1**.
> - Both Din 4 "two worker" runs had a **staggered** second worker, so their splits and elapsed times
>   are start-time artifacts (`P-12`). Din 5 Step 5 starts three workers from one command and reports
>   the **overlap window**, which is also what `D-01`/`D-02` still need.
>
> **Bench note `[MEASURED 2026-08-17, Din 4 close]`:** `jobs` holds **58 rows — 49 `succeeded`, 8
> `failed`, 1 `running` (job 41), 0 `pending`**, `attempts = 0` everywhere, `max(id) = 58`.
> `job_executions` holds **30 rows** (`max(id) = 30`, next id `32`), with one duplicate pair on job 44.
> **0 worker processes running** — check this before every run; Din 4 lost a measurement to four
> forgotten workers (`P-13`).
>
> **Din 5 adds one slow handler and nothing else.** Reaper, lease/`claimed_at`, retry and `attempts`
> increments are all still Week 2 — today's stuck job *is* Week 2's problem statement.


---

## File layout convention

One rule, so nothing gets misfiled again:

| Folder | Holds | Written |
|---|---|---|
| `docs/planning/WEEK_NN.md` | The **plan** — what to do, experiments to run, checklists | Once, before the week starts |
| `docs/logs/WEEK_NN.md` | The **log** — what actually happened, measurements, self-checks | Daily, during the week |
| `docs/roadmap/` | Long-range reference + this pointer | Rarely |

> **Plan and log are never the same file.** The plan states intent; the log states outcome.
> Keeping them separate is what makes it possible to ask "did the original goal get met?"
> six months later — which is a required question in the reviewer rules.

---

## Week status

| Week | Plan | Log | Status |
|---|---|---|---|
| Week 0 | [`planning/WEEK_00.md`](../planning/WEEK_00.md) | [`logs/WEEK_00.md`](../logs/WEEK_00.md) | ✅ Complete (1 open item: `POSTMORTEMS.md` entry #2) |
| **Week 1** | [`planning/WEEK_01.md`](../planning/WEEK_01.md) | [`logs/WEEK_01.md`](../logs/WEEK_01.md) | 🔄 **Din 1–4 done** |
| Week 2 | not written | — | ⏳ Durability, leases, reaper |
| Week 3 | not written | — | ⏳ Idempotency, dedup |
| Week 4 | not written | — | ⏳ Rate limiting, backoff, hardening |

---

## Reading rules (unchanged)

| File | Status | Why |
|---|---|---|
| This file + current week's plan | ✅ Open daily | Tells you today's work |
| `BACKEND_ROADMAP.md` (Part 1) | ✅ 1–2× per week | Context and reference |
| `BACKEND_ROADMAP_PART2.md` | 🔒 **CLOSED** | Do not open until Month 1 ends. It will only cause overwhelm. |

---

## Supporting documents

| File | Contents |
|---|---|
| [`../DECISIONS.md`](../DECISIONS.md) | Architecture decisions. `D-03`..`D-08` = schema, `D-21` = the `job_executions` instrument. `D-01`, `D-02` reserved for Week 1 Din 6. **New Week 1 numbers continue from `D-22`** — `D-09`..`D-20` belong to roadmap Part 2 |
| [`../LEARNING_LOG.md`](../LEARNING_LOG.md) | Master index into the weekly logs |
| [`../POSTMORTEMS.md`](../POSTMORTEMS.md) | Others' incidents. 1 entry so far; Week 0 DoD wants 2 |
| [`../PROBLEMS.md`](../PROBLEMS.md) | Problem explorations. `P-01`..`P-13` (`P-09` at-most-once inversion, `P-10` poll interval prices three things, `P-11` the instrument's expiry date, `P-12` the concurrency that never happened, `P-13` orphan workers contaminate measurements) |
