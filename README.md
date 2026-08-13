# Relay — Durable Job Execution Engine & AI Infrastructure Gateway

`Relay` is a zero-data-loss background job execution engine built on PostgreSQL with lease-based crash recovery and idempotency guarantees.

## Structure

```
relay/
  docs/
    DECISIONS.md     # Architecture Decision Records (ADR)
    LEARNING_LOG.md  # Master Index of learning logs
    POSTMORTEMS.md   # Incident postmortems
    PROBLEMS.md      # Interesting problem explorations
    logs/            # Modular weekly learning logs (WEEK_00.md...)
  labs/              # Week 0 L0 experiment scripts
  relay/             # Core application package (from Week 1)
  tests/             # Integration and Property-based tests
  docker-compose.yml # Infrastructure setup (Postgres)
  requirements.txt   # Python dependencies
```
