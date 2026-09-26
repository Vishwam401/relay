# DIN 1 BRIEF — Side effect pehli baar exist karta hai, aur wo do baar hota hai

**Week 3 · Din 1** · Plan: [`../../planning/WEEK_03.md`](../../planning/WEEK_03.md) (DIN 1 section) ·
Log: [`../../logs/WEEK_03.md`](../../logs/WEEK_03.md) · Sealed: [`DIN_01_KEY.md`](DIN_01_KEY.md)

**Budget:** plan says **~2h15m**. Iss BRIEF me Step 0 (bench) aur Step 7 (carried-debt run) bhi hai.
Honest number: **~2h30m**.

> **Paste rule.** Parts A, C, D Gemini ko jaate hain. **Part B never travels. The KEY never travels.**
> Part B `docs/planning/WEEK_03.md` ke `PART B` block, `## Din 1` subsection me hai — **chhe** sawaal.
>
> **Seal rule.** Ek step ka KEY section uss step ka **output aane ke baad** khulta hai. Prediction likhne
> ke baad nahi.
>
> **Aaj se ek naya process rule, aur wo measured reason se aaya hai:**
> `docs/daily/week_03/DIN_01_ANSWERS.md` **Step 0 se PEHLE** banti hai, chhe headings ke saath, aur har
> answer **uss step se pehle** save hota hai. Week 2 me chhe din me se **ek** din answers pehle likhe gaye
> (Din 3) aur wahi ek din `5/6` aaya. Din 5 pe file thi par uska mtime saare measurements ke baad ka tha.
> Din 1/2/4/6 pe file hi nahi thi. **File ka mtime khud ek measurement hai.**

---

## Aaj kya alag hai, aur wo poore hafte ka framing hai

Week 2 ne prove kiya ki **duplicate execution asli hai** — job 95, do worker, overlap `14.783 s`
`[MEASURED-R]`. Aur phir bhi: **iss project me aaj tak kisi side effect ko nuksaan nahi hua**, kyunki
teeno handler — `sleep`, `boom`, `slow` — **time ke pure functions** hain. Unko do baar chalao, database
me ek `job_executions` row extra aati hai aur duniya me kuch nahi badalta.

**To contract #2 aaj tak *unprotected* nahi tha. Wo *untestable* tha.** Aur ye do bilkul alag problems
hain: unprotected ka fix ek mechanism hai, untestable ka fix ek **instrument** hai.

Aaj instrument banta hai. Ye iss project ka established pattern hai aur wo `D-21` me likha hua hai —
`job_executions` Week 1 Din 4 me isliye bani thi ki duplicate *dikh* sake, aur uske bina Week 2 ka
`14.783 s` kabhi prove nahi hota.

**Aaj protection NAHI banti.** Aaj `UNIQUE` nahi lagti, dedup nahi lagti, `try/except` nahi lagta. Aaj ka
poora output ek number hai, aur wo number `2` hona chahiye.

---

## Prereq — teen cheezein, aur do carried debts

| Kya | Kaise check hota hai | Kyu aaj |
|---|---|---|
| **Week 2 ka handoff padha hua** — teesri heading, `What Week 3 Must Not Assume` | [`../WEEK_02_HANDOFF.md`](../WEEK_02_HANDOFF.md), chhe items | Wo aaj ke Step 1 ka **input** hai. Aaj ka problem statement wahan se derive hota hai, plan se nahi |
| **Paanch written Week 2 answers** — 🔴 **dasva carry, aur ye Step 0 se pehle hai** | `LEARNING_LOG.md` me `slipped` labelled | Chaar me se chaar sawaal ab **measured** hain, to likhna ab derivation se zyada recall hai — aur wahi slip ki keemat hai. **Gyaarva slip hua to item delete ho jaata hai**, aur wo bhi ek honest ending hai |
| **`DDIA_CH8_LINKS.md` lines 10–13** — reviewer-written, paanch din unconfirmed | File kholke padho | Ch 11 ki pehli line likhne se pehle. Warna Ch 11 bhi wahi shape le lega |

---

# PART A — STEPS

---

## Step 0 — Opening bench (10 min) · executable

**Pehle bench, phir kuch bhi.** Aur teesra check aaj **chalta hai aur log me jaata hai** — Week 2 me wo do
baar BRIEF me aaya aur ek baar bhi report nahi hua.

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId, ParentProcessId, CommandLine
```

```sql
select pid, application_name, state, backend_start, xact_start
  from pg_stat_activity where datname = 'relay' order by backend_start;

select status, count(*) from jobs group by status order by status;
select count(*) as total, max(id) as maxid from jobs;
select last_value from jobs_id_seq;
select count(*) from job_executions;
select attempts, count(*) from jobs group by attempts order by attempts;
select version_num from alembic_version;
```

**Expected, Week 2 ke close se `[MEASURED 2026-08-29]`:**

```
89 succeeded / 15 failed / 3 dead_letter / 0 pending / 0 running     total 107
max(id) 108 · jobs_id_seq 108 · job_executions 94
attempts:  0|95 · 1|3 · 3|8 · 4|1
alembic_version = 682e01d87be9 · python.exe = 0 · idle in transaction = 0
```

Kuch aur aaya to wo **`E2`** hai aur Step 1 tab tak rukta hai jab tak divergence ka **naam wala cause** na
mile.

**Do cheezein iss output me jo aaj ke liye load-bearing hain:**

1. **`pending = 0` aur `running = 0`.** Queue khaali hai. Aaj ka pehla worker koi purani row nahi
   uthayega — aur ye Week 2 me teen baar galat gaya tha (`P-13`).
2. **`max(id) = 108`.** Aaj ki nayi rows `109` se shuru hongi. Ye number closing reconciliation ke liye
   chahiye, aur `max(id)` se chain **kabhi** nahi jodi jaati (`P-05`) — ye sirf "aaj ki rows kahan se
   shuru hui" ka marker hai.

> **Terms used in this step**
> - **`backend_start` vs `xact_start`** — connection kab khuli, versus uski current transaction kab khuli.
>   `xact_start` `NULL` = connected, transaction me nahi, koi lock nahi.
> - **`E2`** — is project ka naam uss situation ke liye jab din ka opening bench expected state se match na
>   kare. Rule: aage badhne se pehle cause ka naam.

---

## Step 1 — Problem statement, apne shabdon me (30 min) · output ek file hai

**Ye aaj ka pehla asli kaam hai aur iska output `docs/daily/week_03/DIN_01_PROBLEM.md` hai.** Chaar
paragraph. Iska scoring nahi hota; iska point ye hai ki hafte ka baaki kaam **iske against** padha ja sake.

1. **Week 2 ne kya prove kiya — ek line, number ke saath.** Aur wo line *"reaper narrow karta hai"* **nahi**
   hai. Wo line ye hai: *do worker ek job pe kitni der overlap kiye, aur uske baad kis writer ne kya likha.*
2. **Side effect ka koi record nahi hai. To *"exactly once"* ko aaj kaise falsify kiya ja sakta hai?** Ek
   observable likho jo `2` de sake. Agar wo observable exist nahi karta, to claim **testable nahi** hai.
3. **Sabse chhoti cheez jo add karni padegi** taki (2) ka observable exist kare — aur **wo addition kaunsa
   naya failure mode laati hai?** (Week 2 Din 1 me yahi sawaal lease column ke liye tha, aur uska jawab
   `P-19` ban gaya. Aaj ka jawab bhi ek `P-` ban sakta hai.)
4. **`Interim_Guarantee`** — aaj ke baad Relay kya promise karti hai? *"Side effect ek baar hoga"* **nahi**.
   Aaj ke baad promise sirf ye hai: *"side effect count ab observable hai."* Wo difference ek line me likho.

**Ye Gemini se nahi poochha jaata** — ye Part B nahi hai, ye tumhara likha hua output hai. Par agar kisi
term ka matlab nahi pata (*idempotent*, *at-least-once*, *outbox*), wo poochhna **allowed** hai: wo
vocabulary hai, outcome nahi.

> **Terms used in this step**
> - **Side effect** — handler ka wo asar jo Relay ke `jobs`/`job_executions` ke bahar hai: ek row kisi
>   doosri table me, ek email, ek HTTP call, ek charge. *"Handler chala"* aur *"side effect hua"* do alag
>   facts hain.
> - **Observable** — koi bhi cheez jise tum baad me padh sakte ho aur wo bata de ki kya hua. `print` ek
>   kamzor observable hai (process ke saath mar jaata hai); ek committed row ek strong observable hai.
> - **Falsify** — ek claim ko *galat* saabit karne ka rasta. Agar koi rasta hi nahi hai, claim se kuch
>   seekha nahi ja sakta.
> - **`Interim_Guarantee`** — iss project ka naam uss line ke liye jo har din ke baad likhi jaati hai:
>   *aaj ke baad system kya promise karta hai, aur kya nahi*.

---

## Step 2 — Side-effect store: ek faisla, phir ek migration (25 min) · executable

**Do shapes hain. Faisla tumhara, aur uski cost aaj likhni hai.**

| Shape | Kaisa dikhta hai | Kya deta hai | Kya nahi deta |
|---|---|---|---|
| **Counter** | ek row per job, ek `integer` jo `UPDATE` se badhta hai | `2` seedha dikhta hai, chhoti table | *kaun* aur *kab* — `UPDATE` pichhla writer mita deta hai |
| **Ledger** | ek row per side effect, append-only, apne `worker_id` / `created_at` ke saath | poori timeline, aur `count(*)` phir bhi `2` deta hai | zyada rows, aur `count(*)` ka matlab baad me badal sakta hai (`P-11` ka shape) |

**Ek precedent, aur wo ek reason nahi hai:** `D-21` me Week 1 me counter option **reject** hua tha, iss
argument pe ki *"`UPDATE` evidence mita deta hai aur ye nahi bata sakta ki kaun aur kab"*. **Wahi argument
aaj lagu hota hai ya nahi — ye tumhara faisla hai.** *"Pichhli baar aisa kiya tha"* precedent hai, reason
nahi. Aur ek naya factor bhi hai: `job_executions` ka `count(*)` ab **paanch** cheezein matlab rakhta hai
(`D-21` amendment), aur wo ek warning hai ki `count(*)` ko meaning ki tarah use karna kitni jaldi bigadta
hai.

**Build:**
1. Migration — `upgrade()` **aur** `downgrade()`, dono chalayi hui. (`--autogenerate` chalane se pehle
   `models.py` save karo. Week 2 Din 1 me ulta hua tha aur ek **permanently khaali revision** chain me
   baith gayi jo aaj bhi wahan hai.)
2. **Aaj `UNIQUE` NAHI lagti.** Wo Din 2 hai. Aaj lagi to aaj ka `2` kabhi nahi aayega.
3. **Koi FK bhi nahi** — `D-21` ki teen branches abhi bhi unattractive hain aur retention policy Week 4 hai.
   Isko *deferred* likho, *bhoola hua* nahi.

**Step ka executable end:** migration up, `\d <table>` me table dikhi, `downgrade` chala, table gayi,
`upgrade` dobara. Dono outputs log me.

> **Terms used in this step**
> - **Append-only** — sirf `INSERT`, kabhi `UPDATE`/`DELETE` nahi. Isse purana record naye se mit nahi
>   sakta.
> - **Autogenerate** — Alembic ka `models.py` (disk pe) aur database ka diff nikalna. Wo **file** dekhta
>   hai, tumhara editor buffer nahi.

---

## Step 3 — Ek handler jo asli side effect karta hai (20 min) · executable

`REGISTRY` me ek naya entry. Teen property chahiye aur teesri sabse aasaani se chhoot jaati hai:

1. **Effect database me observable ho** — Step 2 wali table me ek row / ek increment.
2. **Duration `payload` se aaye**, exactly jaise `handle_slow` `payload.get("seconds", 8.0)` padhta hai.
   **Naya named handler har duration ke liye NAHI.** `P-23` ka poora sabaq: Week 2 ka centrepiece
   `super_slow` pe chala aur wo **kisi commit me nahi hai** — `git log --all -S"super_slow"` khaali hai —
   to wo run ab dobara nahi hota.
3. **Side effect handler ke *andar* likha jaaye, uske baad nahi.** Agar tum effect ko mark ke saath likhoge,
   to aaj ka duplicate **dikhega hi nahi** — kyunki doosre worker ka mark `rowcount = 0` pe reject ho sakta
   hai aur effect uske saath rollback ho jaayega. **Wo Din 3 ka subject hai; aaj usko produce nahi karna.**

**Step ka executable end:** ek job enqueue karo (`payload {}`), worker chalao, `psql` me row dekho, worker
band karo. **Ek** dispatch, **ek** effect. Ye aaj ka baseline hai.

> **Terms used in this step**
> - **`REGISTRY`** — `worker.py` ka `dict` jo `type` string ko handler function pe map karta hai. Agar
>   `type` isme nahi hai, worker row ko `failed` mark karta hai aur **koi** execution row nahi likhta
>   (`P-11`).
> - **Handler** — ek `async` function jo `payload` leta hai. Relay usko bound **nahi** karta — na time se,
>   na resource se (`P-15`).

---

## Step 4 — Duplicate deliberately produce karo (30 min) · executable · **aaj ka centrepiece**

**"Deliberately" ka matlab do worker hai, ek nahi.** Ek worker do baar dispatch kare — wo job `44` ka shape
hai (`6m54s` apart, same `worker_id`) aur wo **overlap nahi** hai.

**Setup — ye already measured hai aur isliye naam se diya ja raha hai** (Week 2 Din 3 me isne kaam kiya):

| Dial | Value | Kyu |
|---|---|---|
| Handler duration | **`45 s`** — `payload {"seconds": 45}` | Lease `30 s` hai. Handler **lease se lamba** hona chahiye, warna expiry hi nahi hogi |
| Lease | `30 s` — **badalna nahi** | Week 2 ne `30 s` jaan-boojh ke intact rakha tha taki evidence `30 s` ke **baare me** bane (`D-22` Cost 2) |
| Poll interval / backoff | **badalna nahi** | Iss hafte ki comparability Week 2 ke numbers pe khadi hai |
| Heartbeat | **niche wala fault model dekho** — ya temporarily off, ya handler ko yield na karne do | `10 s` ka repeating heartbeat lease ko fresh rakhta hai, to bina iske faisle ke duplicate **banega hi nahi** |
| Workers | **do**, ek command se nahi — do alag terminal, aur dono ka start time note karo | `P-12`: Week 1 me do "concurrent" worker `+10.1 s` aur `+24.3 s` late start hue the, aur splits start-time artifacts nikle |
| Reaper | **ek, live** | Uske bina lease expire hone se kuch nahi hota — reclaim reaper karta hai |

**Aur heartbeat ke baare me ek baat jo aaj chubh sakti hai:** heartbeat har `10 s` pe `claimed_at` aage
badhata hai, aur wo **lease ko expire hone se rok sakta hai** — Week 2 Din 3 ke Run 2 me exactly wahi hua
(job 96, `claimed_at` dispatch se `40.295 s` aage, zero duplicate). **Handler `asyncio.sleep` pe yield karta
hai, to heartbeat chalega.**

**To Step 4 shuru karne se PEHLE ek fault model chuno — aur sirf do valid hain:**

| Fault model | Kya karna hai | Kya likhna hai |
|---|---|---|
| **(a) Heartbeat temporarily off** | `send_heartbeat` ka `UPDATE` comment out / ek env flag se skip. `src/` ka **temporary** change | Ki heartbeat band tha, **aur** experiment ke baad revert (`git diff` khali) |
| **(b) Non-yielding handler** | Handler `asyncio.sleep` ke bajaye **block** kare (`time.sleep` jaisa). Event loop yield hi nahi hoga, to heartbeat task chalne ka mauka nahi paayega | Ki duplicate ka cause **event-loop starvation** tha, generic slow handler nahi. Ye do alag failure modes hain aur unko ek likhna galat hoga |

> **Aur wo teesra "option" jo dimaag me aata hai — *handler ko lease + heartbeat dono se lamba kar do* — wo
> arithmetic se kaam nahi karta, isliye usko yahan se hata diya gaya hai.** Heartbeat **repeat** hota hai:
> har `10 s` pe `claimed_at = now()`. Yielding handler `45 s` ka ho ya `45 min` ka, `claimed_at < now() -
> interval '30 seconds'` **kabhi** sach nahi hoga. Duration badhane se sirf heartbeat ki ginti badhti hai.
> Week 2 Din 3 Run 2 isi ka record hai (job 96, `claimed_at` `40.295 s` aage, zero duplicate).

**Jo chuno wo log me `duplicate kaise bana` ke cause ki tarah likhna hai** — kyunki Din 2 ka run *bilkul
wahi* setup dobara chalata hai, aur agar fault model badal gaya to Din 1 vs Din 2 ka comparison kisi cheez
ka nahi rahega.

**Step ka executable end aur aaj ka asli output:**

```sql
select job_id, worker_id, executed_at from job_executions where job_id = <id> order by executed_at;
select count(*) from <side_effect_table> where job_id = <id>;   -- ya counter ki value
```

**Prediction Part B me pehle likhi hui honi chahiye** (sawaal 3 aur 4).

**Aur stdout capture DELETE karne se pehle uski relevant lines log me copy hoti hain.** Week 2 me paanch
din capture pehle delete hui, aur ek din usne ek measurement kha liya.

> **Terms used in this step**
> - **Lease** — ek deadline jo claim ke waqt `claimed_at` me likhi jaati hai. Reaper uska expiry SQL me
>   evaluate karta hai: `claimed_at < now() - interval '30 seconds'`.
> - **Reclaim** — reaper ka `running → pending` `UPDATE`, apne compare-and-set guard ke saath.
> - **Heartbeat** — worker ka `UPDATE` jo har `10 s` pe `claimed_at = now()` likhta hai, `WHERE id AND
>   status = 'running'` guard ke saath. Sirf tab chalta hai jab handler event loop ko yield kare.
> - **Overlap** — do handler intervals ka wo hissa jo ek hi waqt me chal raha tha. Ek **interval** chahiye,
>   ek instant nahi — aur `job_executions.executed_at` sirf **dispatch** ka instant deta hai.

---

## Step 5 — Overlap prove karo, maano nahi (15 min)

**`job_executions` ke do rows duplicate *dispatch* prove karte hain. Overlap wo prove nahi karte.**
`executed_at` dispatch ka instant hai, `record_execution()` handler body se **pehle** apni transaction me
commit karta hai. Interval ka doosra sira sirf **stdout** me hai — aur wahi cheez Week 2 me do baar mehngi
padi (`D-22` Cost 10 me priced).

**To aaj do endpoints chahiye, aur unko *ek clock* me rakhna hai:**

- Handler apne start aur end print karta hai (worker stdout, **local IST**).
- `executed_at` aur `claimed_at` database me hain (**`Etc/UTC`**).
- **Clock offset `[MEASURED]` `+5:30:00` hai** (Week 2 Din 2, `~5 ms` ke andar) — par preferred derivation
  wo hai jisme **ek bhi conversion na ho**: dono dispatch ke `executed_at` ka gap, handler duration ke
  against. Week 2 me dono raste `2 ms` ke andar mile the.

**Likho:** overlap seconds me, aur **kaunsi derivation use ki**.

> **Terms used in this step**
> - **`record_execution()`** — `worker.py` ka function jo `job_executions` me ek row daalta hai, **apni
>   alag transaction** me, handler chalne se pehle. `D-21` isko *"evidence ko uski subject ke saath nahi
>   marna chahiye"* se justify karta hai.

---

## Step 6 — Closing reconciliation (10 min) · executable

**Chain `created_at` / `executed_at` ke `group by` se banti hai, gin-ti se nahi.** Ye Week 2 Din 6 ka naya
rule hai kyunki wahan report-based chain me **do compensating errors** the (Din 3 aur Din 4 ek-ek row se
galat, opposite direction me, total sahi).

```sql
select created_at::date, count(*) from jobs where id > 108 group by 1 order by 1;
select executed_at::date, count(*) from job_executions group by 1 order by 1;
select status, count(*) from jobs group by status order by status;
select count(*) as total, max(id) as maxid from jobs;
select last_value from jobs_id_seq;
```

| Line | Kahan se |
|---|---|
| opening counts | BENCH block: `89 / 15 / 3 / 0 / 0` = `107`, `job_executions 94` |
| `+` aaj ki nayi rows, **ids naam se** | aaj ke `psql` output se, `id > 108` |
| `±` bucket shifts | koi row `pending → succeeded` etc gayi? |
| `=` closing | arithmetic |
| aaj ka `psql` | paanchon bucket + total |
| `job_executions` delta | **aur wo `jobs` delta se BADA hoga** — duplicate ki wajah se. Wo excess **naam se** likho |

**Aaj ka delta `jobs` se zyada `job_executions` me hoga**, aur wahi aaj ka poora point hai. Week 2 Din 3 me
excess `+4` tha aur wo naam se likha gaya tha.

**Cleanup:** worker aur reaper band, `Get-Process python` khaali, `idle in transaction` `0`, teesra check
(`backend_start`) chala. **Probe rows delete NAHI hoti** — unke ids delta me count hote hain (`P-05`). Agar
heartbeat ya kuch aur `src/` me temporarily badla, **wo revert hua aur wo log me likha hua**.

---

## Step 7 — Carried debt: ek run jo `D-22` ka hole band kar sakta hai (10 min) · optional par sasta

**Aaj ka Step 4 setup `D-22` ke `Revisit when` wale run se bahut milta hai**, aur wo run do hafte se owed
hai:

> ek `slow` job with `payload {"seconds": 45}`, `SIGBREAK` at `T = 3 s`, worker aur reaper dono live,
> worker stdout captured aur **delete se pehle log me copy**.

Wo band karta hai: `D-22` **Cost 8** (shutdown-versus-lease, abhi `[INFERRED]` — Din 5 ka run handler `8 s`
< lease `30 s` pe chala tha, to wo apna subject test hi nahi kar paaya), `P-21` ka untested half, aur `P-25`
ka rejection on the terminal write.

**Ye aaj optional hai** aur agar chalao to **Step 4 ke BAAD** chalao, alag job pe, aur uska apna delta
likho. **Agar na chalao, to ye line log me jaati hai:** *"chala nahi, owner: <naam wala slot>"* — kyunki
*carried without an owner* aur *forgotten* ek jaise padhe jaate hain.

---

# PART C — VERIFICATION

**Har check differential hai. Jo check fail nahi ho sakti wo check nahi hai (`P-18`).** Har row ke dono
right-hand columns padho aur confirm karo ki wo **alag** hain.

| Check | Command / action | Mechanism maujood | Mechanism ghayab |
|---|---|---|---|
| Bench chain se pehle liya gaya | Log me Step 0 ka output Step 6 ke **upar** | Saat query outputs, phir chain | Chain pehle, phir bench jo usse agree karta hai. Baad me dono ek jaise dikhte hain — **order hi ek evidence hai** |
| Migration dono direction chalti hai | `alembic upgrade head` → `\d <table>` → `downgrade -1` → `\d <table>` → `upgrade head` | Table dikhi, gayi, wapas aayi — teen outputs | Sirf `upgrade` chala. Aur yaad rakho: Week 2 Din 1 me ek **khaali** revision ne `upgrade` pe exit `0` diya aur kuch nahi banaya |
| Handler ka effect asli hai | Ek job, `payload {}`, phir side-effect table padho | Ek row/count jo handler ke bina exist nahi karti | Table khaali — aur baaki poora hafta ek **no-op** ko protect karta rahega |
| Duration `payload` se aati hai | Do jobs: `{}` aur `{"seconds": 45}`; phir `git log --all -S"<handler name>"` | Elapsed **alag**, aur handler naam **ek hi** baar | Do alag handler names → `P-23` dobara, aur agla hafta ye run reproduce nahi kar payega |
| **Duplicate execution ACTUALLY hui** | `select job_id, worker_id, executed_at from job_executions where job_id = <id> order by executed_at;` | **Do rows, do ALAG `worker_id`**, aur unka gap handler duration se **chhota** | Do rows **ek hi** `worker_id` se → sequential re-dispatch (job `44` ka shape), overlap nahi. **Ya** ek row → duplicate hua hi nahi, aur aaj ka side effect count kisi cheez ka evidence nahi |
| Do worker **actually** compete kar rahe the | Dono ka start time, aur dono ke `executed_at` | Dono worker ka overlap window naam se likha hua | *"do worker chalaye"* → `P-12`: Week 1 me wo `+10.1 s` / `+24.3 s` late the aur ek run me effectively ek hi worker tha |
| Overlap **prove** hua | Step 5 ki derivation, ek clock me | Ek interval jo doosre dispatch ko **contain** karta hai, seconds me, aur derivation ka naam | *"lagta hai overlap hua"* — `P-12` ka exact shape |
| Side effect count | `select count(*) ... where job_id = <id>` | Number, aur uske **saath** Part B ka pehle likha hua prediction | Number pehle padha, prediction baad me likha → `E8`, wo step *reconstruction* score karta hai |
| Heartbeat ka asar likha hua | `select claimed_at, (select executed_at from job_executions where job_id=<id> order by executed_at limit 1) from jobs where id=<id>;` | `claimed_at` dispatch se `~10 s` ke multiples aage → heartbeat fire hua. Ya `~25 ms` aage → nahi hua. **Dono cases likhe jaate hain** | Heartbeat ka zikr nahi — aur agar usne lease bacha li, to *"duplicate nahi hua"* ka cause galat likha jaayega (Week 2 Din 3 Run 2 exactly ye tha) |
| Capture pehle copy, phir delete | Log me handler ke start/end lines aur mark lines | Lines log me, phir file deleted, aur *"deleted"* likha hua | File pehle delete → Week 2 me paanch din, aur ek din ek measurement gayi |
| `src/` ka temporary change reverted | `git status` ; `git diff` | `src/` clean, ya changed hai to **jaan-boojh ke** aur committed | Heartbeat band kar diya aur wo waise hi reh gaya → agle din ka behaviour chup-chaap alag |
| Answers file prediction hai, reconstruction nahi | `Get-ChildItem docs\daily\week_03\DIN_01_ANSWERS.md \| Select LastWriteTime` — aur usko Step 4 ke output ke waqt ke against rakho | mtime Step 4 se **pehle** | mtime baad me → `E8`. Week 2 Din 5 exactly ye tha (`15:03` vs `14:27`) |
| Files disk pe hain, editor me nahi | `Select-String` se padho | Filesystem se output | Stage Day pe chaar files `0 B` thi jab editor content dikha raha tha. **`docs/daily/` gitignored hai** — `git status` madad nahi karega |

---

# PART D — SCOPE GUARD

| Tempting | Owner | Aaj karne se kya khota hai |
|---|---|---|
| `UNIQUE` aaj hi laga dena | **Din 2** | Aaj ka poora output ek `2` hai. `UNIQUE` lagi to `2` kabhi nahi aayega, aur baaki hafta ek aise fix ko validate karta rahega jiski **zaroorat prove nahi hui** |
| Lease `5 s` kar dena taki duplicate jaldi mile | **kabhi nahi** | Week 2 ne `30 s` jaan-boojh ke intact rakha tha taki duplicate `30 s` ke **baare me** evidence bane. Badla to `D-22` Cost 2 iss hafte ke against non-comparable |
| Side effect ko mark ke saath ek transaction me likhna | **Din 3** | Wo outbox ka faisla hai aur wo Din 3 ke crash ke **baad** liya jaata hai. Aaj likh diya to Din 3 ka sawaal poochha hi nahi ja sakta |
| Handler me `try/except` daal ke "safe" banana | **kabhi nahi** | Aaj handler ko fail nahi karna hai. Aaj usko **do baar chalana** hai |
| `idempotency_key` bhi aaj hi | **Din 4** | Do dedup layers ek din me → jab count `1` aayega, **kis layer ne** kiya ye pata nahi chalega |
| Fencing token | **Din 5 ka sawaal, Week 4 ka build** | Iss hafte ka point ye hai ki **fencing ke bina** bhi side effect ek baar ho. Token pehle bana to property test mechanism attribute nahi kar payega |
| `attempts < :max` claim gate me (kyunki `P-27` chubh raha hai) | **Week 4, agar kabhi** | Overdraft `D-23` me **accept** kiya hua hai, aur iss hafte ka property test usko **test** karta hai — fix nahi |
| Purani rows (`44`, `63`, `65`, `95`, `75`, `98`–`103`, `104`, `105`, `108`) ko *"saaf"* karna | **kabhi nahi** | Wo paanch causes ka evidence hai (`D-21` amendment). `95` ek hi row hai jahan overlap **prove** hua — wo iss hafte ka historical justification hai |
| `jobs_id_seq` reset karna | **kabhi nahi** | Gap `P-05` ka evidence hai. Reset karna evidence delete karna hai |
| Property test aaj shuru karna | **Din 5** | Aaj property ke paas check karne ko kuch nahi hai — dedup exist hi nahi karti. Green test jo kuch check na kare, wo red test se zyada khatarnak hai |
