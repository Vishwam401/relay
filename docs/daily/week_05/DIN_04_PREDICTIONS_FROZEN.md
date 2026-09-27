# Week 5 Din 4 — FROZEN PREDICTIONS

## Q1 (Step 1 se pehle)
Pool RELAY_POOL_SIZE=2, RELAY_MAX_OVERFLOW=0 set kar ke uvicorn chala.
(a) src/database.py ka import-time print kya likhega — exact shape.
(b) Koi request bhejne se PEHLE, pg_stat_activity me us application_name ke
    liye kitne rows honge — ek number.
(c) Teen concurrent /slow-hold ke DORAN kitne rows honge — ek number.
(d) Aur asli sawaal: (a) ka output (c) ke number ko prove karta hai ya nahi?
    Ek aisa scenario likho jisme print `pool=2+0` kahe aur process fir bhi
    2 se ZYADA connections hold kare. Agar aisa scenario possible nahi hai,
    to likho kyun nahi.

### Prediction
idk

## Q2 (Step 2 se pehle)
pool_size=2, max_overflow=0, pool_timeout=3.0. Teen concurrent
/slow-hold?seconds=8.
(a) Teesra request ka HTTP status code kya hoga — ek number.
(b) Wo kitni der me return karega — ek number, aur likho wo kis cheez se
    bandha hai: pool_timeout, seconds, ya kuch aur.
(c) Exception ka class name kya hoga — poora naam.
(d) Aur: agar RELAY_POOL_TIMEOUT set NA karta (default 30.0), to (b) ka
    number kya hota? Week 4 Din 5 ne 3.0055 s report kiya tha — us din
    pool_timeout kya raha hoga?

### Prediction
idk

## Q3 (Step 3 se pehle)
Pool saturated hai (do /slow-hold chal rahe hain).
(a) /healthz kya karega — 200, hang, ya error? Aur kitni der?
(b) /health kya karega? /db-ping kya karega? Teeno ka jawab same hai ya nahi?
(c) Aur asli sawaal: ek failing /healthz ke teen causes hain — pool starvation,
    DB down, process dead. Kaunsi EK observation pool starvation ko baaki do se
    alag karti hai? Naam se likho.
(d) Us observation ka D-28 ke "liveness, not readiness" label pe kya asar hai?

### Prediction
idk

## Q4 (Step 4 se pehle)
Ek /slow-hold?seconds=20 bheja, aur client ko 3 s baad maar diya.
(a) Server pe pg_sleep ruk jaayega ya chalta rahega? Haan/nahi aur mechanism.
(b) Pooled connection pool me kab wapas aayegi — 3 s pe, 20 s pe, ya kabhi nahi?
(c) pg_stat_activity disconnect ke turant baad us session ka state kya
    dikhayega — ek shabd.
(d) Iska /slow-hold?seconds=100000 ke liye kya matlab hai — ek line.

### Prediction
idk

## Q5 (Step 5 se pehle)
Ek asyncpg connection ne sink_deliveries me key K insert ki aur transaction
khuli rakhi. Do outbox rows ka job_id same hai, to dispatcher dono ke liye wahi
K mint karega. Sink ka pool 2+0 hai. Dispatcher chalu hai.
(a) Dispatcher ka pehla dispatch attempt kitni der me kya dega? Error class
    aur latency.
(b) Kaunsa timeout pehle firega — httpx ka 5.0 s, ya sink ka pool_timeout?
    Aur wo farak Relay ke logs me kis shakal me dikhega?
(c) Outbox row ka FOR UPDATE lock kitni der held rahega — aur kya wo HTTP
    timeout ke saath release hota hai? Mechanism.
(d) Aur asli sawaal: jo error Relay ke log me aayegi, usko padh kar kya tu
    asli cause (receiver ke DB me ek uncommitted row ka lock) tak pahunch
    sakta hai? Haan/nahi. Agar nahi, to kaunsi ek line log me hoti to
    pahunch jaata?

### Prediction
idk
