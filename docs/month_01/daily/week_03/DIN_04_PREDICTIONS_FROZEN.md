# Week 3 Din 4 — Answers & Predictions

## Q1 — Unkeyed Requests / Opt-out Uniqueness

**Question:** jobs.idempotency_key nullable aur UNIQUE hai. Same body ke do POST, dono key omit karte hain. Final rows 1 hongi ya 2? PostgreSQL mechanism naam se likho.

### Prediction — frozen before the step
idk

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q2 — Sequential Replay, Sequence Movement & Conflict Surface

**Question:** Same non-null key ka sequential replay atomic INSERT path tak pahunchta hai. jobs count aur jobs_id_seq ke baare me separately predict karo. Integrity conflict Python/SQLAlchemy me execute, flush, ya commit me kahan surface hoga—apne chosen implementation ke liye exact bolo.

### Prediction — frozen before the step
idk

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q3 — Genuine Concurrent Race & Transaction Wait

**Question:** Do identical keyed POST genuinely concurrent hain; winner commit se pehle 5 s trigger me held hai. Loser immediately answer karega ya wait? pg_stat_activity me expected wait_event_type/wait_event kya hai, aur final row count kya hoga?

### Prediction — frozen before the step
idk

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q4 — Key Reuse With Different Content / Fingerprint Contract

**Question:** Same key pe pehle type=sleep,payload={a:1,b:2}; phir type=sleep,payload={a:1,b:3}. Sirf original job_id return kar dena kis correctness bug ko create karta hai? Fingerprint me type aur payload dono kyu hone chahiye, aur JSON object-key order ka kya?

### Prediction — frozen before the step
idk

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q5 — Aborted Transaction, Failed Session & Constraint Scope

**Question:** IntegrityError catch karne ke baad rollback se pehle usi AsyncSession par original row SELECT kar sakte ho? SQLAlchemy/PostgreSQL kis failed-transaction behavior se rokta hai? Har IntegrityError ko replay treat karna kyu unsafe hai?

### Prediction — frozen before the step
idk

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]

---

## Q6 — Enqueue UNIQUE vs Execute UNIQUE Coexistence

**Question:** Enqueue UNIQUE ship hone ke baad side_effects.effect_key UNIQUE hata sakte hain? Ek client-retry case aur ek lease-reclaim case se derive karo.

### Prediction — frozen before the step
idk

### Observed + meri explanation
[PENDING RUN]

### After KEY
[PENDING KEY]
