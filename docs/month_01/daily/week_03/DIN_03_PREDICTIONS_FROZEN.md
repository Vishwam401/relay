# DIN 3 — Answers & Predictions

**Week 3 · Din 3: 🎯 Crash side effect ke BEECH me**

> **Provenance Rule:**
> Har question ke neeche teen permanent blocks hain.
> 1. `### Prediction — frozen before the step` (Step run hone se pehle freeze; never edit).
> 2. `### Observed + meri explanation` (Output dekhne ke baad, KEY kholne se pehle).
> 3. `### After KEY` (Reviewer KEY verify karne ke baad).

---

## Q1 — Pre-Mark Crash Par Job Row Ki State

**Question:** Side effect commit ho gaya, mark se pehle worker mar gaya. jobs me row kis state me hai? Aur ye state Week 2 ke kis entry me already likhi hui hai?

### Prediction — frozen before the step
Job ka status running hi reh jayega bcz wo success mark nahi kar paya. Aur second part ka exact entry number nahi pata, but thoda pata hai ki ek worker aisa tha ki usne job execution mark kar diya tha but fir bhi running reh gaya tha.

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q2 — Reclaim Ke Baad Side-Effect Count

**Question:** Uss row ko reaper reclaim karega. Naya worker handler dobara chalayega—side effect count 1 rahega ya 2 hoga? Tumhara jawab Din 2 key ke scope par depend karta hai; dependency likho.

### Prediction — frozen before the step
Count 1 hi rahega bcz apan ne unique constraint lagaya hai. Koi aur worker wo same job leke aayega toh detect ho jayega aur usko skip (dedup) kar denge ignore. Dependency: Din 2 ka unique constraint feature jo apan ne lagaya hai.

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q3 — Side-Effect Aur Mark Ek Hi Transaction Me Kyu Nahi?

**Question:** Side effect aur mark ek hi transaction me hote to middle crash state exist nahi karti. To wo ek transaction me kyu nahi hain? Do reasons aur ek external side effect likho.

### Prediction — frozen before the step
idk

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q4 — Recovery Ke Baad Dedup vs No-Replay Distinction

**Question:** Recovery ke baad count 1 do wajah se aa sakta hai—dedup, ya handler dobara chala hi nahi. Kaunsa ek number in dono ko separate karta hai?

### Prediction — frozen before the step
job_executions table se pata chal jayega ki job again kisi worker ne chalayi ya nahi (job_executions ka count).

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q5 — os._exit() vs raise — "Worker Mar Gaya" Kehna Kyu Galat Hai?

**Question:** os._exit() aur raise—dono ko “worker mar gaya” kehna kyu galat hai? Handler-level aur post-mark placement ko separately reason karo.

### Prediction — frozen before the step
raise exception mai toh aisa hai ki wo pehle kaam khatam karega / exception handle karega then jayega, aur doosre (os._exit) mai toh turant marega (immediate hard process termination).

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q6 — Teen Crash Cases Ke Final Attempts

**Question:** Teen crash cases ke final attempts kya honge, aur D-23 increment-on-claim se kaise derive hote hain?

### Prediction — frozen before the step
Case A: 1, Case B: 1, Case C: 0 shayad.

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]
