# WEEK 6 · DIN 3 — Provider interface, `llm_completion`, aur Relay ka pehla asli token number

**Budget `125 min` · Layer L2 · `src/` me: ek naya provider module (naam tera), `worker.py` (handler + result write),
`models.py`, `fake_provider.py` (delay param), aur Month 2 ki pehli migration.** Saare runs ek disposable DB
`relay_w6d3` pe. **Evidence DB `relay` pe koi write nahi, koi migration nahi** — bench uska `alembic_version` padhta hai.

> Kal provider ne `14` gine, uvicorn ne `12`, caller ne `15` bheje. Aaj pehli baar ye call **Relay ka worker** karega,
> aur ek chautha record banega: `jobs` + `job_executions`. Aur pehli baar ek **asli** provider, jiska apna bill hai.
> **Aaj ka sawaal:** jab provider `+1` kahe aur Relay kuch aur, to Relay ka kaunsa column bata sakta hai ki bill bana?

### Din 3 se PEHLE (ye nahi hua to Step 4 `slipped`, baaki din chalta hai)

1. Provider chuno (Step 1 Faisla 6 ka table pehle padh lo) aur uske console se ek API key banao.
2. `.env` me ek line: `<TERA_KEY_VAR>=<value>` (jaise `GEMINI_API_KEY=...`). **Key kabhi:** chat me, Gemini me,
   `ANSWERS` me, shell command me (`$env:X = '...'` PowerShell history me chala jaata hai), `payload` me, code me nahi.
3. `git check-ignore -v .env` → `.gitignore` ki line dikhni chahiye.

**Aaj ki files** (`D-32`: BRIEF/FROZEN publish, KEY/ANSWERS Local):

| File | Kya | Kaun likhta hai |
|---|---|---|
| `labs/w6d3_interface_check.py` | provider module ka bahar se shape | BRIEF me diya hai — save karo |
| `labs/w6d3_job_run.py` | ek job asli worker se, disposable DB pe, census file | BRIEF me diya hai — save karo |
| `labs/w6d3_key_scan.ps1` | key logs/tracked/history/DB me kahin hai? controls ke saath | BRIEF me diya hai — save karo |
| provider module (jaise `src/providers.py`) | interface + `FakeProvider` + real provider | **tu** |
| `src/worker.py` · `src/models.py` · `src/fake_provider.py` | handler, result write, delay param | **tu** |
| `alembic/versions/w6d3_*.py` | additive migration | **tu** |
| `.env.example` | sirf `<TERA_KEY_VAR>=` (khaali value) | **tu** |
| `DIN_03_PREDICTIONS_FROZEN.md` · `DIN_03_ANSWERS.md` | seal · Beat 4 (Local) | **tu** |

Teeno lab scripts reviewer ne ek throwaway copy (`%TEMP%`, disposable DB, ek naive handler) pe chala ke dekhe hain.
Tere code pe unka output Part B hai.

**Kal ke teen record defects, aaj ka fix:**

| Kal | Aaj |
|---|---|
| seal hash file commit ke `11 s` baad **bani** (CreationTime) | `w6d3_step0_seal_commit.txt` me `hash_file_before_commit=` — Step 6 bench padhta hai |
| C5 `7 ≠ 8` fail tha aur `ANSWERS` me *"All close bench criteria met"* | Step 6 ki explanation me **har `False` check naam se**. Ek bhi `False` ho to *"all met"* likhna galat record hai |
| chaar `[padh ke]` reading gaps | har `[padh ke]` jawab me **file:line + us line se ek chhota quote** (copy-paste). Quote nahi = file khuli nahi |

---

## PART A — Steps

### Step 0 — 10 min: commit, bench, seal

**Pehle, isi PowerShell window me (baaki din yahi window):**

```powershell
cd d:\PROJECTS\relay
$KeyVar  = '<TERA_KEY_VAR>'     # sirf NAAM, value kabhi nahi
$ProvMod = 'src.providers'      # Step 1 me tera module ka naam; badle to yahan badlo
```

**0a. Ye BRIEF commit — named file, `-A` kabhi nahi.**

```powershell
git status --short
git add docs/daily/week_06/DIN_03_BRIEF.md
git diff --cached --name-only | Out-File -Encoding utf8 logs\w6d3_step0_staged.txt
Get-Content logs\w6d3_step0_staged.txt          # exactly 1 line
git commit -m "docs(w6d3): Din 3 brief"
```

**0b. Bench.**

```powershell
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("head=" + (git rev-parse --short HEAD))
$o.Add("src_diff=" + @(git diff --name-only HEAD -- src/ alembic/).Count)
$o.Add("src_untracked=" + @(git ls-files --others --exclude-standard -- src/ alembic/).Count)
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py src/sink.py src/models.py src/schemas.py src/fake_provider.py | ForEach-Object { $o.Add("hash " + $_) }
$o.Add("heads=" + ((.\.venv\Scripts\python.exe -m alembic heads 2>&1) -join ' | '))
$o.Add("relay_revision=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -c "SELECT version_num FROM alembic_version;") -join ''))
$o.Add("relay_python=" + @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" }).Count)
$o.Add("listen_8000_8002=" + @(Get-NetTCPConnection -State Listen -LocalPort 8000, 8002 -ErrorAction SilentlyContinue).Count)
$o.Add("dbs=" + ((docker exec relay-db-1 psql -U postgres -d postgres -t -A -c "SELECT string_agg(datname, ',' ORDER BY datname) FROM pg_database WHERE NOT datistemplate;") -join ''))
$o.Add("counters=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -F '|' -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');") -join ''))
$o.Add("protected=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -c "SELECT string_agg(id || '|' || status || '|' || attempts || '|' || claim_generation, ' ; ' ORDER BY id) FROM jobs WHERE id IN (108, 128, 136);") -join ''))
$o.Add("dotenv_has_keyvar=" + @(Select-String -Path .env -Pattern "^\s*$KeyVar\s*=").Count)
$o.Add("env_ignored=" + $(git check-ignore -q .env; if ($LASTEXITCODE -eq 0) { 'True' } else { 'False' }))
$o.Add("env_example_keyvar=" + @(Select-String -Path .env.example -Pattern "^\s*$KeyVar\s*=").Count)
$o.Add("key_index=" + @(git ls-files -- "*_KEY.md").Count)
$o.Add("brief_control=" + @(git ls-files -- "*_BRIEF.md").Count)
$o | Out-File -Encoding utf8 logs\w6d3_step0_bench.txt
pwsh -File scripts\seal_audit.ps1 -Out logs\w6d3_step0_seals.txt
Get-Content logs\w6d3_step0_bench.txt
```

Expected (instrument): `src_diff=0` · `src_untracked=0` · hashes `0eb94373…` worker · `95518640…` reaper · `920d0d4a…`
dispatcher · `7241c055…` main · `fc5bde22…` database · `fcfc9059…` sink · `04f04f84…` models · `a53e7cc8…` schemas ·
`53f1cbfe…` fake_provider · `heads=w4d4_sink_unique (head)` · **`relay_revision=w4d4_sink_unique`** · `relay_python=0` ·
`listen_8000_8002=0` · `dbs=postgres,relay` · counters `133|145|19|4|7|39|5|0|1` · protected
`108|dead_letter|4|0 ; 128|succeeded|4|4 ; 136|running|1|1` · **`dotenv_has_keyvar=1`** · `env_ignored=True` ·
`env_example_keyvar=0` · `key_index=0` · `brief_control=32` · seals `seals=18 … blocked=0`.
`dotenv_has_keyvar=0` → Step 4 `slipped`, `ANSWERS` me likho, baaki din chalao.

**0c. Seal.** `docs/daily/week_06/DIN_03_PREDICTIONS_FROZEN.md`, har sub-part alag. **`[padh ke]` = file:line + ek
copy kiya hua quote.** Phir ek command, ye file dobara kabhi nahi:

```powershell
$f = "docs\daily\week_06\DIN_03_PREDICTIONS_FROZEN.md"
@(("sha256=" + (Get-FileHash -Algorithm SHA256 $f).Hash), ("git_blob=" + (git hash-object $f))) | Out-File -Encoding utf8 logs\w6d3_step0_frozen_hash.txt
git add docs/daily/week_06/DIN_03_PREDICTIONS_FROZEN.md
git commit -m "seal(w6d3): Din 3 predictions frozen before any experiment"
$hf = Get-Item logs\w6d3_step0_frozen_hash.txt
$ct = [datetimeoffset]::Parse((git log -1 --format=%cI))
@(("head_blob=" + (git rev-parse "HEAD:docs/daily/week_06/DIN_03_PREDICTIONS_FROZEN.md")), ("seal_commit_time=" + $ct.ToString('o')), ("hash_file_before_commit=" + ($hf.CreationTime -lt $ct.LocalDateTime.AddSeconds(1)))) | Out-File -Encoding utf8 logs\w6d3_step0_seal_commit.txt
Get-Content logs\w6d3_step0_frozen_hash.txt, logs\w6d3_step0_seal_commit.txt
```

(`AddSeconds(1)`: `%cI` second-granular hai, CreationTime nahi.) `git_blob = head_blob`, `hash_file_before_commit=True`.

**0d. `DIN_03_ANSWERS.md`** — har step: `Observed:` (file + value) aur `Meri explanation (KEY se pehle):`. Sabse upar
**`## Din 2 carry`**, chaar line jo kal owed thi: Step 1b pick ki cost · `labs/w5d4_pool_probe.py` ab flag ke bina `404`
· README rows `525`/`526`/`563` purani (owner Din 6) · `src/fake_provider.py` kaise bani (kisne kaunsi lines likhi).
Har step ke baad, KEY kholne se pehle:

```powershell
"step=<N> at=" + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff') + " sha=" + (Get-FileHash -Algorithm SHA256 docs\daily\week_06\DIN_03_ANSWERS.md).Hash.Substring(0, 12) | Out-File -Append -Encoding utf8 logs\w6d3_answers_trail.txt
```

**Executable end:** staged (1) · commit · bench · seals · frozen hash (exactly 2 lines) · seal commit · seal_commit file
(3 lines). Trail `step=0`.

| Term | Kya hai |
|---|---|
| `alembic_version` | DB ke andar ek table, ek row: ye DB kis migration revision tak pahuncha |
| `git check-ignore -q` | exit `0` = path ignored hai |

---

### Step 0.5 — 10 min: Din 2 ka `💡`, apne shabdon me

`docs/logs/WEEK_06.md` Din 2 ka `📊 Measured / Observed` (`~407`) padho, **`💡` section (`~677`) nahi**. Uske upar
`### 💡 What I understood — own words, <aaj ki date>`, 3–5 points, har ek me ek number ya file. **`narrows` /
`eliminates` dhyan se** — kal tere Din 1 block me dono ek saath the. Phir reviewer section padho, apne block ke neeche
`Gaps vs reviewer: …`. Reviewer section mitao mat.

```powershell
$f = 'docs\logs\WEEK_06.md'; $lines = @(Get-Content $f)
$din = ($lines | Select-String -Pattern '^## Din 2 ' | Select-Object -First 1).LineNumber
$next = ($lines | Select-String -Pattern '^## Din ' | Where-Object { $_.LineNumber -gt $din } | Select-Object -First 1).LineNumber
if (-not $next) { $next = $lines.Count + 1 }
$in = { param($m) $m.LineNumber -gt $din -and $m.LineNumber -lt $next }
$own = @($lines | Select-String -Pattern '^### 💡 What I understood — own words' | Where-Object { & $in $_ })
$gap = @($lines | Select-String -Pattern '^Gaps vs reviewer:' | Where-Object { & $in $_ })
$rev = @($lines | Select-String -Pattern '^### 💡 What the session established' | Where-Object { & $in $_ })
$ord = ($own.Count -eq 1 -and $gap.Count -eq 1 -and $rev.Count -eq 1 -and $own[0].LineNumber -lt $gap[0].LineNumber -and $gap[0].LineNumber -lt $rev[0].LineNumber)
"section_from=$din own=$($own.Count) gaps=$($gap.Count) rev=$($rev.Count) order_own_gaps_rev=$ord eliminat_words_in_own_block=" + @($lines[($own[0].LineNumber)..($gap[0].LineNumber - 2)] | Select-String -Pattern 'eliminat').Count | Out-File -Encoding utf8 logs\w6d3_step05_rewrite.txt
Get-Content logs\w6d3_step05_rewrite.txt
```

Pehle `[MEASURED-R]`: Din 2 section `own=0 gaps=0 rev=1`. Baad: `own=1 gaps=1 rev=1 order_own_gaps_rev=True`.
`eliminat_words_in_own_block` `0` na ho to wo shabd evidence se match karo. Trail `step=0.5`.

---

### Step 1 — 15 min: interface ka faisla (Situation 3) — `D-11` ki zameen

**Gemini se options aur cost, pick kabhi nahi.** Saat faisle, har ek ek line `ANSWERS` me: pick + cost.

**Faisla 1 — module kahan.** Ek file (`src/providers.py`: base + `FakeProvider` + real) · ek package
(`src/providers/`) · `worker.py` ke andar. Cost socho: worker import graph, aur **kya ye module `src.database` import
karta hai** (wo import pe evidence-DB engine banata hai).

**Faisla 2 — failure bahar kaise aata hai.** Kal measured: httpx `4xx`/`5xx` pe raise nahi karta.

| Option | Shape | Cost |
|---|---|---|
| (A) **typed exceptions** | success pe `(text, tokens_in, tokens_out)`; failure pe `ProviderError` ke subclasses (status, `retry_after` attribute) | worker ka existing `except Exception` path bina badle chalta hai; Din 4 class pe classify karega. Exception ke saath partial data (jaise ek billed-but-failed call ke tokens) bahar nahi aata |
| (B) **result object** | hamesha `Completion(ok, text, tokens_in, tokens_out, error_kind, status, …)` | har caller ko `ok` check karna hai — bhoola to `500` phir success (kal ka exact bug). Worker sirf exceptions pe retry karta hai, to handler ko khud raise karna padega |
| (C) dono ka mel | apna design | likho kaunsa half kahan |

**Faisla 3 — HTTP client ki life.** Har call pe naya `httpx.AsyncClient` · ek shared client (process-level). Cost: har
call pe connection + SSL context setup, vs ek client jiska close/lifetime kisi ko sambhalna hai. Kitna farak — Step 2
ka census dikhayega.

**Faisla 4 — timeout ka number.** Kal: `timeout=5.0` = chaar phase-timeouts, deadline nahi. Ek real LLM call ka pehla
byte kai second le sakta hai. Number chuno, aur ek line: **timeout se upar ki call ka kya hota hai** (Relay ki taraf
retry = provider ki taraf doosri call). Poora deadline faisla `D-22`, Month 3 — aaj sirf number.

**Faisla 5 — provider kaun chunta hai, real ya fake.**

| Option | Cost |
|---|---|
| (i) **per-process env var** (jaise `RELAY_LLM_PROVIDER`) | switch = restart; har worker ek hi provider |
| (ii) **per-job `payload` field** | `POST /jobs` unauthenticated hai — **koi bhi caller paid provider chun sakta hai** (cost amplification), aur `payload` `echo=True` me log hota hai |

Fake mode (kal ka `x-fake-mode` header) handler tak kaise pahunchta hai — `payload` ka field ya env — wo bhi likho.
Fake provider URL **`127.0.0.1`** likho, `localhost` nahi (`D-28`: is host pe `localhost` pehle `::1` try karta hai).

**Faisla 6 — real provider, aur raw `httpx` vs SDK.** Limits aur terms din pe provider ke page pe check karo — neeche
wala snapshot `2026-10-03` ka search hai, verify nahi kiya:

| Option | Kya milta hai | Cost |
|---|---|---|
| Google Gemini API | free tier; usage response me (`usageMetadata`) | free tier pe content product improvement ke liye use hota hai ([Gemini API terms](https://ai.google.dev/gemini-api/terms)); thinking models ke tokens alag field me |
| Groq | free tier, OpenAI-compatible JSON | per-model RPM/RPD/TPD limits ([Groq rate limits](https://console.groq.com/docs/rate-limits)) |
| OpenRouter `:free` models | ek key, kai models | free tier pe roz ki request limit chhoti ([OpenRouter limits](https://openrouter.ai/docs/api_reference/limits)); ek hop aur — asli provider beech me badal sakta hai |
| Paid (OpenAI, Anthropic, …) | saaf data terms | card aur asli paisa |

**Raw `httpx` vs SDK:** SDK = nayi dependency, `D-33` ke hisaab se `==` pin + uske transitive deps. **Aur SDK ki apni
retry policy padho** — kai SDK default me retry karte hain ([OpenAI SDK, 2 retries default](https://community.openai.com/t/openai-base-client-retrying-request-to-chat-completions-in-x-seconds/1355000/2)).
Agar hai, to Relay ka `attempts=1` provider ki `3` calls ho sakti hain — is hafte ki saari ginti toot jaati hai. SDK
chuno to `max_retries=0` (ya jo bhi uska naam ho) aur `ANSWERS` me likho. **Key header me jaaye ya URL query me — dono
jagah kaam karta hai; cost Part B `Q4(c)` hai, pehle wo padho.**

**Faisla 7 — fake provider ke kal ke teen review notes:** (1) unknown mode → chupchaap `200` · (2) startup line literal
port · (3) `trickle` ke tokens hardcoded. Har ek: *aaj fix* / *Din 4 Step 0* / *kabhi nahi*, ek line cost. (1) Din 4
ke retry experiment ko seedha chhoota hai.

**Executable end — interface ka stub.** Module banao: dono provider classes, `async def complete(...)`, Faisla 2 ki
exception/result classes, bodies `raise NotImplementedError`. `.env.example` me `<TERA_KEY_VAR>=` (khaali). Phir
`labs/w6d3_interface_check.py` save karo:

```python
r"""labs/w6d3_interface_check.py -- Week 6 Din 3, Step 1: what the provider module LOOKS like from outside.
Imports one module and lists (1) every class defined in it that has a `complete` method, with its signature and
whether it is a coroutine function, (2) every exception class defined in it, with its bases, (3) whether importing it
pulled in src.database (which builds the evidence-DB engine at import), and (4) whether a fresh interpreter can import
it with the key variable REMOVED from the environment. Values and labels only (P-52).
Usage: .\.venv\Scripts\python.exe -u labs\w6d3_interface_check.py --module src.providers [--key-name YOUR_KEY_VAR]"""
import argparse
import importlib
import inspect
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

ap = argparse.ArgumentParser()
ap.add_argument("--module", required=True)
ap.add_argument("--key-name", default="")
a = ap.parse_args()

before = set(sys.modules)
mod = importlib.import_module(a.module)
print(f"module={a.module} file={Path(mod.__file__).relative_to(REPO)}")
print(f"src_database_imported={'src.database' in sys.modules} newly_imported_src="
      + ",".join(sorted(m for m in set(sys.modules) - before if m.startswith("src."))))
for name, obj in sorted(vars(mod).items()):
    if not inspect.isclass(obj) or obj.__module__ != mod.__name__:
        continue
    if issubclass(obj, BaseException):
        print(f"exception_class={name} bases={','.join(b.__name__ for b in obj.__bases__)}")
    elif hasattr(obj, "complete"):
        fn = getattr(obj, "complete")
        print(f"provider_class={name} complete_is_coroutine={inspect.iscoroutinefunction(fn)} "
              f"signature={inspect.signature(fn)}")
    else:
        print(f"other_class={name}")
if a.key_name:
    env = {k: v for k, v in os.environ.items() if k != a.key_name}
    r = subprocess.run([sys.executable, "-c", f"import {a.module}"], cwd=REPO, env=env, capture_output=True, text=True)
    last = (r.stderr.strip().splitlines() or ["-"])[-1]
    print(f"import_without_{a.key_name}=" + ("ok" if r.returncode == 0 else "fail:" + last.split(":")[0]))
```

```powershell
.\.venv\Scripts\python.exe -u labs\w6d3_interface_check.py --module $ProvMod --key-name $KeyVar | Out-File -Encoding utf8 logs\w6d3_step1_interface.txt
"env_example_keyvar=" + @(Select-String -Path .env.example -Pattern "^\s*$KeyVar\s*=\s*$").Count | Out-File -Append -Encoding utf8 logs\w6d3_step1_interface.txt
Get-Content logs\w6d3_step1_interface.txt
```

Expected: `src_database_imported=False` · do `provider_class=` lines, `complete_is_coroutine=True` · Faisla 2 ki classes
dikhein · `import_without_<KEY>=ok` · `env_example_keyvar=1` (naam + khaali value). Trail `step=1`.

| Term | Kya hai |
|---|---|
| interface | ek function/method ka shape jo har provider follow kare — caller ko pata na chale kaun sa hai |
| typed exception | `Exception` ka apna subclass; `except ProviderRateLimited:` class se pakadta hai |
| coroutine function | `async def` — call karne pe chalti nahi, awaitable deti hai |
| SDK | provider ki apni Python library, httpx jaise client ke upar |

---

### Step 2 — 20 min: `FakeProvider` + `llm_completion`, ek job end to end

**2a — 3 min: disposable DB.**

```powershell
docker exec relay-db-1 psql -U postgres -d postgres -c "CREATE DATABASE relay_w6d3;" | Out-File -Encoding utf8 logs\w6d3_step2a_db.txt
$env:DATABASE_URL = 'postgresql+asyncpg://postgres:relay@localhost:5433/relay_w6d3'
.\.venv\Scripts\python.exe -m alembic upgrade head 2>&1 | ForEach-Object { "$_" } | Out-File -Append -Encoding utf8 logs\w6d3_step2a_db.txt
Remove-Item Env:DATABASE_URL
Select-String -Path logs\w6d3_step2a_db.txt -Pattern 'resolved_db=|CREATE DATABASE|w4d4_sink_unique'
```

**Ruk jao agar line `alembic resolved_db=relay_w6d3 source=env` nahi hai.** (`Remove-Item` isliye: baad ki har alembic
command apna env khud set karegi — Part B `Q3(a)`.)

**2b — 12 min: code (tu).** Rules:

1. `FakeProvider.complete` → `POST http://127.0.0.1:8002/v1/complete`, fake mode Faisla 5 ke raaste se header me.
   Non-2xx kabhi success na bane (Faisla 2 ka shape).
2. `llm_completion` handler `REGISTRY` me. `payload` se prompt (aur jo params tune chune). **Key `payload` me nahi.**
3. Handler result **return** kare — worker abhi use ignore karta hai (`worker.py:266`); store Step 3.
4. Ek log line `[llm] job_id=… tokens_in=… tokens_out=…` — ye **provider ke response** ka record hai, DB ka nahi.
5. Worker ka claim/mark/retry/heartbeat code **nahi badalta**. `D-11` aaj nahi: har failure purane retry path se.

**2c — 5 min: do arms.** `labs/w6d3_job_run.py` save karo (neeche, Part A ke end me). Phir:

```powershell
.\.venv\Scripts\python.exe -m py_compile src\worker.py; "py_compile_exit=$LASTEXITCODE" | Out-File -Encoding utf8 logs\w6d3_step2_compile.txt
.\.venv\Scripts\python.exe -u labs\w6d3_job_run.py --label s2_ok --fake --payload '{"prompt": "the quick brown fox"}'
.\.venv\Scripts\python.exe -u labs\w6d3_job_run.py --label s2_500 --fake --deadline 60 --payload '{"prompt": "the quick brown fox", "fake_mode": "500"}'
```

`fake_mode` sirf example hai — jo field tera handler padhta hai wahi likho (env pick kiya to `--env NAME=VALUE`). `500`
arm `~17 s` (do backoffs). Har run `logs\w6d3_s2_*_census.txt` likhta hai. Trail `step=2`.

| Term | Kya hai |
|---|---|
| disposable DB | experiment ke liye banaya, din ke end me drop. Evidence DB ki ginti isse nahi hilti |
| census | ek run ki values ki ek file — label + value, koi conclusion nahi (`P-52`) |
| `ledger_delta` | fake provider ki apni ginti, run se pehle aur baad ka farak |

---

### Step 3 — 20 min: result kahan jaata hai — Month 2 ki pehli migration

**3a — 5 min: faisla (Situation 3).**

| Option | Kya milta hai | Cost |
|---|---|---|
| (a) **`jobs` pe columns** (`result_text`, `tokens_in`, `tokens_out`, …) | ek row, ek read; mark ke `UPDATE` me hi likh sakte ho — status ke saath atomic | sirf **aakhri** attempt bachta hai; fail hue attempt ka koi token record nahi. Bada text TOAST me jaata hai |
| (b) **per-attempt table** (jaise `llm_calls`: `job_id`, `claim_generation`, outcome, tokens, time) | har call ka ek row, fail hui bhi — Week 8 `job_costs` ka source | kab likha jaaye: handler ke andar alag transaction (mark fail ho to bhi row bachti hai) ya mark ke saath (ek hi commit, par fenced worker ka row bhi jaata hai). Har read ek join |
| (c) **dono** | job ka result + har call ka bill | do jagah likhna; dono ka meaning alag rakhna padega |

Ek soch jo pick se pehle karni hai: **fencing.** Mark `claim_generation == generation` pe hi likhta hai
(`worker.py:312–324`). Fenced worker ka *result* job ka nahi hona chahiye — par uska *bill* to ban chuka. Kaunsa
option dono ko sahi jagah rakhta hai? Pick + Rejected naam se ek asli faisla hai → **`D-34`** (grep first:
`Select-String -Path docs\DECISIONS.md -Pattern '^## D-34'` → `0` hona chahiye).

**3b — 10 min: migration (tu), disposable pe.** Rules: **additive only** — naye columns nullable, **bina volatile
default**; nayi table theek. Revision id `w6d3_<kuch>`, `down_revision = 'w4d4_sink_unique'`. `downgrade()` likho jo
upgrade ka ulta kare. `models.py` me wahi columns. Autogenerate use karo to output padh ke hi rakho.

```powershell
$env:DATABASE_URL = 'postgresql+asyncpg://postgres:relay@localhost:5433/relay_w6d3'
.\.venv\Scripts\python.exe -m alembic heads 2>&1 | ForEach-Object { "$_" } | Out-File -Encoding utf8 logs\w6d3_step3_migrate.txt
.\.venv\Scripts\python.exe -m alembic upgrade head 2>&1 | ForEach-Object { "$_" } | Out-File -Append -Encoding utf8 logs\w6d3_step3_migrate.txt
.\.venv\Scripts\python.exe -m alembic check 2>&1 | ForEach-Object { "$_" } | Out-File -Append -Encoding utf8 logs\w6d3_step3_migrate.txt
Remove-Item Env:DATABASE_URL
Select-String -Path logs\w6d3_step3_migrate.txt -Pattern 'resolved_db=|\(head\)|Running upgrade|upgrade operations|Target database'
```

Expected: har `resolved_db=` line `relay_w6d3 source=env` · ek hi head `w6d3_…` · `Running upgrade w4d4_sink_unique ->
w6d3_…` · `alembic check` → `No new upgrade operations detected` (models aur migration ek hi baat kehte hain).

**3c — 5 min: write wire karo, phir data ke saath down/up.** Worker ab handler ka return value tere 3a pick ke
mutabik likhta hai. Phir (`--table` sirf agar (b)/(c) chuna; naam tera):

```powershell
.\.venv\Scripts\python.exe -u labs\w6d3_job_run.py --label s3_ok --fake --payload '{"prompt": "the quick brown fox"}' --table llm_calls
$cols = "SELECT table_name || '.' || column_name FROM information_schema.columns WHERE table_schema='public' AND (table_name NOT IN ('jobs','job_executions','side_effects','outbox','sink_deliveries','alembic_version') OR column_name NOT IN ('id','type','payload','status','attempts','created_at','claimed_at','next_attempt_at','idempotency_key','request_fingerprint','claim_generation','completed_at','last_error','job_id','worker_id','executed_at','effect_key','dispatched_at','received_at','body')) ORDER BY 1;"
$env:DATABASE_URL = 'postgresql+asyncpg://postgres:relay@localhost:5433/relay_w6d3'
& { "--- up"; docker exec relay-db-1 psql -U postgres -d relay_w6d3 -t -A -c $cols
    .\.venv\Scripts\python.exe -m alembic downgrade -1 2>&1 | ForEach-Object { "$_" } | Select-String 'resolved_db=|Running downgrade'
    "--- down"; docker exec relay-db-1 psql -U postgres -d relay_w6d3 -t -A -c $cols
    .\.venv\Scripts\python.exe -m alembic upgrade head 2>&1 | ForEach-Object { "$_" } | Select-String 'resolved_db=|Running upgrade'
    "--- up_again"; docker exec relay-db-1 psql -U postgres -d relay_w6d3 -t -A -c $cols } | Out-File -Encoding utf8 logs\w6d3_step3_downup.txt
Remove-Item Env:DATABASE_URL
Get-Content logs\w6d3_step3_downup.txt
```

Phir **wahi `s3_ok` job ka result dobara padho** (job id census me hai) — `ANSWERS` me ek line. Ye `Q3(b)` hai.
Trail `step=3`.

| Term | Kya hai |
|---|---|
| additive migration | sirf jodta hai (column/table), kuch hataata ya badalta nahi |
| `alembic check` | models aur DB ka diff; kuch bacha ho to non-zero exit |
| TOAST | Postgres bade values (`~2 KB` se upar) row ke bahar alag rakhta hai |
| volatile default | `DEFAULT clock_timestamp()` jaisa — har row ki alag value, to table rewrite |

---

### Step 4 — 25 min: real provider — ek call, asli tokens, teen record

**4a — 12 min: real provider ki `complete` (tu).** Faisla 6 ke hisaab se. Rules: key `os.environ` se **call ke
waqt** (import pe nahi — Step 1 ka `import_without_…=ok`); key log, exception message, return value me nahi; output
tokens ka cap ek param se (cost); response ka usage → `tokens_in`/`tokens_out`. Kaunsa field kya ginta hai — provider
docs se, `ANSWERS` me ek line.

**4b — 8 min: ek job.** `w6d3-canary` key scan ka DB control hai — payload me rakhna zaroori.

```powershell
.\.venv\Scripts\python.exe -u labs\w6d3_interface_check.py --module $ProvMod --key-name $KeyVar | Out-File -Encoding utf8 logs\w6d3_step4_interface.txt
.\.venv\Scripts\python.exe -u labs\w6d3_job_run.py --label s4_real --deadline 90 --env RELAY_LLM_PROVIDER=<tera_value> --payload '{"prompt": "the quick brown fox", "tag": "w6d3-canary"}' --table llm_calls
```

(`--env` / `--table` apne Faisla 5 aur 3a ke hisaab se badlo.) Terminal `dead_letter` aaye to `last_error_tail` padho
— **teen attempts = teen calls**, provider ki free limit me gino.

**4c — 5 min: provider ka record + key scan.** Provider console/usage page kholo. `logs\w6d3_step4_dashboard.txt` me
haath se: `checked_at=<time>` · page kya dikhata hai (requests, tokens) · granularity (per-request/day/model) · *"is
call ki line nahi dikhi"* bhi ek valid value hai. Fir 15–30 min baad ek doosri line `checked_at=` (Step 6 se pehle).
`labs/w6d3_key_scan.ps1` save karo (neeche), phir:

```powershell
pwsh -File labs\w6d3_key_scan.ps1 -KeyName $KeyVar -Out logs\w6d3_step4_keyscan.txt
```

Expected: har `*_hits=0`, aur har `*_control_hits ≥ 1` (`history_file_exists=False` ho to wo row likho, chhodo mat).
Ek bhi hit → **ruko**, key rotate karo (provider console), `ANSWERS` me sirf *kahan* likho, value nahi. Trail `step=4`.

| Term | Kya hai |
|---|---|
| usage field | provider ke response me token ginti — provider ka *bayan*, uska bill nahi |
| thinking/reasoning tokens | kuch models jawab se pehle andar tokens banate hain; kuch APIs inhe alag field me dete hain |
| key rotation | purani key revoke, nayi banao — leak ka ek hi pakka ilaaj |

---

### Step 5 — 15 min: slow provider vs heartbeat aur lease (hang nahi — wo Din 5)

**5a — 5 min (tu):** fake provider ka slow mode request se seconds le (jaise `x-fake-delay` header), ek **cap** ke
saath (unauthenticated loopback hai, `P-44` ki shakal). Handler use params se pass kare. Apna client timeout dekho —
`25 s` ki call us ke andar aani chahiye, warna `ANSWERS` me likho aur jo hota hai wahi naapo.

**5b — 10 min: do runs, reaper ke saath.**

```powershell
.\.venv\Scripts\python.exe -u labs\w6d3_job_run.py --label s5_d3 --fake --reaper --deadline 60 --payload '{"prompt": "the quick brown fox", "fake_mode": "slow", "delay": 3}'
.\.venv\Scripts\python.exe -u labs\w6d3_job_run.py --label s5_d25 --fake --reaper --deadline 90 --linger 4 --payload '{"prompt": "the quick brown fox", "fake_mode": "slow", "delay": 25}'
```

(Field names tere.) Census se `ANSWERS` me table: delay · `completed_minus_first_executed_s` ·
`worker_heartbeat_sent_lines` · `echo_heartbeat_update_at` · `reaper_reclaim_lines` · `ledger_delta` · job row ka
`claimed_at` vs `completed_at`. Trail `step=5`.

| Term | Kya hai |
|---|---|
| lease | `claimed_at` se `30 s` (`reaper.py:12`); usse purana `running` row reaper `pending` kar deta hai |
| heartbeat | ek alag asyncio task jo `claimed_at = now()` likhta hai (`worker.py:36–70`) |

---

### Step 6 — 10 min: close

**6a. Key scan pehle (DB drop se pehle — DB domain ko DB chahiye):**

```powershell
pwsh -File labs\w6d3_key_scan.ps1 -KeyName $KeyVar -Out logs\w6d3_step6_keyscan_predrop.txt
docker exec relay-db-1 psql -U postgres -d postgres -c "DROP DATABASE relay_w6d3 WITH (FORCE);" | Out-File -Encoding utf8 logs\w6d3_step6_drop.txt
```

**6b. Bench:** Step 0b wala block, `step0` ki jagah `step6`, aur ye teen lines `$o | Out-File` se pehle jodo:

```powershell
$sealAt = [datetimeoffset]::Parse((git log -1 --format=%cI -- docs/daily/week_06/DIN_03_PREDICTIONS_FROZEN.md))
$firstExp = Get-ChildItem logs -Filter 'w6d3_s2_*' | Sort-Object LastWriteTime | Select-Object -First 1
$o.Add("seal_before_first_experiment=" + ($sealAt.LocalDateTime -lt $firstExp.LastWriteTime) + " first=" + $firstExp.Name)
$trail = @(Get-Content logs\w6d3_answers_trail.txt)
$o.Add("trail_lines=" + $trail.Count + " trail_distinct_sha=" + @($trail | ForEach-Object { ($_ -split 'sha=')[1] } | Sort-Object -Unique).Count)
$o.Add("seal_commit_file=" + ((Get-Content logs\w6d3_step0_seal_commit.txt) -join ' ; '))
```

**6c. Commit — named files.** List tere file names pe depend karti hai; `.env`, `ANSWERS`, `KEY`, `FROZEN` kabhi nahi.

```powershell
git add <provider module> src/worker.py src/models.py src/fake_provider.py alembic/versions/<w6d3 file> .env.example labs/w6d3_interface_check.py labs/w6d3_job_run.py labs/w6d3_key_scan.ps1 docs/logs/WEEK_06.md
# D-34 likha ho to docs/DECISIONS.md bhi
git diff --cached --name-only | Out-File -Encoding utf8 logs\w6d3_step6_staged.txt
pwsh -File labs\w6d3_key_scan.ps1 -KeyName $KeyVar -Out logs\w6d3_step6_keyscan_staged.txt
Get-Content logs\w6d3_step6_staged.txt, logs\w6d3_step6_keyscan_staged.txt
git commit -m "feat(w6d3): provider interface, llm_completion, result storage migration, real provider; job harness, key scan"
```

`keyscan_staged` me DB ab nahi hai → `db_dump_bytes=0 db_control_hits=0` **expected**; baaki domain pichhle jaise.
`staged_diff_hits=0` na ho to commit mat karo. Step 6 ki explanation: har `False` check ka naam.

---

### Saved scripts

**`labs/w6d3_job_run.py`** — ek job, disposable DB, census:

```python
r"""labs/w6d3_job_run.py -- Week 6 Din 3: ONE job through Relay's real worker, on a DISPOSABLE database.
Optionally starts the fake provider (127.0.0.1:8002) and the reaper, starts the worker, inserts one job, waits for a
terminal status or a deadline, stops every child it started, and writes one census file. Values and labels only; it
writes no conclusions (P-52). Refuses the evidence DB `relay`. The DB must already exist and be migrated (Step 2a).
Usage (PowerShell -- single quotes keep the JSON intact):
  .\.venv\Scripts\python.exe -u labs\w6d3_job_run.py --label ok --fake --payload '{"prompt": "the quick brown fox"}'
Options: --db (default relay_w6d3) · --type (default llm_completion) · --table NAME (also dump NAME's rows whose
job_id is this job; repeatable) · --env NAME=VALUE (extra env for the worker; repeatable) · --reaper · --deadline S ·
--linger S (keep the processes S seconds after the terminal status, default 2)."""
import argparse
import asyncio
import datetime as dt
import json
import os
import re
import subprocess
import time
from pathlib import Path

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

REPO = Path(__file__).resolve().parents[1]
PY = REPO / ".venv" / "Scripts" / "python.exe"
FAKE = "http://127.0.0.1:8002"
TERMINAL = {"succeeded", "dead_letter", "failed"}
ECHO_TS = r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) INFO sqlalchemy\.engine\.Engine "


def base_url() -> str:
    env_file = REPO / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ["DATABASE_URL"]


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else f"git_error_{r.returncode}"


def start(name: str, module_args: list[str], env: dict, run: str, logs: Path) -> subprocess.Popen:
    e = dict(env, RELAY_PROCESS_NAME=f"{name}_w6d3")
    out = open(logs / f"{run}_{name}.log", "w", encoding="utf-8")
    err = open(logs / f"{run}_{name}.err.log", "w", encoding="utf-8")
    return subprocess.Popen([str(PY), "-u", *module_args], cwd=REPO, env=e, stdout=out, stderr=err)


def stop_all(procs: list[subprocess.Popen]) -> int:
    for p in reversed(procs):
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
    for p in procs:
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    # the venv python.exe is a launcher stub; the real interpreter is its child (P-53(b)) -- sweep by command line
    ps = ("$n = @(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*"
          + str(REPO) + "*' -and $_.CommandLine -match 'src\\.(worker|reaper|fake_provider)' });"
          " $n | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; $n.Count")
    r = subprocess.run(["pwsh", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    return int(r.stdout.strip() or "0")


def wait_for_line(path: Path, needle: str, seconds: float) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if path.exists() and needle in path.read_text(encoding="utf-8", errors="replace"):
            return True
        time.sleep(0.2)
    return False


async def ledger(client: httpx.AsyncClient):
    try:
        return (await client.get(f"{FAKE}/v1/ledger", timeout=3.0)).json().get("calls")
    except Exception as exc:
        return f"ERR:{type(exc).__name__}"


async def main(a) -> None:
    if not re.fullmatch(r"relay_w6d3[a-z0-9_]*", a.db):
        raise SystemExit(f"refusing db={a.db!r}: this harness only runs on relay_w6d3* (never the evidence DB)")
    for t in a.table:
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", t):
            raise SystemExit(f"bad table name {t!r}")
    json.loads(a.payload)  # fail before starting anything if the payload is not JSON
    url = re.sub(r"/[^/]+$", f"/{a.db}", base_url())
    if not url.endswith(f"/{a.db}"):
        raise SystemExit("DATABASE_URL rewrite failed")
    logs = REPO / "logs"
    logs.mkdir(exist_ok=True)
    run = f"w6d3_{a.label}_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    o: list[str] = []
    o.append(f"run_id={run}")
    o.append(f"label={a.label} type={a.type} fake={a.fake} reaper={a.reaper} extra_env={','.join(a.env) or '-'}")
    o.append("src_diff_files_vs_HEAD=" + ",".join(git("diff", "--name-only", "HEAD", "--", "src/", "alembic/").split()))
    o.append("src_untracked=" + ",".join(git("ls-files", "--others", "--exclude-standard", "--", "src/", "alembic/").split()))

    eng = create_async_engine(url, echo=False)
    async with eng.connect() as c:
        o.append("current_database=" + (await c.execute(text("SELECT current_database()"))).scalar_one())
        try:
            o.append("db_revision=" + ",".join(r[0] for r in (await c.execute(text("SELECT version_num FROM alembic_version"))).all()))
        except Exception as exc:
            o.append(f"db_revision=ERR:{type(exc).__name__}")
            raise SystemExit("\n".join(o) + "\nDB not migrated -- run Step 2a first")
        o.append("jobs_before=" + str((await c.execute(text("SELECT count(*) FROM jobs"))).scalar_one()))

    env = dict(os.environ, DATABASE_URL=url, PYTHONUNBUFFERED="1")
    for pair in a.env:
        k, v = pair.split("=", 1)
        env[k] = v
    procs: list[subprocess.Popen] = []
    job_id, status, t_ins = None, "not_inserted", None
    async with httpx.AsyncClient() as hc:
        try:
            if a.fake:
                procs.append(start("provider", ["-m", "uvicorn", "src.fake_provider:app", "--host", "127.0.0.1",
                                                "--port", "8002"], env, run, logs))
                for _ in range(60):
                    if isinstance(await ledger(hc), int):
                        break
                    await asyncio.sleep(0.25)
            led0 = await ledger(hc) if a.fake else "-"
            if a.reaper:
                procs.append(start("reaper", ["-m", "src.reaper"], env, run, logs))
            procs.append(start("worker", ["-m", "src.worker"], env, run, logs))
            o.append("worker_ready=" + str(wait_for_line(logs / f"{run}_worker.log", "Starting worker process", 20)))
            async with eng.begin() as c:
                row = (await c.execute(text("INSERT INTO jobs (type, payload) VALUES (:t, CAST(:p AS jsonb)) "
                                            "RETURNING id, clock_timestamp()"), {"t": a.type, "p": a.payload})).one()
            job_id, t_ins = row[0], time.monotonic()
            o.append(f"job_id={job_id} inserted_at={row[1].isoformat()}")
            deadline = t_ins + a.deadline
            while time.monotonic() < deadline:
                async with eng.connect() as c:
                    status = (await c.execute(text("SELECT status FROM jobs WHERE id = :i"), {"i": job_id})).scalar_one()
                if status in TERMINAL:
                    break
                await asyncio.sleep(0.25)
            o.append(f"terminal={status if status in TERMINAL else 'deadline:' + status} "
                     f"wait_s={time.monotonic() - t_ins:.3f}")
            await asyncio.sleep(a.linger)
            led1 = await ledger(hc) if a.fake else "-"
            o.append(f"ledger_before={led0} ledger_after={led1} ledger_delta="
                     + (str(led1 - led0) if isinstance(led0, int) and isinstance(led1, int) else "-"))
        finally:
            o.append(f"swept_leftover_python={stop_all(procs)}")

    if job_id is not None:
        async with eng.connect() as c:
            j = (await c.execute(text("SELECT to_jsonb(j) - 'payload' - 'last_error', j.last_error FROM jobs j "
                                      "WHERE j.id = :i"), {"i": job_id})).one()
            o.append("job_row=" + json.dumps(j[0], sort_keys=True)[:2000])
            le = j[1] or ""
            tail = [ln.strip() for ln in le.strip().splitlines() if ln.strip()][-3:]
            o.append(f"last_error_len={len(le)} last_error_tail=" + " | ".join(tail)[:600])
            ex = (await c.execute(text("SELECT count(*), array_agg(claim_generation ORDER BY id), "
                                       "EXTRACT(EPOCH FROM (SELECT completed_at FROM jobs WHERE id = :i) - min(executed_at)), "
                                       "EXTRACT(EPOCH FROM (SELECT completed_at FROM jobs WHERE id = :i) - max(executed_at)) "
                                       "FROM job_executions WHERE job_id = :i"), {"i": job_id})).one()
            o.append(f"executions={ex[0]} execution_generations={ex[1]} completed_minus_first_executed_s="
                     f"{'-' if ex[2] is None else f'{float(ex[2]):.3f}'} completed_minus_last_executed_s="
                     f"{'-' if ex[3] is None else f'{float(ex[3]):.3f}'}")
            for t in a.table:
                rows = (await c.execute(text(f"SELECT to_jsonb(t) FROM {t} t WHERE t.job_id = :i ORDER BY 1"),
                                        {"i": job_id})).all()
                o.append(f"table={t} rows={len(rows)}")
                for r in rows:
                    o.append(f"  {t}: " + json.dumps(r[0], sort_keys=True)[:1000])
    await eng.dispose()

    w = (logs / f"{run}_worker.log").read_text(encoding="utf-8", errors="replace").splitlines()
    jid = str(job_id)
    o.append("worker_claim_lines=" + str(sum(f"[claim] Claimed job {jid} " in ln for ln in w)))
    o.append("worker_execute_lines=" + str(sum(f"[execute] Executing job {jid} " in ln for ln in w)))
    o.append("worker_failed_attempt_lines=" + str(sum(f"Job_id={jid} failed attempt" in ln for ln in w)))
    o.append("worker_mark_lines=" + str(sum(f"[mark] Marked job {jid} " in ln for ln in w)))
    o.append("worker_heartbeat_sent_lines=" + str(sum(f"Heartbeat sent for job_id={jid}" in ln for ln in w)))
    o.append("worker_error_tags=" + str(sum(any(t in ln for t in ("[poll_error]", "[heartbeat_error]", "[mark_error]",
                                                                       "[heartbeat_join_error]")) for ln in w)))
    hb = [m.group(1) for ln in w if (m := re.match(ECHO_TS + r"UPDATE jobs SET claimed_at=now\(\)", ln))]
    ex_at = [m.group(1) for ln in w if (m := re.match(ECHO_TS + r"INSERT INTO job_executions", ln))]
    o.append("echo_heartbeat_update_at=" + (",".join(x[11:] for x in hb) or "-"))
    o.append("echo_execution_insert_at=" + (",".join(x[11:] for x in ex_at) or "-"))
    if a.reaper:
        r = (logs / f"{run}_reaper.log").read_text(encoding="utf-8", errors="replace").splitlines()
        o.append("reaper_reclaim_lines=" + str(sum(f"[reclaim] job_id={jid} " in ln for ln in r)))
    if a.fake:
        p = (logs / f"{run}_provider.log").read_text(encoding="utf-8", errors="replace").splitlines()
        p += (logs / f"{run}_provider.err.log").read_text(encoding="utf-8", errors="replace").splitlines()
        o.append("provider_access_post_lines=" + str(sum('"POST /v1/complete HTTP/1.1"' in ln for ln in p)))
    o.append("logs=" + ",".join(sorted(x.name for x in logs.glob(f"{run}_*"))))
    out = logs / f"{run}_census.txt"
    out.write_text("\n".join(o) + "\n", encoding="utf-8")
    print("\n".join(o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, type=lambda s: s if re.fullmatch(r"[a-z0-9_]+", s) else ap.error("label: [a-z0-9_]+"))
    ap.add_argument("--payload", required=True)
    ap.add_argument("--type", default="llm_completion")
    ap.add_argument("--db", default="relay_w6d3")
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--reaper", action="store_true")
    ap.add_argument("--deadline", type=float, default=60.0)
    ap.add_argument("--linger", type=float, default=2.0)
    ap.add_argument("--table", action="append", default=[])
    ap.add_argument("--env", action="append", default=[])
    asyncio.run(main(ap.parse_args()))
```

**`labs/w6d3_key_scan.ps1`** — key kahin hai? Value kabhi print nahi hoti:

```powershell
# labs/w6d3_key_scan.ps1 -- Week 6 Din 3: is the provider API key anywhere it must not be?
# Reads the key's VALUE from .env by NAME, keeps it in memory, and counts where it appears. Never prints it.
# Every domain has a positive control that uses the SAME search code, so a domain the scan cannot actually see shows
# up as control_hits=0 instead of a quiet "0 leaks":
#   logs    : every logs\w6d3_* file                    control: "resolved_db=<Database>" (src/database.py prints it)
#   tracked : every git-tracked file + the staged diff  control: "DATABASE_URL=" (.env.example)
#   history : PSReadLine ConsoleHost_history.txt        control: "git "
#   db      : pg_dump --data-only of <Database>         control: "w6d3-canary" (put it in one job payload)
# Usage: pwsh -File labs\w6d3_key_scan.ps1 -KeyName <YOUR_KEY_VAR> -Out logs\w6d3_<step>_keyscan.txt [-Database relay_w6d3]
# Values and labels only; no conclusions (P-52).
param(
  [Parameter(Mandatory = $true)][ValidatePattern('^[A-Z][A-Z0-9_]*$')][string]$KeyName,
  [Parameter(Mandatory = $true)][string]$Out,
  [ValidatePattern('^relay_w6d3[a-z0-9_]*$')][string]$Database = 'relay_w6d3',
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
  [string]$EnvFile = ''
)
$ErrorActionPreference = 'Stop'
Set-Location $RepoRoot
if ($EnvFile -eq '') { $EnvFile = Join-Path $RepoRoot '.env' }
$line = @(Get-Content $EnvFile | Where-Object { $_ -match "^\s*$KeyName\s*=" }) | Select-Object -First 1
if (-not $line) { throw "$KeyName not found in $EnvFile" }
$key = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
if ($key.Length -lt 20) { throw "$KeyName value is shorter than 20 chars -- refusing (a short needle matches by accident)" }

function Count-In([string[]]$paths, [string]$needle) {
  $n = 0
  foreach ($p in $paths) {
    if (Test-Path -LiteralPath $p -PathType Leaf) {
      if ([IO.File]::ReadAllText((Resolve-Path -LiteralPath $p).Path).Contains($needle)) { $n++ }
    }
  }
  return $n
}

$o = [System.Collections.Generic.List[string]]::new()
$o.Add("key_name=$KeyName key_len_ge_20=True database=$Database at=" + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'))

$logFiles = @(Get-ChildItem (Join-Path $RepoRoot 'logs') -Filter 'w6d3_*' -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
$o.Add("logs_files=$($logFiles.Count) logs_hits=" + (Count-In $logFiles $key) + " logs_control_hits=" + (Count-In $logFiles "resolved_db=$Database"))

$tracked = @(git ls-files | ForEach-Object { Join-Path $RepoRoot $_ })
$staged = (git diff --cached) -join "`n"
$o.Add("tracked_files=$($tracked.Count) tracked_hits=" + (Count-In $tracked $key) + " tracked_control_hits=" + (Count-In $tracked 'DATABASE_URL=') +
       " staged_diff_hits=" + [int]$staged.Contains($key))

$hist = Join-Path $env:APPDATA 'Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt'
$o.Add("history_file_exists=" + (Test-Path -LiteralPath $hist) + " history_hits=" + (Count-In @($hist) $key) + " history_control_hits=" + (Count-In @($hist) 'git '))

$dump = (docker exec relay-db-1 pg_dump -U postgres --data-only --no-owner $Database) -join "`n"
$o.Add("db_dump_bytes=$($dump.Length) db_hits=" + [int]$dump.Contains($key) + " db_control_hits=" + [int]$dump.Contains('w6d3-canary'))
$key = $null
$o | Out-File -Encoding utf8 $Out
Get-Content $Out
```

---

## PART B — Prediction questions

> **Gemini ko NAHI. Step 0c pe, kisi experiment se pehle, apne head se.** `[padh ke]` = pehle file kholo, jawab ke
> saath **file:line + us line ka ek copy kiya quote**. Uske bina `idk` reading gap gina jaata hai. `[chala ke]` ka `idk`
> bilkul theek. `idk` sub-part level pe. **Gyarah sub-parts, chhe `[padh ke]`.**

```text
Q1 (Step 2 se pehle — fake 500)
(a) [padh ke: src/fake_provider.py:40–45 · src/worker.py:262–297] Ek client
    jo status dekhe bina seedha r.json()["text"] padhta hai. Fake 500 ka ek
    job, aaj ka worker (MAX_ATTEMPTS=3): final status, attempts, last_error ki
    aakhri line, aur provider ledger_delta.
(b) [chala ke] Tera client (Step 1 ka failure shape), wahi 500 job:
    jobs.attempts, job_executions rows, ledger_delta — teeno barabar? Aur
    last_error ki aakhri line kya kahegi?

Q2 (Step 3 se pehle — record)
(a) [padh ke: src/worker.py:262–270 · :312–324 · src/models.py] Step 2 ka ok
    job succeed hua, migration abhi nahi. Is job ke tokens_in / tokens_out
    Relay me kahan-kahan hain (DB column? log?), aur provider ki taraf kahan?

Q3 (Step 3 — migration)
(a) [padh ke: alembic/env.py:29–53 · alembic.ini:89 · src/database.py:2–4]
    Naya PowerShell window, $env:DATABASE_URL set nahi,
    `alembic upgrade head`. Kaunsa database migrate hoga, env.py ki line
    `source=` kya kahegi, aur .env ka isme koi role hai?
(b) [chala ke] s3_ok ka result store hone ke baad `downgrade -1` phir
    `upgrade head`: us job ke tokens kya dikhenge? Ek line: "additive
    migration reversible hai" — kis cheez ke liye sach, kis ke liye nahi.

Q4 (Step 4 — real provider)
(a) [chala ke] Prompt "the quick brown fox": real tokens_in fake ke 4 se
    zyada, barabar, ya kam? Kyun?
(b) [chala ke] Call ke 5 min ke andar provider ka dashboard is call ko
    dikhata hai? Kis granularity pe?
(c) [padh ke: src/database.py:41 · src/worker.py:271–272 · :312–324] Maan
    lo key URL ke query string me hai aur call 401 pe raise_for_status() se
    raise hoti hai. Relay me key kahan-kahan pahunchegi (har jagah file:line),
    aur echo=True ki log line me poori dikhegi ya kati hui?

Q5 (Step 5 — slow)
(a) [padh ke: src/worker.py:36–47 · :258–260] 3 s delay wala job:
    "Heartbeat sent" lines kitni?
(b) [padh ke: src/worker.py:36–58 · src/reaper.py:12, :29–32 · tera client
    timeout] 25 s delay, reaper chalu: heartbeat lines kitni, [reclaim]
    lines kitni? Tera client timeout 25 s se kam ho to kya badlega?
(c) [chala ke] 25 s job: completed_at − executed_at 25 s se kitna upar
    (±0.1 s)? Aur job khatam hone pe claimed_at kis moment ka hai?
```

---

## PART C — Verification

Har check ki ek file. Jahan value Part B hai, wahan sirf ye ki instrument use pakadta hai. Aakhri column: **kaunsa galat
implementation is check ko pass nahi karega.**

### C0 — Step 0 / 0.5

| Subject | Check | Broken reading |
|---|---|---|
| `w6d3_step0_staged.txt` | exactly `1` line, BRIEF | `-A` ne kuch aur utha liya |
| `w6d3_step0_bench.txt` | Step 0b ke expected values | `relay_revision ≠ w4d4_sink_unique` = evidence DB migrate ho chuka; `dotenv_has_keyvar=0` = Step 4 nahi chalega |
| `w6d3_step0_frozen_hash.txt` | exactly `2` lines, koi line `=` pe khatam nahi | |
| `w6d3_step0_seal_commit.txt` | `head_blob = git_blob` · `hash_file_before_commit=True` | kal wala order: hash file commit ke baad bani |
| `w6d3_step05_rewrite.txt` | `own=1 gaps=1 rev=1 order_own_gaps_rev=True` | |

### C1 — interface (Step 1)

| Check | Kaunsa galat implementation pass nahi karega |
|---|---|
| `src_database_imported=False` | provider module ne `src.database` import kiya → har import pe evidence-DB engine |
| `import_without_<KEY>=ok` | key module/class level pe `os.environ[...]` se padhi — fake-only run bhi key maangega (reviewer ne aisa ek throwaway module pe chala ke `fail:KeyError` dekha) |
| do `provider_class=`, dono `complete_is_coroutine=True` | sync `def complete` → event loop block (Din 5 ka Arm B) |
| `env_example_keyvar=1` | naam bhoola, ya **value** likh di (pattern khaali value maangta hai) |

### C2 — Step 2

| Subject | Check | Kaunsa galat pass nahi karega |
|---|---|---|
| `w6d3_step2a_db.txt` | `CREATE DATABASE` · `alembic resolved_db=relay_w6d3 source=env` | env set nahi → `relay source=alembic.ini` |
| `s2_ok` census | `current_database=relay_w6d3` · `terminal=succeeded` · `ledger_delta=1` · `executions=1` · `provider_access_post_lines=1` · `worker_error_tags=0` · `swept_leftover_python=0` | handler provider ko call hi nahi karta → `ledger_delta=0` |
| `s2_500` census | **`terminal ≠ succeeded`** · baaki values Part B `Q1(b)` | client jo `500` ko success banata hai (body bina parse kiye lauta diya) → `succeeded` |
| ok vs 500 | `ok` succeeded **aur** `500` nahi | sirf ek arm dono galtiyon (kabhi call nahi / hamesha success) ko alag nahi karta |

### C3 — Step 3

| Subject | Check | Kaunsa galat pass nahi karega |
|---|---|---|
| `w6d3_step3_migrate.txt` | har `resolved_db=` = `relay_w6d3 source=env` · ek head `w6d3_…` · `No new upgrade operations detected` | `models.py` aur migration alag columns kehte hain → `check` ops dikhata hai |
| `w6d3_step3_downup.txt` | `--- up` me naye columns/table · `--- down` me **nahi** · `--- up_again` me phir | `downgrade()` khaali/adhoora → `--- down` me bache |
| `s3_ok` census | `job_row` (ya `table=` rows) me tokens **int, null nahi** | write wire hi nahi hua |
| Step 6 bench | `relay_revision=w4d4_sink_unique` | kisi alembic command ne `relay` migrate kar diya |

### C4 — Step 4

| Subject | Check | Kaunsa galat pass nahi karega |
|---|---|---|
| `w6d3_step4_interface.txt` | C1 ki saari rows, real provider ke saath | key import pe padhi |
| `s4_real` census | `terminal=succeeded` · tokens int · `ledger_delta=-` (fake nahi chala) | fake pe chala → `ledger_delta` number |
| `w6d3_step4_keyscan.txt` | har `*_hits=0` **aur** har `*_control_hits ≥ 1` | jo domain scan dekh hi nahi pa raha, wo control `0` se dikhta hai |
| `w6d3_step4_dashboard.txt` | do `checked_at=` lines | |

### C5 — Step 5

| Subject | Check | Kaunsa galat pass nahi karega |
|---|---|---|
| `s5_d3` · `s5_d25` | `terminal=succeeded` · `completed_minus_first_executed_s ≥ 3.0` / `≥ 25.0` · `ledger_delta=1` | delay param ignore → `~0.0` · client timeout delay se chhota → `ledger_delta ≥ 2` |
| heartbeat / reclaim / `claimed_at` | **Part B `Q5`** | |

### C6 — close

| Subject | Check |
|---|---|
| `w6d3_step6_keyscan_predrop.txt` | C4 jaisa |
| `w6d3_step6_drop.txt` | `DROP DATABASE` |
| `w6d3_step6_bench.txt` | `dbs=postgres,relay` · `relay_revision=w4d4_sink_unique` · `heads=w6d3_… (head)` · counters/protected Step 0 jaise · `relay_python=0` · `listen_8000_8002=0` · `key_index=0` · `seal_before_first_experiment=True` · `trail_distinct_sha = trail_lines` · `hash_file_before_commit=True` |
| `w6d3_step6_staged.txt` | `0` KEY · `0` ANSWERS · `0` FROZEN · `0` `.env` |
| `w6d3_step6_keyscan_staged.txt` | `staged_diff_hits=0` · `tracked_hits=0` |
| seals | `seals=19 … blocked=0` |

### C7 — Aaj ye quote nahi honge

| Kya | Kyun |
|---|---|
| *"provider ka bill = Relay ka record"* | `n = 1`; response ka usage provider ka bayan hai, dashboard alag record hai, aur dono ka match aaj sirf ek call pe |
| *"key safe hai"* | chaar domain, controls ke saath, `0` — par Gemini chat, screenshots, doosri machines scan nahi hui → `narrowed` |
| *"migration reversible hai"* | schema ke liye; data ke liye `Q3(b)` |
| *"`D-11` ho gaya"* | aaj har failure purane retry path pe — classification Din 4 |
| *"heartbeat lease bachaata hai"* | ek async handler pe, lease se chhoti call pe. Blocking client aur lease se lambi call Din 5 |

---

## PART D — Scope guard

| Kya | Owner | Kyun aaj nahi |
|---|---|---|
| Retryable vs non-retryable (`D-11`), `P-51` | **Din 4** | aaj ka shape us ki zameen hai; aaj sab purane path se retry |
| Max-cost-per-job cap | **Din 4 Step 6** | aaj sirf output tokens ka ek param |
| `job_costs`, budget | **Week 8** | aaj us number ka pehla source |
| `Retry-After` honour, rate limiter | **Week 7** | |
| Provider hang vs lease, blocking client | **Din 5** | aaj sirf lease se chhoti slow call |
| Handler deadline (`D-22`) | **Month 3** | aaj sirf timeout ka number |
| Fallback chain, circuit breaker, streaming | **Month 3 / Month 2 me nahi** | |
| Evidence DB `relay` pe migration | **user ka faisla, Din 6 se pehle nahi** | is hafte ke experiments disposable DBs pe; `relay` ka schema Week 5 ke records ka hai |
| `P-58`, `P-59` fixes | user ka faisla (Month 4 / Week 7) | |
| README provider rows | **Din 6 Step 3** | |
| Naye tests (`P-37`) | **Month 3** | |
| `git push` | **user** | push se pehle `git log --stat origin/main..HEAD` |

**Cut order** (`0 min` slack): pehle Step 5 ka `s5_d3` arm (`Q5(a)` reading se derivable) → phir Step 2 ka `s2_500` arm
(Din 4 Step 4 me jaata hai) → phir Step 4c ki doosri dashboard line. Har cut DoD me `slipped`. **Kabhi cut nahi:** Step 0
(seal commit samet), 0.5, Step 3 ka disposable migration + `resolved_db` check, Step 4 ka real call (key ho to), dono
key scans, Step 6.

---

*Plan:* [`../../planning/WEEK_06.md`](../../planning/WEEK_06.md) · *Pichhla din:* [`DIN_02_BRIEF.md`](DIN_02_BRIEF.md) ·
*Seal:* `DIN_03_PREDICTIONS_FROZEN.md` (Step 0c) · *Log:* [`../../logs/WEEK_06.md`](../../logs/WEEK_06.md)
