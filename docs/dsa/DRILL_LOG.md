# DSA Drill Log

DSA/CP training ka record. Relay backend docs se alag — dono mix nahi hone chahiye.

**Rules aur "kyun" ke liye → `PLAYBOOK.md`. "Aaj kya karna hai" ke liye → Algo-Path app.**
Ye file sirf **numbers aur history** hai.

Coach (`dsa-coach` agent) session start pe ye padhta hai aur session end pe khud update karta hai.

> **Bahut saara measurement ab app mein hai, is file mein nahi.** `attempts` table har solving event
> pe cause code, time-to-first-idea aur blind hit rakhti hai. Coach yahan **summary** likhta hai —
> row-by-row dobara nahi. Jahan app authoritative hai, wahan "app dekho" likhna theek hai.

---

## 1. Current state (last updated: 2026-09-22)

**Background:** ~250-270 LeetCode problems solved (sheet-style, graphs tak). Knowledge base hai.
Missing cheez knowledge nahi — **direction** hai.

**Diagnosis, measured:** sheet mein `trigger` ek field hai **`Pattern` pe**, aur questions pattern ke
**andar nested** hain. Toh question tak pahunchne ka ek hi rasta tha: pattern card → trigger padho →
question kholo. Retrieval direction `pattern → question`. Contest `statement → pattern` chalata hai.
**Wo direction 250 problems mein ek baar bhi practice nahi hui.** Isliye recognition 80% pe hai aur
production 0 pe.

| Cheez | Level | Note |
|---|---|---|
| Topic knowledge (breadth) | ok | bottleneck nahi hai |
| Untagged recognition | **weak** | ab naapa jaayega — blind hit rate |
| Independent production | **weak** | |
| Constraints → allowed complexity | weak | cost gine bina optimize karta hai |
| Edge case khud generate karna | absent | |
| Plan → code fidelity | **weak** | mistake ledger ka top entry, count 6 |
| STL syntax reflex | weak | skeleton drill isko target karti hai |
| Apne code ka self dry-run | kabhi nahi kiya | |

**Rating:** not recorded.

**Gap:** `2026-09-11` se `2026-09-22` tak zero entries. `git log -- docs/dsa` mein **ek** commit.
`[MEASURED]` Iska matlab pehla failure skill ka nahi tha — **system chala hi nahi.**

---

## 2. Naye instruments — jo pehle maujood hi nahi thay

Ye chaar cheez `2026-09-22` se pehle **kahin record nahi hoti thi**. Isliye "improvement dikhta nahi"
ka jawab pehle mil hi nahi sakta tha.

| Instrument | Kya naapta hai | Kahan |
|---|---|---|
| **Blind hit rate** | unlabeled problem pe prediction sahi nikli ya nahi | `attempts.blind_hit`, sealed prediction se compute hota hai — self-marked nahi |
| **Time-to-first-idea** | sahi approach kis minute pe aayi (`NULL` = kabhi nahi aayi) | `attempts.first_idea_minutes` |
| **Cause code C1-C6** | fail kyun hui — chhe alag diagnoses | `attempts.cause` |
| **Reframe move** | kaunsa move unlock karta hai | `attempts.reframe` |
| **Skeleton reps** | plan→code reflex | `skeleton_reps.clean_reps` + `best_seconds` |
| **Gates G1-G4** | pattern acquired hai ya sirf ticked | `pattern_progress.*_at` timestamps |
| **Station time** | **kahan** atakta hai, aath mein se | `attempts.station_log` |
| **Hint level** | kaunsa rung laga. `solved y/n` se bahut behtar signal | `attempts.hint_level` |
| **Lapses** | ek problem kitni baar fail hui (leech) | `attempts.lapses` |
| **Idea health** | ek idea baar baar fail (wheel-spinning) | `idea_health.fails` + `mode` |

---

## 2B. Station time — kahan atakta hai

`station_log` se sum. **Jahan minute jama hote hain wahi asli gap hai** — aur ye wo number hai jo
"mujhe lagta hai pattern recognition weak hai" ko evidence se replace karta hai.

| Station | Stall | Total minutes | Share |
|---|---|---|---|
| 1 | statement samajhna | not recorded | — |
| 2 | brute force | not recorded | — |
| 3 | waste dekhna | not recorded | — |
| 4 | kill | not recorded | — |
| 5 | plan → code | not recorded | — |
| 6 | galat answer | not recorded | — |
| 7 | TLE | not recorded | — |

**Prediction on record:** bulk `2` aur `3` pe hoga (brute + waste), `4` pe nahi. Ye **`[INFERRED]`**
hai. Agar sach mein `4` pe nikla toh diagnosis galat tha aur wo likhna hai — kyunki tab gap genuinely
knowledge ka hai, derivation ka nahi.

---

## 2C. Hint level distribution

| Rung | Kitni baar | Matlab |
|---|---|---|
| H0 — koi hint nahi | 0 | independent solve |
| H1 — family | 0 | |
| H2 — waste | 0 | |
| H3 — structure | 0 | |
| H4 — editorial | 0 | |

`H3 + H4` ka share `>50%` hote hi **hint-creep** breaker band `-100` kar dega. Ye solve rate se
**pehle** move karta hai, toh yahi sabse early warning hai.

---

## 2D. Leeches aur idea health

| Problem | Lapses | Status |
|---|---|---|
| — | — | — |

| Idea | Fails | Passes | Mode |
|---|---|---|---|
| — | 0 | 0 | blind |

`lapses >= 2` → problem band, usi idea ki aasan problem. `fails >= 3` → idea `guided` mode mein,
aur rasta hai anchor → skeleton → labeled problem. Ek pass fail streak `0` kar deta hai aur mode
`blind` wapas.

---

## 2E. Breaker firing log

| Date | Breaker | Evidence | Kya kiya |
|---|---|---|---|
| — | — | — | — |

Breaker fire hona **event** hai, mood nahi. `day_log.breakers` mein bhi store hota hai.

---

## 3. Daily log

Coach roz ek **summary row** likhega. Per-attempt detail app mein hai.

| Date | Clock min | Blocks done | Blind attempts | Blind hits | Causes | Skeleton reps | Note |
|---|---|---|---|---|---|---|---|
| 2026-09-10 | not recorded | — | 0 | 0 | — | 0 | baseline session: 3019 + 3020, 35 exchanges, ek syntax galti 6 baar |
| 2026-09-11 → 2026-09-21 | — | — | — | — | — | — | **gap.** System banaya gaya, chalaya nahi gaya |
| 2026-09-22 | — | — | — | — | — | — | redesign ship hua. Migration chalana baaki |

---

## 4. Blind hit rate — Track A

App ise khud compute karti hai. Yahan **hafte ka snapshot** rakhna hai, taaki trend dikhe.

| Hafta | Attempts | Solved | Solve rate | Blind hits | Hit rate | Band | Median first-idea |
|---|---|---|---|---|---|---|---|
| — | 0 | 0 | — | 0 | — | 1400-1600 (cold) | not recorded |

**Solve rate jaanbujh ke target nahi hai** — band khud usko `30-40%` pe hold karta hai, toh wo hil
nahi sakta. **Hit rate aur first-idea** hil sakte hain. Wahi dekhna hai.

---

## 5. Cause distribution — asli diagnostic

~20 attempts baad ye table bata dega kahan kaam karna hai. Abhi khaali hai, aur **khaali hona hi
honest hai**.

| Code | Kya | Count |
|---|---|---|
| C1 | brute force hi nahi likha | 0 |
| C2 | brute tha, waste nahi dikha | 0 |
| C3 | reframe miss | 0 |
| C4 | invariant / monotonicity check nahi kiya | 0 |
| C5 | pattern pata tha, detail galat | 0 |
| C6 | technique hi nahi pata thi | 0 |

**Prediction on record:** bulk `C2 + C3` hoga, `C6` nahi. Ye **`[INFERRED]`** hai — measured nahi.
20 rows baad isko check karna aur galat nikla toh likhna.

---

## 6. Gates — pattern acquisition

| Metric | Count | Note |
|---|---|---|
| Patterns total | 107 | |
| Questions total | 319 | 299 LeetCode, 274 distinct slugs |
| `acquired` (chaaron gate) | 0 | naya metric, zero se shuru |
| `ungated` (tick hai, gate nahi) | app dekho | **yehi asli re-do list hai** |

Purana `mastered` flag `deprecated` hai — wo "teeno question tick" naapta tha, jo completion hai,
recall nahi. App ab `acquired` aur `ungated` dono header mein dikhati hai.

---

## 7. Mistake ledger

Count `3` cross kare toh wo skeleton drill mein aa jaati hai.

| Mistake | Count | Last seen | Category | Skeleton |
|---|---|---|---|---|
| `freq(key)` instead of `freq[key]` / `freq.find(key)` | 6 | 2026-09-10 | syntax | `hash-complement` |
| `if/else` while ke andar rakha, baahar ki jagah | 6 | 2026-09-10 | plan→code | `mono-next-greater` (trap wahi hai) |
| Shortcut socha bina complexity cost gine | 3 | 2026-09-10 | reasoning | — (Gate 2 / BRUTE line) |
| Loop ki state-advance line chhod dena | 2 | 2026-09-10 | plan→code | `win-longest` (trap: `l++`) |
| While condition ka ek clause chhod dena | 2 | 2026-09-10 | plan→code | `mono-deque` (do alag while) |
| Manual trace skip karna | 2 | 2026-09-10 | process | — |
| Loop bound `n` jahan `n-1` chahiye | 1 | 2026-09-10 | boundary | `bs-lower` |
| Accumulator ki init value galat | 1 | 2026-09-10 | plan→code | `kadane` (trap: `v[0]` se init) |
| `max(int, long long)` type mismatch | 1 | 2026-09-10 | syntax | — |

**Har ledger entry ka ek skeleton hai.** 22 skeletons mein se 6 seedha inhi galtiyon ko target karte
hain, aur har skeleton pe `trap` field likhi hai — wo exact line jo memory se type karne pe gayab
hoti hai. Saare 22 `g++ -std=c++17` pe compile verified hain. `[MEASURED]`

---

## 8. Skeleton reps

| Metric | Value |
|---|---|
| Skeletons total | 22 |
| Reflex ban gaye (5 clean reps, `<= 90s`) | 0 |
| Compile verified | 22 / 22 `[MEASURED]` |

---

## 9. Blank re-solve / park tracker

Park ka rule badal gaya: fail hui problem **editorial se band nahi hoti**, park hoti hai, aur
`30 din` baad **blind** wapas aati hai. Pehle `parked_at` likha jaata tha aur kabhi padha nahi
jaata tha — `dueReviews()` parked rows ko skip karta tha, toh parked problem permanently system se
nikal jaati thi. Wo bug band hua.

| Problem | Parked on | Wapas kab | Status |
|---|---|---|---|
| — | — | — | — |

---

## 10. Contest log

| Date | Contest | Rank | Solved | Rating after | Upsolve | Unsolved problem pe kitna time gaya |
|---|---|---|---|---|---|---|
| — | — | — | — | not recorded | — | — |

Aakhri column naya hai aur zaroori hai: **contest failure often triage failure hoti hai, thinking
failure nahi.** Agar ek unsolved problem pe `>25 min` gaya, wo triage bug hai — uska fix alag hai
(shuru mein 3 min saare problems padho aur rank karo), solving practice se theek nahi hoga.

---

## 11. Leading indicators

| Indicator | Target | Abhi |
|---|---|---|
| Blind hit rate | naapna hai, phir target | not recorded |
| Time-to-first-idea median | girta hua | not recorded |
| Hint level — H3/H4 ka share | girta hua | not recorded |
| Blind band centre | `1600+` | `1400` cold start |

**Hataye gaye indicators:** `syntax errors per session` aur FAST ke time targets. Dono ke columns
maujood hain (`attempts.syntax_errors`, `attempts.fast_seconds`) par **koi code unme likhta nahi** —
`[MEASURED]` audit se. Jis indicator ka source nahi hai wo na hone se bura hai.

Chaar hit ho gaye toh OA-reliable hai, chahe hafta 6 ho ya 16.

**Timeline honestly:** pehla hafta sirf measurement hai (15 problems, koi change nahi). Uske baad
timeline actual rate se compute hogi — purana `6-10 hafte` ka number **repeat nahi karna**, wo 6
problems/hafta maan ke banaya tha aur uske peeche koi data nahi tha.

---

## 12. Open items

| Item | Status |
|---|---|
| `migrations/002_intuition.sql` | **done** — 2026-09-22 |
| `Algo-Path DSA` git + GitHub + Vercel | **done** — `github.com/Vishwam401/Algo-Path`, auto-deploy on push |
| `migrations/003_stations.sql` chalana | **pending — iske bina app tootegi** |
| Pehle 15 blind attempts | pending |
| Cause distribution check (C2+C3 prediction sahi thi?) | 20 attempts baad |
| Station time check (station 2+3 prediction sahi thi?) | 20 attempts baad |
| **`stall` breaker** — abhi fire nahi kar sakta | `headlineNumbersFlat` hardcoded `false` hai. Trend ke liye weekly snapshot table chahiye, wo nahi bana. Baaki saat breakers live hain |
