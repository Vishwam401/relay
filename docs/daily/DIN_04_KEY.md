# DIN 4 — KEY (sealed)

> 🔒 **Open one step's section only after that step's experiment has been run.**
> Not after you have written your answer. After the **measurement**.
>
> Din 1 scored `0/9` because the answers were read before the questions were attempted. Din 2 scored
> `62%` because they were not. Din 3 skipped scoring entirely, so there is no data point — which is
> itself a reason to keep this file shut until each step has run.
>
> **Never paste this file to Gemini.**
>
> Every claim is labelled `[MEASURED]` or `[INFERRED]`. Where an answer depends on your machine or
> your implementation, it says **must be measured** instead of giving you a number.

---

## STEP 0 — ordering

**0.1 — All ten `created_at` values will be identical.** `[MEASURED on Din 3, K2]`
```
SELECT now() AS a, now() AS b FROM generate_series(1,3);
→ 2026-08-15 20:17:56.264363+00   (identical in all three rows, and a = b)
```
`now()` is the **transaction** timestamp, not the statement or row timestamp. One `INSERT ... SELECT
... generate_series` is one transaction, so every row ties. Ten separate `INSERT`s are ten
transactions and give ten distinct values (Din 2 measured exactly that on the original 9 rows).

`D-08` chose `now()` over `clock_timestamp()` deliberately — one clock per transaction — so this tie
is the *other face of that decision*, not a bug in it.

**0.2 — Which row `LIMIT 1` returns when all rows tie: undefined, and not stable.** `[INFERRED]`
SQL gives no guarantee. In practice it falls out of the plan — with a `Sort` feeding `LockRows`
feeding `Limit`, ties resolve by whatever order the `Seq Scan` produced, which itself changes as rows
are updated (a heap `UPDATE` writes a new tuple version, typically later in the heap). So the answer
can change between runs on the same data.

Why this matters more today than it looks: Din 4's central question is *which* job the second worker
got. If ordering is undefined, **no answer to that question is falsifiable** — you cannot distinguish
"it correctly took the next job" from "it took an arbitrary row". Sorting by `(created_at, id)` makes
the expected answer predictable, which is what makes a wrong answer detectable.

**0.3 — Adding `id` to the sort does change the eventual index, and the effect is small.**
`[INFERRED]` `ORDER BY created_at, id` is satisfied by a composite index on `(created_at, id)`, or
partially by one on `created_at` alone plus a cheap in-memory sort of the tied group. Since `id` is
monotonic and `created_at` is `DEFAULT now()`, the two orders almost always agree, so the practical
index shape barely changes. **Do not settle this here** — it is `P-03`, Week 4, by `EXPLAIN ANALYZE`.
Note that the cost of the tiebreak is trivially small and the cost of *not* having it is an
unfalsifiable experiment.

---

## STEP 1 — the instrument

**1.1 — `job_executions` is telling the truth; `jobs` is telling you the last thing anyone managed to
record.** `[INFERRED]` The handler ran, so an execution genuinely happened. The mark failed, so `jobs`
still says `running`. Neither row is lying — they answer different questions:

| Table | Question it answers |
|---|---|
| `jobs.status` | What is the *current intent/state* of this job, per the last successful write |
| `job_executions` | What *actually happened*, as facts, append-only |

This is why the instrument has to be separate. A status column is a **mutable summary**; it can only
ever hold one value, and each write destroys the previous one. Din 3's M4 is the same shape from the
other side: the guard prevented a write precisely because the row's state had already moved on.

**1.2 — Same transaction as the mark = the evidence disappears exactly when you need it.**
`[INFERRED]` If the execution row and the terminal mark commit together, then any failure between the
side effect and that commit rolls back *both*. You are left with a job that ran and no record that it
ran — which is the one case the instrument exists for. Din 3's `P-09` reasoning applies directly:
recovery has to reason about work that started and did not finish.

The opposite choice has a cost too, and it is worth stating so the decision is not free: writing the
execution row in its **own** transaction, before the mark, means you can end with `job_executions`
showing an execution while `jobs` shows `running` forever, or (with Week 2's reaper) an execution row
for an attempt that later gets requeued and executed again. That is not a contradiction — it is
at-least-once being visible. **Prefer the version that over-records over the version that can lose the
record.** Un-recorded work is undetectable; double-recorded work is merely confusing.

**1.3 — A foreign key makes Week 4's retention delete fail, by design.** `[INFERRED]`
`DELETE FROM jobs WHERE created_at < now() - interval '30 days'` raises a foreign-key violation while
child rows exist. Two options at that moment, and they are genuinely different products:

| Option | Consequence |
|---|---|
| `ON DELETE CASCADE` | Execution history disappears with the job. Retention is simple; audit trail is not durable |
| Delete children explicitly first, or no FK at all | History can outlive the job. Then `job_id` may point at nothing, and any join must tolerate that |

There is no free answer, and the choice is really *"is execution history an audit log, or a debugging
aid?"* An audit log outlives its subject. A debugging aid does not need to. Decide it, write it, and
note that today's decision costs one line of migration in Week 4 either way.

**1.4 — `jobs` can never show a double execution because `UPDATE` overwrites.** `[MEASURED in Week 0
Day 5]` Two workers both write `status='running'`, then both write `status='succeeded'`. Same column,
same values, one row, no constraint violated. Your own Week 0 log: *"dono ne same value likhi, row
bilkul theek dikhi."*

The general rule, and it is worth carrying past this project: **a mutable column records the latest
claim about state; it cannot record how many times something happened.** Counting requires either an
append-only log or a counter that is incremented rather than assigned. `attempts` is the counter
version and it is Week 2's; `job_executions` is the log version and it is today's.

---

## STEP 2 — two workers, `FOR UPDATE` only

**2.1 / 2.2 / 2.3 — the mechanism, then what to expect.** `[INFERRED — this is the day's measurement,
so treat the shape as a prediction and your output as the answer.]`

Both workers run the same claim query. `FOR UPDATE` takes a row lock; a second transaction wanting
the same row's lock **waits** until the holder commits or rolls back. There is no shorter unlock —
Din 3's brief said this and Week 0 Day 5 measured the blocking behaviour directly.

The crucial detail is *how long* the wait is, and Din 3 already measured what decides it:
the claim transaction contains only `SELECT ... FOR UPDATE` + `UPDATE` + `COMMIT`, and it committed
**before** the handler ran (`state='idle'`, `xact_start NULL`). So a blocked worker waits for a
**claim**, on the order of milliseconds, not for a 2 s handler. If you predicted "blocked for the
handler duration", you predicted the pre-Din-3 design.

Expected wait event when it does block: `Lock` / `transactionid` (waiting on the holding transaction
to end), the same pair Week 0 Day 5 Exp 3 produced. `Lock` / `tuple` is also possible — it appears
when several waiters queue on one row. **If you see `Lock`/`tuple`, that is a finer-grained fact than
the Day 5 log has, and it is worth recording as new.**

An honest warning about what you will probably see: with a claim this short, the collision window is
tiny. Two workers polling every 2 s may simply **never overlap**, in which case your snapshots show
two `idle` backends and no waiting at all. That is not evidence that blocking does not happen — it is
a sampling failure, and the correct write-up is *"no contention observed in N snapshots"*, not
*"`FOR UPDATE` does not block"*. Step 3 exists precisely because it forces the collision instead of
hoping for one.

**2.4 — the arithmetic, which is what matters here.** `[INFERRED]`
Ten jobs, handler 2 s, two workers, one job at a time each. Serial floor is `10 x 2 s = 20 s`;
perfect two-way parallelism is `10 s`. Add per-job claim/mark overhead (Din 3's echo timestamps show
claim→mark cycles of roughly 2.0 s plus single-digit milliseconds of SQL) and up to one poll interval
of idle latency at the start and between jobs — the loop sleeps only when it finds nothing, so a busy
queue does not pay the 2 s per job, but a worker that hits a zero-row claim does.

So the defensible prediction is *"a little over 10 s, well under 20 s"*, and the number you should
write down is your own measured one. **Do not report a speed-up factor from one run each** — Din 2's
"~11 ms unexplained" is the standing example of a number quoted past what it supported.

**2.5 — expect zero natural duplicates, and expect that to be uninformative.** `[INFERRED]`
The compare-and-set guard makes a duplicate claim structurally hard: whichever worker's guarded
`UPDATE ... AND status='pending'` runs second gets `rowcount = 0` and abandons the row. Din 3's M4
measured that branch firing under real interference.

The result that should make you doubt the **instrument** rather than the conclusion:
`SELECT worker_id, count(*) FROM job_executions GROUP BY worker_id` showing all ten executions
against one worker. That means the second worker never did anything, so the run never tested
contention at all — and a duplicate count of `0` from such a run says nothing.

---

## STEP 3 — the blocked claim, and today's real finding

**3.1 — While X holds job 5 uncommitted: your worker blocks. It does not skip to job 6.**
`[INFERRED, must be measured]` This is the direct consequence of Din 3's measured plan shape:

```
Limit  →  LockRows  →  Sort  →  Seq Scan
```

`LockRows` sits **below** `Limit`, so locking happens *while* rows are being produced, before `Limit`
has its one row. Without `SKIP LOCKED`, the executor's only option on a locked row is to wait. It
cannot say "fine, next one" — that behaviour is exactly what `SKIP LOCKED` adds, and its absence is
why today has a "before".

**3.2 vs 3.3 — these have different answers, and this is the thing worth learning today.**
`[INFERRED, must be measured]`

When the lock is finally granted, Postgres does not blindly return the row it waited for. Under
`READ COMMITTED` it **re-evaluates the now-current version of that row against the query's
`WHERE`** — the mechanism is called `EvalPlanQual`:

| Case | Row's state when the lock is released | Expected outcome |
|---|---|---|
| **3.2** X set it to `running`, then committed | no longer matches `status='pending'` | The row **fails the re-check and is dropped**. Your claim iteration most likely returns **zero rows** — even though jobs 6–14 are sitting there `pending` — because `Limit` had already committed to this one row |
| **3.3** X committed without changing status | still matches `status='pending'` | The row **passes the re-check** and is returned. Your worker claims job 5, `rowcount = 1` |

So the same code path produces "claimed a job" or "found nothing" depending on what the *other*
transaction did while you waited. Two consequences, and the second one is the one that generalises:

1. **A zero-row claim does not mean the queue is empty.** Your worker's loop treats "no job found" as
   "queue empty → sleep the poll interval". Under contention that is wrong: there is work, and the
   worker just agreed to do nothing for 2 s. This is real throughput loss and it is invisible in the
   `jobs` table — nothing is broken, nothing is stuck, the queue is simply drained slower than it
   could be. `[This is the honest answer to 3.5.]`
2. **`rowcount = 0` on the guarded `UPDATE` is not the only "someone beat me to it" signal.** There is
   a second, quieter one: the `SELECT` returning nothing at all. Din 3 handled the first and logged
   it loudly; today reveals the second, which currently looks identical to an empty queue. Whether to
   distinguish them — e.g. retry the claim immediately rather than sleeping when other work provably
   exists — is a Week 4 throughput decision. **Noticing it is today's finding; do not build it.**

If your measured outcome differs from the table above, **your output wins.** Record it verbatim and
work out why: plan shape, isolation level, and whether X's transaction really committed are the three
places to look.

**3.4 — the separating mechanism, named:** the `READ COMMITTED` re-check after lock acquisition. Under
`REPEATABLE READ` the same situation raises a serialization failure instead of silently dropping the
row (`40001`, the error Week 0 Day 5's bonus produced), which is a third distinct behaviour from the
same code. Isolation level does not just change what you see; it changes *what your code has to
handle*.

---

## STEP 4 — duplicates

**4.1 — No. With one job per worker and a compare-and-set guard, `FOR UPDATE` alone should not produce
a genuine double execution today.** `[INFERRED]` For two handlers to run for one job, both workers
would have to leave the claim transaction believing they own the row. The guard prevents that: the two
guarded `UPDATE`s are serialised by the row lock, and the loser gets `rowcount = 0`.

**4.2 — So state today's goal honestly, because it is not "find duplicates".** It is:

> *Prove that duplicate execution cannot be detected from `jobs`, build something that can, and
> measure what `FOR UPDATE` alone costs in throughput — the blocking and the zero-row claims — rather
> than in correctness.*

The correctness failure arrives later and by a different route (`P-09`): a reaper resetting
`running → pending`, or a claim written without the guard. That is why Step 4 forces a duplicate by
hand — **an instrument that has never shown a positive is not yet known to work**, which is Din 2's
`413` lesson applied to a measurement instead of a check.

**4.3 — Your hand-edit `UPDATE ... SET status='pending'` is the reaper, played by you.**
`[INFERRED]` It simulates recovery: something outside the worker decided the job should run again.
Which contract point? **#1, "an accepted job is never lost"** — recovery serves durability. And in
doing so it creates the risk in **#2, "exactly once"**. Week 2 owns doing it automatically, on a
deadline, and Week 3 owns making the second execution harmless.

Note what you have just done manually: the `running → pending` transition that Din 3's `D-06` notes
the schema cannot prevent, and that Din 3's brief listed as Week 2's. Doing it by hand for one row,
deliberately, in an experiment, is fine. Doing it in `src/` today is the thing Part D asks you hardest
not to do.

---

## STEP 5 — `SKIP LOCKED`

**5.1 — Duplicates: still zero, and for a reason unrelated to `SKIP LOCKED`.** `[INFERRED]`
`SKIP LOCKED` changes what a *competing claimer does while another holds the row* — it does not touch
the guard, which is what provides correctness. Din 3's KEY made this split explicit and it is worth
re-reading here: **the compare-and-set is correctness; `FOR UPDATE` / `SKIP LOCKED` is efficiency and
ordering under contention.** If your duplicate count changes between Step 2 and Step 5, something
else changed too — find it before believing the number.

**5.2 — Faster, and probably by less than you expect on this bench.** `[INFERRED, must be measured]`
The mechanism is clear: a worker that would have blocked instead takes the next unlocked row, so no
worker sits idle while work exists, and zero-row claims from Step 3's re-check disappear. But the
saving is proportional to the time actually spent blocked — and with a millisecond-scale claim
transaction, that may be a small fraction of a 10 s run. **Report the two times; report the delta;
do not report a factor from one run each.** If they are within noise, the correct conclusion is
*"no difference measurable at this scale"*, which is a real result and is exactly what Week 4's load
test exists to revisit.

**5.3 — The row that should disappear from the snapshot is the waiting one:** any backend showing
`wait_event_type = Lock`. If you never captured one in Step 2, then this comparison has nothing to
compare, and the honest write-up is *"contention never observed in either run"*.

**5.4 — Where skipping is wrong: anywhere the specific row is the point.** `[INFERRED]`
`SKIP LOCKED` means "give me *a* row, I do not care which". That is exactly right for a work queue
and exactly wrong for, say, `SELECT balance FROM accounts WHERE id = 42 FOR UPDATE` — you cannot
transfer money out of "some other account that happened to be free". Skipping there would silently
operate on the wrong entity. The distinction: **is the row interchangeable, or identified?**
Queues hold interchangeable rows; almost nothing else does.

Your Week 0 Day 5 log already picked the right primitive for the queue case before measuring it:
*"skip and take the next one is the behaviour I actually want, not wait and not abort."*
Today is that sentence being priced. `D-02` is where it gets written up, and it needs both this and
`SERIALIZABLE`'s `40001`-plus-retry alternative from Week 0 Day 5.

**5.5 — Yes, two workers can still execute the same job, and `SKIP LOCKED` is irrelevant to it.**
`[INFERRED]` Routes, none of which locking addresses:

- Week 2's reaper requeues a job whose worker is **slow rather than dead** — `P-02`: a timeout bounds
  intent, not reality, so the reaper cannot stop the first worker, only outrun it.
- A future claim written **without** the guard, where the row lock is released before the second
  worker looks (Week 0 Day 5 Exp 1, reproduced).
- Duplicate *enqueue* — two rows, two jobs, one intent. That is `P-07`, Week 3, and no locking
  primitive can see it.

The generalisation worth keeping: **`SKIP LOCKED` is a scheduling optimisation, not a safety
mechanism.** Treating it as safety is the mistake that makes Week 3 feel optional.

---

## STEP 6 — prefetch

**Answers to the three one-liners** `[INFERRED from documentation]`:

1. **Prefetch limits unacknowledged messages in flight per consumer**, not messages per second. It is
   a bound on how much work a consumer may be holding but not yet finished.
2. **On consumer death, its prefetched-but-unacked messages are requeued** and redelivered to someone
   else, once the broker detects the disconnection. That detection is the part Relay has no equivalent
   of (`P-09`) — Postgres notices the dead connection but does not know a job was owed.
3. **A large prefetch starves other consumers**: one consumer grabs a batch and sits on it while
   others idle. The queue looks busy and the fleet is underutilised — the classic head-of-line
   problem, and the same shape as a worker blocked on a lock while other rows are free.

**6.1 — Claiming five and dying mid-batch: all five stay `running` forever.** `[INFERRED, and it is
`P-09` scaled]` Din 3 established that a committed claim has nothing watching it. Claiming five
multiplies the blast radius of one crash by five, with no change to the recovery story — because there
is no recovery story yet. **Batch size and crash blast radius are the same dial**, which is exactly
why prefetch cannot be tuned before leases exist.

**6.2 — At 2 workers and 1000 jobs, both extremes cost you something.** `[INFERRED]`

| Claim size | Cost |
|---|---|
| 1 at a time | 1000 claim transactions, 1000 marks, plus a poll round trip whenever a claim finds nothing. `P-10`'s per-poll transaction cost, multiplied |
| 50 at a time | 20 claim transactions, but each crash risks 50 stuck jobs, and load balances badly — one worker can hold 50 while the other has none |

The right answer is a measurement, in Week 4, with a load generator. Today the only defensible
statement is that the trade is *round trips against blast radius and fairness*, and that Relay cannot
even evaluate it until Week 2 makes a stuck job recoverable.

---

## Known traps — things you cannot find by reading

**T1 — Two workers in one PowerShell window will not work.** `[MEASURED on Din 3]` A worker started in
the foreground blocks that shell until `Ctrl+C`; the reviewer lost several minutes to exactly this.
Two workers need two terminals, and you still need a third for `psql`. Also note both workers write to
their own stdout, and Din 3's echo output is verbose — the `worker-<pid>` tag is what makes the two
logs separable afterwards.

**T2 — Both workers import `src/database.py`, so each gets its own engine and its own pool.**
`[INFERRED, definitional — Din 3's KEY 1.1]` Two processes means two pools; `max_connections` bounds
the *sum*. Two workers plus the API is still nowhere near the default `100`, so this will not bite
today — it is here so that Din 5's three workers do not surprise you.

**T3 — `alembic check` will go red if you create `job_executions` with `create_all` instead of a
migration.** `[MEASURED in spirit on Din 1]` Week 0's leftover tables made the check permanently red,
and Din 1's log recorded the real cost: a diagnostic you learn to ignore, plus a subsequent
`--autogenerate` silently producing a `DROP TABLE`. Migration first, then `downgrade -1` /
`upgrade head` / `check` to prove all three directions.

**T4 — `rowcount` on the claim `SELECT` is meaningless.** `[Din 3's K3, unchanged]` It is the guarded
`UPDATE`'s `rowcount` that carries information. And today adds a second signal that has no `rowcount`
at all: the `SELECT` returning zero rows after a blocked wait (Step 3). Both mean "my belief was
stale"; only one of them currently logs anything.

**T5 — Do not reset the whole table between runs with `DELETE FROM jobs`.** `[INFERRED]` It breaks the
arithmetic that C6 asks you to reconcile, it takes `job_executions` history with it if you added a
cascade, and Din 3 already showed how a moved bench state makes a later log unverifiable. Seed fresh
rows and track id ranges instead.

**T6 — Timing two workers by hand includes your own reaction time.** `[INFERRED]` Starting the second
terminal by hand adds a second or two before the run is really parallel. For a ~10 s run that is
10–20% error, which is larger than any difference `SKIP LOCKED` is likely to show at this scale. Say
how you timed it, or the two numbers in C5 are not comparable to each other.

**T7 — `pg_stat_activity` snapshots are samples, not history.** `[MEASURED on Din 3]` The reviewer
took one snapshot 4 s into a run and caught the state; another attempt at measuring a lock queue hit
an already-finished window and produced a *false negative* that looked like a result. If you cannot
positively identify both workers' backends in the output, the snapshot proves nothing — the same
precondition Din 3's Step 5 established.

---

## Outputs that will look wrong and are correct

| You will see | Why it is fine |
|---|---|
| Zero duplicate executions all day | Expected. Today's duplication risk is not implemented yet — `P-09`. The instrument, not the count, is the deliverable |
| One worker doing 6 jobs and the other 4 | Uneven split is normal; whichever finishes its 2 s handler first claims next. Only an all-10-to-one split is a problem |
| A claim iteration returning nothing while `pending` rows exist | Step 3's re-check. Real, currently indistinguishable from an empty queue in your logs |
| `Seq Scan` still, on ~40 rows | Correct at this size. `P-03`, Week 4 |
| `attempts = 0` on everything | Nothing increments it in Week 1 |
| `ROLLBACK` in the echo with nothing failing | Session teardown returning the connection to the pool (Din 2's M2) |
| Two workers' logs interleaved unreadably | Two writers, one console each — that is why the `worker-<pid>` tag exists |
| `SKIP LOCKED` making no measurable time difference | Entirely possible at 10 jobs with a millisecond claim. "No difference measurable at this scale" is a result |

---

## What must be measured, not predicted

- Whether two workers on this bench ever actually collide, and in how many snapshots.
- The wait event when they do: `Lock`/`transactionid` or `Lock`/`tuple`.
- Step 3's two cases — the row returned, the `rowcount`, and whether your conflict branch fired.
- Both total times, and whether their difference exceeds your timing error (T6).
- The per-`worker_id` execution split for both runs.
- That your duplicate-detection query can return a positive at all (C4's forced duplicate).
- Whether `alembic downgrade -1` / `upgrade head` / `check` all pass after the new migration.
