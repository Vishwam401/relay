# Blog Post 01 — Outline and evidence map

**Status: scaffolding only. Every word of prose in the published post must be yours.**
This file gives the structure, tells you which exact number/table/plan goes in which beat, and says
where that evidence lives so you never have to retype it from memory. Where a claim still needs
checking before publication it is marked **`⚠ VERIFY`**.

- **Working title (pick one, do not invent a clever one):**
  - *The Postgres job-claim query that silently claims the same job twice*
  - *`EvalPlanQual` is not a concurrency safety feature*
  - *Two workers, one job, no error: a lost update inside `UPDATE … RETURNING`*
- **Target length:** 1200–1800 words. If it exceeds 2000, a second finding has crept in — cut it out and
  make it post 02.
- **Audience:** a backend engineer who has written, or is about to write, a Postgres-backed queue. Assume
  they know `FOR UPDATE`. Do **not** assume they know `EvalPlanQual` or `InitPlan`.
- **One thing the reader must leave with:** a predicate recheck only rechecks the predicate you wrote.
- **Language:** English. Keep the compressed Hinglish lines for the repo, not the post.

---

## Beat 1 — The claim that is wrong (100–150 words)

Open with the broken assertion, not with context.

> This single statement is the most-recommended way to claim a job in Postgres. One variant of it hands
> the same job to two workers, returns `UPDATE 1` to both, and leaves the row in a state
> indistinguishable from one correct claim.

Then two sentences only: what Relay is (one line — a durable job engine on Postgres, no broker), and
that this was found by running two `psql` sessions, not by reading docs.

**Do not** write "in this post we will explore". **Do not** introduce the tech stack.

**Evidence:** none needed yet. This beat is a promise; beats 3–5 pay it.

---

## Beat 2 — The pattern everyone writes (150–200 words)

Show the code the reader will recognise as their own. This is the hook.

```sql
UPDATE jobs
SET    status = 'running'
WHERE  id = (SELECT id FROM jobs
             WHERE status = 'pending'
             ORDER BY created_at, id
             LIMIT 1)
RETURNING id, type, payload;
```

Say why it looks obviously correct — one statement, atomic by definition, no explicit lock to reason
about, `RETURNING` gives the worker its row in the same round trip. That apparent simplicity is exactly
why it gets recommended.

One aside worth a single sentence, because it earns credibility early: `ORDER BY created_at, id` needs
the `id` tiebreaker because jobs enqueued in one transaction share `created_at` exactly.

**Evidence map**
| Item | Source |
|---|---|
| The `ORDER BY created_at, id` tiebreaker reason | `docs/PROBLEMS.md` → `P-05` |

---

## Beat 3 — Reproduction the reader can run (200–250 words)

**This is the beat most posts skip and it is what makes yours trustworthy.** Give exact steps, not a
description of steps.

Setup: one table, a handful of `pending` rows, two `psql` sessions side by side.

```
Session 1:  BEGIN;
            <the statement above>      -- claims id = 76, DOES NOT COMMIT
Session 2:  <the same statement>       -- blocks
Session 1:  COMMIT;
Session 2:  <unblocks — read what it returned>
```

State plainly that session 1 is deliberately left uncommitted, because that is the whole experiment:
it holds the row lock while session 2 tries to claim.

Then three variants of session 2's statement, changing **one** thing each time:

1. `WHERE id = (subquery)` — plain subquery
2. `WHERE id = (subquery) AND status = 'pending'`
3. `WHERE id = (subquery)` where the subquery itself carries `FOR UPDATE SKIP LOCKED`

**Evidence map**
| Item | Source |
|---|---|
| Two-session setup, session 1 left uncommitted | `docs/DECISIONS.md` L306–308 (`D-02`, Din 6 Step 6) |
| The three variants | `docs/DECISIONS.md` L309–314 |

**Done — re-run on a disposable database on 2026-09-19.** See *Re-verification run* at the bottom. Use
ids **`1`, `2`, `3`** in the post, not `76`/`77`: a three-row table that the reader creates himself is
copy-pasteable, and `76` invites the question "what else is in that table?"

---

## Beat 4 — What actually happened (150–200 words)

The table. Paste it almost as-is — it took four paragraphs of reasoning to earn and it reads in ten
seconds.

Use the re-measured numbers, not `D-02`'s original ids.

| Variant | Outer `WHERE` | Subquery | Session 2 blocked? | id returned | `rowcount` | Final rows | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | `id = (subquery)` | plain | **yes**, on the row lock | **`1` — the same id session 1 claimed** | **1** | `1 running, 2 pending, 3 pending` | silent duplicate claim |
| 2 | `id = (subquery) AND status='pending'` | plain | **yes** | none | **0** | `1 running, 2 pending, 3 pending` | safe, but it waited and got nothing |
| 3 | `id = (subquery)` | `FOR UPDATE SKIP LOCKED` | **no** | **`2` — the next row** | **1** | `1 running, 2 running, 3 pending` | safe, and it got useful work |

**Include the `Final rows` column. It is the argument.** Variant 1 and variant 2 end in *byte-identical*
table state — `1 running, 2 pending, 3 pending` — and one of them handed the same job to two workers. No
query against `jobs` can tell them apart afterwards.

Three sentences of commentary, hardest one last:

- No error. No warning. Both sessions got `rowcount = 1`.
- The row's final state is `status = 'running'` — **exactly what one correct claim looks like.**
- The safe run and the broken run leave the table in the same state, so there is no post-hoc query that
  finds this. It is only observable while it is happening.

**Evidence map**
| Item | Source |
|---|---|
| The table | Re-measured 2026-09-19, see *Re-verification run* |
| Original run this replicates | `docs/DECISIONS.md` L309–314 |
| "final state is what one correct claim looks like" | `docs/DECISIONS.md` L337–339 |

---

## Beat 5 — Mechanism (300–400 words, the core of the post)

Slow down here. Four moves, in this order:

**5a. Show the plan — and show *both* plans side by side.** Do not redraw them; the plan *is* the
diagram. `[MEASURED 2026-09-19, Postgres 16.14, disposable DB, READ COMMITTED]`

Variant 1, the unsafe one:

```
Update on jobs
  InitPlan 1 (returns $0)
    ->  Limit
          ->  Sort  (Sort Key: jobs_1.created_at, jobs_1.id)
                ->  Seq Scan on jobs jobs_1   Filter: (status = 'pending'::text)
  ->  Index Scan using jobs_pkey on jobs
        Index Cond: (id = $0)            <-- this is the whole qualification
```

Variant 2, the safe one. **The diff is one line:**

```
  ->  Index Scan using jobs_pkey on jobs
        Index Cond: (id = $0)
        Filter: (status = 'pending'::text)     <-- the only difference
```

**This side-by-side is the strongest single artifact in the post and it did not exist in the original
notes.** You can *see* the safety in `EXPLAIN`. One `Filter:` line separates a correct claim mechanism
from a silent duplicate one, and it is visible before you ever run the race. Lead beat 5 with it.

**5b. `InitPlan`, in one paragraph.** The subquery does not reference the outer row, so it is
*uncorrelated*. Postgres evaluates it **once, before the scan**, and freezes the result into a constant
`$0`. Therefore the outer statement's qualification is literally `Filter: (id = $0)`.

**5c. `EvalPlanQual`, in one paragraph, with an inline definition.** Under `READ COMMITTED`, a writer
that blocks on a locked row does **not** wake up holding a stale tuple. It re-fetches the newest
committed version and re-evaluates the statement's qualification against it. That sounds like safety,
and that is the trap.

**5d. Put 5b and 5c together — this is the punchline.** In variant 1 the qual is `id = $0`, which is
*still true* after session 1 set `status = 'running'`. The recheck passes. The `UPDATE` applies a second
time and `RETURNING` hands back the same id. In variant 2 the qual contains `status`, the recheck fails,
and the row count is `0`. **Same mechanism, opposite outcomes, and the only difference is whether the
column that changed is in your predicate.**

Then name it: this is a textbook lost update (DDIA Ch 7), and the fix DDIA names is compare-and-set.

**Evidence map**
| Item | Source |
|---|---|
| Both `EXPLAIN` plans, incl. the one-line diff | **Re-measured 2026-09-19, see *Re-verification run* below** |
| `InitPlan` / uncorrelated explanation | `docs/DECISIONS.md` L328–330 |
| `EvalPlanQual` recheck reasoning | `docs/DECISIONS.md` L331–339 |
| Lost update / DDIA reference | `docs/DECISIONS.md` L340–345 |

**One correction to carry into the post.** `D-02` L319–326 records the outer node as
`Seq Scan on jobs · Filter: (id = $0)`. On the re-run it is
`Index Scan using jobs_pkey · Index Cond: (id = $0)`. The *finding is unchanged* — `status` is still
absent from the outer qualification, which is the entire mechanism — but the node name differs with table
size and statistics. **Paste your own plan and say which Postgres version and row count produced it**,
otherwise a reader on a different shape will think you made it up.

---

## Beat 6 — The fix, and what it does not fix (200–250 words)

**6a. Price the two halves separately.** This is the part almost nobody writes, and it is the most
useful table in the post.

| Half | Provides | What its absence costs |
|---|---|---|
| `FOR UPDATE SKIP LOCKED` in the claim `SELECT` | **liveness** — never wait behind a row a peer holds | variant 2: correct, but the worker blocks and is then told `rowcount = 0` for its trouble |
| `AND status = 'pending'` on the `UPDATE` | **safety** — the old value is part of the predicate | variant 1: a silent duplicate claim |

Then the sentence that stops readers cargo-culting `SKIP LOCKED`: **`SKIP LOCKED` does not prevent
duplicate claims.** The row lock plus the compare-and-set do. Back it with the measured contrast —
with a 6 s lock held on the oldest pending row, the `SKIP LOCKED` worker started real work **1.25 s**
in, while a plain `FOR UPDATE` worker waited the full **6 s**. And separately, two workers claiming
different rows **6 ms** apart with no `SKIP LOCKED` at all produced no duplicate.

**6b. Be fair to the single-statement form.** Variant 2 — the same single statement *with the guard in
the predicate* — is a sound claim mechanism, and arguably simpler than the two-statement form. What it
gives up is variant 3's property: on collision, variant 3 has both workers doing useful work, variant 2
has the loser blocked and then handed nothing.

This fairness is not politeness. A post that says "the pattern is broken" is wrong and will be corrected
in the comments. **The naive form is broken. The guarded form is fine.** That distinction is the post.

**6c. State the residual.** The guard lives in your discipline, not in the schema: no `CHECK` constraint
can express "`succeeded → running` is illegal", because that needs two versions of one row. Every
`status` update must carry the guard and the database will not remind you.

**Evidence map**
| Item | Source |
|---|---|
| Two-halves table | `docs/DECISIONS.md` L349–351 |
| `1.25 s` vs `6 s` lock wait | `docs/DECISIONS.md` L384–390 (`[MEASURED]`, Din 4) |
| `6 ms` apart, no duplicate, no `SKIP LOCKED` | `README.md` → *The claim, in one query* |
| Variant 2 is sound; what it gives up | `docs/DECISIONS.md` L403–411 |
| No constraint can express the transition | `docs/PROBLEMS.md` → `P-04`; `docs/DECISIONS.md` `D-06` |

**Do not claim any throughput comparison.** `P-12` disqualified the numbers that looked like one — both
Din 4 two-worker runs had a staggered second worker, so the splits are start-time artifacts. There is no
like-for-like run of plain `FOR UPDATE` in either direction. Writing a throughput line here is the one
mistake that would cost the post its authority.

---

## Beat 7 — Generalisation (80–120 words)

Two ideas, then stop. No summary, no "thanks for reading", no bullet list of takeaways.

1. **A predicate recheck rechecks your predicate, not your intent.** `EvalPlanQual` is not a concurrency
   safety feature. Variants 1 and 2 are the same mechanism producing opposite outcomes.
2. **The generalisation past Postgres:** a mechanism whose name sounds like a guarantee is the most
   dangerous kind, because the name is what you remember under pressure. Same shape as `timeout=0.5`
   bounding intent rather than reality, and `SIGTERM` requesting a stop rather than causing one.

Close with the uncomfortable observation from beat 4 rather than a conclusion: this failure leaves no
trace. A correct claim and a double claim produce the same row.

**Evidence map**
| Item | Source |
|---|---|
| Generalisation wording | `docs/DECISIONS.md` L340–345 |
| The "name promises more than the mechanism delivers" family | `docs/PROBLEMS.md` → `P-04` (ending), `P-02` |

---

## Diagrams — two, and only two

### Diagram 1 — the race (goes in beat 4, above the table)

**Must be a timeline, not a flowchart.** A flowchart has no time axis and the entire finding is about
time. Mermaid `sequenceDiagram`, two lifelines, vertical order = real time order.

```mermaid
sequenceDiagram
    autonumber
    participant S1 as Session 1
    participant DB as jobs row id=76
    participant S2 as Session 2

    S1->>DB: BEGIN; UPDATE ... WHERE id=(subquery)
    Note over DB: row locked, status='running'<br/>NOT COMMITTED
    S2->>DB: UPDATE ... WHERE id=(subquery)
    Note over S2: InitPlan already froze $0 = 76<br/>then blocks on the row lock
    S1->>DB: COMMIT
    DB-->>S2: EvalPlanQual re-fetches newest version<br/>rechecks Filter: (id = $0) -- still true
    DB-->>S2: UPDATE 1, RETURNING id = 76
    Note over S1,S2: both sessions believe they own job 76
```

Caption underneath, bold, one line: *what this diagram is drawn to make visible* — that `$0` was frozen
**before** the block, so the recheck after the unblock had nothing left to catch.

### Diagram 2 — where the two defences sit (goes in beat 6)

A small flowchart is correct here, because this one has no time in it. Claim `SELECT` → guarded
`UPDATE`, with `SKIP LOCKED` labelled **liveness** on the first and `AND status='pending'` labelled
**safety** on the second. Two boxes, two labels, nothing else.

Do **not** reuse the full Relay architecture diagram from `README.md` here. It is correct and it is for a
different purpose; in this post it would show the reader eight transaction boundaries when the point
involves two statements.

### Diagram rules

- Author in Mermaid, commit the source under `docs/blog/`, **and export PNG.** Dev.to and GitHub render
  Mermaid; Medium and LinkedIn do not.
- One idea per diagram. Two ideas in one diagram communicates zero.
- Every diagram gets a bold one-line caption saying what it is drawn to make visible.
- Alt text on both images, describing the finding rather than the shape ("timeline showing both sessions
  told they own job 76"), not "sequence diagram".

---

## Re-verification run — `[MEASURED 2026-09-19]`

Run by Claude at outline time, so the post does not rest on a five-week-old reviewer measurement.

- **Environment:** `postgres:16` container, `server_version = 16.14 (Debian 16.14-1.pgdg13+1)`,
  `default_transaction_isolation = read committed`, port `5433`.
- **Database:** `blogprobe`, created and dropped for this run. The `relay` database was **not touched** —
  no rows read, written or deleted in it.
- **Table:** `jobs (id bigserial PK, type text, status text DEFAULT 'pending', created_at timestamptz)`.
  Three `pending` rows, `created_at` one second apart so the `ORDER BY` is deterministic.
- **Sessions:** two separate `asyncpg` connections. Session 1 opened a transaction, ran the variant, and
  was held uncommitted for `1.0 s` while session 2 issued the same statement; blocking was detected by
  session 2's future still being pending at the 1 s mark. Then session 1 committed and session 2's result
  was read.
- **`n = 1` per variant.** Each variant ran once, against a freshly truncated table. This is a
  deterministic mechanism demonstration, not a statistical result, and the post should say so.
- **Results:** exactly as recorded in beats 4 and 5a above. All three variants reproduced the behaviour
  `D-02` recorded. Variant 1 gave a duplicate claim; variant 2 gave `rowcount = 0`; variant 3 skipped to
  the next row without blocking.
- **One difference from `D-02`:** outer node is `Index Scan using jobs_pkey / Index Cond: (id = $0)`
  rather than `Seq Scan / Filter: (id = $0)`. Mechanism identical, node name is size-and-statistics
  dependent.
- **New, and not in `D-02`:** the variant-1 vs variant-2 plan diff is a single `Filter:` line on the
  outer node. The safety is visible in `EXPLAIN` before any race is run.
- **Cleanup:** `blogprobe` dropped, probe script `tmp_blog_probe.py` deleted, `relay-db-1` left running
  (it was started for this run — stop it with `docker compose down` if you want it off).

---

## Pre-publication checklist

- [x] Reproduction re-run on a **throwaway** database with a minimal `jobs` table; all three variants
      re-observed; ids in the post match what was actually seen (`1`, `2`, `3`)
- [x] `EXPLAIN` output in beat 5 is freshly measured, not `D-02`'s `[MEASURED-R]` one
- [x] Postgres version stated (`16.14`) — behaviour here is isolation-level and planner dependent, so a
      reader on a different version needs to know what was run
- [x] `READ COMMITTED` named explicitly as the isolation level
- [ ] `n = 1` per variant stated in the post, so nobody reads it as a benchmark
- [ ] No throughput claim anywhere (`P-12`)
- [ ] Every mitigation reads `narrows` / `reduces`, never `closes` / `eliminates` / `prevents entirely`
- [ ] Every number carries its condition and its `n`
- [ ] Beat 6b present — the guarded single statement is explicitly called sound
- [ ] Word count under 2000
- [ ] Both diagrams have captions and alt text
- [ ] Links to `docs/DECISIONS.md` `D-02` and `docs/PROBLEMS.md` for readers who want the full trail

---

## Deliberately out of scope for post 01

These are the rest of the series. Do not let any of them leak into this post; each one is strong enough
to stand alone, and spending them here wastes them.

| Candidate | Core finding | Evidence |
|---|---|---|
| **Post 02 — fencing** | A stale worker's terminal mark landed `32.973 s` before the live worker finished. `claim_generation` fence turns it into `rowcount = 0` | job `126`, job `128`, job `7` (`README.md` failure matrix rows 4–5) |
| **Post 03 — bounded retries that are not bounded** | `attempts = 4` against `MAX_ATTEMPTS = 3`; the bound governs scheduling, not dispatches | job `108`, `P-27` |
| **Post 04 — jitter erased by sampling** | Jitter narrower than the `2.0 s` poll interval; the convoy it was added to prevent re-formed, `33–69 ms` apart inside one tick | `README.md` → *State machine* |
| **Post 05 — a size limit the sender controls** | `413` enforced from `Content-Length`; three differential requests distinguished a working limit from a decorative one, `loc: ["body", 306274]` | `P-08` |
| **Post 06 — the stuck row nothing looks at** | `kill -9` mid-handler leaves `status='running'`; a fresh polling worker ignores it forever because the claim query says `WHERE status='pending'` | job `63`, `D-01` Cost 1 |
