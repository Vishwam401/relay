# DIN 2 BRIEF — Reaper: recovery bahar se aati hai

**Week 2 · Din 2** · Plan: [`../../planning/WEEK_02.md`](../../planning/WEEK_02.md) (DIN 2 section) ·
Log: [`../../logs/WEEK_02.md`](../../logs/WEEK_02.md) · Sealed: [`DIN_02_KEY.md`](DIN_02_KEY.md)

**Budget:** plan says **150 min**. This BRIEF adds a **Step 0** worth ~10 min that the plan did not
schedule, because Din 1 left two worker processes running. Honest number today: **~160 min**.

> **Paste rule.** Part A and Part C go to Gemini. **Part B never travels. The KEY never travels.**
> Part B does not live in this file — it is in `WEEK_02.md`'s `PART B` block, `## Din 2` subsection,
> six questions.
>
> **Seal rule.** A step's KEY section opens **after that step's measurement has run** — not after you
> have written your answer. Din 1's Part B answers were never written down, so that day scored `0/6` for
> **absence of data**, not for wrong answers. That is the one failure mode this rule exists to prevent,
> and it has now happened once. Write today's six first, `idk` included and recorded as `idk`.

---

## Prereq — three things, and two of them are new debts from Din 1

| Kya | Kya dikhna chahiye | Status |
|---|---|---|
| `claimed_at` exists, migration ran both ways | `\d jobs` → 7 columns, `claimed_at timestamptz` nullable | ✅ Din 1, `[MEASURED]` |
| One measured claim → lease-written pair | Din 1 log M3: job 88, `claimed_at 09:46:55.549422+00`, `now() 09:47:05+00`, both `Etc/UTC` | ✅ Din 1 |
| **Din 1's written predicate** | ❌ **Does not exist.** Din 1 produced the *column*, not the predicate | ⬜ **Step 1 today** |

**That third row changes today's shape and you should know it before you start.** The plan assumed Din 1
would leave a written predicate behind, and Din 2 would run it *as-written*. It did not. So today the
predicate is written **and** run on the same day — which means the usual protection is gone: there is
nothing stopping you from quietly adjusting the predicate while writing it because you can already picture
the rows it has to match.

**The substitute protection, and it is the whole discipline of today:** Step 1's output is written to the
log **and not edited afterwards**. Step 4 runs it read-only. If Step 4's verdict surprises you, the
surprise goes in the log **before** the predicate changes, and the changed version goes in as a second
row. Two versions in the log is a good outcome. One version that was silently correct is not evidence of
anything.

---

# PART A — STEPS

---

## Step 0 — Kill Din 1's leftover workers, then the opening check (10 min) · executable

**Two worker processes from Din 1 Step 7 are still running.** At `2026-08-23 10:27 UTC` they were OS PIDs
`34280` and `32636`, both `python -m src.worker`, started `15:16:54 IST`, and one asyncpg backend
(`3119`) had a `state_change` 0.35 s old when sampled `[MEASURED-R]`. They contaminated nothing on Din 1
**by luck** — `pending` was `0`, and `running` rows are invisible to the claim query (`P-16`).

**Today that luck runs out.** Reclaiming 41/63/65 turns them `pending`, which makes them **immediately
claimable**. A live worker takes them, and today's reclaim-latency number stops being anyone's number.

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId, CommandLine
Stop-Process -Id 34280,32636 -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, StartTime
```

PIDs will differ if the machine restarted — read them, do not trust the numbers above. Then:

```sql
select pid, state, xact_start, backend_start, left(query, 50) as q
from pg_stat_activity where datname = 'relay' order by backend_start;

select status, count(*) from jobs group by status order by status;
select count(*) as total, max(id) as maxid from jobs;
select count(*) from job_executions;
select id, status, claimed_at from jobs where id in (41, 63, 65, 75, 88) order by id;
```

**Expected against Din 1's close:** `75 succeeded / 9 failed / 3 running / 0 pending`, total `87`,
`max(id) 88`, `job_executions 58`, 41/63/65 `running` with `claimed_at` **`NULL`**, 75 `failed`,
88 `succeeded` with `claimed_at` non-null.

Anything else is an `E2` divergence and Step 1 waits. **Also count the leftover `psql` sessions** — Din 1
closed with 8 of them, all `state = 'idle'` with `xact_start` `NULL`, so no locks held. If any shows
`idle in transaction`, that is `P-06` and it gets handled first.

> **Terms used in this step**
> - **`backend_start`** — when that connection was opened. Distinct from `xact_start` (when its current
>   transaction began) and `state_change` (when it last changed state).
> - **`Stop-Process`** — PowerShell's terminate. Roughly `SIGKILL`, not `SIGTERM`: the worker's shutdown
>   handler does **not** run.

---

## Step 1 — Write the predicate, and write the duration as a *choice* (15 min)

**Nothing executes in this step. That is deliberate.** Output is text in the log, and it is not edited
after Step 4 runs.

Write three things.

**1. The predicate, as actual SQL.** It goes inside the reaper's `WHERE`, next to a compare-and-set guard
on `status`. Din 1 chose Option B, so the `IS NULL` branch is part of it.

**2. The lease duration — a number, and the reason.** Din 1's column is `claimed_at`, an **event**, not a
deadline. That has a consequence the plan did not schedule: a deadline column keeps the duration in the
*writer*, an event column puts it in **every reader**. So the duration — which `WEEK_02.md` defers to
`D-22` on Din 6, because its `Cost` line needs Din 3's duplicate count — has to be picked **today**,
before the evidence exists.

Write the number. Write why. And write the sentence **"chosen on Din 2, ahead of measurement"** next to
it, because on Din 6 the question will be *"did you measure this or choose it"* and the honest answer has
to survive four days.

**3. The reaper's poll interval — a second number, and its own reason.** It is not the same knob as the
duration, and it is not `worker.py`'s `POLL_INTERVAL_SECONDS`. `P-10` already recorded that a poll
interval prices three things at once.

**Output:** predicate SQL, duration + reason + the "chosen" label, poll interval + reason. In the log,
before Step 4.

> **Terms used in this step**
> - **`interval`** — a Postgres duration type. `now() - interval '30 seconds'` is a `timestamptz`.
> - **Compare-and-set guard** — naming the value you expect to find in the `WHERE`, so the write only
>   lands if nobody moved it first.
> - **Poll interval** — how long the loop sleeps between passes. Sets the *upper bound* on how late a
>   reclaim can be, separately from how late expiry makes it.

---

## Step 2 — Pre-reclaim state, verbatim, before anything mutates (10 min) · executable

**This output cannot be recovered after Step 5.** 41/63/65 stop being a fixture the moment they move.

```sql
select id, status, claimed_at, created_at, attempts from jobs where id in (41, 63, 65, 75) order by id;
select job_id, worker_id, executed_at from job_executions where job_id in (41, 63, 65, 75) order by job_id;
select now();
```

**Output:** all three, verbatim, in the log. The second query is the one that matters most — it is the
only thing that will still show, six months from now, that **41 had no execution row and 63/65 did**, and
that difference is why reclaiming them is not one operation.

> **Terms used in this step**
> - **Fixture** — rows deliberately left in a known broken state so an experiment has something real to
>   run against.

---

## Step 3 — One decision, written before the run: worker on or off? (10 min)

After reclaim, 41/63/65 become `pending` and claimable. So: **is a worker running during the reclaim, or
not?**

| Choice | What you get | What you lose |
|---|---|---|
| **Worker off** | Reclaim measured alone. `job_executions` delta is `0`, reclaim latency is clean, reconciliation is one variable | You do not see what happens next, and 41's *"reclaim is free"* claim stays an argument rather than an observation |
| **Worker on** | You watch a reclaimed row get picked up. 63/65 will produce a **second** execution row each | Two variables in one run (`P-12`). Reclaim latency gets mixed with claim latency, and today's centrepiece is not the duplicate — that is Din 3, deliberately |

**Decide, write it in the log with the reason, and do not revisit it after seeing the output.** The plan
is explicit that this is decided in advance and not explained afterwards.

**One more thing to notice and write, not fix.** After reclaim, worker A's mark statement is
`UPDATE jobs SET status = ... WHERE id = :id AND status = 'running'`. If the row is `pending`, the guard
rejects it and `rowcount` is `0` — compare-and-set doing its job (`D-06`, `P-17`). But if a second worker
has already moved it back to `running`, **the same guard matches**, and worker A marks work that worker B
is currently doing. Once `running → pending → running` is reachable, `status` alone stops being a
sufficient guard. The structural answer is a fencing token and that is Din 5's reading. **Notice it
today, write it, do not build it.**

> **Terms used in this step**
> - **Fencing token** — a monotonically increasing number handed out with a lease, so a stale holder's
>   writes can be rejected on arrival. Named here only so the term is not new on Din 5.

---

## Step 4 — Run the predicate read-only, per-row verdict on four rows (15 min) · executable

**A `SELECT` first, not the `UPDATE`.** Same predicate, no mutation. This is what makes Step 1's text
falsifiable while the rows are still in their original state.

Run **three** queries, not one — the split is the point:

```sql
-- (a) the whole predicate, as written in Step 1
select id, status, claimed_at from jobs
 where status = 'running' and (<your predicate>) order by id;

-- (b) the expiry branch ONLY
select id, status, claimed_at from jobs
 where status = 'running' and claimed_at < now() - interval '<your duration>' order by id;

-- (c) the NULL branch ONLY
select id, status, claimed_at from jobs
 where status = 'running' and claimed_at is null order by id;
```

**Then write the verdict table by hand — four rows, one line each:**

| id | pre-state | matched by (a)? | matched by (b)? | matched by (c)? | should it have? |
|---|---|---|---|---|---|
| 41 | | | | | |
| 63 | | | | | |
| 65 | | | | | |
| 75 | | | | | |

**Output:** the three query outputs verbatim, plus that table filled in. **Whatever (b) returns is the
finding**, and read the number before you interpret it — `P-12`'s rule is that a count means nothing until
you have shown the condition it counts could have occurred at all.

> **Terms used in this step**
> - **Read-only probe** — running a predicate as a `SELECT` to see what it selects, before letting it
>   drive a write.

---

## Step 5 — The reaper, for real (15 min) · executable

A **separate loop in a separate process**. Not inside `worker.py`'s loop — a reaper that lives inside the
worker dies with the worker, and the entire argument of today is that recovery arrives from outside.
`POSTMORTEMS.md` entry #3 is the measured version: no participant could resolve that lock, and
`pg_terminate_backend` came from outside all of them.

The transition, one statement:

```sql
UPDATE jobs
   SET status = 'pending', claimed_at = NULL
 WHERE id = :id
   AND status = 'running'
   AND (<your Step 1 predicate>)
```

Three things are deliberate. **The guard on the old value** (`status = 'running'`). **The predicate in the
`WHERE`, not in a Python `if`** — `EvalPlanQual` rechecks the predicate you wrote, and only what you wrote
(`P-17`). **A `rowcount` check on every pass**; `rowcount = 0` is a result, not an error (`D-06`).

`attempts` is **not** touched today — Din 4, `D-23`.

Capture stdout with `python -u`. Per-row output, not a total: `id · pre-state · matched · post-state`.
*"3 reclaimed"* demonstrates nothing and `P-18` is the entry that says why.

**Output:** the reaper's per-row stdout, plus `select id, status, claimed_at from jobs where id in
(41,63,65,75) order by id;` afterwards.

> **Terms used in this step**
> - **`python -u`** — unbuffered stdout. Without it a killed or still-running process can leave a
>   truncated log, and a truncated log is indistinguishable from "nothing happened".

---

## Step 6 — Run it twice, back to back (10 min) · executable

Immediately run the reaper a second time with **nothing else changed**.

**Output:** the second run's `rowcount` per row. This is the only check today that tests whether your
guard is a real guard, and it is designed so a missing guard cannot pass it.

---

## Step 7 — Reclaim latency, in one clock (15 min) · executable

Two timestamps and their difference: when the claim became reclaimable under your predicate, and when the
row actually went `pending`.

```sql
select id, status, claimed_at from jobs where id = <a row that had a non-null claimed_at>;
select now();
```

Reaper stdout is **local (IST)**; the DB session is `Etc/UTC`. Convert before subtracting and **label
every timestamp with its clock** — a lease bug and a timezone bug are identical in a diff, and Din 1 only
half-measured this offset.

**Then answer, in writing:** reclaim latency is bounded by the lease duration, by the poll interval, or by
both? And — the plan's own question — **which part of that number did you measure and which part did you
choose?**

**Output:** two labelled timestamps, their difference, and the measured-versus-chosen split.

---

## Step 8 — Reading: Ch 8 *Timeouts and Unbounded Delays* (20 min)

The section immediately after *Detecting Faults* (roughly pp. 281–286 in the 1st edition — check your
copy; the section name is authoritative, the page numbers are not).

Read it **after** Step 1, not before. Step 1 makes you pick a timeout with no evidence; this section
explains why that is the normal condition and not a personal failing.

**Output:** one-line links appended to `docs/ddia_summaries/DDIA_CH8_LINKS.md`, each right-hand side an
**existing** named `D-`/`P-` entry. **One of them must land on `P-02`.** No new numbers.

**Carried debt, and it is specific:** Din 1's two links were never appended — that file's mtime is still
`2026-08-22 17:28`. Note also that lines 2 and 3 already cite `pp. 278–284` and `281–283`, written on
Stage Day, so today's lines have to go **past** them rather than restate them.

---

## Step 9 — Log, reconciliation, cleanup, commit (15 min)

Full shape: goal → goal met (yes/no/partial) → **anything else learned** (separate field) → 📊 Measured →
💡 Understood → 🧠 self-check with an honest score → corrections table → 🚧 Unresolved → ❓ Next thought.

Into the log specifically: the **pre-reclaim verbatim state**, the **per-row verdict for all four rows**,
**reclaim latency**, the **chosen duration and poll interval with their reasons**, and the Din 5
observation (`status` alone stops being a sufficient guard).

**Reconciliation** — opening counts from **Din 1's log entry**, not the plan's BENCH block:
`0 pending / 3 running / 75 succeeded / 9 failed / 87 total`, `job_executions 58`. Never `max(id)`, never
id contiguity. Total rows must **not** change from reclaim alone. Job 75 is still counted in `failed`.

**`PROBLEMS.md`** — a new entry on the reaper's predicate and what it keys on. **Grep for the next free
number on the day you assign it**; `P-19` was taken on Din 1, so `P-20` is the likely one, and the grep
still runs:

```
grep -n "^## P-" docs/PROBLEMS.md
```

**`DECISIONS.md` gets nothing today.** `D-22` is Din 6's. Today's numbers sit in the log with
`[MEASURED]` tags so Din 6 can pick them up.

**Cleanup:** delete the reaper's stdout capture after copying the relevant lines up into the log, and say
so. **Kill the reaper and any worker** — Din 1's lesson. Reclaimed rows are **not** deleted; they are
normal rows now and they count in the delta.

**Commit:** staged paths **by name**, never `.`. Din 1's commit never happened, so today's staging also
carries `src/models.py`, `src/worker.py`, and both migration files. Check `labs/day2_signals.py` — it is
modified and was not part of Din 1's scope; either its own commit or reverted.

---

# PART B — PREDICTION QUESTIONS

**Not in this file, on purpose.** `docs/planning/WEEK_02.md`, `PART B — PREDICTION QUESTIONS` block,
`## Din 2` subsection — six questions.

Answer from your own head **before** the relevant step runs. `idk` is a valid written answer and scores as
not-answered, which is accurate.

| Part B question | Answer it before |
|---|---|
| 1 (41's reclaim vs 63's — same operation? `status` or evidence?) | Step 2 |
| 2 (predicate joined on `job_executions` → what happens to 41, and how does the stranded row *look*?) | Step 4 |
| 3 (inverse rule — "no execution row → reset" — on 75, and how fast is it caught?) | Step 4 |
| 4 (long reaper transaction — which instant is `now()`, which clock computed expiry?) | Step 5 |
| 5 (first worker alive — when does its mark give `rowcount` 0, and when does it give 1 while another worker does the work?) | Step 3 |
| 6 (reclaim latency — bound by duration, poll interval, or both? measured or chosen?) | Step 7 |

---

# PART C — VERIFICATION

**Clock discipline:** `select`s run in the DB session (`Etc/UTC`); reaper stdout is **local (IST)**. Label
every timestamp. Capture with `python -u` — a truncated log and a genuine zero are the same output
(`P-18`).

Each row below was written by asking: *what wrong implementation would also pass this?*

| Check | Command | Mechanism present | Mechanism absent |
|---|---|---|---|
| **41 actually moved** | `select id, status, claimed_at from jobs where id = 41;` | `pending`, `claimed_at` `NULL` | Still `running` while the reaper's output says reclaim succeeded — `P-16`'s exact case, and the reason a total is not evidence |
| **Four rows are distinguished in one output** | Step 4's table + `select id, status from jobs where id in (41,63,65,75) order by id;` | Four rows, a per-row verdict on each, and 75 **not matched** | A single line: `3 reclaimed`. Decorative — it passes whether or not the predicate can tell the four apart (`P-18`) |
| **Which branch fired, per row** | Step 4's queries (b) and (c), run separately | (c) matches 41/63/65; **(b) matches nothing**, because all three have `claimed_at NULL` and there is nothing to subtract a duration from | Only query (a) was run. Then "the predicate matched three rows" is true and **says nothing about the expiry branch** — the branch the reaper actually exists for is untested and looks tested |
| **The expiry branch is honestly reported** | compare (b)'s result against your Step 1 claim | The log says **"the expiry branch matched 0 rows and was not exercised today"** | The log says "the predicate worked". `P-12`: before interpreting a count, show the condition it counts could have occurred. Today it could not — no `running` row has a non-null `claimed_at` |
| **75 untouched** | `select id, status from jobs where id = 75;` | `failed` | `pending` or `running` — a terminal row resurrected. `E4`: record it, put it back to `failed`, **and record the revert too** |
| **The guard is a real guard** | run the reaper twice back to back | Second run: `rowcount 0` on those rows — they are `pending`, the guard rejects | Second run reports the same rows reclaimed again — `AND status = 'running'` was not in the `WHERE` |
| **Reclaim latency is a real number** | `python -u` capture + the two timestamps from Step 7 | Two timestamps, each labelled with its clock, and their difference | Empty or truncated capture, which looks identical to "nothing was reclaimed" (`P-18`) |
| **Pre-reclaim state survived** | Step 2's output in the log | Four rows verbatim **plus** the `job_executions` query showing 41 has no row and 63/65 do | Nothing in the log — and that state **cannot be recreated** |
| **Nothing else moved** | `select status, count(*) from jobs group by status;` vs Din 1's close | `running` down by exactly the rows reclaimed, `pending` up by the same, **total unchanged**, `job_executions` delta consistent with Step 3's worker decision | Any other movement. First suspect a forgotten worker (`P-13`) — which happened yesterday, so check before assuming |

**Two checks deliberately absent.** Anything claiming duplicate execution is prevented — nothing today
prevents it. And anything claiming the lease duration is *correct* — it was chosen without evidence, and a
check that blessed it would be manufacturing confidence.

---

# PART D — SCOPE GUARD

| Tempting | Owner | What you lose by doing it today |
|---|---|---|
| Add a heartbeat | **Din 3** | A mitigation applied before watching the failure. `WEEK_01.md` blocks this in four places. Din 3 produces the duplicate **first**, then the heartbeat — otherwise *"narrows, does not close"* is a slogan with no measurement under it |
| Fix the predicate before running it | **today, but after** | The row-by-row verdict on the predicate **as written** is the week's data. Fix first and you never learn which direction you were wrong in |
| Seed a `running` row with a non-null `claimed_at` so the expiry branch has a target | **Din 3** | Two variables in one run, and Din 3's centrepiece needs a live-but-slow worker, not a killed one. Today, record that the branch was **unexercised** — that sentence is worth more than a manufactured pass |
| Two reapers, leader election | **Week 4** | `P-12`'s shape: you would not know which reaper produced which reclaim. Single-reaper tradeoffs are their own measured decision |
| Re-stick 41/63/65 and repeat the run | **never** | After reclaim they are not a fixture. Re-sticking them is manufactured evidence. Din 3 seeds its own rows |
| Touch `attempts`, start retry | **Din 4 (`D-23`)** | Reclaim and retry are two transitions. Both today and no inter-attempt number belongs to either |
| `dead_letter`, shutdown path | **Din 5** | New `status` writers get their own day, with the `ACCESS EXCLUSIVE` window measured |
| Build a fencing token | **Din 5** | Today's job is to *notice* that `status` alone stops being a sufficient guard. Building the answer before writing the problem is the same trap as the heartbeat |
| Write `D-22` with today's duration | **Din 6** | Its `Cost` line needs Din 3's duplicate count. Written today it would record a chosen number as a justified one |
| Change the claim's two-part shape | **`D-02` — locked** | Din 5 and Din 7's runs are against this shape. The lease was **added** to the claim; the claim was not replaced |

**Not being built today:** heartbeat, retry, backoff, jitter, `dead_letter`, fencing tokens, graceful
shutdown changes, metrics, indexes, a second reaper. Today produces **one loop in one new process, one
predicate that was written down before it ran, four per-row verdicts, and one latency number** — and the
per-row verdicts are the part the rest of the week rests on.
