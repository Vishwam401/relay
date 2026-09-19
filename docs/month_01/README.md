# Month 1 — archive

Closed `2026-09-11`. Everything in this folder is finished and frozen. Nothing here should be edited
except to correct a factual error, and a correction should say that it is one.

**What is not here, on purpose.** Four files are cumulative rather than month-scoped, so they stay at
`docs/` root and Month 2 keeps appending to them:

| File | Why it did not move |
|---|---|
| [`../DECISIONS.md`](../DECISIONS.md) | `D-01`–`D-29` are Month 1's. Month 2 continues from `D-30` in the same file |
| [`../PROBLEMS.md`](../PROBLEMS.md) | `P-01`–`P-47` are Month 1's. Month 2 continues from `P-48` |
| [`../LEARNING_LOG.md`](../LEARNING_LOG.md) | Master index across all months |
| [`../POSTMORTEMS.md`](../POSTMORTEMS.md) | Others' incidents plus Relay's own, not tied to a month |
| [`../MAP.md`](../MAP.md) | Symptom-to-entry index, cross-cutting |

Splitting those per month would break the numbering and the cross-references that make them useful.

---

## Reading order for a cold start

1. [`daily/WEEK_04_HANDOFF.md`](daily/WEEK_04_HANDOFF.md) — the Month 1 verdict table and the
   line-by-line DoD audit. Start here.
2. [`../../README.md`](../../README.md) — the nine-row failure matrix.
3. [`../DECISIONS.md`](../DECISIONS.md) — why each mechanism is the one that shipped.

## Contents

| Folder | What is in it |
|---|---|
| `logs/` | `WEEK_00`–`WEEK_04`. Evidence and provenance in time order. The only place that records what was measured against what was assumed |
| `planning/` | `WEEK_00`–`WEEK_04`. What each week intended, before it ran |
| `daily/week_NN/` | Per-day `BRIEF`, sealed `KEY`, `ANSWERS`, `PREDICTIONS_FROZEN`, and Week 4's `DESIGN` files |
| `daily/WEEK_NN_HANDOFF.md` | Week close: what stuck, what needs reinforcement, what the next week must not assume |
| `design/` | `SCHEMA_DECISIONS_MENTOR.md`, the Week 1 schema walkthrough |

## Weeks

| Week | Subject | Plan | Log | Handoff |
|---|---|---|---|---|
| 0 | Fundamentals: event loop, signals, pools, timeouts, isolation | [plan](planning/WEEK_00.md) | [log](logs/WEEK_00.md) | — |
| 1 | Schema, API ingress, worker claim, `D-01`/`D-02` | [plan](planning/WEEK_01.md) | [log](logs/WEEK_01.md) | [handoff](daily/WEEK_01_HANDOFF.md) |
| 2 | Lease, reaper, heartbeat, bounded retry, DLQ | [plan](planning/WEEK_02.md) | [log](logs/WEEK_02.md) | [handoff](daily/WEEK_02_HANDOFF.md) |
| 3 | Two-layer idempotency, enqueue and execute dedup | [plan](planning/WEEK_03.md) | [log](logs/WEEK_03.md) | [handoff](daily/WEEK_03_HANDOFF.md) |
| 4 | Fencing token, outbox, dispatcher, load, Month 1 close | [plan](planning/WEEK_04.md) | [log](logs/WEEK_04.md) | [handoff](daily/WEEK_04_HANDOFF.md) |

## Two things to know before quoting anything from here

**The sealed `KEY` files are answer keys.** They were written before the day ran and were opened only
after each step's measurement. Reading one out of order is the failure mode the whole protocol exists to
avoid, and `PREDICTIONS_FROZEN.md` next to it is the immutable record of what was actually predicted.

**Most of this folder is not in git.** `.gitignore` excludes `docs/daily/`, `docs/planning/`, and
`docs/roadmap/`, so only `logs/WEEK_00`–`WEEK_04.md` from this archive are tracked. That is `P-47`, it is
a scoping decision rather than an oversight, and it is still open.
