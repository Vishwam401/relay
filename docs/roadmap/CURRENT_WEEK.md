# CURRENT WEEK → Week 1

> This file is a **pointer only**. It holds no plan content of its own, so there is
> nothing here to fall out of sync. Update the two links below when the week changes.

**Current week: Week 1 — Relay Core: queue banao, at-least-once ka matlab dekho**

| What | Where |
|---|---|
| 📋 **Plan — aaj kya karna hai** | [`../planning/WEEK_01.md`](../planning/WEEK_01.md) |
| 📓 **Log — kya hua, measured numbers** | [`../logs/WEEK_01.md`](../logs/WEEK_01.md) |

**Progress:** Din 1–3 complete (schema + migration; both API endpoints; worker loop `claim → execute → mark`). Next: **Din 4 — two workers, one job: build the instrument, then break the queue**.

| Din 4 files | |
|---|---|
| 📄 **Open this** | [`../daily/DIN_04_BRIEF.md`](../daily/DIN_04_BRIEF.md) — 6 steps, prediction questions, differential verification, scope guard |
| 🔒 **Sealed** | [`../daily/DIN_04_KEY.md`](../daily/DIN_04_KEY.md) — one section per step, opened only *after* that step has been run |
| 📁 Done | [`../daily/DIN_03_BRIEF.md`](../daily/DIN_03_BRIEF.md) · [`../daily/DIN_03_KEY.md`](../daily/DIN_03_KEY.md) |

> **Two Din 3 findings that Din 4 depends on:**
> - `LockRows` sits **below** `Limit` in the claim plan `[MEASURED]`, so a row is locked before `Limit`
>   is satisfied. That is the mechanism behind Din 4's central question.
> - `ORDER BY created_at` has **no tiebreak**, and `now()` is per-transaction. **Settle this before
>   seeding Din 4's ten jobs**, or "which job did the second worker get?" becomes unfalsifiable.
>
> **Bench note `[MEASURED 2026-08-16]`:** `jobs` holds **27 rows — 21 `succeeded`, 6 `failed`, 0
> `running`, 0 `pending`**, `attempts = 0` everywhere, `max(id) = 27`. Bench is clean; record this as
> Din 4's starting count.
>
> **Din 4 adds one table (`job_executions`, via a migration) and one query change (`SKIP LOCKED`, in
> Step 5).** Nothing else — lease, reaper, retry and `attempts` increments are all still Week 2.


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
| **Week 1** | [`planning/WEEK_01.md`](../planning/WEEK_01.md) | [`logs/WEEK_01.md`](../logs/WEEK_01.md) | 🔄 **Din 1–3 done** |
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
| [`../DECISIONS.md`](../DECISIONS.md) | Architecture decisions. `D-03`..`D-08` = schema. `D-01`, `D-02` reserved for Week 1 Din 6 |
| [`../LEARNING_LOG.md`](../LEARNING_LOG.md) | Master index into the weekly logs |
| [`../POSTMORTEMS.md`](../POSTMORTEMS.md) | Others' incidents. 1 entry so far; Week 0 DoD wants 2 |
| [`../PROBLEMS.md`](../PROBLEMS.md) | Problem explorations. `P-01`..`P-10` (`P-09` at-most-once inversion, `P-10` poll interval prices three things) |
