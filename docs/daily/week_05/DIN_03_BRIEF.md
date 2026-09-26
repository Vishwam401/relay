# WEEK 5 · DIN 3 — `2026-09-26` — Ek retention faisla, ek misclassified DB fault, aur gyarah pins

**Budget `125 min` · Layer L2 · Aaj `src/` me ek line nahi badlegi — aur wo ek gate hai, ek preference nahi**
**Aaj ka din teen din se bada hai kyunki aaj ke faisle decide karte hain ki Din 1 aur Din 2 ka kaam
kal bhi maujood rahega ya nahi.**

> **Do din ki sabse valuable cheezein aaj repository me nahi hain.** Din 1 ka Step 6 seam, Din 2 ka
> `fault_to_reclaim = 35.191 s`, supervisor ke chaar restarts, `pre_ping` ka `p50` — inn sab ke artifacts
> `logs/` aur `scratch/` me padhe hain, aur **`git log --all` me `logs/` ka ek bhi path aaj tak kabhi nahi
> aaya** — `0`, poori history me `[MEASURED-R 2026-09-25]`. `docs/logs/WEEK_05.md`, jisme ye dono din likhe
> hain, wo bhi kisi commit me nahi hai.
>
> **Aur ek cheez jo iss din ka shape badal deti hai, aur wo tere apne commits me hai.** `2026-09-24` ko —
> Din 1 wale din — teen commits ne tracking **kam** ki: `docs/career/`, `docs/dsa/`, `scratch/`, `scripts/`,
> aur `docs/blog/` ke **nau** files (`1639` lines, jisme published post bhi hai). Aaj ka kaam `P-47` band
> karna hai, aur `P-47` tracking **badhane** ka sawaal hai. **Do direction hain aur wo aapas me takra rahi
> hain.** Jo bhi faisla aaj likhe, usko unn teen commits ke saath reconcile hona padega — warna `D-32` apne
> hi hafte ke teen commits ke khilaaf khadi hogi.
>
> **Aur teesri cheez jo sabse mehengi hai aur sabse chhoti dikhti hai: `P-51`.** `await
> record_execution(...)` handler ke `try` ke andar hai, to `job_executions` unavailable hone pe ek **healthy**
> job `~10 s` me `dead_letter` ho jaati hai, `attempts = 3` pe, `last_error` me `UndefinedTableError` ka
> traceback le kar, aur handler **ek baar bhi nahi chalta**. `D-26` ke `Cost 6` ko do outage chahiye. Isko
> **ek**. Ye ek faisla hai; aaj ka koi bhi edit isko chhupa nahi sakta.

---

## PART A — Steps

### Step 0 — 10 min: bench, aur do gate jo structurally toote hue hain

```powershell
cd d:\PROJECTS\relay
git status --short          # expected: khaali — Din 2 commit ho chuka hai
git log --oneline -1        # expected: d277375 feat(w5d2): process exception boundaries, ...
```

**Din 2 commit ho chuka hai** — `d277375`, *"feat(w5d2): process exception boundaries, D-31 decision, and Din 2
review docs"*, chhe files, working tree **clean** `[MEASURED-R 2026-09-25]`. To Din 2 ka *"`0` commits"* wala
haal khatam hai.

**Par us commit me ek cheez nahi hai, aur wo aaj ke din ka subject hai.** Uska message *"Din 2 review docs"*
kehta hai; `docs/logs/WEEK_05.md` — jisme Din 2 ka **poora** entry likha hai — us commit me **nahi** hai,
kyunki wo `.gitignore` line `39` se ignored hai. **Din 1 ka commit `997f5cd` bhi exactly yahi karta hai:**
message me *"and Day 1 logs"*, aur commit me `logs/` ki **shoonya** files. **Do din, do commits, dono ka
message wo claim karta hai jo commit me nahi hai.** Ye aaj ka sabse saaf single example hai ki `P-47` kya
cheez hai.

**Aur do gate abhi bhi galat hain. Dono ka kaaran naam se:**

| Purana gate | Kyun toota hua hai | Aaj ka replacement |
|---|---|---|
| `git rev-parse HEAD:src` | Ye **committed** tree padhta hai. Din 2 pe teen `src/` files badli thi aur commit baad me hua, to *"Step 0 se badla hua"* us din pass hi nahi ho sakta tha. Aaj ulta chahiye — *"badla hua nahi"* — aur agar aaj beech me koi commit hua to ye gate uske saath move kar jaayega | `git hash-object src/worker.py src/reaper.py src/dispatcher.py` — **working tree** ke bytes ka hash. Index aur commit dono se independent, to wo dono dinon ke shape me kaam karta hai |
| `(Get-Process python).Count` | Host ki **koi bhi** python ginta hai. Abhi ek chal rahi hai aur wo Relay ki nahi — wo ek editor ka gateway process hai | command line pe filter — neeche |

```powershell
# aaj ka src gate — teen hashes likh lo, close pe inhi se compare karna hai
git hash-object src/worker.py src/reaper.py src/dispatcher.py

# Relay-only process count
(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count

# expected: w4d4_sink_unique (head)  — ek line, ek head
.\.venv\Scripts\python.exe -m alembic heads
```

Nau counters evidence DB `relay` pe. **Note: role `postgres` hai, `relay` nahi** — `psql -U relay` `FATAL:
role "relay" does not exist` deta hai:

```powershell
docker exec relay-db-1 psql -U postgres -d relay -t -A -F "|" -c "SELECT (SELECT count(*) FROM jobs), (SELECT count(*) FROM job_executions), (SELECT count(*) FROM side_effects), (SELECT count(*) FROM outbox), (SELECT count(*) FROM sink_deliveries), (SELECT last_value FROM side_effects_id_seq), (SELECT last_value FROM outbox_id_seq), (SELECT count(*) FROM jobs WHERE status='pending'), (SELECT count(*) FROM jobs WHERE status='running');"
```

**Expected `133|145|19|4|7|39|5|0|1`**, delta `0`.

**Executable end:** teen `src` hashes likhe hue, Relay-process count `0`, nau counters ka output, **aur aaj ka
`DIN_03_PREDICTIONS_FROZEN.md` likha aur hash liya hua** — Part B ke paanch jawab, `idk` included.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| `git hash-object <file>` | File ke **current content** ka SHA-1 blob hash. Index aur commit dono se independent — sirf bytes padhta hai |
| `git rev-parse HEAD:<dir>` | `HEAD` commit ke andar us directory ka tree hash. Working tree ke changes isme **nahi** dikhte |
| `Get-CimInstance Win32_Process` | WMI se process list, aur ye `CommandLine` bhi deti hai — `Get-Process` nahi deta |
| gate ka input | wo expected value jiske against check compare karta hai. Galat input wala check pass aur fail dono galat de sakta hai |

---

### Step 1 — 15 min: pehle surface naapo, phir faisla — aur ye order Din 2 ka sabak hai

Din 2 ka teesra finding ye tha: **boundary ek classification deti hai, protection nahi** — aur `P-51` isliye
nahi mili ki wo **traceback produce hi nahi karti.** Death frames padhne ki technique khatam ho chuki hai;
**state padhni padti hai.** Aaj wahi lesson `.gitignore` pe lagta hai: rule likhne se **pehle** naapo ki abhi
kya tracked hai.

**Kuch decide mat karo iss step me. Sirf ginti.**

```powershell
# 1. kitni files tracked hain, total aur docs/ me
(git ls-files | Measure-Object).Count
(git ls-files docs/ | Measure-Object).Count

# 2. disk pe kitni hain
(Get-ChildItem docs -Recurse -File | Measure-Object).Count

# 3. artifact class ke hisaab se disk pe ginti
foreach ($p in 'BRIEF','KEY','PREDICTIONS_FROZEN','HANDOFF') {
  "$p = $((Get-ChildItem docs -Recurse -File -Filter "*$p*" | Measure-Object).Count)"
}

# 4. ye wala sabse important hai — tracked files jinko ek ignore pattern ALREADY match karta hai
git ls-files | git check-ignore --no-index --stdin -v

# 5. kya logs/ ka koi path kabhi commit hua hai, poori history me
(git log --all --name-only --pretty=format: -- "logs/" | Where-Object { $_ } | Sort-Object -Unique | Measure-Object).Count
```

**Executable end — ek table, aur uski aakhri row aaj ka pehla real finding hai:**

| Class | disk pe | tracked | ignore pattern match karta hai |
|---|---|---|---|
| `docs/` total | | | |
| `BRIEF` / `KEY` / `PREDICTIONS_FROZEN` / `HANDOFF` | | | |
| `docs/month_01/logs/WEEK_0*.md` | | | |
| `docs/logs/WEEK_05.md` | | | |
| **`git ls-files` ∩ ignored** | — | | |

**Aur check 4 ke output me ek file aisi hai jo document nahi hai aur usko kabhi commit nahi hona chahiye
tha.** Usko naam se likho, aur likho ki wo abhi bhi wahan **kyun** hai. Ye `Q1` hai.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| tracked | file jo git ke **index** me hai. Tracking ek per-file state hai, directory ka property nahi |
| ignored | file jiska path kisi `.gitignore` pattern se match karta hai. Ye **pattern** ka property hai, index ka nahi |
| `git check-ignore --no-index` | pattern match batao **chahe file tracked ho ya na ho**. Bina iss flag ke behaviour alag hai, aur wo farak `Q3` hai |
| `--stdin` | paths ko argument ki jagah standard input se lo — long lists ke liye |

---

### Step 2 — 15 min: classification rule — **ye `D-32` ka pehla field hai, aur faisla tera hai**

`P-47` ka core sentence: ye ek **typo nahi, classification problem hai.** `docs/daily/` me sealed KEY hain jo
public **nahi** honi chahiye, aur BRIEF / handoff / frozen files jo honi chahiye. **Directory ek coarse unit
hai** us distinction ke liye jo enforce karni hai.

**Scope chaar cheez ka hai, `P-47` ke amendment aur `P-50` ke baad:**

1. `logs/` — runtime artifacts, aur `docs/logs/` jo sirf naam se `logs` hai
2. harness console transcripts (`P-50`) — jo `.gitignore` se theek **nahi** hote
3. `scripts/` — Din 2 ka measurement instrument (`scripts/supervisor.py`) kisi commit me nahi hai
4. `docs/daily/` ka andar ka farak — KEY vs baaki sab

**Chaar options, chaaron ka asli cost. Ye `P-47` me likhe hain aur inme se ek bhi free nahi hai:**

| Option | Cost |
|---|---|
| (1) Directory split — `KEY` ignored, `docs/daily/` ka baaki track | Sabse sasta, aur rule **actual invariant** express karta hai. Par uska pattern ka shape ek trap hai — `Q2` |
| (2) Files ko ignored subtree ke bahar move karo (`docs/handoffs/`, `docs/frozen/`) | Path saaf, aur **har relative link tootegi**. Month 1 archive move me `99` links re-resolve hui thi |
| (3) `git add -f` se specific files | Aaj chalta hai, kal drift karta hai — agla BRIEF phir ignored hoga. Aur ek irreversibility saath laata hai: `Q3` |
| (4) Chhod do, aur teen naye links delete kar do | Honest, aur artifact phenk deta hai |

**Ek paanchwan constraint jo inn chaaron se upar hai aur wo tere apne commits se aata hai.** `2026-09-24` pe
`f6a85c2`, `2582b37`, `15d82d9` — teen commits ne `docs/blog/`, `docs/career/`, `docs/dsa/`, `scratch/`,
`scripts/` untrack kiye. Aur poori history me **saat** aise commits hain (`5da8fe4`, `270078c`, `74f8611`,
`a516d76`, `15d82d9`, `2582b37`, `f6a85c2`) `[MEASURED-R 2026-09-25]`. **Matlab publishing surface saat baar
reactively kam hui hai aur ek baar bhi decide nahi hui.** `D-32` ka kaam wahi hai jo aaj tak nahi hua: rule
pehle likho, pattern baad me.

**Gemini se options aur unke costs discuss kar sakta hai. Pick usse nahi poochna** — iska koi ek sahi jawab
nahi hai, aur ye tera repository hai.

**Executable end — koi `.gitignore` edit NAHI. Sirf ek likha hua rule**, `docs/DECISIONS.md` ke `D-32` draft
me ya ek scratch note me. Har artifact class pe ek line, teen column: class · `public` ya `local` · **kaaran**.
Aur ek line jo unn teen commits ko address kare: *blog/career/dsa untrack rehte hain kyunki ___.*

**Terms used in this step**

| Term | Kya hai |
|---|---|
| sealed KEY | us din ke prediction questions ke jawab. Seal rule kehti hai wo measurement ke **baad** khulti hai — public repo me wo kisi aur ke liye seal nahi rehti |
| classification problem | jab ek rule ko do cheezein alag karni hain par uska unit unse **mota** ho. Directory-level ignore, file-level invariant |
| publishing surface | wo set jo `git clone` karne wale ko dikhta hai |
| retention | ye sawaal ki evidence **kitne din** aur **kahan** zinda rehti hai. Tracking se alag sawaal hai |

---

### Step 3 — 20 min: rule ko `.gitignore` me likho, aur ek check banao jo **fail kar sake**

Ab edit. **Aur yahan ek behaviour hai jo padh ke pata nahi chalta** — isliye `Q2` iss step se pehle answer
hona hai, aur uske baad run karke dekhna hai.

Abhi ke relevant lines, `check-ignore` se attribute ki hui `[MEASURED-R 2026-09-25]`:

```
.gitignore:19:__pycache__/     .gitignore:39:logs/        .gitignore:48:**/planning/
.gitignore:49:**/daily/        .gitignore:52:docs/roadmap/
.gitignore:73:scratch/         .gitignore:74:scripts/
```

**Do chhoti cheez jo `P-47` amendment ne naam se di hain, aur wo ek-ek character hain:** `logs/` aur
`scripts/` dono **unanchored** hain, to wo kisi bhi depth pe match karte hain — isliye `docs/logs/WEEK_05.md`
line `39` se ignored hai. Anchor (`/logs/`, `/scripts/`) usko rok deta hai.

**Aur ab wo hissa jo ek pattern likhne se `nahi` hota.** Step 2 me tune jo rule chuna hai, usko express karne
ke do shape hain aur **ek shape chup-chaap kuch nahi karta.** Kaunsa — wo `Q2` ka jawab hai aur wo run se
milega, argue karne se nahi.

**Run karne ka tareeka, aur ye destructive nahi hai:**

```powershell
# pattern likhne ke baad — kya STAGE hoga, actually stage kiye bina
git add -A --dry-run
git status --porcelain docs/daily/week_05/
```

**Aur seal ka check.** Ek check chahiye jo *"koi KEY track nahi hui"* ko prove kare. Pehla instinct
`git check-ignore -v <KEY>` hai aur **wo instinct exactly us case pe ulta jawab deta hai jiske liye check
exist karti hai** — `Q3`. Isliye seal ka check teen hisse ka hai:

```powershell
# index — git pathspec, case-sensitive, verified with a positive control
(git ls-files -- "*_KEY.md" | Measure-Object).Count                                  # must be 0

# commit tree — dhyaan do, yahan pathspec NAHI chalti (neeche dekho kyun)
(git ls-tree -r --name-only HEAD |
  Select-String -CaseSensitive "_KEY\.md" | Measure-Object).Count                     # must be 0

# pattern
git check-ignore -v --no-index docs/daily/week_05/DIN_03_KEY.md                       # must print the line
```

**Do cheez inn commands me deliberate hain aur dono ek galat check se bachne ke liye hain
`[MEASURED-R 2026-09-25]`:**

- **`git ls-tree` ke saath `-- "*KEY*"` pathspec use NAHI karni.** `ls-files` ki pathspec wildmatch hai,
  `ls-tree` ki nahi — `git ls-tree -r --name-only HEAD -- "*.pyc"` ek tracked `.pyc` hote hue bhi **khaali**
  output deta hai. Matlab wo check **hamesha `0`** deti hai, chahe KEY leak ho ya na ho. **Wo decorative hai**
  — theek wahi shape jo Din 2 ke `413` gate ka tha
- **`-CaseSensitive` zaroori hai.** `Select-String` default me case-insensitive hai, aur
  `alembic/versions/dbe13b69056d_add_effect_key_and_unique_constraint_to_.py` me `effect_key` hai — wo
  `"KEY"` se match kar jaata hai aur ek **saaf repo pe check fail** kar deta hai

**Apni check ko ek positive control se verify karo, warna `0` ka matlab pata nahi chalta:**

```powershell
(git ls-files -- "*.pyc" | Measure-Object).Count    # 1 aana chahiye — agar 0 aaya, teri pathspec kaam hi nahi kar rahi
```

**Executable end — teen cheez, aur pehli wali ek differential hai:**

- `git add -A --dry-run` ka output: BRIEF aur frozen file **naam se** aaye, KEY **na** aaye
- teeno seal checks ka output, `0 / 0 / ek line`
- ek line: **tera pehla pattern chala tha ya nahi.** Agar nahi chala, to kyun nahi chala — mechanism likho

**Ek cheez jo aaj mat karna:** `git add -f` kisi KEY pe, *"bas test karne ke liye"*. Uska kaaran `Q3` ka
doosra half hai aur wo reversible nahi hai.

**Terms used in this step**

| Term | Kya hai |
|---|---|
| anchored pattern | jisme `/` shuru me ya beech me ho. Wo `.gitignore` ki jagah se **relative** match karta hai, har depth pe nahi |
| negation pattern (`!`) | ek line jo pehle ignore hui file ko wapas include karti hai |
| directory pruning | git ka wo behaviour jisme ek ignored **directory** ke andar wo jaata hi nahi |
| `git add -A --dry-run` | batao kya stage hota, kuch stage kiye bina. Index chhoota nahi |
| `git ls-tree -r HEAD` | `HEAD` commit ke andar ki files. Index se alag cheez |

---

### Step 4 — 15 min: harness aur probe retention — wo half jo `.gitignore` theek **nahi** karta

`P-50` ka structural conclusion word-for-word: *"`.gitignore` on `logs/` is not the whole problem. These
artifacts were never **in** `logs/`."* Din 1 ke teen khoye hue numbers `Write-Host` pe the. Ek rule jo sirf
`logs/` ke baare me ho, unme se **ek bhi** nahi bachata.

**Do cheez naapo — aur dono ek hi hafte se hain, jo isko saaf kar deta hai:**

```powershell
git ls-files labs/                   # Din 1 ka exception probe kahan hai?
git ls-files scratch/                # Din 2 ke paanch harness kahan hain?
Get-ChildItem scratch -File | Select-Object Name
git log --all --oneline -- scratch/step6_harness.ps1
```

Aakhri command pe rukna — uska jawab `Q4` ka doosra half hai, aur wo `P-50` ki framing ko badalta hai.

**Teen cheez aaj likhni ya theek karni hain:**

1. **`logs/w5d2_step5_preping.log` ka fabricated section** — `=== OUTCOME ANALYSIS ===` ke neeche teen
   `print` statements hain jo measurement dikhti hain aur nahi hain (`P-52`). **Ya delete karo, ya
   `[NOT MEASURED — see P-52]` se annotate karo.** Chhodne ka matlab hai agla din usko quote karega
2. **`scratch/step5_preping_bench.py` ka `p99`** — `n = 100` pe wo `max` return kar raha hai. **Ya
   nearest-rank index theek karo, ya label `max` kar do.** Dono acceptable hain; chhupana nahi
3. **Ek rule, do line me:** probe **kahan** rehti hai, aur uska transcript kaise banta hai taaki re-run
   purane ko **overwrite na kare**. `P-50` ne mechanism de diya hai — filename me run id ya timestamp

**Executable end:**

- `git ls-files labs/` aur `git ls-files scratch/` ka output, saath me ek line: **dono ka faisla kisne kiya**
- `w5d2_step5_preping.log` ka wo section — delete ya annotate, aur `git diff` ya file ka naya content
- likha hua probe rule, aur ek check jo usko **fail** kar sake: ek probe do baar chalao aur log files gino.
  `1` mile to rule lagoo nahi hua, `2` mile to hua

**Terms used in this step**

| Term | Kya hai |
|---|---|
| transcript | process ke stdout/stderr ki ek file me likhi hui copy. Console pe dikhna transcript nahi hai |
| run id | ek unique string per run (timestamp ya counter) jo output filename me jaati hai |
| nearest-rank percentile | `p99` ka wo definition jisme sorted sample ka index `ceil(0.99 × n) − 1` hota hai |
| fabricated output | wo line jo output jaisi dikhti hai par kisi observation se nahi aayi |

---

### Step 5 — 15 min: `P-51` ka faisla — **aaj ka sabse mehenga item, aur isme koi code nahi**

**Yahan `Q` nahi hai, aur wo deliberate hai.** Outcome already measured hai (`P-51` me poora table hai), to
predict karne ko kuch nahi bacha. Ye **design judgement** hai — Situation 3. Gemini se options aur costs
discuss karna theek hai; **pick usse nahi poochna.**

Jo measured hai aur jisko given maanna hai `[MEASURED-R 2026-09-25]`: healthy `sleep` job,
`job_executions` unavailable → `dead_letter` at `attempts = 3` in `~10 s`, `last_error` me
`UndefinedTableError` traceback, `side_effects = 0`, `outbox = 0`, **handler ek baar bhi nahi chala.**

**Teen shapes, teeno ka cost `P-51` me hai. Chauthi cheez jo likhni hai wo `attempts` ka sawaal hai:**

`attempts` ke ab **teen carrier** hain aur **ek counter**:

| Carrier | Kahan se aata hai |
|---|---|
| Job ka apna failure | handler ne raise kiya — jiske liye `MAX_ATTEMPTS` bana tha |
| Lost mark | `D-26` ka `Cost 6` — ek outage, do attempts |
| Infrastructure fault | `P-51` — ek fault, teen attempts |

**`MAX_ATTEMPTS = 3` teeno ko same treat karta hai.** To sawaal: `attempts` ek number hai, ya do hone
chahiye? Do karne ka matlab schema change hai, aur **iss hafte `alembic heads` gate hai** — matlab faisla aaj
ho sakta hai, migration nahi.

**Executable end — koi `src/` edit nahi. Teen likhi hui cheezein:**

1. Chuna hua shape, aur **kaunsa cost accept kiya** — naam se
2. Uska **owner day**, kyunki fix aaj nahi hai. Ek din ka naam likho, `"Month 3"` nahi — ya agar `Month 3`
   hai to wo kis cheez ka wait kar raha hai
3. Ek line jo ye kehti ho: `D-30` ka boundary scope `P-51` ko **cover nahi karta**, aur ye boundaries ka
   failure nahi hai — unhone process-death surface **narrow** kiya, misattribution surface ko **chhua nahi**

**Terms used in this step**

| Term | Kya hai |
|---|---|
| misclassification | ek failure ko galat category me daalna — yahan infra fault ko job failure samajhna |
| audit table | wo table jo *kya hua* record karti hai, na ki *kya hona hai*. `job_executions` yahi hai |
| carrier | wo raasta jisse ek counter badhta hai. Ek counter ke kai carrier ho sakte hain |
| `alembic heads` gate | iss hafte ka rule: ek head, koi nayi migration nahi. Schema wale option ko aaj rokta hai |

---

### Step 6 — 15 min: `requirements.txt` — gyarah pins, aur resolver se, `freeze` se nahi

Abhi `requirements.txt` me gyarah line hain aur **ek bhi constraint nahi.** Week 4 ka DoD isko `slipped`
likh chuka hai.

**Do shortcut hain aur dono galat output dete hain. Chalao aur ginti dekho — `Q5`:**

```powershell
(.\.venv\Scripts\python.exe -m pip freeze | Measure-Object).Count
.\.venv\Scripts\python.exe -m pip list --not-required --format=freeze
```

Doosri command ki ginti pe **dhyaan se dekhna** — wo `requirements.txt` ki ginti ke barabar aati hai, aur wo
**wahi gyarah nahi hain.** Kaunsi do missing hain aur kyun — wo `pip show` se nikalta hai:

```powershell
.\.venv\Scripts\python.exe -m pip show sqlalchemy pytest | Select-String "^Name:|^Required-by:"
```

**Ek aur cheez jo dono shortcut tod dete hain:** `requirements.txt` ki line `psycopg[binary]` hai. `freeze`
aur `--not-required` dono usko **do** line banate hain aur `[binary]` extra ka declaration kho jaata hai.

**Resolver run — ye actual resolve karta hai, aur install nahi karta:**

```powershell
.\.venv\Scripts\python.exe -m pip install --dry-run --ignore-installed --report - -r requirements.txt
```

`--ignore-installed` ke **bina** ye sirf `Requirement already satisfied` likhta hai aur kuch prove nahi
karta — wo farak khud dekh lena.

**Executable end:** `requirements.txt` me **gyarah** pinned lines, `psycopg[binary]==` apne extra ke saath,
aur ek dry-run jo exit `0` de. Aur ek line: **kaunsa operator** chuna — `==`, `~=`, ya `>=,<` — aur kis
kaaran se. Ye `D-33` hai (grep karke confirm karna).

**Terms used in this step**

| Term | Kya hai |
|---|---|
| direct vs transitive dependency | direct wo jo tu import karta hai; transitive wo jo tere dependency ko chahiye |
| `pip list --not-required` | wo installed packages jinpe **koi doosra installed package** depend nahi karta |
| extra (`psycopg[binary]`) | ek optional dependency group jo package declare karta hai. `[binary]` pre-compiled wheel laata hai |
| `~=` (compatible release) | `~=1.2.3` ka matlab `>=1.2.3, ==1.2.*` — patch allowed, minor nahi |
| lock file vs pin | pin direct deps constrain karta hai; lock **poora** resolved graph hash ke saath freeze karta hai |

---

### Step 7 — 10 min: close bench

```powershell
# src/ AAJ badalna nahi chahiye — Step 0 ke teen hashes se compare karo
git hash-object src/worker.py src/reaper.py src/dispatcher.py

.\.venv\Scripts\python.exe -m alembic heads    # ek head, w4d4_sink_unique. Aaj koi migration NAHI
(Select-String -Path src\*.py -Pattern "except BaseException" | Measure-Object).Count   # 0
(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like "*PROJECTS\relay*" } | Measure-Object).Count       # 0
```

Nau counters — delta `0`. `pg_database LIKE 'relay\_%'` — `0` rows. Aaj koi disposable DB nahi bani honi
chahiye; agar bani to drop karo.

**`logs/w5d1_*`, `logs/w5d1r_*`, `logs/w5d2_*` teeno rakho.** Aaj unko delete karne ka din **nahi** hai —
aaj unke liye rule banane ka din hai, aur wo do alag cheezein hain.

**Aur aaj ka milestone, agar Step 3 chala:** `DIN_03_PREDICTIONS_FROZEN.md` pehli baar ek commit me jaayegi.
`git ls-files -- "*PREDICTIONS_FROZEN*"` ki ginti `0` se badalni chahiye.

---

## PART C — Verification

Har check ke saath ek sawaal: **kaunsa galat implementation isko bhi pass kar dega?**

### C1 — `.gitignore` ka rule — ek check kaafi nahi hai, teen chahiye

Ye aaj ka sabse important gate hai, kyunki *"KEY ignored hai"* **ek aisi rule ko bhi pass karta hai jisne
kuch bhi track nahi kiya.**

| Observation | Rule ne kuch nahi kiya (negation silently dead) | Rule ne sab track kar liya, KEY bhi | **Sahi** |
|---|---|---|---|
| `git check-ignore -v --no-index <KEY>` ek line print karti hai | ✅ | ❌ | ✅ |
| `git add -A --dry-run` me `DIN_03_BRIEF.md` **naam se** aata hai | ❌ | ✅ | ✅ |
| `git add -A --dry-run` me koi `*KEY*` **nahi** aata | ✅ | ❌ | ✅ |

**Teeno record karo.** Pehli row akeli wo silent-failure case bhi pass karti hai jisme `.gitignore` badla
aur kuch bhi trackable nahi hua — aur wo aaj ka sabse likely galat outcome hai.

### C2 — Seal ka check jo tracked-KEY case pe ulta nahi hota

| Check | Expected | Kya padhta hai / kya galti pakadta hai |
|---|---|---|
| `(git ls-files -- "*_KEY.md").Count` | `0` | **index** — to force-added KEY bhi pakadta hai |
| `(git ls-tree -r --name-only HEAD \| Select-String -CaseSensitive "_KEY\.md").Count` | `0` | **commit tree** — index se alag cheez |
| `git check-ignore -v --no-index <KEY>` | ek line, exit `0` | **pattern** — aur `--no-index` ke bina ye **tracked** KEY pe exit `1` deta hai, matlab *"ignored nahi"*, jo bilkul ulta hai |
| `(git ls-files -- "*.pyc").Count` | `1` | **positive control** — iske bina upar wale `0` ka koi matlab nahi |

**Chaaron zaroori hain aur pehle teen teen alag cheez padhte hain:** index, commit, aur pattern. `Q3` yahi
farak hai. **Chauthi row control hai** — ek check jo hamesha `0` deti hai aur ek check jo sahi se `0` deti
hai, output me identical dikhti hain.

### C3 — Probe retention rule fail kar sakti hai ya nahi

| Check | Mechanism maujood | Mechanism ghayab |
|---|---|---|
| Ek probe **do baar** chalao — `logs/` me kitni files | `2`, dono readable | `1` — doosra pehle ko kha gaya, aur ye `P-50` ka exact mechanism hai |
| `logs/w5d2_step5_preping.log` me `poll_failures = 5` wali do line | delete, ya `[NOT MEASURED]` label ke saath | bina label — agla din usko measurement samajh ke quote karega |
| `p99` wali line | `max` label, ya theek kiya hua index | `p99` likha hua `max` value ke saath, `n = 100` pe |
| `git ls-files scripts/` | Step 2 ke rule ke mutabik — aur jo bhi ho, **likha hua** | rule ke khilaaf, aur kisi ko pata nahi |

### C4 — `requirements.txt` — ginti aur content dono, kyunki ginti akeli jhooth bol sakti hai

| Check | Expected | Kyun ginti akeli kaafi nahi |
|---|---|---|
| `(Select-String -Path requirements.txt -Pattern "==" ).Count` | `11` | `pip list --not-required` bhi `11` deta hai aur wo **galat** gyarah hain |
| `psycopg\[binary\]==` maujood | `1` match | `freeze` wala output `psycopg==` aur `psycopg-binary==` deta hai — ginti badh jaati hai, extra kho jaata hai |
| `sqlalchemy` aur `pytest` dono pinned | dono maujood | `--not-required` inhe **chhod** deta hai, aur kaaran `pip show` me hai |
| `pip` khud pinned **nahi** hai | `0` match | `--not-required` usko **include** karta hai |
| `pip install --dry-run --ignore-installed --report - -r requirements.txt` | exit `0` | `--ignore-installed` ke bina ye sirf `already satisfied` likhta hai aur resolve hi nahi karta |

### C5 — Aaj `src/` nahi badla, aur ye aaj ka sabse aasan gate hai to isko decorative mat banao

| Check | Expected |
|---|---|
| `git hash-object src/worker.py src/reaper.py src/dispatcher.py` | Step 0 ke **teen hashes ke barabar** |
| `alembic heads` | ek — `w4d4_sink_unique` |
| `except BaseException` in `src/` | `0` |
| Relay python processes at close | `0` — aur ye **filtered** count hai, bare `Get-Process` nahi |

### C6 — Evidence DB untouched, aur numbers ke saath unka source

| Check | Expected |
|---|---|
| Nau counters delta | `0` |
| Job `108` · `128` · `136` | `dead_letter\|4\|0` · `succeeded\|4\|4` · `running\|1\|1` |
| `pg_database LIKE 'relay\_%'` | `0` rows |
| `DIN_03_PREDICTIONS_FROZEN.md` | maujood, hash Step 0 aur Step 7 dono pe liya hua |
| Aaj ka har number | `[MEASURED 2026-09-26]` label ke saath |

**`P-53` ka rule aaj se lagoo hai aur aaj usko todne ka koi bahana nahi hai:** aaj koi fault inject nahi hoti,
to koi fault timestamp nahi chahiye — **par har command ka output ek file me jaata hai.** `git ls-files` ki
ginti bhi ek measurement hai, aur wo bhi `Write-Host` pe mar sakti hai.

### C7 — Do cheez jo aaj quote nahi honi chahiye

| Check | Kyun |
|---|---|
| `3.44 s` ya `7.9 s` recovery bound ki tarah kahin nahi | dono process-launch latency hain. Din 1 aur Din 2 dono pe ye rok lagi hai |
| `35.191 s` `fault_to_reclaim` ke naam se nahi | wo **lease-anchor to reclaim** hai. `P-53` ne dikhaya ki fault ka timestamp kisi file me nahi hai, to *fault* to reclaim derivable **nahi** hai |
| `poll_failures` ke `pre_ping` arms | `5` vs `5` sahi hai **`[MEASURED-R]`**, par wo reviewer ke run se hai, harness ke `print` se nahi |

---

## PART D — Scope guard

Aaj ye **nahi** banega. Har ek ka owner naam se:

| Kya | Owner | Kyun aaj nahi |
|---|---|---|
| `P-51` ka **code** fix | Step 5 me naam se chuna gaya din | Aaj faisla hai. Schema wala option `alembic heads` gate se blocked hai |
| Koi bhi `src/` edit | **Din 4 ke baad** | Aaj ka `C5` gate hi yahi hai. `src/` chhua to gate decorative ho gaya |
| Din 5 ke chaar khoye hue measurements | **Din 4** | Wo aaj ke retention rule pe depend karte hain — ulta order ka matlab hai Din 4 ke numbers bhi kal `[REPORTED, NOT VERIFIABLE]` ban jaayein |
| `/slow-hold` ka faisla | **Din 4, Step 5** | Uska fix Din 4 ke Step 2 ki measurement ko weak karta hai |
| `pg_dump` / evidence backup | **Din 4 ya Din 5 ka khaali slot** | Aaj ka sawaal *"evidence public hoti hai"* hai. Backup *"evidence survive karti hai"* hai — related, alag field. Aaj dono karna Step 2 ko `35 min` bana deta hai |
| `logs/` ki purani files delete karna | **Din 6 ke baad** | Aaj rule banti hai. Rule banne ke din usko apply karna wo hi galti hai jo `P-50` describe karta hai |
| History rewrite (`filter-repo`, force push) | **kabhi nahi, bina explicit faisle ke** | `Q3` ka doosra half. Aaj ke scope me ek bhi cheez isko zaroori nahi banati |
| `D-30` ka close, `D-32`/`D-33` ka final text | **Din 6** | Aaj notes aur draft banti hain. Entry Din 6 pe close hoti hai |
| README rows 7/9, promise #4 ka verdict | **Din 6** | Din 2 ke baad row 9 ka verdict badal sakta hai — likhna Din 6 ka kaam hai |
| `P-36` (`os._exit` boundary se nikal jaata hai) | **Month 3** | Aaj ka koi change isko **chhuta nahi**, aur wo likhna zaroori hai |
| Handler timeout | **Month 3** | Ek sawaal pehle chahiye: *timed-out handler ka status kya hai?* |
| Naye tests | **Month 3, Week 6 ke baad** | Week 6 ka fake provider pehli cheez hai jo integration test possible banati hai |
| Koi bhi migration | **iss hafte nahi** | `alembic heads` gate |
| LLM, provider, Redis, rate limit, token, budget | **Weeks 6–8** | [`../../planning/MONTH_02.md`](../../planning/MONTH_02.md) Section 0 |

### Numbering — grep karke confirm karna, likhne se pehle

`2026-09-25` pe grep kiya hua `[MEASURED-R]`: next free decision **`D-32`** (retention/classification ke liye
reserved), uske baad **`D-33`** free hai (`requirements.txt` pins ke liye — ya usko `D-32` me merge kar do, wo
tera call hai aur usko likhna hai). `D-30` abhi **`OPEN`** hai aur Din 6 pe close hoti hai. **`D-09`–`D-20`
Part 2 ne reserve kiye hain.** Next free problem card **`P-54`**.

**Collision do baar ho chuki hai. `Select-String` chalao, phir number do.**

### Budget ki honest arithmetic

Step times ka jod: `10 + 15 + 15 + 20 + 15 + 15 + 15 + 10 = 115 min`. Budget `125`. **Headroom `+10`** —
aur wo deliberate hai, kyunki Step 5 (`P-51`) ek open-ended faisla hai aur wo overrun karega.

**Plan ne Step 5 (`pool_pre_ping`) ko aaj ke opening slot me slip karne ke liye likha tha. Wo Din 2 pe hi
chal gaya (`D-31`, `False`), to wo slot free hai** — aur `P-51`, `P-52`, `P-53` usme aa gaye hain.

**Cut order, naam se:**

1. **Pehla cut — Step 6 (`requirements.txt`) Din 4 ke opening me slip hota hai.** Wo kisi aur step ka
   precondition nahi hai
2. **Step 5 (`P-51`) cut NAHI hota.** Wo aaj ki list ka sabse mehenga item hai aur roz ek healthy job ke
   dead-letter hone ka raasta khula rehta hai
3. **Step 3 cut NAHI hota.** Aaj ke `C1` ka poora matlab wahi hai
4. Agar phir bhi overflow hai: Step 4 ka **teesra** hissa (probe rule likhna) slip karo, par `P-52` ka
   annotate/delete **aaj** hona hai — wo ek din aur zinda raha to agla din usko quote karega

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  PART B — PREDICTION QUESTIONS                                               ║
║  Ye block Gemini ko paste NAHI hota.                                         ║
║  Jawab apne head se, us step se PEHLE,                                       ║
║  docs/daily/week_05/DIN_03_PREDICTIONS_FROZEN.md me. Phir hash lo.           ║
║  `idk` ek valid jawab hai, 0 score karta hai, aur wo accurate hai.           ║
║  Din 2 pe seal ne kaam kiya aur wo din ka sabse saaf process win tha.        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Q1 (Step 1 se pehle)
    `git ls-files` ki poori list lo aur usko `git check-ignore --no-index --stdin`
    se guzaro. Kitni tracked files ko ek ignore pattern ALREADY match karta hai —
    ek number likho.
    Aur: wo files kaunsi class ki hain? Unme se ek document NAHI hai aur usko kabhi
    commit nahi hona chahiye tha — kaunsi tarah ki file hogi, aur wo abhi bhi tracked
    kyun hai? Mechanism ek line me.

Q2 (Step 3 se pehle)
    Maano tu `.gitignore` me `**/daily/` rakhta hai aur uske neeche do line add karta
    hai: `!**/daily/**/*BRIEF*` aur `!**/daily/**/*PREDICTIONS_FROZEN*`.
    `git add -A --dry-run` chalane pe `DIN_03_BRIEF.md` us output me aayega ya nahi?
    Haan/nahi, aur mechanism.
    Aur doosra half: agar nahi aayega, to kya do line ka ORDER badalne se aa jaayega?
    Ya koi bhi order kaam nahi karega? Kyun.

Q3 (Step 3 se pehle)
    Maano kisi din ek sealed KEY galti se `git add -f` se add hui aur commit ho gayi.
    Aaj tu `git check-ignore -v docs/daily/week_05/DIN_02_KEY.md` chalata hai (bina
    --no-index). Exit code `0` aayega ya `1`, aur kya wo koi line print karega?
    Aur: uske baad `git rm --cached` + commit karne se us KEY ka CONTENT repository se
    chala jaata hai, ya nahi? Ek shabd, aur mechanism.

Q4 (Step 4 se pehle)
    Din 1 ne apna exception probe `labs/w5d1_exc_probe.py` me rakha. Din 2 ne apne
    paanch harness `scratch/` me rakhe. Ek hi hafta, ek hi repo.
    Dono me se kaunsa git me hai? Aur wo faisla kisne liya — ek line.
    Aur teesra, aur ye wala sabse ulta jawab de sakta hai: `scratch/step6_harness.ps1`
    — wahi harness jisko `P-50` Din 1 ki evidence maarne ka zimmedaar batata hai — kya
    wo AAJ repository se padhi ja sakti hai? Haan/nahi, aur kahan se.

Q5 (Step 6 se pehle)
    `requirements.txt` me gyarah declared deps hain.
    `pip freeze` kitni line degi — ek number.
    `pip list --not-required --format=freeze` kitni line degi — ek number.
    Aur asli sawaal: doosri list wale gyarah, kya WAHI gyarah hain jo requirements.txt
    me hain? Agar nahi, to kaunsi missing hain aur kaunsi extra hai — aur missing wali
    ka MECHANISM kya hai (wo install hi hain, to list me kyun nahi aayi)?
```

---

*Aaj ke measurement ke **baad** kholna:* [`DIN_03_KEY.md`](DIN_03_KEY.md)
*Kal ka log:* [`../../logs/WEEK_05.md`](../../logs/WEEK_05.md) ·
*Plan:* [`../../planning/WEEK_05.md`](../../planning/WEEK_05.md) ·
*Pointer:* [`../../roadmap/CURRENT_WEEK.md`](../../roadmap/CURRENT_WEEK.md)
