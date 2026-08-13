# POSTMORTEMS.md

Weekly incident postmortems and external system failure analyses.

---

## Incident 01 — Buttondown Database Connection Exhaustion

- **What Broke:** New incoming HTTP requests failed to acquire database connections, causing cascading timeouts and 500 errors across the application.
- **Root Cause:** Application hit configured database connection pool ceiling (`pool_size` + `max_overflow`). Connection queue timed out under sudden load spike.
- **Key Takeaway:** Connection pool exhaustion looks like "Database is slow/down" to end-users, but the database engine itself is healthy — the application layer ran out of connection handles.
- **Relay System Fix:** Configure explicit pool timeouts (`pool_timeout`), separate read/write pools, and monitor active connection metrics (`pg_stat_activity`).


## Buttondown — Database Connection Exhaustion (Week 0, Day 3)

**Source:** [Buttondown incident 0024](https://buttondown.com/blog/incident-0024)
*Summary paraphrased; see source for the full writeup.*

**What broke:** New requests could not acquire a database connection, so they failed or hung. From the outside the application looked like it had a slow or failing database.

**Root cause:** The configured connection ceiling was reached. There were no connections left to hand out, so incoming work had nowhere to go — the database itself was not the failing component.

**What I learned:** Connection exhaustion impersonates database slowness. The symptom (requests taking long or failing) points at the database, but the actual constraint sits in the application's connection layer. Debugging in the wrong layer is the default failure mode here.

**Evidence from my own experiments the same day:** I reproduced this shape locally with `pool_size=2` and 10 concurrent 1-second queries.
- Total time was **5.25s** for work that was only 1 second deep, because requests queued for connections. REQ 10 reported **5.20s latency for a 1s query** — roughly **4.2s of pure waiting**.
- With `pool_timeout=1` the failures surfaced as `QueuePool limit of size 2 overflow 0 reached, connection timed out` — thrown by **SQLAlchemy, not Postgres**. Those requests never reached the database, which means Postgres-side monitoring would have shown a perfectly healthy database while 8 of 10 requests failed.
- Raising `pool_size` to 10 dropped total time to **1.66s**, confirming the pool was the bottleneck.

**What this means for Relay:**
1. I have never consciously chosen a `pool_size` — it has always been a default I ignored. That is an unowned failure mode. → future `DECISIONS.md` entry.
2. `workers × pool_size` must stay under Postgres `max_connections` (default 100), otherwise the failure moves to a different layer with a different error (`FATAL: sorry, too many clients already`) and a different fix.
3. Latency alone cannot detect this. Relay's observability needs **error rate and pool wait time** alongside latency, because a fail-fast config makes latency graphs look *better* while dropping work.
4. Enqueue needs a deliberate saturation policy — wait, or reject with 503 and let the caller retry. Silent waiting is the default, and defaults are how incidents like this happen.

**Still to verify:** I have not yet confirmed with `pg_stat_activity` that my configured pool size matches the actual connection count on the server side, and I have not read the full writeup closely enough to capture their detection and remediation timeline. Both are follow-ups.
