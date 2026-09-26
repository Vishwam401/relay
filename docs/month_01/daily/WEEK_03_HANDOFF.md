# Week 3 Handoff — What Stuck, What Needs Reinforcement, What Week 4 Must Not Assume

Definitions:
- **What Stuck:** Rebuildable from scratch with no notes. Blank editor, nothing open.
- **What Needs Reinforcement:** Recognisable, but not derivable under viva pressure. *"haan haan ye to pata hai"* is this category's signal.
- **What Week 4 Must Not Assume:** The empirical reality and open holes left by Week 3 that Week 4 must take as given.

---

## What Stuck

1. **Two-Layer Idempotency Architecture (`D-24`):**
   - Enqueue-layer idempotency (`uq_jobs_idempotency_key`) and execute-layer idempotency (`uq_side_effects_effect_key`) solve orthogonal failure domains.
   - Enqueue dedup handles network ack loss on HTTP ingress ($|J(k_e)| \le 1$). If omitted, client retries create multiple jobs.
   - Execute dedup handles worker crashes, lease expiry, and reaper redispatches ($|E(k_x)| \le 1$). Even if a single job is created, multiple worker dispatches can occur.

2. **Database Constraint as Conflict Arbiter (`D-25`):**
   - Application-level `SELECT`-then-`INSERT` is subject to concurrency race conditions (empirically reproduced at count 2 under barrier test).
   - Linearization must occur inside PostgreSQL via a unique index.
   - `INSERT ... ON CONFLICT ON CONSTRAINT ... DO NOTHING` converts the concurrent conflict into a deterministic `rowcount = 0` no-op instead of an aborting exception.

3. **Mid-Handler Crash and Seam Mechanics:**
   - Writing the side effect and marking the terminal status in separate transactions creates a visible crash seam.
   - If a worker crashes after committing the effect but before marking terminal status, the reaper safely reclaims the job. The subsequent worker re-executes, encounters the conflict, obtains `rowcount = 0`, and completes terminal status mark without duplicating the ledger row.

4. **Fingerprint Normalization Boundary (`D-05`):**
   - Request body normalization occurs in Python application space using `sort_keys=True` and compact `separators=(',', ':')` before database insertion.
   - PostgreSQL `jsonb` storage does not perform API-level request deduplication.

---

## What Needs Reinforcement

1. **Local Atomicity vs External Side Effects:**
   - Database transactions provide ACID guarantees strictly within PostgreSQL heap pages.
   - External operations (sending emails, calling Stripe/HTTP endpoints) cannot participate in a PostgreSQL commit.
   - A committed local ledger row does not prove exactly-once external delivery.

2. **`NULL` Semantics in Unique B-Tree Indexes:**
   - Standard SQL unique constraints treat `NULL` values as distinct.
   - Multiple unkeyed rows with `NULL` effect keys or idempotency keys can coexist legally without triggering conflict resolution.

3. **Status Cycle vs Monotonic Epochs:**
   - Compare-and-set on `status = 'running'` is generation-blind because status values cycle (`running -> pending -> running`).
   - A stale worker waking up after lease reclamation can still match `WHERE status = 'running'` if a second worker has claimed the job.

4. **PostgreSQL Rollback Semantics and Sequence Gaps:**
   - Aborted transactions and unique constraint conflicts increment `jobs_id_seq` and `side_effects_id_seq`. Sequences are non-transactional and gaps are normal.

---

## What Week 4 Must Not Assume

1. **Pending Jobs at Week Close:**
   - Evidence database contains four pending jobs: `116`, `121`, `123`, `124`.
   - Jobs `116` and `121` carry idempotency keys; jobs `123` and `124` are unkeyed. Week 4 startup must account for these existing rows.

2. **Fencing and Epoch Tracking are Unbuilt:**
   - Explicit generation fencing tokens are unbuilt in the database schema.
   - Compare-and-set remains generation-blind; stale heartbeats or marks can race against fresh claims.
   - The completion endpoint timestamp `completed_at` has slipped to Week 4.

3. **Retry Attempts Overdraft:**
   - Bounded retries bound scheduling, not dispatches.
   - A job can reach `attempts = 4` (e.g., Job 108) when reclaimed at max attempts (`P-27`).

4. **Din 5 Verification Limits (Reviewer Score 6.5 / 10):**
   - Week 3 Din 5 received a review score of `6.5` / 10 because Layer B witnesses were test-side SQL implementations rather than driving the real `src.worker` loop.
   - The production path witness has slipped to Week 4 and requires a:
     `disposable DB + two real current src.worker processes + production transaction boundaries`.
   - The test-side evidence proved model safety, but production multi-process interleavings remain unverified against live workers.

5. **External Side Effects and Outbox Dispatcher:**
   - Local side-effect dedup proves local ledger safety only; external effects (HTTP/email) remain `[NO EVIDENCE]`.
   - The transactional outbox dispatcher is unbuilt and deliberately deferred to Week 4.

6. **Carried Debts and Environmental Hazards:**
   - `P-28`: Alembic targets `sqlalchemy.url` in `alembic.ini`, ignoring runtime `DATABASE_URL`. Disposable database migrations must explicitly assert connection targets.
   - `P-29`: Stored final rows cannot distinguish live recovery components from omitted tests. stdout logs must retain placement proofs before cleanup.
   - The 45 s payload shutdown test with `SIGBREAK` at T = 3 s has slipped and remains unmeasured.
