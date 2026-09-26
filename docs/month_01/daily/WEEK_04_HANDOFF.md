# Week 4 Handoff — What Stuck, What Needs Reinforcement, What Month 2 Must Not Assume

Definitions, unchanged from Weeks 1–3 so the four handoffs read side by side:
- **What Stuck:** Rebuildable from scratch with no notes. Blank editor, nothing open.
- **What Needs Reinforcement:** Recognisable, but not derivable under viva pressure. *"haan haan ye to pata hai"* is this category's signal.
- **What Month 2 Must Not Assume:** The empirical reality and open holes left by Month 1 that Month 2 must take as given.

**This handoff closes Month 1.** It carries a fifth section the previous three did not have — the
[Month 1 verdict table](#month-1-verdict-table) — and a [line-by-line DoD audit](#definition-of-done-audit-week-4).

> **Provenance:** every number below is `[MEASURED]` on this machine, `[MEASURED-R]` at review,
> `[REPORTED, NOT VERIFIABLE]` (recorded, artifact gone — `P-45`), `[NOT TESTED]`, or `[NO EVIDENCE]`.
> **No new measurement was taken on Din 6**; it was a writing day, and every figure here has a prior day as its
> source.

---

## What Stuck

1. **A compare-and-set on a *cycling* value cannot express ownership, and a monotonic epoch can (`D-26`).**
   - `status` cycles: `running → pending → running` is reachable through a reaper reclaim. So `WHERE status =
     'running'` asks *"is this row held?"* and has no vocabulary for *"is it held by me?"*
   - The harm was measured **before** the fix, deliberately: job `126`, stale worker A marked `succeeded` with
     `rowcount = 1` while worker B's handler was still running, `32.973 s` before B finished — at which point
     B's own correct mark conflicted with `rowcount = 0`. **The wrong writer won and every compare-and-set was
     correct at the instant it ran.**
   - The fix is one `bigint` incremented **inside the claim's own `UPDATE`** and read back through that
     statement's `RETURNING`, so the held generation and the committed generation cannot diverge. Job `128`:
     `held_generation=1 current_generation=2 rowcount=0`.
   - **Only the claim increments it.** The reaper deliberately does not. That is why `attempts` and
     `claim_generation` moving *together* proves claims and moving *apart* proves reclaims — the property Din
     4's `attempts = 4, claim_generation = 4` result depends on.

2. **A fence rejects stale *writes*; it does not cancel stale *work* — so `effect_key` is a second layer, not a
   consequence of the first (`D-25` amendment).**
   - In job `128`, worker A had already attempted its effect insert before being fenced.
   - Putting the generation *into* the effect key (`job:{id}:gen:{g}`) **destroys** dedup: every redispatch
     mints a new key, `ON CONFLICT` never fires, duplicates commit — with the `UNIQUE` index present and
     reporting nothing wrong. Claim identity must change per claim; effect identity must not.

3. **A dual write has no safe ordering, and an outbox removes the dual write without making delivery atomic
   (`D-27`).**
   - Commit-then-call loses the call; call-then-commit duplicates the call on retry. Neither window closes by
     reordering.
   - One `COMMIT` covering `side_effects` + `outbox` makes local effect and delivery *intent* atomic. Measured
     four consecutive times in Din 4's crash loop: `side_effects = 0` across four handler runs.
   - **Delivery stays at-least-once.** Exactly-once *storage* at the far end is the receiver's
     `UNIQUE (idempotency_key)` — in another service. Relay can **require** it; Relay cannot enforce it.

4. **`rowcount` is the return value that carries the safety, and two different predicate failures produce the
   same `0`.**
   - `Mark fenced` (generation mismatch) and `Conflict on mark` (status mismatch) are both `rowcount = 0`.
     Din 4's fence was grepped by line **name** — `fenced_lines=1`, `conflict_on_mark_lines=0` — because
     `rowcount` alone cannot separate them.
   - Same shape everywhere: `ON CONFLICT DO NOTHING` turns a would-be exception into a readable `0`, and the
     reaper's reclaim reads `matched` from `RETURNING` rather than assuming.

5. **A lease runs on the server's wall clock, not on activity — and that makes recovery latency a function of
   the outage's length.**
   - During Din 5's `26.8 s` outage `claimed_at` was frozen while `now()` advanced, so the lease was already
     spent when the database returned and the row was reclaimable *immediately*.
   - The honest form is a bound, not a number: `remaining lease + one reaper poll + possibly one failed poll`,
     **conditional on the reaper being alive.**

---

## What Needs Reinforcement

1. **Where the retry bound is *evaluated* versus where the counter is *incremented*.**
   - `attempts` increments in the claim's `UPDATE`; the `MAX_ATTEMPTS` comparison happens in
     `except Exception`. The `except` block only **reads** `current_attempts`.
   - One root cause, two opposite harms, and both were derived rather than recalled: `os._exit` skips the
     branch so a poison pill never terminates (`P-36`, `attempts = 4`, `status = running` throughout), and a
     mid-handler outage spends two attempts for one fault so a healthy job can be dead-lettered (`[NOT TESTED]`,
     `D-26` Cost 6).

2. **`[NO EVIDENCE]` versus *broken*, and *Recovery mechanism* versus *Evidence*.**
   - Recovery mechanism is a **claim** and can be written without ever running the failure. Evidence is an
     **observation**. Row 9 of the README's failure matrix has a confident mechanism (*"none"*) and
     `[NO EVIDENCE]`, and both cells are load-bearing.
   - An empty cell says *"not considered"*. `"none"` + `[NO EVIDENCE]` says *"considered, and it is a gap"*.

3. **`count(*)` lies after a `DELETE`; the sequence does not.**
   - `sink_deliveries` reads `7` rows with `sink_deliveries_id_seq.last_value = 10`. A reader who checks only
     the first learns *"seven deliveries happened"*. Ten did.
   - **Read a sequence alongside `count(*)` on any table a `DELETE` has ever touched.** This is a different
     cause from `P-05`'s rollback gaps and the two must not be written as one.

4. **Compensating errors, and why a reconcile chain is checked per line.**
   - Two errors in opposite directions cancel in a total, so the aggregate looks right and both hide. This week
     supplied a live example: had `sink_deliveries`' `-3` gone unrecorded and met a `+3` transcription slip
     elsewhere, the chain would have closed with two faults invisible.
   - **A total that joins is not evidence that the lines are right.** Every line carries its source.

5. **A liveness probe that shares the pool it reports on.**
   - `/healthz` queues in `QueuePool`'s FIFO behind user traffic and times out while the process is healthy and
     merely busy. Its remediation is a restart; a restart does not fix load.
   - Four things it deliberately does **not** report, each for its own reason: worker liveness (the heartbeat
     runs only during a job, `P-21`), dispatcher liveness (nothing observes it), queue backlog (business volume
     on an unauthenticated port, `D-03`), and its own pool saturation (measuring it needs the exhausted
     resource).

6. **Which of Month 1's numbers can be re-derived, and which cannot.**
   - Three cannot (`P-45`): pool timeout `3.0055 s`, receiver contention `2.8133 s` vs `0.4703 s`, `/healthz`
     timeout `3.1618 s`. No `w4d5_step2*`/`w4d5_step3*` log survives, no probe script is in the tree, and
     `.gitignore` contains `logs/`.
   - The drain rate is the counter-example and the strongest number of the week precisely because it **was**
     recomputed from retained timestamps: `7.01 jobs/s`, `0.1427 s` per job, `186` marks in `26.391 s`.

---

## What Month 2 Must Not Assume

1. **Do not assume a crash is recoverable at the *process* level. It is not, and this is Month 1's largest
   hole.**
   - `src/worker.py`'s `except Exception` wraps **only** handler execution; the claim block and the terminal-mark
     block are unguarded. `src/reaper.py`'s loop has no `try` at all. `src/dispatcher.py` is the same shape.
   - Din 5's `26.8 s` outage killed the worker outright: outermost frame `worker.py:321 asyncio.run(run_worker())`
     → `worker.py:185 await session.execute(claim_query)`, stdout stops at `15:22:16.128` and never resumes with
     `echo=True` on `[MEASURED-R]`.
   - **The failure lands on the *most likely* path**, not the least likely: an idle worker spends nearly all its
     time in the unguarded claim poll.
   - **Relay ships no supervisor** — no `restart:` policy in `docker-compose.yml`, no systemd unit, no
     orchestrator manifest. A one-second database restart stops all execution until a human intervenes (`P-43`).
   - **Correction Month 2 must carry forward:** Din 5's log recorded the worker as *"caught the exception and
     remained alive"*. That is false. Fix order is not a preference: **exception boundary first, then re-price
     `pool_pre_ping`** — Din 5's Faisla 4 rejected the flag on the stated ground that these loops have "built-in
     exception handling", and that premise does not exist.

2. **Do not assume the reaper was ever tested as a live recovery component.**
   - It was **not running** during Din 5's outage. Its first engine line (`select pg_catalog.version()`) is at
     `15:22:46.428`, after the database returned; it was launched by hand and reclaimed `63 ms` later.
   - **`7.9 s` is process-launch latency, not a recovery bound.** Do not quote it.
   - The case *"worker and reaper both die in one outage"* has never been produced. And **no two-reaper run has
     ever been done**, which is why `D-29` rejects the advisory-lock alternative **on scope, not on
     measurement**. That run is the honest owner of `D-29`'s weakest field.

3. **Do not assume `alembic upgrade head` is data-safe, and do not re-run `w4d4_sink_unique` expecting a clean
   round trip.**
   - Commit `cb17c36` put an unguarded `DELETE … USING` inside `upgrade()` and it ran on the evidence database:
     `sink_deliveries` `10 → 7`, ids `3, 5, 10` gone, sequence still `10` `[MEASURED-R 2026-09-11]`.
   - Three separable properties: **irreversible** (`downgrade()` drops the constraint and cannot restore rows —
     so the round trip verified as clean was clean in *schema*, not in *data*), **unlogged** (no row count, so
     `-3` appears nowhere in the day's transcript), **unconditional** (it deletes whatever it finds in whatever
     database it is pointed at).
   - **What it deleted was evidence:** `P-33`'s original race measurement and `P-40`'s negative control. The
     dedup fix consumed the evidence for the problem it fixed (`P-46`).
   - The migration-hygiene rule applies to **future** revisions. `w4d4_sink_unique` is **not** to be rewritten —
     it has already run everywhere it will ever run, and editing a migration that has run gives two databases
     divergent history.
   - **The `-3` must stay named in any future reconcile chain.** A delta gate whose frozen set excludes the
     bucket where the change landed reports `0` truthfully and misses three deleted rows. Both statements are
     true; only one was written down at the time.

4. **Do not assume the `SINK_DEDUP=0` arm is a negative control. It is not any more.**
   - With the constraint below both branches, dedup-off gives `200 applied` + `500 Internal Server Error` from
     an unhandled `IntegrityError` — not `2` rows `[MEASURED-R]`. **A `500` is not a duplicate**, and it is
     indistinguishable from a receiver bug in any log.
   - Din 3's Run A / Run B numbers remain valid **as history** and are **not** reproducible against current
     `HEAD`. *"Exactly one row at the receiver"* is now an **enforced** invariant, and an enforced invariant
     needs a different kind of evidence than a measured one.

5. **Do not assume delivery identity is defined anywhere.**
   - `src/dispatcher.py` mints `f"job:{job_id}"` — **one key per job**, not per delivery attempt and not per
     effect. The property that makes `result = duplicate` safe is *one key ⇒ one intended payload*, and it is
     asserted nowhere, tested nowhere, and stated in no design file (`P-42`).
   - `D-24` covers enqueue identity and execute identity. **Delivery identity is a third layer with no written
     invariant.** Any change that puts two payloads under one job — a second effect kind, a regenerated body, a
     re-run after `dead_letter` — turns a silent discard into data loss whose only trace is a routine-looking
     `duplicate` line.
   - Corollary: `D-25` Cost 2's *"one logical effect per job"* now reaches across a service boundary. One change
     breaks both layers.

6. **Do not assume the dispatcher is bounded or observed.**
   - No backoff, no attempt bound (`P-35`), and `outbox.attempts` counts **committed marks** rather than
     attempts — so the column that looks like an attempt counter cannot bound anything. `MAX_ATTEMPTS` governs
     jobs, not deliveries.
   - It holds a Postgres row lock **across** the HTTP call by design, so a receiver-side lock wait consumes a
     Relay connection in `idle in transaction`. Composed with a small pool that is a plausible exhaustion path —
     and the composition is `[INFERRED]`; no run has produced it (`P-41`).
   - A dead dispatcher is silent: `dispatched_at IS NULL` rows accumulate with no alarm.

7. **Do not assume the numbers about capacity are as comfortable as Din 5's log says.**
   - Headroom is **`~3–5`** connections under full theoretical saturation, not `22`. The `75` figure omits the
     load script's own engine (up to `+15`) and the observing `psql`/`docker exec` sessions (`+2–4`); a full
     count is `~92–94` against `97`. **And full saturation has never been run.**
   - The throughput ceiling is **handler duration**, not `echo=True`: `0.1 s` of a measured `0.1427 s`; echo is
     `~11 ms`, about `8%`. Removing echo moves `7.01` to roughly `7.6 jobs/s`. Din 5's Faisla 1 states this
     backwards.
   - `POLL_INTERVAL_SECONDS = 2.0` is **discovery latency on an empty queue**, not a throughput divisor — the
     worker loop did not sleep while a backlog existed.

8. **Do not assume `pytest tests -q` protects any of this.**
   - `7 passed` covers schema and model invariants. It does **not** drive the worker loop, the reaper, the
     dispatcher, or any interleaving (`P-37`). Every concurrency result in Month 1 came from real OS processes
     and their stdout.
   - **And `requirements.txt` pins nothing** — all eleven dependencies are unconstrained, so a resolver run
     today may not reproduce the versions these measurements were taken on (`P-45`).

9. **Rows carried into Month 2 in the evidence database, by name.**
   - **Job `136`** — `136|running|1|1`, a `crash_at: before_commit` poison pill left deliberately untouched
     (`P-05`, `P-36`). Do not hand-terminate it; its mechanism is the record.
   - **Job `128`** — `running|2|2`, the fenced row. The fence discarded the only terminal mark offered, so the
     safety gain shows up here as a liveness cost. The problem changed shape; it was not eliminated.
   - **Job `108`** — `dead_letter` at `attempts = 4` against `MAX_ATTEMPTS = 3` (`P-27`).
   - **`113` of `145`** `job_executions` rows carry `claim_generation IS NULL`, and **`3` of `19`**
     `side_effects` rows carry `effect_key IS NULL` — outside the `UNIQUE`'s protection, since ordinary SQL
     treats nulls as distinct.
   - **`sink_deliveries` id gaps `3, 5, 10`** — permanent, and now themselves evidence (`P-46`).
   - **`outbox` id gap `2`** — a consumed sequence value with no row.
   - **Three `dead_letter` rows predate `last_error`** (`104`, `105`, `108`): terminal, with the diagnosis
     unrecoverable. Two (`129`, `130`) carry both `last_error` and `completed_at`.

10. **Do not open `BACKEND_ROADMAP_PART2.md`'s decisions as if Month 1's verdicts were provisional.** The
    verdict table below is written on the evidence that exists **today**. Reading it through *"Month 2 will fix
    that"* is what makes a verdict table worthless. `D-09`–`D-20` remain reserved by Part 2; new decisions
    continue from **`D-30`**, and the next free problem card is **`P-47`**.

---

## Month 1 verdict table

Five contract promises. Three verdicts allowed: **`protected`** (holds against the failures tested — and the
scope is written next to it, or it is an overclaim), **`narrowed`** (the window is smaller, not closed),
**`[NO EVIDENCE]`** (not tested — which is **not** the same as broken).

| # | Promise | Verdict | Evidence, and the scope that limits it |
|---|---|---|---|
| 1 | An accepted job is never silently lost | **`narrowed`** | **Scope, from `202`'s semantics:** *accepted* means a `202` was returned, which requires a committed `jobs` row. `POST /jobs` cannot return `202` without that commit, so a request arriving while Postgres is unavailable is **rejected, not accepted**, and falls outside this promise. **A rejected job is not a lost job.** · `[MEASURED]` a `running` row returns to `pending` after lease expiry on the reaper's next poll — job `1`, `matched=1`, generation unchanged. **Not `protected`, for a run-level reason as well as a scope-level one:** the evidence needed was *an accepted job that was `running`, whose worker died, that came back anyway*. Din 5 did not produce it — job `1` was pre-seeded `running` and never claimed by that worker, and the reaper was launched by hand **after** recovery (`P-43`) |
| 2 | Duplicate execution does not duplicate side effects | **`narrowed`** — and the two layers have **different** verdicts, which is the part that must not be collapsed | **Local, and this one is Relay's own:** behind `UNIQUE (effect_key)` + `INSERT … ON CONFLICT DO NOTHING`, a job's `side_effects` row stays **one** however many times it executes — `[MEASURED]` Week 3 job `114`, Week 3 job `112` (`rowcount` `{1,0}`), and Din 4's four interleavings. **Duplicate execution happens and no attempt was made to prevent it**; what is bounded is the duplicate *effect*, not the duplicate *run*. · **External, and this one is not Relay's guarantee:** delivery is **at-least-once**; exactly-once is the **receiver's** job. Behind the receiver's `UNIQUE (idempotency_key)`, storage does not duplicate — `[MEASURED]` Din 4: `1 × 200 applied` + `4 × 200 duplicate` = **`1`** row. **The noun that `narrows` applies to is *storage*, not *delivery*:** five requests still crossed the network, `src/dispatcher.py` has no backoff and no bound (`P-35`), and `result=duplicate` asserts the **key** was seen, not that the payload matches (`P-42`). A receiver without that constraint breaks this promise on the external side **without violating a single Relay guard** — Relay's requirement on the receiver, not Relay's property |
| 3 | Retries are bounded | **`narrowed`** | `[MEASURED]` `MAX_ATTEMPTS = 3` with exponential backoff and equal jitter; three dispatches, gaps `4.07 s → 6.10 s`, execution count frozen at the bound while the worker stayed alive. **Two named leaks:** the bound governs retry **scheduling**, not dispatches — job `108` at `attempts = 4`, because a reclaim spends budget with no failure (`P-27`); and `os._exit` bypasses the `except` block where the bound is evaluated, so the branch is unreachable — Din 4's B′ reached `attempts = 4` and `claim_generation = 4` with `status = running` throughout, period `~32 s`, `2` sequence values burned per iteration (`P-36`). **A third case is `[NOT TESTED]`:** a mid-handler outage costs two attempts for one fault (`D-26` Cost 6) |
| 4 | Crashes are recoverable | **`narrowed`** at the **row** level · **`[NO EVIDENCE]`** at the **process** level | `[MEASURED]` Row level: four Din 4 interleavings on two real OS worker processes against a disposable database recovered every row — post-flush-pre-commit (nothing written, `side_effects = 0`), post-commit-pre-mark (`rowcount = 0`, effect count `1`, job `succeeded`), stale-writer-after-reclaim (`fenced_lines=1`), and delivery-then-dispatcher-crash (`1` stored row). · `[MEASURED-R]` Process level: a database restart killed the worker — the exception escaped `run_worker()` and the process exited, with no supervisor anywhere in the repository (`P-43`). **These are two different claims that had been written as one.** The row survives because it is durable and the lease expires; the process does not survive at all, and *"worker and reaper both die in one outage"* was never produced |
| 5 | Terminal failures enter a DLQ | **`narrowed`** — the strongest of the five, and still not `protected` | `[MEASURED 2026-09-11]` `dead_letter` is a real status in the `CHECK` constraint (landed via `NOT VALID` + `VALIDATE CONSTRAINT`), and five rows carry it: `104`, `105`, `108`, `129`, `130`. Since Din 2 a terminal row carries a **diagnosis** as well as a verdict — `129` and `130` have `last_error` (full traceback) and `completed_at`; `104`, `105`, `108` predate the column and their cause is unrecoverable. `last_error` is deliberately **absent** from `GET /jobs/{id}`, since Relay has no authentication (`D-03`). **Why not `protected`:** `dead_letter` is reachable **only** through the handler-exception path, so `P-36`'s poison pill (never terminal) and `P-27`'s overdraft (`attempts = 4`, terminal for the wrong reason) both sit outside it. One root cause — the bound's location — puts two failures outside the DLQ in opposite directions |

**Not one of the five is a bare `protected`, and that is the honest result.** Three weeks of writing `narrows`,
`bounds`, and *under the failures tested* would be undone by a single unqualified `protected` in this table.

---

## Definition of Done audit — Week 4

Line-by-line against `planning/WEEK_04.md`. Every unticked item gets **one** line: `deliberately deferred`
**with an owner**, or `slipped` **with what specifically it needs**. Two of one, or neither, is the silent carry
this audit exists to prevent.

### Build

| Item | Status | Line |
|---|:---:|---|
| `jobs.claim_generation` migration, default `0`, `NOT NULL` | ✅ | `w4d1_claim_generation`; single head verified |
| Claim CAS `RETURNING` generation; heartbeat + mark + `completed_at` gated on `:g` | ✅ | All four predicates carry the generation term |
| `job_executions.claim_generation`, old rows honest `NULL` | ✅ | `113` `NULL` / `32` stamped / `145` total `[MEASURED 2026-09-11]` |
| `jobs.completed_at` + `jobs.last_error`, both decisions written | ✅ | Din 2 Faisla 1–3; published as `D-23`'s amendment |
| Structured lifecycle log, grep-able by `job_id`, with generation | ✅ | Proven by use: Din 4 grepped the fence by line **name**, `unstructured = 0` |
| `outbox` table, in **one** `COMMIT` with the side effect | ✅ | Din 3; `D-27` |
| `src/dispatcher.py`, `FOR UPDATE SKIP LOCKED`, HTTP-in-transaction decision written | ✅ | Din 3 Faisla 4; cost recorded as `D-27` Cost 3 |
| Receiver + `sink_deliveries` `UNIQUE`, **and a dedup-off switch** | ⚠️ | Both shipped, and **the switch is no longer a negative control** — it returns `500`, not `2` rows (`P-40`). Satisfied on its own terms; the *control* is `slipped` and needs either the constraint itself made the switch, or the receiver moved to its own database. Owner: Month 2 |
| `/healthz`, and what it does **not** report written down | ✅ | `D-28` Cost 2, four named omissions |
| Pool override (`pool_size=2, max_overflow=0`) in an isolated run | ⚠️ **slipped** | The run happened; the **observation** did not survive. `DIN_05_BRIEF.md`'s C3 required the per-process connection count filtered by `application_name`, and no `w4d5_step2*` log exists — so the override rests on having been *configured*, not on having been *observed* (`P-45`). Needs: the step re-run with the log committed, or the claim downgraded in writing. Owner: Month 2 |
| Load tool decision + **pinned version** in `requirements.txt` | ❌ **slipped** | Two specifics. (1) The decision is written (`locust`'s `28` transitive deps vs `httpx`) but its `Chosen` artifact `step4_load_probe.py` **is not in the tree**, so the rejection's chosen alternative has no implementation. (2) `requirements.txt` pins **nothing** — all eleven dependencies unconstrained. Needs: the harness committed, and a resolver run producing pins. Owner: Month 2 |
| Four metrics' SQL in one place | ✅ | Queue depth `214` · `p50 10.2849 s` / `p99 18.3357 s` · retry rate `0.0%` · DLQ `0` on the load DB |

### Hygiene

| Item | Status | Line |
|---|:---:|---|
| Every process `python -u` / `PYTHONUNBUFFERED`, last log line verified after an `os._exit` | ✅ | Din 4 B′; also how `P-43` was diagnosed — a surviving worker would have printed a `BEGIN` |
| `alembic heads` — exactly **one** head after Din 1 and Din 2 | ✅ | Verified each day; `w4d4_sink_unique` at close |
| Every new revision's `downgrade()` run on a disposable DB | ⚠️ | Done (`head → -1 → head`, `relay_w4d1_closeout` and Din 5 arm 3) — **and clean in *schema* only.** `w4d4_sink_unique`'s `DELETE` is not reversed by its `downgrade()`, so a round trip that passed as clean lost data (`P-46`). The **check** is satisfied; the **wording** is corrected here |
| `pytest tests -q` green after both migrations | ✅ | `7 passed`. Recorded, and **not** a gate over Week 4's code — the suite drives no worker, reaper, dispatcher, or interleaving (`P-37`). Coverage gap `deliberately deferred`, owner **Month 2** |

### Measured

| Item | Status | Line |
|---|:---:|---|
| Stale write's harm **before** fencing (`status`/`attempts` pair) | ✅ | Job `126`, stale mark `rowcount = 1`, `32.973 s` before the live worker finished |
| Fence fired — `rowcount = 0` in the stale worker's stdout, Din 1 **and** Din 4 | ✅ | Job `128` (single process) and job `7` (two real OS processes, `fenced_lines=1`) |
| Generation monotonic across `running → pending → running` | ✅ | `pre_generation = post_generation` on every reclaim; `attempts = 4` with `claim_generation = 4` on four real claims |
| First latency number from `completed_at`, with its `n` | ✅ | `p50 = 10.2849 s`, `p99 = 18.3357 s` over a `400`-job backlog — and these are dominated by **queue dwell**, since the metric is `completed_at − created_at` |
| `45 s` + `SIGBREAK` at `T = 3 s`, with three snapshots | ✅ | Runs 1 and 2 written separately; **Run 3 void with its cause named** (anchor bound to a specific job id, queue returned an older row) |
| One `COMMIT` with effect + outbox, and **both** gone on crash | ✅ | Din 3, and four consecutive times in Din 4's B′ |
| Delivery count `2` vs receiver effect count `1`, **and the dedup-off count** | ⚠️ **slipped** | First two `[MEASURED]`. The dedup-off count is **no longer obtainable on current `HEAD`** — that arm returns `500` (`P-40`). Din 3's Run A/Run B stand as dated history. Needs the switch redesigned before it can be re-measured. Owner: Month 2 |
| Four interleavings, two real worker processes, disposable DB | ✅ | A (fence), B (effect/mark seam), B′ (poison loop), C (delivery dedup), D (`SKIP LOCKED` loser) — five, on `relay_w4_witness`, dropped at close |
| `max_connections` + idle **and load** connection counts | ⚠️ **slipped** | Idle is `[MEASURED]` (`5` processes, `5` connections, `97` effective). The **load** counts were in the missing Step 2 log (`P-45`). Needs a re-run with the log retained. Owner: Month 2 |
| Pool exhaustion's exact error + wait time | ⚠️ **slipped** | `3.0055 s` and `QueuePool limit of size 2 overflow 0 reached` are `[REPORTED, NOT VERIFIABLE]`. Needs the artifact. Owner: Month 2 — and re-running today would produce a **fourth** number, not evidence for this one |
| `/healthz` latency/outcome **during** pool exhaustion | ⚠️ **slipped** | `3.1618 s`, same reason, same owner |
| `45 s` shutdown's **two** runs — yielding and `block: true`, written separately | ✅ | The pairing is the result: `signal_to_exit_s` is `~42.2–42.5 s` in **both** with opposite outcomes, so a single run would have reported the useless number. Real finding: `signal_to_handler_s = 42.068 s` |
| Queue lag as a **series**, not a single reading | ⚠️ | Series recorded (`91 → 133 → 177 → 221 → 267`) — **and it is transcribed inconsistently.** `DIN_05_ANSWERS.md` records `91 → 155 → 221 → 267`. The two imply different accumulation rates (`+8.8/s` vs `+12.8/s`), and the second matches `19.8 − 7.0`. `slipped`: needs one series designated authoritative against the retained log. Owner: Month 2 |
| Postgres-down's **two** failures named separately | ⚠️ **slipped** | Two were named and **one was described wrongly** — the worker did not remain alive, it exited (`P-43`); corrected today in the README's failure matrix and `D-28`. And the second real case (*worker and reaper both die*) was never produced, now labelled `[NO EVIDENCE]`. Needs: the corrected run once the exception boundary exists. Owner: Month 2 |
| Evidence DB delta `0` on Din 4 and Din 5 | ✅ **with its exclusion now named** | `0` on the eight asserted counters both days, independently re-read. **And `sink_deliveries` lost three rows on Din 5** — outside the frozen set by a decision taken two days earlier for a good reason. Both statements are true; only one had been written down (`P-46`). Din 6's bench asserts **nine** counters, `sink_deliveries` included |

### Written

| Item | Status | Line |
|---|:---:|---|
| Six log entries, each with `📊 Measured` filled | ✅ | Din 1–6 in `logs/WEEK_04.md` |
| Each day's `💡` **that day, in his own words** | ❌ **slipped** | Present for all six days and marked *"user must rewrite this in his own words"*; the rewrite has not happened, and this repeats Week 2's identical debt. Needs: six short rewrites with the reviewer text closed first. Owner: **the user**, Month 2 Week 1 |
| Six `PREDICTIONS_FROZEN.md`, sealed before the step | ✅ | Din 1–6; Din 6's SHA-256 `934764139408B2DAFBEC93CCA2BD8385FFEF2B105F75752F275A0296C82C9D97`, unchanged from C0 to C6 |
| `D-26` · `D-27` · `D-28` · `D-29`, every `Rejected` filled | ✅ | Published today. Numbers grepped free **before** writing (C0), because that collision has happened twice |
| `D-06`/`D-21`/`D-22`/`D-23`/`D-25` amendments | ✅ | Five amendment blocks, in place under their entries — not new entries, so a reader of the original never sees only the old truth |
| `README.md` — five things, zero empty cells in the failure matrix | ✅ | Nine-row matrix, three `[NO EVIDENCE]` cells, transaction boundaries drawn, zero banned vocabulary |
| Blog post, every claim with a number or a *"not measured"* | ❌ **deliberately deferred** | **Owner: Month 2, Week 1's writing slot**, titled *"Building a durable job queue on Postgres: what breaks and why"*, with its section skeleton already fixed in `DIN_06_BRIEF.md` Step 4. Deferred by the day's own cut order: a blog is a **publishing** artifact and everything else today is **evidence**, and incomplete evidence is worse than an unwritten post. **Not** *"kal likh doonga"* — it has an owner and a slot |
| `WEEK_04_HANDOFF.md` + Month 1 verdict table | ✅ | This file |
| `MAP.md` · `LEARNING_LOG.md` · `CURRENT_WEEK.md` | ✅ | Updated today |
| `POSTMORTEMS.md` | ⚠️ **deliberately deferred** | **Owner: Month 2.** No external incident was studied this week, and Month 1's own incidents are fully written as `P-43`–`P-46`. Copying them into a second file creates two homes for one truth and both drift. The next entry should be an **external** postmortem that maps onto `P-43` (process death with no supervisor) |
| `DDIA_CH11_LINKS.md` + `DDIA_CH9_LINKS.md` | ⚠️ **slipped** | `CH11_LINKS` exists. `CH9_LINKS` **does not exist in the tree**. Needs: one linking pass on Ch 9's consistency/consensus material, which is also the reading that would price `D-29`'s advisory-lock alternative. Owner: Month 2 |

### Carried debt — each with one line, none silent

| Debt | Status | Line |
|---|:---:|---|
| Week 2's `💡`/`🧠` sections written by the reviewer | ❌ **slipped**, third week carried | All six Week 2 days plus Week 4's six. Needs the rewrites above. Owner: **the user** |
| Five Week 2 answers | ❌ **slipped** | Owner: the user, alongside the `💡` rewrites |
| `DDIA_CH8_LINKS.md` lines 10–13 | ❌ **slipped**, and the debt is authorship rather than absence | `[MEASURED 2026-09-11]` All **18** items exist — `1`–`13` and `17`–`18` are Ch 8 links, `14`–`16` are the Din 4 Marc Brooker links. So nothing is missing. What is owed is that **lines 10–13 were written by the reviewer** at Din 3's close, after three consecutive append slips, and the user has not yet confirmed them in his own words. Lines 14–16 are the user's own; three of those five carry a reviewer note beneath them correcting a parenthetical, and line 18's mechanism is `[INFERRED]`. Needs: four short rewrites of `10`–`13`. Owner: **the user** |
| Week 1 Din 7's log entry | ❌ **slipped** | `logs/WEEK_01.md` has `Day 1`–`Day 5` and **no `Day 6` or `Day 7` entry** `[MEASURED 2026-09-11]` — and Din 6 is the day `D-01`/`D-02` were written, so the reasoning has a home and the day does not. Needs two short entries reconstructed from `DECISIONS.md` and the briefs, **labelled as reconstructed**. Owner: Month 2 |
| `P-29` — raw-evidence retention | ❌ **slipped**, and it now costs verifications | `.gitignore` contains `logs/`, so even retained logs are local-only. This is the direct cause of `P-45`'s three unverifiable numbers. Needs a decision: commit a curated `logs/evidence/` subtree, or copy the load-bearing lines into the day's log **before** cleanup. Owner: Month 2, and it is the cheapest high-value item on this list |
| **`P-47` — five `docs/` subtrees are gitignored, so this file is not in the repository** | ❌ **slipped**, opened at Din 6's commit | `[MEASURED 2026-09-11]` `git ls-files docs/` returns **twelve** files; the other ~90 are local-only, including **all four handoffs, twenty-nine BRIEF/KEY pairs, twelve `PREDICTIONS_FROZEN.md` files, `CURRENT_WEEK.md`, both roadmaps, and `DDIA_CH8_LINKS.md`**. The sharpest case is the frozen seal: the whole prediction discipline rests on immutability checked by hashing at C0 and C6, and **that hash is compared against a shell variable, on a file no commit contains.** Three tracked files (`LEARNING_LOG.md`, `MAP.md`, and `CURRENT_WEEK.md`) now link here, so those are dead links in a clone. **Not a typo — a classification problem:** `docs/daily/` legitimately holds sealed KEYs that should not be published, and the directory is a coarser unit than the distinction being enforced. Needs a scoping decision the reviewer will not take unasked, since it is about what becomes public. Owner: Month 2, **with `P-45` and `P-29` — all three are one root cause seen from three angles, and one retention decision closes all three** |
| `P-05` — sequence-gap list and job `136` | ⚠️ **carried by design** | Job `136` stays `running|1|1`, untouched. Its mechanism is `P-36`; hand-terminating it would delete the record |
| `P-44` — `/slow-hold` unauthenticated and unbounded | ⚠️ **deliberately deferred** | **Owner: Month 2.** Not fixed today because Din 6 changes no `src/`, and because `D-28`'s endpoint inventory carries it **by name** — removing it would delete the decision's subject. Three options, each weakening the Step 3 measurement slightly; pick one on the record |
| `P-43` — no exception boundary, no supervisor | ⚠️ **deliberately deferred** | **Owner: Month 2, and it is the first item.** Deliberately not fixed today: it is the **input** to promise 4's `[NO EVIDENCE]` verdict. Fixing it first would write Month 1's verdict against a system Month 1 did not have |
| `pool_pre_ping` re-decision | ⚠️ **deliberately deferred** | **Owner: Month 2, after `P-43`.** The order is load-bearing, not a preference — the deletion test's answer inverts once the missing exception boundary is known |
| `P-03` — `EXPLAIN ANALYZE`-driven index on `jobs` | ⚠️ **deliberately deferred** | **Owner: Month 2.** At `n = 133` a `Seq Scan` is correct. `D-23`'s `+123%` heap-page measurement from `last_error` is a real input to it |
| Handler timeout · retention · `job_executions` index · partitioning | ⚠️ **deliberately deferred** | **Owner: Month 2.** All four are `Cost` lines today, not features. The handler timeout needs one question answered first: *what is a timed-out handler's status?* — retryable burns budget, terminal dead-letters a slow-but-healthy job |

---

## Month 1 in one line

**The queue was never the hard part.** Every mechanism that mattered — `SKIP LOCKED`, compare-and-set,
`ON CONFLICT DO NOTHING`, a lease, an outbox — is a handful of lines and was correct almost immediately. What
took four weeks was learning **what each one does not do**, and the only way that was ever learned was by
producing the failure and reading the output: a `14.783 s` overlap, a `rowcount = 1` from the wrong writer, a
`42.068 s` signal delay, a worker that died silently on a database restart, and three rows deleted by a
migration whose only surviving witness was a sequence.
