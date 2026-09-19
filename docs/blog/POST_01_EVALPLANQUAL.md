A common way to claim a background job in PostgreSQL is a single `UPDATE` with a subquery that picks the oldest pending row. It is one statement, so it looks atomic.

It is not. The most common version of it lets two workers claim the same row at the same time. Both get `rowcount = 1`. Neither gets an error. All of this happens on PostgreSQL's default isolation level, `READ COMMITTED`.

The failure is hard to catch because it leaves nothing behind. The row ends up with `status = 'running'`, which is exactly what one clean claim looks like. There is no query you can run afterwards to find out that it happened.

I hit this while building [Relay](https://github.com/Vishwam401/relay), a background job engine that runs on Postgres with no broker. Two `psql` sessions side by side were enough to show it.

## The pattern

Here is the statement, close to how it usually gets written:

```sql
UPDATE jobs
SET    status = 'running'
WHERE  id = (SELECT id FROM jobs
             WHERE status = 'pending'
             ORDER BY created_at, id
             LIMIT 1)
RETURNING id, type, payload;
```

It reads well. One statement instead of two. One round trip to the database. No explicit lock anywhere, so there is nothing about locking to think about. And `RETURNING` hands the worker its row in the same call, so there is no second query to fetch what was just claimed.

That is a lot of things going right, and it is why this version gets recommended.

One small thing in the `ORDER BY` before we move on. The `id` is there as a tiebreaker, not for ordering. Jobs inserted inside one transaction get the same `created_at` down to the microsecond, because `now()` returns the time the transaction started. Sort by `created_at` alone and two workers can read those rows in a different order on different runs.

## Reproducing it

Three rows and two `psql` sessions are enough. Nothing here depends on Relay.

```sql
CREATE TABLE jobs (
    id         bigserial   PRIMARY KEY,
    type       text        NOT NULL,
    payload    jsonb       NOT NULL DEFAULT '{}'::jsonb,
    status     text        NOT NULL DEFAULT 'pending',
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO jobs (type, payload, created_at) VALUES
  ('send_email', '{"to": "a@example.com"}', now()),
  ('send_email', '{"to": "b@example.com"}', now() + interval '1 second'),
  ('send_email', '{"to": "c@example.com"}', now() + interval '2 seconds');
```

The three `created_at` values are one second apart so that the `ORDER BY` picks the same row every time. Three rows matter too. With only one pending row there is nothing else a second worker could have claimed instead, and that is the thing we want to be able to see.

Now open two `psql` sessions next to each other.

Session 1 starts a transaction, claims a job, and stops there:

```sql
BEGIN;

UPDATE jobs SET status = 'running'
WHERE  id = (SELECT id FROM jobs
             WHERE status = 'pending'
             ORDER BY created_at, id
             LIMIT 1)
RETURNING id, type, payload;
```

It gets row `1`. **Do not commit.**

Session 2 runs exactly the same statement. It hangs. Session 1 holds a lock on row `1`, and session 2 has to wait for it.

Session 1 now commits:

```sql
COMMIT;
```

Session 2 wakes up. What it prints is the whole point of this post.

Leaving session 1 uncommitted is not a trick to force a rare case. It is a slow motion version of something that happens constantly: two workers reach for the same row, and one of them gets there a few microseconds earlier. Holding the transaction open makes that gap wide enough to watch.

Run the whole thing three times, changing one condition each time:

1. `WHERE id = (subquery)`: the statement above, as is.
2. `WHERE id = (subquery) AND status = 'pending'`: one extra condition.
3. `WHERE id = (subquery)`: with `FOR UPDATE SKIP LOCKED` inside the subquery.

Reset the table between runs with `TRUNCATE jobs RESTART IDENTITY;` and the `INSERT` again.

## What session 2 printed

| Version | Session 2 waited? | Row it got back | `rowcount` | Table afterwards |
|---|---|---|---|---|
| 1. plain | yes | **row `1`, the row session 1 already claimed** | 1 | `1 running, 2 pending, 3 pending` |
| 2. `AND status = 'pending'` | yes | nothing | 0 | `1 running, 2 pending, 3 pending` |
| 3. `FOR UPDATE SKIP LOCKED` | no | row `2`, the next one | 1 | `1 running, 2 running, 3 pending` |

In version 1, both sessions were told they own job `1`. Both got `UPDATE 1`. Neither saw an error or a warning.

Now look at the last column. **Version 1 and version 2 leave the table in exactly the same state.** One of them handed the same job to two workers and the other one did not, and afterwards the rows are identical. There is no query that separates them. This failure is only visible while it is happening.

If the job was `send_email`, the email goes out twice. If it was `charge_card`, the card is charged twice. Both workers did what the database told them to do.

## Why version 1 does this

Ask Postgres for the plan. Run `EXPLAIN` on version 1:

```text
Update on jobs
  InitPlan 1 (returns $0)
    ->  Limit
          ->  Sort  (Sort Key: jobs_1.created_at, jobs_1.id)
                ->  Seq Scan on jobs jobs_1   Filter: (status = 'pending'::text)
  ->  Index Scan using jobs_pkey on jobs
        Index Cond: (id = $0)
```

Two things to read here.

The subquery does not mention the outer row at all. It is not correlated, so Postgres does not have to run it once per row. It runs it a single time, before the scan starts, and stores the answer in a constant called `$0`. That is the `InitPlan` line.

So by the time the `UPDATE` starts looking for a row to change, the whole condition is `Index Cond: (id = $0)`. The word `status` is gone. It was used to pick the target and then thrown away.

Now the part that makes this quiet instead of loud. When a statement blocks on a row that someone else has locked, Postgres does not wake up holding a stale copy of that row. It fetches the newest committed version and checks the statement's condition against it again. That recheck is called `EvalPlanQual`, and it sounds like exactly the safety net you would want.

It checks the condition you wrote. In version 1 the condition is `id = $0`. Session 1 changed `status`, not `id`. So `id = 1` is still true, the recheck passes, the `UPDATE` applies a second time, and `RETURNING` hands back the same row.

Version 2 is the same mechanism with a different outcome. Its plan has one extra line:

```text
  ->  Index Scan using jobs_pkey on jobs
        Index Cond: (id = $0)
        Filter: (status = 'pending'::text)     <-- the only difference
```

One `Filter:` line. `status` is now part of what gets rechecked, the recheck fails, and `rowcount` comes back `0`. The safety is visible in the plan before you run anything.

This has a name. It is a lost update, and DDIA chapter 7 describes it along with the fix: put the old value into the write's condition, so a write that was based on stale information cannot apply. That is compare and set.

## The fix, and the part it does not fix

Relay claims with two separate pieces, and they solve two different problems.

| Piece | What it gives | What happens without it |
|---|---|---|
| `FOR UPDATE SKIP LOCKED` in the `SELECT` | the worker never waits behind a row someone else holds | version 2: correct, but the worker blocks and is then handed nothing |
| `AND status = 'pending'` on the `UPDATE` | the old value is part of the condition | version 1: a silent double claim |

It is worth being blunt about which piece does which, because `SKIP LOCKED` gets credit it has not earned. **`SKIP LOCKED` does not stop double claims.** The row lock and the compare and set do. What `SKIP LOCKED` removes is waiting. In Relay, with a 6 second lock held on the oldest pending row, the `SKIP LOCKED` worker started real work 1.25 seconds in, while a plain `FOR UPDATE` worker sat there for the full 6 seconds. Separately, two workers claiming different rows 6 ms apart with no `SKIP LOCKED` anywhere produced no duplicate at all.

And version 2 deserves a fair word. The single statement with the guard in it is a sound way to claim a job. It is one statement instead of two, it needs no explicit lock, and it returned `rowcount = 0` correctly under a live race. What it gives up is version 3's behaviour: when two workers collide, version 3 has both of them doing useful work, while version 2 leaves the loser blocked and then empty handed.

So this is not a broken pattern. It is a broken version of a working pattern, and the difference is one condition.

One thing the fix does not buy. The guard lives in your discipline, not in the schema. No `CHECK` constraint can express "`succeeded` must never go back to `running`", because that needs to compare two versions of the same row and a constraint only ever sees one. Every `status` update has to carry the guard, forever, and the database will not remind you when one does not.

## Two things I took away

A recheck rechecks your condition, not your intention. `EvalPlanQual` is not a concurrency safety feature. Versions 1 and 2 are the same mechanism producing opposite results, and the only difference is whether the column that changed is in the condition you wrote.

The wider version of that, which is not about Postgres. The mechanisms that catch people out are the ones whose names sound like guarantees. `timeout=0.5` reads like a hard limit and is a request. `SIGTERM` reads like stopping a process and is asking it to stop. `EvalPlanQual` reads like a concurrency check and is a predicate recheck. The name is what you remember when you are in a hurry.

Which brings this back to the uncomfortable part. A correct claim and a double claim leave the same row behind. If this is happening in your system right now, nothing in your database is going to tell you.

## What I ran, and what I did not

PostgreSQL 16.14 in Docker, default `READ COMMITTED`, three rows, two connections. Each version ran once. This demonstrates a mechanism, so one run is enough to show it exists, and it is not a benchmark of anything.

I have not run this on any other Postgres version. Plan shape depends on table size and statistics, so the node names in your `EXPLAIN` output may differ from mine. The `InitPlan` line and the missing `status` in the outer condition are the parts that matter.

The 1.25 second and 6 millisecond numbers come from Relay's own worker processes rather than from this three row reproduction.

The full reasoning behind Relay's claim path, including the versions I rejected and what each one cost, is in [`docs/DECISIONS.md`](https://github.com/Vishwam401/relay/blob/main/docs/DECISIONS.md) under `D-02`.
