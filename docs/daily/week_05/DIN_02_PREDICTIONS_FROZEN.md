# Week 5 Din 2 — FROZEN PREDICTIONS

## Q1 (Step 1 se pehle)
Handler `25 s` chalta hai, HEARTBEAT_INTERVAL_SECONDS = 10, aur DB claim ke `3 s`
baad marta hai. Worker marega ya nahi? Agar marega, to `worker.py:305` (mark) se
PEHLE ya BAAD me? Ek line number ya ek function ka naam likho.
Aur: us job ka `claimed_at` claim ke waqt ka hoga, ya kisi heartbeat ne usko aage
badhaya hoga?

### Prediction
worker nai marega bcz 25 second ka kaam hai wo handler chalta rahega or kaam khtam krega but heart beat down hai to fi rjab finnaly block mai jayega kaam khtam krne to await chalega heartbeat or wo to behosh padi hai to waha error handl enai kiya apan en to waha dikkat krega or mark ke pehele marega ye nai heart beat ne usko nai padhaya wahi same rahega claim ai to

## Q2 (Step 2 se pehle)
Maano tu mark ko retry karta hai jab tak DB wapas na aaye.
Retry ke DORAN job ki lease ka kya hota hai — kaun usko refresh kar raha hai?
Aur agar ek reaper zinda hai aur lease expire ho jaati hai: wo job ko reclaim kar
lega ya nahi? Agar haan, to jab DB wapas aaye aur tera retry ka UPDATE chale, uska
`rowcount` kya hoga, aur worker kaunsi line print karega — `Mark fenced` ya
`Conflict on mark`? Ek chuno, aur mechanism likho.

### Prediction
reaper ane ke baad wapis pending h ojayega but han rowcount 0 hi rahega and fenced ho jayega wo

## Q3 (Step 3 se pehle)
Dispatcher HTTP `200` le chuka hai. `dispatched_at` set ho gaya hai object pe, par
COMMIT abhi nahi hua. Ab DB marta hai.
Boundary lagane ke BAAD: `outbox` row `dispatched` hui ya nahi? Recovery ke baad wo
row dobara deliver hogi ya nahi? Aur `outbox.attempts` ka number sahi hoga ya kam?
Aur: delivery ka at-least-once property preserve hua, kharab hua, ya waisa hi raha?

### Prediction
apan ne reveiiver idempotency lagaya hai to at leas once to rahege hi exaclty once nai possible um idk or to

## Q4 (Step 4 se pehle)
Supervisor lag gaya. Worker aur reaper dono ek `25 s` outage me marte hain.
`restart_to_first_claim` ka ek number likho, aur `restarts` ka ek number likho.
Aur doosra half, jo number nahi hai: Step 2 ke baad worker poll, mark AUR heartbeat
teeno pe guarded hai. To supervisor ko fire karne ki koi wajah bachi hai? Agar haan,
to kaunsi — naam se ek failure.

### Prediction
idk

## Q5 (Step 5 se pehle)
Boundary ab maujood hai. `pool_pre_ping=True` ke saath, wahi `~25 s` outage pe,
`poll_failures` `5` se `4` hoga, `0` hoga, ya waisa hi rahega? Mechanism likho.
Aur per-checkout cost ka ek number `ms` me likho.
Aur teesra: `pre_ping` kal ki DO maut (mark pe aur heartbeat pe) me se kisi ko
bachata hai? Haan/nahi, aur kyun.

### Prediction
poll faliour mai change syaeg but minor hi miliseconds ka bcz extra query chalit hai sleect 1 usme han of c bachata hai
