# Backend Systems Roadmap

**Theme 1: Reliable Background Execution**
Scope: sirf backend systems. DSA aur open-source iss doc me nahi hain (unke alag plan).

---

## 0. Ye doc kaise use karna hai

Ye ek roadmap hai, checklist nahi. Roz subah isko kholo, current week ka section padho, aur **aaj ka ek task** uthao.

Teen rules:

1. **Ek waqt pe ek layer.** Aage ka section padhne ka man kare toh mat padho. Wahi "samandar" wali feeling wapas laata hai.
2. **Padhna aur banana same hafte me.** Jo chapter padha, usi hafte usko code me utaro. Warna wo knowledge 2 hafte me chali jayegi.
3. **Har hafte likhna zaroori hai.** Code adhura ho sakta hai, writeup nahi. Resume pe code nahi jaata, writeup jaata hai.

---

## 1. Layer Map — main kaha hu

Backend ek chain nahi hai (jaise ABCD → words → essay). Ek graph hai. Par usme rough layers hain, aur yahi mera syllabus hai:

| Layer | Kya hai | "Aa gaya" ka test |
|---|---|---|
| **L0 — Machine** | process, thread, async, signals, file descriptors, sockets, TCP, disk | "`kill -9` pe kya kho sakta hai aur kyu" bata sakun |
| **L1 — Ek process, ek DB** | transactions, isolation levels, locks, MVCC, indexes, N+1 | write skew khud reproduce kar sakun |
| **L2 — Do cheezein baat kar rahi hain** | timeouts, retries, at-least-once, idempotency, dual-write, outbox | "ye request do baar aa gayi toh?" ka jawab design me pehle se ho |
| **L3 — State ek se zyada jagah** | caching + invalidation, replication lag, consistency models, CDC | stale read ka scenario khud bana sakun |
| **L4 — Scale aur ops** | partitioning, load balancing, backpressure, observability, capacity | load test se bottleneck predict kar sakun |

**Dependency:** L0 → L1 → L2. Uske baad L3 aur L4 mostly parallel.

**Meri current position:**
- L1 ka bada hissa aa gaya (transactions, locks, conditional updates use kiye hain)
- L2 me ghus chuka hu **bina L0 ke** — isliye phisalta hu
- L3 ko tools ke through chhua hai (Redis cache lagaya) par samjha nahi
- L4 abhi nahi

**Toh target: L0 patch karo → L2 pe kaam karo.** Do cheezein. Samandar nahi.

---

## 2. Core mental models

Ye teen models har jagah lagenge. Inhe yaad rakhna, roz use karna.

### 2.1 Infra ke 4 roles — brand name bhool jao

Har infra component in 4 roles me se ek nibhata hai:

| Role | Kaam | Ye gira toh |
|---|---|---|
| **Store** | Truth rakhta hai | Data gaya |
| **Cache** | Copy rakhta hai | Sirf slow |
| **Queue** | Kaam transfer karta hai A → B | Naya kaam accept nahi hoga |
| **Coordinator** | Kaun-kya-karega decide karta hai (locks, leader) | Split brain / duplicate work |

**Redis charo roles nibha sakta hai — aur teen me bura hai.** Yahi 90% confusion ka source hai.

Jab bhi socho "Redis use karu?", pehle poocho: **"kaunse role me?"** Kyunki tradeoff role ka hota hai, tool ka nahi.

> Docker iss list me nahi hai. Wo infra component nahi, **packaging** hai. Uska koi runtime tradeoff nahi jo design badalta ho. Buzzword list se hata do.

### 2.2 Har component pe ye 5 sawaal maaro

Kisi bhi naye tool pe ye lagao, aur wo buzzword se **decision** ban jayega:

1. **Ye kya guarantee deta hai, aur kya nahi?**
   Celery at-least-once deta hai, exactly-once nahi → *duplicate execution mera problem hai, Celery ka nahi.*
   Redis default me durability nahi deta → restart pe data ja sakta hai.

2. **Ye gira toh system degrade karega ya die karega?** (= blast radius)
   Redis as cache → slow par chalta rahega. Redis as broker → background kaam ruk gaya. Redis as source of truth → data gaya.
   *Same tool, teen bilkul alag blast radius — sirf role badalne se.*

3. **Do copies chal gaye toh kya hoga?**
   Do worker ne same task uthaya → do email? do charge? Agar haan → idempotency key chahiye.
   *Ye ek sawaal 90% real-world bugs pakad leta hai.*

4. **Data do jagah hai toh sync kaise rahega?**
   Cache + DB. Payment gateway + DB. Beech me crash → **dual-write problem** → jawab outbox pattern.

5. **Load badhne pe pehle kya tootega?**
   Connection pool? Queue depth? Redis memory (`maxmemory-policy` kya hai)?
   *Ye tab tak guess hai jab tak load test nahi chalaya.*

### 2.3 Tradeoffs kitaab se nahi, failure se aate hain

Ye sabse important realization hai. Tool ko wahan use karna jahan wo kaam kar jaye — usse kuch samajh nahi aata. **Samajh tab aati hai jab wo tootta hai.**

Toh: **jaan bujh ke todo.** Har experiment 15 minute ka hai.

| Experiment | Kya seekhunga |
|---|---|
| `docker compose stop redis`, phir API hit karo | Code Redis pe hard-depend karta hai ya gracefully degrade karta hai |
| Cache khali karke 200 requests ek saath | Cache stampede / thundering herd, aur request coalescing ki zarurat |
| Worker ko task ke beech me `kill -9` | At-least-once ka asli matlab. Task dobara chalega? Side effect duplicate? |
| Worker ko `SIGTERM` bhejo | Graceful shutdown vs hard kill ka farq |
| `docker compose stop postgres` while API running | Connection pool behaviour, retry storm, error propagation |
| Postgres pool 2 connections pe limit karke load | Pool exhaustion kaisa dikhta hai, latency kaise phatti hai |
| Do terminal, do transactions, ek row | Isolation levels, lost update, write skew — apni aankho se |
| 10k jobs ek saath enqueue | Queue depth behaviour, backpressure ki zarurat |

**Har experiment ke baad 2 line likho:** kya expect kiya, kya hua.
15 aise experiments ke baad main infra tradeoffs pe first-hand baat kar sakta hu — Medium article se rata hua nahi.

> Ye interview ka bhi content hai. "Redis down hone pe kya hoga?" ka jawab jab "maine actually kiya tha, ye hua tha" ho — wo round jeet leta hai.

---

## 3. Week 0 — L0 Patch (4-5 din, kal se shuru)

**Kyu:** meri saari "Redis/Celery ke tradeoffs samajh nahi aate" wali confusion **ek layer neeche se** aa rahi hai. Tool ka tradeoff samajhne ke liye pata hona chahiye ki machine pe kya ho raha hai.

Ye gap **finite hai** — 10-12 ghante ka kaam. Poora OS course nahi.

### Din 1 — Process, thread, async

- Ek process me kya shared hota hai, kya nahi (memory, fd table)
- Thread vs async: dono concurrency dete hain, par kaise alag
- **Blocking call actual me kya karta hai** (syscall → kernel wait → thread ruk gaya)
- Event loop kaise ek thread me hazaar connections handle karta hai

**Verify karo (code likh ke):**
- [ ] Ek async function me `time.sleep(5)` daalo, 3 concurrent requests bhejo → 15s lagega. Phir `asyncio.sleep(5)` → 5s. Ye khud dekho.
- [ ] Samjhao (likh ke) ki `run_in_executor` kyu chahiye tha blocking SDK call ke liye.

### Din 2 — Signals aur process death

- `SIGTERM` vs `SIGKILL` — kaunsa trap ho sakta hai, kaunsa nahi
- Graceful shutdown ka matlab: in-flight kaam khatam karo, naya accept mat karo
- Ye directly job runner ke liye chahiye

**Verify karo:**
- [ ] Ek Python script jo `SIGTERM` catch karke "cleaning up" print kare, phir exit ho
- [ ] Usi script ko `kill -9` karo → cleanup nahi hua. **Yahi "job kho gaya" ka root cause hai.**

### Din 3 — File descriptors, sockets, connection pools

- Ek TCP connection = ek fd. `ulimit -n` kya hai
- Connection pool kya solve karta hai (handshake cost + fd limit)
- Pool exhaust hone pe kya hota hai: wait, timeout, ya error

**Verify karo:**
- [ ] DB pool size 2 karo, 10 concurrent requests bhejo, latency dekho
- [ ] Likho: pool exhaustion ka error kaisa dikhta tha

### Din 4 — TCP lifecycle aur timeouts

**Padho:** Kurose **sirf Chapter 3**. Baaki book chhod do.

- Handshake, connection reuse / keepalive
- **Connect timeout vs read timeout** — ye do alag cheezein hain
- Retransmission — isliye "network slow" aur "network down" me farq karna mushkil hai

**Verify karo:**
- [ ] `httpx` se ek request bhejo jisme connect timeout 1s ho, aur ek unreachable IP hit karo
- [ ] Phir ek slow endpoint pe read timeout test karo
- [ ] Likho: mere system me kaunsa timeout kaha lagna chahiye

### Din 5 — Postgres transaction internals

**Padho:** DDIA **Ch 7** (Transactions) — pehla pass. Focus: isolation levels, lost update, write skew.

- MVCC: reader writer ko block nahi karta, aur iska cost kya hai
- Row locks: `FOR UPDATE`, `FOR UPDATE SKIP LOCKED`, advisory locks
- Isolation levels: Read Committed (Postgres default) me kya allowed hai

**Verify karo (ye sabse important experiment hai):**
- [ ] Do `psql` terminals kholo
- [ ] **Lost update** reproduce karo: dono same row padho, dono badlo, ek update kho gaya
- [ ] **Write skew** reproduce karo: dono ne constraint check kiya, dono pass hue, phir dono ne likha, constraint toot gaya
- [ ] Phir `FOR UPDATE` lagao aur dekho behaviour kaise badla

> Week 0 ke end me: **L0 ka floor ban gaya.** Ab "kill -9 pe kya kho sakta hai" ka jawab mere paas hai. Yahi wo "page 1" thi jo missing lag rahi thi.

---

## 4. Project: `Relay` — durable job execution engine

Ye **wahi project hai jo resume pe jayega.** Koi alag "resume project" nahi hai.

**Kyu ye project:** jab main queue *banata* hu, Celery ke peeche chhup nahi sakta. Har wo sawaal jisme main confuse hu, mujhe khud answer karna padega.

### 4.0 Relay kya hai — concrete picture

Ecommerce ka user **customer** tha. Relay ka user **developer** hai. Koi UI nahi, koi customer nahi — ek API jise doosra app call karta hai.

**Scenario:** purane ecommerce me order paid hone pe receipt email bhejna tha. Celery ko bolta tha. Us Celery ki jagah Relay:

```
POST /jobs
{
  "type": "send_email",
  "payload": { "to": "a@b.com", "template": "receipt" },
  "idempotency_key": "order-1234-receipt"
}
→ 202 { "job_id": "j_8f3a...", "status": "pending" }
```

**Relay ka contract (= yahi pura product hai):**

1. Job kabhi nahi khoyega — API crash ho, DB restart ho, worker mare
2. Email **exactly ek baar** jayega, chahe worker 5 baar beech me crash kare
3. Fail hone pe smartly retry — hamesha ke liye loop nahi
4. 10 baar fail hua toh dead letter, chup-chaap nahi
5. Har waqt bata sakta hai job kaha hai (`GET /jobs/{id}`)

Andar teen cheezein: **API process** (accept), **worker process** (execute), **reaper loop** (atke jobs recover). Ek table.

Simple bhasha me: **Relay = Celery ka chhota version, khud ka banaya hua.** Celery *use* karne se Celery samajh nahi aaya. Celery *banane* se aayega.

### 4.0.1 Ecommerce vs Relay — difference kind ka hai, size ka nahi

| | Ecommerce | Relay |
|---|---|---|
| User kaun | customer | developer |
| Kya hai | **product** | **infrastructure** |
| Value | features | guarantees |
| Interview me | "kya banaya" | "kya guarantee kiya, aur kaise prove kiya" |

Ye upgrade hai — **backend roles infrastructure banane wale hire karti hain.** Product banane wale bahut hain.

### 4.0.2 "Ek hi project extend karunga toh naya kya sikhunga?"

**Features add nahi karunga. Problem ka *nature* badlunga.** Ye do bilkul alag cheezein hain:

- ❌ **Feature add karna** = priorities, tags, dashboard → naya kuch nahi. Ye alpha-commerce wali galti hai. **Mana hai.**
- ✅ **Nature badalna** = wahi substrate, par jo kaam execute hota hai uski properties badal gayi → **naya problem class**

| Kab | Kaam ki nature | Naya problem class |
|---|---|---|
| **M1** | sasta, local, deterministic | crash recovery, lease, idempotency, at-least-once |
| **M2-3** | mehenga, external, rate-limited, non-deterministic | execution se *pehle* budget check; retry ka **economics** (har retry pe paisa); non-deterministic output ko test karna; **shared** token bucket across workers (distributed coordination); provider fallback = quality tradeoff |
| **M4-5** | high volume, multi-node | tenant fairness/isolation (ek tenant ne 1 lakh jobs daale); backpressure; multiple reaper → leader election; table partitioning + archival |

**Teen mahine, teen alag problem classes, ek system.** Month 1 ka koi concept M2 me repeat nahi hota.

Ye "ek cheez pe atke rehna" nahi hai — **ek imaarat me manzilein chadhna** hai. Neev wahi, har floor naya.

> **Underrated bonus:** ek system jiska 6 mahine ka git history ho, jisme evolution dikhta ho — wo 5 alag one-month projects se strictly better signal hai. Kyunki asli kaam aisa hi hota hai. Koi company greenfield project nahi degi; existing system evolve karna hoga.

### 4.0.3 "Project 3" hai ya nahi?

**Default: nahi.** Do project — ecommerce (wide, ho gaya) + Relay (deep, evolving). Portfolio shape sahi hai.

**Par ye dogma nahi hai. Exit signal:** jab koi naya theme Relay me ghusane ke liye kuch **unnatural bolt-on** karna pade, tab naya project sahi hai.

*Example:* agar Theme 4 ke baad stream processing / CDC gehra seekhna ho — Relay uska natural ghar nahi hai (wo request-response substrate hai, stream nahi). Tab ek chhota alag project banana sahi hoga.

Wo decision **Month 5 me** aayega. Abhi wo sawaal exist nahi karta.

### Scope lock — Andar

- `jobs` table + `POST /jobs` enqueue API
- Worker process jo job claim karke chalata hai
- Lease + heartbeat (crash recovery)
- Retry with exponential backoff + jitter
- Dead letter queue
- Idempotency keys (exactly-once side effects)
- Metrics + structured logs

### Scope lock — Bahar (mahine bhar bahar hi rahega)

- ❌ UI / dashboard
- ❌ Auth
- ❌ Job dependencies / DAG
- ❌ Cron scheduling
- ❌ Priorities
- ❌ Multi-tenancy

> **Scope guard:** agar week 3 me DAG add karne ka man kare — wo signal hai ki main hard problem se bhaag raha hu. Mat karna.

**Thin:** 4-5 endpoints, ek table, do process.
**Tall:** paanch hard problems, har ek ka documented tradeoff.

---

## 5. Week 1 — Queue banao, at-least-once ka matlab dekho

**Layer: L1**

### Padho
- DDIA **Ch 7** doosra pass — isolation levels, lost update, write skew (ab code ke context me)
- RabbitMQ ke **acknowledgements aur prefetch** wale docs (~2 ghante). Queue ka mental model saaf ho jayega.

### Banao
- [ ] `jobs` table: `id, type, payload, status, attempts, created_at`
- [ ] `POST /jobs` — enqueue
- [ ] `GET /jobs/{id}` — status
- [ ] Worker loop: job claim karo `SELECT ... FOR UPDATE SKIP LOCKED` se → chalao → `succeeded` mark karo
- [ ] States: `pending → running → succeeded / failed`

Bas itna. Aur kuch nahi.

### Todo (failure injection)
- [ ] Do worker ek saath chalao **bina** `SKIP LOCKED` → dono same job uthate hain. Dekho.
- [ ] Phir `SKIP LOCKED` lagao → problem gaya. **Ab pata hai wo clause kya kar raha hai.**
- [ ] Worker ko job ke beech me `kill -9` → job hamesha ke liye `running` me atak gaya

> **Ye atka hua job = Week 2 ka problem statement.**

### Likho (DECISIONS.md)
- **D-01:** Postgres as queue vs Redis vs RabbitMQ — kyu Postgres (hint: business data ke saath ek hi transaction me enqueue kar sakta hu = outbox ka fayda muft)
- **D-02:** `SKIP LOCKED` vs advisory lock vs status-flag update — kyu ye

---

## 6. Week 2 — Crash recovery, retries, dead letter

**Layer: L0 + L2. Ye hafta sabse important hai.**

### Padho
- DDIA **Ch 8** (Unreliable networks, unreliable clocks) — ye samjhayega ki timeout choose karna *inherently* hard kyu hai
- Marc Brooker ka blog: timeouts, retries, backoff

### Banao
- [ ] Lease: `locked_until` column. Worker job claim karte waqt lease leta hai
- [ ] Heartbeat: worker beech beech me lease extend karta hai
- [ ] Reaper: expired lease wale jobs ko `pending` pe wapas laata hai
- [ ] Retry: exponential backoff **+ jitter** (jitter kyu — likho)
- [ ] `max_attempts` cross → dead letter
- [ ] Graceful shutdown: `SIGTERM` pe current job khatam karo, naya mat lo (Week 0 Din 2 ka use)

### Todo — iss mahine ka sabse important experiment
- [ ] `kill -9` worker → reaper ne job reclaim kiya → recovered ✓
- [ ] **Ab ye:** ek worker banao jo lease se **zyada** time leta hai par **zinda hai**. Reaper job reclaim karega, doosra worker chalu karega, aur **pehla worker bhi chal raha hoga.**

> Ek job, do execution, dono legit. **Yahi wo moment hai jab "at-least-once" buzzword se sach ban jayega.**
> Lease expire hone se purana worker rukta nahi hai. Ye Week 3 ka reason hai.

- [ ] Ek job jo hamesha fail hota hai → dekho retries + backoff + DLQ me pahuchna

### Likho
- **D-03:** Retry policy — backoff formula, aur jitter kyu (thundering herd)
- **D-04:** Lease duration ka tradeoff. Format:

```
## D-04: Lease duration = 30s + heartbeat
Problem: worker crash hone pe job kab reclaim kare?
Options: (a) 5s  — fast recovery, par slow jobs pe false duplicate
         (b) 30s + heartbeat — balanced
         (c) 5min — safe, par crash pe 5min delay
Chose: (b). Heartbeat se long jobs safe, crash detection 30s me.
Cost: har job pe extra DB write. 1000 jobs/min pe acceptable (measured).
Rejected (a) because: load test me 12% jobs 5s se zyada lete the.
```

---

## 7. Week 3 — Idempotency aur correctness proof

**Layer: L2 ka core. Ye hafta mera differentiator hai.**

### Padho
- DDIA **Ch 11** (Stream Processing) — at-least-once, dedup, exactly-once ka poora treatment. Ye literally Celery/RabbitMQ ke tradeoffs ka theory hai.
- Brandur ka blog: idempotency keys, background jobs, outbox

### Banao
- [ ] `idempotency_key` column + **unique constraint** (application-level check nahi — wo race condition hai, jo Week 2 me dekh liya)
- [ ] Ek side-effect handler (email jaisa — fake SMTP ya counter table)
- [ ] Dedupe: duplicate execution ke baad bhi side effect **exactly ek baar**
- [ ] Outbox pattern: side effect ka record job ke same transaction me likho

### Property test — ye resume line hai
- [ ] Hypothesis se property test likho
- [ ] **Property:** *kisi bhi random sequence of crashes, retries, aur concurrent workers ke baad, har job ka side effect count exactly 1 hai*
- [ ] Hypothesis random interleavings generate karega

> Jab ye pass hoga, mere paas **evidence** hai — opinion nahi. 99% students ke paas ye nahi hota.

### Todo
- [ ] Do worker forcibly same job pe chalao → prove karo ek hi side effect hua
- [ ] Side effect ke *beech* me crash karo → recovery pe duplicate nahi hona chahiye

### Likho
- **D-05:** Dedupe at enqueue vs at execute — kaha aur kyu
- **D-06:** Unique constraint vs application-level check (race condition ka concrete example ke saath)

---

## 8. Week 4 — Load, observability, aur writeup

**Layer: L4 ka taste. Deliverable-heavy hafta.**

### Padho
- DDIA **Ch 9** skim — consensus. Sirf itna ki pata ho main leader election *nahi* kar raha aur **kyu nahi** kar raha (wo bhi ek decision hai, D-08 me likho)
- Redis **persistence (RDB vs AOF)** aur **eviction policies** docs — 20 minute, blast radius clear ho jayega

### Banao
- [ ] Metrics: queue depth, job latency p50/p99, retry rate, DLQ count
- [ ] Structured logs with `job_id` (ek job ka pura lifecycle trace ho sake)
- [ ] `/healthz` — aur socho "healthy" ka matlab kya hai (DB reachable? worker alive?)
- [ ] Locust load test: kitne jobs/sec sustain hote hain, queue lag kaise badhta hai

### Todo
- [ ] Postgres pool 2 connections pe limit karke load → pool exhaustion
- [ ] Postgres beech me band karo → worker crash karta hai ya retry karta hai?
- [ ] 10k jobs ek saath → queue depth behaviour, backpressure ki zarurat dikhi?

### Likho — ye week ka asli deliverable
- [ ] **README:** problem statement, ek architecture diagram, `DECISIONS.md` ka link, failure matrix, **numbers**
- [ ] **Ek blog post:** "Building a durable job queue on Postgres: what breaks and why"
- [ ] **D-07:** observability me kya measure kiya aur kyu
- [ ] **D-08:** leader election kyu nahi kiya (single reaper ka tradeoff)

> **Week 4 ka writeup non-negotiable hai.** Code thoda adhura ho toh chalega. Writeup adhura hua toh pura mahina waste, kyunki resume pe code nahi jaata.

---

## 9. Artifacts — jo actually resume pe jaate hain

Code artifact nahi hai. Ye teen artifact hain.

### 9.1 `DECISIONS.md`

**Ye mera interview script hai.** Isme jo likha hoga, wahi main 45 minute bolunga.

Har hafte 2 entries. Fixed format:

```
## D-NN: <decision ek line me>
Problem:  kya solve kar raha hu
Options:  (a) ... (b) ... (c) ...
Chose:    kaunsa aur kyu
Cost:     iska nuksaan kya hai (har decision ka hota hai)
Rejected: (x) because <concrete reason, ideally measured>
```

**Rule:** "Cost" khali nahi chhodna. Agar cost nahi likh paa raha, matlab decision samjha nahi.

### 9.2 Failure Matrix (README me)

| Component | Failure | System behaviour | Blast radius | Recovery |
|---|---|---|---|---|
| Worker | `kill -9` | Job `running` me atka, reaper 30s me reclaim | 1 job, 30s delay | Automatic |
| Worker | `SIGTERM` | Current job complete, naya nahi liya | Zero | Automatic |
| Postgres | Down | Enqueue 503, worker retry loop me | Poora system | Manual |
| Pool | Exhausted | Requests queue, p99 phatta | Latency degradation | Automatic |

Ye table khud bharna experiments se. **Guess nahi karna.**

### 9.3 README structure

1. **Problem** — ek paragraph. "Background jobs at-least-once chalte hain. Exactly-once side effects kaise?"
2. **Architecture** — ek diagram. API → jobs table → worker → side effect. Reaper alag.
3. **Correctness properties** — formally likho:
   - *No loss:* accepted job eventually terminal state me pahuchega (`succeeded` ya `dead_letter`)
   - *No duplicate effect:* har job ka side effect exactly ek baar
   - *No stuck jobs:* koi job indefinitely `running` me nahi rahega
4. **Numbers** — throughput, p50/p99, zero-duplicate proof (property test runs)
5. **Failure matrix** — upar wala table
6. **Decisions** — `DECISIONS.md` ka link

---

## 10. Reading strategy — cover to cover nahi

**Rule:** book se chapter tab padho jab project me us problem se takra chuke ho. Pehle sawaal, phir jawab. Warna kuch yaad nahi rahega.

| Kab | Kya | Kitna |
|---|---|---|
| Week 0 Din 4 | Kurose **Ch 3** (TCP) | Sirf ye chapter |
| Week 0 Din 5 | DDIA **Ch 7** — pehla pass | Isolation levels focus |
| Week 1 | DDIA **Ch 7** — doosra pass + RabbitMQ ack/prefetch docs | — |
| Week 2 | DDIA **Ch 8** (networks, clocks) + Marc Brooker (timeouts/retries) | — |
| Week 3 | DDIA **Ch 11** (stream processing) + Brandur (idempotency) | — |
| Week 4 | DDIA **Ch 9** skim + Redis persistence/eviction docs | Ch 9 sirf skim |

**Abhi ke liye chhod do:**
- ❌ **Alex Xu Vol 1 & 2** — ye interview prep hai, learning nahi. Placement 3 mahine door hone pe uthao.
- ❌ **Building Microservices** — tab jab actually multiple services honge. Warna sirf monolith-shaming milega.
- ❌ **Database Internals** — DDIA Ch 3 ke baad, agar B-tree/LSM ki curiosity jage. Optional.
- ❌ **Kurose ka baaki** — Ch 3 ke alawa kuch nahi, on-demand.
- ❌ **DDIA Ch 1-6, 10, 12** — Theme 2/3 me aayenge.

> DDIA ki 600 pages sach me samandar hai. Par jab Week 2 me lease timeout ka decision lena hai, tab **Ch 8 ke 20 pages exactly wahi hain jo chahiye. Baaki 580 pages tab exist nahi karte.** Yahi trick hai.

---

## 10.1 Books — poora mapping (aur kya SKIP karna hai)

| Book | Kya hai | Kab | Kitna |
|---|---|---|---|
| **Kleppmann DDIA (1st ed)** | **Core textbook.** Baaki sab optional, ye nahi. | Poore saal, on-demand | Ch 7, 8, 11 → Theme 1. Ch 5, 6 → Theme 3/4. Ch 1-4 → kabhi bhi. Ch 9 → skim. **Ch 10, 12 SKIP.** |
| **DDIA 2nd ed** | Incomplete/updated | Baad me | **Abhi chhod do.** 1st edition padho. |
| **Kurose Networking** | L0 ka hissa | Week 0 Din 4 | **Sirf Ch 3 (Transport/TCP).** Ch 2 halka. **Baaki 6 chapters SKIP** — wo network engineer ke liye hain. |
| **Alex Xu Vol 1** | **Interview prep**, learning nahi | Month 5-6 | Poora — par tab, abhi nahi |
| **Alex Xu Vol 2** | Advanced patterns | Month 6+ | Optional. Vol 1 kaafi hai. |
| **Building Microservices** | Multi-service ke liye | Month 6+ ya kabhi nahi | Fresher se microservices expertise expect nahi karte. Zarurat pade toh **sirf** communication styles + sagas/workflow chapters. |
| **Database Internals** | Optional deep dive | DDIA Ch 3 ke baad, agar curiosity jage | **Sirf Part I (storage engines — B-Tree, LSM).** Part II DDIA se overlap. |

> **Sadhi baat:** actual required reading = DDIA ke ~5 chapters + Kurose ka 1 chapter. **Baaki 6 books ka 80% abhi exist nahi karta.** Shelf pe padi books ka guilt yahi khatam.

> **Honest gap:** mere do sabse bade gaps ke liye **book hi nahi hai** — SQL/query performance aur cloud. Wo Postgres docs + `EXPLAIN ANALYZE` chala ke seekhte hain. Nayi book kharidne ki zarurat nahi.

---

## 10.2 Relay kitna cover karta hai — honest coverage map

| Skill area | Relay cover karta hai? |
|---|---|
| Transactions, isolation, locks, MVCC | ✅ **Strong** |
| Idempotency, retries, at-least-once, DLQ | ✅ **Strong** |
| Crash recovery, leases, graceful shutdown | ✅ **Strong** |
| Testing strategy (unit/integration/**property**) | ✅ **Strong** — differentiator |
| Observability, load testing, capacity | ✅ M4 |
| Outbox / dual-write | ✅ M2 |
| Rate limiting, cost control, backpressure | ✅ M2-M4 |
| Design communication (`DECISIONS.md`) | ✅ **Strong** |
| Caching + invalidation | ⚠️ M4 tak gap |
| **SQL & query optimization, indexes, `EXPLAIN`** | ❌ bada gap |
| **API design polish** (versioning, pagination, error contracts) | ❌ |
| **Auth/authz depth** (OAuth flows, RBAC) | ❌ |
| **Cloud** (ek provider, kuch services) | ❌ hiring ke liye matters |
| **Replication, consistency models** | ❌ Theme 3/4 tak |
| **Kafka / stream processing** | ❌ fresher ke liye mostly zaruri nahi |
| **Kubernetes** | ❌ **fresher ke liye noise hai** |
| **System design breadth** | ❌ Alex Xu, M5-6 |

**Verdict:** Relay mera **correctness + reliability core** banata hai — backend interview ka sabse gehra hissa. Coverage ke hisaab se ye **aadha** hai.

### Par coverage hiring ka bar nahi hai

Achhi MNC / big startup me fresher backend role ka asli bar **teen** cheezein hain:

1. **DSA gate paas** — binary hai
2. **Ek system jise 45 minute defend kar sakun** — depth. Relay ye deta hai.
3. **Itni breadth ki narrow na lagu** — "cache kaise?", "auth kaise?", "DB slow ho toh?" pe **sensible** jawab ho. Expert jawab nahi.

Bas. Ye teen.

> Koi fresher se poori list expect nahi karta. Jo log resume pe poori list likhte hain, unko wo **shallow** aati hai — interviewer 3 sawaal me pakad leta hai.
>
> Interviewer dhoondh raha hai: **kya ye banda ek problem ko gehrai tak le jaa sakta hai, aur kya ye seekh sakta hai.** Depth ye dono prove karti hai. Coverage kuch prove nahi karti.
>
> **Baaki 60% list job pe fill hoti hai — aur interviewer ko ye pata hai.**

### Gaps kab fill honge

| Gap | Kab | Effort |
|---|---|---|
| **SQL / query optimization** | M2 ke parallel | ~10 ghante. `jobs` table pe `EXPLAIN ANALYZE`, index ke saath/bina, 10 lakh rows daal ke. Relay me hi ho jayega. |
| **API design** | M2 | ~5 ghante. Relay ke API pe versioning, pagination, consistent errors, idempotent POST. |
| **Cloud** | M4 | ~15 ghante. **Ek** provider, **paanch** services (compute, managed DB, object store, queue, monitoring). Relay deploy karo. **Certification nahi chahiye.** |
| **Auth depth** | M4 | ~8 ghante. OAuth2 flows samjho (padh ke), RBAC vs ABAC. |
| **Caching, replication** | Theme 3 (M4-5) | DDIA Ch 5 + Relay pe apply |
| **System design breadth** | M5-6 | Alex Xu Vol 1 |
| **Kafka, K8s, microservices** | **Abhi nahi. Possibly kabhi nahi.** | Job pe milega |

> **Pura gap list ~50 ghante ka hai, 4 mahine me spread.** Ye samandar nahi — ye checklist hai.

---

## 10.3 Planning loop se bahar nikalna

Sach: **jo clarity main chahta hu, wo planning se nahi aayegi. Wo Week 2 se aayegi.**

Planning se planning ki bhookh **badhti** hai, mit'ti nahi. Har planning round ek confusion clear karta hai aur ek naya kholta hai. Ye loop hai.

Week 2 me jab worker **zinda** hoga par lease expire ho chuki hogi aur ek job **do baar** chalega — us ek moment me "at-least-once" itna samajh aayega jitna 10 planning conversations se nahi. Aur uske baad mere sawaal **bilkul alag** honge — better, specific.

**Review checkpoints (anxiety ka scheduled outlet):**
- **Week 1 end** — kya bana, kya atka. Plan adjust.
- **Week 2 end** — sabse valuable checkpoint. Tab tak aadhi list khud answer kar chuka hounga.

Beech me atko toh **specific atkav** pe poochna ("ye race condition samajh nahi aa raha", "ye query slow hai") — plan ke baare me nahi. **Plan kaafi hai. Ab test hone ka waqt hai.**

---

## 11. Daily rhythm

Backend ke liye **~2 ghante roz + weekend pe 2 ghante experiments.** Hafte me ~16 ghante.

**Roz ka shape:**

| Time | Kaam |
|---|---|
| 30 min | Padho (current week ka assigned reading) |
| 75 min | Banao (current week ka ek checkbox) |
| 15 min | Likho (aaj kya samjha, kya atka — 3-4 line) |

Wo 15 minute skip nahi karna. Mahine ke end me wahi notes README aur blog post ban jaate hain. Tab se likhna shuru karoge toh sab bhool chuke honge.

**Weekend:** ek failure experiment + `DECISIONS.md` update.

---

## 12. Definition of Done

Mahine ke end me ye sab hona chahiye:

- [ ] `Relay` chal raha hai — enqueue, execute, crash recovery, retry, DLQ
- [ ] Property test pass ho raha hai: any crash/retry interleaving → exactly-once side effect
- [ ] `DECISIONS.md` me **8 entries**, har ek me Cost bhara hua
- [ ] Failure matrix bhara hua — measured, guessed nahi
- [ ] Load test numbers: sustained jobs/sec, p50/p99
- [ ] README complete (section 9.3 ka structure)
- [ ] Ek blog post published
- [ ] L0 ke 5 topics verify ho chuke (Week 0 ke checkboxes)

### Iske baad resume pe ye 3 lines likhne ka haq hoga

> - Built a durable job execution engine on PostgreSQL with lease-based crash recovery; verified exactly-once side effects across randomized crash/retry interleavings using property-based testing (Hypothesis).
> - Documented 8 architecture decisions with measured tradeoffs — lease duration, retry backoff, dedupe placement — validated via load testing (X jobs/sec sustained, p99 Yms).
> - Mapped failure behaviour of every dependency through fault injection (worker kill, DB outage, pool exhaustion), documenting blast radius and degradation mode for each.

Teeno lines pe interviewer 20-20 minute baat kar sakta hai. Aur teeno **ek mahine ke ek project** se aa rahi hain.

---

## 13. Theme 1 ke baad — domain aur aage ka arc

### 13.1 Pehle ek principle: domain vs depth

- **Depth** decide karti hai main interview **paas** karunga ya nahi → *conversion*
- **Domain** decide karta hai mujhe interview ke liye **bulayenge** ya nahi → *routing*

Dono chahiye, **par order fixed hai.** Domain pehle chunna aur depth baad me = wahi 8/10 LinkedIn profile. Depth pehle, phir usko domain pe point karna = differentiated.

**Month 1 domain-neutral hai (depth building). Domain Month 2 se enter karega.**

### 13.2 Domain choice: AI infrastructure — par tutorial layer pe nahi

**Observation:** 10 me se 8 log RAG + HuggingFace embeddings + vector DB kar rahe hain.
**Galat conclusion:** "main bhi RAG chatbot banau."
**Sahi conclusion:** agar 8/10 ek cheez kar rahe hain, wo differentiator nahi — **baseline noise hai.** Ek aur RAG chatbot = 9va banda.

Demand real hai, par **us layer pe nahi jahan wo 8 log khade hain.** Industry me jo pattern actual demand me hai wo **LLM gateway / AI execution layer** hai: multi-provider routing, semantic caching, rate limiting, cost tracking, fallback chains, tenant isolation, evals.

**In me ek bhi AI/ML skill nahi hai. Sab backend reliability problems hain.**

### 13.3 Aur yahi mera unfair advantage hai

LLM calls slow, mehenge, non-deterministic, rate-limited, aur frequently failing hote hain. Unke around jo chahiye:

| AI system ki zarurat | Underlying problem | Main kab seekh raha hu |
|---|---|---|
| Provider 429 → sensibly retry | backoff + jitter | Week 2 |
| Same request ke liye dobara paisa na lage | idempotency key | Week 3 |
| 100k docs embed, beech me crash | durable queue, checkpoint resume | Week 1-2 |
| Provider A down → B | fallback chain + blast radius | Section 2.2 |
| Per-tenant token cost + budget cap | metering + accounting | Week 4 |
| Cache with staleness bound | invalidation tradeoff | Theme 3 |
| Non-deterministic output test karna | property/statistical testing | Week 3 |

**Poora AI infra curriculum = mera Theme 1 curriculum.** Sirf load ka type badalta hai.

`Relay` **exactly wo substrate hai jo AI pipelines ko chahiye.** 100k documents embed karna literally durable job queue problem hai.

**Positioning:** *"Sabne RAG chatbot banaya. Maine wo layer banayi jo usko diwaliya hone se aur girne se bachati hai."*

### 13.4 Ye NAHI karna

- ❌ **Model training / fine-tuning / transformer internals** — ye ML engineer ka lane hai. Mera lane AI **infra** hai.
- ❌ **Naye framework chase karna** — LangChain/LlamaIndex type tooling fast churn karta hai. **Patterns seekho, wrappers nahi.**
- ❌ **Vector DB ko "AI cheez" samajhna** — wo ek **store** hai jiska index alag hai. Section 2.2 ke 5 sawaal usi pe lagao. Demystified.

### 13.5 Theme arc

**Ek waqt pe ek theme.** Ye ordering hai, isse aage abhi mat sochna.

| Kab | Theme | Layer | Kya | Project |
|---|---|---|---|---|
| **Month 1** ← abhi | Reliable execution | L0→L2 | at-least-once, idempotency, crash recovery | `Relay` |
| **Month 2-3** | AI execution layer | L2→L3 | rate limits, cost metering, budget caps, semantic cache, fallback chain, idempotent billing, eval harness | `Relay` + LLM gateway |
| **Month 4-5** | Read scale + ops | L3→L4 | invalidation, stampede, replication lag, observability, capacity | `Relay` scale karo |
| **Month 5-6+** | Interview mode | — | Alex Xu Vol 1+2 uthao | portfolio consolidate |

**Note:** Theme 2, 3, 4 me naya project nahi banana. `Relay` ko extend karna better hai — ek system ko gehra karna paanch naye system banane se zyada sikhata hai.

> **Ye arc pathhar pe nahi likha hai.** Month 1 ke baad mera understanding badal chuka hoga, aur tab Month 2 ka scope main khud better decide karunga. Abhi bas **direction** pata honi chahiye — detail nahi.

> **GenAI system design interviews ke liye note:** ab wahan *tradeoff reasoning* maanga jaata hai (embedding latency vs retrieval accuracy vs token cost), RAG tutorial nahi. Aur tradeoff reasoning exactly wo cheez hai jo `DECISIONS.md` train kar raha hai.

---

## 14. Rules — inhe todna mana hai

1. **Scope kabhi nahi badhega.** Feature add karne ka man kare = main hard problem se bhaag raha hu. Section 4 ka "Bahar" list dekho.
2. **Ek theme ek waqt pe.** Theme 2 ki cheezein Theme 1 me nahi ghusegi.
3. **Padha hua usi hafte code me utrega.** Warna 2 hafte me bhool jaunga.
4. **Har infra decision pe section 2.2 ke 5 sawaal.** Bina inke koi tool add nahi karunga.
5. **Blast radius pehle, feature baad me.** Naya dependency add karne se pehle: "ye gira toh kya hoga?"
6. **Writeup week 4 me non-negotiable.** Code slip ho sakta hai, writeup nahi.
7. **Buzzword ban hai.** "Redis lagaya" nahi bolunga. "Redis ko cache role me lagaya, blast radius = degraded latency" bolunga.

---

## 15. Ek honest note (jab motivation gire toh ye padhna)

**Week 2 aur 3 me atkega.** Lease/heartbeat aur idempotency me subtle race conditions milengi jo pehli baar me samajh nahi aayengi. **Ye plan fail nahi ho raha — yahi asli seekhna hai.** Agar Week 3 Week 4 me chala jaye, theek hai. Bas scope na badhne dena.

Aur wo "samandar me phenk diya" wali feeling — **wo kabhi poori tarah nahi jayegi, aur ye kamzori nahi hai.**

College **just-in-case learning** sikhata hai: pehle sab padho, phir exam do. Industry **just-in-time learning** pe chalti hai: problem aayi, uske liye jo chahiye wo gehra seekha, aage badhe.

Main abhi in dono ke beech ki transition me hu. Dimaag "poora syllabus pehle" maang raha hai kyunki 15 saal wahi sikhaya gaya. Par backend ka syllabus infinite hai — jo bhi padh lu, kal ek naya tool aayega.

10 saal ka senior bhi roz "mujhe ye nahi pata" me hota hai. Farq sirf ye hai ki wo us feeling se darta nahi, kyunki usko pata hai: **usko sab nahi aana chahiye — bas jo problem saamne hai, uske liye kaafi aana chahiye.**

Isliye ye plan project ke around bana hai, syllabus ke around nahi. **Project batata hai ki ab kya seekhna hai. Wo mera filter hai.**

---

*Kal se: Section 3, Week 0, Din 1.*
