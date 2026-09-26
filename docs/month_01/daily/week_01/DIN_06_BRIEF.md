# DIN 6 — `DECISIONS.md`: write `D-01` and `D-02`, and refuse to write a single unbacked claim

**Week 1 · Layer L1 · Budget ~2h15m** · Plan: [`../planning/WEEK_01.md`](../../planning/WEEK_01.md) (DIN 6 section)

> **How to use this file.** Part A + Part C are safe to paste to Gemini, along with
> [`GEMINI_RULES.md`](../../../daily/GEMINI_RULES.md) and the SHARED CONTEXT block from the week plan.
> **Part B is not.** `DIN_06_KEY.md` stays closed until each step's experiment has actually run.
>
> **Order per step:** answer that step's Part B questions from your own head → do the work → run
> Part C → compare with your prediction and write your *own* explanation of any difference →
> *then* open that step's KEY section. `idk` is a legitimate answer and is recorded as one.

---

## Today in one line

The week plan calls `DECISIONS.md` *"hafte ka asli deliverable"* — code can be a bit unfinished,
this cannot. But Din 4 and Din 5 both produced a specific failure: **a conclusion written before
the number that supports it existed.** So today is not "write two ADRs". It is **write two ADRs in
which every `Cost` and `Rejected` line names its evidence — and where the evidence does not exist,
either run it today or downgrade the wording.**

Two of those lines get run today, and they are the two most interesting experiments left in Week 1.
Neither has ever been executed.

---

## Bench state as of right now `[MEASURED by reviewer, 2026-08-18, after Din 5 close]`

```
jobs: 74 rows — succeeded 63, failed 8, running 3, pending 0     max(id) = 74
  running = 41  (Din 4 lock probe — claim committed, handler NEVER entered, no execution row)
            63  (Din 5 kill -9, 3s into an 8s handler — execution row present)
            65  (Din 5 kill -9, 3s into an 8s handler — execution row present)
attempts = 0 on every row in the table

job_executions: 46 rows, max(id) = 47      duplicates over jobs 59-74: 0
  jobs 55-58 and 74 are reviewer probe jobs, deliberately not deleted

worker processes: 0      connections to relay: 1 (psql)      idle in transaction: 0
```

**Three things to carry into today:**

1. **Those three `running` rows are Week 2's test fixture. Do not clean them up, and do not fix them.**
   Today you *cite* them; you do not touch them.
2. **Job 41 is not the same kind of stuck row as 63 and 65** — no execution row, so no handler ever
   ran. `P-16` is the write-up. This distinction is load-bearing in Step 2.
3. **`pending = 0` right now.** Step 6 needs pending rows and will seed them. Step 0 records the
   count so the closing arithmetic still reconciles.

---

## What Din 5 changed about today, before you write a word

Din 5 did not just add measurements. It **added one argument to `D-01` and removed one from `D-02`.**

| | What changed |
|---|---|
| **`D-01` gains its strongest Cost** | Every cost previously listed for Postgres-as-queue is about *load* — polling, MVCC bloat, vacuum, blast radius. Din 5 measured a **correctness** cost: job 63 is `running`, nothing recovers it, and a fresh polling worker ignored it. A broker redelivers an unacked message for free; Postgres does not. So the trade is not "free outbox in exchange for polling overhead" — it is **"free outbox in exchange for writing redelivery yourself."** |
| **`D-02` loses a Rejected reason** | The plan suggests rejecting plain `FOR UPDATE` with *"Din 4 C1 me measured — blocking se throughput gira."* `P-12` disqualified that number: both Din 4 two-worker runs had a staggered second worker. The **valid** Din 4 measurement is about *lock wait* — `skip_locked` began real work **1.25 s** into a 6 s lock, plain `FOR UPDATE` waited the full 6 s. Use that. The throughput version has no evidence in either direction. |
| **`D-02` gains a clean baseline** | Din 5's three-worker run: first claims within **12.6 ms**, survivors split **4/4**, drain **32.2 s** against a predicted 32 s, **0 duplicates**, and the two survivors claimed **4 µs apart** in convoy (`P-14`). Contention was near-worst-case, which makes the safety result stronger than a realistic workload would give. |
| **`D-02` still cannot claim *why* it is safe** | `SKIP LOCKED` skipping a locked row, or the compare-and-set guard returning `rowcount = 0`, are both consistent with Din 5's data. `rowcount = 0` has **never been observed** in this project. Step 6 is where that finally gets tested. |

---

# PART A — Steps

Nine steps. A documentation day still has to end each step in something **checkable**, and two steps
end in something **executable**. If a step passes ~15 minutes, it is too big — split it.

**No changes to `src/` today.** Steps 1 and 6 are `psql`-only. Part D lists what that protects.

---

## Step 0 — Clean bench, and a claims ledger (10 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| ADR | Architecture Decision Record — one file entry per decision, with the *rejected* options kept |
| Provenance | Where a claim came from: measured by you, measured by someone else, or inferred |
| Claims ledger | A table of every assertion you intend to make, with its evidence status, written *before* prose |

**Do:**
1. Run C0. Record worker count, connections, status counts, `max(id)`, `pending` count.
2. Before writing any prose, list **every** claim you intend to put in `D-01`'s and `D-02`'s
   `Cost` and `Rejected` fields. One line each. Do not write reasons yet — just the claims.
3. Mark each one: `[MEASURED-mine]`, `[MEASURED-R]`, `[INFERRED]`, or **`[NO EVIDENCE]`**.
4. Count the `[NO EVIDENCE]` rows. **That number is today's actual workload.**

**Runnable end state:** a ledger table where every row has a provenance tag, and a count of the
rows that need either an experiment or a softened sentence.

---

## Step 1 — Prove `D-01`'s headline argument, which has never actually been run (15 min)

`D-01`'s central claim is the transactional enqueue: business write and job enqueue in **one**
transaction, so both happen or neither does. It is the strongest argument in either entry, it is the
one you will use in interviews, and **nobody in this project has ever demonstrated it.**

**Terms used in this step**

| Term | What it is |
|---|---|
| Dual-write | Writing the same logical fact to two systems that cannot share a transaction |
| Outbox pattern | Writing the "please send this" record into the *same* database as the business row, and delivering it separately |
| `TEMP TABLE` | A table visible only to your session, dropped when the session disconnects |
| `RETURNING` | Makes an `INSERT`/`UPDATE` return the affected rows in the same statement |

**Do — three cases, in one `psql` session (commands in C1):**
1. Create a **temp** `orders_probe` table. *Why temp: Day 1 measured that leftover real tables break
   `alembic check` and would make the next `--autogenerate` emit a silent `DROP TABLE`. A temp table
   cannot do that.*
2. **Case A — one transaction, committed.** Insert an order and a `send_receipt` job together, commit.
   Count both.
3. **Case B — one transaction, interrupted.** Insert the order, then `ROLLBACK` as if the process died
   before it could enqueue. Count both.
4. **Case C — two transactions, interrupted between them.** Commit the order. Stop. Do *not* insert the
   job. This is what Redis or RabbitMQ forces you into. Count both.
5. Write down, in one sentence each, what state Cases B and C leave behind and **which one is
   permanent.**

**Runnable end state:** three measured counts, and one sentence naming which case produces a state no
retry can repair.

---

## Step 2 — Din 5's missing Step 6: the four Week 2 answers (15 min)

Din 5's Step 6 was not delivered, and it is not optional homework — it **is** `D-01`'s Cost field.
Three lines maximum each, your own words.

**Do:**
1. What exactly is lost when a worker dies mid-job? Name the record, not the vibe.
2. Who can bring the job back, and **why can it not be the worker itself, or Postgres?**
   (Din 5 measured both halves of this. Use the measurements.)
3. Whatever brings it back must decide *"is this worker dead, or just slow?"* — **on what
   information?** List what `jobs` can currently tell it, and be specific about what is missing.
   Then say whether `job_executions` helps, and what it costs to depend on it (`D-21`, `P-11`).
4. If it guesses wrong — worker alive, merely slow, job reset to `pending` — **which contract point
   breaks and which one is protected?** Then answer the same question for guessing the other way.

**Do also:** look at jobs 41 versus 63 in the bench block. Write one line on why a reaper that
handles 63 correctly might still get 41 wrong.

**Runnable end state:** five short written answers, and the sentence Week 2 starts from.

---

## Step 3 — `D-01`: Problem, Options, Chose (15 min)

**Do:**
1. Open `DECISIONS.md`, find the reserved `D-01`, and write `Problem` / `Options` / `Chose`.
2. In `Chose`, use Step 1's **measured** output for the transactional-enqueue argument. Cite the
   three cases. This is the difference between an entry that says "both or neither" and one that
   shows it.
3. Bring in the Week 0 four-roles model: name which role Postgres is playing here, and what changes
   when one process plays two roles.
4. State the Redis-specific correctness point explicitly: Redis default durability versus contract #1.

**Runnable end state:** three fields written, with the `Chose` field citing Step 1's own output.

---

## Step 4 — `D-01`: `Cost` and `Rejected`, headed by Din 5 (15 min)

> **Rule from the plan: `Cost` khali nahi chhodna.** If you cannot write the cost, you have not
> understood the decision. Today's version is stricter — **every cost line carries its provenance tag.**

**Do:**
1. Write the `Cost` field. Lead with Din 5's finding, phrased as ownership rather than performance,
   and cite job 63 with the stuck-count reading from C0. Then the load costs: polling (`P-10`'s
   0.5 tx/s per idle worker, and `P-13`'s measured 3 idle connections for zero work), MVCC churn,
   the claim query at depth (`P-03`, unmeasured, Week 4), shared blast radius.
2. Add `P-15`: the stuck row is reachable from the **graceful** path too, whenever handler duration
   exceeds the supervisor's grace period. So the cost is not conditional on anyone using `kill -9`.
3. Write `Rejected` for Redis and RabbitMQ. For each, name the one thing it does **better** than
   Postgres before saying why it lost. An ADR that cannot state its rejected option's strength is
   not an ADR.
4. Add a `Revisit when:` line.

**Runnable end state:** a `Cost` field where every line ends in a provenance tag, and a `Rejected`
field where each option's genuine advantage is stated.

---

## Step 5 — `D-02`: read what the code actually does before writing about it (10 min)

Din 1 caught a real bug by **compiling** the model's DDL instead of reading the source. Din 2's `413`
bug survived a code read. Do not describe the claim query from memory.

**Do:**
1. Start one worker for ~10 s with the queue empty and copy the **actual** claim SQL out of the
   `echo=True` output (C5 has the command). Paste it into `D-02` verbatim.
2. Write `Problem` and `Options` — all five from the plan: `FOR UPDATE`, `FOR UPDATE SKIP LOCKED`,
   `UPDATE ... WHERE status='pending' RETURNING`, advisory lock, `SERIALIZABLE`.
3. For each option, one line: **what does the second worker experience?** Wait, skip, conflict, or error.
4. Stop the worker. Confirm 0 worker processes before Step 6 — Step 6 is `psql`-only and a live worker
   will eat its rows (`P-13`).

**Runnable end state:** the real SQL text in the entry, a five-row options table, and 0 workers running.

---

## Step 6 — Run option (c). It is the only line in either entry with zero evidence (15 min)

The plan asks directly: *"kya `UPDATE ... RETURNING` bhi kaam kar jaata?"* Nobody has run it. It is
the one option that would claim atomically with **no explicit lock at all**, and you cannot honestly
reject it without knowing what it does.

**Terms used in this step**

| Term | What it is |
|---|---|
| `rowcount` | How many rows a statement actually affected. `0` means the `WHERE` matched nothing |
| Compare-and-set | `UPDATE ... WHERE id=$1 AND status='pending'` — the old value is part of the predicate |
| Correlated subquery in `WHERE` | `WHERE id = (SELECT id FROM ... LIMIT 1)` — picks the target row inside the same statement |

**Do — two `psql` sessions, side by side (exact SQL in C6):**
1. Seed 3 `sleep` jobs. Record the ids.
2. **Variant 1, the naive form.** Session 1: `BEGIN`, then
   `UPDATE jobs SET status='running' WHERE id = (SELECT id FROM jobs WHERE status='pending' ORDER BY created_at, id LIMIT 1) RETURNING id, status;`
   **Do not commit.** Session 2: run the identical statement. Record: does session 2 return
   immediately, block, or error? Then commit session 1 and record what session 2 does **the moment
   the commit lands** — the `id` it returns and its `rowcount`.
3. **Variant 2, with the guard.** Roll everything back to `pending` first. Repeat, but add
   `AND status='pending'` to the **outer** `UPDATE`'s `WHERE`. Record session 2's `rowcount`.
4. **Variant 3.** Repeat variant 1 but put `FOR UPDATE SKIP LOCKED` inside the subquery. Record which
   `id` session 2 gets.
5. Reset the three jobs to `pending`, or leave them and record it — either is fine, say which.

**Runnable end state:** three variants, each with session 2's returned `id` and `rowcount` written
down. One of these three is a claim mechanism you would ship. Two are not.

---

## Step 7 — `D-02`: `Chose`, `Cost`, `Rejected`, and the honesty audit (15 min)

**Do:**
1. Write `Chose` — (b) — justified by the **three behaviours**, not by a preference: wait vs
   abort-and-retry vs skip, and what each does to a worker that has other work available.
2. Write `Cost`. At minimum: ordering becomes more approximate (`P-05`), an extra `UPDATE` per claim
   (write amplification, MVCC churn), the `LIMIT` subtlety, and one round trip per claim with the
   poll interval bounding throughput (`P-10`).
3. Write `Rejected` for all four losing options, with Step 6's output carrying option (c) and Din 4's
   **lock-wait** number carrying option (a).
4. **The audit — do this last and do it against the file, not from memory.** Re-read both finished
   entries and, for every sentence containing a number or the word *measured*, confirm the number
   exists in `logs/WEEK_01.md`. Two specific traps:
   - Any throughput comparison between claim strategies. **It does not exist.** (`P-12`)
   - Any claim that `SKIP LOCKED` is *why* Din 5 produced no duplicates. That is `[INFERRED]`
     unless Step 6 changed your view — say which mechanism your own data supports.
5. Then re-read for **elimination language**. `narrows`, not `closes`. `reduces`, not `zero`. This is
   the recurring wording error across the whole log; two finished ADRs are the worst place for it.

**Runnable end state:** both entries complete, and an audit pass where every number was traced to a
line in the log or reworded.

---

## Step 8 — Week 1 Definition of Done, and DDIA Ch 7 (15 min)

**Do:**
1. Open the Week 1 DoD in `planning/WEEK_01.md`. Tick honestly. For every unticked item write one
   line: *deliberately deferred* (with the owner) or *slipped* (with what it needs).
2. Finish **DDIA Ch 7, second pass, pp. 233–251** — carried since Din 4. One line on which of Din 5's
   observations the chapter already names. The stuck-job / dead-versus-slow problem in `P-16` has a
   name in the literature; find whether Ch 7 gives it one.
3. Run C8 and confirm the bench closes.

**Runnable end state:** a ticked DoD with reasons on every gap, one line on DDIA, and a reconciled bench.

---

# PART B — Prediction questions

> ⛔ **DO NOT PASTE THIS SECTION TO GEMINI. DO NOT OPEN THE KEY TO ANSWER IT.**
>
> Answer each step's questions **before** doing that step, from your own head, in writing.
> Vocabulary questions are fine to ask Gemini — the glossaries in Part A exist for that. If the
> answer to your question would also answer one of these, do not ask it.
>
> **Din 5's predictions were never handed over, so Din 5 is unscored.** Write these down somewhere
> you will actually paste back.

```
STEP 0 — the ledger
0.1  Before counting: guess how many of your intended Cost/Rejected claims have NO evidence.
     Write the number now, then compare after the ledger. Which direction were you wrong in?
0.2  A claim tagged [MEASURED-R] is a number someone else produced. Is it usable in an ADR?
     Say what it is and is not usable for.

STEP 1 — transactional enqueue
1.1  Case B rolls back an order INSERT and a job INSERT together. Afterwards, is the jobs
     sequence value the same as before the transaction? Answer from Din 2's own measurement.
1.2  Case C commits the order and never inserts the job. Name what a retry can and cannot fix.
     Is there any query that could later detect this state?
1.3  You are using a TEMP table so alembic cannot be affected. What would go wrong if you used
     a real table and forgot to drop it? You have measured this exact failure — where?
1.4  The outbox pattern normally needs a separate relay/publisher process. Relay's workers poll
     the jobs table directly. Which component of the classic outbox pattern is Relay skipping,
     and what does it buy by skipping it?

STEP 2 — Week 2's problem statement
2.1  Write the reaper's decision rule as a single SQL predicate, using ONLY columns that exist
     in jobs today. Then state why it does not work.
2.2  What is the smallest schema addition that makes it work, and what NEW failure does that
     addition introduce?
2.3  Job 41 has no execution row; job 63 does. Which of the two is more dangerous to reset, and
     why? Does your answer change if Relay had idempotent handlers?
2.4  P-15 says there is no handler timeout. If you add a lease shorter than the slowest handler,
     what have you built on purpose?

STEP 3-4 — D-01
3.1  Postgres is playing two of Week 0's four roles at once here. Name them, and name the
     failure that becomes possible only because one process plays both.
3.2  RabbitMQ redelivers an unacknowledged message when a consumer dies. Is that redelivery
     at-least-once or exactly-once? What does the consumer have to do for it to be safe?
3.3  Redis can be configured with AOF + fsync-always. Does that make Redis-as-queue satisfy
     Relay's contract #1? Name what is still missing.
3.4  D-01's Cost gains "you write redelivery yourself". Estimate: is that a Week 2 cost only,
     or does it recur? What keeps costing after the reaper is written?

STEP 5-6 — D-02, and option (c)
5.1  Predict the exact claim SQL the worker emits. Write it out, then compare with the echo.
     Anything you got wrong is a thing you believed about your own code.
5.2  Variant 1: session 1 holds an uncommitted UPDATE on the oldest pending row. Session 2 runs
     the identical statement. Does it return immediately, block, or error? Why?
5.3  Variant 1: when session 1 commits, what id does session 2 return, and what is its rowcount?
     Answer in terms of what session 2's WHERE clause is actually matching on. This is the
     question of the day -- take it slowly.
5.4  Variant 2 adds AND status='pending' to the outer UPDATE. Predict session 2's rowcount.
     Which Din 1 decision is this exact predicate?
5.5  Variant 3 puts FOR UPDATE SKIP LOCKED in the subquery. Which id does session 2 get?
5.6  Din 4 named EvalPlanQual. Which of the three variants does it explain, and does it produce
     a safe or an unsafe outcome there?
5.7  Din 5 saw two workers claim 4 microseconds apart with 0 duplicates. After running Step 6,
     say which mechanism you now believe was responsible -- and what evidence would settle it.

STEP 7-8 — audit
7.1  Name one sentence you expect to have to soften in the audit pass. Predict it before you look.
7.2  Week 1's DoD -- predict how many items you will tick. Then count.
```

---

# PART C — Verification

Every check is written to **distinguish** a correct entry or result from a plausible wrong one. For
each, ask the Din 2 question: *what wrong implementation would also pass this?*

Environment: PowerShell, repo root, `.venv` active. Statement separator is `;`, never `&&`.
Step 6 needs **two** `psql` sessions side by side, so open two terminals for it.

> **Clock trap.** The database session's `TimeZone` is `Etc/UTC` `[MEASURED]`; the worker's
> `echo=True` lines are local (IST, +5:30). Either convert with
> `executed_at AT TIME ZONE 'Asia/Kolkata'` or stay inside one clock per calculation, and write down
> which clock each number is in.

---

### C0 — Baseline (2 min)

```powershell
Get-CimInstance -ClassName Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*src.worker*' } | Select-Object ProcessId, CreationDate
docker compose exec -T db psql -U postgres -d relay -c "SELECT count(*) AS conns, count(*) FILTER (WHERE state LIKE 'idle in transaction%') AS idle_in_txn FROM pg_stat_activity WHERE datname='relay';" -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT max(id) FROM jobs;" -c "SELECT count(*) FROM job_executions;" -c "SELECT count(*) AS stuck FROM jobs WHERE status='running';"
```

Expected `[MEASURED 2026-08-18]`: **0** workers, **1** connection, **0** `idle in transaction`,
`running = 3`, `pending = 0`, `max(id) = 74`, 46 execution rows.

| Would also pass "the bench looks fine" | Caught by |
|---|---|
| A forgotten worker eating Step 6's seeded rows | The process list, before **and** after (`P-13`) |
| A probe session left mid-transaction | `idle_in_txn` — this instance has `idle_in_transaction_session_timeout = 0`, i.e. unlimited (`P-06`) |

---

### C1 — Transactional enqueue, three cases (Step 1)

One `psql` session, interactive:

```powershell
docker compose exec -it db psql -U postgres -d relay
```

```sql
CREATE TEMP TABLE orders_probe (id bigserial PRIMARY KEY, amount int NOT NULL);

-- Case A: one transaction, committed
BEGIN;
  INSERT INTO orders_probe (amount) VALUES (500) RETURNING id;
  INSERT INTO jobs (type, payload) VALUES ('send_receipt', '{"case":"A"}') RETURNING id;
COMMIT;
SELECT count(*) AS orders FROM orders_probe;
SELECT count(*) AS jobs FROM jobs WHERE payload->>'case' = 'A';

-- Case B: one transaction, interrupted before the enqueue
BEGIN;
  INSERT INTO orders_probe (amount) VALUES (900) RETURNING id;
  -- process "dies" here
ROLLBACK;
SELECT count(*) AS orders FROM orders_probe;
SELECT last_value, is_called FROM jobs_id_seq;

-- Case C: two transactions, interrupted between them  (the Redis/Rabbit shape)
BEGIN;
  INSERT INTO orders_probe (amount) VALUES (1200) RETURNING id;
COMMIT;
-- process "dies" here. No job is inserted. Deliberately.
SELECT count(*) AS orders FROM orders_probe;
SELECT count(*) AS jobs FROM jobs WHERE payload->>'case' = 'C';
```

Required: Case A → 1 order, 1 job. Case B → order count **unchanged from Case A**. Case C → order
count **incremented**, job count **0**.

| Would also pass "the outbox argument holds" | Caught by |
|---|---|
| Only running Case A — both rows appear, proving nothing about failure | Case B and Case C are the argument. A alone is just an insert |
| Treating Case B and Case C as the same failure | Compare the two order counts. One rolled back, one is **permanent** — that asymmetry is the entire entry |
| Using a real table and breaking `alembic check` later | `CREATE TEMP TABLE`. Verify after with `alembic check` |

Afterwards, in the repo shell:

```powershell
.venv\Scripts\alembic.exe check
```

Required: `No new upgrade operations detected.` — proof the temp table left no drift.

---

### C5 — The actual claim SQL (Step 5)

```powershell
.venv\Scripts\python.exe -m src.worker
```

Let it poll ~10 s with the queue empty, then `Ctrl+C`. Copy the `SELECT ... FOR UPDATE SKIP LOCKED`
block verbatim out of the echo output.

| Would also pass "I documented the claim query" | Caught by |
|---|---|
| Writing the SQL from memory, or from the plan | Diff your Part B 5.1 prediction against the echo. Any difference is a belief about your own code that was wrong |
| Leaving the worker running into Step 6 | Re-run C0's process check before seeding |

---

### C6 — Option (c) under real concurrency (Step 6)

Seed, in the repo shell:

```powershell
docker compose exec -T db psql -U postgres -d relay -c "INSERT INTO jobs (type) VALUES ('sleep'),('sleep'),('sleep') RETURNING id;"
```

Two interactive sessions, side by side:

```powershell
docker compose exec -it db psql -U postgres -d relay
```

**Variant 1 — naive, no guard on the outer UPDATE.**

```sql
-- SESSION 1
BEGIN;
UPDATE jobs SET status='running'
 WHERE id = (SELECT id FROM jobs WHERE status='pending' ORDER BY created_at, id LIMIT 1)
 RETURNING id, status;
-- STOP. Do not commit. Go to session 2.

-- SESSION 2  (run the identical statement, and watch whether it returns or hangs)
UPDATE jobs SET status='running'
 WHERE id = (SELECT id FROM jobs WHERE status='pending' ORDER BY created_at, id LIMIT 1)
 RETURNING id, status;

-- SESSION 1
COMMIT;
-- now look at session 2 immediately: which id came back, and what does psql report as the row count?
```

**Variant 2 — same, but the outer `UPDATE` carries the guard.** Reset first:

```sql
UPDATE jobs SET status='pending' WHERE id IN (<the three seeded ids>);
```

then repeat with `AND status='pending'` appended to the outer `WHERE`.

**Variant 3 — naive outer `UPDATE`, but the subquery locks:**

```sql
 WHERE id = (SELECT id FROM jobs WHERE status='pending' ORDER BY created_at, id LIMIT 1
             FOR UPDATE SKIP LOCKED)
```

Record for each variant: whether session 2 blocked, the `id` it returned, and its row count.

| Would also pass "option (c) works" | Caught by |
|---|---|
| Running the two statements **sequentially**, session 1 committed first | Session 1 must be left **uncommitted** while session 2 runs. That is the whole experiment |
| Reading only "it returned a row" as success | Compare the two returned `id`s. If both sessions return the **same** id, two workers just claimed one job |
| Reading `UPDATE 0` as an error | `0` is a *result*. Which variant produces it, and why, is the finding |
| Testing only variant 1 and concluding (c) is broken | Variant 2 changes one thing. If it fixes it, then (c) is not broken — the *naive form* is, and the entry must say which |

Cleanup — and say in the log which you chose:

```powershell
docker compose exec -T db psql -U postgres -d relay -c "UPDATE jobs SET status='pending' WHERE id IN (<ids>) RETURNING id, status;"
```

> **Do not** reset jobs 41, 63 or 65. They are Week 2's fixture. Reset only the ids you seeded today.

---

### C8 — Close the bench (2 min)

```powershell
Get-CimInstance -ClassName Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*src.worker*' } | Select-Object ProcessId
docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT count(*) FROM job_executions;" -c "SELECT count(*) AS conns, count(*) FILTER (WHERE state LIKE 'idle in transaction%') AS idle_in_txn FROM pg_stat_activity WHERE datname='relay';"
```

Required: **0** workers, **0** `idle in transaction` — Step 6 uses long-lived open transactions on
purpose, so this check matters more today than usual (`P-06` is four abandoned sessions blocking a
`DROP TABLE`). Arithmetic: `jobs_after = 74 + Case A + Case C + 3 seeded`. `running` must **still be
exactly 3** — if it is 4 or more, a Step 6 session was left uncommitted or unreset.

Then commit `DECISIONS.md`, the log, and `PROBLEMS.md` with a real message.

---

# PART D — Scope guard

**Not today. Each one has an owner.**

| Tempting | Owner | What you lose by doing it today |
|---|---|---|
| Writing the reaper | **Week 2, Din 1** | Step 2 turns the stuck job into a written problem statement. Build the fix first and the statement is never made |
| `lease_expires_at`, `claimed_at`, `locked_by` | Week 2 | Step 2's whole value is naming **which column is missing** and what adding it breaks. `P-16` lists the open sub-decisions |
| Changing the claim query in `src/` | Din 4 settled it; revisit Week 4 | Step 6 explores the alternatives in `psql`. Nothing in `src/` changes today |
| Fixing jobs 41 / 63 / 65 | Week 2 | They are the test fixture, and `P-16` needs all three because 41 is a different shape |
| A handler timeout, or slicing the poll sleep | Week 2 shutdown hardening | `P-15` shows these are **two** decisions. Bundling them now hides that |
| Writing `D-22` for the completion-row question | Week 2 | Din 5 Step 1's design judgement is a real decision, but it needs the reaper's requirements to price. Note it, do not decide it |
| Retry / `attempts` / DLQ | Week 2 | `attempts = 0` on three stuck rows is a finding, not a bug |
| An index on `job_executions.job_id`, or the FK | Week 4 / retention | `D-21` priced both and deferred them deliberately |
| Structured logging, metrics | Week 4 | `echo=True` and two prints carried Week 1 fine |

**Two ADRs written, two `psql` experiments run, zero lines changed in `src/`.**
