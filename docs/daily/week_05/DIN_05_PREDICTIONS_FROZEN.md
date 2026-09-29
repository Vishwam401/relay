# Week 5 Din 5 — FROZEN PREDICTIONS

## Q1 (Step 2 se pehle — arm A)
(a) Din 4 pe API ki pehli DB request 0.17 s thi aur baaki milliseconds me.
    Sink ki PEHLI uncontended /deliver baaki nau jaisi hogi, ya pehli wali
    mehngi padegi? Mechanism ek line me — src/sink.py padh ke.
(b) Holder 3 s ka. job:42 wali direct POST kitni der me, kis status ke saath
    lautegi — ek number, aur wo number kis cheez se bandha hai.
(c) Wait ke dauran poll file me sink_w5d5 ki row: state, wait_event_type,
    wait_event — teen shabd. Aur pg_blocking_pids me kiska pid hoga?
(d) Wait ke dauran sink ke apne log me us request ke baare me kya likha hoga?
    Aur holder ke rollback ke baad sink kya print karega — applied ya duplicate?

### Prediction
idk

## Q2 (Step 3 se pehle — arm B, holder anchor ke 6 s baad khatam)
(a) holder_end se pehle kitne dispatch attempts sink tak pahunchenge? Ek number,
    aur har attempt anchor ke lagbhag kitne second baad shuru hoga.
(b) Attempt 1 ke liye outbox row 1 ka lock kitni der held rahega, aur kis
    statement pe khatam hoga? (src/dispatcher.py — ye padh ke nikalta hai.)
(c) Holder rollback hone pe job:42 ki INSERT kis request ki land karegi —
    attempt 1 ki ya attempt 2 ki? Aur data me kaunsa column padh ke tu ye
    decide karega?
(d) Final: outbox row 1 ka attempts aur dispatched_at. Aur Relay ki
    "[dispatch] ... status=dispatched" line — kya wo us request ke baare me
    hai jisne effect apply kiya?

### Prediction
idk

## Q3 (Step 4 se pehle — arm C, holder anchor ke 20 s baad khatam)
(a) Anchor + 12 s pe poll file me kitne sink_w5d5 sessions
    wait_event_type = Lock pe honge? Ek number, aur kyun wahi number.
(b) In 20 s me dispatcher ke log me kaunsi result-line shapes aayengi, kis
    order me? ("[dispatch_error] ... error=" / "[dispatch_failed] ...
    status_code=..." / "[dispatch] ... status=dispatched")
(c) "QueuePool limit ... timeout 3.00" kahin aayega? Kis process ke log me,
    aur pehli baar anchor ke lagbhag kitne second baad?
(d) P-41 kehta hai: "two dispatch attempts stalled behind one slow
    sink_deliveries writer exhaust the pool, and the symptom surfaces as
    pool_timeout in Relay". Run se pehle is sentence ko apne shabdon me
    dobara likho — kaunsa pool, kis process ka, kitne dispatchers chahiye.

### Prediction
idk

## Q4 (Step 6 se pehle — supervised fleet, 35 s outage, backlog)
(a) Outage ke dauran supervisor kitni baar restart karega? Ek number, aur
    Din 1–2 ke measured record se derive karo.
(b) Jo job outage shuru hote waqt handler me tha (sleep 1.0), uska final
    attempts kya hoga — aur usko 'running' se wapas kaun laayega? Log lines
    ke naam se raasta likho.
(c) Backlog ke BAAKI jobs me se kisi ka attempts > 1 hoga? Haan/nahi aur kyun.
(d) P-53(d) ka backoff defect (>= 5 s uptime pe reset) — is run me exercise
    hoga ya nahi? Kyun?

### Prediction
idk

## Q5 (Step 6 se pehle — API, usi outage ke dauran)
(a) Outage ke dauran /health, /healthz, /db-ping — teeno ka status.
(b) /healthz ka latency outage ke dauran Din 4 ke saturated 3.03 s se
    distinguishable hoga? Pehla failing sample aur baad wale — same ya alag?
(c) Pool starvation ko DB down se alag karne wali EK observation kaunsi hai —
    aur kya ek HTTP prober usko dekh sakta hai?
(d) DB wapas aane ke baad pehla /healthz — 200 ya 500? (D-31:
    pool_pre_ping = False.)

### Prediction
idk
