<!--
Hashnode already holds the title and subtitle, so this file starts at the body.

Title:    The Postgres job-claim query that silently claims the same job twice
Subtitle: A lost update inside UPDATE ... RETURNING under READ COMMITTED that leaves
          no trace in the table.

All measurements: 2026-09-19, PostgreSQL 16.14 in Docker, default READ COMMITTED,
three pending rows, two connections, n = 1 per case, disposable database.

Before publishing, replace the two GitHub placeholder links near the top and bottom.
-->

A common way to claim a background job in PostgreSQL is a single `UPDATE` with a subquery that picks
the oldest pending row. It is one statement, so it looks atomic.

It is not. The most common version of it lets two sessions claim the same row. Both get
`rowcount = 1`. Neither gets an error. This happens on PostgreSQL's default isolation level,
`READ COMMITTED`.

The failure leaves nothing behind. The row ends up with `status = 'running'`, which is exactly what
one clean claim looks like. There is no query you can run afterwards to find out that it happened.

I hit this while building [Relay](https://github.com/), a background job engine that runs on Postgres
with no broker. Two `psql` sessions side by side were enough to show it.

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

It reads well. One statement instead of two. One round trip to the database. No explicit lock
anywhere, so there is nothing about locking to think about. And `RETURNING` hands the worker its row
in the same call, so there is no second query to find out which row was just taken.

That is a lot of things going right, and it is why this version gets recommended.

One small thing in the `ORDER BY`. The `id` is a tiebreaker, not an ordering. Rows inserted inside one
transaction get the same `created_at` down to the microsecond, because `now()` returns the time the
transaction started rather than the time the statement ran. Sort by `created_at` alone and two runs
can return those rows in a different order.

## Reproducing it

Three rows and two `psql` sessions. Nothing here depends on Relay.

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

The `created_at` values are a second apart so the `ORDER BY` picks the same row on every run. Three
rows matter too. With a single pending row there is nothing else a second session could have taken
instead, and being able to see that is half the experiment.

Session 1 opens a transaction, claims a job, and stops:

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

Session 2 runs the same statement. It hangs. Session 1 holds a lock on row `1`, so session 2 has to
wait.

Session 1 commits:

```sql
COMMIT;
```

Session 2 wakes up, and what it returns is the point of this post.

Leaving session 1 uncommitted is not a trick to force a rare case. It is a slow motion version of
something that happens constantly: two workers reach for the same row and one arrives a few
microseconds earlier. Holding the transaction open makes that gap wide enough to watch.

Run it three times, changing one condition each time:

1. `WHERE id = (subquery)`, the statement above as is
2. `WHERE id = (subquery) AND status = 'pending'`
3. `WHERE id = (subquery)`, with `FOR UPDATE SKIP LOCKED` inside the subquery

Reset with `TRUNCATE jobs RESTART IDENTITY;` and the `INSERT` between runs.

## What session 2 returned

| Version | Waited? | Row it got | `rowcount` | Table afterwards |
|---|---|---|---|---|
| 1. plain | yes | **row `1`, the row session 1 already claimed** | 1 | `1 running, 2 pending, 3 pending` |
| 2. `AND status = 'pending'` | yes | nothing | 0 | `1 running, 2 pending, 3 pending` |
| 3. `FOR UPDATE SKIP LOCKED` | no | row `2`, the next one | 1 | `1 running, 2 running, 3 pending` |

In version 1, both sessions were told they own job `1`. Both got `UPDATE 1`. Neither saw an error or
a warning.

Now read the last column. **Version 1 and version 2 leave the table in the same state.** One of them
handed the same job to two sessions and the other did not, and afterwards the rows are identical.
There is no query that separates them, so this failure is only visible while it is happening.

The job type was `send_email`, so the email goes out twice. Had it been `charge_card`, the card is
charged twice. Both workers did what the database told them to do, and the database has no record
that it told two of them the same thing.

## Why version 1 does this

Ask Postgres for the plan. Version 1:

```
Update on jobs
  InitPlan 1 (returns $0)
    ->  Limit
          ->  Sort  (Sort Key: jobs_1.created_at, jobs_1.id)
                ->  Seq Scan on jobs jobs_1
                      Filter: (status = 'pending'::text)
  ->  Index Scan using jobs_pkey on jobs
        Index Cond: (id = $0)
```

Version 2, and the difference is one line:

```
  ->  Index Scan using jobs_pkey on jobs
        Index Cond: (id = $0)
        Filter: (status = 'pending'::text)     <-- the only difference
```

Two mechanisms explain that line.

### The subquery becomes a number

The subquery never mentions the outer row. It asks for the oldest pending id and can answer that on
its own. A subquery like this is uncorrelated, so Postgres does not run it once per row. It runs it a
single time before the scan and stores the answer in a parameter, `$0`. That is the `InitPlan` line.

So by the time the `UPDATE` goes looking for a row to change, its whole condition is
`Index Cond: (id = $0)`, which is `id = 1`. The word `status` is gone. It was used to pick the target
and then dropped.

This is the shape of the bug. I wrote a condition, `give me a pending job`. Postgres turned it into an
address, `go to job 1`. Both meant the same thing at that instant. An address does not stop being
true when the row's status changes.

### The recheck rechecks what you wrote

Under `READ COMMITTED`, a statement that blocks on a locked row does not wake up holding stale data.
It follows the row to its newest committed version and re-evaluates the statement's condition against
it. This is called `EvalPlanQual`, and it sounds like the safety net you would want.

It is a real safety net. It checks the condition you wrote.

In version 1 the condition is `id = $0`. Session 1 changed `status`, not `id`, so `id = 1` is still
true. The recheck passes, the update applies a second time, and `RETURNING` hands back the same row.

In version 2 the condition contains `status`. The recheck finds `running`, fails, and `rowcount`
comes back `0`.

Same mechanism, opposite results. The only difference is whether the column that changed was in the
condition.

### Proof that the recheck does not redo the subquery

This part is worth checking rather than assuming, and the reproduction already proves it.

The recheck re-evaluates the condition. It does not re-run the `InitPlan`. If it did, the oldest
pending row after session 1's commit would have been `2`, and session 2 would have returned `2`.

It returned `1`.

So the constant computed before the block survived the wake-up. That is why the condition no longer
knew anything about `status`.

### This has a name

This is a lost update. DDIA chapter 7 describes it, along with the fix: put the old value into the
write's condition so a write based on stale information cannot apply. That is compare and set.

## What about a higher isolation level

This is the first thing I wanted to check, so here it is measured. Same reproduction, only session 2's
isolation level changed.

| Session 1 | Session 2 isolation | Session 2 result |
|---|---|---|
| `COMMIT` | `READ COMMITTED` | row `1`, the row session 1 claimed |
| `COMMIT` | `REPEATABLE READ` | `40001 could not serialize access due to concurrent update` |
| `COMMIT` | `SERIALIZABLE` | `40001 could not serialize access due to concurrent update` |

Raising the isolation level does stop the duplicate. There is no recheck at those levels. A concurrent
update to a row you are trying to write is a serialization failure, and you get an error instead of a
wrong answer.

That is better, and it is not free. Every caller now has to catch `40001` and retry. For a claim that
is contended on purpose, conflicts are expected rather than exceptional, so this turns the normal case
into an error path.

One more case, because it is the one people skip. If session 1 **rolls back** instead of committing,
session 2 wakes up and gets row `1`, and that is completely correct. Session 1 undid its claim, so the
row was free. Getting row `1` back is not the bug. Getting it back after someone else committed a claim
on it is the bug, and the blocked session cannot tell those two apart.

## The fix, and the part it does not fix

Relay claims with two separate pieces that solve two different problems.

| Piece | What it gives | What happens without it |
|---|---|---|
| `FOR UPDATE SKIP LOCKED` in the `SELECT` | the session never waits behind a row someone else holds | version 2: correct, but it blocks and is then handed nothing |
| `AND status = 'pending'` on the `UPDATE` | the old value is part of the condition | version 1: a silent double claim |

Worth being blunt about which does which, because `SKIP LOCKED` gets credit it has not earned.
**`SKIP LOCKED` does not stop double claims.** The row lock and the compare and set do. What
`SKIP LOCKED` removes is waiting.

Two measurements from Relay's own worker processes. With a 6 second lock held on the oldest pending
row, the `SKIP LOCKED` worker began real work 1.25 seconds in, while a plain `FOR UPDATE` worker sat
there for the full 6 seconds. Separately, two workers claiming different rows 6 ms apart, with no
`SKIP LOCKED` anywhere, produced no duplicate. So the safety was never coming from `SKIP LOCKED`.

Version 2 also deserves a fair word. The single statement with the guard inside it is a sound way to
claim a job. It is one statement, it needs no explicit lock, and it returned `rowcount = 0` correctly
under a live race. What it gives up is version 3's behaviour: when two workers collide, version 3 has
both of them doing useful work, while version 2 leaves the loser blocked and then empty handed.

So this is not a broken pattern. It is a broken version of a working pattern, and the difference is
one condition.

One thing the fix does not buy. The guard lives in your discipline, not in the schema. No `CHECK`
constraint can express "`succeeded` must never become `running`", because that compares two versions
of the same row and a constraint only ever sees one. Every `status` update has to carry the guard, and
the database will not remind you when one does not.

## Two things I took away

A recheck rechecks your condition, not your intention. `EvalPlanQual` is not a concurrency safety
feature. Versions 1 and 2 are the same mechanism producing opposite results, and the only difference is
whether the column that changed appears in the condition you wrote.

The wider version of that is not about Postgres. The mechanisms that catch people out are the ones
whose names sound like guarantees. `timeout=0.5` reads like a hard limit and is a request: in my own
measurement a `0.5 s` read timeout aborted at `2.172 s`, because the in-flight socket read could not be
interrupted. `SIGTERM` reads like stopping a process and is asking it to stop. `EvalPlanQual` reads
like a concurrency check and is a predicate recheck. The name is what you remember when you are in a
hurry.

Which brings it back to the uncomfortable part. A correct claim and a double claim leave the same row
behind. If this is happening in your system right now, nothing in your database is going to tell you.

## What I ran, and what I did not

PostgreSQL 16.14 in Docker, default `READ COMMITTED`, three rows, two connections, on a disposable
database. Each case ran once. This demonstrates a mechanism, so one run shows that it exists, and none
of it is a benchmark.

I have not run any of this on another PostgreSQL version. Plan shape depends on table size and
statistics, so the node names in your `EXPLAIN` output may differ from mine. The `InitPlan` line and
the absent `status` in the outer condition are the parts that matter.

I also did not check whether the recheck behaves the same when the subquery is correlated and becomes a
`SubPlan` evaluated per row instead of an `InitPlan`. I measured the plan shape for that case and
stopped there.

The 1.25 second and 6 millisecond figures come from Relay's worker processes, not from this three row
reproduction.

The full reasoning behind Relay's claim path, including the versions I rejected and what each one cost,
is in [`docs/DECISIONS.md`](https://github.com/) under `D-02`.
