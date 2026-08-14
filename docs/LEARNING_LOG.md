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
| **Week 1** | Job Engine & DB-backed Queue (`SKIP LOCKED`) | [plan](planning/WEEK_01.md) | [**log**](logs/WEEK_01.md) | 🔄 Din 1 done |
| **Week 2** | Durability, Leases & Reaper Design | not written | — | ⏳ Upcoming |
| **Week 3** | Idempotency & Deduplication Engine | not written | — | ⏳ Upcoming |
| **Week 4** | Rate Limiting, Backoff & Production Hardening | not written | — | ⏳ Upcoming |

---

## 🔗 Companion documents

| File | Contents |
|---|---|
| [`DECISIONS.md`](DECISIONS.md) | Architecture decisions. `D-03`..`D-08` = `jobs` schema. `D-01`, `D-02` reserved for Week 1 Din 6 |
| [`PROBLEMS.md`](PROBLEMS.md) | Problem explorations, `P-01`..`P-06` |
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
