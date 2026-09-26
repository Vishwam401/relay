<!--
  Week 4 Din 4 — ANSWERS / frozen prediction card template.

  HOW TO USE THIS FILE (Step 0C):
    1. Sirf `### Prediction` blocks bharo. Apne head se, KEY kholne se PEHLE, Gemini se poochne se PEHLE.
       `idk` ek valid answer hai aur wo `0` score karta hai — ek guess ko knowledge ki tarah likhna usse bura hai.
    2. `### Observed + meri explanation` aur `### After KEY` freeze ke waqt KHAALI rehne chahiye.
       Step 0C ka seal command inhe check karta hai aur non-empty hone pe `throw` karta hai.
    3. Freeze karo (Step 0C). Wo is file ki ek immutable copy DIN_04_PREDICTIONS_FROZEN.md banata hai.
       Us copy ko phir kabhi chhoona nahi. Ye file (ANSWERS) din bhar badalti rehti hai.
    4. Har step ke measurement ke TURANT BAAD uss question ka `### Observed + meri explanation` bharo —
       pehle apni explanation, phir Gemini ke saath output pe reason karo. Din ke ant me nahi, tab bhool jaate ho.
    5. USKE BAAD KEY ka relevant section kholo aur `### After KEY` bharo.
    6. Din ke ant me is file ke END me ek `## Total Score` section ADD karo — freeze ke waqt wo maujood
       NAHI hona chahiye, warna wo Q5 ke `### After KEY` block ka hissa ban jaata hai aur seal command
       usko non-empty samajh ke `throw` karega. Shape:

           ## Total Score
           SCORE: x.x/5.0
           - Q1: _._/1.0 — <reason>
           ... Q5 tak

       Part-marks explicitly likho, e.g. "Q3: 0.5/1.0 — (b) ka Conflict-on-mark half NOT ANSWERED".
       Chat me nahi, is file me.

  Question ka poora text BRIEF ke Part B me hai. Yahan short form hai taaki cards ordered rahein.
  Structure ko badalna nahi — seal command `## Q1..Q5` order aur teeno headings exactly maangta hai.
-->

## Q1
`src/database.py` import pe `load_dotenv()` chalata hai (`override=False`) aur `DATABASE_URL = os.environ["DATABASE_URL"]` ek module-level constant hai; `engine` usi waqt banta hai. Repo root ka `.env` `relay` pe point karta hai. Tum PowerShell me `$env:DATABASE_URL` ko `relay_w4_witness` pe set karke `python -m src.worker` chalate ho.
(a) Worker kis DB pe connect karega — `.env` jeeta ya shell?
(b) Usi terminal se `python -m alembic upgrade head`. Kis DB pe, aur kyu?
(c) Ek naya PowerShell tab, kuch set kiye bina, wahi worker command. Kis DB pe?

### Prediction
(a) shyd database new banega us se connect karega, idk.
(b) temp db banaya usi me chalega shyd.
(c) normal me to fir apne original db me rahega.

### Observed + meri explanation


### After KEY


## Q2
Do asli worker process, ek hi `pending` row. Dono ka claim `SELECT ... WHERE status='pending' ORDER BY created_at, id LIMIT 1 FOR UPDATE SKIP LOCKED` phir ek guarded `UPDATE ... WHERE id=:id AND status='pending'`. `READ COMMITTED`.
Kitne worker claim karenge, aur **haarne wale** ke stdout me kya aayega — teen possibilities hain (empty poll · `Conflict: ... rowcount=0` · ek error) aur jawab iss pe hai ki `SKIP LOCKED` ne usko row **dikhayi** thi ya nahi. Ek chuno aur mechanism likho.

### Prediction
Ek worker uthayega. Doosra worker agar doosri row hogi to wahan chala jayega simple, aur agar nahi to polling pe chala jayega (empty poll).

### Observed + meri explanation


### After KEY


## Q3
Interleaving A: worker A ne claim kiya (generation `g`), `45 s` blocking handler chal raha hai, lease `30 s` pe expire hui, reaper ne reclaim kiya, worker B ne claim kiya. Ab A apna mark chalata hai: `WHERE id=:id AND status='running' AND claim_generation=:g`.
(a) `rowcount` kya hoga?
(b) A ke stdout me `Mark fenced` aayega ya `Conflict on mark` — aur reaper ke reclaim ke **baad** par B ke claim se **pehle** A mark karta to kaunsa aata?
(c) A ke paas `status`, `next_attempt_at`, `completed_at`, `last_error` — chaar value thi. Rejection ke baad in chaar ka DB me kya hota hai?

### Prediction
(a) rowcount 1 hi aayega.
(b) Mark fenced aayega bcz worker 2 ne token bada diya tha to ab wo purana token leke change karega to nahi hoga.
(c) idk, shyd clear ya aisa kuch hota hoga.

### Observed + meri explanation


### After KEY


## Q4
Step 1 me `sink_deliveries.idempotency_key` pe `UNIQUE` aa gaya hai. Ab do dispatcher process ek hi outbox row pe, bilkul same instant, dono ne wahi `idempotency_key` bheji.
(a) `sink_deliveries` me kitni rows?
(b) Dono dispatcher ko kaunsa HTTP status code milega — aur ye `src/sink.py` me pre-`SELECT` hai ya `ON CONFLICT DO NOTHING`, uspe depend karta hai. **Dono ke liye alag likho.**
(c) Jis dispatcher ko non-`200` mila, uske outbox row ka `dispatched_at` aur `attempts` ka kya hoga?

### Prediction
(a) 1 row banegi.
(b) Ek ko 200 OK milega, doosre ko error/conflict aayega aur skip ho jayega.
(c) idk.

### Observed + meri explanation


### After KEY


## Q5
Interleaving B′: job `136` ka clone **disposable DB pe** — payload `{"seconds": 1, "crash_at": "before_commit"}`, reaper aur worker dono live, `90 s` tak chhod do.
(a) Kitni iteration hongi? (Exact number nahi — **order of magnitude** aur uska mechanism: kaunsa timer period decide karta hai?)
(b) `90 s` ke baad `attempts` kya hoga, aur `status` kya hoga?
(c) `side_effects_id_seq` aur `outbox_id_seq` ka total delta kya hoga, aur per iteration kitna?

### Prediction
(a) Usme to kuch nahi, worker job uthayega aur kaam karega.
(b) attempts 1 hoga, status success ho jayega.
(c) idk.

### Observed + meri explanation


### After KEY


