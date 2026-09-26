## Q1
Step 1 (fencing se pehle) me worker A 45 s blocking handler pe hai, reaper ne 30 s pe reclaim kiya, B ne claim kiya. A wapas aakar WHERE status = 'running' se succeeded mark karta hai. Uss instant ke baad row ka (status, attempts, next_attempt_at) kya hoga, aur B ka handler jab khatam hoga to uska mark kya karega?

### Prediction
Pehle agar worker A block hua toh status 'running' par atka rahega aur attempt 1 hoga. Jab worker B aayega tab rowcount 0 hi rahega (uska kaam ignore hoga), aur worker A seedha running ko success karega.

### Observed + meri explanation

### After KEY

## Q2
Claim CAS me RETURNING claim_generation vs claim ke baad ek alag SELECT claim_generation — in dono ke beech ek window hai. Wo window kis cheez ko allow karti hai?

### Prediction
Jaise hi window khuli, worker 1 ne update kiya row ko, par beech mein dooja koi aayega wo bhi update karega row ko kyunki worker A ka read/select complete nahi hua tha, toh usko bhi purana wala status dikhega aur dono concurrent ho jayenge waha gadbad hogi.

### Observed + meri explanation

### After KEY

## Q3
job_executions.claim_generation ko NOT NULL DEFAULT 0 banaya jaaye to purani rows me kya likha jaayega, aur kaunsi future query uss value se galat jawab degi?

### Prediction
NOT NULL isliye taaki pehle wo column nahi thi toh error na aaye, aur purani rows mein 0 default rakhenge.

### Observed + meri explanation

### After KEY

## Q4
Agar effect_key ke andar claim_generation chala jaaye, to Din 1 Step 4 ke run me select count(*) from side_effects where job_id = <id> kya dega? Aur kyu?

### Prediction
2 hi aayega because job_id par query lagaya hai humne generation par thodi.

### Observed + meri explanation

### After KEY

## Q5
Reaper ke reclaim UPDATE me generation nahi badhaya, aur queue khaali hai (koi doosra worker claim nahi karta). Stale worker A wapas aata hai. Uska mark accept hoga ya fenced?

### Prediction
idk (abhi mujhe generation and ye nahi pata, aaj seekhunga)

### Observed + meri explanation

### After KEY
