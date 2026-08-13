# DDIA Chapter 7 — Transactions

---

## Part 1 — Transaction kyu exist karta hai

Book shuruat me ek list deti hai — **kya-kya galat ho sakta hai:**

- DB ka software/hardware kabhi bhi mar sakta hai (write ke beech me bhi)
- Application kabhi bhi crash ho sakta hai (operations ki series ke aadhe me)
- Network app ko DB se kaat sakta hai
- Kai clients ek saath likh sakte hain, ek doosre ke changes mita sakte hain
- Client aisa data padh sakta hai jo aadha updated hai
- Race conditions surprising bugs de sakti hain

In sabko handle karna bahut kaam hai. Har failure case sochna padega, phir test karna padega ki solution actually kaam karta hai.

**Transaction ka pura maqsad:** ye saara sochna DB ko de do. Kai reads aur writes ko ek logical unit me baandh do. Ya poora chalega (commit), ya poora ud jayega (abort/rollback). Beech ka koi state nahi.

Book ka ek line jo yaad rakhna:

> *Transactions are not a law of nature; they were created with a purpose — to simplify the programming model.*

Matlab ye koi jaadu nahi hai. Ye ek tool hai jiska cost hai. Aur kabhi kabhi usse weaken karna ya chhod dena sahi hota hai (performance/availability ke liye). Toh sawaal ye nahi ki *"transaction use karu?"*, sawaal ye hai ki *"mujhe kaunsi guarantee chahiye, aur uska cost kya hai?"*

---

## Part 2 — ACID ka sach (yahan sabse zyada log confuse hote hain)

ACID 1983 me coined hua. Par book bilkul saaf bolti hai:

> *Today, when a system claims to be "ACID compliant," it's unclear what guarantees you can actually expect. ACID has unfortunately become mostly a marketing term.*

Ek-ek letter dekho.

### A — Atomicity (aur ye naam hi galat hai)
**Sabse important galatfehmi:** ACID me atomicity ka concurrency se koi lena dena nahi hai.

Multi-threaded programming me "atomic" ka matlab hota hai — koi doosra thread aadha result nahi dekh sakta. ACID me wo cheez **"I" (Isolation)** ke andar aati hai, "A" me nahi.

ACID atomicity ka matlab hai: agar tum 5 writes kar rahe ho aur 3rd ke baad fault aa gaya (process crash, network cut, disk full, constraint violation), toh DB pehle 3 writes ko undo kar dega.

Book ka jawab:

> *Perhaps abortability would have been a better term than atomicity.*

Aur iska asli fayda kya hai? **Retry safe ho jaata hai.** Agar transaction abort hua, tumhe pakka pata hai ki kuch nahi badla — toh dobara try kar sakte ho. Warna tumhe pata hi nahi chalega ki kaunse changes lag gaye aur kaunse nahi, aur dobara try karne pe wahi change do baar ho sakta hai.

### C — Consistency (ye ACID me hona hi nahi chahiye tha)
Book bolti hai "consistency" shabd terribly overloaded hai — 4 alag matlab hain (replica consistency, consistent hashing, CAP ka consistency = linearizability, aur ACID ka consistency).

ACID me iska matlab: tumhare data ke baare me kuch invariants hain jo hamesha sach hone chahiye. Jaise accounting me credits aur debits balance hone chahiye.

Par ye DB guarantee nahi kar sakta. Ye application ki zimmedari hai. Agar tum bura data likhoge jo invariant todta hai, DB tumhe rok nahi sakta.

> *Atomicity, isolation, and durability are properties of the database, whereas consistency (in the ACID sense) is a property of the application. Thus, the letter C doesn't really belong in ACID.*

Footnote me Joe Hellerstein ka comment hai ki C ko *"acronym banane ke liye ghusaya gaya tha"* — 1983 me use important nahi maana gaya tha. 😄

### I — Isolation
Concurrently chalne wale transactions ek doosre ke pair pe nahi chadhne chahiye.

Figure 7-1 dekho — ye poore chapter ki neev hai. Do clients ek counter increment kar rahe hain. Counter 42 se 44 hona chahiye tha (do increment hue), par actually 43 hua. Ek increment kho gaya.

Textbook isolation ko serializability ke roop me define karta hai: har transaction ye pretend kar sakta hai ki wo akela chal raha hai. DB guarantee karta hai ki result waisa hi hoga jaise wo ek-ek karke (serially) chale hote.

Par practice me serializable use hi nahi hota, kyunki performance cost hai. Oracle 11g me toh implement bhi nahi hai — usme "serializable" naam ka level hai jo actually snapshot isolation hai, jo weaker hai.

### D — Durability
Commit ho gaya = data nahi jayega. Single node pe iska matlab disk/SSD pe likh diya, aur usually write-ahead log bhi. Replicated DB me iska matlab kuch nodes pe copy ho gaya.

Par book ka honest hissa ye hai — **perfect durability exist nahi karti:**

- Disk pe likha par machine mar gayi → data safe hai par inaccessible
- Correlated fault (power outage, ya ek bug jo har node ko crash kare) → saare replicas ek saath gir sakte hain
- Async replication me leader marne pe recent writes kho sakti hain
- SSDs power cut pe apni guarantee tod dete hain — fsync bhi guaranteed nahi
- Ek study: 30% se 80% SSDs char saal me kam se kam ek bad block develop karte hain
- SSD ko power se hataao toh kuch hafton me data kho sakta hai

> *There is no one technique that can provide absolute guarantees. There are only various risk-reduction techniques... it's wise to take any theoretical "guarantees" with a healthy grain of salt.*

Ye tumhare Week 0 ke pattern se match karta hai — har jagah certainty nahi, sirf risk reduction.

---

## Part 3 — Single-object aur multi-object

### Single object pe bhi problem hoti hai
Socho tum ek 20 KB JSON document likh rahe ho:

- 10 KB ke baad network toota → DB wo aadha-toota JSON store karega?
- Power gaya likhte waqt → purani aur nayi value spliced mil jayegi?
- Koi padhe likhte waqt → partially updated value dikhegi?

Isliye storage engines single object pe atomicity aur isolation almost universally dete hain. Atomicity log se (crash recovery), isolation per-object lock se.

Kuch DBs zyada bhi dete hain:
- **Atomic increment** — read-modify-write cycle ki zarurat khatam
- **Compare-and-set** — write sirf tab ho jab value beech me kisi ne na badli ho

Par ye transactions nahi hain. Book saaf bolti hai — inhe "lightweight transactions" ya "ACID" bolna marketing hai aur misleading hai. Transaction ka matlab hai multiple objects pe multiple operations ko ek unit banana.

### Multi-object kab zaroori hai
- **Foreign keys** — ek table ki row doosri table ko refer karti hai, references valid rehne chahiye
- **Denormalized data** — jaise unread email counter. Update ek saath hone chahiye warna sync se bahar
- **Secondary indexes** — value badalne pe index bhi update hota hai. Bina isolation, record ek index me dikhega, doosre me nahi

Relational DB me transaction ki boundary usually TCP connection se decide hoti hai — `BEGIN` se `COMMIT` tak sab ek transaction.

Aur yahan book ka footnote iii bilkul Day 4 ka insight hai:

> *If the interruption happens after the client has requested a commit but before the server acknowledges that the commit happened, the client doesn't know whether the transaction was committed or not.*

Ye exactly tumhara read timeout = "pata nahi" hai. Kal tumne khud ye pakda tha, aur DDIA wahi bol rahi hai.

---

## Part 4 — Retry ka jaal (ye section chhota hai par bahut important)

Transaction ka core feature: abort karke safely retry kar sakte ho. Par book batati hai ki retry perfect nahi hai:

1. **Succeeded-but-ack-lost** — transaction actually succeed ho gaya, par network toot gaya jab server acknowledge kar raha tha. Client ko laga fail hua. Retry kiya → kaam do baar hua.
   > *unless you have an additional application-level deduplication mechanism in place.*  
   Ye literally Relay ke idempotency key ka justification hai, DDIA ke shabdon me.

2. **Overload pe retry problem badhata hai** — agar error load ki wajah se hai, retry aur load daalega. Isliye: retry count limit karo, exponential backoff use karo, aur overload errors ko baaki errors se alag treat karo.

3. **Sirf transient errors pe retry karna** — deadlock, isolation violation, temporary network issue, failover. Permanent error (constraint violation) pe retry bekaar hai.

4. **DB ke bahar ke side effects** — transaction abort ho gaya par email chala gaya. Abort side effect ko undo nahi karta.

5. **Client retry karte waqt khud mar gaya** → data gaya.

Aur ek observation jo book me hai aur real hai: ORMs (Rails ActiveRecord, Django) aborted transactions ko retry nahi karte — exception upar chala jaata hai, user input phenk diya jaata hai, user ko error dikhta hai. Book bolti hai ye "a shame" hai kyunki abort ka pura point hi safe retry enable karna tha.

---

## Part 5 — Read Committed (Postgres ka default = aaj tumhara experiment)

Ye sabse basic level hai. Do guarantees deta hai — dono alag hain, dono samajhna:

### Guarantee 1 — No dirty reads
Tum sirf committed data dekhoge. Kisi uncommitted transaction ka writes tumhe nahi dikhega.

Figure 7-4: user 1 ne `x = 3` set kiya par commit nahi kiya. User 2 ko abhi bhi purani value 2 dikhti hai. Commit hone ke baad hi naya value dikhta hai, aur saare writes ek saath dikhte hain.

**Ye kyu chahiye:**
- Multi-object update me kuch changes dikhein aur kuch nahi → Figure 7-2 wala email case (naya email dikha par counter purana). Ye confusing hai aur doosre transactions galat decisions le sakte hain.
- Agar transaction abort ho gaya, toh uske writes rollback honge. Dirty read allow karne ka matlab tum aisa data dekh sakte ho jo kabhi commit hi nahi hua.

### Guarantee 2 — No dirty writes
Do transactions same object likhna chahte hain. Normally hum maante hain baad wala pehle wale ko overwrite karega. Par agar pehla write ek uncommitted transaction ka hissa hai, aur doosra usko overwrite kar de — wo dirty write hai.

Figure 7-5 dekho — used car website. Alice aur Bob dono same car khareed rahe hain. Car kharidne me do writes hain: listings table me buyer update, aur invoices me invoice.

Result: sale Bob ko mila (usne listings ka winning update kiya), par invoice Alice ko gaya (usne invoices ka winning update kiya). Read Committed isse rokta hai.

Par dhyan do: Read Committed Figure 7-1 wala counter problem NAHI rokta. Kyunki wahan doosra write pehle transaction ke commit hone ke baad hota hai — toh wo dirty write hi nahi hai. Galat hai, par alag reason se.

### Implementation — ye detail important hai
Dirty writes rokne ke liye: row-level locks. Object modify karne se pehle uska lock lo, aur transaction end tak hold karo. Ek waqt me ek hi transaction lock rakh sakta hai.

Dirty reads rokne ke liye — yahan trick hai. Same lock read pe bhi laga sakte the (read karne se pehle lock lo, turant chhod do). Par ye practice me bura hai:

> *one long-running write transaction can force many read-only transactions to wait... a slowdown in one part of an application can have a knock-on effect in a completely different part.*

Toh actual solution: DB do versions yaad rakhta hai — purana committed value, aur naya uncommitted value. Jo padhna chahta hai use purana de dete hain. Commit hone pe sab naye pe switch ho jaate hain.

Book ka footnote vi: sirf IBM DB2 aur MS SQL Server (ek specific config me) read committed ke liye locks use karte hain. Baaki sab ye version-wala tareeka.

---

## Part 6 — Snapshot Isolation aur MVCC

### Problem jo Read Committed nahi solve karta: Read Skew
Figure 7-6 dekho. Alice ke paas $1000 hain, do accounts me $500-$500. Ek transaction $100 transfer kar raha hai.

Alice galat waqt pe dekhti hai:
- Account 1: $500 (paisa aane se pehle ka state)
- Account 2: $400 (paisa jaane ke baad ka state)
- Total $900 dikha. $100 hawa me gayab.

Isko nonrepeatable read ya read skew kehte hain. Aur ye Read Committed me acceptable hai — kyunki jo values Alice ne dekhi wo dono committed thi, bas alag-alag time pe.

Alice ke case me ye temporary hai, page refresh karo theek ho jayega. Par kuch cases ye bardaash nahi kar sakte:
- **Backups:** bade DB ka backup ghanto lag sakta hai. Us dauraan writes chalte rehte hain. Result — backup ke kuch hisse purane version ke, kuch naye. Restore karo toh inconsistency permanent ho jayegi.
- **Analytics aur integrity checks:** badi queries jo pura DB scan karti hain. Alag-alag time ke hisse dekhein toh bekaar result denge.

### Solution — Snapshot Isolation
Idea: har transaction ek consistent snapshot se padhta hai. Transaction jab shuru hua, us waqt jo committed tha — bas wahi dikhega. Baad me koi badle toh farq nahi padta.

Aur ye crucial line yaad rakho (Read Committed vs Snapshot Isolation ka asli farq):

> *A typical approach is that read committed uses a separate snapshot for each query, while snapshot isolation uses the same snapshot for an entire transaction.*

Isi wajah se Read Committed me tumhara check-then-act tootta hai — tumhara SELECT aur tumhara UPDATE do alag snapshots dekh rahe hain.

### MVCC — mechanism
Isko multi-version concurrency control kehte hain. DB ek object ke kai committed versions saath-saath rakhta hai.

Performance ka core principle — ise ratt lo:

> *readers never block writers, and writers never block readers.*

Iska matlab: lambi read query chal sakti hai aur writes normally chalte rahenge, koi lock contention nahi.

Figure 7-7 dekho — Postgres ka actual implementation:
- Har transaction ko ek unique, badhta hua transaction ID (txid) milta hai
- Har row me `created_by` field — kis txid ne banaya
- Har row me `deleted_by` field — shuru me khali
- Delete actually delete nahi karta — bas `deleted_by` me txid daal deta hai. Baad me jab pakka ho jaye ki koi transaction us data ko access nahi kar sakta, tab garbage collection use hata deta hai.

Update = delete + create. Figure 7-7 me transaction 13 ne account 2 se $100 kaate ($500 → $400). Ab accounts table me account 2 ki do rows hain:
- $500 wali, jise txid 13 ne deleted mark kiya
- $400 wali, jise txid 13 ne banaya

### Visibility ke 4 rules (ye precise mechanism hai)
Transaction padhte waqt kaise decide karta hai ki kya dikhega:
1. Transaction shuru hote waqt DB un saare transactions ki list banata hai jo in-progress hain. Unke writes ignore honge — chahe wo baad me commit ho jayein.
2. Aborted transactions ke writes ignore honge.
3. Jinka txid bada hai (jo tumhare baad shuru hue) unke writes ignore honge — chahe commit ho gaye hon.
4. Baaki sab visible hai.

Ya doosre shabdon me — object visible hai agar dono sach hain:
- Jab reader ka transaction shuru hua, usko banane wala transaction already commit ho chuka tha
- Object delete-marked nahi hai; ya hai, toh delete karne wala transaction reader ke shuru hone tak commit nahi hua tha

Figure 7-7 me: txid 12 account 2 padhta hai toh $500 dikhta hai — kyunki $500 ka deletion txid 13 ne kiya (rule 3 se txid 12 use nahi dekh sakta), aur $400 ka creation bhi usi rule se nahi dikhta.

Cost: value ko jagah pe update nahi karte, har baar naya version banate hain. Isse consistent snapshot mil jaata hai bas thoda overhead pe. Par garbage collection ka kaam badhta hai.

### Naming ka bawaal (ye jaan lena zaroori hai)
Snapshot isolation ko har DB alag naam se bulata hai:

| DB | Naam |
|---|---|
| Oracle | serializable |
| PostgreSQL | repeatable read |
| MySQL | repeatable read |
| IBM DB2 | "repeatable read" ka matlab serializability |

Kyu? Kyunki SQL standard 1975 ke System R definitions pe based hai, aur snapshot isolation tab invent hua hi nahi tha. Standard me "repeatable read" hai jo superficially similar dikhta hai, toh PG/MySQL usko wahi bol dete hain aur "standards compliant" claim kar lete hain.

Book ka verdict:

> *The SQL standard's definition of isolation levels is flawed — it is ambiguous, imprecise, and not as implementation-independent as a standard should be... As a result, nobody really knows what repeatable read means.*

Isliye aaj jab tum REPEATABLE READ test karoge, naam pe bharosa mat karo — behaviour measure karo.

---

## Part 7 — Lost Update (aaj ka Exp 1) aur uske 5 ilaaj

### Problem
Read-modify-write cycle. App value padhta hai, modify karta hai, wapas likhta hai. Do transactions ek saath karein → ek modification kho jaata hai, kyunki doosra write pehle wale ka change include nahi karta.

Book kehti hai baad wala write pehle wale ko "clobbers" karta hai.

**Kahan hota hai:**
- Counter ya account balance increment
- JSON document ke andar list me element add karna (parse → change → write back)
- Do users same wiki page edit kar rahe hain, dono poora page bhej rahe hain

### Ilaaj 1 — Atomic write operations (best, agar possible ho)
```sql
UPDATE counters SET value = value + 1 WHERE key = 'foo';
```
Ye concurrency-safe hai. Read-modify-write cycle application code me hi nahi hai.

Implementation: object read karte waqt exclusive lock le liya jaata hai, jab tak update apply na ho. Isko cursor stability kehte hain.

Warning jo book deti hai: ORMs bahut aasani se aisa code likhwa dete hain jo unsafe read-modify-write karta hai, jabki DB atomic operation deta tha. Aur ye bug testing se pakadna mushkil hai.

### Ilaaj 2 — Explicit locking (FOR UPDATE) — aaj tum ye karoge
```sql
BEGIN TRANSACTION;
SELECT * FROM figures
  WHERE name = 'robot' AND game_id = 222
  FOR UPDATE;
-- move valid hai ya nahi check karo, phir position update karo
UPDATE figures SET position = 'c4' WHERE id = 1234;
COMMIT;
```
`FOR UPDATE` DB ko bolta hai: iss query se jo rows aayi, un sab pe lock lo.

Ye kab chahiye atomic operation ki jagah? Jab logic DB query me express nahi ho sakta — jaise multiplayer game me "ye move game ke rules ke hisaab se valid hai ya nahi."

Book ki warning: ye kaam karta hai par tumhe carefully sochna padta hai. Code me kahin lock lagana bhool jao toh race condition aa jaati hai.

### Ilaaj 3 — Automatic detection
Locks aur atomic ops rokte hain (read-modify-write ko serial banate hain). Alternative: parallel chalne do, aur agar transaction manager lost update detect kar le toh transaction abort karo aur retry karao.

Fayda: snapshot isolation ke saath ye check efficiently ho jaata hai.

Ye table dhyan se dekho — real behaviour hai:

| DB + level | Lost update detect karta hai? |
|---|---|
| PostgreSQL repeatable read | ✅ Haan |
| Oracle serializable | ✅ Haan |
| SQL Server snapshot isolation | ✅ Haan |
| MySQL/InnoDB repeatable read | ❌ Nahi |

Isliye kuch authors kehte hain ki MySQL snapshot isolation provide hi nahi karta, kyunki lost update prevention snapshot isolation ki definition ka hissa hona chahiye.

Book kehti hai detection better hai kyunki application ko kuch special karne ki zarurat nahi — lock lagana bhool sakte ho, detection automatic hai, isliye less error-prone.

### Ilaaj 4 — Compare-and-set
Jahan transactions nahi hain, wahan ye milta hai. Update sirf tab ho jab value badli na ho:
```sql
UPDATE wiki_pages SET content = 'new content'
  WHERE id = 1234 AND content = 'old content';
```
Par yahan chhupa hua khatra hai — book explicitly warn karti hai:

> *if the database allows the WHERE clause to read from an old snapshot, this statement may not prevent lost updates, because the condition may be true even though another concurrent write is occurring. Check whether your database's compare-and-set operation is safe before relying on it.*

### Ilaaj 5 — Replicated DBs me (alag duniya)
Multi-leader ya leaderless replication me ek up-to-date copy hi nahi hoti. Toh locks aur compare-and-set lagu hi nahi hote (dono maante hain ki ek authoritative copy hai).

Wahan approach: concurrent writes ko kai conflicting versions (siblings) banane do, aur baad me application code ya special data structures se merge karo.

Commutative atomic operations achhe kaam karte hain — jaise counter increment ya set me element add karna. Order badle toh bhi same result. Riak 2.0 ke datatypes yehi karte hain.

Aur ek warning: last write wins (LWW) lost updates ke liye prone hai — aur badqismati se kai replicated DBs me ye default hai.

---

## Part 8 — Write Skew aur Phantoms (aaj ka Exp 2 — chapter ka sabse subtle hissa)

### Problem
Figure 7-8 dekho — doctors on-call example. Hospital rule: kam se kam ek doctor on call hona chahiye.

Alice aur Bob dono on-call hain. Dono bimar hain, dono leave maangte hain, lagbhag ek hi waqt pe button dabate hain.

Har transaction pehle check karta hai: "do ya zyada doctors on call hain?" Snapshot isolation ki wajah se dono checks 2 return karte hain. Dono aage badh jaate hain. Alice apni row update karti hai, Bob apni. Dono commit. Ab koi doctor on call nahi hai. Requirement toot gayi.

### Characterization — ye definition important hai
Ye na dirty write hai, na lost update — kyunki do transactions do alag objects update kar rahe hain (Alice ki row, Bob ki row).

Book ki precise definition:

> *You can think of write skew as a generalization of the lost update problem. Write skew can occur if two transactions read the same objects, and then update some of those objects (different transactions may update different objects). In the special case where different transactions update the same object, you get a dirty write or lost update anomaly.*

Toh hierarchy samajh lo: write skew general case hai. Lost update uska special case hai (jab dono same object likhein).

Aur yahan options bahut kam ho jaate hain:
- Atomic single-object operations kaam nahi karte — multiple objects involved hain
- Automatic lost-update detection bhi kaam nahi karti. Book explicit hai — write skew automatically detect nahi hota PostgreSQL repeatable read, MySQL/InnoDB repeatable read, Oracle serializable, ya SQL Server snapshot isolation me. Automatically rokne ke liye true serializable chahiye.
- Constraints — DB enforce kar sakta hai (unique, foreign key). Par "kam se kam ek doctor on call" ke liye multiple objects wala constraint chahiye, jo most DBs support nahi karte (triggers ya materialized views se kar sakte ho)

Agar serializable use nahi kar sakte, toh second-best: explicitly lock the rows jinpe transaction depend karta hai:
```sql
BEGIN TRANSACTION;
SELECT * FROM doctors
  WHERE on_call = true
  AND shift_id = 1234 FOR UPDATE;

UPDATE doctors
  SET on_call = false
  WHERE name = 'Alice'
  AND shift_id = 1234;
COMMIT;
```

### Chaar aur examples (pattern pehchano)
1. **Meeting room booking** — overlapping booking check karo, na mile toh insert karo. Snapshot isolation doosre user ko concurrently conflicting meeting insert karne se rok nahi sakta.
2. **Multiplayer game** — lock do players ko same figure move karne se rokta hai, par do alag figures ko same position pe move karne se nahi rokta.
3. **Username claim** — do users same username se account bana rahe hain. Check karo, na mile toh banao. Snapshot isolation me safe nahi. Par yahan unique constraint simple solution hai — doosra transaction constraint violation se abort ho jayega.
4. **Double-spending** — user ke paas jitna hai usse zyada kharch na kare. Tentative spending item insert karo, sab items list karo, sum positive check karo. Write skew se do items concurrently insert ho sakte hain jo milke balance negative kar dein, aur kisi transaction ko doosre ka pata na chale.

### Common pattern — teen steps
Book saaf-saaf pattern nikalti hai. Saare examples yahi hain:
1. Ek `SELECT` check karta hai ki koi requirement satisfy hoti hai — search condition se matching rows dhoondh ke
2. Us result ke basis pe application decide karta hai kya karna hai
3. Aage badhne ka faisla hua toh write karta hai (`INSERT`/`UPDATE`/`DELETE`) aur commit

Aur crucial baat:

> *The effect of this write changes the precondition of the decision of step 2. In other words, if you were to repeat the SELECT query from step 1 after committing the write, you would get a different result.*

Yehi wo check-then-act hai jo maine plan me bola tha. DDIA ne isko formally teen steps me tod diya hai.

### Phantoms — ab asli subtle baat
Doctors example me step 3 me jo row modify hui, wo step 1 me return hui rows me se ek thi. Isliye `SELECT FOR UPDATE` se safe kar sakte the.

Par baaki char examples alag hain. Wo rows ki GAIRHAAZIRI check karte hain, aur write ek nayi row add karta hai jo usi condition pe match karti hai.

> *If the query in step 1 doesn't return any rows, SELECT FOR UPDATE can't attach locks to anything.*

Ye effect — jahan ek transaction ka write doosre transaction ki search query ka result badal deta hai — usko phantom kehte hain.

Book: snapshot isolation read-only queries me phantoms se bacha leta hai, par read-write transactions me phantoms write skew ke bahut tricky cases de dete hain.

### Materializing conflicts — last resort
Agar problem ye hai ki lock lagane ke liye koi object hi nahi hai, toh... artificially ek lock object bana do?

Meeting room case me: ek table banao time slots × rooms ka. Har row = ek room, ek time period (jaise 15 min). Aage ke 6 mahine ke saare combinations pehle se bana do.

Ab booking wala transaction desired room aur time ki rows ko `SELECT FOR UPDATE` se lock kar sakta hai. Lock milne ke baad overlapping bookings check karo aur insert karo.

Dhyan do: ye extra table booking ki information store karne ke liye nahi hai. Ye purely locks ka collection hai.

Isko materializing conflicts kehte hain — phantom ko concrete rows pe lock conflict me badal dena.

Par book ka verdict clear hai:

> *it can be hard and error-prone to figure out how to materialize conflicts, and it's ugly to let a concurrency control mechanism leak into the application data model. For those reasons, materializing conflicts should be considered a last resort... A serializable isolation level is much preferable in most cases.*

---

## Part 9 — Serializability ke teen raaste

Pehle book ka honest assessment (ye "sad situation" wala paragraph):
- Isolation levels samajhna mushkil hai, aur different DBs me inconsistently implemented hain
- Apna code dekh ke batana mushkil hai ki kisi particular isolation level pe safe hai ya nahi — khaaskar bade application me jahan tumhe pata bhi nahi ki concurrently kya-kya ho raha hai
- Race conditions detect karne ke acche tools nahi hain. Testing mushkil hai kyunki ye nondeterministic hote hain — sirf tab dikhte hain jab timing se unlucky ho jao

Aur ye 1970s se aisa hi hai. Researchers ka jawab shuru se simple raha: serializable isolation use karo.

Toh sabhi kyu nahi use karte? Kyunki cost hai. Teen implementations hain.

### Raasta 1 — Actual Serial Execution
Sabse simple idea: concurrency hi hata do. Ek waqt me ek transaction, ek single thread pe. Conflicts detect karne ka sawaal hi khatam — result by definition serializable hai.

Ye idea obvious lagta hai, par DB designers ne ~2007 me hi ise feasible maana. Do cheezein badli:
- RAM sasta ho gaya — pura active dataset memory me rakh sakte hain. Data disk se load karne ka wait nahi.
- Realization — OLTP transactions usually chhote hote hain, kam reads/writes karte hain. Lambi analytic queries typically read-only hoti hain, toh unhe snapshot isolation pe alag chala sakte hain, serial loop ke bahar.

VoltDB/H-Store, Redis, Datomic ye approach use karte hain.

#### Stored procedures kyu zaroori ho gaye
Purane zamane me socha gaya tha ki ek transaction pura user flow cover kare — flight booking me search, itinerary, seats, passenger details, payment.

Par insaan bahut slow hai. Agar transaction user input ka wait kare, toh DB ko hazaron concurrent transactions support karne padenge, jinme se most idle honge. Most DBs ye efficiently nahi kar sakte. Isliye almost saare OLTP applications transactions chhote rakhte hain — web pe ek transaction ek HTTP request ke andar commit ho jaata hai.

Par insaan hatane ke baad bhi transactions interactive client/server style me chalte rahe — ek statement at a time. App query bhejta hai, result padhta hai, uske basis pe agli query bhejta hai. Bahut time network communication me jaata hai.

Figure 7-9 dekho — interactive transaction vs stored procedure ka farq (Figure 7-8 ka doctors example use karke).

Toh agar tum single-threaded ho aur interactive transactions allow karo, throughput bekaar ho jayega — DB apna zyada time app ke agli query bhejne ka wait karne me bitayega.

Isliye single-threaded systems interactive multi-statement transactions allow nahi karte. App ko pura transaction code pehle se bhejna padta hai — stored procedure ke roop me.

#### Stored procedures ke problems (aur unka hal)
Book honest hai — inki reputation kharab hai:
- Har vendor ki apni language (Oracle PL/SQL, SQL Server T-SQL, PostgreSQL PL/pgSQL) — ye languages general-purpose languages ke saath develop nahi hui, ugly aur archaic lagti hain, aur library ecosystem nahi hai
- DB me chalne wala code manage karna mushkil — debug karna, version control, deploy, test, monitoring integration — sab awkward
- DB zyada performance-sensitive hoti hai (ek DB instance kai app servers share karte hain), toh ek bura stored procedure app server ke bure code se zyada nuksaan karta hai

Par ye overcome ho sakte hain. Modern implementations general-purpose languages use karte hain: VoltDB → Java/Groovy, Datomic → Java/Clojure, Redis → Lua.

Ek interesting baat: VoltDB replication ke liye bhi stored procedures use karta hai — writes copy karne ke bajaye, wahi stored procedure har replica pe chalata hai. Isliye VoltDB require karta ki stored procedures deterministic hon. Current date/time chahiye toh special deterministic APIs se lena padta hai.

#### Partitioning
Serial execution ka limit: ek single CPU core ki speed. Scale karne ke liye data partition karo.

Agar aisa partition kar sako ki har transaction sirf ek partition ke andar read/write kare, toh har partition ka apna thread ho sakta hai — throughput CPU cores ke saath linearly scale karega.

Par cross-partition transactions bahut mehnge hain. VoltDB ~1,000 cross-partition writes/second report karta hai — jo uske single-partition throughput se orders of magnitude neeche hai, aur machines add karke badhaya nahi ja sakta.

Simple key-value data aasani se partition ho jaata hai. Multiple secondary indexes wala data bahut cross-partition coordination maangta hai.

#### Summary — serial execution kab viable hai
- Har transaction chhota aur fast hona chahiye — ek slow transaction pura processing rok deta hai
- Active dataset memory me fit hona chahiye
- Write throughput ek CPU core pe handle hona chahiye, warna partition karna padega
- Cross-partition transactions possible hain par unki hard limit hai

### Raasta 2 — Two-Phase Locking (2PL)
~30 saal ye ek hi widely used algorithm tha.

2PL is not 2PC. Two-phase locking aur two-phase commit bilkul alag cheezein hain.

Dirty writes rokne wale locks yaad hain? 2PL similar hai par requirements bahut stronger hain:

Kai transactions ek saath padh sakte hain jab tak koi likh na raha ho. Par jaise hi koi likhna chahe, exclusive access chahiye:
- A ne object padha hai aur B likhna chahta hai → B ko wait karna padega jab tak A commit/abort na kare
- A ne object likha hai aur B padhna chahta hai → B ko wait karna padega

Aur yahi wo critical farq hai:

> *In 2PL, writers don't just block other writers; they also block readers and vice versa. Snapshot isolation ka mantra tha: readers never block writers, and writers never block readers.*

Iska matlab 2PL serializability deta hai — lost updates aur write skew, sab race conditions se protection.

#### Implementation
Har object pe ek lock, shared ya exclusive mode me:
- Read karna hai → shared mode me lock lo. Kai transactions ek saath shared rakh sakte hain. Par agar kisi ke paas exclusive lock hai, toh wait karo.
- Write karna hai → exclusive mode me lock lo. Koi doosra lock nahi rakh sakta (shared bhi nahi). Koi bhi existing lock hai toh wait karo.
- Pehle read phir write → shared lock ko exclusive me upgrade kar sakte ho
- Lock transaction ke end tak hold karna padta hai (commit ya abort)

"Two-phase" naam kahan se aaya: pehla phase (transaction chalte waqt) = locks acquire hote hain. Doosra phase (transaction ke end pe) = saare locks release hote hain.

#### Deadlocks
Itne locks use ho rahe hain ki aasani se ho jaata hai — A, B ke lock ka wait kar raha hai, aur B, A ke. Isko deadlock kehte hain.

DB automatically detect karta hai aur ek transaction abort kar deta hai. Aborted transaction ko application ko retry karna padta hai.

#### Performance — yehi wajah hai ki sab use nahi karte
> *transaction throughput and response times of queries are significantly worse under two-phase locking than under weak isolation.*

Kyu:
- Locks acquire/release ka overhead
- Zyada important: reduced concurrency. By design, agar do transactions kuch aisa karein jo kisi bhi tarah race condition de sakta hai, ek ko doosre ka wait karna padega

Aur ek subtle problem: traditional relational DBs transaction ki duration limit nahi karte (kyunki wo interactive apps ke liye design hue the jo human input ka wait karte hain). Toh jab ek transaction doosre ka wait kare, kitni der wait karega uski koi limit nahi. Tum apne transactions chhote rakho phir bhi, agar kai transactions same object chahte hain toh queue ban jaayegi.

Result:

> *databases running 2PL can have quite unstable latencies, and they can be very slow at high percentiles if there is contention... It may take just one slow transaction, or one transaction that accesses a lot of data and acquires many locks, to cause the rest of the system to grind to a halt.*

Aur deadlocks 2PL me bahut zyada frequent hote hain. Deadlock se abort hone pe transaction ko pura kaam dobara karna padta hai — agar deadlocks frequent hain toh ye significant wasted effort hai.

#### Predicate locks — phantoms ka theoretical hal
Serializable DB ko phantoms rokne padte hain. Meeting room example me: agar ek transaction ne kisi room ke kisi time window me bookings search ki hain, toh doosre transaction ko usi room aur time range me booking insert/update allow nahi hona chahiye.

Kaise? Conceptually ek predicate lock chahiye. Ye shared/exclusive lock jaisa hi hai, par ye kisi ek object ka nahi — un saare objects ka hai jo kisi search condition pe match karte hain:
```sql
SELECT * FROM bookings
WHERE room_id = 123 AND
      end_time > '2018-01-01 12:00' AND
      start_time < '2018-01-01 13:00';
```
- A ko condition matching objects padhne hain → us condition pe shared-mode predicate lock lo. Agar B ke paas koi matching object pe exclusive lock hai, A wait karega.
- A ko kuch insert/update/delete karna hai → pehle check karo ki purani ya nayi value kisi existing predicate lock pe match karti hai. Match kare toh wait karo.

Aur ye key idea hai:

> *a predicate lock applies even to objects that do not yet exist in the database, but which might be added in the future (phantoms).*

#### Index-range locks — practical approximation
Predicate locks acche perform nahi karte — active transactions ke bahut locks hon toh matching locks check karna time-consuming ho jaata hai. Isliye most 2PL DBs actually index-range locking (ya next-key locking) karte hain.

Aur ye insight important hai:

> *It's safe to simplify a predicate by making it match a GREATER set of objects.*

Room 123 ke noon-1pm ka predicate lock ho, toh use approximate kar sakte ho:
- Room 123 ki kisi bhi time ki bookings lock karke, ya
- Saare rooms ki noon-1pm bookings lock karke

Ye safe hai, kyunki jo write original predicate pe match karega wo definitely approximation pe bhi match karega.

Practically: agar `room_id` pe index hai, DB us index entry pe shared lock attach kar deta hai. Ya time-based index ho toh us index me values ki range pe lock.

Ab doosra transaction usi room/overlapping time ki booking insert karna chahe toh use index ka wahi hissa update karna padega — wahan wo shared lock milega aur wait karna padega.

Index-range locks predicate locks jitne precise nahi hain (zaroorat se badi range lock kar sakte hain), par overhead bahut kam hai — good compromise.

Aur agar koi suitable index na mile? DB poori table pe shared lock le lega. Performance ke liye bura hai, par safe fallback hai.

### Raasta 3 — Serializable Snapshot Isolation (SSI)
Book pehle situation ka summary deti hai:

> *On the one hand, we have implementations of serializability that don't perform well (2PL) or don't scale well (serial execution). On the other hand, we have weak isolation levels that have good performance, but are prone to various race conditions. Are serializable isolation and good performance fundamentally at odds?*
>
> *Perhaps not.*

SSI full serializability deta hai, snapshot isolation ke muqable sirf chhota performance penalty ke saath.

SSI naya hai — pehli baar 2008 me describe hua (Michael Cahill ki PhD thesis). Aaj PostgreSQL me version 9.1 se serializable isolation level SSI hai. FoundationDB similar algorithm use karta hai.

#### Pessimistic vs Optimistic — ye framing zaroori hai
2PL pessimistic hai: principle ye hai ki agar kuch bhi galat ho sakta hai (doosre ka lock dikha), toh behtar hai wait karo jab tak situation safe na ho. Ye mutual exclusion jaisa hai.

Serial execution extreme pessimistic hai — essentially har transaction ke paas pure DB ka exclusive lock hai. Iss pessimism ko compensate karte hain transactions ko bahut fast banake, taki "lock" kam time hold karna pade.

SSI optimistic hai: kuch potentially dangerous ho raha hai toh block nahi karte — transactions chalte rehte hain, umeed me ki sab theek ho jayega. Jab commit karna ho, DB check karta hai ki kuch bura hua tha kya. Hua toh abort aur retry. Sirf wo transactions commit hote hain jo serializably execute hue.

Optimistic ka tradeoff (ye purana debate hai):
- High contention (bahut transactions same objects pe) me bura perform karta hai — bahut transactions abort hote hain. Aur agar system already apne max throughput ke paas hai, toh retried transactions ka extra load performance aur bigaad deta hai.
- Agar spare capacity hai aur contention zyada nahi, toh optimistic techniques pessimistic se better perform karte hain.

Contention kam karne ka ek tareeka: commutative atomic operations. Jaise kai transactions counter increment karna chahte hain — order se farq nahi podta (jab tak usi transaction me counter read na ho), toh saare increments bina conflict apply ho sakte hain.

SSI snapshot isolation pe based hai — saare reads consistent snapshot se. Uske upar SSI ek algorithm add karta hai jo write conflicts detect karta hai aur decide karta kisko abort karna hai.

#### "Outdated premise" — SSI ka core idea
Write skew ka pattern yaad karo: transaction data padhta hai, result dekhta hai, aur uske basis pe action leta hai. Par snapshot isolation me, commit ke waqt tak wo original result purana ho chuka ho sakta hai.

Doosre shabdon me: transaction ek premise pe action le raha hai (ek fact jo transaction ke shuru me sach tha — "abhi do doctors on call hain"). Baad me commit ke waqt, premise sach na rahe.

Aur yahan DB ki majboori samjho:

> *When the application makes a query, the database doesn't know how the application logic uses the result of that query. To be safe, the database needs to assume that any change in the query result (the premise) means that writes in that transaction may be invalid.*

Toh serializable isolation dene ke liye DB ko detect karna padega ki transaction ne outdated premise pe action liya, aur us case me abort karna padega.

Do cases hain:

#### Case 1 — Stale MVCC read detect karna
Figure 7-10 dekho.

Snapshot isolation MVCC se implement hota hai. Transaction consistent snapshot se padhta hai, aur un transactions ke writes ignore karta hai jo snapshot lene ke waqt uncommitted the.

Figure 7-10 me: transaction 43 ko Alice `on_call = true` dikhti hai, kyunki transaction 42 (jisne Alice ka status badla) uncommitted hai. Par jab transaction 43 commit karna chahta hai, transaction 42 already commit ho chuka hai. Matlab jo write consistent snapshot padhte waqt ignore kiya gaya tha, wo ab effect me aa gaya hai — aur transaction 43 ka premise ab sach nahi hai.

Toh DB ko track karna padta hai ki kab ek transaction ne MVCC visibility rules ki wajah se doosre ke writes ignore kiye. Commit ke waqt DB check karta hai ki wo ignored writes ab commit ho gaye hain kya. Ho gaye toh abort.

Ek smart sawaal: commit tak wait kyu? Stale read detect hote hi abort kyu nahi?

Book teen reasons deti hai:
- Agar transaction 43 read-only tha, toh abort karne ki zarurat hi nahi — write skew ka risk hi nahi
- Read ke waqt DB ko abhi pata nahi ki ye transaction aage write karega ya nahi
- Transaction 42 khud abort ho sakta hai, ya 43 ke commit hone tak uncommitted reh sakta hai — toh read stale hi na nikle

Aur unnecessary aborts avoid karke SSI, snapshot isolation ka lambi read-only queries wala fayda bachaye rakhta hai.

#### Case 2 — Prior reads ko affect karne wale writes detect karna
Figure 7-11 dekho. Ye ulta case hai — koi transaction data padhne ke baad use modify karta hai.

2PL me index-range locks yaad hain? Yahan similar technique use hoti hai, par SSI ke locks doosre transactions ko block nahi karte.

Figure 7-11 me transactions 42 aur 43 dono shift 1234 ke on-call doctors search karte hain. Agar `shift_id` pe index hai, DB index entry 1234 use karke record kar leta hai ki 42 aur 43 ne ye data padha. (Index na ho toh table level pe track.)

Ye information thodi der ke liye rakhni padti hai: transaction finish hone ke baad, aur saare concurrent transactions finish hone ke baad, DB bhool sakta hai ki usne kya padha.

Jab transaction likhta hai, use indexes me dekhna padta hai ki kaunse doosre transactions ne recently ye data padha. Ye process affected key range pe write lock lene jaisa hai — par readers ke commit hone tak block karne ke bajaye, lock ek **TRIPWIRE** ki tarah kaam karta hai: wo un transactions ko notify kar deta hai ki jo data unhone padha wo ab up-to-date na ho.

Figure 7-11 me: 43 ne 42 ko notify kiya ki uska prior read outdated hai, aur vice versa. Transaction 42 pehle commit karta hai aur successful hota hai — kyunki 43 ka write 42 ko affect karta tha, par 43 ne abhi commit nahi kiya, toh wo write abhi effect me nahi aaya. Par jab 43 commit karna chahta hai, 42 ka conflicting write already commit ho chuka hai — toh 43 ko abort hona padta hai.

#### SSI ki performance
Granularity ka tradeoff: DB har transaction ki activity kitni detail me track kare?
- Zyada detail → precise pata chalega kisko abort karna hai, par bookkeeping overhead badh jayega
- Kam detail → faster, par zaroorat se zyada transactions abort honge

Kuch cases me transaction ko aisi information padhne dena theek hai jo doosre ne overwrite kar di — depending on kya-kya hua, kabhi prove kiya ja sakta hai ki result phir bhi serializable hai. PostgreSQL ye theory use karta hai unnecessary aborts kam karne ke liye.

2PL ke muqable bada fayda:

> *one transaction doesn't need to block waiting for locks held by another transaction. Like under snapshot isolation, writers don't block readers, and vice versa. This design principle makes query latency much more predictable and less variable.*

Khaaskar read-only queries bina kisi lock ke consistent snapshot pe chal sakti hain — read-heavy workloads ke liye bahut appealing.

Serial execution ke muqable: SSI ek CPU core ke throughput tak limited nahi hai. FoundationDB serialization conflict detection kai machines pe distribute karta hai. Data multiple machines pe partitioned ho toh bhi transactions multiple partitions me read/write kar sakte hain serializable isolation ke saath.

Abort rate hi sab kuch decide karta hai: ek transaction jo lambe time tak read aur write kare, uske conflicts me phasne aur abort hone ke chances zyada hain. Toh SSI require karta hai ki read-write transactions kaafi chhote hon (lambi read-only transactions theek hain).

Par book ye bhi kehti hai: SSI probably 2PL ya serial execution se kam sensitive hai slow transactions ke prati.

---

## Part 10 — Chapter ka summary table (revision ke liye)

### Anomaly Matrix
| Anomaly | Kya hota hai | Kaun rokta hai |
|---|---|---|
| Dirty read | Ek client doosre ke uncommitted writes padh leta hai | Read Committed aur usse strong |
| Dirty write | Ek client doosre ka uncommitted write overwrite kar deta hai | Almost saare transaction implementations |
| Read skew (nonrepeatable read) | Client DB ke alag hisse alag time pe dekhta hai | Snapshot isolation (usually MVCC se) |
| Lost update | Do clients concurrently read-modify-write karte hain, ek write kho jaata hai | Kuch snapshot isolation implementations automatically; warna manual lock (SELECT FOR UPDATE) |
| Write skew | Transaction kuch padhta hai, decision leta hai, likhta hai — par likhne tak premise jhoothi ho chuki hai | Sirf serializable |
| Phantom read | Transaction search condition pe rows padhta hai; doosra client aisa write karta hai jo us search ka result badal de | Snapshot isolation simple phantoms rok deta hai; write skew ke context me phantoms ke liye special treatment (index-range locks) chahiye |

### Serializability ke teen raaste:
| Approach | Kab achha hai | Kya cost |
|---|---|---|
| Serial execution | Transactions bahut fast, throughput ek core pe fit, dataset memory me | Stored procedures majboori, cross-partition mehnga, ek slow transaction sab rok deta hai |
| 2PL | Decades ka standard, correct | Unstable latency, bura tail latency, frequent deadlocks |
| SSI | Predictable latency, readers/writers block nahi karte, distribute ho sakta hai | High contention pe abort rate phat jaata hai; read-write transactions chhote rakhne padte hain |

---

### Ab aaj ke experiments ka map
- **Exp 1: counter, 101 instead of 102** → Lost Update (Figure 7-1)
- **Exp 1 + FOR UPDATE** → Explicit locking (Ilaaj 2, Example 7-1)
- **Exp 2: doctors, count 0** → Write Skew (Figure 7-8)
- **Exp 2 at REPEATABLE READ** → Snapshot isolation — write skew NAHI rokega
- **Exp 2 at SERIALIZABLE** → SSI — detect karke abort (40001) (Figure 7-10, 7-11)
- **Exp 3: pg_stat_activity lock wait** → 2PL ka blocking behaviour

### Relay ke liye teen takeaways
1. **Week 1 ka SKIP LOCKED** — ab reason pata hai. Do workers same pending job `SELECT` karte hain aur dono `running` mark karte hain = lost update on the job row (Figure 7-1 ka exact shape). `FOR UPDATE` isse rokta hai kyunki row exist karti hai. `SKIP LOCKED` extra ye karta hai ki doosra worker wait na kare — wo agli available job utha le.

2. **Week 3 ka unique constraint** — ab reason pata hai. Book ne username-claim example me saaf bola: snapshot isolation safe nahi, par unique constraint simple solution hai. Tumhara `idempotency_key` pe unique constraint wahi hai — isolation level pe bharosa nahi, DB ko rule enforce karne do. Ye "materializing conflicts" se saaf aur behtar hai.

3. **Retry ke bina serializable adhura hai.** `SERIALIZABLE` choose karne ka matlab hai 40001 handle karne ka commitment. Aur retry ka matlab Day 4 ka "pata nahi" wapas — jo book me bhi likha: retry safe hai sirf tab jab application-level deduplication ho.

Ab experiments karo. Prediction 3 (REPEATABLE READ pe write skew) ka jawab ab tumhe theory se pata hai — par khud measure karo, kyunki "nobody really knows what repeatable read means" wala point yahi hai: naam se nahi, behaviour se pata chalta hai.
