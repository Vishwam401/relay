## Q1
Handler side_effects row aur outbox row EK HI session me insert karta hai, phir COMMIT se PEHLE os._exit(1). DB me kitni rows hongi (dono tables), aur side_effects_id_seq / outbox_id_seq ka last_value kya hoga? Do cheezein alag likho: row count, aur sequence value.

### Prediction
dono table pai ek ek row hogi commit se pehele mara hai na to ofc row to ban chuki thi ..and duja ki rollback ho jayega jab fail ya esa kuch hua to badhega nai

### Observed + meri explanation


### After KEY


## Q2
Dispatcher HTTP 200 le chuka hai aur dispatched_at mark karne se pehle mar jaata hai. Reaper outbox ko nahi dekhta (src/reaper.py sirf Job.status == 'running' padhta hai). Wo row dobara KAB uthegi, aur usko dobara uthane wala mechanism KAUNSA hai? Agar koi mechanism nahi hai to wahi likho.

### Prediction
idk

### Observed + meri explanation


### After KEY


## Q3
Receiver ka dedup OFF hai, wahi crash (HTTP 200 ke baad, mark se pehle). sink_deliveries me kitni rows, aur side_effects me kitni? Do numbers alag-alag likho, aur kyu.

### Prediction
dedup off hai to 2 bar ho jayega (sink_deliveries me 2 rows)

### Observed + meri explanation


### After KEY


## Q4
Do dispatcher process ek hi backlog pe, SELECT ... FOR UPDATE SKIP LOCKED + WHERE dispatched_at IS NULL, READ COMMITTED. Ek row do baar deliver ho sakti hai ya nahi — aur agar haan, to exactly kis sequence me? (Sochne se pehle ye tay karo: HTTP call transaction ke ANDAR hai ya BAHAR — jawab dono ke liye alag hai, aur dono likho.)

### Prediction
idk

### Observed + meri explanation


### After KEY


## Q5
HTTP call transaction ke ANDAR hai. Receiver 30 s ke liye respond nahi karta. Uss dauran uss dispatcher ke pool ka kya haal hai, aur pg_stat_activity me wo backend kis state me dikhega? Aur ek doosra hissa: wo "30 s" actually 30 s hoga ya nahi?

### Prediction
idk

### Observed + meri explanation


### After KEY

