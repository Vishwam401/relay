# WEEK 6 · DIN 1 — `2026-09-30` — Log lines jo sach bolein: database khud `COMMIT` mana karega, aur fix ke baad pata chalega ki kaunsi ginti badli

**Budget `135 min` · Layer L2 · `src/` me paanch hafton me pehli edit — sirf teen files (`worker.py`, `reaper.py`,
`dispatcher.py`), aur un teeno me sirf `print` lines.** `main.py`, `database.py`, `sink.py`, `models.py`, `schemas.py`
ke hash Step 0 = Step 7. Koi SQL, koi sleep, koi retry, koi migration nahi badlega.

> **Din 5 ne `P-56` ek sanyog se pakda tha.** `35 s` outage ka `COMMIT` ek `~5 ms` window me gira, worker ne `Marked job 8
> as 'succeeded'` likha, aur wo kabhi sach nahi hua. `n = 1`, by phase, not by design.
>
> **Aaj wahi failure deterministic hai.** Ek disposable database me **deferred constraint triggers** chune hue `COMMIT`s
> ko mana karenge — har writer ka ek arm: claim, heartbeat, mark, reclaim, dispatch. Saath me **audit triggers** jinka
> `INSERT` usi transaction ka hissa hai, to jo transition commit nahi hua uska audit row bhi gayab. **Database khud
> committed transitions ginega; log jo kahega uske saath compare hoga.**
>
> Phir tu teen files me outcome lines `COMMIT` ke baad le jaayega, aur wahi harness dobara chalega. **Din ka sawaal ek
> hai: fix ke baad kaunsi ginti badli, aur kaunsi bilkul nahi?** Ye mitigation hai, elimination nahi — Part C isko alag
> karke dikhayega.
>
> Do cheezein aur, dono debt: `P-57` (chaudah seals is working copy me CRLF hain) Step 0 me, aur Week 5 ke paanch `💡`
> Step 6 me — **Step 6 kabhi cut nahi hota.**

**Aaj ki files** (sab Local ke alawa publish hoti hain — `D-32`):

| File | Kya | Kaun likhta hai |
|---|---|---|
| `scripts/seal_audit.ps1` | har tracked seal ko uske committed blob se compare karta hai; `-Restore` sirf line-ending wale farak ko theek karta hai | BRIEF me diya hai — save karo |
| `labs/w6d1_print_census.py` | `session.begin()` blocks ke andar ke `print` AST se | BRIEF me |
| `labs/w6d1_commit_refusal.sql` · `.ps1` | triggers + seeds · harness | BRIEF me |
| `labs/w6d1_silent_server.py` · `labs/w6d1_p55_check.ps1` | `P-55` ka check | BRIEF me |
| `src/worker.py` · `src/reaper.py` · `src/dispatcher.py` | **fix** | **tu** |
| `docs/daily/week_06/DIN_01_PREDICTIONS_FROZEN.md` | Part B ke jawab, seal | **tu** |
| `docs/daily/week_06/DIN_01_ANSWERS.md` | har step ke baad: observed + meri explanation (Beat 4). **Local** | **tu** |

Saare harness scripts reviewer ne **ek disposable DB pe chala ke dekhe hain** — wo chalte hain. Unka *output* kya hoga,
wo Part B hai.

---

## PART A — Steps

### Step 0 — 20 min: kal raat ka commit, bench, seal, phir seals ki marammat, attribute, `blogprobe`

**0a. Kal raat ke review docs ka commit — named files, `-A` kabhi nahi.**

```powershell
cd d:\PROJECTS\relay
git add docs/DECISIONS.md docs/LEARNING_LOG.md docs/POSTMORTEMS.md docs/PROBLEMS.md docs/daily/WEEK_05_HANDOFF.md docs/logs/WEEK_05.md docs/logs/WEEK_06.md docs/daily/week_06/DIN_01_BRIEF.md
git diff --cached --name-only | Out-File -Encoding utf8 logs\w6d1_step0_staged.txt
Get-Content logs\w6d1_step0_staged.txt          # exactly ye 8. Koi *_KEY.md nahi
git commit -m "docs(w5d6-review): Din 6 review, P-57 amendment, D-30/D-32 notes, Week 6 log header, Din 1 brief"
```

`docs/roadmap/` aur `**/planning/` ignored hain — list me mat daalo (ignored path poora `git add` fail kar deta hai).

**0b. Bench — har line file me.** Aaj se DB check **har non-template database** list karta hai, naam ke pattern se nahi
(`blogprobe` `relay\_%` filter ko dikhta hi nahi tha).

```powershell
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("head=" + (git rev-parse --short HEAD))
$o.Add("src_diff=" + @(git diff --name-only HEAD -- src/).Count)
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py src/sink.py src/models.py src/schemas.py | ForEach-Object { $o.Add("hash " + $_) }
$o.Add("heads=" + ((.\.venv\Scripts\python.exe -m alembic heads 2>&1) -join ' | '))
$o.Add("relay_python=" + @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" }).Count)
$o.Add("dbs=" + ((docker exec relay-db-1 psql -U postgres -d postgres -t -A -c "SELECT string_agg(datname, ',' ORDER BY datname) FROM pg_database WHERE NOT datistemplate;") -join ''))
$o.Add("counters=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -F '|' -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');") -join ''))
$o.Add("protected=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -c "SELECT string_agg(id || '|' || status || '|' || attempts || '|' || claim_generation, ' ; ' ORDER BY id) FROM jobs WHERE id IN (108, 128, 136);") -join ''))
$o.Add("key_index=" + @(git ls-files -- "*_KEY.md").Count)
$o.Add("brief_control=" + @(git ls-files -- "*_BRIEF.md").Count)
$o | Out-File -Encoding utf8 logs\w6d1_step0_bench.txt
Get-Content logs\w6d1_step0_bench.txt
```

Expected (instrument, outcome nahi): `src_diff=0` · aath hashes `a2ec8e9f…` (worker) `edcde815…` (reaper) `dcdb6343…`
(dispatcher) `d55e3b8a…` (main) `fc5bde22…` (database) `fcfc9059…` (sink) `04f04f84…` (models) `a53e7cc8…` (schemas) ·
`heads=w4d4_sink_unique (head)` · `relay_python=0` · `dbs=blogprobe,postgres,relay` · counters `133|145|19|4|7|39|5|0|1` ·
`protected=108|dead_letter|4|0 ; 128|succeeded|4|4 ; 136|running|1|1` · `key_index=0` · `brief_control=30`.

**0c. Seal — Part B ke jawab, abhi, kisi experiment se pehle.** `docs/daily/week_06/DIN_01_PREDICTIONS_FROZEN.md`: har
sub-part ka alag jawab. **`[padh ke]` sub-part me likho kya padha** (file:line), `idk` bhi usi ke saath. Phir:

```powershell
$f = "docs\daily\week_06\DIN_01_PREDICTIONS_FROZEN.md"
"sha256=" + (Get-FileHash -Algorithm SHA256 $f).Hash | Out-File -Encoding utf8 logs\w6d1_step0_frozen_hash.txt
"git_blob=" + (git hash-object $f) | Out-File -Append -Encoding utf8 logs\w6d1_step0_frozen_hash.txt
Get-Content logs\w6d1_step0_frozen_hash.txt
```

Aur `docs/daily/week_06/DIN_01_ANSWERS.md` banao — khaali, bas har step ka heading. Har step ke baad do line:
`Observed:` (file ka naam + value) aur `Meri explanation (KEY se pehle):`. **Wo file Local hai; KEY kholne se pehle likhi
jaati hai.**

**0d. Seals — pehle naapo, phir theek karo.** `scripts/seal_audit.ps1` save karo:

```powershell
# scripts/seal_audit.ps1 -- audit every tracked *_PREDICTIONS_FROZEN.md against its committed blob (P-57).
# Read-only by default. With -Restore it rewrites a working copy from the index ONLY when that copy differs from
# the committed bytes by line endings alone; any other difference is reported as BLOCKED and left untouched.
# Usage: pwsh -File scripts\seal_audit.ps1 -Out logs\<name>.txt [-Restore]
param([Parameter(Mandatory = $true)][string]$Out, [switch]$Restore)
function Sha([byte[]]$b) { [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($b)) }
function LfOnly([byte[]]$b) {
  $o = [System.Collections.Generic.List[byte]]::new($b.Length)
  for ($i = 0; $i -lt $b.Length; $i++) { if (-not ($b[$i] -eq 13 -and $i + 1 -lt $b.Length -and $b[$i + 1] -eq 10)) { $o.Add($b[$i]) } }
  return , $o.ToArray()
}
function CommittedSha([string]$f) {
  $tmp = New-TemporaryFile
  cmd /c "git cat-file blob HEAD:$f > `"$($tmp.FullName)`""
  $h = Sha ([IO.File]::ReadAllBytes($tmp.FullName)); Remove-Item $tmp; return $h
}
$r = [System.Collections.Generic.List[string]]::new()
$seals = @(git ls-files -- '*_PREDICTIONS_FROZEN.md')
$restored = 0; $blocked = 0
foreach ($f in $seals) {
  $committed = CommittedSha $f
  $bytes = [IO.File]::ReadAllBytes((Resolve-Path $f))
  $wc = Sha $bytes; $lf = Sha (LfOnly $bytes)
  $eol = ((git ls-files --eol -- $f) -split '\s+')[1]
  $action = '-'
  if ($Restore -and $wc -ne $committed) {
    if ($lf -eq $committed) { Remove-Item $f; git checkout -- $f; $restored++; $action = 'restored' }
    else { $blocked++; $action = 'BLOCKED_content_differs' }
  }
  $r.Add($f + ' ' + $eol + ' wc=' + $wc.Substring(0, 8) + ' lf_only=' + $lf.Substring(0, 8) + ' committed=' + $committed.Substring(0, 8) + ' action=' + $action)
}
$match = 0; $blobMatch = 0
foreach ($f in $seals) {
  if ((CommittedSha $f) -eq (Sha ([IO.File]::ReadAllBytes((Resolve-Path $f))))) { $match++ }
  if ((git hash-object $f) -eq (git rev-parse "HEAD:$f")) { $blobMatch++ }
}
$r.Add('seals=' + $seals.Count + ' wc_sha_equals_committed=' + $match + ' hash_object_equals_head=' + $blobMatch + ' restored=' + $restored + ' blocked=' + $blocked)
$r.Add('attr_line2=' + (Get-Content .gitattributes | Select-Object -Skip 1 -First 1))
$r.Add('git_status_lines=' + @(git status --porcelain).Count)
$r | Out-File -Encoding utf8 $Out
Get-Content $Out
```

Phir teen cheezein, isi order me — **`Q1(a)` pehle se seal ho chuka hai:**

```powershell
pwsh -File scripts\seal_audit.ps1 -Out logs\w6d1_step0_seals_before.txt
$f4 = 'docs/daily/week_05/DIN_04_PREDICTIONS_FROZEN.md'
"start:   " + (git ls-files --eol -- $f4) | Out-File -Encoding utf8 logs\w6d1_step0_restore_arms.txt
git checkout -- $f4;             "checkout: " + (git ls-files --eol -- $f4) | Out-File -Append -Encoding utf8 logs\w6d1_step0_restore_arms.txt
git restore --worktree -- $f4;   "restore:  " + (git ls-files --eol -- $f4) | Out-File -Append -Encoding utf8 logs\w6d1_step0_restore_arms.txt
Get-Content logs\w6d1_step0_restore_arms.txt
pwsh -File scripts\seal_audit.ps1 -Out logs\w6d1_step0_seals_after.txt -Restore
```

Script delete + `checkout` wala teesra arm khud chalata hai, par **sirf un files pe jinke bytes committed blob se sirf
line endings me alag hain.** `blocked` `0` se zyada aaye to **ruk jao** — matlab kisi seal ka content badla hai, aur wo
ek alag finding hai.

**0e. Attribute ka faisla (Situation 3 — Gemini se options, pick tera).** `D-32` `eol=lf` kehta hai, `.gitattributes`
line 2 `-text`.

| Option | Kya karna | Cost |
|---|---|---|
| (a) `-text` rakho | `D-32` ke *"Week 5 Din 6 review"* subsection ke neeche ek line: `-text` chuna, aur uska cost | `D-32` ka text badalta hai; attribute ka behaviour wahi |
| (b) `eol=lf` pe jao | `.gitattributes` line 2 badlo, `seal_audit` dobara chalao (`logs\w6d1_step0_seals_attr.txt`), wahi ek line `D-32` me | ek aur `.gitattributes` commit; purane commits ke checkout pe koi asar nahi |

Dono ka mechanism tujhe `Q1(b)` ke liye pata hona chahiye — isliye ye faisla seal ke **baad** hai.

**0f. `blogprobe` (Situation 3).** Blog ke `2026-09-19` run ka probe database — `7655 kB`, ek `jobs` table, Relay ka
evidence nahi, aur `docs/blog/POST_01_OUTLINE.md:337` usko *dropped* kehta hai. Drop karna hai to (**irreversible**):

```powershell
docker exec relay-db-1 psql -U postgres -d postgres -c "DROP DATABASE blogprobe WITH (FORCE);" | Out-File -Encoding utf8 logs\w6d1_step0_blogprobe.txt
```

Rakhna hai to ek line `DIN_01_ANSWERS.md` me — kyun, aur close bench me `dbs=` kya expect karna hai.

**Executable end:** `w6d1_step0_staged.txt` (8 lines) · commit · `w6d1_step0_bench.txt` · `w6d1_step0_frozen_hash.txt`
(do lines) · `w6d1_step0_seals_before.txt` · `w6d1_step0_restore_arms.txt` (teen lines) · `w6d1_step0_seals_after.txt`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `git ls-files --eol` | teen column: `i/` = index ke blob ki line endings, `w/` = working copy file ki, `attr/` = us path pe laga attribute |
| stat cache | index har file ka size aur mtime yaad rakhta hai. Git file ko dobara tabhi padhta hai jab ye badle |
| `-text` | *"is path ko text mat maano"* — add pe bhi aur checkout pe bhi koi line-ending conversion nahi, bytes jaise hain waise |
| `eol=lf` | *"is path ko text maano"* — index me LF, aur checkout pe LF likho |
| `git hash-object <file>` | *"is file ko abhi add karein to kaunsa blob id banega"* — attributes lagane ke baad |
| `git rev-parse HEAD:<path>` | commit me jo blob hai uska id. Working copy ko dekhta hi nahi |
| `datistemplate` | Postgres ke `template0`/`template1` jaise databases ka flag; bench unhe chhodta hai |

---

### Step 1 — 10 min: `P-56` census — instrument se, aankh se nahi

`P-56` ka apna table chaar lines ka naam leta hai. **Census use scope karta hai, aur card khud kehta hai census fix ke
saath chalta hai.** Aankh se ginna wahi galti dohrata hai jisne Din 2 pe mark ki position miss ki thi.

`labs/w6d1_print_census.py` save karo:

```python
r"""labs/w6d1_print_census.py -- Week 6 Din 1 (P-56 census).
Lists every print() call that sits lexically inside an `async with <x>.begin():` block in src/*.py,
found by walking the AST rather than by eye. Prints values only; the classification is yours.
Usage: .\.venv\Scripts\python.exe labs\w6d1_print_census.py"""
import ast
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"


def is_begin(item: ast.withitem) -> bool:
    call = item.context_expr
    return (
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "begin"
    )


def is_print(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"


inside_total = 0
for path in sorted(SRC.glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    all_prints = sum(1 for n in ast.walk(tree) if is_print(n))
    inside = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncWith) and any(is_begin(i) for i in node.items):
            for sub in ast.walk(node):
                if is_print(sub):
                    inside.add((sub.lineno, node.lineno))
    inside_total += len(inside)
    print(f"file={path.name} prints_total={all_prints} prints_inside_begin={len(inside)}")
    for line, block in sorted(inside):
        print(f"  {path.name}:{line} (inside the begin() block that starts at line {block})")
print(f"prints_inside_begin_total={inside_total}")
```

```powershell
.\.venv\Scripts\python.exe labs\w6d1_print_census.py | Out-File -Encoding utf8 logs\w6d1_step1_census.txt
Get-Content logs\w6d1_step1_census.txt
```

**Ab classification — tera kaam, file me:** `logs\w6d1_step1_classified.txt`, har listed line ke liye ek line:
`file:line CLASS reason`. Teen classes:

- **O — outcome:** ek aisi DB state batati hai jo sirf `COMMIT` sach karta hai
- **B — observation:** batati hai ki ek statement ne kya lautaya; commit karne ko kuch nahi
- **I — intent:** batati hai ki kya hone wala hai

Ek line me do hisse hon (ek observed, ek pre-commit) to dono likho (`O+B`). **Tera O-class list hi Step 3 ki edit list
hai.**

**Executable end:** do files. `prints_total` har file me `prints_inside_begin` se bada ya barabar — wo census ka apna
positive control hai (instrument ne file padhi).

**Terms used in this step**

| Term | Kya hai |
|---|---|
| lexically inside | code jo text me `async with ...begin():` ke indented block ke andar likha hai — chahe kitna bhi gehra `if` ho |
| AST | Python code ka parse tree; `ast.walk` uske har node pe jaata hai |
| `async with session.begin():` | block shuru = transaction shuru; block normally khatam = `COMMIT`; exception = `ROLLBACK` aur exception aage |

---

### Step 2 — 15 min: control — aaj ke code pe database `COMMIT` mana karega

Do files save karo. **Pehle SQL padho** — `Q3` ke jawab isi me aur teen `src/` files me hain.

`labs/w6d1_commit_refusal.sql`:

```sql
-- labs/w6d1_commit_refusal.sql -- Week 6 Din 1. Disposable database relay_w6d1 ONLY.
--
-- Two kinds of trigger, and the difference between them is the whole experiment:
--   w6d1_refuse_*  DEFERRABLE INITIALLY DEFERRED -> runs at COMMIT and makes that COMMIT fail.
--   w6d1_audit_*   ordinary AFTER UPDATE        -> its INSERT belongs to the same transaction,
--                  so it disappears whenever that transaction's COMMIT fails.
-- w6d1_audit therefore holds COMMITTED transitions only, counted by the database itself.

DO $$ BEGIN
  IF current_database() <> 'relay_w6d1' THEN
    RAISE EXCEPTION 'refusing to run in database %', current_database();
  END IF;
END $$;

CREATE TABLE w6d1_audit (
  kind   text        NOT NULL,
  row_id bigint      NOT NULL,
  at     timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE SEQUENCE w6d1_hb_seq;

CREATE FUNCTION w6d1_audit_row() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO w6d1_audit (kind, row_id) VALUES (TG_ARGV[0], NEW.id);
  RETURN NULL;
END $$;

CREATE FUNCTION w6d1_refuse_commit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  -- heartbeat arm: refuse only the FIRST heartbeat commit, allow the ones after it
  IF TG_ARGV[0] = 'heartbeat' AND nextval('w6d1_hb_seq') > 1 THEN
    RETURN NULL;
  END IF;
  RAISE EXCEPTION 'w6d1: % commit refused for id=%', TG_ARGV[0], NEW.id;
END $$;

-- audit: every committed transition of each kind, on every row
CREATE TRIGGER w6d1_audit_claim AFTER UPDATE ON jobs FOR EACH ROW
  WHEN (OLD.status = 'pending' AND NEW.status = 'running')
  EXECUTE FUNCTION w6d1_audit_row('claim');
CREATE TRIGGER w6d1_audit_heartbeat AFTER UPDATE ON jobs FOR EACH ROW
  WHEN (OLD.status = 'running' AND NEW.status = 'running' AND NEW.claimed_at > OLD.claimed_at)
  EXECUTE FUNCTION w6d1_audit_row('heartbeat');
CREATE TRIGGER w6d1_audit_mark AFTER UPDATE ON jobs FOR EACH ROW
  WHEN (OLD.status = 'running' AND NEW.status <> 'running' AND NEW.claimed_at IS NOT NULL)
  EXECUTE FUNCTION w6d1_audit_row('mark');
CREATE TRIGGER w6d1_audit_reclaim AFTER UPDATE ON jobs FOR EACH ROW
  WHEN (OLD.status = 'running' AND NEW.status = 'pending' AND NEW.claimed_at IS NULL)
  EXECUTE FUNCTION w6d1_audit_row('reclaim');
CREATE TRIGGER w6d1_audit_dispatch AFTER UPDATE ON outbox FOR EACH ROW
  WHEN (OLD.dispatched_at IS NULL AND NEW.dispatched_at IS NOT NULL)
  EXECUTE FUNCTION w6d1_audit_row('dispatch');

-- refusal: one arm per lifecycle writer, selected by the row's payload
CREATE CONSTRAINT TRIGGER w6d1_refuse_claim AFTER UPDATE ON jobs
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
  WHEN (OLD.status = 'pending' AND NEW.status = 'running' AND NEW.payload->>'fail_commit' = 'claim')
  EXECUTE FUNCTION w6d1_refuse_commit('claim');
CREATE CONSTRAINT TRIGGER w6d1_refuse_heartbeat AFTER UPDATE ON jobs
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
  WHEN (OLD.status = 'running' AND NEW.status = 'running' AND NEW.claimed_at > OLD.claimed_at
        AND NEW.payload->>'fail_commit' = 'heartbeat')
  EXECUTE FUNCTION w6d1_refuse_commit('heartbeat');
CREATE CONSTRAINT TRIGGER w6d1_refuse_mark AFTER UPDATE ON jobs
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
  WHEN (OLD.status = 'running' AND NEW.status <> 'running' AND NEW.claimed_at IS NOT NULL
        AND NEW.payload->>'fail_commit' = 'mark')
  EXECUTE FUNCTION w6d1_refuse_commit('mark');
CREATE CONSTRAINT TRIGGER w6d1_refuse_reclaim AFTER UPDATE ON jobs
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
  WHEN (OLD.status = 'running' AND NEW.status = 'pending' AND NEW.claimed_at IS NULL
        AND NEW.payload->>'fail_commit' = 'reclaim')
  EXECUTE FUNCTION w6d1_refuse_commit('reclaim');
CREATE CONSTRAINT TRIGGER w6d1_refuse_dispatch AFTER UPDATE ON outbox
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
  WHEN (OLD.dispatched_at IS NULL AND NEW.dispatched_at IS NOT NULL
        AND NEW.payload->>'fail_commit' = 'dispatch')
  EXECUTE FUNCTION w6d1_refuse_commit('dispatch');

-- seeds: ids 1..3 share one created_at, so the claim order is by id
INSERT INTO jobs (type, payload) VALUES
  ('sleep', '{"seconds": 0.5, "fail_commit": "mark"}'),
  ('sleep', '{"seconds": 22,  "fail_commit": "heartbeat"}'),
  ('sleep', '{"seconds": 0.5, "fail_commit": "claim"}');
INSERT INTO jobs (type, payload, status, attempts, claim_generation, claimed_at)
  VALUES ('sleep', '{"fail_commit": "reclaim"}', 'running', 1, 1, now() - interval '60 seconds');
INSERT INTO outbox (job_id, effect_key, payload)
  VALUES (99, 'job:99', '{"fail_commit": "dispatch"}');

SELECT 'seeded_jobs=' || count(*) FROM jobs;
SELECT 'triggers=' || count(*) FROM pg_trigger WHERE tgname LIKE 'w6d1\_%';
```

`labs/w6d1_commit_refusal.ps1`:

```powershell
# labs/w6d1_commit_refusal.ps1 -- Week 6 Din 1.
# Runs sink + worker + reaper (+ dispatcher for a window) against a disposable database relay_w6d1 in which
# the database REFUSES chosen COMMITs.
#   Phase 1 (t = 0..40 s): refusal triggers active.
#   Phase 2 (t = 40..52 s): refusal triggers dropped, audit triggers kept, so every writer also gets
#                           committed transitions (the positive controls).
# Usage:  pwsh -File labs\w6d1_commit_refusal.ps1 -Phase control    (today's code, before the fix)
#         pwsh -File labs\w6d1_commit_refusal.ps1 -Phase fixed      (after the Step 3 edit)
# Every line it writes is a value or a label. It writes no conclusions (P-52).
param(
  [Parameter(Mandatory = $true)][ValidatePattern('^[a-z]+$')][string]$Phase,
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)
$ErrorActionPreference = 'Continue'
Set-Location $RepoRoot
$db  = 'relay_w6d1'
$run = "w6d1_${Phase}_" + (Get-Date -Format 'yyyyMMdd_HHmmss_ffffff')
$L   = Join-Path $RepoRoot 'logs'
New-Item -ItemType Directory -Force -Path $L | Out-Null
$py  = (Resolve-Path (Join-Path $RepoRoot '.venv\Scripts\python.exe')).Path
$sql = Join-Path $PSScriptRoot 'w6d1_commit_refusal.sql'
$tl  = Join-Path $L "${run}_timeline.txt"

function Stamp([string]$label) { "$label=" + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff') | Out-File -Append -Encoding utf8 $tl }
function Psql([string]$q) { ((docker exec relay-db-1 psql -U postgres -d $db -t -A -F '|' -c $q) -join ' ').Trim() }
function CountIn([string]$file, [string]$needle, [string]$regex = '') {
  if (-not (Test-Path $file)) { return -1 }
  $n = 0
  foreach ($line in [IO.File]::ReadLines($file)) {
    if ($line.Contains($needle) -and ($regex -eq '' -or [regex]::IsMatch($line, $regex))) { $n++ }
  }
  return $n
}
function Snapshot([string]$path) {
  $o = [System.Collections.Generic.List[string]]::new()
  $o.Add("db=" + (Psql "SELECT current_database();"))
  $o.Add("jobs(id:status:attempts:generation)=" + (Psql "SELECT string_agg(id || ':' || status || ':' || attempts || ':' || claim_generation, ' ' ORDER BY id) FROM jobs;"))
  $o.Add("outbox(id:dispatched:attempts)=" + (Psql "SELECT string_agg(id || ':' || (dispatched_at IS NOT NULL) || ':' || attempts, ' ' ORDER BY id) FROM outbox;"))
  $o.Add("sink_rows=" + (Psql "SELECT count(*) FROM sink_deliveries;"))
  $o.Add("audit=" + (Psql "SELECT string_agg(k.kind || '_committed=' || coalesce(c.n, 0), ' ' ORDER BY k.kind) FROM (VALUES ('claim'),('heartbeat'),('mark'),('reclaim'),('dispatch')) AS k(kind) LEFT JOIN (SELECT kind, count(*) AS n FROM w6d1_audit GROUP BY kind) c ON c.kind = k.kind;"))
  $o.Add("hb_seq(last_value:is_called)=" + (Psql "SELECT last_value || ':' || is_called FROM w6d1_hb_seq;"))
  $o.Add("refusal_triggers_left=" + (Psql "SELECT count(*) FROM pg_trigger WHERE tgname LIKE 'w6d1\_refuse\_%';"))
  $o | Out-File -Encoding utf8 $path
}
function Start-Relay([string]$name, [string[]]$argList) {
  $env:RELAY_PROCESS_NAME = "${name}_w6d1"
  $p = Start-Process -FilePath $py -ArgumentList $argList -WorkingDirectory $RepoRoot -PassThru -NoNewWindow `
       -RedirectStandardOutput (Join-Path $L "${run}_${name}.log") `
       -RedirectStandardError  (Join-Path $L "${run}_${name}.err.log")
  Stamp "start_$name"
  return $p
}

$before = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*$RepoRoot*" }).Count
if ($before -ne 0) { throw "relay_python=$before before start -- stop those processes first" }

$saved = @{}
foreach ($k in 'DATABASE_URL', 'PYTHONUNBUFFERED', 'RELAY_PROCESS_NAME', 'SINK_URL') { $saved[$k] = [Environment]::GetEnvironmentVariable($k) }
$procs = @()
try {
  Stamp 'run_start'
  "run_id=$run" | Out-File -Append -Encoding utf8 $tl
  "src_hashes(worker,reaper,dispatcher)=" + ((git hash-object src/worker.py src/reaper.py src/dispatcher.py) -join ',') | Out-File -Append -Encoding utf8 $tl
  "src_diff_files_vs_HEAD=" + (@(git diff --name-only HEAD -- src/).Count) | Out-File -Append -Encoding utf8 $tl

  docker exec relay-db-1 psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS $db WITH (FORCE);" | Out-Null
  docker exec relay-db-1 psql -U postgres -d postgres -c "CREATE DATABASE $db;" | Out-Null
  $base = (Get-Content (Join-Path $RepoRoot '.env') | Select-String '^DATABASE_URL=').Line.Split('=', 2)[1]
  $env:DATABASE_URL = $base -replace '/relay$', "/$db"
  if (-not $env:DATABASE_URL.EndsWith("/$db")) { throw "DATABASE_URL rewrite failed" }
  $env:PYTHONUNBUFFERED = '1'
  $mig = (& $py -m alembic upgrade head 2>&1 | ForEach-Object { "$_" }) -join "`n"
  $mig | Out-File -Encoding utf8 (Join-Path $L "${run}_migrate.txt")
  if ($mig -notmatch "resolved_db=$db source=env") { throw "alembic did not target $db -- see ${run}_migrate.txt" }
  Get-Content $sql -Raw | docker exec -i relay-db-1 psql -U postgres -d $db -v ON_ERROR_STOP=1 *> (Join-Path $L "${run}_setup.txt")
  if ($LASTEXITCODE -ne 0) { throw "setup SQL failed -- see ${run}_setup.txt" }

  $procs += Start-Relay 'sink' @('-u', '-m', 'uvicorn', 'src.sink:app', '--host', '127.0.0.1', '--port', '8001')
  $up = $false
  for ($i = 0; $i -lt 40 -and -not $up; $i++) {
    try { Invoke-RestMethod -Uri 'http://127.0.0.1:8001/health' -TimeoutSec 2 | Out-Null; $up = $true } catch { Start-Sleep -Milliseconds 500 }
  }
  if (-not $up) { throw "sink did not answer /health" }
  Stamp 'sink_healthy'

  Stamp 't0'
  $procs += Start-Relay 'worker' @('-u', '-m', 'src.worker')
  $procs += Start-Relay 'reaper' @('-u', '-m', 'src.reaper')
  Start-Sleep -Seconds 28
  $env:SINK_URL = 'http://127.0.0.1:8001/deliver'
  $procs += Start-Relay 'dispatcher' @('-u', '-m', 'src.dispatcher')
  Start-Sleep -Seconds 12

  Snapshot (Join-Path $L "${run}_phase1.txt")
  Psql "DROP TRIGGER w6d1_refuse_claim ON jobs; DROP TRIGGER w6d1_refuse_heartbeat ON jobs; DROP TRIGGER w6d1_refuse_mark ON jobs; DROP TRIGGER w6d1_refuse_reclaim ON jobs; DROP TRIGGER w6d1_refuse_dispatch ON outbox;" | Out-Null
  Stamp 'phase2_start'
  Start-Sleep -Seconds 12
}
finally {
  foreach ($p in $procs) { if ($p) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } }
  Start-Sleep -Seconds 2
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like "*$RepoRoot*" -and $_.CommandLine -match 'src\.(worker|reaper|dispatcher|sink)' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Seconds 1
  Stamp 'stopped'
  "relay_python_after=" + @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*$RepoRoot*" }).Count | Out-File -Append -Encoding utf8 $tl
  foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) }
}

Snapshot (Join-Path $L "${run}_final.txt")
$w = Join-Path $L "${run}_worker.log"; $r = Join-Path $L "${run}_reaper.log"
$d = Join-Path $L "${run}_dispatcher.log"; $s = Join-Path $L "${run}_sink.log"
$c = [System.Collections.Generic.List[string]]::new()
foreach ($f in $w, $r, $d, $s) { $c.Add("premise $(Split-Path $f -Leaf): " + ((Select-String -Path $f -Pattern '^resolved_db=' | Select-Object -First 1).Line)) }
$c.Add("claim_lines=" + (CountIn $w '[claim] Claimed job'))
$c.Add("heartbeat_lines=" + (CountIn $w 'Heartbeat sent for job_id='))
$c.Add("mark_lines=" + (CountIn $w '[mark] Marked job'))
$c.Add("reclaim_lines=" + (CountIn $r '[reclaim]' 'matched=1'))
$c.Add("dispatch_lines=" + (CountIn $d 'status=dispatched'))
$c.Add("mark_error_lines=" + (CountIn $w '[mark_error]'))
$c.Add("heartbeat_error_lines=" + (CountIn $w '[heartbeat_error]'))
$c.Add("worker_poll_error=" + (CountIn $w '[poll_error]'))
$c.Add("reaper_poll_error=" + (CountIn $r '[poll_error]'))
$c.Add("dispatcher_poll_error=" + (CountIn $d '[poll_error]'))
$c.Add("worker_echo_COMMIT=" + (CountIn $w 'COMMIT' 'sqlalchemy\.engine\.Engine COMMIT$'))
$c.Add("sink_applied=" + (CountIn $s 'result=applied'))
$c.Add("sink_duplicate=" + (CountIn $s 'result=duplicate'))
$c.Add("final_" + ((Get-Content (Join-Path $L "${run}_final.txt") | Select-String '^audit=').Line))
$c | Out-File -Encoding utf8 (Join-Path $L "${run}_census.txt")
Get-Content $tl, (Join-Path $L "${run}_phase1.txt"), (Join-Path $L "${run}_final.txt"), (Join-Path $L "${run}_census.txt")
```

Chalao — `~70 s`, aur is dauran `relay` ke process kuch aur nahi chal rahe hone chahiye (script khud check karta hai):

```powershell
pwsh -File labs\w6d1_commit_refusal.ps1 -Phase control
```

**Timeline, taaki output padh sako:** `t0` pe worker aur reaper · `t ≈ 28 s` pe dispatcher · `t ≈ 40 s` pe phase-1
snapshot, phir refusal triggers drop · `t ≈ 52 s` pe sab band, final snapshot aur census. Seeds: job `1` ka **mark**
refuse · job `2` (`22 s` sleep) ka **pehla heartbeat** refuse · job `3` ka **claim** refuse · job `4` pehle se `running`,
expired lease ke saath, uska **reclaim** refuse · outbox row `1` ka **dispatch** refuse.

**Executable end:** `logs\w6d1_control_<runid>_{timeline,phase1,final,census}.txt` + chaar process logs. `DIN_01_ANSWERS.md`
me do line.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| deferred constraint trigger | `DEFERRABLE INITIALLY DEFERRED` — statement ke waqt nahi, **`COMMIT` ke waqt** chalta hai. Wahan exception = `COMMIT` fail, poora transaction rollback |
| `RAISE EXCEPTION` | PL/pgSQL ka error; jis transaction me uthe use abort karta hai |
| ordinary `AFTER UPDATE` trigger | usi statement ke saath chalta hai; uska `INSERT` usi transaction ka hissa hai |
| `nextval()` | sequence se agla number. **Rollback isko wapas nahi leta** — sequences transaction ke bahar hain |
| positive control | ek case jiska sahi jawab `≥ 1` hai, taaki `0` ya barabari kuch kahe. Yahan: phase 2 ke committed transitions |
| premise line | har Relay process startup pe `resolved_db=… app_name=…` likhta hai; wahi batata hai ki process kis DB pe tha |

---

### Step 3 — 25 min: fix — outcome lines `COMMIT` ke baad, aur `P-55` ki class

**Pehle 3 min, design pick (Situation 3) — Gemini se options aur cost, pick tera:**

| Option | Shape | Cost |
|---|---|---|
| (a) **ek line, commit ke baad** | tag wahi, line block ke bahar | commit aur print ke beech crash → committed state, koi line nahi |
| (b) **do lines** | naya intent tag andar (jaise `[claim_try]`), purana tag commit ke baad | dono direction ka record; lifecycle log volume do-guna, aur har grep ko naya tag pata hona chahiye |

`P-56` ke *"Fix directions"* paragraph me dono ka zikr hai. Pick aur ek line cost `DIN_01_ANSWERS.md` me.

**Rules, pick jo bhi ho:**

1. **Purane tags ka text bilkul wahi** — `[claim] Claimed job`, `Heartbeat sent for job_id=`, `[mark] Marked job`,
   `[reclaim] … matched=`, `status=dispatched`. Week 2 se har check in strings pe grep karta hai (`P-32`), aaj ka harness bhi.
2. **Committed line `async with session.begin():` block ke *baad*, par usi `try` ke andar** jo exception pakadta hai — taaki
   fail hua `COMMIT` line tak pahunche hi nahi.
3. **Print ko jo values chahiye (ids, `rowcount`, `attempts`, generation), unhe block ke andar local variables me rakh lo.**
   Block ke baad ORM object ke attributes pe bharosa mat karo.
4. **Behaviour nahi badalna:** koi naya `sleep`, retry, SQL, ya control flow nahi. Sirf lines ki jagah aur text.
5. **`P-55`:** `[dispatch_error]` wahi shape le jo `src/` ki baaki chhe exception lines ki hai — class ka naam, phir message.

**Edit list = Step 1 ki O-class lines.** Reaper me ek loop ke andar kai lines banti hain; unhe block ke baad print karne ka
tareeka tera.

**Executable end:**

```powershell
.\.venv\Scripts\python.exe -m py_compile src\worker.py src\reaper.py src\dispatcher.py; "py_compile_exit=$LASTEXITCODE" | Out-File -Encoding utf8 logs\w6d1_step3_edit.txt
git diff --stat -- src/ | Out-File -Append -Encoding utf8 logs\w6d1_step3_edit.txt
.\.venv\Scripts\python.exe labs\w6d1_print_census.py | Out-File -Encoding utf8 logs\w6d1_step3_census_after.txt
Get-Content logs\w6d1_step3_edit.txt, logs\w6d1_step3_census_after.txt
```

`py_compile_exit=0` · diff me **exactly teen files** · aur census-after me tera koi O-class line ab kisi `begin()` block ke
andar nahi (B aur I classes andar reh sakti hain).

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `expire_on_commit=False` | `src/database.py` ka session setting: commit ke baad bhi jo attributes DB se load hue the, wo memory me rehte hain |
| `CursorResult.rowcount` | statement ne kitni rows match ki. Statement ka result hai, `COMMIT` ka nahi |
| grep contract | ek log tag ka exact text ek interface hai; badla to har purana check chupchaap `0` padhega |

---

### Step 4 — 12 min: wahi harness, fixed code — aur differential

```powershell
pwsh -File labs\w6d1_commit_refusal.ps1 -Phase fixed
```

Phir dono census files ek jagah:

```powershell
$ctl = Get-ChildItem logs -Filter "w6d1_control_*_census.txt" | Sort-Object Name | Select-Object -Last 1
$fix = Get-ChildItem logs -Filter "w6d1_fixed_*_census.txt" | Sort-Object Name | Select-Object -Last 1
function Kv($file) {
  $h = @{}
  foreach ($l in Get-Content $file.FullName) { if ($l -match '^([a-z_]+)=(-?\d+)$') { $h[$Matches[1]] = [int]$Matches[2] } }
  $a = (Get-Content $file.FullName | Select-String '^final_audit=').Line
  foreach ($m in [regex]::Matches($a, '([a-z]+)_committed=(\d+)')) { $h[$m.Groups[1].Value + '_committed'] = [int]$m.Groups[2].Value }
  return $h
}
$CT = Kv $ctl; $FX = Kv $fix
$out = [System.Collections.Generic.List[string]]::new()
$out.Add('control=' + $ctl.Name); $out.Add('fixed=' + $fix.Name)
foreach ($t in 'claim', 'heartbeat', 'mark', 'reclaim', 'dispatch') {
  $out.Add($t + ': control lines=' + $CT[$t + '_lines'] + ' committed=' + $CT[$t + '_committed'] + ' | fixed lines=' + $FX[$t + '_lines'] + ' committed=' + $FX[$t + '_committed'] + ' | fixed_equal=' + ($FX[$t + '_lines'] -eq $FX[$t + '_committed']) + ' committed_ge_1=' + ($FX[$t + '_committed'] -ge 1))
}
foreach ($k in 'mark_error_lines', 'heartbeat_error_lines', 'worker_poll_error', 'reaper_poll_error', 'dispatcher_poll_error', 'worker_echo_COMMIT', 'sink_applied', 'sink_duplicate') {
  $out.Add($k + ': control=' + $CT[$k] + ' fixed=' + $FX[$k])
}
$out | Out-File -Encoding utf8 logs\w6d1_step4_diff.txt
Get-Content logs\w6d1_step4_diff.txt
```

**Correct fix ki definition — aur ye prediction nahi, requirement hai:** fixed run me har tag ke liye `fixed_equal=True`
**aur** `committed_ge_1=True`. Pehla kehta hai log ne har committed transition ek baar likha; doosra kehta hai wo
barabari `0 = 0` wali khokhli barabari nahi hai.

Agar koi tag `fixed_equal=False` de: us process ka fixed log kholo, aur **pehle apni explanation `ANSWERS` me likho**,
phir Gemini se sirf *vocabulary* (kisi exception class ka matlab) — Situation 1.

**Executable end:** `logs\w6d1_step4_diff.txt` — do file names + 5 tag lines + 8 comparison lines.

---

### Step 5 — 8 min: `P-55` — ek server jo connection leta hai aur kabhi jawab nahi deta

Do files save karo.

`labs/w6d1_silent_server.py`:

```python
"""labs/w6d1_silent_server.py -- Week 6 Din 1.
Accepts TCP connections on 127.0.0.1:8099 and never sends a byte back. A client sees a connection that
succeeds and a response that never starts. Stop it with Ctrl+C or Stop-Process."""
import socket

s = socket.socket()
s.bind(("127.0.0.1", 8099))
s.listen(16)
held = []
print("silent_server listening 127.0.0.1:8099", flush=True)
while True:
    conn, addr = s.accept()
    held.append(conn)  # keep a reference so the socket is not closed
    print(f"accepted {addr}", flush=True)
```

`labs/w6d1_p55_check.ps1`:

```powershell
# labs/w6d1_p55_check.ps1 -- Week 6 Din 1, Step 5 (P-55).
# Two arms against the disposable database relay_w6d1 that the Step 4 harness run leaves behind:
#   silent : SINK_URL -> labs/w6d1_silent_server.py (accepts the TCP connection, never answers)
#   closed : SINK_URL -> a port nothing listens on
# Writes values only.
param([string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path)
Set-Location $RepoRoot
$db     = 'relay_w6d1'
$run    = 'w6d1_p55_' + (Get-Date -Format 'yyyyMMdd_HHmmss_ffffff')
$py     = (Resolve-Path .\.venv\Scripts\python.exe).Path
$server = Join-Path $PSScriptRoot 'w6d1_silent_server.py'
$reset  = 'DO $$ BEGIN IF current_database() <> ''relay_w6d1'' THEN RAISE EXCEPTION ''wrong db''; END IF; END $$; TRUNCATE outbox RESTART IDENTITY; INSERT INTO outbox (job_id, effect_key, payload) VALUES (55, ''job:55'', ''{}'');'
$keep = @{}
foreach ($k in 'DATABASE_URL', 'SINK_URL', 'RELAY_PROCESS_NAME', 'PYTHONUNBUFFERED') { $keep[$k] = [Environment]::GetEnvironmentVariable($k) }
$env:DATABASE_URL = (Get-Content .env | Select-String '^DATABASE_URL=').Line.Split('=', 2)[1] -replace '/relay$', "/$db"
$env:PYTHONUNBUFFERED = '1'
$o = [System.Collections.Generic.List[string]]::new()
$srv = Start-Process -FilePath $py -ArgumentList '-u', $server -PassThru -NoNewWindow -RedirectStandardOutput "logs\${run}_server.log" -RedirectStandardError "logs\${run}_server.err.log"
try {
  Start-Sleep -Seconds 2
  foreach ($arm in @(@('silent', 'http://127.0.0.1:8099/deliver', 13), @('closed', 'http://127.0.0.1:8098/deliver', 8))) {
    docker exec relay-db-1 psql -U postgres -d $db -v ON_ERROR_STOP=1 -c $reset | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "reset failed -- does relay_w6d1 exist? run the Step 4 harness first" }
    $env:SINK_URL = $arm[1]; $env:RELAY_PROCESS_NAME = "dispatcher_w6d1_$($arm[0])"
    $log = "logs\${run}_$($arm[0])_dispatcher.log"
    $d = Start-Process -FilePath $py -ArgumentList '-u', '-m', 'src.dispatcher' -PassThru -NoNewWindow -RedirectStandardOutput $log -RedirectStandardError "logs\${run}_$($arm[0])_dispatcher.err.log"
    Start-Sleep -Seconds $arm[2]
    Stop-Process -Id $d.Id -Force
    Start-Sleep -Seconds 1
    $lines = @([IO.File]::ReadAllLines((Resolve-Path $log)) | Where-Object { $_.Contains('[dispatch_error]') })
    $attempts = (docker exec relay-db-1 psql -U postgres -d $db -t -A -c 'SELECT attempts FROM outbox WHERE id = 1;') -join ''
    $o.Add($arm[0] + ' window_s=' + $arm[2] + ' dispatch_error_lines=' + $lines.Count + ' with_ReadTimeout=' + @($lines | Where-Object { $_.Contains('ReadTimeout') }).Count + ' with_ConnectError=' + @($lines | Where-Object { $_.Contains('ConnectError') }).Count + ' outbox_attempts=' + $attempts)
    if ($lines.Count -gt 0) { $o.Add($arm[0] + ' first_line: ' + $lines[0]) }
  }
}
finally {
  Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*w6d1_silent_server*' -or ($_.CommandLine -like "*$RepoRoot*" -and $_.CommandLine -match 'src\.dispatcher') } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  foreach ($k in $keep.Keys) { [Environment]::SetEnvironmentVariable($k, $keep[$k]) }
}
$o.Add('relay_python_after=' + @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*$RepoRoot*" -or $_.CommandLine -like '*w6d1_silent_server*' }).Count)
$o | Out-File -Encoding utf8 "logs\${run}_census.txt"
Get-Content "logs\${run}_census.txt"
```

```powershell
pwsh -File labs\w6d1_p55_check.ps1
```

**Control fix se pehle ka hai aur retained hai:** `logs/w5d4_step5_20260927_081356_093927.log` —
`[dispatch_error] job_id=42 outbox_id=1 error= attempts=1`, aaj ke `HEAD` wala hi dispatcher.

**Executable end:** `logs\w6d1_p55_<runid>_census.txt` — do arm lines, do first lines, `relay_python_after=0`.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| silent server | TCP connection accept karta hai, ek byte nahi bhejta. Client ke liye connect safal, response kabhi shuru nahi |
| closed port | wahan koi listen nahi karta; OS connection mana karta hai |
| `httpx.AsyncClient(timeout=5.0)` | ek number, chaar alag timeouts: connect, read, write, pool — har ek `5 s` |

---

### Step 6 — 35 min (do half, `20` + `15`): Week 5 ke paanch `💡`, apne shabdon me

`docs/logs/WEEK_05.md` me Din 1–5 ke `💡` sections reviewer ke likhe hain — Din 1 (line `~333`), Din 2 (`~678`), Din 3
(`~971`), Din 4 (`~1329`), Din 5 (`~1667`). **Handoff ne inka owner naam se Week 6 Din 1 likha hai. Ye step cut nahi hota.**

**Procedure, har section — aur yahi is step ki value hai:**

1. Us din ka `📊 Measured / Observed` padho (Din 1 `~38`, Din 2 `~425`, Din 3 `~796`, Din 4 `~1090`, Din 5 `~1439`).
   **`💡` section mat padho.**
2. `### 💡 What I understood — own words, 2026-09-30` likho, reviewer wale section ke **upar**. Teen se paanch points, har
   point me ek number ya ek file.
3. **Ab** reviewer ka section padho. Neeche ek line: `Gaps vs reviewer: …`
4. Reviewer section ko mitao mat.

**6a:** Din 1, Din 2, Din 3. **6b:** Din 4, Din 5. Din 6 ka `💡` kal (Week 6 Din 2, Step 0.5).

**Executable end:**

```powershell
@("own_words_blocks=" + @(Select-String -Path docs\logs\WEEK_05.md -SimpleMatch "What I understood — own words, 2026-09-30").Count,
  "gaps_lines=" + @(Select-String -Path docs\logs\WEEK_05.md -SimpleMatch "Gaps vs reviewer:").Count,
  "reviewer_blocks_kept=" + @(Select-String -Path docs\logs\WEEK_05.md -Pattern "^### 💡 What the session established").Count) | Out-File -Encoding utf8 logs\w6d1_step6_rewrites.txt
Get-Content logs\w6d1_step6_rewrites.txt      # 5 · 5 · 6
```

Aaj se pehle ye `0 · 0 · 6` padhta hai `[MEASURED-R 2026-09-29]` — to check fail ho sakta hai. `6` isliye ki Din 6 ka
reviewer section bhi hai.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| recall vs recognition | padh ke *"haan yahi"* kehna recognition hai; bina dekhe likh paana recall. Order isi liye hai |

---

### Step 7 — 10 min: close — DB drop, bench, commit

```powershell
docker exec relay-db-1 psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS relay_w6d1 WITH (FORCE);" | Out-File -Encoding utf8 logs\w6d1_step7_drop.txt
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("src_diff_files=" + ((git diff --name-only HEAD -- src/) -join ','))
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py src/sink.py src/models.py src/schemas.py | ForEach-Object { $o.Add("hash " + $_) }
$o.Add("heads=" + ((.\.venv\Scripts\python.exe -m alembic heads 2>&1) -join ' | '))
$o.Add("dbs=" + ((docker exec relay-db-1 psql -U postgres -d postgres -t -A -c "SELECT string_agg(datname, ',' ORDER BY datname) FROM pg_database WHERE NOT datistemplate;") -join ''))
$o.Add("relay_python=" + @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" }).Count)
$o.Add("counters=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -F '|' -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');") -join ''))
$o.Add("protected=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -c "SELECT string_agg(id || '|' || status || '|' || attempts || '|' || claim_generation, ' ; ' ORDER BY id) FROM jobs WHERE id IN (108, 128, 136);") -join ''))
$o.Add("key_index=" + @(git ls-files -- "*_KEY.md").Count)
$o.Add("key_tree=" + @(git ls-tree -r --name-only HEAD | Select-String -CaseSensitive "_KEY\.md").Count)
$o.Add("brief_control=" + @(git ls-files -- "*_BRIEF.md").Count)
$o.Add("frozen_sha256=" + (Get-FileHash -Algorithm SHA256 docs\daily\week_06\DIN_01_PREDICTIONS_FROZEN.md).Hash)
$o.Add("frozen_git_blob=" + (git hash-object docs\daily\week_06\DIN_01_PREDICTIONS_FROZEN.md))
$o | Out-File -Encoding utf8 logs\w6d1_step7_bench.txt
pwsh -File scripts\seal_audit.ps1 -Out logs\w6d1_step7_seals.txt
Get-Content logs\w6d1_step7_bench.txt
```

**Commit — named files, `-A` kabhi nahi:**

```powershell
git add src/worker.py src/reaper.py src/dispatcher.py scripts/seal_audit.ps1 labs/w6d1_print_census.py labs/w6d1_commit_refusal.sql labs/w6d1_commit_refusal.ps1 labs/w6d1_silent_server.py labs/w6d1_p55_check.ps1 docs/logs/WEEK_05.md docs/DECISIONS.md docs/daily/week_06/DIN_01_PREDICTIONS_FROZEN.md
# Step 0e me (b) chuna ho to:  git add .gitattributes
git diff --cached --name-only | Out-File -Encoding utf8 logs\w6d1_step7_staged.txt
Get-Content logs\w6d1_step7_staged.txt
git commit -m "fix(w6d1): lifecycle lines print after COMMIT (P-56), dispatch_error names the class (P-55); commit-refusal harness, seal audit"
```

`DIN_01_ANSWERS.md` list me **nahi** — wo Local hai, aur `git add` ignored path pe poori command fail karta hai.

---

## PART B — Prediction questions

> **Gemini ko NAHI. Step 0c pe, kisi bhi experiment se pehle, apne head se.** `[padh ke: …]` wale sub-part ka jawab repo
> me hai — pehle wo file/line kholo, aur jawab ke saath likho kya padha. Us sub-part ka `idk` tabhi `idk` hai jab saath me
> likha ho kya padha; warna wo reading gap gina jaayega. `[chala ke]` wale ka `idk` bilkul theek hai. **`idk` sub-part
> level pe.**

```text
Q1 (Step 0d se pehle — seals)
(a) [padh ke: docs/PROBLEMS.md, P-57 ka Week 5 Din 6 review amendment]
    DIN_04 ki working copy aaj `i/lf w/crlf attr/-text` hai aur `git status`
    clean hai. Teen commands, isi order me: `git checkout -- <file>` ·
    `git restore --worktree -- <file>` · file delete karke `git checkout --
    <file>`. Har ek ke baad `w/` column kya dikhayega?
(b) [padh ke: .gitattributes line 2 · D-32 "Week 5 Din 6 — final" item 4 ·
    Step 0 ka terms table] CRLF working copy pe `git hash-object` HEAD ke blob
    id ke barabar aayega — `-text` ke neeche? `eol=lf` ke neeche? Ek line
    mechanism.

Q2 (Step 1 se pehle — census)
(a) [padh ke: src/worker.py · src/reaper.py · src/dispatcher.py] Kitne
    `print()` calls kisi `async with session.begin():` block ke ANDAR likhe
    hain? Teeno files ka alag number.
(b) [padh ke: wahi teen files + P-56 ka table] Unme se kitne O class ke hain
    (aisi DB state jo sirf COMMIT sach karta hai)? file:line do. Kaunse P-56
    ke table me NAHI hain?

Q3 (Step 2 se pehle — control run, aaj ka code)
(a) [padh ke: src/worker.py:299–345] Phase 1 me `[mark] Marked job 1 as
    'succeeded'` kitni baar print hoga (±2)? Phase-1 snapshot me job 1 ka
    status?
(b) [padh ke: src/reaper.py:24–79] Job 1 ki lease uske claim ke ~30 s baad
    expire hoti hai; job 4 ka reclaim har pass pe refuse hota hai. Phase 1 me
    job 1 reclaim hoga? Reaper ka log job 1 ke baare me kya kahega, aur
    phase-1 snapshot ka `reclaim_committed`? Mechanism.
(c) [padh ke: src/dispatcher.py:34–106 · PROBLEMS.md P-35] Dispatcher phase 1
    me ~12–15 s chalta hai, sink milliseconds me jawab deta hai, aur har
    dispatch COMMIT refuse hota hai. Sink ko kitne POST milenge — ~1, ~5, ~50,
    ya ~400? Kyun?

Q4 (Step 4 se pehle — fix ke baad)
(a) [padh ke: PROBLEMS.md P-56 "Fix directions"] Fixed run me census ki kaunsi
    values control se alag hongi aur kaunsi lagbhag wahi: paanch `*_lines` ·
    `mark_error_lines` · `worker_echo_COMMIT` · `sink_duplicate` · final DB
    state.
(b) [padh ke: wahi paragraph] Fix ek nayi failure direction kholta hai.
    Kaunsi? Aur kya aaj ka harness use kabhi paida karta hai?

Q5 (Step 5 se pehle — P-55, fixed code)
(a) [padh ke: PROBLEMS.md P-55 · src/dispatcher.py:34 aur :93–106] Silent
    server ke against: pehli do `[dispatch_error]` lines ke beech kitne seconds
    (koi sleep?), aur 13 s window ke baad `outbox_attempts` lagbhag kitna?
(b) [chala ke] Closed port pe fix se PEHLE wali line bhi `error=` khaali hoti?
    Fix ke baad closed-port line kya dikhayegi?
```

---

## PART C — Verification

**Din 5 ka sabak:** jis check ki output file nahi bani, wo chala hi nahi. **Har check ki ek file.** Jahan outcome Part B ka
sawaal hai, wahan value nahi di gayi — sirf ye ki instrument us value ko pakad sakta hai.

### C0 — Step 0

| Subject | Check | Broken reading |
|---|---|---|
| `w6d1_step0_staged.txt` | exactly `8` lines, `0` matching `_KEY\.md` | `-A` ne kuch aur utha liya |
| `w6d1_step0_bench.txt` | Step 0 ke expected values (upar) | koi hash alag = kal raat se kuch badla |
| `w6d1_step0_frozen_hash.txt` | do lines, file ka mtime Step 0d ki pehli file se pehle | seal experiment ke baad likha gaya |
| `w6d1_step0_seals_after.txt` | `blocked=0` · `wc_sha_equals_committed` aur `hash_object_equals_head` ki values file me | `blocked > 0` = kisi seal ka content badla hai — ruk jao |
| `w6d1_step0_restore_arms.txt` | teen lines (`start`, `checkout`, `restore`) | line missing = arm chala nahi |

### C1 — Census (Steps 1, 3)

| Subject | Check | Broken reading |
|---|---|---|
| `w6d1_step1_census.txt` | har file ki line, `prints_total ≥ prints_inside_begin`, aur ek `prints_inside_begin_total=` | instrument ne file padhi hi nahi |
| `w6d1_step1_classified.txt` | census ki har listed line ki ek classification | ek line chhooti = edit list adhoori |
| `w6d1_step3_census_after.txt` | tere O-class lines me se koi bhi kisi `begin()` block ke andar nahi | print hila, block ke andar hi raha |

### C2 — Harness premise (Steps 2, 4)

| Subject | Check | Broken reading |
|---|---|---|
| census ki chaar `premise` lines | chaaron `resolved_db=relay_w6d1` | ek bhi `relay` = evidence DB pe writes — **ruk jao, counters check karo** |
| control timeline | `src_diff_files_vs_HEAD=0` | control fixed code pe chala |
| fixed timeline | `src_diff_files_vs_HEAD=3` aur teeno hashes control se alag | fixed run purane code pe chala |
| `*_phase1.txt` | `refusal_triggers_left=5` | refusal laga hi nahi |
| `*_final.txt` | `refusal_triggers_left=0` aur audit ke paancho `*_committed ≥ 1` | positive controls bane hi nahi |
| timeline | `relay_python_after=0` | harness ke process bache (`P-13`) |

### C3 — Differential (Step 4) — din ka asli check

| Subject | Check | Kaunsa galat fix isko pass nahi karega |
|---|---|---|
| har tag, fixed run | `fixed_equal=True` | print block ke andar hi raha → lines > committed |
| har tag, fixed run | `committed_ge_1=True` | line hata di → lines `0`, committed `≥ 1` — *"0 false lines"* jaisa dikhta, par log ne sach bhi likhna band kar diya |
| har tag, fixed run | lines aur committed **dono** file me | line `finally` me → refused commit pe bhi print |
| control run ki values | file me hain, compare `ANSWERS` me tu karega | Part B `Q3`, `Q4(a)` |

### C4 — `P-55` (Step 5)

| Subject | Check | Broken reading |
|---|---|---|
| silent arm | `dispatch_error_lines ≥ 2` aur `with_ReadTimeout = dispatch_error_lines` | class abhi bhi nahi |
| closed arm | `with_ConnectError = dispatch_error_lines` | |
| dono arms | `dispatch_error_lines = outbox_attempts` | attempts-line commit se pehle ya baad — dono yahan barabar honi chahiye, kyun, `ANSWERS` me |
| `relay_python_after` | `0` | silent server bacha |

### C5 — `💡` aur close

| Subject | Check |
|---|---|
| `w6d1_step6_rewrites.txt` | `5 · 5 · 6` |
| `w6d1_step7_bench.txt` | `src_diff_files=src/dispatcher.py,src/reaper.py,src/worker.py` · `main`/`database`/`sink`/`models`/`schemas` ke hash Step 0 jaise · `heads=w4d4_sink_unique (head)` · `dbs=postgres,relay` (ya `blogprobe` ke saath, agar rakha — `ANSWERS` me likha ho) · `relay_python=0` · counters `133\|145\|19\|4\|7\|39\|5\|0\|1` · protected wahi · `key_index=0` · `key_tree=0` · `brief_control ≥ 30` · frozen dono lines = Step 0 |
| `w6d1_step7_seals.txt` | `blocked=0`; values file me |
| `w6d1_step7_staged.txt` | `12` lines (ya `13` `.gitattributes` ke saath), `0` KEY, `0` `ANSWERS` |

### C6 — Aaj ye quote nahi honge

| Kya | Kyun |
|---|---|
| *"`P-56` closed"* | fix ek nayi direction kholta hai (`Q4(b)`); `narrowed` |
| *"log ab commit prove karta hai"* | log line ab bhi DB read nahi hai |
| *"dispatcher theek ho gaya"* | aaj sirf log lines badli; behaviour `P-35` ka hai, Week 7 |
| *"`0` false lines"* bina `committed ≥ 1` ke | khokhli barabari |
| seal *"auditable everywhere"* | blob id hi har checkout pe same hai |

---

## PART D — Scope guard

| Kya | Owner | Kyun aaj nahi |
|---|---|---|
| Dispatcher ki retry pacing, bound, outbox terminal state (`P-35`) | **Week 7** | aaj behaviour nahi badalta; aur fix ke baad ki barabari tabhi kuch kehti hai jab baaki sab same ho |
| Aaj ke run me jo bhi *naya* behaviour dikhe | **review** — `DIN_01_ANSWERS.md` me likho, fix mat karo | ek din, ek variable |
| `P-44` (`ENABLE_TEST_ROUTES`) | **Din 2** | `main.py` ka hash aaj gate hai |
| `P-51` (`record_execution`) | **Din 4**, `D-11` ke saath | wo control flow hai, log line nahi |
| Fake provider, `llm_completion` | **Din 2 / Din 3** | |
| `echo=True` band karna | **nahi** | aaj ke har mechanism ka ek witness echo hai |
| Koi migration, evidence DB `relay` pe koi write | **kabhi nahi aaj** | `heads` aur counters gate |
| `logs/` ka koi hissa commit karna | **Week 8** (`D-32` retention half) | |
| `git push` | **user ka faisla** | push se pehle `git log --stat origin/main..HEAD` |

**Cut order, agar time khatam ho:** Step 5 (`P-55` check → Din 2 Step 0.5 ke saath, `+10 min`; fix commit me rehta hai,
check DoD me `slipped`) → Step 0f (`blogprobe` → Din 2). **Kabhi cut nahi:** Step 0a–0e, Steps 2–4 (differential hi din
hai), Step 6 (`💡` — handoff ne naam se owner likha hai), Step 7.

---

*Plan:* [`../../planning/WEEK_06.md`](../../planning/WEEK_06.md) · *Pichhla din:* [`../week_05/DIN_06_BRIEF.md`](../week_05/DIN_06_BRIEF.md) ·
*Seal:* `DIN_01_PREDICTIONS_FROZEN.md` (Step 0c pe banegi) · *Log:* [`../../logs/WEEK_06.md`](../../logs/WEEK_06.md)
