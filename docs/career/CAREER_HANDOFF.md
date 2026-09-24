# Career & Distribution Handoff — Antigravity Agent Context

> **File:** `docs/career/CAREER_HANDOFF.md`  
> **Purpose:** Ye file kisi bhi AI agent ya conversation session ke liye permanent single source of truth hai. Isme Vishwam ka career roadmap, daily/weekly operating cadence, distribution rules, aur exact boundaries documented hain.

---

## 1. Core Profile & Goal

- **Engineer:** Vishwam (Gandhinagar University, Moti Bhoyan / Kalol, Ahmedabad region).
- **Core Goal:** Tier A Backend / Platform / Systems Engineer banna aur Ahmedabad Tier A companies (Crest Data Systems, Cygnet.One, Apexon, GIFT City Fintech) ya high-quality startups me internal referral ke through strong role crack karna.
- **Engine (Capability):** **Relay** — ek durable job execution engine (Python + PostgreSQL) jo Celery-like systems ki depth, at-least-once semantics, bounded retries, concurrency anomalies, aur crash-recovery guarantees ko measure aur prove karta hai.
- **Distribution (Wheels):** Relationship-first networking with 2–6 YOE backend/platform engineers. Zero cold begging, pure engineering credibility.

---

## 2. Current Status (Live Snapshot)

- **Relay Technical State:** Week 0 done (network/system failure reproduction). Week 1 Din 1 done (`jobs` table). Next: Din 2 (`POST /jobs`, `GET /jobs/{id}`).
- **Network Tracker:** `docs/career/NETWORK_TRACKER.csv`
- **Active Leads Identified (Tier A — Crest Data Systems):**
  1. **Ayush Vachhani** (Software Engineer, 4+ YOE, Python/Vue) — Stage: `0-Identified`
  2. **Ved Madhu** (Software Engineer, 4+ YOE, Python/React) — Stage: `0-Identified`
  3. **Rishika Khetawat** (Site Reliability Engineer, 5+ YOE, Splunk Cloud/SRE) — Stage: `0-Identified`
- **Next Outreach Action Date:** `2026-09-17` (Activity check for Stage 1 warm-up comment vs Stage 2 connection).

---

## 3. Operating Cadence: Roz Kya Karna vs Hafte me Kya Karna

### Daily Cadence (Monday to Saturday):
- **90% Time:** Relay engineering code, failure reproduction, DDIA reading, tests.
- **10% Time (Max 10 Minutes):**
  - Sirf LinkedIn notification / inbox check karna.
  - Agar kisi engineer ka reply aaya hai, toh **12 ghante ke andar** thoughtful answer dena (momentum rule).
  - Roz naye logo ko search karke time waste **nahi** karna.

### Weekly Ritual (Only Sunday — 45 Minutes Max):
- **00–10 min:** `docs/career/NETWORK_TRACKER.csv` review karna. Jin leads ki `Next_Action_Date` aaj ya past hai unko follow-up karna.
- **10–20 min:** Target companies me se **sirf 2 naye engineers** (2–6 YOE) dhoondhna aur tracker me `0-Identified` daalna.
- **20–30 min:** Stage 1 Warm-up: Unki 1–2 technical posts par thoughtful, genuine comment likhna.
- **30–45 min:** Stage 2 ya Stage 3 action: Connection accept hone ke baad ek focused technical sawaal bhejna.

---

## 4. Multi-Channel Strategy & The Strict Stage-Gate

> **Golden Rule:** Platform multiplication productivity jaisi dikhti hai, par actual me focus todti hai.

### Channel Priority:
1. **Relay + GitHub:** Capability proof (Asli truth — bina iske baaki sab zero).
2. **LinkedIn:** Primary distribution channel for local engineers, alumni, aur high-conversion referrals.
3. **X (Twitter):** Public distribution later (short threads, observations).
4. **Reddit:** Harsh technical feedback & architecture scrutiny (not for local networking).

### The Strict Stage-Gate (X aur Reddit Kab Open Honge?):
X aur Reddit tab tak active **nahi** honge jab tak ye 4 shartein poori na ho jayein:
- [ ] Relay README recruiter-readable ho (60-second clarity on guarantees).
- [ ] Kam-se-kam **1 measured public writeup** publish ho chuka ho (e.g. transaction rollback anomaly, pool starvation).
- [ ] `NETWORK_TRACKER.csv` me **8 verified engineers** add ho chuke hon.
- [ ] Lagataar **4 weeks** tak Sunday LinkedIn cadence bina ruke follow hui ho.

### Content Repurposing (One Artifact, Multiple Formats):
Alag-alag platform ke liye alag content nahi banana. Ek hi measured finding ko re-package karna hai:
- **Full Writeup:** GitHub / LinkedIn Article.
- **Summary (4-line):** LinkedIn Post.
- **3–5 Concise Observations:** X Thread.
- **Reddit Post:** Sirf technical problem-solving perspective se `r/backend` ya `r/postgresql` me.

---

## 5. The 5-Stage Ladder (Per Person Cycle)

$$\text{0-Identified} \longrightarrow \text{1-Warmed} \longrightarrow \text{2-Connected} \longrightarrow \text{3-Messaged} \longrightarrow \text{4-Conversing} \longrightarrow \text{5-Bonded} \longrightarrow \text{6-Asked}$$

1. **`0-Identified`:** Profile dhoondhi, criteria verify kiya (2–6 YOE, backend/platform/SRE), tracker me daala.
2. **`1-Warmed`:** Unki post/repo par 1 meaningful technical comment kiya (taaki naam notification me chala jaye).
3. **`2-Connected`:** Blank connection request (highest acceptance) ya <300 char humble note without demand.
4. **`3-Messaged` (2–3 din baad):** Single technical production question about their domain vs Relay's tradeoff.
5. **`4-Conversing`:** Advice aane par Relay me try karna aur update bhejna: *"Aapne jo bola tha try kiya, ye result aaya."* (Deep bond creator).
6. **`5-Bonded` (8–12 weeks later):** 3+ genuine technical exchanges ya 15-min call.
7. **`6-Asked`:** Chhota, polite referral/team inquiry ask.

---

## 6. Strict "Never Do" Rules (Red Flags)

- ❌ Pehle 4 hafte me galti se bhi referral, internship, ya "please guide me" mat maangna.
- ❌ HR, Recruiters, Founders, ya 10+ YOE wale logo ko target mat karna.
- ❌ Copy-paste spam messages mat bhejna.
- ❌ Ek din me 15-20 logo ko message bhej ke agle 2 mahine gayab mat hona.
- ❌ Roz ghanto LinkedIn scroll mat karna — Relay coding hamesha primary rahegi.

---

## 7. Next Agent Instruction

Jab bhi Vishwam se aage baat ho:
1. Relay ke technical code context ke liye `docs/roadmap/CHAT_HANDOFF.md` aur `docs/roadmap/CURRENT_WEEK.md` padho.
2. Career, outreach, ya networking context ke liye is file (`docs/career/CAREER_HANDOFF.md`) aur `docs/career/NETWORK_TRACKER.csv` ko reference karo.
3. Vishwam ko shiny-object distraction (X/Reddit hype, buzzwords) se rok ke **Relay execution + Sunday LinkedIn cadence** par aligned rakho.
