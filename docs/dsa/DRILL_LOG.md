# DSA Drill Log

DSA/CP training ka single source of truth. Relay backend docs se alag — dono mix nahi hone chahiye.

Coach (`dsa-coach` agent) session start pe ye file padhta hai aur session end pe khud update karta
hai. Tujhe manually bharna nahi hai, verify karna hai.

**Rules aur "kya karna hai" ke liye → `PLAYBOOK.md`.** Ye file sirf record hai (numbers, history).

---

## 1. Current state (last updated: 2026-09-10)

**Background:** ~270 LeetCode problems solved (sheet-style, topics tak graphs bhi). Knowledge base
hai. Missing cheez knowledge nahi hai — **recognition** (untagged problem pe technique pehchanna)
aur **production** (bina help khud likh paana) hai.

| Cheez | Level | Note |
|---|---|---|
| Topic knowledge (breadth) | ok | 270 problems, graphs tak |
| Untagged recognition | weak | sheet problems pre-labeled aate hain, contest problems nahi |
| Independent production | **weak** | 270 mein se kaafi editorial/help ke saath nikle honge |
| Problem decode + manual trace | ok, par **trace skip karta hai** | isi wajah se gates zaroori hain |
| Constraints → allowed complexity | weak | cost gine bina optimize karta hai |
| Edge case pakadna (jab dikhaya jaaye) | strong | turant samajh jaata hai |
| Edge case khud generate karna | absent | |
| STL syntax reflex | weak | biggest time sink |
| Plan → code translation | weak | structure likhte waqt gir jaata hai |
| Apne code ka self dry-run | kabhi nahi kiya | |

**Rating:** not recorded. Pehle virtual contest ke baad bharna hai.

**Baseline (2026-09-10):** Weekly 381 ke 3019 + 3020. 35 exchanges total. Ek hi syntax galti
(`freq()` vs `freq[]`) 6 baar. Self-generated counter-examples 0.

**Diagnosis, evidence se:** 3020 (ek Q2) ka poora logic khud derive hua — pattern, ones parity,
`-1` rule, overflow. Knowledge maujood tha. Jo nahi tha: usko code mein utaarna. Saath hi
`for(char c : s)` se next character access karne ki koshish, aur `int len += times;` — 270 solved
problems ke saath ye galtiyan nahi hoti. Isliye `270` weak evidence hai; ye session strong evidence
hai. Bottleneck **production + speed** hai, topic coverage nahi.

---

## 2. Hafta kaise chalta hai

Roz `75 min`. Saturday `~2.5 hr` — hafte ka sabse important din.

| Din | Kaam |
|---|---|
| Mon | Scales 15 min + **2 problems, mixed untagged** (guided, koi timer nahi) |
| Tue | Scales 15 min + **2 problems, mixed untagged** (timed, solo) |
| Wed | Scales 15 min + **2 problems, mixed untagged** (guided) |
| Thu | Scales 15 min + **2 problems, mixed untagged** (timed, solo) |
| Fri | Scales 15 min + **blank re-solve** — hafte ke 2 problems scratch se, notes band |
| Sat | Scales 15 min + **virtual contest 90 min** + **upsolve 60 min** (jo nahi hui, scratch se, phir editorial) |
| Sun | **Postmortem 30 min** coach ke saath. Baaki rest. Koi solving nahi |

Timer ka ek hi rule: **aisa timer jisme ~30-40% problems solve ho jaayein.** 90% pass ho raha hai
matlab bahut aasan; 10% matlab bahut mushkil. Fixed number nahi hai.

Guided din pe timer nahi. Session 75 min pe khatam, chahe problem adhoori ho — agli guided din
continue.

**Koi problem adhoori nahi chhodni.** Timed din pe pehle measurement (timer, jahan pahuncha wahan
ruk), phir close-out (guided mode mein poora solve). Record pehle banta hai, isliye honest rehta
hai.

---

## 3. Problems kahan se — mixed untagged, contest-level

**Topic batches upfront NAHI karne hain.** Wo beginner ke liye theek hai; 270 problems ke saath
galat hai. Knowledge already hai — jo missing hai wo untagged problem pe technique **pehchanna** aur
bina help **khud likhna** hai.

Toh Mon-Thu: **random purane contests ke Q1 + Q2**, mixed, untagged. Roz ek different contest.

LeetCode pe kaise:
1. Contest → past contests → koi bhi purana **Weekly ~340-380** ya usse neeche
2. Uska Q1 (Easy) + Q2 (Medium)
3. Verify: problem page pe contest ka naam likha hona chahiye
4. Recent contests (Weekly 400 aur upar) **chhodo** — wo Saturday virtuals ke liye reserved hain

**LeetCode ka "Topics" aur "Hint" section collapsed rakhna hai.** Wo kholna Gate 2 ka jawab dekh
lena hai, aur exactly wahi cheez sheet-practice ne pehle se muft de rakhi hai. Contest mein nahi
milegi.

**Problem tu pick karta hai, coach nahi.** Reason: coach ko technique pehle se pata ho gaya toh
Gate 2 ka sawaal dikhawa ban jaata hai aur uske counter-examples genuine nahi rahenge.

### Topic batch — reactive, upfront nahi

Topic batch tabhi trigger hota hai jab **diagnosis** kahe, guess nahi:

> Mistake ledger ya Daily log mein ek hi topic pe **3 failures cluster** ho jaayein → us topic ke
> **10 problems** ka batch, phir wapas mixed untagged.

Coach ko ye trigger dekhna hai aur khud propose karna hai. Iss tarah topic depth wahan jaayegi
jahan measured gap hai, wahan nahi jahan maine andaaza lagaya tha.

### Reference topic list (batch trigger hone pe)

Hash Table / counting · Sorting + Greedy · Two Pointers / Sliding Window · Prefix Sum ·
Binary Search (+ on answer) · Stack / Monotonic Stack · BFS / DFS on grids · Basic 1D DP

---

## 4. Scales — 15 min, roz

Purpose: syntax ko reflex banana, taaki working memory logic ke liye free ho. 10 Sep pe ek hi galti
6 baar hui kyunki ungli ko syntax nahi pata tha, aur us load ne structure gira diya.

Kaise: nayi khali `.cpp` file, notes band. Memory se type → compile → run → file delete.

```
1. unordered_map banao aur bharo
2. count() se existence check
3. find() + end() se existence check
4. operator[] ka side effect: map.size() pehle aur baad mein print karo
5. range loop se p.first / p.second
6. sort with lambda comparator
7. two-pointer skeleton
8. prefix-sum array
```

Ye list badalti rahegi — jo galti ledger mein 3 baar aa jaaye, wo add ho jaati hai.

**Ye temporary hai.** 3-4 hafte baad review: syntax errors per session `0-1` pe aa gaye toh Scales
5 min pe cut ya band. Permanent ritual nahi hai.

---

## 5. Ek hard rule — no help before 40 minutes

Recognition ko production mein badalne ka ek hi tareeka hai: **genuine solo attempt.**

Koi bhi problem editorial, hint, ya coach ki help se solve nahi hogi jab tak tu genuinely **40
minute** na de chuka ho. Ye timed days ke timer se alag hai — ye baaki sab din pe bhi lagta hai.

Reason: pichhle 270 problems mein jo shortcut liye gaye, wahi aaj bhugatne pad rahe hain. Editorial
padh ke solve karna recognition banata hai, production nahi.

---

## 6. Daily log

| Date | Problem | Diff | Topic | Mode | Gate reached | Exchanges | Syntax errs | Solved? |
|---|---|---|---|---|---|---|---|---|
| 2026-09-10 | 3019 Number of Changing Keys | Easy | Hash Table | guided | Solved | 10 | 4 | yes |
| 2026-09-10 | 3020 Max Elements in Subset | Medium | Hash Table | guided | Solved | 25 | many | yes |

- Mode: `guided` / `timed` / `blank` / `contest` / `upsolve` / `batch`
- Gate reached: `1` / `2` / `3` / `4` / `Solved` — timed din pe `solved?` se zyada useful, kyunki
  `Gate 2 → Gate 3 → Gate 4` progress dikhata hai chahe solve na ho
- `Topic` column reactive batch trigger detect karne ke liye hai — failures kis topic pe cluster
  ho rahe hain

---

## 7. Mistake ledger

Count `3` cross kare toh wo galti agle din ke Scales mein add hoti hai.

| Mistake | Count | Last seen | Category | Scales mein? |
|---|---|---|---|---|
| `freq(key)` instead of `freq[key]` / `freq.find(key)` | 6 | 2026-09-10 | syntax | **yes** |
| `if/else` while ke andar rakha, baahar ki jagah | 6 | 2026-09-10 | plan→code | **yes** |
| Shortcut socha bina complexity cost gine | 3 | 2026-09-10 | reasoning | **yes** |
| Loop ki state-advance line (`value *= value`) chhod dena | 2 | 2026-09-10 | plan→code | no |
| While condition ka ek clause chhod dena | 2 | 2026-09-10 | plan→code | no |
| Manual trace skip karna, verbal summary de dena | 2 | 2026-09-10 | process | no |
| Loop bound `n` jahan `n-1` chahiye | 1 | 2026-09-10 | boundary | no |
| Accumulator ki init value galat | 1 | 2026-09-10 | plan→code | no |
| `max(int, long long)` type mismatch | 1 | 2026-09-10 | syntax | no |
| Variable redeclare karna | 1 | 2026-09-10 | syntax | no |

---

## 8. Topic failure tracker — reactive batch trigger

Yahan failures topic-wise ginte hain. `3` cross karte hi us topic ka 10-problem batch trigger hota
hai.

| Topic | Failures | Batch triggered? |
|---|---|---|
| Hash Table / counting | 0 | no |

---

## 9. Blank re-solve tracker

| Problem | Topic | Solved on | Blank re-solve | Status |
|---|---|---|---|---|
| 3019 Number of Changing Keys | Hash Table | 2026-09-10 | — | pending |
| 3020 Max Elements in Subset | Hash Table | 2026-09-10 | — | pending |

Blank re-solve fail hua toh status `pending` wapas — agle hafte phir test. Ek baar solve karna bar
nahi hai; blank se recall aana bar hai.

---

## 9B. Freeze windows

Planned pauses (exams, travel) — taaki gap "missed days" na ginne jaaye aur timeline honest rahe.

| Se | Tak | Reason |
|---|---|---|
| — | — | — |

---

## 10. Contest log

| Date | Contest | Rank | Solved | Rating after | Upsolve done | Time kahan gaya |
|---|---|---|---|---|---|---|
| — | — | — | — | not recorded | — | — |

Saturday contest ke turant baad upsolve — jo problems nahi hui, pehle scratch se try, phir
editorial, phir core idea dobara implement. Hafte ka highest-value block.

---

## 11. Leading indicators — calendar se zyada ye dekho

| Indicator | Target | Matlab |
|---|---|---|
| Timed Easy ka time | 8 min ke andar, lagataar 3 baar | speed aa gayi |
| Syntax errors per session | `0-1` | Scales ka kaam khatam |
| Friday blank re-solve pass rate | 80%+ | seekha hua hai, samjha hua nahi |
| Own counter-examples jo bug pakde | coach se zyada | Gate 3 develop ho gaya |

Chaar hit ho gaye toh Q1+Q2 reliable hai, chahe hafta 6 ho ya 12.

**Revised timeline** (270 problems ki knowledge base ko count karke):

| Kab | Kya |
|---|---|
| Hafta 1-3 | Scales se syntax settle. Timed days pe fail hona normal |
| Hafta 4-6 | Q1 consistent. Q2 kabhi-kabhi |
| Hafta 6-10 | Q1+Q2 reliable. Rating `1650-1750` |

Condition: Saturday contests miss nahi hone chahiye, aur section 5 ka 40-minute rule tootna nahi
chahiye.

---

## 12. Kya cut kiya, aur kyun

- **Upfront topic batches** → mixed untagged contest problems. Reason: 270 problems ke saath topic
  coverage bottleneck nahi hai; recognition aur production hai. Batches ab reactive hain.
- **Progressive timer ka 4-row table** → ek rule: timer aisa jo ~30-40% success de
- **`pending close-out` cap, `leaked Gate 2` marking, counter-example scoreboard** → bureaucracy;
  mistake ledger aur leading indicators wahi kaam kar rahe hain

Ye rakha kyunki ye actual CP practice se match karta hai: har contest + upsolve, ~30-40% success
rate wali difficulty, postmortem notes, blank/spaced recall, aur editorial se pehle genuine attempt.
