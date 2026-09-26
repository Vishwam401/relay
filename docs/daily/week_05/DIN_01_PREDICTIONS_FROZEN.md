# Week 5 Din 1 — FROZEN PREDICTIONS

## Q1 (Step 2 se pehle)
Postgres down hone ke DO moment hain: (a) connection pehle se open thi aur toot gayi,
(b) nayi connection banane ki koshish refuse hui.
Kya SQLAlchemy dono pe ek hi exception class deta hai? Agar nahi, to kaunsi kaunsi?

### Prediction
dono mai alag error fekega shyd buthan interface erorr hi dega mere khayals e to but still dkehte hai chlao

## Q2 (Step 3 se pehle)
Claim poll me exception pakdne ke baad, agar main session pe kuch NA karu aur seedhe
loop continue kar du — DB wapas aane ke baad agla `session.execute()` chalega ya nahi?
Agar nahi, to kya error aayega?

### Prediction
are ofc cleam kr lega apan ne erorr pakda usi liye haio handle tabhi kiya taki manualy apan ko na cmd dena pade ye apne ap claim kr lega db ane ke baad

## Q3 (Step 4 se pehle)
Ek `25 s` ke outage me, `POLL_INTERVAL_SECONDS = 2.0` ke saath, `poll_failures` ka
number kya hoga? Ek number likho, range nahi.
Aur: DB start hone ke baad PEHLA poll success hoga ya wo bhi fail hoga? Kyun?

### Prediction
11 12 jitni fail hogi claim query and db start hone ke baad to fail nia hogi

## Q4 (Step 5 se pehle)
Do arms — (i) catch ke baad turant retry, (ii) catch ke baad POLL_INTERVAL wait.
Kaunsa arm `recovery_to_first_claim` kam dega, aur uska cost kya hai?
(Cost ek number hona chahiye ya ek naam, "load badhega" nahi.)

### Prediction
idk

## Q5 (Step 6 se pehle)
Handler khatam, side effect COMMIT ho gaya, aur mark se PEHLE DB chala gaya.
Boundary lagane ke BAAD: is job ka `attempts` kitna hoga jab wo eventually
`succeeded` hota hai? Aur `side_effects` me kitni rows?

### Prediction
attempt 2 hoga but side effcet atble mai ek hi row rahegi
