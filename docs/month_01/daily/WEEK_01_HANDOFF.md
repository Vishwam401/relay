# Week 1 Handoff — What Stuck, What Needs Reinforcement, What Week 2 Must Not Assume

Definitions:
- **What Stuck:** Bina notes ke blank editor mein scratch se derive aur code kar sakta hoon.
- **What Needs Reinforcement:** Padhke samajh aata hai, par viva pressure mein derive karne ke liye dhyan se sochna padega.
- **What Week 2 Must Not Assume:** Jo Week 1 ne assume kiya tha par physically measure nahi kiya (Direct input to Week 2 Din 1 Problem Statement).

---

## What Stuck
- Signals physics: `SIGTERM` (catchable, graceful) vs `SIGKILL` (uncatchable, instant crash).
- Database Concurrency: `SELECT FOR UPDATE SKIP LOCKED` liveness deta hai (workers skip over locked rows without blocking).
- Compare-and-Set Guard: `UPDATE ... WHERE id=$1 AND status='pending'` with `rowcount == 1` assertions for safe state transitions (`D-06`).
- Postgres Identity vs Primary Key: Consumed sequences on rollback produce unrecoverable gaps (`P-05`), contiguity is not an invariant.

## What Needs Reinforcement
- `EvalPlanQual` (EPQ): Why PostgreSQL re-evaluates the written `WHERE` clause on the newly committed tuple rather than the application's intended transaction invariant (`P-17`).
- Write Skew vs Lost Update: Lost update mutates the same row; Write skew mutates different rows that jointly violate a global search premise.

## What Week 2 Must Not Assume
- Week 1 assumed that an in-flight worker always runs to completion or exits cleanly via `SIGTERM`. Week 2 must NOT assume workers die cleanly.
- Week 1 assumed `status='running'` means a worker is actively executing code. Week 2 must NOT assume a running row is healthy (`P-16`).
- Week 1 assumed database connections disconnect on client death. Week 2 must NOT assume dead workers release their own DB state (`P-06`).
- Week 1 assumed local timestamps and DB timestamps match. Week 2 must NOT assume clocks are synchronized across processes without explicit UTC conversion.
