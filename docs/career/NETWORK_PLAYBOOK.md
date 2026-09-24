# Network Playbook — Ahmedabad / Gandhinagar backend circle

**Purpose:** ek aisa network banana jahan 6–9 mahine baad jab internship ya referral chahiye,
tab maangne se pehle hi log tera naam aur tera kaam jaante hon.

**Owner:** Vishwam · **Base:** Gandhinagar University, Moti Bhoyan (Kalol) · **Started:** _fill date_

Tracker: `docs/career/NETWORK_TRACKER.csv`

---

## 0. The one rule

> **Pehle 4 hafte kuch nahi maangna. Sirf technical baat.**

Reason: referral ek *favour* nahi hai, woh us bande ka **reputation risk** hai. Woh apna naam
tere pe lagata hai. Ajnabi ke liye koi nahi karta. Jo banda tere 2 sawaal answer kar chuka hai
aur tera repo dekh chuka hai, uske liye referral dena low-risk hai — kyunki woh already jaanta
hai tu kaam karta hai.

Isliye ye playbook **relationship-first** hai, aur referral/internship maangna Stage 5 (`5-Bonded`) pe aata hai, Stage 1 pe nahi.

**Planning assumption, guarantee nahi:** kaafi messages unanswered rahenge aur sirf kuch contacts
real conversation tak jayenge. Isliye volume aur consistency dono chahiye — ek mahine me 30
message bhej ke chhod dena kaam nahi karta.

---

## 1. Target map — kis company ke log

Priority order. Har company ke saamne likha hai **kya poochhna** hai, kyunki relevant sawaal
hi reply rate decide karta hai.

### Tier A — pehle inko (domain match strong hai)

| Company | Kya karte hain | Tera hook |
|---|---|---|
| **Crest Data Systems** | Splunk/observability platform integrations, data pipelines | Tera contact already andar hai. Job engine, retry, dedup — direct overlap |
| **Cygnet.One** | GST/tax-tech product, GIFT City | Reconciliation, idempotent transactions, correctness-critical backend |
| **Apexon** (ex-Infostretch) | Digital engineering, US clients | Backend/platform practice |
| **eInfochips** (Arrow) | Product engineering, semiconductor-adjacent | Systems depth. Bond ka sawaal poochhna |
| **GIFT City fintech/BFSI teams** | Payments, trading, banking backends | Exactly-once, ledger, retry semantics |

### Tier B — reply rate zyada, ceiling kam

Simform, TatvaSoft, Softweb Solutions. Log approachable hote hain aur reply karte hain, to
practice ke liye achhe hain. Referral value Tier A se kam.

### Tier C — skip

Agency shops (Mindinventory, Bacancy, Yudiz, X-Byte, Brilworks, Thirdrock, etc.). Ek exception:
agar koi individual engineer wahan interesting technical content likhta hai, to woh banda worth
hai — company nahi.

### Tier D — remote / non-local, high value

Razorpay, Zerodha, Juspay, Atlan, Hasura, Postman ke backend engineers. Ye Ahmedabad me nahi
hain par tera Relay-type kaam inke domain ke closest hai, aur ye log technically zyada engaged
hote hain. Reply rate kam, par jo reply karega woh sabse valuable conversation degi.

---

## 2. Kis banda ko — the profile filter

**Target karo:**
- 2–6 saal experience. **Ye sabse important filter hai.** Senior enough ki referral ka weight ho,
  junior enough ki time ho aur student ki baat relatable lage.
- Title: SDE / Software Engineer / Senior SDE / Platform Engineer / Data Engineer / Backend Engineer
- Profile me actual tech dikhta ho — Python, Postgres, Kafka, queues, distributed systems, AWS
- Bonus: LinkedIn pe technical posts likhta ho, ya GitHub active ho. Aisa banda usually
  engage karne ke liye zyada reachable hota hai — phir bhi reply assume mat karo

**Avoid karo:**
- HR / TA / Recruiter — ye ATS me daalenge, relationship nahi banegi
- CEO / Founder / VP — reply nahi karenge, aur kare bhi to HR ko forward kar denge
- 10+ saal wale — bandwidth nahi, aur tera context unse door hai
- "Open to work" wale — woh khud dhoond rahe hain, help nahi kar paayenge

---

## 3. Logon ko dhoondhne ke exact tareeke

### 3.1 LinkedIn Alumni tool (pehla stop)

1. `linkedin.com/alumni` kholo, ya apne college page pe jaake **Alumni** tab
2. "Gandhinagar University" search karo — **aur** "Gujarat Technological University" bhi try karo,
   bahut log GTU affiliation likhte hain
3. Filters: *Where they work* → company name, *What they do* → Engineering

**Reality check:** GNU Moti Bhoyan ka alumni pool Tier A companies me patla hoga. Ye expect karna.
Isliye alumni angle **primary nahi**, ek bonus hai. Agar 3–4 log mil gaye to woh tere warmest
leads hain — unhe pehle karo.

### 3.2 Company People tab (yahan se bulk aayega)

1. Company page → **People** tab
2. Filter: *What they do* → Engineering, *Where they live* → Ahmedabad / Gandhinagar
3. List scan karo, profile filter (Section 2) apply karo, tracker me daalo

Ek company se 5–8 naam nikaalo. Ek hi baar me sabko message nahi karna — tracker me park karo.

### 3.3 People search + filters

LinkedIn search → People tab → filters:
- *Current company*: Crest Data Systems
- *Locations*: Ahmedabad
- *Keywords/Title*: `backend` ya `python` ya `data engineer`

Boolean bhi chalta hai: `("Crest Data" OR Cygnet) AND (backend OR python)`

### 3.4 GitHub route (sabse under-used, sabse high signal)

- GitHub search: `location:Ahmedabad language:Python`, ya `location:Gandhinagar`
- Jo banda mila, uska LinkedIn dhoondho — ya seedha uske repo pe ek **thoughtful issue** kholo
- Ek achhi issue ya PR 50 LinkedIn messages se zyada credibility deti hai

### 3.5 Local meetups / communities

Ahmedabad me PyCon India regional, GDG Ahmedabad, AWS User Group Ahmedabad type meetups hote
hain. Ek offline meetup = 5–10 warm contacts ek shaam me, aur offline bonding online se 10x
strong hoti hai. Har 2 mahine me ek attend karne ka target rakho.

Dhoondhne ki jagah: Meetup.com (Ahmedabad tech), GDG chapters, LinkedIn Events, Twitter/X pe
`#AhmedabadTech`.

### 3.6 Cold email (jab LinkedIn cap lag jaye)

LinkedIn free account pe personalized invite notes monthly capped hote hain _(exact number
LinkedIn badalta rehta hai — khud check karo)_. Backup: company email pattern guess karo
(`firstname.lastname@company.com`) ya GitHub commits me public email dekho. Email pe reply rate
LinkedIn se kam par cap nahi hai.

---

## 4. Pehle message se PEHLE — profile fix (ek baar, 2 ghante)

Message bhejne se pehle ye zaroori hai, kyunki reply karne se pehle banda tera profile dekhega.
Ahmedabad ke bahut candidates generic web-app portfolios leke aate hain. Tu apna measured
failure-handling work clear rakhega to profile distinguish karna easier hoga.

Checklist:
- [ ] **Headline:** `Backend / Distributed Systems · Python · PostgreSQL · building Relay, a durable job execution engine`
      — "aspiring", "passionate learner", "MERN enthusiast" hata do. Commodity signal hai
- [ ] **About:** 3 line. Kya bana raha hai, kaun si guarantees, kya measure kiya
- [ ] **Featured section:** Relay repo ka link, sabse upar
- [ ] **GitHub profile README:** Relay pinned, ek paragraph me contract likha hua
      (accepted jobs lost nahi hote, crash recoverable, retries bounded, duplicate side effects nahi)
- [ ] **Relay ka README:** koi 60 second me samajh jaye ki ye kya hai aur kya guarantee karta hai
- [ ] **1–2 writeup public:** ek measured finding. Ye tera "proof of thinking" hai jo message me
      link kar sakta hai

**Ye pre-work skip karne ka nuksaan:** reply mil bhi gaya to conversation aage nahi badhegi,
kyunki uske paas tere baare me dekhne ko kuch nahi hoga.

---

## 5. The message ladder — 4 stages, ~6 hafte per person

Har banda in 4 stages se guzarta hai. Stage skip karne se reply rate girta hai.

### Stage 1 — Warm-up (message NAHI)

Connect karne se 3–7 din pehle:
- Uski 1–2 posts pe **substantive comment** karo. "Great post 🔥" nahi — ek actual point ya sawaal
- Uska GitHub repo dekha ho to star/issue

Kyun: jab connection request jayegi, naam pehchana hua hoga. Cold nahi rahega.

### Stage 2 — Connect

Connection request bhejo. Note ki jagah **khali** chhodna better hai jab tak Stage 1 hua ho
(accept rate zyada, aur monthly note cap bachta hai). Agar note bhej raha hai to under 300 chars:

```
Hi <Name> — <College> se hoon, backend/distributed systems pe kaam karta hoon.
<Company> ka <specific thing> wala kaam follow karta hoon. Connect karna chahta tha.
```

### Stage 3 — First real message (accept ke 2–3 din baad)

**Ye sabse important message hai.** Rules:
- 4–6 line, isse zyada nahi
- **Ek** specific technical sawaal. Do nahi
- Apna context ek line me — kya bana raha hai
- **Kuch maangna nahi.** No internship, no referral, no resume, no "guide me"
- Sawaal aisa ho jo Google se na milta ho — unke *production* experience ke baare me

Template:

```
Hi <Name>, thanks for connecting.

Main ek durable job execution engine bana raha hoon (Postgres + Python) — at-least-once
delivery, bounded retries, DLQ. Jo cheez maine measure ki: <one specific measured finding>.

<Company> pe aap log <their domain> pe kaam karte hain — wahan <specific question> kaise
handle karte ho? Main <my approach> use kar raha hoon par production scale pe iska
failure mode nahi samajh paa raha.

Repo, agar dekhna ho: <link>
```

Concrete example:

```
Hi <Name>, thanks for connecting.

Main Relay bana raha hoon — Postgres pe ek durable job queue. Measure karte waqt ek cheez
mili jo mujhe expect nahi thi: rollback hone pe bhi sequence value consume ho jaati hai,
to job IDs me gaps aate hain.

Aap log jo data pipelines chalate ho, unme duplicate execution kaise rokte ho — dedup key
DB-level unique constraint se, ya application level idempotency key se? Maine
`effect_key` pe unique constraint lagayi hai, par worry hai ki ye contention kitna banayegi.

Repo: <link>
```

### Stage 4 — Conversation → bonding (hafte 2 se 12)

- Reply aane pe **12 ghante ke andar** jawab do. Momentum sabse zaroori hai
- Uske jawab pe **actually amal karo**, phir 1–2 hafte baad update bhejo:
  *"aapne jo bola tha usko try kiya, ye hua"* — **ye single move sabse zyada bonding banata hai**,
  kyunki 99% log advice leke gayab ho jaate hain
- Har 3–4 hafte me ek touchpoint. Har touch me kuch naya ho — ek finding, ek writeup, ek sawaal
- 2–3 exchange ke baad, agar vibe achhi hai: 15-min call offer karo. Call >> chat for bonding

Stage 4 me 2–3 mahine rehne aur 3+ useful exchanges/call ke baad tracker ko `5-Bonded` karo.
**Referral/internship ask Stage 5 pe valid hai.**

---

## 6. Sawaal bank — kya poochhna, kya nahi

### Achhe sawaal (production experience maangte hain, Google se nahi milte)

- Duplicate execution production me kaise rokte ho — DB constraint ya app-level idempotency key?
- Retry ke liye exponential backoff use karte ho? Jitter kaise decide kiya?
- Worker crash hone pe in-flight job kaise recover hoti hai — visibility timeout, ya lease/heartbeat?
- DLQ me jaane ke baad kaun dekhta hai? Manual replay ka process hai?
- `SELECT ... FOR UPDATE SKIP LOCKED` use kiya hai kabhi? Contention pe kaisa behave karta hai?
- Postgres ko queue ki tarah use karne pe kab dikkat aayi? Kab Kafka/SQS pe move karna pada?
- Migration production pe kaise chalate ho — downtime window, ya online with NOT VALID constraints?
- Observability: kaun se 3 metrics sabse pehle dekhte ho jab job backlog badhta hai?
- Ek incident jo aapko sabse zyada yaad hai — root cause kya nikla?

### Bure sawaal (reply nahi milega, ya milega to useless)

- "Can you refer me?" — Stage 3 me poison hai
- "How do I get into <company>?" — HR ka sawaal hai, engineer ka nahi
- "Can you mentor me / guide me?" — open-ended, unbounded commitment. Koi haan nahi bolta
- "Roadmap batao / kya seekhu?" — lazy signal. Tu already jaanta hai kya seekhna hai
- "Kitna package milta hai?" — Stage 6 ka sawaal, Stage 3 me nahi
- Koi bhi sawaal jiska jawab documentation me hai — ye credibility maar deta hai

**Test:** sawaal ka jawab StackOverflow pe hai? To mat poochho. Jawab sirf us bande ke
production experience me hai? To perfect hai.

---

## 7. Weekly cadence — Sunday, 45 minutes

Ek fixed slot. Isko Relay ke kaam se alag rakho warna ye kabhi nahi hoga.

```
00–10 min   Tracker kholo. Jo "Next_Action_Date" aaj ya past hai, unko handle karo (follow-ups)
10–20 min   2 naye log dhoondho (Section 3), tracker me Stage 0 pe daalo
20–30 min   Stage 1 warm-up: 3–4 posts pe substantive comment
30–45 min   1–2 Stage 3 messages likho aur bhejo. Personalise karo, copy-paste nahi
```

**Volume target:** hafte me 2 naye + purane sab pe follow-up. Ye chhota lagta hai — 6 mahine me
~50 log ban jate hain, aur consistency hi asli lever hai.

**Anti-goal:** ek din me 20 message. Woh spam lagta hai, reply rate girta hai, aur tu 2 hafte me
burn out hoke chhod dega.

---

## 8. Referral / internship ask — kab aur kaise

**Kab:** tracker me `5-Bonded` ho: minimum 4 hafte + minimum 3 real exchange + ek
"aapki advice apply ki" wala update ho chuka ho. Agar ye teen nahi hue to ask early hai.

**Kaise — ask ko chhota aur specific banao.** "Refer kar do" bada aur vague hai. Ye chhota hai:

```
<Name>, ek chhoti si baat — <Company> me summer internship ya trainee backend roles
khulte hain kya? Main Relay ka core khatam kar chuka hoon (<link>), aur specifically
data-pipeline / platform side pe kaam karna chahta hoon.

Agar aapko lage ki fit hai to bas ye batana kis team se baat karni chahiye — main khud
apply kar loonga. Aur agar referral comfortable ho to obviously bahut madad hogi, par
koi pressure nahi.
```

Kyun ye kaam karta hai:
- "Kis team se baat karun" — ye **information** maang raha hai, favour nahi. Reply karna aasan hai
- "Main khud apply kar loonga" — usse effort se free kar diya
- "Koi pressure nahi" — na bolne ka rasta diya, jo relationship bachata hai
- Repo link — usko justify karne ka material diya jab woh apne manager se bolega

**Ek referral pe do baar nahi maangna.** Na mila to thank karo aur relationship chalu rakho.
6 mahine baad situation badal sakti hai.

---

## 9. Tracker kaise use karna

`docs/career/NETWORK_TRACKER.csv` — Google Sheets me import kar lo (File → Import) ya Excel me
kholo. CSV rakha hai taaki git me diff dikhe aur kahin bhi khule.

**Stage column ki values:**

| Stage | Matlab |
|---|---|
| `0-Identified` | Naam mila, kuch nahi kiya |
| `1-Warmed` | Uski post pe comment kiya / repo pe engage kiya |
| `2-Connected` | Connection accept ho gaya |
| `3-Messaged` | Pehla technical message bhej diya, reply ka wait |
| `4-Conversing` | Reply aaya, 1+ exchange ho chuka |
| `5-Bonded` | 3+ exchange, ya call ho gayi. Ask valid hai |
| `6-Asked` | Referral/internship ask kar diya |
| `X-Dead` | 2 follow-up ke baad no reply. Chhod do, 6 mahine baad phir dekhna |

**Non-negotiable rule:** `Next_Action` aur `Next_Action_Date` **hamesha** bhara hona chahiye.
Khali chhoda = woh lead mar gayi. Sunday ritual isi column pe chalta hai.

---

## 10. Failure modes — jo actually hota hai

| Galti | Kya hota hai | Fix |
|---|---|---|
| Pehle message me referral maangna | Instant ignore, aur woh banda permanently dead | `5-Bonded` se pehle ask nahi |
| Copy-paste template bhejna | Log 5 second me pehchan lete hain | Har message me ek line unke *specific* kaam ki |
| Reply ka jawab 3 din baad | Momentum khatam | 12 ghante ka rule |
| Advice leke gayab | Woh banda dubara effort nahi karega | "Try kiya, ye hua" update bhejo |
| Long paragraphs | Padha hi nahi jayega | 6 line max |
| HR ko message karna | ATS pile | Sirf engineers |
| Ek hafta 20 message, phir 2 mahine kuch nahi | Net zero | Hafte me 2, hamesha |
| Profile fix se pehle outreach | Reply aayega, conversation nahi badhegi | Section 4 pehle |

---

## 11. Ek honest disclaimer

Is playbook me company tiers aur salary-related judgement **public reviews aur second-hand
data** pe based hain (Glassdoor, Indeed, levels.fyi — self-reported aur kuch purane). Allocation
quality bahar se verify nahi hoti. Isliye ye plan **variance kam karta hai, outcome guarantee
nahi karta**.

Aur ek cheez saaf rakhni hai: ye networking **replacement nahi hai** DSA, system design, ya
Relay ka. Woh capability hai, ye distribution hai. Distribution ke bina capability dikhti nahi,
par capability ke bina distribution ka koi matlab nahi. Priority abhi bhi Relay khatam karna hai.

---

## 12. First 30 days — checklist

**Week 0 (abhi, Relay ke saath saath, ~3 ghante total)**
- [ ] Section 4 ka profile fix poora karo
- [ ] Tracker me Tier A ki 4 companies se 10 naam daalo
- [ ] Alumni tool pe GNU + GTU check karo, jo mile unko top pe rakho

**Week 1**
- [ ] Crest wale contact se woh do sawaal poochho: practice-based ya project-based allocation,
      aur backend/data side pe fresher ko kya milta hai
- [ ] 3 logon ki posts pe substantive comment (Stage 1)
- [ ] 2 connection request

**Week 2**
- [ ] 2 Stage 3 technical messages
- [ ] Ek measured finding ka writeup public karo

**Week 3**
- [ ] 2 naye log add
- [ ] Jo reply aaye unpe follow-up + "try kiya" update
- [ ] Ek local meetup dhoondho aur register karo

**Week 4**
- [ ] Review: kitne Stage 3+ pe hain? Kitne dead?
- [ ] Jo reply nahi kiye, ek follow-up, phir `X-Dead`
- [ ] Cadence lock: har Sunday 45 min

Iske baad Section 7 ka weekly loop chalta rehta hai. Bas.

## 13. Sources and verification boundary

Ye document outreach workflow deta hai; kisi individual employee, opening, salary, project allocation,
ya internship availability ko verified fact nahi maanta. Ye sab outreach se pehle current company page,
job page, aur person ke current profile par verify karna hai.

Useful starting sources:

- [LinkedIn Alumni Tool entry point](https://www.linkedin.com/alumni) — college alumni ko current
  company/location se filter karne ke liye. Tool usage ka independent overview:
  [Highperformr guide](https://highperformr.ai/blog/how-to-find-alumni-on-linkedin/).
- [Crest Data Systems employee reviews in Ahmedabad](https://www.glassdoor.com/Reviews/Crest-Data-Systems-Ahmedabad-Reviews-EI_IE1647826.0,18_IL.19,28_IC2935226.htm)
  — employee-generated evidence; project quality aur culture person/team ke hisaab se vary kar sakte hain.
- [Crest Data Systems salary page](https://in.indeed.com/cmp/Crest-Data-Systems/salaries?location=IN/GJ/Ahmedabad)
  — self-reported/estimated data, offer expectation nahi.
- [eInfochips company overview](https://in.indeed.com/cmp/Einfochips) — product-engineering focus ka
  starting point; current role aur employment terms official careers page/interview me verify karo.
- [TatvaSoft careers](https://www.tatvasoft.com/career) — current openings ka official starting point.
- [Ahmedabad backend search on LinkedIn](https://in.linkedin.com/jobs/backend-developer-jobs-ahmedabad)
  — live availability frequently change hoti hai; company quality ka evidence nahi.

**Verification rule:** company ke baare me public review ko signal samjho, truth nahi. Actual decision se
pehle kam-se-kam do current engineers se independently practice structure, client exposure, bond,
on-call expectations, aur fresher allocation verify karo. Kisi specific person ka naam tracker me tabhi
dalo jab uska current profile khud dekh liya ho.

Content sourced from public pages was summarized and rephrased for compliance with licensing restrictions.
