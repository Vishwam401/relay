## Q1
completed_at - claimed_at ko latency maana jaaye, aur handler 45 s ka ho jisme heartbeat har 10 s pe claimed_at = now() likhta hai (yielding handler, lease kabhi expire nahi hoti). Computed latency kya aayegi, aur wo asli execution time se kitni alag hogi? Number likho, aur mechanism.

### Prediction
idk

### Observed + meri explanation

### After KEY

## Q2
last_error me poora Python traceback jaata hai. Worker ka poll SELECT jobs ki rows uthata hai par last_error ko SELECT list me nahi maangta. Poll ka disk I/O badhta hai ya nahi — aur AGENTS.md rule 34 ke hisaab se KIS EXACT CONDITION me badhta hai? (Do alag cases hain; dono likho.)

### Prediction
idk

### Observed + meri explanation

### After KEY

## Q3
Ek job retry hoti hai: attempt 1 fail (last_error likha), attempt 2 succeed. Attempt 2 ke baad row me last_error kya hoga? Ye behaviour tumhare implementation ka faisla hai — likho ki tum kya CHAHTE ho, aur phir kya HOGA agar tum aaj ke mark UPDATE me last_error ko chhedte hi nahi.

### Prediction
idk

### Observed + meri explanation

### After KEY

## Q4
Run 2: type=effect, payload {"seconds": 45, "block": true}, lease 30 s, SIGBREAK at T = 3 s, reaper live, generation gate lagi hui, EK worker. T = 50 s par teen cheezein:
(a) worker process zinda hai ya exit kar gaya?
(b) row ka status kya hai?
(c) completed_at set hai ya NULL — aur worker ka mark accept hua, `fenced` hua, ya `conflict` hua?

### Prediction
idk

### Observed + meri explanation

### After KEY

## Q5
Run 3: wahi Run 2, par ab DO worker hain aur doosre ko SIGBREAK nahi mila. Us job ke liye job_executions me kitni rows hongi, aur side_effects me kitni? Do numbers alag-alag likho, aur kyu.

### Prediction
idk

### Observed + meri explanation

### After KEY
