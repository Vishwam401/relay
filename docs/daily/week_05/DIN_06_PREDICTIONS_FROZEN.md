# Week 5 Din 6 — FROZEN PREDICTIONS

## Q1 (Step 0 se pehle — Din 5 commit)
(a) Commit ke baad `git ls-files logs` kitni files dikhayega? Aur WEEK_05.md
    ke Din 5 section me jo logs/w5d5_* paths cite hain, ek fresh clone me unme
    se kitne khulenge? (.gitignore padh ke)
(b) Commit ke baad `git ls-files -- "*PREDICTIONS_FROZEN*"` — number.
(c) DIN_05_PREDICTIONS_FROZEN.md pe, isi working copy me, commit ke baad:
    Get-FileHash wahi 8B38705B… rahega ya badlega? Aur `git hash-object` us
    file pe vs `git rev-parse HEAD:<path>` — same ya alag?

### Prediction
(a) idk
(b) idk
(c) idk

---

## Q2 (Step 2 se pehle — rule ka differential)
(a) AAJ ke rule ke neeche (.gitignore:47 jaisa hai), chaar probes —
    DIN_99_BRIEF.md, DIN_99_KEY.txt, DIN_99_SEALED.md, DIN_99_NEWCLASS.md —
    har ek PUBLISH ya ignored?
(b) Ek flip rule socho: `**/daily/**`, phir `!**/daily/**/*_BRIEF.md`,
    `!**/daily/**/*_PREDICTIONS_FROZEN.md`, `!**/daily/**/*HANDOFF*.md` — aur
    directory re-include ki koi line NAHI. Chaaron probes ka kya hoga? Aur
    docs/month_01/daily/WEEK_04_HANDOFF.md jaisi file (seedha daily/ ke andar,
    kisi subfolder me nahi) — nayi aisi file publish hogi ya nahi? Mechanism.
(c) Sahi flip ke baad `git ls-files -ci --exclude-standard` (aaj 1) — kitna,
    aur kaunsi file judegi, agar tu sirf BRIEF/FROZEN/HANDOFF re-include kare?
(d) Flip ke baad pehle se tracked 28 BRIEFs untrack ho jaayenge? Haan/nahi,
    aur kyun.

### Prediction
(a) idk
(b) idk
(c) idk
(d) idk

---

## Q3 (Step 3 se pehle — .pyc)
(a) `git rm --cached` + commit ke baad: pyc_tracked, pyc_in_01f42c6_bytes,
    pyc_on_disk — teeno values.
(b) Is hafte ke har Part C me `git ls-files -- "*.pyc"` → 1 positive control
    tha. Removal ke baad wo check kya prove karta hai, aur usko replace kyun
    karna padega? (Din 3 ka ls-tree wala sabak yaad kar.)

### Prediction
(a) idk
(b) idk

---

## Q4 (Step 6 se pehle — README rows)
(a) Row 9 ka crash point: "worker aur reaper dono us outage me marte hain".
    Din 5 ke baad, is repo ke code pe, ye crash point hota bhi hai? Evidence
    ke naam se jawab.
(b) Din 5 ka job 8 outage ke waqt exactly kis phase me tha — handler me, ya
    kahin aur? README ki kaunsi row uska evidence banti hai, aur kyun wo row 8
    ke shabdon se exactly match nahi karta? (w5d5_step6_inflight.txt padh ke)
(c) Agar README ka evidence cell `logs/w5d5_step6_final_jobs.txt` cite kare, to
    GitHub pe padhne wala use khol payega?

### Prediction
(a) idk
(b) idk
(c) idk

---

## Q5 (Step 10 se pehle — fresh clone; sirf tab jab Step 1 me .gitattributes
    `*_PREDICTIONS_FROZEN.md -text` chuna ho. Nahi chuna to (a)-(c) ko us
    rule ke hisaab se predict karo jo chuna)
(a) Fresh clone of HEAD: DIN_04_PREDICTIONS_FROZEN.md ka clone SHA-256 ==
    62196E9A… ?
(b) Usi clone me `git checkout c145a11` (attribute se pehle ka commit) karke
    phir hash karo — kya aayega? Aur ek alag fresh clone `--no-checkout` +
    `git checkout c145a11` me?
(c) Teeno cases me `git hash-object` on the clone's file vs head_blob — same
    ya alag?
(d) Seal ke liye kaunsa number har clone pe same rahega — working-copy
    SHA-256, ya git blob id? Ek line mechanism.

### Prediction
(a) idk
(b) idk
(c) idk
(d) idk
