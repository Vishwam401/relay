<!--
  Week 4 Din 5 — ANSWERS / frozen prediction card template.

  HOW TO USE THIS FILE (Step 0C):
    1. Sirf `### Prediction` blocks bharo. Apne head se, KEY kholne se PEHLE, Gemini se poochne se PEHLE.
       `idk` ek valid answer hai aur wo `0` score karta hai — ek guess ko knowledge ki tarah likhna usse bura hai.
    2. `### Observed + meri explanation` aur `### After KEY` freeze ke waqt KHAALI rehne chahiye.
       Step 0C ka seal command inhe check karta hai aur non-empty hone pe `throw` karta hai.
    3. Freeze karo (Step 0C). Wo is file ki ek immutable copy DIN_05_PREDICTIONS_FROZEN.md banata hai.
       Us copy ko phir kabhi chhoona nahi. Ye file (ANSWERS) din bhar badalti rehti hai.
    4. Har step ke measurement ke TURANT BAAD uss question ka `### Observed + meri explanation` bharo —
       pehle apni explanation, phir Gemini ke saath output pe reason karo. Din ke ant me nahi, tab bhool jaate ho.
    5. USKE BAAD KEY ka relevant section kholo aur `### After KEY` bharo.
    6. Din ke ant me is file ke END me ek `## Total Score` section ADD karo — freeze ke waqt wo maujood
       NAHI hona chahiye, warna wo Q5 ke `### After KEY` block ka hissa ban jaata hai aur seal command
       usko non-empty samajh ke `throw` karega.

  DIN 4 KA SABAK, AUR AAJ YE SABSE ZAROORI LINE HAI:
    Score sirf DIN_05_PREDICTIONS_FROZEN.md ke text ka hota hai. Kal Q2 ka outcome sahi tha aur mechanism
    sirf `### Observed` me likha gaya tha — us se score 1.0 ke bajaye 0.5 hua, aur Q4 me 0.5 ke bajaye 0.25.
    Total 2.25 se 1.5 correct hua. TO: prediction me MECHANISM likho — kaunsa timer, kaunsa predicate,
    kaunsi library default. Sirf outcome likhna aadha score hai.

  Aur ek naya rule: jahan jawab ek measurement hai, wahan "ye naapna hai, aur uska bound X hai" likhna
  POORA credit deta hai. Ek plausible number bhar dena credit nahi deta.

  Question ka poora text BRIEF ke Part B me hai. Yahan short form hai taaki cards ordered rahein.
  Structure ko badalna nahi — seal command `## Q1..Q5` order aur teeno headings exactly maangta hai.
-->

## Q1
`pool_size=2, max_overflow=0`, `pool_timeout=30`. `50` concurrent users `POST /jobs` maar rahe hain.
(a) Client ko kya milega — `500`, ek timeout, ya slow `202`?
(b) **Pehla** error kitni der me, aur wo error kis **layer** se aayega — Postgres se ya application se?
(c) Handler ka DB kaam `5 ms` ka hai. `50` users ke liye `2` connections **kaafi** hain? Apni arithmetic likho.

### Prediction
(a) Slow 202 ya timeout/error milega; slow worker hai to time to lagega kaam karne me, handler kaam karte time lock lagata hai to koi aur pool aayega isko skip karke doosra job le lega.
(b) Pehla error 30 second me aayega, application pool layer exhaust ho jayega.
(c) 5ms me ek kaam ho raha to 50 ke liye 250 ms lagega, aur 2 pool me bat jayega wo time (250/2 = 125 ms jitna time lagega 50 user ko serve karne me agar DB har ek ke liye 5 ms le raha hai to; kaafi hai).

### Observed + meri explanation


### After KEY


## Q2
Paanch process, har ek `create_async_engine` default pe (`pool_size=5, max_overflow=10`).
(a) **Idle** state me Postgres pe kitne connections dikhenge?
(b) Load pe kitne?
(c) `max_connections` ke against safe hai ya nahi — aur **kaunsa** number yahan use kiya, ceiling ya observed?

### Prediction
(a) Idle state me Postgres pe 5 connection dikhenge.
(b) Load pe 15 dikhenge.
(c) idk.

### Observed + meri explanation


### After KEY


## Q3
Ek worker, handler `0.1 s`, `POLL_INTERVAL_SECONDS = 2.0`.
(a) Theoretical max throughput jobs/sec me? **Arithmetic likho**, aur batao `2.0 s` usme aata hai ya nahi.
(b) Enqueue rate `20`/s pe `pending` count kaise behave karega?
(c) Agar `pending` flat rehta hai — iska matlab throughput `20`/s se zyada hai, ya kuch aur bhi ho sakta hai?

### Prediction
(a) Poll interval judega bcz wo har 2 second me jata hai, 2 second wait karega handler aaya usne utha ke kaam kiya. Manle 2 second pehle handle aaya hai aur poll to interval me baitha hai aur kaam sirf 0.1 second ka tha to uske interval ki wajah se latency badhegi (poll interval 2.0s usme aayega).
(b) idk.
(c) idk.

### Observed + meri explanation


### After KEY


## Q4
`docker compose stop db` while a worker is mid-`SELECT`.
(a) Worker crash karega ya exception pakad ke poll karta rahega? Aur `MAX_ATTEMPTS` iss raaste pe **lagta hai ya nahi**?
(b) DB wapas aane ke baad **pehli** query ka kya hoga, `pool_pre_ping` ke **bina**?
(c) DB down thi `20 s`; uss dauran ek row `running` thi jiska worker bhi mar gaya. **Wo row kab `pending` hogi, aur kaun karega?**

### Prediction
(a) idk.
(b) idk.
(c) idk.

### Observed + meri explanation


### After KEY


## Q5
`/healthz` `SELECT 1` karta hai, usi engine ke pool se, aur pool `pool_size=2` pe hai. Load ke peak pe dono
connections `POST /jobs` ke paas hain.
(a) `/healthz` ka response kya hoga, aur **kitni der** me?
(b) Ek orchestrator jiska liveness probe `/healthz` pe hai — wo kya karega?
(c) Iss ek interaction se kaunsa **naya** failure mode paida hota hai jo `/healthz` ke bina exist nahi karta?

### Prediction
(a) idk.
(b) idk.
(c) idk.

### Observed + meri explanation


### After KEY


