# DIN 5 BRIEF — `dead_letter` + graceful shutdown

**Week 2 · Din 5** · Plan: [`../../planning/WEEK_02.md`](../../planning/WEEK_02.md) (DIN 5 section) ·
Log: [`../../logs/WEEK_02.md`](../../logs/WEEK_02.md) · Sealed: [`DIN_05_KEY.md`](DIN_05_KEY.md)

**Budget:** plan says **140 min**. This BRIEF adds **Step 0** (two probe rows Din 4 left in the queue) and
**Step 1** (one arithmetic line Din 4 owes). Honest number: **~155 min**.

> **Paste rule.** Parts A, C and D go to Gemini. **Part B never travels. The KEY never travels.**
> Part B lives in `WEEK_02.md`'s `PART B` block, `## Din 5` subsection — **seven** questions today.
>
> **Seal rule.** A step's KEY section opens **after that step's measurement has run** — not after you have
> written your answer.

---

## The one thing to fix before anything else

**Din 4 scored `0/6` on Part B, and nothing was submitted at all.** Din 1 `0/6`, Din 2 `0/6`, Din 3 **`5/6`**,
Din 4 `0/6`. The variable is not effort — Din 4's code was clean and four named traps were avoided. The
variable is whether the answers get **written before the step runs**.

And it cost something specific yesterday. Three of the six questions were pointing straight at the three
claims that came out wrong:

| Q | It asked | What happened |
|---|---|---|
| Q5 | *first backoff smaller than the poll interval → the measured delay is a number of what?* | `base = 3.0 > 2.0` was chosen, so the question was treated as settled. Equal jitter made the floor `1.50 s`. **The answer was still "the poll interval's"** and it went unwritten |
| Q4 | *why can't jitter be evidenced by one job?* | Four jobs, failing together — the setup was **right**. The reading was wrong |
| Q2 | *reaper's `running → pending` vs retry's — where does the difference show?* | Reported as "the guard distinguished them". Under increment-on-claim **both** transitions move `attempts`, so the distinction is gone |

**Today's fix is mechanical, not motivational:**

```
docs/daily/week_02/DIN_05_ANSWERS.md
```

Create it **now**, before Step 0. Seven headings, one per Part B question. Write `idk` where you do not
know — that is a valid recorded answer and it scores as not-answered, which is accurate. At day close,
hand over the **path**, so the file's mtime settles *prediction* versus *reconstruction* (`E8`).

---

## Prereq — five things, and two are new debt from yesterday

| Kya | Kya dikhna chahiye | Status |
|---|---|---|
| Din 4's **measured attempt sequence** | Job 98: `executed_at` gaps `4.071787 s`, `6.098167 s`, terminal at `attempts = 3` | ✅ `[MEASURED-R]` |
| `max_attempts` with a written reason | `MAX_ATTEMPTS = 3` — chosen, reason written, and **not yet defensible** (`handle_boom` is the only failure it has seen) | ✅ recorded |
| The `CHECK` constraint's **actual name** | `\d jobs` — read it, never guess it | ⬜ **Step 2 today** |
| **An empty queue** | ❌ **Jobs 104 and 105 are `pending`, both `boom`** — reviewer probes from Din 4's close | ⬜ **Step 0 today** |
| Din 4's `base`-versus-quantum arithmetic | ❌ `base = 3.0` does not clear the `2.0 s` quantum once equal jitter halves it. **`base > 4.0` is required.** Not fixed, not decided | ⬜ **Step 1 today** |

**And one prereq that is negative:** Din 4's retry policy does **not** move today. Not the increment point,
not the backoff formula, not the jitter shape, not `MAX_ATTEMPTS`. Step 1 **decides and writes**; whether it
*changes* `BASE_BACKOFF_SECONDS` is itself the decision, and if it does, today's `dead_letter` arrival stops
being comparable to yesterday's sequence — which is a cost, not a blocker. Write the pick either way.

---

# PART A — STEPS

---

## Step 0 — Opening check, and there are two landmines in the queue this time (10 min) · executable

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId, ParentProcessId, CommandLine
```

**Din 4 was the first genuinely clean process close in four days** — `0` rows `[MEASURED-R]`. Din 1 left two
PIDs, Din 2 a reaper `~33 min`, Din 3 two workers `~4h 55m`. Keep it.

**But add a third check today, because `processes = 0` and `idle in transaction = 0` both passed yesterday
while a two-day-old connection sat there:**

```sql
select pid, application_name, state, backend_start, xact_start, left(query,60) as q
  from pg_stat_activity where datname = 'relay' order by backend_start;
```

At Din 4's close this returned a `psql` backend connected since **`2026-08-25 09:55:12.346835+00`** — `~2
days`, state `idle`, no locks, no snapshot `[MEASURED-R]`. Harmless, and **that is exactly why it matters**:
both existing cleanup checks were satisfied. Today it is not harmless — Step 3 runs `ACCESS EXCLUSIVE` DDL,
and a leftover session that ever opens a transaction will queue behind it and take every read and write with
it (`P-06`).

```sql
select status, count(*) from jobs group by status order by status;
select count(*) as total, max(id) as maxid from jobs;
select last_value from jobs_id_seq;
select count(*) from job_executions;
select attempts, count(*) from jobs group by attempts order by attempts;
select id, type, status, attempts, claimed_at, next_attempt_at from jobs where status = 'pending' order by created_at, id;
select id, status from jobs where id = 75;
select conname, convalidated, pg_get_constraintdef(oid) from pg_constraint where conrelid = 'jobs'::regclass;
```

**Expected against Din 4's close (post-review-probe):** `87 succeeded / 15 failed / 2 pending / 0 running`,
total `104`, `max(id) 105`, seq `105`, `job_executions 88`, `attempts` → `0|95 · 1|2 · 2|1 · 3|6`, 75
`failed`. Anything else is `E2` and Step 1 waits.

### The thing this step exists for

**Two `boom` rows are sitting in the queue and they will be claimed before anything you enqueue today.**

| id | State | Why it is there | What it costs |
|---|---|---|---|
| `104` | `pending`, `boom`, `attempts = 1`, `next_attempt_at NULL` | Din 4's Step-7 differential (`P-25`) | **two** more dispatches, then terminal. `job_executions +2` |
| `105` | `pending`, `boom`, `attempts = 2`, `next_attempt_at` **in the past** | Din 4's reclaim/backoff probe (`P-25`) | **one** more dispatch, then terminal. `job_executions +1` |

Both are older than anything you create, and the claim order is `(created_at, id)`. They **cannot be
deleted** (`P-05`, delta arithmetic). Two consequences, and both are useful rather than annoying:

1. **Name them in the opening baseline** with their expected `+2` and `+1`, or they land inside today's
   `dead_letter` delta.
2. **Job `105` is the cheapest `dead_letter` fixture you will get.** It is one dispatch from crossing the
   bound. Once Step 4's terminal transition exists, starting a worker turns `105` terminal on its **first**
   dispatch — no seeding, no waiting through a backoff chain. Use it deliberately and say you did.

**And re-read the `attempts` distribution line.** Jobs `44, 63, 65, 95` must still be `0` — they each ran
twice and nothing retroactively counts a past dispatch `[MEASURED-R]`.

> **Terms used in this step**
> - **`convalidated`** — a `pg_constraint` boolean: `true` if the constraint has been checked against every
>   existing row, `false` if it was added `NOT VALID` and only applies to new writes.
> - **`backend_start` vs `xact_start`** — when the *connection* opened, versus when its current
>   *transaction* opened. `NULL` `xact_start` means connected but not in a transaction.

---

## Step 1 — The one line Din 4 owes: `base` versus the jitter floor (10 min)

**No code required, and it may end in "no change" — but it must end in writing.**

Din 4 chose `BASE_BACKOFF_SECONDS = 3.0` with the written reason *"clears the 2.0 s poll quantum"*. Then it
layered equal jitter on top:

```
delay(n)  = min(3.0 * 2.0 ** (n-1), 15.0)
actual(n) = delay(n)/2 + random.uniform(0, delay(n)/2)
```

so attempt 1's actual delay is in `[1.50, 3.00]` and its **floor is below the quantum** `[MEASURED-R]`.
Roughly `33 %` of the range is invisible in `executed_at`. `P-24`.

**Write three things:**

1. **Which quantity the quantum check belongs against.** `base`, or `base/2`, or something else — say why in
   one sentence.
2. **The pick:** raise `BASE_BACKOFF_SECONDS` above `4.0`, or leave it and accept a partially-masked first
   attempt. Both are defensible. Leaving it is *cheaper today* because it keeps today's arrival comparable
   to Din 4's sequence; raising it costs that comparability and buys a measurable first delay.
3. **`BACKOFF_CAP_SECONDS = 15.0` is currently unreachable** — it first binds at attempt `4` (`raw = 24.0`)
   and `MAX_ATTEMPTS = 3` means attempt 4 does not exist `[MEASURED-R]`, `P-26`. Write which of these it is:
   *reserved for a future `MAX_ATTEMPTS`, crossing point `n = 4`* — or *should be lowered until it binds*.
   Do **not** silently leave it as a tuned-looking number.

**This is `D-23`'s input and it is the only step today that touches yesterday's numbers.** If you change
`BASE_BACKOFF_SECONDS`, say so in the log and say what it makes non-comparable.

> **Terms used in this step**
> - **Observation quantum** — the interval between successive chances to observe. Here
>   `POLL_INTERVAL_SECONDS`, measured in practice at `2.013–2.056 s` because the period is
>   `poll + pass duration`.
> - **Inert parameter** — one whose value cannot change behaviour because no reachable input consults it.

---

## Step 2 — Read the constraint, then decide one migration or two (15 min) · executable

**Read the name. Do not type it from memory.**

```sql
select conname, convalidated, pg_get_constraintdef(oid) from pg_constraint where conrelid = 'jobs'::regclass;
```

Copy both the name and the definition **verbatim** into the log now — the "before" side of today's swap only
exists until you run the migration, and a wrong name in a `DROP CONSTRAINT` makes a half-applied migration,
which is a new problem rather than a failed step.

The shape is a swap, because Postgres has no "add a value to a `CHECK`":

```sql
ALTER TABLE jobs DROP CONSTRAINT <name>;
ALTER TABLE jobs ADD CONSTRAINT <name>
  CHECK (status IN ('pending','running','succeeded','failed','dead_letter')) NOT VALID;
ALTER TABLE jobs VALIDATE CONSTRAINT <name>;
```

### The decision — one migration or two

| Option | What happens | The cost you must write |
|---|---|---|
| **A — all three in one migration** | One `upgrade()`, one transaction | Alembic wraps `upgrade()` in a transaction, so `ADD CONSTRAINT`'s lock is held **until commit** and `VALIDATE`'s scan runs under it. `NOT VALID` is written and its benefit is **not obtained**. On `104` rows the difference is unmeasurable — which is the dangerous part: the pattern will look like it works until the table is large |
| **B — two migrations** | First: `DROP` + `ADD ... NOT VALID`. Second: `VALIDATE CONSTRAINT` | Two files, two `upgrade` steps, and an intermediate state where the constraint exists but is unvalidated. That state has a meaning you must write: a `NOT VALID` `CHECK` **is** enforced on new writes and simply has not been proven against old rows |

**And one fact that is true in both:** between `DROP` and `ADD` there is a moment with **no** `CHECK` on
`status` at all. Inside one transaction other sessions never see it — but the lock is held across the whole
window either way.

**Write the pick and the cost of the other one.** `D-06`'s Cost 4 already predicted this pattern; today
tests whether the prediction was complete.

> **Terms used in this step**
> - **`ACCESS EXCLUSIVE`** — Postgres's strongest table lock. Conflicts with every other lock mode,
>   including plain `SELECT`.
> - **`SHARE UPDATE EXCLUSIVE`** — what `VALIDATE CONSTRAINT` takes. Allows concurrent reads and writes.
> - **`NOT VALID`** — add the constraint without scanning existing rows. Enforced on new writes immediately.

---

## Step 3 — Run it, and try to measure the lock queue (25 min) · executable

**Three checks, and the third is the one that has failed before.**

**3a — the constraint changed.** After `alembic upgrade head`:

```sql
select conname, convalidated, pg_get_constraintdef(oid) from pg_constraint where conrelid = 'jobs'::regclass;
```

`dead_letter` in the definition **and** `convalidated = true`. Under Option B, check it after each migration
separately — `false` then `true` is the whole point of splitting them.

**3b — the constraint actually bites.** A definition is not enforcement:

```sql
update jobs set status = 'not_a_status' where id = 104;
```

This must **error**. If it returns `UPDATE 1`, the `DROP` ran and the `ADD` did not.

**3c — the `ACCESS EXCLUSIVE` queue, and this measurement has failed once already.** Week 1 Din 3 tried it
and the lock was granted instantly, because there was no conflicting session to queue behind. The procedure
is recorded in `LEARNING_LOG.md`'s open items. It needs **two** sessions and an **observer**:

```
session 1 (psql):    begin; select * from jobs limit 1;      -- leave it. Do NOT commit yet.
session 2:           alembic upgrade head                    -- with a lock_timeout set
session 3 (psql):    select pid, state, wait_event_type, wait_event, left(query,60)
                       from pg_stat_activity where datname='relay';
```

**Session 3 exists because the measurement is about a state *during* the migration, not a duration around
it.** This is Din 4's whole lesson arriving one day later: `104` rows validate in microseconds, so timing
`alembic` from outside gives "instant" whether the lock queued or not. The thing that distinguishes them is
`wait_event_type = 'Lock'` observed **while** it waits.

Set a `lock_timeout` so a mistake ends in an error rather than a hang.

**Output:** either session 3's row showing the wait, or — if the lock was granted instantly — a plain
sentence that **the attempt failed and here is the procedure**. Writing "measured" for a lock that never
queued is the specific error Week 1 Din 3 made.

**Then close session 1** (`COMMIT` or `ROLLBACK`) and put its PID in the log. It is a deliberately-created
`P-06` and its removal is a named cleanup item.

> **Terms used in this step**
> - **`lock_timeout`** — a session setting: give up waiting for a lock after N ms and error.
> - **`wait_event_type` / `wait_event`** — what a backend is currently blocked on. `Lock` / `relation`
>   means waiting on a table lock.

---

## Step 4 — The terminal transition, and who is allowed to write it (25 min) · executable

Today `jobs.status` gets a fifth value and a fifth-or-sixth writer. `worker.py`'s failure branch currently
writes `status = "failed"` when `current_attempts >= MAX_ATTEMPTS`. That becomes `dead_letter`.

### The decision — who writes terminal

| Option | What happens | The cost you must write |
|---|---|---|
| **A — the retry writer does it** | The same failure-branch `UPDATE` writes `dead_letter`, guarded `WHERE id = :id AND status = 'running'`, with `rowcount` read | The terminal decision is in the **worker's** hands, and a worker that dies mid-handler never runs the statement. That row stays `running`, the reaper reclaims it, and the next claim increments past the bound |
| **B — a separate sweep** | A statement that terminalises bound-crossed rows: `WHERE status = 'pending' AND attempts >= :max`, guarded, `rowcount` read | A **fifth** writer on `status`, and it enforces the bound *after the fact* — a row can be claimed between crossing and being swept, so the effective bound is `max + 1`. And whether it lives in the reaper or on its own is a second decision |

**Yesterday's measurement is the test case, so answer it with a number.** Under Option A, job `104` is at
`attempts = 1` and job `105` at `attempts = 2` right now `[MEASURED-R]`. **How many more `job_executions`
rows does each get before it is `dead_letter`?** Write both numbers before you start the worker, then check.

**Note the bound check is `<`, not `==`** — `if current_attempts < MAX_ATTEMPTS` `[MEASURED-R from source]`.
That is correct and it is why `P-25`'s double-increment risk does not skip the bound. Do not "tidy" it into
equality.

**And `P-25` is now live on this path.** When the reaper reaches a row first, the retry mark returns
`rowcount = 0` and `next_attempt_at` is never written, so the row is claimable **immediately**
`[MEASURED-R]`. Under Option A the same rejection applies to the `dead_letter` write. **Which means the
terminal transition can be rejected too, and then the row goes back into the queue with `attempts` already
at the bound.** What does the next claim do with it? Answer before Step 5.

**End state:** enqueue nothing new. Start one worker. Job `105` should cross the bound on its first
dispatch. Read:

```sql
select id, status, attempts from jobs where id in (104, 105) order by id;
select job_id, count(*) from job_executions where job_id in (104,105) group by job_id order by job_id;
```

> **Terms used in this step**
> - **Terminal status** — a status no writer moves out of. Today: `succeeded`, `failed`, `dead_letter`.
> - **Sweep** — a periodic statement that acts on every row matching a predicate, rather than on one row a
>   worker is holding.

---

## Step 5 — Does anything move a `dead_letter` row? Check, do not assume (15 min) · executable

**The reaper's predicate is `status = 'running'` and the claim's is `status = 'pending'`, so `dead_letter` is
outside both by inspection.** That is a reading, not a check, and this project has a row that exists
specifically because a reading was trusted: job **75**.

Run the reaper **and** a worker with a `dead_letter` row present, then:

```sql
select id, status, attempts from jobs where id = 105;
select count(*) from job_executions where job_id = 105;
```

Read it twice with a gap, with both processes **alive**. Status unchanged and count unchanged.

**If it moves:** record it, put it back, **and record the revert**. A terminal row that resurrects is job
75's shape on a new value.

**Then the second half, which is Din 4's Q6 finally getting an answer.** Yesterday a bounded-out job and a
genuinely stuck job could only be told apart by reading `status` **and** `attempts` together, and
`max_attempts` lives in Python rather than in the database, so an observer with only `psql` could not decide
(`P-16`). Today `dead_letter` is a self-describing value.

```sql
select status, count(*) from jobs group by status order by status;
select id, status, attempts from jobs where status in ('running','pending','dead_letter') order by id;
```

**Output:** one sentence on what `dead_letter` now tells an observer that `failed` + `attempts` did not —
and one sentence on what it still does not tell them. Job `98` is `failed` with `attempts = 3` from
yesterday and job `75` is `failed` with `attempts = 0` from Week 1 `[MEASURED-R]`; **neither gets
retroactively renamed**, so `failed` stays overloaded for historical rows. Say so.

---

## Step 6 — `downgrade` against a real `dead_letter` row (10 min) · executable

```powershell
alembic downgrade -1
```

with at least one `dead_letter` row in the table.

**This is not a risk, it is a certainty:** a four-value `CHECK` cannot be added while a row holds a fifth
value. So the expected result is a **failure**, and the failure is the finding.

**Output:** the error text **verbatim**, the offending row's id, and one sentence classifying the migration:
*reversible in shape, conditional on data*. Then `alembic upgrade head` and confirm the definition again.

**This is `D-07`'s argument in a new shape** — Din 1 argued that a column's backfill semantics are a data
question the schema cannot answer. Same thing here, on a constraint.

Under Option B (two migrations), `downgrade -1` only undoes the `VALIDATE`. Say which one you ran and what
it left behind.

> **Terms used in this step**
> - **Reversible vs conditionally reversible** — whether `downgrade` succeeds for *any* database state, or
>   only for states its constraints happen to permit.

---

## Step 7 — Mid-job shutdown, and the lease is the actual question (25 min) · executable

Graceful shutdown is **already built and already measured** — `request_shutdown` sets a flag, the loop
checks it at the top, idle shutdown is bounded by `POLL_INTERVAL_SECONDS` (`P-10`) and mid-job shutdown is
bounded by the handler, which Relay does not bound (`P-15`). **None of that is today's question.**

Today's question: **the exiting worker is holding a lease that can expire before its handler finishes.** If
it does, the reaper reclaims, another worker starts the same job, and the exiting worker then runs its mark
statement. That is Din 3's overlap, on the shutdown path.

**Setup — use the mechanism that already worked on this machine.** Week 1 Din 5 used `SIGBREAK` on Windows
and it is recorded in that week's log. A new signalling mechanism today is a second variable.

Handler: `slow` is `8.0 s` and the lease is `30 s`, so **`slow` cannot make the lease expire.** You need
handler `>` lease. **And `super_slow` exists in no commit** (`P-23`) — `git log --all -S"super_slow"` is
empty and `HEAD` has `sleep/boom/slow` only `[MEASURED-R]`. So this needs a decision, and it is the same
one-line decision Din 4 declined to write:

| Option | Cost |
|---|---|
| **Duration from `payload`** — `handle_sleep`/`handle_slow` read `payload.get("seconds", default)` | Makes the knob explicit and closes `P-23`. Touches the registry's handlers, so the `type`-to-duration mapping stops being fixed |
| **A new named handler** | A second registry entry doing what the first should have done. And it will drift out of a commit again unless staged by name |
| **Do not run this today** | Then the shutdown-plus-lease interaction stays `[INFERRED]` and `D-22`'s `Cost` line has a hole. Honest, and it must be written as a hole |

**Pick one and write it.** `P-23` has been carried for two days without a yes or a no.

### The decision — what happens to the lease on shutdown

| Option | What happens | The cost you must write |
|---|---|---|
| **A — do nothing; let the handler finish** | The lease is left to expire; the mark runs at the end with its guard | If the handler outlives the lease, the reaper reclaims **while the worker is shutting down**, a second worker starts, and the exiting worker marks work someone else is doing. Din 3's window on the shutdown path. Graceful shutdown **narrows** the stranded-work window and **does not close** the duplicate one |
| **B — release the lease on shutdown** | The worker writes `running → pending` (guarded) so the job is immediately claimable | The handler is **still running**. You are not even waiting for the reaper — you are inviting the duplicate at once. And it is another writer on `status`, so guard and `rowcount` are non-negotiable |

**Three things to observe, not decide:**

1. Did the handler finish? (its end line, `python -u`, with the signal's timestamp)
2. Was any **new** job claimed after the signal line?
3. **What happened to the lease** — read `claimed_at` and `now()` twice during the handler, after the signal.

**And the heartbeat is the fourth observation.** Din 3 built it at `10.0 s` and measured that it pushes
`claimed_at` forward while the handler yields `[MEASURED-R]`. Does it keep running during shutdown? If it
does, the lease never expires and the shutdown window is **narrowed** by the heartbeat. If it stops, Option
A's full cost appears. **Observe it. Do not change the interval** — Din 3's evidence was taken at `10.0 s`.

**Output:** three durations on one line — **handler · lease · grace period** — and the exiting worker's mark
line with its `rowcount`.

> **Terms used in this step**
> - **Grace period** — how long a supervisor waits after `SIGTERM` before `SIGKILL`. Week 0 Din 2 measured
>   exit `137` when it was shorter than the handler.
> - **Lease** — `claimed_at` plus `LEASE_DURATION_SECONDS = 30`, evaluated by the reaper against `now()`.

---

## Step 8 — Reading: Ch 8 *The leader and the lock* + *Fencing tokens* (15 min)

**Notice it, write it, do not build it.** Fencing tokens are outside this week — a new column plus changes to
**four** guards (claim, reaper, retry, shutdown).

**The reason this reading is not a formality:** the same limitation has now been measured three days running.
The guard asks whether `status` **is** `'running'`, never **whose** `'running'`. Din 3: worker A marked job
95 `succeeded`, `rowcount = 1`, while worker B was executing it `[MEASURED-R]`. Din 4: the reaper-first
ordering returns `0` correctly, and the worker-B-first ordering returns `1` and is still untested
(`P-25`, `P-21`).

**Output:** at least two one-line links appended to `docs/ddia_summaries/DDIA_CH8_LINKS.md`, each right-hand
side an **existing** named entry. `P-17`, `P-02`, `D-02`, `D-06` are natural fits, and `P-25` is now the
sharpest one.

**Carried debt:** lines **10–13** are reviewer-written (Din 3) and still need confirming in your own words.
Lines **14–16** were yours — first time in four days, and it is earned — but two of them carry the overclaim
that Din 4's corrections 1 and 3 name, so a reviewer note now sits under them. **Read that note**: a link
cited by `D-22`/`D-23` with a wrong parenthetical is worse than a missing link.

---

## Step 9 — Log, reconciliation, cleanup, commit (20 min)

Full shape: goal → goal met (yes/no/partial) → **anything else learned** (separate field) → 📊 Measured →
💡 Understood → 🧠 self-check with an honest score → corrections table → 🚧 Unresolved → ❓ Next thought.

Into the log specifically: the constraint's **old name and old definition verbatim**; one-or-two migrations
with the cost of the other; Step 3c's result **or** a plain statement that the attempt failed and the
procedure used; the terminal writer decision (A or B) with its cost; `downgrade`'s error **verbatim** with
the offending row id; the lease-on-shutdown decision with its cost; **three durations on one line**; the
`P-23` decision (yes or no, in writing); and Step 1's `base`/cap decisions.

**Reconciliation** — opening counts from **Din 4's log entry**, post-review-probe line:
`87 succeeded / 15 failed / 2 pending / 0 running / 104 total`, `job_executions 88`, `max(id) 105`, seq
`105`.

Today's delta sources stay separate:

| Source | Effect |
|---|---|
| Job **104** (Din 4 probe, `boom`, `attempts = 1`) | 2 more dispatches → terminal · `job_executions` **`+2`** |
| Job **105** (Din 4 probe, `boom`, `attempts = 2`) | 1 more dispatch → terminal · `job_executions` **`+1`** |
| Step 7's long-handler job | `+1` job · `job_executions` `+1`, possibly `+2` if it is reclaimed |
| Any `not_a_status` / `dead_letter` probe writes on `104` | no new rows; status moves only |

**The special line today: the arithmetic balances across FIVE status buckets, not four.** If closing
`dead_letter` is `0` while the log records a terminal transition, that is a finding — first suspect
`rowcount = 0` (guard rejected), second suspect a migration that never applied.

**`failed` stays overloaded for history.** Job `98` (`failed`, `attempts = 3`, bounded out yesterday) and job
`75` (`failed`, `attempts = 0`, Week 1) are **not** renamed. Say which `failed` rows are historical
bounded-outs, so Din 6 does not read the count as "jobs that failed once".

**`PROBLEMS.md`** — likely a new entry. Candidates: graceful shutdown holds a lease it does not extend; the
`NOT VALID` benefit vanishing inside one transaction; a `dead_letter` write being rejected by the guard and
returning the row to the queue at the bound. **Grep on the day you assign the number.** `P-26` was taken on
Din 4, so `P-27` is the likely one, and the grep still runs:

```powershell
Select-String -Path docs\PROBLEMS.md -Pattern '^## P-'
```

**`DECISIONS.md` gets nothing today.** `D-06`'s amendment and `D-22`/`D-23` are Din 6's. Next free is
`D-22`.

**Cleanup:**

- **Copy output out of the captures before deleting them.** Four consecutive days the capture was deleted
  first. Yesterday it cost a real measurement: the worker's `Scheduling retry in {actual_delay:.2f}s` lines
  were the only surviving record of the intended delays, and `next_attempt_at` is cleared by the mark, so
  **both** instruments were gone by close (`P-24`). Today copy three things: the handler start/end lines, the
  mark line with its `rowcount`, and the `Claimed job` grep count.
- **Kill every worker and the reaper**, then re-run the process check and put the output in the log.
- **Close Step 3c's deliberate `idle in transaction` session** and put its PID in the log. This one you
  created on purpose, so its removal is a named item (`P-06`).
- **Run the third check** — `select backend_start from pg_stat_activity where datname='relay'` — and account
  for anything older than today.
- Probe **rows are not deleted** — ids into the log by name and count in the delta.

**Commit:** staged paths **by name**, never `.`. Today that is one or two files under
`alembic/versions/`, `src/worker.py`, possibly `src/models.py` (the `CHECK` in `__table_args__` must match
the migration, or the next `--autogenerate` will try to revert it), `docs/logs/WEEK_02.md`,
`docs/PROBLEMS.md`, `docs/ddia_summaries/DDIA_CH8_LINKS.md`.

**Do not miss `models.py`.** The `CheckConstraint` there still lists four values. Alembic autogenerate diffs
against the model file as saved on disk — Din 1 produced a permanently-empty revision from exactly that gap
(`79cb2ee38481`) `[MEASURED-R]`.

---

# PART B — PREDICTION QUESTIONS

**Not in this file, on purpose.** `docs/planning/WEEK_02.md`, `PART B — PREDICTION QUESTIONS` block,
`## Din 5` subsection — **seven** questions.

Answer from your own head **before** the relevant step runs, **in
`docs/daily/week_02/DIN_05_ANSWERS.md`**, and hand over that path at day close. `idk` is a valid written
answer and scores as not-answered, which is accurate.

| Part B question | Answer it before |
|---|---|
| 1 (`NOT VALID` + `VALIDATE` in one transaction — how much benefit is left, which lock, how long?) | Step 2 |
| 2 (`downgrade` with a `dead_letter` row — reversible, or conditionally reversible?) | Step 2 |
| 3 (worker dies mid-handler on the bound-crossing attempt — where does `attempts` land, how long is the bound a bound?) | Step 4 |
| 4 (does the reaper's predicate touch `dead_letter` — did you **check** or read? how does job 75 apply?) | Step 4 |
| 5 (lease expires during shutdown — when does the exiting worker's mark return `0`, and when does it return `1` on work someone else is doing?) | Step 7 |
| 6 (handler · lease · grace period — what order, and which does Relay bound?) | Step 7 |
| 7 (what does a fencing token give beyond compare-and-set, and which column does not exist today?) | Step 8 |

---

# PART C — VERIFICATION

**Clock discipline:** `select`s run in the DB session (`Etc/UTC`); worker stdout is naive local (IST); the
measured offset is `local − db_utc = 5:29:59.994671` `[MEASURED-R]`. Today's shutdown arithmetic subtracts
two timestamps, so label every one with its clock. Captures use `python -u`.

Each row was written by asking: *what wrong implementation would also pass this?* — **and, new today after
`P-26`: is there any run in which this row produces a result at all?**

| Check | Command | Mechanism present | Mechanism absent |
|---|---|---|---|
| **Fifth value is in the constraint, and validated** | `select conname, convalidated, pg_get_constraintdef(oid) from pg_constraint where conrelid='jobs'::regclass;` | `dead_letter` in the definition **and** `convalidated = true` | Four values, or the constraint missing entirely (`DROP` ran, `ADD` did not). Under Option B, `convalidated = false` after migration 1 is **correct** — the two-migration split is the only thing that makes this column informative |
| **The `CHECK` actually bites** | `update jobs set status='not_a_status' where id=104;` | Errors — `violates check constraint` | `UPDATE 1`. A definition you can read is not enforcement you have tested. **This is the row that stops the constraint check from being decorative** |
| **`dead_letter` is writable** | `update jobs set status='dead_letter' where id=<probe> and status='failed';` then read it back | `UPDATE 1` and `status = 'dead_letter'` | An error means the value is not allowed; `UPDATE 0` means the guard rejected. **Two different causes, and only `rowcount` separates them** |
| **The lock genuinely queued** | Step 3c's session 3, **during** the migration | A row with `wait_event_type = 'Lock'`, or the migration failing on `lock_timeout` — `D-07`'s `[INFERRED]` hazard measured for the first time | Migration returns instantly. Then **the measurement did not happen**. On `104` rows timing `alembic` from outside returns "instant" either way, so an outside-only timing cannot pass or fail this row — that is `P-26`'s shape, and it is why session 3 exists |
| **`downgrade` fails for the right reason** | `alembic downgrade -1` with a `dead_letter` row present | Errors, and the error names the check constraint. Offending row id recorded | It **succeeds** — then either no row is `dead_letter` (so nothing was tested) or the downgrade does not re-add the four-value constraint. Both make the "reversible" claim unfounded |
| **Bound produces a terminal name** | `select id, status, attempts from jobs where id in (104,105);` twice, worker alive | `status = 'dead_letter'`, `attempts` at the bound, `job_executions` count **stopped** | `attempts` past the bound, or `status` back at `pending` — the terminal write never landed or its guard rejected. **`rowcount` says which, and a single status read cannot** |
| **Predicted dispatch counts matched** | `select job_id, count(*) from job_executions where job_id in (104,105) group by job_id;` against the numbers you wrote in Step 4 | `104` gained exactly **2**, `105` exactly **1** | Any other numbers. **This is the only row that tests the policy rather than the code** — write the two numbers before running the worker |
| **`dead_letter` is not re-claimed** | `select count(*) from job_executions where job_id=105;` twice, gap, worker **alive** | Count unchanged | Count climbing — the claim query is matching more than `status='pending'`. **The worker must be alive**; an unchanged count with a dead worker proves nothing |
| **The reaper does not touch `dead_letter`** | Reaper running, then `select id, status from jobs where id=105;` | Unchanged, and the reaper's per-pass line shows `candidates=0` — so an **idle** reaper is distinguishable from a **dead** one (Din 3 closed `P-20`; deleting the capture undoes it in practice) | `pending` or `running`. Job 75's shape on a new value: record, revert, **and record the revert** |
| **No new claim after the signal** | Worker stdout, lines **after** the signal line | No `Claimed job` after the signal, and a clean-shutdown line at the end | A `Claimed job` after the signal — the flag is not checked at the loop top, or one more iteration slipped in |
| **The handler actually finished** | Worker stdout: handler start/end lines with the signal's timestamp | The **end** line appears after the signal, then the mark line | No end line. Process died on the signal, or the capture was truncated. **Without `python -u` these are identical** (`P-18`) |
| **The lease behaved as the chosen option predicts** | During the handler, after the signal: `select id, status, claimed_at, now() from jobs where id=<job>;` twice | Matches your Step 7 pick — under A the lease ages toward expiry; under B the row is already `pending`. **And check whether `claimed_at` is moving**: if the heartbeat is alive it is being pushed forward and the lease will not expire at all | Behaviour does not match the pick — the decision is in the log and not in the code. **A single read cannot tell an ageing lease from a heartbeat-refreshed one; you need two reads** |
| **The exiting worker's mark** | Its mark line, next to the reaper's `python -u` capture, same row | `rowcount = 0` conflict line — the row was reclaimed and the guard rejected | `Marked job ... as 'succeeded'` while another worker's handler runs. That is the `status`-only guard's limit and the fencing-token argument. **Record it, do not fix it** |
| **75 untouched** | `select id, status from jobs where id=75;` | `failed` | Anything else — `E4`: record, revert, record the revert |
| **44/63/65/95 untouched** | `select attempts, count(*) from jobs where id in (44,63,65,95) group by attempts;` | One row: `attempts = 0`, `count = 4` | Non-zero. Nothing retroactively counts a past dispatch |
| **Probe rows 104/105 accounted separately** | `select id,status,attempts from jobs where id in (104,105);` | Both terminal, and their `job_executions` rows attributed to **Din 4's probes finishing**, not to today's work | Folded into today's `dead_letter` delta, or still `pending` at close with no explanation |
| **Five buckets balance** | `select status, count(*) from jobs group by status order by status;` vs Din 4's close | Five rows where there were four, `dead_letter` count matching the transitions in the log | `dead_letter = 0` with a transition recorded. First suspect `rowcount = 0`, second an unapplied migration |
| **Log completeness** | `Select-String -Path <capture> -Pattern 'Claimed job'` piped to `Measure-Object`, and the file's last line | Count matches expected claims; file ends on the clean-shutdown line | Count low or file cut mid-line. Then *"no new claim happened"* and *"the log stopped"* are the same output (`P-18`) |
| **No connection older than today** | `select pid, application_name, backend_start from pg_stat_activity where datname='relay' order by backend_start;` | Everything started today, and Step 3c's deliberate session is closed with its PID in the log | An older connection. Din 4 had a `psql` backend from `2026-08-25` while both existing cleanup checks passed. **`processes = 0` and `idle in transaction = 0` do not cover this** |

**Three checks deliberately absent.** Anything claiming `dead_letter` prevents duplicate side effects — it
does not, and Week 3 owns it. Anything blessing `MAX_ATTEMPTS` as correct — `handle_boom` is the only failure
it has met. And anything claiming graceful shutdown eliminates duplicates — it **narrows** the stranded-work
window and does not close the duplicate one.

---

# PART D — SCOPE GUARD

| Tempting | Owner | What you lose by doing it today |
|---|---|---|
| Build the fencing token — three days of evidence now point at it | **outside this week** | A new column and **four** guards to change (claim, reaper, retry, shutdown). Today writes the *argument* with Din 2, Din 3, Din 4 and today's evidence in one place; that argument is Week 3's input. Building it overwrites the evidence with a fix |
| Idempotency key — the duplicate now shows on the shutdown path too | **Week 3** | Same trap, third day. Living with the duplicate is what makes Week 3's property test a proof |
| Bound the handler with a timeout | **`D-22`, Din 6** | Handler timeout and lease duration are **one** decision (`P-15`). A timeout today makes today's mid-job shutdown a measurement of the timeout, and `D-22` loses its baseline |
| Add `failed_reason` / an error column alongside `dead_letter` | **outside this week** | Today is a transition, not a new field. How much error text, where, and when to truncate is its own decision |
| Retroactively rename yesterday's `failed` bounded-outs to `dead_letter` | **nothing owns it — do not** | Job `98`'s `failed` is a true record of what the code did yesterday. Rewriting it destroys the only evidence that the split between Din 4 and Din 5 was deliberate |
| Tune the retry policy now that `dead_letter` exists | **Din 4's decision** | Except Step 1, which is a **written** decision about `base` and the cap. Changing anything else makes today's arrival non-comparable to Din 4's measured sequence |
| Convert `status` to an `ENUM` — "the values are final now" | **`D-06` — locked** | `D-06`'s whole argument was that they are **not** final and `DROP VALUE` does not exist. Adding a fifth value and then locking the set makes that entry false |
| Write `D-06`'s amendment today | **Din 6** | Today builds its evidence. Entries are written one day, one place, so `MAP.md` and the log stay in one commit |
| Give the reaper the `dead_letter` sweep as well | **today's Option B decision, written separately** | The reaper's job is recovery. Adding bound-enforcement makes one loop write two transitions, and then Din 2's reclaim-latency number is a number of nothing in particular |
| Change the heartbeat interval so the shutdown lease behaves "properly" | **Din 3's number, frozen at `10.0 s`** | Din 3's narrowing evidence was taken at `10.0 s`. Change it and that evidence describes a setup that no longer exists. Today the heartbeat is **observed** |
| Change the claim query's two-part shape | **`D-02` — locked** | Nothing is added to the claim today. `dead_letter` is outside its `WHERE` already — that is **checked**, not ensured by editing |
| Delete probe rows 104/105 to get a clean queue | **`P-05` — do not** | Delta arithmetic is the only thing that has caught contamination in this project. `105` at `attempts = 2` is also today's cheapest `dead_letter` fixture |
| Turn off `echo=True` | **Week 4, with metrics** | Still a separate decision with its own day |
| Fix `super_slow` with a new named handler | **`P-23`, and Step 7 forces the decision** | A `payload`-driven duration makes the knob explicit; a new named handler is a second registry entry doing the first one's job. **Either way: decide in writing.** Two days carried without a yes or a no |

**Not being built today:** fencing tokens, idempotency, dedup, handler timeouts, error columns, metrics,
indexes, `ENUM` conversion, a `D-` entry. Today produces **the constraint's old definition verbatim, a
one-or-two-migration decision with its cost, a `NOT VALID` lock observation made from inside the migration
rather than around it, a terminal-writer decision with its cost, a `downgrade` that fails for a recorded
reason, a lease-on-shutdown decision with its cost, three durations on one line, and a written `P-23`
verdict** — and the lock observation is the part `D-06`'s amendment rests on.
