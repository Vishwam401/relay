# CURRENT WEEK — Week 0 (L0 Patch)

> Ye file **har hafte overwrite** hogi. Ye "aaj kya karna hai" ka single source hai.
> Week 0 khatam hone pe isko Week 1 ke content se replace kar dena.

---

## A. Kaunsi file khulegi, kaunsi band

| File | Status | Kyu |
|---|---|---|
| `CURRENT_WEEK.md` (ye) | ✅ **Roz khuli** | Aaj ka kaam yahi batata hai |
| `BACKEND_ROADMAP.md` (Part 1) | ✅ Hafte me 1-2 baar | Context aur reference |
| `BACKEND_ROADMAP_PART2.md` | 🔒 **BAND** | Month 1 ke end tak nahi kholna. Isse overwhelm hoga. |

**Ye 4 nayi files banengi (setup me):**

| File | Kya jayega |
|---|---|
| `DECISIONS.md` | Design decisions. Week 0 me khali rahegi (koi design decision nahi hai abhi) |
| `LEARNING_LOG.md` | **Roz 3-4 line.** Kya samjha, kya atka. Ye Month 5 me blog post banega. |
| `POSTMORTEMS.md` | Hafte me 1 entry. Dusro ke incidents se seekhna. |
| `PROBLEMS.md` | Hafte me 2 entries. "Ye problem interesting lagi kyunki..." |

---

## B. Setup — aaj raat, 45 minute (kal se pehle)

Agar aaj nahi kar paye toh Day 1 me 45 min extra lagega. Better aaj kar lo.

### B.1 Naya repo

```
mkdir relay
cd relay
git init
```

**Naam `relay` hi rakho.** `test-project` ya `job-queue-practice` nahi. Ye 6 mahine chalega, isko real naam do.

### B.2 Structure

```
relay/
  labs/              ← Week 0 ke experiments yahan (throwaway code, par committed)
  relay/             ← actual app (Week 1 se)
  tests/
  docker-compose.yml
  requirements.txt
  README.md
  DECISIONS.md
  LEARNING_LOG.md
  POSTMORTEMS.md
  PROBLEMS.md
```

> `labs/` ka code "gandha" hoga aur wo theek hai. Par usko **commit karo** — kyunki 6 mahine ka git history jisme Week 0 ke experiments dikhte hain, wo apne aap me signal hai.

### B.3 Dependencies (minimum, aur yahi rakhna)

```
fastapi
uvicorn
sqlalchemy
asyncpg
psycopg[binary]
alembic
pytest
pytest-asyncio
hypothesis
httpx
```

**Redis abhi nahi.** Redis Month 2 me aayega (shared rate limiter ke liye). Abhi add karna = ek extra moving part jiska koi kaam nahi. **Ye khud ek decision hai** — minimum dependencies se shuru karo.

### B.4 docker-compose.yml — sirf Postgres

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: relay
      POSTGRES_DB: relay
    ports:
      - "5432:5432"
```

Verify: `docker compose up -d` phir `docker compose exec db psql -U postgres -d relay` — prompt mil gaya toh setup done.

### B.5 Pehla commit

```
git add .
git commit -m "chore: initial project skeleton for Relay"
```

---

## C. Week 0 ka shape

**Roz ka budget: ~2 ghante 15 minute**

| Block | Time | Kya |
|---|---|---|
| Main kaam | 90 min | L0 ka topic + uska experiment |
| Side kaam | 30 min | Reading (specific, assigned) |
| Log | 15 min | `LEARNING_LOG.md` me 3-4 line |

**Week 0 ka goal:** L0 ka floor banana. **Koi feature nahi banega.** Ye 5 din pura "samajhne" ke hain.

| Din | Topic | Main experiment | Side reading |
|---|---|---|---|
| 1 | Process, thread, async | blocking vs non-blocking measure | async/event loop |
| 2 | Signals, process death | SIGTERM catch, SIGKILL nahi | worker job loss incident |
| 3 | fd, sockets, conn pools | pool exhaustion banao | real pool exhaustion incident |
| 4 | TCP, timeouts | connect vs read timeout | Kurose Ch 3 |
| 5 | Postgres transactions | **write skew reproduce** | DDIA Ch 7 |
| 6-7 | Weekend | consolidate + postmortem ritual | — |

---

## D. Day 1 — Process, thread, async

### Main kaam (90 min)

**Samajhna (30 min):**
- Ek process me kya shared hai (memory, fd table), kya nahi
- Thread vs async — dono concurrency dete hain, mechanism alag
- **Blocking call actual me kya karta hai:** syscall → kernel wait → wo thread ruk gaya
- Event loop ek thread me hazaar connections kaise handle karta hai

**Experiment (60 min) — `labs/day1_async.py`:**

```python
# Do endpoint banao
@app.get("/blocking")
async def blocking():
    time.sleep(2)          # ← galat: event loop block ho gaya
    return {"ok": True}

@app.get("/nonblocking")
async def nonblocking():
    await asyncio.sleep(2) # ← sahi: event loop free hai
    return {"ok": True}
```

Ab 3 concurrent requests bhejo dono pe (httpx + asyncio.gather se) aur **total time measure karo**.

- [ ] `/blocking` → ~6 second (serialize ho gaya)
- [ ] `/nonblocking` → ~2 second (parallel chala)
- [ ] **Numbers note karo.** Approx nahi, actual.

**Bonus (agar time bache):** ek blocking function ko `run_in_executor` me daal ke dekho — timing kya hui aur kyu.

### Side kaam (30 min)

Async Python ka event loop kaise kaam karta hai — Python docs (`asyncio` ka "Developing with asyncio" page) padho, especially blocking code ke baare me warning wala section.

### Deliverable

`LEARNING_LOG.md`:
```
## Day 1 — async vs blocking
- Measured: /blocking 3 req = 6.1s, /nonblocking 3 req = 2.0s
- Samjha: time.sleep event loop ko block karta hai, poora process ruk jata hai
- Atka: [agar kuch atka]
- Sawaal: agar ek DB driver sync hai toh async app me kya hoga? → Day 3
```

---

## E. Day 2 — Signals aur process death

**Ye din sabse important hai Week 0 me.** Iska direct use Week 2 me hoga.

### Main kaam (90 min)

**Samajhna (30 min):**
- `SIGTERM` — trap ho sakta hai. Ye "politely band ho jao" hai.
- `SIGKILL` (`kill -9`) — **trap nahi ho sakta.** OS process ko turant maar deta hai. Koi cleanup nahi.
- `SIGINT` — Ctrl+C
- Graceful shutdown ka matlab: naya kaam accept band, in-flight kaam complete, phir exit

**Experiment (60 min) — `labs/day2_signals.py`:**

```python
# Ek loop jo "working on item N" print karta rahe
# SIGTERM handler jo "cleaning up..." print kare aur exit ho
```

- [ ] Script chalao, doosre terminal se `SIGTERM` bhejo → "cleaning up" print hua ✓
- [ ] Phir se chalao, `kill -9` karo → **cleanup nahi hua** ✗
- [ ] Ab isko realistic banao: script ek "job" 5 second le raha ho. Beech me SIGTERM → job complete karke exit hona chahiye. Beech me SIGKILL → job aadha, kuch nahi hua.

> **Ye wahi hai jo Week 2 me tera job "running" me atka dega.** Aaj isko choti scale pe dekh lo.

Windows note: `kill` nahi hai. PowerShell me `Stop-Process -Id <pid>` = forceful. Graceful signal test ke liye Docker container use karo (`docker stop` SIGTERM bhejta hai, `docker kill` SIGKILL) — ye actually better hai kyunki production me aisa hi hota hai.

### Side kaam (30 min)

[thoughtbot ka "Graceful Switching of Worker Processes"](https://thoughtbot.com/blog/graceful-switching-of-worker-processes) — ek real client project jisme misconfiguration ki wajah se worker jobs kho rahe the. Chhota post hai, exactly tera problem.

### Deliverable

`LEARNING_LOG.md` + ye sawaal khud se: *"agar mera worker `kill -9` se mara, toh job ka kya hoga aur usko kaun wapas laayega?"* — iska jawab likhna, kyunki **Week 2 ka pura design isi sawaal ka jawab hai.**

---

## F. Day 3 — File descriptors, sockets, connection pools

### Main kaam (90 min)

**Samajhna (30 min):**
- Ek TCP connection = ek file descriptor. `ulimit -n` (Linux/container me) kya hai
- Connection pool kya solve karta hai: handshake cost + fd limit + DB ka `max_connections`
- Pool exhaust hone pe teen possible behaviours: **wait**, **timeout**, ya **error** — aur ye configurable hai

**Experiment (60 min) — `labs/day3_pool.py`:**

- [ ] SQLAlchemy engine banao `pool_size=2, max_overflow=0`
- [ ] Ek endpoint jo DB me `SELECT pg_sleep(1)` chalata hai
- [ ] 10 concurrent requests bhejo
- [ ] **Measure karo:** total time, per-request latency, aur kya koi error aaya
- [ ] Ab `pool_timeout=1` set karo → ab error aayega. **Error message note karo** (ye production me dikhega)
- [ ] `pool_size=10` karo → farq measure karo
- [ ] Postgres me `SELECT count(*) FROM pg_stat_activity;` chala ke actual connections dekho

### Side kaam (30 min)

Ek real public incident writeup: [Buttondown ka database connection exhaustion incident](https://buttondown.com/blog/incident-0024). Chhota aur honest hai — unhone connection ceiling hit kar liya tha aur naye requests connection acquire nahi kar paa rahe the.

Agar time bache: [incident.io ka "Battling database performance"](https://incident.io/blog/database-performance) — pool se connection na milne pe operation kaise block hota hai, ye explain karta hai.

### Deliverable

`POSTMORTEMS.md` me **pehli entry** (Buttondown wala):
```
## Buttondown — database connection exhaustion
- Kya toota: naye requests DB connection acquire nahi kar paye
- Root cause: configured connection ceiling hit
- Seekha: pool exhaustion "DB slow hai" jaisa dikhta hai, par DB theek hota hai
- Mere system me: pool_size default hai, maine kabhi socha nahi. Ye D-xx banega.
```

---

## G. Day 4 — TCP aur timeouts

### Main kaam (90 min)

**Padho (60 min):** **Kurose Chapter 3 (Transport Layer).** Sirf ye chapter. Focus:
- TCP handshake (3-way), aur connection setup ka cost
- Connection reuse / keepalive
- Retransmission aur timeout — **isliye "network slow" aur "network down" me farq karna inherently mushkil hai**
- Flow control vs congestion control (bas concept, math nahi)

**Experiment (30 min) — `labs/day4_timeouts.py`:**

Do **alag** timeouts hain, aur ye distinction bahut important hai:

- [ ] **Connect timeout:** unreachable IP hit karo (`10.255.255.1`) with `httpx.Timeout(connect=1.0)` → 1s me fail
- [ ] **Read timeout:** ek slow endpoint (apna hi `/blocking` from Day 1) hit karo with `read=0.5` → 0.5s me fail
- [ ] Dono ka error type note karo — **alag hain**
- [ ] Likho: "mere Relay me provider call pe connect timeout X hoga, read timeout Y, kyunki..."

> Month 2 me jab LLM provider hang karega, ye distinction tumhe bachayega.

### Side kaam (30 min)

Aaj side reading skip — Kurose Ch 3 khud hi bhaari hai. Iske badle **`PROBLEMS.md` me pehli 2 entries likho.** Kuch aisa jo iss hafte padhte waqt interesting laga.

### Deliverable

`LEARNING_LOG.md` + timeout values ka ek chhota note (Month 2 me kaam aayega)

---

## H. Day 5 — Postgres transactions (Week 0 ka climax)

### Main kaam (90 min)

**Padho (40 min):** **DDIA Ch 7 (Transactions)** — pehla pass. Focus: isolation levels, lost update, write skew. Poora chapter nahi samajh aayega, theek hai.

**Experiment (50 min) — ye Week 0 ka sabse important experiment hai.**

Do `psql` terminals kholo. `docker compose exec db psql -U postgres -d relay`

**Experiment 1 — Lost Update:**

```sql
-- Setup (kisi ek terminal me)
CREATE TABLE counter (id int primary key, val int);
INSERT INTO counter VALUES (1, 100);
```

| T1 | T2 |
|---|---|
| `BEGIN;` | `BEGIN;` |
| `SELECT val FROM counter WHERE id=1;` → 100 | `SELECT val FROM counter WHERE id=1;` → 100 |
| `UPDATE counter SET val=101 WHERE id=1;` | |
| `COMMIT;` | `UPDATE counter SET val=101 WHERE id=1;` |
| | `COMMIT;` |

- [ ] Final value dekho: **101, jabki 102 hona chahiye tha.** Ek update kho gaya. **Koi error nahi aaya.**
- [ ] Ab dobara karo par `SELECT ... FOR UPDATE` use karke → dekho T2 block ho gaya, aur result 102 aaya

**Experiment 2 — Write Skew (ye zyada dilchasp hai):**

```sql
CREATE TABLE doctors (id int primary key, name text, on_call boolean);
INSERT INTO doctors VALUES (1,'a',true),(2,'b',true);
-- Business rule: kam se kam ek doctor on-call hona chahiye
```

| T1 (doctor a chhutti maang raha) | T2 (doctor b chhutti maang raha) |
|---|---|
| `BEGIN;` | `BEGIN;` |
| `SELECT count(*) FROM doctors WHERE on_call;` → 2 | `SELECT count(*) FROM doctors WHERE on_call;` → 2 |
| *2 >= 1, safe lagta hai* | *2 >= 1, safe lagta hai* |
| `UPDATE doctors SET on_call=false WHERE id=1;` | `UPDATE doctors SET on_call=false WHERE id=2;` |
| `COMMIT;` | `COMMIT;` |

- [ ] `SELECT count(*) FROM doctors WHERE on_call;` → **0**
- [ ] **Business rule toot gaya. Dono transactions ne check kiya, dono pass hue, aur phir bhi constraint violate ho gaya. Koi error nahi.**
- [ ] Ab isko `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE` se dobara karo → ek transaction fail hoga
- [ ] Aur `SELECT ... FOR UPDATE` se bhi try karo

> **Ye do experiments tera Week 0 ka asli output hain.** Ab tumne apni aankho se dekha ki "code sahi lag raha hai par concurrent me galat hai" ka matlab kya hota hai. Isse aage tumhara `Relay` ka pura design isi darr pe khada hoga — aur wo sahi darr hai.

### Side kaam (30 min)

Postgres docs: **Transaction Isolation** ka page. Read Committed (Postgres default) me kya allowed hai, wo dekho. Aur note karo ki tumne jo experiments kiye, wo docs ke hisaab se **expected behaviour** hain — bug nahi.

### Deliverable

`LEARNING_LOG.md` me dono experiments ka result. Aur ye line likho: *"Read Committed me mera code silently galat ho sakta hai. Isliye Relay me [X] karna padega."*

---

## I. Weekend (Din 6-7)

### Din 6 (~2 ghante)

- [ ] `LEARNING_LOG.md` padho poora hafta. **Kya aisa hai jo abhi bhi dhundhla hai?** Usko 30 min do.
- [ ] Week 0 ke saare `labs/` files commit karo, proper commit messages ke saath
- [ ] `PROBLEMS.md` me total 2 entries ho jani chahiye

### Din 7 (~1.5 ghante) — Weekly ritual shuru

- [ ] **Ek postmortem padho.** [Cloudflare ka post-mortem tag](https://blog.cloudflare.com/tag/post-mortem/) se koi ek uthao. Ye sabse detailed public postmortems hain.
- [ ] `POSTMORTEMS.md` me 3-line entry (total 2 entries ho jayengi iss hafte)
- [ ] **Ye ritual har hafte chalega.** 6 mahine = 24 postmortems. Ye teri "operational scars" ka substitute hai.

**Aur agar man ho toh (optional but recommended):**
Ek preview padho ki tu kahan jaa raha hai — [Postgres ko job queue banane ke consequences](https://techcommunity.microsoft.com/blog/adforpostgresql/potential-consequences-of-using-postgres-as-a-job-queue/4514332). Abhi 60% samajh aayega. Month 4 me tu isko khud measure karega. **Aaj isko padhna sirf ye jaan lene ke liye hai ki aage kya aane wala hai.**

---

## J. Week 0 Definition of Done

- [ ] `relay` repo bana, Postgres chal raha hai, 6-7 commits hain
- [ ] Day 1: async vs blocking ka **measured** farq, numbers ke saath
- [ ] Day 2: SIGTERM catch hua, SIGKILL nahi — khud dekha
- [ ] Day 3: pool exhaustion banaya, error message dekha, `pg_stat_activity` me connections count kiye
- [ ] Day 4: Kurose Ch 3 padha, connect vs read timeout ka farq code me dekha
- [ ] Day 5: **lost update aur write skew dono reproduce kiye** — aur `FOR UPDATE`/`SERIALIZABLE` se fix hote dekha
- [ ] `LEARNING_LOG.md` me 5 entries
- [ ] `POSTMORTEMS.md` me 2 entries
- [ ] `PROBLEMS.md` me 2 entries

### Ye 5 sawaal Week 0 ke end me khud se poochna

1. `kill -9` pe kya kho sakta hai aur kyu? *(ye L0 ka test tha)*
2. Read Committed me mera code silently galat kaise ho sakta hai?
3. Pool exhaustion "DB slow" se kaise alag dikhta hai?
4. Connect timeout aur read timeout alag kyu hain?
5. `time.sleep` async app me kyu ghatak hai?

**Paanchon ka jawab aa gaya → Week 1 ke liye ready.** Kisi ek ka nahi aaya → wo ek din extra do. Jaldi nahi hai.

---

## K. Week 1 ka preview (bas ek line)

Week 1 me `jobs` table banegi aur worker jo `FOR UPDATE SKIP LOCKED` se job claim karega — **aur Day 5 ke experiments ke baad tumhe pata hoga ki wo clause kyu zaruri hai.**

Week 0 khatam hone pe ye file overwrite karna. Detail `BACKEND_ROADMAP.md` Section 5 me hai.

---

*Kal: Section D — Day 1.*
