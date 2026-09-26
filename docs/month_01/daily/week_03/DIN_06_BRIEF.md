# Week 3 Din 6 BRIEF — close: reconcile, likho, handoff

**Week 3 · Din 6 · 2026-09-05** · Plan: [`../../planning/WEEK_03.md`](../../planning/WEEK_03.md) ·
Log: [`../../logs/WEEK_03.md`](../../logs/WEEK_03.md) · Sealed: [`DIN_06_KEY.md`](DIN_06_KEY.md)

**Aaj ka hard boundary:** no `src/` line, no migration, no database write, no new experiment. Din 1–5 ka
recorded evidence close, decisions, amendments, debt verdicts, and Week 4 handoff banta hai.

> **Paste rule:** Part A, Part C, and Part D Gemini ko ja sakte hain. **Part B kabhi nahi. KEY kabhi nahi.**
>
> **Seal rule:** saare seven answers Step 0 me freeze honge. Har KEY section tabhi khulega jab us section ka
> named command/output ya file-on-disk discriminator complete ho, aur output prediction se alag ho to pehle
> apni explanation likhi ho. `idk` valid hai aur `0` score karta hai.
>
> **Provenance rule:** is BRIEF ka recorded bench `[MEASURED-R]` hai—reviewer/user log se read hua, Din 6 ka
> fresh measurement nahi. C0/C1 ka actual output hi Din 6 log me `[MEASURED]` banega. Plausible value fill
> mat karna.

## Prediction seal gate — isko literally follow karo

Generation audit ne plan/log/register me stale assumptions detect kiye hain, but their outcomes intentionally
**Part B ke baad** rakhe gaye hain. Is point par unko reveal karna seven predictions ko reconstruction bana
dega.

1. Ab sirf Step 0 padho.
2. Editor outline se directly **Part B** par jump karo—Steps 1–9 aur Part C abhi mat padho.
3. Seven predictions likho, phir directly Step 0 ke **seal-only command** par return karo; Part C mat kholo.
4. Usi PowerShell terminal me seal-only command run karke frozen copy + printed hash banao.
5. Frozen hash banne ke baad Step 0 par return karke Part C ka C0 run karo; C0 pass ho tab Step 1 aur
   remaining Part A/Part C open hain.

Part A ko Gemini ko tabhi paste karna jab frozen hash already exists. This gate todne par affected questions
prediction score nahi karte; log me `seal broken` naam se jaata hai.

---

# Part A — Steps

## Step 0 — 10–15 min: freeze seven predictions, then take the opening/closing bench

**Terms used in this step**
- **Opening = closing bench:** writing-only day par first database read hi expected week-close state hai;
  baad me re-running until arithmetic matches forbidden hai.
- **Frozen prediction:** pre-output answer ka immutable copy and SHA-256; post-run explanation prediction
  credit nahi leti.
- **Evidence fingerprint:** database identity + row counts + sequence values + migration head ka compact
  tuple; wrong target ya stray writer ko detect karta hai.

1. `DIN_06_ANSWERS.md` banao. Part B ke exact seven questions copy karo. Exact structure:
   `## Q1` … `## Q7`, and under each exactly `### Prediction`, `### Observed + meri explanation`,
   `### After KEY`. Prediction non-empty (`idk` valid); last two bodies freeze time par empty.
2. Editor outline se direct Part B par jump karo; Step 1 ya Part C tab tak mat padho.
3. Predictions likhne ke baad yahin return karke neeche ka seal-only command **usi PowerShell terminal** me run karo.

### Step 0A — seal-only command (outcomes reveal nahi karta)

```powershell
$answers='docs\daily\week_03\DIN_06_ANSWERS.md'
$frozen='docs\daily\week_03\DIN_06_PREDICTIONS_FROZEN.md'
if (-not (Test-Path $answers)) { throw "Missing $answers" }
if (Test-Path $frozen) { throw "Frozen file already exists; overwrite forbidden: $frozen" }

$answerText=(Get-Content $answers -Raw) -replace "`r`n","`n"
if (-not $answerText.EndsWith("`n")) { $answerText += "`n" }
$qHeadings=[regex]::Matches($answerText,'(?m)^## Q(\d+)[ \t]*$')
$qIds=@($qHeadings | ForEach-Object { [int]$_.Groups[1].Value })
if (($qIds -join ',') -ne '1,2,3,4,5,6,7') {
  throw "Answers must contain exactly ordered ## Q1..## Q7 headings; got $($qIds -join ',')"
}

$briefText=(Get-Content docs\daily\week_03\DIN_06_BRIEF.md -Raw) -replace "`r`n","`n"
$questionFence=[regex]::Match($briefText,'(?ms)^# Part B\b.*?^```text[ \t]*\n(?<body>.*?)^```[ \t]*$')
if (-not $questionFence.Success) { throw 'Part B question fence missing from BRIEF' }
$expectedQuestions=[regex]::Matches($questionFence.Groups['body'].Value,'(?ms)^Q(?<id>[1-7])\.[ \t]+(?<question>.*?)(?=^Q[1-7]\.|\z)')
$expectedIds=@($expectedQuestions | ForEach-Object { [int]$_.Groups['id'].Value })
if ($expectedQuestions.Count -ne 7 -or ($expectedIds -join ',') -ne '1,2,3,4,5,6,7') {
  throw 'BRIEF must contain exactly ordered Q1..Q7 source questions'
}
function Normalize-Question([string]$value) {
  [regex]::Replace($value.Trim(),'\s+',' ')
}
$expectedById=@{}
foreach ($question in $expectedQuestions) {
  $expectedById[[int]$question.Groups['id'].Value]=Normalize-Question $question.Groups['question'].Value
}

$cards=[regex]::Matches($answerText,'(?ms)^## Q(?<id>[1-7])[ \t]*\n(?<question>.*?)^### Prediction[ \t]*\n(?<prediction>.*?)^### Observed \+ meri explanation[ \t]*\n(?<observed>.*?)^### After KEY[ \t]*\n(?<after>.*?)(?=^## Q[1-7][ \t]*$|\z)')
if ($cards.Count -ne 7) { throw "Expected 7 complete answer cards, got $($cards.Count)" }
$reconstructed=($cards | ForEach-Object { $_.Value }) -join ''
if ($reconstructed -cne $answerText) { throw 'Answers file may contain only the seven ordered cards' }
foreach ($card in $cards) {
  $id=[int]$card.Groups['id'].Value
  $actualQuestion=Normalize-Question $card.Groups['question'].Value
  if ($actualQuestion -cne $expectedById[$id]) { throw "Q$id text differs from BRIEF Part B" }
  $headings=@([regex]::Matches($card.Value,'(?m)^#{1,6}[ \t]+[^\r\n]*$') |
    ForEach-Object { $_.Value.TrimEnd() })
  $expectedHeadings=@("## Q$id",'### Prediction','### Observed + meri explanation','### After KEY')
  if (($headings -join "`n") -cne ($expectedHeadings -join "`n")) {
    throw "Q$id must contain exactly the three required subsection headings"
  }
  if (-not $card.Groups['prediction'].Value.Trim()) { throw "Q$id prediction empty; write idk if unknown" }
  if ($card.Groups['observed'].Value.Trim()) { throw "Q$id Observed block must be empty before freeze" }
  if ($card.Groups['after'].Value.Trim()) { throw "Q$id After KEY block must be empty before freeze" }
}

Copy-Item $answers $frozen
$sourceHash=(Get-FileHash $answers -Algorithm SHA256).Hash
$din6FrozenHash=(Get-FileHash $frozen -Algorithm SHA256).Hash
if ($sourceHash -ne $din6FrozenHash) { throw 'Frozen copy hash differs from source at freeze time' }
"DIN6_FROZEN_SHA256=$din6FrozenHash"
```

4. Printed hash record karo; answers/frozen ko C0 start hone tak edit mat karo. Ab **sirf Part C ka C0**
   kholo.
5. C0 ko same terminal me run karo; woh seal hash, exact runtime DB, commit, Relay processes, evidence
   fingerprint, five status buckets, pending IDs, infinity gates, idle transactions, and probe DBs assert karega.
6. Any mismatch par **stop**. Stray worker ko run karke state “repair” mat karna.
7. C0 pass hone ke baad Step 1 par jao; remaining Part A and Part C ab open hain.

**Executable end:** seal-only hash printed, then C0 prints `HEAD=616440b`; runtime DB `relay`; no Relay process;
exact C0 tuple on screen; no database write.

**KEY:** closed rakho. Opening output prediction answers nahi kholta.

## Step 1 — 10–15 min: build the five-day chain from database dates, not reports

**Terms used in this step**
- **Per-day attribution:** row ka database timestamp decides day; report prose nahi.
- **Compensating errors:** opposite daily mistakes final total me cancel ho sakti hain.
- **Safety counter:** physical durable rows; role/job summaries se alag quantity.

1. C1 ke UTC date groups run karo for jobs, executions, and side effects.
2. Week opening + five daily groups ko independent equations me write karo.
3. Date-group output ko each day’s report delta ke beside compare karo; any difference quantity/day ke saath
   name karo—report ko silently edit karke match mat banao.
4. Duplicate-effect and missing-ID discriminator outputs preserve karo; expected-looking history ko delete ya
   sequence reset mat karo.
5. Max ID, row count, and sequence ko independent facts ki tarah record karo.

**Executable end:** raw C1 output, four equations, report-vs-group comparison, duplicate list, and missing-ID
list Din 6 log me on disk hain.

**KEY:** output and own explanation ke baad **“Open after Step 1 / C1 — Q1 and reconciliation mathematics”**.

## Step 2 — 10 min: same-day heading audit; old heading never moves

**Terms used in this step**
- **Heading collision:** same numeric `D-`/`P-` heading more than once; citations do not count as headings.
- **Reserved number:** planned allocation, not proof that the number remains free.
- **Dangling citation:** referenced identifier with no defining heading.

1. C2 heading parser run karo; raw heading lines and parsed number lists log me paste karo.
2. Planned `D-24`, `D-25`, `P-28`, and `P-29` ko live heading counts against resolve karo.
3. Duplicate numeric heading count must be zero.
4. Collision par new intended entry moves/becomes an audit; existing heading never moves or duplicates.
5. Actual next-free D/P candidates output se derive and record karo.

**Executable end:** live register output, collision resolution, and next-free verdict exist before any heading
is written.

**KEY:** output ke baad **“Open after Step 2 / C2 — register collision answer”**.

## Step 3 — 15 min: resolve and publish the two uniqueness decisions

**Terms used in this step**
- **Enqueue identity:** one caller intent across API retries.
- **Execute identity:** one logical effect across worker deliveries/redispatches.
- **Database arbiter:** concurrent conflict ka verdict database constraint/index deta hai.

1. C2’s live collision result follow karo; planned number ko force mat karo.
2. Enqueue-vs-execute decision ko both measured case families, alternatives, costs, and rejected one-layer
   designs ke against write karo.
3. UNIQUE-vs-application-check deliverable ko live existing/new block me audit karo; measured race present hai
   ya nahi, exactly wahi provenance publish karo.
4. Existing P entries ko objective text se duplicate mat karo; current content against intended mechanisms
   audit karo.
5. Post-freeze checklist and C3 semantic/provenance gate run karo.

**Executable end:** collision-safe decision/problem headings, non-empty costs, measured-vs-inferred race
boundary, and C3 pass.

**KEY:** C3 ke baad **“Open after Step 3 / C3 — Q2/Q3 and two-layer mathematics”**.

## Step 4 — 10–15 min: append `D-03` and `D-05` amendments

**Terms used in this step**
- **Storage identity:** database row address; caller retry intent se separate concern.
- **Fingerprint:** key reuse ke content-change detector; identity by itself nahi.
- **Stable serialization:** stated input domain ke liye deterministic bytes; broader standard claim alag hai.

1. `D-03` me exact subheading `### Week 3 Din 6 amendment — D-03 (2026-09-05)` append karo.
2. Din 4 ne PK-vs-idempotency prediction ka kya confirm kiya and kya untouched chhoda—both evidence classes
   write karo.
3. `D-05` me exact subheading `### Week 3 Din 6 amendment — D-05 (2026-09-05)` append karo.
4. Fingerprint equality mechanism ko application serialization vs database storage normalization boundary ke
   saath correct karo; current guarantee and unchosen equivalence rules separate rakho.
5. C4a only these two **new amendment slices** inspect karega; historical tokens se pass nahi hoga.

**Executable end:** old decision lines unchanged; both dated amendment slices complete; C4a passes.

**KEY:** C4a ke baad **“Open after Step 4 / C4a — Q4, PK identity, and fingerprint mechanism”**.

## Step 5 — 15 min: append `D-21` and `D-22`; give overdue identity/completion debts an owner

**Terms used in this step**
- **Effect identity:** deliveries ko one logical effect me collapse karne wali identity.
- **Claim generation:** one ownership epoch ko another se distinguish karne wali monotonic identity.
- **Completion evidence:** durable invocation endpoint; dispatch start se distinct.
- **Fencing:** state write current generation present kare, stale generation reject ho.

1. `D-21` me exact subheading `### Week 3 Din 6 amendment — D-21 (2026-09-05)` append karo.
2. Effect identity, claim/execution identity, and completion evidence ko conflate kiye bina Din 5 property
   boundary and remaining owner write karo.
3. `D-22` me exact subheading `### Week 3 Din 6 amendment — D-22 (2026-09-05)` append karo.
4. `D-22` ke har claim ko source-specific provenance do; measured, reviewer-measured, inferred, and no-evidence
   labels output/source audit se decide karo—one blanket tag mat do.
5. C4b only new D-21/D-22 amendment slices inspect karega and exact missing evidence/owner require karega.

**Executable end:** old decision lines unchanged; both new amendment slices distinguish identity,
completion, fencing, and no-evidence boundaries; C4b passes.

**KEY:** C4b ke baad **“Open after Step 5 / C4b — Q5/Q6, property scope, and fencing boundary”**.

## Step 6 — 10–15 min: sync indexes, register truth, learning log, and current pointer

**Terms used in this step**
- **Index document:** address/navigation only; reasoning decision/problem entry me remains.
- **Next-free number:** live headings ke baad derived candidate.
- **Dangling pointer:** link to a file that does not exist.

1. `MAP.md` ko today’s live heading/amendment result se update karo; copied reasoning nahi.
2. `LEARNING_LOG.md` me Week 3 close, scores, open-item truth, and next-free numbers update karo.
3. `CURRENT_WEEK.md` ka stale day pointer close karo; nonexistent future file ka link mat invent karo.
4. `PROBLEMS.md` me live entries preserve karo; new number only genuinely new measured problem ke liye.
5. `DDIA_CH11_LINKS.md` audit karo: only user-derived reading links add; missing work ko DoD slip naam do.
6. Post-freeze checklist and C5 direct-on-disk gate run karo.

**Executable end:** C5 passes current identifiers, index/pointer truth, and no dangling future link.

**KEY:** C5 ke baad **“Open after Step 6 / C5 — sync and debt verdicts”**.

## Step 7 — 10–15 min: write `docs/daily/WEEK_03_HANDOFF.md`

**Terms used in this step**
- **What Stuck:** blank editor, no notes, scratch se rebuildable.
- **What Needs Reinforcement:** recognisable, but viva pressure me mechanism derive nahi hota.
- **Must Not Assume:** empirical baseline and open holes future week may not silently upgrade.

1. Both definitions file me write karo.
2. Exactly three unnumbered H2 headings use karo, prior handoff wording ke same pattern me.
3. First two sections user recall se classify karo; seed/KEY recognition ko “stuck” mat count karo.
4. Third section closing measurements, unresolved guarantees, and exact slipped evidence from post-freeze
   checklist se write karo.
5. C6 must inspect the third section itself, not merely tokens elsewhere in file.

**Executable end:** C6 exact heading/definition/content gate passes by reading ignored file from disk.

**KEY:** classification ke baad **“Open after Step 7 / C6 — Q7 and authorship boundary”**.

## Step 8 — 15 min: full DoD + carried-debt verdict, then complete Din 6 log

**Terms used in this step**
- **Deliberately deferred:** not done by choice, with a named future owner.
- **Slipped:** assigned scope was not completed, with exact evidence/work still required.
- **Partial:** outcome description, not a final disposition by itself.

1. Existing Din 6 DoD table ki every row ko actual evidence against classify karo.
2. Complete rows use exact status `met`; Markdown backticks allowed. Every other status gets exactly one of
   `deliberately deferred — owner ...` or `slipped — needs ...`.
3. Carried debts ko opening record against close/owner/slip do; silent carry forbidden.
4. Full Din 6 log shape fill karo, including correction table and frozen `/7` score.
5. `💡 What I Understood` user-authored hoga; existence ko authorship proof mat label karo.
6. C7 no-placeholder and disposition parser run karo.

**Executable end:** C7 finds no `____`; every incomplete DoD row has one valid disposition; score denominator
`/7` hai.

**KEY:** now open **“Final scoring rubric — frozen text only”** and grade. Post-run prose earns no prediction
credit.

## Step 9 — 10–15 min: final discriminators, cleanup, named-path commit

**Terms used in this step**
- **No-code delta:** `src/` and `alembic/` byte-level tracked diff remains empty.
- **Ignored documentation:** valid files hidden from `git status`; existence/content needs direct reads.
- **Closing fingerprint:** final DB read must equal Step 0 because Din 6 performs no database writes.

1. C8 run karo. Any DB tuple change, process, probe DB, idle transaction, or source/migration diff is a
   finding—do not repair by deleting evidence rows.
2. `git diff --check` and decision append-only check pass karo.
3. Open ignored `CURRENT_WEEK`, handoff, BRIEF/KEY, frozen answers, and Ch 11 links directly.
4. If committing, stage named tracked paths only; never `git add .`. Ignored files cannot be staged under the
   current repository policy and still must be verified on disk.
5. Record exact commit only after it exists; otherwise write `not committed`, not a placeholder hash.

**Executable end:** final C8 output equals C0; no temporary process/database/file; named tracked diff only;
commit truth recorded.

---

# Part B — Prediction questions — Gemini ko paste mat karna

> Step 0 me **all seven** answer and freeze karo. `idk` is valid and scores `0`. `idk — <correct answer>` is
> still `0`. Questions ke answers is block me nahi hain.

```text
Q1. Chain kis din pe tooti — ya jud gayi? Per-day delta report ki gin-ti se aaya ya database GROUP BY se?
    Dono me koi concrete farq nikla to exact quantity aur day likho.

Q2. D-24 ka answer “enqueue”, “execute”, ya “dono” hai? Agar “dono”, ek failure jo sirf enqueue layer
    rokti hai aur ek jo sirf execute layer rokti hai—identity ke saath naam se likho.

Q3. D-25 ke Rejected me application-level SELECT-then-INSERT ka measured number hai, ya sirf argument?
    Agar race reproduce nahi hui hoti, entry ko kya claim karna allowed hota?

Q4. D-03 ne kaha tha “PK aur idempotency key alag concerns hain.” Din 4 ne us prediction ka kaunsa hissa
    confirm kiya, aur kaunsa hissa touch hi nahi hua?

Q5. Property statement Din 5 ki subah se shaam tak exactly kis universe/predicate me badla? Change kis
    measured/source-audited absence ya counterexample boundary ki wajah se hua?

Q6. D-22 ka fencing-token evidence ab [INFERRED], [MEASURED], ya mixed hai? Din 5 ne exactly kya measure
    kiya, aur kaunsa dangerous ordering ab bhi [NO EVIDENCE] hai?

Q7. Iss hafte ka 💡 kis din reviewer ne likha? File record kya establish karta hai, aur authorship ke baare
    me kya mechanically prove nahi ho sakta?
```

---

# Part C — Verification commands and discriminators

All commands Windows PowerShell 7 syntax hain and repository root `d:\PROJECTS\relay` se run hote hain.
`docker compose` service name `db` use hota hai; project-name-dependent container name use nahi hota. SQL is
read-only. Any block with an assertion failure stops the step.

## C0 — frozen provenance + exact opening/closing bench

Seal-only command run hone ke baad, **usi PowerShell terminal** me:

```powershell
$answers='docs\daily\week_03\DIN_06_ANSWERS.md'
$frozen='docs\daily\week_03\DIN_06_PREDICTIONS_FROZEN.md'
if (-not (Test-Path $answers)) { throw "Missing $answers" }
if (-not (Test-Path $frozen)) { throw 'Run the Step 0A seal-only command before opening C0' }
if (-not $din6FrozenHash) { throw 'Step 0A hash variable missing; C0 must use the same PowerShell terminal' }

$sourceHash=(Get-FileHash $answers -Algorithm SHA256).Hash
$currentFrozenHash=(Get-FileHash $frozen -Algorithm SHA256).Hash
if ($currentFrozenHash -ne $din6FrozenHash) { throw 'Frozen predictions changed after Step 0A' }
if ($sourceHash -ne $currentFrozenHash) { throw 'Answers changed between Step 0A and C0' }
"DIN6_FROZEN_SHA256_UNCHANGED=$currentFrozenHash"

$head=(git rev-parse --short HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -ne '616440b') { throw "Unexpected HEAD: $head" }
"HEAD=$head"

$env:DATABASE_URL='postgresql+asyncpg://postgres:relay@localhost:5433/relay'
$runtimeDb=@(& .\.venv\Scripts\python.exe -c "from src.database import engine; print(engine.url.database)")
if ($LASTEXITCODE -ne 0) { throw 'Python runtime target probe failed' }
$runtimeDb=($runtimeDb -join '').Trim()
if ($runtimeDb -ne 'relay') { throw "Runtime DB mismatch: $runtimeDb" }
"python_runtime_database=$runtimeDb"

$relay=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper)|din5.*pg_witness' })
$relay | Select-Object ProcessId,ParentProcessId,CommandLine
if ($relay.Count -ne 0) { throw "Relay process count is $($relay.Count), expected 0" }
"relay_processes=0"

$sql=@'
set time zone 'UTC';
select concat_ws('|', current_database(), count(*), max(id),
  (select last_value from jobs_id_seq),
  (select count(*) from job_executions),
  (select count(*) from side_effects),
  (select last_value from side_effects_id_seq),
  (select version_num from alembic_version))
from jobs;
select concat_ws('|',
  count(*) filter (where status='succeeded'),
  count(*) filter (where status='failed'),
  count(*) filter (where status='pending'),
  count(*) filter (where status='dead_letter'),
  count(*) filter (where status='running'),
  count(*)) from jobs;
select coalesce(string_agg(id::text,',' order by id),'') || '|' || count(*)::text
  from jobs where status='pending';
select count(*) from pg_stat_activity
  where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select count(*) from jobs where next_attempt_at='infinity'::timestamptz;
select count(*) from pg_database where datname like 'relay_din%';
'@
$raw=@($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'C0 SQL failed' }
$actual=@($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$actual
$expected=@(
  'relay|119|125|125|107|9|12|w3d4_enqueue_idempotency',
  '97|15|4|3|0|119',
  '116,121,123,124|4',
  '0',
  '0',
  '0'
)
if (($actual -join "`n") -ne ($expected -join "`n")) {
  throw "C0 fingerprint mismatch.`nACTUAL:`n$($actual -join "`n")`nEXPECTED:`n$($expected -join "`n")"
}

git diff --exit-code -- src alembic
if ($LASTEXITCODE -ne 0) { throw 'Unstaged src/alembic delta exists' }
git diff --cached --exit-code -- src alembic
if ($LASTEXITCODE -ne 0) { throw 'Staged src/alembic delta exists' }
$codeUntracked=@(git ls-files --others --exclude-standard -- src alembic)
if ($codeUntracked.Count) { throw "Untracked src/alembic files exist: $($codeUntracked -join ', ')" }
$openingStatus=@(git status --porcelain=v1)
if ($openingStatus.Count) {
  $openingStatus
  throw 'C0 expects clean tracked/non-ignored opening state; resolve before Din 6'
}
'opening_git_scope=clean'
```

Expected six SQL lines exactly:

```text
relay|119|125|125|107|9|12|w3d4_enqueue_idempotency
97|15|4|3|0|119
116,121,123,124|4
0
0
0
```

## Post-freeze correction register and writing checklists

C0 has now validated exactly seven prediction cards and created the frozen hash. Generation-time repository
audit found `[MEASURED-R 2026-09-04]`:

1. `D-24` heading absent/reserved; same-day C2 confirmation ke baad publish.
2. `D-25` already exactly once exists; duplicate heading forbidden.
3. `P-28` and `P-29` already exactly once exist; next candidate only if needed is `P-30`.
4. Din 1 full effect-row delta is `+3`: Job 109 baseline `+1`, Job 110 duplicate `+2`; full chain uses
   `0+3+2+3+1+0=9`.
5. Din 5 remains `6.5/10`, partial: finite model + test-side SQL/harness evidence, not required current-worker
   two-process production-path proof.

C1/C2 re-read these; fresh output wins.

### Step 3 post-freeze publication checklist

- New D-24 chooses **both** layers and distinguishes caller retry identity from stable local effect identity.
- Name lost-ack/retry failure and lease-reclaim/redispatch failure separately.
- Preserve measured witnesses: Job 121 + one row + `Timeout/PgSleep`/`Lock/transactionid`; Job 125 + one job
  + two attempts/executions/workers + one effect.
- Costs include omitted/lost key, global caller namespace, retention-bound memory, winner latency,
  application-owned fingerprint pairing, serializer boundary, one effect kind/job, legacy NULLs, duplicate
  CPU, and external sink `[NO EVIDENCE]`.
- Every Cost/Rejected bullet is one physical line ending in exactly one provenance tag.
- Existing D-25 must retain named constraint, `ON CONFLICT`, constraint-free two-session final `2`, Din 3
  seam amendment, and local-vs-external boundary. If present, do not append generic duplicate prose.
- Existing P-28/P-29 are audited, not recreated. P-28’s assertion mitigates target risk; it does not unify
  config. P-29’s fresh reproduction validates mechanism, not missing original transcript.

### Step 4 post-freeze amendment checklist

- D-03 new slice: Jobs 116/121 same-key original identity; unkeyed Jobs 123/124 distinct; conflict sequence
  movement; retention-bound/no TTL; bigint-vs-UUID, multi-region, auth, client PK not retested.
- D-05 new slice: cleaned type + compact sorted payload; order equality and type/payload differentials;
  application serialization before/independent of `jsonb`; numeric/Unicode choices remain; payload equality
  is not caller intent.

### Step 5 post-freeze amendment checklist

- D-21 new slice: `job_executions` is pre-handler dispatch; no completion/generation; `effect_key` is correct
  effect identity and wrong claim identity; test-side witness boundary; per-dispatch generation + completion
  endpoint slipped to Week 4.
- D-22 new slice separates: Job 95 historical production mark; Din 5
  `stale_mark_rowcount=1/current_owner_mark_rowcount=0/effects=1` test-side predicate witness; live
  current-worker and stale-heartbeat-after-B ordering `[NO EVIDENCE]`; fencing unbuilt; `completed_at`
  slipped; 45 s + T=3 s `SIGBREAK` run still missing.

### Steps 6–8 post-freeze close checklist

- MAP/LEARNING_LOG use live next-free `D-26/P-30`; CURRENT_WEEK says Week 3 closed without linking absent
  `WEEK_04.md`; no fabricated Ch 11 reading links.
- Handoff third section names pending `116/121/123/124`, local-key-only guarantee, external `[NO EVIDENCE]`,
  no fencing/completion, attempts overdraft, Din 5 `6.5` test-side limit, production-path slip requiring
  disposable DB + **two real current `src.worker` processes + production transaction boundaries**, P-28,
  P-29, outbox absent, and missing 45 s shutdown run.
- DoD marks Din 5 production path `slipped — needs disposable-DB rerun with two real current src.worker
  processes and production transaction boundaries`, outbox `deliberately deferred — owner Week 4`, contract
  #2 narrowed only inside named boundary, identifier/completion and shutdown experiment slipped, and all
  older debts with actual close/owner/slip. `partial` alone is not a disposition.

## C1 — database-date reconciliation + duplicate/gap discriminators

```powershell
$sql=@'
set time zone 'UTC';
select 'jobs|'||created_at::date||'|'||count(*)
  from jobs where id>108 group by created_at::date order by created_at::date;
select 'exec|'||executed_at::date||'|'||count(*)
  from job_executions where job_id>108 group by executed_at::date order by executed_at::date;
select 'effect|'||created_at::date||'|'||count(*)
  from side_effects where job_id>108 group by created_at::date order by created_at::date;
select 'duplicate_effect_job|'||job_id||'|'||count(*)
  from side_effects group by job_id having count(*)>1 order by job_id;
select 'missing_job_ids|'||coalesce(string_agg(g.id::text,',' order by g.id),'')
  from generate_series(1,(select max(id) from jobs)) g(id)
  left join jobs j on j.id=g.id where j.id is null;
'@
$raw=@($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'C1 SQL failed' }
$actual=@($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$expected=@(
  'jobs|2026-08-31|2',
  'jobs|2026-09-01|2',
  'jobs|2026-09-02|3',
  'jobs|2026-09-03|5',
  'exec|2026-08-31|3',
  'exec|2026-09-01|3',
  'exec|2026-09-02|5',
  'exec|2026-09-03|2',
  'effect|2026-08-31|3',
  'effect|2026-09-01|2',
  'effect|2026-09-02|3',
  'effect|2026-09-03|1',
  'duplicate_effect_job|110|2',
  'missing_job_ids|79,117,118,119,120,122'
)
$actual
if (($actual -join "`n") -ne ($expected -join "`n")) {
  throw "C1 date-group/gap mismatch.`nACTUAL:`n$($actual -join "`n")`nEXPECTED:`n$($expected -join "`n")"
}

$jobsClose=107+2+2+3+5+0
$execClose=94+3+3+5+2+0
$effectClose=0+3+2+3+1+0
$statusClose=(89+2+2+3+1)+15+4+3+0
if ($jobsClose -ne 119 -or $execClose -ne 107 -or $effectClose -ne 9 -or $statusClose -ne 119) {
  throw 'Arithmetic chain failed'
}
"jobs:107+2+2+3+5+0=$jobsClose"
"executions:94+3+3+5+2+0=$execClose"
"effects:0+3+2+3+1+0=$effectClose"
"buckets:97+15+4+3+0=$statusClose"
```

## C2 — live heading parser and collision gate

```powershell
function Get-RegisterNumbers {
  param([string]$Path,[ValidateSet('D','P')][string]$Prefix)
  $pattern="^## $Prefix-(\d+)"
  @(Select-String -Path $Path -Pattern $pattern | ForEach-Object {
    if ($_.Line -match $pattern) { [int]$Matches[1] }
  })
}

$d=@(Get-RegisterNumbers 'docs\DECISIONS.md' 'D')
$p=@(Get-RegisterNumbers 'docs\PROBLEMS.md' 'P')
$dDup=@($d | Group-Object | Where-Object Count -gt 1)
$pDup=@($p | Group-Object | Where-Object Count -gt 1)
"D_HEADINGS=" + (($d | Sort-Object) -join ',')
"P_HEADINGS=" + (($p | Sort-Object) -join ',')
if ($dDup.Count -or $pDup.Count) { throw 'Duplicate D/P heading number exists' }
if (@($d | Where-Object { $_ -eq 24 }).Count -ne 0) { throw 'D-24 no longer free; stop and resolve' }
if (@($d | Where-Object { $_ -eq 25 }).Count -ne 1) { throw 'Expected exactly one existing D-25' }
if (@($p | Where-Object { $_ -eq 28 }).Count -ne 1) { throw 'Expected exactly one existing P-28' }
if (@($p | Where-Object { $_ -eq 29 }).Count -ne 1) { throw 'Expected exactly one existing P-29' }
'D24=free; D25=occupied-once; P28=occupied-once; P29=occupied-once; planned-next=D26/P30'

Select-String -Path docs\DECISIONS.md -Pattern '^## D-[0-9]+:'
Select-String -Path docs\PROBLEMS.md -Pattern '^## P-[0-9]+\b'
```

Expected parsed pre-edit numbers:

```text
D_HEADINGS=1,2,3,4,5,6,7,8,21,22,23,25
P_HEADINGS=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29
```

## C3 — D-24/D-25/P-28/P-29 semantic and provenance gates

Run after Step 3 edits:

```powershell
function Get-HeadingBlock {
  param([string]$Path,[string]$Prefix,[int]$Number)
  $text=(Get-Content $Path -Raw) -replace "`r`n","`n"
  $pattern="(?ms)^## $Prefix-$Number\b.*?(?=^## $Prefix-\d+\b|\z)"
  $m=[regex]::Match($text,$pattern)
  if (-not $m.Success) { throw "Missing $Prefix-$Number heading block in $Path" }
  $m.Value
}

$d24=Get-HeadingBlock 'docs\DECISIONS.md' 'D' 24
$d25=Get-HeadingBlock 'docs\DECISIONS.md' 'D' 25
$p28=Get-HeadingBlock 'docs\PROBLEMS.md' 'P' 28
$p29=Get-HeadingBlock 'docs\PROBLEMS.md' 'P' 29

$dNums=@(Select-String docs\DECISIONS.md -Pattern '^## D-(\d+):' | ForEach-Object {
  if ($_.Line -match '^## D-(\d+):') { [int]$Matches[1] }
})
$pNums=@(Select-String docs\PROBLEMS.md -Pattern '^## P-(\d+)\b' | ForEach-Object {
  if ($_.Line -match '^## P-(\d+)') { [int]$Matches[1] }
})
if (@($dNums | Where-Object { $_ -eq 24 }).Count -ne 1) { throw 'D-24 heading count must be 1' }
if (@($dNums | Where-Object { $_ -eq 25 }).Count -ne 1) { throw 'D-25 heading count must remain 1' }
if (@($pNums | Where-Object { $_ -eq 28 }).Count -ne 1 -or
    @($pNums | Where-Object { $_ -eq 29 }).Count -ne 1) { throw 'P-28/P-29 heading count changed' }

foreach ($section in @('**Problem:**','**Options:**','**Chose:**','**Evidence:**','**Cost:**','**Rejected:**','**Revisit when:**')) {
  if (-not $d24.Contains($section)) { throw "D-24 missing $section" }
}
foreach ($token in @('enqueue','execute','Job 121','Job 125','uq_jobs_idempotency_key',
                      'uq_side_effects_effect_key','retention','external')) {
  if ($d24 -notmatch [regex]::Escape($token)) { throw "D-24 missing discriminator: $token" }
}

$cost=[regex]::Match($d24,'(?ms)^\*\*Cost:\*\*\s*(.*?)(?=^\*\*Rejected:\*\*)').Groups[1].Value
$rejected=[regex]::Match($d24,'(?ms)^\*\*Rejected:\*\*\s*(.*?)(?=^\*\*Revisit when:\*\*)').Groups[1].Value
$tagPattern='\[(?:MEASURED|MEASURED-R|INFERRED|NO EVIDENCE)\]'
$provenanceLines=@(($cost -split "`n") + ($rejected -split "`n") |
  Where-Object { $_ -match '^\s*(?:-|\d+\.)\s+' })
if ($provenanceLines.Count -eq 0) { throw 'D-24 Cost/Rejected has no checkable bullet lines' }
foreach ($line in $provenanceLines) {
  $tags=[regex]::Matches($line,$tagPattern)
  if ($tags.Count -ne 1) { throw "D-24 line needs exactly one provenance tag: $line" }
}

foreach ($token in @('uq_side_effects_effect_key','ON CONFLICT','SELECT','constraint-free','`2`')) {
  if ($d25 -notmatch [regex]::Escape($token)) { throw "Existing D-25 missing measured-race discriminator: $token" }
}
if ($p28 -notmatch 'current_database' -or $p28 -notmatch 'sqlalchemy\.url') {
  throw 'P-28 target-assertion mechanism missing'
}
if ($p29 -notmatch 'final row' -or $p29 -notmatch 'negative-control') {
  throw 'P-29 evidence-retention mechanism missing'
}
'D24/D25/P28/P29 semantic gates passed'
```

## C4a — append-only D-03/D-05 amendment slices

```powershell
$unstagedNumstat=@(git diff --numstat -- docs\DECISIONS.md)
if ($LASTEXITCODE -ne 0) { throw 'Unstaged DECISIONS.md numstat failed' }
$stagedNumstat=@(git diff --cached --numstat -- docs\DECISIONS.md)
if ($LASTEXITCODE -ne 0) { throw 'Staged DECISIONS.md numstat failed' }
function Assert-AppendOnlyNumstat([string]$name,[string[]]$lines) {
  foreach ($line in $lines) {
    $m=[regex]::Match($line,'^(?<added>\d+)\t(?<deleted>\d+)\t')
    if (-not $m.Success) { throw "$name DECISIONS.md numstat is not text: $line" }
    if ([int64]$m.Groups['deleted'].Value -ne 0) {
      throw "$name DECISIONS.md is not append-only: $line"
    }
  }
}
Assert-AppendOnlyNumstat 'Unstaged' $unstagedNumstat
Assert-AppendOnlyNumstat 'Staged' $stagedNumstat

function Get-DecisionBlock([int]$n) {
  $id='{0:D2}' -f $n
  $t=(Get-Content docs\DECISIONS.md -Raw) -replace "`r`n","`n"
  $m=[regex]::Match($t,"(?ms)^## D-$id\b.*?(?=^## D-\d+\b|\z)")
  if (-not $m.Success) { throw "Missing D-$id" }
  $m.Value
}
function Get-NewAmendment([int]$n) {
  $id='{0:D2}' -f $n
  $block=Get-DecisionBlock $n
  $pattern="(?ms)^### Week 3 Din 6 amendment — D-$id \(2026-09-05\)[ \t]*\n(?<body>.*?)(?=^### |\z)"
  $m=[regex]::Match($block,$pattern)
  if (-not $m.Success) { throw "Missing exact new amendment heading/body for D-$id" }
  $m.Groups['body'].Value
}
function Assert-AmendmentTokens([string]$name,[string]$body,[string[]]$tokens) {
  foreach ($token in $tokens) {
    if ($body -notmatch [regex]::Escape($token)) { throw "$name new amendment missing: $token" }
  }
}

$a03=Get-NewAmendment 3
$a05=Get-NewAmendment 5
Assert-AmendmentTokens 'D-03' $a03 @('Job 116','Job 121','123','124','jobs_id_seq','retention','TTL','UUID','multi-region','authorization')
Assert-AmendmentTokens 'D-05' $a05 @('sort_keys','separators','jsonb','Unicode','numeric','unkeyed')
foreach ($pair in @(@('D-03',$a03),@('D-05',$a05))) {
  if ($pair[1] -notmatch '\[(?:MEASURED|MEASURED-R)\]' -or $pair[1] -notmatch '\[INFERRED\]') {
    throw "$($pair[0]) new amendment must distinguish measured and inferred claims"
  }
}
'D-03/D-05 new amendment slices passed'
```

## C4b — append-only D-21/D-22 amendment slices

```powershell
$unstagedNumstat=@(git diff --numstat -- docs\DECISIONS.md)
if ($LASTEXITCODE -ne 0) { throw 'Unstaged DECISIONS.md numstat failed' }
$stagedNumstat=@(git diff --cached --numstat -- docs\DECISIONS.md)
if ($LASTEXITCODE -ne 0) { throw 'Staged DECISIONS.md numstat failed' }
function Assert-AppendOnlyNumstat([string]$name,[string[]]$lines) {
  foreach ($line in $lines) {
    $m=[regex]::Match($line,'^(?<added>\d+)\t(?<deleted>\d+)\t')
    if (-not $m.Success) { throw "$name DECISIONS.md numstat is not text: $line" }
    if ([int64]$m.Groups['deleted'].Value -ne 0) {
      throw "$name DECISIONS.md is not append-only: $line"
    }
  }
}
Assert-AppendOnlyNumstat 'Unstaged' $unstagedNumstat
Assert-AppendOnlyNumstat 'Staged' $stagedNumstat

function Get-DecisionBlock([int]$n) {
  $id='{0:D2}' -f $n
  $t=(Get-Content docs\DECISIONS.md -Raw) -replace "`r`n","`n"
  $m=[regex]::Match($t,"(?ms)^## D-$id\b.*?(?=^## D-\d+\b|\z)")
  if (-not $m.Success) { throw "Missing D-$id" }
  $m.Value
}
function Get-NewAmendment([int]$n) {
  $id='{0:D2}' -f $n
  $block=Get-DecisionBlock $n
  $pattern="(?ms)^### Week 3 Din 6 amendment — D-$id \(2026-09-05\)[ \t]*\n(?<body>.*?)(?=^### |\z)"
  $m=[regex]::Match($block,$pattern)
  if (-not $m.Success) { throw "Missing exact new amendment heading/body for D-$id" }
  $m.Groups['body'].Value
}
function Assert-AmendmentTokens([string]$name,[string]$body,[string[]]$tokens) {
  foreach ($token in $tokens) {
    if ($body -notmatch [regex]::Escape($token)) { throw "$name new amendment missing: $token" }
  }
}

$a21=Get-NewAmendment 21
$a22=Get-NewAmendment 22
Assert-AmendmentTokens 'D-21' $a21 @('job_executions','effect_key','claim generation','completed_at','test-side','production','slipped','Week 4')
Assert-AmendmentTokens 'D-22' $a22 @('Job 95','rowcount=1','stale_mark_rowcount','current_owner_mark_rowcount','effects=1','test-side','production','stale heartbeat','NO EVIDENCE','unbuilt','completed_at','SIGBREAK','slipped','Week 4')
if ($a22 -notmatch '\[(?:MEASURED|MEASURED-R)\]' -or $a22 -notmatch '\[NO EVIDENCE\]' -or $a22 -notmatch '\[INFERRED\]') {
  throw 'D-22 new amendment must contain measured, inferred, and no-evidence classes'
}
'D-21/D-22 new amendment slices passed'
```

If an honest equivalent uses different literals, update the relevant token and record why in the Din 6 log;
do not add awkward prose only for grep.

## C5 — index/current-pointer/register sync

```powershell
$map=Get-Content docs\MAP.md -Raw
$learning=Get-Content docs\LEARNING_LOG.md -Raw
$current=Get-Content docs\roadmap\CURRENT_WEEK.md -Raw
$problems=Get-Content docs\PROBLEMS.md -Raw

foreach ($token in @('D-24','D-25','P-28','P-29','D-26','P-30')) {
  if ($map -notmatch [regex]::Escape($token)) { throw "MAP missing $token" }
}
foreach ($token in @('Week 3','6.5','D-26','P-30')) {
  if ($learning -notmatch [regex]::Escape($token)) { throw "LEARNING_LOG missing $token" }
}
if ($current -match '(?is)next executable day.*Din 5|Din 5 template is next') {
  throw 'CURRENT_WEEK still points at Din 5'
}
if ($current -notmatch '(?im)^.*Week 3\b.*\bclosed\b.*$') {
  throw 'CURRENT_WEEK does not contain a direct Week 3 closed statement'
}
if ($current -match 'WEEK_04\.md' -and -not (Test-Path docs\planning\WEEK_04.md)) {
  throw 'CURRENT_WEEK links to absent WEEK_04.md'
}
if (@([regex]::Matches($problems,'(?m)^## P-28\b')).Count -ne 1 -or
    @([regex]::Matches($problems,'(?m)^## P-29\b')).Count -ne 1) {
  throw 'P-28/P-29 must each remain one heading'
}
'MAP/LEARNING_LOG/CURRENT_WEEK/register sync passed'
```

## C6 — handoff exact-heading and boundary gate

```powershell
$handoff='docs\daily\WEEK_03_HANDOFF.md'
if (-not (Test-Path $handoff)) { throw 'WEEK_03_HANDOFF.md missing' }
$text=Get-Content $handoff -Raw
$heads=@(Select-String -Path $handoff -Pattern '^## ' | ForEach-Object { $_.Line })
$expectedHeads=@('## What Stuck','## What Needs Reinforcement','## What Week 4 Must Not Assume')
if (($heads -join "`n") -ne ($expectedHeads -join "`n")) {
  throw "Handoff headings mismatch: $($heads -join ' | ')"
}
foreach ($definition in @('Rebuildable from scratch with no notes','Recognisable, but not derivable under viva pressure')) {
  if ($text -notmatch [regex]::Escape($definition)) { throw "Handoff definition missing: $definition" }
}
$third=[regex]::Match(($text -replace "`r`n","`n"),'(?ms)^## What Week 4 Must Not Assume[ \t]*\n(?<body>.*)\z').Groups['body'].Value
if (-not $third) { throw 'What Week 4 Must Not Assume body missing' }
foreach ($token in @('116','121','123','124','fencing','completed_at','attempts','6.5','test-side','external','P-28','P-29','outbox','SIGBREAK','slipped')) {
  if ($third -notmatch [regex]::Escape($token)) { throw "Week 4 Must Not Assume missing: $token" }
}
$productionBoundary='disposable DB + two real current src.worker processes + production transaction boundaries'
$plainThird=$third -replace '[`*_]',''
if ($plainThird -notmatch [regex]::Escape($productionBoundary)) {
  throw "Week 4 Must Not Assume missing exact production rerun boundary: $productionBoundary"
}
'Handoff exact headings, definitions, and production-path boundary passed'
```

## C7 — Din 6 log completion + DoD disposition gate

```powershell
$log=(Get-Content docs\logs\WEEK_03.md -Raw) -replace "`r`n","`n"
$m=[regex]::Match($log,'(?ms)^## Din 6\b.*\z')
if (-not $m.Success) { throw 'Din 6 log block missing' }
$din6=$m.Value
if ($din6 -match '____') { throw 'Din 6 log still contains placeholder ____' }
if ($din6 -notmatch '(?i)self-check.*?/\s*7') { throw 'Din 6 frozen-answer score denominator /7 missing' }

$dod=[regex]::Match($din6,'(?ms)^### Definition of Done.*?(?=^### Week 3 handoff|^### Hafte ke process findings)').Value
if (-not $dod) { throw 'DoD audit block missing' }
$dodLines=@($dod -split "`n")
$headerIndexes=@(for ($i=0; $i -lt $dodLines.Count; $i++) {
  if ($dodLines[$i] -match '^\| Group \|') { $i }
})
if ($headerIndexes.Count -ne 1) { throw 'DoD table must contain exactly one Group header' }
$headerIndex=$headerIndexes[0]
$header=@($dodLines[$headerIndex].Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim() })
$expectedHeader=@('Group','DoD item','Status','Evidence','Untick ho to: deferred (owner) / slipped (kya chahiye)')
if (($header -join "`n") -cne ($expectedHeader -join "`n")) { throw 'DoD table header changed' }
if (($headerIndex + 1) -ge $dodLines.Count) { throw 'DoD table separator missing' }
$separator=@($dodLines[$headerIndex + 1].Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim() })
if ($separator.Count -ne 5 -or @($separator | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count) {
  throw 'DoD table separator malformed'
}
$rows=[System.Collections.Generic.List[string]]::new()
for ($i=$headerIndex + 2; $i -lt $dodLines.Count; $i++) {
  if ([string]::IsNullOrWhiteSpace($dodLines[$i])) { break }
  [void]$rows.Add($dodLines[$i])
}
if ($rows.Count -ne 48) { throw "Expected all 48 existing DoD rows contiguously; got $($rows.Count)" }
$groupCounts=@{'Build'=0;'Measured'=0;'Likha'=0;'Carried debt'=0}
foreach ($row in $rows) {
  if ($row -notmatch '^[ \t]*\|.*\|[ \t]*$') { throw "Malformed DoD row: $row" }
  $cells=@($row.Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim() })
  if ($cells.Count -ne 5) { throw "DoD row must have exactly five cells: $row" }
  $group=$cells[0]
  if ($group -notin @('Build','Measured','Likha','Carried debt')) {
    throw "Unknown DoD group; every row must be audited: $row"
  }
  $groupCounts[$group]++
  $status=$cells[2]
  $disposition=$cells[4]
  $complete=($status -ceq 'met' -or $status -ceq '`met`')
  if (-not $complete) {
    $deferred=$disposition -cmatch '^deliberately deferred[ \t]+—[ \t]+owner[ \t]+\S.*$'
    $slipped=$disposition -cmatch '^slipped[ \t]+—[ \t]+needs[ \t]+\S.*$'
    if (([int]$deferred + [int]$slipped) -ne 1) {
      throw "Incomplete DoD row needs exactly one complete disposition: $row"
    }
  }
}
$expectedGroupCounts=@{'Build'=20;'Measured'=12;'Likha'=7;'Carried debt'=9}
foreach ($group in $expectedGroupCounts.Keys) {
  if ($groupCounts[$group] -ne $expectedGroupCounts[$group]) {
    throw "DoD group count mismatch for ${group}: $($groupCounts[$group])"
  }
}
"DoD rows parsed=$($rows.Count); exact groups, statuses, and dispositions passed"
```

## C8 — final no-code/no-write close and ignored-file visibility

Run in the same PowerShell terminal as C0 so `$din6FrozenHash` remains available:

```powershell
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Unstaged whitespace/error-marker check failed' }
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'Staged whitespace/error-marker check failed' }
git diff --exit-code -- src alembic
if ($LASTEXITCODE -ne 0) { throw 'Unstaged src/alembic delta exists' }
git diff --cached --exit-code -- src alembic
if ($LASTEXITCODE -ne 0) { throw 'Staged src/alembic delta exists' }
$codeUntracked=@(git ls-files --others --exclude-standard -- src alembic)
if ($codeUntracked.Count) { throw "Untracked src/alembic files exist: $($codeUntracked -join ', ')" }

$head=(git rev-parse --short HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -ne '616440b') { throw "Unexpected closing HEAD: $head" }
"HEAD_UNCHANGED=$head"

$env:DATABASE_URL='postgresql+asyncpg://postgres:relay@localhost:5433/relay'
$runtimeDb=@(& .\.venv\Scripts\python.exe -c "from src.database import engine; print(engine.url.database)")
if ($LASTEXITCODE -ne 0) { throw 'Closing Python runtime target probe failed' }
$runtimeDb=($runtimeDb -join '').Trim()
if ($runtimeDb -ne 'relay') { throw "Closing runtime DB mismatch: $runtimeDb" }
"python_runtime_database_unchanged=$runtimeDb"

if (-not $din6FrozenHash) { throw 'C0 frozen hash variable missing; compare with recorded opening hash manually' }
$finalHash=(Get-FileHash docs\daily\week_03\DIN_06_PREDICTIONS_FROZEN.md -Algorithm SHA256).Hash
if ($finalHash -ne $din6FrozenHash) { throw 'Frozen predictions changed' }
"DIN6_FROZEN_SHA256_UNCHANGED=$finalHash"

$relay=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '(?i)uvicorn|src\.(worker|reaper)|din5.*pg_witness' })
if ($relay.Count) { $relay | Select-Object ProcessId,CommandLine; throw 'Relay process survived close' }

$sql=@'
select concat_ws('|', current_database(), count(*), max(id),
  (select last_value from jobs_id_seq),
  (select count(*) from job_executions),
  (select count(*) from side_effects),
  (select last_value from side_effects_id_seq),
  (select version_num from alembic_version)) from jobs;
select concat_ws('|',
  count(*) filter (where status='succeeded'),
  count(*) filter (where status='failed'),
  count(*) filter (where status='pending'),
  count(*) filter (where status='dead_letter'),
  count(*) filter (where status='running'),
  count(*)) from jobs;
select coalesce(string_agg(id::text,',' order by id),'') || '|' || count(*)::text
  from jobs where status='pending';
select count(*) from pg_stat_activity
  where pid<>pg_backend_pid() and datname='relay' and state='idle in transaction';
select count(*) from jobs where next_attempt_at='infinity'::timestamptz;
select count(*) from pg_database where datname like 'relay_din%';
'@
$raw=@($sql | docker compose exec -T db psql -X -Atq -v ON_ERROR_STOP=1 -U postgres -d relay)
if ($LASTEXITCODE -ne 0) { throw 'Final SQL failed' }
$actual=@($raw | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
$expected=@(
  'relay|119|125|125|107|9|12|w3d4_enqueue_idempotency',
  '97|15|4|3|0|119',
  '116,121,123,124|4',
  '0',
  '0',
  '0'
)
$actual
if (($actual -join "`n") -ne ($expected -join "`n")) { throw 'Final C0-equivalent fingerprint differs' }

$ignored=@(
  'docs\roadmap\CURRENT_WEEK.md',
  'docs\daily\WEEK_03_HANDOFF.md',
  'docs\daily\week_03\DIN_06_BRIEF.md',
  'docs\daily\week_03\DIN_06_KEY.md',
  'docs\daily\week_03\DIN_06_ANSWERS.md',
  'docs\daily\week_03\DIN_06_PREDICTIONS_FROZEN.md',
  'docs\ddia_summaries\DDIA_CH11_LINKS.md'
)
foreach ($path in $ignored) {
  if (-not (Test-Path $path)) { throw "Ignored required file missing: $path" }
  if ((Get-Item $path).Length -eq 0) { throw "Ignored required file empty: $path" }
  $ignoreResult=@(git check-ignore -v -- $path)
  if ($LASTEXITCODE -ne 0) { throw "Expected ignored path is not ignored: $path" }
  $ignoreResult
}

$contentChecks=@{
  'docs\roadmap\CURRENT_WEEK.md'='(?im)^.*Week 3\b.*\bclosed\b.*$'
  'docs\daily\WEEK_03_HANDOFF.md'='(?m)^## What Week 4 Must Not Assume$'
  'docs\daily\week_03\DIN_06_BRIEF.md'='(?ms)^# Part A .*^# Part B .*^# Part C .*^# Part D '
  'docs\daily\week_03\DIN_06_KEY.md'='(?m)^# Final scoring rubric — frozen text only$'
  'docs\daily\week_03\DIN_06_PREDICTIONS_FROZEN.md'='(?m)^## Q7[ \t]*$'
  'docs\ddia_summaries\DDIA_CH11_LINKS.md'='(?m)^# '
}
foreach ($path in $contentChecks.Keys) {
  $body=Get-Content $path -Raw
  if ($body -notmatch $contentChecks[$path]) { throw "Required on-disk content missing: $path" }
}

$allowedTracked=@(
  'docs/DECISIONS.md',
  'docs/PROBLEMS.md',
  'docs/MAP.md',
  'docs/LEARNING_LOG.md',
  'docs/logs/WEEK_03.md'
)
$changed=@(@(git diff --name-only) + @(git diff --cached --name-only) | Sort-Object -Unique)
$unexpected=@($changed | Where-Object { $_ -notin $allowedTracked })
if ($unexpected.Count) { throw "Unexpected tracked Din 6 paths: $($unexpected -join ', ')" }
foreach ($required in @('docs/DECISIONS.md','docs/MAP.md','docs/LEARNING_LOG.md','docs/logs/WEEK_03.md')) {
  if ($required -notin $changed) { throw "Required tracked Din 6 update missing: $required" }
}
$untracked=@(git ls-files --others --exclude-standard)
if ($untracked.Count) { throw "Unexpected non-ignored untracked paths: $($untracked -join ', ')" }
"tracked_scope=" + ($changed -join ',')
git status --short
```

If committing after all gates:

```powershell
git add docs\DECISIONS.md docs\PROBLEMS.md docs\MAP.md docs\LEARNING_LOG.md docs\logs\WEEK_03.md
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'Staged diff check failed' }
git diff --cached --name-only
# Review the named list, then commit. Never use: git add .
```

## Differential matrix — decorative checks forbidden

| Gate | Broken state that a weak check would accept | Discriminator above |
|---|---|---|
| Step 0A | Six/eight questions, changed wording, extra headings, or post-filled observation frozen as “predictions” | pre-outcome seal command does exact BRIEF question/card comparison before copying and hashing |
| C0 | Correct counts from wrong runtime DB | direct SQL `current_database()` **and** Python `engine.url.database` |
| C0/C8 | Arithmetic clean while worker remains alive | OS process query + DB cleanup, both ends of day |
| C1 | Final total right with wrong daily attribution | UTC date groups for all three tables |
| C1 | `effects=9` but a new duplicate replaced another row | exact `HAVING count(*)>1` result = Job 110 only |
| C1 | `max(id)=125` treated as 125 rows | row count, max, sequence, and missing-ID list separately |
| C2 | Citation text mistaken for occupied heading | heading-anchored numeric parser + duplicate groups |
| C3 | Second D-25/P-28/P-29 heading silently added | exact heading count = one |
| C3 | D-24 says “both” without failure-domain evidence | Job 121 + Job 125 + both named constraints required |
| C3 | Application race rejected by opinion | existing D-25 must retain constraint-free final `2` |
| C4a/C4b | Staged/unstaged rewrite, any-content deletion, or old-token borrowing passes as an “amendment” | both `--numstat` deletion counts must be zero + exact zero-padded dated slice extraction |
| C4a | `jsonb` falsely credited for HTTP fingerprint | new D-05 slice must name app serialization and numeric/Unicode choices |
| C4b | Fencing amendment omits production boundary | new D-22 slice requires Job 95, test-side, production, stale heartbeat, and all evidence tags |
| C5 | `git status` clean while ignored docs are stale | direct `Get-Content`/`Test-Path` plus stale-pointer assertions |
| C6 | Correct headings but incomplete production rerun boundary | exact three H2 lines + exact disposable-DB/current-worker/transaction-boundary phrase |
| C7 | Missing/malformed row, alias status, bare disposition, or mistyped group escapes audit | exact contiguous 48 rows + group counts; only `met`; otherwise exact owner/needs disposition |
| C8 | Din 6 “close” mutates a bucket/fixture but keeps totals | full C0 tuple, five buckets, and pending IDs repeat exactly |
| C8 | Runtime target or baseline commit changes after C0 | Python DB probe and exact `HEAD=616440b` repeated at close |
| C8 | Unstaged check clean while staged/untracked code changed | unstaged + staged diffs and untracked `src/alembic` list all empty |
| C8 | Allowed docs plus unrelated tracked file changed | final changed-path set must be a subset of five named tracked docs |

---

# Part D — Scope guard

## Explicitly not built today

| Temptation | Why not today | Owner / exact next evidence |
|---|---|---|
| Fencing token / `claim_generation` | Schema + every claim/heartbeat/mark predicate changes; would contaminate close | Week 4 design; production ownership tests |
| `completed_at` or execution claim ID | New writers and migration; Din 6 only records missing need | Week 4 with fencing/observability design |
| Transactional outbox | Different atomicity problem; local intent does not eliminate remote redelivery | Deliberately deferred to Week 4 |
| Din 5 production-path Layer B rerun | It is a real experiment and would need disposable DB/process orchestration | Slipped; separate Week 4/catch-up measurement with two real current workers |
| Shutdown-vs-lease 45 s run | Would add execution/effect rows and mix measurement day into close | Slipped exact run: `slow {seconds:45}`, `SIGBREAK` T=3 s, worker+reaper, retained stdout |
| Alembic config unification | P-28 remains a code/config hardening item | Week 4 before next lifecycle probe |
| Idempotency TTL/retention worker | Changes dedup window and deletion policy | Week 4 retention decision |
| New handler, retry tuning, load test, auth, UI, cron, priorities, DAGs, multi-tenancy | Not Week 3 close and no current evidence need | Existing roadmap owners only |
| Week 4 implementation plan | No file exists and this day owns a handoff, not speculative plan generation | Separate planning session after close |
| `BACKEND_ROADMAP_PART2.md` | Month 1 not closed | Remains unopened |

## Evidence preservation rules

- Jobs/effects/executions are retained. Job 110's duplicate and sequence gaps are evidence, not dirt.
- Existing decisions are amended by appending. Earlier claims stay visible with their original provenance.
- Mitigations **narrow/reduce**; they do not become elimination claims.
- No `P-30` just to make a checklist look complete.
- No external exactly-once claim: current evidence is one non-null local Postgres ledger key.
- No “all interleavings” claim: Din 5 checked recorded finite model examples and selected test-harness SQL
  witnesses.
- No production-worker claim for Din 5 Layer B.
- No DB write is needed for a writing day. If a command would mutate rows/schema, it is out of scope.
