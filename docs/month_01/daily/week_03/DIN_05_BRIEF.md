# Week 3 Din 5 BRIEF — property test: evidence, opinion nahi

**Aaj production feature nahi banti. Aaj Relay ke execute-side dedup contract ko pehle precise statement, phir deterministic model, random action sequences, real PostgreSQL witnesses, aur load-bearing mutation se testable banaya jaata hai.**

Seal rule: Part A ke six prediction answers sabse pehle `DIN_05_ANSWERS.md` me likho; immutable copy + SHA-256 banao; phir har step ka experiment; observed output ke against apni explanation; tab KEY ka corresponding section kholo. `idk` valid hai. Frozen prediction block Gemini ko paste nahi karna. KEY experiment se pehle nahi kholna.

Current evidence bench `[MEASURED-R 2026-09-03]`: `119` jobs (`97 succeeded / 15 failed / 4 pending / 3 dead_letter / 0 running`), `max(id)=125`, `jobs_id_seq=125`, `107` executions, `9` effects, `side_effects_id_seq=12`, Alembic `w3d4_enqueue_idempotency`, zero Relay processes, zero idle transactions, zero infinity gates, and no Din 4 probe objects/databases. Ye `119` historical evidence rows test fixture nahi hain aur delete/mutate nahi hongi.

**Provenance:** current bench `[MEASURED-R]` hai. Is BRIEF ke future outputs, expected traces, aur mechanism claims `[INFERRED from the approved source/schema and Week 3 plan]` hain jab tak tum corresponding command chala kar actual output `[MEASURED]` record nahi karte. Hypothesis ka exact generated/shrunk trace pre-fill nahi hota.

---

# Part A — Contract cards, Steps 0–9, and frozen predictions

## Contract cards — code se pehle fill and freeze

### Card 1 — property universe and predicate

```text
Logical identity under test: ______________________________
Universe: “har job” / “effect jobs” / “durable effect keys” / other: __________________
Completion evidence available today: ______________________
Safety predicate (mathematical form): ______________________
Conditional liveness/exactness predicate: __________________
Why `job_executions` is or is not completion evidence: _____
Why `status='succeeded'` is or is not enough: ______________
P-27 changes dispatch count how: ___________________________
P-27 changes the effect predicate how: _____________________
```

### Card 2 — two-layer evidence claim

```text
Layer A input: explicit action sequence ____________________
Layer A can claim: _________________________________________
Layer A cannot claim: ______________________________________
Layer B input: real PostgreSQL/process witness _____________
Layer B can claim: _________________________________________
Layer B cannot claim: ______________________________________
Number of configured all-sequence examples: _______________
Number of configured forced-redispatch examples: __________
```

### Card 3 — isolation decision

```text
Evidence DB: relay; opening rows: 119; allowed writes: NONE
Layer A isolation: _________________________________________
Layer B isolation: _________________________________________
Why rollback-per-example does/does not contain subprocess commits: __________
Why key-prefix scoping does/does not stop the production claim query: ________
Disposable DB naming rule: relay_din5_<PID>_<8 hex>
Cleanup proof: pg_database count=0 + evidence fingerprint unchanged
```

### Card 4 — mutation contract

```text
Mutated enforcement point: model effect-write dedup policy
Mutation selector: DIN5_MUTANT=no_dedup (test-only; never src/)
Expected mutant process exit: non-zero
Required failure text: Falsifying example + shrunk_trace + effect_count=2
Required post-mutation control: same node green with mutation absent
What this mutation proves: _________________________________
What this mutation does NOT prove: _________________________
```

## Required test interfaces

Tum implementation likhoge. Verification commands in exact interfaces ko call karengi:

- `tests/din5/test_model.py`
  - deterministic nodes named in C2;
  - Hypothesis nodes named in C3/C4;
  - explicit actions such as `claim`, `effect_write`, `crash`, `reclaim`, `retry`, `mark`;
  - test-only `DIN5_MUTANT=no_dedup` dependency-injects the wrong effect-write policy; production `src/` me mutation flag nahi.
- `tests/din5/pg_witness.py`
  - CLI: `--scenario baseline|concurrent|crash_reclaim|stale_mark --output <json-path>`;
  - only `DIN5_TEST_DATABASE_URL` use kare;
  - first query `current_database()` and refuse unless name matches `relay_din5_<PID>_<8 hex>`;
  - every scenario fresh rows/keys use kare and its own processes stop kare;
  - real writer path imports/calls current Relay worker behavior rather than reimplementing the correct dedup algorithm in the assertion.
- `.din5-artifacts/`
  - temporary JSON/transcripts only; relevant shrunk trace log me copy karne ke baad C9 removes it.

Ye interface contract tests ko implementation-independent rakhta hai; test code ka design tumhara hai. `[INFERRED]`

---

## Step 0 — 10 min: freeze six predictions + prove opening bench

**Terms used in this step**
- **Frozen prediction:** run se pehle saved text; later correction prediction credit nahi.
- **Evidence fingerprint:** historical DB ke selected counts/state ka compact equality check.
- **Vacuous pass:** test green, par antecedent/duplicate case kabhi generate hi nahi hua.

1. Neeche ke exact six questions `DIN_05_ANSWERS.md` me answer karo. Har Q ke neeche permanent `Prediction`, empty `Observed + meri explanation`, aur empty `After KEY` blocks rakho.
2. C0 se immutable `DIN_05_PREDICTIONS_FROZEN.md` banao and SHA-256 record karo.
3. C0 direct SQL target, Python runtime target, process state, revision, status buckets, sequences, infinity gates, and probe DB count assert karega.
4. Koi mismatch ho to stop. Historical rows repair/delete/reset mat karo.

**Executable end:** frozen predictions and exact opening fingerprint `119|125|125|107|9|12|w3d4_enqueue_idempotency`, with no DB delta.

**KEY:** abhi mat kholo.

## Step 1 — 10–15 min: property wording before test code

**Terms used in this step**
- **Safety:** bad state kabhi reachable na ho; yahan duplicate durable effect ka bound.
- **Conditional liveness:** named precondition reach hone par desired durable fact eventually/atomically present ho.
- **Dispatch evidence:** handler start se pehle recorded attempt; completion evidence nahi.
- **Property universe:** kin identities/states par quantifier (`for all`) apply hota hai.

1. Chaar contract cards fill karo before creating `tests/din5/*`.
2. Morning wording verbatim `DIN_05_PROPERTY.md` me rakho; overwrite nahi. Evening correction alag heading me append hogi.
3. `boom`, `dead_letter`, no-effect jobs, crash-before-effect, and effect-write-reached cases ko wording ke against manually classify karo.
4. Ek predicate me safety aur liveness mat mila do. `<= 1` aur conditional `= 1` alag lines deserve karte hain.
5. Layer A ko real-world proof aur Layer B ke 2–3 runs ko exhaustive proof mat bolo.

**Executable end:** C1 property card ko mechanically checks; no test code and no DB write yet.

**KEY:** C1 ke baad “Property mathematics” kholo; prediction answers nahi.

## Step 2 — 10–15 min: deterministic executable model

**Terms used in this step**
- **Reference model:** small explicit state transition system; production implementation ki copy nahi.
- **Action sequence:** values ke bagal me operation order generate hota hai.
- **Precondition:** action tabhi legal jab model state usse allow kare.
- **Redispatch:** same logical job/effect identity ka second claim/dispatch after retry or reclaim.

1. `tests/din5/test_model.py` me model state define karo: job state, claim generation/owner as observation, live/stale workers, dispatch count, effect attempts, durable effect count, and terminal marks.
2. Effect identity stable `job:<logical-id>` rakho; attempts/workers badalne par identity nahi badalni chahiye.
3. Deterministic controls likho:
   - zero effect-write boundary → effect count `0`;
   - one dispatch + one committed effect-write → `1`;
   - write → crash/reclaim → second dispatch/write → still `1` with dedup;
   - P-27-style extra dispatch/write → still safety bound;
   - two dispatches are explicitly counted, so passing result “duplicate hua hi nahi” se explain nahi ho sakta.
4. Model transition and assertion separate rakho. Assertion me production `ON CONFLICT` implementation copy mat karo.

**Executable end:** C2 ke four named deterministic nodes green; reclaim control reports `dispatches>=2` and `effects=1`.

**KEY:** ab “Model boundary” kholo.

## Step 3 — 15 min: Hypothesis generates sequences, not timing noise

**Terms used in this step**
- **Shrinking:** failing input ko smaller reproducible counterexample me reduce karna.
- **Stateful/rule-based testing:** valid state transitions ke rules se action histories generate karna.
- **Forced-redispatch strategy:** generated examples ka named subset jisme at least two dispatches construction se guaranteed hain.
- **Coverage witness:** property antecedent kitni examples me actually reached hua.

1. Ordinary list strategy ya `RuleBasedStateMachine` choose karo; reason contract card me one line.
2. No wall-clock sleep, OS scheduler, 30 s lease, or poll timing in Layer A. Same action sequence must replay to same result.
3. Do named properties:
   - all legal action sequences preserve safety;
   - generated redispatch sequences **construction se** two-or-more dispatches reach karein and preserve safety.
4. `assume(dispatches >= 2)` se almost all examples filter karne ke bajaye a valid redispatch skeleton generate karo, phir random prefix/tail/actions shrinkable rakho.
5. Fixed settings contract: all-sequence `200` examples; forced-redispatch `100`; deadline disabled only because this is an in-memory deterministic model, not to hide slowness; no suppression of health checks without written cause.
6. C3 artifact records configured/completed counts, number with `dispatches>=2`, maximum observed dispatches, and safety failures.

**Executable end:** C3 green, with `all_sequence_examples=200`, `redispatch_examples=100`, `redispatch_examples_with_two_or_more_dispatches=100`, `safety_failures=0`.

**KEY:** corresponding “Hypothesis claim boundary” tabhi kholo.

## Step 4 — 10–15 min: load-bearing mutation must make the same property RED

**Terms used in this step**
- **Mutation testing:** protection deliberately replace/remove karke test sensitivity verify karna.
- **Killed mutant:** same assertion mutant ke against fail hui.
- **Surviving mutant:** protection absent thi phir bhi suite green; test/coverage/oracle weak hai.
- **Shrunk semantic trace:** minimum legal action history printed in domain words, not opaque integers.

1. Production source edit mat karo. Model ke effect-write policy ko dependency-inject karo; normal mode set-like/idempotent write, `DIN5_MUTANT=no_dedup` append-every-time wrong policy.
2. **Same forced-redispatch Hypothesis node and same assertion** run karo. Mutant-only special assertion mat likho.
3. Assertion failure me `shrunk_trace=<actions>; dispatches=<n>; effect_writes=<n>; effect_count=2` print hona required.
4. C4 non-zero exit ko expected success of mutation verification treat karega; output me `Falsifying example` and semantic trace mechanically search karega.
5. Mutation env remove karke same node immediately green rerun karo. Suite intentionally red leave mat karo.
6. Shrunk case verbatim Week 3 log template ke M1 block me copy karo; paraphrase alone insufficient.

**Executable end:** mutant red + shrunk trace retained + normal policy green.

**KEY:** ab Q4/Q5 sections kholo.

## Step 5 — 10 min: provision isolated PostgreSQL target

**Terms used in this step**
- **Disposable database:** process/session commits ko evidence DB se physically separate target.
- **Target assertion:** migration/test se pehle same connection par `current_database()` exact expected name.
- **Rollback boundary:** ek transaction sirf apni connection/session ke writes rollback karti hai.
- **Claim contamination:** production claim query test prefix nahi dekhti; any eligible oldest pending row utha sakti hai.

1. C5 same PowerShell terminal me GUID/PID database `relay_din5_<PID>_<8hex>` create karega.
2. Exact URL override se Alembic head migrate karo; bare `alembic upgrade` forbidden.
3. Test DB starts at `0 jobs / 0 executions / 0 effects`; evidence DB exact C0 fingerprint pe recheck.
4. `$env:DIN5_TEST_DATABASE_URL` only disposable target ko point kare. `DATABASE_URL` evidence URL pe leave karke witness mat chalao.
5. C5–C9 same main terminal me run karo so `$testDb` and cleanup function remain available. Failure ho to bhi C9 cleanup run karna mandatory.

**Executable end:** isolated head exists, empty, target checked, evidence fingerprint unchanged.

**KEY:** ab Q3 isolation section kholo.

## Step 6 — 15 min: real PostgreSQL baseline + concurrent dedup witness

**Terms used in this step**
- **Witness:** one concrete real execution supporting a model assumption; exhaustive proof nahi.
- **Unique-index arbitration:** PostgreSQL one non-null effect key ka single durable winner chooses.
- **Production-path witness:** current `handle_effect()`/writer behavior invoked, test-side “correct” clone nahi.

1. C6 baseline scenario run karo: one effect job, one execution/write, one durable keyed effect.
2. Concurrent scenario me same logical job/effect key ke two distinct worker processes/sessions ko overlap karao.
3. Persisted evidence requires: two execution/dispatch witnesses, two worker identities, effect insert verdict multiset `{1,0}`, final durable keyed effects `1`.
4. A single-process sequential double-call acceptable negative fallback nahi; concurrency/process distinction artifact me present honi chahiye.
5. Scenario rows disposable DB me reh sakti hain until C9; every assertion scenario key/job id se scoped ho.

**Executable end:** C6 JSON checks baseline `1/1` and concurrent `2 dispatches / 2 workers / 1 effect / {1,0}`.

**KEY:** “PostgreSQL witness mechanics” kholo.

## Step 7 — 15 min: real hard-crash → reclaim → redispatch witness

**Terms used in this step**
- **Hard crash:** process termination that bypasses worker exception/finally path.
- **Durable orphan effect:** effect committed, job mark not committed; job remains recoverable while effect exists.
- **Committed reclaim barrier:** second worker starts only after DB reads `pending`, attempts `1`, `claimed_at NULL`.

1. C7 harness isolated DB me effect job create kare; Worker A real process starts.
2. Effect row commit and execution row visible hone ke baad, terminal status mark se pehle Worker A hard-kill karo. `raise` substitute nahi.
3. Pre-reclaim snapshot required: `running / attempts=1 / executions=1 / effects=1`.
4. Lease deterministic banane ke liye target `claimed_at` older than lease karo; real reaper process run; committed barrier `pending|1|true` assert karo.
5. Reaper stop; Worker B run; second execution + dedup `rowcount=0`; final `succeeded / attempts=2 / executions=2 / workers=2 / effects=1`.
6. Timeouts fail closed and child PIDs artifact me retain; harness finally all children stop kare.

**Executable end:** C7 proves redispatch happened and real PostgreSQL effect stayed one; test DB only.

**KEY:** “Crash/reclaim witness” kholo.

## Step 8 — 10 min: name the fencing boundary; do not build it

**Terms used in this step**
- **Fencing token / claim generation:** monotonic claim identity included in later writes so stale owner is rejected.
- **Generation blindness:** `WHERE status='running'` old and current running generation ko distinguish nahi kar sakta.
- **Stale mark:** earlier claimant ka terminal update after reclaim/new claim.

1. Is exact interleaving ko model and isolated PostgreSQL witness me execute karo: A claims → A effect commits → lease reclaim → B claims → A stale `UPDATE ... WHERE status='running'` marks succeeded while B is active → B repeats effect (dedup) → B terminal mark.
2. Record both truths separately:
   - effect safety survives: keyed effect count `1`;
   - ownership safety fails: A stale mark gets `rowcount=1`, B's later mark gets `rowcount=0`.
3. This is Week 4 input. No schema column, generation increment, or guarded production writer today.
4. Wording: dedup **narrows duplicate damage for current local keyed ledger effect**; it does not eliminate stale-owner state transitions.

**Executable end:** C8 artifact has `effect_count=1`, `stale_mark_rowcount=1`, `current_owner_mark_rowcount=0`, and a named action trace.

**KEY:** ab Q6 kholo.

## Step 9 — 10 min: cleanup, unchanged-evidence proof, and day-close inputs

**Terms used in this step**
- **Mutation sensitivity:** protection absent hone par same property red hui.
- **Known limit:** test ke quantified model/scope ke bahar ka claim.
- **Reconciliation:** historical evidence fingerprint before/after exact equality, sequences included.

1. C9 first isolated scenario summary query, then every child stop/terminate, disposable DB drop, absence proof.
2. Evidence DB must remain exactly `119 jobs / 107 executions / 9 effects`, max/jobs seq `125`, effect seq `12`, same status buckets/revision. Sequence equality is required because Din 5 writes evidence DB ko touch hi nahi karni thi.
3. Copy to `docs/logs/WEEK_03.md` Din 5 template:
   - morning and evening property wording;
   - configured examples and forced-redispatch count;
   - mutant command exit + shrunk counterexample verbatim;
   - Layer B three witnesses;
   - stale-mark/fencing trace;
   - known limits;
   - cleanup/fingerprint.
4. “What I Understood” apne words me. `D-24`/`D-25` publish mat karo; Din 6 owner.
5. Required known limits: finite generated model traces; model may omit production behavior; only 2–3 DB witnesses; current local non-null keyed ledger row only; external effects `[NO EVIDENCE]`; legacy `NULL` effects outside uniqueness; multiple legitimate effect kinds per job unsupported; no liveness under permanent crashes; no fencing/ownership guarantee.

**Executable end:** C9 test DB/process/artifact cleanup complete; evidence fingerprint byte-for-byte logical match; log has verbatim counterexample.

---

## Frozen prediction questions — Gemini ko paste mat karna

```text
Q1. Property “har job ka side effect count exactly 1” — boom wali job pe ye sach hai? dead_letter wali
    pe? To property ka scope kaise likhoge?

Q2. P-27 (bound cross karke ek extra dispatch) ke saath property = 1 maangegi ya <= 1? Inme se kaunsa
    asli contract hai?

Q3. Test jobs table ke 119 historical evidence rows ke against chalega. Kaunsi teen strategies hain isko
    isolate karne ki, aur unme se kaunsi historical evidence nahi todti aur real subprocess commits ko
    contain karti hai?

Q4. Dedup hata ke test chalao — test red hona chahiye. Agar wo green rehta hai, iska matlab kya hai?

Q5. Hypothesis shrink karke sabse chhota failing case deti hai. Wo case tumhare liye kis cheez ka sabse
    accurate description hai — bug ka, ya property ke wording/model boundary ka?

Q6. Property paas ho gayi bina fencing token ke. To fencing token kis cheez ke liye chahiye tha? Ek
    concrete interleaving likho jo dedup se bachta hai par fencing se rukta hai.
```

---

# Part B — Exact PowerShell verification commands C0–C9

All commands workspace root `d:\PROJECTS\relay` se PowerShell me. Native exit code mechanically check hota hai. C5–C9 **same main terminal** me run karo. Long-lived children C7 harness own karega; manual worker terminals allowed nahi, because cleanup and target proof harness contract ka part hain.

## C0 — frozen provenance + opening evidence fingerprint

Predictions file pehle likho, then:

```powershell
$answers='docs\daily\week_03\DIN_05_ANSWERS.md'
$frozen='docs\daily\week_03\DIN_05_PREDICTIONS_FROZEN.md'
if (-not (Test-Path $answers)) { throw 'Write all six predictions before C0' }
if (Test-Path $frozen) { throw 'Frozen file already exists; overwrite forbidden' }
Copy-Item $answers $frozen
Get-FileHash $frozen -Algorithm SHA256
New-Item -ItemType Directory -Force .din5-artifacts | Out-Null

$env:DATABASE_URL='postgresql+asyncpg://postgres:relay@localhost:5433/relay'
$runtimeDb=@(.\.venv\Scripts\python.exe -c "from src.database import engine; print(engine.url.database)")
if ($LASTEXITCODE -ne 0) { throw 'runtime target probe failed' }
$runtimeDb=($runtimeDb -join '').Trim()
if ($runtimeDb -ne 'relay') { throw "runtime database=$runtimeDb, expected relay" }

$evidenceSql=@'
select current_database()||'|'||count(*)||'|'||max(id)||'|'||(select last_value from jobs_id_seq)||'|'||(select count(*) from job_executions)||'|'||(select count(*) from side_effects)||'|'||(select last_value from side_effects_id_seq)||'|'||(select version_num from alembic_version) from jobs;
select status||'|'||count(*) from jobs group by status order by status;
select count(*) from jobs where next_attempt_at='infinity'::timestamptz;
select count(*) from pg_stat_activity where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
'@
$open=@($evidenceSql | docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'opening evidence SQL failed' }
$open | ForEach-Object { $_ }
if ($open[0].Trim() -ne 'relay|119|125|125|107|9|12|w3d4_enqueue_idempotency') { throw "opening fingerprint mismatch: $($open[0])" }
$expectedBuckets=@('dead_letter|3','failed|15','pending|4','succeeded|97')
if ((@($open[1..4]) -join ',') -ne ($expectedBuckets -join ',')) { throw "bucket mismatch: $($open[1..4])" }
if ($open[5].Trim() -ne '0' -or $open[6].Trim() -ne '0') { throw "opening infinity/idle mismatch: $($open[5]),$($open[6])" }

$relay=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'uvicorn|src\.(worker|reaper)|din5.*pg_witness' })
if ($relay.Count -ne 0) { $relay | Select-Object ProcessId,CommandLine; throw 'Relay/test process already running' }
$probeDbs=@("select count(*) from pg_database where datname like 'relay_din5_%';" |
  docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d postgres)
if ((($probeDbs -join '').Trim()) -ne '0') { throw "pre-existing Din 5 DBs: $probeDbs" }
"python_runtime_database=$runtimeDb evidence_fingerprint=$($open[0]) relay_processes=0 probe_dbs=0"
```

## C1 — property-card shape before code

Create `docs\daily\week_03\DIN_05_PROPERTY.md` with these exact field labels, then:

```powershell
$property='docs\daily\week_03\DIN_05_PROPERTY.md'
if (-not (Test-Path $property)) { throw 'Property wording must exist before test code' }
$raw=Get-Content $property -Raw
$required=@(
  '^Morning wording:',
  '^Logical identity:',
  '^Universe:',
  '^Safety:',
  '^Conditional exactness:',
  '^Completion evidence:',
  '^P-27 effect:',
  '^Layer A claim:',
  '^Layer A limit:',
  '^Layer B claim:',
  '^Layer B limit:',
  '^Isolation decision:',
  '^Mutation claim:',
  '^Mutation limit:'
)
foreach ($pattern in $required) {
  if ($raw -notmatch "(?m)$pattern\s*\S+") { throw "missing/blank property field: $pattern" }
}
if ($raw -notmatch '(?m)^Safety:.*<=\s*1') { throw 'Safety must state an at-most-one predicate' }
if ($raw -notmatch '(?m)^Conditional exactness:.*=\s*1') { throw 'Conditional exactness must be separate' }
if ($raw -notmatch '(?mi)^Completion evidence:.*(absent|unavailable|none|nahi)') { throw 'Current completion-evidence gap must be explicit' }
if ($raw -match '(?mi)^Layer A claim:.*(real[- ]world|production).*(prove|all|every)') { throw 'Layer A overclaims real schedules' }
"property_contract_fields=$($required.Count) safety_and_conditional_exactness_separate=True"
```

Expected one summary line, no test file required yet.

## C2 — deterministic model controls

After writing `tests\din5\test_model.py`:

```powershell
.\.venv\Scripts\python.exe -m py_compile tests\din5\test_model.py
if ($LASTEXITCODE -ne 0) { throw 'model compile failed' }
$nodes=@(
  'tests/din5/test_model.py::test_zero_writes_has_zero_effects',
  'tests/din5/test_model.py::test_one_dispatch_one_effect',
  'tests/din5/test_model.py::test_reclaim_two_dispatches_one_effect',
  'tests/din5/test_model.py::test_p27_extra_dispatch_preserves_safety'
)
.\.venv\Scripts\python.exe -m pytest @nodes -q -s
if ($LASTEXITCODE -ne 0) { throw 'deterministic controls failed' }
```

Expected: four named nodes pass. The reclaim and P-27 tests must include an assertion `dispatches >= 2`; effect count alone is decorative.

## C3 — Hypothesis green run + redispatch coverage artifact

```powershell
Remove-Item Env:DIN5_MUTANT -ErrorAction SilentlyContinue
$green='.din5-artifacts\model-green.json'
$env:DIN5_MODEL_ARTIFACT=$green
try {
  .\.venv\Scripts\python.exe -m pytest `
    tests/din5/test_model.py::test_all_action_sequences_preserve_effect_safety `
    tests/din5/test_model.py::test_redispatch_sequences_preserve_effect_safety `
    -q -s --hypothesis-show-statistics
  if ($LASTEXITCODE -ne 0) { throw 'normal Hypothesis run failed' }
} finally {
  Remove-Item Env:DIN5_MODEL_ARTIFACT -ErrorAction SilentlyContinue
}
if (-not (Test-Path $green)) { throw 'model green artifact missing' }
$g=Get-Content $green -Raw | ConvertFrom-Json
if ($g.mode -ne 'dedup_on') { throw "mode=$($g.mode)" }
if ([int]$g.all_sequence_examples -ne 200) { throw "all examples=$($g.all_sequence_examples)" }
if ([int]$g.redispatch_examples -ne 100) { throw "redispatch examples=$($g.redispatch_examples)" }
if ([int]$g.redispatch_examples_with_two_or_more_dispatches -ne 100) { throw 'forced redispatch coverage missing' }
if ([int]$g.max_dispatches_observed -lt 2 -or [int]$g.safety_failures -ne 0) { throw 'green artifact assertions failed' }
$g | Format-List
```

Expected artifact shape:

```text
mode                                      dedup_on
all_sequence_examples                     200
redispatch_examples                       100
redispatch_examples_with_two_or_more_dispatches 100
max_dispatches_observed                   >=2
safety_failures                           0
```

## C4 — mutation must be RED, shrink, then normal control GREEN

```powershell
$mutantOut='.din5-artifacts\mutation-output.txt'
$env:DIN5_MUTANT='no_dedup'
try {
  & .\.venv\Scripts\python.exe -m pytest `
    tests/din5/test_model.py::test_redispatch_sequences_preserve_effect_safety `
    -vv -s --tb=short 2>&1 | Tee-Object -FilePath $mutantOut
  $mutantExit=$LASTEXITCODE
} finally {
  Remove-Item Env:DIN5_MUTANT -ErrorAction SilentlyContinue
}
if ($mutantExit -eq 0) { throw 'SURVIVING MUTANT: property stayed green without dedup' }
$mutantText=Get-Content $mutantOut -Raw
foreach ($needle in @('Falsifying example','shrunk_trace=','effect_count=2')) {
  if ($mutantText -notmatch [regex]::Escape($needle)) { throw "mutation output missing: $needle" }
}
"mutation_killed=True exit=$mutantExit"
Select-String -Path $mutantOut -Pattern 'Falsifying example|shrunk_trace=|effect_count=2'

.\.venv\Scripts\python.exe -m pytest `
  tests/din5/test_model.py::test_redispatch_sequences_preserve_effect_safety -q -s
if ($LASTEXITCODE -ne 0) { throw 'normal policy did not recover after mutation' }
"post_mutation_green=True"
```

Expected: mutant command non-zero; minimal trace names at least two legal effect-write boundaries separated by retry/reclaim; same node then passes without env mutation.

## C5 — create and migrate exact disposable DB

Run C5–C9 in this same terminal:

```powershell
$testDb="relay_din5_${PID}_$([guid]::NewGuid().ToString('N').Substring(0,8))"
if ($testDb -notmatch '^relay_din5_\d+_[0-9a-f]{8}$') { throw "unsafe DB name: $testDb" }
$testAsyncUrl="postgresql+asyncpg://postgres:relay@localhost:5433/$testDb"
$testSyncUrl="postgresql+psycopg://postgres:relay@localhost:5433/$testDb"
function Remove-Din5TestDb {
  if ($script:testDb -and $script:testDb -match '^relay_din5_\d+_[0-9a-f]{8}$') {
    $drop=@"
select pg_terminate_backend(pid) from pg_stat_activity where datname='$script:testDb' and pid<>pg_backend_pid();
drop database if exists $script:testDb;
"@
    $drop | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d postgres | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'Din 5 DB cleanup failed' }
  }
}

"create database $testDb;" | docker exec -i relay-db-1 psql -X -v ON_ERROR_STOP=1 -U postgres -d postgres
if ($LASTEXITCODE -ne 0) { throw 'test DB create failed' }
$env:DIN5_SYNC_URL=$testSyncUrl
$env:DIN5_EXPECTED_DB=$testDb
$migrate=@'
import os
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
url=os.environ["DIN5_SYNC_URL"]
expected=os.environ["DIN5_EXPECTED_DB"]
engine=create_engine(url)
try:
    with engine.connect() as c:
        actual=c.scalar(text("select current_database()"))
finally:
    engine.dispose()
if actual != expected:
    raise SystemExit(f"REFUSING TARGET expected={expected} actual={actual}")
print(f"din5_target_checked={actual}")
cfg=Config("alembic.ini")
cfg.set_main_option("sqlalchemy.url", url)
command.upgrade(cfg, "head")
'@
try {
  .\.venv\Scripts\python.exe -c $migrate
  if ($LASTEXITCODE -ne 0) { throw 'exact-target migration failed' }
} catch {
  Remove-Din5TestDb
  throw
} finally {
  Remove-Item Env:DIN5_SYNC_URL,Env:DIN5_EXPECTED_DB -ErrorAction SilentlyContinue
}
$shape=@("select current_database()||'|'||version_num||'|'||(select count(*) from jobs)||'|'||(select count(*) from job_executions)||'|'||(select count(*) from side_effects) from alembic_version;" |
  docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $testDb)
if ($LASTEXITCODE -ne 0) { Remove-Din5TestDb; throw 'test DB shape query failed' }
$shape=($shape -join '').Trim()
if ($shape -ne "$testDb|w3d4_enqueue_idempotency|0|0|0") { Remove-Din5TestDb; throw "test DB shape=$shape" }
$evidence=@("select count(*)||'|'||max(id)||'|'||(select count(*) from job_executions)||'|'||(select count(*) from side_effects) from jobs;" |
  docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ((($evidence -join '').Trim()) -ne '119|125|107|9') { Remove-Din5TestDb; throw "evidence changed before witnesses: $evidence" }
$env:DIN5_TEST_DATABASE_URL=$testAsyncUrl
"test_database_ready=$shape evidence=119|125|107|9"
```

## C6 — real baseline and concurrent witnesses

```powershell
if (-not $env:DIN5_TEST_DATABASE_URL -or -not $testDb) { throw 'Run C5 in this terminal first' }
.\.venv\Scripts\python.exe -m py_compile tests\din5\pg_witness.py
if ($LASTEXITCODE -ne 0) { throw 'witness harness compile failed' }

$baseFile='.din5-artifacts\pg-baseline.json'
$concurrentFile='.din5-artifacts\pg-concurrent.json'
.\.venv\Scripts\python.exe -u tests\din5\pg_witness.py --scenario baseline --output $baseFile
if ($LASTEXITCODE -ne 0) { throw 'baseline witness failed' }
.\.venv\Scripts\python.exe -u tests\din5\pg_witness.py --scenario concurrent --output $concurrentFile
if ($LASTEXITCODE -ne 0) { throw 'concurrent witness failed' }
$b=Get-Content $baseFile -Raw | ConvertFrom-Json
$c=Get-Content $concurrentFile -Raw | ConvertFrom-Json
if ($b.database -ne $testDb -or $b.scenario -ne 'baseline' -or [int]$b.dispatches -ne 1 -or [int]$b.effects -ne 1) { throw 'baseline artifact mismatch' }
if ($c.database -ne $testDb -or $c.scenario -ne 'concurrent') { throw 'concurrent target/scenario mismatch' }
if ([int]$c.dispatches -ne 2 -or [int]$c.distinct_workers -ne 2 -or [int]$c.effects -ne 1) { throw 'concurrent count mismatch' }
if ((@($c.effect_rowcounts | Sort-Object) -join ',') -ne '0,1') { throw "effect verdicts=$($c.effect_rowcounts)" }
$b,$c | ConvertTo-Json -Depth 8
```

## C7 — real crash/reclaim/redispatch witness

```powershell
$crashFile='.din5-artifacts\pg-crash-reclaim.json'
.\.venv\Scripts\python.exe -u tests\din5\pg_witness.py --scenario crash_reclaim --output $crashFile
if ($LASTEXITCODE -ne 0) { throw 'crash/reclaim witness failed' }
$x=Get-Content $crashFile -Raw | ConvertFrom-Json
if ($x.database -ne $testDb -or $x.scenario -ne 'crash_reclaim') { throw 'crash target/scenario mismatch' }
if ($x.crash_kind -ne 'hard_process_exit' -or [int]$x.worker_a_exit_code -eq 0) { throw 'hard crash not proved' }
if ($x.pre_reclaim -ne 'running|1|1|1') { throw "pre_reclaim=$($x.pre_reclaim)" }
if ($x.reclaim_barrier -ne 'pending|1|true') { throw "reclaim_barrier=$($x.reclaim_barrier)" }
if ($x.final -ne 'succeeded|2|2|2|1') { throw "final=$($x.final)" }
if ([int]$x.replay_effect_rowcount -ne 0) { throw 'redispatch dedup verdict absent' }
if (@($x.child_pids).Count -lt 3 -or [int]$x.live_children_after_cleanup -ne 0) { throw 'process evidence/cleanup failed' }
$x | ConvertTo-Json -Depth 8
```

`final` fields: `status|attempts|executions|distinct_workers|effects`.

## C8 — fencing boundary witness, without implementation

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/din5/test_model.py::test_generation_blind_stale_mark_trace -q -s
if ($LASTEXITCODE -ne 0) { throw 'stale-mark model trace failed' }

$staleFile='.din5-artifacts\pg-stale-mark.json'
.\.venv\Scripts\python.exe -u tests\din5\pg_witness.py --scenario stale_mark --output $staleFile
if ($LASTEXITCODE -ne 0) { throw 'stale-mark PostgreSQL witness failed' }
$s=Get-Content $staleFile -Raw | ConvertFrom-Json
if ($s.database -ne $testDb -or $s.scenario -ne 'stale_mark') { throw 'stale target/scenario mismatch' }
if ([int]$s.dispatches -ne 2 -or [int]$s.effect_count -ne 1) { throw 'dedup side of stale witness failed' }
if ([int]$s.stale_mark_rowcount -ne 1 -or [int]$s.current_owner_mark_rowcount -ne 0) { throw 'generation blindness not reproduced' }
if ($s.trace -notmatch 'claim:A.*effect:A.*reclaim.*claim:B.*mark:A.*effect:B.*mark:B') { throw "trace lacks named interleaving: $($s.trace)" }
$s | ConvertTo-Json -Depth 8
```

Expected result is deliberately mixed: effect property green, ownership property red/currently unprotected.

## C9 — cleanup + exact evidence no-delta assertion

```powershell
try {
  $testSummary=@("select count(*)||'|'||(select count(*) from job_executions)||'|'||(select count(*) from side_effects) from jobs;" |
    docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d $testDb)
  if ($LASTEXITCODE -ne 0) { throw 'test summary query failed' }
  "disposable_summary=$(($testSummary -join '').Trim())"
} finally {
  Remove-Item Env:DIN5_TEST_DATABASE_URL -ErrorAction SilentlyContinue
  Remove-Din5TestDb
}
$remaining=@("select count(*) from pg_database where datname='$testDb';" |
  docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d postgres)
if ((($remaining -join '').Trim()) -ne '0') { throw 'Din 5 DB survived cleanup' }

$closeSql=@'
select count(*)||'|'||max(id)||'|'||(select last_value from jobs_id_seq)||'|'||(select count(*) from job_executions)||'|'||(select count(*) from side_effects)||'|'||(select last_value from side_effects_id_seq)||'|'||(select version_num from alembic_version) from jobs;
select status||'|'||count(*) from jobs group by status order by status;
select count(*) from jobs where next_attempt_at='infinity'::timestamptz;
select count(*) from pg_stat_activity where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
'@
$close=@($closeSql | docker exec -i relay-db-1 psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'closing evidence SQL failed' }
if ($close[0].Trim() -ne '119|125|125|107|9|12|w3d4_enqueue_idempotency') { throw "EVIDENCE DB CHANGED: $($close[0])" }
if ((@($close[1..4]) -join ',') -ne 'dead_letter|3,failed|15,pending|4,succeeded|97') { throw "closing bucket mismatch: $($close[1..4])" }
if ($close[5].Trim() -ne '0' -or $close[6].Trim() -ne '0') { throw 'closing infinity/idle mismatch' }
$relay=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'uvicorn|src\.(worker|reaper)|din5.*pg_witness' })
if ($relay.Count -ne 0) { $relay | Select-Object ProcessId,CommandLine; throw 'process survived C9' }
.\.venv\Scripts\python.exe -m pytest tests\din5 -q
if ($LASTEXITCODE -ne 0) { throw 'normal Din 5 suite not green at close' }
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'diff check failed' }
Get-FileHash docs\daily\week_03\DIN_05_PREDICTIONS_FROZEN.md -Algorithm SHA256
"closing_evidence=$($close[0]) test_db_remaining=0 relay_processes=0"

# First copy mutation-output/shrunk trace and JSON summaries into WEEK_03 log, then:
Remove-Item -Recurse -Force .din5-artifacts
```

---

# Part C — Discriminating expected shapes and output assertions

Every check asks: broken implementation bhi pass karegi kya? If yes, check incomplete hai.

| Check | Correct/mechanism present `[INFERRED until run]` | Broken/mechanism absent | Required discriminator |
|---|---|---|---|
| **C0 baseline** | Exact evidence fingerprint `119|125|125|107|9|12|head`; no process/DB | Historical rows altered or stale worker alive | Counts **plus** max/sequences/status buckets/revision/processes; total alone insufficient |
| **C1 wording** | Safety and conditional exactness separate; scope/completion gap explicit | “Every job exactly one effect” slogan | Required fields + `<=1` and conditional `=1`; no universal production proof claim |
| **C2 model control** | Redispatch/P-27 traces have `dispatches>=2`, effect `1` | Only one dispatch ever generated | Dispatch count asserted independently from effect count |
| **C3 random coverage** | `200` broad + `100` constructed redispatch examples; all redispatch examples reach `>=2` | Green due to rejected/vacuous examples | `redispatch_examples_with_two_or_more_dispatches=100`; configured count alone insufficient |
| **C4 mutation** | Same node non-zero; Hypothesis shrinks to semantic trace with `effect_count=2`; normal rerun green | Mutant stays green or mutant-only assertion fails | Same generator + same invariant, only policy switched; red then green control |
| **C5 isolation** | Exact disposable target starts empty; evidence fingerprint unchanged | Prefix/rollback fiction while subprocess writes `relay` | `current_database()` before migration/run + physical DB name + evidence no-delta |
| **C6 DB arbitration** | Two distinct sessions/workers, two dispatches, `{1,0}`, one row | Sequential luck/no second writer | Distinct worker IDs + two execution witnesses + verdict multiset + final count |
| **C7 crash/reclaim** | Hard exit; pre `running|1|1|1`; committed reclaim; final `succeeded|2|2|2|1`; replay `0` | Handler never redispatched or exception handled normally | Non-zero process exit + pre/barrier/final snapshots + child PID cleanup |
| **C8 fencing boundary** | Effect count `1`, stale A mark `1`, B mark `0` | Claim generations actually fenced, or duplicate never happened | Mixed result required: effect invariant passes while stale-owner update succeeds |
| **C9 cleanup** | Disposable DB gone; exact evidence sequences/counts unchanged; normal suite green | Test rows leaked/deleted, mutant env remained, child survived | `pg_database=0`, exact fingerprint, process count `0`, normal full suite |

### Expected semantic trace shapes

Normal exact action order is implementation-dependent, but these facts are mandatory:

```text
GREEN redispatch witness:
  claims/dispatches >= 2
  committed effect-write boundaries >= 2
  durable keyed effect rows = 1

RED no-dedup mutant (shrunk):
  one logical effect identity
  first legal committed effect-write
  retry/reclaim leading to another legal dispatch
  second committed effect-write
  durable effect count = 2

FENCING input:
  claim A -> effect A -> reclaim -> claim B -> stale mark A(rowcount=1)
  -> effect B(dedup, durable count=1) -> mark B(rowcount=0)
```

### Claims allowed after C9

- `[MEASURED]` The chosen deterministic model ran the recorded finite examples; forced-redispatch examples reached two dispatches; with dedup the model invariant held; without dedup the same property failed and shrank.
- `[MEASURED]` The disposable PostgreSQL witnesses reproduced baseline, concurrent duplicate, crash/reclaim redispatch, and stale-mark generation blindness with the recorded artifacts.
- `[INFERRED from model + witnesses]` Current non-null `effect_key` uniqueness narrows duplicate damage to at most one durable row for the current single local ledger effect identity.

### Claims forbidden after C9

- “Hypothesis mathematically proved every production interleaving.”
- “Exactly-once external effects are solved.”
- “Every succeeded job's handler completed exactly once.”
- “Fencing is unnecessary.”
- “Retries/dispatches are bounded to three.”
- “No duplicate execution happens.”
- “One effect row means duplicate execution did not happen.”

---

# Part D — Scope guard

| Aaj tempting kya hai | Owner | Aaj karne se kya khota hai |
|---|---|---|
| **Fencing token / claim-generation column + guarded writers** | **Week 4 build input** | C8 ka current generation-blind counterexample disappear hoga before being recorded; dedup vs ownership mechanisms mix honge |
| **Outbox table / dispatcher / relay loop** | Week 4 | Local ledger uniqueness, atomic intent, and remote delivery teen contracts ek test me mix ho jaayenge |
| **External SMTP/HTTP/payment exactly-once harness** | Week 4+ | Receiver cooperation/idempotency separate design hai; today's DB-row property usko prove nahi karti |
| **Auth / tenant-scoped idempotency / multi-tenancy** | Later month | Global key namespace ka current contract prematurely tenant model demand karega |
| **`completed_at` schema change** | `D-22` Cost 10, Week 4 decision/build | Aaj property ko missing completion evidence honestly expose karna hai, hole hide nahi |
| **`attempts < MAX_ATTEMPTS` claim gate** | Week 4 if chosen (`P-27`) | Accepted overdraft baseline badlega; property comparison non-comparable hogi |
| **Production `src/worker.py` mutation flag** | Never | Test-only fault injection production behavior/safety surface ban jaayegi |
| **Real 30 s sleeps in every Hypothesis example** | Rejected for Layer A | Scheduler/wall clock shrink input nahi; suite flaky and tiny hogi |
| **Rollback-only or key-prefix-only Layer B isolation** | Rejected today | Worker subprocess commits escape rollback; claim query prefix ignore karti hai |
| **Delete/reset the 119 evidence rows or sequences** | Never for test cleanup | Week chain and sequence evidence falsify ho jaayega |
| **Publish `D-24` / `D-25`** | Din 6 after same-day grep | Input ko premature final decision/provenance bana doge |
| **UI, cron, priorities, DAGs, metrics, Redis** | Future roadmap | Din 5 ka load-bearing property/mutation evidence dilute hota hai |

**Day is complete only when:** wording predates code; Layer A green has explicit redispatch coverage; no-dedup mutant is red and shrunk; normal rerun green; Layer B runs only in an exact disposable DB; stale mark is named as fencing input; disposable DB/processes/artifacts are removed; evidence DB remains exactly `119/107/9` at revision `w3d4_enqueue_idempotency`.