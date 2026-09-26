# Week 2 Handoff — What Stuck, What Needs Reinforcement, What Week 3 Must Not Assume

Definitions:
- **What Stuck:** Rebuildable from scratch with no notes. Blank editor, nothing open.
- **What Needs Reinforcement:** Recognisable, but not derivable under viva pressure. *"haan haan ye to pata hai"* is this category's signal.
- **What Week 3 Must Not Assume:** The empirical reality and open holes left by Week 2 that Week 3 Din 1 must take as given.

---

## What Stuck

1. **Lease as a Deadline Written at Claim Time (`claimed_at`):**
   - A lease is not an active lock held in memory; it is a timestamp written to PostgreSQL heap storage during claim.
   - The Reaper evaluates expiry inside SQL: `claimed_at < now() - interval '30 seconds'`.
   - Event column (`claimed_at`) puts the lease duration policy inside the reader/reaper query rather than hardcoding a deadline in the writer.

2. **Reaper as a Dedicated Independent Process:**
   - Worker crashes (`kill -9`, power failure, kernel OOM) cannot clean up their own database state.
   - Recovery must come from an outside observer that polls on an interval and reclaims abandoned work (`running -> pending`).

3. **Compare-and-Set (CAS) on Every Status Transition:**
   - Every single status update must carry a `WHERE` guard asserting its previous expected state (e.g. `WHERE id = :id AND status = 'running'`).
   - Every CAS update must check `result.rowcount == 1`. If `rowcount == 0`, the worker must abort and discard the write to avoid state corruption.

4. **Zero-Downtime Check Constraint Updates (`NOT VALID` + `VALIDATE`):**
   - Adding a check constraint normally takes `ACCESS EXCLUSIVE` table lock across the entire table scan.
   - Zero-downtime requires two distinct transactions:
     - Migration 1: `DROP CONSTRAINT` + `ADD CONSTRAINT ... NOT VALID` (takes `ACCESS EXCLUSIVE` for ~1ms to update catalog metadata without scanning rows).
     - Migration 2: `ALTER TABLE ... VALIDATE CONSTRAINT` (takes only `SHARE UPDATE EXCLUSIVE`, scanning historical rows while allowing concurrent reads, writes, and updates).

5. **Bounded Retries with Exponential Backoff and Equal Jitter:**
   - Incrementing `attempts` on claim ensures crashing workers cannot cause unbounded retry loops (`P-01`).
   - Equal Jitter (`delay = (base / 2) + random(0, base / 2)`) breaks synchronization clusters (`P-14`).
   - The Jitter floor (`base / 2`) must strictly exceed the worker polling interval quantum (`5.0s / 2 = 2.50s > 2.0s`) to ensure 0% of the jitter distribution is masked (`P-24`).

---

## What Needs Reinforcement

1. **Dead Node vs Slow Node (The Distributed Asymmetry):**
   - A distributed system cannot distinguish a worker that has permanently crashed (`SIGKILL`) from a worker that is temporarily paused (GC pause, event loop freeze, slow database query).
   - A lease timeout is only a guess; if a slow worker resumes, it becomes a Zombie Worker.

2. **Three-Valued Logic in SQL `NULL` Comparisons:**
   - In SQL, `NULL < now()` evaluates to `UNKNOWN` (falsy in `WHERE` clauses).
   - A query `WHERE claimed_at < now() - interval '30s'` silently drops all rows where `claimed_at IS NULL`.
   - The predicate must explicitly use `(claimed_at IS NULL OR claimed_at < now() - interval '30s')`.

3. **Transaction-Start Time vs Statement Time (`now()` vs `clock_timestamp()`):**
   - In PostgreSQL, `now()` (`CURRENT_TIMESTAMP`) returns the timestamp of the **transaction start**, freezing across the entire transaction.
   - `clock_timestamp()` returns the actual real-time clock.
   - Long transactions evaluate all lease calculations against the instant `BEGIN` was executed.

4. **Fencing Tokens vs Compare-and-Set:**
   - Status values cycle (`running -> pending -> running`).
   - A CAS guard `WHERE status = 'running'` cannot distinguish Worker A's running claim from Worker B's running claim.
   - A Fencing Token is a monotonically increasing counter (Epoch / Generation) that rejects stale writes at the database layer even if the status value recurs.

5. **The Five Distinct Causes of `job_executions.count(*) > 1`:**
   - `count(*) > 1` is an append-only audit trail, not proof of a duplicate execution bug.
   - Causes by historical ID:
     1. Same-worker re-dispatch (`Job 44`)
     2. Reclaim re-execution after worker crash (`Jobs 63, 65`)
     3. Overlapping concurrent execution / Zombie Worker collision (`Job 95` — the only true duplicate)
     4. Bounded retries after handler exception (`Jobs 98–104`)
     5. Bound-crossed re-dispatch after mid-handler death on attempt limit (`Job 108`, `P-27`)

---

## What Week 3 Must Not Assume

1. **Contract #2 (Exactly-Once Side Effects) is STILL UNPROTECTED:**
   - The Reaper narrows the abandoned work window, but does NOT eliminate duplicate execution.
   - If a handler outlives its lease (or freezes), two workers will execute the same job concurrently (`Job 95`).
   - True duplicate prevention requires Week 3's Idempotency Keys and Transactional Outbox.

2. **The `attempts = 4` Overdraft Reality (`P-27`):**
   - `MAX_ATTEMPTS = 3` bounds retry *scheduling*, not dispatches.
   - If a worker dies mid-handler on attempt 3, the Reaper reclaims it, and the next claim increments to `attempts = 4` before terminalizing to `dead_letter`.

3. **Untested Shutdown-Lease Interaction:**
   - On Din 5, graceful shutdown was tested on an 8.0s handler against a 30s lease.
   - The failure mode where a shutting-down worker outlives its lease (`handler > lease`) remains `[INFERRED]` until tested with a 45s handler.

4. **Heartbeat Event-Loop Dependency (`P-21`):**
   - Heartbeat only sends updates if the handler cooperatively yields to the async event loop (`await asyncio.sleep()`).
   - For CPU-bound or synchronous blocking handlers, Heartbeat stops firing, and lease expiry will trigger duplicate claims.

5. **`P-23` is closed in mechanism and open in exercise — the week's centrepiece does not re-run as it was:**
   - `handle_sleep` / `handle_slow` now read `payload.get("seconds", default)` and that **is** committed (`399febb`).
   - But **no row in `jobs` carries a `seconds` key**, so only the default branch has ever executed `[MEASURED-R]`, and `super_slow` — the `45 s` handler that produced job 95's `14.783 s` overlap — exists in **no commit**. Jobs `93`–`96` carry that `type` with no handler behind them.
   - Two consequences Week 3 inherits: the duplicate in `D-22` Cost 2 was produced on an **uncommitted working-tree state**, and the unknown-`type` branch (which those four rows would hit if they were not all terminal) writes `failed` **without consulting `attempts`** — a second route around the retry bound.

6. **The week-close chain joined, and one row was attributed to the wrong day:**
   - Totals are exact and independently verified (`107` jobs, `94` execution rows).
   - Per-day deltas taken from the day-close reports had Din 3 and Din 4 each off by **one** row, in opposite directions, so the errors cancelled `[MEASURED 2026-08-29]`. The boundary row is `97`: created on Din 3, first dispatched on Din 4.
   - **No day's numbers are untrustworthy.** What Week 3 must not assume is the method: a per-day delta comes from a `group by` on `created_at` / `executed_at`, not from counting what the day's report claimed.
