# DSA Playbook — end to end

Ye file **tere** liye hai, agent ke liye nahi. Jab confusion ho, yahi kholo.

- `PLAYBOOK.md` (ye file) — kya karna, kaise, kyun. Rules aur decisions.
- `DRILL_LOG.md` — kya hua. Numbers, history, progress. Agent isko bharta hai.

Goal: **LeetCode contest ke Q1 aur Q2, har baar, time ke andar.** Q3/Q4 abhi target nahi hai.

Asli target **MNC interview ka OA round** hai, CP nahi. Kyun aur kab tak — section 0B mein.

---

## 0. Ek page mein sab

```
ROZ (75 min)
├─ 15 min  SCALES        syntax reps, koi problem nahi
└─ 60 min  din ka kaam

Mon   guided   2 problems (Q1+Q2 purane contest se), coach ke saath, timer nahi
Tue   timed    2 problems, akela, timer on
Wed   guided   2 problems, coach ke saath, timer nahi
Thu   timed    2 problems, akela, timer on
Fri   blank    hafte ke 2 problems SCRATCH SE, notes band
Sat   contest  virtual contest 90 min + upsolve 60 min      <- sabse important din
Sun   rest     30 min postmortem, baaki chhutti

INTERFACE
  nayi chat -> dsa-coach agent -> "aaj kya karna hai" -> problems paste karo
  Tujhe din/mode/timer yaad rakhne ki zaroorat nahi. Agent batayega.
```

---

## 0B. DSA kyun, aur kab tak — real target

**Goal MNC interview clear karna hai. CP nahi. 1800-1900 rating nahi.** Ye section wahi define
karta hai, taaki hafta 6 pe jab bore ho tab reason likha mile.

### 2026 ke interview rounds — kya badla, kya nahi

**Badla — later rounds.** Ek analysis kehti hai 2026 ke onsite loops mein Amazon, Google, Meta,
Palantir mein ~60% loops mein kam se kam ek round aisa hai jahan candidate **existing code padhta
hai**, scratch se likhta nahi. Google ne "code comprehension" round add kiya — 200-500 line ka
unfamiliar codebase, 60 min, bugs dhoondho, design discuss karo, aur Gemini AI assistant available
hota hai; evaluate hota hai AI fluency, prompt engineering, output validation, debugging. Stripe
LeetCode hi nahi poochhta — real codebase, failing test, debug karo.

**Nahi badla — OA round.** Ye important hai. OA abhi bhi pure DSA hai:
- Visa: CodeSignal/HackerRank, 70-90 min, 4 questions Easy/Medium se Medium/Hard, aage badhne ke
  liye 3/4 fully solve
- D.E. Shaw: 90-120 min, 2-3 medium-to-hard coding problems
- Palantir new grad: HackerRank OA, DSA-focused
- Salesforce intern/new grad: 2-3 coding problems, aur intern roles ke liye **OA hi main technical
  filter** hai

Sources: [debugging round analysis](https://dglearning.substack.com/p/reading-code-like-an-interviewer) ·
[Google code comprehension](https://careers.northeastern.edu/blog/2026/05/13/googles-ai-assisted-coding-interview-2026-guide/) ·
[Stripe](https://www.interviewcoder.co/blog/stripe-software-engineer-interview) ·
[Visa OA](https://www.techprep.app/blog/visa-interview-process) ·
[D.E. Shaw OA](https://www.techprep.app/blog/de-shaw-interview-process) ·
[Palantir](https://articles.shadecoder.com/palantir-software-engineer-interview-process-every-round-explained-2026-complete) ·
[Salesforce](https://www.lodely.com/companies/salesforce/online-assessment)

*Content licensing ke liye rephrase kiya gaya. Ye interview-prep blogs aur candidate reports hain,
official company docs nahi — company se company vary karega.*

### Isse nikalta hua conclusion

```
DSA        = FILTER          OA. Isse pass hue bina koi interview hi nahi hoga
Debugging  = DIFFERENTIATOR  later rounds. Yahan offer banta ya tootta hai
```

Toh DSA **chhodna nahi hai** — par uska bar clear hai:

> **DSA pe utni mehnat jitni OA clear karne ke liye chahiye. Usse ek rupya zyada nahi.**

OA ka bar: 70-90 min mein 4 ka 3, mostly Easy/Medium. Yani **Easy 8-10 min, Medium 20-25 min,
reliably.** Rating terms mein `1600-1700`, `1900` nahi. Aur ye exactly wahi target hai jo iss
playbook mein already hai — Q1+Q2 reliable. Plan sahi size ka hai.

### Relay iss plan ka doosra half hai

Debugging round mein exactly ye poochha jaata hai: "ye code kya karta hai, kahan toot sakta hai,
tumne ye design kyun chuna". Relay — durable job engine, crash recovery, retries, idempotency, DLQ,
aur `DECISIONS.md` / `PROBLEMS.md` mein measured postmortems — us round ka answer hai.

**Relay pe kaam interview prep se alag nahi hai.** Wo doosra half hai.

### Time allocation

**Phase 1 — ab se ~8-10 hafte, OA gate cross karne tak**

| Kaam | Share |
|---|---|
| DSA (ye playbook, 75 min/din) | 60% |
| Relay | 40% |

Reason: OA hard gate hai aur tu abhi uske neeche hai. 10 Sep pe ek Q2 untimed bhi submit nahi hua.

**Phase 2 — jab OA-reliable ho jaaye** (Easy 8 min, Medium 25 min, lagataar)

| Kaam | Share |
|---|---|
| DSA — maintenance: 2-3 din/hafta + Saturday contest | 25% |
| Relay + system design | 50% |
| **Debugging practice** (naya block) | 25% |

Phase 2 ka debugging block:
- Apne Relay codebase mein deliberately bug daalo, ek hafte baad dhoondho
- Mid-size open-source repo ka code padho, likho "ye kahan toot sakta hai"
- GitHub pe active repos ke open PRs padho — PR review practice
- **AI fluency** — Google explicitly evaluate kar raha hai. AI ka output validate karna, uske galat
  jawab pakadna. 10 Sep pe coach ka code review karwana aur measured output maangna — wahi skill hai

### Phase 1 se Phase 2 kab shift hoga

Section 8 ke chaar leading indicators hit hone pe. Calendar se nahi. Agent log ke data se propose
karega.

System design abhi **third** priority hai — fresher/new-grad loops mein wo usually senior rounds
mein aata hai.

---

## 1. Why — ye plan aisa kyun hai

Poora plan **ek** measurement pe khada hai: 10 Sep 2026 ka session, Weekly 381 ke 3019 + 3020.

Us din ye hua:

| Observation | Iska matlab |
|---|---|
| 3020 (Q2) ka **poora logic khud derive kiya** — pattern, ones parity, `-1` rule, overflow | Knowledge **hai**. Sochna aata hai |
| Ek hi syntax galti (`freq()` vs `freq[]`) **6 baar** | Ungli ko syntax nahi pata. Working memory syntax mein bhar gayi |
| Pseudocode sahi likha, phir C++ mein `value *= value` **gayab** ho gaya | Working memory full thi, toh structure gir gaya |
| Apne code ko **ek baar bhi** khud dry-run nahi kiya | Coach ko compiler aur debugger dono bana diya |
| Counter-examples **saare coach ne banaye**, tune ek bhi nahi | Edge case generate karna develop nahi hua |
| Manual trace **do baar skip** kiya, verbal summary de diya | Gate 1 ka discipline nahi hai |

Aur ek aur cheez: **270 LeetCode problems already solved**, graphs tak. Par upar wali galtiyan 270
genuinely solve kiye hue problems ke baad nahi hoti. Honest read: un 270 mein se kaafi editorial ya
help ke saath nikle. Usse **recognition** banti hai ("ye maine dekha hai") par **production** nahi
("main ye khud likh sakta hoon").

### Isliye plan ka har hissa kyun hai

| Plan ka hissa | Kis observation ko address karta hai |
|---|---|
| **Scales** (roz 15 min syntax) | 6 baar wali syntax galti. Syntax reflex banega toh working memory logic ke liye free hogi |
| **Gates** (Socratic drill) | trace skip karna, aur bina cost gine shortcut sochna |
| **Gate 3 mein tere 3 counter-examples** | counter-example generate karna absent hai |
| **Gate 4 solo** (coach syntax nahi batata) | coach ko compiler banane wali aadat |
| **Mixed untagged problems** (topic batches nahi) | sheet problems pre-labeled aate hain, contest problems nahi. Recognition chahiye |
| **40-minute rule** (help se pehle) | 270 problems mein editorial shortcut lene wali aadat |
| **Friday blank re-solve** | "samjha" aur "seekha" ka farak — recognition vs recall |
| **Saturday contest, non-negotiable** | rating sirf contest se badhti hai, practice se nahi |
| **Sunday rest** | 3 hafte mein burnout se plan chhod dene wala failure mode |

Agar tujhe koi rule bekaar lage — upar table mein dekh ki wo kis measured galti se aaya hai.

---

## 2. Scales — roz, 15 min, non-negotiable

### Kya hai

Piano wala scales. Roz 15 minute **sirf syntax** — koi problem solve nahi.

### Kyun

10 Sep pe teri galti sochne ki nahi thi, ungli ki thi. Aur jab ungli sochti hai, dimaag ka logic
gir jaata hai — `value *= value` isliye gayab hua.

Dimaag ek waqt mein 4-5 cheezein hold kar sakta hai. Agar syntax unmein 3 slot le raha hai, toh
structure ke liye jagah nahi bachti. Isko **chunking** kehte hain — syntax reflex ban jaaye toh wo
ek slot leta hai, teen nahi.

### Kaise

1. Nayi khali file: `scales.cpp`
2. Notes band, browser band, purana code band
3. Neeche ki 8 cheezein **memory se** type karo
4. `g++ scales.cpp -o scales.exe` phir `.\scales.exe`
5. Error aaye toh error message **khud padho** aur fix karo
6. File delete kar do. Kal scratch se

### 8 cheezein

```cpp
// 1. map banao aur bharo
unordered_map<int,int> freq;
for (int x : {5,3,5,1,3}) freq[x]++;

// 2. count() se existence check
if (freq.count(5)) cout << "5 hai\n";

// 3. find() + end() se existence check
if (freq.find(9) != freq.end()) cout << "9 hai\n";

// 4. operator[] ka side effect
cout << freq.size() << "\n";
cout << freq[100] << "\n";     // 100 map mein nahi tha
cout << freq.size() << "\n";   // size badh gaya? khud dekho

// 5. range loop
for (auto& p : freq) cout << p.first << " -> " << p.second << "\n";

// 6. sort with lambda
vector<int> v = {5,2,9,1};
sort(v.begin(), v.end(), [](int a, int b){ return a > b; });

// 7. two-pointer skeleton
int l = 0, r = v.size()-1;
while (l < r) { l++; r--; }

// 8. prefix sum
vector<int> pre(v.size()+1, 0);
for (int i = 0; i < v.size(); i++) pre[i+1] = pre[i] + v[i];
```

Pehle din 25 min lagenge. Ek hafte mein 8 min. Do hafte mein bina sochne.

### Ye kab khatam hoga

**Ye permanent nahi hai.** 3-4 hafte baad, agar syntax errors per session `0-1` pe aa gaye — Scales
5 min pe cut ya band. Agent khud propose karega, log ke data se.

### List badalti rahegi

Jo galti mistake ledger mein **3 baar** aa jaaye, wo Scales mein add ho jaati hai. Agent roz batayega
aaj kaunsi 2-3 cheezein focus karni hain.

---

## 3. Problems kahan se laane hain

### Rule

**Roz ek purana contest ka Q1 (Easy) + Q2 (Medium).** Mixed, untagged, roz alag contest.

### Kaise

1. LeetCode → Contest → past contests
2. Koi bhi purana contest — **Weekly ~340-380 ya usse neeche**
3. Uska Q1 aur Q2 utha lo
4. Verify: problem page pe contest ka naam likha hona chahiye

### Do cheezein jo mat karo

**Recent contests (Weekly 400 aur upar) practice mein mat chhuo.** Wo Saturday virtual contests ke
liye reserved hain. Agar practice mein khatam kar diye, Saturday ke liye kuch unseen nahi bachega —
aur virtual contest ka pura point unseen hona hai.

**LeetCode ka "Topics" aur "Hint" section collapsed rakho.** Wo kholna Gate 2 ka jawab dekh lena
hai. Sheet practice ne tujhe ye muft de rakha tha; contest mein nahi milega.

### Topic batch kab hoga

**Upfront nahi.** Tere paas 270 problems ki knowledge hai — topic coverage tera bottleneck nahi
hai. Topic batch **reactive** hai:

> Log mein ek hi topic pe **3 failures** cluster ho jaayein → us topic ke **10 problems** ka batch →
> phir wapas mixed untagged.

Agent ye trigger log se khud dekhega aur propose karega. Tujhe track nahi karna.

### Problem tu pick karta hai, agent nahi

Kyun: agar agent problem chunega toh usko technique pehle se pata hogi. Phir Gate 2 mein "kaunsi
technique ki khushbu aa rahi hai" poochhna dikhawa hoga, aur uske sawaalon ka phrasing hi answer
leak kar dega. Agent ko **blind** rehna chahiye — tabhi uska counter-example genuine hai.

**Exception:** Friday. Wahan agent log se `pending` problems ke naam batayega, kyunki wo already
solved hain.

---

## 4. Din ke hisaab se — poora detail

### MONDAY / WEDNESDAY — Guided

```
15 min  Scales
60 min  Q1 (compressed gates) + Q2 (full 4 gates)
```

**Timer nahi.** Session 75 min pe khatam, chahe problem adhoori ho — agli guided din continue.

**Q1 (Easy) — compressed gates:**

| Gate | Kya |
|---|---|
| 1 | Ek line restatement + sample ka trace. **Trace mandatory hai** |
| 2 | Ek line: allowed complexity + max `n` |
| 3 | **1** counter-example |
| 4 | Poora review — tu code likhta hai, compile karta hai, dry-run karta hai, phir paste |

**Q2 (Medium) — full gates:**

| Gate | Kya | Kyun |
|---|---|---|
| 1 | Restatement + **poora manual trace**, step-by-step table | Tu fast padh ke misread karta hai. 3020 mein "subset" ko "substring" padha tha |
| 2 | Constraints ka **cost calculate** — actual number nikalna hoga | "bada hai" accept nahi hoga. 3020 mein bina cost gine 3 galat shortcut aaye |
| 3 | Plan 3-4 bullets + **tere 3 counter-examples**, phir agent ka counter-example | Tera counter-example count 0 hai. Ye gate wahi number move karta hai |
| 4 | Tu code likhta hai **solo**. Compile na ho toh agent errors nahi batayega | Tu agent ko compiler bana raha tha |

**Gate 4 ka exact flow:**

```
tu code likhta hai
   ↓
tu compile karta hai (g++ ya LeetCode Run)
   ↓  error aaya?  -> tu khud padh ke fix karta hai. Agent ek line bolega:
   │                  "compile nahi hoga, compiler ka error padh ke fix kar"
   ↓  compile ho gaya
tu apna code Gate 1 wale example pe KHUD dry-run karta hai
   ↓  output galat?  -> tu khud dhoondhta hai
   ↓  output sahi
NOW paste karo
   ↓
agent review karta hai: boundary, naming, plan->code fidelity
agent tera code .dsa_tmp/ mein compile+run karke MEASURED output deta hai
agent temp files delete karta hai
   ↓
Contest Takeaway (1 line)
```

---

### TUESDAY / THURSDAY — Timed

```
15 min  Scales
        PHASE 1 - MEASUREMENT (akela, agent se baat nahi)
          Easy  : timer on
          Medium: timer on
        PHASE 2 - CLOSE OUT (agent ke saath)
```

**Timer kitna?** Fixed number nahi. Rule: **aisa timer jisme ~30-40% problems solve ho jaayein.**
90% pass ho raha hai matlab problems bahut aasan; 10% matlab bahut mushkil. Agent log ke recent
results dekh ke roz batayega.

**Kyun 30-40%?** Kyunki ye CP practice ka established target hai — apni ability se thoda upar
practice karna. 90% pass ho raha hai toh tu comfort zone mein hai, kuch seekh nahi raha.

**Phase 1 ka exact flow:**

```
timer on
   ↓
timer khatam  -> HAATH UTHAO, turant. Chahe 1 line baaki ho
   ↓
2 min: likho kaunse gate tak pahuncha, kahan atka
   ↓
+15 min UNTIMED, phir bhi akela, koi help nahi
   ↓
result se diagnosis:
   "Gate 3 tak gaya, extension mein solve ho gaya"  -> tu SLOW hai. Speed pe kaam
   "Gate 2 pe tha, extension mein bhi Gate 2"       -> KNOWLEDGE GAP. Topic pe kaam
```

**Phase 2:** ab agent ke paas laao. Wahi problem guided mode mein **poora solve** hoga. Time nahi
bacha toh ye agle guided din ka Q2 ban jaayegi.

**Zaroori:** measurement **pehle** hota hai, isliye record honest rehta hai. "40 min mein Gate 2"
wala sach nahi badalta chahe baad mein solve ho jaaye.

**Metric:** timed din pe `solved: yes/no` bekaar hai. Metric hai **furthest gate reached** —
`Gate 1 / 2 / 3 / 4 / Solved`. Hafta 1 mein tu Gate 2 tak jaayega, hafta 6 mein Gate 4. Progress
dikhega chahe solve na ho.

---

### FRIDAY — Blank re-solve

```
15 min  Scales
60 min  Hafte ke 2 problems (1 Easy + 1 Medium) SCRATCH SE
```

**Kaise:** notes band, purana code band, editorial band, agent se help nahi. Bilkul zero se dobara
likhna.

**Kyun:** ye hafte ka sabse honest test hai. 3020 dobara likhoge — kya `-1` rule khud aayega? Kya
`1` ka case yaad aayega? Agar nahi aaya, wo **seekha nahi** tha, sirf **samjha** tha. Recognition
aur recall ka farak yahi pakadta hai.

**Timer nahi**, par ek problem 40 min se zyada le toh ruk jao.

**Result:**

```
blank se aa gaya   -> tracker mein "pass". Wo topic solid hai
nahi aaya          -> close-out mein solve karo, AUR status "pending" wapas
                      agle hafte phir blank test hoga
```

Ek baar solve karna bar nahi hai. **Blank se recall aana bar hai.**

---

### SATURDAY — Virtual contest + upsolve

```
15 min  Scales (warm-up)
90 min  Virtual contest, RECENT unseen contest (Weekly 400+), 4 problems
60 min  UPSOLVE
```

**Contest ke rules:** phone door. Koi extra tab nahi. Koi AI nahi. Koi editorial nahi. Jo aaya aaya.

**Upsolve kya hai:** jo problems contest mein nahi hui, unhe contest ke **turant baad** karna:

```
1. pehle SCRATCH SE try karo (15-30 min per problem, bina editorial)
2. phir editorial padho
3. phir core idea KHUD DOBARA implement karo — copy nahi
```

**Kyun upsolve sabse important hai:** ye hafte ka highest-value block hai. Strong competitive
programmers ka ye universal habit hai — contest ke baad 1-2 ghante disciplined upsolve. Contest
tumhe exactly wo problems deta hai jo tumhari current limit pe hain, aur upsolve us limit ko
aage dhakelta hai.

**Ye din non-negotiable hai.** Rating sirf contest se badhti hai. Roz practice karo par contest na
do — rating **exactly wahi** rahegi.

Baad mein agent ko do: rank, kitne solve, rating, aur ek line "time kahan gaya".

---

### SUNDAY — Postmortem + rest

```
Scales    — aaj nahi
30 min    — postmortem agent ke saath
baaki din — REST. Koi solving nahi
```

**Postmortem mein kya:** kya galat gaya, kaunsa pattern pehchana nahi, kahan time gaya, kya ek
cheez agle hafte badalni hai.

**Rest kyun plan ka hissa hai:** consolidation neend aur gap mein hoti hai, screen pe nahi. Sunday
bhi solve karega toh 3 hafte mein thak ke poora schedule chhod dega — aur wahi sabse common
failure mode hai. Rest chhutti nahi hai, training ka hissa hai.

---

## 5. "Agar aisa hua toh kya karna" — decision table

Ye section sabse zyada kaam aayega.

### Problem solve nahi ho rahi

| Situation | Kya karna |
|---|---|
| **Guided din, problem samajh nahi aa rahi** | Agent se poochho — par wo sawaal wapas karega, answer nahi. Ye by design hai |
| **Guided din, 75 min ho gaye, problem adhoori** | Session khatam. Log mein note. Agli guided din wahi problem continue |
| **Timed din, timer khatam, solve nahi hua** | Haath uthao. Gate note karo. +15 min untimed. Phir close-out |
| **Timed + extension dono mein solve nahi hua** | Normal hai, especially hafta 1-3. Close-out mein guided mode se solve hoga |
| **40 min ho gaye aur kuch bhi samajh nahi aa raha** | **Ab help allowed hai.** 40-minute rule cross ho gaya. Agent se hint le sakta hai (phir bhi wo sawaal ke roop mein hi dega) |
| **40 min se pehle help chahiye** | **Nahi.** Ye rule hi tera asli problem address karta hai. Chhoti problem pe shift karo ya `n = 2` ke liye haath se solve karo |
| **Ek problem 2 din se atki hui hai** | Band karo. Agent ke saath poora solve karo, log mein `knowledge gap` mark karo. Us topic ka failure count badhega |

### Code / syntax

| Situation | Kya karna |
|---|---|
| **Compile error aa gaya** | **Khud padho aur fix karo.** Agent errors enumerate nahi karega. Ye deliberate hai — tune usko compiler bana rakha tha |
| **Compile ho gaya par output galat** | Apne code ko Gate 1 wale example pe **khud trace karo**. Line by line. Agent ko paste karne se pehle |
| **Ek hi syntax galti baar baar** | Log mein count badhega. `3` cross karte hi wo Scales mein add ho jaayegi |
| **STL ka koi API yaad nahi aa raha** | Agent se **ek baar** poochh sakta hai — vocabulary free hai. Doosri baar wahi API poochha toh wo docs pe bhejega aur ledger mein daal dega |
| **Pata nahi kaunsa data structure use karu** | Ye vocabulary nahi, ye **outcome** hai. Nahi poochh sakta. `idk` likho aur try karo |

### Din miss ho gaya

→ Section 5B dekho.

### Performance signals

| Situation | Iska matlab | Kya karna |
|---|---|---|
| **Timed Easy 8 min ke andar, lagataar 3 baar** | Speed aa gayi | Easy `review-only` pe shift. Bacha time Q2 ko |
| **Syntax errors per session 0-1** | Scales ka kaam ho gaya | Scales 5 min pe cut ya band |
| **Friday blank pass rate 80%+** | Seekha hua hai | Difficulty badhao — Q2 se Q3 ki taraf |
| **90% timed problems pass ho rahe hain** | Problems bahut aasan | Timer kam karo ya harder problems |
| **10% timed problems pass ho rahe hain** | Bahut mushkil | Timer badhao. Panic nahi |
| **Ek hi topic pe 3 failures** | Real knowledge gap | Us topic ka 10-problem reactive batch |
| **Tere counter-examples agent se zyada bug pakad rahe hain** | Gate 3 develop ho gaya | Gate 3 compress karo |

### Motivation / thakan

| Situation | Kya karna |
|---|---|
| **Bahut thak gaya, aaj nahi ho payega** | Sirf Scales karo, 15 min. Streak bach jaayega, load nahi padega |
| **6 hafte ho gaye, koi progress nahi dikh raha** | Log kholo aur numbers dekho — feeling pe bharosa mat karo. Chunking silent hoti hai. Agar 4 leading indicators mein se ek bhi move nahi hua, tab plan galat hai aur badalna chahiye |
| **Lag raha hai ye sab rule bekaar hai** | Section 1 ka table dekho — har rule ek measured galti se aaya hai, opinion se nahi |

---

## 5B. Gap handling — bas itna

Structure **kabhi nahi badalta**: roz 2 problems, guided/timed schedule wahi.

| Situation | Kya |
|---|---|
| Kal nahi ho payega (kahin jaana hai, Relay heavy) | Agent ko bata do. Wo din skip. Bas |
| Wapas aa gaya | Aaj ke **weekday** ka normal kaam. 2 problems, wahi mode |
| Catch-up | **Nahi.** Miss hua din gaya. Kabhi 4 problems ek din mein nahi |
| Exams / travel — lamba gap | Pehle se bol do ("18-28 Sep frozen"). Agent log mein mark karega, missed days nahi ginega |
| Lamba gap ke baad pehla Medium fail | Ye **warm-up loss** hai, skill loss nahi. Agla din normal |
| Bahut thak gaya, 15 min hi hai | Sirf Scales. 0 se better |
| Saturday contest miss | Agle available din kar lo — iska substitute nahi hai |

**Timeline:** `6-10 hafte` 6 problems/hafta pe. Kam karega toh lamba hoga — agent actual rate se
recompute karega, purana number repeat nahi karega.

---

## 6. Ye chaar rules kabhi nahi todne

**1. Gate 4 solo.** Compile error agent se nahi poochhna. Compiler 2 second mein batata hai aur us
error message ko padhna contest mein kaam aata hai.

**2. Plan se pehle tere 3 counter-examples.** Gate 3 mein plan ke saath 3 aise test bhejne hain jo
tere plan ko tod sakte hain. Ye number `0` hai abhi. Yahi gate usko move karta hai.

**3. Paste karne se pehle apna dry run.** Jo example Gate 1 mein trace kiya, usi pe apna **code**
trace karo. 10 Sep pe tu ek baar bhi ye nahi kiya.

**4. 40 minute se pehle koi help nahi.** Editorial, hint, agent — kuch nahi. Ye seedha tere 270
problems wale pattern ko address karta hai.

---

## 7. Kaun kya karta hai

| Kaam | Tu | Agent |
|---|---|---|
| Problem chunna | ✅ (Friday chhod ke) | ❌ blind rehna hai |
| Din/mode/timer decide karna | ❌ | ✅ date + log se |
| Trace, plan, counter-examples | ✅ | poochhta hai |
| Code likhna | ✅ | ❌ kabhi nahi |
| Compile + syntax fix | ✅ | ❌ deliberately |
| Apne code ka dry-run | ✅ | ❌ |
| Code review (logic, boundary, naming) | ❌ | ✅ |
| Tera code compile+run karke measured output | ❌ | ✅ `.dsa_tmp/` mein, phir delete |
| Counter-example se attack | ❌ | ✅ tere 3 ke baad |
| Drill log update | ❌ | ✅ roz, khud |
| Progress numbers track karna | verify karna | ✅ likhna |

---

## 8. Progress kaise naapna

**Hafte ginne se kuch pata nahi chalta.** Ye chaar number dekh:

| Indicator | Target | Abhi (10 Sep) |
|---|---|---|
| Timed Easy ka time | 8 min ke andar, lagataar 3 baar | not recorded |
| Syntax errors per session | `0-1` | bahut |
| Friday blank pass rate | 80%+ | 0 (abhi shuru nahi hua) |
| Tere counter-examples jo bug pakde | agent se zyada | 0 vs 4 |

Chaar hit ho gaye toh Q1+Q2 reliable hai, chahe hafta 6 ho ya 12.

**Expected timeline** (270 problems ki knowledge base count karke):

| Kab | Kya |
|---|---|
| Hafta 1-3 | Scales se syntax settle. Timed days pe fail hona normal |
| Hafta 4-6 | Q1 consistent. Q2 kabhi-kabhi |
| Hafta 6-10 | **Q1+Q2 reliable.** Rating `1650-1750` |

Condition: Saturday contests miss nahi hone chahiye, aur 40-minute rule tootna nahi chahiye. Dono
mein se ek toot gaya toh timeline `3-4 mahine` ho jaayega.

**Rating ke baare mein ek honest baat:** rating **sirf contest dene se** badhti hai. Roz practice
karo aur contest na do — rating exactly wahi rahegi. Aur LeetCode ka rating moving average hai,
asli skill dikhne mein 5-8 contests lagte hain. Toh hafta 3 pe rating dekh ke conclusion mat
nikalna.

---

## 9. Confusions jo already aa chuki hain

**"Days kaise count honge? Mujhe track karna hai?"**
Nahi. Agent ko system se date aur weekday milta hai. Schedule weekday ke naam se hai, koi
"Day 1, Day 2" counter nahi. Tu bas "aaj kya karna hai" poochh.

**"Nayi chat mein context paste karna padega?"**
Nahi. Agent prompt aur drill log dono auto-load hote hain. Kuch paste nahi karna.

**"Scales 15 min ka hai, toh solve kab karunga?"**
Scales warm-up hai, uski jagah nahi. `75 min = 15 Scales + 60 solving`. Sunday chhod ke roz solve
hota hai.

**"Problem agent dega?"**
Nahi, tu dega. Sirf Friday pe agent naam batayega (already solved problems hain).

**"Timed din pe solve nahi hua toh guided pe shift ho jaun?"**
Nahi. Guided timed ke **baad** aata hai, uski jagah nahi. Warna measurement khatam.

**"Koi problem adhoori chhodni hai?"**
Nahi. Har problem eventually solve hoti hai. Sirf timing badalti hai — measurement pehle, close-out
baad mein.

**"Ye sab rule chochle hain? Log aise karte hain?"**
Aadha. **Core validated hai** — har contest + upsolve, ~30-40% success rate wali difficulty,
postmortem notes, blank/spaced recall, editorial se pehle genuine attempt. Ye sab established CP
practice hai.
**Ceremony meri thi** — gates, Scales, drill log. Ye scaffolding hai, permanent nahi. Strong log ye
implicitly 60 second mein karte hain. Tere liye justified hai kyunki tu trace skip karta hai aur ek
syntax galti 6 baar karta hai. Jaise jaise wo theek hoga, ye scaffolding hategi. Agent ko bola hai
ki khud propose kare kab hataana hai.

---

## 10. Kal ka kaam (11 Sep, Friday)

```
15 min  Scales — focus: freq.find() vs freq[], aur post-loop logic ki placement
60 min  Blank re-solve:
          3019 Number of Changing Keys   (Easy)
          3020 Max Elements in Subset    (Medium)
        Notes band. Purana code band. Scratch se.
```

Dekhna hai: 3020 mein `-1` rule aur ones-parity blank se aata hai ya nahi.

**Aur ek verification:** nayi chat kholke `dsa-coach` agent select karo, "aaj kya karna hai" likho.
Agar wo 3019 aur 3020 ke naam leta hai — drill log theek load ho raha hai. Agar sirf "blank re-solve
karo" bol ke ruk gaya — mujhe batao, path fix karna padega.
