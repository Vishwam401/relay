# WEEK 5 · DIN 6 — `2026-09-29` — Week close: har verdict ek record pe khada hai, aur record kis moment ka hai ye pehle check hoga

**Budget `155 min` (plan ka `150` + `5`, cut order Part D me) · Layer L2 · `src/` me aaj bhi ek line nahi — lagatar
chautha din.** Aaj ka kaam faisle likhna hai: `D-30` close, `D-32` final, `D-28` amendment, README ka promise #4, chaar
`💡` rewrites, handoff. Teen measurements bhi hain — `.gitignore` ka differential, `.pyc` removal, aur ek fresh clone.

> **Din 5 ne din ka sawaal saaf compose kiya.** Ek sequential dispatcher ne receiver ka `2+0` pool orphaned handlers se
> bhar diya, `QueuePool limit` sink ke log me aaya, Relay ne sirf `500` dekha. `35.006 s` outage pe teeno process
> zinda rahe, `30/30 succeeded`.
>
> **Par Din 5 ke teen sabse zaroori findings teen records ke baare me the jo kisi pichhle moment ke hain:**
> `received_at` aur `dispatched_at` transaction ke start hain (`now()`), aur worker ne `Marked job 8 as 'succeeded'`
> apne `COMMIT` se **pehle** print kiya — jo `COMMIT` mara (`P-56`). Review me ek chautha mila: seal ka SHA-256
> working-copy bytes pe hai, aur is machine pe fresh clone un bytes ko badal deta hai (`P-57`).
>
> **Aaj jo bhi verdict likha jaayega — `D-30` ka *"bounded"*, README ka *"recoverable"*, seal ka *"auditable"* — wo
> kisi record pe khada hoga.** Har step me ek sawaal: ye record us cheez ka hai jiska naam le raha hai, ya kisi pehle
> moment ka?

---

## PART A — Steps

### Step 0 — 10 min: Din 5 ka commit, bench, seal — is baar do hash

**Din 5 commit — named files, `-A` kabhi nahi.** `P-54` ki bees files aaj bhi gate hain.

```powershell
cd d:\PROJECTS\relay
git add docs/daily/week_05/DIN_05_PREDICTIONS_FROZEN.md labs/w5d5_chain_probe.py labs/w5d4_pool_probe.py labs/w5d4_composed_failure.py scripts/supervisor.py docs/logs/WEEK_05.md docs/LEARNING_LOG.md docs/PROBLEMS.md docs/daily/week_05/DIN_06_BRIEF.md
git diff --cached --name-only | Out-File -Encoding utf8 logs\w5d6_step0_staged.txt
Get-Content logs\w5d6_step0_staged.txt            # exactly ye 9. Koi *_KEY.md nahi, koi _ANSWERS/_DESIGN/_PROBLEM/_PROPERTY nahi
git commit -m "docs(w5d5): chain probe, supervisor prefix + dispatcher, Din 5 review, frozen seal"
```

`docs/roadmap/CURRENT_WEEK.md` aur `docs/planning/WEEK_05.md` ignored hain — list me mat daalo.

**Bench — har line file me:**

```powershell
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("head=" + (git rev-parse --short HEAD))
$o.Add("src_diff=" + (git diff --name-only HEAD -- src/ | Measure-Object).Count)
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py src/sink.py | ForEach-Object { $o.Add("hash $_") }
$o.Add("heads=" + ((.\.venv\Scripts\python.exe -m alembic heads 2>&1) -join ' | '))
$o.Add("relay_python=" + (Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count)
$o.Add("p54=" + (git status --porcelain | Select-String -CaseSensitive "_ANSWERS\.md|_DESIGN\.md|_PROBLEM\.md|_PROPERTY\.md" | Measure-Object).Count)
$o.Add("tracked_ignored=" + (git ls-files -ci --exclude-standard | Measure-Object).Count)
$o.Add("frozen_tracked=" + (git ls-files -- "*PREDICTIONS_FROZEN*" | Measure-Object).Count)
$o.Add("logs_in_head=" + (git ls-files logs | Measure-Object).Count)
$o.Add("pyc_control=" + (git ls-files -- "*.pyc" | Measure-Object).Count)
$o | Out-File -Encoding utf8 logs\w5d6_step0_bench.txt
docker exec relay-db-1 psql -U postgres -d relay -t -A -F "|" -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');" | Out-File -Encoding utf8 logs\w5d6_step0_counters.txt
Get-Content logs\w5d6_step0_bench.txt, logs\w5d6_step0_counters.txt
```

Expected (instrument, outcome nahi): `src_diff=0` · chhe hashes `a2ec8e9f…` `edcde815…` `dcdb6343…` `d55e3b8a…`
`fc5bde22…` `fcfc9059…` · `heads=w4d4_sink_unique (head)` **string pe assert** · `relay_python=0` · `p54=20` · counters
`133|145|19|4|7|39|5|0|1`. `frozen_tracked`, `logs_in_head`, `tracked_ignored` ki values Part B me hain — file me honi
chahiye, bas.

**Seal:** `DIN_06_PREDICTIONS_FROZEN.md` likho — Part B ke jawab **har sub-part ka alag**, `idk` bhi sub-part level pe.
Jis sub-part me file ya command ka naam hai, uske jawab ke saath **wo line number ya command likho jo tune padha/chalaya**.
Phir **do** hash, ek file me:

```powershell
$f = "docs\daily\week_05\DIN_06_PREDICTIONS_FROZEN.md"
"sha256=" + (Get-FileHash -Algorithm SHA256 $f).Hash | Out-File -Encoding utf8 logs\w5d6_step0_frozen_hash.txt
"git_blob=" + (git hash-object $f) | Out-File -Append -Encoding utf8 logs\w5d6_step0_frozen_hash.txt
Get-Content logs\w5d6_step0_frozen_hash.txt
```

**Executable end:** staged file me `9` lines, commit, bench + counters files, do-line hash file.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `git hash-object <file>` | git ka blob id (SHA-1) jo is file ko add karne pe banega. Git pehle apne "clean" filters (jaise line-ending conversion) lagata hai, phir hash karta hai |
| `git rev-parse HEAD:<path>` | commit me jo blob hai, uska id. Working copy ko nahi dekhta |
| `git ls-files -ci --exclude-standard` | wo files jo **tracked** hain *aur* kisi ignore rule se match karti hain |
| blob | git ke andar stored file content. Commit ke baad badalta nahi |

---

### Step 1 — 15 min: `D-32` final — `P-54` ke teen faisle aur `P-57` ka ek

`D-32` `DRAFT` hai kyunki uski policy table me do rows `—` hain aur rule ka default *publish* hai. Aaj chaar faisle,
**tere**, har ek ka cost ek line me. Gemini se options aur costs le sakta hai, pick nahi (Situation 3).

| # | Faisla | Options |
|---|---|---|
| 1 | `*_ANSWERS.md` (`13` files) | `Local` / `Public` — inme `### After KEY` blocks hain, yaani sealed outcomes ka paraphrase |
| 2 | `*_DESIGN.md` / `*_PROBLEM.md` / `*_PROPERTY.md` (`7`) | `Local` / `Public` / class-wise alag |
| 3 | Rule ka shape | (a) aaj jaisa: ignores ki list, default publish · (b) **flip:** `daily/` ke andar sab ignore, publish hone wali classes naam se re-include — default ignore |
| 4 | Seal ka hash (`P-57`) | (a) `.gitattributes` me frozen files `-text` · (b) har seal pe `git hash-object` bhi record (Step 0 aaj se karta hai) · (c) dono |

**Kahan likhna hai:** `docs/DECISIONS.md` me `D-32` ke header se `DRAFT` hatao, policy table ki `—` rows bharo, `Cost` me
teen naye faislon ka cost jodo, aur ek naya subsection `### Week 5 Din 6 — final` jisme chaaron picks aur har ek ka
`Rejected` **naam se**. **Existing text edit mat karo** — amendment ke roop me jodo, jaise baaki entries me hai.

**Executable end:**

```powershell
$d = Get-Content docs\DECISIONS.md -Raw
$s = $d.Substring($d.IndexOf("## D-32"), $d.IndexOf("## D-33") - $d.IndexOf("## D-32"))
"d32_header_draft=" + ([regex]::Matches(($s -split "`n")[0], 'DRAFT')).Count | Out-File -Encoding utf8 logs\w5d6_step1_d32.txt
"d32_undecided_rows=" + ([regex]::Matches($s, '\*\*`—` undecided\*\*')).Count | Out-File -Append -Encoding utf8 logs\w5d6_step1_d32.txt
"d32_final_section=" + ([regex]::Matches($s, '### Week 5 Din 6 — final')).Count | Out-File -Append -Encoding utf8 logs\w5d6_step1_d32.txt
"d32_rejected_lines=" + ([regex]::Matches($s, '(?m)^\*\*Rejected')).Count | Out-File -Append -Encoding utf8 logs\w5d6_step1_d32.txt
Get-Content logs\w5d6_step1_d32.txt           # 0 · 0 · 1 · >= 1
```

**Terms used in this step**

| Term | Kya hai |
|---|---|
| allow-list of ignores vs allow-list of publishes | pehle me jo naam liya wo chhupta hai aur baaki sab dikhta hai; doosre me jo naam liya wo dikhta hai aur baaki sab chhupta hai. Nayi, bina naam ki class ka kya hota hai — wahi farak hai |
| re-include (`!pattern`) | gitignore me negation: pehle ignore hui cheez ko wapas include karna |
| `.gitattributes` `-text` | git ko batana ki is path pe line-ending conversion mat karo |
| one-way door | `Public` kiya aur push hua to history me hamesha ke liye. `Local` → `Public` reversible hai, ulta nahi |

---

### Step 2 — 15 min: rule lagao aur differential chalao — ek check jo galat rule pe fail ho

Step 1 ka faisla `.gitignore` (aur agar chuna to `.gitattributes`) me likho. **Phir chaar probe files, jo aaj ke
kisi rule me naam se nahi hain** — inka kaam ye dikhana hai ki rule *bina naam ki* cheez ke saath kya karta hai.

```powershell
$probes = 'docs/daily/week_05/DIN_99_BRIEF.md','docs/daily/week_05/DIN_99_KEY.txt','docs/daily/week_05/DIN_99_SEALED.md','docs/daily/week_05/DIN_99_NEWCLASS.md'
$probes | ForEach-Object { Set-Content -Path $_ -Value 'probe' }
$pub = @(git add -A --dry-run 2>&1 | ForEach-Object { ($_ -replace "^add '", "") -replace "'$", "" })
$r = [System.Collections.Generic.List[string]]::new()
foreach ($p in $probes) { $r.Add($(if ($pub -contains $p) { "PUBLISH $p" } else { "ignored $p" })) }
$r.Add("p54=" + (git status --porcelain | Select-String -CaseSensitive "_ANSWERS\.md|_DESIGN\.md|_PROBLEM\.md|_PROPERTY\.md" | Measure-Object).Count)
$r.Add("tracked_ignored=" + (git ls-files -ci --exclude-standard | Measure-Object).Count)
git ls-files -ci --exclude-standard | ForEach-Object { $r.Add("  ti: $_") }
$r.Add("dryrun_total=" + $pub.Count)
$r.Add("dryrun_key_md=" + ($pub | Where-Object { $_ -cmatch '_KEY\.md$' } | Measure-Object).Count)
$r.Add("frozen_05_publishable=" + ($(git check-ignore -q docs/daily/week_05/DIN_05_PREDICTIONS_FROZEN.md; $LASTEXITCODE) -ne 0))
$r | Out-File -Encoding utf8 logs\w5d6_step2_rule.txt
$probes | ForEach-Object { Remove-Item $_ }
"probes_left=" + ($probes | Where-Object { Test-Path $_ } | Measure-Object).Count | Out-File -Append -Encoding utf8 logs\w5d6_step2_rule.txt
Get-Content logs\w5d6_step2_rule.txt
```

**Is check ko kaunsa galat rule pass kar dega?** Ek rule jo `daily/` ke andar **sab kuch** ignore kar de — wo KEY, SEALED,
NEWCLASS teeno chhupa dega aur *"seal safe hai"* padhega. Isliye `DIN_99_BRIEF.md` probe hai: wo positive control hai,
aur `frozen_05_publishable` doosra. Dono mein se ek bhi galat aaya to rule toota hai, chahe baaki teen sahi hon.

`dryrun_key_md` **`0`** hi hona chahiye, har rule ke neeche.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| probe file | ek jaan-boojh ke banayi file jo sirf ye dekhne ke liye hai ki rule uske saath kya karta hai. Check ke baad delete |
| positive control | ek case jiska result **publish** hona chahiye. Uske bina *"sab ignored"* ek toota rule bhi ho sakta hai |
| `git check-ignore -q` | exit `0` = ignored, exit `1` = ignored nahi |
| traversal | git ignored directory ke andar jaata hi nahi — uske andar ka koi negation kabhi evaluate nahi hota (`D-32`, Din 3) |

---

### Step 3 — 10 min: `.pyc` ka faisla, aur uska positive control

`labs/__pycache__/day1_async.cpython-313.pyc` Week 1 Din 1 se tracked hai (`01f42c6`, `868` bytes), aur is hafte ke
**har** Part C ne `pyc_control=1` ko positive control ki tarah use kiya. Do options: (a) `git rm --cached` + commit, (b)
chhod do. **Tera faisla, ek line cost ke saath, `D-32` ke Din 6 section me.**

Agar (a):

```powershell
git rm --cached labs/__pycache__/day1_async.cpython-313.pyc
git commit -m "chore: untrack day1 pyc (D-32)"
```

Dono case me, file me:

```powershell
$q = [System.Collections.Generic.List[string]]::new()
$q.Add("pyc_tracked=" + (git ls-files -- "*.pyc" | Measure-Object).Count)
$q.Add("pyc_in_01f42c6_bytes=" + (git cat-file -s "01f42c6:labs/__pycache__/day1_async.cpython-313.pyc" 2>&1))
$q.Add("pyc_on_disk=" + (Test-Path labs\__pycache__\day1_async.cpython-313.pyc))
$q.Add("new_control_brief=" + (git ls-files -- "*_BRIEF.md" | Measure-Object).Count)
$q | Out-File -Encoding utf8 logs\w5d6_step3_pyc.txt
Get-Content logs\w5d6_step3_pyc.txt
```

**Executable end:** chaar lines. **Aaj ke Part C ka har `0`-expecting `ls-files` check `new_control_brief` ko control ki
tarah use karega** — kyun, wo Part B me hai.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `git rm --cached` | file ko index se hatana, disk se nahi. Agle commit se `HEAD` me nahi rehti |
| `git cat-file -s <commit>:<path>` | us commit me us path ke blob ka size. Blob na ho to error |

---

### Step 4 — 15 min: `D-30` close

`D-30` `OPEN` hai, `Supervisor` section me Din 2 ke notes hain aur do gate `[NOT SATISFIED BY EVIDENCE]`. Din 5 ne dono
chalaye. **Aaj ye entry band hoti hai — decision ki shape me, notes ki nahi.**

**Kya likhna hai** (`### Supervisor — Week 5 Din 6, decided` naam ka naya subsection, purana text edit nahi):

- **Chose:** kaunsa option, aur Din 5 pe instrument me kya badla (prefix, dispatcher).
- **Evidence:** Din 2 ke numbers + Din 5 ke do gates, **har number ke saath file ka naam**. Gate 1 aur gate 2 ke liye
  wahi do lines jo `WEEK_05.md` Din 5 section 7 me hain — **apne shabdon me.**
- **Cost:** kam se kam ye teen — (i) bound kis cheez se aaya aur supervisor ka backoff kitni baar chala; (ii) gate 2 me
  kaunsa process load ke neeche nahi tha; (iii) Windows-only aur not deployable.
- **Rejected:** Din 2 ke (a) aur (c), naam se, reason ke saath.
- **Owner / Revisit:** `os._exit` crash-loop pe backoff ka pricing — **Week 6, aaj run nahi.**
- Header se `OPEN` hatao.

**Executable end:**

```powershell
$d = Get-Content docs\DECISIONS.md -Raw
$s = $d.Substring($d.IndexOf("## D-30"), $d.IndexOf("## D-31") - $d.IndexOf("## D-30"))
$c = [System.Collections.Generic.List[string]]::new()
$c.Add("d30_header_open=" + ([regex]::Matches(($s -split "`n")[0], 'OPEN')).Count)
$c.Add("d30_decided_section=" + ([regex]::Matches($s, '### Supervisor — Week 5 Din 6, decided')).Count)
$c.Add("d30_cites_w5d5_step6=" + ([regex]::Matches($s, 'w5d5_step6')).Count)
$c.Add("d30_rejected=" + ([regex]::Matches($s, '(?m)^\*\*Rejected')).Count)
$c.Add("d30_week6_owner=" + ([regex]::Matches($s, 'Week 6')).Count)
$c | Out-File -Encoding utf8 logs\w5d6_step4_d30.txt
Get-Content logs\w5d6_step4_d30.txt           # 0 · 1 · >= 1 · >= 2 · >= 1
```

**Terms used in this step**

| Term | Kya hai |
|---|---|
| gate satisfied *as written* | jo shabd gate me likhe the wo sach hue. Iska matlab ye nahi ki gate ne wo cheez test ki jo uska irada tha |
| backoff exercised | supervisor ka backoff code sirf child ke exit pe chalta hai. Exit nahi → code nahi chala |

---

### Step 5 — 10 min: `D-28` amendment — discriminator ka teesra column

Din 4 pe *starvation* column bhara, Din 5 pe *DB down*. **Ek amendment block `D-28` me:** teen causes (process dead ·
pool starved · DB down) × chaar observations (`/health` · `/healthz` status + latency · process log ki exception class ·
`pg_stat_activity`). Har cell me value **aur** file. Aur do lines: (1) latency ne aaj kyun alag kiya, aur kaunsa ek config
change dono ko mila deta — dono latencies ke mechanism ke saath; (2) HTTP prober in teen me se kitne alag kar sakta hai.

**Executable end:**

```powershell
$d = Get-Content docs\DECISIONS.md -Raw
$s = $d.Substring($d.IndexOf("## D-28"), $d.IndexOf("## D-29") - $d.IndexOf("## D-28"))
@("d28_din6_block=" + ([regex]::Matches($s, 'Week 5 Din 6')).Count,
  "d28_interfaceerror=" + ([regex]::Matches($s, 'InterfaceError')).Count,
  "d28_refused=" + ([regex]::Matches($s, 'ConnectionRefusedError')).Count,
  "d28_queuepool=" + ([regex]::Matches($s, 'QueuePool')).Count) | Out-File -Encoding utf8 logs\w5d6_step5_d28.txt
Get-Content logs\w5d6_step5_d28.txt           # har ek >= 1
```

**Terms used in this step**

| Term | Kya hai |
|---|---|
| discriminator | ek observation jo do causes ke liye alag value deti hai |
| structural vs coincidental discriminator | pehla mechanism ki wajah se alag hai; doosra do unrelated config values ke sanyog se |

---

### Step 6 — 15 min: README rows 7, 8, 9 aur promise #4

README ki crash table ki teen rows Month 1 ke evidence pe likhi hain: row 7 (*idle-polling pe DB down — process exited*),
row 8 (*mid-handler pe DB down — `[NO EVIDENCE]`*), row 9 (*worker aur reaper dono marte hain — `[NO EVIDENCE]`*). Week 5
ne teeno ka evidence badla. **Aur promise #4 ki row** (`narrowed` row level · `[NO EVIDENCE]` process level).

**Rules:**
- Teen shabd hi allowed hain: `protected` · `narrowed` · `[NO EVIDENCE]`. **Kisi row me `protected` bina scope ke nahi.**
- *Recovery mechanism* claim hai, *Evidence* observation. Dono column alag rakho.
- Purana evidence mitao mat — agar ek row ka crash point khud ab nahi hota, wo bhi likho.
- **Har evidence cell ek aisi jagah point kare jo repo clone karne wala khol sake.**

**Executable end:**

```powershell
$rm = Get-Content README.md
$rows = $rm | Where-Object { $_ -match '^\| (4|7|8|9) \|' }
$e = [System.Collections.Generic.List[string]]::new()
foreach ($row in $rows) { $n = ($row -split '\|')[1].Trim(); $e.Add("row$n no_evidence=" + ([regex]::Matches($row, 'NO EVIDENCE')).Count + " week5=" + ([regex]::Matches($row, 'Week 5')).Count + " cites_logs_dir=" + ([regex]::Matches($row, 'logs/w5d')).Count) }
$e | Out-File -Encoding utf8 logs\w5d6_step6_readme.txt
Get-Content logs\w5d6_step6_readme.txt
```

Paanch lines aani chahiye (promise table ki row `4` aur crash table ki `7`, `8`, `9` — row `4` do baar match ho sakti hai
kyunki crash table me bhi row `4` hai; dono likhe jaayenge). `week5 >= 1` har badli row me. `cites_logs_dir` ki value
Part B me hai.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| verdict vocabulary | README ke teen allowed shabd (line `31`). Chauthe shabd ka matlab hai reader ko khud decide karna pade |
| crash point | table ka column 2 — failure ka exact moment. Agar code badal gaya to moment khud badal sakta hai |

---

### Step 7 — 30 min (do half, `15` + `15`): Week 4 ke chaar `💡`, apne shabdon me

`docs/month_01/logs/WEEK_04.md` me chaar `💡` sections reviewer-written hain — Din 1 (line `~190`), Din 2 (`~596`), Din 4
(`~1076`), Din 6 (`~1979`). **Ye teesra hafta carry ho raha hai.** Din 3 aur Din 5 ke sections tune pehle hi likhe the.

**Procedure, har section ke liye — aur yahi is step ki value hai:**
1. Us din ka `📊 Measured` padho. **`💡` section mat padho.**
2. Us din ne kya establish kiya, **apne shabdon me** likho, `### 💡 What I understood — own words, 2026-09-29` ke neeche,
   reviewer wale section ke **upar**. Teen se paanch points. Har point me ek number ya ek file.
3. **Ab** reviewer ka section padho. Uske neeche ek line: `Gaps vs reviewer: …` — jo tune miss kiya, ya jahan tu uske
   khilaaf hai aur kyun.
4. Reviewer section ko mitao mat.

**7a:** Din 1, Din 2. **7b:** Din 4, Din 6.

**Executable end:**

```powershell
@("own_words_blocks=" + (Select-String -Path docs\month_01\logs\WEEK_04.md -SimpleMatch "What I understood — own words, 2026-09-29" | Measure-Object).Count,
  "gaps_lines=" + (Select-String -Path docs\month_01\logs\WEEK_04.md -SimpleMatch "Gaps vs reviewer:" | Measure-Object).Count,
  "reviewer_blocks_kept=" + (Select-String -Path docs\month_01\logs\WEEK_04.md -Pattern "^### 💡 What the session established" | Measure-Object).Count) | Out-File -Encoding utf8 logs\w5d6_step7_rewrites.txt
Get-Content logs\w5d6_step7_rewrites.txt      # 4 · 4 · 6
```

Teesri value `6` isliye: `Select-String` case-insensitive hai, to Din 3 aur Din 5 ke *"What the Session Established"*
headings bhi match karte hain. Aaj se pehle ye `0 · 0 · 6` padhta hai `[MEASURED-R 2026-09-28]` — to check fail ho sakta hai.

Week 5 ke paanch `💡` (Din 1–5) **Week 6 Din 1** ko carry — DoD me ek line.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| recall vs recognition | padh ke *"haan yahi"* kehna recognition hai; bina dekhe likh paana recall. Step ka order isi liye hai |

---

### Step 8 — 15 min: `WEEK_05_HANDOFF.md` aur DoD audit

**Handoff:** `docs/daily/WEEK_05_HANDOFF.md`. Shape Week 4 ke handoff jaisa
(`docs/month_01/daily/WEEK_04_HANDOFF.md`): kya bana, kya naapa, kya khula hai **owner ke saath**, Week 6 ka pehla item.
**Har open item `narrowed` ya `open` — `closed` sirf wahan jahan measurement ne band kiya.**

**DoD audit:** `docs/planning/WEEK_05.md` ke *"Week 5 ka Definition of Done"* ki har line — `[x]` ya ek line: `deliberately
deferred — owner` ya `slipped — needs <X>`. **`P-45` wali line ke liye dhyaan:** teen numbers replace hue; Faisla 3 ka
load harness nahi.

**Executable end:**

```powershell
$p = Get-Content docs\planning\WEEK_05.md
$dod = $p[($p | Select-String -SimpleMatch "## Week 5 ka Definition of Done").LineNumber..($p | Select-String -SimpleMatch "## PART B").LineNumber]
@("dod_unticked_without_reason=" + ($dod | Where-Object { $_ -match '^- \[ \]' -and $_ -notmatch 'deferred|slipped' } | Measure-Object).Count,
  "dod_ticked=" + ($dod | Where-Object { $_ -match '^- \[x\]' } | Measure-Object).Count,
  "handoff_exists=" + (Test-Path docs\daily\WEEK_05_HANDOFF.md),
  "handoff_publishable=" + ($(git check-ignore -q docs/daily/WEEK_05_HANDOFF.md; $LASTEXITCODE) -ne 0)) | Out-File -Encoding utf8 logs\w5d6_step8_close.txt
Get-Content logs\w5d6_step8_close.txt         # 0 · (jo bhi) · True · True
```

---

### Step 9 — 10 min: ek external postmortem, `P-43` pe mapped

`docs/POSTMORTEMS.md` me `Incident 04`. Ek **public** postmortem chuno jisme ek process apni dependency ke restart pe mar
gaya, ya restart hone ke baad bhi broken raha. Shape baaki teen incidents jaisa: source link, kya hua, mechanism, aur ek
section *"Relay me ye kahan hai"* — `P-43`, `D-30`, aur Din 5 ka `P-56` agar lagu ho.

**Executable end:** `(Select-String -Path docs\POSTMORTEMS.md -Pattern "^## Incident 04" | Measure-Object).Count` → `1`,
aur usme `P-43` ka naam.

---

### Step 10 — 10 min: close — bench, fresh clone, commit

```powershell
$o = [System.Collections.Generic.List[string]]::new()
$o.Add("src_diff=" + (git diff --name-only HEAD -- src/ | Measure-Object).Count)
git hash-object src/worker.py src/reaper.py src/dispatcher.py src/main.py src/database.py src/sink.py | ForEach-Object { $o.Add("hash $_") }
$o.Add("heads=" + ((.\.venv\Scripts\python.exe -m alembic heads 2>&1) -join ' | '))
$o.Add("except_BaseException=" + (Select-String -Path src\*.py -Pattern "except BaseException" | Measure-Object).Count)
$o.Add("relay_underscore_dbs=" + ((docker exec relay-db-1 psql -U postgres -d postgres -t -A -c "SELECT count(*) FROM pg_database WHERE datname LIKE 'relay\_%';") -join ''))
$o.Add("relay_python=" + (Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count)
$o.Add("key_index=" + (git ls-files -- "*_KEY.md" | Measure-Object).Count)
$o.Add("key_tree=" + (git ls-tree -r --name-only HEAD | Select-String -CaseSensitive "_KEY\.md" | Measure-Object).Count)
$o.Add("brief_control=" + (git ls-files -- "*_BRIEF.md" | Measure-Object).Count)
$o.Add("p54=" + (git status --porcelain | Select-String -CaseSensitive "_ANSWERS\.md|_DESIGN\.md|_PROBLEM\.md|_PROPERTY\.md" | Measure-Object).Count)
$o.Add("tracked_ignored=" + (git ls-files -ci --exclude-standard | Measure-Object).Count)
$o.Add("frozen_sha256=" + (Get-FileHash -Algorithm SHA256 docs\daily\week_05\DIN_06_PREDICTIONS_FROZEN.md).Hash)
$o.Add("frozen_git_blob=" + (git hash-object docs\daily\week_05\DIN_06_PREDICTIONS_FROZEN.md))
$o.Add("counters=" + ((docker exec relay-db-1 psql -U postgres -d relay -t -A -F "|" -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');") -join ''))
$o | Out-File -Encoding utf8 logs\w5d6_step10_bench.txt
Get-Content logs\w5d6_step10_bench.txt
Get-Content logs\w5d6_step0_frozen_hash.txt
```

**Commit — named files:** `docs/DECISIONS.md`, `README.md`, `docs/month_01/logs/WEEK_04.md`, `docs/POSTMORTEMS.md`,
`docs/daily/WEEK_05_HANDOFF.md`, `docs/daily/week_05/DIN_06_PREDICTIONS_FROZEN.md`, `.gitignore`, aur agar Step 1 me
chuna to `.gitattributes`. **`git diff --cached --name-only` file me, commit se pehle.**

**Fresh clone — commit ke baad, `%TEMP%` me, check ke baad delete:**

```powershell
$dst = Join-Path $env:TEMP ("w5d6_clone_" + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
git clone -q --no-hardlinks . $dst
$k = [System.Collections.Generic.List[string]]::new()
foreach ($f in 'docs/daily/week_05/DIN_04_PREDICTIONS_FROZEN.md','docs/daily/week_05/DIN_05_PREDICTIONS_FROZEN.md','docs/daily/week_05/DIN_06_PREDICTIONS_FROZEN.md') {
  $k.Add("$f here=" + (Get-FileHash -Algorithm SHA256 $f).Hash.Substring(0,8) + " clone=" + (Get-FileHash -Algorithm SHA256 (Join-Path $dst $f)).Hash.Substring(0,8) + " clone_blob=" + (git -C $dst hash-object (Join-Path $dst $f)).Substring(0,8) + " head_blob=" + (git rev-parse "HEAD:$f").Substring(0,8))
}
Remove-Item -Recurse -Force $dst
$k.Add("clone_removed=" + (-not (Test-Path $dst)))
$k | Out-File -Encoding utf8 logs\w5d6_step10_clone.txt
Get-Content logs\w5d6_step10_clone.txt
```

---

## PART B — Prediction questions

> **Gemini ko NAHI. Har sawaal apne step se PEHLE, apne head se. Aaj se `idk` sub-part level pe.** Jis sub-part me
> file, command ya line ka naam hai, **pehle wo kholo/padho, aur jawab ke saath line number likho**. Wo Situation 1 hai.
> Kaunsa rule chunna hai (Step 1) wo Situation 3 hai — uspe prediction nahi, faisla hai. Neeche ke sawaal outcomes ke
> hain.

```text
Q1 (Step 0 se pehle — Din 5 commit)
(a) Commit ke baad `git ls-files logs` kitni files dikhayega? Aur WEEK_05.md
    ke Din 5 section me jo logs/w5d5_* paths cite hain, ek fresh clone me unme
    se kitne khulenge? (.gitignore padh ke)
(b) Commit ke baad `git ls-files -- "*PREDICTIONS_FROZEN*"` — number.
(c) DIN_05_PREDICTIONS_FROZEN.md pe, isi working copy me, commit ke baad:
    Get-FileHash wahi 8B38705B… rahega ya badlega? Aur `git hash-object` us
    file pe vs `git rev-parse HEAD:<path>` — same ya alag?

Q2 (Step 2 se pehle — rule ka differential)
(a) AAJ ke rule ke neeche (.gitignore:47 jaisa hai), chaar probes —
    DIN_99_BRIEF.md, DIN_99_KEY.txt, DIN_99_SEALED.md, DIN_99_NEWCLASS.md —
    har ek PUBLISH ya ignored?
(b) Ek flip rule socho: `**/daily/**`, phir `!**/daily/**/*_BRIEF.md`,
    `!**/daily/**/*_PREDICTIONS_FROZEN.md`, `!**/daily/**/*HANDOFF*.md` — aur
    directory re-include ki koi line NAHI. Chaaron probes ka kya hoga? Aur
    docs/month_01/daily/WEEK_04_HANDOFF.md jaisi file (seedha daily/ ke andar,
    kisi subfolder me nahi) — nayi aisi file publish hogi ya nahi? Mechanism.
(c) Sahi flip ke baad `git ls-files -ci --exclude-standard` (aaj 1) — kitna,
    aur kaunsi file judegi, agar tu sirf BRIEF/FROZEN/HANDOFF re-include kare?
(d) Flip ke baad pehle se tracked 28 BRIEFs untrack ho jaayenge? Haan/nahi,
    aur kyun.

Q3 (Step 3 se pehle — .pyc)
(a) `git rm --cached` + commit ke baad: pyc_tracked, pyc_in_01f42c6_bytes,
    pyc_on_disk — teeno values.
(b) Is hafte ke har Part C me `git ls-files -- "*.pyc"` → 1 positive control
    tha. Removal ke baad wo check kya prove karta hai, aur usko replace kyun
    karna padega? (Din 3 ka ls-tree wala sabak yaad kar.)

Q4 (Step 6 se pehle — README rows)
(a) Row 9 ka crash point: "worker aur reaper dono us outage me marte hain".
    Din 5 ke baad, is repo ke code pe, ye crash point hota bhi hai? Evidence
    ke naam se jawab.
(b) Din 5 ka job 8 outage ke waqt exactly kis phase me tha — handler me, ya
    kahin aur? README ki kaunsi row uska evidence banti hai, aur kyun wo row 8
    ke shabdon se exactly match nahi karta? (w5d5_step6_inflight.txt padh ke)
(c) Agar README ka evidence cell `logs/w5d5_step6_final_jobs.txt` cite kare, to
    GitHub pe padhne wala use khol payega?

Q5 (Step 10 se pehle — fresh clone; sirf tab jab Step 1 me .gitattributes
    `*_PREDICTIONS_FROZEN.md -text` chuna ho. Nahi chuna to (a)-(c) ko us
    rule ke hisaab se predict karo jo chuna)
(a) Fresh clone of HEAD: DIN_04_PREDICTIONS_FROZEN.md ka clone SHA-256 ==
    62196E9A… ?
(b) Usi clone me `git checkout c145a11` (attribute se pehle ka commit) karke
    phir hash karo — kya aayega? Aur ek alag fresh clone `--no-checkout` +
    `git checkout c145a11` me?
(c) Teeno cases me `git hash-object` on the clone's file vs head_blob — same
    ya alag?
(d) Seal ke liye kaunsa number har clone pe same rahega — working-copy
    SHA-256, ya git blob id? Ek line mechanism.
```

---

## PART C — Verification

**Din 5 ka sabak:** jis check ki output file nahi bani, wo chala hi nahi — chahe report me *"pass"* likha ho. **Har check
ka ek file.** Aur jahan outcome Part B ka sawaal hai, wahan value nahi di gayi — sirf ye ki instrument us value ko pakad
sakta hai.

### C1 — Commit aur surface

| Subject | Check | Broken reading |
|---|---|---|
| `w5d6_step0_staged.txt` | exactly `9` lines, `0` matching `_KEY\.md\|_ANSWERS\|_DESIGN\|_PROBLEM\|_PROPERTY` | `-A` ne `P-54` ki files utha li |
| har `0`-expecting `ls-files` check | usi file me ek positive control jo `≥ 1` ho — **Step 3 ke baad `*_BRIEF.md`**, `*.pyc` nahi | control hi gayab, zero decorative |
| `key_tree` | `git ls-tree -r --name-only` + `Select-String -CaseSensitive` (pathspec nahi — Din 3: `ls-tree` pathspec always-zero) | |

### C2 — Rule differential (Step 2)

| Subject | Check | Kya pakadta hai |
|---|---|---|
| `DIN_99_BRIEF.md` | `PUBLISH` | *"sab ignore"* wala rule |
| `frozen_05_publishable` | `True` | seal file chhup gayi |
| `dryrun_key_md` | `0` | seal leak |
| `probes_left` | `0` | probe files commit me chali gayi |
| `tracked_ignored` ki list | har file naam se file me | ek naya tracked∩ignored bina naam ke |

### C3 — Decisions (Steps 1, 4, 5)

| Subject | Check |
|---|---|
| `w5d6_step1_d32.txt` | `0` · `0` · `1` · `≥ 1` |
| `w5d6_step4_d30.txt` | `0` · `1` · `≥ 1` · `≥ 2` · `≥ 1` |
| `w5d6_step5_d28.txt` | chaaron `≥ 1` |
| teeno entries | **koi purani line edit nahi** — `git diff -U0 -- docs/DECISIONS.md` me `-` lines sirf header ki (`DRAFT`/`OPEN`), aur file me likho: `git diff -U0 -- docs/DECISIONS.md \| Select-String '^-[^-]' \| Out-File logs\w5d6_c3_removed_lines.txt` |
| har naya number | `[MEASURED …]` + file ka naam; koi `strictly`, `zero`, `closes` jahan measurement `narrows` kehta hai |

### C4 — README (Step 6)

| Subject | Check | Broken reading |
|---|---|---|
| `w5d6_step6_readme.txt` | har badli row me `week5 ≥ 1` | row badli, source nahi |
| verdict words | rows 4/7/8/9 me sirf `protected` / `narrowed` / `[NO EVIDENCE]` | ek chautha shabd |
| `cites_logs_dir` | value file me — kya honi chahiye, Part B `Q4(c)` | |

### C5 — Rewrites aur close

| Subject | Check |
|---|---|
| `w5d6_step7_rewrites.txt` | `4` · `4` · `6` |
| `w5d6_step8_close.txt` | `0` · (jo bhi) · `True` · `True` |
| `w5d6_step10_bench.txt` | `src_diff=0`, chhe hashes Step 0 ke barabar, `heads=w4d4_sink_unique (head)`, `except_BaseException=0`, `relay_underscore_dbs=0`, `relay_python=0`, `key_index=0`, `key_tree=0`, `brief_control ≥ 28`, counters `133\|145\|19\|4\|7\|39\|5\|0\|1` |
| frozen hash | `frozen_sha256` aur `frozen_git_blob` = `w5d6_step0_frozen_hash.txt` ki dono lines |
| `w5d6_step10_clone.txt` | teen lines + `clone_removed=True`. Values Part B `Q5` |
| `p54` at close | Step 1 ke faisle ke baad jo number hona chahiye — **wo number `D-32` ke Din 6 section me likha ho, aur file uske barabar** |

### C6 — Aaj ye quote nahi honge

| Kya | Kyun |
|---|---|
| *"D-30 strictly satisfied"* | gate as written satisfied; bound boundaries se, backoff kabhi nahi chala |
| *"zero corrupted"* | naapa nahi gaya |
| *"attempt 6 succeeded"* bina *"sink: duplicate"* ke | effect attempt 1 ki orphan ne apply kiya |
| worker log ki `[mark]` count *"marks"* ke naam se | prints hain, commits nahi (`P-56`) |
| *"seal auditable by anyone"* bina `P-57` ke | Windows clone pe working-copy hash badalta hai |
| `2.8133 s`, `0.4703 s`, `3.0055 s`, `3.1618 s`, `7.6771 s` bina *"retired"* | sab replace hue |

---

## PART D — Scope guard

| Kya | Owner | Kyun aaj nahi |
|---|---|---|
| Koi bhi `src/` edit — `P-44`, `P-51`, `P-55`, `P-56` | **Week 6** | Week rule. Aaj verdicts us code ke likhe ja rahe hain jo naapa gaya |
| `P-56` census | **Week 6**, fix ke saath | census fix ko scope karta hai; aaj ka budget verdicts pe |
| `os._exit` crash-loop pe supervisor backoff ka run | **Week 6** | `D-30` me deferred + owner. Aaj run kiya to *"close"* ek naye measurement pe khada hoga jiska review nahi hua |
| Supervisor backoff redesign, child PID logging (`P-53(b)`) | **Week 6** | |
| `logs/` retention / pruning, ya `logs/` ka koi hissa publish karna | **Week 6 ya baad**, `D-32` ka doosra half | aaj ka `D-32` publishing surface hai; retention ek alag faisla hai aur uska owner `D-32` me naam se likho |
| Week 5 ke paanch `💡` | **Week 6 Din 1** | aaj Week 4 ke chaar |
| History rewrite, `filter-repo` | **kabhi nahi, bina explicit faisle ke** | one-way door ki doosri taraf |
| `git push` | **user ka faisla, aaj ki list me nahi** | publishing surface abhi-abhi final hua; push se pehle `git log --stat origin/main..HEAD` padho |
| Processes Compose me | `D-30` option (a), **Month 2 ke baad** | har retained baseline invalid |
| Koi migration, koi `POST /jobs` evidence DB pe | **kabhi nahi aaj** | `alembic heads` gate, counters gate |
| Week 6 ka planning | **Week 6 Din 0** | aaj close hai, open nahi |

**Cut order, agar time khatam ho:** Step 9 (postmortem → Week 6, DoD me `slipped — needs 10 min`) → Step 5 (`D-28` ka
amendment → Week 6 Din 1, par `D-30` ke Cost me ek line ki *"discriminator logs me hai"*) → Step 3 (`.pyc`: *"leave it"*,
ek line, control intact). **Kabhi cut nahi:** Step 0, Step 1–2 (`D-32` aaj final hona hai, warna `P-54` teesre hafte
carry), Step 4 (`D-30`), Step 7 (`💡` chautha carry nahi hona chahiye), Step 10.

---

*Wapas:* [`../../logs/WEEK_05.md`](../../logs/WEEK_05.md) · *Din 5 BRIEF:* [`DIN_05_BRIEF.md`](DIN_05_BRIEF.md) ·
*Seal:* `DIN_06_PREDICTIONS_FROZEN.md` (Step 0 pe banegi)
