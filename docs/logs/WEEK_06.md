# WEEK 6 — Provider ke paise, aur pehle wo log lines jo sach bolein

**Month 2 ka doosra hafta · Layer L2** · Daily log with measurements, prediction scoring, and unresolved items.
Plan: [`../planning/WEEK_06.md`](../planning/WEEK_06.md) · Decisions: [`../DECISIONS.md`](../DECISIONS.md) ·
Problems: [`../PROBLEMS.md`](../PROBLEMS.md)

> **Plan intent rakhta hai; ye file outcome rakhti hai.** Har factual claim ke saath provenance hai:
> `[MEASURED]` user ke retained output se · `[MEASURED-R]` reviewer ke apne run/read se, iss machine pe ·
> `[REPORTED, NOT VERIFIABLE]` number record hua par uska artifact tree me nahi hai (`P-45`) ·
> `[NOT TESTED]` case enumerate hua, kabhi chala nahi · `[INFERRED]` source/mechanism se ·
> `[NO EVIDENCE]` judgement, aur wo label ke saath.
>
> **Ek untagged line `[MEASURED]` padhti hai, aur ye iss file ka sabse mehenga default hai.**
>
> **Week 6 ka ek naya rule:** jo number *paisa* naapta hai (provider calls, tokens, attempts), uska source har baar likha
> jaayega — provider-side counter, Relay ki DB, ya Relay ka log. Teeno alag cheezein ginte hain.

---

## Din 1 — Lifecycle lines ab `COMMIT` ke baad bolti hain, `489 → 13` ek differential ke saath jo fail ho sakta tha; par Part B ke gyarah `idk` me ek bhi *"kya padha"* nahi, aur control run me ek reaper wedge baitha tha jo kisi ne nahi padha (`2026-10-02`)

**Layer L2 · plan date `2026-09-30`, run `2026-10-02` · commit `58071f3` (`12` named files, `0` KEY, `0` ANSWERS).**
`src/` me paanch hafton me pehli edit: sirf `worker.py`, `reaper.py`, `dispatcher.py`, `+36/−17`. Baaki paanch hashes
(`main` `d55e3b8a` · `database` `fc5bde22` · `sink` `fcfc9059` · `models` `04f04f84` · `schemas` `a53e7cc8`) Step 0 =
Step 7 `[MEASURED]`. Evidence DB delta `0` `[MEASURED]`, reviewer ke probes ke baad bhi `[MEASURED-R]`.

**Original goal (BRIEF se):** database khud chune hue `COMMIT` mana kare, log ki outcome lines ko committed transitions
(audit triggers) se compare karo, phir fix ke baad wahi harness — aur dikhao ki *kaunsi ginti badli aur kaunsi nahi*.
Saath me `P-55` ki class, `P-57` ke chaudah seals, `blogprobe`, aur Week 5 ke paanch `💡`.

- **(a) Goal met?** Haan, tested scope ke andar. Control `489` lines vs `13` committed; fixed `13` vs `13`, paancho tags
  pe `fixed_equal=True` aur `committed_ge_1=True` `[MEASURED]`. Reviewer ka independent re-run (`relay_w6d1_review`) bhi
  wahi `[MEASURED-R]`. `P-55`: silent arm `ReadTimeout`, closed arm `ConnectError` `[MEASURED]`. Seals `16/16` restored.
- **(b) Kuch aur seekha?** Haan, teen cheezein jo question me nahi thi: reaper ka ek-transaction pass ek un-committable row
  ke peeche har doosri row ka reclaim rollback karta hai (**`P-58`**, naya card) · dispatcher ki `432` refused attempts
  `432` asli HTTP POST thi (`sink_duplicate=432`) — fix log badalta hai, delivery count nahi · aur seal ka *record*
  (`frozen_hash.txt`) commit ke `21 s` baad dobara likha gaya.

**Grade `7.5/10`.** Build aur measurement ka hissa achha hai — differential ke saath positive controls, tag text
unchanged (grep contract `P-32`), saare checks file me. Neeche khinchne wali cheezein: Part B me `10/10` derivable
sub-parts bina reading ke `idk`; Beat 4 ki explanations zyada tar BRIEF ka framing dohraati hain, mechanism nahi; apne
hi control log me reaper wedge nahi padha; *"eliminated all false positive logs"* aur *"exact 1:1 match with database
reality"* wahan jahan evidence `narrows` kehta hai; `D-32` ka naya sub-bullet `git hash-object` ko invariant bolta hai.

---

### 📊 Measured / Observed

User ke saare `logs/w6d1_*` artifacts reviewer ne padhe. **Reviewer ke apne runs `[MEASURED-R 2026-10-02 19:59–20:09]`**,
`HEAD 58071f3` pe, ek disposable `relay_w6d1_review` pe (dropped) — artifacts `logs/w6d1rv_*` (gitignored, `26` files).
`[R]` = user ne khud nahi chalaya.

#### Seal — hash sahi, record ka ek check fail

| Check | Value | Provenance |
|---|---|---|
| `Get-FileHash` `DIN_01_PREDICTIONS_FROZEN.md` | `0CFE74DD…BA4F3` = recorded | `[MEASURED-R]` |
| `git hash-object` = `git rev-parse HEAD:<path>` | `634f3958…30cd3c` dono | `[MEASURED-R]` |
| bytes · CR · attribute | `1165` · `0` · `text: unset` (`-text`) | `[MEASURED-R]` |
| `logs/w6d1_step0_frozen_hash.txt` | **chaar lines** — do sahi, phir do khaali `git_blob=`; mtime `19:33:25.278`, commit `19:33:04` ke **`21 s` baad** | `[MEASURED-R]` |
| C0 check *"do lines, mtime Step 0d ki pehli file se pehle"* | **fail as written** | `[MEASURED-R]` |
| frozen file ka apna mtime | `18:51:01.342` — `seals_before` (`18:52:34`) aur Step 1 census (`19:04:17`) se pehle | `[MEASURED]` |

**Hash values sahi hain; khaali lines kisi baad ke append ki hain jiska command kuch print nahi kiya `[INFERRED]`.** To
*"predictions experiment se pehle likhi gayi"* ka ek hi witness bacha — frozen file ka apna mtime, jo badla ja sakta
hai, aur blob commit me `19:33:04` pe pahuncha, saare experiments ke baad. **`[INFERRED]` from a mutable timestamp, kisi
third party ka attestation nahi** (`P-47` ka point). Aaj ke case me ye farak nahi daalta (gyarah `idk` the), par
instrument wahi hai jo kal ek asli jawab ko protect karega.

#### Step 0 — seals, attribute, `blogprobe`

| Kya | Result | Provenance |
|---|---|---|
| `seal_audit.ps1` before → after `-Restore` | `16 · 2 · 2 · 0 · 0` → `seals=16 wc_sha_equals_committed=16 hash_object_equals_head=16 restored=14 blocked=0` | `[MEASURED]` |
| restore arms (`w6d1_step0_restore_arms.txt`) | `start` · `checkout` · `restore` — teeno **`w/crlf`**. Plain `checkout`/`restore` ne bytes nahi badle; `seal_audit.ps1:29` pehle delete karta hai, phir checkout — wahi chala | `[MEASURED]` |
| seal audit, review pe (read-only) | `seals=17` `17/17/17 restored=0 blocked=0` — `17` kyunki Din 1 ka seal ab committed hai | `[MEASURED-R]` |
| `.gitattributes` | line 2 `*_PREDICTIONS_FROZEN.md -text` rakha; `D-32` item 1 ke neeche ek sub-bullet | `[MEASURED-R]` diff |
| `blogprobe` | `DROP DATABASE`; `dbs=blogprobe,postgres,relay` → `postgres,relay` | `[MEASURED]` |

**Restore arms ki file Q1(a) ka poora jawab thi** — aur `ANSWERS` Step 0 me uska zikr nahi.

#### Step 1 — census (`labs/w6d1_print_census.py`, AST)

| Kya | Result | Provenance |
|---|---|---|
| `prints_inside_begin_total` | `15` — dispatcher `5` (`60,75,83,89,95`) · reaper `2` (`65,75`) · worker `8` (`60,64,113,209,222,324,328,332`) | `[MEASURED]`, reviewer ne `58071f3^` ke `src/` pe dobara chalaya `[MEASURED-R]` |
| O class | `7`: dispatcher `83` `[dispatch]` · `89` `[dispatch_failed]` · `95` `[dispatch_error]` · reaper `65` `[reclaim]` · worker `64` `Heartbeat sent` · `222` `[claim]` · `332` `[mark]` — saato text se verify | `[MEASURED-R]` |
| `P-56` ke table me nahi the | `worker.py:64` heartbeat, `dispatcher.py:89`, `dispatcher.py:95` | `[MEASURED-R]` |

#### Step 2 — control (`labs/w6d1_commit_refusal.ps1 -Phase control`, `relay_w6d1`)

Premise: chaaron `resolved_db=relay_w6d1`, `src_diff_files_vs_HEAD=0`, hashes `a2ec8e9f/edcde815/dcdb6343` (pre-fix) `[MEASURED]`.

| Tag | lines | committed (audit) | false |
|---|---|---|---|
| claim | `10` | `5` | `5` |
| heartbeat | `2` | `1` | `1` |
| mark | `15` | `4` | `11` |
| reclaim | `29` | `2` | `27` |
| dispatch | `433` | `1` | `432` |
| **total** | **`489`** | **`13`** | **`476`** |

`[MEASURED]`. Arithmetic: `10+2+15+29+433 = 489`, `5+1+4+2+1 = 13`. **`476` false lines for `13` commits, aur unme se `432`
ek hi tag (`dispatch`) ke** — headline number yahi hai; *"~3700 %"* `(489−13)/13 = 3662 %` ka rounding hai.

**Control me jo question nahi tha, aur jo user ke log me hi tha** (reviewer ne control reaper log ko `BEGIN` se group kiya,
`[MEASURED-R]`):

- **Reaper: `29` lines = `15 × [job 4, COMMIT, ERR]` + `6 × [job 1, job 4, COMMIT, ERR]` + `1 × [job 1, job 4, COMMIT]`**
  → `15 + 12 + 2`. `21` errors = `reaper_poll_error=21`, `2` committed. **Job 1 ki apni koi refusal nahi thi** — uska
  reclaim chhe baar rollback hua kyunki job 4 usi transaction me tha (`src/reaper.py:27–79`, ek `begin()` saare
  candidates ke liye). Ek un-committable row us pass ki har reclaim rokti hai, jab tak wo fail hoti rahe
  `[INFERRED from the measured grouping]`. **`P-56` nahi hai. Naya card `P-58`.**
- **Echo `COMMIT` har refused transaction me error se *pehle* aata hai.** `worker_echo_COMMIT=36` control me bhi aur
  fixed me bhi — ye *attempted* COMMITs ginta hai, succeeded nahi `[MEASURED]`.
- **Job 1 ka raasta:** claim committed → mark `11` baar refused (`mark_error_lines=11`) → `mark_abandoned=1` → lease
  expiry → reclaim (job 4 ke peeche blocked) → phase 2 me re-claim → `succeeded|2|2` `[MEASURED]`.
- **`dispatch`: `432` refused + `1` committed, aur har refused attempt ek asli delivery thi** — `sink_duplicate=432` =
  `dispatcher_poll_error=432` `[MEASURED]`. Week 6 ka rule yahan lagta hai: **Relay ke log ne `433` kaha, Relay ki DB ne
  `1`, receiver ne `432` duplicates log kiye** (applied count is run ke liye yahan record nahi). Teen source, teen alag
  cheezein.

#### Steps 3–4 — fix aur differential

| Tag | control lines / committed | fixed lines / committed | `fixed_equal` | `committed_ge_1` |
|---|---|---|---|---|
| claim | `10 / 5` | `5 / 5` | `True` | `True` |
| heartbeat | `2 / 1` | `1 / 1` | `True` | `True` |
| mark | `15 / 4` | `4 / 4` | `True` | `True` |
| reclaim | `29 / 2` | `2 / 2` | `True` | `True` |
| dispatch | `433 / 1` | `1 / 1` | `True` | `True` |

`[MEASURED]` (`logs/w6d1_step4_diff.txt`). Fixed premise: `src_diff_files_vs_HEAD=3`, teeno hashes control se alag. Post-edit
census `prints_inside_begin_total=8`, koi O-class line andar nahi `[MEASURED]`, HEAD pe reviewer ka re-run identical
`[MEASURED-R]`. **Reviewer ka fixed-phase re-run** (`relay_w6d1_review`): `refusal_triggers_left` `5 → 0`, lines
`5/1/4/2/1` = committed `5/1/4/2/1`, `relay_python_after=0` `[MEASURED-R]`. Ab `n = 2` runs.

**Jo fix ke baad bhi nahi badla, aur jo badalna bhi nahi chahiye tha:** `worker_echo_COMMIT` `36 = 36` · final DB state
sab `succeeded` · `dispatcher_poll_error` `432` (control) / `482` (user fixed) / `442` (reviewer fixed) — **ye ginti
loop speed follow karti hai, code correctness nahi, aur runs ke beech comparable nahi** `[MEASURED]` / `[INFERRED]` cause.

#### Step 5 — `P-55` (`logs/w6d1_p55_20261002_192647_405993_census.txt`)

| Arm | window | lines | class | `outbox_attempts` | first line |
|---|---|---|---|---|---|
| silent `127.0.0.1:8099` | `13 s` | `2` | `ReadTimeout` × `2` | `2` | `error=ReadTimeout:  attempts=1` |
| closed `127.0.0.1:8098` | `8 s` | `3` | `ConnectError` × `3` | `3` | `error=ConnectError: All connection attempts failed attempts=1` |

`[MEASURED]`; `relay_python_after=0`. **Double space** = `": "` + khaali `str` + `" attempts"`.

**Mechanism `[MEASURED-R]`** (`logs/w6d1rv_httpx_probe.txt`, httpx `0.28.1`, source read): `httpcore/_backends/anyio.py:33`
read ko `anyio.fail_after()` me wrap karta hai, jo expiry pe bina argument ka builtin `TimeoutError()` raise karta hai
→ `httpcore.ReadTimeout(TimeoutError())` → `httpx/_transports/default.py:117–118` `message = str(exc)` = `''` →
`httpx.ReadTimeout('')`. Probe: `str=''`, `repr=ReadTimeout('')`, elapsed `5.1031` / `5.0149 s`. `ConnectError` anyio ka
`OSError("All connection attempts failed")` le jaata hai, isliye message bachta hai; elapsed `2.0289`–`2.0477 s`.
**Class name ab wo information leti hai jo `str` me kabhi thi hi nahi.**

**`2` vs `3` lines kyun — failure class ka farak nahi, window ka:** dispatcher failure ke baad sleep nahi karta
(`dispatched = True` row milte hi, `src/dispatcher.py:53`; `P-35`), agla `BEGIN` pichhle `COMMIT` ke `4–5 ms` baad. To
lines `≈ floor((window − startup) / per-attempt)`. Silent: `(13 − 1.65) / 5.04 = 2.25 → 2`. Closed: `(8 − 1.75) / 2.05 =
3.05 → 3`, aur teesri line kill se **`~0.1 s`** pehle giri — thoda slow start hota to `2`. Timestamps `[MEASURED]`,
arithmetic `[INFERRED]`. Is Windows host pe closed loopback port ka connect `~2.03 s` leta hai (`D-28` ka `~2.02 s` jaisa),
`5 s` connect timeout ke andar — isliye `ConnectError`, `ConnectTimeout` nahi `[MEASURED-R]`.

#### Step 6 — Week 5 ke paanch `💡`

`own_words_blocks=5 gaps_lines=6 reviewer_blocks_kept=6` `[MEASURED]`. Diff (`58071f3^..58071f3 -- docs/logs/WEEK_05.md`):
**`+5` own-words blocks, `+5` `Gaps` lines, `0` lines removed** `[MEASURED-R]`. `6` me ek line (`1867`, Din 6 ka
pre-existing sentence) pehle se thi — **ye `ANSWERS` Step 6 me khud likha hai**, aur sahi likha hai. Wording ka quality
yahan score nahi hua.

#### Step 7 — close

`relay_w6d1` dropped · `src_diff_files=src/dispatcher.py,src/reaper.py,src/worker.py` · `heads=w4d4_sink_unique (head)` ·
`dbs=postgres,relay` · `relay_python=0` · counters `133|145|19|4|7|39|5|0|1` · protected `108|dead_letter|4|0 ;
128|succeeded|4|4 ; 136|running|1|1` · `key_index=0` · `key_tree=0` · seals `blocked=0` · staged `12`, `0` KEY, `0`
ANSWERS `[MEASURED]`. Reviewer bench pre/post (`logs/w6d1rv_bench_pre.txt`, `_post.txt`): saare fields Step 7 ke barabar
→ **delta `0`** `[MEASURED-R]`.

---

### 🔎 Code audit — `git diff 58071f3^ 58071f3 -- src/` (3 files, `+36/−17`)

Har moved line pe chaar checks: (a) sirf `begin()` ke normal exit (= `COMMIT`) ke baad chalti hai · (b) `COMMIT` raise
kare to nahi chalti · (c) har variable har path pe defined · (d) andar bachi koi B/I line outcome claim nahi karti.

| Moved line (HEAD) | (a) | (b) | (c) | Label |
|---|---|---|---|---|
| `dispatcher.py:100–102` `if post_commit_msg: print(...)` — `[dispatch]` `87–89`, `[dispatch_failed]` `92–94`, `[dispatch_error]` `97–99` | haan; `begin()` ke baad, `async_session()` ke andar | haan → outer `except` `:103` `[poll_error]` | `post_commit_msg = None` `:40` `begin()` se pehle; `row_job_id`, `row_outbox_id`, `new_attempts` `:54–56` | source `[MEASURED-R]` |
| `reaper.py:81–82` `for msg in post_commit_reclaims` | haan | haan → `:100` | list `:26`, dono context managers ke bahar | source `[MEASURED-R]` |
| `worker.py:66–67` heartbeat | haan | haan → `[heartbeat_error]` `:68–70` | `heartbeat_msg = None` `:48`; `rowcount=0` path `begin()` ke andar `break` karta hai, message `None` | source `[MEASURED-R]` |
| `worker.py:229–230` `[claim]` | haan | haan → `[poll_error]` `:233–235` | `claim_msg = None` `:179` | source `[MEASURED-R]` |
| `worker.py:343–344` `[mark]` | haan | haan → `[mark_error]` + retry loop | `mark_msg = None` `:309` | source `[MEASURED-R]` |

**Tag text unchanged** — diff me har `[claim]`/`[mark]`/`[reclaim]`/`[dispatch*]` f-string ka text wahi, sirf `print(` →
`msg = (` `[MEASURED-R]`. Grep contract (`P-32`) bacha. `P-55`: `dispatcher.py:98` `error={type(exc).__name__}: {exc}` —
`src/` ki baaki exception lines pehle se isi shape me thi.

**(b) measure hua, sirf padha nahi:** claim/heartbeat/mark/reclaim/dispatch — user ke fixed run aur reviewer ke re-run me
lines = committed, har ek apni kind ki `≥ 1` refused COMMIT ke against `[MEASURED][R]`.

**Harness ka ek blind spot, aur reviewer ne use alag se bhara.** Dispatch ka refusal arm sirf `dispatched_at IS NOT NULL`
pe fire hota hai — success path. **`[dispatch_error]` refused COMMIT ke neeche user ke harness me kabhi nahi chala.**
Reviewer probe (closed-port sink + deferred trigger jo `attempts + 1` ka commit refuse kare,
`logs/w6d1rv_dErr_20261002_200449_356008_census.txt`):

| Arm | refusal trigger | `[dispatch_error]` lines | `poll_error` *"commit refused"* | `outbox.attempts` |
|---|---|---|---|---|
| R | `1` | **`0`** | `3` | **`0`** |
| P (positive control) | `0` | **`3`** | `0` | **`3`** |

`[MEASURED-R]`. **`[dispatch_failed]` (non-200) refused COMMIT ke neeche: not recorded** — wahi variable, wahi print site,
to `[INFERRED]` same behaviour.

**(d) classification audit.** Andar bachi `8` lines: dispatcher `:64` (`Attempting dispatch`, intent), `:79` (`crash_at`
`os._exit` se pehle); reaper `:77` (`candidates=0`); worker `:61` (`Heartbeat lost`), `:116` (`crash_at`), `:213` (claim
conflict), `:332` (`Mark fenced`), `:336` (`Conflict on mark`). **Koi committed state change claim nahi karti** `[MEASURED-R]`.
`reaper.py:65` `O+B` tha aur poora move hua — to `matched=0` observation ab sirf tab print hota hai jab pass commit ho,
aur COMMIT fail ho to kho jaata hai. Outcome line ke liye ye sahi taraf ki galti hai, par B half ka meaning badla `[INFERRED]`.

**Census ka domain hi jo nahi dekh sakta** — transaction ke *bahar* ki lines jo outcome jaisi padhti hain:
`worker.py:250–252` `Unknown handler … Marking terminal 'dead_letter'` · `:287–289` `failed attempt … Scheduling retry …
(new_status='pending')` · `:294–296` `reached max_attempts … Marking terminal 'dead_letter'`. Teeno mark transaction
**shuru hone se pehle** print hoti hain aur ek aisa status naam leti hain jo agla `[mark]` shayad kabhi commit na kare (job
1: `11` refused marks, phir `mark_abandoned`). Wording irade ki hai, par `new_status='pending'` status grep karne wale ko
result jaisa padhta hai `[MEASURED]` source / `[INFERRED]` reading risk. **Fix ka bug nahi; instrument ka blind spot.**

**Ek added line jo kuch protect nahi karti:** `worker.py:232` `claimed_job = None` claim `except` me. `except` `continue`
(`:237`) pe khatam hota hai aur loop `:176` pe waise bhi `claimed_job = None` karta hai. **Deletion test: line hatao,
behaviour same** — explicitness hai, protection nahi (AGENTS rule 22) `[MEASURED-R]` source.

**Fix kya cover nahi karta — isliye `narrowed`, `closed` nahi** `[INFERRED]`:

1. **Committed par print nahi hua (false negative).** `COMMIT` aur `print` ke beech process death (`os._exit`, SIGKILL,
   power loss) → committed transition, koi line nahi. Control over-count karta tha; fixed under-count kar sakta hai.
   **Aaj ke harness ne ye direction kabhi paida nahi ki** — processes sirf end pe `Stop-Process` se marte hain.
2. **Commit ka outcome pata nahi.** `COMMIT` Postgres tak pahuncha aur commit hua, par ack se pehle connection mara →
   asyncpg raise karta hai → code `[poll_error]`/`[mark_error]` likhta hai ek aise transition ke liye jo commit ho chuka.
   Caller ke paas ye information exist hi nahi karti (AGENTS rule 29). **Line ab commits ka lower bound hai, exact count
   nahi.**
3. **Timestamp ab bhi pichhle moment ka.** `[reclaim]` ka `DB_TIME` `clock_timestamp()` hai, `UPDATE` ke `RETURNING` se
   (`reaper.py:51`) — print COMMIT ke baad hai, time andar ka.
4. **Dispatcher ka HTTP side effect ab bhi COMMIT se pehle** — log honest hua, delivery count nahi badla (`P-35`, Week 7).

---

### 🧠 Prediction review — `0.00 / 5.0`, aur gyarah me se das reading gaps

Frozen text `docs/daily/week_06/DIN_01_PREDICTIONS_FROZEN.md` se **quote**, hash verify hua. Har sub-part ke neeche
sirf BRIEF ka tag copy hua hai (*"Target: `[padh ke: …]`"*) aur *"Jawab: idk"* — **kis file ki kaunsi line padhi, ye ek bhi
sub-part me nahi.** BRIEF ka rule: *"Us sub-part ka `idk` tabhi `idk` hai jab saath me likha ho kya padha; warna wo
reading gap gina jaayega."* Tag ko dohraana *"kya padha"* nahi hai.

| Q | Sub-part · tag | Frozen text (verbatim) | Score | Before measurement | After measurement (`ANSWERS`, Beat 4) |
|---|---|---|---|---|---|
| **Q1** | (a) `[padh ke]` · (b) `[padh ke]` | *"Jawab: idk"* · *"Jawab: idk"* | **`0.00 / 1.0`** | not answered — **reading gap ×2** | Step 0 me *"14 CRLF seals restored to LF"*. `checkout`/`restore` ke no-op ka zikr nahi, jabki apni `restore_arms.txt` me teeno `w/crlf` the. `-text` vs `eol=lf` ka hash mechanism nahi. **Not explained** |
| **Q2** | (a) `[padh ke]` · (b) `[padh ke]` | *"Jawab: idk"* · *"Jawab: idk"* | **`0.00 / 1.0`** | not answered — **reading gap ×2** | `15`, `7` O, `8` B/I sahi likhe, aur heartbeat `64` classified file me O hai. **`P-56` ke table se compare nahi kiya** — kaunse teen table me nahi the, ye kahin nahi. Outcome observed, gap unnamed — **partial** |
| **Q3** | (a) · (b) · (c), teeno `[padh ke]` | *"Jawab: idk"* ×3 | **`0.00 / 1.0`** | not answered — **reading gap ×3** | (a) `mark 15 vs 4` likha, `11 = 10 s deadline / 1 s sleep` nahi. (b) **reaper wedge nahi dekha** — job 1 ka rollback job 4 ke peeche. (c) *"tight loop with no sleep (P-35)"* — mechanism ka aadha; `dispatched = True` POST se pehle, aur ki har line ek asli POST thi, ye nahi. **(c) partial, (a)(b) not explained** |
| **Q4** | (a) · (b), dono `[padh ke]` | *"Jawab: idk"* ×2 | **`0.00 / 1.0`** | not answered — **reading gap ×2** | *"eliminated all false positive logs … exact 1:1 match with database reality"*. Kya **same** raha (`mark_error`, echo `COMMIT`, `sink_duplicate`, `poll_error`) — nahi likha. Nayi direction (committed-not-printed) — nahi likha. **Not explained, aur wording elimination ki** |
| **Q5** | (a) `[padh ke]` · (b) `[chala ke]` | *"Jawab: idk"* · *"Jawab: idk"* | **`0.00 / 1.0`** | (a) not answered — **reading gap**; (b) not answered — **honest `idk`**, yahi experiment ka kaam tha | `str(ReadTimeout)` khaali, class name ab carry karta hai — **sahi**, aur closed port pe *"ConnectError prints class name and OS failure message"* — **sahi** (observed). Par (b) ka pehla half — fix se *pehle* closed-port line khaali hoti ya nahi — seedha nahi likha; `str` khaali *kyun* hai (httpcore ka bare `TimeoutError()`), `5 s` interval aur `2` attempts ka mechanism — nahi. **(b) partial, (a) not explained** |

**Total `0.00 / 5.0`.** Week 6 frozen running total: **`0.00 / 5.0`**. KEY ke scoring note ke mutabik `Q5(b)` ke alawa
**sab run se pehle derivable tha** — `4.5` points padhne se. Ye **lagatar chhatha din** hai jisme ek bhi prediction
attempt nahi hui (Week 5 Din 6 ki entry ne use paanchwa gina tha). **Naya format (`≤ 11` sub-parts, har ek pe tag) ne pehli baar test kiya, aur jo behaviour
wo badalna chahta tha wo nahi badla.**

**Provenance — teen categories, strict:**

| Category | Sub-parts |
|---|---|
| Derived before measurement | **`0`** |
| Explained after measurement, mechanism ke saath | **`0`** |
| Explained after measurement, partial (outcome sahi, mechanism adhoora) | `3` — `Q2(b)`, `Q3(c)`, `Q5(b)` |
| Not explained even after measurement | `8` — `Q1(a)`, `Q1(b)`, `Q2(a)` (count sahi, per-file mechanism nahi), `Q3(a)`, `Q3(b)`, `Q4(a)`, `Q4(b)`, `Q5(a)` |
| Recalled / recognised | **pehchaan nahi ho sakti.** `ANSWERS` ki explanations BRIEF ke phrases dohraati hain (*"Deterministic commit refusal proves P-56"*, *"Option (a)"*, *"rowcount=0 observations"*). Ye understanding hai ya recognition, file se tay nahi hota |
| *"KEY se pehle"* ka order | **not recorded.** `DIN_01_ANSWERS.md` ki ek hi mtime hai, `19:32:43` — Step 7 bench (`19:31:55`) ke baad. Per-step likha gaya ya end pe ek saath, file se verify nahi hota |

**Ek line jo earned hai:** inflation zero. Frozen file me koi confident galat jawab nahi, aur report me koi self-score
claim nahi.

**Beat 4 ka asli hisaab.** `ANSWERS` pehli baar maujood hai — Week 5 me ek bhi nahi thi, to format change ka ye half
chala. Par saat me se paanch explanations *observed* ko dohraati hain aur *kyun* nahi kehti. Sabse mehenga miss Step 2
ka hai: reaper ke `29` lines ka breakdown (`15 + 12 + 2`) user ke apne log me tha, aur `P-58` usi se nikla.

---

### 🤖 Reviewer ki apni galat predictions aur defects — record ke liye

1. **BRIEF ka dispatch refusal arm sirf success path pe fire hota tha.** Teen dispatcher tags me se ek hi harness ke
   differential me tha; `[dispatch_error]` review probe ne bhara, `[dispatch_failed]` abhi bhi unmeasured. Narrow, galat nahi.
2. **BRIEF C3 row 2 ne `committed_ge_1` ko deletion pakadne ka credit diya.** `committed_ge_1` DB se aata hai, log nahi
   padhta — deleted print use dikhta hi nahi. **Deletion `fixed_equal` pakadta hai** (`0 ≠ committed`); `committed_ge_1`
   wo premise hai jo `0 = 0` ko pass hone se rokta hai. **Sirf pair deletion rule out karta hai.**
3. **`worker_echo_COMMIT` as a check decorative tha** (`36 = 36`, attempted commits). KEY ne context me sahi kaha; Part C
   me ise context hi rehna chahiye tha.
4. **C5 ka `5 · 5 · 6` sahi tha, par check ke paas `6` ka matlab batane wala koi column nahi tha** — ek pre-existing line.
   User ne `ANSWERS` me khud pakda.
5. **KEY `Q5(a)` ka *"`13 s` = `~2.6 s` startup + `2 × 5 s`"*** — measured startup `1.65 s`. Line count wahi (`2`), arithmetic galat.
6. **KEY `Q4(a)` ne `dispatcher_poll_error` ko *"same"* likha.** `432 / 482 / 442` — order same, value timing-dependent.
   *"Comparable nahi"* likhna chahiye tha.

**KEY ne jo theek kaha, aur aaj measured:** `Q1(a)` teeno arms (`restore_arms.txt`) · `Q2(a)` `15` aur per-file split ·
`Q2(b)` `7` aur teen naam · `Q3(a)` `11` · `Q3(b)` wedge aur `reclaim_committed` · `Q3(c)` order of magnitude (`433` vs
`423`) · `Q4(a)` paancho `*_lines = committed` · `Q5(a)` `2` · `Q5(b)` `ConnectError: All connection attempts failed`.

---

### 💡 What I understood — own words, 2026-10-03

1. Log line sirf DML intent hoti hai jab tak `COMMIT` safal na ho: Outcome lines ko `session.begin():` ke bahar shift karke uncommitted false positive logs (489 prints vs 13 commits) ko eliminate kiya gaya (`P-56`).
2. Nayi failure window (Narrowed, not eliminated): Commit safal hone ke baad aur print chalne se pehle agar process crash ho jaye to DB me committed transition exist karega par log me line nahi aayegi (false negative).
3. Differential ke do guards: `fixed_equal=True` ke sath `committed_ge_1=True` hona anivarya hai taaki line deletion se aane wali khokhli barabari (`0 = 0`) prevent ho sake.
4. Exception class explicit formatting: `httpx.ReadTimeout` ka `str(exc)` empty hota hai, isliye `{type(exc).__name__}: {exc}` format use karne par hi log me class name `ReadTimeout:` dikhta hai (`P-55`).

Gaps vs reviewer: Reviewer ne note kiya ki transaction ka scope uska blast radius hota hai (reaper ke ek pass me ek refusal sabhi reclaims ko rollback karta hai - P-58), aur ek hi event ke teen alag records hote hain (log, DB, receiver).

### 💡 What the session established — **draft, user ko ye apne shabdon me dobara likhna hai** (Week 6 Din 2, Step 0.5)

> Ye section reviewer ne likha hai. **Ye user ki samajh nahi hai.** Protocol ke hisaab se Din 2 Step 0.5 pe iske upar
> `### 💡 What I understood — own words, <date>` aur ek `Gaps vs reviewer:` line aayegi — bina ye section dobara padhe.

1. **Log line ek irada hai jab tak `COMMIT` wapas na aaye.** Print ko `begin()` ke baad le jaao to jhooti line jaati hai,
   aur ek nayi direction khulti hai: committed transition jiski line nahi. Wo direction recoverable hai kyunki DB query ho
   sakta hai — par log ab bhi DB read nahi hai.
2. **Differential ko do numbers chahiye.** `lines = committed` akela `0 = 0` pe pass hota hai; `committed ≥ 1` akela log
   padhta hi nahi. Pair hi deletion aur *"andar hi raha"* dono ko alag karta hai.
3. **Transaction ka scope uska blast radius hai.** Reaper ka ek pass ek transaction hai, to ek row ki refusal har doosri
   row ka reclaim rollback karti hai (`P-58`).
4. **Ek hi event ke teen record alag ginte hain:** Relay ka log (`433`), Relay ki DB (`1`), receiver (`432` duplicates). Fix ne pehla badla; teesra wahi raha.
5. **Kuch exceptions ka `str` khaali hota hai by construction** — httpcore bare `TimeoutError()` wrap karta hai. Class
   name hi wo information le jaata hai.
6. **Line count ek window aur ek per-attempt cost ka quotient hai** jab loop sleep nahi karta. `2` vs `3` failure class ka
   farak nahi tha.
7. **`git checkout` aur `git restore` stat-clean file ko dobara nahi likhte.** Bytes theek karne ke liye file delete karni
   padi — instrument bytes padhta hai, `git status` nahi.

---

### ⚠️ Closeout corrections

| # | Jaise report / record hua | Jo measured hai | Provenance |
|---|---|---|---|
| 1 | *"~3700% false positive logging"* | `476` false lines / `13` commits = `3662 %` excess; `432` of `476` ek tag (`dispatch`) | `[MEASURED]` arithmetic |
| 2 | *"proving P-56"* (Step 2) | `P-56` Week 5 Din 5 pe measured tha (`n = 1`, sanyog). Aaj **deterministic reproduction**, ek run per phase | `[MEASURED]` |
| 3 | *"eliminated all false positive logs … exact 1:1 match with database reality"* (Step 4) | Paanch tags pe, is harness ke refusals ke neeche, `n = 2` runs (user + `[R]`). `[dispatch_failed]` unmeasured; `[dispatch_error]` sirf reviewer probe `[R]`; committed-not-printed aur commit-outcome-unknown kabhi paida nahi hue → **`narrows`** | `[MEASURED]` / `[INFERRED]` |
| 4 | *"Fixed P-55"* | Relay ka apna symptom self-describing hua. Receiver ka lock (`P-41`) ab bhi line me nahi; `ReadTimeout` ka message khaali hi hai (`error=ReadTimeout:  attempts=1`) → **resolved for the class, `narrows` for diagnosis** | `[MEASURED]` |
| 5 | `D-32` sub-bullet: *"immutable Git blob ID (`git hash-object`) remains canonical and byte-auditable across all clones"* | `git hash-object` working-copy bytes pe chalta hai: `-text` ke neeche CRLF copy pe `81584003…` vs `HEAD` blob `90f6da79…`. Canonical number `git rev-parse HEAD:<path>` hai. Aur `-text` ki latent commit hazard (`P-57` Consequence 2) cost me nahi likhi. Review note `D-32` ke neeche | `[MEASURED-R]` replica (`P-57` amendment) |
| 6 | Step 0: frozen hash *"two lines"* (C0) | Chaar lines, do khaali `git_blob=`, mtime commit ke `21 s` baad. Seal values sahi, record ka check fail | `[MEASURED-R]` |
| 7 | *"Meri explanation (KEY se pehle)"* ×7 | Order not recorded — `ANSWERS` ki ek mtime, `19:32:43`, Step 7 ke baad | `[MEASURED-R]` mtime |
| 8 | `WEEK_05.md` me paanch headings *"own words, 2026-09-30"* | Commit `2026-10-02 19:33`, Step 6 logs `2026-10-02`. Heading plan ki date carry karti hai, likhne ki nahi — **record kis moment ka hai**, Week 5 ka hi sawaal | `[MEASURED]` git log |
| 9 | Step 3 *"If COMMIT fails, exception skips the print statement"* | ✅ sahi, paancho tags pe measured; `[dispatch_error]` pe reviewer probe `[R]` | `[MEASURED][R]` |
| 10 | Step 6 *"gaps_lines=6 because Din 6 line 1867 … already quoted"* | ✅ sahi — diff `+5` | `[MEASURED-R]` |
| 11 | `worker.py:232` `claimed_job = None` | Deletion test: koi behaviour change nahi (`:237` `continue`, `:176` reset) — explicitness, protection nahi | `[MEASURED-R]` source |

---

### 🚧 Unresolved / carried

1. **`P-56` — `narrowed`.** Baaki: committed-not-printed direction (aaj ka harness paida nahi karta) · commit-outcome-unknown
   (line ab lower bound) · `[dispatch_failed]` refused COMMIT ke neeche unmeasured · transaction ke bahar ki teen intent
   lines (`worker.py:250`, `:287`, `:294`) · `[reclaim]` ka `DB_TIME` pre-commit. Owner: **open — koi ek din abhi nahi**;
   committed-not-printed ka test Week 6 Din 5 ke `os._exit` hook (Arm C) ke saath sasta hai, user ka faisla.
2. **`P-58` (naya) — reaper ka ek-transaction pass.** Fix ka owner **user ka faisla**; KEY ka candidate Month 4, `D-20` ke
   reaper coordination ke saath. Aaj ke schema me per-row persistent commit failure ka source (deferred trigger/constraint)
   nahi hai `[INFERRED]`, to severity abhi low hai; mechanism measured.
3. **`P-35`** — dispatcher ne `432` real POSTs refused commits ke peeche bheje. Week 7.
4. **Seal ka record** — `frozen_hash.txt` me khaali lines aur post-commit mtime. Din 2 se seal hash file **ek hi command
   me** likho aur dobara mat chhuo; C0 check Din 2 BRIEF me line count ke saath.
5. **Is entry ka `💡` aur Week 5 Din 6 ka `💡`** — Week 6 Din 2 Step 0.5 (plan me do blocks).
6. **`D-32` review note** — `-text` ka cost (`git hash-object` invariant nahi, latent commit hazard). Pick wahi rahta hai;
   user chahe to `eol=lf` pe switch, warna note hi record.
7. **`P-44`** — Din 2 Step 1.

---

### ❓ Next thought

Aaj log ki ginti database ki ginti ke barabar aayi — par sirf us harness ke andar jo ek hi direction ki galti paida karta
hai. Do directions abhi bhi khuli hain, aur dono me log *kam* bolega: commit hua, line nahi; ya commit hua aur line ne
error kaha.

Din 2 pe Relay ke saamne pehli baar ek aisa process hoga jo **apni** ginti rakhta hai — fake provider ka call counter.
**Jab provider kahe `3` calls aur Relay ki DB kahe `attempts=1`, kaunsa number bill hai — aur Relay ka kaunsa record us
gap ko dekh bhi sakta hai?**

---

*Din 1 BRIEF:* [`../daily/week_06/DIN_01_BRIEF.md`](../daily/week_06/DIN_01_BRIEF.md) ·
*Seal:* [`../daily/week_06/DIN_01_PREDICTIONS_FROZEN.md`](../daily/week_06/DIN_01_PREDICTIONS_FROZEN.md) ·
*Reviewer evidence:* `.agents/tasks/w6d1-review-w6d2-brief/EVIDENCE.md` ·
*Din 2 BRIEF:* [`../daily/week_06/DIN_02_BRIEF.md`](../daily/week_06/DIN_02_BRIEF.md)

---

## Din 2 — `P-44` ka gate register-time pe, ek differential ke saath jo galat gate ko pass nahi hone deta; fake provider ne dikhaya ki `timeout=5.0` ek deadline nahi hai (`trickle` `200` at `8.462 s`) — par Part B phir das me das `idk`, chaar reading gaps, aur close bench ka ek fail check *"all criteria met"* likha gaya (`2026-10-03`)

**Layer L2 · run `2026-10-03 13:24–14:26` · seal commit `d1d0ea9` (`13:37:40`) · feature commit `bb90c15` (`6` named
files, `0` KEY, `0` ANSWERS, `0` FROZEN).** `src/` me do cheezein: `main.py` `+11/−10` (`d55e3b8a → 7241c055`) aur nayi
`fake_provider.py` (`108` lines). Baaki saat hashes (`worker` `0eb94373` · `reaper` `95518640` · `dispatcher`
`920d0d4a` · `database` `fc5bde22` · `sink` `fcfc9059` · `models` `04f04f84` · `schemas` `a53e7cc8`) Step 0 = Step 5
`[MEASURED]`. Evidence DB delta `0` `[MEASURED]`, reviewer ke probes ke baad bhi `133|145|19|4|7|39|5|0|1` `[MEASURED-R]`.

**Original goal (BRIEF se):** `P-44` ka decided shape implement karo — test routes sirf `ENABLE_TEST_ROUTES` on hone pe
*register* hon, `/db-ping` jaaye, flag ki raw value startup pe dikhe — aur ek chhe-arm differential se dikhao ki gate
register-time hai. Phir ek fake provider (deterministic failures, apna ledger, sirf `127.0.0.1`) aur caller ka view
naapo: har mode pe `httpx.AsyncClient(timeout=5.0)` ko status, exception class, elapsed kya dikhta hai, aur kahan provider
ki ginti aur caller ka record alag ho jaate hain. Saath me do `💡` own-words (Week 5 Din 6, Week 6 Din 1).

- **(a) Goal met?** Haan, tested scope ke andar. Gate: fixed census me paanch off arms `slow_hold_get=404
  slow_hold_post=404 openapi_slow_hold=0 db_ping=404 flag_lines=1`, `one` arm `200/405/1`, control me chhe ke chhe arms
  `200/405/1` `[MEASURED]`. Provider: C3 aur C4 ki har row pass `[MEASURED]`. Do `💡` structure check pass `[MEASURED]`.
  **Ek check fail:** C5 `trail_distinct_sha = trail_lines` — `7 ≠ 8` `[MEASURED]`.
- **(b) Kuch aur seekha?** Haan. Provider-side ki teen ginti teen alag sawaalon ka jawab hain — ledger `14`, access log
  `12`, posts `15` — aur dono direction me alag (`malformed` access me hai, ledger me nahi; `slow_above`/`hang` ledger me
  hain, access me nahi) `[MEASURED]`. Review pe: provider ka **unknown mode chupchaap `200 ok`** deta hai (`5OO`, `Hang`,
  `''`, `slow-above` → `200`) aur uski **startup line ek hardcoded literal hai** — port `8099` pe chalaya to bhi
  `listening=127.0.0.1:8002` likha `[MEASURED-R]`. Aur ek multi-hop jo sawaal me nahi tha: Relay ka dispatcher
  `FOR UPDATE SKIP LOCKED` row lock ke andar isi `timeout=5.0` ke saath POST karta hai → **`P-59`** (naya card).

**Grade `7.0/10`.** Build aur measurement ka hissa Din 1 se saaf hai — gate ka differential apna kaam karta hai (POST
column aur `openapi.json` v1 ko v2 se alag karte hain), saare Part C checks file me, provider loopback pe, koi DB import
nahi. Neeche khinchne wali cheezein: Part B `0.00/5.0` aur paanch `[padh ke]` me se chaar me *"kya padha"* nahi — BRIEF ne
ye exact defect naam leke warn kiya tha; Step 5 ki explanation *"All close bench criteria met"* jabki usi bench me
`trail_lines=8 trail_distinct_sha=7` tha; Step 1b ki cost line aur do owed `ANSWERS` lines (pool probe, README) gayab;
Step 4a ki explanation me koi mechanism nahi; provider ki startup line witness nahi, claim hai.

---

### 📊 Measured / Observed

User ke saare `logs/w6d2_*` artifacts reviewer ne padhe (`52` files). **Reviewer ke apne runs `[MEASURED-R 2026-10-03
~14:50]`**, `HEAD bb90c15` pe: gate ke paanch import-time arms (temp script, `src/` ke bahar) aur fake provider ek alag
port `8099` pe chhe requests. Temp files (`%TEMP%\w6d2r_*`, `4`) delete kiye; `relay_python_after=0`, `listen_8099=0`,
counters same. `[R]` = user ne khud nahi chalaya.

#### Seal — record sahi, order phir ulta

| Check | Value | Provenance |
|---|---|---|
| `Get-FileHash` frozen file | `A544B933…AC021CC0` = Step 0 = Step 5 = review | `[MEASURED]` / `[MEASURED-R]` |
| `git hash-object` = `git rev-parse HEAD:<path>` | `289f308b…54d3` dono | `[MEASURED-R]` |
| `w6d2_step0_frozen_hash.txt` | **exactly `2` lines**, koi khaali `=` nahi — C0 pass. Kal ka defect fix hua | `[MEASURED]` |
| seal commit · hash file | commit `13:37:40`; hash file **CreationTime** `13:37:51` — commit ke **`11 s` baad bani** | `[MEASURED-R]` |
| `seal_before_first_experiment` | `True` — commit `13:37:40` < `w6d2_gate_control_…_unset_api.log.err` `13:40:04` | `[MEASURED]` |

**BRIEF ka block hash file pehle likhta hai, phir commit.** File commit ke baad *bani*, to block us order me nahi chala
`[INFERRED from CreationTime]`. Aaj farak nahi padta — `git_blob = head_blob`, aur seal ka asli witness ab commit hai,
hash file nahi. Kal `21 s`, aaj `11 s`: shakal wahi.

#### Step 0 / 0.5

| Kya | Result | Provenance |
|---|---|---|
| staged (0a) | exactly `5`, `0` KEY | `[MEASURED]` |
| bench (0b) | saare expected values: `src_diff=0`, aath hashes, `heads=w4d4_sink_unique (head)`, `relay_python=0`, `listen_8000_8002=0`, `dbs=postgres,relay`, counters `133\|145\|19\|4\|7\|39\|5\|0\|1`, protected same, `dotenv_mentions_flag=0`, `key_index=0`, `brief_control=31` | `[MEASURED]` |
| seals | `17/17/17 restored=0 blocked=0` → Step 5 `18/18/18 restored=0 blocked=0` | `[MEASURED]` |
| `💡` rewrites | dono sections `own=1 gaps=1 rev=1 order_own_gaps_rev=True`; totals `6·6·6`, `1·1·1` | `[MEASURED]` |

**`💡` ke content pe ek galti, user ke apne block me:** Week 6 Din 1 own-words point 1 — *"uncommitted false positive
logs … ko eliminate kiya gaya"* — aur usi block ka point 2 — *"Narrowed, not eliminated"*. Din 1 ki closeout correction
#3 ne ye exact wording `narrows` me badli thi. Ek block me dono claim nahi ho sakte. Structure check sirf headings
ginta hai, wording nahi — ye usi check ka blind spot hai.

#### Step 1 — `P-44`, control vs fixed (`logs/w6d2_step1_both.txt`)

| Arm | control `get/post/db_ping/openapi_sh/flag_lines` | fixed `get/post/db_ping/openapi_sh/flag_lines` | fixed `flag_line` |
|---|---|---|---|
| `unset` | `200/405/200/1/0` | `404/404/404/0/1` | `test_routes=None` |
| `empty` | `200/405/200/1/0` | `404/404/404/0/1` | `test_routes=''` |
| `zero` | `200/405/200/1/0` | `404/404/404/0/1` | `test_routes='0'` |
| `true` | `200/405/200/1/0` | `404/404/404/0/1` | `test_routes='true'` |
| `garbage` | `200/405/200/1/0` | `404/404/404/0/1` | `test_routes='banana'` |
| `one` | `200/405/200/1/0` | `200/405/404/1/1` | `test_routes='1'` |

`[MEASURED]`. Har arm `health=200 healthz=200 listening=True err_mentions_flag=0`; `relay_python_after=0` dono phases.
Control `main_hash=d55e3b8a…`, `src_diff_files_vs_HEAD=` khaali; fixed `7241c055…`, `src/main.py`. `py_compile_exit=0`,
`db_ping_mentions=0`. Pick **(i)** — sirf exact `"1"` on — `true`/`garbage` off arm jaisa, jo (i) ka required row hai.

**Differential ne kya alag kiya:** `slow_hold_post` off arms pe `404`, `405` nahi — route registered hi nahi, to router
method tak pahunchta hi nahi. Handler-andar-`404` wala galat gate yahan `405` deta (KEY v2 `[MEASURED-R 2026-10-02]`).
Akela `GET → 404` dono ko alag nahi karta.

**Reviewer probes, user ke `main.py` pe, import-time `[MEASURED-R]`** (`app.routes` me `/slow-hold`, `/db-ping` dhundha):

| `ENABLE_TEST_ROUTES` | test paths at import | import ke baad `os.environ = "1"` |
|---|---|---|
| `' 1'` | `[]` | `[]` |
| `'1 '` | `[]` | `[]` |
| `'TRUE'` | `[]` | `[]` |
| unset (`None`) | `[]` | `[]` |
| `'1'` (positive control) | `['/slow-hold']` | `['/slow-hold']` |

Whitespace aur case strict gate pe off. **Chalte process me env badalne se route nahi judta** — KEY trap 7 `[INFERRED]` tha,
ab off→on direction measured. Flag `main.py:18` pe padha jaata hai, `from src.database import get_db` (`:7`) ke baad — to
`.env` me flag likha ho to wo lagega (`load_dotenv(override=False)`, shell jeet-ta hai) `[INFERRED from source]`; `.env` me
flag aaj `0` mentions `[MEASURED]`; reviewer ne `.env` nahi chhui.

#### Step 2 — design picks (`ANSWERS` Step 2; committed record sirf ye table hai)

| Faisla | Pick | Cost (user ka likha) | Review |
|---|---|---|---|
| 1 trigger | (B) header `x-fake-mode` | caller ko headers thread karne padenge; header `jobs` me persist nahi | Din 3 ke `complete(prompt, params)` ko header ka rasta chahiye — input, aaj ka faisla nahi |
| 2 ledger | (i) memory counter + `GET /v1/ledger` | restart pe `0` | `--workers N` = `N` ledgers `[INFERRED]`, cost me nahi likha |
| 3 counter position | handler ki pehli line | — | ginta hai *"kitni valid calls handler tak aayi"*, *"kitni process hui"* nahi (neeche correction #6) |
| 4 token rule | `tokens_in = len(prompt.split())`, `tokens_out = 10` | — | `ok` path pe sahi; `trickle` me `4` hardcoded `[MEASURED-R]` |
| 5 hang shapes | `hang` = silence, `trickle` = chunked stream | — | `hang` `asyncio.sleep(30.0)` ke baad poora `200` deta hai — bounded silence |

`w6d2_step2_requests.txt`: `labels=11 ok_equals_repeat=True distinct_requests=10` — C2 pass `[MEASURED]`.

#### Step 3 — provider (`logs/w6d2_step3a_check.txt`, `w6d2_step3b_check.txt`)

C3 ki har row pass `[MEASURED]`: `listen=127.0.0.1` · `ledger_read_stable=True` · `ok`/`ok_repeat`/`ok_longer` `200`,
`ledger_delta=1` har ek, `ledger_total_delta=3` · `ok_keys=text,tokens_in,tokens_out` · tokens `(4,10) (4,10) (12,10)` —
pair dono `True` · `imports_database=0` `resolved_db_lines=0` · `429` `retry_after='2'` · `500`/`400`/`401` · `slow_below`
`3.020 s` · `py_compile_exit=0`. Har error mode pe `exc=none` `[MEASURED]` — httpx status pe raise nahi karta.

**Timeline `[MEASURED]` file times se:** trail `step=2` `14:18:23` → `src/fake_provider.py` **CreationTime** `14:20:45` →
3a check `14:21:22` → file ki aakhri write `14:22:29` → 3b check `14:22:58`. Step 3 ka budget `30 min`; Step 2 trail se
Step 3b trail tak `4 min 52 s`, aur `108`-line file ki pehli save se aakhri save tak `104 s`. **File times authorship tay
nahi karte** — file kahin aur likhi jaa sakti thi aur yahan save hui `[INFERRED]`. Protocol ka rule hai `src/` ki har line
user likhta hai; ye kaise bani, `ANSWERS` me ek line user ko likhni hai. Poora din `62 min 44 s`, budget `125 min`.

#### Step 4 — caller ka view (`logs/w6d2_step4_probe.txt`, `w6d2_step4_census.txt`)

| Label | status / exc | `str` | elapsed | `ledger_delta` | stream `headers_at` / chunks / `max_gap` | access line |
|---|---|---|---|---|---|---|
| `ok` … `401` (7) | `200`/`429`/`500`/`400`/`401` · `none` | `''` | `0.005`–`0.007 s` | `1` har ek | — | haan |
| `slow_below` | `200` · `none` | `''` | `3.013 s` | `1` | `3.017` / `1` / `0.000` | haan (dono pass) |
| `slow_above` | `-` · `ReadTimeout` | `''` | `5.007 s` | `1` | — | **nahi** |
| `hang` | `-` · `ReadTimeout` | `''` | `5.010 s` | `1` | `-` / `0` / `ReadTimeout` at `5.013 s` | **nahi** (dono pass) |
| `trickle` | `200` · `none` | `''` | **`8.462 s`** | `1` | `0.014` / `8` / `1.217` | haan (dono pass) |
| `malformed` | `422` · `none` | `''` | `0.008 s` | **`0`** | — | haan |

`[MEASURED]`. `posts_sent=15 ledger_end=14 ledger_total_delta=14` · `access_lines_post_v1_complete=12` (`200×7`, `400`,
`401`, `422`, `429`, `500` ek-ek) · `distinct_client_ports=3` · `listen=127.0.0.1` · `relay_python_after=0`.

**Arithmetic:** `15 − 1` (`malformed`) `= 14` ledger. `15 − 3` (`slow_above`, `hang`, stream `hang`) `= 12` access.
`200×7` = `ok`, `ok_repeat`, `ok_longer`, `slow_below`, `trickle`, stream `slow_below`, stream `trickle`. `trickle` =
`7` gaps × `1.2 s` = `8.4 s` + overhead → `8.462` `[MEASURED]` / `[INFERRED]` split.

**Connections, user ke provider log se `[MEASURED-R]`:** chaar client ports — `63692` (`ok` … `slow_below`, phir
`slow_above` ka POST jiski line nahi) · `65387` (sirf do `GET /v1/ledger`; `hang` ka POST yahin timeout hua) · `57796`
(`trickle` … stream `slow_below`, phir stream `hang`) · `59564` (stream `trickle`). **Teen `ReadTimeout`, chaar
connections**; census sirf un ports ko ginta hai jinpe ek POST access line hai → `3`.

**Teen ginti, teen sawaal, dono direction me alag:**

| Source | Count | Kya ginta hai | Jo isme hai par doosre me nahi |
|---|---|---|---|
| probe | `15` posts | caller ne kitni requests bheji | — |
| provider ledger (handler line 1) | `14` | kitni requests validation paar karke handler tak aayi | `slow_above`, `hang` ×2 — access log me nahi |
| uvicorn access log | `12` | kitne responses **client ke rehte start** hue | `malformed` `422` — ledger me nahi |

Mechanism `[MEASURED-R]` source, `uvicorn/protocols/http/h11_impl.py`: `:464` `if self.disconnected: return` response
start se pehle; access line `:481–482` response start pe. Isliye `trickle` ki line `t ≈ 0.014 s` pe likhi gayi, body
khatam hone se pehle, aur `slow_above` (`7 s` pe start, client `5 s` pe gaya) ki line kabhi nahi.

#### Step 5 — close (`logs/w6d2_step5_bench.txt`)

`src_status= M src/main.py ; ?? src/fake_provider.py` · saat hashes Step 0 jaise · `heads=w4d4_sink_unique (head)` ·
`dbs=postgres,relay` · `relay_python=0` · `listen_8000_8002=0` · counters same · protected same · `key_index=0` ·
`key_tree=0` · frozen dono Step 0 jaise · `seal_before_first_experiment=True` · staged `6`, `0` KEY/ANSWERS/FROZEN — pass
`[MEASURED]`.

**Fail:** `trail_lines=8 trail_distinct_sha=7`. Trail file `[MEASURED-R]`:

```
step=4a at=2026-10-03 14:25:34.369 sha=CB15DD8D8EA1
step=4b at=2026-10-03 14:25:34.419 sha=CB15DD8D8EA1
```

`50 ms` apart, same hash → **4a aur 4b ki `ANSWERS` ek saath likhi gayi**, census (`14:24:59`) ke baad. BRIEF C5 ne
exactly ye meaning likha tha. Trail ab `9` lines / `8` distinct — `step=5` line bench (`14:26:01`) ke baad `14:26:32`
pe append hui. `ANSWERS` ka current SHA prefix `FACDA5E86938` = `step=5` line → us ke baad file nahi badli `[MEASURED-R]`.

---

### 🔎 Code audit — `git diff 0baaf1a bb90c15 -- src/` (2 files, `+119/−10`)

**`src/main.py`**

| Line | Kya | Check |
|---|---|---|
| `:1` `import os` · `:18` `ENABLE_TEST_ROUTES = os.environ.get(...)` | flag ek baar, import pe | `:7` `src.database` import ke baad → `.env` dikhta hai `[INFERRED]` source |
| `:19` `print(f"test_routes={ENABLE_TEST_ROUTES!r}", flush=True)` | raw `repr`, grep prefix | `None` / `''` / `'0'` alag dikhe `[MEASURED]` |
| `:33–37` `if ENABLE_TEST_ROUTES == "1":` → `@app.get("/slow-hold")` | register-time gate | off pe `openapi_slow_hold=0`, POST `404` `[MEASURED]` |
| `/db-ping` | deleted | `db_ping=404` har arm, `db_ping_mentions=0` `[MEASURED]` |
| `/slow-hold` body | unchanged | `seconds` ab bhi unbounded jab flag on (`P-44` note (b)) — rule 4 ke mutabik sahi |

**Deletion test, `print`:** line hatao to gate wahi kaam karta hai — print protection nahi, **observability** hai. Wahi
cheez jo `P-44` note (a) ne maangi thi: flag ki value ek premise hai, configure hona kaafi nahi. Ek limit: print stdout pe
hai, aur uvicorn ki apni lines stderr pe (KEY trap 6) — log collector sirf ek stream padhe to ye line kho sakti hai `[INFERRED]`.

**`src/fake_provider.py`** — contract ke andar, chaar review notes:

1. **Unknown mode → `200 ok`, fail-open** `[MEASURED-R]`: `x-fake-mode: 5OO` / `Hang` / `''` / `slow-above` → `200
   {"text":"fake completion",…}`. `Header(default="ok")` aur aakhri `return` ka fallthrough. Din 4 ka retry experiment
   agar mode ka spelling galat kare, to *"koi retry nahi hua"* ek passing-looking result hoga. **Gate pe user ne fail-closed
   chuna (typo → off); provider pe ulta hai.** Test lab me *"jo maanga wo nahi mila"* aur *"success"* alag dikhne chahiye.
   Fix user ka; aaj ke contract ka violation nahi.
2. **Startup line ek literal hai, witness nahi** `[MEASURED-R]`: `--port 8099` pe chalaya →
   `fake_provider listening=127.0.0.1:8002 ledger=in_memory`, jabki uvicorn ne `Uvicorn running on http://127.0.0.1:8099`
   likha. `resolved_db=` config se nikalta hai; ye line kuch nahi padhti. Bind ka asli witness aaj `Get-NetTCPConnection`
   (`listen=127.0.0.1`) tha. **BRIEF me is contract row ka koi Part C check nahi tha** — reviewer defect, neeche.
3. **`trickle` ke tokens hardcoded** (`', "tokens_in": 4'`) `[MEASURED-R]`: `LONGER` prompt pe bhi `tokens_in: 4`, jabki
   `ok` pe `12`. Din 3 agar `trickle` ka body result me store kare to token rule toot-ta hai.
4. **`hang` bounded hai: `asyncio.sleep(30.0)`, phir poora `200`** `[MEASURED]` source. Contract (`≥ 2 × 5 s`) pass. Par
   `timeout > 30 s` wala caller `hang` se ek success paayega `[INFERRED]`. Aur non-streaming handler client ke jaane pe
   cancel nahi hota (KEY trap 5, reviewer throwaway pe measured) — user ke provider pe *not measured*: koi completion
   line nahi hai.

Concurrency: `ledger["calls"] += 1` ke beech koi `await` nahi → ek event loop pe lost update nahi (KEY trap 12
`[MEASURED-R 2026-10-02]` throwaway pe). `import sys` unused.

---

### 🧠 Prediction review — `0.00 / 5.0`, das me das `idk`, chaar reading gaps

Frozen text `docs/daily/week_06/DIN_02_PREDICTIONS_FROZEN.md` se **quote**; hash verify hua. Scoring KEY ke note se:
outcome + mechanism = full · sirf outcome = aadha · `idk` = `0` · `[padh ke]` ka `idk` bina *"kya padha"* = `0` + reading gap.

| Q | Sub-part · tag | Frozen text (verbatim) | Score | Before measurement | After measurement (`ANSWERS`, Beat 4) |
|---|---|---|---|---|---|
| **Q1** | (a) `[padh ke]` | *"idk (padha: src/main.py:1-30, /health, /healthz, /db-ping dekha)"* | `0.00 / 0.34` | not answered — **honest `idk`, kya padha likha** (is file me pehli baar). Par jo padha usi me jawab ka aadha tha: `/db-ping` `:27` pe module-level, aur file me `ENABLE_TEST_ROUTES` kahin nahi → `db_ping=200`, `flag_lines=0`. `/slow-hold` `:33` pe hai — range `27–37` maangi gayi thi, padhi `1–30` | Step 1 Observed: *"all 6 arms had slow_hold_get=200, db_ping=200, openapi_slow_hold=1"*. `slow_hold_post=405`, `flag_lines=0`, *"koi gate nahi"* — nahi. **Partial outcome, mechanism nahi** |
| | (b) `[padh ke]` | *"[padh ke: src/main.py:5 · src/database.py:1–4 · …dotenv/main.py:105 aur :383–387] idk"* | `0.00 / 0.33` | not answered — **reading gap** (tag dohraya) | `.env`, `override`, import order — `ANSWERS` me kahin nahi. **Not explained** |
| | (c) `[chala ke]` | *"[chala ke] idk"* | `0.00 / 0.33` | not answered — honest `idk` | *"route is omitted at registration time (returning 404 and excluded from openapi.json)"* — registration-time sahi; **POST `404` vs galat gate ka `405` aur router ka path-then-method — nahi**. **Partial** |
| **Q2** | (a) `[padh ke]` | *"[padh ke: src/dispatcher.py:60–99] idk"* | `0.00 / 0.5` | not answered — **reading gap** | *"All failure injection paths return their expected status and headers cleanly"* — `exc=none` aur *kyun* (`raise_for_status()` opt-in; `dispatcher.py:71` ka `status_code == 200` branch isi wajah se hai) nahi. **Not explained** |
| | (b) `[chala ke]` | *"[chala ke] idk"* | `0.00 / 0.5` | not answered — honest `idk` | *"429 returns an integer seconds Retry-After header"* — Python type `str` aur HTTP-date pe `int()` → `ValueError` nahi. **Not explained** |
| **Q3** | (a) `[padh ke]` | *"[padh ke: docs/PROBLEMS.md P-55 (~3080) · docs/logs/WEEK_06.md (~146)] idk"* | `0.00 / 0.5` | not answered — **reading gap**. Apne hi Din 1 ka measurement tha: `error=ReadTimeout:  attempts=1`, `5.035–5.050 s`. **Aur seal ke ~2 min baad (Step 0.5) user ne apne own-words me likha:** *"`httpx.ReadTimeout` ka `str(exc)` empty hota hai"* — jawab ka aadha, seal se pehle uski apni yaad me | Step 4b (1): *"dono me status=-, exc=ReadTimeout, elapsed=~5.01s … Caller cannot tell"* — outcome aur *"alag nahi bata sakta"* sahi. Read phase ka first-byte wait aur `str=''` ka source nahi. **Partial** |
| | (b) `[chala ke]` | *"[chala ke] idk"* | `0.00 / 0.5` | not answered — honest `idk` | Step 4b (3): *"timeout=5.0 poore request-response lifecycle ka ceiling nahi hai, balki har individual network I/O read … ka maximum gap"* + `8.46 s`, gap `1.2 s`. **Mechanism ke saath — aaj ka sabse achha Beat 4.** `httpx.Timeout` ke chaar phase timeouts aur *"total deadline hai hi nahi"* — nahi |
| **Q4** | (a) `[padh ke]` | *"[padh ke: docs/DECISIONS.md:650] idk"* | `0.00 / 0.5` | not answered — **reading gap**. Week 1 ka `loc: ["body", 306274]` mechanism. **Aur Step 2 line 3 (run se pehle, seal ke baad) me user ne khud likha:** *"malformed requests (422) rejected before handler are not counted"* | Step 4a: `malformed returns 422 with ledger_delta=0`. Middleware half kahin nahi. **Partial** |
| | (b) `[chala ke]` | *"[chala ke] idk"* | `0.00 / 0.5` | not answered — honest `idk` | Step 4b (2): `ledger_delta=1`, caller `ReadTimeout` — sahi. *"Provider ledger shows request processed"* — **galat noun**: handler line 1 *entry* ginta hai; `hang` me kuch process nahi hua tha jab caller gaya. **Partial, ek imprecision ke saath** |
| **Q5** | (a) `[chala ke]` | *"[chala ke] idk"* | `0.00 / 1.0` | not answered — honest `idk` | Table: `slow_above`/`hang` *"No (absent)"*, `trickle` *"Yes"*; census `12`. Stream `hang` ka missing line aur *kyun* (response start pe likhi jaati hai, disconnected pe skip) — nahi. **Partial outcome, mechanism nahi** |

**Total `0.00 / 5.0`.** Week 6 frozen running total: **`0.00 / 10.0`**. KEY ke mutabik **`2.17` points padhne se derivable
the** (`Q1(a)`, `Q1(b)`, `Q2(a)`, `Q3(a)`, `Q4(a)`). Ye **lagatar saatwa din** hai bina ek bhi prediction attempt ke.

**Provenance — strict:**

| Category | Sub-parts |
|---|---|
| Derived before measurement | **`0`** |
| `[padh ke]` idk with *"kya padha"* | `1` — `Q1(a)` (pehli baar; par padhi range maangi range se chhoti) |
| `[padh ke]` idk, reading gap | `4` — `Q1(b)`, `Q2(a)`, `Q3(a)`, `Q4(a)` |
| `[chala ke]` honest idk | `5` |
| Explained after measurement, mechanism ke saath | `1` — `Q3(b)` |
| Explained after measurement, partial | `6` — `Q1(a)`, `Q1(c)`, `Q3(a)`, `Q4(a)`, `Q4(b)`, `Q5(a)` |
| Not explained even after measurement | `3` — `Q1(b)`, `Q2(a)`, `Q2(b)` |
| *"KEY se pehle"* ka order | **per-step trail se aaj pehli baar verify hua** — sirf 4a/4b ek saath likhe gaye. KEY kab khula, ye trail nahi batata, aur file access times bharose ke nahi |

**Ek line jo earned hai:** jo chahiye tha wo kal se ek kadam aage gaya — `Q1(a)` me *kya padha* likha, aur `Q3(b)` ka Beat 4
mechanism ke saath hai.

**Sabse mehenga pattern, aaj do jagah measured:** jawab user ke paas *tha*, seal pe nahi aaya. `Q3(a)` ka aadha uske
own-words me seal ke do minute baad; `Q4(a)` ka aadha uski Step 2 design line me. **Knowledge gap nahi, retrieval-at-seal
gap.** Seal pe `[padh ke]` file kholna hi wo step hai jo chhoot raha hai.

---

### 🤖 Reviewer ki apni galat predictions aur defects — record ke liye

1. **BRIEF Step 3 contract ki *"Startup"* row ka Part C me koi check nahi tha.** Hardcoded literal pass ho gaya kyunki kisi
   check ne provider ko doosre port pe nahi chalaya. Check decorative nahi tha — tha hi nahi.
2. **BRIEF/C3 ne unknown mode ka koi arm nahi rakha.** Fail-open fallthrough review pe mila, run pe nahi.
3. **KEY trap 13** ne throwaway pe *"connections paanch the"* likha; user ke run pe chaar (teen timeouts). Number server
   pe depend karta hai — KEY ko *"must be measured"* likhna chahiye tha. Mechanism sahi.
4. **KEY `Q1(b)` ka `.env` arm user ke code pe kisi ne nahi chalaya.** User ne flag `:18` pe padha (database import ke
   baad); KEY ka mechanism throwaway pe measured tha, user ke `main.py` pe nahi. Reviewer ne `.env` nahi chhui (secrets),
   to ye `[INFERRED]` hi rahega. BRIEF ko is arm ke liye ek alag dotenv file wala instrument dena chahiye tha.

**KEY ne jo theek kaha, aaj user ke code pe measured:** `Q1(a)` chaaron values · `Q1(c)` `404` (v1 shape) · `Q2(a)` chaaron
`exc=none` · `Q2(b)` `retry_after='2'` `str` · `Q3(a)` `ReadTimeout`, `str=''`, `5.007`/`5.010 s` · `Q3(b)` `200`, `> 5 s` ·
`Q4(a)` handler `0` · `Q4(b)` `1` · `Q5(a)` `12`, missing `slow_above` + `hang` ×2.

---

### 💡 What the session established — **draft, user ko ye apne shabdon me dobara likhna hai** (Week 6 Din 3, Step 0.5)

> Ye section reviewer ne likha hai. **Ye user ki samajh nahi hai.** Protocol ke hisaab se Din 3 Step 0.5 pe iske upar
> `### 💡 What I understood — own words, <date>` aur ek `Gaps vs reviewer:` line aayegi — bina ye section dobara padhe.

1. **Gate register-time pe ho to route app me hai hi nahi**, aur ye `405` vs `404` se dikhta hai: path ka route nahi →
   `404` har method pe; route hai par method nahi → `405`. Ek `GET` akela sahi aur galat gate ko alag nahi karta.
2. **Flag ek baar, import pe padha jaata hai.** Chalte process me env badlo, kuch nahi badalta; `.env` sirf tab lagta hai
   jab flag `load_dotenv()` ke baad padha jaaye, aur shell ki value `.env` se jeet-ti hai.
3. **httpx `4xx`/`5xx` pe raise nahi karta.** Caller jab tak status khud na dekhe, `500` ek success hai.
4. **`timeout=5.0` chaar phase timeouts hain, deadline nahi.** Har byte `< 5 s` me aaye to request `8.462 s` (ya kitni
   bhi) chal sakti hai, aur `200` milta hai. Jahan ye call ek row lock ke andar hai, wahan lock bhi utni der (`P-59`).
5. **`slow_above` aur `hang` caller ko ek jaise dikhte hain** — class, `str=''`, `~5.0 s`. Farak sirf provider ki taraf hai.
6. **Provider ki teen ginti teen sawaal hain** — posts `15`, ledger `14` (handler tak aayi), access `12` (response client
   ke rehte start hua). Dono direction me alag; koi ek doosre ka substitute nahi.
7. **Test lab ka default bhi fail-closed hona chahiye.** Unknown mode jo `200` de, wo experiment ko chupchaap pass karata hai.

---

### ⚠️ Closeout corrections

| # | Jaise report / record hua | Jo measured hai | Provenance |
|---|---|---|---|
| 1 | Step 5: *"All close bench criteria met … 8 trail entries logged"* | C5 `trail_distinct_sha = trail_lines` **fail**: `7 ≠ 8`. 4a/4b same hash, `50 ms` apart | `[MEASURED]` user ki apni bench file |
| 2 | Review request: *"8 cryptographic trail hashes sealed"* | Trail ab `9` lines, `8` distinct; bench ne `8`/`7` gine | `[MEASURED-R]` |
| 3 | Review request: *"P-44: mark as resolved"* | **Narrowed.** Decided shape implemented aur measured; production me flag off rakhna koi enforce nahi karta, flag on pe `seconds` unbounded — BRIEF C6 ne *"P-44 closed"* exactly isi wajah se mana kiya | `[MEASURED]` / `[INFERRED]` |
| 4 | Step 4b (3): *"keep-alive connection dropped on the two timeout events"* | **Teen** `ReadTimeout` (`slow_above`, `hang`, stream `hang`), **chaar** connections; census `3` kyunki port `65387` pe sirf `GET` lines hain | `[MEASURED-R]` user ka provider log |
| 5 | Step 4b (2): *"Provider ledger shows request processed"* | Ledger handler entry ginta hai. `hang` ka handler us waqt `asyncio.sleep(30)` me tha | `[MEASURED]` source |
| 6 | Step 1: *"Option (i) fail-closed pick chosen"* | BRIEF ne *"pick + ek line cost"* maangi thi. Cost (typo chupchaap off) nahi likhi | `[MEASURED]` `ANSWERS` |
| 7 | `ANSWERS` me owed lines | `labs/w5d4_pool_probe.py` ab flag ke bina `404` paayega · README rows `525`, `526`, `563` purani (`/db-ping`, `/slow-hold`) — dono lines nahi likhi | `[MEASURED-R]` grep |
| 8 | Step 4a explanation: *"Pass 1 and Pass 2 systematically demonstrate caller vs provider perspectives …"* | Koi mechanism nahi, koi number nahi — BRIEF ke framing ka paraphrase | `[MEASURED]` `ANSWERS` |
| 9 | Step 1: *"/db-ping permanently deleted to remove duplicate DB-ping attack surface"* | Drop ka recorded reason `D-28` amendment row 3: `/healthz` ka duplicate (`3.0658` vs `3.0674 s`). Surface ek kam hua; `/healthz` wahi `SELECT 1` unauthenticated karta hai → surface **narrowed**, gaya nahi | `[MEASURED]` `D-28` |
| 10 | Week 6 Din 1 own-words point 1: *"… ko eliminate kiya gaya"* | Usi block ka point 2 *"Narrowed, not eliminated"*; Din 1 correction #3 `narrows` | `[MEASURED]` file |
| 11 | Provider startup line `listening=127.0.0.1:8002` | Literal — port `8099` pe bhi yahi | `[MEASURED-R]` |
| 12 | Step 3a: *"strictly binding to 127.0.0.1:8002"* | Bind command line ka `--host 127.0.0.1` karta hai, file nahi. `listen=127.0.0.1` sahi measured; file me koi bind code nahi | `[MEASURED]` source + bind file |

---

### 🚧 Unresolved / carried

1. **`P-44` — `narrowed`.** Baaki: flag off rakhna koi enforce nahi karta · flag on pe `seconds` unbounded (note (b), cap
   chuna nahi gaya) · `D-28` ka *"three-arm with `ENABLE_TEST_ROUTES=1`"* re-run nahi hua (aaj `one` arm sirf `seconds=0`).
   Owner: cap user ka faisla; re-run jab koi pool experiment `/slow-hold` chahe.
2. **`P-59` (naya)** — dispatcher ka row lock `timeout=5.0` ke andar; trickling receiver pe koi upar ki seema nahi.
   Owner: user ka faisla; candidates Week 7 (`P-35` ke saath) ya `D-22` Month 3.
3. **Fake provider ke teen notes** — unknown mode fail-open · startup literal · `trickle` tokens. Din 3 se pehle user ka
   faisla; Din 4 ka retry experiment pehle ko seedha chhoota hai.
4. **`hang` handler client ke jaane ke baad chalta hai ya nahi** — user ke provider pe not measured.
5. **README** rows `525`, `526`, `563` — Din 6 Step 3 (Part D).
6. **`ANSWERS` me teen owed lines** (Step 1b cost, pool probe, README) aur `fake_provider.py` kaise bani, ek line.
7. **Is entry ka `💡`** — Din 3 Step 0.5.

---

### ❓ Next thought

Aaj provider ne `14` gine, uvicorn ne `12`, caller ne `15` bheje — aur `hang` pe caller ke paas ek khaali `ReadTimeout`
tha jabki provider ne call gin li. Din 3 pe Relay pehli baar ye call apne worker se karega, aur `job_executions` ek chautha
record banega.

**Jab provider ka ledger `+1` kahe aur Relay ki `job_executions` row `ReadTimeout` kahe, Relay ka kaunsa column bata sakta
hai ki provider ne bill kiya — aur agar koi nahi, to retry karne ka faisla kis information pe hoga?**

---

*Din 2 BRIEF:* [`../daily/week_06/DIN_02_BRIEF.md`](../daily/week_06/DIN_02_BRIEF.md) ·
*Seal:* [`../daily/week_06/DIN_02_PREDICTIONS_FROZEN.md`](../daily/week_06/DIN_02_PREDICTIONS_FROZEN.md) ·
*Commits:* `d1d0ea9` (seal) · `bb90c15` (feature)
