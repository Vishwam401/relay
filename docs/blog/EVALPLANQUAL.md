# `EvalPlanQual` — the complete flow

A reference note. Everything marked `[MEASURED]` was run on 2026-09-19, PostgreSQL 16.14, on a
disposable database, using the naive claim statement:

```sql
UPDATE jobs SET status='running'
WHERE id = (SELECT id FROM jobs WHERE status='pending' ORDER BY created_at, id LIMIT 1)
RETURNING id;
```

---

## The one-line version

> Under `READ COMMITTED`, a writer that gets blocked on a row does not abort and does not use stale
> data. It follows the row to its newest committed version and re-checks **the statement's own
> `WHERE` condition** against that new version. Pass, and it writes. Fail, and it skips the row.

That is `EvalPlanQual`. `Qual` is short for qualification, meaning the condition. `Eval` means
evaluate it again.

**It is a real safety mechanism and it is not broken.** It protects the condition you wrote. If the
column that changed is not in your condition, there is nothing for it to catch.

---

## Why it exists at all

`READ COMMITTED` promises that a writer sees the latest committed data. A concurrent write to the
same row creates a conflict, and there are only three things a database can do about it:

| Option | Consequence |
|---|---|
| Use the stale version you already read | wrong data gets written. Never acceptable |
| Abort the statement with an error | every concurrent writer needs retry logic |
| Re-read the row and re-check the condition | no error, no stale write |

`READ COMMITTED` picks the third. `REPEATABLE READ` and `SERIALIZABLE` pick the second.

So `EvalPlanQual` is the price of not getting an error. It is the mechanism that makes
`READ COMMITTED` usable for concurrent writes.

---

## The full flow, step by step

```
 1. Statement starts.
    READ COMMITTED takes a FRESH SNAPSHOT here, per statement, not per transaction.

 2. The plan runs. Any InitPlan is evaluated ONCE and its result is stored in a
    parameter slot ($0, $1, ...).

 3. The outer scan finds candidate rows, using the snapshot from step 1 and the
    outer qualification.

 4. For each candidate the UPDATE tries to lock the row before writing it.

 5. Three things can happen at that lock attempt:

    (a) row is free
        -> lock it, write it. Done.

    (b) row is locked by a transaction that is still running
        -> WAIT on that transaction's id. This is the `Lock` / `transactionid`
           wait event. Go to step 6 when it finishes.

    (c) row was already modified by a transaction that committed after my snapshot
        -> go straight to step 7.

 6. The blocking transaction finished. Which way?

    ROLLBACK
        -> nothing it did survived. My candidate version is still the live one.
           Proceed normally, as in 5(a).

    COMMIT, and it DELETED the row
        -> the row is gone. Skip it. Contributes 0 to rowcount.

    COMMIT, and it UPDATED the row
        -> a newer version exists. Follow the update chain to it. Go to step 7.

 7. EvalPlanQual runs:

        take the NEW version of the row
        re-evaluate the statement's qualification against it

        PASS -> write the NEW version. rowcount += 1
        FAIL -> skip the row.           rowcount += 0

 8. Under REPEATABLE READ or SERIALIZABLE, step 7 does not exist.
    A concurrent update to a row you are trying to write is a serialization failure:
    SQLSTATE 40001, "could not serialize access due to concurrent update".
```

---

## The part that causes the bug

**Step 7 re-evaluates the qualification. It does not re-run step 2.**

The `InitPlan` already produced its value. That value stays. So if the qualification is
`id = $0`, the recheck asks *"is this row still id 1?"* and not *"is this row still the oldest
pending one?"*

`id` does not change. The recheck passes. The write applies.

### This is measured, not reasoned

`[MEASURED]` Session 1 claimed row `1` and committed. Session 2, blocked and then woken, returned
row **`1`**.

If the `InitPlan` had been recomputed after session 1 committed, the oldest pending row would have
been `2`, and session 2 would have returned `2`. It returned `1`.

So the constant from step 2 survived the recheck. That is the proof.

---

## All four cases, measured

`[MEASURED]` PostgreSQL 16.14, three pending rows, two connections, `n = 1` per case.

| # | Session 1 | Session 2 isolation | Blocked? | Session 2 result | Correct? |
|---|---|---|---|---|---|
| A | `COMMIT` | `READ COMMITTED` | yes | row `1`, the row session 1 already claimed | **no.** Duplicate claim |
| B | `ROLLBACK` | `READ COMMITTED` | yes | row `1` | **yes.** Session 1 undid its claim, so row `1` was free |
| C | `COMMIT` | `REPEATABLE READ` | yes | `40001 could not serialize access due to concurrent update` | **yes.** No duplicate, but the caller must retry |
| D | `COMMIT` | `SERIALIZABLE` | yes | `40001 could not serialize access due to concurrent update` | same as C |

Final table state was `1 running, 2 pending, 3 pending` in **every** case, including the broken one.

**Case B is the case people forget.** Same block, same wake-up, same returned row, and it is
completely correct. Getting row `1` back is not the bug. Getting it back *after someone else
committed a claim on it* is the bug. The blocked session cannot tell those two apart, and neither
can the row afterwards.

**Cases C and D answer the most likely objection.** Raising the isolation level does stop the
duplicate. It replaces it with `40001`, which every caller then has to catch and retry. For a claim
that is contended on purpose, that trades a silent wrong answer for a loud one, which is better, but
it is not free.

---

## The three sentences to explain this to someone else

1. Under `READ COMMITTED`, a blocked writer wakes up, fetches the newest version of the row, and
   re-checks its own `WHERE` against it.
2. That recheck protects whatever you put in the `WHERE`, so if the column that changed is not in
   there, nothing is caught.
3. `UPDATE ... WHERE id = (subquery)` turns a condition into an address, because the subquery is
   evaluated once into a constant, and an address does not go stale the way a condition does.

---

## Quick reference: when does the recheck save you?

| Your `WHERE` on the `UPDATE` | Concurrent change | Recheck result |
|---|---|---|
| `id = $0` | `status` changed | passes. You overwrite |
| `id = $0 AND status = 'pending'` | `status` changed | fails. `rowcount = 0` |
| `id = $0` | row deleted | row skipped. `rowcount = 0` |
| `id = $0` | other txn rolled back | proceeds normally, and correctly |
| anything | any, under `REPEATABLE READ`+ | `40001`, no recheck |

---

## Not measured, so not claimed

- Whether the recheck behaves the same when the subquery is **correlated** and therefore becomes a
  `SubPlan` evaluated per row rather than an `InitPlan`. The plan shape was measured
  (`Filter: (id = (SubPlan 1))`, cost `15968` against `27`); the recheck behaviour was not.
- Any of this on a PostgreSQL version other than `16.14`.
- Whether `claim_generation` in `job_executions` would make a duplicate claim detectable after the
  fact. Relay's probe table did not carry that column.

## Where this connects to Relay

- `D-02` is the decision record for the claim path. This note is the mechanism behind its
  `Rejected` section for the naive single-statement form.
- `P-04` is the reason the guard cannot live in the schema: no `CHECK` constraint can express
  "`succeeded` must not become `running`", because that needs two versions of one row.
- `D-02` previously recorded `SERIALIZABLE` as `[NO EVIDENCE]` on this project. Case D above is the
  first data point, for this one scenario only.
