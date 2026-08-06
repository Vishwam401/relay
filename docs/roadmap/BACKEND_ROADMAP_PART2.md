# Backend Roadmap — Part 2

**Month 2 → 6, aur uske aage**
Companion doc: `BACKEND_ROADMAP.md` (Month 1 — Theme 1, `Relay` ka core)

> Ye doc **living document** hai. Month 1 ke baad meri samajh badlegi, aur tab main isko khud edit karunga. Abhi ye direction hai, contract nahi.

---

## 0. Part 1 se relation

| Doc | Kya |
|---|---|
| `BACKEND_ROADMAP.md` | Week 0 (L0 patch) + Month 1 (`Relay` core). **Roz kholne wala doc.** |
| `BACKEND_ROADMAP_PART2.md` (ye) | Month 2-6 + beyond. **Mahine me ek baar kholne wala doc.** |

**Rule:** Month 1 ke doran ye doc **band rehna chahiye.** Isko padhne se "aage bahut kuch hai" wali feeling aayegi jo focus todegi. Month 1 ke end pe kholna.

---

## 1. Market reality check — 2026 me bar kya hai

Ye section isliye hai ki plan opinion pe nahi, evidence pe khada ho. Maine ye verify kiya:

**Depth > breadth, aur ye explicit hai.** Apple ke backend interview guide me seedha likha hai ki wo **breadth se zyada depth** value karte hain — expectation ye hai ki tumne jo systems banaye unki gehri samajh ho, na ki libraries/frameworks ka naam pata ho ([source](https://dataford.io/interview-guides/apple/backend-engineer)).

**Project walkthrough > abstract puzzles.** Optum ke process ka defining pattern ye bataya gaya hai ki project walkthrough ki depth abstract puzzle solve karne se zyada matter karti hai ([source](https://www.interviewquery.com/guides/optum-software-engineer)).

**Jo cheez AI replace nahi kar sakti, wahi differentiator hai.** 2026 ke hiring analysis me stand-out karne ka nuskha ye bataya gaya: operational scars (on-call, SLOs), latency/uptime/cost pe measurable impact, aur ek-do production-style projects **observability aur clear tradeoff writeups ke saath** — kyunki yahi wo hissa hai jise AI tools convincingly nahi bana sakte ([source](https://www.nucamp.co/blog/top-10-companies-hiring-backend-developers-in-2026-what-they-look-for-how-to-stand-out)).

**Kam projects, gehre projects.** 2026 portfolio guidance: 3-5 deployed systems, deeply done — bahut se shallow repos se better ([source](https://www.nucamp.co/blog/top-10-backend-portfolio-projects-for-2026-that-actually-get-you-hired)).

**Interviews AI ki wajah se badal rahe hain.** Companies practical assessments aur in-person rounds wapas laa rahi hain, kyunki AI-assisted applications aur hiring fraud ki concern hai ([Greenhouse 2026 AI in Hiring Report ke hawale se](https://timesofindia.indiatimes.com/technology/tech-news/are-you-interviewing-claude-or-the-person-stanford-professor-on-why-tech-companies-are-reviving-in-person-interviews/articleshow/132806958.cms)).

**AI engineering ka bar prompting se aage nikal chuka hai.** Hiring un logo ki ho rahi hai jo LLMs ko business data, tools, workflows, evaluation aur infrastructure se jod sakte hain ([source](https://aiengineeringinsider.substack.com/p/the-ai-engineer-job-market-has-moved)).

*(Upar ke sources se information licensing compliance ke liye rephrase ki gayi hai. Attribution inline links me hai.)*

### Iska seedha matlab mere plan pe

| Market signal | Mera response |
|---|---|
| Depth > breadth | Ek system (`Relay`), 6 mahine, gehra |
| Tradeoff writeups differentiate karte hain | `DECISIONS.md` — 20+ entries by Month 5 |
| Operational scars chahiye | Failure injection + SLOs + load tests. **College me on-call nahi milta, toh khud banao.** |
| Measurable impact chahiye | Har mahine numbers: throughput, p99, cost/job |
| AI infra me demand hai, tutorial layer me nahi | Month 2-3: LLM **execution layer**, RAG chatbot nahi |
| In-person/practical rounds wapas | Apna code zubaani defend karne ki practice. Rote nahi. |

---

## 2. Timeline overview

| Month | Theme | Layer | `Relay` ka roop | Primary artifact |
|---|---|---|---|---|
| **1** | Reliable execution | L0→L2 | durable job runner | property test + 8 decisions |
| **2** | External expensive work | L2 | + LLM gateway core | rate limiting + budget enforcement |
| **3** | Cost, cache, correctness | L2→L3 | + caching, fallback, evals | semantic cache tradeoff + eval harness |
| **4** | Scale aur ops | L3→L4 | + multi-node, cloud | **scaling ceiling ka measurement** |
| **5** | Consolidation | — | feature freeze | 4 blog posts + resume + portfolio |
| **6** | Interview mode | — | maintenance only | Alex Xu + mock defenses |

**Har mahine ka non-negotiable:** 1 writeup + `DECISIONS.md` me 4 entries + naye numbers.

---

## 3. Month 2 — External, mehenga, rate-limited kaam

**Problem class shift:** Month 1 me kaam **sasta, local, deterministic** tha. Ab kaam **mehenga, external, rate-limited, non-deterministic** hai.

Isse Month 1 ka kuch bhi repeat nahi hota. Naye control points aate hain.

### 3.1 Kya banega

**Provider abstraction**
- [ ] Do provider minimum. Ek real (jo bhi API key mil jaye) + ek fake/local jo controllable failures deta hai
- [ ] Common interface: `complete(prompt, params) → (text, tokens_in, tokens_out)`
- [ ] Fake provider me **injectable failures**: 429, 500, timeout, slow response. Ye tera test lab hai.

**Naye job types**
- [ ] `llm_completion` — ek prompt, ek response
- [ ] `embed_document` — ek document, ek vector (vector DB abhi nahi chahiye, `float[]` column kaafi hai)

**Rate limiting — ye month ka hardest part hai**
- [ ] Token bucket per provider
- [ ] **Shared across all workers** → Redis me. Ye **distributed coordination** hai, local counter nahi.
- [ ] 429 pe `Retry-After` header respect karo (blind backoff nahi)
- [ ] Do dimensions: requests/min **aur** tokens/min. Dono ek saath enforce karne padte hain.

**Token accounting**
- [ ] Execution se **pehle** estimate (prompt tokens count karo)
- [ ] Execution ke **baad** actual record karo (provider response se)
- [ ] `job_costs` table: `job_id, provider, model, tokens_in, tokens_out, cost_usd`

**Budget enforcement — naya control point**
- [ ] Per-tenant monthly budget cap
- [ ] Check **execution se pehle**, warna paisa lag chuka hoga
- [ ] Budget exhaust hone pe job `rejected` — retry nahi, kyunki retry se budget wapas nahi aata

**Retry economics — Month 1 se fundamentally alag**
- [ ] Retryable vs non-retryable classify karo:
  - **Retryable:** 429, 500/502/503, timeout, connection error
  - **Non-retryable:** 400 (bad request), 401, content filter rejection, context length exceeded
- [ ] **Non-retryable ko kabhi retry nahi karna** — wo paisa jalana hai bina chance ke
- [ ] Max cost per job cap: "is job pe $0.50 se zyada nahi kharch karna, chahe kitne retry"

**Idempotency ab financial hai**
- [ ] Month 1 me duplicate = duplicate email. Ab duplicate = **duplicate bill**
- [ ] Same `idempotency_key` = cached result return karo, provider ko call bhi mat karo
- [ ] Uniqueness ke liye advisory locks ka pattern samajhne layak hai — River Queue ka [advisory lock + FNV hashing wala approach](https://riverqueue.com/blog/uniqueness-with-advisory-locks) padho. Wo dikhata hai ki "SELECT karke check, phir INSERT" naive approach concurrent clients me kyu toot ta hai.

### 3.2 Failure experiments (weekend)

| Experiment | Kya seekhunga |
|---|---|
| Fake provider 429 storm de | Backoff sahi hai? Retry-After respect ho raha? Thundering herd? |
| Fake provider hang kar jaye (koi response nahi) | Timeout kaha lagi hai? Worker forever blocked? Lease expire hoke duplicate? |
| Provider intermittent 500 (30% requests) | Retry se success rate kya hua, cost kitna badha |
| Budget beech me exhaust ho (100 jobs ka batch) | Kitne jobs execute hue, kitne rejected, koi over-budget gaya? |
| Do worker ek saath rate limit hit karein | Shared token bucket kaam kar raha ya dono independently limit maan rahe? |
| Same idempotency_key 50 baar bhejo | Provider ko kitni baar call gaya? (answer 1 hona chahiye) |

### 3.3 Decisions (D-09 se D-12)

- **D-09:** Rate limiter kahan — Redis (shared, network hop) vs local per-worker (accurate nahi) vs DB (slow). Blast radius: Redis gira toh?
- **D-10:** Budget check pehle vs baad. Pehle = extra latency + estimate galat ho sakta. Baad = over-budget ja sakta.
- **D-11:** Retryable/non-retryable classification, aur galat classify karne ka cost
- **D-12:** Idempotent result caching — kitne time tak, kaha store

### 3.4 Reading (Month 2)

- **DDIA Ch 5 (Replication)** — pehla pass. Redis ko shared state banaya toh uske failure modes samajhne ke liye.
- **LLM gateway patterns** — [rate limiting, semantic caching, multi-provider fallback, cost control ke production patterns](https://www.groovyweb.co/blog/llm-integration-rate-limiting-caching-fallbacks-2026). Ye padho **implement karne se pehle nahi, karte waqt** — jab tumhara apna sawaal ban chuka ho.
- **Parallel gap track:** SQL/query optimization (Section 8.1)

---

## 4. Month 3 — Cost, caching, aur non-deterministic correctness

**Problem class shift:** ab output **non-deterministic** hai. Matlab "correct" ka matlab hi badal gaya.

### 4.1 Kya banega

**Exact cache (pehle ye)**
- [ ] Key = hash(model + prompt + params). Deterministic, safe.
- [ ] TTL ka decision: model deprecate ho sakta hai, prompt template badal sakta hai

**Semantic cache (phir ye — aur yahan asli tradeoff hai)**
- [ ] Query ko embed karo, similar past queries dhoondo, threshold se upar ho toh cached answer do
- [ ] **Ye ek correctness risk hai, optimization nahi.** Similarity 0.95 hai par sawaal ka matlab ulta hai → tumne **galat jawab** de diya
- [ ] Threshold tuning: high threshold = kam hits (bachat kam), low threshold = **galat jawab** (trust gaya)
- [ ] Measure karo: hit rate, aur **false hit rate** (manually 50 hits check karo)

> **D-14 iska hoga, aur ye tera best interview story hai.** "Maine semantic cache lagaya, 40% hit rate mila, par manual audit me 6% false hits nikle — matlab har 16va user ko galat jawab. Maine threshold badha diya, hit rate 22% ho gaya. Ye cost vs correctness ka explicit tradeoff hai jo maine correctness ke favour me liya."

**Fallback chain**
- [ ] Provider A fail → B. Par ye **correctness implication** rakhta hai: doosra model, doosri quality
- [ ] Policy decide karo: kaunse job types pe fallback allowed hai, kaunse pe nahi
- [ ] Response me record karo kaunse model ne answer diya (audit trail)
- [ ] Circuit breaker: A repeatedly fail kar raha hai toh usko try karna hi band karo kuch der

**Streaming passthrough**
- [ ] SSE se token-by-token response
- [ ] **Hard question:** mid-stream connection toot gaya. Partial output aaya. Bill karoge? Retry karoge? Resume kar sakte ho? (nahi kar sakte — ye ek fundamental limitation hai, document karo)

**Eval harness — Month 3 ka differentiator**
- [ ] Golden set: 30-50 input/expected-property pairs
- [ ] **Equality assert nahi kar sakte.** Toh properties assert karo:
  - Output valid JSON hai (jab JSON maanga)
  - Output me required fields hain
  - Output length bounds me hai
  - Output me PII leak nahi hua
  - Semantic similarity to expected > threshold
- [ ] Regression detection: prompt ya model badla → golden set pe pass rate gira?
- [ ] Ye **property-based testing ka natural extension** hai — Month 1 ka skill, naye domain me

**Bulk backfill — yahan `Relay` chamakta hai**
- [ ] 100k documents embed karo
- [ ] Checkpoint resume: 60k pe crash → 60k se shuru, 0 se nahi
- [ ] Rate-limit-aware pacing: provider ki limit ke hisaab se throttle
- [ ] Partial failure: 200 docs fail hue → DLQ me, baaki 99,800 successful
- [ ] Idempotency: **dobara chalao, dobara paisa na lage**

> Ye ek line resume pe: *"Backfilled 100k document embeddings with checkpointed resume and rate-limit-aware pacing; re-running the job costs zero additional API spend due to idempotent execution."*

### 4.2 Failure experiments

| Experiment | Kya seekhunga |
|---|---|
| Semantic cache pe 50 hits manually audit karo | False hit rate — actual number, guess nahi |
| Provider A ko permanently down karo | Circuit breaker khula? Fallback chala? Latency kya hui? |
| Mid-stream client disconnect | Billing kya hua? Partial output kahan gaya? |
| Prompt template badal ke golden set chalao | Kitne properties toote? Regression detect hua? |
| Backfill ko 60% pe kill karo, restart karo | Kitne docs dobara embed hue? (answer: 0 hona chahiye) |

### 4.3 Decisions (D-13 se D-16)

- **D-13:** Exact cache TTL aur invalidation trigger
- **D-14:** Semantic cache threshold — **cost vs correctness**, measured false-hit rate ke saath
- **D-15:** Fallback policy — kab allowed, kab nahi, aur audit trail kyu zaruri
- **D-16:** Eval strategy — kaunse properties, kyu equality nahi

### 4.4 Reading (Month 3)

- **DDIA Ch 5** complete + **Ch 6 (Partitioning)** shuru
- Caching invalidation aur staleness bounds pe material
- **Parallel gap track:** API design polish (Section 8.2)

---

## 5. Month 4 — Scale, ops, cloud (sabse important mahina)

**Problem class shift:** ab volume aur multi-node. Aur is mahine ka centerpiece kuch aisa hai jo 99% students ke paas nahi hota — **apne design ka ceiling khud measure karna.**

### 5.1 Tenant fairness aur isolation

- [ ] Ek tenant ne 1 lakh jobs daal diye → baaki tenants bhookhe mar rahe hain (**starvation**)
- [ ] Solutions: per-tenant concurrency cap, weighted fair queuing, ya per-tenant queue partition
- [ ] Measure karo: fairness ke bina ek chhote tenant ka p99 kya tha, baad me kya hua

### 5.2 Backpressure

- [ ] Queue depth threshold cross → enqueue pe **429 do**, infinite accept mat karo
- [ ] Ye counter-intuitive hai: **request reject karna reliability hai**, failure nahi
- [ ] Load shedding policy: kaunse jobs pehle drop honge (priority nahi — *class*)

### 5.3 ⭐ Postgres-as-queue ka ceiling — is mahine ka centerpiece

Month 1 me maine Postgres ko queue banaya (D-01). Ab main uski **limit measure karunga.** Ye sabse valuable exercise hai poore 6 mahine me.

**Kyu:** kisi bhi design ka ceiling jaanna, aur usko *number* ke saath jaanna — ye senior-level behaviour hai. Interviewer ko sabse zyada impress ye karta hai ki tumne apne hi design ki kamzori khud dhoondi.

**Kya expect karna hai:** high concurrency pe `SELECT ... FOR UPDATE SKIP LOCKED` wala pattern degrade karta hai. Documented symptoms: CPU creep, vacuum keep up nahi kar pata, aur wait event stats me `LWLock:MultiXactSLRU` type entries stack hone lagti hain. Aur pattern ye hai ki **dev aur staging me sab theek chalta hai, phir production me real concurrency aane pe cliff aa jaati hai** ([Microsoft/Azure Postgres blog](https://techcommunity.microsoft.com/blog/adforpostgresql/potential-consequences-of-using-postgres-as-a-job-queue/4514332)).

Aur ye guidance bhi note karo: agar throughput hundreds ya low-thousands jobs/sec hai aur Postgres already chal raha hai, toh alag broker ki zarurat nahi — par ek point aata hai jahan ruk kar real broker lena chahiye ([source](https://faizahmed.in/postgres-queue-skip-locked/)).

**Mera kaam:**
- [ ] Worker concurrency badhate jao: 5 → 20 → 50 → 100 → 200
- [ ] Har step pe measure: throughput, p99 claim latency, Postgres CPU, **`pg_stat_activity` ke wait events**
- [ ] Dead tuples aur vacuum lag track karo (`pg_stat_user_tables`)
- [ ] **Wo point dhoondo jahan throughput badhna band ho jaye ya girne lage**
- [ ] Graph banao: concurrency vs throughput. Knee point mark karo.
- [ ] Likho: "Mera design N workers / M jobs/sec tak theek hai. Uske aage ye toot ta hai [specific reason]. Us point pe main [X] pe migrate karunga."

**Mitigations jo try karne layak hain:**
- [ ] Completed jobs ko archive karo (dead rows kam → vacuum pressure kam)
- [ ] Table partitioning by status ya date
- [ ] `LISTEN/NOTIFY` sirf **wake-up signal** ke liye, queue ke liye **nahi** — notifications persist nahi hote, payload ~8KB pe cap hai, aur load me NOTIFY commits ko serialize karta hai ([source](https://nerdleveltech.com/postgres-listen-notify-job-queue))
- [ ] Claim query ka index optimize karo (partial index on `status = 'pending'`)

> **Resume line:** *"Load-tested the queue to its architectural ceiling: measured throughput knee at N concurrent workers, root-caused to vacuum lag and lock contention on the claim path, documented the migration trigger and target."*
>
> Ye line ek fresher se aana **extremely** unusual hai.

### 5.4 Multi-node coordination

- [ ] Do node pe reaper chal raha hai → dono same expired job reclaim kar rahe hain
- [ ] Options: advisory lock se single-reaper election, ya reaping ko partition karo (`job_id % N`)
- [ ] **Ye Month 1 ka D-08 ("leader election kyu nahi kiya") ka jawab hai** — ab wo decision revisit karo. Purane decision ko naye evidence pe badalna maturity hai, galti nahi.

### 5.5 Cloud (~15 ghante, ek weekend + kuch shaam)

**Ek provider. Paanch services. Certification nahi.**

- [ ] Compute: container chalao (ECS/Cloud Run/App Runner — jo simple lage)
- [ ] Managed DB: RDS/Cloud SQL. **Note karo self-hosted se kya alag laga** (connection limits, failover, backup)
- [ ] Object store: S3/GCS — job payloads jo bade hain wahan
- [ ] Managed queue (SQS): **Relay se compare karo.** SQS kya deta hai jo tumne nahi banaya (visibility timeout, DLQ built-in, infinite scale)? Aur tumne kya diya jo SQS nahi deta (**business data ke saath ek transaction me enqueue** = outbox muft)?
- [ ] Monitoring: CloudWatch/equivalent me metrics + ek alarm

> **D-19 yahi hai, aur ye interview me bahut poocha jaata hai:** "SQS use kar sakte the, khud kyu banaya?" Iska ek acha jawab hona chahiye — aur wo jawab "seekhne ke liye" nahi hona chahiye. Asli jawab: transactional enqueue.

### 5.6 Observability upgrade

- [ ] Distributed tracing (OpenTelemetry): enqueue → claim → execute → provider call, ek trace me
- [ ] **SLO define karo:** "99% jobs enqueue ke 60s ke andar start honge"
- [ ] SLO breach pe alert
- [ ] Ek dashboard: queue depth, throughput, error rate, cost/hour, DLQ size

> SLO define karna aur uske against measure karna = wo "operational scars" jo market maangta hai (Section 1). College me on-call nahi milta — **ye uska closest substitute hai.**

### 5.7 Decisions (D-17 se D-20)

- **D-17:** Fairness mechanism — per-tenant cap vs weighted queue vs partition
- **D-18:** Backpressure threshold aur load shedding policy
- **D-19:** Self-built queue vs managed (SQS) — **honest** comparison, cost + ops burden ke saath
- **D-20:** Reaper coordination — advisory lock vs partitioning. Aur D-08 ko formally revise karo.

### 5.8 Reading (Month 4)

- **DDIA Ch 6 (Partitioning)** complete
- **DDIA Ch 5 (Replication)** revisit — ab managed DB failover ke context me
- **Parallel gap tracks:** Cloud (5.5), Auth depth (Section 8.3)

---

## 6. Month 5 — Consolidation (feature freeze)

**Ye mahina code likhne ka nahi hai. Ye packaging ka hai.** Aur ye wo mahina hai jise log skip kar dete hain, aur isliye unka kaam waste ho jata hai.

### 6.1 FEATURE FREEZE

- [ ] Naya feature **ek bhi nahi**. Sirf bug fixes aur documentation.
- [ ] Kuch adhura hai? README me "Known limitations" section me likh do. **Adhura kaam honestly documented hona strength hai**, chhupana weakness hai.

### 6.2 4 blog posts

Ek hafte me ek. Ye 6 mahine ka kaam public evidence me convert karta hai.

1. **"Building a durable job queue on Postgres: what breaks and why"** — Month 1-2 ka content, failure experiments ke saath
2. **"Semantic caching for LLM calls: I measured the false-hit rate"** — Month 3, cost vs correctness. **Ye sabse zyada padha jayega**, kyunki log hit rate bataate hain, false hit rate nahi.
3. **"I load-tested my Postgres queue until it broke"** — Month 4 ka ceiling measurement, graphs ke saath
4. **"Testing non-deterministic systems: property-based evals for LLM output"** — Month 3 ka eval harness

**Format har post ka:** problem → maine 3 approaches consider kiye → ye choose kiya kyunki ye tradeoff → aise verify kiya → ye number mila → ye limitation reh gayi.

**Kahan publish karo:** apna blog (simple static site) + dev.to/Hashnode pe cross-post. LinkedIn pe summary + link.

### 6.3 Portfolio polish

- [ ] `Relay` README final: problem, architecture diagram, correctness properties, numbers, failure matrix, known limitations, decisions link
- [ ] `DECISIONS.md` — **20+ entries** by now. Har ek me "Cost" bhara hua.
- [ ] Ek architecture diagram jo actually sahi ho (excalidraw/mermaid)
- [ ] Alpha-commerce ka README bhi thoda theek karo — usko bhi ek line milegi resume pe

### 6.4 Resume + LinkedIn + GitHub (Section 13 dekho detail ke liye)

### 6.5 Breadth shuru

- [ ] **Alex Xu Vol 1 shuru** — ab uthao. Ab tumhare paas concrete anchors hain, toh patterns actually samajh aayenge, rote nahi honge.
- [ ] Auth depth complete karo (Section 8.3)
- [ ] Mock system design: **zor se bolke practice karo.** Alone, recording ke saath. Ye awkward hai aur bahut effective hai.

---

## 7. Month 6 — Interview mode

### 7.1 Priority shift

| | Month 1-4 | Month 6 |
|---|---|---|
| DSA | 50% | **70%** |
| Backend depth | 40% | 10% (maintenance) |
| Breadth/interview prep | 10% | 20% |

### 7.2 Project defense rehearsal — ye sabse zyada ignore kiya jata hai

Tera pura 6 mahina ek 45-minute conversation me convert hona hai. Wo conversation **practice karni padti hai.**

- [ ] **90-second pitch:** Relay kya hai, kya guarantee karta hai. Ratna nahi, samajh ke bolna.
- [ ] **10-minute walkthrough:** architecture, main decisions
- [ ] **Deep dive prep** — in sawaalon ke jawab bina soche aane chahiye:
  - "Exactly-once kaise guarantee kiya? Prove karo."
  - "Do worker same job pe aa gaye toh?"
  - "Ye SQS se better kyu hai?"
  - "Iska ceiling kya hai? Kaise pata?"
  - "Aaj dobara banate toh kya alag karte?" ← **is sawaal ka acha jawab hona zaroori hai**
  - "Sabse mushkil bug kaunsa tha?"
  - "Semantic cache me galat jawab ka risk kaise handle kiya?"
- [ ] **Whiteboard practice:** Relay ka architecture blank page pe 5 minute me draw karo. 10 baar.

### 7.3 System design breadth

- [ ] Alex Xu Vol 1 complete
- [ ] 8-10 classic designs khud attempt karo (URL shortener, rate limiter, notification system, news feed, chat, search autocomplete, distributed cache, payment system)
- [ ] **Har design me apna Relay experience connect karo.** "Ye notification system me maine jo job queue banayi thi, wahi pattern lagega — aur uska ceiling ye tha."

### 7.4 Practical/live rounds ke liye

Companies practical assessments aur in-person rounds wapas laa rahi hain (Section 1). Toh:

- [ ] **Unfamiliar code padhne ki practice.** Random open-source repo kholo, ek function samjho, zor se explain karo. Hafte me 2 baar.
- [ ] **Debugging practice.** Apne purane commits se ek bug wapas introduce karo, phir dhoondo.
- [ ] **Bina AI code likhne ki practice.** Kam se kam hafte me 2 session, autocomplete off. Ye interview condition hai.

### 7.5 Behavioral

`DECISIONS.md` tera behavioral prep hai. Har decision ek STAR story hai:
- "Ek technical decision batao jisme tumhe tradeoff lena pada" → D-14 (semantic cache)
- "Ek galti batao" → D-08 revise karna (leader election)
- "Kuch mushkil debug kiya ho" → Week 2 ka lease/duplicate race
- "Kaise pata karte ho ki tumhara code sahi hai" → property tests

---

## 8. Parallel gap-filling tracks

Ye Part 1 ke Section 10.2 se aaye gaps hain. **Total ~50 ghante, 4 mahine me spread.** Har ek Relay ke andar hi ho jayega — alag project nahi.

### 8.1 SQL & query optimization (~10 ghante, Month 2)

Sabse bada gap, aur sabse aasan fill karne wala.

- [ ] `jobs` table me **10 lakh rows** daalo (script se)
- [ ] `EXPLAIN ANALYZE` chalao claim query pe. **Plan padhna seekho** — Seq Scan vs Index Scan vs Bitmap Heap Scan
- [ ] Index hatao → phir se `EXPLAIN`. Farq dekho. Numbers note karo.
- [ ] **Partial index** banao (`WHERE status = 'pending'`) → farq measure karo
- [ ] Composite index ka column order ka farq dekho
- [ ] N+1 problem deliberately banao, phir `selectinload` se fix karo, query count compare karo
- [ ] `pg_stat_statements` on karo — sabse slow queries dekho
- [ ] Dead tuples aur `VACUUM` samjho (Month 4 me kaam aayega)

**Interview me ye poocha jaata hai:** "DB slow hai, kya karoge?" Iska jawab step-by-step hona chahiye: measure → explain → index → query rewrite → schema → cache. **Cache sabse last hai**, pehla nahi.

### 8.2 API design polish (~5 ghante, Month 3)

Relay ke API pe hi apply karo:

- [ ] Versioning: `/v1/jobs`, aur breaking change ka policy
- [ ] Pagination: cursor-based (offset kyu nahi — deep offset slow hota hai)
- [ ] Consistent error format: `{error: {code, message, details}}` — har endpoint pe same
- [ ] Idempotent POST: `Idempotency-Key` header ka proper handling (Stripe ka pattern padho)
- [ ] Status codes sahi: 202 for accepted-async, 409 for conflict, 429 for rate limit, `Retry-After` header ke saath
- [ ] OpenAPI spec generate karo, `schemathesis` se test karo

### 8.3 Auth & authz depth (~8 ghante, Month 4)

- [ ] OAuth2 flows **padh ke** samjho (implement nahi karna): authorization code + PKCE, client credentials, refresh token rotation
- [ ] JWT: kya safe hai kya nahi. `alg: none` attack, signature verification, expiry, revocation ka problem
- [ ] RBAC vs ABAC ka farq, aur kab kaunsa
- [ ] Relay me: API key auth + per-tenant scoping (tenant A, B ka job nahi dekh sakta)
- [ ] Secrets management: env var vs secret manager, rotation

### 8.4 Caching & replication (Month 4-5, DDIA ke saath)

- [ ] DDIA Ch 5 — leader/follower, replication lag, read-after-write consistency
- [ ] Cache patterns: cache-aside vs write-through vs write-behind
- [ ] Invalidation strategies aur unke failure modes
- [ ] Stampede prevention: request coalescing, probabilistic early expiry
- [ ] Relay me apply: provider response cache + config cache

---

## 9. Reading system — blogs aur postmortems

Books foundation dete hain. **Blogs current reality dete hain.** Dono chahiye.

### 9.1 Weekly ritual (30 min, non-negotiable)

**Hafte me ek postmortem.** Padho, aur 3 line likho: kya toota, root cause kya tha, kya seekha.

`POSTMORTEMS.md` naam ki file rakho. 6 mahine me 24 entries. **Ye tere "operational scars" ka substitute hai** — dusro ke incidents se seekhna, apna production na hone ke bawajood.

### 9.2 Sources

**Postmortems (priority):**
- [Cloudflare ka post-mortem tag](https://blog.cloudflare.com/tag/post-mortem/) — sabse detailed public postmortems, aur wo apne infra changes bhi document karte hain
- AWS post-event summaries
- GitHub availability reports
- Stripe, Discord, Figma, Uber, Netflix, DoorDash engineering blogs ke incident posts

**Engineering blogs** — 2026 ki ek scoring exercise me top-rated infra/platform blogs Meta, GitHub, Stripe, Cloudflare, Netflix nikle ([source](https://draft.dev/learn/engineering-blogs)). India context ke liye Razorpay, Zerodha, Swiggy, Flipkart ke blogs bhi add karo.

**Individual writers (backend depth ke liye best free material):**
- **Marc Brooker** — timeouts, retries, queueing theory, distributed systems. Tere Month 1-2 ke liye directly relevant.
- **Brandur Leach** — idempotency, background jobs, outbox pattern, Postgres. **Tere project ka sabse close match.**
- **River Queue blog** — Postgres queue internals. [Advisory locks + uniqueness](https://riverqueue.com/blog/uniqueness-with-advisory-locks) wala post Month 2 me padhna.
- **Pragmatic Engineer** — [incident review practices](https://blog.pragmaticengineer.com/postmortem-best-practices/) — postmortem kaise padhna aur likhna hai

### 9.3 Kaise padhna hai

- **Postmortem me** dhoondo: kaunsi assumption galat thi? Detection me kitna time laga? Fix ne kya naya break kiya?
- **Architecture post me** dhoondo: unhone kya reject kiya aur kyu? (Ye aksar likha hota hai aur log skip kar dete hain — asli seekhna wahi hai.)
- Feature announcements **skip** karo. Wo marketing hai.

> Tera senior ne bola tha "blogs padho phir domain decide karo." Ye section wo hai — par domain already decide ho gaya (AI infra). Ab blogs **problems dhoondne** ke liye padho, direction ke liye nahi.

### 9.4 `PROBLEMS.md`

Ek file jisme hafte me 2 entries: "ye problem interesting lagi, aur ye kyu hard hai."

6 mahine me 48 entries. Isse do fayde:
1. Month 7+ me next theme choose karna trivial ho jayega
2. Interview me "aage kya banaoge?" ka jawab specific hoga, generic nahi

---

## 10. 6 mahine ke baad kya bacha rahega — honest list

Ye section isliye hai ki main **jhoothi confidence** na banau. Ye cheezein 6 mahine baad bhi missing rahengi, aur **ye theek hai.**

### 10.1 Jo job ke bina seekh hi nahi sakte

| Kya | Kyu nahi seekh sakta |
|---|---|
| **Real production scale** | 10 lakh real users ka traffic pattern simulate nahi hota. Load test approximation hai. |
| **On-call pressure** | Raat 3 baje, paisa ruk raha hai, 50 log Slack pe — ye feeling banayi nahi ja sakti |
| **Legacy code aur migrations** | 8 saal purana codebase jisme 4 log ja chuke hain. Zero-downtime migration on live data. |
| **Cross-team negotiation** | Doosri team ka API tumhari zarurat pura nahi karta aur unke paas bandwidth nahi hai |
| **Cost at real scale** | Jab ek query ka $40k/month ka bill aata hai, tab priorities alag hoti hain |
| **Multi-region, compliance, audit** | GDPR, data residency, SOC2 — ye process hai, code nahi |
| **Organizational failure modes** | Sabse bade outages technical nahi, coordination failures hote hain |

**Ye list dekh ke ghabraana nahi.** Interviewer ko pata hai ki fresher ke paas ye nahi hai. Wo ye dekh raha hai ki **jab ye milega tab tu handle kar payega ya nahi** — aur wo depth se judge hota hai, coverage se nahi.

### 10.2 Jo seekh sakte the par jaan bujh ke chhoda

| Kya | Kab uthana |
|---|---|
| Kafka / stream processing | Job pe, ya Theme 5 me agar zarurat pade |
| Kubernetes | Job pe. **Fresher ke liye ye noise hai.** |
| Microservices architecture | Job pe. Ek service ko theek karna pehle. |
| gRPC / GraphQL | On-demand, 2 din ka kaam hai jab zarurat pade |
| Model training / fine-tuning | Ye alag career hai (ML engineer). Mera lane AI **infra** hai. |
| Multiple cloud providers | Ek kaafi hai. Concepts transfer hote hain. |

### 10.3 Kya honest tarike se claim kar sakunga

**Kar sakunga:**
- ✅ Concurrent systems me correctness reason karna aur prove karna
- ✅ Failure modes design karna, blast radius samajhna
- ✅ Design tradeoffs explain karna measured evidence ke saath
- ✅ Apne design ka ceiling dhoondna aur measure karna
- ✅ Non-deterministic systems test karna
- ✅ Ek system ko 6 mahine evolve karna (git history proof ke saath)

**Nahi kar sakunga (aur ye bolna theek hai):**
- ❌ "Maine production me 1M users handle kiye"
- ❌ "Maine microservices architecture design ki"
- ❌ "Mujhe Kafka/K8s production experience hai"

> **Interview me "mujhe nahi pata" bolna weakness nahi hai — bluff karna weakness hai.** Sahi jawab: "Production me nahi kiya, par ye samajhta hu ki problem kya hai aur kaise approach karunga."

---

## 11. Interview se pehle — final 6-8 weeks checklist

Ye Month 6 ke aage/upar chalega, jab placement season actually shuru ho.

### 11.1 Assets ready (Week -8)

- [ ] Resume — ek page, Section 13 ke format me
- [ ] `Relay` repo public, README polished, 6 mahine ka clean git history
- [ ] Alpha-commerce repo README theek
- [ ] 4 blog posts live
- [ ] LinkedIn updated — headline, About, projects with links
- [ ] GitHub profile README

### 11.2 Rehearsal (Week -6 se -2)

- [ ] 90-second pitch — 20 baar bol chuka hu, natural lagta hai
- [ ] Architecture blank page pe 5 min me draw — 10 baar
- [ ] Section 7.2 ke saare deep-dive sawaal — bina soche jawab
- [ ] `DECISIONS.md` ke top 8 decisions zubaani explain kar sakta hu
- [ ] 3 mock system design interviews (dost ke saath ya recording ke saath)
- [ ] 2 mock behavioral

### 11.3 DSA (parallel, apna track)

Iss doc ka scope nahi, par ek reminder: **gate binary hai.** Backend depth ka koi value nahi agar gate paas nahi hua.

### 11.4 Week -1

- [ ] Resume se **koi bhi** cheez hata do jise tu 5 minute defend nahi kar sakta. Ek bhi.
- [ ] Company-specific: unka engineering blog padho. 2-3 posts. Interview me reference karna **huge** signal hai.
- [ ] Sona. Seriously — practical/in-person rounds me thakan seedha dikhta hai.

### 11.5 Interview me kya lekar jana hai (mental)

**Teen cheezein har round me establish karni hain:**
1. **Main gehrai me jaa sakta hu** — Relay ka koi ek hissa, ek-do level neeche tak
2. **Main honest hu** — jo nahi pata, wo bolta hu, bluff nahi karta
3. **Main seekhta hu** — D-08 revise karne wali story. "Maine pehle X socha, phir data mila, phir Y kiya."

Teesri sabse underrated hai. Fresher hire karte waqt **learning velocity** hi actual signal hai.

---

## 12. Job lag jaane ke baad — pehle 6 mahine

Ye section abhi useless lagega. Month 6 me kaam aayega.

### 12.1 Pehle 30 din — sirf samajhna

- [ ] Codebase padho, likho mat. Ek architecture map khud banao (jo exist nahi karta hoga)
- [ ] Deployment pipeline follow karo end-to-end — commit se production tak
- [ ] Purane postmortems padho. **Ye sabse valuable onboarding document hai** aur koi tumhe nahi dega.
- [ ] Sawaal poocho aur jawab likho. Same sawaal dobara mat poocho.
- [ ] On-call rotation observe karo (shadow karo, ownership abhi nahi)

### 12.2 Din 30-90 — chhota par real

- [ ] Chhote bug fixes se shuru — codebase ka trust banao
- [ ] Ek cheez pakdo jo **koi nahi kar raha** aur kar do (flaky test, missing dashboard, ek stale doc)
- [ ] Code review me participate karo — **sawaal poochne wale reviews**, "LGTM" nahi
- [ ] On-call shadow → phir primary

### 12.3 Din 90-180 — ownership

- [ ] Ek service ya component ka ownership lo
- [ ] Ek design doc likho aur review karao — **ye promotion ka rasta hai**
- [ ] Ek incident lead karo (ya kam se kam ek postmortem likho)
- [ ] `DECISIONS.md` ki habit job pe le jao. Team me ye rare hai aur bahut visible hai.

### 12.4 Learning kab dobara shuru

**Pehle 3 mahine me side learning zero.** Job hi learning hai, aur wo overwhelming hoga.

Month 4 se: hafte me 3-4 ghante, aur **jo job me actually chahiye** wahi. Ab tera "problem-driven learning" ka filter job dega — yahi wo just-in-time learning hai jiski Part 1 ke Section 15 me baat hui thi.

Aur `PROBLEMS.md` maintain karte rehna. Career ke aage ke decisions wahi se aayenge.

---

## 13. Resume, LinkedIn, GitHub

### 13.1 Resume rules

**Format:** ❌ tool list. ✅ problem + approach + measured outcome.

| ❌ Aisa nahi | ✅ Aisa |
|---|---|
| "Built job queue using FastAPI, PostgreSQL, Redis, Celery" | "Built a durable job execution engine on PostgreSQL; verified exactly-once side effects across randomized crash/retry interleavings using property-based testing" |
| "Implemented caching for LLM calls" | "Implemented semantic response caching; measured 6% false-hit rate at 0.95 threshold and tightened it, trading 18% cache hit rate for output correctness" |
| "Load tested the system" | "Load-tested to architectural ceiling: throughput knee at N workers, root-caused to vacuum lag and lock contention; documented migration trigger" |

**Har bullet me:** kya problem, kya kiya, kya number.

**Projects section — sirf 2:**
1. `Relay` — 4-5 bullets
2. Alpha-commerce — 1-2 bullets (breadth dikhane ke liye: "full-stack e-commerce backend, 60+ endpoints, payment integration")

**"Writing" section add karo** — 4 blog posts ke links. Ye section 95% freshers ke resume me nahi hota, aur ye instant credibility hai.

### 13.2 LinkedIn

- **Headline:** "Backend engineer — distributed systems & AI infrastructure | Building Relay, a durable job execution engine" — specific, buzzword-free
- **About:** 3 paragraph. Kya banata hu, kaunse problems interesting lagte hain, kya seekh raha hu.
- Blog posts share karo, **thoughts nahi.** Ek measured finding wala post 10 motivational posts se zyada value laata hai.
- Recruiters keyword se dhoondhte hain: `PostgreSQL`, `distributed systems`, `idempotency`, `observability`, `LLM infrastructure` — ye naturally content me aane chahiye.

### 13.3 GitHub

- [ ] Profile README: kis pe kaam kar raha hu, links
- [ ] `Relay` pinned, README top-tier
- [ ] **Commit history clean aur meaningful.** "fix", "update", "wip" wale messages nahi. Interviewer commits padhta hai.
- [ ] Commit history se **evolution dikhna chahiye** — ye single biggest differentiator hai 5 one-month projects ke against

---

## 14. Anti-patterns — kya NAHI karna

Ye list utni hi important hai jitna plan.

1. **Naya project shuru karna** kyunki Relay boring lag raha hai. Boring lagna = tumne aasan hissa khatam kar liya, hard hissa shuru hone wala hai. **Wahi valuable hai.**
2. **Feature add karna** learning ke naam pe. Priorities, tags, dashboard — Part 1 Section 4.0.2 dekho.
3. **Tool chase karna.** Naya framework/DB/queue dekha, lagane ka man kiya. **Section 2.2 ke 5 sawaal** pehle. Agar 5 jawab nahi hain, mat lagao.
4. **Writeup postpone karna** "pehle code khatam kar lu" bol ke. Code kabhi khatam nahi hota. **Writeup mahine ke end me, non-negotiable.**
5. **Coverage chase karna.** "Kafka bhi seekh lu, K8s bhi" — Section 10.2 dekho. Ye anxiety hai, strategy nahi.
6. **Books cover-to-cover padhna.** Part 1 Section 10.1 ka mapping follow karo.
7. **Sab kuch resume pe likhna.** Jo 5 minute defend nahi kar sakte, wo liability hai, asset nahi.
8. **Planning ko kaam samajhna.** Part 1 Section 10.3. Agar main iss doc ko 3 baar edit kar chuka hu par code nahi likha — main planning loop me hu.
9. **Numbers ke bina claim karna.** "Fast", "scalable", "reliable" — ye khali shabd hain. Number ya kuch nahi.
10. **AI se code likhwa ke aage badh jana.** Ye project **samajhne** ke liye hai. Jo hissa AI ne likha aur tumne nahi samjha, wo interview me tumhe girayega. Boilerplate ke liye AI theek hai; **core logic khud likho** aur debug karo.

---

## 15. Review cadence

| Kab | Kya review karna |
|---|---|
| **Roz** | 15 min: aaj kya samjha, kya atka (Part 1 Section 11) |
| **Har hafta** | `DECISIONS.md` update, ek postmortem padho, ek `PROBLEMS.md` entry |
| **Har mahine ke end** | Ye doc kholo. Next month ka section padho. **Plan adjust karo based on jo actually seekha.** |
| **Month 3 ke end** | Bada checkpoint: kya AI-infra direction sahi lag raha hai? Change karna hai toh ab karo, baad me nahi. |
| **Month 5 ke end** | Portfolio review. Kya ye 45-min defense ke liye ready hai? |

### Month 1 ke end pe ye 3 sawaal khud se poochna

1. **Kya main Relay ke kisi ek hisse ko 10 minute bina notes explain kar sakta hu?** Nahi → gehrai kam hai, aage mat badho.
2. **Kya mere paas 8 decisions hain jinme "Cost" bhara hai?** Nahi → main implement kar raha hu, design nahi.
3. **Kya mere sawaal Month 1 se pehle ke sawaalon se alag hain?** Haan → **plan kaam kar raha hai.**

---

## 16. Ek last baat

Ye doc bada hai, par jo actually karna hai wo chhota hai: **ek system, chhe mahine, ek waqt pe ek problem class.**

Baaki sab — books ka mapping, gap tracks, blogs, market signals — **filters hain, tasks nahi.** Unka kaam ye batana hai ki **kya NAHI karna.** Isiliye ye doc mostly cheezein *hata* raha hai, add nahi kar raha.

Aur jo teri asli fikr hai — "kya main achha backend engineer ban paunga" — uska jawab iss doc me nahi hai. Wo Week 2 me hai, jab ek race condition 3 din tak samajh nahi aayegi aur chauthe din aa jayegi. **Wo din tera jawab hai.** Ye doc bas usse rasta saaf kar raha hai.

---

*Part 1 pe wapas jao: `BACKEND_ROADMAP.md` → Section 3, Week 0, Din 1.*
*Ye doc Month 1 ke end tak band rakhna.*
