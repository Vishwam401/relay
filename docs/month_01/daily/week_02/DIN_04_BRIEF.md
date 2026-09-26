# DIN 4 BRIEF — Bounded retry, backoff, jitter

**Week 2 · Din 4** · Plan: [`../../planning/WEEK_02.md`](../../planning/WEEK_02.md) (DIN 4 section) ·
Log: [`../../logs/WEEK_02.md`](../../logs/WEEK_02.md) · Sealed: [`DIN_04_KEY.md`](DIN_04_KEY.md)

**Budget:** plan says **160 min**. This BRIEF adds nothing new — Din 3 paid its own debts and left none for
today. Honest number: **~165 min**, and the extra five are Step 0's baseline, which is arithmetic today
rather than a decision.

> **Paste rule.** Parts A, C and D go to Gemini. **Part B never travels. The KEY never travels.**
> Part B lives in `WEEK_02.md`'s `PART B` block, `## Din 4` subsection — six questions.
>
> **Seal rule.** A step's KEY section opens **after that step's measurement has run** — not after you have
> written your answer.
>
> **Din 3 scored `5/6`, one partial, after `0/6` and `0/6`.** The variable that changed was that the answers
> got written down. One process fix carries: paste the **file** they live in, so the score arrives with an
> mtime and *prediction* versus *reconstruction* stops being unverifiable (`E8`). Yesterday's six were
> supplied at day close as prose, which is why the log carries a provenance caveat next to a good score.

---

## Today's shape, in one paragraph

Yesterday you watched a job run twice while both executions were legitimate. Today you make a job run
**many** times on purpose — so yesterday's hazard becomes a written policy. That means today is **not**
"how do I retry". Today is three numbers and two decisions: **how many times, how long apart, and where it
stops**, plus **where `attempts` increments** and **where "not yet" is stored**. The `attempts` column has
existed since Din 1 (`D-07`) and nothing has ever written to it. Today it gets a meaning, and the meaning is
a choice, not a default.

**And one trap is already loaded.** `POLL_INTERVAL_SECONDS = 2.0`. If your first backoff is smaller than
that, the gap you measure between `executed_at` values will be the **poll interval** wearing backoff's name.
Yesterday produced the general form of this failure as `P-22` — a number that was arithmetically perfect and
measured the wrong quantity. Today's version arrives through a different door.

---

## Prereq — five things, and four are clean

| Kya | Kya dikhna chahiye | Status |
|---|---|---|
| Din 3's duplicate count, written after the five diagnosis answers | Job 95, **2** `job_executions` rows, two distinct `worker_id` | ✅ `[MEASURED-R]` |
| Din 3's overlap evidence, one clock | Dispatch gap `30.243370 s` (DB), handler `45.026 s`, **overlap `14.783 s`** | ✅ `[MEASURED-R]` |
| Din 3's reclaim latency | **`1.798192 s`** — and **not** the `19.953818 s` that was first reported. That number measured when the reaper was started, not when the row expired (`P-22`) | ✅ corrected `[MEASURED-R]` |
| `attempts = 0` on every row | `select attempts, count(*) from jobs group by attempts order by attempts;` → one row, `0 | 96` | ✅ `[MEASURED-R]` |
| **An empty queue** | ❌ **Job 97 is `pending`** — reviewer probe from Din 3's close, `type='sleep'`, and it is the **oldest** `pending` row | ⬜ **Step 0 today** |

**And one prereq that is negative:** yesterday's numbers do **not** move today. Lease `30 s`, poll `2.0 s`,
heartbeat `10.0 s`, handler durations — all frozen. Touch any of them and Din 3's duplicate window stops
being comparable to today's retry delays, and `D-22` loses the pair it is built on.

---

# PART A — STEPS

---

## Step 0 — Opening check, and the baseline is arithmetic today (10 min) · executable

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId, ParentProcessId, ThreadCount, CommandLine
```

**This should be empty.** Din 3 left two real worker processes alive for `~4h 55m` and the reviewer stopped
them; Din 2 left a reaper; Din 1 left two PIDs. Three days, same shape, and all three times the closing
arithmetic balanced anyway — **because the leftover process had nothing to move.** Today it would have
something: job 97 is `pending`.

```sql
select status, count(*) from jobs group by status order by status;
select count(*) as total, max(id) as maxid from jobs;
select last_value from jobs_id_seq;
select count(*) from job_executions;
select attempts, count(*) from jobs group by attempts order by attempts;
select id, status, attempts from jobs where status = 'running' order by id;
select id, type, status, attempts, created_at from jobs where status = 'pending' order by created_at, id;
select id, status from jobs where id = 75;
select count(*) from pg_stat_activity where datname='relay' and state='idle in transaction';
```

**Expected against Din 3's close (post-probe):** `86 succeeded / 9 failed / 1 pending / 0 running`, total
`96`, `max(id) 97`, seq `97`, `job_executions 70`, `attempts` → `0 | 96` on one line, `running` empty, 75
`failed`. Anything else is `E2` and Step 1 waits.

### The thing this step exists for

**Job 97 will be claimed first, and it is not yours.** `type='sleep'`, `created_at 2026-08-26
15:41:53.408515+00`, and the claim query is `order_by(Job.created_at, Job.id)`. So the first worker you
start today runs `sleep(2)` on a reviewer probe row before it looks at a single `boom` job. That is `2 s`
and `+1` execution row.

**It cannot be deleted** (delta arithmetic, `P-05`), and there is nothing to decide — just **name it in the
log before you start**, so `job_executions`'s delta has `97 → +1, sleep, reviewer probe` sitting next to
`boom job → +N, retries`. Merge them and the first inter-attempt gap belongs to nobody.

**And the second thing:** the `attempts` distribution line is today's most load-bearing single output. It
must be `0 | 96` — one bucket. Jobs `44`, `63`, `65` and `95` have each executed **twice** and all four show
`attempts = 0` `[MEASURED-R]`. **The database currently has no record that anything ever ran twice**, and
that absence is the entire reason today's increment point is a real decision. If any row shows non-zero
`attempts`, someone wrote it before today — find that first.

> **Terms used in this step**
> - **`attempts`** — an `integer NOT NULL DEFAULT 0` column on `jobs`, added on Din 1 (`D-07`), never
>   written to by any code path.
> - **Baseline** — the counts today's deltas are added to. Comes from Din 3's log entry, never from
>   `max(id)`.

---

## Step 1 — Two decisions, written with their costs, before any code (20 min)

**No code in this step, and it is the most important step of the day.** Both decisions are yours; the plan
deliberately does not pick either. What goes in the log is the pick **and** the cost of the option you did
not take.

### Decision 1 — where does `attempts` increment?

| Option | What happens | The cost you must write |
|---|---|---|
| **A — on claim** | The claim `UPDATE` also writes `attempts = attempts + 1` | Counts **dispatches**, whether or not the handler was entered. Job 41's shape (claim committed, handler never entered) counts as an attempt. But an attempt is **never lost** to a crash |
| **B — on failure** | The retry `UPDATE` (`running →` claimable) writes `attempts + 1` | Counts **actual failures**, which reads cleanly. But a worker that dies mid-handler is not alive to write its own increment, so a crash-loop job's attempts are never counted |

**And there is a third path that is real this week, not hypothetical: the reaper's reclaim.** `src/reaper.py`
does **not** touch `attempts` — that was a deliberate Din 2 choice. So under Option A, the claim after a
reclaim counts; under Option B it does not.

**Yesterday's measurement is the test case, so answer it in writing with a number:** job 95 was dispatched
twice, by `worker-19804` and `worker-54112`, overlapping by `14.783 s`, and it **succeeded**. It never
failed once. **What is job 95's `attempts` under your policy?** Then the same question for job 44 (same
worker, two dispatches, Week 1) and job 63 (two dispatches, a week apart). Four rows, one policy, four
numbers — write them.

### Decision 2 — where does "not yet, a bit later" live?

Backoff means a failed job is not **immediately** claimable. The claim query is
`where(Job.status == "pending")`. A time condition has to go somewhere.

| Option | What happens | The cost you must write |
|---|---|---|
| **A — a new column** (`next_attempt_at` shape) | Retry writer writes the not-before; claim query adds `AND <col> <= now()` | Another column, another clock, and Din 1's `NULL` trap returns: `NULL <= now()` is `NULL`, so 96 existing rows need a branch or a backfill. `D-07`'s backfill-semantics argument applies unchanged |
| **B — reuse `claimed_at`** | The lease column doubles as the not-before gate | One column, **two meanings**: a running claim's deadline, and a retry's not-before. And the reaper's predicate is built on that column — so it would read a retry-waiting row as an *expired lease* and reclaim it. Cheap, and it makes the predicate ambiguous |

**Re-read Din 1's `NULL` differential before choosing** — `claimed_at < now()` returned `0` and
`(claimed_at IS NULL OR claimed_at < now())` returned `3`, same table, same instant `[MEASURED-R]`. That is
Option A's cost with a face on it.

**Write both picks, both costs, and one sentence you will have to defend on Din 6:** which of today's
numbers is `[MEASURED]` and which is `[NO EVIDENCE]`.

> **Terms used in this step**
> - **Compare-and-set (CAS)** — an `UPDATE` guarded on the value it expects to find, so a concurrent writer
>   that changed it first causes `rowcount = 0` instead of a silent overwrite.
> - **Not-before** — a timestamp meaning "do not consider this row until after this instant".
> - **`attempts` increment point** — the transition whose `UPDATE` carries `attempts = attempts + 1`.

---

## Step 2 — Backoff and jitter formulas, written literally, before code (15 min)

**Write them as expressions with numbers in them, not as prose.** Din 6's `D-23` is meant to be a verbatim
copy of what you write here, so if it is vague here it is vague there.

**Backoff needs three parts and a cap.**

```
delay(n) = min( base * multiplier ** (n - 1), cap )
```

Pick `base`, `multiplier`, `cap`, and `max_attempts`. **The cap is not optional:** without it the third or
fourth attempt lands so far out that the job has practically stopped without crossing the bound — and that
is a *silent stop*, not a bounded retry. Those two states look identical in `psql` and only one of them is
a design.

**And check `base` against `POLL_INTERVAL_SECONDS = 2.0` before you commit to it.** This is today's loaded
trap and it deserves the arithmetic in advance: a worker notices a newly-claimable row up to one poll late,
so any delay below `~2 s` is invisible in the data — the observed gap becomes the poll interval.

**Jitter sits on top of backoff, not instead of it.** Write it separately:

```
actual_delay(n) = delay(n) * <something random>     -- or delay(n) + <something random>
```

There are several standard shapes (full jitter, equal jitter, decorrelated). Pick one, write which, and
write **why that one** — the shapes differ in how much they preserve the backoff's growth versus how much
spread they buy.

**Jitter's evidence cannot come from one job.** One job's delays show only backoff. Spread needs **several
jobs failing at nearly the same instant**, then their next-attempt times compared. So the seed set has two
parts: **one** job that builds a long retry chain, and **several** enqueued together.

**The Relay-specific reason jitter matters is already measured** and it is not from a blog: `P-14` — equal
handler durations synchronised workers into a convoy, `4 µs` apart across three consecutive rounds. Today's
question is whether deterministic backoff rebuilds that convoy inside the retry path.

> **Terms used in this step**
> - **Exponential backoff** — each retry waits a multiple of the previous wait.
> - **Cap** — an upper bound on a single delay, so growth stops rather than continuing forever.
> - **Jitter** — randomisation applied to a computed delay so that jobs which failed together do not retry
>   together.
> - **Thundering herd** — many clients retrying at the same instant, recreating the load that caused the
>   failure.

---

## Step 3 — Build the retry write, and prove it is a third guarded writer (20 min) · executable

`jobs.status` now has three writers: the claim (`pending → running`), the reaper (`running → pending`), and
from today the retry path (`running →` claimable). **Same discipline on all three** — guard on the old
value, read `rowcount` (`D-06`, `P-17`).

`worker.py`'s mark statement is already `where(Job.id == job_id, Job.status == "running")`, so the shape
exists. Today it gains `attempts` (if Option A put it here) and the not-before value, and the failure branch
has to decide between *retry* and *terminal* by comparing `attempts` against `max_attempts`.

**Bound-crossing today does NOT produce `dead_letter`.** The `CHECK` allows `pending`, `running`,
`succeeded`, `failed` only. `dead_letter` arrives on **Din 5** via `NOT VALID` then `VALIDATE CONSTRAINT`
(`D-06`). Today's job is to show that **retry stops**; naming the stop is tomorrow's. **Write that split in
the log**, or Din 5 will look like it is finishing something that was left broken.

**The always-failing handler already exists.** `handle_boom` raises `RuntimeError` unconditionally — no new
handler needed, and it makes today's failure **deterministic**, so every bit of variation in the observed
delays is yours.

**End state for this step:** enqueue **one** `boom` job, run **one** worker for long enough to see two
failures, and read:

```sql
select id, status, attempts from jobs where id = <boom job>;
select job_id, worker_id, executed_at from job_executions where job_id = <boom job> order by executed_at;
```

Two execution rows, `attempts` moved, and the worker's stdout showing the failure line **and** the retry
write's `rowcount`. If `attempts` is still `0` while stdout shows two failures, the increment did not land
or its guard rejected — and `rowcount` says which.

> **Terms used in this step**
> - **Terminal status** — a status no writer moves out of. Today: `succeeded`, `failed`.
> - **`max_attempts`** — the number at which retry stops. A chosen number with a written reason, not a
>   config value.

---

## Step 4 — Measure the inter-attempt gaps, in the database's clock (20 min) · executable

Let the `boom` job run its whole chain with one worker. Then:

```sql
select job_id, worker_id, executed_at,
       executed_at - lag(executed_at) over (partition by job_id order by executed_at) as gap
  from job_executions where job_id = <boom job> order by executed_at;
```

**`executed_at` is the right instrument here for one specific reason:** it is written by the database, in
the database's clock, so this whole list needs **zero** clock conversions. Din 3's whole overlap proof came
down to that property (`14.783 s` derived in one clock versus `14.785 s` derived across two, differing by
`2 ms`).

**But `executed_at` is a dispatch instant, not a failure instant** (`P-11`, `D-21`) — `record_execution()`
commits before the handler runs. So `gap` is *dispatch-to-dispatch*, which includes the handler's own
runtime and the claim delay, **not** the pure backoff. With `handle_boom` that runtime is near zero, so the
error is small — but write the sentence, because Din 6 will ask what the number is a number *of*.

**Then answer, before Step 5:** are the gaps growing? Does the growth stop at your cap? And **the question
that decides whether the measurement means anything at all** — is your first gap larger than
`POLL_INTERVAL_SECONDS`? If it is not, what did you actually measure?

> **Terms used in this step**
> - **`lag()`** — a window function returning the previous row's value in an ordered partition.
> - **Inter-attempt gap** — the interval between consecutive dispatches of the same job.

---

## Step 5 — Jitter: several jobs, one instant, and look at the spread (20 min) · executable

Enqueue **several** `boom` jobs together (four or five is enough) and let them fail. Then compare their
attempt timestamps:

```sql
select job_id, executed_at,
       executed_at - min(executed_at) over () as offset_from_first
  from job_executions
 where job_id in (<ids>) order by executed_at;
```

**What you are looking for is spread within an attempt round, not spread within a job.** Group the rows by
which attempt number they are and check whether jobs that failed together came back at *different* instants.

**One worker versus several is itself a decision, and it changes what this can show.** With one worker the
retries are serialised by the worker itself, so some of the spread you see is the worker's own turn-taking
rather than your jitter. With two workers you get closer to a real herd and you also get two variables.
**Pick one, write which, and write what the pick makes the measurement unable to show.**

**Output:** the offsets, and a plain statement — is the observed spread larger than what the poll interval
alone would produce? If your jitter's range is smaller than `2.0 s`, think about what that means before you
read anything into the numbers.

> **Terms used in this step**
> - **Attempt round** — the *n*-th attempt across a set of jobs that failed together.
> - **Spread** — the width of the interval containing a set of timestamps that "should" have been
>   simultaneous.

---

## Step 6 — Is the bound a real bound? And is a bounded-out row distinguishable from a stuck one? (15 min) · executable

Two separate checks, and the second one is the interesting one.

**6a — the bound holds.** With the worker still running, read twice with a gap:

```sql
select id, status, attempts from jobs where id = <boom job>;
select count(*) from job_executions where job_id = <boom job>;
```

`attempts` stopped at `max_attempts` and the execution count **stopped growing while the worker is still
alive**. If the count keeps climbing, retry is unbounded and `P-01`'s hazard is now a loop.

**6b — and this is `P-16`'s shape on a new column.** A job that has exhausted its attempts and a job that is
genuinely stuck should not read the same in `psql`. Look at the bounded-out row:

- If its `status` is terminal and `attempts = max_attempts`, the two fields **together** say *stopped by
  design*.
- If its `status` is `pending` and `attempts = max_attempts`, the row is **claimable and not being
  claimed** — which is exactly what a stuck row looks like. And ask the follow-up that matters: **what
  stops a worker from claiming it?** If the answer is "the claim query filters on `attempts`", then that
  filter is now part of the claim path and it needs its own line in the log.

**Output:** the bounded-out row verbatim, and one sentence on how an outside observer tells the two states
apart using only `psql`.

---

## Step 7 — The retry writer's guard, tested against the reaper (10 min) · executable

Deliberately invert the order: let the **reaper** reclaim the row first, then let the worker's retry write
land on it.

**Output:** the retry write's `rowcount`.

- `rowcount = 0` → the row was already `pending`, the guard rejected, and `attempts` was **not** incremented
  a second time for one failure.
- `rowcount = 1` → the reclaim and the retry both wrote the same transition, and `attempts` moved twice for
  one failure. **That is a `PROBLEMS.md` entry with today's number.**

**This step exists because Din 2 shipped a guard that was present and untested** (`P-20`) and Din 3 had to
have its heartbeat equivalent run by the reviewer at day close (`P-21`). Do not make it three.

**And note what this check cannot reach, so you do not overclaim it.** Yesterday established that the guard
asks whether the value **is** `'running'`, never **whose** `'running'` it is — so if a *second worker* has
re-claimed the row, the retry write from the first worker satisfies the guard and returns `1`. That case is
Din 5's (fencing token). **Today's check covers the reaper-first ordering only**, and the log should say so.

---

## Step 8 — Reading: Marc Brooker on timeouts, retries and backoff (30 min)

The plan names this reading specifically because the thundering-herd argument is sharper there than in the
books, and because it is where `D-23`'s `Cost` line comes from.

**Output:** at least two one-line links appended to `docs/ddia_summaries/DDIA_CH8_LINKS.md` (same file the
Ch 8 lines go into), each right-hand side an **existing** named entry. `P-01`, `P-14` and `P-22` are natural
fits.

**Carried debt, and it changed shape yesterday:** the file's Din 3 lines (10–13) were written by the
**reviewer** after three consecutive append slips. So today's two are yours, and **the four reviewer lines
need confirming in your own words** — a link you did not write is a link you cannot defend at `D-22`. That
confirmation is not today's deliverable; noticing that it is owed is.

---

## Step 9 — Log, reconciliation, cleanup, commit (15 min)

Full shape: goal → goal met (yes/no/partial) → **anything else learned** (separate field) → 📊 Measured →
💡 Understood → 🧠 self-check with an honest score → corrections table → 🚧 Unresolved → ❓ Next thought.

Into the log specifically: **both Step 1 decisions with the cost of the option not taken**; the backoff
formula **verbatim**; the jitter formula **separately**; `max_attempts` with its reason; the measured
inter-attempt gaps in `Etc/UTC`; the jitter spread across several jobs; the bounded-out row verbatim; and
**Step 7's `rowcount`**.

**Reconciliation** — opening counts from **Din 3's log entry**, and the post-probe line specifically:
`86 succeeded / 9 failed / 1 pending / 0 running / 96 total`, `job_executions 70`, `max(id) 97`, seq `97`.
Never `max(id)`, never id contiguity.

Today's delta has **three** sources and they stay separate:

| Source | Effect |
|---|---|
| Job **97** (reviewer probe, `sleep`) | leaves `pending`; `job_executions` **`+1`** |
| Step 3's single `boom` job | `+1` job; `job_executions` `+N` where `N` is its attempt count |
| Step 5's several `boom` jobs | `+k` jobs; `job_executions` `+` their attempts, and that is most of today's excess |

**`job_executions` will exceed the `jobs` delta by a lot today, and that is expected rather than a finding.**
The finding is *which* cause each extra row has. And there are now **four** causes in the table:
same-worker re-dispatch (job 44, Week 1), reclaim re-execution (63/65, Din 2), overlapping duplicate (95,
Din 3), and retry (today). **Write which ids are in which category**, and use the word *duplicate* only
where overlap was proved.

**`PROBLEMS.md`** — likely a new entry. Candidates: a backoff smaller than the poll interval being invisible;
a bounded-out row and a stuck row reading identically; or Step 7's `rowcount` if it comes back `1`.
**Grep on the day you assign the number.** `P-23` was taken on Din 3, so `P-24` is the likely one, and the
grep still runs:

```powershell
Select-String -Path docs\PROBLEMS.md -Pattern '^## P-'
```

**`DECISIONS.md` gets nothing today.** `D-23` is Din 6's, built from today's numbers. Today's values sit in
the log with `[MEASURED]` tags.

**Cleanup — this has failed three days running and today the queue is not empty:**

- Copy the relevant output **out of** the captures **before** deleting them. Yesterday the reaper's capture
  was deleted before its reclaim line and its `candidates=0` lines were copied up, and the reviewer had to
  regenerate the shape. Three things get copied every time: the failure lines, the retry write's `rowcount`
  lines, and the `Claimed job` grep count.
- **Kill every worker and the reaper.** Then run the process check **again** and put its output in the log.
  Din 1 left two PIDs, Din 2 left a reaper `~33 min`, Din 3 left **two real workers `~4h 55m`** with two
  live asyncpg backends `[MEASURED-R]`, and all three days the report said the close was clean.
  `idle in transaction = 0` and `processes = 0` are **two different checks**.
- Probe **rows are not deleted** — ids go into the log by name and count in the delta.

**Commit:** staged paths **by name**, never `.`. Today that is `src/worker.py`, possibly a migration if
Decision 2 went to Option A, `docs/logs/WEEK_02.md`, `docs/PROBLEMS.md`.

**One carried item worth a line:** `super_slow` exists in **no commit** (`P-23`), so Din 3's centrepiece
cannot be re-run from `HEAD`. Today does not fix that, but if you touch `worker.py` anyway, a
`payload`-driven duration is the cheap version — and if you decide not to, that decision belongs in the log
so `D-22` can cite it.

---

# PART B — PREDICTION QUESTIONS

**Not in this file, on purpose.** `docs/planning/WEEK_02.md`, `PART B — PREDICTION QUESTIONS` block,
`## Din 4` subsection — six questions.

Answer from your own head **before** the relevant step runs, **in a file**, and paste that file's path with
the answers at day close. `idk` is a valid written answer and scores as not-answered, which is accurate.

| Part B question | Answer it before |
|---|---|
| 1 (`attempts` on claim vs on failure — which situation separates them, and did it actually happen this week?) | Step 1 |
| 2 (reaper's `running → pending` vs retry's — where does the difference show, and does your policy show it?) | Step 1 |
| 3 (retry without backoff increases what? name one concrete failure cause) | Step 2 |
| 4 (why can't jitter be evidenced by one job? how many, and failing when?) | Step 2 |
| 5 (first backoff smaller than `POLL_INTERVAL_SECONDS` — what is the measured delay a number of?) | Step 4 |
| 6 (a **stuck** job vs a **bounded-out** job — how do you tell them apart from `psql`?) | Step 6 |

---

# PART C — VERIFICATION

**Clock discipline:** all delay arithmetic comes from `job_executions.executed_at`, which the database
writes in `Etc/UTC` — so today's headline numbers need **zero** conversions. Worker stdout is naive local
(IST); the measured offset is `local − db_utc = 5:29:59.994671`, read gap `7.262 ms` `[MEASURED-R]`. Label
every timestamp with its clock. Captures use `python -u`.

Each row was written by asking: *what wrong implementation would also pass this?*

| Check | Command | Mechanism present | Mechanism absent |
|---|---|---|---|
| **`attempts` actually moves** | `select id, status, attempts from jobs where id = <boom>;` twice, with a gap | `attempts` increased, and its value matches the dispatch count in `job_executions` | `attempts` at `0` while stdout shows more than one failure — the increment never landed, or its guard rejected. **`rowcount` says which, and a single read of `attempts` cannot** |
| **The increment count matches the policy** | `select j.id, j.attempts, count(e.*) from jobs j join job_executions e on e.job_id=j.id where j.id = <boom> group by j.id, j.attempts;` | Under Option A the two numbers are **equal**; under Option B `attempts` is **one less** than dispatches, or equal, depending on where the last one landed | The two numbers differ in a way your policy does not predict. **This check is the only one that tests the policy rather than the code** — write the expected relationship *before* running it |
| **The measured gap is backoff, not poll interval** | The `lag()` query from Step 4 | First `gap` is **larger** than `POLL_INTERVAL_SECONDS = 2.0`, and subsequent gaps **grow** | Every `gap` sits at `~2.0–2.02 s`. Then the number is the poll interval, and a correct backoff and a **missing** backoff produce the same list. `P-22`'s shape on a new quantity — and this is today's most likely silent failure |
| **The cap engages** | Same `gap` list, last attempts | Gaps grow, then **flatten** at one value — that is the cap | Gaps keep growing. No cap. The job has practically stopped without crossing the bound: a *silent stop*, not a bounded retry |
| **Jitter produces spread, and it is not the worker's turn-taking** | Step 5's `offset_from_first`, grouped by attempt round | Jobs that failed together return at **different** instants, and the spread is **wider than `2.0 s`** | Offsets clustered at one instant → no jitter, and `P-14`'s convoy has reappeared inside retry. Offsets spread by `~2 s` steps → that is one worker taking turns, **not** jitter. A single-worker run cannot separate these two, so state which you ran |
| **Retry is bounded** | `select count(*) from job_executions where job_id = <boom>;` twice, worker still alive | Count **stops** growing while the worker is running, and `attempts = max_attempts` | Count keeps growing — unbounded retry, `P-01` as a loop. **The worker must still be alive for this check to mean anything**; a stopped count with a dead worker proves nothing |
| **Bounded-out ≠ stuck** | `select id, status, attempts from jobs where id = <boom>;` plus *"what stops a worker claiming it?"* | `status` terminal **and** `attempts = max_attempts` — two fields agreeing that it stopped by design | `status = 'pending'` with `attempts = max_attempts` — claimable and unclaimed, which is what a stuck row looks like. `P-16` on a new column |
| **The retry writer's guard is a real guard** | Step 7: reaper first, then the retry write | `rowcount = 0` — row was `pending`, guard rejected, `attempts` moved **once** for one failure | `rowcount = 1` — reclaim and retry wrote the same transition and `attempts` moved **twice**. Record it, do not fix it today |
| **The reaper is distinguishable from the retry writer** | Reaper capture's per-pass lines against the worker's retry lines, same row | You can say **which** writer moved the row, because the reaper prints a line per pass now (`candidates=0` included) | No reaper line at all. Din 3 fixed this (`P-20`); if the capture is deleted before being copied, the fix is undone in practice |
| **75 untouched** | `select id, status from jobs where id = 75;` | `failed` | `pending` or `running` — a terminal row resurrected. `E4`: record it, put it back, **and record the revert** |
| **Probe row 97 accounted separately** | `select job_id, count(*) from job_executions where job_id = 97;` | Exactly **1**, attributed to the reviewer probe and **not** to today's retries | 97's row folded into the retry delta, or 97 still `pending` at close with no explanation |
| **Log completeness** | `Select-String -Path <capture> -Pattern 'raised an exception' \| Measure-Object` against `attempts` | Failure-line count matches `attempts`, and the last line of the file is intact | Count low, or a file cut mid-line. Then *"retry stopped"* and *"the log stopped"* are the same output (`P-18`). `echo=True` buries this — grep, do not scroll |
| **Nothing else moved** | `select status, count(*) from jobs group by status;` and `select attempts, count(*) from jobs group by attempts;` vs Din 3's close | `attempts` now has **more than one** bucket, and every non-zero row is a job you enqueued today | A non-zero `attempts` on a row you did not touch — including 44/63/65/95, which have all executed twice and must **stay** at `0`, because nothing retroactively counts a reclaim |

**Two checks deliberately absent.** Anything claiming the retry policy prevents duplicate side effects —
nothing today does, and Week 3 owns it. And anything blessing `max_attempts`, `base`, or the jitter range as
*correct* — all four were chosen, and Din 5's `dead_letter` arrival plus Din 6's `D-23` is where they get
defended.

---

# PART D — SCOPE GUARD

| Tempting | Owner | What you lose by doing it today |
|---|---|---|
| Add `dead_letter` to `status` while you are here — retry stops and there is no name for the stop | **Din 5 (`D-06`)** | `NOT VALID` + `VALIDATE CONSTRAINT` gets its own day, with its `ACCESS EXCLUSIVE` window measured. Doing it today puts a schema migration and a retry policy in the same run |
| Idempotency key — retry makes the duplicate risk obvious now | **Week 3** | Same trap as Din 3, one day later. Living with bounded retry **before** seeing the fix is what makes Week 3's property test a proof |
| Build the fencing token — Din 3 asked for it twice | **Din 5** | Today's Step 7 **measures** what the `status` guard cannot express. Fixing it now turns Din 5's argument from a measurement back into a memory |
| Align backoff with the lease duration so the numbers look tidy | **`D-22`, Din 6** | Lease `30 s` now has two measurements attached to it (`1.798192 s`, `≥ 15.04 s`). Move it and Din 3's run stops being comparable to today's |
| Tune the heartbeat interval | **Din 3's number, frozen** | Run 2's narrowing evidence was taken at `10.0 s`. Change it and that evidence describes a setup that no longer exists |
| Make retry "smart" — inspect the failure type and decide | **outside this week** | `handle_boom` fails **identically** every time, and that is what makes today's variation entirely yours. Conditional retry adds a second source of variation |
| Put `max_attempts` in env/config | **outside this week** | Today it is a **number with a written reason**. Configurable replaces the reason with a default |
| Change the claim query's two-part shape | **`D-02` — locked** | Today **adds** to the claim (a time condition, and `attempts` under Option A). The shape is not replaced |
| Two workers everywhere so the herd is convincing | **one variable per run** | Step 5 may use two **if you write that you did** and write what it makes unmeasurable. Silently switching worker count between Step 4 and Step 5 makes the spread belong to nobody |
| Turn off `echo=True` because the captures are noisy | **Week 4, with metrics** | The reaper's own per-pass line now exists (Din 3), so this is finally *safe* — but it is still a separate decision with its own day |
| Add a `failed_reason` / error column while you are in `worker.py` | **outside this week** | Today is a policy and a set of measured delays, not a new field |
| Fix `super_slow` properly with a new named handler | **`P-23`, and it is a one-line decision** | A `payload`-driven duration is the cheap version and it makes the knob explicit. A new named handler is a second registry entry doing what the first should have done. Either way: **decide in writing**, do not drift |

**Not being built today:** `dead_letter`, idempotency, dedup, fencing tokens, shutdown changes, metrics,
indexes, conditional retry, config extraction, a second reaper. Today produces **two written decisions with
the cost of the road not taken, one verbatim backoff formula, one verbatim jitter formula, a measured
inter-attempt gap list in one clock, a measured jitter spread across several jobs, a bounded-out row that is
distinguishable from a stuck one, and the retry writer's `rowcount` against a reaper that got there first**
— and the gap list is the part `D-23` rests on.
