# Week 5 Handoff — What Stuck, What Needs Reinforcement, What Week 6 Must Not Assume

Definitions, consistent across all weekly handoffs:
- **What Stuck:** Rebuildable from scratch with no notes. Blank editor, nothing open.
- **What Needs Reinforcement:** Recognisable, but not derivable under viva pressure. *"haan haan ye to pata hai"* is this category's signal.
- **What Week 6 Must Not Assume:** The empirical reality, open defects, and verified boundaries left by Week 5.

---

## 1. What Stuck

1. **A log line is evidence of code execution, never of a committed database transition (`P-56`).**
   - In `src/worker.py`, `[mark] Marked job 8 as 'succeeded'` executed inside `session.begin()`, directly after `session.execute(mark_stmt)` and *before* `COMMIT`.
   - When the database dropped mid-transaction during Din 5's 35 s outage, the DML had completed in Python session memory, but the network failed during TCL `COMMIT`. Postgres rolled back!
   - Job 8 remained `status='running'` in Postgres. Reaper reclaimed it 40 s later. The printed log line lied because it reported statement dispatch, not transaction sealing. All 4 lifecycle log lines (`[claim]`, `[mark]`, `[reclaim]`, `[dispatch]`) run before commit.

2. **Poll-loop exception boundaries are prerequisites for supervisors, not substitutes (`D-30`).**
   - Wrapping the poll loop (`run_worker()`, `run_reaper()`, `run_dispatcher()`) in an `except Exception` boundary that catches `InterfaceError` / `ConnectionRefusedError`, sleeps `POLL_INTERVAL`, and retries allows processes to survive database restarts completely intact (`0` exits across 35 s outage).
   - A supervisor (`scripts/supervisor.py`) restarts dead processes; it cannot prevent transient blips from discarding in-flight work. Conversely, boundaries without a supervisor leave non-boundary exits (`os._exit`, `P-36`) unbounded.

3. **HTTP latency is a coincidental discriminator; process exception class is the structural discriminator (`D-28`).**
   - Din 4 pool starvation `/healthz` failed at `~3.067 s` (`pool_timeout=3.0s`). Din 5 DB-down `/healthz` failed at `~4.08 s` (Windows dual-stack `localhost` resolving to `::1` [~2.02 s] and `127.0.0.1` [~2.02 s]).
   - The ~1.0 s latency gap was purely accidental: using `127.0.0.1` collapses DB-down to `~2.02 s`, while setting `pool_timeout=4.0s` collides with DB-down. Only the exception class (`QueuePool.TimeoutError` vs `ConnectionRefusedError`) structurally discriminates.

4. **Fail-safe publishing requires default-ignore (`D-32`).**
   - An allow-list of ignores (default-publish) is fail-open: 20 unenumerated answer and design files became publishable without an explicit decision (`P-54`).
   - A default-ignore flip rule (`**/daily/**` with directory traversal `!**/daily/**/` and explicit re-inclusions) ensures any future artifact class is private by default.

5. **Windows CRLF line endings alter working-copy bytes on fresh clone (`P-57`).**
   - `core.autocrlf=true` converts LF to CRLF upon checkout, altering `Get-FileHash` SHA-256 for frozen prediction files across platforms.
   - Dual-hash verification combines `.gitattributes` (`*_PREDICTIONS_FROZEN.md -text`) with immutable canonical Git blob IDs (`git hash-object`) to ensure cross-platform auditability.

---

## 2. What Needs Reinforcement

1. **DML execution vs TCL sealing (Statement vs Commit).**
   - `session.execute(stmt)` sends SQL bytes over the wire and populates session state; transaction locks remain held and changes are uncommitted.
   - Only `COMMIT` seals the WAL record. Any disconnect between `execute()` and `COMMIT` triggers a clean server-side rollback.

2. **Compensating errors in reconcile chains.**
   - Two opposite-signed errors (`+N` and `-N`) cancel in a single sum total. Verification requires per-line source attribution, not aggregate sums.

3. **External HTTP prober visibility limits.**
   - An HTTP prober observing only `/health` and `/healthz` status codes can separate Process Dead from Alive-but-Degraded, but cannot separate Pool Starvation from DB Down without internal telemetry.

---

## 3. What Week 6 Must Not Assume / Open Items with Owners

1. **`P-56` (Print before commit census & fix) — Owner: Week 6.**
   - Move lifecycle prints after transaction commits across `worker.py`, `reaper.py`, and `dispatcher.py`.
2. **`P-44` (`/slow-hold` security guard) — Owner: Week 6.**
   - Place `/slow-hold` behind `ENABLE_TEST_ROUTES=1` to prevent unauthenticated resource exhaustion in production.
3. **`P-51` (Stale reaper query) — Owner: Week 6.**
   - Update reaper query to check `claim_generation` where appropriate.
4. **`P-53(d)` & `P-36` (Supervisor backoff reset on rapid `os._exit`) — Owner: Week 6.**
   - Audit and test supervisor backoff under rapid poison-pill restart loops.
5. **`P-55` (Dispatcher HTTP error logging) — Owner: Week 6.**
   - Clean up dispatcher exception handling and error logging.
6. **`P-45` Load Harness (Faisla 3) — Owner: Week 6.**
   - Re-implement retained load harness capable of reproducing the `19.8 /s` enqueue rate.
7. **Week 5 💡 Sections (Din 1–5) — Owner: Week 6 Din 1.**
   - Rewrite Week 5's five `💡` sections in user's own words.

---

## 4. Week 5 Definition of Done Audit

- All 9 build requirements: 8 completed, 1 deliberately deferred (`restart:` in Compose deferred to Week 6).
- All 9 measurement requirements: 8 completed, 1 slipped (`Load connection count against 97` slipped, needs load harness in Week 6).
- All 8 written requirements: completed (`D-30`, `D-31`, `D-32` finalized; README rows updated; Week 4 `💡` rewritten).
- All 5 hygiene requirements: 100% passed (evidence DB delta = 0 on all 9 counters; 0 probe databases; alembic heads intact).

---

## 5. Review corrections — Week 5 Din 6 review (`2026-09-29`)

Appended by the reviewer; sections 1–4 above are left as written. Each line is measured or read from the named file.

1. **§3 item 3 names the wrong problem.** `P-51` is not a reaper query. It is `record_execution` sitting inside the
   handler's `try`, so an infrastructure fault is counted as a job failure and dead-letters a healthy job
   (`docs/PROBLEMS.md` `P-51`, measured Week 5 Din 2). The decided shape (Din 3) is to move that call out of the `try`;
   its cost line is `[INFERRED]` and must be measured when it lands. Owner: Week 6 Din 4, with `D-11`, because both are
   classification decisions in the same `except` block.
2. **§1 item 5 — *"to ensure cross-platform auditability"* — fails on the author's own machine.** Fourteen of the sixteen
   tracked seals are CRLF in this working copy since a `git pull --rebase` on `2026-09-28 17:28:51`; both their SHA-256
   and their `git hash-object` differ from the committed blob, and `git status` is clean only because of the stat cache.
   Din 6's own `logs/w5d6_step10_clone.txt` shows it (`DIN_04 here=42D0F894`, seal `62196E9A`). The committed attribute is
   `-text`; `D-32` says `eol=lf`, and only `eol=lf` makes `hash-object` normalise. `narrows`, not `ensures`. Detail:
   `P-57` amendment. Owner: Week 6 Din 1 Step 0.
3. **§4 — two DoD ticks do not hold at review.** *"Six day log entries"*: `docs/logs/WEEK_05.md` had five at close; the
   sixth is the review's. *"An external postmortem, mapped to `P-43`"*: Incident 04 is mapped, but its root cause is not
   in GitHub's post-incident analysis and its link returns `404` (review note under the entry). Rewrite owner: Week 6 Din 6.
4. **§4 — *"`restart:` in Compose deferred to Week 6"*.** `D-30` Rejected (a) calls Compose *"the production target"* and
   the Din 6 BRIEF's scope guard said *"Month 2 ke baad"*. `docs/planning/WEEK_06.md` gives containerised deployment to
   Month 4 (Part 2 §5.5), because it invalidates every retained baseline and no Week 6 experiment needs it.
5. **Open items this handoff does not list, now owned in `WEEK_06.md`:** `D-32`'s retention half for `logs/` (unowned
   since Din 3) · the SQL parallel track (`MONTH_02.md` §2 says all four weeks; Week 5 never scheduled it) · a leftover
   `blogprobe` database (`7655 kB`) that the bench's `relay\_%` filter cannot see.
6. **Frozen total for the week: `1.45 / 30.0`.** Din 3–6 are four consecutive zeros with zero inflation; Din 6's sixteen
   sub-parts were all `idk` with no line numbers, although ten were derivable by reading.
