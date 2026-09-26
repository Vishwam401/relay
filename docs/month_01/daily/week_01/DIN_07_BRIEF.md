# DIN 7 — Week 1 review checkpoint: pay the one debt that Week 2 cannot start without

**Week 1 · Din 7 · Budget ~2h20m** · Plan: [`../planning/WEEK_01.md`](../../planning/WEEK_01.md) (Din 7 section)

> **How to use this file.** Part A + Part C are safe to paste to Gemini, along with
> [`GEMINI_RULES.md`](../../../daily/GEMINI_RULES.md) and the SHARED CONTEXT block from the week plan.
> **Part B is not.** `DIN_07_KEY.md` stays closed until each step's work has actually been done.
>
> **Order per step:** answer that step's Part B questions from your own head → do the work → run
> Part C → compare with your prediction and write your *own* explanation of any difference →
> *then* open that step's KEY section. `idk` is a legitimate answer and is recorded as one.

---

## Today in one line

Week 1's build is finished and both ADRs are written. **What is missing is the one thing nobody else can
produce for you: the Week 2 problem statement in your own words.** It has slipped three times — Din 5
Step 6, Din 6 Step 2, now here. Everything else today is secondary to Step 1 and Step 2.

The day has exactly one new measurement in it, and it closes the last `[INFERRED]` in `D-02`.

---

## ⚠️ Read this before Step 1 — a seal question, answer it honestly

`DIN_06_KEY.md` has a **STEP 2** section, and it contains full answers to today's Step 1 and Step 2.
Step 2 of Din 6 was never delivered, so that section should never have been opened.

**If you did open it, say so at the top of your dossier.** Nothing bad happens; the day just changes
shape. Writing answers you have already read produces recognition, and recording it as recall would put
a false result into the log — which is a worse outcome than a slipped step. If it was opened, Steps 1
and 2 become *"reconstruct it from the measurements without re-reading, then diff"*, and they get scored
as reconstruction rather than as derivation.

---

## Bench state as of right now `[MEASURED by reviewer, 2026-08-19, after Din 6 close]`

```
jobs: 78 rows — succeeded 63, failed 8, running 3, pending 4      max(id) = 78
  running = 41  (Din 4 lock probe — claim committed, handler NEVER entered, no execution row)
            63  (Din 5 kill -9, 3s into an 8s handler — execution row present)
            65  (Din 5 kill -9, 3s into an 8s handler — execution row present)
  pending = 75  (Din 6 Case A — type 'send_receipt', NOT in the worker's REGISTRY)
            76, 77, 78  (Din 6 Step 6 seeds — type 'sleep')
attempts = 0 on every row in the table

job_executions: 46 rows
jobs_id_seq.last_value = 79   ← against max(id) = 78. The next enqueue is id 80

worker processes: 0      connections to relay: 1 (psql)      idle in transaction: 0
```

**Three things to carry into today:**

1. **The sequence has its first gap.** A reviewer probe rolled back an `INSERT` and permanently consumed
   value 79 (`nextval` is non-transactional — `P-05`, `P-18`). Row counts are unaffected. Today's closing
   arithmetic must account for it or it will look like a lost row.
2. **Job 75 is armed.** It is `pending` with a type no handler exists for. **The moment any worker starts
   — including Step 3's — it gets claimed, marked `failed`, and no execution row is written.** Step 0
   decides what to do about that *before* Step 3 runs, on purpose.
3. **Jobs 41, 63, 65 are still Week 2's fixture. Do not clean them up and do not fix them.** Verified
   intact yesterday. Today you *use* them in Step 2; you do not touch them.

---

## What Din 6 changed about today

| | What changed |
|---|---|
| **`D-01` and `D-02` are written** | Both complete, every `Cost` line carrying a provenance tag, two believed claims deliberately absent (any throughput comparison between claim strategies, and *"`SKIP LOCKED` prevents duplicate execution"*). They were **reviewer-written**, which means the reasoning in them is currently recognisable to you rather than recallable — the same state `DECISIONS.md`'s Din 1 provenance warning describes. Steps 4–5 are the antidote |
| **`D-02` has exactly one `[INFERRED]` left** | Which half kept Din 5's 4 µs claims safe — `SKIP LOCKED` skipping, or the guard firing. Din 6 priced both halves but ran in `psql`, not in the worker, so it could not say which one fired. **Step 3 settles it in about fifteen minutes**, and either answer is publishable |
| **`rowcount = 0` finally exists** | Observed for the first time in the project, in `psql`. The **worker's** `rowcount == 0` branch is still unexecuted code, and Step 3 is the one run that could execute it |
| **The reaper's information problem is now fully documented and completely unanswered** | `P-16` names it, `P-17` shows that `jobs` cannot even record a duplicate claim, `D-01` Cost 1–3 prices it. Every input Step 1 needs exists. Nothing has been written |
| **DDIA: stop looking for `P-16` in Ch 7** | It is **Ch 8**. What Ch 7 *does* contain is the name for Din 6's variant-1 failure. Step 7 is narrowed accordingly |

---

# PART A — Steps

Ten steps. Two end in something executable; the rest end in something written and checkable. If a step
passes ~15 minutes, it is too big — split it.

**No changes to `src/` today.** Part D lists what that protects.

---

## Step 0 — Bench close, and decide about job 75 (10 min)

**Terms used in this step**

| Term | What it is |
|---|---|
| Fixture | A deliberately-preserved database state that a future test will be measured against |
| Reconciliation | Proving the closing row counts equal the opening counts plus everything you did |
| Sequence gap | A consumed `nextval` with no committed row behind it |

**Do:**
1. Run C0. Confirm the numbers above, including `last_value = 79`.
2. **Decide about job 75, and write the decision down with its reason.** Three options, all defensible,
   and the point is that you pick one *deliberately* rather than discovering it:
   - **Leave it.** Step 3's workers will convert it: `pending 4 → 3`, `failed 8 → 9`, no execution row,
     and a **fourth** fixture shape now exists.
   - **Delete it.** Bench stays clean; the Din 6 Case A reconciliation no longer closes against the log.
   - **Retype it** to `sleep`. It executes normally; the log's record of Case A becomes inaccurate.
3. Write one line naming which Week 2 test the fourth shape would help or hurt.

**Runnable end state:** C0's numbers recorded, and a written decision with a reason and a consequence.

---

## Step 1 — Week 2's problem statement, part 1: the predicate and the column (15 min)

> **This is the most important step of the week.** Three lines maximum per answer, your own words. If the
> honest answer is `idk`, write `idk` — it scores as not-answered, which is accurate, and it marks
> exactly what Week 2 then teaches.

**Terms used in this step**

| Term | What it is |
|---|---|
| Reaper | A process that finds jobs stuck in `running` and returns them to a claimable state |
| Predicate | The `WHERE` clause — the condition a row must satisfy |
| Lease | A time-bounded claim: the holder owns the job until a deadline, after which others may take it |
| Heartbeat | A periodic "still alive" write by the holder, extending its lease |

**Do:**
1. **Write the reaper's decision rule as a single SQL predicate, using ONLY columns that exist in `jobs`
   today.** Look at `src/models.py` if you need the column list — that is a fact, not an outcome.
2. **Then state why it does not work.** Be specific about *which quantity* it is actually measuring
   versus the quantity you wanted. And say whether it fails in the safe direction or the dangerous one.
3. **Name the smallest schema addition that makes it work** — one column, its type, its nullability, and
   which statement writes it.
4. **Then name the new failure that addition introduces.** State it as a certainty, not a risk. If your
   answer contains the word "might", you have not finished the sentence.

**Runnable end state:** one SQL predicate, one sentence on what it actually measures, one column
definition, and one named failure.

---

## Step 2 — Week 2's problem statement, part 2: 41 vs 63, and the short lease (15 min)

**Do:**
1. **Look at jobs 41 and 63 in the bench block. Which is more dangerous to reset, and why?** Then: does
   your answer change if Relay's handlers were idempotent?
2. **Write one line on why a reaper that handles 63 correctly might still get 41 wrong.** Look at what
   distinguishes them in the bench block, then think about what a reaper would naturally key on.
3. **`P-15` says there is no handler timeout. If you add a lease shorter than the slowest handler, what
   have you built — on purpose?** One sentence, and use the strongest available verb.
4. **Then the sentence Week 2 starts from.** One sentence, stating the interim guarantee Relay actually
   offers once the reaper exists but before Week 3's dedup does. It should be uncomfortable to write.

**Runnable end state:** four short answers, and one sentence you would be willing to put in a design doc.

---

## Step 3 — Close `D-02`'s last `[INFERRED]`: which half made the convoy safe (15 min)

`D-02` can say the claim path is safe at 4 µs separation `[MEASURED]`. It cannot say **which half** made
it safe. `SKIP LOCKED` steering the second worker to a free row, and the compare-and-set guard returning
`rowcount = 0`, are both consistent with every measurement this project has. `P-17` states what settles
it, and it costs one run.

**Terms used in this step**

| Term | What it is |
|---|---|
| Convoy | Workers that start together and run equal-duration handlers, so they finish and re-poll together |
| `-u` | Python's unbuffered-stdout flag |
| `Tee-Object` | PowerShell: write a stream to a file **and** to the terminal |

**Do — two terminals, exact commands in C3:**
1. Seed 8 `slow` jobs. Record the ids.
2. Start **two** workers, one per terminal, each piping through `Tee-Object` to its own log file.
   **Use `-u`.** C3 explains what happens if you do not.
3. Let the queue drain fully (≈ 32 s at 8 s per handler, 2 workers, 4 rounds each). Then `Ctrl+C` both.
4. **Grep both logs for the conflict line.** Count occurrences.
5. Read the claim timestamps out of `job_executions` and check whether the convoy re-formed.
6. Delete both log files. Say so in the dossier.

**Runnable end state:** a conflict-line count, a per-worker job split, and the round-by-round claim
timestamps. One number decides a sentence in `D-02`.

---

## Step 4 — Week 0's five questions, cold (15 min)

**Do:** no notes, no files open, your own words, written down.

1. `kill -9` pe kya kho sakta hai, aur kyu?
2. Read Committed me mera code silently galat kaise ho sakta hai?
3. Pool exhaustion "DB slow" se kaise alag dikhta hai?
4. Connect timeout aur read timeout alag kyu hain?
5. `time.sleep` async app me kyu ghatak hai?

Then, and this is the part that matters: **for each one, mark whether you derived it or recalled a
sentence.** A remembered phrase that you cannot unpack is not an answer.

**Runnable end state:** five written answers, each tagged *derived* or *recalled*. Anything you cannot
answer gets 30 minutes later in the week — write which.

---

## Step 5 — Day 5's weak-point retest, and Din 6's two new corrections (15 min)

Day 5's quiz scored 2.5/10 and the same pattern appeared on Day 4. These are the items that were flagged
for consolidation. **In your own words, now:**

**Corrections:**
1. Read Committed kya rokta hai, kya nahi?
2. `FOR UPDATE` vs `SERIALIZABLE` — kaunsa block karta hai, kaunsa error deta hai?
3. `REPEATABLE READ` read locks leta hai ya nahi?
4. `idle in transaction` default me kill hota hai?

**Untouched concepts:**
5. "Pivot" ka matlab aur retry obligation
6. `FOR UPDATE` vs `SERIALIZABLE` ka mechanism + cost
7. Phantom kya hai, aur `FOR UPDATE` kab lock nahi laga sakta
8. Unique constraint username pe kaam karta hai, doctors pe nahi — kyu
9. Do-worker scenario: mechanism vs consequence, aur do-layer defence

**Plus two from Din 6, which you now have measurements for:**
10. `EvalPlanQual` kya recheck karta hai — aur Din 4 aur Din 6 me ulta result kyu aaya?
11. Relay ke claim ke do halves — kaunsa liveness deta hai, kaunsa safety, aur ek nikaal do toh kya tootta hai?

**Runnable end state:** eleven written answers with a self-assessed count. Items 9, 10 and 11 are the
same mechanism from three directions; if one of them is solid and the others are not, say which.

---

## Step 6 — `POSTMORTEMS.md`: entries #2 and #3 (15 min)

One entry exists. Week 0's DoD wanted 2, Week 1's wants 3. This has been open since the week it was
written, which makes it the longest-running open item in the project.

**Do:**
1. Read one [Cloudflare postmortem](https://blog.cloudflare.com/tag/post-mortem/). Write entry #2.
2. Write entry #3 from anywhere — a public incident, or one of your own (`P-06` is a real incident with a
   real blast radius and a real resolution; it would make a legitimate entry).
3. For each, the useful shape is not a summary. It is: **what did they believe was protecting them, and
   what was that protection actually covering?** That is the `P-04` question, and it is why these are
   worth reading at all.

**Runnable end state:** two entries, each ending in one sentence connecting the incident to a specific
Relay decision or problem number.

---

## Step 7 — DDIA Ch 7, pp. 233–251 — fifth attempt, narrowed (15 min)

This has slipped four times, which is a signal that the target was wrong rather than that the reading is
hard. So it is narrowed to three things, and one of them you have now produced yourself.

**Do:**
1. Find **lost update** and its listed remedies. Then write one line: *which remedy is `D-06`'s guard,
   and which Din 6 variant is the textbook example of the failure?*
2. Find **write skew and phantoms**, and why row-level locks cannot catch them. This has failed twice in
   your self-checks (Week 0 Day 5 Q4, then Q2b) and is the highest-priority consolidation item. One line
   on what makes it structurally different from a lost update.
3. Find **SSI / `SERIALIZABLE`** presented as abort-and-retry rather than blocking. One line on why that
   is the wrong shape for a claim that is contended by design.
4. **Then stop.** `P-15` and `P-16` — the dead-versus-slow problem — are **Ch 8**, not Ch 7. Write that
   down as the next chapter and do not go looking for it today.

**Runnable end state:** three one-line connections between the chapter and a specific `D-` or `P-` entry,
and Ch 8 named as the next target.

---

## Step 8 — Definition of Done, honestly, and the Week 2 handoff list (15 min)

**Do:**
1. Open the Week 1 DoD in `planning/WEEK_01.md`. The Din 6 log contains a **reviewer audit** of it. Tick
   it yourself first, then compare — **where you disagree is the interesting part**, and it goes in the
   dossier either way.
2. **For every unticked item write one line:** *deliberately deferred* (with the owner — which week, which
   `D-`/`P-` number) or *slipped* (with what it specifically needs). Those are different states and
   collapsing them is how a deferred decision quietly becomes a forgotten one.
3. **Then the handoff list, which is the actual output of a checkpoint day.** Three headings, and be
   concrete:
   - **What stuck** — what you could rebuild from scratch without notes
   - **What did not** — what you can recognise but not derive
   - **What Week 2 must not assume you know**

**Runnable end state:** a ticked DoD with a reason on every gap, a written disagreement list, and three
short lists that Week 2's plan will be built from.

---

## Step 9 — Commit, and close the bench (10 min)

**Do:**
1. Run C9. Confirm 0 workers, 0 `idle in transaction`, and that `running` is **still exactly 3**.
2. Reconcile the arithmetic, including Step 0's job-75 decision and Step 3's 8 seeded jobs.
3. Commit `docs/DECISIONS.md`, `docs/logs/WEEK_01.md`, `docs/PROBLEMS.md`, `docs/LEARNING_LOG.md` and
   `docs/POSTMORTEMS.md` with a real message. **Stage those paths explicitly, not `.`.**

> **`docs/daily/`, `docs/roadmap/` and `docs/planning/` are in `.gitignore` on purpose** `[MEASURED]`, so
> the BRIEF, the KEY and `CURRENT_WEEK.md` are **not** committed and will not appear in `git status`. That
> is a deliberate choice already made, not an oversight — but it has a consequence worth knowing on a
> checkpoint day: **the pointer that tells a cold reader where the project is has no history and no
> backup.** If `CURRENT_WEEK.md` is lost, it is reconstructed from the log rather than from git. Decide in
> Step 8 whether that is still the trade you want; `*.log` being ignored is also why Step 3's two capture
> files cannot accidentally be committed.

**Runnable end state:** a reconciled bench, and Week 1's tracked documentation committed.

---

# PART B — Prediction questions

> ⛔ **DO NOT PASTE THIS SECTION TO GEMINI. DO NOT OPEN THE KEY TO ANSWER IT.**
>
> Answer each step's questions **before** doing that step, from your own head, in writing.
> Vocabulary questions are fine to ask Gemini — the glossaries in Part A exist for that. If the answer
> to your question would also answer one of these, do not ask it.
>
> **Din 5 and Din 6 are both unscored because the predictions were never handed over. Four of six days
> now have no score.** The score exists to track concept formation, which is the weak half of this week.
> Write these somewhere you will actually paste back.

```
STEP 0 — the bench
0.1  Which of the three job-75 options do you expect to regret least in Week 2? Commit to one
     before reading the consequences you wrote in Step 0.3.
0.2  jobs has 78 rows and the sequence is at 79. Is that recoverable — can the sequence be put
     back? Should it be? Answer before looking anything up.

STEP 1-2 — Week 2's problem statement
1.1  Before you write anything: does any column in jobs today record when EXECUTION began?
     Yes or no. This is a fact you can check in models.py, so check it.
1.2  Predict how many new columns your Step 1 answer will need: none, one, or more than one.
     Write the number now, then compare with what you actually write.
1.3  Predict which kind of evidence your "dead or slow?" answer ends up resting on --
     a timestamp, a heartbeat, or a token. Name one before you reason it out.
2.1  Predict whether your Step 2.4 sentence (the interim guarantee) will be one Relay can ship
     with, or one that blocks the reaper until Week 3. Answer before you write it.

STEP 3 — the convoy
3.1  Predict the conflict-line count across both logs. Then -- and this is the more important
     half -- write down what a count of 0 would prove, and what a count of 3 would prove.
     If both counts would support the same conclusion, your prediction is not a prediction.
3.2  Two workers started from one command, 8 identical 8-second handlers. Predict whether the
     convoy re-forms, and predict the claim separation per round: milliseconds, microseconds,
     or unpredictable?
3.3  If the grep returns 0 conflicts, name a WRONG setup that would also return 0. Then name
     the check in C3 that distinguishes it. (This is the P-18 discipline, applied live.)
3.4  Predict which worker claims job 75, and what it prints. Then predict the four bench
     numbers after the run.

STEP 4-5 — the retests
4.1  Before answering: predict your own score out of 5 on Step 4, and out of 11 on Step 5.
     Write both numbers. Your documented failure pattern is claiming 3/3 on questions you had
     not derived, so the calibration error matters as much as the score.
5.1  Of items 9, 10 and 11 -- the same mechanism from three directions -- predict which ONE
     you will answer best. Then check whether being right about that is good news.

STEP 7-8 — reading and the audit
7.1  Predict whether Ch 7 names the remedy D-06 already uses, without going and looking.
8.1  The Din 6 log contains a reviewer audit of the DoD. Predict how many items you will
     DISAGREE with -- not how many are ticked. Then find them.
8.2  Predict which single item on your "what did not stick" list Week 2 will be most damaged by.
```

---

# PART C — Verification

Every check is written to **distinguish** a correct result from a plausible wrong one. `P-18` was written
yesterday because one Din 6 check could not do that, so each table below states the output when the
mechanism is **present** and when it is **absent**. If those two lines ever match, the check is decorative
and needs rewriting before it ships.

Environment: PowerShell, repo root, `.venv` active. Statement separator is `;`, never `&&`.
Step 3 needs **two** terminals.

> **Clock trap.** The database session's `TimeZone` is `Etc/UTC` `[MEASURED]`; the worker's `echo=True`
> output is local (IST, +5:30). Either convert with `executed_at AT TIME ZONE 'Asia/Kolkata'` or stay
> inside one clock per calculation, and write down which clock each number is in.

---

### C0 — Baseline (3 min)

```powershell
Get-CimInstance -ClassName Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*src.worker*' } | Select-Object ProcessId, CreationDate
docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT count(*) AS total, max(id) FROM jobs;" -c "SELECT last_value, is_called FROM jobs_id_seq;" -c "SELECT count(*) FROM job_executions;" -c "SELECT id, type, status FROM jobs WHERE status='pending' ORDER BY id;" -c "SELECT count(*) AS conns, count(*) FILTER (WHERE state LIKE 'idle in transaction%') AS idle_in_txn FROM pg_stat_activity WHERE datname='relay';"
```

Expected `[MEASURED 2026-08-19]`: **0** workers, **1** connection, **0** `idle in transaction`,
`running = 3`, `pending = 4` (75, 76, 77, 78), `total = 78`, `max(id) = 78`,
**`last_value = 79`**, 46 execution rows.

| Check | Mechanism present | Mechanism absent |
|---|---|---|
| The sequence gap is real | `last_value = 79` while `max(id) = 78` | `last_value = 78` — meaning the probe was misreported |
| No worker is running before Step 3 | empty process list | one or more PIDs, and Step 3's split is already contaminated (`P-13`) |
| No session left mid-transaction | `idle_in_txn = 0` | `≥ 1`, and this instance has `idle_in_transaction_session_timeout = 0`, i.e. unlimited (`P-06`) |

---

### C3 — The convoy, with stdout captured (Step 3)

**Seed**, in the repo shell:

```powershell
docker compose exec -T db psql -U postgres -d relay -c "INSERT INTO jobs (type) VALUES ('slow'),('slow'),('slow'),('slow'),('slow'),('slow'),('slow'),('slow') RETURNING id;"
docker compose exec -T db psql -U postgres -d relay -c "SELECT max(id) FROM job_executions;"
```

Record both — the `job_executions` high-water mark is what makes the after-count unambiguous.

**Terminal 1:**

```powershell
.venv\Scripts\python.exe -u -m src.worker 2>&1 | Tee-Object -FilePath labs\w1.log
```

**Terminal 2**, started immediately after:

```powershell
.venv\Scripts\python.exe -u -m src.worker 2>&1 | Tee-Object -FilePath labs\w2.log
```

> **`-u` is not optional.** Without it Python buffers stdout when it is not writing to a terminal, and
> the pipe into `Tee-Object` is not a terminal. The KEY explains what you would lose; the short version
> is that a run without `-u` can produce a log file that is missing the exact line this experiment
> exists to count, which would look identical to a genuine zero.

Let it drain (≈ 32 s), then `Ctrl+C` **both**. Then:

```powershell
Select-String -Path labs\w1.log, labs\w2.log -Pattern 'Conflict' | Select-Object Filename, LineNumber, Line
(Select-String -Path labs\w1.log, labs\w2.log -Pattern 'Conflict').Count
(Select-String -Path labs\w1.log, labs\w2.log -Pattern 'Claimed job').Count
Select-String -Path labs\w1.log, labs\w2.log -Pattern 'Unknown job type'
docker compose exec -T db psql -U postgres -d relay -c "SELECT worker_id, count(*), min(executed_at), max(executed_at) FROM job_executions WHERE id > <the recorded max> GROUP BY worker_id ORDER BY worker_id;" -c "SELECT job_id, worker_id, executed_at FROM job_executions WHERE id > <the recorded max> ORDER BY executed_at;"
```

| Check | Mechanism present | Mechanism absent |
|---|---|---|
| **Both workers actually competed** | two distinct `worker_id`s, roughly even split | one `worker_id`, or a 7/1 split — then a 0 conflict count proves **nothing**, and this is the wrong setup 3.3 asks you to name |
| **The convoy re-formed** | claim timestamps pairing up round by round, separation in µs or low ms | claims spread evenly across 32 s — contention never happened, same failure as `P-12` |
| **The guard's branch fired, or did not** | a `Conflict:` line with `rowcount=0` | no such line **in a log that is otherwise complete** — check `Claimed job` count is 8 first |
| **The log is complete** | `Claimed job` count = 8 (or 9 with job 75) | fewer — output was buffered and lost. Re-run with `-u`. **A truncated log and a genuine zero look the same** |
| **Job 75 behaved as predicted** | one `Unknown job type` line, `failed`, no execution row | no line ⇒ job 75 was deleted or retyped in Step 0; say which |

**Cleanup:**

```powershell
Remove-Item labs\w1.log, labs\w2.log
```

The 8 seeded jobs end `succeeded` and hold execution rows. **Leave them** — deleting them would orphan
execution rows and break the reconciliation, which is the precedent set by jobs 55–58 and 74.

> **Do not** reset or delete jobs 41, 63 or 65. They are Week 2's fixture.

---

### C9 — Close the bench (3 min)

```powershell
Get-CimInstance -ClassName Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*src.worker*' } | Select-Object ProcessId
docker compose exec -T db psql -U postgres -d relay -c "SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status;" -c "SELECT count(*) AS total, max(id) FROM jobs;" -c "SELECT count(*) FROM job_executions;" -c "SELECT count(*) AS conns, count(*) FILTER (WHERE state LIKE 'idle in transaction%') AS idle_in_txn FROM pg_stat_activity WHERE datname='relay';"
git status --short
Get-ChildItem labs\*.log -ErrorAction SilentlyContinue
```

`git status` will list **only** the five tracked `docs/` files. It will **not** list this BRIEF, the KEY,
or `CURRENT_WEEK.md` — see Step 9's note. The `labs\*.log` check should return nothing; if it lists files,
Step 3's cleanup was skipped (they are gitignored, so git will not remind you).

Required: **0** workers, **0** `idle in transaction`, and **`running` still exactly 3**.

Arithmetic, starting from 78 rows and `last_value = 79`:

```
jobs_after        = 78 + 8 (Step 3 seeds)  ± Step 0's job-75 decision
first seeded id   = 80          ← not 79. The gap is real
execs_after       = 46 + 8      ← job 75 adds NONE if it was left in place
```

| Check | Mechanism present | Mechanism absent |
|---|---|---|
| Nothing was stranded | `running = 3` | `≥ 4` — a Step 3 worker was killed mid-handler, or a `psql` session was left open |
| Job 75's transition is understood | `failed` count moved by exactly 1 with **no** new execution row | a new execution row appeared ⇒ your model of the unknown-handler path is wrong; go read `run_worker()` |
| Execution rows reconcile | `execs_after − 46 = ` the number of handlers actually entered | any mismatch is either a duplicate or a missing dispatch — both are findings, neither is noise |

---

# PART D — Scope guard

**Not today. Each one has an owner.**

| Tempting | Owner | What you lose by doing it today |
|---|---|---|
| Writing the reaper | **Week 2, Din 1** | Steps 1–2 turn the stuck job into a written problem statement. Build the fix first and the statement is never made — this is the fourth time this guard has been needed |
| Adding `claimed_at` / `lease_expires_at` / `locked_by` | Week 2 | Step 1's whole value is naming which column is missing **and what adding it breaks**. Adding it skips the second half |
| Deciding `D-22` (completion evidence as a row) | Week 2 | It needs the reaper's requirements to price. Din 6 added a reason to think it may be ordered *earlier* than assumed — note that, do not decide it |
| Changing the claim query, or the `rowcount = 0` branch's sleep | Week 4 / Din 4 settled the claim | `D-02` Cost 5 is a recorded cost. Fixing it today makes Step 3's run non-comparable with Din 5's |
| Fixing jobs 41 / 63 / 65 | Week 2 | They are the fixture, and `P-16` needs all three because 41 is a different shape |
| A handler timeout | Week 2 shutdown hardening | `P-15` shows the lease and the timeout are **one** decision. Bundling them now hides that |
| Writing Week 2's plan | **Mentor, from Step 8's handoff list** | Step 8's three lists are the input. Writing the plan yourself skips the checkpoint's only purpose |
| Retry / `attempts` / DLQ | Week 2 | `attempts = 0` on every row in the table is a finding, not a bug |
| Resetting the sequence to close the gap | Nobody — the gap is correct | It is evidence for `P-05`. Removing it destroys a measurement to make a number look tidy |
| An index on the claim query | Week 4 (`P-03`) | Today's `Seq Scan` at 78 rows says nothing about depth. Guessing now freezes an assumption you cannot later isolate |

**One measurement, ten written answers, two postmortems, a reconciled bench, and zero lines changed in
`src/`.**
