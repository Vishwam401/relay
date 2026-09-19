# Post 01 — how it is being written

Written so a cold session can pick this up. Nothing here depends on chat memory.

## The loop, per beat

```
1. Claude says what must be understood BEFORE this beat can be written
2. Claude asks 3-5 questions on exactly that
3. User answers from his own head. `idk` is a valid answer and is recorded as one
4. Claude scores, corrects, and fills only the gaps the answers revealed
5. Claude re-checks with different questions on the same ground
6. Answers good enough (not senior level, enough to defend) -> move on
7. Claude states what this beat must contain and how much space it gets.
   No prose from Claude
8. User writes the beat, however rough
9. Claude marks it: what is right, what is missing, what would get corrected
   publicly. Hints first, not answers
10. User rewrites. If he still cannot get it, THEN Claude explains the concept
11. Repeat 8-10 until the beat holds. It goes into the final file in the user's words
```

## Sealed

`SEALED_POST_01_REFERENCE.md` is Claude's own full draft of this post. It contains
every answer. **It stays closed until the user's version of a beat is finished**, and
then only that beat's section is compared. Reading it early converts this exercise
back into the recognition problem it exists to avoid.

## Status 2026-09-19

`POST_01_FINAL.md` is the post to publish. It supersedes `SEALED_POST_01_REFERENCE.md`, which was
written before the isolation-level and rollback cases were measured and before the `InitPlan` proof
existed. Keep the sealed file only as history.

The final version was written by Claude at the user's request after the user worked through the
mechanism in the Q-and-A above. The user understands `InitPlan`, `EvalPlanQual`, the
condition-to-address framing, and why `SKIP LOCKED` is not the safety mechanism. He has not yet
written the prose himself. Beat 1 was drafted by him once and reviewed; that draft is not in the
final file.

## Progress

| Beat | Prereq questions | Written | Final |
|---|---|---|---|
| 1. The broken claim | done | in progress | |
| 2. The pattern | | | |
| 3. Reproducing it | | | |
| 4. What session 2 printed | | | |
| 5. Why version 1 does this | | | |
| 6. The fix, and what it does not fix | | | |
| 7. Two things I took away | | | |

## Score log

| Date | Beat | Asked | Self-answered | Notes |
|---|---|---|---|---|
| 2026-09-19 | pre-beat-1 sanity | 5 | 1 (half) | Q1/Q2 `idk`. Q3 half right (`SKIP LOCKED` saves waiting). Q3 conflated the lease/reaper duplicate (post 02) with the claim-time duplicate (this post). Q4 not understood. Q5 answered a different post's question |
| 2026-09-19 | beat 1 prereqs | 5 | 3 of 5, after pushback | Q1 right first try (atomicity is per-statement, not about concurrency); named it as ACID `A` vs `I`. Q2(b) right first try and strong (external side effects have no rollback). Q2(a) took two hints and then had to be given: nothing in the table is wrong after the failure. Q3 not answered directly; conflated the claim's `rowcount=0` branch with the `ON CONFLICT DO NOTHING` on the side-effect insert. Q4 good reasoning (two execution rows = retry, overlap = duplicate) but rests on `job_executions`, which is Relay's own instrument and which has no per-execution completion time, so the overlap check does not run against the current schema. Q5 vocabulary, supplied |

## Corrections that stuck during beat 1 prereqs

1. **Atomicity is not isolation.** `A` and `I` in ACID. A single statement being all-or-nothing says
   nothing about concurrent statements.
2. **Scope of atomicity is the statement or transaction, not the worker.** One worker can run two
   statements and hit the same problem.
3. **A plain `SELECT` takes no row lock.** That is why `FOR UPDATE` has to be written explicitly, and
   it is why the decision in the naive claim is made with nothing held.
4. **The guard does work.** `[MEASURED]` `AND status='pending'` gives `rowcount = 0` on the blocked
   session. The user believed it would still pick the row up because the writer had not committed;
   that is wrong, because the blocked statement re-reads the newest committed version after it wakes.
5. **Nothing in the table is wrong after the failure.** Variant 1 and variant 2 leave identical rows.
   `[MEASURED]`
6. **The logs do not show it either.** `worker.py:217` prints
   `[claim] Claimed job ... rowcount=1`, and both duplicate claimants would print that same line.
   `[INFERRED from source]`, not yet reproduced against a live worker pair.
7. **`job_executions` records dispatch, not duration.** Columns are
   `(id, job_id, worker_id, executed_at, claim_generation)`. Overlap between two executions cannot be
   computed from it. Open and worth measuring: whether `claim_generation` distinguishes a duplicate
   claim. Not measured, so not claimed.

## Beat 5 prereqs — done 2026-09-19

Plan reading and `InitPlan` taught from scratch after the user reported being blank on it.
Two extra measurements were run to teach it, both on disposable databases, both dropped after:

**Uncorrelated vs correlated, on the jobs query itself** `[MEASURED]`

| Subquery | Plan node | Runs | Cost |
|---|---|---|---|
| no reference to the outer row | `InitPlan 1 (returns $0)`, outside the scan | once | `27.57` |
| `j2.type = jobs.type` added | `SubPlan 1`, inside `Filter: (id = (SubPlan 1))` | per outer row | `15968.13` |

**Same contrast on a neutral table**, to separate the concept from the bug `[MEASURED]`

| Query | Plan | Cost |
|---|---|---|
| `salary > (SELECT avg(salary) FROM employees)` | `Filter: (salary > $0)` + `InitPlan 1` | `42.29` |
| `salary > (SELECT avg(salary) ... WHERE e2.dept = e.dept)` | `Filter: (salary > (SubPlan 1))` + `SubPlan 1` | `16341.63` |

Not measured, and deliberately not claimed: whether the recheck is safe in the correlated case.

Answers the user got right cold, after the teaching: uncorrelated vs correlated; why `SubPlan`
costs more; and the condition-to-address framing (`status` was a condition, `id = $0` is an
address, and the address does not carry `pending` with it).

**Carry-forward for beat 5:** the heuristic is the generalisable part. When a plan shows
`InitPlan`, ask what it collapsed into a constant and whether that constant can go stale. In a
read-only query a stale constant means a slightly wrong answer. In a write it means writing to
the wrong row.
