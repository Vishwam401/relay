<!--
  Week 4 Din 6 — ANSWERS / frozen prediction card template.

  HOW TO USE THIS FILE (Step 0C):
    1. Sirf `### Prediction` blocks bharo. Apne head se, KEY kholne se PEHLE, Gemini se poochne se PEHLE.
       `idk` ek valid answer hai aur wo `0` score karta hai — ek guess ko knowledge ki tarah likhna usse bura hai.
    2. `### Observed + meri explanation` aur `### After KEY` freeze ke waqt KHAALI rehne chahiye.
       Step 0C ka seal command inhe check karta hai aur non-empty hone pe `throw` karta hai.
    3. Freeze karo (Step 0C). Wo is file ki ek immutable copy DIN_06_PREDICTIONS_FROZEN.md banata hai.
       Us copy ko phir kabhi chhoona nahi. Ye file (ANSWERS) din bhar badalti rehti hai.
    4. Har step ke baad uss question ka `### Observed + meri explanation` bharo.
    5. USKE BAAD KEY ka relevant section kholo aur `### After KEY` bharo.
    6. Din ke ant me is file ke END me ek `## Total Score` section ADD karo.

  AAJ KA ASUL:
    Aaj koi library behaviour nahi naapna. Aaj ke paanch sawaal tumhare hi hafte ke evidence,
    logs, DECISIONS.md, aur PROBLEMS.md pe khade hain. Mechanism likho — kaunsa job id,
    kaunsa number, kaunsa problem card.
-->

## Q1
Din 5 ka delta 0 expected hai kyunki poora din disposable DBs pe chala.
(a) Agar wo 0 nahi nikla, to sabse likely cause kya hai — aur usko git / psql se exactly kaise pakdoge? Ek command likho.
(b) Chain ke kaunse bucket pe 0 expect karna hi galat hai, aur kyun?
(c) Chain ka total match kar jaaye par ek line galat ho — ye kaise possible hai, aur uska naam kya hai?

### Prediction
idk

### Observed + meri explanation

### After KEY

## Q2
Promise #2: duplicate execution ≠ duplicate side effect.
(a) Verdict kya hoga — protected, narrowed, ya [NO EVIDENCE]?
(b) Uska scope statement exactly kya hoga? Ek vaakya likho jo overclaim na ho.
(c) Local effect aur external delivery ka verdict ek hai ya alag? Agar alag, to dono likho.

### Prediction
idk

### Observed + meri explanation

### After KEY

## Q3
Promise #1: accepted job is never silently lost.
(a) Din 5 ka Postgres-down run isko protected banata hai ya nahi? Aur 202 ka semantics iss jawab me kaise aata hai?
(b) Ek failure naam se likho jo isko todta hai aur jo iss hafte test nahi hua.
(c) Ek job jo running thi aur DB down thi — uske pending hone ka bound kya hai? Bound likho, ek number nahi.

### Prediction
idk

### Observed + meri explanation

### After KEY

## Q4
D-29 = leader election nahi kiya. Uska strongest rejected alternative Postgres advisory lock hai.
(a) Usko honestly maarne ke liye kaunsa Din 5 ka number chahiye tha?
(b) Wo number aaj maujood hai ya nahi?
(c) Agar nahi hai, to D-29 ka Rejected field exactly kya kehna chahiye? Ek vaakya likho.

### Prediction
idk

### Observed + meri explanation

### After KEY

## Q5
README ke failure matrix me har row ka evidence cell bharna hai.
(a) Kaunsi row aisi hogi jiska evidence cell [NO EVIDENCE] likhna padega? Naam se likho.
(b) Uss row ka Recovery mechanism cell kya kehta hai — aur wo cell [NO EVIDENCE] hone ke baad bhi bhara ja sakta hai ya nahi?
(c) Agar tumhe lagta hai ki koi row [NO EVIDENCE] nahi hogi, wo bhi likho — aur Step 3B pe check karo.

### Prediction
idk

### Observed + meri explanation

### After KEY
