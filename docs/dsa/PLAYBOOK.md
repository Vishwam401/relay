# DSA Playbook — do track, ek app

Ye file **tere** liye hai. Rules aur unke reasons yahan hain.

- `PLAYBOOK.md` (ye file) — kyun. Rules, tradeoffs, aur kya cut kiya.
- `DRILL_LOG.md` — kya hua. Numbers aur history.
- **Algo-Path app** (`D:\PROJECTS\Algo-Path DSA`) — **aaj kya karna hai.** Wo authoritative hai.

> Aaj ka plan is file mein nahi hai. App kholo, batao aaj kitne minute hain, plan bana hua milega.
> Wo live progress se derive hota hai. Ye file wo batati hai jo app nahi bata sakti — **kyun**.

Goal wahi hai: **OA clear karna.** Easy 8-10 min, Medium 20-25 min, reliably. LC `1600-1700`.
CP rating nahi. Iska poora reasoning section 6 mein hai.

---

## 1. Ek page mein

```
ROZ — app mein minute daalo, plan khud banega

  blocks priority order mein aate hain, aur ye order hi poora design hai:
    1  skeleton     warm-up, trigger phrase se blank file mein type
    2  review       FIXED commitment — due recall + re-solve + park se wapsi
    3  blind        TRACK A — kholo, padho, predict, phir 8 station · 60 min budget
    4  log          cause code + kis minute pe idea aaya
    5  fast         pehle solve ki hui problems, timer on
    6  implement    jo "mind-solved" chhoda tha
    7  acquire      TRACK B — naya pattern. SABSE AAKHIR MEIN, aur backlog >= 4 pe BAND

  Sunday    rest — 30 min postmortem, koi solving nahi
  Saturday  contest + upsolve
  kharab din  60 min floor: skeleton + 1 blind + log. YE COUNT HOTA HAI
```

---

## 2. Do track, do **ulti** rules — ye playbook ka core hai

Do strong practitioners exactly opposite advice dete hain, aur dono sahi hain, kyunki dono alag
cheez optimize kar rahe hain:

| | [Um_nik](https://codeforces.com/blog/entry/98806) | [Practice guide](https://codeforces.com/blog/entry/116371) |
|---|---|---|
| Editorial | **kabhi nahi.** Fail hui problem 1 mahine baad wapas | **15-30 min soch, phir padh lo** |
| Kya train hota hai | khud se solve karna | naye concepts ki **rate** |

Resolution, aur ye teri hi baat se nikla hai — *"old pattern mein hustle kar sakta hu, new mein
intuition bithane mein struggle"*:

```
TRACK A — COVERED patterns
  Concept already pata hai. Editorial kuch NAYA nahi sikhata, sirf recognition rep jala deta hai.
  => No editorial. Atak gaya toh PARK. 30 din baad blind wapas aayega.

TRACK B — NAYE patterns
  Concept genuinely naya hai. 3 ghanta standard technique dobara-invent karna bura trade hai.
  => 20-30 min soch, phir padh lo. Par chaar gates paas karo, warna baad mein dobara seekhna padega.
```

*Content licensing ke liye rephrase kiya gaya.*

---

## 3. Chaar gates — Track B ka "wapas na karna pade" ka jawab

Tere covered patterns ko redo karna pad raha hai kyunki wo **sirf ek direction mein** seekhe gaye:
`pattern → question`. Contest `statement → pattern` chalata hai. Gates wahi missing direction add
karte hain.

| Gate | Kab | Kya | App kahan |
|---|---|---|---|
| **G1 derive** | Day 0 | `coreMove` **padhne se pehle** BRUTE / WASTE / KILL likho. Galat hona allowed | pattern card, reveal se pehle |
| **G2 trigger** | Day 0 | canonical trigger **dekhne se pehle** apna likho | wahi form |
| **G3 skeleton** | Day +1 | trigger phrase se skeleton **type** karo, blank file, compile | pattern card ke neeche |
| **G4 blind** | Day +7 se +10 | unlabeled problem pe **kholne se pehle** pehchano | Track A se |

**G4 hi asli gate hai.** Baaki teen support hain. G4 tak nahi pahuncha toh pattern acquired nahi hai,
chahe teeno question tick ho.

App ab yahi count karti hai. Header mein `acquired` aur `ungated` dono dikhte hain — `ungated` matlab
"tick hai, gate nahi". **Wahi teri asli re-do list hai, aur uska size wahi teri asli problem ka size
hai.**

---

## 3B. Station map — ek problem ke andar aath jagah

"Atak gaya" ek state nahi hai, aath hain. Aur aath mein se **paanch pe kuch padhna galat move hai.**
App ek station live rakhti hai, aur do exit deti hai: `ho gaya` ya `atak gaya`.

| # | Stall | Time | Karo | Mat karo |
|---|---|---|---|---|
| 1 | Statement samajh nahi aayi | 8m | Sample **haath se** trace karo. **Trace likhna mandatory hai** — bina uske station 1 chhoot nahi sakta | Pattern guess karna |
| 2 | Brute force nahi aa raha | 8m | Brute **enumeration** hai, cleverness nahi. O(n^3) bhi chalega | Optimal dhoondhna |
| 3 | Waste nahi dikh raha | 6m | `n=3` pe brute chalao aur steps **gino** | Dimaag mein loop karna |
| 4 | Kill nahi aa raha | 10m | "Dobara dekhna" ko O(1) kaun banata hai — map/prefix/stack/heap/memo? | Statement dobara padhna |
| 5 | Approach hai, code nahi ban raha | 10m | Plan ko **numbered comments** mein, phir neeche bharo | Seedha likhna shuru |
| 6 | Code chala, galat answer | 10m | Failing test pe **khud dry-run**, comments ke against | Random badal ke resubmit |
| 7 | Code sahi, par TLE | 8m | Kill galat tha — **station 3 pe wapas** | Micro-optimisation |
| 8 | H4 ke baad bhi nahi | — | **Park.** Valid terminal state | Aaj hi khatam karna |

**Jahan minute jama hote hain wahi tera asli gap hai.** App `station_log` rakhti hai. Zyadatar time
station 2 pe gaya toh gap brute-force enumeration hai, pattern knowledge nahi — aur dono ka kaam
bilkul alag hai.

### Station 1 pe trace mandatory kyun hai

Ye station pehle button dabane se clear ho jaata tha, jo kuch prove nahi karta. Do cheezein kehti
hain ki yahi station sabse zyada sakht hona chahiye:

- Contest literature: **galat answer ki sabse badi wajah statement misread karna hai**, algorithm gap
  nahi ([faceprep](https://faceprep.in/article/how-to-approach-a-competitive-programming-question-face-prep/)).
- Tera apna baseline: `3020` pe "subset" ko "substring" padha tha. `[MEASURED]`

Aur tere **purane** playbook mein "manual trace mandatory" tha — ye build usko chup-chaap gira chuka
tha. Audit mein pakda gaya aur wapas daala. Gate **server** pe lagta hai, sirf disabled button nahi —
disabled button suggestion hai, gate nahi.

*Content licensing ke liye rephrase kiya gaya.*

### Hint ladder — chaar rung, time + station dono se gated

| Rung | Deta hai | Rokta hai | Khulta hai |
|---|---|---|---|
| **H1** family | window / hash / BS / stack / greedy / DP | approach | `8m` + station 1 |
| **H2** waste | brute kya dobara kar raha hai | kill | `20m` + station 2 |
| **H3** structure | actual kill ka naam | code | `32m` + station 4 |
| **H4** editorial | poora | kuch nahi | `50m` + station 4 |

Gate **server** pe lagta hai — tera bheja hua level trust nahi hota. Aur **dono** condition chahiye,
sirf time nahi: warna problem khol ke ek ghanta gayab hone se poori ladder khul jaati.

Purana rule *"editorial sirf C6 pe, warna kuch nahi"* **bahut binary tha.** Research kehti hai
productive failure aur productive struggle mein farak support ke **timing** ka hai, uski absence ka
nahi — poora withhold karna unproductive struggle deta hai, jo kuch nahi sikhata. Rungs wahi beech
ka rasta hain.

---

## 3C. Circuit breakers — kab sheet khud bole "ruk, plan badal"

Har breaker pe number, aur **instruction**. Number laal ho jaana kuch nahi badalta.

| Breaker | Trigger | Kya hota hai |
|---|---|---|
| **problem-leech** | ek problem `2` baar fail | Wo problem band. Usi idea ki **aasan** problem aayegi |
| **idea-wheelspin** | ek idea `3` baar fail, alag problems pe | Us idea ke blind band. anchor → skeleton → **labeled** problem |
| **hint-creep** | last 10 mein `>50%` ne H3/H4 liya | Band `-100`. **Solve rate se pehle** dikhta hai |
| **band-slide** | solve rate `<30%` | Band `-100`. Normal correction, kuch karna nahi |
| **floor-breach** | solve rate `<20%` **aur** band `1200` pe | **Blind ek hafta BAND.** Sirf labeled + FAST |
| **park-flood** | parked `>40%` of attempts | Band `-100` **aur** naya pattern band |
| **burnout** | `3` din miss, ya `5` floor din | Naya pattern band, blind slot `1`. Catch-up nahi |
| **stall** | `3` hafte mein dono headline number flat | *Plan galat hai.* Postmortem, aur **sirf ek** cheez badlo |

**`floor-breach` aur `park-flood` wo do hain** jo tere sawaal ka jawab hain — "low rating ke bhi nahi
ho rahe, sab bucket mein jaa raha hai". Us waqt app **khud** blind band kar deti hai. Tujhe decide
nahi karna.

Aur jab breaker rokta hai, **problems sach mein nahi aate.** Banner dikha ke phir bhi problems dena
decoration hota; kaam rok dena hi intervention hai.

### Ye numbers kahan se aaye

- **`2` lapses** — Anki `8` lapses pe card suspend karta hai. Ek problem flashcard se bahut mehnga
  hai, toh `2` uska equivalent hai. Logic wahi: **baar baar fail hona matlab material galat hai**,
  reps kam nahi. [Anki manual](https://docs.ankiweb.net/leeches.html)
- **`3` fails per idea** — ITS literature mein ise **wheel-spinning** kehte hain: bahut practice ke
  baad bhi mastery nahi. Aur published response **alag strategy** hai, zyada reps nahi — zyada reps
  hi wheel-spinning hai. [EDM](https://files.eric.ed.gov/fulltext/ED599222.pdf)
- **Method badalna, volume nahi** — Bloom ka mastery learning **method aur time dono** vary karta
  hai, sirf time nahi.

*Content licensing ke liye rephrase kiya gaya.*

---

## 4. Chhe cause, ek dawa nahi

*"Editorial dekh ke laga itna aasan tha, mere dimaag mein kyun nahi aaya"* — ye symptom hai, aur chhe
alag failures isko produce karte hain. Teeno abhi tak ek hi dawa mili hai: "aur problems karo".
Isliye kuch move nahi hua.

| Code | Kya hua | Iska fix |
|---|---|---|
| **C1** | Brute force hi nahi likha | BRUTE line mandatory |
| **C2** | Brute tha, **waste nahi dikha** | WASTE line pe rukna |
| **C3** | **Reframe miss** — ulta, pairs mein, endpoint fix | reframe ledger |
| **C4** | Invariant / monotonicity check nahi kiya | "operation ke baad kya constant hai?" |
| **C5** | Pattern pata tha, detail galat | comments-first + skeleton reps |
| **C6** | Technique hi nahi pata thi | **sirf yahan editorial theek hai** |

Har fail hui problem pe **ek hi** code. App usko `attempts.cause` mein rakhti hai. ~20 rows baad
distribution bata dega kahan kaam karna hai — **ye naapna hai, predict nahi karna.** Mera guess C2 +
C3 hai aur wo `[INFERRED]` hai, measured nahi.

---

## 5. Kya cut kiya, aur kyun

Ye section sabse zaroori hai, kyunki purana playbook padhke confusion hogi.

| Cut hua | Kyun |
|---|---|
| **40-minute rule** ("koi help 40 min se pehle nahi") | Ek hi number dono tracks pe lagta tha. Track A mein 40 min bhi kam hai — wahan editorial hi allowed nahi. Track B mein 40 min bekaar wait hai jab concept hi naya hai. Track-specific rule ne isko replace kiya |
| **"Koi problem adhoori nahi chhodni"** | Ye seedha Um_nik ke ulta tha, aur yahi wo rule tha jo editorial kholne pe majboor karta tha. Ab: Track A mein fail = **park**, 30 din baad blind wapas. Editorial sirf C6 pe |
| **New problems pe timer** | Timed din pe naye problems pe timer lagta tha. Wo dono kharab karta hai — time pressure solve attempt corrupt karta hai, aur speed build nahi hoti kyunki solution pata hi nahi. Ab timer sirf FAST block mein, **pehle solve ki hui** problems pe |
| **`retire pattern` = 3 checkbox** | Completion naapta tha, recall nahi. Chaar gates ne replace kiya |
| **Recall = "bas bolo"** | Card khula rakh ke pattern ke baare mein bolna kuch test nahi karta. Ab recall = skeleton blank se **type** karo |
| **`TARGET_DAYS = 90`** | Code ka comment khud admit karta tha ki 2-patterns-per-day sirf 3-mahine ke target ke liye tha. Deadline ne load decide kiya, capacity ne nahi — aur wahi burnout ka source tha. Ab 1 pattern/din, aur calendar `[MEASURED] 127 din` pe girta hai |
| **Scales = STL API drill** | Galat target. Mistake ledger ke top 2 (dono count 6) mein ek `plan→code` hai, API nahi. Ab skeleton drill hai — 22 skeletons, prompt **trigger phrase** hai, aur har ek pe `trap` likha hai: wo exact line jo memory se type karne pe gayab hoti hai |

---

## 6. DSA kyun, aur kab tak

**Goal MNC OA clear karna hai. CP nahi.**

```
DSA        = FILTER          OA. Isse pass hue bina koi interview hi nahi hoga
Debugging  = DIFFERENTIATOR  later rounds. Yahan offer banta ya tootta hai
```

OA ka bar: 70-90 min mein 4 ka 3, mostly Easy/Medium. Yani **Easy 8-10 min, Medium 20-25 min,
reliably.** Rating terms mein `1600-1700`, `1900` nahi.

App ka blind band `1400-1600` se shuru hota hai aur measured solve rate se upar chadta hai. Target
band pe pahunchna hi Phase 1 khatam hone ka signal hai.

**Relay iss plan ka doosra half hai.** Debugging round mein exactly ye poochha jaata hai: "ye code
kya karta hai, kahan toot sakta hai, tumne ye design kyun chuna". Relay ke `DECISIONS.md` /
`PROBLEMS.md` us round ka answer hain. Relay pe kaam interview prep se alag nahi hai.

### Phase shift kab

Section 7 ke chaar indicators hit hone pe — calendar se nahi. Tab DSA maintenance pe (2-3 din/hafta +
Saturday contest) aur weight Relay + system design + debugging practice pe.

---

## 7. Progress kaise naapna

**Hafte ginne se kuch pata nahi chalta.** Ye chaar number dekh — teeno naye hain, aur teeno app khud
bharti hai:

| Indicator | Target | Abhi |
|---|---|---|
| **Blind hit rate** — prediction sahi nikli | measure karna hai, pehle 20 attempts | not recorded |
| **Time-to-first-idea** ka median | girta hua | not recorded |
| **Hint level** — H3/H4 ka share | girta hua | not recorded |
| Blind band ka centre | `1600+` | `1400` (cold start) |

> **Yahan se do indicator HATA diye gaye:** *"syntax errors per session `0-1`"* aur FAST ke
> *"Easy 8 min, Medium 20 min"*. Audit mein pata chala ki `attempts.syntax_errors` aur
> `attempts.fast_seconds` dono columns hain jinme **koi code kuch likhta hi nahi** — FAST block mein
> timer hi nahi hai. Jis indicator ka data source nahi hai, wo list mein rehna bura hai: wo dekh ke
> conclusion nikalta hai jo kisi cheez pe khada nahi. Jab timer banega, tab wapas aayenge.

**Solve rate jaanbujh ke list mein nahi hai.** Teri volume pe wo bahut noisy hai, aur band khud usko
`30-40%` pe hold karta hai — toh wo number hil nahi sakta chahe tu kitna improve kar le. Blind hit
rate aur time-to-first-idea hil sakte hain. Wahi dekh.

**Pehla hafta: sirf naapna. Kuch change nahi karna.** 15 problems, blind mode, teen cheez per
problem: cause code, time-to-first-idea, blind hit. Apna solving style badalna mat. Kyun: tu already
teen baar system redesign kar chuka hai bina data ke, aur `git log docs/dsa` mein ek hi commit hai
(`2026-09-11`). `[MEASURED]`

---

## 8. Chaar rules jo nahi todne

**1. Prediction code se pehle — problem se pehle nahi.** Teen step hain: problem kholo → statement
padho → **phir** trigger + idea + BRUTE/WASTE/KILL seal karo → tab code likho.

> Pehla version galat tha aur usko badal diya gaya. Wo BRUTE/WASTE/KILL **problem dene se pehle**
> maangta tha, jo impossible hai — wo teeno statement se **derive** hote hain. Rating number dekh ke
> BRUTE likhna kuch naap hi nahi raha tha.
>
> "Blind" ka matlab hai **problem pe koi pattern label na ho.** Wo feed ki property hai (zerotrac
> mein tags nahi hote), UI gate ki nahi. Jo seal hona chahiye wo prediction hai, aur wo **code se
> pehle** hoti hai. Ab `blind_hit` zyada meaningful hai: *statement padh ke sahi pattern pehchana?* —
> wahi contest skill hai.

**2. Track A mein editorial nahi.** Sirf C6. Baaki paanch causes mein answer pahunch mein tha, aur
padh lena rep jala deta hai. Park karo.

**3. Reveal se pehle apna trigger.** G2 timestamp compare karta hai. Baad mein likhna copy hai, aur
app usko count nahi karegi.

**4. Rest din rest hai.** Sunday solving nahi. Consolidation neend aur gap mein hoti hai. Teen hafte
7-ghante ke baad 2 hafte zero = net zero, aur wo do baar ho chuka hai.

---

## 9. Agar aisa hua toh

| Situation | Kya karna |
|---|---|
| Bahut din gap ho gaya, sab late dikh raha hai | App ke "Aaj" tab pe banner aayega — ek click, saare khaali din rest ban jaayenge, plan aage khisak jaayega. Backlog banta hi nahi |
| Aaj sirf 1 ghanta hai | App mein `60 min` daalo. Floor plan milega: skeleton + 1 blind + log. **Ye count hota hai** |
| Blind problem pe atak gaya | 30-40 min genuine, phir **park**. Editorial nahi. 30 din baad wapas aayegi aur tab tak tu badal chuka hoga |
| Naye pattern pe kuch samajh nahi aa raha | 20-30 min baad editorial theek hai — par pehle G1 (BRUTE/WASTE/KILL) likh ke reveal karo, warna gate jal jaayega |
| Review backlog bada ho gaya | App khud naya pattern band kar degi (`>= 4` due pe). Force mat karo |
| Rating feed nahi mil raha | Track A band, baaki blocks chalenge. Net check |
| 6 hafte ho gaye, progress nahi dikh raha | Section 7 ke chaar number dekho, feeling pe nahi. Agar blind hit rate aur first-idea dono nahi hile, **tab plan galat hai** aur badalna chahiye |

---

## 10. Kaun kya karta hai

| Kaam | Tu | App | Coach |
|---|---|---|---|
| Aaj ka plan | minute batana | ✅ generate | ❌ |
| Blind problem chunna | ❌ | ✅ deterministic, reroll nahi | ❌ |
| Prediction, derive, trigger | ✅ | seal karti hai | ❌ |
| Code likhna | ✅ | ❌ | ❌ kabhi nahi |
| Compile + syntax fix | ✅ | ❌ | ❌ deliberately |
| Cause code assign karna | ✅ | store karti hai | review mein challenge karega |
| Counter-example se attack | ❌ | ❌ | ✅ tere 3 ke baad |
| Numbers track karna | verify | ✅ | padhta hai |

Coach ka kaam ab **naapna aur challenge karna** hai, plan batana nahi — wo app karti hai.
