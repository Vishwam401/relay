# Relay

A durable background job execution engine built from PostgreSQL primitives.
No Redis. No message broker. One table, three guarantees.

---

## The Contract

| # | Guarantee |
|---|---|
| 1 | An accepted job is **never lost** — API crash, DB restart, worker death |
| 2 | A side effect happens **exactly once**, even if the worker crashes five times |
| 3 | Failures **retry boundedly** — never an infinite loop |
| 4 | Attempts exhausted → **dead letter queue**, never silence |
| 5 | The system can always say **where a job is** |

---

## Architecture

```
┌─────────────────┐        ┌──────────────────────────────────┐
│   API Process   │        │          PostgreSQL               │
│                 │        │                                   │
│  POST /jobs ────┼──────► │  jobs table (status state machine)│
│  GET  /jobs/:id ◄────────┼─ id · type · payload · status    │
│                 │        │  attempts · created_at            │
└─────────────────┘        └──────────┬───────────────────────┘
                                      │
                           ┌──────────▼───────────┐
                           │    Worker Process     │
                           │                       │
                           │  claim (FOR UPDATE)   │
                           │  → execute handler    │
                           │  → mark succeeded/    │
                           │    failed             │
                           └──────────┬────────────┘
                                      │
                           ┌──────────▼───────────┐
                           │    Reaper Loop        │
                           │  (Week 2)             │
                           │  Lease expiry →       │
                           │  reset running→pending│
                           └───────────────────────┘
```

### State Machine

```
pending ──► running ──► succeeded
                  └───► failed ──► (retry) ──► dead_letter
```

Every transition is a **guarded compare-and-set**:
```sql
UPDATE jobs SET status='running'
WHERE id=$1 AND status='pending'   -- guard: only move forward
```
`rowcount = 0` means a concurrent writer changed state first. Never overwrite.

---

## Stack

```
Python 3.13  ·  FastAPI  ·  SQLAlchemy 2.0 (async)  ·  asyncpg
PostgreSQL 16  ·  Alembic  ·  Docker Compose
```

No Redis. No Celery. No RabbitMQ. PostgreSQL is the queue.

---

## Key Design Decisions

Full rationale in [`docs/DECISIONS.md`](docs/DECISIONS.md).

| Decision | Chose | Why |
|---|---|---|
| Queue backend | PostgreSQL `jobs` table | Durable by default; `COMMIT` = guaranteed delivery |
| Job ID | DB-generated `bigint` | Primary key ≠ idempotency key — kept as separate concerns |
| `status` column | `text + CHECK` | `ENUM` has no `DROP VALUE`; Alembic cannot autogenerate enum changes |
| Payload size limit | HTTP middleware | Body must be rejected *before* it is read and parsed |
| Claim transaction | Committed **before** handler runs | Holding locks across I/O = `idle in transaction`, blocking DDL |
| Status transitions | Compare-and-set + rowcount check | Only correct mechanism under concurrent writers |

---

## Empirical Findings (Measured, Not Assumed)

Every claim below was measured on this machine. Labelled `[MEASURED]` throughout [`docs/`](docs/).

- **Idle poll cost:** `BEGIN + SELECT FOR UPDATE + COMMIT` per interval — a transaction rate, not a query rate. At 2 s interval: 0.5 tx/s per worker.
- **`idle in transaction` trap:** A worker that holds its claim transaction open across a 2 s handler becomes PID 53 from `P-06` — blocking routine DDL (`ALTER TABLE`, migrations) for as long as the handler runs. Verified with `pg_stat_activity` differential (Run A vs Run B).
- **At-most-once on crash:** Today's engine delivers each job *at most once*. After the claim commits, a worker crash leaves `status = running` forever — the claim query filters on `pending`. At-least-once requires the reaper (Week 2).
- **Transition guard is load-bearing:** Manually updating a claimed job's status during the handler window produced `rowcount = 0` on the mark — the guard detected the conflict and did not overwrite.

---

## Running Locally

```bash
# 1. Start Postgres
docker compose up -d

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
alembic upgrade head

# 4. Start API
uvicorn src.main:app --reload

# 5. Start worker (separate terminal)
python -m src.worker
```

### Enqueue a job

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/jobs `
  -ContentType application/json `
  -Body '{"type":"sleep","payload":{}}'
```

### Check status

```powershell
Invoke-RestMethod http://127.0.0.1:8000/jobs/1
```

---

## Project Structure

```
src/
  main.py        # FastAPI app — POST /jobs, GET /jobs/{id}
  worker.py      # Worker loop — claim → execute → mark
  models.py      # SQLAlchemy Job model
  schemas.py     # Pydantic request/response models
  database.py    # Async engine + session factory
  middleware.py  # Payload size limit (HTTP layer)
alembic/         # Migrations
docs/
  DECISIONS.md   # Architecture Decision Records
  PROBLEMS.md    # Interesting failure modes & open questions
  LEARNING_LOG.md
  logs/          # Weekly measurement logs (WEEK_00.md, WEEK_01.md …)
labs/            # Week 0 experiments (throwaway)
tests/           # Integration tests (Week 1+)
```

---

## Roadmap

| Week | Focus | Key addition |
|---|---|---|
| ✅ Week 1 | Core engine | `jobs` table · two endpoints · worker loop · handler registry · graceful shutdown |
| Week 2 | Crash recovery | Leases · heartbeats · reaper · retries with backoff · dead letter queue |
| Week 3 | Exactly-once | Idempotency keys · deduplication · side-effect counter table |
| Week 4 | Production hardening | Rate limiting · `EXPLAIN ANALYZE` index tuning · load tests · stream-counting payload limit |

---

## Documentation

| File | Contents |
|---|---|
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Every architecture decision with rejected alternatives |
| [`docs/PROBLEMS.md`](docs/PROBLEMS.md) | Failure modes, open questions, residual gaps |
| [`docs/LEARNING_LOG.md`](docs/LEARNING_LOG.md) | Master index of weekly measurement logs |
| [`docs/logs/WEEK_00.md`](docs/logs/WEEK_00.md) | Async I/O, signals, Postgres transaction anomalies |
| [`docs/logs/WEEK_01.md`](docs/logs/WEEK_01.md) | Schema design, API, worker loop, concurrency traps |
