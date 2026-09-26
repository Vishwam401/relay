# DIN 1 BRIEF — Problem statement, phir lease column

**Week 2 · Din 1** · Plan: [`../planning/WEEK_02.md`](../../planning/WEEK_02.md) (DIN 1 section) ·
Log: [`../logs/WEEK_02.md`](../../logs/WEEK_02.md) · Sealed: [`DIN_01_KEY.md`](DIN_01_KEY.md)

**Budget:** plan says **140 min**. This BRIEF adds a **Step 0** worth ~20 min that the plan did not
schedule, so the honest number today is **~160 min**. Reason is in Step 0 and it is not optional.

> **Paste rule.** Part A and Part C go to Gemini. **Part B never travels. The KEY never travels.**
> Today Part B does not even live in this file — it is in `WEEK_02.md`'s `PART B` block, `## Din 1`
> subsection. That block is not pasted with the day section.
>
> **Seal rule.** A step's KEY section opens **after that step's measurement has run** — not after you
> have written your answer. Answer first, from your own head, `idk` included and written down as `idk`.
> Then run. Then try your own explanation of any difference. Then open the KEY.

---

## Prereq — three things, and the third one is `psql`

| Kya kholo | Kya dikhna chahiye | Status |
|---|---|---|
| `docs/daily/WEEK_01_HANDOFF.md` | Three headings, none empty. *What Week 2 Must Not Assume* is today's direct input | ✅ verified on disk, Stage Day |
| `docs/POSTMORTEMS.md` | Three `## Incident` headings, and entry #3 contains the "resolution came from outside" line | ✅ verified on disk, Stage Day |
| `psql` — opening bench | Counts match the BENCH block; 41/63/65 `running`; 75 `failed` | ⬜ **today's first executable** |

**If the third does not match, Step 2 stops and `E2 — bench divergence` runs first.** New numbers become
the week's baseline, and that goes in the log. Do not edit the plan's BENCH block, and do not repair the
database to match it.

**Extra reason to take the bench check seriously today:** the plan's BENCH block claims it was measured
at Din 7's close (86 rows, `max(id) 87`), but **`docs/logs/WEEK_01.md` has no Din 7 entry** — it ends at
`# DIN 6` (78 rows, `max(id) 78`, seq `79`). So today's bench check is the first thing that can tell you
whether the BENCH block is real. Whatever `psql` says is the truth; the plan's block is a claim.

---

# PART A — STEPS

Every step ends in something on disk or something in `psql`. Each carries its own
**terms used in this step** so you do not have to go looking (and so you are never tempted to open the
KEY for vocabulary). Knowing what a thing **is** never reveals what will **happen**.

---

## Step 0 — Pay the Week 1 debt: the five written answers (20 min)

**This is not part of Din 1's design. It is here because it has slipped four times** — Din 5 Step 6 →
Din 6 Step 2 → Din 7 → now — and `CURRENT_WEEK.md` states the rule in your own words: *"Week 2 Din 1
should not start before it exists in his own words."* It is deliberately **not** written for you.

Write these five, in your own words, in the Din 1 log entry. Short is fine. `idk` is fine and is
recorded as `idk`.

1. The reaper's predicate **using only today's columns** — write the actual SQL — and why it fails.
2. The **smallest** schema addition that fixes it.
3. The **new failure** that addition creates.
4. **Job 41 versus job 63** — why reclaiming them is not the same operation.
5. **The short lease** — what goes wrong if the lease is much shorter than the handler.

**Output:** five short written answers in the log. **Do not read the plan's DIN 1 section before writing
them** — that section answers three of the five. Write yours, then read it, then note the gaps. That
ordering is the whole value; reversed, this step is transcription.

> **Terms used in this step**
> - **Predicate** — the boolean expression in a `WHERE` clause. "The reaper's predicate" = the condition
>   that decides which rows the reaper picks up.
> - **Lease** — a claim with an expiry time attached. The holder owns the row until a deadline.
> - **Reclaim** — moving a row out of `running` and back into a claimable state.

---

## Step 1 — Opening check + bench divergence (10 min) · executable

Run both. Output goes in the log **verbatim**, not from memory.

```powershell
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, StartTime
```

```sql
select pid, state, xact_start, left(query, 60) as q
from pg_stat_activity where datname = 'relay';
```

Workers must be **zero**, `idle in transaction` must be **zero**. A leftover worker keeps claiming jobs
and contaminates every count today (`P-13`); a leftover `idle in transaction` session sits on locks
(`P-06`).

Then the bench:

```sql
select status, count(*) from jobs group by status order by status;
select count(*) as total from jobs;
select max(id) from jobs;
select last_value from jobs_id_seq;
select count(*) from job_executions;
select id, status from jobs where id in (41, 63, 65, 75) order by id;
```

**Output:** the divergence table in the log filled in, and a named classification if anything differs.

> **Terms used in this step**
> - **`pg_stat_activity`** — a system view with one row per server connection: its state, what it is
>   waiting on, and its last query.
> - **`state = 'idle in transaction'`** — the connection has an open transaction and is currently
>   waiting for the client to send the next command.
> - **`xact_start`** — the wall-clock time the connection's current transaction began.
> - **`last_value` on a sequence** — the most recently handed-out value from that sequence.

---

## Step 2 — Problem statement, part 1: what today's columns measure (15 min)

Written output. The handoff file's third heading and your Step 0 answers are **given** — do not rewrite
them, write only the **gaps**.

`jobs` today: `id`, `type`, `payload`, `status`, `attempts`, `created_at`. `job_executions`: `job_id`,
`worker_id`, `executed_at`. The reaper asks one question — *"is this claim still alive?"* — and you need
to state, in writing, which column answers it. Then state what `created_at` actually measures, and what
`job_executions` presence actually means.

Then the line that matters most today: **does the naive predicate fail in the safe direction or the
dangerous one, and why?** One sentence, plus one sentence on what happens to it under load.

**Output:** this text in the log. It is the day's primary deliverable, ahead of the migration.

> **Terms used in this step**
> - **`created_at` / `D-08`** — the column's decided meaning is **enqueue** time.
> - **`now()`** — a Postgres function returning a `timestamptz`. Which instant it returns is a
>   prediction question; do not look it up in the KEY.
> - **`record_execution()`** — the worker function that inserts the `job_executions` row.
> - **Append-only instrument / `D-21`** — `job_executions` is written to be *read as evidence*, and is
>   explicitly not a control input for other logic.

---

## Step 3 — Problem statement, part 2: the smallest addition (10 min)

One column on `jobs`, holding the claim's **deadline**. Write three things about it:

1. **Type** — and why it has to sit in the same clock as `created_at`, which is already
   `DateTime(timezone=True)`.
2. **Nullability** — and what each choice *demands* from something else.
3. **Who writes it** — name the statement. Today's claim is:

```sql
UPDATE jobs SET status = 'running' WHERE id = :id AND status = 'pending'
```

The lease is **added to that `SET`**. The two-part claim shape (`FOR UPDATE SKIP LOCKED` + compare-and-set
`UPDATE`) does **not** change — `D-02` is locked, and changing it breaks comparability with Din 5 and
Din 7's runs.

**Output:** column name, type, nullability, and the writing statement, in the log.

> **Terms used in this step**
> - **`timestamptz`** — Postgres `timestamp with time zone`. Stores an absolute instant; renders in the
>   session's timezone.
> - **`DateTime(timezone=True)`** — the SQLAlchemy type that maps to `timestamptz`.
> - **Compare-and-set** — an update whose `WHERE` names the value you expect to find, so it only
>   succeeds if nobody changed it first.

---

## Step 4 — Problem statement, part 3: the two certainties (10 min)

Write the **new failure** the column introduces — as certainties, not risks. Two of them, and both are
already determined by mechanisms you have measured:

- One about **lease expiry versus a running worker** (`P-02` is the shape).
- One about **what the new column holds for rows 41, 63 and 65**, and what that does to a predicate that
  looks completely correct.

**Output:** both written as "this will happen", not "this could happen".

> **Terms used in this step**
> - **Three-valued logic** — SQL comparisons yield `true`, `false`, or `NULL`. A `WHERE` clause keeps
>   only rows where the result is `true`.
> - **Stranded row** — a row that should have been picked up and was not, with nothing reporting it.

---

## Step 5 — `Interim_Guarantee` + what Relay cannot say (10 min)

One paragraph, and it should feel uncomfortable. Name **which contract point improves** and **which one
pays for it**. Use `narrows` and `does not close`. `fixes` and `prevents` are not available today, even
if every run is clean.

Then one line on the thing Relay genuinely cannot answer — *how many workers are alive* (`P-13`) — and
therefore that the reaper's decision is **always a guess**, with the direction of the guess deciding
which contract point breaks.

**Output:** the `Interim_Guarantee` paragraph, verbatim, in the log.

> **Terms used in this step**
> - **Relay's contract #1** — an accepted job is never lost. **#2** — the side effect happens once.
> - **Interim guarantee** — what is true *today*, mid-build, as opposed to what the finished design promises.

---

## Step 6 — Migration, both directions (15 min) · executable

`ALTER TABLE jobs ADD COLUMN ...` plus a real `downgrade`. Then run the cycle:

```
alembic downgrade -1
docker compose exec db psql -U postgres -d relay -c "\d jobs"
alembic upgrade head
docker compose exec db psql -U postgres -d relay -c "\d jobs"
```

**Both `\d jobs` outputs go in the log.** The first must not show the column; the second must.

**Output:** migration applied, `downgrade`'s actual output recorded — not "it worked".

> **Terms used in this step**
> - **`alembic downgrade -1`** — run the current migration's `downgrade()` and step back one revision.
> - **`\d jobs`** — psql's table description: columns, types, nullability, indexes, constraints.

---

## Step 7 — The claim writes the lease (15 min) · executable

Add the lease to the claim's `SET`. Same guard, same `rowcount` check. `rowcount == 0` is still a
**result**, not an error (`D-06`).

Enqueue one slow job, start a worker, and **while it is running**:

```sql
select id, status, <lease>, now() from jobs where id = <new id>;
```

**Output:** `status`, the lease value, and `now()` — from the same query, so they share a clock.

> **Terms used in this step**
> - **`rowcount`** — the number of rows a statement affected. Available as `result.rowcount`.
> - **Handler** — the Python function the worker runs for a given job `type`.

---

## Step 8 — The `NULL` backfill decision (15 min) · executable

**This decision is yours and the plan deliberately does not pick it.** Read `D-07` first — its
backfill-semantics argument stops being hypothetical today.

| Option | What happens | Cost |
|---|---|---|
| **A — backfill in the migration** | Migration writes a value into existing rows | The migration now writes **data**, not just shape. The value is **fiction** — nobody knows when 41 was claimed. `downgrade` cannot restore it, so the migration is reversible in shape and not in information |
| **B — leave `NULL`, branch in the predicate** | Predicate becomes `(<lease> IS NULL OR <lease> < now())` | The `IS NULL` branch is now in the predicate **forever**, and it makes every `NULL`-lease row reclaimable — including any future writer that forgets to stamp the lease. Every later reader asks why the branch exists; the answer lives only in the log |

Common to both: the backfill touches **only the new column**, never `status` (fixture rule), and
**41/63/65's pre-migration state goes in the log verbatim first**.

```sql
select id, status, <lease> from jobs where id in (41, 63, 65) order by id;
```

**Output:** the decision, its cost in your own words, and this query's output.

> **Terms used in this step**
> - **Backfill** — writing values into rows that already existed before the column did.
> - **`D-07`** — the existing entry on what a backfilled value *means* versus a value that was recorded.

---

## Step 9 — Three-valued logic, with your own eyes (10 min) · executable

Two counts. Run both.

```sql
select count(*) from jobs where status='running' and <lease> < now();
select count(*) from jobs where status='running' and (<lease> is null or <lease> < now());
```

**Output:** both numbers in the log. Whatever the relationship between them is, it is the finding — and
Din 2's central trap compressed into one line.

---

## Step 10 — Reading: Ch 8 opening + *Detecting Faults* (15 min)

DDIA Ch 8: chapter opening, *Unreliable Networks*, *Network Faults in Practice*, *Detecting Faults*.
Not the whole chapter — the rest is split across the week and each piece arrives with the decision it
feeds.

**Output:** at least **two** one-line links appended to `docs/ddia_summaries/DDIA_CH8_LINKS.md`, same
shape as the existing five, each right-hand side an **existing** named `D-`/`P-` entry. No new numbers.

---

## Step 11 — Log, reconciliation, cleanup (15 min)

Log entry in full shape: goal → goal met (yes/no/partial) → **anything else learned** (separate field) →
📊 Measured → 💡 Understood → 🧠 self-check with an honest score → corrections table → 🚧 Unresolved →
❓ Next thought. The **full problem statement text** goes in this entry, and so does the backfill
decision with its cost.

Closing reconciliation: **opening counts + today's delta**. Never `max(id)`, never id contiguity.
Add the line **"the migration changed no row's `status`"** — if `running` differs from opening plus
today's claims, that is a finding, and the first suspect is a forgotten worker (`P-13`).

Also today: `CURRENT_WEEK.md` repoints to Week 2 and its status table updates. And a new `PROBLEMS.md`
entry — the lease introduces a **second clock**, plus the `NULL`-lease trap. **Grep for the next free
number on the day you assign it**, do not trust the plan's guess:

```
grep -n "^## P-" docs/PROBLEMS.md
```

**Cleanup:** delete the worker stdout capture file (`python -u`) after copying the relevant output up
into the log, and say in the log that you deleted it. **Probe rows are not deleted** — deleting rows
breaks delta arithmetic and destroys `P-05`'s evidence. Record their ids by name.

**Commit:** staged paths **by name**, never `.`. `docs/planning/`, `docs/roadmap/` and `docs/daily/` are
gitignored, so an empty `git status` does **not** mean nothing was written.

---

# PART B — PREDICTION QUESTIONS

**Not in this file, on purpose.** They are in `docs/planning/WEEK_02.md`, in the
`PART B — PREDICTION QUESTIONS` block, `## Din 1` subsection — six questions.

Rules, unchanged: answer from your own head **before** the relevant step runs. Write `idk` where it is
`idk` — it scores as not-answered, which is accurate, and it marks exactly what the experiment then
teaches. That block is never pasted to any model, and neither is the KEY.

Mapping, so you know which questions to answer before which step:

| Part B question | Answer it before |
|---|---|
| 1 (`created_at`, predicate direction) | Step 2 |
| 2 (`job_executions` row, which transaction) | Step 2 |
| 3 (`now()` in a long transaction) | Step 9 |
| 4 (`NOT NULL` vs `NULL` demands) | Step 8 |
| 5 (which contract point improves, which weakens) | Step 5 |
| 6 (does `rowcount` tell you anything new) | Step 7 |

---

# PART C — VERIFICATION

`<lease>` = the column name you chose. **Clock discipline:** all three `select`s run in the DB session,
which reports `Etc/UTC`; worker stdout is **local (IST)**. Convert before comparing, and write the clock
next to every timestamp. A lease bug and a timezone bug look **identical** in a timestamp diff.

Each check below is designed to fail against a wrong implementation. The question asked of every row was:
*what broken version would also pass this?*

| Check | Command | Mechanism present | Mechanism absent |
|---|---|---|---|
| Column shape | `docker compose exec db psql -U postgres -d relay -c "\d jobs"` | New column present as `timestamp with time zone`, with the nullability you chose | Only six columns — the migration never applied |
| Migration is reversible | `alembic downgrade -1` ; `\d jobs` ; `alembic upgrade head` ; `\d jobs` | Column **absent** in the first `\d`, **present** in the second | `downgrade` errors, or the column survives the first `\d` — `downgrade()` was never really written. **A second failure mode is specific to Option A:** re-adding a `NOT NULL` column to a table that already has rows fails unless `upgrade` supplies a value. If `upgrade head` errors here, that is not a bug in Alembic |
| Claim writes the lease | enqueue a `sleep` job, start a worker, and during the run: `select id, status, <lease>, now() from jobs where id = <new id>;` | `status='running'`, `<lease>` **non-null**, and `<lease> > now()` | `status='running'` with `<lease>` `NULL` — the column exists but was never added to the claim's `SET`. **This is the check that stops `rowcount = 1` from being mistaken for proof**: the guard is in the `WHERE`, so a claim that forgets the `SET` still reports `rowcount = 1` |
| Old `running` rows show the chosen value | `select id, status, <lease> from jobs where id in (41, 63, 65);` | Option A: a backfilled value on all three · Option B: `NULL` on all three **and** the decision written in the log | `NULL` on all three and nothing in the log — the database **cannot** distinguish "chose B" from "forgot". That distinction exists only in writing |
| Three-valued logic | the two `count(*)` queries from Step 9 | The two counts **differ** | The counts are **equal** — which means the lease column holds values (Option A ran), and the `IS NULL` argument does not apply today. **That is also a finding, and it gets written**, not discarded |
| Nothing else moved | `select status, count(*) from jobs group by status;` against opening counts | `running` = opening + today's claims, and no other bucket moved | Any other movement — first suspect is a forgotten worker (`P-13`), second is a probe you forgot you ran |

**One check that is deliberately *not* here:** anything that claims duplicate execution is prevented.
Nothing today prevents it, and a check that passes for that reason would be decorative — the exact
failure recorded in `P-08` and `P-18`.

---

# PART D — SCOPE GUARD

| Tempting | Owner | What you lose by doing it today |
|---|---|---|
| Write the reaper | **Din 2** | The predicate has to be written **first**, or it is a guess that never got recorded. Din 2 measures your predicate **as written** — that is the experiment |
| Heartbeat | **Din 3** | A mitigation applied before you have watched the failure. `WEEK_01.md` blocks that in four places for the same reason |
| Pick the lease **duration** | **`D-22`, Din 6** | Its `Cost` line cannot be written without Din 3's duplicate number. Choosing today means being unable to defend it later |
| Touch `attempts`, start retry | **Din 4 (`D-23`)** | Two variables in one run. The increment point is its own decision |
| Add `dead_letter` to the `status` `CHECK` | **Din 5 (`D-06`)** | `NOT VALID` + `VALIDATE CONSTRAINT` has its own day, which also measures its `ACCESS EXCLUSIVE` window |
| "Clean up" the two-part claim | **`D-02` — locked** | Din 5 and Din 7's runs are against this shape. Change it and comparability is gone |
| "Fix" 41/63/65 | **Din 2's experiment** | Those three are the week's fixture. Today only the new column touches them, never `status` |
| Idempotency key, dedup | **Week 3** | You have not seen the duplicate yet. Seeing the fix before living with the problem turns Week 3's property test into paperwork |

**Not being built today:** the reaper, the heartbeat, retry, backoff, jitter, `dead_letter`, graceful
shutdown changes, metrics, indexes. Today produces **one column, one migration, one claim change, and
roughly two pages of writing** — and the writing is the deliverable that the rest of the week rests on.
