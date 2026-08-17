# DECISIONS.md — Architecture Decision Records (ADR)

Format for each entry:
```markdown
## D-NN: <decision in one line>
Problem:  What problem am I solving?
Options:  (a) ... (b) ... (c) ...
Chose:    Which option and why?
Cost:     What is the trade-off or downside of this choice?
Rejected: (x) because <concrete reason, ideally measured>
```

---
## Reserved numbers

`D-01` and `D-02` are deliberately left open — they are scheduled for Week 1, Din 6:

- **D-01:** Postgres as queue vs Redis vs RabbitMQ *(needs Din 3's polling loop and Din 4's throughput numbers to fill the Cost field)*
- **D-02:** `FOR UPDATE SKIP LOCKED` vs `SERIALIZABLE` for worker claim *(needs Din 4's measured duplicate-execution and total-time comparison)*

Both depend on measurements that do not exist yet. Writing them now would mean guessing the Cost field.

**Raw material collected so far — `D-01`'s Cost field** (Din 3, `[MEASURED]`, one idle worker, `POLL_INTERVAL_SECONDS = 2.0`, this machine):

- The idle poll is **a transaction per poll**, not a bare `SELECT`: `BEGIN` → `SELECT … FOR UPDATE` → `COMMIT` in the SQL echo, repeating forever. That is **0.5 tx/s per idle worker** at a 2 s interval, each one a `Seq Scan`. The statement is reported `cached`, so it is not re-planned; the poll is read-only, so it writes no WAL.
- Load scales with **worker count × 1/interval**, not with job count — an idle fleet is not free.
- The interval simultaneously bounds **enqueue-to-start latency** and, because the loop sleeps it in a single `await`, **shutdown latency**. Full write-up: `P-10`.
- Still missing before `D-01` can be written: Din 4's throughput comparison, and the claim query's behaviour at a queue depth where `Seq Scan` stops being appropriate (`P-03`, Week 4).

**Raw material collected on Din 4 — and one gap that got bigger, not smaller.**

`D-01`'s Cost field gains one measured number: an idle fleet's cost is **3 idle Postgres connections and ~2 tx/s for zero work**, measured on four forgotten workers (`P-13`, log `M9`; connections to `relay` dropped 4 → 1 when they were killed). That is the same claim Din 3 made per-worker, now observed at fleet scale by accident.

`D-02`'s Cost field is **still not writable**, and Din 4 is the reason it looked writable when it was not. What Din 4 gives it:

- **Measured, and it is the useful half:** `SKIP LOCKED` does not prevent duplicate execution — `FOR UPDATE` plus the compare-and-set guard already did that, including two workers claiming different rows **6 ms apart** with no duplicate. What `SKIP LOCKED` removes is a worker sitting in `Lock`/`transactionid` in front of a row someone else holds: with a 6 s lock held on the oldest pending row, the `skip_locked` worker started real work **1.25 s in**, while the plain `FOR UPDATE` worker had waited the full 6 s. Cost: the skipped row is deferred to a later poll, so best-effort FIFO (`P-05`) gets more approximate.
- **Not measured, and previously believed measured:** the throughput comparison. Both of Din 4's "two worker" runs had a staggered second worker (10 s late, then 23 s late), so the 7/3 and 8/2 splits and the elapsed times are start-time artifacts, not strategy results (`P-12`). One clean run with a **proven overlap window** is still owed before `D-02` can state a Cost.
- `SERIALIZABLE` was never run, so the third option in `D-02`'s title has no data at all.

**Numbering note, so the next collision does not happen:** `D-09`..`D-20` are already claimed by `roadmap/BACKEND_ROADMAP_PART2.md` (Months 2–4), and `D-01`/`D-02` are reserved above. New Week 1 decisions therefore continue from **`D-21`**.

---

# Schema decisions (Week 1, Din 1)

> **Provenance — read this before trusting the reasoning below.**
>
> These six decisions were **explained to me**, not derived by me. I read the trade-offs for the first time on Din 1 and understood roughly 60% on first pass. The conclusions are recorded here because the schema had to be built, but the *reasoning* is currently **recognisable to me, not recallable**.
>
> **Measurement status:** most of the reasoning below is documentation-based **inference** about PostgreSQL 16 behaviour. Two specific claims were subsequently **verified on this instance** and are marked `[MEASURED]` with their actual output — the enum-in-transaction restriction (D-06) and the `ADD COLUMN ... DEFAULT` rewrite question (D-07). Both verifications *contradicted the reason originally given for the choice* without changing the choice itself; that is recorded in place rather than quietly corrected.
>
> Everything not marked `[MEASURED]` is inference. Notably, the `ACCESS EXCLUSIVE` lock-queue hazard in D-07 is **not** measured.
>
> Weekend consolidation must re-test these without context. Whatever survives that is mine; the rest is still borrowed.

---

## D-03: `jobs.id` is a DB-generated `bigint` identity column, not a client-supplied UUID

**Problem:** Every row needs a unique identity. The choice also silently decides *who* is allowed to mint that identity — Relay, or its caller — and that has consequences well beyond this column.

**Options:**
- (a) `bigint GENERATED BY DEFAULT AS IDENTITY` — DB-generated sequence
- (b) `bigserial` — same mechanism, legacy Postgres syntax
- (c) `UUID` v4 — random, client-generatable
- (d) `UUID` v7 — timestamp-prefixed, client-generatable, index-friendly

**Chose:** (a).

The tempting argument for a client-supplied UUID was duplicate suppression: if a `POST /jobs` response is lost and the client retries with the same id, the primary key conflict blocks the duplicate. This is technically true and was the strongest case for (c)/(d).

It was rejected because **a primary key and an idempotency key are different concerns**, and merging them creates three problems:

1. **Storage identity would depend on caller input.** A buggy client reusing one id would have its genuinely-new jobs silently rejected. That is silent data loss, which violates contract #1.
2. **Idempotency needs a time window; a primary key has none.** If Week 4 adds cleanup of old rows, a client replaying the same id six months later would find no conflict and the job would execute again.
3. **Dedup should be opt-in.** Two logically distinct jobs may legitimately carry identical payloads. A PK-based scheme removes that choice from the caller.

The correct shape is two columns: `id` stays internal and DB-owned; Week 3 adds a separate nullable `idempotency_key text UNIQUE` supplied by the caller. This also matches what the Week 0 Day 5 log already anticipated (*"idempotency key + unique constraint"*).

Once that argument is settled, no remaining UUID benefit is consumed by Relay this month:
- Client-side generation → not needed (idempotency lives in its own column)
- Unguessable ids → **there is no auth in Week 1**, so an unguessable id is obscurity, not security. The real fix is authorization, not id format.
- Distributed generation → single Postgres, no sharding, no multi-master

And one practical factor that genuinely matters for this project: Din 4 and Din 5 are entirely `psql`-driven failure injection. Copying `42` versus `550e8400-e29b-41d4-a716-446655440000` dozens of times across two days of experiments directly affects how fast the experiments run — and the experiments are the point of the project.

Chose (a) over (b) because `GENERATED ... AS IDENTITY` is SQL-standard (PG 10+) and handles sequence ownership cleanly. **If SQLAlchemy/Alembic setup creates friction, `bigserial` is an acceptable substitute** — the practical difference is close to zero and this must not become a Din 1 blocker.

**Cost:**
1. **Ordering is not guaranteed.** `nextval` is non-transactional, so ids have gaps after rollbacks, and more importantly **id order is not commit order**: a transaction that took `id = 5` first can commit *after* one that took `id = 6`. So `ORDER BY id` is an approximation of "oldest job", not a guarantee. Accepted knowingly — FIFO fairness is not one of Relay's five contract promises. Tracked as `P-05`.
2. **The door to client-generated ids is closed** for as long as `id` is the only identity column. Reopening it means a table rewrite. Acceptable now because Month 1 has no production data, so the reversal cost is currently low.
3. Ids leak approximate job volume to anyone who can read them. Irrelevant while the only user is the developer; would need revisiting alongside auth.

**Rejected:**
- **(b) `bigserial`** — functionally equivalent, but legacy syntax with messier sequence ownership. Kept as a fallback, not a preference.
- **(c) UUID v4** — 16 bytes instead of 8, and random values insert into the middle of the B-tree index, causing page splits and poor cache locality. Pays a write cost for benefits Relay does not use.
- **(d) UUID v7** — strictly better than v4 when time-ordering is acceptable (timestamp prefix keeps inserts at the index's right edge). Rejected only because the client-generation requirement itself was rejected. Also **not built into PG 16** — [`uuidv7()` arrived in PostgreSQL 18](https://www.postgresql.org/docs/current/release-18.html) — so it would need app-side generation. Note that its timestamp prefix leaks creation time, which is a reason to prefer v4 if that ever matters.

**Revisit when:** Relay needs multi-region or multi-database id generation, or a client genuinely needs the id before the DB round-trip.

---

## D-04: `jobs.type` is unconstrained `text`; validation lives in the application, not the database

**Problem:** `type` selects which handler executes the job. Should the database enforce that the value is one of a known set?

**Options:**
- (a) `text NOT NULL`, no DB constraint
- (b) `text` + `CHECK (type IN (...))`
- (c) native `ENUM`
- (d) `text` + lookup table + foreign key

**Chose:** (a).

**The decisive reason: the database cannot express the invariant I actually care about.** The real rule is not *"type is a valid string"* — it is **"a handler function for this type is registered in the worker."** Postgres has no knowledge of the worker's handler registry.

So a `CHECK` constraint would accept `'send_email'`, and if no `send_email` handler exists, the job still enters the DB, is still claimed, and still fails at execution. The constraint prevents nothing and supplies **false confidence** — which is worse than no constraint, because I would start trusting it. Generalised as `P-04`.

This is the Week 0 Day 5 lesson recurring. From that log: *"Exp 2 = the rule was never in the database at all."* The doctors' on-call rule lived in an application `if`, so Postgres had nothing to object to. Same shape here.

**Second reason: the cost of a bad value is bounded and visible.** A typo (`'send_emial'`) produces: job accepted → handler lookup fails → exception → `failed` → Week 2 retry → attempts exhausted → **DLQ**. That is contract #4 working as designed (*"terminal failures enter a DLQ, not silence"*). No corruption, no silent wrongness, no other job affected.

This is the sharp contrast with `status` (D-06): a bad `status` value makes a row **invisible** to `WHERE status = 'pending'`, which is silent. A bad `type` value produces a loud, contained failure. **The constraint decision follows the failure mode, not a general preference for strictness.**

**Third reason: change frequency.** Adding job types is the single most frequent change in a job queue's lifetime. Putting migration friction on the most-changed axis is backwards. General heuristic: *whatever changes most often should be cheapest to change.*

**Reversal is cheap**, which is what makes (a) safe: going from `text` to `text + CHECK` is one DDL statement with no rewrite, and back again is equally cheap. When reversal is cheap, prefer the option that does not block you and tighten only once real pain appears.

**Cost:**
1. **Typos reach the database.** Garbage job types will accumulate as DLQ entries. Accepted because they are visible and contained.
2. **No single place lists the valid types.** The authoritative set lives in the worker's handler registry, which means the DB alone cannot answer "what job types exist?"
3. `text` is unbounded, so a malformed client could store a very large `type` string. A `CHECK (length(type) <= 100)` bound is cheap and defensible; **not applied yet** — treated as optional hardening, not correctness.

**Rejected:**
- **(c) `ENUM`** — worst of both: requires a migration for the most frequently changing value set, *and* still does not enforce the real invariant. Appropriate for genuinely closed domain sets (weekdays, compass directions), which job types are not.
- **(b) `text + CHECK`** — same objection as (c) with easier migrations. Reconsider only if unbounded typos become a measured operational problem.
- **(d) lookup table + FK** — adds a table and a per-write FK check for a set that will change constantly, and still cannot see the handler registry. Becomes genuinely attractive only when per-type *metadata* is needed (per-type timeout, retry policy, enabled flag) — at which point validation is a free side effect rather than the goal.

**Revisit when:** Week 4 needs per-type configuration. Then (d) arrives naturally and brings validation with it.

**Amendment — Din 3, the bill for this decision arrived, and it was cheaper than the Cost section predicted.** Din 3 built the handler registry, so the invariant this entry said the database could not see now exists somewhere concrete. An unregistered type was enqueued and the worker's behaviour was **measured**: job `23`, `type = 'does_not_exist'` → claimed once, marked `failed` once, then the worker went back to polling. No hot loop, no crash, no other job affected.

Cost #1 above ("typos reach the database … visible and contained") is therefore confirmed rather than assumed. Two refinements the original entry did not state:

1. **The chosen handling — claim it, then mark `failed` — consumes the claim.** That is deliberate (the alternative, leaving it claimable, means writing `running → pending`, which is Week 2's reaper's transition, and it re-encounters the row every poll). The cost is specific: a **deployment ordering mistake**, where the worker rolls out before its handler is registered, becomes permanent for those rows rather than self-healing. With Week 2's retries it will burn every attempt and land in the DLQ for a reason that has nothing to do with the job.
2. **So the mitigation is operational, not schema-level:** deploy handler registration before, or with, the workers that consume the type. Nothing in the database can enforce that ordering — which is the same conclusion this entry started from, now arriving from the deployment side rather than the validation side.

This does not change the decision. It is what *"the invariant lives in the application"* actually costs, priced.

---

## D-05: `jobs.payload` is `jsonb NOT NULL DEFAULT '{}'::jsonb`

**Problem:** Job input data must be stored. Relay never interprets it; it is an opaque blob forwarded to the worker.

**Options:**
- (a) `json` — stored as raw text
- (b) `jsonb` — stored as decomposed binary
- (c) `text` / `bytea` — fully opaque

**Chose:** (b).

**Correction to a common framing:** both `json` and `jsonb` validate JSON syntax on insert, so "validation" is *not* a differentiator between them. The real differences are: `json` preserves byte-exact text, key order, and duplicate keys, and re-parses on every access; `jsonb` normalises (key order lost, duplicate keys collapsed to last-wins), does not re-parse on read, and can carry a GIN index.

The reason usually given for `jsonb` — GIN indexing and querying inside the payload — **is not consumed by Relay**, since the scope lock means Relay never reads inside the payload. Basing the decision on an unused capability would be dishonest. The three reasons that actually apply:

1. **Option value is free.** `jsonb` costs nothing today and leaves the door open to an admin/debug query later (e.g. "which jobs reference `user_id = 5`"). `json` closes that door, and reopening it later means a table rewrite. When two options cost the same today, prefer the one that preserves future options.
2. **Read performance.** The worker reads the payload on every execution. `json` re-parses text on each access; `jsonb` does not. This shows up in Week 4's throughput work.
3. **Normalisation helps Week 3.** If the idempotency key is ever derived from a payload hash, `jsonb`'s normalisation is an asset: two logically identical payloads with different key order hash identically. Under `json`, `{"a":1,"b":2}` and `{"b":2,"a":1}` are different strings with different hashes.

**`NOT NULL DEFAULT '{}'` reasoning:** a NULL payload and an empty payload carry no distinct business meaning — both mean "no arguments". Keeping two representations of one state only creates bugs, since every handler would need to check both and one will eventually be forgotten. The default means jobs needing no input (e.g. a cleanup job) require nothing from the caller, and handlers are guaranteed a dict rather than `None`. General pattern: *represent "missing" as "empty", not as NULL, when both mean the same thing.*

**Cost:**
1. **Byte-exact input is not recoverable.** Key order and duplicate keys are lost. If a signed payload ever needs verification, re-serialising from `jsonb` will break the signature. Not a Relay requirement today — Relay does not sign payloads — but this permanently forecloses that option without a migration.
2. **Insert is slightly more expensive** than `json` (parse + normalise rather than store text).
3. **Large payloads carry a TOAST cost.** Values beyond roughly 2 KB are compressed and stored out-of-line. Precisely: a TOASTed value is **not** read unless the column is actually selected, and an `UPDATE` that does not modify the payload reuses the TOAST pointer rather than rewriting it. So the claim query is only affected if it selects `payload`. A Week 4 concern, not a Din 1 one.
4. **Payload size limit and `GET` response exclusion — resolved in Din 2.** Both ends of the pipeline constrain this one column, for different reasons. Full reasoning in the amendment below.


**Rejected:**
- **(a) `json`** — one strong use case exists: byte-exact preservation for cryptographic signature verification, audit/compliance requirements, or storing third-party signed webhook bodies. None apply to Relay.
- **(c) `text` / `bytea`** — maximally opaque and cheapest to write, but discards free syntax validation and all future query ability for no benefit. Would only make sense if payloads were genuinely non-JSON binary.

---

### `[AMENDED — Din 2]` Cost #4 resolved: what bounds this column, on the way in and on the way out

Cost #4 deferred two things to Din 2: the exact size limit, and where to enforce it. Recorded here rather than as a new `D-` number because both concern this same column.

#### Ingress — the size limit

**Chose:** a **256 KB payload budget**, enforced as a **266,240-byte bound on the whole request body**, in **HTTP middleware**, returning **`413`**.

Two numbers, one check. The 4 KB difference is envelope: the JSON structure and the `type` field. Only 266,240 is enforced; 256 KB is the budget it derives from, not a second independent limit. That distinction is worth stating because the first implementation *did* have two independent checks — a middleware bound on the body and a Pydantic validator on the payload dict — and they disagreed, producing `413` for some oversized requests and `422` for others. There is now exactly one enforcement point, and the Pydantic validator has been removed.

On the status code: RFC 9110 names 413 **`Content Too Large`**. The older `Request Entity Too Large` label is RFC 7231's; both constants exist in Starlette and both mean 413. The code uses the RFC 9110 name to match the RFC being cited.

**Why 256 KB:** a job payload is *arguments to a function call*, not a data transfer. Anything genuinely large — files, images, exports — belongs in object storage with the payload carrying only a reference. Managed queues land in the same order of magnitude for the same reason (AWS SQS caps a message at 256 KB), which is corroboration rather than justification. **No measurement supports 256 KB specifically** — it is an order-of-magnitude judgement, and cheap to move either way.

**Why middleware, and not a validator — this was found the hard way. `[MEASURED]`**

The first implementation put the check inside the `create_job` handler body. FastAPI reads and parses the request body while resolving parameters, *before* the function body runs, so the check ran after the damage. Three ~306 KB requests separated the cases:

| Request | Before the fix | After the fix |
|---|---|---|
| oversized, valid JSON | `413` | `413` |
| oversized, `type: ""` | `422` `string_too_short` | **`413`** |
| oversized, malformed JSON | `422` `json_invalid`, `loc: ["body", 306274]` | **`413`**, no `loc` |

The `loc: ["body", 306274]` is the proof: the JSON parser had reached character 306,274, so the entire body was buffered and parse was attempted before any size check. The limit provided **no** memory or CPU protection, and the status code for an oversized body depended on whether the body happened to be valid. After the move, all three return `413` and the parser offset is gone — no parse is attempted.

This is precisely the property Cost #4 asked for (*"reject before bytes are parsed"*), and it is only obtainable outside the handler: FastAPI reads the body before dependency resolution, so not even a `Depends` guard runs early enough.

**Cost:**
1. **The limit rests on a header the sender controls.** `Content-Length` is absent under `Transfer-Encoding: chunked` and optional in HTTP/2, and the check is skipped when the header is missing. The threat model is therefore *an honest client that made a mistake*, not an adversary. Recorded as `P-08` and deliberately unfixed in Week 1: closing it needs ASGI-level stream byte-counting, which is Week 4 hardening. `D-04`'s heuristic applies — tighten once real pain appears.
2. **The database column stays unbounded.** This constrains one entry point, not the column. Din 4 and Din 5 insert directly via `psql`, entirely outside it. Same shape as `D-04` Cost #3, where `max_length=100` on `type` lives at the API layer and the DB `CHECK` is still unapplied.
3. **The number is not derived from measurement.** If Week 4 finds real payloads clustering above it, the limit was wrong; far below, it was never load-bearing. Both are information; neither exists yet.

**Rejected:**
- **A Pydantic `field_validator` on serialised payload size** — measured above to run after parse, so it cannot prevent the cost that motivates the limit. It also had to re-serialise the payload with `json.dumps` purely to measure it, making the oversized path *more* expensive.
- **A DB `CHECK` on `octet_length(payload)`** — would bound the column (which the API-layer choice does not), but only after the bytes crossed the network, were parsed, and reached Postgres. Worth reconsidering when non-API write paths start mattering.
- **No limit at all** — tenable while the only client is the developer, but the failure mode is unusually bad. Week 0 Day 1 measured that CPU-bound synchronous work inside the event loop stalls every concurrent request (`6.04s vs 2.04s`), and a large `json.loads` is exactly that. One connection could stall the whole API process.

#### Egress — `payload` is excluded from `GET /jobs/{id}`

`GET /jobs/{id}` returns `{job_id, status}` and selects only those two columns at the SQL level. Two independent reasons, and it is worth keeping them separate because one of them turned out to be weaker than assumed:

**(a) Avoids the TOAST read.** Cost #3 above established that a TOASTed value is not read unless the column is selected. `GET` is the polling endpoint, so this is the one query that runs repeatedly per job. **Correction to an earlier framing:** the saving is *only* the TOAST dereference. PostgreSQL is a row-store reading whole 8 KB heap pages, so `SELECT id, status` and `SELECT id, status, type, created_at` cost the same heap I/O — every non-TOASTed column is already in the tuple. Adding `type` or `created_at` to the response later is therefore close to free, and the reason for keeping the response minimal is **not** I/O.

**(b) Narrows unauthenticated data exposure.** `D-03` chose sequential DB-generated ids, explicitly accepting that they are guessable, on the grounds that *"an unguessable id is obscurity, not security. The real fix is authorization."* That acceptance is cheap only while ids reveal nothing. Returning `payload` would turn a guessable id into a data read primitive over an endpoint with no auth — enumeration would yield whatever callers put in payloads. Excluding it **narrows the blast radius; it does not eliminate exposure**: `404` versus `200` still reveals which ids exist, and `status` still reveals what the system is doing. `D-03` Cost #3 already noted ids leak approximate job volume. The real fix remains authorization, which is out of scope for the month.

The actual reason the response is minimal is neither of the above: **adding a response field is backward-compatible, removing one is a breaking change.** Under that asymmetry, minimal is the reversible starting point. `attempts` was excluded on top of that because it is always `0` in Week 1 — a field that cannot vary teaches a client nothing while creating a compatibility obligation.

---

## D-06: `jobs.status` is `text` + `CHECK`; state *transitions* are enforced by compare-and-set, not by the schema

**Problem:** Two separate problems hide in this one column, and conflating them is the trap:
1. Which *values* are legal?
2. Which *transitions between* values are legal?

**Options for (1):**
- (a) native `ENUM`
- (b) `text` + `CHECK (status IN (...))`
- (c) lookup table + FK

**Chose (1): (b)** — `text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','succeeded','failed'))`.

First, the argument usually given for (b) needs correcting. *"Adding an enum value is painful in transactional migrations"* rests on pre-PG 12 behaviour, where `ALTER TYPE ... ADD VALUE` could not run inside a transaction block at all. **On PG 12+ it can** — the new value simply cannot be *used* in the same transaction that added it. Since Relay runs PG 16, adding `dead_letter` in Week 2 would have been easy either way, so that argument does not decide this. **`[MEASURED]`** — see verification at the end of this entry.

The reasons that do decide it:

1. **`DROP VALUE` does not exist, at all.** This is decisive given where the project is. Week 1 is the start of a four-week design I do not yet fully understand, so status naming will very likely change — `failed` may need splitting into retryable and terminal, `cancelled` may appear, `dead_letter` semantics may shift. Under `ENUM`, a wrong value is permanent unless the entire type is recreated and the column cast. Under `CHECK`, it is `DROP CONSTRAINT` + `ADD CONSTRAINT`.
2. **Alembic does not autogenerate enum value changes.** Alembic is being set up today. With `ENUM`, `alembic revision --autogenerate` would run, detect nothing, and give a false all-clear — a silent trap waiting in Week 2.
3. **The storage difference is irrelevant here.** `ENUM` is 4 bytes against roughly 11 for `'pending'` as text. With order-of-thousands rows in Month 1, that is a few KB. Trading flexibility for it would be optimisation without measurement.

The real driver: **this schema is going to change and I do not yet know how.** Under high uncertainty, minimise the cost of change, not the cost of storage.

`DEFAULT 'pending'` is included because a job is *born* pending — it makes that invariant structural, prevents an `INSERT` from accidentally creating a job in `running`, and makes manual `psql` inserts during Din 4/5 experiments trivial.

**Chose (2): compare-and-set in the application.**

**Neither `ENUM`, nor `CHECK`, nor an FK can prevent this:**

```sql
UPDATE jobs SET status = 'running' WHERE id = 1;   -- job was already 'succeeded'
```

Every constraint is satisfied, because `'running'` is in the allowed set. The transition is nonetheless wrong.

The reason no constraint can catch it: evaluating *"succeeded → running is illegal"* requires seeing **both the old and the new value**. A `CHECK` constraint sees only the row's current state; it has no access to what the row was before.

This is the Day 5 rule of thumb again, from my own log: *"a constraint works when the invariant fits inside a single row. When the invariant spans multiple rows, constraints cannot help."* Here the invariant spans two *versions* of one row rather than multiple rows, but the limitation is identical.

Enforcement therefore lives in the claim statement:

```sql
UPDATE jobs SET status = 'running' WHERE id = $1 AND status = 'pending'
```

`AND status = 'pending'` is **not an optimisation — it is the transition guard**, and the worker must check the affected row count: 1 means the claim succeeded, 0 means someone else got there first and this worker should move on.

This single statement does three things at once: it blocks illegal transitions, it blocks double claims, and it is **atomic** — the check and the write are in one statement, so nothing can interleave between them. That third property is what defeats Day 5's lost update. From that log: *"check-then-act is broken under concurrency... the truth of the read expires the moment I stop holding a lock on it."* A separate `SELECT` then `UPDATE` is check-then-act. `UPDATE ... WHERE status = 'pending'` is not.

**Cost:**
1. **Illegal transitions are only prevented where the guard is written.** Any future code path that updates `status` without a `WHERE` predicate on the old value bypasses the rule entirely. The database will not help. This is a permanent discipline requirement, and it is exactly the failure mode listed in the Day 5 log's `FOR UPDATE` column: *"forgetting the lock in one code path."*
2. `text` costs a few bytes more per row than `ENUM`.
3. Every status update site must check affected row count. Ignoring a `0` result would silently swallow a lost claim.
4. Adding `dead_letter` in Week 2 requires `DROP CONSTRAINT` + `ADD CONSTRAINT`, and `ADD CONSTRAINT ... CHECK` takes an `ACCESS EXCLUSIVE` lock and validates the whole table. The correct two-step pattern must be used then:
   ```sql
   ALTER TABLE jobs ADD CONSTRAINT jobs_status_check CHECK (...) NOT VALID;  -- instant
   ALTER TABLE jobs VALIDATE CONSTRAINT jobs_status_check;                   -- scans, but only SHARE UPDATE EXCLUSIVE; writes not blocked
   ```
   Irrelevant on today's empty table; needed in Week 2.

**Rejected:**
- **(a) `ENUM`** — no `DROP VALUE`, Alembic blind spot, and a storage saving too small to measure. Appropriate when the value set is genuinely permanent, when storage has been *measured* as a problem, or when enum's creation-order sorting is wanted (e.g. `('low','medium','high')`, which sorts uselessly as text).
- **(c) lookup table + FK** — adds a table and a per-write FK check for a set of five values that changes perhaps twice in the project's life, and still cannot enforce transitions.
- **A trigger for transition enforcement** — a trigger *can* see `OLD` and `NEW`, so it would work. Rejected because: it hides the rule from the Python code where a reader expects it; it is harder to unit test; it duplicates a guard that is needed anyway for concurrency, so the same rule would live in two places and eventually diverge; and in a project whose purpose is understanding where safety comes from, burying that safety inside the database defeats the purpose. A trigger becomes correct when multiple independent applications write to the same table and none can be trusted individually.

**`[MEASURED]` — enum-in-transaction behaviour on this instance (PostgreSQL 16):**

```sql
CREATE TYPE t_enumtest AS ENUM ('a','b');
BEGIN;
ALTER TYPE t_enumtest ADD VALUE 'c';        -- CREATE TYPE / BEGIN / ALTER TYPE  → all OK
CREATE TABLE tt_enumtest (x t_enumtest);    -- CREATE TABLE → OK
INSERT INTO tt_enumtest VALUES ('c');       -- ERROR
COMMIT;                                      -- became ROLLBACK (txn already aborted)
```

Actual error text:
```
ERROR:  unsafe use of new value "c" of enum type t_enumtest
HINT:   New enum values must be committed before they can be used.
```

**Result:** the corrected framing holds exactly. `ALTER TYPE ... ADD VALUE` **does** run inside a transaction block on PG 16 — so "you cannot add enum values in a transactional migration" is false here. The real restriction is narrower: the new value cannot be *used* until the adding transaction commits. Practically that means a `dead_letter` migration would need **two** migration steps (add the value, then use it), which is an inconvenience rather than the blocker it is usually described as.

**This does not change the decision.** The reasons that actually decided it — no `DROP VALUE`, and Alembic's autogenerate blind spot — are untouched by this measurement. Recording it because the *stated* reason for the choice must be the *real* reason, or the entry is worthless in six months.

*(Test artefacts were rolled back / dropped; `t_enumtest` and `tt_enumtest` do not exist.)*

---

## D-07: `attempts integer NOT NULL DEFAULT 0` is added now, in Week 1, although retries arrive in Week 2

**Problem:** Retry logic is Week 2's scope. Should the column exist before the logic that reads it?

**Options:**
- (a) Add `attempts` now
- (b) Add it in Week 2 with the retry logic
- (c) Add `attempts` plus the rest of the retry columns (`max_attempts`, `next_run_at`, `last_error`) now

**Chose:** (a).

First, a **rejected justification**: the common argument is that adding a column with a default to a large table causes a rewrite and lock contention. **On PG 11+ this is wrong for a constant default** — `ADD COLUMN ... DEFAULT 0` stores the default in the catalog and does not touch the table, so it is effectively instant regardless of row count. A rewrite *does* occur for a **volatile** default such as `DEFAULT random()` or `DEFAULT clock_timestamp()`, and that distinction is the part worth remembering. **`[MEASURED]`** — see verification at the end of this entry.

What *is* true, and is the more useful operational lesson: `ALTER TABLE` still takes a brief `ACCESS EXCLUSIVE` lock. The real hazard is not the rewrite but the **lock queue** — if a long-running transaction holds the table, the `ALTER` waits behind it, and every subsequent read and write queues behind the `ALTER`. An "instant" migration can therefore freeze the table. Mitigated with `lock_timeout`, so the migration fails instead of blocking everything. Relevant to Week 4 operations, not to today's empty table.

The actual reason to add it now: **the schema is itself a design document**, and deferring the column bundles two decisions together in Week 2. The second one is the awkward one — **backfill semantics**: for rows already sitting in `running` or `failed` when the column appears, is `attempts` 0 or 1? That question would arrive precisely while wrestling with retry logic. Adding the column today, against an empty table, makes the question disappear: every job starts at 0.

Practically, Week 1's worker already marks jobs `failed`. With the column present, Week 2's change is one line (increment) rather than migration plus backfill plus code.

**`NOT NULL` is a correctness requirement, not style.** In SQL, `NULL + 1` evaluates to `NULL`. A nullable `attempts` means the worker's `attempts = attempts + 1` never increments — it stays `NULL` forever. Week 2's `if attempts >= max_attempts` would then never be true, and the job would **retry indefinitely**. That directly breaks contract #3 (*"bounded retry, not an infinite loop"*), and it breaks it **silently**. One missing keyword, one broken contract, no error message — the same class of silent wrongness Week 0 was built around.

General rule extracted: **counters, flags, and states should never be nullable.** NULL should mean "value unknown"; a counter's value is always known, at worst `0`.

`integer` over `smallint`: `smallint` would save 2 bytes, but Postgres row **alignment padding** ahead of the 8-byte `timestamptz` would likely absorb that saving. With no measurable gain, take the boring option — fewer surprises with Python ints and SQLAlchemy defaults.

**Cost:**
1. **An unused column exists for a week.** Nothing reads or writes it in Week 1, so a reader could reasonably ask why it is there. Accepted deliberately.
2. **Its exact semantics are not yet pinned.** Is `attempts` incremented at claim time or at failure time? That is Week 2's decision, and the column being present does not answer it. Only the counter's *shape* is committed, not its update policy.
3. `integer` is 4 bytes where 2 would functionally do.

**Rejected:**
- **(b) defer to Week 2** — forces the column decision and the backfill-semantics decision to be made simultaneously, under pressure, while the retry logic itself is still being worked out.
- **(c) add all retry columns now** — scope creep, and the distinction matters. `attempts` has an **obvious** semantic (a counter, incremented on attempt) with no embedded design decision. `next_run_at` does **not**: its meaning depends on the backoff strategy (exponential? jittered? capped?), on how the reaper reads it, and on timezone handling — none of which are known yet. Adding it today would commit a guess that Week 2 then has to fight, or leave an unused column that misleads future readers. **Rule: add a column whose meaning is known today; do not add one whose meaning depends on a future design decision.**

**`[MEASURED]` — does `ADD COLUMN ... DEFAULT` rewrite the table? (PostgreSQL 16, 50,000 rows)**

A table rewrite changes the relation's on-disk file, so `pg_class.relfilenode` is a direct indicator — same value means no rewrite.

```sql
CREATE TABLE rw_test (id int);
INSERT INTO rw_test SELECT generate_series(1,50000);
SELECT relfilenode FROM pg_class WHERE relname='rw_test';                          -- 24660
ALTER TABLE rw_test ADD COLUMN c1 integer NOT NULL DEFAULT 0;                      -- constant default
SELECT relfilenode FROM pg_class WHERE relname='rw_test';                          -- 24660  ← unchanged
ALTER TABLE rw_test ADD COLUMN c2 timestamptz NOT NULL DEFAULT clock_timestamp();  -- volatile default
SELECT relfilenode FROM pg_class WHERE relname='rw_test';                          -- 24665  ← changed
DROP TABLE rw_test;
```

| Operation | `relfilenode` | Rewrite? |
|---|---|---|
| baseline | 24660 | — |
| `ADD COLUMN ... DEFAULT 0` (constant) | 24660 | **No** |
| `ADD COLUMN ... DEFAULT clock_timestamp()` (volatile) | **24665** | **Yes** |

**Result:** both halves of the claim confirmed on this instance. The commonly-repeated "adding a column with a default rewrites the table" is **false for a constant default on PG 16**, and **true for a volatile one**. So that argument could not have justified adding `attempts` early — the justification is the backfill-semantics one given above, not a performance one.

What this measurement does **not** cover: the `ACCESS EXCLUSIVE` lock-queue hazard described above. `relfilenode` says nothing about lock waits, and no contention was present during this test. **That part remains inference** and would need a separate experiment (hold a long transaction on the table, then time the `ALTER`).

*(Test table dropped.)*

---

## D-08: `created_at timestamptz NOT NULL DEFAULT now()`, generated by the database

**Problem:** Job creation time must be recorded. Three sub-decisions hide here: which type, which default function, and which process supplies the value.

**Options:**
- (a) `timestamp` vs `timestamptz`
- (b) `now()` vs `clock_timestamp()`
- (c) DB-generated vs application-generated

**Chose (a): `timestamptz`.**

`timestamp` stores a wall-clock reading **without recording which zone it belongs to** — `2026-08-13 14:30:00` gives no way to know whose 14:30 that was. `timestamptz` stores an unambiguous absolute instant, internally as UTC. (The name misleads: it does **not** retain the original zone. It converts to UTC on input and renders via the session's `TimeZone` on output. The point is that the stored value is unambiguous, not that the zone is remembered.)

This matters because Relay is three processes — API, worker, reaper — potentially in different containers today and on different machines in Week 4. Week 2's reaper will compute things like `now() - created_at > interval '30 seconds'`. Under `timestamp`, if writer and reader sit in different zones, that arithmetic is **silently wrong**: the reaper declares live jobs dead, or leaves dead jobs alone. A live job declared dead is duplicate execution — contract #2 broken, with no error raised. `timestamptz` eliminates that entire class of bug at zero cost, since both types occupy 8 bytes.

**Chose (b): `now()`.**

`now()` (= `CURRENT_TIMESTAMP` = `transaction_timestamp()`) returns **transaction start time** and stays constant for the whole transaction. `clock_timestamp()` returns the real clock and advances within a transaction.

The apparent objection to `now()` is that inserting ten jobs in one transaction gives all ten an identical `created_at`, producing ties in FIFO ordering. On reflection **the tie is correct, not a defect.** Consider the outbox pattern that motivates D-01's choice of Postgres:

```sql
BEGIN
  INSERT INTO orders ...
  INSERT INTO jobs (type='send_receipt', ...)
COMMIT
```

Those rows were created **atomically**. The job was not created "after" the order — both became real at the same instant. An identical `created_at` states that truthfully. `clock_timestamp()` would assign them timestamps microseconds apart, implying an ordering with no business meaning — fake precision, which is dangerous precisely because it invites trust.

Ties are then handled cheaply with a deterministic tiebreaker: `ORDER BY created_at, id`.

`now()` is also the convention, so any reader understands it immediately; `clock_timestamp()` would make every reader stop and look for a special reason that does not exist.

**Chose (c): DB-generated.**

If the application set the timestamp, Week 4's multiple API instances would inject **multiple clocks** into the ordering. Even under NTP, machines drift by milliseconds, so a job created on instance A could appear older than one created later on instance B. `DEFAULT now()` means **one clock, one source of truth**.

This connects directly to Week 0's central thread — from the Day 3/4 log: *"No system can directly inspect another process's liveness — it can only observe signals... Set a deadline."* A deadline is meaningless if two processes disagree about the time. Week 2's lease expiry rests entirely on this, and the answer to *"whose clock decides the lease expired?"* is the database's, because there is only one of it.

Secondary benefit: the default cannot be forgotten, so manual `psql` inserts during Din 4/5 experiments always get a valid timestamp.

**Cost:**
1. **`created_at` does not give true FIFO either.** Since `now()` is transaction *start* time and commit happens later, a transaction starting at 10:00:00 and running 5 seconds commits after one that started at 10:00:03. The later-stamped row becomes visible first. This is **the same flaw as D-03's id ordering** — two different columns, one shared cause, which is MVCC's nature rather than any column choice. No column can fix it. Relay's ordering is therefore **best-effort FIFO**, and that is acceptable because ordering is not among the five contract promises. Tracked as `P-05`.
2. **Ties are guaranteed** for jobs enqueued in one transaction, so any query needing deterministic order must add a tiebreaker.
3. **Enqueue time cannot be attributed to a specific application instance**, since the DB stamps it. Fine today; would matter if per-instance latency attribution were ever needed.

**Rejected:**
- **(a) `timestamp`** — correct only for genuinely "floating" local times, where the wall-clock reading is the meaning regardless of zone (a shop opening at 9 AM, a birthday). Server events are absolute instants, never floating.
- **(b) `clock_timestamp()`** — appropriate when measuring real elapsed time *inside* a long transaction, e.g. a batch processing 1000 rows where each row's true processing time matters. Relay's enqueue transactions are deliberately short (Din 2: commit, then respond), so the difference here is microseconds and unmeasurable.
- **(c) application-generated** — introduces clock skew across instances into the one column the claim query orders by, and can be forgotten on manual inserts.

---

## D-21: `job_executions` is an append-only instrument table, written *before* the handler runs, in its own transaction, with no foreign key and no index

*(Week 1, Din 4. Numbered `D-21` because `D-09`..`D-20` belong to the Month 2–4 roadmap — see the numbering note at the top of this file.)*

**Problem:** Relay's contract says a job's side effects must not be duplicated. Din 4 had to test that, and `jobs` alone **cannot** answer the question: `status` is a single column that gets overwritten, so `succeeded` looks identical whether one worker ran the job or five did. An `UPDATE` destroys the evidence of the previous writer by design. So the day needed a place where a second execution cannot erase the first one's record.

**Options:**
- (a) Append-only table, one row per execution, `(job_id, worker_id, executed_at)`
- (b) An `executions integer` counter column on `jobs`, incremented per run
- (c) The execution row written in the **same** transaction as the terminal `succeeded`/`failed` mark
- (d) (a) plus `FOREIGN KEY (job_id) REFERENCES jobs(id)` and an index on `job_id`

**Chose:** (a), with three specific placement decisions that matter more than the schema:

1. **Written after the claim commits, before `await handler(payload)`.** So the row means *"a handler was entered for this job"*.
2. **Written in its own session and its own transaction** (`record_execution()`), not inside the claim transaction and not inside the mark transaction.
3. **No foreign key, no index on `job_id`.**

**Why (1) — the ordering is the whole design.** A row written at *mark* time is evidence of completion, and a worker killed mid-handler leaves no trace at all — exactly the case Din 5 exists to observe. A row written at *claim* time would be evidence of intent, and would count jobs that never reached a handler. Writing it immediately before dispatch is the only position where the row means "work started", which is what a duplicate-execution test needs: two rows mean the handler ran twice, whatever `jobs` says.

**Why (2) — evidence must not share a fate with the thing it is evidence about.** If the execution row is written in the same transaction as the terminal mark, then a failed mark rolls back the proof that the job ran (`P-11`'s starting point, and Din 4's own Step 1 prediction question). Committing separately means the two records can disagree — and that disagreement is the diagnostic. `job_executions` says the handler ran; `jobs` says `running`; the truthful reading is *"it ran and nobody recorded how it ended"*, which is precisely Week 2's problem.

**Why (3) — measured to cost nothing yet, and both parts are reversible.** At 58 jobs and 30 execution rows the duplicate query (`GROUP BY job_id HAVING count(*) > 1`) is a sequential scan over a table of tens of rows. Adding an index today would be `P-03`'s mistake in miniature: freezing a guess before the data shape exists. The FK is a real decision rather than an omission, argued below.

**Cost — all four of these are measured, not theoretical:**

1. **It records handler dispatch, not claims.** `[MEASURED]` A job with an unregistered `type` is claimed, marked `failed`, and leaves **no** row (job `58`); a job whose handler raises leaves one (job `57`, `type = boom`). So "claimed" and "executed" are different populations, and only the second is instrumented. Consequence: the table cannot detect a job that was claimed and lost before dispatch.
2. **`count(*) > 1` is a duplicate test only while retries do not exist.** Week 2's retry legitimately produces several rows for one job. The test expires the moment retries land, and the fix is another column (attempt number, or a claim id), not another query. Tracked as `P-11`.
3. **No FK means orphan rows are accepted.** `[MEASURED]` `INSERT INTO job_executions (job_id, worker_id) VALUES (999999, 'probe-orphan')` succeeded. The instrument can therefore assert an execution of a job that never existed, and nothing catches a typo'd `job_id` in a manual probe. *(Probe row deleted; it consumed `id = 31`.)*
4. **A crash between the claim commit and the execution row's commit under-counts.** `[INFERRED from code]` The gap is milliseconds wide and has not been reproduced deliberately, but in it a job is `running` with no execution row — the mirror image of Cost 1.

**Rejected:**
- **(b) counter column on `jobs`** — an `UPDATE` again, so it inherits the exact problem it was meant to solve: it cannot say *which* worker ran the job, or *when*, and a lost update loses the count silently. It also cannot support Din 4's actual use: `executed_at` is what made it possible to reconstruct a finished experiment's timeline and discover that the two workers barely overlapped (`P-12`). A counter would have hidden that permanently.
- **(c) same transaction as the terminal mark** — kills the evidence exactly when it is most needed (mark fails, DB restarts, worker dies after the handler). Also makes the killed-mid-handler case indistinguishable from the never-started case, which is Din 5's entire subject.
- **(d) FK + index — deferred, not dismissed.** The FK would buy referential honesty (Cost 3), and its price is a specific Week 4 conflict: deleting `jobs` rows older than 30 days then either fails on the FK, or needs `ON DELETE CASCADE`, which **deletes the execution history** — i.e. the audit trail disappears with the audited row, and an audit trail that vanishes with its subject is not much of an audit trail. The third option, `ON DELETE SET NULL`, needs a nullable `job_id` and turns the row into an orphan by design. That is a real decision with three unattractive branches, and it needs Week 4's retention policy to exist first. Recorded as deferred below.

**Revisit when:** Week 2 adds retries (Cost 2 forces an attempt/claim identifier), or Week 4 defines job retention (forces the FK/cascade question), or the duplicate query gets slow enough to measure (then index `job_id`, with `EXPLAIN ANALYZE`, alongside `P-03`).

---

## What was deliberately NOT decided today

Recording these so that "not yet decided" is never mistaken for "overlooked":

| Deferred | Scheduled | Why not today |
|---|---|---|
| Index for the claim query | Week 4 | To be **measured** with `EXPLAIN ANALYZE`. Guessing today would freeze an assumption into the schema. Tracked as `P-03` |
| `idempotency_key` + unique constraint | Week 3 | Its scope (what forms the key, what TTL applies) becomes clear only after Din 4's duplicate-POST experiment |
| `lease_expires_at`, heartbeat columns | Week 2 | Din 5 must first produce a stuck job and observe it. Designing the fix before seeing the failure means copying a solution rather than understanding it |
| `max_attempts`, `next_run_at`, `last_error` | Week 2 | Semantics depend on the backoff strategy, which is not yet designed. See D-07 |
| `updated_at` | Week 2 | No consumer exists yet; the reaper will justify it |
| `dead_letter` status value | Week 2 | Add via the `NOT VALID` + `VALIDATE CONSTRAINT` pattern in D-06's Cost section |
| ~~Payload size limit and where to enforce it~~ | ~~Din 2~~ | ✅ **Resolved Din 2** — 266,240-byte body bound in HTTP middleware, `413`. See `D-05` Cost #4 amendment. Residual gap: `P-08` |
| ~~`type` validation placement (API vs worker)~~ | ~~Din 2–3~~ | ✅ **Resolved Din 3** — API bounds shape; the real invariant (*a handler is registered*) is now checked by the worker's registry at claim time. Measured: unregistered type → claimed once, `failed` once, no hot loop. `D-04`'s position unchanged; its priced cost is the deploy-ordering hazard in the Din 3 amendment |
| Shutdown observation latency vs poll interval | Week 2 | `P-10`. The loop sleeps the interval in one `await`, so the shutdown flag is seen up to a full interval late. Fix is slicing the sleep or waiting on an `asyncio.Event`; safe at 2 s inside Docker's 10 s grace, so deferred with the rest of shutdown hardening |
| ~~`ORDER BY (created_at, id)` tiebreak on the claim query~~ | ~~Din 4, before seeding~~ | ✅ **Resolved Din 4, Step 0** — claim query now orders by `(created_at, id)`. It was load-bearing: the ten seeded jobs did share one `created_at`, and the reconstruction in the Din 4 log (`M4`) is only possible because job order was deterministic |
| FK `job_executions.job_id → jobs(id)`, and an index on `job_id` | Week 4 (retention), or when the duplicate query gets slow | `D-21`. FK's three branches are all unattractive until a retention policy exists: plain FK blocks the delete, `CASCADE` deletes the audit trail with its subject, `SET NULL` orphans by design. Index deferred for `P-03`'s reason — measure, do not guess |
| An attempt number / claim id on `job_executions` | Week 2, with retries | `P-11`. `count(*) > 1` stops meaning "duplicate" the moment a retry legitimately writes a second row |
| A claim timestamp on `jobs` (`claimed_at` / `lease_expires_at`) | Week 2 | Din 4 made the gap concrete: a stuck `running` row carries no answer to *"how long has this been running?"* — `created_at` is enqueue time, not claim time. Do not add it before Din 5 has looked at a real stuck job |
| `signal.SIGBREAK` registration in the worker | Week 2 | Only `SIGINT` is live on Windows today; `SIGTERM` is registered and correct for Docker but undeliverable natively. Decides whether `Ctrl+Break` is graceful or fatal |
| DB-level bound on `type` length | Week 4 | `D-04` Cost #3's `CHECK (length(type) <= 100)` is still unapplied. Din 2 bounded it at the API layer only, so `psql` inserts bypass it |
| Stream-level body limit (`Content-Length`-independent) | Week 4 | `P-08`. Record the fix's own overshoot bound (limit + one chunk) when it lands |
| Response fields `type` / `created_at` on `GET /jobs/{id}` | When a consumer needs them | Measured to be near-free (row-store; same heap page). Excluded only for response-surface reversibility, not cost |

